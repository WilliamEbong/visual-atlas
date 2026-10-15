"""Opt-in live checks: real provider APIs and the user's signed-in assistants. Run: uv run pytest -m live"""

import io

import pytest
from PIL import Image, ImageDraw

from atlas import catalog, providers, rights
from atlas.ai import claude_cli, codex_cli, tasks
from atlas.fetch import Fetcher, FetchError

pytestmark = pytest.mark.live
TAXONOMY, POLICIES, *_ = catalog.load()
IDS = {t['id'] for t in TAXONOMY['techniques']}


@pytest.mark.parametrize('provider, query', [('aic', 'lighthouse'), ('met', 'lighthouse'), ('cma', 'lighthouse'),
                                             ('smithsonian', 'lighthouse'), ('commons', 'lighthouse')])
def test_provider_search_and_rights(provider, query):
    try:
        candidates = providers.search(Fetcher(POLICIES), provider, query, 0, 5)
    except FetchError as error:
        if error.code == 'rate_limited':
            pytest.skip(f'{provider} rate limit reached (shared demo key); not a failure')
        raise
    assert candidates, f'{provider} returned nothing'
    decisions = [rights.check(c, catalog.policy(POLICIES, provider)) for c in candidates]
    assert all('eligible' in d for d in decisions)


@pytest.mark.parametrize('provider, query', [('rijksmuseum', 'landscape'), ('nga', 'harbor')])
def test_v03_sources_search_rights_and_one_image(provider, query, tmp_path):
    """The National Gallery case downloads its open data (about 190 MB) into a temporary folder."""
    fetcher = Fetcher(POLICIES)
    candidates = providers.search(fetcher, provider, query, 0, 4, home=tmp_path)
    assert candidates, f'{provider} returned nothing'
    decisions = [rights.check(c, catalog.policy(POLICIES, provider)) for c in candidates]
    eligible = [c for c, d in zip(candidates, decisions) if d['eligible']]
    assert eligible, [d.get('reason') for d in decisions]
    data = fetcher.get_image(provider, eligible[0]['image_url'])
    assert Image.open(io.BytesIO(data)).size[0] > 400


@pytest.fixture
def picture(tmp_path):
    image = Image.new('RGB', (900, 600), (235, 232, 222))
    draw = ImageDraw.Draw(image)
    draw.rectangle([620, 380, 660, 520], fill=(20, 20, 20))  # one small dark figure in a large empty field
    path = tmp_path / 'figure.jpg'
    buffer = io.BytesIO()
    image.save(buffer, 'JPEG')
    path.write_bytes(buffer.getvalue())
    return path


@pytest.mark.parametrize('module, model', [(codex_cli, 'gpt-6-luna'), (claude_cli, 'haiku')])
def test_backend_sees_pixels_and_answers_the_contract(module, model, picture):
    metadata = {'title': 'Test card', 'creator': 'Visual Atlas'}
    answer = module.run(tasks.analyze_prompt(TAXONOMY['techniques'], metadata), tasks.analyze_schema(sorted(IDS)),
                        [picture], model=model)
    result = tasks.validate_analysis(answer['result'], IDS, metadata)
    assert result['observations']
    assert answer['cli_version'] != 'unknown'
