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

## 2026-10-03, The window is the machine's own browser in app mode, not a packaged app

**Decision:** `python interface/app.py --window`, and the double-click launchers, start the same server and
open its pages in Edge or Chrome with `--app=` on a profile kept for this tool. No installer, no bundled
browser, no new dependency; with no such browser the page opens as an ordinary tab.

**Why:** The developer asked for "a UI instead of an interface in a browser" and chose the no-install route.
A packaged app would add a build per system, a signing question on macOS and a second code path to keep in
step with the tab. App mode gives the window, the taskbar icon and the title for the cost of one command
line. Measured on Windows 11, Edge and Chrome: the process started for the window owns it and exits 0.2 s
after it closes, which is the stop signal.

**What the spike found that the plan had not:** a new Edge profile signs itself in to the Windows account
and puts a sync dialog over the window. Of four variants tried on fresh profiles, only
`--disable-features=msImplicitSignin` left the profile with no account; `--guest` and `--inprivate` still
signed in and rename the window. The flag is pinned by a test.

**Consequence if reversed:** A packaged app removes the dependence on an installed browser and, on macOS,
the Terminal window and the browser's Dock icon, at the price above. Not checked on a Mac yet.

## 2026-10-03, Closing the window stops the interface, and a run with it, after a warning

**Decision:** With a window, the server stops when the window's process has ended and no page has been
connected for five seconds. A run in progress is stopped with it; the page asks before the window closes.
While the window exists a run is never cut short, whatever the page's connection does.

**Why:** The developer's call. A server left running with no window has nothing to read its output or
stop its stage, which is the failure the run layer's shutdown was written for. The grace is counted in
loop ticks, not seconds, so a laptop waking from sleep is not taken for a window closed an hour ago.

**Consequence if reversed:** Keeping a run alive after the window closes needs a way to come back to it:
a tray icon or a second launch that reattaches. A second launch already brings the first window forward,
so the reattach half exists; the hidden-run half was not wanted.

## 2026-10-03, Results are filed by economy and source; hand collection is for designated sources only

**Decision:** A crawl writes to `scrape/<economy>/<source>/<time>`, hand-collected files go to
`inbox/<economy>/<source>/<date_time>`, and the inbox takes a file only for a source the stage's own files
designate: an economy's watchlist, and China's by-hand publishers.

**Why:** The developer's call, after asking how a hand-collected Chinese file's source could be identified:
it cannot be, from the file alone. The folder a person chooses is the only reliable statement of source,
and the source decides both the reading method (which portal parser) and the citation. A box for files
from anywhere produced files with neither.

**Consequence if reversed:** A free box needs detection of the source from content, which was estimated at
most of the triage workstream and still ends in "unknown" for a bare PDF.

## 2026-10-04, The registries receive their seed laws: the one change under stages/

**Decision:** The seed laws in `stages/p1-scrape/links/<cc>/seed_laws.yaml` are appended to
`sources_<cc>.yaml`, in both `instrument/` and `contracts/instrument/`, for all five economies. It is a commit of
its own (`e61d324`), registry data only.

**Why:** Each link list's README describes this join as the hand-back step, and the repository never received
it. The crawler therefore loaded a registry with no seeds, whose fingerprint differed from every shipped link
list's, and refused the list: a crawl with "Shipped link list" skipped the economy, in all five. The interface
cannot repair that from outside, because the crawler reads its registry from two fixed folders. The rule that
the interface never edits the pipeline was weighed against a default path that could not work at all; the
developer had asked for the scraping function to be made to work.

**What it changes:** 638 lines added, none altered. Each registry's fingerprint now equals its link list's.
The stage's 427 tests pass before and after. Seeds also become visible to a refresh from the portal, as the
stage intends.

**Consequence if reversed:** Reverting the commit returns to registries without seeds. The shipped lists are
then refused again; a list refreshed from the page (built for the seedless registry) would still be accepted.
**Still to decide by a person:** the judged tag carries the same defect, and the live test's rule that seeds
come from the host's portal list has to be checked against these seeds.

## 2026-10-04, Refresh from the portal replaces live discovery on the page

**Decision:** The second Sources option reads the portal's listings with the stage's catalogue tool into a link
list kept under the runs root, then crawls from that list. The crawler's inline discovery is no longer offered
on the page; it remains in the stage.

**Why:** Reading the listings is the long, silent part of a crawl: by the lists' own build logs, 68 minutes for
Singapore and 134 for Malaysia, where the page had said "up to 20 minutes". Inline discovery spends that time
and throws the list away; the same wait spent on a refresh leaves a list that later runs, second passes and
quick runs reuse, and whose counts the page can show before fetching. With Dry run ticked it only rebuilds
the list, which is the step wanted before a live test.

**Consequence if reversed:** Inline discovery needs fewer moving parts and no list folder, at the price of the
wait on every run and no count before the first document.

## 2026-10-04, Which Python runs a stage is kept per machine, and set from the page

**Decision:** The three stage interpreters can be named in Appendix, This machine. The choice is written to
`machine.json` in the state folder and applies at once. An environment variable of the same name wins; a
`.venv` in the repository is still found by itself.

**Why:** The window is started by double-click, with no terminal to set a variable in. On the developer's
machine the extraction stage's packages live in an environment outside the repository, so Extraction failed at
its first step. A fact about one computer does not belong in the repository or in a project folder.

**Consequence if reversed:** Without it the only ways are a system-wide environment variable or a `.venv`
inside the clone; the first is invisible from the page, the second is a second copy of a large environment.

## 2026-10-04, Each step of a mapping run has its own choice, and an unmeasured choice says so

**Decision:** The Run block of the Mapping tab holds one block per step: a slider for the candidate selection,
and a provider with one of its models for the quick screen, the careful reading, the re-check and the
tie-break. The banner's engine remains and sets all four at once. Providers and models are read from the
stage's declaration; whatever the pipeline was not measured on is marked "not measured" on the block and
warned about in Check. Keys are held per provider, in memory.

**Why:** Asked for by the developer on 4 October: the thresholds were readable on the page but could only be
moved by editing a file, and a run took one provider for every step. The prompts and the traps were written
for Claude and every reported figure comes from three Claude models, so offering another model without
saying so would let an untested row look like a tested one.

**Consequence if reversed:** One engine per run and fixed numbers are simpler and cannot produce a
combination nobody has scored. The price is a file edit to move a threshold and no way to try a cheaper or a
newer model on a Quick run.
