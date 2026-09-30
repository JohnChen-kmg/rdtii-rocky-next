# P3 Kickoff — Decisions & Workflow Update (2026-07-12)

**Read after** `START_HERE.md` and `PLAN.md`. START_HERE marks this project *provisional* pending a re-detailing of the mapping workflow — **this document is that re-detailing (v1)**, consolidating the P0/proposal sessions and two deep-research passes (claims below marked *verified* survived 3-vote adversarial verification against primary sources). The interfaces (consume Hand-off #2, emit the frozen 13-column CSV/JSON) are unchanged.

---

## 0. Prerequisites — what P3 blocks on

| Dependency | Status | What P3 needs from it |
|---|---|---|
| **P0 instrument** | **✅ BUILT + VALIDATED (2026-07-12), vendored to `contracts/instrument/`** | `indicators.yaml` (scoring trees + traps), `policies.yaml` (edge cases), `signatures/*.yaml` (keywords, embed text, 57 exemplars incl. negatives + teaching notes), `gold/gold_set.jsonl` (51 rows, 7 label-flagged; **post-mapping use only** — decisions 11/12). `.env` `INSTRUMENT_DIR=contracts/instrument` already points at it. |
| **P2 handoff2/** | Not built yet (P2 starts now) — **the remaining blocker** | `provisions.jsonl`, `source_text/`, `laws.jsonl`. |
| P1 manifest | ✅ complete | Passed through for coverage enumeration (contract §7.2). |

**What you can build before `handoff2/` lands:** repo scaffold, config/model-swap layer, the prefilter (bm25s + embeddings — the real signatures are now available), the mapping-prompt assembly + `trap_checks` schema generation from the vendored instrument, the 13-column CSV writer + schema validator, and the eval harness against `gold_set.jsonl` (fixture provisions can stand in for `handoff2/` until P2 delivers).

## 1. Decisions that update PLAN.md

| # | Decision | Affects | Why (evidence) |
|---|---|---|---|
| 1 | **Mapper model = `claude-sonnet-5`** (bare alias — no date-suffixed ID exists; "pin" by recording alias + run date in `model_version`) | PLAN §9 | LegalBench 83.9% (verified); contract default confirmed. |
| 2 | **Blind verifier = `claude-haiku-4-5`**, escalate disagreements to Sonnet/`claude-opus-4-8` | PLAN §5.1 | *Verified:* Haiku scores 81.2% LegalBench — 2.7 pts below Sonnet at ⅓ price ($1/$5 vs $3/$15). A different-model verifier also strengthens the blind-verify story. Expected total cost ≈ $0.035/mapped provision. |
| 3 | **Local models never do mapping or verification** | PLAN §9 | *Verified:* 16GB-class open models cluster at 68–71% LegalBench (13–15 pts below Sonnet); the gap closes only at 70B+. Ollama `llama3.1:8b` remains the mandated **no-key resilience fallback only**, with the accuracy delta documented in the README. Local JSON *validity* is fine (verified — constrained decoding beats API JSON modes); its legal judgment is not. |
| 4 | **Prefilter = bm25s (MIT) + BGE-M3 + RRF, with summary-augmented chunking** (prepend "{Act} ({year}): {one-liner}" to chunks before embedding) | PLAN §3.1 | *Verified:* bm25s = 100–500× rank_bm25 on CPU; BGE-M3 MRR@5 0.824 vs BM25 0.519 on statute retrieval; SAC halves wrong-document retrieval on boilerplate legal corpora. Recall-first, no hard Top-N ("all relevant hits advance" — grader-endorsed). Optional: a SetFit/logistic classifier over embeddings trained on the ~227 gold rows (CPU, minutes) as an extra routing signal — nice-to-have, cut first if time is short. |
| 5 | **Structured output = native `client.messages.parse()` + Pydantic** (no Instructor/Outlines dependency). **Schema field order enforces the decision procedure**: core_legal_question_answer → who_is_regulated → conditions_and_exceptions → trap_checks (explicit booleans per trap) → only then `applies`/coverage/score_hint/verbatim_quote/rationale(≤300)/confidence. Multi-label: one verdict per candidate indicator. | PLAN §4.2 | The schema IS the skilled structure — it forces the human coder's procedure and counters the organizers' #1 error class ("wrong core legal question"). Closed 9-ID vocabulary = anti-hallucination. |
| 6 | **Instrument rides in a byte-stable cached system prefix** (`cache_control: {type:"ephemeral", ttl:"1h"}`); all 9 indicator blocks always present (stable prefix), candidate indicators named in the user turn | new | Cache reads ≈ 0.1× input price — this is what makes per-provision cost ~$0.02–0.04. No timestamps/randomness in the prefix. |
| 7 | **⚠️ A/B-test few-shot exemplars against the gold set — do not assume more = better** | PLAN §4 | *Verified:* 3 *randomly chosen* few-shot exemplars **degraded** legal classification for most models in a 2026 study (Qwen3-30B collapsed 0.69→0.53). Our exemplars are curated + include negatives (different regime), but exemplar count/selection must be tuned empirically. Never few-shot the small fallback model. |
| 8 | **Batch API (−50%) for bulk non-demo runs** — optional lever; live CLI path stays the judged mode | PLAN §8.1 | 50% off everything incl. cached tokens; most batches complete <1h (Anthropic docs). Keep out of the demo path. |
| 9 | **Gold set = Round 1 only; signature exemplars = Round 1 + Round 2** (7 country tabs, 176 P6/P7 rows) | P0 seam | Round 1 alone has only 3 exemplars each for 6.1/6.3/7.2/7.4. Exclude the flagged label-noise rows (MY 7.3 "PDPA Retention Principle"=1; AU My Health Records 0.5) from eval scoring. |
| 10 | **Pin everything**: `pip freeze > requirements.lock` after install | PLAN §10 | Rubric forbids "latest". |
| 11 | **Gold-set quarantine — gold is post-mapping only.** Discovery, extraction, prefilter and mapping never consult `gold_set.jsonl`; it enters only after CSV rows exist (Discovery Tag diff, MY error-check, eval). The triage **allowlist is a production-only overlay: OFF for every reported recall number** (organic signature-only recall is the metric), ON — and disclosed in the README — for the submission run as a known-row safety net. | eval honesty | Allowlist-ON recall is trivially 100% and meaningless; the Finale assigns unseen economies with zero gold coverage, so the pipeline must achieve recall organically. |
| 12 | **`EXEMPLAR_PROFILE` config value: `eval` = Round-2-only few-shots (all 51 Round 1 SG/AU/MY gold rows held out) → this is the accuracy number we report; `production` = all curated exemplars for the submission run.** | leakage guard | The same rows must not serve as few-shot anchors AND the accuracy test set; Round 2 economies (CN/IN/ID/LA/MN/RU/TH) have zero overlap with the Round 1 eval set, so the split is airtight. |

## 2. The mapping workflow (consolidated — supersedes the provisional sketch)

Per provision from `handoff2/provisions.jsonl`:

```
A · PREFILTER (no LLM)      keywords + embeddings + obligation_type hint → top 3–4 candidate indicators
B · MAPPING CALL (Sonnet)   cached instrument prefix + provision & context → schema-forced verdicts
                            (core legal question → facts → trap checks → applies/coverage/quote/rationale)
C · BLIND VERIFY (Haiku)    fresh call, never sees B's rationale; re-answers the core legal question
                            agree → proceed · disagree → escalate to Sonnet/Opus tiebreak or flag_for_review
D · VALIDATORS (no LLM)     verbatim_quote is exact substring of source_text (char offsets) — else drop+log
                            URL HEAD < 400 · closed indicator vocab · rationale ≤300 · coverage normalized
                            repealed/currency flags propagate to Notes
ASSEMBLE                    one row per measure×indicator · deterministic "No provision found" rows (§7.2)
                            NEW/KNOWN provision-level diff vs gold_set.jsonl · MY error-check
                            13-col CSV + JSON + cost_report.json (measured)
EVAL (CI, not runtime)      prefilter recall vs gold laws · mapping F1 + field accuracy vs gold rows
                            run with allowlist OFF + EXEMPLAR_PROFILE=eval (decisions 11/12)
                            re-run on every prompt/instrument change
```

The four traps in START_HERE each map to an explicit `trap_checks` boolean in the schema **and** a verifier check — belt and braces.

## 3. Build order

1. Scaffold + config/model-swap layer (`get_llm(settings)` per contract §5.2) + CSV writer + schema validator.
2. Eval harness against `reference/Round1_Baseline_Database.xlsx` (parse the three **country sheets**, never Consolidated; forward-fill merged Indicator_ID cells; indicator IDs as strings — see P0's examples-analysis notes).
3. Prefilter over fixture provisions; measure recall vs gold laws.
4. **Wait-point: P0 instrument arrives** → mapping prompt + schema; iterate on the gold set until trap checks hold.
5. Blind verify + validators; SG PDPA s.26 → P6-I4 KNOWN row end-to-end (the vertical slice).
6. NEW/KNOWN diff + MY error-check + no-provision rows; breadth.

## 4. Documents/things to move or wire into this repo

| Item | Action |
|---|---|
| **P0 outputs** (`indicators.yaml`, `policies.yaml`, `signatures/`, `gold/gold_set.jsonl`) | When P0 finishes: copy into `contracts/instrument/` (vendored, pinned) — set `INSTRUMENT_DIR` in `.env`. **This is the blocker to finish first.** |
| `handoff2/` | Don't copy — point `HANDOFF2_DIR` at P2's output. |
| P1 `manifest.csv` | Point `MANIFEST_PATH` at `../rdtii-p1-scrape/handoff1_v2/manifest.csv` (coverage enumeration). |
| Round 1 baseline | Already staged at `reference/Round1_Baseline_Database.xlsx`. |
| Round 2 workbook | Copy `Round2_Methodology_and_Examples.xlsx` from `rdtii-p0-instrument/examples/` into `reference/` (exemplar mining per decision #9 happens in P0, but keep the source at hand). |
| Worked examples (answer key, slides, practice dataset) | Already staged in `reference/`. |

`requirements.txt` and `.env.example` are now in the repo root (this kickoff).
