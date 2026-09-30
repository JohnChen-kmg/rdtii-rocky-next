# RDTII 2.1 Instrument Notes — Pillars 6 & 7 (the human-readable understanding)

**What this is.** The qualitative companion to the machine-readable instrument
(`indicators.yaml`, `policies.yaml`, `signatures/`, `gold/`). Written for the
pitch deck, the reviewer, and future-us. Every claim below is sourced from the
RDTII 2.1 Guide (pp. 60–75), the Round 2 methodology sheet, the Internal Guide
FAQ, or the Assignment 1 answer key — the scoring trees are **triple-attested**.

**Verification note (what is machine-checked and what is not).** The validator
(`scripts/validate_instrument.py`) machine-verifies the mined artifacts (every
gold row and exemplar round-trips against its source workbook cell) and, per
indicator, the `category_official` name + allowed score set against the Round 2
methodology sheet itself. The fuller definition and scoring-tree **prose** was
written from the Guide/FAQ in Round 1, not extracted by script, and spot-checked — it
is not machine-diffed against the PDFs. A disclosed gap beats an undisclosed one.

---

## 1. The nine indicators in one breath each

| ID | Asks | Scores | The one thing to not get wrong |
|---|---|---|---|
| P6-I1 | Transfer banned / must data be processed locally? | 1 / 0.5 / 0 | "Prohibited **unless** conditions" is NOT a ban — it's P6-I4 |
| P6-I2 | Must a **copy** stay in-country (transfer still allowed)? | 1 / 0.5 / 0 | Location, not duration — duration rules are P7-I3 |
| P6-I3 | Must a provider **build/use local infrastructure** to serve? | 1 / 0 | Data-centre *licensing* is 9.4 (out of scope), not 6.3 |
| P6-I4 | Transfer allowed **only if** consent/adequacy/approval? | 1 / 0.5 / 0 | Personal data ⇒ 1 **even if sector-specific** (unlike 6.1/6.2) |
| P7-I1 | **Lack of** comprehensive (horizontal) DP law? | 1 / 0.5 / 0 | INVERTED — a strong PDPA means **0** |
| P7-I2 | **Lack of** dedicated cybersecurity framework? | 1 / 0.5 / 0 | INVERTED — dedicated horizontal act means **0** |
| P7-I3 | Data must be kept **at least** N period? | 1 / 0 | "Not longer than necessary" = maximum rule = **0** |
| P7-I4 | DPO (± DPIA) duty? | 1 / 0.5 / 0 | Advisory DPIA ≠ mandate; contact persons ≠ DPO |
| P7-I5 | Government access **without court order**? | 1 / 0 | Look OUTSIDE privacy law — CPC, surveillance, telecom acts |

Global polarity: **0 = simplified, 1 = heavily regulated.** Pillar-internal
weights (informational): 6.1 38%, 6.2 12%, 6.3 31%, 6.4 12% (+8% for excluded
6.5); 7.1 31%, 7.2 31%, 7.3 16%, 7.4 6%, 7.5 16%.

**6.5 is out of scope** — a non-regulatory, treaty-participation indicator
sourced from TAPED/agreement texts; the workbook header says the tool "is not
required to extract information for these indicators."

## 2. The traps (all encoded as `disambiguation` + `trap_checks`)

1. **Ban vs conditional (6.1 vs 6.4)** — the #1 mis-mapping. Test: does a
   compliant transfer path exist? MY PDPA s.129 reads as a prohibition but has
   an exceptions list → the baseline itself codes it **6.1 = 0, 6.4 = 1**.
2. **Maximum ≠ minimum retention (7.3)** — retention-limitation principles in
   DP laws ("as long as necessary") score **0**. Only "at least N" floors score
   1 (permanent retention counts as a floor). SG PDPA s.25 = 0 is the canonical
   negative.
3. **Government data not scored** — exception on 6.1–6.4 **and 7.3** (per the
   methodology sheet). The DB captures commercial activity.
4. **Inverted polarity (7.1/7.2)** — "Lack of…" indicators; finding a strong
   law means score 0. Never report 1 because evidence was found.
5. **6.4's personal-data asymmetry** — the Guide explicitly scores conditions
   on personal data **1 "regardless of whether horizontal or sector-specific"**,
   while sectoral personal-data measures under 6.1/6.2 sit at 0.5 (AU My Health
   Records = 0.5 precedent). 6.4's category 2 is only non-personal/specific
   data (e.g. Korea's survey-data permission).
6. **Escalation clause scope** — ">1 category-(2) measure ⇒ 1" exists for
   **6.1 and 6.2 only**, never 6.4.
7. **Confidentiality ≠ transfer ban** — bank-secrecy rules (SG Banking Act
   s.47) regulate disclosure, not cross-border movement.
8. **Adjacent roles ≠ DPO (7.4)** — Türkiye's VERBIS contact person, grievance
   officers, local representatives don't satisfy the DPO duty. DPIA-only would
   be a theoretical 0.25 (never observed) → flag for human review, don't emit.

## 3. Where the evidence lives (drives triage + prefilter)

- **P6-I1/I2/I4, P7-I1, P7-I4**: comprehensive DP statutes + sectoral codes
  (banking, communications, health) + tax/companies acts (storage location).
- **P6-I3**: platform/sector measures (ride-hailing, maps, online publishing),
  financial-regulator rules, DP laws' database-location provisions.
- **P7-I2**: dedicated cybersecurity acts; computer-crimes acts are usually
  offence-only predecessors (check which is controlling).
- **P7-I3**: telecom licences & interception acts, tax/companies/employment
  acts, AML/KYC rules — **usually NOT the privacy statute**.
- **P7-I5**: criminal procedure codes, security-offences/surveillance acts,
  intelligence laws, cybersecurity acts' access powers, data-sharing schemes.

This is exactly why act-name filtering alone fails: a third of the relevant
laws are named "Income Tax Act", "Employment Act", "Criminal Procedure Code".

## 4. Operational rules from the answer key (folded into policies.yaml)

- **Recording ≠ controlling.** Sectoral instruments (even regulator Notices)
  are recorded although a horizontal law exists; the horizontal law is the
  *controlling evidence* for the indicator-level score.
- **Currency check.** A canceled Notice recorded as active is wrong evidence —
  record the successor instrument (MAS 1119 → FSM-N16 case).
- **Enforced only.** Pending bills (AU Cyber Security Bill 2024 at baseline
  time) are noted but never scored.
- **Score is a hint.** Zone 3 (final 0/0.5/1) stays with a human; the tool
  emits `score_hint` + the features that drive it.

## 5. Known baseline quirks (gold-set `label_flag`s)

- **Suspect (2)** — prime Malaysia error-check targets (double-weighted
  deliverable): MY 7.3 "PDPA Retention Principle" = 1 and MY 7.3 Communications
  CoP = 1, both maximum-period rules the Guide/FAQ score 0; SG's identical
  pattern was scored 0.
- **Advisory (5)** — AU My Health Records 6.1/6.2 (gov-data tension, but the
  Guide itself cites it as the worked example → 0.5 stands); MY 7.1 sectoral
  CoPs at 0.5 vs SG's Banking Act analog at 0 (baseline-internal
  inconsistency; controlling-evidence rule resolves it); SG telecom-licence 7.3
  row marked "Horizontal" though sectoral.
- Suspect rows are **excluded from few-shot exemplars** (they'd teach the
  trap wrong) but kept, flagged, in the gold set for the error-check and for
  honest recall measurement.

## 6. How the artifacts are consumed

- **P2 (triage)**: `signatures/` keywords + `definition_text` embeddings +
  `exemplar_law_types` score all 2,616 laws; `gold/` laws are a guaranteed-keep
  allowlist and the recall yardstick.
- **P3 (mapping)**: `indicators.yaml` renders into the cached system prompt;
  `disambiguation` entries become schema-forced `trap_checks`; `signatures/`
  exemplars are the few-shot anchors; `policies.yaml` drives edge-case rows and
  deterministic validators; `gold/` seeds NEW/KNOWN and the accuracy eval.
- **Reproducibility**: `scripts/build_gold.py` and `scripts/build_signatures.py`
  regenerate the mined artifacts from the source workbooks;
  `scripts/validate_instrument.py` is the CI gate (9/9 coverage, ≥3 exemplars
  each, gold round-trips 1:1).

*Instrument version 2.1.0 · built 2026-07-12 · sources: RDTII_2.1_guide.pdf,
Round2 methodology sheet, RDTII_2.1_internal_guide.pdf, Assignment 1 answer
key, Round 1 baseline (SG/AU/MY), Round 2 example tabs (7 economies).*

---

## 7. Finale extension — all twelve pillars (draft, 2026-09-13)

**Scope.** The finale template's Indicator Reference lists 62 IDs; 61 are scoreable. 6.5 is
non-regulatory (treaty participation) and declared out of scope. The rest of the non-regulatory set
(1.1-1.3, 2.4, 4.4, 4.7, 4.8, 5.6, 9.2, 12.10-12.13) is not on the list. 3.4, 5.3 and 9.1 are
practice-based: the host allows secondary sources to evidence enforcement (Internal Guide p.8).

**IDs are text, and three differ from the Guide's numbering.** The host writes the Guide's first
pillar-4 indicator (patent application) as `4.01`, its tenth (trade-secrets framework) as `4.1`, and the
Guide's 12.1 (e-commerce equity) as `12.01`. Match Guide sections by name, never by number.

**The host now states its mapping traps** (Indicator Reference rows 79-85), and three of them
tighten Round 1 readings:
- 6.2 is a storage locus, not general record-keeping (row 83).
- 7.1 and 7.2 are economy-level: per-provision citations of the act are not discoveries and score 0 (row 80).
- 7.5 excludes generic inspection of business records and secrecy duties with court-order carve-outs (row 82).
- 7.3 needs a stated number; prescribed periods, notification deadlines and appeal windows do not count (row 81).
- An amending act cited in place of the principal act scores 0 (row 85).
All are encoded in `indicators.yaml` and `policies.yaml` with their row numbers.

**Tiers.** A: the nine pillar 6-7 blocks of the Round 1 codebook. B: drafted 2026-09-13 at Tier A
depth from the Guide, FAQ, methodology sheet and host rows, every rule line cited, not yet reviewed.
C: extracted by script from host text only, no traps; rows mapped under Tier C must say so and clear
a higher NEW threshold (D4). All 61 blocks sit in one file, `indicators.yaml`, in host order; the tier
is a field on each block, and every block is read the same way.

**Gold set.** Every coded host row, all pillars, ten economies. Label flags: `suspect` and `advisory`
(reviewed in Round 1), `host_marked` (the host's own data verification said "Not correct", Thailand
sheet), `candidate` (machine check, unreviewed). `exemplar_for` marks rows used to build retrieval
queries, so an economy's evaluation can exclude them.

**Where the host data is thin** (no clean score-1 row, or none at all): 7.1 and 7.2 (no economy lacks a
framework), 1.4, 3.4, 4.1, 4.2, 4.3, 4.5, 4.6, 5.1, 5.2, 8.1, 11.1, 11.4, 12.4.3, 12.4.6, 12.5, 12.6, 12.9. Rows for 4.2, 4.3 and
4.6 all score 0. One host row (r2-id-035) is tagged 4.1 but describes a patent application (4.01). Drafter notes list rows believed to be
mislabelled; they are review material, not flags.

**Machine-checked vs not.** The validator machine-checks, for all 61: category names and score sets against
the methodology sheet, one scoring branch per score, a citation on every Tier A/B rule line, the Guide
defining sentence verbatim on its printed page (when `RDTII_GUIDE_TEXT` is supplied), exemplar and gold
round-trips. It does not check that a cited page says what the line says; a heuristic citation audit was run,
its listed lines were read, and one wrong page citation was corrected. Its corrected run lists 30 lines.
