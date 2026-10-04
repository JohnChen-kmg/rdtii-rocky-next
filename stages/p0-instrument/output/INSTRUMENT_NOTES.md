# RDTII 2.1 Instrument Notes (the plain-language understanding)

**What this is.** The qualitative companion to the machine-readable instrument
(`indicators.yaml`, `policies.yaml`, `signatures/`, `gold/`). Written for the
pitch deck, the reviewer, and future-us.

**How it is laid out.** Sections 1 to 6 are the Round 1 notes on pillars 6 and 7, the
nine indicators used in the Round 1 run and the 30 September submission. Section 7
covers the finale's extension to all twelve pillars. Sections 8 to 10 are rebuilt by
`scripts/build_notes.py` from the instrument files and cover every indicator. Every claim below is sourced from the
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

## 1. The nine pillar 6-7 indicators in one breath each

| ID | Asks | Scores | The one thing to not get wrong |
|---|---|---|---|
| 6.1 | Transfer banned / must data be processed locally? | 1 / 0.5 / 0 | "Prohibited **unless** conditions" is NOT a ban — it's 6.4 |
| 6.2 | Must a **copy** stay in-country (transfer still allowed)? | 1 / 0.5 / 0 | Location, not duration — duration rules are 7.3 |
| 6.3 | Must a provider **build/use local infrastructure** to serve? | 1 / 0 | Data-centre *licensing* is 9.4, not 6.3 |
| 6.4 | Transfer allowed **only if** consent/adequacy/approval? | 1 / 0.5 / 0 | Personal data ⇒ 1 **even if sector-specific** (unlike 6.1/6.2) |
| 7.1 | **Lack of** comprehensive (horizontal) DP law? | 1 / 0.5 / 0 | INVERTED — a strong PDPA means **0** |
| 7.2 | **Lack of** dedicated cybersecurity framework? | 1 / 0.5 / 0 | INVERTED — dedicated horizontal act means **0** |
| 7.3 | Data must be kept **at least** N period? | 1 / 0 | "Not longer than necessary" = maximum rule = **0** |
| 7.4 | DPO (± DPIA) duty? | 1 / 0.5 / 0 | Advisory DPIA ≠ mandate; contact persons ≠ DPO |
| 7.5 | Government access **without court order**? | 1 / 0 | Look OUTSIDE privacy law — CPC, surveillance, telecom acts |

Global polarity: **0 = simplified, 1 = heavily regulated.** Pillar-internal
weights (informational): 6.1 38%, 6.2 12%, 6.3 31%, 6.4 12% (+8% for excluded
6.5); 7.1 31%, 7.2 31%, 7.3 16%, 7.4 6%, 7.5 16%.

**6.5 is out of scope** — a non-regulatory, treaty-participation indicator
sourced from TAPED/agreement texts; the workbook header says the tool "is not
required to extract information for these indicators."

## 2. The pillar 6-7 traps (all encoded as `disambiguation` + `trap_checks`)

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

## 3. Where the pillar 6-7 evidence lives (drives triage + prefilter)

- **6.1/6.2/6.4, 7.1, 7.4**: comprehensive DP statutes + sectoral codes
  (banking, communications, health) + tax/companies acts (storage location).
- **6.3**: platform/sector measures (ride-hailing, maps, online publishing),
  financial-regulator rules, DP laws' database-location provisions.
- **7.2**: dedicated cybersecurity acts; computer-crimes acts are usually
  offence-only predecessors (check which is controlling).
- **7.3**: telecom licences & interception acts, tax/companies/employment
  acts, AML/KYC rules — **usually NOT the privacy statute**.
- **7.5**: criminal procedure codes, security-offences/surveillance acts,
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

## 5. Known pillar 6-7 baseline quirks (gold-set `label_flag`s)

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

## 7. Finale extension — all twelve pillars (2026-09-13, deepened 2026-10-04)

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

**Tiers and elements.** A: the nine pillar 6-7 blocks of the Round 1 codebook. B: every other
indicator, 52 blocks, drafted at Tier A depth from the Guide, FAQ, methodology sheet and host rows,
every rule line cited, not yet reviewed and not yet used in a filed run (14 drafted 2026-09-13, 38 on
2026-10-04). C: none at present. All 61 blocks sit in one file, `indicators.yaml`, in host order, and
every block carries the same elements: question, definition, scoring tree, coding rules, exceptions,
disambiguation with TRAP lines, Guide examples, weight, the statement an absence row makes, and its
sources. Blocks answered once per economy say so (`level: economy`, with the framework's name), and
blocks where an absent framework scores 1 say `polarity: inverted`; `policies.yaml` lists both sets.
Each trap is written on both sides: a block that sends a look-alike to a sibling is named back by that
sibling, because a run may load one indicator without the other.

**Two fields for the roll-up** (2026-10-04, decision D17; neither reaches the mapping prompt).
- `absence_score` says what a cell scores when the tool searched and found nothing: 0 on 41 blocks,
  the host's rule for an absence of specific measures (Guide p.12; Internal Guide p.10). It is null,
  meaning the cell stays unscored, on 20 blocks: the 14 inverted ones, where finding nothing would be
  the top score and has to be established; 11.2, where a 0 needs positive evidence that
  self-declaration is allowed; and 1.4, 5.3, 9.1, 11.4 and 12.6, whose answer does not live in the
  legislation the tool searches. Not found in the corpus is not the same as absent in law.
- `count_rule` states, as data, the rule of the 15 blocks that score by how many measures an economy
  has: what is counted, which per-measure scores count, and the thresholds. For 6.1 and 6.2 it is the
  rule the mapping stage used before: two or more distinct half-point measures score 1. Six rules count
  something finer or coarser than a law (sectors in 3.1, cap regimes in 5.2, companies in 5.3, products
  in 10.1 and 10.3, procedures in 10.2); until a verdict records that fact, distinct laws stand in.

**Gold set.** Every coded host row, all pillars, ten economies. Label flags: `suspect` and `advisory`
(reviewed; pillars 6-7 in Round 1, the other pillars while drafting on 2026-10-04 and not confirmed by a
person; `basis` on each flag says which), `host_marked` (the host's own data verification said "Not
correct", Thailand sheet), `candidate` (machine check, unreviewed). `exemplar_for` marks rows used to
build retrieval queries, so an economy's evaluation can exclude them. Section 10 counts the reviewed
flags by indicator.

**Where the host data is thin** (no clean score-1 row, or none at all): 7.1 and 7.2 (no economy lacks a
framework), 1.4, 3.4, 4.1, 4.2, 4.3, 4.5, 4.6, 5.1, 5.2, 8.1, 11.1, 11.4, 12.4.3, 12.4.6, 12.5, 12.6, 12.9. Rows for 4.2, 4.3 and
4.6 all score 0. One host row (r2-id-035) is tagged 4.1 but describes a patent application (4.01). The rows the drafters believed mislabelled are now
reviewed flags (section 10).

**Machine-checked vs not.** The validator machine-checks, for all 61: category names and score sets against
the methodology sheet, one scoring branch per score, a citation on every rule line, the same elements on
every block, the Guide defining sentence verbatim on its printed page (when `RDTII_GUIDE_TEXT` is supplied),
and exemplar and gold round-trips. The drafting checker also confirmed that every cited Guide page and host
row exists and that every Guide example's country is on its cited page. Nothing machine-checks that a cited
page says what the line says: a heuristic citation audit lists the lines worth reading, and no person has
yet read the 52 Tier B blocks.

<!-- BEGIN GENERATED by scripts/build_notes.py: do not edit between the markers -->

## 8. Every indicator in one breath

All 61 in-scope indicators, in host order. Tiers: A 9, B 52. Marks: *inverted* means an absent framework scores 1; *economy* means the indicator is answered once per economy; *practice* means evidence of practice is allowed (Internal Guide p.8).

### Pillar 1: Tariffs and Trade Defence

| ID | Asks | Scores | Marks | The one thing to not get wrong |
| :---- | :---- | :---- | :---- | :---- |
| 1.4 | Are anti-dumping, countervailing or safeguard measures in force on ICT or ICT-related goods, and how many? | 1 / 0.75 / 0.5 / 0.25 / 0 | tier B | A trade remedy law or a pending investigation is not a measure; count only active duties, 0.25 each |

### Pillar 2: Public Procurement

| ID | Asks | Scores | Marks | The one thing to not get wrong |
| :---- | :---- | :---- | :---- | :---- |
| 2.1 | Are foreign firms, or specific foreign firms, barred from public procurement of ICT goods or services? | 1 / 0.5 / 0 | tier B | Quotas, preferences and local-content conditions are 2.3; a power to exclude with no implementing ban scores 0 |
| 2.2 | Must bidders surrender source code, trade secrets or patents, or use a specific encryption standard? | 1 / 0.5 / 0 | tier B | Only tender conditions count; disclosure to government outside procurement is 4.9 and market-wide encryption rules are 11.4 |
| 2.3 | Do quotas, supplier preferences or price preferences limit bidding, and do they discriminate against foreign bidders? | 1 / 0.5 / 0 | tier B | Foreign bidders admitted only when no domestic supplier exists is exclusion (2.1), not a limitation |

### Pillar 3: Foreign Direct Investment

| ID | Asks | Scores | Marks | The one thing to not get wrong |
| :---- | :---- | :---- | :---- | :---- |
| 3.1 | What maximum foreign equity share is allowed in digital-trade sectors other than telecom and e-commerce? | 1 / 0.8 / 0.5 / 0 | tier B | Telecom caps are 5.2 and e-commerce caps are 12.01; approval above a threshold is screening (3.4), not a cap |
| 3.2 | Must foreign firms form a joint venture with a local partner to invest or operate? | 1 / 0 | tier B | An equity cap that merely makes a local partner convenient is 3.1; 3.2 needs a mandated partner |
| 3.3 | Must any director or manager be a national or resident of the economy? | 1 / 0 | tier B | Officers who are not directors or managers do not count; shareholder nationality rules are 3.1 |
| 3.4 | Is foreign investment screened in digital-trade sectors, by how many mechanisms, and was any investment blocked? | 1 / 0.5 / 0.25 / 0 | tier B, practice | Score 1 needs a documented block in a digital-trade sector; antitrust merger review is not screening |
| 3.5 | Must foreign providers set up a local branch, subsidiary or office to supply services? | 1 / 0 | tier B | Appointing a local agent or representative for remote supply is 12.8; registration without presence is not scored |

### Pillar 4: Intellectual Property Rights

| ID | Asks | Scores | Marks | The one thing to not get wrong |
| :---- | :---- | :---- | :---- | :---- |
| 4.01 | Is the patent application process restricted, and by what type of rule? | 1 / 0.5 / 0 | tier B | Host ID 4.01 is patent applications; 4.1 is trade secrets. A local agent for filing scores 1. |
| 4.2 | Does patent law lack civil or administrative procedures and remedies, or provisional measures? | 1 / 0.5 / 0 | tier B, inverted, economy | Inverted: remedies and interim orders found mean 0. Provisional protection of a published application is not a provisional measure. |
| 4.3 | Does any law restrict patent enforcement, horizontally or in specific cases? | 1 / 0.5 / 0 | tier B | TRIPS-consistent compulsory licences and government use with remuneration are not restrictions; score 0. |
| 4.5 | Does the economy lack a copyright framework or clear fair use or fair dealing exceptions? | 1 / 0.5 / 0 | tier B, inverted, economy | Inverted: fair use or fair dealing scores 0; a closed list with no fairness test scores 0.5. |
| 4.6 | Does copyright law lack civil or administrative procedures and remedies, or provisional measures? | 1 / 0.5 / 0 | tier B, inverted, economy | Inverted and de jure: remedies found mean 0; piracy statistics do not raise the score. Safe harbour is 8.1. |
| 4.9 | Must firms disclose trade secrets, source code or algorithms to the Government without safeguards? | 1 / 0.5 / 0 | tier B | Procurement source-code duties are 2.2, encryption certification is 11.4, and a law protecting trade secrets is 4.1. |
| 4.1 | Does the economy lack a legal framework that effectively protects trade secrets? | 1 / 0.5 / 0 | tier B, inverted, economy | Inverted: protection found means 0. Host ID 4.1 is trade secrets, not patent applications (4.01). |

### Pillar 5: Telecom Regulations & Competition

| ID | Asks | Scores | Marks | The one thing to not get wrong |
| :---- | :---- | :---- | :---- | :---- |
| 5.1 | Does the economy lack an obligation to share passive telecom infrastructure (towers, ducts, poles)? | 1 / 0.5 / 0 | tier B, inverted, economy | Inverted: a sharing mandate means 0; sharing only permitted or practised is 0.5. Answered once per economy |
| 5.2 | How much of a telecom company may foreign investors own under telecom-specific rules? | 1 / 0.8 / 0.5 / 0 | tier B | Telecom-specific caps only: horizontal and broadcasting caps are 3.1, e-commerce caps 12.01, approval thresholds 3.4 |
| 5.3 | Does the Government hold shares in telecom companies, and how large are the holdings? | 1 / 0.5 / 0 | tier B, practice | Ownership facts, not a legal provision or a foreign equity cap (5.2); any holding above 50% scores 1 |
| 5.4 | Does the economy lack accounting and functional separation duties for dominant telecom operators? | 1 / 0.5 / 0.25 / 0 | tier B, inverted, economy | Inverted, four levels: both mandates 0, functional only 0.25, accounting only 0.5, neither 1. Answered once per economy |
| 5.5 | Do telecom operator licences carry discriminatory conditions or significant entry barriers? | 1 / 0 | tier B | A licence alone is not scored; ISP, content and broadcasting licences are 9.4, e-commerce licences 12.3 |
| 5.7 | Does the economy lack a telecom regulator independent of operators and the Government? | 1 / 0 | tier B, inverted, economy | Inverted: an independent regulator means 0. Government appointment of its members alone does not fail the test |

### Pillar 6: Cross-border Data Policies

| ID | Asks | Scores | Marks | The one thing to not get wrong |
| :---- | :---- | :---- | :---- | :---- |
| 6.1 | Is transfer banned, or must data be processed locally? | 1 / 0.5 / 0 | tier A | "Prohibited unless conditions" is not a ban; it is 6.4 |
| 6.2 | Must a copy stay in-country (transfer still allowed)? | 1 / 0.5 / 0 | tier A | Location, not duration or general record-keeping; duration rules are 7.3 |
| 6.3 | Must a provider build or use local infrastructure to serve? | 1 / 0 | tier A | Data-centre licensing is 9.4, not 6.3 |
| 6.4 | Is transfer allowed only on consent, adequacy or approval? | 1 / 0.5 / 0 | tier A | Personal data scores 1 even if sector-specific, unlike 6.1 and 6.2 |

### Pillar 7: Domestic Data Protection & Privacy

| ID | Asks | Scores | Marks | The one thing to not get wrong |
| :---- | :---- | :---- | :---- | :---- |
| 7.1 | Does the economy lack a comprehensive (horizontal) data protection law? | 1 / 0.5 / 0 | tier A, inverted, economy | Inverted: a strong data protection act means 0. Answered once per economy |
| 7.2 | Does the economy lack a dedicated cybersecurity framework? | 1 / 0.5 / 0 | tier A, inverted, economy | Inverted: a dedicated horizontal act means 0. Answered once per economy |
| 7.3 | Must data be kept for at least a stated period? | 1 / 0 | tier A | "Not longer than necessary" is a maximum rule and scores 0 |
| 7.4 | Is there a duty to appoint a DPO or carry out a DPIA? | 1 / 0.5 / 0 | tier A | An advisory DPIA is not a mandate; contact persons are not a DPO |
| 7.5 | Can the government access personal data without a court order? | 1 / 0 | tier A | Look outside privacy law: criminal procedure, surveillance and telecom acts |

### Pillar 8: Internet Intermediary Liability

| ID | Asks | Scores | Marks | The one thing to not get wrong |
| :---- | :---- | :---- | :---- | :---- |
| 8.1 | Does the economy lack a safe harbour for intermediaries against users' copyright infringement? | 1 / 0.5 / 0 | tier B, inverted, economy | Inverted and economy-level: a shield found means 0 or 0.5; a general shield silent on copyright still counts |
| 8.2 | Does the economy lack a safe harbour for users' illegal content other than copyright? | 1 / 0.5 / 0 | tier B, inverted, economy | Inverted; a copyright-only shield is 8.1 evidence, and a removal duty with no exemption is 8.4 |
| 8.3 | Must intermediaries verify users' identity for Internet access, online services or SIM registration? | 1 / 0.5 / 0 | tier B | Keeping identity or traffic records for a set period is 7.3; government access to them is 7.5 |
| 8.4 | Must intermediaries monitor users' activity, or remove or block illegal content? | 1 / 0.5 / 0 | tier B | Interception and data-access duties for agencies are 7.5; removal duties triggered by a notice still count here |

### Pillar 9: Content Access

| ID | Asks | Scores | Marks | The one thing to not get wrong |
| :---- | :---- | :---- | :---- | :---- |
| 9.1 | Has the Government blocked or filtered commercial websites, or required intermediaries to do so? | 1 / 0.5 / 0 | tier B, practice | Political, criminal, age-restricted, defamatory and copyright-infringing content is not scored; shutdowns are 9.2 and never extracted |
| 9.3 | Does a rule limit online advertising, beyond truthfulness and product health or safety rules? | 1 / 0 | tier B | Bans on misleading ads are consumer protection, scored 0 here; that law is 12.9 evidence |
| 9.4 | Must online content providers or applications hold a licence, and is the licence strict? | 1 / 0.5 / 0 | tier B | Telecom operator licences are 5.5 and e-commerce licences 12.3; registration or notification alone scores 0 |

### Pillar 10: Non-technical NTMs

| ID | Asks | Scores | Marks | The one thing to not get wrong |
| :---- | :---- | :---- | :---- | :---- |
| 10.1 | Is the import of an ICT good or online service prohibited outright? | 1 / 0.5 / 0 | tier B | A prohibition lifted by a permit or licence is 10.2; a government-only ban is checked against 2.1. |
| 10.2 | Do quotas, licences, permits, registration or labelling restrict imports of ICT goods or online services? | 1 / 0.5 / 0 | tier B | Count the measures: one cost-adding measure is 0.5; two or more, or any quota, is 1. |
| 10.3 | Must ICT goods or online services for the commercial market contain a domestic share? | 1 / 0.5 / 0 | tier B | Local content rules in public procurement tenders are 2.3, not 10.3. |
| 10.4 | Is the export of ICT goods or online services banned, licensed or otherwise limited? | 1 / 0 | tier B | Dual-use export licensing that covers ICT items scores 1; raw-material export controls score 0. |

### Pillar 11: Standards and Procedures

| ID | Asks | Scores | Marks | The one thing to not get wrong |
| :---- | :---- | :---- | :---- | :---- |
| 11.1 | Are foreigners barred from standard-setting, or are standards made without public consultation? | 1 / 0 | tier B, inverted, economy | Inverted and economy-level: an open, consulted standards process scores 0; exclusion or opacity scores 1. |
| 11.2 | Can foreign suppliers self-certify conformity, or at least use foreign conformity assessment bodies? | 1 / 0.5 / 0 | tier B | The certification route is 11.2 and extra testing is 11.3; MRA members score 0.5 or less. |
| 11.3 | Must ICT products be screened or tested domestically before entering the market? | 1 / 0.5 / 0 | tier B | Accepting third-party test results gives 0.5; testing only by in-country designated labs gives 1. |
| 11.4 | Does any measure require encryption that deviates from ISO/IEC standards? | 1 / 0 | tier B | Licensing or registering encryption products is not a deviation; it belongs to 10.2, 10.4 or 9.4. |

### Pillar 12: Online Sales and Transactions

| ID | Asks | Scores | Marks | The one thing to not get wrong |
| :---- | :---- | :---- | :---- | :---- |
| 12.01 | Is foreign ownership of e-commerce businesses capped, and at a minority or a controlling stake? | 1 / 0.5 / 0 | tier B | Caps in other sectors are 3.1 and telecom caps 5.2; a horizontal cap is 3.1 only |
| 12.2 | Does any measure limit online purchases or the delivery of products bought online? | 1 / 0 | tier B | Alcohol, tobacco and pharmaceutical limits, taxes and duties are not scored; de minimis is 12.5 |
| 12.3 | Must an e-commerce business hold a licence to operate? | 1 / 0 | tier B | Payment-service licences are 12.4.4 and delivery licences are out; platform licences reaching social media also go to 9.4 |
| 12.4.1 | Is a local bank account required for online payments? | 1 / 0 | tier B | Domestic processing of payments is 6.1 and local incorporation of the provider is 12.4.4 |
| 12.4.2 | Is the currency of international payments prescribed by law? | 1 / 0 | tier B | A domestic legal-tender rule that exempts international trade does not score |
| 12.4.3 | Does a mandatory national payment-security standard deviate from international standards? | 1 / 0 | tier B | A standard based on ISO/IEC or PCI DSS scores 0; general encryption mandates are 11.4 |
| 12.4.4 | Does a payment-service licence carry restrictive conditions such as local incorporation or nationality? | 1 / 0 | tier B | A payment licence with only prudential conditions scores 0; an e-commerce business licence is 12.3 |
| 12.4.5 | Is the amount payable or holdable through electronic payment methods capped? | 1 / 0 | tier B | AML reporting thresholds are not ceilings; purchase quotas are 12.2 and de minimis is 12.5 |
| 12.4.6 | Must online payments pass through a specific, designated intermediary? | 1 / 0 | tier B | A duty to use licensed providers is not a mandated intermediary; authorisation rules are 12.4.4 |
| 12.4.7 | Is there any payment restriction that fits none of the six listed types? | 1 / 0 | tier B | Use last: ceilings are 12.4.5 and licence conditions 12.4.4; safeguards and AML duties score 0 |
| 12.5 | Is there a duty-free value threshold for imported goods, and is it below USD 200? | 1 / 0.5 / 0 | tier B, inverted | Inverted: no de minimis rule scores 1; a rule found scores 0.5 or 0 by USD value |
| 12.6 | Are customs duties charged, or legally possible, on digital products delivered electronically? | 1 / 0.5 / 0 | tier B | A tariff line at a zero rate is a legal mechanism and scores 0.5, not 0 |
| 12.7 | Must firms use a local domain name, or meet presence or representative conditions to register one? | 1 / 0.5 / 0 | tier B | A representative for supplying services, not tied to a domain, is 12.8 |
| 12.8 | Must a foreign online provider appoint a local representative, agent or contact point to serve remotely? | 1 / 0 | tier B | A duty to set up a branch, subsidiary or company is commercial presence, 3.5 |
| 12.9 | Does the economy lack a consumer protection law that applies to online purchases? | 1 / 0 | tier B, inverted, economy | Inverted: a consumer protection law found means 0; only its absence scores 1 |

## 9. Where the evidence lives, by pillar

The kinds of law each pillar's measures are found in. This is what triage and the prefilter have to
reach; an act's name alone rarely says which indicator it carries.

- **Pillar 1: Tariffs and Trade Defence.** Active duty orders, not statutes: WTO anti-dumping and countervailing notifications and official gazette notices of the responsible ministry. The customs or trade remedy act is only the legal basis, cited as the reference when no measure on ICT goods is in force (Guide p.17; Guide p.12).
- **Pillar 2: Public Procurement.** Public procurement acts and their implementing regulations, procurement orders and manuals, domestic-product and local-content rules for government purchasing, and rules on software or electronic systems supplied to public bodies. Where no restriction exists the procurement act is the reference law (Guide pp.18-20; Guide p.12).
- **Pillar 3: Foreign Direct Investment.** Laws governing companies, foreign investment laws and investment lists, and sectoral laws such as telecommunications, broadcasting and media statutes. Blocking cases for investment screening come from official decisions and, as practice evidence, secondary reports (Guide p.24; Internal Guide p.8).
- **Pillar 4: Intellectual Property Rights.** Patent, copyright and trade secret acts or a single intellectual property code, with their implementing regulations; general laws such as civil codes and civil procedure codes for remedies and interim orders; case law for common-law trade secret protection; and communications, cybersecurity or national security laws for disclosure mandates (Guide pp.30-31; Guide p.34; Guide pp.37-38).
- **Pillar 5: Telecom Regulations & Competition.** Telecommunications acts and their implementing regulations; regulator codes, notifications and determinations on access, sharing (5.1) and accounting separation (5.4); licensing rules and licence conditions (5.5); investment lists and telecom FDI policy (5.2); the act establishing the regulator (5.7); market reports, SOE lists and company records for 5.3 (Guide p.43; Internal Guide pp.12-13).
- **Pillar 6: Cross-border Data Policies.** comprehensive data-protection statutes AND sectoral laws for health, finance (credit-card information) and telecommunications (computer traffic data). (Guide p.49)
- **Pillar 7: Domestic Data Protection & Privacy.** data-protection statutes, cybersecurity acts, AND NON-privacy laws (criminal procedure, surveillance/interception, telecom, AML/financial, tax/corporate record-keeping). (Guide pp.57-62; Extraction slides p.47)
- **Pillar 8: Internet Intermediary Liability.** Copyright acts and civil codes, e-commerce, electronic-transactions and IT acts, telecommunications and ICT laws, SIM-registration and real-name rules, cybercrime laws, and online-safety, platform and content-code regulations (Guide pp.64-67; 8.1 workbook round2 Russian Federation row 60; 8.2 workbook round1 Singapore row 50; 8.4 workbook round1 Singapore row 55).
- **Pillar 9: Content Access.** Information-technology, cybercrime, broadcasting and media acts with blocking powers, electronic-system and platform regulations, government blocking orders, advertising laws and content codes, and licensing rules for news, broadcasting, social media, VPN, cloud and data-centre services. Internet shutdowns (9.2) come from V-Dem and are not extracted (Guide pp.69-72; Internal Guide p.14).
- **Pillar 10: Non-technical NTMs.** Customs acts and prohibited or restricted goods orders, import and export licensing regulations and notifications, strategic and dual-use control lists, telecom and radio equipment import rules, ministry regulations setting domestic-content thresholds, and government orders banning named applications (Guide pp.74-76).
- **Pillar 11: Standards and Procedures.** Standardization and conformity assessment laws, procedures of national standards bodies and telecom regulators, type-approval and certification regulations for telecom and radio equipment, mutual recognition arrangements, security review rules for network products, and cryptography laws or regulator directions on encryption (Guide pp.78-81; Internal Guide p.14).
- **Pillar 12: Online Sales and Transactions.** E-commerce laws and decrees; foreign investment policies and negative lists; postal and courier rules; central bank rules on payment systems, electronic money and foreign exchange; customs rules on low-value imports and electronic transmissions; domain name registry rules; rules on local representatives of online service providers; consumer protection laws (Guide pp.83-88).

## 10. Reviewed label flags, all pillars

215 host rows carry a reviewed flag: 208 from drafting_review_2026-10-04, 7 from round1_review.
A *suspect* row contradicts an explicit host rule or is filed under the wrong indicator, and is never
used as an exemplar. An *advisory* row is defensible but rests on a judgement. The reasons are in
`gold/gold_set.jsonl` (`label_flag.reason`). Flags outside pillars 6-7 were set while drafting and
have not been confirmed by a person.

| Indicator | Suspect | Advisory |
| :---- | ----: | ----: |
| 1.4 | 0 | 2 |
| 2.1 | 5 | 6 |
| 2.2 | 0 | 3 |
| 2.3 | 0 | 14 |
| 3.1 | 5 | 4 |
| 3.2 | 1 | 1 |
| 3.3 | 1 | 1 |
| 3.4 | 3 | 5 |
| 3.5 | 1 | 3 |
| 4.01 | 1 | 2 |
| 4.3 | 0 | 1 |
| 4.5 | 0 | 2 |
| 4.6 | 0 | 1 |
| 4.9 | 0 | 2 |
| 4.1 | 1 | 3 |
| 5.1 | 2 | 2 |
| 5.2 | 0 | 3 |
| 5.3 | 1 | 0 |
| 5.4 | 1 | 1 |
| 5.5 | 0 | 3 |
| 5.7 | 1 | 2 |
| 6.1 | 0 | 1 |
| 6.2 | 0 | 1 |
| 7.1 | 0 | 2 |
| 7.3 | 2 | 1 |
| 8.1 | 2 | 5 |
| 8.2 | 2 | 5 |
| 8.3 | 0 | 4 |
| 8.4 | 4 | 6 |
| 9.1 | 3 | 7 |
| 9.3 | 0 | 6 |
| 9.4 | 1 | 11 |
| 10.1 | 0 | 3 |
| 10.2 | 0 | 6 |
| 10.3 | 0 | 4 |
| 10.4 | 1 | 0 |
| 11.1 | 0 | 2 |
| 11.2 | 0 | 4 |
| 11.3 | 1 | 4 |
| 11.4 | 0 | 1 |
| 12.01 | 0 | 1 |
| 12.2 | 0 | 1 |
| 12.3 | 0 | 3 |
| 12.4.1 | 1 | 3 |
| 12.4.2 | 1 | 3 |
| 12.4.4 | 2 | 2 |
| 12.4.5 | 0 | 2 |
| 12.4.6 | 1 | 1 |
| 12.4.7 | 0 | 3 |
| 12.5 | 2 | 1 |
| 12.6 | 1 | 0 |
| 12.7 | 2 | 3 |
| 12.8 | 2 | 1 |
| 12.9 | 2 | 4 |

<!-- END GENERATED -->
