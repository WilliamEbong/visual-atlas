"""Maintainers: run Suggest directions once for real on a fresh starter library and save the answer as
atlas/data/example_brief.json, which Projects shows before the first brief is written.

    uv run python scripts/make_example_brief.py --backend codex

One AI call through the chosen CLI. Uses a throwaway library in the temp folder, never yours.
"""

import argparse
import datetime
import json
import tempfile
from pathlib import Path

from atlas import jobs, transfer
from atlas.home import REPO

TITLE = 'Winter concert poster for a community choir'
TEXT = ('A poster for a community choir\'s winter concert in a village church. Warm and welcoming, so neighbours who '
        'have never been feel invited. A3 portrait for noticeboards and shop windows; the title and date must read '
        'from across the street.')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--backend', default='codex', choices=['codex', 'claude'])
    backend = parser.parse_args().backend
    home = Path(tempfile.mkdtemp(prefix='va-example-'))
    with jobs.open_store(home) as store:
        transfer.import_starter(store, home, REPO / 'starter')
        brief_id = store.save_brief(TITLE, TEXT)
        job_id = jobs.create_job(store, 'directions', {'brief_id': brief_id, 'backend': backend})
    jobs.Worker(home).run_once(job_id)
    with jobs.open_store(home) as store:
        refs = {r['id']: f"{r['provider']}:{r['provider_item_id']}" for r in store.rows('SELECT id, provider, provider_item_id FROM images')}
        rows = store.rows('SELECT d.result_json, a.backend, a.model, a.model_version FROM directions d JOIN analyses a '
                          'ON a.id=d.analysis_id WHERE d.brief_id=? ORDER BY d.position', (brief_id,))
    if not rows:
        raise SystemExit(f'No directions came back; see the job log in {home}.')
    directions = []
    for row in rows:
        data = json.loads(row['result_json'])
        directions.append({k: data[k] for k in ('title', 'idea', 'rationale', 'execution', 'tradeoffs')}
                          | {'techniques': data['technique_ids'], 'images': [refs[i] for i in data['image_ids'] if i in refs]})
    out = {'title': TITLE, 'text': TEXT, 'backend': rows[0]['backend'], 'model': rows[0]['model_version'] or rows[0]['model'],
           'made': datetime.date.today().isoformat(), 'directions': directions}
    (REPO / 'atlas' / 'data' / 'example_brief.json').write_text(json.dumps(out, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(f'Saved {len(directions)} directions.')


if __name__ == '__main__':
    main()
