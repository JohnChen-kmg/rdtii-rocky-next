# Run note: MY_ws_2026-09-13

Malaysia, web scraping, 13 September 2026. A test crawl of scope `seed`, the first live test of the new Malaysia
scraper: the 21 seed laws and 4 later amending acts of seed acts. The folder also holds that evening's dry run and a
discovery-only check.

**Superseded by `MY_ws_2026-09-14`,** which holds all 17 documents stored here, byte for byte, and the 8 that failed
here. Match the two runs by `content_sha256` or `source_url`, not by `doc_id`: `my-csr2024-001` is the Cyber Security
(Compounding of Offences) Regulations 2024 here, but the Licensing of Cyber Security Service Provider Regulations
2024 in `MY_ws_2026-09-14`, where the Compounding Regulations are `my-csr202460e1-001`.

## At a glance

| | |
| :---- | :---- |
| Country | Malaysia (`MY`) |
| Run type | Test crawl, scope `seed`. Discovery ran inside the crawl, before the link list existed |
| Date | 2026-09-13 |
| Time, UTC | Dry run 19:55:11 to 19:56:24. Crawl 19:57:59 to 20:02:04 (245 s). Discovery-only check: requests 21:02:36 to 21:04:42 (the script took 130.5 s) |
| Time, machine clock | US Eastern Daylight Time, UTC−4: crawl 15:57 to 16:02 |
| Result | 25 documents fetched: **17 stored**, **8 not recorded** because the Windows path was too long |
| Size | 12.6 MB of stored documents, out of 75.3 MB downloaded (`cost_report.json`). Of the 62.7 MB not recorded, 32 MB is in `raw/` as 2 unrecorded files (missing item 2); the rest was never written |
| Validation | `scrape.py --validate manifest.csv`: 17 rows, 0 errors, 0 warnings, contract 0.2.0 (run again on 2026-09-14) |
| Status | Test run, superseded. Kept for the record |
| Checked | Re-checked against the files by independent reviewers on 2026-09-14 |

## Steps and times

| Step | UTC | Requests | Output |
| :---- | :---- | :---- | :---- |
| 1. Dry run, scope `seed` | 19:55:11 to 19:56:24 | Discovery requests to lom, not logged. No documents | `dry_run/`: status only. 80 candidates, none attempted: the 25 seed-scope documents plus 55 subsidiary instruments from the seed acts' timelines, because timeline instruments were still switched on for this step |
| 2. Crawl, scope `seed` | 19:57:59 to 20:02:04 | The console reports 12 discovery requests (robots.txt, 5 listing requests, 6 timeline links). Each timeline link also redirected, and the scraper followed the redirect without a pause or a count, so lom received 18. Then 25 documents | `raw/`, `manifest.*`, `crawl_log.jsonl` |
| 3. Discovery-only check of the revised scraper | 21:02:36 to 21:04:42 | 28 to lom: robots.txt, 5 listing requests, and 11 detail pages (6 acts, 5 amendments) at two hops each, every hop paced. No documents | `discovery_only/`: 28 candidates |

## How it was run

- **Engine:** the Round 1 crawl engine in sandbox copies in the session scratchpad: `sbx` for steps 1 and 2,
  `sbx2` for step 3. The repo was not used or changed.
- **Malaysia scraper:** the single file `countries/my-malaysia/scraper.py`, copied into the sandbox as
  `adapters/my_gazette.py`. That was before the package split and before the link list (both 2026-09-14).
  - It was being edited during the session, so each step used a different copy:
    - step 1: the copy of 19:54 UTC, with instruments from timelines switched on (at most 25 per act);
    - step 2: the copy of 19:57 UTC, with them switched off and a P.U. (A)-only filter added;
    - step 3: the rewrite copied at 21:02 UTC, which follows redirects hop by hop.
  - None of these copies survives in the sandboxes. The session transcript is the only record.
- **Registry:** `countries/my-malaysia/sources.yaml` of the time. `lom.subsidiary_from_timeline` was changed from
  `true` to `false` at 19:57:42 UTC, between steps 1 and 2.
- **Politeness:**
  - Steps 1 and 2 set `REQUEST_DELAY_MS=4000`, slower than the default 3000, plus up to 2 s jitter, one request at
    a time. The 6 timeline redirects of each step went out without a pause.
  - Step 3 ran at the default 3000 ms plus up to 1.5 s jitter; its logged waits are 3.0 to 4.4 s.
- **Commands** (from `<sandbox>`):

  ```
  REQUEST_DELAY_MS=4000 python -X utf8 scrape.py --economy MY --scope seed --dry-run --out <scratchpad>/runs/my_seed_dry
  REQUEST_DELAY_MS=4000 python -X utf8 scrape.py --economy MY --scope seed --out <scratchpad>/runs/my_seed_live
  ```

  Step 3 was a short Python script that called the adapter's discovery directly and saved its candidates, its
  request log and the robots.txt record.

## What is in this folder

| Path | What it is |
| :---- | :---- |
| `RUN_NOTE.md` | This note |
| `manifest.csv`, `manifest.jsonl` | 17 rows, Hand-off #1 format (contract 0.2.0) |
| `crawl_log.jsonl` | 33 lines: one `ok` line per document, plus an `error` line for each of the 8 not recorded |
| `raw/my/` | 25 folders: the 17 documents with their header files, 2 folders holding one unrecorded PDF each (missing item 2), and 6 empty folders left by the store errors |
| `cost_report.json`, `crawl_status.json`, `.idmap.json` | Engine counters, final status, document-ID map |
| `logs/crawl_stdout.log` | The crawl's console output. The last 60 lines of step 1's console output survive only in the session transcript |
| `dry_run/` | Step 1's status file, an empty crawl log and an empty ID map |
| `discovery_only/` | Step 3's `run.json` (summary and robots.txt record), `candidates.json` and `discovery_log.jsonl` |

## What is stored

17 documents: 16 native PDF and 1 scanned PDF (the Personal Data Protection Regulations 2013).

- **From lom, principal acts (6):**
  - Personal Data Protection Act 2010
  - Cyber Security Act 2024
  - Computer Crimes Act 1997
  - Criminal Procedure Code
  - Security Offences (Special Measures) Act 2012
  - Income Tax Act 1967
- **From lom, amending acts (5):**
  - Personal Data Protection (Amendment) Act 2024
  - Criminal Procedure Code (Amendment) (No. 2) Act 2023
  - Criminal Procedure Code (Amendment) Act 2024
  - Criminal Procedure Code (Amendment) Act 2025
  - Security Offences (Special Measures) (Amendment) Act 2024
- **From agency sites (6):**
  - `www.nacsa.gov.my`: Cyber Security (Compounding of Offences) Regulations 2024, and Cyber Security
    (Exemption) Order 2025
  - `www.pdp.gov.my`: Personal Data Protection Standard 2015, and Personal Data Protection Regulations 2013
  - `www.sc.com.my`: Guidelines on Technology Risk Management (SC-GL/2-2023)
  - `www.bnm.gov.my`: Risk Management in Technology (RMiT) Policy Document (2025)

## What is missing

1. **8 documents fetched but not recorded.** The engine could not write their files: the paths were 263 to 273
   characters, and Windows allows 259. The output folder sat deep inside the session scratchpad.
   - Personal Data Protection Code of Practice for Banking and Financial Sector 2017 (a web page)
   - Personal Data Protection Code of Practice for the Communications Sector 2017 (a web page)
   - Personal Data Protection Guideline on Cross-Border Personal Data Transfer (GP 3/2025)
   - Personal Data Protection Guideline on the Appointment of Data Protection Officer (2025)
   - Personal Data Protection Guideline on Data Breach Notification (2025)
   - Cyber Security (Licensing of Cyber Security Service Provider) Regulations 2024
   - Cyber Security (Notification of Cyber Security Incident) Regulations 2024
   - Cyber Security (Period for Cyber Security Risk Assessment and Audit) Regulations 2024

   For 6 of the 8 nothing was written. All 8 were stored by `MY_ws_2026-09-14`.
2. **2 PDFs written without a header file or a manifest row.**
   - `raw/my/cyber_security_notification_of_cyber_security_incident_regulations_2024/20260913T2001Z__native.pdf`
     (0.2 MB)
   - `raw/my/personal_data_protection_guideline_on_data_breach_notification_2025/20260913T2001Z__native.pdf`
     (31.8 MB)

   No manifest row or ID-map entry refers to them. Only the store-error lines in `crawl_log.jsonl` and
   `logs/crawl_stdout.log` name their header files, at the scratchpad path. They are kept as found.
3. **3 commencement orders now in the seed scope were not fetched:** P.U. (B) 522/2024 (commencing A1727), P.U. (B)
   329/2025 (A1692) and P.U. (B) 434/2024 (A1722).
   - The crawl's scraper did not look for commencement orders.
   - Step 3's revised scraper lists them (`discovery_only/candidates.json`), and `MY_ws_2026-09-14` stored them.
4. **Subsidiary instruments on the seed acts' timelines.** They were not fetched in step 2
   (`lom.subsidiary_from_timeline` off).
   - Step 3 counted 256 of them.
   - The dry run, with the setting still on, listed 55: 25 P.U. (B) notices under the Criminal Procedure Code, 21
     P.U. (A) under the Income Tax Act, 6 under the Cyber Security Act and 3 P.U. (B) under the PDPA.
5. **Everything outside the seed scope,** by design, since this was a test.

## Issues encountered

1. **The Windows path length limit** (missing items 1 and 2). This is why run folders now sit at a short path with a
   short name (`outputs/README.md`).
2. **lom's robots.txt answered HTTP 500.**
   - The crawl's console output records it at the start of step 2.
   - `discovery_only/run.json` records it again at 21:02:36 UTC.
   - The portal was crawled anyway, under the rule that became decision 9.
3. **Unpaced requests.**
   - The 6 timeline redirects in each of steps 1 and 2 went out without a pause.
   - The engine's limiter spaces request starts per host and does not wait after a download ends. The crawl log
     shows lom downloads ending 2 s apart despite the 4 s setting: Criminal Procedure Code at 19:59:35 and
     Security Offences (Special Measures) Act 2012 at 19:59:37 UTC.
4. **Agency sites.**
   - robots.txt was read for lom only, never for `www.pdp.gov.my`, `www.nacsa.gov.my`, `www.sc.com.my` or
     `www.bnm.gov.my`.
   - The two PDP Code of Practice pages were loaded with Playwright in headless Chromium, which also fetches their
     scripts, styles and images, unlogged (`cost_report.json`: `playwright` 2).
5. **Step 1's discovery requests were not logged.** Its status file survives, and the last 60 lines of its console
   output are in the session transcript.
6. **`crawl_status.json` counts the 8 as successes.** It reports 25 attempted and `recent_outcomes` `ok` 25, although
   8 of those were not recorded. Its `stored_total` (17) is right, as is `docs_retrieved` in `cost_report.json`. The
   manifest (17 rows) and the `error` lines in `crawl_log.jsonl` are the reliable counts.

## Changes after the run

- **2026-09-14, copied here** from the session scratchpad: `runs/my_seed_live`, `runs/my_seed_dry`,
  `runs/my_seed_discovery_v2` and `runs/my_seed_live.log`.
  - At the copy, the seed crawl's 42 files were compared byte for byte with the scratchpad and the manifest was
    validated again. After the move into `outputs\MY\`, all 49 copied files were compared again: 0 differences.
  - The scratchpad copies were left in place, but the scratchpad is temporary.
- **2026-09-14, moved into the country folder** `outputs\MY\` (a rename inside the workspace). The manifest was
  validated again, the 17 stored documents were checked against their manifest SHA-256, and the folder's 50 files
  were counted.
- **Logs still name the scratchpad folder.** `logs/crawl_stdout.log` and the store errors in `crawl_log.jsonl`
  refer to it.
- **2026-09-14, this note was checked** against the files by independent reviewers, and corrected.
- 2026-09-15: `audit.md` and `audit.json` added by `tools/audit_run.py` (decision 17): 17 documents read, 1 flagged (the PDP Regulations 2013 file has no text layer), the 8 failed fetches listed under "missing". Every document of this run is superseded in `MY_corpus_2026-09-15` by the 2026-09-14 copies.

## Decisions still open that affect this run

None: the run is superseded. The open decisions are listed in `MY_ws_2026-09-14/RUN_NOTE.md`.
