# Decisions: Dashboard

Task-level choices and the reason for each. Newest at the bottom, so the file reads forward in time.

Code changes are not logged here. They go in
`C:\Users\woshi\Desktop\rdtii-rocky-finale\docs\CHANGELOG_FINALE.md`, three lines each.

Entries marked **Proposed** have not been agreed. They are this task's recommendation with the
reason attached, so a decision can be made quickly rather than reopened from nothing.

---

## 2026-09-12, One file, standard library only

**Decision:** The interface stays a single Python file that imports nothing outside the standard
library.

**Why:** No dependency to install is the shortest path through the thirty-minute clean-machine test.
C4a is worth eight points and a failed `pip install` on a borrowed laptop costs all of them. The
file already runs on `ThreadingHTTPServer` with no package to fetch.

**Consequence if reversed:** Every future reader of the repository has to build an environment before
they see anything. The deployment time stops being controllable, because it then depends on the
tester's network, their Python version and a package index. Protect this property in any redesign,
including the review screen and the export writer.

## 2026-09-12, The interface never edits the pipeline

**Decision:** The interface passes environment variables and runs `main.py` as a subprocess. It
reads what the stages write. It does not import stage code and does not write into stage
directories.

**Why:** The pipeline has to stay reproducible from the command line with the interface absent. A
wrapper can be inspected in an afternoon. A tool that reaches into the stages cannot be audited
separately from them.

**Consequence if reversed:** Every claim about the pipeline would need re-verifying with the
interface in the loop. The secretariat's check of cost claims against the code gets harder, not
easier. The blast radius of a UI bug becomes the whole pipeline.

## 2026-09-12, Secrets live in memory only

**Decision:** The API key arrives by a POST to `/api/key`, lives in a process-memory holder, is
redacted from every captured line, and is never written to disk or rendered. Anything in the launch
settings whose name contains KEY, TOKEN or SECRET is rejected outright rather than filtered.

**Why:** The repository must be public at a release tag. Nothing carrying credentials can ship.
Rejecting outright rather than stripping means a mistake fails loudly at the moment it is made.

**Consequence if reversed:** A key reaches a log, a sidecar or a static export, and the public
repository leaks it. That is not a lost point, it is a disqualifying incident.

## 2026-09-12, Informed by templates, built on none

**Decision:** The redesign looks at interface patterns found online for layout and wording, and
copies none of them as code.

**Why:** Almost every modern template brings a build step, a package manager or a font from a CDN.
The finale needs a page that deploys with zero installation and runs on a machine that may have no
network beyond the government sites being crawled.

**Consequence if reversed:** The first decision on this page falls. The clean-machine deployment
stops being a four-command story, and the Apache 2.0 release picks up third-party licence
obligations that have to be tracked and declared.

## 2026-09-12, revised the same day: the walkthrough recording is about four minutes, with five beats

**Decision:** Record to about four minutes, state the length on screen and in the file name, and
cover all five beats that Section 6 of the Word template lists.

**Why:** The first version of this entry said five minutes, on the evidence of two documents. Reading
every host template line by line found five, and they split three against two. The README template,
the workbook Instructions sheet and checklist item 19 say three to four minutes. The Word template
Section 6 and the orientation slides say five. Four minutes satisfies "three to four" exactly and
stays under five, so it cannot miss either limit. The workbook also says the recording "is the
fallback if we cannot deploy your system from your guide", so it may carry C3a and C3b on its own.
That is a reason to cover every beat, not to run long.

The five beats, from Word Section 6:

1. Start a run from the interface, with progress in plain words.
2. The audit view: one row shown beside the source text it came from.
3. Follow that row to its official source and show the quoted words at the cited article.
4. Reject a row, then export, and show that the correction took effect.
5. Switch the AI engine in the interface.

Question 2 in `C:\Users\woshi\Desktop\RDTII Finale Plan\3_Final_Stage\OPEN_QUESTIONS_FOR_HOST.md`
now lists all five sources.

**Consequence if reversed:** If the host confirms five minutes, add the honest limitations close as a
final minute. The four-minute cut still stands on its own.

## 2026-09-12, Review applies to run output, never to the frozen submission

**Decision:** Accept, reject and correct operate on findings produced by a run. The Round 1 records
in `rdtii-rocky-finale\submission\` stay read-only in the interface.

**Why:** Those records are the judged Round 1 evidence. The interface already keeps a firewall
between judged numbers and demonstration numbers, and a reviewer verdict written onto a judged row
would destroy the distinction that firewall exists to protect.

**Consequence if reversed:** The judged corpus stops being a fixed reference, and no number in the
submission can be quoted with confidence again.

## 2026-09-12, Proposed: decisions are an append-only log, never an edit in place

**Decision, proposed:** Each accept, reject or correct appends one line to
`interface\db\decisions.jsonl`. Lines are never rewritten. The latest line for a finding wins, and
the earlier lines remain as the trail.

**Why:** C3a is audit mode. A reviewer who changes their mind is normal and the record of the change
is the audit. The existing `promote_log.jsonl` already works this way. Its reader,
`_promote_log_entries()` at `dashboard.py` :1275, is twelve lines long, so this costs nothing to
build. The file itself is runtime data under the gitignored `interface\db\`, so do not expect to
find it in a clean clone.

**Consequence if reversed:** An in-place store is smaller and faster to read, and it loses the
history. On the day, a judge asking "did you change that verdict" would have no answer.

## 2026-09-12, Proposed: rejected rows leave the evidence file, and the review log keeps them

**Decision, proposed:** The exported evidence file carries exactly the host's fourteen columns.
Rejected rows are removed from it, corrected values are substituted in place, and a separate
`review_log.csv` records every decision including the removals.

**Why:** The host template has fourteen columns and adding a fifteenth risks a schema-conformance
mark for a gain the template never asked for. Splitting the trail into its own file keeps the
evidence file clean and the audit complete.

**Consequence if reversed:** Extra columns on the evidence file might read as richer, or might read
as not following the template. The safer reading of a fixed-schema instruction is to follow it
exactly and put the extra material beside it.

## 2026-09-12, Proposed: the export is written as xlsx by zipfile, all cells inline strings

**Decision, proposed:** Write the workbook directly with `zipfile` and hand-built sheet XML, with
every cell typed as an inline string.

**Why:** Indicator IDs are decimal text. Entered as numbers, `12.10` collapses to `12.1` and `4.01`
to `4.1`, and those are different indicators. A CSV cannot prevent Excel coercing on open, whatever
was written. Inline strings make coercion impossible by construction, and `zipfile` is standard
library, so the first decision on this page survives. The reading half of the same format already
exists in `dashboard.py` at `_xlsx_preview()`.

**Consequence if reversed:** Exporting CSV only is quicker to build and leaves the single most
specific trap the host named, twice, open on the judges' machine rather than ours.

## 2026-09-12, Proposed: two named engine presets, raw variables demoted

**Decision, proposed:** Add `engine_a` and `engine_b` as named presets beside `judged`, `keyless`
and `custom`, each a frozen dictionary in the code. The UI shows one control with two labelled
options. The eight allowlisted variables stay reachable under `custom`, collapsed.

**Why:** A steward watches the switch on 15 October. A radio pair changing from "Claude, hosted" to
"Qwen 2.5 14B, open weights, local" is visibly an engine switch. Typing a model name into a field is
a command typed into a box, and that reading loses the four points of C5b.

**Consequence if reversed:** Keeping only the free-form `custom` preset is more flexible and puts
four points at the mercy of how one steward reads one sentence. Flexibility is not what is being
marked.

## 2026-09-12, Proposed: engine is recorded per run, not per row

**Decision, proposed:** The engine preset is written once into the run's sidecar. Rows inherit the
engine of the run that produced them.

**Why:** It needs no change to the mapping stage and no new column upstream, and every row in a run
was produced by one engine anyway. The comparison file is then a join of two runs.

**Consequence if reversed:** A per-row engine field would be more precise if a run ever mixed
engines. No run does, and adding the field means changing a stage this task does not own, two weeks
before a code freeze.

## 2026-09-12, Six economies and pillars 6 and 7 are required. Further is optional

**Decision:** The run screen offers the six covered economies and pillars 6 and 7. Any other
economy or pillar appears greyed out with a one-line reason, rather than being hidden.

**Why:** The developer's scope call. Showing the unsupported choices, with the reason, is the honest
version of the scope. It also helps on 15 October: if the sealed task lands outside scope, a steward
sees a deliberate, documented limit rather than a missing feature, and the engine switch and the
comparison still work on any run that does exist.

**Consequence if reversed:** Hiding unsupported economies makes the scope look accidental. Enabling
them without support produces runs that fetch and map nothing, which reads worse than a stated limit.
