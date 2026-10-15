"""Licence eligibility, decided by ordinary code from provider evidence. AI output never reaches here."""

import html
import re

CC0_URL = 'https://creativecommons.org/publicdomain/zero/1.0/'
PD_URL = 'https://creativecommons.org/publicdomain/mark/1.0/'
LABELS = {'CC0': 'CC0 — source checked', 'PD': 'Public domain — source checked',
          'BY': 'Free with attribution — credit included'}
_BY = re.compile(r'^CC BY (\d\.\d)((?: [a-z]{2,3})?)$', re.I)


def plain(value) -> str:
    """Provider HTML (Commons Artist/Credit fields) reduced to plain text."""
    text = re.sub(r'<[^>]+>', ' ', str(value or ''))
    return re.sub(r'\s+', ' ', html.unescape(text)).strip()


def _no(reason: str) -> dict:
    return {'eligible': False, 'reason': reason}


def _yes(kind, candidate, policy, *, code, version, url, evidence, attribution=None, restrictions=''):
    credit = attribution or credit_line(candidate, policy['name'], code)
    return {'eligible': True, 'license_code': code, 'license_version': version, 'license_url': url,
            'label': LABELS[kind], 'evidence_url': candidate['source_url'], 'evidence': evidence,
            'required_attribution': credit,
            'restrictions': '; '.join(filter(None, [policy.get('restrictions', ''), restrictions])),
            'permitted_mode': policy['permitted_mode']}


def credit_line(candidate: dict, institution: str, licence: str) -> str:
    parts = [candidate.get('creator') or 'Unknown maker', candidate.get('title') or 'Untitled']
    if candidate.get('date_text'):
        parts.append(candidate['date_text'])
    return f"{', '.join(parts)}. {institution}. {licence}."


def _host_ok(url, policy) -> bool:
    match = re.match(r'^https://([^/:?#]+)/', url or '')
    return bool(match) and match.group(1).lower() in policy['hosts']


def check(candidate: dict, policy: dict) -> dict:
    """Eligibility for one candidate under its provider policy. Missing evidence is never eligible."""
    if policy.get('status') != 'enabled':
        return _no('source not enabled')
    if not candidate.get('source_url', '').startswith('https://'):
        return _no('no source page to cite')
    rule = _RULES.get(policy['id'])
    if rule is None:
        return _no('no eligibility rule for this source')
    decision = rule(candidate, candidate.get('raw') or {}, policy)
    if decision['eligible'] and not candidate.get('image_url'):
        return _no('no image available')
    if decision['eligible'] and not _host_ok(candidate.get('image_url'), policy):
        return _no('image is not hosted by the provider')
    return decision


def _aic(candidate, raw, policy):
    if raw.get('is_public_domain') is not True:
        return _no('not marked public domain by the museum')
    if not raw.get('image_id'):
        return _no('no image available')
    return _yes('CC0', candidate, policy, code='CC0', version='1.0', url=CC0_URL,
                evidence={'is_public_domain': True, 'image_id': raw['image_id']})


def _met(candidate, raw, policy):
    if raw.get('isPublicDomain') is not True:
        return _no('not marked public domain by the museum')
    if not raw.get('primaryImage'):
        return _no('no image available')
    credit = credit_line(candidate, policy['name'], 'CC0')
    if raw.get('creditLine'):
        credit = credit[:-1] + f" ({raw['creditLine']})."
    return _yes('CC0', candidate, policy, code='CC0', version='1.0', url=CC0_URL, attribution=credit,
                evidence={'isPublicDomain': True, 'primaryImage': raw['primaryImage']})


def _cma(candidate, raw, policy):
    if raw.get('share_license_status') != 'CC0':
        return _no(f"licence status is {raw.get('share_license_status') or 'missing'}, not CC0")
    return _yes('CC0', candidate, policy, code='CC0', version='1.0', url=CC0_URL,
                evidence={'share_license_status': 'CC0'})


def _smithsonian(candidate, raw, policy):
    media = raw.get('media') or {}
    if (media.get('usage') or {}).get('access') != 'CC0':
        return _no('image media is not marked CC0 (metadata licence alone is not enough)')
    return _yes('CC0', candidate, policy, code='CC0', version='1.0', url=CC0_URL,
                evidence={'media.usage.access': 'CC0', 'idsId': media.get('idsId', '')})


def _commons(candidate, raw, policy):
    meta = raw.get('extmetadata') or {}

    def value(key):
        return plain((meta.get(key) or {}).get('value', ''))

    name = value('LicenseShortName')
    if not name:
        return _no('no licence stated on the file page')
    if value('NonFree').lower() == 'true':
        return _no('file is marked non-free')
    if re.search(r'[,;/]| or | and ', name, re.I):
        return _no(f'more than one licence ("{name}"); not handled automatically')
    if re.search(r'\b(SA|NC|ND)\b', name):
        return _no(f'{name}: share-alike or restricted licences are excluded')
    restrictions = value('Restrictions')
    flag = f'Commons restriction flags: {restrictions}' if restrictions else ''
    evidence = {key: value(key) for key in ('LicenseShortName', 'LicenseUrl', 'Artist', 'Credit',
                                             'AttributionRequired', 'Restrictions', 'Copyrighted')}
    if name.upper() in ('CC0', 'CC0 1.0', 'CC-ZERO'):
        return _yes('CC0', candidate, policy, code='CC0', version='1.0', url=CC0_URL, evidence=evidence,
                    restrictions=flag, attribution=_commons_credit(candidate, value('Artist'), 'CC0'))
    if name.lower() in ('public domain', 'pdm', 'public domain mark', 'public domain mark 1.0'):
        if value('Copyrighted').lower() == 'true':
            return _no('public-domain tag conflicts with a copyrighted flag')
        return _yes('PD', candidate, policy, code='PD', version='', url=PD_URL, evidence=evidence,
                    restrictions=flag, attribution=_commons_credit(candidate, value('Artist'), 'Public domain'))
    match = _BY.match(name)
    if match and f'CC-BY-{match.group(1)}' not in policy.get('accepted_licenses', []):
        return _no(f'{name} is not a licence version this source policy accepts')
    if match:
        url = value('LicenseUrl')
        artist = value('Artist')
        licence_path = '/'.join((match.group(1) + match.group(2)).lower().split())
        if not re.fullmatch(r'https?://creativecommons\.org/licenses/by/' + re.escape(licence_path)
                            + r'(?:/(?:deed|legalcode)(?:\.[a-zA-Z_-]+)?)?/?', url):
            return _no(f'{name} without a matching licence link')
        if not artist:
            return _no(f'{name} requires an author credit, but no author is recorded')
        version = (match.group(1) + match.group(2)).strip()
        credit = _commons_credit(candidate, artist, f'{name} ({url.replace("http://", "https://")})')
        return _yes('BY', candidate, policy, code='CC BY', version=version, url=url.replace('http://', 'https://'),
                    evidence=evidence, restrictions=flag, attribution=credit)
    return _no(f'licence "{name}" is not on the accepted list')


def _commons_credit(candidate, artist, licence):
    title = candidate.get('title') or 'Untitled'
    return f'"{title}" by {artist or "unknown author"}, {licence}, via Wikimedia Commons ({candidate["source_url"]}).'


_RULES = {'aic': _aic, 'met': _met, 'cma': _cma, 'smithsonian': _smithsonian, 'commons': _commons}
