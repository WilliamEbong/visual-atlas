"""The reference desk: a design brief in, ranked references with reasons and technique guidance out. No AI.

One deterministic engine behind the CLI (`atlas refs`, `atlas advise`), the MCP server (atlas/mcp.py) and the
web app (/api/desk). It reads three layers and labels each result with the layer it came from:
  library        images in the user's library, licence-checked by atlas/rights.py, with model or human readings;
  generated      original images made for Visual Atlas (atlas/layers.py), labelled generated, no licence asserted;
  design-system  the owner's private style libraries, opt-in, on his machine only (atlas/layers.py).
Every reason is built from stored data (an annotation, a subject word, a metric), so it can be checked.
"""

import json
import re
from pathlib import Path

from atlas import catalog, coding, jobs, layers
from atlas.home import home_dir

LAYERS = ('library', 'generated', 'design-system')
STATE_WEIGHT = {'human_reviewed': 3.0, 'model_reviewed': 2.0, 'proposed': 1.0, 'intended': 1.0}
STATE_WORDS = {'human_reviewed': 'confirmed by a person', 'model_reviewed': 'agreed by a second model',
               'proposed': 'proposed by a model, not yet checked', 'intended': 'intended by the prompt, checked by eye'}
PUBLISHABLE = {'cc0', 'pd', 'cc-by'}  # licence codes with a documented free licence (generated and unclear are not)
ORIENTATIONS = ('portrait', 'landscape', 'square')
MAX_TEXT = 4000
# Format and occasion words say what is being made, not what the picture shows (they still route design systems).
FORMAT_WORDS = {'deck', 'pitch', 'keynote', 'studio', 'launch', 'brand', 'client', 'opener', 'reel', 'thumbnail'}
VARIANT = re.compile(r'-\d+x\d+$')  # the same picture cropped for another format (gen-x-4x5)


def _year(text: str) -> int | None:
    match = re.search(r'\b(\d{3,4})\b', text or '')
    if match:
        return int(match.group(1))
    match = re.search(r'\b(\d{1,2})(?:st|nd|rd|th)\s*c', text or '')
    return (int(match.group(1)) - 1) * 100 + 50 if match else None


def _orientation(width, height) -> str:
    if not width or not height:
        return ''
    ratio = width / height
    return 'square' if 0.9 <= ratio <= 1.1 else 'landscape' if ratio > 1 else 'portrait'


def _library(home: Path) -> list[dict]:
    """Every ready library image as a reference record (one pass; fine for thousands of images)."""
    with jobs.open_store(home) as store, store.reading():
        images = store.rows(
            "SELECT i.id, i.title, i.creator, i.date_text, i.medium, i.description, i.provider, i.source_url, i.width, "
            "i.height, i.original_path, i.analysis_path, i.thumb_path, a.result_json, m.color_family, m.palette_json, "
            "m.orientation, (SELECT json_object('code', r.license_code, 'version', r.license_version, 'label', r.label, "
            "'url', r.license_url, 'attribution', r.required_attribution, 'restrictions', r.restrictions) FROM "
            "rights_records r WHERE r.image_id=i.id ORDER BY r.id DESC LIMIT 1) AS rights FROM images i "
            "LEFT JOIN analyses a ON a.id=i.analysis_id LEFT JOIN image_metrics m ON m.image_id=i.id "
            "WHERE i.removed_at IS NULL AND i.status='ready'")
        notes = {}
        for row in store.rows("SELECT image_id, technique_id, state, role, evidence_json, effect FROM annotations "
                              "WHERE state!='rejected' ORDER BY role='primary' DESC, confidence DESC"):
            notes.setdefault(row['image_id'], []).append(
                {'id': row['technique_id'], 'state': row['state'], 'role': row['role'],
                 'evidence': json.loads(row['evidence_json'])[:2], 'effect': row['effect']})
    media = home / 'media'
    out = []
    for row in images:
        result = json.loads(row['result_json']) if row['result_json'] else {}
        rights = json.loads(row['rights']) if row['rights'] else {}
        code = (rights.get('code') or '').lower()
        code = 'cc0' if code == 'cc0' else 'pd' if code in ('pd', 'pdm', 'public-domain') else \
            'cc-by' if code.startswith('cc-by') or code == 'cc by' else code
        path = row['analysis_path'] or row['original_path']
        out.append({
            'ref': f"library:{row['id']}", 'layer': 'library', 'title': row['title'], 'creator': row['creator'],
            'date': row['date_text'], 'medium': row['medium'], 'subjects': result.get('subjects', []),
            'summary': result.get('summary', ''), 'description': row['description'],
            'techniques': notes.get(row['id'], []), 'colour': row['color_family'] or '',
            'palette': [p['hex'] for p in json.loads(row['palette_json'] or '[]')][:4],
            'orientation': row['orientation'] or _orientation(row['width'], row['height']),
            'width': row['width'], 'height': row['height'], 'generated': False, 'provider': row['provider'],
            'source_url': row['source_url'],
            'licence': {'label': rights.get('label', ''), 'code': code, 'url': rights.get('url', ''),
                        'restrictions': rights.get('restrictions', ''), 'checked_by': 'atlas/rights.py'},
            'credit': rights.get('attribution', ''), 'file': str(media / path) if path else None,
            'thumb': row['thumb_path'], 'image_id': row['id']})
    return out


def references(home: Path | None = None, layer_names=LAYERS) -> list[dict]:
    home = home_dir(home)
    out = []
    if 'library' in layer_names:
        out += _library(home)
    if 'generated' in layer_names:
        out += [{**r, 'orientation': _orientation(r.get('width'), r.get('height'))} for r in layers.generated()]
    if 'design-system' in layer_names:
        for system in layers.systems(home):
            out += [{**r, 'orientation': _orientation(r.get('width'), r.get('height'))} for r in system['references']]
    return out


def _clean_list(values, limit: int, length: int = 80) -> list[str]:
    if values is None:
        return []
    if isinstance(values, str):
        values = [values]
    if not isinstance(values, (list, tuple)) or len(values) > limit:
        raise ValueError(f'give at most {limit} values')
    out = []
    for value in values:
        if not isinstance(value, str) or len(value) > length:
            raise ValueError(f'each value must be text of at most {length} characters')
        if value.strip():
            out.append(value.strip())
    return out


def route(brief: str, home: Path | None = None) -> dict:
    """Which design system and which of the user's collections suit a brief: shared distinctive words, no AI."""
    tokens = set(coding.words(brief)) - coding.STOPWORDS
    picks = []
    for system in layers.systems(home):
        vocabulary = set(coding.words(system['description'])) - coding.GENERIC
        # The descriptions name each other; only the part before "Not for" describes this system.
        own = set(coding.words(system['description'].split('Not for')[0])) - coding.GENERIC
        matched = sorted(word for word in tokens & own if len(word) > 2)
        picks.append({'system': system['name'], 'matched': matched, 'score': len(matched), '_v': vocabulary})
    picks.sort(key=lambda p: (-p['score'], p['system'] != 'archive-of-looking'))
    best = picks[0] if picks else None
    system = None
    if best:
        system = {'name': best['system'], 'matched': best['matched'],
                  'why': (f"the brief shares {', '.join(best['matched'][:6])} with its description" if best['score']
                          else 'no system matched the brief; archive-of-looking is the owner\'s default')}
        if not best['score'] and best['system'] != 'archive-of-looking':
            system = None
    collections = []
    with jobs.open_store(home_dir(home)) as store:
        for row in store.rows('SELECT id, name, description FROM collections'):
            matched = sorted(tokens & (set(coding.words(f"{row['name']} {row['description']}")) - coding.GENERIC))
            if matched:
                collections.append({'id': row['id'], 'name': row['name'], 'matched': matched})
    return {'system': system, 'alternatives': [{'name': p['system'], 'matched': p['matched']} for p in picks[1:]
                                               if p['score']],
            'collections': sorted(collections, key=lambda c: -len(c['matched']))[:5]}


def guidance(technique_ids: list[str], taxonomy: dict | None = None) -> list[dict]:
    """What each technique is, when it helps, what to look for, how not to confuse it, and its limits."""
    taxonomy = taxonomy or catalog.load()[0]
    by_id = {t['id']: t for t in taxonomy['techniques']}
    names = {t['id']: t['name'] for t in taxonomy['techniques']}
    return [{'id': tid, 'name': by_id[tid]['name'], 'definition': by_id[tid]['definition'],
             'how_it_works': by_id[tid]['explanation'], 'when_it_helps': by_id[tid]['when_it_helps'],
             'look_for': by_id[tid]['observable_cues'], 'limitations': by_id[tid]['limitations'],
             'counterexample': by_id[tid]['counterexample'],
             'not_to_confuse_with': [{'technique': names.get(c['technique'], c['technique']),
                                      'how_to_tell': c['how_to_tell']} for c in by_id[tid]['confusions']]}
            for tid in technique_ids if tid in by_id]


def search(*, brief: str = '', techniques=None, goals=None, subjects=None, orientation: str = '', colour: str = '',
           medium: str = '', era_from: int | None = None, era_to: int | None = None, layers_wanted=None,
           system: str = '', publishable_only: bool = False, limit: int = 8, home: Path | None = None) -> dict:
    """Rank references across layers. Inputs are validated here because agents call this directly."""
    if not isinstance(brief, str) or len(brief) > MAX_TEXT:
        raise ValueError(f'the brief must be text of at most {MAX_TEXT} characters')
    taxonomy = catalog.load()[0]
    known_t = {t['id'] for t in taxonomy['techniques']}
    known_g = {g['id'] for g in taxonomy['goals']}
    techniques, goals = _clean_list(techniques, 12), _clean_list(goals, 12)
    unknown = [t for t in techniques if t not in known_t] + [g for g in goals if g not in known_g]
    if unknown:
        raise ValueError(f"unknown technique or goal id: {', '.join(unknown)} (list them with the techniques tool)")
    subjects = [w for s in _clean_list(subjects, 8) for w in coding.words(s)]
    wanted_layers = _clean_list(layers_wanted, 3) or list(LAYERS)
    if any(layer not in LAYERS for layer in wanted_layers):
        raise ValueError(f"layers are {', '.join(LAYERS)}")
    if orientation and orientation not in ORIENTATIONS:
        raise ValueError(f"orientation is one of {', '.join(ORIENTATIONS)}")
    if not isinstance(limit, int) or not 1 <= limit <= 40:
        raise ValueError('limit is between 1 and 40')
    for name, value in (('colour', colour), ('medium', medium), ('system', system)):
        if not isinstance(value, str) or len(value) > 80:
            raise ValueError(f'{name} must be short text')
    reading = coding.code_request(brief, taxonomy, techniques, goals) if brief else \
        {'techniques': [{'id': t, 'exact': True} for t in techniques], 'goals': [{'id': g, 'exact': True} for g in goals],
         'subject_terms': []}
    want_t = [t['id'] for t in reading['techniques']]
    want_g = [g['id'] for g in reading['goals']]
    terms = list(dict.fromkeys(subjects + [t for t in reading['subject_terms'] if t not in coding.GENERIC | FORMAT_WORDS]))[:12]
    goal_links = {g['id']: {t['id'] for t in taxonomy['techniques'] if g['id'] in t['goals']} for g in taxonomy['goals']}
    names = {t['id']: t['name'] for t in taxonomy['techniques']} | {g['id']: g['name'] for g in taxonomy['goals']}
    routed = route(brief, home) if brief and 'design-system' in wanted_layers else {'system': None}
    routed_system = system or (routed['system'] or {}).get('name', '')

    ranked = []
    for ref in references(home, wanted_layers):
        if publishable_only and ref['licence']['code'] not in PUBLISHABLE:
            continue
        if orientation and ref.get('orientation') != orientation:
            continue
        if system and ref.get('system') != system:
            continue
        if colour and colour.lower() not in (ref.get('colour') or '').lower():
            continue
        if medium and medium.lower() not in (ref.get('medium') or '').lower():
            continue
        year = _year(ref.get('date', ''))
        if (era_from is not None or era_to is not None) and (
                year is None or (era_from is not None and year < era_from) or (era_to is not None and year > era_to)):
            continue
        score, reasons = 0.0, []
        shown = {t['id']: t for t in ref['techniques']}
        for tid in want_t:
            if tid in shown:
                note = shown[tid]
                score += STATE_WEIGHT.get(note['state'], 1) + (1 if note.get('role') == 'primary' else 0)
                evidence = f": {note['evidence'][0]}" if note.get('evidence') else ''
                reasons.append(f"Shows {names[tid]} ({STATE_WORDS.get(note['state'], note['state'])}){evidence}")
        for gid in want_g:
            via = sorted(goal_links.get(gid, set()) & set(shown) - set(want_t),
                         key=lambda v: -STATE_WEIGHT.get(shown[v]['state'], 1) - (shown[v].get('role') == 'primary'))
            if via:
                best = shown[via[0]]
                score += 0.75 * (STATE_WEIGHT.get(best['state'], 1) + (1 if best.get('role') == 'primary' else 0))
                reasons.append(f"Serves “{names[gid]}” through {', '.join(names[v] for v in via[:3])} "
                               f"({STATE_WORDS.get(best['state'], best['state'])})"
                               + (f": {best['evidence'][0]}" if best.get('evidence') else ''))
        strong = ' '.join(coding.words(' '.join([ref['title'], *ref.get('subjects', [])])))
        weak = ' '.join(coding.words(' '.join([ref.get('summary', ''), ref.get('notes', ''), ref.get('medium', ''),
                                               ref.get('description', '')])))
        hits_strong = [t for t in terms if f' {t} ' in f' {strong} ']
        hits_weak = [t for t in terms if t not in hits_strong and f' {t} ' in f' {weak} ']
        if hits_strong or hits_weak:
            score += 1.5 * len(hits_strong) + 0.5 * len(hits_weak)
            reasons.append(f"Subject matches {', '.join(hits_strong + hits_weak)}")
        if score and routed_system and ref.get('system') == routed_system:
            score += 1
            reasons.append(f'From {routed_system}, the design system that suits this brief')
        filtered = bool(orientation or colour or medium or system or era_from or era_to)
        if not score and not (filtered and not (want_t or want_g or terms)):
            continue
        ranked.append((score, ref, reasons))
    ranked.sort(key=lambda item: (-item[0], item[1]['layer'] != 'library', item[1]['ref']))
    # Each other layer with a match keeps its best two places, so library volume never hides them.
    seen, unique = set(), []
    for item in ranked:
        family = VARIANT.sub('', item[1]['ref'])
        if family not in seen:
            seen.add(family)
            unique.append(item)
    ranked = unique
    chosen = []
    for layer in wanted_layers:
        if layer != 'library':
            chosen += [item for item in ranked if item[1]['layer'] == layer][:2]
    chosen = chosen[:limit // 2]
    chosen += [item for item in ranked if item not in chosen][:limit - len(chosen)]
    chosen.sort(key=lambda item: (-item[0], item[1]['layer'] != 'library', item[1]['ref']))
    results = [{**_public(ref), 'score': round(score, 2), 'reasons': reasons or ['Matches the filters you set']}
               for score, ref, reasons in chosen]
    return {'reading': {'techniques': [{'id': t, 'name': names[t]} for t in want_t],
                        'goals': [{'id': g, 'name': names[g]} for g in want_g], 'subject_terms': terms},
            'route': routed, 'total_matches': len(ranked), 'results': results,
            'note': 'Rankings use stored readings and words only, no AI. Check licence and restrictions before use; '
                    'generated and design-system references are labelled and are not licence-checked by Visual Atlas.'}


def _public(ref: dict) -> dict:
    keep = ('ref', 'layer', 'system', 'title', 'creator', 'date', 'medium', 'subjects', 'orientation', 'colour',
            'palette', 'width', 'height', 'generated', 'licence', 'credit', 'source_url', 'file', 'prompt', 'studied')
    out = {key: ref[key] for key in keep if key in ref and ref[key] not in (None, '', [])}
    out['techniques'] = [{'id': t['id'], 'state': t['state']} for t in ref.get('techniques', [])]
    return out


def advise(brief: str, *, limit: int = 6, publishable_only: bool = False, layers_wanted=None,
           home: Path | None = None) -> dict:
    """For a visual decision: how the brief reads, which techniques could serve it and how, and references."""
    if not isinstance(brief, str) or not brief.strip():
        raise ValueError('describe the visual decision in a sentence or two')
    found = search(brief=brief, limit=limit, publishable_only=publishable_only, layers_wanted=layers_wanted, home=home)
    taxonomy = catalog.load()[0]
    technique_ids = [t['id'] for t in found['reading']['techniques']]
    if not technique_ids:  # a goal with no named technique: offer that goal's techniques, best covered first
        goal_ids = {g['id'] for g in found['reading']['goals']}
        technique_ids = [t['id'] for t in taxonomy['techniques'] if goal_ids & set(t['goals'])][:4]
    steps = ['Pick one technique below and say in a sentence what it should do for this audience.',
             'Open two or three references and check the "look for" cues in each before borrowing anything.',
             'Borrow the technique, never the picture: change subject, palette and framing so the result is yours.',
             'Check each reference\'s licence and restrictions before it appears in published work.']
    if not technique_ids:
        steps.insert(0, 'The brief named no goal or technique the atlas knows. Say what the image should do '
                        '(stand out, feel calm, show scale, surprise) or name a technique.')
    return {**found, 'guidance': guidance(technique_ids[:4], taxonomy), 'next_steps': steps}


REF = re.compile(r'^(library:\d{1,9}|generated:[a-z0-9][a-z0-9-]{0,80}|system:[a-z0-9-]{1,60}:[a-z0-9][a-z0-9-]{0,80})$')


def get(ref: str, home: Path | None = None) -> dict:
    """One reference in full: evidence and effect per technique, licence, credit, and its local file."""
    if not isinstance(ref, str) or not REF.match(ref):
        raise ValueError('ref looks like library:12, generated:some-id or system:archive-of-looking:some-id')
    if ref.startswith('library:'):
        found = next((r for r in _library(home_dir(home)) if r['ref'] == ref), None)
    else:
        found = layers.find(ref, home)
    if found is None:
        raise LookupError(f'no reference {ref} (removed, not ready, or its layer is not enabled here)')
    taxonomy = catalog.load()[0]
    names = {t['id']: t['name'] for t in taxonomy['techniques']}
    out = {**_public(found), 'orientation': found.get('orientation') or _orientation(found.get('width'), found.get('height'))}
    out['techniques'] = [{**t, 'name': names.get(t['id'], t['id']), 'state_means': STATE_WORDS.get(t['state'], t['state'])}
                         for t in found.get('techniques', [])]
    for key in ('summary', 'notes', 'slots', 'review', 'description'):
        if found.get(key):
            out[key] = found[key]
    return out


def techniques(goal: str = '') -> dict:
    """The codebook for agents: goals and the techniques that serve them, with ids."""
    taxonomy = catalog.load()[0]
    if goal and goal not in {g['id'] for g in taxonomy['goals']}:
        raise ValueError(f'unknown goal id: {goal}')
    return {'goals': [{'id': g['id'], 'name': g['name'], 'description': g['description']} for g in taxonomy['goals']
                      if not goal or g['id'] == goal],
            'techniques': [{'id': t['id'], 'name': t['name'], 'definition': t['definition'], 'goals': t['goals'],
                            'operations': t['operations'], 'domains': t['domains']}
                           for t in taxonomy['techniques'] if not goal or goal in t['goals']]}


def technique(technique_id: str, *, limit: int = 4, publishable_only: bool = False, home: Path | None = None) -> dict:
    """Guidance for one technique with its strongest references."""
    taxonomy = catalog.load()[0]
    if technique_id not in {t['id'] for t in taxonomy['techniques']}:
        raise ValueError(f'unknown technique id: {technique_id} (see list_techniques)')
    found = search(techniques=[technique_id], limit=limit, publishable_only=publishable_only, home=home)
    return {**guidance([technique_id], taxonomy)[0], 'references': found['results'],
            'examples_available': found['total_matches']}
