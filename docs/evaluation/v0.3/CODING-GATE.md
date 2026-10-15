# v0.3 request-coding gate (fixed 2026-10-15, before any coder change)

**Question.** Do descriptive cue phrases in the taxonomy (`request_cues`) help the deterministic request coder
read briefs that describe a technique without naming it, without making it tag wrongly?

**Sets.**
- *Development:* the 16 v1.1 briefs (`docs/evaluation/v1.1/briefs.json`), which also carry the relevance judgments
  used for retrieval recall. They are no longer a holdout, because v1.1 has reported on them. Cue phrases may be
  written and adjusted while looking at development results.
- *Final holdout:* the 20 briefs in `briefs-final.json` (sha256 prefix `543457fb8e219103`), written and coded by
  the builder before any coder change. They are run once, after the decision, and are never used to tune.

**Arms.**
1. The v1.1 coder (names, aliases and distinctive name words).
2. The v0.3 coder: arm 1 plus cue phrases and the stopword fixes.

**Metrics.** Micro-precision, recall and F1 over techniques and goals together. Retrieval recall@20 on the
development set, with the same relevance judgments and ranking code as v1.1. Wilson 95% intervals throughout.

**Adopt arm 2 if all of these hold on the development set:**
- micro-F1 is at least 0.10 above arm 1;
- precision is at least 0.60;
- retrieval recall@20 is not lower than arm 1's.

**Final.** After the decision, run both arms once on the final holdout and report them as they come out. A final
result below the development result is reported, not fixed.

**Limits.** The codes are the builder's provisional judgment. There are 16 and 20 briefs, so the intervals are
wide.
