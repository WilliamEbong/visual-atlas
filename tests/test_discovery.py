"""Find/Grow report whether they found what was asked, and automatic rejections stay distinct from a person's."""

import json

from helpers import aic_fetcher

from atlas import jobs
from atlas.ai import fake


class Blank:
    """An analyser that sees no clear technique in any picture."""
    NAME = 'codex'

    @staticmethod
    def run(prompt, schema, images, **kwargs):
        if 'observations' not in schema['properties']:
            return fake.run(prompt, schema, images, **kwargs)
        return {'result': {'image_usable': True, 'unusable_reason': None,
                           'observations': [{'id': 'o1', 'text': 'A plain field.', 'region': 'whole'}],
                           'techniques': [], 'ambiguities': [], 'subjects': [], 'summary': 'Plain.',
                           'creator_intent': None}, 'input_tokens': 1, 'output_tokens': 1, 'cli_version': 't'}


def run_find(home, backend=fake, **spec):
    with jobs.open_store(home) as store:
        job_id = jobs.create_job(store, 'find', {'goal': 'harbour', 'providers': ['aic'], 'backend': 'codex',
                                                 'target_new_images': 2, **spec})
    jobs.Worker(home, owner=job_id, fetcher=aic_fetcher(), backends={'codex': backend}).run_once(job_id)
    with jobs.open_store(home) as store:
        return (store.one('SELECT * FROM jobs WHERE id=?', (job_id,)),
                store.rows("SELECT * FROM job_items WHERE job_id=? AND kind='candidate'", (job_id,)))


def test_each_added_image_records_whether_it_shows_the_requested_technique(home):
    job, items = run_find(home, technique_ids=['silhouette'], target_new_images=1)
    spec = json.loads(job['spec_json'])
    assert spec['targets'] == ['silhouette']
    added = [i for i in items if i['state'] == 'added']
    assert added
    with jobs.open_store(home) as store:
        for item in added:
            match = json.loads(item['payload_json'])['match']
            carried = {r['technique_id'] for r in store.rows(
                "SELECT technique_id FROM annotations WHERE image_id=? AND state!='rejected'", (item['image_id'],))}
            assert match['techniques'] == sorted(carried & {'silhouette'})  # read from the analysis, never forced
    matching = sum(bool(json.loads(i['payload_json'])['match']['techniques']) for i in added)
    assert f'{matching} show' in job['message'] and 'show other techniques' in job['message']
    if not matching:  # nothing showed it: the job says so instead of claiming success
        assert 'Ready.' not in job['message']


def test_exact_technique_names_in_the_request_become_targets(home):
    with jobs.open_store(home) as store:
        spec = json.loads(store.one('SELECT spec_json FROM jobs WHERE id=?', (jobs.create_job(
            store, 'find', {'goal': 'a lighthouse with lots of negative space', 'backend': 'fake'}),))['spec_json'])
    assert spec['targets'] == ['negative-space'] and 'lighthouse' in spec['reading']['subject_terms']


def test_an_automatic_rejection_is_reconsidered_only_by_a_newer_analysis_version(home):
    job, items = run_find(home, Blank, target_new_images=1)
    rejected = {i['provider_item_id'] for i in items if i['state'] == 'no_technique'}
    assert rejected
    with jobs.open_store(home) as store:
        kinds = {r['provider_item_id']: (r['source'], r['rule_version']) for r in store.rows('SELECT * FROM tombstone_kinds')}
    assert {kinds[i][0] for i in rejected} == {'auto'} and all(kinds[i][1] for i in rejected)
    _, again = run_find(home, Blank, target_new_images=1)
    assert not rejected & {i['provider_item_id'] for i in again}  # same version: not looked at again
    _, newer = run_find(home, models={'analyze': 'a-newer-model'}, target_new_images=5)
    revived = rejected & {i['provider_item_id'] for i in newer if i['state'] == 'added'}
    assert revived  # a different analysis version looks again, and can add it
    with jobs.open_store(home) as store:
        row = store.one('SELECT removed_at, status FROM images WHERE provider_item_id=?', (next(iter(revived)),))
    assert row == {'removed_at': None, 'status': 'ready'}


def test_a_persons_removal_is_never_reconsidered(home):
    run_find(home, target_new_images=1)
    with jobs.open_store(home) as store:
        image = store.one('SELECT * FROM images WHERE removed_at IS NULL')
        store.remove_image(image['id'], 'not for me')
    _, later = run_find(home, models={'analyze': 'a-newer-model'}, target_new_images=5)
    assert image['provider_item_id'] not in {i['provider_item_id'] for i in later}
