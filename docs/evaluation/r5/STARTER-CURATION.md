# Starter curation, r5: museum works replace stock snapshots

Checked 2026-11-23. **102 references, down from 104: sixteen stock snapshots removed, fourteen museum and archive
works added, all proposed.** Nineteen display titles were also cleaned. This is a builder/model curatorial judgment,
not independent expert ground truth. It follows the procedure in [../v0.4/CURATION.md](../v0.4/CURATION.md) and
[../r2/typography/CURATION.md](../r2/typography/CURATION.md): the same search helper (`scripts/curate_v04.py`), the same
rights path, the same evidence standard and the same analysis contract.

## Why

The pack is meant to be a curated archive. Sixteen references were stock snapshots from Commons/Flickr: sunsets,
backlit keyboards, "odd one out" photos and a hackathon shot. They carried almost all of the silhouette and
odd-one-out coverage, and most of the tight-cropping and selective-focus coverage, with weak teaching value and
file-name titles. This round removes them and replaces that coverage with works from museums (Met, AIC, Cleveland)
and public-domain scans on Commons.

## Removed

All sixteen were `commons` items; their records and their analysis and thumbnail copies were deleted.

| Removed | Licence | Labels it carried |
|---|---|---|
| Sunset over Trommekilen from Norrkila 6 | CC0 | colour harmony, layered depth, silhouette |
| Slovenian Sunset (7027587519) | CC BY | colour contrast, negative space, silhouette |
| Frigate Bird Silhouette Against St Lucia Sunset 5738 | CC BY | implied motion, silhouette |
| Frigate Bird Silhouette Against St Lucia Sunset 5746 | CC BY | colour contrast, silhouette |
| Silhouette eines Steinwälzers | CC BY | negative space, selective focus, silhouette |
| Backlit Margarita Island Sunset in Las Guevaras | CC0 | asymmetric balance, silhouette |
| Sidney Ken Backlit Sunset | CC0 | selective focus, silhouette |
| Backlit Laptop Keyboard | CC0 | rhythm, tight cropping, vantage point |
| Backlit laptop keyboard (Unsplash) | CC0 | rhythm, selective focus, tight cropping |
| Spot the odd one out (5322927182) | CC BY | repetition with interruption, value contrast |
| Odd one out (29633471507) | CC BY | colour contrast, proximity, repetition with interruption |
| Odd One Out (2875941109) | CC BY | colour contrast, juxtaposition |
| Odd one out (15828284123) | CC BY | colour contrast, repetition with interruption, symmetry |
| Odd one out (6097084986) | CC BY | repetition with interruption, tight cropping |
| Spot the odd one out (49622539126) | CC BY | layered depth, repetition with interruption, tight cropping |
| MA9 Mashup Camp Maker Hackathon Odaiba Mono (9333975564) | CC BY | leading lines, repetition with interruption |

## Added

Every accepted file was downloaded through the app and opened as actual pixels in this session.
[starter-additions.json](starter-additions.json) holds the observations, proposed effects, teaching value and
ambiguity for each; the same text is validated with `tasks.validate_analysis` and stored in the starter as the reading.

| Example | Technique (primary; supporting) | Mechanism | Source / rights |
|---|---|---|---|
| Auguste Edouart, *Frank Johnson … with his wife, Helen*, 1842–44 | silhouette | Two full-length black cut-paper profiles; bugle, coat tails and skirt read by outline alone. | [Met 337070](https://www.metmuseum.org/art/collection/search/337070), CC0 |
| Auguste Edouart, *South Sea Islanders* | silhouette; layered depth | Black cut figures on a painted wash; gestures read as outline, figures shrink toward the horizon. | [Met 370826](https://www.metmuseum.org/art/collection/search/370826), CC0 |
| Arthur Rackham, *Cinderella*, silhouette illustration, 1919 | silhouette; implied motion | A leaping girl and two jumping dogs as pure black shapes on white, kept mostly unoverlapped. | [Commons](https://commons.wikimedia.org/wiki/File:Arthur_Rackham_Cinderella_silhouette_illustration.jpg), public domain |
| Philipp Otto Runge, *Neujahrsglückwunsch*, 1800 | silhouette; framing | A whole landscape in black cut paper inside an oval wreath; detail only through cut openings. | [Commons](https://commons.wikimedia.org/wiki/File:Philipp_Otto_Runge_Neujahrsgl%C3%BCckwunsch_1800.jpg), public domain |
| Hiroshige, *The Moon-Viewing Promontory*, 1857 | framing; silhouette | A room frames the moonlit bay; a guest appears only as a shadow on the paper screen. | [Cleveland 1985.320](https://clevelandart.org/art/1985.320), CC0 |
| Ferdinand Hodler, *Der Auserwählte*, 1893–94 | repetition with interruption; rhythm | Six near-identical robed figures, broken by one small kneeling child. | [Commons](https://commons.wikimedia.org/wiki/File:Ferdinand_Hodler_002.jpg), public domain |
| Ernst Haeckel, *Stephoidea*, Kunstformen der Natur, 1904 | repetition with interruption; value contrast | Open, spiky white rings on black; one closed latticed sphere at the centre. | [Commons](https://commons.wikimedia.org/wiki/File:Haeckel_Stephoidea.jpg), public domain |
| Hishikawa Moronobu, *Procession of a Daimyo*, c. 1681/84 | repetition with interruption; rhythm | Striding men in black jackets repeat; one pale green robe and tall spear break the run. | [AIC 30113](https://www.artic.edu/artworks/30113), CC0 |
| Degas, *Ballet at the Paris Opéra*, 1877 | proximity grouping; tight cropping | The corps packed into one overlapping line, the soloist apart across empty floor; audience heads cut by the frame. | [AIC 61603](https://www.artic.edu/artworks/61603), CC0 |
| Degas, *Yellow Dancers (In the Wings)*, 1874–76 | tight cropping; proximity grouping | Dancers cut by the edges, others shown only as feet under a flat; three huddled as one group. | [AIC 18951](https://www.artic.edu/artworks/18951), CC0 |
| Hiroshige, *Kinryūsan Temple at Asakusa*, 1856 | tight cropping; framing | A giant lantern and a gate post cut by the frame enclose the snowy precinct. | [Met 56689](https://www.metmuseum.org/art/collection/search/56689), CC0 |
| Hiroshige, *Fukagawa Susaki and Jumantsubo*, 1857 | vantage point; tight cropping, scale contrast | Bird's-eye view down past a diving eagle whose wings run off the sheet. | [AIC 26605](https://www.artic.edu/artworks/26605), CC0 |
| Julia Margaret Cameron, *Sir John Herschel*, 1867 | selective focus; value contrast | Sharp face; hair and cloak soften into a dark ground. | [Cleveland 1996.345](https://clevelandart.org/art/1996.345), CC0 |
| Julia Margaret Cameron, *Julia Jackson*, 1867 | tight cropping; selective focus | The head fills the frame; features sharper than the soft hair around them. | [Cleveland 2015.15](https://clevelandart.org/art/2015.15), CC0 |

## Counts per technique

Non-rejected labels in the pack: before this round, after the removals alone, and after the additions.
Techniques not listed are unchanged.

| Technique | Before (104) | After removals (88) | After additions (102) |
|---|---:|---:|---:|
| Silhouette | 8 | 1 | 6 |
| Repetition with interruption | 6 | 0 | 3 |
| Tight cropping | 5 | 1 | 6 |
| Selective focus | 3 | 0 | 2 |
| Proximity grouping | 3 | 2 | 4 |
| Unusual vantage point | 2 | 1 | 2 |
| Colour contrast | 11 | 6 | 6 |
| Framing | 13 | 13 | 16 |
| Rhythm and pattern | 15 | 13 | 15 |
| Layered depth | 17 | 15 | 16 |
| Scale contrast | 8 | 8 | 9 |
| Value contrast | 35 | 34 | 36 |
| Implied motion | 7 | 6 | 7 |
| Negative space | 20 | 18 | 18 |
| Colour harmony | 9 | 8 | 8 |
| Asymmetric balance | 18 | 17 | 17 |
| Juxtaposition | 6 | 5 | 5 |
| Leading lines | 5 | 4 | 4 |
| Symmetry | 2 | 1 | 1 |

Silhouette now has five examples besides *Divan Japonais*: four strong cut-paper or drawn silhouettes and one
softer cast shadow (Hiroshige). The collection now has 138 model-reviewed and 82 proposed labels (was 167 and 65;
the removed snapshots carried model-reviewed labels). Licences: 78 CC0, 19 public domain, 5 CC BY (was 73, 15, 16).
Providers: Commons 28, AIC 27, Cleveland 20, Smithsonian 15, Met 12.

## Display titles

Nineteen existing references had file-name or uploader-style titles; the display `image.title` was rewritten from
the pixels and the source description. For each changed field the original source value is kept in the rights
record's `provenance_json` as `source_title`, `source_creator` or `source_date`. `evidence_json`,
`required_attribution`, licences and every other rights field are unchanged. Four additions also got a display
title different from the source title, recorded the same way.

| Source title | Display title | Creator / date |
|---|---|---|
| Surrealism in photography 06 | Surrealism in Photography: View from Beneath a Table | date 2020-05-28 05:42:32 → 2020 |
| Elegant preventive of the cholera. | Elegant Preventive of the Cholera | "Print made by: Robert Seymour Published by: Thomas McLean" → Robert Seymour |
| The Lancaster Caleb Quotem, i.e. Jack of all trades. | The Lancaster Caleb Quotem, i.e. Jack of All Trades | "Print made by: Charles Williams …" → Charles Williams |
| French Generals retiring, on account of their health:-with Lepaux presiding in the Directory Dispensary. | French Generals Retiring on Account of Their Health, with Lepaux Presiding in the Directory Dispensary | "Print made by: James Gillray …" → James Gillray |
| Ronchamp17f.jpg - Flickr - scarletgreen | Notre-Dame-du-Haut, Ronchamp: painted window ("la mer") | scarletgreen from Japan → scarletgreen; "Taken on 19 February 2003, 20:37" → 2003 |
| Composition (1939) - Auguste Herbin (1882-1960) (25176351757) | Auguste Herbin, Composition (1939) | "Pedro Ribeiro Simões from Lisboa, Portugal" → Pedro Ribeiro Simões; 2015-11-22 14:29 → 2015 |
| Celestial Jellyfish - photomotage | Celestial Jellyfish (photomontage) | 2019-09-05 20:10:00 → 2019 |
| Alan Warburton - Quantified Human | Quantified Human | |
| 01 Irrational behavior, surreal absurd street scene in Budapest, Hungary | Irrational Behaviour: Top Hats on a Fire Hydrant, Budapest | "Marek Ślusarczyk ( Tupungato ) Photo portfolio" → Marek Ślusarczyk (Tupungato); "Taken on 21 June 2014" → 2014 |
| Civil War optical illusion card-The Eagle of the Republic | The Eagle of the Republic (optical illusion card) | "Unknown author Unknown author" → Unknown maker |
| Alice 05a-1116x1492 | Alice and the Caterpillar | |
| Temple of Time (1846) Emma Willard | Temple of Time | "Emma Hart Willard (February 23, 1787 – April 15, 1870) First published …" → Emma Willard |
| Playfair piecharts | Statistical Chart of the Principal Nations of Europe (Statistical Breviary) | 1801-01-01 → 1801 |
| A series of statistical charts illustrating the condition of the descendants of former African slaves … LCCN2013650373 | Occupations in Which 10,000 or More American Negroes Are Engaged | collection name → Atlanta University ("Done by Atlanta University" is printed on the sheet) |
| Tube map 1908-2 | London Underground Map, 1908 | "Unknown author Unknown author" → Unknown maker |
| 1882 Cincinnati Type Foundry specimen book detail p148 | Cincinnati Type Foundry Specimen Book, page 148 | |
| Bodoni Book type specimen (16335113031) | Bodoni Book Type Specimen | "James Puckett from Boulder, USA" → James Puckett; 2013-09-17 16:28 → 2013 |
| Filippo Tommaso Marinetti - Parole in Liberta 1932 A | Parole in libertà (SI NO) | |
| Ludwig Hohlwein - Igeha Schokolade, 1926 | Igeha Schokolade | |
| *Addition:* Arthur Rackham Cinderella silhouette illustration | Cinderella, silhouette illustration | |
| *Addition:* Philipp Otto Runge Neujahrsglückwunsch 1800 | Neujahrsglückwunsch (New Year's greeting), 1800 | |
| *Addition:* German: Der Auserwählte | Der Auserwählte (The Chosen One) | |
| *Addition:* Haeckel Stephoidea | Stephoidea, plate from Kunstformen der Natur | |

Museum titles (AIC, Met, Cleveland, Smithsonian) were already readable and were left alone. The Ronchamp title
names what the pixels and source show (a painted window inscribed "la mer"); it does not claim which wall.

## Rights and access

All candidates went through `providers.search`, `Fetcher`, `images.open_checked` and the quality checks, and
`rights.check` with `atlas/data/source_policies.json`. At build time `rights.check` was run again on each selected
candidate and had to return eligible. No provider, policy or licence rule was added or relaxed, and no licence was
entered by hand. Each new record keeps its source page, creator, item-level evidence JSON, licence URL, required
attribution, retrieval and verification timestamps, policy hash, original-file hash and resized-copy hash;
`provenance_json.redistribution` records the basis (the licence URL) and that the bundled copy is a resized,
re-encoded JPEG with attribution. Only the 1024 px analysis copies and 480 px thumbnails are bundled.

New files: 10 CC0 (Met 3, AIC 4, Cleveland 3) and 4 public domain (Commons). Model readings never authorized rights.
The owner's real library was never opened; all work used `%TEMP%\va-curate5*` homes.

## Searches and exclusions

About thirty bounded queries (12 results each) and 33 targeted downloads; no bulk downloads, no National Gallery.
Met: `Edouart silhouette`, `shadow puppet`, `katagami stencil`, `Hiroshige Famous Views of Edo`,
`Julia Margaret Cameron`, `kage-e shadow picture`, `butterflies specimen plate`, `facsimile procession`,
`Seurat Circus Sideshow`. AIC: `silhouette`, `Degas`, `flock of sheep`, `Hiroshige One Hundred Famous Views`,
`procession`. Cleveland: `silhouette`, `row of soldiers`, `Jan van Kessel`, `Julia Margaret Cameron`. Commons:
`Kunstformen der Natur`, `Rackham silhouette`, `Henri Riviere Chat Noir shadow theatre`, `Haeckel Trochilidae`,
`Haeckel Ascidiae`, `Haeckel Diatomea`, `Haeckel Cubomedusae`, `Muybridge Animal Locomotion plate`,
`row of identical houses Farm Security Administration`, `Hodler Der Auserwählte`, `Hodler Eurythmie`,
`Hodler Lebensmüde`, `Philipp Otto Runge Scherenschnitt`, `ombres chinoises`, `Rackham Sleeping Beauty silhouette`.

Rejected after rights or pixel review:

- **Manet, *Berthe Morisot in Silhouette* (AIC 11137)**: the pixels show a line portrait, not a silhouette.
- **Daumier, *Silhouettes* plate 1 (AIC 61099)**: "Silhouettes" is the series title; the picture is a shaded figure.
- **Théâtre d'Ombres in Le Chat Noir (Commons)**: failed the quality check, too small (552×400).
- **Met shadow puppets**: the Javanese ones were not marked public domain; the Chinese ones are coloured,
  translucent objects, not silhouettes.
- **Haeckel *Trochilidae*, *Discomedusae*, *Ascidiae*, *Diatomea*; Met katagami stencils**: repetition with
  variation, but no single element breaks the series; not labelled as odd one out.
- **Hodler, *Aus der Eurythmie* sketch and *Lebensmüde***: repetition without an interruption; redundant with
  *Der Auserwählte*.
- **Cleveland *Maharaja Ranbir Singh … with Sons and Courtiers*; AIC *Maharana Bhim Singh in Procession***: group
  hierarchy rather than odd one out.
- **Commons shadow-puppetry performance photographs** (CC BY): contemporary event photographs, the kind of snapshot
  this round replaces.
- **Muybridge plates on Commons**: CC BY 4.0 records with no author recorded were deterministically rejected; the
  public-domain plates teach sequence, not interruption.
- **Met downloads that failed** with `wrong_type` from the app's fetcher (*Sudden Shower over Shin-Ōhashi*, two
  Cameron portraits, *Forty-one Insects*, two Egyptian procession facsimiles, Seurat's *Circus Sideshow*). Not
  investigated; `atlas/` was out of scope. Cleveland's Cameron prints were used instead.
- The Commons `row of identical houses …` query returned nothing eligible.

Remaining gaps: selective focus has two examples (was three), both Cameron photographs, so the pack has no
painted or modern-lens example of it. Repetition with interruption has three (was six), and two of them (Haeckel,
Moronobu) are softer cases where a second element also differs; Hodler is the clean one. Colour contrast fell from
11 to 6 and was not replaced. Symmetry stays at one.

## Review and verification

The fourteen readings were written by the interactive Claude curation agent after pixel inspection, with
`backend: claude-interactive`, `model: Claude Opus 5.5 curation agent`, prompt tag `interactive-curation-r5-starter`,
no CLI version and no token usage. All are `proposed`, not locked, and not `human_reviewed` or `model_reviewed`.
The 0.7 confidence is a qualitative judgment required by the schema, **not a measured probability**.
`creator_intent` is null.

- Fresh scratch import of the new pack: 102 imported, repeat import 0, 102 rows in the search index.
- `starter/CREDITS.md` was regenerated in full by `transfer.credits` from that clean import (the numbering changed
  with the removals, and the current function writes provider names such as "Art Institute of Chicago" where the
  old file had ids such as "aic"). The explanatory header line is kept.
- Near duplicates: the closest pair involving a new reference is the two Cameron portraits at dHash distance 14
  (the worker's threshold is 6).
- No orphan or missing media files; every bundled analysis copy matches its SHA-256.
- `tests/test_desk.py`: the fixture's hard-coded starter count changed from 104 to 102; nothing else edited.
- `uv run pytest -q`: 470 passed, 1 skipped, 9 deselected (offline, about 3 minutes).
- `uv run python scripts/check_no_data.py`: passed. `uv run ruff check atlas tests scripts`: all checks passed.
