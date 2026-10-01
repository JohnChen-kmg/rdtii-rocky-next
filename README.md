# RDTII Rocky — AI Tool for Digital Trade Regulatory Analysis

UN Global Hackathon on AI for Digital Trade Regulatory Analysis
Team: **Rocky has a home run** | Round: **Final**
Last updated: 2026-10-01

> **Final round requirement.** Every section below is mandatory. This README is part of the submission
> and is read during the desk review — it is the front door to criterion **C4a, Technical Handover**.

---

## What This Tool Does

This tool automates two tasks required by the ESCAP Regional Digital Trade Integration Index (RDTII 2.1):

**Task 1 — Automated Evidence Discovery**
Given an economy and a pillar, the tool crawls official government legal portals politely (robots.txt
obeyed, one request at a time), retrieves the relevant legislation — including scanned and image-based
PDFs — and extracts clean, article-level text. Where a portal forbids automated collection (China's
national database does, in writing), documents are collected by hand through the interface's inbox,
with a per-file provenance sheet, and flow through the identical extraction path.

**Task 2 — Intelligent Mapping and Categorisation**
Extracted provisions are mapped to RDTII indicator IDs against a machine codebook built from the RDTII
2.1 methodology: one block per indicator with the legal question, a scoring tree, coding rules and the
host's trap wording. Each filed row carries an article-level citation, a verbatim snippet that is a
character-exact substring of the stored source, a rationale, a confidence, a NEW/KNOWN Discovery Tag
and the Language of Source.

**Mandatory pillars:** 6 (Cross-border data policies) and 7 (Domestic data protection and privacy).
**Also in scope:** all twelve RDTII 2.1 pillars — demonstrated end to end on Timor-Leste, which was
mapped against all 61 in-scope indicators.
**Economies run end to end this round:** Australia, Malaysia, Singapore (English), China (Chinese),
Lao PDR (Lao), Timor-Leste (Portuguese).
**Live-test readiness, stated honestly:** of the nine 2025-database economies, the tool has actually
been run against **China** and **Lao PDR**. The other seven need a source registry and, for new
portals, an adapter; economy and indicator scope are run settings, not code.

---

## Quick Start

⚠ **A competent programmer must reach a working system from this section alone, on a clean machine, in
under 30 minutes.** No Docker is required or provided: one venv and a standard-library interface keep
the path short.

### 1. Clone the repository

```
git clone https://github.com/JohnChen-kmg/rdtii-rocky-finale-9.30
cd rdtii-rocky-finale-9.30
git checkout final-submission
```

### 2. Set up the environment

```
# Python 3.10+ required
python -m venv .venv
.venv\Scripts\pip install -r requirements-demo.txt
.venv\Scripts\pip install -e stages/p2-extract
```

Only for live crawling: `python -m playwright install chromium`.
Only for scanned PDFs: install Tesseract 5 (`winget install UB-Mannheim.TesseractOCR`); the language
packs (English, Lao, Chinese, Portuguese, Malay) ship in `stages/p2-extract/fixtures/`.

For the open-weights engine (Engine B, $0): install [Ollama](https://ollama.com), then
`ollama pull qwen2.5:14b` and verify the digest with `ollama list --digests`
(`sha256:7cdf5a0187d5…`).

Optional dense-retrieval leg: `pip install torch --index-url https://download.pytorch.org/whl/cpu`
then `pip install sentence-transformers` (first index build downloads the BGE-M3 model, ~2 GB). The
BM25-only leg runs end to end without it.

### 3. Configure

Nothing is required for a first run. Every data location is an environment variable with a clean-clone
default; the full table is in `interface/README.md` and `interface/DATA_PATHS.md`. The Engine A key is
entered in the interface and held in memory only — it is never written to disk.

### 4. Start the interface

```
.venv\Scripts\python interface/app.py
```

Open **http://127.0.0.1:8765/**. The header shows health dots for Ollama, Tesseract, Chromium, key
held and stages present.

### 5. Verify

Five minutes: Overview tab → follow the worked example (Singapore PDPA s.26(1)) from its crawl folder
to its filed row. Mapping tab → Output → open a row: original text beside labelled machine English.
Reject the row, Export CSV and xlsx, confirm the rejected row is gone and indicator IDs are text.
Appendix tab → run the self-test.

---

## Your Interface

One page served by standard-library Python (no web framework): an **Overview** (workflow map with a
worked example running down the right), **Scraping**, **Extraction** and **Mapping** tabs — each with
Set up, Run (Check then Start, progress in plain words, Stop) and Output — and an **Appendix**
(shipped docs, settings in effect, a self-test). A hand-collected inbox sits between Scraping's Run
and Output. Review is Accept / Reject / Correct per row, appended to a decisions log; the filed
submission is read-only. Crawl folders, the OCR cache, the index and run folders are clearable from
the page, only under the runs root, with a preview and a confirm. 93 interface tests:
`python -m unittest discover -s interface/tests -t interface`.

## Your Two Declared Engines

Declared in `stages/p3-map/config/llm/engines.json`; the interface reads that file, so the declared
and offered engines cannot drift apart. Both engines run the **same conversation**: a cached codebook
prefix plus one provision turn, the same schema-forced reply, the same grounding checks — they differ
in weights, not protocol.

| | Engine A | Engine B |
| :-- | :-- | :-- |
| Models | Claude Sonnet 5 (mapper) · Haiku 4.5 (blind verifier) · Opus 4.8 (tie-break) | Qwen2.5-14B-Instruct (Apache-2.0), all roles |
| Where it runs | Hosted Anthropic API; Message Batches lane at 50% pricing | Local via Ollama, digest-pinned; no key; nothing leaves the machine |
| Triage | always local qwen2.5:14b — a local model never maps, verifies or breaks a tie | same |
| Measured cost | whole finale run **$275.24** (`submission/reports/cost_ledger.json`) | **$0**; ≈ 27 s per provision, one worker |

### Switching between them

Mapping tab → **Engine Selection** banner → Engine A or Engine B. One control, no file edit, no typed
command. The browser can only name an allowlisted choice that the server validates; the choice is
recorded in the run's `run_manifest.json`.

### Re-running without fetching

Only Stage 1 touches the network. A second pass reads the frozen bytes of documents already
downloaded; its fetched-documents list is empty by construction. Downloaded documents live under the
crawl folder's `raw/`, the OCR cache under the run — both visible and clearable in the interface.

## Crawling Politely

robots.txt is read first and obeyed; a refusal is never retried with a different client, and the
user-agent is never changed to evade a block. At least 3 seconds between requests to a host, plus the
host's own Crawl-delay when longer; one request at a time; back-off on 429 and 503. China's national
database forbids automated collection, so it is hand-collected with per-file provenance; CAC, which
permits crawling, was crawled.

## Architecture Overview

```
official portals / hand inbox
  → P1 collect   (robots-polite crawler; China via its own tools)  → manifest + frozen bytes
  → P2 extract   (per-script OCR → segment → byte-anchored provisions, contract 0.3.0)
  → P3 map       (select 0.1% of pairs → local triage → mapper ⇄ blind verify → rollup → NEW/KNOWN)
  → evidence     (14-column rows, labelled glosses, audit views, per-run cost ledger)
  → Interface    (review, export, engine switch; subprocess orchestration, never imports stage code)
```

### Key modules

| Path | What it does |
| :-- | :-- |
| `stages/p0-instrument/output/` | the machine codebook: 61 decimal-ID indicator blocks, scoring trees, traps, and a 1,054-row gold set that scores results and never tunes parameters |
| `stages/p1-scrape/src/` + `countries/` | crawler engine, six economy adapters, per-economy source registries |
| `stages/p2-extract/src/rdtii_p2/` | per-script OCR, segmentation, grounding ("no quote, no record") |
| `stages/p3-map/src/p3map/` | retrieval, the selection function, triage, mapping, blind verification, rollup, NEW/KNOWN, export |
| `stages/p3-map/config/llm/engines.json` | the two declared engines, checkpoint- and digest-pinned |
| `interface/app.py` | the whole interface, standard library only |

### The cost design worth reading first

Mapping cost is decided before any model call, by selection. We analysed our own Round 1 artifacts per
indicator and replaced hand-set caps with a per-indicator threshold function with small per-language
offsets. The finale run passed **46,494 candidate pairs of 46.8 million possible (0.10%)**, and the
gray band went through a local triage before anything paid ran. Measured on Round 1's own data,
doubling every ceiling gained **zero** additional gold rows for 61% more volume. The complete
six-economy, 61-indicator run cost **$275.24** on Engine A and **$0** on Engine B.

## Swapping the OCR Engine

`OCR_ENGINE` selects `tesseract` (default, measured per script) | `paddleocr` | `azure_docint`
(optional and proprietary — never required). The OCR language comes from the crawler's own language
field, never guessed from characters. The comparison that fixed these choices, per script, with the
losing engines named — including the vision models that wrote Lao in Thai and Khmer script — is
`docs/stages/p2-extract/TOOLS_BY_ECONOMY.md`.

## Supported Economies and Portals

| Economy | Official source | How |
| :-- | :-- | :-- |
| Australia | Federal Register of Legislation | crawled |
| Singapore | Singapore Statutes Online | crawled |
| Malaysia | Laws of Malaysia (the e-Federal Gazette) + named regulators | crawled |
| Timor-Leste | Jornal da República | crawled |
| Lao PDR | Lao Official Gazette | crawled; 96% scans → Lao OCR |
| China | national database (hand; its robots.txt forbids crawling) + CAC (crawled, permitted) + ministry sites (hand, prepared worklist) | mixed, provenance per file |

Adding an economy is a `sources.yaml` registry plus, for a new portal, an adapter; pipeline code does
not change. The per-economy record, including what each portal does not publish, is under
`docs/stages/p1-scrape/`.

## Output Format

Per economy: `records_<ECON>.csv` — the host's 14 columns in the host's order, UTF-8 with BOM,
indicator IDs as decimal **text** (`6.1`, `12.4.1`, never `P6-I1`); `records_<ECON>.json` (the same
rows, grouped per law); a review workbook `RDTII_P3_results_<ECON>.xlsx`; audit HTML with the original
beside labelled machine English; and `run_manifest.json` (engine, git commit, settings, per-stage
cost). The filed evidence is in `submission/`: 101 rows filed of 318 produced. A machine translation
is never evidence — the exporter does not open gloss files, and a test pins exactly that.

## Measured Cost

From `submission/reports/cost_ledger.json`, every figure re-derivable from the run's own reports:

| Stage | USD |
| :-- | --: |
| S4 mapping (Sonnet, batch lane at 50%) | 126.69 |
| S3b triage (Haiku) | 100.89 |
| S5 blind verification (Haiku + Opus tie-break) | 41.33 |
| Glosses (quotes + provision text) | 5.98 |
| S6 economy rollup | 0.35 |
| **Whole finale run — six economies, 61 indicators, Engine A** | **275.24** |

196 batch results that failed to parse were retried live with the identical conversation, $3.27,
recovering 187 of 196. Retrieval, selection, local triage, NEW/KNOWN and export are $0. Engine B: $0.

## Known Limitations

- **Lao OCR.** ~94% character agreement and 0.856 article-number sequence agreement: roughly one Lao
  article number in seven was repaired from its position. Every repair is visible per row
  (`citation_confidence`, `article_number_as_read`); 17 of the 101 filed rows carry the caveat. We do
  **not** claim the under-5% CER for Lao — no hand-keyed Lao reference page exists.
- **China.** The national database carries statutes and administrative regulations; the operative tier
  below them lives on ministry sites by law. MIIT and Customs refuse an honest client and stay manual.
  Only 6 of 1,090 hand-collected files have full retrieval timestamps; the provenance gaps are
  recorded rather than invented.
- **Indicators outside pillars 6 and 7** run through the same pipeline, but their codebook blocks are
  host-criteria-only, and rows whose answers live outside legal databases (facts, technical standards,
  WTO postures) carry a manual-check notice instead of a pretended answer.
- **Glosses** are machine-made and labelled; Lao glosses are flagged "not literal" at 96%, a property
  of an OCR corpus rather than a per-row signal.
- The 30-minute deploy has been rehearsed on the development machine only; a second-machine rehearsal
  is scheduled before 15 October.

## Running the Test Suite

```
python -m unittest discover -s interface/tests -t interface     # 93 tests, stdlib only
cd stages/p2-extract && pytest -q                                # extraction suite
cd stages/p1-scrape  && pytest -q                                # crawler engine + adapters
cd stages/p3-map     && pytest -q                                # mapping, incl. the gloss-isolation test
```

## Reproducing Your Submitted Evidence

The filed rows are `submission/records_<ECON>.csv`, 101 filed of 318 produced; the selection rule is
stated in the submission document. Full corpora (19 GB) are deliberately not shipped: rebuild any
economy from the Scraping tab, run Extraction, then Mapping with either engine. Every stage writes its
own report, and `submission/reports/` holds the cost ledger and the per-economy scores behind the
filed rows. The development history — five workshop folders and the original repository, with every
decision and measurement dated — is preserved offline and can be shown on request.

## Team

**Rocky has a home run** — John (Jiaxiang) Chen, jiaxiangchen.kmg@gmail.com. Solo.

## Licence

Apache License 2.0 — see `LICENSE`. Third-party components and their licences are listed in Section 3
of the submission document; no AGPL component is used anywhere in the pipeline.

## Acknowledgements

UN ESCAP and KMITL for the RDTII 2.1 framework, templates and baselines. The open-source components
named in Section 3 — in particular Tesseract, PDFium, Ollama, Qwen2.5, BGE-M3 and bm25s.
