"""Request coding: tag a brief or a Find request with codes from the taxonomy, without AI.

The taxonomy is the codebook (as in qualitative coding with the owner's Qualia app): each technique and goal is a
code with a name and include terms (aliases). A request is tagged with every code whose terms it uses, each tag
keeping the words that triggered it, so the reading can be shown and corrected. 'exact' tags come from a full name
or alias (or a choice in the form); single distinctive words give weaker, non-exact tags."""

import re

STOPWORDS = set("""a an and are as at be but by for from how i images image in into is it its me my of on or our show
showing some that the their them this to use used using want we with you your find need picture pictures photo
photos something like look looks feel feels should would could make making made create build suggest guide one
very more most less lot lots about over under than then there these those what when where which while who will
can may might also just only into onto off out up down any each every other another such own same so too again
poster posters slide slides cover page website site logo banner talk event project brief audience people person
family families adult adults top bottom small large big title date sponsor sponsors format portrait landscape
against flyer leaflet brochure booklet invitation programme program album sleeve newsletter campaign hero spread zine
post opener""".split())
GENERIC = STOPWORDS | {'contrast', 'balance', 'view', 'space', 'frame', 'pattern', 'colour', 'light', 'line', 'thing',
                       'stand', 'order', 'size', 'idea', 'visible', 'together', 'belong', 'point', 'direction', 'ground',
                       'figure', 'middle', 'background', 'foreground', 'central', 'energy', 'focus', 'perspective',
                       'depth', 'visual', 'dark', 'within', 'tight', 'limited', 'unusual', 'part', 'parts', 'viewer'}


def _singular(token: str) -> str:
    if len(token) > 4 and token.endswith('ies'):
        return token[:-3] + 'y'
    if len(token) > 4 and token.endswith('s') and not token.endswith(('ss', 'us', 'is')):
        return token[:-1]
    return token


def words(text: str) -> list[str]:
    """Lower-case word tokens, British spelling of colour, simple plural folding (lines -> line, skies -> sky)."""
    text = (text or '').lower().replace('color', 'colour').replace('centered', 'centred').replace('center', 'centre')
    text = re.sub(r"['’]s\b", '', re.sub(r'[-–_/]', ' ', text))
    return [_singular(token) for token in re.findall(r'[a-z]+', text)]


def _phrases(technique: dict) -> list[str]:
    name = re.split(r'[(]', technique['name'])[0]
    terms = [name, technique['id'].replace('-', ' '), *technique.get('aliases', [])]
    terms += re.findall(r'\(([^)]+)\)', technique['name'])  # "Light–dark contrast (chiaroscuro)" -> chiaroscuro
    return [' '.join(words(term)) for term in terms if words(term)]


def _distinctive(entries: dict[str, list[str]]) -> dict[str, str]:
    """word -> the only code whose terms use it (shared or generic words tag nothing on their own)."""
    owners: dict[str, set] = {}
    for code, texts in entries.items():
        for text in texts:
            for word in words(text):
                if len(word) >= 4 and word not in GENERIC:
                    owners.setdefault(word, set()).add(code)
    return {word: next(iter(codes)) for word, codes in owners.items() if len(codes) == 1}


def _cues(codes: list[dict], joined: str, found: dict[str, dict], used: set[str]):
    """Descriptive phrases from the codebook ("backlit" for silhouette): weaker than a name, so never exact."""
    for code in codes:
        for cue in code.get('request_cues', []):
            phrase = ' '.join(words(cue))
            if phrase and f' {phrase} ' in joined and code['id'] not in found:
                found[code['id']] = {'id': code['id'], 'exact': False, 'why': f'“{cue}”'}
                used.update(phrase.split())


def code_request(text: str, taxonomy: dict, technique_ids=(), goal_ids=(), subject: str = '') -> dict:
    """{'techniques': [{id, exact, why}], 'goals': [{id, exact, why}], 'subject_terms': [...]} for a request."""
    tokens = words(f'{text} {subject}')
    joined = f" {' '.join(tokens)} "
    used: set[str] = set()
    techniques: dict[str, dict] = {}
    for technique_id in technique_ids:
        techniques[technique_id] = {'id': technique_id, 'exact': True, 'why': 'chosen in the form'}
    for technique in taxonomy['techniques']:
        for phrase in _phrases(technique):
            if f' {phrase} ' in joined and technique['id'] not in techniques:
                techniques[technique['id']] = {'id': technique['id'], 'exact': True, 'why': f'“{phrase}”'}
                used.update(phrase.split())
    single = _distinctive({t['id']: [re.split(r'[(]', t['name'])[0], *re.findall(r'\(([^)]+)\)', t['name'])]
                           for t in taxonomy['techniques']})  # single words come from names only
    for token in tokens:
        if token in single and single[token] not in techniques:
            techniques[single[token]] = {'id': single[token], 'exact': False, 'why': f'“{token}”'}
            used.add(token)
    _cues(taxonomy['techniques'], joined, techniques, used)
    goals: dict[str, dict] = {g: {'id': g, 'exact': True, 'why': 'chosen in the form'} for g in goal_ids}
    _cues(taxonomy['goals'], joined, goals, used)
    goal_words = _distinctive({g['id']: [g['name'], g['description']] for g in taxonomy['goals']})
    for token in tokens:
        if token in goal_words and goal_words[token] not in goals:
            goals[goal_words[token]] = {'id': goal_words[token], 'exact': False, 'why': f'“{token}”'}
            used.add(token)
    subject_terms = []
    for token in words(subject) + tokens:
        if len(token) > 2 and token not in STOPWORDS and token not in used and token not in subject_terms:
            subject_terms.append(token)
    return {'techniques': list(techniques.values()), 'goals': list(goals.values()), 'subject_terms': subject_terms[:8]}
