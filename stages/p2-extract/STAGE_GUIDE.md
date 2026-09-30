# P2 stage guide — OCR + grounded provision extraction (submission-repo orientation)

> Submission-repo documentation layered on top of the stage. The stage's own
> `README.md`, docs, fixtures, and code are preserved **verbatim** from the
> source repository (every committed file is hash-identical to it).

## What this stage is

P2 turns the raw files P1 fetched (HTML, native PDF, scanned PDF) into
article-level **Provision-Records** — the citable units all indicator mapping
stands on. The core discipline is **"no quote = no record"**: every document's
text is normalized once and frozen as `source_text/<doc_id>.txt`; every quoted
snippet must be a character-exact substring of that frozen text at recorded
byte offsets, re-verified before any record is written and again at
`validate`. The LLM (Claude Haiku via the Batches API, or local Ollama at $0)
adds only **soft routing tags** — every load-bearing field (quotes, offsets,
citations) is deterministic and never touches a model.

Current output (**Hand-off #2**, corpus v2.4 + segmentation fix):
**411,986 records** across 2,673 documents (SG 95,320 · AU 251,332 ·
MY 65,334); 2,486 docs with records + 184 zero-provision + 3 parse-failed.
Measured cost **$177.52**, ledger-exact (`cost_report.json` in the payload).

## What's shipped here vs. external

| Shipped in this stage | Usage |
|---|---|
| `src/rdtii_p2/` + `tests/` (82 tests) + `pyproject.toml` / `requirements.lock` | The runnable pipeline (`pip install -e .` → `p2-extract` CLI). Apache-2.0. |
| `fixtures/ocr_reference/` | The OCR honesty kit: committed gold pages + `cer_report.json` (CCA-1997 p.5 → **0.93%** CER; CMA-1998 p.36 → **0.00%**), incl. a full committed scan (`my-cca1997-001.pdf`) so a reviewer can recompute CER end-to-end. |
| `fixtures/tessdata_local/msa.traineddata` | Malay Tesseract language pack (MY scans). |
| `docs/HANDOFF2_NOTES_2026-07-{13,14,15,18,18b}.md` | The dated release-note chain — every corpus delta, with per-doc counts, measured costs, and the **Known extraction limitations** disclosures. |
| `docs/delta_20260718b/` | Committed fix evidence: `validate_summary.txt` (exit 0, 411,986, schema/grounding PASS), survivor lists, before/after counts. |
| `docs/delta_20260718/`, `docs/delta_20260714/` | Multi-volume retirement evidence (`retire_log.json`, old-vs-new counts), tagging comparisons. |
| `00_contracts/` | The Hand-off #2 schema (provision.schema.json) — the seam contract with P3. |
| **NOT shipped: the `handoff2/` payload** (~2 GB) | provisions.jsonl, source_text/, by_law/, ocr/ — distributed as Release assets + regenerable; see `docs/DATA.md` at repo root. |

Related in this repo: `demo_data/my-cma1998-001.pdf` (root) — the scanned
Malaysian CMA 1998 used by the demo command below (kept out of the source
repo by size policy; committed here as the demo artifact).

## Code map (`src/rdtii_p2/`, from the modules' own docstrings)

| Module | Usage |
|---|---|
| `ingest.py` | Manifest ingest: schema gate + contract-version gate + environment preflight (also filters superseded manifest rows in code). |
| `router.py` | Routes each document to its lane by source type. |
| `parse_html.py` | Lane A — per-portal HTML parsers. |
| `parse_pdf_native.py` | Lane B — native-PDF text extraction (pypdfium2). |
| `ocr_scanned.py` | Lane C — Tesseract OCR for the 43 scanned docs (per-doc results cached in the payload's `ocr/`). |
| `normalize.py` | Normalization applied ONCE, then frozen as `source_text/<doc_id>.txt` — the grounding substrate. |
| `segment.py` | Hierarchy-aware article-boundary detection (Parts/Divisions/Sections/**Schedules** — schedule-context segmentation emits ids like `sch.1 APP 8.1`). |
| `ground.py` | **The grounding gate** — "no quote = no record": asserts `source_text[start:end] == verbatim_snippet`; failures drop the record and are logged. |
| `extract_fields.py` | Provision-Record assembly: deterministic fields + grounded metadata + LLM soft tags. |
| `tag_batches.py` | Anthropic Batches API tagging lane (−50% cost; content-exact tag grafting on re-runs). |
| `cer.py` | CER measurement + `cer_report.json`; `meets_rubric()` enforces that the <5% claim can only rest on gold-page/native-twin measurements — estimates can never claim the bar. |
| `twin.py` | Native-twin comparison (scan vs. native text of the same document) — one of the two admissible CER reference methods. |
| `emit.py` | Hand-off #2 writers (provisions.jsonl, laws.jsonl, by_law/, doc_status.jsonl). |
| `status.py` | Per-document outcome ledger (ok / zero_provisions / parse_failed, with reasons). |
| `cli.py` | The `p2-extract` verbs below. |

## Workflow (how a corpus run flows)

1. **Ingest** the P1 manifest (schema + contract gates; superseded rows filtered).
2. **Route** each doc: HTML → parse; native PDF → extract; scan → OCR (Malay
   pack for MY).
3. **Normalize once, freeze** as `source_text/<doc_id>.txt`.
4. **Segment** into provisions with byte offsets (incl. schedule clauses).
5. **Ground**: every quote re-verified against the frozen text — failures are
   dropped and logged (drops are disclosed per run in the release notes).
6. **Tag** via Batches API (or local Ollama at $0 — empty key auto-falls back,
   loudly); unchanged records on re-runs re-use prior tags via content-exact
   grafting at $0.
7. **Emit + validate**: the validate gate re-checks schema, grounding
   (byte-exact for all records), and doc_status/manifest completeness; the
   verdict is committed as bytes (`docs/delta_20260718b/validate_summary.txt`).
8. **Deltas, never rebuilds**: corpus changes are absorbed additively with a
   dated HANDOFF2_NOTES entry (per-doc before/after counts + measured cost).

## Commands

```
pip install -e .                       # Python >= 3.11; Tesseract 5 for OCR lane
p2-extract run --manifest <handoff1>/manifest.csv --raw <handoff1>/ --out <handoff2>/
p2-extract tag-corpus [--dry-run]      # Batches API tagging (or local fallback)
p2-extract validate --provisions <handoff2>/provisions.jsonl
p2-extract pilot --scan <pdf> --gold <gold.txt> --page N    # standalone CER
p2-extract demo --doc my-cma1998-001   # Deliverable #4: live gold-page CER
                                       # re-measurement (0.00%) + full pipeline
python -m pytest tests -q              # 82 tests
```

## Honesty properties worth knowing before judging

- The <5% CER claim is **scoped in code** to committed, hand-keyed reference
  pages; all other scans carry a conservative disclosed estimate.
- Deterministic output is **model-invariant**: 309/309 SG PDPA records
  byte-identical across qwen2.5:14b, llama3.1:8b, and Claude Haiku. No
  cross-provider tag parity is claimed — identical citations + a disclosed
  tag delta is the claim.
- Known extraction limitations (18+3 under-segmented docs, 218 schedule-gap
  docs — none carrying pillar scope) are disclosed with committed survivor
  lists; full text remains keyword-reachable in `source_text/`.
