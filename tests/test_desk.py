"""Reference desk, layers and the design-system commit guard. Offline: the real starter pack, temp homes only."""

import importlib.util
import json
import shutil
from pathlib import Path

import pytest
from PIL import Image

from atlas import desk, jobs, layers, transfer
from atlas.home import REPO

GUARD = importlib.util.spec_from_file_location('check_no_data', REPO / 'scripts' / 'check_no_data.py')
check_no_data = importlib.util.module_from_spec(GUARD)
GUARD.loader.exec_module(check_no_data)


@pytest.fixture(scope='module')
def starter_home(tmp_path_factory):
    home = tmp_path_factory.mktemp('desk') / 'home'
    with jobs.open_store(home) as store:
        assert transfer.import_starter(store, home, REPO / 'starter') == 102
    return home


@pytest.fixture
def no_extra_layers(monkeypatch, tmp_path):
    monkeypatch.setattr(layers, 'GENERATED', tmp_path / 'no-generated')
    monkeypatch.delenv('VISUAL_ATLAS_DESIGN_SYSTEMS', raising=False)
    monkeypatch.setenv('VISUAL_ATLAS_HOME', str(tmp_path / 'unused-home'))  # .env lookups never reach a real home


def _jpeg(path: Path, size=(400, 300), colour=(120, 90, 60)):
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new('RGB', size, colour).save(path, 'JPEG')


@pytest.fixture
def fake_system(tmp_path):
    """A design-system skill folder shaped like the owner's: SKILL.md, references/images.csv, assets/library."""
    root = tmp_path / 'skills' / 'harbour-of-drifting'
    (root / 'references').mkdir(parents=True)
    (root / 'SKILL.md').write_text('---\nname: harbour-of-drifting\ndescription: >-\n  Retro anime cyberpunk harbour '
                                   'megacity at night for game studios. Not for science or data.\n---\n# x\n',
                                   encoding='utf-8')
    rows = ['id,slots,subjects,ground,colour,medium,title,creator,date,licence,credit,page,image,notes,size',
            'gen-canal-dusk,cel,night;city;canal,dark,muted,painted background,Canal at dusk,Codex,2026-10-05,'
            'original image generated for William,Generated,prompt.txt,,lamps on water,1600x900',
            'nasa-earth,letterbox,earth;night,dark,vivid,space photograph,Night Earth,NASA,2012,'
            'Public domain (NASA),NASA,https://images.nasa.gov/x,,limb 58%,900x1600',
            '../escape,cel,night,dark,muted,painting,Bad id,x,1900,CC0,x,x,,x,10x10',
            'missing-file,cel,night,dark,muted,painting,No file,x,1900,CC0,x,x,,x,10x10']
    (root / 'references' / 'images.csv').write_text('\n'.join(rows) + '\n', encoding='utf-8')
    _jpeg(root / 'assets' / 'library' / 'gen-canal-dusk.jpg', (640, 360))
    _jpeg(root / 'assets' / 'library' / 'nasa-earth.jpg', (360, 640), (10, 20, 40))
    _jpeg(root / 'assets' / 'escape.jpg')
    return root


@pytest.fixture
def fake_generated(tmp_path, monkeypatch):
    folder = tmp_path / 'generated'
    _jpeg(folder / 'fg-01.jpg', (500, 500))
    manifest = {'version': 1, 'licence_note': 'no licence asserted', 'images': [
        {'id': 'fg-01', 'file': 'fg-01.jpg', 'title': 'Vase or faces', 'tool': 'Codex image generation',
         'date': '2026-11-22', 'subjects': ['vase', 'profile'], 'techniques': ['figure-ground-ambiguity'],
         'width': 500, 'height': 500, 'prompt': 'p', 'studied': [], 'review': {'result': 'pass'}},
        {'id': 'outside', 'file': '../outside.jpg', 'title': 'x', 'tool': 't', 'date': 'd', 'prompt': 'p'}],
        'dropped': []}
    _jpeg(tmp_path / 'outside.jpg')
    (folder / 'manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
    monkeypatch.setattr(layers, 'GENERATED', folder)
    return folder


def test_advise_reads_the_brief_and_gives_reasoned_credited_references(starter_home, no_extra_layers):
    result = desk.advise('make one thing stand out with lots of empty space around a small figure',
                         limit=5, home=starter_home)
    assert {'draw-attention'} <= {g['id'] for g in result['reading']['goals']}
    assert 'negative-space' in {t['id'] for t in result['reading']['techniques']}
    assert result['guidance'][0]['look_for'] and result['guidance'][0]['not_to_confuse_with']
    assert 1 <= len(result['results']) <= 5
    for ref in result['results']:
        assert ref['layer'] == 'library' and ref['reasons'] and ref['licence']['label']
        assert ref['licence']['checked_by'] == 'atlas/rights.py' and ref['credit']
        assert Path(ref['file']).is_file()
    scores = [r['score'] for r in result['results']]
    assert scores == sorted(scores, reverse=True)


def test_explicit_technique_returns_only_references_that_show_it(starter_home, no_extra_layers):
    result = desk.search(techniques=['silhouette'], limit=20, home=starter_home)
    assert result['results'] and result['total_matches'] == len(result['results'])
    for ref in result['results']:
        assert 'silhouette' in {t['id'] for t in ref['techniques']}
        assert ref['reasons'][0].startswith('Shows Silhouette (')


def test_unknown_words_return_nothing_rather_than_padding(starter_home, no_extra_layers):
    result = desk.advise('zzqx wvvq', home=starter_home)
    assert result['results'] == [] and result['guidance'] == []
    assert 'matched no goal or technique' in result['next_steps'][0] and result['codebook']['goals']


@pytest.mark.parametrize('kwargs, message', [
    ({'techniques': ['not-a-technique']}, 'unknown technique'), ({'limit': 0}, 'limit'), ({'limit': 41}, 'limit'),
    ({'layers_wanted': ['web']}, 'layers'), ({'brief': 'x' * 4001}, 'brief'), ({'orientation': 'tall'}, 'orientation'),
    ({'techniques': ['a'] * 13}, 'at most'), ({'subjects': [3]}, 'text'), ({'colour': 'x' * 81}, 'colour')])
def test_inputs_are_validated(starter_home, no_extra_layers, kwargs, message):
    with pytest.raises(ValueError, match=message):
        desk.search(home=starter_home, **kwargs)


@pytest.mark.parametrize('ref', ['library:abc', '../etc/passwd', 'system:../x:y', 'generated:A B', 'C:\\x.jpg'])
def test_refs_are_ids_never_paths(starter_home, ref):
    with pytest.raises(ValueError):
        desk.get(ref, home=starter_home)


def test_missing_refs_are_lookup_errors(starter_home, no_extra_layers):
    for ref in ('library:999999', 'generated:nope', 'system:archive-of-looking:nope'):
        with pytest.raises(LookupError):
            desk.get(ref, home=starter_home)


def test_get_returns_evidence_and_review_state(starter_home, no_extra_layers):
    first = desk.search(techniques=['negative-space'], limit=1, home=starter_home)['results'][0]
    full = desk.get(first['ref'], home=starter_home)
    note = next(t for t in full['techniques'] if t['id'] == 'negative-space')
    assert note['evidence'] and note['effect'] and note['state_means']


def test_generated_layer_is_labelled_and_never_publishable(starter_home, fake_generated, monkeypatch):
    monkeypatch.delenv('VISUAL_ATLAS_DESIGN_SYSTEMS', raising=False)
    result = desk.search(techniques=['figure-ground-ambiguity'], limit=10, home=starter_home)
    generated = [r for r in result['results'] if r['layer'] == 'generated']
    assert [r['ref'] for r in generated] == ['generated:fg-01']  # the entry pointing outside its folder is ignored
    assert generated[0]['generated'] and 'no licence' in generated[0]['licence']['label'].lower()
    assert 'intended by the prompt' in generated[0]['reasons'][0]
    publishable = desk.search(techniques=['figure-ground-ambiguity'], limit=10, publishable_only=True, home=starter_home)
    assert all(r['layer'] == 'library' for r in publishable['results'])


def test_design_systems_are_opt_in_and_read_in_place(starter_home, fake_system, no_extra_layers, monkeypatch):
    brief = 'cyberpunk harbour city at night for a game studio'
    assert not [r for r in desk.search(brief=brief, home=starter_home)['results'] if r['layer'] == 'design-system']
    monkeypatch.setenv('VISUAL_ATLAS_DESIGN_SYSTEMS', str(fake_system))
    before = sorted(p.relative_to(fake_system) for p in fake_system.rglob('*'))
    result = desk.search(brief=brief, home=starter_home)
    assert result['route']['system']['name'] == 'harbour-of-drifting'
    found = {r['ref']: r for r in result['results'] if r['layer'] == 'design-system'}
    assert set(found) == {'system:harbour-of-drifting:gen-canal-dusk', 'system:harbour-of-drifting:nasa-earth'}
    canal = found['system:harbour-of-drifting:gen-canal-dusk']
    assert canal['generated'] and canal['licence']['code'] == 'generated'
    assert Path(canal['file']).parent == fake_system / 'assets' / 'library'
    assert found['system:harbour-of-drifting:nasa-earth']['orientation'] == 'portrait'
    assert sorted(p.relative_to(fake_system) for p in fake_system.rglob('*')) == before  # nothing written
    publish = desk.search(brief=brief, publishable_only=True, home=starter_home)['results']
    assert 'system:harbour-of-drifting:gen-canal-dusk' not in {r['ref'] for r in publish}


def test_router_falls_back_to_the_owners_default(starter_home, fake_system, no_extra_layers, monkeypatch, tmp_path):
    archive = tmp_path / 'skills' / 'archive-of-looking'
    shutil.copytree(fake_system, archive)
    (archive / 'SKILL.md').write_text('---\ndescription: >-\n  Archival scientific modernism plates.\n---\n',
                                      encoding='utf-8')
    monkeypatch.setenv('VISUAL_ATLAS_DESIGN_SYSTEMS', f'{fake_system};{archive}')
    assert desk.route('quarterly budget review', starter_home)['system']['name'] == 'archive-of-looking'
    assert desk.route('cyberpunk game night', starter_home)['system']['name'] == 'harbour-of-drifting'


def test_design_system_paths_cannot_be_committed():
    for path in ('archive-of-looking/assets/library/a.jpg', 'x/assets/library/b.jpg', 'x/references/images.csv',
                 'harbour-of-drifting.skill', 'docs/garden-of-lingering/notes.md'):
        assert check_no_data.forbidden(path), path
    assert not check_no_data.forbidden('generated/fg-01.jpg')  # copies by content: test_desk_review.py


def test_gitignore_keeps_design_system_folders_out():
    ignore = (REPO / '.gitignore').read_text(encoding='utf-8')
    for pattern in ('**/assets/library/', '**/references/images.csv', '*.skill', 'archive-of-looking/'):
        assert pattern in ignore
