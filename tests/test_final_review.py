"""Final pre-merge Codex review: library files stay inside the library, MCP reads UTF-8, readable output keeps credits."""

import json
import os
import subprocess
import sys

import pytest
from PIL import Image
from typer.testing import CliRunner

from atlas import desk, jobs, mcp_server, transfer
from atlas.cli import app
from atlas.home import REPO


@pytest.fixture(scope='module')
def starter_home(tmp_path_factory):
    home = tmp_path_factory.mktemp('final') / 'home'
    with jobs.open_store(home) as store:
        transfer.import_starter(store, home, REPO / 'starter')
    return home


def test_view_reference_refuses_a_library_file_outside_the_media_folder(starter_home, tmp_path, monkeypatch):
    outside = tmp_path / 'elsewhere.jpg'
    Image.new('RGB', (20, 20)).save(outside, 'JPEG')
    monkeypatch.setenv('VISUAL_ATLAS_HOME', str(starter_home))
    monkeypatch.setattr(desk, 'get', lambda ref, **_: {'ref': ref, 'layer': 'library', 'file': str(outside),
                                                       'title': 't', 'licence': {'label': 'x'}})
    with pytest.raises(LookupError):
        mcp_server._view('library:1', 256)


def test_mcp_reads_utf8_requests_without_an_encoding_override(starter_home):
    request = {'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call',
               'params': {'name': 'advise', 'arguments': {'brief': 'é' * 3000}}}  # 3000 characters, 6000 if misread
    environment = {k: v for k, v in os.environ.items() if k not in ('PYTHONIOENCODING', 'PYTHONUTF8')}
    environment['VISUAL_ATLAS_HOME'] = str(starter_home)
    environment.pop('VISUAL_ATLAS_DESIGN_SYSTEMS', None)
    process = subprocess.run([sys.executable, '-c', 'from atlas.mcp_server import serve; serve()'],
                             input=(json.dumps(request, ensure_ascii=False) + '\n').encode('utf-8'),
                             capture_output=True, env=environment, cwd=REPO, timeout=120)
    reply = json.loads(process.stdout.decode('utf-8').splitlines()[0])
    assert reply['result']['isError'] is False, reply


def test_readable_publish_output_prints_each_credit(starter_home, monkeypatch):
    monkeypatch.setenv('VISUAL_ATLAS_HOME', str(starter_home))
    monkeypatch.delenv('VISUAL_ATLAS_DESIGN_SYSTEMS', raising=False)
    out = CliRunner().invoke(app, ['refs', '--technique', 'rhythm-pattern', '--publish', '--text', '--limit', '40']).output
    assert 'Credit: ' in out and 'creativecommons.org' in out
