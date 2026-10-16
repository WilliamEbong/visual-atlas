# Visual Atlas 0.4.0 — visual reasoning

This is a local, unpublished release. The database remains at schema 2; existing libraries, human corrections,
collections and saved comparisons remain compatible.

- **Explore reasoning:** goals, operations and domains are entry points into the existing taxonomy. The focused
  canvas and accessible list explain memberships, distinguish related techniques and recorded examples, and
  retain main/supporting roles and review states. Counts reveal hidden examples; expansion and comparison retain
  the exploration context through image, technique and library pages.
- **Correct ordinary-language readings:** deterministic interpretation recognises more descriptions, handles
  ordinary negation and removes more instruction words from subject searches. Find and My project let you change
  goals, techniques and subject words directly. The adviser retains the original brief, and subject matches keep
  places in the reference candidates. There is no new service, AI call for reading, or model call for navigation.
- **Curated starter examples:** eight additions bring the pack to 93 references. Contextual incongruity grows
  from 1 to 5, visual metaphor from 3 to 6, figure–ground ambiguity from 1 to 2; juxtaposition remains 6.
  Photography, photomontage, illustration and an information graphic broaden the examples. New readings remain
  proposed because independent CLI review was unavailable. See `evaluation/v0.4/CURATION.md` for item evidence,
  verified reuse terms, exclusions and the three-example figure–ground shortfall.

Evaluation uses provisional model-authored judgments, not an expert panel. Across 16 held-out briefs, combined
goal/technique precision rose from 14/19 to 12/13, while recall fell from 14/20 to 12/20. Expected techniques
represented in the first 20 candidates remained 12/13. See `evaluation/v0.4/BRIEF-REPORT.md` for raw counts,
development results, subject-word leakage and limitations. More conservative suggestions do not establish broad
natural-language understanding; the correction controls remain important.

## Try it

Launch `uv run visual-atlas` from the repository, or extract the local release zip and run
`Install Visual Atlas.cmd`. Keep the library outside OneDrive; `VISUAL_ATLAS_HOME` can select a separate library.

1. Open Explore → See connections, and choose **Make one thing stand out**.
2. Follow **Isolate**, **Space and depth**, then **Negative space isolation**. Read the membership explanation.
3. Use **Show more examples**, choose two to four **+ Compare**, and **Compare side by side**.
4. Use **Return to your exploration** to recover the same focus, view, expansion and trail.
5. In Find or My project, try the solitude brief, then **Correct this reading** before submitting.

Build locally with `powershell -ExecutionPolicy Bypass -File scripts/build-release.ps1 -Version v0.4.0 -WorkingTree`.
The explicit working-tree build copies tracked and nonignored source, respects export exclusions, checks copied
file hashes, and adds the freshly compiled frontend. It does not require a commit or publish anything.

The comparison baseline is the owner's supplied description of the Iris demonstration: operation/domain,
technique and execution/example, with network exploration and comparison. Visual Atlas exposes those recorded
memberships with license evidence and honest review states; it does not claim parity with the full Iris product.
The linked TikTok and public site were inaccessible through the built-in fetch, so no claim of watching them is made.
