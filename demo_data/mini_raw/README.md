# mini_raw — pre-fetched 5-doc slice for `main.py --mini-run --offline`

**What this is.** The raw inputs for the offline variant of the demonstration
mini-run: the 5 curated documents' P1 crawl artifacts, harvested byte-for-byte
from the shipped Hand-off #1 corpus (`stages/p1-scrape/handoff1_v2`, corpus
v2.4). Live-crawl evidence is the `.headers.json` sidecars plus the
`crawl_log.jsonl` slice — the offline path substitutes the fetch, not the
provenance.

**This slice is curated, not representative.** The 5 docs were chosen because
they verifiably produced rows in the full judged run and together cover all
three source types (html / pdf_native / pdf_scanned) and all three economies.
Outputs built from them are demonstration material, never the judged records.

| doc_id | economy | source_type | why chosen |
|---|---|---|---|
| `au-scia2018-001` | AU | html | Security of Critical Infrastructure Act 2018 — the HTML lane; P7-I2 KNOWN anchor `s.30CW(4)` |
| `au-ta1979-002` | AU | html | Telecommunications (Interception and Access) Act 1979 — strongest html NEW-row producer in the judged run (5 NEW rows in `records_AU`) |
| `my-cma1998-001` | MY | pdf_scanned | Communications and Multimedia Act 1998 — the mandatory scanned-OCR beat with live gold-page CER |
| `my-pdpa2010-001` | MY | pdf_native | Personal Data Protection Act 2010 — KNOWN anchors, 257 provisions in the full run |
| `sg-pdpa2012-001` | SG | pdf_native | Personal Data Protection Act 2012 — the canonical `s.26(1)` trap-doc walkthrough case (P6-I4 applies / P6-I1 rejected) |

**Contents**

- `manifest.csv` — the 5 corresponding rows of the shipped corpus manifest,
  fields unchanged (contract 0.2.x; validates against
  `stages/p2-extract/00_contracts/schemas/manifest.schema.json`).
- `raw/**` — 4 of the 5 raw bodies at their manifest `local_path`, SHA-256
  verified against the manifest's `content_sha256` at harvest time.
- `raw/**/*.headers.json` — all 5 HTTP header sidecars (fetch evidence).
- `crawl_log.jsonl` — the 5 crawl-log lines for these fetches (URL, status,
  retrieval method, timestamps), sliced from the shipped
  `handoff1_v2/crawl_log.jsonl`.

**The scanned PDF body is not duplicated here.** `my-cma1998-001`'s 12 MB raw
scan is committed once at `demo_data/my-cma1998-001.pdf` (byte-identical to
the corpus copy — SHA-256
`3f01e2a123551e6c28bf446b7c35403b3e2e43c44f9c145585e0c74dd1455c2a`, matching
the manifest row). `main.py` stages it to the manifest `local_path` inside the
run's work directory during offline substitution.
