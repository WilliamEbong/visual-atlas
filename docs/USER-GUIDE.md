# Visual Atlas user guide

Visual Atlas finds free-to-use images, files them by the visual techniques that make them work, explains
from visible evidence why they may work, and helps you use those ideas in your own projects. Everything
runs on your computer.

- [1. Basic ideas](#1-basic-ideas)
- [2. Install and open](#2-install-and-open)
- [3. Set up AI (optional)](#3-set-up-ai-optional)
- [4. Find images](#4-find-images)
- [5. Grow my library](#5-grow-my-library)
- [6. The library](#6-the-library)
- [7. An image, its evidence and its credits](#7-an-image-its-evidence-and-its-credits)
- [8. Correct a reading](#8-correct-a-reading)
- [9. Explore goals and techniques](#9-explore-goals-and-techniques)
- [10. See connections](#10-see-connections)
- [11. Help with my project](#11-help-with-my-project)
- [12. Collections](#12-collections)
- [13. Compare](#13-compare)
- [14. Jobs: progress, pause, cancel, resume](#14-jobs-progress-pause-cancel-resume)
- [15. Where images come from, and how permission is checked](#15-where-images-come-from-and-how-permission-is-checked)
- [16. Credits and exports](#16-credits-and-exports)
- [17. Back up and restore](#17-back-up-and-restore)
- [18. Using Visual Atlas from Claude Code or Codex](#18-using-visual-atlas-from-claude-code-or-codex)
- [19. Editing the taxonomy](#19-editing-the-taxonomy)
- [20. Troubleshooting](#20-troubleshooting)

## 1. Basic ideas

| Word | Meaning |
|---|---|
| **Goal** | What you want an image to do: make one thing stand out, show scale, create calm… |
| **Operation** | What a technique does: contrast, isolate, repeat, frame, juxtapose… |
| **Domain** | The visual variable it works on: colour, light and value, scale, position, gaze… |
| **Technique** | A concrete, nameable move, such as *negative space isolation* or *leading lines*. One technique can serve several goals; one image can use several techniques. |
| **Reference** | An image in your library, with its source and licence record. |
| **Reading** (annotation) | A technique proposed for one image, with the visible **evidence**, a hedged **possible effect** and a **review state**. |

Review states are always honest:

| State | Meaning |
|---|---|
| ○ proposed by a model | One assistant suggested it after looking at the picture. |
| ◐ agreed by a second model | A different assistant looked at the picture and agreed. This is not a human review. |
| ● confirmed by you | You confirmed or wrote it. Later analysis never changes it. |
| ✕ rejected | You (or the evidence) ruled it out. It stays rejected. |

Style, medium, subject and period describe an image; they are kept apart from the techniques, which
describe how it works.

## 2. Install and open

**Windows, no terminal:**

1. Download `VisualAtlas-<version>.zip` from the [Releases page](https://github.com/WilliamEbong/visual-atlas/releases/latest).
2. Right-click the zip → **Properties** → tick **Unblock** → **OK**. Extract it to a folder you keep
   (for example `Documents\VisualAtlas`).
3. Double-click **Install Visual Atlas**. It installs what it needs (uv and Python), adds the starter
   library and puts a **Visual Atlas** icon on your Desktop and Start menu. It takes a few minutes the
   first time.
4. Double-click the icon whenever you want to work. Visual Atlas opens in its own window. Closing the
   window stops it a few minutes later (a running job finishes first).

To update, download the newer zip, extract it over the old folder and run **Install Visual Atlas** again.
Your library is not touched. To remove Visual Atlas, delete its folder and the two shortcuts; your
library stays in `%USERPROFILE%\VisualAtlas` until you delete that too.

**Where your library lives:** `%USERPROFILE%\VisualAtlas` (database, images, backups, exports). It is
kept out of OneDrive on purpose: cloud sync can damage a database that is in use. To use another
folder, set the `VISUAL_ATLAS_HOME` environment variable.

**From source (any platform, developers):** Python 3.14, Node 24, [uv](https://docs.astral.sh/uv/):

```
git clone https://github.com/WilliamEbong/visual-atlas.git
cd visual-atlas
uv sync
npm --prefix web ci
npm --prefix web run build
uv run atlas starter-import
uv run visual-atlas
```

## 3. Set up AI (optional)

Browsing, searching, filtering, collections, comparison, credits and backups work with no AI at all.
AI is used only to **look** at pictures (describe what is visible and name techniques), to turn your
words into searches, to compare images and to suggest project directions.

Visual Atlas uses the assistants already installed on your computer, signed in with your own
subscription. It never reads, stores or sends your passwords or tokens.

| Assistant | Install | Sign in once |
|---|---|---|
| **Codex** (ChatGPT plan) | `npm install -g @openai/codex` | run `codex login` in a terminal |
| **Claude Code** (Claude plan) | see [claude.com/claude-code](https://claude.com/claude-code) | run `claude` in a terminal and sign in |

Open **Settings → AI setup** to see whether each one is ready. Choose which one **analyses images** and
which one does the **second-model check**. The recommended split is Codex analysing and Claude Code
checking, so the work is spread over both plans. A **daily AI limit** (number of calls) protects your
plan; jobs pause politely when it is reached.

**Practice mode** answers instantly without any model. Its readings are clearly marked as practice and
are only for trying the workflow.

How the assistants are run: each call uses a fixed command with every tool switched off (no file,
shell, web or browser access), an empty temporary folder, and a strict answer format. Picture titles,
museum descriptions and any text inside images are passed as untrusted data, never as instructions.
Answers that break the format — unknown technique names, evidence that cites nothing, links, a claim
of the artist's intention that the museum record does not support — are discarded, never saved.

## 4. Find images

**Find images** turns a request into searches across the open collections.

1. Describe what you want to see, in plain words. Optionally pick a **goal**, a **technique**, a
   **subject**, an **intended use**, a **shape** (landscape, portrait, square), a **main colour** and how
   many new images you want.
2. Choose which collections to search and who analyses.
3. Select **Find images**. The job runs in the background; you can keep browsing.

What happens, in order:

1. **Searching** — your request becomes a few short keyword searches (planned by the assistant; if it is
   unavailable, Visual Atlas uses the search hints stored with each technique).
2. **Checking permissions** — every result's licence is checked in code against the museum's own record.
   Unclear means skipped.
3. Duplicates and near-duplicates, very small or blank images, and images outside your shape or colour
   filter are skipped **before** any AI is used.
4. **Analyzing** — the assistant describes what it sees and proposes techniques; the second assistant can
   check each reading.
5. **Ready** — only images with at least one clear technique are added.

The panel shows how many were checked, how many were free to use, what was added, and why the rest
were skipped.

## 5. Grow my library

**Find images → Fill gaps in technique coverage** looks for examples of the techniques that have the
fewest examples in your library. It uses each technique's curated search hints, so no AI is needed for
planning. Run it a few times to build a balanced library.

## 6. The library

- **Search** finds words in titles, makers, what the assistant saw, and technique names and aliases.
- **Filters**: technique, goal, shape, source, review state, main colour and favourites. **Sort** by
  newest, oldest, title, maker, most techniques, most colourful, lightest or darkest. Filters live in
  the address, so Back and reload keep them.
- Use the arrow keys to move between images; Enter opens one.
- **+ Compare** adds an image to the comparison tray (up to four).
- If a job stopped before analysing some downloaded images, a notice offers **Analyse them now**.

## 7. An image, its evidence and its credits

- **What you can see** — numbered observations of the picture, each with where it is. Open questions
  are listed as *Left open*. These are a model's description of the pixels, not a catalogue record.
- **Why it may work** — each technique with its **evidence** (the observations it rests on), a hedged
  **possible effect**, its review state, who proposed it and who checked it.
- **Documented intent** appears only when the museum's own record states the maker's intention.
- **Related images** share techniques with this one.
- **Usage and credits** — the licence label (for example *CC0 — source checked* or *Free with attribution
  — credit included*), the exact credit line, the licence link, what was checked and when, restrictions,
  and a link to the source page. Labels describe what was checked; they are not legal advice. Check the
  source before publishing.
- **Remove from library** deletes the image, its copies and readings; it will not be collected again.

## 8. Correct a reading

On any reading:

- **✓ Confirm** — mark it confirmed by you.
- **✕ Reject** — rule it out. It stays rejected even if the image is analysed again.
- **Edit** — rewrite the evidence (one point per line) and the possible effect.
- **Add a technique** — record one the assistants missed, with the evidence you see.

Every change is kept in the **annotation history** (who, what, when). Your decisions always win over
later model output.

## 9. Explore goals and techniques

**Explore** starts from goals. A goal page lists the techniques that can serve it. A technique page
explains it: definition, how it works, where to look, when it may help, what it is often confused with
and how to tell, its limits and a counterexample, related techniques, and the examples in your library.
Definitions are Visual Atlas's own working definitions; the source links are background reading.

## 10. See connections

**See connections** draws one focus at a time (a goal, a technique or an image) and what it connects to.
Select a node to make it the new focus; select the centre to open it. Use **Zoom in**, **Zoom out** and
**Fit**, or drag to pan. **List** shows the same connections as text (it opens by default on a phone).

## 11. Help with my project

Describe a project — audience, message, format, mood, constraints — and select **Suggest directions**.
You get three to five directions, each with the idea, why it suits the brief, the techniques it uses,
reference images **from your library** (never invented), how to execute it and the tradeoffs. **Keep** the
ones you like; asking again replaces only the unkept ones. Briefs and suggestions are saved.

## 12. Collections

Save images to collections from any image page. A collection page lets you rename it, reorder images
(← →), remove images, download its **credits**, or **Export zip**: the original files, `CREDITS.md` and
`annotations.json`.

## 13. Compare

Pick two to four images with **+ Compare**, then **Compare side by side**. Shared techniques are
highlighted. **Ask an assistant to compare them** writes a saved comparison (what they share, how they
differ, one note per image).

## 14. Jobs: progress, pause, cancel, resume

Searches and analyses run one job at a time in the background. **Jobs** lists them. **Pause** stops after
the current step; **Resume** continues where it stopped; **Cancel** stops (images already added stay).
Jobs survive closing the app or a crash: unfinished work continues the next time Visual Atlas (or the
`atlas worker` command) runs, without repeating finished steps. If an assistant reaches its usage limit
the job pauses with a plain message; resume later or switch assistant in Settings.

## 15. Where images come from, and how permission is checked

| Source | Rule checked on every item |
|---|---|
| Art Institute of Chicago | `is_public_domain` is true and an image exists (CC0) |
| The Met | `isPublicDomain` is true and an image exists (CC0) |
| Cleveland Museum of Art | `share_license_status` is `CC0` |
| Smithsonian Open Access | the image media itself is marked `CC0` (metadata alone is not enough) |
| Wikimedia Commons | the file's licence is CC0, public domain or CC BY (with author and licence link); share-alike, non-commercial and no-derivatives licences are excluded |

Unsplash, Pexels and Pixabay are **not used**: their terms either require hotlinking or restrict AI and
machine-learning use in ways that are unclear for this app. Settings → *Image sources and permissions*
shows every source, its rule, its evidence links and when it was last checked. The policies live in
`atlas/data/source_policies.json`.

Smithsonian works with a shared demonstration key that allows only a few searches per hour. For more,
get a free key at [api.data.gov](https://api.data.gov/signup/) and put `SMITHSONIAN_API_KEY=your-key` in
a `.env` file in your library folder.

For a researched list of free-to-use inspiration sites (and popular sites that are *not* free to use),
see [FREE-IMAGE-SOURCES.md](FREE-IMAGE-SOURCES.md).

## 16. Credits and exports

- **Settings → Download all credits** (Markdown or CSV), or a collection's **Credits** button.
- Every credit carries the licence name and link, the exact attribution text and the source URL.
- **Export zip** on a collection includes credits automatically.

## 17. Back up and restore

**Settings → Back up now** saves the whole library (database, images, readings) into
`%USERPROFILE%\VisualAtlas\backups`, with a manifest of checksums. **Restore…** checks the backup first,
makes a safety backup of what you have now, then swaps it in. Restoring is refused while a job is
running. From a terminal: `uv run atlas backup` and `uv run atlas restore <file name>` (close the app first).

## 18. Using Visual Atlas from Claude Code or Codex

The project folder has identical `CLAUDE.md` and `AGENTS.md` files, so either assistant can maintain it.
Useful commands (run in the project folder):

| Command | What it does |
|---|---|
| `uv run atlas find "foggy harbours, silhouettes" --count 6` | queue and run a Find job |
| `uv run atlas grow --count 8` | fill technique gaps |
| `uv run atlas analyze` | analyse images waiting for analysis |
| `uv run atlas jobs` / `uv run atlas job <id> pause|resume|cancel` | see and control jobs |
| `uv run atlas worker` | continue unfinished jobs (safe alongside the app: a lease stops two workers sharing a job) |
| `uv run atlas library` / `uv run atlas coverage` | list images / technique coverage |
| `uv run atlas credits --format csv` | print credits |
| `uv run atlas backup` / `uv run atlas restore <name>` | back up / restore |
| `uv run atlas doctor` | check the library folder, knowledge files and both assistants |

Jobs and their results use one shared JSON format (`schemas/job.schema.json`,
`schemas/analysis.schema.json`), so a job started in the app can be finished by either agent.

## 19. Editing the taxonomy

Goals, operations, domains and techniques live in `atlas/data/taxonomy.json`; source rules in
`atlas/data/source_policies.json`. Edit them, then run `uv run atlas taxonomy check` (it reports any
broken reference) and restart the app. A technique still used by readings in your library cannot be
removed until those readings are rejected or removed.

## 20. Troubleshooting

| Problem | What to do |
|---|---|
| Windows says the installer is from the internet | You skipped **Unblock**: right-click the zip → Properties → Unblock, extract again. |
| “Port 8775 is used by another program” | Close that program, or add `VISUAL_ATLAS_PORT=8776` to a `.env` file in your library folder. |
| AI setup shows “not signed in” | Sign in once in a terminal (`codex login` or `claude`), then **Check again**. |
| A job paused with a usage-limit message | Wait for your plan to reset, or switch assistant in Settings, then **Resume**. |
| A source keeps failing | Museums occasionally go offline; the job records the failure and moves on. Try again later. |
| Smithsonian searches fail | The shared demo key is limited; add your own free key (section 15). |
| Something else | See `%USERPROFILE%\VisualAtlas\visual-atlas-app.log`, or run `uv run atlas doctor`. |
