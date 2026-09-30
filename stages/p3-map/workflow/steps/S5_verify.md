# S5 — Blind verify · **Haiku (blind) + Opus (tiebreak)** · the precision layer

**What we're doing:** re-judging every fire with a *different* model that never sees
the mapper's answer. Agreement → verified; disagreement → an Opus tiebreak, 2-of-3
majority. ~33–38% of fires get overturned — this is where false "applies" die.

**Why cross-family:** the check must not share the mapper's blind spots, so a
different model family re-answers from scratch. (Stays Claude-family by design,
regardless of any cheap-model A/B result.)

---

### The API conversation (real — `s.26(1)` / P6-I4)

**FED IN** (same cached instrument SYSTEM as S4; the mapper's rationale is **hidden**):

```
USER:
PROVISION sg-pdpa2012-001#s.26(1)
Economy: SG | Law: Personal Data Protection Act 2012 | Section: s.26(1)
TEXT:
… 26.—(1) An organisation must not transfer any personal data to a country or
territory outside Singapore except in accordance with requirements prescribed …

QUESTION (answer independently from the text alone): does this provision constitute
evidence for indicator P6-I4 under its scoring tree? Run the trap checks in the
system instructions before answering. If it applies, which branch fires
('1','0.5','0'); if not, 'n/a'.
```

**GOT BACK** (Haiku, blind — schema `{applies, score_hint, confidence, reason}`)

```json
{"applies": true, "score_hint": "1", "confidence": 0.95,
 "reason": "PDPA s.26(1) imposes a conditional regime on cross-border transfer of
   personal data. The provision mandates that organisations \"must not transfer any
   personal data to a country or territory outside…\" [conditional path exists]"}
```

---

**Outcome:** Haiku's `applies/score_hint` matches the mapper → **`agree`**, no Opus
call needed. Recorded to `verified_SG.jsonl` as `verifier_verdict:"agree",
final_applies:true, final_score_hint:"1"`. Only `agree` / `tiebreak_upheld` fires
count as evidence downstream; `tiebreak_overturned` are dropped; `split` → human.
