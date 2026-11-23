# Mood goals (23 November 2026)

A brief like "Poster for a community choir concert in a church, warm and communal" names a feeling, not a mechanism.
The codebook had no goal for it, so the desk answered that it could not tell what the picture should do. Five mood
goals now sit in `atlas/data/taxonomy.json`, each mapped to the techniques that produce the feeling.

## Goals and techniques
| Goal | Techniques that serve it |
|---|---|
| `feel-warm` Feel warm and welcoming | color-harmony, proximity-grouping, gaze-direction, framing |
| `feel-serious` Feel serious and credible | symmetry, value-contrast, negative-space, vantage-point |
| `feel-playful` Feel playful | juxtaposition, contextual-incongruity, color-contrast, scale-contrast, repetition-with-interruption |
| `feel-luxurious` Feel luxurious | negative-space, value-contrast, color-harmony, texture-contrast, selective-focus |
| `feel-wistful` Feel lonely or wistful | negative-space, atmospheric-perspective, silhouette, gaze-direction |

Each has 23–25 request cues (mood words people write: cosy, convivial, gravitas, cheeky, high end, bittersweet…).

Not duplicated:
- **Calm** is the existing `create-calm`; it gained five cues (unwind, slow down, slowing down, decompress, breathe easy).
- **Energetic** is the existing `suggest-motion` ("Suggest movement or energy", which already had energetic, lively,
  dynamic). It gained high energy, high octane, adrenaline, punchy, buzzing, exhilarating, upbeat, exciting.

Cues dropped because they collided with other words: "electric" (an electric car on a dev brief), "vibrant"
(vibrant colours), "solitude" and "solitary" (a calm brief about solitude is not lonely; caught by an existing test),
plus "intimate" and "moody", which the brief labels say are not goals.

## Mood briefs (`mood-briefs.json`, 13 briefs written before the cues)
| | Any goal read | Intended goal read |
|---|---|---|
| Before | 3/13 | 2/13 (both calm) |
| After | 13/13 | 13/13 |

One extra read: m13 ("quiet and bittersweet") also reads `create-calm` from "quiet". These briefs were written by
the same agent that chose the cues, so 13/13 is an optimistic figure, not a held-out score.

## Held-out briefs (`scripts/eval_r2.py`, labels written against the old 11-goal codebook)
| Split | Combined P / R before | after | Goals P / R before | after | Briefs with a right code |
|---|---|---|---|---|---|
| dev (35) | 0.84 / 0.389 | 0.778 / 0.389 | 0.714 / 0.263 | 0.556 / 0.263 | 17/28 → 17/28 |
| **test (45)** | **0.871 / 0.37** | **0.73 / 0.37** | **1.0 / 0.214** | **0.5 / 0.214** | 24/40 → 24/40 |
| v0.4 held-out (16) | 0.857 / 0.60 | 0.857 / 0.60 | 0.75 / 0.857 | 0.75 / 0.857 | |

Recall and technique scores do not change. Every new false positive is a mood goal (test: warm 2, wistful 2,
serious 1, luxurious 1; dev: serious 1, wistful 1). Those labels could not contain mood goals because the codebook had
none; the two visible on dev are "steady and trustworthy" → serious and "a podcast cover about grief" → wistful,
which are right readings under the new codebook. Scored on the old 11 goals only, both splits are identical to before
(test goals 1.0 / 0.214, dev 0.714 / 0.263). Test cases were not read.

## Limits
- Mood cues are single words matched literally: "warm light" reads warmth, "not warm" is vetoed only by the clause
  negation rule, and figurative moods ("feels like Sunday afternoon at gran's") are missed.
- Technique mappings are judgment, not measured: a reference "serves" a mood when it shows a mapped technique, so a
  colour-harmony picture in cold blues can still be offered as warm. Colour temperature is not in the analysis.
- The held-out labels should be re-judged against the 16-goal codebook before goal precision is compared again.

Reproduce: `uv run python scripts/eval_r2.py test`, `uv run python scripts/eval_v04.py heldout` (then restore its
results file), `uv run pytest tests/test_mood_goals.py`.
