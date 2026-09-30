# S6 — Economy rollup · deterministic + **2 LLM calls / economy**

**What we're doing:** turning verified fires into the 9 economy-level scores.

- **7 provision-level indicators:** pure Python — take the max verified score, then
  apply the instrument's clauses (escalation: ≥2 distinct verified half-point laws
  → 1.0 for P6-I1/I2; binary indicators never 0.5). **No LLM.**
- **2 economy-level indicators (P7-I1, P7-I2, inverted polarity):** one LLM call each
  — "given the collected evidence, does the economy *lack* a comprehensive
  framework?" (1 = no framework, 0 = comprehensive exists).

---

### The API conversation (real — Singapore P7-I1)

**FED IN**

```
USER:
Evidence rows collected for SG / P7-I1 (each: law, section, coverage, quote):
- Personal Data Protection Act 2012 s.13 [Horizontal] …
- Personal Data Protection Act 2012 s.26(1) [Horizontal] …
- Personal Data Protection Act 2012 s.18/s.20 [Horizontal] …
  … (up to 40 evidence rows)

QUESTION (P7-I1, INVERTED polarity): does SG LACK a comprehensive legal framework
for personal data protection? Score 1 = no framework; 0.5 = sectoral/partial only;
0 = comprehensive framework exists. Judge ONLY from the evidence above.
```

**GOT BACK** (schema `{score, controlling_law, reason}`)

```json
{"score": "0",
 "controlling_law": "Personal Data Protection Act 2012",
 "reason": "The evidence shows a single comprehensive horizontal statute, the PDPA
   2012, covering consent (s.13), notification (s.20), use/disclosure limits (s.18),
   access/correction, and cross-border transfer (s.26) — a comprehensive framework
   exists, so the economy does not lack one."}
```

---

**Result (SG):** P7-I1 = **0** (PDPA exists), P7-I2 = **0** (Cybersecurity Act 2018
+ 2024 amendments exist). Written to `economy_scores_SG.json`. Scores live in JSON's
`score_value`, never as a 14th CSV column. The rollup reads `verified_*.jsonl`
directly and counts **distinct verified laws** for escalation.
