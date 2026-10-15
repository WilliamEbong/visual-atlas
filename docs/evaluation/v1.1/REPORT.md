# Visual Atlas v1.1 evaluation

**Read this first.** The reference readings are the builder's provisional judgments, made by looking at each image before any model ran on it (`cases.json`, committed before the runs). They are not expert or human ground truth. Samples are small; every proportion has a 95% Wilson interval, and overlapping intervals mean "no clear difference". Numbers count labels (techniques), except where they say images.

## Setup

- 25 images new to Visual Atlas: 11 development and 14 final cases. Categories: clear, subtle, ambiguous, monochrome, catalogue photo or text (expect no technique), and commonly confused pairs.
- Each case records its source and item id, the original and evaluation-copy SHA-256, the reference techniques, acceptable alternatives, uncertainty and what the pixels show.
- Proposer: Codex `gpt-6-astra`, which analyses the pixels as the app does; labels are kept at confidence ≥ 0.4.
- Checker: Claude Code `sonnet`, in two arms (one call each per image):
  - **shown**: the v1 production checker, which sees the proposals at once (prompt `b3652cd3f3216483`);
  - **independent**: lists its own reading first, then judges (prompt `2145210ed8d38812`).
- Frozen on 2026-10-15 10:56 (`freeze.json`): final cases, prompts, models and metric code. The final split was run once, after the checker decision.

## Technique readings

| Measure | Development | Final |
|---|---|---|
| Proposer precision (reference or acceptable alternative) | 19/23 = 0.83 [0.63–0.93] | 23/28 = 0.82 [0.64–0.92] |
| Proposer recall of reference techniques | 10/13 = 0.77 [0.50–0.92] | 14/15 = 0.93 [0.70–0.99] |
| Images with a reference technique where it proposed nothing | 0/9 = 0.00 [0.00–0.30] | 0/12 = 0.00 [0.00–0.24] |
| No-technique images where it proposed something wrong | 1/2 = 0.50 [0.09–0.91] | 0/2 = 0.00 [0.00–0.66] |
| Proposer invalid or failed answers | 0 | 0 |
| Proposer mean seconds per call | 18.1 | 16.6 |
| Checker (shown): false acceptance of wrong labels | 3/4 = 0.75 [0.30–0.95] | 4/5 = 0.80 [0.38–0.96] |
| Checker (shown): false rejection of right labels | 3/19 = 0.16 [0.06–0.38] | 2/22 = 0.09 [0.03–0.28] |
| Checker (shown): precision of accepted labels | 16/19 = 0.84 [0.62–0.94] | 20/24 = 0.83 [0.64–0.93] |
| Checker (shown): invalid or failed answers | 0 | 1 |
| Checker (shown): calls per useful label (accepted and right) | 1.31 | 1.3 |
| Checker (shown): mean seconds per call | 4.5 | 4.4 |
| Checker (independent): false acceptance of wrong labels | 2/4 = 0.50 [0.15–0.85] | 2/5 = 0.40 [0.12–0.77] |
| Checker (independent): false rejection of right labels | 2/19 = 0.11 [0.03–0.31] | 2/23 = 0.09 [0.02–0.27] |
| Checker (independent): precision of accepted labels | 17/19 = 0.89 [0.69–0.97] | 21/23 = 0.91 [0.73–0.98] |
| Checker (independent): invalid or failed answers | 0 | 0 |
| Checker (independent): calls per useful label (accepted and right) | 1.24 | 1.24 |
| Checker (independent): mean seconds per call | 4.2 | 4.6 |
| Independent checker's own reading: precision | 26/35 = 0.74 [0.58–0.86] | 31/44 = 0.70 [0.56–0.82] |
| Independent checker's own reading: recall of reference | 11/13 = 0.85 [0.58–0.96] | 14/15 = 0.93 [0.70–0.99] |

### Checker decision

Rule, fixed before the development run: On the development split only: adopt the independent-first checker if its false acceptance is at least 0.10 lower than the current checker's, its false rejection is at most 0.10 higher, and it has no more invalid answers plus one. The calls per image are equal (one each). The final split is run once afterwards and only reported; it never changes the decision.

On the development split the rule held: the app now uses the independent-first checker (false acceptance 0.75 → 0.5, false rejection 0.16 → 0.11). Only 4 wrong proposals were available to judge, so this is weak evidence of a real difference, chosen because it costs nothing extra.

Final split (reported, not used to decide): false acceptance 4/5 = 0.80 [0.38–0.96] (shown) vs 2/5 = 0.40 [0.12–0.77] (independent); false rejection 2/22 = 0.09 [0.03–0.28] vs 2/23 = 0.09 [0.02–0.27].

## Project help: which references reach the model (no AI)

16 frozen briefs (`briefs.json`), with relevance judged from contact sheets of the 85 starter images before the run. v1 sent the newest images; v1.1 ranks by the request coding. The prompt budget currently holds 40 records.

| References considered | v1 newest first | v1.1 relevance ranking |
|---|---|---|
| top 10 | 9/80 = 0.11 [0.06–0.20] | 40/80 = 0.50 [0.39–0.61] |
| top 20 | 24/80 = 0.30 [0.21–0.41] | 54/80 = 0.68 [0.57–0.77] |
| top 40 | 43/80 = 0.54 [0.43–0.64] | 72/80 = 0.90 [0.81–0.95] |

Deterministic request coder against the builder's codes: techniques precision 3/4 = 0.75 [0.30–0.95], recall 3/18 = 0.17 [0.06–0.39]; goals precision 3/7 = 0.43 [0.16–0.75], recall 3/10 = 0.30 [0.11–0.60]. The coder is conservative: it rarely tags wrongly but misses most techniques that are described rather than named. The relevance ranking still gains mainly through subject words. The coder was written before these briefs and has not been tuned on them.

## TypeSafe Jev decision gate

Criteria in [JEV-GATE.md](JEV-GATE.md), fixed before any call. All arms are text only.

### 1. Request coding (tagging a brief with codebook codes)

| Coder | Precision | Recall | micro-F1 | Retrieval recall@20 |
|---|---|---|---|---|
| v1: none | — | — | — | (recency) 24/80 = 0.30 [0.21–0.41] |
| v1.1 deterministic | 6/11 = 0.55 [0.28–0.79] | 6/28 = 0.21 [0.10–0.40] | 0.31 | 54/80 = 0.68 [0.57–0.77] |
| Jev (noul ≥ 0.5) | 23/74 = 0.31 [0.22–0.42] | 23/28 = 0.82 [0.64–0.92] | 0.45 | 57/80 = 0.71 [0.61–0.80] |

Jev: 20 calls, 0 failures, median 0.1 s, 2/4 repeated briefs gave identical tags, about $0.0032; model ['jev-1.13.0'].

**Decision: not integrated.** Not every criterion held (see the table and JEV-GATE.md).

### 2. Relevance ranking of library references

| Ranking | recall@10 | recall@20 |
|---|---|---|
| v1: newest first | 9/80 = 0.11 [0.06–0.20] | 24/80 = 0.30 [0.21–0.41] |
| v1.1 deterministic | 40/80 = 0.50 [0.39–0.61] | 54/80 = 0.68 [0.57–0.77] |
| Jev (noul per reference) | 69/80 = 0.86 [0.77–0.92] | 76/80 = 0.95 [0.88–0.98] |

Jev: 16 calls, median 0.1 s, about $0.0004 per brief. This use sends library titles and summaries to TypeSafe. Caveat: the relevance judgments were made from contact sheets that showed titles, so a ranker that reads titles may be favoured; the gap over the deterministic ranking is still well outside the intervals.

**Decision: integrate (optional, off by default).** Every criterion held.

### 3. Metadata classification (skip documentation photos before download)

At the pre-set threshold 0.8: 2 of 4 negative cases would be skipped (saving those analyses) and 0 of 21 cases with a reference technique would be lost. Highest score on a positive case: 0.23; lowest on a negative: 0.65.

**Decision: promising, deferred.** The criteria held, but with 4 negative cases the pre-registered small-sample rule allows no more than "promising, deferred".

### 4. Annotation review (text only)

Reading only the definition and the cited evidence sentences: false acceptance 8/9 = 0.89 [0.56–0.98], false rejection 2/42 = 0.05 [0.01–0.16] (development and final proposals together).

**Decision: not integrated**, neither as a checker (it never sees the pixels, so it cannot replace the image check, as fixed in advance) nor as a pre-filter (that needed false acceptance at least 0.15 below the pixel checker's; reading text alone it accepted almost every wrong label).

## Limits

- The reference readings come from one builder and are provisional; a second human reader would change some of them. Treat differences smaller than the intervals as noise.
- 25 images and 16 briefs are enough to catch large failures, not to rank close alternatives.
- Model behaviour drifts between versions; `model_version` is recorded in the raw results.
- The v1 held-out numbers (`../HELDOUT.md`) used different images and builder labels, so they are not directly comparable with these.

Raw results: `results-dev.json`, `results-final.json`, `retrieval-results.json` and `jev-*.json`. Reproduce: `uv run python scripts/eval_v11.py report`.
