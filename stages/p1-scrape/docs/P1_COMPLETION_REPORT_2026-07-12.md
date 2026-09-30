# Project 1 Completion Report — Web Scraping / Retrieval (Hand-off #1)

**Project:** RDTII Rocky, Stage 1 of 3 (P1 scrape → P2 text extraction → P3 mapping)
**Status: COMPLETE** — corpus delivered, validated, version-controlled
**Date:** 2026-07-12 · **Repo:** https://github.com/JohnChen-kmg/rdtii-p1-scrape (private)

---

## 1. Executive summary

Project 1 built a production-grade crawler and used it to retrieve the **complete,
pillar-agnostic statute corpus** of Singapore, Malaysia, and Australia from their
official government portals — **2,616 laws (~6.7 GB)** as raw native-PDF / scanned-PDF /
HTML documents, each with legal metadata (title, dates, status) and a full HTTP audit
trail. The output passes the frozen manifest contract (v0.2.0) with **0 errors and 0
warnings**, and the whole corpus is reproducible with one resumable command.

Deliberate scope decision (recorded): laws are **not** filtered by pillar/indicator at
crawl time — mapping is Project 3's job. This makes the corpus a one-time asset reusable
for any future pillar.

## 2. What was delivered

### The corpus

| Economy | Portal (official) | Laws | native PDF | scanned PDF | HTML |
|---|---|--:|--:|--:|--:|
| Singapore | sso.agc.gov.sg (Current Acts) | 525 | 524 | 1 | — |
| Malaysia | lom.agc.gov.my (Laws of Malaysia, act 1–900) | 833 | 357 | 474 | 2 |
| Australia | legislation.gov.au (in-force principal Acts) | 1,258 | 867 | — | 391 |
| **Total** | | **2,616** | **1,748** | **475** | **393** |

### Per-law metadata (manifest, 28 fields)

| | Real title | Publication date | Assent date | Commencement | In-force status |
|---|---|---|---|---|---|
| SG | 100% | — (portal listing has none) | — | — | 100% ("Current") |
| MY | 89% (92 acts blank **on the portal itself**) | 92% | 87% | 90% | — |
| AU | 100% | — | 99% | — | 99% ("InForce") |

Plus, for every row: provenance (source URL, HTTP status, redirect chain, response
headers in a `.headers.json` sidecar), `content_sha256`, byte size, page count,
classification (`source_type` + `pdf_is_scanned`), and a stable `doc_id` join key
(`<cc>-<lawslug>-<seq>`) that survives re-crawls.

### The machinery (reusable)

- **Crawler** (`src/p1_scrape/`): thin core + one adapter per portal; scope
  `seed | relevant | all`; forms `pdf | html | both`.
- **Resilience**: resumable (re-runs skip retrieved laws), checkpoint every 10 docs,
  anti-bot escalation + backoff, per-document and per-economy fault isolation, built-in
  health tracker (`crawl_status.json` heartbeat + auto-abort on portal throttling) and an
  external watchdog (`tools/crawl_tracker.py`).
- **Contract enforcement**: JSON-Schema validation gate (`scrape.py --validate`), 16
  automated tests.
- Full engineering log: [docs/WORKFLOW.md](WORKFLOW.md) (per-portal recipes + every
  problem hit and its fix).

## 3. Verification evidence

| Check | Result |
|---|---|
| Contract validation (schema 0.2.0, 28 fields) | **2,616 rows, 0 errors, 0 warnings** |
| doc_id / sha256 uniqueness | 2,616 / 2,616 unique |
| Every `local_path` + sidecar resolves on disk | 0 missing |
| Live-crawl audit trail | `crawl_log.jsonl`: 1,257 OK fetches from legislation.gov.au + 833 from lom.agc.gov.my (current run); 524 from sso.agc.gov.sg (v1 run log, retained in `handoff1_old_v01/`) |
| Content fidelity spot-checks | AU HTML carries full Act text (e.g. Privacy Act 2.35 MB, 353 section headers); MY native PDFs ~1,000 chars/page; MY scanned PDFs 0 chars/page (correctly routed to OCR) |
| Rerunnability | fresh-clone quickstart verified; 16/16 tests; dry-run; bad input exits cleanly |

## 4. Known limitations (honest list for the record)

1. **92 MY acts have generic titles ("Act N")** — verified blank on the portal itself;
   their PDFs carry the title on the cover page → P2 can recover them during extraction.
2. **SG has no date metadata** (the browse listing exposes none); dates are inside the
   PDFs → recoverable in P2.
3. **391 AU acts are HTML, not PDF** — these are the multi-volume giants (Criminal Code,
   Customs Act…) for which **no single official PDF exists**. The HTML is the complete,
   cleanest text form.
4. **Deep-link anchors (`anchor_hint`) are not populated** in the PDF-first corpus (an
   HTML-page feature); P3 citations should use `source_url`, which resolves for every row.
5. **SSO anti-bot**: Singapore re-crawls within the same day can trigger HTTP 202/junk
   responses. The crawler now detects and stops early; guidance in WORKFLOW.md.
6. Scanned-vs-native classification is heuristic (chars/page ≥ 100); P2 re-checks during
   extraction (a mis-flag is recoverable, and the flag is present on every row).

## 5. What Project 2 can rely on (the hand-off interface)

**Inputs on disk** (`handoff1_v2/`, ~6.7 GB, not in git — regenerable):

- `manifest.csv` / `manifest.jsonl` — one row per document; **`doc_id` is the join key**
  for everything downstream.
- `raw/<CC>/<law_slug>/<ts>__<kind>.<ext>` — the document bytes (`kind` ∈ native /
  scanned / page), with `.headers.json` provenance sidecars.
- `inventory_<cc>.csv` — curated **seed inventories** (~20 rows each). *(Corrected
  2026-07-16 — see Addendum 4: earlier text called these "the complete portal
  listings", but later seed-scope runs overwrote the full-harvest CSVs. The complete,
  auditable retrieval record is `manifest.jsonl`; the v1 full SG harvest survives in
  `handoff1_old_v01/inventory_sg.csv`.)*

**The routing field for P2 is `source_type`** — it splits the corpus into exactly the
three processing lanes P2 must build:

| Lane | Volume | Suggested tooling |
|---|---|---|
| `html` → parse DOM to text | 393 docs, ~125 MB (AU-dominant) | HTML→text parser; AU section headers are `p.ActHead5` etc. |
| `pdf_native` → extract text layer | 1,748 docs, **119,129 pages** (median 35 pg) | pypdfium2 text extraction (BSD/Apache; P1 switched from AGPL PyMuPDF 2026-07-12) |
| `pdf_scanned` → **OCR** | 475 docs, **12,292 pages** (median 16 pg; 474 MY + 1 SG) | OCR engine (e.g. Tesseract / cloud OCR); this is the bounded, budgetable OCR workload |

**Quality approach already decided** (P1 discussion, recorded): hybrid grounding —
automated extraction plus **manual spot-checks** that randomly sample extracted text back
against the source PDF/HTML, before trusting the corpus for mapping.

**Suggested P2 output shape**: one text artifact per `doc_id` (e.g.
`text/<doc_id>.json` with page/section structure), a P2 manifest keyed by the same
`doc_id` carrying extraction method + quality metrics (chars extracted, OCR confidence,
spot-check result), and recovered metadata (the 92 MY titles, SG dates) written back as
enrichment. That gives P3 a single joinable chain: P1 provenance → P2 text → P3 mapping.

## 6. Asset locations

| Asset | Where |
|---|---|
| Code + docs + contract (52 files) | https://github.com/JohnChen-kmg/rdtii-p1-scrape (**private**) |
| Final corpus (v2) | local `handoff1_v2/` (rename to `handoff1/` pending a file lock) |
| v1 corpus backup (incl. SG live-crawl log) | local `handoff1_old_v01/` |
| Regenerate command | `.\.venv\Scripts\python scrape.py --economy SG,MY,AU --scope all --out handoff1` |
| Validation gate | `.\.venv\Scripts\python scrape.py --validate handoff1\manifest.csv` |
| Workflow map + engineering log | `README.md` (mermaid) + `docs/WORKFLOW.md` |

---

## Addendum (2026-07-14) — audit response & version-currency fixes → corpus v2.1

An independent baseline audit (P2/P3 planning side) was verified against the corpus.
Result: its official-hosts claim confirmed (all documents from the six government hosts,
zero exceptions); its "Acts-only / no second layer" gap confirmed (the ~20-document
second-layer delta list remains open, awaiting URLs); its SG staleness finding confirmed
and **fixed**; its AU "broken SOCI PDF" finding **refuted** (file verified healthy —
438k chars, current compilation; the 1-provision result is a P2 splitter issue).

Beyond the audit, P1's own check found a **systemic Malaysia version-currency defect**:
the picker stored as-enacted originals although lom offers current consolidated English
versions (`/EN/`). Fixed (unit-tested) and **Malaysia fully re-crawled**.

### Corpus v2.1 (supersedes §2's table)

| Economy | Laws | native PDF | scanned PDF | HTML |
|---|--:|--:|--:|--:|
| SG | 525 | 524 | 1 | — |
| MY | **858** (+25) | **815** | **41** | 2 |
| AU | 1,258 | 867 | — | 391 |
| **Total** | **2,641** | **2,206** | **42** | 393 |

`validate`: **2,641 rows, 0 errors, 0 warnings** (contract 0.2.0). ~1.5 GB.

Material changes for P2 planning:
- **OCR lane collapsed 92%**: 42 docs / ~1,016 pages (was 475 docs / 12,292 pages) —
  the old scans were superseded editions; the current consolidations are native text.
- **Version currency now guaranteed** across all three economies (SG current
  consolidations — incl. the re-fetched Cybersecurity Act 2018 with its 2024
  amendments; MY `/EN/` consolidations or newest reprints; AU latest compilations).
- MY gained 25 acts (858), including 2026 legislation (e.g. the Johor Bahru–Singapore
  RTS Link Act 2026) — the corpus is fresher than the baseline's cutoff.
- Native-PDF lane is now 2,206 docs; HTML lane unchanged at 393.

---

## Addendum 2 (2026-07-14 late) — delta crawl: the subsidiary/regulator layer → corpus v2.2

P3's 18-item delta request (`rdtii-p3-map/docs/DELTA_CRAWL_REQUEST_2026-07-14.md`) is
**fully delivered** — every outstanding Tier-1 and Tier-2 item, including the optional
MAS notice. **18/18 fetched, 0 failures; validate OK: 2,658 rows** (SG 531 / MY 866 /
AU 1,261; 2,219 native PDF / 42 scanned / 397 HTML; ~1.6 GB).

New doc_ids (for P2 `run --only-doc`):

| Economy | doc_id | Document |
|---|---|---|
| SG | sg-ca2024-001 | Cybersecurity (Amendment) Act 2024 (No. 19/2024, as enacted) |
| SG | sg-can2025-001 | Cybersecurity (Amendment) Act 2024 (Commencement) Notification — S 677/2025 |
| SG | sg-pdpn2025-001 | PDP (Statutory Bodies)(Amendment) Notification 2025 — S 217/2025 |
| SG | sg-pdpr2021-001 | Personal Data Protection Regulations 2021 — S 63/2021 |
| SG | sg-agpcspd2024-001 | PDPC Advisory Guidelines — Children's Personal Data (2024) |
| SG | sg-mnfnch-001 | MAS Notice FSM-N16 Cyber Hygiene |
| MY | my-pdpgcbpdt2025-001 | PDP Guideline — Cross-Border Personal Data Transfer (GP 3/2025) |
| MY | my-pdpgadpo2025-001 | PDP Guideline — Appointment of DPO (2025) |
| MY | my-pdpgdbn2025-001 | PDP Guideline — Data Breach Notification (2025) |
| MY | my-csr2024-001 | Cyber Security (Licensing of CSSP) Regulations 2024 |
| MY | my-csr20245c36-001 | Cyber Security (Notification of Incident) Regulations 2024 |
| MY | my-csr20248a94-001 | Cyber Security (Risk Assessment & Audit) Regulations 2024 |
| MY | my-csr202460e1-001 | Cyber Security (Compounding of Offences) Regulations 2024 |
| MY | my-pdps2015-001 | Personal Data Protection Standard 2015 |
| AU | au-scia2018-001 | **SOCI Act 2018 — re-issued as full-text HTML** (222 section headers; replaces the PDF that P2's splitter read as 1 provision) |
| AU | au-tolaa2018-001 | Telecom & Other Leg. Amendment (Assistance & Access) Act 2018 (C2018A00148 — the old seed id C2021C00496 was withdrawn by the register) |
| AU | au-csr2025-001 | Cyber Security (Ransomware Payment Reporting) Rules 2025 (F2025L00278) |
| AU | au-tr2021-001 | Telecommunications Regulations 2021 (F2021L00289) |

Mechanics added for this layer (reusable): SG adapter accepts SL/SL-Supp URLs
(`?ViewType=Pdf` works on subsidiary legislation); AU adapter accepts F-series
instrument ids and honours a per-seed `form: html` pin; MY seed resolution no longer
misreads guideline numbers (GP 3/2025) as LOM act numbers (regression-tested).
All new sources remain **official government hosts** (sso/pdpc/mas ·
pdp/nacsa · legislation.gov.au). Still open for P2 (not P1): the 3 re-parse docs.

---

## Addendum 3 (2026-07-15) — proactive discovery sweep → corpus v2.3

A structured discovery pass (16 web sweeps across pdpc/imda/mas/csa · pdp/mcmc/bnm/sc/nacsa ·
oaic/acma/apra/cisc + both statute registers' SL sections) surfaced 18 candidate regulator
instruments not in the corpus; 17 URLs verified on official hosts; **15 fetched**
(one intentionally skipped: IMDA's telecom code text is not published as a document;
one failed: BNM RMiT — bnm.gov.my answers HTTP 202 to non-browser clients, attempt logged).

**Corpus v2.3: 2,673 documents** (SG 536 / MY 869 / AU 1,268; 2,228 native / 43 scanned /
402 html; ~1.6 GB), `validate` **0 errors, 0 warnings**.

New doc_ids (for P2 `run --only-docs`):

| Economy | doc_id | Instrument | Note |
|---|---|---|---|
| SG | sg-pdpr2021413f-001 | PDP (Notification of Data Breaches) Regulations 2021 (S 64/2021) | completes the PDPA SL set |
| SG | sg-cr2018-001 | Cybersecurity (CII) Regulations 2018 (S 519/2018) | |
| SG | sg-cr2025-001 | Cybersecurity (CII) (Amendment) Regulations 2025 (S 678/2025) | post-baseline |
| SG | sg-ccpcii-001 | CSA Cybersecurity Code of Practice for CII, 2nd Ed. Rev 1 | binding code, 65pp |
| SG | sg-mtrmg2021-001 | MAS Technology Risk Management Guidelines (2021) | |
| MY | my-pdpr2013-001 | Personal Data Protection Regulations 2013 (P.U.(A) 335/2013) | **scanned** (BM text) → OCR lane |
| MY | my-gtrm2023-001 | SC Guidelines on Technology Risk Management (SC-GL/2-2023) | post-baseline revision |
| MY | my-cso2025-001 | Cyber Security (Exemption) Order 2025 | 5th Act 854 instrument |
| AU | au-scir2025-001 | SOCI (Telecommunications Security and RMP) Rules 2025 (F2025L00325) | post-baseline |
| AU | au-scir2023-001 | SOCI (Critical infrastructure risk management program) Rules 2023 (F2023L00112) | |
| AU | au-csr2025c482-001 | Cyber Security (Security Standards for Smart Devices) Rules 2025 (F2025L00276) | post-baseline |
| AU | au-pscis-001 | Prudential Standard CPS 234 Information Security (F2018L01745) | |
| AU | au-pac2017-001 | Privacy (AGA — Governance) APP Code 2017 (F2017L01396) | mandatory-PIA duty (topic 8) |
| AU | au-pscorm-001 | Prudential Standard CPS 230 Operational Risk Management | commenced 1 Jul 2025 |
| AU | au-pc2024-001 | Privacy (Credit Reporting) Code 2024 | in force 1 Oct 2024 |

Known gaps, disclosed: BNM RMiT (202-gated; retry from a residential browser context or
accept the logged attempt), IMDA Telecom Cybersecurity CoP (no public document URL),
MCMC INSG Dec 2024 (no stable official URL found).

---

## Addendum 4 (2026-07-16) — independent-audit corrections (disclosed)

An independent audit (2026-07-16) confirmed the headline numbers from the artifacts
(2,673 docs; v2.3 = 15 docs; 3,013 crawl-log entries across 12 official hosts; 2,682
`.headers.json` sidecars) and found five defects. All five are fixed; none changed any
corpus content or count. Corrections are disclosed here, not silently rewritten:

1. **Overstated claim (corrected in place, §5 above):** `inventory_<cc>.csv` were called
   "the complete portal listings". In fact later seed-scope runs **overwrote** the
   full-harvest CSVs with ~20-row seed lists. Wording corrected to "curated seed
   inventories"; the complete retrieval record is `manifest.jsonl`. Root cause fixed in
   the orchestrator (a seed run can no longer clobber a harvest artifact).
2. **Crawl-log misclassification:** the 2026-07-15T03:22:48Z BNM RMiT entry said
   `outcome: ok` for an HTTP 202 non-retrieval. The original line is untouched; a
   **disclosed correction entry** (`correction: true`, true outcome `failed`) is appended
   to `crawl_log.jsonl`. Root cause fixed: both the playwright-request fetch rung and the
   log call now require an actually-retrieved artifact of the expected content type
   before "ok". The document was verified absent from the manifest.
3. **Version traceability:** the corpus versions (v2.0 → 2,616 · v2.1 → 2,641 · v2.2 →
   +18 fetched/+17 net → 2,658 · v2.3 → +15 → 2,673) are now a first-class ledger:
   [docs/CORPUS_VERSIONS.md](CORPUS_VERSIONS.md). The frozen manifest schema is untouched.
4. **Evidence now version-controlled:** `handoff1_v2/manifest.jsonl`, `manifest.csv`,
   `crawl_log.jsonl`, `cost_report.json` (~9 MB) are committed (raw/** stays out of git),
   marked byte-exact in `.gitattributes`.
5. **Stale example config:** `config/.env.example` CONTRACT_VERSION bumped 0.1.0 → 0.2.0.

Also added (audit's pre-20-Jul advice): a WORKFLOW.md note on where SG live-fetch
provenance lives (per-doc sidecars + the v1 run log — the v2 log alone under-represents
SG), and a local `--smoke` rehearsal ahead of judging.

## Addendum 5 (2026-07-17) — CRITICAL: AU multi-volume truncation fix → corpus v2.4

**The defect (found by the independent judge's substantive spot-check,
`RDTII Judge/01_Findings/SUBSTANTIVE_SPOTCHECK_MY_AU_2026-07-17.md`; verified, then
found to be larger than reported).** The AU HTML lane captured act text from the
`iframe#epubFrame` viewer on `/latest/text`. That viewer renders **one epub spine
document at a time — and one spine document is one volume** — so every multi-volume
compilation was silently stored as **volume 1 only**. The judge named 7 acts; the full
audit found **33** (of 399 AU register HTML docs). The flagship case: `au-ta1979-001`
(Telecommunications (Interception and Access) Act 1979) held ss.1–186J — all of
**Part 5-1A (ss.187A–187N, the 2-year metadata-retention obligation, incl. the s.187C
cited verbatim by the host baseline's only AU 7.3 row)** was absent. MY/SG PDF lanes
are unaffected (multi-volume acts have no single PDF, which is exactly why they were on
the HTML lane).

**Root cause & fix (adapter + fetcher, regression-tested).** The register publishes,
at the same dated endpoint family as the PDFs, a single epub whose spine contains
EVERY volume as a separate HTML document (`/{rid}/{date}/{date}/text/original/epub`).
The fix: multi-volume (and `form: html`-pinned) acts are now fetched as that epub via
plain `requests`, and `p1_scrape/epub.py` extracts and concatenates **all** spine
documents, verified against the OPF spine — any shortfall (bad zip, missing spine doc,
zero documents) is a **loud failure, never a silent partial**. Each stored artifact
carries `p1-epub-spine-doc i/n` markers, so completeness is machine-checkable forever.
The old framed capture survives only as a last-resort fallback and now **rejects**
(fails loudly on) any capture that self-declares "This compilation is in N volumes".
9 new regression tests (`tests/test_au_multivolume.py`); suite 30/30.

**Truncation audit (deliverable):** `docs/AU_HTML_TRUNCATION_AUDIT_2026-07-17.md` +
`tools/audit_au_truncation.py` — every AU register HTML doc checked against its own
front-matter volume map. Result after the re-fetch: **0 truncated documents remaining**
(33 truncated rows all superseded). Note for auditors: a TOC-vs-body check cannot find
this defect — each volume carries its own TOC, so a volume-1-only capture is internally
consistent; the volume map in the front matter is the reliable in-file signal.

**Re-fetch (33/33, §5.4 supersession).** Priority order honored: TIA 1979 first
(acceptance: text now contains s.187C, the phrase "data retention", Part 5-1A, and
runs to s.300 — verified before proceeding), then Telecommunications Act 1997
(3 spine docs, to s.594) and Corporations Act 2001 (7 spine docs, to s.1712), then the
rest. Every law kept its identity: the idmap allocated seq `-002`, each new row carries
`supersedes <old>`, no other doc_id changed. The superseded `-001` rows REMAIN in the
manifest for provenance, each annotated
`superseded by <new> (2026-07-17: epubFrame capture held volume 1 of N only …)` so the
truncated text cannot be consumed unknowingly. Manifest: **2,706 rows = 2,673 current
+ 33 superseded; validate OK, 0 errors, 0 warnings (contract 0.2.0)**. All fetches:
official host, rate-limited, logged in `crawl_log.jsonl`, `.headers.json` sidecars.

Old → new doc_ids (full table also in the hand-off note
`docs/HANDOFF_AU_MULTIVOLUME_2026-07-17.md`): au-ta1979-001→002, au-ta1997-001→002,
au-ca2001-001→002, au-asica2001-001→002, au-ba2015-001→002, au-bsa1992c8a4-001→002,
au-ca1901-001→002, au-ca1914-001→002, au-cca1995-001→002, au-cca2010-001→002,
au-cea1918-001→002, au-cta1995-001→002, au-epbca1999-001→002, au-fbtaa1986-001→002,
au-fla1975-001→002, au-fwa2009936e-001→002, au-hia1973-001→002, au-itaa1936-001→002,
au-itaa1997-001→002, au-ma1958-001→002, au-nccpa2009f78b-001→002,
au-ntsa199954b8-001→002, au-ntsa199978da-001→002, au-opggsa2006-001→002,
au-sa1976-001→002, au-sia1993-001→002, au-ssa1991-001→002, au-ssa1999-001→002,
au-ssa1999dcb5-001→002, au-taa1953-001→002, au-tga1989-001→002, au-vea1986-001→002,
au-wa2007-001→002.

**Disclosures (nothing silent):**
1. TIA 1979 was fetched **twice** (34 epub fetches for 33 docs): a tool re-run
   re-selected the already-superseded row; the second fetch was byte-identical (same
   sha), so the idmap correctly reused `au-ta1979-002`. The row rebuild momentarily
   dropped its `supersedes au-ta1979-001` note — restored the same hour; the selection
   logic now skips superseded rows (idempotent).
2. `cost_report.json` was clobbered by an idle (0-target) idempotency re-run; it was
   **reconstructed byte-exactly from the run's own evidence** (crawl_log entries +
   manifest byte sizes: 34 requests, 249.5 MB, 33 docs, 294 s) and the tool now skips
   the write on idle runs. Both crawl-log correction rules were respected: original log
   lines untouched, all corrections disclosed here.
3. The judge's count (7 named acts) was an under-count — the audit found 33. Documented
   rather than quietly fixed beyond the request.
