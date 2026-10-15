"""Held-out challenge for technique readings (maintainers; uses live AI and providers).

  uv run python scripts/heldout.py fetch   # download the challenge images (licence-checked) into scratch/heldout
  (a person writes docs/evaluation/heldout-expectations.json after looking at the images, before any model runs)
  uv run python scripts/heldout.py run     # Codex analyses, Claude checks Codex, Claude analyses independently

The expectations are the builder's judgment, not expert ground truth; the report says so.
Superseded by scripts/eval_v11.py (separate development and final splits); kept to reproduce the v1 rounds."""

import hashlib
import json
import sys
from pathlib import Path

from atlas import catalog, images, providers, rights
from atlas.ai import claude_cli, codex_cli, tasks
from atlas.ai.process import BackendError
from atlas.fetch import Fetcher, FetchError

ROOT = Path(__file__).resolve().parent.parent
SCRATCH = ROOT / 'scratch' / 'heldout'
EVAL = ROOT / 'docs' / 'evaluation'
# (provider, query, why it is in the set). Chosen to span clear, subtle and ambiguous cases.
QUERIES = [
    ('aic', 'Hiroshige rain bridge', 'diagonal rain, possible diagonal energy'),
    ('aic', 'Whistler nocturne', 'limited palette, very low contrast'),
    ('met', 'Vermeer', 'interior light, possible framing/value'),
    ('cma', 'candlelight', 'chiaroscuro'),
    ('cma', 'abstract composition', 'abstract: techniques ambiguous'),
    ('aic', 'Seurat', 'pattern/rhythm, figures'),
    ('met', 'Hokusai wave', 'scale contrast, motion'),
    ('commons', 'lone tree fog', 'negative space, atmosphere'),
    ('commons', 'symmetrical corridor', 'symmetry, leading lines'),
    ('cma', 'map', 'a map: probably unusable or no technique'),
    ('met', 'portrait looking', 'gaze direction'),
    ('commons', 'market crowd', 'busy scene: ambiguous'),
]


def fetch():
    taxonomy, policies, *_ = catalog.load()
    fetcher = Fetcher(policies)
    SCRATCH.mkdir(parents=True, exist_ok=True)
    chosen = []
    for provider, query, why in QUERIES:
        try:
            candidates = providers.search(fetcher, provider, query, 0, 8)
        except FetchError as error:
            print(f'{provider} {query!r}: search failed ({error.code})')
            continue
        for candidate in candidates:
            decision = rights.check(candidate, catalog.policy(policies, provider))
            if not decision['eligible']:
                continue
            try:
                data = fetcher.get_image(provider, candidate['image_url'], headers=candidate['image_headers'])
                picture, kind = images.open_checked(data)
            except (FetchError, images.ImageRejected):
                continue
            stats = images.metrics(picture)
            if images.quality_problem(picture, stats):
                continue
            name = f"{len(chosen) + 1:02d}-{provider}-{candidate['provider_item_id']}.jpg"
            copy = picture.copy()
            copy.thumbnail((1024, 1024))
            copy.save(SCRATCH / name, 'JPEG', quality=88)
            chosen.append({'file': name, 'provider': provider, 'query': query, 'why': why,
                           'title': candidate['title'], 'creator': candidate['creator'], 'date': candidate['date_text'],
                           'source_url': candidate['source_url'], 'licence': decision['label'],
                           'sha256': hashlib.sha256(data).hexdigest()})
            print(f"{name}: {candidate['title'][:60]} ({decision['label']})")
            break
    (SCRATCH / 'images.json').write_text(json.dumps(chosen, indent=2, ensure_ascii=False), encoding='utf-8')


def run():
    taxonomy, *_ = catalog.load()
    techniques = {t['id']: t for t in taxonomy['techniques']}
    ids = set(techniques)
    chosen = json.loads((SCRATCH / 'images.json').read_text(encoding='utf-8'))
    expected = {e['file']: e for e in json.loads((EVAL / 'heldout-expectations.json').read_text(encoding='utf-8'))}
    results = []
    for item in chosen:
        path = SCRATCH / item['file']
        metadata = {'title': item['title'], 'creator': item['creator'], 'date': item['date'], 'source': item['provider']}
        prompt = tasks.analyze_prompt(list(techniques.values()), metadata)
        schema = tasks.analyze_schema(sorted(ids))
        record = {**item, 'expected': expected.get(item['file'], {})}
        for name, module, model in (('codex', codex_cli, 'gpt-6-astra'), ('claude', claude_cli, 'sonnet')):
            try:
                answer = module.run(prompt, schema, [path], model=model)
                result = tasks.validate_analysis(answer['result'], ids, metadata)
                record[name] = {'usable': result['image_usable'],
                                'techniques': {t['technique_id']: t['confidence'] for t in result['techniques']},
                                'ambiguities': result['ambiguities'], 'model': answer.get('model_version')}
            except (BackendError, tasks.InvalidResult) as error:
                record[name] = {'error': str(getattr(error, 'code', error))}
        proposals = [{'technique_id': t, 'evidence': ['(see image)'], 'effect': ''}
                     for t in record.get('codex', {}).get('techniques', {})]
        if proposals:
            try:
                answer = claude_cli.run(tasks.verify_prompt(proposals, techniques), tasks.verify_schema(sorted(ids)), [path],
                                        model='sonnet')
                verdicts = tasks.validate_verify(answer['result'], {p['technique_id'] for p in proposals}, ids)['verdicts']
                record['claude_verify'] = {v['technique_id']: v['holds'] for v in verdicts}
            except (BackendError, tasks.InvalidResult) as error:
                record['claude_verify'] = {'error': str(getattr(error, 'code', error))}
        results.append(record)
        print(item['file'], json.dumps({k: record.get(k) for k in ('codex', 'claude', 'claude_verify')})[:300])
    (EVAL / 'heldout-results.json').write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding='utf-8')
    report(results, techniques)


def report(results, techniques):
    def overlap(a, b):
        return len(a & b) / len(a | b) if a | b else 1.0

    lines = ['# Held-out challenge: technique readings', '',
             'Twelve images that were never in the library, chosen to include clear, subtle and ambiguous cases.',
             'Expected techniques were written by the builder (Claude, while building Visual Atlas) after looking at',
             'each image and before any model ran. **They are builder judgment, not expert ground truth**; treat the',
             'numbers as a sanity check of behaviour, not as accuracy.', '',
             '| # | Image | Builder expects | Codex proposed | Claude (independent) | Claude agrees with Codex on |',
             '|---|---|---|---|---|---|']
    stats = {'codex_hits': 0, 'codex_total': 0, 'expected_total': 0, 'expected_found': 0, 'jaccard': [], 'verify': [0, 0]}
    for n, record in enumerate(results, 1):
        expected = set(record['expected'].get('techniques', []))
        codex = set(record.get('codex', {}).get('techniques', {}))
        claude = set(record.get('claude', {}).get('techniques', {}))
        verify = record.get('claude_verify', {})
        agreed = [t for t, holds in verify.items() if holds is True]
        stats['codex_hits'] += len(codex & expected)
        stats['codex_total'] += len(codex)
        stats['expected_total'] += len(expected)
        stats['expected_found'] += len(expected & (codex | claude))
        if 'error' not in record.get('codex', {}) and 'error' not in record.get('claude', {}):
            stats['jaccard'].append(overlap(codex, claude))
        if 'error' not in verify:
            stats['verify'][0] += len(agreed)
            stats['verify'][1] += len(verify)

        def names(values):
            return ', '.join(techniques[t]['name'] for t in sorted(values)) or '—'

        note = record['expected'].get('note', '')
        lines.append(f"| {n} | {record['title'][:40]} ({record['provider']}) | {names(expected)}{' — ' + note if note else ''} | "
                     f"{names(codex) if 'error' not in record.get('codex', {}) else record['codex']['error']} | "
                     f"{names(claude) if 'error' not in record.get('claude', {}) else record['claude']['error']} | {names(agreed)} |")
    jaccard = sum(stats['jaccard']) / len(stats['jaccard']) if stats['jaccard'] else 0
    lines += ['', '## Summary', '',
              f"- Codex proposals that match a builder expectation: {stats['codex_hits']} of {stats['codex_total']}.",
              f"- Builder expectations found by at least one model: {stats['expected_found']} of {stats['expected_total']}.",
              f"- Codex vs Claude independent readings, mean overlap (Jaccard): {jaccard:.2f}.",
              f"- Claude agreed with {stats['verify'][0]} of {stats['verify'][1]} Codex proposals when asked to check them.",
              '', 'Raw results: `heldout-results.json`. Expectations: `heldout-expectations.json`.']
    (EVAL / 'HELDOUT.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print('\n'.join(lines[-6:]))


if __name__ == '__main__':
    {'fetch': fetch, 'run': run}[sys.argv[1]]()
