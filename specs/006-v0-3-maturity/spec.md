# Spec 006 — Visual Atlas v0.3: maturity and the archive-of-looking redesign

Package version 0.3.0. The owner chose the scope on 2026-10-15: polish and finish; a visual redesign that pushes
the archive-of-looking style (design canvas: https://claude.ai/artifact/XLoCPcCUxu11FpCyK8AWd9); and the deferred
features except uploads (new sources, better request coding, metadata classification). The build runs
autonomously. v0.2.0 is published; v0.3.0 is built and verified locally and is published only on the owner's
go-ahead.

## Overview
Make the app feel finished and look like the archive it is: the pictures lead, every screen says what is
happening, mistakes can be undone, and the keyboard and a screen reader can do everything a mouse can. Widen
where it finds images with four more open collections, each admitted only under a mechanical rights rule.
Understand briefs written in ordinary words, and stop spending analyses on documentation photos, but only where
a pre-registered evaluation supports it.

Out of scope: uploading your own images, a macOS or Linux installer, libraries far beyond the current size,
a new graph or vector store, taxonomy expansion beyond cue phrases and search hints, publishing v0.3.0
without the owner's go-ahead.

## Working principles (recorded before implementation)
1. **What a practitioner would check beyond the features:** that every state a screen can be in (loading,
   empty, failed, busy) is designed, not just the happy path; that an action can be undone or is confirmed
   with its consequences named; that a keyboard and a screen reader reach every control; that layout does not
   jump as images load; that a new source's licence rule rests on the source's own field, not a guess.
2. **Raw evidence to start from:** the v0.2.0 screens and their screenshots, the design canvas, each source's
   official API documentation and live records, the v1.1 evaluation briefs and cases, the v0.2.0 published zip
   for upgrade runs.
3. **Methods and tools that establish correctness:** unit tests for rights rules and connectors on saved
   fixtures; a source-code test that no browser alert or confirm remains; Playwright journeys at desktop and
   375 px; axe-core accessibility scans in the browser; layout-shift measurement with PerformanceObserver;
   frozen evaluation splits with metrics fixed before the final run.
4. **Evidence independent of the builder's opinion:** axe and layout-shift numbers, live source smoke results,
   a fresh final holdout written and coded before any final run, installs and upgrades from the published
   v0.2.0 artifact, and an independent review.

## User scenarios
- **US1 (P1) Every screen says what is happening.** While data loads, the screen shows its shape; when there is
  nothing, it says why and offers the next step; when something fails, it says what and how to retry; when the
  library is busy (restore), it says so. Nothing shows a blank page or a browser alert.
- **US2 (P1) Mistakes are recoverable.** Removing an image from a collection, dismissing a direction or
  unstarring shows a notice with Undo. Removing an image from the library, deleting a brief or collection, and
  restoring a backup ask first in the app, naming what will be lost.
- **US3 (P1) The pictures lead.** The library opens on a grid where every image keeps its proportions, captioned
  like a plate. An image page marks on the picture where each observation is, beside why it may work and how it
  may be used.
- **US4 (P2) Keyboard and screen reader.** Every journey works by keyboard alone, with visible focus, a skip
  link, named landmarks, dialogs that hold and return focus, and announcements for notices and job progress.
- **US5 (P2) More places to look.** Find can search the Rijksmuseum, the National Gallery of Art, the Library of
  Congress and NASA, each admitted only where its own records state a permission the app accepts.
- **US6 (P2) Briefs in ordinary words are understood.** "Backlit figures against a pale sky" is read as
  silhouette even though the word "silhouette" never appears.
- **US7 (P3) Fewer wasted analyses.** Candidates that are plainly documentation photographs or pages of text are
  skipped before download, with the reason shown, when the evaluation supports it.
- **US8 (P2) Settings are easy to scan.** Settings are grouped into sections with plain status for assistants,
  sources (with each source's rule), project help, backups and appearance.

## Functional requirements
### Visual system and screens
- FR-1 Design tokens (colour, type, spacing, rules) are defined once as CSS custom properties with light and dark
  values, matching the canvas palette and type (Perpetua/Cormorant Garamond display, Franklin Gothic/Libre
  Franklin text, Consolas/IBM Plex Mono captions). Square corners, keylines, no drop shadows.
- FR-2 The horizon: every top-level page has a 1 px rule at the same distance from the top of the page
  (desktop) with the page title standing on it; content starts below it. Library and technique pages stand
  specimen windows or the aperture lens on the rule. At phone widths the rule sits higher, still the same on
  every page.
- FR-3 Library: a justified grid in which each image's width is proportional to its aspect ratio within a row;
  plate captions (figure number, review state, title, creator and date, techniques); space reserved before images
  load; search, technique, goal and sort always visible, other filters in a "More filters" panel; the active
  filters listed with remove buttons and "Clear all"; the four ways in as catalogue drawers.
- FR-4 Image page: a large image with observation regions drawn on it when the analysis has regions, linked
  both ways with the observation list; three sections (what you can see, why it may work, usage and credits);
  previous and next within the current results, also by the arrow keys; related images by technique; history.
- FR-5 Technique page: the aperture lens showing an example, the definition, four trays (how to spot it, when it
  helps, easily confused with, limits), examples in the library, nearby techniques and goals.
- FR-6 Find: a field-note form with a live "read as" preview of the request coding, guided fields and source
  choices; job progress as a four-step timeline with counts and each item's outcome.
- FR-7 My project: the brief as a slip, the reading as trays, directions under coloured rules with their cited
  thumbnails, and a prompt to find more when the evidence is thin.
- FR-8 Compare: images standing on one baseline; a technique matrix with state marks; palette strips; the saved
  comparison.
- FR-9 Collections: drawers with contact strips, image counts and export or copy credits.
- FR-10 Settings: sections with in-page navigation; the sources table shows each source's rule from the policy
  data.
- FR-11 Phone widths (≤ 600 px): one column, a menu button for navigation, the image page's sections stacked in reading order, and no
  horizontal scrolling at 375 px.

### Polish
- FR-12 No `window.alert`, `window.confirm` or `window.prompt` remains in the web app. Reversible actions show a
  notice with Undo (polite live region, about 8 s, paused while hovered or focused). Irreversible actions use an
  in-app dialog that names the consequences.
- FR-13 Every data view uses shared loading, empty, error and busy states. The busy state appears when the API
  answers 503 during maintenance.
- FR-14 Accessibility: skip link, landmarks, visible focus, focus trapped in and returned from dialogs, Escape
  closes them, labelled controls, announcements for notices and job progress, and targets of at least 44 px for
  primary controls. The main screens have no serious or critical axe-core violations.
- FR-15 Large libraries: images lazy-load with their space reserved; cumulative layout shift on the library's
  first load stays below 0.05.

### Sources
- FR-16 Each new source (Rijksmuseum, National Gallery of Art, Library of Congress, NASA) either has a connector
  with fixture tests, a rights rule in `atlas/rights.py` with passing and failing tests, and a policy entry with
  evidence URLs and the date checked; or is recorded as disabled with the reason and evidence. No rule accepts an
  image on the strength of free text an assistant interprets.
- FR-17 Techniques gain search hints for the new sources, as data.
- FR-18 Each enabled new source passes a live smoke test (marked `live`), reported as live-tested,
  fixture-tested, unavailable or blocked.

### Request coding
- FR-19 Techniques and goals gain descriptive cue phrases in the taxonomy data, and the coder matches them,
  with word-boundary and stopword fixes ("against", "flyer").
- FR-20 Evaluation: the v1.1 briefs become the development set; a fresh final holdout of at least 16 briefs is
  written and coded before any final run. The cues are adopted if, on the development set, micro-F1 rises by at
  least 0.10 with precision at least 0.60 and retrieval recall@20 not lower. The final holdout is run once and
  reported, never used to tune.

### Metadata classification
- FR-21 A deterministic pre-download filter for documentation photographs and text pages, with its rules in data,
  and the optional Jev arm, are evaluated on a case set with at least 10 negative cases. An arm is integrated only
  if no positive case is skipped and at least half of the negatives are. With fewer than 10 negatives the outcome
  is "deferred". A skipped candidate shows the matched rule, and the filter can be switched off in Settings.

### Release
- FR-22 Version 0.3.0, a migration only if the schema changes, and updated README, guide, quick-start and
  screenshots.
- FR-23 A fresh install and an upgrade from the published v0.2.0 zip are verified in scratch homes; the release
  zip is built locally from the final commit.
- FR-24 An independent review in at most 2 rounds; findings are fixed with tests or rejected with evidence.

## Success criteria
- SC-1 The web source has no `window.alert`, `confirm` or `prompt` (enforced by a test); the main screens show 0
  serious or critical axe-core violations.
- SC-2 Library first-load cumulative layout shift is below 0.05; no screen scrolls horizontally at 375 px.
- SC-3 Every new source is either accepted (rule, tests, live smoke) or disabled with evidence.
- SC-4 Coding and metadata-filter decisions follow the rules fixed in FR-20 and FR-21, with dev and final
  results reported separately with intervals.
- SC-5 All offline tests and web checks pass; fresh install and upgrade from v0.2.0 pass.

## Edge cases
- A library with no images, filters matching nothing, an analysis without regions, a technique with no
  examples, a brief with no matching evidence, a source that is down or rate-limited, a candidate whose rights
  field is missing, dark mode, a 375 px screen, reduced motion.
