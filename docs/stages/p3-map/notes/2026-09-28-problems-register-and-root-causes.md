# Problems register and root causes: what broke, why, and what needs revising

28 September 2026. Written after the first end-to-end run on non-English economies. Every entry is
something measured, not suspected. The last two sections are the ones that matter for how we work.

---

## 0. A framing correction that changes every number below

**The gold set is a reference, not ground truth.** It is the host's 2025 database, and this run
produced direct evidence that it is fallible:

| evidence | what it means |
| :---- | :---- |
| **0 of 201** China and Lao baseline rows carry an article number | it cites laws, not provisions; we cannot reproduce a citation it never made, and where we match we are *more* precise than it is |
| **2 of the 7** laws it cites that we lack are **GB/T and JR/T technical standards**, not legislation | a law corpus will never contain them, and whether a standard belongs in a database of laws is the host's question, not our defect |
| **LA 7.4 = 1** rests on a provision that two independent reviewers judged to be a *data-security officer*, not a Data Protection Officer | the baseline may simply be wrong here; our 0.0 is defensible |
| **CN 6.1**: baseline 0.5, ours 1.0 | the codebook's own escalation clause says ten distinct sectoral measures escalate to 1. Ours follows the instrument; the baseline does not |
| **LA 6.2, 6.3, 7.5**: baseline 0.0, ours 1.0 | we found a local satellite-ground-station mandate, a Lao data-centre mandate and four government-access instruments. Real findings the baseline lacks |
| **Timor-Leste has no baseline at all** | 27 rows today and ~40-80 more coming cannot be scored against it in either direction |

**So "40.6% baseline reproduction" is not an accuracy figure and must never be reported as one.**
A disagreement has a direction, and it has to be read before it is counted:

- we found something the baseline lacks → likely a **discovery**, which is what the host rewards;
- we missed something the baseline has, and the law is in our corpus → a **real miss**, ours to fix;
- we missed it because the law was never crawled → a **collection ceiling**;
- the baseline's own row is questionable → **neither of us is reproducing anything useful**.

This is why Timor-Leste was the right economy to widen: with no gold rows, there is nothing there to
fit to, even accidentally.

---

## 1. The register

`code` = shipping code. `workflow` = how we worked. `upstream` = collection or extraction.
`host` = the host's own data.

| # | problem | class | status |
| :-- | :---- | :---- | :---- |
| 1 | `main.py` carried Round 1's three-economy table; `--economy China` and `--docs cn-…` both exited 2 | code | **fixed** `ff92190` |
| 2 | Widening that table alone would have created a silent zero-row run: the sparse leg returns nothing for CN/LA | code | **fixed** `ff92190`, same commit by design |
| 3 | Neither triage pass honoured `ECONOMIES`; a scoped run judged 42,263 pairs instead of 21,175 | code | **fixed** `c3d50e0` |
| 4 | S3b had no `--limit`, so a pre-flight could not be priced | code | **fixed** `c3d50e0` |
| 5 | Emit caps (`NEW_CONF`, `NEW_CAP`, `NEW_CAP_TAIL`, `SECTORAL_MAX`) and three worker counts were constants, unchangeable after the freeze | code | **fixed** `1de0d5b` |
| 6 | No-provision rows were tagged `KNOWN` unconditionally — untrue for 31 of 54 cells | code | **fixed** `7246cf5` |
| 7 | **32.8% of S4 discarded** (1,487 of 4,530): schema-forced replies arriving in an envelope or flattened | code | **fixed** `0b6dd0b`, 1,322 recovered for $0 |
| 8 | Cost report double-counted a re-ingest: $51.72 claimed against $38.81 billed; `provisions` exceeded the provisions that exist | code | **fixed** `98316d0` |
| 9 | Column N (required, drives C1c) blank on 4 Lao rows | code | **fixed** `948e8ff` |
| 10 | Economy-level scorer lost a whole cell to a transient reply shape (LA 7.2, 36 evidence rows unused) | code | **fixed** `ae9deab` |
| 11 | A complete *refusal* was discarded for omitting three narrative fields that nothing downstream reads | code | **fixed** `912dfba`, another 48 recovered for $0 |
| 12 | My own cost fix let a *partial* re-ingest overwrite a batch's price ($0.67 against $21.86) | code | **fixed** `912dfba` |
| 13 | Dedupe keyed on `doc_id`, so two copies of one law filed duplicate rows | code | **fixed** `1d4c4ae` |
| 14 | **Four selection ceilings were fitted to where gold rows ranked**, and the resulting recall was reported as a measurement | **workflow** | **labelled, not undone** — M15 |
| 15 | Economy-level cells go `pending` when every fire is overturned, discarding an informative rejection | code | **fixed** `edfba41` — verified 29 Sep: all six 7.1/7.2 cells carry a score with a reasoned basis (LA 7.1 reads "Rejected rows confirm Laos has a dedicated Law on Electronic Data Protection"); TL 7.1/7.2 now 0.5, not pending |
| 16 | Replies with no usable verdict. **225, not 117** — the 117 counted only CN/LA/TL after the first re-parse. AU 24, MY 13, SG 12, CN 67, LA 17, TL 33 + 59 | code | **fixed** `4136d55` + `c0b5510` — the batch lane now retries live (it only printed advice; the live lane has retried since Round 1) and the narrative gate no longer discards a provision. 124 were placeholder tool calls, 47 malformed, 29 ours, 25 other. Re-run `fetch` to clear, ~$4 |
| 17 | TL rows cite a decree that *approves* a code rather than the code itself | code | **fixed** `e2536a0` — 45 of the 59 were one branch: with no baseline, `_np_citation` cited "the largest law in the corpus", which in a civil-law jurisdiction is the civil code. Civil Code citations 45 → 0; the 15 remaining decree titles are correct (the decree IS the instrument) |
| 18 | A row whose Law Name is a body or gazette issue rather than an act is not refused | code | **closed, not real** — verified 29 Sep: **zero** filed rows carry a gazette-issue or body name. The decree form was the real instance (17), and a blanket refusal would have dropped 11 correct rows where the decree IS the instrument |
| 19 | CSV files law names in original script only; `law_name_en` exists and is unused | code | **fixed** — verified 29 Sep: 97 rows carry a labelled English title in Notes (CN 55, LA 21, TL 21) |
| 20 | Same statutes crawled from both `cac.gov.cn` and `flk.npc.gov.cn`: 20 CN names with two doc_ids | upstream | **note owed** |
| 21 | `www.gov.cn` barely crawled: 11 documents against 924 from the NPC database; one law there costs 4 gold rows | upstream | **note owed** |
| 22 | 29 of 56 China rows carry a bare-domain Source URL | upstream | **note owed** |
| 23 | Lao's Cyber Crime Law absent though we hold 1,109 gazette documents | upstream | **note owed** |
| 24 | Baseline records no article numbers; two cited "laws" are technical standards | host | **disclose** |
| 25 | The review workbook's English column translated a *different* span from the column beside it: the gloss reads the corpus row, `Full section text` comes from `_full_section()`'s document window. For China the two diverge badly | code | **fixed** `6ce0cf1` |
| 26 | `_full_section()`'s section regex is Anglophone, so for Chinese, Lao and Portuguese it found no heading and fell back to a window starting `s-6000` | code | **fixed** `91fb2da` — per-economy heading forms, plus an off-by-one in the walk-back that `endpos=s+1` hid (a 3-character `第九条` **at** `s` never matched, so it landed one article early; `snippet_char_start` is exactly on the heading in 397 of 400 CN provisions). Extract now begins at the labelled article in 514/516 CN, 188/188 LA, 310/316 TL |
| 27 | `gloss.py` read `language_of_source_name` off the verdict row; that field is absent from all 7,049 rows, so every gloss prompt said "the source language" and left the model to infer it | code | **fixed** `6ce0cf1` |
| 28 | The 225 provisions whose verdict failed validation appeared nowhere but a Summary count -- no sheet listed *which* ones, so "67 China provisions failed" was unactionable | code | **fixed** `6ce0cf1`, new QA Errors sheet |
| 29 | **`law_name` is not resolved per act in a multi-act gazette file.** 364 of 364 multi-act TL documents carry one document-level title across every act, 0 vary by act; 120,690 provisions affected, `citation_confidence` says `exact` regardless. **51% of TL's filed citations cannot be defended as written** | upstream | **note owed** + mapping defence shipped `8e85342`: the row is kept, the one doubtful field is caveated in three confidence buckets |
| 30 | The audit page item 11 is marked on showed no English at all — the gloss reached only the Excel workbook | code | **fixed** `4001965` — second time this stage produced a thing and wired it nowhere |
| 31 | `run_manifest.json` records `economies` but not `INDICATORS_SCOPE`, so a scoped run does not say what it was scoped to | code | **fixed** `012332f` — it cost a destroyed-and-restored file first |
| 32 | Timor-Leste had TWO records files, workbooks and audit pages while every other economy had one; the host reads one per economy | code | **fixed** `f2e7c0b` + `9cc1737`. The guard matters more than the merge: a workbook copied from one arm looks entirely normal and is silently missing 52 indicators |
| 33 | Nothing filled the host's Output Data sheet. 101 slots, 319 rows, and the selection rule existed only as a paragraph | code | **fixed** `3146d67` — S9c, rule as code, verified by emulating the host's own column O formula over the filled sheet |
| 34 | The economy-level rollup is **sampling-dependent**. TL 7.1 returned 0.5 on one run and `pending` on a re-run, from the same zero evidence rows. `pending` is the correct answer — the 0.5 was the model inferring from absence and naming a law, which slipped past the guard | code | **open, and it is the guard that is thin, not the fix**. Problem 15 is fixed in that a reasoned rejection CAN score; it is not guaranteed to |
| 35 | `urlcheck` drew a ConnectError from `laoofficialgazette.gov.la` that returned 200 on an immediate re-check — we may be hitting it faster than the scraping stage's 1 req/s politeness | code | **open**, cosmetic for the submission, relevant to checklist item 25 |

**Verified 29 September, end of day: twenty-eight fixed, one closed as not real, two open in code, one
open workflow decision, five notes owed, one to disclose.** The two still open (34, 35) were both
found by re-running work that had already "passed" — which is problem C1's argument restated. Rows 15 and 19 were stale as *open* and
are confirmed fixed against the output; 16 and 17 were understated and are corrected above; 18 does
not exist in the filed output. The two still open in code are 31 (the manifest scope) and the
second half of 29, which is upstream's to fix rather than ours.

**One finding retracted.** I reported that 52 of China's 55 filed provisions carried an article label
disagreeing with the article containing their text, every one off by exactly one. That was my own
measurement bug — the same `endpos`/strict-`<` boundary as problem 26, in the checking script.
**China's article labels are correct.** A uniform offset across every case should have been read as a
bug in the check rather than a finding.

---

## 2. Root causes — five patterns, not twenty-four accidents

### P1. Round 1 assumptions that the migration did not reach

Problems 1, 3, 6, 8, 17. All were **correct code for three English economies** and silently wrong for
six multilingual ones. The migration list was built by reading code for *indicator-ID* assumptions,
because that is what the instrument hand-off forced us to look for. Nobody re-read the same files
asking "what else assumed three economies and one language?"

### P2. Trusting a schema as a guarantee

Problems 7, 10, 11. `v["key"]` indexed directly on a model reply. A forced schema makes the shape
*likely*, not certain — 620 of 4,530 replies arrived enveloped. Two separate stages had the identical
bug because the assumption, not the code, was shared.

### P3. Counting outcomes without validating them

Problems 7, 8, 12 — and this is the expensive one. The run printed `errors: 849` and continued.
**Nothing asked what kind of error.** That is how a third of the mapping was discarded while every
report said success. The same shape twice more: a cost figure nothing compared against the bill, and
`provisions: 3,466` against 2,617 that exist — an impossible number nothing cross-checked.

### P4. Treating a reference as a target

Problem 14, and section 0. The recall gate was handled as *a number to improve* rather than *a
measurement to report*, so four ceilings were tuned until gold rows fit. No code caused it. It cost
no rows and would have cost the credibility of every other figure.

### P5. Tests that verify the code, not the data

**283 tests passed the entire time a third of the mapping was being thrown away.** Every problem
above lives in the gap between our fixtures and the real corpus: Chinese text, a reply in an
unexpected shape, two copies of one law, an economy with no baseline, a cell with no article number.
The suite proves the code does what we wrote. Only a real run proves we wrote the right thing.

---

## 3. Workflow revisions

**W1. A reference set scores; it never steers.** Gold may report an outcome and must never choose a
parameter, threshold, prompt or target. Where a parameter was fitted, the entry says so in its own
words and the published figure is the un-fitted one. `test_gold_derived_overrides_are_labelled_in_sample`
enforces the labelling; the discipline is ours to keep.

**W2. Read the disagreement before counting it.** Every gold mismatch gets a direction — discovery,
real miss, collection ceiling, or a questionable baseline row — before it enters any rate. A bare
"reproduction %" is not a quality claim.

**W3. Diagnose an error class before paying to retry it.** The 1,487 failures looked like $70 of
re-running and were 1,322 free recoveries plus 165 real ones. One hour of reading beat the retry by
a factor of forty.

**W4. A migration list is written per *assumption*, not per symptom.** The ID migration was thorough
and the economy migration was incidental, because the list was built from one question. Next
migration: enumerate the assumptions (economies, languages, scripts, counts, hosts), then grep each.

**W5. `--limit` samples a prefix, not a population.** A pre-flight on an ordered file reads its easy
end: China's 150-pair probe said 68% keep, the full band 35.7%. Any future pre-flight samples
randomly, and an estimate from a prefix is labelled an upper bound.

---

## 4. Code revisions still needed

Ordered by value. **C2 through C5 and the retry all landed on 29 September** and are struck through
below with their commits. **C1 is the only one left, and it is the one worth protecting** — it is the
root cause behind four of today's five fixes.

**C1. Cross-checks as gates, not probes (P3).** `evidence/probes/verify_s4.py` works but is a
workshop script someone has to remember to run. Move the pattern *into* the pipeline: every stage
derives its report from its own output and refuses to write a figure that contradicts it, the way
`batch_runner` now does. **This is the one to protect** — on 15 October nobody reads a log mid-hour,
and tonight's silent 33% loss was reported without being diagnosed.

**~~C2. Decide problem 15.~~** **Done** `edfba41`, verified 29 Sep against the output: all six 7.1/7.2
cells carry a score with a reasoned basis, and TL's are 0.5 rather than pending. LA 7.1 now reads
"Rejected rows confirm Laos has a dedicated Law on Electronic Data Protection" — the informative
rejection the old code discarded.

**~~C3. Problems 17 and 18.~~** **Done** `e2536a0`. The irrelevant governing law is gone (45 Civil Code
citations → 0). The second half turned out not to exist: **zero** filed rows carry a body or gazette
name, and a blanket refusal would have dropped 11 correct rows where the decree IS the instrument.

**~~C4. Problem 19.~~** **Done** — 97 rows carry a labelled English title in Notes (CN 55, LA 21,
TL 21), and as of `4001965` the audit page and the workbook both show the machine English beside
the original, labelled and never filed.

**~~C5. Problem 26 (P1 again).~~** **Done** `91fb2da`, and it hid a second bug — see the register row.
Original statement: `_full_section()` in `excel_export.py` locates a section by an English statute regex -- `26.-(1)`, `PART IV`, `Division 3`, `Schedule`. It was written when the run was Singapore, Malaysia and Australia, and the migration to six economies never reached it. For Chinese it matches nothing, so the function silently falls back to a 6,000-character window before the provision; near the top of a short instrument that window starts at Article 1. The column is reviewer context rather than filed evidence, so this misleads without corrupting -- which is exactly why it survived a migration that checked the evidence path. A per-economy heading pattern (`第\d+条`, `Artigo \d+`, `ມາດຕາ \d+`) is half an hour; until then the sheet banner says the column is not what the English translates.

**~~Retry problem 16~~** — the code is in (`4136d55`, `c0b5510`); re-run `fetch` per economy to clear the
225, ~$4. That is a run, not a code change, so it is not freeze-bound.

---

## 5. Notes owed to other workshops

Findings go back as notes, never as edits. **All five are now written up in
`notes/2026-09-29-notes-for-extraction-and-collection.md`**, addressed to those workshops, with the
measurements and a re-derivation path for each. Two are new and extraction-stage; four are collection:

1. **The duplicate crawl** (20) — same statutes from two portals; the single cause of our duplicate rows.
2. **`www.gov.cn`** (21) — 11 documents against 924 from the NPC database; the largest single gold gap.
3. **Bare-domain URLs** (22) — 29 of China's 56 rows land a reviewer on a portal search page.
4. **Lao's Cyber Crime Law** (23) — one targeted check, not a crawl expansion.

5. **`law_name` not resolved per act** (29) — NEW, extraction. 364 of 364 multi-act TL documents carry
   one title across every act; `citation_confidence` says `exact` regardless. The cheap ask is not
   "fix the titles" but **"stop reporting `exact` when the title is the file's rather than the
   act's"**.
6. **How bad the Lao OCR is, per provision** (new) — 196 of 205 Lao provision glosses came back
   flagged as too damaged to render, against 10% for China. Not a request to re-run; a heads-up that
   a host reviewer checking a Lao row against the PDF will see it.

And one for the submission's own disclosures: the baseline records no article numbers, and two of the
instruments it cites are technical standards rather than legislation (24).
