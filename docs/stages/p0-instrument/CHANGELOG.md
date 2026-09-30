# Changelog — instrument workspace

Every change made in this folder, newest first. Each entry gives three things: what changed, why, and
how it was verified.

Each entry carries one of two tags:
- **instrument**: the change is inside `instrument/`. At hand-off, paste these entries into the repo's
  `docs/CHANGELOG_FINALE.md` under W3 (`HANDOFF.md` step 5).
- **workspace**: the change stays in this folder.

---

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
