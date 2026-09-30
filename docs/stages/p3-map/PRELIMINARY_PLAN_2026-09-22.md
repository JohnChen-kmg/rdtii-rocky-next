# Preliminary plan: mapping, 22 to 30 September

Written 2026-09-22, eight days before the code freeze, while stage 1 is still crawling. It re-orders
`PLAN.md` for the time that is left and adds the work `PLAN.md` never had: the decimal-ID migration that
the instrument hand-off waits on, three non-English economies, and the output rules set since 12
September. `PLAN.md` still holds the step detail for 2A to 2G. Where the two disagree on order or scope,
this file is the newer one.

**Preliminary** means the decisions in section 8 are proposals. Nothing here is settled until it has a
`DECISIONS.md` entry.

---

## 1. The task, in one page

**What the stage does.** Mapping reads grounded provisions from extraction and decides which RDTII
indicator each one evidences, with a verbatim quote, a rationale and a confidence. It then rolls
provisions up to an economy score, tags each row NEW or KNOWN against the 2025 baseline, and emits the
evidence rows. Round 1 did this in eleven steps, S0 to S10:

- **S1 and S2**, free retrieval: BM25 plus BGE-M3 embeddings, where the indicator is the query.
- **S3**, a cheap lenient triage.
- **S4**, a schema-forced verdict from the strong model against the cached codebook.
- **S5**, blind re-judging by a second model, with a third as tiebreak.
- **S6 to S10**: rollup, NEW/KNOWN, emit and evaluation, all deterministic.

The walk-through is `reference/round1/mechanism/MAPPING_MECHANISM.md`.

**What it is marked on.** Directly: C2a 10, C2b 10, C4b 7 and C5 10, which is 37 of 100. Indirectly, the
rows it writes are the evidence for C1a, C1b and C1c, worth 40 more. The export schema behind C3b is
also written here.

**What it receives.**

| From | What | Where it lands |
| :---- | :---- | :---- |
| Extraction | `laws.jsonl`, `provisions.jsonl`, `doc_status.jsonl`, `source_text\` | `HANDOFF2_DIR`, read by `ingest.py` |
| Instrument | Codebook, policies, signatures and gold set | `stages\p3-map\contracts\instrument\`, copied in at hand-off |

**What it must produce, by date.**

| Date | Deliverable | Mapping's part |
| :---- | :---- | :---- |
| 30 Sep | Evidence workbook, 14 columns, rows 9 to 109 only, so **101 rows at most** | Every row: decimal-text IDs, the Language of Source column, a verbatim snippet, a rationale of at most 300 characters in the host's sentence form, and a confidence |
| 30 Sep | Word Section 5, the engine declaration. "Cannot be corrected after the deadline" | Per engine: the exact checkpoint, the cost of one run of two indicators, and known weaknesses on legal text. **Only real runs produce these** |
| 30 Sep | Code freeze. Settings may change afterwards, code may not | Everything in section 5 of this plan |
| 15 Oct | Live test: one of nine economies, one pillar, two indicators; Engine A, then Engine B over the same documents | The comparison file, per-engine cost, and the run manifest proving the second pass fetched nothing |

## 2. Where things stand on 22 September

Checked by reading the code and the other workshops. No figure below is from memory.

| Area | State | Evidence |
| :---- | :---- | :---- |
| **Stage code** | **Unchanged since Round 1.** The only finale commit under `stages\p3-map` adds `config\indicator_ids.py` and its test, and no module imports the helper yet | `git log` on `finale`, head `92a5e9d`, tree clean |
| Engines, prices, ledger, comparison, run manifest | **None built.** No `engines.json`, `prices.json`, `pricing.py`, `ledger.py`, `openai_compatible.py`, `compare.py` or manifest writer exists | glob over the repo |
| Instrument | New draft ready: decimal IDs, 61 scoreable indicators and a gold set of 1,054 rows. **Not handed off, and waiting on this stage** | `rdtii-finale-0-instrument\HANDOFF.md`, "When to hand off" item 1 |
| Scraping, stage 1 | Still running. Six economies have a current corpus, listed below. Its code changes are not yet handed back to the repo | `rdtii-finale-1-scraping\outputs\*\README.md` |
| Extraction, stage 2 | Workshop plan dated 12 September. **No finale extraction code in the repo, and no finale provisions on disk for any economy.** Lao needs a full OCR pass | `rdtii-finale-2-extraction\PLAN.md`; `git log` |
| Dashboard | Plans its own engine presets, with Engine B as `qwen2.5:14b` on local Ollama, and its own comparison export (D4, D5 and D17). It budgets 86 hours | `rdtii-finale-4-dashboard\PLAN.md` |
| Host questions | None recorded as sent. Question 5 (a hosted open-weights Engine B) and question 7 (the 101-row limit) bear on this stage | `3_Final_Stage\OPEN_QUESTIONS_FOR_HOST.md` |

**The six economies stage 1 has collected**:

| Economy | Current corpus | What mapping must know |
| :---- | ----: | :---- |
| Australia | 1,278 documents | Round 1 economy; new crawl |
| Singapore | 738 | Round 1 economy; new crawl; repealed acts excluded on purpose |
| Malaysia | 1,391 | Round 1 economy; new crawl |
| China | about 1,060, in per-source folders | Chinese. The national database was downloaded by hand, because its robots.txt forbids crawling. CAC was crawled. Pillar 6 is framework-only here: the numbers sit below the database |
| Lao PDR | 1,762 | Lao. **93.6% scans**, and every principal pillar 6 and 7 law is a scan. The 53 English translations are left out of the corpus |
| Timor-Leste | 1,921 gazette issues | Portuguese, native text. **One PDF can carry several acts**: 923 of the 1,953 listed issues do. No status or version date on the portal. No baseline sheet, and **not one of the nine live-test economies** |

## 3. What changed since `PLAN.md` was written on 12 September

| Change | Source | What it adds to this stage |
| :---- | :---- | :---- |
| Indicator IDs become decimal text, 61 scoreable | Instrument notice, 13 Sep | The migration in step 3A. Mapping is the hand-off gate. The full list with file and line is `notes\INSTRUMENT_IMPACT_2026-09-22.md` |
| Rows for indicators the tool does not automate carry one fixed notification sentence | M8 and M9, 20 Sep | A notification-row writer, driven by the instrument's `coverage` mark, which is still empty (request R1) |
| Three new economies, all non-English | Scraping outputs | Retrieval that works without English keywords; Language of Source on every row; name matching across languages |
| Discovery Tag matched on instrument name and section, never URL | `ISSUES\2026-09-21_minimal-source-set.md` | Blocking for the comparison export |
| A null for an unchecked watch-list source means "not looked for", not "no provision found" | `ISSUES\2026-09-21_update-watchlist.md` | A distinct null statement. Cut candidate, see section 9 |
| The host's live-test sheets, read cell by cell | `OUTPUT_TEMPLATE_FINAL_ROUND.xlsx` | Exact capacities and strings, in the appendix. **The comparison sheet counts 40 provisions**, so a run producing more needs a rule |

## 4. The critical path

```
3A decimal-ID migration ──► instrument hand-off ──► mapping runs on CN, LA, TL ──► ≤101 workbook rows ──► 30 Sep
                                                       ▲
                        extraction delivers CN, LA, TL provisions, by 27 Sep at the latest

2A prices + 2D engines + manifest ──► 2C ledger ──► live-profile run per engine ──► Section 5 numbers ──► 30 Sep
                                                 └─► 2E comparison, fed by those two runs
```

Two chains run in parallel, and only the first depends on another stage. **The engine chain can be built
and tested today against the Round 1 reference arm**, `OUT_DIR` and `INDEX_DIR` pointed at
`RDTII\pipeline-data\rdtii-p3-map`, while stages 1 and 2 are still working. That is the main reason to
start it now.

The one date this stage cannot control: **extraction must hand over provisions for China, Lao PDR and
Timor-Leste by 27 September.** A later hand-over leaves no time to map, verify and review by eye before the
freeze. Section 10 says what happens if it slips.

## 5. The work, in priority order

Tier 1 is the freeze minimum. Tier 2 goes in if Tier 1 lands early. Tier 3 is cut unless something
changes. Hours are working estimates for one developer.

| # | Work | Hours | Tier | Detail |
| :---- | :---- | ----: | :---- | :---- |
| W1 | **3A Decimal-ID migration and any-economy readiness** | 10 | 1 | Section 5.1 |
| W2 | 2A.1 to 2A.2 price table that refuses; 2D engines and run manifest | 6 | 1 | `PLAN.md` 2A and 2D, section 5.2 |
| W3 | **Grounding by construction**, new | 2 | 1 | Section 5.3 |
| W4 | Retrieval that works without English keywords, new | 4 | 1 | Section 5.4 |
| W5 | The 14-column output: notification rows, zero-score filters, NEW/KNOWN by name and section | 7 | 1 | `PLAN.md` 2F, section 5.5 |
| W6 | 2C cost ledger and roll-up | 3 | 1 | `PLAN.md` 2C |
| W7 | 2E comparison, in the host's exact shape | 3 | 1 | `PLAN.md` 2E, section 5.6 |
| W8 | One pre-registered live-profile run per engine, which gives the Section 5 numbers | 4 | 1 | Section 5.7 |
| W9 | Mapping runs and review for the evidence workbook | 6 attended | 1 | Section 5.8 |
| W10 | 2A.3 OpenAI-compatible client, needed only if Engine B is hosted | 2 | 2 | `PLAN.md` 2A.3, decision D-1 |
| W11 | 2G reproduce-evidence verb | 2 | 2 | `PLAN.md` 2G. The cheaper version documents the existing `chain` module as the one command |
| W12 | "Not looked for" null statement from the watch lists | 2 | 3 | The watch lists live in the scraping workshop, not the repo, so a clean clone could not read them |
| W13 | 2B.1 and 2B.2, lifting the full provider-agnostic harness out of `ab_deepseek.py` | 5 | 3 | W8 gives Section 5 what it needs |
| W14 | Extract-stage ledger mirror | 1 | 3 | Already first on `PLAN.md`'s cut list |
| | **Tier 1 total** | **45** | | Plus 2 to 4 for Tier 2 |

**45 hours in 8 days is the honest size of this stage's freeze minimum.** It competes with the scraping
hand-back, extraction's Lao OCR work, which has not started, and a dashboard plan of 86 hours. The
cross-folder cut decision the reviewers asked for on 12 September is due now. The smallest mapping scope
that still earns its criteria is in section 9.

### 5.1 W1: decimal IDs, and accepting any economy

The detail, with file and line, is in `notes\INSTRUMENT_IMPACT_2026-09-22.md`, items A1 to A18. In order:

1. **A loader over `indicator_order.yaml`** replaces the `INDICATORS` literal at `config\settings.py:74-77`.
   It keeps host order and filters to the automated set. Until request R1 fills `coverage`, filter on
   pillars 6 and 7, `status: in_scope`, which gives the same nine.
2. **Remove the legacy literals** from `schema.py`, `select.py`, `rollup.py`, `submission.py` and
   `excel_export.py`, and fix the `P*.yaml` globs. Read `level` and polarity from the YAML rather than
   keeping per-ID branches.
3. **Accept any economy.** Replace `ECONOMIES = ["SG","AU","MY"]` at `settings.py:78` with codes read from
   the input, plus one table from code to official UN name. The live test may draw any of nine economies,
   and seven of them have no crawler yet, so this stage must at least not be the reason one fails.
4. **Apply leave-one-economy-out at run time**, not only at evaluation, in `prefilter\queries.py`. China's
   and Lao PDR's own host rows are now signature exemplars. Left in a China query, they are the baseline
   answer inside the retrieval.
5. **Read Round 1 artifacts through `indicator_ids.normalize()`.** Never rewrite the reference arm in place.
6. **Hand off.** Run the instrument's `HANDOFF.md` steps 2 to 5 on a branch, then this stage's tests and a
   small mapping run.

**Done when** the stage runs on the workshop copy of `instrument\output\`, and the tests pass. A re-emit of
Singapore's 42 filed rows must reproduce them with only two changes: the ID form, and the new language
column.

### 5.2 W2: prices, engines and the run manifest

`PLAN.md` steps 2A.1, 2A.2, 2A.4 and 2D, unchanged in substance. Three sharpenings:

- **Pin exact model identifiers** in `engines.json`. The defaults in `settings.py:26-33` are
  `claude-sonnet-5`, `claude-haiku-4-5` and `claude-opus-4-8`. Section 5 says a floating alias is not an
  answer, so record the dated identifier each one resolved to on the day it was tested.
- **Engine B's four roles are all open weights**, triage included. Otherwise the Section 3 box, "no
  proprietary API or hosted service", cannot be ticked honestly.
- **The run manifest records what p1 fetched for this run**, not only what p3 read. The live-test proof is
  "documents fetched during the second pass: 0". That number is the crawler's; the manifest copies it
  rather than inferring it.

### 5.3 W3: grounding by construction, new

Round 1 lets the model write `verbatim_quote` as free text (`schema.py`), and `runner.py:115` checks
afterwards whether it is a substring of the provision. That check is where every alternative model
failed in Round 1: the Haiku mapper grounded **43.4%**, and DeepSeek **48.4% and 71.7%**, against a 98% bar
(`reference/round1/brief/STATION_3_P3_MAP.md`). Engine B would almost certainly fail it too.

**Proposal.** When a verdict's quote is not an exact substring, emit the provision's own `verbatim_snippet`
instead. Extraction already byte-grounds that text at recorded offsets. Mark the substitution in Notes and
lower the confidence. Never emit an ungrounded quote.

- The Article / Section column already comes from the provision record, not from the model, so citation
  precision does not change.
- C2b becomes a property of the pipeline rather than of the engine.
- The stronger version has the model return sentence indices instead of text, and code cuts the quote. It
  is better, and it is also a larger change to the mechanism a week before the freeze. Recommend the
  fallback now. After 30 September neither can be added, because that is code.

### 5.4 W4: retrieval without English keywords, new

Signature keywords are English only, so the BM25 leg cannot find a Chinese, Lao or Portuguese provision.
BGE-M3, the dense leg, is multilingual. But **the interface's run path, `main.py:575-577`, runs the BM25 leg
only and writes an empty dense stub.** A Chinese corpus run from the button today would get English keyword
retrieval and nothing else.

**Proposal.** For a non-English economy, run the dense leg over the automated indicators, restricted to
candidate laws: the seed and core acts the registries already name. The minimal-source-set issue measured
that pillars 6 and 7 need a median of two websites. The candidate set is small, which keeps embedding
time inside a live hour. Agree this with whoever owns `main.py`, because that file is outside the stage.
Request R3 would add source-language keywords as a second leg, but it is optional.

**Done when**, with China's own rows left out, retrieval surfaces China's gold pillar 6 and 7 rows at a
recall worth stating. Measure it and write the number down, whatever it is.

### 5.5 W5: the 14-column output

| Rule | Source | Where |
| :---- | :---- | :---- |
| 14 columns, with Language of Source last. IDs written as text | Workbook Instructions sheet | `submission.py` `COLUMNS` `:35-38` |
| Economy in the official UN name. Coverage Matrix label workarounds belong to the workbook writer, which is the dashboard's D6 | Workbook field rule; host question 7 | `submission.py` |
| Rationale of at most 300 characters in the host's form: "This [article] [prohibits/requires/permits/establishes] [what]. Maps to [indicator] because [reason]." | Output Data `J5` | prompt, and a validator at emit |
| Confidence on every row, with a stated threshold below which a human checks | Workbook: "flagging low confidence is treated as a strength"; README template | emit, and the README |
| **Zero-score filters**, before emit: repealed text, drafts, an amending act cited instead of the principal act, per-provision rows for 7.1 and 7.2, and measures applied only to government data | `policies.yaml` `edge_cases`; `indicator_order.yaml` `host_mapping_traps` | `PLAN.md` 2F |
| **Notification rows**: one fixed sentence for any non-automated indicator in a run's task, and for any automated indicator an economy override marks, for example China's pillar 6 | M8, M9; request R1 | new, in `submission.py` |
| **NEW/KNOWN on instrument name and section**, never URL. Read the Round 1 and Round 2 baselines. Timor-Leste has no sheet: every row there is NEW, and Notes says why. Lao needs cross-language name matching, because the host names Lao laws in English and our corpus names them in Lao | Workbook Instructions; the minimal-source-set issue; request R2 | `discovery\baseline.py`, `discovery\newknown.py` |
| Timor-Leste rows name the **act** inside the gazette issue, never the issue | Scraping `outputs\TL\README.md` | extraction supplies it; emit refuses a row whose law name is an issue title |
| Rows quoted from OCR text say so in Notes | Lao corpus | emit |

### 5.6 W7: the comparison, in the host's exact shape

`compare.py` takes two run directories and refuses runs over different document sets, per `PLAN.md` 2E. It
emits exactly the host's Engine Comparison sheet, not something like it:

- **Per-engine block:** provider and model, start and end in hh:mm, elapsed minutes, documents fetched
  during the pass, and cost in US dollars. Cost is read from the ledger, never computed in the page.
- **One row per provision** either engine produced: law name, article or section, indicator ID, and
  **found by, exactly `Engine A only`, `Engine B only` or `Both`**. Then indicator differs, citation
  differs and quoted words differ, each Yes or No, and one line on how they differ.
- **A slot for the paragraph** on which output you would hand to a ministry, and why. The sheet says this
  paragraph "carries the marks".
- **Capacity:** the sheet counts rows 17 to 56, so 40 provisions. When a run produces more, the file keeps
  every row, and the sheet takes the 40 chosen by a stated rule.

**Ownership, proposed as D-4:** this stage builds the comparison. The dashboard renders it and writes it
into the template sheet, D5 and D17 in its plan. One join, not two.

### 5.7 W8: one pre-registered run per engine at live-test scale

The Section 5 numbers come from the live-test profile only: one economy, one pillar, two indicators. Copy
the order of `reference/round1/ab/ab_deepseek_preregistration.md`, and write the pre-registration
**with a real timestamp**, which the Round 1 pair lacked. Its order:

1. Engine and checkpoint.
2. A hard budget cap.
3. The price table, with its source and the date it was retrieved.
4. The fixed sample.
5. The metrics.

Record per engine:

- The cost of the run.
- Elapsed time.
- Grounding before the W3 fallback.
- Agreement with Engine A.
- Trap accuracy on the canonical 6.1-against-6.4 case.

Weaknesses are written in plain words a Section 5 cell can take.

**The Round 1 gates change role here.** They were written to decide whether a cheaper model could
*replace* the Claude stack. Engine B does not replace Engine A; it is declared alongside it. So the gates
become reported metrics, and Engine B's failures become its "known weaknesses on legal text". What Engine B
must do is run end to end and produce valid rows.

Use a Round 1 economy as the stand-in if China's provisions have not arrived by 26 September, and say so.

### 5.8 W9: the rows the workbook will carry

- **The new economies** run on Engine A as their provisions arrive, then blind verification. Every NEW row
  is checked by eye before it can be chosen.
- **The Round 1 economies**, proposed as D-2: reuse the 142 verified Round 1 rows. Migrate them to decimal
  IDs and check each one's currency against the new crawl's law table. Re-map only laws whose text
  changed. Disclose the reuse.
- **Budget.** Round 1 spent between US$24.01 and US$140.26 per economy on mapping alone
  (`AUTHORITATIVE_NUMBERS.md`). Price each run with the dry-run estimate first, and set `COST_HARD_STOP`
  per run.
- **101 rows at most**, proposed as D-6. First, the strongest verified row per automated indicator per
  economy where evidence exists. Then NEW rows by confidence. No economy is left with none. Keep the full
  set beside the workbook; the workbook carries the selection, and the rule is stated in the Word document.

## 6. Day by day

| Day | Mapping | Needs from others |
| :---- | :---- | :---- |
| Tue 22 | Decisions D-1 to D-7 taken. W1 starts | Developer |
| Wed 23 | W1 done and tested; hand-off rehearsed on a branch. W2 price table | Instrument: R1, R2 answered |
| Thu 24 | W2 engines and manifest. W3 grounding fallback. W6 ledger | Dashboard: engine labels agreed |
| Fri 25 | W4 retrieval without English keywords. W5 output rules | `main.py` owner: dense leg agreed |
| Sat 26 | W5 done. W8 pre-registered live-profile runs, A then B | China provisions, or a Round 1 stand-in |
| Sun 27 | W7 comparison, built from the two W8 runs | **Extraction: CN, LA and TL provisions** |
| Mon 28 | W9 runs, verification and review by eye for the new economies | |
| Tue 29 | Row selection to 101. Section 5 text. W11 if time. Changelog entries | Dashboard: xlsx writer ready |
| Wed 30 | Freeze. Tag. Nothing new starts today | |

After the freeze, `PLAN.md`'s "After the freeze" section stands unchanged: rehearse the live sequence on an
economy not yet run, from cleared caches, on a pillar outside 6 and 7, and time every phase.

## 7. What this stage needs from others

| From | What | By | Why it matters |
| :---- | :---- | :---- | :---- |
| Extraction | Provisions for CN, LA and TL with `language_of_source`, act-level `law_name` (TL), `article_section`, and whatever marks principal against amending acts and in-force against draft. The widened `provision.schema.json` copied into `stages\p3-map\00_contracts\schemas\` | 27 Sep | Without it the new economies have no rows. Wrong section or wrong act scores zero |
| Scraping | Hand-back of the six-economy engine changes to the repo. The Lao translation link, `translation_doc_id`, set on 0 rows today. `law_table.csv` status columns, which the zero-score filters read | 27 Sep | NEW/KNOWN for Lao; the repealed and draft filters |
| Instrument | Requests R1 to R4 in the impact note, then the hand-off | 23 Sep | Notification rows; the automated set; the baseline rule |
| Dashboard | Engine labels and the switch's screen and control name, final for Section 5. Agreement on D-4. The 14-column xlsx writer into the host template | 29 Sep | Section 5 cannot be corrected after 30 September |
| Developer, host | Send questions 5 and 7, and the 7.3 question from the 20 September email. None is recorded as sent | now | Engine B's form; the row limit; how many sources 7.3 needs in India and Thailand |

## 8. Decisions needed now, with a recommendation each

| # | Decision | Recommendation | Why |
| :---- | :---- | :---- | :---- |
| D-1 | **Engine B: local or hosted?** M6 proposes hosted, with the local lane as proof. The dashboard proposes `qwen2.5:14b` on local Ollama | **Local Ollama for the freeze, checkpoint pinned by digest.** The hosted path, W10, is optional, a settings-only switch if it lands | The Ollama client exists and has run. It ticks the Section 3 box literally, and it saves W10 in a week with no slack. A narrow live-test run is small enough for the measured 1 provision per second. Reverses M6's default, so it needs a new entry |
| D-2 | Round 1 economies: re-map on the new corpora, or reuse the verified rows | **Reuse the verified rows**, migrated and currency-checked; re-map only laws whose text changed | Round 1 AU mapping and verification alone cost US$176.31. The rows were verified by a blind panel and audited from artifacts |
| D-3 | The Round 1 6.2 cells built on sectoral record-keeping, Round 1 decision D3 | **Re-judge them under the new Tier A text**, which says 6.2 is where data is stored, not general record-keeping. Apply the result in every economy alike | The instrument lists this as open. Reusing the rows under D-2 without settling it carries the question into the workbook |
| D-4 | Who builds the comparison | **Mapping builds it** (`compare.py`, CSV and JSON). The dashboard renders it and writes the template sheet | Two joins of the same runs would disagree. Record it in both workshops' `DECISIONS.md` |
| D-5 | Grounding fallback, W3 | **Adopt it for both engines** | It makes C2b hold whatever engine answers. It is code, so it is now or never |
| D-6 | The 101-row selection rule | Section 5.8's rule, stated in the Word document | The template holds 101; Round 1 alone filed 142. Host question 7 is unsent |
| D-7, M11 | One prompt prefix or one per pillar | **One prefix, of the automated blocks.** Instrument D3's per-pillar design is moot while M7 holds | The notice asks this stage to choose. The pillar 6 and pillar 7 prefixes measure 19,842 and 20,902 characters; one prefix of both stays near Round 1's 25,974 plus the host's new trap text |

## 9. If the hours run out

Cut in this order: W12, W13, W14, then W11 down to a documented `chain` command, then W10. Then W4 shrinks
to candidate-law pre-selection with no dense leg.

The smallest scope that still earns its criteria is about 27 hours:

| Work | Hours |
| :---- | ----: |
| W1, decimal IDs and any economy | 10 |
| W2, without the OpenAI-compatible client | 5 |
| W3, grounding fallback | 2 |
| W5, reduced to 14 columns, decimal text and the zero-score filters | 4 |
| W6, cost ledger | 3 |
| W7, comparison | 3 |

**Never cut:**

- The migration, because the instrument waits on it.
- The run manifest. Without it the engine swap cannot be proven, and 4 marks go with it.
- The ledger lines. Cost is verified against the code.
- The 14-column output with decimal text.
- The grounding rule.

## 10. Risks

| Risk | Consequence | Mitigation |
| :---- | :---- | :---- |
| Extraction delivers the new economies late, or not at all for Lao | Few or no rows for 3 of 6 economies: C1a, and C1c most of all | Map whatever arrives. The Section 4 readiness table says exactly what ran. Lao OCR is the slowest input, so ask for Timor-Leste and China first |
| Lao OCR errors inside a byte-exact quote | The quote matches the OCR text, not the official scan | Say OCR in Notes, lower confidence, and have a human open the scan for every chosen Lao row |
| A Timor-Leste row cites the gazette issue, not the act | A real act cited to the wrong place scores zero | Emit refuses issue titles as law names |
| Own-economy exemplars in retrieval for China and Lao | Baseline leakage into discovery, and a weaker NEW claim | Leave-one-economy-out at run time, W1 step 4. Re-run the Round 1 leakage audit's argument before 30 September |
| The live test draws an economy with no crawler: 7 of the 9 | C5a discovery points are likely lost | Out of this stage's hands. Its job is to accept any economy and language without a code change, W1 step 3 |
| Engine B's quality on legal text | A weak comparison paragraph | Report it honestly; the sheet rewards the paragraph, not agreement |
| 45 hours against every other stage's load | Something unplanned gets cut on 29 September | Take the cross-folder cut decision now, using section 9 |

## 11. Done on 30 September

- [ ] The instrument is handed off, tests pass, and `stages\p3-map` holds no legacy ID outside the
  translation table.
- [ ] `engines.json` declares two engines, one open weights, with exact checkpoints. `RDTII_ENGINE` changes
  every role at once.
- [ ] An unpriced model raises before any call is made.
- [ ] Every model call writes a ledger line. The roll-up reproduces the per-stage totals, and unpriced calls
  show as unpriced.
- [ ] Every run writes a manifest: resolved models, commit, input documents, and documents fetched by p1.
- [ ] No row carries an ungrounded quote, under either engine.
- [ ] `compare` emits the host's Engine Comparison shape with the exact found-by strings.
- [ ] Rows for six economies, or an honest gap per economy. Every row carries decimal-text IDs, the
  language column, notification rows where they apply, and the zero-score filters.
- [ ] Section 5 carries measured numbers from one pre-registered live-profile run per engine.
- [ ] `evidence\` holds the pre-registrations and score cards, the cost roll-up, one comparison and both run
  manifests.

---

## Appendix: the host's live-test sheets, read cell by cell on 2026-09-22

From `1_Rules\Final_Round\OUTPUT_TEMPLATE_FINAL_ROUND.xlsx`.

| Sheet | Shape | What the code must match |
| :---- | :---- | :---- |
| Output Data | Headers in row 4, columns A to N plus the Pillar formula in O. Example rows 7 and 8 are deleted before submitting. Data rows 9 to 109 | Column E is text. `J`: at most 300 characters, in the host's sentence form. `L`: 0.00 to 1.00. `N`: the original language |
| Engine Comparison | Per-engine block in rows 5 to 10. Provision rows 17 to 56, with row 16 an example. `COUNTIF` on column E for `Engine A only`, `Engine B only` and `Both` at `D58:D60`. The paragraph prompt at `A62` to `A68` | Found-by strings exactly as written. At most 40 counted provisions |
| Run Record | Engine rows 5 and 6, and the total at `F7`. Document rows 12 to 56, with row 11 an example. `COUNTIF` on column C for `Engine A pass` and `Engine B pass` at `E58:E59`. The short-note block at rows 61 to 67 | "Fetched during" strings exactly as written. At most 45 counted documents. The second count must be 0 |

The Run Record's document list is the crawler's to fill. The manifest in W2 carries the numbers across.
