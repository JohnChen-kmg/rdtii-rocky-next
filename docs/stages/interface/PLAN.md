# Plan: Dashboard

Written 2026-09-12. Eighteen days to the 30 September freeze. Steps are ordered by the order they
should be built, not by size. Every step names the file it touches.

Proposals are marked **Proposed**. Everything unmarked is already settled by the brief or by the
code as it stands.

## Budget

| | Hours |
| :---- | ----: |
| Steps D1 to D7, the freeze minimum | 44 |
| Steps D8 to D13, handover and the day itself | 26 |
| D14, polish | 4 |
| **Total** | **74** |

Seventy-four hours over eighteen days is roughly four hours a day on this task alone. That is more
than one person has while four other workstreams run. The cut list at the bottom is not decoration.
Read it on 24 September and act on it.

### Changed by the host templates, read 2026-09-12

| Change | Hours | Freeze minimum |
| :---- | ----: | :---- |
| D6 writes into a copy of the host template instead of a new workbook, and handles its defects | +3 | Yes |
| **New D15, clear caches on screen.** One visible control, confirmed before it acts, that clears downloaded documents, the crawl index and extraction caches. Calls the functions the scraping and extraction folders expose | 2 | Yes, checklist item 26 |
| **New D16, live-test run setup.** Pick an economy, a pillar and two indicator IDs, then press start. Replaces the Round 1 slice-variant picker. Under the scope decision the pickers list the six covered economies and pillars 6 and 7. Unsupported choices are shown greyed with the reason, never hidden | 4 | Yes, live test step 1 |
| **New D17, the two morning sheets.** Export the Run Record and Engine Comparison into the template's own sheets, with the exact found-by strings | 3 | Yes, C5 |
| D11 walkthrough cut to about four minutes, five beats | 0 | Yes |

Revised total: 86 hours. This folder is now the largest single load on the desk. The
cross-folder cut decision the reviewers asked for on 2026-09-12 is more urgent, not less.

---

## D1. The decision record, 4 h

Build the record before the screen. The export reads it, the judges read the export, so its shape is
the only thing here that is expensive to change later.

**Touches.** `interface\dashboard.py` near `svc_db_promote()` :1311 for the store, and the route
table inside `Handler.do_POST` :3637 for the route.

**Proposed shape.** One append-only JSONL file at `interface\db\decisions.jsonl`, gitignored like
the rest of `interface\db\`. That directory is not in the repo. `.gitignore` lists `interface/db/`
and `dashboard.py` creates it on first write at `DB_DIR.mkdir()` :1342, so a clean clone has no such
folder until a run writes one. One line per decision. Lines are never rewritten. The latest line for
a finding key wins, and the earlier lines stay as the audit trail. This mirrors `promote_log.jsonl`,
which already works this way, so the reader helper `_promote_log_entries()` :1275 is the template.

**Proposed finding key.** `run_id` plus `economy` plus `provision_id` plus `indicator`. The
provision ID already carries the document and the article, in the form `au-pa1988-001#s.26WE(1)`,
and `svc_trace()` :1736 already splits on `#`. Nothing new has to be invented upstream.

**Proposed fields per line.**

| Field | Value |
| :---- | :---- |
| `decided_at` | Timestamp |
| `reviewer` | The name typed for this browser session |
| `run_id`, `economy`, `provision_id`, `indicator` | The finding key |
| `verdict` | `accept`, `reject` or `correct` |
| `reason` | Required on a rejection |
| `corrections` | Field-to-value map |
| `prior` | The values the correction replaced |

**Proposed reviewer identity.** A name typed once per browser session and held in memory, stamped
onto every decision. No login, no accounts, no database. A judge trying the tool types "Judge 3" and
their verdicts are attributable. Anything heavier adds a dependency or a migration.

**Done when.** `POST /api/decisions` accepts a decision, rejects a malformed one with a specific
message, and `GET /api/decisions?run=<id>` returns the current verdict for every finding in a run.

## D2. The review screen that C3a is marked on, 12 h

This is the ten-point screen. A policy officer has to agree or disagree in seconds, without reading
code, without reading JSON, and without opening a file browser.

**Touches.** `interface\dashboard.py`, a new route in `Handler.do_GET` :3553 and a new view in
`PAGE_TEMPLATE` :3768, added as a seventh entry in `NAV` :4639 named **Review**.

**Proposed layout, one finding per card, nothing below the fold that matters.**

| Zone | Content | Where the data already comes from |
| :---- | :---- | :---- |
| Header | Economy, law name, article or section, indicator ID as decimal text | `mini_records_<ECON>.csv`, read by `_parse_records_csv()` :1156 |
| Quote | The verbatim snippet, the matched span marked inside its surrounding text | `svc_source_slice()` :2619, which returns `before`, `span`, `after` |
| Citation | Source URL as a live link, access date, SHA-256 of the retrieved bytes | the manifest branch of `svc_trace()` :1736 |
| Why | The model's one-line rationale, and the blind verifier's agreement or overturn | the map and verify branch of `svc_trace()` |
| Verdict | Accept, Reject, Correct, plus the running count | new, D1 |

**Proposed interaction.** Three buttons and three keys. `A` accepts, `R` rejects, `C` corrects,
`J` and `K` move through the queue. A reviewer who never touches the keyboard is not penalised, and
one who learns three keys clears fifty rows in ten minutes.

**Proposed reject flow.** A reject demands a reason chosen from a short fixed list, with a free-text
box for anything else. Proposed list: wrong indicator, quote not in the source, citation wrong,
provision not in force, out of scope. A rejection without a reason is worth nothing on 15 October,
because the comparison file has to say how the engines differed.

**Proposed correct flow.** Only five fields are editable, and each opens with the current value:
Indicator ID, Article / Section, Verbatim Snippet, Discovery Tag, Notes. Indicator ID is validated
against the codebook helper `stages\p0-instrument\scripts\indicator_ids.py` and refused if it is not
a known decimal-text ID. Every other column stays as the pipeline wrote it, so a corrected row is
still traceable to its run.

**Rules this screen must not break.** No file path is shown in the main flow, only as a footnote
link. No JSON is rendered. The judged Round 1 rows and the demonstration-run rows stay separated,
which is the four-layer firewall described in `interface\CLAUDE.md`. Review applies to run output,
never to the frozen `submission\` records.

**Done when.** A person who has never seen the tool opens Review and reads one finding. They check
the quote against the source URL in another tab. They record a verdict. No instruction beyond the
page itself.

## D3. Decisions reach the export, 6 h

A decision that does not change the exported file scores nothing.

**Touches.** `interface\dashboard.py`, `svc_records()` :1199 to join decisions onto rows, and the
new export writer from D6.

**Proposed rule for the evidence file.** Rejected rows are removed. Corrected values are substituted
in place, so the file still has exactly the host's fourteen columns and nothing extra. Accepted rows
pass through unchanged.

**Proposed rule for the audit trail.** A second file, `review_log.csv`, is written beside the
evidence file in the same export action. It carries every decision, including the rejections that
were removed, with reviewer, timestamp, reason and the replaced values. This is the honest answer to
"the workbook has fourteen columns and reviewer decisions need more than fourteen columns". The
schema stays clean and the trail stays complete.

**Done when.** Reject three findings, correct one, export, and the evidence file has three fewer
rows and one changed cell, while `review_log.csv` has four lines.

## D4. The named engine control, 6 h

Four points of C5 and a steward standing behind the laptop.

**Touches.** `interface\dashboard.py`, `PRESETS` :890, `MODEL_ENV_ALLOWLIST` :886,
`validate_launch_spec()` :893, `build_child_env()` :977, and the launcher panel in `PAGE_TEMPLATE`.

**Proposed design.** Add two named presets, `engine_a` and `engine_b`, beside the existing three.
Each is a frozen dictionary in the code that sets the allowlisted variables for that engine. The UI
shows one control with two options and a plain-language label for each, for example "Engine A,
Claude, hosted" and "Engine B, Qwen 2.5 14B, open weights, local". The eight raw variables stay
available under `custom`, hidden behind a collapsed section so a curious reviewer can see them but
nobody has to type one.

**Why a preset and not a text field.** The steward has to see an engine change happen. A radio pair
is unambiguous. A field that accepts `qwen2.5:14b` is a command typed into a box, and that is the
reading of C5b that loses the four points.

**Proposed frozen pairing.** Engine A is the hosted Claude stack that produced the Round 1 records.
Engine B is `qwen2.5:14b` served locally by Ollama. `probe_ollama()` :3415 already checks it, and it
is already evidenced. Citations, offsets and metadata were byte-identical across `qwen2.5:14b`,
`llama3.1:8b` and Claude Haiku 4.5 on 309 of 309 provisions. Open weights on one side is mandatory.
Two models from one vendor do not count. The declaration freezes in the Word submission on
30 September. Agree this pair with the engines workstream before then, not on the day.

**Done when.** Switching from A to B and starting a second run takes two clicks. No file is edited
and no command is typed. The header names the engine the current run is using.

## D5. Engine provenance on rows, and the comparison export, 7 h

**Touches.** `interface\dashboard.py`, the run sidecar writer inside `run_worker_loop()` :1056 so
each run records its engine preset, and a new comparison view and export.

**Proposed rule.** The engine name is recorded once per run, in the run sidecar, not per row. Rows
inherit their run's engine. This costs nothing upstream and needs no change to the mapping stage.

**Proposed comparison export.** One row per provision that either engine produced.

| Column | Content |
| :---- | :---- |
| Found by | Which engine produced the provision, or both |
| Indicator | The indicator each engine assigned |
| Citation | The citation each engine gave |
| Quote match | Whether the quoted words matched |
| Elapsed | Wall time per engine, from the run record |
| Cost | Cost per engine, from the run record |

Cost and elapsed time come from the run record, never from arithmetic done in the page. If the
unified cost ledger is not ready, the cell reads "not recorded by this run" rather than a number.

**Dependency to flag now.** The cost per run and per engine is produced by the cost-ledger
workstream. This task displays it and exports it. If that ledger does not land, this export ships
with an honest blank, and the live-test hand-in is weaker. Raise it in the weekly check, do not
absorb it silently.

**Done when.** Two runs over the same documents, one per engine, produce a comparison file that
covers every provision either engine produced.

## D6. The fourteen-column export writer, 6 h

**Touches.** `interface\dashboard.py`, a new writer beside `do_export()` :8568, and the existing
xlsx reading helpers at `_xlsx_preview()` :2980 which prove the approach.

**The column set.** Thirteen columns are already fixed by
`stages\p3-map\src\p3map\output\submission.py`, `COLUMNS` :35. They were verified against
`submission\records_SG.csv`.

| # | Column | # | Column |
| ----: | :---- | ----: | :---- |
| 1 | Economy | 8 | Location Reference |
| 2 | Law Name | 9 | Verbatim Snippet |
| 3 | Law Number / Ref | 10 | Mapping Rationale |
| 4 | Last Amended | 11 | Source URL |
| 5 | Indicator ID | 12 | Confidence |
| 6 | Article / Section | 13 | Notes |
| 7 | Discovery Tag | 14 | Language of Source |

The fourteenth is the language of the source. The stage owns writing it. This task must not invent
it here, or the interface and the pipeline will disagree.

**Proposed format, and this is the recommendation.** Write `.xlsx` directly with `zipfile` and
hand-built sheet XML, every cell an inline string. Standard library only, no dependency, and every
value is typed as text by construction. That is the one design that cannot let `12.10` collapse to
`12.1` or `4.01` to `4.1`. A CSV cannot promise it, because Excel coerces on open regardless of how
the file was written. The file is about 120 lines and the reading half of the same format already
exists in this file.

**Also export CSV.** Same data, UTF-8 with a byte-order mark, for anyone who wants to diff it.

**Done when.** The exported workbook opens in Excel with `12.10` still reading `12.10`, and its
column headers match the first fourteen headers on row 4 of
`C:\Users\woshi\Desktop\RDTII Finale Plan\1_Rules\Final_Round\OUTPUT_TEMPLATE_FINAL_ROUND.xlsx`
exactly.

**One detail about that template.** Row 4 carries fifteen headers, not fourteen. The fifteenth is
the `Pillar` column in column O, marked `AUTO` on row 3. The template's own note says it is a
formula that reads the Indicator ID, that nobody should type in it, and that nobody should delete
it. So write the fourteen authored columns and leave column O untouched. Do not treat "fourteen
columns" as "the sheet has fourteen columns", or the export will overwrite the host's formula.

**Revised 2026-09-12 after reading every sheet of the template.** Generating a fresh workbook with
`zipfile` loses the Coverage Matrix, the Pillar formulas and the two morning sheets, and the
secretariat validates against the template. So the writer must **copy the host template and write
rows into Output Data from row 9**, still as inline strings, leaving every formula intact. That is
harder with the standard library, because it means editing the template's existing sheet XML rather
than building new XML. Add about 3 hours. The writer must also:

- remove example rows 7 and 8;
- write the Coverage Matrix label for Lao, "Lao PDR", and put the UN name in Notes;
- add a Russian Federation row to the Coverage Matrix, which the template lacks;
- extend the formula range past row 109 if more than 101 provisions are exported, and never truncate
  silently.

Question 7 in `OPEN_QUESTIONS_FOR_HOST.md` covers the last three. D6 is now about 9 hours.

## D7. The second pass reads zero, 3 h

The host has said more than once that the second pass must fetch nothing and its document count must
read zero. The short note has a field pre-filled "must be 0".

**Touches.** `interface\dashboard.py`, the run progress view `renderRunProgress()` :6893, and the
run detail service `svc_run_detail()` :2426.

**What this task owns.** The number on the screen. A prominent counter reading **Documents fetched:
0** on the second pass, taken from the run's own crawl log rather than from a flag the page sets.

**What this task does not own.** The behaviour that makes it zero. That is the crawler and the
re-run path. If a second pass fetches one document, this screen must show `1`. Never make the
display lie to protect the claim.

**Done when.** A re-run over already-downloaded documents shows a zero fetched count read from the
artifact, and a run that did fetch shows the true number.

## D8. The first-run experience on a clean clone, 5 h

A stranger's first view has no runs at all. `outputs/` is gitignored and absent, so every run-scoped
panel is empty until something is launched.

**Touches.** `interface\dashboard.py`, the empty-state branches in the Run and History views, and
the landing tab.

**Proposed design.** The Run tab opens with one obvious primary button that launches the offline
mini-run over `demo_data\mini_raw\`. No key, no network, no options to understand. Every empty panel
says what will fill it and which button fills it. The judges' trial lasts thirty minutes for five
tools, so the first click has to be the right one without a briefing.

**Done when.** A clean clone plus one click produces a finished run with reviewable findings.

## D9. Repository documentation and the thirty-minute rehearsal, 6 h

**The gap, stated plainly.** `C:\Users\woshi\Desktop\rdtii-rocky-finale\README.md` does not mention
the interface anywhere. Its Quick Start clones `rdtii_rocky_7.20` and states that the repository is
private. A stranger following the repository documentation today never reaches the interface. This
is the C4a failure mode and it is a documentation bug, not a code bug.

**Touches.** `rdtii-rocky-finale\README.md`, and `interface\README.md` for the detail behind it.

**Proposed content.** One section in the repo README titled "Run the interface", four commands at
most, ending at `http://127.0.0.1:8765`. State the Python version. State that nothing is installed
for the interface itself. State what works with no key and no network, which is the offline
mini-run, and what needs a key.

**Proposed rehearsal.** Timed, on a machine that has never held this project, by someone who did not
build it. Start the clock at the repository URL and stop it at a finished mini-run on screen. Record
the time, the Python version, and every place the reader hesitated. Two rehearsals: one about
22 September to find the gaps, one after the fixes to prove the time.

**Who.** This is the weakest link in the plan and it needs naming now. Nobody has been identified.
**Proposed:** ask the KMITL contact or one non-technical acquaintance to sit the first rehearsal. If
no person can be found by 20 September, run it inside a fresh Windows user account with the project
folder inaccessible. Say in the submission that it was self-administered. A self-administered
rehearsal honestly described beats a claim of thirty minutes with nothing behind it.

**Done when.** A written record exists in `evidence\` giving the measured minutes and the tester.

## D10. Correct the stale interface documents, 2 h

**Touches.** `interface\CLAUDE.md`, `interface\PLAN.md` and `interface\README.md`.

| File | What is false in it |
| :---- | :---- |
| `interface\CLAUDE.md` | Titled `rdtii-dashboard`. Every path in its source map points into `rdtii_rocky_7.20` |
| `interface\PLAN.md` | Its location amendment puts `dashboard.py` in a separate `rdtii-dashboard` repo |
| `interface\README.md` | Titled `rdtii-dashboard`. Its run command is `rdtii_rocky_7.20\.venv\Scripts\python.exe` |

Neither `rdtii_rocky_7.20` nor `rdtii-dashboard` is on the Desktop any more. Both were archived and
every path into them is dead. `interface\MIGRATION_NOTE.md` records the move and is correct. Leaving
three false documents in a public repository at a release tag reads as carelessness to anyone who
opens them, and the secretariat will open them.

**Done when.** All three files describe the repo as it is, or say at the top which parts are Round 1
history.

## D11. The walkthrough recording, 5 h

**Length: about four minutes. Revised 2026-09-12.** Five host documents split three against two.
Three say three to four minutes, two say five. Four satisfies both. State the length in the file
name and the opening frame. Logged in `DECISIONS.md`.

**Running order, built on the five beats Word Section 6 requires.** Start a run from the button, with
progress in plain words. One finding in the audit view beside its source text. Follow that finding to
the official source and show the quoted words at the cited article. Reject a different finding,
export, and open the export to show the rejected row is gone and the indicator ID is still text.
Switch the engine. If time remains, close on what does not work yet.

The recording is the host's fallback if deployment from the guide fails, so every beat must be
visible even if the deployed instance never starts for the reviewer.

**Proposed recording rule.** One take, no cuts, real machine, real timings. A cut recording invites
the question of what was cut. If a run is too slow to show live, say so on camera and jump to a
finished run, visibly.

**Delivers to.** `C:\Users\woshi\Desktop\RDTII Finale Plan\3_Final_Stage\Deliverables_30Sep\3_Walkthrough_Recording\`,
which exists and is empty.

## D12. The five judge stations, 3 h

Four Round 1 briefs exist and are in the right format at
`C:\Users\woshi\Desktop\RDTII Finale Plan\2_What_We_Built\Self_Assessment\03_Submission\briefs\`:
Station 0 instrument, Station 1 scrape, Station 2 extract, Station 3 map. The 13:00 walkaround on
15 October has five stations.

**Proposed fifth station: the interface.** It is the only station a judge can operate themselves in
thirty seconds, and it is the one this task owns. Write `STATION_4_INTERFACE.md` into that same
`briefs\` folder, in the same format: what this station does, the numbers that matter, how it was
verified, known limitations.

**Proposed station script, thirty seconds.** Hand the judge the keyboard. They accept one finding
and reject one. They watch the engine switch. They see the export open. Nothing is explained
unless they ask.

**Note.** Refreshing the other four briefs for the finale belongs to the stage workstreams, not
here. Flag it, do not do it.

## D13. Operability pass, 5 h

**Touches.** `PAGE_TEMPLATE` :3768 throughout.

Walk the whole page as a stranger. Every button says what it does. Every error message says what to
do next. Every number says where it came from. No panel renders an empty box with no explanation.
The existing provenance ribbons and `[J]`, `[D]`, `[PROJ]` badges are kept, because they are the
thing that stops a judge mistaking a demonstration number for a judged one.

**Done when.** Someone reads every screen aloud and nothing needs a spoken footnote.

## D14. Visual polish, 4 h

Spacing, type scale, colour contrast, print stylesheet for the export. Inline CSS only. No web font,
no icon set, no build step.

---

## Minimum for the 30 September freeze

Three things. Everything else is negotiable.

| # | The minimum | Steps | Hours |
| :---- | :---- | :---- | ----: |
| 1 | A working accept, reject and correct flow whose decisions reach the export | D1, D2, D3, D6 | 28 |
| 2 | The named engine switch, two options, one control, engine visible on the rows | D4, D5 | 13 |
| 3 | A clean-clone deployment a stranger can follow to a working interface | D8, D9 | 11 |

Fifty-two hours. D7 at three hours joins them, because the zero document count is stated by the host
twice and shows on screen during the live test.

Remember what the freeze is. Code freezes on 30 September. Settings do not. The walkthrough
recording, the station briefs and the rehearsal record are deliverables and documents, so they can
be finished in the first days of October if the code is done. The code cannot.

## What gets cut first, in this order

1. **D14 visual polish.** Four hours that change no verdict.
2. **The CSV half of D6.** The xlsx is the deliverable. The CSV is a convenience.
3. **The comparison export in D5, reduced.** Keep the engine label on every row, which is what makes
   a comparison possible at all. Drop the side-by-side view. Build the comparison file from two
   exports by hand on the day and declare that it was assembled by hand. Anything typed by hand is
   recorded either way.
4. **The keyboard shortcuts in D2.** Buttons alone still score C3a.
5. **D10 stale document correction, downgraded.** Give all three files a one-line header saying
   they are Round 1 history, which takes ten minutes instead of two hours.

**Never cut, at any price.** The decision record in D1, because a review flow whose decisions do not
reach the export earns none of the ten points. The named engine control in D4, because it is four
points that cannot be recovered by anything else on the day. The repo README section in D9, because
eight points rest on a stranger reaching the interface, and no amount of interface quality survives
them not finding it.

**Never add, at any price.** A dependency. Not one. Not a small one.
