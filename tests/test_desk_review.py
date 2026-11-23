"""Regression tests for the Codex review of the reference desk (2026-11-23). Each fails on the code before the fix."""

import importlib.util
import io
import json
import os
import re
import shutil
import sqlite3
import subprocess

import pytest
from PIL import Image

from atlas import desk, jobs, layers, mcp_server, transfer
from atlas.home import REPO

GUARD = importlib.util.spec_from_file_location('check_no_data', REPO / 'scripts' / 'check_no_data.py')
check_no_data = importlib.util.module_from_spec(GUARD)
GUARD.loader.exec_module(check_no_data)


@pytest.fixture(scope='module')
def starter_home(tmp_path_factory):
    home = tmp_path_factory.mktemp('review') / 'home'
    with jobs.open_store(home) as store:
        transfer.import_starter(store, home, REPO / 'starter')
    return home


def _system(tmp_path, rows):
    root = tmp_path / 'skills' / 'garden-of-lingering'
    (root / 'references').mkdir(parents=True)
    (root / 'SKILL.md').write_text('---\ndescription: >-\n  Gardens, tea and flowers.\n---\n', encoding='utf-8')
    header = 'id,slots,subjects,ground,colour,medium,title,creator,date,licence,credit,page,image,notes,size'
    (root / 'references' / 'images.csv').write_text('\n'.join([header, *rows]) + '\n', encoding='utf-8')
    for row in rows:
        path = root / 'assets' / 'library' / f"{row.split(',')[0]}.jpg"
        path.parent.mkdir(parents=True, exist_ok=True)
        Image.new('RGB', (300, 200), (len(row) % 255, 90, 60)).save(path, 'JPEG')
    return root


@pytest.mark.parametrize('note, code', [('CC BY-NC 4.0', 'unclear'), ('CC BY-SA 2.0', 'unclear'),
                                        ('not in the public domain', 'unclear'), ('CC BY 4.0', 'cc-by'),
                                        ('NASA (no US copyright)', 'pd'),
                                        ('public domain; source states: "Copyright Status: Public Domain"', 'pd')])
def test_licence_notes_read_the_claim_and_catch_restrictions(note, code):
    assert layers._licence(note)['code'] == code


def test_design_system_images_are_never_publishable(starter_home, tmp_path, monkeypatch):
    root = _system(tmp_path, ['tea-cc0,window,tea;garden,light,muted,painting,Tea garden,A,1800,CC0 (Met),A,'
                              'https://x,,tea,300x200',
                              'tea-nc,window,tea;garden,light,muted,painting,Tea house,B,1800,CC BY-NC 4.0,B,'
                              'https://x,,tea,300x200'])
    monkeypatch.setenv('VISUAL_ATLAS_DESIGN_SYSTEMS', str(root))
    monkeypatch.setattr(layers, 'GENERATED', tmp_path / 'none')
    everything = {r['ref']: r for r in desk.search(brief='tea garden', home=starter_home)['results']}
    assert 'Restricted' in everything['system:garden-of-lingering:tea-nc']['licence']['label']
    published = desk.search(brief='tea garden', publishable_only=True, home=starter_home)['results']
    assert all(r['layer'] == 'library' for r in published)


def test_desk_never_creates_or_migrates_a_library(tmp_path, monkeypatch):
    monkeypatch.delenv('VISUAL_ATLAS_DESIGN_SYSTEMS', raising=False)
    monkeypatch.setattr(layers, 'GENERATED', tmp_path / 'none')
    empty = tmp_path / 'empty-home'
    assert desk.search(techniques=['silhouette'], home=empty)['results'] == []
    assert desk.route('tea house', empty)['collections'] == []
    assert not (empty / 'atlas.db').exists()
    old = tmp_path / 'old-home'
    old.mkdir()
    connection = sqlite3.connect(old / 'atlas.db')
    connection.execute('PRAGMA user_version=1')
    connection.close()
    before = (old / 'atlas.db').read_bytes()
    with pytest.raises(ValueError, match='another version'):
        desk.search(techniques=['silhouette'], home=old)
    assert (old / 'atlas.db').read_bytes() == before and not list(old.glob('*.bak'))


def test_a_file_swapped_after_indexing_is_not_served(tmp_path, monkeypatch):
    folder = tmp_path / 'generated'
    folder.mkdir()
    Image.new('RGB', (100, 100)).save(folder / 'g-01.jpg', 'JPEG')
    (folder / 'manifest.json').write_text(json.dumps({'images': [
        {'id': 'g-01', 'file': 'g-01.jpg', 'title': 't', 'tool': 'x', 'date': 'd', 'prompt': 'p'}]}), encoding='utf-8')
    monkeypatch.setattr(layers, 'GENERATED', folder)
    assert layers.find('generated:g-01')  # indexed and cached
    secret = tmp_path / 'secret.txt'
    secret.write_text('private', encoding='utf-8')
    (folder / 'g-01.jpg').unlink()
    assert layers.find('generated:g-01') is None  # gone since indexing: checked at access time
    try:
        os.symlink(secret, folder / 'g-01.jpg')
    except OSError:
        pytest.skip('this account cannot create symbolic links')
    assert layers.find('generated:g-01') is None


def test_guard_reads_what_would_be_committed_not_the_working_file(tmp_path):
    library = tmp_path / 'private' / 'assets' / 'library'
    library.mkdir(parents=True)
    Image.new('RGB', (64, 64), (200, 30, 30)).save(library / 'secret.jpg', 'JPEG')
    repo = tmp_path / 'repo'
    repo.mkdir()
    git = ['git', '-c', 'user.email=t@example.invalid', '-c', 'user.name=t']
    subprocess.run([*git, 'init', '-q'], cwd=repo, check=True)
    shutil.copy(library / 'secret.jpg', repo / 'notes.txt')  # renamed and re-extensioned
    subprocess.run([*git, 'add', 'notes.txt'], cwd=repo, check=True)
    (repo / 'notes.txt').write_text('harmless now', encoding='utf-8')  # the working copy no longer matches
    assert check_no_data.design_system_copies(repo, [library]) == ['notes.txt']


def test_mcp_session_survives_hostile_frames():
    lines = ['[' * 200000, '{"a": ' + '1' * 5000 + '}', json.dumps({'jsonrpc': '2.0', 'id': 7, 'method': 'ping'})]
    out = io.StringIO()
    mcp_server.serve(io.StringIO('\n'.join(lines) + '\n'), out)
    replies = [json.loads(line) for line in out.getvalue().splitlines()]
    assert replies[-1] == {'jsonrpc': '2.0', 'id': 7, 'result': {}}
    assert replies[0]['error']['code'] in (-32700, -32600)


def test_goal_reasons_quote_one_technique_with_its_own_state(starter_home, monkeypatch, tmp_path):
    monkeypatch.delenv('VISUAL_ATLAS_DESIGN_SYSTEMS', raising=False)
    monkeypatch.setattr(layers, 'GENERATED', tmp_path / 'none')
    results = desk.search(goals=['create-calm'], limit=20, home=starter_home)['results']
    reasons = [reason for r in results for reason in r['reasons'] if reason.startswith('Serves')]
    assert reasons
    for reason in reasons:
        assert re.match(r'Serves “[^”]+” through [^,(]+ \(', reason), reason
