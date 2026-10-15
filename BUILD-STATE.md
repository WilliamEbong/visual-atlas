# Visual Atlas — BUILD-STATE

Durable checkpoint for the autonomous build. Newest status first. Plan of record:
`C:\Users\Owner\.claude\plans\first-make-a-folder-iridescent-fountain.md` (approved 2026-10-15).

## Next concrete action
v1.1 is complete and committed locally on main (package 0.2.0; not pushed or tagged). Both review rounds are folded
in and the gates pass. release/VisualAtlas-v0.2.0.zip is built from the commit that carries this file. Next, only on
the owner's go-ahead: push main, tag v0.2.0 (the release workflow runs Checks on Linux and Windows, then packages),
and let Pages rebuild the demo. Deferred scope is listed under "v1.1 decisions".

## v1.1 status (2026-10-15)
- Baseline on 680b199 (scratch home): pytest 290 passed / 7 live deselected; ruff clean; taxonomy check OK;
  tsc clean; vitest 6 passed; web build OK; data guard clean; pip-audit and npm audit clean. Python 3.14.3,
  uv 0.11.29, Node 24.14.1, codex-cli 0.160.0, Claude Code 2.1.284.
- Reproduced on 680b199 (docs/evaluation/v1.1/repro-before.json): restore loses an acknowledged collection;
  second server start deletes a worker's media; quota verifier reported "checked" with 0 saved; 4+3 proposals
  leave 7 active vs a 6-verdict contract, empty analysis leaves 7 labels with status unanalyzed; a direction with
  no images accepted; directions prompt JSON truncated mid-record; Retry-After unused; target 40 gets 30 downloads.
- Working principles recorded in specs/005-v1-1-dependability/spec.md.
- Owner input mid-run: (1) evaluate "request coding" like Qualia's qualitative coding -> adopted as FR-12
  (deterministic coder; Jev as gate arm). (2) "The public version must not use my key; users bring their own"
  -> any Jev integration is bring-your-own-key, off by default. (3) "Use qualia key for local evaluation" ->
  the live Jev evaluation may use the Qualia TypeSafe key, loaded into the eval process only (never printed,
  logged, copied into this repo or used by the app).
- Version decision: 0.2.0 (repo uses 0.x semver + v tags; behaviour change + migration -> minor bump).

### v1.1 decisions (reversible, logged)
- Restore swaps database contents with SQLite's backup API under a maintenance lock + marker (no file renames),
  so an interruption leaves the old or the new library; media is copied additively and orphans swept.
- Superseded model labels: a history row (state 'superseded') then the annotation row is removed; no schema change
  to the annotations CHECK constraint. Verification batches of 6 remain as a guard for upgraded libraries.
- Request coder (atlas/coding.py) uses technique names, aliases and distinctive name words, and goal names and
  descriptions. Observable-cue sentences are NOT matched (T529): in trials their common words ("dark", "subject",
  "background") produced spurious tags. Cue matching was dropped rather than tuned against the frozen briefs.
- Coder stopword gaps seen in the browser ("against", "flyer") were left unfixed: those words occur in the frozen
  evaluation briefs, so changing them now would tune on the test set. Fix in the next iteration with new briefs.
- Find/Grow add analysed images that do not show the requested technique as ordinary references, reported
  separately; only matching ones count toward the target.
- Checker: the independent-first prompt was adopted on the pre-registered dev rule (weak evidence, equal cost).
- Jev: only relevance ranking for project help is integrated (optional, off by default, bring-your-own key,
  text only). Request coding, metadata classification and text-only review were not integrated (REPORT.md).
- Release workflow calls the Checks workflow (Linux + new Windows job) and packages only after it passes; not yet
  exercised on GitHub (no push in this iteration).

### v1.1 evidence (2026-10-15)
- Reproductions: docs/evaluation/v1.1/repro-before.json (run on a detached worktree of 680b199) vs repro-after.json:
  write during restore now refused (503) instead of acknowledged and lost; second server start no longer deletes a
  running job's files (job finishes, files present); quota verifier pauses the job (0 verifications counted);
  4 then 3 proposals leave 3 active (old ones superseded with history); an uncited direction is rejected; prompt
  JSON complete; Retry-After honoured; target 40 gets 80 downloads / 44 analyses.
- Tests: 343 passed, 7 live deselected after both review rounds (290 at baseline; 337 before review); new files test_maintenance (9 deterministic
  interleavings incl. a second process and a v0.1 backup), test_checks (10), test_coding (6), test_discovery (4),
  test_jev (5), plus retry/budget/stop/pagination tests. ruff, tsc, vitest (7), build, data guard, pip-audit,
  npm audit all clean. No key or token in the tree or history (prefix scan of the TypeSafe key: 0 hits).
- Browser (Playwright, scratch libraries): pagination (offset=60 only, 85 unique, keyboard across pages), filter
  reset and Back; stale page ignored after a filter change (delayed route, T527); targeted Find ending "Stopped
  short" with matching vs other additions and the analysis-limit reason (found and fixed a real defect: a spent
  job waited ~1 h on a rate-limited source); verify paused at a usage limit then resumed with real Claude under
  the new prompt; a person's confirm/reject surviving CLI re-analysis with superseded history; grounded Codex
  directions (5, none dropped) and the no-evidence message; live restore in the running app; a write refused during
  maintenance held by another process, then accepted; 375 px on 6 screens without overflow; demo paging; console
  errors only from deliberate restarts and the deliberate 503. Screenshots: design-review/v1.1/.
- Install/upgrade: published v0.1.0 zip installed, used (collection, confirm, reject, removal, backup), then local
  v0.2.0 zip installed over it: schema 2, atlas.db.v1.bak kept, decisions and collection intact, the removal
  classified 'user', v0.1 backup restores under 0.2; fresh v0.2.0 install: 85 starter, doctor ready, serves 0.2.0.
  Deep extraction paths (~25 chars deeper) broke uv's venv on Windows (path length): documented short-path advice.
- Evaluation: docs/evaluation/v1.1/REPORT.md (dev/final splits, provisional builder labels, retrieval, Jev gate).

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
- Claude owns all tracked files for v1.1. `.codex-remote-attachments/` (untracked, created 09:28 by the Codex
  desktop app) is not ours: left untouched and excluded locally via .git/info/exclude.

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
7. v1.1 adversarial review round 1 (base 680b199, 2026-10-15): 4 reproduced findings, all accepted and fixed with
   regression tests that fail on the old code (7760d43, 49fc78c): [high] restore let writes in during its file sweep
   (the restored contents now carry the marker); [high] a crash between saving a row and writing its files was not
   repaired once a budget was spent (repair now precedes budget checks); [medium] an unavailable verifier stayed
   skipped for later jobs in the same worker (reset per job); [medium] library paging could stall when offsets
   shifted (advance by server rows consumed). Round 2 is the last (bound of 2 for v1.1).
8. v1.1 adversarial review round 2 (final, 2026-10-15): confirmed all four round-1 fixes; 2 new findings, both fixed
   with regression tests that fail on the old code (be18152): [medium] a verification saved just before a crash was
   reported as "not checked" when the job resumed, in Verify and in Find/Grow (a check this job already saved now
   counts); [medium] prompt data was clipped at 1200 characters, cutting the end of accepted briefs (now 4000, the
   longest accepted brief). Review rounds stop here (bound of 2); these two fixes are verified by tests only.

## Verification evidence
- Published 2026-10-15: https://github.com/WilliamEbong/visual-atlas (public), Pages demo
  https://williamebong.github.io/visual-atlas/ (Playwright: 85 references, technique page, images, no console errors),
  release v0.1.0 with VisualAtlas-v0.1.0.zip (25.0 MB). CI "Checks" green on Ubuntu (ruff, pytest, taxonomy, data
  guard, pip-audit, npm typecheck/test/build/audit, gitleaks). First run failed only on gitleaks false positives
  (starter cache-key hex digests) -> .gitleaks.toml allowlist limited to that line shape in starter/library.json.
  The tag push did not start the release workflow, so it was dispatched on the tag (`gh workflow run release.yml
  --ref v0.1.0`). The published zip was downloaded, installed into a scratch home and passed `atlas doctor`.
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
