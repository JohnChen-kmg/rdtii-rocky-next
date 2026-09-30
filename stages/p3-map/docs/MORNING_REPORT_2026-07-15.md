# Morning report — Phase A overnight build (2026-07-15, ~02:40)

**TL;DR: Phase A is built, gated, and green — at $0 spent.** The corpus is ingested
with a perfect grounding score, both retrieval legs ran, banded selection passes the
recall gate at 1.0, and the local-model triage of the gray band is running now
(checkpointed; finishes mid-morning). Nothing has touched the Anthropic API.

## What ran tonight (all measured, all committed)

| Stage | Result | Gate |
|---|---|---|
| Environment | CUDA torch 2.6.0 on the RTX 4070 Ti SUPER; `requirements.lock` frozen | pinned ✅ |
| T0 scaffold | config spine, CLI, README, git history (4 commits) | `version` prints CONTRACT_VERSION=0.2.0 ✅ |
| S0 ingest | 319,026 records streamed in 15 s + 629 source-text chunks for the 7 thin-extraction docs | **100% byte-exact grounding, 0 schema failures** ✅ |
| S1 sparse | bm25s, indicator-as-query, 22 s | s.26(1) → P6-I4 rank 39 ✅ |
| S1 dense | BGE-M3 on GPU, 83.7 min (after a 50× throughput fix: BGE-M3's default 8192-token padding → capped at 512) | cosine ranges sane ✅ |
| S2 selection | RRF + soft hint boosts + Appendix-A caps → **direct 9,750 / gray 29,250 pairs** (framework est. 25–35k ✓) | **organic recall 1.0 (37/37), allowlist OFF** ✅ |
| Baseline parser | Round-1 country sheets → 228 rows, 51 in P6/P7 scope | AU 11 / MY 26 / SG 14 == gold distribution exactly ✅ |
| S3 triage | qwen2.5:14b on the 29,250 gray pairs, $0, checkpoint/resume-safe | running — check `out/triage/` |

## Two decisions I made overnight (flagging for your review)

1. **Recall-gate denominators.** Score-0 gold rows citing no articles (e.g. "no
   infrastructure requirements were found") are excluded from retrieval-recall — they
   are produced by the deterministic no-provision stage, not by search. **Exception:**
   the inverted-polarity rows (P7-I1/P7-I2, where score 0 = framework exists) stay in,
   and all three hit organically.
2. **`PREFILTER_FLOOR` recalibrated** 0.008 → 0.0001 (the old value was mis-scaled
   for RRF and silently emptied the gray band).

## What's next (needs you)

1. **API top-up** → unlocks the day-2 A/Bs (~$10–15: local-triage-vs-Haiku on 200
   pairs; Haiku-vs-Sonnet mapper on ~500 SG pairs) and then S4 mapping of the SG slice.
2. **P2 lane fix for AU SOCI** (`au-scia2018-001` still 1 provision; full text is in
   source_text as fallback, so not a blocker).
3. Framework Part 4 open questions — none block S4 prompt-building, which I can start
   at $0 (prompt assembly + schema + validators, no API calls).

## Where everything lives
- Stage artifacts: `out/` (ingest_report, select/select_report.json, triage/, baseline_rows.jsonl)
- Indexes: `data/index/` (embeddings.f16.npy 625 MB, bm25_top.npz, dense_top.npz)
- Run it yourself: `python -m src.p3map.cli {version|ingest|prefilter|select|triage}`
