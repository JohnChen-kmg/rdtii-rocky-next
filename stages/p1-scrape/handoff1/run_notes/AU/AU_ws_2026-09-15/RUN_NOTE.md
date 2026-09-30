# Run note: AU_ws_2026-09-15

Australia, web scraping, 15 September 2026: the **first crawl from a link list**, every in-force principal Act of
the Commonwealth and the 20 seeds' documents, from the Federal Register of Legislation (`www.legislation.gov.au`,
its API for the list) plus two regulator pages.

## Read this first

- **1,277 of 1,277 listed documents are stored:** 1,264 principal Acts (783 as the current compilation, fetched as
  the register's epub and unpacked to HTML; 481 as the as-made PDF, titles never compiled), 3 amending Acts,
  7 legislative instruments and 3 regulator documents. Nothing failed at the end; one document needed a second
  pass (issue 1).
- **One document's header file is out of reach from the workshop path.** The engine names each folder after the
  whole law name, and one title of 138 characters pushes `…__native.pdf.headers.json` past Windows' 260-character
  limit under `C:\Users\woshi\Desktop\rdtii-finale-1-scraping\outputs\AU\…`. The file exists and the PDF itself
  is readable; the sidecar is readable through a shorter path (`subst R: <ws>`, then `R:\outputs\AU\…`) or once
  Windows long paths are enabled. `scrape.py --validate` passes through `R:` and reports 1 error through `C:`.
- **The audit flags 89 documents, none a wrong file:** old as-made Acts of one to four pages (1908 to 1999), whose
  first page carries the Act's own title in 83 cases and its enactment title in 6 (Acts renamed since). No
  Australian rule set exists yet, so the generic "short principal act" flags fire.
- **The 792 HTML documents are the engine's own rendering** of the register's epub (spine concatenated), not a page
  of the website; the epub bytes are not kept (`countries/au-australia/NOTES.md` 2.5).
- **The corpus `outputs/AU/AU_corpus_2026-09-15` is this run** (1,277 documents, built 17:01 UTC): the folder for
  downstream to read for Australia.

## At a glance

| | |
| :---- | :---- |
| Country | Australia (`AU`) |
| Run type | Full crawl from the link list of 12:33 UTC (`links_used/`), scope `all`, then a one-document resume (issue 1) |
| Date | 2026-09-15 |
| Time, UTC | Crawl 12:33:16 to 17:00:06 (16,010 s, 4 h 27 min). Resume 17:00:28 to 17:00:31 |
| Time, machine clock | US Eastern Daylight Time, UTC−4: 08:33 to 13:00 |
| Result | 1,277 listed documents: **1,277 stored** (1,276 in the crawl, 1 in the resume), **0 failed**, 0 duplicates. 1,279 log entries: 1,278 fetches answered HTTP 200, 1 store error |
| Size | 794,616,999 bytes (795 MB) of documents; 13,021 pages in the 485 PDFs (HTML rows carry no page count) |
| Validation | `scrape.py --validate manifest.csv` through `R:`: 1,277 rows, 0 errors, 0 warnings, contract 0.2.0. Through the workshop path: 1 error, the header file of issue 1 |
| Audit | `tools/audit_run.py` with `RULES["AU"]` (written 2026-09-16): 91 rows flagged, 0 missing, 1 orphan file. 88 are short as-made Acts that print their own number, so they are whole; 2 are Acts renamed since enactment; 1 has a scan whose year reads "ll73" |
| Status | **Usable.** Read the second and third points above first |
| Checked | `crawl_status.json`, `crawl_log.jsonl`, `manifest.jsonl`, `links_used/catalogue_meta.json`, `links_used/documents.jsonl`, `audit.json`, `logs/crawl_stdout.log` |

## Steps and times

| Step | UTC | Requests | Output |
| :---- | :---- | :---- | :---- |
| 1. Build the link list | 12:24 to 12:33:16 (a first build at 12:14 gave the same figures; this one ran the review-fixed code) | 122 to the register's API (48 title pages of 100, ordered by id: 4,765 titles in the Act collection, 1,264 principal; the version batches of 18) plus robots.txt on `www` (`Crawl-delay: 10`; the API host has none, HTTP 404): 121 API requests and 1 to `www`. No `www` page, no document | `countries/au-australia/links/`, copied here as `links_used/` |
| 2. Crawl the list | 12:33:16 to 17:00:06 | 1,277 document fetches at `REQUEST_DELAY_MS=10000` (12.5 s per document on average, download included): 1,274 to `www.legislation.gov.au`, 2 to `www.oaic.gov.au`, 1 to `www.apra.gov.au`; 1,270 by `requests`, 7 by Playwright | `raw/`, `manifest.*`, `crawl_log.jsonl` (1,276 stored, 1 store error) |
| 3. Resume through `R:` | 17:00:28 to 17:00:31 | 1 fetch (the document of issue 1) | `manifest.*` at 1,277 rows; `crawl_status.json` and `cost_report.json` now describe this step |
| 4. Validate, audit | 17:00:57 to 17:01 | none | `audit.md`, `audit.json` |
| 5. Corpus | 17:01:52 | none | `outputs/AU/AU_corpus_2026-09-15` (hard links) |

## How it was run

- **Engine:** the sandbox copy `scratchpad\sbx2\p1-scrape` of the repo's `stages\p1-scrape` (commit `92a5e9d`),
  unchanged, with the Round 1 module `adapters/au_legislation.py` replaced by the package.
- **Country scraper:** `countries/au-australia/scraper/` (package `adapters/au_legislation/`, 2026-09-15 state,
  its sha256 in `links_used/catalogue_meta.json` as `scraper_sha256`) and Malaysia's package for the paced client
  and robots.txt rules.
- **Registry:** `countries/au-australia/sources.yaml` (block `register:`: `detail_pages: all`, `version_batch: 18`,
  `title_page_size: 100`, `max_titles: 6000`, `collection: Act`, `document_form: epub`) joined with
  `links/seed_laws.yaml` (20 seeds); fingerprint `f2e6cf88…`, the same as the list's.
- **Politeness:** `REQUEST_DELAY_MS=10000` (the `www` host's `Crawl-delay`), the engine's jitter, one process, one
  request at a time; robots.txt read at the start (0 rows dropped). The register did not throttle.
- **Commands** (from `<sandbox>`; `<ws>` the workshop, `<run>` this folder):

  ```
  PYTHONPATH=src python -m p1_scrape.adapters.au_legislation.catalogue \
      --registry <ws>/countries/au-australia/sources.yaml --seeds <ws>/countries/au-australia/links/seed_laws.yaml \
      --out <ws>/countries/au-australia/links
  mkdir -p <run>/logs && cp -r <ws>/countries/au-australia/links <run>/links_used
  REQUEST_DELAY_MS=10000 REGISTER_FRONTIER=links_file REGISTER_LINKS_FILE=<run>/links_used/documents.jsonl \
      python scrape.py --economy AU --scope all --out <run>
  # the resume of 17:00, through the subst drive (subst R: <ws>)
  REQUEST_DELAY_MS=10000 REGISTER_FRONTIER=links_file REGISTER_LINKS_FILE=<run>/links_used/documents.jsonl \
      python scrape.py --economy AU --scope all --out R:/outputs/AU/AU_ws_2026-09-15
  python scrape.py --validate R:/outputs/AU/AU_ws_2026-09-15/manifest.csv
  PYTHONPATH=src python tools/audit_run.py <run>
  PYTHONPATH=src python tools/merge_corpus.py --outputs R:/outputs/AU --out R:/outputs/AU/AU_corpus_2026-09-15 --hardlink
  ```

## What is in this folder

| Path | What it is |
| :---- | :---- |
| `RUN_NOTE.md` | This note |
| `manifest.csv`, `manifest.jsonl` | 1,277 rows, one per document, in the Hand-off #1 shape (contract 0.2.0) |
| `crawl_log.jsonl` | 1,279 entries: 1,278 fetches (HTTP 200) and 1 store error, in fetch order; the last entry is the resume's |
| `raw/au/<law>/` | 2,555 files: 1,277 documents (`__page.html` for the epub renderings and framed captures, `__native.pdf` for the PDFs), their 1,277 `.headers.json` sidecars, and 1 orphan (issue 1) |
| `cost_report.json`, `crawl_status.json` | The engine's counters **for the resume of 17:00 only** (1 request); the crawl's own were overwritten by it. The crawl's figures are in `crawl_log.jsonl` and the `[health]` lines of `logs/crawl_stdout.log` |
| `.idmap.json` | The engine's doc_id map (1,277 laws) |
| `inventory_au.csv`, `inventory_au.jsonl` | The engine's inventory of the frontier (1,277 rows) |
| `links_used/` | The list the crawl read: `documents.jsonl`, `documents.csv`, `laws.csv` (4,765 titles, principal or not), `catalogue_meta.json`, `discovery_log.jsonl`, `build.log` (`countries/au-australia/links/README.md`) |
| `audit.md`, `audit.json` | The content check of every stored file (`tools/audit_run.py`, generic flags) |
| `logs/crawl_stdout.log` | The console output of the crawl, then a `=== top-up resume via R:` marker and the resume's |

## What is stored

| Kind (from the list) | Documents | Form |
| :---- | ----: | :---- |
| Principal Acts in force | 1,264 | 783 current compilations as HTML unpacked from the register's dated epub (`/<id>/<start>/<start>/text/original/epub`), 481 as-made PDFs (`/<id>/asmade/<start>/text/original/pdf`) for titles never compiled |
| Amending Acts (seeds) | 3 | 1 compilation as HTML, 2 as-made PDFs |
| Legislative instruments (seeds) | 7 | 2 compilations as HTML from the epub; 5 as-made instruments as Playwright captures of `/latest/text` (Round 1's path: a rendering of the viewer's frame) |
| Regulator documents (seeds) | 3 | 2 PDFs (APRA, OAIC), 1 Playwright capture of the OAIC guidance page |

By host: 1,274 from `www.legislation.gov.au`, 2 from `www.oaic.gov.au`, 1 from `www.apra.gov.au`. By method: 1,270
`requests`, 7 Playwright (the 6 captures above and one as-made PDF, `C1967A00090`, that `requests` did not get and
the browser did). The 485 PDFs all report a text layer (`pdf_is_scanned: false`); on the oldest Acts that layer is
an OCR of a scan with letters spaced out ("SURPLUS REVENUE . No. 1 5 o f 1908").

Against the Round 1 corpus of July 2026 (1,268 current documents and 33 superseded versions, in the frozen
`handoff1_v2`): this run holds 1,277 current documents and no superseded version; every principal Act in force on
the register on 2026-09-15 is here once, as its latest version.

## What is missing

### Documents not downloaded

None. The one store failure of 15:32:40 UTC (issue 1) was fetched again at 17:00:28 and is in the manifest.

### Not collected, by the settings

- **Repealed, ceased and never-in-force titles:** the harvest takes in-force titles only (`legal_status`
  `in_force`); Round 1's 33 superseded versions are not re-fetched.
- **Non-principal titles:** 3,501 of the 4,765 titles in the API's Act collection are not principal (amending and
  repeal Acts); only the 3 seeded amending Acts are fetched.
- **Legislative instruments beyond the 7 seeds:** the register's `authorises` page (the instruments under an Act)
  is not read yet (`countries/au-australia/NOTES.md` 2.3).
- **Older compilations:** one document per title, its latest version.
- **The epub bytes and the register's own PDF of a compiled Act:** the engine keeps the concatenated HTML only.

### Missing details (metadata)

- `page_count` is empty on the 792 HTML rows (the engine counts PDF pages only).
- `in_force_status` is empty on the 3 regulator documents (not legislation).
- `contract_meta` in `links_used/documents.jsonl` carries what the API gave: the title id, `No. N, YYYY`, the
  version's start and register id, the compilation number, `registeredAt`, the amending instruments (`reasons`);
  the engine's manifest does not carry these columns (`countries/au-australia/NOTES.md` 4).

## Stored, but not what the row says

From `audit.md` (generic flags; no Australian rule set yet):

| Flag | Rows | What they are |
| :---- | ----: | :---- |
| `short_principal` | 89 | As-made Acts of 1 to 4 pages (16 of one page, 41 of two, 22 of three, 10 of four), enacted 1908 to 1999 (29 in the 1970s). Genuine short Acts: the first page carries the Act's own title in 83 and, in 6, the title it was enacted under and has since lost (Flags Act 1953 as "FLAGS. No. 1 of 1954"; Meteorology Act 1955; Papua New Guinea (Members of the Forces Benefits) Act 1957 as "Native Members of the Forces Benefits"; the two Offshore Minerals fee Acts as "Minerals (Submerged Lands) (… Fees)"; the Superannuation (Self Managed Superannuation Funds) Supervisory Levy Imposition Act 1991 as "Superannuation Supervisory Levy Act 1991") |
| `one_page_principal` | 16 | The one-page Acts among them (Seat of Government Act 1908, for instance) |
| `orphan_file` | 1 | `raw/au/families_housing_…_act_2008/20260915T1532Z__native.pdf`, the PDF written at 15:32 before its header file failed (issue 1). The same bytes are in the manifest under the 17:00 file. Left in place (decision 17) |

No file is another Act's text, a notice or a landing page as far as the generic flags see; no scan without a text
layer; no duplicate bytes under two doc_ids.

## Issues encountered

1. **One title is too long for Windows.** "Families, Housing, Community Services and Indigenous Affairs and Other
   Legislation Amendment (Further 2008 Budget and Other Measures) Act 2008" (138 characters) becomes a 138-character
   folder name; under `<ws>\outputs\AU\AU_ws_2026-09-15\raw\au\`, the header file's path is 260 characters, one
   over the limit. At 15:32:40 UTC the PDF was written and the sidecar raised `FileNotFoundError`; the engine logged
   `outcome: error` and went on. **Effect:** the document was not in the manifest at the crawl's end (1,276 rows).
   **Done:** the workshop was mapped to `R:` (`subst R: C:\Users\woshi\Desktop\rdtii-finale-1-scraping`, 38
   characters to `raw\au\`) and the same run resumed through it at 17:00:28: the engine skipped the 1,276 stored
   rows and fetched the one document (HTTP 200, 106,495 bytes, 41 pages), now `au-fhcsiaolaa2008-001`. The 15:32
   PDF stays as an orphan file. **Still to do:** the engine should cap the folder name (`countries/au-australia/NOTES.md`
   2.5); until then, a reader on Windows reaches that sidecar through a short path or with long paths enabled
   (`HKLM\SYSTEM\CurrentControlSet\Control\FileSystem\LongPathsEnabled`, off on this machine). Two Singaporean
   titles hit the same limit the same day.
2. **The resume overwrote two of the engine's files.** `crawl_status.json` and `cost_report.json` describe the
   resume (1 request, 2.3 s), not the 4 h 27 min crawl. The crawl's counts survive in `crawl_log.jsonl` (1,278 fetches)
   and in the `[health]` lines of `logs/crawl_stdout.log` (the last one before the marker: `1273/1277 attempted,
   1272 stored total`, then `manifest has 1276 row(s); validate OK`). A resume that keeps the earlier counters is a further engine request.
3. **The generic audit flags fire on short Acts.** 89 as-made Acts of at most four pages are flagged
   `short_principal` because the rule was calibrated on Malaysia, where a short principal-act file is usually a
   repeal notice. Here they are the Acts themselves (see above). An Australian rule set should exempt an as-made
   Act whose first page carries "No. N of YYYY" and its title, and read the enactment title for renamed Acts.
4. **Seven documents came through the browser.** Five as-made legislative instruments are stored as Playwright
   captures of `/latest/text` (Round 1's path for instruments the list gives as `form: html`): a rendering of the
   viewer's frame, not the register's file. The OAIC guidance page likewise. One as-made PDF (`C1967A00090`) failed
   in `requests` and succeeded in the browser; the log keeps the browser's answer only.
5. **The list's API harvest needs `$orderby=id`.** A first harvest that morning paged with `$skip` alone and got
   340 titles twice while missing others; the list of 12:33 orders by id and reports `repeated: 0`
   (`countries/au-australia/NOTES.md` 1.3). The crawl read that list.
6. **Pace.** 1,277 documents in 16,010 s: 12.5 s each, the 10 s delay plus jitter and the download (the largest
   document is the Income Tax Assessment Act 1997, 33.4 MB of HTML; the Criminal Code is 7.2 MB). No throttling, no failed fetch on the register's side.

## Changes after the run

- **2026-09-15 17:00:28 UTC:** the run resumed through `R:` for one document (issue 1); the manifest went from
  1,276 to 1,277 rows. Checked with `scrape.py --validate` through `R:` (0 errors) and the audit (0 missing).
- **2026-09-15 17:01:53 UTC:** `outputs/AU/AU_corpus_2026-09-15` built from this run alone (1,277 documents, hard
  links, validation OK; `CORPUS_NOTE.md` there).

## Decisions still open that affect this run

- **Long paths.** Cap the storage folder name in the engine (hand-back), enable Windows long paths on the
  machines that read the runs, or keep reading through a `subst` drive. Until one is chosen, one sidecar here
  (and the corpus copy of it) is unreadable from the workshop path.
- **An Australian audit rule set** (`RULES["AU"]` in `tools/audit_run.py`): as-made short Acts, renamed titles,
  the framed captures.
- **Keep the epub bytes** beside the HTML (engine request, `countries/au-australia/NOTES.md` 2.5): a reader who
  wants the register's own file must fetch it again today.
- **Scope beyond this run:** repealed and ceased titles, instruments under the seed Acts (`authorises`), older
  compilations; the update check (`countries/au-australia/updates/WORKFLOW.md`, a stub).
- **What downstream reads.** `outputs/README.md` rule 6: one `HANDOFF1_DIR` per stage run, so Australia is read
  from `AU_corpus_2026-09-15` in a run of its own, or the corpora are joined first (not built).
