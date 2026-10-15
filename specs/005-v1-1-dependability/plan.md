# Plan 005 — v1.1

Stack unchanged (Python 3.14/uv/FastAPI/Typer/SQLite WAL/Pillow; React/Vite/TS). No new dependency. One
migration (`002_v11.sql`). Version 0.2.0 in `pyproject.toml`, `atlas/__init__.py`, `web/package.json`.

## Decisions
- **Maintenance coordination (FR-1–4).** `transfer.maintenance(home)` context manager: take a non-blocking
  OS lock on `<home>/maintenance.lock` (`msvcrt.locking` on Windows, `fcntl.flock` elsewhere; released by the OS
  if the process dies), then in one write transaction refuse if any job is queued/running/cancelling or holds a
  live lease, else write `settings.maintenance=<token>`. `Store.transaction()` (the single write path) checks the
  marker after `BEGIN IMMEDIATE` and raises `LibraryBusy` unless this store is the holder; a marker whose file
  lock can be taken is stale and is cleared in place. Release clears the marker (idempotent) and the lock in
  `finally`. Spike (2026-10-15): SQLite's backup API replaced a live WAL database's contents while another
  connection had it open, and that connection then saw the new rows and schema; a dead process's msvcrt lock
  was released and a second holder was refused.
- **Restore (FR-3).** Validate archive → extract staged db → if its `user_version` is older, migrate the staged
  copy with `Store` → full schema/integrity/FK/media validation → enter maintenance → safety backup (backups
  strip the marker from their snapshot) → copy archive media into `media/` additively (temp file + rename,
  checksum-verified) → `staged.backup(live)` (atomic contents swap; no file renames, so nothing can be left
  half-swapped and other processes' connections stay valid) → sweep orphans → leave maintenance. The server no
  longer stops its worker thread: the marker blocks claims and writes.
- **Media ordering (FR-4).** `images.prepare_files()` computes paths, hashes and encoded copies; the job commits
  `add_image` first and then `images.write_files()`; the crash-adoption path rewrites missing files; analysis of
  an image whose file is missing fails that item with a plain reason. Starter import inserts the row before
  copying files and re-copies missing files of known starter images. `transfer.sweep(home)` runs at app start
  only if it can enter maintenance (skipped while a job is live); orphans are computed from a snapshot taken
  after the marker is set.
- **Verification outcomes (FR-5, 6, 10).** `verify_image()` returns `checked | nothing | unavailable | invalid |
  retry` and raises for `cancelled`, pausing codes in a Verify job, and `daily_cap`. Unjudged proposals are
  `state='proposed'` without a "second model disagreed" note (existing semantics); judged in batches of ≤6, each
  batch saved with its verdicts atomically. Discovery records the outcome in the item reason and the summary
  counts checked images. Verify job: `checked` → item added/checked; `nothing` → skipped; `retry`/`invalid` →
  `_retry_or_fail`; `unavailable` → pause with the backend message.
- **Superseding (FR-9, 11).** `apply_analysis()` deletes unlocked annotations not in the applied set after
  writing an `annotation_history` row with `state='superseded'` and the new analysis id; unusable results go
  through the same path with an empty set. Status = `ready` if any non-rejected annotation remains.
  Migration 002 performs the same reconciliation for existing libraries (history rows, then delete).
- **Request coding (FR-12).** New `atlas/coding.py`: `code_request(text, fields, taxonomy)` → `{techniques:
  [{id, why, exact}], goals, subject_terms, constraints}` from word-boundary matches on names, aliases and
  observable cues (cues weigh less), goal names/descriptions, and guided fields (exact). `_fallback_queries`
  reuses it.
- **Directions (FR-13, 14).** `retrieve_for_brief(store, coding, limit)` scores ready images in SQL/Python:
  technique match by state (human 3, model_reviewed 2, proposed 1), goal links 1, FTS subject hits 1 each, id
  as tiebreak. Records (id, title, maker, date, summary, techniques with names) are added whole while the JSON
  stays under 24 000 characters (~40 records). Prompt allows 1–5 directions and an optional
  `insufficient_evidence` note; validator enforces citation and technique–image relationships; zero valid →
  job `done` with the insufficient-evidence message and nothing replaced. `GET /api/briefs/{id}` returns the
  coding for the page.
- **Discovery relevance (FR-15, 16).** Targets = explicit `technique_ids`, Grow gap ids, or exact coded
  techniques. Items get `payload.match = {techniques: [...], subject: bool}`; `_added()` counts matching
  additions when targets exist. Tombstones gain `source` (`user`/`auto`) and `rule_version`
  (analysis cache identity without the image hash); the skip query honours user tombstones always and auto ones
  only at the same version; a reconsidered auto-rejected item revives its removed row
  (`Store.revive_image`). The cross-job `no_technique` job-item cache is dropped (the tombstone covers it).
- **Retry-After (FR-7).** `FetchError.retry_after` flows into `_retry_or_fail`; delay = max(back-off,
  Retry-After) capped at one hour; pending query/eligible items of that provider get `next_attempt_at` raised;
  `Fetcher` keeps a per-provider cooldown and raises `rate_limited` immediately inside it.
- **Budgets (FR-8).** Defaults derived from target: downloads max(30, 2×target), analyses max(12, target+4),
  candidates max(80, 4×target), searches max(10, ceil(target/3)+4). Summary names the stopping reason.
- **Pagination (FR-17).** Server sorts end in `i.id`; page size ≤200. `Library.tsx` keeps pages in state keyed
  by the filter string, appends `offset=items.length`, drops responses whose key is stale.
- **Evaluation (FR-18–21).** `docs/evaluation/v1.1/`: `cases.json` (dev + final, provider, item id, image sha,
  reference, alternatives, uncertainty, notes, `provisional: true`), `freeze.json` (sha256 of final cases,
  prompts, model ids, metrics code), `scripts/eval_v11.py` (fetch → run arms → metrics → report),
  `briefs.json` + retrieval metrics (no AI), Jev gate criteria in `JEV-GATE.md` with a harness that runs only
  when `TYPESAFE_API_KEY` is set in the scratch eval environment.
- **Privacy wording (FR-22)** and **release gating (FR-23):** `ci.yml` becomes callable and gains a Windows job
  (pytest + installer smoke); `release.yml` calls it and packages only after it passes.

## Verification
Deterministic tests per FR (hook-based interleavings for FR-1–4); repro script rerun; full checks; Playwright
journeys (find/grow progress and partial outcomes, verify failure and resume, human edit across re-analysis,
filters/pagination/Back/stale responses, directions incl. insufficient evidence, restore maintenance, keyboard,
375 px, console and failed requests); fresh install + upgrade from the v0.1.0 zip; local release zip.
