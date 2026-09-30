# S4 — Mapping · **Sonnet** · the core verdict

**What we're doing:** for each provision, deciding — per candidate indicator —
whether it applies, with a **verbatim quote**, a score, and (first) the answers to
the human coder's preliminary questions and trap checks.

**Why Sonnet:** A/B-2 measured Haiku quote-grounding at 43% vs Sonnet 91% — the gap
is exactly the byte-exact-quote guarantee we can't give up.

---

### The API conversation (real — Singapore PDPA `s.26(1)`)

**FED IN — `SYSTEM` (the "prefilled" block: the entire instrument, 25,974 chars,
byte-stable and prompt-cached so we pay for it once):**

```
You are a legal analyst coding statutory provisions against the RDTII 2.1
digital-trade indicators (Pillars 6-7). Decide from the provided text only; never
invent provisions. Follow each indicator's scoring tree exactly.

## Score polarity
GLOBAL RULE — the score runs from 0 (low regulation) to 1 (heavily regulated)…
## Shared definitions … ## P6-I1 … ## P6-I4 … <full scoring tree, disambiguation,
coding_rules, exceptions for all 9 indicators> … ## Cross-cutting scoring policy …
```
*(identical bytes on every call → cache hit; this is what makes it ~$0.016/provision)*

**FED IN — `USER` (the provision + its candidate indicators):**

```
PROVISION sg-pdpa2012-001#s.26(1)
Economy: SG | Law: Personal Data Protection Act 2012 | Section: s.26(1)
TEXT (context :: snippet :: context):
… Transfer of personal data outside Singapore
26.—(1) An organisation must not transfer any personal data to a country or
territory outside Singapore except in accordance with requirements prescribed
under this Act to ensure that organisations provide a standard of protection to
personal data so transferred that is …

CANDIDATE INDICATORS (emit exactly one verdict per candidate):
["P6-I1","P6-I2","P6-I4","P7-I1","P7-I3","P7-I4"]
Answer the core legal question first, run every trap check, then emit verdicts.
verbatim_quote must be an exact substring of TEXT.
```

**GOT BACK — `ASSISTANT` (forced tool call `emit_verdict`; field order = the coder's
procedure):**

```json
{
  "core_legal_question_answer": "s.26(1) requires organisations to ensure
      transferred personal data receives protection comparable to PDPA standards
      as a condition of cross-border transfer — a conditional flow regime, not an
      outright ban.",
  "who_is_regulated": "Organisations (private-sector data controllers) in Singapore
      transferring personal data abroad.",
  "conditions_and_exceptions": "Transfer permitted if prescribed comparable-
      protection requirements are met; Commission may exempt on application.",
  "trap_checks": {"conditional_path_exists": true, "retention_is_minimum": false,
                  "government_data_only": false, "provision_in_force": true,
                  "sectoral_scope": false},
  "verdicts": [
    {"indicator":"P6-I1","applies":false,"score_hint":"n/a","confidence":0.9,
     "verbatim_quote":"An organisation must not transfer any personal data … except
       in accordance with requirements prescribed",
     "rationale":"Conditional path exists — not a per se ban; belongs under P6-I4."},
    {"indicator":"P6-I4","applies":true,"coverage":"Horizontal","score_hint":"1",
     "confidence":0.95,
     "verbatim_quote":"An organisation must not transfer any personal data … except
       in accordance with requirements prescribed",
     "rationale":"Conditional flow regime covering personal data horizontally →
       scores 1 per the P6-I4 tree."}
    // + P6-I2 false, P7-I1 applies/score 0 (framework exists), P7-I3 false
    //   (max-retention, not minimum), P7-I4 false
  ]
}
```

---

**The point:** the schema forces `trap_checks` **before** any verdict, so the model
rules out the ban-vs-conditional trap (`conditional_path_exists=true`) *before* it
can mis-fire P6-I1. It fires **P6-I4=1** and correctly **rejects P6-I1**. Every quote
is validated as an exact substring; ungrounded quotes are flagged.

**Transports:** same prompt/schema live (`runner.py`) or Batch API
(`batch_runner.py`, −50%).
