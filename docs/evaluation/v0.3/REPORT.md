# Visual Atlas v0.3 evaluation (2026-10-15)

Every criterion below was written down before its results existed: [CODING-GATE.md](CODING-GATE.md),
[METADATA-GATE.md](METADATA-GATE.md), and the source rule in [SOURCES.md](SOURCES.md). Rates carry Wilson 95%
intervals. Reference codes and labels are the builder's provisional judgment, not an expert panel's.
Reproduce with `uv run python scripts/eval_v03.py coding dev`, `… coding final` and
`… metadata [--env-file PATH]`.

## 1. Request coding: reading briefs written in ordinary words

v0.3 adds descriptive cue phrases (for example "backlit" for silhouette, "misty" for atmospheric perspective) to
the taxonomy as data. The coder treats a cue match as a weaker, non-exact tag. Format words such as "against" and
"flyer" stop counting as subject words. Arm 1 is the shipped v1.1 coder, loaded from the v0.2.0 tag.

| Set | Coder | Precision | Recall | micro-F1 | Retrieval recall@20 |
|---|---|---|---|---|---|
| Development (16 v1.1 briefs) | v1.1 | 6/11 = 0.55 | 6/28 = 0.21 | 0.31 | 54/80 = 0.68 |
| Development | v0.3 | 24/29 = 0.83 [0.65–0.92] | 24/28 = 0.86 [0.69–0.94] | 0.84 | 62/80 = 0.78 [0.67–0.85] |
| Final holdout (20 new briefs) | v1.1 | 8/15 = 0.53 [0.30–0.75] | 8/41 = 0.20 [0.10–0.34] | 0.29 | (no relevance judgments) |
| Final holdout | v0.3 | 22/30 = 0.73 [0.56–0.86] | 22/41 = 0.54 [0.39–0.68] | 0.62 | — |

**Decision: adopted.** On the development set every criterion held:
- F1 rose by 0.53, against a bar of 0.10;
- precision is 0.83, against a floor of 0.60;
- retrieval did not drop.

The final holdout ran once, after the decision. F1 roughly doubled there too (0.29 to 0.62), but recall is about
half. The coder still misses described ideas that use words outside its cues, such as "pulling your eye", "a
chimney that is also a tree" or "only the watch is sharp". It also adds a few wrong goals. These misses are left
as they are, because tuning on the holdout would void it.

**Limits.**
- The same person wrote the cues, the development codes and the holdout briefs. The cues were written from what
  each technique means, with the development briefs visible and before any holdout result. Shared vocabulary
  could still favour the holdout.
- 16 and 20 briefs give wide intervals.
- Retrieval recall is measured on the development set only, because the holdout has no relevance judgments.

## 2. Metadata filter: skipping record shots before download

| Arm | Negatives skipped (n = 18) | Positives skipped (n = 29) | Decision |
|---|---|---|---|
| Phrase rules (written before the cases) | 11/18 = 0.61 [0.39–0.80] | 5/29 = 0.17 [0.08–0.35] | not integrated |
| Jev, the v1.1 question, skip at ≥ 0.8 (94 calls, about $0.002) | 10/18 = 0.56 [0.34–0.75] | 5/29 = 0.17 [0.08–0.35] | not integrated |

**Decision: neither arm is integrated.** The gate allows no lost positive, and both arms lost five.
- **Phrase rules:** the word "letter" caught Cassatt's *The Letter* and two illustrated alphabet sheets; "verso"
  caught a two-sided landscape drawing.
- **Jev:** it skipped textile and stained-glass fragments that the builder would file for pattern.

Every eligible candidate is still analysed, as in v0.2.0. The evaluated rules are kept in
[metadata-rules.json](metadata-rules.json); nothing ships in the app.

**Limits.**
- The 47 cases come from live searches on six sources; the Smithsonian's demo key was rate-limited.
- Labels came from thumbnails with the text hidden, and 10 are marked uncertain (fragments, alphabet sheets, a
  title page, a staged photograph).
- A different labeller might count fragments as negatives, and then the outcome changes.

## 3. Sources

Two sources were added, each with live smoke tests that found eligible images and downloaded one:
- **Rijksmuseum.** The rights statement comes from each image's own record.
- **National Gallery of Art.** The open-access flag comes from its open data, searched through a local index.

The Library of Congress and NASA stay disabled with evidence: their rights are free text, not a field code can
read. Details are in [SOURCES.md](SOURCES.md).

## 4. Interface quality checks

- **Accessibility:** axe-core 4.13.0, WCAG 2.0/2.1 A and AA, on 12 main screens in light and dark themes. It
  found 0 serious or critical violations, after one fix: caption grey on cream cards was below 4.5:1.
  Script: [scripts/a11y-scan.js](../../../scripts/a11y-scan.js).
- **Layout shift on the library's first load:** cumulative layout shift 0.015, and 0.029 on a later run, against a
  target below 0.05. The justified grid reserves each picture's space from its stored size.
- **Phone width (375 px):** no screen scrolls sideways, after fixes to the image page grid and the collections
  header.
- **Browser journeys:** 12 of 12 passed, with no console errors. Script:
  [scripts/journeys-v03.js](../../../scripts/journeys-v03.js). They cover:
  - filters, arrow keys and previous/next;
  - Undo for favourites, collections and directions;
  - in-app confirmation for deletes, where Escape keeps the item;
  - the brief's reading;
  - a live Find on the Rijksmuseum.
