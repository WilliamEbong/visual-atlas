# Overnight changes, 22–23 November 2026

## Landed 2026-11-23

The branch was merged into `visual-atlas-v0.4` as `a30add4` (originally `9f2c85b`) and pushed, followed by the dependency security patch `e3c8d23` (originally `42ead4b`; pillow 13.0.0, certifi and opentelemetry-api; the audit is clean), and CI is green. The MCP server `visual-atlas` is registered for Claude Code. `main` and the public demo were deliberately left alone until your blind test.

On 2026-11-23, with your approval, the design-review screenshots the merge had added (354 files, about 400 MB, in `design-review/r2`, `r3`, `r4`, `r5` and `v0.5`) were removed from this branch's history and are now gitignored. The captures are kept locally, not in the repository: in `design-review/` of this working copy and in `C:\Users\Owner\VisualAtlas-design-review-backup\` (with earlier overwritten versions and a commit map). Every screenshot path named below refers to those local copies. Commit hashes after `f9e400c` quoted below are the pre-rewrite ones; `commit-map.txt` in that backup folder gives the new hash for each, and the local branch `backup/v0.4-before-strip` keeps the old history.

Branch `claude/product-direction-d8e569`, cut from `visual-atlas-v0.4` at `f9e400c`. It was merged into
`visual-atlas-v0.4` (`9f2c85b`) and pushed on 2026-11-23; nothing was merged to `main`, tagged or released, and the
version number is unchanged (0.4.0). Your real library at `C:\Users\Owner\VisualAtlas`
was never touched.

## Design root-cause pass (23 November, branch `claude/design-root-cause`)

On your instruction this round stopped the pass-and-rescore loop and went at the causes. The full causes table,
the fixes and the verification verdicts are in `docs/evaluation/r6/CAUSES.md`; the tactics and their sources (the
William Web Design kit, impeccable, taste-skill, frontend-design, design-critique, and how Are.na, Cosmos and museum
collection sites present pictures) are in `docs/evaluation/r6/TACTICS.md`.

**Causes, ranked.**
- **A. The content and fit of picks** affects 6 screens. The content round had already removed the stock photos and
  raw titles, picked a lead for each technique and judged moods per picture. Still left:
  - Ask ignored the curator's leads, so negative-space answers opened on prints whose empty space is the paper
    margin.
  - The front-page sample's pictures did not show its brief.
  - Weak readings taught techniques (Divan Japonais as silhouette).
  - Two techniques shared one picture on the index.
- **B. The picture-row system** (orphan rows, uneven phone strips) affects 5 screens.
- **C. Leftovers specific to one screen:**
  - Compare's empty key column;
  - the image title aligned to the bottom;
  - Explore's boxed goal cards;
  - tiny Projects pictures;
  - Library techniques shown only on hover.
- **D. Reasons** describe pixels, not fit.

**Fixed, and how each was checked.** A fresh reviewer answered one question per screen from before-and-after
screenshots.

| Cause | Verdict |
|---|---|
| Answers lead with the curator's chosen examples; calm and motion prefer pictures that carry them | Partly: scale contrast now opens on the Hiroshige eagle, but no calm picture in the starter shows negative space |
| Technique pages teach with chosen examples; other readings fold away | Fixed |
| One index picture per technique | Fixed |
| Library techniques shown on every tile | Fixed |
| Goals as a ruled index | Fixed |
| One lead picture per Projects direction | Fixed |
| Image title moved to the top | Partly |
| Compare key column narrowed to hold the legend | Partly; the table columns now also line up with the pictures |

**Codex review of this branch:** three real defects, all fixed with tests:
- a picture tagged only with motion could pass the warm filter;
- the curator bonus could outrank a reading you confirmed;
- the technique routes failed without `leads.json`.

A fourth finding (thumbnail assignment in personal libraries) is a fringe case and was left.

**Final scores** (one fresh pair, screenshots `h-*`):
- product designer 7.1, editorial designer 6.8, a mean of 6.95, against 7.5 for the content round;
- both scored the front page 6 because my reworded sample brief read no technique, so the front page showed no
  pictures. That was fixed after scoring (`2848611`) and a test now guards it. With the front page at its earlier 8,
  the mean would be about 7.15. That figure is my estimate, not a measured score.

**What still keeps each screen under 9, and the next tactic:**

| Screen | Still under 9 | Next tactic |
|---|---|---|
| Ask answer, Projects, Find, Library, Image | Rows end short, and phone strips change width (B) | Lay rows out in code and give a short last row a deliberate half or two-thirds layout. Source: TACTICS B, Flickr-style rows |
| Ask answer, mood brief | Picks fit the technique, not the brief's mood: eerie Redon for a calm slide | Content: add calm negative-space and warm works to the starter. Ranking already prefers tagged moods |
| Mood brief | One way, one picture; the honest note sits below it | Lead with the thin-answer note and Find; offer mood techniques first |
| Explore | Goals have no pictures | One lead picture per goal |
| Compare | A matrix of dashes, unlabelled numbers | Put shared techniques first; use words or bars |
| Image | Empty space beside the picture under the buttons | Move the licence and credit into that column |
| Projects | The saved AI answer's picks are weak (ballet for "neighbours singing") | Curate or pin the example's pictures |

**How reliable the scores are.**
- The same build drew 6 and 8 for one screen from two scorers.
- Means moved by 0.1–0.3 between builds with no relevant change.
- Treat differences under about 0.5 as noise.
- The direct per-cause checks are the better evidence: 5 of 8 causes fixed, 3 partly.
- The scores do agree, across every scorer, on what remains: row layout and the fit of picks to the brief.

## What changed for you, in plain words

**Visual Atlas is now a reference desk.** You, or an AI agent working for you, say what a picture should do. It
answers with ways to do it. Each way is one technique, with pictures that show it, the reason each picture was
chosen, and whether you may publish it.

**In the app**
- **Three places: Ask, Library, Techniques.** Find images, Projects, Collections, Jobs and Settings sit on the
  right.
- **Ask is the front page.** It opens on a sample answer.
  - Your brief gets "Ways to do it": each technique as a band of large pictures, with "how to carry it out" folded
    underneath.
  - The other matches fold under one link.
  - If the brief names a mood ("warm and communal", "serious", "playful"), the answer uses only pictures that carry
    that mood. When your library has little for it, the answer says so and offers Find.
- **More like this.** Open any picture to see pictures with a similar composition. The back link returns you to your
  answer.
- **The starter library is curated: 102 museum and archive works.**
  - The stock sunsets, laptops and "odd one out" snapshots are gone.
  - Titles are cleaned, and the original stays in each record.
  - Every technique opens on its strongest example, chosen by a reviewer from the pixels.
- **Find shows what it recently added.** **Projects** shows a real saved answer (four directions for a choir poster)
  before you write your first brief.
- **The whole app had design passes.** Keyboard and contrast meet WCAG AA, phones work, and pictures are not
  cropped.

**For AI agents (Claude Code, Codex)**
- A read-only MCP server and CLI let agents:
  - ask for advice and get distinct directions;
  - look at the pictures and find look-alikes;
  - search the public museum collections live.
- Every result is licence-checked by the atlas and comes with its credit. The guide's section "Use Visual Atlas
  from an AI agent" has the one-line setup.

**What the tests say, honestly**
- **Reading briefs.**
  - Recall doubled on 45 briefs the reader was never tuned on (0.18 to 0.37).
  - Mood briefs are now read: 13 of 13 on new mood briefs. These were written alongside the cues, so the result is
    optimistic.
  - Word matching still misses about half of what people mean.
- **Proxy blind test.** Opus judges preferred an Opus agent without the desk. **Your own blind test is the deciding
  one** (`docs/evaluation/v0.5/BLIND-TEST.md`).
- **Design scores.** Fresh scorers rated ten screens out of 10:
  - from 6.98 to 7.5 overall (product designer 7.25, editorial designer 7.8);
  - technique pages scored 8.5, and the Ask front page and image page 8.

  Layout changes alone stalled at about 7; better pictures and honest answers moved the score. What is left before 9
  is listed under "Content round".
- **Checks.** 477 backend tests, 18 web tests, Ruff, TypeScript, the taxonomy and data checks, and four Codex
  reviews. Every confirmed finding was fixed with a test.

**Your decisions**
1. Run the blind test.
2. Merge if you like it. The steps and rollback are at the end of this file.
3. Decide whether merging to `main` should republish the public demo.

## Structural design (23 November, after round 4)

Polishing had stalled at about 7 out of 10, and the target is 9 on every main screen. So the work stopped polishing
and looked for the cause.

**Diagnosis.** One reader went through every reviewer report from five scored rounds. Three fresh Opus reviewers,
each with a different lens (information architecture, editorial identity, image tools), looked at the app as it
stood (`design-review/r5/base-*`). All three named the same cause:
- **The app had no centre.** The brief was typed into three different forms (Ask, Find, My project), and none of
  them was the first screen: `#/` opened an uncurated 8,000 px wall.
- **In the answer, pictures were subordinate to text.** The answer's own pictures were 100 to 170 px beside a text
  column, smaller than the leftover "More references" below them.
- Navigation had six peer places plus two tools.

The comment reader added two causes. There was no single picture system, and content problems (stock photos,
raw titles, thin matches) that layout cannot fix.

References the reviewers cited:
- Are.na: the brief or technique as the one container.
- Rijksmuseum and Cooper Hewitt object pages: one large picture with a quiet register.
- Cosmos and Savee: a near-captionless grid, with detail on demand.

**Pass A: Ask is the centre; pictures lead.** Commit `1881e76`; screenshots `design-review/r5/a-*`.
- **Navigation:** three places, Ask, Library and Techniques. Find images, Projects, Collections, Jobs and Settings
  are tools on the right. `#/` opens Ask, the Library moved to `#/library`, and old `#/?technique=…` links still open
  the Library.
- **The answer:** each way is a full-width band. The technique and its idea sit above, and its pictures fill the
  band at up to 400 px tall. "How to carry it out" folds away. The other matches fold under "See N more pictures
  that match".
- **Library:** tiles show the picture and its title, with maker and techniques on hover or focus. Rows are taller
  (300 px). The random hero collage is gone.

| Pass | Product designer | Editorial designer | Kept? |
|---|---|---|---|
| before (round 5 scores) | 7.1 | 6.85 | |
| A | 6.9 | 7.0 | kept: flat (6.95 against 6.98), but both scorers named the answer bands the best composition in the app |
| B | 7.0 | 7.1 | kept: flat (7.05) |
| C | 6.8 | 6.8 | reverted: lower (6.8). Its screenshots stay as `design-review/r5/c-*` |

**Pass B: one picture system, one job per screen.** Commit `5d94449`; screenshots `b-*`.
- Picture rows fill their width, capped at 1.6 times the row height.
- Once you have asked, the brief folds to one line.
- The sample answer shows only pictures and their technique.
- Compare keeps each picture with its caption, and the table lines up with the pictures.
- Find shows the request and the sources, with the rest under Refine.
- Projects shows a sample while it is empty.
- The technique lens carries its own caption.
- Explore folds its glossary away.
- The review buttons on the image page appear on hover or focus.

**Pass C: rows measured in code.** Commit `87b6b78`, reverted. A justified-layout function sized every row from the
container's width. Both scorers called it the single biggest lever, provided it also balanced the last row, but the
pass scored lower, so it was reverted as the rule requires. It can be restored with
`git revert fb5bae3`.

**Stopped: three structural approaches did not raise the score.** Fresh scorers put every build since round 4
between 6.8 and 7.1. This is what blocks a 9, from the eight reports of this cycle:
1. **Content, which layout cannot fix.** Every scorer, every round, names the pictures themselves:
   - stock photos (sunsets, laptops, bins) beside museum works;
   - raw source titles ("Odd one out" several times, "MA9 Mashup Camp…", file numbers);
   - weak technique examples (sunsets as the silhouette lead);
   - generated examples among museum works.

   A 9 needs a curated starter: museum works first, cleaned display titles, and a lead example chosen by
   strength.
2. **Missed briefs.** "Warm and communal" reads as nothing, because there are no mood goals. That is the
   taxonomy decision already listed for you.
3. **Screens with no pictures of what you get back.**
   - Find shows no recent results.
   - Projects shows no real example direction. Directions come from an assistant, so a convincing sample needs a
     saved real run, not a mock-up.
4. **A long tail on every screen.** Each scorer finds two or three new items per screen:
   - Compare's numbers have no labels;
   - phone tabs wrap;
   - text links are 4 px off the edge;
   - "Fig. 10 843 × 979" reads as one number.

   Fixing these lifts single screens, but no 2-screen change moves a 10-screen mean.
5. **The measurement.** The same build drew 8 and 6 for Explore from two scorers. Pass-to-pass differences of
   0.1 to 0.25 are inside that noise. A 9 would need a steady panel of scorers, or a smaller set of screens.

The most-named next step is to restore pass C with a balanced last row, then move the image page's two old strips
onto it. After that comes content curation (point 1), which matters more than any layout change.


## Content round (23 November, after the structural cycle)

The scorers' reasons pointed at content, not layout, so this round worked on content. One commit per item.

- **Curated starter** (`b1a99fb`, record `docs/evaluation/r5/STARTER-CURATION.md`). Sixteen stock snapshots were
  removed: sunsets, laptop keyboards, "odd one out" photos and a hackathon photo. Fourteen museum and archive works
  replaced them: Edouart silhouettes, Rackham, Runge, Hodler, Haeckel, Moronobu, Degas, Hiroshige and Julia Margaret
  Cameron. The pack is now 102 references. 23 display titles were cleaned, and each original is kept in its rights
  record (`source_title`). Licences and licence evidence are unchanged.
- **Leads by strength** (`47ddecd`, `1b9171d`, `docs/evaluation/r5/LEADS.md`). A fresh reviewer ranked every
  technique's starter examples from the pixels. Each technique page and the Techniques index now open on the
  strongest one; a picture you confirmed still comes first. Four techniques have no strong example in the pack:
  symmetry, selective focus, leading lines and figure–ground ambiguity.
- **Mood goals** (`1b4de9a`, `docs/evaluation/r2/MOOD-GOALS.md`). Five were added: warm and welcoming, serious and
  credible, playful, luxurious, and lonely or wistful. Calm and energetic were already covered by existing goals.
  - On 13 new mood briefs, the intended goal was read 2 times out of 13 before and 13 out of 13 after. These briefs
    were written with the cues, so the result is optimistic.
  - On the held-out set, recall is unchanged. Goal precision falls from 0.87 to 0.73 because those labels predate
    mood goals; scored on the original 11 goals, the numbers are identical.
- **Moods belong to pictures** (`a39a9ab`, `docs/evaluation/r5/MOODS.md`). A fresh reviewer tagged the moods each
  starter picture itself conveys (42 of 102).
  - A brief that asks for a mood is now answered only with pictures that carry it. "Warm and communal" no longer
    offers a cholera caricature.
  - Warm is thin (two pictures), and the answer now says so plainly. Finding more becomes the next step.
- **What you get back.** Find shows the pictures it recently added. Projects shows a saved real answer before the
  first brief: one Codex run, four directions for a choir poster, from `scripts/make_example_brief.py`.
- **Long tail.**
  - Compare labels its measures, and the image page separates the figure number from the image size.
  - Phone tabs scroll instead of wrapping, and the Find switch stacks.
  - A missed brief keeps the same button order as a normal answer.
  - A picture teaches one way only.
  - Generated examples never lead.
- **Codex reviews.**
  - Structural pass, 4 findings fixed: the read-only demo's front page, return links from the sample, "Show more"
    collapsing its own list, and phone Compare overlapping.
  - Content round, 4 findings fixed: false mood claims, the Library mood filter, uniqueness applied after the limit,
    and a stale "Recently added".
  - Final review of the whole branch against `visual-atlas-v0.4`, 3 findings, all confirmed and fixed with tests:
    - the MCP image viewer could open a library file outside the media folder;
    - MCP input on Windows mangled non-ASCII text;
    - readable CLI output dropped the stored credit.

| Build | Product designer | Editorial designer | Mean |
|---|---|---|---|
| after pass B (structural) | 7.0 | 7.1 | 7.05 |
| curated starter, leads, Find, Projects, long tail | 6.8 | 7.3 | 7.05 |
| moods gated by picture | 6.8 | 7.0 | 6.9 |
| final (thin answers said plainly, Codex fixes) | 7.25 | 7.8 | **7.5** |

Final per-screen means (product, editorial):

| Screen | Score |
|---|---|
| Technique | 8.5 (one scorer gave 9) |
| Ask front page | 8 |
| Image page | 8 |
| Library | 7.75 |
| Ask answer | 7.75 |
| Find | 7.75 |
| Techniques index | 7.5 |
| Compare | 6.75 |
| Projects | 6.75 |
| Mood brief | 6.5 |

Content moved the score where three layout passes did not.

**Still between this and 9, per the final scorers:**
1. **Fit of picks.**
   - The front-page example pairs "one small figure in empty space" with a floral print.
   - Reasons describe pixels rather than why the picture suits the brief.
   - Warm has only two pictures, and "communal" could also reach proximity grouping and rhythm.
2. **One picture-row system.**
   - Phone rows switch patterns within a strip.
   - Short last rows are orphaned.
   - Projects' direction pictures are small and uneven.
3. **Compare.** The empty key column, and a matrix of dashes.
4. **Explore.** Goals are text-only boxed cards, and some techniques share a thumbnail.
5. **Content still thin.** Four techniques have no strong starter example. Two Podangis orchids and two Mammals Hall
   photographs sit side by side.

## Round 4: acceptance, merge rehearsal, scored design (23 November)

**Independent acceptance.** Two fresh Opus testers, each given only the README and the user guide.
- *Designer on a deadline* installed the release zip into a temp folder (install 13 s, exit 0, your library untouched)
  and worked a printed choir poster and a calm slide end to end: Ask, references, Explore, Compare, a project,
  a collection, an export.
- *AI agent* did three jobs over MCP and the CLI: a slide, a publishable poster, a landing-page hero.

Everything worked. What they hit, and what changed:
| Found | Fix | Who notices |
|---|---|---|
| "Room on the left", "headline space" became subjects; "warm" matched a gold medal | Layout and mood words are not subjects, and are dropped before the 8-word cap (tested) | every agent and designer |
| Technique ids an agent passed were outranked by word matches | Pictures with technique or goal evidence always come first; confidence breaks ties (tested) | every agent |
| The same two pictures led every negative-space answer | Ties broken by the reading's confidence, not ref order (tested) | everyone who asks |
| `atlas serve` announced an address on a port another app held | It says the port is taken and suggests the next (tested) | anyone running two local apps |
| Credits said "Source: aic"; practice mode showed "fake"; "n.d.." in credits | Collection names, plain names, one full stop (tested) | anyone printing credits |
| The release zip carried `.claude`, `.agents`, `.specify`, `specs` and these notes | Left out of the zip with export-ignore | anyone opening the download |
| The Commons note promised personality-rights flags that are not shown | Note now says they are not checked | anyone using recent photos of people |
| Error named a "techniques tool" | Names `list_techniques`; the guide maps CLI and MCP names | agents |

Not fixed (content or decisions): the starter has no choir or gathering pictures; museum copies are about 850 px
wide, so they are references, not print files; there are no mood goals such as "warm and welcoming"; search on AIC
matches artist names ("church" finds Frederic Church).

**Merge rehearsal.** Clean merge onto `visual-atlas-v0.4`; 456 backend tests and every other check passed on the
merged result (steps and rollback at the end of this file).

**Scored design cycle.** Fresh scorers (a senior product designer with `impeccable`, an editorial designer with
`taste-skill`) scored ten screens out of 10 after each fix batch; screenshots `design-review/r4/score1-*` to
`score5-*`.
| Round | Product designer | Editorial designer | Main fix that followed |
|---|---|---|---|
| 1 | 6.7 | 6.6 | strips stop cutting off; reasons under pictures; Compare and Find on phones |
| 2 | 6.9 | 6.3 | (scored the old ranking by mistake) Explore thumbnails; mood words |
| 3 | 7.45 | 6.9 | one-band strips; generated examples after licensed ones |
| 4 | 7.5 | 7.15 | every strip uses the Library's justified rows |
| 5 | 7.1 | 6.85 | scores fell, so the cycle stopped; a last fix put the technique examples on the same rows and capped phone pictures at 320 px (`final-*`) |

Left from the last scoring (both scorers, about 6 to 7 out of 10 on these screens): Compare on a phone and its matrix lining up with the pictures; My project showing one worked example direction; Find explaining its steps twice; raw uploader titles in the Library ("Odd one out"); a missed brief showing a single picture under "Meanwhile".

**Codex review of round 4:** four findings, then two more on the fix, all confirmed and fixed with tests (word-only
results outranking evidence, mood words crowding out a subject, phone Compare losing its controls, unreachable word
matches, a routed word match counted as evidence, phone strips wrapping). A final review of the last changes found two more, both fixed: strip pictures were cropped (now shown whole), and two works with the same title had the same link name (the maker is now read out).

## Round 3: tidy, simplify, graphify (23 November)

**Bar used:** only changes someone notices (a designer, an agent, a maintainer) or that remove code. Two read-only Opus
audits (`ponytail-audit` style) covered the Python and the web app; every cut was checked by grep before it was made.

| Change | Who notices | Measured |
|---|---|---|
| Reverted two round-2 pieces that served only contrived cases: the on-disk picture-signature cache (owner-only cold start; the app already warms at start) and design-system id numbering (two folders whose names slug alike) | maintainers | −107 lines, 4 tests for removed code removed |
| The desk no longer imports the job runner (httpx, providers) | an agent starting the MCP server | `import atlas.mcp_server` ~2.7 s → ~1.5 s (median of 6) |
| Dead code: `Store.fix_metadata`, two unused constants, a one-line CLI wrapper, `scripts/heldout.py` (superseded, unreferenced) | maintainers | −176 lines |
| Dead frontend code: unused CSS, `techniqueName`, `nextIndex` (+ its test), `refreshTaxonomy`, never-passed props | maintainers | −27 lines |
| Five unused screenshots in `docs/media` | anyone downloading the release | −1.3 MB per zip |

**Measured and left alone:** Ask is already fast (advise ~73 ms, directions ~110 ms on the starter library), so caching
the library read was not worth its code. Deferring pydantic model builds saved ~150 ms of import and nothing visible on
the CLI, so it was reverted. Lazy-loading the job runner in the CLI would save ~0.4 s per `atlas` call but touches ~15
commands and only helps agents that use the CLI instead of MCP: listed, not done.

**Audit findings not applied:** `scripts/curate_v04.py` has a test; `eval_v03/v04/r2` are cited as reproduction commands;
`atlas analyze --verify-with none` was reported as a bug but the job layer already turns "none" into no verifier;
replacing cytoscape on the Connections map with plain SVG needs a visual redraw (listed).

**graphify:** `graphify-out/` holds the knowledge graph of the code and docs: 1,498 nodes, 3,884 edges, 84 labelled
communities (`GRAPH_REPORT.md`, interactive `graph.html`, `graph.json`). Code was read structurally (no model); the 44
docs were read by two Opus extraction passes (~358k tokens, no paid service). `.graphifyignore` keeps pictures,
screenshots, evaluation data and builds out; the extraction cache and the local interpreter path are gitignored;
`graphify-out/` is export-ignored, so the release zip is unchanged. Ask it questions from the repo root:
```powershell
graphify query "how does a brief become ranked references"
```
Rebuild after big changes with `/graphify . --update` in Claude Code.

**Codex review of the design pass and clean-up:** 5 findings, all confirmed and fixed (publish mode lost on the sample
strip and on related links, the series rule merging same-titled works, two unnamed thumbnail links, generated examples
showing the second-model mark).

## Design pass (23 November, after your note on UI/UX for the apps)

**How it was run.** Every journey was captured at 1440 px and 375 px (`design-review/r3/before-*`). Seven
fresh-context Opus reviewers each took one lens: first impression and identity (the William Web Design reviewer),
hierarchy and type (with `impeccable` and `frontend-design`), pictures and credits (`taste-skill`), words
(`design:ux-copy`, `humanizer`), flow and states (`design:design-critique`), accessibility
(`design:accessibility-review`, contrast computed from the tokens), and a designer on a two-hour deadline. Fixes went
in six batches, each checked in the browser at both widths with no overflow and no console errors. Fresh reviewers
looked again after batches 3, 4 and 5 (three, two and two reviewers). By the fourth round both said most pages had
nothing a user would notice; their remaining real items (a phone layout I had broken, cropped landscape pictures, the
sample strip's choice, raw dates) were fixed in batch 6.

**What changed, and who notices**
| Change | Who notices |
|---|---|
| Ask opens on pictures: a sample answer before you type | everyone opening Ask |
| "Ways to do it" pictures are not repeated below; one picture per numbered series | everyone who asks |
| Reasons read as technique, a state mark (○ ◐ ●) and the evidence, without lab wording | everyone who asks |
| A brief the atlas could not read shows the goal choices and no stray word match | anyone with a business or mood brief |
| Goal chips are square, fold away once the brief is read, and goals read from the brief say so | anyone correcting a reading |
| A next step after every answer: start a project from the brief (named for you), or find more images | everyone who asks |
| Opening an image from an answer leads back to the answer, and the nav says Ask | everyone who asks |
| Image page in catalogue order, a plain line on what you may do with the picture, checks in words, no model or vendor names in the readings, evidence not repeated | everyone opening an image |
| Captions under each figure on technique pages and strips; file-name noise and camera timestamps removed from titles | everyone browsing |
| Library: the five boxed "ways in" only for a new library; two pictures per row on a phone (page half as long) | every Library visit |
| Collapsed sections show + / − | everyone |
| Keyboard focus visible on every thumbnail; each new page starts at the top with focus on its content | keyboard and screen-reader users |
| Field borders, caption grey and dark-mode region tags meet WCAG AA | low-vision users |
| Finished jobs say so in the top bar; plain job states and assistant names; Compare says when it is full | anyone running Find or Grow |
| One vocabulary for review states: proposed by a model / agreed by a second model / confirmed by you | everyone |
| Pictures shown at their true shape: strips no longer crop landscapes; the technique example is a plate, not a circle | anyone reading a composition |
| Library cards label only checked readings; camera timestamps, file names and "Unknown author Unknown author" cleaned | every Library visit |
| A reading's state said once, the second model's note on its own line; projects from Ask named sensibly | anyone opening an image or starting a project |

Screenshots: before `design-review/r3/before-*`, after the first passes `after-*`, current `final-*`.

**Left on purpose** (minor, or needs a decision): a spacing and type scale token refactor (many small inline values;
no single screen is wrong enough to notice); Explore's technique table without thumbnails; Find's goal selects beside
its reading correction, and assistant names in its "Who analyses" choice (it is a real choice between your two
sign-ins); the Settings source table's exact rules; Compare's contrast and colour numbers without words; the sample
answer's pictures come from the desk's own ranking, so their fit depends on the readings; the Connections map
(cytoscape) redrawn as SVG.

## Round 2 (23 November, after your approval to keep going)

**The headline is a negative result.** In a proxy of your blind test, Opus judges preferred an Opus agent
*without* the desk on most briefs, in both rounds. Everything else below is what I built and fixed around that.

### What changed
- **Brief reading, measured properly.** 80 new briefs written by Opus subagents acting as designers and as AI agents,
  split dev/test by a hash and frozen before any change (`docs/evaluation/r2/BRIEF-REPORT.md`). A third subagent,
  who never saw a brief, wrote 594 everyday phrases for the codebook. On the **test split** (not looked at while
  tuning): recall **0.18 → 0.37**, precision **0.77 → 0.87**, briefs with at least one right code **13/40 → 24/40**.
  Word matching still misses about half of paraphrases, so:
- **Agents and people can say what the words missed.** `advise` and `suggest_directions` take technique and goal ids;
  when the words match nothing, the answer includes the codebook. On **Ask**, goal chips under the reading change
  the answer with one click.
- **New agent tools** (MCP and CLI): `suggest_directions` (`atlas directions`): distinct ways to answer a brief, one
  technique each, with pictures; `similar_references` (`atlas similar`): composition look-alikes;
  `search_open_collections` (`atlas search-open`): live search of Commons, the Met, AIC, Cleveland and the
  Rijksmuseum, every result licence-checked by `atlas/rights.py`, nothing downloaded or stored. It is the one tool
  that goes online.
- **Ask page:** "Ways to do it" (one technique each, with its pictures), pictures that matched on words only kept
  apart, "Picture unavailable" instead of blank boxes, longer reasons. **More like this** on reference and image
  pages. Image page: a reading the second model disputed is marked; related tabs open on the best-checked technique.
  Full-app design review by a fresh-context reviewer: 14 findings, 12 applied (skipped: removing the Library's five
  boxed ways in; numbering plates on the technique page). Before/after screenshots: `design-review/r2/`.
- **Starter library 93 → 104:** 11 typography, poster and information-design references (Minard, Playfair, Du Bois,
  the 1908 Underground map, type specimens, Lissitzky, Toulouse-Lautrec, Hohlwein, Marinetti). Rights by
  `atlas/rights.py`; readings `proposed`. `docs/evaluation/r2/typography/CURATION.md`.
- **Generated layer 9 → 18:** two each for leading lines, tight cropping, gaze direction, contextual incongruity, and
  a figure–ground retry (all nine passed the rubric). Every generated file now carries an IPTC
  "trainedAlgorithmicMedia" XMP label (C2PA-readable; not a signed manifest), added without re-encoding.
- **Closed from the round 1 list:** design-system id clash (left as is: it needs two of your folders whose names slug alike); `generated/` stays in
  the release on purpose (the layer needs it); release zip rebuilt and installed into a temp folder (installer
  exit 0, CLI and MCP answer from the installed copy); slow Ask traced to tokenising every reference on each
  request (now cached, ~0.2 s → ~0.08 s) plus a cold first call (the app now warms the desk at start).
- **Defects fixed with failing tests first:** Rijksmuseum search crashed on list-shaped Linked Art dates; Commons
  credits carried language prefixes, hidden Wikidata labels, footnote markers and run-on descriptions (found by the
  blind judges); "centre" alone was read as off-centre placement.
- **Codex review, round 2:** 8 findings, all confirmed and fixed, each with a test that fails on the old code: an
  empty collection choice searched every provider; publish mode was lost on the way to More like this; the
  signature cache kept paths and previews in a shared file; library-only directions could reveal private routing;
  directions dropped technique examples outranked by word matches; `use=Publish` silently meant "everything";
  provider cooldowns were lost between agent searches; long colliding design-system ids broke lookups.
- **Codex review, round 3** (on those fixes): 3 findings, all confirmed and fixed with failing tests first: the old
  shared cache file was left on disk; two comparisons could write the cache at once; directions could still miss
  technique examples ranked below 40 word matches.

### Proxy blind test (`docs/evaluation/r2/proxy/PROXY-REPORT.md`)
| Round | Desk arm | A wins / desk wins / ties (two judges) | Fit A vs desk | Licence A vs desk |
|---|---|---|---|---|
| 1 | local library + generated | 8/1/1 and 8/1/1 | 4.65 vs 3.65 | 5.00 vs 4.95 |
| 2 | + open search, fit first | 6/1/3 and 7/2/1 | 4.50 vs 3.95 | 5.00 vs 4.20 (credit noise, now fixed) |

What it means: an Opus agent with web search already finds good public-domain pictures and reads their licences
correctly, so licence checking alone does not make the desk worth calling for that agent. It does not test your
taste, your briefs, or weaker agents. **Your blind test is still the deciding one**; it is ready.

### Decisions, and how to undo each
| Decision | Undo |
|---|---|
| One MCP tool goes online (`search_open_collections`), bounded, nothing stored | Delete it from `TOOLS` in `atlas/mcp_server.py` |
| 594 cue phrases merged into `atlas/data/taxonomy.json` | `git revert` the commit `5485765`, or edit the phrases |
| Kept a figure–ground image whose lower half also reads as a bust | Remove `fg-ambiguity-03` from `generated/manifest.json` |

### Not done
- **Your blind test** (`docs/evaluation/v0.5/BLIND-TEST.md`). It decides whether the desk beats plain search.
- **Design, before 9.** The details are in "Content round":
  - picks that do not always fit the brief, starting with the front-page example;
  - one picture-row system on phones;
  - Compare's empty column and its table of dashes;
  - text-only goal cards on the Techniques index.
- **Content.**
  - "Warm" has two pictures.
  - Four techniques have no strong example: symmetry, selective focus, leading lines, figure–ground ambiguity.
  - Museum copies are about 850 px wide, so they work as references, not print files.
- **Brief reading.** Word matching still misses about half of what people mean. Agents can pass technique or goal
  ids directly. The held-out labels need re-judging against the 16-goal codebook before goal precision can be
  compared again.
- **Later:** an HTTP MCP transport; C2PA manifests on generated files (an IPTC label is there now).
- **Not run:** the live provider tests (`-m live`), because nothing that touches the providers changed.

## Try it
```powershell
uv run atlas advise "a calm opening slide: one small figure in a lot of empty space" --text
```
```powershell
uv run atlas refs --technique figure-ground-ambiguity --text
```
```powershell
$env:VISUAL_ATLAS_DESIGN_SYSTEMS="auto"; uv run atlas advise "cyberpunk night city in the rain for a game pitch" --text
```
```powershell
claude mcp add visual-atlas -s user -e VISUAL_ATLAS_DESIGN_SYSTEMS=auto -- uv run --directory C:\Users\Owner\OneDrive\Documents\VisualAtlas atlas mcp
```
Then ask Claude Code: "Use visual-atlas to find two references for a calm opening slide and show me them." In the
app, start it with `uv run visual-atlas` and open **Ask**.

## How to merge
Done on 2026-11-23 (merge `9f2c85b` on `visual-atlas-v0.4`, pushed); the steps are kept for the record.
`visual-atlas-v0.4` then still pointed at `f9e400c`, where this branch was cut, so the merge had no conflicts (85 commits).
A full merge rehearsal passed every check in round 4; the final checks on this branch passed again: 477 backend
tests, 18 web tests, Ruff, TypeScript, the taxonomy check and the data guard.

From the main checkout (`C:\Users\Owner\OneDrive\Documents\VisualAtlas`), with a clean working tree:
```powershell
git switch visual-atlas-v0.4
```
```powershell
git merge --no-ff claude/product-direction-d8e569
```
```powershell
uv sync; npm --prefix web ci; npm --prefix web run build; uv run pytest
```
No database migration is involved; an existing library keeps working. To bring the curated starter works into an
existing library, run `uv run atlas starter-import`. It adds the 14 new works and skips those already present. The
16 retired stock snapshots stay in a library that already has them; remove them in the app if you like.

**Rollback:** the merge is pushed, so use `git revert -m 1 9f2c85b` (the reset that worked before pushing no
longer applies).

**Warning about `main`:** a push to `main` triggers the GitHub Pages workflow and republishes the public demo.
Merge into `visual-atlas-v0.4` first, and only bring it to `main` when you want the demo updated. The merge into
`visual-atlas-v0.4` is pushed; `main` has not been touched.
