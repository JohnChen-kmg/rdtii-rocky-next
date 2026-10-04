# Progress — the instrument (p0-instrument), 4 October 2026

The first instrument file in this folder. It covers the stage from the start of the finale work
(13 September) to today, with the weight on 4 October. Written from the files; every count can be checked
against the file named beside it. Workshop: `Desktop/rdtii-finale-0-instrument/`. The instrument:
`instrument/output/` there. Code: `code/scripts/`. Check: `python code/tools/validate.py`, PASS, exit 0
(`evidence/VALIDATION_2026-10-04.txt`). Record of every change: the workshop's `CHANGELOG.md`; decisions
D1 to D16 in its `DECISIONS.md`.

**The stage is not closed.** The repos hold the instrument as handed off on 29 September, and the
30 September submission ran on it. Everything dated 4 October below is in the workshop only.

---

## 1. Where it stands

| Item | State on 4 October | Check |
| :---- | :---- | :---- |
| Indicators with an instrument | 61 of the 62 the host's sheet lists. 6.5 is out of scope; the other 13 non-regulatory numbers are not on the sheet and get no instrument (D10) | `indicator_order.yaml` |
| Depth | **All 61 at the depth of pillars 6 and 7.** Tier A 9 (pillars 6 and 7), Tier B 52, Tier C 0. At submission it was A 9, B 14, C 38 | each block's `tier`; validator PASS line |
| Review | The nine Tier A blocks were used and evaluated in the filed runs. **No person has read the 52 Tier B blocks** | each block's `review_status` |
| One shape | Every block carries the same 18 keys; the validator fails if one is missing | validator group 1d |
| Retrieval | 61 signature files, 401 exemplars, 5 to 8 per indicator | `signatures/` |
| Gold set | 1,054 host rows, 9 to 55 per indicator. Flags: 53 suspect, 162 advisory, 34 host-marked, 7 candidate | `gold/gold_set.jsonl`; `evidence/label_flags_2026-10-04.md` |
| Coverage marks | 9 automated (pillars 6 and 7), 52 manual, as decided on 20 September (D14). They agree with `3_Final_Stage/COVERAGE_AND_MANUAL_CHECKS.md` for all 61 | validator INFO line |
| Pillar 6–7 mapping prompt | 31,929 characters, byte-identical to the one the submission ran on | `evidence/prefix_sizes_2026-10-04.md` |
| In the repos | The 29 September instrument. 45 files differ from the workshop's | validator INFO line |
| Hand-off | Rehearsed against `rdtii_rocky_next`; every test passes before and after (section 5) | the workshop's `HANDOFF.md` |

---

## 2. What happened, in order

| Date | What | Record |
| :---- | :---- | :---- |
| 13 September | The instrument rebuilt for the finale: 61 indicators, decimal text IDs, one codebook file in host order. 9 blocks at full depth from Round 1, 14 drafted at that depth, 38 restating host text only. Moved into the workshop, which became its working home | D9, D11, D12; `REPORT_2026-09-13_overnight.md` |
| 20 September | The tool automates pillars 6 and 7; every other indicator is "manual" and can still be run on request | D13, D14; the coverage register |
| 29 September | **First hand-off.** Repo commit `bf2bb3e`, merged as `ad27d1f`. The submission ran on this instrument | `STAGE_RESULT_p3-map_2026-09-29.md`, section 5 |
| 4 October | **Every indicator at pillar 6–7 depth.** The 38 host-text-only blocks rewritten, the 14 drafted blocks completed, the nine pillar 6–7 blocks given the non-rendered keys they lacked | D15; `REPORT_2026-10-04_parity.md` |
| 4 October, later | Coverage marks written into `indicator_order.yaml` from the register. This is mapping's request R1 | D16 |
| 4 October, evening | The hand-off target corrected to `rdtii_rocky_next` and the hand-off rehearsed there | `HANDOFF.md`; `CHANGELOG.md` |

---

## 3. What exists

### The files, in `instrument/output/`

| File | How many | What it holds |
| :---- | :---- | :---- |
| `indicators.yaml` | 1 file, 61 blocks | The codebook: one block per indicator, in host order under pillar banners |
| `policies.yaml` | 1 file, shared | Cross-cutting rules (inclusion, source hierarchy, citation contract, scoring policy, edge cases) and `indicator_sets` |
| `indicator_order.yaml` | 1 file, 62 entries | Host order, pillar labels, scope status and the coverage marks |
| `signatures/<ID>.yaml` | 61 files | Keywords, law types, scope patterns, negative signals and exemplars for retrieval |
| `gold/gold_set.jsonl` | 1,054 rows | Every coded host row, each with a `label_flag` |
| `INSTRUMENT_NOTES.md`, `README.md`, `VALIDATION_*.txt` | — | Notes, and the validator's transcript |

### One indicator block: the keys every block carries

| Key | What it holds | In the mapping prompt |
| :---- | :---- | :---- |
| `id`, `name` | Host ID as text, host name | Yes |
| `question`, `definition` | What is asked; the Guide's definition | Yes |
| `scoring` | Scale type and allowed values | Yes |
| `scoring_tree` | 2 to 5 "if … then score" branches (166 in total) | Yes |
| `coding_rules` | 2 to 9 rules for coding a measure (381) | Yes |
| `exceptions` | Host exceptions; an empty list on 24 blocks | Yes |
| `disambiguation` | 2 to 14 traps against sibling indicators (382), each written on both blocks it concerns | Yes |
| `pillar`, `tier`, `review_status` | Pillar, depth tier, drafting history | No |
| `category_official`, `weight` | Host category name, weight in the pillar | No |
| `scoring_features` | What moves the score; filled on 29 blocks | No |
| `guide_examples` | The Guide's country examples; filled on 42 blocks (156) | No |
| `null_statement` | What an absence row says | No |
| `sources` | Guide heading and pages, FAQ pages, methodology row, template row | No |

### What depends on the indicator

IDs are the host's text IDs: `4.01` is Guide 4.1, `4.1` is Guide 4.10, `12.01` is Guide 12.1.

| Element | Meaning | Indicators |
| :---- | :---- | :---- |
| `polarity: inverted` | An absent framework scores 1 | 14: 4.2, 4.5, 4.6, 4.1, 5.1, 5.4, 5.7, 7.1, 7.2, 8.1, 8.2, 11.1, 12.5, 12.9 |
| `level: economy` with `framework_name` | Answered once per economy, not per law | 13: the 14 above without 12.5 |
| `review_notes` | The drafter's open questions (218) | 39 blocks, none in pillars 6 and 7 |
| `scoring` binary, 1 / 0 | | 23: 3.2, 3.3, 3.5, 5.5, 5.7, 6.3, 7.3, 7.5, 9.3, 10.4, 11.1, 11.4, 12.2, 12.3, 12.4.1 to 12.4.7, 12.8, 12.9 |
| `scoring` 1 / 0.5 / 0 | | 33: every block not named in this group of rows |
| `scoring` on another scale | | 3.1, 5.2 (1 / 0.8 / 0.5 / 0); 3.4, 5.4 (1 / 0.5 / 0.25 / 0); 1.4 (five steps of 0.25) |
| `weight` null | Seven sub-indicators share one Guide weight | 12.4.1 to 12.4.7 |
| `coverage: automated` | In the default run | 9: pillars 6 and 7 |
| `coverage: manual`, reason `scope` | Runs on request, with a manual-check notice | 46 |
| `coverage: manual`, reason `practice` | Needs practice or external evidence | 6: 1.4, 3.4, 5.3, 9.1, 11.4, 12.6 |
| Counting rule, in prose only | The score depends on how many measures the economy has | 14: 1.4, 2.1, 2.3, 3.1, 4.3, 4.9, 5.2, 5.3, 6.1, 6.2, 9.4, 10.1, 10.2, 10.3 |

Where each indicator's answer lives, by the register's first code (`answer_nature`): primary legislation
22, delegated legislation 16, a regulator's instrument 17, a technical standard 1 (11.4), a fact or
practice 3 (3.4, 5.3, 9.1), a trade posture 2 (1.4, 12.6).

---

## 4. How good it is

### How the 4 October round was made and checked

- **Drafted** by seven drafting agents, one per pillar group, from the host documents and under one
  brief. `drafting/2026-10-04/` in the workshop holds the brief, the drafts and each group's notes.
- **Checker on every draft:** every rule line carries a citation; every cited Guide page and host row
  exists; every Guide example's country is on its cited page; one scoring branch per host score.
  0 errors in all seven groups.
- **Both sides of every trap:** 37 one-sided references found after the first pass, all closed. The
  validator reports 0.
- **Scoring branches read against the host criteria** for the 38 rewritten blocks. They line up.
- **Validator:** PASS, exit 0. It now also checks that every block has the same keys, that the marks in
  `policies.yaml` match the blocks, and that the coverage marks match the register.
- **Rebuild:** every built file comes out byte for byte the same from a full rebuild.
- **Pillars 6 and 7 untouched where it matters:** the prompt is byte-identical, built with the mapping
  stage's own code, and the nine signature files are identical to the repo's.

### What is weak, stated plainly

- **The 52 Tier B blocks are drafts.** Machine checks confirm that citations exist, not that each rule
  says what its source says. A heuristic audit of 1,272 rule lines listed 231 for reading; one group of
  them was read and held, the rest were not (`evidence/citation_audit_2026-10-04.txt`).
- **208 of the label flags were set while drafting** and are not confirmed by a person. Three suspect
  rows are their economy's only row for that indicator.
- **19 indicators have no unflagged score-1 row** in the host data, so their top branch rests on the
  Guide and the methodology sheet alone.
- **Five economy-level calls are uncertain:** 4.2, 4.6, 5.1, 11.1, 12.9. The host states the
  once-per-economy rule only for 7.1 and 7.2.
- **Search keywords are English only**, for every pillar.
- **Twelve places where host documents disagree with each other** are written into the blocks and
  flagged, not resolved (`REPORT_2026-10-04_parity.md`, section 6). Each needs a host ruling.

---

## 5. The hand-off, rehearsed and not made

The target is `Desktop/rdtii_rocky_next`, the working copy since 3 October. `rdtii_rocky_finale_9.30` is
the submission repository and `rdtii-rocky-finale` the development history; neither receives it unless
the developer says so.

The rehearsal copied the new files into an export of `rdtii_rocky_next` at commit `2edcf44`. No repo was
touched.

| Check | Before the copy | After |
| :---- | :---- | :---- |
| Mapping tests (`stages/p3-map`) | 450 passed, 9 skipped | 450 passed, 9 skipped |
| Interface tests (`interface/tests`) | 216 passed, 17 skipped | 216 passed, 17 skipped |
| Pillar 6–7 prompt | 31,929 characters | identical, same SHA-256 |
| Automated set, as mapping and the interface resolve it | the nine of pillars 6 and 7 | the same nine |
| Interface indicator picker | tiers A 9, B 14, C 38 | tiers A 9, B 52, C 0 |
| Mapping prompt for one indicator at a time | not run | builds for each of the 61 |
| Mapping prompt for all 61 together | not run | builds, 322,081 characters |

One thing the rehearsal could not catch: `interface/tests/test_map_start.py` line 29 pins the old tier
counts and is skipped in an export. It will fail in the working copy until it reads
`{"A": 9, "B": 52, "C": 0}`.

A run can read the new files before any copy, by setting `INSTRUMENT_DIR` to the workshop's
`instrument/output` and naming indicators in `INDICATORS_SCOPE`.

---

## 6. What the other stages inherit

**Mapping.**
1. `rollup.py` knows the framework's name only for 7.1 and 7.2. For the eleven new economy-level
   indicators the cell ends "pending". The blocks now carry `framework_name`.
2. Its fixed 1 / 0.5 / 0 scale does not fit 5.4 or the binary 5.7, 11.1 and 12.9.
3. Twelve indicators outside pillar 6 score by counting measures; the roll-up counts only for 6.1
   and 6.2.
4. 12.5 is inverted but not binary. For 11.2, an absence should not default to 0.
5. Prompt size: a two-indicator scope is 18,605 to 22,101 characters, smaller than the pillar 6–7
   prompt. All 52 other indicators in one prompt is 298,967, three times its earlier size.
6. The evaluator does not read `label_flag`, so 53 suspect rows still count as gold.
7. R1 (coverage marks) is delivered. R2 (the gold set as the NEW/KNOWN baseline) and R3 (source-language
   keywords) are open.

**Interface.**
1. After the copy, the picker shows 52 indicators as "not reviewed" and none as "host criteria only".
2. The pinned test above, and the sentence in the repo `README.md` (Known Limitations) that calls the
   other blocks "host-criteria-only".
3. `review_notes` must never be shown as host text.

**Scraping.** Many answers outside pillars 6 and 7 sit in regulators' instruments the crawler does not
collect. 1.4 needs WTO trade-remedy notifications (scraping's R4, open).

**Extraction.** Nothing new.

**This folder.** In `3_Final_Stage/COVERAGE_AND_MANUAL_CHECKS.md` the Tier column is out of date for 38
indicators. It was not edited from the instrument side. The Timor-Leste rows of 27 September were made
with the old blocks: 13 of the 52 indicators produced scored rows, and a re-run would not give the same
rows, since four of those 13 (5.1, 5.4, 5.7, 12.9) are now answered once per economy.

The full list of contract changes is the workshop's `NOTICE_FOR_OTHER_STAGES.md`, "Update of 4 October
2026".

---

## 7. Decisions waiting on the developer

1. **Make the hand-off now, or after review.** It is safe for pillars 6 and 7 either way.
2. **Whether the submission repository also receives it,** given that its tag is what runs on
   15 October.
3. **Whether any of the 52 moves to "automated".** One line in `code/scripts/data/coverage.yaml`.
4. **Who reads the 52 Tier B blocks, and in what order.** Suggested: the 13 indicators with Timor-Leste
   findings first (2.1, 2.3, 3.3, 3.5, 5.1, 5.4, 5.7, 8.3, 8.4, 12.4.4, 12.5, 12.8, 12.9).
5. **The five uncertain economy-level calls** in section 4.
6. **Which of the twelve host contradictions go to the secretariat.**

---

## 8. Deliberately not done

- No file was copied into any repo, and nothing was committed.
- No indicator was promoted to automated. D14 stands.
- The 14 non-regulatory indicators have no instrument, by decision (D10).
- No source-language keywords, and no rule for reading the gold set as a NEW/KNOWN baseline.
- The coverage register was not edited.
- The retired worktree `rdtii-rocky-finale-w3` was not removed.

---

## 9. Where everything is, in the workshop

| What | Where |
| :---- | :---- |
| The instrument | `instrument/output/` |
| Builders and the validator | `code/scripts/`; how they fit together, `code/README.md` |
| Hand-off steps and the rehearsal | `HANDOFF.md` |
| Contract changes, for the other stages | `NOTICE_FOR_OTHER_STAGES.md` |
| The 4 October round in full | `REPORT_2026-10-04_parity.md` |
| Proof | `evidence/*_2026-10-04.*`: validation, coverage, label flags, prompt sizes, citation audit |
| Drafts, brief, checker, pre-round snapshots | `drafting/2026-10-04/` |
| What the Timor-Leste run says | `notes/timor_leste_all_indicator_run.md` |
