"""The v0.4 curated additions retain inspectable evidence and honest review provenance."""

import hashlib
import json
from pathlib import Path

from atlas import catalog, jobs, transfer
from atlas.ai import tasks

ROOT = Path(__file__).resolve().parents[1]


def test_curated_starter_additions_are_proposals_with_real_media_and_rights(tmp_path):
    pack = ROOT / 'starter'
    data = json.loads((pack / 'library.json').read_text(encoding='utf-8'))
    decisions = json.loads((ROOT / 'docs/evaluation/v0.4/curation-additions.json').read_text(encoding='utf-8'))
    selected = {(a['provider'], a['item_id']) for a in decisions}
    additions = [r for r in data['references'] if (r['image']['provider'], r['image']['provider_item_id']) in selected]
    assert len(additions) == len(selected) == 8
    known = {t['id'] for t in catalog.load()[0]['techniques']}
    for row in additions:
        image, rights = row['image'], row['rights']
        assert hashlib.sha256((pack / 'media' / image['analysis_path']).read_bytes()).hexdigest() == image['analysis_sha256']
        assert rights['evidence_url'] == image['source_url']
        assert rights['required_attribution'] and rights['verified_at']
        assert json.loads(rights['provenance_json'])['redistribution']['basis'] == rights['license_url']
        assert all(a['state'] == 'proposed' and not a['human_locked'] for a in row['annotations'])
        assert {a['backend'] for a in row['analyses']} == {'codex-interactive'}
        assert all(a['cli_version'] is None for a in row['analyses'])
        for analysis in row['analyses']:
            tasks.validate_analysis(json.loads(analysis['result_json']), known, {})
    with jobs.open_store(tmp_path) as store:
        assert transfer.import_starter(store, tmp_path, pack) == len(data['references'])
        assert transfer.import_starter(store, tmp_path, pack) == 0
        credits = transfer.credits(store)
        for row in additions:
            assert row['rights']['required_attribution'] in credits


def test_curation_search_refuses_application_data_in_repo(monkeypatch):
    import pytest

    from scripts import curate_v04

    monkeypatch.setattr('sys.argv', ['curate_v04', str(ROOT / 'unsafe-library'), 'example'])
    with pytest.raises(SystemExit, match='2'):
        curate_v04.main()
