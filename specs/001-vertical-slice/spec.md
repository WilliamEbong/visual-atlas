# Spec 001 — Vertical slice: find, ingest, analyse, show, follow, persist

## Overview
Prove the whole Visual Atlas path on real data before building breadth: a person asks for
images, the app searches one eligible open-access provider, checks the licence in code, downloads
and validates the actual image with full provenance, sends the actual pixels to a live AI backend,
validates and saves the annotation, shows the image and explanation, lets the person follow a
technique to related techniques and their images, searches again, and keeps everything after a
restart.

## Functional requirements
- FR-1 Store: SQLite database in the data home (`VISUAL_ATLAS_HOME`, default
  `%USERPROFILE%\VisualAtlas`), numbered migrations, WAL, append-only triggers on rights records,
  analyses, annotation history, attempts and tombstones. The home may not be inside the repository
  or a OneDrive folder.
- FR-2 Taxonomy as data: `atlas/data/taxonomy.json` holds goals, operations, domains and at least
  6 fully written techniques (every field present; sources or `working_definition: true`). Sync
  into the database fails on any dangling reference.
- FR-3 Source policy as data: `atlas/data/source_policies.json` records each provider's status,
  host allowlist, accepted licences, attribution text, storage/display mode, evidence URLs and
  check date.
- FR-4 Eligibility in code: the Art Institute of Chicago rule accepts only `is_public_domain ==
  true` with an `image_id`; anything missing is ineligible with a reason. AI never decides rights.
- FR-5 Safe download: https only, provider host allowlist, private/loopback/link-local addresses
  rejected after DNS resolution, at most 3 redirects each re-checked, 25 MB cap, image content type,
  Pillow decode with a pixel cap. Files are content-addressed by SHA-256.
- FR-6 Rights record per image: source URL, provider item ID, creator, title, exact licence and
  version, licence URL, evidence URL, retrieval and verification timestamps, required attribution,
  restrictions, permitted storage/display mode, file SHA-256 and provenance JSON.
- FR-7 Metrics: width, height, aspect ratio, orientation, dominant palette, mean luminance,
  contrast, colourfulness and a 64-bit dHash, computed without AI.
- FR-8 Analysis: a job sends a ≤1024 px re-encoded copy (metadata stripped) to the selected backend
  (Codex or Claude Code CLI, tools off). Output must match the analysis schema: observations with
  ids, techniques citing observation ids, hedged effects, confidence 0–1, summary, and
  `creator_intent` only when a supplied metadata field backs it. Invalid output is rejected and
  never saved.
- FR-9 Job: "Find images" creates a persistent job with items; a worker claims it with a lease,
  runs search → permission check → download → analysis → save, and records per-item state and
  reason. States shown: Searching, Checking permissions, Analyzing, Ready.
- FR-10 UI: library grid of accepted images; image page with What you can see, Why it may work,
  Techniques (linking to the technique page), Usage & credits; technique page with definition,
  related techniques and their images; a search box over titles, creators, observations and
  technique names.
- FR-11 Persistence: after stopping and restarting the server, the library, annotations and job
  history are unchanged.

## User scenarios
1. "Find images showing negative space" → job runs live → ≥3 real AIC images appear with credits.
2. Open an image → read observations and why it may work → click a technique → see the
   definition, a related technique and its images.
3. Search "lighthouse" (or a technique name) → matching images listed.
4. Restart the app → same images, annotations and job record.

## Success criteria
- A live job adds at least 3 images with complete rights records and validated annotations.
- Unit tests cover store persistence and append-only rules, AIC eligibility (pass and each failure
  reason), downloader rejections, analysis validation (unknown id, dangling evidence, extra keys,
  invented intent) and job resume after interruption.
- Playwright walk-through of scenarios 1–4 with screenshots and no uncaught console errors.
