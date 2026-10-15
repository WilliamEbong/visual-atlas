"""v0.3 evaluation (deterministic, no AI). Criteria fixed beforehand in docs/evaluation/v0.3/*-GATE.md.

  uv run python scripts/eval_v03.py coding dev     # v1.1 coder vs v0.3 coder on the v1.1 briefs (+ retrieval recall)
  uv run python scripts/eval_v03.py coding final   # once, after the decision: the fresh 20-brief holdout
  uv run python scripts/eval_v03.py metadata       # the documentation-photo filter on the labelled case set

The v1.1 coder is loaded from the v0.2.0 tag (git show), so arm 1 is exactly what shipped."""

import hashlib
import json
import subprocess
import sys
import tempfile
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import eval_v11  # noqa: E402  (shared helpers: rate, starter_library)

from atlas import catalog, coding, jobs  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
EVAL = ROOT / 'docs' / 'evaluation' / 'v0.3'
FINAL = EVAL / 'briefs-final.json'
FINAL_SHA = '543457fb8e219103'


def v11_coder():
    source = subprocess.run(['git', 'show', 'v0.2.0:atlas/coding.py'], cwd=ROOT, capture_output=True, text=True,
                            encoding='utf-8', check=True).stdout
    module = types.ModuleType('coding_v11')
    exec(compile(source, 'coding_v11.py', 'exec'), module.__dict__)  # the shipped v1.1 code, run as-is
    return module


def scores(rows: list[dict]) -> dict:
    coded = sum(len(r['coded']) for r in rows)
    expected = sum(len(r['expected']) for r in rows)
    hits = sum(len(set(r['coded']) & set(r['expected'])) for r in rows)
    precision = hits / coded if coded else 0.0
    recall = hits / expected if expected else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {'precision': eval_v11.rate(hits, coded), 'recall': eval_v11.rate(hits, expected), 'micro_f1': round(f1, 2),
            'coded': coded, 'expected': expected, 'hits': hits}


def code_rows(module, briefs: list[dict], taxonomy: dict) -> list[dict]:
    rows = []
    for brief in briefs:
        reading = module.code_request(brief['text'], taxonomy)
        coded = sorted(t['id'] for t in reading['techniques']) + sorted(g['id'] for g in reading['goals'])
        rows.append({'id': brief['id'], 'coded': coded, 'expected': brief['techniques'] + brief['goals'],
                     'why': {t['id']: t['why'] for t in reading['techniques'] + reading['goals']}, 'reading': reading})
    return rows


def recall_at(briefs: list[dict], readings: dict, k: int = 20) -> dict:
    with tempfile.TemporaryDirectory() as directory:
        store, ids = eval_v11.starter_library(Path(directory))
        with store:
            found = total = 0
            for brief in briefs:
                ranked = [r['image_id'] for r in jobs.relevant_references(store, readings[brief['id']], limit=200, budget=10**9)]
                relevant = {ids[key] for key in brief['relevant']}
                found += len(relevant & set(ranked[:k]))
                total += len(relevant)
    return eval_v11.rate(found, total)


def coding_eval(split: str):
    taxonomy = catalog.load()[0]
    old = v11_coder()
    if split == 'dev':
        briefs = eval_v11.load_briefs()
    else:
        digest = hashlib.sha256(FINAL.read_bytes()).hexdigest()[:16]
        if digest != FINAL_SHA:
            raise SystemExit(f'briefs-final.json changed since it was frozen ({digest} != {FINAL_SHA})')
        briefs = json.loads(FINAL.read_text(encoding='utf-8'))['briefs']
    result = {'split': split, 'briefs': len(briefs)}
    for arm, module in (('v1.1', old), ('v0.3', coding)):
        rows = code_rows(module, briefs, taxonomy)
        result[arm] = scores(rows)
        if split == 'dev':
            result[arm]['retrieval_recall@20'] = recall_at(briefs, {r['id']: r['reading'] for r in rows})
        result[f'{arm}_rows'] = [{k: r[k] for k in ('id', 'coded', 'expected', 'why')} for r in rows]
    if split == 'dev':
        a, b = result['v1.1'], result['v0.3']
        result['decision'] = {
            'f1_gain': round(b['micro_f1'] - a['micro_f1'], 2),
            'f1_gain_at_least_0.10': b['micro_f1'] - a['micro_f1'] >= 0.10,
            'precision_at_least_0.60': b['precision']['rate'] >= 0.60,
            'retrieval_not_lower': b['retrieval_recall@20']['k'] >= a['retrieval_recall@20']['k'],
        }
        result['decision']['adopt'] = all(v for k, v in result['decision'].items() if k != 'f1_gain')
    out = EVAL / f'coding-{split}.json'
    out.write_text(json.dumps(result, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if not k.endswith('_rows')}, indent=1, ensure_ascii=False))


if __name__ == '__main__':
    command = sys.argv[1:] or ['coding', 'dev']
    if command[0] == 'coding':
        coding_eval(command[1] if len(command) > 1 else 'dev')
    else:
        raise SystemExit(__doc__)
