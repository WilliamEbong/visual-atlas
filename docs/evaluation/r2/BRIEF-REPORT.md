# Brief reading, round 2 (23 November 2026)

The desk reads a brief by matching words against the codebook in `atlas/data/taxonomy.json`. The first overnight run
showed it missed 2 of 8 real briefs. This round measures that properly and improves it without tuning on the test set.

## Cases
80 briefs by two Opus subagents who read only the taxonomy and the v0.4 labelling policy, never the code:
`briefs-designers.json` (40, written as designers) and `briefs-agents.json` (40, written as AI agents passing a
user's request). Each case goes to dev or test by a hash of its id (`scripts/eval_r2.py`), fixed in commit `57595f2`
before any change. Labels are model judgments, not expert ground truth.

## What changed
- **Everyday phrases** (`cue-additions.json`, merged into each code's `request_cues`): 594 short phrases written by a
  third Opus subagent from the taxonomy alone. It never saw an evaluation brief.
- **One general fix:** the word "centre" alone no longer means off-centre placement ("dead centre" is symmetry).
- Nothing was added from a dev or test brief.

## Results (codes = techniques plus goals)
| Split | Before: precision / recall | After: precision / recall | Briefs with at least one right code |
|---|---|---|---|
| dev (35 briefs, looked at) | 0.71 / 0.19 | 0.84 / 0.39 | 8/28 → 17/28 |
| **test (45 briefs, aggregates only)** | **0.77 / 0.18** | **0.87 / 0.37** | **13/40 → 24/40** |
| v0.4 held-out (older set) | 0.92 / 0.60 | 0.86 / 0.60 | one new false positive |

Techniques on test: recall 0.20 → 0.47. Goals on test: recall 0.14 → 0.21; goals stay the weak part.

## What this means
Recall roughly doubled and precision rose on briefs the changes were not tuned on, but word matching still misses
about half of what people mean when they paraphrase ("a speck at the foot of a glacier", "the cafe behind melting
away"). That ceiling is why agents now get a second path: `advise` and `suggest_directions` accept technique and
goal ids, and when the words match nothing the answer includes the codebook so the calling agent, which reads the
brief far better, can pass the ids itself. Reproduce: `uv run python scripts/eval_r2.py test --rev 57595f2` (before)
and `uv run python scripts/eval_r2.py test` (after).
