# Visual Atlas user guide

Visual Atlas helps you find reference images, examine the techniques they use, and apply those ideas to a design brief. Your library includes the pictures, their recorded usage terms, and explanations you can question or correct.

This guide covers v0.4.0. The online demo is for browsing; searches for new images, editing and AI requests need the installed app. A public release or demo may be older than the source version described here.

If you've just installed the app, start with [Your first session](#your-first-session). You can do that walkthrough without an assistant account.

## Contents

- [Install and update](#install-and-update)
- [Your first session](#your-first-session)
- [Set up an assistant](#set-up-an-assistant)
- [Find new images](#find-new-images)
- [Correct the interpretation of a request](#correct-the-interpretation-of-a-request)
- [Fill gaps in your library](#fill-gaps-in-your-library)
- [Search and organise the library](#search-and-organise-the-library)
- [Read an image page](#read-an-image-page)
- [Confirm or correct an image reading](#confirm-or-correct-an-image-reading)
- [Explore visual techniques](#explore-visual-techniques)
- [Follow connections](#follow-connections)
- [Compare images](#compare-images)
- [Get directions for a project](#get-directions-for-a-project)
- [Make a collection and export it](#make-a-collection-and-export-it)
- [Manage jobs and usage limits](#manage-jobs-and-usage-limits)
- [Understand sources and usage terms](#understand-sources-and-usage-terms)
- [Back up and restore](#back-up-and-restore)
- [Use the command line](#use-the-command-line)
- [Edit the taxonomy](#edit-the-taxonomy)
- [Troubleshooting](#troubleshooting)

## Install and update

### Windows installation

1. Download `VisualAtlas-<version>.zip` from the [Releases page](https://github.com/WilliamEbong/visual-atlas/releases/latest), or use a local release zip you have built.
2. Right-click the zip and open **Properties**. If **Unblock** appears, tick it and choose **OK**.
3. Extract the zip to a short, permanent folder, such as `C:\VisualAtlas`. Open the extracted folder; don't run the installer from inside the zip.
4. Double-click **Install Visual Atlas.cmd**. The installer sets up uv and Python if needed, installs the app, imports the starter library, and creates Desktop and Start menu shortcuts. The first installation needs an internet connection.
5. When the app opens, choose **Look around first** to browse the starter images. Use the **Visual Atlas** shortcut for later sessions.

The app normally opens in an Edge or Chrome app window. If neither is available, it opens in your default browser. After you close the window, the local server stops after roughly three minutes without activity. A running job keeps it active; use **Pause** or **Cancel** in Jobs if you want that work to stop.

### Where your work is saved

The application folder contains the software. Your library is a separate folder:

```text
%USERPROFILE%\VisualAtlas
```

Paste that path into File Explorer's address bar to open it. It contains the database, images, backups and exports. Keep this folder outside OneDrive, Dropbox and other sync services, because a live database should not be synced between machines.

The `VISUAL_ATLAS_HOME` environment variable selects a different library folder. Set it before launching the app. A different folder opens a different library; it does not move your existing work.

### Update an existing installation

1. In **Settings**, choose **Back up now**.
2. Let active jobs finish, or pause them. Close Visual Atlas and allow its server to stop.
3. Extract the newer release over the application folder and run **Install Visual Atlas.cmd** again.
4. Open the app and check your library. The installer adds any missing starter references without duplicating existing ones or replacing your personal corrections.

When an upgrade changes the database structure, the app saves a copy of the old database before applying it. Version 0.4 uses the same database structure as 0.3. Removing the application folder and shortcuts does not remove the separate library folder.

### Run from source

Install Git, Node.js 24 and [uv](https://docs.astral.sh/uv/), then run these commands in a terminal:

```sh
git clone https://github.com/WilliamEbong/visual-atlas.git
cd visual-atlas
uv sync
npm --prefix web ci
npm --prefix web run build
uv run atlas starter-import
uv run visual-atlas
```

uv supplies the project's Python 3.14 environment. To use a regular browser, run `uv run atlas serve` instead of the last command and open the address it prints. Keep that terminal open; Ctrl+C stops the server.

After updating a source checkout, run `uv sync`, the two npm commands, and `uv run atlas starter-import` again. Merely launching the app does not import additions to the starter pack.

## Your first session

Try this with the starter library. It takes you from an intention to a pair of examples without making an AI call.

1. Open **Explore**, then **See connections**.
2. In **Start or focus on**, choose **Make one thing stand out**.
3. In the context panel, follow **Isolate**, then **Space and depth**.
4. Follow **Negative space isolation** in the map or List. Its explanation describes a subject surrounded by a large, quiet area.
5. Scroll to **Examples in this exploration**. Read the count and select **Show more examples** to reveal more of the library.
6. Open an image. Read **What you can see**, **Why it may work**, and **Usage and credits**. Use **Return to your exploration** to go back.
7. Choose **+ Compare** on two examples, then **Compare side by side**. Look at the amount of space around each subject and the technique table below the pictures.
8. Select **Return to your exploration**. Your focus, Map/List view, expanded examples and trail are restored.

You are following related techniques, not a strict family tree. One technique can use several operations and domains. You can take another route through the same collection.

## Set up an assistant

You can browse, search your existing library, compare pictures side by side, edit readings, manage collections and export credits without AI. An assistant is needed to analyse newly found images, write a comparison, or suggest project directions.

Visual Atlas uses an installed **Codex CLI** or **Claude Code**, signed in with your own account. A ChatGPT browser session alone does not establish a Codex CLI sign-in.

1. Install the assistant using its official instructions: [Codex CLI](https://developers.openai.com/codex/cli/) or [Claude Code](https://claude.com/claude-code).
2. In a terminal, run `codex login` for Codex, or `claude` for Claude Code, and complete the sign-in.
3. Open **Settings → Assistants** in Visual Atlas and choose **Check again**.
4. Select the assistant that will analyse images. If both are ready, you can choose the other for the second-model check. If you have only one, use the corresponding single-assistant option in **Who analyses** on Find images.
5. Set **Daily AI limit (calls)** to a limit you are comfortable with. This counts calls, not money, and does not replace your account's own usage limits.

The readiness check confirms that the assistant can be found and has the expected setup. A real request can still fail because of authentication, connectivity or account limits. Jobs shows the reason when that happens.

**Practice mode** makes no model calls and produces demonstration answers. Use it to learn the workflow, not to assess an image. Source searches can still require a network connection.

### What is sent outside your computer

The library is stored locally. These actions send specific information to outside services:

| Action | Information sent |
|---|---|
| Search a source | Search terms go to the selected museum or archive service; eligible files are downloaded from it. |
| Plan a Find request with AI | The request and search context go to the selected assistant. |
| Analyse or check an image | The image copy and catalogue details go to OpenAI or Anthropic through the selected assistant. |
| Ask for a written comparison | The selected image copies and their reference information go to the assistant. |
| Suggest project directions | Your original brief, corrected interpretation and summaries of selected library references go to the assistant. |

Those services process requests under the terms of your account. Browsing stored results and correcting a brief's interpretation do not make model calls. You can reopen a saved comparison or project direction without requesting it again.

Each assistant call runs with its tools disabled and a restricted answer format. This limits what the assistant can do during an Atlas task; it does not make the model's interpretation infallible.

### Optional TypeSafe Jev ranking

Jev is off by default. Under **Settings → Project help**, **Rank references with TypeSafe Jev** can reorder the references offered for a project brief. It requires your own `TYPESAFE_API_KEY` in the library folder's `.env` file and is billed to that account.

When enabled, it sends the brief and text about up to 120 references, including titles, creators, dates, summaries and technique names. It does not receive picture files for this ranking step. Jev does not interpret images, decide permissions or check annotations. If it fails, the built-in ranking is used. You do not need it to use project help.

## Find new images

**Library search** searches what you already have. **Find images** searches outside collections and adds new references.

1. Open **Find images** and leave **Find images for a request** selected.
2. In **Describe what you need**, write the subject and the effect you want. For example: "A calm poster about solitude, with one small person in a large empty landscape. Leave space for a title."
3. Read the suggested goals, techniques and subject words below the text. Correct them if needed, following the next section.
4. Use **Goal**, **Technique to look for**, **Subject** and **Intended use** if you want to be more specific. Shape and main-colour filters narrow the results further.
5. Choose **How many new images**. Start with a small request, such as four or six, while you learn which searches work.
6. Check **Who analyses** and the selected **Sources**. The National Gallery of Art is off by default because its first search downloads about 190 MB of catalogue data.
7. Choose **Start finding**. You can keep browsing while the job runs.

The progress panel shows search, permission checks, analysis and the result. The app skips unclear licences, duplicates, near-duplicates, unsuitable files and images outside your chosen filters. The assistant then proposes techniques for usable pictures. A second assistant can check those proposals if you selected one.

The requested count is a target, not a guarantee. When you ask for a technique, an image only counts toward that target if its analysis supports the requested technique. Other useful images may still enter the library. The result explains how many match and how many show other techniques.

Open **Not added** to inspect skipped results. **Stopped short** can mean the job reached its analysis limit; it does not prove the sources have no suitable images. If a second-model check fails, an image may still be added with a proposed reading. It is not marked as checked unless a check completed and was saved.

## Correct the interpretation of a request

The interpretation is a local word-matching suggestion. It can recognise a technique you describe without naming, but it can also miss a phrase or mistake an instruction for a subject.

For the solitude example, look for **Create calm and order**, **Negative space isolation** and **Scale contrast**. The useful subject word is **solitude**. If you specifically need a person rather than any image about solitude, add **person** in the correction editor.

1. Open **Correct this reading**.
2. Tick the goals and techniques you want. Untick suggestions that do not fit. Choosing none is allowed.
3. Edit **Subject words**, separated by commas. Use concrete search words such as `person, coast, boat`, rather than layout instructions such as `leave room for title`.
4. Check the summary above the editor, then start the search or ask for project directions.

Corrections apply to the next submitted request. They do not rewrite your original text or the readings attached to library images. Changing the request fields recalculates the automatic reading and clears the correction; in My project, editing the saved brief clears it too. Use **Use automatic reading** to discard your corrections deliberately.

If the automatic reading is unavailable in Find, the page says so and leaves the correction controls available. You can also continue with your original request. Unfamiliar descriptions, conflicting instructions and phrases such as "avoid X and use Y" still need care. A mistaken suggestion affects reference ranking, but does not remove all other candidates from consideration.

## Fill gaps in your library

On **Find images**, select **Fill gaps in technique coverage**. The app lists techniques with few examples first and preselects some of the thinnest categories.

Choose the techniques you want, the number of new images, sources and assistant, then select **Grow my library**. This uses the techniques' stored search hints, so planning needs no AI call. Analysing the downloaded images still uses the selected assistant.

Coverage counts include proposals. Five labels do not necessarily mean five strong examples; inspect the new images before relying on a category for teaching or project work.

## Search and organise the library

Library search looks through titles, creators, saved observations, and technique names and aliases. It does not make an AI call.

Technique, goal and sort controls sit above the pictures. **More filters** adds shape, source, review state, main colour and favourites. Remove an individual active filter or choose **Clear all** to broaden the results. Sorting changes their order; it does not change the saved images or readings. Filters are recorded in the page address, so Back and reload retain them.

Use **Show the next …** when more results are available. Images keep their proportions in the grid. The arrow keys move between pictures, and Enter opens the focused image. On narrow screens, use the menu to reach the other sections.

You can mark an image as a favourite, save it to a collection, or add it to the comparison tray. If a job downloaded images but stopped before analysis, the library offers **Analyse them now**. That action uses the selected assistant.

## Read an image page

An image page separates what was observed from what was inferred.

**What you can see** contains numbered observations. Hover over an observation or focus it with the keyboard to outline the relevant area on the image. **Show every marked area** displays all of them. Some regions are approximate bands, such as foreground or background. Check that the description matches the picture.

**Why it may work** lists techniques, the evidence for each, a possible effect, and its review state. "Main technique" and "supporting technique" describe the saved reading's roles, not certainty. A picture can support several techniques.

**Left open** records ambiguities. **Documented intent**, when present, comes from the source record; it is separate from the assistant's interpretation. The source's catalogue text is also shown separately.

**Usage and credits** contains the credit line, licence link, source link, restrictions and the date and evidence of the check. Use **Copy credit** to copy the attribution. If you need a production file, follow **Open at the source** and check the available size and usage terms there.

Previous and Next, or the arrow keys when not editing a field, move through the library results you opened. When you arrived through Connections, **Return to your exploration** takes you back to that context.

## Confirm or correct an image reading

Review labels tell you who has assessed a technique claim:

| Label | What it means |
|---|---|
| Proposed by a model | An assistant suggested the technique. It has not been personally confirmed. |
| Agreed by a second model | A different model checked the image and agreed. This is still model review. |
| Confirmed by you | You confirmed or wrote the reading. Later model analysis preserves it. |
| Rejected | The reading was ruled out. A personal rejection is preserved during later analysis. |

On the image page, choose **Confirm** if the evidence supports the technique, or **Reject** if it does not. **Edit evidence** lets you correct the observations and possible effect. Put one observation per line. Use **Add a technique** when a relevant technique is missing.

For example, "the person occupies a small part of the frame, with empty sky around them" describes evidence. "This makes the person feel isolated" is a possible effect. Keep those separate so another reader can assess the claim.

History records changes. If a later analysis drops an earlier model proposal, that proposal becomes superseded and stays in history rather than appearing as a current reading. Your saved decisions are not overwritten by that analysis.

**Remove from library…** removes an image from the active library, deletes its stored image files and active readings, and removes it from collections. Audit history and a removal record remain; that record prevents automatic collection of the image again. The app asks before removal. Use rejection when you want to keep the picture but disagree with its classification.

## Explore visual techniques

Use **Explore** when you know what you want an image to do but do not yet have a reference in mind.

| Term | Example | Meaning |
|---|---|---|
| Goal | Make one thing stand out | The communication effect you want. |
| Operation | Isolate | What the technique does to the arrangement. |
| Domain | Space and depth | The aspect of the image it works with. |
| Technique | Negative space isolation | A specific visual mechanism you can look for and use. |

A technique page gives its definition, where to look, when it may help, common confusions, limitations and related techniques. It also shows examples from your library. These are Visual Atlas's working definitions; background links let you read further.

Subject, medium and style answer different questions. A painting of a boat can use the same spatial technique as a photograph of a person. Compare the mechanism, rather than assuming the subject or period explains the effect.

## Follow connections

**See connections** focuses on one goal, operation, domain, technique or image at a time. Choose a focus from the dropdown, follow links in the context panel, or select a map node. The trail above the view records the route you took.

Operations and domains are shared memberships. A technique can belong to several of each, so the map does not assign every node a single parent. The context panel helps you read the current focus without tracing every line.

Select a line to read its explanation above the canvas. The legend distinguishes goal links, operation links, domain links, related techniques and saved image readings. Thick example lines indicate a main technique in that reading; proposed readings use dotted lines. Neither thickness nor a model-reviewed state means you personally confirmed it.

The canvas scrolls to keep labels and thumbnails readable. **List** presents the same connections as text and links and works with keyboard navigation and screen readers. It opens by default on a phone.

### See more examples without losing your place

Under **Examples in this exploration**, each technique shows a displayed count and a total. Follow **Explore examples** to focus on that technique. **Show more examples** expands the displayed set; **View all in library** opens the complete matching library result.

Open **Visible evidence** on an example card to see what supports the reading. Select two to four examples with **+ Compare**, then choose **Compare side by side**. The return link restores the focus, view, expansion and trail, including after visits to image, technique and library pages.

## Compare images

Choose **+ Compare** on at least two images. The tray accepts up to four; remove one or use **Clear** if you want to change the group. Choose **Compare side by side** to open it.

The pictures and technique table use saved library information. They do not call an assistant. The table distinguishes proposals, second-model agreement and your confirmations. A dash means that technique is not recorded for that image, not that it is impossible to see it there. Palette and contrast measurements offer another way to compare the pictures; they are not quality scores.

If you want a written explanation, select **Ask an assistant to compare them**. This makes an AI request. When it finishes, choose **Show the comparison**. The result is saved so reopening it needs no additional call.

When you started from Connections, use **Return to your exploration** to resume that exact route.

## Get directions for a project

1. Open **My project** and enter a project name.
2. Write the brief with its audience, message, format, mood and constraints. For example: "An A2 poster for a public talk about solitude. Calm, with a small person in a wide landscape. Keep the top third quiet enough for a title."
3. Choose **Save and continue**. Saving the brief does not request AI advice.
4. Read and, if necessary, correct its goals, techniques and subject words.
5. Choose **Suggest directions**. This uses the assistant selected in Settings.
6. Once the job finishes, select **Show the results**.

The adviser receives your full original brief as well as the structured interpretation. It is offered a limited set of library references ranked for the request, with room for subject matches as well as technique matches.

A direction includes an idea, why it might fit, reference images, techniques, and **How to do it, and tradeoffs**. Open the images and judge the proposal against your brief. Advice may be useful without being the direction you ultimately choose.

Choose **Keep** to retain a direction when asking for new ones. **Dismiss** removes it from the current view and offers Undo. Asking again replaces unkept suggestions; kept directions remain. Briefs and suggestions are saved under **Your briefs**.

If the library cannot support a direction, the app may return no suggestion. Use **Find images for this brief** to gather more evidence, or correct a mistaken interpretation. Adding more images only helps if they illustrate the mechanisms your project needs.

**Delete this brief…** removes the brief and its directions after confirmation. Reference images remain in the library.

## Make a collection and export it

Save images to a collection from an image page. Open **Collections** to return to it. You can rename the collection, move images with the left and right controls, or remove an image from the collection. Removing it here leaves the image in the library and offers Undo.

Use **Credits** for the collection's attribution list, or **Export zip** for a package containing image files, `CREDITS.md` and `annotations.json`.

For references found by the app, the export uses the downloaded original. For starter references, it uses the bundled reduced copy, up to 1024 pixels on the long side. The annotation export identifies those reduced copies. Check the source if you need a larger file.

In **Settings**, **All credits (Markdown)** and **Credits as CSV** export credits for the whole library. Keep credits with the images when sharing or publishing, and follow each image's licence conditions.

Deleting a collection removes its grouping, not the images. Deleting an image from the library removes it from collections too.

## Manage jobs and usage limits

Find, Grow, analysis, model checks, written comparisons and project directions run as background jobs. Open **Jobs** to see their state and any failure message. A worker handles one job at a time.

- **Pause** requests a stop after the current step. It may not interrupt a model call already running.
- **Resume** continues the unfinished work.
- **Cancel** stops further work on the job. Images already added stay in the library.

The queue records progress so a restart can continue unfinished steps. If you want work to stay stopped when reopening the app, pause or cancel it explicitly.

A daily call cap and the assistant account's limits are separate. When an account limit pauses a job, wait until the account is available and resume it. Changing the default assistant in Settings affects new jobs; an existing job retains the assistant chosen when it was created. Start a new request with another assistant if you need to switch immediately.

Failures do not all mean the same thing. A source can be temporarily unavailable, a download can be rejected, an assistant can be signed out, or a job can exhaust its own search or analysis budget. Read the job's message before repeating the request. [Troubleshooting](#troubleshooting) gives the common next steps.

## Understand sources and usage terms

Visual Atlas collects images through these supported sources:

| Source | What the app accepts |
|---|---|
| Art Institute of Chicago | Images marked public domain under its CC0 policy. |
| The Met | Images the item record marks public domain under its CC0 policy. |
| Cleveland Museum of Art | Images marked CC0. |
| Smithsonian Open Access | Image media marked CC0, not merely open catalogue metadata. |
| Wikimedia Commons | CC0, public domain or CC BY files with the required author and licence evidence. |
| Rijksmuseum | The image's own Public Domain Mark, CC0 or CC BY 4.0 rights statement. |
| National Gallery of Art | Open-access primary images without a size cap, under its CC0 policy. |

The app decides eligibility from recorded source fields and its source policy. Models do not decide whether an image can be used. Missing or unclear evidence means the item is skipped. Commons share-alike, non-commercial and no-derivatives licences are outside the automatic collection policy.

**Settings → Sources** shows each source's rule, supporting links and checking date. An image page keeps the item-specific evidence and the date it was checked. Review **Usage and credits** for the exact attribution and restrictions before using an image outside the app. Copyright permission may not cover a person's likeness, a trademark or every intended use.

The starter pack's distribution rights were checked separately from the app's permission to store, display and analyse an image. Its files retain their own licences. The [curation report](evaluation/v0.4/CURATION.md) records the accepted additions and remaining gaps; the [credits file](../starter/CREDITS.md) carries their attribution.

### Source-specific setup

The **National Gallery of Art** is opt-in. Its first search downloads about 190 MB of open catalogue data, builds a smaller index in the library's `sources\nga` folder, and deletes the downloaded CSV files. Later searches reuse that index. It refreshes after 30 days; a failed refresh leaves the old index available.

**Smithsonian** can use a shared demonstration key with limited capacity. If you hit that limit, get your own key at [api.data.gov](https://api.data.gov/signup/) and add `SMITHSONIAN_API_KEY=your-key` to the library folder's `.env` file. Do not put credentials in a brief or commit them to the project repository.

Sources such as Unsplash, Pexels, Pixabay, the Library of Congress and NASA are not enabled in the shipped policy. See [source research](evaluation/v0.3/SOURCES.md) for the recorded reasons and [other image sources](FREE-IMAGE-SOURCES.md) for further reading. Their absence does not imply that every image on those sites has the same rights.

## Back up and restore

In **Settings**, choose **Back up now**. The backup contains the database, images and saved readings and is stored in the library's `backups` folder. Copy completed backup files to another drive if you need protection against loss of the computer or its disk.

To return to a backup, select **Restore…** beside it and read the confirmation before proceeding. Restore replaces the current library with the backup's state; it does not merge your latest edits into that older version.

The app checks the archive, makes a safety backup of the current library, and restores the selected copy. If a job is active, stop it and try again. While maintenance is in progress, other writes are refused with a message; retry them when it finishes.

If restore is interrupted, restart the app and inspect the library. Recovery is designed to leave the previous or restored database intact, and the safety backup provides a route back. Keep a separate backup of important work rather than relying on recovery alone.

From a source checkout, the equivalent commands are `uv run atlas backup` and `uv run atlas restore <backup-file-name>`. The restore argument is a filename in the library's backups folder.

## Use the command line

Run these commands from the project or extracted application folder. They use the same library as the app, unless you set a different `VISUAL_ATLAS_HOME`.

| Command | Purpose |
|---|---|
| `uv run atlas find "foggy harbours, silhouettes" --count 6` | Find and analyse references; uses the configured assistant. |
| `uv run atlas grow --count 8` | Search for examples of techniques with low coverage. |
| `uv run atlas analyze` | Analyse downloaded images that are still waiting. |
| `uv run atlas jobs` | List recent jobs. |
| `uv run atlas job <id> pause` | Pause a job; use `resume` or `cancel` for the other actions. |
| `uv run atlas worker` | Work the next unfinished job. |
| `uv run atlas worker --forever` | Keep processing the queue until stopped with Ctrl+C. |
| `uv run atlas library` | List library images and readings. |
| `uv run atlas coverage` | Show examples per technique. |
| `uv run atlas credits --format csv` | Print the library's credits as CSV. |
| `uv run atlas starter-import` | Add missing bundled references without duplicating existing ones. |
| `uv run atlas doctor` | Check the library, knowledge files and assistant setup. |
| `uv run atlas --help` | List available commands and options. |

Use `--backend codex` or `--backend claude` on a Find request to choose an assistant explicitly. `--verify-with none` turns off its second-model check. These commands can make real model calls and use your account allowance.

Claude Code and Codex can both work with this project. [`AGENTS.md`](../AGENTS.md) and [`CLAUDE.md`](../CLAUDE.md) give them the same instructions. Jobs use shared JSON contracts in [`schemas/`](../schemas/); the app and a command-line worker coordinate through job leases to avoid processing the same job together.

## Edit the taxonomy

For maintainers, goals, operations, domains and techniques live in [`atlas/data/taxonomy.json`](../atlas/data/taxonomy.json). Source eligibility rules and evidence links live in [`atlas/data/source_policies.json`](../atlas/data/source_policies.json).

After editing the knowledge files, run `uv run atlas taxonomy check` and restart the app. Keep existing technique IDs stable while saved readings refer to them. Changes to source rules affect what the app may collect, so test them against the rights-policy tests before use.

## Troubleshooting

| What you see | What to try |
|---|---|
| Windows blocks the downloaded installer | Check the zip's Properties for **Unblock**, then extract it again. Confirm you are using the release you intended to download. |
| Installation fails with a long-path error | Extract into a shorter application path, such as `C:\VisualAtlas`, and rerun the installer. Leave your library folder where it is. |
| The app opens with no starter images | Run the installer again, or run `uv run atlas starter-import` from the application folder. Check whether `VISUAL_ATLAS_HOME` points to a different library. |
| An assistant is not ready | Run `codex login` or `claude` in a terminal, complete sign-in, then use **Settings → Assistants → Check again**. |
| A second-model check is unavailable | Keep the reading as proposed, or retry the check when that assistant is ready. Agreement is not required to browse or personally review an image. |
| A request has the wrong goals or subjects | Use **Correct this reading** before submitting it. Editing the brief clears previous corrections. |
| Find returns fewer images than requested | Read **Not added** and the job message. Broaden shape, colour or subject constraints, or run a new request if the job reached its limit. |
| Project help returns no directions | Check the brief's interpretation and whether the library has relevant examples. Use **Find images for this brief** if it needs more references. |
| A job pauses at a usage limit | Wait for the account limit to reset, then resume. To use another assistant immediately, choose it for a new job. |
| A source reports a temporary error | Retry later or use other sources. For Smithsonian limits, consider your own key. The first National Gallery search can take longer because it builds an index. |
| “Port 8775 is used by another program” | Close the conflicting program, or add `VISUAL_ATLAS_PORT=8776` to the library folder's `.env` file and relaunch. |
| A restore refuses to start | Pause or cancel active jobs, allow the current step to finish, then retry. |
| Changes are refused during maintenance | Wait for restore or recovery to finish, then repeat the action. |
| A starter image is too small for print | Follow **Open at the source** for a larger file and check its terms. The bundled copies are for reference use. |

For a window launched from the Windows shortcut, check `%USERPROFILE%\VisualAtlas\visual-atlas-app.log`. If you use a custom library folder, look there instead. A terminal launch prints errors in that terminal. Run `uv run atlas doctor` for a setup check, and include the specific error message when reporting a problem. Remove credentials and private brief text before sharing logs.
