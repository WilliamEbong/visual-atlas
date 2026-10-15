import json
import socket
from pathlib import Path
from urllib.parse import urlsplit

import httpx
import pytest

from atlas import providers, rights
from atlas.catalog import load
from atlas.fetch import Fetcher

FIXTURES = Path(__file__).parent / 'fixtures' / 'providers'
API_URLS = {
    'aic': 'https://api.artic.edu/api/v1/artworks/search',
    'met': 'https://collectionapi.metmuseum.org/public/collection/v1.1/search',
    'cma': 'https://openaccess-api.clevelandart.org/api/artworks/',
    'smithsonian': 'https://api.si.edu/openaccess/api/v1.0/search',
    'commons': 'https://commons.wikimedia.org/w/api.php',
}


def record(name):
    return json.loads((FIXTURES / name).read_text(encoding='utf-8'))


@pytest.mark.parametrize(('provider', 'fixture', 'ids', 'first_title', 'eligible'), [
    ('aic', 'aic_search.json', ['66144', '148047', '133358'], 'Rocks at the Lighthouse, Biarritz', [True] * 3),
    ('cma', 'cma_search.json', ['173965', '114500', '114496'],
     'Lighthouse Village (also known as Cape Elizabeth)', [True] * 3),
    ('smithsonian', 'smithsonian_search.json', None, 'Design for a Lighthouse', [True] * 3),
    ('met', 'met_search.json', ['374483', '382738'], 'Lighthouse', [False, True]),
    ('commons', 'commons_search_free.json', None, None, [True] * 6),
    ('commons', 'commons_search_bysa.json', None, None, [False] * 3),
])
def test_recorded_api_responses_and_rights(monkeypatch, provider, fixture, ids, first_title, eligible):
    monkeypatch.setattr(providers, 'local_setting', lambda _: None)
    payload = record(fixture)
    objects = {str(item['objectID']): item for item in
               [record('met_object_pd.json'), record('met_object_not_pd.json')]}
    requests = []

    def handler(request):
        requests.append(request)
        url = str(request.url).split('?')[0]
        if url == API_URLS[provider]:
            assert request.method == 'GET'
            if provider == 'met':
                assert request.url.params['limit'] == '2'
                assert request.url.params['offset'] == '0'
            if provider == 'smithsonian':
                assert request.url.params['api_key'] == 'DEMO_KEY'
            return httpx.Response(200, json=payload)
        assert provider == 'met'
        object_id = request.url.path.rsplit('/', 1)[-1]
        assert url == f'https://collectionapi.metmuseum.org/public/collection/v1/objects/{object_id}'
        return httpx.Response(200, json=objects[object_id])

    def resolver(host, port, **kwargs):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, '', ('8.8.8.8', port))]

    policies = load()[1]
    policy = next(p for p in policies['providers'] if p['id'] == provider)
    fetcher = Fetcher(policies, transport=httpx.MockTransport(handler), resolver=resolver, sleep=lambda _: None)
    try:
        candidates = providers.search(fetcher, provider, 'lighthouse', page=0,
                                      per_page=2 if provider == 'met' else len(eligible))
    finally:
        fetcher.close()

    assert len(candidates) == len(eligible)
    assert len(requests) == (3 if provider == 'met' else 1)
    if provider == 'smithsonian':
        ids = [row['id'] for row in payload['response']['rows']]
    if provider == 'commons':
        pages = payload['query']['pages']
        pages = list(pages.values()) if isinstance(pages, dict) else pages
        pages = sorted(pages, key=lambda item: item.get('index', 0))
        ids = [str(item['pageid']) for item in pages]
    assert [c['provider_item_id'] for c in candidates] == ids
    if first_title:
        assert candidates[0]['title'] == first_title
    decisions = []
    for candidate in candidates:
        assert candidate['provider'] == provider
        assert candidate['title']
        assert urlsplit(candidate['source_url']).scheme == 'https'
        assert urlsplit(candidate['source_url']).hostname
        assert candidate['raw']
        if candidate['image_url']:
            assert urlsplit(candidate['image_url']).scheme == 'https'
            assert urlsplit(candidate['image_url']).hostname in policy['hosts']
        else:
            assert provider == 'met' and candidate['raw']['isPublicDomain'] is False
        decisions.append(rights.check(candidate, policy))
    assert [decision['eligible'] for decision in decisions] == eligible

    if provider == 'aic':
        for candidate, item in zip(candidates, payload['data'], strict=True):
            assert candidate['raw']['is_public_domain'] is item['is_public_domain']
            assert candidate['raw']['image_id'] == item['image_id']
            assert candidate['image_headers']['AIC-User-Agent'] == policies['user_agent']
    elif provider == 'met':
        for candidate in candidates:
            assert candidate['raw']['isPublicDomain'] is objects[candidate['provider_item_id']]['isPublicDomain']
            assert candidate['image_url'] == objects[candidate['provider_item_id']]['primaryImage']
        assert decisions[0]['reason'] == 'not marked public domain by the museum'
    elif provider == 'cma':
        assert all(c['raw']['share_license_status'] == 'CC0' for c in candidates)
    elif provider == 'smithsonian':
        assert all(c['raw']['media']['usage']['access'] == 'CC0' for c in candidates)
    elif fixture == 'commons_search_free.json':
        assert {d['license_code'] for d in decisions} == {'CC0', 'CC BY'}
        for candidate, decision, page in zip(candidates, decisions, pages, strict=True):
            meta = page['imageinfo'][0]['extmetadata']
            assert candidate['raw']['extmetadata']['LicenseShortName']['value'] == meta['LicenseShortName']['value']
            assert candidate['creator']
            assert candidate['creator'] in decision['required_attribution']
            assert candidate['source_url'] in decision['required_attribution']
    else:
        assert all('share-alike or restricted licences are excluded' in d['reason'] for d in decisions)


def test_met_skips_objects_the_object_api_no_longer_serves():
    import httpx
    from helpers import public_resolver

    from atlas import catalog
    from atlas.fetch import Fetcher
    pd = json.loads((FIXTURES / 'met_object_pd.json').read_text(encoding='utf-8'))

    def handler(request):
        if request.url.path.endswith('/v1.1/search'):
            return httpx.Response(200, json={'total': 2, 'objectIDs': [111, pd['objectID']]})
        if request.url.path.endswith('/objects/111'):
            return httpx.Response(404, json={'message': 'Not a valid object'})
        return httpx.Response(200, json=pd)

    _, policies, *_ = catalog.load()
    fetcher = Fetcher(policies, transport=httpx.MockTransport(handler), resolver=public_resolver, sleep=lambda s: None)
    found = providers.search(fetcher, 'met', 'lighthouse', 0, 5)
    assert [c['provider_item_id'] for c in found] == [str(pd['objectID'])]


def test_commons_template_residue_is_stripped_from_catalogue_text():
    from atlas.providers import _clip
    assert _clip('1812 date QS:P571,+1812-00-00T00:00:00Z/9') == '1812'
    assert _clip('A Market Place and Crowd title QS:P1476,en:"A Market Place and Crowd"') == 'A Market Place and Crowd'
    assert _clip('An ordinary title with dates 1890–1900') == 'An ordinary title with dates 1890–1900'
