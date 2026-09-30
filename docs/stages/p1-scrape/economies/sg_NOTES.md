# Singapore: the website and our scraper

The general note for Singapore, in the layout `CONVENTIONS.md` section 4 fixes for every country. It holds the
findings of the Round 1 amendment audit of 2026-09-13 (every count re-checked independently the same day, the key
portal facts re-fetched live) and, since 2026-09-15, the catalogue step built that day (decision 18). Counts are
over the frozen Round 1 corpus, `pipeline-data\rdtii-p1-scrape\handoff1_v2`, unless a line says "live" or names a
build.

**Where Singapore stands (2026-09-15):** the scraper is a package with the convention's catalogue step, run live
once (11:50 to 12:58 UTC: 1,041 documents listed, in `links/`). From 13:00 UTC the portal's edge answered every
request from our plain client with a WAF challenge (section 1.3); it lifted after an hour's silence, and the first
crawl from the list started at 14:09 UTC into `outputs/SG/SG_ws_2026-09-15/` (section 3), watched for the
challenge's return. The rebuild with the review fixes waits for a quieter day. No audit rule set, no update check
(a stub), no corpus yet. `scraper/WORKFLOW.md` and `updates/WORKFLOW.md` say what runs today.

## 1. The website

### 1.1 The sites we use

| Portal | Host | robots.txt, read live 2026-09-13 and 2026-09-15 | Delay to use |
| :---- | :---- | :---- | :---- |
| Singapore Statutes Online (AGC) | `sso.agc.gov.sg` | `Crawl-delay: 6`, `Disallow: /search` (48 bytes) | **6 s.** In Round 1's crawl, 389 of 523 gaps were under 6 s (median 5 s) |
| PDPC, CSA, IMDA | the regulators named in `sources.yaml` | not read | Seed sources for guidance and codes; the default 3 s until each host's robots.txt is read |
| MAS and the other seed hosts | named only in `links/seed_laws.yaml` | not read | The same |

`sources.yaml` names SSO as the primary statute portal and three regulators; its `sso:` block holds the catalogue's
settings. Never request `/search`.

### 1.2 What Singapore Statutes Online looks like

**Listings**, all server-rendered, plain GET, `PageSize=500` on 2026-09-15 (the default page shows 20 rows); read 100 rows a page from 2026-09-16,
because the 500-row page was refused (1.3). The paths below are the first page; later pages are `/All/1`, `/All/2`. The table's header
row has no closing tag, so a parser splits on `<tr` openings.

| Listing | Address | What it gives | Count (live, 2026-09-15) |
| :---- | :---- | :---- | ----: |
| Current acts | `/Browse/Act/Current/All?PageSize=500&SortBy=Title&SortOrder=ASC` and `DESC` | title, act code (`/Act/PDPA2012`), the PDF link (`?ViewType=Pdf`); no number or date column | 525, in two pages of 500 |
| Repealed acts | `/Browse/Act/Repealed/All?PageSize=500` | title, the repeal date in the link (`/Act/AA1987/Repealed/20040401?DocDate=20101014`); a PDF link for 34 rows only, but every repealed act's page serves a PDF at `<path>&ViewType=Pdf` (HEAD on AA1987: HTTP 200, 24,745 bytes) | 298 |
| Uncommenced acts | `/Browse/Act/Uncommenced/All?PageSize=500` | title, `Act N of YYYY`, a link whose stamp changes daily (`/Act/AMLOMA2024/Uncommenced/20260915020850?DocDate=20240830`) | 10 |
| Acts Supplement by year | `/Browse/Acts-Supp/Published/<YYYY>?PageSize=500` | every Act of the year as published, with `Act N of YYYY`, its date and PDF (`/Acts-Supp/8-2026/Published/20260427?DocDate=20260427`), new principal acts and amending acts alike with no column saying which | 18 in 2026, 26 in 2025 |
| Current subsidiary legislation | the SL browse listing (its address was not kept by the audit) | S number and document date | 5,844 (2026-09-13) |

**Each act's detail page**, `/Act/<code>`, over plain GET, is the authoritative source:
- the current version's valid-from date beside `id="versionsButton2"` and `id="versionDateHidden"` (for example
  "05 Dec 2025"); it matches the newest timeline entry;
- the desktop timeline, one `<li data-id>` per version (14 for PDPA 2012, 71 for CPC 2010, 354 for ITA 1947),
  each with its `ValidDate`, its published date (`data-date`), its PDF, and a `group_status` line: "Amended by Act
  19 of 2025", "Amended by S 19/2015", the original enactment "Act 26 of 2012", or "2020 RevEd";
- the front page's revised-edition sentence ("This revised edition incorporates all amendments up to and including
  1 December 2021 and comes into operation on 31 December 2021");
- the subsidiary legislation tab, `?DocType=Act&ViewType=Sl&PageIndex=<n>&PageSize=100` (S number, title, document
  date, PDF `/SL/PDPA2012-S65-2021?DocDate=20240705&ViewType=Pdf`; PDPA 2012 lists 10, the Income Tax Act 774),
  and an RSS feed of provision changes.
Pages are 195 KB to 1.88 MB.

**The stored PDFs carry the version data themselves:**

| What the PDFs carry | Count |
| :---- | ----: |
| Footer "Informal Consolidation – version in force from D/M/YYYY" | 377 of 523 acts, 3 of 3 SL |
| Revised Edition acts with no footer (unamended since the revision; in force from 31 December 2021): 145 of the 2020 edition and the Multimodal Transport Act 2021 of the 2021 edition | 146 |
| A LEGISLATIVE HISTORY listing every amending instrument with its commencement | 486 of 523 |

The as-at date is derivable offline for all 523 acts; the official number for 522. The stored histories hold 6,185
references to 3,002 distinct amending instruments, 308 of them dated 2022 or later; two of those instruments are in
the corpus as documents.

**URL types:** `/Act/` and `/SL/` are consolidations; `/Acts-Supp/` and `/SL-Supp/` are as published.

**Official numbers:** `Act N of YYYY` for acts, `S N/YYYY` for subsidiary legislation. Older laws are cited by
their original ordinance. **The 2020 Revised Edition** re-issued every act in force from 31 December 2021: a
revision, not an amendment; on the timeline it is a version whose status reads "2020 RevEd".

**Dates:** the footer `5/12/2025` is day-first; the timeline reads `05 Dec 2025`; URLs `YYYYMMDD`. Never read
`5/12/2025` month-first.

### 1.3 What to watch for on this website

- **Three update checks refused, all of them sent with the wrong User-Agent** (2026-09-16 21:29 UTC to 2026-09-17
  02:04 UTC). Every listing request the update check sent was refused with HTTP 403: the first check stopped at
  once; the second rested 1, 5 and then 30 minutes four times at up to 60 s a request and got **seven 403s in a row
  over 126 minutes** on the 500-row Current listing; the third, reading 100 rows a page, got the same seven 403s on
  the 100-row page. Between the second and third, **single probes all answered 200**: the Online Criminal Harms
  Act's page, the Current listing at 100 rows, and its second page (23:45 to 23:53 UTC).

  **The page size was not the cause**, although it looked like it for an evening: the third check was refused on
  the very page a probe had loaded eleven minutes earlier. **What differed was the User-Agent.** The probes, the list
  build of 2026-09-15 and the crawl all send the stage's configured User-Agent, which carries the contact address;
  the update check built its client with no settings and sent the adapter's bare fallback,
  `RDTII-Rocky-Crawler/0.1 (+polite public-law retrieval)`, with no contact address. That was a bug in the check,
  fixed on 2026-09-17: it now identifies itself exactly as the list build and the crawl do, and prints the identity
  it uses. It is the most likely explanation, not a proven one; the next check will show.

  Two paging facts found on the way: **`PageIndex=` in the query is ignored** (the same first 100 rows), and the
  portal pages **by path**, `/Browse/Act/Current/All/1?PageSize=100&...` for rows 101 to 200, which is what each
  page's Next Page link names. Per-letter pages (`/Browse/Act/Current/S?PageSize=100`) also load; the longest current
  letter is S with 70 acts, the longest repealed S with 105. Listings are read 100 rows a page by the Next Page
  links since 2026-09-17 (`sso.listing_paging: next`, the code's default; `orders` keeps the single 500-row page
  read ASC and DESC): 12 listing requests instead of 7, each a fifth of the weight.

- **The edge challenges a plain client after sustained access.** The catalogue build of 11:50 to 12:58 UTC on
  2026-09-15 (540 requests, 6.0 to 8.4 s apart, every one at or above the `Crawl-delay`) got HTTP 200 on 490 and
  **HTTP 202 on 50** act pages from about its 45th minute; from 13:00 UTC every request, the PDF endpoint and
  `robots.txt` included, answered 202 with an empty body, `Server: CloudFront` and `x-amzn-waf-action: challenge`:
  AWS WAF bot control demanding a JavaScript challenge that a plain HTTP client cannot pass. Three probes 30 s
  apart and one 6 s apart were all challenged. The adapter treats that header as a stop (`LomThrottled`), never
  retries against it, and refuses to read anything when `robots.txt` itself is challenged. Round 1's crawl of July
  2026 (523 PDFs at 3 to 5 s) was not challenged, so the rule is new.

  **An hour of silence lifts it** (a probe at 14:05 UTC: `robots.txt` HTTP 200, no header), so the crawl runs in
  cycles: rest, one probe of `robots.txt`, resume the same run, and let the engine stop itself when 10 answers in
  a row are empty (it writes its manifest first). Every cycle of 2026-09-15 and 16:

  | Rest before | Pace | Crawled (UTC) | Span | Stored |
  | :---- | :---- | :---- | ----: | ----: |
  | 1 h (the first lift) | 6 s | 14:09 to 14:35 | 26 min | 125 |
  | 13 min | 15 s | 15:52 to 16:51 | 59 min | 74 |
  | 62 min | 30 s | 17:53 to 19:03 | 70 min | 74 |
  | 21 min | 15 s | 19:24 to 19:46 | 21 min | 48 |
  | 20 min | 15 s | 20:06 to 20:31 | 25 min | 39 |
  | 21 min | 15 s | 20:52 to 21:11 | 19 min | 21 |
  | **46 min** | **60 s** | **21:59 to 03:38** | **5 h 40 min** | **203** |
  | 30 min | 60 s | 04:09 to 04:59 | 50 min | 28 |

  The run's `RUN_NOTE.md` tabulates all 15 stretches, with the rest before each and what it stored.

  **What the numbers say.** The rest between cycles governs how long the next one lasts, more than the pace does:
  the same 60 s pace ran for 5 h 40 min after a 45-minute rest and for 50 min after a 30-minute one. Short rests
  give short cycles whatever the pace (three 20-minute rests at 15 s bought 21, 25 and 19 minutes). The best
  combination found is **a 45-minute rest and 60 s between fetches**, which is what the loop runs from 05:01 UTC
  on 2026-09-16. The challenge arrives in bursts before it settles: at 30 s it took 7 or 8 fetches at a time
  (18:17, 18:27, 18:43) with ten good minutes between, then every fetch from 18:57. **Every challenged fetch
  costs two requests,** because the engine falls through to its Playwright rung, which gets the same 202: headless
  Chromium does not pass the challenge either. A browser session that keeps the `aws-waf-token` would; that is the
  structural fix to decide (section 5).

  One resume, 15:36 UTC, was **not** challenged: the watcher of that hour counted the challenged fetches of 14:35
  at the tail of the crawl log and killed a healthy crawl after 9 good fetches, whose manifest rows were lost
  (their files are orphans in `raw/`: `orphan_file` in `tools/audit_run.py`). The loop was corrected at 15:47 UTC
  to let the engine stop itself, and a hard kill is never the first move (`scraper/WORKFLOW.md`, step 3).
- **After the crawl, the edge refuses the client outright.** On 2026-09-16 at 21:29 UTC, seven hours after the
  24-hour crawl ended, the first update check got robots.txt with HTTP 200 and then **HTTP 403** on the Current
  listing, its second request. That is a refusal, not the challenge (HTTP 202 with `x-amzn-waf-action`) the crawl
  met. The check stopped at once and wrote nothing. A plain client should now rest for hours, not minutes, before
  one attempt, and a browser session carrying the portal's token is the structural fix (section 5).
- **Two titles are too long for Windows.** The engine names each document's folder after the whole law name
  (`raw/sg/<slug>/<stamp>__native.pdf.headers.json`); under the run folder's path, two SL titles of 148 and 154
  characters push the sidecar past Windows' 260-character limit, and the store fails after the bytes arrived
  (`FileNotFoundError` in the crawl log, twice in the crawl of 14:09 UTC; `store_failed` in the audit). The crawl
  runs through drive `R:` (`subst R: <ws>`, 38 characters to `raw\sg\`) so every path fits; the engine should
  cap the folder name (2.5).
- **"Status: Current version as at …"** on every detail page is the viewing date in Singapore time and reads the
  same on every page. Never read it as the version date.
- **`Last-Modified` is not a legal date:** it is when SSO generated the PDF. PDPA's reads 14 July 2026 on a version
  in force from 5 December 2025, and 431 sidecars are more than 30 days older than the fetch. It moved on 3 of the
  9 seed re-fetches of 14 July 2026 although the bytes were identical; the bytes moved on none of the 9.
- **The default listing page is truncated to 20 rows.** Always ask for a size: `PageSize=100`, following the Next Page links (the 500-row page was refused from
  2026-09-16, 1.3); the SL tab pages at 100.
- **Two repealed acts can share a title** ("Accountants Act (Repealed)", 6 such pairs in the listing of
  2026-09-15). The engine keys its id map on the name, so the list suffixes the second with `[CODE, repealed DATE]`.
- **An act's official number is on its timeline only when the oldest version is the enactment:** 256 of 525 current
  acts on 2026-09-15; the rest begin with a revised edition or an amendment (`law_number_unknown`), and the number
  is on the PDF's page 1 or in the legislative history.
- **The RSS feed repeats a provision across versions:** PDPA 2012's feed has 902 items for 149 provisions, s 15 ten
  times. Each provision's first item carries its latest date.
- **A seeded title is out of date.** `links/seed_laws.yaml` line 47 says "Cybersecurity (Critical Information
  Infrastructure) Regulations 2018"; the stored PDF and the portal say "Cybersecurity (Provider-Owned Critical
  Information Infrastructure) Regulations 2018".
- **Amending acts are seeded with indicator tags,** against `POLICY.md` 3.2: `links/seed_laws.yaml` lines 10-11 give
  the PDPA (Amendment) Act 2020 six indicators, and lines 30-31 give the Cybersecurity (Amendment) Act 2024 one.
  Round 1's SG submission cites "Cybersecurity (Amendment) Act 2024" as the Law Name on 2 rows; under the finale
  instrument both score zero. The consolidation that contains the amended text, `sg-ca2018-001`, is already in the
  corpus.
- **Subsidiary legislation is thin in the corpus:** PDPA has 10 SL on the portal and 2 in the corpus; the
  Cybersecurity Act 7 and 1. The list of 2026-09-15 holds 188 SL under the seed acts.
- **Files that are not the law's text: checked since 2026-09-16.** `RULES["SG"]` in `tools/audit_run.py` reads
  the four prints the portal uses: a revised edition opens `THE STATUTES OF THE REPUBLIC OF SINGAPORE`, the title
  and `<YYYY> REVISED EDITION`; an act passed since the 2020 revision opens with its title and `(No. N of YYYY)`;
  subsidiary legislation opens `First published in the Government Gazette …`, `No. S <n>` and its parent act; an
  act as passed is printed in the `ACTS SUPPLEMENT`. The rules check that the row's title words and its number are
  on the page, and tell a short act printed in full from a repeal notice. **On the corpus of 738 documents they
  flag 27, none of them a wrong file:** 22 amending acts in their gazette form and 5 short acts printed in full.

## 2. How our scraper works

### 2.1 The big picture

```
sources.yaml + links/seed_laws.yaml      SSO and three regulators; 21 seed laws
        |
        |  step 1: build the link list   (scraper/catalogue.py: 540 requests at 6 s+, 68 minutes on 2026-09-15)
        |          robots.txt; the four listings; every current act's page; the seed acts' SL tabs
        v
links/documents.jsonl    1,041 documents in crawl order, each with its details
links/laws.csv           877 rows: the four listings, with what was decided for each act
        |
        |  step 2: crawl the list        (the Round 1 engine, SSO_FRONTIER=links_file, REQUEST_DELAY_MS=6000)
        |          not run yet: the WAF challenge of section 1.3
        v
outputs/SG/SG_ws_<date>/ manifest, raw files, crawl log
        |
        |  step 3: audit the files       (tools/audit_run.py, generic flags)
        |  step 4: write RUN_NOTE.md
        v
        |  step 5: update check          (updates/: a stub)
        |  step 6: merge the runs        (tools/merge_corpus.py)
        v
outputs/SG/SG_corpus_<date>/
```

| Step | Singapore, 2026-09-15 | What is still needed |
| :---- | :---- | :---- |
| 1. Link list | **Built** (`scraper/catalogue.py`), run live once; the review fixes (section 2.3) are in the code, not yet in the list | A rebuild once the WAF lifts, or a browser transport for the pages |
| 2. Crawl | Not run: every request is challenged since 13:00 UTC | The first crawl at `REQUEST_DELAY_MS=6000`, then its audit and note |
| 3. Audit | Generic flags | An `SG` rule set: the short title on page 1, "REPEALED" markers, the Revised Edition page |
| 4. Run note | The template | After the first crawl |
| 5. Update check | **A stub** (`updates/__init__.py`, section 2.6) | The check itself |
| 6. Corpus | `tools/merge_corpus.py` | A run to merge |

### 2.2 The code

| File in `scraper/` | What it does |
| :---- | :---- |
| `adapter.py` | `SgSsoAdapter`, what the engine calls. `discover` reads the portal through the paced client (robots.txt, the four listings, every current act's page, the seed acts' SL tabs page by page, capped by `subsidiary_max_per_act`) and builds one candidate per document with its `contract_meta`; with `sso.frontier: links_file` it replays a list instead. One failed page is a note (`amendment_check_incomplete` on that act); five in a row, a throttle code (403, 429, 467, 503) or a WAF challenge stop the build. `build_plans` is Round 1's recipe: the PDF by `requests` at the row's own address, the HTML form by a Playwright capture of `?WholeDoc=1` |
| `parse.py` | The page parsers: the listings (`parse_listing`), the detail page (`parse_detail`: current date, every version with its published date and amending instrument, the original number, the revised edition), the SL tab (`parse_sl_tab`); the date forms |
| `catalogue.py` | Step 1: builds and writes the list (`documents.jsonl`, `documents.csv`, `laws.csv`, `catalogue_meta.json`, `discovery_log.jsonl`) and reads it back; `cfg_fingerprint` (seeds, `sso:` settings, search terms) |
| `__init__.py` | Re-exports the adapter, `SsoUnavailable`, `LISTINGS`, `parse` and `catalogue` |

The paced client and the robots.txt rules are imported from Malaysia's package (`..my_gazette.client`,
`..my_gazette.robots`): one request at a time, the larger of the delay and `Crawl-delay` (6 s here), every request
logged.

### 2.3 What goes into the link list

**The build of 2026-09-15, 11:49:59 to 12:58:17 UTC** (`links/`): 540 requests, every gap 6.0 s or more (mean 7.6 s);
490 pages read, 50 act pages challenged (section 1.3) and left without details.
- **525 current acts**, one PDF each (`/Act/<CODE>?ViewType=Pdf`, Round 1's `source_url` form): 475 with their
  current version date, 423 with amending instruments, 438 with a revised edition, 256 with their official number
  (the rest `law_number_unknown`), 12.6 versions listed on average (0 to 354).
- **298 repealed acts**, one PDF each at `<path>&ViewType=Pdf`, with the repeal date.
- **10 uncommenced acts recorded only** (`laws.csv`: "not yet in force; the portal's address for its text changes daily").
- **The Acts Supplement of 2026 and 2025** (44 entries): 23 amending acts as published; 21 new principal acts
  recorded only, their consolidated text coming from the Current listing. The review fix of 2026-09-15 fetches a new
  principal act the Current listing does not carry yet (it takes effect at the next build).
- **188 SL under the 8 seed acts that are current acts**, from their SL tabs (one page of 100 in this build; the
  Income Tax Act lists 774; the setting `subsidiary_max_per_act: 100` caps a rebuild at 100 per act, every total
  recorded in `subsidiary_listed`).
- **The 21 seeds:** 11 SSO acts (among the 525, with their tags and provenance), 3 SL served from their acts' tabs,
  2 Acts Supplement and 3 SL-Supp entries at their own addresses, 5 regulator documents as they are. In this build
  the 8 non-`/Act/` SSO seeds kept their registry addresses (the review fix gives them the PDF address the crawl
  cites; the SL seeds are served once, from the tab).
- **Scopes:** `seed` 203 (the seeds and their SL), `relevant` 204 (plus the acts the title net selects), `all` 1,041.
- **Kinds:** 823 principal acts, 188 subsidiary legislation, 25 amending acts, 5 agency documents.

### 2.4 Politeness

6 s between requests to SSO (`Crawl-delay`), plus jitter: the build's 540 requests were 6.0 to 8.4 s apart. One
request at a time; never `/search`. The crawl runs through the engine's limiter, which has one delay for every
host: `REQUEST_DELAY_MS=6000`, and the links-file frontier warns when the engine's delay is below the host's
`Crawl-delay` (`POLICY.md` 5.5). Politeness did not prevent the WAF challenge of section 1.3.

### 2.5 What the engine must change

The same list as Malaysia's `NOTES.md` 2.5 (`POLICY.md` 5.5: robots.txt and `Crawl-delay` in the fetcher, a delay
per host, a wait before discovery requests, a language column, the link-file frontier read by the orchestrator, the
paced client moved from `adapters/my_gazette/` into the engine). Singapore adds: a browser transport for the
catalogue's page reads when the edge challenges plain clients (the engine's Playwright rung exists for documents;
the catalogue's client is plain HTTP). Two more, for every country: **cap the storage folder name** (`storage.py`
`store()` slugifies the whole law name; about 100 characters plus a short hash keeps every path under Windows'
limit, 1.3), and **checkpoint on every stored document** (the manifest is written every 10; a crawl killed
in between leaves files no row names, and the next resume fetches them again).

### 2.6 Updates: what changed since the last run

**Built 2026-09-16** (decision 22); `updates/WORKFLOW.md` is the procedure. It works from a date, as the developer
designed it, and reads only what could have changed.

- **New acts:** the Current listing, against the acts the baseline held (an act the baseline held as uncommenced
  has commenced).
- **New and amending acts as published:** the Acts Supplement of this year and last, by publication date.
- **Repeals:** the Repealed listing, by repeal date. Reported, never fetched.
- **Amendments: the act's timeline, by in-force date.** Each version on an act's page carries the date it took
  effect, the date the amending instrument was published, and which instrument it was. The two dates can be years
  apart (Act 40 of 2020: published December 2020, in force October 2022), so only the in-force date decides.
- **Which timelines are read:** the Current listing's file stamp is when the portal last generated the act's file.
  It is not a legal date (it matches the version date on 5 of 458 acts), but a new version always makes a new file,
  so an act with an older file cannot have been amended. The rest are read, seeds first, capped at 60.
- **New regulations under the seed acts:** each seed act's regulations tab, one request each.
- **Cost:** twelve listing requests plus one per timeline and one per seed act's regulations tab; 22 for the
  first two days (section 3).
- **The first check that read the portal** (2026-09-17 02:35 UTC): nothing changed since 2026-09-15.
- **The first live run was refused** (1.3): HTTP 403 on the second request, 2026-09-16. So were the second and third, on every listing request: the check sent a bare fallback User-Agent instead of the configured one, fixed 2026-09-17 (1.3).
- **Cadence and flaws** (`updates/WORKFLOW.md` section 8): check monthly, rebuild quarterly. The baseline of 2026-09-15 has no version date for 50 of 525 acts, and checks carry that gap forward until a rebuild.

## 3. Runs

| Run | What | Result |
| :---- | :---- | :---- |
| `outputs\SG\SG_ws_2026-09-15` | The first crawl from the list of 12:58 UTC, scope `all`, started 14:09 UTC on 2026-09-15 at `REQUEST_DELAY_MS=6000` and finished 14:19 UTC on 2026-09-16, in 15 stretches through drive `R:` (rest, probe, resume, the engine stopping itself at each challenge); from 05:17 UTC against the list without the repealed acts (decision 19) | **739 documents**: 524 of the 525 current acts, all 188 regulations under the seed acts, 24 of the 25 Acts Supplement acts, 5 regulator documents. 2 missing, 1 validation error by design (one instrument under two titles), 26 orphan files from a watcher's false kill. Corpus `SG_corpus_2026-09-16`, 738 documents, validates clean. Every stretch is in its `RUN_NOTE.md` |
| `outputs\SG\SG_ws_2026-09-15_to_2026-09-16` | The first update check that read the portal, since 2026-09-15, 02:35 to 02:54 UTC on 2026-09-17 at `REQUEST_DELAY_MS=15000`, with the configured User-Agent | **Nothing changed**: 525 current, 298 repealed, 44 Acts Supplement entries, 0 timelines to read, no new regulation under the 8 seed acts. 22 requests, all answered (one 503 rested and retried). 0 documents to crawl. `RUN_NOTE.md` |

The Round 1 crawl of July 2026 lives in the frozen corpus, which is hands off (decision 17) and is described in
section 7.

## 4. Output format against CONTRACT.md

| Contract column | Where it comes from on this portal | What Round 1 wrote | On the list of 2026-09-15 |
| :---- | :---- | :---- | :---- |
| `law_name` | The detail-page title or PDF masthead, not the YAML | title case, one outdated seed title | the listing's title; the page's in `law_name_portal` |
| `law_number` | History entry 1 (`Act 26 of 2012`), page 1 `(No. N of YYYY)`, or `S N/YYYY` for SL | empty on 523 of 536. Extraction then took table-of-contents fragments such as "Act\n14" on 116 laws | 256 of 525 current acts (the timeline's oldest entry); every SL, Acts Supplement and Uncommenced row |
| `portal_id` | The SSO act code (`PDPA2012`), the SL code (`PDPA2012-S65-2021`), the supplement entry (`8-2026`) | not recorded | every SSO row |
| `version_as_at` | The detail page's valid-from date; offline, the PDF footer, or 31 Dec 2021 for an unamended Revised Edition | not recorded | 475 of 525 current acts |
| `last_amended_year` | The valid-from year of the latest "Amended by" version on the timeline whose valid-from date is on or before the stored `version_as_at`; offline, the latest amending entry in the history. **Never the Revised Edition date.** 36 acts enacted after the revision have no history: 25 carry inline `[Act N of YYYY wef …]` or `[S N/YYYY wef …]` notes to parse, and 11 carry none | not recorded. Extraction wrote the Revised Edition cut-off, "1 December 2021", on 484 documents | 423 rows (`last_amending_instrument`, `linked_amendments`) |
| `legal_status` | The Current, Repealed and Uncommenced listings | the literal `Current` on all 536, including 2 amending acts and a PDPC guide | `in_force` 525, `repealed` 298, `not_yet_in_force` 10 (recorded), `unknown` on supplement entries and seeds off SSO |
| `document_kind`, `principal_law_number` | URL type (`/Act/`, `/Acts-Supp/`, `/SL/`, `/SL-Supp/`), the SL tab's parent act, "Amendment of X Act" in the amending act | not recorded | every row; SL rows carry `principal_portal_id` |
| `citation_url` | `https://sso.agc.gov.sg/Act/<code>`, optionally with `?ValidDate=YYYYMMDD` | `?ViewType=Pdf` download links on 531 rows, which download a file instead of opening the law | the PDF address (the row's `url`); the page address is `/Act/<code>` |
| `language` | `eng` | not recorded | every row |
| Dates | Footer `5/12/2025` is day-first; timeline `05 Dec 2025`; URLs `YYYYMMDD` | none recorded | ISO on every row read |

## 5. Open choices for the developer

Costs are at the 6 s minimum, one request at a time. `POLICY.md` 5.1 adds up to half again as jitter (6 to 9 s a
request), so real times run up to 1.5 times these figures, plus download time.

| Choice | Now | What to weigh |
| :---- | :---- | :---- |
| The WAF challenge (section 1.3) | Wait and probe; the adapter stops cleanly | A browser transport (the engine's Playwright rung) for the catalogue's page reads would pass the challenge at the cost of a browser per page; a slower pace may or may not avoid it. Decide after the first probe |
| Subsidiary legislation | The seed acts' SL, at most 100 per act (`sso.subsidiary_max_per_act`) | The Income Tax Act lists 774; all 5,844 current SL would take about 9.7 h to fetch, not recommended. Decision 12's rule (core acts only) applies |
| Amending acts | The Acts Supplement of two years, as published, linked to no principal (`principal_unlinked`) | F5 of the audit: record them as linked metadata from the timelines instead; the timelines already name every amending act per version |
| Status | From the listings | The Revoked listing is not read |
| Audit rules | An `SG` rule set in `tools/audit_run.py` | 0 requests |
| Offline metadata (F1) | Not done | Version date, official number, last-amended year and amending instruments from the stored PDFs' footers and histories, about 5 s locally, would fill the 50 acts the challenge left without details and the 269 without a number |

## 6. Known gaps

- No run, no audit rule set, no update check, no corpus (section 2.1); the list lacks details for 50 acts and the
  review fixes (section 2.3) until it is rebuilt.
- The subsidiary legislation of acts other than the seeds is not listed.
- `inventory_sg.csv` in the frozen corpus holds only the 21 seeds. The 523-row browse harvest survives only in
  `handoff1_old_v01`.
- 515 of 536 SG documents have no `.idmap.json` entry and no crawl-log line in the frozen corpus, so the delta
  lookup of step 1B cannot find them until those entries are rebuilt from the manifest. A new run under
  `outputs/SG/` starts its own map (decision 17), so this binds only anyone still reading the Round 1 corpus.
- 18 unreferenced files in `raw/sg` of the frozen corpus: 9 PDF-and-sidecar pairs from 11 July, still stored beside
  the byte-identical 14 July copies that the manifest now points to.

## 7. Round 1 corpus, against the portal

Hands off (decision 17); these counts describe it. 536 rows:

| Kind | Rows |
| :---- | ----: |
| `/Act/` consolidations | 523 |
| `/Acts-Supp/`, as-published amending acts | 2 |
| `/SL/` consolidations | 3 |
| `/SL-Supp/` | 3 |
| Regulator PDFs off SSO | 5 |

Everything that is not a current principal act came from hand seeds: 2 amending acts, 3 subsidiary legislation,
3 supplement instruments and 5 regulator PDFs. Nothing requested the subsidiary-legislation, Acts Supplement,
Repealed or Uncommenced listings. Round 1's adapter fetched the Current listing twice through Playwright (ascending
and descending) and wrote `in_force_status="Current"` as a literal on every row.

**Currency of the 11 SSO seed consolidations, live 2026-09-13.** 3 were behind the portal:

| Law | Stored version | Portal then | Indicators at risk |
| :---- | :---- | :---- | :---- |
| Criminal Procedure Code 2010 | 30 Jan 2026 | 17 Aug 2026, 2 versions later | 7.5 |
| Income Tax Act 1947 | 1 Jul 2026 | 11 Sep 2026, 2 versions later | 7.3 |
| PDP Regulations 2021 (S 63/2021) | 2 Mar 2026 | 1 Sep 2026, 1 version later | 6.4, 7.1 |

The other 8 matched the portal, PDPA 2012 and the Cybersecurity Act 2018 among them. The 9 seed PDFs re-fetched on
14 July 2026 were byte-identical to the 11 July copies.

## 8. Dead ends

- `Last-Modified` as a change signal (section 1.3). A byte hash did not move on any of the 9 re-fetches, so the
  byte hash is not a dead end. `PLAN.md` 1B-3 and decision 3 repeat Round 1's `docs/WORKFLOW.md`, which says SSO
  regenerates PDF bytes server-side; no re-fetch has shown it yet.
- Playwright for listings and detail pages: plain GET returns them server-rendered — until the edge challenges the
  client (section 1.3), when only a browser passes.
- Retrying a WAF challenge after 30 s: challenged again, three times.

## 9. Evaluation only

No gold-set count was made for Singapore. If one is made, it is never a seed list (`POLICY.md` section 4).

## 10. Files, hand-back and evidence

| Path | What it is | Repo counterpart, under `stages\p1-scrape\` |
| :---- | :---- | :---- |
| `scraper/checker.py` | **New, 2026-09-16** (decision 19). The law table: reads this folder's own files and writes `law_table.csv` into a run or corpus, one row per law with its status and dates. No repo counterpart yet; hand back with the package as `adapters/sg_sso/checker.py` |
| `scraper/` | The scraper package (section 2.2), with `WORKFLOW.md`: how to run a full crawl step by step | `src/p1_scrape/adapters/sg_sso/` (a package that replaces `sg_sso.py`); `WORKFLOW.md` to `docs/SG_CRAWL_WORKFLOW.md` |
| `updates/__init__.py`, `updates/WORKFLOW.md` | The stub: where SSO shows changes (section 2.6), and how the check will run | none until developed |
| `sources.yaml` + `links/seed_laws.yaml` | The registry: the Round 1 portals and search terms, the `sso:` block added 2026-09-15, and the 21 seeds | joined, `sources.yaml` first, into `instrument/sources_sg.yaml` and `contracts/instrument/sources_sg.yaml` |
| `links/documents.jsonl`, `documents.csv`, `laws.csv`, `catalogue_meta.json`, `discovery_log.jsonl`, `build.log` | The generated link list of 2026-09-15 (`links/README.md`) | not handed back as crawl input |
| `tests/test_sg_sso.py`, `tests/fixtures/` | 16 tests on the pages saved 2026-09-15 (`tests/README.md`) | `tests/`, `tests/fixtures/sg/` |

**Evidence behind this note:** the Round 1 amendment audit of 2026-09-13 (live requests to SSO: robots.txt, the
four listings, the PDPA, CPC and ITA detail pages, the seed consolidations' pages), the frozen corpus's manifest,
sidecars and PDFs, `pipeline-data\rdtii-p1-scrape\logs\sg_full_crawl.log`; the probes of 2026-09-15 (8 GETs and 1
HEAD at 6 s or more before the build, 7 probes of the challenge after it, all logged in the session scratchpad
`sso/probe_log_2026-09-15.jsonl`; the pages in `tests/fixtures/`); the catalogue build of 2026-09-15
(`links/discovery_log.jsonl`, `build.log`).
