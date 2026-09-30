# Run note: MY_ws_2026-09-15_to_2026-09-15

Malaysia, web scraping, 15 September 2026: an **update check with the rebuilt link list** (`--list`, the mode built
that morning after the developer's answer "yes" to fetching what the `timeline: all` rebuild revealed), followed by
the crawl of what it found. The check covered 2026-09-15 to 2026-09-15 against `MY_ws_2026-09-14_to_2026-09-15`.

## Read this first

- **75 documents fetched:** 46 "amending act" rows the timelines alone reveal (P.U. orders and gazette supplements
  listed under an act's AMENDMENTS) and 29 commencement orders found on amending acts' pages.
- **23 fetches failed:** the 4 HTTP 500 files of 2026-09-14 (Acts 175 and 150, A1740, A1626), 18 old gazette or
  P.U. files that also answer HTTP 500, and 1 that did not answer at all. Every later check reports them again.
- **The corpus was rebuilt with this run:** `MY_corpus_2026-09-15`, 1,391 documents (11:58 UTC).
- **27 of the 75 stored files are scans with no text layer** (old gazette supplements): OCR needed (`audit.md`).

## At a glance

| | |
| :---- | :---- |
| Country | Malaysia (`MY`) |
| Run type | Update check against `MY_ws_2026-09-14_to_2026-09-15` (since 2026-09-15, baseline mode) with `--list countries/my-malaysia/links/documents.jsonl`, then the crawl of its delta list |
| Date | 2026-09-15 |
| Time, UTC | Check 11:33:27 to 11:35:09 (18 requests). Crawl 11:36:00 to 11:53:02 (17 min) |
| Time, machine clock | US Eastern Daylight Time, UTC−4: 07:33 to 07:53 |
| Result | 393 changes found: 98 documents to fetch, **75 stored**, **23 failed**, 295 recorded only |
| Size | 327,126,376 bytes (327 MB), 1,302 pages |
| Validation | `scrape.py --validate manifest.csv`: 75 rows, 0 errors, 0 warnings, contract 0.2.0 |
| Audit | `tools/audit_run.py`: 46 rows flagged (27 `no_text_layer`, 19 `subsidiary_amendment`), 23 missing |
| Checked | `links_used/discovery_log.jsonl`, `links_used/catalogue_meta.json`, `changes.json`, `crawl_log.jsonl`, `manifest.jsonl`, `crawl_status.json`, `audit.json` |

## Steps and times

| Step | UTC | Requests | Output |
| :---- | :---- | :---- | :---- |
| 1. Update check with the list | 11:33:27 to 11:35:09 | 18 to lom, every wait at least 3.0 s: robots.txt (HTTP 500); the updated-acts page and 2 POSTs; the amendment page and 1 POST; 1 POST each for the newest 500 P.U. (A) and P.U. (B); the detail pages of the 4 unstored acts (two hops each; A1791's timeline unreadable). The link list was compared offline: 1,414 rows, 98 stored by no run | `links_used/` (98 documents), `changes.json`, `changes.md` |
| 2. Crawl of the delta list | 11:36:00 to 11:53:02 | 98 document fetches, plus a Playwright retry for each failure | `raw/`, `manifest.*`, `crawl_log.jsonl` |
| 3. Audit | 11:58 | none | `audit.md`, `audit.json` |
| 4. Corpus | 11:58 | none | `outputs/MY/MY_corpus_2026-09-15` rebuilt from the 4 runs |

## How it was run

- **Engine and scraper:** the sandbox copy `scratchpad\sbx2\p1-scrape` with `countries/my-malaysia/scraper/` and
  `updates/` (with the new `listcheck.py`) installed at 11:33 UTC.
- **Registry:** `countries/my-malaysia/sources.yaml` (`lom.timeline: all`) and `links/seed_laws.yaml`; the link list
  `countries/my-malaysia/links/documents.jsonl` rebuilt 05:07 to 07:21 UTC (fingerprint cbb0bd1e…, the same as
  the registry's).
- **Baseline:** listing state from `MY_ws_2026-09-14_to_2026-09-15\links_used\laws.csv`; stored documents from every
  run (1,317 URLs); the 5 duplicates from `MY_ws_2026-09-14\crawl_log.jsonl`.
- **Commands** (from `<sandbox>`, `<ws>` the workshop):

  ```
  PYTHONPATH=src python -m p1_scrape.adapters.my_gazette.updates --outputs <ws>/outputs/MY \
      --registry <ws>/countries/my-malaysia/sources.yaml --seeds <ws>/countries/my-malaysia/links/seed_laws.yaml \
      --list <ws>/countries/my-malaysia/links/documents.jsonl
  LOM_FRONTIER=links_file LOM_LINKS_FILE=<run>/links_used/documents.jsonl \
      python scrape.py --economy MY --scope all --out <run>
  PYTHONPATH=src python tools/audit_run.py <run>
  PYTHONPATH=src python tools/merge_corpus.py --outputs <ws>/outputs/MY --out <ws>/outputs/MY/MY_corpus_2026-09-15
  ```

## What is in this folder

| Path | What it is |
| :---- | :---- |
| `RUN_NOTE.md` | This note |
| `changes.md`, `changes.json` | The 393 changes: 4 `not_stored` acts, 291 P.U. instruments recorded, and the link list against the runs (98 `not_in_runs`, 0 stored under another address) |
| `links_used/documents.jsonl`, `documents.csv` | The delta list: the 98 documents to fetch, each with `contract_meta.update` (`change: not_in_runs` for the 94 from the list alone) |
| `links_used/laws.csv` | One row per listed act (1,291) |
| `links_used/catalogue_meta.json`, `discovery_log.jsonl` | The check's settings, `delta.link_list` figures, and its 18 requests |
| `manifest.jsonl`, `manifest.csv`, `crawl_log.jsonl`, `cost_report.json`, `crawl_status.json`, `.idmap.json` | The engine's output for the 75 documents |
| `raw/my/<law>/` | The 75 documents and their header files |
| `audit.md`, `audit.json` | The content check |
| `logs/update_check.log`, `logs/crawl_stdout.log` | The console output of both steps |

## What is stored

| Kind | Documents | Notes |
| :---- | ----: | :---- |
| Amendments known only from timelines (`amending_act` rows without an A-number: P.U. orders and gazette supplements listed under an act's AMENDMENTS) | 46 | 19 are P.U. orders (`subsidiary_amendment`, informational); 27 are scans with no text layer |
| Commencement orders (P.U. (B)) found on amending acts' pages | 29 | Native PDFs |

All from `lom.agc.gov.my`. The doc_ids this run minted collide with 7 ids the 2026-09-14 run gave to other documents;
the corpus keeps the older ids and renames these rows `-002`/`-003` (`MY_corpus_2026-09-15/CORPUS_NOTE.md`).

## What is missing

1. **23 documents failed:** the 4 HTTP 500 files retried since 2026-09-14 (Trade Marks Act 1976, Passports Act 1966,
   Supply Act 2025, Supply Act 2021); 18 amendments known only from timelines whose old files answer HTTP 500
   (P.U. (A) 67/1972, P.U. (A) 77/2007, P.U. (B) 111/2007 and others under Acts 273, 353, 499, listed in
   `audit.md`); and P.U. (A) 158/2010 (Act 278), which did not answer (status 0). The portal does not serve them.
2. **295 changes recorded, not fetched:** 291 P.U. instruments outside the core acts (decision 12) and the 4
   `not_stored` acts counted above.
3. **The 5 Cyber Security Act instruments** in the list are stored from NACSA under other addresses; the engine
   logged their lom copies as byte-duplicates on 2026-09-14, so the list comparison skipped them.

## Stored, but not what the row says

From `audit.md`: 27 scans with no text layer (old gazette supplements: OCR needed); 19 rows recorded as amending
acts that are P.U. orders, as the portal's timelines give them (informational). No wrong-file flag.

## Issues encountered

1. **lom's robots.txt answered HTTP 500** (11:33:27 UTC), as on every read. Crawled under decision 9.
2. **Old gazette and P.U. files fail on the portal's side:** 19 of the 94 timeline-only documents answered HTTP 500
   or nothing. The engine retried each once through Playwright, unpaced (the engine gap of `POLICY.md` 5.5).
3. **The crawl took 17 minutes for 98 documents** (about 10 s each): large gazette supplements (up to 60 MB) and
   the 23 failures' retries.

## Changes after the run

- 2026-09-15: `logs/update_check.log` copied in from the session scratchpad. `audit.md` and `audit.json` added.
  `MY_corpus_2026-09-15` rebuilt with this run (1,391 documents).

## Decisions still open that affect this run

- None. The list-vs-runs mode is the check's `--list` option (decision 17's knock-on, built 2026-09-15 on the
  developer's "yes").
