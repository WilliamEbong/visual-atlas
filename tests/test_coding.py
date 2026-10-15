"""Request coding (no AI) and the relevance-ranked, grounded references it feeds to project directions."""

import json
import os

import pytest

from atlas import catalog, coding, jobs
from atlas.ai import fake
from atlas.store import now

TAXONOMY = catalog.load()[0]


def tags(text, **kwargs):
    reading = coding.code_request(text, TAXONOMY, **kwargs)
    return {t['id']: t['exact'] for t in reading['techniques']}, {g['id'] for g in reading['goals']}, reading


def test_names_and_aliases_are_exact_tags_and_carry_their_reason():
    techniques, _, reading = tags('Silhouettes of birds at sunset, strong chiaroscuro, and a low angle')
    assert techniques == {'silhouette': True, 'value-contrast': True, 'vantage-point': True}
    assert {t['why'] for t in reading['techniques']} >= {'“silhouette”', '“chiaroscuro”'}
    assert 'bird' in reading['subject_terms'] and 'sunset' in reading['subject_terms']


def test_form_choices_are_exact_and_vague_requests_tag_nothing():
    techniques, goals, _ = tags('something nice', technique_ids=['framing'], goal_ids=['create-calm'])
    assert techniques == {'framing': True} and goals == {'create-calm'}
    techniques, goals, _ = tags('make it pop')
    assert techniques == {} and goals == set()  # honest: nothing in the codebook matches


def test_distinctive_single_words_give_weaker_tags_and_goals():
    techniques, goals, _ = tags('a calm poster about the rhythm of a vast desert')
    assert techniques.get('rhythm-pattern') is False and {'create-calm', 'show-scale'} <= goals


def add(store, number, technique, state='proposed'):
    image_id = store.add_image(
        {'provider': 'commons', 'provider_item_id': str(number), 'title': f'Plate {number}', 'source_url': 'https://x',
         'file_sha256': f'{number:064x}', 'analysis_sha256': f'{number:064x}', 'dhash': f'{number:016x}', 'width': 9,
         'height': 9, 'bytes': 9, 'mime': 'image/jpeg', 'description': 'evening sky' if number == 1 else 'a room'},
        {'license_code': 'CC0', 'license_version': '1.0', 'license_url': 'https://x', 'label': 'CC0', 'evidence_url':
         'https://x', 'evidence_json': '{}', 'required_attribution': '', 'restrictions': '', 'permitted_mode': 'x',
         'file_sha256': f'{number:064x}', 'retrieved_at': now(), 'verified_at': now(), 'policy_sha': 'x',
         'provenance_json': '{}'},
        {'aspect': 1, 'orientation': 'square', 'mean_luma': 1, 'contrast': 1, 'colorfulness': 1, 'saturation': 1,
         'palette_json': '[]', 'color_family': 'blue'})
    analysis = store.add_analysis({'image_id': image_id, 'task': 'analyze', 'backend': 'codex', 'model': 'm',
                                   'prompt_sha': 'p', 'taxonomy_sha': 't', 'input_sha': 'i',
                                   'cache_key': os.urandom(8).hex(), 'result_json': json.dumps({'summary': 'S'})})
    store.apply_analysis(image_id, analysis, [{'technique_id': technique, 'evidence': ['seen'], 'effect': 'may',
                                               'confidence': .9, 'role': 'primary'}], 'model:codex/m')
    if state == 'human_reviewed':
        store.human_annotation(image_id, technique, state='human_reviewed')
    return image_id


@pytest.fixture
def library(home):
    with jobs.open_store(home) as store:
        oldest = add(store, 1, 'silhouette', 'human_reviewed')
        for number in range(2, 61):
            add(store, number, ['framing', 'symmetry', 'rhythm-pattern'][number % 3])
    return home, oldest


def test_an_older_relevant_reference_beats_newer_unrelated_ones(library):
    home, oldest = library
    reading = coding.code_request('Silhouettes against the evening sky', TAXONOMY)
    with jobs.open_store(home) as store:
        ranked = jobs.relevant_references(store, reading, limit=10)
        newest = [r['id'] for r in store.rows("SELECT id FROM images ORDER BY id DESC LIMIT 10")]
    assert ranked[0]['image_id'] == oldest and oldest not in newest  # the old recency rule would have missed it
    assert ranked[0]['techniques'] == [{'id': 'silhouette', 'state': 'human_reviewed'}]


def test_references_are_whole_records_within_the_budget(library):
    home, _ = library
    with jobs.open_store(home) as store:
        records = jobs.relevant_references(store, coding.code_request('frames', TAXONOMY), budget=3000)
    assert 0 < len(records) < 60 and len(json.dumps(records, ensure_ascii=False)) <= 3000
    assert all({'image_id', 'title', 'summary', 'techniques'} <= set(r) for r in records)


class Empty:
    NAME = 'codex'

    @staticmethod
    def run(prompt, schema, images, **kwargs):
        return {'result': {'directions': [], 'insufficient_evidence': 'No reference shows a night sky.'},
                'input_tokens': 1, 'output_tokens': 1, 'cli_version': 't'}


def directions(home, backend, brief_id):
    with jobs.open_store(home) as store:
        job_id = jobs.create_job(store, 'directions', {'brief_id': brief_id, 'backend': 'codex'})
    jobs.Worker(home, owner='d', backends={'codex': backend}).run_once(job_id)
    with jobs.open_store(home) as store:
        return (store.one('SELECT state, message FROM jobs WHERE id=?', (job_id,)),
                store.rows('SELECT * FROM directions WHERE brief_id=?', (brief_id,)))


def test_grounded_directions_are_saved_and_insufficient_evidence_keeps_earlier_ones(library):
    home, _ = library
    with jobs.open_store(home) as store:
        brief = store.save_brief('Night sky poster', 'Silhouettes against an evening sky, calm and wondrous.')
    job, saved = directions(home, fake, brief)
    assert job['state'] == 'done' and saved
    with jobs.open_store(home) as store:
        for row in saved:
            result = json.loads(row['result_json'])
            for image_id in result['image_ids']:  # every cited image carries a cited technique
                carried = {r['technique_id'] for r in store.rows(
                    "SELECT technique_id FROM annotations WHERE image_id=? AND state!='rejected'", (image_id,))}
                assert carried & set(result['technique_ids'])
    job, kept = directions(home, Empty, brief)
    assert job['state'] == 'done' and 'Not enough matching evidence' in job['message'] and 'night sky' in job['message']
    assert [r['id'] for r in kept] == [r['id'] for r in saved]  # an empty answer never wipes earlier suggestions
