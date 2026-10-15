"""Library-wide maintenance (restore and media clean-up): no acknowledged write is ever lost, across the API, the
background worker, the CLI and other processes. Every interleaving here is forced with a hook, never a sleep."""

import json
import subprocess
import sys
import time
import zipfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from helpers import aic_fetcher

from atlas import images, jobs, transfer
from atlas.ai import fake
from atlas.server import create_app
from atlas.store import LibraryBusy, Store

TOKEN = {'X-Atlas-Token': 't'}
ROOT = Path(__file__).resolve().parents[1]


def find(store, **spec):
    return jobs.create_job(store, 'find', {'goal': 'harbour', 'providers': ['aic'], 'backend': 'fake',
                                           'target_new_images': 1, **spec})


@pytest.fixture
def library(home):
    with jobs.open_store(home) as store:
        find(store)
    jobs.Worker(home, owner='seed', fetcher=aic_fetcher(), backends={'fake': fake}).run_once()
    return home


def client_for(home):
    return TestClient(create_app(home, token='t'), base_url='http://127.0.0.1')


def test_an_api_write_during_a_restore_is_refused_not_lost(library, monkeypatch):
    client = client_for(library)
    saved = client.post('/api/backups', headers=TOKEN).json()
    during = {}
    real_copy = transfer._copy_media

    def copy_then_write(*args):  # after the safety backup, before the database swap
        during['write'] = client.post('/api/collections', json={'name': 'made during restore'}, headers=TOKEN)
        during['read'] = client.get('/api/collections', headers=TOKEN)
        return real_copy(*args)

    monkeypatch.setattr(transfer, '_copy_media', copy_then_write)
    assert client.post(f"/api/backups/{saved['name']}/restore", headers=TOKEN).status_code == 200
    assert during['write'].status_code == 503 and 'restoring' in during['write'].json()['detail']
    assert during['read'].status_code == 200  # reading never waits
    assert client.post('/api/collections', json={'name': 'after'}, headers=TOKEN).status_code == 201
    names = [c['name'] for c in client.get('/api/collections', headers=TOKEN).json()]
    assert names == ['after']


def test_another_process_cannot_write_during_maintenance_and_can_afterwards(library):
    script = ('import sys; from atlas.store import Store, LibraryBusy\n'
              'with Store(sys.argv[1]) as s:\n'
              '    try: s.create_collection(sys.argv[2]); print("written")\n'
              '    except LibraryBusy: print("refused")')
    run = [sys.executable, '-c', script, str(library / 'atlas.db')]
    with Store(library / 'atlas.db') as store, store.maintenance(idle='jobs'):
        assert subprocess.run([*run, 'during'], capture_output=True, text=True, cwd=ROOT).stdout.strip() == 'refused'
    assert subprocess.run([*run, 'after'], capture_output=True, text=True, cwd=ROOT).stdout.strip() == 'written'


def test_a_second_restore_cannot_start_while_one_runs(library, monkeypatch):
    saved = transfer.backup(library)
    outcome = {}
    real_copy = transfer._copy_media

    def nested(*args):
        try:
            transfer.restore(library, saved['name'])
        except LibraryBusy as error:
            outcome['second'] = str(error)
        return real_copy(*args)

    monkeypatch.setattr(transfer, '_copy_media', nested)
    transfer.restore(library, saved['name'])
    assert 'Another restore' in outcome['second']


def test_restore_waits_for_jobs_and_jobs_cannot_start_during_it(library):
    with jobs.open_store(library) as store:
        job_id = find(store)
        with pytest.raises(LibraryBusy, match='job is still running or waiting'):
            with store.maintenance(idle='jobs'):
                pass
        store.request_job_state(job_id, 'cancel')
        with store.maintenance(idle='jobs'), jobs.open_store(library) as other:
            with pytest.raises(LibraryBusy):
                find(other)  # creating a job (from the app or another terminal) is a write like any other
    with Store(library / 'atlas.db') as store, store.maintenance(idle='jobs'):
        assert jobs.Worker(library, owner='w', fetcher=aic_fetcher(), backends={'fake': fake}).run_once() is None


def test_a_worker_whose_lease_lapsed_stops_cleanly_when_clean_up_starts(library):
    with jobs.open_store(library) as store:
        job_id = find(store, goal='lighthouse')
        store.claim_job('stalled', 60, job_id)
        store.update_job(job_id, None, lease_until=time.time() - 1)  # the worker stalled past its lease
        with store.maintenance(idle='leases'):
            worker = jobs.Worker(library, owner='stalled', fetcher=aic_fetcher(), backends={'fake': fake})
            assert worker.run_once(job_id) is None  # refused before any item changed
        assert store.rows('SELECT * FROM job_items WHERE job_id=?', (job_id,)) == []


def test_a_marker_left_by_a_holder_that_died_is_cleared(library):
    holder = subprocess.Popen(
        [sys.executable, '-c', 'import sys; from atlas.store import take_lock\n'
         'lock = take_lock(__import__("pathlib").Path(sys.argv[1])); print("locked", flush=True); sys.stdin.readline()',
         str(library / 'maintenance.lock')], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, cwd=ROOT)
    assert holder.stdout.readline().strip() == 'locked'
    with Store(library / 'atlas.db') as store:
        store.set_setting('maintenance', 'someone-else')  # as if that holder had started a restore
        with pytest.raises(LibraryBusy):
            store.create_collection('while held')
        holder.communicate('\n')  # the holder exits (a crash frees the lock the same way)
        store.create_collection('after the holder died')
        assert store.one("SELECT 1 FROM settings WHERE key='maintenance'") is None


def legacy_v1_database(path: Path):
    """A library database exactly as Visual Atlas 0.1 created it (migration 001 only)."""
    sql = (ROOT / 'atlas/migrations/001_initial.sql').read_text(encoding='utf-8')
    for table in ('rights_records', 'analyses', 'annotation_history', 'attempts', 'tombstones', 'comparisons'):
        for action in ('UPDATE', 'DELETE'):
            sql += (f'\nCREATE TRIGGER {table}_{action.lower()} BEFORE {action} ON {table}'
                    f" BEGIN SELECT RAISE(ABORT,'{table} is append-only'); END;")
    import sqlite3
    db = sqlite3.connect(path)
    db.executescript(f'BEGIN;\n{sql}\nPRAGMA user_version=1;\nCOMMIT;')
    db.execute("INSERT INTO tombstones(provider,provider_item_id,file_sha256,dhash,reason,created_at) "
               "VALUES('aic','1','a','b','not added: no clear technique','2026-10-15'), "
               "('aic','2','c','d','removed by the person','2026-10-15')")
    db.execute("INSERT INTO collections(name,created_at) VALUES('kept from 0.1','2026-10-15')")
    db.commit()
    db.close()


def test_a_backup_from_version_0_1_restores_and_upgrades(home):
    with jobs.open_store(home):
        pass
    (home / 'backups').mkdir()
    legacy = home / 'legacy.db'
    legacy_v1_database(legacy)
    data = legacy.read_bytes()
    name = 'visual-atlas-backup-20261015-000000.zip'
    with zipfile.ZipFile(home / 'backups' / name, 'w') as archive:
        archive.writestr('atlas.db', data)
        archive.writestr('manifest.json', json.dumps({
            'format': 'visual-atlas-backup', 'version': 1, 'created': '2026-10-15', 'app_version': '0.1.0',
            'files': {'atlas.db': __import__('hashlib').sha256(data).hexdigest()}, 'missing': []}))
    assert transfer.restore(home, name)['restored'] == name
    with Store(home / 'atlas.db') as store:
        assert store.connection.execute('PRAGMA user_version').fetchone()[0] == 2
        assert store.one("SELECT name FROM collections")['name'] == 'kept from 0.1'
        kinds = {r['provider_item_id']: r['source'] for r in store.rows('SELECT * FROM tombstone_kinds')}
        assert kinds == {'1': 'auto', '2': 'user'}


def test_starting_another_app_mid_download_never_deletes_the_new_files(home, monkeypatch):
    with jobs.open_store(home) as store:
        job_id = find(store)
    real_write = images.write_files
    started = []

    def another_window_starts_first(media_root, blobs):  # the row is committed; files come next
        started.append(create_app(home, token='other'))
        return real_write(media_root, blobs)

    monkeypatch.setattr(jobs.images, 'write_files', another_window_starts_first)
    jobs.Worker(home, owner='A', fetcher=aic_fetcher(), backends={'fake': fake}).run_once(job_id)
    assert started
    with jobs.open_store(home) as store:
        job = store.one('SELECT state, message FROM jobs WHERE id=?', (job_id,))
        image = store.one('SELECT * FROM images WHERE removed_at IS NULL')
    assert job['state'] == 'done' and 'Added 1 image' in job['message']
    for key in ('original_path', 'analysis_path', 'thumb_path'):
        assert (home / 'media' / image[key]).is_file()


def test_abandoned_files_are_cleaned_up_only_when_no_worker_is_downloading(library):
    stray = library / 'media' / 'analysis' / 'ab' / ('ab' + '0' * 62 + '.jpg')
    stray.parent.mkdir(parents=True, exist_ok=True)
    stray.write_bytes(b'left by a crash')
    with jobs.open_store(library) as store:
        job_id = find(store, goal='lighthouse')
        store.claim_job('downloading', 60, job_id)  # a live lease: someone may be writing files right now
    assert transfer.sweep(library) is None and stray.is_file()
    with jobs.open_store(library) as store:
        store.update_job(job_id, None, lease_owner=None, lease_until=None)
    assert transfer.sweep(library) == 1 and not stray.exists()
