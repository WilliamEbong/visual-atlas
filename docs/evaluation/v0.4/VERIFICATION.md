# v0.4 verification

All development libraries were under the system temporary directory, outside OneDrive. The owner's default
library was never opened. The initial working tree was clean at v0.3.0, commit e43e0932ece8be850926e013fc91ce3f84920c32.

## Automated checks

- Baseline offline pytest: 359 passed, 9 live deselected.
- Integrated offline pytest: 372 passed, 9 live deselected. After the candle exclusion, affected starter/curation
  tests passed 10/10. Existing Starlette/httpx deprecation
  warning remains; no dependency change made for it.
- Ruff clean; TypeScript clean; frontend Vitest 15 passed; production Vite build passed.
- Taxonomy validation: 11 goals, 11 operations, 10 domains, 26 techniques. Data-file guard passed.
- New frozen evaluations reproduced by `scripts/eval_v04.py` for development and held-out splits.
- Existing `eval_v03.py` coding development/final rerun with output redirected to `legacy/`, preserving historical
  reports. Its current-code arm is still named v0.3 in JSON; it actually ran v0.4 source.

## Real browser checks (Playwright MCP)

The actual bundled frontend was served on loopback with the temporary library and no worker. Screenshots were
captured and inspected in `design-review/v0.4/`.

- Goal → Isolate operation → Space and depth domain → Negative space isolation technique, with trail retained.
- Readable initial map labels/thumbnails; scrolling canvas; operation/domain relationship explanations in List.
- Clicking an actual domain edge displayed its explanation. Moved the explanation above the canvas after
  visual inspection; rebuilt and verified that it is visible in the initial viewport.
- Expanded negative-space examples from 6 to 18, displaying the full total of 19 in the baseline corpus.
- Selected two images; two-image comparison rendered; exact focus/view/limit/trail URL restored afterward.
- Selected four images; the fifth selection was disabled; four-image comparison rendered at 375px without
  page overflow. Keyboard Enter activated the Isolate link in the accessible exploration list.
- Technique full explanation → Compare them → image → return preserved context. View all in Library → title
  sort → image → next image → return also preserved the expanded List context.
- Image-focused List exposed proposed and second-model-reviewed readings, and main/supporting roles, without
  turning proposals into confirmed classifications. Confirmed-state data flow is separately covered by API tests.
- The reported solitude sentence displayed calm, negative space and scale contrast; subject `solitude`.
  Removed scale contrast, added a goal, edited subjects and verified unchanged original text.
- Corrected Find submitted HTTP 201 with the exact structured correction and original request in the saved job.
  My project saved a real temporary brief and submitted HTTP 201 directions with the corrected interpretation.
  These jobs were cancelled before execution; they prove submission/persistence, not live AI advice.
- Injected reading-endpoint HTTP 503: visible recovery message, manual correction still usable, automatic
  reading recovered after the intercept was removed. This is a deliberate mock failure, not an actual outage.
- At 375 × 812: connections List, image-focused List, Find correction and Project correction had no horizontal
  page overflow; keyboard Tab reached a real link with a visible solid focus outline. Desktop was 1440 × 1000.
- No broken images in inspected graph/example views. Clean post-reload navigation reported zero browser console
  errors/warnings. Deliberate 503 and an earlier stale-server 400 generated expected errors during testing;
  the final corrected submission passed. Selector/wait mistakes in the test driver were corrected and rerun.

## Independent review

A separate agent reviewed graph/UI/demo and brief integration. Fixed: reciprocal related-edge duplicate keys;
return context dropped on second-hop detail/library/compare routes; Find/Grow job-kind variable shadowing;
correction-only subject rejection; long planner input dropping appended corrections; overly broad negation
exception. Regression tests and affected browser journeys were rerun. No open material source-review finding.

Live curation/provider/model results and source permissions are reported separately in CURATION.md. Offline,
mock and actual network/model checks are deliberately not conflated.

## Starter and compatibility

- Final fresh import: 93; second import: 0. Credits matched every attribution/source/license/restriction entry
  (local image IDs normalized for comparison). Schema remains 2; SQLite integrity check passed.
- Upgrade from the original 85-reference pack added 8, retained a deliberately saved personal correction,
  and a further import added 0. All test homes were disposable system-temp directories.
- Root inspected all nine candidate images; independent review excluded the weaker broken-candle metaphor,
  leaving eight additions. No material rights/provenance findings; corrected an Alice source-link extension.
- Image pages retain roles/model attribution/review states but no longer display model confidence as a
  percentage. A required stored qualitative score is not presented as a probability of correctness.
- Read-only demo browser journey passed operation/domain navigation, expansion, two-image compare and exact
  context return with zero broken images/console errors; final demo rebuilt from the 93-reference pack.

## Local distributable

`release/VisualAtlas-v0.4.0.zip` was built from the working tree with freshly compiled assets. Every included
file was compared byte-for-byte with its source; the HTML's generated asset references resolve. A first archive
check caught PowerShell 5 adding carriage returns to piped paths, defeating export exclusions. Argument batches
fixed this, and the rebuilt archive excludes screenshots, dependencies, local libraries and secrets.

The actual Windows installer ran in an extracted system-temp folder with `-NoShortcuts -NoLaunch`, using a
separate temporary library. It installed version 0.4.0, imported 93 images, retained schema 2, and a repeat import
added zero. Playwright then used the extracted app server: all five contextual-incongruity examples appeared;
Titan's Goblet displayed the correct proposed reading and evidence, with zero broken images/console errors.
The first-run welcome was dismissed normally. Test-driver waits were corrected to allow its asynchronous
navigation to finish. The final mobile demo image page also showed proposed status, credit/checking evidence,
no percentage-confidence claim, no horizontal overflow and no broken images.

Spec Kit convergence: 10 functional requirements, 4 acceptance criteria, 5 plan steps and 6 constitutional
principles assessed; no actionable implementation gaps remained. Documented coverage/model-access limitations
are not claimed as completed targets. No remote release, push or deployment occurred during that local build.

## Documentation and authorized branch push (2026-10-16)

The owner's follow-up authorized a commit and push. Commit `9aaafa1` on `visual-atlas-v0.4` includes the
implementation, rewritten README and detailed user guide. Main was not updated because its push workflow
deploys the public demo. No release tag or public release was created.

[CI run 38871909266](https://github.com/WilliamEbong/visual-atlas/actions/runs/38871909266) passed on Linux
and Windows: 372 backend tests on each platform, 15 frontend tests, TypeScript, Ruff, production builds,
Windows scratch installation, dependency audits and secret scanning. Nine live tests were deselected.

Independent source review corrected three documentation claims: collections contain reference images,
the library button says “Show the next …”, and image removal retains audit history. All 49 local README
and guide links, anchors and image references resolve. Playwright inspected the rendered GitHub pages,
including loaded README screenshots, guide contents and a readable 375px layout without page overflow.
GitHub's global-navigation payload returned 404; the documents and their images loaded successfully.

The local zip includes the revised documents. All 473 archived source files match the working source;
247 runtime files remain byte-identical to the previously installed and tested copy. The current receipt
is `release/verification.json`. No live model checks were repeated for this documentation-only follow-up.
