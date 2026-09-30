# Foundation sync — 2026-07-14 (read before building anything)

P2 shipped the full corpus on 2026-07-13. Before P3's build starts, a four-agent
seam audit compared what this folder's docs *expect* against what Hand-off #2
*actually contains*. This note records (a) what was synced into this folder today,
(b) the four T0 blockers found and their resolutions, and (c) the seam facts the
code must handle. **Where this note disagrees with PLAN.md, this note wins**
(same precedence rule as `KICKOFF_DECISIONS_2026-07-12.md`).

The delivered corpus (verified by direct count on disk, not from P2's report):
**305,980 provision records / 2,616 manifest docs**, `Desktop\handoff2\`,
every record stamped `contract_version 0.2.0`. Read
`HANDOFF2_NOTES_2026-07-13.md` (copied here) — it is P2's own list of seam
details P3 must handle.

---

## A. What was synced into this folder today

| Item | Action |
|---|---|
| `00_contracts/schemas/` | **Created.** `provision.schema.json`, `laws.schema.json`, `manifest.schema.json` vendored (plain copy, contract §8.1) from `rdtii-p2-extract/00_contracts/schemas/` — the copies P2's final `validate` ran against. |
| `INTERFACE_CONTRACT.md` | **Replaced** with P2's synced v0.2.0 copy (this folder had a stale pre-sync revision still pinned 0.1.0). |
| `requirements.txt` | Fixed `anthropic>=0.5x` → `anthropic>=0.40` (the literal `x` broke `pip install` outright — same typo P2 had). |
| `PLAN.md` | Patched stale literals: contract pin 0.1.0→0.2.0 (header + §9 table), `rank_bm25`→`bm25s` (3 spots), hardcoded `handoff1/`→resolve via `.env` (`handoff1_v2/` is what P1 shipped). |
| `docs/` | Added `HANDOFF2_NOTES_2026-07-13.md` + `RDTII_PROGRESS_REPORT_2026-07-14.md` from P2. |
| `contracts/instrument/` | Hash-verified byte-identical to P0 `output/` (all 14 files); refreshed the stale stub `README.md`. |
| `reference/rdtii_official/` | Added: ESCAP RDTII 2.1 guide + internal guide + non-regulatory-indicators PDF, Round 2 Database, hackathon knowledge base, Q&A summary, SG/MY/AU Legal Inventory CSV. |
| `reference/assignments/` | Added both take-home assignments complete (briefs, answer key + feedback, practice dataset, hands-on slides) — the host's worked mapping examples. |
| `reference/submission_templates/` | Added `OUTPUT_TEMPLATE_31MAY.xlsx` (the exact filename `indicators.yaml`'s WARNING references; same artifact as `reference/OUTPUT_TEMPLATE.xlsx`), README template, pitch-deck template, format-requirements PDF. |
| `reference/pre_application/` | Added the pre-application set: `Technical_memo_rocky.pdf` (the architecture the judges saw at application — the anchor for the "how the project has grown" pitch narrative), the concept-video document, hackathon knowledge base. |
| `reference/research_literature/` | Added the full `05_Research` literature: **AI for law** (LegalBench-RAG, legal-RAG hallucinations, reasoning-focused legal retrieval, legal IE pipelines — grounds the prefilter/verify design), **AI paper** (deep-research agents, Agent Laboratory, semantic triple extraction), **AI for econ** (AI agents for economic datasets), each with its summary .md. |

## B. The four T0 blockers and their resolutions

1. **Contract-pin drift (fixed above).** The corpus stamps `0.2.0`; this folder
   said `0.1.0`. `.env` `CONTRACT_VERSION` is the single runtime source of the
   pin; the §8 gate compares MAJOR only.
2. **Schemas were never vendored (fixed above).** PLAN's T0 gate requires
   `00_contracts/schemas/provision.schema.json`; it now exists.
3. **`requirements.txt` was uninstallable (fixed above).**
4. **⚠️ DESIGN DECISION — `laws.jsonl` coverage fields are empty.**
   `indicators_searched` and `pillars_in_scope` are `[]` in **2,587 of 2,613**
   rows (e.g. SG Computer Misuse Act: 80 provisions, both arrays empty). The
   contract §7.2 expected-cell enumeration (`indicators_searched ×
   pillars_in_scope`) therefore enumerates almost nothing.
   **Resolution: build the coverage grid as (every laws.jsonl `doc_id`) × (the
   9 in-scope indicators from `contracts/instrument/indicators.yaml`), using
   laws rows only for `provision_count`/`searched`.** Never read the two empty
   fields. (Optionally raise with P2 whether to backfill; not required.)

## C. Seam facts the code must handle (from the audit + HANDOFF2_NOTES)

**Identity & joins**
- `provision_id` is an **opaque join key**: 9,975 records carry a `~n`
  disambiguator (`sg-pdpa2020-001#s.48R(2)~2`) from consolidated statutes and
  bilingual reprints. Never split on `#` to recover the section; cite via
  `article_section` + `location_reference`. Add a `~n` fixture to ingest tests
  and to NEW/KNOWN canonicalization.
- `laws.jsonl` has **2,613 rows, not 2,616**: the 3 `parse_failed` docs
  (`my-pdpcpbfs2017-001`, `my-pdpcpcs2017-001`, `au-piag-001`) have no
  laws/by_law/source_text entries — enumerate them from `doc_status.jsonl`
  (non-contract extra) or by diffing the manifest. Report 2,613 vs 2,616
  honestly in coverage claims.

**Validation & ingest**
- Validate records against the **vendored `provision.schema.json`** (38
  properties, 25 required, `additionalProperties: false`) — never a Pydantic
  model hand-rolled from the contract §3.3 prose table (real records carry 10+
  additive fields beyond it: `snippet_source`, grounded-metadata offsets,
  `model_version`, `processing_time_seconds`, …).
- `provisions.jsonl` is **639 MB — stream line-by-line**, never json-load whole.
- `instrument_version` is **null** in every record (contract §8: informational,
  never gate). `last_amended` is portal-format prose ("1 December 2021"), not ISO.
- `handoff2/` contains non-contract extras (`doc_status.jsonl`,
  `tag_inputs.jsonl` ~278 MB, `tag_batch_state.json`, `cost_report.json`,
  `ocr/`, and a `<doc_id>.pages.json` page-offset sidecar per source text —
  free page-anchored audit deep-links). Glob `source_text/*.txt` explicitly;
  don't fail ingest on unknown files.

**Output hygiene**
- **44,710 provision records (and 359 laws rows) carry literal `\n` inside
  `law_number`** (e.g. `"Act\n14"`). `law_number` is CSV column 3 — collapse
  internal whitespace in the CSV writer for all string columns; add a
  newline-bearing fixture to the 13-col tests.
- ~15% of AU `location_reference` values have trailing TOC page numbers
  ("Division 3 — Injunctions 341") — display-only, never parse.

**Provenance & claims honesty**
- **Mixed models, stamped per record:** 305,937 records tagged by
  `claude-haiku-4-5`, 43 by `qwen2.5:14b` (the no-key demo doc). Never assert a
  global model string; pass `extraction_model`/`model_version` through.
  (The contract's `claude-sonnet-5-<pinned>` example is illustrative — no
  date-suffixed id exists.)
- **CER honesty:** 475/476 OCR docs carry `cer_method: engine_fixture_estimate`
  (the conservative pilot 0.0272, not per-doc measurement); only
  `my-cma1998-001` is `gold_page`-measured. The <5% rubric claim is made on
  gold-page docs only. `doc_status.doc_cer` is null everywhere — per-doc CER
  lives in `ocr/<doc_id>/cer_report.json` and record `ocr_quality_cer`.
- **Tags are soft boosts, never gates** (measured local-model agreement as low
  as 46.6% on `scope`). `extraction_confidence` skews low by design (0.1 on
  perfectly valid records); ≤0.3 can mean normalized invalid enum output —
  it signals "widen the search", never exclusion.
- **Bilingual MY gazettes:** Malay + English twins are both real grounded
  provisions (Malay ones carry `~n` ids). English keyword prefilters won't match
  Malay twins — expected, not missing coverage. Exclude Malay twins from
  prefilter-recall denominators; dedupe measure rows by (doc_id, canonical
  article_section) preferring the English twin.
- 6,297 provisions pre-flagged with cross-border classes
  (ban/conditional/storage/infrastructure: SG 2,128 / AU 3,087 / MY 1,082) — a
  strong P6 prefilter *start*, never a gate.

**CLI & config**
- Build `cli.py` from **contract §7's** `run` invocation (`--provisions --laws
  --source-text --manifest`) — PLAN §10.2 omits `--laws`/`--source-text`/
  `--manifest` (contract wins by its own precedence rule).
- `.env.example` lacks keys PLAN/KICKOFF name: `PREFILTER_TOPK`,
  `PREFILTER_FLOOR`, `NEWKNOWN_SIM`, `COST_HARD_STOP`, `EXEMPLAR_PROFILE` — add
  with defaults at T0.
- `final_record.schema.json` exists nowhere yet — **P3 authors it** (it is P3's
  own output contract), stamped `contract_version 0.2.0`, contributed back to
  `00_contracts/`.

---

*Produced from the 2026-07-14 seam audit (4 agents: P3-expectations reader,
P2-actuals reader, corpus spot-check, drift diff). Corpus counts in §B/§C were
measured directly on `Desktop\handoff2\`, not quoted from P2's report.*
