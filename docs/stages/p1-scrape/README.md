# Task 1, Scraping: finding and retrieving the law

This folder is a workshop, not a code repository. It holds the plan, the decisions, the working
notes and the evidence for one task. The crawler itself lives in the one repo, at
`C:\Users\woshi\Desktop\rdtii-rocky-finale\stages\p1-scrape`. Source is copied only into `countries\` and, for the audit and corpus tools, `tools\` (decisions 8 and 17).

## What this task owns

The crawler is the only stage that touches the live internet. It finds candidate laws on official
government portals. It retrieves the raw bytes with full HTTP provenance. It hands Project 2 a
manifest that every downstream stage joins on.

| Owned | Where it lives in the repo |
| :---- | :---- |
| Portal discovery | `src/p1_scrape/adapters/` and `instrument/sources_<cc>.yaml` |
| Fetching over anti-bot and JS pages | `src/p1_scrape/fetcher.py`, the four-rung escalation ladder |
| Politeness and robots | `src/p1_scrape/politeness.py`, `config/settings.py` |
| Source classification | `src/p1_scrape/classifier.py`, html / pdf_native / pdf_scanned |
| Stable document IDs and supersession | `src/p1_scrape/dedup.py`, `.idmap.json` |
| The Hand-off #1 manifest | `contracts/schemas/manifest.schema.json`, 28 columns, 15 required |
| Raw byte storage and header sidecars | `src/p1_scrape/storage.py` |

## What this task does NOT own

OCR. Text cleaning. Provision splitting. Indicator mapping. The interface. Those belong to P2, P3
and the interface task. This task stops at bytes on disk plus a validated manifest row.

One boundary is easy to get wrong. The manifest **records** the language of a document. It does
not translate, normalise or interpret it. Deciding what a Thai provision means is P3's work.

## Where the code lives

Repo root: `C:\Users\woshi\Desktop\rdtii-rocky-finale`. Branch `finale`. No remote yet.

| File, relative to `stages\p1-scrape\` | What it does |
| :---- | :---- |
| `src/p1_scrape/orchestrator.py` | `run_crawl` at line 149, the work queue, resume, `_build_row` at 357 |
| `src/p1_scrape/adapters/base.py` | The three-method contract: `discover`, `build_plans`, `extract_anchor` |
| `src/p1_scrape/adapters/registry.py` | `get_adapter`, today a hard-coded if-chain over SG, MY, AU |
| `src/p1_scrape/fetcher.py` | requests, then api_request, then Playwright twice, each rung logged |
| `src/p1_scrape/politeness.py` | `RateLimiter` with jitter, `RobotsAdvisor` |
| `src/p1_scrape/dedup.py` | `.idmap.json`, `stable_id`, `is_retrieved`, URL normalisation |
| `src/p1_scrape/classifier.py` | `classify`, mean characters per page against a threshold of 100 |
| `src/p1_scrape/economies.py` | The economy list, hard-coded in `_NAME_TO_CODE` and `VALID_CODES` |
| `src/p1_scrape/models.py` | `MANIFEST_FIELDS` at line 15, `Candidate.law_slug` at line 100 |
| `contracts/schemas/manifest.schema.json` | The Hand-off #1 authority |
| `instrument/sources_{sg,my,au}.yaml` | Per-economy portals, seed laws, queries |

Data, outside the repo: `C:\Users\woshi\Desktop\RDTII\pipeline-data\rdtii-p1-scrape\handoff1_v2`.
That is the frozen corpus, about 1.85 GB, plus the manifests and the crawl log. It is hands off (decision 17).
New crawls are written to this workshop's `outputs\<CC>\<CC>_ws_<YYYY-MM-DD>\`, one folder per country and one
per run, each run with a `RUN_NOTE.md` and an `audit.md` (decisions 15 and 17), and the runs are merged into
`outputs\<CC>\<CC>_corpus_<date>\`, the folder downstream reads (`MY_corpus_2026-09-15`, 1,316 documents, is the
first). The repo versions only the light evidence, about 9 MB, and ignores the raw tree by a `.gitignore` rule.

**One trap before you edit any YAML.** `sources.py` searches `contracts/instrument/` first and
`instrument/` second. The two directories currently hold byte-identical copies of all three files.
Edit only `instrument/` and nothing changes, because the vendored copy wins silently. Edit both in
the same commit, every time.

## Rubric criteria this task carries

| Criterion | Marks | This task's share |
| :---- | ----: | :---- |
| C1a jurisdiction coverage, three or more diverse economies, minimal reconfiguration | 15 | Owned outright. Six or more economies must run without a code edit |
| C1c linguistic versatility | 10 | Shared. The crawler records the document's language, or nothing downstream knows what it is reading |
| C5 live stress test, discovery run | 6 | Dependency, not owned. The second pass reads 0 documents only if delta detection exists and the flag is reachable from the button |

C1c is shared. P3 proves the same indicator fires in any language. This task supplies the
`language` column that makes the claim checkable rather than asserted.

## Current state, 2026-09-12

Three English-language economies, crawled and frozen. Figures below come from
`C:\Users\woshi\Desktop\RDTII Finale Plan\3_Final_Stage\AUTHORITATIVE_NUMBERS.md`, the only place
Round 1 numbers may be quoted from.

| | Value |
| :---- | :---- |
| Current documents | 2,673, being SG 536, MY 869, AU 1,268 |
| Manifest rows | 2,706, being 2,673 current plus 33 superseded |
| Forms | 2,228 native PDF, 43 scanned PDF, 402 HTML |
| Corpus version | v2.4, 18 July 2026 |
| Raw size | about 1.85 GB including superseded files |
| Validation | 0 errors, 0 warnings across 2,706 rows |
| Politeness | 1 request per 3 seconds per host, 1 parallel per host, robots respected for discovery |
| Contract version | 0.2.0 |

Politeness already exceeds the host's floor. The host asks for 1 request per second. The default
`REQUEST_DELAY_MS` is 3000, with jitter of up to half the delay added on top. Do not relax it.

## What is missing, verified by reading the code today

| Gap | Where | Effect |
| :---- | :---- | :---- |
| **Economy list hard-coded three times** | `economies.py` `_NAME_TO_CODE` and `VALID_CODES`, schema `economy` enum at line 41, schema `doc_id` pattern at line 37 | A new economy fails validation even after its adapter works |
| **Registry is an if-chain** | `adapters/registry.py` `get_adapter` | A new economy needs a Python edit, which contradicts "minimal reconfiguration" |
| **Non-Latin titles collide** | `utils.py` `slugify` returns `"unknown"` for any title with no ASCII letters | Every Thai or Lao law lands in one directory. `Candidate.law_slug` exists at `models.py:100` and is never read |
| **Fetcher is pinned to English** | `fetcher.py:73` sends `Accept-Language: en`, `fetcher.py:85` sets a US locale | A bilingual portal serves the English page, so the non-English text is never fetched |
| **No language column** | `models.py` `MANIFEST_FIELDS`, all three schema copies | C1c has no machine-readable basis at all |
| **No change detection** | `dedup.py` `is_retrieved` is a binary "seen before" check, called at `orchestrator.py:209` | A re-run never re-fetches. A portal update is invisible. ETag and Last-Modified are stored in the sidecars and never read back |

Two smaller drifts surfaced in the same pass. The p1 copy of the schema still describes itself as
"24 fields" while carrying 28. The p2 and p3 copies already say 28. The `indicator_hints`
description at schema line 77 gives `P7-I2` as its example, which is the format the finale
forbids. Both belong in the 0.3.0 commit. See DECISIONS.md entry 5.

## Blocked on: which economies

**Scope decided 2026-09-12: six economies, so three new ones, all non-English, pillars 6 and 7
only. Further economies are optional.** See `DECISIONS.md` decision 7. What is still blocked is
which three. The text below predates the decision and explains the candidates.

Adapter work for the wrong economies is wasted work. Three host documents name three different
lists. The question is filed as question 1 in
`C:\Users\woshi\Desktop\RDTII Finale Plan\3_Final_Stage\OPEN_QUESTIONS_FOR_HOST.md`.

The working assumption is the seven economies that appear on every list and hold a baseline sheet.
Those are China, India, Indonesia, Lao PDR, Mongolia, the Russian Federation and Thailand. Add the
three Round 1 economies. Timor-Leste is a stretch target.

**Revised 2026-09-12 after reading the workbook.** Two things change the priority order. First,
the live test draws only from nine economies, and those nine include **Viet Nam and Kazakhstan**,
which have no baseline sheet. They were stretch targets. They are now live-test risks: an adapter
that cannot crawl them on the day scores zero on C5a if either is drawn. Second, question 6 asks
whether C1a needs three economies or six. Every host document agrees depth beats breadth. Finish
three deep new economies before starting a fourth.

Step 1A is deliberately economy-agnostic. It can be built and finished before the answer arrives.
Each new economy then costs the following.

| Item, per economy | Estimate |
| :---- | :---- |
| Adapter code | 4 to 8 hours |
| Seed-law curation | 2 to 4 hours |
| First full crawl, wall clock | 6 to 8 hours, politeness-limited, per `main.py:916` |

The crawl hours are the harder cost. That time cannot be compressed. The politeness limits are
not negotiable.

## New from the host templates, read line by line on 2026-09-12

This task is the most exposed of the five. Full detail is in
`C:\Users\woshi\Desktop\RDTII Finale Plan\3_Final_Stage\REQUIREMENTS.md`.

### The one sentence that changes the design

The Run Record sheet says: **"if no documents were fetched during the hour, C5a scores zero
regardless of what the evidence file contains."** Engine A must crawl live, on the day, cold. The
checklist adds that caches and downloaded-document folders must be **clearable on screen before
the clock starts**. A frozen corpus, however good, earns nothing in the live test.

Round 1's discovery was deliberately enumerative: crawl the whole portal, map later. That cannot
fit the live hour. At the current 3 seconds per request, 90 minutes allows about 1,800 requests
for crawling, extraction, mapping, review and export combined, and the task is one pillar and two
indicators. **The live test needs a targeted discovery mode**: given an economy, a pillar and two
indicator IDs, find and fetch the handful of laws most likely to carry them. The frozen corpus
stays the right tool for the 30 September evidence workbook. It is the wrong tool for 15 October.

### Everything else that binds this task

| Requirement | Source | Consequence |
| :---- | :---- | :---- |
| Live test is **one of nine economies**: Thailand, Viet Nam, Indonesia, China, India, Kazakhstan, Lao PDR, Mongolia, Russian Federation | Workbook Instructions, Word Section 4, README template | A working adapter for each is a live-test requirement, not only a C1a one. Singapore, Malaysia and Australia are not in the draw |
| **Every document downloaded is listed** with source URL, which pass, time, size in KB and file type | Workbook Run Record sheet | The crawl log must record the pass label and be exportable in that shape. A steward checks the Engine B count reads zero |
| **Caches clearable on screen** before the clock starts | Checklist item 26 | The crawler needs a clear operation the interface can call. It must also clear `.idmap.json`, or the resume check skips every law and fetches nothing, which is the C5a zero |
| **Politeness file and line references** for 1 request per second, 1 parallel per host, robots respected | README template, Crawling Politely | Three rows naming `config/settings.py` lines. See the robots note below |
| **robots.txt respected** | Checklist item 25, README template | Today robots is advisory: `ROBOTS_HARD_BLOCK=false`, and canonical seed URLs are never gated. Decide whether that can honestly be written as "respected: yes", and record the decision |
| **Zone 1 and Zone 2 are separate, documented modules** | Checklist item 10 | Already true by stage split. Say so in the README |
| **No hard-coded paths** | Checklist item 8 | `test_classifier.py` still defaults to a Desktop path, environment-overridable. Scrub before the release tag |
| **Economy uses the official UN name** in the output, but the Coverage Matrix counts "Lao PDR" and has **no Russian Federation row** | Workbook Instructions and Coverage Matrix | The economy YAML header should carry both `name` (the official UN name) and `matrix_label`. The export writer, owned by the dashboard task, reads them. See question 7 |
| **"Reads and translates"** is step 2 of the live test | Orientation slide 9 | The crawler must fetch the source-language text. `fetcher.py` still sends `Accept-Language: en`, which can serve an English page and hide the original |

## Borrow from Round 1

Round 1 built this crawler and wrote it up twice. Point at that material, never copy it. Nothing
below is duplicated into this folder, and no line of it is restated here. A document that has
gone stale stays on the list with the staleness named, because knowing a document is stale is
worth as much as knowing it exists.

Two roots, written once. `repo\` is `C:\Users\woshi\Desktop\rdtii-rocky-finale`. `plan\` is
`C:\Users\woshi\Desktop\RDTII Finale Plan`.

### Templates, worth more than the reference below

These four are the things you build from, not the things you read.

| Path | Why you open it for this task |
| :---- | :---- |
| `repo\stages\p1-scrape\src\p1_scrape\adapters\sg_sso.py` | The Playwright-portal pattern. SSO renders client-side, so HTML needs Playwright on `?WholeDoc=1` waiting for `div#legisContent`, while the PDF takes a plain `requests` fast-path. Model the fourth adapter on this when the portal needs a browser |
| `repo\stages\p1-scrape\src\p1_scrape\adapters\my_gazette.py` | The detail-page pattern. Every act is addressed by number, and one static fetch yields the document plus title, publication date, assent date and commencement remark. Model on this when the portal gives each law a landing page |
| `repo\stages\p1-scrape\src\p1_scrape\adapters\au_legislation.py` | The API-driven-register pattern. Metadata from an OData API, bytes from dated endpoints, epub spine concatenated for multi-volume acts. Model on this when the portal publishes a machine-readable index |
| `repo\stages\p1-scrape\tools\refetch_au_multivolume.py` | The only delta precedent anywhere in this codebase. It drives a targeted re-fetch through the normal orchestrator, so `.idmap.json` allocates the next seq and supersession happens by itself, and it acceptance-checks each stored file on the spot. Read it before writing 1B-4 and 1B-5 |

### Reference, beside the code

| Path | Why you open it for this task |
| :---- | :---- |
| `repo\stages\p1-scrape\START_HERE.md` | Four pages. The reading order for the stage, and the sentence that still governs: a tool reading pre-downloaded files scores zero on live crawling |
| `repo\stages\p1-scrape\STAGE_GUIDE.md` | How the stage is presented to a judge rather than to a builder. The register the finale write-up has to match |
| `repo\stages\p1-scrape\INTERFACE_CONTRACT.md` | The frozen seam. §2.2 is the manifest field set step 1A-6 bumps to 0.3.0, §4 is the `sources_<cc>.yaml` spec the new YAML header extends, §8 is the versioning rule that makes the bump MINOR |
| `repo\stages\p1-scrape\PLAN.md` | The Round 1 build plan, tasks T0 to T8. Not a finale plan, but it is where the adapter contract and the escalation ladder were argued out. Correct on the PDF library where the planning-folder copy is not |
| `repo\stages\p1-scrape\docs\CORPUS_VERSIONS.md` | The hand-kept ledger, v2.0 to v2.4. Every figure in the Current state table above reconciles here. The manifest carries no version field, so a new economy needs a v2.5 row written by hand |
| `repo\stages\p1-scrape\docs\P1_COMPLETION_REPORT_2026-07-12.md` | Dated at v2.0; Addenda 1 to 5 carry it forward to v2.4. Addendum 5 holds the `doc_id` table for the 33 supersessions, which is the worked example of the write-back step 1B-5 asks for |
| `repo\stages\p1-scrape\docs\AU_HTML_TRUNCATION_AUDIT_2026-07-17.md` | An audit wired to an acceptance chain. It defines the truncation detector that the re-fetch tool then re-runs per document, so a shortfall fails loudly. The shape an evidence artefact should have |
| `repo\stages\p1-scrape\docs\HANDOFF_AU_MULTIVOLUME_2026-07-17.md` | The note P1 sent P2 when 33 documents changed underneath it. Step 1B-6's changed-docs file is the machine-readable form of this note, so read it for what P2 actually needs told |
| `repo\stages\p1-scrape\reference\Sample_government_portals_Pillar6_7.csv` | The host's law-to-URL map that seeded all three existing YAML files. The precedent for how a new economy's seed list is sourced and cited |
| `repo\stages\p1-scrape\reference\Legal_Inventory_SG_MY_AU.csv` | The broader all-pillar inventory for the three existing economies. Useful as a shape, not as data, since the finale is twelve pillars |

### Reference, in the planning workspace

| Path | Why you open it for this task |
| :---- | :---- |
| `plan\2_What_We_Built\Reference\Stage_Plans\1_Scraping.md` | **Stale twice over.** The original stage plan, 44 KB. Same body as the in-repo `PLAN.md`, plus a status banner and a §11.1 risk-retirement table the repo copy lacks. The banner stops at corpus v2.3, quoting 2,673 documents and about 1.6 GB, where v2.4 is 2,706 rows and about 1.85 GB. Four lines still name PyMuPDF, which `pypdfium2` replaced on 2026-07-12 over the AGPL licence. The in-repo copy wins on the library |
| `plan\2_What_We_Built\Reference\Stage_Plans\WEB_RESEARCH_POLICY.md` | **Adopted 2026-07-16 and never applied.** The rule for the discovery half of a new economy. Search guides discovery, the official portal supplies the evidence, never the reverse. Round 1 deferred it deliberately, so the finale is its first real use. Read §1 before the first search for a Thai or Lao portal |
| `plan\2_What_We_Built\Reference\Stage_Plans\0_Interfaces_and_Contracts.md` | **One stale line apart from the in-repo copy.** The frozen spine every stage keys off. It is `repo\stages\p1-scrape\INTERFACE_CONTRACT.md` line for line, except that line 90 names PyMuPDF where the code imports `pypdfium2`. Open the in-repo copy. Use this one only to confirm the spine is the same document in both trees |
| `plan\2_What_We_Built\Reference\Stage_Plans\round1_plan\DISCLOSURES.md` | The honesty habit, worked through. No estimate presented as a measurement, every figure traced to where it is logged, a disclosed gap preferred to a hidden one. The model for how this task reports the delta run and the crawl hours |
| `plan\2_What_We_Built\Reference\Stage_Reports\p1\P1_README.md` | **Identical to `repo\stages\p1-scrape\README.md`** once line endings are normalised. Open the in-repo copy. This row exists so nobody spends an hour diffing the two looking for a difference |
| `plan\2_What_We_Built\Self_Assessment\03_Submission\briefs\STATION_1_P1_SCRAPE.md` | **Its path shorthand is dead.** How this stage was pitched to a judge, every claim tied to an artefact path, and the model for the evidence folder here. `P1\` expands to `C:\Users\woshi\Desktop\rdtii-p1-scrape\` and `J\` to `C:\Users\woshi\Desktop\RDTII Judge\`. Neither exists now. The stage lives in the one repo, the findings in `01_Findings\` |
| `plan\2_What_We_Built\Self_Assessment\01_Findings\LEAKAGE_AUDIT_2026-07-16.md` | The live test is sealed, so every path by which baseline answers could reach the model must stay closed. This audit traced P1's seed inventories among the rest and found no backward induction. Re-run its reasoning over any new economy's seed list before committing it |
| `plan\2_What_We_Built\Self_Assessment\01_Findings\SUBSTANTIVE_SPOTCHECK_MY_AU_2026-07-17.md` | The spot-check that caught the AU multi-volume truncation. Read it for how a silent retrieval defect actually surfaces, which is never from the crawler's own logs |
| `plan\2_What_We_Built\Self_Assessment\01_Findings\GROUND_TRUTH_2026-07-16.md` | Every Round 1 number with the artefact path that proves it, reconciled from artefacts and git history rather than from completion reports. The method AUTHORITATIVE_NUMBERS.md inherits |
| `plan\2_What_We_Built\Self_Assessment\01_Findings\2026-07-20_portal_readiness_check.md` | **The filename misleads.** "Portal" here is the submission portal, not a government one. It is a three-hours-to-deadline cross-check of every submitted claim against the live repo state. Read it once before 30 September as the list of things that break under time pressure |

The full `01_Findings\` directory holds 19 files. Three of the four above touch retrieval. The
readiness check earns its place for a different reason. The remaining fifteen are mapping,
extraction and scorecard audits owned by other tasks.

## The first thing to do

Start step 1A-1 in PLAN.md. Open the working copy
`countries\sg-singapore\sources.yaml` (the repo's `instrument\sources_sg.yaml`) and
extend the existing top-level `economy: SG` key into the header in `countries\_template\sources.yaml`:
code, name, matrix label, aliases, adapter, default language, script and smoke URLs. Do the same for
Malaysia and Australia, then hand all three back to both registry folders in one commit.

That header is the seed of the whole workstream. Every later step reads it.

**Do not re-tag the `indicators:` lists to decimal IDs in the same edit.** Added 2026-09-13.
`sources.indicator_pillar()` cannot parse `6.1`, so every seed filter drops every law and a seed crawl
fetches nothing while still exiting 0. The helpers change in the same commit as the tags. See
`notes/INSTRUMENT_IMPACT_2026-09-13.md` items A1 to A3.

## How this workshop is organised

Updated 2026-09-15, decisions 8, 11, 15 and 17.

| Path | What it is |
| :---- | :---- |
| `CONVENTIONS.md` | **The rulebook of the scraping tool:** what we scrape, the six-step mechanism (link list, crawl, audit, run note, update check, corpus), what it writes, the country folder and its `NOTES.md` layout, the rules that do not move, where each country stands |
| `POLICY.md` | What the crawler fetches, from where, and how politely. Every economy follows it |
| `CONTRACT.md` | What every economy hands to extraction: files, columns, formats, the conformance check. A draft of contract 0.3.0 |
| `countries/` | One folder per economy with the same layout (decision 11, `CONVENTIONS.md` section 4): `scraper/` with `WORKFLOW.md`, `updates/` with `WORKFLOW.md`, `sources.yaml` (destinations and settings), `links/` (`seed_laws.yaml`, plus, for Malaysia only today, the generated list of every document to crawl), `NOTES.md`, `tests/`. `_template/` is where a new economy starts. `countries/README.md` has the hand-back rules |
| `outputs/` | The runs and corpora, by country: `outputs/<CC>/<CC>_ws_<date>/` per run, `<CC>_corpus_<date>/` per corpus, each with its note (`outputs/README.md`) |
| `tools/` | The audit (`audit_run.py`: which stored files are not the law's text) and the corpus merge (`merge_corpus.py`), with their tests (`tools/README.md`) |
| `PLAN.md`, `DECISIONS.md` | The build steps and the choices behind them |
| `notes/` | Dated working notes that cover more than one economy, such as the instrument impact record and requests |
| `evidence/` | The artefacts that back claims others will check |
