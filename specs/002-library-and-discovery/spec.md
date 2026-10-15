# Spec 002 — Library, discovery and corrections

## Overview
Everything a person does with the library day to day, plus discovery across all enabled sources:
Find images (natural language and guided choices), Grow my library (fill technique gaps), browse with
search, sort and filters, correct annotations, favourites, collections, comparison, removal, credits.

## Functional requirements
- FR-1 Five connectors (AIC, Met v1.1, Cleveland, Smithsonian, Wikimedia Commons) with per-item
  licence rules in code; disabled providers documented with evidence and no connector built.
- FR-2 Cheap filters before any AI: tombstones, earlier rejections, eligibility, exact and near
  duplicates (dHash distance ≤ 6), quality (size, proportions, tonal variation), optional
  orientation and colour.
- FR-3 Find: description, subject, technique, goal, orientation, colour, intended use, quantity,
  sources and assistant. Grow: techniques with the fewest examples, curated search hints, no AI plan.
- FR-4 Job progress shows Searching → Checking permissions → Analyzing → Ready, counts, added
  images, skipped items with plain reasons, and pause/resume/cancel; jobs survive restarts.
- FR-5 One picture's AI error retries that picture; a verifier error leaves the proposal unverified;
  usage limits pause the job with a plain message.
- FR-6 Library: full-text search, filters (technique, goal, shape, source, review state, colour,
  favourites, collection), eight sorts, keyboard grid navigation, load more.
- FR-7 Image page: what you can see, why it may work (evidence, effect, state, proposer, checker),
  related images, usage and credits, history, confirm/reject/edit/add technique, favourite, save to
  collection, compare, and remove with confirmation (tombstoned).
- FR-8 Collections: create, rename, describe, add/remove, reorder, export a zip with credits.
- FR-9 Compare two to four images side by side with shared techniques and an optional saved AI
  comparison.

## Success criteria
Offline tests for each rule (eligibility, filters, duplicates, jobs, corrections, collections) pass;
Playwright exercises find/progress/cancel, filters, corrections, collections and comparison.
