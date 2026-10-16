# Starter curation, v0.4

Checked 2026-10-15–16. **93 references, up from 85; eight new readings, all proposed.**
The original 85 records and their review states were preserved. This is a builder/model curatorial judgment,
not independent expert ground truth. Counts measure non-rejected labels, not validated teaching quality.

## Audit before sourcing

The baseline had 85 references across all 26 techniques: Commons 24, AIC 23, Cleveland 16,
Smithsonian 15 and Met 7. Museum collections supplied 61/85 references; historical paintings,
prints and object photographs dominated. Counts were concentrated in value contrast (35), negative
space (19) and asymmetric balance (18). The smallest conceptual categories were contextual incongruity
(1), figure–ground ambiguity (1) and visual metaphor (3). Juxtaposition had six labels, but only three
were agreed by a second model; the other three were proposals. Neither raw counts nor museum ownership
alone establish quality or medium diversity.

| Priority | Before | After | New examples | Limitation |
|---|---:|---:|---|---|
| Contextual incongruity | 1 | 5 | Sky jellyfish montage; hats on hydrant; smoking caterpillar; giant goblet landscape | Four new proposals, awaiting independent check |
| Figure–ground ambiguity | 1 | 2 | Eagle/profile shared contours | Three short of five; no padding with other illusions |
| Visual metaphor | 3 | 6 | Quantified Human; All Is Vanity; Temple of Time | Three new proposals; metaphor interpretations remain debatable |
| Juxtaposition | 6 | 6 | None | Three existing proposals; no claim of five independently validated examples |

Detailed before/after counts and all returned search records are in [coverage.json](coverage.json).
The collection now contains 167 model-reviewed and 54 proposed labels. No new reading is human-reviewed
or model-reviewed. New distribution media adds 2,178,274 bytes (about 2.08 MiB); only the existing
1024px analysis copies and 480px thumbnails are bundled, not full-resolution originals.

## Accepted examples and teaching evidence

Every accepted downloaded image was opened with `view_image` and inspected as actual pixels in this
session. [curation-additions.json](curation-additions.json) records the concrete observations, proposed
effect, teaching value and ambiguity for each. Those same observations are validated with the app's
analysis contract and stored in the starter, rather than kept only in this report.

| Example | Mechanism and distinct contribution | Source / rights |
|---|---|---|
| Celestial Jellyfish | A marine body flies above an otherwise ordinary coastal inlet; contemporary photomontage changes setting. | [Commons, W.carter](https://commons.wikimedia.org/wiki/File:Celestial_Jellyfish_-_photomotage.jpg), CC0 1.0 |
| Quantified Human | A portrait is divided into tiles and overlaid with meshes/networks; contemporary editorial metaphor for a person represented as data. | [Commons, Alan Warburton for BBC](https://commons.wikimedia.org/wiki/File:Alan_Warburton_-_Quantified_Human.jpg), CC BY 4.0; BBC / Better Images of AI credit also retained |
| Irrational behavior, Budapest | Black top hats stacked on a fire hydrant create mismatch in an everyday street photograph. No performance or advertising intent is asserted. | [Commons, Marek Ślusarczyk](https://commons.wikimedia.org/wiki/File:01_Irrational_behavior,_surreal_absurd_street_scene_in_Budapest,_Hungary.jpg), CC BY 3.0 |
| Eagle of the Republic | Pale gaps beside dark eagle wings become face profiles along shared contours; historical graphic figure–ground reversal. | [Commons scan of 1865 card](https://commons.wikimedia.org/wiki/File:Civil_War_optical_illusion_card-The_Eagle_of_the_Republic.png), public domain |
| All Is Vanity | Woman, reflection, mirror and table assemble into a skull-like form, linking grooming and mortality. A compound metaphor, **not** counted as figure–ground reversal. | [Commons, Charles Allan Gilbert](https://commons.wikimedia.org/wiki/File:Charles_Allan_Gilbert_-_All_is_Vanity.jpg), public domain |
| Alice and the Caterpillar | An upright caterpillar uses a hookah on a mushroom: animal/human activity mismatch in narrative illustration. | [Commons, John Tenniel illustration](https://commons.wikimedia.org/wiki/File:Alice_05a-1116x1492.jpg), public domain; exact file URL in starter record |
| Temple of Time | Names and dates occupy receding columns, floor and ceiling; history becomes an architectural space in an information graphic. Small type needs the source original. | [Commons, Emma Willard, 1846](https://commons.wikimedia.org/wiki/File:Temple_of_Time_(1846)_Emma_Willard.jpg), public domain |
| The Titan's Goblet | A giant drinking vessel holds boats and a tree-lined lake above mountains; impossible object/environment relationship. | [The Met, Thomas Cole, 1833](https://www.metmuseum.org/art/collection/search/10499), item-level CC0 |

## Rights and actual access

All candidates used the existing `providers.search`, `Fetcher`, image decoder/quality checks and
`rights.check`; no provider or permission rule was added. Each accepted item retains its source page,
creator, item-level evidence, license URL/version, attribution, retrieval/checking timestamp, policy hash,
original downloaded-file hash and resized-copy hash. Each addition's rights provenance separately
records the redistribution basis and resizing/re-encoding. This is additional distribution evidence;
the app's existing local storage/display/analysis permission label was not redefined.

Official information read during the session:

- [Commons reuse guidance](https://commons.wikimedia.org/wiki/Commons:Reusing_content_outside_Wikimedia):
  check each file's license and credit the creator, including restrictions beyond copyright.
- [Wikimedia User-Agent policy](https://foundation.wikimedia.org/wiki/Policy:Wikimedia_Foundation_User-Agent_Policy):
  the existing descriptive app user agent and throttled API path were used, with bounded requests.
- [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) and [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/):
  redistribution follows the recorded grant; attribution and indication of resizing are included.
- [The Met Open Access policy](https://www.metmuseum.org/hubs/open-access): CC0 images can be downloaded,
  shared and remixed; the live API returned `isPublicDomain: true` and `primaryImage` for item 10499.
- [Better Images of AI library](https://betterimagesofai.org/images): CC BY licensing and its request to
  retain the image's attribution; Quantified Human also retains the BBC / Better Images of AI credit.
- Live Commons API responses supplied the exact license/creator/source evidence for all seven Commons
  additions. The public file pages for Celestial Jellyfish, Quantified Human and Temple of Time were
  additionally fetched. Web fetch for a guessed All Is Vanity page failed; the actual file's live API
  evidence is retained, and no successful page fetch is claimed.

All new files are 2 CC0, 4 public domain and 2 CC BY. Current total: 71 CC0, 7 public domain, 15 CC BY.
Permission for a particular use can still depend on personality rights, trademarks or other restrictions.
Model interpretations never authorized rights. The user's real library was never opened or altered.

## Searches, exclusions and remaining gap

Eleven bounded live queries returned 70 unique candidates. Commons: `Rubin vase`, `"figure ground"`,
`"optical illusion"`, `surreal photomontage`, `"photomontage"`, `"visual metaphor"`, `surreal`,
`"ambiguous"`, `"figure-ground"`, `"Temple of Time"`; Met: `Titans Goblet`. The search helper requests
12 results per query through the existing eligibility-narrowed provider path. A console encoding error
interrupted the first optical-illusion pass; its duplicate retry is de-duplicated in the coverage log.

Independent final pixel review by the root and holdout agents rejected the broken question-mark candle: the damaged punctuation could be a literal still life, and the proposed abstract message was too speculative for a strong teaching example. It was removed before release.

Excluded examples included the shaded Rubin vase (weak reversal at this view), duck/rabbit
(object ambiguity, not ground reversal), cracks resembling mountains (pareidolia), forced-perspective
hand/person photography (scale, not ground reversal), generic surreal skies/ruins/cemeteries, duplicate
baseline figure-ground text, repetitive Warburton Plant and fish/car abstraction triptychs, advertising
screenshots and brand/logo examples, uncertain sculpture-composite rights, and irrelevant search returns.
The Met's modern *Titan's Goblet at the Approach of the Third Millennium* was deterministically rejected
as not public domain. Two Phall-O-meter records were rejected for missing required author credit.

The user's Archive of Looking, Garden of Lingering, Citadel of Watching and Harbour of Drifting local
catalogs were also screened as discovery leads. The Titan's Goblet and Temple of Time were selected,
re-fetched and independently rights-checked through supported providers. Wellcome's pea/brain image
looked promising in catalog review but had no current provider route; no provider was added for one item.
Generated Harbour images were excluded from provider-based starter records because their catalog did not
establish a redistribution license. No Iris assets or copyrighted advertising references were scraped.

Figure–ground remains two credible examples, three below the five-example aim. A bounded search could
not establish three more meaningfully different eligible examples with the correct mechanism.
Contemporary graphic design and typography are still underrepresented, and juxtaposition's three old
proposals remain unverified. These are explicit collection gaps, not evidence of completed target coverage.

## Review and verification

Claude and Codex checks in the sandbox returned `subscription_auth_required`. A bounded host adapter
check confirmed Codex CLI 0.160.0 available but Claude still unavailable. The requested host Codex image
analysis never executed: its approval call was interrupted after waiting. This authorization blocker is
separate from the sandbox credential failures. No successful CLI analysis or independent model verdict
is fabricated. The eight actual interactive curation-agent readings use `backend: codex-interactive`,
`model: GPT-6 curation agent`, no CLI version and no claimed token usage; they remain `proposed`.
The schema-required 0.7 score is a qualitative model judgment, **not a measured probability**.

Fresh scratch import: 93 imported; repeat import: 0; CSV credits: 93 rows. Credits were regenerated from
that fresh import, including all required attribution, license URLs and source links. The original source
library's gapped image numbers are replaced by the clean starter import's sequential credit numbers.
Regression tests validate all eight contracts, review provenance, rights and image checksums, then import
the complete pack and check idempotency/credits. Final targeted suite: **10 passed** (eight existing starter tests, two curation regressions); Ruff passes. A fresh explicit system-temp test base avoided the sandbox default temp-folder permission failure. A stale nine-item assertion exposed by candle removal was corrected before the passing final run. No migration was needed and original records were not reclassified.
