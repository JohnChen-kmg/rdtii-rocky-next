# Decisions: instrument

Task-level choices and the reason for each. Newest entry on top. Code changes are not logged here.
They go in `C:\Users\woshi\Desktop\rdtii-rocky-finale\docs\CHANGELOG_FINALE.md` under workstream W3.

Each entry gives the decision, the reason, and what breaks if it is reversed. The third line is the
important one. It is what stops a decision being quietly undone in week three.

---

## 2026-09-20 D14. Every indicator the tool does not automate is marked for a manual check, in every economy

**Decision:** the developer's call, 2026-09-20, widening D13: "not only for China, there's a general
pattern that some pillars will not be covered, which need researcher to do manual checking, please
mark those down." The automated scope is pillars 6 and 7, D8. Every other in-scope indicator, in every
economy, carries a mark: not automated, manual check by a researcher, with the reason. Where an
automated indicator's operative tier is not published by an economy's portal, that economy gets the
same mark for that indicator.

- **Machine-readable, the instrument.** Extend `indicator_order.yaml`'s `evidence` field, or add a
  `coverage` field beside it, with values for: automated; manual, outside the automated scope; manual,
  practice or external evidence; manual, tier not published by this portal. Per-economy overrides live
  beside it. The shape is the instrument's implementation choice. The validator should check the file
  against the register below, so the two cannot drift.
- **Human-readable, the register.**
  `C:\Users\woshi\Desktop\RDTII Finale Plan\3_Final_Stage\COVERAGE_AND_MANUAL_CHECKS.md`, generated
  from `indicator_order.yaml` and the tiers in `indicators.yaml` on 2026-09-20, with per-economy notes
  added by hand. It is what a researcher reads. Today it marks 9 indicators automated and 52 manual.
- **The mark in the output** is one sentence, the same everywhere, carrying the reason. The mapping
  stage writes it, its decision M9.
- D10 is unchanged: the 14 non-regulatory indicators get no row at all.

**Why:** the finding in the issue record is a general pattern. The operative content of the index often
sits in a tier below the statute. Most official gazettes and legislation databases publish that tier,
and our crawler collects it only under core or seed acts; China's database does not publish it at all,
and forbids crawling. Six indicators are outside any law database everywhere, because a fact, a standard
or a trade posture answers them. Building retrieval for the rest is out of reach before the freeze.
(Corrected 2026-09-20: an earlier wording said no surveyed portal publishes every tier, which
overstated China's case as the general one.) The host rewards the alternative
in its own words: an honest gap in the readiness table "costs you nothing", and saying plainly what
does not work is marked up. Word Section 4 asks per economy which pillars run end to end, and the
live-test short note asks which indicator a ministry should check first. The register answers both.

**Consequence if reversed:** the tool either claims coverage it does not have, or presents a wrong
confident answer read off the statute where the number sits a tier below. The China survey shows
the second case concretely. Dropping the register means Section 4 is filled from memory, which is
the one thing the secretariat checks against the code.

## 2026-09-20 D13. Indicators whose answer is not in the legal dataset are marked, not automated

**Decision:** the developer's call, 2026-09-20, in their words: "we don't need to automate for those
special pillars, just mark them down, as a notification for users that the result may be from another
source than the legal dataset."

- No retrieval, mapping or scoring is built for an indicator whose answer is not published in any
  legal instrument the tool reads.
- The instrument carries the marker. `indicator_order.yaml` already has `evidence: practice` on 3.4,
  5.3 and 9.1 (`notes\finale_scope_and_id_hazards.md`). Extend that field rather than add a second:
  one value for answers that live in practice evidence or an external source, and a per-economy
  override for the cases where one economy's portal does not publish the tier, such as China's 10.3,
  12.5 and 12.7. The shape of the field is the instrument's implementation choice.
- Every row, and every null row, the tool emits for such an indicator carries a notification to the
  user: the result may come from a source other than the legal dataset and is to be checked outside
  the tool. One sentence, the same everywhere. The mapping stage emits it, its decision M8.
- D10 is unchanged. The 14 non-regulatory indicators still get no instrument at all. D13 covers
  indicators that are in scope and scoreable but whose answer the legal dataset does not hold.

**Why:** the finding recorded on 2026-09-20 in
`C:\Users\woshi\Desktop\RDTII Finale Plan\3_Final_Stage\ISSUES\2026-09-20_subordinate-tier-coverage.md`.
For China's national database, 9 of 61 indicators are answered by no legal instrument at any tier it
carries: 5.3 by a state-enterprise catalogue and company filings, 9.1 by a blocklist published nowhere,
11.4 by a set of national standards. Retrieving from catalogues, standards bodies and filings is a
different tool. The host's format guidance asks for an informative statement where there is no
relevant law, and the host marks honesty up. A marked gap costs nothing. A confident wrong answer read
off the statute costs the point and the reviewer's trust.

**Consequence if reversed:** either the tool grows retrieval paths into non-legal sources for a handful
of indicators, before a code freeze ten days away, or it scores them as absent and prints "no provision
found" with full confidence. The China research shows the second failure concretely: telecom foreign
equity read as 49 percent from the database, while a MIIT notice of October 2024 lifted the cap in four
zones.

## 2026-09-13 D12. The code sits in `code\` at the workspace root, apart from the instrument's files

**Decision:** all code for the instrument sits in `code\`, beside `PLAN.md`:
- `code\scripts\` holds the builders, the validator, the helper modules and `data\`. It goes to the
  repo as `stages\p0-instrument\scripts\`.
- `code\tools\` holds the two workspace-only checks.
- `code\README.md` explains the workflow.

`instrument\` keeps the instrument's files: outputs, host workbooks and stage documents.
- `rdtii_examples.py` finds the stage folder in both layouts: `scripts\` inside the stage in the
  repo, and `code\scripts\` beside `instrument\` here.
- `data\` always travels with the scripts.

**Why:** the user's call, 2026-09-13. The code was two levels deep, mixed in with outputs and host
workbooks, and they wanted one visible folder for the coding files with the workflow explained.

**Consequence if reversed:**
- Putting the scripts back inside `instrument\` means reverting the paths in `code\tools\` and in
  every document that names `code\`.
- Removing the two-layout detection from `rdtii_examples.py` breaks one layout silently: the scripts
  would stop at "cannot find the instrument stage folder".
- The hand-off copies `code\scripts\`, not `instrument\scripts\`. A copy of the old path would leave
  the repo on old scripts.

## 2026-09-13 D11. One codebook file, every indicator in host order; the tier is a field, not a file

**Decision:** all 61 codebook blocks live in `instrument\output\indicators.yaml`, ordered as in
`indicator_order.yaml` and grouped under a banner per pillar. `indicators_generated.yaml` no longer
exists.
- How deep a block goes stays recorded in its `tier` field (A, B or C). The file's `tiers` key
  describes the three once.
- No script rewrites an existing block. `build_indicators_from_methodology.py` only adds a Tier C
  block for an in-scope ID that has none.
- `--check` compares the Tier C blocks with today's host sheets, and `--reorder` restores host order.

**Why:** the user's call, 2026-09-13. The mapping logic reads every block the same way, so the file
layout should not separate them, and one list ranked by index is easier to read and review.

The split also rested on a wrong premise: "hand-authored" against "generated". The user confirmed
that the Round 1 codebook was generated, not written by people. So the real difference between the
tiers is depth, not authorship:
- The live files now say "Round 1 codebook", "drafted" and "extracted by script".
- Read "hand-authored" in D2 and D8 the same way.
- The Round 1 snapshots in `sources\round1_record\` still say "written by hand" and
  "human-transcribed". Correct that before any submission text quotes them.

**Consequence if reversed:** splitting again means the mapping loader reads two files and the
validator polices the boundary between them. Breaking the add-only rule is worse: a script that
rewrites existing blocks would silently undo every edit made while reviewing Tier B and Tier C.

## 2026-09-13 D10. The fourteen non-regulatory indicators get no instrument

**Decision:** there is no codebook block, signature or gold row for these fourteen indicators, and the
tool writes no rows for them:
- 1.1 and 1.2, from the WITS database
- 9.2, from the V-Dem database
- 1.3, 2.4, 4.4, 4.7, 4.8, 5.6, 6.5 and 12.10 to 12.13, from treaty and agreement status

D5 already covers 6.5; this entry covers all fourteen.

**Why:** the host says in two documents that these come from external databases and treaty status
lists, not from legal text:
- the Non-regulatory indicators note, p.1: "an automated data retrieval method is not required"
- the Internal Guide, p.8: "No need to develop data-extraction tools"

Thirteen of them are also missing from the finale template's Indicator Reference and from the
methodology sheet. The template's note says "Gaps in the numbering are intentional".

**Consequence if reversed:** a retrieval path to databases and treaty lists that the host does not
ask for, and rows nobody marks. Worse, it invites a wrong mapping: for example, a domestic
e-signature law tagged 12.12, which asks about adopting the UNCITRAL model law. Keep this group apart
from the practice-based indicators 3.4, 5.3 and 9.1. Those are regulatory, stay in scope, and need
evidence of practice.

## 2026-09-13 D9. This folder is the instrument's working home; the finale repo receives it at hand-off

**Decision:** all instrument work happens in `instrument\` in this folder: codebook, policies,
signatures, gold set, and the scripts that build and check them. The finale repo gets a copy only at
hand-off, when the mapping stage can read it, following `HANDOFF.md`. The overnight worktree
`rdtii-rocky-finale-w3` is retired. This replaces the earlier rule in `README.md`: "No source code
lives here. The code lives in the repo."

**Why:** the user's call, 2026-09-13. Keep the documents in this folder, work and document here, and
merge into the finale folder at the end so the pipeline can compute. It keeps the host documents,
drafts and evidence beside the instrument they justify, and away from the public repo. The mapping
stage cannot read the new instrument yet anyway.

**Consequence if reversed:** if work also continues in the repo, there are two live copies and they
drift. Pick one, and delete or freeze the other. The opposite risk is forgetting the hand-off: the
pipeline would then compute with the Round 1 instrument, nine indicators with legacy IDs. The
validator's "NOT re-vendored yet" line is the standing reminder.

---

## 2026-09-12 D8. Required scope is pillars 6 and 7. Further pillars are optional

**Decision:** the 30 September submission requires only pillars 6 and 7, the nine scoreable
indicators already hand-authored at full depth. Pillars 1 to 5 and 8 to 12 are optional stretch
work. Tiered depth, D2 and D4, now applies only if optional pillars are attempted.

**Why:** the developer's scope call, taken on 2026-09-12 against a freeze minimum that had grown
past what 18 days can hold. Pillars 6 and 7 are the host's mandatory pair. The nine indicators
already exist, so the required instrument work shrinks to the decimal ID migration and encoding the
host's own trap wording.

**Consequence if reversed:** all of steps 3B to 3F come back, about 46 hours. What is lost by keeping
it: the "further RDTII domains" share of C1b, and the live test's discovery points if the sealed task
lands on another pillar. The cheapest partial hedge is step 3B alone, about 8 hours, which gives every
pillar a machine-extracted Tier C entry without hand authoring.

## 2026-09-12 D7. The export writes decimal IDs, despite the column hint saying otherwise

**Decision:** every indicator ID written to the finale output workbook is decimal text, `6.1` and
`12.4.1`. The Output Data column hint that reads "P6-I1" is treated as a stale example, not an
instruction.

**Why:** the same workbook contradicts itself. Its Indicator Reference sheet lists all 62 IDs in
decimal text. Its Output Data column hint at row 5 column E gives the example as "P6-I1". The finale
brief says to write 6.1, never P6-I1, and warns that a numeric ID collapses 12.10 to 12.1. The
Indicator Reference sheet is the authority on what the IDs are. A column hint is not.

**Consequence if reversed:** the Coverage Matrix derives the pillar from the Indicator ID by formula.
A wrong format either breaks that derivation or silently mis-attributes rows to the wrong pillar,
which is a direct C1b loss. Reversal also means re-migrating every artefact that step 3A touched.

**Open with the host.** This belongs as a sub-point of question 4 in
`C:\Users\woshi\Desktop\RDTII Finale Plan\3_Final_Stage\OPEN_QUESTIONS_FOR_HOST.md`. That question
asks only whether the format change is retroactive. It does not name the contradiction inside the
finale workbook.

---

## 2026-09-12 D6. The ordered indicator list is an instrument artefact, not a test fixture

**Decision:** generate `output\indicator_order.yaml` from the host Indicator Reference sheet and make
it the one ordered list of indicator IDs. The `HOST_ORDER` literal in
`stages\p3-map\tests\test_indicator_ids.py` asserts against that file instead of carrying its own
copy.

**Why:** today the canonical 62-ID order exists only inside a test file. Three separate steps key off
it. The Tier C generator needs it to decide which IDs to emit. The per-pillar prompt needs it to group
candidates. The validator needs it to prove that every in-scope ID is defined exactly once. A test
fixture is the wrong home for something three production paths read.

**Consequence if reversed:** each of those three steps grows its own list, and the three drift. The
failure is silent. An indicator defined nowhere just produces no rows, and nobody notices until a
judge asks why pillar 10 is empty.

---

## 2026-09-12 D5. Indicator 6.5 stays out of scope, and 61 is the scoreable count

**Decision:** 6.5 is declared out of scope in `output\indicators.yaml` under `scope.out_of_scope`. The
instrument targets 61 scoreable indicators against the 62 the host lists. Every document says "61
scoreable of 62 listed" rather than "62".

**Why:** the host's own methodology sheet carries no scoring criteria row for 6.5. It holds 61
indicator rows where the Indicator Reference sheet holds 62. The methodology sheet header states that
gaps in the ID sequence are intentional, because those indicators are non-regulatory. 6.5 asks about
participation in agreements with binding commitments on data transfer, which is a treaty check, not a
reading of national legislation. The tool is not required to extract it.

**Consequence if reversed:** the tool would need a treaty-text source it does not have, which means a
new crawl target, a new document type and a new evidence path. That is a workstream, not a fix. The
cheaper reversal is to emit a 6.5 row with a null statement, which is worse, because it claims
coverage the tool did not perform.

---

## 2026-09-12 D4. Tier C discloses its depth, and needs more confidence before a NEW tag

**Decision:** every Tier C indicator declares its depth in the output Notes column. A Tier C row must
clear a higher confidence threshold than a Tier A row before it is tagged NEW rather than KNOWN.

**Why:** a Tier C indicator has a definition and a score set but no trap rules and no labelled
exemplars. That is a weaker instrument, and a weaker instrument produces more plausible-looking wrong
matches. Disclosing the depth is honest and the host marks honesty up. Raising the NEW threshold is
the practical guard, because a wrong NEW claims a discovery the tool did not make.

**Consequence if reversed:** without disclosure, a reviewer comparing a pillar 10 row against a
pillar 6 row assumes equal rigour behind both. That is a C2a problem, because framework alignment is
judged on consistency. Without the threshold, Tier C indicators contribute most of the false NEW rows
and every one of them is a C2b citation-fidelity risk.

---

## 2026-09-12 D3. Per-pillar cached mapper prefixes, not one prefix holding every indicator

**Decision:** `build_system_prefix()` takes a pillar argument. The mapper groups candidate indicators
by pillar and makes one call per group.

**Why:** one prefix holding 61 indicator blocks is about seven times today's prefix.

| Prefix | Characters |
| :---- | ----: |
| Today, 9 indicator blocks | 25,974, measured |
| Projected, 61 indicator blocks in one prefix | about 176,000 |

Per pillar, the prefix stays at or below the size of today's nine-indicator prefix. Cost and latency
both scale with the prefix. Prompt caching only pays when the prefix is stable and reused. Cost per
run is a recorded, verified figure in the finale, so this is not a tuning detail.

**Consequence if reversed:** one prefix per call multiplies the input tokens on every provision by
roughly seven. The cost ledger is checked against the code by the secretariat, so the increase is
visible. It also risks pushing the prefix past a useful cache window, which turns a cached read into a
full-price read on every call.

---

## 2026-09-12 D2. Tiered instrument depth A, B and C, disclosed in the prompt and the export

**Decision:** three tiers. Tier A is the 9 existing indicators at full depth. Tier B is about 12
hand-authored with scoring tree, traps and disambiguation. Tier C is the rest, machine-extracted from
the methodology sheet with name, category, definition, scoring values and exceptions where the host
states them.

**Why:** Round 1 depth took real hand-authoring per indicator. It cannot be repeated 52 times in 18
days by one developer. Tiering is the only honest way to reach twelve-pillar coverage by the freeze.
The alternative is to hand-author a few more and leave most pillars empty, which loses C1b outright.

**Consequence if reversed:** reverting to uniform full depth means either two pillars of coverage, or
52 hand-authored indicators. Neither fits. Reverting to uniform shallow depth throws away the trap
rules that stop 6.1 and 6.4 being confused, which is the single most valuable thing the instrument
does.

---

## 2026-09-12 D1. Decimal text is the one internal vocabulary, migrated now, never float-parsed

**Decision:** indicator IDs are decimal text everywhere inside the tool. `6.1`, `4.01`, `12.4.1`. The
legacy `P6-I1` form survives only as a translation table for reading Round 1 artefacts. IDs are never
parsed as numbers and order never comes from their numeric value.

**Why:** three separate reasons, each sufficient. `P6-I1` cannot express a three-level ID such as
12.4.1, and the host list contains seven of them. Entered as a number, `4.01` collapses to `4.1`, and
both exist in the host methodology sheet as different indicators. The finale brief warns about that
exact pair in `C:\Users\woshi\Desktop\RDTII Finale Plan\3_Final_Stage\REQUIREMENTS.md`. `12.01`
carries the same trailing-zero risk, although it has no twin in the host list today. That methodology
sheet stores its two-level IDs as numbers and only its seven `12.4.x` IDs as text. The Indicator
Reference sheet stores all 62 as decimal text. Follow the text sheet.

**Why now rather than at export time:** an export-time translation means every internal artefact, log
and index keeps the legacy form. The mismatch then has to be held in the developer's head for the rest
of the build. The live stress test is the worst possible place to discover a translation gap.

**Consequence if reversed:** seven `12.4.x` indicators become unaddressable, and `4.01` merges into
`4.1`, which are two different indicators. Both are wrong-row failures, and the Coverage Matrix shows
them to a judge. Reversal also invalidates the re-keyed retrieval index, which would force a re-run
of the dense leg and the triage pass, the two most expensive artefacts Round 1 produced.
