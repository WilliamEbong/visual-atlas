# What keeps each screen under 9

Source: the six fresh scorer reports of the last three builds:
- d: the content pass;
- e: moods gated by picture;
- f: the final build, product designer and editorial designer.

"Said by" counts the reports that named the reason (out of 6). The final scores are the means of f.

| Screen (final) | Reason under 9 | Said by | Root cause |
|---|---|---|---|
| Mood brief (6.5) | One technique and one picture for "warm and communal"; a single plate in an empty row | 6 | **A. Content**: thin warm set. **B. Layout**: a lone way has no layout of its own |
| Mood brief | Word-only matches look like answers (the Igeha chocolate advert for a choir) | 3 | **A. Content/fit**: word matches shown at full weight |
| Ask answer (7.75) | Picks fit the technique, not the brief (Floral Fantasy for "one small figure") | 5 | **A. Content/fit**: the negative-space examples are prints whose empty space is the paper margin |
| Ask answer | Rows end ragged; a way's row fills about 70% | 6 | **B. Picture-row system** |
| Ask answer | Reasons describe pixels, not why the picture fits | 2 | **D. Copy** |
| Ask front page (8) | The sample "one small figure in a lot of empty space" shows a floral sprig, medallions and a crowded interior | 6 | **A. Content/fit**: sample brief vs its pictures |
| Ask front page | On phone the strip changes pattern partway down | 4 | **B. Picture-row system** |
| Library (7.75) | Techniques hidden until hover, though the page says "filed by technique" | 4 | **C. Screen leftover**: hover-only caption line |
| Library | Near-duplicates side by side (two Podangis, two Mammals Hall) | 3 | **A. Content**: duplicates in the starter |
| Library | Orphan last row; ragged phone rows | 5 | **B. Picture-row system** |
| Technique (8.5) | Doubtful examples (Divan Japonais, Moon-Viewing Promontory as silhouette) | 4 | **A. Content**: weak proposed readings shown as examples |
| Technique | Header count (6) differs from the strip (5); the hero crosses the rule | 3 | **C. Screen leftover** |
| Image (8) | Title block bottom-aligned, leaving a block of empty space | 4 | **C. Screen leftover** |
| Image | "More like this" orphan; "Also shows" ragged | 4 | **B. Picture-row system** |
| Techniques index (7.5) | Goals are text-only boxed cards | 6 | **C. Screen leftover** (generic card grid) |
| Techniques index | Techniques share thumbnails (Repetition/Rhythm, Scale/Vantage) | 3 | **A. Content**: one picture leads two techniques |
| Compare (6.75) | Empty key column (about 370 px) over a one-line note | 6 | **C. Screen leftover** |
| Compare | Matrix of dashes; numbers without scale; phone clipped | 5 | **C. Screen leftover** |
| Projects (6.75) | Direction pictures tiny and uneven | 6 | **C. Screen leftover** |
| Projects | The same poster in two directions (from the saved AI answer) | 3 | **A. Content**: example answer not curated |
| Find (7.75) | Recent strip orphan rows | 3 | **B. Picture-row system** |

## Root causes, ranked, and what the content round already removed

| Root cause | Share of the gap | Removed by the content round | Still there |
|---|---|---|---|
| **A. Content and fit of picks** | largest: 6 screens | Stock photos (all 16 gone); raw titles (23 cleaned); weak leads (a lead chosen for each technique); generated pictures never lead; moods judged per picture | The front-page sample's pictures don't show its brief; weak proposed examples still shown (silhouette); duplicates side by side; one picture leads two techniques; the warm set is thin; word-only matches shown as answers; the saved Projects answer reuses a poster |
| **B. Picture-row system** | 5 screens | Rows fill on desktop, generated sorted last | Orphan or ragged last rows; phone strips that switch pattern; a single way laid out like a full row |
| **C. Screen leftovers** | 5 screens | Compare captions and labels; Find and Projects show results | Compare's empty key column; image title alignment; Explore goal cards; Projects thumbnails; Library techniques hidden on hover; the technique count |
| **D. Copy of reasons** | 2 reports | — | Reasons read as pixel inventory, not as why the picture fits |

## What was fixed, and the check that each cause is gone

Tactics are in `TACTICS.md`. Each fix was verified by one fresh reviewer, who answered one question per screen from
the before (`f-*`) and after (`g-*`) screenshots. These screenshots are kept on disk only, outside git.

| Cause | Fix (commit) | Verdict |
|---|---|---|
| A. Answers ignored the curator's leads, so negative space opened on paper-margin prints | The desk ranks each technique's curated leads first, in the curator's order; it prefers pictures tagged calm or energetic when the brief asks for them (`e3140aa`) | Partly. Scale contrast now opens on the Hiroshige eagle. Negative space opens on a Redon: the reviewer judged it strongest for the technique, but it is eerie for a calm brief. No calm picture in the starter shows negative space (content gap) |
| A. The front-page sample's pictures did not show its brief | The sample is a brief the library answers well, about figures read by their outline (`e3140aa`, `ae70a5f`) | Partly, then reworded so the brief matches what its pictures show |
| A. Weak readings taught techniques (Divan Japonais as silhouette) | Technique pages show the chosen examples; other readings fold away, marked unchecked (`fa7a2a1`) | Fixed |
| A. Two techniques led by the same picture | Each technique gets its own index picture (`fa7a2a1`) | Fixed |
| C. Library techniques hidden until hover | Every tile shows its techniques (`189fc01`) | Fixed |
| C. Explore goals as boxed cards | A ruled index (`189fc01`) | Fixed |
| C. Projects direction pictures tiny and uneven | One lead picture per direction at one height (`189fc01`, `ae70a5f`) | Fixed |
| C. Image title bottom-aligned | Top-aligned (`189fc01`) | Partly: the empty space moved below the buttons |
| C. Compare's empty key column | A 160 px column holding the legend, on desktop only (`189fc01`, `6bbe7a1`, `ae70a5f`) | Partly: the column is narrower and holds the key |

Not addressed in this round:
- **B. Picture-row system.** Orphan and ragged rows, and phone patterns that change within a strip. Code-measured rows
  were tried in pass C and reverted.
- **D. Reason copy.** Reasons still describe the pixels rather than why the picture fits.
- **Content gaps.** Warm has two pictures. No calm picture shows negative space. Duplicate orchids and Mammals Hall
  photographs remain in the starter.
