# Code map — where the logic lives

Rewritten on 5 October 2026 for the tool as it stands on branch `feature/desktop-workspace-triage`. It
replaces the map of 12 September, which described the Round 1 layout and a one-file interface,
`interface/dashboard.py`, that is no longer in the repository.

A reference such as `run_crawl :149` is a name and the line it is defined on. Every such pair in this file
was checked by script against the tree of 5 October. Line numbers drift as the code is edited; the names
do not. When a section says "start here", that file is the one to read first.

## How to read this repository in one sitting

Read in this order. The first three show the whole pipeline as it is really run; the rest are the stages
from the inside.

1. `interface/app.py`: `build_app :29` names every module that adds routes; `run_tab :90` and
   `run_window :122` are the two ways to start.
2. `interface/rdtii_ui/jobs.py`, the run layer: `Step :32`, `Job :44` and `JobManager._run_step :227`.
   One child process at a time, its printed lines turned into sentences, and Stop.
3. The three plans. `interface/rdtii_ui/pages/scrape.py` `plan_scrape :1206`,
   `interface/rdtii_ui/pages/extract.py` `plan_extract :854` and
   `interface/rdtii_ui/pages/mapping.py` `plan_map :1117` each turn one request from the page into the
   stage's own command lines. Nothing else starts a stage.
4. `stages/p1-scrape/src/p1_scrape/orchestrator.py` `run_crawl :149`: the crawl loop.
5. `stages/p1-scrape/src/p1_scrape/adapters/base.py` `PortalAdapter :19`, the three methods every portal
   adapter fills in; then one adapter package, `adapters/sg_sso/`.
6. `stages/p2-extract/src/rdtii_p2/cli.py`: `_parse_doc :141` (the four reading lanes) and
   `_extract_doc :227` (the records and the grounding gate). Then
   `stages/p2-extract/src/rdtii_p2/ground.py`, 73 lines that carry "no quote, no record".
7. `stages/p3-map/config/llm/engines.json`, then `stages/p3-map/config/llm/factory.py` `get_llm :66`:
   which provider and model a step is given.
8. `stages/p3-map/config/selection.py` `params_for :200` and `stages/p3-map/src/p3map/select.py`
   `run_select :143`: where the cost of a run is decided, before any model is called.
9. `stages/p3-map/src/p3map/mapping/prompt.py` `build_system_prefix :43` (what the model is shown),
   `stages/p3-map/src/p3map/mapping/runner.py` `run_mapping :57`, and
   `stages/p3-map/src/p3map/verify/blind.py` `run_verify :48`, the blind re-check.
10. `stages/p3-map/src/p3map/chain.py` `run_chain :38`: the order of everything after the careful reading.
11. `stages/p3-map/src/p3map/output/submission.py` `run_submission :270`: the 14 columns and every rule
    about what may appear in a row.
12. `interface/rdtii_ui/review.py`: decisions and the export, 283 lines.

## Repository layout

```
rdtii-rocky-next/
├── Start-RDTII-Rocky.cmd · Start-RDTII-Rocky.command · start-rdtii-rocky.sh
│                            launchers: the interface in a window of its own
├── interface/               what a person drives
│   ├── app.py               start: a browser tab, or --window
│   ├── rdtii_ui/            the server, the run layer, one module per page
│   ├── static/              the page: index.html, app.js, app.css
│   ├── fixtures/            a slice of the finale run, shown on a clean clone
│   └── tests/               291 tests, standard library only
├── stages/
│   ├── p0-instrument/       the codebook: output/ (61 indicator blocks, signatures, gold set), scripts/
│   ├── p1-scrape/           crawl official portals -> manifest + stored documents
│   ├── p2-extract/          read, OCR, split, ground -> provisions.jsonl
│   └── p3-map/              select -> quick screen -> careful reading -> re-check -> scores -> rows
├── submission/              the filed evidence; read-only
├── demo_data/               five documents for a first run
├── inbox/                   documents collected by hand (contents not in git)
├── outputs/                 the runs root: everything a run writes (not in git)
├── docs/                    DATA.md · CODE_MAP.md (this) · CHANGELOG_FINALE.md · RELEASE_NOTES.md · the working record
├── main.py                  the Round 1 command-line driver, carried over; the interface does not use it
└── requirements-demo.txt    one environment for the three stages
```

The stages share no Python. They are joined only by files on disk (see "Seams"), and each stage keeps its
own pinned copy of the schemas and of the instrument it reads. The interface imports no stage code.

---

## The interface (`interface/`)

**What it is.** A local web server on `127.0.0.1:8765` and one page. It reads what the stages write,
starts the stages' own command lines as child processes, and keeps the review decisions. Standard library
only, so a reviewer installs nothing for it. 8,355 lines of Python outside the tests (`app.py` and the
package `rdtii_ui/`), 51 routes, 291 tests in 24 files. Start here: `interface/app.py`.

Paths in this table are relative to `interface/rdtii_ui/`.

| File | What it holds | Names |
| :--- | :--- | :--- |
| `server.py` | the route table, a per-process token on every POST, JSON and static files | `App :61` · `Handler._dispatch :165` · `make_server :236` |
| `settings.py` | every location is an environment variable with a clean-clone default | `DEFAULTS :24` · `Settings :109` · `load :165` · `describe :235` |
| `machine.py` | which Python runs each stage on this computer, kept in `machine.json` | `describe :36` · `set_python :63` |
| `jobs.py` | the run layer: a queue of one, lines to sentences, Stop, the self-test | `Step :32` · `Job :44` · `JobManager :109` · `JobManager._run_step :227` · `selftest_job :306` |
| `proc.py` | every child process goes through here; Stop ends the whole process tree | `popen_quiet :41` · `kill_tree :54` · `console_python :133` |
| `envbuild.py` | the engine choice, the keys held in memory, the allowlist the browser is held to | `ALLOWLIST :18` · `KeyHolder :32` · `EngineState :94` · `role_choices :211` · `build_env :242` |
| `probes.py` | the header's health dots: Ollama, Tesseract, the crawler's browser (a real launch), stages present | `probe_ollama :20` · `probe_tesseract :76` · `probe_browser_launch :165` · `probe_imports :188` · `stage_presence :243` |
| `readers.py` | readers for what the stages write, with a small cache | `HOST_COLUMNS :15` · `cached :33` · `run_manifest :159` · `manifest_cost :175` · `parse_indicator_order :214` |
| `sources.py` | the sources of each economy and the folder each one owns | `HAND :30` · `crawl_source :64` · `designated :75` · `scrape_run_dir :129` · `scrape_runs :138` |
| `fsguard.py` | path safety for the Clear buttons | `CLEARABLE :25` · `check_clearable :80` · `issue_token :129` · `clear :151` |
| `review.py` | the decisions log and the export | `record_decision :63` · `apply_decisions :119` · `write_csv :136` · `write_xlsx :161` · `export :210` |
| `notes.py` | the run note a person types at Start | `write :23` · `read :34` · `carry :47` |
| `readiness.py` | whether the extraction stage can read a hand-collected file, judged from what the file is | `sniff :20` · `judge :59` |
| `detect.py` | language and economy of a hand-collected file: a warning, never the record | `detect_language :129` · `detect_folder :179` |
| `weburl.py` | the address a saved web page came from, read from the file | `recover_url :35` |
| `lifecycle.py` | when the interface stops, once it has a window | `decide :61` · `watch :84` · `InstanceNote :115` |
| `shell.py` | the window: the machine's own Edge or Chrome in app mode | `state_dir :36` · `find_browser :110` · `app_args :133` · `launch :147` |
| `paths.py` | path rules that hold on every system | `venv_python :19` |
| `core.py` | routes every page shares: health, engines, keys, Open folder, the documentation list | `register :22` · `list_docs :181` |
| `pages/scrape.py` | the Scraping page | `list_economies :255` · `holdings :372` · `run_state :491` · `list_crawl_folders :530` · `registry_fingerprints :733` · `link_state :762` · `estimate :793` · `precheck :937` · `P1_RULES :1051` · `write_quick_list :1184` · `plan_scrape :1206` |
| `pages/cn_run.py` | China from the Scraping page: its own tools as a run | `PUBLISHERS :34` · `precheck_cn :190` · `plan_cn :230` · `list_documents :319` |
| `pages/china.py` | the page Scraping › China | `describe :109` |
| `pages/inbox.py` | the Hand-collected block: drops, archives, addresses | `describe :190` · `unpack :260` · `save :301` · `set_address :336` |
| `pages/extract.py` | the Extraction page | `DEFAULT_LANGUAGE :35` · `HAND_ECONOMIES :37` · `list_inputs :339` · `build_manifest_rows :513` · `write_manifest :595` · `P2_RULES :638` · `precheck :687` · `plan_extract :854` · `unread_documents :978` · `output_state :1051` |
| `pages/mapping.py` | the Mapping page | `step_models :101` · `recorded_cost :119` · `list_runs :172` · `build_rows :268` · `row_detail :360` · `indicator_picker :421` · `MODEL_STAGES :487` · `describe_handoff :557` · `precheck :750` · `P3_RULES :1008` · `selection_with :1096` · `plan_map :1117` |

**How a run goes.** The page posts the request to the stage's `precheck` route (Check), then to its
`start` route. Start runs the same checks again and refuses when one fails. The plan function builds a
`Job` of `Step`s: for each, the command, the stage folder to run it in, the environment, and the table of
patterns (`P1_RULES`, `P2_RULES`, `P3_RULES`) that turns the stage's printed lines into the sentences shown
under the button. `JobManager` runs one job at a time. Stop ends the child and everything it started.

**What each Start runs**, in the stage's own folder, with the Python that Appendix → This machine names:

| Page | Commands, in order |
| :--- | :--- |
| Scraping | an import check; with Refresh from the portal, `python -m p1_scrape.adapters.<package>.catalogue --out <list folder>`; then `python scrape.py --economy <CC> --pillars 6,7 --out <run folder> --scope <scope> --forms pdf`, with `--dry-run` when ticked. One job per economy. The link list is handed over in two variables the adapter reads, `<PREFIX>_FRONTIER=links_file` and `<PREFIX>_LINKS_FILE` |
| Scraping, China | the China tools, `collect.py` or `update.py` (`pages/cn_run.py`) |
| Extraction | an import check; `python -m rdtii_p2.cli ocr` when the input holds scanned PDFs; `python -m rdtii_p2.cli run --manifest … --raw … --out … --default-language <lang> --skip-tags`. One pass per economy when the economies of a folder read in different languages |
| Mapping | an import check; `python -m src.p3map.cli ingest`, `prefilter --leg bm25`, `prefilter --leg dense` (each only when the index lacks it); `cli select`; `python -m src.p3map.triage.haiku` (the quick screen); `python -m src.p3map.discovery.baseline` when a baseline workbook is set; then per economy `python -m src.p3map.mapping.runner <CC>` and `python -m src.p3map.chain <CC>`, with `--gloss` when translation is ticked |

**The engine and the model of a step.** The browser names a choice; the server checks it against lists it
owns. `envbuild.py` reads the engines from the stage's `engines.json`, holds one key per provider in memory
under the variable its engine reads, and builds the child's environment: `RDTII_ENGINE`, and for a step
given its own provider `RDTII_ENGINE_MAPPER`, `RDTII_ENGINE_VERIFIER` or `RDTII_ENGINE_ESCALATION` with the
model variable of that role. A key no step uses is passed to no process.

**The page.** `static/index.html` holds the markup of every page, the whole text of the Overview, and the
one data block the cost report is drawn from (`#cost-data`). `static/app.js` draws the stage pages from the
routes. `static/app.css` ends with one layer that sets shapes and spacing and no colour.

The rules the code keeps (what Clear may touch, what the export may read, when the window stops) are
listed in `interface/README.md`.

---

## P0 — the instrument (`stages/p0-instrument/`)

**What it is.** The codebook the mapping stage reads. Nothing here runs inside the pipeline: the scripts
build and check YAML, which the mapping stage keeps as a byte-identical copy in
`stages/p3-map/contracts/instrument/`.

```
p0-instrument/
├── output/     indicators.yaml (61 blocks) · policies.yaml · indicator_order.yaml
│               signatures/<ID>.yaml (61) · gold/gold_set.jsonl (1,054 rows)
│               INSTRUMENT_NOTES.md · VALIDATION_<date>.txt
└── scripts/    the builders, the validator, the reports
```

A block of `indicators.yaml` gives the reading its question, definition, scoring, scoring tree,
disambiguation (the TRAP lines), coding rules and exceptions, and gives the roll-up its count rule and
what an absence scores. The host's workbooks the scripts parse are not in the repository; `.gitignore`
names them.

Paths in this table are relative to `stages/p0-instrument/scripts/`.

| File | Role | Names |
| :--- | :--- | :--- |
| `rdtii_examples.py` | the shared parser for the host workbooks, all pillars, decimal IDs | `parse_workbook :140` · `load_methodology :202` |
| `build_indicator_order.py` | writes `indicator_order.yaml`, the one ordered list of IDs with scope and coverage marks | `main :73` |
| `build_indicators_from_methodology.py` | gives every in-scope indicator a block, from the host's text where none was written | `tier_c_block :87` · `main :134` |
| `codebook_file.py` | the codebook file as text: a header, then one block per indicator in host order | `split :30` · `assemble :85` |
| `build_rollup_fields.py` | writes the count rule and the absence score into the blocks | `main :116` |
| `build_signatures.py` | writes `signatures/<ID>.yaml`, what the retrieval step searches with | `main :42` |
| `build_gold.py` | the host's baseline rows as `gold_set.jsonl`, with label flags | `load_label_flags :46` · `main :107` |
| `validate_instrument.py` | the validation; with `--require-vendored` it also checks the mapping stage's copy | `check :97` · `same_content :493` |
| `indicator_ids.py` | decimal text is the one vocabulary of IDs (`6.1`, never `P6-I1`); the same file sits in `stages/p3-map/config/` | `normalize :34` · `sort_key :72` |

Reports: `report_coverage.py`, `report_flags.py`, `report_rollup_fields.py`, `measure_prefix.py`,
`build_notes.py`. Their outputs are under `docs/stages/p0-instrument/evidence/`.

---

## P1 — the crawler (`stages/p1-scrape/`)

**In:** a source registry per economy, `instrument/sources_<cc>.yaml`, and usually a link list.
**Out:** a crawl folder: `manifest.csv` and `manifest.jsonl` (one row per stored document),
`manifest_meta.jsonl` (the adapter's facts about each file, such as its language), `raw/` with a headers
file beside each document, `crawl_log.jsonl`, `crawl_status.json`, `cost_report.json`. Nothing is parsed
or read by OCR here.

```
p1-scrape/
├── scrape.py                 the wrapper the interface calls -> src/p1_scrape/cli.py
├── config/settings.py        delay, retries, robots flags, user agent
├── contracts/schemas/manifest.schema.json     the manifest's authority
├── instrument/ · contracts/instrument/        sources_<cc>.yaml, the registry, in two copies
├── links/<cc>/               the shipped link list of each economy, with the seed laws
├── handoff1/<CC>/            the finale corpus described without its bytes (manifests, law tables)
├── src/p1_scrape/            the engine, and one package per portal under adapters/
├── tools/                    audit_run.py, merge_corpus.py and one-off checks
└── tests/                    429 pass, 3 skipped
```

Paths in this table are relative to `stages/p1-scrape/src/p1_scrape/`. Start here: `orchestrator.py`.

| File | Role | Names |
| :--- | :--- | :--- |
| `cli.py` | `crawl`, `smoke`, `validate` | `build_parser :17` · `cmd_crawl :76` · `cmd_validate :49` · `main :111` |
| `orchestrator.py` | the crawl loop | `CrawlHealth :42` · `run_crawl :149` · `_crawl_queue :245` · `_store_row :326` · `_build_row :363` |
| `adapters/base.py` | the contract every adapter fills in | `PortalAdapter :19` · `PortalAdapter.discover :23` · `PortalAdapter.build_plans :27` · `PortalAdapter.extract_anchor :31` |
| `adapters/registry.py` | economy code to adapter: SG, MY, AU, TL, LA | `get_adapter :24` |
| `fetcher.py` | requests first, the browser when needed, with backoff | `Fetcher :65` · `Fetcher.fetch :108` · `THROTTLE_STATUSES :28` |
| `politeness.py` | the delay per host and the robots check | `RateLimiter :17` · `RobotsAdvisor :37` |
| `classifier.py` | web page, PDF with text, or scanned PDF | `classify :39` |
| `dedup.py` | seen-before, and the stable `doc_id` | `Dedup :31` · `Dedup.is_retrieved :83` · `Dedup.stable_id :89` |
| `storage.py` | where a file and its headers are stored | `Storage :25` |
| `manifest.py` | the writers and the check a crawl ends with | `write_manifest_meta :35` · `write_manifest :67` · `validate_manifest :117` |
| `models.py` | the manifest's 28 columns and the candidate and plan records | `MANIFEST_FIELDS :15` · `Candidate :77` · `FetchPlan :104` · `FetchResult :165` |
| `schema.py` | rows checked against `manifest.schema.json` | `validate_row :85` |
| `economies.py` | codes and names; a bad name is refused, not guessed | `VALID_CODES :15` · `parse_economies :29` |
| `sources.py` | loads the registry | `load_sources :20` |
| `utils.py` | time stamps, hashes, slugs | `slugify :34` · `acronym_slug :72` |

**One crawl.** `cmd_crawl` → `run_crawl`: for each economy, `get_adapter`, then `adapter.discover()`
gives candidates and `adapter.build_plans()` the documents to fetch; `_crawl_queue` paces and fetches with
retry rounds; `_store_row` classifies and stores; `_build_row` fills the manifest row. An economy that
fails is skipped and the others go on. The run ends by writing the manifest and checking it against the
schema; a manifest that fails makes the crawl exit 1.

**The adapters.** One package per portal under `adapters/`: `sg_sso`, `my_gazette`, `au_legislation`,
`tl_jornal`, `la_gazette`. Each has `adapter.py` (discovery and fetch plans), `catalogue.py` (reads the
portal's listings into a link list: `documents.jsonl`, `laws.csv` and `catalogue_meta.json`, which records
the fingerprint of the registry the list was built for), `checker.py` (the law table), `parse.py`, and
`updates/` (what changed since a baseline). A crawl replays a link list when the adapter's frontier is
`links_file`, and refuses a list built for another registry.

**Politeness.** `REQUEST_DELAY_MS` (3000 by default) and one request at a time per host, in
`config/settings.py`. Malaysia's portal has its own paced client and robots rules:
`stages/p1-scrape/src/p1_scrape/adapters/my_gazette/client.py` `LomClient :19` and
`stages/p1-scrape/src/p1_scrape/adapters/my_gazette/robots.py` `RobotsRules :11`.

**China** is not in the adapter registry. `adapters/cn_npc/` holds tools, not an adapter: `collect.py`
(the publishers that permit collection), `update.py` (what changed), `layer1.py` (the national database's
archives, read offline), `manual_check.py` and `triage.py` (the worklists for what is fetched by hand),
`checkdocs.py`, and the client every Chinese source goes through,
`stages/p1-scrape/src/p1_scrape/adapters/cn_npc/polite.py` `PoliteClient :70`.

---

## P2 — extraction (`stages/p2-extract/`)

**In:** a crawl folder (manifest and stored files), or the manifest the interface writes for
hand-collected files. **Out:** `provisions.jsonl` (one record per provision, each with a snippet that is a
character-exact passage of the stored text), `laws.jsonl`, `doc_status.jsonl`, `source_text/<doc_id>.txt`
(the frozen text), `by_law/`, `ocr/` (the page cache), `extract_log.jsonl`, `cost_report.json`. Contract
0.3.0.

```
p2-extract/
├── config/                 settings.py · ocr/ (Tesseract, optional PaddleOCR and Azure) · llm/ (tagging)
├── 00_contracts/schemas/   manifest, provision and laws schemas
├── fixtures/               the Tesseract packs (fast, best) and the reference pages
├── src/rdtii_p2/           the stage
└── tests/                  128 pass, 2 skipped, 6 fail for want of a workshop tool this repository does not hold
```

Paths in this table are relative to `stages/p2-extract/src/rdtii_p2/`. Start here: `cli.py`.

| File | Role | Names |
| :--- | :--- | :--- |
| `cli.py` | `run`, `ocr`, `tag-corpus`, `validate`, `demo`, `pilot` | `cmd_run :362` · `cmd_ocr :793` · `cmd_validate :842` · `_segment_for :116` · `_parse_doc :141` · `_extract_doc :227` · `main :1153` |
| `ingest.py` | the manifest's schema gate and contract check | `load_manifest :119` · `check_contract_major :108` · `preflight :166` |
| `sidecars.py` | facts the manifest does not carry (language, several acts in one file), and the decision to read a file | `DocFacts :50` · `_read_manifest_meta :165` · `load_facts :199` |
| `router.py` | the lane for a file: A web page, B PDF with text, C scanned PDF, D Word | `LANE_BY_TYPE :21` · `route :35` |
| `parse_html.py` | lane A, one parser per portal | `PORTAL_PARSERS :317` · `parse :340` · `parse_au :51` · `parse_cn_portal :285` |
| `parse_pdf_native.py` | lane B | `extract_pages :16` |
| `ocr_prepass.py` · `ocr_cache.py` | lane C: scanned pages read in parallel into a page cache, once | `run_prepass :93` |
| `parse_docx.py` | lane D | `extract :63` |
| `normalize.py` | the text is normalised once, then frozen | `normalize_pages :182` · `detect_furniture :113` |
| `segment.py` | splitting in the common-law style: sections, subsections, schedules | `segment :362` |
| `segment_civil.py` | splitting by article, one profile per language (Artigo, ມາດຕາ, 第…条, Article), with repair of a misread number from its position | `PROFILES :112` · `ENGLISH_ARTICLES :110` · `segment_civil :257` · `_repair_sequence :209` |
| `acts.py` | which act inside a gazette file a provision belongs to | `locate :81` · `act_at :128` |
| `ground.py` | the grounding gate | `copy_grounded :29` · `verify :42` · `locate_exact :54` |
| `extract_fields.py` | the record: fixed fields, grounded metadata, optional tags | `build_record :430` · `ground_doc_metadata :135` · `candidate_spans :335` · `snippet_offsets :363` |
| `emit.py` | the writers | `write_source_text :54` · `write_doc_status :94` · `write_laws :99` · `write_provisions :113` · `write_cost_report :150` |
| `status.py` | the statuses a document can end with | `VALID_STATUSES :12` |
| `cer.py` | the character-error measurement on the reference pages | `cer :30` · `measure_doc :63` |

**One document.** `cmd_run` loads the manifest (every row checked against the schema), and for each
document: `route` picks the lane; `_parse_doc` reads it; the text is normalised; `_segment_for` picks the
splitter from the declared language (never from the text); `_extract_doc` builds a record per provision,
and `ground.verify` drops any record whose snippet is not in the text. The frozen text is written only
after the document succeeded. The interface runs with `--skip-tags`, so no model is called in this stage.

**Language.** The OCR pack follows the declared language:
`stages/p2-extract/config/ocr/langmap.py` `LANGUAGE_TO_PACK :27`, `check_packs :72`. The engine is chosen
in `stages/p2-extract/config/ocr/factory.py` `get_ocr :13`.

---

## P3 — mapping (`stages/p3-map/`)

**In:** an extraction output, the instrument, and the host's baseline workbooks when they are set.
**Out**, under `OUT_DIR`: `submission/records_<E>.csv` (14 columns) and `.json`, `rollup/`, `verify/`,
`audit/`, `results/` (the review workbook), and `run_manifest.json`.

```
p3-map/
├── config/
│   ├── settings.py · selection.py + selection.json · instrument.py · economies.py · manifest.py
│   └── llm/                engines.json · engines.py · factory.py · one client per provider
├── contracts/instrument/   the byte-identical copy of p0-instrument/output
├── 00_contracts/schemas/   copies of the hand-off schemas
├── src/p3map/              the stage
├── docs/ab/                the July A/B tests, with their rules written before the runs
└── tests/                  505 pass, 8 skipped
```

Paths in this table are relative to `stages/p3-map/`. Start here: `config/llm/factory.py`, then
`src/p3map/select.py`.

| Step | File | Names |
| :--- | :--- | :--- |
| Settings | `config/settings.py` | `Settings :24` · `ECONOMIES :161` |
| The instrument, one view of it | `config/instrument.py` | `Instrument :70` · `Instrument.values :118` · `Instrument.count_rule :142` · `Instrument.absence :151` · `Instrument.traps :169` · `load :269` |
| Economies and their languages | `config/economies.py` | `ECON_NAME :25` · `PRIMARY_LANGUAGE :43` · `resolve :66` |
| The engines | `config/llm/engines.py` | `Engine :60` · `selected :160` · `price_cards :185` |
| Provider for a role | `config/llm/factory.py` | `PROVIDERS :32` · `get_llm :66` |
| The clients | `config/llm/anthropic_client.py` · `config/llm/ollama_client.py` · `config/llm/openai_compat_client.py` | `OpenAICompatClient :77` |
| Prices and usage | `config/llm/base.py` | `Usage :9` · `PRICES :25` · `price_card :32` · `usd :45` · `LLMClient :54` |
| The run manifest | `config/manifest.py` | `header :96` · `record :146` |
| S0 ingest: every quote checked again | `src/p3map/ingest.py` | `run_ingest :105` |
| S1 keyword index | `src/p3map/prefilter/bm25.py` | `run_bm25 :23` |
| S1 meaning index | `src/p3map/prefilter/dense.py` | `run_dense :34` |
| S2 candidate selection (A on the page) | `src/p3map/select.py` | `MODES :40` · `CAPS :45` · `run_select :143` · `_select_by_score :193` · `caps_in_effect :247` · `_select_by_caps :269` |
| The threshold function | `config/selection.py` | `load_config :138` · `params_for :200` · `select_cell :262` |
| S3 quick screen (B) | `src/p3map/triage/haiku.py` | `run_haiku_triage :43` |
| S4 careful reading (C): the prompt | `src/p3map/mapping/prompt.py` | `number_traps :29` · `build_system_prefix :43` · `build_user_turn :78` |
| S4: the answer form | `src/p3map/mapping/schema.py` | `TrapChecks :46` · `IndicatorVerdict :71` · `OwnTrap :121` · `MappingVerdict :161` · `coerce_verdict :259` |
| S4: the run | `src/p3map/mapping/runner.py` | `run_mapping :57` |
| S4: the batch lane the finale used | `src/p3map/mapping/batch_runner.py` | `submit :189` · `poll :224` · `fetch :249` |
| The quote anchored to the source | `src/p3map/mapping/anchor.py` | `anchor :96` |
| S5 re-check (D) and tie-break (E) | `src/p3map/verify/blind.py` | `run_verify :48` |
| S7 NEW against KNOWN | `src/p3map/discovery/newknown.py` | `run_newknown :103` |
| The baseline loader | `src/p3map/discovery/baseline.py` | `load_baseline :139` |
| S6 scores per economy | `src/p3map/rollup.py` | `apply_count_rule :46` · `measure_score :114` · `run_rollup :181` · `_framework_score :276` |
| S9 the rows | `src/p3map/output/submission.py` | `COLUMNS :54` · `run_submission :270` |
| S9b English for review | `src/p3map/output/gloss.py` | `run_gloss :76` · `run_section_gloss :190` |
| The review workbook | `src/p3map/output/excel_export.py` | `export :196` |
| The audit page | `src/p3map/verify/audit_view.py` | `render :100` |
| S10 self-evaluation against the gold set | `src/p3map/eval/evaluator.py` | `run_eval :49` |
| The order of S5 to S10 | `src/p3map/chain.py` | `run_chain :38` |
| S9c the host's workbook | `src/p3map/output/template.py` | `curate :99` · `fill :175` · `verify_filled :229` |
| S9d the submission folder | `src/p3map/output/package.py` | `merge_csv :45` · `build :112` |

**How the steps run.** `src/p3map/cli.py` covers ingest, the two indexes and selection. The later steps
run as `python -m src.p3map.<module> <ECON>`; `chain.py` runs S5, S7, S6, S9, S10, then the glosses when
asked, the workbook and the audit page, in that order for one economy. Filling the host's workbook and
assembling the submission folder are whole-run steps, run by hand after the last economy; the interface
does not run them.

**What the model sees.** A system prefix built from the instrument's blocks for the indicators in scope,
the same bytes for every provision of a run, then one turn with the provision and its candidate
indicators. The answer is forced into the form in `mapping/schema.py`. The five fixed trap questions are
asked only when an indicator of pillars 6 and 7 is in the run; any other indicator answers the TRAP lines
of its own block. `tests/test_second_handoff.py` pins the requests for pillars 6 and 7.

**The engines.** `config/llm/engines.json` (version 1.1.0) declares five: A Claude and B local Qwen, the
two the pipeline was measured on, and C DeepSeek, D Kimi and E ChatGPT, reached through the
OpenAI-compatible client and marked `measured: false`. Each lists its models with a price card.
`RDTII_ENGINE` selects one; `RDTII_ENGINE_MAPPER`, `RDTII_ENGINE_VERIFIER` and `RDTII_ENGINE_ESCALATION`
give a role an engine of its own; `RDTII_ENGINES_FILE` names another declaration. A role whose provider
has no key is refused: the stage does not hand the careful reading, the re-check or the tie-break to a
local model by itself.

**Cost.** Prices live in the engines' price cards and `config/llm/base.py`. Each step writes its own
report and adds its cost to `run_manifest.json`; the interface shows that figure and computes none.

---

## `main.py` — the Round 1 driver (1,080 lines)

Carried over on 29 September and unchanged since: `--economy X --pillar N` (serve), `--demo`, `--quick`,
`--mini-run`, `--full-pipeline`. The interface does not call it. Tried on 5 October, the serve mode ends
without error and writes no rows, because `main.py` `cmd_serve :225` keeps rows whose Indicator ID begins
`P6-` and the filed rows carry `6.1`. The other modes were not tried. See `docs/DATA.md`.

---

## Seams — the files that join the stages

| Seam | From → to | Files | Authority |
| :--- | :--- | :--- | :--- |
| Crawl folder | P1 → P2 | `manifest.csv`, `manifest.jsonl`, `manifest_meta.jsonl`, `raw/**`, the headers files, `crawl_log.jsonl` | `stages/p1-scrape/contracts/schemas/manifest.schema.json`; the columns in `stages/p1-scrape/src/p1_scrape/models.py` `MANIFEST_FIELDS :15`. The manifest admits no other field, which is why the adapter's facts are a side file |
| Hand-collected files | interface → P2 | the manifest and law table written under `outputs/scrape/<CC>/Hand_collected/`, and `left_out.csv` | `interface/rdtii_ui/pages/extract.py` `build_manifest_rows :513`, to the same schema |
| Extraction output | P2 → P3 | `provisions.jsonl`, `laws.jsonl`, `doc_status.jsonl`, `source_text/<doc_id>.txt` | `stages/p2-extract/00_contracts/schemas/`; copies in `stages/p3-map/00_contracts/schemas/` |
| Instrument | P0 → P3 | `indicators.yaml`, `policies.yaml`, `indicator_order.yaml`, `signatures/`, `gold/` | `stages/p0-instrument/output/`; copy in `stages/p3-map/contracts/instrument/`, checked by the validator |
| Rows | P3 → interface, host | `records_<E>.csv`, 14 columns, and `.json` | `stages/p3-map/src/p3map/output/submission.py` `COLUMNS :54`; the interface holds the same list in `interface/rdtii_ui/readers.py` `HOST_COLUMNS :15` |
| Run record | P3 → interface | `run_manifest.json`: the model of each role, the git commit, the settings, the cost per step | `stages/p3-map/config/manifest.py` |
| Decisions | interface | `outputs/reviews/<run>/decisions.jsonl`, append-only | `interface/rdtii_ui/review.py` `record_decision :63` |

---

## Configuration

| Part | File | Keys that matter |
| :--- | :--- | :--- |
| P1 | `stages/p1-scrape/config/settings.py` | `REQUEST_DELAY_MS` (3000), `MAX_CONCURRENCY_PER_HOST` (1), `FETCH_TIMEOUT_MS`, `FETCH_RETRIES`, `RESPECT_ROBOTS_FOR_DISCOVERY`, `MAX_CANDIDATES_PER_ECONOMY`, `USER_AGENT`; per adapter, `<PREFIX>_FRONTIER` and `<PREFIX>_LINKS_FILE` |
| P2 | `stages/p2-extract/config/settings.py` | `HANDOFF1_DIR`, `OUT_DIR`, `OCR_ENGINE` (tesseract), `LLM_PROVIDER` and `LLM_MODEL` for tagging, `TAG_BATCH_SIZE` |
| P3 | `stages/p3-map/config/settings.py` | `HANDOFF2_DIR`, `OUT_DIR`, `INDEX_DIR`, `INSTRUMENT_DIR`, `BASELINE_PATH`, `BASELINE_R2_PATH`, `ECONOMIES`, `INDICATORS_SCOPE`, `SELECT_MODE`, `SELECTION_CONFIG`, `CAPS_OVERRIDE`, `PREFILTER_TOPK`, `EMBED_MODEL`, `EMBED_DEVICE`, `OLLAMA_NUM_CTX`, `MAP_WORKERS`, `VERIFY_WORKERS`, `TRIAGE_WORKERS`, `COST_HARD_STOP`, `NEW_CONF`, `NEW_CAP`; the engine variables above |
| Interface | `interface/rdtii_ui/settings.py` | the data locations (`docs/DATA.md`), `RDTII_RUNS_ROOT`, `RDTII_INBOX_DIR`, `RDTII_PYTHON_P1`, `_P2`, `_P3`, `RDTII_HOST`, `RDTII_PORT`, `RDTII_BROWSER`, `RDTII_STATE_DIR`, `RDTII_REVIEWER`; the full table is in `interface/README.md` |

Each stage also loads a `.env` from its own folder; a real environment variable wins. The interface sets
variables for the child process and edits no file under `stages/`.

---

## Where to look when…

| Symptom or task | Go to |
| :--- | :--- |
| A crawl ends "schema check FAILED" | `stages/p1-scrape/src/p1_scrape/manifest.py` `validate_manifest :117`; a field that is not in the schema belongs in the side file, `write_manifest_meta :35` |
| The crawler refuses a link list | the list's `catalogue_meta.json` against the registry; the interface asks the crawler's own code in `interface/rdtii_ui/pages/scrape.py` `registry_fingerprints :733` and reports it in `link_state :762` |
| A portal blocks or slows the crawl | `stages/p1-scrape/src/p1_scrape/fetcher.py` `THROTTLE_STATUSES :28` and the backoff in `Fetcher`; `stages/p1-scrape/src/p1_scrape/orchestrator.py` `CrawlHealth :42` |
| Check says the crawler's browser cannot start | `interface/rdtii_ui/probes.py` `probe_browser_launch :165`; repair with `python -m playwright install chromium` |
| A hand-collected file "cannot be read" | `interface/rdtii_ui/readiness.py` `judge :59`; the portals with a page parser are `stages/p2-extract/src/rdtii_p2/parse_html.py` `PORTAL_PARSERS :317` |
| A document gave no provisions | Extraction → 2.3 Output → "N to check" (`interface/rdtii_ui/pages/extract.py` `unread_documents :978`); the splitting patterns are `stages/p2-extract/src/rdtii_p2/segment_civil.py` `PROFILES :112` |
| A scanned page was read in the wrong language | the declared language in the manifest or `manifest_meta.jsonl`; `stages/p2-extract/config/ocr/langmap.py` `LANGUAGE_TO_PACK :27` |
| A quoted snippet does not match the source | `stages/p2-extract/src/rdtii_p2/ground.py` `verify :42`; checked again at `stages/p3-map/src/p3map/ingest.py` `run_ingest :105`; a model's quote is anchored by `stages/p3-map/src/p3map/mapping/anchor.py` `anchor :96` |
| Mapping says the index is ranked for other indicators | `interface/rdtii_ui/pages/mapping.py` `describe_handoff :557`; Start ranks both indexes again |
| The wrong indicator fired | first `stages/p3-map/src/p3map/mapping/prompt.py` (what the model saw), then the trap answers in `mapping/schema.py`, then `verify/blind.py` (was it overturned?) |
| A NEW or KNOWN tag looks wrong | `stages/p3-map/src/p3map/discovery/newknown.py` `run_newknown :103`; names compared by `stages/p3-map/config/lawnames.py` `same_law :88`; with no baseline set every match is NEW |
| A score looks wrong | `stages/p3-map/src/p3map/rollup.py` `measure_score :114`; the block's count rule and absence score in `indicators.yaml` |
| A cost figure looks wrong | the price card in `engines.json`; `stages/p3-map/config/llm/base.py` `usd :45`; the run's `run_manifest.json` read by `interface/rdtii_ui/pages/mapping.py` `recorded_cost :119`; the Overview's figures are the `#cost-data` block of `interface/static/index.html` |
| Give a step another model | Mapping → 3.2 Run; under it `interface/rdtii_ui/envbuild.py` `role_choices :211` and `stages/p3-map/config/llm/factory.py` `get_llm :66` |
| Add a provider with an OpenAI-compatible API | one entry in `stages/p3-map/config/llm/engines.json` |
| Move a threshold for one run | the number box in Mapping → 3.2 Run → A; `interface/rdtii_ui/pages/mapping.py` `selection_with :1096` writes the run's own copy; the stage reads it through `SELECTION_CONFIG` |
| Add an economy | the list in the interface, Appendix → Adding a new economy; then `stages/p1-scrape/src/p1_scrape/adapters/registry.py`, `stages/p1-scrape/src/p1_scrape/economies.py` `VALID_CODES :15`, a registry and a link list; `stages/p2-extract/src/rdtii_p2/segment_civil.py` `PROFILES :112` and the OCR pack; `stages/p3-map/config/economies.py` `ECON_NAME :25` and a language offset in `selection.json`; `interface/rdtii_ui/pages/extract.py` `DEFAULT_LANGUAGE :35` |
| Change a rulebook or add an indicator | `stages/p0-instrument/output/indicators.yaml`, then `validate_instrument.py`, then the copy in `stages/p3-map/contracts/instrument/`; a threshold class in `selection.json` |
| Output shows no runs, or the wrong ones | `python interface/app.py --print-settings`; `OUT_DIR` and `RDTII_RUNS_ROOT`; `interface/rdtii_ui/pages/mapping.py` `list_runs :172` |
| Stop leaves a process behind | `interface/rdtii_ui/proc.py` `kill_tree :54` |
| The window does not stop the tool, or stops it too early | `interface/rdtii_ui/lifecycle.py` `decide :61` |
| Clear refuses a folder | `interface/rdtii_ui/fsguard.py` `check_clearable :80` |
| An exported file looks wrong | `interface/rdtii_ui/review.py` `apply_decisions :119`, `write_xlsx :161`; the decisions are in `outputs/reviews/<run>/decisions.jsonl` |
| Which Python runs a stage | Appendix → This machine; `interface/rdtii_ui/settings.py` `Settings.python_for :137` |
| Why the code looks the way it does | `docs/CHANGELOG_FINALE.md`, one entry per change with how it was verified; decisions in `docs/stages/<stage>/DECISIONS.md` |
