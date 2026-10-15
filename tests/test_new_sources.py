"""v0.3 sources: the Rijksmuseum (Linked Art, rights on the image's VisualItem) and the National Gallery of Art
(open-data CSV files searched through a local index). Recorded live 2026-10-15; see docs/evaluation/v0.3/SOURCES.md."""

import json
import os
import time
from pathlib import Path

import httpx
import pytest
from helpers import FIXTURES, public_resolver

from atlas import catalog, jobs, nga, providers, rights
from atlas.fetch import Fetcher, FetchError

PDM = 'https://creativecommons.org/publicdomain/mark/1.0/'
INC = 'https://rightsstatements.org/vocab/InC/1.0/'


def record(name):
    return json.loads((FIXTURES / name).read_text(encoding='utf-8'))


def policy(provider_id):
    return catalog.policy(catalog.load()[1], provider_id)


def fetcher(handler) -> Fetcher:
    return Fetcher(catalog.load()[1], transport=httpx.MockTransport(handler), resolver=public_resolver, sleep=lambda s: None)


def rijks_handler(seen: list):
    by_id = {'200108226': record('rijks_object_pd.json'), '202108226': record('rijks_visual_pd.json'),
             '500675478112727476112': record('rijks_digital_pd.json'), '200496110': record('rijks_object_inc.json'),
             '202496110': record('rijks_visual_inc.json'),
             '500721089790835111278': {'id': 'https://id.rijksmuseum.nl/500721089790835111278', 'type': 'DigitalObject',
                                        'access_point': [{'id': 'https://iiif.micr.io/xyzAB/full/max/0/default.jpg'}]}}

    def handler(request: httpx.Request):
        seen.append(request)
        if request.url.host == 'data.rijksmuseum.nl':
            search = record('rijks_search.json')
            search['orderedItems'] = [{'id': 'https://id.rijksmuseum.nl/200108226', 'type': 'HumanMadeObject'},
                                      {'id': 'https://id.rijksmuseum.nl/200496110', 'type': 'HumanMadeObject'}]
            return httpx.Response(200, json=search, headers={'content-type': 'application/ld+json'})
        if request.url.host == 'id.rijksmuseum.nl':
            item = by_id.get(request.url.path.strip('/'))
            return httpx.Response(200, json=item, headers={'content-type': 'application/ld+json'}) if item else httpx.Response(404)
        return httpx.Response(404)
    return handler


def test_rijksmuseum_reads_the_image_rights_not_the_metadata_licence():
    seen = []
    found = providers.search(fetcher(rijks_handler(seen)), 'rijksmuseum', 'pond at sunset')
    assert [c['provider_item_id'] for c in found] == ['200108226', '200496110']
    pond = found[0]
    assert pond['title'] == 'Woodland Pond at Sunset' and pond['creator'] == 'Gerard Bilders'
    assert pond['date_text'] == 'c. 1862' and pond['medium'] == 'oil on panel'
    assert pond['source_url'].startswith('https://www.rijksmuseum.nl/')
    assert pond['image_url'] == 'https://iiif.micr.io/ffnha/full/1600,/0/default.jpg'
    assert pond['raw']['rights'] == [PDM]  # from the VisualItem; the object's CC0 metadata licence is ignored
    decision = rights.check(pond, policy('rijksmuseum'))
    assert decision['eligible'] and decision['label'] == 'Public domain — source checked'
    assert 'Rijksmuseum' in decision['required_attribution']
    refused = rights.check(found[1], policy('rijksmuseum'))
    assert not refused['eligible'] and 'InC' in refused['reason']
    assert {r.url.host for r in seen} <= set(policy('rijksmuseum')['hosts'])
    assert all(r.headers['accept'] == 'application/ld+json' for r in seen if r.url.host == 'id.rijksmuseum.nl')


@pytest.mark.parametrize(('raw', 'eligible', 'reason'), [
    ({'rights': ['https://creativecommons.org/publicdomain/zero/1.0/']}, True, ''),
    ({'rights': ['https://creativecommons.org/licenses/by/4.0/']}, True, ''),
    ({'rights': []}, False, 'no rights statement'),
    ({'rights': [PDM, INC]}, False, 'more than one'),
    ({'rights': ['https://creativecommons.org/licenses/by-sa/4.0/']}, False, 'not one this source policy accepts'),
])
def test_rijksmuseum_rule(raw, eligible, reason):
    candidate = {'source_url': 'https://www.rijksmuseum.nl/en/collection/SK-A-1', 'image_url': 'https://iiif.micr.io/a/full/1600,/0/default.jpg',
                 'title': 'T', 'creator': 'C', 'raw': raw}
    decision = rights.check(candidate, policy('rijksmuseum'))
    assert decision['eligible'] is eligible and reason in decision.get('reason', '')
    if eligible and 'by/4.0' in raw['rights'][0]:
        assert decision['license_code'] == 'CC BY' and 'creativecommons.org/licenses/by/4.0' in decision['required_attribution']


IMAGES = ('uuid,iiifurl,iiifthumburl,viewtype,sequence,width,height,maxpixels,openaccess,created,modified,depictstmsobjectid,assistivetext\n'
          'a1,https://api.nga.gov/iiif/a1,x,primary,0,3365,4332,,1,2013,2026,17387,"A drawing of two jugs"\n'
          'b2,https://api.nga.gov/iiif/b2,x,primary,0,900,700,900,0,2013,2026,50,""\n'
          'c3,https://api.nga.gov/iiif/c3,x,alternate,1,900,700,,1,2013,2026,17387,""\n'
          'd4,https://api.nga.gov/iiif/d4,x,primary,0,1200,800,900,1,2013,2026,60,""\n'
          'e5,https://api.nga.gov/iiif/e5,x,primary,0,2000,1500,,1,2013,2026,70,""\n')
OBJECTS = ('objectid,uuid,accessioned,accessionnum,locationid,title,displaydate,beginyear,endyear,visualbrowsertimespan,medium,'
           'dimensions,inscription,markings,attributioninverted,attribution,provenancetext,creditline,classification\n'
           '17387,u,1,1943.8.1,,"Two Jugs, with a Shared Base",c. 1700,1700,1700,,watercolor,,,,"Doe, J.",Jane Doe,,'
           'Index of American Design,Drawing\n'
           '50,u,1,1937.1.2,,Restricted Picture,1950,1950,1950,,oil,,,,,A. Painter,,Gift,Painting\n'
           '60,u,1,1937.1.3,,Capped Sunset,1900,1900,1900,,oil,,,,,B. Painter,,Gift,Painting\n'
           '70,u,1,1937.1.4,,Harbor at Dusk,1870,1870,1870,oil on canvas,,,,,,C. Painter,,Gift,Painting\n')
TERMS = ('termid,objectid,termtype,term,visualbrowsertheme,visualbrowserstyle\n'
         '1,70,Keyword,Sunset,,\n2,70,Keyword,Keywords,,\n3,17387,Theme,Ceramics,,\n')


def nga_files(folder: Path) -> dict:
    folder.mkdir(parents=True, exist_ok=True)
    files = {}
    for name, text in (('published_images.csv', IMAGES), ('objects.csv', OBJECTS), ('objects_terms.csv', TERMS)):
        (folder / name).write_text(text, encoding='utf-8')
        files[name] = folder / name
    return files


def test_nga_index_keeps_only_open_access_primary_images(home, tmp_path):
    nga.build(None, home, nga_files(tmp_path / 'csv'))
    data = nga.load(None, home)
    assert sorted(row['id'] for row in data['rows']) == ['17387', '70']  # restricted, capped and alternate views dropped
    harbour = nga.search(data, 'sunsets harbor', 0, 10)
    assert [row['id'] for row in harbour] == ['70'] and harbour[0]['terms'] == ['Sunset']
    found = providers.search(None, 'nga', 'jugs', home=home)
    assert found[0]['title'] == 'Two Jugs, with a Shared Base' and found[0]['image_url'] == 'https://api.nga.gov/iiif/a1/full/!1600,1600/0/default.jpg'
    decision = rights.check(found[0], policy('nga'))
    assert decision['eligible'] and decision['license_code'] == 'CC0' and 'National Gallery of Art' in decision['required_attribution']
    for raw, reason in (({**found[0]['raw'], 'openaccess': '0'}, 'not an open-access'), ({**found[0]['raw'], 'maxpixels': '900'}, 'size-restricted'),
                        ({**found[0]['raw'], 'viewtype': 'alternate'}, 'not the primary')):
        assert reason in rights.check({**found[0], 'raw': raw}, policy('nga'))['reason']


def test_nga_downloads_its_open_data_once_and_keeps_an_old_index_when_a_refresh_fails(home, tmp_path):
    served = {'published_images.csv': IMAGES, 'objects.csv': OBJECTS, 'objects_terms.csv': TERMS}
    calls = []

    def handler(request: httpx.Request):
        calls.append(request.url.host)
        name = request.url.path.rsplit('/', 1)[-1]
        if request.url.host == 'raw.githubusercontent.com' and name in served:
            return httpx.Response(200, text=served[name], headers={'content-type': 'text/plain; charset=utf-8'})
        return httpx.Response(503)

    assert providers.search(fetcher(handler), 'nga', 'harbor', home=home)[0]['provider_item_id'] == '70'
    assert calls == ['raw.githubusercontent.com'] * 3
    assert not list(nga.folder(home).glob('*.csv'))  # the downloads are removed once the index is written
    providers.search(fetcher(handler), 'nga', 'jugs', home=home)
    assert len(calls) == 3  # a fresh index is reused
    index = nga.folder(home) / 'index.json.gz'
    old = time.time() - 40 * 86400
    os.utime(index, (old, old))
    served.clear()  # the refresh now fails
    assert providers.search(fetcher(handler), 'nga', 'jugs', home=home)[0]['provider_item_id'] == '17387'
    index.unlink()
    with pytest.raises(FetchError):  # no index at all and no way to build one: the search fails plainly
        providers.search(fetcher(handler), 'nga', 'jugs', home=home)


def test_jobs_without_chosen_sources_skip_the_opt_in_gallery(home):
    with jobs.open_store(home) as store:
        job_id = jobs.create_job(store, 'find', {'goal': 'harbour at dusk', 'backend': 'fake'})
        spec = json.loads(store.one('SELECT spec_json FROM jobs WHERE id=?', (job_id,))['spec_json'])
    assert 'rijksmuseum' in spec['providers'] and 'nga' not in spec['providers']
