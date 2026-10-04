# Changelog — instrument workspace

Every change made in this folder, newest first. Each entry gives three things: what changed, why, and
how it was verified.

Each entry carries one of two tags:
- **instrument**: the change is inside `instrument/`. At hand-off, paste these entries into the repo's
  `docs/CHANGELOG_FINALE.md` under W3 (`HANDOFF.md` step 5).
- **workspace**: the change stays in this folder.

---

## 2026-10-04 (night): what an absence scores and the count rule, as data (D17)

Not logged here at the time: **the second hand-off was made on 4 October at 10:37** by the session
working in `rdtii_rocky_next` (repo commit `bafe873`), following `HANDOFF.md`. It carried the rounds of
D15 and D16, updated the pinned test and the repo README, and refreshed `docs\stages\p0-instrument\`.
The mapping stage then began reading scales, `level` and `framework_name` from the blocks (commits
`bbcd27a` and `421e7f5`).

**instrument · `output/indicators.yaml`: `absence_score` and `absence_basis` on all 61 blocks,
`count_rule` on 15.**
- What:
  - `absence_score` is 0 on 41 blocks and null on 20: the 14 inverted blocks, 11.2, and 1.4, 5.3, 9.1,
    11.4 and 12.6. `absence_basis` gives the reason and the host source on each.
  - `count_rule` is on 1.4, 2.1, 2.3, 3.1, 3.4, 4.3, 4.9, 5.2, 5.3, 6.1, 6.2, 9.4, 10.1, 10.2 and 10.3.
    Six of them name a fact the roll-up does not have (`needs`): 3.1, 5.2, 5.3, 10.1, 10.2, 10.3.
  - The top-level `block_fields` key describes both fields and how a count rule is applied.
  - New data file `code/scripts/data/rollup_fields.yaml` holds the values. New builder
    `code/scripts/build_rollup_fields.py` writes them into the blocks, just above each `sources:`
    line, and has `--check`. New report `code/scripts/report_rollup_fields.py`.
  - The validator has a new group, 1e: `absence_score` is null or one of the block's own values and
    null on every inverted block; `count_rule` is well formed; 6.1 and 6.2 state exactly "two or more
    distinct half-point measures score 1"; all three keys equal the data file.
  - `output/README.md`, `output/INSTRUMENT_NOTES.md` section 7 and `instrument/README.md` describe the
    fields.
- Why: the mapping stage's requests R5 and R6, decided by the developer on 4 October. Decision D17.
- Verified:
  - 292 lines added to `indicators.yaml` and none changed; the builder stops if any other key of any
    block would parse differently. A second run changes nothing.
  - The mapping stage's own code, at repo commit `421e7f5`, builds the same prompt, character for
    character, from the repo's instrument and from this one: for all 61 indicators together and for
    each of the 61 alone (62 scopes). The pillar 6–7 prompt is 31,929 characters with the same SHA-256.
  - Rehearsed in an exported copy of `rdtii_rocky_next` at `421e7f5`: mapping tests 478 passed and
    9 skipped before and after the copy; interface tests 233 ran, OK, before and after. (The working
    copy itself reports 479 passed and 8 skipped, because one test needs run data an export lacks.)
  - Validator PASS, exit 0. Three deliberate faults were each caught and then undone: a changed data
    file with the block not rebuilt, a 6.1 rule rebuilt with a threshold of three, and hand edits
    giving an inverted block a score and another block a value off its scale.
  - `evidence/rollup_fields_2026-10-04.md` lists every block's rule and absence value.
- **Not done: the copy into the repo.** The hand-off was attempted and refused by this session's
  permission system, which does not let it write into the shared repo. `HANDOFF.md` has the commands
  and the text for `INTERFACE_CONTRACT.md`. The repo is untouched at `421e7f5`.

## 2026-10-04 (evening): the hand-off target is `rdtii_rocky_next`, and the hand-off is rehearsed

**workspace · `HANDOFF.md` rewritten for the repo the tool is developed in now.**
- What:
  - The hand-off target is `C:\Users\woshi\Desktop\rdtii_rocky_next`, the working copy since 3 October.
    `rdtii_rocky_finale_9.30` is the public submission repository and `rdtii-rocky-finale` the
    development history; neither receives the instrument unless the developer says so.
  - `HANDOFF.md` now lists what the repo's owner does with the copy: update the tier counts pinned in
    `interface\tests\test_map_start.py` line 29, read `framework_name` in the mapping stage's
    `rollup.py`, correct the "host-criteria-only" sentence in the repo `README.md`, and refresh
    `docs\stages\p0-instrument\`.
  - `code/tools/validate.py` compares with `rdtii_rocky_next` when it exists, else
    `rdtii-rocky-finale`, and names the repo it compared with in the saved transcript.
  - `NOTICE_FOR_OTHER_STAGES.md`, `README.md` and the header of `DECISIONS.md` name the repos the
    same way; the notice gains the interface items.
- Why: the earlier `HANDOFF.md` named `rdtii-rocky-finale`, which has been frozen at the submission tag
  since 30 September. A copy made there would not have reached the mapping stage or the interface.
- Verified: a rehearsal in an exported copy of `rdtii_rocky_next` at commit `2edcf44`. Nothing was
  written to any repo.
  - Mapping tests: 450 passed, 9 skipped, before and after the copy.
  - Interface tests: 216 passed, 17 skipped, before and after.
  - The pillar 6–7 prompt, built by the mapping stage's code: 31,929 characters, same SHA-256 before
    and after.
  - The mapping stage's code builds its prompt for each of the 61 indicators alone, and for all 61
    together (322,081 characters).
  - The interface's readers give 61 indicators, tiers A 9 / B 52 / C 0, the same nine automated.
  - `python code\tools\validate.py --save`: PASS, exit 0; 45 files differ from the repo's copy.
  - Not caught by the rehearsal: the pinned test above is skipped when the demo extraction output is
    absent, as it is in an export. It will fail in the working copy until its counts are updated.

**workspace · progress report written to the planning folder, at the developer's request.**
- What: `RDTII Finale Plan\finale_progress\PROGRESS_p0-instrument_2026-10-04.md`, and its row in that
  folder's `README.md`. It is the first instrument file there: the state on 4 October, the timeline
  since 13 September, the file and block structure, what depends on the indicator, the rehearsal, what
  each stage inherits and the open decisions.
- Why: the other stages and the developer read that folder, not this one.
- Verified: every count in it was read from `instrument\output\` or from the evidence files the same
  day. Not committed in the planning repo.

## 2026-10-04 (later): the coverage marks (D16)

**instrument · `output/indicator_order.yaml` carries `coverage`, `coverage_reason` and `answer_nature`
on every entry, and a top-level `coverage_marks` section.**
- What:
  - New data file `code/scripts/data/coverage.yaml`: the classes, the reason categories, the nature
    codes, the automated pillars, each indicator's nature codes and the per-economy override for
    China's pillar 6. `build_indicator_order.py` writes the marks from it.
  - 9 automated (pillars 6 and 7), 52 manual, 6.5 excluded. Reason `practice` on 1.4, 3.4, 5.3, 9.1,
    11.4 and 12.6; `scope` on the other 46.
  - The validator checks the marks, and compares them with the coverage register when
    `RDTII_COVERAGE_REGISTER` names it; `code/tools/validate.py` sets that variable.
- Why: decision D14 and the mapping stage's request R1 asked for the marks, and the developer pointed
  to the plan, where Timor-Leste is mapped for all 52 other indicators with a manual-check notice.
- Verified:
  - The nature codes were parsed from the register's tables (61 rows), not retyped. The validator
    reports that classes and nature codes agree for all 61.
  - Every earlier field of every entry is unchanged, and so is every earlier top-level key.
  - The mapping stage's loader, run against this folder, still resolves the automated set to the same
    nine indicators, and its own classification is unchanged. The pillar 6–7 prompt is still
    byte-identical.
  - The register's Tier column is out of date for 38 indicators (they are Tier B now). The register is
    in the planning folder and was not edited.

**workspace · `notes/timor_leste_all_indicator_run.md`.**
- What: what the plan and the Timor-Leste run of 27 September say about the 52 other indicators: 13
  produced scored rows, 39 a "no provision found" row, every row a manual-check notice.
- Why: it decides the review order for the Tier B blocks and explains the coverage marks.
- Verified: counts taken from `out_tl52/submission/records_TL.csv` and `submission_report_TL.json`.

## 2026-10-04: every indicator at pillar 6–7 depth (D15)

Not logged here at the time: the hand-off of 29 September (repo commit `bf2bb3e`, merged as
`ad27d1f`), decisions D13 and D14 of 20 September, and a validator run on 27 September. The repo's
copies matched this folder when this round began.

**instrument · `output/indicators.yaml`: the 52 indicators outside pillars 6 and 7 carry the same
elements as the nine pillar 6–7 blocks.**
- What:
  - 38 thin blocks rewritten at full depth and 14 blocks from 13 September completed. All are Tier B;
    there is no Tier C block.
  - Every block now has `weight` (from each Guide chapter's weights paragraph), `scoring_features`,
    `guide_examples`, `null_statement` and `sources`, and a `question` separate from its `definition`.
  - `polarity: inverted` on 14 blocks. `level: economy` with `framework_name` on 13: 7.1 and 7.2 as
    before, plus 4.2, 4.5, 4.6, 4.1, 5.1, 5.4, 5.7, 8.1, 8.2, 11.1 and 12.9.
  - Every trap is on both blocks it concerns.
  - The nine pillar 6–7 blocks gained only keys the prompt does not render: `scoring_features` and
    `guide_examples` where absent, `null_statement`, `sources`, and `framework_name` on 7.1 and 7.2.
    The absence statements and framework names are the mapping stage's own wording, copied from
    `submission.py` and `rollup.py`.
  - A banner above each pillar says where its measures live. New top-level key `block_fields`;
    `tiers` and `weights_note` rewritten.
- Why: decision D15. The live test may draw any pillar, and a block with no traps gives the model no
  warning about look-alikes.
- Verified:
  - Drafted by seven agents under `drafting/2026-10-04/BRIEF.md`. Each group's output passed
    `check_group.py`: citations on every line, cited pages and host rows exist, Guide examples' countries
    are on their cited pages, branch scores equal the host's.
  - The scoring branches of all 38 rewritten blocks were read against the host criteria.
  - A second pass closed all 37 one-sided sibling references; the validator reports 0.
  - The mapping stage's own `build_system_prefix()`, run against this folder before and after, gives
    the same pillar 6–7 prefix: 31,929 characters, same SHA-256, identical byte for byte.
  - The nine pillar 6–7 signature files are identical to the repo's copies.
  - `python code/tools/validate.py --save`: PASS, exit 0.
  - **No person has read the new blocks.**

**instrument · `output/policies.yaml`: new last section `indicator_sets`.**
- What: lists of the inverted, economy-level, practice-based and non-regulatory indicators.
- Why: the mapping stage lifts the inverted IDs out of a prose sentence and asked for a list a program
  can read.
- Verified: every pre-existing key is unchanged, so the three sections the prompt renders are
  byte-identical. The validator checks the lists against the blocks and the order file, and checks that
  the polarity sentence names the same 14 indicators.

**instrument · Reviewed label flags for every pillar.**
- What:
  - `code/scripts/data/label_flags.yaml` is new. It holds the seven Round 1 flags, moved out of
    `build_gold.py` with their reasons unchanged, and 208 new flags (51 suspect, 157 advisory) for rows
    outside pillars 6 and 7.
  - Each flag in the gold set now carries `basis`: `round1_review` or `drafting_review_2026-10-04`.
  - One exemplar added (3.1, Thailand row 13). Signature files outside pillars 6–7 now say `tier: B`.
- Why: the other pillars had no reviewed flags, so their evaluation would run on labels the drafters
  already knew to be wrong.
- Verified: the gold set rebuilds to 1,054 rows; before the new flags were added, the only difference
  from the previous build was `basis` on the seven Round 1 rows. No suspect row is an exemplar.

**instrument · `output/INSTRUMENT_NOTES.md` covers every indicator; new `build_notes.py`.**
- What:
  - Sections 8 to 10 are generated: one line per indicator, where each pillar's evidence lives, and the
    reviewed flags by indicator. `code/scripts/data/notes_table.yaml` holds the one-line texts.
  - The narrative's 18 legacy `P6-I1`-style IDs are now decimal, and section 7 describes the new state.
- Why: the notes covered pillars 6 and 7 only.
- Verified: `build_notes.py --check` reports the section current.

**instrument · `validate_instrument.py` checks the same elements on every block.**
- What: new group 1d (required keys, weight, row numbers against the host sheets, question differs
  from definition, the allowed forms of `polarity` and `level`), the `indicator_sets` checks, `basis`
  on reviewed flags, and an INFO line counting one-sided sibling references.
- Why: "same structure" should be machine-checked, not asserted.
- Verified: on the instrument as it stood before the merge it listed 203 problems; after the merge it
  passes.

**instrument · New `report_flags.py`; `report_coverage.py` legend updated.**
- What: `report_flags.py` writes the label-flag report that was a one-off on 13 September.
- Verified: `evidence/label_flags_2026-10-04.md` and `evidence/coverage_2026-10-04.md` generated.

**workspace · `drafting/2026-10-04/`, the round's working material; `REPORT_2026-10-04_parity.md`;
evidence dated 2026-10-04; `NOTICE_FOR_OTHER_STAGES.md`, `HANDOFF.md`, `README.md` and `code/README.md`
updated.**
- Why: the record of how the content was made, and what the other stages need to know.
- Verified: evidence files regenerated from the merged instrument; prompt sizes measured with the
  mapping stage's code (`evidence/prefix_sizes_2026-10-04.md`).

## 2026-09-13 (late afternoon): the code gets its own folder

**workspace · The code moves to `code\` at the workspace root: `instrument\scripts\` becomes
`code\scripts\` and `tools\` becomes `code\tools\`. `code\README.md` explains the coding workflow
(D12).**
- What:
  - Both folders were moved as they were; all 15 files have the same SHA-256 before and after.
  - `code\README.md` covers: a picture of inputs, scripts and outputs; each step and when to run it;
    the helpers; common tasks with what to edit and what to run; the full rebuild order; and how one
    set of scripts works in both layouts.
  - Updated to the new paths: `README.md`, `HANDOFF.md` (table, never-leaves list, copy commands with
    a separate `$CODE` source), `PLAN.md`, `NOTICE_FOR_OTHER_STAGES.md`, `evidence\README.md`, the
    evidence audit header, `sources\README.md`, the overnight report, `drafting\2026-09-13\README.md`
    and the archived merge guard's message.
- Why: the user wanted one visible folder for the coding files, with the workflow explained, next to
  `PLAN.md`.
- Verified: see the next entry.

**instrument · The scripts find the stage folder in either layout.**
- What:
  - `rdtii_examples.py` now exports `SCRIPTS` and `DATA` (the scripts' own folder and its `data\`),
    and sets `REPO` to whichever folder holds `output\`: the scripts' parent (repo layout) or
    `instrument\` beside `code\` (workspace layout). If neither exists it stops with a clear message.
  - `build_gold.py`, `build_signatures.py`, `build_indicators_from_methodology.py`,
    `report_coverage.py` and `validate_instrument.py` read `data\` through `DATA`. The validator reads
    `indicator_ids.py` through `SCRIPTS`, and its legacy-ID message no longer fails for files outside
    the stage folder.
  - `code\tools\validate.py` runs `code\scripts\validate_instrument.py` by path.
  - `code\tools\audit_citations.py` sorts the country names it reports. Python's string hash
    randomisation had made the order change between runs, so the output wasn't reproducible. The
    evidence audit was re-saved; it lists the same 30 lines.
- Why: the hand-off copies `code\scripts\` into `stages\p0-instrument\scripts\`, so the same files
  must run in both places.
- Verified:
  - Workspace layout: all four builders, run from the workspace root and from an unrelated folder,
    reproduce every output byte for byte, matching SHA-256 hashes taken before the move.
    `--check` reports no differences. `python code\tools\validate.py` passes. The prompt sizes and
    coverage table are unchanged, and the audit gives identical output under two hash seeds.
  - Repo layout, rehearsed in a scratch copy (`stages\p0-instrument\` with `scripts\` inside, plus the
    mapping stage's two copies taken from the repo): the builders run and the validator passes. After
    a simulated hand-off copy, `--require-vendored` passes with "vendored copy … is identical".

## 2026-09-13 (afternoon)

**workspace · `NOTICE_FOR_OTHER_STAGES.md`: contract and workflow notice for the other stages.**
- What:
  - One notice for the scraping, extraction, mapping and dashboard sessions: status, ID and scope
    rules, the changed contract files with their field names, the host rules, the known baseline, a
    part for each stage with file:line references, the workflow, and what to do.
  - `README.md` now says to update and re-send it after any contract or workflow change.
- Why: the user is starting the other stages in parallel sessions.
- Verified:
  - Field names come from loading the current files: codebook, policies, order, a signature, and a
    gold row.
  - Stage references come from greps of the repo at `92a5e9d`: `p1-scrape/src/p1_scrape/sources.py:31`
    and `contracts/schemas/manifest.schema.json`; `p2-extract/src/rdtii_p2/ingest.py:31` and
    `cli.py:409`; `p3-map/config/settings.py:74`; `interface/dashboard.py` around lines 412–479 and
    1575–1647.
  - The crawler's `sources_<cc>.yaml` registries are crawler-owned, not instrument outputs, so
    `HANDOFF.md` needs no new destination.

## 2026-09-13 (midday): one codebook file

**instrument · The codebook is one file: all 61 blocks in `output/indicators.yaml`, in host order,
grouped by pillar. `output/indicators_generated.yaml` is gone (D11).**
- What:
  - The 38 Tier C blocks moved into `indicators.yaml`. Every block is ordered as in
    `indicator_order.yaml`, under a banner per pillar; the pillar 6 and 7 banners were kept as they
    were. Every ID is written in double quotes.
  - The file header now describes one file, and a new top-level `tiers` key describes A, B and C,
    including Tier C's depth disclosure from the old generated file. The prompt does not render
    that key.
  - New `scripts/codebook_file.py` splits the file into header, pillar banners and raw block texts,
    and reassembles them, so a script can add a block without reformatting the others.
  - `build_indicators_from_methodology.py` now only adds a Tier C block for an in-scope ID that has
    none, and never changes an existing block. `--check` compares the Tier C blocks with today's host
    sheets; `--reorder` restores host order.
  - `validate_instrument.py` checks one file: every in-scope ID exactly once, in host order, tier A,
    B or C, and a `tiers` key. It fails if `indicators_generated.yaml` reappears.
  - `build_signatures.py`, `measure_prefix.py` and `report_coverage.py` read the one file.
- Why:
  - The user's call: the mapping logic treats every block the same, so one list ranked by index.
  - The mapping prompt reads only `indicators.yaml`, so the split would have hidden 38 indicators
    from it. This supersedes the late-morning `HANDOFF.md` note, which is now reworded.
- Verified:
  - A one-off merge script checked that every block equals its source apart from the wording change
    below, that the top-level keys are unchanged apart from the new `tiers`, that the order equals
    host order, and that split and reassemble reproduce the file byte for byte.
  - After the merge, the Tier C script reports "nothing to add", and `--check` finds no differences
    across 38 blocks.
  - Signatures, gold set and order file rebuild byte-identical. Every prompt size equals
    `evidence/prefix_sizes_2026-09-13.md`.
  - The validator passes.
  - In a scratch copy: removing 1.4 and 11.2 and re-running re-added both byte-identical, and an edit
    to 10.1 survived. Moving 12.9 to the top failed the validator's order check, and `--reorder`
    restored the original file byte for byte.

**instrument · Authorship wording corrected: the tiers differ in depth, not in who wrote them.**
- What:
  - Tier A `review_status` "human-authored Round 1 (2026-07-12)" became "Round 1 codebook
    (2026-07-12)".
  - Tier C `review_status` became "extracted by script from host sheets on 2026-09-13; not reviewed".
  - The same correction was made in the codebook header, `output/README.md`, `INSTRUMENT_NOTES.md`,
    the stage `README.md` and `START_HERE.md`, the `guide_refs.yaml` and `signature_spec.yaml` header
    comments, the docstrings of the validator, `build_gold.py` and `build_signatures.py`, and the
    coverage report legend. "Hand-reviewed" flags now read "reviewed in Round 1", and "hand-written"
    retrieval vocabulary now reads "curated (not mined)".
- Why: the user confirmed the Round 1 codebook was generated, not written by people.
- Verified: `review_status` is not rendered into the prompt, and the prompt sizes are unchanged.

**workspace · Workspace docs follow D11.**
- What: `README.md`, `HANDOFF.md`, `PLAN.md` (a "superseded" note on the 3B merge rule), `DECISIONS.md`
  (D11), the overnight report's update note, and `evidence/coverage_2026-09-13.md` (regenerated) and
  `label_flags_2026-09-13.md`.
- Why: they described two codebook files and "hand-authored" blocks.
- Verified:
  - Outside `drafting/`, a grep for `indicators_generated` finds only this changelog, D11, the
    report's update note, `PLAN.md`'s marked original text, and the validator's guard against the
    file coming back.
  - The "hand" and "human" wording left either names a real human task ("pending human review",
    "flag for human review") or is D2/D8 decision text that D11 explains.
  - `tools/audit_citations.py` now skips Tier C blocks, whose Guide sentences the validator checks.
    It still audits 423 lines and lists the same 30, now in host order, and
    `evidence/citation_audit_2026-09-13.txt` was rewritten in that order.

## 2026-09-13 (late morning)

**workspace · `HANDOFF.md`: the mapping stage must read both codebook files.** *(Superseded at midday: the
codebook is now one file, so the note was reworded.)*
- What: a new precondition in "When to hand off".
- Why: the codebook was split into `indicators.yaml` (23 blocks) and `indicators_generated.yaml` (38
  blocks), but the mapping prompt reads only the first (`stages/p3-map/src/p3map/mapping/prompt.py`
  line 20).
- Verified: a grep of `stages/p3-map/src` for either file name finds only that one read.

## 2026-09-13 (morning): the instrument moves into this folder

**workspace · The instrument's working copy moves from the worktree into `instrument/`. The drafting
material is archived in `drafting/2026-09-13/`, and `tools/` is added.**
- What:
  - `instrument/` is a copy of the worktree's `stages/p0-instrument/` (98 files).
  - `drafting/2026-09-13/` holds the session's drafts, the agents' inputs and the scripts (80 files).
    The two items already in `sources/` were not copied again.
  - `tools/validate.py` runs the validator with the Guide text and the finale repo switched on.
  - `tools/audit_citations.py` is the live citation audit.
  - `HANDOFF.md` says what goes where in the repo, and when.
  - `instrument/output/VALIDATION_2026-09-13.txt` and `evidence/VALIDATION_2026-09-13.txt` are
    replaced by a run from this folder (`python tools/validate.py --save`), after the changes below.
- Why: the user's call (D9). Instrument work lives in this folder and is sent to the finale repo when
  it is ready. The session folder the drafts sat in is temporary.
- Verified:
  - A recursive diff of `instrument/` against the worktree stage is empty.
  - Every archived file matches its source.
  - The four builders, re-run from a scratch copy, reproduce `output/` and `scripts/data/` byte for
    byte.
  - `python tools/validate.py` gives PASS, exit 0.

**instrument · `validate_instrument.py`: the mapping-stage checks work from outside the repo and compare
every file.**
- What:
  - `RDTII_FINALE_REPO` names the repo when the stage folder is not inside it. When the mapping stage
    can't be found, an INFO line now says so; before, the checks were skipped silently.
  - The vendored-copy comparison now covers `signatures/` and `gold/`; it used to compare top-level
    files only.
  - Comparisons ignore CRLF against LF line endings.
  - `--require-vendored` now fails when there is no vendored copy at all.
- Why:
  - The hand-off check has to run from this folder, and the old comparison would have passed a stale
    `signatures/` folder.
  - The first run against the main repo failed on `indicator_ids.py` because of line endings alone.
    The main repo's checkout has LF, the worktree's has CRLF, and git holds the same content for both.
- Verified:
  - A plain run from `instrument/` passes, with INFO lines for the two skipped checks.
  - `tools/validate.py` passes and reports "NOT re-vendored yet (78 files differ)": 64 files new, 9
    legacy signature files, 5 changed (`INSTRUMENT_NOTES.md`, `README.md`, `gold_set.jsonl`,
    `indicators.yaml`, `policies.yaml`). None differ by line endings alone.
  - `--require-vendored` fails, as it should while the repo still holds Round 1.

**instrument · `policies.yaml`: the host's wrong-section rule.**
- What: `citation_contract.section_rule` now carries the Instructions sheet's rule: "A real act cited
  to the wrong section scores zero" (finale template, Instructions sheet B22).
- Why: the workspace README lists seven host zero-score rules. Six were encoded overnight; this one was
  missed. Round 1's wording already required article and paragraph, but not the consequence.
- Verified:
  - The validator passes.
  - `citation_contract` is not rendered into the mapping prompt, so the prompt sizes in `evidence/` are
    unchanged.
  - No mapping-stage code reads the key.

**instrument · `output/README.md`: one line on `RDTII_FINALE_REPO`.**
- What: the regenerate section now says when to set it.
- Why: it documents the validator change above.
- Verified: n/a.

**workspace · Corrected citation audit: 30 lines to review, not 19.**
- What:
  - The overnight audit's country-name check never matched. Its pattern held two backspace characters
    where word boundaries were meant, from a shell quoting slip.
  - Fixed in `tools/audit_citations.py`.
  - `evidence/citation_audit_2026-09-13.txt` is replaced by the corrected run.
- Why: the evidence described a check that had not run.
- Verified:
  - The 19 earlier lines are all still listed.
  - The 11 new lines each name a country example that comes from a workbook row cited in the same line.
    Every one of those rows was looked up in the gold set and matches the line's indicator and score.
  - No wrong citation was found. The one wrong page citation found overnight stays corrected.

**workspace · Overnight report corrected and annotated.**
- What:
  - A note at the top of `REPORT_2026-09-13_overnight.md` points to this folder.
  - Concern 13 no longer says the workspace README denies that the host states the traps. The README
    was corrected on 2026-09-12 at 19:00, before the build.
- Why: the report is still the agenda for discussion, and it should not send anyone to fix a correct
  file.
- Verified: file timestamps of `README.md` (2026-09-12 19:00:40) and the report (2026-09-13 02:08).

---

## 2026-09-13 (overnight): built in the worktree `rdtii-rocky-finale-w3`, branch `w3-instrument-61`, uncommitted

Copied from that worktree's `docs/CHANGELOG_FINALE.md`, with `stages/p0-instrument/` shortened to
`instrument/`. All entries are tagged **instrument**. Nothing was vendored into
`stages/p3-map/contracts/instrument/`, and no mapping-stage code changed, so the mapping stage keeps
running on the Round 1 instrument.

**instrument · Step 0: `scripts/build_indicator_order.py` emits `output/indicator_order.yaml`, and the
finale template is copied to `reference/OUTPUT_TEMPLATE_FINAL_ROUND.xlsx`.**
- Why: the host's 62-ID order lived only in a test fixture, but the generator, the per-pillar prompt
  and the validator all need it. The file also carries:
  - the host exception notes
  - the host's "five mapping traps" (template rows 79–85)
  - the non-regulatory list
  - the practice-based list (3.4, 5.3, 9.1)
- Verified: the emitted order equals `HOST_ORDER` in `stages/p3-map/tests/test_indicator_ids.py` (62/62,
  same order). 61 are in scope; 6.5 is declared out.

**instrument · W3A: decimal IDs across the instrument.**
- What:
  - `rdtii_examples.py` now parses every pillar and reads IDs through `indicator_ids.normalize()`,
    three-level `12.4.x` IDs included. `indicator_code()` is gone.
  - It reads each sheet's extra columns by header: Note, Indonesia's update type, the Lao PDR and
    Russia verification questions, and Thailand's verification feedback.
  - `indicators.yaml`, `policies.yaml` and all signature files use decimal IDs. Signature files are
    named like `6.1.yaml`.
- Why: finale decision D1. `P6-I1` cannot express `12.4.1`, and float parsing merges `4.01` into `4.1`.
- Verified: the validator's hygiene check finds no legacy IDs in any output or data file.

**instrument · W3: host trap rows encoded; Tier A citations.**
- What:
  - The nine pillar 6–7 blocks gain template rows 80–84: 7.1/7.2 economy-level, 7.3 prescribed
    periods, 7.5 business records and court-order carve-outs, 6.2 storage locus, and 6.1/6.4
    unless-conditions.
  - Row 85 goes into `policies.yaml`: an amending act cited instead of the principal act scores 0.
  - Every Tier A rule line now ends with a host citation.
  - Guide page references are normalised to printed pages. Round 1 mixed printed and PDF numbers.
- Why: the host states these traps on the finale template, and 6.2, 7.1/7.2 and 7.5 are stricter
  there than in the Round 1 codebook.
- Verified: validator group 1c (host rows present on the right indicators; a citation on every Tier
  A/B line), and citations spot-checked against the Guide text.

**instrument · W3B: `scripts/build_indicators_from_methodology.py` generates
`output/indicators_generated.yaml` (Tier C).**
- What: 38 indicators get a codebook block built only from host text: the methodology category, the
  criteria as scoring branches, the possible scores, host exception notes, and the Guide's defining
  sentence (`scripts/data/guide_refs.yaml`). The generator refuses any ID whose criteria don't line up
  with its scores.
- Verified:
  - No refusals across the 61 IDs.
  - Validator group 1b machine-matches the category and score set for all 61.
  - The mapping-stage loader that would replace the `INDICATORS` literal is not done.

**instrument · W3E: signatures are data-driven.**
- What: `build_signatures.py` reads `scripts/data/signature_spec.yaml` and
  `scripts/data/curated_exemplars.yaml` (Round 1's SPEC and CURATED, migrated there). It builds one
  signature per in-scope ID: 61 files and 400 exemplars, each indicator drawing from at least two
  economies. Rows flagged suspect or host-marked are never exemplars.
- Why: 61 indicators' worth of Python dict literals is unmaintainable. And, contrary to the plan's
  assumption, the host workbooks have exemplars for every indicator (at least 9 coded rows each).
- Verified: every exemplar round-trips to its workbook row (validator group 4).

**instrument · W3F: Tier B drafts for 14 indicators.**
- What: 2.1, 2.3, 3.5, 4.9, 5.5, 8.1, 8.2, 8.3, 8.4, 9.1, 9.4, 12.3, 12.8 and 12.9 are appended to
  `indicators.yaml` between markers, with `review_status: draft ... pending human review`.
  - Drafted from the Guide, the Internal Guide FAQ, the methodology sheet, the Indicator Reference notes
    and the host rows.
  - Unresolved questions sit in a `review_notes` field, which is not rendered into the prompt.
- Why: the 3F priority list in the finale plan.
- Verified: a structural checker per pillar group, the validator's citation checks, and a heuristic
  citation audit that found and corrected one wrong page citation. That audit's country-name check did
  not run; see the morning entry above. **Not reviewed by a human.**

**instrument · W3: the gold set covers every coded host row.**
- What: `build_gold.py` writes 1,054 rows across all pillars: Round 1 AU/MY/SG 249, Round 2
  CN/IN/ID/LA/MN/RU/TH 805. Each row carries `baseline_round`, `pillar`, `host_verification` and
  `exemplar_for`. Flags come in four statuses:
  - suspect 2 and advisory 5: Round 1 flags, reviewed
  - host_marked 34: rows the host's own Thailand verification called "Not correct"
  - candidate 7: machine checks, unreviewed
- Why:
  - The finale's new economies are the Round 2 economies, and their rows are the known baseline.
  - `exemplar_for` lets an economy's evaluation exclude the rows its retrieval queries were built from.
- Verified: the row count equals a fresh parse of both workbooks, and every row round-trips (validator
  group 5).
- Note: `p3map/eval/evaluator.py` and `p3map/discovery/malaysia.py` hard-code flagged IDs and do not
  read `label_flag`.

**instrument · W3: `validate_instrument.py` finale edition, plus `report_coverage.py` and `measure_prefix.py`.**
- Why: the definition of done for 61 indicators; the C1b coverage table; and a measurement to replace
  D3's projected prompt size.
- Verified:
  - `RDTII_GUIDE_TEXT=... python -X utf8 scripts/validate_instrument.py` gives PASS, exit 0.
  - A single 61-indicator prompt prefix is 122,681 characters; per pillar, 10,065–29,070.
