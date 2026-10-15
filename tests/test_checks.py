"""Second-model checks report what really happened, and re-analysis keeps an image's labels coherent."""

import itertools
import json

import pytest
from helpers import aic_fetcher

from atlas import jobs
from atlas.ai import fake
from atlas.ai.process import BackendError


class Verifier:
    """A checking assistant that fails in a chosen way (or answers like the practice backend)."""
    NAME = 'claude'

    def __init__(self, *failures, answer=None):
        self.failures = list(failures)
        self.answer = answer
        self.calls = 0

    def check(self, runner=None, force=False):
        return 'test'

    def run(self, prompt, schema, images, **kwargs):
        self.calls += 1
        if self.failures:
            failure = self.failures.pop(0)
            if callable(failure):
                failure = failure()
            if isinstance(failure, BaseException):
                raise failure
        if self.answer is not None:
            return {'result': self.answer, 'input_tokens': 1, 'output_tokens': 1, 'cli_version': 't'}
        return fake.run(prompt, schema, images, **kwargs)


@pytest.fixture(autouse=True)
def fast_clock(monkeypatch):
    """Retry back-off runs on jobs.clock; each reading moves it on by ten minutes so waits pass at once."""
    ticks = itertools.count()
    monkeypatch.setattr(jobs, 'clock', lambda: 1_800_000_000 + 600 * next(ticks))


def library(home, count=1):
    """Images analysed by the practice backend (as 'codex'), with proposals waiting for a check."""
    with jobs.open_store(home) as store:
        job_id = jobs.create_job(store, 'find', {'goal': 'harbour', 'providers': ['aic'], 'backend': 'codex',
                                                 'target_new_images': count})
    jobs.Worker(home, owner='seed', fetcher=aic_fetcher(), backends={'codex': fake}).run_once(job_id)
    with jobs.open_store(home) as store:
        return [row['id'] for row in store.rows('SELECT id FROM images WHERE removed_at IS NULL ORDER BY id')]


def verify(home, ids, verifier):
    with jobs.open_store(home) as store:
        job_id = jobs.create_job(store, 'verify', {'image_ids': ids, 'backend': 'claude'})
    jobs.Worker(home, owner='v', fetcher=aic_fetcher(), backends={'claude': verifier, 'codex': fake},
                sleep=lambda _: None).run_once(job_id)
    return job_id


def outcome(home, job_id):
    with jobs.open_store(home) as store:
        return (store.one('SELECT state, message, error_code FROM jobs WHERE id=?', (job_id,)),
                store.rows('SELECT state, reason FROM job_items WHERE job_id=?', (job_id,)),
                store.one("SELECT COUNT(*) AS n FROM analyses WHERE task='verify'")['n'],
                [r['state'] for r in store.rows('SELECT state FROM annotations ORDER BY id')])


def test_a_verifier_over_its_limit_pauses_the_check_and_resume_finishes_it(home):
    ids = library(home)
    job_id = verify(home, ids, Verifier(BackendError('quota')))
    job, items, saved, states = outcome(home, job_id)
    assert job['state'] == 'paused' and job['error_code'] == 'quota' and 'usage limit' in job['message']
    assert items[0]['state'] != 'added' and saved == 0 and set(states) == {'proposed'}
    with jobs.open_store(home) as store:
        store.request_job_state(job_id, 'resume')
    jobs.Worker(home, owner='v2', fetcher=aic_fetcher(), backends={'claude': Verifier(), 'codex': fake}).run_once(job_id)
    job, items, saved, states = outcome(home, job_id)
    assert job['state'] == 'done' and 'Checked 1 of 1 image' in job['message']
    assert items == [{'state': 'added', 'reason': 'checked'}] and saved == 1 and 'model_reviewed' in states


def test_timeouts_retry_then_report_the_image_as_not_checked(home):
    ids = library(home)
    job_id = verify(home, ids, Verifier(*[BackendError('timeout')] * 6))
    job, items, saved, states = outcome(home, job_id)
    assert job['state'] == 'done' and 'Checked 0 of 1 image' in job['message'] and 'could not be checked' in job['message']
    assert items[0]['state'] == 'failed' and saved == 0 and set(states) == {'proposed'}


def test_a_malformed_answer_is_recorded_and_never_counts_as_checked(home):
    ids = library(home)
    job_id = verify(home, ids, Verifier(answer={'verdicts': []}))
    job, items, saved, _ = outcome(home, job_id)
    assert items[0]['state'] == 'failed' and saved == 0 and 'Checked 0 of 1' in job['message']
    with jobs.open_store(home) as store:
        codes = [r['error_code'] for r in store.rows("SELECT error_code FROM attempts WHERE job_id=? AND kind='ai'",
                                                     (job_id,))]
    assert codes and set(codes) == {'invalid_response'}  # every bad answer is visible in the attempt ledger


def test_a_pause_mid_check_leaves_the_image_to_check_later(home):
    ids = library(home)

    def person_pauses():  # the user presses Pause while the assistant is answering; the call is stopped
        with jobs.open_store(home) as store:
            store.request_job_state(store.one("SELECT id FROM jobs WHERE kind='verify'")['id'], 'pause')
        return BackendError('cancelled')

    job_id = verify(home, ids, Verifier(person_pauses))
    job, items, saved, _ = outcome(home, job_id)
    assert job['state'] == 'paused' and items[0]['state'] == 'pending' and saved == 0


def test_a_missing_image_file_is_reported_not_checked(home):
    ids = library(home)
    with jobs.open_store(home) as store:
        path = store.one('SELECT analysis_path FROM images WHERE id=?', (ids[0],))['analysis_path']
    (home / 'media' / path).unlink()
    job_id = verify(home, ids, Verifier())
    job, items, saved, _ = outcome(home, job_id)
    assert items[0]['state'] == 'skipped' and 'missing' in items[0]['reason'] and saved == 0


def test_an_unavailable_verifier_never_discards_a_found_image(home):
    verifier = Verifier(*[BackendError('quota')] * 10)
    with jobs.open_store(home) as store:
        job_id = jobs.create_job(store, 'find', {'goal': 'harbour', 'providers': ['aic'], 'backend': 'codex',
                                                 'verify_with': 'claude', 'target_new_images': 2})
    jobs.Worker(home, owner='w', fetcher=aic_fetcher(), backends={'codex': fake, 'claude': verifier}).run_once(job_id)
    with jobs.open_store(home) as store:
        job = store.one('SELECT state, message FROM jobs WHERE id=?', (job_id,))
        added = store.rows("SELECT reason, payload_json FROM job_items WHERE job_id=? AND state='added'", (job_id,))
    assert job['state'] == 'done' and len(added) == 2
    assert {json.loads(r['payload_json'])['check'] for r in added} == {'unavailable'}
    assert all('not checked' in r['reason'] for r in added)
    assert 'not checked by a second model' in job['message']
    assert verifier.calls == 1  # once it is known to be unavailable, the job stops asking


def test_a_check_never_touches_a_persons_decisions(home):
    ids = library(home)
    with jobs.open_store(home) as store:
        first = store.one('SELECT technique_id FROM annotations ORDER BY id')['technique_id']
        store.human_annotation(ids[0], first, state='rejected', note='not this')
    verify(home, ids, Verifier())
    with jobs.open_store(home) as store:
        row = store.one('SELECT state, human_locked, note FROM annotations WHERE technique_id=?', (first,))
    assert (row['state'], row['human_locked'], row['note']) == ('rejected', 1, 'not this')


def analysis(store, image_id, backend='codex'):
    import os
    return store.add_analysis({'image_id': image_id, 'task': 'analyze', 'backend': backend, 'model': 'm',
                               'prompt_sha': 'p', 'taxonomy_sha': 't', 'input_sha': 'i',
                               'cache_key': os.urandom(8).hex(), 'result_json': '{}'})


def proposals(ids, confidence=.8):
    return [{'technique_id': t, 'evidence': ['seen'], 'effect': 'may', 'confidence': confidence,
             'role': 'supporting'} for t in ids]


def test_reanalysis_supersedes_what_the_newer_analysis_omits(home):
    image_id = library(home)[0]
    with jobs.open_store(home) as store:
        techniques = [r['id'] for r in store.rows('SELECT id FROM techniques ORDER BY id')]
        store.human_annotation(image_id, techniques[10], state='human_reviewed', evidence=['a person saw it'])
        store.human_annotation(image_id, techniques[11], state='rejected')
        store.apply_analysis(image_id, analysis(store, image_id), proposals(techniques[:4]), 'model:codex/m')
        latest = analysis(store, image_id)
        result = store.apply_analysis(image_id, latest, proposals(techniques[4:7]), 'model:codex/m')
        active = {r['technique_id']: r['state'] for r in store.rows('SELECT * FROM annotations WHERE image_id=?',
                                                                       (image_id,))}
        image = store.one('SELECT status, analysis_id FROM images WHERE id=?', (image_id,))
        history = store.rows("SELECT technique_id, analysis_id FROM annotation_history WHERE state='superseded' "
                             "AND analysis_id=?", (latest,))
    assert active == {**{t: 'proposed' for t in techniques[4:7]}, techniques[10]: 'human_reviewed',
                      techniques[11]: 'rejected'}
    assert set(result['superseded']) >= set(techniques[:4]) and image == {'status': 'ready', 'analysis_id': latest}
    assert {h['technique_id'] for h in history} == set(techniques[:4])  # each names the analysis that replaced it


def test_an_empty_or_unusable_reanalysis_leaves_only_a_persons_labels(home):
    image_id = library(home)[0]
    with jobs.open_store(home) as store:
        store.apply_analysis(image_id, analysis(store, image_id), [], 'model:codex/m')
        assert store.rows("SELECT * FROM annotations WHERE image_id=? AND state!='rejected'", (image_id,)) == []
        assert store.one('SELECT status FROM images WHERE id=?', (image_id,))['status'] == 'unanalyzed'
        technique = store.one('SELECT id FROM techniques ORDER BY id')['id']
        store.human_annotation(image_id, technique, state='human_reviewed', evidence=['visible'])
        store.apply_analysis(image_id, analysis(store, image_id), [], 'model:codex/m')
        assert store.one('SELECT status FROM images WHERE id=?', (image_id,))['status'] == 'ready'


def test_any_number_of_waiting_proposals_is_checked_in_batches(home):
    image_id = library(home)[0]
    verifier = Verifier()
    with jobs.open_store(home) as store:
        techniques = [r['id'] for r in store.rows('SELECT id FROM techniques ORDER BY id')][:9]
        for technique in techniques:  # as an upgraded 0.1 library could have: nine waiting proposals
            store.connection.execute(
                "INSERT OR REPLACE INTO annotations(image_id,technique_id,state,role,evidence_json,effect,confidence,"
                "analysis_id,human_locked,changed_by,updated_at) VALUES(?,?,'proposed','supporting','[\"x\"]','may',.8,"
                "(SELECT analysis_id FROM images WHERE id=?),0,'model:codex/m','2026')", (image_id, technique, image_id))
        store.connection.commit()
    job_id = verify(home, [image_id], verifier)
    job, items, saved, _ = outcome(home, job_id)
    assert verifier.calls == 2 and saved == 2 and items[0]['state'] == 'added'
    with jobs.open_store(home) as store:
        waiting = store.rows("SELECT 1 FROM annotations WHERE image_id=? AND state='proposed' AND note=''", (image_id,))
    assert waiting == []  # every proposal was judged


def test_a_verifier_unavailable_in_one_job_is_asked_again_in_the_next(home):
    verifier = Verifier(BackendError('quota'))  # over its limit once, then fine
    worker = jobs.Worker(home, owner='app', fetcher=aic_fetcher(), backends={'codex': fake, 'claude': verifier})
    outcomes = []
    for goal in ('harbour', 'lighthouse'):
        with jobs.open_store(home) as store:
            job_id = jobs.create_job(store, 'find', {'goal': goal, 'providers': ['aic'], 'backend': 'codex',
                                                     'verify_with': 'claude', 'target_new_images': 1})
        worker.run_once(job_id)  # the app reuses one worker for every job
        with jobs.open_store(home) as store:
            outcomes += [json.loads(r['payload_json'])['check'] for r in store.rows(
                "SELECT payload_json FROM job_items WHERE job_id=? AND state='added'", (job_id,))]
    assert outcomes == ['unavailable', 'checked'] and verifier.calls == 2


def crash_once(monkeypatch, name, when=lambda *a, **k: True):
    real = getattr(jobs.Worker, name)
    crashed = []

    def wrapper(self, *args, **kwargs):
        if not crashed and when(*args, **kwargs):
            crashed.append(1)
            raise RuntimeError('power cut after the check was saved')
        return real(self, *args, **kwargs)
    monkeypatch.setattr(jobs.Worker, name, wrapper)


def resume(home, job_id, backends):
    with jobs.open_store(home) as store:
        store.update_job(job_id, None, lease_until=0)  # the crashed worker's lease runs out
    jobs.Worker(home, owner='again', fetcher=aic_fetcher(), backends=backends).run_once(job_id)


def test_a_saved_check_still_counts_after_a_crash_in_a_verify_job(home, monkeypatch):
    ids = library(home)
    crash_once(monkeypatch, '_item', lambda item_id, **changes: changes.get('reason') == 'checked')
    with jobs.open_store(home) as store:
        job_id = jobs.create_job(store, 'verify', {'image_ids': ids, 'backend': 'claude'})
    with pytest.raises(RuntimeError):
        jobs.Worker(home, owner='v', fetcher=aic_fetcher(), backends={'claude': Verifier(), 'codex': fake}).run_once(job_id)
    resume(home, job_id, {'claude': Verifier(), 'codex': fake})
    job, items, saved, _ = outcome(home, job_id)
    assert saved == 1 and items == [{'state': 'added', 'reason': 'checked'}] and 'Checked 1 of 1' in job['message']


def test_a_saved_check_still_counts_after_a_crash_in_a_find_job(home, monkeypatch):
    crash_once(monkeypatch, '_added_item')
    with jobs.open_store(home) as store:
        job_id = jobs.create_job(store, 'find', {'goal': 'harbour', 'providers': ['aic'], 'backend': 'codex',
                                                 'verify_with': 'claude', 'target_new_images': 1})
    with pytest.raises(RuntimeError):
        jobs.Worker(home, owner='f', fetcher=aic_fetcher(), backends={'codex': fake, 'claude': Verifier()}).run_once(job_id)
    resume(home, job_id, {'codex': fake, 'claude': Verifier()})
    with jobs.open_store(home) as store:
        added = store.rows("SELECT payload_json FROM job_items WHERE job_id=? AND state='added'", (job_id,))
        checks = store.one("SELECT COUNT(*) AS n FROM analyses WHERE task='verify'")['n']
    assert [json.loads(r['payload_json'])['check'] for r in added] == ['checked'] and checks == 1
