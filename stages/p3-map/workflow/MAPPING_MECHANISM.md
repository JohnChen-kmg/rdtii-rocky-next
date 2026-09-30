# The mapping mechanism, step by step — with real traced examples

Every example below is real pipeline output (not illustrative mock-ups). The
through-line is Singapore's most important provision — **PDPA 2012 s.26(1)**,
the cross-border transfer rule — traced from raw corpus record to verified
verdict, plus counter-examples showing the traps and filters doing their jobs.

---

## Step 0 — Ingest & byte grounding (S0)

Every provision arrives from P2 with its quote plus character offsets into the
source document. S0 re-checks the claim byte-for-byte:

```
record:  provision_id = sg-pdpa2012-001#s.26(1)
         verbatim_snippet = "An organisation must not transfer any personal
                             data to a country or territory outside Singapore
                             except in accordance with requirements prescribed
                             under this Act..."
         snippet_char_start/end = offsets into source_text/sg-pdpa2012-001.txt
check:   source_text[start:end] == snippet  →  byte-exact ✅
```

Measured across the corpus: **411,986 / 411,986 byte-exact (100%)** (corpus v2.4b,
after the 2026-07-18 AU segmentation fix; 392,181 at v2.4, 319,026 pre-v2.4). This is why
every quote the pipeline ever emits can be trusted mechanically — nothing
downstream is allowed to paraphrase.

For the 7 documents whose provision segmentation is thin (e.g. the AU SOCI Act),
S0 additionally chunks the raw source text into 629 pseudo-provisions so the
retrieval stages can still find their content.

## Step 1 — Retrieval: the indicator becomes the query (S1)

We do not search for provisions; we ask, for each of the 9 indicators, "which
provisions look like you?" Each indicator's query document is built from the
vendored instrument — name + definition + keyword list + two exemplar impacts.
Excerpt of the **P6-I4** query:

> *Conditional flow regimes. Cross-border data transfer is permitted only if
> conditions are satisfied: data-subject consent, adequacy or equivalence of
> protection in the destination, contractual safeguards or self-assessment, or
> government approval… unless · except in accordance · adequate level of
> protection · standard contractual clauses · transfer impact assessment…*

Two independent engines score all 319,655 corpus rows against each query:
- **Sparse (bm25s)** catches terms of art — s.26(1) ranks **#39 of 319,655** for
  P6-I4 on keywords alone.
- **Dense (BGE-M3 embeddings)** catches paraphrase — a provision saying "shall
  not disclose to a place beyond the borders" matches "cross-border transfer"
  with no shared words. Provision text is metadata-prefixed
  (`law_name | section | location :: text`) so boilerplate can't hijack matches.

## Step 2 — Selection: bands and caps (S2)

Reciprocal-rank fusion merges both rankings; extraction hints nudge but never
veto (a provision P2 tagged `conditional` gets a boost toward P6-I4 — but tags
were measured only 47–81% reliable, so they can never remove a candidate).

Real S2 output for s.26(1) — it entered **seven** candidate pairs:

| Indicator | RRF score | Band |
|---|---|---|
| P6-I4 conditional flow | 0.0314 | **direct** (top of cell) |
| P7-I3 min-retention | 0.0295 | direct |
| P6-I1 ban | 0.0223 | direct |
| P6-I2 storage | 0.0171 | direct |
| P7-I1 DP framework | 0.0160 | direct |
| P7-I4 DPO/DPIA | 0.0069 | direct |
| P6-I3 infrastructure | 0.0025 | **gray** → triage |

Note the design: P6-I1 (ban) is *deliberately kept* alongside P6-I4 — the
ban-vs-conditional trap is resolved by the mapper with the full text, never by
retrieval scores. Per-cell caps (500 for P6-I1/I4, 600 for P7-I3/I5…) bound the
paid volume: 9,750 direct pairs + 29,250 gray pairs corpus-wide.
**Gate:** all 37 resolvable gold-standard rows surface organically — recall 1.0.

## Step 3 — Triage: cheap screen of the gray band (S3)

Gray pairs get one lenient yes/no from Haiku (adopted after the A/B measured the
local model missing 16% of what Haiku keeps). Real example — s.26(1)'s gray
pair, correctly killed:

```
pair:    s.26(1) × P6-I3 (infrastructure requirement?)
verdict: keep = false
reason:  "Provision concerns data transfer restrictions, not infrastructure"
```

Across the corpus: 29,250 judged, **5,762 kept (20%)**, $44.54. Errors default
to *keep* — recall over precision at every pre-mapping stage.

## Step 4 — Mapping: the schema is the method (S4)

Each surviving provision goes to Sonnet **once**, with all its candidate
indicators. Two structural tricks carry the quality:

**(a) The cached instrument prefix.** A byte-stable 25,974-character system
prompt renders the full official codebook: every indicator's question, scoring
tree, disambiguation rules, and the cross-cutting policies. Byte-stable means it
is written to the prompt cache once and read at ~10% price thereafter — the SG
run read 38.4M cached tokens, which is why mapping cost $0.016/provision.

**(b) Schema-forced field order.** The model cannot emit a verdict until it has
filled, in order: `core_legal_question_answer` → `who_is_regulated` →
`conditions_and_exceptions` → `trap_checks` (five explicit booleans) → then
per-candidate `verdicts`. The schema physically walks the model through the
human coder's procedure — this targets the organizers' #1 declared error class,
"answering the wrong core legal question."

Real verdict for s.26(1) (six candidates in one call):

```
core_legal_question_answer:
  "S.26(1) requires organisations to ensure transferred personal data receives
   protection comparable to PDPA standards as a condition of cross-border
   transfer — a conditional flow regime, not an outright ban; s.26(2) confirms
   exemptions are available..."
trap_checks:
  conditional_path_exists: true      ← the P6-I1 killer
  retention_is_minimum:    false
  government_data_only:    false
  provision_in_force:      true
  sectoral_scope:          false

P6-I1 (ban):        applies = FALSE  — "Conditional path exists (comparable-
                    protection requirement + exemptions) — not a per se ban;
                    classified under P6-I4 instead."
P6-I4 (conditional): applies = TRUE, score 1, Horizontal, confidence 0.95,
                    quote byte-grounded ✅
P7-I1 (framework):  applies = TRUE, score 0  — recorded as evidence that a
                    comprehensive DP framework EXISTS (inverted polarity)
others:             applies = FALSE
```

**Counter-example — the retention trap.** PDPA s.25 says personal data must
cease to be retained when no longer necessary. Naively that reads "retention
rule → P7-I3." The mapper's actual output:

> *"S.25 requires organisations to CEASE retaining personal data… — this is a
> maximum/destroy-after rule, not a minimum retention floor."*
> `retention_is_minimum: false` → P7-I3 applies = FALSE.

This is the exact mistake we suspect in the Malaysia baseline (its 7.3 rows),
so the trap doubles as our error-check argument.

## Step 5 — Blind verification: nothing survives on one model's word (S5)

Every fire is re-judged by **Haiku, which never sees Sonnet's reasoning** — only
the provision text and the indicator question. Agreement → verified. Otherwise
one **Opus** tiebreak, majority of the three decides; a 3-way split is flagged
for human review.

Both outcomes, on the same provision:

| Fire | Haiku (blind) | Opus | Outcome |
|---|---|---|---|
| s.26(1) × **P6-I4** (score 1) | agrees | — | ✅ **verified** — final: applies, score 1 |
| s.26(1) × **P7-I1** (evidence, score 0) | disagrees — "s.26(1) is a transfer condition, not framework-scope evidence" | sides with Haiku | ❌ **overturned** — fire removed |

Of the 272 SG fires verified before the credit pause: 152 straight agreements,
57 upheld on tiebreak, **63 overturned** — the panel visibly deleting
false positives before they can reach the CSV. (The P7-I1/I2 overturns are also
by design: those two indicators are *economy-level* — their provision fires are
inputs to Step 6, and only the controlling scope provision reaches the CSV.)

## Step 6–9 — What happens to the verified row next (built 16 Jul)

Continuing the s.26(1) example through the remaining stages:

- **S6 rollup:** P6-I4's Singapore cell takes the max over verified provision
  scores → 1 (this row is the controlling evidence). P7-I1/P7-I2 get six
  dedicated economy-level calls instead (framework-existence questions).
- **S7 NEW/KNOWN:** normalized law match ("Personal Data Protection Act 2012"
  ≈ baseline row) + section root `26` ∈ the baseline's cited articles →
  **KNOWN, matches r1-sg-036** — reproducing the baseline is rewarded, and the
  tag is recorded with its match evidence. A provision with no baseline row in
  its cell (e.g. the 2025 CII Amendment Regs) would tag **NEW** — and every NEW
  row gets a human eyeball before submission.
- **S8:** the same machinery re-checks all 26 Malaysia baseline rows (URL,
  currency, substance) — the two suspect 7.3 rows get full refutations.
- **S9 emit:** one CSV row — Economy=Singapore · Law=PDPA 2012 · s.26(1) ·
  P6-I4 · KNOWN · byte-grounded quote · rationale ≤300 chars · official SSO URL
  · confidence — passing the 13-column validator and the audit-trio gate.

## Why this shape (one paragraph)

Free stages over-collect (recall 1.0 gate), cheap stages screen leniency-first,
the expensive model decides with the full codebook and a schema that forces the
method, a different model checks blind, and deterministic validators own
everything a program can check (byte quotes, URL hosts, column order, closed
vocabularies). Models are only trusted where judgment is genuinely required —
and never alone.
