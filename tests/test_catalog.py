"""The editable knowledge files: validation, cross-references, sync and the relationship graph."""

import copy
import json
import shutil

import pytest

from atlas import catalog, jobs
from atlas.home import DATA


def test_shipped_files_are_valid_and_complete():
    taxonomy, policies, *_ = catalog.load()
    assert len(taxonomy['techniques']) >= 24
    for technique in taxonomy['techniques']:
        assert technique['sources'] or technique['working_definition']
        assert technique['confusions'] and technique['related'] and technique['counterexample']
    enabled = {p['id'] for p in policies['providers'] if p['status'] == 'enabled'}
    assert enabled == {'aic', 'met', 'cma', 'smithsonian', 'commons'}
    assert {'unsplash', 'pexels', 'pixabay'} <= {p['id'] for p in policies['providers'] if p['status'] == 'disabled'}


def test_dangling_references_are_reported():
    taxonomy, policies, *_ = catalog.load()
    broken = copy.deepcopy(taxonomy)
    broken['techniques'][0]['goals'].append('no-such-goal')
    broken['techniques'][1]['related'].append({'technique': 'ghost', 'relation': 'related'})
    broken['techniques'][2]['sources'] = []
    broken['techniques'][2]['working_definition'] = False
    problems = catalog.check(broken, policies)
    assert any('unknown goal "no-such-goal"' in p for p in problems)
    assert any('unknown technique "ghost"' in p for p in problems)
    assert any('needs sources or working_definition' in p for p in problems)


def test_policy_rules_are_checked():
    taxonomy, policies, *_ = catalog.load()
    broken = copy.deepcopy(policies)
    broken['providers'].append({'id': 'mystery', 'status': 'enabled', 'evidence_urls': ['https://x'], 'checked_on': 'x'})
    broken['providers'].append({'id': 'vague', 'status': 'disabled', 'evidence_urls': ['https://x'], 'checked_on': 'x'})
    problems = catalog.check(taxonomy, broken)
    assert any('mystery' in p and 'enabled providers need' in p for p in problems)
    assert any('vague' in p and 'need a reason' in p for p in problems)


def test_load_reports_schema_errors(tmp_path):
    shutil.copy(DATA / 'source_policies.json', tmp_path)
    data = json.loads((DATA / 'taxonomy.json').read_text(encoding='utf-8'))
    data['techniques'][0]['unexpected'] = 1
    (tmp_path / 'taxonomy.json').write_text(json.dumps(data), encoding='utf-8')
    with pytest.raises(ValueError, match='taxonomy.json is invalid'):
        catalog.load(tmp_path)


def test_sync_only_when_files_change_and_links_match(home):
    with jobs.open_store(home) as store:
        assert catalog.sync(store) is False  # open_store already synced
        taxonomy, *_ = catalog.load()
        links = store.rows("SELECT technique_id, kind, target_id FROM technique_links")
        expected = sum(len(t['goals']) + len(t['operations']) + len(t['domains']) + len(t['related']) + len(t['confusions'])
                       for t in taxonomy['techniques'])
        assert len(links) == expected
        known = {r['id'] for r in store.rows('SELECT id FROM techniques')}
        assert all(link['target_id'] in known for link in links if link['kind'] in ('related', 'confused_with'))
        assert catalog.sync(store, force=True) is True


def test_coverage_lists_every_technique_fewest_first(home):
    with jobs.open_store(home) as store:
        rows = catalog.coverage(store)
        assert len(rows) == len(store.rows('SELECT id FROM techniques'))
        assert [r['examples'] for r in rows] == sorted(r['examples'] for r in rows)
