# Overnight changes, 22–23 November 2026

Branch `claude/product-direction-d8e569`, cut from `visual-atlas-v0.4`. Round 1: 13 commits on top of `f9e400c`; round 2 added more (see `git log d6117cf..HEAD`). Nothing has been pushed, merged, tagged or
released, and the version number is unchanged (0.4.0).

## Design pass (23 November, after your note on UI/UX for the apps)

**How it was run.** Every journey was captured at 1440 px and 375 px (`design-review/r3/before-*`). Seven
fresh-context Opus reviewers each took one lens: first impression and identity (the William Web Design reviewer),
hierarchy and type (with `impeccable` and `frontend-design`), pictures and credits (`taste-skill`), words
(`design:ux-copy`, `humanizer`), flow and states (`design:design-critique`), accessibility
(`design:accessibility-review`, contrast computed from the tokens), and a designer on a two-hour deadline. Fixes went
in four batches, each checked in the browser; then a second round of three fresh reviewers
(`design-review/r3/after-*`) and a third round of two (`design-review/r3/final-*`).

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

Screenshots: before `design-review/r3/before-*`, after the first passes `after-*`, current `final-*`.

**Left on purpose** (fringe, or needs a decision): a spacing and type scale token refactor (many small inline values;
no single screen is wrong enough to notice); Explore goal cards without pictures; Find's two sets of goal controls
(changing it touches how Find reads a request); the Settings source table's exact rules; Connections map
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
Review the branch, then from the main checkout:
```powershell
git merge --no-ff claude/product-direction-d8e569
```
It merges into `visual-atlas-v0.4` (its base) without conflicts at the time of writing. Rebuild the web app
(`npm --prefix web run build`) after merging. No database migration is involved.
