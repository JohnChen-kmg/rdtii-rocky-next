# Plan: running Timor-Leste against the whole instrument

Written 28 September 2026, after S4–S10 completed for CN, LA and TL on the automated nine.

**What I take "the whole TL database" to mean:** Timor-Leste against all **61 in-scope indicators**
rather than the nine in pillars 6 and 7. Decision in `PLAN.md` was "Timor-Leste runs pillars 6 and 7
like the others; widen only if the workbook fills early". If you meant instead "every TL provision
rather than the selected candidates", say so — that is a different and much larger plan, and section
7 says what it would take.

## 1. Why TL is the right economy to widen

| | |
| :---- | :---- |
| corpus | **189,557 provisions across 1,026 documents** — second largest after Australia |
| filed so far | **27 rows** from the automated nine — the least productive corpus per provision |
| baseline | **none.** No Round 1 or Round 2 sheet exists for Timor-Leste |
| language | Portuguese, 99.6% OCR |

Two consequences. Every TL row is **NEW** by construction, because there is no sample kit to
reproduce — so TL rows are the strongest discovery evidence in the submission. And TL is the
diversity argument for C1a: a Portuguese, OCR-heavy, Southeast-Asian corpus that no other economy in
our set resembles.

189,557 provisions yielding 27 rows is the imbalance worth fixing. The cause is not retrieval —
it is that we only ever asked TL nine questions out of 61.

## 2. What this does NOT need

Measured, not assumed:

- **No re-crawl and no re-extraction.** The corpus is already in the index.
- **No re-embedding of provisions.** `embeddings.f16.npy` holds all 189,557 TL vectors. Only the
  query side changes, and 61 query documents embed in seconds.
- **No new code.** `select_cell()` already accepts an `indicator_class`, `config/selection.json`
  already carries a `class_defaults` block for exactly this case, and `settings.INDICATORS` is
  already read from the instrument.
- **No instrument work.** All **61/61** in-scope indicators have a signature with usable
  `definition_text`, so every query document builds. I verified this.

So the whole thing is a settings-and-runtime exercise. That matters: it stays available after the
30 September code freeze.

## 3. The one real blocker: 52 indicators have no selection parameters

`selection.json` defines θ, floor and ceiling for exactly the nine. `params_for()` **refuses** an
unknown indicator rather than guessing, and names the way through: assign one of four classes —
`horizontal_instrument`, `prohibition`, `recurring_duty`, `subject_specific`.

That choice dominates everything. Measured on TL's real cosines, all 61 indicators:

| class assumed for the 52 | automated 9 | other 52 | **total candidate pairs** |
| :---- | ---: | ---: | ---: |
| `subject_specific` (θ 0.60, ceiling 800) | 5,856 | 9,801 | **15,657** |
| `horizontal_instrument` (θ 0.55, ceiling 400) | 5,856 | 19,700 | **25,556** |
| `prohibition` (θ 0.57, ceiling 1,200) | 5,856 | 36,093 | **41,949** |
| `recurring_duty` (θ 0.55, ceiling 1,800) | 5,856 | 72,957 | **78,813** |

**A 7.4× spread.** Classifying the 52 is therefore the first task, not an afterthought, and the rule
is already written in `class_defaults`' own `_` field:

> `level == economy` → horizontal_instrument; binary [1,0] scoring with a duty that recurs across
> sectoral statutes → recurring_duty; a duty defined by its subject matter → subject_specific;
> prohibition phrasing that also appears in secrecy provisions → prohibition

Only 2 of the 61 carry `level: economy` (7.1 and 7.2, both already parameterised), so the other 52
must be classified from their scoring set and phrasing. That is a reading task over 52 codebook
blocks — an hour, and it is the kind of judgement that should not be scripted blind.

## 4. Cost and time, from tonight's measured TL rates

Measured this run, Timor-Leste only: **$0.00167 per triage pair**, **19.1% triage keep**, **1.21
pairs per provision**, **$0.00778 per mapped provision** on the batch lane, **0.127 fires per
provision**, **$0.0147 per verified fire**.

Under the middle assumption (`subject_specific` for all 52 — 9,801 new pairs):

| stage | volume | cost | wall clock |
| :---- | ---: | ---: | :---- |
| S1 query embed + TL top-K | 61 queries | $0 | ~2 min, GPU |
| S2 select | 9,801 pairs | $0 | seconds |
| S3b triage | 9,801 pairs | **$16** | ~18 min |
| S4 map, batch lane | ~1,547 provisions | **$12** | ~10 min queue |
| S5 blind verify | ~196 fires | **$3** | ~3 min |
| **total** | | **~$31** | **under an hour** |

If the 52 land mostly in `recurring_duty` instead, the same arithmetic gives **~$234** and about four
hours. So the classification is worth doing carefully: it is the difference between $31 and $234.

Expected yield, at TL's measured rates: roughly **196 fires → ~125 upheld after verification**
(TL's overturn was 40.6%) → perhaps **40–60 filed rows** after the NEW cap and the audit-trio gate.
That would take TL from 27 rows to something like 70–90, all NEW, spread across ten pillars no other
economy in our set covers.

## 5. The quality caveat that actually constrains this

**Tier.** Of the 52, **14 are Tier B and 38 are Tier C**. The instrument's own `HANDOFF.md` lists
"review of the 14 Tier B drafts" as an *open* precondition, and Tier C is thinner still. The nine we
have been running are all Tier A.

So widening TL means judging provisions against codebook blocks that have not been reviewed to the
standard the nine have. That is a real accuracy risk on C1b, and it is the reason to stage:

1. **Tier B first** — 14 indicators. Review those blocks (already an open instrument task), then run.
2. **Tier C second**, and only if the Tier B rows come out clean.

I have not measured the Tier B subset's volume separately; that is one more run of the same probe and
should be done before committing.

**Three TL-specific risks already measured:**

- **36% of TL provisions have a null `act_index`** (68,867). Those are mappable but **not filable**:
  the act cannot be pinned to the article. Expect the filable fraction to be well below the fire count.
- **OCR noise reaches the quotes.** TL is 99.6% OCR. Tonight's TL quotes are the longest of the three
  economies (median 153 characters) and read cleanly, but Notes must say OCR.
- **Law names are unreliable.** Tonight two TL rows cited "Conselho Contabilístico de Timor-Leste"
  (a body, not an act) and an MFA organic law paired with labour-inspectorate reasoning. Widening to
  ten more pillars multiplies exposure to this. The plan's own rule — "refuse a row whose law name is
  a gazette issue title rather than an act" — is **not yet implemented** and should be before a wide
  TL run, or the extra rows will carry the defect at scale.

## 6. The sequence I would follow

| # | step | who | cost |
| :---- | :---- | :---- | ---: |
| 1 | Classify the 52 into the four classes, from the codebook, by the documented rule | attended, ~1 h | $0 |
| 2 | Re-measure candidate volume with the real classification (the probe in §3) | minutes | $0 |
| 3 | Implement the gazette-title refusal, or accept and disclose | code, before 30 Sept | $0 |
| 4 | Run Tier B only: queries → top-K → select → triage → map → verify → emit | ~30 min | ~$10 |
| 5 | Read every Tier B row. If they hold up, proceed | attended | $0 |
| 6 | Run Tier C | ~1 h | ~$20–200 |
| 7 | Re-run `gold_after_triage.py` — note TL contributes **no** gold rows, so this measures volume, not recall | minutes | $0 |

Steps 1–3 are the real work. Steps 4–6 are the cheap part.

## 7. If you meant every TL provision rather than the selected candidates

Different plan, and I would argue against it. Mapping all 189,557 TL provisions against 61
indicators is 11.6M pairs. Even at the batch lane's $0.00778 per provision and one call per
provision rather than per pair, that is **~$1,475** and roughly 40 hours of queue, to replace a
selection step that tonight's measurements show is not the binding constraint on recall: a uniform
2× ceiling across all cells gained **zero** gold rows (M14). The candidate set is not what is
costing us rows.

The honest version of "run everything" is §6: ask TL all 61 questions, with selection still doing its
job on each.

## 8. What I would not do

- **Do not widen CN or LA the same way** without a separate decision. Both have baselines, so their
  extra rows compete with reproduction rows for the 101 workbook slots, and both are cheaper to
  improve by fixing the 165 incomplete verdicts first.
- **Do not tune the 52 classes against gold.** TL has no gold rows at all, so there is nothing to
  overfit to here — which is another reason TL is the safe economy to widen. Keep it that way: the
  classification comes from the codebook, not from what produces more rows.

---

# RAN, 28 September 2026 — actuals

Completed against the 52 indicators outside pillars 6 and 7. The plan's step 1 (classify the 52) was
done from the codebook by the rule in `class_defaults`: **33 `subject_specific`, 19 `prohibition`**,
no `horizontal_instrument` because only 7.1 and 7.2 carry `level: economy` and both were already
parameterised. Timor-Leste has no gold rows, so nothing here could be fitted to a baseline.

| stage | volume | cost | time |
| :---- | ---: | ---: | ---: |
| S1 retrieval, 61 indicators | cached embeddings | $0 | dense 0.3 min, bm25 a few min |
| S2 select | **17,342** candidate pairs | $0 | seconds |
| S3b triage | 17,286 pairs, kept 3,549 (**21%**) | **$27.54** | 31 min |
| S4 map, batch | 2,519 provisions, **316 fires** | **$30.16** | 10 min |
| S5 blind verify | 316 fires, 48 overturned (**15.2%**) | **$7.93** | 4 min |
| **total** | | **$65.63** | ~50 min |

**Output: 83 rows = 44 scored + 39 no-provision.** Findings in 13 of the 52 indicators, across five
pillars:

| pillar | indicators with a finding | rows |
| :-- | :---- | ---: |
| 2 | 2.1, 2.3 | 9 |
| 3 | 3.3, 3.5 | 11 |
| 5 | 5.1, 5.4, 5.7 | 10 |
| 8 | 8.3, 8.4 | 2 |
| 12 | 12.4.4, 12.5, 12.8, 12.9 | 12 |

Language of Source 83/83 Portuguese. Audit trio complete on every scored row. `row_recall: null`,
correctly — TL has 0 resolvable gold rows.

**Timor-Leste now carries 65 scored rows across 61 indicators** (21 from pillars 6–7, 44 from the
other ten), up from 21. Every one is NEW by construction.

## Three corrections to this plan's own estimates

1. **Cost was $65.63, not $55.** Triage and verify landed within a few percent; **mapping came in at
   $0.01197 per provision against the $0.00778 I projected**, because I used the nine-indicator rate.
   With 52 indicators in scope a provision draws more candidate indicators, so its prompt is longer.
   **The per-provision mapping rate is not constant in the size of the indicator set** — only the
   mapper scales this way, and any future sizing must say which indicator count its rate came from.
2. **The verifier was gentler here, not harsher**: 15.2% overturned against 40.6% on the nine. The
   crisp cells in pillars 2–12 (retention, registration, notification duties) behave like 7.3 did.
3. **39 of 52 indicators found nothing**, which is itself the finding for a small economy — but it
   means 39 no-provision rows with a blank Discovery Tag (decision H4). That is a lot of blank-tag
   rows for one economy and wants a look before they are filed.

## One defect this run exposed

`newknown.py` required `baseline_rows.jsonl` and died on `FileNotFoundError` for an economy that has
no baseline at all — the third instance of pattern P1 in
`notes/2026-09-28-problems-register-and-root-causes.md`. Fixed in `8ada48b`; S7 now says "every fire
is NEW by construction" instead of stopping.

## Not done from this plan

Step 3, the **gazette-title refusal**, is still not implemented — and this run makes it more
pressing, because "Timor-Leste Accounting Council" (a body, not an act) already appears as a Law Name
among the pillar 6–7 rows and the surface area just tripled.
