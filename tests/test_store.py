"""Persistence, append-only history, human-correction preservation, search rows."""

import sqlite3

import pytest

from atlas import catalog, jobs
from atlas.store import Store


def add(store, n=1, **image):
    record = {'provider': 'aic', 'provider_item_id': str(n), 'title': f'Harbour {n}', 'creator': 'A. Painter',
              'source_url': f'https://www.artic.edu/artworks/{n}', 'file_sha256': f'{n:064x}',
              'analysis_sha256': f'{n + 1000:064x}', 'dhash': f'{n:016x}', 'width': 900, 'height': 600,
              'bytes': 1, 'mime': 'image/jpeg', 'analysis_path': f'analysis/x/{n}.jpg', **image}
    rights = {'license_code': 'CC0', 'license_version': '1.0', 'license_url': 'https://creativecommons.org/publicdomain/zero/1.0/',
              'label': 'CC0 — source checked', 'evidence_url': record['source_url'], 'evidence_json': '{}',
              'required_attribution': f'A. Painter, Harbour {n}. AIC. CC0.', 'restrictions': '', 'permitted_mode': 'local',
              'file_sha256': record['file_sha256'], 'retrieved_at': 'now', 'verified_at': 'now', 'policy_sha': 'x',
              'provenance_json': '{}'}
    metrics = {'aspect': 1.5, 'orientation': 'landscape', 'mean_luma': 100, 'contrast': 40, 'colorfulness': 20,
               'saturation': .3, 'palette_json': '[]', 'color_family': 'blue'}
    return store.add_image(record, rights, metrics)


def analysis(store, image_id, task='analyze', result='{"observations":[],"summary":"s","subjects":[]}', backend='fake'):
    return store.add_analysis({'image_id': image_id, 'task': task, 'backend': backend, 'model': 'practice',
                               'prompt_sha': 'p', 'taxonomy_sha': 't', 'input_sha': 'i', 'cache_key': 'c',
                               'result_json': result})


def proposal(technique, confidence=.8, role='primary'):
    return {'technique_id': technique, 'evidence': ['a visible thing'], 'effect': 'may draw the eye', 'confidence': confidence,
            'role': role}


@pytest.fixture
def store(home):
    with jobs.open_store(home) as opened:
        yield opened


def test_data_survives_reopen_and_migrations_are_recorded(home):
    with jobs.open_store(home) as store:
        image_id = add(store)
        store.create_collection('Harbours')
    with Store(jobs.db_path(home)) as reopened:
        assert reopened.one('SELECT title FROM images WHERE id=?', (image_id,))['title'] == 'Harbour 1'
        assert reopened.one('SELECT name FROM collections')['name'] == 'Harbours'
        assert reopened.connection.execute('PRAGMA user_version').fetchone()[0] >= 1


@pytest.mark.parametrize('table', ['rights_records', 'analyses', 'annotation_history', 'attempts', 'tombstones'])
def test_history_tables_are_append_only(store, table):
    image_id = add(store)
    store.apply_analysis(image_id, analysis(store, image_id), [proposal('negative-space')], 'model:fake/practice')
    store.record_attempt({'kind': 'ai', 'status': 'ok'})
    store.remove_image(image_id, 'test')
    for statement in (f'UPDATE {table} SET id=id', f'DELETE FROM {table}'):
        with pytest.raises(sqlite3.DatabaseError, match='append-only'):
            store.connection.execute(statement)


def test_reads_cannot_write(store):
    with pytest.raises(ValueError):
        store.rows('DELETE FROM images')
    with pytest.raises(sqlite3.DatabaseError):
        store.rows('SELECT * FROM images; DELETE FROM images')


def test_human_decisions_survive_later_model_analysis(store):
    image_id = add(store)
    first = analysis(store, image_id)
    store.apply_analysis(image_id, first, [proposal('negative-space'), proposal('scale-contrast', .7, 'supporting')], 'model:codex/m')
    store.human_annotation(image_id, 'negative-space', state='rejected', note='no empty area here')
    store.human_annotation(image_id, 'scale-contrast', state='human_reviewed', evidence=['tiny boat, huge cliff'], effect='feels vast')
    later = analysis(store, image_id)
    result = store.apply_analysis(image_id, later, [proposal('negative-space', .99), proposal('scale-contrast', .9)], 'model:claude/m')
    assert sorted(result['kept_human']) == ['negative-space', 'scale-contrast']
    rows = {r['technique_id']: r for r in store.rows('SELECT * FROM annotations WHERE image_id=?', (image_id,))}
    assert rows['negative-space']['state'] == 'rejected' and rows['negative-space']['changed_by'] == 'human'
    assert rows['scale-contrast']['evidence_json'] == '["tiny boat, huge cliff"]'
    notes = [h['note'] for h in store.rows('SELECT note FROM annotation_history WHERE image_id=?', (image_id,))]
    assert sum('not applied' in note for note in notes) == 2


def test_verification_promotes_only_unlocked_proposals(store):
    image_id = add(store)
    store.apply_analysis(image_id, analysis(store, image_id), [proposal('negative-space'), proposal('framing', .8, 'supporting'),
                                                               proposal('symmetry', .6, 'supporting')], 'model:codex/m')
    store.human_annotation(image_id, 'symmetry', state='rejected')
    store.apply_verdicts(image_id, analysis(store, image_id, 'verify', backend='claude'), [
        {'technique_id': 'negative-space', 'holds': True, 'reason': 'clear'},
        {'technique_id': 'framing', 'holds': False, 'reason': 'no frame'},
        {'technique_id': 'symmetry', 'holds': True, 'reason': 'centred'}], 'model:claude/m')
    states = {r['technique_id']: r['state'] for r in store.rows('SELECT * FROM annotations')}
    assert states == {'negative-space': 'model_reviewed', 'framing': 'proposed', 'symmetry': 'rejected'}


def test_low_confidence_proposals_are_not_saved(store):
    image_id = add(store)
    store.apply_analysis(image_id, analysis(store, image_id), [proposal('negative-space', .2)], 'model:codex/m')
    assert store.rows('SELECT * FROM annotations') == []
    assert store.one('SELECT status FROM images')['status'] == 'unanalyzed'


def test_removal_tombstones_and_clears_derivatives(store):
    image_id = add(store)
    collection = store.create_collection('Board')
    store.collect(collection, image_id)
    store.apply_analysis(image_id, analysis(store, image_id), [proposal('negative-space')], 'model:codex/m')
    removed = store.remove_image(image_id, 'not wanted')
    assert removed['analysis_path'] == 'analysis/x/1.jpg'
    assert store.rows('SELECT * FROM annotations') == [] and store.rows('SELECT * FROM collection_items') == []
    assert store.one('SELECT provider_item_id FROM tombstones')['provider_item_id'] == '1'
    assert store.rows("SELECT rowid FROM images_fts WHERE images_fts MATCH 'harbour'") == []
    with pytest.raises(ValueError):
        store.remove_image(image_id, 'again')


def test_search_index_follows_annotations(store):
    image_id = add(store, title='Lighthouse at dusk')
    store.apply_analysis(image_id, analysis(store, image_id), [proposal('negative-space')], 'model:codex/m')
    def hits(text):
        return [r['rowid'] for r in store.rows('SELECT rowid FROM images_fts WHERE images_fts MATCH ?', (text,))]
    assert hits('lighthouse') == [image_id]
    assert hits('"negative"') == [image_id] and hits('breathing') == [image_id]  # technique name and alias
    store.human_annotation(image_id, 'negative-space', state='rejected')
    assert hits('breathing') == []


def test_collections_validate_names_and_order(store):
    a, b = add(store, 1), add(store, 2)
    board = store.create_collection('Board')
    with pytest.raises(ValueError):
        store.create_collection('Board')
    with pytest.raises(ValueError):
        store.create_collection('   ')
    store.collect(board, a)
    store.collect(board, b)
    store.reorder_collection(board, [b, a])
    assert [r['image_id'] for r in store.rows('SELECT image_id FROM collection_items ORDER BY position')] == [b, a]


def test_catalog_sync_refuses_removing_a_used_technique(store, tmp_path):
    image_id = add(store)
    store.apply_analysis(image_id, analysis(store, image_id), [proposal('negative-space')], 'model:codex/m')
    taxonomy, policies, *_ = catalog.load()
    taxonomy['techniques'] = [t for t in taxonomy['techniques'] if t['id'] != 'negative-space']
    with pytest.raises(ValueError, match='still used'):
        store.replace_catalog(taxonomy, policies, 'a', 'b')
    assert store.one("SELECT id FROM techniques WHERE id='negative-space'")


def test_a_model_cannot_check_its_own_proposal(store):
    image_id = add(store)
    store.apply_analysis(image_id, analysis(store, image_id, backend='codex'), [proposal('negative-space')], 'model:codex/m')
    store.apply_verdicts(image_id, analysis(store, image_id, 'verify', backend='codex'),
                         [{'technique_id': 'negative-space', 'holds': True, 'reason': 'same model'}], 'model:codex/m')
    assert store.one('SELECT state FROM annotations')['state'] == 'proposed'


def test_imported_records_cannot_smuggle_sql_through_field_names(store):
    with pytest.raises(ValueError, match='unknown field'):
        store._insert('settings', {'key': 'a', "value) SELECT value FROM settings --": 'x'})
