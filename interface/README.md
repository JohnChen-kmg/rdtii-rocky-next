# The interface

An Overview, three stage tabs and an Appendix over the three pipeline stages, standard-library Python, nothing to install for it.

    python interface/app.py             a browser tab: open the address it prints; Ctrl+C stops it
    python interface/app.py --window    a window of its own: closing the window stops it

The launchers at the top of the repository (`Start-RDTII-Rocky.cmd`, `Start-RDTII-Rocky.command`,
`start-rdtii-rocky.sh`) run the second line on a double-click. The tab is at http://127.0.0.1:8765/. Built from scratch on 29–30 September 2026; the plan and the reasons
are in `START_PROMPT_INTERFACE_2026-09-29.md` and `DATA_PATHS.md` beside this file. Reworked from 3 to 5 October
(the window, results filed by economy and source, a model per mapping step, a table of runs in every Output, the
cost report); every change, with how it was verified, is in `docs/CHANGELOG_FINALE.md`. This file describes the
pages as they stood on 5 October 2026.

## Layout

The sidebar holds Overview, Stage 1 Scraping (with a sub-page, China), Stage 2 Extraction, Stage 3 Mapping and
Appendix, and lists the open page's blocks under it. Every stage page has the same three blocks: Set up, Run,
Output.

| Page | Block n.1 Set up | Block Run (1.2, 2.2, 3.2) | Block Output (1.4, 2.3, 3.3) |
| :-- | :-- | :-- | :-- |
| **Overview** | five numbered sections, the landing page on every visit. **1 Introduction**: one line and the three stages, each a link to its page. **2 Workflow map**, one column: Scraping, Extraction, Mapping, and Mapping (continued): Review and export, each with a button to its page and a folded "Example: Singapore" in two parts, Input and Output. The Mapping block holds a picture (provisions, the instrument, indicators), the five steps A to E by name, a folded "Mapping, step by step" (one sub-block per step, the model-calling ones with what is sent and what comes back; the example follows Singapore PDPA s.26(1) and indicator 6.4 through all five) and the instrument as a grey fold (the nine elements of a rulebook, 6.4 element by element). **3 Cost report**: Money (by model and step, then the finale run's bill), Time (by stage) and a Calculator, all three drawn from one data block in the page (`#cost-data`); an estimate is marked "≈". **4 Model performance**: "Estimated performance by model", one experiment, said on the page to be small. **5 Before you start** | | |
| **Scraping** | economies the crawler has adapters for, China through its own tools (CAC and gov.cn; the rest by hand), scope, the sources it will read, the sources to check by hand, and a folded "What we hold today" per economy | a notice on how long a crawl takes; a new crawl or a second pass over that economy's own folder; Sources: the link list or **Refresh from the portal**; **Quick run** (the first N documents); dry run; a run note; **Check** then **Start**; one run and one result panel per economy | a table of folders by economy and source (`scrape/<economy>/<source>/<time>`): Began, Last run, Kind, Status (complete, running, paused, stopped, not complete), documents by type, whether the bytes are present, **Fetched last pass**, Open folder, Clear. Between Run and Output, block 1.3 **Hand-collected**: choose the economy, drop PDF or Word files or a .zip (a saved web page only from a portal the reader has a parser for, with its address); they land in `inbox/<economy>/Hand_collected/<date_time>`, and each file says how it will be read or why it cannot be; Output is 1.4 on this page |
| **Extraction** | a crawl folder, or hand-collected documents from `inbox/<economy>/Hand_collected` (the folder names the economy, the language follows the economy table; a Readiness list says per file how it is read, and files that cannot be read are left out and listed; Check reads the text and warns when a file does not fit its folder) | a notice, "How extraction works" (file type, reading, splitting, limit, check); output name; OCR pack (Fast or Best) and workers, with the measured pace and load of each; a run note; **Check** then **Start**: import check, OCR of scanned pages, read and segment, freeze the text | a table of outputs: Began, Last run, Kind, Status, documents by status and lane, provisions, laws, OCR cache and frozen text; **N to check** lists the documents that gave no provisions; Open folder, Clear OCR cache |
| **Mapping** | an extraction output (with the run note it carries), economies, indicators (61, the nine automated ones pre-selected; the nine reviewed ones carry the tag "reviewed", three are marked practice-based) | the write path; a notice naming the model each step used in the finale run, where the Overview explains the steps and compares models, and what the two prices beside a model mean; then one block per step in run order, lettered A to E: A candidate selection (the index, rebuilt by itself when older than the output or ranked for other indicators; the rule, with a number box per ticked indicator holding the recommended threshold or cap, to be changed for this run by typing; the meaning index), then B quick screen, C careful reading, D re-check and E tie-break, each with a provider and one of its models, cheapest first; translation, quick run, a run note; **Check** then **Start**: ingest, the two indexes, candidate selection, quick screen, then per economy the careful reading and a chain of re-check, NEW against KNOWN, scores, evidence rows, glosses, workbook and audit page | a table of runs (Began, Last run, Folder with its run note, Kind, Status, Economies, Rows, Cost): the interface's own runs newest first, then the shipped fixture and the filed rows; a click on a run examines it, and its Record names the model of each step; then filters, Export CSV and xlsx, rows with the English gloss beside the original, row detail with Accept / Reject / Correct and Clear decision, Open folder, Clear run |
| **Appendix** | five blocks: **Adding a new economy** (what each stage needs, the file that holds it, what is built), **This machine** (the Python of each stage), the settings in effect, a run-layer self-test, and the documentation shipped in the repository | | |

The **header** holds the title and the health dots (Ollama, Tesseract, Chromium, API key held, stages present);
the tabs run down a **left sidebar**, Overview first. The Mapping tab, the only stage that uses an AI engine, opens with
**Engine API keys**: one row per engine of `stages/p3-map/config/llm/engines.json` (A Claude and B local Qwen, the
two the pipeline was measured on, then DeepSeek, Kimi and ChatGPT, marked not measured), each hosted one with its
key and each saying whether the current choice calls it. 3.2 Run opens with where the run writes, then a
notice naming the model each step used in the finale run; each step starts on that model and can be given another
provider and model in its own block. A key lives in memory for the life of the process, under the variable its
engine reads, and is never written or shown.

## Settings

Every location is an environment variable with a default that works on a clean clone; see `DATA_PATHS.md`.
The ones the interface adds:

| Name | Default | Purpose |
| :-- | :-- | :-- |
| `RDTII_RUNS_ROOT` | `outputs` | where runs are written and the only tree **Clear** may touch |
| `RDTII_OUT_DIR_EXTRA` | (auto: a sibling `out_*` of `OUT_DIR`) | further arms of the displayed run, comma separated |
| `RDTII_SUBMISSION_DIR` | `submission` | the filed rows, shown read-only |
| `RDTII_INBOX_DIR` | `inbox` | documents collected by hand, `<economy>/Hand_collected/<date_time>`; listed on the Extraction tab |
| `RDTII_PYTHON_P1`, `_P2`, `_P3` | what Appendix, This machine keeps for this computer; else a stage's own `.venv` when it has one, then the repository's, then the interpreter running the page | a different Python per stage when each has its own environment; a relative value is taken against the repository |
| `RDTII_PYTHON_AUTO` | `1` | set to `0` to stop a `.venv` being picked up by itself |
| `RDTII_TESSERACT` | (found on PATH, then in the usual place for the system) | the Tesseract program, when it is somewhere else |
| `RDTII_HOST`, `RDTII_PORT` | `127.0.0.1`, `8765` | bind address; port `0` takes a free one, and a window start does so by itself when the port is taken |
| `RDTII_BROWSER` | (Edge, Chrome, Brave, Chromium, the first one installed) | the browser for the window: a path or a command |
| `RDTII_STATE_DIR` | the system's place for a user's data (`%LOCALAPPDATA%\rdtii-rocky`, `~/Library/Application Support/rdtii-rocky`, `~/.local/state/rdtii-rocky`) | what belongs to the machine, not to a project: the window's browser profile, the note of the running instance, `interface.log` |
| `RDTII_REVIEWER` | the login name | stamped on decisions unless a name is typed on the page |

## Rules the code keeps

- The interface never imports stage code and never writes under `stages/`; it runs the stage command lines
  as subprocesses and reads what they write.
- The browser may only set allowlisted variables to values the server enumerates; the engine ids and the
  models of each come from the stage's own declaration, so the declared and the offered cannot drift apart.
- A run that changes no step receives exactly the variables it always did. A step on another provider needs
  that provider's own key, and a key no step uses is passed to no process.
- A threshold typed for an indicator goes into a copy of the stage's `selection.json`, written into the run's
  folder, and a typed cap into a variable of that run; the stage's own numbers are never written, and a
  number equal to the recommended one changes nothing.
- Indicator IDs stay decimal text everywhere; the xlsx export writes inline strings and never column O.
- A machine translation is shown beside the original and labelled, never in its place, and the export
  never opens a gloss file.
- Review decisions are an append-only log; the filed submission is read-only.
- **The window** is the machine's own Edge or Chrome in app mode on a profile kept for this tool, signed in
  to nothing. The interface stops when the window's process has ended and no page is connected; it never
  cuts a run short while the window exists. Closing the window during a run asks first, then stops the run.
  A second start for the same repository brings the first window forward. With no such browser the page
  opens as an ordinary tab. Started with no console, it writes what it would print to `interface.log`.
- In the window a link to a source opens in the person's own browser, only `http` and `https`, and Export
  says where the file was saved instead of downloading it.
- One server per port: a second start on a port in use is refused (Windows used to let both bind it).
- **A crawl says what it will do before Start.** Check asks the crawler's own code, in a process of its own,
  whether it will accept the link list, and states per economy how many documents and how long, from the
  list's own record: its counts, and the time its last build took from first request to last.
- **The link list in use** is the newest one refreshed from this page that was built for the registry the
  crawler reads (`scrape/<economy>/<source>/links_<time>` under the runs root), else the one shipped in
  `stages/p1-scrape/links/`. Refresh from the portal runs the stage's catalogue tool to read the listings
  into such a list, then replays it; the interface writes nothing under `stages/`.
- **Quick run** replays a small list cut from the one in use (`links_used/` in the run folder), so it works
  for either scope. A second pass runs over a folder of the same economy and no other.
- On Windows without long paths, a run folder so deep that a long-named law could not be stored fails Check.
- The browser check is a real launch by the crawler's own Python, kept until the builds on disk change; a
  Chromium folder says nothing once the Playwright package has moved to another build.
- Which Python runs each stage belongs to the machine: it is kept in `machine.json` in the state folder, set
  from Appendix, This machine, and tested by each stage's Check before Start.
- A crawl asks for one document per law (`--forms pdf`). A run the portal cut short ends as failed, with
  the count missing and the way to resume; nothing fetched is lost.
- **Open folder** opens a run folder in the file manager of the machine that runs the server; it is
  limited to the folders the page itself lists (the runs root, the fixtures, the demo data, the hand-offs).
  On Windows the Explorer window is brought in front of the browser, and a window already showing the
  folder is reused.
- Clear works only under the runs root, on one run folder or one named cache, with a preview and a
  one-minute confirmation token, and never on anything git tracks. It never takes a whole economy or a
  whole source.
- Crawl results are filed by economy, then source: `scrape/<economy>/<source>/<time>`. The sources come
  from the stage's own files (the adapter's portal, its watchlist, China's publisher table), never from a
  list kept in the interface. Folders of the earlier layout are still read.
- Files a person fetched need no source since 5 October 2026: a file's reading method follows from what it
  is and from the economy's language. A drop goes to `inbox/<economy>/Hand_collected/<date_time>`. Beside
  the files the interface writes one sheet, `provenance.tsv`, with the address each came from; it changes
  nothing else there. A folder of the earlier layout, one per designated source, is still read.

## Tests

    python -m unittest discover -s interface/tests -t interface

291 tests: the readers and the traps they guard, the run layer with a real subprocess, the allowlist, the
window (which browser, when to stop, one instance, the presence stream on a real server), the
Clear guard, the folders by economy and source, the inbox (the hand-collected folder, addresses, archives, what
can be read), the run tables of the three Output blocks, the cost report against the ledger, the manifest written for hand-collected documents, the three run plans and their parsers, a model per step
and a key per provider,
review decisions and the export.
