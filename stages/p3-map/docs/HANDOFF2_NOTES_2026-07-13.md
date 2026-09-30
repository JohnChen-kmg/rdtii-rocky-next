# Hand-off #2 release notes — full-corpus run 2026-07-13

What Project 3 (and any reviewer) should know about the delivered corpus,
beyond the frozen [INTERFACE_CONTRACT.md](../INTERFACE_CONTRACT.md) (v0.2.0).
Everything here is observable in the data; nothing changes the contract's
grounding or schema guarantees.

## Contents

**305,980 Provision-Records across 2,616/2,616 manifest laws** (SG 94,892 ·
AU 157,204 · MY 53,884; by lane: native 224,080 · html 57,975 · ocr 23,925).
Final `p2-extract validate` (with `--manifest`): schema PASS, byte-exact
grounding PASS on every record, doc_status/laws/by_law/source_text
completeness PASS, provision_id uniqueness PASS.

- 2,455 docs yielded records; **158 docs are `zero_provisions`** (91 html,
  59 native, 8 scanned) — parsed clean, nothing citable segmented; their
  `laws.jsonl` rows carry `provision_count: 0, searched: true`, which is the
  input P3 uses for "No provision found" rows. Mostly AU non-act instrument
  pages and pre-1980 MY acts with unusual layouts.
- **3 docs are `parse_failed`** (2 MY PDP codes of practice + 1 OAIC guidance
  page — portals without per-portal parsers, decision #5). Visible in
  `doc_status.jsonl` with reasons.

## Seam details P3 must handle

1. **`provision_id` disambiguator suffix `~n`.** Consolidated statutes and
   bilingual gazette reprints restart section numbering, so a repeated
   citation within one doc gets `doc_id#s.5`, `doc_id#s.5~2`, ... The
   `article_section` field keeps the honest human citation (`s.5`) — join on
   `provision_id`, cite with `article_section` + `location_reference`.
2. **`cer_method: "engine_fixture_estimate"`.** Scanned docs without their own
   committed reference carry the conservative pilot-fixture CER (0.0272) in
   `ocr_quality_cer`, with full provenance in `ocr/<doc_id>/cer_report.json`.
   Only `gold_page`/`native_twin` reports may claim the <5% rubric item
   (`cer.py: meets_rubric`); the demo doc `my-cma1998-001` carries a live
   measured 0.0272 (`gold_page`).
3. **Mixed tagging models, stamped per record.** 305,937 records tagged by
   `claude-haiku-4-5` (Batches API); 43 records in `my-cma1998-001` carry
   `qwen2.5:14b` tags from the no-key Deliverable-#4 demo run. Trust
   `extraction_model`/`model_version` on the record, never a global assumption.
4. **Bilingual MY gazettes.** Some scanned gazettes print Malay then English
   full texts; both halves are real grounded provisions (the Malay ones carry
   `~n` ids). An English keyword prefilter simply won't match the Malay
   twins — that is expected, not missing coverage.
5. **AU `location_reference` cosmetic noise.** ~15% of AU native-PDF locators
   include a trailing TOC page number in the Part/Division label (e.g.
   `Division 3 — Injunctions 341`). Harmless for humans, don't parse numbers
   out of hierarchy labels.

## Tag semantics (contract §2.6a reminder + measured numbers)

`scope`/`data_type`/`obligation_type` are **non-exclusive soft routing
hints** — they may boost a candidate, never exclude one. Measured on the SG
PDPA with identical code: deterministic fields byte-identical 309/309 across
qwen2.5:14b, llama3.1:8b, claude-haiku-4-5; local-model tag agreement
(one-provision prompts): obligation_type 80.6%, data_type 49.2%, scope 46.6%.
Distribution over the corpus: `other` 87.5%, `dp_framework` 7.6%,
`gov_access` 2.0%, `conditional` 1.4%, cross-border/localisation classes
(`ban`+`conditional`+`storage`+`infrastructure`) = **6,297 provisions**
(SG 2,128 / AU 3,087 / MY 1,082) — a strong P6 prefilter start, never a gate.
Invalid model enum output is normalized to safe defaults with confidence
capped at 0.3 (18 of 282k occurrences observed), so low confidence means
"widen the search".

## Cost evidence

`handoff2/cost_report.json` is consolidated: extraction 161 s wall (native +
html), 12,292 OCR pages ≈ 100 min wall (6 parallel workers, cached forever in
`source_text/`), four tagging batches totalling **$106.81** (measured tokens,
50% Batches discount) + $0.48 paid test slices = **$107.29 ≈ 4.1¢/law**.
Local fallback measured at 1.02 provisions/s, $0. Per contract §5.3, no
cross-provider output parity is claimed — identical citations + disclosed tag
deltas is the claim.

## Reproducing / extending

```powershell
# verify everything offline
p2-extract validate --provisions ..\handoff2\provisions.jsonl --manifest <manifest.csv>

# re-run any doc (OCR is cached; add --force to re-OCR)
p2-extract run --only-doc <doc_id> [--skip-tags]

# tag anything untagged via the Batches API
p2-extract tag-corpus --only-untagged
```
