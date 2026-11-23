# Overnight changes, 22–23 November 2026

Branch `claude/product-direction-d8e569`, cut from `visual-atlas-v0.4` at `f9e400c`. Nothing has been pushed, merged,
tagged or released, and the version number is unchanged (0.4.0). Your real library at `C:\Users\Owner\VisualAtlas`
was never touched.

## What changed for you, in plain words

**Visual Atlas is now a reference desk.** You (or an AI agent working for you) say what a picture should do, and it
answers with ways to do it, each one a technique with pictures that show it, the reason each picture was chosen, and
whether you may publish it.

**In the app**
- **Ask** is the first page. It opens on a sample answer with pictures. You type a brief and get "Ways to do it",
  more references, and a next step (start a project from the brief, or find more images). If it can't tell what the
  picture should do, you pick it with one click and the answer changes.
- Open any picture and **More like this** shows pictures with a similar composition. The back link returns you to
  your answer.
- The whole app had a design pass: seven specialist reviewers, six rounds of fixes, four rounds of fresh review.
  Pictures are no longer cropped, words are plain, keyboard and contrast meet WCAG AA, and phones work.
  Screenshots are in `design-review/r3` and `design-review/r4`.
- The starter library grew from 93 to 104 pictures, adding posters, type specimens and Minard/Playfair/Du Bois
  charts. There are 18 generated teaching examples, each labelled as generated (with an IPTC tag inside the file),
  and none is ever offered for publication.

**For AI agents (Claude Code, Codex)**
- There is a read-only MCP server and CLI. Agents can ask for advice, get distinct directions, look at the pictures,
  find look-alikes, and search the public museum collections live. Every result is licence-checked by the atlas and
  comes with its credit. The guide's section "Use Visual Atlas from an AI agent" has the one-line setup.

**What the tests say, honestly**
- **Reading briefs.** Recall doubled on 45 new briefs it was never tuned on (from 0.18 to 0.37), and precision rose
  too. Word matching still misses about half of what people mean, so agents and people can now say it directly.
- **Proxy blind test.** Opus judges preferred an Opus agent *without* the desk in both rounds. Licences were
  equally right; the desk lost on fit because its own collection is small. Live open-collection search halved the
  gap. **Your own blind test is still the deciding one** (`docs/evaluation/v0.5/BLIND-TEST.md`).
- **Acceptance testers.** An independent "designer" installed the release from the zip and worked a choir-poster
  brief end to end. An "agent" did three jobs over MCP. Everything worked. What they hit has been fixed
  (listed under "Round 4"). The main gap left is content: the starter has no choir or gathering pictures, and the
  museum copies are about 850 px wide, so they are references, not print files.

**Your decisions**
1. Run the blind test.
2. Merge if you like it (steps at the end; the rehearsal merge passed every check).
3. Optionally: add mood goals such as "warm and welcoming" to the taxonomy (both testers asked for them); decide
   whether merging to `main` should publish the demo.

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
`git revert <the revert commit>`.

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

### Not done in round 2
- Interface and instrument-panel references (none found within the search budget).
- A signed C2PA manifest (needs a signing certificate); the IPTC label is the cheap equivalent.
- The release zip has not been rebuilt since the last commits; rebuild with `scripts/build-release.ps1` before use.

## Product thesis, in five lines
1. **For** designers, and the AI agents that now pick images for their slides, pages and posters.
2. **Job:** turn a brief into a few references worth borrowing from. Each says which technique it shows, the
   visible evidence, how sure the reading is, its licence and credit, and how to apply the idea.
3. **Different:** reference tools keep pictures, not reasons. Agent image tools return links with no licence and no
   reason. Visual Atlas already has evidence, review states and licence records for every image.
4. **Smallest proof:** one engine without AI behind three doors: the **Ask** page, the CLI (`atlas advise`) and a
   read-only MCP server (`atlas mcp`).
5. **Test that decides it:** you rate agent output with and without the desk on 12–20 of your own briefs
   (`docs/evaluation/v0.5/BLIND-TEST.md`). It is prepared but not run, because the ratings must be yours.

Research with sources is in `docs/research/01–04`, and the decision and its reasoning in `docs/research/05-thesis.md`.

## What was built
- **Reference desk** (`atlas/desk.py`). A brief goes in. Out come the goals, techniques and subject words it read
  as, guidance for each technique (what it is, when it helps, what to look for, what not to confuse it with), and
  ranked references. Each reference carries its reasons, licence, credit and layer. It ranks by stored readings,
  taxonomy links and words, with no AI. It writes nothing.
- **CLI**: `atlas advise`, `atlas refs`, `atlas ref`, `atlas mcp`.
- **MCP server** (`atlas/mcp_server.py`), read-only, over stdio. Seven tools: `advise`, `search_references`,
  `get_reference`, `view_reference` (returns the picture itself), `list_techniques`, `get_technique` and
  `route_brief`. References are named by id, never by path. Every input is validated.
- **Ask page** in the app, plus a reference page for generated and design-system images. Ask is first in the
  navigation, first on the Library home, and first in the welcome dialog.
- **Generated layer** (`generated/`): original images made with Codex image generation for techniques with only
  two or three starter examples. Each keeps its prompt, the works studied, the date and a rubric review
  (`generated/RUBRIC.md`, `generated/STUDY.md`). They are labelled generated everywhere, assert no licence, and are
  never offered as publishable. **12 generated, 9 kept, 3 dropped.** Two each were kept for symmetry, vantage point, proximity grouping and selective focus. Figure–ground ambiguity kept one of four; three attempts failed the rubric because the picture did not flip both ways. I checked the kept images myself as well. Total size is 1.4 MB. To regenerate: `uv run python scripts/generate_images.py`.
- **Your four design systems** as an opt-in local layer (`atlas/layers.py`). They are read in place from
  `%USERPROFILE%\.claude\skills\<system>\` (850 images), never copied, and never in the repo. The layer is off unless
  `VISUAL_ATLAS_DESIGN_SYSTEMS=auto` is set, so it exists only on your machine. The router suggests a system for a
  brief: "cyberpunk night city for a game pitch" goes to harbour-of-drifting, and a brief that matches none goes to
  archive-of-looking.
- **Guards**: `.gitignore` patterns, plus `scripts/check_no_data.py` (already run in CI). It now refuses
  design-system paths and any tracked image whose bytes match one of your design-system files, even renamed.
- **Design**: the Ask page, a welcome without jargon or decorative rules, plain licence wording on result plates,
  balanced headings, and the Library's five ways in fitting one row. A design reviewer subagent (the
  william-web-design reviewer) critiqued the page. Its must-fix findings were applied.
- **Docs**: README sections, user guide sections "Ask the atlas" and "Use Visual Atlas from an AI agent" (MCP setup
  for Claude Code and Codex), and constitution 1.1.0 (principle VII, labelled reference layers).

## Decisions, and how to undo each
| Decision | Why | Undo |
|---|---|---|
| MCP implemented with the standard library, not the official SDK | The SDK needs pywin32 on Windows; `uv` failed to install it 4 times (file lock, invalid wheel entry), and the installer uses `uv` | Replace `atlas/mcp_server.py` with an SDK `MCPServer`; tools map one-to-one |
| Desk uses no AI and the MCP server is read-only | Fast, free, checkable; agents never trigger spending | Add an opt-in `suggest_directions` tool later |
| Design systems are read in place, not imported into the library | Keeps the rights invariant (only `atlas/rights.py` admits images) and keeps private files out of exports and the public repo | Remove `VISUAL_ATLAS_DESIGN_SYSTEMS` from `.env` (off), or delete `atlas/layers.py`'s systems part |
| Generated images assert no licence and never count as publishable | US protection for AI output is unsettled; only you can dedicate work | Change `licence_note` in `generated/manifest.json` if you decide otherwise |
| Brief coding left untuned | The two misses in the CLI run are new test briefs; tuning on them would hide the known recall limit | Add `request_cues` in `atlas/data/taxonomy.json` |
| Ties in design-system routing go to archive-of-looking | Your default system | `atlas/desk.py` `route()` sort key |
| Other layers keep up to half the result places | Otherwise 93 library images bury them | `search()` in `atlas/desk.py` |
| Committed evidence made with design systems off | No private catalogue titles in the public repo | n/a; the design-system run is in the session notes folder |

## Evidence (all gathered in this run, against a scratch library in `%TEMP%\va-home`; your real library was not touched)
| Check | Result |
|---|---|
| Backend tests (`uv run pytest`, offline) | **437 passed**, 1 skipped, 9 live deselected (baseline before the work: 372 passed). One symlink test is skipped because Windows does not let this account create links; the same check is also covered by a deleted-file case that runs. |
| New tests | Engine and layers (`tests/test_desk.py`), CLI and MCP (`tests/test_mcp.py`, including a stdio round trip in a subprocess), web API (`tests/test_desk_api.py`), and Codex review regressions (`tests/test_desk_review.py`). Network and model calls: none are made. |
| Ruff, taxonomy check, data guard | Clean |
| Frontend: TypeScript, vitest, production build, npm audit | TypeScript clean; 15 tests passed; build OK; npm audit 0 vulnerabilities |
| Real MCP round trip from a client | The official MCP Python SDK 2.3.0 `Client` launched `uv run atlas mcp`. It negotiated protocol 2025-11-25, listed 7 tools, called `advise`, received a JPEG from `view_reference`, and got a path traversal refused. Output: `docs/evaluation/v0.5/mcp-roundtrip.json`. A second run with design systems on (it routed to harbour-of-drifting) is kept outside the repo. |
| CLI on real briefs | 8 briefs. 6 read as a known goal or technique and returned credited references with reasons. 2 did not (see below). Output: `docs/evaluation/v0.5/CLI-BRIEFS.md`. |
| Playwright, 1440 px and 375 px | Ask, Library, image page, Explore, Find, and the generated reference page. No horizontal overflow, no broken images, 0 console errors. With design systems on, a tea-garden brief routed to garden-of-lingering, and 12/12 of its images loaded through the token-protected endpoint. Screenshots: `design-review/v0.5/`. Private-image screenshots stay outside the repo. |
| Design review | The william-web-design reviewer (Opus) returned 12 findings. 11 were applied; the header specimens on Ask were skipped. |
| Codex review (codex plugin, adversarial, 2 rounds) | **Round 1:** 7 findings, all confirmed and fixed. **Round 2:** confirmed those fixes and found 4 more, all confirmed and fixed. Every fix has a test that fails on the old code (checked by swapping the old files back in). Details are under "Codex review" below. |
| Generated images | 12 generated, **9 kept, 3 dropped** (all figure–ground ambiguity attempts). I reviewed the kept set myself as well. |

### Codex review
- **Round 1:**
  - Publication is decided by `atlas/rights.py` only. Other layers are reference only, and NC, SA and ND notes read as unclear.
  - Private layer pictures sit behind the launch token.
  - The desk reads through a read-only SQLite connection, so it can never create or migrate a library.
  - Layer files are re-checked on disk when they are served.
  - The commit guard reads Git index blobs, not working files.
  - The MCP server survives hostile frames.
  - Goal reasons quote one technique with its own review state.
- **Round 2:**
  - Library licence codes are matched exactly, so `CC-BY-NC` is never publishable.
  - Design-system ids are slugs.
  - The guard also covers folders set in the library's `.env`.
  - MCP frames are read in bounded pieces.

## Not done
- **The blind test that decides the thesis** (`docs/evaluation/v0.5/BLIND-TEST.md`) needs your own briefs and ratings.
- **Brief reading recall.** "Show how big the mountains are" and "Group three related services" were not
  recognised. Word matching is the known weak point (v0.4 held-out recall was 60%). It was not tuned on these new
  briefs. Agents can pass technique or goal ids directly.
- **A second figure–ground generated image.** Three attempts failed the rubric. The image model finds
  shared-contour designs hard.
- **Later** (thesis): an opt-in MCP `suggest_directions`; visual-similarity search; UI and typography
  references, since the corpus is mostly pre-20th-century art; C2PA manifests on generated files; an HTTP MCP
  transport; header specimens on the Ask page; design-system slug collisions (two folders whose names slug the
  same would share ids).
- **Not tested:** the Windows installer and the release zip were not rebuilt. `generated/` is included in
  `git archive` (no export-ignore). The live provider tests (`-m live`) were not run, because nothing touching
  them changed.
- **Timing:** during the parallel image generation, a few Ask requests took 1.5–8.5 s. Once the machine was
  idle they took 70–315 ms.

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
Rehearsed on 23 November in a throwaway worktree: the branch merges onto `visual-atlas-v0.4` with no conflicts
(`visual-atlas-v0.4` had no new commits since this branch was cut), and on the merged result 456 backend tests,
Ruff, the taxonomy and data checks, TypeScript, 17 frontend tests and the web build all passed.

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
No database migration is involved; an existing library keeps working.

**Rollback** (before pushing): `git reset --hard ORIG_HEAD` on `visual-atlas-v0.4` undoes the merge. After pushing,
use `git revert -m 1 <merge commit>` instead.

**Warning about `main`:** a push to `main` triggers the GitHub Pages workflow and republishes the public demo.
Merge into `visual-atlas-v0.4` first, and only bring it to `main` when you want the demo updated. Nothing here
has been pushed.
