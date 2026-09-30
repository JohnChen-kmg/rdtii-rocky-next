# The selection cap function: why it exists, how it is defined, and what every variable means

Written 2026-09-26. **Status: a proposal, verified against Round 1's own artifacts.** Nothing here is
settled until it has a `DECISIONS.md` entry. No API money was spent producing any number in this note:
every measurement comes from files already on disk in the Round 1 reference arm.

Charts of the central result: <https://claude.ai/artifact/QQyDPSqmCfdXhwb1DMhB7b>

---

## 1. The problem this solves

Selection decides what the expensive stages see. Steps S0 to S2 and S6 to S10 are free arithmetic;
every dollar in this stage is spent in S3 triage, S4 mapping and S5 verification, and what reaches them
is decided entirely by the caps in `select.py:28-31`.

Round 1 used nine hand-set integers, one per indicator, each applied per economy:

| Indicator | 6.1 | 6.2 | 6.3 | 6.4 | 7.1 | 7.2 | 7.3 | 7.4 | 7.5 | Sum |
| :---- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Direct cap | 500 | 300 | 200 | 500 | 150 | 200 | 600 | 200 | 600 | **3,250** |

Plus a gray band of three times the cap, screened by a cheap model. Three economies therefore produced
10,213 direct and 30,667 gray pairs: 40,880 of a possible 3,713,085, or 1.10%.

Three things are wrong with that design, and each is measured below.

1. **The integers were not derived from anything.** Some were three times larger than the deepest row
   they ever admitted; three were cutting evidence off at the ceiling.
2. **The numbers cannot move after 30 September.** They are code, and code freezes. The live test names
   its economy and indicators on the morning of 15 October.
3. **Two stages truncate on quality grounds.** When a gold row goes missing, the cap and the triage are
   both candidates and nothing records which did it.

## 2. Method

Everything rests on reconstructing, for each of Round 1's filed evidence rows, where its provision sat
in the rankings that produced it.

| Step | How |
| :---- | :---- |
| Recover the ranking | `out/select/direct_pairs.jsonl` and `gray_pairs.jsonl` carry the fused RRF score per pair. Sorting both together per (economy, indicator) gives one continuous rank. **Both bands together is the right frame**: raising a cap converts a gray pair into a direct one |
| Recover each leg | `data/index/bm25_top.npz` and `dense_top.npz` hold the top 50,000 row indices and scores per indicator. Filtering each to one economy gives that economy's rank in that leg, and the dense score |
| Identify the filed rows | `out/submission/records_*.csv` has no provision id, so each row is joined through `out/discovery/newknown_*.jsonl` on (economy, indicator, law name, article). **135 of 142 rows resolve**; the 7 that do not are 6.1 ×2, 6.3 ×3, 7.4 ×1 and 7.5 ×1, and the three 6.3 rows are consistent with no-provision rows, which have no provision to point at |
| Re-run the official gate | The gold recall gate is replicated exactly as `select.py:124-174` computes it, including the absence-row exclusion and the token-set law matcher. Denominator: **37 resolvable gold rows** |
| Check the deliverable | Economy scores are recomputed as the max over retained verified fires and compared with `out/rollup/economy_scores_*.json`, all 27 cells |

Three metrics, in increasing order of what they actually protect:

- **Gold recall** — the stage's own pre-registered gate, threshold 0.95. Protects the claim.
- **Filed-row retention** — does a row that reached the submission still reach the mapper. Protects the output.
- **Economy scores** — the numbers the index publishes. Protects the deliverable.

## 3. What the measurements say

### 3.1 The funnel, and where filtering actually happens

| After | Documents | Share | Pairs |
| :---- | ----: | ----: | ----: |
| S0, the corpus | 2,486 | 100% | 3,713,085 possible |
| S2 selection | 1,216 | 48.9% | 40,880 (1.10%) |
| S3 triage | 801 | 32.2% | 16,730 into S4 |
| S4, at least one fire | 426 | 17.1% | 3,620 fires |
| S5, fire survives | 339 | 13.6% | 2,328 verified |
| S9 filed | 84 laws | 3.4% | 142 rows |

S2 halves the document set while keeping 1.1% of the pairs: aggressive per indicator, generous per
document. That is the right way round — a law stays in play while irrelevant pairings are dropped.

### 3.2 Depth: half the rows are shallow, and the tail is very long

Median filed row sits at rank **41**. The 90th percentile is **351**. The deepest is **2,480**.

| Depth | 25 | 50 | 100 | 200 | 300 | 600 | 1,000 | 1,500 | 2,000 | 2,400 |
| :---- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Filed rows retained | 29% | 42% | 50% | 59% | 67% | **80%** | 90% | 94% | 99% | 99% |

**The curve never flattens.** Going from 2,000 to 2,400 still adds a row, so Round 1 was still finding
usable evidence at the deepest rank it ever examined. Where the tail truly ends is unknown.

Per indicator, the deepest filed row and today's cap:

| Indicator | p50 | p90 | Max | Cap | Verdict |
| :---- | ---: | ---: | ---: | ---: | :---- |
| 6.1 ban | 979 | 979 | 979 | 500 | cut by the ceiling |
| 6.2 storage | 32 | 293 | 481 | 300 | cut by the ceiling |
| 6.3 infrastructure | — | — | — | 200 | produced no traceable row |
| 6.4 conditional | 7 | 23 | **35** | 500 | 14× oversized |
| 7.1 framework | 26 | 291 | 291 | 150 | cut by the ceiling |
| 7.2 cybersecurity | 107 | 169 | 390 | 200 | cut by the ceiling |
| 7.3 retention | 359 | 997 | **1,566** | 600 | cut by the ceiling |
| 7.4 DPO/DPIA | 29 | 73 | **73** | 200 | 3× oversized |
| 7.5 gov access | 369 | 1,642 | **2,480** | 600 | cut by the ceiling |

### 3.3 The gray band earns its place

30 of the 135 filed rows — **22% of the submission** — arrived through the gray band, along with 1,055 of
2,328 verified fires. An earlier suggestion of mine, to drop triage and the gray band, is wrong on this
evidence. The open question is how deep the gray band should go, not whether it exists.

### 3.4 The two legs are not equal, and not equal in the same way

Rank of the filed rows within each leg, per economy:

| Indicator | BM25 p50 | BM25 max | Dense p50 | Dense max | Best leg max |
| :---- | ---: | ---: | ---: | ---: | ---: |
| 6.2 storage | 935 | 8,007 | **19** | 1,108 | **221** |
| 6.4 conditional | **7** | 6,883 | 16 | 118 | **36** |
| 7.1 framework | 57 | 7,068 | **35** | 83 | **83** |
| 7.3 retention | 432 | 3,592 | 293 | 6,972 | 961 |
| 7.5 gov access | 725 | 5,479 | 437 | 3,105 | 2,463 |

Dense beats sparse overall — 70% against 48% retention at depth 300 — but not everywhere. 6.4's keyword
rank of 7 is the phrase "except in accordance" doing its job; 7.3's tail is better in BM25 than in dense.
Two 7.5 rows are **absent from BM25's top 50,000 entirely**.

At equal pair budget, fused RRF still beats taking top-N from each leg (67% against 61% at 300 pairs), so
the existing fusion design holds. What does not hold is treating all nine indicators alike.

### 3.5 The dense score is comparable across cells, and rank is not

Every filed row in the submission scored at least **0.540**, with p10 at 0.597 and the median at 0.657 —
across eight indicators, three economies and rank depths spanning three orders of magnitude.

A control makes the significance clear: **random** provisions score 0.379–0.406 on average and top out at
**0.51** against four indicator queries. So a threshold near 0.55–0.60 sits just above the noise ceiling.

| Score floor | Filed rows retained | Pairs per economy |
| :---- | ----: | ----: |
| 0.55 | 99% | 48,753 |
| **0.60** | **90%** | **9,102** |
| 0.65 | 55% | 1,216 |

At 0.60 that is ten points more recall than today's caps for 30% fewer pairs.

And the count above the floor scales with the corpus without being told to: **7.7% of provisions in
Singapore, 7.6% in Malaysia, 5.9% in Australia.**

### 3.6 Indicator density varies 150-fold, and that is structural

Candidates above 0.60 as a share of the corpus:

| Indicator | SG | MY | AU | Mean | Spread | Distinct laws in its filed rows |
| :---- | ---: | ---: | ---: | ---: | ---: | ---: |
| 7.3 retention | 16.44% | 15.28% | 9.66% | **13.79%** | 6.78pp | **31** |
| 7.5 gov access | 8.18% | 6.74% | 7.86% | 7.59% | 1.44pp | **33** |
| 7.2 cyber | 2.89% | 2.34% | 2.48% | 2.57% | 0.55pp | 9 |
| 6.1 ban | 1.53% | 4.46% | 1.70% | 2.56% | 2.93pp | 4 |
| 6.2 storage | 2.18% | 1.59% | 0.98% | 1.58% | 1.20pp | 19 |
| 6.4 conditional | 0.66% | 0.90% | 0.17% | 0.58% | 0.72pp | **5** |
| 7.1 framework | 0.35% | 0.46% | 0.11% | 0.31% | 0.35pp | 3 |
| 6.3 infrastructure | 0.30% | 0.12% | 0.25% | 0.22% | 0.18pp | 3 |
| 7.4 DPO/DPIA | 0.11% | 0.15% | 0.02% | **0.09%** | 0.13pp | **5** |

Three structural properties explain the range, and two are already fields in the codebook.

**What the duty attaches to.** 6.4 asks whether transfer is permitted only if conditions are met; 7.4
whether a DPO must be appointed. Only a data instrument says those things: 15 and 8 rows from **5 laws
each**. 7.3 asks whether *any* law requires a minimum retention period, and 7.5 whether government can
compel data without judicial authorisation. Every sectoral statute does bookkeeping and every enforcement
statute grants production powers: 36 and 39 rows from **31 and 33 laws** — income tax, banking,
companies, superannuation, provident fund, employment.

**The scoring range.** All three binary `[1, 0]` indicators are the awkward ones: 6.3, 7.3, 7.5. Every
ordinal `[1, 0.5, 0]` indicator has a half point for sectoral scope — a drafting signal that its authors
expected the obligation in an identifiable horizontal instrument. And because a binary cell scores as a
max, **one verified instance sets it to 1**: ranks 500 to 2,480 in 7.3 and 7.5 cannot change any score.
They add row count and NEW claims only.

**Level.** 7.1 and 7.2 are inverted ("does the economy *lack* …") and marked `level: economy`. 7.1
produced exactly **one filed row per economy** from about 300 candidates. Candidates there only need to
identify and characterise one controlling act.

What does *not* explain the range: keyword count. 7.5 has 18 keywords and 6.4 has 16, and their densities
differ 13-fold.

One outlier worth naming: **6.1 costs 2,134 candidates per filed row**, the worst ratio in the pipeline,
and Malaysia's density is triple Singapore's. The cause is that "shall not transfer" and "must not
disclose outside" pervade banking-secrecy provisions that are not localisation bans. That is a precision
problem; the mapper's `conditional_path_exists` trap fixes it, not depth.

### 3.7 Depth does not scale with corpus size

| Indicator | SG (95,469 prov) | MY (65,443) | AU (251,653) | AU/MY depth ratio |
| :---- | ---: | ---: | ---: | ---: |
| 7.3 retention | 4,701 | 6,689 | 6,972 | **1.04** |
| 7.5 gov access | 2,348 | 3,105 | 2,869 | **0.92** |

Australia holds **3.85×** Malaysia's provisions and needs the same depth. So the ceiling must not be
multiplied by corpus size. Corpus size belongs in the threshold-bound count, where it already lives.

### 3.8 Language costs almost nothing in score

Same provision, source text against an English gloss, scored against the same query. 20 paired
provisions per language, four indicator queries:

| Language | 6.4 | 7.3 | 7.1 | 6.2 | Pooled | Implied θ adjustment |
| :---- | ---: | ---: | ---: | ---: | ---: | ---: |
| Portuguese | +0.019 | +0.025 | +0.034 | +0.038 | **+0.029** | −0.03 |
| Chinese | +0.014 | +0.006 | +0.021 | +0.037 | **+0.020** | −0.02 |
| **Lao** | +0.002 | +0.005 | −0.007 | +0.025 | **+0.006** | −0.01 |

BGE-M3 is genuinely cross-lingual on this text. The feared starvation of Lao by a global threshold does
not appear.

---

## 4. The function

For each economy `e` and indicator `i`:

```
1. score       sᵢ(p) = cos( embed(p), embed(qᵢ) )
2. threshold   θᵢ,L  = θᵢ + δ_L                       L = language of e's corpus
3. candidates  S     = { p ∈ corpus(e) : sᵢ(p) ≥ θᵢ,L }, ordered by sᵢ descending
4. clamp       N     = clip( |S| , mᵢ , Mᵢ )          extend below θ to reach mᵢ
5. band        direct = sᵢ ≥ θ_direct  → mapper
               gray   = θᵢ,L ≤ sᵢ < θ_direct → triage
6. sparse      S ∪= top bᵢ by BM25                    only where BM25 measurably wins
7. report      record which term bound: θ, m, or M
```

### 4.1 Every variable

| Symbol | Name | Type | Where it comes from |
| :---- | :---- | :---- | :---- |
| `e` | economy | code, e.g. `SG` | the run's task. Replaces the hard-coded `ECONOMIES` list at `settings.py:78` |
| `i` | indicator | decimal text, e.g. `7.3` | `indicator_order.yaml`, host order. Never float-parsed: `4.01` ≠ `4.1` |
| `L` | language | ISO code, e.g. `lao` | `language_of_source` on the provision record, read from the crawler, never detected |
| `p` | provision | record | one line of `provisions.jsonl` |
| `qᵢ` | query document | text | `signatures/<i>.yaml`: name + `definition_text` + keywords + up to two exemplar impacts, assembled by `prefilter/queries.py:14` |
| `sᵢ(p)` | relevance score | cosine, 0–1 | BGE-M3 embedding of the provision's prefilter text against `qᵢ`. **Comparable across indicators and economies**, §3.5 |
| `θᵢ` | score threshold | 0.53–0.62 | per indicator, from the p10 of that indicator's filed-row cosines, §5 |
| `δ_L` | language offset | −0.03 … 0 | measured, §3.8. `eng` 0, `por` −0.03, `zho` −0.02, `lao` −0.01 |
| `S` | candidate set | set of provisions | everything at or above the threshold |
| `\|S\|` | its size | count | **this is where corpus size enters** — measured at 6–8% of provisions |
| `mᵢ` | floor | 100–300 | the minimum a cell is looked at, so a null result is evidenced rather than assumed |
| `Mᵢ` | ceiling | 400–1,800 | the budget guard. **Flat per indicator; never multiplied by corpus size**, §3.7 |
| `N` | selected count | count | what the cell actually hands on |
| `θ_direct` | band split | 0.65 | above it, straight to the mapper; below, the cheap screen first. Replaces `GRAY_MULT = 3` |
| `bᵢ` | sparse top-up | 0–300 | BM25 union, non-zero only for 6.4 and 7.3, §3.4 |

### 4.2 Constants the chain uses, all measured in Round 1

These convert a candidate count into money and hours. They are not free parameters.

| Symbol | Value | What it is | Evidence |
| :---- | ----: | :---- | :---- |
| `f` | 0.30 | share of candidates in the direct band | share above 0.65 |
| `κ` | 0.213 | triage keep rate | 6,517 kept of 30,667 judged |
| `ρ` | 1.9 | mapper pairs per provision call | MY: 5,200 pairs → 2,738 provisions. **English only — measured 1.45 on CN/LA/TL, 27 September** (6,549 pairs → 4,530 provisions), so 1.9 under-counts mapper calls outside English by ~30% |
| `φ` | 0.216 | fires per mapped pair | 3,620 of 16,730 |
| `σ` | 0.64 | share of fires surviving verification | 2,328 of 3,620 |
| `c_triage` | $0.00155 | per triage pair | $0.31 per 200, `ab_triage_report.json` |
| `c_map` | $0.016 / $0.0088 | per mapped provision, live / batch | SG main run; MY $24.01 ÷ 2,738 |
| `c_verify` | $0.0114 | per verified fire | MY $9.18 ÷ 807 |
| prefix factor | 1.23 | mapping input inflation for the finale codebook | 31,915 chars against Round 1's 25,974, measured |

`c_triage` is the softest of these: the cost ledger discloses the production triage figure as
**unevidenced**, so it carries an order of magnitude, not a decimal.

### 4.3 The variables this replaces, and what happens to each

Every knob in the current selection path, with its disposition. Two of them do nothing today.

| Variable | Where | Value | Disposition |
| :---- | :---- | :---- | :---- |
| `CAPS` | `select.py:28-31` | nine integers, 150–600 | **Replaced** by `Mᵢ`, and moved to config |
| `GRAY_MULT` | `select.py:32` | 3 | **Replaced** by `θ_direct`: the band split becomes a score boundary rather than a multiple |
| `PREFILTER_FLOOR` | `settings.py:39`, used at `select.py:89` | 0.008 | **Replaced** by `θᵢ`. It was an RRF-score floor, and an RRF score is a deterministic function of rank, so it never carried absolute meaning |
| `RRF_K` | `select.py:26` | 60 | **Kept.** Fusion still orders the candidate set; only the cut changes |
| `HINT_BOOST` | `select.py:33` | 0.35 | **Dead.** Boosts an indicator when `obligation_type` aligns, and every tag in hand-off #2 is null |
| `NONPERSONAL_DAMP` | `select.py:34` | 0.85 | **Dead**, same reason |
| `OBLIGATION_ALIGN` | `select.py:35-36` | 4-entry map | **Dead**, same reason. Also keyed by legacy indicator IDs |
| `TOP_K` | `bm25.py:20`, `dense.py:22` | 50,000 | **Replaced** by score-based storage. It is per indicator across all economies, and it still lost two 7.5 rows |
| `PREFILTER_TOPK` | `settings.py:38` | 3 | **Read by nothing.** `PLAN.md:252` documents it as the per-provision candidate cap, and the shipped code caps per cell instead. Delete it or wire it; leaving a documented knob that does nothing is worse than either |
| `MAX_COST_USD_PER_DOC` | `settings.py:53` | 0.25 | **Kept** as an S4 guard |
| `COST_HARD_STOP` | `settings.py:54` | 400 | **Kept**, but must be set deliberately: the projected live-lane run is $419 |

### 4.4 Why this shape and not another

- **A score, not a rank, is the primary control** because the score means the same thing in every cell
  (§3.5) while rank does not (§3.2). Rank at 300 is generous for 6.4 and starvation for 7.5.
- **A ceiling as well as a threshold**, because for the diffuse indicators no affordable threshold
  exists: catching 7.3's deepest row needs θ ≈ 0.54, which admits 16% of the corpus.
- **A floor as well**, because a cell with no candidates cannot evidence a "no provision found" row, and
  those rows are a required output.
- **Which term binds classifies the indicator.** θ binds → sparse. M binds → diffuse. m binds → nothing
  found. That is also why every cell must record its binding term: it converts a silent truncation into
  a stated limit.
- **Corpus size is implicit.** An explicit `#provisions` coefficient would need fitting and could be
  inflated by boilerplate — Australia's tax and corporations acts would earn it candidates it does not
  need. Through `|S|` the scaling is automatic and content-based.

## 5. Parameters, with the provenance of each value

| Indicator | Class | θ | m | M | Why this θ | Why this M |
| :---- | :---- | ---: | ---: | ---: | :---- | :---- |
| 6.1 ban | prohibition, low precision | 0.56 | 150 | 1,800 | min filed 0.568 | AU's only row sits at dense rank 1,635; and 6.1 is the cell most likely to fire in China |
| 6.2 storage | prohibition, low precision | 0.59 | 150 | 1,200 | min filed 0.597 | deepest 481, headroom for a denser jurisdiction |
| 6.3 infrastructure | subject-specific | 0.58 | 150 | 800 | no filed row; class default | density 0.22%, θ binds anyway |
| 6.4 conditional | subject-specific | 0.61 | 100 | 800 | min filed 0.617 | deepest 36; M never binds |
| 7.1 framework | economy-level | 0.55 | 100 | 400 | **deliberately loose** — see below | one act per economy; M does the selecting |
| 7.2 cybersecurity | economy-level | 0.53 | 100 | 600 | min filed 0.543 | deepest 390 |
| 7.3 retention | recurring duty, binary | 0.53 | 300 | 1,800 | min filed 0.540 | tail is unaffordable; score saturates at the first instance |
| 7.4 DPO/DPIA | subject-specific | 0.62 | 100 | 500 | min filed 0.630 | deepest 73; the cheapest cell in the pipeline |
| 7.5 gov access | recurring duty, binary | 0.58 | 300 | 1,800 | min filed 0.592 | deepest 2,480; same saturation argument |

**7.1 is a deliberate methodological choice, not a fitted value.** The single gold miss on the first pass
was `r1-sg-039`, where the host cites Singapore's Banking Act 1970 s.47 as 7.1 evidence; its best
provision scores 0.594 against a θ of 0.61. Setting θ = 0.58 recovers it and passes 37/37 — with a margin
of **+0.014**, a threshold fitted to one row. Any change of embedding model, OCR text or jurisdiction
would lose it again. So θ drops to 0.55 and the ceiling does the selecting instead.

The general rule that follows: **θ is vulnerable to score drift, M is vulnerable to corpus size.** Use θ
where the scores separate cleanly, and let M bind where they do not.

Safety margins over all 37 gold rows: median **+0.146**, and after the 7.1 change only two rows sit under
0.07 (AU 6.4 at +0.049, AU 7.1 at +0.068).

## 6. Verification

| | Today's caps | This function |
| :---- | ----: | ----: |
| Candidate pairs per economy | 13,627 | **7,464** (−45%) |
| **Gold recall gate** (≥0.95 required) | 37/37 | **37/37** |
| **Economy-score cells changed** | — | **none.** 22 of the 27 cells held a verified fire and all 22 keep their maximum; the other 5 held none and are unaffected |
| Verified fires retained | 100% | 81% |
| Filed rows retained | 100% | **88%** |

By economy: Singapore 34/39 (87%), Malaysia 50/55 (91%), Australia 35/41 (85%). NEW rows: 90 of 105 (86%).

By indicator: 6.2 **22/22**, 6.4 **15/15**, 7.1 **3/3**, 7.4 **7/7**, 7.2 11/12, 7.5 31/38, 7.3 29/36,
6.1 1/2. Every loss sits in the two binary diffuse indicators, where the extra rows are further instances
of an obligation already scored.

Variants tested, all on the same artifacts:

| Variant | Pairs per economy | Filed retained |
| :---- | ----: | ----: |
| θ + per-law cap 3 | 2,785 | 43% |
| θ + per-law cap 25 | 3,923 | 75% |
| θ, no per-law cap | 4,151 | 80% |
| θ at min filed score | 4,166 | 80% |
| **the same, ceilings ×2 (adopted)** | **7,284** | **88%** |
| ceilings ×3 | 9,940 | 94% |

**The workbook holds 101 rows.** Round 1 filed 142 from three economies, so at 88% across six economies
the reachable pool is roughly 200–250 rows for 101 slots. Nothing lost here was going to be filed.

## 7. What was tried and rejected

| Rejected | Why |
| :---- | :---- |
| **A per-law cap** (at most k provisions per law per cell) | Measured harmful: k=3 drops retention to 43%. It cuts the *right* provision inside the *right* law, because the filed row is often not that law's highest-scoring provision. Rows-per-law statistics do not predict this |
| **A name- or title-based filter** | A title-only screen over Round 1's own output would drop 55 of 84 laws and 75 of 142 rows. Retention and storage duties live in tax, banking, companies and superannuation acts whose titles say nothing about data |
| **Screening with a cheap model instead of retrieval** | Without S1 and S2 there is no candidate set, so the screen must judge every pair: 6.9M calls at nine indicators, 46.8M at 61 |
| **An explicit `#provisions` term in M** | Depth does not scale with corpus size (§3.7), and a percentage-of-corpus rule under-serves Australia, whose corpus is diluted by very large acts |
| **θ fitted to the single gold miss** | A +0.014 margin is overfitting; the ceiling is the robust mechanism (§5) |
| **Dropping the gray band and triage** | My own earlier suggestion. It would cost 22% of the submission (§3.3) |

## 8. The limits of these limits: the four-stage system

Each stage needs a limit, but only one may own the tradeoff.

| Stage | Limit | Unit | Rule |
| :---- | :---- | :---- | :---- |
| S1 retrieval | index depth | ranks or score | **Derived.** Store everything above `min(θᵢ) − 0.03`. If a rank cap is kept it must be ≥ 4·Σₑ Mᵢ, because the list is global across economies and Australia skews it. Today's `TOP_K = 50,000` lost two 7.5 rows anyway |
| S2 selection | θ, m, M | pairs | **The single owner of the cost/recall tradeoff** |
| S3 triage | none | proportion | **A monitor, not a cap.** Alarm below 10% keep (over-filtering) and above 40% (not filtering). Round 1 sat at 21.3% |
| S4/S5 | budget, fire rate | dollars, fires per provision | **Guards.** A dry-run projection refuses to start above the cap; a fire rate far above 0.3 signals a prompt or model fault, not a discovery |

The stages chain, so they cannot be tuned independently:

```
N → f·N direct + (1−f)·N gray → triage keeps κ → mapper pairs ÷ ρ → provisions × c_map → dollars
```

Which means the honest direction of derivation is **budget first**: fix the run budget, give every cell
its floor `mᵢ`, then allocate what remains by marginal yield — measured as candidates per filed row, from
27 for 7.4 up to 2,134 for 6.1.

## 9. Cost and time

For the planned run: Timor-Leste across 61 indicators, the other five economies at pillars 6 and 7.

| | Current caps | This function |
| :---- | ----: | ----: |
| Candidate pairs | 153,084 | **~63,700** |
| Triage | $178 | **$69** |
| Mapping | $569 live / $313 batch | **$280 / $154** |
| Verification | $154 | **$70** |
| **Total** | **~$901 live / $645 batch** | **~$419 / $293** |
| Wall clock | ~16 h | **~9 h** |

Round 1 spent US$281.59 on three economies and nine indicators, so this does six economies — one across
all 61 indicators — for about what Round 1 cost.

Three consequences:

1. **The free local triage lane becomes usable.** At 3.0 s per pair measured, triage locally is 24 h under
   today's caps and about **9 h** under this function: an overnight run, and it matters for the claim that
   the pipeline runs with no proprietary service.
2. **The embedding is now the bottleneck** — 3 h 30 of the 9 h, and no cap change touches it.
3. **`COST_HARD_STOP` defaults to 400.** The live-lane estimate is $419, so either run bulk through the
   batch lane or raise the guard deliberately.

## 10. Threats to validity

1. **The analysis is censored.** Only rows Round 1's own caps admitted can be seen. Anything deeper than
   its observed limit is invisible to both designs, so "88%" means 88% of what was findable then.
2. **37 gold rows and 135 filed rows** are a thin basis for nine thresholds. The per-indicator θ for 6.3
   rests on no filed row at all.
3. **Three English common-law economies.** Every derived constant — `κ`, `ρ`, `φ`, `σ` — comes from them.
4. **δ_L is measured at the wrong end of the scale.** The 20 sampled provisions per language are random,
   so their cosines sit at 0.30–0.45, below where θ operates. And the gloss is machine-made, which biases
   the measured offset *downward*: a poor translation scores lower and hides a real penalty. That matters
   most for Lao. **The 53 Lao laws with publisher English settle it** — human translation, same law, both
   languages — and those files are on disk but never reached hand-off #2.
5. **Timor-Leste's 52 extra indicators have no measured density.** They must inherit class defaults from
   `level`, `scoring.values` and duty type, then be corrected after one run.
6. **One unmeasured assumption.** Retention asks whether a filed row's provision still reaches the
   mapper. It assumes the mapper returns the same verdict when that provision arrives with a slightly
   different candidate-indicator list. At temperature 0 on identical text that should hold; it is worth a
   sample check during phase 2.

## 11. Implementation

- **Config, not code.** θ, δ_L, m, M, θ_direct and b live in a JSON file the interface can also read
  (decision M1 keeps configuration in JSON). Code freezes 30 September; settings may change, so the
  sealed live-test task can be met by tuning rather than editing.
- **Replaces** `CAPS`, `GRAY_MULT` and `PREFILTER_FLOOR` at `select.py:26-36`, and the dead hint-boost
  loop at `:76-83` — dead because every tag in hand-off #2 is null.
- **Per-cell report line**, in `select_report.json`: candidates, binding term, keep rate, fires, verified.
  One attributable cause per missing row.
- **Before production**: calibrate δ_L on the new index per language, and re-run this verification per
  economy using the Round 2 gold rows for China and Lao PDR.

## 12. Requests this raises

| To | What |
| :---- | :---- |
| Instrument | Add `evidence_shape` per indicator: `horizontal_instrument \| subject_specific \| recurring_duty`. It is the third key the class assignment needs, and the only one not already in the codebook. Without it, Timor-Leste's 52 indicators are classified by hand |
| Collection, extraction | Carry the 53 Lao publisher translations through as a gloss field. They settle δ_L for Lao, and they are better evidence for a reviewer than any model output |

## 13. Implemented, 2026-09-26

Three new files in the repo, none of them wired into the live path yet:

| File | What |
| :---- | :---- |
| `stages/p3-map/config/selection.json` | every parameter, with the reason for each value in its own `note` field. Settings, so 15 October tuning needs no code |
| `stages/p3-map/config/selection.py` | `params_for(...)` resolves a cell; `select_cell(ranked, ...)` returns the selection, the band split and **which term bound it**. Stdlib only, so the interface can read the same file. An indicator with no entry and no class **raises** rather than defaulting, the same habit as M5's unpriced model |
| `stages/p3-map/tests/test_selection.py` | 21 tests: each binding term, the band split, the language offset changing what is selected, legacy IDs accepted, a float ID refused, overrides winning, a generator consumed in one pass |

**Verified through the shipped module**, replayed over the Round 1 reference arm:

| | Dense only | With the BM25 top-up |
| :---- | ----: | ----: |
| Candidate pairs per economy | **7,864** | 8,133 |
| Gold recall gate | **37/37** | 37/37 |
| Economy scores changed | **none of 22 scored cells** | none |
| Filed rows retained | **120/135 = 89%** | 120/135 |
| NEW rows retained | 91/105 = 87% | 91/105 |
| Verified fires retained | 1,881/2,328 = 81% | 1,897/2,328 |

Binding terms across the 27 cells: **θ in 8, M in 16, m in 3.** That distribution is the taxonomy of
§3.6 showing up in the run log rather than in an argument.

`python -m config.selection` prints the resolved table and validates the file.

### 13.1 No tolerance margin was added

The developer's call, 2026-09-26, after the cost was measured: use the function as verified. For the
record, what was measured before deciding — a θ margin buys nothing on known data because the ceilings
already absorb the extra candidates, while raising ceilings does buy rows:

| Change | Pairs per economy | Filed rows kept |
| :---- | ----: | ----: |
| as verified | 7,864 | 120 |
| θ − 0.01 | 8,597 (+9%) | 120 |
| θ − 0.02 | 9,233 (+17%) | 120 |
| θ − 0.05 | 9,666 (+23%) | 120 |
| ceilings ×1.10 | 8,524 (+8%) | 122 |
| ceilings ×1.50 | 10,658 (+36%) | 127 |

The sweep is worth keeping for a second reason: **even a badly chosen θ only moves the total from 7,864
to 9,666, because the ceilings bound it.** The architecture is insensitive to getting θ wrong, which is
the main reason to trust it on an economy we have not calibrated.

### 13.2 One finding from running it: the direct band is not calibrated

`direct_band` is a single 0.65 for every indicator, and per cell the split lands unevenly:

| | Direct | Gray |
| :---- | ----: | ----: |
| Singapore | 789 | 7,344 |
| Malaysia | 895 | 7,238 |
| **Australia** | **1,964** | 6,169 |

Australia's 7.5 alone puts **1,701 provisions straight to the mapper**, against Round 1's 600 for that
cell. Averaged across economies the direct band is still far below Round 1's 3,250, and mapper volume
roughly halves — about 2,689 mapper pairs per economy against 5,460 — but one cell now carries a
disproportionate share of the expensive path.

Two candidate fixes, neither adopted yet: a per-indicator `direct_band`, or a `max_direct` share of the
cell. Both are settings. Measure which on the phase-2 sample rather than choosing now.

## 14. Reproducing this

All of it reads the reference arm at `C:\Users\woshi\Desktop\RDTII\pipeline-data\rdtii-p3-map`, which
must stay unchanged. Nothing writes to it.

| Input | Used for |
| :---- | :---- |
| `out/select/{direct,gray}_pairs.jsonl` | the fused ranking |
| `data/index/{dense,bm25}_top.npz`, `corpus_ids.json` | per-leg rank and dense score |
| `out/discovery/newknown_*.jsonl` | joining filed rows to provision ids |
| `out/submission/records_*.csv` | the 142 filed rows |
| `out/verify/verified_*.jsonl` | fires and `final_applies` |
| `out/rollup/economy_scores_*.json` | the 27 cells |
| `contracts/instrument/gold/gold_set.jsonl`, `data/index/doc_meta.json` | the gold recall gate |
| `rdtii-finale-0-instrument/instrument/output/signatures/*.yaml` | query documents, and θ calibration |
