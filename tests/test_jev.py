"""The optional Jev ranking: off by default, the person's own key, text only, and a working fallback."""

import json

import httpx
import pytest
from fastapi.testclient import TestClient
from test_coding import add

from atlas import jobs
from atlas.ai import fake, jev
from atlas.server import create_app

KEY = 'test-key-not-real'


def answering(scores: dict, calls: list, status=200):
    def handler(request: httpx.Request):
        calls.append(request)
        if status != 200:
            return httpx.Response(status, json={'error': 'nope'})
        questions = json.loads(request.content)['questions']
        return httpx.Response(200, json={'model': 'jev-1.13.0', 'usage': {'input_tokens': 100, 'output_tokens': 0},
                                         'answers': {k: {'type': 'noul', 'noul': scores.get(k, .1)} for k in questions}})
    return httpx.MockTransport(handler)


@pytest.fixture
def library(home):
    with jobs.open_store(home) as store:
        ids = [add(store, number, technique) for number, technique in
               ((1, 'silhouette'), (2, 'framing'), (3, 'symmetry'), (4, 'framing'))]
        brief = store.save_brief('Evening poster', 'Silhouettes against an evening sky.')
    return home, ids, brief


def run_directions(home, brief):
    with jobs.open_store(home) as store:
        job_id = jobs.create_job(store, 'directions', {'brief_id': brief, 'backend': 'fake'})
    jobs.Worker(home, owner='d', backends={'fake': fake}).run_once(job_id)
    with jobs.open_store(home) as store:
        analysis = store.one("SELECT result_json FROM analyses WHERE task='directions' ORDER BY id DESC LIMIT 1")
        job = store.one('SELECT state FROM jobs WHERE id=?', (job_id,))
        attempts = store.rows("SELECT status, error_code FROM attempts WHERE backend='jev'")
    return job, json.loads(analysis['result_json']), attempts


def test_off_by_default_even_with_a_key(library, monkeypatch):
    home, _, brief = library
    monkeypatch.setenv('TYPESAFE_API_KEY', KEY)
    monkeypatch.setattr(jev, 'rank', lambda *a, **k: pytest.fail('Jev must not be called unless switched on'))
    job, result, attempts = run_directions(home, brief)
    assert job['state'] == 'done' and result['ranking'] == {'method': 'deterministic'} and attempts == []


def test_switched_on_jev_reorders_the_references_and_records_provenance(library, monkeypatch):
    home, ids, brief = library
    monkeypatch.setenv('TYPESAFE_API_KEY', KEY)
    calls = []
    real = jev.rank
    monkeypatch.setattr(jev, 'rank', lambda *a, **k: real(*a, **k, transport=answering({f'r:{ids[3]}': .9}, calls)))
    with jobs.open_store(home) as store:
        store.set_setting('jev_ranking', '1')
    job, result, attempts = run_directions(home, brief)
    assert job['state'] == 'done' and result['ranking']['method'] == 'jev' and attempts == [{'status': 'ok',
                                                                                            'error_code': None}]
    assert result['ranking']['question_sha'] == jev.QUESTION_SHA and result['ranking']['model'] == 'jev-1.13.0'
    sent = json.loads(calls[0].content)
    assert calls[0].headers['authorization'] == f'Bearer {KEY}' and calls[0].url == jev.URL
    assert 'Silhouettes' in sent['state'] and all('Reference: ' in q['instructions'] for q in sent['questions'].values())


def test_a_failing_jev_falls_back_to_the_built_in_ranking(library, monkeypatch):
    home, _, brief = library
    monkeypatch.setenv('TYPESAFE_API_KEY', KEY)
    real = jev.rank
    monkeypatch.setattr(jev, 'rank', lambda *a, **k: real(*a, **k, transport=answering({}, [], status=503),
                                                          sleep=lambda _: None))
    with jobs.open_store(home) as store:
        store.set_setting('jev_ranking', '1')
    job, result, attempts = run_directions(home, brief)
    assert job['state'] == 'done' and result['ranking'] == {'method': 'deterministic', 'jev_error': 'http_503'}
    assert attempts == [{'status': 'error', 'error_code': 'http_503'}]


def test_bad_keys_and_bad_answers_raise_short_codes_without_secrets():
    records = [{'image_id': 1, 'title': 't', 'creator': '', 'date': '', 'summary': '', 'techniques': []}]
    calls = []
    with pytest.raises(jev.JevError) as error:
        jev.rank('brief', records, {}, KEY, transport=answering({}, calls, status=401))
    assert error.value.code == 'auth' and len(calls) == 1 and KEY not in str(error.value)  # no retry on a bad key

    def wrong_keys(request):
        return httpx.Response(200, json={'answers': {'r:999': {'noul': .5}}})
    with pytest.raises(jev.JevError, match='invalid_response'):
        jev.rank('brief', records, {}, KEY, transport=httpx.MockTransport(wrong_keys))


def test_settings_say_whether_a_key_exists_but_never_return_it(home, monkeypatch):
    monkeypatch.setenv('TYPESAFE_API_KEY', KEY)
    client = TestClient(create_app(home, token='t'), base_url='http://127.0.0.1')
    settings = client.get('/api/settings', headers={'X-Atlas-Token': 't'})
    assert settings.json()['jev_key'] is True and settings.json()['jev_ranking'] is False and KEY not in settings.text
