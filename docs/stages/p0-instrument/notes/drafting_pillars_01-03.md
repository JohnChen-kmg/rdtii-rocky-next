<!-- Drafting notes for pillars 1-3 (1.4, 2.1-2.3, 3.1-3.5). Written 2026-09-13 by a Claude drafting agent working from the host
sources in ../sources/. Checked by the lead for structure (checker, merge, citation audit) but NOT reviewed by a
human. Row IDs: r1-/r2-<economy>-<row> = gold_id in the repo gold set. -->

# g1 notes: pillars 1-3 (1.4, 2.1, 2.2, 2.3, 3.1, 3.2, 3.3, 3.4, 3.5)

Draft 2026-09-13, pending lead and human review. Tier B blocks: 2.1, 2.3, 3.5.

## Conventions, checker status, inputs

- **Citations.** Guide = RDTII 2.1 Guide, printed pages. Internal Guide = PDF pages of `pdftext/internal.txt`
  (FAQ for pillars 1-3 is on p.11). "Hands-on workshop deck p.17" = `pdftext/nikita_handson.txt` PDF page 17
  (ESCAP hands-on workshop, 5 June 2026). "Extraction slides p.9" = `pdftext/slides.txt` PDF page 9.
  Workbook rows are cited as "workbook roundN <sheet> row <row>". Gold ids are given as well.
- **Checker** (`python -X utf8 check_drafts.py g1`): 0 errors, 1 warning. The warning is on purpose:
  the 3.4 `asks` sentence has 68 words. Cutting it to 60 would drop clause (b), the blocking-case test
  that decides score 1, so the whole verbatim sentence is kept.
- **Coordinator correction (assign2.txt).** No g1 file cites the Assignment 2 brief. I re-read the corrected
  file; it covers 6.1, 7.3 and 5.3 only. No change needed.
- **Sources read in full:** guide_pillar_01-03; the sibling sections needed for boundaries (Guide p.37 for 4.9,
  pp.40-44 for 5.2/5.5, p.51 for 6.2, p.72 for 9.4, pp.74-76 for 10.1-10.3, pp.80-81 for 11.4, pp.84-88
  for 12.01/12.2/12.8); guide intro pp.8-12; Internal Guide pp.1-15; non-regulatory note; slides; hands-on
  and canvas decks; all 171 workbook rows for pillars 1-3; sibling rows for 5.2, 12.01, 12.8 and rows in other
  indicators that reuse g1 laws.

### Group-wide observation: what a row score means

Rows are one measure each (format requirements p.4: add rows by the number of measures found). In most pools
the row score is the category of that single measure and the economy score is built from the rows:
1.4 India has four rows at 0.25 (economy total 1.0); 3.4 rows are 0.25 per mechanism and no row is 0.5; a
reviewer note on 3.1 (workbook round2 Indonesia row 26) says the row is 0.5 but the "raw score is 1.00"
across rows. **Exception: 2.3 round2.** All 25 round2 rows are 1, including single local-content rules the
methodology puts at 0.5, while round1 Australia keeps three rows at 0.5. Those round2 rows read like
economy-level totals copied to every row, or like a reading that treats all domestic preferences as
discrimination. The mapping side should not treat 2.3 row scores as per-measure truth.

---

## 1.4 Trade defence measures (anti-dumping, countervailing duties, safeguards) on ICT-related goods

**What it asks.** Whether the economy is enforcing anti-dumping duties, countervailing duties or safeguard
measures against ICT goods and ICT-related goods imported from economies in the considered region (Guide p.16).
It is extracted by the tool: only 1.1-1.3 of pillar 1 are non-regulatory (Non-regulatory note p.1).

**Criteria to scores.** Methodology sheet 1.4 has five categories: more than three measures = 1, three = 0.75,
two = 0.5, one = 0.25, none = 0. The line "(0.25 for each measure, up to 1)" is a counting rule, not a sixth
branch. The Guide says the same (0.25 per measure, four or more = 1, 0 when none is enforced; Guide p.17).
No conflict.

**Scope details.**
- ICT-related goods = finished products and components used to make ICT equipment: electrical connection
  terminals, aluminium alloy strips, power transformers, galvanized steel coils, stainless steel tubes, glass
  fibre materials (Guide p.16).
- Raw materials (rare earths, lithium, cobalt, silicon) are excluded (Guide p.16). The Internal Guide says the
  same and adds that e-waste and used ICT products get no score (Internal Guide p.7).
- Only active measures count. Investigations not yet in force and terminated measures do not (Guide p.16).
- Evidence is measure-level: WTO anti-dumping notifications (G/ADP/N/1), countervailing notifications, gazettes.
  I-TIP and GTA are leads only (Guide p.17). The pipeline has to find customs and trade remedy notices, not
  just statutes.
- FAQ: the ICT product list is WTO ITA I, ITA II and the proposed ITA 3 (ITIF list; HS codes in Guide Annex III
  and ITIF Appendix D) (Internal Guide p.11).

**Trap candidates (not promoted; 1.4 is not Tier B).**
- A trade remedy act or investigating authority with no active ICT measure scores 0: workbook round1 Singapore
  row 3, round2 Lao PDR row 3, round1 Malaysia row 3.
- Raw materials are not scored (Guide p.16; Internal Guide p.7).
- Pending investigations and expired measures are not scored (Guide p.16).
- Products off the ITA / ITIF list, such as the PVC resin in the FAQ, need an HS check (Internal Guide p.11).
- Import bans and import licensing on ICT goods are 10.1 and 10.2 (Guide pp.74-75). Applied tariffs (1.1, 1.2)
  are non-regulatory.

**Exemplars and why.** India row 4 (r2-in-004): the Guide's own PCB example (Guide p.17), 0.25. Russian Federation
row 3 (r2-ru-003): aluminium alloy strips, a component the Guide names, so inputs count. Australia row 3
(r1-au-003): one row, two measures, 0.5, which teaches the counting. China row 3 (r2-cn-003): a measure
extended by expiry reviews is still active. Singapore row 3 (r1-sg-003) and Lao PDR row 3 (r2-la-003):
absence rows where an enabling law exists without an ICT measure. No 0.75 or 1 row exists (totals only).

**Suspect rows (not curated).**
- r2-in-005 (workbook round2 India row 5, 0.25): digital offset printing plates. The row's own reviewer note says
  they are not an ITA product and may be removed. The HS lines (3701, 3704, 3705, 7606, 8442.50) look like
  printing supplies. If removed, India's total drops from 1.0 to 0.75.
- r2-in-006 (round2 India row 6, 0.25): electronic calculators. HS 390720 is listed next to 847010. The reviewer
  note "It should be 0.28" is unexplained (duty rate or score?). Needs clarifying.
- r2-cn-004 (round2 China row 4, 0.25): duty on optical fibre from the European Union and the United States.
  The indicator covers imports from economies in the considered UN region (Guide p.16), but the Guide's own
  examples (Argentina against Germany, Türkiye) show no regional filter. Unclear whether this row counts.
- r2-th-003 (round2 Thailand row 3, 0): says Thailand has trade defence on "steel or steel alloys" but none on
  ICT goods. The Guide counts galvanized steel coils and stainless steel tubes as ICT-related (Guide p.16), so
  some of those steel measures may qualify. Possibly under-scored.
- r2-id-003 (round2 Indonesia row 3, 0): the law column says Reg. 34/M-DAG/PER/6/2014 but also "2011". Fine as
  an absence row, but the instrument citation is inconsistent.

**Disagreements / open questions.**
1. Which list defines "ICT-related goods": the Guide's broad component list (steel coils, tubes, glass fibre;
   Guide p.16) or the ITA-based HS list the FAQ points to (Internal Guide p.11)?
2. Regional filter (see China row 4).
3. Counting unit: the workbook counts one duty on one product against different origins, announced separately,
   as two measures (China rows 3 and 4). The Guide does not define "measure".

---

## 2.1 Foreign exclusions from public procurement (Tier B)

**What it asks.** Measures that exclude foreign enterprises from public procurement, including for ICT goods and
online services (Guide p.19).

**Criteria to scores.** Methodology sheet 2.1: 1 = a legislative measure excludes foreign firms "under any
circumstances", or more than one measure of category 2; 0.5 = excludes a specific (group of) foreign firm(s);
0 = no measure, including when there is only a legal basis to exclude. The Guide matches and lists the forms of
exclusion: closed to foreign firms for certain ICT goods and online services, or a banned list of economies,
groups or companies; foreign firms allowed only when domestic suppliers are absent (Nepal, Bolivia); foreign
firms allowed only in cooperation with domestic firms (Thailand consultants) (Guide p.19).
The FAQ settles "under any circumstances": a rule that lets foreign companies into PPPs only when nationals
cannot meet demand scores 1.0, because it applies to all foreign companies (Internal Guide p.11). The FAQ
answer opens with "Yes" to a question that proposed 0.5 and then says 1.0; I read it as 1.0.

**Trap candidates and sources** (promoted in the block unless marked):
- 2.1 vs 2.3: decide limitation vs exclusion first (Guide p.20). The workbook splits India's orders this way
  (round2 India rows 8, 10, 11 under 2.1; rows 15, 17, 18 under 2.3).
- 2.1 vs 10.1: bans that apply only to government entities (TikTok on ministry devices) may be either; check which
  (Internal Guide p.11). Australia round1 row 5 mentions the TikTok device ban inside its 2.1 text.
- 2.1 vs 2.2: code, trade secret or encryption conditions (Guide pp.19-20).
- Status preferences (Bumiputera) are not foreign exclusions; trade agreement schedules (CPTPP) are not domestic
  law (Hands-on workshop deck p.17; Guide p.20; Internal Guide p.8).
- Not promoted (training material, not codified): Treasury Instructions and Circulars in Malaysia lack force of
  law, so they are recorded but not scored (Hands-on workshop deck p.17).
- Not promoted: teaming rules in tenders are procurement measures, not 3.2 joint venture requirements
  (inference from Guide p.19 listing them under 2.1).

**Exemplars and why.** China row 8 (r2-cn-008): the textbook "domestic unless unavailable" rule, 1. India row 8
(r2-in-008): only local suppliers may bid, coded 1, kept as a flagged boundary (open question 4). Mongolia
row 5 (r2-mn-005): listed goods reserved to domestic makers, 1. Russian Federation row 6 (r2-ru-006): the Guide's messenger example, 0.5. India rows 11 and 10
(r2-in-011, r2-in-010): preference and MSE quota scored 0 here because they are 2.3 limitations; the MSE quota
is the Guide's own 2.3 example (Guide p.20). Thailand row 5 (r2-th-005): construction-only nationality rules not
scored. Singapore row 5 (r1-sg-005): absence row. Six economies.

**Suspect rows (not curated).**
- r2-in-009 (round2 India row 9, 1): GFR Rule 153(iii) only lets the government mandate procurement from
  categories of bidders or grant preferences. Legal basis only, so 0 (Guide p.19; Methodology sheet 2.1).
- r2-ru-005 (round2 Russian Federation row 5, 1): Art. 14 of 44-FZ lets the Government adopt bans. No
  implementing act is cited. Legal basis only, so 0, unless implementing bans are added.
- r2-id-006 (round2 Indonesia row 6, 1): Presidential Instruction 2/2022, 40% of budgets to domestic SME
  products. A quota, so 2.3 (Guide p.20). Already in 2.3 as row 18.
- r2-id-007 (round2 Indonesia row 7, 1): PP 29/2018 domestic-product duty with local-content thresholds and price
  preferences. 2.3 (Guide p.20); duplicated in the 2.3 pool.
- r2-id-008 (round2 Indonesia row 8, 1): Kominfo Reg. 41/2009, local content in telecom operators' network
  capex. Commercial-market local content (10.3; Guide p.75), already recorded as workbook round2 Indonesia row
  134 under 10.3. Not a procurement exclusion.
- r2-id-009 (round2 Indonesia row 9, 1): MoI Reg. 15/2016, 40% domestic content for transmission towers and
  conductors. This is the Guide's own 2.3 example (Guide p.20). Duplicated as 2.3 row 17.
- r2-id-005 (round2 Indonesia row 5, 1): the impact text concludes Indonesia does not exclude foreign firms, yet
  the score is 1. The below-threshold "only if no qualified national firm" rule would justify 1 under the FAQ
  (Internal Guide p.11), but the narrative contradicts the score.
- r1-au-005 (round1 Australia row 5, 0.5): cites government "discretion" plus the 2012 Huawei NBN exclusion,
  the 2018 Huawei/ZTE 5G ban and the 2023 TikTok device ban. If two or more of these count as procurement
  exclusions of specific firms, the Guide gives 1 (Guide p.19). The 5G ban applied to carriers and the TikTok
  ban is the FAQ's 10.1 question, so the correct score is unclear.
- r2-in-012 (round2 India row 12, 0.5): mobile phones may be bought only from local suppliers. This closes one
  ICT product to all non-local suppliers, which the Guide describes as exclusion (Guide p.19), not a specific
  group of firms (0.5). India's total is 1 either way.
- r2-cn-007 (round2 China row 7, 1): MLPS Art. 21, level-3+ systems must use security products from
  Chinese-invested producers with Chinese IP. It binds system operators in general, not only procurement.
  Boundary with pillars 10-11.
- r1-my-005 (round1 Malaysia row 5, 1): the hands-on deck says this should be 1 (international tenders for
  works only when local contractors lack capability). But the rule is about works (construction), and the cited
  sections (6, 13, 15A, 36) do not contain it. Compare Thailand row 5, where construction-only rules are not scored.
- r1-my-007 (round1 Malaysia row 7, 0): Treasury Directive local preference recorded at 0, which fits the
  "record, don't score" teaching. But 2.3 row r1-my-010 scores the same directive 1.

**Disagreements / open questions.**
1. **Teaming rules.** The Guide lists "foreign firms may bid only with a domestic partner" (Thailand consultants)
   as a form of exclusion (Guide p.19) but gives no score for it. The workbook records such rules under 2.3
   (round2 Thailand row 8; round2 Indonesia row 19). I kept the Guide example in `guide_examples` and did not
   write a rule for it.
2. **Scope.** Horizontal procurement laws count (China row 8, Mongolia row 5). Construction-only rules do not
   (Thailand row 5), yet the Malaysia works rule is taught as 1 (Hands-on workshop deck p.17).
3. Round2 Indonesia coded the same instruments under both 2.1 and 2.3.
4. **Eligibility bars defined by local content.** India's order lets only "local suppliers" bid, and a local
   supplier is defined by the local-content share of the offer, not by nationality (workbook round2 India row 8).
   The workbook calls it a 2.1 exclusion (1). But local content is a 2.3 trigger (Guide p.20), and the Guide's
   closest 2.1 example (Nigeria, buy hardware locally; Guide p.19) is not framed by local content either. I dropped
   a draft coding rule that called such bars exclusions; the lead should decide.

---

## 2.2 Specific requirements on source codes, encryption and trade secrets

**What it asks.** (a) whether firms must surrender source code, encryption or other trade secrets, or transfer IP
such as patented technology, as a condition for winning public procurement; (b) whether firms must use a
specific encryption standard to win bids (Guide p.19).

**Criteria to scores.** Methodology sheet 2.2: 1 = surrender patents, source codes or trade secrets as a tender
condition; 0.5 = specific encryption to win tenders; 0 = none. The Guide matches (Guide p.20) and gives the
compliance-cost rationale (Guide p.10). Examples: Egypt (use of encryption needs approval of the telecom
regulator, armed forces and national security bodies), Indonesia (custom software for public electronic systems:
source code to the institution), Kazakhstan (source code and configuration for a government software
register) (Guide pp.19-20). The Egypt example is not procurement-specific as written.
Unlike 2.1 and 2.3, the Guide states no "legal basis only = 0" rule for 2.2; the workbook applies it anyway
(round2 India row 14, IT Act s.84A power with no rules = 0).

**Trap candidates.**
- 2.2 vs 4.9: 4.9 does not cover disclosure tied to public procurement or encryption; those sit in Pillars 2 and
  11 (Guide p.37). The same page cites Indonesia's escrow for custom-made software as a limited-scope example.
  Given the exclusion sentence, the Indonesian procurement measure belongs to 2.2 only.
- 2.2 vs 11.4: deviation from ISO/IEC encryption standards, including disclosure of source code or keys when
  certifying encryption products; encryption registration or licensing goes to pillars 9 or 10 (Guide pp.80-81).
- Duties on the buyer to keep bidders' trade secrets confidential are not surrender requirements (workbook
  round2 Lao PDR row 6).

**Exemplars and why.** Indonesia row 10 (r2-id-010): the Guide's example, 1. Lao PDR row 6 (r2-la-006): a
confidentiality duty, negative. Thailand row 7 (r2-th-007): an IP statute with no tender condition, negative.
Mongolia row 6 and Australia row 6: absence rows. **Thin:** no 0.5 row exists in either workbook, and there are
only two score-1 rows.

**Suspect / open rows.**
- r2-in-013 (round2 India row 13, 1): open-source preference policy for e-government. It is not stated as a
  condition to hand over source code to win tenders, and the row says the documents are policies without
  regulatory structure. The score of 1 needs confirming.
- r2-in-014 (round2 India row 14, 0): the row says patent claims for "Identified Standards" must be royalty-free
  (surrender of patent rights?) yet scores 0. Either explain why it is not a tender condition or re-score.
- r2-cn-009 (round2 China row 9, 0): level-3+ entities must buy encryption products that comply with the
  national encryption authority (GB/T 22239-2019 8.1.9.3). Under the Guide's Egypt example that could be 0.5;
  the row reads it as no tender condition. Open.
- r1-my-009 (round1 Malaysia row 9, 0): Official Secrets Act used as a reference law. Harmless but not relevant.
- r2-ru-007 (round2 Russian Federation row 7, 0): the note mentions Decree 313 and FSB Order 66, which are
  encryption licensing rules. Per Guide p.81 these belong to pillars 9 or 10, not 2.2.

---

## 2.3 Limitations in procurement bidding (Tier B)

**What it asks.** Limitations on participation in public procurement (Guide p.20).

**Criteria to scores.** Methodology sheet 2.3: 1 = a measure that directly discriminates against foreign bidders,
or more than one category-2 measure; 0.5 = a measure applying to all bidders, such as local content requirements
and performance-based conditions; 0 = none, including a bare legal basis. (The sheet has a typo: "measures
measure".) The Guide lists the forms (quota, preference, price preference) and the triggers (nationality; other
status such as SME or indigenous; local content), and gives the two-step test (Guide p.20).
**Guide-only trigger:** the Guide also gives 1 for "absence of institutional transparency" (Guide p.20;
definition also on Guide p.12). The methodology criteria do not include it. It is carried as a coding rule with
both citations.
**Status triggers.** The Guide does not map each trigger to a score. My reading, used in the block: nationality
triggers = direct discrimination (1); local content and performance conditions = all bidders (0.5, methodology);
status set-asides (SME, indigenous) = not nationality-based, so 0.5 per measure. Round1 Australia scores its SME
and Indigenous schemes 0.5; the hands-on deck says Bumiputera preferences also hit domestic firms. Round2 scores
SME schemes 1 (China row 10, India row 17, Russian Federation row 9). India row 17 says "Indian" MSEs, which may
add a nationality element.
**FAQ.** Target price: normal unless it treats domestic and foreign applicants differently (Internal Guide p.11).
The FAQ says such a case "will be considered a restriction and given a score" without the value, so the tree does
not name it; it sits in exceptions.

**Trap candidates.**
- 2.3 vs 2.1 (promoted): "foreign only if no domestic supplier" is the 2.1 exclusion pattern (Guide p.19;
  Internal Guide p.11). Pool rows that look like it: round1 Malaysia row 10 (imports only if local goods cannot
  be obtained), round2 Indonesia row 12 (foreign service firms only if no domestic firm takes part), round2
  Russian Federation row 10 (foreign radio-electronics bids rejected when an EAEU-origin bid exists).
- 2.3 vs 10.3 (promoted): procurement local content stays in Pillar 2; commercial-market local content is 10.3
  (Guide p.75). Kominfo 41/2009 appears under 2.1, 2.3 and 10.3.
- 2.3 vs 6.2 (not promoted): data-storage rules for public-scope electronic system operators (round2 Indonesia
  row 13) are localisation rules. The 6.2 exception excludes government data (Indicator Reference note on 6.2;
  Guide p.51), so recording them as 2.3 may double-dip.
- 2.3 vs 3.5 (not promoted): local incorporation before using state property in PPP projects (round2 Indonesia
  row 14) is a commercial presence condition.
- 2.3 vs 3.2 (not promoted): teaming requirements, see 2.1 open question 1.

**Exemplars and why.** Singapore row 7 (r1-sg-007): national treatment, minister's power = legal basis only, 0.
Australia row 9 (r1-au-009): status-based set-aside, 0.5 (the only clean 0.5). India row 18 (r2-in-018): preference
for India-incorporated firms with Indian IP, 1. Mongolia row 7 (r2-mn-007): several preferences including
Mongolian-owned bidders, 1. Thailand row 10 (r2-th-010): a Thai bidder within 3% beats a cheaper foreign bid,
1. Indonesia row 11 (r2-id-011): domestic companies majority-owned by Indonesians must be involved, 1.
Lao PDR row 7 was dropped: its price margin covers works only, and its goods preference is expressly not
nationality-based.

**Suspect rows (not curated).**
- r2-id-013 (round2 Indonesia row 13, 1): data storage for public ESOs. Not a bidding limitation (see above).
- r2-id-014 (round2 Indonesia row 14, 1): Indonesian company required before using state property in PPPs. The
  row itself calls it a liberalisation. Commercial presence type.
- r2-id-016 (round2 Indonesia row 16, 1): the law column names Kominfo 41/2009 but the impact describes MoI Reg.
  102/2009 (558 sub-sectors). Citation mismatch; the note admits thresholds were not found.
- r2-in-020 (round2 India row 20, 1): the row's note says "may be deleted" and "no allocation of quota, no
  preference", which contradicts the score.
- r2-th-011 (round2 Thailand row 11, 1): the reviewer note says "Not correct".
- r2-in-016 (round2 India row 16, 1): cloud empanelment (data stored in India, Indian law only). Either an
  equal-treatment condition (0.5 per measure) or data localisation (6.2).
- r2-id-017 (round2 Indonesia row 17, 1): the Guide's own 2.3 example (40% local content). A single local-content
  rule is 0.5 per measure, and the impact also pulls in PP 29/2018 Arts. 57-64. Row score cannot be tied to one
  measure.
- r1-my-010 (round1 Malaysia row 10, 1): Treasury Directive, which the deck says lacks force of law; the main
  clause is the 2.1 pattern; the transparency argument rests on secondary sources.
- r2-id-012 and r2-id-015 (round2 Indonesia rows 12 and 15): the same MoI Reg. 02/2014 recorded twice; row 12 is
  the 2.1 pattern.
- r2-ru-010 (round2 Russian Federation row 10, 1): the second-bid rejection rule makes foreign participation depend
  on the absence of EAEU offers. Arguably 2.1.
- r2-th-008 and r2-id-019 (round2 Thailand row 8; round2 Indonesia row 19): teaming duties, which the Guide places
  under 2.1 (Guide p.19).
- r2-cn-010, r2-in-017, r2-ru-009: status-based quotas scored 1 each (see status triggers above).

---

## 3.1 Foreign equity limits in sectors relevant to digital trade

**What it asks.** The maximum foreign equity shares in sectors related to digital trade (Guide p.25).

**Criteria to scores.** Methodology sheet 3.1: 1 = a ban (0%) in at least one sector, or minority-only in more than
one sector; 0.8 = minority stake (1-50%) in one sector; 0.5 = controlling stake (51-99%) allowed, or restrictions
only in SOEs; 0 = full ownership. The Guide matches (Guide p.25) with one wording gap: minority = "less than 50%"
and controlling = "more than 50%", which leaves an exact 50% cap undefined; the methodology puts it under minority.

**Scope.**
- Telecom caps go to 5.2 and e-commerce caps to 12.01 (Indicator Reference note; Guide p.25; Guide p.42; Guide
  p.84). The FAQ calls these "Pillar 5.1 and Pillar 12.1" (Internal Guide p.11). The host IDs are 5.2 and
  12.01, and Internal Guide p.12 itself says 5.2.
- Private firms and SOEs are both covered (Guide p.25; Internal Guide p.11). 12.01 has no SOE metric (Guide p.84).
- Horizontal caps are recorded **only** under 3.1 to avoid double counting (Guide p.25).
- **Broadcasting conflict.** The Guide says broadcasting is not in Pillar 5 and its FDI measures, including equity
  caps, are recorded under Pillar 3 (Guide p.25 fn 9; Guide p.40 fn 27). The FAQ says telecom licensing and foreign
  equity "include broadcasting services, radio frequencies, and VoIP" (Internal Guide p.11). The workbook follows
  the Guide: broadcasting caps are 3.1 rows (round1 Malaysia row 12; round2 Thailand row 15, Indonesia row 25,
  India row 22).
- Sectors: the Guide lists telecom equipment manufacturing, telecom, computer and Internet services (Guide p.24).
  The FAQ says all digital-trade sectors (Internal Guide p.11). The workbook includes media, satellites, fintech,
  banking and trust companies.

**Trap candidates.**
- Telecom network licence caps belong to 5.2: round1 Malaysia row 13 (NFP/NSP 70% cap) duplicates the 5.2 row
  (workbook round1 Malaysia row 32).
- Horizontal SOE caps belong only to 3.1 (Guide p.25), yet the workbook repeats them under 5.2: round2 Indonesia
  row 48, Russian Federation row 36, Thailand row 36, China row 33. **Flag to g2.**
- A mandated local partner is 3.2 (Guide p.25); a digital bank held in partnership with a 99% ceiling appears as
  3.2 (round2 Indonesia row 28).
- Government shareholdings in telecom companies are 5.3 (Internal Guide p.12).
- Government-approval routes above a threshold (India space 74%) may be screening (3.4) rather than a cap.
- Shareholding caps that bind domestic and foreign holders alike are not foreign equity limits (Guide p.25 defines
  foreign equity shares).

**Exemplars and why.** China row 12 (ban, 1); India row 22 (minority caps in several sectors, 1); Thailand row 15
(broadcasting 25%, 0.8, reviewer "Correct", teaches the broadcasting rule); Russian Federation row 12 (media 20%,
0.8); Indonesia row 26 (SOE-only 49% cap, 0.5); Singapore row 9 and Lao PDR row 9 (absence rows). **No clean
"controlling stake allowed" 0.5 row exists** (the 85% caps are coded 0.8).

**Suspect rows (not curated).**
- r1-my-013 (round1 Malaysia row 13, 0.5): telecom NFP/NSP licence cap. Belongs to 5.2 (exception).
- r1-my-014 (round1 Malaysia row 14, 0.8): Trust Companies Act 20% cap binds all shareholders, not only foreign
  ones; the link of trust companies to digital trade is unclear.
- r2-id-022 (round2 Indonesia row 22, 0.5): describes a 49% cap on digital news and media content, which is a
  minority stake (0.8 by the criteria). It also cites 67%/70% caps without naming sectors.
- r2-id-023 (round2 Indonesia row 23, 0.8): e-money 85% cap. A controlling stake is allowed, so 0.5 (Methodology
  sheet 3.1; Guide p.25).
- r2-id-024 (round2 Indonesia row 24, 0.8): P2P lending 85% cap. Same, 0.5.
- r2-th-014 (round2 Thailand row 14, 0.5): reviewer note "Not correct".
- r2-ru-014 (round2 Russian Federation row 14, 0.5): unitary-enterprise law and strategic-enterprise list. No
  foreign equity cap is stated.
- r2-ru-013 (round2 Russian Federation row 13, 0.8): a banking-sector quota on total foreign capital, not a
  per-firm cap; digital-trade relevance unclear.
- r2-in-023 (round2 India row 23, 0.5): 100% allowed, government route above 74%. An approval threshold, not a
  cap.
- r2-th-013 (round2 Thailand row 13, 0): the Foreign Business Act List 3 needs a licence for majority-foreign
  firms in "other services". The row scores 0 because permission or treaty routes allow 100%. The Guide does not
  say whether a licensing route removes a cap.
- r2-id-021 (round2 Indonesia row 21, 0): mixes e-commerce openness (a 12.01 matter) into a 3.1 row.

---

## 3.2 Joint venture requirements

**What it asks.** Whether firms must enter a joint venture with a local firm to invest or operate (Guide p.25).
**Criteria.** Any measure = 1, otherwise 0 (Methodology sheet 3.2; Guide p.25). No conflict.
Guide examples: China VPN joint ventures (50% cap, pilot free trade zones); Egypt trade-sector projects; Liberia
printing, advertising, graphics and commercial artists (Liberian holding at least 25%, capital at least US$
300,000); Vanuatu partnership after more than three expansions (Guide p.25).

**Trap candidates.**
- An equity cap with no mandated partner is 3.1: round1 Malaysia row 15 (caps make joint ventures common, but the
  3.2 score is 0).
- Teaming with domestic firms in tenders is procurement (Guide p.19 lists it under 2.1; the workbook uses 2.3).
- Foreign postal operators must cooperate with local delivery firms: 12.2 (Guide p.84, Indonesia example).
- Local counterpart workers for skills transfer are not joint ventures (round2 Indonesia row 29).
- A law that only defines joint ventures does not require one (round2 Lao PDR row 10).
- The China VPN example combines a joint venture with a 50% cap. Pillar 5 covers value-added telecom services
  (Guide p.40), but the Guide lists VPN among online services for 9.4 (Guide p.71). Whether the cap is 3.1 or
  5.2 is open; the joint venture part stays in 3.2 (Guide p.25).

**Exemplars and why.** China row 14 (the Guide example, 1); Indonesia row 27 (IPTV consortium of at least two
Indonesian entities, 1); Indonesia row 28 (digital bank partnership, 1, boundary with 3.1); Malaysia row 15
(boundary, 0); Indonesia row 29 and Lao PDR row 10 (negatives). **Thin:** only three score-1 rows, two of them
Indonesian.

**Suspect rows.** r2-id-030 (round2 Indonesia row 30, 0) cites the same IPTV Regulation 6/2017 Art. 4 as
r2-id-027 (round2 Indonesia row 27, 1). The criteria say any measure = 1, so row 30 looks like a stale duplicate.
r2-id-028 (row 28) is itself unsure ("no explicit mention of joint venture requirements"). It is kept because
the regulation lets foreigners own a bank only in partnership with Indonesian parties.

---

## 3.3 Nationality or residency requirements for board of directors or managers

**What it asks.** Whether there are nationality or residency requirements for board members or managers (Guide
p.26). The reference name has "for board of directors"; the Guide heading adds "the" and "in sectors relevant
to digital trade".
**Criteria.** Any measure = 1, otherwise 0 (Methodology sheet 3.3; Guide p.26). Examples: Bhutan (ISP local
managers must be citizens), Indonesia (19 positions reserved), Palau, Kiribati and Singapore (one resident
director), Georgia (LLC manager domicile). Footnote: requirements only for officers who are not directors or
managers do not count (Guide p.26 fn 10).

**Trap candidates.**
- Officers who are not directors or managers (company secretaries, chief accountants, interception officers) do
  not count (Guide p.26 fn 10).
- Workforce nationality quotas (for example 75% Russian employees in banks) are my inference: not a director or
  manager rule. No Guide text covers them directly.
- Licence conditions that also require national directors (India broadcasting; Thailand broadcasting s.15, 75%
  Thai directors) can be 9.4 strict-licence conditions too (Guide p.72); record under 3.3 as well (Guide p.11).
- The nationality of shareholders is 3.1.

**Exemplars and why.** Singapore row 11 and Indonesia row 31 (Guide examples); India row 26 (sectoral nationality
rule); Thailand row 17 and Australia row 13 (company-law residency); Russian Federation row 17 (fn 10 boundary,
0); China row 15 (absence row).

**Suspect rows.**
- r2-in-027 (round2 India row 27, 1): single-brand retail conditions. The text has no director or manager rule. The
  30% sourcing rule is the Guide's 10.3 example (Guide p.76), and the store condition is recorded under 3.5
  (round2 India row 31).
- r2-ru-018 (round2 Russian Federation row 18, 1): the row says no official source was found. Unusable until
  sourced.
- Possible gold gaps: Thailand's broadcasting rule (75% Thai directors) is only in 3.1 and 3.5 row text (round2
  Thailand rows 15 and 20). Indonesia's broadcasting ban on foreign managers outside finance and technical roles
  is only in 3.1 (round2 Indonesia row 25). Neither has a 3.3 row.

---

## 3.4 Screening of investment and acquisitions (practice-based)

**What it asks.** (a) any screening mechanism for foreign investment or M&A in digital-trade sectors, excluding
antitrust-only mechanisms unless discriminatory; (b) any case of blocking investment through it (Guide p.26).
**Criteria.** Methodology sheet 3.4: 1 = a case of the mechanism blocking an investment in a digital-trade sector;
0.5 = two or more mechanisms; 0.25 = one mechanism; 0 = none. The Guide matches and says two or more mechanisms are
"capped at 0.5" (Guide p.27).
**Exception.** Antitrust M&A measures are not a restriction unless discriminatory (Indicator Reference note;
Guide p.27).
**Evidence type.** Practice-based: secondary sources may evidence enforcement (Internal Guide p.8). The Extraction
slides say to use primary legal texts for the mechanism and factual materials to show whether it was used "to
block or condition" an investment (Extraction slides p.9). Score 1 needs a block, not a condition (Methodology
sheet 3.4; Guide p.27). So: (i) the instrument creating each mechanism (0.25 each, 0.5 for two or more); (ii) for
1, a documented block in a digital-trade sector (official decision or announcement, or a secondary report).
Guide examples show economic-benefit approvals count too: Armenia, Kiribati, Mexico, New Zealand, Uganda, Vanuatu
(Guide pp.26-27).

**Trap candidates.**
- Competition-law merger review applied to all firms is not scored: round2 Lao PDR row 13 scores it 0.25 against
  the exception.
- Hybrid telecom or media approval regimes (round1 Singapore row 12, Telecom Competition Code acquisition approval;
  round1 Malaysia row 18, MCMC review for competition and national security): the exception needs "solely"
  antitrust, so these need case-by-case review.
- Equity caps and prohibitions are 3.1.
- Approval of licences for foreign-invested telecom firms (round2 China row 16): screening per Guide p.11
  (screening stays in Pillar 3 even in telecom) rather than 5.5.
- A block outside digital-trade sectors does not give 1 (Guide p.27; Internal Guide p.7 on raw materials).
- Sanctions lists (round2 China row 19), post-investment suspension of shareholder rights (round2 Russian
  Federation row 21) and notice-only duties (round1 Australia row 14) are not clearly entry screening. Open.

**Exemplars and why.** China row 18 (IT and internet security review, 0.25); Singapore row 13 (national security
act, 0.25); Russian Federation row 20 (strategic sectors, no reported ICT block, so not 1); Mongolia row 12
(sectoral: foreign state investors in media and communications); Lao PDR row 15 (online activities such as VPN on
the controlled list); Thailand row 18 (Foreign Business Act permission criteria); Indonesia row 32 (the only 0
row). **No score-1 exemplar curated.** Both score-1 rows are doubtful (below). A 0.5 appears only as an economy total.

**Suspect rows.**
- r1-au-015 (round1 Australia row 15, 1): the block cited is a 2024 divestment order in a heavy rare earths
  project, not a digital-trade sector (Guide p.27; Internal Guide p.7). Without it, FATA plus SOCI Act = two
  mechanisms = 0.5.
- r2-in-028 (round2 India row 28, 1): the evidence is a news report of pending approvals, not a documented block.
  It also repeats Press Note 3, which row 29 (r2-in-029) scores 0.25.
- r2-la-013 (round2 Lao PDR row 13, 0.25): competition-law merger review, excluded by the antitrust exception.
- r2-cn-019 (round2 China row 19, 0.25): unreliable entity list, a sanctions tool. The row says no digital-trade
  firm is listed.
- r2-ru-021 (round2 Russian Federation row 21, 0.25): suspension of corporate rights, not entry screening.
- r2-in-030 (round2 India row 30, 0.25): coverage says "E-commerce in food products", but the text is about
  single-brand retail and notes 100% under the automatic route. Internally inconsistent.
- r1-my-017 and r1-my-018 (round1 Malaysia rows 17 and 18, 0.25 each): the note on row 18 calls the two regimes
  "mutually exclusive". Should they count as two mechanisms (economy total 0.5) or one?

---

## 3.5 Commercial presence requirements (Tier B)

**What it asks.** Whether foreign service providers must establish a commercial presence (Guide p.27).
**Criteria.** Any measure = 1, otherwise 0 (Methodology sheet 3.5; Guide p.28). No conflict.
**Scope and boundaries used in the block.** Mode 3 presence (office, branch, subsidiary, representative office);
registration without physical or operational presence excluded (Guide p.27). Commercial presence in telecom stays
in 3.5 (Guide p.11). Strict licences can include commercial presence conditions (Guide p.72). Delivery-firm FDI
measures go to Pillar 3 (Guide p.84). 12.8 vs 3.5 tie-break (Guide pp.87-88).

**Disagreements / ambiguities.**
1. **Guide p.27 wording.** The example list (Colombia, Lao PDR, Malaysia, Pakistan, Kyrgyzstan, Viet Nam) follows
   straight after the sentence that excludes registration-only rules, ending "for example:". Read literally, the
   examples could be of excluded rules. The content (branches, local offices, incorporation, a permanent office)
   and the workbook (Malaysia and Lao PDR examples scored 1 in round1 Malaysia row 20 and round2 Lao PDR row 18)
   show they are covered requirements. The block treats them that way. Please confirm.
2. **"Representative office" is in both definitions:** 3.5 (Guide p.27) and 12.8 ("physical representative
   office", Guide p.87). The block uses the Guide p.88 test: local entity or office = 3.5; administrative contact
   only = 12.8.
3. **Telecom.** The Thailand telecom licence local-incorporation row under 3.5 is struck (r2-th-019). The
   requirement now lives only in 5.5 (round2 Thailand row 39), although Guide p.11 places commercial presence under
   Pillar 3 even for telecom.

**Trap evidence in the workbook.** Singapore Companies Act: 3.5 = 1 (round1 row 14), 12.8 = 0 (round1 row 92).
Australia Corporations Act: 3.5 = 1 (round1 row 16), 12.8 = 0 (round1 row 82). Russia 236-FZ: 3.5 = 1 (round2
row 23), 12.8 = 0 (round2 row 108), 9.1 = 1 (round2 row 72). China internet information services: 3.5 = 1 (round2
row 21), 9.4 = 0.5 (round2 row 89). Thailand foreign satellites: 3.5 = 1 (round2 row 21), 5.5 = 1 (round2 row 40).
**For g7:** round1 Malaysia row 109 scores local incorporation for an application service provider licence as
12.8 = 1. Under the Guide p.88 tie-break, a local entity is commercial presence (3.5).

**Exemplars and why.** Malaysia row 20 and Lao PDR row 18 (the Guide's examples); Russian Federation row 23 (12.8
boundary); Thailand row 21 (sectoral, reviewer "Correct"); Singapore row 14 (registered office, 12.8 boundary);
China row 21 (9.4 boundary); Lao PDR row 16 (absence row). **Thin:** only two score-0 rows, both Lao PDR.

**Suspect rows.**
- r2-ru-022 (round2 Russian Federation row 22, 1): Mass Media Law Art. 54 needs a distribution permit from a
  foreign publisher that has **no** branch. That is a permit, not a duty to set up presence.
- r2-mn-013 (round2 Mongolia row 13, 1): Investment Law Art. 4 registration and Art. 5.1.1, which **permits**
  representative offices or subsidiaries. Looks registration-only (Guide p.27).
- r2-id-033 (round2 Indonesia row 33, 1): an inference from the company-law domicile rule for Indonesian
  companies. The e-commerce regulation named in the law column (PP 80/2019) is not analysed.
- r2-th-022 (round2 Thailand row 22, 1): reviewer note "Not correct" (juristic-person requirement for digital ID
  services).
- r2-la-017 (round2 Lao PDR row 17, 0): says businesses are "typically required" to have a registered entity, yet
  scores 0. Fits only if that is registration without presence. Ambiguous, not curated.
- r2-in-031 (round2 India row 31, 1): the physical-store condition for online single-brand retail fits 3.5. The RBI
  permission for branch offices of certain nationals is an approval rule (3.4 type). Mixed but acceptable.

---

## Top concerns (whole group)

1. **Round2 2.3 scores are not per measure.** All 25 round2 rows are 1, including single local-content rules that
   the methodology places at 0.5, while round1 keeps per-measure 0.5. Gold built from these rows will over-score.
2. **2.1 / 2.3 boundary is inconsistent in the workbook.** Round2 Indonesia codes the same instruments under both,
   including the Guide's own 2.3 example (transmission towers, Guide p.20) as 2.1 = 1. The Guide lists teaming
   duties as 2.1 (Guide p.19); the workbook puts them in 2.3.
3. **"Legal basis only" rows scored 1:** India GFR Rule 153(iii) (2.1), Russia 44-FZ Art. 14 (2.1). The Guide and
   the methodology say 0 (Guide p.19).
4. **Broadcasting equity caps.** The Guide sends them to Pillar 3 (Guide p.25 fn 9, p.40); the Internal Guide FAQ
   puts broadcasting inside telecom (Internal Guide p.11), and also misnumbers the siblings as 5.1 and 12.1. Also:
   a telecom licence cap in 3.1 (round1 Malaysia row 13) and horizontal SOE caps repeated under 5.2 despite the
   no-double-count rule.
5. **3.1 category errors.** 85% caps coded 0.8 (should be 0.5), a 49% cap coded 0.5 (should be 0.8), and a
   non-discriminatory 20% cap treated as a foreign cap. No clean controlling-stake exemplar remains.
6. **3.4 has no trustworthy score-1 row.** Australia's block is in rare earths and India's is pending approvals.
   One competition-law row breaks the antitrust exception. As a practice-based indicator it needs case evidence
   the crawler may not find in statutes.
7. **Guide vs methodology.** 2.3 has a Guide-only transparency trigger for 1. 3.1 has a 50% boundary gap. 1.4 has
   a regional filter and an ICT-related goods list that go beyond the ITA-based FAQ. The 3.5 example list sits
   under the exclusion sentence.
8. **Thin pools.** 2.2 has no 0.5 row and only two score-1 rows (one doubtful). 3.2 has three score-1 rows. 3.5
   has two score-0 rows. 1.4 has no row above 0.5.
