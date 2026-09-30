# A/B-3 (triage) + A/B-4 (mapper) — DeepSeek V4 Flash swap: PRE-REGISTRATION

Timestamp: 2026-07-18T00:00:00+08:00
Provider: DeepSeek (OpenAI-compatible), base https://api.deepseek.com
Models: non-thinking `deepseek-v4-pro` · thinking `deepseek-reasoner`
Budget cap: $10.00 (hard; measured from API usage fields, abort → BUDGET-ABORTED)

Registered BEFORE any API spend. Methodology mirrors A/B-1 (ab_triage.py) and
A/B-2 (ab_mapper.py): fixed sample, fixed reference, pre-registered binary gate.

## Price table (posted, recorded pre-spend)
Source: https://api-docs.deepseek.com/quick_start/pricing · retrieved 2026-07-18 · USD per 1,000,000 tokens
- deepseek-v4-pro: cache-hit 0.003625 / cache-miss 0.435 / output 0.87
- deepseek-reasoner: same card (reasoning tokens billed as output). reasoner = thinking mode of v4-flash; reasoning tokens billed as output. deepseek-chat/deepseek-reasoner deprecate 2026-07-24.

## Input readiness (fail-loud list)
ALL PRESENT

## A/B-3 — triage. Sample rule (branch chosen from the current index)
- Draw: `random.Random(42)` over `out/triage/triage_results.jsonl`, 100 keeps +
  100 drops, exactly as ab_triage.py. Validate every provision_id against the
  CURRENT (v2.4b) index.
- If ALL resolve → REUSE (cross-check: the 40 persisted A/B-1 disagreement ids
  must be in the sample). If ANY gone → REDRAW seed-42, same stratification,
  over current `out/triage/haiku_results.jsonl`; disclose the redraw + death count.
- **Decided now:** branch = **redraw**; details:
  `{"branch": "redraw", "n": 200, "dead_ab1_ids": ["au-cca1995-001#s.105.39(7)", "au-ma1958-001#s.140ZH(2)", "au-ta1979-001#s.38B(1)", "au-ta1997-001#s.305(1)", "au-ta1979-001#s.142A(1)", "au-ta1979-001#s.11B(2)", "au-ta1979-001#s.163", "au-ta1979-001#s.181A(2)", "au-ta1979-001#s.186D(3)", "au-ta1979-001#s.77(2)", "au-ba2015-001#s.294(1)", "au-ta1979-001#s.55(4)", "au-ca1914-001#s.3L(1A)", "au-ta1979-001#s.161", "au-opggsa2006-001#s.201", "au-cca2010-001#s.51ABZZQ(1)", "au-wa2007-001#s.135N(1)", "au-ta1979-001#s.49(4)", "au-ssa1999dcb5-001#s.123YE(1)", "au-ta1979-001#s.6T", "au-ta1979-001#s.180K(1)", "au-cca1995-001#s.105A.7B(6)"], "n_dead": 22, "redraw_source": "out/triage/haiku_results.jsonl", "reason": "22 of 200 A/B-1 seed-42 ids no longer resolve in the v2.4b index (retirement / re-segmentation)"}`
- Prompt: ab_triage.py PROMPT verbatim; parse errors default to KEEP.
- Reference = Haiku: production verdict from haiku_results.jsonl where the pair
  exists there, else a fresh Haiku call with the same prompt (split logged).
- Metrics: DeepSeek false-negative rate (drops that Haiku keeps), overall
  agreement, schema-parse-failure rate, measured $.
- **GATE: FN < 5% → PASS (DeepSeek triage viable).** Report, then STOP for
  John's go-ahead before any A/B-4 spend.

## A/B-4 — mapper (only after go-ahead)
- 150 provisions stratified SG/AU/MY × 9 indicators; oversample (a) trap-relevant
  (ban-vs-conditional, retention max/min, not-in-force, inverted P7-I1/I2) and
  (b) S5-verified fires. Seed logged. Canonical `sg-pdpa2012-001#s.26(1)`
  force-included.
- Same schema-forced S4 prompt (byte-identical system prefix for cache parity;
  DeepSeek enforcement = response_format json_object, not a tool call — recorded,
  no parity claimed). Output budget scales by candidate count.
- Reference = S4 Sonnet verdicts on disk (`out/map/verdicts_{SG,AU,MY}.jsonl`,
  AU v2.4b). TWO arms reported separately: non-thinking + thinking (reasoning
  tokens in cost).
- Metrics/arm: strict char-offset quote grounding; applies-agreement overall AND
  vs the S5-verified subset; trap-set accuracy (+ canonical s.26(1) must hold:
  P6-I4 applies, P6-I1 rejected); schema validity; per-economy (watch MY Malay
  grounding); measured cost/provision incl. reasoning; projected full-run cost
  (labelled projection).
- **GATES: grounding ≥ 98% AND agreement ≥ 90% AND no systematic trap failure →
  PASS mapping. A/B-3 PASS + A/B-4 FAIL → verdict "triage-only".**

## Invariants
- TEST-ONLY: no S3/S4/S5 default changed; nothing written to out/map, out/verify,
  out/submission, or any judged CSV. All output → out/ab/.
- S5 blind verify stays Claude-family by design (cross-family verification),
  regardless of outcome.
- API key is env-only (`AB3_API_KEY`); never written to any file, log, or report.
- No cross-provider output parity claimed — identical citations + disclosed
  deltas is the only admissible claim shape.
