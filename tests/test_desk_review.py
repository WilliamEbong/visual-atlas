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


# ---- round 2 -------------------------------------------------------------------------------------------------


def test_restricted_library_codes_are_never_publishable(starter_home, tmp_path, monkeypatch):
    home = tmp_path / 'copy'
    shutil.copytree(starter_home, home)
    monkeypatch.delenv('VISUAL_ATLAS_DESIGN_SYSTEMS', raising=False)
    monkeypatch.setattr(layers, 'GENERATED', tmp_path / 'none')
    target = desk.search(techniques=['silhouette'], publishable_only=True, home=home)['results'][0]['image_id']
    connection = sqlite3.connect(home / 'atlas.db')
    columns = [row[1] for row in connection.execute('PRAGMA table_info(rights_records)') if row[1] != 'id']
    copied = ', '.join("'CC-BY-NC'" if c == 'license_code' else "'Noncommercial only'" if c == 'label' else c
                       for c in columns)
    connection.execute(f"INSERT INTO rights_records({', '.join(columns)}) SELECT {copied} FROM rights_records "
                       "WHERE image_id=? ORDER BY id DESC LIMIT 1", (target,))
    connection.commit()
    connection.close()
    published = desk.search(techniques=['silhouette'], publishable_only=True, limit=40, home=home)['results']
    assert target not in {r.get('image_id') for r in published}


def test_custom_folder_names_give_refs_that_open(starter_home, tmp_path, monkeypatch):
    root = _system(tmp_path, ['tea-1,window,tea;garden,light,muted,painting,Tea garden,A,1800,CC0,A,https://x,,tea,'
                              '300x200'])
    custom = root.with_name('Studio References')
    root.rename(custom)
    monkeypatch.setenv('VISUAL_ATLAS_DESIGN_SYSTEMS', str(custom))
    monkeypatch.setattr(layers, 'GENERATED', tmp_path / 'none')
    found = desk.search(brief='tea garden', home=starter_home)['results']
    ref = next(r['ref'] for r in found if r['layer'] == 'design-system')
    assert ref == 'system:studio-references:tea-1'
    assert desk.get(ref, home=starter_home)['title'] == 'Tea garden'


def test_guard_covers_folders_configured_in_the_home_env_file(tmp_path, monkeypatch):
    home = tmp_path / 'home'
    home.mkdir()
    root = _system(tmp_path, ['a-1,window,tea,light,muted,painting,T,A,1800,CC0,A,https://x,,n,300x200'])
    (home / '.env').write_text(f'VISUAL_ATLAS_DESIGN_SYSTEMS={root}\n', encoding='utf-8')
    monkeypatch.setenv('VISUAL_ATLAS_HOME', str(home))
    monkeypatch.delenv('VISUAL_ATLAS_DESIGN_SYSTEMS', raising=False)
    assert root / 'assets' / 'library' in check_no_data.libraries()


def test_mcp_discards_an_oversized_frame_and_answers_the_next(monkeypatch):
    monkeypatch.setattr(mcp_server, 'MAX_FRAME', 100)

    class Bounded(io.StringIO):  # every read must be bounded; reading a whole line at once is the defect
        def readline(self, size=-1):
            assert 0 < size <= 101
            return super().readline(size)

        def __iter__(self):
            raise AssertionError('unbounded line iteration')

    out = io.StringIO()
    ping = json.dumps({'jsonrpc': '2.0', 'id': 8, 'method': 'ping'})
    mcp_server.serve(Bounded('x' * 1000 + '\n' + ping + '\n'), out)
    replies = [json.loads(line) for line in out.getvalue().splitlines()]
    assert replies == [{'jsonrpc': '2.0', 'id': None, 'error': {'code': -32700, 'message': 'Parse error'}},
                       {'jsonrpc': '2.0', 'id': 8, 'result': {}}]


# ---- round 3 (overnight round 2) -----------------------------------------------------------------------------


def test_two_folders_with_the_same_slug_keep_separate_refs(starter_home, tmp_path, monkeypatch):
    first = _system(tmp_path / 'a', ['tea-1,window,tea;garden,light,muted,painting,First tea,A,1800,CC0,A,https://x,,'
                                     'tea,300x200'])
    second = _system(tmp_path / 'b', ['tea-1,window,tea;garden,light,muted,painting,Second tea,A,1800,CC0,A,https://x,,'
                                      'tea,300x200'])
    monkeypatch.setenv('VISUAL_ATLAS_DESIGN_SYSTEMS', f'{first};{second}')
    monkeypatch.setattr(layers, 'GENERATED', tmp_path / 'none')
    refs = [r['ref'] for r in desk.search(brief='tea garden', home=starter_home)['results'] if r['layer'] == 'design-system']
    assert len(refs) == len(set(refs)) == 2
    assert {desk.get(ref, home=starter_home)['title'] for ref in refs} == {'First tea', 'Second tea'}


def test_every_generated_file_carries_its_provenance_label():
    manifest = json.loads((REPO / 'generated' / 'manifest.json').read_text(encoding='utf-8'))
    for item in manifest['images']:
        xmp = Image.open(REPO / 'generated' / item['file']).info.get('xmp', b'')
        assert b'digitalsourcetype/trainedAlgorithmicMedia' in xmp, item['file']
        assert item['id'].encode() in xmp


def test_more_like_this_ranks_the_closest_composition_first(tmp_path, monkeypatch):
    folder = tmp_path / 'generated'
    folder.mkdir()
    pictures = {'red-left': [(200, 30, 30), (240, 240, 240)], 'red-left-copy': [(190, 40, 35), (235, 235, 230)],
                'blue-right': [(240, 240, 240), (30, 30, 200)]}
    items = []
    for name, (left, right) in pictures.items():
        picture = Image.new('RGB', (200, 100), right)
        picture.paste(Image.new('RGB', (100, 100), left), (0, 0))
        picture.save(folder / f'{name}.jpg', 'JPEG')
        items.append({'id': name, 'file': f'{name}.jpg', 'title': name, 'tool': 'x', 'date': 'd', 'prompt': 'p'})
    (folder / 'manifest.json').write_text(json.dumps({'images': items}), encoding='utf-8')
    monkeypatch.setattr(layers, 'GENERATED', folder)
    monkeypatch.setattr(desk, 'SIGNATURES', tmp_path / 'cache')
    monkeypatch.delenv('VISUAL_ATLAS_DESIGN_SYSTEMS', raising=False)
    found = desk.similar('generated:red-left', layers_wanted=['generated'], home=tmp_path / 'home')
    assert [r['ref'] for r in found['results']] == ['generated:red-left-copy', 'generated:blue-right']
    assert found['results'][0]['score'] > 0.9 > found['results'][1]['score']
    cache = list((tmp_path / 'cache').glob('signatures-*.json'))
    assert len(cache) == 1 and not (tmp_path / 'home').exists()
    assert 'red-left' not in cache[0].read_text(encoding='utf-8')  # opaque keys: no file names or paths
    (folder / 'blue-right.jpg').unlink()  # a full pass forgets pictures that are gone
    desk.similar('generated:red-left', home=tmp_path / 'home')
    assert len(json.loads(cache[0].read_text(encoding='utf-8'))) == 2


def test_open_search_returns_only_rights_checked_candidates(monkeypatch):
    from atlas import providers
    found = [{'provider': 'aic', 'title': 'Lighthouse', 'creator': 'A', 'date_text': '1900', 'medium': 'oil',
              'source_url': 'https://www.artic.edu/artworks/1', 'image_url': 'https://www.artic.edu/iiif/2/x/full/843,/0/default.jpg',
              'image_headers': {}, 'credit_line': '', 'raw': {'is_public_domain': True, 'image_id': 'x'}},
             {'provider': 'aic', 'title': 'Modern', 'creator': 'B', 'date_text': '1990', 'medium': 'oil',
              'source_url': 'https://www.artic.edu/artworks/2', 'image_url': '', 'image_headers': {}, 'credit_line': '',
              'raw': {'is_public_domain': False, 'image_id': None}}]
    calls = []

    def fake(fetcher, provider, query, page, per_page, home=None):
        calls.append((provider, query, per_page))
        return found
    monkeypatch.setattr(providers, 'search', fake)
    result = desk.open_search('lighthouse at night', providers_wanted=['aic'], per_provider=3, fetcher=object())
    assert calls == [('aic', 'lighthouse at night', 3)]
    assert [r['title'] for r in result['results']] == ['Lighthouse'] and result['results'][0]['publishable']
    assert result['results'][0]['licence']['checked_by'] == 'atlas/rights.py' and sum(result['rejected'].values()) == 1
    for bad in ({'query': ''}, {'query': 'x' * 201}, {'query': 'x', 'providers_wanted': ['nga']},
                {'query': 'x', 'per_provider': 11}):
        with pytest.raises(ValueError):
            desk.open_search(**bad, fetcher=object())



# ---- Codex review, overnight round 2 ------------------------------------------------------------------------------


def test_open_search_never_widens_an_empty_selection(monkeypatch):
    from atlas import providers
    calls = []
    monkeypatch.setattr(providers, 'search', lambda *a, **k: calls.append(a) or [])
    for empty in ([], [''], ['  ']):
        with pytest.raises(ValueError, match='at least one collection'):
            desk.open_search('lighthouse', providers_wanted=empty, fetcher=object())
    assert calls == []
    assert mcp_server.call('search_open_collections', {'query': 'x', 'collections': []})['isError'] is True


def test_open_searches_share_one_fetcher_so_cooldowns_carry_over(monkeypatch):
    from atlas import providers
    seen = []
    monkeypatch.setattr(providers, 'search', lambda fetcher, *a, **k: seen.append(fetcher) or [])
    desk.open_search('a', providers_wanted=['met'])
    desk.open_search('b', providers_wanted=['met'])
    assert len(seen) == 2 and seen[0] is seen[1]


def test_long_colliding_system_names_still_give_refs_that_open(starter_home, tmp_path, monkeypatch):
    long = 'x' * 70
    first = _system(tmp_path / 'a', ['tea-1,window,tea,light,muted,painting,First,A,1800,CC0,A,https://x,,tea,300x200'])
    second = _system(tmp_path / 'b', ['tea-1,window,tea,light,muted,painting,Second,A,1800,CC0,A,https://x,,tea,300x200'])
    first, second = first.rename(first.with_name(long)), second.rename(second.with_name(long))
    monkeypatch.setenv('VISUAL_ATLAS_DESIGN_SYSTEMS', f'{first};{second}')
    monkeypatch.setattr(layers, 'GENERATED', tmp_path / 'none')
    refs = [r['ref'] for r in desk.search(brief='tea', home=starter_home)['results'] if r['layer'] == 'design-system']
    assert len(set(refs)) == 2
    assert {desk.get(ref, home=starter_home)['title'] for ref in refs} == {'First', 'Second'}


def test_library_only_directions_do_not_route_to_private_systems(starter_home, tmp_path, monkeypatch):
    root = _system(tmp_path, ['tea-1,window,tea;garden,light,muted,painting,Tea,A,1800,CC0,A,https://x,,tea,300x200'])
    monkeypatch.setenv('VISUAL_ATLAS_DESIGN_SYSTEMS', str(root))
    monkeypatch.setattr(layers, 'GENERATED', tmp_path / 'none')
    assert desk.search(brief='tea garden calm', home=starter_home)['route']['system']  # routed when allowed
    scoped = desk.directions('tea garden calm', goals=['create-calm'], layers_wanted=['library'], home=starter_home)
    assert scoped['route']['system'] is None and scoped['directions']
