# 008 Reference desk: references with reasons, for people and agents

## Overview
Thesis: `docs/research/05-thesis.md`. A design brief goes in. Out come ranked references, each with its reasons,
licence and credit, plus guidance for the visual decision. One deterministic engine serves the CLI, a read-only MCP
server and a new page in the app. Two labelled layers join the licence-checked library: generated images made for
Visual Atlas, and the owner's private design-system libraries, which are local and opt-in.

## User scenarios
1. An agent building a slide deck calls the MCP tool `advise` with the brief "calm opener for a tea-house launch".
   It gets the techniques that fit, how to apply each, and six references with reasons and credits. It then
   calls `view_reference` to look at two of them.
2. A designer types the same brief on the app's **Ask** page and sees the same answer, with pictures. They open a
   reference, or filter to "can publish" only.
3. On the owner's machine, with `VISUAL_ATLAS_DESIGN_SYSTEMS=auto`, the brief "cyberpunk night city for a game
   pitch" routes to harbour-of-drifting and returns its images. On any other machine that layer does not exist.
4. An agent asks for figure–ground ambiguity. Next to the two library examples it gets generated examples, labelled
   generated, each with its prompt and the works studied.

## Functional requirements
- FR-1 `desk.search` ranks references from the chosen layers (library, generated, design-system) by brief,
  technique ids, goal ids, subjects, orientation, colour, medium, era, system and publishable-only. Every result has
  `reasons` built only from stored data and a `licence` with `checked_by`.
- FR-2 `desk.advise` adds technique guidance (definition, how it works, when it helps, what to look for, how not to
  confuse it, limits) and next steps. A brief with no known goal or technique says so instead of padding.
- FR-3 `desk.route` picks a design system and the user's collections for a brief from shared distinctive words. It
  falls back to archive-of-looking, the owner's default.
- FR-4 CLI: `atlas advise`, `atlas refs`, `atlas ref`, `atlas mcp`. JSON output by default, `--text` for people.
- FR-5 MCP server over stdio: `advise`, `search_references`, `get_reference`, `view_reference` (a JPEG of at most
  1024 px), `list_techniques`, `get_technique`, `route_brief`. All are read-only (`readOnlyHint`). It never starts
  AI work or downloads. Inputs are validated. References are named by ref id, never by a path. Errors come back as
  tool errors and never as tracebacks.
- FR-6 Generated layer: `generated/manifest.json` plus image files. Each entry has a prompt, the works studied, the
  tool, the date, the techniques intended and a review against `generated/RUBRIC.md`. Dropped images are listed
  with reasons, without files. Labels say "Generated image: no licence asserted". They never pass `publishable`.
- FR-7 Design-system layer: indexes `<skill>/references/images.csv` and `assets/library/<id>.jpg` in place,
  read-only. It is enabled only by the `VISUAL_ATLAS_DESIGN_SYSTEMS` setting. A test fails if any design-system
  file could be committed.
- FR-8 Web: an **Ask** page (brief, use filter, layer toggles, results with reasons, guidance) and the
  `/api/desk` and `/api/desk/media` endpoints, behind the existing token and Host checks. Layer media is served only
  for indexed refs. The visual design improves across the main views (calm, fast, accessible, usable without
  technical knowledge).
- FR-9 Docs: README section, a user-guide section for agents (MCP config for Claude Code and Codex), and a note
  that the design-system layer exists only on the owner's machine.

## Success criteria
- SC-1 Offline tests cover the engine, router, layers, CLI and MCP, with no network or model calls.
- SC-2 A real external MCP client lists the tools and calls `advise` and `view_reference`.
- SC-3 The CLI answers 6 or more real briefs with credited references. Outputs are recorded in
  `docs/evaluation/v0.5/`.
- SC-4 Playwright screenshots at 1440 and 375 px of the Ask page, Library and an image page, with no console
  errors.
- SC-5 Backend and frontend tests, TypeScript, Ruff and the builds are green.

## Clarifications (answered autonomously, 2026-11-22)
- Q: Should design-system images enter the SQLite library? A: No. They are indexed in place. The library's rights
  invariant (atlas/rights.py only) stays intact.
- Q: Should generated images be CC0? A: No licence is asserted. US copyright of AI output is unsettled, and only
  the owner can dedicate work.
- Q: Should MCP include AI directions? A: No. It stays read-only and directions remain an app job (Later: opt-in).
