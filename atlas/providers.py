"""Search connectors for the enabled open-access providers. Each returns candidate dicts:

provider, provider_item_id, title, creator, date_text, medium, description, source_url, image_url,
image_headers, raw (the exact licence evidence fields rights.py checks)."""

import re
from pathlib import Path

from atlas import nga
from atlas.fetch import Fetcher, FetchError
from atlas.home import home_dir, local_setting
from atlas.rights import plain

PROVIDERS = ('aic', 'met', 'cma', 'smithsonian', 'commons', 'rijksmuseum', 'nga')
NAMES = {'aic': 'Art Institute of Chicago', 'met': 'The Met', 'cma': 'Cleveland Museum of Art',
         'smithsonian': 'Smithsonian', 'commons': 'Wikimedia Commons', 'rijksmuseum': 'Rijksmuseum',
         'nga': 'National Gallery of Art'}
# Searched when a job names no sources. The National Gallery is opt-in: its first search downloads ~190 MB.
DEFAULT_PROVIDERS = tuple(p for p in PROVIDERS if p != 'nga')
LINKED_ART = ('application/ld+json', 'application/json')
ENGLISH = 'http://vocab.getty.edu/aat/300388277'
CREATOR_NOTE = 'http://vocab.getty.edu/aat/300435417'
MATERIAL_NOTE = 'http://vocab.getty.edu/aat/300435429'
DESCRIPTION_NOTE = 'http://vocab.getty.edu/aat/300435452'
# Commons structured-data licence statements used only to narrow searches; each file is still checked.
COMMONS_LICENCES = ('haswbstatement:P275=Q6938433|P275=Q20007257|P275=Q14947546|P275=Q19125117'
                    '|P6216=Q19652')


def _clip(value, limit=500) -> str:
    # Commons templates leak Wikidata residue such as "1812 date QS:P571,+1812-00-00T00:00:00Z/9".
    text = re.sub(r'\s*\b(?:date|title|label)\s+QS:[PL]\w*,(?:[a-z-]+:)?(?:"[^"]*"|\S*)\S*', '', plain(value))
    return text.strip()[:limit]


def search(fetcher: Fetcher, provider: str, query: str, page: int = 0, per_page: int = 10,
           home: Path | None = None) -> list[dict]:
    if provider == 'nga':
        return _nga(fetcher, query, page, per_page, home_dir(home))
    if provider not in _SEARCH:
        raise ValueError(f'unknown provider {provider}')
    return _SEARCH[provider](fetcher, query, page, per_page)


def _aic(fetcher, query, page, per_page):
    headers = {'AIC-User-Agent': fetcher.user_agent}
    data = fetcher.get_json('aic', 'https://api.artic.edu/api/v1/artworks/search', headers=headers, params={
        'q': query, 'query[term][is_public_domain]': 'true', 'limit': per_page, 'page': page + 1,
        'fields': 'id,title,artist_title,artist_display,date_display,medium_display,image_id,'
                  'is_public_domain,credit_line,thumbnail,artwork_type_title'})
    iiif = ((data.get('config') or {}).get('iiif_url') or 'https://www.artic.edu/iiif/2').rstrip('/')
    results = []
    for item in data.get('data') or []:
        if not isinstance(item, dict) or not item.get('id'):
            continue
        image_id = item.get('image_id')
        results.append({
            'provider': 'aic', 'provider_item_id': str(item['id']), 'title': _clip(item.get('title'), 300),
            'creator': _clip(item.get('artist_title') or (item.get('artist_display') or '').split('\n')[0], 200),
            'date_text': _clip(item.get('date_display'), 80), 'medium': _clip(item.get('medium_display'), 200),
            'description': _clip((item.get('thumbnail') or {}).get('alt_text'), 400),
            'source_url': f"https://www.artic.edu/artworks/{item['id']}",
            'image_url': f'{iiif}/{image_id}/full/843,/0/default.jpg' if image_id else '',
            'image_headers': headers, 'credit_line': _clip(item.get('credit_line'), 300),
            'raw': {'is_public_domain': item.get('is_public_domain'), 'image_id': image_id,
                    'credit_line': item.get('credit_line')}})
    return results


def _met(fetcher, query, page, per_page):
    found = fetcher.get_json('met', 'https://collectionapi.metmuseum.org/public/collection/v1.1/search',
                             params={'q': query, 'hasImages': 'true', 'limit': per_page, 'offset': page * per_page})
    results = []
    for object_id in (found.get('objectIDs') or [])[:per_page]:
        if not isinstance(object_id, int):
            continue
        try:
            item = fetcher.get_json('met', f'https://collectionapi.metmuseum.org/public/collection/v1/objects/{object_id}')
        except FetchError as error:
            if error.code == 'http_404':
                continue  # the search index lists some objects the object API no longer serves
            raise
        results.append({
            'provider': 'met', 'provider_item_id': str(object_id), 'title': _clip(item.get('title'), 300),
            'creator': _clip(item.get('artistDisplayName'), 200), 'date_text': _clip(item.get('objectDate'), 80),
            'medium': _clip(item.get('medium'), 200), 'description': '',
            'source_url': item.get('objectURL') or f'https://www.metmuseum.org/art/collection/search/{object_id}',
            'image_url': item.get('primaryImage') or '', 'image_headers': {},
            'credit_line': _clip(item.get('creditLine'), 300),
            'raw': {'isPublicDomain': item.get('isPublicDomain'), 'primaryImage': item.get('primaryImage'),
                    'creditLine': item.get('creditLine')}})
    return results


def _cma(fetcher, query, page, per_page):
    data = fetcher.get_json('cma', 'https://openaccess-api.clevelandart.org/api/artworks/', params={
        'q': query, 'cc0': '1', 'has_image': '1', 'limit': per_page, 'skip': page * per_page})
    results = []
    for item in data.get('data') or []:
        if not isinstance(item, dict) or not item.get('id'):
            continue
        creators = item.get('creators') or []
        web = ((item.get('images') or {}).get('web') or {})
        results.append({
            'provider': 'cma', 'provider_item_id': str(item['id']), 'title': _clip(item.get('title'), 300),
            'creator': _clip(creators[0].get('description') if creators else '', 200),
            'date_text': _clip(item.get('creation_date'), 80), 'medium': _clip(item.get('technique'), 200),
            'description': _clip(item.get('description'), 400),
            'source_url': (item.get('url') or '').replace('http://', 'https://'),
            'image_url': web.get('url') or '', 'image_headers': {}, 'credit_line': _clip(item.get('creditline'), 300),
            'raw': {'share_license_status': item.get('share_license_status')}})
    return results


def _smithsonian(fetcher, query, page, per_page):
    key = local_setting('SMITHSONIAN_API_KEY') or 'DEMO_KEY'
    data = fetcher.get_json('smithsonian', 'https://api.si.edu/openaccess/api/v1.0/search', params={
        'q': f'{query} AND online_media_type:"Images" AND media_usage:"CC0"', 'rows': per_page,
        'start': page * per_page, 'api_key': key})
    results = []
    for row in (data.get('response') or {}).get('rows') or []:
        content = row.get('content') or {}
        described = content.get('descriptiveNonRepeating') or {}
        media = next((m for m in (described.get('online_media') or {}).get('media') or []
                      if m.get('type') == 'Images' and m.get('idsId')), None)
        if media is None:
            continue
        text = content.get('freetext') or {}

        def first(field):
            values = text.get(field) or []
            return values[0].get('content', '') if values and isinstance(values[0], dict) else ''

        link = described.get('record_link') or ''
        results.append({
            'provider': 'smithsonian', 'provider_item_id': str(row.get('id')), 'title': _clip(row.get('title'), 300),
            'creator': _clip(first('name'), 200), 'date_text': _clip(first('date'), 80),
            'medium': _clip(first('physicalDescription'), 200), 'description': _clip(first('notes'), 400),
            'source_url': link if link.startswith('https://') else f"https://collections.si.edu/search/detail/{row.get('url', '')}",
            'image_url': f"https://ids.si.edu/ids/deliveryService?id={media['idsId']}&max=1200",
            'image_headers': {}, 'credit_line': _clip(first('creditLine') or described.get('data_source'), 300),
            'raw': {'media': {'usage': media.get('usage'), 'idsId': media.get('idsId')},
                    'unit': described.get('unit_code')}})
    return results


def _commons(fetcher, query, page, per_page):
    data = fetcher.get_json('commons', 'https://commons.wikimedia.org/w/api.php', params={
        'action': 'query', 'format': 'json', 'formatversion': '2', 'generator': 'search', 'gsrnamespace': '6',
        'gsrsearch': f'{query} filetype:bitmap {COMMONS_LICENCES}', 'gsrlimit': per_page,
        'gsroffset': page * per_page, 'prop': 'imageinfo', 'iiprop': 'url|size|mime|extmetadata',
        'iiurlwidth': '1280', 'iiextmetadatafilter': 'LicenseShortName|LicenseUrl|Artist|Credit|'
        'AttributionRequired|Restrictions|Copyrighted|ObjectName|ImageDescription|DateTimeOriginal|NonFree|UsageTerms'})
    pages = (data.get('query') or {}).get('pages') or []
    if isinstance(pages, dict):
        pages = pages.values()
    results = []
    for item in sorted(pages, key=lambda p: p.get('index', 0)):
        info = (item.get('imageinfo') or [{}])[0]
        meta = info.get('extmetadata') or {}
        if info.get('mime') not in ('image/jpeg', 'image/png', 'image/webp'):
            continue
        title = _clip((meta.get('ObjectName') or {}).get('value'), 300) or item.get('title', '').removeprefix('File:')
        results.append({
            'provider': 'commons', 'provider_item_id': str(item.get('pageid')), 'title': title[:300],
            'creator': _clip((meta.get('Artist') or {}).get('value'), 200),
            'date_text': _clip((meta.get('DateTimeOriginal') or {}).get('value'), 80), 'medium': 'Photograph or image file',
            'description': _clip((meta.get('ImageDescription') or {}).get('value'), 400),
            'source_url': info.get('descriptionurl') or '', 'image_url': info.get('thumburl') or info.get('url') or '',
            'image_headers': {}, 'credit_line': _clip((meta.get('Credit') or {}).get('value'), 300),
            'raw': {'extmetadata': {k: {'value': (v or {}).get('value')} for k, v in meta.items()},
                    'width': info.get('width'), 'height': info.get('height')}})
    return results


def _english(entries, classified: str | None = None) -> str:
    """The English text of a Linked Art name or note list (optionally of one classification), else the first."""
    matches = [e for e in entries or [] if isinstance(e, dict) and isinstance(e.get('content'), str)
               and e.get('type') in ('Name', 'LinguisticObject')
               and (classified is None or any(c.get('id') == classified for c in e.get('classified_as') or []))]
    english = [e for e in matches if any(lang.get('id') == ENGLISH for lang in e.get('language') or [])]
    return (english or matches or [{'content': ''}])[0]['content']


def _first_id(entries) -> str:
    entry = (entries or [{}])[0] if isinstance(entries, list) else {}
    return entry.get('id', '') if isinstance(entry, dict) else ''


def _linked(fetcher, url: str) -> dict:
    if not url.startswith('https://id.rijksmuseum.nl/'):
        return {}
    return fetcher.get_json('rijksmuseum', url, headers={'Accept': 'application/ld+json'}, types=LINKED_ART)


def _rijksmuseum(fetcher, query, page, per_page):
    """Linked Art: the object gives title, maker and date; its VisualItem carries the image's own rights statement
    and points to the DigitalObject whose access point is the IIIF image (three requests per item)."""
    found = fetcher.get_json('rijksmuseum', 'https://data.rijksmuseum.nl/search/collection',
                             params={'title': query, 'imageAvailable': 'true'}, types=LINKED_ART)
    ids = [i.get('id', '') for i in found.get('orderedItems') or [] if isinstance(i, dict)]
    ids = [i for i in ids if i.startswith('https://id.rijksmuseum.nl/')][page * per_page:(page + 1) * per_page]
    results = []
    for object_url in ids:
        try:
            item = _linked(fetcher, object_url)
            visual_url = _first_id(item.get('shows'))
            visual = _linked(fetcher, visual_url)
            digital_url = _first_id(visual.get('digitally_shown_by'))
            digital = _linked(fetcher, digital_url)
        except FetchError as error:
            if error.code == 'http_404':
                continue
            raise
        produced = item.get('produced_by') or {}
        makers = [_english(part.get('referred_to_by'), CREATOR_NOTE)
                  for part in produced.get('part') or [] if isinstance(part, dict)]
        pages = [_first_id(carrier.get('access_point')) for s in item.get('subject_of') or [] if isinstance(s, dict)
                 for carrier in s.get('digitally_carried_by') or [] if isinstance(carrier, dict)]
        page_url = next((u for u in pages if u.startswith('https://www.rijksmuseum.nl/')), '')
        number = next((e.get('content', '') for e in item.get('identified_by') or []
                       if isinstance(e, dict) and e.get('type') == 'Identifier'), '')
        access = _first_id(digital.get('access_point'))
        image_url = access.replace('/full/max/', '/full/1600,/') if access.startswith('https://iiif.micr.io/') else ''
        rights = sorted({c.get('id', '') for r in visual.get('subject_to') or [] if isinstance(r, dict)
                         for c in r.get('classified_as') or [] if isinstance(c, dict)})
        results.append({
            'provider': 'rijksmuseum', 'provider_item_id': object_url.rsplit('/', 1)[-1],
            'title': _clip(_english(item.get('identified_by')), 300),
            'creator': _clip(re.sub(r'\s*\([^)]*\)\s*$', '', next((m for m in makers if m), '')), 200),
            'date_text': _clip(_english((produced.get('timespan') or {}).get('identified_by')), 80),
            'medium': _clip(_english(item.get('referred_to_by'), MATERIAL_NOTE), 200),
            'description': _clip(_english(item.get('referred_to_by'), DESCRIPTION_NOTE), 400),
            'source_url': page_url or (f'https://www.rijksmuseum.nl/en/collection/{number}' if number else ''),
            'image_url': image_url, 'image_headers': {},
            'credit_line': f'Rijksmuseum, Amsterdam{f" ({number})" if number else ""}',
            'raw': {'visual_item': visual_url, 'rights': rights, 'digital_object': digital_url, 'access_point': access}})
    return results


def _nga(fetcher, query, page, per_page, home: Path):
    data = nga.load(fetcher, home)
    results = []
    for row in nga.search(data, query, page, per_page):
        results.append({
            'provider': 'nga', 'provider_item_id': row['id'], 'title': _clip(row['title'], 300),
            'creator': _clip(row['creator'], 200), 'date_text': _clip(row['date'], 80), 'medium': _clip(row['medium'], 200),
            'description': _clip(', '.join(row['terms'][:12]), 400),
            'source_url': f"https://www.nga.gov/collection/art-object-page.{row['id']}.html",
            'image_url': f"{row['iiif']}/full/!1600,1600/0/default.jpg", 'image_headers': {},
            'credit_line': _clip(row['credit'], 300),
            'raw': {'openaccess': row.get('openaccess'), 'maxpixels': row.get('maxpixels'), 'viewtype': row.get('viewtype'),
                    'iiifurl': row['iiif'], 'index_built': data['built'], 'index_source': data['source']}})
    return results


_SEARCH = {'aic': _aic, 'met': _met, 'cma': _cma, 'smithsonian': _smithsonian, 'commons': _commons,
           'rijksmuseum': _rijksmuseum}
