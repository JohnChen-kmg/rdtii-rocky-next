# S3 — Triage · **Haiku 4.5** · lenient keep/drop screen

**What we're doing:** cheaply screening the ~29k gray-band pairs so only
plausibly-relevant ones reach the expensive mapper. A screen must **over-keep** —
dropping a real candidate here loses it forever.

**Why Haiku:** A/B-1 measured local qwen at 16% false-negatives (gate <5%) → Haiku
adopted. (DeepSeek later tested, A/B-3, failed worse at 28–34%.)

---

### The API conversation (real — `sg-cpc2010-001#s.20(1A)` against P6-I1)

**FED IN**

```
USER:
You are screening legal provisions for a digital-trade regulation index.

INDICATOR P6-I1 — Ban and local processing requirements:
A law prohibits, per se, the cross-border transfer of data, or mandates that
certain data be processed domestically … A complete prohibition with no compliant
transfer path…

PROVISION (from Criminal Procedure Code 2010, s.20(1A)):
… a copy of the document or thing, at the time and place stated in the order; or
(ii) to give a police officer access to … [police production-order powers]

Question: could this provision PLAUSIBLY be relevant to the indicator above?
Be lenient — answer YES if there is any reasonable connection … NO only if it is
clearly unrelated.
```

**GOT BACK** (schema-forced `{keep, why}`, `max_tokens=100`)

```json
{"keep": true,
 "why": "Plausibly relevant. Provision grants police/authorities power to issue
         orders for data production/access. Could indirectly…"}
```

---

**What happens to the output:** `keep:true` → the pair advances to S4 mapping;
`keep:false` → dropped. Errors default to **keep** (never lose recall on a glitch).
Result: 5,762 keeps of 29,250, $44.54.
