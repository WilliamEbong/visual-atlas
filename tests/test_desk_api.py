"""The web door to the reference desk: token-guarded API, no local paths, layer pictures only by indexed ref."""

import json

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from atlas import jobs, layers, transfer
from atlas.home import REPO
from atlas.server import create_app

TOKEN = 'test-token'


@pytest.fixture(scope='module')
def starter_home(tmp_path_factory):
    home = tmp_path_factory.mktemp('api') / 'home'
    with jobs.open_store(home) as store:
        transfer.import_starter(store, home, REPO / 'starter')
    return home


@pytest.fixture
def client(starter_home, tmp_path, monkeypatch):
    folder = tmp_path / 'generated'
    folder.mkdir()
    Image.new('RGB', (300, 200), (40, 80, 120)).save(folder / 'sym-01.jpg', 'JPEG')
    (folder / 'manifest.json').write_text(json.dumps({'images': [
        {'id': 'sym-01', 'file': 'sym-01.jpg', 'title': 'Mirrored hall', 'tool': 'Codex', 'date': '2026-11-22',
         'techniques': ['symmetry'], 'subjects': ['hall'], 'width': 300, 'height': 200, 'prompt': 'p'}]}),
        encoding='utf-8')
    monkeypatch.setattr(layers, 'GENERATED', folder)
    monkeypatch.delenv('VISUAL_ATLAS_DESIGN_SYSTEMS', raising=False)
    app = create_app(starter_home, token=TOKEN, dist=tmp_path / 'dist')
    return TestClient(app, base_url='http://127.0.0.1:8775', headers={'x-atlas-token': TOKEN})


def test_desk_needs_the_launch_token(client):
    assert client.get('/api/desk', params={'brief': 'calm'}, headers={'x-atlas-token': 'no'}).status_code == 401


def test_desk_answers_with_pictures_reasons_and_no_local_paths(client):
    response = client.get('/api/desk', params={'brief': 'make one thing stand out', 'limit': 5})
    assert response.status_code == 200
    data = response.json()
    assert data['results'] and data['guidance'] and data['layers'] == {'generated': True, 'design-system': []}
    for ref in data['results']:
        assert 'file' not in ref and ref['reasons']
        assert ref['image'].startswith('/media/' if ref['layer'] == 'library' else '/api/desk/media?ref=')
        assert client.get(ref['thumb']).status_code == 200
    assert str(REPO) not in json.dumps(data, ensure_ascii=False).replace('\\\\', '\\')


def test_technique_mode_and_generated_pictures(client):
    data = client.get('/api/desk', params={'technique': 'symmetry', 'limit': 6}).json()
    generated = next(r for r in data['results'] if r['layer'] == 'generated')
    assert generated['image'] == '/api/desk/media?ref=generated:sym-01'
    picture = client.get(generated['image'])
    assert picture.status_code == 200 and picture.headers['content-type'] == 'image/jpeg'
    assert client.get(generated['image'], headers={'x-atlas-token': ''}).status_code == 401  # private layers need it
    assert data['guidance'][0]['id'] == 'symmetry'
    assert all(r['layer'] == 'library' for r in client.get('/api/desk', params={
        'technique': 'symmetry', 'use': 'publish'}).json()['results'])


@pytest.mark.parametrize('ref', ['../../atlas.db', 'generated:../manifest', 'system:x:..', 'library:1', 'generated:nope'])
def test_layer_media_serves_only_indexed_layer_refs(client, ref):
    assert client.get('/api/desk/media', params={'ref': ref}).status_code == 404


def test_empty_request_and_unknown_ref(client):
    assert client.get('/api/desk').status_code == 400
    assert client.get('/api/desk/ref', params={'ref': 'library:999999'}).status_code == 404
    assert client.get('/api/desk/ref', params={'ref': 'bad ref'}).status_code == 400
