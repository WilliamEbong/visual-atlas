# Plan 003 — Explore, connections and project help

- `/api/graph?focus=` builds the ego network on the server; `web/src/lib/graph.ts` lays it out in
  rings (pure and unit-tested) and Cytoscape.js draws it with a preset layout, loaded on demand.
- Directions use the `directions` task in `atlas/ai/tasks.py`, with the library summary passed as
  untrusted data and every cited id checked against the library.
