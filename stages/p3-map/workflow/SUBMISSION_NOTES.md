# Submission content notes (deck + README) — accumulating

Points John has flagged to include. Source measurements in WORKFLOW_LOG.md.

## Cost & scaling story (deck section — flagged 16 Jul)

**Measured unit economics (Round 1, all real):**
- $0.017 per provision mapped (Sonnet, cached instrument prefix)
- $0.012 per fire blind-verified (Haiku + Opus tiebreaks)
- ≈ $1.60 per final CSV row with byte-grounded quote + full audit trail
- Marginal cost per additional economy: ~$55–85 (bounded by per-cell caps,
  independent of corpus size)

**Scaling table (assumptions in framework doc §2.11):**
| Scope | One-time | Annual update |
|---|---|---|
| Round 1: 3 economies × Pillars 6–7 | ≈ $230 | — |
| 3 economies × all ~50 regulatory indicators | ≈ $600–850 | — |
| 20 economies × all regulatory indicators | ≈ $3,700–4,500 | **≈ $200–400/yr** ($10–20/economy) |
| Same with a gate-passed cheaper mapper (DeepSeek-class / self-hosted) | ≈ $1,500–2,000 | ≈ $80–150/yr |

**Why updates are cheap (all built, not aspirational):** content-addressed
deltas (sha256 — only changed provisions re-run; legislation churns 2–8%/yr),
cached embeddings, and the distillation cascade (local model fine-tuned on our
accumulated Sonnet verdicts screens the easy 70–80%).

**The cheaper-model position (MUST-MENTION, John 16 Jul):**
- Pipeline is provider-agnostic: one `LLMClient` adapter interface; adding any
  vendor (DeepSeek API is OpenAI-compatible) is a ~50-line adapter.
- Cheap models are adopted PER-STAGE only when they pass the same
  pre-registered A/B gates used in Round 1 (we have the receipts: Haiku failed
  quote-grounding 43% vs required 98%; local 14B failed triage FN 16% vs 5% —
  both rejected on measurement, not vibes; Haiku PASSED for triage-by-reference
  and was adopted, −$100).
- The blind-verification layer (different-model re-judge + mechanical byte-
  grounding) makes cheap-mapper adoption a controlled experiment, not a
  quality gamble — errors are caught, not shipped.
- For a UN/ESCAP production system, the clean cheap path is SELF-HOSTED open
  weights (data-governance + the judges' key-free reproducibility rubric),
  which is exactly the distillation cascade design; DeepSeek/Qwen are candidate
  base models.
- 15 RDTII indicators are officially non-regulatory and several pillars are
  formula-based — "all 12 pillars" overstates the extraction surface (~50
  regulatory indicators); scope deck claims accordingly.

## Also queued for the submission
- Traceable-changes formatting on MY error-check corrections (host format
  PDF: new info in a distinct color, strikethrough for removals) — S9 does this.
- The A/B tables as a "engineering discipline" slide (gates pre-registered,
  decisions measured).
- Verification-panel stats (SG: 1,210 fires, 399 overturned = precision layer
  visibly working) as the audit-trail evidence.
