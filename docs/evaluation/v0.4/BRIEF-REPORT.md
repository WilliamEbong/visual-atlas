# Brief interpretation — v0.4.0

The deterministic reader now catches the reported solitude brief, suppresses mechanisms in ordinary negative clauses, consumes all matched cue words, removes more format/instruction words from searches, and offers direct corrections in Find and My project. It makes no additional model calls. Explicit choices override inference. User corrections are validated and recorded with the submitted job and directions analysis; they apply to that request. The full original project brief still reaches the adviser.

Subject-based references receive every fourth candidate slot when available, so a mistaken technique cannot crowd all of them out. Find's offline planning fallback puts subject searches before technique hints, keeping them within its bounded query list. Neither inference nor correction deletes references. AI advice remains explicit, using the configured existing assistant; this work does not enable Jev.

## Protocol and provenance

See [BRIEF-GATE.md](BRIEF-GATE.md). Sixteen development judgments were saved before baseline outputs or tuning. A separate Codex agent authored sixteen held-out cases without reading the implementation, development cases or outputs. The implementer received only its SHA256 and case count until declaring tuning frozen. These are provisional builder/model judgments, **not independent expert ground truth**. Both arms use the same unchanged 85-reference baseline starter corpus and baseline taxonomy memberships. The baseline coder and ranker are loaded from commit `e43e0932ece8be850926e013fc91ce3f84920c32`; the current arm uses the working source.

Frozen hashes:

- Development: `52b57a35f05797e3890ab7c7e824d92f5deff0bd05b60cf388e8ed560469e951`.
- Held-out: `f38360b4e1b7d5e3fca1b15af24710f4e929fe75b422eefb705c804a4c9e0a3e`.

The script rejects changed judgments. Expected subject words and forbidden words are compared after the baseline's plural/spelling normalization in both arms. This evaluator fix was applied after the first held-out run (which incorrectly counted plural expected words as misses); labels and implementation were unchanged.

## Results

Combined technique and goal micro counts:

| Split / version | TP | FP | FN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|
| Development / v0.3 | 17 | 7 | 4 | 70.83% | 80.95% | .7556 |
| Development / v0.4 | 21 | 0 | 0 | 100% | 100% | 1.0000 |
| Held-out / v0.3 | 14 | 5 | 6 | 73.68% | 70% | .7179 |
| Held-out / v0.4 | 12 | 1 | 8 | 92.31% | 60% | .7273 |

Development clears the predeclared adoption gate (F1 +.2444; precision improves; candidate coverage does not decrease). Held-out precision improves but recall **falls ten percentage points**. The small F1 gain is not evidence of broad natural-language understanding. No held-out misses were tuned away.

| Split | Required subject words, old → new | Forbidden subject leakage, old → new | Expected techniques represented in top 20, old → new | Top 40, old → new |
|---|---|---|---|---|
| Development | 18/18 → 18/18 | 12/18 → 0/18 | 14/15 → 15/15 | 15/15 → 15/15 |
| Held-out | 23/24 → 23/24 | 37/79 → 26/79 | 12/13 → 12/13 | 12/13 → 12/13 |

Technique-only held-out: TP/FP/FN `7/3/6 → 6/0/7`. Goal-only held-out: `7/2/0 → 6/1/1`. Full readings and supplied candidate IDs are in `brief-results-dev.json` and `brief-results-heldout.json`.

Candidate coverage checks whether any current annotation for an expected technique appears among supplied references. It does not establish image quality, subject relevance or classification correctness; proposed annotations count too. A separate regression creates sixty references where a mistaken technique outranks an older subject match, and verifies that the subject match reaches the first four candidates.

## Observed sentence and remaining limits

“A calm poster about solitude, with one small person in a large empty landscape. Leave space for a title.”

- Baseline: scale contrast, calm; subject terms include `empty`, `leave`, `space`.
- Current: negative space isolation, scale contrast, calm; subject term `solitude`.

Unseen descriptions such as unoccupied water around a sailboat, crisp butterfly against dissolved blur, a piano in a supermarket, and a candle standing in for burnout remain weak. Clause-level negation also misses a positive replacement inside a negative coordinated clause (“avoid X and use Y”). The current generic stopword policy still drops `portrait` when it is the subject, and some unrecognised mechanism/instruction words leak into search terms. Use **Correct this reading** to remove/add goals or techniques and replace subject words. No measured probabilities are shown.

## Verification and review

- `uv run --no-sync pytest tests/test_coding.py tests/test_jobs.py tests/test_discovery.py tests/test_tasks.py -q`: **74 passed** after fixes.
- Ruff for all changed brief Python files: clean. Frontend TypeScript validation: passed. Real browser evidence is recorded by the integrating agent in BUILD-STATE.md; unit/type checks alone are not claimed as UI verification.
- Independent source review found and fixed a job-kind variable shadow, correction-only subject requests being rejected, and corrected data being truncated from long Find planner prompts. A broad `does not` negation exemption was narrowed to the existing “does not belong” cue. These postfreeze fixes address implementation defects, not held-out miss tuning. Rerun held-out counts were unchanged.
- All evaluation and targeted tests are offline. Fake-adapter tests verify correction/original-text plumbing and job persistence; they are not live-model evidence. No interpretation AI fallback was added.
- Root also ran the existing v0.3 evaluations into `legacy/`: those scripts label the current-code arm `v0.3`, but it is the v0.4 working implementation. Reported current-code development precision/recall is 24/25 and 24/28 with retrieval 62/80; legacy final is 20/24 and 20/41. These older examples are context, not a new held-out set.

Reproduce with `uv run python scripts/eval_v04.py dev` and `uv run python scripts/eval_v04.py heldout`. Scratch libraries are created under the system temporary directory and removed afterward; the real user library is never opened.
