"""Search connectors for the enabled open-access providers. Each returns candidate dicts:

provider, provider_item_id, title, creator, date_text, medium, description, source_url, image_url,
image_headers, raw (the exact licence evidence fields rights.py checks)."""

import re

from atlas.fetch import Fetcher, FetchError
from atlas.home import local_setting
from atlas.rights import plain

PROVIDERS = ('aic', 'met', 'cma', 'smithsonian', 'commons')
NAMES = {'aic': 'Art Institute of Chicago', 'met': 'The Met', 'cma': 'Cleveland Museum of Art',
         'smithsonian': 'Smithsonian', 'commons': 'Wikimedia Commons'}
# Commons structured-data licence statements used only to narrow searches; each file is still checked.
COMMONS_LICENCES = ('haswbstatement:P275=Q6938433|P275=Q20007257|P275=Q14947546|P275=Q19125117'
                    '|P6216=Q19652')


def _clip(value, limit=500) -> str:
    # Commons templates leak Wikidata residue such as "1812 date QS:P571,+1812-00-00T00:00:00Z/9".
    text = re.sub(r'\s*\b(?:date|title)\s+QS:P\d+,(?:[a-z-]+:)?(?:"[^"]*"|\S*)\S*', '', plain(value))
    return text.strip()[:limit]


def search(fetcher: Fetcher, provider: str, query: str, page: int = 0, per_page: int = 10) -> list[dict]:
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
        title = plain((meta.get('ObjectName') or {}).get('value')) or item.get('title', '').removeprefix('File:')
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


_SEARCH = {'aic': _aic, 'met': _met, 'cma': _cma, 'smithsonian': _smithsonian, 'commons': _commons}
