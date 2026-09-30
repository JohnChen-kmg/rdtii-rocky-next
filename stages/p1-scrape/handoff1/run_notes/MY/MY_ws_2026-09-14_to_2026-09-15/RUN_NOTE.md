# Run note: MY_ws_2026-09-14_to_2026-09-15

Malaysia, web scraping, 15 September 2026: an **update check** covering 2026-09-14 (the last check) to 2026-09-15,
followed by the crawl of what it found. The first run of the update module after its three reviews, and the first
to fetch anything. It also retried the 4 files that failed on 2026-09-14.

## Read this first

- **6 documents fetched:** a new act (National Trust Fund Act 2026, Act 885), a newer Service Tax Act 2018
  (as at 1 January 2025), three new amending acts (A1794 to A1796) and one commencement order (P.U. (B)
  200/2026, commencing A1780).
- **The 4 files that failed on 2026-09-14 failed again,** each with HTTP 500 from the portal: Trade Marks Act
  1976, Passports Act 1966, Supply Act 2025, Supply Act 2021. The fault is on the portal's side (the same four
  addresses, two attempts each, two days running).
- **The current corpus is `MY_corpus_2026-09-15`,** the three crawls merged by `tools/merge_corpus.py` (decision 17):
  this run's 6 documents supersede the Service Tax Act 2018 of 2026-09-14 and add the other 5. Two of them
  (`my-rta2026-001`, `my-puca2026-001`) got a doc_id the 2026-09-14 run had given to other documents and are
  `-002` in the corpus.

## At a glance

| | |
| :---- | :---- |
| Country | Malaysia (`MY`) |
| Run type | Update check against `MY_ws_2026-09-14_to_2026-09-14` (since 2026-09-14, baseline mode), then the crawl of its delta list |
| Date | 2026-09-15 |
| Time, UTC | Check 05:02:22 to 05:05:15 (34 requests). Crawl 05:05:42 to 05:06:23 (41 s) |
| Time, machine clock | US Eastern Daylight Time, UTC−4: 01:02 to 01:06 |
| Result | 300 changes found: 10 documents to fetch, **6 stored**, **4 failed** (HTTP 500), 290 recorded only |
| Size | 2,084,057 bytes (2.1 MB), 174 pages |
| Validation | `scrape.py --validate manifest.csv`: 6 rows, 0 errors, 0 warnings, contract 0.2.0 |
| Checked | Figures from `links_used/discovery_log.jsonl`, `links_used/catalogue_meta.json`, `changes.json`, `crawl_log.jsonl`, `manifest.jsonl`, `cost_report.json` |

## Steps and times

| Step | UTC | Requests | Output |
| :---- | :---- | :---- | :---- |
| 1. Update check | 05:02:22 to 05:05:15 | 34 to lom, every wait at least 3.0 s: robots.txt (HTTP 500); the updated-acts page and 2 POSTs (886 records); the amendment page and 1 POST (409 rows, 405 acts); 1 POST each for the newest 500 P.U. (A) and P.U. (B); the detail pages of the 7 changed or unstored acts and 6 amending acts, 2 hops each. No document | `links_used/` (10 documents), `changes.json`, `changes.md` |
| 2. Crawl of the delta list | 05:05:42 to 05:06:23 | 10 document fetches, plus a Playwright retry for each of the 4 HTTP 500 files | `raw/`, `manifest.*`, `crawl_log.jsonl` |

## How it was run

- **Engine and scraper:** the sandbox copy `scratchpad\sbx2\p1-scrape` with `countries/my-malaysia/scraper/` and
  `updates/` installed as of 2026-09-15 (after the three reviews).
- **Registry:** `countries/my-malaysia/sources.yaml` with `lom.timeline: all` (set that morning, decision 17) and
  `links/seed_laws.yaml`. Fingerprint `cfg_sha256` cbb0bd1e…, which differs from the 2026-09-14 lists (they were
  built with `timeline: rule`).
- **Baseline:** listing state from `MY_ws_2026-09-14_to_2026-09-14\links_used\laws.csv`; stored documents from
  every run (1,311 URLs); the 5 duplicates from `MY_ws_2026-09-14\crawl_log.jsonl`.
- **Commands** (from `<sandbox>`, `<ws>` the workshop):

  ```
  PYTHONPATH=src python -m p1_scrape.adapters.my_gazette.updates --outputs <ws>/outputs/MY \
      --registry <ws>/countries/my-malaysia/sources.yaml --seeds <ws>/countries/my-malaysia/links/seed_laws.yaml
  LOM_FRONTIER=links_file LOM_LINKS_FILE=<run>/links_used/documents.jsonl \
      python scrape.py --economy MY --scope all --out <run>
  ```

## What is in this folder

| Path | What it is |
| :---- | :---- |
| `RUN_NOTE.md` | This note |
| `changes.md`, `changes.json` | The 300 changes since 2026-09-14, fetched or not, with the reason |
| `links_used/documents.jsonl`, `documents.csv` | The delta list: the 10 documents to fetch, each with `contract_meta.update` |
| `links_used/laws.csv` | One row per listed act (1,291): 1,236 "unchanged since MY_ws_2026-09-14_to_2026-09-14", 45 "the portal offers no document", 10 in the list |
| `links_used/catalogue_meta.json`, `discovery_log.jsonl` | The check's settings, request count, and its 34 requests |
| `manifest.jsonl`, `manifest.csv`, `crawl_log.jsonl`, `cost_report.json`, `crawl_status.json`, `.idmap.json` | The engine's output for the 6 documents |
| `raw/my/<law>/` | The 6 documents and their header files |
| `logs/update_check.log`, `logs/crawl_stdout.log` | The console output of both steps |

## What is stored

| Document | Kind | Change | Pages |
| :---- | :---- | :---- | ----: |
| National Trust Fund Act 2026 (Act 885) | principal act | new act, listed since yesterday (as at 15 September 2026) | 26 |
| Service Tax Act 2018 (Act 807) | principal act | new consolidation, as at 1 January 2025 (the crawl had 1 December 2024) | 111 |
| Employment Insurance System (Amendment) Act 2026 (A1796) | amending act | new | 11 |
| Sexual Offences Against Children (Amendment) Act 2026 (A1795) | amending act | new | 4 |
| Road Transport (Amendment) Act 2026 (A1794) | amending act | new | 20 |
| P.U. (B) 200/2026, commencing A1780 | commencement order | published 5 June 2026, cited by A1780 | 2 |

All native PDFs, from `lom.agc.gov.my`.

## What is missing

1. **4 documents failed again with HTTP 500:** Trade Marks Act 1976 (Act 175), Passports Act 1966 (Act 150), Supply
   Act 2025 (A1740), Supply Act 2021 (A1626). The same addresses as on 2026-09-14; the portal does not serve them.
   Every future check will report them `not_stored` and try again.
2. **290 changes recorded, not fetched**, as the settings say (decision 12): 133 P.U. (A) instruments under acts
   outside the core groups, 157 P.U. (B) notices no amending act cites, all published since 17 May 2026 (the 120-day
   look-back). They are listed in `changes.md`.
3. **Four new amending acts' detail pages held no timeline** (A1791, A1794, A1795, A1796), so no commencement
   order was found for them; none cites one yet.
4. **The listing grew:** 886 principal acts (885 yesterday), 409 amendment rows (406).

## Issues encountered

1. **lom's robots.txt answered HTTP 500** (05:02:22 UTC), as on every read. Crawled under decision 9.
2. **`timeline: all` was set before this check** (decision 17), so the check read the detail pages of every act it
   touched: 7 principal acts and 6 amending acts, 26 requests of the 34.
3. **Failed downloads got an immediate second request** through Playwright, unpaced (the engine gap of
   `POLICY.md` 5.5), as on 2026-09-14.

## Changes after the run

- 2026-09-15: `logs/update_check.log` copied in from the session scratchpad.
- 2026-09-15: `audit.md` and `audit.json` added by `tools/audit_run.py` (decision 17): 6 documents read, 0 flagged,
  the 4 failed fetches listed under "missing". Merged into `MY_corpus_2026-09-15`.

## Decisions still open that affect this run

- None. Decision 17 (2026-09-15) settled the open items; the 4 failed files are the portal's problem and are retried
  by every check.
