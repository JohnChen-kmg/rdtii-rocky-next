<!-- Drafting notes for pillar 8 (8.1-8.4). Written 2026-09-13 by a Claude drafting agent working from the host
sources in ../sources/. Checked by the lead for structure (checker, merge, citation audit) but NOT reviewed by a
human. Row IDs: r1-/r2-<economy>-<row> = gold_id in the repo gold set. -->

# g3 notes: Pillar 8, Internet intermediary liability (8.1, 8.2, 8.3, 8.4)

Draft 2026-09-13 for lead review. All four IDs are Tier B. Files: `guide_refs.yaml`, `signatures_spec.yaml`,
`curated.yaml`, `codebook_tierB.yaml`, this file.

## Sources read

- Guide pp.64-68 (Pillar 8). For comparison: pp.57-63 (Pillar 7), pp.69-72 (Pillar 9), p.34 (4.6), pp.83-84 (Pillar 12 list, 12.7).
  Also pp.10-12: scoring conditions, cross-cutting measures, lack of measures.
- Internal Guide pp.8 (practice-based list), 10 (scoring), 11 (one measure under several sub-pillars), 13 (FAQ 8.4).
- Methodology rows 41-44 (the same in the round 1 and round 2 DBs). Indicator Reference rows 44-47: no exception note for any Pillar 8 ID.
- All 80 Pillar 8 workbook rows (none struck), plus sibling rows in 4.6, 7.3, 7.4, 7.5, 9.1, 12.3, 12.7 and 12.9 that reuse the same instruments.
- Training texts (slides, answer key, Nikita and Juntong decks, QA, WITADA overview) have no Pillar 8 content. The corrected
  `assign2.txt` (Assignment 2 brief) covers only 6.1, 7.3 and 5.3, and nothing in these drafts cites it.

ID matching: the host names for 8.1-8.4 match the Guide's four headings in order (Guide p.64 list). There is no numbering
hazard. Only typo: the reference and methodology sheets both read "User identify requirements" for 8.3. `category_official`
keeps the typo (exact text); `name` fixes it.

| ID | Rows (R1/R2) | Scores in pool | Economies |
| :-- | :-- | :-- | :-- |
| 8.1 | 14 (3/11) | 0 x11, 0.5 x2, 1 x1 | AU CN ID IN LA MN MY RU SG TH |
| 8.2 | 15 (5/10) | 0 x8, 0.5 x2, 1 x5 | same 10 |
| 8.3 | 22 (3/19) | 1 x11, 0.5 x10, 0 x1 | same 10 |
| 8.4 | 29 (9/20) | 1 x20, 0 x9, 0.5 x0 | same 10 |

`scoring_features` is empty for all four because the Guide lists no scoring features for this pillar. `exceptions` is empty
for all four because neither the Guide nor the Indicator Reference states an exception.

---

## 8.1 Lack of safe harbour for copyright infringements

**What it asks.** Whether an economy has a safe harbour provision for copyright infringement. A safe harbour protects
intermediaries (ISPs and Internet content providers) from liability for certain activities of their users. Without one, they
are liable per se even when unaware of the content (Guide p.64).

**Criteria to scores.** Methodology 8.1 has three categories. (1) No intermediary liability framework scores 1. (2) A sectoral
framework that limits liability scores 0.50. (3) A horizontal framework that limits liability scores 0. Possible scores are
written "1 / 0.50 / 0", encoded as `[1, 0.5, 0]`. Guide p.65 gives the same three levels.
- TRAP, inverted polarity: 1 means the shield is missing. Guide p.10 lists safe-harbour provisions among the norms whose absence
  pushes a score towards 1. Internal Guide p.10 (condition 3) says the same for a missing legal mechanism.
- Wording gap: the Guide's 0 is a horizontal framework that "fully protects"; the methodology's 0 is one that "limits
  liability". Every Guide example is conditional (below), so "fully" cannot mean unconditional immunity. I read it as "across
  all sectors". This is an inference; see Top concerns.
- Methodology typos: "liablity", "Hoirzontal".

**How the Guide separates the cases (the brief's leads, checked against the Guide text).**
- *Sector-specific vs horizontal.* Guide p.65: the shield "can take various forms under sector-specific laws" (examples:
  telecommunications or e-commerce service providers) or applies across all sectors. Footnote 40 gives the sector-specific
  example: Georgia's Law on E-commerce. The Guide never scores its NZ, Japan or Korea examples, and never says whether a
  copyright act (every sector, but copyright only) counts as horizontal.
  - Workbook practice: copyright acts, civil codes and IT acts are scored 0 as horizontal (SG 49, RU 60, TH 72, CN 72, IN 103,
    ID 96, AU 47). E-commerce regulations are scored 0.5 as sectoral (ID 95). `scope_patterns` follows that practice; it is
    workbook-derived, not Guide-stated.
- *Notice-based conditions.* All four Guide examples attach conditions, so conditions do not cancel a safe harbour:
  - New Zealand: no specific knowledge, or prompt removal on notice.
  - Japan: unless aware, or with good reason to be aware.
  - Korea: listed requirements.
  - Georgia: did not initiate or alter, no actual knowledge, prompt removal (Guide p.65, footnote 40).
- *8.1 vs 8.2.* Guide p.65 lists three forms:
  - Separate laws: NZ copyright amendment act for copyright, NZ Harmful Digital Communications Act for other content (p.66).
  - One law covering both: Japan Act No.137 of 2001, used in both sections.
  - Copyright only: Korea's Copyright Act, with "no safe harbour regime for other activities".
  Footnote 40 adds that a general exemption silent on copyright "remains applicable" to it. Footnote 41, the 8.2 copy, drops that
  sentence. So: one law covering both is evidence for both IDs; a copyright-only law answers 8.1 only; a general law silent on
  copyright still answers 8.1.

**Confusions (sourced; codebook TRAP or disambiguation lines).**
- 8.1 vs 8.2: Guide p.65. Rows Lao PDR 50/51, China 72/73, Malaysia 66/68, Russian Federation 60/61.
- 8.1 vs 4.6 (online copyright enforcement, Guide p.34): the same notice-and-takedown provisions are recorded under both
  (Malaysia row 26 is 4.6, row 66 is 8.1; Thailand row 29 is 4.6, row 72 is 8.1). Legitimate double-listing (Guide p.11), but the
  questions differ. 4.6 asks about rights-holder remedies; 8.1 asks about a liability shield for intermediaries.
- 8.1 vs 8.4: Mongolia row 44 records a copyright duty to prevent infringement and block infringing works as 8.1 = 0. That duty
  is not a shield (Guide p.64). It is removal or blocking material (Internal Guide p.13).
- 8.1 vs 9.1: blocking of IP-infringing content is not a 9.1 restriction (Guide p.70). Australia row 54 scores the Copyright Act
  s.115A site-blocking injunctions 0 under 9.1, which is consistent.

**Exemplars chosen.** SG 49 (canonical 0), RU 60 (IP-only shield, pairs with RU 8.2 = 1), IN 103 (general shield covers
copyright), CN 72 (copyright regulation with notice-and-removal), TH 72 (copyright act notice-and-takedown), ID 95 (0.5,
sectoral e-commerce). No score-1 exemplar: the only score-1 row is judged mislabelled (below).

**Rows excluded or suspected mislabelled.**
- `r2-la-050` (Lao PDR row 50, score 1). Its law text (Law on Electronic Transactions Art. 44-45) and note ("without separation
  for the IP infringement or other illegal activities") match row 51 (8.2), which scores 0. Guide p.65 footnote 40 says a general
  exemption still covers copyright. Expected: the same score as 8.2. **Likely mislabel.**
- `r2-mn-044` (Mongolia row 44, score 0). The Copyright Law Art. 52 duties it describes (prevent infringement, promptly block
  infringing works) contain no liability limit. As recorded, the evidence supports 1, not 0, and the duty is 8.4 material.
  Mongolia has no other 8.1 row. **Likely mislabel or wrong evidence.**
- `r2-id-097` (Indonesia row 97, 0.5). The text says the ITE Law "does not explicitly offer a safe harbor" and gives no
  protections, yet it also cites an Art. 15 fault-based exemption. Text and score do not line up; it looks like the economy
  score was copied onto the row. Not used.
- `r2-id-096` (Indonesia row 96, 0). Hedged ("could be interpreted as providing a form of safe harbor"). The Art. 55 description
  cannot be checked from host materials. Plausible but low confidence; not used.
- `r2-in-104` (India row 104, 0). A court judgment ordering Telegram to disclose infringers' identities. This is a disclosure
  order, not a safe-harbour provision. Not used.
- `r2-in-105` (India row 105, 0). A news report of a police complaint (FIR) against Google. The host reviewer kept the secondary
  source, but Pillar 8 is not practice-based (Internal Guide p.8 lists only 3.4, 5.3 and 9.1). Not used.
- `r1-my-066` (Malaysia row 66, 0). The score fits the Guide, but both URLs point to the Patent Act 1983 and Patents (Amendment)
  Act 2022 PDFs, not the Copyright Act. Not used because the citation is broken. Same URLs on row 68.
- `r1-au-047` (Australia row 47, 0). It names the "Copyright Amendment (Service Providers) Bill 2017" (a bill title). The
  Division 2AA shield covers only listed provider types (carriage service providers, disability bodies, libraries, archives,
  cultural and educational institutions). The Guide does not settle whether that is sectoral (0.5) or horizontal (0). Not used.

**Open questions.**
- Is a copyright shield that covers only named provider types "sectoral"?
- Should enforcement episodes (court orders, police complaints) be recorded as 8.1 rows at all?
- Indonesia has three 8.1 rows scored 0.5, 0 and 0.5. Which row controls the economy score?

---

## 8.2 Lack of safe harbour for other illegal activities

**What it asks.** Whether an economy has a safe harbour for illegal activities other than copyright infringement (Guide p.65).
Without one, intermediaries hosting such content are liable per se even when not notified (Guide p.65).

**Criteria to scores.** The methodology criteria text is identical to 8.1: none = 1, sectoral = 0.50, horizontal = 0. The Guide
scoring is on p.66, with the same "fully protects" versus "limits" gap as 8.1.
- TRAP, inverted polarity (Guide p.10; Guide p.66).
- The Guide's forms list on p.66 has only two bullets: separate laws (NZ Harmful Digital Communications Act) and one law covering
  both (Japan). There is no copyright-only bullet, since such a law gives 8.2 nothing.
- Footnote 41 repeats the Georgia example without the "remains applicable" copyright sentence.

**Confusions (sourced).**
- 8.2 vs 8.1, copyright evidence used for 8.2:
  - China row 73 cites the copyright-only network dissemination-right regulation (Arts 20-22: works, performances, recordings),
    the same instrument as 8.1 row 72.
  - Malaysia row 68 scores 8.2 = 1 on Copyright Act offences (s.43AA streaming technology, s.41).
  - Guide p.65 (Korea example) rules both out.
- 8.2 vs 8.4, removal duties:
  - Australia row 48 (8.2 = 1) cites the abhorrent violent material Act and Online Safety Act, the same laws as Australia 8.4
    rows 50 and 52.
  - Russian Federation row 61 describes an access-restriction duty in place of a safe harbour (1).
  - Thailand row 74 describes a notice procedure that exempts providers who comply (0).
  - Test: is there an exemption for intermediaries? The duty itself goes to 8.4 (Internal Guide p.13).
- 8.2 vs 9.1: the Singapore POFMA immunity for complying with access-blocking orders is 8.2 row 51 (0). The same Act's power to
  order blocking is 9.1 row 58 (1). Guide pp.69-70.
- 8.1/8.2 vs 12.9: overlap is at instrument level only. Indonesia GR 80/2019 (12.9 row 183), Indonesia ITE Law (12.9 row 182) and
  the Lao Law on Electronic Transactions (12.9 row 103) carry consumer-protection clauses (12.9) and intermediary exemptions
  (8.1/8.2). The provisions differ and no score confusion was found. This is **not** the 8.3-vs-12.9 claim tested below.

**Exemplars chosen.** SG 50 (canonical horizontal 0), IN 106 (conditional shield still 0), TH 74 (notice procedure, boundary with
8.4), LA 51 (general law covering all content), ID 98 (0.5 sectoral), RU 61 (1, IP-only shield elsewhere), MN 46 (1, absence
row).
- MN 46 is weak evidence: it cites the communications law's service duties and civil liability, not a content-liability rule.
  It is kept because its score agrees with the Guide and the pool has only one other clean score-1 row.

**Rows excluded or suspected mislabelled.**
- `r2-cn-073` (China row 73, 0). The cited instrument is copyright-only and cannot show a non-copyright safe harbour (Guide p.65).
  The score may still be right on other Chinese law, but none is cited. **Wrong evidence.**
- `r1-my-068` (Malaysia row 68, 1). The evidence is copyright offences (8.1 scope). It contradicts Malaysia row 67 (0). URLs are
  Patent Act PDFs. **Likely mislabel.**
- `r1-my-067` (Malaysia row 67, 0). Innocent-carrier clause in an industry Content Code made under the Communications and
  Multimedia Act. The Guide's sector-specific examples are telecommunications and e-commerce rules (pp.65-66), so 0.5 may fit
  better. Open question; not used.
- `r2-id-099` (Indonesia row 99, 0.5). The text says the ITE Law "does not provide a safe harbor" and requires takedown on
  government request (an 8.4-type duty), yet the row scores 0.5. It appears to carry row 98's score. Not used.
- `r1-au-048` (Australia row 48, 1). Relies on removal and reporting duties and does not check whether those Acts limit hosts'
  or ISPs' liability. A reviewer should check the Online Safety Act for any host or ISP liability limitation before promoting
  this row. Not used.
- `r2-mn-045` (Mongolia row 45, 1). Cites information-transparency, secrecy and personal-data laws that never mention
  intermediaries. The useful reasoning sits in the note (content-service takedown duties without immunity). Score plausible,
  evidence weak; not used.
- `r1-sg-051` (Singapore row 51, 0). Immunity for complying with government directions, closer to Japan's deletion immunity
  (Guide p.66) than to a user-content shield. The text was "edited by Singapore feedback" from a version that said intermediaries
  can be held liable. Boundary case; not used.
- `r2-th-073` (Thailand row 73, 0). Mixes CCA s.15 (a liability rule) with a news item about a ministry lawsuit against Facebook.
  The exemption itself is in the Notification (row 74). Not used.

---

## 8.3 User identity requirements

**What it asks.** Whether an economy imposes user identity requirements. Intermediaries must verify and record accurate personal
information of users as a condition for access to their services or networks. This includes collecting, storing and sometimes
authenticating documents or data (Guide p.66).

**Criteria to scores.** Guide p.67: 1 if the requirement applies "in order to connect to the Internet or access online services";
0.5 if it is for SIM card registration; otherwise 0. Methodology 8.3 uses the same three categories. Its (2) has a typo, "Used
identity requirement for SIM registration".
- The Guide does not score its six examples. My reading (inference only):
  - Argentina and Venezuela (mobile subscriber registration) and Tajikistan (communications contracts) look like the SIM or
    subscriber branch.
  - Bangladesh (first originator on messaging) and Rwanda and Uganda (intermediaries generally) look like the online branch.

**Team-plan claims tested.**
- **8.3 vs 7.4: not supported.** 7.4 is DPO/DPIA requirements (Guide pp.60-61; Methodology 7.4). No Guide text, FAQ line or row
  links identity verification to DPO or DPIA duties.
  - The only overlap is one instrument with different provisions: India IT Rules 2021 appear under 7.4 (row 95, compliance
    officer, 0) and 8.3 (row 108).
  - The **sourced** sibling is **7.3** (retention). Guide p.60 lists India's cyber-café user-ID records (at least 1 year) as a
    7.3 example. The Guide's own 8.3 Bangladesh example includes keeping registration data for 180 days (p.66). Rows record the
    same instruments under both: India 86 (7.3) and 109 (8.3); Thailand 64-65 (7.3) and 75-76 (8.3). The plan may have meant 7.3.
- **8.3 vs 12.9: not supported.** 12.9 is the lack of an online consumer protection framework (Methodology 12.9; Guide p.83
  list). All 23 12.9 rows cite consumer-protection or e-commerce laws, and none mentions identity verification.
  - The nearest identity-related rows outside Pillar 8 are 12.7 China row 121 (domain registrants must give true identity;
    recorded as context, score 0) and 12.3 Thailand row 111 (licensing of digital-ID service businesses). Neither is 12.9.
- **Additional sourced sibling: 7.5.** Guide p.62 (India: ISPs log all users; agencies get the subscriber list) and Guide p.67
  (Uganda: collect customer data and disclose it to authorities). The identity-collection duty is 8.3; authorities' access is 7.5.
- **8.3 vs 8.4 (sourced).**
  - India row 113 codes under 8.4 the first-originator duty that Guide p.66 (Bangladesh) places in 8.3. India row 108 already has
    it under 8.3.
  - Mongolia rows 48 (8.3) and 49 (8.4) both cite the Digital Content Service conditions; the IP-display clause 7.3.4 appears in
    both.

**Exemplars chosen.** CN 76, RU 62, LA 52 and IN 109 (1: forums and comments, messaging, social media, cyber café); AU 49, MY 69 and
ID 100 (0.5: SIM); CN 78 (0: voluntary authentication). IN 109 doubles as the 7.3 boundary row.

**Rows excluded or suspected mislabelled.**
- `r2-th-075` (Thailand row 75, 1). The legal hook is CCA s.26 traffic-data retention (90 days to 2 years), which is 7.3 and also
  Thailand 7.3 row 64. The identity element is café Wi-Fi practice plus a Starbucks privacy statement (a company policy). Thailand
  row 64 notes that s.26 also requires keeping client identification data, which could support 8.3, but row 75 does not cite it.
  **Weak evidence / possible mislabel.**
- `r2-th-076` (Thailand row 76, 1). The score fits (Clause 8 identity verification for all users). But the first ~600 characters
  of the impact text describe only the retention scheme, so a trimmed exemplar would teach retention as 8.3. Not used; fine as a
  gold row.
- `r2-in-108` (India row 108, 1). The score fits (first originator), but the impact text is copied from 8.2 row 106, and the 8.3
  element appears only at the end. Not used for the same trimming reason.
- `r2-mn-048` (Mongolia row 48, 1). Publicly displaying a user's IP address is de-anonymisation, not verifying and recording
  identity as a condition of access (Guide p.66). Borderline; not used.
- `r2-mn-047` (Mongolia row 47, 0.5). CRC licence conditions require telephone **and IP-based** service operators to register each
  user's citizen number and name. Coverage of Internet services suggests 1 (Guide p.67), not the SIM-only 0.5. **Possible
  under-score.**
- `r2-id-101` (Indonesia row 101, 1). The instrument is titled a regulation on telecommunications operation (MOCI No.5/2021), but
  the text describes identity checks by electronic system operators for digital transactions and e-signatures. The same URL
  appears on row 100 for a different regulation. Cannot verify; not used.
- `r1-sg-052` (Singapore row 52, 0.5). No law is named ("Regulatory Controls on Prepaid SIM Cards"). URLs are an IMDA press release
  on SMS sender-ID registration and a Singtel page. Score plausible, source weak; not used.

**Open questions.**
- Where do fixed or broadband subscriber registration and domain-registrant identity rules fall? The Guide covers only Internet
  or online-service access versus SIM.
- A duty to *enable* identification on request (first originator) is scored 1 by the workbook and matches the Guide's Bangladesh
  example. Keep it at 1?

---

## 8.4 Monitoring requirements

**What it asks.** Whether an economy imposes content monitoring requirements. Intermediaries must actively monitor users'
activities, or remove or block content deemed illegal, to avoid liability. Duties can be explicit or indirect, such as installing
software, algorithms or tools to detect or manage prohibited content (Guide p.67). The FAQ confirms two aspects: (a) monitoring
content, (b) blocking or removing content (Internal Guide p.13).

**Criteria to scores.** Guide p.67: 1 if at least one monitoring requirement is implemented; 0.5 for active monitoring of users
without any legal obligation to remove or block; otherwise 0. Methodology 8.4 has three categories: (1) any monitoring requirement
(monitor users or remove/block); (2) active monitoring without a removal or blocking obligation; (3) no measure.
- Categories (1) and (2) overlap for a monitoring-only duty. The codebook gives any removal or blocking duty 1 and a
  monitoring-only duty 0.5, which is the only reading that keeps the categories exclusive. **Inference; needs a host ruling.**
- No 0.5 row exists in either workbook. Malaysia row 71 uses the 0.5 wording in its text but is scored 1.

**Team-plan claims tested.**
- **8.4 vs 7.5: supported.** The workbook codes the same agency-access provisions under both:
  - India licence clauses (subscriber list for security agencies, lawful interception and monitoring systems): 7.5 row 97 and
    8.4 row 112. Guide p.62 uses the subscriber-list clause as its 7.5 example.
  - India IT Act s.69 interception, monitoring and decryption directions: 7.5 row 98 and 8.4 row 111.
  - Australia Telecommunications (Interception and Access) Act with the Assistance and Access Act: 7.5 row 44 and 8.4 row 51.
    Row 51 itself says there is "no general monitoring requirement".
  - China Counterterrorism Law: Art. 18 interfaces and decryption as 7.5 (row 68). The 8.4 row 80 adds Art. 84 penalties for
    failing that duty to its valid Art. 19 content-monitoring evidence.
  Guide p.67 frames 8.4 as intermediaries policing content. Guide p.62 frames 7.5 as Government access to personal data without
  independent judicial authorisation, matching the host trap row on 7.5.
- **8.4 vs 9.1: supported (sibling, not always an error).**
  - Guide p.69 9.1 examples read like 8.4 duties: Brunei licensees must use best efforts to ban content; Türkiye social networks
    must remove or block illegal content within 24 hours of notification.
  - Guide p.68 links intermediaries' over-blocking to Pillar 9.
  - The same instruments appear under both 8.4 and 9.1 in eight of the ten economies. Pairs give the 8.4 row first, then the
    9.1 row:
    - Malaysia Content Code (70-71 / 74)
    - Indonesia MOCI Reg 5/2020 (102 / 107)
    - Mongolia Digital Content Service conditions (49 / 55)
    - Russian Federation 149-FZ (65 / 70)
    - Singapore OCHA (54 / 60) and Broadcasting Act codes (55-56 / 59)
    - Australia Online Safety Act (52 / 55)
    - Lao PDR cybercrime law (56 / 60)
    - India IT Rules 2021 (113 / 117)
  - What differs: 9.1 is practice-based (Internal Guide p.8) and limited to commercial content. It excludes political, criminal,
    age-restricted and defamation content and IP-based blocking (Guide p.70; Indicator Reference note for 9.1). No content
    exception is stated for 8.4. Guide p.11 allows recording under both.
- **Also sourced.**
  - 7.3: the Lao PDR cybercrime law's retention periods are 7.3 = 1 (row 45) and 8.4 = 0 (row 56), a correct split.
  - 8.3: India row 113.
  - 8.1: Russian Federation row 64 (knowledge standard is not monitoring, 0).

**Exemplars chosen.** LA 54 (the Guide's own Lao PDR example), MN 49 (mandated word filter = indirect monitoring), SG 55 (proactive
detection), CN 79, AU 50 (removal offence), ID 102 (notice-triggered removal); RU 64 (8.1 boundary, 0), LA 56 (7.3 boundary, 0).

**Rows excluded or suspected mislabelled.**
- `r1-au-052` (Australia row 52, 0). Online Safety Act removal notices (24 hours) and ISP blocking in crisis events are
  removal/blocking duties, so 1 under Internal Guide p.13 (b). Inconsistent with Australia row 50 and Indonesia row 102.
  **Conflicts with the FAQ.**
- `r1-sg-053` (Singapore row 53, 0). Duty to comply with directions to disable access or block, with criminal liability. The row
  reasons that no monitoring is required, but FAQ (b) counts blocking and removal duties. **Conflicts with the FAQ.**
- `r2-th-078` (Thailand row 78, 0). Says Thailand has no monitoring requirement, yet Thailand 8.2 row 74 describes a 2022
  ministerial notification requiring removal within 24 hours to 7 days. Open question: probably an 8.4 = 1 measure under FAQ (b).
- `r1-my-071` (Malaysia row 71, 1). The text says there is "no mandate for active monitoring" and uses the 0.5 wording, but the
  row scores 1. Text and score disagree.
- `r2-mn-050` (Mongolia row 50, 0). The Child Protection Law Art. 25.5-25.6 requires online media and ISPs to monitor, restrict
  and block content harmful to children, so 1 on Guide p.67. Coverage and timeframe are empty. The 9.1 age-restricted exception
  may have been borrowed; Singapore row 55 scores similar child-safety duties 1.
- `r2-in-110` (India row 110, 1). Its URL is `Draft_Intermediary_Amendment_24122018.pdf`, a draft, and drafts score 0 (host trap
  rows). The enacted technology-based-measures duty is described in the IT Rules 2021 rows (India 106/108). **Mislabel under the
  host draft rule.**
- `r2-in-111` and `r2-in-112` (India rows 111, 112, 1). Government interception, decryption and subscriber-list access, which are
  7.5 (already rows 98 and 97). They do not fit Guide p.67. **Double-coded; human decision.**
- `r2-in-113` (India row 113, 1). The first-originator duty belongs to 8.3 (Guide p.66) and is already India row 108.
  **Likely mislabel.**
- `r1-au-051` (Australia row 51, 1). The interception-assistance part is 7.5 (row 44), and the removal part duplicates row 50.
- `r2-cn-080` (China row 80, 1). The score is fine on Art. 19, but it mixes in 7.5 material (Art. 84 interface and decryption
  penalties). Not used.

---

## Checker

`python -X utf8 check_drafts.py g3`: 0 errors, 0 warnings on the final run.

## Top concerns (group)

1. **8.4 removal on notice or direction is scored both ways.** Australia 52, Singapore 53 and Thailand 78 score it 0; Indonesia
   102, Malaysia 70 and Russian Federation 65 score it 1. Internal Guide p.13 (b) says blocking or removal duties count, so the
   codebook scores 1. A host ruling is needed; it moves several economies.
2. **8.4 double-codes government access.** India 111/112, Australia 51 and part of China 80 are 7.5 material (Guide p.62 uses the
   India clause as its 7.5 example). The codebook TRAP sends them to 7.5; a human should decide whether the 8.4 copies stay.
3. **"One law covers both" is broken in 8.1.** Lao PDR 50 (1) and 51 (0) score the same text differently, against Guide p.65
   footnote 40. As a result, 8.1 has no trustworthy score-1 exemplar, and 8.2 has only one clean score-1 row (Russian Federation 61).
4. **Wrong evidence in 8.1/8.2.** Copyright instruments are cited for 8.2 (China 73, Malaysia 68), and a copyright duty is recorded
   as a safe harbour (Mongolia 44). The pipeline must ask "is there a liability shield?", not "is there an intermediary or
   copyright provision?".
5. **Sectoral vs horizontal is undefined for intermediary statutes.** The Guide's 0 is a framework that "fully protects"; the
   methodology's 0 is one that "limits". All Guide examples are conditional. Is a copyright act covering only listed providers
   (Australia 47) or an industry content code (Malaysia 67) horizontal? The Guide does not say.
6. **The 8.4 scale is untested at 0.5.** No 0.5 row exists, and methodology categories 1 and 2 overlap for monitoring-only duties.
   The codebook's "monitoring only = 0.5" is an inference.
7. **Team-plan claims.** 8.3 vs 7.4 and 8.3 vs 12.9: not supported by any source. The sourced 8.3 siblings are 7.3 (retention of
   ID records, Guide p.60) and 7.5 (Guide pp.62, 67). 8.4 vs 7.5: supported. 8.4 vs 9.1: supported (the same instruments are
   coded under both in eight of the ten economies).
8. **Data quality.**
   - A draft is cited and scored 1 (India 110).
   - URLs point to the Patent Act (Malaysia 66/68).
   - A SIM row names no law (Singapore 52).
   - Secondary-source enforcement rows sit in a non-practice indicator (India 104/105).
   - Impact text is copied across indicators, so trimmed exemplars mislead (India 106/108/113; Thailand 76 leads with retention).
