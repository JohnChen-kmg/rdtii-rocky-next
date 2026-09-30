# Malaysia notes

The general note for Malaysia:
- **Section 1:** what the Laws of Malaysia website looks like.
- **Section 2:** how our scraper reads it.
- **Sections 4 to 9:** what was decided, and what is still open or missing.

Results of individual runs are not kept here. Each run has its own folder and `RUN_NOTE.md` under
`outputs\MY\` (section 3).

Written 2026-09-13; reorganised 2026-09-14 into this general note after the first full crawl. Counts marked
"2026-09-14" come from the link list of that day (08:56 UTC, kept in `outputs\MY\MY_ws_2026-09-14\links_rebuilt`)
unless a run note is named; the list in `links/` was rebuilt on 2026-09-15 with every act's timeline (section 2.3).

## 1. The website

### 1.1 The sites we use

| Site | Host | What we take from it | robots.txt |
| :---- | :---- | :---- | :---- |
| **Laws of Malaysia**, Attorney General's Chambers (AGC) | `lom.agc.gov.my` | The current file of every principal act that offers one; the amending acts in the amendment list (A1392 on), and what a read timeline lists as amendments but that list lacks; the commencement orders amending acts cite, where a read timeline lists them; and P.U. (A) subsidiary legislation on the core acts' timelines | **HTTP 500** on every logged read, 2026-09-13 and 2026-09-14 (the last at 08:40 UTC). Crawled anyway under decision 9 |
| Federal gazette | `federalgazette.agc.gov.my` | Nothing: the host does not resolve | unreachable |
| Personal Data Protection Department | `www.pdp.gov.my` | Seed documents: three guidelines, the PDP Standard 2015 and the PDP Regulations 2013 (PDFs), and the landing pages of two codes of practice (the codes themselves are not downloaded). Its pages for Act 709 and A1727 are used only if lom cannot be read | none (404) |
| Securities Commission, Bank Negara | `www.sc.com.my`, `www.bnm.gov.my` | Seed documents: one guideline each | not read |
| NACSA, Royal Malaysia Police (CCID) | `www.nacsa.gov.my`, `ccid.rmp.gov.my` | Fallbacks only: the five Cyber Security Act instruments are taken from lom since the list of 2026-09-14 08:56 UTC, and CCID's Computer Crimes Act PDF is used only if lom cannot be read. The 2026-09-14 crawl, from the older list, stored the NACSA copies | not read |
| Secondary copies | `cyrilla.org`, `commonlii.org`, `um.edu.my` | Seed fallbacks only, flagged `secondary_copy` | not read |

### 1.2 What Laws of Malaysia looks like

**Two lists of acts.**

| Page | What it lists | Records |
| :---- | :---- | ----: |
| `principal.php?type=updated` | Every principal act, with its current file and "As At" date in English (BI) and Malay (BM) where the portal has them. On 2026-09-14, 45 acts offered no file, 96 only one, and 131 had no "As At" date | 890 on 2026-09-13, 885 on 2026-09-14. The five dropped records (26/1947, 31/1961, 49/1965, 91 (revised), 406 (Revised)) each repeated another record's act id |
| `principal.php?type=amendment` | Every amending act from A1392 (published 2 June 2011) on, with royal assent, publication and commencement dates, and PDFs in both languages | 406 rows, 402 acts |

**Two lists of subsidiary legislation** (read since 2026-09-14, by the update check).

| Page | What it lists | Records |
| :---- | :---- | ----: |
| `subsid.php?type=pua` | Every P.U. (A) instrument: number, titles, publication date, a status (raw values seen: PRINCIPAL, AMENDMENT, PINDAAN, CORRIGENDUM, CANCEL; the page's script also labels REVOCATION, REPRINT and REPRINT ONLINE, and shows CANCEL and REVOCATION alike as "Revocation"), the parent act's number, a related instrument, and the file. The server sorts by publication date, newest first; the sort is not unique, so a record can straddle two pages | 7,306 on 2026-09-14 |
| `subsid.php?type=pub` | Every P.U. (B) notice, the same way | 9,150 |

Both POST to `json-subsid-2024.php` with `type=pua` or `pub`, encrypted like the act lists, with the same key.

**The home page has a "What's New" panel:** one tab per day for the last seven days, listing what was published
that day; boxes with the three newest principal acts (884 to 882 on 2026-09-14) and amending acts (A1793 to A1791);
and three P.U. (A) and three P.U. (B) entries that are not simply the newest (that day 262, 253, 324/2026 and
98.1998, 335/2026, 334/2026). Its "See All" link (`kuda.php`) is commented out. The scraper does not read it: the
listings cover any period.

**The lists are encrypted.**
- Both pages are empty shells. Their DataTables code POSTs to `json-updated-2024.php` or `json-amendment-2024.php`
  and receives `{"encrypted": true, "data": …}`.
- The data is base64 of an IV (12 bytes), a tag (16 bytes) and AES-256-GCM ciphertext. The browser decrypts it
  with a key the page itself publishes (`SEARCH_RESPONSE_KEY`).

**Each act has a detail page, reachable only through a signed link.**
- A list row links to `processFile.php?isDirect=1&token=…`, which answers with a redirect (302) to a signed
  `act-detail.php?a=…`.
- A hand-built `act-detail.php?act=709&lang=BI&date=01-07-2023` (the parameters the signed link carries) answers
  "Invalid request", with or without the list page as referer. So does `act-detail.php?type=amendment&act=A1727&lang=BI`.

**The detail page has three tabs:** Timeline, Subsidiary Legislation and Brief Description.
- **Subsidiary Legislation** is another encrypted table. It loads its rows with a POST to `json-subsid-2024.php`,
  the endpoint behind the site-wide P.U. lists above, with the act's number. That per-act request was never sent:
  the update check reads the site-wide lists instead, and the timelines list the instruments.
- **Brief Description** read "Not available in this portal." on the Act 709, A1727, Act 53 and Act 874 pages saved.

**The Timeline tab is the act's history.** Each entry has a date, a project id, a type and a PDF:
- **ORIGINAL, REVISED, REPRINT, REPRINT ONLINE:** the act's own versions. The Income Tax Act's timeline has one
  REVISED entry, its 1971 revised edition.
- **AMENDMENTS:** what amended it.
  - Most entries are amending acts. Some are P.U. (A) and P.U. (B) instruments: 24 of the Income Tax Act's 107.
  - An entry's project id equals `ILP_PROJECT_ID` in the amendment list.
  - It also equals the project id in the file path of a plain-numbered act, such as a Finance Act, that the
    principal list shows as an act of its own, but only while the list still offers that act's as-enacted file.
    On the Income Tax Act's timeline that is 16 of 51 plain-numbered acts (14 Finance Acts, and Acts 863 and 875).
    The rest are listed under a later reprint with another project id (Act 742), or under an old path with no
    project id (Act 578).
  - The Income Tax Act's timeline goes back to 1967 and lists 48 of the 49 Finance Acts.
- **SUBSIDIARY_LEGISLATION:** P.U. (A) instruments (regulations, orders, rules) and P.U. (B) notices, each with a
  file and no title, and usually a number. 8 of the Income Tax Act's 220 show only a date and a file
  (`PUA344_2023.pdf` to `PUA352_2023.pdf`).

**An amending act's own detail page names its commencement order.**
- It gives the order's PDF and its per-section dates.
- A1727's list remark "24/12/2024 [P.U. (B) 522/2024]" is the order's publication date. The order brings
  sections into force on 1 January, 1 April and 1 June 2025.

**Documents are plain downloads** of `/ilims/upload/portal/akta/…` PDFs.

**How the website writes things.**
- **Numbers:**
  - `Act N` is a principal act and `Act AN` an A-numbered amending act.
  - `P.U. (A) N/YYYY` is subsidiary legislation and `P.U. (B) N/YYYY` a notice, including commencement orders.
- **Plain-numbered amending acts:** Finance Acts and tax-measures acts sit in the principal list. Only another act's
  timeline shows what they amend.
- **Revised editions** take a new act number.
  - When the law they replace is a listed act, the list usually marks it "(Superseded by Act N)" in English and
    "(Diganti oleh Akta N)" in Malay: 12 acts on 2026-09-14.
  - Act 437, replaced by Act 865, has no marker; only its file says "Superseded by Act 865".
  - Some revised editions replace laws that are not in the list at all (the National Land Code, Act 828).
  - The revised edition prints a "LIST OF LAWS OR PARTS THEREOF SUPERSEDED".
- **Status markers** in titles and remarks: "(Repealed by Act N)", "(Dimansuhkan oleh …)", "(Superseded by …)",
  "(BELUM BERKUAT KUASA)" (not yet in force), and remarks such as "NOT YET IN FORCE". Most acts carry no marker.
- **Language and edition:**
  - Icons mark English (BI) and Malay (BM) files, printed or online.
  - An asterisk before a title marks an online version of an updated reprint, not a reprint made under section 14
    of the Revision of Laws Act 1968.
  - A file under `/terjemahan/` is a translation.
- **Dates:** mostly day-first, a few ISO, and month names in English or Malay in remarks and orders. A date beside
  a P.U. (B) number can be that order's publication date.
- **Filenames** say nothing reliable about draft status, version or even which act the file is.

### 1.3 What to watch for on this website

Found while building the scraper and checking the 2026-09-14 crawl. The run note is
`outputs\MY\MY_ws_2026-09-14\RUN_NOTE.md`.
- **robots.txt answers HTTP 500.** RFC 9309 treats that as "disallow everything". Decision 9 crawls lom anyway.
- **Some files answer HTTP 500:** 4 in the 2026-09-14 crawl, and 19 of the 94 old gazette and P.U. files the
  timelines revealed (2026-09-15). The portal keeps the entries and fails to serve the files.
- **Some detail pages have no timeline:** 5 amendment pages answered HTTP 200 without one on 2026-09-14.
- **The file listed for an act is not always its text.** `tools/audit_run.py` reads the first two pages of every
  stored file and flags these (decision 17; `audit.md` in each run folder). On the 1,311 files of the 2026-09-14
  crawl, 132 rows carry a flag and 116 a wrong-file or unreadable one (4 of them more than one, so the parts below
  sum to 121):
  - **Repealed acts:** 76 files are a repeal notice of 1 to 4 pages (`repeal_notice`); 90 principal-act files have
    4 pages or fewer, the other 14 being short acts (Act 880, the Fees validation acts, the Anti-Fake News (Repeal)
    Act 2020) or scanned notices.
  - **Another act's text** (`other_act_text`, 5): Act 696, Witness Protection Act 2009, links the Judicial
    Appointments Commission Act (695); Acts 90, 320 and 310 link the repealing act's text (611, 646, 364); Act 565
    links Akta 556. Act 756 links a gazette notification (`gazette_notice`).
  - **Language** (`language_mismatch`, 7): English links point to Malay files for Acts 680, 575, 556, 348, 337, 310
    and 104.
  - **No text layer** (29): scanned files that need OCR: 14 principal acts, 14 amending acts and the PDP Regulations
    2013.
  - **Landing pages** (2): the two PDPC codes of practice from the seed list are HTML pages, not documents.
  - **A bundle** (`parent_not_named`, 1): the "amendment" of the Communications and Multimedia Act 1998 of 5 November
    2015 is a 51-page P.U. (B) supplement whose first pages are plant-variety notices.
  - Informational: 7 older amending acts are stored as their gazette print (cover page first, the act from page 2),
    and 4 "amending act" rows are P.U. orders, as the portal's amendment listing gives them.
- **Timeline "amendments" are not always amending acts.** The 4 amendments known only from timelines are Gazette
  supplements and P.U. (A) orders.
- **Current texts trail their amendments.** On 2026-09-14, 80 principal acts had 93 amending acts dated after the
  text's as-at date. The PDPA's 2023 reprint predates A1727 (2024): no s.12A (data protection officer), no s.12B
  (breach notification), and the old s.129(1).
- **One file can be listed for two acts:** "Act 714 (Repealed by Act 811).pdf" is listed for both.
- **lom's clock runs about 6 minutes fast** (`Date` header), so time events by our own timestamps.
- **The list changes between days:** 890 records on 2026-09-13, 885 the next day. Nothing else differed between
  those two readings, nor between the morning and the evening of 2026-09-14 (section 2.6).
- **No upload date is published for an act's file.** The listing gives the consolidation's "As At" date only. The
  file's `Last-Modified` header is the upload time (on or after the as-at date for 732 of 733 dated acts stored on
  2026-09-14), but it is seen only by requesting the file.
- **Validators are nearly stable, and a file can change behind its path.** 560 lom files were refetched at the same
  path between 14 July and 14 September 2026 (Round 1 wrote the paths with spaces, the 2026-09-14 crawl with `%20`).
  559 were byte-identical; 557 of those kept both ETag and Last-Modified, and 2 (Acts 719 and 866) were re-uploaded
  unchanged with new validators on 27 August and 7 September 2026. The one file whose bytes changed (Act 869, uploaded
  21 August 2026, 6 bytes shorter, its listing as-at date still 18 July 2025) changed both validators, so no changed
  file hid behind old validators. A conditional GET answers 304 without a body (checked 2026-09-14 21:47 UTC on the
  stored PDPA file), and so does a conditional HEAD (22:28 UTC).

## 2. How our scraper works

### 2.1 The big picture

```
sources.yaml             where to look and how: lom addresses, settings, the title rule
links/seed_laws.yaml     the 21 laws named on purpose, with their links
        |
        |  step 1: build the link list   (scraper/catalogue.py; about 226 paced requests, no documents)
        |          reads robots.txt, both lists, and the detail-page timelines the settings ask for
        v
links/documents.jsonl    every document to fetch, in crawl order, with its details and scopes
links/laws.csv           every listed act, and why it has no document when it has none
        |
        |  step 2: crawl the list        (the Round 1 engine, with LOM_FRONTIER=links_file)
        |          downloads each file, classifies it, stores it with its HTTP headers
        v
outputs/MY/MY_ws_<date>/ manifest, raw files, crawl log
        |
        |  step 3: audit the files       (tools/audit_run.py: the first two pages of every stored file)
        |  step 4: write RUN_NOTE.md     (from the files; a row in outputs/MY/README.md)
        v
        |  step 5: update check          (updates/: 8 requests, plus two per changed act under timeline: all;
        |                                 a delta list crawled into MY_ws_<since>_to_<date>/)
        |  step 6: merge the runs        (tools/merge_corpus.py, an option: never into a run)
        v
outputs/MY/MY_corpus_<date>/ one document per law, the newest run's copy; what extraction and mapping read
```

The six steps are the convention for every country (`CONVENTIONS.md` section 2, decision 17).

**Why two steps.**
- The list can be read, checked and changed before anything is downloaded.
- A crawl can be repeated from the same list.
- The list keeps the details the Round 1 engine does not write to the manifest (document kind, status, language,
  version date). A manifest row joins back to its list row on `source_url`.

**How to run it, step by step:** `scraper/WORKFLOW.md` (a full crawl) and `updates/WORKFLOW.md` (only what
changed). `links/README.md` explains the list's files; `outputs/README.md` gives the rules for run folders and notes;
`tools/README.md` the audit and the corpus merge.

### 2.2 The code

| File in `scraper/` | What it does |
| :---- | :---- |
| `adapter.py` | `MyGazetteAdapter`, what the engine calls. It reads the lists and timelines, decides what to fetch and fills every row's details |
| `client.py` | The paced connection to lom: one request at a time, redirects followed hop by hop, `Retry-After` honoured |
| `robots.py` | robots.txt parsing and matching (RFC 9309) |
| `parse.py` | Decrypting the lists, reading timelines and dates, choosing a version |
| `relevance.py` | The title rule |
| `catalogue.py` | Step 1: builds and writes the link list, and reads it back for step 2 |
| `records.py` | The data records and error types |
| `__init__.py` | Re-exports the names of `records`, `robots`, `client`, `parse` and `relevance`, `MyGazetteAdapter` with three `adapter.py` constants, and the `catalogue` module, so `my_gazette.X` keeps working |

### 2.3 What goes into the link list

**Rebuilt 2026-09-15 with `lom.timeline: all`** (decision 17), 05:07 to 07:21 UTC: 1,970 paced requests (every
gap at least 3.0 s, 4.1 s on average; `links/build.log`, `discovery_log.jsonl`), no document fetched. Against the
`rule` list of 2026-09-14 (226 requests, 15 minutes; kept in `outputs\MY\MY_ws_2026-09-14\links_rebuilt`):
- **1,414 documents** (1,315 before): 823 principal acts, 491 amending acts (422), 47 commencement orders (17),
  44 P.U. (A) instruments, 9 agency documents. 100 addresses are new: 68 amending acts (65 of them amendments
  known only from timelines, `not_in_amendment_listing`, plus Act A1796, Act A1795, Act A1794), 30 commencement orders found on
  the amending acts' timelines, and 2 principal acts (Act 885 and the new Act 807 file). The 6 documents the delta
  run of that morning stored are among the 100; 1 address left (the old Act 807 file).
- **Every act's dates:** `published_on` on 1,267 rows (545 before), `enacted_on` on 1,157 (484), an edition
  (`timeline_log_type`) on 796 (80), `linked_amendments` on 480 (208); **0 rows with an incomplete amendment check**
  (298 before). `laws.csv` has 1,291 rows; 982 had a detail page read: all 886 principal acts, and 96 of the 405
  amending acts (those the commencement rule asks for).
- **103 documents in the list that no run stored** (on the morning of the rebuild): 67 amending acts, 29 commencement orders, 2 principal
  acts and 5 P.U. (A) instruments. 9 of them were in the 2026-09-14 list too:
  the 4 HTTP 500 files (Acts 175 and 150, A1740, A1626) and the 5 Cyber Security Act instruments, which the crawl
  stored from NACSA under other addresses. The other 94 are new to the list. A crawl from the list would fetch
  all 1,414 again (the engine's id map starts fresh per run), so the check gained a `--list` mode the same day
  (section 2.6): it fetched 98 of them at 11:36 UTC (the 5 NACSA copies were logged duplicates), 75 stored and 23
  failed on the portal's side (`MY_ws_2026-09-15_to_2026-09-15`).
- **29 amending acts' detail pages held no readable timeline** (HTTP 200), against 5 seen under `rule`: A1444,
  A1449, A1452, A1455, A1456, A1485, A1509, A1515, A1522, A1526, A1539, A1564, A1582, A1586, A1634, A1730, A1756,
  A1757, A1758, A1759, A1769, A1785, A1786, A1787, A1790, A1791, A1794, A1795, A1796.
- **4,735 distinct subsidiary instruments** listed on 270 read timelines were recorded, not fetched (decision 12):
  Act 19 447, Act 828 431, Act 235 409, Act 333 342, Act 53 172, Act 634 157, and so on.
- The delta list of `MY_ws_2026-09-14_to_2026-09-15` was built under the same settings (same `cfg_sha256`
  cbb0bd1e…).

**Where documents come from.**
- The two lists, for every principal act's current file and every amending act from A1392 on.
- Timelines, for commencement orders, P.U. (A) instruments under the core acts, and AMENDMENTS entries the
  amendment list lacks.
- `links/seed_laws.yaml`, for agency documents.

**Scopes.** A crawl takes one scope. Each scope contains the one before it.

| Scope | Holds | Rows, 2026-09-14 |
| :---- | :---- | ----: |
| `seed` | The 21 seeds (the 5 Cyber Security Act instruments among them, as the portal's copies), their later amending acts and commencement orders | 28 |
| `relevant` | Plus the 81 other live acts the title rule selects (79 principal acts, and Acts 863 and 875 recorded as amending acts of Act 53), their later amendments and orders, and P.U. (A) instruments under the core acts | 184 (189 in the crawl's 07:04 list, which listed the five Cyber Security instruments twice) |
| `all` | Every principal act's current file (823; 45 acts offer none), every amending act (422, of which 16 are plain-numbered acts the portal lists as amendments), 17 commencement orders, 44 P.U. (A) instruments, 9 agency documents | 1,315 |

Malaysia crawls scope `all` (decision 11).

**The title rule** (decision 11) is data in `sources.yaml`, derived from the instrument's pillar 6 and 7 definitions,
never from the gold set.
- **Groups:**
  - 5 core: data protection; cyber security and computer misuse; communications and interception; electronic
    transactions and online services; criminal procedure and security.
  - 6 sectoral: financial, tax, company, health, employment records, and platform and survey carriers.
- **Exclusions:** 4, among them annual Finance Acts and "(AMENDMENT)" titles.
- **What it does:** orders the crawl, decides whose timelines are read (the 87 live acts it selects, and the
  seeds), and decides whose subsidiary legislation is fetched.
- **What it never does:** set indicator hints. `seed_query` holds the words it matched (`data`, `tax`).
- **Why crawl everything anyway:** the rule misses real carriers found in Round 1 texts: six acts where the Public
  Prosecutor authorises interception, and about nine acts with minimum retention periods.

**Which version of an act** (`POLICY.md` 3.1):
- The document with the latest as-at date of its own edition, in the first preferred language (English, decision
  14).
- Printed before online only on equal dates.
- A date is never borrowed from another edition.

**Later amendments** (`POLICY.md` 3.3):
- **What is fetched.** An amending act is fetched with its principal when any date the portal gives for it is after
  the principal's as-at date, or it is not yet in force, or it has no date at all.
  - The dates used are the commencement field, every date in the remark and its commencement order's dates.
  - The publication date is used when none of those has one.
- **Flag.** The principal gets `stale_vs_portal`.
- **Amendments not in the amendment list.** An AMENDMENTS entry on a read timeline with no row in the amendment
  list, which includes every amendment before A1392, is fetched when it is dated after the as-at date
  (`not_in_amendment_listing`). On 2026-09-14 the 4 such rows are dated 2015 to 2017 and are Gazette supplements
  and P.U. (A) orders, not amending acts (section 1.3).
- **Where the check cannot see.** When an act's timeline was not read and its as-at date is before 2 June 2011, or
  missing, the row gets `amendment_check_incomplete`: 298 on 2026-09-14.

**Linking an amending act to the act it amends.**
- **How:** by the timeline's project id, else by title. The title match normalises apostrophes and allows
  "1959/63" years. When several acts match, it prefers the one not repealed or superseded and not younger than the
  amending act.
- **2026-09-14:** 358 of the 422 amending rows are linked, 128 by timeline and 230 by title. The other 64, mostly
  Supply and Appropriation Acts, are `principal_unlinked`.

**Plain-numbered amending acts** (decision 13).
- **The rule:** a principal-list act that a read timeline lists under AMENDMENTS is recorded as an amending act,
  matched by its current file's project id or by the same file.
  - It gets `amending_act`, `principal_law_number` (the act whose timeline lists it), `amends` (all such acts), no
    indicator hints, and the flag `listed_as_principal_by_portal`.
  - On 2026-09-14 that is 16 acts on the Income Tax Act's timeline: Finance Acts and the 2024 and 2025
    tax-measures acts.
- **Exceptions:**
  - A Finance Act that AGC has reprinted keeps its own text and stays a principal act.
  - A repealed act, or a repeal-notice file, is never reclassified this way; it is flagged
    `listed_on_other_timeline` (Act 125).

**Legal status is never guessed** (`POLICY.md` 3.5):

| Portal statement | `legal_status` | `status_source` | Rows, 2026-09-14 |
| :---- | :---- | :---- | ----: |
| "(Repealed by Act N)", "(Repealed by Act P.U. (A) 146/1969)", "(Dimansuhkan oleh …)" | `repealed` | `portal_listing` | 90 principal |
| "(Superseded by Act N)", "(Diganti oleh Akta N)" (decision 10) | `repealed` | `portal_listing` | included above |
| "(Repealed by Act 655 in respect of its application to …)" | `partially_in_force` | `portal_listing` | 0 (Act 508 has no document) |
| "(BELUM BERKUAT KUASA)" in a title | `not_yet_in_force` | `portal_listing` | 6 |
| Amendment remark "NOT YET IN FORCE" | `not_yet_in_force` | `portal_remark` | 11 |
| Remark "Not Yet In Force except …", or one that also dates parts | `partially_in_force` | `portal_remark` | 1 (A1530) |
| Commencement date field later than the run date | `not_yet_in_force` | `portal_listing` | 1 (A1770) |
| anything else | `unknown` | none | |

**Language** (decision 14).
- **English first** when AGC publishes an English text, printed or online. Malay only when it does not: 2
  documents.
- **Official is not authoritative.** Every row taken from the two lists records its language and edition. The 74
  rows found on timelines or from agency seeds record neither. 19 acts carry `english_online_malay_printed`.
- **The language comes from the portal's icon,** so a Malay file behind an English link is recorded as English
  (section 1.3).

**Subsidiary legislation** (decision 12, confirmed by decision 17).
- **Fetched:** P.U. (A) instruments under the core acts, once each, no cap. On 2026-09-14 that is 44:
  - AMLA 2001 (Act 613) 15;
  - the Communications and Multimedia Act (Act 588) 11;
  - the Online Safety Act 2025 (Act 866) 7;
  - the Cyber Security Act 2024 (Act 854) 5;
  - Mutual Assistance in Criminal Matters (Act 621) 4;
  - Acts 843 and 741, 1 each.
- **Counted only:** numbered instruments on the read timelines of other acts, 1,138 on 45 timelines, led by the
  Customs Act (409), the Income Tax Act (172) and the Printing Presses and Publications Act (74).
- **Neither counted nor fetched:** P.U. (B) notices on the core acts' timelines, and instruments on acts whose
  timeline was not read.
- **Commencement orders** are fetched when a read timeline (the amending act's own, or its principal's) lists the
  P.U. (B) number an amending act's remark cites: 17 orders for 286 distinct cited numbers on 2026-09-14 (287
  citations: P.U. (B) 189/2012 is cited by both A1422 and A1424).

**Seeds naming a P.U. instrument** carry its full number (P.U. (A) 221/2024 and so on, read from the gazette copy).
The portal's copy on the act's timeline is then fetched once, under the seed's name, tags and provenance
(`seed_resolved_to_portal`; `POLICY.md` 2 ranks the portal first).

**A file listed for two acts** is stored once, under the repealed act whose own marker names the other act (Act 714,
"Repealed by Act 811"), and the other act is recorded on that row (`also_listed_for`).

**If lom cannot be read** (robots.txt, an outage, three throttled answers, a changed page format):
- Every seed outside lom is kept.
- A seed on lom falls back to its registry `url` when that is not the lom root, else to a whitelisted
  `fallback_url` flagged `secondary_copy` (Acts 593, 747 and 53). A seed with neither, the Cyber Security Act 2024
  (Act 854), is dropped with a note.
- The failure is printed and kept in `adapter.lom_error`, and a run that selects nothing raises.
- A link-list build that cannot read lom writes nothing.

**Replaying a list** (step 2):
- The scraper reads robots.txt again and drops any lom row it disallows.
- It refuses a list whose fingerprint (`cfg_sha256` in `catalogue_meta.json`) differs from the registry. A list
  without a fingerprint is served with a warning only.

### 2.4 Politeness

- **Speed limit:** one request at a time per host, `REQUEST_DELAY_MS` (3000) plus up to half again as jitter, or a
  longer robots.txt Crawl-delay. The limits do not move (decision 6).
- **robots.txt** is read first and matched on the product token `RDTII-Rocky-Crawler`, with `*` and `$` patterns and
  the longest match. Every request, redirect hop and lom document is checked. lom's 5xx answer is passed only
  under `lom.robots_5xx: allow`, which is read from the registry only, never from the environment.
- **During link-list builds,** the scraper paces every request itself, retries and redirect hops included.
- **HTTP 429 or 503** waits `Retry-After` (at most 600 s) and re-sends up to twice. Three such answers in a row stop
  lom for the run.
- **One host, one process.** No link-list build runs while a crawl of the same host runs.
- **Document downloads in step 2 are paced by the Round 1 engine,** which has gaps that section 2.5 does not list: no
  wait after a download ends, an unpaced fallback request, and no robots.txt read for agency hosts (`POLICY.md`
  5.5). The 2026-09-14 run note, issues 3 to 5, measures them.

### 2.5 What the engine must change, or part of this scraper's work is lost

All are in the Round 1 engine's `orchestrator.py`, and belong to the hand-back (section 10).

| Engine change | Why | What the scraper provides |
| :---- | :---- | :---- |
| Write each discovery request to `crawl_log.jsonl`, plus one line for the robots.txt decision | `CONTRACT.md` section 2 wants one line per request. Discovery is invisible there today, including the robots.txt read a link-list replay makes (`POLICY.md` 5.5) | `adapter.discovery_log`, `adapter.robots_record`. The build writes `links/discovery_log.jsonl` itself |
| Seed the rate limiter's last-request time for `lom.agc.gov.my` from the scraper, and use the larger of `REQUEST_DELAY_MS` and the scraper's host minimum | One wait per host across discovery and documents (`POLICY.md` 5.1) | `adapter.last_request_at`, `adapter.host_min_delay`. Until then the scraper waits one delay before returning |
| Return non-zero when an economy is skipped, selects no candidates, or reports a lom failure | `POLICY.md` 5.6 | `adapter.lom_error`. The scraper raises when it selects nothing |
| Keep `cand.contract_meta` per stored document | Links, kinds, status and version dates exist only there | `cand.contract_meta`. Meanwhile the link list holds it, joined on `source_url` |
| Resume by comparing the stored `source_url` with the candidate's, or refresh into a new folder and migrate (`CONTRACT.md` section 5) | Resuming into the Round 1 hand-off skips by name 20 of the 28 seed-scope rows (20 of 25 in the 2026-09-13 seed crawl), so it keeps Round 1's older texts of Acts 709, 593 and 53 | nothing needed. Each run has its own folder (`outputs/README.md`) |
| Seed the content-hash check from the loaded manifest, and rename the 95 bare `Act N` entries (85 of them for acts listed today) and Act 719 before any cumulative crawl | Otherwise 86 acts get new `doc_id`s, and 63 of them re-store bytes identical to Round 1's and fail validation | nothing needed |

### 2.6 Updates: what changed since the last run

`updates/` (decision 16) answers "what changed since the last run?" without fetching any document, and writes the
list of what to fetch. In one sentence: the check asks the website what it has published since the date of the
last run and fetches only that; for the main acts, which carry no upload date, it compares today's list of acts
with the list saved from the last run. The steps are in `updates/WORKFLOW.md`. It is separate from the scraper and reuses its parsers and its candidate builders.

```
outputs/MY/<newest run>/   laws.csv (what the portal listed), manifest.jsonl (what was stored, with ETag)
        |
        |  check    python -m p1_scrape.adapters.my_gazette.updates --outputs outputs/MY [--since YYYY-MM-DD]
        |           8 paced requests, no document: robots.txt, both act lists whole (1 GET and 2 POSTs; 1 GET and 1
        |           POST), the newest page of the P.U. (A) and of the P.U. (B) list (1 POST each, the act lists'
        |           key reused), and the detail pages of the acts that changed
        v
outputs/MY/MY_ws_<since>_to_<date>/   changes.md, changes.json   every change found, fetched or not, and why
                           links_used/                the delta list: only the documents to fetch, in the link-file format
        |
        |  crawl    the normal replay (LOM_FRONTIER=links_file), into the same run folder
        v
                           manifest, raw/, crawl_log  the new and changed documents only
```

**What "since" means.** By default the day the newest run under `outputs/MY/` started; `--since` overrides it.
With a run to compare with, the check is exact for acts (baseline mode). Without one (`--no-baseline`, or no run),
date mode takes acts whose as-at date and amending acts whose publication date fall on or after the date, and says
on each of those rows that this is approximate: an act re-uploaded with an older as-at date is missed. Instruments
are taken by publication date in both modes, on or after the date less the look-back (below), minus what a run
already stored.

**What counts as a change, and what is fetched.**

| The portal now shows | Change recorded | Fetched |
| :---- | :---- | :---- |
| A principal act not in the last run's list | `new_act` | its file |
| A different file or a different as-at date for an act | `new_version` | the new file; its later amending acts and commencement orders; under `lom.subsidiary_acts`, its P.U. (A) instruments. Its timeline is read when `lom.timeline` asks |
| A status marker that changed, the same file | `status_changed` | nothing |
| Another document offered, or a new title, the same file | `listing_changed` | nothing |
| The same file and date as the last run, but no run stored the file (a failed or skipped fetch) | `not_stored` | the file. The 4 files that answered HTTP 500 on 2026-09-14 are caught this way; the 5 the engine logged as duplicates are not, since their bytes are stored under another URL |
| An act the last run listed, no longer listed (or an amending act) | `gone` | nothing |
| An amending act not in the last run's list | `new_amending_act` | its file, and the commencement order its remark cites, from its detail page (when `lom.timeline` reads it) or from the P.U. (B) list |
| A changed commencement remark or date | `commencement_changed` | nothing new, unless its detail page (when `lom.timeline` reads it) now lists an order that is not stored |
| A P.U. (A) published since the date less the look-back and not stored | `new_instrument` | when it is under an act `lom.subsidiary_acts` covers (core acts today) or a seed names it |
| A P.U. (B) published since the date less the look-back and not stored | `new_instrument` | only when an amending act whose detail page `lom.timeline` reads cites it (a commencement order), or a seed names it: the same rule as the full build |
| A stored file that answers 200, not 304, to a conditional HEAD (`--verify-stored N`) | `stored_file_changed` | the file again |

Every row of the delta list carries `contract_meta.update`: the change, its reasons, the date, the baseline run, how
the document was found, and the document the baseline stored for the same law (`doc_id`, URL, SHA-256, as-at date).
`discovery_path` is `delta` (`CONTRACT.md` 3.3), and an instrument taken from a P.U. list carries
`principal_link_source: portal_listing`. `laws.csv` lists every act (1,287 rows): "unchanged since <run>" (1,242 on
2026-09-14), the change, or "the portal offers no document" (45).

**What the check cannot see.** A file replaced behind the same path with the same as-at date. It happens: Act 869's
file was replaced on 21 August 2026 with its listing entry unchanged (section 1.3), and the check of 22:07 UTC
reported it "unchanged". `--verify-stored N` sends one conditional HEAD per stored file (the N newest), never
following a redirect; 304 means unchanged, 200 with other validators means changed and the file is fetched again.

**The look-back.** An instrument can be uploaded long after its publication date (P.U. (B) 196/2026: published
29 May 2026, uploaded 3 September), and the P.U. lists sort by publication date. So the check reads them back to
the date less `updates.subsidiary_lookback_days` (120) and lets the stored URLs remove what a run already holds.

**Settings** are the `updates:` block of `sources.yaml` (the P.U. list pages and endpoints, page size 500, the
look-back, page cap, `verify_stored`). The block is outside the link-file fingerprint, so changing it invalidates no list. The timeline
and subsidiary policies are the scraper's own (`lom.timeline`, `lom.subsidiary_acts`).

**The first check, 2026-09-14 22:07 UTC**, against the morning's crawl: 10 requests (the code then read the P.U.
pages for their key and had no look-back), every gap at least 3 s, and one change, P.U. (B) 335/2026 (a notice no
amending act cites, not fetched). Nothing to crawl. It is run `MY_ws_2026-09-14_to_2026-09-14` (section 3). The code was
revised after it (its run note says how); the 4 files that failed in the morning crawl would now be reported
`not_stored` and fetched.

**The second check, 2026-09-15 05:02 UTC**, against the first: 34 requests (the 8 of a plain check, plus the detail
pages of 7 changed or unstored acts and 6 amending acts under `timeline: all`), 300 changes, 10 documents to fetch,
6 stored and the 4 HTTP 500 files failed again. It is run `MY_ws_2026-09-14_to_2026-09-15` (section 3).

**The link list against the runs (`--list`, built 2026-09-15).** The listing diff cannot see documents the
listings never show: amendments known only from an act's timeline and the commencement orders on an amending
act's page. After a list rebuild, `--list links/documents.jsonl` compares the rebuilt list with every run
(`updates/listcheck.py`): a row no run stored goes on the delta list as `not_in_runs`; a row whose title a run
stored from another address (a seed fetched from an agency's copy) is `stored_elsewhere`, recorded only; a list
built from another registry is refused before any request. No request is sent for the comparison. First use
11:33 UTC: 98 `not_in_runs`, 75 stored (section 3).

**Merging runs into one corpus** is done by `tools/merge_corpus.py` (decision 17), never into a run: a new folder
`outputs/MY/MY_corpus_<date>` with the newest run's copy of each law, `superseded.jsonl` for the older copies, the
audit flags on the rows, and a validated manifest. The first is `MY_corpus_2026-09-15` (section 3). A reader of "the
current text of every act" reads that folder. Nine delta documents got a `doc_id` the 2026-09-14 run had given to
other documents (the engine's id map starts fresh per run); the corpus keeps the older run's ids and renames the
newer rows (`-002`, `-003`), recorded in its note.

## 3. Runs

Each run's folder holds its files and a `RUN_NOTE.md`: the run, its times, what is missing and the issues
(`outputs/README.md`, decision 15). The index is `outputs\MY\README.md`.

| Run | What | Result |
| :---- | :---- | :---- |
| `outputs\MY\MY_corpus_2026-09-15` | **The corpus:** the four crawls merged by `tools/merge_corpus.py` (decision 17); rebuilt 11:58 UTC | 1,391 documents, 18 older copies superseded, 9 doc_ids renamed, 178 rows with audit flags, 0 validation errors. What downstream reads |
| `outputs\MY\MY_ws_2026-09-15_to_2026-09-15` | Update check with the rebuilt link list (`--list`), 11:33 UTC (18 requests), then the crawl of its delta list | 393 changes, 98 to fetch: 75 stored (46 timeline-only amendments, 29 commencement orders), 23 failed on the portal's side. Audited: 27 scans |
| `outputs\MY\MY_ws_2026-09-14_to_2026-09-15` | Update check against the check below, 05:02 UTC 2026-09-15 (34 requests), then the crawl of its delta list | 300 changes, 10 to fetch: 6 stored (Act 885, Act 807 as at 1 January 2025, A1794 to A1796, P.U. (B) 200/2026), the 4 HTTP 500 files failed again. Audited: 0 flags |
| `outputs\MY\MY_ws_2026-09-14_to_2026-09-14` | Update check against the crawl below, 22:07 UTC | 1 change recorded (a P.U. (B) notice), nothing to fetch |
| `outputs\MY\MY_ws_2026-09-14` | Full crawl, scope `all`, from the link list of 07:04 UTC (built before the code review fixes) | 1,311 of 1,320 stored, 4 failed. Audited: 132 rows flagged (section 1.3). Read its "Read this first" |
| `outputs\MY\MY_ws_2026-09-13` | Test crawl, scope `seed` | 17 of 25 stored. Audited: 1 scan. Every document superseded in the corpus |

## 4. Output format against CONTRACT.md

Values are on the candidate, and so in `links/documents.jsonl` (`contract_meta` unless the column exists in
0.2.0). They are not in the manifest: the Round 1 engine drops them, and they join back on `source_url`.

| Column | Where it comes from | Example |
| :---- | :---- | :---- |
| `law_name_guess` | registry name for seeds (keeps `doc_id`s stable); the list's English title otherwise; "P.U. (A) N/YYYY under Act N" for subsidiary legislation; "Amendment of Act N (date)" for an amendment known only from a timeline | "Personal Data Protection Act 2010" |
| `law_number_guess`, `law_number`, `portal_id` | "Act " + the list's Act No.; `portal_id` is the bare number, A-number or P.U. number | `Act 709` / `709` |
| `document_kind` | the list or timeline the document came from, and decision 13 for plain-numbered acts listed as amendments | `principal_act`, `amending_act`, `commencement_instrument`, `subsidiary_legislation` |
| `principal_law_number`, `principal_link_source`, `amends`, `commences_law_number` | timeline project id, else title match; `portal_listing` on an instrument taken from a P.U. list by the update check. `amends` is filled only on plain-numbered acts recorded as amending acts under decision 13 (16 rows, 2026-09-14), with every act whose read timeline lists them; A-numbered amending acts carry only `principal_law_number`. `commences_law_number` is set on an order | Act 874: `Act 53`, `portal_timeline`, `[Act 53]` |
| `version_as_at`, `version_source` | the list's As At date for the document's own edition; `version_source` only with a date | `2023-07-01`, `portal_field` |
| `text_version`, `timeline_log_type`, `edition` | ORIGINAL → `as_enacted`, REPRINT and REPRINT ONLINE → `reprint`, others → `unknown`; without a matching timeline entry an online file → `reprint` and a printed file → null (463 of 823 principal rows); decision 13 acts → `as_enacted`; REVISED → `unknown` | `reprint`, `REPRINT`, `printed` |
| `language`, `language_source` | the download icon; null on timeline documents | `eng`, `portal_field` |
| `legal_status`, `status_source`, `in_force_status` | the status table in section 2.3; `in_force_status` holds the marker or remark as printed, on one line | `repealed`, `portal_listing`, "Repealed by Act 805" |
| `published_on`, `enacted_on`, `commenced_on`, `commencement_note`, `commencement_dates` | the amendment list or the timeline's ORIGINAL entry; `commencement_note` keeps the raw remark with its line breaks, `commencement_date` (0.2.0) holds it on one line | A1727: `2024-10-17`, `2024-10-09`, null |
| `commencement_instrument_refs`, `commencement_instruments_found`, `timeline_instruments` | P.U. (B) references in the remark and what the timelines list | A1727: `[P.U. (B) 522/2024]` |
| `linked_amendments`, `amendments_after_as_at`, `amendment_check_complete` | every amendment linked to a principal, including plain-numbered acts from its timeline | PDPA: `[A1727, after]` |
| `last_amending_instrument`, `last_amended_year` | the amendment whose latest date on or before the as-at date is latest, plain-numbered acts included (the draft definition, `CONTRACT.md` section 7) | Act 53: `Act 875`, `2025` |
| `seed_query` | the words the title rule matched (`CONTRACT.md` 3.2) | PDPA: `data` |
| `title_rule_groups`, `title_rule_tier`, `title_rule_exclusion` | the title rule | `G1_data_protection_privacy`, `core` |
| `seed_provenance` | the seed's `provenance` in `links/seed_laws.yaml` | `round1_registry`, `host_row:r1-my-053` |
| `discovery_path` | `seed`, `browse_listing`, `amendment_list`, `subsidiary_list`; `delta` on every row of a delta list (the original path is in `update.found_by`) | as listed |
| `crawl_flags` | only `CONTRACT.md` 3.3 values: `stale_vs_portal`, `secondary_copy` | PDPA: `stale_vs_portal` |

**Proposed for `CONTRACT.md` 3.3** (`review_flags`; counts from the list in `links/`, 2026-09-14):

| Flag | Meaning | Rows |
| :---- | :---- | ----: |
| `amendment_check_incomplete` | as-at date before the amendment list starts, or none, and no timeline read | 298 |
| `newer_version_in_other_language` | the other language's consolidation is newer (often a Malay translation under `/terjemahan/`) | 76 |
| `principal_unlinked` | an amending act or order with no principal found | 64 |
| `english_online_malay_printed` | English exists only online beside a printed Malay text (decision 14) | 19 |
| `listed_as_principal_by_portal` | a principal-list act recorded as an amending act (decision 13) | 16 |
| `seed_resolved_to_portal` | a seed naming P.U. N/YYYY, fetched as the portal copy on its act's timeline | 5 |
| `not_in_amendment_listing` | an amendment known only from a timeline | 4 |
| `preferred_language_unavailable` | no English text; Malay taken | 2 |
| `document_shared_with_other_act`, `seed_indicator_hints_dropped`, `listed_on_other_timeline` | as named; the last is a repealed act or repeal notice a timeline lists under AMENDMENTS, not reclassified (decision 13) | 1, 1, 1 |
| `commencement_instrument_unresolved`, `newest_document_belongs_to_other_act` | as named | 0, 0 |

## 5. Open choices for the developer

Decision 17 (2026-09-15) settled the first six rows below; they stay here with the answer so the reasoning is not lost.

| Choice | Settled | What was weighed |
| :---- | :---- | :---- |
| Subsidiary legislation (decision 12) | **Kept:** P.U. (A) under core acts; other acts' instruments recorded. Keep developing with regulations in | Timeline entries carry no title. The Customs Act alone lists 409 instruments and the Income Tax Act 172. Mapping them later is mapping's cost |
| Supply and Appropriation Acts | **As the portal lists them:** `amending_act`, `principal_unlinked` | By function they are principal acts: 37 Supply and Supplementary Supply Acts in the amendment list, plus A1678 (Consolidated Fund) and A1683 (Windfall Profit Levy validation, linked to Act 592). Not worth a rule |
| Finance Acts with savings or "special provision" sections | **As decision 13 has them:** amending acts unless AGC reprinted them | At least 17 have such sections |
| Files that are not the law's text (section 1.3) | **Flagged, not fixed:** `tools/audit_run.py`, flags on the corpus rows | Taking them from Round 1 would make the corpus unreproducible; reporting them to AGC is open to the developer |
| `timeline: all` | **Set,** the convention for every country; the list rebuilt with it on 2026-09-15 (section 2.3) | 798 listed principal acts had no timeline read under `rule`: no dates, and 298 documents without a full amendment check. `all` reads those detail pages at two paced hops each, about 1.8 hours once per list build |
| Round 1 corpus | **Hands off.** `MY_corpus_2026-09-15` is the new corpus; deleting `handoff1_v2` is the developer's call | P2 and P3 still read `handoff1_v2` by their defaults (`outputs/README.md` rule 5) |
| Carriers the title rule misses | crawled anyway at scope `all` | Tell extraction: six Public Prosecutor interception powers (MACC Act 694 s.43, Strategic Trade Act 708 s.37, Copyright Act 332 s.50B, Kidnapping Act 365 s.11, Dangerous Drugs Act 234 s.27A, Act 340 s.20); minimum retention periods in Acts 71, 139, 262, 381, 438, 723, 778 (kept in Malaysia), 795 and 861 |
| Reporting wrong files to AGC | not done | The 5 wrong texts, 7 Malay files and the 4 HTTP 500 addresses (`audit.md` of `MY_ws_2026-09-14`) are the list to send |

## 6. Known gaps

- Plain-numbered amending acts are linked only when a timeline listing them was read, and only while their current
  document is the text as enacted.
- 64 amending rows link to no principal.
- A remark's later dates can be phases rather than commencements (A1788), which errs toward fetching more.
- Commencement orders are found only on read timelines: the amending act's own or its principal's. On 2026-09-14
  all 17 came from amending acts' own timelines. Five amendment detail pages answered HTTP 200 without a readable
  timeline (A1759, A1539, A1730, A1756, A1586). Two of them cite an order that was not found, because their
  principals' read timelines (Acts 498 and 350) do not list it with a file: A1539 (P.U. (B) 547/2017) and A1586
  (P.U. (B) 62/2019). A1759, A1730 and A1756 cite only a date.
- The scraper takes the language from the portal's icon and does not look inside the file; the audit
  (`tools/audit_run.py`) catches the Malay files behind English links after the crawl (section 1.3), and the link
  list still records `eng` for them.
- The audit reads two pages: a P.U. (B) supplement that bundles several notices is flagged `parent_not_named` when
  the right notice is further in, and a wrong file whose first two pages carry no act number is not flagged.
- The engine gaps in section 2.5.
- **23 old gazette and P.U. files the portal does not serve** (HTTP 500 or no answer; `MY_ws_2026-09-15_to_2026-09-15`,
  `audit.md`), on top of the 4 act files failing since 2026-09-14. Every check reports them `not_stored` /
  `not_in_runs` and tries again.
- **27 timeline-only amendments are scans with no text layer** (old gazette supplements): OCR is extraction's work.
- The 2026-09-14 crawl ran on the scraper and link list from before the code review fixes. The run note, issue 1,
  lists what that changed in its manifest.

## 7. Round 1 corpus, against the portal

**Round 1 stored older texts than the portal lists as current.** Of 855 Round 1 rows numbered `Act N`, 834 match a
listed act that offers a document. Against the file the scraper chooses today:

| Result | Rows |
| :---- | ----: |
| Same URL | 559 |
| Same filename under a different path | 34 |
| **A different file** | **241** |
| … of which the portal's current version is as at 2020 or later | 143 |

| Act | Round 1 stored | Portal lists today |
| :---- | :---- | :---- |
| PDPA 2010 (709) | `Act 709 14 6 2016.pdf`, as at 15 June 2016 | `ACT 709-REPRINT 2023.pdf`, as at 1 July 2023 |
| Criminal Procedure Code (593) | `Draf 2-Act 593 CPC (17.5.2018).pdf`, as at 1 September 2017 | `Act 593 - Muktamad as at 4.7.23 …pdf`, as at 4 July 2023 |
| Income Tax Act 1967 (53) | `Pindaan Act 53 - 23 11 2017.pdf`, as at 1 October 2017 | `Act 53 (Online 2026).pdf`, as at 1 January 2026 |

Whether each different file was already listed when Round 1 crawled in July cannot be checked. The byte-level
comparison of the 2026-09-14 crawl with Round 1 is in its run note.

**Round 1 corpus findings that still stand** (audit re-check, corrected by the 2026-09-13 review):
- `in_force_status` is empty on all 869 rows. 71 rows carry a repeal signal: 59 a repeal notice in the text, 11 a
  filename marker only, 1 a "Repealed by" commencement remark.
- 13 files named "draft" or "draf" are official online reprints.
- 4 `doc_id` pairs end `-002`. Three are revised editions under a new number (783 replaces 13, 794 replaces 356, 796
  replaces 353). One is two different acts: Act 719, Finance Act 2011, titled "FINANCE ACT 2010" on its detail
  page.
- 23 stored acts are provably stale against amending laws in the same corpus.
- The two PDP Codes of Practice are stored only as landing pages.

## 8. Dead ends

- **Hand-built `act-detail.php` URLs:** "Invalid request", with or without cookies and Referer. 2026-09-13.
- **`federalgazette.agc.gov.my`:** does not resolve. Round 1 and 2026-09-13.
- **`www.pdp.gov.my`'s two PDPA pages:** no consolidated PDPA that includes A1727. 2026-09-13.
- **`Last-Modified` as a change signal:** 581 of 869 Round 1 sidecars carry the 2023-11-06 bulk-upload date.
- **Choosing a version by filename or upload order:** see section 7.
- **Python's `urllib.robotparser`:** matches groups on "Mozilla" and ignores wildcards. Replaced. 2026-09-13.
- **A "printed only" reading of official:** leaves 311 acts with no text (decision 14).

## 9. Evaluation only

These counts measure the gap. They are never a seed list (`POLICY.md` section 4).
- **Round 1 corpus:** of 98 Malaysian gold rows, 42 cite a law whose text is absent or stale (11 of the 26 in pillars
  6 and 7). Counting codes and guidelines as well, 68 of 98.
- **The title rule:** 17 of the 26 pillar 6 and 7 rows cite at least one of 7 distinct listed acts, and the rule
  (research v2) selects all 7. Of those 17, 12 cite only listed acts (with or without an amending act), and 5 also
  cite a code of practice or a standard. The other 9 rows cite only codes of practice, which no act-title rule
  reaches.

Re-measure on `outputs\MY\MY_ws_2026-09-14`.

## 10. Files, hand-back and evidence

| Path | What it is | Repo counterpart, under `stages\p1-scrape\` |
| :---- | :---- | :---- |
| `scraper/checker.py` | **New, 2026-09-16** (decision 19). The law table: reads this folder's own files and writes `law_table.csv` into a run or corpus, one row per law with its status and dates. No repo counterpart yet; hand back with the package as `adapters/my_gazette/checker.py` |
| `scraper/` | The scraper package (section 2.2), with `WORKFLOW.md`: how to run a full crawl step by step | `src/p1_scrape/adapters/my_gazette/` (a package that replaces `my_gazette.py`); `WORKFLOW.md` to `docs/` |
| `updates/` | The update check (section 2.6), a package: `__init__.py` (where the portal shows changes; `check`, `find_changes`), `baseline.py` (the last run), `listings.py` (the P.U. lists), `diff.py` (the comparison), `listcheck.py` (the link list against the runs, `--list`), `delta.py` (the delta list, `--verify-stored`), `__main__.py` (the command); with `WORKFLOW.md`: how to run a check step by step | `src/p1_scrape/adapters/my_gazette/updates/`, a subpackage; `WORKFLOW.md` to `docs/` |
| `sources.yaml` | The general part of the registry: destinations (lom root, list pages and endpoints, agency sites, whitelist), crawl settings, the title rule, search terms | joined with the next file into `instrument/sources_my.yaml` and `contracts/instrument/sources_my.yaml` |
| `links/seed_laws.yaml` | The 21 seed laws with their links, indicator tags and provenance. Hand-edited | joined after `sources.yaml` |
| `links/documents.jsonl`, `documents.csv`, `laws.csv`, `catalogue_meta.json`, `discovery_log.jsonl` | The generated link list (`links/README.md`) | not handed back as crawl input |
| `tests/test_my_lom.py`, `tests/test_my_catalogue.py`, `tests/test_my_updates.py` | 58, 67 and 41 offline tests (as pytest collects them), 166 passed on 2026-09-15; the workshop's `tools/test_tools.py` adds 17 for the audit and the corpus merge | `tests/` |
| `../../tools/audit_run.py`, `merge_corpus.py` | The audit and the corpus merge (decision 17), shared by every country; Malaysia's audit rules are in `RULES["MY"]` | `tools/` |
| `tests/fixtures/` | 13 pages and replies saved from the portal | `tests/fixtures/my/`, as in the sandbox. The tests also read `tests/fixtures/`, the generic destination `countries/README.md` names |
| `tests/test_my_selection.py` | **Removed here.** It tested the Round 1 picker. Delete the repo copy at hand-back | `tests/test_my_selection.py` |

**Hand-back, in one commit** (`countries/README.md`):
- Copy `scraper/*.py` to `adapters/my_gazette/`, including `__init__.py`, and delete `adapters/my_gazette.py`.
- Copy `updates/*.py` to `adapters/my_gazette/updates/`.
- Join `sources.yaml` and `links/seed_laws.yaml` into both registries.
- Copy the tests and fixtures, and delete `tests/test_my_selection.py`.
- Copy `tools/audit_run.py` and `tools/merge_corpus.py` to `tools/`, and `tools/test_tools.py` to `tests/`.
- Pin `cryptography==44.0.0` in `requirements.txt`.
- The interface task repoints `interface/dashboard.py:327` and `:532` to the package.
- The engine changes in section 2.5.

**Evidence behind this note:**
- **Live:** the portals examined by hand, 2026-09-13 and 2026-09-14: 37 logged requests in two logs (scratchpad
  `lom/log.jsonl` 29, `live/log.jsonl` 8), at least 6 s apart. One of them (19:39:57 UTC) also followed a redirect
  without a pause or a log line, so 38 HTTP requests (decision 9). The last 6 lines of `lom/log.jsonl` are the
  requests of 21:45 to 22:28 UTC below.
- **Link lists:** two live builds on 2026-09-14, 226 paced requests each, and one on 2026-09-15 with
  `timeline: all`, 1,970 paced requests (05:07 to 07:21 UTC), no document fetched.
  - The first (06:49 to 07:04 UTC) used the scraper from before the review fixes. The crawl used it, and it is kept
    in `outputs\MY\MY_ws_2026-09-14\links_used`.
  - The second (08:40 to 08:56 UTC) used the fixed scraper; it was the list in `links/` until the rebuild of
    2026-09-15 replaced it (section 2.3), and survives in `outputs\MY\MY_ws_2026-09-14\links_rebuilt`.
- **Runs:** section 3. The update check of 2026-09-14 22:07 UTC sent 10 paced requests, no document; the check of
  2026-09-15 05:02 UTC sent 34 and its crawl 10 document fetches (4 retried once through Playwright).
- **Audits:** `audit.json` in each run folder, 2026-09-15, from the first two pages of every stored file
  (`tools/audit_run.py`); the corpus `MY_corpus_2026-09-15` carries the flags per row.
- **By hand, 2026-09-14 21:45 to 22:28 UTC:** the home page, the P.U. (A) page, one P.U. (A) and one P.U. (B)
  listing POST, one conditional GET (21:47) and one conditional HEAD (22:28) on the stored PDPA file, both 304:
  6 requests at least 6 s apart, logged in scratchpad `lom/log.jsonl`.
- **Offline:** the scraper run over lists and pages saved live, behind a fake portal.
- **Round 1:** counts over the frozen corpus `pipeline-data\rdtii-p1-scrape\handoff1_v2`, from the audit of
  2026-09-13 as corrected by its re-check.
