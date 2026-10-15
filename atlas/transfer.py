"""Credits, portable archives, restore and media clean-up (the last two under the library's maintenance mode)."""

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

from atlas import __version__, images
from atlas.store import APPEND_ONLY, MAINTENANCE_KEY, LibraryBusy, Store

MAX_ARCHIVE_BYTES = 20 * 1024**3
MAX_ARCHIVE_MEMBERS = 200_000
MEDIA_KINDS = ('originals', 'analysis', 'thumbs')
MEDIA_PATH = re.compile(r'(originals|analysis|thumbs)/[0-9a-f]{2}/[0-9a-f]{64}\.(jpg|png|webp)')
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
                reduced = original.is_relative_to(media / 'analysis')
                if not (original.is_relative_to(media / 'originals') or reduced) or not original.is_file():
                    raise ValueError(f"original file missing or outside originals/analysis: {row['id']}")
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
                if reduced:
                    annotations[-1]['file'] = 'reduced copy (starter library)'
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


def _schema(db) -> set[tuple]:
    return {(kind, name, ' '.join((sql or '').split())) for kind, name, sql in db.execute(
        "SELECT type, name, sql FROM sqlite_schema WHERE name NOT LIKE 'sqlite_%'")}


_REFERENCE: dict = {}


def _reference_schema() -> tuple[int, set[tuple]]:
    """The exact schema this version creates (built once from the migrations in a scratch database)."""
    if not _REFERENCE:
        with tempfile.TemporaryDirectory() as directory:
            with Store(Path(directory) / 'reference.db') as store:
                _REFERENCE['version'] = store.connection.execute('PRAGMA user_version').fetchone()[0]
                _REFERENCE['schema'] = _schema(store.connection)
    return _REFERENCE['version'], _REFERENCE['schema']


def _upgrade_staged(path):
    """A backup from an older Visual Atlas is migrated in its staging copy (never in place) before validation."""
    with closing(sqlite3.connect(path.resolve().as_uri() + '?mode=ro&immutable=1', uri=True)) as db:
        found = db.execute('PRAGMA user_version').fetchone()[0]
    if not 1 <= found <= _reference_schema()[0]:
        raise ValueError('unsupported backup database version')
    if found < _reference_schema()[0]:
        with Store(path):
            pass


def _validate_database(path, members, missing=frozenset()):
    # immutable keeps validation read-only, including for a database saved in WAL mode.
    with closing(sqlite3.connect(path.resolve().as_uri() + '?mode=ro&immutable=1', uri=True)) as db:
        version, schema = _reference_schema()
        if db.execute('PRAGMA user_version').fetchone()[0] != version:
            raise ValueError('unsupported backup database version')
        if _schema(db) != schema:
            raise ValueError('backup database does not have the expected tables, columns and triggers')
        if db.execute('PRAGMA integrity_check').fetchall() != [('ok',)]:
            raise ValueError('backup database failed integrity check')
        if db.execute('PRAGMA foreign_key_check').fetchone() is not None:
            raise ValueError('backup database failed foreign key check')
        tables = {row[0] for row in db.execute("SELECT name FROM sqlite_schema WHERE type='table'")}
        if not {'images', 'rights_records', 'annotations', 'analyses', 'jobs', 'job_items',
                'collections', 'techniques'} <= tables:
            raise ValueError('backup database is missing core tables')
        triggers = set(db.execute("SELECT name, tbl_name FROM sqlite_schema WHERE type='trigger'"))
        if not {(f'{table}_{action}', table) for table in APPEND_ONLY
                for action in ('update', 'delete')} <= triggers:
            raise ValueError('backup database is missing append-only triggers')
        for row in db.execute('SELECT original_path, analysis_path, thumb_path FROM images '
                              'WHERE removed_at IS NULL'):
            for relative in row:
                if relative is not None and (not isinstance(relative, str)
                                             or not MEDIA_PATH.fullmatch(relative)
                                             or (f'media/{relative}' not in members and relative not in missing)):
                    raise ValueError('backup database references invalid or missing media')
        return db.execute('SELECT COUNT(*) FROM images WHERE removed_at IS NULL').fetchone()[0]


def backup(home, allow_missing: bool = False) -> dict:
    """Back up the library. allow_missing (used only for the safety copy before a restore) records files that are
    already missing instead of refusing, so a damaged library can still be replaced by a good backup."""
    home = Path(home)
    missing = []
    path = _archive_path(home / 'backups', 'visual-atlas-backup')
    created = datetime.now(UTC).isoformat()
    with tempfile.TemporaryDirectory(dir=path.parent) as temporary:
        temporary = Path(temporary)
        snapshot = temporary / 'atlas.db'
        with Store(home / 'atlas.db') as store:
            store.backup_to(snapshot)
        with closing(sqlite3.connect(snapshot)) as db:  # a backup never carries a restore's maintenance marker
            if db.execute('SELECT 1 FROM settings WHERE key=?', (MAINTENANCE_KEY,)).fetchone():
                db.execute('DELETE FROM settings WHERE key=?', (MAINTENANCE_KEY,))
                db.commit()
        files = {'atlas.db': snapshot}
        media = (home / 'media').resolve()
        with closing(sqlite3.connect(snapshot.resolve().as_uri() + '?mode=ro&immutable=1', uri=True)) as db:
            count = db.execute('SELECT COUNT(*) FROM images WHERE removed_at IS NULL').fetchone()[0]
            for row in db.execute('SELECT original_path, analysis_path, thumb_path FROM images'):
                for relative in row:
                    if relative is None:
                        continue
                    file = media / relative
                    if not MEDIA_PATH.fullmatch(relative) or not file.resolve().is_relative_to(media):
                        raise ValueError('media file outside library')
                    if allow_missing and not file.is_file():
                        missing.append(relative)
                        continue
                    files[f'media/{relative}'] = file
        hashes = {}
        archive_path = temporary / 'backup.zip'
        with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as archive:
            for name, file in files.items():
                digest = hashlib.sha256()
                try:
                    with file.open('rb') as source, archive.open(name, 'w', force_zip64=True) as target:
                        while chunk := source.read(1024 * 1024):
                            digest.update(chunk)
                            target.write(chunk)
                except FileNotFoundError as error:
                    raise ValueError('The library changed during the backup; try again.') from error
                hashes[name] = digest.hexdigest()
            archive.writestr('manifest.json', json.dumps({
                'format': 'visual-atlas-backup', 'version': 1, 'created': created,
                'app_version': __version__, 'files': hashes, 'missing': sorted(set(missing))}, indent=2))
        os.replace(archive_path, path)
    return {**_file_info(path), 'created': created, 'images': count, 'missing': len(set(missing))}


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
    missing = manifest.get('missing', [])
    if not isinstance(missing, list) or not all(isinstance(m, str) and MEDIA_PATH.fullmatch(m) for m in missing):
        raise ValueError('invalid backup manifest')
    for name, expected in files.items():
        with archive.open(name) as source:
            if hashlib.file_digest(source, 'sha256').hexdigest() != expected:
                raise ValueError('backup checksum mismatch')
    return frozenset(missing)


def restore(home, name) -> dict:
    """Replace the library with a backup without ever losing an acknowledged change.

    Everything is validated (and an older backup migrated) in a staging copy first. Then, under maintenance mode
    (no job running, every other write refused): a safety backup of the current library, media copied in
    additively, and the database contents replaced in one atomic SQLite backup step. No file is renamed, so an
    interruption leaves either the previous library or the restored one; files left over are cleaned up."""
    if not isinstance(name, str) or not re.fullmatch(r'visual-atlas-backup-[0-9-]+\.zip', name):
        raise ValueError('invalid backup name')
    home = Path(home).resolve()
    path = home / 'backups' / name
    if not path.is_file() or path.resolve().parent != (home / 'backups').resolve():
        raise ValueError('backup not found')
    with tempfile.TemporaryDirectory(prefix='visual-atlas-restore-') as temporary:  # outside the library
        staged = Path(temporary) / 'atlas.db'
        try:
            with zipfile.ZipFile(path) as archive:
                missing = _validate_archive(archive)
                with archive.open('atlas.db') as source, staged.open('wb') as target:
                    shutil.copyfileobj(source, target)
                hashes = json.loads(archive.read('manifest.json'))['files']
            _upgrade_staged(staged)
            count = _validate_database(staged, set(hashes) | {'manifest.json'}, missing)
        except (zipfile.BadZipFile, sqlite3.DatabaseError, UnicodeError, KeyError, RuntimeError) as error:
            raise ValueError('invalid backup archive') from error
        with zipfile.ZipFile(path) as archive, Store(home / 'atlas.db') as live, live.maintenance(idle='jobs'):
            safety = backup(home, allow_missing=True)
            _copy_media(archive, hashes, home / 'media')
            with closing(sqlite3.connect(staged)) as source:
                source.backup(live.connection)  # atomic: other connections see the old or the new library, never a mix
            images.sweep_orphans(home / 'media', referenced_media(live))
    return {'restored': name, 'images': count, 'safety_backup': safety['name']}


def _copy_media(archive, hashes: dict, media: Path):
    """Add the backup's media files; content-addressed names make this safe for the current library too."""
    for item in archive.infolist():
        if not item.filename.startswith('media/'):
            continue
        target = media / item.filename.removeprefix('media/')
        if target.is_file() and hashlib.sha256(target.read_bytes()).hexdigest() == hashes[item.filename]:
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        part = target.with_name(target.name + '.part')
        digest = hashlib.sha256()
        with archive.open(item) as source, part.open('wb') as out:
            while chunk := source.read(1024 * 1024):
                digest.update(chunk)
                out.write(chunk)
        if digest.hexdigest() != hashes[item.filename]:  # the backup file changed since it was validated
            part.unlink()
            raise ValueError('backup checksum mismatch')
        os.replace(part, target)


def sweep(home) -> int | None:
    """Delete media no row refers to (crash leftovers) and stale restore folders, under maintenance mode so no
    worker can be mid-download. Skipped (None) while a job holds a live lease or other maintenance runs."""
    home = Path(home)
    try:
        with Store(home / 'atlas.db') as store, store.maintenance(idle='leases'):
            for folder in home.glob('.restore-*'):  # staging left in the library by a 0.1 restore that crashed
                shutil.rmtree(folder, ignore_errors=True)
            return images.sweep_orphans(home / 'media', referenced_media(store))
    except LibraryBusy:
        return None


STARTER_IMAGE_FIELDS = ('provider', 'provider_item_id', 'title', 'creator', 'date_text', 'medium', 'description',
                        'source_url', 'file_sha256', 'analysis_sha256', 'dhash', 'width', 'height', 'bytes', 'mime',
                        'status', 'favorite')


def export_starter(store: Store, home: Path, out: Path) -> int:
    """Write the library as a starter pack: library.json plus the ≤1024 px copies and thumbnails.

    The full-size originals stay out (size); each record keeps the original's SHA-256 so a later download of the
    same original is recognised as a duplicate."""
    home, out = Path(home), Path(out)
    if out.exists():
        shutil.rmtree(out)
    references = []
    for row in store.rows('SELECT * FROM images WHERE removed_at IS NULL AND status=\'ready\' ORDER BY id'):
        for key in ('analysis_path', 'thumb_path'):
            target = out / 'media' / row[key]
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(home / 'media' / row[key], target)
        rights = store.one('SELECT * FROM rights_records WHERE image_id=? ORDER BY id DESC LIMIT 1', (row['id'],))
        metrics = store.one('SELECT * FROM image_metrics WHERE image_id=?', (row['id'],))
        analyses = store.rows("SELECT * FROM analyses WHERE image_id=? AND task IN ('analyze','verify') ORDER BY id",
                              (row['id'],))
        annotations = store.rows('SELECT technique_id, state, role, evidence_json, effect, confidence, analysis_id, '
                                 'human_locked, changed_by, note, updated_at FROM annotations WHERE image_id=?', (row['id'],))
        references.append({
            'image': {**{k: row[k] for k in STARTER_IMAGE_FIELDS}, 'analysis_path': row['analysis_path'],
                      'thumb_path': row['thumb_path']},
            'rights': {k: v for k, v in rights.items() if k not in ('id', 'image_id')},
            'metrics': {k: v for k, v in metrics.items() if k != 'image_id'},
            'analyses': [{k: v for k, v in a.items() if k not in ('image_id', 'job_id')} for a in analyses],
            'annotations': annotations, 'current_analysis': row['analysis_id']})
    (out / 'library.json').write_text(json.dumps({'format': 'visual-atlas-starter', 'version': 1,
                                                  'app_version': __version__, 'references': references},
                                                 ensure_ascii=False, indent=1), encoding='utf-8')
    return len(references)


def import_starter(store: Store, home: Path, source: Path) -> int:
    """Add the bundled starter references to a library (skips ones already present or removed)."""
    home, source = Path(home), Path(source)
    source_media, target_media = (source / 'media').resolve(), (home / 'media').resolve()
    data = json.loads((source / 'library.json').read_text(encoding='utf-8'))
    if data.get('format') != 'visual-atlas-starter' or data.get('version') != 1:
        raise ValueError('not a Visual Atlas starter pack')
    added = 0
    for reference in data['references']:
        image = dict(reference['image'])
        paths = {key: image.pop(key) for key in ('analysis_path', 'thumb_path')}
        for key, relative in paths.items():
            if not isinstance(relative, str) or not re.fullmatch(r'(analysis|thumbs)/[0-9a-f]{2}/[0-9a-f]{64}\.jpg', relative):
                raise ValueError('unexpected path in starter pack')
            parts = relative.split('/')
            if (parts[1] != parts[2][:2]
                    or not (source_media / relative).resolve().is_relative_to(source_media)
                    or not (target_media / relative).resolve().is_relative_to(target_media)):
                raise ValueError('unexpected path in starter pack')
            if key == 'analysis_path' and hashlib.sha256((source / 'media' / relative).read_bytes()).hexdigest() != \
                    image['analysis_sha256']:
                raise ValueError('starter image does not match its checksum')
        provenance = json.loads(reference['rights']['provenance_json'])
        provenance['starter_copy'] = 'Bundled reduced copy (≤1024 px); the full original is at the source.'
        rights = {**reference['rights'], 'provenance_json': json.dumps(provenance, ensure_ascii=False, sort_keys=True)}
        image_id = store.import_reference(
            {**image, 'original_path': paths['analysis_path'], **paths}, rights, reference['metrics'],
            reference['analyses'], reference['annotations'], reference['current_analysis'])
        added += image_id is not None
        if image_id is not None or store.one('SELECT 1 FROM images WHERE file_sha256=? AND removed_at IS NULL',
                                             (image['file_sha256'],)):
            for relative in paths.values():  # written after the row commits, so clean-up never sees them as strays
                target = home / 'media' / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                if not target.exists():
                    shutil.copyfile(source / 'media' / relative, target)
    return added
