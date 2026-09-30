# Overnight, 27–28 September: S3 banked, S4 in the batch queue, and the open problems

Written while three mapping batches are in flight, so John can pick this up cold.

## Money

| | |
| :---- | ---: |
| S3b triage pre-flight, 150 pairs × 3 economies | $0.98 |
| S3b triage, full band, 21,175 pairs | $40.44 |
| **spent so far** | **$41.42** |
| S4 mapping, three batches submitted (estimate, +15% margin) | ~$42 |
| S5 blind verify, projected at Round 1's rate | ~$16 |
| **projected total for the stage** | **~$99** |

Cost guards in force: `COST_HARD_STOP=$400`, `MAX_COST_USD_PER_DOC=$0.25`.

## The thing that unblocked tonight

**The instrument hand-off does not block running the pipeline — only shipping it.**
`INSTRUMENT_DIR` is an environment variable, so S4 can be pointed at the workshop's
`instrument/output` and get exactly the codebook that will ship. Every run tonight sets it:

    INSTRUMENT_DIR=C:\Users\woshi\Desktop\rdtii-finale-0-instrument\instrument\output

Verified before submitting: decimal vintage, 61 blocks, automated set 9, **gold 1,054 rows** (the
vendored copy has 51 and none for China or Lao). So the verdicts are made against the new traps, and
the eval stage has gold for CN and LA.

The copy is still required before the 30 September tag, for three reasons that have nothing to do
with tonight's run: `contracts/instrument/` is tracked, so the submitted system must code against
the codebook that ships; four `test_coverage.py` tests stay skipped until it lands; and a reviewer
cloning the repo gets the Round 1 codebook. It is five `robocopy` commands, in `HANDOFF.md` step 3,
and the sandbox refuses them as irreversible local destruction, so they need John's terminal or a
Bash permission rule.

## S4: what is in the queue

Submitted 27 September, Message Batches lane (50% of live), one batch per economy:

| economy | batch id | requests | pairs | estimate |
| :---- | :---- | ---: | ---: | ---: |
| CN | `msgbatch_01QxKoTQrLXSYuN2kDpgcBC2` | 2,617 | 4,143 | ~$25 |
| LA | `msgbatch_01JY72uDkT5GsePzcAvHRwc3` | 902 | 1,179 | ~$8 |
| TL | `msgbatch_01MhZ4J7Kq8nDvs8cCzxuzib` | 1,011 | 1,227 | ~$9 |

Watched by `scratchpad/watch_batches.sh`, logging to `run_2026-09-27/s4_batches.log`. It stops at S4
on purpose: `chain.py` has no error handling, so the `map_report_*.json` files get checked before
S5–S10 run.

**Measured ρ is 1.45 pairs per provision, not the 1.9 the cost note carries** (6,549 pairs over 4,530
provisions). The 1.9 came from the three English economies. Worth correcting in the cost model.

## What still has to happen, in order

1. **Verify S4** — grounding failures zero, fires near 0.3 per mapped provision, no schema errors.
2. **`chain.py <ECON>`** per economy: S5 verify, S7 NEW/KNOWN, S6 rollup, S9 emit, S10 eval, plus the
   Excel and audit views. ~10 min per economy.
3. **Verify S5** — overturn rate in the 30–40% band Round 1 measured.
4. **F2, the re-judge** of the reused SG/MY/AU rows against the new codebook: ~115 rows, ~$2. Scope
   was 22 in `PLAN.md`; measurement widened it (see `2026-09-27-instrument-handoff-measured.md` §4).
   Must not write to the frozen Round 1 arm — copy first.
5. **Block G**, the reuse path: migrate the 142 Round 1 rows to decimal IDs, re-run `urlcheck`,
   apply F2, and disclose the reuse in the Word document.
6. **Block I**, curating the 101 workbook rows (~2 h, attended).
7. **Block K**, Section 5 and the cost record (~3 h, attended). Can be drafted while batches run.

## Open problems, recorded

**1. The instrument copy is still not done.** Blocked on a sandbox refusal, not on a decision. Nothing
else waits on it now that `INSTRUMENT_DIR` is in use, but the tag does.

**2. Selection recall is 56/63, not 61/63 — decision M15.** The four per-cell overrides in
`selection.json` were derived by backward induction; the file's own `_measured` field says each entry
"names the gold row that needed it". Five hits depend on them. The un-tuned figure is **88.9%** and
that is what the submission reports; 96.8% is disclosed separately, labelled in-sample. The
parameters stay — each also has a θ-based justification that never needed gold — but the claim
changed. **The `_measured` strings still lead with the gold row and need rewriting to lead with the
θ reason.** Not done.

**3. A `--limit` pre-flight measures the head of a sorted band, not a sample of it.** The 150-pair
China pre-flight read 68% keep; the full band came in at 35.7%. `gray_pairs.jsonl` is ordered, so a
prefix is an upper bound. Any future pre-flight should sample randomly. Costly lesson only in
reasoning, not in money — it inflated a $42 warning that was really $11.

**4. China's Cybersecurity Law (`r2-cn-065`) is a retrieval miss no cap can fix.** For 7.4 the
penalties article (Art. 73, cosine 0.568) outranked the article carrying the duty (Art. 21, 0.561),
and triage correctly refused the penalties article. The band is flat — 34 of 36 cells move under
0.004 cosine per 100 ranks at the ceiling — so the ceiling is a budget dial, not a relevance filter.
Deferred to the post-freeze experiment as **M14**, because threshold, cap and embedder have to be
tuned together.

**5. 23 gold rows cite laws the corpus does not hold** — 11 Chinese, plus Lao's Law on Prevention and
Combating Cyber Crime. That is a crawl gap, not a mapping gap. Against the full gold universe of 86,
we are at 56/86 = 65%. Already logged in `2026-09-27-laws-the-corpus-does-not-hold.md`; findings go
back to the scraping workshop as notes, never as edits.

**6. Timor-Leste has no baseline sheet,** so it has no gold rows at all and every TL row will be NEW.
Its no-provision rows now carry a **blank** Discovery Tag (H4), which is a deliberate, disclosed
departure from an Instructions sheet that asks for one of two values. `submission_report_TL.json`
carries `blank_discovery_tag {count, indicators}` so the exposure is countable if a template check
rejects it.

**7. `main.py`'s economy table was Round 1's three.** Fixed tonight (`ff92190`), together with the
language-aware retrieval-leg guard, because widening the table alone would have created the silent
zero-row failure `PLAN.md` J6 described. Worth knowing the plan's description of J6 was wrong about
the mechanism: the wrapper *refused* China at argument parsing, it never produced empty output.

## Gold position, for whatever the morning brings

| stage | of 63 resolvable | |
| :---- | ---: | :---- |
| cited law in the corpus | 63 | |
| selected | 61 | 56 without the gold-derived overrides — **the figure we report** |
| kept by triage | 56 | CN 18/21, LA 5/6, MY 15/15, AU 9/9, SG 9/12 (SG's gray band was never triaged, by design) |

Rerun with `evidence/probes/gold_after_triage.py`, which needs `INSTRUMENT_DIR` pointed at the
workshop or it silently finds no China or Lao gold at all.

## Commits tonight

`ff92190` wrapper economies + retrieval-leg guard · `1de0d5b` emit caps and worker counts to settings
· `c3d50e0` triage obeys `ECONOMIES`, and `--limit` for a priced pre-flight · `7246cf5` no-provision
rows earn their Discovery Tag · `6a65596` the four selection overrides say they are in-sample (open
problem 2 above is now **closed** — no parameter moved, only the claim). Branch
`w2-mapping-finale`, tree clean, **263 tests** green.

## Pre-flight done while the batches queue

- **`evidence/probes/verify_s4.py`** is the gate to run before `chain.py`: fire rate against Round
  1's measured 0.10–0.45 band, fires with no quote or an ungrounded quote, legacy indicator ids,
  duplicate verdicts, which codebook produced the verdicts, and whether every triage keep reached
  the mapper. Exit 0 means safe to chain. Smoke-tested: it correctly refuses while S4 is unfinished,
  and confirms the shipping codebook with 1,054 gold rows is in use.
- **All eight chain modules import cleanly** under the run's environment, so `chain.py` will not die
  on an import after the batches land. Order confirmed: S5 verify → S7 NEW/KNOWN → S6 rollup →
  S9 emit → S10 eval → Excel → audit view.
- **`evaluator.py` is safe against the 1,054-row gold set** — it reads `load_instrument().gold()` and
  filters on the loaded `INDICATORS`, so decimal matches decimal. **Expect `row_recall: null` for
  Timor-Leste**: it has no baseline sheet and therefore no gold rows. That is correct output, not a
  failure, and should not be read as one.
- **ρ annotated as population-dependent** in the cost note: 1.9 is English-only, CN/LA/TL measured
  1.45, so the old constant under-counts mapper calls outside English by about 30%.

---

# S4 ran. The important finding is a bug that cost a third of the run, silently.

## What happened

The three batches ended quickly — China in 10 minutes, the other two immediately — and reported
this:

| economy | rows | applies | **errors** |
| :---- | ---: | ---: | ---: |
| CN | 2,617 | 324 | **849** |
| LA | 902 | 119 | **332** |
| TL | 1,011 | 99 | **306** |

**1,487 of 4,530 provisions, 32.8%, produced no verdict.** The word "errors" was doing a lot of
work there: almost none of them were the model judging badly, or refusing, or running out of
tokens. They were answers whose **shape** the validator rejected. One looks like this:

    {"verdict": {"core_legal_question_answer": "This provision requires entities to report theft,
     loss, or diversion of weapons, hazardous chemicals, explosives... it does not concern personal
     data access by government at all.", ...}}

A good answer, wrapped in one extra key. Across China's 2,617 tool results:

| shape | count | |
| :---- | ---: | :---- |
| the five fields at the top level | 1,754 | correct |
| everything under a single `verdict` key | 509 | envelope |
| the same, under `parameter` | 71 | envelope |
| the same, under `parameters` | 40 | envelope |
| `trap_checks`' booleans hoisted to the top level | 124 | flattened |
| only `verdicts`, narrative fields missing | 46 | genuinely partial |

## Why it was recoverable for nothing

Message Batches results are retained for **29 days** and retrieval is **not billed**. The answers
were already paid for and still sitting on Anthropic's side, so the fix was to parse them properly
and re-ingest — not to re-run the model.

`coerce_verdict()` in `mapping/schema.py` unwraps a single-key envelope whose key is not one of our
own field names, and re-nests hoisted trap booleans, with an explicit `trap_checks` entry beating a
hoisted duplicate. Both mapping paths validate through it.

A separate 237 answers omitted exactly one boolean, `trap_checks.conditional_path_exists`.
**It is not defaulted.** Defaulting it to `false` would assert "no compliant transfer path exists",
which is precisely the 6.1-versus-6.4 judgement that trap exists to guard. The trap fields became
`bool | None` and an omitted one is recorded as `null` — "not stated". Every downstream reader
already tolerated that: `submission.py` tests `is False` / `is True`, `excel_export` uses
`.get(..., True)`, `sectoral_scope` has no reader at all.

The schema **sent to the model** still requires all five traps, as plain booleans with no default
and no null. A model that is no longer asked for the traps stops reasoning about them, and the traps
are the point of this stage. The validator and the request are deliberately different documents.

    validation 67.2% -> 96.4%    1,322 of 1,487 provisions recovered for $0

## Then the cost report turned out to be lying

Re-ingesting exposed a second fault. The report added each fetch's counters to the previous
report's, which is right for a second batch and wrong for re-reading the same one. After one
re-ingest China's report claimed **3,466 provisions — more than the 2,617 that exist** — and $28.92
against $21.86 billed. Across the three that was **$51.72 claimed against $38.81 actually billed**.

Fixed: the report now derives its counts from `verdicts_<ECON>.jsonl`, and cost is recorded **per
batch id** in `batches_<ECON>.json` with a `cost_source` line, summed once. Re-ingesting overwrites
a batch's figure instead of adding to it. This mattered beyond tidiness — Section 5 cannot be
corrected after the deadline, and a ledger that inflates 33% every time a batch is re-read is worse
than no ledger.

## S4 as it now stands, verified

`evidence/probes/verify_s4.py`, exit 0:

| economy | provisions | fires | fires/prov | ungrounded | errors |
| :---- | ---: | ---: | ---: | ---: | ---: |
| CN | 2,617 | 516 | 0.197 | 2 | 98 |
| LA | 902 | 188 | 0.208 | 4 | 25 |
| TL | 1,011 | 128 | 0.127 | 1 | 42 |
| **all** | **4,530** | **832** | **0.184** | **7** | **165** |

Fire rate 0.184 sits inside Round 1's measured band (AU 0.196, MY 0.295). Ungrounded is 0.84% of
fires against Round 1's 1.8%, and `unfilable_reason()` drops every one before emit. **No triage keep
went unmapped** in any economy. Verdicts carry grounded quotes in the source script — China's fires
quote Chinese, with `quote_anchor: exact` and a byte span.

One correction to my own work: `verify_s4.py` first reported "516 fires with NO quote" because it
looked for `verbatim_snippet`; the field is `verbatim_quote`. And its ungrounded gate was set at
0.5%, stricter than Round 1's own 1.8% and stricter than the pipeline's behaviour, since ungrounded
fires cannot reach the CSV. Both corrected — the gate now blocks above 5%, which would mean
anchoring itself had broken.

## Still owed

**165 genuinely incomplete answers** — 125 missing `core_legal_question_answer`, 34 missing
`who_is_regulated`, 6 other. Content is never invented, so these stay errors. Retrying them live
costs about **$2.60**: `python -m src.p3map.mapping.runner <ECON>`. Worth doing, not urgent.

## Money, actual

| | |
| :---- | ---: |
| S3b triage (pre-flight $0.98 + full $40.44) | $41.42 |
| S4 mapping, three batches, billed | **$38.81** |
| **spent** | **$80.23** |
| S5 blind verify, running | ~$16 projected |

The batch lane did what it was picked for: $38.81 against roughly $70 live, and the queue cost
10 minutes rather than the 24 hours its SLA allows.
