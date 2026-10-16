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


def test_descriptive_cue_phrases_tag_a_technique_without_its_name():
    reading = coding.code_request('Backlit figures against a pale evening sky for a festival flyer', TAXONOMY)
    tags = {t['id']: t for t in reading['techniques']}
    assert 'silhouette' in tags and tags['silhouette']['exact'] is False and tags['silhouette']['why'] == '“backlit”'
    assert 'against' not in reading['subject_terms'] and 'flyer' not in reading['subject_terms']
    assert 'festival' in reading['subject_terms']
    calm = coding.code_request('A serene, misty morning by the lake', TAXONOMY)
    assert {'create-calm'} <= {g['id'] for g in calm['goals']}
    assert 'atmospheric-perspective' in {t['id'] for t in calm['techniques']}


def test_ordinary_isolation_brief_excludes_layout_words():
    techniques, goals, reading = tags('A calm poster about solitude, with one small person in a large empty landscape. '
                                      'Leave space for a title.')
    assert set(techniques) == {'negative-space', 'scale-contrast'} and goals == {'create-calm'}
    assert reading['subject_terms'] == ['solitude']


def test_negation_conflict_and_explicit_choices():
    techniques, goals, reading = tags('Use silhouette. No silhouette or deep shadow, but keep it calm.')
    assert techniques == {} and goals == {'create-calm'}
    assert not {'silhouette', 'shadow', 'no'} & set(reading['subject_terms'])
    techniques, _, _ = tags('Avoid symmetry.', technique_ids=['symmetry'])
    assert techniques == {'symmetry': True}
    techniques, _, _ = tags('A cup where it does not belong.')
    assert techniques == {'contextual-incongruity': False}
    techniques, _, _ = tags('The picture does not use silhouette.')
    assert techniques == {}


def test_explicit_subject_is_not_a_technique_instruction():
    techniques, _, reading = tags('Find a photograph', subject='symmetry exhibition')
    assert techniques == {} and reading['subject_terms'] == ['symmetry', 'exhibition']


def test_corrected_reading_can_remove_every_inference_and_validates_input():
    original = coding.code_request('silhouette and calm', TAXONOMY)
    correction = {'technique_ids': [], 'goal_ids': [], 'subject_terms': ['otters', 'river reeds']}
    assert coding.correct_reading(original, correction, TAXONOMY) == {
        'techniques': [], 'goals': [], 'subject_terms': ['otter', 'river', 'reed']}
    for invalid in [False, {}, {**correction, 'technique_ids': ['invented']},
                    {**correction, 'goal_ids': [['create-calm']]}, {**correction, 'subject_terms': [4]}]:
        with pytest.raises(ValueError):
            coding.correct_reading(original, invalid, TAXONOMY)


def test_subject_candidate_survives_a_mistaken_technique(library):
    home, oldest = library
    reading = coding.code_request('', TAXONOMY, technique_ids=['framing'], subject='evening')
    with jobs.open_store(home) as store:
        ranked = jobs.relevant_references(store, reading, limit=4)
    assert ranked[3]['image_id'] == oldest


def test_find_correction_preserves_choices_and_can_clear_inferred_subjects(home):
    with jobs.open_store(home) as store:
        job = jobs.create_job(store, 'find', {'goal': 'silhouette', 'technique_ids': ['framing'],
                              'goal_ids': ['create-calm'], 'backend': 'fake', 'reading_correction': {
                              'technique_ids': [], 'goal_ids': [], 'subject_terms': []}})
        spec = json.loads(store.one('SELECT spec_json FROM jobs WHERE id=?', (job,))['spec_json'])
        assert store.one('SELECT kind FROM jobs WHERE id=?', (job,))['kind'] == 'find'
        grow = jobs.create_job(store, 'grow', {'technique_ids': ['framing'], 'backend': 'fake'})
        assert store.one('SELECT kind FROM jobs WHERE id=?', (grow,))['kind'] == 'grow'
    assert [t['id'] for t in spec['reading']['techniques']] == ['framing']
    assert [g['id'] for g in spec['reading']['goals']] == ['create-calm']
    assert spec['reading']['subject_terms'] == [] and spec['targets'] == ['framing']


def test_fallback_search_keeps_subject_queries_with_many_providers():
    worker = jobs.Worker.__new__(jobs.Worker)
    worker.taxonomy = TAXONOMY
    worker.techniques = {t['id']: t for t in TAXONOMY['techniques']}
    worker.spec = {'reading': coding.code_request('silhouette, symmetry, negative space', TAXONOMY, subject='heron')}
    providers = ['commons', 'aic', 'met', 'cma', 'smithsonian', 'rijksmuseum', 'nga']
    queries = worker._fallback_queries('', providers)
    assert {q['provider'] for q in queries if q['query'] == 'heron'} == set(providers)
    assert len(queries) <= 12


def test_corrected_subject_alone_is_valid_and_long_find_preserves_correction(home):
    from atlas.ai import tasks

    correction = {'technique_ids': [], 'goal_ids': [], 'subject_terms': ['otters']}
    with jobs.open_store(home) as store:
        job = jobs.create_job(store, 'find', {'backend': 'fake', 'reading_correction': correction})
        spec = json.loads(store.one('SELECT spec_json FROM jobs WHERE id=?', (job,))['spec_json'])
    worker = jobs.Worker.__new__(jobs.Worker)
    worker.spec = {**spec, 'goal': 'Detailed brief. ' * 65}
    worker.techniques = {t['id']: t for t in TAXONOMY['techniques']}
    prompt = tasks.plan_prompt(worker._goal_text(), TAXONOMY['techniques'], ['aic'])
    assert 'otter' in prompt and worker.spec['goal'] in prompt


def test_directions_use_corrections_and_keep_original_brief(library):
    from atlas.ai import tasks

    home, _ = library
    text = 'Silhouette, no cropping. ' + 'Original detail. ' * 150
    correction = {'technique_ids': ['framing'], 'goal_ids': [], 'subject_terms': ['evening']}
    with jobs.open_store(home) as store:
        brief = store.save_brief('Test', text)
        job = jobs.create_job(store, 'directions', {'brief_id': brief, 'backend': 'fake', 'reading_correction': correction})
    worker = jobs.Worker(home, owner='corrected', backends={'fake': fake})
    worker.run_once(job)
    with jobs.open_store(home) as store:
        analysis = json.loads(store.one("SELECT result_json FROM analyses WHERE task='directions'")['result_json'])
        assert analysis['reading']['techniques'] == [{'id': 'framing', 'exact': True, 'why': 'corrected by you'}]
        assert store.one('SELECT text FROM briefs WHERE id=?', (brief,))['text'] == text.strip()
    prompt = tasks.directions_prompt({'title': 'Test', 'text': text, 'reading': analysis['reading']}, TAXONOMY['techniques'], [])
    assert text in prompt and 'corrected by you' in prompt
