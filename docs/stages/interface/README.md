# Task 4: the interface a stranger has to operate

This folder is the working record of the interface task: this file, `PLAN.md` and `DECISIONS.md`. The code
is in `interface/`, with its own engineering notes in `interface/README.md`.

**This file has two parts.** The first is the state on 5 October 2026. The second, from "As written on
12 September 2026" down, is the file as it stood at the start of the task and is kept as written: the
one-file dashboard it describes was replaced on 29 and 30 September and is no longer in the repository.

## What this task owns

Everything a user sees and touches. The button that starts a run. The progress in plain words. The screen
where a reviewer checks a quoted phrase against its source. The accept, reject and correct controls. The
choice of engine and model. The export.

## What this task does not own

The pipeline stages it drives. The interface starts each stage's own command line as a child process and
reads what the stages write to disk. It imports no stage code and writes nothing under `stages/`.
Crawler politeness, mapping quality, the instrument and the cost ledger belong to the stages. This task
shows them and must not compute them a second time.

One boundary is worth stating twice. The fourteen columns of an evidence row are written by the mapping
stage. This task reads them, applies the reviewer's decisions, and writes the exported file.

One thing changed on 4 October. On the post-finale branch, a fault the interface found in a stage has
been repaired in the stage, at the developer's word, where before it was only noted: the registries'
seed laws, the splitting patterns, the adapters' facts beside the manifest, the engines' declaration.
Each is in `docs/CHANGELOG_FINALE.md`, and the decisions are in `DECISIONS.md`.

## Where the code lives

| What | Path |
| :---- | :---- |
| The interface | `interface/app.py`, `interface/rdtii_ui/` (the server, the run layer, one module per page), `interface/static/` (the page) |
| Its own notes, beside it | `interface/README.md`, `interface/DATA_PATHS.md`, `interface/START_PROMPT_INTERFACE_2026-09-29.md` |
| The rows shown on a clean clone | `interface/fixtures/` |
| Tests | `interface/tests/`, 291, standard library only |
| Launchers | `Start-RDTII-Rocky.cmd`, `Start-RDTII-Rocky.command`, `start-rdtii-rocky.sh`, at the top of the repository |
| Code map | `docs/CODE_MAP.md` |
| Change log, one entry per change with how it was verified | `docs/CHANGELOG_FINALE.md` |
| The 14-column writer it must stay compatible with | `stages/p3-map/src/p3map/output/submission.py`, `COLUMNS` |
| The data contract mapping handed over | `docs/stage_results/UI_HANDOFF_p3-map_2026-09-29.md` |
| Progress reports | `docs/stage_results/` |

## Current state, 5 October 2026

A standard-library server and one page: an Overview, three stage pages (Scraping, Extraction, Mapping),
each with Set up, Run and Output, and an Appendix. 8,355 lines of Python outside the tests, 51 routes,
291 tests. It starts as a browser tab or, from the launchers, in a window of its own.

**What works today.** Code paths in this table are relative to `interface/`.

| Capability | Where on the page | Where in the code | Last tried |
| :---- | :---- | :---- | :---- |
| Start a run, Check first, progress in plain words, Stop | 1.2, 2.2 and 3.2 Run | `rdtii_ui/jobs.py`; `plan_scrape`, `plan_extract`, `plan_map` in `rdtii_ui/pages/` | 5 October, small runs of every stage from the page; a run stopped after 25 seconds left no process behind |
| The audit view: a row beside the text it came from, the original beside labelled machine English | Mapping → 3.3 Output → a run → a row | `rdtii_ui/pages/mapping.py`, `row_detail` | 5 October |
| Follow a row to its official source | the same view: Source, and the fold "Where the quote sits in the source text" | `rdtii_ui/pages/mapping.py` | 5 October |
| Accept, Reject, Correct, Clear decision, each appended to a log | the same view | `rdtii_ui/review.py`, `record_decision` | 5 October: each one, with an export after it |
| Export to the 14 columns, CSV and xlsx, IDs as text | Mapping → 3.3 Output | `rdtii_ui/review.py`, `export` | 5 October: the rejected row left the file, the corrected text was in it |
| A provider and a model for each model step | Mapping → 3.2 Run, steps B to E; keys under Engine API keys | `rdtii_ui/envbuild.py`; the stage's `engines.json` | 5 October on local Qwen in all four steps; 4 October with a different engine per step, on a test engine. No hosted model has been called from the page since this was built |
| A number per indicator for candidate selection | Mapping → 3.2 Run, step A | `rdtii_ui/pages/mapping.py`, `selection_with` | 4 October |
| Hand-collected files, any of the six economies, no source asked | Scraping → 1.3 | `rdtii_ui/pages/inbox.py`, `rdtii_ui/readiness.py` | 5 October |
| A table of runs in every Output: began, last run, complete or not | 1.4, 2.3, 3.3 | `run_state` in `rdtii_ui/pages/scrape.py` and `rdtii_ui/pages/mapping.py`, `output_state` in `rdtii_ui/pages/extract.py` | 5 October |
| Clear a run folder or a cache, with a preview and a confirmation | every Output | `rdtii_ui/fsguard.py` | 5 October |
| A window of its own, one instance, closing it stops the tool | the launchers, or `--window` | `rdtii_ui/shell.py`, `rdtii_ui/lifecycle.py` | 3 October on Windows 11. Not opened on a Mac |
| Which Python runs each stage, set from the page | Appendix → This machine | `rdtii_ui/machine.py` | 4 October |
| The cost report and its calculator; estimated performance by model | Overview, sections 3 and 4 | `static/index.html`, the block `#cost-data`; `tests/test_cost_report.py` | 5 October, in a browser |

**What does not exist.** Said plainly, because the host marks honesty.

1. **No comparison of two engines' runs.** A pass on each engine is a run with its own export. The host's
   workbook has sheets named Engine Comparison and Run Record; the tool fills neither.
2. **The export is a workbook of its own**, one sheet with the 14 columns. Filling the host's template,
   with its formulas, is a step of the mapping stage (`stages/p3-map/src/p3map/output/template.py`) that is
   run by hand, not from the page.
3. **No hosted model has been called from the page since the rework of 4 and 5 October.** The requests
   for DeepSeek, Kimi and ChatGPT are tested against a stand-in for the network only.
4. **No second machine.** The thirty-minute deployment has been rehearsed on the development machine
   only, and no window has been opened on a Mac. The interface's tests passed on Windows, macOS and
   Ubuntu in the repository's workflow on 4 October.
5. **A stopped run** reads "stopped" only while the interface that stopped it is open; after a restart it
   reads "not complete". Stop writes nothing into the run folder.
6. **The calculator** prices the careful reading as a live call. The finale read in the batch lane at half
   the price; the page has no batch option.
7. **Old Word `.doc` files** are not converted. The page says to save them as `.docx`.
8. **A working folder outside the clone** (a project a person opens and comes back to) was planned on
   3 October and deferred.

## What the host asks of this task, and where each stands

The requirements were read line by line from the host's templates on 12 September; that reading is in the
second part of this file. Where each stands today:

| Requirement | Today |
| :---- | :---- |
| Set the economy and the indicators in the interface (live test, step 1) | Mapping → 3.1 Set up: the economies of the chosen extraction output, and any of the 61 indicators. Six economies are built; of the nine 2025-database economies, China and Lao PDR have been run |
| The README names a screen and a control for six actions | `README.md`, "Your Interface", rewritten on 5 October |
| One command starts the interface, and the command line is not needed again | a launcher, or `python interface/app.py`; no `.env` to edit |
| Progress in plain words; review and export in the interface | built, above |
| The engine is switched inside the interface, with no file edited and no command typed | Provider and Model in steps B to E of Mapping → 3.2 Run |
| Caches and downloaded documents can be cleared on screen | Clear in every Output; only under the runs root |
| Export into the host's workbook | not in the interface: item 2 above |
| Run Record and Engine Comparison sheets | not built: item 1 above |
| A walkthrough recording | `walkthrough_RockyHasAHomeRun_Oct05_5min.mp4`, recorded on 5 October, submitted with the Word document |
| The interface can be left available for the marking period | the address and the port are settings; not rehearsed on another machine |

## Rubric criteria this task carries

| Criterion | Points | What the marker checks |
| :---- | ----: | :---- |
| C3a audit mode, human in the loop | 10 | A policy officer checks the source unaided and records a verdict |
| C3b UI/UX and export | 5 | Operable without training, exports to the RDTII schema |
| C4a technical handover, interface share | part of 8 | A stranger reaches a working interface from the repository's documents in 30 minutes |
| C5b engine swap, live test | 4 of 10 | The switch happens inside the interface, no file edited, no command typed |

Nothing here may add an installation step. A failed install on a clean machine costs more than good
styling earns, which is why the interface is still standard library only.

## The rest of the record

- `DECISIONS.md`: the choices of this task and the reason for each, in order of time, with what became of
  the proposals of 12 September.
- `PLAN.md`: the plan of 12 September for the one-file dashboard. Superseded by the rebuild; kept as
  written. The plan the rebuild followed is `interface/START_PROMPT_INTERFACE_2026-09-29.md`.
- `docs/CHANGELOG_FINALE.md`: every change since, with how it was verified.
- `docs/stage_results/PROGRESS_interface_2026-10-05.md`: the progress report of 5 October.

---

# As written on 12 September 2026 (kept as written)

The paths below are the author's working paths of that month, and `interface\dashboard.py`, `interface\PLAN.md`,
`interface\CLAUDE.md` and `interface\MIGRATION_NOTE.md` are no longer in the repository.

This folder is a workshop. The code lives in the repo. Nothing here is source, and nothing here
is a second copy of the repo's engineering docs.

## What this task owns

Everything a user sees and touches. The button that starts a run. The progress stream. The screen
where a reviewer checks a quoted phrase against its source. The accept, reject and correct
controls. The engine switch. The export.

## What this task does not own

The pipeline stages it drives. The interface runs `main.py` as a subprocess and reads what the
stages write to disk. It never imports stage code and never edits stage files. Crawler politeness,
mapping quality, the twelve-pillar instrument and the cost ledger belong to other tasks. This task
surfaces them and must not silently re-compute them.

One boundary is worth stating twice. The evidence workbook's fourteen columns are written by the
mapping stage. This task consumes that output, applies reviewer decisions to it, and writes the
file the judges receive.

## Where the code lives

| What | Path |
| :---- | :---- |
| The interface, one file | `C:\Users\woshi\Desktop\rdtii-rocky-finale\interface\dashboard.py` |
| Its own docs, in the repo beside it | `interface\README.md`, `interface\PLAN.md`, `interface\CLAUDE.md`, `interface\MIGRATION_NOTE.md` |
| Repo code map | `C:\Users\woshi\Desktop\rdtii-rocky-finale\docs\CODE_MAP.md` |
| Code change log | `C:\Users\woshi\Desktop\rdtii-rocky-finale\docs\CHANGELOG_FINALE.md` |
| The 13-column writer it must stay compatible with | `stages\p3-map\src\p3map\output\submission.py`, `COLUMNS` at line 35 |
| Per-step workflow documents the Workflow tab renders | `stages\p3-map\workflow\steps\`, 13 files present |

`interface\CLAUDE.md`, `interface\PLAN.md` and `interface\README.md` still describe the Round 1
world. They name `C:\Users\woshi\Desktop\rdtii_rocky_7.20` as the pipeline repo and a separate
`rdtii-dashboard` repo as the home of the code. Both statements are now false. Neither folder is on
the Desktop any more. Both were archived, and every path into them is dead.
`interface\MIGRATION_NOTE.md` records the move and is the accurate one. Correcting the three stale
files is a step in `PLAN.md`.

## New from the host templates, read line by line on 2026-09-12

Full detail is in `C:\Users\woshi\Desktop\RDTII Finale Plan\3_Final_Stage\REQUIREMENTS.md`.

### Three things that change the build

**1. Export into the host's workbook, do not generate a new one.** The host template is not just
fourteen columns. Column O of the Output Data sheet carries a Pillar formula, and the Coverage Matrix
counts provisions per economy and pillar by reading it. The secretariat validates against the
template. A freshly generated workbook, however correct its columns, loses the matrix and the
formulas. Write rows into a copy of `OUTPUT_TEMPLATE_FINAL_ROUND.xlsx` instead. `PLAN.md` step D6 is
revised accordingly.

**2. The template has defects the writer must handle.** Verified cell by cell:

| Defect | Effect | Working answer until question 7 is answered |
| :---- | :---- | :---- |
| The Coverage Matrix has **no Russian Federation row** | Russian provisions are counted nowhere | Add a row by copying an existing row's formulas. Declare it |
| The matrix labels Lao **"Lao PDR"**, but the field rule demands the UN name "Lao People's Democratic Republic" | Following the field rule makes Lao count zero | Write the label the matrix counts. Put the full UN name in Notes |
| Data rows stop at **row 109**, room for 101 provisions | Round 1 alone filed 142 | Extend the formula range if needed. Never truncate silently |
| Example rows 7 and 8 must be **removed** before submitting | Easy to forget | The writer removes them |

**3. Caches must be clearable on screen.** Checklist item 26: "Cache and downloaded-document folders
can be cleared on screen before the clock starts." The Run Record sheet adds that C5a scores zero if
no documents are fetched during the hour. So the interface needs a visible clear control, and it must
clear the crawler's document index too, or the next run skips every law and fetches nothing.

### Everything else that binds this task

| Requirement | Source | Consequence |
| :---- | :---- | :---- |
| **Walkthrough: about four minutes, five beats**, including follow a row to its official source at the cited article, and reject a row, export, and show the correction took effect | Word Section 6, workbook Instructions, checklist 19, README template | Revised in `DECISIONS.md`. The recording is also the fallback if deployment fails |
| **Live test step 1: set the economy and indicators in the interface** | Orientation slide 9, workbook Instructions | The run screen must pick one of nine economies, a pillar and two indicator IDs, not only a Round 1 slice variant |
| **The README names a screen and control for six actions**: start a run, audit view, follow to source, accept or reject or correct, switch engine, export | README template, "Your Interface" | Names must be final by 30 September. Section 5 of the Word template also asks for the switch's screen and control name, and cannot be corrected afterwards |
| **One command starts the interface**, from a root `requirements.txt` and `.env.example`, and a reviewer never needs the command line again | README template, Quick Start | Today there is no root `requirements.txt` and no root `.env.example`. The C4a path starts here |
| **Progress in plain words; review and export happen in the interface** | Checklist item 24 | The progress text is marked, not decorative |
| **Run Record and Engine Comparison sheets** in the host's shape, including the strings `Engine A only`, `Engine B only`, `Both` | Workbook | The mapping folder builds the data. This task exports it into the template's two morning sheets |
| **The interface can be left available for the marking period** | Checklist item 29 | Question 9 asks what this means. Until answered, the deployed-from-repo instance is the answer |
| **Judges may ask you to run the tool live on a case they choose, with no time to rerun** | Pitching rules from 3 August, the only precedent | The 13:00 station and the 14:00 defence both need a run that starts cleanly on any economy, not a rehearsed path |

## Borrow from Round 1

Round 1 left more usable material for this task than for any of the other four. Point at it. Nothing
below gets copied into this folder, because one source of truth is worth more than a convenient
duplicate. Every path here was checked on 2026-09-12 and exists.

Repo paths are relative to `C:\Users\woshi\Desktop\rdtii-rocky-finale\`. Planning paths are relative
to `C:\Users\woshi\Desktop\RDTII Finale Plan\`.

### Reusable templates, worth more than the reference rows below

| Path | Why you would open it |
| :---- | :---- |
| `2_What_We_Built\Self_Assessment\03_Submission\briefs\` | Four station briefs in the finale's own format: `STATION_0_P0_INSTRUMENT.md`, `STATION_1_P1_SCRAPE.md`, `STATION_2_P2_EXTRACT.md`, `STATION_3_P3_MAP.md`. Copy the four-section shape for D12, which is what this stage does, the numbers that matter, how it was verified, known limitations |
| `2_What_We_Built\Filed_FROZEN\audit\` | `index_SG.html`, `index_MY.html`, `index_AU.html`. The audit view a reviewer gets today, quote to locator to source URL, offline and self-contained. This is the read-only baseline the D2 review screen has to beat |
| `2_What_We_Built\Filed_FROZEN\` | What a reviewer currently receives: `records_{SG,MY,AU}.csv` in the thirteen host columns, and `RDTII_P3_results_{SG,MY,AU}.xlsx` with every fired verdict, kept and rejected, grouped per indicator. That workbook is the closest thing Round 1 has to a review surface. D6 extends its shape to fourteen columns |
| `2_What_We_Built\Filed_FROZEN\README.md` | The per-file note that ships beside those records. Reuse its wording for the export's own README so the judges' file explains itself |
| `2_What_We_Built\Self_Assessment\03_Submission\drafts\VIDEO_SCRIPT.md` | A shot list that got made, with narration word count, per-beat timings and a named non-negotiable beat. Re-point the beats at the interface for D11 |
| `2_What_We_Built\Self_Assessment\03_Submission\RECORDING_SETUP_2026-07-20.md` | The pre-flight check that verified the script's claims against the machine and found blockers the script missed. Re-run its shape before the D11 take |
| `2_What_We_Built\Self_Assessment\03_Submission\drafts\WORKFLOW_DIAGRAMS.md` | Mermaid sources for the pipeline map, already written in plain problem-language with the jargon demoted. Reuse the wording in the Workflow tab and the recording opener |
| `2_What_We_Built\Filed_FROZEN\README_round1_repo.md` | The filed Round 1 repo README. Borrow the Quick Start shape for D9, not its content. Its text is identical to the finale repo README today, line endings aside, and that is the README which never mentions the interface |

### Reference, background you read once

| Path | Why you would open it |
| :---- | :---- |
| `interface\MIGRATION_NOTE.md` | The accurate record of what moved into this repo on 2026-09-10, what was left behind, and what the code already does against the finale rubric. Read it before trusting the other three interface documents |
| `interface\README.md` | Usage and the version history to v3.16. Stale. It is titled `rdtii-dashboard` and its run command points into the archived `rdtii_rocky_7.20\.venv\`. D10 corrects it |
| `interface\PLAN.md` | The 2026-07-20 architecture and screens plan, and the reasoning behind the six tabs the page still has. Stale. Its location amendment puts the code in a separate `rdtii-dashboard` repo. D10 corrects it |
| `interface\CLAUDE.md` | Project rules, including the four-layer judged-versus-demo firewall the D2 review screen must not break. Stale. Every path in its source map points into `rdtii_rocky_7.20`. D10 corrects it |
| `2_What_We_Built\Self_Assessment\03_Submission\DASHBOARD_SPEC_2026-07-19.md` | The written spec for the Round 1 static explorer. It names the host's own judge loop, which is filter Discovery Tag NEW, read the rationale, check the snippet against the source URL. D2 turns that loop into a recorded verdict. It also argues the no-CDN, no-server, no-install case this task is still making |
| `2_What_We_Built\Self_Assessment\03_Submission\MINIRUN_SPEC_2026-07-19.md` | How the offline five-law mini-run is wired, and the exact disclosure lines it stamps on its outputs. D8 launches that run from the first-click button, so read the disclosures before rewording them |
| `2_What_We_Built\Reference\Stage_Plans\0_Interfaces_and_Contracts.md` | The frozen spine every stage keys off. It is the authority for the boundary this README states twice, that stages hand off through files on disk and no sub-project imports another |
| `2_What_We_Built\Reference\Stage_Plans\round1_plan\DISCLOSURES.md` | The honesty habit to carry forward. No estimate is presented as a measurement and every figure traces to evidence. Apply it to the D5 cost cells that may have no number to show |
| `2_What_We_Built\Self_Assessment\01_Findings\LEAKAGE_AUDIT_2026-07-16.md` | The backward-induction check, and the audit that matters most here. The live test is sealed, so every path by which baseline answers could reach the model must stay closed. D2 puts a human in the loop who can see baseline material, so re-run its reasoning against the review screen. The same folder holds the mapping, corpus and scorecard audits |

## Rubric criteria this task carries

| Criterion | Points | What the marker actually checks |
| :---- | ----: | :---- |
| C3a audit mode, human in the loop | 10 | A policy officer checks the source unaided and records a verdict |
| C3b UI/UX and export | 5 | Operable without training, exports to the RDTII schema |
| C4a technical handover, interface share | part of 8 | A stranger reaches a working interface from the repo docs in 30 minutes |
| C5b engine swap, live test | 4 of 10 | The switch happens inside the interface, no file edited, no command typed |

That is nineteen points directly, plus a share of eight. The judges carry fifty marks of the total
and meet the tool through this interface in a private hands-on trial at 13:00 on 15 October.
Correct output presented badly loses points that correct output presented well would keep.

The counterweight is absolute. Nothing here may add an installation step. C4a is worth eight points
on its own and a failed install on a clean machine costs far more than good styling earns.

## Current state, verified by reading the code on 2026-09-12

The file is further along than a listing suggests. It is 8,676 lines, Python standard library only,
serving `127.0.0.1:8765` from `ThreadingHTTPServer`. A reviewer installs nothing to run it.

**What works today.**

| Capability | Where it lives in `dashboard.py` |
| :---- | :---- |
| Launch a run from the page, validated server side | `validate_launch_spec()` :893, `build_cmd()` :962, `enqueue_run()` :1003 |
| Serial single-run queue with a live progress stream | `run_worker_loop()` :1056, server-sent events from `Handler._serve_events` |
| Settings reach the subprocess as environment only | `build_child_env()` :977 |
| Model and provider choice gated server side | `MODEL_ENV_ALLOWLIST` :886, eight variables, three presets |
| Open-weights lane probed before launch | `probe_ollama()` :3415 |
| Source-to-verdict trace for one document | `svc_trace()` :1736 |
| Byte-grounding proof with surrounding context | `svc_source_slice()` :2619, returns `before`, `span`, `after` and the character offsets |
| Static single-file export | `do_export()` :8568 over `build_boot_data()` :8510 |
| Six tabs | `NAV` :4639, Workflow, Instrument, Run, Database, History and Cost, Guide |

**What does not exist.** Say this plainly, because the host marks honesty up.

1. **No human accept, reject or correct.** Review today is three read-only things. The model's own
   trail, shown but not editable. An Excel reviewer workbook written by the mapping stage. A one-way
   promote gate, `svc_db_promote()` :1311, which appends a whole run to a working CSV and refuses to
   do it twice. There is no per-finding verdict, no reviewer identity, no correction, and nothing a
   decision could flow into. C3a is ten points for exactly the thing that is missing.
2. **No named two-engine control.** The presets are `judged`, `keyless` and `custom`. Custom exposes
   eight individual environment variables. A steward watching a text field being filled in is not
   watching an engine switch.
3. **No engine provenance on rows.** Nothing in the output says which engine produced which finding.
   The comparison hand-in on 15 October requires exactly that.
4. **No fourteen-column export.** The interface exports a static HTML page. The evidence file the
   judges receive has fourteen columns and indicator IDs as decimal text.
5. **The repo README never mentions the interface.** Its Quick Start still clones
   `rdtii_rocky_7.20` and says the repository is private. A stranger following the repository
   documentation today does not reach the interface at all. That is the C4a failure mode.

**Fixed today, 2026-09-12.** `DEFAULT_REPO` at :60 now resolves to the file's own parent of parent,
so a clean clone drives the right checkout. The 13 per-step workflow documents were copied into
`stages\p3-map\workflow\steps\`, so the Workflow tab renders on a clean clone. Both entries are in
`docs\CHANGELOG_FINALE.md`.

**One thing a clean clone will surprise you with.** `outputs/` is in `.gitignore` and absent from
the repo. A stranger's first view of the interface has zero runs and every run-scoped panel is
empty. The offline mini-run over `demo_data\mini_raw\` is the only way to fill it without network
or a key. Design the empty state for that, do not hope nobody sees it.

## The first thing to do

Build the review record before building the review screen. Decide the shape of one decision, decide
where it is stored, and write the POST route that accepts it. Everything else in this task,
including the export and the engine comparison, hangs off that record.

Concretely, tomorrow morning. Add a `decisions` store inside the runtime `interface\db\` directory.
Add `POST /api/decisions` next to the existing `/api/db/promote` at `dashboard.py` :3673. Make
`svc_records()` :1199 join the decision onto the row it belongs to. The screen can be ugly on day
one. The record cannot be wrong, because the export reads it and the judges read the export.

A note on that directory. `interface\db\` is not in the repo. It is listed in `.gitignore` and
`dashboard.py` creates it on first write, at `DB_DIR.mkdir()` :1342. Do not expect to find it in a
clean clone or on disk today.
