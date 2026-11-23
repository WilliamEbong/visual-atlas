# 008 session log (append-only)

- 2026-11-22 Start. Baseline on 9aaafa1-derived worktree: 372 backend passed / 9 live deselected. Resume cron fafcd8a7 (hourly :17), keep-awake on.
- 2026-11-22 Decision: feature dir specs/008-reference-desk; build docs = BUILD-STATE.md + this log + spec/plan/tasks (no separate BUILD-PLAN). Undo: delete the folder.
- 2026-11-22 Research by Opus subagent: docs/research/01–04. Thesis A adopted (docs/research/05-thesis.md).
- 2026-11-22 Decision: MCP via stdlib JSON-RPC, not the official SDK. Reason: `mcp` needs pywin32 on Windows; uv failed to install it 3× (file lock, then invalid wheel entry). Undo: replace atlas/mcp_server.py with an SDK MCPServer.
- 2026-11-22 Decision: design-system images indexed in place (never in SQLite, never copied). Enabled by VISUAL_ATLAS_DESIGN_SYSTEMS=auto|paths. Canonical copies: C:\Users\Owner\.claude\skills\<system>\ (850 images, all rows map to files).
- 2026-11-22 Decision: generated images assert no licence; excluded from publishable filter. Target gaps: symmetry, vantage-point, proximity-grouping, figure-ground-ambiguity (2 starter examples each), selective-focus (3).
- 2026-11-22 Decision: router ties go to archive-of-looking (owner default). Other layers keep up to half the result places so library volume never hides them.
- 2026-11-22 Real MCP round trip: official SDK 2.3.0 client (pip in scratch venv; npx inspector run was refused by the permission classifier) -> `uv run atlas mcp`. Negotiated 2025-11-25 after server/discover fallback; advise, view_reference (JPEG), traversal refused. Evidence docs/evaluation/v0.5/mcp-roundtrip.json (design systems off); design-system run kept outside the repo in the session notes folder.
- 2026-11-23 Design review (william-web-design reviewer, Opus) on Ask/Welcome: 12 findings; applied 1–7, 9–12; skipped 8 (header specimens on Ask; nice-to-have). Welcome "Check the assistants" button dropped (Settings is in the nav).
- 2026-11-23 CLI on 8 real briefs: 6/8 read a goal/technique; 2 misses left untuned on purpose (docs/evaluation/v0.5/CLI-BRIEFS.md).
- 2026-11-23 Library drawers minmax 240->200 so five ways in fit one row at 1440.
- 2026-11-23 Generated layer (Opus subagent via Codex companion): 12 generated, 9 kept, 3 dropped (all figure-ground; rubric checks 1/3/7). I independently viewed all 9 (contact sheet) and fg-ambiguity-01 full size: pass. Fixed its script's E731 lint. 1.4 MB.
- 2026-11-23 Observed 1.5–8.5 s /api/desk responses in the browser while the generator and the test suite were running; once the machine was idle: 70–315 ms in the browser, 0.07–0.6 s over HTTP, 0.1–0.3 s in-process. Recorded as load, not a defect.
- 2026-11-23 Full offline suite: 422 passed / 9 live deselected (baseline 372). Codex adversarial review started on f9e400c..HEAD.
- 2026-11-23 Codex adversarial review round 1 (base f9e400c): 7 findings, all confirmed and fixed (e9bbd1f); regression tests fail on old code (9 cases). Round 2: fixes confirmed, 4 new findings, all fixed (round-2 commit); 4 tests fail on old code. Review rounds stop at 2 (project convention).
- 2026-11-23 Design-system plates now say "Private design system: reference only" (0c07d87). Browser check with design systems on: garden-of-lingering routing, 12/12 token-protected images, 0 console errors; screenshot kept outside the repo.
- 2026-11-23 Decision: no separate HANDOFF.md; OVERNIGHT-CHANGES.md + BUILD-STATE.md serve as the handoff (owner asked for OVERNIGHT-CHANGES). Dev servers stopped; Playwright browser closed.
