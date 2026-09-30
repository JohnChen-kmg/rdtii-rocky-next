# Plan: the instrument, pillars 6 and 7 required, further pillars optional

This is workstream 3 of the finale build plan. The repo logs its code changes under W3. The stage's
own `PLAN.md` inside `stages\p0-instrument` is the Round 1 engineering plan and is marked complete.
This file is the finale plan and supersedes it for anything dated after 2026-09-12.

> **Where the work happens, since 2026-09-13 (decisions D9 and D12).**
> - Every `stages\p0-instrument` file named below is edited in this folder and logged in
>   `CHANGELOG.md`. A `scripts\...` file is in `code\scripts\`; everything else is in `instrument\`.
>   `code\README.md` explains the code workflow.
> - Those files reach the repo at hand-off, following `HANDOFF.md`.
> - Files under `stages\p3-map` are repo work and are not mirrored here.
> - Status: the instrument side of steps 0, 3A, 3B, 3E, 3F (drafts), 3G and 3H was built overnight.
>   See `REPORT_2026-09-13_overnight.md` and the "State" table in `README.md`.

## Scope decision, 2026-09-12

**Required: pillars 6 and 7 only. Further pillars are optional.** See `DECISIONS.md` D8 and the scope
decision at the top of `C:\Users\woshi\Desktop\RDTII Finale Plan\3_Final_Stage\GAPS_AND_PLAN.md`.
The nine scoreable indicators already exist at full depth, so the required work is small.

| Step | What | Hours | Status |
| :---- | :---- | ----: | :---- |
| 3A | Decimal ID migration across the instrument and the run artefacts. The output workbook demands `6.1`, so this stays required | 6 | **Required** |
| 3H | Encode the host's seven zero-scoring rules in the host's wording for the nine indicators. See the trap section in `README.md` | 2 | **Required** |
| 3G | Extend the gold set to the Round 2 country sheets of the three new economies, so NEW and KNOWN can be tagged there | 2 | **Required** |
| 3B | Generated Tier C entries for the other ten pillars. The cheapest live-test insurance | 8 | Optional, do first if any time frees up |
| 3C | De-hardcoding special cases into YAML | 8 | Optional, only needed with 3B |
| 3D | Per-pillar prompt prefix | 8 | Optional, only needed with 3B |
| 3E | Retrieval refresh and re-export check | 4 | Optional, only needed with 3B |
| 3F | Tier B hand-authoring | 20 | Optional |

**Required total: about 10 hours**, down from about 35. Optional total: about 48 hours.

Step 0, `output\indicator_order.yaml`, was a prerequisite for 3B. It is now needed only if 3B runs.
3A does not depend on it, because the nine IDs are already known.

The sections below were written when all twelve pillars were required. They stay as the plan for the
optional steps. Read 3A in full. Read 3B to 3F only if optional time is available.

The previous step table, kept for reference:

| Step | What | Hours | Was |
| :---- | :---- | ----: | :---- |
| 3A | Decimal ID migration across the instrument and the run artefacts | 6 | Yes |
| 3B | Generated Tier C indicators plus a loader | 8 | Yes |
| 3C | De-hardcoding per-indicator special cases into YAML | 8 | Yes |
| 3D | Per-pillar prompt prefix | 8 | Yes |
| 3E | Retrieval refresh and re-export check | 4 | Yes |
| 3F | Tier B hand-authoring | 20 | First six only |

### Changed by the host templates, read 2026-09-12. Superseded in part by the scope decision

The notes below assumed twelve pillars. Under the scope decision, the trap wording moves into
required step 3H and the gold set extension into required step 3G. The 3B notes apply only if 3B is
attempted.

- **3B rises in priority above all Tier B work.** The live test is one pillar and two indicators,
  and may be a pillar never worked. An indicator with no codebook entry scores zero on the day.
- **3B gains a first check, 30 minutes.** The workbook says the Indicator Reference sheet comes from
  the methodology sheet in the **Round 1** database. This plan reads the Round 2 copy. Diff the two
  methodology sheets cell for cell before generating Tier C, and read whichever the host names if
  they differ.
- **3C must encode the host's seven zero-scoring rules in the host's own wording.** They sit at the
  foot of the Indicator Reference sheet, rows 79 to 85, and on the Instructions sheet. Three of them
  are stricter than Round 1 encoded: per-provision 7.1 and 7.2 rows score zero; a "prescribed period"
  with no number is not 7.3; drafts, repealed provisions and amending acts cited in place of the
  principal act score zero. No extra hours, because 3C already moves traps into YAML.
- **The gold set must reach the seven Round 2 country sheets**, not only the three Round 1 sheets,
  so NEW and KNOWN can be tagged for live-test economies. This was already in 3B's scope. It is now
  a freeze requirement rather than an evaluation nicety.

---

## 3A. ID migration, about 6 hours

Decimal text becomes the only internal vocabulary. `indicator_ids.py` is already written and its 28
tests pass, so this step is rename work plus one new script, not design work.

### Files to edit in `stages\p0-instrument`

| File | What changes |
| :---- | :---- |
| `output\indicators.yaml` | The 9 `- id:` values, `scope.in_scope_indicators`, the `scope.out_of_scope` key `P6-I5`, and the disambiguation prose that names sibling indicators by legacy ID |
| `output\policies.yaml` | Any legacy ID inside `edge_cases`, `scoring_policy` and `measure_inclusion` |
| `scripts\build_signatures.py` | The `SPEC` keys at line 30, the `CURATED` keys at line 324, and the filename written under `OUT_DIR` at line 25 |
| `scripts\build_gold.py` | The indicator written into each gold row |
| `scripts\rdtii_examples.py` | `indicator_code()` at line 67 turns 6.1 into P6-I1. Delete it and call `indicator_ids.normalize()` instead |
| `scripts\validate_instrument.py` | `EXPECTED` at line 32 and `SCORESETS` at line 34 |
| `output\signatures\*.yaml` | Rename all 9 files to `6.1.yaml` form, and change the `indicator:` field inside each |

### Files to edit in `stages\p3-map`

| File | What changes |
| :---- | :---- |
| `config\settings.py` line 74 | The `INDICATORS` nine-item literal. Step 3B replaces it with a loader, so a straight rename here is temporary |
| `src\p3map\discovery\baseline.py` line 70 | Builds a legacy ID with `f"P{p}-I{ind_n}"` while reading the Round 1 baseline sheet. Normalise to decimal on read |
| `contracts\instrument\` | Re-vendor the whole folder after `output\` is green. It must stay byte-identical |
| `tests\test_indicator_ids.py` | Point `HOST_ORDER` at `indicator_order.yaml` |

Three places in the tree build a legacy ID. `rdtii_examples.indicator_code()` and
`baseline.py` line 70 both go, because both are on a live path. `indicator_ids.legacy_of()` stays.
It is the sanctioned translation table for reading Round 1 artefacts, and decision D1 keeps it.

### The new script: `scripts\migrate_ids.py`

Its job is to rewrite the Round 1 run artefacts in place so the expensive legs are not re-run. Both
targets are verified to exist and to carry legacy IDs today.

| Target | Location | Size | Shape |
| :---- | :---- | ----: | :---- |
| Run artefacts | `C:\Users\woshi\Desktop\RDTII\pipeline-data\rdtii-p3-map\out\**\*.jsonl` | 25 files, 96.5 MB | Every one of the 25 contains legacy IDs |
| Retrieval index | `C:\Users\woshi\Desktop\RDTII\pipeline-data\rdtii-p3-map\data\index\bm25_top.npz` and `dense_top.npz` | 2 files | 18 keys each, named `P6-I1_idx` and `P6-I1_score`. Re-key to `6.1_idx` and `6.1_score` |

The folder holds seven files. The other five need no migration.

| File | Size | Why it needs no migration |
| :---- | ----: | :---- |
| `embeddings.f16.npy` | 845 MB | Keyed by provision row, not by indicator |
| `prefilter_corpus.jsonl` | 526 MB | No indicator field, confirmed by reading its first record |
| `corpus_ids.json` | 12.2 MB | No indicator ID, confirmed by grep |
| `doc_meta.json` | 850 KB | No indicator ID, confirmed by grep |
| `embed_meta.json` | 71 B | No indicator ID, confirmed by grep |

Write the script to be idempotent and to write a `.bak` beside each file before touching it. The
dense leg and the triage pass are the two most expensive things Round 1 bought. Losing them to a bad
rename would cost days.

### Done test

`python scripts\validate_instrument.py` exits 0. `python -m pytest tests\test_indicator_ids.py -q`
passes from `stages\p3-map`. `grep -r "P6-I\|P7-I"` over `stages\p0-instrument`,
`stages\p3-map\contracts` and `stages\p3-map\src\p3map\discovery` returns only deliberate
legacy-translation lines. Re-vendoring is not checked by any test, so diff `output\` against
`contracts\instrument\` by hand before calling this step done.

---

## 3B. Generated Tier C plus loader, about 8 hours

### The generator: `scripts\build_indicators_from_methodology.py`

It reads two host sources and emits `output\indicators_generated.yaml`. *(Since D11, 2026-09-13: it adds
Tier C blocks to `output\indicators.yaml` instead, for IDs that have none.)*

| Source | Path | What it supplies |
| :---- | :---- | :---- |
| Methodology sheet | `C:\Users\woshi\Desktop\RDTII Finale Plan\1_Rules\Baselines\ESCAP-RDTII-2.1_ Round 2 Database.xlsx`, sheet `RDTII 2.1 Methodology` | 61 indicator rows. Columns: Pillar_ID, Indicator_ID, Category, Criteria for scoring, Possible scores |
| Indicator Reference | `C:\Users\woshi\Desktop\RDTII Finale Plan\1_Rules\Final_Round\OUTPUT_TEMPLATE_FINAL_ROUND.xlsx`, sheet `Indicator Reference` | 62 IDs, the host's order, plus weight for 10 of them and exceptions text for 13 of them |

Three facts measured from those sheets. They decide how much the generator can do on its own.

**Score sets parse cleanly.** Six distinct sets cover all 61 indicators.

| Score set | Indicators |
| :---- | ----: |
| `1 / 0.5 / 0` | 31 |
| `1 / 0` | 23 |
| `1 / 0.8 / 0.5 / 0` | 2 |
| `1 / 0.5 / 0.25 / 0` | 2 |
| `1 / 0.50 / 0` | 2 |
| `1 / 0.75 / 0.50 / 0.25 / 0` | 1 |
| **Total** | **61** |

Normalise the text before comparing. Three rows write the middle value as `0.50`, namely 1.4, 8.1 and
8.2. Thirty-five rows write it as `0.5`.

**Criteria and score lines align** for 60 of 61. Indicator 1.4 is the only exception, with 6
criteria lines against 5 scores. Hand-fix 1.4. Let the generator refuse anything else that fails the
count check, rather than guessing.

**Exceptions text is thin.** Only 13 of the 62 Indicator Reference rows carry an exceptions note. The
other 49 have to say so rather than pretend. Leave the field absent and let the Notes column disclose
Tier C depth.

### The merge rule

> **Superseded 2026-09-13 by D11.** There is one codebook file. All 61 blocks sit in
> `indicators.yaml`, in host order. The generator only adds a Tier C block where none exists. The
> validator fails on a missing, repeated or out-of-order ID. The paragraph below is the original
> two-file plan.

Any ID present in the hand-authored `output\indicators.yaml` is skipped by the generator. The
validator fails if an ID appears in both files, and fails if an in-scope ID appears in neither.
That is the single check that keeps 61 indicators honest.

### The loader

Replace the `INDICATORS` literal at `stages\p3-map\config\settings.py` line 74 with a function that
reads the merged, ordered list. Order comes from `indicator_order.yaml`, never from sorting the IDs.
`indicator_ids.sort_key()` already enforces that and raises on an ID not in the order list.

### Done test

The loader returns 61 IDs in host order. The validator reports every ID as hand-authored or
generated, never both, never neither.

---

## 3C. De-hardcoding, about 8 hours

Per-indicator special cases currently live in mapping code. With 61 indicators they have to live in
the instrument. These are the real sites, all verified by grep.

| File and line | What is hard-coded | Proposed YAML field |
| :---- | :---- | :---- |
| `src\p3map\output\submission.py` lines 84 to 94 | Nine null statements, one per indicator, in a dict | `null_statement` on the indicator block |
| `src\p3map\output\submission.py` line 254 | `if ind in ("P7-I1", "P7-I2")` selects economy-level handling | `level: economy` or `level: provision` |
| `src\p3map\output\submission.py` lines 31, 32, 304 | `NEW_CAP = 8`, `NEW_CAP_TAIL = 10`, applied to P7-I3 and P7-I5 | `row_cap` on the indicator block |
| `src\p3map\output\submission.py` lines 364 to 368 | The 6.1 to 6.4 cross-reference sentence | `cross_reference` naming the sibling ID and the sentence |
| `src\p3map\output\excel_export.py` lines 23 to 40 | Nine method notes and nine trap notes | `method_note` and `trap_note` |
| `src\p3map\select.py` lines 28 to 31 | `CAPS`, nine retrieval caps from 150 to 600 | `retrieval_cap` |
| `src\p3map\select.py` lines 35 to 36 | `OBLIGATION_ALIGN`, four obligation types tied to 6.1 to 6.4 | `obligation_type` on the indicator block |
| `src\p3map\select.py` line 152 | Polarity exclusion for P7-I1 and P7-I2 | `polarity: inverted` |
| `src\p3map\rollup.py` lines 26, 27, 35, 36 | `ESCALATION_INDICATORS`, `BINARY_INDICATORS`, `WHAT` | `escalation: true`, the existing `scoring.type`, and `framework_name` |
| `src\p3map\mapping\schema.py` lines 17 to 26 | Three trap sentences naming legacy IDs | Already instrument content. Render from the YAML instead |

Tier C indicators get sensible defaults rather than blank fields. Proposed defaults: `level:
provision`, `polarity: normal`, `row_cap: 8`, `retrieval_cap: 300`. Reason. Every trap the host
names is a pillar 6 or pillar 7 trap. Those nine are hand-authored. A default that is wrong for a
Tier C indicator costs a row cap, not a wrong score.

### Done test

`grep -r "P6-I\|P7-I\|\"6\.1\"" src\p3map` returns no per-indicator branch. The three A/B scripts
under `src\p3map\ab\` are excluded from this step. They are Round 1 evidence and are on the cut list.

---

## 3D. Per-pillar prompt, about 8 hours

`build_system_prefix()` at `src\p3map\mapping\prompt.py` line 18 renders every indicator block into
one cached prefix. That worked for 9. It does not work for 61.

Change the signature to `build_system_prefix(pillar)`, keep the `lru_cache`, and key the cache on the
pillar. Then group candidates by pillar in the mapper and make one call per group.

Five call sites read the function today. All five need updating.

| Call site | Line |
| :---- | ----: |
| `src\p3map\mapping\runner.py` | 82 |
| `src\p3map\mapping\batch_runner.py` | 95 |
| `src\p3map\verify\blind.py` | 47 |
| `src\p3map\ab\ab_mapper.py` and `src\p3map\ab\ab_deepseek.py` | 50 and 474 |

The A/B scripts can take a default pillar argument rather than a rewrite. They are not on the freeze
path.

Byte stability matters here. The current prefix is cacheable because the render has fixed order and
no timestamps. Per-pillar rendering must keep both properties, or prompt caching stops paying and the
cost per run rises. Measure the character length of each pillar prefix and record it in
`evidence\`. The target is at or below the size of today's nine-indicator prefix.

### Done test

Each pillar prefix renders identically twice in a row. One mapping run over a small provision set
produces the same verdicts as the single-prefix build, for the pillar 6 and 7 indicators.

---

## 3E. Retrieval refresh and re-export check, about 4 hours

Two questions, both about what 52 new indicators do to a retrieval path built for 9.

**Signatures.** `output\signatures\` holds 9 files, each with keywords, definition text, negative
signals and 6 or more labelled exemplars. Tier C indicators have no exemplars, because exemplars
come from Round 1 country sheets that only cover pillars 6 and 7. Proposed answer. Generate a
reduced signature for Tier C from the methodology Category and Criteria text. Mark it
`depth: tier_c`. Have the validator require exemplars for Tier A and Tier B only. Reason. A
signature without exemplars is still a usable BM25 query and is honest about what it is.

**Dense leg.** `bm25_top.npz` and `dense_top.npz` hold one column pair per indicator. Adding 52
indicators to the dense leg means re-scoring the whole embedded corpus against 52 new queries with
`BAAI/bge-m3`. That is the single most expensive thing on this list and it is on the cut list.
Proposed answer. Tier C retrieval is keyword-only for the freeze build, disclosed in the README and
in the export Notes. Pillars 6 and 7 keep both legs.

**One reconciliation to do here.**
`C:\Users\woshi\Desktop\RDTII\pipeline-data\rdtii-p3-map\data\index\embed_meta.json` records a row
count for the dense index that does not match the authoritative provision count in
`C:\Users\woshi\Desktop\RDTII Finale Plan\3_Final_Stage\AUTHORITATIVE_NUMBERS.md`.

| Source | Rows |
| :---- | ----: |
| `embed_meta.json`, keys `n` and `done_rows` | 412,565 |
| `AUTHORITATIVE_NUMBERS.md`, v2.4 plus segmentation fix | 411,986 |
| Difference | 579 |

The difference most likely depends on whether the index was built before or after the segmentation
fix. Reconcile it before either figure is quoted anywhere. Do not quote either until then.

**Re-export check.** Run one export end to end. Confirm the Coverage Matrix populates from decimal
IDs, including the three-level `12.4.x` family. The pillar formula in Output Data column O is
`=IF($E9="","",IFERROR(INT($E9),IFERROR(VALUE(LEFT($E9,FIND(".",$E9)-1)),"?")))`. A two-level ID such
as 6.1 resolves on the `INT` branch. A three-level ID such as 12.4.1 fails `INT` and resolves on the
`LEFT` branch. A legacy `P6-I1` fails both and writes `?`.

---

## 3F. Tier B hand-authoring, about 20 hours

Twelve to fourteen indicators get a scoring tree, trap rules and disambiguation, at roughly the depth
of the nine. Priority order, highest first. The first six are the freeze target.

| Order | ID | Policy issue | Why it is high |
| ----: | :---- | :---- | :---- |
| 1 | 8.3 | User identity requirements | Confusable with 7.4 and with 12.9 |
| 2 | 8.4 | Monitoring obligations | Confusable with 7.5 government access |
| 3 | 9.1 | Content blocking | Distinct from 9.4 licensing |
| 4 | 9.4 | Content licensing | The instrument notes already flag data-centre licensing as 9.4, not 6.3 |
| 5 | 12.3 | E-commerce licensing | Confusable with 5.5 telecom licensing |
| 6 | 12.8 | Local presence requirements | The nearest neighbour of 6.3 infrastructure |
| 7 | 5.5 | Telecom licensing | Pairs with 12.3 |
| 8 | 12.9 | Consumer protection | Broad wording, high false-positive risk |
| 9 | 2.1 and 2.3 | Public procurement | Two indicators, one law family |
| 10 | 4.9 | Source-code disclosure | Overlaps 2.2 |
| 11 | 3.5 | Commercial presence | Overlaps 12.8 |
| 12 | 8.1 and 8.2 | Safe harbour | Score set is `1 / 0.50 / 0`, so the text normaliser must already be right |

Note the pattern. Every entry above is on the list because it is confusable with something else. Tier
B exists to buy disambiguation, not prose.

---

## Minimum for the 30 September freeze

**Revised 2026-09-12 by the scope decision.** Steps 3A, 3G and 3H, complete. That means:

| Must be true on 30 September | Check |
| :---- | :---- |
| The 9 pillar 6 and 7 indicators at full depth, 6.5 declared excluded | Validator's per-indicator field checks pass |
| Decimal IDs everywhere, no legacy ID in a live path | Grep over the instrument and the vendored copy |
| The host's seven zero-scoring rules encoded in its wording | Each rule findable in `indicators.yaml` or `policies.yaml` |
| NEW and KNOWN can be tagged for the three new economies | Gold set holds their Round 2 rows |
| Validator green | `python scripts\validate_instrument.py` exits 0 |
| Vendored copy identical | `diff -r output ..\p3-map\contracts\instrument` is empty |

The minimum below was written for twelve pillars. It now describes the optional extension only.

Previous minimum, 3A through 3E:

| Must be true on 30 September | Check |
| :---- | :---- |
| 61 scoreable indicators defined, 6.5 declared excluded | Loader returns 61 in host order |
| The 9 pillar 6 and 7 indicators still at full depth | Validator's per-indicator field checks pass |
| Decimal IDs everywhere, no legacy ID in a live path | Grep over the instrument and the vendored copy |
| Per-pillar prompt in use | Prefix length recorded per pillar |
| Validator green | `python scripts\validate_instrument.py` exits 0 |
| Tier disclosed in the export | Notes column names the tier on every Tier C row |

## What gets cut first, in this order

1. **Tier B beyond the first six.** Entries 7 to 12 in the 3F table. They are disambiguation polish
   on indicators that will still score at Tier C depth.
2. **Dense re-scoring for Tier C.** Keyword-only retrieval for the new 52, disclosed. Pillars 6 and 7
   keep both legs.
3. **Re-running the Round 1 A/B scripts.** `src\p3map\ab\ab_mapper.py` and `ab_deepseek.py` are
   Round 1 evidence. Give them a default pillar argument so they still import, and leave them.
4. **Exceptions text for the 49 indicators that lack it.** Leave the field absent rather than write
   an exception the host did not state.

## What is not done and is not planned

Say this plainly rather than let a reviewer find it. Tier C indicators carry no labelled exemplars,
because Round 1 produced exemplars only for pillars 6 and 7. The gold set therefore covers 9
indicators, not 61. There is no evaluation yardstick for the other 52 before the freeze. The
mitigation is decision 4 in `DECISIONS.md`: Tier C rows need higher confidence before they are tagged
NEW.
