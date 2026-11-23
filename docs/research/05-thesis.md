# Product thesis (decided 2026-11-22)

**For** designers and art directors, and the AI agents (Claude Code, Codex) that now make visual choices for them
in decks, sites and posters.

**The job:** turn a design brief into a few references worth borrowing from. Each one says which technique it shows,
the visible evidence for that reading, how sure the reading is, the licence and credit, and how to apply the idea
without copying the picture.

**Why it is different:** reference tools store pictures, not reasons (01-landscape, 03-gaps §3). Agent image tools
return URLs with no licence and no reason (02-agent-tools). The one licence-aware museum MCP found
(`open-museum-mcp`) has no ranking and no design reasoning. Visual Atlas already holds per-image evidence, review
states and deterministic rights records. Putting those behind an agent interface is the product; the rest of the
market does not have that data.

**Smallest proof:** one deterministic engine (`atlas/desk.py`) behind three doors: the CLI (`atlas advise`,
`atlas refs`, `atlas ref`), a read-only MCP server (`atlas mcp`), and an "Ask" page in the app. Each result carries
its reasons, licence, credit and a layer label. Two labelled layers sit beside the licence-checked library: a small
set of generated images that fills thin techniques, and the owner's four design-system libraries, which exist only
on his machine.

## Reasoning

- Research recommendation A (04-synthesis) is adopted. B (the private libraries) and C (generated images) are
  built now because the owner asked for them, but only as plug-in layers with their own labels. They never enter
  the licence-checked pool. `use="publish"` filters to CC0, public domain and CC BY.
- No AI in the desk. Ranking uses stored readings, taxonomy links and words. Agents can pass technique and goal
  ids directly, which avoids the weak point of word matching (BRIEF-REPORT recall 60%).
- "Suggest directions" stays in the app as an AI job. The MCP server is read-only and never starts model work or
  downloads. Agents that want more images are told the CLI command.
- The MCP protocol is implemented with the standard library (stdio JSON-RPC, handshake versions up to 2025-11-25).
  The official Python SDK needs pywin32 on Windows, and uv could not install that wheel here (it failed three
  times with a file lock and then an "invalid entry" error). The one-zip installer would hit the same failure.
  A real external MCP client verifies the protocol.

## How it will be judged

- Built now: tests for the engine, CLI and MCP server; an MCP round trip from a real client; the CLI run on real
  briefs; Playwright screenshots of the new page.
- Not provable tonight: research's blind test, where the owner rates agent output with and without the desk on
  12–20 of his own briefs. The briefs file and protocol are prepared (`docs/evaluation/v0.5/BLIND-TEST.md`); the
  ratings must come from the owner.

## Later

The research synthesis Later list, plus: an MCP `suggest_directions` behind an explicit opt-in; visual-similarity
search (needs embeddings, a measured need first); UI and typography references (the corpus is mostly
pre-20th-century art); C2PA manifests on generated files; a hosted or HTTP MCP transport.
