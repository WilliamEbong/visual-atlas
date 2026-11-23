# CLI on real briefs (2026-11-23)

Run with the v0.4 starter library (93 references) in a scratch home, design systems off, generated layer as committed at the time. Command: `uv run atlas advise "<brief>" --limit 4 --text`. No AI calls.

**Result:** 6 of 8 briefs read as at least one known goal or technique and returned credited references with reasons. Two did not: "Show how big the mountains are" (the goal *Show scale* has no cue for "how big") and "Group three related services" (no cue for "read as one family"). Those two fell back to subject words. That is the known recall limit of word matching (v0.4 held-out recall was 60%). It was left untuned because these are new test briefs, and tuning on them would hide the limit. Agents avoid it by passing technique or goal ids (`atlas refs --goal show-scale`), and people can use the guidance list. These are builder observations, not owner ratings; the blind test in BLIND-TEST.md is still owed.

## A calm opening slide for a talk about rest: one small figure in a lot of empty space

```
Reads as: Create calm and order, Negative space isolation, Scale contrast; subjects opening, rest

Negative space isolation: A subject is surrounded by a large, quiet, mostly empty area, so the emptiness itself frames it.

Scale contrast: Two things of very different apparent size appear together, so each makes the size of the other legible.

library:41  Alarums and Excursions — Maxfield Parrish (American, 1870–1966)
  library · CC0 — source checked
  · Shows Scale contrast (agreed by a second model): An enormous coiled serpent occupies the upper and right portions of the illustration; its open mouth and head l
  · Serves “Create calm and order” through Rhythm and pattern (agreed by a second model): Outlined polygonal scales repeat across the serpent's body, while broad tr
library:55  Floral Fantasy, "Fleurs de Gout" — Jean-Baptiste Pillement, French, 1728–1808
  library · CC0 — source checked
  · Shows Negative space isolation (agreed by a second model): A vertically arranged botanical illustration occupies the middle of a pale sheet, with broad empty ma
  · Serves “Create calm and order” through Rhythm and pattern (agreed by a second model): Three large sprays in the upper half have curved stems lined with closely 
library:64  Slovenian Sunset (7027587519) — whatleydude from London, United Kingdom
  library · Free with attribution — credit included
  · Shows Negative space isolation (agreed by a second model): A small boat with a person-shaped upright form occupies the lower-left portion of the image, surround
  · Serves “Create calm and order” through Silhouette (agreed by a second model): The boat and upright form are nearly black, with little interior detail, against o
library:67  Silhouette eines Steinwälzers — Stephan Sprinz
  library · Free with attribution — credit included
  · Shows Negative space isolation (agreed by a second model): A black bird shape stands right of center, with its bill pointing left; its head, body, legs and proj
  · Serves “Create calm and order” through Silhouette (agreed by a second model): A black bird shape stands right of center, with its bill pointing left; its head, 
```

## Make one product stand out on a dark poster

```
Reads as: Make one thing stand out; subjects product

Negative space isolation: A subject is surrounded by a large, quiet, mostly empty area, so the emptiness itself frames it.

Scale contrast: Two things of very different apparent size appear together, so each makes the size of the other legible.

Colour contrast: An area of one hue sits against a field of a strongly different hue — often complementary or warm against cool.

Light–dark contrast (chiaroscuro): The subject is much lighter or darker than its surroundings, often lit by a single strong source.

library:10  Interior of St. Mark's, Venice — David Dalhoff Neal
  library · CC0 — source checked
  · Serves “Make one thing stand out” through Scale contrast, Light–dark contrast (chiaroscuro) (agreed by a second model): Tall piers, arches, and vaults occupy mo
library:14  The Dreamer (La Rêveuse) — Jean Antoine Watteau
  library · CC0 — source checked
  · Serves “Make one thing stand out” through Light–dark contrast (chiaroscuro), Colour contrast (agreed by a second model): Dense, dark brown-green foliage fills t
library:15  Dream Vision — Odilon Redon
  library · CC0 — source checked
  · Serves “Make one thing stand out” through Light–dark contrast (chiaroscuro) (agreed by a second model): Dense dark crosshatching forms a large irregular mass ac
library:19  Joseph Telling His Dreams — Rembrandt van Rijn
  library · CC0 — source checked
  · Serves “Make one thing stand out” through Light–dark contrast (chiaroscuro) (agreed by a second model): A curly-haired standing figure near the center has a pal
```

## Show how big the mountains are for a travel talk

```
Reads as: no known goal or technique; subjects mountain, travel

library:4  Landscape: Beautiful Scenery Frozen in Mist — Li Shizhuo
  library · CC0 — source checked
  · Subject matches mountain
library:13  The Dream of Paris — Monogrammist PG
  library · CC0 — source checked
  · Subject matches mountain
library:84  Ronchamp17f.jpg - Flickr - scarletgreen — scarletgreen from Japan
  library · Free with attribution — credit included
  · Subject matches travel
```

## A surprising image for an essay about cities

```
Reads as: Surprise or provoke a second look; subjects essay, city

Repetition with interruption: A regular series of similar elements is broken by one element that differs in colour, direction, shape or position.

Tight cropping: The frame cuts close to or through the subject, showing only part of it or filling the whole picture with it.

Juxtaposition: Two unlike things are placed together so the viewer compares them and reads a relationship between them.

Figure–ground ambiguity: Shapes and the spaces between them are balanced so the viewer can read either as the subject, and the reading flips.

library:27  Then There Appears a Singular Being, Having the Head of a Man on the B — Odilon Redon (French, 1840–1916)
  library · CC0 — source checked
  · Serves “Surprise or provoke a second look” through Visual metaphor (agreed by a second model): A humanlike head in left-facing profile joins an elongated, curve
library:28  Everywhere Eyeballs are Aflame — Odilon Redon (French, 1840–1916)
  library · CC0 — source checked
  · Serves “Surprise or provoke a second look” through Contextual incongruity (agreed by a second model): An isolated eye-like oval floats above the midpoint, sligh
library:35  A floral fantasy of animals and birds (Waq-waq) — 
  library · CC0 — source checked
  · Serves “Surprise or provoke a second look” through Visual metaphor (agreed by a second model): Curving green stems branch across the tan field, carrying leaves,
library:58  Surrealism in photography 06 — Mostafameraji
  library · CC0 — source checked
  · Serves “Surprise or provoke a second look” through Unusual vantage point, Tight cropping (agreed by a second model): A person appears inverted near the center, 
```

## Lead the eye to the headline on a festival flyer

```
Reads as: Guide the eye, Leading lines; subjects festival

Leading lines: Lines in the scene — roads, rivers, walls, rails, edges of light — run toward the subject or deep into the picture.

library:12  The Dream of Saint Jerome — Matteo di Giovanni
  library · CC0 — source checked
  · Shows Leading lines (agreed by a second model): Red floor panels alternate with pale dividing strips; strips running into the room angle inward and the panels b
  · Serves “Guide the eye” through Rhythm and pattern (agreed by a second model): Repeated pale columns, rectangular wall panels, and dark upper openings with trian
library:17  Jacob's Dream — Raphael
  library · CC0 — source checked
  · Shows Leading lines (proposed by a model, not yet checked): A staircase rises behind the reclining figure toward the upper center, becoming narrower with smalle
  · Serves “Guide the eye” through Layered depth (foreground, middle, background) (agreed by a second model): A large reclining figure spans the lower portion, with
library:22  Fantastic Landscape — Francesco Guardi
  library · CC0 — source checked
  · Shows Leading lines (proposed by a model, not yet checked): The wall base and adjoining ground extend from the lower left toward the arch and figures near the c
  · Serves “Guide the eye” through Off-centre placement (agreed by a second model): A broken stone arch, tower, and long masonry wall occupy the lower left portion 
library:13  The Dream of Paris — Monogrammist PG
  library · CC0 — source checked
  · Serves “Guide the eye” through Layered depth (foreground, middle, background) (agreed by a second model): Five large adult figures fill the lower half: three pa
```

## A tense, unsettling cover for a thriller

```
Reads as: Create tension or unease

Light–dark contrast (chiaroscuro): The subject is much lighter or darker than its surroundings, often lit by a single strong source.

Tight cropping: The frame cuts close to or through the subject, showing only part of it or filling the whole picture with it.

Diagonal energy: The main lines or forms run diagonally across the frame instead of horizontally or vertically.

Unusual vantage point: The scene is seen from markedly above or below normal eye level.

library:14  The Dreamer (La Rêveuse) — Jean Antoine Watteau
  library · CC0 — source checked
  · Serves “Create tension or unease” through Light–dark contrast (chiaroscuro) (agreed by a second model): Dense, dark brown-green foliage fills the left side and 
library:15  Dream Vision — Odilon Redon
  library · CC0 — source checked
  · Serves “Create tension or unease” through Light–dark contrast (chiaroscuro) (agreed by a second model): Dense dark crosshatching forms a large irregular mass ac
library:16  Dream of Flogging — Francisco José de Goya y Lucientes
  library · CC0 — source checked
  · Serves “Create tension or unease” through Diagonal energy (agreed by a second model): Overlapping human figures form an elongated cluster running from the lower
library:19  Joseph Telling His Dreams — Rembrandt van Rijn
  library · CC0 — source checked
  · Serves “Create tension or unease” through Light–dark contrast (chiaroscuro) (agreed by a second model): A curly-haired standing figure near the center has a pal
```

## Group three related services so they read as one family

```
Reads as: no known goal or technique; subjects group, three, related, service, they, read

library:3  Mishima: Morning Mist (Mishima, asagiri), from the series "Fifty-three — Utagawa Hiroshige
  library · CC0 — source checked
  · Subject matches three, group
library:12  The Dream of Saint Jerome — Matteo di Giovanni
  library · CC0 — source checked
  · Subject matches group
library:13  The Dream of Paris — Monogrammist PG
  library · CC0 — source checked
  · Subject matches group
library:27  Then There Appears a Singular Being, Having the Head of a Man on the B — Odilon Redon (French, 1840–1916)
  library · CC0 — source checked
  · Subject matches three
```

## An image that suggests motion for a running club

```
Reads as: Suggest movement or energy, Implied motion; subjects running, club

Implied motion: A still image shows cues of movement — a pose mid-action, blur, flying material, or a moment just before or after an event.

library:11  The Fall of the Giants — Salvator Rosa
  library · CC0 — source checked
  · Shows Implied motion (agreed by a second model): Numerous human figures crowd among angular boulders across the lower three quarters of the image.
  · Serves “Suggest movement or energy” through Diagonal energy (agreed by a second model): Figures lean, twist, and lie across rocks with extended arms, bent legs,
library:12  The Dream of Saint Jerome — Matteo di Giovanni
  library · CC0 — source checked
  · Shows Implied motion (agreed by a second model): A bare-chested figure wearing a pale hip cloth stands near the center with bent legs and raised hands.
  · Serves “Suggest movement or energy” through Rhythm and pattern (agreed by a second model): Repeated pale columns, rectangular wall panels, and dark upper openin
library:16  Dream of Flogging — Francisco José de Goya y Lucientes
  library · CC0 — source checked
  · Shows Implied motion (agreed by a second model): The figures have tilted heads, bent limbs, extended arms, and loose garments with sweeping folds. Several feet 
  · Serves “Suggest movement or energy” through Diagonal energy (agreed by a second model): Overlapping human figures form an elongated cluster running from the low
library:41  Alarums and Excursions — Maxfield Parrish (American, 1870–1966)
  library · CC0 — source checked
  · Shows Implied motion (agreed by a second model): An enormous coiled serpent occupies the upper and right portions of the illustration; its open mouth and head l
  · Serves “Suggest movement or energy” through Rhythm and pattern (agreed by a second model): Outlined polygonal scales repeat across the serpent's body, while bro
```

