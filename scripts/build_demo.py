"""Build the read-only public demo (web/dist-demo) from the bundled starter pack. No AI, no network.

Usage: uv run python scripts/build_demo.py [BASE_PATH]   (BASE_PATH defaults to ./)"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import quote

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
STAGE = ROOT / 'web' / 'public-demo'


def main(base: str = './'):
    from atlas import jobs, transfer
    from atlas.server import create_app

    with tempfile.TemporaryDirectory() as directory:
        home = Path(directory) / 'home'
        os.environ['VISUAL_ATLAS_HOME'] = str(home)
        with jobs.open_store(home) as store:
            transfer.import_starter(store, home, ROOT / 'starter')
        client = TestClient(create_app(home, token='demo', dist=Path(directory)), base_url='http://127.0.0.1',
                            headers={'x-atlas-token': 'demo'})
        responses = {}

        def grab(path):
            response = client.get('/api/' + path)
            response.raise_for_status()
            responses[path] = response.json()
            return responses[path]

        taxonomy = grab('taxonomy')
        for path in ('sources', 'coverage', 'collections', 'briefs'):
            grab(path)
        library = grab('library?limit=200')
        for item in library['items']:
            grab(f"images/{item['id']}")
            grab(f"graph?focus=image:{item['id']}")
        for technique in taxonomy['techniques']:
            grab(f"techniques/{technique['id']}")
            grab(f"graph?focus=technique:{technique['id']}")
        for goal in taxonomy['goals']:
            grab(f"goals/{goal['id']}")
            grab(f"graph?focus=goal:{goal['id']}")
        for kind in ('operation', 'domain'):
            for entry in taxonomy[kind + 's']:
                grab(f"graph?focus={kind}:{entry['id']}")
        for technique in taxonomy['techniques']:
            grab(f"graph?focus=technique:{technique['id']}&limit=200")
        if STAGE.exists():
            shutil.rmtree(STAGE)
        shutil.copytree(ROOT / 'web' / 'public', STAGE)
        for kind in ('analysis', 'thumbs', 'originals'):
            if (home / 'media' / kind).is_dir():
                shutil.copytree(home / 'media' / kind, STAGE / 'media' / kind, dirs_exist_ok=True)
    (STAGE / 'snapshot.json').write_text(json.dumps({'responses': responses, 'library': library}, ensure_ascii=False),
                                        encoding='utf-8')
    npm = shutil.which('npm') or 'npm'
    subprocess.run([npm, 'run', 'build:demo', '--', '--base', base], cwd=ROOT / 'web', check=True,
                   env={**os.environ, 'VITE_DEMO': '1'})
    print(f"Demo built in web/dist-demo with {len(library['items'])} images (base {quote(base)}).")


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else './')
