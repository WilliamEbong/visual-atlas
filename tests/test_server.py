"""Local server: loopback-only access rules, token, media confinement, and the main API flows."""

import pytest
from fastapi.testclient import TestClient
from helpers import aic_fetcher

from atlas import jobs
from atlas.ai import fake
from atlas.server import create_app

TOKEN = 'test-token'


@pytest.fixture
def client(home, tmp_path):
    dist = tmp_path / 'dist'
    dist.mkdir()
    (dist / 'index.html').write_text('<html><head></head><body>app</body></html>', encoding='utf-8')
    app = create_app(home, token=TOKEN, dist=dist)
    return TestClient(app, base_url='http://127.0.0.1:8775', headers={'x-atlas-token': TOKEN})


@pytest.fixture
def library(home, client):
    with jobs.open_store(home) as store:
        jobs.create_job(store, 'find', {'goal': 'harbour', 'providers': ['aic'], 'backend': 'fake', 'target_new_images': 2})
    jobs.Worker(home, owner='T', fetcher=aic_fetcher(), backends={'fake': fake}).run_once()
    return client


def test_requests_need_loopback_host_same_origin_and_token(client):
    assert client.get('/api/health').status_code == 200
    assert client.get('/api/health', headers={'x-atlas-token': 'wrong'}).status_code == 401
    assert client.get('/api/health', headers={'host': 'evil.example'}).status_code == 403  # DNS rebinding
    assert client.get('/api/health', headers={'origin': 'https://evil.example'}).status_code == 403
    response = client.get('/')
    assert 'name="atlas-token" content="test-token"' in response.text
    assert "frame-ancestors 'none'" in response.headers['content-security-policy']
    assert response.headers['cross-origin-resource-policy'] == 'same-origin'
    assert response.headers['cache-control'] == 'no-store'  # an upgraded app never runs a cached old page


def test_media_is_confined_to_the_library(library):
    image = library.get('/api/library').json()['items'][0]
    assert library.get(image['thumb'], headers={'x-atlas-token': ''}).status_code == 200
    for path in ('/media/../atlas.db', '/media/%2e%2e/atlas.db', '/media/tmp/x', '/media/originals/../../atlas.db',
                 '/media/%2e%2e%2fatlas.db', '/atlas.db'):
        response = library.get(path)
        assert b'SQLite format' not in response.content  # never the database; at most the app page or a 404
        assert response.status_code == 404 or response.text.startswith('<html>')


def test_library_search_filters_and_detail(library):
    items = library.get('/api/library').json()
    assert items['total'] == 2
    first = items['items'][0]
    assert first['license_label'] == 'CC0 — source checked' and first['techniques']
    technique = first['techniques'][0]['id']
    assert library.get('/api/library', params={'technique': technique}).json()['total'] >= 1
    assert library.get('/api/library', params={'q': first['title'].split()[0]}).json()['total'] >= 1
    assert library.get('/api/library', params={'q': 'zzzz-nothing'}).json()['total'] == 0
    detail = library.get(f"/api/images/{first['id']}").json()
    assert detail['rights']['required_attribution'] and detail['analysis']['observations']
    assert detail['annotations'][0]['proposed_backend'] == 'fake'
    assert library.get('/api/images/9999').status_code == 404


def test_corrections_collections_and_removal(library, home):
    image_id = library.get('/api/library').json()['items'][0]['id']
    technique = library.get(f'/api/images/{image_id}').json()['annotations'][0]['technique_id']
    corrected = library.post(f'/api/images/{image_id}/annotations', json={'technique_id': technique, 'state': 'rejected'}).json()
    assert next(a for a in corrected['annotations'] if a['technique_id'] == technique)['state'] == 'rejected'
    assert library.post(f'/api/images/{image_id}/annotations', json={'technique_id': technique, 'state': 'proposed'}).status_code == 400
    collection = library.post('/api/collections', json={'name': 'Harbours'}).json()['id']
    assert library.post(f'/api/collections/{collection}/items', json={'image_id': image_id}).status_code == 200
    assert library.get('/api/library', params={'collection': collection}).json()['total'] == 1
    assert library.delete(f'/api/images/{image_id}').status_code == 200
    assert library.get('/api/library').json()['total'] == 1
    assert library.get('/api/library', params={'collection': collection}).json()['total'] == 0


def test_graph_focus_paths_and_unknown_focus(library):
    image_id = library.get('/api/library').json()['items'][0]['id']
    graph = library.get('/api/graph', params={'focus': f'image:{image_id}'}).json()
    ids = {node['id'] for node in graph['nodes']}
    assert f'image:{image_id}' in ids and any(i.startswith('technique:') for i in ids)
    assert all(edge['source'] in ids and edge['target'] in ids for edge in graph['edges'])
    goal = library.get('/api/graph', params={'focus': 'goal:draw-attention'}).json()
    assert goal['nodes'][0]['ring'] == 0 or any(n['ring'] == 0 for n in goal['nodes'])
    assert library.get('/api/graph', params={'focus': 'goal:nope'}).status_code == 404


def test_graph_memberships_counts_and_annotation_states(library):
    taxonomy = library.get('/api/taxonomy').json()
    for facet in ('operation', 'domain'):
        entry = taxonomy[facet + 's'][0]
        graph = library.get('/api/graph', params={'focus': f'{facet}:{entry["id"]}'}).json()
        expected = {t['id'] for t in taxonomy['techniques'] if entry['id'] in t[facet + 's']}
        assert {n['id'].split(':')[1] for n in graph['nodes'] if n['kind'] == 'technique'} == expected
        assert all(e['explanation'] for e in graph['edges'] if e['kind'] != 'example')
        assert library.get('/api/graph', params={'focus': f'{facet}:unknown'}).status_code == 404
    image_id = library.get('/api/library').json()['items'][0]['id']
    annotation = library.get(f'/api/images/{image_id}').json()['annotations'][0]
    tid = annotation['technique_id']
    graph = library.get('/api/graph', params={'focus': f'technique:{tid}', 'limit': 1}).json()
    edges = [e for e in graph['edges'] if e['kind'] == 'example']
    assert len(edges) == 1 and graph['example_counts'][tid] >= 1
    expanded = library.get('/api/graph', params={'focus': f'technique:{tid}', 'limit': 200}).json()
    assert len([e for e in expanded['edges'] if e['kind'] == 'example']) == graph['example_counts'][tid]
    assert {'goal', 'operation', 'domain'} <= {n['kind'] for n in graph['nodes']}
    edge = next(e for e in expanded['edges'] if e['target'] == f'image:{image_id}' and e['kind'] == 'example')
    assert (edge['state'], edge['role'], edge['evidence']) == (annotation['state'], annotation['role'], annotation['evidence'])
    library.post(f'/api/images/{image_id}/annotations', json={'technique_id': tid, 'state': 'human_reviewed'})
    checked = library.get('/api/graph', params={'focus': f'image:{image_id}'}).json()
    assert next(e for e in checked['edges'] if e['source'] == f'technique:{tid}' and e['target'] == f'image:{image_id}')['state'] == 'human_reviewed'
    library.post(f'/api/images/{image_id}/annotations', json={'technique_id': tid, 'state': 'rejected'})
    rejected = library.get('/api/graph', params={'focus': f'technique:{tid}'}).json()
    assert not any(e['target'] == f'image:{image_id}' for e in rejected['edges'])


def test_jobs_api_validates_and_controls(client):
    assert client.post('/api/jobs', json={'kind': 'find', 'spec': {}}).status_code == 400
    job = client.post('/api/jobs', json={'kind': 'find', 'spec': {'goal': 'fog', 'backend': 'fake'}}).json()
    assert job['state'] == 'queued'
    assert client.post(f"/api/jobs/{job['id']}/pause").json()['state'] == 'paused'
    assert client.post(f"/api/jobs/{job['id']}/explode").status_code == 400


def test_restore_refuses_while_a_job_is_running(client):
    client.post('/api/jobs', json={'kind': 'find', 'spec': {'goal': 'fog', 'backend': 'fake'}})
    backup = client.post('/api/backups').json()
    response = client.post(f"/api/backups/{backup['name']}/restore")
    assert response.status_code == 503 and 'job is still running' in response.json()['detail']


def test_brief_and_directions_flow(library, home):
    brief = library.post('/api/briefs', json={'title': 'Poster', 'text': 'A calm poster about solitude.'}).json()['id']
    job = library.post('/api/jobs', json={'kind': 'directions', 'spec': {'brief_id': brief, 'backend': 'fake'}}).json()
    jobs.Worker(home, owner='T', backends={'fake': fake}).run_once(job['id'])
    directions = library.get(f'/api/briefs/{brief}').json()['directions']
    assert directions and all(d['techniques'] for d in directions)
    real = {i['id'] for i in library.get('/api/library').json()['items']}
    assert all(image['id'] in real for d in directions for image in d['images'])
    library.post(f"/api/directions/{directions[0]['id']}", json={'state': 'kept'})
    assert library.get(f'/api/briefs/{brief}').json()['directions'][0]['state'] == 'kept'


def test_library_pages_never_repeat_or_skip_images_with_equal_sort_values(home, client):
    from test_coding import add
    with jobs.open_store(home) as store:
        ids = [add(store, number, 'framing') for number in range(2, 9)]  # same technique count and similar titles
        store.connection.execute("UPDATE images SET title='Same'")
        store.connection.commit()
    for sort in ('title', 'techniques', 'colorful', 'newest'):
        seen = []
        for offset in (0, 3, 6):
            seen += [item['id'] for item in client.get(f'/api/library?sort={sort}&limit=3&offset={offset}').json()['items']]
        assert sorted(seen) == sorted(ids) and len(seen) == len(set(seen))
    assert len(client.get('/api/library?limit=100000').json()['items']) <= 200  # pages are bounded


def test_reading_shows_how_a_request_is_coded_without_ai(client):
    reading = client.get('/api/reading', params={'text': 'one figure in a lot of empty negative space', 'technique': 'silhouette',
                                                 'goal': 'no-such-goal'}).json()
    ids = [t['id'] for t in reading['techniques']]
    assert ids[0] == 'silhouette' and 'negative-space' in ids and reading['goals'] == []
    assert all(t['name'] for t in reading['techniques'])


def test_reading_keeps_subject_separate_and_checks_choice_kind(client):
    reading = client.get('/api/reading', params={'subject': 'silhouette', 'goal': 'negative-space',
                                                 'technique': 'create-calm'}).json()
    assert reading['techniques'] == [] and reading['goals'] == []
    assert reading['subject_terms'] == ['silhouette']


def test_page_data_carries_image_sizes_for_layout(library):
    first = library.get('/api/library').json()['items'][0]
    detail = library.get(f"/api/images/{first['id']}").json()
    technique = detail['annotations'][0]['technique_id']
    example = library.get(f'/api/techniques/{technique}').json()['examples'][0]
    assert example['width'] > 0 and example['height'] > 0 and example['display'].startswith('/media/analysis/')
    assert all(r['width'] > 0 and r['height'] > 0 for r in detail['related'])


def test_undo_of_a_collection_removal_restores_the_exact_position(home, client):
    from pathlib import Path

    from atlas import transfer
    with jobs.open_store(home) as store:
        transfer.import_starter(store, home, Path(__file__).resolve().parent.parent / 'starter')
    ids = [i['id'] for i in client.get('/api/library', params={'limit': 200}).json()['items']]
    made = client.post('/api/collections', json={'name': 'Long board'}).json()
    for image_id in ids:
        client.post(f"/api/collections/{made['id']}/items", json={'image_id': image_id, 'add': True})

    def order():
        return [i['id'] for i in client.get('/api/library', params={'collection': made['id'], 'sort': 'collection', 'limit': 200}).json()['items']]
    before = order()
    removed = before[70]  # deep in the board, past any page a screen has loaded
    answer = client.post(f"/api/collections/{made['id']}/items", json={'image_id': removed, 'add': False}).json()
    assert answer['position'] == 71 and removed not in order()
    client.post(f"/api/collections/{made['id']}/items", json={'image_id': removed, 'add': True, 'position': answer['position']})
    assert order() == before
    again = client.post(f"/api/collections/{made['id']}/items", json={'image_id': removed, 'add': True}).json()
    assert again['position'] is None and order() == before  # adding an image already there changes nothing
