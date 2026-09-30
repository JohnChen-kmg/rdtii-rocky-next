# Australia: the register and our scraper

The general note for Australia, in the layout `CONVENTIONS.md` section 4 fixes for every country. It holds the
findings of the Round 1 amendment audit of 2026-09-13 (every count re-checked the same day against the stored files
and the saved API responses) and, since 2026-09-15, the catalogue step built that day (decision 18). Counts are over
the frozen Round 1 corpus, `pipeline-data\rdtii-p1-scrape\handoff1_v2`, unless a line says "live" or names a build.

**Where Australia stands (2026-09-15):** the scraper is a package with the convention's catalogue step, run live at
12:14 UTC (1,277 documents listed) and again at 12:33 with the review-fixed code; the first crawl from that list
started at 12:33 UTC into `outputs/AU/AU_ws_2026-09-15/` (section 3). No audit rule set, no update check (a stub),
no corpus yet. `scraper/WORKFLOW.md` and `updates/WORKFLOW.md` say what runs today.

## 1. The website

### 1.1 The sites we use

| Portal | Host | robots.txt, read live 2026-09-13 and 2026-09-15 | Delay to use |
| :---- | :---- | :---- | :---- |
| Federal Register of Legislation | `www.legislation.gov.au` | `Crawl-delay: 10`, `Disallow: /assets/` | **10 s.** Round 1's limiter waited 3 to 4.5 s |
| Register OData API | `api.prod.legislation.gov.au` | none (HTTP 404) | The default 3 s plus jitter. A separate host from `www` |
| OAIC, ACSC, Home Affairs | the regulators named in `sources.yaml` | not read | Seed sources; the default until each host's robots.txt is read |
| APRA and the other seed hosts | named only in `links/seed_laws.yaml` (APRA at line 49) | not read | The same |

Two hosts, two delays: `www.legislation.gov.au` at 10 s, the API host at the default. The catalogue step reads the
API only; the crawl fetches every document from `www` (`REQUEST_DELAY_MS=10000`).

### 1.2 What the Federal Register looks like

**The API has the full point-in-time model** (live, 2026-09-13; the shapes saved 2026-09-15 in `tests/fixtures/`):
- **Title:** `id`, `name`, `collection` (`Act`, `LegislativeInstrument`, …), `subCollection`, `isPrincipal`,
  `isInForce`, `status` (`InForce`, `Ceased`, `Repealed`, `NeverEffective`), `makingDate`, `year`, `number`,
  `seriesType`, `hasCommencedUnincorporatedAmendments`, name and status histories.
- **Version:** `titleId`, `registerId` (the compilation id, `C2026C00227`; the title id itself for an as-made
  version), `start`, `end`, `isCurrent`, `isLatest`, `registeredAt`, `compilationNumber` (`0` for an as-made
  version), `status`, and `reasons`: the amendments the compilation incorporates, each with the amending title's
  id, name, year, number and provisions. The Privacy Act has 113 versions, two of them future.
- **Queries that work:** `titles?$filter=isInForce eq true and collection eq 'Act'&$top=100&$skip=N`, **with
  `$orderby=id`** (section 1.3); `versions?$filter=isLatest eq true and titleId in ('C…','C…')` with up to 18 ids;
  `versions?$filter=isLatest eq true and registeredAt ge 2026-09-01T00:00:00 and startswith(titleId,'C')` for the
  update check. On 2026-09-15 the in-force `Act` collection held 4,765 titles, 1,264 of them principal.

**Document addresses** (checked live on 2026-09-15, one request each):
- A compilation's dated PDF: `www.legislation.gov.au/<titleId>/<start>/<start>/text/original/pdf`, `start` being the
  version's start date (the Privacy Act's C2026C00227: HTTP 200, `application/pdf`, 1.9 MB). A multi-volume
  compilation has no single PDF: the same address answers **HTTP 405** (the Criminal Code).
- A compilation's dated epub: `…/<start>/<start>/text/original/epub`, every volume as spine documents (the Criminal
  Code: HTTP 200, `application/epub+zip`, 630 KB). The engine concatenates the spine (`p1_scrape.epub`).
- An as-made title's PDF: `www.legislation.gov.au/<titleId>/asmade/<start>/text/original/pdf`, the link its own
  downloads page gives (C2021A00098, F2025L00278). No epub is offered for an as-made title. The address without the
  date (`/asmade/text/original/pdf`) answers an HTML page, not a file.
- `/<id>/latest/downloads` shows compilation id, number, date, Act number, status and volumes; `/<id>/latest/authorises`
  lists the instruments made under an Act (the SOCI Act authorises 6 in force; the corpus holds 2); `/<id>/latest/text`
  is the viewer, which renders volume 1 only of a multi-volume act.

**Stored files carry the version:** on all 899 dated Round 1 rows the sidecar holds the dated URL and the
compilation id as the Content-Disposition filename (`C2026C00227.pdf`). PDF page 1 reads "Compilation No. 104,
Compilation date: 4 June 2026, Includes amendments: Act No. 75, 2025, Authorised Version C2026C00227": the
compilation date appears on 863 of 866 PDFs, an amendment statement on 846.

**Register IDs:** `C…A…` is an Act title, `C…C…` an Act compilation, `F…L…` a legislative instrument, `F…C…` its
compilation. The API also returns `C…G…` gazette notices and `C…Q…` titles (the Constitution is `C2004Q00685`), so a
`C` prefix does not mean an Act. **Act numbers** read `No. 119, 1988`.

**API query limits learnt live:** `titleId in (...)` with 18 IDs works, but an OR-chain of 18 returns 400 (read as
a node-count limit; the error body was not kept); datetime literals take no trailing `Z`; `/v1/affect` returns 404;
a third `$filter` term on `isPrincipal`, a filter on `hasCommencedUnincorporatedAmendments`, and `authorisedBy/any()`
all return 400.

### 1.3 What to watch for on this website

- **`$skip` pages overlap without `$orderby`.** The build of 12:05 UTC on 2026-09-15 saw 340 principal titles twice
  across 48 pages and missed about as many (940 distinct principal acts against 1,264 with `$orderby=id`). The
  catalogue orders every paged query and warns when a title comes back twice.
- **The register publishes late:** of the 73 versions newer than the corpus on 2026-09-13, 46 had started before the
  Round 1 crawl ran. A check by registration date, not by start date, catches them.
- **The first `No. N, YYYY` on a cover can be an amending Act's number:** on at least 35 of 1,256 rows (31 epubs,
  the SOCI and TOLA framed seeds, 2 PDFs). The API's `year` and `number` are the source now.
- **`isPrincipal` alone does not mean a principal Act:** 110 amendment-titled Acts in the corpus (19 from 2020 or
  later) are marked principal by the register. Read it together with the amending titles in `Version.reasons`.
- **The compilation start year and the "Includes amendments" year differ** on 209 of 866 rows (`last_amended_year`,
  `CONTRACT.md` section 7).
- **A title never compiled** has `compilationNumber 0` and `registerId` equal to its title id: 488 of the 1,264
  in-force principal acts on 2026-09-15 (`as_made_only`). Its document is the as-made PDF; the Round 1 date regex
  missed such titles and fell back to a framed capture of `/latest/text` (366 rows, 362 of them as-made). The repo's
  `docs/WORKFLOW.md` 104-106 wrongly attributes these fallbacks to multi-volume Acts: only 33 were.
- **`Ceased` and `NeverEffective`** map to `ceased` and `never_in_force`, values `CONTRACT.md` 3.3 does not have yet.
- **A comment in `links/seed_laws.yaml` (line 25)** calls TOLA's `C2021C00496` withdrawn. The API returns it as the
  live register id (compilation 1, start 2021-09-01).
- **Files that are not the law's text: checked since 2026-09-16.** `RULES["AU"]` in `tools/audit_run.py` checks
  the title and the number against the file, in both shapes: a compilation unpacked from the epub, which opens
  with the title, and an Act as made, which opens with the title, `No. N of YYYY` and `An Act to …`. HTML is not a
  fault here, because it is the form we chose. **On the corpus of 1,277 documents the rules flag 91:** 88 short
  as-made Acts that print their own number and are therefore whole, 2 Acts renamed since enactment, and 1 whose
  scan reads "No. 114 of ll73" so no number can be matched. Two things had to be handled: the register's older
  scans space letters and digits, so every number is read twice, once with the spaces removed; and the first
  number on a page is often the Act being amended, so a mismatch counts only when this Act's own number is absent
  from the page.
- **One title is too long for Windows.** The engine names each document's folder after the whole law name
  (`raw/au/<slug>/<stamp>__native.pdf.headers.json`); under the run folder's path, the "Families, Housing, Community
  Services and Indigenous Affairs and Other Legislation Amendment (…) Act" title (138 characters) pushes the
  sidecar past Windows' 260-character limit and the store fails after the bytes arrived (`FileNotFoundError` in the
  crawl log of 2026-09-15, 15:32 UTC; `store_failed` in the audit). A resume through drive `R:` (`subst R: <ws>`)
  fetches it; the engine should cap the folder name (2.5).

## 2. How our scraper works

### 2.1 The big picture

```
sources.yaml + links/seed_laws.yaml      the register and its API, three regulators; 20 seeds
        |
        |  step 1: build the link list   (scraper/catalogue.py: the API only; 121 requests, 9 minutes on 2026-09-15)
        |          robots.txt on both hosts; every in-force Act title; every principal act's latest version
        v
links/documents.jsonl    1,277 documents in crawl order, each with its dated address and details
links/laws.csv           4,765 titles, principal or not, with their latest version
        |
        |  step 2: crawl the list        (the Round 1 engine, REGISTER_FRONTIER=links_file, REQUEST_DELAY_MS=10000)
        |          every document from www at 10 s: epubs unpacked to HTML, PDFs, 5 framed captures
        v
outputs/AU/AU_ws_<date>/ manifest, raw files, crawl log
        |
        |  step 3: audit the files       (tools/audit_run.py, generic flags)
        |  step 4: write RUN_NOTE.md
        v
        |  step 5: update check          (updates/: a stub; the API query by registration date is known)
        |  step 6: merge the runs        (tools/merge_corpus.py)
        v
outputs/AU/AU_corpus_<date>/
```

| Step | Australia, 2026-09-15 | What is still needed |
| :---- | :---- | :---- |
| 1. Link list | **Built** (`scraper/catalogue.py`), run live twice | Repealed and ceased titles (`isInForce eq false`) are not harvested; instruments under the core acts (`/authorises`) are not listed (decision 12's rule: seeds only) |
| 2. Crawl | The first crawl from the list started 12:37 UTC (section 3) | Its result and note |
| 3. Audit | Generic flags | An `AU` rule set: the compilation statement on page 1 against the row's version |
| 4. Run note | The template | After the first crawl |
| 5. Update check | **A stub** (`updates/__init__.py`, section 2.6) | The check itself |
| 6. Corpus | `tools/merge_corpus.py` | A run to merge |

### 2.2 The code

| File in `scraper/` | What it does |
| :---- | :---- |
| `adapter.py` | `AuLegislationAdapter`, what the engine calls. `discover` reads the API (robots.txt on both hosts, the title harvest, the latest version of every principal act and every seed in batches of 18, the seeds' titles) and builds one candidate per document with its `contract_meta`; with `register.frontier: links_file` it replays a list instead. `build_plans` is Round 1's recipe: a dated PDF by `requests`; a dated epub by `requests` with `unpack: epub_html`, cited at its own dated address; a `/latest/text` address by a Playwright capture of the viewer's frame that rejects a multi-volume act; a regulator page rendered |
| `api.py` | The API's records (`Title`, `LatestVersion`, `Reason`), the queries (`titles_url` with `$orderby=id`, `versions_url` for a batch of ids, `versions_since_url` for the update check) and the document addresses (`pdf_url`, `epub_url`) |
| `catalogue.py` | Step 1: builds and writes the list (`documents.jsonl`, `documents.csv`, `laws.csv`, `catalogue_meta.json`, `discovery_log.jsonl`) and reads it back; `cfg_fingerprint` (seeds, `register:` settings, search terms) |
| `__init__.py` | Re-exports the adapter, `RegisterUnavailable`, and `_MULTIVOL_DECL` for Round 1's test |

The paced client and the robots.txt rules are imported from Malaysia's package (`..my_gazette.client`,
`..my_gazette.robots`): one request at a time, the larger of the delay and `Crawl-delay`, every request logged.
Round 1's `src/p1_scrape/epub.py` (the spine concatenation) stays in the repo, as do `tools/refetch_au_multivolume.py`,
`tools/audit_au_truncation.py`, `tools/verify_au_multivolume_acceptance.py` and the two 2026-07-17 documents.

### 2.3 What goes into the link list

Built 2026-09-15 at 12:14 UTC (121 API requests at 3.0 to 4.5 s, one `www` request for robots.txt, 9 minutes; the
list in `links/` is the rebuild that ended 12:33 with the review-fixed code, same figures):

- **1,264 principal acts** in force, one document each: 786 dated epubs (`document_form: epub`) and 483 as-made PDFs
  (titles never compiled, `as_made_only`), or a framed capture where a version is unknown (none on 2026-09-15).
  Every row carries `portal_id` (the title id), `law_number` (`No. N, YYYY` from the API), `version_as_at` (the
  version's start), `version_id` (the register id), `compilation_number`, `published_on` (`registeredAt`),
  `linked_amendments` (the `reasons`, 891 rows have some), `last_amending_instrument` and `last_amended_year`,
  `legal_status` (`in_force`), the PDF and epub addresses, `language: eng`.
- **The 20 seeds:** 10 Acts (among the 1,264), 3 amending acts (`isPrincipal false`, harvested but not principal:
  their compilations as epubs, `principal_unlinked`), 7 legislative instruments (F-series: 5 as-made ones with
  `form: html` as framed captures of `/latest/text`, Round 1's path; 2 compiled ones as epubs) and 3 regulator
  documents as they are.
- **Amending acts are recorded, not fetched:** the register compiles them into the principal act, and the version's
  `reasons` name them (decision 13's rule). `laws.csv` holds every harvested title, 3,501 of them non-principal.
- **Scopes:** `seed` 20, `relevant` 22 (the seeds plus the acts the title net selects), `all` 1,277.

### 2.4 Politeness

The API host at 3 s plus jitter (no robots.txt); `www.legislation.gov.au` at 10 s (`Crawl-delay`). The catalogue's
121 requests of 2026-09-15 were 3.0 to 4.5 s apart. The crawl runs through the engine's limiter, which has one delay
for every host: `REQUEST_DELAY_MS=10000`, and the links-file frontier warns when the engine's delay is below the
host's `Crawl-delay` (`POLICY.md` 5.5). Round 1's limiter waited 3 to 4.5 s before each `www` document and nothing
during discovery on either host.

### 2.5 What the engine must change

The same list as Malaysia's `NOTES.md` 2.5 (`POLICY.md` 5.5: robots.txt and `Crawl-delay` in the fetcher, a delay
per host, a wait before discovery requests, a language column, the link-file frontier read by the orchestrator, the
paced client moved from `adapters/my_gazette/` into the engine). Australia adds: keep the original epub bytes
beside the concatenated HTML (`transform: epub_spine_concat`, section 4), and `legal_status` values for `Ceased` and
`NeverEffective`. For every country: **cap the storage folder name** (`storage.py` `store()` slugifies the whole
law name; about 100 characters plus a short hash keeps every path under Windows' limit, 1.3), and **checkpoint on
every stored document** (the manifest is written every 10; a crawl killed in between leaves files no row names).

### 2.6 Updates: what changed since the last run

**Built and run 2026-09-16** (decision 21): `updates/` is a working package, and `updates/WORKFLOW.md` is the
procedure. The register makes this the cheapest check of the three countries.

- **Version identity is data, not a date to read.** Every version carries a `registerId` (a compilation id such as
  `C2026C00227`; the title id for an as-made version). A title whose id differs from the one the baseline's
  `laws.csv` recorded has a new text. Nothing is fetched to find that out.
- **One paged query per prefix:** `versions?$filter=isLatest eq true and registeredAt ge <since>T00:00:00 and
  startswith(titleId,'C')&$orderby=registeredAt`, then the same with `'F'`. **Query by registration date**, not by
  the version's start: the register lags, and 46 of the 73 new versions found on 2026-09-13 had started before
  Round 1's crawl ran. **Order every paged query**, or `$skip` pages overlap (1.3).
- **Scope matters more than the prefix.** The register registers hundreds of legislative instruments a month, and
  the harvest reads the Act collection plus the seeds (decision 12). A title is in scope when the baseline lists
  it, when it is a seed, or when it is an Act; the rest are counted by series and dropped. Without that rule the
  first live check queued 31 out-of-scope instruments.
- **Repeals and cessations** come free in the same pass, from `Title.status` (`InForce`, `Ceased`, `Repealed`,
  `NeverEffective`).
- **Cost, measured 2026-09-16:** 3 API requests plus 2 for `robots.txt` to check 4,772 titles, finding one
  changed law. A daily check is well within the register's tolerance.
- **Not covered:** new instruments made under an Act (`<titleId>/latest/authorises`, one `www` request per Act at
  10 s), a rectification that keeps the register id, and a title that stops being returned at all.

## 3. Runs

| Run | What | Result |
| :---- | :---- | :---- |
| `outputs\AU\AU_ws_2026-09-15` | The first crawl from the list of 12:33 UTC, scope `all` (1,277 rows), 12:33:16 to 17:00:06 UTC at `REQUEST_DELAY_MS=10000` (12.5 s per document), then a one-document resume through drive `R:` at 17:00 | **1,277 of 1,277 stored** (783 compilations as HTML from the epub, 481 as-made PDFs, the seeds' 13 documents), 0 failed, validation 0 errors. Audit: 89 short as-made Acts flagged (1 to 4 pages, 1908 to 1999), none a wrong file; 1 orphan file. The corpus `AU_corpus_2026-09-15` is this run. `RUN_NOTE.md` there |

| `outputs\AU\AU_ws_2026-09-15_to_2026-09-16` | **The first update check** (decision 21), 17:12 UTC on 2026-09-16, against `AU_ws_2026-09-15`: 3 API requests plus 2 for robots.txt, then the crawl of its delta list | 1 law changed and was fetched (the Water Act 2007, recompiled `C2026C00302` -> `C2026C00398`); 1 title checked and unchanged; 39 out-of-scope titles counted and dropped. Corpus rebuilt as `AU_corpus_2026-09-16` |

| `outputs\AU\AU_ws_2026-09-19` | The list rebuilt after the Commonwealth of Australia Constitution Act was seeded (22:27 to 22:37 UTC, 122 requests), then the two rows the rebuild added, crawled 22:38:59 to 22:39:14 UTC | 1,278 rows in the list (was 1,277); **2 documents stored, 0 flagged, 0 missing**: the Constitution, and the 2008 Social Security act whose as-made address the register moved with no change of version id. The Water Act's new compilation was already stored on 16 September. Corpus rebuilt as `AU_corpus_2026-09-19`, 1,278 documents |

The Round 1 crawl of July 2026 lives in the frozen corpus, which is hands off (decision 17) and is described in
section 7.

## 4. Output format against CONTRACT.md

| Contract column | Where it comes from on this portal | What Round 1 wrote | On the list of 2026-09-15 |
| :---- | :---- | :---- | :---- |
| `law_number` | API `year` and `number`, as `No. N, YYYY` | register title IDs on 1,248 rows, F-IDs on 7, `No. N, YYYY` from `links/seed_laws.yaml` on 4, empty on 9 | every register row |
| `portal_id` | The register title ID (`C2004A03712`) | in `law_number_guess` | every register row |
| `version_as_at` | API `Version.start`; offline, the sidecar URL date on 899 rows | not recorded | 1,274 rows |
| `version_id` | The version's register ID: the compilation ID (`C2026C00227`), or the title ID for an as-made version | not recorded | 1,274 rows |
| `last_amended_year` | **Definition open** (`CONTRACT.md` section 7); the list gives the latest year among the amending titles the compilation incorporates | not recorded | 891 rows |
| `last_amending_instrument` | API `Version.reasons`, "name (No. N, YYYY)" | not recorded | 891 rows |
| `legal_status` | API `Title.status`, raw value in `in_force_status`: `InForce` → `in_force`, `Repealed` → `repealed`, `Ceased` → `ceased`, `NeverEffective` → `never_in_force` | `InForce` on 1,254, empty on 14 | every register row |
| `document_kind` | `isPrincipal` and `collection`, read with the amending titles named in `Version.reasons` | not recorded | every row |
| `citation_url` | The document's own dated address (the epub's or the PDF's); `/latest/text` for a framed capture | 866 dated PDF URLs, 399 undated `/latest/text` | every row |
| `transform` | `epub_spine_concat` on every epub row | not recorded | 786 rows |
| `language` | `eng` | not recorded | every row |

## 5. Open choices for the developer

| Choice | Now | What to weigh |
| :---- | :---- | :---- |
| The document form (decision 18, proposed) | `register.document_form: epub`: every compilation as its dated epub, one form for single- and multi-volume acts | `pdf` gives single-volume acts as PDF and fails the multi-volume ones (HTTP 405; 33 in Round 1). Extraction's HTML lane parsed the 33 Round 1 epubs; its PDF splitter did badly on the 267-page SOCI PDF (the seed's own note) |
| Repealed and ceased titles | Not harvested (`isInForce eq true`) | Malaysia fetches its repealed acts' files. A second harvest (`isInForce eq false and collection eq 'Act'`) would list them; their count is unknown |
| Subsidiary legislation (decision 12's rule) | The 7 seeded instruments only | `/authorises` per core act at 10 s lists the instruments in force (the SOCI Act 6); the API's `LegislativeInstrument` collection is thousands |
| Audit rules | None (generic flags only) | The compilation statement on page 1 against the row's `version_as_at` and `version_id`; a framed capture's "This compilation is in N volumes" |
| The 5 as-made instruments with `form: html` | Framed captures of the viewer (Round 1's path) | Their as-made PDFs exist (`pdf_url` on the row); the framed capture depends on the viewer |
| `last_amended_year` | The latest year among the incorporated amending titles | `CONTRACT.md` section 7 |

## 6. Known gaps

- No update check (section 2.6), no audit rule set, no corpus; the first crawl's result is not yet known.
- Repealed and ceased titles, and instruments under the core acts, are not in the list (section 5).
- Amending acts are not documents of their own: none of the 7 amending Acts named in the seeded pillar 6 and 7
  Acts' latest versions is in the corpus as its own document; the list records them in `linked_amendments`.
- `inventory_au.csv` in the frozen corpus holds only the 20 seeds. A seed run overwrote the full harvest; an older
  one survives in `handoff1_old_v01`.
- 2 unreferenced files in `raw/au` of the frozen corpus: the TIA Act `20260718T0436Z__page.html` pair.

## 7. Round 1 corpus, against the portal

Hands off (decision 17); these counts describe it. 1,301 Australian rows: 1,268 current and 33 superseded.

| By fetch form (current rows) | Rows |
| :---- | ----: |
| Dated compilation PDF | 866 |
| Dated epub (multi-volume) | 33 |
| Framed `/latest/text` capture | 366 |
| Regulator documents | 3 |

- **By series:** 1,258 C-series titles (1,254 `InForce`), 7 F-series legislative instruments, 3 off the register.
  The list of 2026-09-15 holds 1,264 principal acts in force.
- **Amendment-titled rows:** 113. 110 are amending or consequential Acts (19 of them from 2020 or later) that the
  register itself marks principal. The other 3 are seeded amending Acts the register marks `isPrincipal: false`:
  Surveillance Legislation Amendment (Identify and Disrupt) Act 2021, Telecommunications Legislation Amendment
  (International Production Orders) Act 2021, and TOLA (Assistance and Access) Act 2018. Citing any of the three
  scores zero; the principal Acts they amend (the Surveillance Devices Act 2004, TIA Act 1979, Crimes Act 1914,
  ASIO Act and Telecommunications Act 1997, also the Customs Act 1901 and the Mutual Assistance in Criminal Matters
  Act 1987) are in the corpus; the Law Enforcement Integrity Commissioner Act 2006 is not.

**Currency, live 2026-09-13.** 8 of the 10 seeded register Acts matched the latest compilation. The ASIO Act (C83 to
C84), the TIA Act (C133 to C134) and the Surveillance Devices Act 2004 (C61 to C62) had been re-compiled from
27 August 2026. Corpus-wide, at least 73 of 1,265 register rows had a newer compilation (53 PDF, 20 epub); 46 of
those newer versions had started before the crawl ran.

## 8. Dead ends

- **URL comparison as a free change test.** The dated URL is known only after requesting each title's downloads
  page, about 3.5 h for 1,265 register titles at 10 s. The API registration-date query found the changes in 3
  requests; and since 2026-09-15 the API's `start` date builds the dated address without a downloads page.
- **Capturing a multi-volume Act from `/latest/text`.** The viewer renders only volume 1. Fixed in Round 1 by the
  dated epub.
- **`$skip` paging without `$orderby`** (section 1.3).
- **Guessing the as-made address** as `/asmade/text/original/pdf`: an HTML page comes back. The date is part of it.

## 9. Evaluation only

These counts measure the gap. They are never a seed list (`POLICY.md` section 4). Of 70 Australian gold rows (11
in pillars 6 and 7):
- None has stored text older than its own "last amended" date.
- 11 cite an absent legislative instrument (0 in pillars 6 and 7).
- 3 cite an amending Act the corpus holds only as its own document, the zero-score pattern (2 in pillars 6 and 7).
- 20 cite an Act re-compiled since the crawl (3 in pillars 6 and 7).

## 10. Files, hand-back and evidence

| Path | What it is | Repo counterpart, under `stages\p1-scrape\` |
| :---- | :---- | :---- |
| `scraper/checker.py` | **New, 2026-09-16** (decision 19). The law table: reads this folder's own files and writes `law_table.csv` into a run or corpus, one row per law with its status and dates. No repo counterpart yet; hand back with the package as `adapters/au_legislation/checker.py` |
| `scraper/` | The scraper package (section 2.2), with `WORKFLOW.md`: how to run a full crawl step by step | `src/p1_scrape/adapters/au_legislation/` (a package that replaces `au_legislation.py`); `WORKFLOW.md` to `docs/AU_CRAWL_WORKFLOW.md` |
| `updates/__init__.py`, `updates/WORKFLOW.md` | The stub: where the register shows changes (section 2.6), and how the check will run | none until developed |
| `sources.yaml` + `links/seed_laws.yaml` | The registry: the Round 1 portals and search terms, the `register:` block added 2026-09-15, and the 20 seeds (10 Acts, 7 legislative instruments, 3 regulator documents; a comment on TOLA's compilation id, line 25) | joined, `sources.yaml` first, into `instrument/sources_au.yaml` and `contracts/instrument/sources_au.yaml` |
| `links/documents.jsonl`, `documents.csv`, `laws.csv`, `catalogue_meta.json`, `discovery_log.jsonl`, `build.log` | The generated link list (`links/README.md`) | not handed back as crawl input |
| `tests/test_au_register.py`, `tests/test_au_multivolume.py`, `tests/fixtures/` | 10 tests on the saved API replies and downloads pages, and Round 1's 9 multi-volume tests (the epub citation assertion changed 2026-09-15) | `tests/`, `tests/fixtures/au/` |

**Evidence behind this note:** the Round 1 amendment audit of 2026-09-13 (live requests: robots.txt on both hosts,
the API title and version queries, the seeded Acts' downloads and authorises pages), the frozen corpus's manifest,
sidecars, PDFs and epub-derived HTML; the probes of 2026-09-15 (5 API requests, 2 robots.txt reads, 5 HEADs and 3
GETs on `www` at 10 s, logged in the session scratchpad `au/probe_log_2026-09-15.jsonl`; the replies in
`tests/fixtures/`); the three catalogue builds of 2026-09-15 (`links/discovery_log.jsonl`, `build.log`).
