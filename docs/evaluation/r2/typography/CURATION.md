# Starter curation, r2: typography, posters and information design

Checked 2026-11-23. **104 references, up from 93; eleven new readings, all proposed.**
The original 93 records are byte-identical in `starter/library.json`; the eleven new ones are appended.
This is a builder/model curatorial judgment, not independent expert ground truth. It follows the v0.4
procedure in [../../v0.4/CURATION.md](../../v0.4/CURATION.md): same search helper, same rights path, same
evidence standard, same analysis contract.

## Why

The 93-reference starter was almost entirely painting, prints and object photography. Designers and agents ask
for posters, type, layout and interface references, and the pack had no type specimen, no transit map and no
statistical chart. This round adds historical graphic design and information design whose rights the app could
establish.

| Technique | Before | After | New examples |
|---|---:|---:|---|
| Scale contrast | 5 | 8 | Playfair circles; Cincinnati Gothic No. 2 specimen; Marinetti *SI NO* |
| Leading lines | 4 | 5 | Minard, *Carte figurative* (Russia 1812–13 and Hannibal) |
| Proximity grouping | 2 | 3 | Du Bois, occupations of 10,000 or more (bracketed tail) |
| Colour contrast | 10 | 11 | London Underground map, 1908 |
| Rhythm and pattern | 14 | 15 | Bodoni Book specimen page, 8–36 pt |
| Diagonal energy | 4 | 5 | El Lissitzky, *Beat the Whites with the Red Wedge* |
| Silhouette | 7 | 8 | Toulouse-Lautrec, *Divan Japonais* |
| Limited palette harmony | 8 | 9 | Van Rysselberghe, poster for the Lembrée gallery |
| Negative space | 19 | 20 | Hohlwein, *Igeha Schokolade* |

Counts are non-rejected labels. The collection now has 167 model-reviewed and 65 proposed labels (was 54
proposed). New distribution media adds 2,617,475 bytes (about 2.50 MiB): only the 1024 px analysis copies
and 480 px thumbnails, as in v0.4.

## Accepted examples and teaching evidence

Every accepted file was downloaded through the app and opened as actual pixels in this session.
[typography-additions.json](typography-additions.json) holds the concrete observations, proposed effect,
teaching value and ambiguity for each; the same text is validated with `tasks.validate_analysis` and stored in
the starter as the reading.

| Example | Mechanism | Source / rights |
|---|---|---|
| Minard, Carte figurative, 1869 | A pink band runs Kowno → Moscou and a black band returns; the eye follows the route. Width also encodes the army size. | [Commons](https://commons.wikimedia.org/wiki/File:Carte_figurative_des_pertes_successives_en_hommes_de_l%27arm%C3%A9e_fran%C3%A7aise_dans_la_Campagne_de_Russie_1812-13.jpg) (Gallica scan), public domain |
| Playfair, Statistical Breviary chart, 1801 | One huge circle (Russian Empire) beside a row of shrinking circles on one baseline. | [Commons](https://commons.wikimedia.org/wiki/File:Playfair_piecharts.jpg) (David Rumsey), public domain |
| Du Bois / Atlanta University, 1900 | Fourteen short bars gathered by a bracket into one combined bar beside the long ones. | [Commons](https://commons.wikimedia.org/wiki/File:A_series_of_statistical_charts_illustrating_the_condition_of_the_descendants_of_former_African_slaves_now_in_residence_in_the_United_States_of_America_LCCN2013650373.jpg) (Library of Congress), public domain |
| London Underground map, 1908 | Each route a distinct saturated hue over a muted street map, with a colour key. | [Commons](https://commons.wikimedia.org/wiki/File:Tube_map_1908-2.jpg), public domain, author unknown |
| Cincinnati Type Foundry, 1882 | Each Gothic No. 2 block opens with one large capital word over smaller lines: hierarchy by size. | [Commons](https://commons.wikimedia.org/wiki/File:1882_Cincinnati_Type_Foundry_specimen_book_detail_p148.png), public domain |
| Bodoni Book specimen page | The same two-line unit repeats eight times at 8→36 pt on an inch grid. | [Commons, James Puckett](https://commons.wikimedia.org/wiki/File:Bodoni_Book_type_specimen_(16335113031).jpg), CC BY 2.0 (photograph of the page) |
| El Lissitzky, 1919 | Red wedge, split ground and rotated lettering all run on diagonals. | [Commons](https://commons.wikimedia.org/wiki/File:Beat_the_Whites_with_the_Red_Wedge.jpg), public domain |
| Toulouse-Lautrec, Divan Japonais, 1892–93 | The main figure is one flat black mass against yellow and grey. | [The Met 334197](https://www.metmuseum.org/art/collection/search/334197), CC0 |
| Van Rysselberghe, Lembrée poster, 1897 | Orange, pale green, cream and dark blue repeat across figure, room and lettering. | [Cleveland 1968.257](https://clevelandart.org/art/1968.257), CC0 |
| Marinetti, Parole in libertà, 1932 | SI / NO alternate down a diagonal, growing from small to dominant. | [Commons](https://commons.wikimedia.org/wiki/File:Filippo_Tommaso_Marinetti_-_Parole_in_Liberta_1932_A.jpg), public domain |
| Hohlwein, Igeha Schokolade, 1926 | One figure centred on an empty cream ground, with script lettering in the open space. | [Commons](https://commons.wikimedia.org/wiki/File:Ludwig_Hohlwein_-_Igeha_Schokolade,_1926.jpg), public domain |

## Rights and access

All candidates went through the existing `providers.search`, `Fetcher`, `images.open_checked` and quality checks,
and `rights.check` with `atlas/data/source_policies.json`. At build time `rights.check` was run again on each
selected candidate and had to return eligible. No provider, policy or licence rule was added or relaxed, and no
licence was entered by hand. Each record keeps its source page, creator, item-level evidence JSON, licence URL,
required attribution, retrieval and verification timestamps, policy hash, original-file hash and resized-copy
hash. As in v0.4, `provenance_json.redistribution` records the basis (the licence URL) and that the bundled copy
is a resized, re-encoded JPEG with attribution.

New files: 8 public domain, 2 CC0, 1 CC BY. Pack total: 73 CC0, 15 public domain, 16 CC BY.
Public-domain status on Commons is the file page's statement as read by `rights.py`; a particular use can
still depend on trademarks (Igeha / Hauswaldt, Underground lettering) or other restrictions, which the
standard restrictions text records. The Bodoni licence covers James Puckett's photograph of the page.
Model readings never authorized rights. The owner's real library was never opened; all work used
`%TEMP%\va-typo*` homes.

## Searches and exclusions

Sixteen bounded queries (12 results each), 20 targeted downloads, no bulk downloads, no National Gallery.
Commons: `Minard Napoleon map`, `W. E. B. Du Bois data`, `Playfair chart`, `Du Bois Paris Exposition 1900 chart`,
`type specimen book`, `El Lissitzky`, `Bauhaus poster`, `Ludwig Hohlwein`, `Beat the Whites with the Red Wedge`,
`Underground map 1908`, `Marinetti parole in liberta`. Met: `Toulouse-Lautrec poster`, `Bradley poster`.
Cleveland: `poster`. Smithsonian: `type specimen`. Rijksmuseum: `affiche`.

Rejected after rights or pixel review:

- **Will Bradley (Met, 12 results)**: all deterministically rejected, not marked public domain by the museum.
- **Smithsonian `type specimen`**: returned botanical type specimens only; irrelevant.
- **Rijksmuseum `affiche`**: the provider raised `AttributeError` parsing a record's date (`providers.py`
  `_rijksmuseum`, a `timespan` that is a list). No candidates; not fixed here, since `atlas/` was out of scope.
- **Du Bois mortality chart (Commons 32221473)**: strong colour-contrast example, but its source metadata
  describes almshouse residents while the pixels show mortality. Rejected for metadata mismatch; the
  occupations chart, whose metadata matches, was used.
- **Haus Bergmann *Privat* cigarette poster, 1935**: the Commons "artist" is the uploader and the designer is
  unknown; it also carries a still-used-style logo. Dropped as a weak rights and trademark case.
- **Yvette Guilbert (Cleveland)**: a pencil sketch, not graphic design.
- **El Lissitzky *Proun 5A***: a gallery photograph of a painting with frame edges; the poster covers the same
  lesson more cleanly.
- **Marinetti *Treni* 1910**: a manuscript sketch; weak as a typography reference.
- **Playfair imports/exports, Du Bois stacked occupations and enrolment, Hohlwein *Deutscher Rundflug***:
  credible but redundant with chosen examples; not added to avoid over-weighting one designer or series.
- CC BY photographs of Marinetti works in private collections were skipped in favour of public-domain scans.

Remaining gaps: no interface-like diagram or instrument panel was found within the search budget; the
pack still has no twentieth-century modernist grid layout (Swiss style is not yet public domain), and three of
the eleven teach scale contrast.

## Review and verification

The eleven readings were written by the interactive Claude curation agent after pixel inspection, with
`backend: claude-interactive`, `model: Claude Opus 5.5 curation agent`, no CLI version and no token usage.
All are `proposed`, not locked, and not `human_reviewed` or `model_reviewed`. The 0.7 confidence is a
qualitative judgment required by the schema, **not a measured probability**. `creator_intent` is null.

Fresh scratch import of the new pack: 104 imported, repeat import 0. Credits for #94–#104 were generated by
`transfer.credits` from that clean import and appended; entries #1–#93 are unchanged. No new reference is a
near-duplicate of any other (minimum dHash distance 14; the worker's threshold is 6).

- `uv run pytest -q tests/test_starter.py tests/test_curation.py tests/test_transfer.py`: 61 passed.
- `tests/test_desk.py`: 22 errors, all from the fixture's hard-coded `import_starter(...) == 93`; the pack
  now imports 104. A scratch copy with only that number changed to 104 passed (24 passed). The test file
  belongs to another session and was not edited here.
- `uv run python scripts/check_no_data.py`: passed.
