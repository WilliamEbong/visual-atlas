# Visual Atlas — BUILD-STATE

Durable checkpoint for the autonomous build. Newest status first. Plan of record:
`C:\Users\Owner\.claude\plans\first-make-a-folder-iridescent-fountain.md` (approved 2026-10-15).

## Next concrete action
Publish: create public repo WilliamEbong/visual-atlas, push main, enable Pages (GitHub Actions), tag v0.1.0,
check CI/release/Pages, then record the results here and give the owner the final report.

## Owner decisions (2026-10-15 plan gate)
- Publish like Qualia: public repo `WilliamEbong/visual-atlas`, Releases zip, read-only Pages demo —
  only after tests, Codex review and secret/data scans pass. Overrides the brief's "no public deploy".
- AI split: Codex proposes annotations; Claude Code does the second-model check (`model_reviewed`) and
  the held-out challenge.
- Help material: illustrated guide, quick-start, in-app welcome, README screenshots, GIF tour (no videos).

## Assumptions and decisions (Claude)
- Reuse Qualia's stack and patterns (same owner, MIT): Python 3.14/uv/FastAPI/Typer/SQLite + React/Vite/TS with plain CSS tokens (no Tailwind).
- Project folder `C:\Users\Owner\OneDrive\Documents\VisualAtlas`; data home `%USERPROFILE%\VisualAtlas` (outside OneDrive).
- Enabled providers: Met, AIC, Cleveland, Smithsonian (DEMO_KEY or owner key), Wikimedia Commons (CC0/PD/CC BY only).
  Disabled with evidence: Unsplash (hotlink + ML-dataset clause), Pexels, Pixabay (AI/ML clauses), others = later candidates.
- `/design` is the Claude Desktop host command that creates a "Design" Artifact canvas (not a skill file); style input archive-of-looking.
- Spec Kit project skills were installed after this session started, so the Skill tool cannot load them by name;
  the build follows the installed `.claude/skills/speckit-*/SKILL.md` instructions directly (read 2026-10-15, lean preset).
- WELCOME-BACK.md (the owner handoff) stays local and gitignored: it is personal and lists local paths.
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
- No Codex task running. Claude owns all files.

## Codex delegated tasks
1. task-mv9a1vza-xi4tsp (2026-10-15) — atlas/transfer.py + tests/test_transfer.py (credits, collection zip,
   backup, restore with zip-slip/manifest/sha validation). Result inspected: 37 passed, ruff clean; code read.
   Finding accepted: server must not restore while the worker runs -> restore now refuses during a running
   job and joins the worker thread first (atlas/server.py).
2. task-mv9al476-5imman (2026-10-15) — offline tests + fixes for fetch/images/rights/providers: 136 tests; 7 fixes
   (malformed URLs/redirects, empty userinfo, HTTP-date Retry-After, precise missing-image reason, CC BY link must match
   the stated version, dict-shaped Commons pages). Diff read and accepted.
3. task-mv9bjogp-h6q1pb (2026-10-15) — independent read-only architecture/code review. 20 verified findings; all accepted:
   - Codex task 4 fixed #1 restore validation (integrity, FKs, version, tables, triggers, media), #4 backup reads media
     references from its own snapshot, #6 starter path traversal, #16 starter images in collection exports.
   - Claude fixed #2 (any live lease blocks a claim; image/analysis/annotation writes fenced in the same transaction),
     #3 (web data hook never returns a previous page's record; image actions wait for the matching record),
     #5 (generic insert/update only accept real column names), #7 (private-peer check at TCP connect via httpx trace,
     before any HTTP bytes), #8 (adopt own image after a crash; cached analysis before budget; resume a missed
     verification), #9 (verify/analyse jobs wait for retries), #10 (pause/cancel mid-call never marks failed),
     #11 (filters no longer suppress candidates for other jobs), #12 (explicit budgets kept; candidate batch capped),
     #13 (a model never checks its own proposal), #14 (documented intent must restate the description text),
     #15 (only recognised PD names and policy-listed CC BY versions), #17 (paging cap 5000), #18 (honest privacy text),
     #19 (malformed Claude envelopes are recorded failures), #20 (dead code removed).
   - Gap noted by the review (adapter argv/env/event handling untested) closed by tests/test_adapters.py.
4. task-mv9c6ruu-ej6r51 (2026-10-15) — transfer findings #1/#4/#6/#16 with tests: 57 passed in its files; full suite 283.
5. Adversarial review round 2 (base 01e5953): 9 findings, all fixed in aee4c4b (fenced and guarded automatic removal,
   leases valid only while unexpired, restore of a library with missing media, full schema comparison, pause->cancel
   stops the worker, resumable and atomic verification, no model-authored intent, late web answers ignored).
6. Adversarial review round 3 (final, base 01e5953): confirmed round-2 fixes; 2 new findings, both fixed with
   regression tests: [high] slow searches/downloads let the lease expire (the heartbeat now covers every step, not only
   AI calls); [medium] a cancel or pause arriving during a quick resume could be overwritten (queued->running is now
   conditional, then the state is read again). Review rounds stop here (bound of 3).

## Verification evidence
- Release zip (local build, 24.6 MB) extracted to a scratch folder; `scripts/install-atlas.ps1 -NoShortcuts -NoLaunch`
  with a scratch VISUAL_ATLAS_HOME: dependencies, screens, starter (85 references), `atlas doctor` (Codex 0.160.0 and
  Claude 2.1.284 ready); the installed server showed the welcome dialog and 85 references (Playwright,
  design-review/journeys/10-fresh-install-welcome.png).
- Demo built from the starter (85 images, 20 MB) and checked in Playwright: library, image page, credits, no errors.
- README media taken with Playwright from the real library and a scratch copy of it (find and project directions
  were live runs there: 2 images added by Codex + Claude check; 4 grounded directions by Codex).
- Offline: `uv run pytest` 290 passed (7 live deselected); `npm --prefix web test` 6 passed; ruff clean; tsc clean.
- Real library (`%USERPROFILE%\VisualAtlas`): 85 ready references after curation (removed an order form and a burst
  frame), all 26 techniques with >=1 example, 24 with >=2; annotations 169 model_reviewed, 46 proposed.
- Held-out challenge: docs/evaluation/HELDOUT.md (two rounds; builder judgment, not expert ground truth).
- Live (2026-10-15): Codex analyse + Claude verify via CLI (AIC); Claude analyse + Codex verify via UI (Commons);
  Codex directions for a brief (4 grounded directions); Codex plan step; Claude haiku/sonnet aliases resolve to
  claude-haiku-4-5 / claude-sonnet-5-5 (recorded per analysis).
- Playwright (screenshots in design-review/slice and design-review/journeys): welcome dialog, library grid,
  image detail (proposer/checker shown), reject + edit correction persisted, technique page → related technique,
  search, restart persistence, Find via UI with progress stages, collections create/save, compare 2 images,
  connections map, project directions, settings AI status, backup, remove → restore (image, media, annotations back),
  375 px: no horizontal overflow on 11 screens, keyboard grid arrows with visible focus, no console errors after fixes.

## Blockers
(none)

## Recovery
If context is lost: read this file, the plan file above, `specs/*/tasks.md` (unchecked items are open), `git log`.
