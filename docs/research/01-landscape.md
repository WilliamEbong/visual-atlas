# 01 — Landscape: reference tools and licence-clean image sources

Research date: 2026-11-22. Prices come mostly from vendor pages or third-party
directories and drift often. Where sources disagreed, the disagreement is noted.
"Not verified" means I looked and found no reliable source.

## 1. Reference and mood-board tools

| Tool | Who uses it / job | How search works | Licence / provenance | Price | API / agent access |
|---|---|---|---|---|---|
| Are.na | Researchers, artists, designers; slow, connected collecting in "channels" | Text; Premium searches full block content and adds advanced filters ([help](https://help.are.na/docs/getting-started/premium-features), [roadmap](https://are.na/roadmap)). No visual similarity found | Keeps source URL of saved blocks; no licence checking found | Free; Premium; Supporter renamed Plus Plus and rising from $120 to $150/yr on 1 Dec 2026 ([editorial](https://www.are.na/editorial/supporter-to-plus-plus)) | Public API, tiered rate limits 30–600/min ([developers](https://www.are.na/developers)); official hosted MCP at `mcp.are.na/mcp` ([repo mirror](https://github.zuike.workers.dev/aredotna/mcp)) |
| Cosmos (cosmos.so) | Creatives curating visual "clusters"; Pinterest alternative without ads | Keyword, hex colour, visual similarity; says it uses AI to surface original artist and source ([llms.txt](https://www.cosmos.so/llms.txt)) | Claims source/artist attribution research; no licence status | Free; Premium $8/mo per its own llms.txt, not independently confirmed ([llms.txt](https://www.cosmos.so/llms.txt)) | No public API; one unofficial MCP calls its private GraphQL with a session token ([glama](https://glama.ai/mcp/servers/mrmos/cosmos-mcp)) |
| Pinterest | Mass-market inspiration, also widely used by designers | Visual + text, recommendation feed | Labels suspected gen-AI Pins (Apr 2025) and lets users see less AI content in art, beauty, fashion, decor (Oct 2025) ([newsroom](https://newsroom.pinterest.com/news/introducing-gen-ai-labels), [newsroom](https://newsroom.pinterest.com/news/pinterest-rolls-out-new-tools-to-give-users-more-control-over-gen-ai-content/)); no reuse licence | Free to use (not separately verified) | API v5; an official MCP announced, status reported as partner alpha / read-only, sources conflict ([scalekit](https://www.scalekit.com/blog/pinterest-mcp-vs-api), [Pinterest community](https://community.pinterest.biz/t/introducing-the-pinterest-mcp-server/51358.md)) |
| Eagle | Designers/illustrators managing large local image libraries | Local tags, folders, colour, file metadata | Stores source URL of grabbed images; no licence checks found | One-time ~$29.95, two devices, 30-day trial ([Capterra UK](https://www.capterra.co.uk/software/184384/eagle), [GetApp](https://www.getapp.com/all-software/a/eagle/)) | Has a plugin system and local API (not verified this session) |
| PureRef | Concept artists, 3D, illustrators; a floating canvas of refs while working | None to speak of; it is a board, not a search tool | None | Pay-what-you-want for personal use; custom amount reported defaulting to $20 in 2026; business licences/subscriptions ([support page](https://pureref.com/support_us.php), [CG Channel 2024](https://www.cgchannel.com/2024/05/pureref-2-0-is-out), [CG Channel 2026](https://www.cgchannel.com/?p=173921)) | None found |
| Savee | Designers saving and discovering high-taste inspiration; 1.2M users claimed ([savee.com](https://savee.com/)) | AI recommendations, search by image, colour name/hex ([savee.com](https://savee.com/), [search post](https://inspire.savee.com/new-search-on-savee/)) | None found | Free + paid upgrade; price not confirmed ([upgrade](https://savee.com/upgrade), [TrustRadius](https://www.trustradius.com/products/savee/pricing)) | None found |
| Same Energy | Anyone browsing by "vibe" | Pure image-embedding similarity (CLIP-like), no tags; ~19M images from Reddit, Instagram, Pinterest ([about](https://same.energy/about), [Jacob Jackson](https://jacobjackson.com/searching-for-style/)) | None | Free, ad-free ([PetaPixel](https://petapixel.com/2021/02/10/same-energy-is-a-visual-search-engine-that-finds-similar-photos-in-a-snap/)) | No official API; unofficial MCP on its unauthenticated endpoint ([mcpmarket](https://mcpmarket.com/server/same-energy)) |
| Milanote | Creative teams organising briefs and boards | Board organisation, not discovery | None | Free (100 notes, 10 uploads); ~$9.99–12.50/mo individual ([Software Advice](https://www.softwareadvice.com/whiteboard/milanote-profile/)) | Not verified |
| Mobbin | Product/UI designers studying real app screens | Natural-language search over ~621,500 screens, flows, sections ([BusinessWire](https://www.businesswire.com/news/home/20260511053592/en/Mobbin-Launches-MCP-Server-Giving-AI-Tools-621500-Real-App-Screens-to-Reference)) | Screens are third-party product UI; MCP guide says "do not copy protected designs... verbatim" ([mcp.md](https://mobbin.com/mcp.md)) | Free/Pro/Team/Enterprise ([pricing.md](https://mobbin.com/pricing.md)) | Official read-only MCP (beta), paid plans, 60 req/min ([mcp.md](https://mobbin.com/mcp.md)) |
| Refero | Same audience as Mobbin; pitches "give your AI agent design taste" ([hunted.space](https://hunted.space/dashboard/refero)) | Styles, screens, flows, similar screens; 120–125k screens ([Product Hunt](https://www.producthunt.com/p/refero/refero-mcp)) | Not addressed in docs ([getting started](https://doc.refero.design/mcp/getting-started.md)) | Pro/Team/Lifetime; 8,000 MCP calls/month ([getting started](https://doc.refero.design/mcp/getting-started.md)) | Official MCP + companion "research-first" agent skill ([skill](https://doc.refero.design/skill/overview.md)) |
| Flim | Filmmakers, art directors, ad creatives; film/series stills | AI search over ~1.1M+ stills ([CGMagazine](https://www.cgmagonline.com/newswire/flim-ai-video-stills-database-ai), [creati.ai](https://creati.ai/ai-tools/flim-ai/)) | Stills from copyrighted films; reference use only (no licence offered, not verified) | Freemium; ~€12.90 Basic, ~€29.90 Pro, figures inconsistent ([creati.ai](https://creati.ai/ai-tools/flim-ai/), [toolify](https://www.toolify.ai/tool/flim-ai)) | None found |
| ShotDeck | Cinematographers, colourists, directors | Filters by colour, frame size, lighting, lens, time of day, plus semantic (vector) search after redesign ([store](https://store.shotdeck.com), [No Film School](https://nofilmschool.com/shotdeck-redesign)) | Copyrighted film stills, curated by professionals | ~$12.95/mo or $99.95/yr ([help](https://help.shotdeck.com/?p=425)) | None found |
| Kive | Brand/creative teams; library + AI generation | AI-powered search on all plans ([pricing](https://kive.ai/pricing)) | Not addressed | Credit-based Free/Basic/Pro/Enterprise; ~$15–20 Basic, ~$75–100 Pro, sources conflict ([pricing](https://kive.ai/pricing), [alternatives.co](https://alternatives.co/software/kive-ai/pricing)) | Not verified |

### Notes

- **Two jobs, rarely joined.** Discovery tools (Pinterest, Cosmos, Savee, Same
  Energy) find pictures that look right. Board tools (PureRef, Milanote, Eagle,
  Are.na) hold pictures. None of the tools above records *why* an image works.
  Refero comes closest. Its skill tells the agent to name its references and say
  which decision came from each, but it does not judge why a reference succeeds
  ([skill](https://doc.refero.design/skill/overview.md)).
- **Licence is almost nobody's problem.** Most of these libraries are made of
  copyrighted material (film stills, app UI, scraped web images) meant for
  reference, not reuse. Mobbin says so outright: a screen shows a product used a
  design, not that the design worked, and you must not copy it verbatim
  ([mcp.md](https://mobbin.com/mcp.md)). No tool in the table checks whether an image
  may be published.
- **Visual similarity is commodity.** Same Energy showed in 2021 that tag-free
  embedding search over a big corpus is enough to browse by vibe
  ([about](https://same.energy/about)). Cosmos, Savee and ShotDeck all ship some
  form of it now. Visual Atlas should not compete on similarity search.
- **Agent access is new and UI-only.** In 2026 Mobbin, Refero and Are.na all
  launched MCP servers ([BusinessWire](https://www.businesswire.com/news/home/20260511053592/en/Mobbin-Launches-MCP-Server-Giving-AI-Tools-621500-Real-App-Screens-to-Reference),
  [Refero](https://doc.refero.design/mcp/getting-started), [Are.na](https://github.zuike.workers.dev/aredotna/mcp)).
  The two "taste for agents" products (Mobbin, Refero) cover UI screens only, not
  imagery, art or photography.
- **AI images are flooding inspiration feeds.** Pinterest needed labels and an
  opt-down control for AI content in exactly the categories designers use (art,
  decor, fashion) ([TechCrunch](https://techcrunch.com/2025/04/30/pinterest-launches-new-tools-to-fight-ai-slop/),
  [newsroom](https://newsroom.pinterest.com/news/pinterest-rolls-out-new-tools-to-give-users-more-control-over-gen-ai-content/)).
  Museum collections are free of this by construction, which is an underused advantage.

## 2. Museum open-access APIs and licence-clean sources

| Source | Access | Licence signal an app can test | Notes |
|---|---|---|---|
| The Met | No key; ask ≤80 req/s; 470k+ objects ([docs](https://metmuseum.github.io/)) | `isPublicDomain` boolean; `primaryImage` only when Open Access ([docs](https://metmuseum.github.io/)) | Search endpoint returns IDs; one fetch per object |
| Art Institute of Chicago | No key; asks for an identifying `AIC-User-Agent` ([Jentic summary](https://jentic.com/apis/artic.edu/artic.md), [API](https://api.artic.edu/docs)) | `is_public_domain`; CC0 images; IIIF manifests for PD works ([open access](https://www.artic.edu/open-access/open-access-images)) | Some descriptive text is CC BY, not CC0 ([Jentic summary](https://jentic.com/apis/artic.edu/artic.md)) |
| Cleveland Museum of Art | No key in examples ([API](https://openaccess-api.clevelandart.org/)) | `cc0` filter flag; `share_license_status` = CC0 / Copyrighted / Other ([API](https://openaccess-api.clevelandart.org/)) | Image assets for 37k+ works; only CC0 works give CC0 images |
| Smithsonian Open Access | Key via api.data.gov ([devtools](https://www.si.edu/openaccess/devtools)) | CC0 at item level; restricted items get metadata but no media ([FAQ](https://dashboard.si.edu/openaccess/faq)) | 2.8M images at 2020 launch, later 4.4M+ ([Creative Commons](https://creativecommons.org/2020/02/27/smithsonian-releases-2-8-million-images-data-into-the-public-domain-using-cc0/), [DesignTaxi](https://designtaxi.com/news/422024/The-Smithsonian-Has-Released-Over-4M-Free-Images-From-Its-Collections-Online/faq)); CC0 covers copyright only |
| Rijksmuseum | Key required; old APIs deprecated for Linked Open Data / Linked Art APIs ([data overview](https://www.rijksmuseum.nl/en/data/overview), [API docs](https://data.rijksmuseum.nl/docs/api)) | Reproductions and metadata CC0 ([policy](https://www.rijksmuseum.nl/en/data/policy)) | Migration risk for any client written against the old API |
| National Gallery of Art | Daily CSV dump, not an API ([GitHub](https://github.com/NationalGalleryOfArt/opendata)) | Data CC0; images referenced, not included | Needs local ingest |
| Europeana | Key (`wskey`) ([Pro search](https://pro.europeana.eu/page/search)) | `reusability=open|restricted|permission` ([Europeana blog](https://pro.europeana.eu/post/new-media-search-methods-in-the-europeana-api)) | Aggregator; "open" includes CC BY / BY-SA, so per-item rights still matter |
| Wikimedia Commons | Public MediaWiki API | `extmetadata` LicenseShortName etc., which are free text and unreliable for multi-licensed files ([CommonsMetadata](https://www.mediawiki.org/wiki/Extension:CommonsMetadata/en), [Commons MRD](https://commons.wikipedia.com/wiki/Commons:MRD)) | Licence may describe the depicted object, not the photo ([Phabricator](https://phabricator.wikimedia.org/T59465)) |
| Openverse | Public API; low anonymous limits ([npm mcp-openverse](https://www.npmjs.com/package/mcp-openverse)) | Licence fields aggregated, but Openverse "does not verify" them and tells users to check independently ([about, archived](https://webcf.waybackmachine.org/web/20231210110130/https://openverse.org/about)) | Good breadth, weak guarantees |

### Notes

- **The sources disagree on what "open" means.** Booleans (Met, AIC), enums
  (Cleveland, Europeana), free text (Commons) and unverified aggregation
  (Openverse) all coexist. A deterministic per-source rule set, as Visual Atlas
  already has in `atlas/data/source_policies.json`, is the right shape. The
  evidence above supports keeping "unclear ⇒ ineligible".
- **CC0 is not "safe for every use".** The Smithsonian says CC0 only covers
  copyright and other permissions may still apply
  ([FAQ](https://dashboard.si.edu/openaccess/faq)). That matches the project invariant.

### Existing MCP servers that wrap these sources

| Server | Covers | Rights handling | Ranking / reasons |
|---|---|---|---|
| `open-museum-mcp` (cfpramod) | Met, Cleveland, AIC, Commons, Europeana, Walters, SMK, Wellcome, NGA, Harvard, Getty; Smithsonian and Rijksmuseum planned ([README](https://raw.githubusercontent.com/cfpramod/open-museum-mcp/main/README.md)) | **Strict rights gate**: "Missing or unclear indicators drop the record"; licence object with `verificationSource`, `verifiedAt`, `confidence`; `cite` tool gives three citation styles ([README](https://raw.githubusercontent.com/cfpramod/open-museum-mcp/main/README.md)) | No ranking described; no visual or design reasoning; dominant-colour extraction planned |
| `metmuseum-mcp` (mikechao) and others | Met only ([glama](https://glama.ai/mcp/servers/mikechao/metmuseum-mcp)) | Returns Open Access image when present | None |
| `museum-mcp-server` (PyPI) | Met, AIC ([PyPI](https://pypi.org/project/museum-mcp-server/)) | Not detailed | None |
| `rijksmuseum-mcp` (r-huijts) | Rijksmuseum, needs key ([mcpservers.org](https://mcpservers.org/servers/r-huijts/rijksmuseum-mcp)) | Not detailed | None |
| `mcp-openverse` and others | Openverse ([glama](https://glama.ai/mcp/servers/@neno-is-ooo/mcp-openverse)) | Returns licence and attribution fields as Openverse reports them | None |

`open-museum-mcp` is the closest overlap with Visual Atlas's source layer. It
already does much of the licence gate as a free MCP. Visual Atlas cannot claim
"licence-aware museum search for agents" as unique. Its difference has to be
what it adds on top: technique readings, evidence, connections and human-locked
corrections. I did not check this server's maturity (stars, release cadence, tests).
