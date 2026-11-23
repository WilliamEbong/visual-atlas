# 008 Plan

## Approach
- `atlas/layers.py` (new): reads the generated manifest and the design-system CSVs in place, with `lru_cache`
  keyed on mtime.
- `atlas/desk.py` (new): `references`, `search`, `advise`, `route`, `guidance`, `get`. It reads the library through
  `jobs.open_store` and writes nothing.
- `atlas/mcp_server.py` (new): a stdlib JSON-RPC 2.0 stdio loop. Methods: `initialize`, `ping`, `tools/list` and
  `tools/call`, plus notifications. Tool results carry `structuredContent` and a JSON text block. `view_reference`
  returns image content, a Pillow thumbnail made in memory.
- `atlas/cli.py`: `advise`, `refs`, `ref`, `mcp`. `atlas/home.py` allows the `VISUAL_ATLAS_DESIGN_SYSTEMS` setting.
- `atlas/server.py`: `GET /api/desk` (advise), `GET /api/desk/ref`, `GET /api/desk/media` (layer refs only, looked
  up by ref).
- `web/`: `Ask.tsx`, nav entry, types; then the design pass across shell, Library, image page and Find.
- `generated/`: RUBRIC.md, manifest.json, images (1024 px JPEG). They are made by `scripts/generate_images.py`
  through the Codex companion, with the prompt on stdin. It is a maintainer script, not app runtime.
- `.gitignore` and `tests/test_layers.py` keep design-system files out of git.

## Constitution check
- Rights: library eligibility is unchanged. The other layers are labelled and excluded from `publishable`. The
  constitution moves to 1.1.0 and records reference layers outside the library.
- Evidence: reasons quote stored evidence. The generated layer's techniques are "intended", never "reviewed".
- Ordinary code: no new dependency, deterministic ranking.
- Local and safe: stdio only, read-only, ref ids instead of paths, validated inputs.

## Steps
1. Layers and desk engine, with tests.
2. CLI and MCP server, with tests and a real client round trip.
3. Generated layer: rubric, generation, review, manifest.
4. Web Ask page and API, then the design pass, then Playwright.
5. Docs, evaluation outputs, Codex review, OVERNIGHT-CHANGES.md.
