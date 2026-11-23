"""Reference layers that live outside the library database, read in place and never written to.

* generated: original images made for Visual Atlas with Codex image generation. They ship in the repository
  (`generated/manifest.json`), each with its prompt, the works studied for craft, the date and its review against
  `generated/RUBRIC.md`. They are labelled as generated everywhere and never pass through atlas/rights.py.
* design systems: the owner's private style libraries (Claude skill folders with `references/images.csv` and
  `assets/library/<id>.jpg`). Opt-in through VISUAL_ATLAS_DESIGN_SYSTEMS; indexed where they sit, never copied into
  the library or the repository. On any other machine the setting is absent and the layer is empty.
"""

import csv
import json
import os
import re
from functools import lru_cache
from pathlib import Path

from atlas.home import REPO, local_setting

GENERATED = REPO / 'generated'
SKILLS = Path.home() / '.claude' / 'skills'
SYSTEM_NAMES = ('archive-of-looking', 'garden-of-lingering', 'citadel-of-watching', 'harbour-of-drifting')
ID = re.compile(r'^[a-z0-9][a-z0-9-]{0,80}$')


def _split(value: str) -> list[str]:
    return [part.strip() for part in (value or '').split(';') if part.strip()]


def _licence(text: str) -> dict:
    """Plain words for a design-system row's own licence note. The row's note is kept verbatim as evidence."""
    lowered = text.split(';')[0].lower()  # the claim itself; quoted source evidence follows the ';'
    # "no US copyright" (NASA) is a public-domain statement, not a restriction.
    restricted = re.search(r'\b(nc|nd|sa|non-?commercial|no ?deriv\w*|share ?alike|not in the public domain|'
                           r'all rights reserved)\b|(?<!no us )\bcopyright(ed)?\b', lowered)
    if restricted and not lowered.startswith('original image generated'):
        label, code = 'Restricted or unclear licence: check the source', 'unclear'
    elif lowered.startswith('original image generated'):
        label, code = 'Generated image (owner\'s design system)', 'generated'
    elif lowered.startswith('cc0'):
        label, code = 'CC0 (per the design system catalogue)', 'cc0'
    elif lowered.startswith('cc by'):
        label, code = f'{text.split(";")[0].split("(")[0].strip()} (per the design system catalogue)', 'cc-by'
    elif 'public domain' in lowered or lowered.startswith('nasa'):
        label, code = 'Public domain (per the design system catalogue)', 'pd'
    else:
        label, code = 'Licence unclear: check the source', 'unclear'
    return {'label': label, 'code': code, 'note': text, 'checked_by': 'design system catalogue, not atlas/rights.py'}


def system_root(name: str) -> Path:
    return SKILLS / name


def enabled_systems(home: Path | None = None) -> list[Path]:
    """VISUAL_ATLAS_DESIGN_SYSTEMS: 'auto' (the four known skill folders) or a ';'-separated list of folders."""
    value = (local_setting('VISUAL_ATLAS_DESIGN_SYSTEMS', home) or '').strip()
    if not value or value.lower() in ('0', 'off', 'no', 'false'):
        return []
    folders = [system_root(name) for name in SYSTEM_NAMES] if value.lower() == 'auto' else \
        [Path(part.strip()) for part in value.split(';') if part.strip()]
    return [folder for folder in folders if (folder / 'references' / 'images.csv').is_file()]


def _description(folder: Path) -> str:
    """The skill's own description (front matter), used by the router to pick a system for a brief."""
    try:
        text = (folder / 'SKILL.md').read_text(encoding='utf-8')
    except OSError:
        return ''
    match = re.search(r'^description:\s*>?-?\s*\n?(.*?)\n---', text, re.S | re.M)
    return ' '.join((match.group(1) if match else '').split())


@lru_cache(maxsize=8)
def _read_system(folder: Path, mtime: float) -> dict:
    del mtime  # part of the cache key: an edited catalogue is read again
    name = re.sub(r'[^a-z0-9]+', '-', folder.name.lower()).strip('-')[:60] or 'system'  # always a valid ref part
    library = (folder / 'assets' / 'library').resolve()
    refs = []
    with open(folder / 'references' / 'images.csv', encoding='utf-8', newline='') as handle:
        for row in csv.DictReader(handle):
            rid = (row.get('id') or '').strip()
            if not ID.match(rid):
                continue
            path = (library / f'{rid}.jpg').resolve()
            if not path.is_relative_to(library) or not path.is_file():
                continue
            width, _, height = (row.get('size') or '').partition('x')
            licence = _licence(row.get('licence', ''))
            refs.append({
                'ref': f'system:{name}:{rid}', 'layer': 'design-system', 'system': name, 'title': row.get('title', ''),
                'creator': row.get('creator', ''), 'date': row.get('date', ''), 'medium': row.get('medium', ''),
                'subjects': _split(row.get('subjects', '')), 'slots': _split(row.get('slots', '')),
                'colour': row.get('colour', ''), 'ground': row.get('ground', ''), 'notes': row.get('notes', ''),
                'width': int(width) if width.isdigit() else None, 'height': int(height) if height.isdigit() else None,
                'licence': licence, 'credit': row.get('credit', ''), 'source_url': row.get('page', ''),
                'generated': licence['code'] == 'generated', 'techniques': [], 'file': str(path),
                'root': str(library)})
    return {'name': name, 'description': _description(folder), 'references': refs}


def systems(home: Path | None = None) -> list[dict]:
    out = []
    for folder in enabled_systems(home):
        try:
            system = _read_system(folder, os.path.getmtime(folder / 'references' / 'images.csv'))
        except (OSError, csv.Error, UnicodeDecodeError):
            continue  # an unreadable catalogue leaves that system out; the rest still answer
        taken = {s['name'] for s in out}
        if system['name'] in taken:  # two folders whose names slug alike: number the later one, in setting order
            name = next(f"{system['name']}-{n}" for n in range(2, 100) if f"{system['name']}-{n}" not in taken)
            refs = [{**r, 'system': name, 'ref': f"system:{name}:{r['ref'].rsplit(':', 1)[1]}"}
                    for r in system['references']]
            system = {**system, 'name': name, 'references': refs}
        out.append(system)
    return out


@lru_cache(maxsize=4)
def _read_generated(path: Path, mtime: float) -> list[dict]:
    del mtime
    data = json.loads(path.read_text(encoding='utf-8'))
    root = path.parent.resolve()
    refs = []
    for item in data.get('images', []):
        rid = item.get('id', '')
        file = (root / item.get('file', '')).resolve()
        if not ID.match(rid) or not file.is_relative_to(root) or not file.is_file():
            continue
        refs.append({
            'ref': f'generated:{rid}', 'layer': 'generated', 'title': item['title'], 'creator': item['tool'],
            'date': item['date'], 'medium': item.get('medium', 'generated image'), 'subjects': item.get('subjects', []),
            'techniques': [{'id': t, 'state': 'intended'} for t in item.get('techniques', [])],
            'colour': item.get('colour', ''), 'notes': item.get('notes', ''), 'width': item.get('width'),
            'height': item.get('height'), 'generated': True, 'prompt': item['prompt'],
            'studied': item.get('studied', []), 'review': item.get('review', {}),
            'licence': {'label': 'Generated image: no licence asserted', 'code': 'generated',
                        'note': data.get('licence_note', ''), 'checked_by': 'not a rights decision'},
            'credit': f"Generated for Visual Atlas with {item['tool']} on {item['date']}", 'source_url': '',
            'file': str(file), 'root': str(root)})
    return refs


def generated(path: Path | None = None) -> list[dict]:
    path = path or GENERATED / 'manifest.json'
    try:
        return _read_generated(path, os.path.getmtime(path))
    except (OSError, ValueError, KeyError, TypeError):
        return []


def safe_file(record: dict) -> Path | None:
    """The record's file, checked again at access time: still a regular file inside its layer folder. The index is
    cached, so a file swapped for a link after indexing must not lead outside the folder."""
    try:
        path = Path(record['file'])
        resolved = path.resolve(strict=True)
        if path.is_symlink() or not resolved.is_relative_to(Path(record['root'])) or not resolved.is_file():
            return None
        return resolved
    except (OSError, KeyError, RuntimeError):
        return None


def find(ref: str, home: Path | None = None) -> dict | None:
    """One layer reference by its ref string, or None. Only indexed files that are still in place are returned."""
    found = None
    if ref.startswith('generated:'):
        found = next((r for r in generated() if r['ref'] == ref), None)
    elif ref.startswith('system:'):
        found = next((r for system in systems(home) for r in system['references'] if r['ref'] == ref), None)
    return found if found and safe_file(found) else None
