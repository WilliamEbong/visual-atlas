"""The National Gallery of Art publishes its collection as CC0 open data (CSV files on GitHub) with no search API.

The first search downloads three files (about 190 MB), keeps only open-access primary images in a compact index
in the library folder (a few MB) and deletes the files. Searches match words against that index. The rights
evidence (openaccess, maxpixels, viewtype) is copied into each candidate for atlas/rights.py to check.
ponytail: linear scan over ~60k rows per search; a word index if searches ever feel slow."""

import csv
import gzip
import json
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path

from atlas.fetch import Fetcher, FetchError

DATA = 'https://raw.githubusercontent.com/NationalGalleryOfArt/opendata/main/data/'
FILES = ('published_images.csv', 'objects.csv', 'objects_terms.csv')
MAX_FILE_BYTES = 150 * 1024 * 1024
MAX_AGE = timedelta(days=30)
SKIP_TERMS = {'Keywords', 'Themes', 'Styles', 'Schools', 'Techniques'}
COLUMNS = {'published_images.csv': {'depictstmsobjectid', 'openaccess', 'maxpixels', 'viewtype', 'iiifurl'},
           'objects.csv': {'objectid', 'title', 'attribution', 'displaydate', 'medium'},
           'objects_terms.csv': {'objectid', 'term'}}
csv.field_size_limit(10 * 1024 * 1024)


def folder(home: Path) -> Path:
    return home / 'sources' / 'nga'


def _words(text: str) -> list[str]:
    return re.findall(r'[a-z0-9]{3,}', text.lower())


def _rows(path: Path, name: str):
    """CSV rows, after checking the file still has the columns this index reads (a changed format must not
    quietly produce an empty index that lasts 30 days)."""
    with path.open(encoding='utf-8', newline='') as handle:
        reader = csv.DictReader(handle)
        missing = COLUMNS[name] - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f'{name} lacks {sorted(missing)}')
        yield from reader


def build(fetcher: Fetcher, home: Path, files: dict[str, Path] | None = None) -> Path:
    """Download (unless `files` gives local copies), filter to open-access primary images, write the index."""
    out = folder(home)
    out.mkdir(parents=True, exist_ok=True)
    given = dict(files or {})
    paths = dict(given)
    index = out / 'index.json.gz'
    try:
        for name in FILES:
            if name in paths:
                continue
            part = out / f'{name}.part'
            with part.open('wb') as sink:
                fetcher.get('nga', DATA + name, max_bytes=MAX_FILE_BYTES, types=('text/plain', 'text/csv'), sink=sink)
            part.replace(out / name)
            paths[name] = out / name
        rows = _index_rows(paths)
        if not rows:
            raise ValueError('no open-access images in the open data')
        with gzip.open(index.with_suffix('.part'), 'wt', encoding='utf-8') as handle:
            json.dump({'built': datetime.now(UTC).isoformat(timespec='seconds'), 'source': DATA, 'rows': rows}, handle)
        index.with_suffix('.part').replace(index)
    finally:  # downloads are large: never leave them (or half-written files) behind, whatever happened
        for name in FILES:
            if name not in given:
                (out / name).unlink(missing_ok=True)
                (out / f'{name}.part').unlink(missing_ok=True)
        index.with_suffix('.part').unlink(missing_ok=True)
    return index


def _index_rows(paths: dict[str, Path]) -> list[dict]:
    images: dict[str, dict] = {}
    for row in _rows(paths['published_images.csv'], 'published_images.csv'):
        object_id = row.get('depictstmsobjectid') or ''
        if (row.get('openaccess') == '1' and not row.get('maxpixels') and row.get('viewtype') == 'primary'
                and object_id and object_id not in images and row.get('iiifurl', '').startswith('https://api.nga.gov/iiif/')):
            images[object_id] = {'iiif': row['iiifurl'], 'width': int(row.get('width') or 0),
                                 'height': int(row.get('height') or 0), 'openaccess': row['openaccess'],
                                 'maxpixels': row['maxpixels'], 'viewtype': row['viewtype']}  # the record's own values
    terms: dict[str, list[str]] = {}
    for row in _rows(paths['objects_terms.csv'], 'objects_terms.csv'):
        if row.get('objectid') in images and row.get('term') and row['term'] not in SKIP_TERMS:
            terms.setdefault(row['objectid'], []).append(row['term'])
    rows = []
    for row in _rows(paths['objects.csv'], 'objects.csv'):
        image = images.get(row.get('objectid') or '')
        if image is None:
            continue
        text = {key: str(row.get(field) or '') for key, field in (  # short rows give None: never store it
            ('title', 'title'), ('creator', 'attribution'), ('date', 'displaydate'), ('medium', 'medium'),
            ('classification', 'classification'), ('credit', 'creditline'), ('accession', 'accessionnum'))}
        rows.append({'id': row['objectid'], **text, 'terms': sorted(set(terms.get(row['objectid'], [])))[:30], **image})
    return rows


_cache: dict[str, tuple[float, dict]] = {}


def load(fetcher: Fetcher, home: Path) -> dict:
    index = folder(home) / 'index.json.gz'
    fresh = index.exists() and datetime.now(UTC) - datetime.fromtimestamp(index.stat().st_mtime, UTC) < MAX_AGE
    if not fresh:
        try:
            build(fetcher, home)
        except (FetchError, csv.Error, KeyError, ValueError, OSError) as error:
            if not index.exists():  # an old index still serves searches when a refresh fails
                if isinstance(error, FetchError):
                    raise
                raise FetchError('bad_data', 'The National Gallery open data could not be read.') from None
    stamp = index.stat().st_mtime
    key = str(index)
    if key not in _cache or _cache[key][0] != stamp:
        with gzip.open(index, 'rt', encoding='utf-8') as handle:
            data = json.load(handle)
        for row in data['rows']:
            row['_text'] = ' '.join(_words(' '.join([row['title'], row['creator'], row['medium'], row['classification'],
                                                     *row['terms']])))
        _cache[key] = (stamp, data)
    return _cache[key][1]


def search(data: dict, query: str, page: int, per_page: int) -> list[dict]:
    """Rows containing every query word first, then rows containing most of them."""
    wanted = [word for word in dict.fromkeys(_words(query))]
    if not wanted:
        return []
    scored = []
    for row in data['rows']:
        text = f" {row['_text']} "
        score = sum(f' {word}' in text for word in wanted)  # word starts, so "sunset" finds "sunsets"
        if score:
            scored.append((-score, int(row['id']) if row['id'].isdigit() else 0, row))
    scored.sort(key=lambda item: item[:2])
    best = -scored[0][0] if scored else 0
    rows = [row for score, _, row in scored if -score >= max(1, best - 1)]
    return rows[page * per_page:(page + 1) * per_page]
