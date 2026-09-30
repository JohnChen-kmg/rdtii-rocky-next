# Mapping → UI handoff

**29 September 2026.** Written for whoever designs the interface. Everything here was verified
against the run and the repository today, not copied from earlier notes. Where a figure was wrong
in an earlier document, the correction is marked.

Read §1 before designing anything. It is a deadline problem, not a design problem.

---

## 1. The deadline, which constrains the design more than any requirement

The host's own timetable (`1_Rules/Framework/RDTII_hackathon_knowledge_base.md`, line 43):

| 30 September | **Round 2 final submission** |
| 15 October | Onsite final pitch + Award Ceremony, Bangkok |

30 September is **the host's submission deadline**, not an internal code freeze. And checklist item 2
reads: *"Final release tag recorded — that exact tag is what will run on 15 October."*

Two consequences for a new UI:

1. **A UI written after 30 September is not in the submission.** It can be shown at the Bangkok
   pitch, but it is not what a marker deploys, and C3a (10) + C3b (5) are marked on the tag.
2. **The tag today points at 2026-07-20.** `final-submission` → `2ba4be21`, and `finale` is 44
   commits behind `w2-mapping-finale`. As things stand a marker deploying the declared tag gets
   Round 1's interface reading Round 1's rows — none of the finale's work.

**Decision taken 29 September: the new UI is built from scratch.** `interface/dashboard.py` is not
being repaired. Three things follow, and they are the whole brief:

1. **A from-scratch UI must reimplement functionality, not just screens.** Items 9 and 21 are not
   "show which model is selected" — they require the AI backend to be **swappable from inside the
   interface with no code or config change**, and the swap to be watchable while it happens. That is
   the one part of `dashboard.py` worth reading before deleting it (§4).
2. **Whatever exists on 30 September is what gets marked.** A UI that deploys, runs, and lets a
   non-technical officer review rows beats a better-looking one that misses the tag. Rank the seven
   checklist items in §4 and build down the list.
3. **The repo must end up naming one interface.** If the old dashboard stays in the tree, the README
   and the Word document have to say plainly which one a marker deploys, or item 18 is ambiguous
   and C3a/C3b are marked against whichever a reviewer opens first. Deleting it is cleaner than
   explaining it.

One question worth sending to the host regardless, because item 2's wording says no but it has not
been asked: **may the interface be updated between 30 September and 15 October?** A yes changes the
whole calculus; the cost of asking is one email.

---

## 2. Where mapping stands

Complete and verified. 61 indicators, 6 economies, one run.

| | |
| :---- | :---- |
| Filed rows | **318** — AU 39, CN 55, LA 25, MY 53, SG 36, TL 27 + 83 |
| Coverage Matrix economies | 6 (host needs ≥3) |
| Pillars | all 12 appear; the two mandatory ones are pillar 6 (72 rows) and pillar 7 (163) |
| Languages of source | Chinese 55, Lao 25, Portuguese 110, English 128 (host needs ≥1 non-English) |
| Provisions judged | 14,456 across the six economies |
| Review workbook rows | 3,615 across 7 workbooks, of which 1,733 carry machine English |
| Machine English | 1,340 provision glosses + 1,145 quote glosses |
| Tests | 297 passed, 8 skipped |
| Spend to date | ~$269 |

**The binding constraint is no longer retrieval — it is curation.** The host's Output Data sheet has
rows 9–109, i.e. **101 slots for 318 rows**. Any UI that presents "our results" has to distinguish
*produced* from *filed*.

### Known-bad rows the UI should not present as sound

- **51% of filed Timor-Leste citations name the wrong act.** Measured today: of 364 multi-act
  Timorese gazette documents, **364 attach one document-level title to every act inside them** and
  0 vary by act. The extractor sets `act_index` correctly but does not resolve `law_name` per act,
  and reports `citation_confidence: "exact"` anyway. One hand-verified case: a credit-registry
  retention provision (a correct 7.3 hit, confidence 0.9) titled *Estatuto dos Combatentes da
  Libertação Nacional*, with `law_name_en` about police food allowances.
- **45 Timorese no-provision rows cite "Aprova o Código Civil"** as governing law — including for
  6.1, data localisation. Cause: Timor-Leste has no baseline sheet, so `_np_citation` falls through
  to "cite the largest law in the corpus", which in a civil-law jurisdiction is the Civil Code.
  **Being fixed tonight.**
- **225 of 14,456 provisions produced no verdict** (1.6%). Not empty replies: 124 were placeholder
  tool calls (`{'parameter name': 'value'}`), 47 malformed verdict objects, 29 rejected by our own
  validator, 25 other. **Being fixed tonight**, and they are now listed per provision on a new
  `QA Errors` sheet rather than existing only as a Summary count.

---

## 3. The data contract

Everything below is what the pipeline writes today. **Bind to these names.** The one prior failure
mode is exactly this: `interface/dashboard.py` was written on 12 September against
`work/p3out/map/verdicts_*` and `work/p3out/ingest_report.json`, and mapping's layout, economy table
and indicator scope all changed underneath it without anyone noticing.

### Directory layout

```
<RUN>/                                  e.g. rdtii-finale-p3-runs/run_2026-09-27  (2.8 GB)
  index/          prefilter_corpus.jsonl, embeddings.f16.npy, doc_meta.json,
                  bm25_top.npz, dense_top.npz
  out/            the six-economy, nine-indicator arm
    select/ triage/ map/ verify/ rollup/ discovery/ submission/ results/ audit/ eval/
    run_manifest.json  ingest_report.json  baseline_rows.jsonl
  out_tl52/       Timor-Leste against the other 52 indicators. SAME shape, separate directory.
```

**`out_tl52` is the trap.** Timor-Leste appears in both arms with the same file names. A UI that
globs `records_TL.csv` finds two different files. They must be read as two arms and, for any
economy-level total, summed — TL's 110 rows are 27 + 83.

### Per-economy files, and the key each one is joined on

| file | join key | holds |
| :---- | :---- | :---- |
| `submission/records_<E>.csv` | — | **the filed rows.** 14 columns, see below |
| `submission/records_<E>.json` | `_provision_id` | the host's per-law JSON: `{contract_version, economy, economy_name, laws[]}`, each law `{law_name, law_number, source_url, provisions[]}`; each provision carries the 14 column names verbatim plus `_provision_id`, `_record_type` (`scored` \| `no_provision`), `_score_hint`, `model_version`, `ocr_quality_cer`, `processing_time`, `raw_context`, `source_pdf_path` |
| `map/verdicts_<E>.jsonl` | `provision_id` | the mapper's reasoning: `article_section, candidates, conditions_and_exceptions, core_legal_question_answer, doc_id, economy, law_name, model, provision_id, trap_checks, verdicts[]`. **An error row has only `provision_id`, `economy`, `error`** — no other key. Check for `"error" in row` before touching anything else |
| `verify/verified_<E>.jsonl` | `(provision_id, indicator)` | `final_applies, final_score_hint, indicator, mapper, verifier, verifier_verdict, trap_checks`. **This is the file to read when a row looks wrong** — it carries the mapper, the verifier and the escalation reviewer each with their own reason |
| `rollup/economy_scores_<E>.json` | `scores[<indicator>]` | `{economy, economy_level_model, cost_usd, scores}`; each score `{score, basis, evidence_rows, pending}`. **Scores live only here** — they are not in the CSV and not in the workbook |
| `discovery/newknown_<E>.jsonl` | `(provision_id, indicator)` | `discovery_tag, baseline_match, law_matched_name, law_fuzzy, match_evidence, coverage, score_hint, verification` |
| `audit/gloss_<E>.jsonl` | `(provision_id, indicator)` | machine English of the **quote** |
| `audit/gloss_sections_<E>.jsonl` | `provision_id` | machine English of the **provision text** |
| `audit/index_<E>.html` | — | the current audit view. 5 columns; see §4 |
| `results/RDTII_P3_results_<E>.xlsx` | `Provision ID` | the review workbook; see below |
| `map/map_report_<E>.json` | — | `{provisions, verdict_fires, ungrounded_fires, errors, cost_usd, cost_note, batches[]}` |
| `submission/submission_report_<E>.json` | — | `{csv_rows, cells, dropped_before_curation, blank_discovery_tag}` |
| `eval/eval_report_<E>.json` | — | `{row_recall, row_recall_on_parsed_sources, law_match, misses, cited_but_unparsed_sources, known_tag_accuracy_on_hits, ...}` |

### Run-level files

| file | holds |
| :---- | :---- |
| `run_manifest.json` | `{run_id, created, git, engine, instrument, contract_version, settings, entries[]}` — **`engine` and `git` are what prove the engine swap for item 20 and J4.** `entries[]` carries per-stage `cost_usd` |
| `ingest_report.json` | `{stats, gates, records_streamed, elapsed_seconds, contract_version_mismatches, grounding_fail_samples, schema_error_samples}` |
| `select/select_report.json` | `{mode, selection_version, selection_config, totals, cells, languages, recall_gate}` |

### The 14 CSV columns, in order — this order is the host's

```
 1 Economy                 the official UN name, e.g. "Timor-Leste", not "TL"
 2 Law Name
 3 Law Number / Ref
 4 Last Amended
 5 Indicator ID            DECIMAL text: "6.1", "12.4.1". Never "P6-I1"
 6 Article / Section        "n/a" on a no-provision row
 7 Discovery Tag           NEW | KNOWN | "" (blank is meaningful, see below)
 8 Location Reference
 9 Verbatim Snippet        the SOURCE's own bytes. Never a translation
10 Mapping Rationale
11 Source URL
12 Confidence
13 Notes
14 Language of Source      a NAME: Chinese, Lao, Portuguese, English
```

Three rules a UI must not break:

- **Indicator IDs are decimal text.** The host's own formula in column O derives the pillar from
  this. Given `P6-I1` it returns `"?"`, and the Coverage Matrix's `COUNTIFS` then counts zero
  provisions for every economy. Any UI that re-writes, re-keys or re-formats an ID must preserve
  the decimal string, and must keep it as text so `6.10` does not become `6.1`.
- **Column O must stay empty in our output.** It is the host's formula. A 15th data column
  overwrites it.
- **A blank Discovery Tag is a deliberate value, not a missing one.** It means the row is neither a
  discovery nor a baseline reproduction. Do not render it as an error or coerce it to NEW.

### The workbook, per economy

Sheets: `Summary`, `All fires`, **one sheet per indicator**, then `QA Overturned`,
`QA Ungrounded`, `QA NotInForce`, `QA Errors`. Every sheet has a wrapped explanation banner in
**row 1**, the header in **row 2**, data from row 3.

A fire row's columns:

```
Indicator | Law | Section | Source URL | Enacted | Last amended | Crawled |
Score hint | Coverage | Confidence | Quote grounded | Verification | Final applies |
Verbatim quote | English (machine) |
Provision text | Provision text (English, machine) | Full section text |
Rationale | Verifier reason | Provision ID
```

**`Provision text` and `Provision text (English, machine)` are the same span in two languages.
`Full section text` is a wider, separate extract from the source document and is NOT what the
English column translates.** This matters: `_full_section()` locates a section with an English
statute regex (`26.—(1)`, `PART IV`, `Division 3`), nothing in it matches `第九条`, so for Chinese
it falls back to a window starting 6,000 characters before the provision — which near the top of a
short instrument is the document's first article. Do not build a side-by-side comparison on that
column.

A gloss prefixed `[not literal — source text is garbled]` is the glosser refusing to smooth over
OCR damage. Flag rates measured today: quotes 0–13%, provision text CN 10%, TL 39–43%, **LA 96%**.
At 96% the Lao flag has stopped discriminating and should be read as a property of that corpus
(99.6% OCR at ~94% character agreement), not as a per-row signal.

### The hard rule about translations

`output/submission.py` **never opens a gloss file**, and `tests/test_gloss_isolation.py` pins that
by checking for the read rather than for the word. A translated string must never become a
`Verbatim Snippet`; the original is the evidence, byte-anchored with a span. **A UI must not
"helpfully" substitute the English into column 9 or into any export.** Show it beside, labelled.

---

## 4. What the UI has to do, and where the current one falls short

Seven checklist items and 15 rubric points rest on the interface: **9** (AI backend swappable from
inside the interface, no code or config change), **11** (audit interface driveable by a
non-technical policy officer), **18** (deploys from the repo at the declared tag — C3a + C3b),
**21** (engine switch made inside the interface, watchable), **24** (run from a button, progress in
plain words, review and export in the interface), **26** (cache and download folders clearable on
screen), **29** (left available for the marking period).

### The gap I would fix first

`stages/p3-map/src/p3map/verify/audit_view.py` is 119 lines and renders exactly five columns:

```
Indicator | Law / section | Score | Verification | Evidence (quote + rationale)
```

**No English.** So a non-technical officer opening `audit/index_CN.html` sees a Chinese quote and
has no way to check it — which is precisely what item 11 asks about, and precisely the gap the
gloss was built to close. `interface/dashboard.py` is the same story: 34 references to `records_*`,
11 to `verdicts_*`, 7 to `economy_scores`, 2 to the workbook, and **zero to `gloss_`**.

Wiring the gloss into the audit view is small and is being done tonight. A new UI should read
`audit/gloss_<E>.jsonl` and `audit/gloss_sections_<E>.jsonl` directly and show original and English
side by side, labelled machine-made, with the `is_literal` flag surfaced.

### The one thing to read in `dashboard.py` before deleting it

433 KB, single file, stdlib only, v3.16. Almost all of it is replaceable. **One pattern is not, and
reinventing it badly is a security hole rather than a missing feature.**

Items 9 and 21 require the model to be switchable from the browser. The obvious implementation —
let the page post a model name that the server puts in the environment — lets anyone who reaches the
page set arbitrary environment variables in the process that spends money and reads the corpus.
`dashboard.py` solves it with a **server-side allowlist**: the browser may only ask for a value from
a fixed set, and only for these names —

```
LLM_PROVIDER  LLM_MODEL  VERIFIER_MODEL  ESCALATION_MODEL  TRIAGE_MODEL
OLLAMA_MODEL  OLLAMA_HOST  OCR_ENGINE
```

— plus an Ollama probe so the open-weights lane can report whether it is actually reachable rather
than failing mid-run. Keep that shape: **the UI names a choice, the server validates it against a
list it owns.** Never let the client supply the variable name, and never let it supply a value the
server has not enumerated.

The engines themselves are already declared in `config/llm/engines.json` — engine A is the Claude
stack with exact checkpoints pinned (not aliases), engine B is `qwen2.5:14b` pinned by digest. A UI
should read that file rather than hardcoding a model list, so the declared engines and the offered
engines cannot drift apart.

Everything else in that file — layout, progress rendering, file browsing — is fair game to discard.

---

## 5. What changes tonight — do not bind to these until they settle

| what | effect on the contract |
| :-- | :-- |
| batch lane retries live on a parse failure | fewer `error` rows in `verdicts_*.jsonl`; `map_report_*.json` may gain a `retry_live_usd` figure |
| the narrative validator stops discarding provisions | a verdict row may gain `narrative_gaps: []` |
| `_np_citation` no longer cites the largest corpus law | ~45 Timorese `Law Name` values change |
| gloss wired into the audit view | `audit/index_<E>.html` gains English columns |
| per-economy section-heading patterns | `Full section text` in the workbook becomes trustworthy for CN/LA/TL |

Column names in the CSV, the JSON and the workbook are **not** changing. Row *contents* for
Timor-Leste will.

---

## 6. What is left that the UI cannot fix

1. **Merge and re-tag.** `finale` needs `p2-extract-contract-0.3.0` (4 commits) and
   `w2-mapping-finale` (44), then a new release tag. This decides what runs on 15 October and is
   the single highest-value action on the whole list.
2. **Promote the run's output into `submission/`.** That folder still ships Round 1: 13 columns,
   `P6-I1` IDs, AU/MY/SG only.
3. **Curate 101 rows from 318**, with the rule written down in the Word document. Suggested
   additions to the rule, from today's findings: exclude Timorese rows from multi-act gazette
   documents unless `act_index == 1` (33 of 65), and prefer exact-citation rows over repaired ones.
4. **The Stage 3 Word document** — `1_Rules/Final_Round/submission_template_stage3_v2_CLEAN.docx`,
   sections 1 (deployment guide), 3 (dependencies and licences), 5 (the two engines). **Section 5
   cannot be corrected after the deadline.**
5. **Notes owed upstream**, findings only, never edits: the duplicate China crawl from two portals,
   `www.gov.cn` barely crawled (11 documents against 924), 29 of 56 China rows on bare-domain URLs,
   Lao's Cyber Crime Law absent, and — new today — **`law_name` not resolved per act in Timorese
   multi-act gazette files, while `citation_confidence` reports `exact`.**

---

## 7. Standing constraints, which do not change

- Do not change anything in the extraction or collection workshops. Findings go back as notes.
- Do not choose a source, a seed or a target by reading the host's 2025 database. No backward
  induction from the gold set — and the gold set is not ground truth: it carries odd sources and
  wrong selections.
- Do not let a translated string become a `Verbatim Snippet`. The original is the evidence.
- Do not report a pooled accuracy figure across scripts.
- Never rewrite the frozen Round 1 arm at `RDTII/pipeline-data/rdtii-p3-map`.
- Do not edit any instrument file, `stages/p0-instrument`, or
  `stages/p3-map/contracts/instrument`. Write a request instead.
