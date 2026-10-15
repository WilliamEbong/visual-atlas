# Spec 003 — Explore, connections and project help

## Functional requirements
- FR-1 Explore: goals as entry points; a goal page lists the techniques that serve it with a sample
  image; a technique page shows definition, explanation, where to look, when it helps, confusions,
  limits, counterexample, related techniques, goals/operations/domains, examples and sources (or a
  working-definition note).
- FR-2 See connections: one focus (goal, technique or image) at a time, depth at most two, a stable
  ring layout, pan/zoom/fit, select to refocus, and a list view giving every connection as text.
- FR-3 Help with my project: saved briefs; a directions job returns three to five directions that
  cite only real technique and image ids (invented ids dropped), each with an idea, rationale,
  execution suggestions and tradeoffs; keep/dismiss; saved, so reopening costs nothing.

## Success criteria
Graph integrity and directions-grounding tests pass; Playwright navigates the map and the list and
creates a brief that receives grounded directions.
