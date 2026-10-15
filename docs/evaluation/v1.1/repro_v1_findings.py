"""Reproduce the read-only review's findings against the current checkout, in scratch homes only.

Run from the repo root:  uv run python <this file>"""

import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path.cwd()
sys.path[:0] = [str(ROOT), str(ROOT / 'tests')]
SCRATCH = Path(tempfile.mkdtemp(prefix='va-repro-'))
os.environ['VISUAL_ATLAS_HOME'] = str(SCRATCH / 'unused')  # nothing may touch the real library

from fastapi.testclient import TestClient  # noqa: E402
from helpers import aic_fetcher  # noqa: E402

from atlas import catalog, jobs, transfer  # noqa: E402
from atlas.ai import fake, tasks  # noqa: E402
from atlas.ai.process import BackendError  # noqa: E402
from atlas.server import create_app  # noqa: E402

results = {}


def home(name):
    path = SCRATCH / name
    os.environ['VISUAL_ATLAS_HOME'] = str(path)
    return path


def seeded(name, count=2):
    path = home(name)
    with jobs.open_store(path) as store:
        jobs.create_job(store, 'find', {'goal': 'harbour', 'providers': ['aic'], 'backend': 'fake',
                                        'target_new_images': count})
    jobs.Worker(path, owner='seed', fetcher=aic_fetcher(), backends={'fake': fake}).run_once()
    return path


# A. restore accepts a write it then discards
path = seeded('restore')
backup = transfer.backup(path)
client = TestClient(create_app(path, token='t'), base_url='http://127.0.0.1')
original_backup = transfer.backup
status = {}


def backup_then_write(home_, allow_missing=False):
    made = original_backup(home_, allow_missing)
    response = client.post('/api/collections', json={'name': 'made during restore'},
                           headers={'X-Atlas-Token': 't'})  # the API acknowledges the write
    status['collection'] = response.status_code
    return made


transfer.backup = backup_then_write
response = client.post(f"/api/backups/{backup['name']}/restore", headers={'X-Atlas-Token': 't'})
transfer.backup = original_backup
with jobs.open_store(path) as store:
    kept = store.one("SELECT 1 FROM collections WHERE name='made during restore'") is not None
results['A_restore'] = {'collection_post': status.get('collection'), 'restore': response.status_code,
                        'collection_survived': kept}

# B. another server starts while a worker is saving a downloaded image (same hook point in old and new code)
path = home('sweep')
with jobs.open_store(path) as store:
    job_b = jobs.create_job(store, 'find', {'goal': 'harbour', 'providers': ['aic'], 'backend': 'fake',
                                            'target_new_images': 1})
from atlas.store import Store  # noqa: E402

real_add = Store.add_image


def add_with_second_start(self, *args, **kwargs):
    create_app(path, token='other')  # a second window/server starts at this moment
    return real_add(self, *args, **kwargs)


Store.add_image = add_with_second_start
try:
    jobs.Worker(path, owner='b', fetcher=aic_fetcher(), backends={'fake': fake}).run_once(job_b)
    crash = None
except Exception as error:  # noqa: BLE001 - the old code crashed here
    crash = repr(error)[:160]
Store.add_image = real_add
with jobs.open_store(path) as store:
    job = store.one('SELECT state, message FROM jobs WHERE id=?', (job_b,))
    image = store.one('SELECT analysis_path FROM images WHERE removed_at IS NULL')
results['B_sweep'] = {'worker_crash': crash, 'job': job,
                      'analysis_file_exists': bool(image) and (path / 'media' / image['analysis_path']).is_file()}

# C. verification failure reported as a successful check
class QuotaVerifier:
    NAME = 'claude'

    @staticmethod
    def run(*args, **kwargs):
        raise BackendError('quota')


path = seeded('verify', 1)
with jobs.open_store(path) as store:
    image_id = store.one('SELECT id FROM images')['id']
    store.connection.execute("UPDATE annotations SET state='proposed'")
    store.connection.commit()
    job_id = jobs.create_job(store, 'verify', {'image_ids': [image_id], 'backend': 'claude'})
jobs.Worker(path, owner='v', fetcher=aic_fetcher(), backends={'claude': QuotaVerifier, 'fake': fake}).run_once(job_id)
with jobs.open_store(path) as store:
    job = store.one('SELECT state, message FROM jobs WHERE id=?', (job_id,))
    item = store.one('SELECT state, reason FROM job_items WHERE job_id=?', (job_id,))
    saved = store.one("SELECT COUNT(*) AS n FROM analyses WHERE task='verify'")['n']
results['C_verify'] = {'job': job, 'item': item, 'verify_analyses_saved': saved}

# D. reanalysis accumulates proposals beyond the verifier contract
path = seeded('reanalysis', 1)
with jobs.open_store(path) as store:
    image_id = store.one('SELECT id FROM images')['id']
    ids = [t['id'] for t in catalog.load()[0]['techniques']]
    store.connection.execute('DELETE FROM annotations')
    store.connection.commit()

    def apply(chosen):
        analysis = store.add_analysis({'image_id': image_id, 'task': 'analyze', 'backend': 'codex', 'model': 'm',
                                       'prompt_sha': 'p', 'taxonomy_sha': 't', 'input_sha': 'i',
                                       'cache_key': os.urandom(8).hex(), 'result_json': '{}'})
        return store.apply_analysis(image_id, analysis, [
            {'technique_id': t, 'evidence': ['e'], 'effect': 'may', 'confidence': .8, 'role': 'supporting'}
            for t in chosen], 'model:codex/m')

    apply(ids[:4])
    apply(ids[4:7])
    active = store.one("SELECT COUNT(*) AS n FROM annotations WHERE image_id=? AND state='proposed'", (image_id,))['n']
    apply([])
    after_empty = store.one("SELECT COUNT(*) AS n FROM annotations WHERE image_id=? AND state!='rejected'",
                            (image_id,))['n']
    status_ = store.one('SELECT status FROM images WHERE id=?', (image_id,))['status']
schema_max = tasks.verify_schema(ids)['properties']['verdicts']['maxItems']
results['D_reanalysis'] = {'active_after_4_then_3': active, 'verify_schema_max': schema_max,
                           'labels_after_empty_analysis': after_empty, 'status_after_empty': status_}

# 4A. directions: empty image list accepted; fewer than 3 accepted; recency selection
direction = {'title': 'T', 'idea': 'An idea.', 'rationale': 'Because.', 'technique_ids': [ids[0]], 'image_ids': [],
             'execution': ['Do it.'], 'tradeoffs': ['Risk.']}
try:
    accepted = tasks.validate_directions({'directions': [direction]}, set(ids), {1, 2})
    results['4A_directions_validator'] = {'accepted_empty_image_ids_single_direction': len(accepted['directions'])}
except tasks.InvalidResult as error:
    results['4A_directions_validator'] = {'rejected': str(error)}
library = [{'image_id': i, 'title': 'x' * 400, 'summary': 'y' * 400} for i in range(400)]
prompt = tasks.directions_prompt({'title': 'b', 'text': 'b'}, catalog.load()[0]['techniques'], library)
segment = prompt.split('Library references (JSON): ')[1].split('\n\nBrief (JSON data)')[0]
try:
    json.loads(segment)
    results['4A_prompt_json_complete'] = True
except ValueError:
    results['4A_prompt_json_complete'] = False

# 5A. Retry-After ignored by retry scheduling
import inspect  # noqa: E402

results['5A_retry_after_used'] = 'retry_after' in inspect.getsource(jobs.Worker._retry_or_fail)

# 5B. budgets for 40 images
with jobs.open_store(home('budget')) as store:
    spec = json.loads(store.one('SELECT spec_json FROM jobs WHERE id=?', (jobs.create_job(
        store, 'find', {'goal': 'x', 'target_new_images': 40, 'backend': 'fake'}),))['spec_json'])
results['5B_budgets_for_40'] = spec['budgets']

print(json.dumps(results, indent=1, default=str))
