# Data dictionary — instrument, inputs, and outputs

What every file in the pipeline is, and the **variables inside each**. Field names
are the real ones (introspected from the files). Three parts:
**A. the instrument** (the rubric we code against), **B. inputs** (what we consume),
**C. outputs** (what each stage writes).

---

## A. The instrument — `contracts/instrument/` (read-only "law")

The vendored rubric. The code renders these into prompts and executes their clauses;
it never invents a rule. If the code and these files disagree, these win.

### `indicators.yaml` — the authoritative rubric for the 9 indicators
Top-level keys:
| key | what it is |
|---|---|
| `instrument_version` | version pin (2.1.0) |
| `methodology_source` | which official RDTII doc this was extracted from |
| `WARNING_DO_NOT_USE` | flags the template's GDPR-style "Indicator Reference" tab as wrong — do not use it |
| `scope` | which pillars/indicators are in scope (6.5 excluded, etc.) |
| `weights_note` | pillar weighting note |
| `score_polarity` | the global rule: 0 = low regulation … 1 = heavily regulated |
| `definitions` | shared terms: `personal_data`, `non_personal_data`, `processing`, `horizontal`, `sectoral` |
| `indicators` | list of 9 indicator blocks (below) |

Each entry in `indicators[]`:
| key | what it is |
|---|---|
| `id` | e.g. `P6-I4` |
| `pillar` | 6 or 7 |
| `name` | short name |
| `category_official` | official RDTII category label |
| `weight` | indicator weight |
| `question` | the core legal question the coder must answer |
| `definition` | full definition |
| `scoring` | the score values and what each means |
| `scoring_features` | features that drive the score |
| `scoring_tree` | the decision tree the model must follow |
| `coding_rules` | do/don't rules |
| `exceptions` | carve-outs (e.g. government data) |
| `disambiguation` | how to tell this indicator from its neighbours |
| `guide_examples` | worked examples from the official guide |

### `policies.yaml` — cross-cutting rules
| key | what it is |
|---|---|
| `instrument_version` | version pin |
| `measure_inclusion` | what counts as a measure: `enforced_only`, `non_preferential_only`, `official_sources_only`, `commercial_focus`, `vertical_coverage`, `regional_consistency` |
| `source_hierarchy` | ranked source types (statute > regulation > …) |
| `hierarchy_is_not_a_filter` | note: lower-tier sources are leads, not excluded |
| `citation_url_preference` | which URL to cite when several exist |
| `conflict_rule` | how to resolve conflicting sources |
| `citation_contract` | `requires`, `rule`, `verbatim_rule`, `section_rule` — the audit-trio requirement |
| `scoring_policy` | `polarity`, `score_greater_than_zero_means`, `absence_handling`, `score_is_hint_only` |
| `edge_cases` | `no_provision_found`, `repealed`, `broken_url`, `same_provision_two_indicators`, `one_indicator_many_laws`, `sectoral_and_horizontal`, `bad_country_input`, `dual_processing_and_storage` |

### `signatures/P*.yaml` — one per indicator (retrieval + triage inputs)
| key | what it is | used by |
|---|---|---|
| `indicator` | id | — |
| `name` | short name | S1 query, S3 prompt |
| `instrument_version` | version pin | — |
| `keywords` | trigger phrases (`unless`, `adequacy`, `whitelist`, …) | S1 query |
| `definition_text` | prose definition | S1 query, S3 prompt |
| `exemplar_law_types` | kinds of laws that typically match | reference |
| `scope_patterns` | `horizontal` vs `sectoral` scoring guidance | reference |
| `negative_signals` | the traps (what looks similar but is a *different* indicator) — **deliberately NOT in the retrieval query** | reference |
| `exemplars` | real Round-1/2 rows: `economy`, `law`, `coverage`, `score`, `impact`, `url`, `teaching_note`, `provenance` | S1 query (impact snippets) |

### `gold/gold_set.jsonl` — 51 hand-graded rows (the answer key for eval)
`gold_id` · `economy` · `indicator` · `raw_score` · `law` · `coverage` · `impact` ·
`timeframe` · `urls` · `note` · `articles_mentioned` · `label_flag` (marks the 7
label-noise rows) · `provenance`.

### `INSTRUMENT_NOTES.md`, `README.md` — human notes on how the instrument was built.

---

## B. Inputs — the corpus (`handoff2/`, produced by upstream P1/P2)

### `provisions.jsonl` — one row per extracted provision (411,986). 38 fields, grouped:
- **Identity:** `provision_id` (opaque join key, never split on `#`), `doc_id`, `economy`.
- **Law meta:** `law_name` (+ `law_name_grounded`, `law_name_char_start/end`),
  `law_number` (+ char offsets), `last_amended` (+ char offsets).
- **Text:** `article_section`, `verbatim_snippet`, `snippet_char_start/end`,
  `snippet_source`, `location_reference`, `raw_context_before`, `raw_context_after`.
- **Classification (soft hints):** `scope`, `data_type`, `obligation_type`,
  `extraction_confidence`.
- **Provenance:** `source_url`, `source_file_path`, `source_type`, `pdf_is_scanned`,
  `ocr_quality_cer`, `ocr_engine`, `retrieval_method`, `extraction_model`,
  `model_version`, `access_date`, `processing_time_seconds`.
- **Meta:** `contract_version`, `instrument_version`.

The byte-grounding guarantee: `verbatim_snippet == source_text[snippet_char_start:end]`.

### `laws.jsonl` — one row per law/document (2,673)
`contract_version` · `doc_id` · `economy` · `law_name` · `law_number` · `source_url`
· `pillars_in_scope` · `indicators_searched` · `provision_count` · `searched` · `notes`.

### `source_text/<doc_id>.txt` + `.pages.json` — raw law text (for byte-grounding & re-anchoring).
### `doc_status.jsonl` — per-doc extraction status (`ok` / `zero_provisions` / `parse_failed`).

### The baseline — `reference/Round1_Baseline_Database.xlsx` → parsed once to
`out/baseline_rows.jsonl` (the KNOWN answer key; fields: `baseline_id`, `economy`,
`indicator`, `law`, `urls`, `articles_mentioned`, `raw_score`, `in_p3_scope`).

---

## C. Outputs — what each stage writes

### `data/index/` (S0–S1, rebuildable)
| file | contents |
|---|---|
| `prefilter_corpus.jsonl` | compact per-provision record: `provision_id`, `doc_id`, `economy`, `text` (metadata-prefixed), `law_name`, `article_section`, `obligation_type`, `data_type`, `scope`, `grounding`, `lang_malay_guess`, `snippet_source` |
| `bm25_top.npz` / `dense_top.npz` | top-50k ranks per indicator (sparse / dense) |
| `embeddings.f16.npy` / `embed_meta.json` | dense vectors (resume marker) |
| `doc_meta.json` | per-doc economy/law_name/counts/status |

### `out/select/` (S2)
`direct_pairs.jsonl`, `gray_pairs.jsonl` — each row:
`provision_id` · `doc_id` · `economy` · `indicator` · `rrf` (fused score) ·
`law_name` · `article_section`.

### `out/triage/haiku_results.jsonl` (S3)
`provision_id` · `indicator` · `economy` · `keep` (bool) · `why` (≤120 chars).

### `out/map/verdicts_<ECON>.jsonl` (S4) — one row per provision
`provision_id` · `economy` · `doc_id` · `law_name` · `article_section` ·
`candidates` (indicators asked) · `core_legal_question_answer` · `who_is_regulated`
· `conditions_and_exceptions` · `trap_checks` · `verdicts` · `model`.
- `trap_checks`: `conditional_path_exists`, `retention_is_minimum`,
  `government_data_only`, `provision_in_force`, `sectoral_scope` (all bool).
- `verdicts[]`: `indicator`, `applies`, `coverage`, `score_hint` (`1`/`0.5`/`0`/`n/a`),
  `verbatim_quote`, `rationale`, `confidence`, `quote_grounded_ws`.
- Error rows instead carry just `provision_id`, `economy`, `error`.

### `out/verify/verified_<ECON>.jsonl` (S5) — one row per fire
`provision_id` · `indicator` · `economy` · `mapper` (the S4 verdict) · `trap_checks`
· `verifier` (Haiku: `applies`/`score_hint`/`confidence`/`reason`) ·
`escalation` (Opus, only if there was a tiebreak) · `verifier_verdict`
(`agree` | `tiebreak_upheld` | `tiebreak_overturned` | `split_flagged`) ·
`final_applies` · `final_score_hint`.

### `out/discovery/newknown_<ECON>.jsonl` (S7) — one row per verified fire
`provision_id` · `doc_id` · `law_name` · `article_section` · `economy` ·
`indicator` · `score_hint` · `coverage` · `verification` · `discovery_tag`
(`NEW`/`KNOWN`) · `baseline_match` (matched `baseline_id` or null) ·
`match_evidence` · `law_fuzzy` (match score).

### `out/rollup/economy_scores_<ECON>.json` (S6)
`economy` · `scores` = `{<indicator>: {score, basis, evidence_rows, pending}}`
(P7-I1/P7-I2 also carry `controlling_law`). The score lives here, never as a CSV column.

### `out/submission/records_<ECON>.csv` (S9) — **the judged deliverable, 13 frozen columns**
`Economy` · `Law Name` · `Law Number / Ref` · `Last Amended` · `Indicator ID` ·
`Article / Section` · `Discovery Tag` · `Location Reference` · `Verbatim Snippet` ·
`Mapping Rationale` · `Source URL` · `Confidence` · `Notes`.

### `out/submission/records_<ECON>.json` (S9) — richer, grouped per law
`contract_version` · `economy` · `economy_name` · `laws[]`, each
`{law_name, law_number, source_url, provisions[]}`. Each provision carries the 13
CSV fields **plus host extras** `source_pdf_path`, `ocr_quality_cer`,
`processing_time`, `model_version`, `raw_context`, and internal `_record_type`
(`scored`/`no_provision`), `_provision_id`, `_score_hint`.

### `out/eval/eval_report_<ECON>.json` (S10)
`economy` · `resolvable_gold_rows` · `row_recall` · `known_tag_accuracy_on_hits` ·
`misses[]` · `csv_rows` · `note` (MY also: `resolvability_note`).

### `out/errorcheck/malaysia_errorcheck.csv` (S8)
`Baseline Entry` · `Retrieved Provision` · `Check Class` (url/currency/substance) ·
`Correct / Not-correct` · `Discrepancy` · `Action` · `Baseline Source` ·
`Main-CSV crossref`.

### Supporting artifacts
| file | contents |
|---|---|
| `out/urlcheck/submission_urls_<date>.json` | `checked`, `not_ok`, `results[]{url, status, ok, rows}` |
| `out/cost_ledger.json` | `evidenced_total_usd`, `components[]{stage, amount, evidence_path, note}`, `unevidenced_components` |
| `out/preflight_report.json` | phantom-id gate: per-economy `pairs`/`ok`/`synthetic`/`phantom`, `verdict` |
| `out/{map,verify}/*_report_<ECON>.json` | per-run tallies + measured cost (cumulative merge) |
| `out/results/RDTII_P3_results_<ECON>.xlsx` | the human review workbook (per-indicator sheets) |
| `out/audit/index_<ECON>.html` | filterable per-fire evidence table |
| `docs/ab/*` | the A/B model-choice evidence (triage & mapper gates) |

---

*Grounded 2026-08-03 (corpus v2.4b). The instrument (`contracts/instrument/`) is the
source of truth for scoring; this dictionary describes files, not rules — if it
disagrees with a `.yaml`, the `.yaml` wins.*
