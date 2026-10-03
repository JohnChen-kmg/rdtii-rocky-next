# The interface

An Overview, three stage tabs and an Appendix over the three pipeline stages, standard-library Python, nothing to install for it.

    python interface/app.py

Then open http://127.0.0.1:8765/. Built from scratch on 29–30 September 2026; the plan and the reasons
are in `START_PROMPT_INTERFACE_2026-09-29.md` and `DATA_PATHS.md` beside this file.

## Layout

| Tab (Stage 1 to 3 in the sidebar, which also lists the open page's blocks) | Block n.1 Set up | Block Run (1.2, 2.2, 3.2) | Block Output (1.4, 2.3, 3.3) |
| :-- | :-- | :-- | :-- |
| **Overview** | a workflow map: Scraping, Extraction, Mapping, Review and export, one line each with a button to the page, and below it the instrument (methodology to a rulebook per indicator) as a reference row; the model-calling steps are drawn as short conversations; the mapping step by step (index, select, triage, read, re-check, tag, score, evidence, review) folded inside the Mapping node, an open grey Before-you-start block under the map; the worked example on Singapore PDPA s.26(1) runs down the right of the map, one card per node, with a button to its row | | |
| **Scraping** | economies the crawler has adapters for, China through its own tools (CAC and gov.cn; the rest by hand), scope, the sources it will read and the sources to check by hand | fresh folder or second pass, shipped link list or live discovery, dry run, **Check** then **Start** | crawl folders, documents by economy and type, whether the bytes are present, **Fetched last pass**, Clear. Between Run and Output, block 1.3 **Hand-collected**: choose one economy, drop PDF, HTML or Word files, they land in `inbox/<economy>`; Output is 1.4 on this tab |
| **Extraction** | a crawl folder, or hand-collected documents from `inbox/<economy>` (the folder names the economy, the language follows the economy table; Check reads the text and warns when a file does not fit its folder) | output name, OCR pack and workers, **Check** then **Start**: import check, OCR of scanned pages, read and segment, freeze the text | documents by status and lane, provisions, cache sizes, Open folder, Clear OCR cache |
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
| `RDTII_INBOX_DIR` | `inbox` | documents collected by hand, one subfolder per economy; listed on the Extraction tab |
| `RDTII_PYTHON_P1`, `_P2`, `_P3` | a stage's own `.venv` when it has one, then the repository's, then the interpreter running the page | a different Python per stage when each has its own environment; a relative value is taken against the repository |
| `RDTII_PYTHON_AUTO` | `1` | set to `0` to stop a `.venv` being picked up by itself |
| `RDTII_TESSERACT` | (found on PATH, then in the usual place for the system) | the Tesseract program, when it is somewhere else |
| `RDTII_HOST`, `RDTII_PORT` | `127.0.0.1`, `8765` | bind address |
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
- **Open folder** opens a run folder in the file manager of the machine that runs the server; it is
  limited to the folders the page itself lists (the runs root, the fixtures, the demo data, the hand-offs).
  On Windows the Explorer window is brought in front of the browser, and a window already showing the
  folder is reused.
- Clear works only under the runs root, on one run folder or one named cache, with a preview and a
  one-minute confirmation token, and never on anything git tracks.

## Tests

    python -m unittest discover -s interface/tests -t interface

123 tests: the readers and the traps they guard, the run layer with a real subprocess, the allowlist, the
Clear guard, the manifest written for hand-collected documents, the three run plans and their parsers,
review decisions and the export.
