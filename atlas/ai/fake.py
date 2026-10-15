"""Offline practice backend: deterministic, schema-valid answers with no model behind them.

Used by tests and the offline demo. Every result it produces is labelled 'practice' in the app."""

import hashlib
import re
from pathlib import Path

NAME = 'fake'


def check(runner=None, force=False) -> str:
    return 'offline'


def _pick(options: list, seed: bytes, count: int) -> list:
    digest = hashlib.sha256(seed).digest()
    ordered = sorted(options, key=lambda option: hashlib.sha256(digest + str(option).encode()).digest())
    return ordered[:count]


def run(prompt: str, schema: dict, images: list[Path], *, model: str = 'practice', record=None, timeout=0,
        cancel=None, runner=None) -> dict:
    seed = b''.join(Path(path).read_bytes()[:4096] for path in images) or prompt.encode()
    properties = schema['properties']
    if 'observations' in properties:
        ids = properties['techniques']['items']['properties']['technique_id']['enum']
        chosen = _pick(ids, seed, 2)
        result = {
            'image_usable': True, 'unusable_reason': None,
            'observations': [{'id': 'o1', 'text': 'Practice observation: the main shape sits near the centre.',
                              'region': 'center'},
                             {'id': 'o2', 'text': 'Practice observation: the surrounding area is comparatively plain.',
                              'region': 'background'}],
            'techniques': [{'technique_id': technique, 'role': 'primary' if n == 0 else 'supporting',
                            'evidence': ['o1', 'o2'][: n + 1], 'effect': 'Practice effect: may focus attention.',
                            'confidence': 0.6} for n, technique in enumerate(chosen)],
            'ambiguities': ['Practice answer from the offline demo backend, not a real analysis.'],
            'subjects': ['practice'], 'summary': 'Offline practice analysis (no model was used).',
            'creator_intent': None}
    elif 'verdicts' in properties:
        proposed = list(dict.fromkeys(re.findall(r'"technique_id": "([a-z0-9-]+)"', prompt)))
        result = {'verdicts': [{'technique_id': t, 'holds': n % 2 == 0, 'reason': 'Practice verdict.'}
                               for n, t in enumerate(proposed)]}
    elif 'queries' in properties:
        query = properties['queries']['items']['properties']
        providers = query['provider']['enum']
        techniques = query['technique_id']['anyOf'][1]['enum']
        words = re.findall(r'[a-z]{4,}', prompt.rsplit('Request (JSON data):', 1)[-1].lower())[:3] or ['landscape']
        result = {'queries': [{'provider': p, 'query': ' '.join(words[:2]), 'technique_id': _pick(techniques, seed, 1)[0]}
                              for p in providers]}
    elif 'directions' in properties:
        item = properties['directions']['items']['properties']
        techniques = item['technique_ids']['items']['enum']
        images = [i for i in item['image_ids']['items']['enum'] if i]
        result = {'directions': [{'title': f'Practice direction {n + 1}', 'idea': 'A practice idea from the offline demo.',
                                  'rationale': 'Practice rationale; no model was used.',
                                  'technique_ids': _pick(techniques, seed + bytes([n]), 2),
                                  'image_ids': _pick(images, seed + bytes([n]), 2),
                                  'execution': ['Practice suggestion.'], 'tradeoffs': ['Practice tradeoff.']}
                                 for n in range(3)]}
    else:
        image_ids = properties['per_image']['items']['properties']['image_id']['enum']
        result = {'shared': ['Practice: both images use a clear focal area.'],
                  'differences': ['Practice: they differ in palette.'],
                  'per_image': [{'image_id': i, 'note': 'Practice note.'} for i in image_ids],
                  'technique_notes': []}
    return {'result': result, 'input_tokens': 0, 'output_tokens': 0, 'cli_version': 'offline',
            'model_version': 'practice'}
