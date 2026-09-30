# The sparse leg returns nothing at all for China and Lao PDR

Measured 2026-09-27 on the real six-economy index, not inferred.

## What was measured

S0 ingest and the BM25 leg were run over hand-off #2 (766,526 provisions plus 579 chunks) into
`C:\Users\woshi\Desktop\rdtii-finale-p3-runs\run_2026-09-27`. For each of the nine automated
indicators the leg stores its top 50,000 corpus rows — 450,000 slots in total. Counting those rows
by economy:

| Indicator | CN | LA | TL | SG | MY | AU |
| :---- | ---: | ---: | ---: | ---: | ---: | ---: |
| 6.1 | **0** | **0** | 723 | 10,942 | 7,630 | 30,705 |
| 6.2 | **0** | **0** | 444 | 11,444 | 9,580 | 28,532 |
| 6.3 | **0** | **0** | 3,635 | 9,608 | 5,964 | 30,793 |
| 6.4 | **0** | **0** | 1,680 | 14,461 | 8,294 | 25,565 |
| 7.1 | **0** | **0** | 10,720 | 7,753 | 4,060 | 27,467 |
| 7.2 | **0** | **0** | 452 | 11,575 | 6,780 | 31,193 |
| 7.3 | **0** | **0** | 290 | 12,712 | 9,166 | 27,832 |
| 7.4 | **0** | **0** | 1,814 | 9,867 | 5,699 | 32,620 |
| 7.5 | **0** | **0** | 183 | 12,786 | 9,431 | 27,600 |
| **Total of 450,000** | **0** | **0** | 19,941 | 101,148 | 66,604 | 262,307 |

Corpus share for comparison: AU 39.4%, TL 24.7%, SG 14.4%, MY 9.5%, CN 6.5%, LA 5.4%.

## What it means

**China's 50,026 provisions and Lao's 41,534 are invisible to the sparse leg.** Not
under-represented — absent. The reason is the alphabet, not the tokeniser. Measured on the same
index, over a 20,000-row sample:

| Economy | Latin letters, share of characters | Spaces per 100 characters |
| :---- | ---: | ---: |
| AU | 75.8% | 16.2 |
| MY | 76.2% | 16.4 |
| SG | 74.6% | 16.4 |
| TL | 74.7% | 14.9 |
| **CN** | **0.7%** | 2.0 |
| **LA** | **0.4%** | 7.4 |

The query side is the other half of the measurement: each indicator's query document, built from
the signature's name, definition and keywords, is **entirely ASCII** — 0 non-ASCII characters in
6.1's 1,554, one curly quote in 7.3's 1,263. BM25 scores on tokens two texts share. An English
query and a corpus that is 99.3% non-Latin share none, whatever either side is split on.

Note that Lao does use spaces (7.4 per 100 characters, between phrases rather than words), so
`bm25s.tokenize` produces plenty of Lao tokens. They are simply Lao.

**Timor-Leste is present but 5.6 times under-represented** — 4.4% of slots against a 24.7% corpus
share. Portuguese tokenises correctly, so the failure there is only that the signature keywords
are English.

So for three of six economies, **the dense leg is not a second opinion, it is the only retrieval
path.** For China and Lao it is the whole mechanism.

## The consequence that matters before the freeze

`main.py:575-577` runs the BM25 leg only and writes an **empty** `dense_top.npz` stub:

```
run_step("P3 S1 prefilter (bm25 leg only)", … "--leg", "bm25", …)
_stub_dense_leg(index_dir)
```

That is the path the interface drives, the path a reviewer gets by deploying the repository, and
the path the live test uses. On it, **a China or Lao run retrieves zero candidates and therefore
produces zero rows** — while reporting success.

Two of the nine live-test economies are China and Lao. This is code, so it cannot be fixed after
30 September, and it would be discovered on the morning of 15 October with a steward watching.

**Action: the live path must run the dense leg, at least for a non-English economy.** The owner of
`main.py` decides how — always run it, or run it when the drawn economy's language is not English.
Documenting the limitation is not sufficient, because the limitation is "this economy yields
nothing".

## One thing this validates

The scored selection function adopted on 26 September thresholds on **dense cosine**, not on fused
rank. That is exactly the right shape for these economies: where the sparse leg contributes
nothing, a fused-rank cap would be diluted by a leg that has no opinion, while a cosine threshold
is unaffected. See `2026-09-26-selection-cap-function.md`.

## The check still outstanding

This measures only that the sparse leg is blind. It does **not** yet show that the dense leg sees
those economies well. The dense run over 767,105 rows is in progress; when it finishes, count its
top-K by economy the same way. If China and Lao are also thin there, the problem is retrieval as a
whole rather than one leg, and that is a Section 4 readiness gap rather than a bug.

Related: the measured language offsets for the dense leg were small — Portuguese −0.03, Chinese
−0.02, Lao −0.01 — which is the reason to expect it does see them. That measurement is in
`2026-09-24-experiment-proposal.md`.

## Does fixing this need another package?

Asked 2026-09-27. **No — and the package that looks like the fix is not one.**

**The wrong fix: a CJK/Lao tokeniser.** `jieba` for Chinese, `laonlp` or ICU for Lao, or a
dependency-free character-bigram split, would all segment the corpus side properly. None of them
would return a single extra row, because the query is in English and the corpus is not. A
tokeniser changes how a text is cut up, not which alphabet it is written in. This is worth stating
plainly because it is the obvious-looking fix and it would cost a day of the three that are left.

**What the sparse leg would actually need** is the indicator query documents in Chinese and Lao —
nine short documents, our own material, not host data — plus a segmenter for each language so the
translated terms can match. That is a translation step, a new dependency for Lao segmentation
(ICU needs native libraries, which is a poor thing to add to an environment a judge will deploy),
and no measured retrieval quality. It is post-deadline work.

**What is needed instead, and needs no package:** BGE-M3, the dense leg, is trained
cross-lingually and scores an English query against Chinese or Lao text directly. It is already
the leg that runs for all six economies, and the selection function already thresholds on its
cosine. Two supporting measurements:

- the selection harness's dense-only arm reproduces the gold gate (37/37) and leaves all 22
  economy scores unchanged at 7,864 candidate pairs per economy. The BM25 top-up adds 269 pairs
  per economy and touches two indicators (6.4, 7.3);
- the measured language offsets are small — Portuguese −0.03, Chinese −0.02, Lao −0.01 — so one
  threshold plus a per-language offset covers all six corpora.

So the fix for China and Lao is **J6, not a dependency**: make the live path run the dense leg
instead of writing an empty stub. The cost of that is compute time, which we have, rather than a
new package in a frozen environment.

**Still to confirm** (unchanged by this section): that the dense leg *sees* CN and LA well. The
count-by-economy of its top-K is the check, and it needs the run in progress to finish.