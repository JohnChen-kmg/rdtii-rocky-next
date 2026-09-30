# Timor-Leste: the gazette and our scraper

The general note for this economy, in the layout `CONVENTIONS.md` section 4 fixes for every country. Dated
entries; a newer fact replaces an older one and says what it replaced.

**Where Timor-Leste stands (2026-09-20, evening):** the link list, the first crawl (1,935 documents), the audit,
the law table and the corpus all exist; the update check is built and has not run live. The portal was explored
on 2026-09-20
(`../\_finale-survey/explore-2026-09-20/tl-timor-leste.md`) and the scraper built the same day: the catalogue step
(`scraper/`), the update check (`updates/`), the law table (`scraper/checker.py`) and 29 offline tests. **No crawl
has run yet**, so there is no run folder, no audit and no corpus.

## 1. The website

### 1.1 The sites we use

| Portal | Host | robots.txt, read 2026-09-20 | Delay to use |
| :---- | :---- | :---- | :---- |
| Jornal da República (the official gazette, Ministério da Justiça) | `www.mj.gov.tl/jornal/` | HTTP 200, 2,189 bytes, Drupal's default file. **`Crawl-delay: 10`**. Disallows the Drupal machinery (`/admin/`, `/node/add/`, `/search/`, `/user/*`) and the `?q=` forms of the same. Nothing we read is disallowed | **10 s**, the delay it states |

The gazette's pages are proper UTF-8. There is no second host: the ANC (telecom regulator) and the government's
own site are listed in `sources.yaml` for provenance, and neither is read.

### 1.2 What the Jornal da República looks like

**Timor-Leste publishes law in a gazette and keeps no consolidated database.** Série I carries the acts; there is
no "as amended" text of anything, anywhere on the portal.

**Each kind of act has one page, and that page carries its whole history** — no paging, no search, no session.
Read 2026-09-20:

| Kind | Address | Acts parsed | Documents | Acts with no file |
| :---- | :---- | ----: | ----: | ----: |
| Leis do Parlamento Nacional | `/jornal/?q=node/12` | 285 | 232 | 3 |
| Decretos-Leis do Governo | `/jornal/?q=node/13` | 939 | 479 | 11 |
| Decretos do Presidente da República | `/jornal/?q=node/10` | 1,786 | 843 | 16 |
| Decretos do Governo | `/jornal/?q=node/18` | 253 | 195 | 4 |
| Resoluções do Parlamento Nacional | `/jornal/?q=node/19` | 594 | 376 | 2 |
| Resoluções do Governo | `/jornal/?q=node/20` | 931 | 524 | 13 |

**4,788 acts in six requests, resolving to 1,953 distinct documents**, 2002 to 2026 (the list of 2026-09-20). The
raw tables hold a few more rows than that — year headings, the header row and the filter row, which the parser
drops. **923 documents carry more than one act; one carries 39.**

**A row is four columns**, under a year heading:

```
NUMÉRO      | DESCRIÇÃO           | PUBLICADA EM | PDF
N.º 1/2026  | Lei da Concorrência | 25/3/2026    | PT -> public/docs/2026/serie_1/SERIE_I_NO_12.pdf
```

so every act's number, Portuguese title, publication date and document address come from the listing itself.

**The document is the gazette issue, not the act.** `SERIE_I_NO_12.pdf` (11 pages, 141 KB) carries Lei 1/2026 and
Decreto-Lei 13/2026; `SERIE_I_NO_13.pdf` carries Leis 3/2026 and 4/2026. Each issue opens with a `SUMÁRIO` naming
every act in it and the page it starts on:

```
SUMÁRIO
PARLAMENTO NACIONAL : Lei N.º 1/2026 de 25 de Março — Lei da Concorrência ............ 276
GOVERNO : Decreto-Lei N.° 13/2026 de 25 de Março — Medidas de Estabilização … ....... 284
```

**Nearly all the PDFs are native text**, in 2026 and in 2003 alike: 4,213 characters on page 1 of a 2026 issue,
913 on page 1 of a decree of 22 July 2003. **The full crawl of 2026-09-20 found 30 scans among 1,935 documents**
(1.6%), all of them older issues, so a little OCR is needed after all — against Laos, where every page is an
image.

**Amendments name their target in their own title** — "Primeira alteração ao Decreto-Lei n.º 75/2023, de 15 de
setembro" — so the link between an amending act and the act it alters is parsed from the listing, without opening
a document.

### 1.3 What to watch for on this website

- **One PDF holds several acts.** The manifest's unit is a document and the law's unit is a section of one, so
  `documents.jsonl` is shorter than `laws.csv` by design, and each document row names the acts it carries in
  `contract_meta.contains`. Stage 2 has to split on the `SUMÁRIO`.
- **No status, anywhere.** The portal never says whether an act is in force, amended or repealed. `legal_status`
  is `unknown` and the law table's `in_force` is `not stated` on every row — a reading of the portal, never an
  inference (`POLICY.md` 3.5).
- **No version date.** The gazette publishes as made. `version_as_at` is empty for every row.
- **Two Portuguese orthographies in one table.** The 1990 agreement was adopted part-way through the period, so
  `eletrónico` and `electrónico`, `proteção` and `protecção` both appear. Folding the accents is not enough: the
  older spelling carries an extra consonant, so the title rule writes both out (`PROTEC(C)?AO`, `ELE(C)?TRONIC`).
- **The number is written a dozen ways**: `N.º 1/2026`, `N.o 12 /2024`, `N. o 72 / 2023`, `No12/2019`, `N0 16/2017`,
  `4/2017`. Only the digits are kept.
- **File addresses vary**: `_A`, `_B`, `_C`, `_SUPLEMENTO_I`, `_NORMAL` suffixes, spaces inside filenames
  (`SERIE I N. 15A.pdf`), and a few rows with no link at all. An address is always taken from the row, never built.
- **Soft hyphens inside words** in the older PDFs (`impõe­se`), which extraction must normalise.
- **Unverified:** whether every year between 2004 and 2015 is native text (two of about twenty years sampled), and
  what the Tetum-language documents look like (one file, `9_2002_tet.pdf`, is named for Tetum).

### 1.4 Are the presidential decrees and resolutions law?

**Yes, and mostly not the kind that makes rules.** Recorded 2026-09-20 at the developer's request, from the titles
of all 4,788 listed acts — it decides what a later stage should read, and what it can safely skip.

| Kind | Acts | What the titles show they do |
| :---- | ----: | :---- |
| Decretos do Presidente da República | 1,786 | 712 honours or national mourning, 581 appointments and dismissals, 93 pardons: about 1,390 of 1,786 are **individual acts** |
| Resoluções do Parlamento Nacional | 594 | **83 ratify a treaty and 108 approve one**; 65 authorise presidential travel, 49 elections, 48 official trips |
| Resoluções do Governo | 931 | 102 approve, 101 appointments, 29 create a body, 26 donations |

**Two different questions, and they have different answers.**

- **Formally legal?** Yes. Each is an act of a constitutional organ, signed and published in **Série I**, the same
  series as the laws, and effective on publication. A pardon or an appointment is binding law for the person it
  names.
- **A source of regulatory obligations?** Almost never. Rules come from `Lei` and `Decreto-Lei` (primary law) and
  from `Decreto do Governo` and ministerial diplomas (subsidiary). That is why this adapter gives the first two
  `principal_act` and `subsidiary_legislation`, and these three `agency_or_other`.

**So they are collected, and they must not be dropped wholesale.** About **190 parliamentary resolutions ratify or
approve treaties**, and Timor-Leste has **no data-protection statute at all** (section 6): if a commitment on
electronic commerce, data flows or telecommunications binds this country, it may arrive only as a ratification.
Dropping the category to halve the crawl would lose exactly the instruments that could carry an indicator.

**What is worth building** is not a filter but a label: record *what each act does* — ratify, approve, appoint,
honour, pardon — so a later stage can skip 3,300 ceremonial documents in one pass instead of reading them, and so
the law table's `use` column can stop calling an appointment `evidence`. That is a parser change, not a crawl
change; the documents are already stored.

**The limit of this reading.** These counts come from titles, not from Timorese constitutional law. Whether a
presidential decree may itself carry a general norm, and whether a treaty approved but not yet ratified binds, are
questions for the instrument or a lawyer, not for this scraper.

## 2. How our scraper works

### 2.1 The big picture

```
sources.yaml + links/seed_laws.yaml
        |  1. LINK LIST   scraper/catalogue.py: robots.txt + six category pages = 7 requests, no document
        v
links/documents.jsonl (issues), laws.csv (acts)
        |  2. CRAWL       the shared engine replays the list at 10 s: 1,953 PDFs, about 5.5 hours
        v
outputs/TL/TL_ws_<date>/
        |  3. AUDIT  4. RUN NOTE  5. UPDATE CHECK (updates/, 7 requests)  6. CORPUS  7. LAW TABLE
```

| Step | Built? | Cost |
| :---- | :---- | :---- |
| 1. Link list | **Yes** (`scraper/catalogue.py`) | 7 requests, about a minute |
| 2. Crawl | **Done** (`TL_ws_2026-09-20`) | 1,935 of 1,953 stored in 8.5 h |
| 3. Audit | **Yes**, `RULES["TL"]` (the masthead, the SUMÁRIO, per-law extracts): 160 flags of 1,935 | 0 requests |
| 4. Run note | **Yes** (`RUN_NOTE.md`) | — |
| 5. Update check | **Yes** (`updates/`) | 7 requests |
| 6. Corpus | **Yes** (`TL_corpus_2026-09-20`, 1,921 documents) | 0 requests |
| 7. Law table | **Yes**, on the run and the corpus (4,788 rows with `--all`) | 0 requests |

### 2.2 The code

| File in `scraper/` | What it does |
| :---- | :---- |
| `parse.py` | The category pages: rows into acts (number, title, date, document), the six categories and their document kinds, `fold()` for the two orthographies, and the amendment link a title states |
| `adapter.py` | `TlJornalAdapter`: robots.txt, the six reads, the title rule, the seeds, and **one candidate per issue** with the acts it carries |
| `catalogue.py` | The link-list step and its five files; `laws.csv` is per act, `documents.jsonl` per issue |
| `checker.py` | The law table from a run or corpus, with `use` (decision 20) and the amendment linkage |
| `updates/` | The update check: `baseline.py`, `diff.py`, `query.py`, `delta.py`, `__main__.py` |

The paced client, the robots.txt reader and the link-list writer are **Malaysia's**, imported
(`..my_gazette.client`, `.robots`, `.catalogue`), as Singapore's and Australia's are.

### 2.3 What goes into the link list

- **One row per distinct issue**, in scope order (seed, then relevant, then the rest). `contract_meta` carries
  `portal_id` (our code, `L-1-2026`), `law_number`, `document_kind`, `published_on`, `principal_law_number` when
  the act amends another, `language: por`, `legal_status: unknown`, and **`contains`**, the codes of every act in
  that file, with `contains_titles` for the first twelve.
- **`review_flags`**: `several_acts_in_one_document`, `amends_another_act`, `law_number_unknown`.
- **`laws.csv` is the census**: every act on every category page, with the issue it appears in and why it is not
  crawled when it is not (`the portal lists this act with no document link`).

### 2.4 Politeness

`Crawl-delay: 10` from the portal's own robots.txt, adopted by the client at the first request; one request at a
time; the shared client rests and slows down if the portal ever refuses (decision 23). The list build sent 7 requests in 89 seconds on 2026-09-20. A crawl at 10 s takes about five and a half hours for 1,953 documents.

### 2.5 What the engine must change

Nothing specific to Timor-Leste yet. The general hand-back list is in Malaysia's `NOTES.md` 2.5.

### 2.6 Updates: what changed since the last run

**The gazette is append-only.** It publishes acts and never revises an issue, and it states no status. So the
check compares today's six pages with the last run's `laws.csv` and says: `new_act` (never listed before),
`not_stored` (listed, but no run holds its issue), `document_moved` (the portal now points an act at a different
file), `delisted` (the portal no longer lists it — reported, never fetched) or `unchanged`. **There is no
"amended" verdict**, because an amending act is a *new act* that names the one it alters.

Cost: **7 requests**, the same as the list build. `updates/WORKFLOW.md` is the procedure.

**Addresses are compared by `canonical_url()`, never as strings (fixed 2026-09-22).** The first live check reported 191 acts as moved: 188 differed only in scheme and host (`http://mj.gov.tl/…` against `https://www.mj.gov.tl/…`) and 3 were host-less links the parser now repairs, because the baseline was recorded before the parser canonicalised addresses. It asked for 66 documents, 50 of them already stored. `scraper/parse.py` now has `canonical_url()`, one key for one file, and `updates/diff.py` uses it for the act's previous and current document and for every stored-document lookup. Four tests in `tests/test_tl_updates.py` hold it. The corrected check asked for 16.

## 3. Runs

| Run | What | Result |
| :---- | :---- | :---- |
| `links/` (2026-09-20 05:56 to 05:58 UTC) | The link list: 7 requests, 89 seconds | 4,788 acts, 1,953 documents, all 9 seeds matched |
| `outputs\TL\TL_ws_2026-09-20` | **The first crawl**, scope `all`, 06:27 to 14:52 UTC at the portal's 10-second delay, with one resume | **1,935 of 1,953 stored**, 3.9 GB, covering 4,707 acts. No refusal from the portal. 160 audit flags; 18 not stored, 12 of them dead links on the portal. Three engine defects found (`RUN_NOTE.md`) |
| `outputs\TL\TL_corpus_2026-09-20` | The corpus, merged from that run | 1,921 documents, 14 superseded, validation OK. What downstream reads |
| `outputs\TL\TL_ws_2026-09-20_to_2026-09-22` | **The first live update check**, 2026-09-22, 7 requests | **Wrong, and superseded**: 191 acts reported as moved and 66 documents to fetch, 50 of them already stored — addresses compared as strings (2.6). Kept as the record; do not crawl its delta |
| `outputs\TL\TL_ws_2026-09-22_to_2026-09-22` | The update check, corrected, 2026-09-22, 7 requests | 4,759 unchanged, **29 acts in 16 issues not stored** — the first crawl's failures. The delta waits to be crawled |

## 4. Output format against CONTRACT.md

| Contract column | Where it comes from on this portal | On the list of 2026-09-20 |
| :---- | :---- | :---- |
| `law_name` | The listing's DESCRIÇÃO, in Portuguese | every act |
| `law_number` | The NUMÉRO column, digits only (`1/2026`) | nearly every act; `law_number_unknown` flags the rest |
| `portal_id` | Ours, from the category and the number: `L-1-2026`, `DL-12-2024` | every act |
| `version_as_at` | **Nothing**: the gazette publishes as made | empty everywhere |
| `published_on` | The PUBLICADA EM column, day-first, stored ISO | every act with a date |
| `last_amended`, `last_amending_instrument` | A later act's own title, which names what it alters | filled where an amendment exists |
| `legal_status` | **Nothing**: the portal states none | `unknown` everywhere |
| `document_kind` | The category page, and the title for amendments | every row |
| `principal_law_number` | The number an amending title names | every amending act |
| `citation_url` | The issue's address on the portal | every document |
| `language` | `por` | every row |
| Dates | Listing `25/3/2026` is day-first; stored ISO | every date |

## 5. Open choices for the developer

| Choice | Now | What to weigh |
| :---- | :---- | :---- |
| One PDF, several acts | One document row per issue, with `contains` naming the acts | The alternative is one row per act pointing at the same file: simpler for joining, but it stores or fetches the same PDF several times |
| Presidential decrees and resolutions | Collected, kind `agency_or_other`; the title rule's exclusions keep honours and appointments out of the relevant scope | **Do not drop the category** (1.4): about 190 parliamentary resolutions ratify or approve treaties, and for a country with no data-protection statute a treaty may be the only instrument touching an indicator. What is worth building is a `function` field so 3,300 ceremonial acts can be filtered without reading them |
| Tetum documents | Not distinguished | A handful of files are named `_tet`; the language rule would record `tet` if they are separate texts |
| The audit's `TL` rules | Not written | Generic flags only until they are |

## 6. Known gaps

- **The update check has not run live yet**; everything else in section 2.1 is done.
- **Timor-Leste has no comprehensive data-protection statute.** Searching all 4,788 listed acts for "dados
  pessoais" and "proteção/protecção de dados" returns nothing. The pillar 6 and 7 material is the electronic
  commerce and signatures regime (Decreto-Lei 12/2024), the telecommunications regime (Decreto-Lei 15/2012 and its
  2024 amendment, and Decreto-Lei 11/2003), the civil identification regime (Decreto-Lei 2/2004) and the ICT
  agency (Decreto-Lei 29/2017). **That absence is a finding for the instrument**, not a defect of this scraper.
- **No status and no consolidated text** (1.3): the law table can never say whether an act is in force.

## 7. Round 1 corpus, against the portal

Timor-Leste was not in Round 1. Nothing to compare.

## 8. Dead ends

Nothing yet.

## 9. Evaluation only

No gold set for Timor-Leste.

## 10. Files, hand-back and evidence

| Path | What it is | Repo counterpart, under `stages\p1-scrape\` |
| :---- | :---- | :---- |
| `scraper/` | The adapter package (`parse.py`, `adapter.py`, `catalogue.py`, `checker.py`) | `src/p1_scrape/adapters/tl_jornal/` |
| `scraper/WORKFLOW.md` | How to build the list and run a crawl | `docs/TL_CRAWL_WORKFLOW.md` |
| `updates/` | The update check | `src/p1_scrape/adapters/tl_jornal/updates/` |
| `updates/WORKFLOW.md` | How to run a check | `docs/TL_UPDATE_WORKFLOW.md` |
| `sources.yaml` + `links/seed_laws.yaml` | joined, `sources.yaml` first | `instrument/sources_tl.yaml` and `contracts/instrument/sources_tl.yaml` |
| `tests/` | 29 offline tests (20 + 9) and three fixtures | `tests/` |

**Evidence behind this note:** the exploration of 2026-09-20 (38 paced requests, logged in
`../_finale-survey/probe_log_2026-09-20.jsonl`), the three saved fixtures in `tests/fixtures/`, and the link list
in `links/` with its `discovery_log.jsonl`.
