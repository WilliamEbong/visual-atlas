# Visual Atlas — BUILD-STATE

Durable checkpoint for the autonomous build. Newest status first. Plan of record:
`C:\Users\Owner\.claude\plans\first-make-a-folder-iridescent-fountain.md` (approved 2026-10-15).

## Next concrete action
Playwright-verify the slice UI against a running server (scratch home with 3 live images), write
Claude-owned tests (store, jobs, tasks, catalog, server), then fold in Codex task 2 results.

## Owner decisions (2026-10-15 plan gate)
- Publish like Qualia: public repo `WilliamEbong/visual-atlas`, Releases zip, read-only Pages demo —
  only after tests, Codex review and secret/data scans pass. Overrides the brief's "no public deploy".
- AI split: Codex proposes annotations; Claude Code does the second-model check (`model_reviewed`) and
  the held-out challenge.
- Help material: illustrated guide, quick-start, in-app welcome, README screenshots, GIF tour (no videos).

## Assumptions and decisions (Claude)
- Reuse Qualia's stack and patterns (same owner, MIT): Python 3.14/uv/FastAPI/Typer/SQLite + React/Vite/TS/Tailwind.
- Project folder `C:\Users\Owner\OneDrive\Documents\VisualAtlas`; data home `%USERPROFILE%\VisualAtlas` (outside OneDrive).
- Enabled providers: Met, AIC, Cleveland, Smithsonian (DEMO_KEY or owner key), Wikimedia Commons (CC0/PD/CC BY only).
  Disabled with evidence: Unsplash (hotlink + ML-dataset clause), Pexels, Pixabay (AI/ML clauses), others = later candidates.
- `/design` is the Claude Desktop host command that creates a "Design" Artifact canvas (not a skill file); style input archive-of-looking.
- Spec Kit project skills were installed after this session started, so the Skill tool cannot load them by name;
  the build follows the installed `.claude/skills/speckit-*/SKILL.md` instructions directly (read 2026-10-15, lean preset).
- Manual upload / URL import skipped (brief marks upload optional); the SSRF-safe fetcher protects all provider downloads.

## Done
- 2026-10-15: spikes passed — Codex `exec --image=` and Claude `--input-format stream-json` base64 image both read
  real pixels with every tool disabled; all 5 providers live (Met search moved to /v1.1; AIC IIIF needs the
  documented AIC-User-Agent header; Cleveland CDN had a temporary 521).
- 2026-10-15: vertical slice live via CLI — `atlas find ... --backend codex --verify-with claude --count 3 --provider aic`
  added 3 real AIC CC0 images; Codex (gpt-6-astra) analysed pixels, Claude (sonnet -> claude-sonnet-5-5) verified;
  plan step by gpt-6-luna. Prompts then tightened (models over-proposed ~4 techniques each; verifier agreed with all).
- 2026-10-15: /design canvas (4 artboards) https://claude.ai/artifact/6fHxDYjPYSVhEwWwoPgX8A ; React app built from it.
- 2026-10-15: folder, `git init` (branch main), Spec Kit init + lean preset + Codex integration (claude default),
  CLAUDE.md = AGENTS.md, constitution v1.0.0, docs/FREE-IMAGE-SOURCES.md, .gitignore, keep-awake held.

## Remaining (phases)
0 spikes · 1 vertical slice (spec 001) · 2 connectors · 3 taxonomy + jobs · 4 library features ·
5 connections + briefs · 6 packaging + docs · 7 ingestion (~60 refs) + held-out · 8 converge, reviews, release.

## File ownership
- Codex task 2 (running): atlas/fetch.py, atlas/images.py, atlas/rights.py, atlas/providers.py,
  tests/test_fetch.py, tests/test_images.py, tests/test_rights.py, tests/test_providers.py.
- Claude: everything else.

## Codex delegated tasks
1. task-mv9a1vza-xi4tsp (2026-10-15) — atlas/transfer.py + tests/test_transfer.py (credits, collection zip,
   backup, restore with zip-slip/manifest/sha validation). Result inspected: 37 passed, ruff clean; code read.
   Finding accepted: server must not restore while the worker runs -> restore now refuses during a running
   job and joins the worker thread first (atlas/server.py).
2. task-mv9al476-5imman (2026-10-15, running) — offline tests + bug fixes for fetch/images/rights/providers.

## Verification evidence
(none yet)

## Blockers
(none)

## Recovery
If context is lost: read this file, the plan file above, `specs/*/tasks.md` (unchecked items are open), `git log`.
