# RDTII Rocky — AI Tool for Digital Trade Regulatory Analysis

UN Global Hackathon on AI for Digital Trade Regulatory Analysis
Team: **Rocky has a home run** | Round: **Final**
Last updated: 2026-10-05

> **Final round requirement.** Every section below is mandatory. This README is part of the submission
> and is read during the desk review — it is the front door to criterion **C4a, Technical Handover**.

**What changed since the release of 1 October.** The filed evidence is the same: the 101 workbook rows and
everything under `submission/` come from the run of 27 September and have not been touched. The tool around
them was worked on: the interface opens in a window of its own, every stage's Output is a table of runs,
hand-collected files need no source, each model step of Mapping takes its own provider and model, the
Overview carries a cost report with a calculator, and one fault that ended every crawl with an error was
found and repaired. The list, with what was tested, is in `docs/RELEASE_NOTES.md`.

---

## What This Tool Does

This tool automates two tasks required by the ESCAP Regional Digital Trade Integration Index (RDTII 2.1):

**Task 1 — Automated Evidence Discovery**
Given an economy and a pillar, the tool crawls official government legal portals politely (robots.txt
obeyed, one request at a time), retrieves the relevant legislation — including scanned and image-based
PDFs — and extracts clean, article-level text. Where a portal forbids automated collection (China's
national database does, in writing), documents are collected by hand through the interface's
Hand-collected block and flow through the identical extraction path.

**Task 2 — Intelligent Mapping and Categorisation**
Extracted provisions are mapped to RDTII indicator IDs against a machine codebook built from the RDTII
2.1 methodology: one block per indicator with the legal question, a scoring tree, coding rules and the
host's trap wording. Each filed row carries an article-level citation, a verbatim snippet that is a
character-exact substring of the stored source, a rationale, a confidence, a NEW/KNOWN Discovery Tag
and the Language of Source.

**Mandatory pillars:** 6 (Cross-border data policies) and 7 (Domestic data protection and privacy).
**Also in scope:** all twelve RDTII 2.1 pillars — demonstrated end to end on Timor-Leste, which was
mapped against all 61 in-scope indicators.
**Economies covered:** Australia, Malaysia, Singapore (English), China (Chinese), Lao PDR (Lao),
Timor-Leste (Portuguese).
**Ready for the live test, stated honestly:** of the nine 2025-database economies, the tool has actually
been run against **China** and **Lao PDR**. The other seven have not been run. A new economy is not a
setting: each stage needs something of its own for it, and the list is in the interface, Appendix →
Adding a new economy, and under Supported Economies below.

---

## Quick Start

⚠ **A competent programmer must reach a working system from this section alone, on a clean machine, in
under 30 minutes.** No Docker is required or provided: one venv and a standard-library interface keep
the path short.

### 1. Clone the repository

```
git clone https://github.com/JohnChen-kmg/rdtii-rocky-next
cd rdtii-rocky-next
git checkout final-submission
```

### 2. Set up the environment

Python 3.12 or newer for the stages (the pinned numpy needs it; the interface alone runs on 3.10).

Windows:

```
python -m venv .venv
.venv\Scripts\pip install -r requirements-demo.txt
.venv\Scripts\pip install -e stages/p2-extract
.venv\Scripts\python -m playwright install chromium
```

macOS (12 or newer) and Linux:

```
python3.12 -m venv .venv
.venv/bin/pip install -r requirements-demo.txt
.venv/bin/pip install -e stages/p2-extract
.venv/bin/python -m playwright install chromium
```

The `playwright` line is only for live crawling. For scanned PDFs install Tesseract 5
(`winget install UB-Mannheim.TesseractOCR`, `brew install tesseract`, or `sudo apt install tesseract-ocr`);
the language packs (English, Lao, Chinese, Portuguese) ship in `stages/p2-extract/fixtures/`.

A `.venv` at the top of the repository is found by itself: the launcher starts with it and every stage runs
with it. When a stage's packages live somewhere else, name that Python once in the interface, Appendix →
This machine. **Check** on each stage's Run block says what is missing before anything starts.

For the open-weights engine (Engine B, $0): install [Ollama](https://ollama.com), then
`ollama pull qwen2.5:14b` and verify the digest with `ollama list --digests`
(`sha256:7cdf5a0187d5…`).

Optional dense-retrieval leg: `pip install torch --index-url https://download.pytorch.org/whl/cpu`
then `pip install sentence-transformers` (first index build downloads the BGE-M3 model, ~2 GB). The
BM25-only leg runs end to end without it.

### 3. Configure

Nothing is required for a first run, and there is no `.env` to edit. Every data location is an environment
variable with a clean-clone default; the full table is in `interface/README.md` and
`interface/DATA_PATHS.md`. A hosted engine's key is typed in the interface (Mapping → Engine API keys) and
held in memory only — it is never written to disk.

### 4. Start the interface

Double-click **`Start-RDTII-Rocky.cmd`** (Windows) or **`Start-RDTII-Rocky.command`** (macOS); on Linux run
`./start-rdtii-rocky.sh`. The pages open in a window of their own, in the Edge or Chrome already on the
machine; nothing is installed. Closing the window stops the tool, and a run with it, after a warning.

Or from a terminal, as a browser tab that Ctrl+C stops:

```
.venv\Scripts\python interface/app.py        (Windows)
.venv/bin/python interface/app.py            (macOS, Linux)
```

Open **http://127.0.0.1:8765/**. The header shows health dots for Ollama, Tesseract, Chromium, Key and
Stages; green means ready. **Everything else happens in the interface.**

### 5. Verify

Without running anything, about five minutes:

1. Mapping → 3.3 Output: the shipped run of the finale (kind "fixture", 52 rows, six economies) is listed.
   Click it, then click a row: the original text beside labelled machine English, the scores, the
   re-check, the source link.
2. Press **Reject…**, give a reason, then **Export CSV** and **Export xlsx**: the rejected row is gone and
   indicator IDs are text. **Clear decision** brings it back.
3. Appendix → Check the run layer: the self-test ends "Finished".

With a small run on the open-weights engine, at $0 (needs Ollama and, for the one scanned document,
Tesseract):

1. Extraction → 2.1 Set up: choose the shipped demo corpus (`demo_data/mini_raw`, five documents) →
   **Check** → **Start**. Expected: 5 documents, about 3,600 provisions, listed in 2.3 Output as complete.
2. Mapping → 3.1 Set up: that output, Singapore, indicators 6.1 and 6.4. 3.2 Run: Provider **Qwen** in
   steps B to E, Quick run 5 → **Check** → **Start**. Expected: 8 steps in about three minutes on a
   machine with a graphics card, two rows in the host's 14 columns (PDPA s.26(1) under 6.4, and the
   no-provision row for 6.1), under `outputs/map/`.

If Start stays locked, the failed line of Check says what is missing.

---

## Your Interface

One page served by standard-library Python (no web framework): an **Overview**, **Scraping**,
**Extraction** and **Mapping**, each with Set up, Run and Output, and an **Appendix**.

| What a reviewer needs to do | Where it is |
| :---- | :---- |
| Start a run and watch progress in plain words | Scraping → 1.2 Run, Extraction → 2.2 Run, Mapping → 3.2 Run: **Check**, then **Start**. Progress is written under the button, one sentence a step; **Stop** ends it |
| Open the audit view: a result beside the source text it came from | Mapping → 3.3 Output → click a run in the table → click a row: the verbatim snippet in the original language beside labelled machine English, with the score, the re-check and the rationale |
| Follow a row to its official source at the cited article | the same row view → **Source** (the official address) and the fold **Where the quote sits in the source text** |
| Accept, reject or correct a row | the same row view → **Accept**, **Reject…**, **Correct…**, **Clear decision**; every decision is appended to a log |
| Switch the AI engine | Mapping → 3.2 Run → steps B to E → **Provider** and **Model**; keys under **Engine API keys** at the top of the page |
| Export to the RDTII schema | Mapping → 3.3 Output → **Export CSV**, **Export xlsx** |

Also on the page: the Overview's workflow map, a cost report (money, time and a calculator) and the estimated
performance by model; a Hand-collected block (Scraping 1.3) for files a crawler may not fetch; a table of
runs in every Output block (when it began, when it last ran, complete or not); crawl folders, the OCR cache,
the index and run folders clearable from the page, only under the runs root, with a preview and a confirm.
The filed submission is shown read-only.

**Walkthrough recording:** `walkthrough_RockyHasAHomeRun_Oct05_5min.mp4`, submitted with the Word document. It
was recorded on 5 October 2026 and replaces the recording of 1 October, which showed the screens before they
were rearranged (the engine choice moved from a banner into the steps of 3.2 Run).

---

## Your Two Declared Engines

Declared in `stages/p3-map/config/llm/engines.json`; the interface reads that file, so the declared
and offered engines cannot drift apart. Both engines run the **same conversation**: a cached codebook
prefix plus one provision turn, the same schema-forced reply, the same grounding checks — they differ
in weights, not protocol.

| | Engine A — commercial hosted | Engine B — open weights |
| :---- | :---- | :---- |
| Provider and model | Anthropic: Claude Sonnet 5 (careful reading), Haiku 4.5 (quick screen, re-check), Opus 4.8 (tie-break) | Qwen2.5-14B-Instruct (Apache-2.0), every step |
| Version / checkpoint | `claude-sonnet-5`, `claude-haiku-4-5`, `claude-opus-4-8` | `qwen2.5:14b`, Q4_K_M, digest `sha256:7cdf5a0187d5…` |
| Local or hosted API | hosted, Anthropic API | local via Ollama; no key; nothing leaves the machine |
| Config value | `RDTII_ENGINE=A` | `RDTII_ENGINE=B` |
| Measured cost | whole finale run **$275.24** (`submission/reports/cost_ledger.json`) | **$0**; about 27 s per provision, one worker |

The interface sets the config value; nobody types it.

### Switching between them

In the interface: Mapping → 3.2 Run → each model step (B quick screen, C careful reading, D re-check,
E tie-break) has its own **Provider** and **Model**. The steps start on Engine A; **Qwen** in the four steps
is Engine B. No file edit, no typed command. The browser can only name an allowlisted choice that the server
validates; the model of each step is recorded in the run's `run_manifest.json` and shown in the run's Record.

The abstraction lives in `stages/p3-map/config/llm/` (`base.py`, `factory.py`, one client per provider);
adding a provider with an OpenAI-compatible API is one entry in `engines.json`.

**Three more providers, added after 30 September and not declared engines:** DeepSeek, Kimi and ChatGPT
can be chosen per step in the same place. The pipeline's prompts, traps and every reported figure were made
on Engine A; these three are marked "not measured" in `engines.json` and on the page. What a first
experiment showed is under Measured Cost below.

### Re-running without fetching

Only Stage 1 touches the network. A second pass reads the frozen bytes of documents already
downloaded; its fetched-documents list is empty by construction.

In the interface: Extraction → 2.1 Set up (choose the crawl folder) and Mapping → 3.1 Set up (choose the
extraction output); neither page has a control that fetches.
Where downloaded documents are cached: `outputs/scrape/<economy>/<source>/<time>/raw/`; the OCR cache sits
under the extraction run. Both are listed, and clearable, in the Output blocks.

---

## Crawling Politely

Built in and on by default. robots.txt is read first and obeyed; a refusal is never retried with a
different client, and the user-agent is never changed to evade a block. China's national database forbids
automated collection, so it is hand-collected with per-file provenance; CAC, which permits crawling, was
crawled.

| Setting | Value | Where it is set |
| :---- | :---- | :---- |
| Max requests per second per host | one every 3 seconds at most, or the host's own Crawl-delay when longer | `stages/p1-scrape/config/settings.py` (`REQUEST_DELAY_MS`, default 3000); `stages/p1-scrape/src/p1_scrape/adapters/my_gazette/robots.py` (the host's delay) |
| Parallel requests per host | 1 | `stages/p1-scrape/src/p1_scrape/adapters/my_gazette/client.py` (one paced client per host; waits on 429 and 503, then stops) |
| robots.txt respected | yes | `stages/p1-scrape/src/p1_scrape/adapters/my_gazette/robots.py` (`RobotsRules.allowed`); China: `adapters/cn_npc/polite.py` |

The interface states the time a crawl will take before it starts, and offers a Quick run (the first N
documents) for a trial.

---

## Architecture Overview

```
official portals / files collected by hand
  → P1 collect   (robots-polite crawler; China via its own tools)  → manifest + frozen bytes
  → P2 extract   (per-script OCR → segment → byte-anchored provisions, contract 0.3.0)
  → P3 map       (select 0.1% of pairs → quick screen → careful reading ⇄ blind re-check → rollup → NEW/KNOWN)
  → evidence     (14-column rows, labelled glosses, audit views, per-run cost ledger)
  → Interface    (runs, review, export, engine choice; subprocess orchestration, never imports stage code)
```

Fetching and reading are separate programs joined by files: only P1 has network code; P2 and P3 read what
P1 stored.

### Key modules

| Module | File | Description |
| :---- | :---- | :---- |
| Instrument | `stages/p0-instrument/output/` | the machine codebook: 61 decimal-ID indicator blocks, scoring trees, traps, and a 1,054-row gold set that scores results and never tunes parameters |
| Portal Crawler | `stages/p1-scrape/src/p1_scrape/` (`orchestrator.py`, `adapters/`) | crawler engine, one adapter per portal, per-economy source registries, the manifest and its contract check |
| Document Processor | `stages/p2-extract/src/rdtii_p2/` (`router.py`, `ocr_scanned.py`, `segment.py`, `ground.py`) | routes each file by what it is, per-script OCR, splitting into provisions, grounding ("no quote, no record") |
| Retrieval | `stages/p3-map/src/p3map/prefilter/` (`bm25.py`, `dense.py`), `select.py` | keyword and meaning search, then the per-indicator selection function |
| Mapper | `stages/p3-map/src/p3map/` (`triage/`, `mapping/`, `verify/`, `rollup.py`) | quick screen, careful reading, blind re-check, tie-break, scores |
| Engines | `stages/p3-map/config/llm/engines.json` | the two declared engines, checkpoint- and digest-pinned, and the models a step may be given |
| Interface | `interface/app.py`, `interface/rdtii_ui/`, `interface/static/` | run control, audit view, review, export; standard library only |
| Output Writer | `stages/p3-map/src/p3map/output/` (`submission.py`, `template.py`, `excel_export.py`) | the 14-column rows, the host's workbook, the review workbook |

### The cost design worth reading first

Mapping cost is decided before any model call, by selection. We analysed our own Round 1 artifacts per
indicator and replaced hand-set caps with a per-indicator threshold function with small per-language
offsets. The finale run passed **46,494 candidate pairs of 46.8 million possible (0.10%)**, and the
gray band went through a quick screen before the careful reading saw anything. Measured on Round 1's own
data, doubling every ceiling gained **zero** additional gold rows for 61% more volume. The finale run,
six economies on pillars 6 and 7 and one of them on all 61 indicators, cost **$275.24** on Engine A and
**$0** on Engine B; one economy on the two mandatory pillars is about $33.

---

## Swapping the OCR Engine

| Engine | Config value | Notes |
| :---- | :---- | :---- |
| Tesseract 5 | `OCR_ENGINE=tesseract` (default) | open source, local; measured per script; language packs shipped |
| PaddleOCR | `OCR_ENGINE=paddleocr` | open source, local; optional, not installed by default |
| Azure Document Intelligence | `OCR_ENGINE=azure_docint` | **proprietary hosted service**; optional, never required |

The core pipeline runs with no proprietary service: OCR is Tesseract, embeddings are BGE-M3, and
translation for review is made by the model chosen for the re-check step (with Engine B: local Qwen). The OCR language comes
from the crawler's own language field, never guessed from characters. In the interface, Extraction → 2.2 Run
offers the pack (Fast or Best) and the number of workers, with the measured pace and memory of each. The
comparison that fixed these choices, per script, with the losing engines named — including the vision
models that wrote Lao in Thai and Khmer script — is `docs/stages/p2-extract/TOOLS_BY_ECONOMY.md`.

---

## Supported Economies and Portals

| Economy | Official portal | Language | Run end to end? | Notes |
| :---- | :---- | :---- | :---- | :---- |
| Australia | Federal Register of Legislation | English | yes | crawled |
| Singapore | Singapore Statutes Online | English | yes | crawled |
| Malaysia | Laws of Malaysia, and named regulators | English | yes | crawled |
| Timor-Leste | Jornal da República | Portuguese | yes, all 61 indicators | crawled |
| Lao PDR | Lao Official Gazette | Lao | yes | crawled; 96% scans, read by Lao OCR |
| China | national database, CAC, ministry sites | Chinese | yes | the national database by hand (its robots.txt forbids crawling), CAC crawled, ministry sites by hand; provenance per file |
| Thailand, Viet Nam, Indonesia, India, Kazakhstan, Mongolia, Russian Federation | — | — | no | named in the mapping stage with an assumed language; nothing built, nothing measured |

**What a new economy needs**, per stage (the same table, with the file that holds each piece, is in the
interface: Appendix → Adding a new economy):

- **Scraping:** permission first (robots.txt and terms; where a host says no, its files are collected by
  hand); an adapter for the portal; a source registry; a link list; a watchlist of sources that cannot be
  crawled.
- **Extraction:** the language of every document; a splitting pattern for the way its laws number their
  provisions (built: Section, Article, Artigo, ມາດຕາ, 第…条); an OCR pack if its laws are scanned (built:
  English, Lao, Portuguese, Chinese); a page parser only if the portal publishes web pages. PDF with a text
  layer and Word need nothing new.
- **Mapping:** its name and language; a threshold offset measured for the language; a check that the chosen
  models read the language; the host's existing rows, where there are any. The rulebooks are the same for
  every economy.

Hand collection works for any of the six economies today: Scraping → 1.3 Hand-collected takes PDF and Word
files (a saved web page only from a portal the tool has a parser for, with its address), judges each file by
what it is, and files it under `inbox/<economy>/Hand_collected/<date_time>/`.

---

## Output Format

Per economy: `records_<ECON>.csv`, UTF-8 with BOM, in the host's column order; `records_<ECON>.json` (the
same rows, grouped per law); a review workbook `RDTII_P3_results_<ECON>.xlsx`; audit HTML with the original
beside labelled machine English; and `run_manifest.json` (the model of each step, git commit, settings,
cost per step).

| # | Column | Required | Description |
| :---- | :---- | :---- | :---- |
| 1 | economy | Required | Official UN country name |
| 2 | law_name | Required | Full official statute name and year |
| 3 | law_number_ref | Optional | Official act or law number |
| 4 | last_amended | Optional | Year of most recent amendment |
| 5 | indicator_id | Required | RDTII 2.1 code as **text**: `6.1`, `7.3`, `12.4.1`, never `P6-I1` |
| 6 | article | Required | Exact article and paragraph |
| 7 | discovery_tag | Required | NEW or KNOWN, matched on instrument name and section, never on the address |
| 8 | location_reference | Optional | PDF page number, or section path |
| 9 | verbatim_snippet | Required | A character-exact passage of the stored source, in the original language |
| 10 | mapping_rationale | Optional | Why this provision maps to this indicator |
| 11 | source_url | Required | Address on the official portal |
| 12 | confidence | Optional | 0.00–1.00 |
| 13 | notes | Optional | OCR repairs, citation caveats, manual-check notices |
| 14 | language_of_source | Required | Original language of the document |

The filed evidence is in `submission/`: 101 rows filed of 318 produced. A machine translation is never
evidence — the exporter does not open gloss files, and a test pins exactly that.

---

## Measured Cost

Measured on the finale run of 27 September 2026 (six economies, 766,526 provisions), from
`submission/reports/cost_ledger.json`; every figure is re-derivable from the run's own reports
(`map_report_<E>.json`, `verify_report_<E>.json`, `run_manifest.json`). Every run from the interface writes
the same manifest, and its cost is shown in the run table without arithmetic.

| Component | Engine used | Measured cost |
| :---- | :---- | :---- |
| Crawling | none | $0 |
| OCR | Tesseract 5, local | $0 |
| Embedding and retrieval | BM25 and BGE-M3, local | $0 |
| Selection, local triage, NEW/KNOWN, export | none | $0 |
| Mapping — Engine A: quick screen | Claude Haiku 4.5 | $100.89 |
| Mapping — Engine A: careful reading | Claude Sonnet 5, batch lane at half price | $126.69 |
| Mapping — Engine A: blind re-check and tie-break | Claude Haiku 4.5, Opus 4.8 | $41.33 |
| Mapping — Engine A: translations for review, rollup | Claude | $5.98 + $0.35 |
| Mapping — Engine B, every step | Qwen2.5 14B, local | $0 |
| **Total, Engine A** | | **$275.24** for the run; **$32.96** for one economy on pillars 6 and 7 (Singapore) |
| **Total, Engine B** | | **$0** |

**Benchmark:** Singapore, the nine indicators of pillars 6 and 7: mapping $15.48, quick screen $12.53,
re-check $4.93, rollup $0.02. The same scope cost between **$22** (Lao PDR, Timor-Leste) and **$52** (China,
which also pays $3.06 of translation); the median is $32. One economy on two indicators, the shape of the
15 October draw, is about **$7**. Per document the figure means little here: cost follows the candidate
pairs selected, not the pages. **Wall-clock, Engine B:** about 27 seconds per provision, one worker.

### What the finale run cost

| Scope | USD |
| :-- | --: |
| Six economies on pillars 6 and 7: AU 46.38, CN 52.08, MY 30.65, SG 32.96, LA 22.00, TL 21.93 | 206.00 |
| Timor-Leste on the other 52 indicators, the whole instrument for one economy | 69.04 |
| Rollup re-runs during the build, not attributed to an economy | 0.20 |
| **Whole finale run, Engine A** | **275.24** |

196 batch results that failed to parse were retried live with the identical conversation, $3.27,
recovering 187 of 196. The quick screen is attributed to economies pro rata by their gray-band pairs.

### Estimate: six economies, all 61 indicators

Timor-Leste is the one economy run against the whole instrument: $21.93 for pillars 6 and 7 and $69.04 for the
other 52 indicators, so the full instrument cost **4.1 times** the two mandatory pillars. Applied to each economy's
measured two-pillar cost, six economies on all 61 indicators come to **about $850** on Engine A (AU 192, CN 216,
MY 127, SG 137, LA 91, TL 91). If cost scaled with the indicator count instead (61/9 = 6.8 times) the ceiling would
be about $1,400; the lower figure is the measured one, because the 52 other indicators are mostly subject-specific
and admit fewer candidates. Engine B: $0.

### In the interface: a calculator, and its one caution

Overview → Cost report gives money by model and step, time by stage, and a calculator (tick economies, give
each step a model, read dollars and hours). It scales the finale's bill. A run started from the interface
reads live, not in the batch lane, so the careful reading costs twice what the finale paid: Singapore with
the finale's models shows $48.44 there, against $32.96 billed. Time figures are estimates: a pace measured
on a sample, applied to the finale's counts.

### A third way to cut cost: another model in a step

Besides selection (fewer pairs) and Engine B (free), a step can be given a cheaper model. Two rounds of
evidence, both small:

- **July, under pre-registered gates** (`stages/p3-map/docs/ab/`): local Qwen as the screen dropped 16% of
  the pairs Haiku keeps; Haiku as reader grounded 43% of quotes against Sonnet's 91%; the DeepSeek models of
  that month failed the gates as screen and as reader. A swap is not free of risk.
- **4 October, one experiment** on provisions the finale had judged, the tool's own three requests on each
  model the page offers. The reference is Claude's finale answer, not a person's, so these are agreement
  figures, not accuracy. Every model answered in the form the tool needs. Re-check, same verdict as Claude
  (English / Chinese / Portuguese / Lao, 50 provisions each): DeepSeek V4 Pro 96 / 94 / 98 / 92%, Kimi K3
  94 / 90 / 94 / 94%, GPT-6.1 Sol 88 / 78 / 82 / 78%, local Qwen 94 / 90 / 90 / 78%. Careful reading, of 25
  matches: Sonnet 5 asked again finds 19, DeepSeek V4 Pro 18, Kimi K3 17, GPT-6.1 Sol 12; Qwen 18, with 7
  wrong yes and 4 quotes not in the law. Metered cost per 1,000 careful readings: Qwen $0, DeepSeek V4 Pro
  $4.70, GPT-6.1 Sol $9.60, Kimi K3 $18.80, Sonnet 5 $26.90. The full table is on the Overview, under
  Estimated performance by model, with the same caution: one experiment, small samples.

No full run has been made and scored on any model outside the two declared engines.

---

## Known Limitations

- **Lao OCR.** ~94% character agreement and 0.856 article-number sequence agreement: roughly one Lao
  article number in seven was repaired from its position. Every repair is visible per row
  (`citation_confidence`, `article_number_as_read`); 17 of the 101 filed rows carry the caveat. We do
  **not** claim the under-5% CER for Lao — no hand-keyed Lao reference page exists.
- **China.** The national database carries statutes and administrative regulations; the operative tier
  below them lives on ministry sites by law. MIIT and Customs refuse an honest client and stay manual.
  Only 6 of 1,090 hand-collected files have full retrieval timestamps; the provenance gaps are
  recorded rather than invented.
- **Indicators outside pillars 6 and 7** run through the same pipeline. Since 4 October their codebook
  blocks carry the same depth as pillars 6 and 7 — scoring trees, coding rules, disambiguation, traps —
  but **no person has yet reviewed those 52 blocks**, so their rows deserve a reviewer's eye, and rows
  whose answers live outside legal databases (facts, technical standards, WTO postures) carry a
  manual-check notice instead of a pretended answer. The pipeline computes every indicator the same way;
  the only thing that differs is the rulebook it is given
  (`stages/p0-instrument/output/indicators.yaml`, no code).
- **Documents of an unusual shape.** Extraction splits a law at the headings common in its economy's laws.
  A document built differently (a notice, a circular with no articles) may come out as one piece or with
  none; Extraction → 2.3 Output lists every such document as "to check".
- **Local Qwen on Lao.** It agrees with Claude's verdict on 78% of Lao provisions against 90–94% in the
  other languages; for Lao, Engine B's rows need the closer look.
- **Models outside the two declared engines** have been tried on small samples only (above).
- **Confidence calibration.** The confidence is the model's own figure, relative and not a calibrated
  probability. What to trust instead is on each row: whether the blind re-check agreed, and whether the
  citation is exact or repaired. A row the re-check overturned is never filed; a row with a repaired
  citation says so in Notes and should be opened by a person.
- **Glosses** are machine-made and labelled; Lao glosses are flagged "not literal" at 96%, a property
  of an OCR corpus rather than a per-row signal.
- **A stopped run** reads "stopped" only while the interface that stopped it is open; after a restart it
  reads "not complete".
- **Deployment rehearsal.** The 30-minute deploy has been rehearsed on the development machine only. The
  interface's tests passed on Windows, macOS and Ubuntu in the repository's workflow on 4 October; no
  window has yet been opened by us on a Mac.

---

## Running the Test Suite

```
python -m unittest discover -s interface/tests -t interface     # 291 tests, standard library only
cd stages/p1-scrape  && pytest -q                                # 429 tests
cd stages/p2-extract && pytest -q                                # 134 tests
cd stages/p3-map     && pytest -q                                # 505 tests
```

| Test folder | What it tests |
| :---- | :---- |
| `interface/tests/` | run control, Check, the run tables, review decisions, export (rejected rows removed, IDs as text), Clear guards, hand-collected filing, the cost report against the ledger |
| `stages/p1-scrape/tests/` | crawler engine, adapters, robots rules, the manifest and its contract check |
| `stages/p2-extract/tests/` | routing by file type, OCR handling, splitting per language, grounding |
| `stages/p3-map/tests/` | indicator IDs as text, selection, the request each model receives, rollup, export, and that a translation never becomes evidence |

Known: six of the extraction tests (`test_fresh_keeps_ocr_cache.py`) load a development tool that is not in
this repository and fail without it; the other 128 pass. A workflow runs the interface's tests on Windows,
macOS and Ubuntu with Python 3.10 and 3.12 (`.github/workflows/interface-tests.yml`); its last run, on
4 October, passed on all three.

---

## Reproducing Your Submitted Evidence

The filed rows are `submission/records_<ECON>.csv`, 101 filed of 318 produced; the selection rule is code
(`stages/p3-map/src/p3map/output/template.py`, `curate`) and is stated in the submission document. They were
produced by the release of 1 October from the run of 27 September, and are shipped unchanged.

In the interface: Scraping → Run for the economy, Extraction on that crawl folder, then Mapping with either
engine; Mapping → 3.3 Output lists the run beside the filed submission for comparison. Full corpora (19 GB)
are deliberately not shipped.

Two honest notes. A rerun today will not give the same rows byte for byte: the portals have moved on, a
model does not always answer twice alike (Sonnet asked twice gave the same verdict on 73 of 78), and since
4 October the rulebooks of the 52 indicators outside pillars 6 and 7 are deeper than the ones the filed rows
were made with. And every stage writes its own report: `submission/reports/` holds the cost ledger and the
per-economy scores behind the filed rows. The development history — five workshop folders and the original
repository, with every decision and measurement dated — is preserved offline and can be shown on request.

---

## Team

| Role | Name | Responsibility |
| :---- | :---- | :---- |
| Technical Lead and Substantive Lead | John (Jiaxiang) Chen, jiaxiangchen.kmg@gmail.com | everything: architecture, pipeline, instrument, output review. Solo team |

---

## Licence

Released under the **Apache License 2.0** — see [LICENSE](LICENSE). Third-party components and their
licences are listed in Section 3 of the submission document; no AGPL component is used anywhere in the
pipeline.

---

## Acknowledgements

Built for the UN Global Hackathon on AI for Digital Trade Regulatory Analysis, organised by ESCAP and KMITL;
thanks to both for the RDTII 2.1 framework, templates and baselines. The open-source components named in
Section 3 — in particular Tesseract, PDFium, Ollama, Qwen2.5, BGE-M3 and bm25s.
