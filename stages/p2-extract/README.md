# rdtii-p2-extract — OCR & Tag Extraction (RDTII Rocky, Project 2)

Turns Project 1's raw retrieved files (Hand-off #1) into **grounded, article-level
Provision-Records** (Hand-off #2). Owns the **OCR <5% CER** rubric item and
**verbatim grounding**: every quoted snippet is a character-exact substring of a
frozen `source_text/<doc_id>.txt`, re-verified by offsets before any record is
written — *no quote = no record*.

Contract authority: [INTERFACE_CONTRACT.md](INTERFACE_CONTRACT.md) (frozen, v0.2.0).
Build plan: [PLAN.md](PLAN.md) + [docs/KICKOFF_DECISIONS_2026-07-12.md](docs/KICKOFF_DECISIONS_2026-07-12.md).

## Quick Start (Windows)

```powershell
# 1. venv + pinned deps (Python 3.11+)
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
.\.venv\Scripts\pip install -e .

# 2. OCR binary (Lane C / CER pilot only)
winget install UB-Mannheim.TesseractOCR
# Malay docs (my-pdpr2013-001): the msa pack lives in fixtures/tessdata_local/
# (system tessdata often not writable). Run those with:
#   $env:TESSDATA_PREFIX='<repo>\fixtures\tessdata_local'; $env:OCR_LANG='msa+eng'

# 3. local LLM for tag extraction (no API key needed)
ollama pull qwen2.5:14b        # dev GPU box
ollama pull llama3.1:8b        # CPU-viable judge-box default

# 4. configure the input seam
copy .env.example .env         # point HANDOFF1_DIR at the P1 corpus
                               # leave ANTHROPIC_API_KEY empty -> auto-Ollama

# 5. run + validate
.\.venv\Scripts\p2-extract run --only-doc sg-pdpa2012-001
.\.venv\Scripts\p2-extract validate --provisions ..\handoff2\provisions.jsonl
```

`run` is fully non-interactive. Entry gates fail loudly before any work:
manifest schema (28-field v0.2.0), contract-MAJOR compatibility, and an
environment preflight (Tesseract resolvable, configured Ollama model actually
pulled). Every stage streams one narration line per decision to stdout and
mirrors JSONL to `logs/`.

**No API key is required or shipped.** `LLM_PROVIDER=ollama` is the default;
an empty `ANTHROPIC_API_KEY` with `LLM_PROVIDER=anthropic` auto-falls back to
Ollama, loudly. Swapping any model-bearing engine (LLM or OCR) is a `.env`
edit, never a rewrite (`config/` factories, contract §5.2).

## CLI

```
p2-extract run        --manifest handoff1/manifest.csv --raw handoff1/ --out handoff2/
                      [--only-doc <id>] [--only-docs <file>] [--economy SG|AU|MY]
                      [--skip-tags]   # defer tags -> tag_inputs.jsonl (Batches lane)
                      [--force]       # re-OCR cached lane C docs
p2-extract tag-corpus [--model claude-haiku-4-5] [--batch-size 10] [--dry-run]
                      [--resume] [--only-untagged]   # Anthropic Batches API (-50%)
p2-extract validate   --provisions handoff2/provisions.jsonl [--manifest <csv>] [--check-urls]
p2-extract pilot      --scan <pdf> --gold <gold.txt> --page N  # T2b CER measurement
p2-extract demo       [--doc <scanned_doc_id>]                 # Deliverable #4: live
                      # gold-page CER + full pipeline on a manifest-retrieved scan
```

Two tagging lanes, one prompt: the **local lane** (`run` with Ollama) tags
inline with one-provision prompts, and the **API lane** (`run --skip-tags`
then `tag-corpus`) packs ~10 provisions per request through the Anthropic
Batches API at the 50% batch discount. Both use byte-identical tag
definitions; deterministic fields never touch the LLM in either lane.

`validate` runs the **hard offline gates**: JSON-schema validation
(`00_contracts/schemas/provision.schema.json`, `laws.schema.json`), the
grounding assertion `source_text[start:end] == verbatim_snippet` on every
record, scanned-source CER presence, and doc_status consistency. URL liveness
is advisory only (`--check-urls`) and never drops a record (contract §2.3a).

## Pipeline

```
manifest (entry gates) -> route by source_type (+ mis-flag recheck, §2.4.4)
  Lane A html        -> per-portal DOM parser (sections + deep-link anchors for free)
  Lane B pdf_native  -> pypdfium2 (Apache-2.0-safe; PyMuPDF is AGPL - do not add)
  Lane C pdf_scanned -> Tesseract 5 (pilot-validated <5% CER; see fixtures/ocr_reference/)
-> normalize ONCE (NFC, header/footer stripping, de-hyphenation) -> freeze source_text
-> hierarchy-aware segmentation (Part/Division/Section/Subsection + offsets)
-> deterministic fields + grounded law_name/number/last_amended (regex-first,
   value bytes copied from text, null-if-ungrounded)
-> LLM soft tags via get_llm() (scope/data_type/obligation_type - non-exclusive hints)
-> GROUNDING GATE -> handoff2/ (provisions.jsonl · by_law/ · source_text/ ·
   laws.jsonl · doc_status.jsonl · ocr/ · extract_log.jsonl · cost_report.json)
```

## Measured results — full three-country corpus (v2.4 delta update 2026-07-18)

All numbers below are **measured**, not estimated; the token counts and USD
figures are in `handoff2/cost_report.json`, and every gate is re-runnable via
`p2-extract validate`. Three upstream corpus re-issues were absorbed
**incrementally**: v2.1 (Malaysia re-crawled to current consolidations —
868 docs re-extracted, 7 renamed ids purged,
[notes](docs/HANDOFF2_NOTES_2026-07-14.md)), v2.3 (+32 additive regulator
instruments incl. one bilingual Malay scan OCR'd `msa+eng`,
[notes](docs/HANDOFF2_NOTES_2026-07-15.md)), and v2.4 (the judge-caught **AU
multi-volume truncation fix** — 33 acts re-extracted complete, truncated
extractions retired, acceptance-verified,
[notes](docs/HANDOFF2_NOTES_2026-07-18.md)).

| | |
|---|---|
| Laws processed | **2,673 / 2,673** extractable (Hand-off #1 corpus v2.4; manifest 2,706 rows incl. 33 provenance-only superseded) |
| Provision-Records emitted | **411,986** — grounded, offset-verified, tagged (SG 95,320 · AU 251,332 · MY 65,334), incl. **7,553 schedule-clause records** (`sch.1 APP 8.1`-style ids — the Privacy Act APPs are citable) |
| Docs with records | 2,486 (93.0%); 184 parsed clean with zero citable provisions; 3 failed (portal pages without per-portal parsers) |
| Lanes | HTML + native PDF + **OCR 35 docs with records** (43 scans — v2.1 flipped ~430 MY scans to native; incl. one bilingual Malay scan, `msa+eng`) |
| Final validate | schema **PASS** · grounding **PASS** (all 411,986 quotes byte-verified) · doc_status/manifest completeness **PASS** incl. the superseded-retirement gate · unique provision_ids **PASS** (re-run 2026-07-18 post segmentation fix; verdict committed at [docs/delta_20260718b/validate_summary.txt](docs/delta_20260718b/validate_summary.txt)) |

**Cost — two lanes, one engine, same prompts:**

| Lane | Wall-clock | Measured cost |
|---|---|---|
| Claude Haiku 4.5 via **Batches API** (full run + four deltas) | full run same-day; each delta absorbed same-day it shipped | **$177.52 total** ≈ **6.6¢/law** ≈ $0.00043/provision (ten batches totalling $177.04 + paid test slices $0.48; `cost_report.json` sums to this exactly). The segmentation-fix delta re-used 99,299 existing tags via content-exact grafting — $6.49 instead of ~$40 |
| Local Ollama (qwen2.5:14b, one consumer GPU) | measured ~1 provision/s | **$0** — proven as a real fallback: when a batch's sync-retry lane hit credit exhaustion, 407 provisions were repaired locally the same day (later re-tagged with Haiku after top-up; measured qwen-vs-Haiku comparison in `docs/delta_20260714/retag_api_comparison.json`) |

**Cross-model reproducibility (SG PDPA, 309 provisions, same code):**
deterministic fields — snippet bytes, offsets, citations, URLs, grounded
metadata — are **byte-identical 309/309 across qwen2.5:14b, llama3.1:8b, and
Claude Haiku 4.5**. Soft-tag agreement between the two local models in the
shipped configuration (one-provision prompts): `obligation_type` 80.6%,
`data_type` 49.2%, `scope` 46.6% — which is exactly why the contract makes
tags **non-exclusive routing hints** that can boost but never exclude an
indicator candidate downstream (§2.6a). The s.26(1) ban-vs-conditional trap
resolves to `conditional` on all three models. Per contract §5.3, output
parity between providers is **not** claimed; identical citations plus a
disclosed tag delta is the claim.

Small-model caveat (measured): packing 10 provisions per prompt degrades
llama3.1:8b tag quality (it fails the s.26(1) trap batched, passes single) —
so the local lane defaults to `TAG_BATCH_SIZE=1`; batching exists for the API
lane, where it cuts input tokens 2.4× and it does not change Haiku's answer
on the trap case.

Known limitations and seam details for Hand-off #2 consumers (provision_id
`~n` suffixes, bilingual MY gazettes, `engine_fixture_estimate` CER method,
AU locator cosmetics, the 184 zero-provision + 3 unparsed docs) are documented
in [docs/HANDOFF2_NOTES_2026-07-13.md](docs/HANDOFF2_NOTES_2026-07-13.md) and
the v2.1 delta notes
[docs/HANDOFF2_NOTES_2026-07-14.md](docs/HANDOFF2_NOTES_2026-07-14.md) —
**P3 must re-consume, not diff**: MY/SG provision_ids changed under v2.1.

## Known extraction limitations (disclosed, measured 2026-07-18)

- **18 AU docs remain under-segmented** (>100 KB of text, ≤10 provisions) —
  layouts that defeat every current segmentation pass (appropriation-style
  and pre-1980 consolidations; none carries `pillars_in_scope`). List:
  [docs/delta_20260718b/under_segmented_survivors.txt](docs/delta_20260718b/under_segmented_survivors.txt).
- **218 docs have schedule text without schedule-clause records** — almost all
  amendment acts (schedules = amendment instructions) and table-only schedules
  (e.g. tariff rate tables), deliberately not clause-segmented. List:
  [docs/delta_20260718b/schedule_gap_survivors.txt](docs/delta_20260718b/schedule_gap_survivors.txt).
- In both cases the **full text IS captured** in `source_text/` and is
  keyword-search reachable; only provision-level records are absent.
- **Record-level grounding drops are by design** (no quote = no record) and
  each is logged in `extract_log.jsonl` — distinct from doc-level parse
  failures (the 3 known portal gaps). Guidance-style PDFs segment coarsely
  (see the 2026-07-15 notes).

## OCR CER evidence (rubric item, 10 pts)

Measured on real Malaysian scans with hand-keyed gold pages — see
[fixtures/ocr_reference/README.md](fixtures/ocr_reference/README.md):
Computer Crimes Act 1997 p.5 **CER 0.93%**, Communications & Multimedia Act
1998 p.36 **CER 0.00%** on the corpus-v2.1 reprint scan (2.72% on the retired
pre-v2.1 gazette scan, quarantined with provenance), Tesseract 5.4,
reproducible via `p2-extract pilot`.

Deliverable #4 (`p2-extract demo`, re-run 2026-07-14): the manifest-retrieved
scanned CMA 1998 re-measures its gold page **live** — CER 0.00%, **meets the
<5% bar** — then runs the full pipeline; its 472 records carry the measured
value. The v2.1 scan is a different artifact than the one the original gold
page was keyed from, so p.36 was re-keyed from the new scan's page image
before any claim was made. Corpus scanned docs without their own committed
reference carry the conservative pilot-fixture figure (2.72%, deliberately
not lowered) with `cer_method: "engine_fixture_estimate"` disclosed in
`ocr/<doc_id>/cer_report.json`; the <5% claim is **only** made on gold-page /
native-twin references (enforced in `cer.py: meets_rubric`).

## Tests

```powershell
.\.venv\Scripts\python -m pytest tests -q
```

Golden tests pin the SG PDPA `s.26(1)` span, grounding drop-on-mismatch,
offset round-trips, furniture stripping, CER math (a `synthetic` reference can
never claim the rubric bar), URL composition, and the AU HTML parser shape.

## License

Apache-2.0. Dependency policy: no AGPL (PyMuPDF explicitly excluded);
versions pinned via `requirements.lock`.
