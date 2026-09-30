# DeepSeek cheap-model swap — A/B-3 (triage) + A/B-4 (mapper)

Test-only evaluation of DeepSeek as a cheaper alternative to the production
Claude stack, same methodology as A/B-1/A/B-2: pre-registered gates, measure,
binary PASS/FAIL. Two candidates tested: **V4 Flash** (triage only) and **V4
Pro** (triage + mapper, both thinking arms). Provider DeepSeek, OpenAI-compatible
`https://api.deepseek.com`. Prices posted 2026-07-18 (Flash $0.0028/0.14/0.28;
Pro $0.003625/0.435/0.87 per 1M cache-hit/miss/output). Budget cap honoured;
total measured spend **≈ $0.48** across every run.

**TEST-ONLY.** No S3/S4/S5 default changed; nothing written to out/map,
out/verify, out/submission, or any judged CSV. S5 blind verify stays
Claude-family by design (cross-family verification). No cross-provider output
parity is claimed — the only admissible claim shape is identical citations +
disclosed deltas. The API key is env-only and appears in no file, log, or report.

## Verdict: NOT ADOPTED (both roles, both models)

| Test | Model / arm | Key metric | Gate | Result |
|---|---|---|---|---|
| A/B-3 triage | Flash | false-negative 34.0% | FN < 5% | **FAIL** |
| A/B-3 triage | Pro (non-thinking) | false-negative 28.8% | FN < 5% | **FAIL** |
| A/B-4 mapper | Pro non-thinking | grounding 48.4% / agreement 77.1% | ground ≥98% ∧ agree ≥90% | **FAIL** |
| A/B-4 mapper | Pro thinking (high) | grounding 71.7% / agreement 81.8% | ground ≥98% ∧ agree ≥90% | **FAIL** |

Production stack stands: **Haiku triage + Sonnet-first mapping + Haiku/Opus
blind verify**. DeepSeek is cheaper per token but misses the recall bar as a
screener and the byte-exact-quote bar as a mapper.

## A/B-3 — triage (lenient screen; reference = Haiku)

Sample: 200 pairs, **redraw** branch (seed-42 over `haiku_results.jsonl`; 22 of
200 A/B-1 seed-42 ids no longer resolve after v2.4/v2.4b — disclosed). Reference
= Haiku production verdicts (0 fresh Haiku calls). Schema-parse failure 0.00.

| model | FN rate | agreement | confusion (DSkeep/Hkeep · DSdrop/Hkeep · DSdrop/Hdrop · DSkeep/Hdrop) | cost |
|---|---|---|---|---|
| Flash | 0.340 | 0.740 | 49 · 51 · 99 · 1 | $0.015 |
| Pro (non-thinking) | 0.288 | 0.795 | 60 · 40 · 99 · 1 | $0.047 |

**Why both fail:** DeepSeek applies mapper-level strictness during what is
specified as a *lenient* screen — it drops on "not the controlling evidence"
reasoning, so recall-critical candidates never reach the mapper. Pro is modestly
better than Flash but still ~6× over the 5% gate. Same failure class A/B-1 found
for local qwen (16% FN).

## A/B-4 — mapper (reference = S4 Sonnet verdicts on disk; V4 Pro, two arms)

Sample: 150 provisions, seed 4, stratified AU 77 / SG 51 / MY 22; 76 trap-relevant,
83 S5-verified; canonical `sg-pdpa2012-001#s.26(1)` force-included. Enforcement =
`response_format json_object` with the byte-identical S4 system prefix (DeepSeek
uses no forced tool call — recorded, no parity claimed). Schema-valid 100% both arms.

| metric | non-thinking | thinking (high) | Sonnet ref | Haiku (A/B-2) | gate |
|---|---|---|---|---|---|
| **quote grounding (exact substring)** | 48.4% (n=62) | 71.7% (n=99) | 91.3% | 43.4% | **≥ 98%** |
| applies-agreement vs Sonnet | 77.1% (n=231) | 81.8% (n=231) | — | — | **≥ 90%** |
| agreement vs S5-verified subset | 63.9% (n=83) | 79.5% (n=83) | — | — | — |
| trap-set accuracy | 89.2% (n=37) | 86.8% (n=38) | — | — | no systematic fail |
| canonical s.26(1) (P6-I4 yes / P6-I1 no) | ✅ pass | ✅ pass | ✅ | — | must hold |
| per-economy agreement (AU/SG/MY) | 0.68 / 0.80 / 0.91 | 0.76 / 0.83 / 0.91 | — | — | — |
| cost / provision | $0.00041 | $0.00171 | ~$0.016 | — | — |
| projected full-run (10,574 pairs, PROJECTION) | ~$4.29 | ~$18.13 | measured $-per-row | — | — |
| reasoning tokens | 0 | 233,637 | — | — | — |
| **arm gate** | **FAIL** | **FAIL** | — | — | — |

**The decisive failure is quote grounding.** The pipeline's integrity guarantee
is byte-exact verbatim quotes (validated by exact-substring); DeepSeek paraphrases
or lightly edits the quoted text even when it identifies the right provision.
Thinking mode nearly doubles grounding (48% → 72%) and lifts agreement, but 72%
is still far below the 98% audit-trail bar, and agreement never clears 90%.
Notably MY (Malay-mixed) agreement is the *highest* per economy (0.91), so the
failure is not Malay-language grounding — it is systematic quote paraphrase.
The canonical s.26(1) trap holds and trap accuracy is ~87–89% (not a systematic
trap failure), so the model *reasons* acceptably; it just cannot be trusted to
copy text verbatim, which is non-negotiable for the audit trail.

Cost is genuinely low (non-thinking ~$4 projected full-run vs Sonnet's measured
~$170-scale), but the honesty rule forbids trading the byte-exact-quote guarantee
for price. Recommendation for the submission's cost-scaling section: cite this as
measured evidence that the cheap-model swap was *tested and rejected on
grounding*, and keep the distillation-cascade roadmap (fine-tune a local model on
Claude verdicts) as the real cost lever — not an off-the-shelf provider swap.
