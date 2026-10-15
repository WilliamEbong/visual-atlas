"""Persistent, resumable jobs: Find images, Grow my library, and AI follow-ups (verify, compare, directions).

One job runs at a time, claimed with a lease. Every item moves through explicit states, one transition
per step, so a crash or restart resumes exactly where it stopped. Usage: Worker(home).run_once()."""

import hashlib
import json
import os
import re
import socket
import threading
import time
import uuid
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

from atlas import __version__, catalog, images, providers, rights
from atlas.ai import claude_cli, codex_cli, fake, tasks
from atlas.ai.process import BackendError
from atlas.fetch import Fetcher, FetchError
from atlas.home import home_dir
from atlas.store import LeaseLost, LibraryBusy, Store, canonical, now

BACKENDS = {'codex': codex_cli, 'claude': claude_cli, 'fake': fake}
BACKEND_NAMES = {'codex': 'Codex', 'claude': 'Claude Code', 'fake': 'Practice mode'}
LEASE_SECONDS = 60
HEARTBEAT_SECONDS = 5
DEFAULT_BUDGETS = {'max_searches': 10, 'max_candidates': 80, 'max_downloads': 30, 'max_analyses': 12}
DAILY_AI_CAP = 120
clock = time.time  # retry back-off clock (tests replace it; leases use the real clock in store.py)
RETRYABLE = {'timeout', 'network', 'rate_limited', 'http_500', 'http_502', 'http_503', 'http_504', 'http_521',
             'http_522', 'provider_error', 'invalid_response'}
PAUSING = {'quota', 'subscription_auth_required', 'unavailable', 'unsupported_version', 'unsupported_flag',
           'containment_unavailable', 'daily_cap'}
STOPWORDS = set('a an and are as at be but by for from how i images image in into is it its me my of on or our '
                'show showing some that the their them this to use used using want we with you your find need '
                'picture pictures photo photos something like look looks'.split())


def db_path(home: Path) -> Path:
    return home / 'atlas.db'


def open_store(home: Path | None = None) -> Store:
    home = home_dir(home)
    store = Store(db_path(home))
    catalog.sync(store)
    return store


def backend_message(code: str, backend: str) -> str:
    name = BACKEND_NAMES.get(backend, backend)
    return {
        'unavailable': f'{name} is not installed or could not be found on this computer.',
        'subscription_auth_required': f'{name} is not signed in. Open AI setup for the one-time sign-in steps.',
        'quota': f'{name} reached its usage limit. Resume later, or switch to the other assistant.',
        'daily_cap': 'Today\'s AI limit in Settings was reached. Resume tomorrow or raise the limit.',
        'timeout': f'{name} took too long to answer.',
        'invalid_response': 'The answer did not pass Visual Atlas\'s checks, so it was not saved.',
        'tool_call': 'The assistant tried to use a tool, which Visual Atlas does not allow. The answer was discarded.',
        'unsupported_version': f'{name} is too old. Update it, then resume.',
        'unsupported_flag': f'This version of {name} changed its options. Update Visual Atlas or {name}.',
        'cancelled': 'Stopped.',
        'provider_error': f'{name} reported an error.',
        'output_limit': 'The answer was too long and was discarded.',
        'containment_unavailable': 'Windows would not let Visual Atlas run the assistant safely.',
    }.get(code, f'{name} could not finish ({code}).')


class Worker:
    def __init__(self, home: Path | None = None, *, owner: str | None = None, fetcher: Fetcher | None = None,
                 backends: dict | None = None, sleep=time.sleep):
        self.home = home_dir(home)
        self.media = self.home / 'media'
        self.owner = owner or f'{socket.gethostname()}:{os.getpid()}:{uuid.uuid4().hex[:8]}'
        self._fetcher = fetcher
        self.backends = backends or BACKENDS
        self.sleep = sleep
        self.activity = 0  # bumped on every step; the app launcher treats a running job as activity

    # ---- entry points ---------------------------------------------------------------------------
    def run_once(self, job_id: str | None = None) -> str | None:
        """Claim one job and work it until it finishes, pauses, is cancelled or the lease is lost."""
        with open_store(self.home) as store:
            try:
                job = store.claim_job(self.owner, LEASE_SECONDS, job_id)
            except LibraryBusy:
                return None  # a restore or clean-up is running; try again later
            if job is None:
                return None
            self.store = store
            self.job = job
            self.spec = json.loads(job['spec_json'])
            taxonomy, policies, self.taxonomy_sha, _ = catalog.load()
            self.policies = policies
            self.techniques = {t['id']: t for t in taxonomy['techniques']}
            try:
                self._work()
            except LeaseLost:
                pass  # another worker took over after our lease expired; it continues from the same items
            except LibraryBusy:
                return None  # maintenance began after our lease lapsed: stop; the job resumes from its items later
            return job['id']

    def loop(self, stop: threading.Event, idle_seconds: float = 2):
        while not stop.is_set():
            try:
                worked = self.run_once()
            except Exception as error:  # keep the background worker alive; the job records its own failure
                print(f'worker error: {error!r}', flush=True)
                worked = None
            if not worked:
                stop.wait(idle_seconds)

    # ---- helpers ------------------------------------------------------------------------------
    @property
    def fetcher(self) -> Fetcher:
        if self._fetcher is None:
            self._fetcher = Fetcher(self.policies)
        return self._fetcher

    def _job(self) -> dict:
        self.job = self.store.heartbeat(self.job['id'], self.owner, LEASE_SECONDS)
        self.activity += 1
        return self.job

    def _set(self, **changes):
        self.store.update_job(self.job['id'], self.owner, **changes)

    def _item(self, item_id: int, **changes):
        self.store.update_item(self.job['id'], self.owner, item_id, **changes)

    def _items(self, where: str = '1', parameters=()) -> list[dict]:
        return self.store.rows(f"SELECT * FROM job_items WHERE job_id=? AND {where} ORDER BY id",
                               (self.job['id'], *parameters))

    def _analysed(self) -> int:
        """Images this job has sent for analysis (second-model checks are not counted against the budget)."""
        return self.store.one("SELECT COUNT(*) AS n FROM attempts a JOIN job_items i ON i.id=a.item_id WHERE a.job_id=? "
                              "AND a.kind='ai' AND a.backend=? AND i.kind='candidate'", (self.job['id'], self.job['backend']))['n']

    def _count(self, kind: str) -> int:
        return self.store.one('SELECT COUNT(*) AS n FROM attempts WHERE job_id=? AND kind=?',
                              (self.job['id'], kind))['n']

    def _ai_today(self) -> int:
        today = datetime.now(UTC).strftime('%Y-%m-%d')
        return self.store.one("SELECT COUNT(*) AS n FROM attempts WHERE kind='ai' AND backend!='fake' "
                              "AND created_at>=?", (today,))['n']

    def _budget(self, key: str) -> int:
        return int((self.spec.get('budgets') or {}).get(key, DEFAULT_BUDGETS[key]))

    def _finish(self, state: str, message: str, error_code: str | None = None):
        if state in ('cancelled', 'done'):
            open_states = "('pending','found','eligible','downloaded','analyzed')"
            for item in self._items(f'state IN {open_states}'):
                self._item(item['id'], state='skipped', reason='cancelled' if state == 'cancelled' else
                           'not needed: the job reached its target or a budget')
        self._set(state=state, stage=state, message=message[:500], error_code=error_code, finished_at=now(),
                  lease_owner=None, lease_until=None)

    def _pause(self, message: str, code: str):
        self._set(state='paused', stage='paused', message=message[:500], error_code=code, lease_owner=None,
                  lease_until=None)

    def _retry_or_fail(self, item: dict, code: str, message: str):
        attempts = item['attempts'] + 1
        if code in RETRYABLE and attempts < 3:
            self._item(item['id'], attempts=attempts, next_attempt_at=clock() + min(5 * 2 ** attempts, 300),
                       reason=f'retrying: {message}')
        else:
            self._item(item['id'], attempts=attempts, state='failed', reason=message[:300])

    # ---- AI calls -----------------------------------------------------------------------------
    def _call(self, task: str, prompt: str, schema: dict, image_paths: list[Path], *, item_id=None,
              backend: str | None = None) -> dict:
        backend = backend or self.job['backend']
        model = (self.spec.get('models') or {}).get(task) or tasks.DEFAULT_MODELS[backend][task]
        if backend != 'fake':
            row = self.store.one("SELECT value FROM settings WHERE key='daily_ai_cap'")
            if self._ai_today() >= (int(row['value']) if row else DAILY_AI_CAP):
                raise BackendError('daily_cap')
        started = time.monotonic()
        try:
            answer = self.backends[backend].run(prompt, schema, image_paths, model=model, record=item_id,
                                                cancel=self._cancel)
        except BackendError as error:
            self.store.record_attempt({'job_id': self.job['id'], 'item_id': item_id, 'kind': 'ai', 'backend': backend,
                                       'model': model, 'status': 'error', 'error_code': error.code,
                                       'input_tokens': error.input_tokens, 'output_tokens': error.output_tokens,
                                       'latency_ms': int((time.monotonic() - started) * 1000),
                                       'cli_version': error.cli_version})
            raise
        self.store.record_attempt({'job_id': self.job['id'], 'item_id': item_id, 'kind': 'ai', 'backend': backend,
                                   'model': model, 'status': 'ok', 'input_tokens': answer['input_tokens'],
                                   'output_tokens': answer['output_tokens'],
                                   'latency_ms': int((time.monotonic() - started) * 1000),
                                   'cli_version': answer['cli_version']})
        return {**answer, 'backend': backend, 'model': model}

    def _save_analysis(self, task: str, answer: dict, result: dict, *, image_id=None, input_sha='', cache_key=''):
        return self.store.add_analysis(fence=(self.job['id'], self.owner), record={
            'image_id': image_id, 'job_id': self.job['id'], 'task': task, 'backend': answer['backend'],
            'model': answer['model'], 'model_version': answer.get('model_version'),
            'cli_version': answer.get('cli_version'), 'prompt_sha': tasks.prompt_sha(task),
            'taxonomy_sha': self.taxonomy_sha, 'input_sha': input_sha, 'cache_key': cache_key or uuid.uuid4().hex,
            'result_json': canonical(result), 'input_tokens': answer['input_tokens'],
            'output_tokens': answer['output_tokens']})

    # ---- the job loop -------------------------------------------------------------------------
    @contextmanager
    def _lease_kept(self):
        """Keep the lease alive for a whole step (slow searches and downloads as well as AI calls), and stop a
        running AI call when the user pauses or cancels or the lease is lost. Writes stay fenced either way."""
        self._cancel = cancel = threading.Event()
        done = threading.Event()

        def watch():
            with Store(db_path(self.home)) as side:
                while not done.wait(HEARTBEAT_SECONDS):
                    try:
                        job = side.heartbeat(self.job['id'], self.owner, LEASE_SECONDS)
                    except (LeaseLost, LibraryBusy):
                        cancel.set()
                        return
                    if job['state'] not in ('running', 'queued'):
                        cancel.set()
                        return

        watcher = threading.Thread(target=watch, daemon=True)
        watcher.start()
        try:
            yield
        finally:
            done.set()
            watcher.join(timeout=10)

    def _work(self):
        kind = self.job['kind']
        self._set(message='Starting…')
        while True:
            job = self._job()
            if job['state'] == 'cancelling':
                return self._finish('cancelled', 'Cancelled. Images already added were kept.')
            if job['state'] == 'queued':  # resumed before this worker noticed the pause
                self.store.update_job(self.job['id'], self.owner, only_from='queued', state='running')
                continue  # read the state again: a pause or cancel may have arrived in between
            if job['state'] != 'running':  # paused, or already finished elsewhere: let go and stop
                return self._set(lease_owner=None, lease_until=None)
            try:
                with self._lease_kept():
                    progressed = {'find': self._discovery_step, 'grow': self._discovery_step,
                                  'verify': self._verify_step, 'analyze': self._reanalyze_step,
                                  'compare': self._compare_step, 'directions': self._directions_step}[kind]()
            except BackendError as error:
                if error.code == 'cancelled':
                    continue  # paused or cancelled mid-call; the loop top carries out the request
                message = backend_message(error.code, self.job['backend'])
                if error.code in PAUSING:
                    return self._pause(message, error.code)
                return self._finish('failed', message, error.code)
            if progressed is False:
                return
            if progressed is None:  # only waiting items remain (back-off); idle briefly with the lease held
                self.sleep(2)

    # ---- discovery: find and grow -------------------------------------------------------------
    def _added(self) -> int:
        return len(self._items("kind='candidate' AND state='added'"))

    def _discovery_step(self):
        target = int(self.spec.get('target_new_images', 8))
        if not self._items("kind='query'"):
            return self._plan()
        if self._added() >= target:
            return self._done(f'Ready. Added {self._added()} images.')
        now_ = clock()
        for state, step in (('downloaded', self._analyze), ('eligible', self._download), ('found', self._permission)):
            item = self.store.one("SELECT * FROM job_items WHERE job_id=? AND kind='candidate' AND state=? AND "
                                  "next_attempt_at<=? ORDER BY json_extract(payload_json,'$.rank'), id LIMIT 1",
                                  (self.job['id'], state, now_))
            if item:
                step(item)
                return True
        query = self.store.one("SELECT * FROM job_items WHERE job_id=? AND kind='query' AND state='pending' AND "
                               "next_attempt_at<=? ORDER BY id LIMIT 1", (self.job['id'], now_))
        candidates = len(self._items("kind='candidate'"))
        if query and self._count('search') < self._budget('max_searches') and candidates < self._budget('max_candidates'):
            self._search(query)
            return True
        waiting = self.store.one("SELECT COUNT(*) AS n FROM job_items WHERE job_id=? AND state IN "
                                 "('pending','found','eligible','downloaded') AND next_attempt_at>?",
                                 (self.job['id'], now_))['n']
        if waiting:
            return None
        return self._done(self._summary(exhausted=True))

    def _done(self, message: str):
        self._finish('done', message)
        return False

    def _summary(self, exhausted=False) -> str:
        counts = {row['state']: row['n'] for row in self.store.rows(
            "SELECT state, COUNT(*) AS n FROM job_items WHERE job_id=? AND kind='candidate' GROUP BY state",
            (self.job['id'],))}
        added = counts.get('added', 0)
        parts = [f'Added {added} image{"s" if added != 1 else ""}.']
        labels = {'ineligible': 'without a usable free licence', 'duplicate': 'duplicates', 'low_quality':
                  'too small or unclear', 'no_technique': 'with no clear technique', 'failed': 'failed',
                  'filtered': 'outside your filters'}
        skipped = [f'{counts[k]} {v}' for k, v in labels.items() if counts.get(k)]
        if skipped:
            parts.append('Skipped ' + ', '.join(skipped) + '.')
        if exhausted and added < int(self.spec.get('target_new_images', 8)):
            parts.append('The searches ran out before reaching your number; try a broader request.')
        return ' '.join(parts)

    def _plan(self):
        self._set(stage='planning', message='Planning searches…')
        enabled = [p for p in self.spec.get('providers') or providers.PROVIDERS
                   if catalog.policy(self.policies, p).get('status') == 'enabled']
        queries = []
        if self.job['kind'] == 'grow':
            for technique_id in self.spec.get('technique_ids') or []:
                hints = self.techniques[technique_id]['search_hints']
                for provider in enabled:
                    for hint in (hints.get(provider) or [])[:2]:
                        queries.append({'provider': provider, 'query': hint, 'technique_id': technique_id})
        else:
            goal = self._goal_text()
            planned = None  # AI planning first; curated taxonomy hints if it is unavailable or invalid
            try:
                schema = tasks.plan_schema(sorted(self.techniques), enabled)
                answer = self._call('plan', tasks.plan_prompt(goal, list(self.techniques.values()), enabled),
                                    schema, [])
                planned = tasks.validate_plan(answer['result'], set(self.techniques), set(enabled))
                self._save_analysis('plan', answer, planned, input_sha=hashlib.sha256(goal.encode()).hexdigest())
            except (BackendError, tasks.InvalidResult) as error:
                if isinstance(error, BackendError) and error.code in ('quota', 'daily_cap', 'cancelled'):
                    raise
                planned = None
            queries = planned['queries'] if planned else self._fallback_queries(goal, enabled)
        items = [{'kind': 'query', 'key': f"{q['provider']}:{q['query'].lower()}", 'provider': q['provider'],
                  'payload': {'query': q['query'], 'technique_id': q.get('technique_id')}} for q in queries]
        if not items:
            return self._done('Nothing to search for. Add a few words about what you want to see.')
        self.store.add_items(self.job['id'], self.owner, items)
        self._set(stage='searching', message=f'Searching {len(enabled)} collections…')
        return True

    def _goal_text(self) -> str:
        spec = self.spec
        parts = [spec.get('goal', '')]
        for key, label in (('subject', 'Subject'), ('intended_use', 'Intended use'), ('orientation', 'Orientation'),
                           ('color', 'Colour')):
            if spec.get(key):
                parts.append(f'{label}: {spec[key]}')
        if spec.get('technique_ids'):
            parts.append('Techniques: ' + ', '.join(self.techniques[t]['name'] for t in spec['technique_ids']
                                                    if t in self.techniques))
        return '. '.join(p for p in parts if p)[:1000]

    def _fallback_queries(self, goal: str, enabled: list[str]) -> list[dict]:
        """No AI: match goal words to technique names and aliases, then use their curated search hints."""
        words = {w for w in re.findall(r"[a-z]+", goal.lower()) if w not in STOPWORDS and len(w) > 2}
        scored = []
        for technique in self.techniques.values():
            text = ' '.join([technique['name'], *technique['aliases']]).lower()
            score = sum(1 for word in words if word in text)
            if technique['id'] in (self.spec.get('technique_ids') or []):
                score += 5
            if score:
                scored.append((score, technique['id']))
        chosen = [tid for _, tid in sorted(scored, reverse=True)[:3]]
        queries = []
        subject = (self.spec.get('subject') or '').strip()
        for technique_id in chosen:
            for provider in enabled:
                for hint in (self.techniques[technique_id]['search_hints'].get(provider) or [])[:1]:
                    queries.append({'provider': provider, 'query': hint, 'technique_id': technique_id})
        keywords = subject or ' '.join(sorted(words - {w for t in chosen for w in t.split('-')}))[:40]
        if keywords:
            queries += [{'provider': provider, 'query': keywords, 'technique_id': None} for provider in enabled]
        return queries[:12]

    def _search(self, query: dict):
        payload = json.loads(query['payload_json'])
        self._set(stage='searching', message=f"Searching {providers.NAMES[query['provider']]} for “{payload['query']}”…")
        started = time.monotonic()
        try:
            found = providers.search(self.fetcher, query['provider'], payload['query'], payload.get('page', 0),
                                     int(self.spec.get('per_query', 8)))
        except FetchError as error:
            self.store.record_attempt({'job_id': self.job['id'], 'item_id': query['id'], 'kind': 'search',
                                       'backend': query['provider'], 'status': 'error', 'error_code': error.code,
                                       'latency_ms': int((time.monotonic() - started) * 1000)})
            return self._retry_or_fail(query, error.code, str(error))
        self.store.record_attempt({'job_id': self.job['id'], 'item_id': query['id'], 'kind': 'search',
                                   'backend': query['provider'], 'status': 'ok',
                                   'latency_ms': int((time.monotonic() - started) * 1000)})
        fresh = []
        for rank, candidate in enumerate(found):
            known = self.store.one(
                "SELECT 1 FROM images WHERE provider=? AND provider_item_id=? UNION ALL "
                "SELECT 1 FROM tombstones WHERE provider=? AND provider_item_id=? UNION ALL "
                "SELECT 1 FROM job_items WHERE provider=? AND provider_item_id=? AND state IN "
                "('ineligible','duplicate','low_quality','no_technique') LIMIT 1",
                (candidate['provider'], candidate['provider_item_id']) * 3)
            if known:
                continue
            fresh.append({'kind': 'candidate', 'key': f"{candidate['provider']}:{candidate['provider_item_id']}",
                          'provider': candidate['provider'], 'provider_item_id': candidate['provider_item_id'],
                          'payload': {**candidate, 'rank': rank, 'technique_hint': payload.get('technique_id')},
                          'state': 'found'})
        room = self._budget('max_candidates') - len(self._items("kind='candidate'"))
        added = self.store.add_items(self.job['id'], self.owner, fresh[:max(0, room)])
        self._item(query['id'], state='searched', reason=f'{len(found)} results, {added} new')

    def _permission(self, item: dict):
        self._set(stage='checking', message='Checking permissions…')
        candidate = json.loads(item['payload_json'])
        decision = rights.check(candidate, catalog.policy(self.policies, item['provider']))
        if not decision['eligible']:
            return self._item(item['id'], state='ineligible', reason=decision['reason'])
        self._item(item['id'], state='eligible', payload_json=canonical({**candidate, 'rights': decision}))

    def _download(self, item: dict):
        if self._count('download') >= self._budget('max_downloads'):
            return self._item(item['id'], state='skipped', reason='download budget reached')
        if self._analysed() >= self._budget('max_analyses'):
            return self._item(item['id'], state='skipped', reason='analysis budget reached')
        candidate = json.loads(item['payload_json'])
        self._set(stage='checking', message=f"Downloading “{candidate['title'][:60]}”…")
        started = time.monotonic()
        try:
            data = self.fetcher.get_image(item['provider'], candidate['image_url'], headers=candidate['image_headers'])
            picture, kind = images.open_checked(data)
        except FetchError as error:
            self._attempt('download', item, 'error', error.code, started)
            return self._retry_or_fail(item, error.code, str(error))
        except images.ImageRejected as error:
            self._attempt('download', item, 'error', error.code, started)
            return self._item(item['id'], state='low_quality', reason=str(error))
        self._attempt('download', item, 'ok', None, started)
        sha = hashlib.sha256(data).hexdigest()
        mine = self.store.one('SELECT id FROM images WHERE file_sha256=? AND job_id=? AND provider=? '
                              'AND provider_item_id=? AND removed_at IS NULL',
                              (sha, self.job['id'], item['provider'], item['provider_item_id']))
        if mine:  # saved just before a crash; write any file that did not make it, then carry on
            images.write_files(self.media, images.prepare_files(data, picture, kind)[1])
            return self._item(item['id'], state='downloaded', image_id=mine['id'])
        stats = images.metrics(picture)
        problem = images.quality_problem(picture, stats)
        if problem:
            return self._item(item['id'], state='low_quality', reason=problem)
        for key, wanted in (('orientation', self.spec.get('orientation')), ('color_family', self.spec.get('color'))):
            if wanted and stats[key] != wanted:
                return self._item(item['id'], state='filtered', reason=f'{key.replace("_", " ")} is {stats[key]}')
        fingerprint = images.dhash(picture)
        duplicate = self.store.one('SELECT id FROM images WHERE file_sha256=? UNION ALL '
                                   'SELECT id FROM tombstones WHERE file_sha256=? LIMIT 1', (sha, sha))
        if duplicate is None:
            # ponytail: linear dHash scan; a BK-tree is worth it only past ~20k images
            for row in self.store.rows("SELECT dhash FROM images WHERE removed_at IS NULL UNION ALL "
                                       "SELECT dhash FROM tombstones"):
                if images.hamming(row['dhash'], fingerprint) <= 6:
                    duplicate = row
                    break
        if duplicate is not None:
            return self._item(item['id'], state='duplicate', reason='same or nearly the same picture is already known')
        files, blobs = images.prepare_files(data, picture, kind)
        decision = candidate['rights']
        stamp = now()
        image_id = self.store.add_image(
            {'provider': item['provider'], 'provider_item_id': item['provider_item_id'],
             'title': candidate['title'] or 'Untitled', 'creator': candidate['creator'],
             'date_text': candidate['date_text'], 'medium': candidate['medium'],
             'description': candidate['description'], 'source_url': candidate['source_url'],
             'dhash': fingerprint, 'job_id': self.job['id'], **files},
            {'license_code': decision['license_code'], 'license_version': decision['license_version'],
             'license_url': decision['license_url'], 'label': decision['label'],
             'evidence_url': decision['evidence_url'], 'evidence_json': canonical(decision['evidence']),
             'required_attribution': decision['required_attribution'], 'restrictions': decision['restrictions'],
             'permitted_mode': decision['permitted_mode'], 'file_sha256': files['file_sha256'],
             'retrieved_at': stamp, 'verified_at': stamp,
             'policy_sha': hashlib.sha256(canonical(catalog.policy(self.policies, item['provider'])).encode()).hexdigest(),
             'provenance_json': canonical({'image_url': candidate['image_url'], 'job_id': self.job['id'],
                                           'search_rank': candidate['rank'], 'credit_line': candidate.get('credit_line', ''),
                                           'retrieved_by': f'Visual Atlas {__version__}'})},
            {**{k: stats[k] for k in ('aspect', 'orientation', 'mean_luma', 'contrast', 'colorfulness', 'saturation',
                                      'color_family')}, 'palette_json': canonical(stats['palette'])},
            fence=(self.job['id'], self.owner))
        images.write_files(self.media, blobs)  # after the row commits, so clean-up never sees them as strays
        self._item(item['id'], state='downloaded', image_id=image_id)

    def _attempt(self, kind, item, status, code, started):
        self.store.record_attempt({'job_id': self.job['id'], 'item_id': item['id'], 'kind': kind,
                                   'backend': item['provider'], 'status': status, 'error_code': code,
                                   'latency_ms': int((time.monotonic() - started) * 1000)})

    def _analyze(self, item: dict):
        image = self.store.one('SELECT * FROM images WHERE id=?', (item['image_id'],))
        if image is None or image['removed_at']:
            return self._item(item['id'], state='skipped', reason='image was removed')
        if image['status'] != 'pending':  # analysed already (e.g. a crash after saving)
            if image['status'] == 'ready':
                self._finish_verification(image['id'], item['id'])
            return self._item(item['id'], state='added' if image['status'] == 'ready' else 'no_technique', reason='')
        if self._analysed() >= self._budget('max_analyses') and not self._cached(image):
            return self._item(item['id'], state='skipped', reason='analysis budget reached')
        self._set(stage='analyzing', message=f"Analyzing “{image['title'][:60]}”…")
        try:
            outcome = self.analyze_image(image, item_id=item['id'])
        except BackendError as error:
            if error.code in PAUSING:
                raise
            if error.code == 'cancelled':
                return None  # paused or cancelled mid-call: the item stays as it was and resumes later
            # One picture's trouble (a timeout, a provider hiccup) never stops the whole job.
            return self._retry_or_fail(item, error.code, backend_message(error.code, self.job['backend']))
        if outcome == 'retry':
            return self._retry_or_fail(item, 'invalid_response', backend_message('invalid_response', self.job['backend']))
        if outcome == 'added':
            return self._item(item['id'], state='added', reason='')
        self._remove_unhelpful(image, outcome)
        self._item(item['id'], state='no_technique', reason=outcome)

    def _cache_key(self, image: dict) -> str:
        backend = self.job['backend']
        model = (self.spec.get('models') or {}).get('analyze') or tasks.DEFAULT_MODELS[backend]['analyze']
        return hashlib.sha256('|'.join([image['analysis_sha256'], self.taxonomy_sha, tasks.prompt_sha('analyze'),
                                        backend, model]).encode()).hexdigest()

    def _cached(self, image: dict) -> bool:
        return self.store.one("SELECT 1 FROM analyses WHERE cache_key=? AND task='analyze'",
                              (self._cache_key(image),)) is not None

    def _finish_verification(self, image_id: int, item_id: int):
        """After a crash between analysis and the second-model check, run the check that was missed."""
        verifier = self.spec.get('verify_with')
        if verifier and not self.store.one("SELECT 1 FROM analyses WHERE image_id=? AND task='verify' AND job_id=?",
                                           (image_id, self.job['id'])):
            self.verify_image(image_id, verifier, item_id=item_id)

    def _remove_unhelpful(self, image: dict, reason: str):
        try:
            removed = self.store.remove_image(image['id'], f'not added: {reason}', fence=(self.job['id'], self.owner))
        except ValueError:
            return  # someone is already using this image; keep it
        images.delete_files(self.media, removed)

    def analyze_image(self, image: dict, *, item_id=None) -> str:
        """Analyse (or reuse a cached analysis), validate, save, merge; optionally verify with the other model."""
        backend = self.job['backend']
        model = (self.spec.get('models') or {}).get('analyze') or tasks.DEFAULT_MODELS[backend]['analyze']
        metadata = {'title': image['title'], 'creator': image['creator'], 'date': image['date_text'],
                    'medium': image['medium'], 'description': image['description'],
                    'source': image['provider']}
        cache_key = self._cache_key(image)
        cached = self.store.one("SELECT * FROM analyses WHERE cache_key=? AND task='analyze' ORDER BY id DESC LIMIT 1",
                                (cache_key,))
        if cached:
            result, analysis_id = json.loads(cached['result_json']), cached['id']
        else:
            schema = tasks.analyze_schema(sorted(self.techniques))
            prompt = tasks.analyze_prompt(list(self.techniques.values()), metadata)
            answer = self._call('analyze', prompt, schema, [self.media / image['analysis_path']], item_id=item_id)
            try:
                result = tasks.validate_analysis(answer['result'], set(self.techniques), metadata)
            except tasks.InvalidResult:
                return 'retry'
            analysis_id = self._save_analysis('analyze', answer, result, image_id=image['id'],
                                              input_sha=image['analysis_sha256'], cache_key=cache_key)
        if not result['image_usable']:
            self.store.set_image_status(image['id'], 'unanalyzed', analysis_id)
            return f"not a usable picture: {result['unusable_reason'] or 'unclear'}"
        texts = tasks.evidence_texts(result)
        proposals = [{'technique_id': t['technique_id'], 'evidence': texts[t['technique_id']], 'effect': t['effect'],
                      'confidence': t['confidence'], 'role': t['role']} for t in result['techniques']]
        merged = self.store.apply_analysis(image['id'], analysis_id, proposals, f'model:{backend}/{model}',
                                           fence=(self.job['id'], self.owner))
        if not merged['applied'] and not merged['kept_human']:
            return 'no technique was clear enough'
        verifier = self.spec.get('verify_with')
        if verifier and verifier != backend and merged['applied']:
            self.verify_image(image['id'], verifier, item_id=item_id)
        return 'added'

    def verify_image(self, image_id: int, verifier: str, *, item_id=None):
        rows = self.store.rows("SELECT a.technique_id, a.evidence_json, a.effect FROM annotations a LEFT JOIN "
                               "analyses p ON p.id=a.analysis_id WHERE a.image_id=? AND a.state='proposed' AND "
                               "a.human_locked=0 AND COALESCE(p.backend,'')!=?", (image_id, verifier))
        if not rows:
            return
        image = self.store.one('SELECT analysis_path, analysis_sha256 FROM images WHERE id=?', (image_id,))
        proposals = [{'technique_id': r['technique_id'], 'evidence': json.loads(r['evidence_json']),
                      'effect': r['effect']} for r in rows]
        self._set(stage='analyzing', message='Checking the analysis with a second model…')
        try:
            for attempt in (1, 2):  # one quick retry: the subscription CLIs occasionally report a transient error
                try:
                    answer = self._call('verify', tasks.verify_prompt(proposals, self.techniques),
                                        tasks.verify_schema(sorted(self.techniques)),
                                        [self.media / image['analysis_path']], item_id=item_id, backend=verifier)
                    break
                except BackendError as error:
                    if attempt == 2 or error.code not in ('provider_error', 'timeout'):
                        raise
            result = tasks.validate_verify(answer['result'], {p['technique_id'] for p in proposals})
        except tasks.InvalidResult:
            return  # leave annotations as 'proposed'; the verification simply did not count
        except BackendError as error:
            if error.code in ('daily_cap', 'cancelled'):
                raise  # a pause or cancel leaves the check to be resumed
            return  # verifier unavailable, over its limit or erroring: keep the proposal unverified and go on
        with self.store.transaction():  # the saved answer and its effect commit together
            analysis_id = self._save_analysis('verify', answer, result, image_id=image_id,
                                              input_sha=image['analysis_sha256'])
            self.store.apply_verdicts(image_id, analysis_id, result['verdicts'],
                                      f"model:{answer['backend']}/{answer['model']}", fence=(self.job['id'], self.owner))

    # ---- follow-up jobs -------------------------------------------------------------------------
    def _image_items(self, state: str):
        return self.store.one("SELECT * FROM job_items WHERE job_id=? AND state=? AND next_attempt_at<=? "
                              "ORDER BY id LIMIT 1", (self.job['id'], state, clock()))

    def _waiting(self, state: str) -> bool:
        return self.store.one('SELECT 1 FROM job_items WHERE job_id=? AND state=? LIMIT 1',
                              (self.job['id'], state)) is not None

    def _seed_images(self, state: str):
        if not self._items():
            ids = [int(i) for i in self.spec.get('image_ids') or []]
            self.store.add_items(self.job['id'], self.owner, [
                {'kind': 'candidate', 'key': f'image:{i}', 'provider': 'library', 'provider_item_id': str(i),
                 'payload': {'image_id': i}, 'state': state} for i in ids])

    def _verify_step(self):
        self._seed_images('pending')
        item = self._image_items('pending')
        if item is None:
            return None if self._waiting('pending') else self._done('Ready. Second-model check finished.')
        image_id = int(item['provider_item_id'])
        self._item(item['id'], image_id=image_id)
        self.verify_image(image_id, self.job['backend'], item_id=item['id'])
        self._item(item['id'], state='added', reason='checked')
        return True

    def _reanalyze_step(self):
        self._seed_images('pending')
        item = self._image_items('pending')
        if item is None:
            return None if self._waiting('pending') else self._done('Ready. Analysis finished.')
        image = self.store.one('SELECT * FROM images WHERE id=? AND removed_at IS NULL', (int(item['provider_item_id']),))
        if image is None:
            self._item(item['id'], state='skipped', reason='image was removed')
            return True
        never_added = image['status'] == 'pending'  # downloaded by a job that stopped before analysing it
        self._set(stage='analyzing', message=f"Analyzing “{image['title'][:60]}”…")
        try:
            outcome = self.analyze_image(image, item_id=item['id'])
        except BackendError as error:
            if error.code in PAUSING:
                raise
            if error.code != 'cancelled':  # a pause or cancel leaves the item to be resumed
                self._retry_or_fail(item, error.code, backend_message(error.code, self.job['backend']))
            return True
        if outcome == 'retry':
            self._retry_or_fail(item, 'invalid_response', backend_message('invalid_response', self.job['backend']))
        elif outcome == 'added':
            self._item(item['id'], state='added', image_id=image['id'])
        else:
            if never_added:  # same rule as Find: only images with a clear technique join the library
                self._remove_unhelpful(image, outcome)
            self._item(item['id'], state='no_technique', reason=outcome, image_id=image['id'])
        return True

    def _compare_step(self):
        ids = [int(i) for i in self.spec.get('image_ids') or []][:4]
        rows = [self.store.one('SELECT * FROM images WHERE id=? AND removed_at IS NULL', (i,)) for i in ids]
        if len(ids) < 2 or None in rows:
            return self._done_failed('Pick two to four images that are still in the library.')
        self._set(stage='analyzing', message='Comparing images…')
        annotations = {str(i): [r['technique_id'] for r in self.store.rows(
            "SELECT technique_id FROM annotations WHERE image_id=? AND state!='rejected'", (i,))] for i in ids}
        answer = self._call('compare', tasks.compare_prompt(ids, annotations),
                            tasks.compare_schema(ids, sorted(self.techniques)),
                            [self.media / r['analysis_path'] for r in rows])
        try:
            result = tasks.validate_compare(answer['result'], set(ids), set(self.techniques))
        except tasks.InvalidResult as error:
            return self._done_failed(f'The comparison did not pass checks ({error}).')
        analysis_id = self._save_analysis('compare', answer, result,
                                          input_sha='|'.join(r['analysis_sha256'] for r in rows))
        self.store.add_comparison(ids, analysis_id)
        return self._done('Ready. Comparison saved.')

    def _directions_step(self):
        brief = self.store.one('SELECT * FROM briefs WHERE id=?', (int(self.spec.get('brief_id') or 0),))
        if brief is None:
            return self._done_failed('That brief no longer exists.')
        self._set(stage='analyzing', message='Thinking through directions for your brief…')
        library = self.store.rows(
            "SELECT i.id AS image_id, i.title, i.creator, i.date_text AS date, "
            "json_extract(a.result_json,'$.summary') AS summary, "
            "(SELECT group_concat(technique_id) FROM annotations n WHERE n.image_id=i.id AND n.state!='rejected') AS techniques "
            "FROM images i LEFT JOIN analyses a ON a.id=i.analysis_id WHERE i.removed_at IS NULL AND i.status='ready' "
            "ORDER BY i.id DESC LIMIT 150")
        for row in library:
            row['techniques'] = (row['techniques'] or '').split(',') if row['techniques'] else []
        image_ids = [row['image_id'] for row in library]
        answer = self._call('directions', tasks.directions_prompt(brief, list(self.techniques.values()), library),
                            tasks.directions_schema(sorted(self.techniques), image_ids), [])
        try:
            result = tasks.validate_directions(answer['result'], set(self.techniques), set(image_ids))
        except tasks.InvalidResult as error:
            return self._done_failed(f'The suggestions did not pass checks ({error}).')
        analysis_id = self._save_analysis('directions', answer, result,
                                          input_sha=hashlib.sha256(brief['text'].encode()).hexdigest())
        self.store.save_directions(brief['id'], analysis_id, result['directions'])
        return self._done(f"Ready. {len(result['directions'])} directions saved.")

    def _done_failed(self, message: str):
        self._finish('failed', message, 'invalid')
        return False


def create_job(store: Store, kind: str, spec: dict) -> str:
    """Validate a job request (from the UI, CLI or another agent) and queue it."""
    if kind not in ('find', 'grow', 'verify', 'analyze', 'compare', 'directions'):
        raise ValueError('unknown job kind')
    backend = spec.get('backend') or 'codex'
    if backend not in BACKENDS:
        raise ValueError('backend must be codex, claude or fake')
    clean = {'backend': backend}
    if kind in ('find', 'grow'):
        technique_ids = [t for t in spec.get('technique_ids') or [] if isinstance(t, str)]
        known = {r['id'] for r in store.rows('SELECT id FROM techniques')}
        if set(technique_ids) - known:
            raise ValueError('unknown technique')
        if kind == 'grow' and not technique_ids:
            technique_ids = [row['id'] for row in catalog.coverage(store)[:4]]
        chosen = [p for p in spec.get('providers') or providers.PROVIDERS if p in providers.PROVIDERS]
        if not chosen:
            raise ValueError('choose at least one collection')
        target = int(spec.get('target_new_images') or 8)
        if not 1 <= target <= 40:
            raise ValueError('ask for between 1 and 40 images per job')
        goal = str(spec.get('goal') or '').strip()
        if kind == 'find' and not (goal or spec.get('subject') or technique_ids):
            raise ValueError('describe what you are looking for, or pick a technique')
        asked = spec.get('budgets') or {}
        budgets = {k: max(1, min(int(asked.get(k, DEFAULT_BUDGETS[k])), 200)) for k in DEFAULT_BUDGETS}
        if 'max_analyses' not in asked:  # by default leave room for a few pictures that turn out unclear
            budgets['max_analyses'] = max(budgets['max_analyses'], min(target + 4, 200))
        clean.update(goal=goal[:1000], subject=str(spec.get('subject') or '')[:120],
                     intended_use=str(spec.get('intended_use') or '')[:200], technique_ids=technique_ids,
                     orientation=spec.get('orientation') if spec.get('orientation') in ('landscape', 'portrait', 'square') else None,
                     color=str(spec.get('color') or '')[:20] or None, providers=chosen, target_new_images=target,
                     budgets=budgets, per_query=max(3, min(int(spec.get('per_query') or 8), 20)))
        verifier = spec.get('verify_with')
        clean['verify_with'] = verifier if verifier in ('codex', 'claude') and verifier != backend else None
    elif kind in ('verify', 'analyze', 'compare'):
        ids = [int(i) for i in spec.get('image_ids') or []]
        if not ids or (kind == 'compare' and not 2 <= len(ids) <= 4):
            raise ValueError('pick images' if kind != 'compare' else 'compare needs two to four images')
        clean['image_ids'] = ids[:200]
        verifier = spec.get('verify_with')
        if kind == 'analyze' and verifier in ('codex', 'claude') and verifier != backend:
            clean['verify_with'] = verifier
    elif kind == 'directions':
        clean['brief_id'] = int(spec.get('brief_id') or 0)
        if not store.one('SELECT id FROM briefs WHERE id=?', (clean['brief_id'],)):
            raise ValueError('brief not found')
    if isinstance(spec.get('models'), dict):
        clean['models'] = {k: str(v)[:120] for k, v in spec['models'].items() if k in tasks.DEFAULT_MODELS[backend]}
    model = (clean.get('models') or {}).get('analyze') or tasks.DEFAULT_MODELS[backend]['analyze']
    return store.create_job(uuid.uuid4().hex[:12], kind, clean, backend, model)
