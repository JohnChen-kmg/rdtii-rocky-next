# S2 — Selection · $0 · no LLM

**What we're doing:** merging the two ranked lists and cutting each
`(economy × indicator)` cell down to a bounded candidate set, split into two bands.

**In → Out**
- In: `bm25_top.npz` + `dense_top.npz` + corpus metadata.
- Out: `out/select/direct_pairs.jsonl` (straight to the mapper) and
  `gray_pairs.jsonl` (needs the S3 screen).

**How it works** (`select.py`)
- **RRF fusion** (`RRF_K=60`): combine the two rank lists into one score per
  provision per indicator.
- **Soft hint boosts (never remove):** a provision whose `obligation_type` aligns
  with the indicator is boosted ×1.35; non-personal data down-weighted ×0.85 for P7.
- **Bands + caps (Appendix A):** top-N per economy → **direct**; next 3×N above the
  floor → **gray**. Caps: P6-I1/I4=500, P6-I2=300, P6-I3=200, P7-I1=150, P7-I2=200,
  P7-I3/I5=600, P7-I4=200. Caps bound cost regardless of corpus size.

**Gate:** every resolvable gold row must appear in the candidates —
**recall 1.0 (37/37)**, allowlist OFF (we don't hand it the answers).
