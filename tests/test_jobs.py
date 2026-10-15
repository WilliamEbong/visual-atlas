"""Jobs: discovery end to end (offline), leases, interruption and resume, cancel/pause, failures, budgets."""

import json
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

    monkeypatch.setattr(jobs, 'clock', fake_time)
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
        assert store.one("SELECT COUNT(*) AS n FROM attempts WHERE kind='ai' AND job_id=? AND item_id IS NOT NULL",
                         (job_id,))['n'] <= 2  # the planning call is not an image analysis
        assert store.one("SELECT COUNT(*) AS n FROM images WHERE status='pending'")['n'] == 0  # nothing left unanalysed
        message = store.one('SELECT message FROM jobs WHERE id=?', (job_id,))['message']
        assert "Stopped at this job's analysis limit (2)" in message  # not 'the searches ran out'


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


def test_a_verifier_error_keeps_the_proposal_and_the_job_going(home):
    with jobs.open_store(home) as store:
        job_id = find(store, verify_with='claude')
    broken_verifier = Flaky(fail_on={1, 2, 3, 4}, error=BackendError('provider_error'))
    jobs.Worker(home, owner='A', fetcher=aic_fetcher(), backends={'fake': fake, 'claude': broken_verifier}).run_once()
    with jobs.open_store(home) as store:
        assert store.one('SELECT state FROM jobs WHERE id=?', (job_id,))['state'] == 'done'
        assert {r['state'] for r in store.rows('SELECT state FROM annotations')} == {'proposed'}


def test_an_analysis_error_retries_that_picture_only(home, monkeypatch):
    clock = types.SimpleNamespace(now=1e9)
    monkeypatch.setattr(jobs, 'clock', lambda: setattr(clock, 'now', clock.now + 50) or clock.now)
    with jobs.open_store(home) as store:
        job_id = find(store)
    hiccup = Flaky(fail_on={2}, error=BackendError('provider_error'))  # first image's analysis fails once
    worker(home, 'A', hiccup).run_once()
    with jobs.open_store(home) as store:
        assert store.one('SELECT state FROM jobs WHERE id=?', (job_id,))['state'] == 'done'
        assert len(store.rows("SELECT * FROM job_items WHERE state='added'")) == 2


def test_pause_then_quick_resume_cannot_hand_a_live_job_to_a_second_worker(home):
    with jobs.open_store(home) as store:
        job_id = find(store)
        assert store.claim_job('A')['id'] == job_id
        store.request_job_state(job_id, 'pause')
        assert store.request_job_state(job_id, 'resume')['state'] == 'queued'
        assert store.claim_job('B') is None  # A still holds the lease until it really stops
        with pytest.raises(LeaseLost):
            store.add_analysis({'task': 'plan', 'backend': 'x', 'model': 'y', 'prompt_sha': 'p', 'taxonomy_sha': 't',
                                'input_sha': 'i', 'cache_key': 'c', 'result_json': '{}'}, fence=(job_id, 'B'))


def test_explicit_budgets_are_kept(home):
    with jobs.open_store(home) as store:
        job_id = find(store, target_new_images=1, budgets={'max_analyses': 1})
        spec = json.loads(store.one('SELECT spec_json FROM jobs WHERE id=?', (job_id,))['spec_json'])
        assert spec['budgets']['max_analyses'] == 1


def test_an_expired_lease_cannot_be_renewed_or_written_with(home):
    with jobs.open_store(home) as store:
        first, second = find(store), find(store)
        store.claim_job('A', job_id=first)
        store.update_job(first, None, lease_until=time.time() - 1)  # A stalled past its lease
        assert store.claim_job('B', job_id=second)['id'] == second
        with pytest.raises(LeaseLost):
            store.heartbeat(first, 'A')


def test_cancelling_a_paused_job_with_an_active_worker_lets_the_worker_stop(home):
    with jobs.open_store(home) as store:
        job_id = find(store)
        store.claim_job('A')
        store.request_job_state(job_id, 'pause')
        assert store.request_job_state(job_id, 'cancel')['state'] == 'cancelling'  # A still holds the lease
    worker(home, 'A').run_once(job_id)
    with jobs.open_store(home) as store:
        assert store.one('SELECT state FROM jobs WHERE id=?', (job_id,))['state'] == 'cancelled'
        assert store.rows('SELECT * FROM images') == []


def test_automatic_removal_never_takes_an_image_a_person_is_using(home):
    with jobs.open_store(home) as store:
        find(store, target_new_images=1)
    worker(home, 'A').run_once()
    with jobs.open_store(home) as store:
        image = store.one('SELECT * FROM images')
        board = store.create_collection('Mine')
        store.collect(board, image['id'])
        job_id = find(store)
        store.claim_job('W', job_id=job_id)
        with pytest.raises(ValueError, match='in use'):
            store.remove_image(image['id'], 'automatic', fence=(job_id, 'W'))


def test_slow_searches_and_downloads_keep_the_lease(home, monkeypatch):
    monkeypatch.setattr(jobs, 'LEASE_SECONDS', 0.6)
    monkeypatch.setattr(jobs, 'HEARTBEAT_SECONDS', 0.1)
    with jobs.open_store(home) as store:
        job_id = find(store)
    slow = worker(home, 'A')
    fetcher = slow.fetcher
    get_json, get_image = fetcher.get_json, fetcher.get_image

    def later(call):
        def wrapped(*args, **kwargs):
            time.sleep(0.8)  # each request outlasts the whole lease
            return call(*args, **kwargs)
        return wrapped

    fetcher.get_json, fetcher.get_image = later(get_json), later(get_image)
    slow.run_once()
    with jobs.open_store(home) as store:
        job = store.one('SELECT * FROM jobs WHERE id=?', (job_id,))
        assert job['state'] == 'done' and 'Added 2 images' in job['message']


def test_a_cancel_that_arrives_while_resuming_is_kept(home):
    with jobs.open_store(home) as store:
        job_id = find(store)
    racing = worker(home, 'A')
    read_state = racing._job
    raced = []

    def resumed_then_cancelled():
        if not raced:
            raced.append(True)
            with jobs.open_store(home) as other:
                other.request_job_state(job_id, 'pause')
                other.request_job_state(job_id, 'resume')
                job = read_state()  # the worker sees 'queued'...
                other.request_job_state(job_id, 'cancel')  # ...and a cancel lands before it acts on that
                return job
        return read_state()

    racing._job = resumed_then_cancelled
    racing.run_once(job_id)
    with jobs.open_store(home) as store:
        assert store.one('SELECT state FROM jobs WHERE id=?', (job_id,))['state'] == 'cancelled'
        assert store.rows('SELECT * FROM images') == []


def held_worker(home, monkeypatch):
    """A worker holding a fresh job with pending steps for two providers (for retry scheduling)."""
    monkeypatch.setattr(jobs, 'clock', lambda: 1_000_000.0)
    with jobs.open_store(home) as store:
        job_id = find(store)
        store.claim_job('A', 60, job_id)
        store.add_items(job_id, 'A', [
            {'kind': 'query', 'key': f'{provider}:{query}', 'provider': provider, 'payload': {'query': query}}
            for provider, query in (('aic', 'a'), ('aic', 'b'), ('met', 'c'))] + [
            {'kind': 'candidate', 'key': key, 'provider': 'aic', 'payload': {}, 'state': state}
            for key, state in (('aic:1', 'eligible'), ('aic:2', 'found'))])
    held = worker(home, 'A')
    held.store, held.job, held.spec = jobs.open_store(home), {'id': job_id}, {}
    return held


def schedule(held):
    return {r['key']: (r['next_attempt_at'], r['reason']) for r in held.store.rows('SELECT * FROM job_items')}


@pytest.mark.parametrize(('retry_after', 'wait'), [(600, 600), (3, 10), (None, 10)])
def test_retry_after_holds_the_item_and_every_network_step_for_that_provider(home, monkeypatch, retry_after, wait):
    held = held_worker(home, monkeypatch)
    item = held.store.one("SELECT * FROM job_items WHERE key='aic:a'")
    held._retry_or_fail(item, 'rate_limited', 'AIC asked us to slow down.', retry_after)
    times = {key: value[0] for key, value in schedule(held).items()}
    assert times['aic:a'] == times['aic:b'] == times['aic:1'] == 1_000_000 + wait  # never sooner than asked
    assert times['met:c'] == 0 and times['aic:2'] == 0  # other providers and offline checks are not held up


def test_a_very_long_provider_wait_is_capped_and_reported(home, monkeypatch):
    held = held_worker(home, monkeypatch)
    item = held.store.one("SELECT * FROM job_items WHERE key='aic:a'")
    held._retry_or_fail(item, 'rate_limited', 'AIC asked us to slow down.', 7200)
    when, reason = schedule(held)['aic:a']
    assert when == 1_000_000 + 3600 and '120 minutes' in reason


def test_default_budgets_can_reach_the_largest_request(home):
    with jobs.open_store(home) as store:
        spec = json.loads(store.one('SELECT spec_json FROM jobs WHERE id=?', (find(store, target_new_images=40),))
                          ['spec_json'])
    assert spec['budgets']['max_downloads'] >= 40 and spec['budgets']['max_analyses'] >= 40
    assert spec['budgets']['max_candidates'] >= spec['budgets']['max_downloads'] and spec['per_query'] == 20


def test_a_budget_stop_is_reported_as_a_budget_not_as_running_out(home):
    with jobs.open_store(home) as store:
        job_id = find(store, target_new_images=5, budgets={'max_analyses': 1})
    worker(home, 'A').run_once()
    with jobs.open_store(home) as store:
        message = store.one('SELECT message FROM jobs WHERE id=?', (job_id,))['message']
    assert "Stopped at this job's analysis limit (1)" in message and 'ran out' not in message


def test_a_spent_budget_ends_the_job_instead_of_waiting_for_a_slow_source(home, monkeypatch):
    held = held_worker(home, monkeypatch)
    job_id = held.job['id']
    held.job = held.store.one('SELECT * FROM jobs WHERE id=?', (job_id,))
    held.spec = {'target_new_images': 3, 'budgets': {'max_analyses': 1}}
    item = held.store.one("SELECT id FROM job_items WHERE key='aic:1'")['id']
    held.store.record_attempt({'job_id': job_id, 'item_id': item, 'kind': 'ai', 'backend': held.job['backend'],
                               'status': 'ok'})
    held.store.delay_provider(job_id, 'A', 'aic', 1_000_000 + 3000)  # a source asked for a long wait
    held._discovery_step()
    job = held.store.one('SELECT state, message FROM jobs WHERE id=?', (job_id,))
    assert job['state'] == 'done' and "Stopped at this job's analysis limit (1)" in job['message']


def test_waiting_only_for_a_slow_source_says_so(home, monkeypatch):
    held = held_worker(home, monkeypatch)
    job_id = held.job['id']
    held.job = held.store.one('SELECT * FROM jobs WHERE id=?', (job_id,))
    with held.store.transaction():
        held.store.connection.execute("UPDATE job_items SET state='skipped' WHERE kind='candidate'")
        held.store.connection.execute("UPDATE job_items SET next_attempt_at=? WHERE kind='query'", (1_000_000 + 600,))
    assert held._discovery_step() is None
    message = held.store.one('SELECT message FROM jobs WHERE id=?', (job_id,))['message']
    assert message.startswith('Waiting for Art Institute of Chicago') and 'about 10 minutes' in message
