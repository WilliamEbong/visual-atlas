# Tasks 001 — Vertical slice

## Setup
- [ ] T001 pyproject.toml (uv, deps, scripts `atlas` + gui `visual-atlas`, pytest live marker, ruff) and `uv sync`
- [ ] T002 web/ scaffold (package.json, vite, tsconfig, Tailwind, index.html) and `npm ci`

## Foundational
- [ ] T003 atlas/home.py data home rules (refuse repo/OneDrive), media dirs, local .env settings
- [ ] T004 atlas/migrations/001_initial.sql full schema + atlas/store.py (migrate, backup, transactions, rows authorizer)
- [ ] T005 atlas/data/taxonomy.json (goals, operations, domains, 6+ full techniques) + atlas/data/source_policies.json
- [ ] T006 atlas/catalog.py load/validate/sync with dangling-reference failure
- [ ] T007 atlas/rights.py AIC rule + labels; tests/test_rights.py
- [ ] T008 atlas/fetch.py safe download; tests/test_fetch.py
- [ ] T009 atlas/images.py validate/copies/metrics/dHash; tests/test_images.py
- [ ] T010 atlas/ai/process.py (Qualia copy + cancel event), atlas/ai/codex_cli.py and claude_cli.py with image input, atlas/ai/fake.py
- [ ] T011 atlas/ai/tasks.py analysis prompt + schema + validator; tests/test_tasks.py

## User story: find → analyse → show
- [ ] T012 atlas/providers.py AIC search → Candidate; fixture test
- [ ] T013 atlas/jobs.py job/items/lease/worker for `find`; tests/test_jobs.py (resume, second worker blocked)
- [ ] T014 atlas/server.py API (library, image, technique, search, jobs, media) + SPA serving + middleware
- [ ] T015 atlas/cli.py (serve, find, worker, jobs, taxonomy check)
- [ ] T016 web: library grid, image page, technique page, search, find form with job progress

## Verification
- [ ] T017 Live: run a Find job with Codex and with Claude (≥3 images total), record evidence
- [ ] T018 Playwright: scenarios 1–4 incl. restart; screenshots in design-review/slice/
- [ ] T019 BUILD-STATE.md evidence + commit
