# What the instrument change of 13 September means for mapping, checked 2026-09-22

The instrument notice (`C:\Users\woshi\Desktop\rdtii-finale-0-instrument\NOTICE_FOR_OTHER_STAGES.md`) asks
every stage to check its plan, decisions and code against sections 2 to 4, list what breaks with file and
line, and send requests rather than edit instrument files. This is that list for mapping.

**Checked against** the repo `C:\Users\woshi\Desktop\rdtii-rocky-finale` on branch `finale` at commit
`92a5e9d`, working tree clean; the instrument's `instrument\output\` as it stands on 2026-09-22; and this
workshop's `README.md`, `PLAN.md` and `DECISIONS.md`. Line numbers are from that commit. Paths starting
`P\` mean `stages\p3-map\`.

## Short version

**What changes.** Mapping is the gate for the instrument hand-off. The instrument cannot be copied into the
repo until this stage reads decimal IDs from `indicator_order.yaml` instead of its own lists. The stage
code has not changed since Round 1. The only finale commit under `P\` adds `config\indicator_ids.py`, and
no module imports it yet. About 60 lines in 11 files carry legacy IDs or legacy file globs, and two
more modules, the evaluator and the query builder, inherit them through `INDICATORS`.

**What is silent and dangerous.** Two failures would not crash. `triage\haiku.py:46` globs `P*.yaml`,
so after hand-off it finds no signatures and triages with no definitions. The trap descriptions in
`mapping\schema.py:19-26` are sent to the model and name `P6-I1`, `P6-I4` and `P7-I3`, so the model would
be taught one vocabulary and asked to answer in another.

**What blocks.** Nothing outside this stage blocks the migration itself. Three things block using it well:
the instrument's `coverage` marker is empty (request R1), the Round 1 6.2 cells wait on the instrument's
trap-wording decision, and English-only signature keywords leave non-English retrieval to the dense leg,
which the interface's run path does not execute (item A18).

**Requests.** Four, in section C.

## A. What breaks in the stage code

Severity: **silent** means a wrong result with no error; **loud** means a crash or refusal.

| # | Where | What breaks after hand-off | Change | Severity |
| :---- | :---- | :---- | :---- | :---- |
| A1 | `P\config\settings.py:74-77` | `INDICATORS` is the nine legacy IDs. `prompt.py:35` then looks up `blocks["P6-I1"]` in a file keyed `6.1` | A loader over `indicator_order.yaml` in host order, filtered to the automated set (decision M10, proposed) | loud, KeyError |
| A2 | `P\config\settings.py:78` | `ECONOMIES = ["SG","AU","MY"]`. Not in the notice, but it blocks China, Lao PDR and Timor-Leste, and any live-test economy | Derive economies from the input, and map codes to UN names in one table | loud or silent, per caller |
| A3 | `P\src\p3map\mapping\schema.py:19`, `:23`, `:26` | Trap descriptions name `P6-I1`, `P6-I4`, `P7-I3`. They are part of the tool schema the model reads | Decimal IDs in the text. `:36` closes the vocabulary through `INDICATORS`, so it follows A1 | **silent** |
| A4 | `P\src\p3map\mapping\prompt.py:27`, `:3` | The header says "Pillars 6-7" and the docstring says "all 9 indicator blocks". Both stay true under M7. Checked and safe: `review_notes` never renders, because `:36-38` is an allow-list; `score_polarity` and `definitions` still exist as top-level keys | Keep the header, but derive it from the automated set | none today |
| A5 | `P\src\p3map\triage\haiku.py:46`; `P\src\p3map\ab\ab_triage.py:47`; `P\src\p3map\ab\ab_deepseek.py:222`, `:253` | `glob("P*.yaml")` matches no decimal-named signature file, so `defs` is empty and triage runs with no definitions | Load `signatures\{id}.yaml` for each automated ID. Pin the two `ab_*` scripts to a Round 1 instrument copy instead (A15) | **silent** |
| A6 | `P\src\p3map\prefilter\queries.py:18` | Loads `signatures\{ind}.yaml`, which works once A1 lands. The 400 exemplars now include the economies we will run: China, Lao PDR and the Round 1 three | Leave-one-economy-out through `exemplar_for`, **at run time as well as at evaluation**. An economy's own host rows in its retrieval query are the Round 1 soft leakage channel, and on a sealed live test they would be a hard one | **silent** |
| A7 | `P\src\p3map\select.py:29-30`, `:35-36`, `:82`, `:146`, `:152` | Per-cell budget dict and `OBLIGATION_ALIGN` keyed by legacy ID. `:82` tests `ind.startswith("P7")` | Key by decimal ID; use `indicator_ids.pillar_of()` | silent, budgets fall to default |
| A8 | `P\src\p3map\rollup.py:26`, `:27`, `:35-36`, `:81`, docstring `:3-11` | `ESCALATION_INDICATORS`, `BINARY_INDICATORS` and `WHAT` are legacy-keyed | Read `level` from the codebook blocks and the polarity lists from `policies.yaml` `scoring_policy`, per the notice | silent, no escalation |
| A9 | `P\src\p3map\output\submission.py:84-94`, `:254`, `:304`, `:355-368`, docstring `:9-10`; `COLUMNS` `:35-38` | Not-present reasons, the economy-level rule for 7.1 and 7.2, the 7.3 and 7.5 caps, and the 6.1-to-6.4 cross-reference are all legacy-keyed. `COLUMNS` has 13 columns, and the finale has 14 | Decimal keys from the YAML; add `Language of Source`; write IDs as text | silent, wrong rows |
| A10 | `P\src\p3map\output\excel_export.py:23-39` | Indicator-description dict keyed by legacy ID | Names from `indicator_order.yaml` | silent, blank labels |
| A11 | `P\src\p3map\discovery\baseline.py:70`, `:94`, docstring `:13` | Builds `f"P{p}-I{ind_n}"` from the workbook, converting decimal back to legacy. It reads only the three Round 1 sheets | Keep decimal; also read the Round 2 sheets for China and Lao PDR. Timor-Leste has no sheet, so every row there is NEW with the reason in Notes | silent, all NEW |
| A12 | `P\src\p3map\discovery\malaysia.py:184`, `:194` | Hard-coded `"P7-I3"` in the Round 1 Malaysia error-check | Decimal, or retire the check for the finale | silent |
| A13 | `P\src\p3map\eval\evaluator.py:65` | Filters the gold set through `INDICATORS`. The gold set grows from 51 rows to 1,054 and carries `label_flag` | Restrict to the automated set; decide per `label_flag.status`; exclude an economy's own exemplar rows | silent, inflated or empty recall |
| A14 | Round 1 artifacts in `C:\Users\woshi\Desktop\RDTII\pipeline-data\rdtii-p3-map` | Index keys `P6-I1_idx` in `bm25_top.npz` and `dense_top.npz`, and IDs in `out\**\*.jsonl` | **Never rewrite the reference arm in place.** It is the frozen evidence the experiments read. Normalise at read time through `indicator_ids.normalize()`, or write migrated copies to a new directory | loud or silent, by reader |
| A15 | `P\src\p3map\ab\ab_deepseek.py:77`, `:441`, `:593`, `:595`, `:733`, `:744` | Filed evidence of a rejected provider. It must keep reproducing its report | Run it against a Round 1 instrument copy through `INSTRUMENT_DIR`; do not migrate it | loud |
| A16 | `P\tests\test_holdout_smoke.py:23` | Asserts 9 rows. That still holds if the automated set is nine | Assert against the automated set's length | loud |
| A17 | `P\tests\test_indicator_ids.py` | Compares the two copies of `indicator_ids.py` byte for byte. The hand-off copies both | No change. Run after hand-off | loud |
| A18 | `main.py:575-577` (repo root) | Not an instrument break, but the notice's point about English-only keywords lands here. The interface's run path runs the BM25 leg only and writes an **empty dense stub**, so a Chinese, Lao or Portuguese corpus gets English keyword retrieval and nothing else | Run the dense leg on the automated indicators for non-English economies, or pre-select candidate laws. Owner to agree: `main.py` is not inside `P\` | **silent**, empty results |

The following live outside this stage and were found on the same sweep. They are recorded so they are not
lost, and they belong to the named workshop.

| Where | Owner |
| :---- | :---- |
| `interface\dashboard.py:1606` regex `P[67]-I\d`; `:949` `pillar_view in (6,7)`; `:5675` | Dashboard |
| `main.py:235`, `:245`, `:257` prefix `P{pillar}-`; `:961` `--pillar choices=[6,7]` | Whoever owns `main.py` |
| `stages\p2-extract\src\rdtii_p2\cli.py:408` maps `pillar_hint` to pillars 6 and 7 only | Extraction |

## B. This workshop's own documents against the notice

| Where | What is now wrong | Change |
| :---- | :---- | :---- |
| `README.md:53` | "gold set, 51 rows" | 51 until hand-off, 1,054 after. Say both |
| `README.md` "Current state" | Economies SG, AU, MY | Six economies now: the Round 1 three plus China, Lao PDR and Timor-Leste, from the scraping workshop's outputs |
| `PLAN.md` | No step for the decimal-ID migration, which the notice makes this stage's hand-off job | Added as step 3A in `PRELIMINARY_PLAN_2026-09-22.md` |
| `PLAN.md` step 2F | "The rules come from the instrument folder." Now confirmed: `policies.yaml` carries `repealed`, `amending_act_cited_instead_of_principal` and `government_data_measure`, and `indicator_order.yaml` carries `host_mapping_traps` | Read those keys; do not restate them in code |
| `DECISIONS.md` M7 | The notice asks this stage to choose between one prefix and one per pillar | Under M7 the answer is one prefix of the automated blocks, about the Round 1 size. Instrument D3 is moot while M7 stands. Proposed as M10 |
| `DECISIONS.md` M8, M9 | "Read the marker from the instrument." The `coverage` field exists on all 62 entries of `indicator_order.yaml` and is `null` on every one | Request R1 |

## C. Requests to the instrument

For the developer to take to the instrument workstream. Nothing here edits an instrument file.

| # | What | Why | Which code reads it |
| :---- | :---- | :---- | :---- |
| R1 | **Populate `coverage` in `indicator_order.yaml`**, decision D14: automated; manual, outside the automated scope; manual, practice or external evidence; manual, tier not published by this economy's portal. Add per-economy overrides, starting with China, where pillar 6 is framework-only per the coverage register. Declare it in `INTERFACE_CONTRACT.md` section 4 | M8 and M9 read the mark rather than keep a second list. The same field defines the automated set that A1 filters to, so one field drives both | The loader replacing `settings.py:74`; the notification rows in `output\submission.py` |
| R2 | **Say whether stage S7 may read `gold\gold_set.jsonl` as the NEW/KNOWN baseline.** Notice section 3 says the gold set holds the Round 2 sheets and defines KNOWN from them; section 2 says the gold set is "evaluation only; never use it to decide anything" | The two readings conflict. Tagging is not a verdict, and the Round 1 leakage audit allowed S7 to read the baseline, but the rule should be written down once | `discovery\baseline.py`, `discovery\newknown.py` |
| R3 | **Optional: source-language keywords per signature**, at least Chinese, Lao and Portuguese | `keywords` is English only, so the BM25 leg cannot find a Chinese, Lao or Portuguese provision. Without it the dense leg carries non-English retrieval alone | `prefilter\queries.py`, `prefilter\bm25.py` |
| R4 | **Hand-off timing.** Mapping will signal when A1 to A16 pass on a branch against the workshop copy of `instrument\output\`, so the hand-off is a copy plus a test run, not a debugging session | The notice makes mapping the gate | `HANDOFF.md` step 4 |
| R5 | **Added 4 October 2026. The count rule as data on each block that scores by how many measures an economy has:** 1.4, 2.1, 2.3, 3.1, 4.3, 4.9, 5.2, 5.3, 9.4, 10.1, 10.2 and 10.3 (6.1 and 6.2 have theirs in the roll-up already). What is counted (measures, products, sectors), which per-measure values count, and the thresholds that give each score. The developer's decision: the instrument states the rule, the stage does not hand-code it | Each rule is a sentence inside `scoring_tree[].if` today, different per block. The roll-up takes the highest verified score and escalates only 6.1 and 6.2, so a cell with several half-point measures comes out too low. Seven of these indicators are also in the instrument's list of host contradictions (criteria that count, host rows scored one by one) | `src\p3map\rollup.py`, `measure_score()` |
| R6 | **Added 4 October 2026. What an absence scores, as a field on each block,** for instance `absence_score`: a value, or null for "left unscored". The developer's decision: a field, not a rule in the stage | Needed first for 11.2, where a score of 0 needs positive evidence that self-declaration is allowed, and for the 14 inverted indicators, where an absence scores 1 only when it is established. Today a no-provision row carries score 0 for every indicator and an empty provision-level cell rolls up to 0. `null_statement` gives the words of an absence row, not its score | `src\p3map\output\submission.py` (the no-provision row) and `src\p3map\rollup.py`, `measure_score()` |

One request goes to scraping, not the instrument. `LA_corpus_2026-09-21` files the 53 English
translations as superseded, because `merge_corpus.identity()` ignores language. The host's Lao baseline
names laws in English, and our corpus names them in Lao, so NEW/KNOWN matching by instrument name needs the
translation link, `translation_doc_id`, which is set on 0 rows today.
