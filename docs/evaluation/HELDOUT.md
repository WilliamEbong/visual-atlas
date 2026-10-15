# Held-out challenge: technique readings

> **How to read this (added in v1.1).** This is a *development / regression* set, not a fresh held-out test:
> round 1 was run, the prompts were then revised after reading its results, and round 2 (below) re-ran the same
> twelve images. The expected techniques are the builder's own judgment (Claude, while building), not expert or
> human ground truth. All numbers are label-level agreement (how many proposed labels match an expected label),
> not image-level accuracy. The v1.1 evaluation with separate development and final splits is in
> [v1.1/REPORT.md](v1.1/REPORT.md).

Twelve images that were never in the library, chosen to include clear, subtle and ambiguous cases.
Expected techniques were written by the builder (Claude, while building Visual Atlas) after looking at
each image and before any model ran. **They are builder judgment, not expert ground truth**; treat the
numbers as a sanity check of behaviour, not as accuracy.

| # | Image | Builder expects | Codex proposed | Claude (independent) | Claude agrees with Codex on |
|---|---|---|---|---|---|
| 1 | Bird's Nest and Ferns (aic) | Colour contrast, Texture contrast — small blue eggs against dark greens and browns; busy surround, so not negative space | Colour contrast, Texture contrast | Colour contrast, Limited palette harmony, Light–dark contrast (chiaroscuro) | Colour contrast |
| 2 | Nocturne: Blue and Gold—Southampton Wate (aic) | Colour contrast, Limited palette harmony, Negative space isolation — near-monochrome nocturne with one small orange light; very low contrast is the point | Atmospheric perspective, Colour contrast, Limited palette harmony | Colour contrast, Limited palette harmony, Negative space isolation | Colour contrast, Limited palette harmony |
| 3 | A Maid Asleep (met) | Frame within a frame, Layered depth (foreground, middle, background) — doorway opens onto a second room; eyes closed, so no gaze reading | Off-centre placement, Layered depth (foreground, middle, background), Light–dark contrast (chiaroscuro) | Limited palette harmony, Layered depth (foreground, middle, background), Texture contrast | Off-centre placement, Layered depth (foreground, middle, background), Light–dark contrast (chiaroscuro) |
| 4 | A Scientist Seated at a Desk by Candleli (cma) | Gaze direction, Light–dark contrast (chiaroscuro) — single candle source; sitter looks out at the viewer | Off-centre placement, Light–dark contrast (chiaroscuro) | Limited palette harmony, Gaze direction, Light–dark contrast (chiaroscuro) | Off-centre placement, Light–dark contrast (chiaroscuro) |
| 5 | Composition with Red, Yellow, and Blue (cma) | Off-centre placement, Colour contrast — abstract; red mass upper left balanced by small yellow and blue; the large white field could also be read as negative space | Off-centre placement, Colour contrast, Light–dark contrast (chiaroscuro) | Off-centre placement, Colour contrast, Negative space isolation | Off-centre placement, Colour contrast |
| 6 | A Sunday on La Grande Jatte — 1884 (aic) | Layered depth (foreground, middle, background), Rhythm and pattern — repeated upright figures, trunks and parasols; ambiguous and crowded | Layered depth (foreground, middle, background), Rhythm and pattern, Light–dark contrast (chiaroscuro) | Layered depth (foreground, middle, background), Scale contrast, Light–dark contrast (chiaroscuro) | Layered depth (foreground, middle, background), Rhythm and pattern |
| 7 | Under the Wave off Kanagawa (Kanagawa ok (met) | Frame within a frame, Implied motion, Scale contrast — the wave dwarfs a tiny Mount Fuji and the boats; the wave's curl frames Fuji | Implied motion, Rhythm and pattern, Scale contrast | Frame within a frame, Implied motion, Scale contrast | Implied motion, Rhythm and pattern, Scale contrast |
| 8 | Lone Tree in Yosemite Winter Fog (578393 (commons) | Atmospheric perspective, Limited palette harmony — fog and a near-monochrome blue; negative space is debatable because the tree fills the frame | Atmospheric perspective | Atmospheric perspective, Limited palette harmony, Symmetry and central balance | Atmospheric perspective |
| 9 | Corridor of Vizianagaram Hall, Universit (commons) | Frame within a frame, Leading lines, Rhythm and pattern — converging arcade, repeated arches and doors, arches frame the far door | Frame within a frame, Leading lines, Rhythm and pattern | Colour contrast, Leading lines, Rhythm and pattern, Symmetry and central balance | Leading lines, Rhythm and pattern |
| 10 | Map/Print Case (cma) | — — catalogue photo of a furniture object on a plain ground; any isolation is incidental to museum photography, so no technique is expected | — | Limited palette harmony, Texture contrast | — |
| 11 | [Female Portrait, Standing, Looking Left (met) | Gaze direction — sitter looks out of frame to the left; the oval mount and monochrome come from the medium, not a choice | Frame within a frame, Light–dark contrast (chiaroscuro) | Frame within a frame, Gaze direction | Light–dark contrast (chiaroscuro) |
| 12 | A Market Place and Crowd (commons) | Proximity grouping — a crowd clustered under awnings against empty walls; ambiguous sketch | Layered depth (foreground, middle, background), Selective focus | Diagonal energy, Proximity grouping, Selective focus | Layered depth (foreground, middle, background) |

## Summary

- Codex proposals that match a builder expectation: 16 of 27.
- Builder expectations found by at least one model: 22 of 23.
- Codex vs Claude independent readings, mean overlap (Jaccard): 0.33.
- Claude agreed with 20 of 27 Codex proposals when asked to check them.

Raw results: `heldout-results.json`. Expectations: `heldout-expectations.json`.

## Two rounds, and what changed between them

Round 1 ([round1/](round1/HELDOUT.md)) used the first analysis prompt. It showed two habits:

- Codex attached *light–dark contrast* and *off-centre placement* to most pictures, and proposed two
  techniques for a plain museum catalogue photo of a piece of furniture.
- Claude often attached *limited palette harmony* to pictures whose single colour comes from the medium
  (a monochrome photograph, an ink sketch).

The prompt now tells both models that qualities imposed by the medium or by catalogue photography are not
techniques, that light–dark contrast needs one area that clearly pulls the eye, and that an empty list is
the right answer for a documentation photo. Round 2 (this page) used that prompt.

| | Round 1 | Round 2 |
|---|---:|---:|
| Codex proposals | 33 | 27 |
| … matching a builder expectation | 17 (52%) | 16 (59%) |
| Builder expectations found by either model | 22 of 23 | 22 of 23 |
| Claude agreed with Codex when checking | 26 of 33 | 20 of 27 |
| Codex on the catalogue photo | 2 techniques | none (correct) |

Claude, analysing independently, still over-uses *limited palette harmony* on monochrome material; in the
app Claude is used as the checker, and readings remain "agreed by a second model", never "confirmed by
you", until a person decides. Twelve images are far too few for accuracy claims: read this as a check
that the prompt changes moved behaviour in the intended direction.
