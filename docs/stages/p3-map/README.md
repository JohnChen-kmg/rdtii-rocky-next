# Mapping: provisions to indicators, and the two engines

This workshop holds the thinking for one stage. Mapping takes a grounded provision and decides
which RDTII indicator it evidences, with a rationale and a verbatim citation. It is the highest
leverage stage in the pipeline, and it owns the engine question that C4b and C5 are marked on.

No code lives here. The code lives in the repo. This folder holds the plan, the decisions, the
working notes and the evidence gathered.

**Start here, as of 2026-09-22:** `PRELIMINARY_PLAN_2026-09-22.md`, which re-orders `PLAN.md` for the
eight days to the freeze and adds the decimal-ID migration the instrument hand-off waits on. What the
instrument change breaks in this stage, with file and line, is `notes\INSTRUMENT_IMPACT_2026-09-22.md`.
Frozen Round 1 files the plan leans on are copied into `reference\`; its README lists each file's origin
and hash.

## Where the stage stands, 27 September 2026

Read these four, in this order, to pick the work up cold:

1. `DECISIONS.md` — M11 to M13 at the top: which host economy list governs, the selection function
   adopted with its measured performance, and the pre-freeze list with what measurement rejected.
2. `notes/2026-09-27-overnight-freeze-work.md` — what changed in the repo on the 26th and 27th,
   fifteen commits, with the evidence for each.
3. `notes/2026-09-27-cap-function-and-query-review.md` — the selection function as it now stands and
   every number behind it.
4. The three-day plan, in the session plan file. Blocks B, D and E are done and verified;
   C and F to K remain.

**State of the run.** `rdtii-finale-p3-runs/run_2026-09-27` holds the finished index (767,105
provisions, both legs at depth 150,000), the selection (46,494 candidate pairs, gold 61 of 63),
baseline rows for all ten host economies, and a run manifest. It is ready for S3.

**Mapping has run.** S4-S10 completed for China, Lao PDR and Timor-Leste against the shipping
codebook (via `INSTRUMENT_DIR`, so the copy is still owed). 108 rows filed: CN 56, LA 25, TL 27, plus
142 reused from Round 1. Spend to date **$93.6**. Read, in this order:

1. `notes/2026-09-28-gold-set-comparison-and-filter-audit.md` — the full comparison against the 2025
   baseline: score agreement per country per indicator, loss attribution (53% of misses are a crawl
   gap, 47% ours), where the seven missing laws live, and a line-by-line audit of the five rows our
   filters rejected. Three filters were right, one is a real defect, one goes against us. It also
   records two things I got wrong and corrected.
2. `notes/2026-09-27-overnight-s4-state.md` — the S4 batch run, the 32.8% validation failure and its
   $0 recovery, the cost-report double-count, and the seven open problems.
3. `notes/2026-09-27-triage-keep-rate-measured.md` — triage keep rates measured per economy, and why a
   `--limit` pre-flight reads high.
4. `notes/2026-09-28-plan-full-timor-leste-run.md` — the plan for running TL against all 61 indicators.

**The next two steps, in order.** Block C, the instrument hand-off — the repo still vendors the
legacy nine-block codebook, and S4's cached prefix should come from the codebook that ships. Then
S3 triage on China, Lao PDR and Timor-Leste: $33, about an hour. Nothing has been spent yet.


## What this task owns

| Owns | Implemented in |
| :---- | :---- |
| Seam re-verification of every quote | `stages/p3-map/src/p3map/ingest.py` |
| Retrieval and candidate selection | `prefilter/bm25.py`, `prefilter/dense.py`, `select.py` |
| Triage, local and paid | `triage/local.py`, `triage/haiku.py` |
| The schema-forced verdict | `mapping/prompt.py`, `mapping/schema.py`, `mapping/runner.py` |
| The batch lane | `mapping/batch_runner.py` |
| Blind verification and tiebreak | `verify/blind.py` |
| Economy rollup | `rollup.py` |
| NEW versus KNOWN against the baseline | `discovery/baseline.py`, `discovery/newknown.py` |
| The 14-column CSV and JSON | `output/submission.py` |
| Scoring against the gold set | `eval/evaluator.py` |
| The two declared engines | `config/llm/engines.json` declares them, `engines.py` resolves `RDTII_ENGINE`, and `config/manifest.py` records which one produced a run |
| The cost ledger | no writer exists, PLAN.md step 2C. The Round 1 file was assembled by hand |
| The two-engine comparison | does not exist yet, PLAN.md step 2E |

## What this task does NOT own

Crawling and polite fetching belong to p1-scrape. OCR, segmentation and grounding belong to
p2-extract. The user-facing interface belongs to the interface workstream and lives in
`interface/dashboard.py`. This task supplies the engine names and the ledger that the interface
displays. It does not build the control that displays them.

One boundary matters more than the rest. The live test's second pass must fetch nothing and must
read a document count of zero. That guarantee is p1-scrape's. This task's job is to re-map the
documents already on disk under a second engine, and to prove it did so.

## Where the code lives

All paths sit inside `C:\Users\woshi\Desktop\rdtii-rocky-finale`.

| Path | What it is |
| :---- | :---- |
| `stages\p3-map\src\p3map\` | the stage, S0 through S10 |
| `stages\p3-map\config\llm\base.py` | the one-method interface, the `Usage` record, the `PRICES` dict |
| `stages\p3-map\config\llm\factory.py` | the provider switch, 30 lines, two providers |
| `stages\p3-map\config\llm\anthropic_client.py` | forced tool use for schema, 1h prompt caching |
| `stages\p3-map\config\llm\ollama_client.py` | schema-constrained decoding through `format=schema` |
| `stages\p3-map\src\p3map\ab\ab_deepseek.py` | the worked OpenAI-compatible provider, priced and budgeted |
| `stages\p3-map\config\settings.py` | every knob, read from `.env`, one frozen dataclass |
| `stages\p3-map\src\p3map\cli.py` | the stage CLI, where new verbs go |
| `stages\p3-map\contracts\instrument\gold\gold_set.jsonl` | the gold set, 51 rows, verified by line count. 1,054 rows after the instrument hand-off |
| `docs\CODE_MAP.md` | repo-level code map, items 5 to 8 cover this stage |
| `docs\CHANGELOG_FINALE.md` | every code change, three lines each |

The finale repo has no `out/` and no `data/index/`. Every large artifact from Round 1 sits in the
reference arm at `C:\Users\woshi\Desktop\RDTII\pipeline-data\rdtii-p3-map`. Point `OUT_DIR` and
`INDEX_DIR` at it to run an experiment against real verdicts. Both are environment variables that
`config/settings.py` already reads.

Paths in the next table are relative to that reference arm, not to the repo.

| Reference artifact | Size on disk |
| :---- | ----: |
| `out\map\verdicts_{SG,AU,MY}.jsonl` | about 20 MB |
| `out\verify\verified_{SG,AU,MY}.jsonl` | about 7 MB |
| `out\triage\{triage,haiku}_results.jsonl` | about 11 MB |
| `data\index\prefilter_corpus.jsonl` | about 502 MB |
| `out\ab\ab_deepseek_report.json` | the rejected-provider report, keep it |

## Rubric criteria this task carries

| ID | Points | What it asks | Where this task answers it |
| :---- | ----: | :---- | :---- |
| C2a | 10 | Framework alignment stays consistent across every economy | one cached instrument prefix and one schema for every economy |
| C2b | 10 | Article-level verbatim citation, no hallucinations | byte-exact grounding re-checked at the seam and again at emit |
| C4b | 7 | One config change swaps in an open-weight model | steps 2A and 2D |
| C5 | 10 | Live stress test, 6 for discovery and 4 for the engine swap | steps 2D and 2E, then the rehearsal |
| | 37 | of 100 marks in total | |

C3b belongs to the interface, but the RDTII-schema export it is marked on is written by
`output/submission.py`, which belongs here. Treat export-schema breakage as this task's fault.

## Current state, 2026-09-12

Verified by reading the code, not quoted from memory.

**Works today.** Nine indicators across three economies, SG, AU and MY. Every "applies" verdict is
re-judged blind by a second model that never sees the first model's reasoning, with a third model
as a 2-of-3 tiebreak. Roughly a third of all fires were overturned and excluded, and the excluded
rows are listed rather than hidden. An open-weight lane exists and has actually run. An empty
`ANTHROPIC_API_KEY` falls back to Ollama with a loud banner printed from `factory.py`. DeepSeek was
tested against pre-registered gates, failed them, and the report is kept.

**Missing, ordered by how much it hurts.**

| Gap | Evidence in the code | Criterion at risk |
| :---- | :---- | :---- |
| Two providers only. A third needs a factory branch, a price entry, and two modules that bypass the factory | `config/llm/factory.py`, plus `mapping/batch_runner.py` calling `anthropic.Anthropic()` directly and `triage/local.py` posting to Ollama with raw `httpx` | C4b 7 |
| No named engine concept. A reviewer cannot choose Engine A or Engine B, only individual model variables | `MODEL_ENV_ALLOWLIST` in `interface/dashboard.py` exposes eight separate variables | C5b 4 |
| No unified cost ledger. Each stage writes its own report and no code writes the aggregate | `submission/reports/cost_ledger.json` is read at `interface/dashboard.py:2070` and `:2148`, and written by nothing | C5, submission Section 2 |
| Unpriced models cost zero. `usd()` returns `0.0` for any model absent from `PRICES`, so an unpriced provider reads as free and the budget guard never fires | `config/llm/base.py`, the `if p is None: return 0.0` branch | C5, and the secretariat's cost check |
| No two-engine comparison export. Section 5 of the submission template asks whether the tool produces it natively | nothing in `src/p3map/output/` | C5 10 |

A quieter version of the pricing bug lives in `ab_deepseek.py`. Its `_price()` falls back to the
`deepseek-v4-flash` row for any unknown model. An unpriced DeepSeek model would be costed at the
cheapest rate in the table rather than refused.

**Round 1 cost, stated correctly.** Mapping and verification evidenced US$281.59, recorded in
`submission/reports/cost_ledger.json`. Three components are disclosed as unevidenced and are
excluded from that figure. Quote it only from
`C:\Users\woshi\Desktop\RDTII Finale Plan\3_Final_Stage\AUTHORITATIVE_NUMBERS.md`.

**Not decided yet.** Neither engine's provider is chosen. The developer picks when the experiments
run. Question 5 in `C:\Users\woshi\Desktop\RDTII Finale Plan\3_Final_Stage\OPEN_QUESTIONS_FOR_HOST.md`
asks the secretariat whether a hosted endpoint serving an open-weights checkpoint satisfies the
Engine B requirement. The plan is written so their answer changes an environment variable and
nothing else.

## New from the host templates, read line by line on 2026-09-12

Full detail is in `C:\Users\woshi\Desktop\RDTII Finale Plan\3_Final_Stage\REQUIREMENTS.md`.

### The Engine B question has a new constraint

The Word template contradicts itself, and the contradiction bears directly on the Engine B
disagreement between this folder and the dashboard folder.

| Word template | What it says |
| :---- | :---- |
| Section 5 | "A hosted open-weights API is acceptable" |
| Section 3 checkbox | "The core pipeline can be run end to end with no proprietary API **or hosted service**, that is, on the open-weights engine declared in Section 5" |

Checklist item 20 also expects Engine A to be "commercial hosted" and Engine B "open weights". The
defensible reading is: **declare an open-weights checkpoint that demonstrably runs locally**, so the
Section 3 box can be ticked honestly, and use a hosted endpoint serving the same checkpoint on the day
if venue hardware requires it. Question 5 now asks this explicitly. Record the outcome in
`DECISIONS.md` so the dashboard folder stops holding a competing proposal.

### Section 5 needs numbers only experiments produce

| Field, per engine | Where the number comes from |
| :---- | :---- |
| Exact version or checkpoint identifier | The engines file, step 2D. A floating alias is not an answer |
| **Approximate cost of one run of two indicators, in US dollars** | The experiment harness, step 2B, run at the live-test scale of one economy, one pillar, two indicators. Not a per-provision average |
| **Known weaknesses of this engine on legal text** | The harness report. Trap accuracy and grounding rate are the evidence |
| Screen and control name of the switch | The dashboard folder. Names must be final by 30 September |

"An incomplete Section 5 cannot be corrected after the deadline."

### The comparison file has a fixed shape

| Requirement | Source |
| :---- | :---- |
| Found-by values are exactly **`Engine A only`**, **`Engine B only`**, **`Both`**. The sheet's formulas count those strings and nothing else | Workbook, Engine Comparison sheet |
| Columns: law name, article or section, indicator ID, found by, indicator differs, citation differs, quoted words differ, one line on how | same |
| Per-engine summary: provider and model, start and end hh:mm, elapsed minutes, **documents fetched**, cost | same |
| **A paragraph on which engine's output you would submit**, with the reason | Live test short note says it belongs in the comparison file |
| The short note also asks per engine for provisions exported and how many you believe are absent from the 2025 baseline | Live test short note, section 2 |

Step 2E must emit these exact strings and columns, not a similar table.

### Everything else that binds this task

| Requirement | Source | Consequence |
| :---- | :---- | :---- |
| **A real act cited to the wrong section scores zero.** The host's example praises `s. 26(1)` over `s. 26` as "the more precise citation" | Workbook Instructions and Engine Comparison example | Citation precision is scored, not cosmetic |
| **Per-provision 7.1 or 7.2 rows score zero.** Drafts, repealed provisions, and amending acts cited in place of the principal act score zero | Indicator Reference sheet, rows 80 and 85 | Filter these before emit. The instrument folder encodes the rules |
| **NEW means not in the 2025 baseline you hold** | Workbook Instructions | Baseline diffing must read the seven Round 2 country sheets. Viet Nam and Kazakhstan have none, so every find there is NEW, and the Notes column should say why |
| **Flagging low confidence is treated as a strength** | Workbook Instructions | Emit confidence on every row, and state a calibration threshold in the README |
| **Measured cost per document per engine**, split into OCR, embedding, mapping A, mapping B, crawling, with a benchmark document | README template | The ledger in step 2C must break cost out in those five lines |
| **Reproducing your submitted evidence**, one command | README template | A reviewer regenerates the workbook rows and compares. Plan it as a CLI verb |
| **The workbook holds 101 provisions**, rows 9 to 109 | Workbook Output Data sheet | Round 1 alone filed 142. Question 7 asks what to do. The writer must not silently truncate |

## Borrow from Round 1

Most of this task has been done once already. Point at that work, never copy it here. One source of
truth, and it is wherever the file already lives. One exception, made at the developer's request on
2026-09-22: frozen Round 1 files, which can no longer change, are copied into `reference\round1\` with
their origin and hash. Living documents are still only pointed at. Repo paths below are relative to
`C:\Users\woshi\Desktop\rdtii-rocky-finale`. Planning-folder paths are absolute. Every path in this
section was checked on 2026-09-12.

### Reusable templates, worth more than the reference material

These three are a working format, not background. Step 2B should adopt it rather than invent one.
The first two rows are the pre-registration and report pair. Between them they write the gates
down before any money is spent, record the price table with its source and retrieval date, and
report a binary pass or fail. DeepSeek failed four gates out of four, and the report was kept
rather than buried. That is the behaviour the host marks up.

| Path | What to reuse it for |
| :---- | :---- |
| `stages\p3-map\docs\ab\ab_deepseek_preregistration.md` | The pre-registration template for step 2B. Copy its order: provider, models, hard budget cap, price table with source URL and retrieval date, fixed sample, fixed reference arm, then the binary gate. All of it written before the first API call |
| `stages\p3-map\docs\ab\ab_deepseek_report.md` | The score card template that pairs with it. One row per arm, metric against threshold, PASS or FAIL, measured cost. Stale in one place: its headline total of about $0.48 does not reconcile with its own itemized $0.38, so state the total the entries actually sum to |
| `C:\Users\woshi\Desktop\RDTII Finale Plan\2_What_We_Built\Self_Assessment\01_Findings\AB_DEEPSEEK_VERIFICATION_2026-07-18.md` | The six checks a reviewer ran over that pair. Use it as the checklist your own experiment must survive, including the flag that both pre-registrations carry a placeholder timestamp instead of a real write time. Fix that in the new harness |

### Reference, beside the code

| Path | Why open it |
| :---- | :---- |
| `stages\p3-map\workflow\MAPPING_MECHANISM.md` | How a verdict is actually produced, traced on real output through SG PDPA 2012 s.26(1). Read it before touching `mapping/prompt.py`, so an engine swap does not quietly change the mechanism as well as the model |
| `stages\p3-map\workflow\WORKFLOW_MAP.md` | The S0 to S10 map with the per-stage cost table, which is the shape step 2C's roll-up has to reproduce. Stale for AU: its S4, S5 and S9 rows predate the 2026-07-18 segmentation-fix re-map, so AU cost and row counts there disagree with the filed ledger |
| `stages\p3-map\workflow\WORKFLOW_LOG.md` | The dated run log and the narrative ledger that step 2C replaces with machine-written lines. Its $44.54 Haiku triage figure is the one the filed ledger discloses as unevidenced, so read it for method and never quote it as cost |
| `stages\p3-map\workflow\REVIEW_ITEMS.md` | Every judgment call and its disposition. The two-engine comparison in 2E will refill this queue, so match the shape rather than designing a new one |
| `stages\p3-map\workflow\REVIEW_PACKET_2026-07-16.md` | A generated packet a human actually worked through, row by row with the evidence attached. The closest existing model for the 2E comparison export a judge has to read |
| `stages\p3-map\workflow\SUBMISSION_NOTES.md` | The measured Round 1 unit economics, per provision and per row. These are the claims step 2C must now produce by logging instead of by hand |
| `stages\p3-map\workflow\steps\` | Thirteen files: `README.md`, `DATA_DICTIONARY.md`, and `S0_ingest.md`, `S1_prefilter.md`, `S2_select.md`, `S3_triage.md`, `S4_mapping.md`, `S5_verify.md`, `S6_rollup.md`, `S7_newknown.md`, `S8_malaysia.md`, `S9_emit.md`, `S10_eval.md`. Each carries the real prompt and the real response for its stage, which is what a new engine has to be judged against |
| `stages\p3-map\PLAN.md` | The Round 1 stage plan as it shipped, decision-forcing and naming the rejected design each time. Read it for rationale, not for stage names: it still uses the old P3/P4/P5/P9/P6 labels rather than S0 to S10, and it is marked provisional at 2026-07-09 |
| `stages\p3-map\STAGE_GUIDE.md` | The shortest accurate description of what this stage does. Reusable wording for the 30 September Word document |
| `stages\p3-map\INTERFACE_CONTRACT.md` | The frozen seam as vendored beside this stage, synced to `CONTRACT_VERSION` 0.2.0. Check any new output file shape against it before adding one. This is the current copy, newer than the planning-folder copy below |

### Reference, in the planning folder

| Path | Why open it |
| :---- | :---- |
| `C:\Users\woshi\Desktop\RDTII Finale Plan\2_What_We_Built\Reference\Stage_Plans\3_Mapping_to_RDTII.md` | The original stage plan, about 42 KB. Superseded: this is an earlier cut of `stages\p3-map\PLAN.md`, pinned at contract 0.1.0 and still naming `rank_bm25` where the repo shipped `bm25s`. Prefer the repo copy, and open this one only to see what changed |
| `C:\Users\woshi\Desktop\RDTII Finale Plan\2_What_We_Built\Filed_FROZEN\reports\cost_ledger.json` | The filed ledger and the exact artifact step 2C has to beat. Read `unevidenced_components` and `evidence_files_read` first: three components are null and disclosed, and the evidence paths are absolute Desktop paths a reviewer cannot follow. Both are the failures 2C fixes |
| `C:\Users\woshi\Desktop\RDTII Finale Plan\2_What_We_Built\Self_Assessment\03_Submission\briefs\STATION_3_P3_MAP.md` | The stage brief, every number paired with the artifact that evidences it. The fastest way back into the stage, and a working model for how to present the finale's numbers |

### Cross-cutting, relevant to every task

| Path | Why open it |
| :---- | :---- |
| `C:\Users\woshi\Desktop\RDTII Finale Plan\2_What_We_Built\Reference\Stage_Plans\0_Interfaces_and_Contracts.md` | The frozen spine all stages key off, and the reason no stage imports another's Python. Stale: this copy is pinned at `CONTRACT_VERSION` 0.1.0 and names PyMuPDF where the shipped seam uses pypdfium2. The current text is `stages\p3-map\INTERFACE_CONTRACT.md` |
| `C:\Users\woshi\Desktop\RDTII Finale Plan\2_What_We_Built\Reference\Stage_Plans\round1_plan\DISCLOSURES.md` | The honesty habit this task inherits: never present an estimate as a measurement, and a disclosed gap beats an undisclosed one. Item (c) is this stage's three disclosed baseline soft channels, which the sealed live test will test again |
| `C:\Users\woshi\Desktop\RDTII Finale Plan\2_What_We_Built\Self_Assessment\01_Findings\LEAKAGE_AUDIT_2026-07-16.md` | The leakage audit, found by listing `01_Findings`. It traces every path by which a baseline answer could reach the model and rules S3, S4, S5 and S6 blind. The live test is sealed, so re-run its argument over any new engine, prompt or retrieval change |
| `C:\Users\woshi\Desktop\RDTII Finale Plan\2_What_We_Built\Self_Assessment\01_Findings\` | The rest of the audits, eighteen Markdown findings plus `corpus_sweep_report_2026-07-17.json`. `MAPPING_AUDIT_ALL_ECONOMIES_2026-07-16.md`, `SEGFIX_VERIFICATION_2026-07-18.md` and `V24_VERIFICATION_2026-07-18.md` are the ones that re-derived this stage's counts from artifacts rather than from reports |

## The first thing to do

Fix the price table before anything else. It takes about 45 minutes and it unblocks the rest.

1. **Move the price table.** Lift the three-model `PRICES` dict out of `config/llm/base.py` into
   `config/llm/prices.json`, one object per model carrying rates, currency, source URL and
   retrieval date.
2. **Make an unknown model raise.** Add `config/llm/pricing.py` with `price_for(model)` that
   raises `UnpricedModel` instead of returning zero. Keep `usd()` as its only caller.
3. **Refuse to build an unpriced paid client.** A wrong model name then fails before it spends.
   That is decision 5 in DECISIONS.md.

Then start step 2A in PLAN.md. Log each code change in
`C:\Users\woshi\Desktop\rdtii-rocky-finale\docs\CHANGELOG_FINALE.md`, never here.
