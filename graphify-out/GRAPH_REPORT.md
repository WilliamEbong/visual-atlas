# Graph Report - .  (2026-11-23)

## Corpus Check
- 142 files · ~139,373 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1498 nodes · 3884 edges · 84 communities (77 shown, 7 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 283 edges (avg confidence: 0.76)
- Token cost: 358,024 input · 0 output

## Community Hubs (Navigation)
- Job worker and leases
- Claude Code adapter
- Reference desk engine
- Library store records
- Job tests and leases
- Image checks and hashing
- Command line
- Collections and projects UI
- Brief coding and job creation
- Compare and job progress UI
- Knowledge sync and analysis
- Backup and restore
- Second-model checks
- National Gallery open data
- AI result validation
- Connections map
- Library page
- Desktop launcher
- Local web server
- App shell and Find
- Taxonomy and policy checks
- Evaluation harness v1.1
- Test helpers
- Rights decisions
- Collection providers
- Credits and portable archives
- Network fetch errors
- CI and release workflows
- Request coding
- Safe downloader
- Desk review regressions
- Generated and design-system layers
- Desk tests
- Ask and Explore UI
- AI task schemas
- Agent rules and invariants
- Market research
- Licence rules per provider
- Server app and demo build
- Jev ranking
- test_store.py
- fake.py
- Path
- eval_v03.py
- jev.py
- catalog.py
- mcp_server.py
- Ask.tsx
- ImagePage.tsx
- Remove an image, its files and annotatio
- generate_images.py
- Backups and verified restore
- test_mcp.py
- test_server.py
- Metadata filter not integrated
- TypeSafe Jev decision gate
- analyze_prompt()
- Gaps: designers, agents, licence and pro
- Plan 008 Reference desk
- analyze_schema()
- Commit guard for design-system files (ch
- Product thesis (2026-11-22)
- Plan 003 Explore, connections and projec
- Plan 004 Install, release, demo and docu
- eval_r2.py
- Plan 007 Visual reasoning
- Visual Atlas starter credits
- Rights decided only by rights.py; unclea
- demo.ts
- credits()
- mcp()
- make_tour.py
- Tasks 002 Library, discovery and correct
- conftest.py
- __init__.py
- Web app HTML entry (index.html)
- noalert.test.ts
- visual-atlas

## God Nodes (most connected - your core abstractions)
1. `open_store()` - 104 edges
2. `Store` - 92 edges
3. `Worker` - 87 edges
4. `store()` - 84 edges
5. `BackendError` - 40 edges
6. `load()` - 38 edges
7. `useData()` - 38 edges
8. `Fetcher` - 37 edges
9. `FetchError` - 35 edges
10. `href()` - 31 edges

## Surprising Connections (you probably didn't know these)
- `AGENTS.md agent entrypoint` --semantically_similar_to--> `CLAUDE.md agent entrypoint`  [INFERRED] [semantically similar]
  AGENTS.md → CLAUDE.md
- `search_open_collections MCP tool (only online tool)` --semantically_similar_to--> `open-museum-mcp`  [INFERRED] [semantically similar]
  OVERNIGHT-CHANGES.md → docs/research/01-landscape.md
- `similar_references / More like this` --conceptually_related_to--> `Visual similarity is commodity`  [AMBIGUOUS]
  OVERNIGHT-CHANGES.md → docs/research/01-landscape.md
- `Jev` --uses--> `BackendError`  [INFERRED]
  scripts/eval_v11.py → atlas/ai/process.py
- `timed()` --indirect_call--> `BackendError`  [INFERRED]
  scripts/eval_v11.py → atlas/ai/process.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Reference desk behind CLI, MCP and Ask page** — docs_research_05_thesis_reference_desk, atlas_mcp_server, readme_ask_page, docs_user_guide_mcp_tools [EXTRACTED 1.00]
- **Three candidate product theses** — docs_research_04_synthesis_thesis_a, docs_research_04_synthesis_thesis_b, docs_research_04_synthesis_thesis_c [EXTRACTED 1.00]
- **CI, release packaging and Pages demo pipeline** — _github_workflows_ci, _github_workflows_release, _github_workflows_pages, build_state_publish_like_qualia [INFERRED 0.85]
- **One desk engine served by CLI, MCP and Ask page** — specs_008_reference_desk_spec_desk_engine, specs_008_reference_desk_spec_mcp_server, specs_008_reference_desk_spec_ask_page, specs_008_reference_desk_plan_layers [EXTRACTED 1.00]
- **v1.1 data preservation flow** — specs_005_v1_1_dependability_spec_maintenance_mode, specs_005_v1_1_dependability_plan_atomic_restore, specs_004_release_and_docs_spec_backups_restore [INFERRED 0.85]
- **Brief reading and grounded help** — specs_005_v1_1_dependability_spec_request_coding, specs_006_v0_3_maturity_spec_request_cues, specs_005_v1_1_dependability_plan_retrieve_for_brief, specs_003_connections_and_projects_spec_directions_job [INFERRED 0.85]

## Communities (84 total, 7 thin omitted)

### Community 0 - "Job worker and leases"
Cohesion: 0.06
Nodes (26): Continue unfinished jobs. Safe alongside the app: a lease stops two workers shar, worker(), backend_message(), db_path(), fit_records(), Path, Whole records, in order, while they fit the prompt budget (never a record cut in, Images this job has sent for analysis (second-model checks are not counted again (+18 more)

### Community 1 - "Claude Code adapter"
Cohesion: 0.10
Nodes (46): build_argv(), check(), _environment(), message(), Path, Claude Code CLI adapter: the user's own subscription, no tools, images as base64, Native claude.exe; never a .cmd/.ps1 shim, so prompts never pass through a shell, Return the CLI version after confirming a claude.ai subscription sign-in. Cached (+38 more)

### Community 2 - "Reference desk engine"
Cohesion: 0.09
Nodes (47): advise(), _candidates(), _clean_list(), _codebook(), directions(), _fetcher_for(), get(), guidance() (+39 more)

### Community 3 - "Library store records"
Cohesion: 0.12
Nodes (14): canonical(), now(), Rewrite one image's search row from its metadata, observations and technique nam, Forget an image: files are deleted by the caller after this commits; a tombstone, Bring back an image that an older analysis version rejected automatically, for a, Add one reference exported from another library (the starter pack), keeping its, Make `analysis_id` the image's current analysis. Its techniques become the activ, A second model agreeing promotes proposed -> model_reviewed; disagreement is not (+6 more)

### Community 4 - "Job tests and leases"
Cohesion: 0.13
Nodes (38): LeaseLost, Another worker took over the job; the current worker must stop writing., RuntimeError, find(), Flaky, held_worker(), Jobs: discovery end to end (offline), leases, interruption and resume, cancel/pa, A backend that behaves like the practice backend but can fail on chosen calls. (+30 more)

### Community 5 - "Image checks and hashing"
Cohesion: 0.11
Nodes (34): color_name(), delete_files(), dhash(), hamming(), ImageRejected, _jpeg(), metrics(), open_checked() (+26 more)

### Community 6 - "Command line"
Cohesion: 0.08
Nodes (35): advise(), backup(), coverage(), directions(), doctor(), find(), grow(), job() (+27 more)

### Community 7 - "Collections and projects UI"
Cohesion: 0.14
Nodes (30): MoreLikeThis(), SampleAnswer(), CollectionPage(), Collections(), Source, SaveToCollection(), BriefForm(), BriefPage() (+22 more)

### Community 8 - "Brief coding and job creation"
Cohesion: 0.09
Nodes (32): coverage(), Techniques ordered by how few non-rejected examples they have (fewest first)., code_request(), Cheap, correctable suggestions. Negative clauses veto inferred tags; explicit ch, create_job(), Validate a job request (from the UI, CLI or another agent) and queue it., The library references most relevant to a coded request, as complete records wit, relevant_references() (+24 more)

### Community 9 - "Compare and job progress UI"
Cohesion: 0.10
Nodes (27): MARK, Saved, ACTIVE, JobProgress(), KIND, ORDER, OUTCOME, SKIP_LABELS (+19 more)

### Community 10 - "Knowledge sync and analysis"
Cohesion: 0.11
Nodes (29): Reload the knowledge files into the database when they changed. Returns True if, sync(), analyze(), _queue(), Reload the knowledge files into the library database now., Analyse (or re-analyse) images. A person's corrections are never overwritten., taxonomy_sync(), _work() (+21 more)

### Community 11 - "Backup and restore"
Cohesion: 0.17
Nodes (29): backup(), _copy_media(), _file_info(), list_backups(), Path, Back up the library. allow_missing (used only for the safety copy before a resto, Replace the library with a backup without ever losing an acknowledged change., Add the backup's media files; content-addressed names make this safe for the cur (+21 more)

### Community 12 - "Second-model checks"
Cohesion: 0.16
Nodes (26): analysis(), crash_once(), fast_clock(), library(), outcome(), proposals(), Second-model checks report what really happened, and re-analysis keeps an image', A checking assistant that fails in a chosen way (or answers like the practice ba (+18 more)

### Community 13 - "National Gallery open data"
Cohesion: 0.16
Nodes (27): build(), folder(), _index_rows(), load(), Path, The National Gallery of Art publishes its collection as CC0 open data (CSV files, Rows containing every query word first, then rows containing most of them., CSV rows, after checking the file still has the columns this index reads (a chan (+19 more)

### Community 14 - "AI result validation"
Cohesion: 0.13
Nodes (26): evidence_texts(), InvalidResult, _parse(), ValueError, Reject invented ids, dangling evidence, unbacked intent, links and markup., technique_id -> the observation texts it cites (stored with the annotation)., The model answered, but the answer broke the contract. Never saved., Keep only grounded directions: known techniques, and at least one supplied image (+18 more)

### Community 15 - "Connections map"
Cohesion: 0.11
Nodes (23): Connections(), KIND, RELATION, adjacency(), layout(), Positioned, route(), graph (+15 more)

### Community 16 - "Library page"
Cohesion: 0.21
Nodes (23): COLORS, HERO, Library(), LibraryPage, plateState(), STATES, activeCount(), activeFilters() (+15 more)

### Community 17 - "Desktop launcher"
Cohesion: 0.15
Nodes (21): _default_browser(), find_browser(), main(), _notify(), _open(), _probe(), Double-click entry point: Visual Atlas in its own browser app window; it stops o, chrome' or 'edge' when that is the Windows default browser, else None. (+13 more)

### Community 18 - "Local web server"
Cohesion: 0.14
Nodes (19): AnnotationInput, BriefInput, CollectionInput, JobRequest, MembershipInput, BaseModel, Local API + bundled web app. Loopback only, per-launch token, Host/Origin checks, StateInput (+11 more)

### Community 19 - "App shell and Find"
Cohesion: 0.15
Nodes (19): App(), NAV, readCompare(), TOOLS, GoalChoice(), Compare(), ASSISTANTS, COLORS (+11 more)

### Community 20 - "Taxonomy and policy checks"
Cohesion: 0.12
Nodes (21): check(), load(), Path, Cross-reference checks that the schema cannot express., Return (taxonomy, policies, taxonomy_sha, policies_sha); raise ValueError listin, _sha(), Validate atlas/data/taxonomy.json and source_policies.json., taxonomy_check() (+13 more)

### Community 21 - "Evaluation harness v1.1"
Cohesion: 0.18
Nodes (22): excluded(), fetch(), fmt(), freeze(), frozen_parts(), jev_decisions(), load_cases(), mean() (+14 more)

### Community 22 - "Test helpers"
Cohesion: 0.14
Nodes (21): aic_fetcher(), jpeg(), public_resolver(), Shared offline test helpers: a data home, fake provider HTTP, distinct test JPEG, A distinct, high-contrast picture per seed (so dHash never calls two of them dup, Fetcher whose AIC search returns the recorded fixture and whose IIIF images are, client_for(), find() (+13 more)

### Community 23 - "Rights decisions"
Cohesion: 0.15
Nodes (20): policy(), check(), _host_ok(), Eligibility for one candidate under its provider policy. Missing evidence is nev, The National Gallery case downloads its open data (about 190 MB) into a temporar, test_provider_search_and_rights(), test_v03_sources_search_rights_and_one_image(), candidate_for() (+12 more)

### Community 24 - "Collection providers"
Cohesion: 0.15
Nodes (21): _aic(), _clip(), _cma(), _commons(), _commons_title(), _english(), _first_id(), _linked() (+13 more)

### Community 25 - "Credits and portable archives"
Cohesion: 0.14
Nodes (21): _archive_path(), credits(), export_collection(), _images(), Credits, portable archives, restore and media clean-up (the last two under the l, The exact schema this version creates (built once from the migrations in a scrat, A backup from an older Visual Atlas is migrated in its staging copy (never in pl, Every media path a database row refers to (anything else in media/ is a crash le (+13 more)

### Community 26 - "Network fetch errors"
Cohesion: 0.21
Nodes (17): FetchError, Exception, Plain-language network failure with a stable code; never contains response bodie, Chunks, make_fetcher(), test_a_provider_cooldown_refuses_at_once_without_calling_or_sleeping(), test_blocked_urls_never_reach_transport(), test_exact_size_cap_and_content_type_parameters_are_accepted() (+9 more)

### Community 27 - "CI and release workflows"
Cohesion: 0.11
Nodes (19): Checks workflow (ci.yml), Linux verify job, Windows install-and-starter check job, Public demo workflow (pages.yml), Release workflow (release.yml), Codex adversarial review rounds, CSS-only justified library grid with horizon header band, Publish like Qualia: public repo, Releases zip, Pages demo (+11 more)

### Community 28 - "Request coding"
Cohesion: 0.17
Nodes (18): correct_reading(), _cues(), _distinctive(), _phrases(), Request coding: tag a brief or a Find request with codes from the taxonomy, with, Validate direct user corrections, including deliberately empty selections; never, Lower-case word tokens, British spelling of colour, simple plural folding (lines, word -> the only code whose terms use it (shared or generic words tag nothing on (+10 more)

### Community 29 - "Safe downloader"
Cohesion: 0.16
Nodes (8): Fetcher, _public(), The only network path: https to allowlisted provider hosts, public addresses, bo, The body, or b'' after streaming it into `sink` (an open binary file) for large, Downloads only through fetch.py, Bounded v0.4 starter searches; all network and rights checks use the app's exist, FR-5 safe download, Opt-in live checks: real provider APIs and the user's signed-in assistants. Run:

### Community 30 - "Desk review regressions"
Cohesion: 0.12
Nodes (9): Regression tests for the Codex review of the reference desk (2026-11-23). Each f, _system(), test_custom_folder_names_give_refs_that_open(), test_design_system_images_are_never_publishable(), test_guard_covers_folders_configured_in_the_home_env_file(), test_library_only_directions_do_not_route_to_private_systems(), test_licence_notes_read_the_claim_and_catch_restrictions(), test_open_search_never_widens_an_empty_selection() (+1 more)

### Community 31 - "Generated and design-system layers"
Cohesion: 0.19
Nodes (19): _description(), enabled_systems(), find(), generated(), _licence(), Path, Reference layers that live outside the library database, read in place and never, The record's file, checked again at access time: still a regular file inside its (+11 more)

### Community 32 - "Desk tests"
Cohesion: 0.12
Nodes (8): fake_generated(), fake_system(), _jpeg(), Path, Reference desk, layers and the design-system commit guard. Offline: the real sta, A design-system skill folder shaped like the owner's: SKILL.md, references/image, test_advise_reads_the_brief_and_gives_reasoned_credited_references(), test_design_systems_are_opt_in_and_read_in_place()

### Community 33 - "Ask and Explore UI"
Cohesion: 0.14
Nodes (17): Answer(), Ask(), Explore(), ExploreIndex(), GoalPage(), RELATION, short(), TechniquePage() (+9 more)

### Community 34 - "AI task schemas"
Cohesion: 0.19
Nodes (18): Analysis, Comparison, Direction, Directions, Intent, Note, Observation, Plan (+10 more)

### Community 35 - "Agent rules and invariants"
Cohesion: 0.16
Nodes (16): AGENTS.md agent entrypoint, AI split: Codex proposes, Claude checks (model_reviewed), CLAUDE.md agent entrypoint, Evidence / technique / effect / intent separation, Server binds 127.0.0.1 with Host/Origin checks and launch token, Simplicity ladder (Ponytail), store.py is the only SQL writer invariant, Vendor CLI launches isolated (fixed argv, tools off, schema-validated) (+8 more)

### Community 36 - "Market research"
Cohesion: 0.18
Nodes (18): Landscape: reference tools and licence-clean sources, Mobbin MCP, open-museum-mcp, Refero MCP, Same Energy, Visual similarity is commodity, MCP servers and agent tools for visual references, design-critique-mcp (+10 more)

### Community 37 - "Licence rules per provider"
Cohesion: 0.26
Nodes (16): _aic(), _cma(), _commons(), _commons_credit(), credit_line(), _met(), _nga(), _no() (+8 more)

### Community 38 - "Server app and demo build"
Cohesion: 0.12
Nodes (7): create_app(), Path, Build the read-only public demo (web/dist-demo) from the bundled starter pack. N, client(), The web door to the reference desk: token-guarded API, no local paths, layer pic, test_settings_say_whether_a_key_exists_but_never_return_it(), client()

### Community 39 - "Jev ranking"
Cohesion: 0.23
Nodes (15): code_questions(), Jev, jev_coding(), jev_key(), jev_main(), jev_metadata(), jev_ranking(), jev_review() (+7 more)

### Community 40 - "test_store.py"
Cohesion: 0.31
Nodes (14): add(), analysis(), proposal(), Persistence, append-only history, human-correction preservation, search rows., test_a_model_cannot_check_its_own_proposal(), test_catalog_sync_refuses_removing_a_used_technique(), test_collections_validate_names_and_order(), test_data_survives_reopen_and_migrations_are_recorded() (+6 more)

### Community 41 - "fake.py"
Cohesion: 0.17
Nodes (12): _pick(), Path, Offline practice backend: deterministic, schema-valid answers with no model behi, run(), Blank, Find/Grow report whether they found what was asked, and automatic rejections sta, An analyser that sees no clear technique in any picture., run_find() (+4 more)

### Community 43 - "eval_v03.py"
Cohesion: 0.20
Nodes (15): code_rows(), coding_eval(), collect(), decide(), metadata_eval(), Path, v0.3 evaluation (deterministic, no AI). Criteria fixed beforehand in docs/evalua, Live searches; keeps rights-eligible candidates and a small thumbnail of each. P (+7 more)

### Community 44 - "jev.py"
Cohesion: 0.21
Nodes (12): JevError, Exception, rank(), Optional TypeSafe Jev relevance ranking for project directions: off by default,, Image ids most-relevant first (ties keep the given order), plus provenance for t, answering(), The optional Jev ranking: off by default, the person's own key, text only, and a, run_directions() (+4 more)

### Community 45 - "catalog.py"
Cohesion: 0.21
Nodes (12): Confusion, Domain, Goal, Named, BaseModel, Load, validate and sync the editable knowledge files (taxonomy and source polici, Relation, Source (+4 more)

### Community 46 - "mcp_server.py"
Cohesion: 0.18
Nodes (14): call(), _check(), handle(), _publish(), Read-only MCP server over stdio: the reference desk for AI agents.  Standard lib, The schema's own limits, enforced (clients may skip validation)., Run one tool; returns an MCP CallToolResult., One JSON-RPC message in, one response out (None for notifications). (+6 more)

### Community 47 - "Ask.tsx"
Cohesion: 0.25
Nodes (13): aspect(), briefOf(), EXAMPLES, LAYER_NAMES, layerLabel(), plainLicence(), Plates(), RefImage() (+5 more)

### Community 48 - "ImagePage.tsx"
Cohesion: 0.27
Nodes (11): HISTORY_STATE, ImagePage(), readTrail(), who(), Jobs(), date(), backendName(), BOXES (+3 more)

### Community 49 - "Remove an image, its files and annotatio"
Cohesion: 0.21
Nodes (12): Remove an image, its files and annotations; it will not be collected again., Add the bundled starter library (used by the Windows installer; safe to run agai, remove(), starter_import(), home_dir(), _inside(), local_setting(), Path (+4 more)

### Community 50 - "generate_images.py"
Cohesion: 0.22
Nodes (12): build(), companion(), embed_label(), gen_one(), label(), prompt(), Path, Maintainer script: generate the original teaching images in generated/ with Code (+4 more)

### Community 51 - "Backups and verified restore"
Cohesion: 0.19
Nodes (14): Backups and verified restore, Plan 005 v1.1, Atomic restore via SQLite backup API swap, Target-scaled job budgets, Spec 005 v1.1 dependability, grounding and evaluation, Annotation superseding on re-analysis, Frozen dev/final-holdout evaluation, Offset library pagination with stale-response guard (+6 more)

### Community 52 - "test_mcp.py"
Cohesion: 0.24
Nodes (11): call(), MCP server: a real stdio round trip in a subprocess, protocol errors, validation, rpc(), test_an_agent_can_pass_the_ids_the_words_missed(), test_bad_arguments_are_tool_errors_not_crashes(), test_directions_are_distinct_techniques_each_shown_by_its_references(), test_publish_use_keeps_only_free_licences(), test_stdio_round_trip_in_a_subprocess() (+3 more)

### Community 54 - "Metadata filter not integrated"
Cohesion: 0.17
Nodes (13): Metadata filter not integrated, Reuse Qualia stack and patterns, Jobs and usage limits, Plan 001 vertical slice, Analysis cache key, One job at a time (global lease), Spike results (Codex/Claude image input, provider APIs), Spec 001 vertical slice (+5 more)

### Community 55 - "TypeSafe Jev decision gate"
Cohesion: 0.21
Nodes (13): TypeSafe Jev decision gate, Plan 006 v0.3, nextByPosition arrow-key navigation, Observation regions (web/src/lib/regions.ts), Spec 006 v0.3 maturity and archive-of-looking redesign, Accessibility checks (axe-core, keyboard, screen reader), Design tokens (archive-of-looking palette and type), The horizon rule (PageHead) (+5 more)

### Community 56 - "analyze_prompt()"
Cohesion: 0.21
Nodes (12): analyze_prompt(), compare_prompt(), directions_prompt(), `library` is a bounded list of complete records (the caller sizes it); it is nev, Metadata, briefs and proposals go in as quoted JSON data, never as instructions., technique_brief(), untrusted(), verify_prompt() (+4 more)

### Community 57 - "Gaps: designers, agents, licence and pro"
Cohesion: 0.20
Nodes (12): Gaps: designers, agents, licence and provenance, Agents pick images with no licence awareness, AI output copyrightability (USCO Part 2, Thaler), EU AI Act Art. 50 and C2PA labelling, Prompt by technique, refuse living-artist names, Why-this-works is tacit (aesthetic muteness), Thesis B: reasoned private library for designers, Thesis C: craft-studied original imagery (+4 more)

### Community 58 - "Plan 008 Reference desk"
Cohesion: 0.32
Nodes (12): Plan 008 Reference desk, atlas/layers.py reference layers reader, 008 Reference desk session log, Decision: MCP via stdlib JSON-RPC, not official SDK, Spec 008 Reference desk, Ask page (web) and /api/desk endpoints, Design-system layer indexed in place (opt-in), Deterministic reference desk engine (atlas/desk.py) (+4 more)

### Community 59 - "analyze_schema()"
Cohesion: 0.45
Nodes (11): analyze_schema(), _array(), compare_schema(), directions_schema(), _object(), plan_schema(), _string(), verify_schema() (+3 more)

### Community 60 - "Commit guard for design-system files (ch"
Cohesion: 0.24
Nodes (9): Commit guard for design-system files (check_no_data.py), design_system_copies(), libraries(), Path, Fail on tracked user libraries, local configuration or secret environment files, path -> (blob id, size) for every file in the Git index: what a commit would con, Staged files whose bytes equal any file in a design-system library (renamed or r, The four known libraries plus any folders configured for the desk (VISUAL_ATLAS_ (+1 more)

### Community 61 - "Product thesis (2026-11-22)"
Cohesion: 0.29
Nodes (7): Product thesis (2026-11-22), No AI in the desk, Reference desk: one engine, three doors, Seven-lens design review pass, MCP server implemented with the standard library, similar_references / More like this, Ask page

### Community 62 - "Plan 003 Explore, connections and projec"
Cohesion: 0.36
Nodes (8): Plan 003 Explore, connections and project help, Ring layout graph (web/src/lib/graph.ts, Cytoscape preset), Spec 003 Explore, connections and project help, Directions job (project help, grounded citations), Explore goals and techniques pages, See connections ego-network map and list view, Tasks 003 Explore, connections and project help, retrieve_for_brief relevance-ranked directions retrieval

### Community 63 - "Plan 004 Install, release, demo and docu"
Cohesion: 0.36
Nodes (8): Plan 004 Install, release, demo and documentation, scripts/build_demo.py demo snapshot builder, atlas starter-export / starter-import, Spec 004 Install, release, demo and documentation, Public read-only demo (GitHub Pages), Bundled starter library (licence-checked, <=1024 px copies), Windows installer and launcher, Tasks 004 Install, release, demo and documentation

### Community 64 - "eval_r2.py"
Cohesion: 0.48
Nodes (6): at(), coder(), evaluate(), Round-2 brief reading evaluation (overnight 23 Nov 2026). Run: uv run python scr, score(), split_of()

### Community 65 - "Plan 007 Visual reasoning"
Cohesion: 0.47
Nodes (6): Plan 007 Visual reasoning, Spec 007 Visual reasoning v0.4.0, Iris description comparison baseline, Starter coverage audit and curation (FR-004/005), Navigable many-to-many taxonomy memberships, Tasks 007 Visual reasoning

### Community 66 - "Visual Atlas starter credits"
Cohesion: 0.33
Nodes (6): Visual Atlas starter credits, Art Institute of Chicago (aic, 23 credits), Cleveland Museum of Art (cma, 17 credits), Wikimedia Commons (40 credits), The Met (9 credits), Smithsonian (15 credits)

### Community 67 - "Rights decided only by rights.py; unclea"
Cohesion: 0.40
Nodes (5): Rights decided only by rights.py; unclear licence is ineligible, Free-to-use visual inspiration sources, Free to download is not free to use, Inspiration-only sources (Cosmos, Are.na, Savee, Pinterest), CC0 is not safe for every use

### Community 68 - "demo.ts"
Cohesion: 0.50
Nodes (4): demoRequest(), Item, load(), Snapshot

### Community 69 - "credits()"
Cohesion: 0.50
Nodes (4): credits(), Print credits (attribution) for the library or a collection., Maintainers: write the current library as the bundled starter pack., starter_export()

### Community 70 - "mcp()"
Cohesion: 0.50
Nodes (4): mcp(), Run the local server without opening a window (developers and agents)., Run the read-only MCP server on stdio (for Claude Code, Codex and other agents)., serve()

### Community 72 - "make_tour.py"
Cohesion: 0.50
Nodes (3): main(), Path, Assemble the README tour GIF from numbered screenshots (taken with Playwright fr

### Community 73 - "Tasks 002 Library, discovery and correct"
Cohesion: 0.67
Nodes (3): Tasks 002 Library, discovery and corrections, Compare page and saved AI comparison job, Grow job from coverage gaps

## Ambiguous Edges - Review These
- `similar_references / More like this` → `Visual similarity is commodity`  [AMBIGUOUS]
  OVERNIGHT-CHANGES.md · relation: conceptually_related_to

## Knowledge Gaps
- **70 isolated node(s):** `visual-atlas`, `TOOLS`, `EXAMPLES`, `LAYER_NAMES`, `STATE_MARK` (+65 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **7 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `similar_references / More like this` and `Visual similarity is commodity`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `Worker` connect `Job worker and leases` to `Claude Code adapter`, `Job tests and leases`, `Server app and demo build`, `Brief coding and job creation`, `fake.py`, `Knowledge sync and analysis`, `Path`, `Second-model checks`, `jev.py`, `Remove an image, its files and annotatio`, `Local web server`, `test_server.py`, `Test helpers`, `Network fetch errors`, `Safe downloader`, `Desk review regressions`?**
  _High betweenness centrality (0.079) - this node is a cross-community bridge._
- **Why does `Store` connect `Path` to `Job worker and leases`, `Library store records`, `Server app and demo build`, `Brief coding and job creation`, `test_store.py`, `Knowledge sync and analysis`, `Backup and restore`, `Remove an image, its files and annotatio`, `Local web server`, `Test helpers`, `Credits and portable archives`?**
  _High betweenness centrality (0.069) - this node is a cross-community bridge._
- **Why does `open_store()` connect `Knowledge sync and analysis` to `Job worker and leases`, `Job tests and leases`, `credits()`, `Command line`, `Server app and demo build`, `Jev ranking`, `Brief coding and job creation`, `Path`, `fake.py`, `Second-model checks`, `jev.py`, `test_store.py`, `Remove an image, its files and annotatio`, `test_mcp.py`, `Test helpers`, `Request coding`?**
  _High betweenness centrality (0.046) - this node is a cross-community bridge._
- **Are the 9 inferred relationships involving `Store` (e.g. with `Worker` and `AnnotationInput`) actually correct?**
  _`Store` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Are the 6 inferred relationships involving `Worker` (e.g. with `BackendError` and `Fetcher`) actually correct?**
  _`Worker` has 6 INFERRED edges - model-reasoned connections that need verification._
- **Are the 82 inferred relationships involving `store()` (e.g. with `coverage()` and `credits()`) actually correct?**
  _`store()` has 82 INFERRED edges - model-reasoned connections that need verification._