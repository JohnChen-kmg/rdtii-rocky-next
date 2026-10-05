# DATA — what the tool needs, what the repository ships, where a run writes

As of 5 October 2026. This file replaces the Round 1 version, which described three economies, the
`main.py` run modes and a data release that this repository does not have.

The rule has not changed: nothing claims what its bytes cannot show. Where data is not shipped, the
manifests, hashes and logs that describe it are shipped instead, so a claim about the corpus can be
checked without the corpus.

## At a glance

Everything is done from the interface (`python interface/app.py`, or the launcher). The second column
says where; the third says what is needed beyond a clone.

| You want to | Where | Needs beyond a clone |
| :-- | :-- | :-- |
| Read the finale's rows, review them, export | Mapping → 3.3 Output → the shipped run (kind "fixture") or the filed submission | Nothing. The interface is standard library only; Python 3.10 or newer |
| Run Extraction on the demo corpus | Extraction → 2.1 Set up → `demo_data/mini_raw` → Check → Start | The environment of the README's Quick Start. Tesseract 5 for the one scanned document |
| Run Mapping on that output at $0 | Mapping → 3.1 Set up, 3.2 Run with Provider **Qwen** in steps B to E | Ollama and `qwen2.5:14b` |
| Run Mapping on a hosted model | the same, with another provider in a step | That provider's key, typed under Engine API keys. Held in memory, never written |
| Crawl a portal | Scraping → 1.2 Run (try **Quick run** first) | Network; the Playwright Chromium of the Quick Start |
| Add documents by hand | Scraping → 1.3 Hand-collected | Nothing |
| Tag rows NEW against KNOWN | set `BASELINE_PATH`, `BASELINE_R2_PATH` before starting | The host's baseline workbooks, which are theirs and are not shipped. Without them a run says so and tags every match NEW |
| Use the meaning index | Mapping → 3.2 Run → A Candidate selection | `torch` and `sentence-transformers`; the first build downloads BGE-M3, about 2 GB. Without them the keyword index runs alone |
| Rebuild the finale corpus | Scraping, then Extraction, then Mapping, per economy | Hours of polite crawling per portal; see "What is not shipped" |

Measured on 5 October, from the page: the demo corpus gives 5 documents and 3,643 provisions; Singapore
on indicators 6.1 and 6.4 with local Qwen, five provisions, gives two rows in three minutes at $0
(`docs/CHANGELOG_FINALE.md`, 2026-10-05, the night test).

## What the repository ships

Sizes are of the tracked files, measured on 5 October 2026 (1,150 files).

| Path | Size | What it is |
| :-- | --: | :-- |
| `submission/` | 6.2 MB | The filed evidence: `records_<ECON>.csv` and `.json` for six economies, the six audit pages, `package_report.json`, and `reports/` (the cost ledger, the scores, the evaluation and the URL check behind the filed rows). Read-only in the interface |
| `interface/fixtures/` | 0.6 MB | A slice of the finale run in the shapes the mapping stage writes: 52 rows over six economies, the glosses, the verification trail, the scores and the run manifest. It is what Output shows on a clean clone |
| `demo_data/` | 17.5 MB | `mini_raw/`: five documents with their manifest rows, crawl log lines and header sidecars. `my-cma1998-001.pdf`: the scanned Malaysian act, kept once |
| `stages/p0-instrument/output/` | 3.3 MB | The instrument: `indicators.yaml` (61 blocks), `policies.yaml`, `indicator_order.yaml`, 61 signatures, the gold set (1,054 rows). The mapping stage reads a byte-identical copy in `stages/p3-map/contracts/instrument/` |
| `stages/p1-scrape/links/<cc>/` | 20 MB | The link list of each crawled economy (AU, LA, MY, SG, TL): `documents.jsonl`, `laws.csv`, `catalogue_meta.json` with the registry fingerprint, the log of the build, and the seed laws |
| `stages/p1-scrape/handoff1/<CC>/` | 57 MB | The finale corpus described without its bytes: per economy the manifest (CSV and JSONL), the law table, the link list that was used, the audit and the corpus note; for China the collection's notes and `provenance.tsv`; the run notes |
| `stages/p2-extract/fixtures/` | 78 MB | The Tesseract packs, `tessdata_fast/` and `tessdata_local/` (English, Lao, Portuguese, simplified Chinese), and `ocr_reference/`: one hand-transcribed page from each of two scanned Malaysian acts, for the character-error measurement |
| `stages/*/tests/`, `interface/tests/` | 9 MB | Tests and the saved pages they parse |

What the shipped manifests show: for every crawled document of the finale corpus, its address, the date
it was fetched, how it was fetched and the SHA-256 of its bytes (`source_url`, `access_date`,
`retrieval_method`, `content_sha256`). China's hand-collected files have `provenance.tsv` instead, with
the address and the fetch time where one was recorded; its gaps are left as gaps. A later crawl can be
compared hash by hash; portals serve current consolidations, so a difference is a fact about the portal,
and the hashes show where.

## What is not shipped

| Not shipped | Why | To have it |
| :-- | :-- | :-- |
| The raw documents of the finale corpus (19 GB) | Size; they are outputs | Crawl again from Scraping. The page states the time before Start: reading the listings alone took from under 2 minutes (Timor-Leste) to 133 minutes (Malaysia) on 4 October |
| The extraction output of the finale (766,526 provisions) and the retrieval index (2.7 GB) | Size; two files exceed what GitHub accepts (`interface/DATA_PATHS.md`) | Run Extraction on a crawl folder; the index is rebuilt by Mapping when it is missing or older than its input |
| The host's workbooks (baseline database, methodology, output template) | They are the host's; `.gitignore` names them | Place your own copy and set `BASELINE_PATH`, `BASELINE_R2_PATH` |
| Any key | A key never belongs in a repository | Type it under Engine API keys |
| The Malay Tesseract pack | Not in `fixtures/`; the stage maps Malay to `msa+eng` | Add `msa.traineddata` beside the others before reading a scanned document declared Malay |

Three stages together are 28 GB on the development machine (`interface/DATA_PATHS.md`).

## Where a run writes

Everything a run writes goes under the runs root (`RDTII_RUNS_ROOT`, default `outputs/`), which git
ignores. Nothing is written under `stages/`, `submission/`, `demo_data/` or `interface/`.

```
outputs/
  scrape/<economy>/<source>/<time>/          one crawl: manifest.csv, manifest.jsonl, manifest_meta.jsonl,
                                             raw/, crawl_status.json, crawl_log.jsonl, cost_report.json
  scrape/<economy>/<source>/links_<time>/    a link list refreshed from the portal
  scrape/<economy>/Hand_collected/hand_<batch>_<time>/
                                             the manifest and law table written for hand-collected files,
                                             and left_out.csv
  scrape/CN/china-tools/<time>/              a run of the China tools
  extract/<name>/                            provisions.jsonl, laws.jsonl, doc_status.jsonl, source_text/,
                                             by_law/, ocr/ (the page cache), extract_log.jsonl, cost_report.json
  index/<name>/                              prefilter_corpus.jsonl, bm25_top.npz, dense_top.npz, the embeddings
  map/<time>_<engine>[_<name>]/out/          submission/, rollup/, verify/, audit/, results/, run_manifest.json;
                                             selection.json beside out/ when a threshold was typed
  reviews/<run>/decisions.jsonl              the append-only review log
  reviews/<run>/export/                      records_<ECON>_<time>.csv or .xlsx, and review_log.csv
inbox/<economy>/Hand_collected/<date_time>/  files dropped by hand, with provenance.tsv
```

A run folder also holds `run_note.txt` when a note was typed at Start. Folders of the earlier layouts
(`scrape/SG_<time>`, `inbox/<economy>/<source>/`) are still read.

Outside the repository, in the state folder (`%LOCALAPPDATA%\rdtii-rocky`,
`~/Library/Application Support/rdtii-rocky` or `~/.local/state/rdtii-rocky`): `machine.json` (which
Python runs each stage on this computer), `interface.log`, the window's browser profile and the note of
the running instance.

**Clear** on a page removes one run folder or one named cache under the runs root, after a preview and
a confirmation, and never a file git tracks.

## The settings that point at data

Each is an environment variable with a default that works on a clean clone. The names shared with the
stages are the stages' own. The full table, with the settings for the window and the interpreters, is in
`interface/README.md`; the reasoning is in `interface/DATA_PATHS.md`.

| Setting | Default | Points at |
| :-- | :-- | :-- |
| `HANDOFF1_DIR` | `demo_data/mini_raw` | a crawler corpus |
| `HANDOFF2_DIR` | `outputs/extract/demo` | an extraction output |
| `OUT_DIR` | `interface/fixtures` | the mapping run shown first in Output |
| `RDTII_OUT_DIR_EXTRA` | (a sibling `out_*` of `OUT_DIR`) | further arms of that run |
| `INDEX_DIR` | `outputs/index/demo` | the retrieval index of `HANDOFF2_DIR` |
| `INSTRUMENT_DIR` | `stages/p0-instrument/output` | the instrument |
| `BASELINE_PATH`, `BASELINE_R2_PATH` | none | the host's baseline workbooks |
| `RDTII_RUNS_ROOT` | `outputs` | where runs are written, and the only tree Clear may touch |
| `RDTII_SUBMISSION_DIR` | `submission` | the filed rows |
| `RDTII_INBOX_DIR` | `inbox` | documents collected by hand |

`python interface/app.py --print-settings` prints every setting in effect and where it came from.

## The old command line

`main.py`, at the top of the repository, is the Round 1 driver (`--economy`, `--demo`, `--quick`,
`--mini-run`, `--full-pipeline`). It was carried over on 29 September and has not been changed since.
The interface does not use it; it starts each stage's own command line. Tried on 5 October, its default
mode, `python main.py --economy Singapore --pillar 6`, ends without error and writes a file with the 14
column names and no rows: it selects rows whose Indicator ID begins `P6-`, the Round 1 form, and the
filed rows carry `6.1`. Its other modes were not tried. Use the interface.

## Environment notes

- **Python.** 3.12 or newer for the stages (the pinned numpy needs it); the interface alone runs on 3.10.
- **Tesseract 5.** `winget install UB-Mannheim.TesseractOCR`, `brew install tesseract` or
  `sudo apt install tesseract-ocr`. The packs listed above are in the repository; nothing is downloaded.
- **Torch for the meaning index.** Without a graphics card:
  `pip install torch --index-url https://download.pytorch.org/whl/cpu`, then `sentence-transformers`.
- **Keys.** The repository ships none. Check says which hosted provider still needs its key, and the
  mapping stage refuses to hand the careful reading, the re-check or the tie-break to a local model when
  a key is missing: it stops instead.
