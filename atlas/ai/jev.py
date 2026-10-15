"""Optional TypeSafe Jev relevance ranking for project directions: off by default, the person's own key.

Text only. When it is switched on, the brief and, for each candidate reference, its title, maker, date, summary and
technique names are sent to api.typesafe.ai; no image is sent. It only reorders references that ordinary code already
found; licences, review states and image checks never depend on it. It is the one Jev use that met its pre-set
criteria in docs/evaluation/v1.1/REPORT.md, and the question below is the exact one evaluated there."""

import hashlib
import json
import time

import httpx

URL = 'https://api.typesafe.ai/v1/systemone'
MODEL = 'jev-1.13.0'
QUESTION = 'Would a designer pick this library reference as useful visual evidence for the request? Reference: '
QUESTION_SHA = hashlib.sha256((MODEL + QUESTION).encode()).hexdigest()[:16]
MAX_CANDIDATES = 120  # one request stays well inside the documented limits
TIMEOUT = 30


class JevError(Exception):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def rank(request: str, records: list[dict], names: dict[str, str], key: str, *, transport=None,
         sleep=time.sleep) -> tuple[list[int], dict]:
    """Image ids most-relevant first (ties keep the given order), plus provenance for the saved analysis.

    One retry on a rate limit, a server error or a network error; any other failure raises JevError with a short
    code and never the key or the request body."""
    candidates = records[:MAX_CANDIDATES]
    questions = {f"r:{r['image_id']}": {'type': 'noul', 'instructions': QUESTION + json.dumps(
        {'title': r['title'], 'maker': r['creator'], 'date': r['date'], 'summary': r['summary'],
         'techniques': [names.get(t['id'], t['id']) for t in r['techniques']]}, ensure_ascii=False)} for r in candidates}
    started = time.monotonic()
    with httpx.Client(transport=transport, timeout=TIMEOUT, trust_env=False,
                      headers={'Authorization': f'Bearer {key}'}) as client:
        for attempt in (1, 2):
            try:
                response = client.post(URL, json={'model': MODEL, 'state': request[:4000], 'questions': questions})
            except httpx.HTTPError:
                code = 'network'
            else:
                if response.status_code == 200:
                    break
                code = 'auth' if response.status_code in (401, 403) else f'http_{response.status_code}'
                if response.status_code not in (429, 500, 502, 503, 529):
                    raise JevError(code)
            if attempt == 2:
                raise JevError(code)
            sleep(2)
    try:
        body = response.json()
        answers = {key_: float(value['noul']) for key_, value in body['answers'].items()}
    except (ValueError, KeyError, TypeError, AttributeError):
        raise JevError('invalid_response') from None
    if set(answers) != set(questions) or not all(0 <= p <= 1 for p in answers.values()):
        raise JevError('invalid_response')
    position = {r['image_id']: n for n, r in enumerate(candidates)}
    order = sorted(position, key=lambda image_id: (-answers[f'r:{image_id}'], position[image_id]))
    usage = body.get('usage') or {}
    return order, {'method': 'jev', 'model': str(body.get('model') or MODEL)[:40], 'question_sha': QUESTION_SHA,
                   'candidates': len(candidates), 'input_tokens': int(usage.get('input_tokens') or 0),
                   'latency_ms': int((time.monotonic() - started) * 1000)}
