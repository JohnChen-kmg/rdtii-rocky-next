# Review items for John (correction cycle, 18–19 Jul)

Accumulating list of judgment calls the pipeline flags for human decision.
Each has the evidence linked; none blocks the draft.

## 1 · SG P6-I2 escalation → 1.0 (baseline says 0) — HEADLINE-OR-CUT
Verified sectoral storage measures found: Companies Act 1967 s.199(3)/(4)
(accounting records kept in Singapore), Insurance Act 1966 s.19/s.94,
Business Trusts Act 2004 s.75(5). Three distinct verified laws × 0.5 →
escalation clause → economy score 1.0, contradicting baseline SG 6.2 = 0.
DECIDE: assert as NEW challenge (with methodology citation for the escalation
clause + these quotes), or classify these as bookkeeping-not-data-storage and
suppress. Check the Guide's 6.2 examples before claiming.

## 2 · SG Banking Act 1970 → P7-I1 not reproduced (baseline r1-sg-039)
RE-CHECKED 16 Jul with two targeted calls on s.47(1): the model split 1–1
(applies=True/Sectoral at conf 0.55, then applies=False) — both times reasoning
"sectoral banking-secrecy complement; PDPA is the controlling framework
(score 0)". Zero score impact either way (sectoral rows are recorded-not-
controlling). DECIDE: include as a recorded-sectoral row with a Note quoting
the model's reasoning (baseline-reproduction friendly), or omit and disclose
the disagreement. Recommendation: include with Note.

## 3 · SG Employment Act 1968 → P7-I3 not reproduced (baseline r1-sg-045)
Mapper correctly found no minimum period in the act's text (s.95 keeps records;
the 2-year minimum lives in the Employment Records Regulations — subsidiary
legislation not in the corpus). DECIDE: add a row citing s.95 with a Note
("minimum period prescribed in subsidiary regulations"), or leave and disclose.

## 4 · Standing items from the SG run
- 2 provisions with unrecoverable schema errors (hand-check at curation).
- 11 ungrounded quotes (locate in source PDF or drop).
- 22 not-in-force flags (QA NotInForce sheet) — confirm exclusion/Notes.
- ~~938 fires pending verification~~ RESOLVED 16 Jul: all 1,210 verified
  (399 overturned); no draft rows carry "verification pending" anymore.

## 5 · P6-I2 escalation → 1.0 in ALL THREE ECONOMIES — THE headline decision
The escalation clause (≥2 verified half-point measures → 1) fires everywhere:
- **SG**: 3 distinct verified laws (item 1 above).
- **MY**: 12 distinct verified laws — tax/records acts requiring records be
  kept in Malaysia (Income Tax Act 1967 s.82, Service Tax Act 2018 s.24,
  Sales Tax Act 2018 s.24, Tourism Tax Act 2017 s.17, Petroleum (Income
  Tax) Act 1967 s.34A, …). Baseline cell max: 0.5 (Services Tax row).
- **AU**: 10 distinct verified laws (same record-localization class).
  Baseline cell: My Health Records at 0.5 (itself advisory-flagged).
ONE judgment call, applied three times: does sectoral bookkeeping/tax-record
localization count as a "data storage measure" for 6.2? Assert all three as
a systematic finding (with the escalation-clause methodology citation and
the verified quotes), or suppress the class everywhere. Check the Guide's
6.2 examples (Türkiye social-network storage, Kazakhstan Art.12(2)) before
deciding — they are about DIGITAL data storage, which cuts toward suppress;
the clause's plain text cuts toward assert. Consistency matters more to the
judges than either answer.

## 6 · MY PDPA s.129 → P6-I4, baseline files it under P6-I2 (r1-my-039/041)
Baseline's two P6-I2 PDPA rows are score-0 context rows ("no strict
localization law…"). Our mapper put s.129(2)–(4) under P6-I4 score 1
(conditional-transfer regime; trap check: conditional path exists), all
verified "agree". Corpus text still shows the pre-A1727 whitelist mechanism
in s.129(2) — check whether the crawled consolidation predates the 1 Jun 2025
amendment commencement (candidate currency finding for the error-check
narrative). Row-level eval counts these as 2 misses; zero score impact.

## 7 · Standing items from the MY run (mapped 16 Jul, batch lane)
- 2 scored rows dropped by the audit-trio gate: `my-pdpgdbn2025-001#st.23`
  (P7-I3) and `#st.14` (P7-I4) — quote re-anchoring onto the doc's 22 thin
  provisions failed AND no section heading could be derived. The doc has a
  good official URL (pdp.gov.my GP_DBN_ENG.pdf, a 2025 premium-NEW
  candidate). MANUAL ANCHOR at curation: read the PDF, cite the paragraph
  numbers, restore the rows. Quotes are in out/audit/index_MY.html.
- 1 provision with an unrecoverable schema error after 6 attempts:
  `my-pdpgdbn2025-001#st.10` (same doc). Hand-check coverage at curation.
- 10 ungrounded quotes (locate in source text or drop).
- Eval misses r1-my-040/046/047/055 cite the two parse_failed 2017 PDP CoPs
  (docs exist upstream but have no extracted provisions) — structurally
  unreachable, disclosed since 15 Jul; the lenient law matcher still counts
  them "resolvable", so MY recall 0.727 UNDERSTATES mapping performance
  (16/18 = 0.889 on truly reachable rows).
- Error-check substance evidence banked: the mapper independently ruled
  PDPA s.10(2) applies=False for P7-I3 with trap check
  retention_is_minimum=False ("maximum-retention/destroy-after rule …
  disqualified per FAQ trap") — the refutation quote for SUSPECT baseline
  row r1-my-053. r1-my-054's CoP is parse_failed → methodological refutation
  (its own quoted text + the banking-CoP-scored-0 contradiction), as planned.

## 9 · AU P6-I1 escalation → 1.0 (was 0.5) — NEW after corpus v2.4 (18 Jul)
The complete CCA 2010 (au-cca2010-002, Part IVE was truncated pre-v2.4)
surfaced a second verified sectoral offshore-access ban — s.57DD(3),
"A person must not do anything that might reasonably enable the sensitive
information to be accessed outside Australia" (civil penalty) — which
escalates alongside My Health Records Act s.77(2) to 1.0. Same
judgment-call family as the three-economy P6-I2 escalation (§5): decide
sectoral-escalation consistently across P6-I1 and P6-I2. Rests on exactly
2 measures; dropping either returns P6-I1 to 0.5. Full evidence:
workflow/DELTA_AU_v2.4_2026-07-18.md.

## 10 · r1-au-041 conflation — NOT fully resolved (correction, see §11)
~~RESOLVED by v2.4~~ — this was premature. v2.4 happened to pick the right
fire; the matcher weakness persisted and the 2026-07-18b delta surfaced the
wrong citation again. Superseded by §11.

## 11 · r1-au-041 P7-I3 KNOWN cites the wrong telecom act — CITATION SWAP
The fuzzy law-matcher treats "Telecommunications Act 1997" and
"Telecommunications (Interception and Access) Act 1979" as identical (both
reduce to the single token "telecommunication", ratio 1.0), so BOTH acts'
P7-I3 fires tag KNOWN→r1-au-041. Curation picked `au-ta1997-002 s.306(3)`
for the single KNOWN slot; the baseline's canonical citation is
`au-ta1979-002 s.187C(1)` (present, KNOWN, verified agree).
- **Score impact: none** (P7-I3 = 1.0 regardless).
- **Not auto-fixed:** the fix is in shared curation logic; changing it risks
  the SG/MY byte-identical negative control the delta task requires.
- **John's call:** swap the r1-au-041 KNOWN row citation to
  `au-ta1979-002 s.187C(1)` (one-line curation edit). A durable fix (curation
  tie-break preferring the closest baseline law-name) is a post-Round-1 item.
Full context: workflow/DELTA_AU_v2.4b_2026-07-18.md.

## 8 · AU run — findings & standing items (mapped + verified 16 Jul)
- **Eval recall 0.889 (8/9), KNOWN-tag accuracy 1.0.** The one miss,
  r1-au-043 (Data Availability and Transparency Act 2022 → P7-I5), is a
  VERIFIER call, not a retrieval gap: both DATA Act fires (s.135, s.16B(4))
  were mapped, then overturned 2-of-3 at tiebreak. DECIDE: include as a
  recorded row with a Note quoting the panel's reasoning
  (baseline-reproduction friendly, mirrors SG item 2), or omit + disclose.
- P6-I1 = 0.5 on 2 verified fires (My Health Records class) — matches the
  baseline's own advisory-flagged precedent.
- 1 scored row dropped by the audit-trio gate: `au-scia2018-001#st.219`
  (P7-I2, SOCI Act synthetic chunk — the known thin-extraction doc). P7-I2
  keeps 3 KNOWN rows regardless; manual-anchor from the SOCI source text
  only if worth it at curation.
- 2 permanent schema errors after 3 passes: `au-sda2004-001#s.27KE(1)`,
  `au-slaa2021-001#s.63AD(4C)` (both surveillance acts — hand-check at
  curation; P7-I5 already scores 1 from many other verified fires).
- 19 ungrounded quotes (locate or drop).
