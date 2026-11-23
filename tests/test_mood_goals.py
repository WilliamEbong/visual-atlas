"""Mood goals: a brief that only names a feeling still gets a reading and references that serve it."""

import json

import pytest

from atlas import catalog, coding, desk, jobs, layers, transfer
from atlas.home import REPO

CHOIR = 'Poster for a community choir concert in a church, warm and communal'


@pytest.fixture(scope='module')
def starter_home(tmp_path_factory):
    home = tmp_path_factory.mktemp('mood') / 'home'
    with jobs.open_store(home) as store:
        transfer.import_starter(store, home, REPO / 'starter')
    return home


def test_choir_brief_reads_the_warm_goal():
    reading = coding.code_request(CHOIR, catalog.load()[0])
    assert 'feel-warm' in [g['id'] for g in reading['goals']]


def test_choir_brief_finds_references_that_serve_warmth(starter_home, monkeypatch, tmp_path):
    monkeypatch.delenv('VISUAL_ATLAS_DESIGN_SYSTEMS', raising=False)
    monkeypatch.setattr(layers, 'GENERATED', tmp_path / 'none')
    found = desk.search(brief=CHOIR, limit=12, home=starter_home)
    assert 'feel-warm' in [g['id'] for g in found['reading']['goals']]
    reasons = [reason for r in found['results'] for reason in r['reasons']]
    assert any(reason.startswith('Serves “Feel warm and welcoming”') for reason in reasons), reasons



def test_a_mood_is_served_only_by_pictures_that_carry_it(tmp_path, monkeypatch):
    home = tmp_path / 'home'
    with jobs.open_store(home) as store:
        transfer.import_starter(store, home, REPO / 'starter')
        rows = store.rows("SELECT provider, provider_item_id FROM images ORDER BY id LIMIT 2")
    warm = f"{rows[1]['provider']}:{rows[1]['provider_item_id']}"
    data = tmp_path / 'moods.json'
    data.write_text(json.dumps({'goals': ['feel-warm'], 'moods': {warm: ['feel-warm']}}), encoding='utf-8')
    monkeypatch.setattr(desk, 'MOODS', data)
    monkeypatch.delenv('VISUAL_ATLAS_DESIGN_SYSTEMS', raising=False)
    found = desk.search(goals=['feel-warm'], layers_wanted=['library'], home=home)['results']
    serving = [r for r in found if any(x.startswith('Serves') for x in r['reasons'])]
    assert [r['title'] for r in serving] == [found[0]['title']] and len(serving) == 1
