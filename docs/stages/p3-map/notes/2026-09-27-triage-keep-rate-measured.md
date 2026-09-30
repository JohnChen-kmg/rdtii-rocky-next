# The triage keep rate for China, Lao and Timor-Leste, measured

27 September 2026. Cost of the measurement: **$0.98**. It was run because every derived constant in
`notes/2026-09-26-selection-cap-function.md` — κ, ρ, φ, σ — comes from three English common-law
economies, and the three economies we map fresh are none of those. κ was a projection for them, not
a measurement.

## What κ actually is

Measured from the frozen Round 1 arm, read-only:

| pass | file | judged | kept | rate |
| :---- | :---- | ---: | ---: | ---: |
| S3a local (`qwen2.5:14b`) | `triage_results.jsonl` | 29,250 | 4,917 | **16.8%** |
| S3b Haiku (`claude-haiku-4-5`) | `haiku_results.jsonl` | 30,667 | 6,517 | **21.3%** |

So **κ = 0.213 is the Haiku pass**, exactly. Per economy: S3b kept AU 30.8%, MY 13.8%, SG 17.7%;
S3a kept AU 20.6%, MY 12.2%, SG 17.5%. The local model is not systematically permissive — it sits a
few points below Haiku on English.

## The new measurement

150 gray pairs per economy through S3b, scoped with `ECONOMIES`:

| economy | gray band | keep | vs κ | $/pair | S3b cost |
| :---- | ---: | ---: | :---- | ---: | ---: |
| **CN** | 10,637 | **68%** | **3.2× κ** | $0.00193 | $20.56 |
| LA | 4,185 | 24% | ≈ κ | $0.00293 | $12.28 |
| TL | 6,353 | 23% | ≈ κ | $0.00167 | $10.59 |
| | 21,175 | | | | **$43.43** |

Three things follow.

**Lao and Timor-Leste validate the projection.** 24% and 23% against κ = 21.3%. Nothing about the
cap function or the cost model needs revising for them.

**China does not.** 68% is 3.2× κ, above the 40% "not filtering" alarm the cost note set. This is
very likely a consequence of our own recall fix rather than a defect: China's gray band is the
largest at 10,637, and it is large because of the four measured overrides added on 27 September
(6.2 floor 800, 7.4 floor 600 ceiling 700, 7.5 ceiling 3,800), which took the gold gate from 0.871
to 0.968. A wider net at lower cosine returns more borderline-but-genuine content. China's corpus is
also genuinely dense in cross-border provisions — PIPL, DSL, CSL and their implementing measures.
The 68% costs about **$42 extra in S4** against a counterfactual China at κ. That is the price of the
recall those overrides bought, and C1a/C1b pay for found rows.

**The $/pair constant was English.** $0.00155 measured on SG/MY/AU understates all three: Lao is
$0.00293, nearly 2× it, because OCR-heavy Lao script tokenises badly. So S3b is **$43.43**, not the
$32.82 that `PLAN.md` carried.

## Sizing the rest from measured rates

| | pairs | calls | live | batch |
| :---- | ---: | ---: | ---: | ---: |
| S3b triage | 21,175 | — | **$43** | n/a |
| S4 mapping | 10,045 candidates | 5,287 (÷ ρ=1.9) | $85 | $47 |
| S5 blind verify | ~2,170 fires (× φ=0.216) | — | ~$25 | ~$25 |
| **total remaining** | | | **~$153** | **~$115** |

`PLAN.md` F1 projected "~23,600 candidate pairs, ~5,600 mapper calls, $162 live / $112 batch". The
mapper-call figure holds almost exactly (5,287 against 5,600) and the totals land within 6%, so the
plan's F1 budget was sound even though its pair count was high — the scored selection function cut
candidate volume without cutting calls.

## The full run, and where the pre-flight misled

S3b ran to completion the same evening: **21,175 judged, 6,181 kept = 29.2%, 0 errors, $40.44 in
38 minutes** (plus the $0.98 pre-flight).

| economy | pre-flight (150) | **full band** | vs κ |
| :---- | ---: | ---: | :---- |
| CN | 68% | **35.7%** | 1.7× |
| LA | 24% | **27.8%** | 1.3× |
| TL | 23% | **19.1%** | 0.9× |
| all | | **29.2%** | 1.4× |

**The pre-flight over-read China by nearly 2×.** `--limit` takes a prefix of `gray_pairs.jsonl`, and
that file is ordered, so the first 150 China pairs were its highest-cosine ones — the easy end of the
band. The lesson is about the instrument, not China: a `--limit` pre-flight measures the *head* of a
sorted band, so it is an upper bound on the keep rate, not an estimate of it. A future pre-flight
should sample randomly. The $42 "extra S4 cost" projected from 68% was overstated; at 35.7% China
costs about $11 more than a China at κ.

Nothing about the conclusion changes: Lao and Timor-Leste sit at κ, China is modestly above it, and
the whole band at 29.2% is inside the 10–40% monitor the cost note set.

| by indicator | judged | kept | rate |
| :---- | ---: | ---: | ---: |
| 6.1 | 2,971 | 792 | 26.7% |
| 6.2 | 1,100 | 230 | 20.9% |
| 6.3 | 1,179 | 235 | 19.9% |
| 6.4 | 687 | 305 | 44.4% |
| **7.1** | 1,137 | **639** | **56.2%** |
| **7.2** | 1,746 | **1,017** | **58.2%** |
| 7.3 | 5,621 | 1,070 | 19.0% |
| 7.4 | 797 | 288 | 36.1% |
| 7.5 | 5,937 | 1,605 | 27.0% |

### 7.1 and 7.2 are why the hand-off must precede S4

Those two cells are **27% of everything triage kept** — 1,656 pairs, about 872 mapper calls. The
shipping codebook says of both: *"ECONOMY-LEVEL: answer once per economy. Per-provision citations of
a data-protection act tagged 7.1 are not discoveries and score zero."* So the number of rows wanted
from those 1,656 keeps is **six**: one per economy per cell.

The vendored Round 1 codebook does not carry that rule. Run S4 against it and the mapper judges 872
calls with no economy-level instruction, fires on many, and the emitter files per-provision rows the
host scores zero — which is exactly what `PLAN.md` H3 exists to prevent. Run S4 after the hand-off
and the rule is in the cached prefix the model is instructed with.

Triage itself is unaffected: S3b's prompt uses only `name` and `definition_text` from the signature
files, and both are byte-identical across the two vintages (9/9 verified). The mapper is the stage
that reads the codebook blocks, and those differ in all nine.

### Resized again, from actuals

| | | batch |
| :---- | ---: | ---: |
| S3b triage | done, 21,175 pairs | **$41.42 spent** |
| S4 mapping | 6,549 candidates → 3,447 calls | ~$28 (+15% margin ~$32) |
| S5 blind verify | ~1,415 fires (× φ=0.216) | ~$16 |
| **remaining** | | **~$48** |

## Two code fixes this required

Both are code, so neither could have been made after 30 September.

1. **Neither triage pass honoured `ECONOMIES`.** `local.py` and `haiku.py` each read the whole
   `gray_pairs.jsonl` and never consulted `SETTINGS.economies`, so a scoped run judged all 42,263
   pairs instead of the 21,175 in scope — double the cost, half of it on SG/MY/AU whose rows are
   reused from Round 1. Worse for the live test: on 15 October the draw is **one** economy, and an
   unscoped triage would have spent the hour judging five economies nobody asked about.
2. **S3b had no `--limit`,** so there was no way to price a pre-flight. `local.py` already had one.
   Added, mirroring it, with the reason in the code: κ is a projection outside English, and judging
   a few hundred pairs first costs cents and sizes the real run.

## One thing this does not settle

The 200-pair local S3a sample run first was **100% China** — `gray_pairs.jsonl` is ordered by
economy and `--limit` takes a prefix. Its 86% keep is therefore a China-only figure and not
comparable to the 16.8% Round 1 local rate across three economies. Worth knowing that qwen answered
in Chinese with substantive reasons ("提及向境外提供个人信息", "提及重要数据出境安全管理规定"), so the
high keep was judgement, not abstention — but S3a remains the A/B arm, not a predictor of S3b.
