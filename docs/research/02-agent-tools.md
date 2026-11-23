# 02 — MCP servers and agent tools for visual references and design taste

Research date: 2026-11-22. I searched registry listings (glama.ai, mcpservers.org,
mcp.so, lobehub, mcpmarket) and vendor docs. Registries mirror GitHub and are
often stale, so a listing is not proof that a server is maintained. I did not
install or run any of these servers. Descriptions come from their docs.

## What exists, grouped by what the agent gets back

### A. "Taste" from real product UI (commercial, paid)

| Server | Returns | Licence | Reasons / rationale |
|---|---|---|---|
| **Mobbin MCP** (official, beta, read-only) | `search_screens`, `search_flows`, `search_sections`: screen images, product name, flow/section context, link back to Mobbin ([mcp.md](https://mobbin.com/mcp.md), [blog](https://mobbin.com/blog/how-to-use-mobbin-mcp)) | No reuse licence; "do not copy protected designs, branding, text, or assets verbatim" ([mcp.md](https://mobbin.com/mcp.md)) | None in the output. The guide warns that an example shows a product *used* a design, not that it worked |
| **Refero MCP** (official, Pro plan) | Tools for styles, screens, images, similar screens, flows. Styles cover typography, colour, layout, spacing, imagery and **do/don't rules** ([getting started](https://doc.refero.design/mcp/getting-started.md)) | Not addressed | Companion skill has the agent write a brief, pick one primary style, borrow bounded details, keep a "decision ledger", and run "anti-AI-slop quality gates" ([skill](https://doc.refero.design/skill/overview.md)) |

These two are the clearest evidence that a market exists. Both sell
"references so agents stop producing generic design" to coding agents. Refero
markets itself as "Give your AI agent design taste + prevent generic AI design"
([hunted.space](https://hunted.space/dashboard/refero)). Both cover only UI
screens of shipped products, a corpus the user may not legally reuse.

### B. Stock and open-licence image search (community, free)

| Server | Returns | Licence | Reasons |
|---|---|---|---|
| Unsplash MCPs (hellokaton, hanoak; unofficial) | `search_photos` with orientation/colour filters; attribution helpers in hanoak ([mcpservers.org](https://mcpservers.org/servers/hanoak/unsplash-mcp-server), [mcpservers.org](https://mcpservers.org/servers/hellokaton/unsplash-mcp-server)) | Unsplash licence. The API guidelines add their own rules: credit photographer + Unsplash with links, hotlink returned URLs ([guidelines](https://help.unsplash.com/api-guidelines/unsplash-api-guidelines), [attribution](https://help.unsplash.com/api-guidelines/more-on-each-guideline/guideline-attribution)) | None |
| Openverse MCPs (`@mcp/openverse`, Apify actor, others) | Image URL, licence, attribution as Openverse reports them; anonymous 100 req/day ([npm](https://www.npmjs.com/package/mcp-openverse), [Apify](https://apify.com/fit_melon/openverse-cc-media-search.md)) | Openverse itself does not verify licences ([about, archived](https://webcf.waybackmachine.org/web/20231210110130/https://openverse.org/about)) | None |
| Same Energy MCP (unofficial) | Text or image-similarity search; metadata, source platform, URLs; downloads ([mcpmarket](https://mcpmarket.com/server/same-energy)) | None stated; images come from Reddit/Instagram/Pinterest ([about](https://same.energy/about)) | None |
| Pinterest MCPs (official announced; many community) | Pins and boards via API v5 or scraping ([scalekit](https://www.scalekit.com/blog/pinterest-mcp-vs-api), [glama](https://glama.ai/mcp/servers/clugtu/pinterest-mcp)) | None | None |
| Cosmos MCP (unofficial, private GraphQL, session token) ([glama](https://glama.ai/mcp/servers/mrmos/cosmos-mcp)) | Clusters/elements | None | None |
| Are.na MCP (official hosted) | Channels, blocks, read/write ([repo mirror](https://github.zuike.workers.dev/aredotna/mcp)) | None | Only whatever notes the human wrote |

A related signal: one published agent skill tells agents to insert Unsplash
hotlinks into HTML/JSX and never download the image
([skill listing](https://mulerun.com/skillshub/@lxiaolong068/skills~unsplash-image-filler:20260125173615/llm.txt)).
Hotlinking is what the Unsplash API terms expect
([hotlinking guideline](https://help.unsplash.com/api-guidelines/guideline-hotlinking-images)).
So agents are already being set up to drop stock imagery into products, and
whether credit lines survive depends on the skill author.

### C. Museum and open-access collections (community, free)

Covered in `01-landscape.md`. The standout is `open-museum-mcp`. It has a
strict rights gate, a licence object with verification source, date and
confidence, and a `cite` tool. Results carry no ranking and no design reasoning
([README](https://raw.githubusercontent.com/cfpramod/open-museum-mcp/main/README.md)).
Single-museum servers (Met, Rijksmuseum, Smithsonian) return raw collection
records ([glama](https://glama.ai/mcp/servers/mikechao/metmuseum-mcp),
[mcpservers.org](https://mcpservers.org/servers/r-huijts/rijksmuseum-mcp)).

### D. Design-file and design-system context

- **Figma MCP** (official, open beta). Returns design context, screenshots,
  variable definitions and Code Connect maps for a selection. Older tool names
  were `get_code` and `get_image`
  ([mcp-server-guide](https://github.com/figma/mcp-server-guide),
  [connector listing](https://claude.com/connectors/figma-8ef5e4)). Forum users
  report weak results and fallback to screenshot only
  ([Figma forum](https://forum.figma.com/report-a-problem-6/figma-mcp-can-t-get-good-results-have-tried-many-things-41861)).
  It passes along what the designer already decided. It does not help decide.
- Design-system MCPs (tokens, component docs) follow the same pattern. They
  expose a system that already exists. I did not survey them individually.

### E. Critique and "taste" checkers

- **design-critique-mcp** (haasonsaas, MIT). Rule-based image analysis:
  layout score 0–100, balance, grid alignment, hierarchy, colour harmony, WCAG
  contrast ([glama](https://glama.ai/mcp/servers/haasonsaas/design-critique-mcp)).
  These are measurable heuristics, not judgement about meaning or fit to a brief.
- Prompt-level "anti-slop" skills: Anthropic's frontend-design skill, which names
  the failure as convergence to "on distribution" outputs
  ([Claude blog](https://claude.com/resources/articles/improving-frontend-design-through-skills)),
  and community ban lists ([ux-skill wiki](https://github.com/Laith0003/ux-skill/wiki/Anti-AI-slop-ban-list)).
  They tell the agent what to avoid. They do not supply evidence or examples.

### F. Image-generation MCPs

Many community servers wrap Replicate/Flux, OpenAI gpt-image, Google Imagen,
fal and OpenRouter ([GongRzhe](https://github.com/GongRzhe/Image-Generation-MCP-Server),
[lansespirit](https://github.com/lansespirit/image-gen-mcp),
[mcpimg](https://cdn.jsdelivr.net/npm/mcpimg@1.0.2/README.md),
[iplanwebsites](https://mcpservers.org/servers/iplanwebsites/image-mcp)).
They take a prompt and return a file or URL. None I found records why an image
was generated that way, what it was meant to achieve, or provenance beyond what
the vendor embeds. Generation is commodity plumbing.

## Answer to the key question

**Does any existing MCP return licence-aware, ranked visual references with reasons?**

I found none that does all three.

- Licence-aware: `open-museum-mcp` (strict gate, confidence, citations), plus
  Openverse/Unsplash wrappers that pass licence fields through unverified.
- Ranked for a design goal: Mobbin and Refero search by natural language, but
  their ranking method is undocumented ([mcp.md](https://mobbin.com/mcp.md),
  [getting started](https://doc.refero.design/mcp/getting-started.md)).
  `open-museum-mcp` documents no ranking.
- With reasons: Refero's style records carry do/don't rules, and its skill makes
  the agent attribute decisions to references. Nobody returns "this image
  shows technique X, visible as evidence Y, likely producing effect Z, with
  documented intent W (or none)".

This is a negative finding from a ~40-lookup search, not a complete audit.
Registries hold thousands of servers, and a small project could exist that I
missed. Refero's Tools page (doc.refero.design/mcp/tools.md) was not read and
might return more structure than its overview shows.

## What the agent response would need to beat these

From the gaps above, a reference result that is clearly better than the
alternatives would carry:

1. Image URL + local path, with the **rights record**: licence, source rule
   that decided it, credit line, date checked. `open-museum-mcp` sets the bar.
2. **Technique** from a fixed taxonomy, with **observable evidence** in the
   image. No competitor has this.
3. **Possible effect**, kept separate from **documented intent**. Only from
   source metadata, else marked absent.
4. **Review state**: machine-only, model-reviewed, human-locked. No competitor
   exposes this.
5. **Why it ranked here** for this brief: the matched goal, operation and
   technique path in the connections graph.
6. **Use constraint**: "reference only" vs "may publish with credit", so the agent
   can tell the user which images can ship.
