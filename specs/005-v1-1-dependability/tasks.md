# Tasks 005 — v1.1

## Phase 1: Setup
- [ ] T501 Baseline on 680b199 in scratch homes, repro of all review findings, principles recorded (docs/evaluation/v1.1/, BUILD-STATE.md)
- [ ] T502 Version 0.2.0 and migration 002 (tombstone source/rule_version, annotation reconciliation) (pyproject.toml, atlas/__init__.py, web/package.json, atlas/migrations/002_v11.sql)

## Phase 2: Foundational — data preservation (US1, US2)
- [ ] T503 Maintenance lock + marker, LibraryBusy in Store.transaction, stale-marker recovery, claim refusal (atlas/store.py, atlas/transfer.py)
- [ ] T504 Restore rebuilt: validate/migrate staged copy, safety backup without marker, additive media, atomic backup-API swap, sweep, guaranteed release; API 503 handler; route no longer stops the worker (atlas/transfer.py, atlas/server.py, atlas/cli.py)
- [ ] T505 Media written after the row; adoption rewrites files; missing-file analysis fails plainly; starter import order; sweep only under maintenance (atlas/images.py, atlas/jobs.py, atlas/transfer.py, atlas/server.py)
- [ ] T506 Worker handles LibraryBusy (stop, resume later) (atlas/jobs.py)
- [ ] T507 Deterministic interleaving tests: write during restore, second restore, worker during restore, failure mid-restore, stale marker, v0.1.0 backup restore, sweep during download, abandoned orphan cleanup (tests/test_maintenance.py)

## Phase 3: US3 + US4 — truthful jobs and coherent annotations
- [ ] T508 Superseding in apply_analysis (history rows, unusable path, status) + tests (atlas/store.py, atlas/jobs.py, tests/test_store.py)
- [ ] T509 verify_image outcomes, batching ≤6, discovery reporting, Verify job retry/pause/counts + tests for quota, timeout, malformed, cancel, missing image, human decisions untouched (atlas/jobs.py, tests/test_jobs.py)
- [ ] T510 Retry-After: fetcher cooldown, persistent provider delay, cap + tests (numeric, HTTP-date, malformed, longer than back-off) (atlas/fetch.py, atlas/jobs.py, tests/test_fetch.py, tests/test_jobs.py)
- [ ] T511 Budgets scale with target; stopping reason in summary + tests (atlas/jobs.py, tests/test_jobs.py)

## Phase 4: US5 + US6 — relevance and grounding
- [ ] T512 Request coder + tests; _fallback_queries reuses it (atlas/coding.py, atlas/jobs.py, tests/test_coding.py)
- [ ] T513 Directions retrieval, complete records within budget, validator relationships, 1–5 + insufficient evidence, brief coding endpoint + tests (atlas/jobs.py, atlas/ai/tasks.py, atlas/server.py, tests/test_tasks.py, tests/test_jobs.py)
- [ ] T514 untrusted() clips values, never JSON mid-record (atlas/ai/tasks.py)
- [ ] T515 Find/Grow match marking, targets count matches, summary; tombstone source/version, revive; drop no_technique cache + tests (atlas/jobs.py, atlas/store.py, tests/test_jobs.py)
- [ ] T516 UI: project page shows reading of the brief and insufficient evidence; job progress shows matching vs other additions and check counts; history shows superseded labels; 503 restoring message (web/src/components/*.tsx)

## Phase 5: US7 — pagination
- [ ] T517 Deterministic sort tiebreaks, page cap; Library pages with offset, reset, stale guard + vitest for the page reducer (atlas/server.py, web/src/components/Library.tsx, web/src/lib/library.ts)

## Phase 6: US8 — evaluation
- [ ] T518 Clarify v1 HELDOUT.md meaning (dev/regression set, builder labels, label-level agreement)
- [ ] T519 Case pack (dev + final, sources, hashes, references, alternatives, uncertainty), freeze file, eval harness with metrics and arms (current checker vs independent-first) (docs/evaluation/v1.1/, scripts/eval_v11.py)
- [ ] T520 Run dev arms, decide checker approach, freeze, run final once; report (docs/evaluation/v1.1/REPORT.md)
- [ ] T521 Retrieval/coding evaluation on frozen briefs (recency vs relevance) (docs/evaluation/v1.1/briefs.json, scripts/eval_v11.py)
- [ ] T522 Jev decision gate: criteria, harness (key-gated), decision per use (docs/evaluation/v1.1/JEV-GATE.md)

## Phase 7: Polish and release
- [ ] T523 Privacy wording everywhere; docs updated for final behaviour (README.md, QUICK-START.md, docs/USER-GUIDE.md, web/src/components/Welcome.tsx, Settings.tsx)
- [ ] T524 CI callable + Windows job; release needs checks (.github/workflows/*.yml)
- [ ] T525 Full checks; repro-after; Playwright journeys; fresh install + upgrade from v0.1.0; local release zip
- [ ] T526 Independent review, fixes, converge, BUILD-STATE handoff
