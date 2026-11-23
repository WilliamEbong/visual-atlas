# Proxy blind test (23 November 2026)

**This is a proxy, not the owner's verdict.** The real test (`docs/evaluation/v0.5/BLIND-TEST.md`) needs William's own
briefs and ratings; it is still ready to run. Here Opus subagents stood in for both the agents and the raters.

## Method
- 10 briefs (`briefs.json`), written before either arm ran, not taken from the brief-reading sets.
- Same task for both arms: choose two reference images, say why each fits, give credits, say whether each may be
  published.
- **Arm A** (`A.json`): an Opus agent with web search and fetch, no Visual Atlas.
- **Arm B** (`B.json`): an Opus agent with the Visual Atlas CLI (`advise`, `directions`, `refs`, `ref`) on the starter
  library (93 references at the time) plus generated examples, and web search allowed.
- Answers were relabelled X/Y at random per brief (`blind.json`; key in `key.json`). Two Opus judges, who saw only the
  briefs and `blind.json`, scored fit, usefulness of reasoning and licence accuracy from 1 to 5, checked source pages
  on the web, and picked a winner per brief (`judge-1.json`, `judge-2.json`).

## Result, round 1
| | Judge 1 | Judge 2 |
|---|---|---|
| A wins / B wins / ties | 8 / 1 / 1 | 8 / 1 / 1 |

| Mean score (20 ratings per arm) | Fit | Reasoning | Licence |
|---|---|---|---|
| A, without the desk | 4.65 | 4.20 | 5.00 |
| B, with the desk | 3.65 | 4.00 | 4.95 |

**The desk lost.** Both judges agreed. Licence accuracy did not separate the arms: the web-searching agent read
Commons and museum records correctly and flagged share-alike and personality rights. The difference was fit: arm B
leaned on the small local corpus (it took 12 of its 20 picks from it) and often chose a picture that showed the
technique rather than one that showed the brief's subject (a choir poster answered with an organ rehearsal; a
bakery post answered with an "odd one out" photograph that is not bread).

## What changed because of it
- `search_open_collections` (MCP) and `atlas search-open`: live search of Commons, the Met, AIC, Cleveland and the
  Rijksmuseum with every candidate licence-checked by `atlas/rights.py`. The desk's edge becomes the reasoning
  (techniques, what to make sure of) plus checked licences, over the whole of the open collections rather than 104
  pictures.
- The arm B prompt for round 2 says fit comes first.

## Result, round 2
Arm B2 (`B2.json`) had the new open search and was told fit comes first; it took all 20 picks from it (Commons and
the Met). Same arm A, new random labels (`blind2.json`, `key2.json`), two new blind judges (`judge-3.json`,
`judge-4.json`).

| | Judge 3 | Judge 4 |
|---|---|---|
| A wins / B2 wins / ties | 6 / 1 / 3 | 7 / 2 / 1 |

| Mean score (20 ratings per arm) | Fit | Reasoning | Licence |
|---|---|---|---|
| A, without the desk | 4.50 | 4.00 | 5.00 |
| B2, with the desk and open search | 3.95 | 3.90 | 4.20 |

**Still a loss, but the fit gap halved** (1.00 to 0.55). Both judges found every licence claim correct and no wrong
"may publish" on either side. B2 lost licence points on **credit quality**: the credit lines it copied from the desk
carried Commons metadata noise ("Dutch: Zingende engelen Singing Angels", hidden Wikidata labels, footnote markers,
a description run on after the title). That was a real defect in `atlas/providers.py`, now fixed with tests
(commit `2c2a750`).

## What this proxy says, and does not say
- An Opus agent with plain web search already finds well-fitting public-domain pictures and reads their licences
  correctly. On this evidence, "licence-checked references" alone is not a reason for such an agent to use the desk.
- The desk's own corpus is too small to compete on fit; searching the open collections narrows the gap.
- The desk's reasoning (techniques, what to make sure of) did not lift the judges' reasoning scores in either round.
- It does not measure what the thesis is about for William: whether his own briefs, with his taste, get better
  references, and whether weaker or cheaper agents (which misread licences more often) gain more than Opus does.
  Those need the real blind test.
