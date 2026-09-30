# Code map — where the logic lives

Written 2026-09-12 for the finale build. Every reference is `path:line` as of commit
`f0aef69` on branch `finale`. Line numbers drift as we edit; the function names do not.
When a section says "start here", that file is the one to read first.

## How to read this repo in one sitting

Read in this order. Each step is one file, and each file is small except the last two.

1. `main.py` — the driver. It never imports stage code; it runs each stage as a
   subprocess and collects timings. Read `run_step()` (`main.py:191`) and
   `cmd_pipeline_slice()` (`main.py:391`) to see the whole pipeline in one screen.
2. `stages/p1-scrape/src/p1_scrape/orchestrator.py` — the crawl loop. `run_crawl()`
   (`:149`) sets up, `_crawl_queue()` (`:244`) fetches, `_store_row()` (`:325`) writes.
3. `stages/p1-scrape/src/p1_scrape/adapters/base.py` — the three-method contract every
   portal adapter implements. Then one adapter, `adapters/sg_sso.py`, to see it filled in.
4. `stages/p2-extract/src/rdtii_p2/ground.py` — 60 lines that carry the "no quote = no
   record" rule. Then `segment.py:362 segment()` and `extract_fields.py:365 build_record()`.
5. `stages/p3-map/config/llm/base.py` and `factory.py` — the LLM interface (one method)
   and the provider switch (30 lines).
6. `stages/p3-map/src/p3map/mapping/prompt.py` — what the model is shown. Then
   `mapping/runner.py:49 run_mapping()` — how it is asked, in parallel, with a budget.
7. `stages/p3-map/src/p3map/verify/blind.py:45 run_verify()` — the second model that never
   sees the first model's reasoning.
8. `stages/p3-map/src/p3map/output/submission.py:98 run_submission()` — the 13-column
   writer and every rule about what may appear in a row.
9. `interface/dashboard.py` — 8,673 lines, one file. Read only `Config` (`:574`),
   `build_child_env()` (`:974`), `run_worker_loop()` (`:1053`) and the route table inside
   `Handler` (`:3518`). The HTML template starts at `:3765` and is most of the file.

## Repo layout

```
rdtii-rocky-finale/
├── main.py                  driver: serve | --mini-run | --quick | --demo | --full-pipeline
├── requirements-demo.txt    pinned union of stage deps, CPU-only, torch-free
├── docs/                    DATA.md · DISCLOSURES.md · WORKFLOW.md · CODE_MAP.md (this)
├── demo_data/               the 12 MB scanned MY statute for the OCR demo + mini_raw/ for --offline
├── submission/              Round-1 judged records, workbooks, audit pages, cost ledger  (do not edit)
├── interface/dashboard.py   stdlib-only local web UI that drives main.py as a subprocess
└── stages/
    ├── p0-instrument/       the codebook: indicators.yaml, policies.yaml, signatures/, gold/
    ├── p1-scrape/           crawl official portals -> Hand-off #1 (manifest + raw bytes)
    ├── p2-extract/          OCR / parse / segment / ground -> Hand-off #2 (provisions.jsonl)
    └── p3-map/              prefilter -> triage -> map -> blind verify -> NEW/KNOWN -> CSV
```

The stages share no Python. They are wired only by files on disk (see "Seams" below), and
each stage vendors a pinned copy of the schemas and instrument it consumes.

---

## `main.py` — the driver (1,011 lines)

**Entry**: `main()` at `main.py:954` parses flags and dispatches to one of five commands.

| Command | Function | What it does |
| :--- | :--- | :--- |
| `--economy X --pillar N` | `cmd_serve()` `:220` | Re-emits the judged Round-1 rows from `submission/`. No network, no key. |
| `--mini-run [--offline]` | `cmd_pipeline_slice()` `:391` | Real 5-doc P1→P2→P3 slice. `--offline` swaps the crawl for `demo_data/mini_raw` via `stage_offline_handoff1()` `:278`. |
| `--quick` | same function, variant `quick` | 2-doc live-pitch slice. |
| `--demo` | `cmd_demo()` `:872` | Scanned-PDF walkthrough with a live CER measurement. |
| `--full-pipeline` | `cmd_full_pipeline()` `:904` | Prints the full-corpus commands. Executes nothing. |

**How stages are invoked**: `run_step(label, cmd, cwd, env)` at `:191` is a
`subprocess.run` with the stage directory as `cwd`. It appends wall-clock and return code
to a module-level list that `write_run_summary()` (`:706`) turns into the timings table in
`RUN_SUMMARY.md`. `_base_env()` (`:207`) forces UTF-8 on Windows; P3 additionally receives
`HANDOFF2_DIR`, `MANIFEST_PATH`, `OUT_DIR`, `INDEX_DIR` (`:567-571`).

**Backend selection**: `keyless()` (`:161`) checks `ANTHROPIC_API_KEY`;
`announce_backend()` (`:165`) prints the loud fallback banner the dashboard parses.

**Economy input**: `resolve_economy()` (`:130`) is typo-tolerant and hard-codes SG/MY/AU.
Workstream 1A replaces the list with the P1 YAML glob.

---

## P0 — the instrument (`stages/p0-instrument/`)

**What it is**: the codebook the mapper reads. Not code that runs in the pipeline; scripts
that build and validate YAML, which P3 then vendors byte-for-byte into
`stages/p3-map/contracts/instrument/`.

```
p0-instrument/
├── examples/   Round1_Baseline_Database.xlsx · Round2_Methodology_and_Examples.xlsx  (host files)
├── reference/  legal inventory CSV, output template, scoring criteria
├── output/     indicators.yaml · policies.yaml · signatures/<ID>.yaml · gold/gold_set.jsonl
└── scripts/    rdtii_examples.py · build_signatures.py · build_gold.py · validate_instrument.py
```

| File | Role |
| :--- | :--- |
| `output/indicators.yaml` | 9 indicator blocks (`:80 P6-I1` … `:472 P7-I5`). Each has `question, definition, scoring{values,type}, scoring_features, scoring_tree, coding_rules, exceptions, disambiguation, guide_examples`. Header carries `scope` (`:25`) and `score_polarity` (`:46`). |
| `output/policies.yaml` | Cross-cutting rules: source hierarchy, citation contract, edge cases, measure inclusion, scoring policy. |
| `output/signatures/<ID>.yaml` | Per-indicator retrieval signature: keywords, `definition_text`, negative signals, ≥3 labelled exemplars. Used by the prefilter and triage, not by the mapper. |
| `output/gold/gold_set.jsonl` | 51 Round-1 baseline rows, the eval yardstick and the KNOWN set. |
| `scripts/rdtii_examples.py` | Shared workbook parser. `parse_workbook()` `:85` handles merged cells, float IDs, strikethrough. `indicator_code()` `:67` is the `'6.1' -> 'P6-I1'` converter (to be replaced by `indicator_ids.py`). |
| `scripts/build_signatures.py` | `SPEC` `:30` (hand-authored keywords and definitions) + `CURATED` `:324` (workbook rows with teaching notes) → `signatures/`. |
| `scripts/build_gold.py` | Round-1 country sheets → `gold_set.jsonl`, with `LABEL_FLAGS` `:20` for suspect rows. |
| `scripts/validate_instrument.py` | The definition of done. `EXPECTED` `:32` order and `SCORESETS` `:34`; cross-checks category and score sets against the methodology sheet (`:64-84`); signatures round-trip; gold round-trip. Exit 0 = frozen-ready. |

**Where the 9 is hard-coded**: `validate_instrument.py:32`, `indicators.yaml:27`,
`build_signatures.py:30,324`, `rdtii_examples.py:97` (filters to `6.`/`7.`), and in P3
`config/settings.py:74`.

---

## P1 — the crawler (`stages/p1-scrape/`)

**In**: `instrument/sources_<cc>.yaml` (portals, seed laws, queries).
**Out**: Hand-off #1 = `handoff1/manifest.csv` + `manifest.jsonl` + `raw/**` +
`crawl_log.jsonl`. One manifest row per retrieved document. Nothing is parsed or OCR'd here.

```
p1-scrape/
├── scrape.py                       friendly wrapper -> src/p1_scrape/cli.py
├── config/settings.py              REQUEST_DELAY_MS, MAX_CONCURRENCY_PER_HOST, UA, robots flags
├── contracts/schemas/manifest.schema.json   the Hand-off #1 authority (28 columns)
├── contracts/instrument/sources_{sg,my,au}.yaml   pinned copies; instrument/ has working copies
├── src/p1_scrape/
│   ├── cli.py            build_parser :17 · cmd_crawl :76 · cmd_smoke :69 · cmd_validate :49
│   ├── orchestrator.py   run_crawl :149 · _crawl_queue :244 · _store_row :325 · _build_row :357
│   ├── adapters/         base.py (PortalAdapter :19) · registry.py (get_adapter :11)
│   │                     sg_sso.py :34 · my_gazette.py :42 · au_legislation.py :48
│   ├── fetcher.py        Fetcher :65 — requests → Playwright escalation ladder
│   ├── politeness.py     RateLimiter :17 · RobotsAdvisor :37
│   ├── classifier.py     classify :39 — html / pdf_native / pdf_scanned
│   ├── dedup.py          Dedup :31 — .idmap.json, is_retrieved :75, stable_id :81
│   ├── storage.py        Storage :25 — raw/<cc>/<slug>/<stamp>__<kind>.<ext> + .headers.json
│   ├── manifest.py       write_manifest :32 · validate_manifest :80
│   ├── models.py         MANIFEST_FIELDS :15 · Candidate :77 · FetchPlan :104 · FetchResult :165
│   ├── economies.py      normalize_economy :17 · parse_economies :24  (hard-coded SG/AU/MY)
│   ├── sources.py        load_sources :20
│   └── epub.py · inventory.py · crawl_logger.py · cost.py · smoke.py · utils.py
├── tests/                31 tests
└── tools/                one-off scripts (refetch_au_multivolume.py is the delta precedent)
```

**Control flow of one crawl**: `cmd_crawl` → `run_crawl` (loads sources YAML, builds
adapter via `registry.get_adapter`, reloads prior manifest rows for resume) →
`adapter.discover()` yields `Candidate`s → for each, `adapter.build_plans()` yields
`FetchPlan`s (html and/or pdf) → `_crawl_queue` rate-limits and calls `Fetcher.fetch()` →
`_store_row` classifies, stores bytes + headers sidecar, asks `Dedup.stable_id()` for the
`doc_id`, and `_build_row` fills the 28 manifest columns → `write_manifest`.

**The adapter contract** (`adapters/base.py:19`): `discover(pillars, scope, fetcher)`,
`build_plans(candidate, forms)`, optional `extract_anchor(candidate, plan, content)`.

**Things to know**: the economy list lives in three places (`economies.py:4-10`, the schema
enum, and the `doc_id` regex). `slugify()` (`utils.py:23`) returns `"unknown"` for
non-Latin titles. Resume skips any law already in the idmap; there is no change detection
yet. Both are Workstream 1.

---

## P2 — extraction (`stages/p2-extract/`)

**In**: Hand-off #1 manifest + raw files. **Out**: Hand-off #2 = `handoff2/provisions.jsonl`
+ `laws.jsonl` + `source_text/<doc_id>.txt` + `doc_status.jsonl` + `cost_report.json`.
One record per provision, each with a verbatim snippet that is a character-exact substring
of the frozen source text.

```
p2-extract/
├── config/                 settings.py · llm/ (base, factory, anthropic, ollama) · ocr/ · embed/
├── 00_contracts/schemas/   manifest.schema.json (vendored) · provision.schema.json · laws.schema.json
├── src/rdtii_p2/
│   ├── cli.py              main :810 · cmd_run :234 · cmd_tag_corpus :431 · cmd_validate :508
│   │                       cmd_demo :708 · cmd_pilot :763 · _select_rows :61 · _extract_doc :154
│   ├── ingest.py           load_manifest :101 · check_contract_major :90 · preflight :150
│   ├── router.py           route :33 — picks the parsing lane from source_type + pdf_is_scanned
│   ├── parse_pdf_native.py extract_pages :16
│   ├── parse_html.py       parse :260 · parse_au :49
│   ├── ocr_scanned.py      run_lane_c :13 — Tesseract lane for scanned PDFs
│   ├── normalize.py        normalize_pages :146 · detect_furniture :85 — normalise ONCE, then freeze
│   ├── segment.py          segment :362 — article boundaries, schedules, AU quirks
│   ├── ground.py           copy_grounded :29 · verify :42 · locate_exact :54
│   ├── extract_fields.py   build_record :365 · ground_doc_metadata :134 · llm_tags :235 · llm_tags_batch :312
│   ├── emit.py             write_provisions :113 · write_source_text :54 · write_doc_status :94 · write_cost_report :150
│   ├── cer.py              cer :30 · measure_doc :63 — the <5% claim is scoped to committed gold pages
│   └── tag_batches.py      submit :119 · collect_tags :170 · update_cost_report :243 (Anthropic Batches)
└── tests/                  82 tests
```

**Control flow of one document**: `cmd_run` → `load_manifest` (validates every row against
the vendored schema) → `_select_rows` → per doc `_extract_doc`: `route` → parse lane →
`normalize_pages` → `write_source_text` (frozen) → `segment` → `candidate_spans` →
`build_record` (snippet offsets, `ground.verify` asserts
`source_text[start:end] == snippet`) → optional `llm_tags` (scope / data_type /
obligation_type hints) → `write_provisions`.

**The grounding rule** is `ground.py:42 verify()`. A record that fails it is dropped and
logged, never emitted.

**LLM use here is light**: one role, tagging, defaulting to local `qwen2.5:14b`. The
`config/` package is a sibling of P3's but its `LLMClient.complete(prompt, schema)` has a
narrower signature; do not assume the two are interchangeable.

---

## P3 — mapping (`stages/p3-map/`)

**In**: Hand-off #2 + the vendored instrument + the Round-1 baseline workbook.
**Out**: `out/submission/records_<E>.csv` (13 columns) + `.json`, the reviewer workbook,
the audit HTML, per-stage reports.

```
p3-map/
├── config/
│   ├── settings.py         Settings :24 (every env key) · INDICATORS :74 · ECONOMIES :78
│   └── llm/                base.py (Usage :9, PRICES :25, usd :32, LLMClient :41)
│                           factory.py (get_llm :8) · anthropic_client.py :17 · ollama_client.py :14
├── contracts/instrument/   byte-identical vendored copy of p0-instrument/output
├── 00_contracts/schemas/   vendored Hand-off schemas
├── src/p3map/
│   ├── cli.py              main :17 — ingest | prefilter | select | triage | ab-triage | ab-mapper
│   ├── ingest.py           run_ingest :100          S0  re-verifies every quote at the seam
│   ├── prefilter/          bm25.py run_bm25 :23 · dense.py run_dense :34 · queries.py build_queries :14   S1
│   ├── select.py           run_select :55           S2  candidate (provision, indicator) pairs, caps
│   ├── triage/             local.py run_triage :53 (Ollama) · haiku.py run_haiku_triage :43   S3
│   ├── mapping/
│   │   ├── prompt.py       build_system_prefix :18 (cached instrument prefix) · build_user_turn :47
│   │   ├── schema.py       TrapChecks :15 · IndicatorVerdict :35 · MappingVerdict :51
│   │   ├── runner.py       run_mapping :49 · _load_pairs :33      S4  live, 8 workers, budget guard
│   │   └── batch_runner.py dryrun :150 · submit :158 · poll :192 · fetch :216   S4 via Anthropic Batches
│   ├── verify/blind.py     run_verify :45           S5  second model, 2-of-3 tiebreak
│   ├── rollup.py           run_rollup :44 · _framework_score :125   S6  economy-level P7-I1/I2
│   ├── discovery/          baseline.py load_baseline :36 · newknown.py run_newknown :79   S7
│   │                       malaysia.py run_errorcheck :97   S8
│   ├── output/             submission.py run_submission :98 · excel_export.py export :107
│   │                       urlcheck.py run_urlcheck :42   S9
│   ├── eval/evaluator.py   run_eval :47             S10 vs the 51-row gold set
│   ├── chain.py            run_chain :14 — S5→S7→S6→S9→S10 + workbook + audit for one economy
│   ├── preflight.py        run_preflight :27 — must PASS before a batch submit
│   ├── verify/audit_view.py render :47 — the per-fire audit HTML
│   └── ab/                 ab_triage.py :44 · ab_mapper.py :48 · ab_deepseek.py (DeepSeekClient :103, _score_arm :565)
├── workflow/               WORKFLOW_LOG.md (dated run log + cost ledger) · REVIEW_ITEMS.md · per-step docs
├── docs/ab/                A/B preregistrations and reports
└── tests/                  test_holdout_smoke.py
```

**How stages run**: `cli.py` covers S0–S3 only. S4 onward run as
`python -m src.p3map.<module> <ECON>` through each module's `__main__`; `main.py:615-628`
calls them in order per economy.

**What the model sees** (`mapping/prompt.py`): a byte-stable system prefix built from
`indicators.yaml` + `policies.yaml` in `INDICATORS` order (about 26k chars, cached for
1 hour on Anthropic), then a user turn with the provision text and its candidate
indicators. The verdict is schema-forced (`mapping/schema.py`) and includes explicit trap
booleans (ban-vs-conditional, max-vs-min retention, government data).

**The provider switch** (`config/llm/factory.py:8`): role → model from `Settings`; triage
is always Ollama; an empty Anthropic key falls back to Ollama with a banner; then
`anthropic` or `ollama`. Two call sites bypass it: `batch_runner.py` (Anthropic Batches
only) and `triage/local.py:84` (raw Ollama REST).

**Cost**: prices live once in `config/llm/base.py:25`; `usd()` returns 0 for unknown
models. Each stage writes its own report (`out/map/map_report_<E>.json`,
`out/verify/...`). There is no single ledger yet. Workstream 2C.

**Where the 9 indicators are hard-coded**: `config/settings.py:74` plus literals in
`mapping/schema.py`, `output/submission.py`, `output/excel_export.py`, `rollup.py`,
`select.py`, `discovery/malaysia.py`, `discovery/baseline.py`. Workstream 3C.

---

## Interface — `interface/dashboard.py` (8,673 lines, stdlib only)

**What it is**: a local HTTP server on `127.0.0.1:8765` that reads pipeline outputs, shows
the trace from source to verdict, and launches `main.py` runs as subprocesses. One file so
that a reviewer installs nothing.

| Section | Lines | Key names |
| :--- | :--- | :--- |
| Constants and catalog | `:58-570` | `DEFAULT_REPO :58` (**still the Round-1 path; override with `--repo` or `RDTII_REPO`**), `STAGE_CATALOG :74` |
| Runtime state | `:574-843` | `Config :574` · `ApiKeyHolder :600` (key in memory only) · `EventBus :648` · `Registry :682` · `RunParser :783` |
| Launch | `:883-1100` | `MODEL_ENV_ALLOWLIST :883` · `validate_launch_spec :890` (presets judged / keyless / custom) · `build_cmd :959` · `build_child_env :974` · `enqueue_run :1000` · `run_worker_loop :1053` (serial queue) |
| Read services | `:1151-3480` | `svc_records :1196` · `svc_db_promote :1308` · `svc_trace :1733` · `svc_overview :2086` · `svc_runs_list :2323` · `svc_stage_code :2824` · `probe_ollama :3412` |
| HTTP | `:3518-3760` | `Handler :3518` — GET `/api/*` routes, POST `/api/runs`, `/api/key`, `/api/db/promote`; all POSTs need `X-Dash-Token` |
| Page | `:3765-8480` | `PAGE_TEMPLATE` — the inline HTML/JS single-page app, tabs Workflow · Instrument · Run · Database · History & Cost · Guide |
| Export and main | `:8507-8673` | `build_boot_data :8507` · `do_export :8565` (static HTML) · `main :8613` |

**What the engine switch already has**: `MODEL_ENV_ALLOWLIST` lets the UI set
`LLM_PROVIDER`, `LLM_MODEL`, `VERIFIER_MODEL`, `ESCALATION_MODEL`, `TRIAGE_MODEL`,
`OLLAMA_*`, `OCR_ENGINE` in the child env, validated server-side. What it lacks is a named
two-engine control; Workstream 2D adds `ENGINE`.

**What review already has**: the LLM trail (mapper → blind verifier → tiebreak) read-only
via `svc_trace`, the Excel reviewer workbook from P3, and an append-once promote gate. There
is no accept / reject / correct UI yet; that is the dashboard plan.

---

## Seams — the files that connect stages

| Seam | Producer → consumer | File(s) | Schema authority | Vendored copies |
| :--- | :--- | :--- | :--- | :--- |
| Hand-off #1 | P1 → P2 | `handoff1/manifest.{csv,jsonl}`, `raw/**`, `*.headers.json`, `crawl_log.jsonl` | `stages/p1-scrape/contracts/schemas/manifest.schema.json`, mirrored in `models.py:15 MANIFEST_FIELDS` | `p2-extract/00_contracts/schemas/`, `p3-map/00_contracts/schemas/` |
| Hand-off #2 | P2 → P3 | `handoff2/provisions.jsonl`, `laws.jsonl`, `source_text/<doc_id>.txt`, `doc_status.jsonl` | `p2-extract/00_contracts/schemas/provision.schema.json`, `laws.schema.json` | `p3-map/00_contracts/schemas/` |
| Instrument | P0 → P3 (and P1 seed YAML) | `indicators.yaml`, `policies.yaml`, `signatures/`, `gold/` | `p0-instrument/output/` | `p3-map/contracts/instrument/` (byte-identical) |
| Output | P3 → host | `records_<E>.csv` 13 columns, `.json` with per-law grouping | `output/submission.py:35 COLUMNS` | `submission/` at repo root holds the filed copies |

Contract version is `0.2.0`. Appending optional columns is MINOR; renaming, removing,
retyping or reordering is MAJOR. Every consumer checks the MAJOR on load
(`p2 ingest.py:90 check_contract_major`).

---

## Config surface

| Stage | File | Keys that matter |
| :--- | :--- | :--- |
| P1 | `config/settings.py`, `config/.env.example` | `REQUEST_DELAY_MS` (3000 in code, 2000 in the example), `MAX_CONCURRENCY_PER_HOST=1`, `FETCH_TIMEOUT_MS`, `FETCH_RETRIES`, `RESPECT_ROBOTS_FOR_DISCOVERY`, `MAX_CANDIDATES_PER_ECONOMY`, `CRAWL_DEPTH_MAX`; contact email in the UA string |
| P2 | `config/settings.py`, `.env.example` | `LLM_PROVIDER=ollama`, `LLM_MODEL=qwen2.5:14b`, `TAG_BATCH_SIZE`, `OCR_ENGINE`, `OCR_LANG=eng` (one global value; per-doc language is Workstream 1A) |
| P3 | `config/settings.py:24`, `.env.example` | `ANTHROPIC_API_KEY`, `LLM_PROVIDER`, `LLM_MODEL`, `VERIFIER_MODEL`, `ESCALATION_MODEL`, `OLLAMA_HOST`, `OLLAMA_MODEL`, `TRIAGE_MODEL`, `EMBED_MODEL`, `PREFILTER_*`, `HANDOFF2_DIR`, `MANIFEST_PATH`, `INSTRUMENT_DIR`, `BASELINE_PATH`, `OUT_DIR`, `INDEX_DIR`, `MAX_COST_USD_PER_DOC`, `COST_HARD_STOP`, `NEWKNOWN_SIM` |
| Interface | CLI flags / env | `--repo` / `RDTII_REPO`, `--port`, `RDTII_P3MAP_DOCS`; the API key only via `POST /api/key` |

All three stages load `.env` from their own directory; a real environment variable wins.
`main.py` passes its environment down to every subprocess.

---

## Where to look when…

| Symptom or task | Go to |
| :--- | :--- |
| A quoted snippet does not match the source | `p2 ground.py:42 verify()`; P3 re-checks at `p3 ingest.py:100 run_ingest()` |
| A portal blocks or throttles | `p1 fetcher.py:28 THROTTLE_STATUSES` and the backoff in `Fetcher`; `politeness.py` |
| A crawl re-run fetches everything again | `p1 dedup.py:75 is_retrieved()` (binary seen-before; no change detection yet) |
| A non-English law lands in `raw/<cc>/unknown/` | `p1 utils.py:23 slugify()` and `:44 acronym_slug()`; `Candidate.law_slug` (`models.py:100`) is the fix |
| The wrong indicator fired | First `mapping/prompt.py` (what the model saw), then `mapping/schema.py` trap booleans, then `verify/blind.py` (was it overturned?) |
| A NEW/KNOWN tag looks wrong | `discovery/newknown.py:79`; the baseline loader `discovery/baseline.py:36` |
| A cost figure looks wrong | `p3 config/llm/base.py:25 PRICES` and `:32 usd()` (unknown model = 0); `p2 cli.py:393 _estimated_usd()`; per-stage reports in `out/` |
| The dashboard shows no runs or the wrong repo | `dashboard.py:58 DEFAULT_REPO`, `Config :574`; launch with `--repo` |
| Add an economy (today) | `p1 economies.py`, `adapters/registry.py`, `instrument/sources_<cc>.yaml`, the schema enum and `doc_id` regex; then `p3 settings.py:78`, `main.py:130` |
| Add an indicator (today) | `p0 indicators.yaml` + `signatures/` + `validate_instrument.py:32`; then `p3 settings.py:74` and the literals listed under P3 |
| Swap a model (today) | `.env` in `stages/p3-map/` (`LLM_MODEL`, `VERIFIER_MODEL`, …) or `get_llm(..., model=)`; `factory.py:8` |
| Understand what a run cost and produced | `RUN_SUMMARY.md` in the run directory, written by `main.py:706 write_run_summary()` |
| See a decision's rationale | Module docstrings cite "decision #N"; the numbered list is in `stages/p3-map/docs/KICKOFF_DECISIONS_2026-07-12.md` and `workflow/MAPPING_MECHANISM.md` |
