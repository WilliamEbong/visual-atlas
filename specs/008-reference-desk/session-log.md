# 008 session log (append-only)

- 2026-11-22 Start. Baseline on 9aaafa1-derived worktree: 372 backend passed / 9 live deselected. Resume cron fafcd8a7 (hourly :17), keep-awake on.
- 2026-11-22 Decision: feature dir specs/008-reference-desk; build docs = BUILD-STATE.md + this log + spec/plan/tasks (no separate BUILD-PLAN). Undo: delete the folder.
- 2026-11-22 Research by Opus subagent: docs/research/01–04. Thesis A adopted (docs/research/05-thesis.md).
- 2026-11-22 Decision: MCP via stdlib JSON-RPC, not the official SDK. Reason: `mcp` needs pywin32 on Windows; uv failed to install it 3× (file lock, then invalid wheel entry). Undo: replace atlas/mcp_server.py with an SDK MCPServer.
- 2026-11-22 Decision: design-system images indexed in place (never in SQLite, never copied). Enabled by VISUAL_ATLAS_DESIGN_SYSTEMS=auto|paths. Canonical copies: C:\Users\Owner\.claude\skills\<system>\ (850 images, all rows map to files).
- 2026-11-22 Decision: generated images assert no licence; excluded from publishable filter. Target gaps: symmetry, vantage-point, proximity-grouping, figure-ground-ambiguity (2 starter examples each), selective-focus (3).
- 2026-11-22 Decision: router ties go to archive-of-looking (owner default). Other layers keep up to half the result places so library volume never hides them.
