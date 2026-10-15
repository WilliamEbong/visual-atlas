# Tasks 006 — v0.3

## Phase 1: Setup and pre-registration
- [x] T601 Version 0.3.0; principles recorded; v0.2.0 publish evidence in BUILD-STATE (pyproject.toml, atlas/__init__.py, web/package.json, BUILD-STATE.md)
- [x] T602 Fresh final holdout briefs written and coded before any coder change; coding criteria fixed (docs/evaluation/v0.3/briefs-final.json, docs/evaluation/v0.3/CODING-GATE.md)
- [x] T603 Metadata-filter criteria and case set (≥ 10 negatives, labelled from thumbnails) fixed before any arm runs (docs/evaluation/v0.3/METADATA-GATE.md, docs/evaluation/v0.3/metadata-cases.json)

## Phase 2: Foundation — visual system and shared states (US1, US2, US4)
- [x] T604 Tokens, type, horizon header, buttons, fields, plates, trays, dark mode, reduced motion (web/src/styles.css)
- [x] T605 Shared UI: PageHead, Loading, Empty, Failure, Busy, NoticeProvider/useNotice with Undo, useConfirm dialog; client marks 503 maintenance as busy (web/src/components/ui.tsx, web/src/lib/client.ts)
- [x] T606 Shell: nav per canvas, job indicator, phone menu disclosure, skip link, providers; no-alert source test (web/src/App.tsx, web/src/lib/noalert.test.ts)

## Phase 3: Screens (US1, US3, US8)
- [x] T607 Library: horizon with specimen windows, drawers, search row + More filters panel, active filters, justified CSS grid, plate captions, nextByPosition keys + tests (web/src/components/Library.tsx, web/src/lib/library.ts)
- [x] T608 Image page: regions on the picture linked to observations, three sections, prev/next + arrow keys within results, related by technique tabs, history; confirm for removal (web/src/components/ImagePage.tsx, web/src/lib/regions.ts)
- [x] T609 Explore and technique page: lens, trays, examples strip, nearby, goals (web/src/components/Explore.tsx)
- [x] T610 Find and job progress: field-note form, live reading, sources, timeline, counts, item outcomes; Jobs list (web/src/components/Find.tsx, JobProgress.tsx, Jobs.tsx)
- [x] T611 My project: brief slip, reading trays, directions under rules with cited thumbnails, dismiss with Undo, thin-evidence prompt; delete with confirm (web/src/components/Project.tsx)
- [x] T612 Compare (baseline, matrix, palettes, saved comparison) and Collections (drawers, contact strips, remove with Undo, delete with confirm) (web/src/components/Compare.tsx, Collections.tsx)
- [x] T613 Settings sections with in-page nav, sources table from policies, restore with confirm; Welcome and Connections restyled (web/src/components/Settings.tsx, Welcome.tsx, Connections.tsx)

## Phase 4: Sources (US5)
- [x] T614 Research record per source with official URLs and dates (docs/evaluation/v0.3/SOURCES.md)
- [x] T615 Connectors, rights rules, policies, fixtures and tests for each accepted source; disabled entries with evidence for the rest; search hints (atlas/providers.py, atlas/rights.py, atlas/data/source_policies.json, atlas/data/taxonomy.json, tests/)
- [x] T616 Live smoke per enabled new source (tests marked live)

## Phase 5: Request coding (US6)
- [x] T617 request_cues in the taxonomy, coder phrase matching and stopword fixes + tests (atlas/data/taxonomy.json, atlas/coding.py, tests/test_coding.py)
- [x] T618 Coding evaluation: dev decision, final once, report (scripts/eval_v03.py, docs/evaluation/v0.3/)

## Phase 6: Metadata filter (US7)
- [x] T619 Deterministic rules and Jev arm evaluated per METADATA-GATE.md; integrate only a passing arm (skip reason, Settings switch) + tests (atlas/data/metadata_filter.json, atlas/jobs.py, atlas/server.py, tests/)

## Phase 7: Polish, verification and release
- [x] T620 axe scans (light, dark) and layout-shift measurement; fix findings (web/package.json devDependency axe-core)
- [x] T621 Docs and screenshots (README.md, QUICK-START.md, docs/USER-GUIDE.md, design-review/v0.3/)
- [ ] T622 Full checks; Playwright journeys desktop and 375 px; fresh install and upgrade from published v0.2.0; local release zip
- [ ] T623 Independent review (≤ 2 rounds), fixes, converge, BUILD-STATE handoff
