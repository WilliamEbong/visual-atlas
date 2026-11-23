"""Each technique leads with its chosen strongest example; a picture the person confirmed still comes first."""

import json

from fastapi.testclient import TestClient

from atlas import jobs, server, transfer
from atlas.home import REPO
from atlas.server import create_app

TOKEN = 'test-token'


def test_chosen_lead_comes_first_on_the_technique_page_and_index(tmp_path, monkeypatch):
    home = tmp_path / 'home'
    with jobs.open_store(home) as store:
        transfer.import_starter(store, home, REPO / 'starter')
        rows = store.rows("SELECT i.provider, i.provider_item_id, i.thumb_path FROM annotations a JOIN images i "
                          "ON i.id=a.image_id WHERE a.technique_id='negative-space' AND a.state!='rejected'")
    last = rows[-1]
    leads = tmp_path / 'leads.json'
    leads.write_text(json.dumps({'leads': {'negative-space': [f"{last['provider']}:{last['provider_item_id']}"]}}), encoding='utf-8')
    monkeypatch.setattr(server, 'LEADS', leads)
    client = TestClient(create_app(home, token=TOKEN, dist=tmp_path / 'dist'), base_url='http://127.0.0.1:8775',
                        headers={'x-atlas-token': TOKEN})
    first = client.get('/api/techniques/negative-space').json()['examples'][0]
    assert first['thumb'].endswith(last['thumb_path'].split('/')[-1])
    thumb = next(t for t in client.get('/api/taxonomy').json()['techniques'] if t['id'] == 'negative-space')['thumb']
    assert thumb == first['thumb']


def test_example_brief_resolves_its_pictures_in_this_library(tmp_path, monkeypatch):
    home = tmp_path / 'home'
    with jobs.open_store(home) as store:
        transfer.import_starter(store, home, REPO / 'starter')
        row = store.one('SELECT provider, provider_item_id FROM images LIMIT 1')
    client = TestClient(create_app(home, token=TOKEN, dist=tmp_path / 'dist'), base_url='http://127.0.0.1:8775',
                        headers={'x-atlas-token': TOKEN})
    monkeypatch.setattr(server, 'EXAMPLE', tmp_path / 'none.json')
    assert client.get('/api/briefs/example').status_code == 404
    example = tmp_path / 'example.json'
    example.write_text(json.dumps({'title': 'T', 'text': 'B', 'backend': 'codex', 'model': 'm', 'made': '2026-11-23',
                                   'directions': [{'title': 'D', 'idea': 'i', 'rationale': 'r', 'execution': ['e'],
                                                   'tradeoffs': ['t'], 'techniques': ['negative-space'],
                                                   'images': [f"{row['provider']}:{row['provider_item_id']}", 'met:gone']}]}),
                       encoding='utf-8')
    monkeypatch.setattr(server, 'EXAMPLE', example)
    direction = client.get('/api/briefs/example').json()['directions'][0]
    assert len(direction['images']) == 1 and direction['techniques'][0]['name']
