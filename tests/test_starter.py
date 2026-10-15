"""The bundled starter pack round-trips with review states, rights and search intact."""

import json

import pytest
from helpers import aic_fetcher

from atlas import jobs, transfer
from atlas.ai import fake


def build_library(home):
    with jobs.open_store(home) as store:
        jobs.create_job(store, 'find', {'goal': 'harbour', 'providers': ['aic'], 'backend': 'fake', 'target_new_images': 2})
    jobs.Worker(home, owner='T', fetcher=aic_fetcher(), backends={'fake': fake}).run_once()


def test_export_then_import_into_a_fresh_library(tmp_path):
    source, target, pack = tmp_path / 'source', tmp_path / 'target', tmp_path / 'starter'
    build_library(source)
    with jobs.open_store(source) as store:
        image = store.one('SELECT id FROM images')['id']
        technique = store.one('SELECT technique_id FROM annotations WHERE image_id=?', (image,))['technique_id']
        store.human_annotation(image, technique, state='human_reviewed', evidence=['visible thing'])
        assert transfer.export_starter(store, source, pack) == 2
    data = json.loads((pack / 'library.json').read_text(encoding='utf-8'))
    assert all(r['rights']['required_attribution'] for r in data['references'])
    assert not list(pack.glob('media/originals/**/*.*'))  # full originals are not bundled
    with jobs.open_store(target) as store:
        assert transfer.import_starter(store, target, pack) == 2
        assert transfer.import_starter(store, target, pack) == 0  # idempotent
        rows = store.rows('SELECT * FROM images')
        assert all((target / 'media' / r['original_path']).is_file() for r in rows)
        states = {r['state'] for r in store.rows('SELECT state FROM annotations')}
        assert 'human_reviewed' in states
        assert store.rows("SELECT rowid FROM images_fts WHERE images_fts MATCH ?", (f'"{rows[0]["title"].split()[0]}"',))
        provenance = json.loads(store.one('SELECT provenance_json FROM rights_records')['provenance_json'])
        assert 'starter_copy' in provenance
        store.remove_image(rows[0]['id'], 'not for me')
        assert transfer.import_starter(store, target, pack) == 0  # removed references stay removed


def test_tampered_starter_is_rejected(tmp_path):
    source, pack = tmp_path / 'source', tmp_path / 'starter'
    build_library(source)
    with jobs.open_store(source) as store:
        transfer.export_starter(store, source, pack)
    first = next(pack.glob('media/analysis/*/*.jpg'))
    first.write_bytes(first.read_bytes() + b'tampered')
    with jobs.open_store(tmp_path / 'target') as store, pytest.raises(ValueError, match='checksum'):
        transfer.import_starter(store, tmp_path / 'target', pack)
