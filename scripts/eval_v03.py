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


# ---- metadata filter: case collection (labels come from thumbnails only; see METADATA-GATE.md) -------------
QUERIES = {'smithsonian': ['insect specimen', 'herbarium', 'exhibit hall', 'letter', 'landscape'],
           'commons': ['museum exhibit', 'handwritten letter', 'herbarium sheet', 'sunset'],
           'met': ['fragment', 'letter', 'landscape'], 'aic': ['photograph', 'letter', 'portrait'],
           'cma': ['textile fragment', 'landscape'], 'rijksmuseum': ['letter', 'ship'], 'nga': ['page', 'harbor']}
CASES = EVAL / 'metadata-cases.json'


def collect(scratch: Path):
    """Live searches; keeps rights-eligible candidates and a small thumbnail of each. Prints no catalogue text."""
    from io import BytesIO

    from PIL import Image

    from atlas import providers, rights
    from atlas.fetch import Fetcher, FetchError
    policies = catalog.load()[1]
    fetcher = Fetcher(policies)
    thumbs = scratch / 'thumbs'
    thumbs.mkdir(parents=True, exist_ok=True)
    cases, seen = [], set()
    for provider, queries in QUERIES.items():
        for query in queries:
            try:
                found = providers.search(fetcher, provider, query, 0, 6, home=scratch / 'home')
            except FetchError as error:
                print(f'{provider} "{query}": {error.code}')
                continue
            kept = 0
            for candidate in found:
                key = (candidate['provider'], candidate['provider_item_id'])
                if key in seen or not rights.check(candidate, catalog.policy(policies, provider))['eligible']:
                    continue
                try:
                    data = fetcher.get_image(provider, candidate['image_url'], headers=candidate.get('image_headers'))
                except FetchError:
                    continue
                image = Image.open(BytesIO(data)).convert('RGB')
                image.thumbnail((300, 300))
                number = len(cases) + 1
                image.save(thumbs / f'{number:03d}.jpg', quality=85)
                seen.add(key)
                cases.append({'case': number, 'provider': provider, 'provider_item_id': candidate['provider_item_id'],
                              'query': query, 'title': candidate.get('title', ''), 'medium': candidate.get('medium', ''),
                              'description': candidate.get('description', ''), 'source_url': candidate['source_url'],
                              'image_sha256': hashlib.sha256(data).hexdigest(), 'label': None})
                kept += 1
                if kept == 3:
                    break
            print(f'{provider} "{query}": {kept} kept')
    (scratch / 'cases-unlabelled.json').write_text(json.dumps(cases, indent=1, ensure_ascii=False), encoding='utf-8')
    sheet(thumbs, scratch)
    print(f'{len(cases)} cases; contact sheets in {scratch}')


def sheet(thumbs: Path, scratch: Path, per_sheet: int = 30):
    """Numbered contact sheets: pictures and numbers only, no catalogue text."""
    from PIL import Image, ImageDraw
    files = sorted(thumbs.glob('*.jpg'))
    for start in range(0, len(files), per_sheet):
        chunk = files[start:start + per_sheet]
        board = Image.new('RGB', (6 * 310, 5 * 330), (243, 239, 228))
        draw = ImageDraw.Draw(board)
        for i, path in enumerate(chunk):
            x, y = (i % 6) * 310 + 5, (i // 6) * 330 + 25
            board.paste(Image.open(path), (x, y))
            draw.text((x, y - 20), path.stem, fill=(29, 28, 26))
        board.save(scratch / f'sheet-{start // per_sheet + 1}.png')


CASES_SHA = '962dfd24a47f717a'
JEV_QUESTION = {'doc': {'type': 'noul', 'instructions': 'Based only on this catalogue record, is the image most likely a '
                        'plain documentation photograph (an object on a plain background, a coin, a specimen) or a page '
                        'of text, rather than a composed picture?'}}  # the v1.1 question, unchanged


def decide(rows: list[dict], arm: str) -> dict:
    negatives = [r for r in rows if r['label'] == 'negative']
    positives = [r for r in rows if r['label'] == 'positive']
    skipped_negatives = sum(r[arm] for r in negatives)
    skipped_positives = sum(r[arm] for r in positives)
    enough = len(negatives) >= 10
    holds = skipped_positives == 0 and skipped_negatives * 2 >= len(negatives)
    return {'negatives_skipped': eval_v11.rate(skipped_negatives, len(negatives)),
            'positives_skipped': eval_v11.rate(skipped_positives, len(positives)),
            'criteria_hold': holds, 'enough_negatives': enough,
            'decision': 'integrate' if holds and enough else 'promising, deferred' if holds else 'not integrated'}


RULES = EVAL / 'metadata-rules.json'  # the deterministic arm, written before the cases were collected


def rule_match(case: dict, data: dict) -> dict | None:
    """The first rule phrase found, as whole words, in the title, medium or description."""
    text = f" {' '.join(coding.words(' '.join(str(case.get(field) or '') for field in data['fields'])))} "
    for rule in data['rules']:
        for phrase in rule['phrases']:
            normal = ' '.join(coding.words(phrase))
            if normal and f' {normal} ' in text:
                return {'rule': rule['id'], 'label': rule['label'], 'phrase': phrase}
    return None


def metadata_eval(env_file: str | None):
    data = json.loads(RULES.read_text(encoding='utf-8'))
    digest = hashlib.sha256(CASES.read_bytes()).hexdigest()[:16]
    if digest != CASES_SHA:
        raise SystemExit(f'metadata-cases.json changed since it was frozen ({digest} != {CASES_SHA})')
    cases = json.loads(CASES.read_text(encoding='utf-8'))['cases']
    rows = []
    for case in cases:
        hit = rule_match(case, data)
        rows.append({'case': case['case'], 'provider': case['provider'], 'label': case['label'],
                     'uncertain': case['label_uncertain'], 'rules': bool(hit), 'rule': hit})
    result = {'cases': len(rows), 'negatives': sum(r['label'] == 'negative' for r in rows), 'rules': decide(rows, 'rules')}
    if env_file:
        jev = eval_v11.Jev(eval_v11.jev_key(env_file))
        for case, row in zip(cases, rows):
            state = {k: case[k] for k in ('title', 'medium', 'description')} | {'source': case['provider']}
            row['jev_p'] = round(jev.ask(state, JEV_QUESTION)['doc'], 3)
            row['jev'] = row['jev_p'] >= 0.8
        result['jev'] = decide(rows, 'jev') | {'calls': len(jev.calls), 'failures': jev.failures, 'spent_usd': round(jev.spent, 4)}
    result['rows'] = rows
    (EVAL / 'metadata-results.json').write_text(json.dumps(result, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k != 'rows'}, indent=1))


if __name__ == '__main__':
    command = sys.argv[1:] or ['coding', 'dev']
    if command[0] == 'coding':
        coding_eval(command[1] if len(command) > 1 else 'dev')
    elif command[0] == 'collect-metadata':
        collect(Path(command[1]))
    elif command[0] == 'metadata':
        metadata_eval(command[2] if len(command) > 2 and command[1] == '--env-file' else None)
    else:
        raise SystemExit(__doc__)
