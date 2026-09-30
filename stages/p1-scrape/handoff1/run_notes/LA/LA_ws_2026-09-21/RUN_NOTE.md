# Run note: LA_ws_2026-09-21

Lao PDR, web scraping, 21 September 2026. **The first crawl**: every file the Lao Official Gazette lists for
every kind of instrument, current and superseded, from the link list built the night before.

## Read this first

- **1,811 of 1,824 documents stored**, 3.70 GB, in five hours flat. `scrape.py --validate` reports **0 errors,
  0 warnings** against contract 0.2.0.
- **The portal never refused us.** 1,824 documents at 6 s with jitter, over five hours, and not one 403, 429 or
  503 — no rest was taken and the paced client never had to slow down. 6 s is **our own choice**: this host
  publishes no robots.txt and states no delay (`countries/la-lao-pdr/NOTES.md` 1.1).
- **Nearly every document is a scan, but not every one.** The engine classified **1,695 as scanned and 116 as
  native text** (6.4%). An earlier version of this note said the 116 include the pillar-6 and pillar-7 laws and
  that stage 2 could read them without OCR. **That was wrong, and backwards.** Every principal pillar law here
  — Electronic Transactions, Competition, Cyber Security, ICT, Bank of the Lao PDR — is `pdf_scanned`, and so
  are all 12 Lao seed documents. The 116 are 48 English translations, 19 repealed Lao texts and 49 Lao texts of
  mostly subsidiary instruments (`countries/la-lao-pdr/NOTES.md` 3.2).
- **13 documents were not stored, for three different reasons.** **4 were ours** — an HTML entity left in the
  address — and all 4 were fixed and recovered by the delta crawl `LA_ws_2026-09-21_to_2026-09-21_2`. **8 are
  links the portal does not serve**: every one answered HTTP 200 with the site's own page, because this host
  never 404s. **1 is a Word document** (LA-2120) that the portal does serve but `CONTRACT.md` has no
  `source_type` for, so it is correctly declined. Details below.
- **Four engine changes and one country defect were found.** The country defect is mine and is fixed; the
  engine changes live in a sandbox copy and are hand-back requests. The run was crawled with a scraper that has
  since been corrected in ways that change **metadata, not bytes** — see "The census this run read, and the one
  to read instead".

## At a glance

| | |
| :---- | :---- |
| Country | Lao PDR (`LA`) |
| Run type | First crawl, scope `all`, from `links_used/documents.jsonl` (built 2026-09-20 23:56 to 2026-09-21 00:24 UTC) |
| Date | 2026-09-21 (UTC date the run started) |
| Time, UTC | 00:27:41 to 05:27:52 (18,011 s — 5 h 0 min) |
| Time, machine clock | US Eastern Daylight Time, UTC−4: 20:27 on 20 September to 01:27 on 21 September |
| Result | 1,824 documents listed: **1,811 stored**, **13 failed**, 0 duplicates, 0 orphan files |
| Size | 3.70 GB (3,697,548,867 bytes in the manifest; 3.5 GB on disk) |
| Validation | `scrape.py --validate manifest.csv`: **1,811 rows, 0 errors, 0 warnings**, contract 0.2.0 |
| Audit | 1,811 read, 1,697 flagged, 13 missing. Rules: **generic only — there is no `RULES["LA"]`** |
| Law table | `law_table.csv`, from `links_rebuilt/`: 1,773 laws, **1,762 with a Lao text of their own** |
| Status | **Usable.** Read "The census this run read" before using `links_used/` for anything but provenance |
| Checked | `crawl_status.json`, `cost_report.json`, `manifest.jsonl`, `crawl_log.jsonl`, `audit.json`, `logs/crawl_stdout.log`, `links_used/catalogue_meta.json` |

## Steps and times

| Step | UTC | Requests | Output |
| :---- | :---- | :---- | :---- |
| 0. Three paced probes (settling legaltype 6 against 16, `old=1`, the size of the body) | 2026-09-20 23:22 to 23:40 | 63 to `laoofficialgazette.gov.la` | `countries/la-lao-pdr/NOTES.md` 1.2, 8; nine fixtures |
| 1. Link list, first attempt — **discarded** | 2026-09-20 23:28 to 23:54 | 188 | `links/build_discarded_2026-09-20.log`; `max_pages: 60` cut the Agreement listing at 600 of 657 |
| 1b. Link list, rebuilt | 2026-09-20 23:56 to 2026-09-21 00:24 | 194 | `links_used/` — 1,773 laws, 1,824 files |
| 2. Crawl | 2026-09-21 00:27:41 to 05:27:52 | 1,824 plans (see "more requests than plans") | `manifest.*`, `raw/`, `crawl_log.jsonl` |
| 3. Audit | 2026-09-21 05:29 | 0 | `audit.md`, `audit.json` |
| 4. Run note | 2026-09-21 05:35 | 0 | this file |
| 5. Update check | 2026-09-21 05:30 onwards | ~194 | its own run folder |

## How it was run

- **Engine:** a **sandbox copy** of `rdtii-rocky-finale/stages/p1-scrape` at `S:\p1-scrape`. The repo itself was
  not touched. Four changes were needed to make `LA` a real economy (`countries/la-lao-pdr/NOTES.md` 2.5).
- **Country scraper:** `countries/la-lao-pdr/scraper/`, sha256 per file in `links_used/catalogue_meta.json`.
- **Registry:** `countries/la-lao-pdr/sources.yaml` + `links/seed_laws.yaml`, joined into
  `contracts/instrument/sources_la.yaml`; fingerprint `d1d3973c…` in `links_used/catalogue_meta.json`.
- **Politeness:** `REQUEST_DELAY_MS=6000` plus jitter, one request at a time, one process against the host.
  No robots.txt exists to obey; 6 s is ours. `USER_AGENT` carried a contact address.
- **Commands:**

  ```
  # the list (rebuilt after the max_pages fault)
  REQUEST_DELAY_MS=6000 PYTHONPATH=src python -m p1_scrape.adapters.la_gazette.catalogue \
      --registry <ws>/countries/la-lao-pdr/sources.yaml \
      --seeds <ws>/countries/la-lao-pdr/links/seed_laws.yaml \
      --out <ws>/countries/la-lao-pdr/links

  # the crawl
  RUN=R:/outputs/LA/LA_ws_2026-09-21
  mkdir -p $RUN/logs && cp -r <ws>/countries/la-lao-pdr/links $RUN/links_used
  REQUEST_DELAY_MS=6000 GAZETTE_FRONTIER=links_file \
      GAZETTE_LINKS_FILE=$RUN/links_used/documents.jsonl \
      python scrape.py --economy LA --scope all --out $RUN

  # the checks
  python scrape.py --validate $RUN/manifest.csv
  PYTHONPATH=src python tools/audit_run.py $RUN
  ```

## What is in this folder

| Path | What it is |
| :---- | :---- |
| `RUN_NOTE.md` | This note |
| `manifest.csv`, `manifest.jsonl` | 1,811 rows, the Hand-off #1 shape (`CONTRACT.md`) |
| `crawl_log.jsonl` | One line per document attempted: 1,824 lines, 1,811 `ok`, 13 `failed` |
| `raw/` | `raw/la/<law_slug>/<stamp>__scanned.pdf` — the folder is the gazette's own record id, never the Lao title |
| `cost_report.json`, `crawl_status.json`, `.idmap.json` | The engine's counters, heartbeat and id map |
| `links_used/` | **The list the crawl read**, exactly as it read it. Never rewritten |
| `links_rebuilt/` | The same portal rows read again by the corrected scraper: same addresses, better metadata (below) |
| `audit.md`, `audit.json` | The content check of every stored file |
| `logs/crawl_stdout.log` | The console, 1,824 lines plus the health heartbeats |

## What is stored

| | Documents |
| :---- | ----: |
| **Stored** | **1,811** |
| Scanned PDFs (`pdf_scanned`) | 1,695 (93.6%) |
| Native-text PDFs (`pdf_native`) | 116 (6.4%) — of which only **49** are Lao texts of in-force instruments |
| Lao text | 1,758 |
| English translation | 53 |
| Total bytes | 3,697,548,867 (3.44 GiB) |

By kind, **as the list this run read classified them** — see the next section for why these are not the numbers
to quote: 352 principal acts, 1,242 subsidiary instruments, 41 amending acts, 176 other.

## The census this run read, and the one to read instead

`links_used/` is the list the crawl replayed, kept unchanged because that is what the convention asks of it
(`outputs/README.md` rule 1). It was built by a scraper that has since been corrected in three ways that change
**what a document is called, never which bytes were fetched**:

| Corrected | Effect on this run |
| :---- | :---- |
| `document_kind_of` tested "revised version" before "amending", so an amendment whose *target* is a revised law was filed as a principal act | 3 laws, including LA-2323, an in-force one-article amendment |
| The amending pattern matched the bare word ການປັບປຸງ, which ordinarily means *improvement* | 15 instruments that amend nothing were typed `amending_act`, stripped of their indicator tags and marked linkage |
| `agency_or_other` is not a value `CONTRACT.md` 3.3 defines | 176 rows carried it; the value is `other` |

The audit found the first of these independently: **5 of its 8 `short_principal` flags are exactly the amending
acts the corrected classifier now catches** — a 3-page instrument filed as a principal act is what that flag is
for.

So `links_rebuilt/` holds the same 1,773 laws read again, minutes after the crawl, by the corrected scraper.
`scraper/checker.py` prefers it, and the law table and the corpus are built from it. The addresses are the same,
so every manifest row still joins on `source_url`.

## What is missing, and why

**13 of 1,824 documents were not stored. Every one answered HTTP 200**, because this host serves its own web
page for any path that does not exist — a dead link here never returns 404 (`NOTES.md` 1.1). The engine
correctly refused to store a web page as a law.

| Cause | Count | Detail |
| :---- | ----: | :---- |
| **Ours: an HTML entity left in the address** | 4 | The listing writes `&#039;` for an apostrophe (`Women&#039;s_Union Law.pdf`) and `_unescape` resolved only `&amp;`, so we asked for a path containing the literal entity. **Fixed** (`html.unescape`); the update check re-queues all four. LA-446, LA-516, LA-1385, LA-1508 |
| The portal links a file it does not serve | 7 | LA-674, LA-698, LA-699, LA-735, LA-912, LA-1055, LA-1518. Six have spaces or Lao text in the filename; LA-674's address carries **zero-width spaces** (U+200B) between syllables, which is a mistyped link on the portal's side |
| The portal serves a **Word** file the contract cannot hold | 1 | LA-2120, `Decree on Blood Fund No 258GOV - 23082023.docx`. The portal returns it, twice, as `application/vnd.openxmlformats-officedocument.wordprocessingml.document` — a real Word document in the PDF column. `CONTRACT.md` 3.2 allows `source_type` of only `html`, `pdf_native` or `pdf_scanned`, so there is nowhere to record it and the engine correctly declines. **The Lao text of this law is held**; only the gazette's English rendering of it is not |
| An English translation the portal does not serve | 1 | LA-1818, `Eng 566 ລບ 2021.pdf`. The Lao text of the same law **is** stored |

Every one keeps its row in `links_used/laws.csv` and appears in `audit.md` under `fetch_failed`.

### Not collected, by the settings

Nothing was dropped by scope: the crawl ran at `all`. `legaltype=16` is not in the list because it is contained
in `legaltype=6` (`NOTES.md` 1.2), and `legaltype=4` is empty on the portal's own say-so.

### Missing details (metadata)

- **`law_number` is empty on every row.** This portal states no act number for any instrument, anywhere.
- **`version_as_at` is empty on every row.** The gazette publishes as made.
- **`principal_law_number` is empty on every row.** A Lao amending title names its target in words, with no
  number to join on. The law table makes that join on the words, under three tests, and says so.

## Stored, but not what the row says

From `audit.md`, with the **generic** rule set — `tools/audit_run.py` has no `RULES["LA"]`, and this session was
not permitted to edit that shared file (the rule set to add is written out in `NOTES.md` 2.5):

| Flag | Count | What it means here |
| :---- | ----: | :---- |
| `no_text_layer` | 1,697 | **Not a finding on this portal.** 93.7% of these documents are scans by design; this flag counts the corpus rather than finding anything. `RULES["LA"]` turns it into `scanned_as_expected` and adds `native_text` for the 116 that stage 2 can read directly |
| `short_principal` | 8 | A principal act of four pages or fewer. **5 of the 8 are the misfiled amendments** the corrected classifier now catches; the other 3 are genuinely short Presidential Ordinances |
| `fetch_failed` | 13 | The table above |
| `orphan_file` | 0 | No bytes on disk without a manifest row |
| `duplicate_content` | 0 | — |

**Four laws share a file with another law** and are not visible in this list of flags, because the link list
this run read predates the flag that marks them. `001.pdf`, `003.pdf`, `04.pdf` and `scan0001.pdf` are each
claimed by two unrelated laws — `003.pdf` by a 2023 Presidential Ordinance and a 2014 provincial Order, which
cannot both be right. The file is stored once as served; both laws keep their row; `links_rebuilt/` and
`law_table.csv` flag both sides. Flag, do not fix (decision 17).

## Issues encountered

1. **`max_pages: 60` silently truncated a listing, and the first link list was discarded.** The Agreement
   listing holds 657 laws — 66 pages — and the guard stopped at 60, so 57 agreements were missing while the
   build printed a confident summary and exited 0. Fixed three ways: the guard raised to 120, a listing cut
   short now **raises** instead of warning, and a listing whose stated total exceeds the guard says so before it
   starts reading. Two tests cover it. The list was rebuilt from scratch (194 requests) before the crawl, so
   **this run is unaffected** — it read the complete list.
2. **Four addresses were requested with an HTML entity in them** (above). Ours; fixed; re-queued by the update
   check.
3. **129 fetches escalated to the engine's second rung**, and an earlier version of this note read that fact
   exactly backwards. The claim was that the escalation set and the native-text set were the same 116
   documents. **They are not.** Cross-tabulating `retrieval_method` against `source_type` over all 1,811
   stored rows:

   | | `requests` | `playwright` |
   | :---- | ----: | ----: |
   | `pdf_scanned` | 1,586 | **109** |
   | `pdf_native` | **109** | 7 |

   Only **7** documents are in both sets. Two unrelated groups that both happen to number 116 were read as
   one. The escalations are overwhelmingly ordinary scans, and 109 of the 116 native-text PDFs came through
   the first rung like everything else. Counting the 13 failed fetches, which escalated too, `crawl_log.jsonl`
   carries **129** rows with `retrieval_method: playwright`, not 116.

   **What is still true, and is the point:** the portal received more requests than the counters report.
   `cost_report.json` gives `request_count: 1824`, which counts *plans*; each escalation is at least a second
   HTTP request, and `POLICY.md` 5.5 already records that a failed rung falls through to the next with no
   per-host wait. **What is not established is why.** It is not the filename encoding (1,101 non-ASCII
   addresses came through the first rung untouched) and it is not the native-text correlation. Left open in
   `NOTES.md` 5 — and whoever picks it up should start from the table above, not from the correlation this
   note previously asserted.

4. **`_with_backoff` labels every rung exception `playwright`**, whatever rung raised (`fetcher.py`). Nothing in
   this run was stored through that path, but it makes `retrieval_method` unreliable as evidence of what failed.
   A hand-back request.
5. **The engine's slug strips a non-Latin title to nothing.** `slugify` and `acronym_slug` returned `unknown`
   and `law` for every Lao title, which would have put the whole country in one folder under one id key. Fixed
   in the sandbox by honouring `Candidate.law_slug`, which had existed since v0.2.0 and which nothing read.
   Documents store under `raw/la/la_2537/` and doc_ids read `la-la2537-001`. `NOTES.md` 2.5 has the diff.

## Changes after the run

- **2026-09-21, after the crawl:** `links_rebuilt/` added — the same portal rows read again by the corrected
  scraper (above). `links_used/` is unchanged.
- **2026-09-21:** `audit.md`, `audit.json`, `law_table.csv` written.

## Decisions still open that affect this run

| Open | What it would change |
| :---- | :---- |
| **No detail page is read** (`NOTES.md` 2.3). The evidence says the law's own page carries less than the listing row, but `DECISIONS.md` has no Lao entry and decision 17 says every detail page is read | About 1,800 requests, and one field nothing downstream reads (ອອກໂດຍ, the issuing body) |
| **The title rule has never been read by anyone who reads Lao** (`NOTES.md` 5) | Nothing in this run: the crawl was `all`. It would change which 334 documents the `relevant` scope selects |
| `RULES["LA"]` is not in `tools/audit_run.py` | 1,697 of this run's 1,697 flags would become a count, and 116 documents would be marked as needing no OCR |
| Whether ສະບັບເກົ່າ ("old version") is rightly read as `repealed` | 293 laws. Decision 17 settles superseded as repealed, and `CONTRACT.md` has no `superseded` value, so it is read that way with the portal's own word kept beside it |
