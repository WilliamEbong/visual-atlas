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
import sqlite3
from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageChops, ImageStat

from atlas import catalog, coding, layers
from atlas.home import home_dir

SCHEMA = max(int(f.name.split('_')[0]) for f in (Path(__file__).parent / 'migrations').glob('*.sql'))

LAYERS = ('library', 'generated', 'design-system')
STATE_WEIGHT = {'human_reviewed': 3.0, 'model_reviewed': 2.0, 'proposed': 1.0, 'intended': 1.0}
MOODS = Path(__file__).parent / 'data' / 'moods.json'
LEADS = Path(__file__).parent / 'data' / 'leads.json'


def leads() -> dict:
    """Each technique's reviewer-chosen strongest starter examples (provider:item), strongest first."""
    return json.loads(LEADS.read_text(encoding='utf-8'))['leads'] if LEADS.exists() else {}


def moods() -> tuple[set, dict]:
    """Mood goals, and the moods each starter picture itself conveys (provider:item -> goal ids), from data."""
    data = json.loads(MOODS.read_text(encoding='utf-8')) if MOODS.exists() else {}
    return set(data.get('goals', [])), data.get('moods', {})
STATE_WORDS = {'human_reviewed': 'confirmed by you', 'model_reviewed': 'agreed by a second model',
               'proposed': 'proposed by a model', 'intended': 'intended by the prompt, checked by eye'}
PUBLISHABLE = {'cc0', 'pd', 'cc-by'}  # licence codes with a documented free licence (generated and unclear are not)
ORIENTATIONS = ('portrait', 'landscape', 'square')
MAX_TEXT = 4000
# Format and occasion words say what is being made, not what the picture shows (they still route design systems).
FORMAT_WORDS = {'deck', 'pitch', 'keynote', 'studio', 'launch', 'brand', 'client', 'opener', 'reel', 'thumbnail',
                # layout words say where text goes, not what the picture shows ('room on the left for the title')
                'left', 'right', 'room', 'side', 'half', 'corner', 'headline', 'landing', 'space', 'copy', 'text',
                # mood words describe the feeling wanted, not what is in the picture ('warm' matched a gold medal)
                'warm', 'communal', 'calm', 'quiet', 'lonely', 'steady', 'trustworthy', 'cosy', 'cozy', 'festive',
                'hopeful', 'tense', 'credible', 'serious', 'playful', 'friendly', 'elegant', 'moody', 'bold', 'soft'}
VARIANT = re.compile(r'-\d+x\d+$')  # the same picture cropped for another format (gen-x-4x5)
SHOT_NUMBER = re.compile(r'[\s_(-]+\d{2,}\)?$')  # "Sunset 5746", "(7027587519)": a camera's shot number


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


@contextmanager
def _readonly(home: Path):
    """A read-only connection, or None when there is no library yet. Never creates, migrates or syncs anything:
    the desk, the CLI and the MCP server only read. An older library must be opened by the app first."""
    path = home / 'atlas.db'  # jobs.db_path, without importing the job runner (httpx, providers)
    if not path.is_file():
        yield None
        return
    connection = sqlite3.connect(f'{path.resolve().as_uri()}?mode=ro', uri=True, timeout=5)
    connection.row_factory = sqlite3.Row
    try:
        version = connection.execute('PRAGMA user_version').fetchone()[0]
        if version != SCHEMA:
            raise ValueError('This library was made by another version of Visual Atlas. Open the app (or run '
                             '`uv run atlas doctor`) once to bring it up to date, then ask again.')
        yield connection
    finally:
        connection.close()


def _rows(connection, query: str, parameters=()) -> list[dict]:
    return [dict(row) for row in connection.execute(query, parameters)]


def _library(home: Path) -> list[dict]:
    """Every ready library image as a reference record (one pass; fine for thousands of images)."""
    with _readonly(home) as connection:
        if connection is None:
            return []
        images = _rows(connection, 
            "SELECT i.id, i.title, i.creator, i.date_text, i.medium, i.description, i.provider, i.provider_item_id, i.source_url, i.width, "
            "i.height, i.original_path, i.analysis_path, i.thumb_path, a.result_json, m.color_family, m.palette_json, "
            "m.orientation, (SELECT json_object('code', r.license_code, 'version', r.license_version, 'label', r.label, "
            "'url', r.license_url, 'attribution', r.required_attribution, 'restrictions', r.restrictions) FROM "
            "rights_records r WHERE r.image_id=i.id ORDER BY r.id DESC LIMIT 1) AS rights FROM images i "
            "LEFT JOIN analyses a ON a.id=i.analysis_id LEFT JOIN image_metrics m ON m.image_id=i.id "
            "WHERE i.removed_at IS NULL AND i.status='ready'")
        notes = {}
        for row in _rows(connection, "SELECT image_id, technique_id, state, role, evidence_json, effect, confidence FROM annotations "
                              "WHERE state!='rejected' ORDER BY role='primary' DESC, confidence DESC"):
            notes.setdefault(row['image_id'], []).append(
                {'id': row['technique_id'], 'state': row['state'], 'role': row['role'],
                 'evidence': json.loads(row['evidence_json'])[:2], 'effect': row['effect'],
                 'confidence': row['confidence'] or 0.0})
    media = home / 'media'
    tagged = moods()[1]
    out = []
    for row in images:
        result = json.loads(row['result_json']) if row['result_json'] else {}
        rights = json.loads(row['rights']) if row['rights'] else {}
        code = (rights.get('code') or '').lower()
        # Exact codes only: anything else (CC BY-NC, unknown) keeps its own code and is never publishable.
        code = {'cc0': 'cc0', 'pd': 'pd', 'pdm': 'pd', 'cc by': 'cc-by', 'cc-by': 'cc-by'}.get(code, code or 'unclear')
        path = row['analysis_path'] or row['original_path']
        out.append({
            'ref': f"library:{row['id']}", 'layer': 'library', 'title': row['title'], 'creator': row['creator'],
            'date': row['date_text'], 'medium': row['medium'], 'subjects': result.get('subjects', []),
            'summary': result.get('summary', ''), 'description': row['description'],
            'techniques': notes.get(row['id'], []), 'colour': row['color_family'] or '',
            'palette': [p['hex'] for p in json.loads(row['palette_json'] or '[]')][:4],
            'orientation': row['orientation'] or _orientation(row['width'], row['height']),
            'width': row['width'], 'height': row['height'], 'generated': False, 'provider': row['provider'],
            'source_url': row['source_url'], 'moods': tagged.get(f"{row['provider']}:{row['provider_item_id']}", []),
            'key': f"{row['provider']}:{row['provider_item_id']}",
            'licence': {'label': rights.get('label', ''), 'code': code, 'url': rights.get('url', ''),
                        'restrictions': rights.get('restrictions', ''), 'checked_by': 'atlas/rights.py'},
            'credit': rights.get('attribution', ''), 'file': str(media / path) if path else None,
            'thumb': row['thumb_path'], 'display': path, 'image_id': row['id']})
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
    with _readonly(home_dir(home)) as connection:
        for row in _rows(connection, 'SELECT id, name, description FROM collections') if connection else []:
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


@lru_cache(maxsize=4096)
def _text(text: str) -> str:
    """A reference's searchable words, tokenised once: most of a search's time went here."""
    return ' '.join(coding.words(text))


def search(*, brief: str = '', techniques=None, goals=None, subjects=None, orientation: str = '', colour: str = '',
           medium: str = '', era_from: int | None = None, era_to: int | None = None, layers_wanted=None,
           system: str = '', publishable_only: bool = False, limit: int = 8, home: Path | None = None,
           require_technique: str = '') -> dict:
    """Rank references across layers. Inputs are validated here because agents call this directly."""
    if not isinstance(brief, str) or len(brief) > MAX_TEXT:
        raise ValueError(f'the brief must be text of at most {MAX_TEXT} characters')
    taxonomy = catalog.load()[0]
    known_t = {t['id'] for t in taxonomy['techniques']}
    known_g = {g['id'] for g in taxonomy['goals']}
    techniques, goals = _clean_list(techniques, 12), _clean_list(goals, 12)
    unknown = [t for t in techniques if t not in known_t] + [g for g in goals if g not in known_g]
    if unknown:
        raise ValueError(f"unknown technique or goal id: {', '.join(unknown)} (list them with list_techniques)")
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
    reading = coding.code_request(brief, taxonomy, techniques, goals, exclude=coding.GENERIC | FORMAT_WORDS) if brief else \
        {'techniques': [{'id': t, 'exact': True} for t in techniques], 'goals': [{'id': g, 'exact': True} for g in goals],
         'subject_terms': []}
    want_t = [t['id'] for t in reading['techniques']]
    want_g = [g['id'] for g in reading['goals']]
    terms = list(dict.fromkeys(subjects + [t for t in reading['subject_terms'] if t not in coding.GENERIC | FORMAT_WORDS]))[:12]
    goal_links = {g['id']: {t['id'] for t in taxonomy['techniques'] if g['id'] in t['goals']} for g in taxonomy['goals']}
    names = {t['id']: t['name'] for t in taxonomy['techniques']} | {g['id']: g['name'] for g in taxonomy['goals']}
    mood_goals = moods()[0]
    chosen = leads()
    routed = route(brief, home) if brief and 'design-system' in wanted_layers else {'system': None}
    routed_system = system or (routed['system'] or {}).get('name', '')

    ranked = []
    for ref in references(home, wanted_layers):
        # Only atlas/rights.py decides publication: other layers are references only, whatever their own notes say.
        if publishable_only and (ref['layer'] != 'library' or ref['licence']['code'] not in PUBLISHABLE):
            continue
        if orientation and ref.get('orientation') != orientation:
            continue
        if system and ref.get('system') != system:
            continue
        if require_technique and not any(t['id'] == require_technique for t in ref['techniques']):
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
                # A more confident reading of the same state and role ranks higher (otherwise ties fell to ref order).
                score += (STATE_WEIGHT.get(note['state'], 1) + (1 if note.get('role') == 'primary' else 0)
                          + 0.5 * note.get('confidence', 0.8))
                if note['state'] == 'human_reviewed':
                    score += 200.0  # the person's own confirmation comes before any curator's pick
                if ref.get('key') in chosen.get(tid, []):  # a curator's lead example teaches the technique best
                    score += 100.0 - 10 * chosen[tid].index(ref['key'])  # the curator's order decides among leads
                evidence = f": {note['evidence'][0]}" if note.get('evidence') else ''
                reasons.append(f"Shows {names[tid]} ({STATE_WORDS.get(note['state'], note['state'])}){evidence}")
        for gid in want_g:
            if gid in ref.get('moods', []) and gid not in mood_goals:
                score += 50.0  # a reviewer judged that this picture itself conveys the goal (calm, movement)
            if gid in mood_goals:  # a mood is served only by a picture that itself carries it, never by a technique's claim
                if gid in ref.get('moods', []):
                    score += 3.0
                    reasons.append(f"Serves “{names[gid]}”: the picture itself reads that way (a reviewer's reading)")
                continue
            via = sorted(goal_links.get(gid, set()) & set(shown) - set(want_t),
                         key=lambda v: (-STATE_WEIGHT.get(shown[v]['state'], 1) - (shown[v].get('role') == 'primary'), v))
            if via:
                best = shown[via[0]]
                score += 0.75 * (STATE_WEIGHT.get(best['state'], 1) + (1 if best.get('role') == 'primary' else 0))
                # The state and evidence quoted belong to the named technique only.
                reasons.append(f"Serves “{names[gid]}” through {names[via[0]]} "
                               f"({STATE_WORDS.get(best['state'], best['state'])})"
                               + (f": {best['evidence'][0]}" if best.get('evidence') else ''))
        strong = _text(' '.join([ref['title'], *ref.get('subjects', [])]))
        weak = _text(' '.join([ref.get('summary', ''), ref.get('notes', ''), ref.get('medium', ''),
                               ref.get('description', '')]))
        hits_strong = [t for t in terms if f' {t} ' in f' {strong} ']
        hits_weak = [t for t in terms if t not in hits_strong and f' {t} ' in f' {weak} ']
        if hits_strong or hits_weak:
            words_score = 1.5 * len(hits_strong) + 0.5 * len(hits_weak)
            # When the reading names techniques or goals, shown techniques lead; subject words only break ties.
            score += min(words_score, 0.9) if want_t or want_g else words_score
            reasons.append(f"Subject matches {', '.join(hits_strong + hits_weak)}")
        if score and routed_system and ref.get('system') == routed_system:
            score += 1
            reasons.append(f'From {routed_system}, the design system that suits this brief')
        filtered = bool(orientation or colour or medium or system or era_from or era_to)
        if not score and not (filtered and not (want_t or want_g or terms)):
            continue
        ranked.append((score, ref, reasons))
    def order(item):  # pictures that show a requested technique or serve a requested goal always come first
        evidence = any(reason.startswith(('Shows ', 'Serves ')) for reason in item[2])
        return (not evidence if want_t or want_g else False, -item[0], item[1]['layer'] != 'library', item[1]['ref'])
    ranked.sort(key=order)
    # Each other layer with a match keeps its best two places, so library volume never hides them.
    seen, unique = set(), []
    for item in ranked:
        family = VARIANT.sub('', item[1]['ref'])
        # Numbered shots of one subject by one known maker ("Frigate Bird ... Sunset 5746" and "... 5738") are one
        # series; same-titled works without a shot number, or by an unknown maker, stay separate.
        title, maker = (item[1].get('title') or '').lower(), (item[1].get('creator') or '').lower().strip()
        shot = SHOT_NUMBER.search(title)
        number = int(re.sub(r'\D', '', shot.group())) if shot else 0
        is_year = 1400 <= number <= 2099 and len(str(number)) == 4  # "Igeha Schokolade, 1926" is a date, not a shot
        stem = SHOT_NUMBER.sub('', title) if shot and not is_year else title
        series = (stem, maker) if stem != title and maker and not maker.startswith('unknown') else None
        if family not in seen and (series is None or series not in seen):
            seen.update({family, series} - {None})
            unique.append(item)
    ranked = unique
    chosen = []
    for layer in wanted_layers:
        if layer != 'library':
            chosen += [item for item in ranked if item[1]['layer'] == layer][:2]
    chosen = chosen[:limit // 2]
    chosen += [item for item in ranked if item not in chosen][:limit - len(chosen)]
    chosen.sort(key=order)
    results = [{**_public(ref), 'score': round(score, 2), 'reasons': reasons or ['Matches the filters you set']}
               for score, ref, reasons in chosen]
    return {'reading': {'techniques': [{'id': t, 'name': names[t]} for t in want_t],
                        'goals': [{'id': g, 'name': names[g]} for g in want_g], 'subject_terms': terms},
            'route': routed, 'total_matches': len(ranked), 'results': results,
            'note': 'Chosen from your library without AI. Generated examples and design-system pictures have no '
                    'licence checked by Visual Atlas: use them only as references. Check each licence before you publish.'}


def _public(ref: dict) -> dict:
    keep = ('ref', 'layer', 'system', 'title', 'creator', 'date', 'medium', 'subjects', 'orientation', 'colour',
            'palette', 'width', 'height', 'generated', 'licence', 'credit', 'source_url', 'file', 'prompt', 'studied',
            'image_id', 'thumb', 'display')
    out = {key: ref[key] for key in keep if key in ref and ref[key] not in (None, '', [])}
    out['techniques'] = [{'id': t['id'], 'state': t['state']} for t in ref.get('techniques', [])]
    return out


def _codebook(taxonomy: dict) -> dict:
    """The ids an agent can pass back when the word reader missed: one call, then a second with ids."""
    return {'goals': [{'id': g['id'], 'name': g['name'], 'description': g['description']} for g in taxonomy['goals']],
            'techniques': [{'id': t['id'], 'name': t['name'], 'definition': t['definition']}
                           for t in taxonomy['techniques']]}


def _candidates(found: dict, taxonomy: dict) -> list[str]:
    technique_ids = [t['id'] for t in found['reading']['techniques']]
    if not technique_ids:  # a goal with no named technique: offer that goal's techniques, in codebook order
        goal_ids = {g['id'] for g in found['reading']['goals']}
        technique_ids = [t['id'] for t in taxonomy['techniques'] if goal_ids & set(t['goals'])]
    return technique_ids


def advise(brief: str, *, techniques=None, goals=None, limit: int = 6, publishable_only: bool = False,
           layers_wanted=None, home: Path | None = None) -> dict:
    """For a visual decision: how the brief reads, which techniques could serve it and how, and references.
    Technique and goal ids, when given, are added to what the words say (agents can read a brief better)."""
    if not isinstance(brief, str) or not brief.strip():
        raise ValueError('describe the visual decision in a sentence or two')
    found = search(brief=brief, techniques=techniques, goals=goals, limit=limit, publishable_only=publishable_only,
                   layers_wanted=layers_wanted, home=home)
    taxonomy = catalog.load()[0]
    technique_ids = _candidates(found, taxonomy)[:4]
    steps = ['Pick one technique below and say in a sentence what it should do for this audience.',
             'Open two or three references and check the "look for" cues in each before borrowing anything.',
             'Borrow the technique, never the picture: change subject, palette and framing so the result is yours.',
             'Check each reference\'s licence and restrictions before it appears in published work.']
    extra = {}
    if not technique_ids:
        steps.insert(0, 'The words of the brief matched no goal or technique. Choose the ids that fit from '
                        '`codebook` and ask again with them (techniques=[...], goals=[...]), or say what the image '
                        'should do: stand out, feel calm, show scale, surprise.')
        extra['codebook'] = _codebook(taxonomy)
    return {**found, 'guidance': guidance(technique_ids, taxonomy), 'next_steps': steps, **extra}


def directions(brief: str, *, techniques=None, goals=None, count: int = 3, per_direction: int = 2,
               publishable_only: bool = False, layers_wanted=None, home: Path | None = None) -> dict:
    """Distinct ways to answer a brief, one technique each, with how to carry it out, what to avoid and the
    references that show it best. Built from the codebook and stored readings only: no AI, nothing written."""
    if not isinstance(count, int) or not 1 <= count <= 5:
        raise ValueError('count is between 1 and 5')
    if not isinstance(per_direction, int) or not 1 <= per_direction <= 4:
        raise ValueError('per_direction is between 1 and 4')
    found = search(brief=brief, techniques=techniques, goals=goals, limit=1, publishable_only=publishable_only,
                   layers_wanted=layers_wanted, home=home)
    taxonomy = catalog.load()[0]
    by_id = {t['id']: t for t in taxonomy['techniques']}
    goal_names = {g['id']: g['name'] for g in taxonomy['goals']}
    wanted_goals = [g['id'] for g in found['reading']['goals']]
    mood_goals = moods()[0]
    subjects = found['reading']['subject_terms'][:8]
    moods_wanted = [g for g in wanted_goals if g in mood_goals]
    tagged_goals = {g for goals in moods()[1].values() for g in goals}
    soft = [g for g in wanted_goals if g in tagged_goals and g not in mood_goals]  # preferred, not required
    out = []
    used = set()
    # A mood brief first keeps only pictures that carry the mood; with none anywhere, technique evidence alone.
    for strict in ([True, False] if moods_wanted else [False]):
        for tid in _candidates(found, taxonomy):
            if len(out) == count:
                break
            # Only pictures that carry the technique compete; the subject words then rank them.
            refs = search(techniques=[tid], goals=moods_wanted + soft, subjects=subjects, limit=40,
                          publishable_only=publishable_only, layers_wanted=layers_wanted, home=home,
                          require_technique=tid)['results']
            refs = [r for r in refs if r['ref'] not in used]  # each picture teaches one way only
            if strict:  # keep pictures that themselves carry a requested mood; other goal reasons do not count
                carries = tuple(f"Serves “{goal_names[g]}”: the picture itself" for g in moods_wanted)
                refs = [r for r in refs if any(reason.startswith(carries) for reason in r['reasons'])]
            refs = refs[:per_direction]
            if not refs:
                continue  # a direction with nothing to show is advice the agent cannot check; skip it
            technique = by_id[tid]
            carried = {g for g in moods_wanted for r in refs if any(x.startswith(f"Serves “{goal_names[g]}”") for x in r['reasons'])}
            serves = [goal_names[g] for g in wanted_goals if g in technique['goals'] and (g not in mood_goals or g in carried)] or \
                [goal_names[g] for g in technique['goals'] if g in goal_names and g not in mood_goals][:2]
            out.append({'technique': {'id': tid, 'name': technique['name']}, 'serves': serves,
                        'idea': technique['definition'], 'why_it_works': technique['explanation'],
                        'make_sure': technique['observable_cues'], 'watch_out': technique['limitations'],
                        'not_to_confuse_with': [c['how_to_tell'] for c in technique['confusions']][:2],
                        'references': refs})
            used.update(r['ref'] for r in refs)
        if out:
            break
    result = {'reading': found['reading'], 'route': found['route'], 'directions': out,
              'note': 'Directions come from the codebook and stored readings, with no AI. Each one names a single '
                      'technique: pick one, then borrow the technique, never the picture.'}
    if not out:
        result['codebook'] = _codebook(taxonomy)
        result['note'] += ' Nothing matched: choose technique or goal ids from codebook and ask again.'
    return result


REF = re.compile(r'^(library:\d{1,9}|generated:[a-z0-9][a-z0-9-]{0,80}|system:[a-z0-9-]{1,60}:[a-z0-9][a-z0-9-]{0,80})$')


def _record(ref: str, home: Path | None = None) -> dict:
    if not isinstance(ref, str) or not REF.match(ref):
        raise ValueError('ref looks like library:12, generated:some-id or system:archive-of-looking:some-id')
    if ref.startswith('library:'):
        found = next((r for r in _library(home_dir(home)) if r['ref'] == ref), None)
    else:
        found = layers.find(ref, home)
    if found is None:
        raise LookupError(f'no reference {ref} (removed, not ready, or its layer is not enabled here)')
    return found


def get(ref: str, home: Path | None = None) -> dict:
    """One reference in full: evidence and effect per technique, licence, credit, and its local file."""
    found = _record(ref, home)
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


def _picture(record: dict, home: Path) -> Path | None:
    """The record's own image file, only if it is still inside its folder (library media or the layer folder)."""
    if record['layer'] != 'library':
        return layers.safe_file(record)
    try:
        path = Path(record['file']).resolve(strict=True)
    except (OSError, TypeError, RuntimeError):
        return None
    return path if path.is_relative_to((home / 'media').resolve()) and path.is_file() else None


@lru_cache(maxsize=8192)
def _signature(path: str, mtime_ns: int, size: int) -> Image.Image | None:
    """An 8 x 8 luma-chroma thumbnail: where the light, dark and colour sit. Local, no model. Kept in memory for the
    process; the app computes them in the background at start."""
    del mtime_ns, size  # part of the cache key: a changed file is read again
    try:
        with Image.open(path) as picture:
            picture.draft('RGB', (64, 64))
            return picture.convert('RGB').resize((8, 8), Image.Resampling.BOX).convert('YCbCr')
    except (OSError, ValueError, Image.DecompressionBombError):
        return None


def _signature_of(record: dict, home: Path) -> Image.Image | None:
    path = _picture(record, home)
    try:
        stat = path.stat() if path else None
    except OSError:
        return None
    return _signature(str(path), stat.st_mtime_ns, stat.st_size) if stat else None


def similar(ref: str, *, limit: int = 6, publishable_only: bool = False, layers_wanted=None,
            home: Path | None = None) -> dict:
    """References that look like this one: similar placement of light, dark and colour (a composition match, not
    a subject match), with the techniques they share. Local pixel comparison; no AI, no service."""
    if not isinstance(limit, int) or not 1 <= limit <= 40:
        raise ValueError('limit is between 1 and 40')
    wanted = _clean_list(layers_wanted, 3) or list(LAYERS)
    if any(layer not in LAYERS for layer in wanted):
        raise ValueError(f"layers are {', '.join(LAYERS)}")
    home = home_dir(home)
    target = _record(ref, home)
    mine = _signature_of(target, home)
    if mine is None:
        raise LookupError(f'the picture for {ref} cannot be read')
    names = {t['id']: t['name'] for t in catalog.load()[0]['techniques']}
    own = {t['id'] for t in target.get('techniques', [])}
    family = VARIANT.sub('', ref)
    scored = []
    for candidate in references(home, wanted):
        if VARIANT.sub('', candidate['ref']) == family:
            continue
        if publishable_only and (candidate['layer'] != 'library' or candidate['licence']['code'] not in PUBLISHABLE):
            continue
        theirs = _signature_of(candidate, home)
        if theirs is None:
            continue
        # ponytail: brute force over every reference; fine to tens of thousands, index it if libraries grow past that
        distance = sum(ImageStat.Stat(ImageChops.difference(mine, theirs)).mean) / 3  # mean difference, 0-255
        scored.append((distance, candidate))
    scored.sort(key=lambda item: (item[0], item[1]['ref']))
    results = []
    for distance, candidate in scored[:limit]:
        likeness = max(0.0, 1 - distance / 64)  # 1 = the same layout of tones and colours; unrelated pictures ~0.3
        shared = [names[t['id']] for t in candidate.get('techniques', []) if t['id'] in own and t['id'] in names]
        reasons = [f'Similar placement of light, dark and colour ({round(likeness * 100)}% alike)']
        if shared:
            reasons.append(f"Also shows {', '.join(shared[:3])}")
        results.append({**_public(candidate), 'score': round(likeness, 3), 'reasons': reasons})
    return {'like': ref, 'results': results, 'compared': len(scored),
            'note': 'Compared by where light, dark and colour sit in each picture (an 8 x 8 thumbnail), on this '
                    'computer. It finds compositions that look alike, not the same subject.'}


OPEN_PROVIDERS = ('commons', 'met', 'aic', 'cma', 'rijksmuseum')  # live search APIs; NGA needs its large index


@lru_cache(maxsize=1)
def _fetcher_for(key: str):
    from atlas.fetch import Fetcher
    return Fetcher(json.loads(key))


def _shared_fetcher(policies: dict):
    """One fetcher per process, so a provider's Retry-After and pacing carry over between an agent's searches."""
    return _fetcher_for(json.dumps(policies, sort_keys=True))


def open_search(query: str, *, providers_wanted=None, per_provider: int = 6, fetcher=None) -> dict:
    """Search public collections live for a picture the library does not have. Each candidate goes through
    atlas/rights.py, as in Find; only eligible ones are returned, with licence and credit. Nothing is downloaded or
    stored: to keep one, import it with Find in the app. Network use is bounded: one search per collection (the
    Rijksmuseum also reads each result's linked records, about three requests per result)."""
    from atlas import providers, rights
    from atlas.fetch import FetchError
    if not isinstance(query, str) or not query.strip() or len(query) > 200:
        raise ValueError('the query is 1 to 200 characters of plain words (a subject, not a whole brief)')
    wanted = list(OPEN_PROVIDERS) if providers_wanted is None else _clean_list(providers_wanted, len(OPEN_PROVIDERS))
    if not wanted:
        raise ValueError('choose at least one collection, or leave the choice out to search them all')
    if any(p not in OPEN_PROVIDERS for p in wanted):
        raise ValueError(f"collections are {', '.join(OPEN_PROVIDERS)}")
    if not isinstance(per_provider, int) or not 1 <= per_provider <= 10:
        raise ValueError('per_provider is between 1 and 10')
    policies = catalog.load()[1]
    fetcher = fetcher or _shared_fetcher(policies)
    results, rejected, errors = [], {}, {}
    for provider in wanted:
        policy = catalog.policy(policies, provider)
        if policy.get('status') != 'enabled':
            errors[provider] = 'not enabled in source_policies.json'
            continue
        try:
            found = providers.search(fetcher, provider, query.strip(), 0, per_provider)
        except (FetchError, ValueError, KeyError, TypeError, AttributeError) as error:
            errors[provider] = getattr(error, 'code', None) or type(error).__name__
            continue
        for candidate in found:
            decision = rights.check(candidate, policy)
            if not decision['eligible']:
                rejected[decision['reason']] = rejected.get(decision['reason'], 0) + 1
                continue
            code = {'CC0': 'cc0', 'PD': 'pd', 'PDM': 'pd', 'CC BY': 'cc-by'}.get(decision['license_code'], 'unclear')
            results.append({
                'provider': provider, 'title': candidate.get('title', ''), 'creator': candidate.get('creator', ''),
                'date': candidate.get('date_text', ''), 'medium': candidate.get('medium', ''),
                'source_url': candidate['source_url'], 'image_url': candidate['image_url'],
                'licence': {'label': decision['label'], 'code': code, 'url': decision['license_url'],
                            'restrictions': decision['restrictions'], 'checked_by': 'atlas/rights.py'},
                'credit': decision['required_attribution'], 'publishable': code in PUBLISHABLE})
    return {'query': query.strip(), 'results': results, 'rejected': rejected, 'errors': errors,
            'note': 'Live results from public collections, licence-checked by atlas/rights.py from each record. No '
                    'technique reading yet: judge the picture yourself, and import it with Find to keep it. Labels '
                    'say what was checked; they are not legal advice.'}
