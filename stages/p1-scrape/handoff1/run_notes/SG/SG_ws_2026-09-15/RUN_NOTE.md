# Run note: SG_ws_2026-09-15

Singapore, web scraping, 15 to 16 September 2026: the **first crawl from a link list**, every current act, the
regulations under the seed acts and the Acts Supplement of this year and last, from Singapore Statutes Online
(`sso.agc.gov.sg`), plus four regulator documents.

## Read this first

- **739 documents stored**, being 524 of the 525 current acts, all 188 pieces of subsidiary legislation under the
  seed acts, 24 of the 25 Acts Supplement acts, 5 regulator documents, and 8 seed documents the list carries at a
  different address (issue 4). **Two documents are missing** (issue 3).
- **The 298 repealed acts were dropped on purpose** (decision 19), after the developer weighed them against the
  portal's rate limit. They keep their row, status and repeal date in `law_table.csv`, fetched or not.
- **This run took 24 hours of wall clock for 15 hours of fetching**, in 15 stretches, because the portal's edge
  challenges our client after a while and has to be waited out (`countries/sg-singapore/NOTES.md` 1.3). Nothing
  here was hurried and nothing was worked around.
- **Read this run through a short path.** Two subsidiary titles are long enough that their files cannot be opened
  from `C:\Users\woshi\Desktop\rdtii-finale-1-scraping\outputs\SG\…` on Windows. Map the workshop to a drive
  (`subst R: <ws>`) and read `R:\outputs\SG\…` (issue 2).
- **Validation reports one error, and it is a portal fact, not a fault:** two documents have identical bytes
  because the seed file names one instrument by its old title (issue 1). The corpus keeps one of them.
- **The corpus `outputs/SG/SG_corpus_2026-09-16` is what downstream reads for Singapore:** 738 documents,
  validation clean.

## At a glance

| | |
| :---- | :---- |
| Country | Singapore (`SG`) |
| Run type | Full crawl from the link list of 12:58 UTC on 2026-09-15 (`links_used/`), scope `all`, in 15 stretches; from 05:17 UTC on 2026-09-16 against the filtered list without the repealed acts (decision 19) |
| Date | 2026-09-15 to 2026-09-16 |
| Time, UTC | 2026-09-15 14:09:35 to 2026-09-16 14:19:30: **24.2 hours elapsed, 14.8 hours fetching**, the rest resting between challenges |
| Time, machine clock | US Eastern Daylight Time, UTC−4: 10:09 on 15 September to 10:19 on 16 September |
| Result | 1,041 documents listed, 743 after the repealed acts were dropped: **739 stored**, **2 missing**, 0 duplicates fetched twice on purpose |
| Size | 188,570,104 bytes (189 MB), 38,428 pages. One document is a scan; every other has a text layer |
| Validation | `scrape.py --validate manifest.csv` through `R:`: 739 rows, **1 error** (two rows share a content hash, issue 1), 0 warnings, contract 0.2.0 |
| Audit | `tools/audit_run.py` with `RULES["SG"]` (written 2026-09-16): 29 rows flagged, 2 missing, 26 orphan files. Nothing is a wrong file: 22 amending acts in their gazette form, 5 short acts printed in full, and the duplicate pair of issue 1 |
| Law table | `law_table.csv`: 1,072 laws, 731 of them scraped; `use` is `evidence` on 1,045, `evidence, text stale` on 2, `linkage` on 24, `linkage, text needed` on 1 (decision 20) |
| Status | **Usable.** Read the five points above first |
| Checked | `crawl_status.json`, `crawl_log.jsonl`, `manifest.jsonl`, `links_used/`, `audit.json`, `law_table.csv`, `logs/crawl_stdout.log`, the loop's log in the session scratchpad |

## Steps and times

| Step | UTC | Requests | Output |
| :---- | :---- | :---- | :---- |
| 1. Build the link list | 2026-09-15 11:50 to 12:58 | 540 to `sso.agc.gov.sg` at 6 s or more: robots.txt, the Current listing twice, the Repealed and Uncommenced listings, the Acts Supplement of 2026 and 2025, every current act's detail page, the subsidiary tab of the seed acts. The edge challenged 50 of the act pages from about the 45th minute | `countries/sg-singapore/links/` (1,041 documents), copied here as `links_used/` |
| 2. Crawl, 15 stretches | 2026-09-15 14:09 to 2026-09-16 14:19 | 1,031 fetches: 766 answered HTTP 200, 220 the challenge (HTTP 202), 45 no answer at all | `raw/`, `manifest.*`, `crawl_log.jsonl` |
| 3. Validate and audit | 2026-09-16 14:21 | none | `audit.md`, `audit.json` |
| 4. Law table | 2026-09-16 14:21 | none | `law_table.csv` |
| 5. Corpus | 2026-09-16 14:22 | none | `outputs/SG/SG_corpus_2026-09-16` |

Every stretch, with what it cost. A stretch ends when the engine stops itself after ten challenged answers in a
row; the rest between them is the wait for the challenge to lift.

| Rest before | Pace | Crawled (UTC) | Fetches | Stored |
| :---- | :---- | :---- | ----: | ----: |
| 1 h (the first lift) | 6 s | 09-15 14:09 to 14:35 | 135 | 127 |
| 13 min | 15 s | 09-15 15:36 to 15:39 | 11 | 9 (lost: a watcher killed a healthy crawl, issue 5) |
| 13 min | 15 s | 09-15 15:52 to 16:51 | 96 | 74 |
| 62 min | 30 s | 09-15 17:53 to 19:03 | 106 | 74 |
| 21 min | 15 s | 09-15 19:24 to 19:46 | 58 | 48 |
| 20 min | 15 s | 09-15 20:06 to 20:31 | 53 | 39 |
| 21 min | 15 s | 09-15 20:52 to 21:11 | 35 | 21 |
| **46 min** | **60 s** | **09-15 21:59 to 09-16 03:38** | **266** | **203** |
| 30 min | 60 s | 09-16 04:09 to 04:59 | 41 | 28 |
| 45 min | 60 s | 09-16 05:46 to 06:38 | 43 | 28 |
| 45 min | 60 s | 09-16 07:26 to 09:19 | 91 | 52 |
| 45 min | 60 s | 09-16 10:05 to 10:38 | 29 | 14 |
| 45 min | 60 s | 09-16 11:25 to 12:13 | 40 | 20 |
| 45 min | 60 s | 09-16 13:00 to 13:24 | 20 | 13 |
| 45 min | 60 s | 09-16 14:12 to 14:19 | 7 | 5 |

**What the pattern says.** The rest between stretches governs how long the next one lasts, more than the pace
does: the same 60 s pace ran for 5 h 40 min after a 45-minute rest and for 50 minutes after a 30-minute one.
Short rests give short stretches whatever the pace. The best combination found is a 45-minute rest with 60 s
between fetches.

## How it was run

- **Engine:** the sandbox copy `scratchpad\sbx2\p1-scrape` of the repo's `stages\p1-scrape` (commit `92a5e9d`),
  unchanged, with the Round 1 module `adapters/sg_sso.py` replaced by the package.
- **Country scraper:** `countries/sg-singapore/scraper/` (package `adapters/sg_sso/`, 2026-09-15 state) and
  Malaysia's package for the paced client and robots.txt rules.
- **Registry:** `countries/sg-singapore/sources.yaml` (block `sso:`) joined with `links/seed_laws.yaml`;
  fingerprint `e44e4da7…`, the same as the list's.
- **Politeness:** `REQUEST_DELAY_MS` 6000 at the start, then 15000, 30000 and finally 60000 as the challenge
  showed how little the portal would take. The host's own `Crawl-delay` is 6 s, so every pace here is at or
  slower than what it asks. One process, one request at a time, and one probe of `robots.txt` before each
  resume. **The challenge was never worked around**: when it appeared the engine stopped, and the run waited.
- **Output through a `subst` drive** (`subst R: <ws>`) from 15:52 UTC on 2026-09-15, so that two long titles
  could be stored (issue 2).
- **Commands** (from `<sandbox>`; `<ws>` the workshop, `<run>` this folder):

  ```
  PYTHONPATH=src python -m p1_scrape.adapters.sg_sso.catalogue \
      --registry <ws>/countries/sg-singapore/sources.yaml --seeds <ws>/countries/sg-singapore/links/seed_laws.yaml \
      --out <ws>/countries/sg-singapore/links
  mkdir -p <run>/logs && cp -r <ws>/countries/sg-singapore/links <run>/links_used
  REQUEST_DELAY_MS=6000 SSO_FRONTIER=links_file SSO_LINKS_FILE=<run>/links_used/documents.jsonl \
      python scrape.py --economy SG --scope all --out <run>
  # every resume after 15:52 UTC, through the subst drive, and after 05:17 UTC against the filtered list
  REQUEST_DELAY_MS=60000 SSO_FRONTIER=links_file \
      SSO_LINKS_FILE=<run>/links_used/documents_no_repealed.jsonl \
      python scrape.py --economy SG --scope all --out R:/outputs/SG/SG_ws_2026-09-15
  python scrape.py --validate R:/outputs/SG/SG_ws_2026-09-15/manifest.csv
  PYTHONPATH=src python tools/audit_run.py R:/outputs/SG/SG_ws_2026-09-15
  PYTHONPATH=src python -m p1_scrape.adapters.sg_sso.checker R:/outputs/SG/SG_ws_2026-09-15 --all
  PYTHONPATH=src python tools/merge_corpus.py --outputs R:/outputs/SG --out R:/outputs/SG/SG_corpus_2026-09-16 --hardlink
  ```

  The cycles were driven by `scratchpad/sg_resume_loop.sh`: rest, probe `robots.txt` once, resume the same run,
  let the engine stop itself, rest again. Its log is `scratchpad/runs/sg_crawl_watch.log`.

## What is in this folder

| Path | What it is |
| :---- | :---- |
| `RUN_NOTE.md` | This note |
| `manifest.csv`, `manifest.jsonl` | 739 rows, one per document, in the Hand-off #1 shape (contract 0.2.0) |
| `crawl_log.jsonl` | 1,031 entries in fetch order, across the 15 stretches: the challenged fetches are the rows with HTTP 202 |
| `raw/sg/<law>/` | 1,504 files: the 739 documents, their header sidecars, and 26 orphans (issue 5) |
| `links_used/documents.jsonl`, `documents.csv` | **The full list of 1,041 documents**, as built |
| `links_used/documents_no_repealed.jsonl` | The 743 rows the crawl read from 05:17 UTC on 2026-09-16, the full list without the 298 repealed acts (decision 19) |
| `links_used/laws.csv` | The census: 877 acts across the four listings, with status, version date, repeal date and last amending instrument |
| `links_used/catalogue_meta.json`, `discovery_log.jsonl`, `build.log` | The list's settings, fingerprint and the 540 requests that built it |
| `law_table.csv` | One row per law, what the portal says about it, and what a later stage should do with it (`use`) |
| `audit.md`, `audit.json` | The content check of every stored file |
| `cost_report.json`, `crawl_status.json` | The engine's counters **for the last stretch only** (7 requests); every earlier stretch overwrote the one before (issue 6) |
| `.idmap.json`, `inventory_sg.csv`, `inventory_sg.jsonl` | The engine's id map and its inventory of the frontier |
| `logs/crawl_stdout.log` | The console output of all 15 stretches, in order |

## What is stored

| Kind | Listed | Held | Note |
| :---- | ----: | ----: | :---- |
| Current acts | 525 | 524 | Each as the portal's PDF of the current version |
| Subsidiary legislation under the seed acts | 188 | 188 | The regulations, orders and notifications on the seed acts' subsidiary tabs |
| Acts Supplement (new and amending acts of 2025 and 2026) | 25 | 24 | Marked `linkage` in the law table: kept and linked, not read for indicators (decision 20) |
| Regulator documents | 5 | 5 | 2 from `pdpc.gov.sg`, 2 from `mas.gov.sg`, 1 from `isomer-user-content.by.gov.sg` |
| Repealed acts | 298 | 0 | **Dropped on purpose** (decision 19); their rows, status and repeal dates are in `law_table.csv` |
| Uncommenced acts | 10 | 0 | Recorded only: the portal's address for their text changes daily |

By method: 577 documents came through `requests`, 162 through the browser after `requests` was refused. Every
stored file is a PDF; one is a scan without a text layer.

Against Round 1's Singapore corpus of July 2026 (536 documents, in the frozen `handoff1_v2`): this run holds 739,
and the difference is mostly the subsidiary legislation and the Acts Supplement, which Round 1 did not collect.

## What is missing

### Documents not downloaded

| Law | What happened | Attempts |
| :---- | :---- | ----: |
| **Online Criminal Harms Act 2023** | The portal answers `/Act/OCHA2023?ViewType=Pdf` with **HTTP 200 and an HTML page**, not a PDF, every time. This is not the challenge: the challenge answers 202 with an empty body. Either the act has no PDF at that address or the code in the listing does not resolve to one. The act's own page was read when the list was built, so the code came from the portal | 3 |
| **Info-communications Media Development Authority (Amendment) Act 2026** | **No answer at all** (no HTTP status), both through `requests` and through the browser. Its address has the same shape as the 2026 Acts Supplement acts that stored without trouble | 2 |

Both are worth one more attempt on a quiet day; neither is a defect in the scraper.

### Not collected, by the settings

- **The 298 repealed acts** (decision 19). Their status and repeal date are kept.
- **The 10 uncommenced acts**, recorded only.
- **Subsidiary legislation beyond the seed acts.** The portal holds thousands; decision 12's rule limits us to the
  instruments under in-scope principal laws.
- **Older versions of any act.** One document per law, its current version.
- **The Acts Supplement before 2025** (`acts_supp_years: 2`).

### Missing details (metadata)

- **50 acts have no version date**, because the edge challenged their detail pages while the list was being built
  on 2026-09-15. Their rows carry `amendment_check_incomplete`, and the law table leaves `effective_date` empty
  rather than guessing.
- `in_force_status` is empty on the 5 regulator documents and on the 8 seed documents that have no list row.
- The manifest does not carry document kind, status, version date or language: those are in the link rows and
  join back on `source_url` (`countries/sg-singapore/NOTES.md` 4).

## Stored, but not what the row says

From `audit.md` (generic flags; no Singapore rule set yet):

| Flag | Rows | What they are |
| :---- | ----: | :---- |
| `duplicate_content` | 2 | One instrument stored twice under two titles (issue 1) |
| `gazette_print` | 22 | Amending acts as the Acts Supplement publishes them: the form, not a fault |
| `short_act_as_printed` | 5 | Short acts printed in full, title and arrangement of sections and all: the Pensions (Expatriate Officers) Act, the Reciprocal Enforcement of Commonwealth Judgments (Repeal) Act, the Supply Acts of 2025 and 2026, the Supplementary Supply Act |
| `orphan_file` | 26 | 13 documents' files left under `raw/` with no manifest row (issue 5) |

**No file is another act's text.** Every document carries its own title and its own number on page 1: the rules
check both, and the title test found all 739 documents carrying every distinctive word of their title but two,
which carry four of five. The rules were written and calibrated on this corpus on 2026-09-16 (`tools/README.md`).

## Issues encountered

1. **The same instrument is stored twice, and validation says so.** `sg-cr2018022a-001` and `sg-cr20185fdd-001`
   are byte-identical, both the Cybersecurity (Provider-Owned Critical Information Infrastructure) Regulations
   2018. The seed file (`links/seed_laws.yaml` line 47) names it by its **old title**, "Cybersecurity (Critical
   Information Infrastructure) Regulations 2018", so the seed and the subsidiary tab produced two rows with
   different names and slightly different addresses, and the engine's name-keyed id map minted two ids.
   **Effect:** `scrape.py --validate` reports 1 error on the run. The corpus resolves it: `merge_corpus.py`
   matches the two by content hash and keeps one, so `SG_corpus_2026-09-16` validates clean.
   **Still to do:** correct the title in `seed_laws.yaml`. That changes the registry fingerprint and so invalidates
   the current list, which is why it waits for the next list build (decision 17: flag, do not fix mid-run).
2. **Two titles are too long for Windows.** The engine names each document's folder after the whole law name; for
   two subsidiary titles of 148 and 154 characters the sidecar path exceeds 260 characters under
   `<ws>\outputs\SG\…`. Two stores failed on 2026-09-15 before the run moved onto a `subst` drive at 15:52 UTC,
   and both documents were fetched again afterwards. **A reader must use the short path too:** run through `R:`
   or the audit reports a readable file as `unreadable_file` and validation reports a path that does not resolve.
   The engine should cap the folder name (`countries/sg-singapore/NOTES.md` 2.5).
3. **Two documents are still missing**, described above.
4. **Eight documents were fetched at a seed's own address**, which the list does not carry as a row: the seeds'
   consolidations and a few of their subsidiary instruments. They are real documents and distinct laws, not
   duplicates, but they have no link row, so their kind, status and language are unknown to the audit and the law
   table. The list should carry the seed's address as its row.
5. **A watcher killed a healthy crawl at 15:39 UTC on 2026-09-15**, having counted the challenged fetches of the
   previous stretch at the tail of the log. The engine had stored 9 documents since its last checkpoint and those
   rows were lost; their files are the 26 orphans under `raw/`. The loop was corrected at 15:47 UTC to let the
   engine stop itself, which it does after ten challenged answers, writing its manifest first. **The engine should
   checkpoint on every stored document**, not every tenth.
6. **`crawl_status.json` and `cost_report.json` describe the last stretch only** (7 requests, 5 documents). Each
   resume overwrote the previous counters. The run's real figures are in `crawl_log.jsonl` and in the `[health]`
   lines of `logs/crawl_stdout.log`.
7. **The portal's edge challenges a plain client after sustained access.** HTTP 202, an empty body, and
   `x-amzn-waf-action: challenge`, which a plain client cannot pass and which headless Chromium does not pass
   either, so each challenged fetch costs two requests. 220 of the 1,031 fetches were answered this way.
   `countries/sg-singapore/NOTES.md` 1.3 records what was learnt about it.

## Changes after the run

- **2026-09-16 05:17 UTC:** the crawl switched to `links_used/documents_no_repealed.jsonl` (743 of the 1,041 rows)
  on the developer's decision to drop the repealed acts (decision 19). The full list stays beside it.
- **2026-09-16 13:00 and 14:12 UTC:** two extra stretches for the rows the challenge had blocked at the end of the
  list; 18 of the 20 arrived.
- **2026-09-16 14:21 UTC:** validated, audited and the law table written, all through `R:`.
- **2026-09-16 14:22 UTC:** `outputs/SG/SG_corpus_2026-09-16` built from this run alone: 738 documents, one older
  copy superseded (issue 1), validation clean.

## Decisions still open that affect this run

- **A browser transport for Singapore.** Every figure above is shaped by the challenge. A browser session that
  carries the portal's token would turn 24 hours into about 90 minutes. It is the structural fix and it is the
  developer's call (`countries/sg-singapore/NOTES.md` 5).
- **The two missing documents**, and whether to chase them.
- **A Singapore rule set for the audit** (`RULES["SG"]` in `tools/audit_run.py`).
- **The update check**, which is a stub: its listing reads are what triggered the challenge in the first place.
- **Long paths**: cap the storage folder name in the engine, enable Windows long paths, or keep reading through a
  `subst` drive.
