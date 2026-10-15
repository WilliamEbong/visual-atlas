"""Jobs: discovery end to end (offline), leases, interruption and resume, cancel/pause, failures, budgets."""

import time
import types

import pytest
from helpers import aic_fetcher

from atlas import jobs
from atlas.ai import fake
from atlas.ai.process import BackendError
from atlas.store import LeaseLost


def find(store, **spec):
    return jobs.create_job(store, 'find', {'goal': 'harbour', 'providers': ['aic'], 'backend': 'fake',
                                           'target_new_images': 2, **spec})


class Flaky:
    """A backend that behaves like the practice backend but can fail on chosen calls."""
    NAME = 'flaky'

    def __init__(self, fail_on=(), error=None):
        self.calls = 0
        self.fail_on = set(fail_on)
        self.error = error or RuntimeError('power cut')

    def check(self, runner=None, force=False):
        return 'test'

    def run(self, prompt, schema, images, **kwargs):
        self.calls += 1
        if self.calls in self.fail_on:
            raise self.error
        return fake.run(prompt, schema, images, **kwargs)


def worker(home, owner, backend=None, **fetch):
    return jobs.Worker(home, owner=owner, fetcher=aic_fetcher(**fetch), backends={'fake': backend or fake})


def test_find_adds_licence_checked_analysed_images(home):
    with jobs.open_store(home) as store:
        job_id = find(store)
    assert worker(home, 'A').run_once() == job_id
    with jobs.open_store(home) as store:
        job = store.one('SELECT * FROM jobs WHERE id=?', (job_id,))
        assert job['state'] == 'done' and 'Added 2 images' in job['message']
        images = store.rows('SELECT * FROM images WHERE removed_at IS NULL')
        assert len(images) == 2
        for image in images:
            rights = store.one('SELECT * FROM rights_records WHERE image_id=?', (image['id'],))
            assert rights['label'] == 'CC0 — source checked' and rights['evidence_url'].startswith('https://www.artic.edu/')
            assert (home / 'media' / image['original_path']).is_file() and image['status'] == 'ready'
        assert len(store.rows("SELECT * FROM analyses WHERE task='analyze'")) == 2
        assert store.one("SELECT COUNT(*) AS n FROM attempts WHERE kind='search'")['n'] >= 1


def test_second_worker_cannot_take_a_live_job(home):
    with jobs.open_store(home) as store:
        job_id = find(store)
        assert store.claim_job('A')['id'] == job_id
        assert store.claim_job('B') is None
        store.update_job(job_id, None, lease_until=time.time() - 1)  # A disappears; its lease expires
        assert store.claim_job('B')['lease_owner'] == 'B'
        with pytest.raises(LeaseLost):
            store.update_item(job_id, 'A', 1, state='skipped')  # the stale worker is fenced out


def test_interrupted_job_resumes_without_repeating_finished_work(home):
    with jobs.open_store(home) as store:
        job_id = find(store, target_new_images=3)
    crashing = Flaky(fail_on={3})  # call 1 = plan, 2 = first image, 3 = crash during the second image
    with pytest.raises(RuntimeError):
        worker(home, 'A', crashing).run_once()
    with jobs.open_store(home) as store:
        assert store.one('SELECT state FROM jobs')['state'] == 'running'
        assert store.claim_job('B') is None  # lease still held by the crashed worker
        store.update_job(job_id, None, lease_until=0)
        first = store.one("SELECT image_id FROM job_items WHERE state='added'")['image_id']
    resumed = Flaky()
    worker(home, 'B', resumed).run_once()
    with jobs.open_store(home) as store:
        assert store.one('SELECT state FROM jobs')['state'] == 'done'
        added = [r['image_id'] for r in store.rows("SELECT image_id FROM job_items WHERE state='added'")]
        assert len(added) == 3 and first in added
        per_image = store.rows("SELECT image_id, COUNT(*) AS n FROM analyses WHERE task='analyze' GROUP BY image_id")
        assert all(row['n'] == 1 for row in per_image)  # nothing analysed twice
        assert len(store.rows("SELECT * FROM analyses WHERE task='plan'")) == 1  # planning not repeated
    assert resumed.calls == 2


def test_cancel_and_pause(home):
    with jobs.open_store(home) as store:
        queued = find(store)
        assert store.request_job_state(queued, 'cancel')['state'] == 'cancelled'
        running = find(store)
        store.claim_job('A')
        assert store.request_job_state(running, 'cancel')['state'] == 'cancelling'
        store.update_job(running, None, lease_until=0)
    worker(home, 'A').run_once(running)
    with jobs.open_store(home) as store:
        assert store.one('SELECT state FROM jobs WHERE id=?', (running,))['state'] == 'cancelled'
        paused = find(store)
        assert store.request_job_state(paused, 'pause')['state'] == 'paused'
        assert store.claim_job('A', job_id=paused) is None  # paused jobs are not picked up
        assert store.request_job_state(paused, 'resume')['state'] == 'queued'


def test_usage_limit_pauses_with_a_plain_message(home):
    with jobs.open_store(home) as store:
        job_id = find(store)
    limited = Flaky(fail_on={2}, error=BackendError('quota'))
    worker(home, 'A', limited).run_once()
    with jobs.open_store(home) as store:
        job = store.one('SELECT * FROM jobs WHERE id=?', (job_id,))
        assert job['state'] == 'paused' and 'usage limit' in job['message'] and job['lease_owner'] is None
        assert store.one("SELECT COUNT(*) AS n FROM attempts WHERE status='error' AND error_code='quota'")['n'] == 1


def test_unavailable_planner_falls_back_to_taxonomy_hints(home):
    with jobs.open_store(home) as store:
        job_id = find(store, goal='negative space and fog')
    worker(home, 'A', Flaky(fail_on={1}, error=BackendError('timeout'))).run_once()
    with jobs.open_store(home) as store:
        queries = store.rows("SELECT json_extract(payload_json,'$.technique_id') AS t FROM job_items WHERE kind='query'")
        assert any(q['t'] == 'negative-space' for q in queries)
        assert store.one('SELECT state FROM jobs WHERE id=?', (job_id,))['state'] == 'done'


def test_failed_downloads_retry_then_give_up(home, monkeypatch):
    clock = types.SimpleNamespace(now=1e9)

    def fake_time():
        clock.now += 50
        return clock.now

    monkeypatch.setattr(jobs.time, 'time', fake_time)
    with jobs.open_store(home) as store:
        job_id = find(store)
    failing = {'0558d3c0-dd86-7d26-2e55-126c1470ca41'}
    worker(home, 'A', fail_images=failing).run_once()
    with jobs.open_store(home) as store:
        failed = store.one("SELECT * FROM job_items WHERE state='failed'")
        assert failed['attempts'] == 3 and 'slow down' in failed['reason']
        assert store.one('SELECT state FROM jobs WHERE id=?', (job_id,))['state'] == 'done'


def test_budgets_stop_the_job(home):
    with jobs.open_store(home) as store:
        job_id = store.create_job('budget', 'find', {'goal': 'harbour', 'providers': ['aic'], 'target_new_images': 5,
                                                      'budgets': {'max_analyses': 2}}, 'fake', 'practice')
    worker(home, 'A').run_once()
    with jobs.open_store(home) as store:
        assert store.one("SELECT COUNT(*) AS n FROM attempts WHERE kind='ai' AND job_id=?", (job_id,))['n'] <= 2
        assert store.one("SELECT COUNT(*) AS n FROM job_items WHERE reason='analysis budget reached'")['n'] >= 1


def test_removed_images_are_never_collected_again(home):
    with jobs.open_store(home) as store:
        find(store, target_new_images=1)
    worker(home, 'A').run_once()
    with jobs.open_store(home) as store:
        image = store.one('SELECT * FROM images')
        store.remove_image(image['id'], 'not for me')
        find(store, target_new_images=1)
    worker(home, 'A').run_once()
    with jobs.open_store(home) as store:
        ids = [r['provider_item_id'] for r in store.rows('SELECT provider_item_id FROM images WHERE removed_at IS NULL')]
        assert image['provider_item_id'] not in ids


def test_reanalysis_preserves_a_persons_corrections(home):
    with jobs.open_store(home) as store:
        find(store, target_new_images=1)
    worker(home, 'A').run_once()
    with jobs.open_store(home) as store:
        image = store.one('SELECT id FROM images')['id']
        technique = store.one('SELECT technique_id FROM annotations')['technique_id']
        store.human_annotation(image, technique, state='rejected', note='I disagree')
        jobs.create_job(store, 'analyze', {'image_ids': [image], 'backend': 'fake'})
    worker(home, 'A').run_once()
    with jobs.open_store(home) as store:
        row = store.one('SELECT * FROM annotations WHERE technique_id=?', (technique,))
        assert row['state'] == 'rejected' and row['note'] == 'I disagree'


def test_job_requests_are_validated(home):
    with jobs.open_store(home) as store:
        for kind, spec in (('find', {}), ('find', {'goal': 'x', 'target_new_images': 99}), ('find', {'goal': 'x', 'providers': ['nowhere']}),
                           ('find', {'goal': 'x', 'technique_ids': ['made-up']}), ('compare', {'image_ids': [1]}),
                           ('directions', {'brief_id': 404}), ('explode', {}), ('find', {'goal': 'x', 'backend': 'gpt-shell'})):
            with pytest.raises(ValueError):
                jobs.create_job(store, kind, spec)
        grow = jobs.create_job(store, 'grow', {'backend': 'fake'})
        spec = store.one('SELECT spec_json FROM jobs WHERE id=?', (grow,))['spec_json']
        assert '"technique_ids"' in spec
