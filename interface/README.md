# The interface

An Overview, three stage tabs and an Appendix over the three pipeline stages, standard-library Python, nothing to install for it.

    python interface/app.py             a browser tab: open the address it prints; Ctrl+C stops it
    python interface/app.py --window    a window of its own: closing the window stops it

The launchers at the top of the repository (`Start-RDTII-Rocky.cmd`, `Start-RDTII-Rocky.command`,
`start-rdtii-rocky.sh`) run the second line on a double-click. The tab is at http://127.0.0.1:8765/. Built from scratch on 29–30 September 2026; the plan and the reasons
are in `START_PROMPT_INTERFACE_2026-09-29.md` and `DATA_PATHS.md` beside this file.

## Layout

| Tab (Stage 1 to 3 in the sidebar, which also lists the open page's blocks) | Block n.1 Set up | Block Run (1.2, 2.2, 3.2) | Block Output (1.4, 2.3, 3.3) |
| :-- | :-- | :-- | :-- |
| **Overview** | a workflow map: Scraping, Extraction, Mapping, Review and export, one line each with a button to the page, and below it the instrument (methodology to a rulebook per indicator) as a reference row; the model-calling steps are drawn as short conversations; the mapping step by step (index, select, triage, read, re-check, tag, score, evidence, review) folded inside the Mapping node, an open grey Before-you-start block under the map; the worked example on Singapore PDPA s.26(1) runs down the right of the map, one card per node, with a button to its row | | |
| **Scraping** | economies the crawler has adapters for, China through its own tools (CAC and gov.cn; the rest by hand), scope, the sources it will read and the sources to check by hand | a new crawl or a second pass over that economy's own folder, the link list or **Refresh from the portal**, **Quick run** (the first N documents), dry run, **Check** then **Start**; one run and one result panel per economy | folders by economy and source (`scrape/<economy>/<source>/<time>`), documents by type, whether the bytes are present, **Fetched last pass**, Clear. Between Run and Output, block 1.3 **Hand-collected**: choose one economy, then one of its designated sources, drop PDF, Word, saved web pages or a .zip; they land in `inbox/<economy>/<source>/<date_time>`, each file says how it will be read or why it cannot be, and takes the address it came from; Output is 1.4 on this tab |
| **Extraction** | a crawl folder, or hand-collected documents from `inbox/<economy>/<source>` (the folder names the economy and the source, the language follows the economy table; a Readiness list says per file how it is read, and files that cannot be read are left out and listed; Check reads the text and warns when a file does not fit its folder) | output name, OCR pack and workers, **Check** then **Start**: import check, OCR of scanned pages, read and segment, freeze the text | documents by status and lane, provisions, cache sizes, Open folder, Clear OCR cache |
| **Mapping** | an extraction output, economies, indicators (61, the nine automated ones pre-selected) | the write path, the engine from the banner, the index (rebuilt by itself when older than the output); selection rule with its thresholds or caps, meaning index, translation, quick run; **Check** then **Start**: ingest, prefilter, select, triage, map, verify, roll up, glosses, workbook, audit page | run selector (fixtures, interface runs, filed rows), filters, Export CSV and xlsx, rows with the English gloss beside the original, row detail with Accept / Reject / Correct and Clear decision, Open folder, Clear |
| **Appendix** | documentation shipped in the repository, the settings in effect, a run-layer self-test | | |

The **header** holds the title and the health dots (Ollama, Tesseract, Chromium, API key held, stages present);
the tabs run down a **left sidebar**, Overview first. The **Engine Selection** banner sits at the top of the Mapping tab, the
only stage that uses an AI engine (A or B, from `stages/p3-map/config/llm/engines.json`); a key banner folds out
beneath it only when the chosen engine needs one. The key lives in memory for the life of the process and is
never written or shown.

## Settings

Every location is an environment variable with a default that works on a clean clone; see `DATA_PATHS.md`.
The ones the interface adds:

| Name | Default | Purpose |
| :-- | :-- | :-- |
| `RDTII_RUNS_ROOT` | `outputs` | where runs are written and the only tree **Clear** may touch |
| `RDTII_OUT_DIR_EXTRA` | (auto: a sibling `out_*` of `OUT_DIR`) | further arms of the displayed run, comma separated |
| `RDTII_SUBMISSION_DIR` | `submission` | the filed rows, shown read-only |
| `RDTII_INBOX_DIR` | `inbox` | documents collected by hand, one subfolder per economy and designated source; listed on the Extraction tab |
| `RDTII_PYTHON_P1`, `_P2`, `_P3` | a stage's own `.venv` when it has one, then the repository's, then the interpreter running the page | a different Python per stage when each has its own environment; a relative value is taken against the repository |
| `RDTII_PYTHON_AUTO` | `1` | set to `0` to stop a `.venv` being picked up by itself |
| `RDTII_TESSERACT` | (found on PATH, then in the usual place for the system) | the Tesseract program, when it is somewhere else |
| `RDTII_HOST`, `RDTII_PORT` | `127.0.0.1`, `8765` | bind address; port `0` takes a free one, and a window start does so by itself when the port is taken |
| `RDTII_BROWSER` | (Edge, Chrome, Brave, Chromium, the first one installed) | the browser for the window: a path or a command |
| `RDTII_STATE_DIR` | the system's place for a user's data (`%LOCALAPPDATA%\rdtii-rocky`, `~/Library/Application Support/rdtii-rocky`, `~/.local/state/rdtii-rocky`) | what belongs to the machine, not to a project: the window's browser profile, the note of the running instance, `interface.log` |
| `RDTII_REVIEWER` | the login name | stamped on decisions unless a name is typed on the page |

## Rules the code keeps

- The interface never imports stage code and never writes under `stages/`; it runs the stage command lines
  as subprocesses and reads what they write.
- The browser may only set allowlisted variables to values the server enumerates; the engine ids come from
  the stage's own declaration, so the declared and the offered engines cannot drift apart.
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
- A crawl asks for one document per law (`--forms pdf`). A run the portal cut short ends as failed, with
  the count missing and the way to resume; nothing fetched is lost.
- **Open folder** opens a run folder in the file manager of the machine that runs the server; it is
  limited to the folders the page itself lists (the runs root, the fixtures, the demo data, the hand-offs).
  On Windows the Explorer window is brought in front of the browser, and a window already showing the
  folder is reused.
- Clear works only under the runs root, on one run folder or one named cache, with a preview and a
  one-minute confirmation token, and never on anything git tracks. It never takes a whole economy or a
  whole source.
- Results are filed by economy, then source, on both sides: `scrape/<economy>/<source>/<time>` for what
  the crawler fetched, `inbox/<economy>/<source>/<date_time>` for what a person fetched. The sources come
  from the stage's own files (the adapter's portal, its watchlist, China's publisher table), never from a
  list kept in the interface. Folders of the earlier layout are still read.
- The inbox takes files only for a designated source. Beside the files the interface writes one sheet,
  `provenance.tsv`, with the address each came from; it changes nothing else there.

## Tests

    python -m unittest discover -s interface/tests -t interface

205 tests: the readers and the traps they guard, the run layer with a real subprocess, the allowlist, the
window (which browser, when to stop, one instance, the presence stream on a real server), the
Clear guard, the folders by economy and source, the inbox (designated sources, addresses, archives, what
can be read), the manifest written for hand-collected documents, the three run plans and their parsers,
review decisions and the export.
