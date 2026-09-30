# Overnight report — finale instrument (W3), 13 September 2026

> **Update, 13 September, morning.**
> - **The instrument has moved.** It now lives in this folder, in `instrument\` (decision D9). Worktree
>   paths below are historical; `HANDOFF.md` says how the instrument reaches the repo.
> - **Correction: the citation audit's country check did not run overnight.** The corrected audit lists
>   30 lines instead of 19, and no wrong citation turned up.
> - **Correction: concern 13 was wrong about the workspace README.** It already said the host states
>   the traps.
> - **One host rule was missing and is now encoded:** a real act cited to the wrong section scores zero.
> - **Midday: the codebook is one file (D11).** All 61 blocks sit in `indicators.yaml`, in host order;
>   `indicators_generated.yaml` is gone. Tiers describe depth, not authorship: the Round 1 codebook
>   was generated too, so "human-authored" wording has been corrected.
>
> Details are in `CHANGELOG.md`.

**In short.** The Round 1 instrument process (stages A–E) now covers every indicator the tool extracts: 61 of the 62 the host lists. Only 6.5 is left out, because it is non-regulatory. The validator passes. The work sits in a separate git worktree with **nothing committed and nothing vendored**, so the mapping stage still runs on the Round 1 instrument.

Every source document it cites is copied into `sources/`. The rules for pillars 6–7 now include the traps the host wrote on the finale template. Fourteen more indicators have full-depth drafts that nobody has reviewed yet, and the other 38 are generated from host text.

The biggest concerns are about the host's own rules and data, not the build. They are in section 3.

---

## 1. Where everything is

| What | Where |
| :---- | :---- |
| Instrument code and outputs | **Now `instrument\` in this folder.** Built overnight in `C:\Users\woshi\Desktop\rdtii-rocky-finale-w3\stages\p0-instrument\` (git worktree, branch `w3-instrument-61`, uncommitted, parent `92a5e9d`), which is now retired |
| Main repo | `rdtii-rocky-finale` on `finale`: **untouched** (clean) |
| Change log | **Now `CHANGELOG.md` in this folder.** The overnight entries were copied from `rdtii-rocky-finale-w3\docs\CHANGELOG_FINALE.md` |
| Source documents | `sources\` in this folder: 38 host and Round 1 files, 13 text extracts, `README.md` with origin and SHA-256 for each |
| Evidence | `evidence\`: validator transcript, coverage table, prompt sizes, label flags, citation audit |
| Notes | `notes\`: trap sources (pillars 6–7), scope and ID hazards, seven drafting notes, label review queue |

To re-run the check (updated on 13 September), from this folder: `python code\tools\validate.py`

## 2. What was built

- **Ordered ID list** (`output/indicator_order.yaml`), taken from the host template:
  - 62 IDs in host order, 61 in scope, 6.5 declared out
  - host exception notes, and the host's trap rows (template rows 79–85)
  - the non-regulatory list, and the practice-based list (3.4, 5.3, 9.1)
  - it matches the mapping stage's `HOST_ORDER` test fixture exactly
- **Codebook, tiered.**
  - **A, 9 indicators.** The pillar 6–7 blocks, moved to decimal IDs. Every rule line now cites its source. Guide page numbers are fixed to printed pages (Round 1 mixed PDF and printed numbers), and the host's trap rows are added.
  - **B, 14 indicators:** 2.1, 2.3, 3.5, 4.9, 5.5, 8.1–8.4, 9.1, 9.4, 12.3, 12.8, 12.9. Drafted at Tier A depth, with a citation on every line. **Not reviewed by a human.**
  - **C, 38 indicators.** Generated from host text only: category, criteria as scoring branches, score set, exception notes, and the Guide's defining sentence. No traps.
- **Policies.** Decimal IDs; host row 85 (an amending act cited in place of the principal act scores 0); practice-based and non-regulatory rules; 7.1 and 7.2 answered once per economy; an ID policy.
- **Signatures.** 61 files named by decimal ID, 400 exemplars, each indicator drawing from at least two economies. The content now lives in `scripts/data/*.yaml`, not in Python dictionaries.
- **Gold set.** 1,054 rows: every coded host row, all pillars, ten economies.
  - It carries the host's verification feedback: the Thailand sheet's "Correct" or "Not correct" per row, plus the government-verification questions in the Lao PDR and Russia sheets.
  - Flags: 2 suspect and 5 advisory (Round 1, reviewed), 34 "host-marked" rows the host verification called "Not correct", and 7 machine-check candidates.
- **Validator, finale edition.** It passes, with exit code 0. For all 61 indicators it checks:
  - category names and score sets match the host methodology sheet
  - one scoring branch per allowed score
  - a citation on every Tier A and Tier B rule line
  - the Guide's defining sentence appears word for word on the cited page
  - all 400 exemplars and all 1,054 gold rows match their workbook rows
- **Measurements.** One prompt prefix covering all 61 indicators: 122,681 characters. Per pillar: 10,065–29,070. Today's nine-indicator prefix: 25,974.

How the 52 new indicators were drafted:
1. Seven drafting agents, one per pillar group, worked from the host documents with a fixed brief.
2. A checker verified each group's output (quotes, row references, score sets, citations).
3. The merge dropped exemplars that land on host-marked rows.
4. A heuristic citation audit found one wrong page citation, which I corrected. The audit's country-name check did not run; see the update note at the top.

## 3. Concerns to talk about (ranked)

### A. The host's own rules and data

1. **The finale template states the mapping traps, and three are stricter than Round 1.** Rows 79–85 of the Indicator Reference sheet state them; our workspace README says the host doesn't.
   - **6.2 is "a storage locus, not general record-keeping".** Round 1 argued 6.2 up to 1 in Singapore, Malaysia and Australia from rules that records be kept in-country (DISCLOSURES item d), and two Round 1 exemplars sit on that line.
   - **7.1 and 7.2 are answered once per economy.** Citations of individual provisions under them "are not discoveries and score zero", whereas Round 1 filed several 7.1 rows per economy.
   - **7.5 excludes routine inspection of business records**, and secrecy duties with a court-order carve-out.
   - All are now in the codebook. Decide whether the Round 1 6.2 cells still stand. Details: `notes/trap_sources_pillars_6_7.md`.
2. **How rows roll up into an economy score is undefined.** Four drafting groups hit this independently. Several rules only make sense for a whole economy ("more than one measure → 1"; 7.1 and 7.2 answered once), but the host database scores one measure per row:
   - Round 2 scores all 25 of its 2.3 rows at 1, including single local-content rules the criteria put at 0.5.
   - 9.4 applies "more than one scheme → 1" differently in different economies.
   - 10.2 has several 0.5 rows per economy.
   - This is a question for the secretariat.
3. **The host data has label noise, and some of it contradicts the host's own Guide.**
   - **Thailand:** the host's own verification marks 34 rows "Not correct". Most fix impact text or law titles rather than scores, which still breaks matching by law name during evaluation. One says "TO CHECK" (r2-th-086).
   - **Wrong ID in the host data:** r2-id-035 is tagged 4.1 (trade secrets) but describes a patent application, and it is the only score-1 row for 4.1.
   - **Drafters questioned 295 rows** across 48 indicators (`notes/label_review_queue.md`). Examples:
     - blocking of political content scored 1 under 9.1, despite the exclusion
     - Indonesian foreign-equity caps placed in the wrong band
     - a draft rule scored 1 under 8.4
     - "remove on notice" scored both ways under 8.4
   - **The Guide and the methodology sheet disagree** in places:
     - 12.2: purchase limits "AND" delivery restrictions versus "or"
     - 11.2 and 11.3: internal contradictions
     - 3.1: a cap of exactly 50% is undefined
     - 12.5: no threshold scores 1, the reverse of the usual rule
   - **Host documents conflict on scope:** ISP licences (5.5 or 9.4); broadcasting (Pillar 3, 5 or 9.4); registration versus licence (9.4, 12.3).
4. **Thin evidence.** 19 indicators have no clean score-1 row anywhere in the host data: 1.4, 3.4, 4.1, 4.2, 4.3, 4.5, 4.6, 5.1, 5.2, 7.1, 7.2, 8.1, 11.1, 11.4, 12.4.3, 12.4.6, 12.5, 12.6, 12.9. Rows for 4.2, 4.3, 4.6, 11.1, 11.4, 12.4.3 and 12.9 all score 0.
5. **Practice-based indicators (3.4, 5.3, 9.1) need evidence the legal-text pipeline doesn't collect**: blocking incidents, government shareholdings, cases where screening blocked an investment. 3.4 has no trustworthy score-1 row.

### B. Decisions to confirm

6. **Review the 14 Tier B drafts.** They are careful and cited, but a human has not read them. Suggested order: the six freeze targets (8.3, 8.4, 9.1, 9.4, 12.3, 12.8), then the rest. Open questions are in each block's `review_notes` field (not sent to the model) and in `notes/drafting_*.md`.
7. **Exemplars now come from the economies we will run.** The finale's new economies are the Round 2 countries, whose rows are both our exemplars and their known baseline, so the Round 1 in-sample lean would repeat.
   - `exemplar_for` in the gold set makes a leave-one-economy-out rule possible.
   - The query builder (`p3-map/prefilter/queries.py`) still has to apply it.
8. **Tier C now carries exemplars.** The finale plan (3E) assumed none existed, but every indicator has at least 9 coded rows. The plan's "no gold set for the other 52" statement is also no longer true.
9. **Prompt size.** D3 targeted per-pillar prefixes no larger than today's 25,974 characters.
   - Pillar 12 is 29,070 and misses the target.
   - The single 61-indicator prefix is 122,681, below D3's projected 176,000.
   - 8,815 characters of shared header repeat in every per-pillar prefix.
   - Settle per-pillar versus single prefix with a small mapping run.

### C. Integration not done (blocks using the new instrument)

10. **The mapping stage still expects the Round 1 instrument.** Before re-vendoring:
    - replace the `INDICATORS` literal with a loader
    - make the prompt per pillar (`build_system_prefix(pillar)`)
    - remove the hard-coded legacy IDs in `submission.py`, `select.py` and `rollup.py`
    - have `evaluator.py` and `discovery/malaysia.py` read `label_flag` instead of their own hard-coded ID lists
    - move `baseline.py` to decimal IDs
    - write `migrate_ids.py` for the Round 1 run artefacts
    - add a check that the vendored copy matches: the validator now reports whether it does, and can enforce it
    - Re-vendoring today would break mapping.
11. **Crawler registries.** `sources_<cc>.yaml` exist only for Singapore, Malaysia and Australia, pillars 6–7, with legacy IDs, and `indicator_pillar()` returns nothing for decimal IDs. The live test can draw any pillar in any of nine economies, and must download during the hour.
12. **Keywords are English only.** Three of the six finale economies are non-English, so the keyword search leg will miss native-language text; only the embedding leg is multilingual.

### D. Corrections and housekeeping

13. **Stale statements.** PLAN.md 3E's premises (no Tier C exemplars, gold for 9 only) are wrong. PLAN.md 3F pairs 5.5 with 12.3, but the host FAQ contrasts 5.5 with 9.4. *(Corrected in the morning: this item also said the workspace README denied that the host states the traps. The README had already been fixed on 12 September at 19:00.)*
14. **The host renumbered three IDs:**
    - Guide 4.1 is host `4.01`
    - Guide 4.10 is host `4.1`
    - Guide 12.1 is host `12.01`
    Never map by the Guide's numbers.
15. **Public-repo question.** I copied the finale template (a host workbook) into the stage's `reference/` folder for reproducibility. This touches open host question 10, about ESCAP workbooks in a public repo.
16. **Incident.** A shell copy mistake overwrote one text extract (the Assignment 2 brief) for about 15 minutes. It was re-extracted, all drafters were told, and no citation relied on the bad copy.
17. **Guide sentence check.** The validator checks Guide sentences only when given the Guide text (`RDTII_GUIDE_TEXT`). The PDF can't ship in the public repo, so a reviewer's clone skips that check.

## 4. Decisions I took without you (reverse any)

- Worked in a separate worktree and branch; no commits, no vendoring, no mapping-stage changes.
- Drafted all 14 of the plan's Tier B priorities, not just the first six.
- Gave Tier C signatures exemplars.
- Put every host row (ten economies) in the gold set, not just Round 1.
- Encoded the host template's trap rows in the Tier A blocks (stricter 6.2, 7.1/7.2 and 7.5).
- Added two flag statuses (`host_marked`, `candidate`) and a `host_verification` field.
- Kept host typos verbatim in `category_official` so the checks can match exactly.
- Moved "UNRESOLVED" rule lines out of the codebook into `review_notes`.
- Copied the finale template into the stage's `reference/` folder.

## 5. What I did not do

- Commit, merge or vendor anything.
- Touch mapping-stage or crawler code.
- Rewrite the Round 1 run artefacts (the migrate script).
- Run a mapping or evaluation pass with the new instrument.
- Add reviewed flags from the drafters' questions: they are a queue, not flags.
- Answer the open host questions, or have a human review the drafts.

## 6. Suggested first half hour

1. Read section 3A, then open `evidence/coverage_2026-09-13.md` (one table, every indicator).
2. Read two Tier B blocks to judge the draft quality: 8.4 and 12.3, at the end of `indicators.yaml`.
3. Decide on the three stricter host traps (concern 1), and whether to ask the host about roll-up (concern 2).
4. Decide: merge the branch as a draft, or keep iterating in the worktree.
