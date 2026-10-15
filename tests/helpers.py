"""Shared offline test helpers: a data home, fake provider HTTP, distinct test JPEGs."""

import io
import json
import random
import socket
from pathlib import Path

import httpx
from PIL import Image, ImageDraw

from atlas import catalog
from atlas.fetch import Fetcher

FIXTURES = Path(__file__).parent / 'fixtures' / 'providers'


def jpeg(seed: int, size=(900, 640)) -> bytes:
    """A distinct, high-contrast picture per seed (so dHash never calls two of them duplicates)."""
    rng = random.Random(seed)
    image = Image.new('RGB', size)
    draw = ImageDraw.Draw(image)
    blocks = 6
    for bx in range(blocks):
        for by in range(blocks):
            color = (rng.randrange(256), rng.randrange(256), rng.randrange(256))
            draw.rectangle([bx * size[0] // blocks, by * size[1] // blocks, (bx + 1) * size[0] // blocks,
                            (by + 1) * size[1] // blocks], fill=color)
    out = io.BytesIO()
    image.save(out, 'JPEG', quality=85)
    return out.getvalue()


def public_resolver(host, port, type=None):
    return [(socket.AF_INET, socket.SOCK_STREAM, 6, '', ('93.184.216.34', port))]


def aic_fetcher(requests: list | None = None, fail_images: set[str] | None = None) -> Fetcher:
    """Fetcher whose AIC search returns the recorded fixture and whose IIIF images are distinct JPEGs."""
    search = json.loads((FIXTURES / 'aic_search.json').read_text(encoding='utf-8'))

    def handler(request: httpx.Request):
        if requests is not None:
            requests.append(str(request.url))
        if request.url.host == 'api.artic.edu':
            return httpx.Response(200, json=search)
        if request.url.host == 'www.artic.edu' and '/iiif/2/' in request.url.path:
            image_id = request.url.path.split('/')[3]
            if fail_images and image_id in fail_images:
                return httpx.Response(503)
            return httpx.Response(200, content=jpeg(sum(map(ord, image_id))), headers={'content-type': 'image/jpeg'})
        return httpx.Response(404)

    _, policies, *_ = catalog.load()
    return Fetcher(policies, transport=httpx.MockTransport(handler), resolver=public_resolver, sleep=lambda s: None)
