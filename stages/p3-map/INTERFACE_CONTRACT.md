# 0 · Interfaces & Contracts

**RDTII Rocky — the frozen spine that all three sub-project plans key off.**
Status: authoritative. If a sub-project plan disagrees with this document, this document wins until a versioned amendment is agreed (see §8).
Owner of this file: the P0/integration role (solo builder, John). Physical home: a fourth, tiny folder `00_contracts/` that Projects 1–3 each vendor a pinned **copy** of via `make sync-contracts` (a plain copy at a pinned SHA — **not** a git submodule; see §4, §8).

> **⚠️ VERSION NOTE (synced 2026-07-12): this seam is `CONTRACT_VERSION` = `0.2.0` as shipped by Project 1.**
> v0.2.0 added four **optional** legal-metadata manifest fields over v0.1.0 — `publication_date`, `assent_date`, `commencement_date`, `in_force_status` (see §2.2). This is a backward-compatible MINOR bump (same MAJOR `0`), so nothing on P2's critical path changed. The **authoritative field set is the vendored `00_contracts/schemas/manifest.schema.json`** (copied verbatim from `rdtii-p1-scrape/contracts/schemas/`, 28 fields / 15 required) — P2's `ingest.py` entry gate validates the real manifest against *that JSON*, not against the prose below. Any bare `0.1.0` literal remaining in the examples below is illustrative history; treat `0.2.0` as current.

---

## 1. Overview — the three sub-projects and the by-stage seam

The repo plan (P0–P10) is cut **horizontally by pipeline stage** into three independently-built folders. Each folder is a standalone repo with its own README, its own pinned `requirements.txt`, and its own CLI. They are wired only through two file-on-disk hand-off contracts (§2, §3) plus two shared specs (§4 instrument, §5 config). No sub-project imports another's Python.

| Sub-project | Folder | Pipeline stage | OWNS (one line) | Does NOT own |
|---|---|---|---|---|
| **Project 1 — Web Scraping (retrieval)** | `rdtii-p1-scrape/` | P1 | Crawl live SG/AU/MY portals and retrieve the raw bytes (HTML, native PDF, scanned PDF) + write Manifest (Hand-off #1). Owns the 10-pt **live portal crawling** item. | No OCR, no text cleaning, no tagging, no mapping. Emits raw files only. |
| **Project 2 — OCR + Tag Extraction** | `rdtii-p2-extract/` | P2 + field extraction | Turn raw files into clean **article-level text**, then extract structured feature tags + verbatim snippet + provenance per provision → Provision-Records + normalized source-text + a law-level coverage index (Hand-off #2). Owns the 10-pt **OCR <5% CER** item and verbatim grounding. | No crawling (consumes Manifest), no indicator scoring/mapping, no NEW/KNOWN, no final CSV. |
| **Project 3 — Mapping to RDTII** | `rdtii-p3-map/` | P3+P4+P5+P9+P6 | Prefilter → map each provision to indicator(s) with rationale → blind-verify → NEW/KNOWN diff → Malaysia error-check → write final 13-col CSV + JSON, incl. mandatory "No provision found" rows. Owns the 40% substantive block incl. **20-pt NEW-evidence** and **15-pt audit trail**. | No crawling, no OCR. Consumes Provision-Records + source-text + law index + Manifest; never re-reads raw PDFs except to re-confirm a snippet offset. |

**Shared spines (not owned by any single stage, §4–§5):** P0 Instrument (`indicators.yaml` + `sources_<cc>.yaml` + frozen policies) is read by all three. P7 config/model-swap layer is shared by Projects 2 and 3 (both run LLM/document-AI pipelines — the user's "similar pipelines" point; design once, do not duplicate).

**Build order (locked):** thin vertical slice first — Singapore, Pillar 6, one law (PDPA), end-to-end through P1→P2→P3 to **one correct, verifiable, cited row** — then Australia, then Malaysia, then breadth. The slice, live crawl, NEW-evidence, and audit trail are protected over breadth. Discretionary integration machinery is explicitly deferred (§8.1) so it never competes with the 40% substantive-accuracy work.

---

## 2. HAND-OFF #1 — Project 1 → Project 2 (raw files + Manifest)

Project 1 emits a **folder of raw retrieved files** plus a **Manifest** with exactly one row per retrieved document. Files are NOT OCR'd, NOT cleaned. Project 2's only entry point is this Manifest; it must never crawl.

### 2.1 Raw-file folder convention

```
handoff1/                              # the whole hand-off is this dir; hand a copy to P2
  manifest.csv                         # authoritative row-per-doc index (schema 2.2)
  manifest.jsonl                       # same rows, one JSON object per line (richer http meta)
  raw/
    sg/
      pdpa_2012/
        20260709T1032Z__native.pdf     # <access-ts>__<kind>.<ext>
        20260709T1032Z__native.pdf.headers.json   # sidecar: http status/headers/redirects
      cybersecurity_act_2018/
        20260709T1101Z__page.html
        20260709T1101Z__page.html.headers.json
    au/
      privacy_act_1988/
        20260709T1140Z__page.html
        20260709T1140Z__page.html.headers.json
    my/
      pdpa_2010/
        20260709T1210Z__scanned.pdf    # gazette scan → OCR demo / Deliverable #4
        ...
  crawl_log.jsonl                      # append-only: every URL touched, incl. failures/retries
```

Rules: one leaf directory per `(economy, law)` guess; `local_path` in the Manifest is **relative to `handoff1/`** (portable across machines — no absolute paths in the contract). Every retrieved file has a `.headers.json` sidecar so citation-fidelity (working URL) and the resilience story are auditable. `crawl_log.jsonl` records failed/blocked/retried URLs so the 10-pt live-crawl item is demonstrable even for docs that did not resolve.

### 2.2 Manifest schema (one row per retrieved document)

| Field | Type | Required | Description | Example |
|---|---|---|---|---|
| `contract_version` | string (SemVer) | ✅ | Seam/schema version this row was produced against; MAJOR-gated by P2/P3 (§8). | `0.1.0` |
| `instrument_version` | string \| null | ⬜ | RDTII methodology tag from `indicators.yaml` (informational, NOT gated). | `2.1.0` |
| `doc_id` | string (slug) | ✅ | Stable unique id; P2/P3 carry it end-to-end. `<cc>-<lawslug>-<seq>`. | `sg-pdpa2012-001` |
| `economy` | enum `SG\|AU\|MY` | ✅ | ISO-ish economy code. | `SG` |
| `source_url` | string (URL) | ✅ | Exact URL the bytes came from; must resolve at judging time. | `https://sso.agc.gov.sg/Act/PDPA2012` |
| `access_date` | ISO-8601 UTC | ✅ | When retrieved. | `2026-07-09T10:32:00Z` |
| `source_type` | enum `html\|pdf_native\|pdf_scanned` | ✅ | Retrieval-stage classification (see 2.3). | `pdf_scanned` |
| `pdf_is_scanned` | bool \| null | ✅ (null if html) | True if PDF has no extractable text layer / is image-only. Drives P2's OCR-vs-parse branch. | `true` |
| `local_path` | string (rel path) | ✅ | Path under `handoff1/` to the raw file. | `raw/my/pdpa_2010/2026...__scanned.pdf` |
| `law_name_guess` | string | ✅ | Best-effort law title from page/anchor/filename. Non-authoritative; P2 may refine. | `Personal Data Protection Act 2012` |
| `law_number_guess` | string \| null | ⬜ | Act/gazette number if visible. | `Act 26 of 2012` |
| `pillar_hint` | string \| null | ⬜ | `P6\|P7\|both` if the seed query/seed law targeted a pillar (feeds P3's expected-cell enumeration, §7.2). | `both` |
| `indicator_hints` | string \| null | ⬜ | Comma-list of in-scope indicator IDs the seed targeted (e.g. `P7-I2` for a cybersecurity act). Traceability for the coverage checklist. | `P7-I2` |
| `retrieval_method` | enum `playwright\|requests\|api` | ✅ | How bytes were fetched (feeds provenance + resilience story). | `playwright` |
| `http_status` | int | ✅ | Final HTTP status after redirects. | `200` |
| `http_headers_path` | string (rel path) | ✅ | Path to `.headers.json` sidecar. | `raw/sg/.../...headers.json` |
| `content_type` | string | ✅ | Server `Content-Type`. | `application/pdf` |
| `content_sha256` | string (hex) | ✅ | Hash of retrieved bytes; dedupe + integrity. | `9f2c...` |
| `byte_size` | int | ✅ | File size. | `4823191` |
| `page_count` | int \| null | ⬜ | For PDFs. | `312` |
| `anchor_hint` | string \| null | ⬜ | **Portal-specific deep-link suffix** to append to `source_url` to reach the provision (see 2.5). Store the whole suffix, incl. its leading `?`/`#`. | `?ProvIds=pr26-` |
| `anchor_kind` | enum `query\|fragment\|none` \| null | ⬜ | How `anchor_hint` attaches: `query` (append after path, portal builds its own `?`/`&`), `fragment` (`#…`), or `none`. Lets P2 compose a live URL deterministically. | `query` |
| `seed_query` | string \| null | ⬜ | The `sources_<cc>.yaml` query that surfaced this doc (traceability). | `"transfer" personal data outside Singapore` |
| `crawl_notes` | string \| null | ⬜ | Free text: replaced a dead URL, followed N redirects, hit anti-bot, etc. | `orig URL 404; used AGC replacement` |
| `publication_date` | string \| null | ⬜ | **(v0.2.0)** Date the law was published/gazetted, as shown on the portal (raw portal format). | `2010-06-10` |
| `assent_date` | string \| null | ⬜ | **(v0.2.0)** Royal assent / making date (MY "Royal Assent Date", AU register `makingDate`). | `2010-06-02` |
| `commencement_date` | string \| null | ⬜ | **(v0.2.0)** Commencement date or remark, as shown on the portal (may be a multi-jurisdiction remark). | `2013-11-15` |
| `in_force_status` | string \| null | ⬜ | **(v0.2.0)** Portal status, e.g. "In force" / "Current" / "Repealed". | `Current` |

`manifest.jsonl` carries the same fields plus a nested `http` object (`{status, redirect_chain[], headers{}}`) that would bloat the CSV.

> **v0.2.0 enrichment note:** the four fields above are optional and P2 does not need them for the SG slice. They partially close the "recovered metadata rides along" gap: MY dates now arrive on the manifest (~90% coverage) so P2 need not re-extract them, while SG dates remain null on the manifest (recover from the PDF text) and the 92 blank MY titles still come from the cover page.

### 2.3 How scanned vs native PDF vs HTML is recorded (the decision rule Project 1 must apply)

- **HTML** → `source_type=html`, `pdf_is_scanned=null`. Store the rendered HTML (Playwright DOM after JS) + `anchor_hint`/`anchor_kind` for deep-linking. HTML is the harder, higher-value differentiator — it must round-trip a working deep URL.
- **PDF, text extractable** → open with pypdfium2; if mean extractable chars/page ≥ threshold (default **100**) → `source_type=pdf_native`, `pdf_is_scanned=false`.
- **PDF, image-only / below threshold** → `source_type=pdf_scanned`, `pdf_is_scanned=true`. This is the flag that routes the doc into P2's OCR path and ultimately drives Deliverable #4 (scanned-PDF demo). Project 1 makes the *classification*; Project 2 makes the *quality measurement* (`ocr_quality_cer`, §3.5). A mis-flag is recoverable (P2 re-checks) but the field must always be present.

### 2.4 `anchor_hint` semantics (the working-URL contract)

`anchor_hint` stores the **complete portal-specific suffix**, not a bare fragment, so P2 can build a live deep-link by simple composition (§3.6). Two portal styles seen in scope:

- **Singapore SSO (query style):** `anchor_hint = "?ProvIds=pr26-"`, `anchor_kind = "query"`. Working URL = `base + "?ProvIds=pr26-"` (or `base + "&ProvIds=pr26-"` if `base` already has a query string — P2 handles the join per `anchor_kind`).
- **AU legislation.gov.au (fragment style):** `anchor_hint = "#sec.6"`, `anchor_kind = "fragment"`. Working URL = `base + "#sec.6"`.

The §2.2 example and the §3.3 worked example are aligned to `?ProvIds=pr26-`. A bare `#pr26-` fragment is **not** acceptable for SSO because SSO deep-links are query-driven, not fragment-driven.

### 2.5 Project 1 exit criteria for Hand-off #1

- `manifest.csv` + `manifest.jsonl` validate against a committed JSON Schema (`00_contracts/schemas/manifest.schema.json`); the `validate` CLI passes.
- **At least one `pdf_scanned` row exists across the retrieved set (any in-scope economy)** — this feeds the OCR item and Deliverable #4. The planned demo doc is a **Malaysia federal-gazette scan**; if none can be retrieved cleanly, P1 self-sources one scanned instrument (aligns with P2 §3.5 and the OCR-demo task). The scanned row need NOT be Singapore.
- Every row's `local_path` and `http_headers_path` resolve on disk; every `source_url` returns `http_status < 400` at retrieval time (else `crawl_notes` explains and, for HTML, an official replacement is preferred).
- `content_sha256` unique per distinct file (dedupe enforced).
- Every row carries `contract_version` matching the vendored `00_contracts` (§8).

---

## 3. HAND-OFF #2 — Project 2 → Project 3 (Provision-Records + source-text + law index)

Project 2 emits **three** artifacts that together form Hand-off #2. Project 3's entry points are **`provisions.jsonl`, `source_text/`, and `laws.jsonl`** (plus `handoff1/manifest.csv`, passed through for coverage — §7.2). It is not a single file.

### 3.1 Hand-off #2 directory spec

```
handoff2/
  provisions.jsonl              # one Provision-Record per article/provision (schema 3.2)
  by_law/
    <doc_id>.json               # provisions grouped per law (incl. laws with empty provisions[])
  source_text/
    <doc_id>.txt                # FROZEN normalized text the char offsets index into (schema 3.4)
  laws.jsonl                    # law-level COVERAGE index — one row per doc_id P2 processed (schema 3.7)
  extract_log.jsonl             # append-only: per-doc OCR/parse decisions, dropped-record reasons
```

- `source_text/<doc_id>.txt` is a **frozen, contract-level artifact**: the exact normalized text (post-OCR for scanned, extracted text for native, cleaned DOM text for HTML) that every `snippet_char_start/end` offset indexes into. P3 re-asserts `source_text[start:end] == verbatim_snippet` against **this file** (§3.4, §7). Without it the grounding offsets are meaningless, so it is part of the frozen seam.
- `laws.jsonl` exists so P3 can enumerate every governing law P2 processed — **including laws that yielded zero citable provisions** — and deterministically emit the mandatory "No provision found" rows (§4.2, §7.2). A law that P1 retrieved and P2 read but found nothing citable in still gets a `laws.jsonl` row with `provision_count: 0` and an empty `by_law/<doc_id>.json` `provisions[]` array.

### 3.2 GROUNDING RULE (non-negotiable): **no quote = no record.**
A Provision-Record MUST carry a `verbatim_snippet` that is a **character-exact substring of `source_text/<doc_id>.txt`**. Project 2 stores the character offsets and re-verifies the substring match before writing. If no faithful snippet can be produced, **no record is emitted** for that provision — but the law still appears in `laws.jsonl` so P3 can decide at the law level whether to write a "No provision found" row (that decision is P3's job, §4.2/§7.2, not P2's).

### 3.3 Provision-Record schema

| Field | Type | Required | Description | Example |
|---|---|---|---|---|
| `contract_version` | string (SemVer) | ✅ | Seam version; MAJOR-gated (§8). | `0.1.0` |
| `instrument_version` | string \| null | ⬜ | RDTII methodology tag (informational). | `2.1.0` |
| `provision_id` | string | ✅ | `<doc_id>#<article_section>` unique key. | `sg-pdpa2012-001#s.26(1)` |
| `doc_id` | string | ✅ | FK to Manifest row + `laws.jsonl`. | `sg-pdpa2012-001` |
| `economy` | enum `SG\|AU\|MY` | ✅ | Economy. | `SG` |
| `law_name` | string | ✅ | Authoritative law title (refined from `law_name_guess`). | `Personal Data Protection Act 2012` |
| `law_number` | string \| null | ✅ | Act/gazette ref. | `Act 26 of 2012` |
| `last_amended` | string (date/year) \| null | ✅ | Last amendment as printed in source. | `2021-02-01` |
| `article_section` | string | ✅ | Section incl. paragraph, RDTII citation style. | `s.26(1)` |
| `verbatim_snippet` | string | ✅ | **Exact** substring of `source_text/<doc_id>.txt`. No paraphrase. | `An organisation shall not transfer any personal data to a country or territory outside Singapore…` |
| `snippet_char_start` | int | ✅ | Offset into `source_text/<doc_id>.txt` where snippet begins (grounding proof). | `48213` |
| `snippet_char_end` | int | ✅ | Offset end. | `48532` |
| `location_reference` | string \| null | ✅ | Human locator: page N / anchor / part. | `Part VI, p.42` |
| `source_url` | string (URL) | ✅ | Deep URL to the provision (composed per §3.6). Working. | `https://sso.agc.gov.sg/Act/PDPA2012?ProvIds=pr26-` |
| `raw_context_before` | string | ✅ | ~200 chars preceding snippet (audit + LLM disambiguation). | `…Transfer of personal data outside Singapore 26.—` |
| `raw_context_after` | string | ✅ | ~200 chars following snippet. | `(2) The Minister may make regulations…` |
| **feature tags** | | | *extracted, not yet mapped* | |
| `scope` | enum `horizontal\|sectoral` | ✅ | Breadth of the instrument's application. | `horizontal` |
| `data_type` | enum `personal\|non-personal` | ✅ | What data the provision governs. | `personal` |
| `obligation_type` | enum (10 values, see below) | ✅ | Coarse obligation class covering **all 9 indicators** (feeds P3 prefilter, NOT the final score). | `conditional` |
| **provenance / audit** | | | | |
| `source_file_path` | string (rel) | ✅ | Raw file this came from — PDF **or** HTML (replaces the old `source_pdf_path`/undefined `source_html_path` split). Disambiguate kind via `source_type`. | `raw/sg/pdpa_2012/...native.pdf` |
| `source_type` | enum `html\|pdf_native\|pdf_scanned` | ✅ | Carried from Manifest. | `pdf_native` |
| `pdf_is_scanned` | bool \| null | ✅ | Carried from Manifest. | `false` |
| `ocr_quality_cer` | float \| null | ✅ | Measured CER vs the reference sample (§3.5); null if not OCR'd. Must be **< 0.05** on the demo doc to claim the OCR item. | `0.021` |
| `ocr_engine` | string \| null | ✅ | Engine + version if OCR'd, else null. | `tesseract-5.3.3-eng` |
| `retrieval_method` | enum `playwright\|requests\|api` | ✅ | Carried from Manifest. | `playwright` |
| `extraction_model` | string | ✅ | Model+version used for tag extraction (pinned). | `claude-sonnet-5-<pinned>` |
| `extraction_confidence` | float 0–1 | ⬜ | P2's self-reported tag confidence. | `0.86` |
| `access_date` | ISO-8601 | ✅ | Carried from Manifest. | `2026-07-09T10:32:00Z` |

**`obligation_type` enum (extended to cover Pillar 7 so the P3 prefilter has signal for all 9 indicators):**
`ban` (→P6-I1) · `storage` (→P6-I2) · `infrastructure` (→P6-I3) · `conditional` (→P6-I4) · `retention_minimum` (→P7-I3) · `dp_framework` (→P7-I1/I4) · `cybersecurity` (→P7-I2) · `dpia_dpo` (→P7-I4) · `gov_access` (→P7-I5) · `other`.
These are **descriptive hints for the prefilter only**; a single mapping is not implied and Project 3 alone assigns the indicator via the scoring trees.

> **Boundary note:** feature tags are *descriptive*, not the indicator score. `obligation_type=conditional` is a hint; Project 3 alone decides P6-I4 vs P6-I1 using the scoring trees (§4) — this preserves the P6-I4 consent/adequacy trap as P3's responsibility. Likewise `retention_minimum` is a hint; P3 alone applies the "do not keep longer than necessary is NOT 7.3" trap.

### 3.4 `source_text/<doc_id>.txt` (the grounding reference)

- Encoding UTF-8, LF newlines, no BOM. Whatever normalization P2 applies (whitespace collapse, de-hyphenation, OCR post-processing) is applied **once** and frozen here. Offsets are byte-agnostic **character** offsets into this exact string.
- P2's `validate` CLI asserts, for every record: `read(source_text/<doc_id>.txt)[start:end] == verbatim_snippet`. Mismatch = hard fail, record dropped, reason logged to `extract_log.jsonl`.
- P3 re-runs the same assertion as its intake gate; it never re-OCRs or re-parses raw files to reproduce offsets.

### 3.5 CER ground-truth definition (makes the 10-pt OCR claim verifiable)

CER is undefinable without a reference transcription, so the contract fixes one:

- A `fixtures/ocr_reference/` directory (committed in `rdtii-p2-extract/`) holds, for the demo scanned doc, a **ground-truth reference transcription** of a defined sample: either (a) a **native-text twin** of the same law/pages (e.g. the same gazette re-published as native PDF or HTML), or (b) a **manually transcribed sample page** (≥ 1 full page, ≥ 1500 chars) of the exact scanned file.
- `ocr_quality_cer` is the Levenshtein-based CER between P2's OCR output for that sample region and the committed reference — **measured on the reference sample, not the whole corpus.** The reference file, the sample-region offsets, and the CER computation are committed so a technical judge can recompute it.
- Records outside the sampled region inherit the doc-level CER for reporting; the **< 0.05 claim is made and proven on the reference sample.**

### 3.6 URL composition rule (P2)

P2 builds `source_url` deterministically from the Manifest: `source_url = compose(manifest.source_url, anchor_hint, anchor_kind)` where `compose` appends a `query` suffix with the correct `?`/`&` join, appends a `fragment` suffix directly, or returns the base unchanged for `none`. The result is HEAD-checked (`< 400`) before the record is written.

### 3.7 `laws.jsonl` schema (law-level coverage index — read by P3)

| Field | Type | Required | Description |
|---|---|---|---|
| `contract_version` | string | ✅ | Seam version. |
| `doc_id` | string | ✅ | FK to Manifest + Provision-Records. |
| `economy` | enum `SG\|AU\|MY` | ✅ | Economy. |
| `law_name` | string | ✅ | Authoritative title. |
| `law_number` | string \| null | ✅ | Act/gazette ref. |
| `source_url` | string (URL) | ✅ | Working law-level URL (for the "No provision found" row's citation). |
| `pillars_in_scope` | list `[6\|7]` | ✅ | Which pillars this law was searched against (from `pillar_hint`/`indicator_hints`). |
| `indicators_searched` | list of indicator IDs | ✅ | The in-scope indicator cells P2 searched this law for (enables P3's expected-cell enumeration, §7.2). |
| `provision_count` | int | ✅ | Number of Provision-Records emitted for this doc (may be `0`). |
| `searched` | bool | ✅ | True if P2 actually read/parsed the doc (vs skipped). |
| `notes` | string \| null | ⬜ | e.g. `read fully; no cross-border transfer provision present`. |

### 3.8 Worked example (Singapore PDPA s.26 — realistic)

```json
{
  "contract_version": "0.1.0",
  "instrument_version": "2.1.0",
  "provision_id": "sg-pdpa2012-001#s.26(1)",
  "doc_id": "sg-pdpa2012-001",
  "economy": "SG",
  "law_name": "Personal Data Protection Act 2012",
  "law_number": "Act 26 of 2012",
  "last_amended": "2021-02-01",
  "article_section": "s.26(1)",
  "verbatim_snippet": "An organisation shall not transfer any personal data to a country or territory outside Singapore except in accordance with requirements prescribed under this Act to ensure that organisations provide a standard of protection to personal data so transferred that is comparable to the protection under this Act.",
  "snippet_char_start": 48213,
  "snippet_char_end": 48532,
  "location_reference": "Part VI — Transfer of Personal Data Outside Singapore, p.42",
  "source_url": "https://sso.agc.gov.sg/Act/PDPA2012?ProvIds=pr26-",
  "raw_context_before": "Transfer of personal data to country or territory outside Singapore\n26.—(1) ",
  "raw_context_after": " (2) The Minister may make regulations to prescribe the requirements referred to in subsection (1).",
  "scope": "horizontal",
  "data_type": "personal",
  "obligation_type": "conditional",
  "source_file_path": "raw/sg/pdpa_2012/20260709T1032Z__native.pdf",
  "source_type": "pdf_native",
  "pdf_is_scanned": false,
  "ocr_quality_cer": null,
  "ocr_engine": null,
  "retrieval_method": "playwright",
  "extraction_model": "claude-sonnet-5-<pinned>",
  "extraction_confidence": 0.86,
  "access_date": "2026-07-09T10:32:00Z"
}
```

### 3.9 Project 2 exit criteria for Hand-off #2

- Every record validates against `00_contracts/schemas/provision.schema.json`; every `laws.jsonl` row validates against `laws.schema.json`.
- For every record, `source_text/<doc_id>.txt[snippet_char_start:snippet_char_end] == verbatim_snippet` (grounding assertion in the `validate` CLI). Any mismatch = hard fail, record dropped, reason logged.
- Every processed `doc_id` has a `laws.jsonl` row and a `by_law/<doc_id>.json` (even with empty `provisions[]`), and a `source_text/<doc_id>.txt`.
- The demo scanned doc carries a non-null `ocr_quality_cer` **< 0.05** measured against the committed reference sample (§3.5); its `ocr_engine` is pinned.
- Every `source_url` resolves (`< 400`); anchor deep-links composed per §3.6 where the portal supports them.
- Every record carries `contract_version` matching the vendored `00_contracts`.

---

## 4. Shared P0 INSTRUMENT — `indicators.yaml` + `sources_<cc>.yaml`

**Physical home:** `00_contracts/instrument/`. Each sub-project vendors a **pinned copy** at build time via `make sync-contracts` (a plain copy at a pinned SHA — not a submodule, §8.1). The versions (§8) are stamped into every Manifest and Provision-Record.

```
00_contracts/
  instrument/
    indicators.yaml            # the 9-indicator codebook + scoring trees (READ BY P3; hints for P1/P2)
    policies.yaml              # frozen policies: source hierarchy, citation contract, conflict rule, edge cases
    sources_sg.yaml            # SG portal/regulator registry + seed URLs + vocabulary queries (all 9 indicators)
    sources_au.yaml
    sources_my.yaml
  schemas/
    manifest.schema.json       # Hand-off #1
    provision.schema.json      # Hand-off #2 (Provision-Record)
    laws.schema.json           # Hand-off #2 (law coverage index)
    final_record.schema.json   # Project 3 output (13-col CSV + JSON), incl. No-provision variant (§4.2)
  config_template/             # the shared P7 config/ package + .env.example (§5)
  CONTRACT_VERSION             # SemVer seam version, e.g. 0.1.0 (see §8)
```

**Who reads what:**
- **Project 1** reads `sources_<cc>.yaml` (portal roots, gazette/regulator URLs, seed laws, seed queries) — its crawl frontier. Ignores scoring trees.
- **Project 2** reads `indicators.yaml` *disambiguation/keywords* only as **article-boundary + feature-tag hints** (vocabulary that suggests `obligation_type`). It does **not** score.
- **Project 3** reads the full `indicators.yaml` scoring trees + `policies.yaml` — its rulebook for mapping, coding, conflict resolution, and the "No provision found" edge case.

### 4.1 `indicators.yaml` layout (per-indicator schema)

```yaml
instrument_version: "2.1.0"                 # RDTII methodology tag — INFORMATIONAL, not the seam version
methodology_source: "RDTII 2.1 Methodology sheet"
WARNING_DO_NOT_USE: >
  The OUTPUT_TEMPLATE_31MAY.xlsx 'Indicator Reference' tab is WRONG (GDPR-style taxonomy).
  It mislabels P6-I1 as 'General prohibition', P6-I2 'Adequacy standard',
  P6-I3 'Contractual safeguards', P6-I4 'Consent exception', P7-I1 'Legal basis for
  processing', etc. IGNORE it. Only the definitions below are authoritative.

indicators:
  - id: P6-I1
    pillar: 6
    name: "Ban & local processing"
    question: "Is transfer banned / must data be processed locally?"
    scoring: {values: [1, 0.5, 0], type: ordinal}
    scoring_tree:
      - if: "transfer of personal data outside the economy is prohibited outright, OR data must be processed only locally"
        score: 1
      - if: "partial / sector-limited ban or local-processing requirement"
        score: 0.5
      - else: {score: 0}
    coding_rules:
      - "Applies to personal (and where relevant non-personal) data held by private organisations."
    exceptions:
      - "Do NOT score data-localization applied to GOVERNMENT data. (applies to all of P6-I1..P6-I4)"
    disambiguation:
      - "TRAP: consent/adequacy conditions are P6-I4 (conditional), NOT a P6-I1 ban."
```

The nine in-scope indicators, verbatim-correct, populate this file:

- **P6-I1 Ban & local processing** — *is transfer banned / must data be processed locally?* Scores **1 / 0.5 / 0**.
- **P6-I2 Local storage** — *must a COPY be stored domestically (transfer may still be allowed)?* **1 / 0.5 / 0**.
- **P6-I3 Infrastructure** — *are local servers/data centres required to supply the service?* **1 / 0**.
- **P6-I4 Conditional flow** — *transfer allowed only if consent/adequacy/contract/approval?* **1 / 0.5 / 0**. **TRAP: consent/adequacy = P6-I4 conditional, NOT a P6-I1 ban.**
- **Exception for all of P6-I1..P6-I4:** do **NOT** score data-localization applied to **GOVERNMENT** data.
- **P7-I1 Comprehensive DP framework (horizontal law?)** — **1 = none / 0.5 = sectoral only / 0 = comprehensive**. (Inverted polarity — higher score = less protection.)
- **P7-I2 Dedicated cybersecurity framework** — **1 / 0.5 / 0**.
- **P7-I3 Minimum data-retention** — *rule requiring data kept AT LEAST N period?* **1 / 0**. **TRAP: "do not keep longer than necessary" is NOT 7.3.**
- **P7-I4 DPIA/DPO duty** — **1 = all sectors / 0.5 = specific / 0 = none**.
- **P7-I5 Government access to personal data (esp. without court order)** — **1 / 0**. Look beyond privacy law → criminal procedure, surveillance, telecom.

Scope reminder encoded at top of file: **Pillars 6 & 7 only; 6.5 OUT; 7.5 IN.**

Two fields added for the finale roll-up (instrument decision D17, 4 October 2026). Neither is
rendered into the mapping prompt. Their values are kept in
stages/p0-instrument/scripts/data/rollup_fields.yaml and written by build_rollup_fields.py.

```yaml
    absence_score: 0            # on every block. The score of a cell when the corpus was
                                # searched and no qualifying provision was found: one of the
                                # block's scoring.values, or null = leave the cell unscored.
    absence_basis: "..."        # why, with the host source
    count_rule:                 # only on blocks that score by how many measures an economy has
      unit: measure             # what the host criterion counts: measure | sector | company |
                                # product | procedure
      counts: "..."             # the same, in words
      counted_as: law           # what stands in for the unit today: distinct laws
      method: threshold         # threshold | sum
      counted_scores: [0.5]     # a law counts when its highest verified score is one of these
      thresholds:               # method threshold: the highest threshold met gives a score
        - {at_least: 2, score: 1}
      cap: 1                    # method sum only: add the laws' scores and stop here
      otherwise: highest_verified_score
      needs: []                 # facts a verdict would have to carry to count the unit exactly:
                                # a list of {fact, why}
      basis: "..."              # the host rule, cited
```

How a rule is applied: for one economy and one indicator, take each law's highest verified
score. With method threshold, count the laws whose score is one of counted_scores; the cell
takes the higher of the threshold's score and the highest single verified score. With method
sum, add the laws' scores and stop at cap. A rule never lowers a cell.

### 4.2 `policies.yaml` (frozen policies read by Project 3)

```yaml
source_hierarchy: [statute, regulation, guidance, tracker]   # LEGAL AUTHORITY: statute > regulation > guidance > tracker
citation_url_preference:        # WHERE to fetch/cite the Source URL (distinct axis from legal authority)
  - official_statutes_portal              # SG sso.agc.gov.sg · AU legislation.gov.au
  - official_regulator_or_agency_site     # e.g. pdpc.gov.sg, oaic.gov.au, pdp.gov.my, mcmc.gov.my
  - official_gazette_scan                 # MY lom.agc.gov.my / federalgazette (often scanned)
  - whitelisted_reputable_secondary       # MALAYSIA LAST RESORT ONLY; flag in Notes; never for SG/AU
conflict_rule: "lex specialis — the more specific instrument governs when two conflict"
citation_contract:
  requires: [verbatim_snippet, article_section_with_paragraph, working_source_url]
  rule: "every SUBSTANTIVE output row MUST carry all three; missing any => not audit-valid"
edge_cases:
  no_provision_found:
    rule: 'write a row per (governing law × searched in-scope indicator) that yielded nothing; never blank'
    row_shape: 'Verbatim Snippet=\"No provision found\"; Article/Section=\"n/a\"; cite governing law (name+number+working law-level URL) and reason in Notes'
    schema_variant: 'validated by the No-provision branch of final_record.schema.json (§6) — verbatim/section/anchor relaxed, governing-law citation + reason REQUIRED'
  repealed: "do not record; or set Notes=repealed/superseded"
  broken_url: "flag in Notes; prefer official replacement URL"
  same_provision_two_indicators: "emit two rows"
  one_indicator_many_laws: "separate rows, cross-referenced in Notes"
  sectoral_and_horizontal: "record both; authority = who enacted it, not breadth"
  bad_country_input: "must not crash; skip with logged warning"
```

### 4.3 `sources_<cc>.yaml` — MUST cover all 9 in-scope indicators per economy

**Seeded from the provided host files (not hand-curated).** `sources_<cc>.yaml` is populated directly from `Knowledge Portal/Resource Library/Sample governemnt portals_Pillar 6_7.csv` + the Round 1 baseline DB — the near-complete KNOWN law→URL map for SG/AU/MY. Per-country source strategy, grounded in those files:
- **Singapore & Australia — one official portal each is sufficient.** SG: `sso.agc.gov.sg` + regulators `pdpc.gov.sg`, `imda.gov.sg`. AU: `legislation.gov.au` + `oaic.gov.au`, `cyber.gov.au`, `homeaffairs.gov.au`. Every in-scope law sits on the official portal; crawl official only.
- **Malaysia — a *federation* of official sites, not one portal.** No consolidated free official statutes portal exists; laws are scattered across official agency sites (`pdp.gov.my`, `mcmc.gov.my`, `bnm.gov.my`, `ssm.com.my`, `customs.gov.my`, `miti.gov.my`, `hasil.gov.my`) + the federal gazette (`lom.agc.gov.my`/`federalgazette.agc.gov.my`, often scanned). The host's own baseline cites several MY acts (PDPA 709, Cyber Security Act 854, Criminal Procedure Code, Security Offences Act) from **non-government** copies (university/NGO/law-firm) because no official online copy is reachable — so MY carries a **narrow whitelisted reputable fallback** per the citation hierarchy (§4.2), flagged in Notes. Third-party sites are a last-resort *fetch* fallback, never a discovery crawl target.

**Mandate:** every `sources_<cc>.yaml` carries `seed_laws` + `seed_queries` whose union covers **all nine in-scope indicators**, not just data-protection/privacy. Otherwise P7-I2 (cybersecurity) and P7-I5 (government access) have no crawl frontier and silently score zero for lack of retrieval. A CI check asserts each in-scope indicator ID appears in at least one seed law's `indicators` list or one `seed_queries` bucket.

```yaml
economy: SG
portals:
  primary_statutes:
    name: "Singapore Statutes Online"
    root: "https://sso.agc.gov.sg"
    crawl_style: "playwright"          # JS + anti-bot
  gazette: null
  regulators:
    - {name: "PDPC", root: "https://www.pdpc.gov.sg"}
    - {name: "CSA", root: "https://www.csa.gov.sg"}      # cybersecurity → P7-I2
seed_laws:                              # known targets; each tags the indicators it feeds
  - {law_name: "Personal Data Protection Act 2012", url: "https://sso.agc.gov.sg/Act/PDPA2012",
     indicators: [P6-I1, P6-I2, P6-I3, P6-I4, P7-I1, P7-I3, P7-I4]}
  - {law_name: "Cybersecurity Act 2018", url: "https://sso.agc.gov.sg/Act/CA2018",
     indicators: [P7-I2]}                                                       # P7-I2 frontier
  - {law_name: "Criminal Procedure Code 2010", url: "https://sso.agc.gov.sg/Act/CPC2010",
     indicators: [P7-I5]}                                                       # P7-I5 frontier
  - {law_name: "Telecommunications Act 1999", url: "https://sso.agc.gov.sg/Act/TA1999",
     indicators: [P7-I5]}                                                       # lawful-interception → P7-I5
seed_queries:                          # vocabulary-seeded, per indicator group
  P6-I1_I4: ['"transfer" personal data outside Singapore', '"data localization"', 'cross-border transfer limitation', 'consent adequacy transfer']
  P6-I2:    ['copy stored in Singapore', 'local storage requirement']
  P6-I3:    ['local server data centre requirement']
  P7-I1_I4: ['data protection officer appointment', 'data protection impact assessment', 'breach notification']
  P7-I2:    ['cybersecurity', 'critical information infrastructure', 'computer misuse']
  P7-I3:    ['retention period', 'retain for a period of not less than']
  P7-I5:    ['lawful interception', 'access to computer data by authority', 'surveillance without warrant', 'production order']
```

- `sources_au.yaml` marks `legislation.gov.au` as **HTML-heavy** (`crawl_style: playwright`, deep-anchor `fragment` capture required) and seeds the same 9-indicator coverage: Privacy Act 1988 (P6/P7-I1/I4), Security of Critical Infrastructure Act / relevant cyber framework (P7-I2), Telecommunications (Interception and Access) Act 1979 + criminal-procedure/surveillance instruments (P7-I5).
- `sources_my.yaml` models the **federation**: official agency hosts (`pdp.gov.my`, `mcmc.gov.my`, `bnm.gov.my`, `ssm.com.my`, `customs.gov.my`, `miti.gov.my`, `hasil.gov.my`) + gazette (`lom.agc.gov.my` / `federalgazette.agc.gov.my`, flagged `expect_scanned: true` so Project 1 biases toward capturing the image PDF for the OCR item and Deliverable #4) + a small explicit `reputable_fallback:` allow-list for acts with no reachable official copy. Seeds cover all 9 indicators: PDPA 2010 (P6/P7-I1/I4), Cyber Security Act 854 2024 (P7-I2), Criminal Procedure Code / Security Offences (Special Measures) Act (P7-I5).

---

## 5. Shared CONFIG / MODEL-SWAP layer (P7) — earns the 15-pt modular backend

One config layer, **shared by Projects 2 and 3** (both run LLM/document-AI pipelines — do not duplicate). Physical form: an identical `config/` package + `.env.example` vendored into both `rdtii-p2-extract/` and `rdtii-p3-map/`, sourced from `00_contracts/config_template/`. Project 1 uses only the crawler-relevant keys.

**Constraint alignment:** CPU-only; NO API key shipped (reviewer supplies own via `.env`); every model-bearing stage swappable by a **config VALUE, not a rewrite**; open-weight fallback required (Ollama, already installed on the eval box).

### 5.1 `.env` keys

| Key | Purpose | Default | Fallback / notes |
|---|---|---|---|
| `LLM_PROVIDER` | Which mapping/extraction backend | `anthropic` | `ollama` (open-weight, offline) |
| `LLM_MODEL` | Pinned model id | `claude-sonnet-5-<pinned>` | `qwen2.5:14b` / `llama3.1:8b` for Ollama; `claude-opus-4-8` for hard cases |
| `ANTHROPIC_API_KEY` | Reviewer-supplied key | *(empty — reviewer fills)* | absent ⇒ auto-fall back to `ollama` |
| `OLLAMA_HOST` | Local LLM endpoint | `http://localhost:11434` | — |
| `OCR_ENGINE` | Scanned-PDF OCR backend | `tesseract` | `paddleocr` → `azure_docint` / `mistral_ocr` (cloud, hardest gazettes) |
| `OCR_LANG` | OCR language | `eng` | — |
| `AZURE_DOCINT_KEY` / `AZURE_DOCINT_ENDPOINT` | Cloud OCR (optional) | *(empty)* | only if `OCR_ENGINE=azure_docint` |
| `EMBED_MODEL` | Dense prefilter (P3) | `BAAI/bge-m3` | any sentence-transformers model; CPU |
| `PREFILTER_SPARSE` | Sparse prefilter | `bm25` | rank_bm25 |
| `MAX_COST_USD_PER_DOC` | Cost guardrail | `0.25` | feeds cost instrumentation (§6) |
| `CONTRACT_VERSION` | Pinned **seam/schema** version | `0.2.0` | must match vendored `00_contracts` (§8); MAJOR-gated |

> `instrument_version` (`2.1.0`, the RDTII methodology tag) is a separate, **informational** value read from `indicators.yaml`; it is not a `.env` key and is NOT the version the compatibility gate compares. Only `CONTRACT_VERSION` is gated (§8).

### 5.2 Provider-interface pattern (config-swap, no rewrite)

```
config/
  settings.py            # loads .env, validates, exposes typed Settings object
  llm/
    base.py              # class LLMClient(ABC): def complete(prompt, schema) -> dict
    anthropic_client.py  # default; uses anthropic SDK, structured output
    ollama_client.py     # open-weight fallback; same interface
    factory.py           # get_llm(settings) -> LLMClient   (dispatch on LLM_PROVIDER)
  ocr/
    base.py              # class OCREngine(ABC): def to_text(pdf_path) -> (text, cer|None)
    tesseract_engine.py  # default
    paddle_engine.py
    azure_engine.py
    factory.py           # get_ocr(settings) -> OCREngine
  embed/
    factory.py           # get_embedder(settings)
```

Both P2 and P3 call `get_llm(settings)` / `get_ocr(settings)` — never instantiate a vendor SDK directly. Structured output goes through one `complete(prompt, schema)` signature so swapping Claude↔Ollama is a **`.env` edit**. If `ANTHROPIC_API_KEY` is empty at startup, `factory` auto-selects `ollama` and logs it — guaranteeing the no-key, CPU-only, end-to-end run the rubric demands.

**`model_version` composition (conditional — do not misstate provenance).** The audit `model_version` field is:
```
model_version = LLM_MODEL + ("+" + ocr_engine  if record was actually OCR'd (ocr_quality_cer is not null)  else "")
```
So an HTML or native-PDF record (never OCR'd) reports e.g. `claude-sonnet-5-<pinned>` with **no** OCR component; only a genuinely OCR'd scanned record reports `claude-sonnet-5-<pinned>+tesseract-5.3.3-eng`. The OCR component is recorded as `null`/omitted when `ocr_quality_cer` is null.

### 5.3 CLI signatures (uniform across the three repos)

```
# Project 1
p1-scrape crawl    --economy SG --pillars 6,7 --out handoff1/            [--seed-laws-only]
p1-scrape validate --manifest handoff1/manifest.csv

# Project 2
p2-extract run      --manifest handoff1/manifest.csv --raw handoff1/ --out handoff2/
p2-extract validate --provisions handoff2/provisions.jsonl --source-text handoff2/source_text/ --laws handoff2/laws.jsonl

# Project 3  (consumes the Manifest for coverage — see §7.2)
p3-map run      --provisions handoff2/provisions.jsonl --laws handoff2/laws.jsonl \
                --source-text handoff2/source_text/ --manifest handoff1/manifest.csv \
                --baseline <path | proxy:rdtii_public | NONE> --out out/
p3-map validate --csv out/records.csv
p3-map reconcile --baseline <path | proxy:rdtii_public> --out out/     # POST-SLICE / stretch (§7.1, §8.1)
```

Every `run` also emits `<out>/cost_report.json` (measured per-document cost, tokens, wallclock) → cost-efficiency rubric item.

**Reviewer re-run expectation (set explicitly, avoids a false "divergence" mark):** the **committed Deliverable #2 CSV/JSON is produced with the pinned Claude model** (`LLM_MODEL=claude-sonnet-5-<pinned>`). The Ollama CPU path (`qwen2.5:14b` / `llama3.1:8b`) is a **resilience fallback**, not an accuracy-equivalent one: on CPU it is materially slower and materially weaker on the indicator traps (P6-I4 consent/adequacy vs P6-I1 ban; the P7-I3 "longer than necessary" exclusion). The README states this and instructs a judge's hold-out re-run to compare against the Claude-generated showcase with an expected accuracy/latency delta — parity is **not** claimed.

---

## 6. OWNERSHIP MATRIX — every scored item to exactly one owner

| Rubric item | Pts | Owner (single enforcer) | Contract touchpoint |
|---|---|---|---|
| Live portal crawling (0-or-10) | 10 | **Project 1** | Manifest `retrieval_method`, `http_*`, `crawl_log.jsonl` prove live crawl |
| OCR on scanned PDFs (<5% CER) | 10 | **Project 2** | `ocr_quality_cer < 0.05` vs committed reference sample (§3.5), `ocr_engine` in Provision-Record |
| End-to-end, no manual steps | — (part of Tech Resilience 30) | **P0/integration role (John)** | `run_slice` chains the 3 CLIs + no-key auto-fallback (§5); authored per §7.3 checklist |
| Framework alignment (correct indicator) | ~10 | **Project 3** | `indicators.yaml` scoring trees; blind-verify step |
| Discovery of NEW evidence | **20** | **Project 3** | `Discovery Tag` col; baseline diff (§7.1 graceful degrade; proxy avoids over-claiming) |
| Citation fidelity (article+¶, working URL, verbatim) | ~10 | **Project 3** (enforcer) using P2 fields | P2 produces `verbatim_snippet`+offsets+`source_url`; P3 validates + writes cols 6/9/11 |
| Modular backend (config-swap LLM/OCR) | 15 | **Shared P7**, enforced by **Project 2** `config` tests | `config/` factory + `.env` (§5); consumed by P2 & P3 |
| Audit trail (verbatim+locator+URL every row) | 15 | **Project 3** (using P2 fields) | `final_record.schema.json` rejects any *substantive* row missing the three; No-provision variant (below) |
| Cost-efficiency (measured) | — (part of Architecture 30) | **Project 3** (aggregates); P1/P2 emit per-stage | `cost_report.json` per stage → P3 consolidates real per-doc cost |
| Differentiator: PDF **and** HTML | (folds into crawl + citation) | **Project 1** (retrieve both) + **Project 2** (parse both) | `source_type` distinguishes; HTML deep-anchor URL preserved (§2.4/§3.6) |

No item is orphaned; no item is double-owned; **every row names a single enforcing owner** (the no-manual-steps item now names John, closing the prior "Shared, no enforcer" gap).

**`final_record.schema.json` — two validated variants (resolves the No-provision ↔ audit-trail collision):**
- **Substantive row:** cols 6 (Article/Section w/ paragraph), 9 (Verbatim Snippet), 11 (working Source URL) all REQUIRED and non-placeholder — the audit trio.
- **No-provision row** (detected when col 9 == `"No provision found"` / Notes flags it): the verbatim/section/anchor requirements are **relaxed** (col 6 = `n/a`, col 9 = `No provision found`), but a **governing-law citation (name + number + working law-level URL from `laws.jsonl`) + a reason in Notes are REQUIRED.** This lets the mandated edge-case row validate instead of being rejected or filled with a fake snippet.

---

## 7. INTEGRATION for the Singapore vertical slice

**Wiring approach: documented file hand-off between folders, orchestrated by one thin top-level runner** (not a monorepo import). The three folders stay independent; a repo-root script sequences their CLIs and passes directories.

```
RDTII Plan/
  00_contracts/            # vendored (copied) into each below at a pinned SHA
  rdtii-p1-scrape/
  rdtii-p2-extract/
  rdtii-p3-map/
  run_slice.ps1                    # primary top-level runner (the "no manual steps" proof)
  run_slice.sh                     # generated only if trivial; else README documents WSL/bash invocation
  handoff1/  handoff2/  out/       # created by the run
```

`run_slice` (pseudocode of the seam, not implementation):
```
p1-scrape crawl    --economy SG --pillars 6 --seed-laws-only --out handoff1/
p1-scrape validate --manifest handoff1/manifest.csv                     # gate: schema + URLs live
p2-extract run      --manifest handoff1/manifest.csv --raw handoff1/ --out handoff2/
p2-extract validate --provisions handoff2/provisions.jsonl --source-text handoff2/source_text/ --laws handoff2/laws.jsonl
p3-map run      --provisions handoff2/provisions.jsonl --laws handoff2/laws.jsonl \
                --source-text handoff2/source_text/ --manifest handoff1/manifest.csv \
                --baseline proxy:rdtii_public --out out/                # proxy KNOWN set — see below
p3-map validate --csv out/records.csv                                  # gate: 13-col + audit trio / No-provision variant
```
Each `validate` is a **hard gate**: the runner stops if a hand-off fails its schema, so a broken seam surfaces immediately (the #1 integration risk). Windows note: the runner ships as `.ps1`; the README's Quick Start invokes Python via `py -3` / the resolved interpreter path because Python is not reliably on PATH (only the MS Store stub) — the setup script installs into a venv and records the absolute interpreter path.

**The showcase runner uses `--baseline proxy:rdtii_public`, NOT `--baseline NONE`.** Singapore PDPA s.26 cross-border transfer is the single most canonical **KNOWN** baseline provision; force-tagging it `NEW` (which `--baseline NONE` does, §7.1) would over-claim the 20-pt lever and read as a credibility error to a policy judge. Against the public-RDTII proxy, s.26 correctly tags **KNOWN**. `--baseline NONE` is retained only as a plumbing/smoke-test mode, never the demo output.

**Slice success = one row in `out/records.csv`:** SG · PDPA 2012 · Act 26/2012 · s.26(1) · **P6-I4** · **Discovery Tag = KNOWN** · verbatim snippet · working SSO deep URL (`?ProvIds=pr26-`) · rationale ≤300 chars. That single row exercises all three folders, both hand-offs, both shared spines, and 6 of the scored items. NEW is reserved for genuinely novel clauses surfaced beyond the proxy KNOWN set — it is not asserted on this canonical row.

### 7.1 NEW/KNOWN graceful degradation while the baseline DB is missing

The Round 1 SG/AU/MY baseline **is now in hand** — `Knowledge Portal/Database/ESCAP-RDTII-2.1_ Round 1 Database.xlsx` (sheets: Consolidated · Singapore · Australia · Malaysia). `--baseline <path>` to this real DB is the **primary** target for NEW/KNOWN + the Malaysia error-check. The modes below are retained as documented fallbacks so Project 3 never *blocks* on baseline availability (offline runs, or a refreshed baseline):

- `--baseline <path>` (**the default for real output now that the Round 1 DB is in hand**) diffs against the real SG/AU/MY baseline at provision level. `proxy:rdtii_public` (public RDTII database) remains an offline/no-file **fallback** stand-in KNOWN set, still useful when the real file is unavailable and to keep canonical provisions tagging KNOWN rather than over-claiming NEW.
- `--baseline NONE` (empty `baseline/`) ⇒ every mapped provision is tagged **`NEW`** with `Notes: "candidate-NEW — baseline unavailable; pending reconciliation"` and a lower `Confidence`. This is a **plumbing-test mode only**, not the demo output.
- When the real baseline arrives, `p3-map reconcile --baseline <path>` re-diffs at **provision level** (a new clause inside a baseline law still counts NEW) and rewrites `Discovery Tag` + `Confidence` **without** re-running P1/P2 — a pure post-process over `handoff2/` + `out/`. (Marked **post-slice/stretch**, §8.1.)
- **Malaysia error-check target set (double-weighted, must not block):** the target is the Round-1 baseline MY entries. Because those are not in hand and may never arrive, **the concrete fallback target is the public RDTII MY entries** (`proxy:rdtii_public`, MY subset). `p3-map reconcile --baseline proxy:rdtii_public` runs the MY error-check against that proxy: retrieved MY provisions that contradict a proxy MY entry are flagged in `Notes` (`error-check: contradicts baseline entry <ref>`). This keeps the double-weighted MY deliverable executable on an input that is guaranteed available.

### 7.2 How Project 3 emits "No provision found" deterministically (closes the coverage gap)

P3 consumes provision-records **plus** `laws.jsonl` **plus** `handoff1/manifest.csv`, so it can tell "law searched, nothing citable" from "law never retrieved":

1. **Expected cells** = for each `laws.jsonl` row, the cross-product of its `pillars_in_scope`/`indicators_searched` × the in-scope indicators for that pillar.
2. **Filled cells** = every `(doc_id, indicator)` P3 actually mapped from `provisions.jsonl`.
3. **Empty searched cells** (expected − filled, where `searched=true`) ⇒ emit a **"No provision found"** row citing that law's `law_name` + `law_number` + law-level `source_url` and the reason from `laws.jsonl.notes`. Validated by the No-provision schema variant (§6).
4. **Manifest cross-check:** any Manifest `doc_id` with `indicator_hints` that has **no** `laws.jsonl` row surfaces a loud warning ("retrieved but not processed by P2") — this catches a dropped hand-off rather than silently under-reporting coverage.

### 7.3 Integration checklist (owned by John, the P0 role — the no-manual-steps enforcer)

- [ ] Author `run_slice.ps1` chaining the six CLI calls above with each `validate` as a hard gate (exit-non-zero stops the run). **Exit criterion:** a clean checkout runs `run_slice.ps1` to one validated row with zero manual steps.
- [ ] Generate `run_slice.sh` only if trivial; otherwise document the bash/WSL invocation in the README. **Exit criterion:** a non-Windows judge has one documented path to run.
- [ ] Author `make sync-contracts` (copy `00_contracts/` at a pinned SHA into each sub-repo) and record the pinned SHA + `CONTRACT_VERSION` in each README. **Exit criterion:** all three repos report the same `CONTRACT_VERSION`.
- [ ] Wire the no-key auto-fallback smoke test (empty `ANTHROPIC_API_KEY` ⇒ Ollama path logs + runs). **Exit criterion:** end-to-end run completes with no key set.

---

## 8. Contract versioning + compatibility

The three repos evolve independently, so the contracts are **versioned artifacts**, not ambient assumptions. **Two distinct version strings — do not conflate them:**

- **`CONTRACT_VERSION`** (SemVer, starts at **`0.1.0`**) — the **seam/schema** version covering *jointly* the schemas (`manifest`, `provision`, `laws`, `final_record`), `policies.yaml`, and the config template. It is **stamped into every Manifest row, every Provision-Record, every `laws.jsonl` row, and every final JSON**, and it is the **only** value the compatibility gate compares.
- **`instrument_version`** (currently **`2.1.0`**) — the **RDTII 2.1 methodology tag** from `indicators.yaml`. **Informational only**: carried alongside for provenance, but **never** MAJOR-gated. (This prevents the prior contradiction where a record stamped `2.x` was checked against a build expecting `0.x` and always tripped the gate.)

Both may appear in a record; `validate` CLIs gate on `CONTRACT_VERSION` **only**.

- **Vendoring, not live coupling:** each sub-project pins a **copy** of `00_contracts/` via `make sync-contracts` at a pinned SHA (not a git submodule — §8.1). A repo declares the `CONTRACT_VERSION` it was built against in its README + `config`. This satisfies the pinned-dependency hard constraint (no "latest") and lets P1 ship before P3 is finished.
- **Bump rules (on `CONTRACT_VERSION`):**
  - **PATCH** — clarification, added optional field, doc fix. Fully backward-compatible.
  - **MINOR** — new **required** field with a defined default, or a new enum value. Producers upgrade first; consumers tolerate via schema `additionalProperties` + defaulting.
  - **MAJOR** — renamed/removed field, changed type, reordered CSV columns, or changed indicator scoring semantics. Requires all three repos to re-pin in lockstep. **The 13-column CSV order and the 9 indicator definitions are frozen — any change there is MAJOR and must be avoided before 20 July.**
- **Compatibility gate:** each `validate` CLI checks `CONTRACT_VERSION` **major** compatibility between the file it reads and its own pinned contract, refusing to proceed on a major mismatch with a clear error — e.g. `"Manifest is contract 1.x; this build expects 0.x — re-sync 00_contracts"`. This turns silent seam drift into a loud, early failure — directly mitigating the stated #1 integration risk. (**Deferred to post-slice/stretch per §8.1**; the slice itself relies on the schema `validate` gates, which are not deferred.)
- **Amendment process:** any change to this document or a schema is a change against `00_contracts/` that bumps `CONTRACT_VERSION` and notes the affected hand-off; the three sub-project READMEs record the version they target. Until an amendment merges, this document is authoritative.

### 8.1 Timeline triage — what ships for the slice vs what is stretch (11-day solo, ~75% time)

The infra must not out-compete the 40% substantive-accuracy work it exists to support. Explicit cut line:

| Machinery | Decision | Rationale |
|---|---|---|
| `00_contracts` vendoring | **Copy** via `make sync-contracts` at pinned SHA — **NOT** git submodules | Copy is a one-line pin; submodules add ceremony that earns no points. |
| Top-level runner | **One** runner (`run_slice.ps1`); `.sh` only if trivial | The no-manual-steps proof needs one working path; document the other. |
| Schema `validate` gates (manifest/provision/laws/final_record) | **Ship for the slice** | These *are* the audit-trail + seam-safety points; not discretionary. |
| CER reference sample + OCR demo | **Ship for the slice** | 10-pt OCR item + Deliverable #4 depend on it. |
| `sources_<cc>.yaml` 9-indicator coverage | **Ship** (SG first, then AU/MY) | Missing frontiers = silent zeros on P7-I2/I5. |
| `CONTRACT_VERSION` MAJOR-compat gate | **Post-slice/stretch** | Schema validation already catches seam breaks in a single-builder repo; the version gate hardens later. |
| `p3-map reconcile` (NEW/KNOWN + MY error-check re-diff) | **Post-slice/stretch** | `proxy:rdtii_public` at `run` time already yields correct KNOWN/NEW + MY error-check; `reconcile` only matters once the real baseline arrives. |
| Per-stage cost instrumentation | **Ship a minimal `cost_report.json`** (tokens + wallclock + per-doc USD); skip elaborate dashboards | The rubric wants a *measured* number, not tooling. |

**Protected over all of the above, in order:** the Singapore vertical slice → live crawl (10 pts) → NEW-evidence lever (20 pts) → audit trail (15 pts). Any stretch item is dropped before any protected item slips.

---

## 9. Cross-cutting: transparent logging & how the logic is presented

**Transparency is earned by *showing the reasoning*, not by a UI.** What a judge rewards is per-row auditability + a legible run — not a dashboard. Two rules bind all three sub-projects.

### 9.1 Transparent stage logging (every CLI)
Every `run` streams a human-readable, stage-by-stage narration to **stdout** and mirrors a structured copy to **`logs/run_<ts>.jsonl`**, so a technical judge watching the terminal sees the pipeline think:
```
[P1] crawl SSO → PDPA 2012 (pdf_native, 200) → anchor ?ProvIds=pr26- → manifest sg-pdpa2012-001
[P2] segment → 47 articles → s.26(1) span[48213:48532] grounded ✓
[P3] prefilter s.26(1) → P6-I4 (RRF 0.71) → map: fires P6-I4 (conditional, not ban) → verify: agree → row written
```
Rules: one line per meaningful decision; name the **why** (which branch/disqualifier fired), not just the what; never dump raw prompts; readable at a glance. This is the backbone of the no-manual-steps story and the live demo (engine visible, reasoning streaming — "not a slide show").

### 9.2 Presenting the logic — deck · video · per-row audit (NOT a dashboard, for Round 1)
Round 1 has **no scored UI item**; the graded artifacts are the CSV (policy judge, in Excel), the CLI+JSON (technical judge), and the audit trail (15 pts). So "make the workflow clear" effort goes where it is already required and scored:
- **Per-row audit trail** — `Mapping Rationale` + verbatim snippet + `raw_context` + verifier verdict = the logic, inspectable per row in Excel (P3, §6).
- **Transparent stage logs** (§9.1).
- **Pitch-deck workflow diagram** (Deliverable #3) — the place to draw crawl→OCR→extract→prefilter→map→verify→cite, tracing a real example (SG PDPA s.26 → P6-I4).
- **≤10-min walkthrough video** (Deliverable #4) — the workflow shown live on a scanned PDF.

The optional static **`results.html`** (P3 `audit/index.html`) is a *view over `records.json`* — fully inlined, offline-safe, no server, never runs the pipeline behind a button. A **full interactive dashboard is DEFERRED to the Finale (Stage 3)**, where interface/deployment is weighted ~70%; in Round 1 it earns nothing and must not compete with the scored pipeline in the 11-day window.
