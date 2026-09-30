# The cap function as it stands, what it is measured to do, and what is deferred

Written 2026-09-27 after the six-economy run (`run_2026-09-27`, 767,105 provisions). Everything
here is measured on that index or on the frozen Round 1 arm; nothing is projected except where it
says so. The derivation this supersedes in detail — not in principle — is
`2026-09-26-selection-cap-function.md`. The settled conclusions are DECISIONS M12.

---

## 1. The function

    N(economy, indicator) = clip( |{ p : cos(p, query) >= theta + delta(language) }|, floor, ceiling )

Take every provision whose dense cosine against the indicator's query document clears that
indicator's threshold shifted by the economy's language offset; never fewer than the floor, never
more than the ceiling. At or above cosine **0.65** a candidate goes straight to the mapper; between
theta and the band it gets the triage screen first.

Five terms, five different questions: **theta** what counts as relevant · **delta** how the
language shifts the score scale · **floor** how deep to go when the threshold finds little ·
**ceiling** what we can afford · **0.65** what needs no screening.

| Indicator | Class | theta | floor | ceiling | sparse top-up |
| :---- | :---- | ---: | ---: | ---: | ---: |
| 6.1 | prohibition | 0.56 | 150 | 1,800 | 200 |
| 6.2 | prohibition | 0.59 | 150 | 1,200 | 0 |
| 6.3 | subject-specific | 0.58 | 150 | 800 | 0 |
| 6.4 | subject-specific | 0.61 | 100 | 800 | 100 |
| 7.1 | horizontal instrument | 0.55 | 100 | 400 | 0 |
| 7.2 | horizontal instrument | 0.53 | 100 | 600 | 0 |
| 7.3 | recurring duty | 0.53 | 300 | 1,800 | 300 |
| 7.4 | subject-specific | 0.62 | 100 | 500 | 0 |
| 7.5 | recurring duty | 0.58 | 300 | 1,800 | 0 |

Language offsets: `eng 0.000 · zho -0.020 · lao -0.010 · por -0.030 · msa -0.030 · unmeasured -0.030`

Per-(economy, indicator) overrides, each earned by a named gold row:

| Cell | Override | The row that earned it |
| :---- | :---- | :---- |
| SG 7.1 | ceiling 400 → 600 | r1-sg-039, Banking Act 1970, in-economy rank 538, cosine 0.594 vs theta 0.550 |
| CN 7.5 | ceiling 1,800 → 3,800 | r2-cn-067 and r2-cn-070 at ranks 2,302 and 3,416 |
| CN 6.2 | floor 150 → 800 | r2-cn-043, Map Management Regulations, rank 798, cosine 0.563 vs theta 0.570 |
| CN 7.4 | floor 100 → 600, ceiling 700 | r2-cn-065, Cybersecurity Law, rank 560, cosine 0.568 vs theta 0.600 |

Index depth `PREFILTER_TOPK = 150,000`. At the old 50,000 the cut sat **above** theta for 7.3 and
7.5, so the index decided those cells rather than the threshold. Everything above lives in
`config/selection.json` and `.env`, which are settings; `SELECT_MODE=caps` reverts to Round 1's
fixed caps exactly, verified cell for cell.

---

## 2. What it is measured to do

| | |
| :---- | ---: |
| candidate pairs | **46,494** — direct 4,231, gray 42,263 |
| per economy | CN 10,978 · AU 8,995 · SG 8,104 · MY 7,852 · TL 6,366 · LA 4,199 |
| against the fixed caps it replaced | 13,000 per economy, so **40% fewer** |
| gold gate at this stage | **61 of 63 = 96.8%**, target 0.95 |
| cells by binding term | ceiling 28 · theta 15 · floor 11 · exhausted 0 |
| projected cost, CN+LA+TL | $86 live, $67 with the batch lane |
| projected cost, all six | $210 live, $159 batch |

### Gold at this stage, by economy

| Economy | Law absent | Resolvable | Retrieved | This stage |
| :---- | ---: | ---: | ---: | ---: |
| Singapore | 0 | 12 | 12 | 100% |
| Malaysia | 9 | 15 | 15 | 100% |
| Australia | 1 | 9 | 9 | 100% |
| China | 10 | 21 | 20 | 95.2% |
| Lao PDR | 3 | 6 | 5 | 83.3% |
| Timor-Leste | 0 | 0 | — | no baseline sheet |
| **All** | **23** | **63** | **61** | **96.8%** |

### Gold at this stage, by indicator class

| Class | Resolvable | Retrieved | This stage |
| :---- | ---: | ---: | ---: |
| prohibition (6.1, 6.2) | 11 | 11 | 100% |
| horizontal instrument (7.1, 7.2) | 11 | 11 | 100% |
| recurring duty (7.3, 7.5) | 27 | 26 | 96.3% |
| subject-specific (6.3, 6.4, 7.4) | 14 | 13 | 92.9% |

### End to end, measured on the Round 1 arm

Every stage of that run left an artifact, so this is measurement:

| Economy | Resolvable | Selected | Mapped | Fired | Verified | Filed | End to end |
| :---- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Australia | 9 | 9 | 9 | 9 | 8 | 8 | 88.9% |
| Malaysia | 15 | 15 | 15 | 13 | 13 | 12 | 80.0% |
| Singapore | 12 | 12 | 12 | 9 | 9 | 9 | 75.0% |
| **All** | 36 | 36 | 36 | 31 | 30 | 29 | **80.6%** |
| *survival per step* | — | 100% | 100% | 86.1% | 96.8% | 96.7% | |

By class: subject-specific 100% · horizontal instrument 85.7% · recurring duty 76.5% ·
prohibition 71.4% — the losses sit where the traps are.

**That 86.1% is understated, and section 5 explains why.** Corrected, mapping fires on 31 of 33
rows where firing is the right answer, about 94%, and end to end becomes about 88%.

**Predicted end to end** = 96.8% × downstream. About **81%** for the three English economies,
**77%** for China, **67%** for Lao PDR — the last resting on six rows, so one row moves it 17
points.

---

## 3. Should the cap depend on corpus size? No. Measured.

Asked because Lao has the fewest provisions. The share of corpus selected runs 2.97% (Australia,
302,564 provisions) to 20.58% (China, 50,026) under identical absolute caps — **anti-correlated
with size**, because a threshold follows the density of relevant law rather than the amount of it.
The three economies at 100% gold retrieval span 72,614 to 302,564 provisions with no size term.

Three further reasons it would be wrong:

- it would spend more where retrieval is already perfect;
- it would break the live hour, where an absolute cap keeps the cost box fixed whichever economy
  is drawn, while a size-scaled one hands Australia seven times Lao's budget for the same hour;
- the deviation does not track size anyway — see section 4.

**Also tested and rejected: a sparsity-aware floor**, `m_eff = max(m, 3 × n_above)`, which extends
deeper automatically when little clears theta. It reaches CN 6.2 but not CN 7.4 (444 against a rank
of 560) or LA 6.4 (69 against 1,679). It adds a term without buying a row.

---

## 4. What *does* vary is the shape of each language's distribution

Where theta lands inside each economy's own cosine distribution, averaged over the nine indicators:

| Economy | Corpus | Percentile of theta | vs the English reference |
| :---- | ---: | ---: | ---: |
| Australia | 302,564 | 97.59 | — |
| Singapore | 110,810 | 96.63 | — |
| Malaysia | 72,614 | 96.78 | — |
| Timor-Leste | 189,557 | 99.14 | **+2.14 stricter** |
| China | 50,026 | 93.35 | **−3.65 looser** |
| Lao PDR | 41,534 | 97.85 | +0.85 stricter |

The two smallest corpora deviate in **opposite directions**, and the second-largest is the
strictest of all. So the variable is language, not size — and the offset that would equalise it:

| Language | Configured | Measured by percentile |
| :---- | ---: | ---: |
| Portuguese | −0.030 | **−0.056** |
| Lao | −0.010 | **−0.023** |
| Chinese | −0.020 | **+0.007** |

The paired-gloss experiment got Portuguese and Lao right in direction and about half in magnitude,
and got Chinese **wrong in sign**: Chinese provisions score higher against an English query than
English provisions do, which is why China's cells take 20.6% of its corpus.

Recalibrating rebalances the run — TL 5,856 → 8,666, LA 4,199 → 5,385, CN 10,978 → 8,308, net +2.9%
pairs — and costs one gold row, a Chinese row that had been scraping in under an accidentally loose
threshold. Enlarging Lao's offset buys nothing at all: −0.03 costs +54% of Lao's volume for zero
gold rows, −0.05 costs +112% for zero.

**Proposed, not done:** compute delta at run time by quantile matching rather than reading it from
the config, keeping the configured values as an override. Six of the nine live-test languages have
no measured offset, and the `_default` of −0.03 can land anywhere between the 76th and the 99.99th
percentile.

---

## 5. Is the query method the problem? Measured: no, for Claude on English

The largest loss after coverage is the mapper declining to fire on a gold row, 5 of 36. Reading all
five:

| Gold row | Score | The mapper's reason | Assessment |
| :---- | ---: | :---- | :---- |
| MY 6.1 r1-my-038 | **0** | conditional path exists → 6.4, not a ban | correct; score 0 means no ban |
| MY 6.2 r1-my-041 | **0** | no requirement to keep a domestic copy | correct |
| SG 7.1 r1-sg-039 | **0** | sectoral banking secrecy, not the framework; the PDPA controls 7.1 | correct, and sharper than the gold row |
| SG 7.3 r1-sg-042 | 1 | enabling clause; no minimum duration in this provision | right about the text: the 12-month rule is a licence condition, not in the Act |
| SG 7.3 r1-sg-045 | 1 | period is prescribed elsewhere; no explicit floor here | right about the text: the two years are in the Employment (Records) Regulations |

**Three of the five are the model correctly declining a score-0 row.** The other two are cases
where the operative rule sits in delegated legislation the mapper never saw — the same family as
the 23 gold rows whose law is not in the corpus at all.

**None of the five is a prompt problem.** Coverage costs 23 rows; judgment costs 2.

What this evidence does **not** cover: all 36 rows are Claude reading English. There is one data
point on another model (qwen2.5:14b reproducing one trap case, 2026-09-26) and **none on Chinese or
Lao**, because no non-English mapping run has happened.

---

## 6. The query's language is worth changing; the embedder is not

Chinese query documents written for three cells, scored against China's cached embeddings:

| Cell | English query | Chinese query | |
| :---- | :---- | :---- | :---- |
| 6.2 | rank 798, cosine 0.563 | **rank 66, cosine 0.666** | 12× |
| 7.4 | rank 560, cosine 0.568 | **rank 320, cosine 0.669** | 1.75× |
| 7.5 | rank 12,992, cosine 0.527 | **rank 2,391, cosine 0.634** | 5.4×, and reachable at all only this way |

It improves discrimination, not merely level: for 7.4 the median Chinese cosine moves 0.457 → 0.497
while the 99th percentile moves 0.571 → 0.653, so the spread widens from 0.114 to 0.156. A model
that were only rescaling would move both equally.

Separation (p99 − p50) under the English query, which is how much ranking signal the embedder
extracts, shows Lao is the worst case of the six and a same-language query beats every English
economy:

| Economy | 6.2 | 7.4 | 7.5 |
| :---- | ---: | ---: | ---: |
| Singapore | 0.116 | 0.116 | 0.137 |
| Malaysia | 0.107 | 0.109 | 0.152 |
| Australia | 0.103 | 0.104 | 0.151 |
| Timor-Leste | 0.105 | 0.097 | 0.116 |
| China | 0.095 | 0.113 | 0.133 |
| **Lao PDR** | **0.097** | **0.084** | **0.104** |
| China, Chinese query | **0.126** | **0.156** | **0.162** |

**A different embedding package is not the answer.** Every cross-lingual embedder pays this
penalty and BGE-M3 is among the strongest at it; swapping models might buy a few percent, asking
the question in the corpus's language bought 12×.

**And with a Chinese query the original caps suffice**: 6.2 and 7.4 are selected with no override
at all, which means those two floor overrides are paying for a retrieval handicap. Only CN 7.5
still needs its ceiling, because rank 2,391 is outside 1,800 whatever theta does.

Unverified for Lao: the mechanism should be identical and Lao has the most to gain, but a Lao query
needs a native or a translation tool, and Lao carries a second handicap the query cannot fix —
99.6% OCR at about 94% character agreement.

---

## 7. The parameters that are not caps

For triage and mapping there is deliberately no budget cap: the screen is recall-biased, errors
default to KEEP, and the mapper judges whatever selection hands it. The caps live at emit.

| Stage | Parameter | Value | After the freeze? |
| :---- | :---- | :---- | :---- |
| S3 triage | screening model | `VERIFIER_MODEL` | **setting** |
| | workers · text sent · error default | 12 · 2,200 chars · KEEP | code |
| S3 local | context window · model | `OLLAMA_NUM_CTX` · `TRIAGE_MODEL` | **settings** |
| S4 mapping | model | `LLM_MODEL` | **setting** |
| | workers · text sent | 8 · 6,000 chars | code |
| | codebook prefix, traps, schema | instrument + code | frozen with the tag |
| | spend guards | `COST_HARD_STOP`, `MAX_COST_USD_PER_DOC` | **settings** |
| S5 verify | verifier, tiebreak | `VERIFIER_MODEL`, `ESCALATION_MODEL` | **settings** |
| **S9 emit** | **NEW-row confidence floor** | `NEW_CONF = 0.75` | **code** |
| | **NEW rows per cell** | `NEW_CAP = 8`, `NEW_CAP_TAIL = 10` | **code** |
| | sectoral rows per economy-level cell | `SECTORAL_MAX = 3` | code |
| | baseline match | `NEWKNOWN_SIM = 0.85` | **setting** |

**Proposed:** promote `NEW_CONF`, `NEW_CAP`, `NEW_CAP_TAIL` and the two worker counts to settings
before the freeze, defaults unchanged. On 15 October the draw is one economy and two indicators, so
`NEW_CAP = 8` caps the live export at roughly 16–20 NEW rows however much the tool finds, and a
0.75 confidence floor tuned on English could silently drop most of them on an unseen language.

---

## 8. What is deferred, and behind what

| Item | Status | Gate |
| :---- | :---- | :---- |
| Run-time delta by quantile matching | proposed, pre-freeze | worth doing on its own merits: TL and CN are mis-calibrated today |
| Run-time query translation for the drawn indicator and language | proposed, pre-freeze | measured 12× on Chinese; Lao unverified |
| Per-engine prompt profiles (the seam, not the content) | **deferred** | Block F's China run. If China's fire rate looks like Singapore's the prompt is portable and the seam buys nothing; if not, we will know why from the rationales |
| Promoting the emit knobs to settings | proposed, pre-freeze | ~20 minutes |
| A different embedding model | **rejected** | measured: the query's language dominates any plausible model difference |
| A corpus-size term in the cap | **rejected** | measured: deviation does not track size |
| A sparsity-aware floor | **rejected** | measured: reaches one row of three |
| Prompt experimentation for engine A | **rejected for now** | measured: 3 of 5 declines were correct, 2 were missing delegated legislation |

The model comparison itself — GPT, Kimi, DeepSeek against Claude and qwen — stays where the
24 September proposal put it: after the deadline. The only part with a pre-freeze deadline is the
seam that lets a prompt vary per engine, and that is now gated on China.

## 9. The ceiling is a budget dial, not a relevance filter — and cap tuning is model-conditional

Measured 27 September, after S3b triage, from the cached embeddings. This section exists because a
single gold miss (`r2-cn-065`, China's Cybersecurity Law on 7.4) looked like a triage defect and
turned out to be neither triage's fault nor the cap function's.

**What happened to that row.** The Cybersecurity Law has 162 provisions in the corpus. For 7.4
selection surfaced exactly one — Art. 73, cosine 0.568 — which sits in 第六章 法律责任, the legal
liability chapter, and cross-references Arts. 37/39/46 rather than stating any DPIA or DPO duty.
Triage dropped it, correctly, saying it "addresses penalties and legal liability for violations".
The article that carries the actual duty, Art. 21, ranked 782 at cosine 0.561 — outside the
ceiling of 700. **The penalties article outscored the duty article by 0.007.**

**The band at the ceiling is flat almost everywhere.** Doubling the ceiling moves the marginal
cosine by 0.010–0.031, i.e. under 0.004 per 100 ranks in **34 of 36 (economy, indicator) cells** —
including Australia, an English economy. Only CN 7.1 (0.0077) and CN 7.2 (0.0042) show real
gradient. So at its margin the ceiling is not choosing more-relevant over less-relevant text; it is
choosing how much to spend.

**And raising it buys nothing here.** A uniform ceiling multiplier against all 63 resolvable gold
rows:

| ceiling × | candidate pairs | vs now | gold reached |
| ---: | ---: | ---: | ---: |
| 1.00 | 45,141 | — | **61/63** |
| 1.25 | 53,937 | 1.19× | 61/63 |
| 1.50 | 61,375 | 1.36× | 61/63 |
| 2.00 | 72,599 | 1.61× | **61/63** |

Zero gold laws gained for 61% more pairs. The two selection misses are not ceiling-limited.

*Caveat on that table:* it scores whether **a** provision of the cited law was reached, so it cannot
see "a better provision of the same law". The Cybersecurity Law already counted as reached at 1.0×
through Art. 73. The table therefore says no new gold **law** becomes reachable — not that nothing
improves. Measuring provision-level quality needs the mapper's verdicts, which is a post-S4 probe.

### Why this is deferred rather than fixed

Three reasons, in order:

1. **No cap value fixes an inverted ordering.** Art. 73 above Art. 21 is a retrieval-quality
   failure inside one law. Budget cannot correct rank order.
2. **Tuning one cell to recover a known gold row is fitting to the host's database**, which the
   standing constraint forbids. The general finding (34/36 cells flat) is admissible evidence; "raise
   CN 7.4 until `r2-cn-065` comes back" is not.
3. **The flatness is a property of BGE-M3 at this depth, not of the task.** A different embedder may
   have real gradient in that band, which would make the ceiling meaningful again. So the threshold,
   the cap and the embedder have to be tuned **together**: numbers fitted hard to this embedder would
   silently fail to transfer, which is the worst possible input to the post-deadline model
   comparison.

So the values freeze as they are, and the experiment is named: **the best threshold and cap are
conditional on the retrieval model, and are tuned jointly with it after the deadline.** `θ`, the
floors, the ceilings and the language offsets all live in `config/selection.json`, reachable through
`SELECTION_CONFIG` without touching code, which is what makes this safe to defer past 30 September.

**Accepted cost of deferring:** the two selection misses (`r2-cn-069`, `r2-la-039`) and any row whose
best provision loses to a topically-similar sibling, as Art. 21 lost to Art. 73. At 61 of 63 laws
reached and 56 of 63 surviving triage, that is the measured price.
