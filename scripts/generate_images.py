"""Maintainer script: generate the original teaching images in generated/ with Codex image generation.

Run from the repository root:

    uv run python scripts/generate_images.py prompts            # list image ids
    uv run python scripts/generate_images.py gen ID [ID ...]    # one image per id, 3 at a time
    uv run python scripts/generate_images.py build REVIEW.json  # kept images -> generated/*.jpg + manifest.json
    uv run python scripts/generate_images.py label              # (re)write the provenance label in every kept file

`gen` sends each prompt to the Codex plugin companion (`node codex-companion.mjs task --fresh`,
prompt on stdin) and copies the PNG it reports to the scratch folder (VA_GEN_SCRATCH, default
%TEMP%/va-gen) as <id>-v<n>.png. Generation uses the owner's Codex subscription; nothing is paid.

REVIEW.json is written by the reviewer after checking every image against generated/RUBRIC.md:
    {"kept": {"<id>": {"version": 1, "notes": "rubric notes"}},
     "dropped": [{"id": "<id>-v1", "technique": "...", "reason": "...", "prompt": "..."}]}
"""
import datetime
import glob
import json
import os
import re
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'generated'
SCRATCH = Path(os.environ.get('VA_GEN_SCRATCH') or Path(tempfile.gettempdir()) / 'va-gen')
TOOL = 'Codex image generation (ChatGPT image tool) via the Codex CLI'
LICENCE = ('Generated with Codex image generation for Visual Atlas. Not a photograph or artwork by a person. '
           'US copyright protection for AI-generated images is unsettled; no licence is asserted. '
           'Use as a reference for the technique.')

HEAD = ('Use your built-in image generation tool to generate exactly one image from the brief below. '
        'Do not write code, run shell commands or edit files. When the image is saved, reply with one line: '
        'the full local path of the saved image file.\n\nBRIEF\n')
AVOID = ('Avoid: any text, letters, numbers, signatures, logos or watermarks; real people, real landmarks and brands; '
         'glossy 3D-render look, HDR glow, oversaturated colour, fake lens flare; warped or melted objects.')

STUDIED = {
    'symmetry': [
        {'title': 'The Marriage of the Virgin (Lo Sposalizio)', 'creator': 'Raphael', 'date': '1504',
         'source_url': 'https://pinacotecabrera.org/en/collezioni/collezione-on-line/the-marriage-of-the-virgin/',
         'lesson': 'One structure on the vertical axis with the paving running to it; halves balanced in mass and tone.'},
        {'title': 'The Ideal City (Urbino panel)', 'creator': 'Formerly attributed to Piero della Francesca', 'date': 'c. 1480',
         'source_url': 'https://en.wikipedia.org/wiki/The_Ideal_City_(painting)',
         'lesson': 'Even frontal light and architecture mirrored about the centre make order and stillness read at once.'},
    ],
    'vantage-point': [
        {'title': 'Berlin Radio Tower', 'creator': 'László Moholy-Nagy', 'date': '1928',
         'source_url': 'https://www.artic.edu/artworks/55476/berlin-radio-tower',
         'lesson': 'Pointing straight down removes the horizon and turns the ground into a graphic map; low light makes it legible.'},
        {'title': 'The Boulevard Seen from Above', 'creator': 'Gustave Caillebotte', 'date': '1880',
         'source_url': 'https://nga.gov/features/slideshows/gustave-caillebotte.html',
         'lesson': 'Foreshortened tree, bench and passers-by seen from the top tell the viewer how high they stand.'},
    ],
    'proximity-grouping': [
        {'title': 'The Harvesters', 'creator': 'Pieter Bruegel the Elder', 'date': '1565',
         'source_url': 'https://www.metmuseum.org/art/collection/search/435809',
         'lesson': 'Reapers clustered under one tree with single workers apart: the gaps say who belongs together.'},
        {'title': 'A Sunday on La Grande Jatte — 1884', 'creator': 'Georges Seurat', 'date': '1884–86',
         'source_url': 'https://www.artic.edu/artworks/27992/a-sunday-on-la-grande-jatte-1884',
         'lesson': 'Groups set on an even, open ground so the empty intervals read as clearly as the figures.'},
    ],
    'figure-ground-ambiguity': [
        {'title': 'Sky and Water I', 'creator': 'M. C. Escher', 'date': '1938',
         'source_url': 'https://www.nga.gov/artworks/54215-sky-and-water-i',
         'lesson': 'Two flat tones of equal weight; the flip happens where shapes share every contour.'},
        {'title': "Rubin's vase demonstrations", 'creator': 'Edgar Rubin', 'date': '1915',
         'source_url': 'https://en.wikipedia.org/wiki/Rubin_vase',
         'lesson': 'A centred shape whose outer contour is recognisable from the other side flips most reliably; no shading.'},
    ],
    'selective-focus': [
        {'title': 'The Lacemaker', 'creator': 'Johannes Vermeer', 'date': 'c. 1669–70',
         'source_url': 'https://en.wikipedia.org/wiki/The_Lacemaker_(Vermeer)',
         'lesson': 'Soft foreground threads and crisp hands place the plane of focus exactly; blur in front as well as behind.'},
        {'title': 'Kate Keown', 'creator': 'Julia Margaret Cameron', 'date': '1866',
         'source_url': 'https://www.metmuseum.org/art/collection/search/286404',
         'lesson': 'Shallow focus and gentle side light: only sharpness, not colour or brightness, separates the subject.'},
    ],
    'leading-lines': [
        {'title': 'The Avenue at Middelharnis', 'creator': 'Meindert Hobbema', 'date': '1689',
         'source_url': 'https://en.wikipedia.org/wiki/The_Avenue_at_Middelharnis',
         'lesson': 'A road and two rows of trees run from the bottom edge to one point on the horizon; the eye travels the whole depth.'},
        {'title': 'Paris Street; Rainy Day', 'creator': 'Gustave Caillebotte', 'date': '1877',
         'source_url': 'https://en.wikipedia.org/wiki/Paris_Street;_Rainy_Day',
         'lesson': 'Kerb lines and building edges converge on a distant point, pulling the eye past the foreground figures.'},
    ],
    'tight-cropping': [
        {'title': "The Child's Bath", 'creator': 'Mary Cassatt', 'date': '1893',
         'source_url': 'https://en.wikipedia.org/wiki/The_Child%27s_Bath',
         'lesson': 'A high, close view cut at the frame edges puts the viewer inside the moment; nothing outside it competes.'},
    ],
    'gaze-direction': [
        {'title': 'Young Man at His Window', 'creator': 'Gustave Caillebotte', 'date': '1876',
         'source_url': 'https://en.wikipedia.org/wiki/Young_Man_at_His_Window',
         'lesson': 'A figure seen from behind looks out to the street, so the viewer looks where he looks.'},
        {'title': 'Girl with a Pearl Earring', 'creator': 'Johannes Vermeer', 'date': 'c. 1665',
         'source_url': 'https://en.wikipedia.org/wiki/Girl_with_a_Pearl_Earring',
         'lesson': 'A turned head and sideways eyes make a direction and a question; the gaze is the subject.'},
    ],
    'contextual-incongruity': [
        {'title': 'The Song of Love', 'creator': 'Giorgio de Chirico', 'date': '1914',
         'source_url': 'https://en.wikipedia.org/wiki/The_Song_of_Love',
         'lesson': 'Ordinary objects, each painted plainly, placed where they do not belong; the mismatch alone makes the second look.'},
    ],
}

# id: technique, title, medium, colour, subjects, notes, brief
IMAGES = {
    'symmetry-01': dict(
        technique='symmetry', title='Boathouse on a still lake', colour='muted',
        medium='generated photograph-style image (medium-format colour film look)',
        subjects=['boathouse', 'lake', 'reflection', 'mountains'],
        notes='A small timber boathouse sits on the vertical centre line, its gable apex on the axis; the dead-calm water mirrors it, giving a second, horizontal axis at the waterline.',
        brief='A fine-art photograph on medium-format colour film, soft overcast dawn light, quiet muted colours. '
              'A small old timber boathouse with a steep pitched roof stands on short stilts at the edge of a mountain lake, '
              'seen dead-on from the front from water level. The apex of the gable sits exactly on the vertical centre line of the frame, '
              'the open boat door is centred beneath it, and two identical small square windows sit either side. '
              'Behind it, dark conifer slopes rise evenly on both sides to a pale sky. The water is perfectly still and mirrors the boathouse '
              'and slopes exactly, so the waterline is a second, horizontal axis across the middle of the frame. '
              'Left and right halves balance in shape, mass and tone. Square format. No people, no boats.'),
    'symmetry-02': dict(
        technique='symmetry', title='Glasshouse aisle', colour='muted',
        medium='generated photograph-style image (black-and-white film look)',
        subjects=['glasshouse', 'palms', 'iron architecture', 'aisle'],
        notes='One-point view down the centre aisle of an iron glasshouse; arched ribs, palms and benches mirror left and right about the central path.',
        brief='A fine-art black-and-white film photograph, fine grain, soft diffuse daylight through glass. '
              'An imaginary Victorian iron-and-glass palm house, seen from the exact centre of its main aisle at standing height, looking straight down the aisle. '
              'The tiled path runs from the bottom centre to a round arched doorway at the far end, exactly on the vertical centre line. '
              'Curved white iron ribs arch overhead in matching pairs; tall palms in identical large pots stand in mirrored pairs on both sides, '
              'with low planting beds either side of the path. The left and right halves mirror each other closely in shape and tone. '
              'Slight natural variation in the leaves only. Portrait format 4:5. No people.'),
    'vantage-point-01': dict(
        technique='vantage-point', title='Looking straight up through pines', colour='mono',
        medium='generated photograph-style image (black-and-white film look)',
        subjects=['pine trees', 'forest', 'sky'],
        notes="A worm's-eye view: tall pine trunks rise from every edge of the frame and converge toward a small patch of sky in the centre; no horizon.",
        brief="A fine-art black-and-white film photograph with fine grain, taken lying on the forest floor with a wide lens pointing straight up. "
              'Tall straight pine trunks rise from all four edges of the frame and converge steeply toward the centre, where their crowns '
              'leave an irregular patch of pale overcast sky. The trunks are strongly foreshortened: wide and textured with bark at the edges, '
              'thin and small near the centre. There is no horizon and no ground visible. Bright sky against dark trunks, rich mid-greys in the bark. '
              'Square format. No people, no animals.'),
    'vantage-point-02': dict(
        technique='vantage-point', title='Harbour quay from above', colour='muted',
        medium='generated photograph-style image (colour film look)',
        subjects=['harbour', 'boats', 'quay', 'water'],
        notes="Bird's-eye view looking nearly straight down on a small harbour: boats seen as hull outlines, a figure foreshortened to a head and shoulders, long early shadows; no horizon.",
        brief='A fine-art colour film photograph, muted palette, low early-morning sun from the left casting long shadows. '
              'Seen from very high above, looking almost straight down onto a small stone quay in a fishing harbour. No horizon and no sky. '
              'The quay edge runs diagonally across the frame; half a dozen small wooden rowing and fishing boats are moored in the dark green water '
              'below it, seen from directly above as clean hull outlines with their oars and coiled ropes. On the quay, a single small figure in a dark coat '
              'is seen from the top as a head and shoulders with a long shadow stretching across the paving stones; a few stacked crates and a bollard '
              'also cast long shadows. The ground plane reads as a flat graphic pattern. Portrait format 4:5. No text or numbers on the boats.'),
    'proximity-grouping-01': dict(
        technique='proximity-grouping', title='Swallows on a wire', colour='mono',
        medium='generated photograph-style image (black-and-white film look)',
        subjects=['birds', 'swallows', 'wire', 'sky'],
        notes='Identical swallows on one wire, grouped only by spacing: a tight cluster of five at left, three at centre-right, and one bird alone near the right edge.',
        brief='A fine-art black-and-white film photograph, fine grain, soft overcast light. A single thin wire crosses the frame horizontally, slightly below the middle, '
              'against a plain pale-grey sky. Nine swallows of the same size and pose sit on the wire, all facing the same way, seen in profile as dark silhouettes '
              'with forked tails. Spacing does all the work: five birds sit almost touching in a tight cluster in the left third; a wide empty stretch of wire; '
              'three birds sit close together just right of centre; another wide gap; one single bird sits alone near the right edge. '
              'All birds look alike so only distance separates the groups. Exactly nine birds. Landscape 3:2. Nothing else in the frame.'),
    'proximity-grouping-02': dict(
        technique='proximity-grouping', title='Figures on a winter beach', colour='muted',
        medium='generated painterly illustration (gouache look)',
        subjects=['beach', 'figures', 'sea', 'winter'],
        notes='Small, similar figures on an even stretch of sand form a group of four, a pair, and one figure standing apart at the water’s edge; spacing alone sets the groups.',
        brief='A painterly gouache illustration with flat, matte colour and visible paper texture, muted winter palette of sand, slate blue and off-white, soft overcast light. '
              'Seen from a high dune looking down at a wide, empty, even beach with the sea along the top of the picture. On the sand stand small figures in similar '
              'dark winter coats, all roughly the same size, seen from behind or in simple silhouette with no facial detail: four figures stand close together in a huddle '
              'in the lower left; two stand side by side in the middle distance at centre; one single figure stands alone at the far right by the water’s edge. '
              'Wide empty sand separates the groups. Each figure casts a short soft shadow. Landscape 3:2. Exactly seven figures, no animals.'),
    'fg-ambiguity-01': dict(
        technique='figure-ground-ambiguity', title='Tree or two deer', colour='mono',
        medium='generated cut-paper style illustration',
        subjects=['tree', 'deer', 'positive and negative shape'],
        notes='A cream tree on black: the black spaces either side of the trunk, under the canopy, are two deer heads in profile facing each other, sharing the trunk’s contour.',
        brief='A flat two-tone cut-paper illustration: only cream paper and solid black, no shading, gradients or texture beyond a faint paper grain. '
              'A single cream tree stands in the centre: a broad rounded canopy across the top and a trunk down the middle to a cream ground strip at the bottom. '
              'The two black spaces either side of the trunk, between the canopy and the ground, are shaped precisely as two deer heads in profile facing each other '
              'across the trunk: the trunk’s left and right edges are the deer’s foreheads, noses and chins; small ears and short antlers rise into the underside of the canopy; '
              'their necks run down to the outer edges. One small cream dot marks each deer eye. Cream and black occupy roughly equal areas, so the eye flips between '
              'reading a cream tree and two black deer. Symmetrical, centred, square format.'),
    'fg-ambiguity-02': dict(
        technique='figure-ground-ambiguity', title='Counterchanged pears', colour='muted',
        medium='generated screenprint-style illustration',
        subjects=['pears', 'counterchange', 'positive and negative shape'],
        notes='The frame is split down the middle; a pear that straddles the split is indigo on the cream half and cream on the indigo half, so figure and ground swap along one shared contour.',
        brief='A flat two-colour screenprint illustration in deep indigo and warm cream only, no shading, gradients or outlines, faint paper grain. '
              'The frame is divided exactly down the vertical centre: the left half is cream, the right half is indigo. '
              'One large upright pear with a short stem and a single leaf sits exactly on the dividing line, so half the pear lies on each side. '
              'The colours are counterchanged: on the cream left half, the left half of the pear is solid indigo; on the indigo right half, the right half of the pear is solid cream. '
              'The pear outline is one continuous, symmetrical contour, so on the left the pear is the figure and on the right the pear is the ground, and the eye flips '
              'between reading a pear and reading two pear-shaped holes. The leaf follows the same rule. Nothing else in the picture. Square format.'),
    'selective-focus-01': dict(
        technique='selective-focus', title='Seed head in a meadow', colour='muted',
        medium='generated photograph-style image (colour film look)',
        subjects=['seed head', 'meadow', 'grasses'],
        notes='Only the dry seed head is sharp; grass stems in front of it and the meadow behind dissolve into smooth blur with soft discs of light.',
        brief='A fine-art colour film photograph, muted greens and straw, low warm evening side light. A macro lens at its widest aperture. '
              'A single dry, spherical seed head on a thin stem stands just right of centre, in razor-sharp focus: every fine filament and seed is crisp. '
              'Out-of-focus grass stems cross the foreground as soft translucent streaks, and the meadow behind dissolves into smooth, creamy blur with a few soft round '
              'discs of light. The seed head has the same light and colour as everything around it; only sharpness separates it. '
              'Natural optical blur, no cut-out edges around the subject. Portrait 4:5.'),
    'selective-focus-02': dict(
        technique='selective-focus', title='Teapot on a table', colour='muted',
        medium='generated painterly illustration (oil painting look)',
        subjects=['teapot', 'table', 'still life', 'interior'],
        notes='The teapot is painted with tight, precise strokes; the cups in front and the room behind are broad, loose and blurred, so handling alone draws the eye.',
        brief='An oil painting of a quiet interior still life in soft north window light from the left, muted ochres, greys and blue-white. '
              'A blue-and-white glazed ceramic teapot on a plain wooden table, slightly left of centre, is painted with tight, precise, crisp detail: the glaze highlight, '
              'the lid knob, the curve of the spout, a fine crack line in the glaze. Everything else is painted loosely: two teacups in the near foreground are soft '
              'smudged shapes of colour, and the room behind (a window, a chair, a dresser) dissolves into broad, blurry, sketchy strokes with lost edges. '
              'The teapot is not brighter or more saturated than its surroundings; only the sharpness of the handling sets it apart. Landscape 4:3. No people.'),
    'leading-lines-01': dict(
        technique='leading-lines', title='Boardwalk across a salt marsh', colour='muted',
        medium='generated photograph-style image (medium-format colour film look)',
        subjects=['boardwalk', 'salt marsh', 'hut', 'dusk'],
        notes='The plank boardwalk starts wide at the bottom edge and narrows straight to a small hut on the horizon, so both rails and the plank lines carry the eye to it.',
        brief='A fine-art photograph on medium-format colour film, calm dusk light, muted greens and soft violet sky. '
              'A straight timber boardwalk with a simple rail on each side starts wide across the whole bottom edge of the frame '
              'and runs dead straight away from the viewer across a flat salt marsh, narrowing to a single point on the horizon. '
              'Exactly at that point sits one small weathered wooden hut, the only built thing in view. The plank lines, both rails '
              'and the edges of the walk all converge on the hut. Viewpoint low and centred, a little above the planks. '
              'Wide empty marsh grass on both sides, a low horizon about a third of the way down the frame, a quiet pale sky.'),
    'leading-lines-02': dict(
        technique='leading-lines', title='Vine rows to a farmhouse', colour='muted',
        medium='generated gouache-style illustration',
        subjects=['vineyard', 'rows', 'farmhouse', 'hills'],
        notes='Curved vine rows sweep from the lower left foreground up the slope and all end at a small white farmhouse high on the right.',
        brief='A gouache illustration with flat matte colour and visible brush texture, late-summer afternoon light, ochre, olive and dusty blue. '
              'A rolling hillside vineyard: long parallel rows of vines start large in the lower left foreground and sweep in gentle curves '
              'up and across the slope, narrowing with distance, so every row ends at one small white farmhouse with a terracotta roof '
              'set high on the right third of the picture. Nothing else competes: no people, no vehicles, a plain pale sky. '
              'The rows are clear stripes of green vine and ochre earth so their direction reads at once.'),
    'tight-cropping-01': dict(
        technique='tight-cropping', title='Bow of a fishing boat', colour='muted',
        medium='generated photograph-style image (medium-format colour film look)',
        subjects=['fishing boat', 'peeling paint', 'rope', 'texture'],
        notes='The weathered bow fills the frame and is cut by all four edges; only painted planks, a rope and rivets remain, so the boat is felt rather than shown.',
        brief='A fine-art close-up photograph on medium-format colour film, soft overcast light. An extremely tight crop of the bow of an old '
              'wooden fishing boat: the curved painted planks fill the entire frame and run out past all four edges, so the whole boat is never seen. '
              'Faded blue paint peels to show red undercoat and grey wood; a thick coil of rope crosses the lower right corner and is cut off by the frame; '
              'a short row of rust-streaked iron rivets runs diagonally. No sky, no water, no background at all. Rich but muted colour, fine detail in the paint.'),
    'tight-cropping-02': dict(
        technique='tight-cropping', title='Figs in a bowl, cropped close', colour='vivid',
        medium='generated photograph-style image (medium-format colour film look)',
        subjects=['figs', 'bowl', 'fruit', 'table'],
        notes='Seen from directly above, the bowl rim runs out of the frame on three sides and the figs press to the edges; one split fig sits just off centre.',
        brief='A fine-art food photograph on medium-format colour film, seen from directly above, soft window light from the left. '
              'A shallow glazed ceramic bowl heaped with ripe purple figs, cropped so tightly that the bowl rim leaves the frame on the top, left and bottom edges '
              'and the figs press right up against the frame. One fig, cut in half to show its pink seeded inside, sits just right of centre. '
              'No table, cloth or background visible beyond a sliver at the right edge. Deep purples, green stems, pink flesh, a cream glaze.'),
    'gaze-direction-01': dict(
        technique='gaze-direction', title='Fox looking out of frame', colour='muted',
        medium='generated photograph-style image (medium-format colour film look)',
        subjects=['fox', 'snow', 'winter', 'field'],
        notes='A red fox sits in the left third with its head turned sharply to the right, ears forward; the open snow to the right and the frame edge are where the eye goes.',
        brief='A fine-art wildlife photograph on medium-format colour film, soft grey winter light. A red fox sits upright in a smooth snowfield, '
              'placed in the left third of a wide landscape frame. Its body faces the viewer but its head is turned sharply to the right, '
              'ears pricked forward, eyes fixed on something beyond the right edge of the picture that is not shown. The right two thirds are empty, '
              'even snow with a faint line of bare birch trunks far behind. The fox is sharp and correctly formed: four legs, one tail, natural fur.'),
    'gaze-direction-02': dict(
        technique='gaze-direction', title='Two climbers looking up', colour='muted',
        medium='generated gouache-style illustration',
        subjects=['climbers', 'cliff', 'mountain', 'rope'],
        notes='Two small climbers at the foot of the frame both look up and to the left; their raised heads and a pointing arm send the eye up the rock face to a pale ledge.',
        brief='A gouache illustration with flat matte colour and simple shapes, cool morning light, slate blue, grey and a single warm orange. '
              'Two small climbers in orange jackets stand at the bottom right of the picture at the foot of a tall grey rock face that fills the frame. '
              'Both tilt their heads back and look up and to the left; one points up with an outstretched arm. High on the upper left, a small pale ledge '
              'catches the light where they are looking. Figures are simple and clear (no faces needed): their posture and head direction carry the look.'),
    'incongruity-01': dict(
        technique='contextual-incongruity', title='Dinner table in the surf', colour='muted',
        medium='generated photograph-style image (medium-format colour film look)',
        subjects=['dinner table', 'sea', 'beach', 'dawn'],
        notes='A formally laid table with white linen, silver and candles stands in shallow surf on an empty beach; each object is ordinary, the place is wrong.',
        brief='A fine-art photograph on medium-format colour film, pale dawn light, muted blues and cream. On an empty sandy beach, a long dining table '
              'laid formally for eight (white linen cloth, white plates, polished cutlery, stemmed glasses and two unlit silver candlesticks, with plain wooden chairs) '
              'stands in shallow surf: a thin sheet of sea water runs around the table and chair legs. Everything on the table is neat and dry, as if waiting for guests. '
              'No people. Calm sea to the horizon, an even sky. Shot straight on from the side of the table at seated eye level.'),
    'incongruity-02': dict(
        technique='contextual-incongruity', title='Reading chair in a wheat field', colour='muted',
        medium='generated photograph-style image (medium-format colour film look)',
        subjects=['armchair', 'lamp', 'wheat field', 'summer'],
        notes='A worn velvet armchair, a side table with a book and a lit standard lamp stand in the middle of a ripe wheat field at noon.',
        brief='A fine-art photograph on medium-format colour film, bright high summer noon light, golden wheat and deep blue sky. '
              'In the middle of a wide ripe wheat field stands a worn green velvet armchair, a small wooden side table with an open book and a cup, '
              'and a tall standard lamp with a fabric shade that is switched on and glowing weakly in daylight, its flex trailing into the wheat. '
              'The wheat reaches the seat of the chair. No people, no house in sight, a flat horizon. Everything else is ordinary and real.'),
    'fg-ambiguity-03': dict(
        technique='figure-ground-ambiguity', title='Pawn or two faces', colour='muted',
        medium='generated screenprint-style illustration',
        subjects=['chess pawn', 'faces', 'positive and negative shape'],
        notes='A cream chess pawn stands in the centre of a dark green field; the green spaces either side are two human profiles facing each other, sharing the pawn\'s contours.',
        brief='A flat two-colour screenprint illustration in dark bottle green and warm cream only, no shading, gradients or outlines, faint paper grain. '
              'A single tall cream chess pawn stands upright in the exact centre, filling the full height of the frame, on a dark green ground. '
              'Its left and right contours are drawn so that the two green spaces beside it read equally as two human faces in profile facing each other: '
              'the pawn\'s round head forms the space between two foreheads, its neck collar the noses, its narrow waist the lips and chins, its wide base the necks and shoulders. '
              'Both readings must be equally strong: a pawn, or two faces nearly touching. Perfectly symmetrical, nothing else in the picture.'),
}


def prompt(image_id: str) -> str:
    return HEAD + IMAGES[image_id]['brief'] + '\n\n' + AVOID + '\n'


def companion() -> Path:
    """The highest installed version of the Codex plugin companion."""
    found = glob.glob(str(Path.home() / '.claude/plugins/cache/openai-codex/codex/*/scripts/codex-companion.mjs'))
    if not found:
        sys.exit('codex companion not found: install the codex plugin')
    def ver(p):
        return [int(x) if x.isdigit() else -1 for x in re.split(r'[.-]', Path(p).parents[1].name)]
    return Path(max(found, key=ver))


def gen_one(image_id: str):
    from PIL import Image
    r = subprocess.run(['node', str(companion()), 'task', '--fresh'], input=prompt(image_id),
                       capture_output=True, text=True, encoding='utf-8', timeout=1500)
    pattern = r'(?:[A-Za-z]:[\\/]|/)[^\s`"\'<>|*?]+?\.png'
    found = [p for p in re.findall(pattern, r.stdout) or re.findall(pattern, r.stderr) if os.path.exists(p)]
    if not found:
        return image_id, 'FAILED', (r.stdout + r.stderr)[-400:].replace('\n', ' ')
    n = 1
    while (SCRATCH / f'{image_id}-v{n}.png').exists():
        n += 1
    dst = SCRATCH / f'{image_id}-v{n}.png'
    Image.open(found[-1]).save(dst)
    return image_id, str(dst), Image.open(dst).size


def build(review_path: str):
    from PIL import Image
    review = json.loads(Path(review_path).read_text(encoding='utf-8'))
    images = []
    for image_id, rv in review['kept'].items():
        meta = IMAGES[image_id]
        im = Image.open(SCRATCH / f"{image_id}-v{rv['version']}.png").convert('RGB')
        im.thumbnail((1024, 1024), Image.LANCZOS)
        im.save(OUT / f'{image_id}.jpg', quality=85, optimize=True, progressive=True)
        images.append({
            'id': image_id, 'file': f'{image_id}.jpg', 'title': meta['title'], 'tool': TOOL,
            'date': rv.get('date') or datetime.date.today().isoformat(), 'medium': meta['medium'],
            'subjects': meta['subjects'], 'techniques': [meta['technique']], 'colour': meta['colour'],
            'notes': meta['notes'], 'width': im.width, 'height': im.height, 'prompt': prompt(image_id),
            'studied': STUDIED[meta['technique']],
            'review': {'rubric': 'generated/RUBRIC.md', 'result': 'pass',
                       'checked_by': 'Claude (Opus) by eye, full size', 'notes': rv['notes']},
        })
        print(image_id, im.size, (OUT / f'{image_id}.jpg').stat().st_size, 'bytes')
    old = json.loads((OUT / 'manifest.json').read_text(encoding='utf-8')) if (OUT / 'manifest.json').exists() else {}
    kept = {image['id'] for image in images}  # a later batch adds to the manifest; re-kept ids are replaced
    images = [i for i in old.get('images', []) if i['id'] not in kept] + images
    dropped = old.get('dropped', []) + [d for d in review['dropped'] if d not in old.get('dropped', [])]
    manifest = {'version': 1, 'licence_note': LICENCE, 'images': images, 'dropped': dropped}
    (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


SOURCE_TYPE = 'http://cv.iptc.org/newscodes/digitalsourcetype/trainedAlgorithmicMedia'


def xmp_label(item: dict) -> bytes:
    """IPTC/XMP provenance: 'made by a trained algorithm', the tool, the date and where the prompt is kept. This is
    the IPTC digital source type that C2PA and photo tools read; it is a plain label, not a signed C2PA manifest."""
    from xml.sax.saxutils import escape
    text = escape(f"Generated image for Visual Atlas ({item['tool']}, {item['date']}). Not a photograph or an "
                  f"artwork from a collection. Prompt and review: generated/manifest.json, id {item['id']}.")
    return ('<?xpacket begin="" id="W5M0MpCehiHzreSzNTczkc9d"?><x:xmpmeta xmlns:x="adobe:ns:meta/">'
            '<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"><rdf:Description rdf:about="" '
            'xmlns:Iptc4xmpExt="http://iptc.org/std/Iptc4xmpExt/2008-02-29/" xmlns:dc="http://purl.org/dc/elements/1.1/" '
            f'xmlns:xmp="http://ns.adobe.com/xap/1.0/" Iptc4xmpExt:DigitalSourceType="{SOURCE_TYPE}" '
            f'xmp:CreatorTool="{escape(item["tool"])}" xmp:CreateDate="{item["date"]}">'
            f'<dc:description><rdf:Alt><rdf:li xml:lang="x-default">{text}</rdf:li></rdf:Alt></dc:description>'
            '</rdf:Description></rdf:RDF></x:xmpmeta><?xpacket end="r"?>').encode('utf-8')


def embed_label(path: Path, item: dict):
    """Insert (or replace) the XMP segment without re-encoding the picture."""
    data = path.read_bytes()
    assert data[:2] == b'\xff\xd8', f'{path} is not a JPEG'
    header = b'http://ns.adobe.com/xap/1.0/\x00'
    segments, i = [], 2
    while data[i] == 0xFF and data[i + 1] in range(0xE0, 0xF0) or data[i + 1] == 0xFE:  # APPn and comments
        length = int.from_bytes(data[i + 2:i + 4], 'big')
        segment = data[i:i + 2 + length]
        if not (data[i + 1] == 0xE1 and segment[4:4 + len(header)] == header):  # drop an old XMP label
            segments.append(segment)
        i += 2 + length
    payload = header + xmp_label(item)
    xmp = b'\xff\xe1' + (len(payload) + 2).to_bytes(2, 'big') + payload
    path.write_bytes(b'\xff\xd8' + b''.join(segments[:1]) + xmp + b''.join(segments[1:]) + data[i:])


def label():
    for item in json.loads((OUT / 'manifest.json').read_text(encoding='utf-8'))['images']:
        embed_label(OUT / item['file'], item)
        print('labelled', item['file'])


def _selfcheck():
    assert all(re.fullmatch(r'[a-z0-9-]+', k) for k in IMAGES)
    assert all(v['technique'] in STUDIED for v in IMAGES.values())


if __name__ == '__main__':
    _selfcheck()
    cmd, args = (sys.argv[1], sys.argv[2:]) if len(sys.argv) > 1 else ('', [])
    if cmd == 'prompts':
        print('\n'.join(f"{k}  ({v['technique']})" for k, v in IMAGES.items()))
    elif cmd == 'gen' and args:
        unknown = [a for a in args if a not in IMAGES]
        if unknown:
            sys.exit(f'unknown ids: {unknown}')
        SCRATCH.mkdir(parents=True, exist_ok=True)
        with ThreadPoolExecutor(3) as pool:
            for res in pool.map(gen_one, args):
                print(*res, flush=True)
    elif cmd == 'build' and len(args) == 1:
        build(args[0])
        label()
    elif cmd == 'label':
        label()
    else:
        sys.exit(__doc__)
