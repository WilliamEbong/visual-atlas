# Brief interpretation protocol

Frozen before baseline outputs and tuning, 2026-10-15. These are builder/model judgments, not independent expert ground truth. A second agent authors and holds the held-out split unseen by the implementer until tuning is frozen. Neither set is supplied to an AI prompt.

Baseline: repository HEAD e43e0932ece8be850926e013fc91ce3f84920c32, including its coding module, taxonomy and reference ranking. Compare the same frozen cases against v0.4, reporting combined goal/technique micro precision and recall with TP/FP/FN, plus separate counts. Subject assertions report required and forbidden words. Ambiguous requests should not manufacture a technique. A negative clause suppresses that inferred code even if another clause requests it; explicit form choices win.

Adopt deterministic improvements if development F1 increases by at least .10, precision does not decrease, and relevant-reference candidate coverage does not decrease. Inspect held-out results once, report them without tuning. Small samples are directional evidence only.

Retrieval check: on the unchanged baseline starter corpus, count whether at least one reference carrying each expected technique reaches the first 20 and 40 candidate records. This tests mechanism coverage using existing annotation labels (including proposals); it is not a judgment of subject relevance or independent image ground truth. Report raw covered/expected technique counts. Also test an adversarial early-misinterpretation case where subject-matching references must survive dominant technique scores.
