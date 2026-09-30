# Lao PDR: the gazette and our scraper

The general note for this economy, in the layout `CONVENTIONS.md` section 4 fixes for every country. Dated
entries; a newer fact replaces an older one and says what it replaced.

**Where Lao PDR stands (2026-09-21):** every step of `CONVENTIONS.md` section 2 has been run. The link list,
the first crawl (**1,811 of 1,824 documents**), the audit, the law table, the corpus and **two live update
checks** all exist, and 60 offline tests cover the code. The portal was explored on 2026-09-20
(`../_finale-survey/explore-2026-09-20/la-lao-pdr.md`) and three paced probes the same day settled the
questions that exploration left open (section 8). Section 3 is the record of every run.

**The one thing to know before reading anything else:** **93.6% of the documents on this portal are scans** —
page images with no text layer, which nothing downstream can use without OCR. Counted on the whole crawl, not
sampled: **1,695 scans against 116 with native text (6.4%)**. The exploration read a single document, found an
image, and this note said "every document is a scan" until the crawl counted them. The minority with text
is **not** the pillar-6 and pillar-7 laws: every one of those — Electronic Transactions,
Competition, Cyber Security, ICT, the Bank of the Lao PDR — is a scan in its Lao text, and so are all 12 Lao
seed documents. Section 3.2 says what the 116 really are, and corrects an earlier version of this paragraph
that had it the wrong way round.

## 1. The website

### 1.1 The sites we use

| Portal | Host | robots.txt, read 2026-09-20 | Delay to use |
| :---- | :---- | :---- | :---- |
| Lao Official Gazette (ຈົດໝາຍເຫດທາງລັດຖະການ) | `laoofficialgazette.gov.la` | **There is no robots.txt.** The request answers **HTTP 200 with 137 KB of the site's own HTML** — the server's catch-all for any unknown path. Nothing is published, nothing is disallowed, and no delay is stated | **6 s plus jitter — our own choice**, not the host's (`POLICY.md` 5.1) |

**The 200 is the thing to be careful about, and it is recorded twice on purpose.** A client that reads "HTTP 200"
as "this file exists" would hand the site's own home page to a robots.txt parser and act on whatever it happened
to match. `adapter.py::_check_robots` therefore accepts the answer as a robots file **only when it looks like
one** — not HTML, and carrying at least one `User-agent`/`Disallow`/`Allow`/`Sitemap`/`Crawl-delay` line. It does
not, so the record in `catalogue_meta.json` says so in words: *"no robots.txt: the server answers 200 with its
own page for any unknown path, so nothing is stated and nothing is disallowed. The delay is our own choice."*
The same 200 also means **nothing on this host ever 404s**, so a wrong address looks like a successful fetch of a
web page. That is why no file address is ever constructed (1.3).

The saved answer is `tests/fixtures/la_robots_answer_2026-09-20.html`, kept as evidence.

There is no second host. The Ministry of Technology and Communications and the Bank of the Lao PDR are named in
`sources.yaml` for provenance, and neither is read.

### 1.2 What the Lao Official Gazette looks like

A PHP application (Yii). The 2013 Law on Making Legislation requires every law to be published here, which is what
makes the gazette the authoritative source rather than a convenience copy.

**Three address shapes matter, and only the first two are used:**

| What | Address | Used? |
| :---- | :---- | :---- |
| A listing by kind of instrument | `/index.php?r=site/list&legaltype=<n>&old=<0\|1>` | **Yes**, this is the whole crawl |
| The document | `/kcfinder/upload/files/<name>.pdf` | **Yes**, taken from the row, never built |
| A law's own page | `/index.php?r=site/display&id=<n>` | **No** (2.3) |

**A listing row is nine cells**, in this order, on all 182 rows of the Law listing read on 2026-09-20:

```
ຫົວຂໍ້ (title) | ພາກສ່ວນຮັບຜິດຊອບ (responsible ministry) | ວັນ-ເດືອນ-ປີ ນິຕິກໍາ (date of the instrument)
| ເຜີຍແຜ່ລົງຈົດໝາຍເຫດ (date gazetted) | ປະເພດນິຕິກໍາ (kind) | ສະຖານະພາບ (STATUS)
| ເນື້ອໃນ (the law's page) | PDF ອັງກິດ (English) | PDF ລາວ (Lao)
```

**A status word on every row is the rarest thing this portal gives us.** Malaysia states a status for 133 of
1,291 laws and Timor-Leste for none; here every row carries one. It is what makes the update check able to say
`status_changed` (2.6) and the law table able to answer `in_force` on every row (section 4).

**Two PDF columns, English before Lao.** Getting that order wrong would file every Lao law as a translation.
21 of the 182 laws had an English text; none had English without Lao.

**`legaltype` 6 and 16 are not two bodies of law. 16 is contained in 6.** The exploration left this open and a
crawl that guessed would have missed laws or counted them twice. Settled 2026-09-20 by reading **both listings in
full**, 19 pages and 18 pages, 38 requests:

| | Laws |
| :---- | ----: |
| `legaltype=6` | 182 |
| `legaltype=16` | 180 |
| In both | **180** |
| Only in 6 | **2** — ປະມວນກົດໝາຍແພ່ງ (Civil Code, id 1619) and ປະມວນກົດໝາຍອາຍາ (Penal Code, id 1402) |
| Only in 16 | **0** |

So **the link list uses `legaltype=6` and does not read 16**: it loses no law and saves 18 requests. `legaltype=6`
is the whole body of laws; `legaltype=16` is the same list with the two codes left out.

That answer creates a second problem and the adapter handles it: **the two codes also have listings of their
own** (`legaltype=1` and `legaltype=10`), so three listings carry the same two laws. Every law is kept **once**,
under the first listing that names it, and the row records the rest in `also_listed_under`. The listings are read
most-specific first, so the Civil Code keeps its own kind rather than the general ກົດໝາຍ.

**`old=0` and `old=1` are two halves of one body, and the amending laws are only in the second one.**
`old=0` lists only what the portal marks ປັດຈຸບັນ (current) — all 182 laws, with no exception. `old=1` lists
ສະບັບເກົ່າ ("old version"): the superseded texts **and** the instruments with titles like ກົດໝາຍ
ວ່າດ້ວຍການປັບປຸງບາງມາດຕາຂອງກົດໝາຍວ່າດ້ວຍນໍ້າ — "the Law on the amendment of certain articles of the Law on
Water". `CONVENTIONS.md` section 1 requires every amending instrument the portal lists, so **both are read**.
Turning `gazette.superseded` off would silently drop the entire amendment record of the country.

**What the portal lists, by kind** (each listing's own printed result count, read 2026-09-20):

| `legaltype` | Kind | `old=0` | `old=1` |
| ----: | :---- | ----: | ----: |
| 13 | ລັດຖະທໍາມະນູນ Constitution | 1 | 3 |
| 1 | ປະມວນກົດໝາຍ ແພ່ງ Civil Code | 1 | — |
| 10 | ປະມວນກົດໝາຍ ອາຍາ Penal Code | 1 | — |
| 6 | ກົດໝາຍ **Law** | **182** | **134** |
| 16 | ກົດໝາຍ Law (second listing) | 180 | *not read: contained in 6* |
| 9 | ລັດຖະບັນຍັດ Presidential Ordinance | 17 | 2 |
| 4 | ລັດຖະດໍາລັດ Presidential Decree | **0** | **0** |
| 3 | ດໍາລັດ Decree | 224 | 34 |
| 8 | ຄໍາສັ່ງ Order | 227 | 3 |
| 2 | ຂໍ້ຕົກລົງ Agreement | 657 | 106 |
| 5 | ຄໍາແນະນໍາ Instruction | 164 | 10 |
| 12 | ມະຕິຕົກລົງ Resolution | 8 | 1 |
| | **Total (16 excluded)** | **1,482** | **293** |

**`legaltype=4` is empty, and that is an answer.** The portal prints ບໍ່ມີຂໍ້ມູນ ("no data") instead of a table.
Reading that as a broken page would stop a build over a kind the portal simply has none of, so `results_total()`
returns `0` for it and `None` only when the page carries neither a result count nor the empty marker.

**Paging is ten rows at a time**, `&Document_page=<n>`, with the count printed on the page. **`Document_pageSize`
is ignored** by the server — asking for 50 still returns rows 11 to 20 — so a listing of 657 agreements costs 66
requests and there is no way to ask for fewer. That single fact is what makes both the link list and the update
check expensive here (2.4, 2.6).

### 1.3 What to watch for on this website

- **Nearly every PDF is a scan — but not every one.** The Cyber Security Law 2025 is 26 pages and 2.5 MB, and
  `pypdfium2` reads **zero characters** from it. Across the whole first crawl, 1,695 of 1,811 (93.6%) are the
  same: page images. **116 (6.4%) carry native text** — but **not** the laws that matter most: the Lao
  text of every principal pillar-6/7 law on this portal is a scan (3.2). Assume OCR, and let stage 2
  check each file rather than trust the assumption (3.2). The audit flags `no_text_layer` on every scan until
  `RULES["LA"]` lands (2.5), which is why that flag as it stands counts the corpus rather than finding anything.
- **Four pairs of unrelated laws point at the same file, and the stored bytes say which law each belongs to.**
  The uploads `001.pdf`, `003.pdf`, `04.pdf` and `scan0001.pdf` are each claimed by two laws years apart. The
  portal serves one upload per path, so at most one claimant is right — and the file's own dates settle it
  without another request:

  | File | `Last-Modified` / PDF creation | Claimants (gazette date) | Whose it is |
  | :---- | :---- | :---- | :---- |
  | `003.pdf` | 2024-01-02 | LA-2178 (**2024-01-02**), LA-1069 (2016-10-20) | LA-2178 |
  | `04.pdf` | 2025-04-09 | LA-2357 (**2025-04-09**), LA-1100 (2016-12-16) | LA-2357 |
  | `scan0001.pdf` | 2023-05-30 | LA-2070 (**2023-05-30**), LA-1160 (2017-04-28) | LA-2070 |
  | `001.pdf` | created 2013-12-24 | LA-466 (2014-01-07), LA-1070 (made 2014-01-22) | LA-466 — the file predates LA-1070's own instrument |

  So **four laws have no text at all**: LA-1069, LA-1100, LA-1160, LA-1070. The file is fetched once as served
  and **both claimants keep their row**, flagged `shared_file_address` and named in `shared_file_with`
  (decision 17: flag, do not fix). `checker.py` gives **both** claimants `use: linkage` rather than `evidence`,
  because a wrong attribution would hand a later stage a law scored against a different instrument, and the
  census alone cannot say which. **The table above is not applied automatically** — it is evidence for the
  developer to rule on, not a repair the scraper makes.

  This is why 1,769 Lao documents cover 1,773 laws, and why the honest coverage figure is **1,762 laws with a
  text of their own**, not 1,766.
- **Four file addresses carry an HTML entity**, `&#039;` for an apostrophe (`Women&#039;s_Union Law.pdf`).
  Requesting the entity as written asks for a path that does not exist — and on this portal that does not 404
  (1.1), so all four came back HTTP 200 with a web page and were recorded as failed fetches. `_unescape` now
  resolves every entity.
- **File addresses are inconsistent and must never be constructed.** In one folder: `88-25-6-2025_0001.pdf`,
  `83,25,6,2025_0001.pdf`, `86, 25,6,2025.pdf`, `/kcfinder/upload/files/ 69. 11.12.2024.pdf` (a **leading space
  inside the path**) and `ກົດໝາຍວ່າດ້ວຍ ການຟອກເງິນ…(ສະບັບປັບປຸງ)64.01.07.2024.pdf` (Lao letters and spaces).
  Both were fetched successfully on 2026-09-20 — `requests` percent-encodes them — but only because the address
  came from the page. Combined with the catch-all 200 (1.1), a constructed address would not fail: it would
  return a web page.
- **The /am/ vowel is written two ways in the same table**: 21 titles use ຳ (U+0EB3), 5 use ◌ໍ + າ (U+0ECD
  U+0EB2). The ligatures vary too (ຫ+ລ once against ຫຼ six times). `parse.fold()` settles both before anything is
  matched or stored. **NFC only — NFKC rewrites all 182 titles** and is not a spelling normalisation.
- **ສະບັບປັບປຸງ and ການປັບປຸງ…ມາດຕາ share a root and mean opposite things.** The first is "revised version", a
  consolidated text — 96 of the 182 laws are one. The second is "the amendment of articles", the amending
  instrument itself. `document_kind_of()` separates them, because `POLICY.md` 3.2 turns on it.
- **The portal states no version date.** It publishes as made. `version_as_at` is empty on every row.
- **The developer's caveat, recorded 2026-09-20: the English PDF may not be the latest version of the law.** The
  Lao text is the document of record, always. Each English file is collected with `language: eng`,
  `is_translation: true` and the flag `unofficial_translation`, and **its own dates are not assumed to match the
  Lao one** — the listing gives one pair of dates per law, so where an English file is older than the Lao text
  nothing on the page says so. Treat an English text as a reading aid, never as the citation.
- **Unverified:** whether `Document_pageSize` is honoured on any other view; whether the site's English interface
  (`?r=site/switchpage&lc=en`) changes what the listings carry; and whether the three status words in
  `parse.STATUS` beyond ປັດຈຸບັນ and ສະບັບເກົ່າ ever appear — none has been seen on a page
  (`status_word_not_recognised` is the flag if a fourth turns up).

## 2. How our scraper works

### 2.1 The big picture

```
sources.yaml + links/seed_laws.yaml
        |  1. LINK LIST   scraper/catalogue.py: robots.txt + every listing page, old=0 and old=1.
        |                 About 190 requests, no document, no detail page
        v
links/documents.jsonl (one row per file), laws.csv (one row per law)
        |  2. CRAWL       the shared engine replays the list at 6 s
        v
outputs/LA/LA_ws_<date>/
        |  3. AUDIT  4. RUN NOTE  5. UPDATE CHECK (updates/)  6. CORPUS  7. LAW TABLE
```

| Step | Built? | Cost |
| :---- | :---- | :---- |
| 1. Link list | **Yes** (`scraper/catalogue.py`) | about 190 requests, 25 minutes |
| 2. Crawl | see section 3 | 6 s a document plus the download of a 2.7 MB scan |
| 3. Audit | Generic flags only: **there is no `RULES["LA"]` yet** (2.5) | 0 requests |
| 4. Run note | see section 3 | — |
| 5. Update check | **Yes** (`updates/`) | about 190 requests, or about 25 with `--pages 2` |
| 6. Corpus | `tools/merge_corpus.py` needs no change: it is already generic | 0 requests |
| 7. Law table | **Yes** (`scraper/checker.py`) | 0 requests |

### 2.2 The code

| File in `scraper/` | What it does |
| :---- | :---- |
| `parse.py` | The listings: rows into laws (title, ministry, both dates, status, the two PDF columns), the twelve kinds with their document kinds and the `subset_of` that keeps 16 out, `fold()` for the two spellings, `document_kind_of()` for revised-against-amending, and the law page reader that proves it is not needed |
| `adapter.py` | `LaGazetteAdapter`: the robots record, every listing page at `old=0` and `old=1`, one law kept once across listings, the title rule, the seeds, and **one candidate per file** with `law_slug` set to the gazette's record id |
| `catalogue.py` | The link-list step and its five files; `laws.csv` is per law, `documents.jsonl` per file |
| `checker.py` | The law table from a run or corpus, with `use` (decision 20) and the weak amendment linkage |
| `updates/` | The update check: `baseline.py`, `diff.py`, `query.py`, `delta.py`, `__main__.py` |

The paced client, the robots.txt reader, the title-rule matcher and the link-list writer are **Malaysia's**,
imported (`..my_gazette.client`, `.robots`, `.relevance`, `.catalogue`), as Singapore's, Australia's and
Timor-Leste's are.

### 2.3 What goes into the link list

- **One row per file**, in scope order (seed, then relevant, then the rest). A law with an English translation
  contributes **two** rows, one per language, with the same `portal_id` and different `law_slug`
  (`la-2537` and `la-2537-en`).
- `contract_meta` carries `portal_id` (`LA-2537`), `document_kind`, `published_on` (gazetted), `made_on`,
  `legal_status` with the portal's own `status_word`, `language` and `is_translation`, `is_revised_version`,
  `legal_type`/`legal_type_label`, `listing` (`legaltype=6&old=1`), `also_listed_under`, `agency` and
  `detail_url`. `law_number` and `principal_law_number` are **null everywhere**: this portal states no act number
  for any instrument (section 4).
- **`review_flags`**: `unofficial_translation`, `superseded_listing`, `listed_under_several_kinds`,
  `shared_file_address`, `no_instrument_date`, `status_word_not_recognised`.
- **`laws.csv` is the census**: every law every listing names, once, with both of its files and why a law has none.

**No detail page is read. That is a departure from `CONVENTIONS.md` rule 5, recorded here with its evidence —
and it is not yet a decision.** `DECISIONS.md` carries 23 decisions, none about Lao PDR, and decision 17, which
rule 5 rests on, says "the detail page of every law is read when the link list is built" and stands unamended.
So this is a proposal with the measurements behind it, not settled practice, and section 5 lists it as needing
the developer's ruling. The measurement, on law id 2597, 2026-09-20:

| | The listing row | The law's own page |
| :---- | :---- | :---- |
| Title, kind, ministry, instrument date, gazette date | all present | all present, identical |
| **Status** | ປັດຈຸບັນ | **absent — there is no status on the detail page** |
| Files offered | **two columns**, English and Lao | **one** download link |
| Issuing body (ອອກໂດຍ) | no column | ສະພາແຫ່ງຊາດ |

So the detail page carries **less** than the listing, except for one field nothing downstream reads. The reader
for it is kept in `parse.py` and tested against the saved page, because that claim is only worth making if the
code that would read the page exists and agrees.

### 2.4 Politeness

**6 s plus jitter, our own choice**, because the portal publishes no robots.txt and states no delay (1.1). One
request at a time, one process at a time against the host, and a list build and a crawl never overlap. The shared
paced client rests 1, 5 then 30 minutes and halves its speed if the portal ever refuses us, and stops only after
six refusals in a row (decision 23). **The User-Agent is never changed to get past a block**, and it carries a
contact address.

The portal did not refuse a single request on 2026-09-20 — not during the 63 probe requests, not during the link
list build (section 3).

### 2.5 What the engine must change

**Four changes, all made in a sandbox copy of `stages/p1-scrape`; the repo is untouched.** Each is a hand-back
request. The first three are the ones Timor-Leste predicted; the fourth is new, and it is the one that would have
quietly ruined the corpus.

| # | What happens without it | Where | The fix used here |
| ----: | :---- | :---- | :---- |
| 1 | `WARN unrecognized economy 'LA' — skipping; nothing to crawl.` | `economies.py` | `LA` (and `TL`) added to `_NAME_TO_CODE` and `VALID_CODES`. The repo fix is `PLAN.md` 1A-2/1A-3: read the codes from the YAML headers |
| 2 | `NotImplementedError: adapter for LA not supported` | `adapters/registry.py` | `LA -> LaGazetteAdapter` |
| 3 | `economy: 'LA' is not one of ['SG','AU','MY']` and `doc_id … does not match '^(sg\|au\|my)-…'` at validation | `contracts/schemas/manifest.schema.json` | `economy` widened to `^[A-Z]{2}$`, `doc_id` to `^[a-z]{2}-[a-z0-9]+-\d{3}$` — exactly what `CONTRACT.md` proposes for 0.3.0. Verified against a real LA row |
| 4 | **Every Lao law stores in `raw/la/unknown/` under doc_id `la-law-NNN`** | `utils.py`, `dedup.py`, `orchestrator.py` | below |

**Change 4 is the important one.** `utils.slugify()` is `re.sub(r"[^a-z0-9]+", "_", name.lower())`, and **every
Lao character is outside `[a-z0-9]`**. So `slugify("ກົດໝາຍວ່າດ້ວຍ ຄວາມປອດໄພໄຊເບີ")` returns `"unknown"` and
`acronym_slug()` of the same title returns `"law"` — for **every law in the country**. The storage folder is the
slug and the doc_id key is the acronym, so the whole corpus would land in one folder, and `dedup` would treat
1,800 unrelated laws as versions of a single one, disambiguated only by a 4-character hash with a birthday
collision expected well before the crawl ended. Timor-Leste's path-length failure lost 254 files and was visible;
this one would have produced a complete-looking crawl that was wrong.

`Candidate.law_slug` has existed since v0.2.0 for exactly this and **nothing ever read it**. The sandbox fix:

- `orchestrator.py`: the storage folder and the doc_id key come from `cand.law_slug` when the adapter set one,
  and from the title when it did not — so nothing changes for Singapore, Malaysia or Australia.
- `dedup.py`: `_slug_key`, `is_retrieved` and `stable_id` take an optional `slug`, compacted with
  `law_slug_compact` rather than turned into an acronym (`acronym_slug("la-2537")` is `"l"`).
- `utils.py`: `slugify` is capped at **80 characters plus the title's hash** — Timor-Leste's fix, kept — and
  falls back to a hash when nothing survives; `acronym_slug` does the same when a title has no Latin letters.
  Any future economy in Chinese, Russian or Lao gets a working slug without an adapter change.

A Lao law now stores at `raw/la/la_2537/<stamp>__scanned.pdf` with doc_id `la-la2537-001`, and a law that has a
translation keeps it beside the Lao text — `raw/la/la_1402_en/…`, doc_id `la-la1402en-001`. **The folder uses an
underscore and the doc_id does not**: `slugify` replaces every run of non-alphanumerics, so the `law_slug`
`la-2537` becomes the folder `la_2537`, while `law_slug_compact` strips them for the id. Both are checked
against the crawl of 2026-09-21, not inferred.

**A fifth, found while testing and not fixed:** a link list whose fingerprint does not match the registry makes
the engine print `[crawl] SKIP LA: ValueError: … built from a different registry` and **carry on to exit 0 with
an empty manifest** (`orchestrator.py:234`, the per-economy `except`). `POLICY.md` 5.6 says a run that selects
zero laws must fail loudly and never exit 0. The guard itself is right and did its job; the exit code is wrong.
Until it is fixed, read the first minute of the crawl log for `SKIP LA`.

**`tools/merge_corpus.py` needs no change**: its run-folder pattern is already `[A-Z]{2}` and it already caps
folder names.

### 2.6 Updates: what changed since the last run

**This check can see something none of the others can.** Every listing row carries a status word, so a law that
has been superseded is visible in the listing itself — no document opened, no timeline read. The verdicts are
`new_law`, **`status_changed`** (ປັດຈຸບັນ → ສະບັບເກົ່າ), `not_stored`, `document_moved`, `translation_added`,
`delisted` (reported, never fetched) and `unchanged`.

**There is no `amended` verdict, and that is right.** The gazette publishes as made and never edits a document.
An amendment arrives either as its own instrument (a `new_law` whose `document_kind` is `amending_act`) or as a
whole revised text, which is a `new_law` of its own and pushes the text it replaces into the `old=1` listing —
where the same check reads it as `status_changed`.

**It is also the dearest check in the workshop**, because `Document_pageSize` is ignored (1.2): a full check
re-reads every page, about 190 requests and 25 minutes. `--pages N` buys a shallow check for about 25 requests —
the gazette lists newest first, so everything recently published is in the first pages — and it is honest about
what it gives up: it cannot see a status word that changed further down a listing, and it **never reports
`delisted`**, because a law it did not read is not a law the portal dropped.

`updates/WORKFLOW.md` is the procedure. **Run live twice on 2026-09-21**, 193 requests each (section 3.1).

## 3. Runs

### 3.1 What has been run

| Run | What | Result |
| :---- | :---- | :---- |
| `links/` (2026-09-20 23:28 to 23:54) | The link list, **first attempt** — discarded | `max_pages: 60` cut the Agreement listing at 600 of 657. 188 requests. Kept as `links/build_discarded_2026-09-20.log` (section 8) |
| `links/` (2026-09-20 23:56 to 2026-09-21 00:24) | The link list the crawl read: 194 requests, 28 minutes | 1,773 laws, 1,824 files (1,769 Lao, 55 English). No warning |
| `outputs\LA\LA_ws_2026-09-21` | **The first crawl**, scope `all`, 00:27:41 to 05:27:52 UTC at 6 s | **1,811 of 1,824 stored**, 3.70 GB, validation 0 errors. No refusal of any kind in five hours. 13 not stored: 4 our own entity bug (recovered by `_2`), 8 links the portal does not serve, 1 Word file the contract cannot hold. 1,697 audit flags, of which 1,697 are `no_text_layer` — the normal state here |
| `outputs\LA\LA_ws_2026-09-21_to_2026-09-21` | **The first update check**, 193 requests, no crawl | Reported 46 `document_moved`; **42 were false**, from a whitespace defect in our own census (its `RUN_NOTE.md`). Kept as the record of the listing that day; superseded by `_2` |
| `links/` (2026-09-21 06:00 to 06:28) | The link list **rebuilt** after the census and classifier fixes: 193 requests | The same 1,773 laws and 1,824 files, with `amending_act` down from 41 to 26, one `repealing_act`, `other` in place of `agency_or_other`, and no address flattened. Installed into the crawl's folder as `links_rebuilt/` |
| `outputs\LA\LA_ws_2026-09-21_to_2026-09-21_2` | The check re-run against the corrected census (193 requests), **with its delta crawl** (13) | 1,760 `unchanged`, 13 `not_stored`, **0 `document_moved`** — the 42 false moves are gone. **4 of the 13 recovered**, all four addresses we had mis-parsed; the other 9 returned the portal's catch-all a second time and are its dead links, confirmed rather than assumed |
| `outputs\LA\LA_corpus_2026-09-21` | The corpus, merged from both runs | 1,762 documents, validation OK. **It holds no English translation**: `tools/merge_corpus.py` keys a document on `(portal_id, document_kind)` and not on language, so all 53 are filed as superseded copies of their own Lao law. Nothing is lost on disk; the one-line fix is shared-file edit 6 |

**The law table**, on the corpus: 1,773 laws. `use` comes out `evidence` 1,448, **`evidence, text stale` 4**,
`linkage` 307, `linkage, text needed` 7, `not held` 7; `in_force` **yes 1,480, no (repealed) 293 — and "not
stated" for none of them**, which no other country in this workshop can say.

**How many laws do we actually hold the text of? 1,762 of 1,773.** The arithmetic, which is worth spelling out
because three different numbers are defensible and only one is honest:

| | Laws |
| ----: | :---- |
| 1,773 | the portal lists |
| −7 | the gazette links a file it does not serve (8 addresses, one of which is an English translation whose Lao text we do hold) |
| = 1,766 | have a file stored at their address |
| −4 | share that file with another law, and the file's own dates say it belongs to the other one (1.3) |
| **= 1,762** | **have a text of their own** |

The seven with nothing are two repealed instruments and five in force — an Instruction, two ministerial Orders
on animal disease, and two Instructions on foreign nationals and on social security. Each keeps its row with
its dates and its status, so the gap is visible rather than absent
(`outputs/LA/LA_ws_2026-09-21_to_2026-09-21_2/RUN_NOTE.md` names them).

### 3.2 What stage 2 will receive

Recorded here because the developer asked for it in this section, and because it is the one thing about this
country that changes another stage's plan.

**1,815 PDFs across two runs, 3.70 GB, of which 93.6% are page images with no text layer and 6.4% are native
text.** The second number was not predicted — the exploration read one document, found an image, and this note
said "every document is a scan" until the crawl counted them — but it is easy to read the wrong way, and an
earlier version of this section did. **The native-text minority is not the laws stage 2 most wants.**

The 116 native-text documents of the first crawl break down like this:

| What they are | Documents |
| :---- | ----: |
| English translations of laws still listed as current | 32 |
| English translations from the superseded listing | 16 |
| Lao texts of **in-force** instruments | **49** |
| Lao texts from the superseded listing (repealed) | 19 |

So **49 of 1,769 Lao texts — 2.8% — can be read without OCR**, and they are mostly subsidiary instruments:
decrees, agreements and ministerial instructions. The one that matters for the pillars is LA-1778, ດຳລັດ
ວ່າດ້ວຍການຄ້າທາງເອເລັກໂຕຣນິກ, the **Decree on Electronic Commerce**.

**Every principal pillar-6 and pillar-7 law is a scan.** Checked in the manifest, not assumed: the Lao texts of
the Electronic Transactions Law (LA-2023), the Competition Law (LA-880), the Cyber Security Law (LA-2537), the
Law on Information and Communication Technology (LA-1136) and the Bank of the Lao PDR Law (LA-2383) are all
`pdf_scanned`, and all 12 Lao seed documents are scans. Of the 14 seed documents only two carry text, and both
are **English translations** — which this note is careful to say are never the authoritative text (1.3). So
**stage 2 needs a full Lao OCR pass for the pillar material**, and the 6.4% figure buys it almost nothing where
it counts.

**The OCR pilot, 2026-09-20** (`../_finale-survey/explore-2026-09-20/la-ocr-and-translation.md`), run before any
of this was crawled: Tesseract 5 with `lao.traineddata` from **tessdata_best**, pages rendered at 300 DPI
through pypdfium2, on the real scan of the Cyber Security Law 2025.

| Check | Result |
| :---- | :---- |
| Script | 100% of letters came back as Lao on all three pages — no Thai substitution, no invented characters |
| Volume | 869, 1,015 and 1,584 characters a page: dense legal text, not fragments |
| The law's title against the portal's own Unicode | 89% as read; **100%, an exact match, after normalising the ຫນ/ໝ ligature** |
| Speed | 1.7 s a page |

That normalisation is `parse.fold()` in this package (1.3), so the same spelling rule that matches a title on
the listing will fold OCR output. **Nothing in this scraper does OCR**; it is stage 2's work, and the pilot is
recorded here so stage 2 does not have to rediscover it.

**Three things stage 2 should know before planning:**

1. **`OCR_LANG` is one setting for a whole run** and stage 2's ingest does not read the manifest's `language`
   column, so a Lao corpus needs its own stage 2 pass — a settings change, but one to plan rather than discover.
2. **53 documents are the gazette's own English translations.** They are recorded with `language: eng`,
   `is_translation: true` and the flag `unofficial_translation`, and the law table hangs each off its Lao law in
   `translation_doc_id`. The developer's caveat of 2026-09-20 stands: **the English PDF may not be the latest
   version of the law**, the Lao text is the document of record, and the listing gives one pair of dates for
   both, so nothing on the page says when a translation was made.
3. **There is no translation step anywhere in stage 2 or stage 3.** For Lao that is a new stage, not a
   configuration change, and it is the strongest argument for scheduling this economy carefully.

## 4. Output format against CONTRACT.md

| Contract column | Where it comes from on this portal | On the list of 2026-09-20 |
| :---- | :---- | :---- |
| `law_name` | The listing's ຫົວຂໍ້, in Lao, folded to one spelling | every law |
| `law_number` | **Nothing.** No listing on this portal states an act number for any instrument | empty everywhere |
| `portal_id` | Ours, from the gazette's own record id: `LA-2537` | every law |
| `version_as_at` | **Nothing**: the gazette publishes as made | empty everywhere |
| `published_on` | ເຜີຍແຜ່ລົງຈົດໝາຍເຫດ, the date the gazette published it, day-first, stored ISO | every law |
| `made_on` | ວັນ-ເດືອນ-ປີ ນິຕິກໍາ, the date of the instrument | every law |
| `legal_status` | ສະຖານະພາບ, stated on **every** row: ປັດຈຸບັນ → `in_force`, ສະບັບເກົ່າ → `repealed` | every law |
| `status_source` | `portal_listing` | every law |
| `document_kind` | The `legaltype`, narrowed by what the title says the instrument does | every row |
| `principal_law_number` | **Nothing**: an amending title names its target in words, with no number to join on | empty everywhere |
| `last_amended`, `last_amending_instrument` | A weak join on the words of the title (`checker.py`), with `amends_title_names` carrying what the title actually said | only where a title match is unambiguous |
| `citation_url` | The file's address, taken from the row | every document |
| `language` | `lao`, or `eng` for the gazette's own translation, with `is_translation` | every row |
| Dates | Listing `25-06-2025` is day-first; stored ISO | every date |

**Why `legal_status: repealed` for ສະບັບເກົ່າ.** The word means "old version". `CONTRACT.md` 3.3's vocabulary has
no `superseded`, and decision 17 settles superseded as repealed, so that is the reading — with the portal's own
word kept in `status_word` so nobody has to take our word for it.

## 5. Open choices for the developer

| Choice | Now | What to weigh |
| :---- | :---- | :---- |
| **The title rule is written from vocabulary, by someone who does not read Lao** | `sources.yaml`, `title_rule`, nine groups of plain-substring Lao patterns | This is the weakest thing in the country folder. It was built from the words of titles actually read on 2026-09-20, and it has never been checked by a Lao reader. **It costs nothing today**, because the crawl runs at scope `all` and the rule only orders the work and picks the `relevant` subset — but a later stage that trusts `relevant` would inherit the gap. Worth an hour of a Lao speaker's time before anyone uses that scope |
| The `old=1` listing | Read, and crawled at scope `all` | It is 293 more documents and about 45 minutes. Dropping it would halve nothing but **would lose every amending instrument in the country** (1.2) |
| Detail pages | Not read (2.3) | The evidence says they carry less than the listing. The one field only they have is ອອກໂດຍ, the issuing body; if a later stage wants it, that is about 1,800 requests |
| English translations | Collected, `language: eng`, never authoritative | The developer's caveat (1.3): an English file may be older than the Lao text and nothing on the page says so. Whether a stage 2 that reads English first is a saving or a trap is a judgement for the instrument, not this scraper |
| The audit's `LA` rules | **Not written** (2.5) — the shared tool is not this session's to edit | Without them the audit flags `no_text_layer` on every row, which is the normal state here and says nothing. The rule set is written out below, ready to paste |
| `--pages` on the update check | Available, not the default | A full check is 25 minutes. Whether the daily check should be shallow and the weekly one full is an operational choice |

## 6. Known gaps

### Two manifest columns on the first crawl need a migration, not a re-crawl

Found by the verification of 2026-09-21, after the crawl. Neither affects which bytes were fetched, and both
are fixable by rewriting manifest columns from files already on disk.

| Column | What is wrong | Rows |
| :---- | :---- | ----: |
| `source_url` | It is the adapter's citation URL, **not the percent-encoded address the bytes came from**. 1,177 rows carry raw Lao characters and 793 a literal space; the sidecar's `final_url` has the encoded form beside every one | 1,374 of 1,762 in the corpus |
| `in_force_status` | The first crawl ran before the adapter was corrected and wrote the **normalised enum** (`in_force`, `repealed`); `CONTRACT.md` 3.2 asks for the portal's raw text, which the delta run's four rows correctly carry (ປັດຈຸບັນ, ສະບັບເກົ່າ). So one manifest holds two value spaces | 1,811 of 1,815 |

**`source_url` is the Round 1 defect, reproduced.** `CONTRACT.md` 3.2 already names it — "Round 1 wrote the
adapter's citation URL instead, which differs on 871 frozen rows (Malaysia 837 with unencoded spaces)" — and
already prescribes the remedy: "the migration rewrites them from the sidecar". Lao PDR is now the largest
instance, at 1,374 rows, because this is the first portal whose filenames are mostly non-ASCII. The engine
writes `plan.source_url()`, which is `citation_url or url`; writing `http.final_url` instead would fix it for
every economy at once, and is a hand-back request.

**`in_force_status` is ours**, and the fix is already in `adapter.py` — the crawl simply predates it. Nothing
is lost: the normalised value is in `contract_meta.legal_status` and in `law_table.csv` for all 1,773 laws, and
the portal's own word is in `status_word`.

**Why neither is being fixed by re-crawling.** Re-fetching 1,811 documents — five hours, 3.7 GB and about
1,900 requests to a portal that has been entirely co-operative — to correct two metadata columns whose correct
values are already on disk would be disproportionate. Both want the same thing: a pass over `manifest.jsonl`
that rewrites columns from the sidecars and the link list. That tool does not exist yet, and `CONTRACT.md`
already contemplates it for `source_url`.



- **The title rule has not been read by anyone who reads Lao** (section 5).
- **`RULES["LA"]` is not in `tools/audit_run.py`** (2.5, and "Shared-file edits still to make" below).
- **The amendment linkage is weak, and the law table says so rather than inventing it.** A Lao amending title
  names the law it alters in words — ກົດໝາຍ ວ່າດ້ວຍການປັບປຸງບາງມາດຕາ**ຂອງກົດໝາຍວ່າດ້ວຍນໍ້າ** — and there is no
  number anywhere to join on. `checker.py` fills `last_amending_instrument` only where the target phrase matches
  a law's title outright, and puts what the title said in `amends_title_names` for a person to judge. A wrong
  link between two laws is worse than no link.
- **Laos does have a data-protection statute**, unlike Timor-Leste: ກົດໝາຍ ວ່າດ້ວຍການປົກປ້ອງຂໍ້ມູນເອເລັກໂຕຣນິກ
  (Law on Electronic Data Protection, id 1216, 2017), beside a Cyber Security Law (2025, id 2537), an
  Anti-Cybercrime Law (2015, id 861), an Electronic Transactions Law (revised 2022, id 2023), an Electronic
  Signature Law (2018, id 1495) and a Telecommunications Law (revised 2021, id 1852). That is an unusually
  complete pillar 6 and 7 set for an economy this size, and it is **a finding for the instrument**, not a
  property of this scraper.

### Is a re-crawl needed? No — asked and answered on 2026-09-21

Put directly to the question after the verification, because "re-fetch everything" is the tempting answer and
it is the wrong one here.

**The bytes are not in doubt.** 1,815 documents across two runs, every one with its sha256 in the manifest,
`scrape.py --validate` reporting 0 errors and 0 warnings on both, 0 orphan files and 0 duplicate content
hashes. A second crawl would fetch the same bytes and produce the same hashes.

**The seven missing Lao documents cannot be recovered by fetching again.** Each was already tried twice, on two
days with different code. A third probe on 2026-09-21 (5 requests) tried every way a CMS mangles a filename:

| Tried | Result |
| :---- | :---- |
| LA-674 with its **20 zero-width spaces** (U+200B) removed | HTTP 200, the catch-all page |
| LA-674 with the space before `.pdf` trimmed, and with both | HTTP 200, the catch-all page |
| LA-698 and LA-699 with the space before `.pdf` trimmed | HTTP 200, the catch-all page |
| LA-912, LA-735, LA-1055, LA-1518 under an alternative Unicode normal form | **Not testable**: Lao has no canonical decomposition — U+0EB3 does not decompose — so NFD and NFC are the same string. The stated address is the only spelling there is |

So the files are not on the server under any name we can construct, and the zero-width spaces are a red herring.
These seven are the portal's, and the record now says so on three attempts rather than one.

**The two manifest defects are metadata, and a re-crawl is the wrong tool for them.** `source_url` and
`in_force_status` (section 6) both have their correct values already on disk — in the `.headers.json` sidecars
and in `links_rebuilt/laws.csv`. Re-fetching 3.7 GB from a host that has answered about 4,300 requests without
once refusing us, in order to rewrite two string columns, would be poor stewardship and would change no
document. They want a migration pass, which `CONTRACT.md` 3.2 already prescribes for `source_url`.

**And the engine fix for `source_url` is deliberately *not* being made yet.** Writing `http.final_url` instead
of `plan.source_url()` is one line and is the right fix, but applied now it would put percent-encoded addresses
in any new run's manifest while every existing run holds the unencoded form — and the update check keys on
exactly that column. That is the third time this country would have tripped over a half-migrated address
(1.3, and the census defect of section 8). **It belongs in the same commit as the migration**, so the manifests
and the code change together. Written up as a hand-back request rather than half-done.

## 7. Round 1 corpus, against the portal

Lao PDR was not in Round 1. Nothing to compare.

## 8. Dead ends

- **`legaltype=16` (2026-09-20).** Read in full, 18 pages, on the chance it was a second body of laws. It is not:
  all 180 of its ids are in `legaltype=6`. The 18 requests bought the answer, and the listing is now excluded by
  `subset_of` in `parse.LEGAL_TYPES`. The page is kept as `tests/fixtures/la_listing_law16_p1_2026-09-20.html`.
- **The law's own page (2026-09-20).** Read once, id 2597, to find out whether the convention's "read every
  detail page" rule was worth about 1,800 requests here. It is not: the page carries less than the listing row
  (2.3).
- **`Document_pageSize` (2026-09-20, from the exploration).** The server ignores it. There is no cheap way to
  read a long listing.
- **`max_pages: 60`, the first link list build of 2026-09-20 (188 requests, discarded).** The guard against a
  broken pager was set at 60 pages without checking it against the longest listing. Agreement holds **657** laws
  = 66 pages, so the build stopped at 600 and **57 agreements were missing**. It printed a warning and finished
  with exit 0, which is how a fault like this survives: the summary line said "1,716 laws" and looked right.
  Fixed three ways rather than one — `max_pages` raised to 120 in `sources.yaml`; a listing cut short by the
  guard now raises `GazetteUnavailable` so **nothing is written** instead of something short; and a listing whose
  stated total needs more pages than the guard allows says so **before** it starts reading. Two tests cover it.
  The list was rebuilt from scratch, and both logs are kept beside the list it produced:
  `links/build_discarded_2026-09-20.log` (the 188-request build that stopped at 600) and `links/build.log` (the
  194-request rebuild that reached 657).

## 9. Evaluation only

No gold set for Lao PDR.

## 10. Files, hand-back and evidence

| Path | What it is | Repo counterpart, under `stages\p1-scrape\` |
| :---- | :---- | :---- |
| `scraper/` | The adapter package (`__init__.py`, `parse.py`, `adapter.py`, `catalogue.py`, `checker.py`) | `src/p1_scrape/adapters/la_gazette/` — new, no repo counterpart yet |
| `scraper/WORKFLOW.md` | How to build the list and run a crawl | `docs/LA_CRAWL_WORKFLOW.md` |
| `updates/` | The update check | `src/p1_scrape/adapters/la_gazette/updates/` |
| `updates/WORKFLOW.md` | How to run a check | `docs/LA_UPDATE_WORKFLOW.md` |
| `sources.yaml` + `links/seed_laws.yaml` | joined, `sources.yaml` first | `instrument/sources_la.yaml` and `contracts/instrument/sources_la.yaml` |
| `tests/` | 60 offline tests (40 + 20) and nine fixtures | `tests/` and `tests/fixtures/la/` |
| — | The four engine changes of 2.5 | `economies.py`, `adapters/registry.py`, `contracts/schemas/manifest.schema.json`, `utils.py`, `dedup.py`, `orchestrator.py` |

**Evidence behind this note:** the exploration of 2026-09-20
(`../_finale-survey/explore-2026-09-20/la-lao-pdr.md` and `la-ocr-and-translation.md`), the three paced probes of
2026-09-20 (63 requests in all: 38 to settle 6 against 16, 11 for the per-kind totals, 14 for `old=1`, the detail
page and two documents weighed), the nine saved fixtures in `tests/fixtures/`, and the link list in `links/` with
its `discovery_log.jsonl` and `catalogue_meta.json`.

## Shared-file edits still to make

**This session was asked not to edit shared files.** These are the exact edits the convention calls for, written
out so the developer or a later session can make them. Nothing below has been applied.

### 1. `CONVENTIONS.md` section 6 — a row in the table "Where each country stands"

```
| Lao PDR (`LA`) | Yes since 2026-09-20, rebuilt 2026-09-21 (`scraper/catalogue.py`: every listing, `old=0` and `old=1`, 193 requests: 1,773 laws -> 1,824 documents) | `LA_ws_2026-09-21`, the first crawl: 1,811 of 1,824 stored in 5 h at 6 s, no refusal | Generic flags only: **`RULES["LA"]` not written** (item 7 below) | Both runs | **Yes** (`updates/`, built 2026-09-20, **run live twice on 2026-09-21**: 193 requests each) | `LA_corpus_2026-09-21` | Yes, on the run and the corpus (`scraper/checker.py`) | 60 offline | Yes |
```

and, in the prose under it, Lao PDR is **the fifth country**, and the first whose update check ran live on the
day its first crawl finished.

### 2. `CONVENTIONS.md` section 6, the "what is left" list

```
- **`tools/audit_run.py` has no `RULES["LA"]`**, so Lao PDR's audit applies generic flags only. On a portal
  where 93.6% of the documents are scans that means `no_text_layer` on 1,697 of 1,811 rows — a count of the
  corpus rather than a finding — and nothing marks the 116 documents that carry native text and need no OCR.
- **Lao PDR departs from rule 5** (read every act's detail page) on measured evidence, and `DECISIONS.md` has
  no Lao entry to authorise it. It needs the developer's ruling, not a scraper change.
```

### 3. `outputs/README.md` — a row in the "Countries" table

```
| `LA/` | Lao PDR | `LA/README.md`: 3 runs (1 crawl, 2 update checks) and the corpus **`LA_corpus_2026-09-21`**, which is what downstream reads for Lao PDR | `countries/la-lao-pdr/NOTES.md`; how to run a crawl: `countries/la-lao-pdr/scraper/WORKFLOW.md`; only what changed: `countries/la-lao-pdr/updates/WORKFLOW.md` |
```

`outputs/README.md` has no Timor-Leste row either, so that one is still owed too.

### 4. `countries/README.md` — hand-back rows

```
| `la-lao-pdr/scraper/*.py` | `src/p1_scrape/adapters/la_gazette/*.py`, a new package: Lao PDR is not in the repo yet |
| `la-lao-pdr/updates/*.py` | `src/p1_scrape/adapters/la_gazette/updates/`, the same shape (`python -m p1_scrape.adapters.la_gazette.updates`). New on 2026-09-20, no repo counterpart yet |
| `la-lao-pdr/tests/test_la_*.py` and their `fixtures/` | `tests/` and `tests/fixtures/la/` |
```

and, in the prose about engine changes, the fourth change of 2.5 above — the slug that strips a non-Latin script
to nothing — which is a hand-back request in its own right and affects every future non-Latin economy.

### 5. `countries/my-malaysia/scraper/catalogue.py` — `_cell` must not collapse whitespace in a URL

**This one is a live defect in four countries' shared code**, found by Lao PDR's first update check
(`outputs/LA/LA_ws_2026-09-21_to_2026-09-21/RUN_NOTE.md`). `_cell` puts every string through
`re.sub(r"\s+", " ", v)` so a CSV cell stays on one line. That is right for a title and wrong for an address:
**42 of this portal's filenames contain two consecutive spaces**, and `laws.csv` wrote them as one. The
documents were fetched correctly — `documents.jsonl` and the manifest keep the real address — but the census
no longer matched them, so the update check read 42 laws as having moved and the law table would have reported
46 stored laws as not held.

Singapore, Australia and Timor-Leste import the same `_cell`. It has not shown for them only because no other
portal here has a double space in a filename.

Lao PDR fixes it locally (`scraper/catalogue.py`, `_URL_COLUMNS` and `_cells`, with a test). The shared fix is
to give `_cell` the same exemption, and to have each country's writer name its own URL columns:

```python
#: columns that hold an address: their whitespace is never collapsed
_URL_COLUMNS = frozenset({"url", "lao_url", "english_url", "detail_url", "source_url", "document_url"})


def _cells(row: dict) -> dict:
    return {k: (v if k in _URL_COLUMNS else _cell(v)) for k, v in row.items()}
```

### 6. `tools/merge_corpus.py` — a document's identity must include its **language**

**This one costs 53 documents in the corpus today.** `identity()` returns
`("law", portal_id, document_kind)`, so two files that describe the same law under the same kind are treated as
two copies of one document and the older is superseded. On this portal a law can have **two files in two
languages** — the Lao text and the gazette's own English translation — and they are not copies of each other.
Result, measured on `LA_corpus_2026-09-21`: 1,762 documents, **53 superseded, every one an English
translation**, and no `*_en` folder copied into the corpus at all. `law_table.csv` reports it honestly (55 laws
list a translation, the corpus holds 0), and every file is still in the run folders — but the folder downstream
reads has none of them.

```python
def identity(row: dict, link: Optional[dict]) -> tuple:
    meta = (link or {}).get("contract_meta") or {}
    if meta.get("portal_id") and meta.get("document_kind"):
        # a law can have one document per LANGUAGE: the Lao text and the gazette's own English translation are
        # not two copies of one document, and collapsing them drops the translation from the corpus
        return ("law", str(meta["portal_id"]), meta["document_kind"], meta.get("language") or "")
    return ("url", row["source_url"])
```

Safe for the other four countries: Singapore, Australia and Timor-Leste store one language per law, and
Malaysia takes English first and Malay only where there is no English (decision 14), so no law there has two
language editions in one corpus. Adding the key changes nothing for them and recovers 53 documents here.

### 7. `tools/audit_run.py` — `RULES["LA"]`, and the one line that lets it run

**Two edits, not one.** Today the rules are only applied to a file that has text:

```python
if rules and text and len(text) >= MIN_TEXT_CHARS:
    flags = rule_flags(row, meta, kind, page_count, text, rules, flags)
```

On this portal no document ever has text, so `RULES["LA"]["apply"]` would never be called. Replace with:

```python
if rules and ((text and len(text) >= MIN_TEXT_CHARS) or rules.get("expect_scanned")):
    flags = rule_flags(row, meta, kind, page_count, text, rules, flags)
```

Then the rule set itself:

```python
def _la_flags(row, meta, kind, page_count, text, rules, flags):
    """Lao PDR. **Nearly every document is a scan**, so `no_text_layer` is the normal state of this corpus and
    not a finding: left alone it fires on 95% of the rows and says nothing. Two things here are worth a
    person's time, and neither is the absence of text.

    The first is a file that is not a usable document at all. The second is the **opposite** of the
    expectation: 116 of the 1,811 documents carry native text. They are **not** the pillar laws — every one of
    those is a scan (`../NOTES.md` 3.2) — but marking them still saves stage 2 an OCR pass per document and
    tells it which files carry text it can read directly.

    The portal serves one shape, a PDF of page images at `/kcfinder/upload/files/<name>.pdf`, so there is no
    second shape to tell apart as there is in Timor-Leste.
    """
    scanned = "no_text_layer" in flags
    if scanned:
        flags = [f for f in flags if f != "no_text_layer"]
        flags.append("scanned_as_expected")          # counted in audit.md, never a finding
    else:
        flags.append("native_text")                  # stage 2 can read this one without OCR

    if page_count is not None and page_count < 1:
        flags.append("no_pages")                     # a PDF the reader opens with nothing in it
    size = row.get("byte_size") or 0
    if size and page_count and size / page_count < rules["min_bytes_per_page"]:
        flags.append("thin_scan")                    # far too few bytes for a page of images: truncated

    # A one- or two-page principal act is ordinary here, not a repeal notice: the smallest real documents in
    # the crawl of 2026-09-21 are one-page Decrees and Orders of 26 to 75 KB. The generic `short_principal`
    # cannot tell them apart because there are no words to read, so it is replaced by a plain count.
    if kind == "principal_act" and page_count is not None and page_count <= SHORT_PAGES:
        flags = [f for f in flags if f != "short_principal"]
        flags.append("short_scan")
    return flags


"LA": {
    "html_is_a_fault": True,      # the gazette serves PDFs; an HTML page stored is a landing or error page
    "expect_scanned": True,       # 95% of the documents have no text layer, so the rules must run anyway
    # Calibrated on the crawl of 2026-09-21, not on two sampled documents: the bytes per page run from
    # 5.2 KB (a sparse one-page scan) through a median of about 96 KB to 1.46 MB. 2 KB a page therefore sits
    # an order of magnitude below anything real, and the earlier draft of this rule — 20 KB a page and a 30 KB
    # floor — would have flagged the smallest genuine document in the corpus, a 26,720-byte one-page Decree,
    # as truncated.
    "min_bytes_per_page": 2_000,
    "apply": _la_flags,
},
```
