# P0 — the RDTII 2.1 measuring instrument

> **Finale draft (2026-09-13).** The instrument now covers all twelve pillars: 61 scoreable
> indicators of the 62 the host lists (6.5 is non-regulatory and declared out of scope), with decimal
> text IDs throughout. Tiers: A 9 (pillars 6-7, Round 1) · B 14 (drafted, pending review) ·
> C 38 (extracted by script from the host methodology sheet), all 61 blocks in
> `output/indicators.yaml` in host order. Health check:
> `RDTII_GUIDE_TEXT=<page-numbered Guide text> python -X utf8 scripts/validate_instrument.py`
> → `PASS — 61/62 indicators in scope ...`. Inventory and build order: `output/README.md`.
> The sections below describe the Round 1 build and remain accurate as history.

The frozen instrument every downstream stage obeys. Before any crawling or
mapping, P0 converted the host's published methodology (RDTII 2.1 guide,
Round-2 methodology sheet, assignment answer keys, Round-1 baseline) into
machine-readable artifacts. Built 2026-07-12, hardened 2026-07-16, then
**vendored byte-for-byte into the mapping stage** — see
`../p3-map/contracts/instrument/` (hash-identical copy) — so the mapper can
never drift from the codebook it is scored against.

## Health check (one command)

```
pip install -r requirements.txt
python scripts/validate_instrument.py
```

Expected: **PASS — 9/9 indicators**; category names + score sets machine-match
the methodology sheet; every signature carries >=3 exemplars; gold rows
round-trip 1:1. Committed transcript of the last run:
`output/VALIDATION_2026-07-16.txt`.

## What's in this folder

### `output/` — the instrument itself (what P2/P3 consume)

| File | Usage |
|---|---|
| `indicators.yaml` | The 9-indicator codebook (P6-I1..I4, P7-I1..I5): definitions, 0/0.5/1 scoring trees, TRAP warnings (ban-vs-conditional, min-vs-max retention, inverted polarity), and the triple-source attestation header. The single source of truth for every mapping verdict. |
| `policies.yaml` | Cross-cutting mapping policies (sectoral-vs-horizontal handling, evidence conventions, scope rules) applied to all indicators. |
| `signatures/P6-I1.yaml … P7-I5.yaml` | Per-indicator relevance signatures: keywords, embeddable definition text, negative signals pointing at the correct sibling indicator, and 6–8 curated exemplar provisions with teaching notes + workbook provenance. Used by the mapping stage's retrieval (S1 prefilter) to find candidate provisions **by meaning**, not act name. |
| `gold/gold_set.jsonl` | All 51 Round-1 baseline rows for SG/MY/AU, normalized (AU 11 / MY 26 / SG 14; 2 rows flagged `suspect` with cited reasons). **Post-mapping use only**: NEW/KNOWN reference, Malaysia error-check targets, evaluation. |
| `README.md` / `INSTRUMENT_NOTES.md` | Artifact inventory / the human write-up (the 8 traps, baseline quirks). |
| `VALIDATION_2026-07-16.txt` | The validator PASS transcript (exit 0). |

### `scripts/` — build + verify

| File | Usage |
|---|---|
| `rdtii_examples.py` | Shared workbook parser; defines the two input paths (see below). |
| `build_signatures.py` | Builds the 9 signature YAMLs (curated SPEC tables + workbook mining). |
| `build_gold.py` | Extracts + normalizes the 51 baseline rows into the gold set. |
| `validate_instrument.py` | The health-check gate described above. |

### Inputs & references

| Item | Usage |
|---|---|
| `examples/Round1_Baseline_Database.xlsx` | Host Round-1 baseline (SG/MY/AU sheets) — input to `build_gold` + validator round-trip. |
| `examples/Round2_Methodology_and_Examples.xlsx` | The methodology sheet the validator machine-checks `indicators.yaml` against. |
| `reference/` | Rubric + target-output distillations, host legal inventory + portal CSVs, the 13-column output template. |
| `framework/RDTII_hackathon_knowledge_base.md` | Distilled framework notes used during curation. |
| `START_HERE.md`, `PLAN.md`, `INTERFACE_CONTRACT.md`, `TOOL_WORKFLOW_PROPOSAL.md` | Orientation, method, the schema contract downstream stages rely on, design provenance. |

## Workflow (how the instrument was built — Stages A–E)

1. **A — source freeze**: host methodology documents collected and pinned.
2. **B/C — signatures** (`build_signatures.py`): per-indicator keyword sets,
   definitions, negative signals, and curated exemplars mined from the host
   workbooks, each with provenance (workbook / sheet / row).
3. **D — gold set** (`build_gold.py`): the 51 baseline rows normalized;
   contradictions with the framework docs get `label_flag` with cited reasons.
4. **E — validation** (`validate_instrument.py`): machine-checks the whole
   instrument; the committed PASS transcript is the release gate.
5. **Hand-off**: `output/` vendored into `p3-map/contracts/instrument/`;
   the mapping stage pins `INSTRUMENT_DIR` to that copy.

## Provenance notes

- Indicator definitions are **triple-attested** (Round-2 methodology sheet
  rows 29–39 · RDTII 2.1 Guide pp.60–75 · internal guide FAQ) — and explicitly
  NOT sourced from the output template's "Indicator Reference" tab, which is
  wrong (GDPR-style taxonomy); that warning is encoded in
  `output/indicators.yaml` itself.
- Host-published documents (~9 MB of guide PDFs and workshop/assignment
  materials) are **cited by title, not vendored** in this submission copy.
  The two workbooks the scripts read are retained (paths defined in
  `scripts/rdtii_examples.py:19-20`).
