"""Credits and portable archives. Callers must quiesce database/media users before restore."""

import csv
import hashlib
import io
import json
import ntpath
import os
import re
import shutil
import sqlite3
import stat
import tempfile
import zipfile
from contextlib import closing
from datetime import UTC, datetime, timedelta
from pathlib import Path

from atlas import __version__
from atlas.store import Store

MAX_ARCHIVE_BYTES = 20 * 1024**3
MAX_ARCHIVE_MEMBERS = 200_000
MEDIA_KINDS = ('originals', 'analysis', 'thumbs')
RIGHTS_FIELDS = ('license_code', 'license_version', 'license_url', 'label',
                 'required_attribution', 'evidence_url', 'restrictions')


def referenced_media(store: Store) -> set[str]:
    """Every media path a database row refers to (anything else in media/ is a crash leftover)."""
    paths = set()
    for row in store.rows('SELECT original_path, analysis_path, thumb_path FROM images'):
        paths.update(p for p in row.values() if p)
    return paths


def _images(store, image_ids=None, collection_id=None):
    query = ('SELECT i.*, ' + ', '.join(f'r.{field}' for field in RIGHTS_FIELDS)
             + ' FROM images i LEFT JOIN rights_records r ON r.id='
             '(SELECT MAX(id) FROM rights_records WHERE image_id=i.id) WHERE i.removed_at IS NULL')
    parameters = []
    if image_ids is not None:
        if not image_ids:
            return []
        query += ' AND i.id IN (' + ','.join('?' for _ in image_ids) + ')'
        parameters.extend(image_ids)
    if collection_id is not None:
        query += ' AND i.id IN (SELECT image_id FROM collection_items WHERE collection_id=?)'
        parameters.append(collection_id)
    return store.rows(query + ' ORDER BY i.id', parameters)


def credits(store: Store, image_ids: list[int] | None = None,
            collection_id: int | None = None, fmt: str = 'md') -> str:
    """Export the latest recorded rights without making a new rights decision."""
    if fmt not in ('md', 'csv'):
        raise ValueError('credits format must be md or csv')
    rows = _images(store, image_ids, collection_id)
    if fmt == 'csv':
        output = io.StringIO(newline='')
        writer = csv.writer(output)
        writer.writerow(('id', 'title', 'creator', 'date', 'source', 'source_url', 'license',
                         'license_url', 'attribution', 'restrictions'))
        for row in rows:
            licence = ' '.join(filter(None, (row['license_code'], row['license_version'])))
            writer.writerow((row['id'], row['title'], row['creator'], row['date_text'], row['provider'],
                             row['source_url'], licence, row['license_url'],
                             row['required_attribution'], row['restrictions']))
        return output.getvalue()
    lines = ['# Visual Atlas credits', '',
             'Labels describe what was checked and are not legal advice.', '']
    for row in rows:
        licence = ' '.join(filter(None, (row['license_code'], row['license_version'])))
        lines.extend((f"## {row['title']} (#{row['id']})", '',
                      f"Creator: {row['creator']}", f"Date: {row['date_text']}",
                      f"Source: {row['provider']}",
                      f"Licence: {row['label'] or 'Not recorded'} — [{licence}]({row['license_url'] or ''})",
                      '', row['required_attribution'] or '', '', f"Source URL: {row['source_url']}"))
        if row['restrictions']:
            lines.append(f"Restrictions: {row['restrictions']}")
        lines.append('')
    return '\n'.join(lines)


def _slug(text):
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')[:80] or 'untitled'


def _archive_path(directory, prefix):
    directory.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC)
    while True:
        path = directory / f'{prefix}-{stamp:%Y%m%d-%H%M%S}.zip'
        if not path.exists():
            return path
        stamp += timedelta(seconds=1)


def export_collection(store: Store, home: Path, collection_id: int) -> Path:
    collection = store.one('SELECT name FROM collections WHERE id=?', (collection_id,))
    if collection is None:
        raise ValueError('collection not found')
    home = Path(home)
    path = _archive_path(home / 'exports', 'visual-atlas-' + _slug(collection['name']))
    media = (home / 'media').resolve()
    with tempfile.TemporaryDirectory(dir=path.parent) as temporary:
        archive_path = Path(temporary) / 'collection.zip'
        with store.reading(), zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as archive:
            annotations = []
            for row in _images(store, collection_id=collection_id):
                original = (media / (row['original_path'] or '')).resolve()
                if not original.is_relative_to(media / 'originals') or not original.is_file():
                    raise ValueError(f"original file missing or outside originals: {row['id']}")
                archive.write(original, f"images/{row['id']}-{_slug(row['title'])}{original.suffix}")
                analysis = store.one('SELECT result_json FROM analyses WHERE id=?', (row['analysis_id'],))
                result = json.loads(analysis['result_json']) if analysis else {}
                items = store.rows('SELECT technique_id, state, evidence_json, effect, changed_by '
                                   'FROM annotations WHERE image_id=? ORDER BY technique_id', (row['id'],))
                for item in items:
                    item['evidence'] = json.loads(item.pop('evidence_json'))
                annotations.append({'id': row['id'], 'title': row['title'],
                                    'rights': {field: row[field] for field in RIGHTS_FIELDS},
                                    'observations': result.get('observations', []),
                                    'summary': result.get('summary', ''), 'annotations': items})
            archive.writestr('CREDITS.md', credits(store, collection_id=collection_id))
            archive.writestr('annotations.json', json.dumps(annotations, ensure_ascii=False, indent=2))
        os.replace(archive_path, path)
    return path


def _file_info(path):
    info = path.stat()
    return {'name': path.name, 'size_bytes': info.st_size,
            'created': datetime.fromtimestamp(info.st_mtime, UTC).isoformat()}


def list_backups(home) -> list[dict]:
    entries = [_file_info(path) for path in (Path(home) / 'backups').glob('*.zip') if path.is_file()]
    return sorted(entries, key=lambda entry: (entry['created'], entry['name']), reverse=True)


def _database_images(path):
    # immutable keeps validation read-only, including for a database saved in WAL mode.
    with closing(sqlite3.connect(path.resolve().as_uri() + '?mode=ro&immutable=1', uri=True)) as db:
        if db.execute('PRAGMA user_version').fetchone()[0] < 1:
            raise ValueError('unsupported backup database version')
        return db.execute('SELECT COUNT(*) FROM images WHERE removed_at IS NULL').fetchone()[0]


def backup(home) -> dict:
    home = Path(home)
    path = _archive_path(home / 'backups', 'visual-atlas-backup')
    created = datetime.now(UTC).isoformat()
    with tempfile.TemporaryDirectory(dir=path.parent) as temporary:
        temporary = Path(temporary)
        snapshot = temporary / 'atlas.db'
        with Store(home / 'atlas.db') as store:
            store.backup_to(snapshot)
        count = _database_images(snapshot)
        files = {'atlas.db': snapshot}
        for kind in MEDIA_KINDS:
            for file in sorted((home / 'media' / kind).rglob('*')):
                if file.is_file():
                    if not file.resolve().is_relative_to((home / 'media').resolve()):
                        raise ValueError('media file outside library')
                    files[file.relative_to(home).as_posix()] = file
        hashes = {}
        archive_path = temporary / 'backup.zip'
        with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as archive:
            for name, file in files.items():
                digest = hashlib.sha256()
                with file.open('rb') as source, archive.open(name, 'w', force_zip64=True) as target:
                    while chunk := source.read(1024 * 1024):
                        digest.update(chunk)
                        target.write(chunk)
                hashes[name] = digest.hexdigest()
            archive.writestr('manifest.json', json.dumps({
                'format': 'visual-atlas-backup', 'version': 1, 'created': created,
                'app_version': __version__, 'files': hashes}, indent=2))
        os.replace(archive_path, path)
    return {**_file_info(path), 'created': created, 'images': count}


def _validate_archive(archive):
    members = archive.infolist()
    if len(members) > MAX_ARCHIVE_MEMBERS or sum(item.file_size for item in members) > MAX_ARCHIVE_BYTES:
        raise ValueError('backup exceeds size or member count limit')
    names = set()
    for item in members:
        name = item.filename
        parts = name.split('/')
        if (name != item.orig_filename or '\\' in name or ':' in name
                or any(part in ('', '.', '..') or ntpath.isreserved(part) for part in parts)
                or name.casefold() in names
                or stat.S_IFMT(item.external_attr >> 16) not in (0, stat.S_IFREG)
                or not (name in ('atlas.db', 'manifest.json')
                        or len(parts) >= 3 and parts[0] == 'media' and parts[1] in MEDIA_KINDS)):
            raise ValueError('invalid backup member path or type')
        names.add(name.casefold())
    if 'manifest.json' not in archive.namelist():
        raise ValueError('backup manifest missing')
    with archive.open('manifest.json') as source:
        manifest = json.load(source)
    if (not isinstance(manifest, dict) or manifest.get('format') != 'visual-atlas-backup'
            or manifest.get('version') != 1 or not isinstance(manifest.get('files'), dict)):
        raise ValueError('invalid backup manifest')
    files = manifest['files']
    if set(files) != set(archive.namelist()) - {'manifest.json'} or 'atlas.db' not in files:
        raise ValueError('backup members do not match manifest')
    for name, expected in files.items():
        with archive.open(name) as source:
            if hashlib.file_digest(source, 'sha256').hexdigest() != expected:
                raise ValueError('backup checksum mismatch')


def restore(home, name) -> dict:
    """Validate and stage first; roll back completed renames if the swap fails."""
    if not isinstance(name, str) or not re.fullmatch(r'visual-atlas-backup-[0-9-]+\.zip', name):
        raise ValueError('invalid backup name')
    home = Path(home).resolve()
    path = home / 'backups' / name
    if not path.is_file() or path.resolve().parent != (home / 'backups').resolve():
        raise ValueError('backup not found')
    with tempfile.TemporaryDirectory(prefix='.restore-', dir=home) as temporary:
        stage = Path(temporary)
        try:
            with zipfile.ZipFile(path) as archive:
                _validate_archive(archive)
                with archive.open('atlas.db') as source, (stage / 'atlas.db').open('wb') as target:
                    shutil.copyfileobj(source, target)
                count = _database_images(stage / 'atlas.db')
                safety = backup(home)
                (stage / 'media').mkdir()
                for item in archive.infolist():
                    if not item.filename.startswith('media/'):
                        continue
                    target_path = stage / item.filename
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    with archive.open(item) as source, target_path.open('wb') as target:
                        shutil.copyfileobj(source, target)
        except (zipfile.BadZipFile, sqlite3.DatabaseError, UnicodeError, RuntimeError) as error:
            raise ValueError('invalid backup archive') from error

        previous = Path(tempfile.mkdtemp(prefix=f'pre-restore-{datetime.now(UTC):%Y%m%d-%H%M%S}-',
                                         dir=home / 'backups'))
        moved = []
        try:
            for filename in ('atlas.db', 'atlas.db-wal', 'atlas.db-shm', 'media'):
                source, target = home / filename, previous / filename
                if source.exists():
                    os.replace(source, target)
                    moved.append((source, target))
            for filename in ('atlas.db', 'media'):
                source, target = stage / filename, home / filename
                os.replace(source, target)
                moved.append((source, target))
        except BaseException:
            for source, target in reversed(moved):
                os.replace(target, source)
            shutil.rmtree(previous)
            raise
        shutil.rmtree(previous)
    return {'restored': name, 'images': count, 'safety_backup': safety['name']}
