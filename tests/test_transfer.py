import csv
import hashlib
import io
import json
import os
import re
import sqlite3
import stat
import zipfile
from datetime import datetime

import pytest
from PIL import Image

from atlas import catalog, transfer
from atlas.store import Store, now

ATTRIBUTION = '"Blue, study" by Zoë — credit exactly.\nCourtesy of the artist.'
LICENSE_URL = 'https://creativecommons.org/licenses/by/4.0/'


def add_image(store, home, number):
    output = io.BytesIO()
    Image.new('RGB', (8, 8), (number * 20, 30, 90)).save(output, format='JPEG')
    data = output.getvalue()
    sha = hashlib.sha256(data).hexdigest()
    paths = {}
    for key, kind in (('original_path', 'originals'), ('analysis_path', 'analysis'), ('thumb_path', 'thumbs')):
        relative = f'{kind}/{sha[:2]}/{sha}.jpg'
        file = home / 'media' / relative
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(data)
        paths[key] = relative
    return store.add_image({
        'provider': 'commons', 'provider_item_id': str(number), 'title': f'Study {number}',
        'creator': 'Zoë', 'date_text': '2026', 'source_url': f'https://commons.wikimedia.org/wiki/{number}',
        'file_sha256': sha, 'analysis_sha256': sha, 'dhash': f'{number:016x}',
        'width': 8, 'height': 8, 'bytes': len(data), 'mime': 'image/jpeg', **paths,
    }, {
        'license_code': 'CC BY', 'license_version': '4.0', 'license_url': LICENSE_URL,
        'label': 'Free with attribution — credit included', 'evidence_url': 'https://example.org/evidence',
        'evidence_json': '{}', 'required_attribution': ATTRIBUTION, 'restrictions': 'No endorsement.',
        'permitted_mode': 'download', 'file_sha256': sha, 'retrieved_at': now(), 'verified_at': now(),
        'policy_sha': 'test', 'provenance_json': '{}',
    }, {
        'aspect': 1, 'orientation': 'square', 'mean_luma': 40, 'contrast': 0,
        'colorfulness': 20, 'saturation': .5, 'palette_json': '[]', 'color_family': 'blue',
    })


@pytest.fixture
def library(tmp_path, monkeypatch):
    monkeypatch.setenv('VISUAL_ATLAS_HOME', str(tmp_path))
    with Store(tmp_path / 'atlas.db') as store:
        catalog.sync(store)
        first, second, removed = [add_image(store, tmp_path, number) for number in (1, 2, 3)]
        collection = store.create_collection('Blue / studies')
        store.collect(collection, first)
        store.collect(collection, removed)
        removed_image = store.remove_image(removed, 'test removal')
        for key in ('original_path', 'analysis_path', 'thumb_path'):
            (tmp_path / 'media' / removed_image[key]).unlink()
        technique = store.one('SELECT id FROM techniques ORDER BY id LIMIT 1')['id']
        analysis = store.add_analysis({
            'image_id': first, 'task': 'analyze', 'backend': 'fake', 'model': 'test',
            'prompt_sha': 'test', 'taxonomy_sha': 'test', 'input_sha': 'test', 'cache_key': 'test',
            'result_json': json.dumps({'summary': 'A blue square.',
                                       'observations': [{'text': 'Blue fills the frame.'}]}),
        })
        store.apply_analysis(first, analysis, [{
            'technique_id': technique, 'evidence': ['Blue fills the frame.'],
            'effect': 'A quiet impression.', 'confidence': .9, 'role': 'primary',
        }], 'fake')
        # A newer, unapplied analysis must not replace the current one in the export.
        record = store.one('SELECT * FROM analyses WHERE id=?', (analysis,))
        record.pop('id')
        record.pop('created_at')
        record['result_json'] = '{"summary": "Unapplied analysis"}'
        store.add_analysis(record)
    return tmp_path, first, second, removed, collection


def media_files(home):
    return {path.relative_to(home).as_posix(): path.read_bytes()
            for path in (home / 'media').rglob('*') if path.is_file()}


def state(home):
    return (home / 'atlas.db').read_bytes(), media_files(home)


def test_credits(library):
    home, first, second, removed, collection = library
    with Store(home / 'atlas.db') as store:
        markdown = transfer.credits(store)
        assert markdown.startswith('# ')
        assert 'Labels describe what was checked and are not legal advice.' in markdown
        for text in (ATTRIBUTION, LICENSE_URL, 'Study 1', 'Study 2', 'Zoë', '2026', 'commons',
                     'CC BY 4.0', 'Free with attribution', 'No endorsement.'):
            assert text in markdown
        assert 'Study 3' not in markdown
        selected = transfer.credits(store, collection_id=collection)
        assert 'Study 1' in selected and 'Study 2' not in selected
        assert 'Study 3' not in selected
        rows = list(csv.DictReader(io.StringIO(transfer.credits(store, fmt='csv'))))
        assert list(rows[0]) == ['id', 'title', 'creator', 'date', 'source', 'source_url', 'license',
                                 'license_url', 'attribution', 'restrictions']
        assert [row['id'] for row in rows] == [str(first), str(second)]
        assert rows[0]['attribution'] == ATTRIBUTION
        assert rows[0]['license_url'] == LICENSE_URL
        assert rows[0]['source_url'] == 'https://commons.wikimedia.org/wiki/1'
        filtered = transfer.credits(store, [second, removed], fmt='csv')
        assert [row['id'] for row in csv.DictReader(io.StringIO(filtered))] == [str(second)]
        assert not list(csv.DictReader(io.StringIO(transfer.credits(store, [], fmt='csv'))))
        assert not list(csv.DictReader(io.StringIO(
            transfer.credits(store, [second], collection_id=collection, fmt='csv'))))
        with pytest.raises(ValueError, match='format'):
            transfer.credits(store, fmt='html')


def test_latest_rights(library):
    home, first, *_ = library
    with Store(home / 'atlas.db') as store:
        rights = store.one('SELECT * FROM rights_records WHERE image_id=?', (first,))
        rights.pop('id')
        rights['required_attribution'] = 'Updated exact attribution'
        with store.transaction():
            store._insert('rights_records', rights)
        result = transfer.credits(store, [first])
        assert 'Updated exact attribution' in result
        assert ATTRIBUTION not in result


def test_export_collection(library):
    home, first, _, _, collection = library
    with Store(home / 'atlas.db') as store:
        original = store.one('SELECT original_path FROM images WHERE id=?', (first,))['original_path']
        path = transfer.export_collection(store, home, collection)
        assert path.parent == home / 'exports'
        assert re.fullmatch(r'visual-atlas-blue-studies-\d{8}-\d{6}\.zip', path.name)
        with zipfile.ZipFile(path) as archive:
            assert set(archive.namelist()) == {f'images/{first}-study-1.jpg', 'CREDITS.md', 'annotations.json'}
            assert archive.read(f'images/{first}-study-1.jpg') == (home / 'media' / original).read_bytes()
            assert archive.read('CREDITS.md').decode() == transfer.credits(store, collection_id=collection)
            entries = json.loads(archive.read('annotations.json'))
            assert [entry['id'] for entry in entries] == [first]
            assert entries[0]['rights']['required_attribution'] == ATTRIBUTION
            assert entries[0]['summary'] == 'A blue square.'
            assert entries[0]['observations'] == [{'text': 'Blue fills the frame.'}]
            annotation = entries[0]['annotations'][0]
            assert set(annotation) == {'technique_id', 'state', 'evidence', 'effect', 'changed_by'}
            assert annotation['state'] == 'proposed'
            assert annotation['evidence'] == ['Blue fills the frame.']
            assert annotation['effect'] == 'A quiet impression.'
            assert annotation['changed_by'] == 'fake'
        with pytest.raises(ValueError, match='^collection not found$'):
            transfer.export_collection(store, home, 9999)


def test_backup_restore(library):
    home, first, second, _, _ = library
    expected_media = media_files(home)
    saved = transfer.backup(home)
    assert saved['images'] == 2
    assert saved['size_bytes'] > 0
    datetime.fromisoformat(saved['created'])
    archive_path = home / 'backups' / saved['name']
    with zipfile.ZipFile(archive_path) as archive:
        original_archive = archive_path.read_bytes()
        expected_db = archive.read('atlas.db')
        manifest = json.loads(archive.read('manifest.json'))
        assert manifest['format'] == 'visual-atlas-backup' and manifest['version'] == 1
        assert manifest['app_version'] and manifest['created'] == saved['created']
        assert set(manifest['files']) == {'atlas.db', *expected_media}
        for name, digest in manifest['files'].items():
            assert hashlib.sha256(archive.read(name)).hexdigest() == digest
    with Store(home / 'atlas.db') as store:
        add_image(store, home, 4)
        mutated_images = store.rows('SELECT * FROM images ORDER BY id')
    mutated = state(home)
    restored = transfer.restore(home, saved['name'])
    assert restored['restored'] == saved['name'] and restored['images'] == 2
    assert restored['safety_backup'] != saved['name']
    assert (home / 'backups' / restored['safety_backup']).is_file()
    assert archive_path.read_bytes() == original_archive
    assert state(home) == (expected_db, expected_media)
    assert not list((home / 'backups').glob('pre-restore-*'))
    assert not (home / 'atlas.db-wal').exists() and not (home / 'atlas.db-shm').exists()
    with Store(home / 'atlas.db') as store:
        assert [row['id'] for row in store.rows('SELECT id FROM images WHERE removed_at IS NULL')] == [first, second]
    # The safety archive can itself recover the state that was just replaced.
    transfer.restore(home, restored['safety_backup'])
    with zipfile.ZipFile(home / 'backups' / restored['safety_backup']) as archive:
        assert state(home) == (archive.read('atlas.db'), mutated[1])
    with Store(home / 'atlas.db') as store:
        assert store.rows('SELECT * FROM images ORDER BY id') == mutated_images


def test_backup_includes_live_wal(library, tmp_path):
    home, *_ = library
    with Store(home / 'atlas.db') as store:
        added = add_image(store, home, 4)
        assert (home / 'atlas.db-wal').stat().st_size > 0
        saved = transfer.backup(home)
    with zipfile.ZipFile(home / 'backups' / saved['name']) as archive:
        snapshot = tmp_path / 'snapshot.db'
        snapshot.write_bytes(archive.read('atlas.db'))
    db = sqlite3.connect(snapshot)
    try:
        assert db.execute('SELECT id FROM images WHERE id=?', (added,)).fetchone() == (added,)
    finally:
        db.close()


def test_backup_uses_snapshot_references(library, monkeypatch):
    home, *_ = library
    expected = media_files(home)
    original_backup = Store.backup_to

    def backup_then_add(store, path):
        original_backup(store, path)
        add_image(store, home, 4)

    monkeypatch.setattr(Store, 'backup_to', backup_then_add)
    orphan = home / 'media' / 'originals' / 'orphan.jpg'
    orphan.write_bytes(b'orphan')
    saved = transfer.backup(home)
    assert saved['images'] == 2
    with zipfile.ZipFile(home / 'backups' / saved['name']) as archive:
        assert set(archive.namelist()) == {'atlas.db', 'manifest.json', *expected}
        snapshot = home / 'snapshot.db'
        snapshot.write_bytes(archive.read('atlas.db'))
    db = sqlite3.connect(snapshot)
    try:
        assert db.execute('SELECT COUNT(*) FROM images WHERE removed_at IS NULL').fetchone() == (2,)
    finally:
        db.close()


@pytest.mark.parametrize('when', ['before snapshot', 'after snapshot'])
def test_backup_missing_media_leaves_no_zip(library, monkeypatch, when):
    home, first, *_ = library
    with Store(home / 'atlas.db') as store:
        relative = store.one('SELECT original_path FROM images WHERE id=?', (first,))['original_path']
    missing = home / 'media' / relative
    if when == 'before snapshot':
        missing.unlink()
    else:
        original_backup = Store.backup_to

        def backup_then_remove(store, path):
            original_backup(store, path)
            missing.unlink()

        monkeypatch.setattr(Store, 'backup_to', backup_then_remove)
    before = (home / 'atlas.db').read_bytes()
    with pytest.raises(ValueError, match=r'^The library changed during the backup; try again\.$'):
        transfer.backup(home)
    assert (home / 'atlas.db').read_bytes() == before
    assert list((home / 'backups').iterdir()) == []


@pytest.mark.parametrize('problem', [
    'version 999', 'missing table', 'missing trigger', 'integrity', 'foreign key', 'missing media',
    'traversal', 'absolute', 'empty path',
])
def test_restore_rejects_unusable_database(library, problem):
    home, first, *_ = library
    saved = transfer.backup(home)
    path = home / 'backups' / saved['name']
    with zipfile.ZipFile(path) as archive:
        payload = {name: archive.read(name) for name in archive.namelist()}
    snapshot = home / 'invalid.db'
    snapshot.write_bytes(payload['atlas.db'])
    db = sqlite3.connect(snapshot)
    try:
        if problem == 'version 999':
            db.execute('PRAGMA user_version=999')
        elif problem == 'missing table':
            db.execute('DROP TABLE job_items')
        elif problem == 'missing trigger':
            db.execute('DROP TRIGGER rights_records_update')
        elif problem == 'foreign key':
            db.execute('UPDATE images SET analysis_id=999999 WHERE id=?', (first,))
        elif problem in ('traversal', 'absolute', 'empty path'):
            relative = {'traversal': 'originals/../../escape.jpg',
                        'absolute': '/originals/aa/' + 'a' * 64 + '.jpg', 'empty path': ''}[problem]
            db.execute('UPDATE images SET original_path=? WHERE id=?', (relative, first))
        elif problem == 'missing media':
            relative = db.execute('SELECT original_path FROM images WHERE id=?', (first,)).fetchone()[0]
            payload.pop(f'media/{relative}')
        db.commit()
    finally:
        db.close()
    payload['atlas.db'] = snapshot.read_bytes()
    if problem == 'integrity':
        # Claim one freelist page without a freelist: readable DB, failed integrity_check.
        payload['atlas.db'] = payload['atlas.db'][:36] + (1).to_bytes(4, 'big') + payload['atlas.db'][40:]
        snapshot.write_bytes(payload['atlas.db'])
        db = sqlite3.connect(snapshot)
        try:
            assert db.execute('PRAGMA integrity_check').fetchall() != [('ok',)]
        finally:
            db.close()
    manifest = json.loads(payload.pop('manifest.json'))
    manifest['files'] = {name: hashlib.sha256(data).hexdigest() for name, data in payload.items()}
    with zipfile.ZipFile(path, 'w') as archive:
        for name, data in payload.items():
            archive.writestr(name, data)
        archive.writestr('manifest.json', json.dumps(manifest))
    before = state(home)
    with pytest.raises(ValueError):
        transfer.restore(home, saved['name'])
    assert state(home) == before
    assert len(transfer.list_backups(home)) == 1
    assert not list(home.glob('.restore-*'))


@pytest.mark.parametrize('name', ['..\\x.zip', '../x.zip', '/x.zip', 'C:evil.zip',
                                 'visual-atlas-backup-123.zip:ads', 'other.zip'])
def test_reject_bad_name(library, name):
    home, *_ = library
    before = state(home)
    with pytest.raises(ValueError):
        transfer.restore(home, name)
    assert state(home) == before
    assert transfer.list_backups(home) == []


@pytest.mark.parametrize('problem', [
    'missing manifest', 'wrong format', 'wrong version', 'tamper', 'unlisted', 'missing payload',
    'invalid database', 'zero database version', 'symlink', 'duplicate',
    '../evil.txt', '/evil.txt', 'C:/evil.txt', '\\evil.txt', 'media/originals/x:stream',
    'media/originals/../evil.txt', 'media/originals/CON', 'media/originals/name.',
    'media/originals/x\\evil.txt', 'media/originals/./evil.txt', 'media//evil.txt',
])
def test_reject_invalid_archive(library, problem):
    home, *_ = library
    saved = transfer.backup(home)
    path = home / 'backups' / saved['name']
    with zipfile.ZipFile(path) as archive:
        payload = {name: archive.read(name) for name in archive.namelist()}
    manifest = json.loads(payload.pop('manifest.json'))
    if problem == 'wrong format':
        manifest['format'] = 'other'
    elif problem == 'wrong version':
        manifest['version'] = 2
    elif problem == 'tamper':
        payload['atlas.db'] += b'tampered'
    elif problem == 'unlisted':
        payload['media/originals/extra.jpg'] = b'extra'
    elif problem == 'missing payload':
        payload.pop(next(name for name in payload if name.startswith('media/')))
    elif problem in ('invalid database', 'zero database version'):
        payload['atlas.db'] = (b'not a database' if problem == 'invalid database'
                               else payload['atlas.db'][:60] + b'\0' * 4 + payload['atlas.db'][64:])
        manifest['files']['atlas.db'] = hashlib.sha256(payload['atlas.db']).hexdigest()
    elif problem not in ('missing manifest', 'symlink', 'duplicate'):
        payload[problem] = b'evil'
        manifest['files'][problem] = hashlib.sha256(b'evil').hexdigest()
    with zipfile.ZipFile(path, 'w') as archive:
        for name, data in payload.items():
            if problem == 'symlink' and name.startswith('media/'):
                info = zipfile.ZipInfo(name)
                info.create_system = 3
                info.external_attr = (stat.S_IFLNK | 0o777) << 16
                archive.writestr(info, data)
            else:
                archive.writestr(name, data)
        if problem == 'duplicate':
            with pytest.warns(UserWarning, match='Duplicate name'):
                archive.writestr('atlas.db', payload['atlas.db'])
        if problem != 'missing manifest':
            archive.writestr('manifest.json', json.dumps(manifest))
    before = state(home)
    with pytest.raises(ValueError):
        transfer.restore(home, saved['name'])
    assert state(home) == before
    assert len(transfer.list_backups(home)) == 1
    assert not list(home.glob('.restore-*'))


@pytest.mark.parametrize('limit', ['MAX_ARCHIVE_BYTES', 'MAX_ARCHIVE_MEMBERS'])
def test_archive_limits(library, monkeypatch, limit):
    home, *_ = library
    saved = transfer.backup(home)
    before = state(home)
    monkeypatch.setattr(transfer, limit, 1)
    with pytest.raises(ValueError, match='limit'):
        transfer.restore(home, saved['name'])
    assert state(home) == before


@pytest.mark.parametrize('phase', ['extract', 'swap'])
def test_restore_failure_preserves_current_data(library, monkeypatch, phase):
    home, *_ = library
    saved = transfer.backup(home)
    with Store(home / 'atlas.db') as store:
        add_image(store, home, 4)
    before = state(home)
    if phase == 'extract':
        original_copy = transfer.shutil.copyfileobj

        def fail_copy(source, target, *args):
            if 'media' in str(target.name):
                raise OSError('simulated extraction failure')
            return original_copy(source, target, *args)

        monkeypatch.setattr(transfer.shutil, 'copyfileobj', fail_copy)
    else:
        original_replace = transfer.os.replace

        def fail_replace(source, target):
            if '.restore-' in str(source) and target == home / 'media':
                raise OSError('simulated rename failure')
            return original_replace(source, target)

        monkeypatch.setattr(transfer.os, 'replace', fail_replace)
    with pytest.raises(OSError, match='simulated'):
        transfer.restore(home, saved['name'])
    assert state(home) == before
    assert len(transfer.list_backups(home)) == 2
    assert not list((home / 'backups').glob('pre-restore-*'))


def test_list_backups_ordering(library):
    home, *_ = library
    assert transfer.list_backups(home) == []
    first, second = transfer.backup(home), transfer.backup(home)
    assert first['name'] != second['name']
    os.utime(home / 'backups' / first['name'], (100, 100))
    os.utime(home / 'backups' / second['name'], (200, 200))
    entries = transfer.list_backups(home)
    assert [entry['name'] for entry in entries] == [second['name'], first['name']]
    for entry in entries:
        assert set(entry) == {'name', 'size_bytes', 'created'}
        assert entry['size_bytes'] == (home / 'backups' / entry['name']).stat().st_size
        datetime.fromisoformat(entry['created'])


def test_restore_replaces_a_damaged_library_even_when_current_files_are_missing(home):
    from helpers import aic_fetcher

    from atlas import jobs as job_module
    from atlas.ai import fake
    with job_module.open_store(home) as store:
        job_module.create_job(store, 'find', {'goal': 'harbour', 'providers': ['aic'], 'backend': 'fake',
                                             'target_new_images': 1})
    job_module.Worker(home, owner='T', fetcher=aic_fetcher(), backends={'fake': fake}).run_once()
    good = transfer.backup(home)
    for path in (home / 'media' / 'thumbs').rglob('*.jpg'):
        path.unlink()  # the current library loses a file
    result = transfer.restore(home, good['name'])
    assert result['images'] == 1
    assert any((home / 'media' / 'thumbs').rglob('*.jpg'))


def test_restore_rejects_a_database_missing_a_table(home):
    import sqlite3
    import zipfile as zf

    from atlas import jobs as job_module
    with job_module.open_store(home):
        pass
    made = transfer.backup(home)
    path = home / 'backups' / made['name']
    with zf.ZipFile(path) as archive:
        payload = {name: archive.read(name) for name in archive.namelist()}
    db_file = home / 'tamper.db'
    db_file.write_bytes(payload['atlas.db'])
    connection = sqlite3.connect(db_file)
    connection.execute('DROP TABLE settings')
    connection.commit()
    connection.close()
    payload['atlas.db'] = db_file.read_bytes()
    manifest = json.loads(payload['manifest.json'])
    manifest['files']['atlas.db'] = hashlib.sha256(payload['atlas.db']).hexdigest()
    payload['manifest.json'] = json.dumps(manifest).encode()
    with zf.ZipFile(path, 'w') as archive:
        for name, data in payload.items():
            archive.writestr(name, data)
    with pytest.raises(ValueError, match='expected tables'):
        transfer.restore(home, made['name'])
