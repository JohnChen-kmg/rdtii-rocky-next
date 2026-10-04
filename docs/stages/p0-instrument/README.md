# Instrument: understanding the RDTII pillars

This folder is the workshop for one task: the codebook that defines what the tool is looking for.
The codebook is the RDTII 2.1 framework turned into machine-readable scoring rules. Every
downstream stage reads it.

**Since 2026-09-13 the instrument itself lives here**, in `instrument/`. We build, check and edit it
in this folder, and send it to the finale repo when it is ready. `HANDOFF.md` says how and when, and
decision D9 says why.

## What this task owns

| Owns | Does not own |
| :---- | :---- |
| Indicator definitions and scoring values | Crawling, fetch policy, robots.txt |
| Scoring trees, branch by branch | OCR and text extraction |
| Trap rules that stop a plausible wrong citation | Mapping decisions taken at run time |
| Disambiguation between confusable indicators | The interface and the engine switch |
| Retrieval signatures used by the prefilter | Export writing, beyond supplying the ID vocabulary |
| The gold set used for evaluation | Cost logging |

## How we work

- **Edit the instrument here.** Its files are in `instrument\` and its code in `code\`. Together
  they mirror the repo's `stages\p0-instrument` folder, and the scripts run unchanged in either place.
  `code\README.md` explains how the code fits together.
- **Check after every change.** Run `python code\tools\validate.py` from this folder; exit 0 means
  consistent. It checks the Guide sentences word for word and compares with the finale repo.
- **Record every change** in `CHANGELOG.md`, tagged `instrument` or `workspace`.
- **When the contract or the workflow changes, update `NOTICE_FOR_OTHER_STAGES.md`** and send it again to
  the scraping, extraction, mapping and dashboard sessions.
- **Send it to the repo only at hand-off**, following `HANDOFF.md`. Never edit the repo copy
  directly.
- **Host documents stay here.** `sources\`, `drafting\` and `code\tools\` never go to the repo.

## Where things live

| Folder or file | What it holds | Goes to the repo? |
| :---- | :---- | :---- |
| `code\` | All the code, with `README.md` explaining the workflow | See its two subfolders |
| `code\scripts\` | Builders, the validator, the helper modules, report scripts, and `data\` (retrieval vocabulary, curated exemplars, Guide sentences) | Yes, as `stages\p0-instrument\scripts\` |
| `code\tools\` | `validate.py` (validator with the private checks on) and `audit_citations.py` (heuristic page check) | No, they read `sources\` |
| `instrument\` | The instrument's files: a mirror of `stages\p0-instrument` without its `scripts\` folder | Yes, at hand-off |
| `instrument\output\` | **The contract** the mapping stage reads: codebook, policies, ID order, signatures, gold set | Yes, twice: the stage and `p3-map\contracts\instrument` |
| `drafting\2026-09-13\` | Record of the overnight drafting: agent brief, drafts, inputs, scripts. Not a workspace | No |
| `drafting\2026-10-04\` | Record of the round that brought every indicator to pillar 6–7 depth: brief, drafts, checker, merge script, snapshots. Not a workspace | No |
| `sources\` | Read-only host documents and Round 1 records, with a SHA-256 manifest | No |
| `evidence\` | Proof artefacts the submission quotes | No, quoted from |
| `notes\` | Working notes and the label review queue | No |
| `HANDOFF.md`, `CHANGELOG.md` | How to send it, and what changed | Changelog entries tagged `instrument`, yes |
| `NOTICE_FOR_OTHER_STAGES.md` | What the other stages must know about contract and workflow changes, with a part for each stage | No; other stages read it from here |
| `REPORT_2026-09-13_overnight.md` | The overnight build report and the ranked concerns | No |
| `REPORT_2026-10-04_parity.md` | What the 4 October round changed, how it was checked, and what is still open | No |

Where each artefact sits:

| Artefact | Path |
| :---- | :---- |
| Ordered ID list, 62 listed and 61 in scope | `instrument\output\indicator_order.yaml` |
| Codebook: all 61 blocks in host order, grouped by pillar, each with its `tier` | `instrument\output\indicators.yaml` |
| Cross-cutting rules | `instrument\output\policies.yaml` |
| Retrieval signatures | `instrument\output\signatures\<ID>.yaml` |
| Gold set | `instrument\output\gold\gold_set.jsonl` |
| Definition of done | `code\scripts\validate_instrument.py`, exit 0 means consistent |
| Retrieval vocabulary and curated exemplars | `code\scripts\data\signature_spec.yaml`, `code\scripts\data\curated_exemplars.yaml` |
| Builders | `code\scripts\build_indicator_order.py`, `build_indicators_from_methodology.py`, `build_signatures.py`, `build_gold.py` |
| Helpers: workbook parser, decimal ID rules, codebook file layout | `code\scripts\rdtii_examples.py`, `indicator_ids.py`, `codebook_file.py` |

**The mapping stage's copy.** It reads a vendored copy at
`C:\Users\woshi\Desktop\rdtii_rocky_next\stages\p3-map\contracts\instrument`, and the ID helper has
a second copy at `stages\p3-map\config\indicator_ids.py`. Both hold the instrument as handed off on
29 September until the next hand-off. `HANDOFF.md` explains which of the repos on this machine is
which.
- `code\tools\validate.py` compares `instrument\output\` with the contract copy, file by file with
  subfolders included, and reports how many files differ.
- `--require-vendored` turns that report into a failure. Use it after hand-off.
- The repo test `test_vendored_copy_is_byte_identical_to_canonical`, in
  `stages\p3-map\tests\test_indicator_ids.py`, compares the two copies of `indicator_ids.py`.

**Repo documentation.** It stays in the repo. The index of where each function lives is
`C:\Users\woshi\Desktop\rdtii_rocky_next\docs\CODE_MAP.md`. Instrument changes reach the repo's
`docs\CHANGELOG_FINALE.md`, under W3, at hand-off.

## Marks this task carries

| Criterion | Points | How this task earns them |
| :---- | ----: | :---- |
| C1b regulatory domain coverage | 15 | Pillars 6 and 7, the mandatory pair, are the required scope since 2026-09-12. The "further RDTII domains" share is earned only if optional pillars are added |
| C2a framework alignment at scale | 10 | One vocabulary and one scoring tree per indicator, applied identically in every economy |
| C2b citation fidelity at scale | 10, shared | The traps are what stop a wrong-but-plausible citation. This task underwrites C2b, it does not own it |

## State as of 2026-10-04

| Item | State | Verified against |
| :---- | :---- | :---- |
| Indicators covered | 61 of the 62 the host lists; 6.5 declared out of scope | `instrument\output\indicator_order.yaml` |
| Codebook | one file, `indicators.yaml`: all 61 blocks in host order, every block with the same elements (D11, D15) | validator groups 1 and 1d |
| Depth | Tier A 9 (pillars 6 and 7, the Round 1 codebook, used in the Round 1 run and the 30 September submission); Tier B 52 (every other indicator, drafted at the same depth, **not yet reviewed**); no Tier C | each block's `tier` field |
| Machine-readable marks | `polarity: inverted` on 14 blocks; `level: economy` with `framework_name` on 13; `null_statement` on all 61 | `policies.yaml` `indicator_sets`; validator |
| Traps | written on both blocks they concern; 0 one-sided references | validator INFO line |
| Indicator IDs on disk | decimal text everywhere in `instrument\` | validator hygiene check |
| Signature files | 61, named by decimal ID, 401 exemplars | `instrument\output\signatures\` |
| Gold rows | 1,054: every coded host row, ten economies, all pillars | `instrument\output\gold\gold_set.jsonl` |
| Reviewed label flags | 53 suspect, 162 advisory. 7 from Round 1; 208 set while drafting on 4 October, not confirmed by a person | `code\scripts\data\label_flags.yaml`; `evidence\label_flags_2026-10-04.md` |
| Validator | PASS, exit 0, Guide sentences checked for all 61 | `python code\tools\validate.py` |
| Host zero-score rules | all seven encoded: rows 80–84 on the Tier A blocks, row 85 and the wrong-section rule in `policies.yaml`, the government-data exception on the blocks and in `policies.yaml` | validator group 1c; `CHANGELOG.md` |
| Pillar 6–7 prompt | unchanged by the 4 October round: 31,929 characters, byte-identical | `evidence\prefix_sizes_2026-10-04.md` |
| Repo copy | the instrument as handed off on 29 September (repo commit `bf2bb3e`); the 4 October round is **not** in the repo (45 files differ) | `python code\tools\validate.py` INFO line |
| Hand-off rehearsal | the 4 October instrument copied into an export of `rdtii_rocky_next` (commit `2edcf44`): mapping tests 450 passed and interface tests 216 passed, as before the copy; the mapping prompt builds for each of the 61 indicators | `HANDOFF.md`, "Where things stand" |
| Mapping stage | reads decimal IDs and all 61 blocks; automates pillars 6 and 7 unless a run sets `INDICATORS_SCOPE` | `stages\p3-map\config\settings.py` in the repo |
| Coverage marks (D14, D16) | in `indicator_order.yaml`: 9 automated (pillars 6 and 7), 52 manual, each with its reason and the nature of its answer; they agree with the coverage register | validator INFO line; `code\scripts\data\coverage.yaml` |
| Timor-Leste | the one economy mapped against all 52 other indicators (run of 27 September): 13 produced scored rows, 39 a "no provision found" row | `notes\timor_leste_all_indicator_run.md` |

The gap in one line: every scoreable indicator now has a full-depth block, but only the nine
pillar 6 and 7 indicators have been used and evaluated, and nobody has reviewed the other 52.
`REPORT_2026-10-04_parity.md` lists what that leaves open.

## The five mapping traps

These are the substance of the task. **The host states them itself**, verbatim, at the foot of the
Indicator Reference sheet in `OUTPUT_TEMPLATE_FINAL_ROUND.xlsx`, rows 79 to 85, under the heading "The
five mapping traps checked every round". An earlier edit to this file said otherwise. That edit was
wrong: it checked the Instructions sheet and the Exceptions column but not the foot of the sheet. Our
own reading of the RDTII 2.1 guide and the Round 2 methodology criteria, recorded in
`instrument\output\INSTRUMENT_NOTES.md`, agrees with the host and adds detail.

"Checked every round" means the secretariat marks against these. A model that has not been told them
will produce citations that read well and score zero.

| Indicator | The trap | The host's rule, rows 80 to 84 |
| :---- | :---- | :---- |
| 7.1 and 7.2 | Level and polarity | Economy-level, answered once per economy. **Per-provision citations of a data-protection or cybersecurity act tagged 7.1 or 7.2 are not discoveries and score zero.** Our addition: polarity is inverted, so a comprehensive law scores 0 and no law scores 1 |
| 7.3 | Minimum against maximum | Needs a specified minimum duration such as "5 years". **A "prescribed period" with no number, a notification deadline or an appeal window is not a retention rule.** Our addition: "no longer than necessary" is a maximum-period rule and scores 0 |
| 7.5 | Data type and authorisation | Government access to personal data without independent judicial authorisation. **Not generic inspection of business records, and not a secrecy duty with a court-order carve-out** |
| 6.2 | Location, not record-keeping | Data stored in-country, **a storage locus, not general record-keeping**. Our addition: not a retention rule and not an infrastructure mandate |
| 6.1 against 6.4 | Ban against condition | "Must not transfer UNLESS [condition]" is a conditional flow regime, 6.4, not an outright ban, 6.1. The host repeats this in the Notes cell of its own example row: "never 6.1" |

Two further zero-scoring rules the host states:

| Rule | Where the host states it |
| :---- | :---- |
| **Drafts, repealed provisions, and an amending act cited in place of the principal act all score zero** | Indicator Reference, row 85 |
| **A real act cited to the wrong section scores zero** | Instructions sheet, Article / Section field rule |

And one rule cuts across five indicators. Measures applied to government data are not scored under
6.1 to 6.4 or 7.3. It is the Exceptions note on exactly those five Indicator Reference rows.

**Status, 2026-09-13.** All seven rules are in the instrument in the host's wording.
- Rows 80 to 84 sit on the Tier A blocks in `instrument\output\indicators.yaml`, each cited as
  "Indicator Reference row N". The validator checks each row is on the right indicator.
- Row 85 and the wrong-section rule are in `instrument\output\policies.yaml`.
- The government-data exception is on the 6.1 to 6.4 and 7.3 blocks and in `policies.yaml`.

Still to decide: several of these are stricter than the Round 1 codebook. The overnight report names
6.2, 7.1 and 7.2, and 7.5. In particular, Round 1's argued 6.2 scores for Singapore, Malaysia and
Australia may not survive "a storage locus, not general record-keeping". This is concern 1 in
`REPORT_2026-09-13_overnight.md`.

## 6.5 is out of scope, on the host's own authority

Indicator 6.5 asks whether an economy is party to an agreement with binding commitments on data
transfer. That is a treaty-participation check, not national legislation. Two host facts support the
exclusion. The methodology sheet header says gaps in the ID sequence are intentional because those
indicators are non-regulatory. The methodology sheet then carries no scoring criteria row for 6.5 at
all, which is why it holds 61 indicator rows against the Indicator Reference sheet's 62.

Consequence for wording. The instrument targets 61 scoreable indicators and declares 6.5 excluded in
`instrument\output\indicators.yaml` under `scope.out_of_scope`. Write "61 scoreable of 62 listed". Do not write
"62 scored".

**The other thirteen non-regulatory indicators are not on the finale list at all.** RDTII 2.1 has
fourteen non-regulatory indicators:

| Data source | Indicators |
| :---- | :---- |
| WITS database | 1.1, 1.2 |
| V-Dem database | 9.2 |
| Treaty and agreement status | 1.3, 2.4, 4.4, 4.7, 4.8, 5.6, 6.5, 12.10 to 12.13 |

The host says twice that no extraction tool is needed for them:
- The Non-regulatory indicators note, p.1: "an automated data retrieval method is not required".
- The Internal Guide, p.8: "No need to develop data-extraction tools".

Only 6.5 appears in the finale template's list. None of the fourteen has an instrument entry, and
`policies.yaml` tells the tool to write no rows for them. Decision D10 records this.

Three indicators sit between the two groups: 3.4, 5.3 and 9.1 are practice-based. They stay in scope,
but they need evidence of practice that a legal-text pipeline may not collect.

## The host template contradicts itself on ID format

Verified in `C:\Users\woshi\Desktop\RDTII Finale Plan\1_Rules\Final_Round\OUTPUT_TEMPLATE_FINAL_ROUND.xlsx`.

| Sheet and cell | What it says |
| :---- | :---- |
| Indicator Reference | Lists every ID as decimal text, `1.4`, `6.1`, `12.4.1` |
| Instructions, the INDICATOR IDs block | Write the code exactly: 6.1, 6.4, 7.3, 12.3, 12.9. Not "P6-I1" |
| Output Data, row 5, column E | Column hint reads: RDTII indicator code, e.g. "P6-I1", "P6_I2" |
| Output Data, column O | Pillar is derived from the Indicator ID by formula, so the format decides whether the Coverage Matrix populates |

The working answer is decimal text. Two sheets say so and one column hint disagrees. The Indicator
Reference sheet is the authority on what the IDs are, the Instructions sheet says it in words, and
the finale brief says to write 6.1 rather than P6-I1. This belongs in the secretariat
questions as a sub-point of existing question 4 in
`C:\Users\woshi\Desktop\RDTII Finale Plan\3_Final_Stage\OPEN_QUESTIONS_FOR_HOST.md`. That question
asks only whether the format change is retroactive. It does not yet name the contradiction inside
the finale workbook itself.

One more oddity, now recorded under question 4. Three host documents warn that `12.10` collapses to
`12.1` if typed as a number. No indicator `12.10` exists in the Indicator Reference sheet. The real
trailing-zero pair is `4.01` against `4.1`, which `indicator_ids.py` already tests.

## New from the host templates, read line by line on 2026-09-12

Full detail is in `C:\Users\woshi\Desktop\RDTII Finale Plan\3_Final_Stage\REQUIREMENTS.md`, section
"Read line by line from the primary host documents". What binds this task:

| Requirement | Source | Consequence for this task |
| :---- | :---- | :---- |
| **The live test is one economy, one pillar, two indicators**, and "may be a pillar you were never asked to work" | Workbook, Instructions sheet | Every one of the 61 scoreable indicators must be usable on the day, at least at Tier C. A pillar with no codebook entry is a live-test zero. This makes 3B the most important step in the plan, ahead of any Tier B authoring |
| **Seven zero-scoring rules** stated by the host | Indicator Reference rows 79 to 85, Instructions sheet | See the trap section above. Encode the host's exact wording |
| **Flagging low confidence is treated as a strength** | Instructions sheet, Confidence field rule | Supports capping Tier C confidence and disclosing depth. It is a scoring advantage, not only honesty |
| **The README must state a confidence calibration threshold**, below which a human should check | README template, Known Limitations | The instrument's depth tier is the natural input. Tier C rows are the ones a human checks first |
| **The Indicator Reference sheet is "taken from the RDTII 2.1 Methodology in the Round 1 database"** | Instructions sheet | Our plan reads the methodology sheet from the Round 2 workbook. Before 3B, confirm the two methodology sheets agree cell for cell, or read the one the host names |
| **NEW means not in the 2025 baseline you hold** | Instructions sheet | The gold set must extend to the seven Round 2 country sheets, so NEW and KNOWN can be tagged for the live-test economies. Viet Nam and Kazakhstan have no sheet, so every find there is NEW |
| **The live test's short note asks which indicator a ministry should check first** | Live test short note, section 5 | The depth tier answers this directly on the day. Tier C indicators are the honest answer |

## Borrow from Round 1

Round 1 already answered most of what this task has to answer again. Every path below was checked on
2026-09-12 and exists. Since 2026-09-13, read-only snapshots of most of these files are in
`sources\round1_record\`, so the paths below are their origins. Take the shape or the fact; don't edit
the snapshots.

### Reusable as a template, not just reference

These two are worth more than every reference row below them. Authoring a Tier B indicator is filling
in an existing format, not inventing one.

| Path | Why open it |
| :---- | :---- |
| `instrument\output\indicators.yaml` | The nine Tier A blocks are the shape every block must match, and the 52 Tier B blocks follow it. Copy one, keep every key, fill in the new indicator. This is the single highest-value file in the task |
| `code\scripts\data\signature_spec.yaml` and `curated_exemplars.yaml` | The curated half of a signature, not mined from the workbooks (keywords, definition text, law types, scope patterns, negative signals), and the workbook sheet and row of each exemplar with its teaching note. Round 1 kept these as the `SPEC` and `CURATED` dicts in `build_signatures.py`. All 61 indicators already have an entry in each |

### Reference, beside the code

| Path | Why open it |
| :---- | :---- |
| `stages\p0-instrument\output\INSTRUMENT_NOTES.md` | The paragraph separating what the validator machine-checks from what a human transcribed. Reuse that wording for the Tier C disclosure. Line 113 is stale, it still quotes a 2,616-law corpus |
| `stages\p0-instrument\output\VALIDATION_2026-07-16.txt` | Eight lines. The exact shape of the transcript `evidence\` owes for the merged 61-indicator run |
| `stages\p0-instrument\START_HERE.md` | The regeneration order after a source-workbook change: `build_gold.py`, `build_signatures.py`, validator, re-vendor. Step 3A follows that order. Stale on folder names, it still calls the stage `rdtii-p0-instrument/` |
| `stages\p0-instrument\README.md` | The one-command health check written for a reviewer. Its expected-output paragraph needs the same rewrite from 9 indicators to 61 |
| `stages\p0-instrument\PLAN.md` | Section 5 gives the A to E build stages and names the four traps that were encoded first. Marked complete on 2026-07-12. Its 2,616-law figure is stale |
| `stages\p0-instrument\INTERFACE_CONTRACT.md` | 612 lines, the current copy of the frozen spine. Section 4 is the shared instrument spec, so every field step 3C moves out of mapping code has to be declared there before another stage may read it |
| `stages\p0-instrument\TOOL_WORKFLOW_PROPOSAL.md` | Stages 3 and 4 explain why one instrument feeds both triage and mapping. Useful for deciding what a Tier C signature is allowed to omit. Marked proposal, and its corpus figures are stale |

### Reference, in the planning folder

| Path | Why open it |
| :---- | :---- |
| `C:\Users\woshi\Desktop\RDTII Finale Plan\2_What_We_Built\Reference\Stage_Reports\p0\P0_COMPLETION_REPORT_2026-07-12.md` | Section 3 lists what the build found beyond the four known traps, including the 6.4 personal-data asymmetry and the dual-recording rule. That is free disambiguation material for step 3F. Its folder paths are dead, the stage was a standalone folder then |
| `C:\Users\woshi\Desktop\RDTII Finale Plan\2_What_We_Built\Self_Assessment\03_Submission\briefs\STATION_0_P0_INSTRUMENT.md` | Section 2 puts an artefact path beside every number. Copy that habit into `evidence\`. Its own paths are dead twice, both `rdtii-p0-instrument\` and `RDTII Judge\` are gone, though the filenames it cites still resolve under `01_Findings\` |
| `C:\Users\woshi\Desktop\RDTII Finale Plan\2_What_We_Built\Reference\Stage_Plans\0_Interfaces_and_Contracts.md` | The frozen spine all stages key off. Superseded in one line: its section 2.3 still names PyMuPDF, where the repo copy names pypdfium2 and the licence fix has landed. Prefer the repo copy |
| `C:\Users\woshi\Desktop\RDTII Finale Plan\2_What_We_Built\Reference\Stage_Plans\round1_plan\DISCLOSURES.md` | The honesty habit, never present an estimate as a measurement. Item (h) already discloses a host-template inconsistency without silently resolving it, which is the precedent for how D7 gets written up |
| `C:\Users\woshi\Desktop\RDTII Finale Plan\2_What_We_Built\Self_Assessment\01_Findings\LEAKAGE_AUDIT_2026-07-16.md` | Soft channel 1 says signature exemplars are Round 1 baseline rows, so retrieval is steered toward provisions the baseline already describes. Tier B exemplars inherit that channel. The live test is sealed, so the disclosure has to be repeated, not assumed |
| `C:\Users\woshi\Desktop\RDTII Finale Plan\2_What_We_Built\Self_Assessment\01_Findings\GROUND_TRUTH_2026-07-16.md` | The reconciled record of what P0 actually delivered, built from artefacts and git history rather than from completion reports. Use it to confirm the 9, 51 and 57 counts. Where a figure also appears in `AUTHORITATIVE_NUMBERS.md`, that file wins |

That `01_Findings\` directory holds 19 files. The two above are the ones that bind this task. The
other 17 are audits and scorecards for the later stages.

## First thing to do

**Revised 2026-10-04.** The instrument side of `PLAN.md` is built, and every indicator is at pillar
6–7 depth (D15). What is left:

1. **Decide.** `REPORT_2026-10-04_parity.md` section 4: whether any of the 52 manual indicators should
   be promoted to automated, when to hand off, the five uncertain economy-level calls, and the 51
   suspect flags.
2. **Review.** Read the 52 Tier B blocks, starting with the 13 that produced filed rows for
   Timor-Leste (`notes\timor_leste_all_indicator_run.md`). Open questions are in each block's `review_notes` and in
   `drafting\2026-10-04\drafts\<group>\notes.md`; `evidence\citation_audit_2026-10-04.txt` lists the
   lines worth checking against their cited page. After each edit, run `python code\tools\validate.py`
   and `python code\tools\audit_citations.py`, and add a `CHANGELOG.md` entry.
3. **Hand off.** Follow `HANDOFF.md`. The mapping stage needs one change first for the new
   economy-level indicators (the notice, section "Update of 4 October").
