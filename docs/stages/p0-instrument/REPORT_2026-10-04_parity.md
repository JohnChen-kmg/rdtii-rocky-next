# Report — every indicator at pillar 6–7 depth, 4 October 2026

**In short.** All 52 indicators outside pillars 6 and 7 now have the same instrument elements as the
nine pillar 6–7 indicators: a full codebook block, machine-readable marks, reviewed label flags and
notes. The validator passes. The prompt text the mapping stage builds for pillars 6 and 7 is unchanged,
byte for byte. The work is in this folder only; nothing has been sent to the finale repo.

The new content is a draft. Seven drafting agents wrote it from the host documents, a checker confirmed
every cited page and host row exists, and no person has read it yet.

---

## 1. What changed

| Element | Pillars 6–7 before | Other 52 before | Other 52 now |
| :---- | :---- | :---- | :---- |
| Codebook block at full depth | 9 of 9 | 14 of 52 (38 restated host text only) | 52 of 52 |
| Coding rules per block, average | 2.9 | 5.8 on 14 blocks, 0.1 on 38 | 6.8 |
| Disambiguation lines per block, average (TRAP lines) | 3.4 (1.7) | 5.5 (3.6) on 14 blocks, 0 on 38 | 6.8 (4.8) |
| Guide examples | 7 of 9 blocks | 13 of 52 | 35 of 52; the Guide gives none for the other 17 |
| Weight from the Guide | 9 of 9 | 0 | 45; the seven 12.4.x share one Guide weight and carry null |
| Question separate from definition | 9 of 9 | 14 of 52 | 52 of 52 |
| `polarity: inverted` where an absence scores 1 | 7.1, 7.2 | 8.1, 8.2, 12.9 | 12 indicators (list below) |
| `level: economy` with the framework's name | 7.1, 7.2 | none | 11 indicators (list below) |
| Absence statement (`null_statement`) | in mapping code only | none | 52 of 52, and copied onto the nine |
| Reviewed label flags (suspect, advisory) | 2 and 5 | none | 51 and 157 |
| Line in `INSTRUMENT_NOTES.md` | 9 | none | 52 |
| "Where the measures live" above the pillar | pillars 6, 7 | none | all ten other pillars |

- **One key set.** All 61 blocks now carry the same keys; the validator enforces it.
- **Tiers.** A 9 (pillars 6–7), B 52, C 0.
- **Inverted** (an absent framework, mechanism or threshold scores 1): 4.2, 4.5, 4.6, 4.1, 5.1, 5.4,
  5.7, 7.1, 7.2, 8.1, 8.2, 11.1, 12.5, 12.9. These are the same 14 that `policies.yaml` already named.
- **Economy-level** (answered once per economy): 4.2, 4.5, 4.6, 4.1, 5.1, 5.4, 5.7, 7.1, 7.2, 8.1, 8.2,
  11.1, 12.9. Only 7.1 and 7.2 were marked before. 12.5 is inverted but not economy-level: it is a
  threshold, not a framework.
- **Both sides of every trap.** A block that sends a look-alike to a sibling is named back by that
  sibling. 37 one-sided references were found after the first pass and all were closed; the validator
  now reports 0.
- **Label flags.** 208 host rows outside pillars 6–7 are flagged: 51 suspect (the score contradicts an
  explicit host rule, or the row is under the wrong indicator) and 157 advisory. Each records that the
  call was made while drafting and is not confirmed by a person. One exemplar was added (3.1); no
  exemplar had to be removed.

## 2. What did not change

- **The pillar 6–7 prompt.** Rendered with the mapping stage's own code before and after: 31,929
  characters both times, same SHA-256, compared byte for byte.
- **The pillar 6–7 signature files.** All nine are identical to the repo's copies, so their retrieval
  queries are unchanged.
- **The rendered policy sections.** `measure_inclusion`, `scoring_policy` and `edge_cases` are
  byte-identical. Rules for other pillars sit on those pillars' own blocks.
- **Which indicators are automated.** The mapping stage still maps pillars 6 and 7 unless a run sets
  `INDICATORS_SCOPE` (decisions D13 and D14). The Timor-Leste run of 27 September mapped the other 52
  that way; `notes\timor_leste_all_indicator_run.md` records what it produced.

## 3. How it was checked

1. **Checker on every draft:**
   - every rule line carries a citation
   - every cited Guide and Internal Guide page exists
   - every cited host row exists, is not struck through, and is in the workbook named
   - every Guide example's country is on its cited page
   - one scoring branch per host score, in order
2. **Scoring branches read against the host criteria** for all 38 rewritten blocks. They line up.
3. **Validator, stricter than before:** same elements on every block, row numbers matched to the host
   sheets, `indicator_sets` matched to the blocks. PASS, exit 0 (`evidence/VALIDATION_2026-10-04.txt`).
4. **Heuristic citation audit:** 1,272 rule lines; 231 listed for reading
   (`evidence/citation_audit_2026-10-04.txt`). I read the lowest-scoring group that cites Guide
   pp.10–12 and confirmed those pages say what the lines claim. The rest have not been read.

## 4. Decisions for you

1. **Which indicators are automated: settled by the plan, and now marked in the instrument.**
   - The plan already answers it (D14, the coverage register): the tool automates pillars 6 and 7;
     the other 52 are "manual" but can be run on request, as they were for Timor-Leste.
   - Added the same afternoon: `indicator_order.yaml` now carries the marks the register asks for
     (`coverage`, `coverage_reason`, `answer_nature`), 9 automated and 52 manual. This is the mapping
     stage's request R1. The mapping stage reads the same nine as before.
   - Six indicators get the reason "practice or external evidence", because no legal text states
     their answer in any economy: 1.4, 3.4, 5.3, 9.1, 11.4, 12.6.
   - To automate another indicator later, add it in `code\scripts\data\coverage.yaml` and rebuild.
     That is the one decision left here: whether any of the 52 should move to "automated".
2. **When to hand this off.** It is safe for pillars 6 and 7. For the 11 new economy-level indicators
   the mapping stage needs one change first (section 5, first item); without it their economy scores
   come out "pending".
3. **Five economy-level calls the drafters were unsure of:**
   - 4.2 and 4.6: the two elements (procedures, provisional measures) can sit in two laws.
   - 5.1: host data has two rows per economy in four economies.
   - 11.1: the foreign-exclusion test can apply to one sectoral body.
   - 12.9: the host has up to five rows per economy.

   The host states the economy-level rule only for 7.1 and 7.2; the others rest on the Guide's wording.
4. **Who reviews the 52 Tier B blocks, and in what order.** 39 blocks carry open questions
   (`review_notes`, 218 in total). The audit list and each group's `notes.md` are the reading aids.
   Suggested order: start with the 13 indicators that produced filed rows for Timor-Leste (2.1, 2.3,
   3.3, 3.5, 5.1, 5.4, 5.7, 8.3, 8.4, 12.4.4, 12.5, 12.8, 12.9).
5. **The 51 suspect flags.** Three of them are their economy's only row for that indicator
   (r2-id-159, r2-in-149, r2-in-152), so they put the economy's answer in doubt.

## 5. Still missing before these indicators compute well

### In the mapping stage (`stages\p3-map`)

- **Economy-level scoring knows only 7.1 and 7.2.** `rollup.py` looks the framework's name up in a
  two-entry table, so any other economy-level indicator ends "pending" (a caught `KeyError`). The
  blocks now carry `framework_name`. Its question and answer scale are also fixed at 1 / 0.5 / 0, which
  does not fit 5.4 (1 / 0.5 / 0.25 / 0) or the binary 5.7, 11.1 and 12.9.
- **Counting measures.** Several indicators score by how many measures an economy has (1.4, 2.1, 2.3,
  3.1, 4.3, 4.9, 5.2, 5.3, 9.4, 10.1, 10.2, 10.3). The roll-up escalates only 6.1 and 6.2.
- **12.5 is inverted but not binary.** A rule found scores 0.5 or 0 by its USD value, never 1.
- **11.2 absence rows.** A score of 0 needs positive evidence that self-declaration is allowed; a null
  row should not default to 0.
- **Absence statements** for other indicators fall back to "no qualifying measure found". The blocks
  now carry `null_statement`.
- **Prompt size.** One prefix for all 52 other indicators is 298,967 characters, three times its
  earlier size. A two-indicator scope is about 20,000.
- **The prompt header says "Pillars 6-7"** whatever the scope.
- **Label flags are not read.** The evaluator ignores `label_flag`.
- **The manual-check reason.** `config\coverage.py` gives "practice or external evidence" only to the
  host's three practice-based indicators. The instrument's `coverage_reason` gives it to six (adds
  1.4, 11.4, 12.6). Reading the field from `indicator_order.yaml` closes the difference.

### In scraping (`stages\p1-scrape`)

- **Sources for other pillars.** Many answers sit in regulators' instruments (central-bank circulars,
  licence conditions, registry policies), which the crawler does not collect.
- **1.4** needs WTO trade-remedy notifications and official gazettes (scraping request R4).

### Evidence the legal text cannot give

- **5.3** (government shares in telecom companies) cannot be answered from legislation; every host
  economy scores 0.5 or 1 from ownership facts.
- **3.4** needs a case where screening blocked an investment; **9.1** needs evidence of blocking.

### In the instrument

- **Search keywords are English only**, for every pillar (the mapping stage's request R3).
- **19 indicators have no unflagged score-1 row** in the host data: 1.4, 3.4, 4.2, 4.3, 4.5, 4.6, 4.1,
  5.1, 5.2, 7.1, 7.2, 8.1, 11.1, 11.4, 12.4.3, 12.4.6, 12.5, 12.6, 12.9. Their top branch rests on the
  Guide and the methodology sheet alone.

## 6. Where the host contradicts itself

The blocks follow the Guide and the methodology sheet, state the difference, and flag the rows. Each
needs a host ruling to settle.

| Indicator | The contradiction | What the block does |
| :---- | :---- | :---- |
| 10.1–10.3, 11.2, 11.3, 2.3, 9.4 | The criteria count measures across the economy; host rows are scored one by one (all 25 Round 2 rows for 2.3 score 1) | Scores each measure and states the count |
| 12.2 | The sheet says purchase limits "AND" delivery restrictions; the Guide says "or" | One measure of either kind scores 1; a strict "AND" would turn the Guide's own example to 0 |
| 4.5, 4.6 | The Internal Guide (p.12) gives 1 for a high piracy rate; the Guide, the sheet and every host row score the law | Scores the law |
| 9.3 | Prior approval of advertising for consumer protection: the Guide scores 0; two host rows score 1 | Scores 0; both rows advisory |
| 8.4 | The Internal Guide (p.13) counts removal-on-notice duties; Australia and Singapore rows score them 0 | Counts them; both rows suspect |
| 12.8 | Thailand's in-country contact point: host verification set 0; the Guide counts a local contact point | Follows the Guide |
| 5.2, 3.1 | Horizontal state-enterprise caps are filed under both; the Guide sends them to 3.1 only | 3.1 only |
| 12.4.2 | Indonesia's domestic rupiah obligation scores 1 in three rows and 0 in one; the criterion is international payments | Scores 0; one row suspect |
| 12.3 | Registration against licence: the Guide's Colombia example is a registration; host rows score registration 0 | No rule written; open |
| 5.7 | Independence criteria with no threshold; Singapore and Mongolia score 1 on single criteria | States the criteria; Mongolia row suspect |
| 12.6 | "Imposed in practice" has no evidence standard and no host row | Open |
| 4.1 | Common-law protection scores 0.5 for Australia and Malaysia, 0 for Singapore and India | Follows the Guide's Singapore example |

Each group's `notes.md` lists the rest.

## 7. Where everything is

| What | Where |
| :---- | :---- |
| The instrument | `instrument\output\` (not yet in the repo; 45 files differ from the repo's copy) |
| Decision | `DECISIONS.md`, D15 |
| Change record | `CHANGELOG.md`, 2026-10-04 |
| Evidence | `evidence\*_2026-10-04.*`: validation, coverage, label flags, prompt sizes, citation audit |
| The drafts, the brief, the checker, the merge script | `drafting\2026-10-04\` |
| Each group's reasoning and open questions | `drafting\2026-10-04\drafts\<group>\notes.md` |
| Pre-round copies of the changed files | `drafting\2026-10-04\snapshots\` |
| Notice for the other stages | `NOTICE_FOR_OTHER_STAGES.md`, update of 4 October |
| What the plan and the Timor-Leste run say | `notes\timor_leste_all_indicator_run.md` |
