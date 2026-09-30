# Stage result — mapping (p3-map), 2026-09-29

Written from the files. Every count below can be checked against a CSV, a report or a log named
beside it. Workshop: `Desktop/rdtii-finale-3-mapping/`. Code: `rdtii-rocky-finale/stages/p3-map/`,
branch `w2-mapping-finale`, 286 tests. Run: `Desktop/rdtii-finale-p3-runs/run_2026-09-27/`, 2.8 GB.

---

## 1. What exists

**318 rows across six economies**, of which 263 carry a scored provision and 55 record that no
qualifying measure was found.

| Economy | Rows | Scored | Language | Where |
| :---- | ----: | ----: | :---- | :---- |
| **China** | 55 | 55 | Chinese | `out/submission/records_CN.csv` |
| **Malaysia** | 53 | 51 | English | `out/submission/records_MY.csv` |
| **Australia** | 39 | 37 | English | `out/submission/records_AU.csv` |
| **Singapore** | 36 | 34 | English | `out/submission/records_SG.csv` |
| **Lao PDR** | 25 | 21 | Lao | `out/submission/records_LA.csv` |
| **Timor-Leste**, pillars 6–7 | 27 | 21 | Portuguese | `out/submission/records_TL.csv` |
| **Timor-Leste**, the other ten pillars | 83 | 44 | Portuguese | `out_tl52/submission/records_TL.csv` |
| **Total** | **318** | **263** | | |

Timor-Leste is the only economy mapped against **all 61 in-scope indicators**; the other five cover
the nine automated cells in pillars 6 and 7. Every one of the twelve pillars appears somewhere in the
output, which is a side-effect of that widening.

Economy scores, per `out/rollup/economy_scores_<E>.json`:

| | 6.1 | 6.2 | 6.3 | 6.4 | 7.1 | 7.2 | 7.3 | 7.4 | 7.5 |
| :-- | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: |
| CN | 1.0 | 1.0 | 1.0 | 1.0 | 0.0 | 0.0 | 1.0 | 1.0 | 1.0 |
| AU | 0.5 | 1.0 | 0.0 | 1.0 | 0.0 | 0.0 | 1.0 | 0.0 | 1.0 |
| MY | 0.0 | 1.0 | 0.0 | 1.0 | 0.0 | 0.0 | 1.0 | 1.0 | 1.0 |
| SG | 0.0 | 1.0 | 0.0 | 1.0 | 0.0 | 0.0 | 1.0 | 1.0 | 1.0 |
| LA | 0.0 | 1.0 | 1.0 | 1.0 | 0.0 | 0.0 | 1.0 | 0.0 | 1.0 |
| TL | 0.0 | 1.0 | 0.0 | 0.0 | 0.5 | 0.5 | 1.0 | 0.0 | 1.0 |

7.1 and 7.2 are **inverted**: 0 means the economy *has* a framework.

**Cost, from the per-stage reports: $263.44.** Triage $99.90, mapping (Anthropic Batches, 50% of
live) $123.42, blind verification $39.96, economy-level rollup calls $0.16.

---

## 2. How good it is

### Against the host's four evidence items, all verified 29 September

| Item | Result |
| :---- | :---- |
| 14 — IDs as text, snippets, live URLs | every indicator ID matches `\d+(\.\d+)+`; **all 263 scored rows** carry an Article/Section, a verbatim snippet and a Source URL |
| 15 — three or more economies | **six** |
| 16 — both mandatory pillars | pillar 6 = 72 rows, pillar 7 = 163 |
| 17 — a non-English source | **three** languages: Chinese, Lao, Portuguese |

### Against the 2025 baseline — read the direction, not the rate

Only rows the baseline *scores* can be missed: 32 of them, 27 China and 5 Lao. Timor-Leste has no
baseline at all.

| | reproduced | law never crawled | our pipeline |
| :---- | ---: | ---: | ---: |
| CN (27) | 12 (44%) | 9 (33%) | 6 (22%) |
| LA (5) | 1 | 1 | 3 |
| **combined (32)** | **13 (41%)** | **10 (31%)** | **9 (28%)** |

**"41% reproduction" is not an accuracy figure and must not be reported as one.** A third of the
baseline's rows cite documents that were never crawled, so the achievable ceiling is 69%, and against
that ceiling we reproduce 13 of 22 = **59%**. More importantly the baseline is demonstrably fallible:
**0 of its 201 China and Lao rows carry an article number**, two of the seven instruments it cites
that we lack are **GB/T and JR/T technical standards rather than legislation**, and its Lao 7.4 = 1
rests on a provision two independent reviewers judged to be a security officer rather than a Data
Protection Officer.

Where we disagree we are usually finding *more*: China's 6.4 adds the whole 2022–24 cross-border
transfer apparatus (security assessment, standard contract, certification) to the two instruments the
baseline names; its 7.5 adds the National Intelligence Law and the Criminal Procedure Law; Lao's 7.3
adds ten sectoral minimum-retention duties where the baseline records one law that was never crawled.

Score agreement with the baseline: **CN 8/9, SG 8/9, AU 7/9, MY 7/9, LA 4/9**. 6.2 disagrees in AU,
MY and SG in the same direction, ours 1.0 against 0.5 — the codebook's own escalation clause, and
worth one human read because a systematic disagreement is either a real reading or a systematic error.

### Quality signals from the run itself

- **Blind verification overturned 25.6% of fires** overall (625 of 2,437), inside the 30–40% band
  Round 1 measured. Crisp textual cells behave well (7.3 overturned 3–10%); judgement-heavy cells do
  not (7.5 overturned 48–57%).
- **Ungrounded fires: 0.84%** of all fires, against Round 1's 1.8%, and `unfilable_reason()` drops
  every one before emit — none can reach the CSV.
- **Fire rate 0.184 per mapped provision**, inside Round 1's 0.196–0.295 band.
- Quotes are the source's own bytes in the source's own script, with an anchor kind and a byte span
  recorded per fire.

### What is weak, stated plainly

- **117 replies produced no verdict** (of 4,530 + 2,519 provisions), mostly a malformed tool call
  carrying no content. A live retry costs ~$1.90 and has not been done.
- **Four selection ceilings were fitted to where gold rows ranked.** They are labelled `IN-SAMPLE` in
  `config/selection.json` and the figure we publish is the un-fitted one: **selection recall 56/63 =
  88.9%**, not the 61/63 = 96.8% those overrides produce.
- **39 of Timor-Leste's 83 wider rows are no-provision rows** with a blank Discovery Tag. That is a
  lot of blank-tag rows for one economy and wants a look before filing.
- Timor-Leste's no-provision rows cite **"Approves the Civil Code"** as the governing law, which is
  the fallback for an economy with no baseline and is not informative.
- **29 of China's 55 rows carry a bare-domain Source URL** (`https://flk.npc.gov.cn/`). A reviewer
  clicking one lands on a portal search page. That is a collection-stage gap, recorded as a note.

---

## 3. Output format

### The CSV — `records_<ECON>.csv`, 14 columns, UTF-8 with BOM

| # | Column | Notes |
| ---: | :---- | :---- |
| 1 | Economy | the **Coverage Matrix string**, e.g. `Lao PDR`, not the UN prose form. COUNTIFS depends on it |
| 2 | Law Name | the law's **own name as the corpus holds it**, never a translation. Where we hold a distinct English title it goes to Notes, labelled `machine-rendered, not official` when it is — which is every case outside AU/MY/SG |
| 3 | Law Number / Ref | |
| 4 | Last Amended | |
| 5 | **Indicator ID** | **decimal text** — `6.1`, `12.4.1`. Never `P6-I1`: the host's column-O formula returns `"?"` and the Coverage Matrix then counts nothing |
| 6 | Article / Section | |
| 7 | Discovery Tag | `NEW`, `KNOWN`, or **blank** on a no-provision row that is neither |
| 8 | Location Reference | chapter/page path |
| 9 | **Verbatim Snippet** | the source's **own bytes, never translated**. Each fire carries `quote_grounded_ws`, an anchor kind and a byte span proving it is a literal substring of the document — a translation could not be anchored, so translating it would trade a verifiable citation for a paraphrase. **The host requires no translation anywhere** |
| 10 | Mapping Rationale | **English on every row**, ≤300 characters |
| 11 | Source URL | |
| 12 | Confidence | |
| 13 | Notes | traps, caveats, the M8/M9 manual-check sentence, the H4 tag explanation, and the English title where one exists, labelled by provenance |
| 14 | **Language of Source** | a **name** — `Chinese`, `Lao`, `Portuguese`, `English`. Drives C1c |

Column **O is the host's own formula** and must stay empty in our output; a fifteenth data column
would overwrite it.

### The other artefacts, per economy

| File | Shape |
| :---- | :---- |
| `records_<E>.json` | the host's per-law JSON: `contract_version`, `economy`, `laws[]`, each with `provisions[]` |
| `RDTII_P3_results_<E>.xlsx` | audit workbook in `results/` — **Summary**, **All fires**, one sheet per indicator, then **QA Overturned** / **QA Ungrounded** / **QA NotInForce** / **QA Errors**. Every row on every sheet carries `Provision text` and, for a non-English economy, `Provision text (English, machine)` immediately beside it: the same span in two languages. `Full section text` is a wider document extract and is **not** what that English translates. A fire row also carries `Verbatim quote` + `English (machine)` |
| `audit/gloss_<E>.jsonl`, `audit/gloss_sections_<E>.jsonl` | the machine English, 1,340 provisions + 1,145 quotes, each record carrying the original it glosses, `machine_translation: true` and the model. **The emitter never opens these files** — a translation cannot reach column I, and `tests/test_gloss_isolation.py` pins it |
| `audit/index_<E>.html` | fire-by-fire review view, quote beside source |
| `rollup/economy_scores_<E>.json` | score, basis, evidence count, controlling law per indicator |
| `submission_report_<E>.json` | row counts by cell and tag, and `blank_discovery_tag {count, indicators}` |
| `map/verdicts_<E>.jsonl`, `verify/verified_<E>.jsonl` | the reasoning trail — **`verified_*` carries the mapper, the verifier and the escalation reviewer each with their own reason**, and is the file to read when a row looks wrong |

---

## 4. File structure

```
Desktop/rdtii-finale-p3-runs/run_2026-09-27/        2.8 GB — the run
  index/          prefilter_corpus.jsonl (767,105 rows), embeddings.f16.npy (1.5 GB),
                  doc_meta.json, bm25_top.npz + dense_top.npz (61 indicators; *.9ind.bak.npz
                  preserves the nine-indicator top-K the first run used)
  out/            the six-economy, nine-indicator run
    select/  triage/  map/  verify/  rollup/  discovery/  submission/  results/  audit/  eval/
    baseline_rows.jsonl   run_manifest.json   ingest_report.json
  out_tl52/       Timor-Leste against the other 52 indicators, same shape, kept separate so the
                  completed run could not be overwritten

Desktop/rdtii-finale-3-mapping/                     the workshop — no code
  DECISIONS.md    M11–M15; M14 caps are model-conditional, M15 recall is reported un-fitted
  notes/          the measurement record, including the gold comparison, the problems register
                  and the submission verification
  evidence/probes/  11 read-only scripts with a README saying when to rerun each

rdtii-rocky-finale/stages/p3-map/                   the code, branch w2-mapping-finale
  config/         settings, selection.json (61 indicators), economies, lawnames, languages,
                  coverage, instrument, manifest, llm/{engines.json,factory}
  contracts/instrument/   the vendored codebook — 61 blocks, 1,054 gold rows as of 29 September
  src/p3map/      ingest, prefilter/{bm25,dense}, select, triage/{local,haiku}, mapping/
                  {runner,batch_runner,schema}, verify/blind, rollup, discovery/{baseline,newknown},
                  output/{submission,excel_export,urlcheck}, eval/evaluator, chain
  tests/          286 passing, 8 skipped
```

---

## 5. What the next stage inherits

The next stage is **submission assembly and a rebuilt dashboard**. Four things it must know.

**1. The release tag points at July.** `final-submission` → `2ba4be2`, 2026-07-20, the Round 1 pitch
deck. `finale` is **40 commits behind** `w2-mapping-finale`, and neither `p2-extract-contract-0.3.0`
nor the instrument hand-off is merged into it. Checklist item 2 says the tag *is* what runs on
15 October. **As it stands the live test would run Round 1's code.**

**2. `submission/` in the repository still ships Round 1's rows** — 13 columns, `P6-I1` IDs, only
AU/MY/SG. Filing those makes the Coverage Matrix count zero provisions for every economy and fails
item 17 for want of column N. The 318 rows are in the run directory and have to be promoted.

**3. The instrument hand-off is done** (`bf2bb3e`, merged `ad27d1f`). The repo now vendors the 61-block
decimal codebook with 1,054 gold rows; `validate_instrument --require-vendored` reports *"vendored
copy is identical"*. Anything that read the old nine-block codebook needs re-checking.

**4. Mapping is scopable by setting, not by code.** `ECONOMIES` takes any of 13 economy names and
`INDICATORS_SCOPE` reaches all 61 indicators; both refuse an unknown name rather than skipping it.
The retrieval-leg guard refuses a non-English economy rather than silently returning nothing —
measured, the sparse leg returns **zero rows for China and zero for Lao PDR**. This is what
checklist item 28 rests on.

Two standing constraints do not change: **the gold set scores, it never steers** — no parameter,
threshold or prompt may be chosen from it — and **the original is the evidence**, so a translated
string never becomes a verbatim snippet.

---

## 6. What was deliberately not done

| | Why |
| :---- | :---- |
| **Cap and threshold tuning** | Measured: doubling every ceiling gains **zero** gold rows for 61% more candidate volume, and the band at the ceiling is flat in 34 of 36 cells. It is a budget dial, not a relevance filter, and it is **model-conditional** — tuning it against this embedder produces numbers that will not transfer. Decision M14, deferred to the post-deadline experiment |
| **Re-running the four fitted overrides out** | They are labelled `IN-SAMPLE` and the published figure is the un-fitted 56/63. Clearing them would invalidate 21,175 triaged pairs for two fewer gold rows at double the volume |
| **The 117 empty replies** | ~$1.90, no new rows expected — they are refusals |
| **Stage reports as gates** | `evidence/probes/verify_s4.py` does it as a probe. Making every stage refuse a report that contradicts its own output is the single fix that addresses the *pattern* rather than an instance, and it is the one I would protect if time runs short |
| **The gazette-title refusal** | A row whose Law Name is a body rather than an act is still filed. "Timor-Leste Accounting Council" appears today |
| **Curating 101 rows from 318** | Selection is now the binding constraint rather than retrieval, which is the opposite of the Round 1 problem |
