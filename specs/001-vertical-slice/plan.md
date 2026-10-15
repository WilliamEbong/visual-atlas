# Plan 001 — Vertical slice

## Technical context
- Python 3.14 via uv; FastAPI + uvicorn; Typer CLI; pydantic 2; httpx (installed with the stack)
  for provider HTTP; Pillow for images; SQLite (stdlib) with FTS5.
- Web: React 19, Vite, TypeScript, Tailwind 4 (same versions as Qualia); hash routing; no router,
  query or state library.
- Patterns copied from Qualia (same owner, MIT): `process.py` transport, Claude/Codex argv and auth
  checks, Store core (migrate + backup, transactions, read authorizer), server middleware, launcher,
  web `client.ts`.

## Spike results (2026-10-15)
- Codex 0.160.0: `exec ... --image=<file> -` with every tool feature disabled returns a schema-valid
  description of the actual pixels (gpt-6-luna, ~9.7k input tokens, ~4 s).
- Claude Code 2.1.284: `-p --input-format stream-json --output-format stream-json --verbose
  --json-schema ... --tools ""` with one stdin user message containing a base64 image block returns
  `structured_output` in the `result` event (2 turns: the StructuredOutput tool), no permission
  denials.
- Providers: Met `/v1/search` was retired 2026-10-01 → use `/v1.1/search` (offset/limit; no
  public-domain filter, so check `isPublicDomain` per object). AIC IIIF image requests need the
  `AIC-User-Agent` header (documented courtesy header; without it Cloudflare challenges — never
  bypassed). Cleveland's image CDN returned HTTP 521 during the spike (transient outage → provider
  failure path). Smithsonian DEMO_KEY rate-limit header showed 10/hour. Commons search supports
  `haswbstatement:P275=Q6938433` (CC0), `P275=Q20007257` (CC BY 4.0), `P6216=Q19652` (public domain).
- Slice provider therefore: Art Institute of Chicago.

## Structure (slice subset of the full layout)
```
atlas/__init__.py      version
atlas/home.py          data home + media paths + local .env settings
atlas/store.py         only SQL writer
atlas/migrations/001_initial.sql
atlas/data/taxonomy.json, atlas/data/source_policies.json
atlas/catalog.py       load/validate/sync data files
atlas/rights.py        eligibility rules
atlas/providers.py     provider search → Candidate
atlas/fetch.py         safe download
atlas/images.py        validation, copies, metrics, dHash
atlas/ai/process.py, claude_cli.py, codex_cli.py, fake.py, tasks.py
atlas/jobs.py          job + items + lease + worker
atlas/server.py        API + SPA + /media
atlas/cli.py           commands
web/                   React app
tests/                 pytest
```

## Design decisions
- One job runs at a time (global lease) — keeps subscription and provider limits safe.
- Analysis cache key: analysis-copy sha + taxonomy sha + prompt sha + backend + model.
- `/media/*` serves only content-addressed files under the data home, no token (img tags cannot
  send headers) but Host/Origin checks and `Cross-Origin-Resource-Policy: same-origin` apply.
- The worker runs as a thread inside the app process; `atlas worker` runs the same loop from a
  terminal (either agent) and respects the lease.
