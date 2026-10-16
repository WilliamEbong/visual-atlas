"""Frozen v0.3 vs v0.4 brief evaluation. Run: uv run python scripts/eval_v04.py dev|heldout.

Builder/model judgments, not independent expert ground truth. Only baseline starter references are imported,
into a temporary home outside the repository. No AI or provider calls.
"""

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import types
from pathlib import Path

from atlas import catalog, coding, jobs, transfer

ROOT = Path(__file__).resolve().parent.parent
EVAL = ROOT / 'docs/evaluation/v0.4'
BASE = 'e43e0932ece8be850926e013fc91ce3f84920c32'
FROZEN = {'dev': '52b57a35f05797e3890ab7c7e824d92f5deff0bd05b60cf388e8ed560469e951',
          'heldout': 'f38360b4e1b7d5e3fca1b15af24710f4e929fe75b422eefb705c804a4c9e0a3e'}


def original(path):
    return subprocess.run(['git', 'show', f'{BASE}:{path}'], cwd=ROOT, capture_output=True,
                          encoding='utf-8', check=True).stdout


def module_at_baseline(name):
    module = types.ModuleType(f'baseline_{name}')
    sys.modules[module.__name__] = module
    exec(compile(original(f'atlas/{name}.py'), f'baseline_{name}.py', 'exec'), module.__dict__)
    return module


def metrics(rows, kinds=('techniques', 'goals')):
    tp = fp = fn = 0
    for row in rows:
        expected = {tag for kind in kinds for tag in row['expected'][kind]}
        found = {tag['id'] for kind in kinds for tag in row['reading'][kind]}
        tp += len(expected & found)
        fp += len(found - expected)
        fn += len(expected - found)
    precision, recall = tp / (tp + fp) if tp + fp else 0, tp / (tp + fn) if tp + fn else 0
    return {'tp': tp, 'fp': fp, 'fn': fn, 'precision': round(precision, 4), 'recall': round(recall, 4),
            'f1': round(2 * precision * recall / (precision + recall), 4) if precision + recall else 0}


def evaluate(split):
    source = (EVAL / f'brief-{split}.json').read_bytes()
    if hashlib.sha256(source).hexdigest() != FROZEN[split]:
        raise SystemExit('Frozen judgments changed; do not evaluate altered held-out cases.')
    cases = json.loads(source)['cases']
    old_coding, old_jobs = module_at_baseline('coding'), module_at_baseline('jobs')
    old_taxonomy = json.loads(original('atlas/data/taxonomy.json'))
    result = {'baseline': BASE, 'split': split, 'cases': len(cases),
              'judgments': 'Builder/model judgments; not independent expert ground truth.', 'arms': {}}
    with tempfile.TemporaryDirectory(prefix='atlas-eval-v04-') as directory:
        scratch = Path(directory)
        starter = scratch / 'starter'
        starter.mkdir()
        (starter / 'library.json').write_text(original('starter/library.json'), encoding='utf-8')
        shutil.copytree(ROOT / 'starter/media', starter / 'media')
        with jobs.open_store(scratch / 'home') as store:
            transfer.import_starter(store, scratch / 'home', starter)
            for name, coder, ranker, taxonomy in [('v0.3', old_coding, old_jobs, old_taxonomy),
                                                  ('v0.4', coding, jobs, catalog.load()[0])]:
                rows = []
                covered = {20: 0, 40: 0}
                expected_techniques = 0
                subject_hits = subject_total = subject_leaks = subject_exclusions = 0
                for case in cases:
                    reading = coder.code_request(case['text'], taxonomy, case.get('technique_ids', []),
                                                 case.get('goal_ids', []))
                    ranked = ranker.relevant_references(store, reading, limit=40, budget=10**9)
                    for k in covered:
                        carried = {t['id'] for reference in ranked[:k] for t in reference['techniques']}
                        covered[k] += len(carried & set(case['techniques']))
                    expected_techniques += len(case['techniques'])
                    required = set(old_coding.words(' '.join(case.get('subjects', []))))
                    forbidden = set(old_coding.words(' '.join(case.get('not_subjects', []))))
                    subject_hits += len(required & set(reading['subject_terms']))
                    subject_total += len(required)
                    subject_leaks += len(forbidden & set(reading['subject_terms']))
                    subject_exclusions += len(forbidden)
                    rows.append({'id': case['id'], 'expected': {k: case[k] for k in ('techniques', 'goals')},
                                 'reading': reading, 'candidate_ids': [r['image_id'] for r in ranked]})
                result['arms'][name] = {'combined': metrics(rows), 'techniques': metrics(rows, ('techniques',)),
                                        'goals': metrics(rows, ('goals',)), 'subjects': {'required_found': subject_hits,
                                        'required_total': subject_total, 'forbidden_found': subject_leaks,
                                        'forbidden_total': subject_exclusions},
                                        'retrieval': {f'technique_coverage@{k}': {'covered': v,
                                        'expected': expected_techniques} for k, v in covered.items()}, 'rows': rows}
    (EVAL / f'brief-results-{split}.json').write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n',
                                                   encoding='utf-8')
    print(json.dumps({**result, 'arms': {name: {k: v for k, v in arm.items() if k != 'rows'}
                                       for name, arm in result['arms'].items()}}, indent=2))


if __name__ == '__main__':
    split = sys.argv[1] if len(sys.argv) > 1 else 'dev'
    if split not in ('dev', 'heldout'):
        raise SystemExit('Use dev or heldout')
    evaluate(split)
