"""The only SQL write boundary. Other modules read with rows()/one() and write through methods here."""

import json
import sqlite3
import time
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

APPEND_ONLY = ('rights_records', 'analyses', 'annotation_history', 'attempts', 'tombstones', 'comparisons')
ANNOTATION_STATES = ('proposed', 'model_reviewed', 'human_reviewed', 'rejected')


class LeaseLost(RuntimeError):
    """Another worker took over the job; the current worker must stop writing."""


def now() -> str:
    return datetime.now(UTC).isoformat(timespec='seconds')


def canonical(value) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'))


class Store:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = self._connect(self.path)
        self.migrate()

    @staticmethod
    def _connect(path):
        connection = sqlite3.connect(path, timeout=5, check_same_thread=False)
        connection.row_factory = sqlite3.Row
        connection.execute('PRAGMA foreign_keys=ON')
        connection.execute('PRAGMA busy_timeout=5000')
        connection.execute('PRAGMA journal_mode=WAL')
        return connection

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def close(self):
        self.connection.close()

    # ---- schema ---------------------------------------------------------------------------
    def migrate(self):
        version = self.connection.execute('PRAGMA user_version').fetchone()[0]
        for file in sorted((Path(__file__).parent / 'migrations').glob('*.sql')):
            number = int(file.name.split('_')[0])
            if number <= version:
                continue
            if version:
                self.backup_to(self.path.with_name(self.path.name + f'.v{version}.bak'))
            sql = file.read_text(encoding='utf-8')
            if number == 1:
                for table in APPEND_ONLY:
                    for action in ('UPDATE', 'DELETE'):
                        sql += (f'\nCREATE TRIGGER {table}_{action.lower()} BEFORE {action} ON {table}'
                                f" BEGIN SELECT RAISE(ABORT,'{table} is append-only'); END;")
            try:
                self.connection.executescript(f'BEGIN IMMEDIATE;\n{sql}\nPRAGMA user_version={number};\nCOMMIT;')
            except Exception:
                self.connection.rollback()
                raise
            version = number

    def backup_to(self, path: Path):
        if self.connection.in_transaction:
            raise ValueError('database backup requires no active transaction')
        target = sqlite3.connect(path)
        try:
            self.connection.backup(target)
        finally:
            target.close()

    # ---- transactions and reads ------------------------------------------------------------
    @contextmanager
    def transaction(self):
        outer = not self.connection.in_transaction
        self.connection.execute('BEGIN IMMEDIATE' if outer else 'SAVEPOINT atlas_tx')
        try:
            yield self
            if outer:
                self.connection.commit()
            else:
                self.connection.execute('RELEASE atlas_tx')
        except BaseException:
            if outer:
                self.connection.rollback()
            else:
                self.connection.execute('ROLLBACK TO atlas_tx')
                self.connection.execute('RELEASE atlas_tx')
            raise

    @contextmanager
    def reading(self):
        if self.connection.in_transaction:
            yield self
            return
        self.connection.execute('BEGIN')
        try:
            yield self
        finally:
            self.connection.rollback()

    def rows(self, query: str, parameters=()) -> list[dict]:
        if not query.lstrip().upper().startswith(('SELECT ', 'WITH ')):
            raise ValueError('read query required')
        allowed = {sqlite3.SQLITE_SELECT, sqlite3.SQLITE_READ, sqlite3.SQLITE_FUNCTION,
                   sqlite3.SQLITE_RECURSIVE}
        def authorize(action, first, *rest):
            # FTS5 checks PRAGMA data_version internally; every other pragma or write is refused.
            if action in allowed or (action == sqlite3.SQLITE_PRAGMA and first == 'data_version'):
                return sqlite3.SQLITE_OK
            return sqlite3.SQLITE_DENY

        self.connection.set_authorizer(authorize)
        try:
            return [dict(row) for row in self.connection.execute(query, parameters).fetchall()]
        finally:
            self.connection.set_authorizer(None)

    def one(self, query: str, parameters=()) -> dict | None:
        found = self.rows(query, parameters)
        return found[0] if found else None

    def _columns(self, table: str) -> set[str]:
        cache = self.__dict__.setdefault('_column_cache', {})
        if table not in cache:
            cache[table] = {row[1] for row in self.connection.execute(f'PRAGMA table_info({table})')}
        return cache[table]

    def _check_columns(self, table: str, names) -> None:
        unknown = set(names) - self._columns(table)
        if unknown:  # never interpolate a name that is not a real column (imported data is untrusted)
            raise ValueError(f'unknown field(s) for {table}: {", ".join(sorted(map(str, unknown)))[:200]}')

    def _insert(self, table: str, record: dict) -> int:
        self._check_columns(table, record)
        columns = ','.join(record)
        marks = ','.join('?' for _ in record)
        return self.connection.execute(f'INSERT INTO {table}({columns}) VALUES({marks})',
                                       tuple(record.values())).lastrowid

    def _update(self, table: str, key: str, value, changes: dict) -> int:
        self._check_columns(table, [*changes, key])
        assignments = ','.join(f'{column}=?' for column in changes)
        return self.connection.execute(f'UPDATE {table} SET {assignments} WHERE {key}=?',
                                       (*changes.values(), value)).rowcount

    # ---- knowledge data (catalog.py validates before calling) --------------------------------
    def replace_catalog(self, taxonomy: dict, policies: dict, taxonomy_sha: str, policies_sha: str):
        with self.transaction():
            used = {row['technique_id'] for row in self.rows('SELECT DISTINCT technique_id FROM annotations')}
            missing = used - {technique['id'] for technique in taxonomy['techniques']}
            if missing:
                raise ValueError('techniques still used by annotations cannot be removed: '
                                 + ', '.join(sorted(missing)))
            execute = self.connection.execute
            execute('PRAGMA defer_foreign_keys=ON')
            for table in ('technique_links', 'goals', 'operations', 'domains', 'source_policies'):
                execute(f'DELETE FROM {table}')
            for goal in taxonomy['goals']:
                self._insert('goals', {k: goal[k] for k in ('id', 'name', 'description')})
            for operation in taxonomy['operations']:
                self._insert('operations', {k: operation[k] for k in ('id', 'name', 'description')})
            for domain in taxonomy['domains']:
                self._insert('domains', {'id': domain['id'], 'name': domain['name'],
                                         'description': domain['description'],
                                         'variables_json': canonical(domain['variables'])})
            ids = [technique['id'] for technique in taxonomy['techniques']]
            execute(f'DELETE FROM techniques WHERE id NOT IN ({",".join("?" * len(ids))})', ids)
            for technique in taxonomy['techniques']:
                execute('INSERT INTO techniques(id,name,data_json) VALUES(?,?,?) ON CONFLICT(id) DO UPDATE '
                        'SET name=excluded.name, data_json=excluded.data_json',
                        (technique['id'], technique['name'], canonical(technique)))
                links = [('goal', target, '') for target in technique['goals']]
                links += [('operation', target, '') for target in technique['operations']]
                links += [('domain', target, '') for target in technique['domains']]
                links += [('related', item['technique'], item['relation']) for item in technique['related']]
                links += [('confused_with', item['technique'], item['how_to_tell'])
                          for item in technique['confusions']]
                for kind, target, note in links:
                    self._insert('technique_links', {'technique_id': technique['id'], 'kind': kind,
                                                     'target_id': target, 'note': note})
            for provider in policies['providers']:
                self._insert('source_policies', {'provider': provider['id'], 'status': provider['status'],
                                                  'data_json': canonical(provider)})
            for name, sha in (('taxonomy', taxonomy_sha), ('source_policies', policies_sha)):
                execute('INSERT INTO data_versions(name,sha256,loaded_at) VALUES(?,?,?) ON CONFLICT(name) '
                        'DO UPDATE SET sha256=excluded.sha256, loaded_at=excluded.loaded_at', (name, sha, now()))
            for image in self.rows('SELECT id FROM images WHERE removed_at IS NULL'):
                self.refresh_search(image['id'])

    # ---- images ------------------------------------------------------------------------------
    def add_image(self, image: dict, rights: dict, metrics: dict, fence: tuple | None = None) -> int:
        with self.transaction():
            if fence:
                self._fence(*fence)
            image_id = self._insert('images', {**image, 'created_at': now()})
            self._insert('rights_records', {**rights, 'image_id': image_id})
            self._insert('image_metrics', {**metrics, 'image_id': image_id})
            self.refresh_search(image_id)
            return image_id

    def set_image_status(self, image_id: int, status: str, analysis_id: int | None = None):
        with self.transaction():
            changes = {'status': status}
            if analysis_id is not None:
                changes['analysis_id'] = analysis_id
            self._update('images', 'id', image_id, changes)
            self.refresh_search(image_id)

    def set_favorite(self, image_id: int, favorite: bool):
        with self.transaction():
            if not self._update('images', 'id', image_id, {'favorite': int(favorite)}):
                raise ValueError('image not found')

    def refresh_search(self, image_id: int):
        """Rewrite one image's search row from its metadata, observations and technique names."""
        image = self.one('SELECT * FROM images WHERE id=?', (image_id,))
        self.connection.execute('DELETE FROM images_fts WHERE rowid=?', (image_id,))
        if image is None or image['removed_at']:
            return
        parts = [image['description'], image['medium'], image['date_text']]
        if image['analysis_id']:
            analysis = self.one('SELECT result_json FROM analyses WHERE id=?', (image['analysis_id'],))
            result = json.loads(analysis['result_json'])
            parts += [item['text'] for item in result.get('observations', [])]
            parts += [result.get('summary', '')] + result.get('subjects', [])
        for row in self.rows("SELECT t.name, t.data_json FROM annotations a JOIN techniques t ON t.id=a.technique_id "
                             "WHERE a.image_id=? AND a.state!='rejected'", (image_id,)):
            parts += [row['name'], *json.loads(row['data_json']).get('aliases', [])]
        self.connection.execute('INSERT INTO images_fts(rowid,title,creator,body) VALUES(?,?,?,?)',
                                (image_id, image['title'], image['creator'], ' '.join(filter(None, parts))))

    def remove_image(self, image_id: int, reason: str, fence: tuple | None = None) -> dict:
        """Forget an image: files are deleted by the caller after this commits; a tombstone stops it being re-added.

        An automatic removal (fence given, from a job) never removes an image a person has already worked on."""
        with self.transaction():
            if fence:
                self._fence(*fence)
            image = self.one('SELECT * FROM images WHERE id=? AND removed_at IS NULL', (image_id,))
            if image is None:
                raise ValueError('image not found')
            if fence and (image['status'] == 'ready' or self.one(
                    'SELECT 1 FROM annotations WHERE image_id=? AND human_locked=1 UNION ALL '
                    'SELECT 1 FROM collection_items WHERE image_id=? LIMIT 1', (image_id, image_id))):
                raise ValueError('image is in use and was not removed automatically')
            self._insert('tombstones', {'provider': image['provider'], 'provider_item_id': image['provider_item_id'],
                                        'file_sha256': image['file_sha256'], 'dhash': image['dhash'],
                                        'reason': reason[:200], 'created_at': now()})
            for table in ('annotations', 'collection_items', 'image_metrics'):
                self.connection.execute(f'DELETE FROM {table} WHERE image_id=?', (image_id,))
            self._update('images', 'id', image_id, {'removed_at': now(), 'original_path': None,
                                                    'analysis_path': None, 'thumb_path': None,
                                                    'description': '', 'favorite': 0})
            self.refresh_search(image_id)
            return image

    def import_reference(self, image: dict, rights: dict, metrics: dict, analyses: list[dict],
                         annotations: list[dict], current_analysis: int | None = None) -> int | None:
        """Add one reference exported from another library (the starter pack), keeping its review states.

        Skips anything already present or removed by the user (tombstone)."""
        with self.transaction():
            known = self.one('SELECT 1 FROM images WHERE (provider=? AND provider_item_id=?) OR file_sha256=? UNION ALL '
                             'SELECT 1 FROM tombstones WHERE provider=? AND provider_item_id=?',
                             (image['provider'], image['provider_item_id'], image['file_sha256'], image['provider'],
                              image['provider_item_id']))
            if known:
                return None
            image_id = self._insert('images', {**image, 'analysis_id': None, 'created_at': now()})
            self._insert('rights_records', {**rights, 'image_id': image_id})
            self._insert('image_metrics', {**metrics, 'image_id': image_id})
            mapping = {}
            for analysis in analyses:
                mapping[analysis['id']] = self._insert('analyses', {
                    **{k: v for k, v in analysis.items() if k != 'id'}, 'image_id': image_id, 'job_id': None})
            for annotation in annotations:
                self._insert('annotations', {**annotation, 'image_id': image_id,
                                             'analysis_id': mapping.get(annotation.get('analysis_id'))})
            self._update('images', 'id', image_id, {'analysis_id': mapping.get(current_analysis)})
            self.refresh_search(image_id)
            return image_id

    # ---- analyses and annotations ------------------------------------------------------------
    def add_analysis(self, record: dict, fence: tuple | None = None) -> int:
        with self.transaction():
            if fence:
                self._fence(*fence)
            return self._insert('analyses', {**record, 'created_at': now()})

    def apply_analysis(self, image_id: int, analysis_id: int, techniques: list[dict], changed_by: str,
                       min_confidence: float = .4, fence: tuple | None = None) -> dict:
        """Merge model-proposed techniques without ever overwriting a person's decision."""
        applied, kept = [], []
        with self.transaction():
            if fence:
                self._fence(*fence)
            for item in techniques:
                existing = self.one('SELECT * FROM annotations WHERE image_id=? AND technique_id=?',
                                    (image_id, item['technique_id']))
                values = {'evidence_json': canonical(item['evidence']), 'effect': item['effect'],
                          'confidence': item['confidence'], 'role': item['role'],
                          'analysis_id': analysis_id, 'changed_by': changed_by, 'updated_at': now()}
                if existing and existing['human_locked']:
                    kept.append(item['technique_id'])
                    self._insert('annotation_history', {
                        'annotation_id': existing['id'], 'image_id': image_id, 'technique_id': item['technique_id'],
                        'state': existing['state'], 'role': item['role'], 'evidence_json': values['evidence_json'],
                        'effect': item['effect'], 'confidence': item['confidence'], 'analysis_id': analysis_id,
                        'human_locked': 1, 'changed_by': changed_by,
                        'note': 'model suggestion not applied: a person already decided', 'created_at': now()})
                    continue
                if item['confidence'] < min_confidence:
                    continue
                if existing:
                    self._update('annotations', 'id', existing['id'], {**values, 'state': 'proposed', 'note': ''})
                else:
                    self._insert('annotations', {**values, 'image_id': image_id,
                                                 'technique_id': item['technique_id'], 'state': 'proposed'})
                applied.append(item['technique_id'])
            self._update('images', 'id', image_id, {'analysis_id': analysis_id,
                                                    'status': 'ready' if applied or kept else 'unanalyzed'})
            self.refresh_search(image_id)
        return {'applied': applied, 'kept_human': kept}

    def apply_verdicts(self, image_id: int, analysis_id: int, verdicts: list[dict], changed_by: str,
                       fence: tuple | None = None) -> dict:
        """A second model agreeing promotes proposed -> model_reviewed; disagreement is noted, never deleted."""
        promoted, disputed = [], []
        with self.transaction():
            if fence:
                self._fence(*fence)
            checker = (self.one('SELECT backend FROM analyses WHERE id=?', (analysis_id,)) or {}).get('backend')
            for verdict in verdicts:
                row = self.one("SELECT a.*, p.backend AS proposer FROM annotations a LEFT JOIN analyses p ON "
                               "p.id=a.analysis_id WHERE a.image_id=? AND a.technique_id=?",
                               (image_id, verdict['technique_id']))
                if row is None or row['human_locked'] or row['state'] != 'proposed':
                    continue
                if row['proposer'] == checker:
                    continue  # a model checking its own proposal is not a second opinion
                row.pop('proposer')
                if verdict['holds']:
                    self._update('annotations', 'id', row['id'], {
                        'state': 'model_reviewed', 'changed_by': changed_by, 'updated_at': now(),
                        'note': 'second model agreed: ' + verdict['reason']})
                    promoted.append(verdict['technique_id'])
                else:
                    self._update('annotations', 'id', row['id'], {
                        'changed_by': changed_by, 'updated_at': now(),
                        'note': 'second model disagreed: ' + verdict['reason']})
                    disputed.append(verdict['technique_id'])
            self._insert('annotation_history', {
                'annotation_id': 0, 'image_id': image_id, 'technique_id': '*', 'state': 'verify',
                'role': 'supporting', 'evidence_json': '[]', 'effect': '', 'confidence': 0,
                'analysis_id': analysis_id, 'human_locked': 0, 'changed_by': changed_by,
                'note': f'verification: {len(promoted)} agreed, {len(disputed)} disputed', 'created_at': now()})
        return {'promoted': promoted, 'disputed': disputed}

    def human_annotation(self, image_id: int, technique_id: str, *, state: str, evidence: list[str] | None = None,
                         effect: str | None = None, note: str = '') -> int:
        """A person's accept/reject/add/edit. Locks the annotation against later model output."""
        if state not in ('human_reviewed', 'rejected'):
            raise ValueError('a person either confirms (human_reviewed) or rejects a technique')
        with self.transaction():
            if not self.one('SELECT id FROM images WHERE id=? AND removed_at IS NULL', (image_id,)):
                raise ValueError('image not found')
            if not self.one('SELECT id FROM techniques WHERE id=?', (technique_id,)):
                raise ValueError('unknown technique')
            existing = self.one('SELECT * FROM annotations WHERE image_id=? AND technique_id=?',
                                (image_id, technique_id))
            values = {'state': state, 'human_locked': 1, 'changed_by': 'human', 'updated_at': now(),
                      'note': note[:500]}
            if evidence is not None:
                values['evidence_json'] = canonical([text[:300] for text in evidence if text.strip()][:8])
            if effect is not None:
                values['effect'] = effect[:400]
            if existing:
                self._update('annotations', 'id', existing['id'], values)
                annotation_id = existing['id']
            else:
                if not values.get('evidence_json') or values['evidence_json'] == '[]':
                    if state == 'human_reviewed':
                        raise ValueError('describe the visible evidence for a technique you add')
                annotation_id = self._insert('annotations', {
                    'image_id': image_id, 'technique_id': technique_id, 'role': 'supporting',
                    'evidence_json': values.get('evidence_json', '[]'), 'effect': values.get('effect', ''),
                    'confidence': 1.0, **{k: v for k, v in values.items() if k not in ('evidence_json', 'effect')}})
            self._update('images', 'id', image_id, {'status': 'ready'})
            self.refresh_search(image_id)
            return annotation_id

    # ---- jobs ----------------------------------------------------------------------------------
    def create_job(self, job_id: str, kind: str, spec: dict, backend: str, model: str) -> str:
        with self.transaction():
            self._insert('jobs', {'id': job_id, 'kind': kind, 'spec_json': canonical(spec), 'state': 'queued',
                                  'backend': backend, 'model': model, 'created_at': now()})
        return job_id

    def claim_job(self, owner: str, lease_seconds: float = 60, job_id: str | None = None) -> dict | None:
        """Take the next runnable job if no other worker holds a live lease (one job at a time)."""
        clock = time.time()
        with self.transaction():
            # Any live lease held by someone else blocks a claim, whatever the job's state: a worker that was
            # paused and quickly resumed keeps its lease until it has really stopped.
            busy = self.one('SELECT id FROM jobs WHERE lease_until>? AND lease_owner IS NOT NULL AND lease_owner!=?',
                            (clock, owner))
            if busy:
                return None
            query = ("SELECT * FROM jobs WHERE state IN ('queued','running','cancelling') "
                     + ('AND id=? ' if job_id else '') + 'ORDER BY created_at, id LIMIT 1')
            job = self.one(query, (job_id,) if job_id else ())
            if job is None:
                return None
            self._update('jobs', 'id', job['id'], {
                'lease_owner': owner, 'lease_until': clock + lease_seconds, 'heartbeat_at': clock,
                'state': 'cancelling' if job['state'] == 'cancelling' else 'running',
                'started_at': job['started_at'] or now()})
            return self.one('SELECT * FROM jobs WHERE id=?', (job['id'],))

    def _fence(self, job_id: str, owner: str):
        job = self.one('SELECT lease_owner, lease_until FROM jobs WHERE id=?', (job_id,))
        if job is None or job['lease_owner'] != owner or (job['lease_until'] or 0) <= time.time():
            raise LeaseLost(job_id)

    def heartbeat(self, job_id: str, owner: str, lease_seconds: float = 60) -> dict:
        with self.transaction():
            self._fence(job_id, owner)
            clock = time.time()
            self._update('jobs', 'id', job_id, {'lease_until': clock + lease_seconds, 'heartbeat_at': clock})
            return self.one('SELECT * FROM jobs WHERE id=?', (job_id,))

    def update_job(self, job_id: str, owner: str | None, **changes):
        allowed = {'state', 'stage', 'message', 'error_code', 'finished_at', 'lease_owner', 'lease_until'}
        if not changes or set(changes) - allowed:
            raise ValueError('invalid job change')
        with self.transaction():
            if owner is not None:
                self._fence(job_id, owner)
            self._update('jobs', 'id', job_id, changes)

    def request_job_state(self, job_id: str, action: str) -> dict:
        """User control from the UI or CLI: pause, resume or cancel."""
        with self.transaction():
            job = self.one('SELECT * FROM jobs WHERE id=?', (job_id,))
            if job is None:
                raise ValueError('job not found')
            state = job['state']
            live = (job['lease_until'] or 0) > time.time() and job['lease_owner']
            if action == 'cancel' and state in ('queued', 'paused') and live:
                self._update('jobs', 'id', job_id, {'state': 'cancelling', 'message': 'Stopping…'})
            elif action == 'cancel' and state in ('queued', 'paused'):
                self._update('jobs', 'id', job_id, {'state': 'cancelled', 'stage': 'cancelled',
                                                    'message': 'Cancelled before it finished.', 'finished_at': now()})
                self.connection.execute("UPDATE job_items SET state='skipped', reason='cancelled', updated_at=? "
                                        "WHERE job_id=? AND state NOT IN %s" % _FINAL_SQL, (now(), job_id))
            elif action == 'cancel' and state == 'running':
                self._update('jobs', 'id', job_id, {'state': 'cancelling', 'message': 'Stopping…'})
            elif action == 'pause' and state in ('queued', 'running'):
                self._update('jobs', 'id', job_id, {'state': 'paused', 'message': 'Paused. Resume when ready.'})
            elif action == 'resume' and state in ('paused', 'failed'):
                self._update('jobs', 'id', job_id, {'state': 'queued', 'message': 'Waiting to resume…',
                                                    'error_code': None, 'finished_at': None})
            elif action not in ('cancel', 'pause', 'resume'):
                raise ValueError('unknown job action')
            return self.one('SELECT * FROM jobs WHERE id=?', (job_id,))

    def add_items(self, job_id: str, owner: str, items: list[dict]) -> int:
        added = 0
        with self.transaction():
            self._fence(job_id, owner)
            for item in items:
                added += self.connection.execute(
                    'INSERT OR IGNORE INTO job_items(job_id,kind,key,provider,provider_item_id,payload_json,state,'
                    'reason,updated_at) VALUES(?,?,?,?,?,?,?,?,?)',
                    (job_id, item['kind'], item['key'], item['provider'], item.get('provider_item_id', ''),
                     canonical(item.get('payload', {})), item.get('state', 'pending'), item.get('reason', ''),
                     now())).rowcount
        return added

    def update_item(self, job_id: str, owner: str, item_id: int, **changes):
        allowed = {'state', 'reason', 'attempts', 'next_attempt_at', 'image_id', 'payload_json'}
        if set(changes) - allowed:
            raise ValueError('invalid item change')
        with self.transaction():
            self._fence(job_id, owner)
            self._update('job_items', 'id', item_id, {**changes, 'updated_at': now()})

    def record_attempt(self, record: dict) -> int:
        with self.transaction():
            return self._insert('attempts', {**record, 'created_at': now()})

    # ---- user data ---------------------------------------------------------------------------
    def set_setting(self, key: str, value: str):
        with self.transaction():
            self.connection.execute('INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE '
                                    'SET value=excluded.value', (key, value))

    def create_collection(self, name: str, description: str = '') -> int:
        name = name.strip()
        if not 0 < len(name) <= 80:
            raise ValueError('collection names need 1 to 80 characters')
        with self.transaction():
            if self.one('SELECT id FROM collections WHERE name=?', (name,)):
                raise ValueError('a collection with that name already exists')
            return self._insert('collections', {'name': name, 'description': description[:500],
                                                'created_at': now()})

    def update_collection(self, collection_id: int, name: str | None = None, description: str | None = None):
        changes = {}
        if name is not None:
            if not 0 < len(name.strip()) <= 80:
                raise ValueError('collection names need 1 to 80 characters')
            changes['name'] = name.strip()
        if description is not None:
            changes['description'] = description[:500]
        with self.transaction():
            if changes and not self._update('collections', 'id', collection_id, changes):
                raise ValueError('collection not found')

    def delete_collection(self, collection_id: int):
        with self.transaction():
            if not self.connection.execute('DELETE FROM collections WHERE id=?', (collection_id,)).rowcount:
                raise ValueError('collection not found')

    def collect(self, collection_id: int, image_id: int, add: bool = True, note: str = ''):
        with self.transaction():
            if add:
                if not self.one('SELECT id FROM images WHERE id=? AND removed_at IS NULL', (image_id,)):
                    raise ValueError('image not found')
                position = self.one('SELECT COALESCE(MAX(position),0)+1 AS p FROM collection_items '
                                    'WHERE collection_id=?', (collection_id,))['p']
                self.connection.execute('INSERT OR IGNORE INTO collection_items(collection_id,image_id,position,note,'
                                        'added_at) VALUES(?,?,?,?,?)',
                                        (collection_id, image_id, position, note[:300], now()))
            else:
                self.connection.execute('DELETE FROM collection_items WHERE collection_id=? AND image_id=?',
                                        (collection_id, image_id))

    def reorder_collection(self, collection_id: int, image_ids: list[int]):
        with self.transaction():
            for position, image_id in enumerate(image_ids, 1):
                self.connection.execute('UPDATE collection_items SET position=? WHERE collection_id=? AND image_id=?',
                                        (position, collection_id, image_id))

    def save_brief(self, title: str, text: str, brief_id: int | None = None) -> int:
        if not 0 < len(title.strip()) <= 120 or not 0 < len(text.strip()) <= 4000:
            raise ValueError('a brief needs a title (≤120 characters) and a description (≤4000)')
        with self.transaction():
            if brief_id:
                if not self._update('briefs', 'id', brief_id, {'title': title.strip(), 'text': text.strip(),
                                                                'updated_at': now()}):
                    raise ValueError('brief not found')
                return brief_id
            return self._insert('briefs', {'title': title.strip(), 'text': text.strip(),
                                           'created_at': now(), 'updated_at': now()})

    def delete_brief(self, brief_id: int):
        with self.transaction():
            self.connection.execute('DELETE FROM briefs WHERE id=?', (brief_id,))

    def save_directions(self, brief_id: int, analysis_id: int, directions: list[dict]):
        with self.transaction():
            self.connection.execute("DELETE FROM directions WHERE brief_id=? AND state='proposed'", (brief_id,))
            start = self.one('SELECT COALESCE(MAX(position),0) AS p FROM directions WHERE brief_id=?',
                             (brief_id,))['p']
            for position, direction in enumerate(directions, start + 1):
                self._insert('directions', {'brief_id': brief_id, 'analysis_id': analysis_id, 'position': position,
                                            'result_json': canonical(direction), 'created_at': now()})

    def set_direction_state(self, direction_id: int, state: str):
        if state not in ('proposed', 'kept', 'dismissed'):
            raise ValueError('invalid direction state')
        with self.transaction():
            self._update('directions', 'id', direction_id, {'state': state})

    def add_comparison(self, image_ids: list[int], analysis_id: int) -> int:
        with self.transaction():
            return self._insert('comparisons', {'image_ids': ','.join(map(str, sorted(image_ids))),
                                                'analysis_id': analysis_id, 'created_at': now()})


_FINAL = ('added', 'ineligible', 'duplicate', 'low_quality', 'no_technique', 'failed', 'skipped',
          'searched', 'filtered')
_FINAL_SQL = '(' + ','.join(f"'{state}'" for state in _FINAL) + ')'
FINAL_ITEM_STATES = _FINAL
