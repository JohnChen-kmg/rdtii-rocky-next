# DATA — what each run mode needs

Rule of this repo: nothing claims what its bytes can't show. Where data is not
shipped, the manifests, hashes, and logs that **prove and verify regeneration**
are shipped instead.

Corpus context (v2.4+segfix): **411,986 grounded provision records** across
**2,673 documents** (SG 536 / MY 869 / AU 1,268; forms: 2,228 native PDF /
43 scanned PDF / 402 HTML). 100% byte-exact grounding, validated.

## At a glance

| You want to… | Command | Needs beyond a clone |
|---|---|---|
| See the judged results (serve, default) | `python main.py --economy Singapore --pillar 6` | **Nothing.** Judged records are committed in `submission/`; serve is stdlib-only — no key, no network, no installs. |
| Watch scanned-PDF OCR live | `python main.py --demo` | `demo_data/` (committed) + **Tesseract 5**. Key optional — keyless falls back to local Ollama and says so. |
| Run 2 documents end-to-end (5–10 min) | `python main.py --quick` | Same as `--demo`; API key recommended (the 5–10 min timing is measured on the keyed stack). |
| Run a real 5-document pipeline slice | `python main.py --mini-run` | Same + **live portal access** — or `--offline`, which substitutes the pre-fetched raw files + provenance sidecars with a loud label. |
| Re-verify grounding of every record | — | GitHub Release **`v1.0-data`** (this repo): `handoff2_core.zip` + `handoff2_source_text.zip`. |
| Rebuild the whole corpus | see §Full re-run | `stages/p1-scrape`, ~6–8 h live crawl, then P2/P3 per their stage READMEs. |

## Mode details

- **serve** — filters the committed `submission/records_<ECON>.csv/json` by
  pillar and writes `outputs/<economy>_P<pillar>_<timestamp>.csv` + `.json`
  (exact 13-column order preserved; JSON keeps the per-law `provisions[]`
  grouping and the host's extra fields). `--economy` is typo-tolerant.
- **`--demo`** — re-runs OCR on the committed scanned Communications and
  Multimedia Act 1998 (`demo_data/my-cma1998-001.pdf`) and re-measures the
  gold-page CER **live** (0.00% on the committed gold page).
- **`--quick`** — 2 documents through the pipeline live: `au-scia2018-001`
  (HTML) + `my-pdpa2010-001` (native PDF).
- **`--mini-run`** — 5 documents spanning all 3 economies and all 3 source
  types, including one 144-page full OCR. P3 uses the bm25-only prefilter leg
  (no embedding-model download; CPU-instant). Output is stamped
  "demonstration slice — NOT the judged submission records."
- **`--full-pipeline`** — prints the per-stage commands and points here. It
  does not pretend to run 6–8 hours of crawling for you.

## Release assets — Release `v1.0-data` on this repo

| Asset | Contents | Needed for |
|---|---|---|
| `handoff2_core.zip` | `provisions.jsonl`, `laws.jsonl`, `doc_status.jsonl`, `extract_log.jsonl`, `cost_report.json` | Grounding re-verification (with `source_text`); parse/OCR status per document |
| `handoff2_source_text.zip` | frozen extracted source text | Grounding re-verification; keyword search of full text |
| `handoff2_by_law.zip` | per-law JSON grouping | convenience view |
| `handoff2_ocr.zip` | OCR outputs | OCR inspection |

Grounding re-verification = re-checking every quoted span in `provisions.jsonl`
byte-for-byte against the frozen text in `source_text/` — the same check the
pipeline's own validate gate runs ("no quote = no record"). Core + source_text
are sufficient for this.

## Full re-run — regenerating the corpus

The raw crawl corpus (~1.85 GB) is **not shipped** (size). Regenerate it with
`stages/p1-scrape` (commands quoted from its README; ~6–8 h, resumable, safe
to interrupt — re-running skips every law already retrieved):

```powershell
cd stages/p1-scrape
py -3 -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m playwright install chromium

# the complete 3-economy corpus (~6-8 h, resumable, safe to interrupt)
.\.venv\Scripts\python scrape.py --economy SG,MY,AU --scope all --out handoff1

# validate the hand-off against the frozen schema
.\.venv\Scripts\python scrape.py --validate handoff1\manifest.csv
```

Then run P2 extraction and P3 mapping per `stages/p2-extract/README.md` and
`stages/p3-map/README.md`.

**Proof without the bytes.** Committed in `stages/p1-scrape`:
`manifest.csv`/`manifest.jsonl` (2,706 rows = 2,673 current + 33 superseded;
per-file `content_sha256`; HTTP provenance), `crawl_log.jsonl` (every URL
touched, including failures), and `cost_report.json`. These prove what was
fetched, and they verify a regeneration: the validate gate checks schema +
integrity, and comparing `content_sha256` per file against the committed
manifest identifies byte-identical retrievals versus documents the portals
have since updated (portals serve current consolidations, so a later crawl may
legitimately differ — the hashes show exactly where).

## Environment notes

- **CPU-only Torch for `stages/p3-map`** — its lock pins `torch==2.6.0+cu124`
  (CUDA). Without CUDA, install Torch first:
  `pip install torch --index-url https://download.pytorch.org/whl/cpu`
  then the rest of the P3 requirements.
- **Tesseract 5** — `winget install UB-Mannheim.TesseractOCR`. Malay tessdata
  is vendored in-repo; no extra language-pack download.
- **Keys** — the repo ships no API key. The portal environment-file upload
  carries a fresh, spend-capped key (rotated after judging). Keyless, every
  LLM step falls back to local Ollama and says so; measured keyless speed is
  ~7–11 s/provision (llama3.1:8b) — slower, disclosed.
