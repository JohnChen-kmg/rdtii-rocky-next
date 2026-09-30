# Plan: mapping and the two engines

Five steps, about 17 hours of work, all of it inside
`C:\Users\woshi\Desktop\rdtii-rocky-finale\stages\p3-map`. Step 2A is the gate. Nothing else can
start until a third provider can be constructed and priced.

Eighteen days remain to the 30 September freeze. This workstream is not the biggest one. Economy
coverage is. So finish 2A to 2E early and leave the calendar clear.

## The steps at a glance

| Step | Hours | What lands | Criterion |
| :---- | ----: | :---- | :---- |
| 2A | 4 | OpenAI-compatible client, JSON price table, factory branch | C4b 7 |
| 2B | 4 | Provider-agnostic experiment command with pre-registration and gates | C4b, evidence for Section 5 |
| 2C | 3 | One JSON line per model call, plus a roll-up command | C5, submission Section 2 |
| 2D | 3 | Engine A and Engine B as named bundles behind one variable | C5b 4 |
| 2E | 3 | The host's two-engine comparison table, produced natively | C5 10 |
| | **17** | | |

Log every code change in `C:\Users\woshi\Desktop\rdtii-rocky-finale\docs\CHANGELOG_FINALE.md`.
Log task-level choices in DECISIONS.md in this folder.

### Changed by the host templates, read 2026-09-12

- **2B must measure at live-test scale.** Section 5 asks for the cost of one run of two indicators
  per engine, and the known weaknesses of each engine on legal text. Add a run profile of one
  economy, one pillar, two indicators, and have the report state cost and weaknesses in words a
  Section 5 cell can take. About 1 extra hour.
- **2C must split cost into the README template's five lines:** OCR, embedding, mapping A,
  mapping B, crawling. Plus a benchmark document and wall-clock seconds per document. The OCR and
  crawling lines are $0 today, and a logged $0 is still a line.
- **2D must pin an exact checkpoint** per engine, not a floating alias, and Engine B's checkpoint
  must be one that runs locally. See the Word template Section 3 checkbox in `README.md`.
- **2E must emit the exact strings `Engine A only`, `Engine B only` and `Both`**, the host's column
  set, a per-engine summary including documents fetched, and a slot for a paragraph on which
  engine's output you would submit. About 1 extra hour for the paragraph and summary.
- **New step 2F, emit-time zero-score filters, 2 hours, freeze minimum yes.** Drop or flag rows the
  host says score zero: per-provision 7.1 and 7.2, drafts, repealed provisions, and amending acts
  cited in place of the principal act. The rules come from the instrument folder.
- **New step 2G, reproduce-evidence verb, 2 hours, freeze minimum yes.** One command that regenerates
  the submitted workbook rows from stored verdicts, so the README section "Reproducing Your
  Submitted Evidence" has something real to name.

Revised total: 23 hours. The "leave the calendar clear" sentence above no longer holds.

### Scope decision, 2026-09-12

**Required: six economies and pillars 6 and 7. Further is optional.** See `DECISIONS.md` M7. Steps
2A to 2G are unchanged, because the engines, the ledger and the comparison do not depend on how many
indicators exist. The per-pillar prompt from the instrument folder is no longer a dependency.

---

## 2A OpenAI-compatible client, about 4 hours

This is the minimum that lets experiments start. Do it in this order.

**2A.1 Price table as data, 45 min.** Create `config/llm/prices.json`. One object per model with
`input`, `output`, `cache_read`, `cache_write` in US dollars per million tokens, plus `currency`,
`source` as a URL and `retrieved` as a date. Seed it with the three models currently hard-coded in
the `PRICES` dict in `config/llm/base.py` and the four DeepSeek rows in `PRICE_TABLE` in
`src/p3map/ab/ab_deepseek.py`. The DeepSeek rows already carry provenance in `PRICE_META`, so copy
that source URL and its 2026-07-18 retrieval date rather than inventing one.

**2A.2 Pricing module that refuses, 30 min.** Add `config/llm/pricing.py` exporting
`price_for(model)` and `UnpricedModel`. `price_for` raises rather than returning a default. Rewrite
`usd()` in `config/llm/base.py` to call it, and keep a `PRICES`-shaped mapping exported from the
same module because `mapping/batch_runner.py:30` imports `PRICES` by name and asserts membership at
`batch_runner.py:341`. That assert is the behaviour to generalise, not to delete.

**2A.3 The general client, 1.5 h.** Create `config/llm/openai_compatible.py` by lifting
`DeepSeekClient` from `src/p3map/ab/ab_deepseek.py:103`. Keep its thread-safe budget guard and its
per-call cost meter. Change three things. Make it subclass `LLMClient` from `config/llm/base.py` so
its signature is `complete(prompt, schema, *, system, max_tokens, cache_system)`. Populate
`self.usage` as a `Usage` record so `usd()` works on it unchanged. Add a `schema_strategy` field
taking one of three values.

| Value | How it forces the schema | Status |
| :---- | :---- | :---- |
| `json_object` | appends the schema to the user turn, as DeepSeek needed | the default, proven here |
| `json_schema` | uses `response_format` with a strict schema | untested |
| `tool_call` | forces a named function | untested |

Default to `json_object`. It is the only one proven to work here.

**2A.4 Factory branch, 30 min.** Add a third branch to `get_llm()` in `config/llm/factory.py` for
`provider == "openai_compatible"`. Read base URL and API key from environment variables whose names
come from the engine record, never from the file. Preserve the existing empty-key fallback to
Ollama and its loud banner. The whole file is 30 lines today. Keep it under 60.

**2A.5 The two bypass sites, 30 min.** `mapping/batch_runner.py` builds `anthropic.Anthropic()`
directly at three call sites, `:174`, `:199` and `:220`. Per decision 3 it stays Anthropic-only.
Add an explicit guard that refuses to run when the resolved engine is not Anthropic. Have the
message name the live path as the alternative. `triage/local.py:84` posts to Ollama with a raw
`httpx.Client`. Route it through the factory, or leave it and document it as a fixed local lane.
Recommendation: leave it and document it. It is `$0`, it is recall-biased, and rewiring it buys
nothing on 15 October.

**2A.6 Settings and smoke test, 15 min.** Add the new variables to `config/settings.py` and to
`.env.example`. Write one test that constructs each provider against a fake endpoint and asserts
that an unpriced model raises.

**Done when** a third provider can be constructed from environment variables alone, an unpriced
model raises before any HTTP call, and `python -m pytest tests -q` still passes.

---

## 2B Experiment harness, about 4 hours

Today the only working experiment is welded to one vendor. `src/p3map/ab/ab_deepseek.py` is 778
lines, and roughly half of it is reusable.

**2B.1 Lift the reusable half, 1.5 h.** Create `src/p3map/experiments/` with five modules. Move the
functions listed below out of `ab_deepseek.py` and leave DeepSeek-specific glue behind.

| New module | Lift from `ab_deepseek.py` | What it does |
| :---- | :---- | :---- |
| `inputs.py` | `_required_inputs` `:210`, `validate` `:229`, `_corpus_index` `:242`, `_signatures` `:251` | checks every input file resolves, costs nothing |
| `sample.py` | `sample_ab4` `:429`, `reconstruct_ab3_sample` `:271` | seeded sampling over provisions and triage pairs |
| `reference.py` | `_load_sonnet_verdicts` `:409`, `_verified_fires` `:419`, `_econ_of` `:561` | loads the reference arm's verdicts to compare against |
| `score.py` | `_score_arm` `:565` | every gate metric, unchanged |
| `prereg.py` | `write_preregistration` `:685`, `_write_report` `:662` | writes the pre-registration before spending |

Keep `ab_deepseek.py` working after the lift. It is filed evidence of a rejected provider, so it
must still run and still produce the same report.

**2B.2 One provider-agnostic command, 2 h.** Add `experiment` to `src/p3map/cli.py`, which today
carries `version`, `ingest`, `prefilter`, `select`, `triage`, `ab-triage` and `ab-mapper`. Flags:
`--engine`, `--role` from mapper, verifier and triage, `--n`, `--seed`, `--budget-usd` and
`--dry-run`. Order of operations is fixed and is the point of the step. Validate inputs, draw the
sample, write the pre-registration to disk, print the priced estimate, then and only then spend.

**2B.3 Dry run that prices the experiment, 30 min.** With `--dry-run` the command builds every
prompt, counts tokens, multiplies by `price_for(model)` and prints the projected spend without an
HTTP call. It must refuse to proceed when the projection exceeds `--budget-usd`.

**Gates, taken unchanged from `_score_arm`.** Do not soften them for a new provider.

| Gate | Threshold |
| :---- | :---- |
| Quote grounding rate | at or above 0.98 |
| Applies-agreement with the reference arm | at or above 0.90 |
| Trap accuracy over trap provisions | at or above 0.90 |
| Canonical trap case | must pass |
| Schema validity rate | reported, and a fall in it is a fail |
| Cost per provision | reported, never a gate on its own |

**Done when** one command takes three environment variables and an engine name, and produces a
pre-registration, a spend, a score card and a PASS or FAIL. It must do that for a provider the
code has never seen.

---

## 2C Unified cost ledger, about 3 hours

The rubric asks for cost per run and per engine, produced by logging without manual arithmetic. The
secretariat verifies cost claims against the code. Today `submission/reports/cost_ledger.json` is
read at `interface/dashboard.py:2070` and `:2148`, and written by nothing.

**2C.1 The writer, 1 h.** Create `config/llm/ledger.py` with `record_call(...)` appending one JSON
line to `OUT_DIR/ledger/calls.jsonl`. One line per model call, with these fields.

| Field | Note |
| :---- | :---- |
| `ts`, `run_id`, `engine`, `stage`, `role` | run identity |
| `provider`, `model` | what actually answered, not what was requested |
| `tokens_in`, `tokens_out`, `cache_read`, `cache_write` | straight from the provider's usage object |
| `usd` | null when unpriced, never zero |
| `priced` | false marks the call for the roll-up to count separately |
| `elapsed_s`, `ok`, `error` | a failed call still costs input tokens |

**2C.2 Hook the three clients, 45 min.** Call `record_call` from `AnthropicClient.complete`,
`OllamaClient.complete` and the new `openai_compatible` client. The batch lane calls it from the
fetch path in `mapping/batch_runner.py` after applying `BATCH_DISCOUNT`, which is already a named
constant at `batch_runner.py:36`.

**2C.3 The roll-up, 1 h.** Add `ledger` to `src/p3map/cli.py`. It groups by run, engine, stage and
role and writes `OUT_DIR/ledger/cost_report.json`. It then cross-checks itself against the existing
per-stage reports, `out/map/map_report_*.json` and `out/verify/verify_report_*.json`, and prints
any line that disagrees by more than one cent. Unpriced calls appear as their own row with a count
and a reason, never folded into the total as zero.

**2C.4 Evidence paths, 15 min.** Record evidence paths repo-relative. The Round 1 ledger records
absolute Desktop paths, which a reviewer cloning the public repo cannot follow.

**Done when** a run writes its own ledger, the roll-up reproduces the per-stage figures without a
calculator, and an unpriced model shows as unpriced rather than free.

---

## 2D Engines as named bundles, about 3 hours

**2D.1 The engines file, 1 h.** Create `config/llm/engines.json` declaring exactly two engines.
Each engine names its roles, its worker count, whether its weights are open, and the names of the
environment variables holding key and endpoint. Never the key itself. Proposed shape, one record
per engine:

| Key | Example value | Why |
| :---- | :---- | :---- |
| `id` | `A` | what the reviewer clicks |
| `label` | a human name including the model | the judge reads this, not the id |
| `open_weights` | true or false | Section 5 asks directly |
| `roles.mapper`, `roles.verifier`, `roles.escalation`, `roles.triage` | provider plus model | one bundle, four roles |
| `workers` | integer | Engine B may need fewer than the mapper's 8 |
| `api_key_env`, `base_url_env` | variable names | keeps secrets out of a public repo |
| `notes` | free text | where the weights come from, for the defence |

**2D.2 The resolver, 1 h.** Add `config/llm/engines.py` with `resolve_engine(name)` returning a
frozen record, and read `RDTII_ENGINE` in `config/settings.py`. One variable selects one engine.
`get_llm(settings, role)` then asks the resolved engine for that role instead of reading four
separate model variables. Keep the four variables working as an override so the existing custom
preset in the interface does not break.

**2D.3 The run manifest, 45 min.** Every run writes `OUT_DIR/run_manifest.json`. It records six
fields: run id, engine id, the model resolved for each role, the git commit, the start time and
the input document count. This is decision 2 in DECISIONS.md and it is what makes 2E possible. It
is also the artifact that proves the second live pass fetched nothing, because its document count
reads zero.

**2D.4 Hand the interface a list, 15 min.** Expose the engines file so the interface can render two
choices without knowing any model names. The interface change itself belongs to that workstream.
The contract belongs here.

**Done when** setting one environment variable changes every role at once, and the run manifest
records what actually answered rather than what was asked for.

---

## 2E Native two-engine comparison, about 3 hours

**2E.1 The comparator, 2 h.** Create `src/p3map/output/compare.py` beside `submission.py` and
`excel_export.py`. It takes two run directories, reads both run manifests, and refuses to compare
runs over different document sets. For every provision found by either engine it emits one row.

| Column | Content |
| :---- | :---- |
| `provision_id`, `doc_id`, `article_section` | the provision |
| `found_by` | A only, B only, or both |
| `indicator_a`, `indicator_b` | decimal text such as `6.1`, never a number |
| `indicator_match` | true or false |
| `citation_match` | same article-level citation or not |
| `quote_match` | exact, overlapping or different |
| `difference` | one line of plain English saying how they differ |

**2E.2 The per-engine summary, 45 min.** A second block in the same output giving elapsed time,
total cost, cost per provision, call count and unpriced call count per engine. Read it from the
2C ledger, not by re-counting.

**2E.3 The CLI verb, 15 min.** Add `compare --run-a --run-b --out` to `src/p3map/cli.py`. It writes
CSV and JSON side by side, because the CSV is what a judge opens and the JSON is what the interface
renders.

**Done when** two runs over the same documents produce the host's comparison table from one
command, with no spreadsheet step.

---

## The minimum for the 30 September freeze

All of 2A through 2E, except the extract-stage ledger mirror described in decision 4. Everything on
that list is load-bearing for a criterion. Nothing on it is polish.

| Must be true on 30 September | Why |
| :---- | :---- |
| Two engines are declared in `config/llm/engines.json` and one variable selects one | C5b 4, and the engine swap on the day |
| At least one declared engine has open weights | C4b 7 |
| Every model call writes a ledger line and the roll-up reproduces the totals | C5, submission Section 2 |
| An unpriced model raises rather than costing zero | the secretariat checks cost claims against the code |
| `compare` produces the host's table from two run directories | Section 5 asks whether the tool does this natively |
| The experiment harness is provider-agnostic and pre-registers before spending | this is the evidence that the engine choice was earned |

## What gets cut first, in this order

1. **The extract-stage ledger mirror.** Decision 4 already says the vendored config packages stay
   separate. Cutting the mirror means the ledger covers p3-map only. Say so in the submission
   rather than implying whole-pipeline coverage.
2. **The verifier role in the harness.** Run experiments on the mapper role only. The verifier is
   the cheaper model and a weaker verifier fails loudly through the overturn rate.
3. **The interface key-name change.** Leave `ANTHROPIC_API_KEY` as the variable the interface holds
   even when Engine B is selected. It is ugly and it is not marked.
4. **`schema_strategy` beyond `json_object`.** Ship the one strategy that is proven to work and
   note the other two as untested.

Do not cut the run manifest. Without it the comparison in 2E cannot prove the two runs covered the
same documents, and the 4 marks for the engine swap go with it.

## After the freeze, 1 to 14 October

Code is frozen on 30 September. Settings may still change. Use the fortnight to rehearse.

**Rehearse the live sequence end to end on an economy not yet run.** Run these steps in order.

1. Read the task. Set economy and indicators in the interface.
2. Press start. Engine A finds, downloads, reads, extracts and maps.
3. Review the verdicts in the interface. Export the evidence.
4. Switch to Engine B. Re-run over the documents already downloaded.
5. Export the comparison.

**Check the two numbers that decide 4 marks.** The second pass must fetch nothing, and its document
count must read zero. Confirm both from the run manifest, not from the screen.

**Time it.** Record the wall clock for each phase in `notes/` in this folder, and file the
rehearsal output in `evidence/`.
