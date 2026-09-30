# Run note: MY_ws_2026-09-14

Malaysia, web scraping, 14 September 2026. A crawl of the Laws of Malaysia portal (`lom.agc.gov.my`):
- the current file of every principal act the portal lists with a document;
- the amending acts in the portal's amendment listing;
- 17 commencement orders and 39 P.U. (A) instruments;
- 14 agency documents from the hand-picked seed list.

"What is missing" lists the gaps.

## Read this first

- **Not every stored file is the text of the law it is filed under.**
  - About 80 repealed acts are stored as a repeal notice of 1 to 4 pages.
  - 6 files are another act's text or a notice.
  - 6 Malay files are recorded as English.
  - The 4 "Amendment of …" rows are not amending acts.

  See "Stored, but not what the row says".
- **Take law details from `links_rebuilt/`,** the list rebuilt with the fixed scraper, not from `links_used/`
  (issue 1).
- **4 documents failed** and were retried on 2026-09-15 by the update check (`MY_ws_2026-09-14_to_2026-09-15`) and failed again with HTTP 500.

## At a glance

| | |
| :---- | :---- |
| Country | Malaysia (`MY`) |
| Run type | Full crawl, scope `all`: every document in the link list |
| Date | 2026-09-14 |
| Time, UTC | 06:49 to 08:56 for the three steps. The crawl itself ran 07:05:34 to 08:39:43 (5,649 s) |
| Time, machine clock | US Eastern Daylight Time, UTC−4: crawl 03:05 to 04:39 |
| Result | 1,320 documents listed: **1,311 stored**, **4 failed**, 5 duplicates not stored |
| Size | 624,201,565 bytes of documents (624 MB; Windows shows 595 MB), 40,041 pages |
| Validation | `scrape.py --validate manifest.csv`: 1,311 rows, 0 errors, 0 warnings, contract 0.2.0 (run again after the move, 2026-09-14) |
| Checked | The note's figures were checked against the files by independent reviewers in two passes on 2026-09-14, and the corrections they found were applied |

## Steps and times

The steps ran one after another, and no two processes read the portal at the same time.

| Step | UTC | Requests | Output |
| :---- | :---- | :---- | :---- |
| 1. Build the link list | 06:49:01 to 07:04:25 | 226 to lom: robots.txt, 5 listing requests, and 110 detail pages at two hops each. No documents | `links_used/`, 1,320 documents |
| 2. Crawl the list | 07:05:34 to 08:39:43 | 1,320 document fetches (1,306 lom, 14 agency sites), plus a second, Playwright request for each of the 4 failures. The 2 pdp.gov.my pages were loaded in a headless browser, which also loads their page assets | `raw/`, `manifest.*`, `crawl_log.jsonl` |
| 3. Rebuild the list with the fixed scraper | 08:40:34 to 08:55:58 | 226 to lom, the same kinds as step 1. No documents | `links_rebuilt/`, 1,315 documents |

## How it was run

- **Engine:** the Round 1 crawl engine, in a sandbox copy in the session scratchpad
  (`scratchpad\sbx2\p1-scrape`).
  - The engine code is identical to the repo's `stages\p1-scrape`, and the repo was not changed.
  - In the sandbox, the Round 1 adapter `src/p1_scrape/adapters/my_gazette.py` was replaced by a copy of
    `countries/my-malaysia/scraper/`.
  - The sandbox's `contracts/instrument/sources_my.yaml` and `instrument/sources_my.yaml` were replaced by
    `sources.yaml` and `links/seed_laws.yaml` joined, at 06:47 UTC. The crawl read its registry from there.
  - Both were reinstalled from the fixed working copy at 08:40 UTC, before step 3.
- **Malaysia scraper:** steps 1 and 2 used the package as it was before the code review fixes. The file hashes
  are in `links_used/catalogue_meta.json`, `scraper_sha256`. Step 3 used the fixed package.
- **Registry: the two list builds read different versions of both files.** The hashes are `registry_sha256` in each
  `catalogue_meta.json`. Each build takes them when it writes its files (07:04 and 08:56 UTC), not when it reads the
  registry at its start.

  | Build | `sources.yaml` | `seed_laws.yaml` |
  | :---- | :---- | :---- |
  | Step 1 | `1097a43e…` | `dad111e9…` |
  | Step 3 | `63f18492…` | `7212198b…` |

  The files were edited:
  - `sources.yaml` at 06:51 UTC, while step 1 was running: one comment. Step 1 had already read the file, so its
    recorded hash is of the file one comment newer than the one it read.
  - `seed_laws.yaml` at 07:40 UTC: full P.U. numbers for the five Cyber Security seeds, and a comment.
  - Both files at 08:18 UTC: comments only.
  - `seed_laws.yaml` twice more after the run (08:57 and 13:08 UTC), and `sources.yaml` once more (a comment on
    the scope counts), all comments. Today's files match neither build's hashes. The settings fingerprint
    (`cfg_sha256`) ignores comments and still matches the list in `links/`.
- **Politeness:** `REQUEST_DELAY_MS` at its default of 3000, plus up to 1.5 s random jitter, one request at a time.
  Issues 3 and 4 give what that did and did not cover.
- **robots.txt:**
  - Both list builds read lom's robots.txt first (06:49:01 and 08:40:34 UTC, HTTP 500).
  - The crawl's own read of lom's robots.txt is not logged.
  - No robots.txt was read for the four agency hosts (issue 5).
- **Commands.** `<sandbox>` is `scratchpad\sbx2\p1-scrape`, `<workspace>` is
  `C:\Users\woshi\Desktop\rdtii-finale-1-scraping`, and `<run>` is this folder. All commands were run from `<sandbox>`.

  ```
  # 1. Build the link list (written straight into the workspace)
  PYTHONPATH=src python -m p1_scrape.adapters.my_gazette.catalogue \
      --registry <workspace>/countries/my-malaysia/sources.yaml \
      --seeds <workspace>/countries/my-malaysia/links/seed_laws.yaml \
      --out <workspace>/countries/my-malaysia/links
  # then copied beside the crawl output (now links_used/)

  # 2. Crawl the list
  LOM_FRONTIER=links_file LOM_LINKS_FILE=<run>/links_used/documents.jsonl \
      python scrape.py --economy MY --scope all --out <run>

  # 3. Rebuild the list: the same --registry and --seeds as step 1, --out <scratchpad>/runs/links_rebuild_2026-09-14
  #    (now links_rebuilt/)
  ```

  On the day, `<run>` was `C:\Users\woshi\Desktop\RDTII\pipeline-data\rdtii-p1-scrape\my_finale`, and the list was in
  its `links_2026-09-14\` subfolder. See "Changes after the run". Re-running these commands in a fresh copy of
  the repo does not reproduce the run, because of the sandbox changes above.

## What is in this folder

| Path | What it is |
| :---- | :---- |
| `RUN_NOTE.md` | This note |
| `manifest.csv`, `manifest.jsonl` | One row per stored document, Hand-off #1 format (contract 0.2.0). The 19 multi-line `commencement_date` values and 1 multi-line `in_force_status` are kept as quoted cells in the CSV |
| `crawl_log.jsonl` | One line per document outcome, 1,325 lines. Each duplicate has an `ok` and a `duplicate` line. Each failure keeps only its last attempt |
| `raw/my/<law>/` | The documents, each with a `.headers.json` file of HTTP headers |
| `cost_report.json` | Engine counters. `total_bytes` 625,503,823 counts one response body per document: the 624,201,565 stored, the 5 duplicate downloads and the last attempt at each of the 4 failures. It leaves out the first request at each failure, the pdp.gov.my page assets and the list builds. `retrieval_method_mix` counts successful fetches only |
| `crawl_status.json` | The engine's final status. `recent_outcomes` covers only the last 40 documents, so it does not show the 4 failures |
| `.idmap.json` | The engine's document-ID map. The engine needs it to resume this run |
| `links_used/` | The link list the crawl read, built 07:04 UTC. It holds `documents.csv` and `.jsonl` (one row per document), `laws.csv` (one row per listed law), `catalogue_meta.json` and `discovery_log.jsonl` (the build's 226 requests) |
| `links_rebuilt/` | The same list rebuilt at 08:56 UTC with the fixed scraper. When this note was written it was identical to `countries/my-malaysia/links/` |
| `logs/crawl_stdout.log` | The crawl's console output: 1,311 `OK` lines and 4 `XX` lines. It prints nothing for the 5 duplicates |
| `logs/crawl_summary.json` | The session's post-crawl check, not engine output: the crawl against its list and against Round 1 |
| `logs/links_used_build.log`, `logs/links_rebuilt_build.log` | The console output of steps 1 and 3 |

**Getting a document's full details.**
- **What the manifest lacks:** document kind, language and version date. Legal status is there only as the
  portal's raw text in `in_force_status`, on 108 rows.
- **How to join:** match the manifest's `source_url` to `url` in `links_rebuilt/documents.jsonl`. That matches 1,306
  of the 1,311 rows.
- **The other 5** are the Cyber Security Act 2024 instruments, stored under their `www.nacsa.gov.my` addresses.
  - Join them on `law_name_guess` to the lom rows in `links_rebuilt/documents.jsonl`, which carry the P.U.
    numbers: Licensing of Cyber Security Service Provider Regulations P.U. (A) 221/2024; Notification of Cyber
    Security Incident Regulations 220/2024; Period for Cyber Security Risk Assessment and Audit Regulations
    219/2024; Compounding of Offences Regulations 222/2024; Exemption Order 47/2025.
  - `links_used/` has no details for these five (kind and language empty, law number "P.U.(A) 2024" or "P.U.(A) 2025").

## What is stored

| Kind | By `links_rebuilt/` (use this) | By `links_used/` (what the crawl read) |
| :---- | ----: | ----: |
| Principal acts: the file the portal lists for each act | 821 | 820 |
| Amending acts | 420 | 421 |
| Commencement orders, P.U. (B) | 17 | 17 |
| Subsidiary legislation, P.U. (A) | 44 (39 from lom, 5 from nacsa) | 39 |
| Agency documents from the seed list | 9 | 14 |
| **Total** | **1,311** | **1,311** |

The two lists differ on Act 125, Companies Act 1965 (principal in the rebuilt list), and on the five Cyber Security
instruments.

- **Formats:** 1,278 native PDF, 31 scanned PDF, 2 HTML.
- **Sources:**
  - `lom.agc.gov.my` 1,297;
  - `www.pdp.gov.my` 7;
  - `www.nacsa.gov.my` 5;
  - `www.sc.com.my` 1;
  - `www.bnm.gov.my` 1.
- **Legal status of stored acts** (rebuilt list):
  - 90 principal acts repealed;
  - 6 principal and 12 amending acts not yet in force;
  - 1 amending act partly in force (A1530);
  - 725 principal acts with no status marker on the portal (`unknown`).
- **Language** as recorded in the link list:
  - 1,235 English;
  - 2 Malay (Acts 565 and 519, which have no English text);
  - 74 not recorded (subsidiary instruments, commencement orders, agency documents, 4 amending rows).
  - 6 of the "English" files are Malay (item 17 below), and Act 310's is partly Malay (item 15). The 28 "English"
    files with no text layer were not checked.
- **Scopes:** 28 stored documents are in scope `seed` and 184 in scope `relevant`.
- **Against Round 1** (`handoff1_v2`, 869 Malaysian rows), principal acts compared by act number, using
  `links_used`:
  - 568 byte-identical;
  - 247 a different file;
  - 5 not in Round 1.

  Of the 247, judged by the "As at" date on the cover (a heuristic check of the cover text):
  - at least 113 are a newer consolidation. The data protection act, PDPA, is now the text as at 1 July 2023;
    Round 1 has 15 June 2016.
  - about 50 are the same edition in a new file;
  - 14 are now only a repeal or cessation notice where Round 1 held a longer text;
  - at least 2 are older than Round 1's file: Act 166 as at 1 November 2012 against 1 August 2018, and Act 554, a
    2006 reprint against 1 December 2011;
  - the rest could not be dated from the cover.

## What is missing

### Documents not downloaded

1. **4 documents failed.**
   - The engine made two attempts on each, back to back: a plain request, then its one fallback, a Playwright
     request.
   - lom answered HTTP 500. Only the second attempt is logged.
   - They were retried on 2026-09-15 by the update check (`MY_ws_2026-09-14_to_2026-09-15`) and failed again with HTTP 500.

   | Law | Kind | Scope | File, after `https://lom.agc.gov.my/ilims/upload/portal/akta/` |
   | :---- | :---- | :---- | :---- |
   | Trade Marks Act 1976 (Act 175) | principal act | `all` | `outputaktap/Act%20175%20original.pdf` |
   | Passports Act 1966 (Act 150) | principal act | `all` | `LOM/EN/Act%20150%20Reprint%202006.pdf` |
   | Supply Act 2025 (Act A1740) | amending act | `all` | `outputaktap/2592587_BI/Act%20A1740%20-%20SUPPLY%20ACT%202025.pdf` |
   | Supply Act 2021 (Act A1626) | amending act | `all` | `outputaktap/20201231_A1626_BI_WJW015xxx%20BI.PDF` |

   Round 1 holds a file for Acts 175 and 150.
2. **45 acts on the portal offer no document at all.**
   - Legal status: 43 repealed, 1 partly in force (Act 508, Sewerage Services Act 1993), and 1 with no status
     marker (Act 135, Partnership Act 1961).
   - Each has `not_crawled_reason` "the portal offers no document" in `laws.csv`.
   - Round 1 holds a file for 21 of them: Acts 13, 20, 135, 143, 247, 278, 335, 353, 356, 361, 372, 390, 409, 419,
     449, 480, 509, 528, 553, 642 and 663. For Acts 480, 553 and 642 that file is only a one- or two-page repeal
     notice.
3. **The Witness Protection Act 2009 (Act 696).** Its row holds the text of another act (item 15), so this run has
   no text of it. Round 1 holds it.
4. **Act 811** (Suruhanjaya Pengangkutan Awam Darat (Dissolution) Act 2018) has no row and no text.
   - The portal lists one file for Act 811 and Act 714: a one-page notice that Act 811 repealed Act 714.
   - It is stored once, under Act 714.
   - Round 1's Act 714 row holds the 2015 text of Act 714.
5. **5 duplicates, not stored twice.** Nothing is missing because of them.
   - The engine found each lom copy of the five Cyber Security Act 2024 instruments already stored, by SHA-256
     (logged "sha already stored").
   - Their nacsa.gov.my copies, paired by name, were stored 4 to 35 seconds earlier.
   - The engine does not log which stored file each one matched; the pairing is by name.

### Not collected, by the settings in `sources.yaml`

6. **Subsidiary legislation outside the core pillar 6 and 7 acts** (`lom.subsidiary_acts: core`, decision 12, still
   proposed).
   - **Counted, not fetched:** 1,138 numbered instruments with a file, on the timelines of 45 other acts. Those
     are the 45 of the 66 non-core timelines read that list any.
     - The largest numbers are on Act 235 (409), Act 53 (172: 168 P.U. (A), 4 P.U. (B)), Act 301 (74) and Act 378
       (65).
     - The count includes P.U. (B) notices and is distinct within each act, not across acts.
     - Under `subsidiary_series: P.U. (A)`, only the P.U. (A) share would be fetched.
   - **Neither counted nor fetched:**
     - P.U. (B) notices on the 21 core acts' timelines. The PDPA's timeline lists three. The exception is the
       commencement orders an amending act cites, which are fetched (17 stored).
     - Instruments on acts whose timeline was not read.
7. **Older versions.** Each act has one file, the latest-dated English text the portal lists (Malay only for Acts 565
   and 519).
   - That file is not always current: 79 stored principal acts have an amending act dated after it (crawl flag
     `stale_vs_portal`). The PDPA's 2023 reprint, for example, predates A1727.
   - The amending acts are stored beside them.
8. **Amending acts before A1392.** The amendment listing starts at A1392 (published 2 June 2011).
   - Stored amending acts: 400 from that listing, 4 found only on timelines (item 16), and 16 acts from the
     principal listing that a timeline lists as amendments (decision 13).
   - Older amending acts are not fetched.
9. **Malay texts where an English text exists** (decision 14). For 76 stored documents a newer Malay version exists
   and was not fetched (review flag `newer_version_in_other_language`).
10. **Documents on agency sites** other than the 14 seeds were not searched for.

### Missing details (metadata)

11. **Dates.**
    - Of the 821 stored principal acts, publication and assent dates are empty for 741 and the commencement date for
      744.
    - 736 of these acts had no timeline read (`lom.timeline: rule`).
    - Acts 796, 843 and 855 had a read timeline with no original entry.
    - Acts 53 and 197 had a read timeline but no publication or assent date on it.
    - Acts 350, 564, 643, 674 and 701 had a read timeline but no commencement date.
    - Publication dates are also empty on 18 amending rows: the 4 "Amendment of …" rows, and 14 Finance Acts
      recorded as amending acts (Acts 719, 755, 761, 764, 773, 785, 801, 823, 831, 833, 845, 851, 862 and 874).
    - The build's note gives 798; that counts every listed principal act without a read timeline, stored or not.
12. **Amendment check incomplete** (review flag `amendment_check_incomplete`): 297 stored documents, 296 principal acts
    and Finance Act 2011.
    - None had its timeline read.
    - 209 are as at a date before 2 June 2011, where the amendment listing starts, and 88 have no as-at date.
    - Amendments before 2 June 2011 (and after the as-at date, where there is one) are not checked.
    - The build's note gives 342, counted over the whole principal listing.
13. **Commencement orders not looked up for A1539 (P.U. (B) 547/2017) and A1586 (P.U. (B) 62/2019).**
    - Their detail pages answered HTTP 200 without a readable timeline.
    - A1759, A1730 and A1756 also had no readable timeline, but they cite a date only, so no order was sought.
14. **Other gaps in the details.**
    - **Unlinked amending acts:** 62 stored amending acts are not linked to the act they amend (`principal_unlinked`).
      - 35 are Supply, Supplementary Supply and Supply (Reallocation) Acts.
      - 16 amend a law outside the principal listing: 6 Constitution (Amendment) Acts, 4 Sabah and Sarawak
        ordinance amendments, 3 Merchant Shipping Ordinance amendments, and 3 others.
      - 11 amend listed acts whose title the matcher did not match, for example Road Transport, Industrial
        Relations, Dangerous Drugs, Hire-Purchase and Bankruptcy.
    - **Legal status:** `unknown` for 725 stored principal acts: the portal printed no status marker for them.
      - `in_force_status` is empty on 1,203 of 1,311 rows.
      - On Acts 491 and 496 it names a portal id ("Repealed by Act 1712817" and "1712818") instead of the repealing
        act.
    - **Versions:** `text_version` is null for 461 stored principal acts, and `version_as_at` is missing for 88.
    - **Indicator hints** are set on 20 rows only: the 14 agency documents and 6 seed acts.
    - **Law numbers:** `law_number_guess` is empty on 9 rows: 5 agency documents and the 4 "Amendment of …" rows.

## Stored, but not what the row says

15. **6 files are not the text of the act they are stored under.** The portal links these files. Page 1 of each was
    read on 2026-09-14.
    - Act 696, Witness Protection Act 2009: the file (`Act 695 (Reprint 2019).pdf`) is the Judicial Appointments
      Commission Act 2009, which is also stored under Act 695.
    - Act 90, Juvenile Courts Act 1947: the file is the Child Act 2001 (Act 611) as at 1 February 2018, the act that
      repealed it.
    - Act 320, Convention on the Recognition and Enforcement of Foreign Arbitral Awards Act 1985: the file is the
      Arbitration Act 2005 (Act 646).
    - Act 310, Share (Land Based Company) Transfer Tax Act 1984: the file is 3 pages of the Finance Act 1988 (Act 364),
      the repealing act. Page 1 is a Malay text page whose long title repeals Act 310; pages 2 and 3 are the English
      cover and assent-date page.
    - Act 324, Commodities Trading Act 1985: the file is `Act A987.pdf`, a 26-page scan with no text layer. Its
      page 1, read from the page image, is the cover of Act A987, the Futures Industry (Amendment and Consolidation)
      Act 1997, the act that repealed it.
    - Act 756, Traditional and Complementary Medicine Act 2013: the file is a 2-page gazette notice, P.W. 5450 of
      10 March 2016.
16. **The 4 "Amendment of …" rows are not amending acts.** They carry kind `amending_act`, scope `relevant` and no
    law number.
    - `my-acma2015-001` (Communications and Multimedia Act 1998, 5 November 2015) is a 51-page Gazette supplement
      of P.U. (B) notices. Its only content on that act is a corrigendum.
    - `my-aqsa2016-001` (Quantity Surveyors Act 1967, 7 June 2016) is a 4-page Gazette supplement: corrigenda to the
      Optical Act 1991 (P.U. (B) 272) and the Quantity Surveyors Act 1967 (P.U. (B) 273), and a Customs Act notice of
      crude oil values (P.U. (B) 274) that fills the rest.
    - `my-asca2016-001` and `my-asca2017-001` (Securities Commission Malaysia Act 1993) are the orders P.U. (A)
      112/2016 and P.U. (A) 357/2017, which amend its Schedules 1 and 2.
17. **6 Malay files are recorded as English.** The portal's English link points to a Malay file.
    - Full Malay texts: Act 680, Electronic Government Activities Act 2007 (scope `relevant`); Act 104, Lembaga
      Kemajuan Terengganu Tengah Act 1973; Act 337, Finance Act 1987; Act 348, Diplomatic and Consular Officers
      (Oaths and Fees) Act 1959.
    - Malay repeal notices: Acts 556 and 575.
    - Round 1 holds English texts of Acts 104, 337 and 680.
18. **About 80 repealed acts are stored as a notice, not a text.**
    - Of the 90 stored repealed principal acts, 83 files have 4 pages or fewer. At least 60 of them say on page 1
      that the act is repealed or superseded.
    - 4 hold the last text before repeal: Acts 10, 121, 384 and 651.
    - Act 437 has no status marker, but its file is a 1-page "Superseded by Act 865" notice.
    - For 14 of these acts Round 1 holds a full text: Acts 23, 40, 48, 79, 102, 192, 210, 215, 219, 223, 252, 437,
      691 and 714.
19. **31 PDFs classed as scanned** (little or no text layer) need OCR: 16 principal acts, 14 amending acts and the
    Personal Data Protection Regulations 2013 (by the rebuilt list). They are the rows with `source_type`
    `pdf_scanned`.
20. **2 HTML pages instead of the code text.** The Personal Data Protection Code of Practice for the Banking and
    Financial Sector (2017) and the one for the Communications Sector (2017) were stored as their pdp.gov.my
    landing pages. The codes themselves were not downloaded.

## Issues encountered

1. **The crawl read the link list built before the code review fixes.**
   - **Manifest columns** copied from that list differ from what the fixed scraper writes:
     - `seed_query` holds rule group ids such as `S2_tax_records` instead of search words (87 rows);
     - `commencement_date` runs over several lines on 19 rows, and `in_force_status` on 1 (A1530);
     - the 4 "Amendment of …" rows carry long names, for example "Amendment of QUANTITY SURVEYORS ACT 1967
       (07 Jun 2016)" where the fixed scraper writes "Amendment of Act 487 (07 Jun 2016)". Their `doc_id`s and
       `raw/` folder names come from those names.
   - **The list's details** also differ:
     - Act 125 (Companies Act 1965) is an amending act linked to Act 197;
     - the five Cyber Security instruments are listed twice, which caused the 5 duplicates;
     - the last amending instrument differs on 7 acts (Act 53: A1706, where the fixed scraper finds Act 875);
     - `linked_amendments` differs on 10 acts;
     - in `laws.csv`, 347 amendment rows hold the commencement remark in `status_marker`, where the rebuilt list has
       a `commencement_remark` column;
     - there is no registry fingerprint (`cfg_sha256`), though `registry_sha256` is recorded.
   - **What was done:** the list was rebuilt after the crawl (step 3). The rebuild listed the five Cyber Security
     instruments once because of the fixed code and the full P.U. numbers added to their seeds at 07:40 UTC. The
     rebuilt list has no address the crawl did not have, so no document is missing because of this.
2. **lom's robots.txt answered HTTP 500** at 06:49 and 08:40 UTC. The portal is crawled anyway under decision 9
   (`lom.robots_5xx: allow`).
3. **No wait after a download.**
   - **How the engine paces:** its limiter is per host. It spaces the start of each document's first request to a
     host at least 3 s apart, plus jitter. It does not wait after a download ends, and does not space fallback
     requests (issue 4).
   - **What the log shows:** `crawl_log.jsonl` is stamped to the second as each download ends. Of the 1,305 gaps
     between consecutive lom downloads, 201 show a difference under 3 s: 157 at 2 s, 41 at 1 s, 3 at 0 s.
   - **Why 201 is a minimum:** stamps are cut to the second, so some of the 321 gaps at 3 s may also be under 3 s.
   - **What cannot be shown:** the engine keeps no per-request log, so the spacing of request starts cannot be shown
     (`POLICY.md` 5.5, `evidence/README.md` artefact 4).
4. **Failed downloads got an immediate second request.** For each of the 4 HTTP 500 files the engine sent a plain
   request and then, with no wait, a Playwright request. That fallback is not paced (`POLICY.md` 5.5).
5. **Agency sites: no robots.txt, and unlogged page assets.**
   - The engine never reads robots.txt (`POLICY.md` 5.5). The 14 requests to `www.pdp.gov.my` (7),
     `www.nacsa.gov.my` (5), `www.sc.com.my` (1) and `www.bnm.gov.my` (1) went out without a robots.txt check.
   - The two PDP Code of Practice pages were loaded in headless Chromium, which also fetched their scripts, styles
     and images, unlogged and unpaced.
6. **Engine gaps seen in this run.** These are in the Round 1 engine and not fixed here.
   - The manifest drops the scraper's details (`contract_meta`), so they have to be joined back.
   - Each list build's 226 requests are only in its `discovery_log.jsonl`, not in `crawl_log.jsonl` or
     `cost_report.json`.
   - `cost_report.json` counts 1,320 requests, one per document, without the fallback requests.
7. **lom's clock runs about 6 minutes fast.**
   - The `Date` header on every stored lom response is 350 to 383 s later than the crawl's `access_date`.
   - `www.nacsa.gov.my`, `www.sc.com.my` and `www.bnm.gov.my` agree within 2 s.
   - `www.pdp.gov.my`'s `Date` is 15 to 109 s earlier, and not only because of download time: the PDP Regulations
     2013 shows 15 s although its fetch took under 2 s.
   - Time events by `access_date` and `crawl_log.jsonl`, not by the stored `Date` headers.
8. **Five amendment detail pages gave no readable timeline** (A1759, A1539, A1730, A1756, A1586). They answered
   HTTP 200 in both list builds, and the pages were not saved. This is the cause of item 13.
9. **A harmless warning.** Each list build printed a `RuntimeWarning` from Python's `runpy` about the `catalogue`
   module. It has no effect.

## Changes after the run

- **2026-09-14, moved here** from `C:\Users\woshi\Desktop\RDTII\pipeline-data\rdtii-p1-scrape\my_finale`, on the
  developer's instruction. The frozen corpus `handoff1_v2` was not touched.
  - **How:** a plain move was refused ("Permission denied"), so the folder was copied. Every one of the 2,635 files
    was checked against the original's SHA-256, every manifest row against its file's hash and size, and the
    manifest validated again. Then the original was deleted.
  - **No path inside the output changed:** the manifest stores paths relative to this folder.
- **2026-09-14, the folder was tidied.**
  - `links_2026-09-14/` renamed to `links_used/`.
  - The console log and the summary moved into `logs/` without their dates.
  - The rebuilt list and both build logs were copied in from the session scratchpad.
  - The first line of `logs/crawl_stdout.log` still names the old folder.
- **2026-09-14, this note was checked** against the files by four independent reviewers and a completeness critic,
  and corrected. A second pass of two reviewers checked the corrected text, and its corrections were applied too.
- **2026-09-14, moved into the country folder** `outputs\MY\`, on the developer's instruction (a rename inside
  the workspace). The manifest was validated again, the 1,311 stored documents were checked against their
  manifest SHA-256, and the folder's 2,643 files were counted.
- **Path length.** The longest file path here is 249 characters, and Windows allows 259 unless long paths are
  enabled (they are not on this machine). Copying this folder under a base path more than 10 characters longer
  breaks some files.
- 2026-09-15: `audit.md` and `audit.json` added by `tools/audit_run.py` (decision 17): 1,311 documents read (first two pages), 132 rows flagged, 116 of them a wrong or unreadable file: 76 repeal notices, 29 scans with no text layer, 7 Malay files behind English links, 5 other acts' texts, 2 landing pages, 1 gazette notice, 1 bundled supplement; plus 7 gazette prints and 4 P.U. orders listed as amendments, informational. The files stay as served; the flags travel into `MY_corpus_2026-09-15`, where this run supplies 1,310 of 1,316 documents (the Service Tax Act 2018 was superseded by the 2026-09-15 delta run).

## Decisions still open that affect this run

**Settled on 2026-09-15 by decision 17** (the list below is kept as written on 2026-09-14): regulations under the
core acts stay (decision 12 confirmed); Supply Acts and Finance Acts stay as the portal lists them; `lom.timeline:
all` is the convention and the list was rebuilt with it on 2026-09-15 (1,414 documents); the Round 1 corpus is hands off and
`MY_corpus_2026-09-15` replaces it; wrong files are flagged by `tools/audit_run.py` and left as served. The audit's
counts (76 repeal notices, 5 other acts' texts, 7 Malay files behind English links, 1 gazette notice) supersede the
"about 80 / 6 / 6" counted by hand in items 15 to 18.

- **Decision 12,** fetching regulations under the core acts, is proposed, not confirmed. Widening it changes item 6.
- **Supply Acts:** keep them as amending acts, drop them, or treat them as principal acts (item 14; two of them
  failed, item 1).
- **Finance Acts with savings provisions:** amending or principal acts.
- **`lom.timeline: all`:** it would fill most of items 11 and 12. It needs at least 1,596 more paced requests (two
  for each of the other 798 listed principal acts, about 1.8 hours), plus the timelines of their later amending
  acts.
- **The Round 1 corpus:** whether this run replaces `handoff1_v2` for Malaysia. Items 1, 2, 3, 17 and 18 name
  files Round 1 has and this run lacks. P2 and P3 still read `handoff1_v2`.
- **Wrong or partial files (items 15 to 18):** whether to take them from Round 1, flag them for extraction, or
  report them to the portal.

More detail: `countries/my-malaysia/NOTES.md` (what the website looks like and how the scraper works), and
`DECISIONS.md` decisions 9 to 15.
