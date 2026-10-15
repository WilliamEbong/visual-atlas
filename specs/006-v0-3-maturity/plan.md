# Plan 006 — v0.3

Stack unchanged. Version 0.3.0 in `pyproject.toml`, `atlas/__init__.py`, `web/package.json`. One new dev-only
dependency: `axe-core` (pinned, web devDependency) for accessibility scans run through Playwright; nothing new at
runtime. A migration only if a source or the filter needs a column (not expected: reasons live in item text).

## Decisions
- **Design source of truth.** The canvas (10 artboards) fixes the look. Tokens move into `web/src/styles.css`
  custom properties (light and dark kept), using the fonts already bundled offline (@fontsource Cormorant
  Garamond, Libre Franklin, IBM Plex Mono) behind the installed Perpetua, Franklin Gothic and Consolas.
- **Horizon (FR-2).** One shared `PageHead` component renders the header band: a fixed-height block whose bottom
  border is the horizon (desktop: the rule 300 px from the page top, header band 236 px under a 64 px bar;
  ≤ 600 px: 150 px band). Title and meta stand on it; an optional `aside` slot holds specimen windows or the lens.
- **Justified grid (FR-3), CSS only.** Each plate is `flex: <a·h> 1 <a·h>px` with an aspect-ratio frame (`a` from
  the library item's width/height, which the API already returns), so items in a row grow by the same factor and
  share a height; a trailing filler with a huge grow factor keeps the last row from stretching. No layout
  measurement in JavaScript. Arrow-key navigation moves by position (`nextByPosition` in `lib/library.ts`, pure
  and tested) instead of by grid columns.
- **Regions (FR-4).** The analysis stores named regions (`whole`, `center`, `top`, `bottom`, `left`, `right`,
  four corners, `foreground`, `middle-ground`, `background`). `lib/regions.ts` maps each to a box (percentages);
  depth regions map to horizontal bands and are labelled "approximate area". Hover or focus on an observation
  highlights its box and the box's label; the boxes are decorative (`aria-hidden`), the list carries the
  meaning.
- **States, notices, confirmation (FR-12, 13).** `components/ui.tsx` holds `PageHead`, `Loading` (ruled
  skeleton plates), `Empty`, `Failure` (message plus retry), `Busy` (shown when the client sees a 503 from
  maintenance), a `NoticeProvider` with `useNotice()` (one polite live region, 8 s, paused on hover or focus, an
  optional Undo callback) and `useConfirm()` (a native `<dialog>` opened with `showModal()`; Escape closes; focus
  goes to the safe button and returns to the trigger). A vitest test fails if `window.alert`, `confirm(` or
  `prompt(` appears anywhere in `web/src`.
- **Undo semantics.** Undo replays the inverse API call: remove-from-collection → add back at the same position;
  dismiss direction → keep; unstar → star; reject a technique → no undo (it is already reversible by confirming).
  Library removal, brief and collection deletion, and restore use `useConfirm()`.
- **Phone (FR-11).** At ≤ 760 px the nav collapses behind a menu button (`aria-expanded`, a disclosure, not a
  modal); image page sections become tabs at ≤ 600 px.
- **Accessibility checks (FR-14).** Playwright evaluates `axe-core`'s `axe.run()` (API checked with Context7) on
  each main screen in light and dark; the target is 0 serious/critical violations. Layout shift (FR-15) is
  measured with a `PerformanceObserver` for `layout-shift` entries during the library's first load.
- **Sources (FR-16–18).** Decided per source from the official-documentation research (saved in
  `docs/evaluation/v0.3/SOURCES.md` with URLs and the date). Each enabled source gets a connector in
  `atlas/providers.py` (search + item → candidate), a rule in `atlas/rights.py` reading only the source's own
  rights field, an entry in `atlas/data/source_policies.json` (hosts, rate, rule text, evidence), fixtures in
  `tests/fixtures/`, and search hints in the taxonomy. A source with no mechanical rule stays disabled with its
  evidence in the policy file.
- **Request coding (FR-19, 20).** Taxonomy techniques and goals gain `request_cues` (descriptive phrases a person
  would write). `coding.py` matches them as phrases with word boundaries (a cue is weaker than a name or alias but
  counts). Before any change, a fresh final holdout of ≥ 16 briefs with builder codes is written and committed
  (`docs/evaluation/v0.3/briefs-final.json`); the v1.1 briefs are the development set. Adoption is decided on the
  development set; the final set runs once afterwards (`scripts/eval_v03.py coding`).
- **Metadata filter (FR-21).** Rules as data (`atlas/data/metadata_filter.json`: phrases over title, medium,
  classification and description that mark documentation photographs, specimen sheets and text pages). Criteria
  and the case set (≥ 10 negatives, real candidate records from the sources, builder labels made from the
  thumbnails before any arm runs) are written down first in `docs/evaluation/v0.3/METADATA-GATE.md`. The Jev arm
  reuses `atlas/ai/jev.py`'s transport with the v1.1 question. If an arm passes, discovery skips a matching
  candidate before download with reason "looks like a documentation photo (<rule>)"; a Settings switch turns it
  off. The Jev arm, if adopted, stays optional and off by default (own key).
- **Version and release.** 0.3.0; docs and screenshots updated; fresh install and upgrade from the published
  v0.2.0 zip in scratch homes; local zip only.

## Files
- web: `styles.css` (rewritten), `App.tsx` (shell, phone menu, providers), `components/ui.tsx` (new), every page
  component restyled to the canvas, `lib/regions.ts` (new), `lib/library.ts` (+ `nextByPosition`),
  `lib/client.ts` (busy detection), tests for each pure helper and the no-alert rule.
- python: `atlas/providers.py`, `atlas/rights.py`, `atlas/data/source_policies.json`, `atlas/data/taxonomy.json`,
  `atlas/coding.py`, `atlas/jobs.py` (filter hook), `atlas/data/metadata_filter.json` (if adopted),
  `atlas/server.py` (settings switch), tests.
- docs: `docs/evaluation/v0.3/` (SOURCES.md, METADATA-GATE.md, briefs-final.json, results, REPORT.md), README,
  USER-GUIDE, QUICK-START, `design-review/v0.3/` screenshots.
