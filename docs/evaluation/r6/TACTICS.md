# Tactics for each root cause

"Kit" means `C:\Users\Owner\OneDrive\Documents\William Web Design`. Its photo-generation rules don't apply here; its sequencing, de-duplication, truth and copy rules do.

## A. Content and fit of picks

**A1. One plan for every set of pictures.** Before any strip renders (way, goal, mood or direction), one pass over its candidates drops near-duplicates, gives each picture at most one lead role, and keeps two pictures with the same maker and title stem from sitting side by side. *Source:* Kit `rules/IMAGE-TASTE.md` §2 ("a different compositional device in every frame") and §7.3a (none reads as the same photograph); Kit `rules/PROCESS.md` (`coverage.mjs`: no family twice in a row); photobook editing (no near-identical frames on one spread).

**Near-duplicates (two Podangis, two Mammals Hall).** Store a 64-bit dHash per thumbnail (Pillow, 9×8 greyscale). Hamming distance of 10 or less, or the same maker plus the same `cleanTitle` stem, makes one group. Show the best of the group marked "+1 version"; the image page lists the rest. *Source:* Eagle's duplicate finder; Cosmos and Savee group near-identical saves; museum "related impressions" appear on the object page, not in the grid.

**One picture leads two techniques.** Assign leads greedily: techniques with the fewest strong candidates choose first, and each takes its best candidate not already taken. A unit test fails if any picture leads twice. Run the same rule across a saved answer's directions (the Projects poster) and fix `web/src/lib/demo.ts`. *Source:* Kit IMAGE-TASTE §2 (one idea per frame); museum highlight sets (one object per theme).

**The front-page sample doesn't show its brief.** Pick the brief from what the library can answer. Try five briefs, check each one's top four picks by eye, ship the one whose picks plainly show it, lock those picks as curated, and test that they stay. *Source:* Kit IMAGE-TASTE §7.3a (audit the series before anyone sees it); Are.na channels and museum "Highlights", picked by a person.

**Negative space that is really paper margin.** For prints and plates, trim any near-uniform border first (a brightness-variance scan from each edge), then measure the empty area inside. A pick whose emptiness is mostly border is demoted. *Source:* Kit IMAGE-TASTE §4 (judge what the frame shows); plate convention (the image is what lies inside the platemark).

**Weak proposals shown as examples (Divan Japonais as silhouette).** Only human-reviewed readings, or `model_reviewed` readings above a set confidence, count as "examples". The rest go in a muted "Possible, not yet checked" line. *Source:* the project's evidence/proposal invariant (`CLAUDE.md`); catalogue attribution grades ("attributed to", "circle of") at the Rijksmuseum and the Met.

**Word-only matches look like answers.** Visual or technique matches go in the main row. Word-only matches go in a separate line at half the height, labelled "Matched by words only". *Source:* impeccable `reference/layout.md` (group by meaning; different content looks different); Cosmos and Savee rank by what the picture shows; museum search keeps keyword hits apart from curated "related".

**Thin warm set.** Run `atlas grow` on "warm and communal" (shared tables, festivals, gatherings) until it has at least five reviewed picks. With fewer than three, the screen says so in one line and offers "Find more for this mood". *Source:* impeccable `reference/clarify.md` ("explain the state and provide the next useful action"); `reference/onboard.md` empty-state types.

## B. Picture-row system

**B1. Lay out rows in code, not with flex-grow.** The `.justified` flex-grow rule (`styles.css` lines 157–158) and the 1.6× `max-width` cap leave rows ragged and last rows orphaned. Replace them with `rows(aspects, width, target, gap)`, which breaks rows greedily at the target height and scales each row to fill the width exactly. The last row depends on the screen:
- **Capped strips** (More like this, Also shows, Recent, ways): show only whole rows, with the rest behind "n more".
- **Full lists** (Library): if the last row fills less than 75%, rebalance the last two rows. A lone leftover picture never shows.
- **End of an infinite scroll:** the last row stays at target height, left-aligned.
Re-run it on resize; assert results at 375, 768 and 1440 px. *Source:* the Flickr and Google Photos justified layout (`flickr/justified-layout`, MIT; 40 lines of our own is enough); impeccable layout, Extremes check.

**B2. Sets of one, two and three get their own layouts.** One picture becomes a single plate up to 60% of the width with its caption beside it. Two make a diptych at equal height. Three or more use B1. *Source:* photobook editing (one picture to a page, caption opposite); museum object pages.

**B3. One phone pattern on every screen.** Under 600 px, every strip is a horizontal scroll-snap row at 220 px with the next picture's edge showing. Library and Find use two columns. Nothing switches pattern partway down. *Source:* Savee and Cosmos mobile; impeccable layout ("responsive behaviour is structural").

## C. Screen leftovers

**Library techniques shown on hover only.** Always show the first technique as a muted line under the title. Remove the `display: none` at `styles.css` lines 496–497, and keep only the maker on hover. *Source:* impeccable `reference/craft-floor.md`, Coverage; Cooper Hewitt and Met grids, where the object type is always visible.

**Technique count (6 against 5); hero crosses the rule.** Take the count from the array the strip renders, or say "6 in your library, 5 shown". Hold the hero inside its band (`max-height`, `object-fit: contain`). *Source:* Kit `rules/COPY.md` §3, Truth.

**Image page title block bottom-aligned.** Set `align-self: start` and use the museum tombstone order: title (serif), maker and date, medium and size, then credit and licence (small mono). *Source:* Met and Rijksmuseum object pages; Kit `rules/CRAFT.md` §2 (mono for captions and data only).

**Explore goals are text-only cards.** Each goal gets a lead plate (one-to-one, A1) captioned with the goal name, laid out by B1, with no boxes. *Source:* impeccable craft-floor, Refuse (same-size cards as page structure); taste-skill redesign (generic card look); Are.na channel covers.

**Compare.**
- The label column becomes `max-content`, capped at 160 px, instead of 30%.
- Scores become bars on one shared 0–1 scale, labelled once in the header.
- A missing value is a blank cell, not a dash.
- "Show differences only" is on by default and hides rows that are all the same or all empty.
- On phones, the first column is sticky and the pictures scroll sideways.
*Source:* Tufte's small multiples (one scale, label once); the "show differences only" switch on product comparison tables.

**Projects pictures tiny and uneven.** Each direction gets one lead plate at 240 px, plus up to three supporting pictures in one B1 row. Nothing is smaller than 120 px. *Source:* Are.na and Cosmos covers; photobook practice (the lead picture is the largest).

## D. Reason copy

**Reasons describe pixels, not fit.** Each reason gets two lines. Line 1: "Fits *‹brief phrase›*: ‹how the picture does it›", in 20 words or fewer. Line 2: the observed evidence, muted. If line 1 shares no word stem with the brief or the technique's effect, fall back to the technique's guidance sentence. Example: "Fits *one small figure*: the walker fills a hundredth of the frame against open snow." *Source:* Kit `rules/COPY.md` §1 (specific; every beat names its referent); the evidence/effect invariant; museum wall labels (the reason to look first, the detail after).
