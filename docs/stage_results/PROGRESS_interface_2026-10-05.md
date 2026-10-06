# Progress — the interface (RDTII Rocky), 5 October 2026

Follows `PROGRESS_interface_2026-10-01_pm.md`. Written from the files; every statement can be checked
against the file or the command named beside it.

Code: `Desktop/rdtii_rocky_next/`, a working copy of its own, branch `feature/desktop-workspace-triage`.
It is pushed to the private repository `JohnChen-kmg/rdtii-rocky-next`, branch `main` (the remote named
`next`). The judged copy, `Desktop/rdtii_rocky_finale_9.30` on `master`, and its tag `final-submission`
(commit `35be14a`) have not moved, and `submission/` is the same in both: the command
`git diff final-submission HEAD -- submission` prints nothing. Record of every change and how it was
verified: `docs/CHANGELOG_FINALE.md`, sections 2026-10-03, 2026-10-04 and 2026-10-05.

---

## 1. What changed since 1 October

106 commits since the judged tag: 1 on 1 October, 4 on 3 October, 58 on 4 October, 43 on 5 October
(`git log final-submission..f20a6e2`). 239 files, 27,905 lines added. The interface's tests went from 94
to 291.

**3 October: a window, and results filed by source.**

- The tool opens in a window of its own (`python interface/app.py --window`, or a double-click on a
  launcher): the machine's Edge or Chrome in app mode, nothing installed. Closing the window stops the
  tool, and a run with it, after a warning. One instance per repository.
- Every child process goes through one helper; Stop ends the whole process tree on every system.
- A crawl writes to `outputs/scrape/<economy>/<source>/<time>`. Each hand-collected file is judged by what
  it is (ready, or why not and what to do).
- A workflow runs the interface's tests on Windows, macOS and Ubuntu.

**4 October: scraping made to work, a model per step, the stages repaired where the page found a fault.**

- Scraping: the registries received their seed laws, without which every shipped link list was refused;
  one run per economy; Check asks the crawler whether it will accept the list and states the time; Refresh
  from the portal; Quick run; a crawl the portal cut short ends as failed. All five portals' listings read
  again and a Sample crawl of each completed: 935 documents.
- Extraction: documents that gave no provisions are listed "to check"; three causes repaired in the stage
  (Portuguese headings, English editions of article-style laws, the crawler's language for each file).
- Mapping: 3.2 Run is the steps in order, A to E. A number per indicator for candidate selection, and a
  provider and a model for each of the four model steps. Three more providers (DeepSeek, Kimi, ChatGPT)
  through one OpenAI-compatible client, marked "not measured".
- Which Python runs each stage is set from the page (Appendix → This machine).
- A run note on every Run block, carried with the run folder.
- The Overview: an introduction, the workflow map in one column with a folded example per stage, the
  mapping steps as sub-blocks.

**5 October: the cost report, run tables, hand collection without a source, and a night test.**

- Overview: the cost report in three blocks, Money, Time and a Calculator, from one data block; a block
  "Estimated performance by model" from the experiment of 4 October, said on the page to be one
  experiment with small samples.
- Every Output is a table of runs: when each began, when it last ran, complete or not. All of it is read;
  nothing new is written into a run folder.
- Hand-collected files ask for the economy only and go to `inbox/<economy>/Hand_collected/<date_time>/`.
  This reverses the rule of 3 October.
- Mapping opens with Engine API keys; 3.2 Run names the finale's model for each step; there is no single
  control that sets the four steps at once.
- Appendix opens with "Adding a new economy": what each stage needs, the file that holds it, what is built.
- **A fault found and repaired.** Since 4 October every real crawl had ended as failed after storing its
  documents: the adapters' facts had been written into the manifest, and the crawler's own check allows no
  other field there. They now go to `manifest_meta.jsonl`. Found by a Quick run of three Timor-Leste
  documents from the page.
- The submission README and the release notes were rewritten for this tool (commit `a64454b`); the Word
  document and the portal sheets are in the planning folder, `Final doc\PORTAL_UPLOAD_2026-10-05`.
- The packager now writes the records CSV with a byte-order mark (commit `f20a6e2`). The six filed files
  in `submission/` are unchanged and have none.

---

## 2. Tested on 5 October

**The night test**, small runs, each started from the page on a test copy, no hosted model called, $0
(`docs/CHANGELOG_FINALE.md`, 2026-10-05):

- Scraping: a Quick run of three Timor-Leste documents, a dry run for Australia, two files dropped by hand.
- Extraction: the demo corpus (5 documents, 3,643 provisions), the three Timor-Leste documents (1,361),
  a hand-collected Singapore folder (670), an Australian saved page (1,438).
- Mapping: Singapore, indicators 6.1 and 6.4, five provisions, local Qwen in all four steps: two rows in
  the host's 14 columns in three minutes.
- Accept, Reject, Correct and Clear decision, with an export after each; Stop; Clear run; the self-test.

**The suites, run again on 5 October for this report:**

| Suite | Result |
| :---- | :---- |
| Interface (`python -m unittest discover -s interface/tests -t interface`) | 291 pass |
| Crawler (`stages/p1-scrape`, pytest) | 429 pass, 3 skipped |
| Extraction (`stages/p2-extract`, pytest, with the stage's own Python) | 128 pass, 2 skipped, 6 fail: the six of `test_fresh_keeps_ocr_cache.py`, which load a workshop tool the repository does not hold |
| Mapping (`stages/p3-map`, pytest) | 505 pass, 8 skipped |

---

## 3. Documentation brought to the tool of 5 October

Written on 5 October, each from the code and the change log, not from memory.

| File | What was done |
| :---- | :---- |
| `docs/CODE_MAP.md` | Rewritten. The map of 12 September described the Round 1 layout and `interface/dashboard.py`. The new one covers the interface, the four stages, the seams, the settings and a "where to look when" table. Its 343 references of the form `name :line` were checked by script against the tree |
| `docs/DATA.md` | Rewritten. What the repository ships (with sizes), what it does not, where a run writes, the settings that point at data. The Round 1 text named a corpus and a data release this repository does not have |
| `docs/stages/interface/README.md` | A first part with the state on 5 October (what works and when it was last tried, what does not exist, where each host requirement stands); the text of 12 September kept below it, as written |
| `docs/stages/interface/DECISIONS.md` | Seven entries dated 5 October, the last saying what became of each entry of 12 September; a dated line under each earlier entry that a later decision changed |
| `interface/README.md` | The layout table redrawn page by page; two cells still described the Overview of 1 October and hand collection by source |
| `docs/stage_results/README.md` | The rows for the instrument's progress of 4 October and for this report |
| `README.md` | The recording line names `walkthrough_RockyHasAHomeRun_Oct05_5min.mp4`; the mapping test count is 505; the list of shipped OCR packs no longer names Malay |
| `docs/RELEASE_NOTES.md`, `docs/CHANGELOG_FINALE.md` | The mapping test count; an entry for this day's documentation and for commit `f20a6e2` |

---

## 4. Found while writing the documentation

Facts, each checked on 5 October. The first three were corrected in the documents; the rest are left for
the developer.

1. **The README said the Malay OCR pack ships. It does not.** `stages/p2-extract/fixtures/` holds English,
   Lao, Portuguese and simplified Chinese; the stage maps Malay to `msa+eng`. The README's sentence now
   lists the four.
2. **The mapping suite is 505 tests, not 504**, since the test added with `f20a6e2`.
3. **`docs/DATA.md` and `docs/CODE_MAP.md` described a tool that is gone** (above).
4. **`main.py` serves nothing.** The Round 1 driver is still at the top of the repository. Its default
   mode, `python main.py --economy Singapore --pillar 6`, ends without error and writes the 14 column
   names and no rows: it keeps rows whose Indicator ID begins `P6-`, and the filed rows carry `6.1`. The
   interface does not use it. The two documents now say so; the file is unchanged.
5. **The first recording of 5 October was 46 minutes 26 seconds long** (read from the file's own header),
   against the three to five minutes the host's templates ask for. The developer recorded again the same
   evening: `walkthrough_RockyHasAHomeRun_Oct05_5min.mp4`, 6 minutes 23 seconds, which is the one submitted.
6. **`interface/DATA_PATHS.md`** lists eight variables the browser may set; the code's allowlist has
   twelve (`rdtii_ui/envbuild.py`, `ALLOWLIST`). The file is dated 29 September and was not edited.
7. **`ASSEMBLY.md`** at the top of the repository describes the assembly of 29 September. Not edited.
8. **One line of the start-up banner** in `interface/app.py` still says "one folder per economy and
   source" for the inbox. Code, not edited.

---

## 5. The repository on GitHub

- `next/main` was at `2edcf44` (the push of 4 October) plus one commit made on the GitHub website on
  5 October at 09:50, `6e6c1f8`, "Update repository clone instructions in README": the two clone lines
  changed to `rdtii-rocky-next`. The local branch already made the same change in `a64454b`, so the two
  merged without conflict.
- No tag exists on that repository yet (`git ls-remote --tags next` is empty). The portal asks for a tag
  named `final-submission` on the commit to be judged.
- The old repository, `rdtii-rocky-finale-9.30` (remote `origin`), has the branch at `bafe873`
  (4 October); nothing was pushed there on 5 October.

---

## 6. Not verified, and open

Unchanged from the sheet `MANUAL_TASKS.md` in the upload folder, except where noted.

- **No comparison of two engines' runs** in the tool. The host's workbook has sheets Engine Comparison and
  Run Record.
- **No hosted model has been called from the page** since the rework. The night test used local Qwen.
- **No second machine, no Mac window.** The interface's tests passed on Windows, macOS and Ubuntu in the
  workflow on 4 October; that run was on the old repository, at commit `bafe873`, and the workflow does
  not start on a push to `main`.
- **Three choices in the submission documents wait for the developer's word**: the new repository (his own
  commit `6e6c1f8` makes the same choice in the README), the date in the Word document, and the reworded
  Section 5.
- **Whether the six filed CSV files receive the byte-order mark.** If they do, the sentences "byte for
  byte" and "have not been touched" in the README, the release notes and the Word document must change.
- Left open by the developer earlier: whether one-piece documents (a notice with no articles) go to
  Mapping; the Sonnet 5 price card ($3 / $15 in the stage, $2 / $10 posted); the raw command line under
  Start.

---

## 7. What the next step inherits

1. Decide on the recording's length (item 5 of section 4) before uploading.
2. Tag the commit to be judged on the new repository, and give the portal its SHA.
3. One Quick run on Claude from the page, with a key: it costs cents and is the one path not yet walked.
4. A clean clone on a second machine against the clock, and one window on a Mac.
5. Copy `README.md` to the upload folder again whenever it changes; it was copied on 5 October after this
   day's edits.
