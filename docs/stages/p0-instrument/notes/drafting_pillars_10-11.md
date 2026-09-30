<!-- Drafting notes for pillars 10-11 (10.1-10.4, 11.1-11.4). Written 2026-09-13 by a Claude drafting agent working from the host
sources in ../sources/. Checked by the lead for structure (checker, merge, citation audit) but NOT reviewed by a
human. Row IDs: r1-/r2-<economy>-<row> = gold_id in the repo gold set. -->

# g5 notes: Pillar 10 (Non-technical NTMs) and Pillar 11 (Standards and procedures)

Draft 2026-09-13, pending lead and human review.
Host IDs: `10.1`, `10.2`, `10.3`, `10.4`, `11.1`, `11.2`, `11.3`, `11.4`. No Tier B IDs are assigned to this group,
so every confusion below is a **trap candidate** for later promotion, not a codebook rule.
Pages are printed Guide pages. "Row N" means the workbook row number on that economy's sheet
(round1 = Australia, Malaysia, Singapore; round2 = China, India, Indonesia, Lao PDR, Mongolia, Russian Federation, Thailand).

---

## 0. Group-wide findings

### 0.1 Leads from the brief, checked against the sources

| Lead | Result | Source |
| :--- | :--- | :--- |
| Pillar 10 NTMs on raw materials (rare earths) score 0.00 | Confirmed | Internal Guide p.14; Guide p.9 (raw materials such as rare earth not covered); Internal Guide p.7 |
| 10.4 covers all export restriction types (ban, licence) on ITA I/II/III products | Confirmed | Internal Guide p.14 |
| 2.1 vs 10.1 when a ban applies only to government entities | Confirmed, but the FAQ gives no decision rule: check whether it is an import ban (10.1) or a procurement restriction (Pillar 2); one measure may be listed under several sub-pillars | Internal Guide p.11. The workbook resolves the FAQ's own example (TikTok on Australian government devices) as 2.1 = 0.5 (workbook round1 Australia row 5), with Australia 10.1 = 0 (row 59) |
| 11.2 keywords "certification" and "license"; look at technical standards and telecom equipment regulations | Confirmed. The FAQ adds that 11.2 captures domestic regulations and regional MRAs, and exceptions may sit in MRAs | Internal Guide p.14 |
| ASEAN and APEC MRA members score 0.5 or less | Confirmed; lists ASEAN EE MRA (2012), APEC TEL MRA (1999), APEC EEMRA | Internal Guide p.15 |
| 11.2 = certification (marking) vs 11.3 = (additional) testing procedures | Confirmed | Internal Guide p.15 |
| ICT product scope = WTO ITA lists | Confirmed: ITA I, ITA II and the ITIF-proposed ITA III | Guide p.9; Annex III from Guide p.102; Internal Guide pp.7, 11 |
| 10.1 vs 10.2 vs 10.3 confusion | Real; shown by rows (sections 10.1-10.3) | Guide pp.74-76; workbook round2 Lao PDR row 65 note |
| 11.4 vs 2.2 confusion | Real; 2.2 is encryption as a condition of winning tenders (scored 0.5 there) | Guide p.19 vs Guide pp.80-81 |

The coordinator's correction to `assign2.txt` does not affect this group: the corrected file covers 6.1, 7.3 and 5.3 only, and nothing here cites it.

### 0.2 Sourced rules that apply across the group
- Pillar 10 covers measures other than tariffs or taxes (Guide p.74). Tariffs are the non-regulatory 1.1/1.2 (Non-regulatory note); customs duties on electronic transmissions are 12.6 (Guide p.86).
- ICT goods are ITA I/II and proposed ITA III products (Guide p.9; Annex III p.102). E-waste and used ICT products are not scored (Internal Guide p.7). Raw materials score 0 (Internal Guide p.14).
- One measure can be listed under several sub-pillars (Internal Guide p.11). The workbooks do this often (0.4).
- None of the eight is practice-based (Internal Guide p.8 lists only 3.4, 5.3, 9.1). Each Guide section names secondary sources (WTO I-TIP, Global Trade Alert, WTO TPRs, OECD raw-materials inventory, TIA, ITU, World Map of Encryption Laws and Policies, Freedom House) only as pointers to primary sources (Guide pp.74-81; general rule Guide p.12).
- Where no measure exists, researchers note the absence and cite the governing general law (Guide p.12). That is why so many score-0 rows cite customs acts or standards acts.

### 0.3 Row-level vs economy-level scoring (matters for the pipeline)
Both workbooks score each row (one measure) separately and hold no economy-level aggregate. Several Guide rules only make sense at economy level:
- 10.1: 1 if "more than one measure in place" (Guide p.74).
- 10.2: 1 if two or more cost-adding measures (Guide p.75; Methodology sheet 10.2). Yet Lao PDR has 7 rows and India 4 rows in 10.2, every one scored 0.5.
- 10.3: 1 if two or more product-level LCRs (Guide p.76). Here the workbook did escalate within single rows (Indonesia rows 135, 137, 138).
- 11.2: 0 if SDoC is recognised for at least some ICT products (Guide p.79). Thailand has a 0.5 row (100) next to three 0 rows (101, 102, 104).
- 11.3: 0.5 if third-party testing is accepted for at least some products (Guide p.80).

Inference (not a host rule): the pipeline should score each provision on its own facts and leave escalation to an economy-level step. **Open question for the lead:** how does the host aggregate rows into the economy score?

### 0.4 Measures the workbooks code under several indicators

| Measure | Coded under |
| :--- | :--- |
| EAEU Board Decision No. 30 (non-tariff measures) | 10.1 = 0 (Russian Federation row 80), 10.2 = 0.5 (row 81), 10.4 = 1 (row 84), 11.3 = 1 (row 90) |
| India MTCTE (mandatory testing and certification of telecom equipment) | 11.2 = 1 (India row 134), 11.3 = 1 (India row 137) |
| India BIS registration scheme | 10.2 = 0.5 (row 128, as import condition), 11.2 = 0 (row 135), 11.3 = 1 (row 138) |
| China National Security Law art.59 | 3.4 = 0.25 (China row 20), 11.3 = 1 (China row 105) |
| Indonesia Kominfo Reg. 16/2018 (certification of telecom equipment) | 11.2 = 0.5 (row 145), 11.3 = 0.5 (row 149) |
| Indonesia MOCI Reg. 41/2009 (domestic component level) | 2.1 = 1 (row 8), 2.3 = 1 (row 16), 10.3 = 1 (row 134) |
| Malaysia Strategic Trade Act 2010 | 10.2 = 0.5 (row 82), 10.3 = 0 (row 84), 10.4 = 1 (row 85) |
| Thailand Radio Communication Act B.E. 2498 | 10.2 = 0.5 (row 91), 10.4 = 1 (row 94) |
| Singapore Telecommunications Act / Dealers Regulations | 10.1 = 1 (row 65), 10.2 = 0.5 (row 66); dealer licences also discussed in 5.5 (row 30) |
| Lao PDR Standard Law No.49/NA 2014 | 11.1 = 0 (row 80), 11.2 = 0.5 (row 81), 11.3 = 0.5 (row 82), 11.4 = 0 (row 83) |
| Russian Federal Law 99-FZ (licensing, incl. encryption) | 5.5 = 0 (row 39), 9.4 = 0.5 (row 77), 11.4 = 0 (row 92) |
| India RBI Master Direction on Digital Payment Security Controls 2021 | 11.4 = 0 (India row 140), 12.4.3 = 0 (India row 148) |
| Thailand Computer-Related Crime Act B.E. 2550 | 7.5 = 0 (Thailand row 69), 11.4 = 0 (Thailand row 105) |

### 0.5 Name and text defects noticed
- Reference and methodology name of 10.4 read "ICTgoods"; the spec uses "ICT goods".
- Methodology criteria for 10.2 read "Import estrictions" (category 2).
- Methodology category for 10.3 has a trailing space ("Local content requirements ").
- Guide p.11 says import bans and LCRs "under Pillar 9" capture non-technical NTMs; it means Pillar 10.
- Guide p.75 defining sentence for 10.2 is garbled ("excluding other than import bans..."); it is quoted verbatim in `guide_refs.yaml`.
- Guide p.81 block-size bullet is garbled ("lower than 64-bit block cyphers and 128-bit block cyphers").
- Host 11.1 name "Lack of transparent technical standards" differs from the Guide heading "Technical standards issues" (p.78); matched by the methodology criteria (participation and transparency).

---

## 10.1 Import ban applied to ICT goods and online services

**What it asks.** Import bans on ICT goods and online services, both bans aimed at ICT products and broader bans whose lists include them (Guide p.74). The pillar introduction gives import bans on certain applications, justified by cybersecurity and national security, as an example (Guide p.74).

**Criteria to scores** (Methodology sheet 10.1; Guide p.74).
- 1: ban on more than one ICT good or digital service. The Guide adds: more than one measure in place, or one measure covering more than one product or service.
- 0.5: one ban on one specific product or service.
- 0: no measure.
- Weight 42%, highest in the pillar, because a ban blocks imports outright (Guide p.77).

**Trap candidates.**
1. TRAP candidate: an import prohibition lifted by permit or licence (walkie-talkies, satellite equipment) -> 10.2 at 0.5 (workbook round2 Lao PDR row 65 reviewer note; Lao PDR rows 68, 69 in 10.2). The impact texts of Lao PDR rows 68-70 still use the word "ban", so the word is not decisive.
2. TRAP candidate: a ban limited to government entities or government devices -> 2.1 (Internal Guide p.11; workbook round1 Australia row 5 = 0.5 under 2.1; Australia 10.1 row 59 = 0). The FAQ allows either; the workbook chose 2.1.
3. TRAP candidate: bans on e-waste or used ICT products -> not scored (Internal Guide p.7; workbook round2 China row 95; round1 Malaysia row 79 note; round2 Thailand row 89). Raw materials -> 0 (Internal Guide p.14).
4. TRAP candidate: blocking a website or web content -> 9.1 (Guide p.69); banning named applications -> 10.1 (Guide p.74). India's app bans sit in 10.1 (row 125 = 1) and India's blocking of YouTube channels in 9.1 (row 116); both invoke IT Act s.69A, so the statute alone does not decide.
5. A local content threshold enforced by a sales ban (Indonesia iPhone 16, Google Pixel): the host coded the ban in 10.1 (Indonesia row 126 = 1) and repeated the same story inside the LCR row (Indonesia 10.3 row 135 = 1). Double-counting risk; the LCR itself is 10.3 (Guide pp.75-76).
6. Content-based prohibitions (obscene or extremist media, counterfeit goods) scored 0 (workbook round2 Russian Federation row 80; Thailand row 89). No Guide sentence says so; inference: they are not restrictions on ICT products as such.

**Exemplars chosen.** Singapore 65 (1, several prohibited ICT items in one schedule), India 125 (1, app bans = online services), Malaysia 79 (1, general customs order listing ICT items; waste additions left unscored), Lao PDR 66 (the only 0.5 row), Lao PDR 65 (absence row plus the 10.2 boundary note), China 95 (e-waste negative), Australia 59 (absence row, 2.1 boundary), Russian Federation 80 (content-media negative). Seven economies; scores 1/0.5/0.

**Rows excluded and why.**
- r2-id-126 (Indonesia row 126, 1): the ban facts (iPhone 16, Pixel, TikTok Shop, Temu) come from news cited in the note (Reuters, CNA, FT, The Diplomat); the instruments cited are an LCR regulation and an e-commerce regulation. Weak against the official-source rule (Guide p.12) and double-counts 10.3 row 135. The note also says "The score will change for next year".
- r2-in-124 (India row 124, 0): imports of handsets with fake or duplicate IMEI are prohibited, scored 0 with no reason given. Plausibly anti-counterfeit like Thailand row 89, but a single-product ban scores 0.5 under Guide p.74. Human check.
- r2-in-125 caveat (kept): the row says 267 apps, but its own dated batches (59 + 118 + 43) total 220. Score unaffected; the curated note avoids the number.
- r2-th-089, r2-mn-060: sound absence/negative rows, not needed.

**Guide / methodology / workbook.** Guide p.74 escalates to 1 for "more than one measure in place" (economy level); the methodology criterion counts products; the workbook scores per row.

**Open questions.** (a) Lao PDR row 66 suspends satellite receiver imports "without prior approval": ban (10.1) or licence (10.2)? The reviewer note in row 65 thought the 2018 notification might have lapsed; row 66 says it runs to 31 December 9999. (b) Should content-based media prohibitions be recorded at 0 or left out?

---

## 10.2 Other import restrictions on ICT goods and online services

**What it asks.** Import restrictions other than bans and LCRs (Guide p.75): trade-blocking quotas, and licensing schemes and procedures that add cost and delay. Guide examples: Argentina's non-automatic licences for semiconductor manufacturing machines; Haiti's annual licence for foreign-national importers; Botswana's regulator approval of communications equipment; Pakistan's limit on who may import transmission equipment and cameras (Guide p.75).

**Criteria to scores** (Methodology sheet 10.2; Guide p.75).
- 1: quotas or other trade-blocking restrictions, OR at least two cost-adding measures. The Guide adds "the absence of institutional transparency".
- 0.5: a restriction adding compliance cost: licences, permits, authorisation, registration for ICT goods, labelling requirements and import controls, for goods and online services ("0.5 for each restriction" in the Guide).
- 0: none.
- Weight 21% (Guide p.77). Footnote 45 points to the UNCTAD NTM classification for procedure types (Guide p.75).

**Trap candidates.**
1. TRAP candidate: licence-conditioned "ban" -> 10.2, not 10.1 (workbook round2 Lao PDR row 65 note; Lao PDR rows 68, 69).
2. TRAP candidate: import licensing of encryption devices or technologies -> 10.2, not 11.4 (Guide p.81; workbook round2 Russian Federation row 81; China rows 96, 97). China row 96 restricts importing encryption "stronger than 256-bit"; it reads like a key-length rule but is a technology import licence.
3. Certification or type approval as a precondition of import is coded 10.2 in several rows (Lao PDR rows 70, 71, 73; Malaysia row 81), while the same regimes' SDoC and testing design is coded 11.2/11.3; Lao PDR row 73's note says "Also relevant to 11.3". Dual listing is allowed (Internal Guide p.11); the pipeline should emit both where both facts are present.
4. TRAP candidate: customs duties or VAT on imported intangibles -> 12.6 or out of scope (Guide pp.74, 86). Indonesia row 132 (PMK-190) scored 0.5 here for the import notification form; Indonesia 12.6 row 170 covers the tariff classification. Only the procedural element belongs here.
5. TRAP candidate: telecom operator licence -> 5.5; equipment dealer or import licence -> 10.2 (workbook round1 Singapore row 30 vs row 66).
6. An enabling power to require licences with no ICT goods listed -> 0 (workbook round2 Thailand row 90); generic customs documents -> 0 (Mongolia row 61).
7. The score-1 trigger "absence of institutional transparency" appears only in the Guide (p.75), in public-procurement wording copied from Guide pp.12 and 20; the methodology sheet omits it. Do not score 10.2 = 1 on transparency grounds without a lead decision.

**Exemplars chosen.** Singapore 66 (dealer licence plus import permit), Thailand 91 (radio import licence; reviewer note "Correct"), India 128 (BIS registration and labelling as import condition; testing side in 11.3), Russian Federation 81 (encryption and radio-electronic import permits; 11.4 boundary), Lao PDR 68 (10.1 boundary), Indonesia 131 (the only unstruck 1), Mongolia 61 and Thailand 90 (the only 0 rows). Seven economies.

**Rows excluded / suspected mislabels.**
- r2-la-067 (Lao PDR row 67, 0.5): **suspect**. Its own note says the 2023 goods list is unavailable, "So now put the score of 0.00", and that the 2012 lists cover no ICT goods (HS 4901 printed matter is not ITA). The 0.5 contradicts the note. Sources: row note; ITA scope (Guide p.9).
- r2-id-127 (0.5) vs r2-id-131 (1): both describe Import Approval plus Surveyor Report for electronics. One is mis-scored under the two-measure rule (Methodology sheet 10.2). Row 131 was kept as the only score-1 exemplar, but row 127 says the electronics import regime is now MOT Reg. 36/2023 as amended; the sources do not say whether MOT Reg. 68/2020 (row 131) still applies. Human check.
- r2-id-128 (0.5): importer rules bundle 25 after-sales centres, a three-year local manufacturing commitment and a certificate open only to Indonesian-owned firms. Arguably several measures (1) and an LCR element (10.3). Human check.
- r2-id-130 (1): struck; excluded.
- r2-id-132 (0.5): import notification and VAT for software transmitted electronically; overlaps 12.6 and tax (Guide pp.74, 86). Excluded.
- r1-my-080 (0.5): its item list includes used televisions; used ICT products are not scored (Internal Guide p.7). Mixed row; excluded.
- r2-la-072 (0.5): bundles an import control with a Lao-language menu requirement (a technical requirement). Excluded.
- r1-au-060 (0.5): energy-efficiency registration and trade-description labelling for electrical appliances; ITA coverage of the products is not shown. Excluded.

**Guide / methodology / workbook.** Transparency trigger (trap 7). "0.5 for each restriction" and "1 for two or more" reconcile only if a row is one measure and 1 is an economy-level result; the workbook never shows that result.

**Open questions.** (a) Economy aggregation (0.3). (b) Should certificate-before-import rows be recorded in 10.2 at all when 11.2/11.3 already capture the regime?

---

## 10.3 Local content requirements

**What it asks.** Requirements to use domestically manufactured goods or domestically supplied services in producing ICT-related goods and online services; LCRs in public procurement tenders are excluded and covered by Pillar 2 (Guide p.75). Guide examples: Argentina (manuals, packaging, labels for mobile equipment made in Tierra del Fuego); Bhutan (OTT providers 60% local content); India (single-brand retail 30% local sourcing for foreign ownership above 51%); Indonesia (digital TV receivers and IP set-top boxes 20% rising to 50%) (Guide p.76).

**Criteria to scores** (Methodology sheet 10.3; Guide p.76).
- 1: at least one LCR at sectoral or horizontal level (HS-4, e.g. telephony equipment, or HS-2), OR two or more product-level LCRs.
- 0.5: one LCR at product level (HS-6/HS-8, e.g. mobile phones and smartphones).
- 0: none.
- Weight 21% (Guide p.77).

**Trap candidates.**
1. TRAP candidate: LCR or domestic preference in public procurement -> 2.3 (Guide pp.20, 75). The same Indonesian instrument (MOCI Reg. 41/2009) appears under 2.1 row 8, 2.3 row 16 and 10.3 row 134; the deciding fact is procurement versus commercial market.
2. Quota vs LCR: a cap on a website's foreign dramas relative to its domestic purchases was coded 10.3 = 0.5 (workbook round2 China row 98), while import quotas are 10.2 (Guide p.75). Inference: a cap on imported volume -> 10.2; a required domestic share of inputs or content -> 10.3.
3. Policy objectives, promotion bodies or enabling powers with no binding share -> 0 (workbook round1 Malaysia row 83; round2 Russian Federation row 82; Thailand row 92). A decree repealing LCRs -> 0 (Lao PDR row 74).
4. Sales bans that enforce an LCR -> see 10.1 trap 5.
5. Requirements on raw materials, such as domestic mineral processing -> 0 (Internal Guide p.14; Indonesia 10.4 row 140 note).
6. HS-level criteria do not fit services: the workbook scored content quotas 1 (Australia row 61, Indonesia row 136) or 0.5 (China row 98) with no HS mapping. No host rule for services; needs a lead decision.

**Exemplars chosen.** India 130 (the Guide's own example), Indonesia 136 (matches the Guide's Indonesia example), Indonesia 134 (sector level; procurement boundary), Indonesia 135 (two product-level LCRs; 10.1 boundary), China 98 (the only 0.5), Russian Federation 83 (domestic pre-installed software, a less obvious LCR form), Lao PDR 74 and Malaysia 83 (negatives). Six economies; Indonesia is over-represented because 7 of the 18 pool rows are Indonesian.

**Rows excluded / suspected mislabels.**
- r1-au-061 (Australia row 61, 1): **suspect scope**. Australian content quotas for free-to-air commercial TV; the impact text describes only broadcasting over DVB-T spectrum although coverage says "Streaming services". Measures that apply only to offline versions are excluded (Guide p.9; Internal Guide p.7), and the Guide's services example is OTT (Guide p.76). Check whether any streaming obligation exists.
- r2-id-133 (1): Kominfo Reg. 3/2024 "includes provisions aimed at increasing the local content" with no article or percentage. Thin evidence.
- r2-id-138 (1): law field names Reg. 9/2019 on WDM equipment, but the impact describes MCIT Reg. 4/2019 on DVB-T2 set-top boxes, and the URL is the same as row 139. Citation mismatch.
- r2-id-139 (1): says the regulation text is "not readily available in public records"; shares its URL with row 138. Weak evidence.
- r1-my-084 (0): impact reuses Strategic Trade Act export-licensing text as "local content". Score fine, text misleading.
- r2-ru-082, r1-sg-068, r2-mn-062, r2-th-092 (0): sound, not needed.

**Guide / methodology / workbook.** Guide and methodology agree. Workbook and Guide diverge on services (trap 6).

**Open questions.** How to grade service content quotas (0.5 vs 1) without HS codes.

---

## 10.4 Export restrictions on ICT goods and online services

**What it asks.** Export restrictions on ICT goods and services: export bans, export licences and other limits on the number of goods or services exported (Guide p.76). Guide examples: export licences for strategic and dual-use items including computers, telecom equipment and information-security products (Armenia, Georgia, India, Kyrgyzstan, Republic of Korea); Colombia's smartphone export prohibition; Hong Kong, China export permits for radio transmitting apparatus; Thailand's export licence for radio communication equipment (Guide p.76). All export restriction types on ITA I/II/III products are captured (Internal Guide p.14).

**Criteria to scores** (Methodology sheet 10.4; Guide p.76). Binary: 1 if at least one export restriction; else 0. Weight 17%, the lowest, because its effect on foreign competition at home is limited (Guide p.77).

**Trap candidates.**
1. TRAP candidate: export ban or duty on raw materials (nickel ore, rare earths) -> 0 (Internal Guide p.14; workbook round2 Indonesia row 140; China row 99 text says rare earths are not ICT goods).
2. Export duties or taxes -> outside pillar 10 (Guide p.74).
3. An enabling power to prohibit or license exports with no ICT product listed -> 0 (workbook round2 Thailand row 93; Lao PDR row 78).
4. Import-side and export-side permits in one instrument -> record separately in 10.2 and 10.4 (workbook round2 Russian Federation rows 81, 84; Internal Guide p.11).
5. Export controls on e-waste -> not scored (Internal Guide p.7; Malaysia 10.1 row 79 note).

**Exemplars chosen.** China 99, India 131 (mirrors the Guide's strategic-items example), Australia 62, Russian Federation 85 (outright temporary ban), Lao PDR 76 (a single sectoral permit suffices), Indonesia 140 (raw-materials negative), Thailand 93 (absence, reviewer "Correct"), Mongolia 63 (absence). Eight economies.

**Rows excluded / suspected mislabels.**
- r1-sg-069 (Singapore row 69, 0): **likely mislabel**. The row confirms licences for military and dual-use goods under the Strategic Goods (Control) Order, "aligned with multilateral export control regimes", then scores 0 because Singapore "does not implement export restrictions on ICT goods". Guide p.76 uses strategic and dual-use export licences covering computers and telecom equipment as score-1 examples; Internal Guide p.14 captures all export licences on ITA products; the same regime type scored 1 for Australia (row 62), Malaysia (row 85), China (row 99) and India (row 131). Unless Singapore's list contains no ITA products (not shown in the sources), this should be 1.
- r2-th-094 (Thailand row 94, 1): reviewer note "Not correct", yet the measure is the Guide's own Thailand example (p.76). The impact also says export "into the Kingdom". What is "not correct" is unclear; excluded pending human check.
- r1-my-085 (Malaysia row 85, 1): score matches the Guide, but the impact opens "There is no are export restrictions related to ICT products" and reuses local-content wording. Excluded as confusing.
- r2-ru-084, r2-cn-100, r2-la-077 (1), r2-la-075, r2-la-078 (0): acceptable, not needed.

**Guide / methodology / workbook.** Guide p.76 lists the OECD Inventory on Export Restrictions on Industrial Raw Materials as a secondary source, while Internal Guide p.14 scores raw-material measures 0. Use the inventory only to locate ICT-product measures.

**Open questions.** Does a catalogue of technologies restricted from export (China row 100, intangible technology) count as "ICT goods and online services"? The workbook says yes.

---

## 11.1 Lack of transparent technical standards

**What it asks.** Whether (a) stakeholders, including foreign businesses, are barred or restricted from standard-setting in digital-trade sectors, and (b) whether transparent public consultation or engagement exists (Guide p.78). Examples: Cuba bars foreign companies from bodies that set trade norms; Egypt's NTRA board sets telecom equipment standards without foreign participation; opacity such as no consultation process or no public notice inviting input (Guide p.78).

**Criteria to scores** (Methodology sheet 11.1; Guide p.79). Binary. 1: foreigners not allowed in standard-setting bodies OR standard-setting not transparent. 0: no restriction. Weight 20% (Guide p.82).

**Polarity.** TRAP candidate (inverted polarity): a "Lack of ..." indicator. An open, consulted process scores 0; exclusion or opacity scores 1 (Guide p.79; Methodology sheet 11.1). Every workbook row is an open-process 0.

**Trap candidates.**
1. Inverted polarity (above).
2. A duty to comply with standards, obtain certification or pass testing is 11.2/11.3, not 11.1 (Guide pp.79-80). Inference from the section definitions; no host warning.
3. Adopting ISO/IEC standards, or ISO/IEC/ACCSQ membership, does not answer the 11.1 question about participation and consultation (Guide p.78). Thailand row 96 and India row 133 argue mostly from alignment. Inference.
4. Host hands-on exercise 1 (nikita_handson PDF pp.7-8) shows an AI output for 11.1 India built on IT Act s.70B (CERT-In); the host's answer is that the cited subsections do not appear in the act, i.e. hallucination or wrong retrieval. Trap candidate: cybersecurity agency powers are not standard-setting governance, and the cited section must exist.
5. Observer-only (non-voting) seats for foreign national standards bodies were not treated as exclusion (workbook round2 Russian Federation row 87). Inference: 1 needs foreign firms barred, not just limited voting for foreign standards bodies. Needs the lead's view.

**Exemplars chosen.** China 102, Russian Federation 87, Lao PDR 80, Singapore 71, Indonesia 142 (boundary), Malaysia 87. All 0 because the pool holds no other value; the spec_note records the missing score-1 exemplar.

**Rows excluded / suspected mislabels.**
- r1-au-064 (Australia row 64, 0): **possible mislabel**. A nominating organisation for Standards Australia committees must be headquartered in Australia with an Australian membership base. That limits who can nominate committee members, and Guide p.79 scores restricted foreign participation 1. Scored 0 because the process is collaborative and transparent. Human check.
- r2-in-133 (India row 133, 0): law field "Development of standards" names no instrument, and the only URL is a Business Standard news article. Fails the official-source rule (Guide p.12).
- r2-th-097, r2-th-098 (0): reviewer notes "Not correct"; row 98 is about telecom quality-of-service standards, which says nothing on participation.
- r2-th-099 (0): no timeframe and no URL.
- r2-th-096 (0): acceptable, but argues from adopting international standards.
- r2-mn-065 (0): acceptable, not needed.

**Guide / methodology / workbook.** Scoring texts agree; the workbook has no positive case to test them.

**Open questions.** Does opacity need a documented gap (no consultation provision), or is silence in the standards law enough? Guide p.12 says to cite the general law when no measure exists.

---

## 11.2 Self-certification limitations for product safety (radio transmissions, EMC/EMI)

**What it asks.** Whether suppliers' self-certification of product safety is not allowed; certification verifies that imported products meet domestic standards such as radio, EMI and EMC requirements (Guide p.79). Routes: supplier's declaration of conformity (SDoC), or third-party certification by conformity assessment bodies (CABs), with MRAs such as the ASEAN EE MRA and APEC TEL MRA giving reciprocal recognition (Guide p.79).

**Criteria to scores** (Methodology sheet 11.2; Guide p.79).
- 1: neither SDoC nor third-party certification recognised, and testing required in a local lab. The Guide also gives 1 when there is no framework or indication for accepting SDoC (see conflict below).
- 0.5: SDoC not permitted but certificates from CABs in other economies accepted (the methodology adds "from a number of countries with MRA").
- 0: SDoC permitted for foreign businesses. If SDoC is recognised for at least some ICT products, 0; if third-party certification is recognised for some products and local testing is required for others, 0.5 (Guide p.79).
- ASEAN and APEC MRA members score 0.5 or less (Internal Guide p.15).
- Weight 20% (Guide p.82). Keywords "certification" and "license"; look at technical standards and telecom equipment regulations; MRAs may hold exceptions (Internal Guide p.14).

**Trap candidates.**
1. TRAP candidate: 11.2 is certification (marking); additional testing procedures -> 11.3 (Internal Guide p.15). Local-lab testing sits in both score-1 conditions (Guide pp.79-80), and the workbook scored India's MTCTE 1 in both (rows 134, 137). Assess the certification route and the testing requirement separately.
2. TRAP candidate: MRA membership caps the score at 0.5 (Internal Guide p.15). The workbook records MRAs as rows of their own (Malaysia row 90, Indonesia row 143, Thailand row 100, India row 136 for SAARC).
3. Labelling duties (language, importer details) -> not 11.2 (workbook round2 Indonesia row 146 = 0); labelling as an import condition is 10.2 (Guide p.75).
4. Import licence or permit for equipment -> 10.2 (Guide p.75).
5. Local-entity conditions on SDoC applicants are scored inconsistently: Singapore row 72 = 0.5 (SDoC only for local registered dealers) vs Thailand rows 101, 102, 104 = 0 (applicant must be a Thai person or juristic person, or appoint a Thai representative). The Guide's 0 condition is "SDoC is permitted for foreign businesses" (p.79). Lead decision needed on whether a local-representative rule defeats it.

**Exemplars chosen.** Australia 65 and Mongolia 66 (0, SDoC accepted), Malaysia 88 (0.5, APEC MRA), Indonesia 144 (0.5, methodology wording), China 103 and Russian Federation 88 (1), India 134 (1, dual-coded with 11.3), Indonesia 146 (labelling negative). Seven economies. The inconsistent Singapore and Thailand rows were deliberately left out.

**Rows excluded / suspected mislabels.**
- r1-sg-072 (0.5) vs r2-th-101, r2-th-102, r2-th-104 (0): inconsistency above; none curated. Thailand row 101 also records that NBTC has no MRA, although Thailand is covered by the ASEAN EE MRA for TISI products (row 100).
- r2-cn-104 (China row 104, 1): network access licence requiring at least three months of network testing in China or on MIIT-designated test networks. The facts are a licence (10.2) and in-country testing (11.3); nothing about SDoC or certificates. Possibly the wrong indicator.
- r2-la-081 (Lao PDR row 81, 0.5): the row says Standard Law art.49 permits self-conformity assessment. If that covers at least some ICT products, Guide p.79 gives 0. Possible over-score; human check.
- r2-in-135 (India row 135, 0): calls the BIS Compulsory Registration Scheme an SDoC route although it requires testing at BIS-recognised labs in India. The 0 rests on that reading; human check.
- r2-in-136 (India row 136, 0.5): the SAARC arrangement is treated like an MRA; Internal Guide p.15 names only APEC and ASEAN MRAs. Acceptable by analogy; flagged.
- r1-my-089, r1-my-090, r2-id-143, r2-id-145, r2-th-100, r2-ru-089: acceptable, not needed.

**Guide / methodology / workbook.**
- Guide p.79 gives 1 when an economy has no framework for accepting SDoC, but the next sentence gives 0.5 when SDoC is refused and foreign CAB certificates are accepted. The workbook applies 0.5 (Malaysia row 88; Indonesia rows 143-145), consistent with Internal Guide p.15.
- The methodology ties 0.5 to CABs "from a number of countries with MRA"; the Guide asks only for CABs in other economies (p.79).

**Open questions.** Local-representative rules (trap 5). The "at least some products" rule versus per-row scoring (0.3).

---

## 11.3 Product screening and testing requirements

**What it asks.** Whether ICT imports must undergo screening or testing beyond standard conformity assessment before entering the market, often on national-security grounds (Guide p.80). Examples: The Gambia's local testing of audio and video products by its standards bureau; India's in-economy security testing of all telecom equipment by TEC-designated bodies; Sri Lanka's sample testing of designated goods before customs clearance (Guide p.80). Footnote 48 distinguishes these from public-safety and efficiency testing such as EMC/EMI (Guide p.80).

**Criteria to scores** (Methodology sheet 11.3; Guide p.80).
- 1: a domestic screening or testing requirement, including testing by in-country designated or country-accredited bodies (methodology: "measure in place and used for products in scope").
- 0.5: requirement in place, but third-party testing results accepted.
- 0: no requirement.
- Weight 30% (Guide p.82).

**Trap candidates.**
1. TRAP candidate: certification or marking route -> 11.2; testing procedures -> 11.3 (Internal Guide p.15).
2. TRAP candidate: national security review of foreign investment -> 3.4; of network products -> 11.3 (workbook round2 China rows 20 and 105, both citing National Security Law art.59).
3. Voluntary security manuals or frameworks -> 0 (workbook round1 Australia row 66).
4. Registration or notification of encryption products: Guide p.81 routes encryption registration and licensing to pillars 9 and 10, yet the workbook scored Russia's FSS notification 1 under 11.3 (row 90) and the same Decision's import permits 0.5 under 10.2 (row 81). Unresolved; do not promote without a lead decision.
5. EMC/EMI/RF type-approval testing: footnote 48 suggests it is not the target, but the Guide's own examples are standards-conformity tests and the workbook scores RF/EMC testing regimes 0.5 (Singapore row 73, Thailand row 103, Malaysia row 91). The workbook reading is broader than the footnote.

**Exemplars chosen.** India 137 (the Guide's example), India 138 (country-accredited in-country labs = 1), China 105 (security review), Singapore 73, Thailand 103, Mongolia 67 (0.5), Indonesia 147 (mixed case), Australia 66 (negative). Seven economies.

**Rows excluded / suspected mislabels.**
- r2-cn-106 (China row 106, 0): **suspect**. Under Cryptography Law art.26, listed commercial cryptographic products may only be sold after testing and certification by accredited institutions; art.27 adds a national security review for CII purchases. Guide p.80 scores testing by country-accredited bodies 1. Maybe scored 0 to avoid double counting with row 105, or because it concerns encryption; the row gives no reason.
- r2-ru-090 (Russian Federation row 90, 1): questionable indicator. An FSS notification is a registration step, not testing; Guide p.81 sends encryption registration and licensing to pillars 9/10.
- r1-my-092 (Malaysia row 92, 0.5): law field "Customs (Prohibition of Exports) Order P.U. (A) 117 2023" conflicts with Malaysia rows 79/80 (P.U.(A) 117 = imports order) and row 85 (P.U.(A) 122 = exports order); it also leans on used PCs and used mobile phones, which are not scored (Internal Guide p.7). Citation error.
- r2-id-148 (Indonesia row 148, 0.5): the only source is a certification company's web page (csagroup.org); no official instrument is named. Fails the official-source rule (Guide p.12).
- r1-sg-074 (Singapore row 74, 0.5): PABX security specification; the impact says nothing about testing or acceptance of outside results. Thin.
- r1-my-091 (0.5): law field is an agency name (SIRIM QAS International), and the third-party route cited is a private inspection firm. Acceptable score, weak citation.
- r2-id-149, r2-la-082, r2-ru-091: acceptable, not needed.

**Guide / methodology / workbook.**
- Guide p.80 mixed-case paragraph gives 0.5 where third-party testing is accepted for at least some products, and 1 where domestic testing is required for certain products without third-party acceptance. Both can hold for one economy. The workbook took 0.5 for Indonesia (row 147).
- Footnote 48 versus the examples and the workbook (trap 5).

**Open questions.** Which mixed-case rule wins? Is encryption product testing 11.3 or 11.4 material?

---

## 11.4 Deviation from international encryption standards (ISO, IEC, ITU, FIPS, AES, TDES, and ECC)

**What it asks.** Whether an economy adopts encryption standards that deviate from ISO/IEC-based internationally recognised standards (Guide p.80). The benchmark is ISO/IEC 18033 (encryption systems) and ISO/IEC 11770 (key management) (Guide p.81). Deviations include: algorithms not listed in ISO/IEC 18033, such as mandated domestic algorithms (listed ones include TDEA, MISTY1, CAST-128, HIGHT, AES, Camellia, SEED); block sizes below recommended minimums; symmetric keys under 128 bits; key management outside ISO/IEC 11770; disclosure of trade secrets such as source code or keys when certifying encryption products beyond ISO 19790/24759 validation (Guide p.81). Registration and licensing to use, import or distribute encryption devices are not restrictions here unless they involve those issues; they belong to pillars 9 and 10 (Guide p.81).

**Criteria to scores** (Methodology sheet 11.4; Guide p.81). Binary. 1 for any measure (the methodology adds "or known case"); 0 otherwise. Weight 30% (Guide p.82).

**Trap candidates.**
1. TRAP candidate: licensing or registration of encryption activities or devices -> 9.4 or 10.2, not 11.4 (Guide p.81; workbook round2 Russian Federation rows 77 (9.4 = 0.5) and 92 (11.4 = 0); China 10.2 rows 96, 97).
2. TRAP candidate: specific encryption required to win a public tender -> 2.2 (Guide p.19, where it scores 0.5). The Guide's scoring introduction uses this procurement example (Guide p.10).
3. TRAP candidate: payment-security standards deviating from international standards -> 12.4.3 (Guide p.85). The same RBI direction appears as 11.4 row 140 and 12.4.3 row 148 (India).
4. TRAP candidate: government power to decrypt or to order decryption -> 7.5 (Guide p.62; workbook round2 Thailand row 69 vs row 105).
5. TRAP candidate: disclosure of source code or keys tied to encryption -> 11.4, not 4.9 (Guide p.37 excludes encryption-related disclosure from 4.9). Guide p.37 nonetheless lists Malawi's rule that encryption service providers declare source code as a 4.9 example, which is internally inconsistent.
6. Domestic algorithms that became ISO/IEC standards (SM2, SM3, SM9, ZUC) -> no deviation (workbook round2 China row 107). National algorithm programmes that are optional or still allow ISO/IEC algorithms -> 0 (Indonesia row 150; Malaysia row 93). Inference: the deciding fact is a binding mandate to use an unlisted algorithm or weaker parameters.
7. A statute creating a cyber and crypto agency -> 7.2 context, not 11.4 (workbook round2 Indonesia row 80 coded 7.2).

**Exemplars chosen.** India 140 (canonical alignment), China 107, Indonesia 150 and Malaysia 93 (national-algorithm boundaries), Russian Federation 92 (licensing negative), Australia 67, Thailand 105 (7.5 boundary), Lao PDR 83 (absence). Eight economies, all 0 (no other value in the pool).

**Rows excluded.**
- r1-sg-075 (0): cites a draft reference specification issued for public comment (URL contains "draft" and "public-comment"); drafts are not enforced measures. Score 0 regardless.
- r2-in-139, r2-mn-068 (0): acceptable, not needed.

**Guide / methodology / workbook.**
- The methodology's "for any measure or known case" hints at practice evidence; the Guide asks for official laws, with the World Map of Encryption Laws and Policies and Freedom House as pointers only (Guide p.81), and Internal Guide p.8 does not list 11.4 as practice-based.
- The host name lists ITU, FIPS, AES, TDES and ECC, while the Guide benchmark is ISO/IEC 18033 and 11770 only (Guide p.81). A FIPS-based requirement is presumably aligned, but the host never says so.
- No score-1 row exists. Malaysia (MySEAL), Indonesia (BSSN Reg. 11/2024 domestic algorithms) and China (commercial cryptography) were all scored 0. If any of them binds commercial products to an algorithm outside ISO/IEC 18033, 0 is wrong; the rows argue there is no binding mandate or that the algorithms are ISO/IEC-listed.

**Open questions.** Does BSSN Reg. 11/2024 bind electronic system operators or CII operators to domestic algorithms? Indonesia row 150 says the policy "can be implemented" by them, i.e. apparently optional.

---

## Checker result

`python -X utf8 check_drafts.py g5` on 2026-09-13: **0 errors, 0 warnings**. All eight `asks` sentences matched the printed page verbatim.
`codebook_tierB.yaml` holds an empty list because no Tier B IDs are assigned to g5.

## Top concerns

1. **No positive exemplars for 11.1 and 11.4.** Both workbooks hold 13 rows for 11.1 and 11 rows for 11.4, all scored 0. The score-1 side of both binary indicators rests on Guide text alone, and several 0 rows are close calls (Australia 11.1 row 64; the Malaysia, Indonesia and China national-algorithm rows in 11.4).
2. **Row-level vs economy-level scoring.** Guide escalation rules (10.1 more than one measure, 10.2 two or more measures, 11.2/11.3 "at least some products") read as economy-level, but rows are scored per measure (Lao PDR 7 rows and India 4 rows in 10.2, all 0.5). Indonesia 10.2 rows 127 (0.5) and 131 (1) score the same pair of measures differently.
3. **Suspected mislabels.** 10.4 Singapore row 69 (dual-use export licensing = 0 against Guide p.76); 11.3 China row 106 (accredited in-country crypto product testing = 0 against Guide p.80); 10.2 Lao PDR row 67 (its note says 0, scored 0.5); 10.3 Australia row 61 (free-to-air TV quota = 1, online scope not shown); 11.1 Australia row 64 (Australia-headquartered nominating bodies = 0).
4. **Guide internal conflicts.** 11.2 "no SDoC framework = 1" vs "foreign CAB certificates accepted = 0.5" (p.79); 11.3 mixed-product rule gives both 0.5 and 1 (p.80); 11.3 footnote 48 sets aside EMC/EMI safety testing while the workbook scores RF/EMC type-approval testing; 4.9 excludes encryption disclosure yet cites Malawi's encryption source-code rule (p.37).
5. **Guide vs methodology.** 10.2 "absence of institutional transparency" as a score-1 trigger (Guide p.75, procurement wording) is absent from the methodology; the 11.2 methodology requires an MRA for 0.5, the Guide does not; the 11.4 methodology's "known case" sits uneasily with the official-source rule.
6. **Same measure, several indicators.** EAEU Decision 30 sits in 10.1/10.2/10.4/11.3; India MTCTE scores 1 in both 11.2 and 11.3; China NSL art.59 in 3.4 and 11.3. Russia's FSS encryption notification scored 1 in 11.3 contradicts Guide p.81, which routes encryption registration to pillars 9/10.
7. **Local-entity SDoC rules.** Singapore 11.2 row 72 = 0.5 vs Thailand rows 101, 102, 104 = 0 for materially similar local-applicant conditions.
8. **Evidence quality and reviewer flags.** Unexplained "Not correct" notes on Thailand rows (10.4 row 94, the Guide's own example; 11.1 rows 97, 98); rows resting on news or vendor pages (Indonesia 10.1 row 126, Indonesia 11.3 row 148, India 11.1 row 133); scope edges where e-waste or used products sit inside scored rows (Malaysia 10.2 row 80, Malaysia 11.3 row 92); the Guide's OECD raw-materials source for 10.4 (p.76) against Internal Guide p.14.
