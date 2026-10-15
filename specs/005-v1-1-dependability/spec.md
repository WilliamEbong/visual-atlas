# Spec 005 — Visual Atlas v1.1: dependability, grounding and evaluation

Package version 0.2.0 ("v1.1" is the product iteration name; the repository uses 0.x semantic versions and
v-prefixed tags, and this iteration adds behaviour and a schema migration, so the minor number moves).

## Overview
Make the existing app deeper and more dependable without widening its scope: no acknowledged write is ever
lost, jobs say exactly what happened and resume cleanly, annotation state is coherent across re-analysis,
project help and discovery are relevant and grounded in real library evidence, and quality claims rest on a
reproducible evaluation instead of the builder's opinion. Out of scope: new providers, manual upload, plugin
architecture, vector database, broad redesign, taxonomy expansion.

## Working principles (recorded before implementation)
1. **What a practitioner would check beyond the features:** that an acknowledged edit survives every
   maintenance operation and crash; that "checked" means a saved second reading; that the labels on an image
   are the ones its current evidence supports; that "relevant" and "grounded" are measured against cases
   written down before results are seen; that efficiency counts calls per useful result, not calls.
2. **Raw evidence to start from:** reproductions of every review finding against commit 680b199
   (`docs/evaluation/v1.1/repro-before.json`), the real and starter library databases (read-only), provider
   records and image hashes, job and attempt histories, saved model outputs, and measured browser journeys.
3. **Methods and tools that establish correctness:** deterministic interleaving tests (hooks at the exact
   step, no sleeps) for coordination; property-style checks on annotation state after repeated re-analysis;
   schema and relationship validation of model outputs; frozen evaluation splits with fixed metrics;
   Playwright MCP journeys; fresh-install and upgrade runs from the v0.1.0 artifact in scratch homes.
4. **Evidence independent of the builder's opinion:** the reproductions flipping from failing to passing;
   counts from the database and attempt ledger; a final holdout frozen (cases, reference judgments, prompts,
   model ids, metrics) before any final run; second-model results reported separately and never relabelled
   as human review; installs and upgrades performed from the published artifact.

## User scenarios
- **US1 (P1) Restoring never loses work.** Given a person adds a collection while a restore runs (from the app,
  a terminal or a second window), the change is either refused with a clear "restoring" message or kept; it is
  never acknowledged and then lost. A failed or interrupted restore leaves a working library.
- **US2 (P1) A second window cannot damage a running job.** Starting another app or server while a job
  downloads never deletes that job's files; abandoned files are still cleaned up later.
- **US3 (P1) Checking is reported honestly.** When the checking assistant is over its limit, times out or
  answers badly, the job and image say so, the check can be resumed, and only a saved second reading counts.
- **US4 (P1) Re-analysis keeps labels coherent.** After an image is analysed again, its active labels are
  exactly the current analysis's labels plus the person's own decisions; older model labels stay in the history
  marked as superseded; any number of proposals can be checked.
- **US5 (P2) Project help cites real, relevant evidence.** Directions for a brief draw on the references most
  relevant to it (not the newest), cite images that actually carry the cited techniques, and say plainly when
  the library lacks good evidence. The app shows how it read the brief.
- **US6 (P2) Discovery reports whether it found what was asked.** A Find or Grow job reports how many added
  images show the requested technique or fill the targeted gap, separately from other additions, and why it
  stopped (target reached, budget, or no more results).
- **US7 (P3) Browsing large libraries stays fast and complete.** "Show more" fetches only the next page, never
  repeats or skips images, and stale answers never replace newer ones.
- **US8 (P2) Quality claims are reproducible.** A reviewer can rerun the evaluation, see development and final
  results separately, and see which judgments are provisional.

## Functional requirements
### Data preservation and recovery
- FR-1 One library-wide maintenance mode, recorded in the library database and backed by an operating-system
  file lock in the data home, covers restore and media cleanup. Entering it is atomic with a check that no job
  holds a live lease or is queued to run.
- FR-2 Every database write transaction (API, background worker, CLI, any process) refuses to commit while
  another holder's maintenance mode is on; the API answers 503 with a plain message; workers stop and resume
  later without marking items failed. A marker whose holder no longer holds the file lock is stale and is
  cleared automatically.
- FR-3 Restore validates the archive and staged database (older backup versions are migrated in the staging
  copy first) before anything changes, then makes the safety backup, copies media additively, and replaces the
  database contents in one atomic SQLite backup step. A failure at any point leaves either the previous or the
  restored library, never a missing or empty one, and maintenance is always released.
- FR-4 New media files are written only after their image row commits; a resumed job rewrites missing files.
  Media cleanup runs only under maintenance and never while a job holds a live lease.
### Truthful, resumable jobs
- FR-5 A second-model check returns an explicit outcome: checked, nothing to check, unavailable (not installed,
  signed out, over a limit), invalid answer, retryable error, or cancelled. Only a saved check counts as checked.
- FR-6 In Find/Grow/Analyse, an optional check that fails never discards the added image; the item and job
  summary report how many images were checked and why others were not. A Verify job retries or pauses as
  appropriate and finishes with an accurate count; pausing reasons pause it, retryable errors retry it with a
  bound, invalid answers fail only that image after retries.
- FR-7 A provider's Retry-After (seconds or HTTP date) delays that item and every pending network step for the
  same provider in the job (persisted), and the fetcher refuses further requests to that provider during the
  cooldown without sleeping. Malformed values fall back to normal back-off; very long delays are capped and
  reported.
- FR-8 Default budgets scale with the requested number so the maximum request is achievable; explicit budgets
  are kept. A job that stops because a budget ran out says so, distinctly from "the searches ran out".
### Coherent annotations
- FR-9 Applying an analysis supersedes every unlocked model label the analysis omits (including after an
  empty or unusable result); superseded labels leave a history entry and stop being active. Human-confirmed,
  human-rejected and human-edited labels always survive. Image status follows its remaining active labels.
- FR-10 Verification judges any number of unchecked proposals in batches no larger than the verifier
  contract, persisting each batch; an interrupted check resumes with the proposals not yet judged.
- FR-11 Upgrading a library reconciles labels left over from earlier analyses the same way, with history.
### Relevant, grounded help
- FR-12 Request coding: a deterministic coder reads a brief or Find request against the taxonomy codebook
  (technique and goal names, aliases, cues) and the guided fields, producing techniques, goals, subject terms
  and constraints, each with the words that triggered it. No AI is called.
- FR-13 Directions retrieve a bounded, relevance-ranked set of references (coded techniques and goals carried
  by the image's active labels, weighted by review state, plus full-text subject matches; ties by recency) and
  send complete records within a measured size budget. The model may cite only supplied ids.
- FR-14 Every saved direction cites at least one supplied image and one technique, and each cited image
  carries at least one of the direction's cited techniques. Directions that fail are dropped; one to five valid
  directions are allowed; with none, the job finishes with an insufficient-evidence message that suggests what
  to find. The project page shows how the brief was read.
- FR-15 Find/Grow mark each added image as matching or not matching the requested techniques (explicit
  techniques, Grow gap techniques, or techniques the coder found with an exact name or alias match). Targets
  count matching additions when such techniques exist; other additions are kept and reported separately.
  Strict filters (sources, shape, colour, licence) are applied before any AI call.
- FR-16 Automatic "no clear technique" rejections are recorded separately from a person's removals, with the
  analysis version that made them. A person's removal is never reconsidered; an automatic rejection is
  reconsidered only when the analysis version changes.
### Usability and performance
- FR-17 The library loads in pages using offsets with a deterministic order (every sort ends with the image
  id), resets on filter or sort change, ignores stale responses and keeps keyboard navigation.
### Evaluation
- FR-18 The v1 evaluation stays intact with a note that its second round reused the development images and that
  its labels are builder judgment. A new pack has development and final-holdout splits, each case traceable to
  source record and image hash, with reference techniques, acceptable alternatives, uncertainty and notes,
  explicitly marked provisional. The final split, prompts, model ids and metrics are frozen (hashed) before the
  final run, and the final run is not used for tuning.
- FR-19 Metrics: proposal precision and recall against the reference (alternatives count as acceptable), false
  positives on no-technique cases, checker false acceptance and false rejection, abstention, invalid outputs,
  latency, and calls per useful result. An independent-first checker is compared with the current checker on
  the development split and adopted only with a measured benefit worth its cost.
- FR-20 Request-coding and retrieval evaluation on frozen briefs (no AI for retrieval): recall of relevant
  references within the prompt budget, recency baseline vs relevance ranking.
- FR-21 TypeSafe Jev decision gate with criteria fixed before any run, per use (request coding, metadata
  classification, annotation review): integrate only with a meaningful, repeatable measured benefit. If
  integrated it is optional, off by default, bring-your-own key from the user's own data-home `.env`, text-only
  unless separately enabled, with bounded calls and full provenance; it never touches rights or review states.
  Without owner approval to use a key, the harness and criteria ship and the live run is recorded as deferred.
### Honesty and release
- FR-22 README, quick start, guide, welcome and settings describe remote AI processing accurately: the library
  is local; analysis uses the person's Claude Code or Codex account and sends images and text to that service.
- FR-23 Release packaging runs only after the full checks pass on the same commit, including a Windows job.

## Success criteria
- SC-1 Every reproduction in `repro-before.json` passes against the new code (`repro-after.json`), and each has
  a deterministic regression test.
- SC-2 Full offline checks, data guard and dependency audits pass; Playwright covers the journeys listed in the
  plan; fresh install and upgrade from the v0.1.0 artifact keep starter data, collections, annotations,
  tombstones, backups, and restore of a v0.1.0 backup works.
- SC-3 Retrieval: on the frozen brief set, relevance ranking finds more relevant references within the budget
  than the recency baseline, with numbers reported.
- SC-4 The evaluation pack reports development and final results separately with the stated limits.
