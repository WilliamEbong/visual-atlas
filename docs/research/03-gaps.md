# 03 — Gaps: what designers and agents lack; licence and provenance concerns

Research date: 2026-11-22. The evidence here is uneven. The AI-sameness
complaints are many but mostly blogs. The survey data comes from a vendor
(Figma). The academic work on tacit knowledge is solid but predates AI agents.
I mark the weak spots as I go.

## Part A — What is missing when designers and agents make visual decisions

### Gap 1. Agents default to the median ("AI slop")

- Anthropic's own write-up says Claude tends to converge on generic
  "on distribution" outputs in frontend work, producing what users call the "AI
  slop" aesthetic. It fixes this with a skill, not a model change
  ([Claude blog](https://claude.com/resources/articles/improving-frontend-design-through-skills)).
- Practitioner posts describe the same tell-tale set: purple gradients, Inter,
  rounded cards, a three-box feature grid. They explain it as models producing
  "the median" of their training data
  ([DEV](https://dev.to/alanwest/why-every-ai-built-website-looks-the-same-blame-tailwinds-indigo-500-3h2p),
  [Built In](https://builtin.com/articles/ai-design-slop-era),
  [Kosta Canatselis](https://world.hey.com/kostac/spot-the-slop-a-ui-designer-s-guide-to-fixing-ai-defaults-4c448c9c)).
  One self-run pixel analysis claims 95% of sampled AI UIs cluster around blue-purple
  ([DEV](https://dev.to/kenimo49/why-ai-generated-uis-are-all-the-same-color-and-the-data-to-prove-it-12oe)).
  That is not peer-reviewed, and one counter-post notes the pre-AI web all looked
  like Bootstrap ([DEV](https://dev.to/lyd_lyd_d4869af25d33ce0eb/why-do-ai-generated-websites-all-look-the-same-k2j)).
- The commercial response is to feed agents references. Mobbin and Refero both
  launched MCPs in 2026 on this pitch (see `02-agent-tools.md`).

**Implication:** Specific, non-median references help. A mood board that matches
the median does not. The evidence is about UI. I found nothing that measures
the same effect for imagery choice, so that link is inferred.

### Gap 2. Designers don't trust AI output, and judging it is the hard part

- In Figma's 2025 survey of 2,500 builders, 78% said AI makes them more
  efficient but only 58% said it improves quality. Designers were less
  positive than developers ([TechRadar](https://www.techradar.com/pro/figmas-latest-survey-shows-ai-is-not-yet-living-up-to-its-over-hyped-promise),
  [Figma report](https://figma.com/reports/ai-2025/)). Secondary write-ups give
  conflicting designer figures (32–54%) for different questions
  ([ADPList breakdown](https://adplist.substack.com/p/breakdown-figma-ai-report-2025)),
  so I only rely on the direction, not a number.
- A Figma survey of 1,800 users found the top challenge was assessing the
  quality of AI output ([Analytics India Mag](https://analyticsindiamag.com/ai-news/figma-research-finds-ai-speeds-up-product-building-raises-quality-concerns)).

**Implication:** The scarce thing is a basis for judging, not more output. An
explicit "evidence → technique → effect" reading gives a designer something to
check, accept or overrule.

### Gap 3. "Why this works" is tacit and rarely written down

- Organisational research on design firms describes aesthetic knowledge as
  largely tacit (Polanyi). It names "aesthetic muteness", the difficulty of putting
  aesthetic judgement into words ([Stigliani & Ravasi, UCL](https://discovery.ucl.ac.uk/10058200/1/Stigliani%20and%20Ravasi%20Aesthetic%20Knowledge.pdf)).
- Mood boards are valued mainly for communicating with non-designers and
  prompting lateral thinking. Practitioners call them "love it or hate it"
  ([Illinois scoping study](https://experts.illinois.edu/en/publications/mood-boards-as-a-design-catalyst-and-resource-researching-an-unde/)).
  Lucero's interview work asks what boards are for
  ([Lucero, Aalto](https://users.aalto.fi/~luceroa1/publications/2009/lucero09_codesign.pdf)).
  Cassidy treats making a board as a qualitative research process
  ([Huddersfield](https://pure.hud.ac.uk/en/publications/the-mood-board-process-modeled-and-understood-as-a-qualitative-de/)).
- No tool in `01-landscape.md` stores a rationale per image. Boards hold
  pictures, and the reasoning stays in the designer's head or a meeting.

**Implication:** A shared vocabulary of techniques tied to visible evidence is
an attempt to make tacit knowledge explicit. Evidence that designers *want*
this written down is thin. I found none showing designers asking for
annotated boards. The value claim is strongest for agents, which have no
tacit knowledge and need the reasons in words.

### Gap 4. Generic imagery carries no information

- Jakob Nielsen argues that indistinct or generic pictures confuse users and
  erode credibility, and that generic stock photos aren't helpful
  ([Nielsen Substack](https://jakobnielsenphd.substack.com/p/photography?open=false)).
  The often-repeated claim that NN/g eye-tracking showed users "completely
  ignore" stock photos reached me only through marketing blogs
  ([GroupM7](https://groupm7.com/blog/post/do-customers-distrust-websites-with-stock-photos)).
  **Not verified** at the source.
- Inspiration feeds are filling with AI images. Pinterest added gen-AI labels
  and a "see less" control after user backlash, in art, decor, fashion and beauty
  ([TechCrunch](https://techcrunch.com/2025/04/30/pinterest-launches-new-tools-to-fight-ai-slop/),
  [Pinterest](https://newsroom.pinterest.com/news/pinterest-rolls-out-new-tools-to-give-users-more-control-over-gen-ai-content/)).
  Its classifiers "aren't perfect" ([Pinterest](https://newsroom.pinterest.com/news/introducing-gen-ai-labels)).

**Implication:** Museum collections are known human-made works with
provenance. That is useful precisely because feeds no longer are.

### Gap 5. Agents pick images with no licence awareness

- Agent skills already insert hotlinked Unsplash images into code
  ([skill listing](https://mulerun.com/skillshub/@lxiaolong068/skills~unsplash-image-filler:20260125173615/llm.txt)).
  That is legitimate under Unsplash's API terms only if the attribution rules are
  followed ([Unsplash guidelines](https://help.unsplash.com/api-guidelines/unsplash-api-guidelines)).
- The open aggregators disclaim accuracy. Openverse says it does not verify
  licences ([about, archived](https://webcf.waybackmachine.org/web/20231210110130/https://openverse.org/about)).
  Commons licence metadata is free text and unreliable for multi-licensed files
  ([CommonsMetadata](https://www.mediawiki.org/wiki/Extension:CommonsMetadata/en)).
- The "taste" MCPs return copyrighted UI with a "don't copy verbatim" warning
  and no machine-readable rights field ([Mobbin](https://mobbin.com/mcp.md)).
- **Evidence gap:** I found no incident report, lawsuit or survey about an
  *agent* shipping an unlicensed image. The risk is clear in principle. How
  often it happens is unmeasured.

### Smaller gaps seen in passing

- Same Energy, Cosmos and Pinterest MCPs depend on unofficial endpoints or
  session tokens ([mcpmarket](https://mcpmarket.com/server/same-energy),
  [glama](https://glama.ai/mcp/servers/mrmos/cosmos-mcp)). Agents lack stable,
  sanctioned image sources outside stock and museums.
- Figma MCP users report weak results when the design is complex
  ([Figma forum](https://forum.figma.com/report-a-problem-6/figma-mcp-can-t-get-good-results-have-tried-many-things-41861)).
  Context transfer alone does not produce good decisions.

## Part B — Licence and provenance: AI output and reference use

### US copyright in AI-generated images

- **Prompts are not authorship.** The Copyright Office's Part 2 report (29 Jan
  2025) says AI outputs are protectable only where a human determined
  sufficient expressive elements. Prompting alone does not qualify. Human
  selection, arrangement, modification and perceptible human input can be
  protected ([USCO NewsNet](https://copyright.gov/newsnet/2025/1060.html),
  [Copyright Alliance summary](https://copyrightalliance.org/ai-report-part-2-copyrightability/)).
- **Human authorship is required.** The D.C. Circuit held so in *Thaler v.
  Perlmutter*, 130 F.4th 1039 (2025). The Supreme Court denied cert on 2 March 2026
  ([Holland & Knight](https://www.hklaw.com/en/insights/publications/2026/03/the-final-word-supreme-court-refuses-to-hear-case-on-ai-authorship),
  [Mayer Brown](https://www.mayerbrown.com/en/insights/publications/2026/03/supreme-court-denies-review-in-ai-authorship-case)).
  How much human input is enough remains open, and *Allen v. Perlmutter* (D. Colo.)
  is the case to watch ([Mayer Brown](https://www.mayerbrown.com/en/insights/publications/2026/03/supreme-court-denies-review-in-ai-authorship-case)).
  I did not check Allen's status after March 2026.
- **Consequence for a generated-image layer:** Images a user generates from a
  prompt are likely uncopyrightable as generated. The user cannot stop others
  copying them. Clients who expect to own assets may care. Saving the human edits,
  selections and prompts helps a later authorship claim. That is my inference
  from the USCO report, not legal advice.

### Style imitation and training

- Style itself is not protected by copyright. The Copyright Office's Part 3
  pre-publication report (May 2025) nonetheless treats output that imitates a
  creator's style as possible market harm ("dilution") in fair-use analysis
  ([USCO Part 3 PDF](https://www.copyright.gov/ai/Copyright-and-Artificial-Intelligence-Part-3-Generative-AI-Training-Report-Pre-Publication-Version.pdf),
  [Jones Day](https://www.jonesday.com/en/insights/2025/05/us-copyright-office-issues-guidance-on-generative-ai-training)).
- *Andersen v. Stability AI* (artists v. Stability, Midjourney, DeviantArt,
  Runway) is unresolved. Trial is set for early-to-mid 2027, and sources differ on
  the date ([McKool Smith](https://www.mckoolsmith.com/newsroom-ailitigation-54),
  [joint CMC statement](https://chatgptiseatingtheworld.com/wp-content/uploads/2026/01/Andersen-v-Stability-AI-Joint-Case-Man-Statement.pdf)).
- UK: in *Getty v. Stability* (4 Nov 2025) Getty lost the secondary copyright
  claim because the model stores no copies. Getty won narrow trade-mark points
  over watermark reproduction. Training legality was left open
  ([Cleary Gottlieb](https://www.clearygottlieb.com/news-and-insights/publication-listing/uk-high-court-issues-landmark-ruling-in-getty-images-v-stability-ai),
  [DLA Piper](https://www.dlapiper.com/insights/publications/2025/11/getty-images-v-stability-ai-the-uk-high-court-decision-offers-guidance-but-critical-questions-on-ai)).
- **Consequence:** Prompting from *public-domain* masters ("chiaroscuro as in
  Caravaggio") sits far from the contested ground. Prompting "in the style of"
  a *living* artist is where the market-harm argument and the reputational risk
  sit. A craft-study layer should prompt by **technique**, which Visual Atlas's
  taxonomy already names, and refuse living-artist names by default.

### Labelling and content credentials

- **EU AI Act Art. 50** applies from 2 Aug 2026. Providers of generative systems
  must mark outputs machine-readably, and deployers must label deepfakes. A voluntary
  Code of Practice was published 10 June 2026
  ([Commission FAQ](https://digital-strategy.ec.europa.eu/en/faqs/code-practice-transparency-ai-generated-content),
  [EAO Merlin](https://merlin.obs.coe.int/article/10565),
  [Orrick](https://www.orrick.com/en/insights/2026/08/eu-ai-act-transparency-obligations-for-ai-generated-content-article-50)).
  Whether a local open-source app that calls a vendor model counts as provider or
  deployer is a question I did not resolve. The vendor likely carries the marking duty.
- **C2PA / SynthID:** OpenAI joined the C2PA steering committee and added Google's
  SynthID watermark to its image outputs (May 2026), with a preview verifier
  ([OpenAI](https://openai.com/index/advancing-content-provenance),
  [TNW](https://thenextweb.com/news/openai-c2pa-synthid-ai-image-detection-watermark)).
  Metadata can be stripped in conversion, which is why the pixel watermark
  exists ([OpenAI](https://openai.com/index/advancing-content-provenance)).
- **Consequence:** A generated-image layer should keep vendor C2PA manifests
  intact (no re-encoding that strips them). It should label generated images as
  such everywhere in the UI and in agent responses, and never mix them into the
  "licence-clean reference" pool. That last rule is the project's own
  invariant applied to a new source type.

### Reference use of museum images

- CC0 and public domain settle copyright only. Privacy, publicity, trademark and
  cultural-sensitivity issues can remain ([Smithsonian FAQ](https://dashboard.si.edu/openaccess/faq)).
  This supports the existing rule against ever labelling anything "safe for every use".
- Commons licences can describe the depicted object rather than the photograph
  ([Phabricator](https://phabricator.wikimedia.org/T59465)). This is a concrete
  case for per-source rules over trusting a single licence field.

## Facts I could not verify

- The original NN/g stock-photo eye-tracking finding (only secondary sources).
- Exact current prices for Cosmos, Savee, Flim and Kive (sources conflict).
- Pinterest official MCP availability (sources conflict).
- Any measured incidence of agents shipping unlicensed images.
- Whether designers (not agents) want per-image written rationale.
- Status of *Allen v. Perlmutter* after March 2026.
