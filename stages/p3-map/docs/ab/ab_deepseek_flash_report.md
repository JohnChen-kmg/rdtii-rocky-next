# DeepSeek V4 Flash swap — A/B-3 (triage) + A/B-4 (mapper)

Provider: DeepSeek (OpenAI-compatible, https://api.deepseek.com). Model sent:
`deepseek-chat` (the current non-thinking alias of deepseek-v4-flash; both share
one price card, deprecation 2026-07-24). Price table posted 2026-07-18
(cache-hit $0.0028 / cache-miss $0.14 / output $0.28 per 1M tok). Budget cap
$2.00. Pre-registration: `ab_deepseek_preregistration.md` (written before spend).

**TEST-ONLY.** No S3/S4/S5 default changed; nothing written to out/map,
out/verify, out/submission, or any judged CSV. S5 blind verify stays
Claude-family by design. No cross-provider output parity is claimed — the only
admissible claim shape is identical citations + disclosed deltas. The API key is
env-only and appears in no file, log, or report.

## A/B-3 — triage replication · GATE: FN < 5% → PASS

**Verdict: FAIL.** DeepSeek false-negative rate **0.34** (≥ 5%).

| metric | value |
|---|---|
| Sample | 200 pairs, **redraw** branch (seed-42 over `haiku_results.jsonl`) |
| Redraw reason | 22 of 200 A/B-1 seed-42 ids no longer resolve in the v2.4b index (retirement / re-segmentation) — disclosed |
| Reference | Haiku production verdicts (0 fresh Haiku calls — the redraw source already carries them) |
| Confusion | DS keep/Haiku keep 49 · **DS drop/Haiku keep 51** · DS drop/Haiku drop 99 · DS keep/Haiku drop 1 |
| False-negative rate | **0.34** (51 / 150 DeepSeek drops that Haiku keeps) |
| Overall agreement | 0.74 |
| Schema-parse failure | 0.00 (JSON well-formed every call) |
| DeepSeek cost | $0.015 (200 calls) |

**Why it fails:** DeepSeek applies mapper-level strictness during what is
specified as a *lenient* screen — it reasons about whether a provision is the
*controlling* evidence rather than *plausibly related*, and drops on that basis.
Five worked drops Haiku kept:

- P7-I1 `sg-pdpa2012-001#s.56` — "only sets penalties for offences; no relation to a comprehensive data-protection framework"
- P7-I1 `au-data2022-001#s.127(1)` — "guidelines for a data-sharing scheme, not a comprehensive data-protection framework"
- P6-I3 `au-scia2018-001#st.91` — "critical infrastructure for DNS, not a mandate for local physical infrastructure"
- P6-I4 `my-pcapa2011-001#s.30` — "search-and-seizure powers, not cross-border data transfer"
- P7-I5 `my-bfia1989-001#s.71(2)` — "bank supervision access to documents, not government access to personal data"

This is the same failure class A/B-1 found for local qwen (16% FN), more
pronounced here (34%). A lenient screen must over-keep; DeepSeek under-keeps, so
recall-critical candidates never reach the mapper. **DeepSeek is not viable as
the triage model.** (For comparison, the adopted Haiku triage is the A/B-1
fallback standard.)

## A/B-4 — mapper replication · GATES: grounding ≥ 98% AND agreement ≥ 90% AND no systematic trap failure

**Status: PENDING John's go-ahead** (per the pre-registered stop-point; A/B-4
spends on the 150-provision two-arm run — non-thinking + thinking). A/B-3 FAIL
does not preclude A/B-4: a model can fail the lenient-screen role yet still be a
viable mapper. If A/B-4 also fails, the verdict is a straight "not adopted"; if
A/B-4 passes, the verdict is "mapper-viable but not triage" (DeepSeek maps,
Haiku still screens).
