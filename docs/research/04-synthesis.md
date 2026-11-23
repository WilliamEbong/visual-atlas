# 04 — Synthesis: where Visual Atlas can be unique, and what to build next

Based on `01-landscape.md`, `02-agent-tools.md` and `03-gaps.md`. The claims
about competitors cite those files. This file is judgement, and I mark it as such.

## Where Visual Atlas stands relative to the field

Commodity, or already done well elsewhere. Do not compete here:

- **Visual-similarity search.** Same Energy, Cosmos, Savee and ShotDeck have it.
- **A licence gate over museum APIs.** `open-museum-mcp` already applies a strict
  "unclear ⇒ drop" rule across about 11 museums, with confidence and citations, free.
- **Image generation.** There are dozens of MCP wrappers.
- **Boards and canvases.** PureRef, Milanote, Eagle and Are.na are mature and cheap.
- **"Taste" for UI.** Mobbin and Refero have 120k–620k real product screens, and
  their MCPs are already aimed at coding agents.

What no one I found does, and Visual Atlas already does:

1. **A reasoned reading per image.** Observable evidence, then a named technique
   from a fixed taxonomy, then possible effect. Documented intent is kept apart
   and taken only from source metadata. Competitors return pictures, or at most
   style do/don't rules (Refero).
2. **Review state on every reading.** Machine, then model-reviewed, then
   human-locked, with locks that later runs cannot overwrite. No competitor
   exposes how much to trust a result.
3. **Goal → operation → technique → example links.** This turns a brief into
   reasons. Competitors map a brief to similar pictures.
4. **Rights and reasons in one record.** `open-museum-mcp` has rights without
   reasons. Refero has reasons, of a kind, without rights.
5. **Local, free, on the user's own AI subscription.** Mobbin and Refero are
   paid SaaS with call quotas.

The defensible core is items 1–4 together. Each one alone is copyable.

**Honest limits (judgement):**

- The corpus is small: 93 starter references plus whatever the user fetches.
- It is mostly pre-20th-century art, which is a weak direct fit for agents
  building web UI, the main users of design MCPs today.
- Brief matching is deterministic word matching, so ranking quality is unproven.
- Reading quality depends on the vendor model, and I have no measurement of it.
- I found no direct evidence that designers want per-image written rationale.
  The case is strongest for agents, which have no tacit knowledge to fall back on.

## Three candidate theses

### Thesis A — "Reasons-first, licence-clean visual references for agents"

An MCP server + CLI over the existing library. Given a brief, it returns a
ranked set of references. Each carries technique, evidence, effect, intent
(or "none documented"), review state, rights record, credit line, a use
constraint (publishable with credit / reference only), and why it ranked for
this brief.

- **For:** It fills the one cell no competitor fills (`02-agent-tools.md`). It
  reuses nearly everything already built: store, rights, taxonomy, connections,
  readings. Agents are where the "AI slop" pain is loudest, and vendors are
  already selling references to agents for it. It is cheap to try, local, and
  stdio-only.
- **Against:** Agents mostly build UI, and museum art answers imagery and art-
  direction questions (hero image, illustration direction, editorial tone, brand
  mood), not layout. The market for that slice is unmeasured. Ranking by word
  matching may feel dumb next to vendor semantic search. The corpus is small.
- **Risk to watch:** Agents may ignore the reasons and just grab URLs. The proof
  has to show that the reasons change the agent's output.

### Thesis B — "A reasoned private library for designers"

Make Visual Atlas the designer's own reference library, Eagle-like, with the
owner's private design-system image libraries as local sources. Every image,
museum or private, gets technique readings, and boards carry the rationale.

- **For:** It directly targets the "mood boards with no rationale" gap. Private
  libraries are where designers' real references live. Local-first suits private
  material, and readings make a library searchable by *why*, not only by tag.
- **Against:** It is a UX-heavy fight with mature, cheap tools (Eagle ~$30
  one-time). Private images bring a new rights class (owned / client / unknown)
  that must never leak into "publishable". AI readings of client work raise
  confidentiality questions. The value to designers is the least evidenced claim
  in this research.
- **Risk:** It becomes a slower Eagle with annotations.

### Thesis C — "Craft-studied original imagery"

Use technique readings of public-domain masters to prompt an image model for
original images that apply a technique, such as "figure-ground ambiguity, low-key
light", not a style copy. Then check the result against the reading.

- **For:** It answers "I need a usable image" when museum works don't fit. Prompting
  by technique rather than artist name avoids the most contested ground.
  Pairing a generation with the reference that taught it is novel.
- **Against:** Generation is commodity plumbing. Output from prompts alone is
  likely uncopyrightable in the US (USCO Part 2, *Thaler*), so users don't own
  what they make. EU Art. 50 marking and C2PA preservation become obligations
  to get right. Each image costs time and quota on the user's subscription.
  Quality is hard to judge, and the result invites exactly the "AI slop" judgement
  the project exists to counter.
- **Risk:** It dilutes the clean "human-made, provenance-known" identity, which
  is the main advantage left now that feeds are full of AI images.

## Recommendation: Thesis A, built so B and C plug in later

Judgement, not evidence. A is the only thesis where the unique part (reasons +
rights + review state) is the product rather than a feature on top of a commodity.
It is also the smallest step from what exists. The agent contract pays off for the
UI too: a strict, documented reference record is what better UX needs. A private
library (B) becomes one more source with its own rights class. Generated images (C)
become another source, flagged `generated` and never mixed into the licence-clean
pool.

## Smallest set of capabilities that proves Thesis A

Read-only, local, stdio MCP, with CLI parity over the same functions. No new
storage and no network listener.

1. **`find_references(brief, use="publish"|"reference", limit≤10)`**. Returns
   ranked records, each with:
   `id, title, maker, date, image_path, source_url, rights {licence, rule_id,
   checked_at}, credit_line, use_constraint, technique {id, name}, evidence[],
   possible_effect, documented_intent | null, review_state, why_ranked {goal,
   operation, technique, matched_terms}`.
   CLI: `uv run atlas refs "brief" --json`.
2. **`explain_reference(id)`**. The full reading and correction history summary
   for one image.
3. **`get_technique(id)`**. Definition, guidance from `atlas/data`, how to apply
   it, and the best human-locked exemplars.
4. **`suggest_directions(brief)`**. The existing "My project" output, returned as
   structured data: up to 5 directions, each citing reference ids.
5. **Agent-safe output.** Remote metadata is returned as quoted data fields,
   never as instruction text. That is the existing untrusted-data invariant
   applied to a new boundary.

**Proof test (the part that decides it):** 12–20 real briefs the owner would
actually give an agent. Run them through Claude Code or Codex with and without the
MCP. The owner rates the outputs blind on fit, distinctiveness and whether the
agent could say why. Two pass/fail checks run alongside: every image the agent
proposes to publish carries its credit line, and none is marked "reference only".
If the with-MCP outputs are not clearly better, A is not proven. Rethink before
building B or C.

Two ways A could fail, both worth checking early: deterministic brief matching
picks poorly (fix: let the agent pass goals/techniques explicitly, which suits
agents anyway), or the corpus is too thin for a brief (fix: `find_references`
says "nothing eligible" and offers a fetch job rather than padding with weak matches).

## Later (in rough order)

1. **Private libraries as sources** (Thesis B core). Rights class `private`.
   Never `publishable` unless the owner sets it. Readings run locally only.
2. **Critique against references.** The agent submits its own output, and Visual
   Atlas compares it with the cited technique's evidence. This differs from rule-based
   critique MCPs, which score layout and contrast.
3. **Better ranking.** Embeddings for similarity *within* a technique only.
   Do not chase general visual search.
4. **More sources.** Europeana via `reusability=open` plus per-item rules, and the
   Smithsonian. Possibly reuse or contribute to `open-museum-mcp`'s rights rules
   instead of maintaining duplicates.
5. **Generated-image layer** (Thesis C). Technique-prompted, living-artist names
   refused, C2PA kept intact, labelled `generated` everywhere, a separate pool, and
   prompts and human edits saved.
6. **UX pass on the web app.** Make the reasons and review state the visual centre
   of the image view, and add boards with rationale.
7. **Optional hosted read-only catalogue of human-locked readings.** Only if users
   ask. Conflicts with local-first.

## Facts I could not verify (carried from the other files)

- How Mobbin and Refero rank results, and whether Refero's images tool returns
  rationale (its Tools page was not read).
- The maturity of `open-museum-mcp` (stars, tests, release cadence).
- Current prices for Cosmos, Savee, Flim and Kive.
- Any data on agents shipping unlicensed images.
- Whether designers want written per-image rationale.
- Whether a local app calling a vendor image model has EU Art. 50 duties itself.
