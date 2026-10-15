"""Visual Atlas v1.1 evaluation (maintainers only: live AI and live providers; never touches a real library).

  uv run python scripts/eval_v11.py fetch          # rights-checked candidates per category -> scratch/eval-v11
  (the builder looks at every image and writes docs/evaluation/v1.1/cases.json BEFORE any model runs)
  uv run python scripts/eval_v11.py freeze         # hash the final split, prompts, model ids and this script
  uv run python scripts/eval_v11.py run dev        # proposer + both checker arms on the development split
  uv run python scripts/eval_v11.py run final      # once, after the checker decision; refuses if the freeze changed
  uv run python scripts/eval_v11.py retrieval      # request coding + reference retrieval on frozen briefs (no AI)
  uv run python scripts/eval_v11.py jev USE [--env-file PATH]   # TypeSafe Jev arms (USE: coding, ranking, metadata,
                                                                # review); the key is read into memory only
  uv run python scripts/eval_v11.py report         # docs/evaluation/v1.1/REPORT.md from the saved raw results

Reference judgments are the builder's provisional readings of each image's pixels, not expert ground truth."""

import hashlib
import json
import math
import os
import sqlite3
import sys
import tempfile
import time
from pathlib import Path

from atlas import catalog, coding, images, jobs, providers, rights, transfer
from atlas.ai import claude_cli, codex_cli, tasks
from atlas.ai.process import BackendError
from atlas.fetch import Fetcher, FetchError

ROOT = Path(__file__).resolve().parent.parent
SCRATCH = ROOT / 'scratch' / 'eval-v11'
EVAL = ROOT / 'docs' / 'evaluation' / 'v1.1'
PROPOSER = ('codex', codex_cli, 'gpt-6-astra')
CHECKER = ('claude', claude_cli, 'sonnet')
MIN_CONFIDENCE = .4  # the app applies proposals at this confidence or above

# (category, provider, query, why). Several per category so a few failed searches still leave enough cases.
QUERIES = [
    ('clear', 'commons', 'silhouette sunset person', 'silhouette'),
    ('clear', 'commons', 'railway tracks perspective', 'leading lines'),
    ('clear', 'commons', 'lone boat calm sea', 'negative space'),
    ('clear', 'aic', 'cathedral facade', 'symmetry'),
    ('clear', 'commons', 'tiny hiker mountain', 'scale contrast'),
    ('clear', 'cma', 'candle portrait', 'light-dark contrast'),
    ('clear', 'commons', 'colonnade arches', 'rhythm'),
    ('subtle', 'aic', 'tonalist landscape', 'limited palette'),
    ('subtle', 'met', 'woodblock print bird branch', 'off-centre placement'),
    ('subtle', 'cma', 'portrait woman looking away', 'gaze direction'),
    ('subtle', 'aic', 'river valley landscape', 'layered depth'),
    ('ambiguous', 'commons', 'busy market street', 'crowded scene'),
    ('ambiguous', 'cma', 'abstract painting', 'abstract'),
    ('ambiguous', 'aic', 'still life table', 'still life'),
    ('monochrome', 'commons', 'black and white street photography', 'monochrome photograph'),
    ('monochrome', 'cma', 'etching landscape', 'monochrome print'),
    ('monochrome', 'smithsonian', 'photograph portrait 1900', 'monochrome portrait'),
    ('catalogue', 'smithsonian', 'ceramic vase', 'object on plain ground'),
    ('catalogue', 'cma', 'teapot', 'object on plain ground'),
    ('catalogue', 'met', 'coin', 'object on plain ground'),
    ('none', 'commons', 'scanned document page text', 'mostly text'),
    ('none', 'smithsonian', 'insect specimen', 'specimen photograph'),
    ('confused', 'commons', 'backlit figure window', 'silhouette vs light-dark contrast'),
    ('confused', 'commons', 'fog forest', 'negative space vs atmospheric perspective'),
    ('confused', 'commons', 'red umbrella crowd', 'colour contrast vs repetition with interruption'),
    ('confused', 'commons', 'long corridor arches', 'framing vs leading lines vs symmetry'),
    ('confused', 'aic', 'view through window painting', 'framing vs layered depth'),
    ('confused', 'commons', 'reflection lake mountains', 'symmetry vs colour harmony'),
]


def excluded() -> set[tuple[str, str]]:
    """Items already used: the starter pack, the v1 held-out set, and the owner's library (read-only)."""
    seen = {(r['image']['provider'], r['image']['provider_item_id']) for r in
            json.loads((ROOT / 'starter' / 'library.json').read_text(encoding='utf-8'))['references']}
    for record in json.loads((ROOT / 'docs' / 'evaluation' / 'heldout-results.json').read_text(encoding='utf-8')):
        seen.add((record['provider'], record['file'].split('-', 2)[2].removesuffix('.jpg')))
    real = Path.home() / 'VisualAtlas' / 'atlas.db'
    if real.is_file():
        with sqlite3.connect(real.resolve().as_uri() + '?mode=ro', uri=True) as db:
            seen |= set(db.execute('SELECT provider, provider_item_id FROM images'))
    return seen


def fetch():
    taxonomy, policies, *_ = catalog.load()
    fetcher, skip, chosen = Fetcher(policies), excluded(), []
    SCRATCH.mkdir(parents=True, exist_ok=True)
    for category, provider, query, why in QUERIES:
        try:
            found = providers.search(fetcher, provider, query, 0, 10)
        except FetchError as error:
            print(f'{provider} {query!r}: search failed ({error.code})')
            continue
        for candidate in found:
            if (provider, candidate['provider_item_id']) in skip:
                continue
            decision = rights.check(candidate, catalog.policy(policies, provider))
            if not decision['eligible']:
                continue
            try:
                data = fetcher.get_image(provider, candidate['image_url'], headers=candidate['image_headers'])
                picture, _ = images.open_checked(data)
            except (FetchError, images.ImageRejected):
                continue
            if images.quality_problem(picture, images.metrics(picture)):
                continue
            name = f"{len(chosen) + 1:02d}-{provider}-{candidate['provider_item_id']}.jpg"
            copy = picture.copy()
            copy.thumbnail((1024, 1024))
            copy.save(SCRATCH / name, 'JPEG', quality=88)
            chosen.append({'file': name, 'category': category, 'provider': provider,
                           'provider_item_id': candidate['provider_item_id'], 'query': query, 'why': why,
                           'title': candidate['title'], 'creator': candidate['creator'], 'date': candidate['date_text'],
                           'medium': candidate['medium'], 'description': candidate['description'],
                           'source_url': candidate['source_url'], 'licence': decision['label'],
                           'original_sha256': hashlib.sha256(data).hexdigest(),
                           'eval_copy_sha256': hashlib.sha256((SCRATCH / name).read_bytes()).hexdigest()})
            skip.add((provider, candidate['provider_item_id']))
            print(f"{name}: [{category}] {candidate['title'][:60]} ({decision['label']})")
            break
    (EVAL / 'candidates.json').write_text(json.dumps(chosen, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')


if __name__ == '__main__':
    command = sys.argv[1]
    {'fetch': fetch}[command]()
