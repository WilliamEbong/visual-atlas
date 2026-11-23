"""Round-2 brief reading evaluation (overnight 23 Nov 2026). Run: uv run python scripts/eval_r2.py dev|test [--rev REV]

Cases: docs/evaluation/r2/briefs-*.json, written by Opus subagents acting as designers and as AI agents, who read
only the taxonomy and the v0.4 labelling policy. Each case goes to dev or test by a hash of its id, fixed before any
tuning. The builder tunes on dev only; test prints aggregates only, so its cases are not read while tuning.
--rev evaluates atlas/coding.py and the taxonomy as they were at a Git revision (the before arm).
Model-authored judgments, not expert ground truth. No AI or provider calls."""

import hashlib
import json
import subprocess
import sys
import types
from pathlib import Path

from atlas import catalog, coding

ROOT = Path(__file__).resolve().parent.parent
EVAL = ROOT / 'docs/evaluation/r2'


def split_of(case_id: str) -> str:
    return 'test' if int(hashlib.sha256(case_id.encode()).hexdigest(), 16) % 2 else 'dev'


def at(rev: str, path: str) -> str:
    return subprocess.check_output(['git', 'show', f'{rev}:{path}'], cwd=ROOT).decode('utf-8')


def coder(rev: str | None):
    if not rev:
        return coding, catalog.load()[0]
    module = types.ModuleType(f'coding_{rev}')
    exec(compile(at(rev, 'atlas/coding.py'), 'coding.py', 'exec'), module.__dict__)
    return module, json.loads(at(rev, 'atlas/data/taxonomy.json'))


def score(rows, kind):
    tp = sum(len(set(r['got'][kind]) & set(r['want'][kind])) for r in rows)
    fp = sum(len(set(r['got'][kind]) - set(r['want'][kind])) for r in rows)
    fn = sum(len(set(r['want'][kind]) - set(r['got'][kind])) for r in rows)
    p, r = (tp / (tp + fp) if tp + fp else 0), (tp / (tp + fn) if tp + fn else 0)
    return {'tp': tp, 'fp': fp, 'fn': fn, 'precision': round(p, 3), 'recall': round(r, 3),
            'f1': round(2 * p * r / (p + r), 3) if p + r else 0}


def evaluate(split: str, rev: str | None = None) -> dict:
    module, taxonomy = coder(rev)
    rows = []
    for path in sorted(EVAL.glob('briefs-*.json')):
        for case in json.loads(path.read_text(encoding='utf-8'))['cases']:
            if split_of(case['id']) != split:
                continue
            reading = module.code_request(case['text'], taxonomy)
            rows.append({'id': case['id'], 'text': case['text'],
                         'want': {'techniques': case['techniques'], 'goals': case['goals']},
                         'got': {'techniques': [t['id'] for t in reading['techniques']],
                                 'goals': [g['id'] for g in reading['goals']]}})
    understood = sum(1 for r in rows if (r['want']['techniques'] or r['want']['goals']) and
                     (set(r['got']['techniques']) & set(r['want']['techniques']) or
                      set(r['got']['goals']) & set(r['want']['goals'])))
    answerable = sum(1 for r in rows if r['want']['techniques'] or r['want']['goals'])
    return {'split': split, 'rev': rev or 'working tree', 'cases': len(rows),
            'briefs_with_at_least_one_right_code': f'{understood}/{answerable}',
            'techniques': score(rows, 'techniques'), 'goals': score(rows, 'goals'),
            'combined': score([{'want': {'x': r['want']['techniques'] + r['want']['goals']},
                                'got': {'x': r['got']['techniques'] + r['got']['goals']}} for r in rows], 'x'),
            'rows': rows}


if __name__ == '__main__':
    split = sys.argv[1] if len(sys.argv) > 1 else 'dev'
    rev = sys.argv[sys.argv.index('--rev') + 1] if '--rev' in sys.argv else None
    if split not in ('dev', 'test'):
        raise SystemExit('Use dev or test')
    result = evaluate(split, rev)
    if split == 'test':  # aggregates only: the builder does not read test cases while tuning
        result.pop('rows')
    print(json.dumps(result, indent=1, ensure_ascii=False))
