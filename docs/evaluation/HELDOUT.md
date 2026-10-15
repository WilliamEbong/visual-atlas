# Held-out challenge: technique readings

Twelve images that were never in the library, chosen to include clear, subtle and ambiguous cases.
Expected techniques were written by the builder (Claude, while building Visual Atlas) after looking at
each image and before any model ran. **They are builder judgment, not expert ground truth**; treat the
numbers as a sanity check of behaviour, not as accuracy.

| # | Image | Builder expects | Codex proposed | Claude (independent) | Claude agrees with Codex on |
|---|---|---|---|---|---|
| 1 | Bird's Nest and Ferns (aic) | Colour contrast, Texture contrast — small blue eggs against dark greens and browns; busy surround, so not negative space | Colour contrast, Texture contrast, Light–dark contrast (chiaroscuro) | Colour contrast, Tight cropping, Light–dark contrast (chiaroscuro) | Colour contrast, Light–dark contrast (chiaroscuro) |
| 2 | Nocturne: Blue and Gold—Southampton Wate (aic) | Colour contrast, Limited palette harmony, Negative space isolation — near-monochrome nocturne with one small orange light; very low contrast is the point | Atmospheric perspective, Colour contrast, Limited palette harmony | Colour contrast, Limited palette harmony, Negative space isolation | Colour contrast, Limited palette harmony |
| 3 | A Maid Asleep (met) | Frame within a frame, Layered depth (foreground, middle, background) — doorway opens onto a second room; eyes closed, so no gaze reading | Off-centre placement, Layered depth (foreground, middle, background), Light–dark contrast (chiaroscuro) | Limited palette harmony, Layered depth (foreground, middle, background), Texture contrast | Off-centre placement, Layered depth (foreground, middle, background) |
| 4 | A Scientist Seated at a Desk by Candleli (cma) | Gaze direction, Light–dark contrast (chiaroscuro) — single candle source; sitter looks out at the viewer | Off-centre placement, Limited palette harmony, Light–dark contrast (chiaroscuro) | Limited palette harmony, Gaze direction, Light–dark contrast (chiaroscuro) | Off-centre placement, Limited palette harmony, Light–dark contrast (chiaroscuro) |
| 5 | Composition with Red, Yellow, and Blue (cma) | Off-centre placement, Colour contrast — abstract; red mass upper left balanced by small yellow and blue; the large white field could also be read as negative space | Off-centre placement, Colour contrast, Light–dark contrast (chiaroscuro) | Off-centre placement, Colour contrast, Negative space isolation | Off-centre placement, Colour contrast, Light–dark contrast (chiaroscuro) |
| 6 | A Sunday on La Grande Jatte — 1884 (aic) | Layered depth (foreground, middle, background), Rhythm and pattern — repeated upright figures, trunks and parasols; ambiguous and crowded | Off-centre placement, Layered depth (foreground, middle, background), Rhythm and pattern | Colour contrast, Layered depth (foreground, middle, background), Scale contrast, Light–dark contrast (chiaroscuro) | Off-centre placement, Layered depth (foreground, middle, background), Rhythm and pattern |
| 7 | Under the Wave off Kanagawa (Kanagawa ok (met) | Frame within a frame, Implied motion, Scale contrast — the wave dwarfs a tiny Mount Fuji and the boats; the wave's curl frames Fuji | Implied motion, Rhythm and pattern, Scale contrast | Limited palette harmony, Frame within a frame, Implied motion, Scale contrast | Implied motion, Rhythm and pattern, Scale contrast |
| 8 | Lone Tree in Yosemite Winter Fog (578393 (commons) | Atmospheric perspective, Limited palette harmony — fog and a near-monochrome blue; negative space is debatable because the tree fills the frame | Atmospheric perspective, Limited palette harmony | Atmospheric perspective, Limited palette harmony, Negative space isolation | Atmospheric perspective, Limited palette harmony |
| 9 | Corridor of Vizianagaram Hall, Universit (commons) | Frame within a frame, Leading lines, Rhythm and pattern — converging arcade, repeated arches and doors, arches frame the far door | Frame within a frame, Leading lines, Rhythm and pattern | Limited palette harmony, Leading lines, Rhythm and pattern | Leading lines, Rhythm and pattern |
| 10 | Map/Print Case (cma) | — — catalogue photo of a furniture object on a plain ground; any isolation is incidental to museum photography, so no technique is expected | Diagonal energy, Texture contrast | Limited palette harmony, Texture contrast, Visual metaphor | Diagonal energy, Texture contrast |
| 11 | [Female Portrait, Standing, Looking Left (met) | Gaze direction — sitter looks out of frame to the left; the oval mount and monochrome come from the medium, not a choice | Frame within a frame, Light–dark contrast (chiaroscuro) | Limited palette harmony, Gaze direction, Light–dark contrast (chiaroscuro) | Light–dark contrast (chiaroscuro) |
| 12 | A Market Place and Crowd title QS:P1476, (commons) | Proximity grouping — a crowd clustered under awnings against empty walls; ambiguous sketch | Atmospheric perspective, Limited palette harmony, Layered depth (foreground, middle, background) | Limited palette harmony, Proximity grouping, Selective focus | Layered depth (foreground, middle, background) |

## Summary

- Codex proposals that match a builder expectation: 17 of 33.
- Builder expectations found by at least one model: 22 of 23.
- Codex vs Claude independent readings, mean overlap (Jaccard): 0.39.
- Claude agreed with 26 of 33 Codex proposals when asked to check them.

Raw results: `heldout-results.json`. Expectations: `heldout-expectations.json`.
