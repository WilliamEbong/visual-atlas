# Visual Atlas — BUILD-STATE

Durable checkpoint for the autonomous build. Newest status first. Plan of record:
`C:\Users\Owner\.claude\plans\first-make-a-folder-iridescent-fountain.md` (approved 2026-10-15).

## Next concrete action
Phase 0 spikes: prove Claude image input (stream-json base64 block, tools off) and Codex image
input (`--image=`), live-smoke each provider and save fixtures under `tests/fixtures/providers/`.

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
- 2026-10-15: folder, `git init` (branch main), Spec Kit init + lean preset + Codex integration (claude default),
  CLAUDE.md = AGENTS.md, constitution v1.0.0, docs/FREE-IMAGE-SOURCES.md, .gitignore, keep-awake held.

## Remaining (phases)
0 spikes · 1 vertical slice (spec 001) · 2 connectors · 3 taxonomy + jobs · 4 library features ·
5 connections + briefs · 6 packaging + docs · 7 ingestion (~60 refs) + held-out · 8 converge, reviews, release.

## File ownership
- Claude: everything until a Codex task is recorded below.

## Codex delegated tasks
(none yet)

## Verification evidence
(none yet)

## Blockers
(none)

## Recovery
If context is lost: read this file, the plan file above, `specs/*/tasks.md` (unchecked items are open), `git log`.
