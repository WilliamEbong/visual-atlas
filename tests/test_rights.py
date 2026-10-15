import json
from pathlib import Path

import pytest

from atlas import rights
from atlas.catalog import load

FIXTURES = Path(__file__).parent / 'fixtures' / 'providers'
PROVIDERS = ('aic', 'met', 'cma', 'smithsonian', 'commons')


def record(name):
    return json.loads((FIXTURES / name).read_text(encoding='utf-8'))


def candidate_for(provider):
    # Build rights inputs independently of the connectors so their failures cannot mask rights regressions.
    if provider == 'aic':
        raw = record('aic_search.json')['data'][0]
        source = f"https://www.artic.edu/artworks/{raw['id']}"
        image = f"https://www.artic.edu/iiif/2/{raw['image_id']}/full/843,/0/default.jpg"
    elif provider == 'met':
        raw = record('met_object_pd.json')
        source, image = raw['objectURL'], raw['primaryImage']
    elif provider == 'cma':
        raw = record('cma_search.json')['data'][0]
        source, image = raw['url'], raw['images']['web']['url']
    elif provider == 'smithsonian':
        item = record('smithsonian_search.json')['response']['rows'][0]
        described = item['content']['descriptiveNonRepeating']
        media = described['online_media']['media'][0]
        raw = {'media': media, 'metadata_usage': described['metadata_usage']}
        source, image = described['record_link'], media['content']
    else:
        raw = record('commons_search_free.json')['query']['pages'][1]['imageinfo'][0]
        source, image = raw['descriptionurl'], raw['url']
    return {'provider': provider, 'title': 'Fixture artwork', 'source_url': source,
            'image_url': image, 'raw': raw}


@pytest.fixture(params=PROVIDERS)
def eligible_record(request):
    provider = request.param
    policy = next(p for p in load()[1]['providers'] if p['id'] == provider)
    return candidate_for(provider), policy


def test_enabled_provider_fixture_is_eligible(eligible_record):
    candidate, policy = eligible_record
    decision = rights.check(candidate, policy)
    assert decision['eligible'] is True
    assert decision['evidence']
    assert decision['evidence_url'] == candidate['source_url']
    assert decision['license_url'].startswith('https://creativecommons.org/')
    assert decision['required_attribution']
    assert 'safe' not in decision['label'].lower()


def test_missing_source_page_is_ineligible(eligible_record):
    candidate, policy = eligible_record
    candidate.pop('source_url')
    assert rights.check(candidate, policy) == {'eligible': False, 'reason': 'no source page to cite'}


def test_missing_image_is_ineligible(eligible_record):
    candidate, policy = eligible_record
    candidate['image_url'] = ''
    assert rights.check(candidate, policy) == {'eligible': False, 'reason': 'no image available'}


def test_off_provider_image_is_ineligible(eligible_record):
    candidate, policy = eligible_record
    candidate['image_url'] = 'https://unrelated.example/image.jpg'
    assert rights.check(candidate, policy) == {'eligible': False, 'reason': 'image is not hosted by the provider'}


def test_disabled_policy_is_ineligible(eligible_record):
    candidate, policy = eligible_record
    policy['status'] = 'disabled'
    assert rights.check(candidate, policy) == {'eligible': False, 'reason': 'source not enabled'}


@pytest.mark.parametrize(('provider', 'raw', 'reason'), [
    ('aic', {'is_public_domain': False, 'image_id': 'exists'}, 'not marked public domain by the museum'),
    ('aic', {'is_public_domain': True, 'image_id': None}, 'no image available'),
    ('met', {'isPublicDomain': False, 'primaryImage': 'exists'}, 'not marked public domain by the museum'),
    ('met', {'isPublicDomain': True, 'primaryImage': ''}, 'no image available'),
    ('cma', {'share_license_status': 'Copyrighted'}, 'licence status is Copyrighted, not CC0'),
    ('smithsonian', {'metadata_usage': {'access': 'CC0'}, 'media': {'usage': {'access': 'restricted'}}},
     'image media is not marked CC0 (metadata licence alone is not enough)'),
])
def test_provider_evidence_rejections(provider, raw, reason):
    candidate = candidate_for(provider)
    candidate['raw'] = raw
    policy = next(p for p in load()[1]['providers'] if p['id'] == provider)
    assert rights.check(candidate, policy) == {'eligible': False, 'reason': reason}


@pytest.fixture
def commons():
    return candidate_for('commons'), next(p for p in load()[1]['providers'] if p['id'] == 'commons')


@pytest.mark.parametrize(('updates', 'reason'), [
    ({'LicenseShortName': 'CC BY-SA 4.0'}, 'CC BY-SA 4.0: share-alike or restricted licences are excluded'),
    ({'LicenseShortName': 'CC BY-NC 4.0'}, 'CC BY-NC 4.0: share-alike or restricted licences are excluded'),
    ({'LicenseShortName': 'CC BY-ND 4.0'}, 'CC BY-ND 4.0: share-alike or restricted licences are excluded'),
    ({'LicenseShortName': 'CC BY 4.0, GFDL'},
     'more than one licence ("CC BY 4.0, GFDL"); not handled automatically'),
    ({'Artist': ''}, 'CC BY 2.0 requires an author credit, but no author is recorded'),
    ({'LicenseUrl': ''}, 'CC BY 2.0 without a matching licence link'),
    ({'LicenseUrl': 'https://creativecommons.org/licenses/by/4.0/'}, 'CC BY 2.0 without a matching licence link'),
    ({'LicenseUrl': 'https://creativecommons.org/licenses/by/not-a-license'},
     'CC BY 2.0 without a matching licence link'),
    ({'NonFree': 'true'}, 'file is marked non-free'),
    ({'LicenseShortName': ''}, 'no licence stated on the file page'),
    ({'LicenseShortName': 'Public domain', 'Copyrighted': 'True'},
     'public-domain tag conflicts with a copyrighted flag'),
])
def test_commons_rejects_incomplete_or_restricted_evidence(commons, updates, reason):
    candidate, policy = commons
    candidate['raw']['extmetadata'].update({key: {'value': value} for key, value in updates.items()})
    assert rights.check(candidate, policy) == {'eligible': False, 'reason': reason}


@pytest.mark.parametrize(('name', 'url', 'code'), [
    ('CC0', '', 'CC0'), ('Public domain', '', 'PD'),
    ('CC BY 2.0', 'https://creativecommons.org/licenses/by/2.0', 'CC BY'),
    ('CC BY 4.0', 'http://creativecommons.org/licenses/by/4.0/', 'CC BY'),
    ('CC BY 3.0 de', 'https://creativecommons.org/licenses/by/3.0/de/deed.en', 'CC BY'),
])
def test_commons_allowed_licenses_keep_credits_and_restrictions(commons, name, url, code):
    candidate, policy = commons
    candidate['raw']['extmetadata'].update({
        'LicenseShortName': {'value': name}, 'LicenseUrl': {'value': url},
        'Copyrighted': {'value': 'False'}, 'Restrictions': {'value': 'personality rights'},
    })
    decision = rights.check(candidate, policy)
    assert decision['eligible'] is True
    assert decision['license_code'] == code
    assert 'Maxime Raynal' in decision['required_attribution']
    assert '<a' not in decision['required_attribution']
    assert 'Commons restriction flags: personality rights' in decision['restrictions']
    assert policy['restrictions'] in decision['restrictions']
    assert 'safe' not in decision['label'].lower()


def test_labels_never_claim_safety():
    assert all('safe' not in label.lower() for label in rights.LABELS.values())


@pytest.mark.parametrize('name, url', [('PD-not-a-real-licence', ''), ('CC BY 9.9', 'https://creativecommons.org/licenses/by/9.9/')])
def test_unknown_licence_names_and_versions_are_not_accepted(name, url):
    from atlas import catalog
    _, policies, *_ = catalog.load()
    policy = catalog.policy(policies, 'commons')
    candidate = {'source_url': 'https://commons.wikimedia.org/wiki/File:X.jpg', 'title': 'X',
                 'image_url': 'https://upload.wikimedia.org/x.jpg',
                 'raw': {'extmetadata': {'LicenseShortName': {'value': name}, 'LicenseUrl': {'value': url},
                                         'Artist': {'value': 'Someone'}}}}
    assert rights.check(candidate, policy)['eligible'] is False
