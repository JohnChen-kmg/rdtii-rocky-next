<!-- Drafting notes for pillars 4-5 (4.01, 4.2, 4.3, 4.5, 4.6, 4.9, 4.1, 5.1-5.5, 5.7). Written 2026-09-13 by a Claude
drafting agent working from the host sources in ../sources/. Checked by the lead for structure (checker, merge,
citation audit) but NOT reviewed by a human. Row IDs: r1-/r2-<economy>-<row> = gold_id in the repo gold set. -->

# g2 notes: pillars 4 and 5 (draft 2026-09-13, pending lead and human review)

Files: `guide_refs.yaml`, `signatures_spec.yaml`, `curated.yaml` (13 IDs each), `codebook_tierB.yaml` (4.9, 5.5), this file.
Citations: Guide = RDTII 2.1 Guide, printed pages. Internal Guide = PDF pages of the Internal Guide.
Workbook rows are given as `round1/round2 <sheet> row N` plus the dump `gold_id`. "Slides" = the mentoring workshop
deck (`pdftext/slides.txt`), PDF pages.

---------------------------------------------------------------------------------------------------------

## 0. ID mapping (read first)

**Host "4.01" = the Guide's "Patent application issues"** (1st of ten pillar-4 indicators, Guide pp.29-30).
**Host "4.1" = the Guide's "Lack of effective trade secrets legal framework"** (10th pillar-4 indicator, Guide pp.37-38).

How this was confirmed:
- Methodology `category` and Indicator Reference `name` for "4.01" both read "Patent application issues";
  for "4.1" both read "Lack of effective trade secrets legal framework".
- Workbook rows tagged 4.01 all deal with patent filing (local agents, foreign-filing permission, translation),
  e.g. round1 Malaysia row 22, round2 China row 23. Rows tagged 4.1 deal with trade secret protection,
  e.g. round1 Singapore row 23, round2 Thailand row 32. In each economy sheet the 4.1 rows follow the 4.9 row
  (one exception, noted below).
- The slides call the Singapore trade-secret case "4.10" (Slides p.11), i.e. the Guide's own numbering.
- One exception inside the host data: round2 Indonesia row 35 (r2-id-035) carries ID 4.1 but is a
  patent-application row; it sits directly before the 4.01 row 36. See 4.01 and 4.1 below.

| Host ID | Guide position and heading (printed page) | Methodology row (R1/R2 DB) | Template row | Guide weight |
| :-- | :-- | :-- | :-- | :-- |
| "4.01" | 1st: Patent application issues (p.29) | 15/15 | 17 | 14% |
| "4.2" | 2nd: Patent enforcement issues: civil and administrative procedures, and provisional measures (p.30) | 16/16 | 18 | 6% |
| "4.3" | 3rd: Patent enforcement issues: others (p.31) | 17/17 | 19 | 8% |
| 4.4 | 4th: Not in the WIPO PCT (p.32), non-regulatory, not drafted | none | none | 6% |
| "4.5" | 5th: Lack of a copyright framework and exceptions (p.33) | 18/18 | 20 | 14% |
| "4.6" | 6th: Online copyright enforcement issues: civil and administrative procedures and provisional measures (p.34) | 19/19 | 21 | 6% |
| 4.7, 4.8 | 7th, 8th: Not in the WCT (p.34) / WPPT (p.35), non-regulatory, not drafted | none | none | 6%, 6% |
| "4.9" | 9th: Mandatory disclosure of trade secrets (p.37) | 20/20 | 22 | 22% |
| "4.1" | 10th: Lack of effective trade secrets legal framework (p.37) | 21/21 | 23 | 14% |
| "5.1" | 1st: Lack of passive infrastructure sharing (p.41) | 23/23 | 25 | 15% |
| "5.2" | 2nd: Foreign equity limits in telecom sector (p.42) | 24/24 | 26 | 29% |
| "5.3" | 3rd: Shares owned by the Government (p.42) | 25/25 | 27 | 15% |
| "5.4" | 4th: Lack of functional/accounting separation (p.43) | 26/26 | 28 | 15% |
| "5.5" | 5th: Licensing requirements in telecom sector (p.44) | 27/27 | 29 | 15% |
| 5.6 | 6th: Not in the WTO Telecom Reference Paper (p.45), non-regulatory, not drafted | none | none | 6% |
| "5.7" | 7th: Lack of independent telecom authority (p.46) | 28/28 | 30 | 6% |

Weights are informational, as printed (Guide p.38: pillar 4 figures sum to 102%; Guide p.46: pillar 5 figures sum to 101%).
Non-regulatory 4.4, 4.7, 4.8 and 5.6: Internal Guide p.8; Non-regulatory note p.1.

**Internal Guide FAQ numbering is not reliable; match by topic.** Internal Guide p.11 calls telecom foreign
equity "Pillar 5.1" and e-commerce "12.1" (older numbering), while p.12 uses "5.2". The p.12 answer labelled
"4.2 (Patent enforcement)" is about TRIPS Art.31 compulsory licences, which the 2.1 Guide discusses under
"Patent enforcement issues: others" (host 4.3, Guide p.31). The p.12 answer labelled "4.5 (Copyright privacy)"
is about piracy rates. I applied each FAQ answer by topic and flag the numbering where it matters.

## 1. Leads from the brief: verification

| Lead | Status |
| :-- | :-- |
| Internal Guide p.12, 4.2: TRIPS Art.31-consistent exceptions are not restrictions | Text verified. By topic it belongs to host 4.3 (Guide p.31); used there. |
| Internal Guide p.12, 4.5: high piracy rate despite a copyright law gives 1 | Text verified. Contradicted by workbook practice (see 4.5); not written into rules. |
| Internal Guide p.12, pillar 5: ITU Datahub only a guide to the official law | Verified (answer says always use secondary sources as a guide to the official law). Host-wide, not repeated in YAML. |
| Internal Guide p.12, 5.2: caps on private companies and SOEs in telecom | Verified. |
| Internal Guide p.12, 5.3: government-held shares, not caps; market reports, SOE lists | Verified (also: list company names and percentages). |
| Internal Guide p.12, 5.5 vs 9.4: ISP/ICP licences are 9.4 | Verified. |
| Internal Guide p.13, 5.7 | Verified: the law establishing the regulator or the Telecommunications Act determines independence. |
| Internal Guide p.8: 5.3 practice-based | Verified (3.4, 5.3, 9.1). |
| Assignment 2 brief, optional 5.3 India case | Verified in the corrected `assign2.txt` (01:36), p.2. The first copy of that file held the Assignment 1 answer key; nothing in these drafts was based on it. The same case is on Slides pp.55 and 58. |
| 4.4, 4.7, 4.8, 5.6 out of scope | Verified; not drafted. |

Slides and the Assignment briefs are not in the checker's citation whitelist, so YAML rule lines cite the Guide,
Internal Guide, methodology or workbook rows; slide and brief references stay in these notes.

---------------------------------------------------------------------------------------------------------

## 2. Per-indicator notes (host order)

### "4.01" Patent application issues

**What it asks.** Whether there is a restriction on the patent application process and of what type; it covers
differential treatment of local and foreign applications and measures applied to both (Guide p.29).

**Criteria and scores.**
- 1: methodology criterion 1 = differential treatment of local and foreign firms, a local representative
  requirement, or discriminatory rejection. Guide p.30 = a local representative requirement or discriminatory rejection.
- 0.5: methodology criterion 2 = non-transparent process, high filing fees, high registration costs, substantive
  examination, filing locally before filing abroad. Guide p.30 = procedural requirements such as filing locally first.
- 0: no restriction.
- The Guide also lists restriction types without assigning a score: translation into an official language
  (Kyrgyzstan) and local registration of foreign patents (Nepal) (Guide pp.29-30). Inference only: translation reads
  as procedural (0.5); Nepal-type registration looks closer to differential treatment (1). Needs a host ruling.
- "Substantive examination" in methodology criterion 2 would put almost every patent system at 0.5; no row scores on it.

**Confusions (trap candidates).**
- 4.01 vs 4.1: ID hazard, see r2-id-035 below.
- 4.01 vs 4.3: a local agent for enforcement-related matters is the Guide's low-impact 4.3 example (0.5, Guide p.31);
  a local agent for filing is 4.01 at 1 (Guide p.30). China's Patent Law Art.18 covers applications "or other
  patent-related matters" and is coded 4.01 = 1 (round2 China row 23) and 4.3 = 0 (round2 China row 25).
- Pre-filing security or secrecy clearance (China Art.19, Russia Civil Code Art.1395, Singapore s.34, India s.39,
  Malaysia s.23A) is the Guide's procedural type (Guide p.30), not a national-security trade secret disclosure (4.9).
- A patent agent or address-for-service rule is 4.01, not a general commercial presence requirement (3.5). Inference
  from the Guide's Bhutan example (Guide p.29).

**Exemplars and why.** Malaysia 22, China 23, Russian Federation 25, Lao PDR 20, Thailand 25 (local agent or
representative, 1); Australia 18 (absence row, 0); India 34 (easing amendments, negative 0). Five economies at 1 show the
same clause across patent acts, an IP law, a civil code and a ministerial regulation. The pool has no clean example of the
methodology's other score-1 branch (differential treatment); see Thailand 24 below.

**Rows flagged.**
- r2-id-035 (round2 Indonesia row 35): tagged 4.1, but the content is Regulation No.38/2018 on Patent Applications (PCT
  local representation, fees, Bahasa Indonesia translation, priority). It belongs to 4.01 (Guide p.29 vs pp.37-38). As a
  4.1 row, its score of 1 says Indonesia lacks trade secret protection, which contradicts round2 Indonesia row 42
  (Trade Secret Law 2000, score 0). Any gold set built on the dump label inherits this error.
- r1-sg-016 (round1 Singapore row 16): scored 1, but the evidence is only a pre-filing requirement for residents and an
  English-language rule, both procedural (Guide p.30 gives 0.5). No local representative rule is cited.
- r2-in-035 (round2 India row 35): CSIR IP management policy 1996, sourced from a csir.org.gh URL (Ghana's CSIR domain).
  An institutional IP policy is not a restriction on the application process. Score 0 is harmless; evidence unusable.
- r2-id-036 (round2 Indonesia row 36): score 1 plausible, but the text says a local consultant is mandatory only if the
  applicant uses a representative; not used.
- r2-th-024 (round2 Thailand row 24): scored 1 on Patent Act s.14, which limits applicants to Thai nationals or
  headquarters, nationals of treaty partners, reciprocity countries, or persons domiciled in Thailand or a treaty country.
  This is treaty-based national treatment of the Paris Convention kind. Guide p.31 fn 14 notes that different treatment
  of foreign applicants would usually mean the economy is outside the Paris Convention or the WTO, which it calls very
  rare. Debatable as differential treatment; not used, so that standard eligibility clauses are not taught as score 1.

**Guide / methodology / workbook disagreements.** The pool is 10 rows at 1 and 3 at 0; no 0.5 row exists, so the
procedural band has no example. The only procedural-only row (Singapore 16) was scored 1.

**Open questions.** Score for translation-only rules; Nepal-type validation; the "substantive examination" criterion;
row-level score when one act has both a 1-type and a 0.5-type rule (host practice: one row at the higher score, e.g.
Malaysia 22, China 23, Russian Federation 25, India 33).

### "4.2" Patent enforcement issues: civil and administrative procedures and remedies; and provisional measures

**What it asks.** Whether the patent legal framework incorporates (a) civil and administrative procedures and (b)
provisional measures, following TRIPS Arts 42-49 and 50 (Guide p.30). General laws such as civil codes and procedure
laws count (Guide p.30). Footnote 12 defines civil procedures, administrative procedures (a government agency or IP
enforcement body) and provisional measures (urgent temporary orders to stop infringement or preserve evidence) (Guide p.30).

**Criteria and scores.** Both elements: 0; one: 0.5; neither: 1 (Guide p.31; Methodology sheet 4.2). Absence-based
polarity (as in policies.yaml). The reference and methodology names add "and remedies"; the Guide heading does not.

**Confusions (trap candidates).**
- 4.2 vs 4.6: identical test, patents vs copyright (Guide pp.30, 34). One civil procedure code can evidence both.
- 4.2 vs 4.3: compulsory licences and government use are 4.3 matters (Guide p.31). Read the Internal Guide p.12 FAQ
  labelled "4.2" as 4.3.
- "Provisional protection" of a published application (compensation for use before grant) is not a TRIPS Art.50
  provisional measure (Guide p.30 fn 12): round2 Russian Federation row 26 cites Civil Code Art.1392 as its provisional
  measure; round2 Lao PDR row 21 cites Art.84 (provisional protection tied to breeder's rights) and Art.137 border
  inspection.
- Criminal penalties alone show neither element: round2 Thailand row 26 cites only the offences chapter (ss.81-88).

**Exemplars and why.** Indonesia 37 (explicit court provisional determinations matching Art.50 functions), India 36
(temporary injunctions under the Civil Procedure Code: general law counts), China 24 (administrative, civil and evidence
preservation), Malaysia 23, Mongolia 16. All score 0; nothing else exists.

**Rows flagged (evidence quality, not score).** r2-th-026 (criminal offences only; note says "Correct"); r2-ru-026
(misidentified provisional measure); r2-la-021 (same issue; its note says it is based on the 2017 law replaced in 2024);
r1-sg-017 (no provisional measure cited). The 0 scores may be right in substance, but these rows do not evidence (b).

**Thin data.** 10 rows, all 0: no example of 0.5 or 1.

### "4.3" Patent enforcement issues: others

**What it asks.** Whether there is a restriction on patent enforcement and its scope (Guide p.31).

**Criteria and scores.** Methodology: 1 = high-impact restriction affecting all circumstances and sectors, or more than
one category-2 measure; 0.5 = limited impact, one circumstance or sector; 0 = none. The Guide adds examples of scored
measures (terms of protection discriminating against foreign applicants, fn 14; state intervention restricting patent
holders' rights) and names a local agent for enforcement-related matters as the low-impact 0.5 case (Guide p.31).

**Exception.** Exceptions allowed by TRIPS Arts 30, 31 and 31bis, including compulsory licences and government use with
adequate remuneration, are not restrictions (Guide p.31; Internal Guide p.12, labelled "4.2"). The methodology criteria
do not mention this exception.

**Confusions (trap candidates).** 4.3 vs 4.01 (agent at filing vs enforcement stage); 4.3 vs 4.2; TRIPS-consistent
compulsory licensing (all three such rows correctly 0: Lao PDR 22, Russian Federation 27, Thailand 27); local working
requirements (Indonesia 38).

**Exemplars and why.** Lao PDR 22, Russian Federation 27, Thailand 27 (TRIPS exceptions, 0); Indonesia 38 (local working
duty satisfiable by import or licence, boundary 0); Malaysia 24 (five-year limitation period, boundary 0; its note says
0 or 0.5 are both arguable); Singapore 18 (absence row).

**Rows flagged.**
- r2-cn-025 (round2 China row 25): the only evidence is Patent Law Art.18 (foreigners without an establishment must use a
  patent agency for applications or other patent-related matters). Guide p.31 names exactly this kind of local-agent rule
  as the low-impact 0.5 example. The host scored 0 and the note cites "recent practical evidence" of good enforcement, a
  de facto reason on a de jure indicator. Likely should be 0.5.

**Thin data.** 10 rows, all 0.

**Open questions.** Is a local-working obligation backed by compulsory licences a restriction when importing does not
count as working? Is a statutory limitation period a restriction (Malaysia 24 note)?

### "4.5" Lack of copyright framework and exceptions

**What it asks.** Whether a copyright legal framework exists and which type of exceptions it adopts (Guide p.33).
**TRAP: inverted polarity.** A clear exception regime scores 0; no framework or no exceptions scores 1.

**Criteria and scores.** Methodology: 1 = no framework or no exceptions; 0.5 = unclear exceptions such as the three-step
test and other types; 0 = clear exceptions following fair use or fair dealing. Guide p.33: fair use is a flexible
case-by-case test (four factors); fair dealing is an exhaustive list of purposes plus a fairness requirement (e.g.
attribution); the three-step test alone creates uncertainty; closed lists such as Indonesia's (non-commercial education,
research, personal use, public interest, review) and the Marshall Islands' are "other forms" at 0.5. Guide p.10 lists fair
use and fair dealing among widely recognised norms.

**Decision point for coders.** The line between fair dealing (0) and a closed list (0.5) is a fairness requirement or
fairness factors. A bare enumerated list, with or without a three-step chapeau, is 0.5 under the Guide.

**Internal Guide p.12 FAQ conflict.** The FAQ labelled "4.5 (Copyright privacy)" says a high piracy rate despite a
copyright law gives 1.0. Against it:
- No 4.5 or 4.6 row in the workbooks is scored on piracy. Round2 Thailand row 29 (4.6) notes a change to a "de jure
  approach" with the score moved from 1 to 0. Round2 Mongolia row 19 (4.6) reports that at least 85% of the domestic
  market uses pirated software, yet scores 0.
- The host-wide rule is enforced measures from official sources (Internal Guide p.8), and the mapping pipeline reads
  legislation, not piracy statistics.
- The FAQ numbering is unreliable (section 0), so the answer may have been meant for online enforcement (4.6).
I did not put a piracy rule into the YAML. This needs a host decision.

**Confusions (trap candidates).** 4.5 vs 4.6 (exceptions vs enforcement); 4.5 vs 8.1 (intermediary safe harbour for
copyright, Guide pp.64-65); anti-circumvention and rights-management exceptions belong to the WCT/WPPT discussion
(Guide p.36, non-regulatory 4.7/4.8); patent exceptions (4.3).

**Exemplars and why.** Indonesia 39 (the only 0.5 row; matches the Guide's Indonesia example); Australia 21, Malaysia 25,
Singapore 19, India 38 (fair dealing or fair use, 0); Lao PDR 23 (statute labels its list "fair use" and calls for an
overall assessment, boundary 0).

**Rows flagged (Guide vs workbook).**
- r2-cn-026 (round2 China row 26): Art.24 is an exhaustive list of 13 cases plus a catch-all pointing to other laws;
  courts partly apply the three-step test. Guide p.33 suggests 0.5; host 0 (note: the 2020 amendment made exceptions clearer).
- r2-mn-018 (round2 Mongolia row 18): a three-step-type chapeau (Art.38) plus purpose-specific Arts 39-46; the row calls it
  "a clear fair use regime" and scores 0; Guide suggests 0.5.
- r2-ru-028 (round2 Russian Federation row 28): enumerated free uses (Civil Code Arts 1273-1280); host 0; Guide's closed-list
  logic suggests 0.5 unless the attribution and purpose conditions are read as fair dealing.
- r2-th-028 (round2 Thailand row 28): s.32 para 1 is the three-step test and para 2 an enumerated list; host 0 (Thai
  practice calls it fair use); Guide suggests 0.5.
- r2-in-039 (round2 India row 39): a ministry press release on AI-generated works; a policy statement, not a law. Not used.

**Thin data.** One 0.5 row, no score-1 row.

### "4.6" Online copyright enforcement issues: civil and administrative procedures and remedies; and provisional measures

**What it asks.** Whether copyright legal frameworks incorporate (a) civil and administrative procedures and (b)
provisional measures, following TRIPS Arts 42-50; general laws count (Guide p.34). Absence-based polarity.

**Criteria and scores.** Same as 4.2 (Guide p.34; Methodology sheet 4.6). The Guide's scoring sentence on p.34 says
"legal framework concerning patents", a copy error from 4.2; read it as copyright. The weights text says this indicator
"partially focuses on online materials" (Guide p.38), but the defining sentence does not require online-specific tools;
host rows accept general copyright remedies.

**Confusions (trap candidates).**
- 4.6 vs 8.1: notice-and-takedown clauses appear in both. Takedown as a right-holder remedy supports 4.6; conditions that
  exempt intermediaries from liability are 8.1 (Guide p.65). Inference: record both when one provision does both.
- 4.6 vs 9.1: blocking or filtering for IP infringement is not a 9.1 restriction (Guide p.70), but court blocking orders
  are 4.6 enforcement evidence (round1 Singapore row 21; round2 Thailand row 30).
- 4.6 vs 4.5; piracy statistics (see 4.5).

**Exemplars and why.** Malaysia 26 (takedown with counter-notice, injunctions), Singapore 21 (court orders disabling access
to online locations, takedown notices), China 27 (civil, administrative and pre-suit preservation measures), Russian
Federation 29 (compensation, injunctions including blocking), Thailand 29 (de jure switch from 1 to 0), India 40 (dynamic
injunctions; case law as an official source). All 0.

**Rows flagged.**
- r2-in-041 (round2 India row 41): the law column names the "Cinematograph (Amendment) Bill" although the text says the Act
  was passed on 4 August 2023. Cite the enacted Act. Not used.
- r2-mn-019 (round2 Mongolia row 19): piracy evidence with score 0; fine under a de jure reading, conflicts with the FAQ.
- r2-la-024 (round2 Lao PDR row 24): the note says Lao PDR lacks takedown procedures and online rules; the 0 rests on
  general IP enforcement. Consistent with the Guide text; shows the "online" ambiguity.

**Thin data.** 13 rows, all 0.

### "4.9" Mandatory disclosure of trade secrets, such as source code and algorithms (Tier B)

**What it asks.** Whether a Government mandates the disclosure of trade secrets such as source code and algorithms
(Guide p.37). Highest pillar-4 weight, 22%, because disclosure undermines the exclusive right (Guide p.38).

**Criteria and scores.** See the codebook block: safeguards first, then scope (specific products or circumstances = 0.5;
entire sector or horizontal, or more than one limited measure = 1). National-security disclosures score 0.5 or 1 by scope
(Guide p.37 fn 22). Name: the reference and methodology spell "souce code"; the spec and codebook `name` fix the typo,
`category_official` keeps it so it matches the sheet.

**Tensions inside the Guide.**
1. Carve-outs vs examples. Guide p.37 says disclosure tied to procurement (Pillar 2) or encryption (Pillar 11) is not
   covered, yet its own examples include Malawi's encryption service providers declaring source code and Indonesia's escrow
   for custom-made software, which is also the Guide's 2.2 example (Guide p.19).
2. The Pillar 11 carve-out. 11.4 covers disclosure of source code or keys when certifying encryption products (Guide p.81).
   Lawful-access decryption duties are not certification, so the carve-out does not clearly reach them.
3. Methodology vs Guide. Methodology criterion 2 lists "disclosure due to court order, regulatory proceedings" as 0.5; the
   Guide says disclosure with safeguards against unfair commercial use is not scored. The Guide's Solomon Islands
   (proceedings, no further disclosure) and Turkmenistan (authorities' access, no further disclosure) examples both have
   safeguards and would score 0 under the Guide's own rule.

**Workbook practice.**
- All rows above 0 sit on a carve-out: decryption-assistance duties (round2 India row 42 = 1; round2 Russian Federation
  row 30 = 1), procurement source code (round2 Indonesia row 41 = 0.5) and a general security-assistance duty (round2 China
  row 28 = 0.5).
- The same provisions are also coded elsewhere: India IT Act s.69 as 7.5 (round2 India row 98 = 1); Russia's decryption
  duty as 7.5 (round2 Russian Federation row 58 = 1); Malaysia CPC s.116B as 7.5 = 1 (round1 Malaysia row 64) but 4.9 = 0
  (round1 Malaysia row 27); Indonesia's source-code rule as 2.2 = 1 (round2 Indonesia row 10). One measure may sit under
  several indicators (Guide p.11; Internal Guide p.11; Assignment 1 answer key p.3).
- Malaysia row 27 (warrant-based police access to passwords and decryption codes) = 0, while methodology criterion 2
  would give court-ordered disclosure 0.5.
- China row 28 cites Cybersecurity Law Art.28, which applies to all network operators (arguably sector-wide, so 1 under
  methodology criterion 1) and is an assistance duty with no explicit disclosure of code or algorithms.

**How the codebook handles this (draft choice, needs review).** Procurement disclosure goes to 2.2 and
encryption-certification disclosure to 11.4 (exceptions, Guide p.37 and p.81). Lawful-access decryption duties are recorded
here, citing the host rows, and also under 7.5. Judicial oversight is a review case.

**Confusions (trap candidates).** 4.9 vs 4.1 (protection vs mandate; Lao PDR row 25 reuses the trade secret articles for 4.9
and is correctly 0); 4.9 vs 2.2; 4.9 vs 11.4; 4.9 vs 7.5; algorithm filing (China row 28 note); general inspection powers
under enforcement acts (Malaysia Trade Descriptions Act ss.34-35, cited in Malaysia row 27).

**Exemplars and why.** Thailand 31 (safeguards, not scored), Australia 23 (absence), Lao PDR 25 (4.1 look-alike), Indonesia
41 (2.2 boundary, 0.5), China 28 (national security, 0.5), India 42 and Russian Federation 30 (decryption duties, 1, with the
7.5 overlap in the notes). The two score-1 rows are kept because host coders treat these duties consistently as 4.9.

**Rows flagged.** r1-my-027 (score vs methodology criterion 2); r2-cn-028 (scope arguably horizontal; weak disclosure
evidence); r2-id-041 (double-coded with 2.2 against Guide p.37); r2-in-042 and r2-ru-030 (tension with the encryption
carve-out).

**Open questions.** (1) Should lawful-access decryption duties be 4.9 at all, or only 7.5? (2) Does judicial authorisation
count as a safeguard? (3) Is a duty on all network operators horizontal (1) or aimed at certain companies (0.5)?

### "4.1" Lack of effective trade secrets legal framework

**What it asks.** Whether the economy has adopted a trade secrets legal framework providing effective protection (Guide
p.37): confidential business information protected against unauthorised acquisition, use or disclosure by enforceable
provisions or established common-law principles, with remedies such as injunctions, damages and, where applicable,
criminal sanctions (Guide p.37). In common-law systems case law on breach of confidence can suffice; Singapore is the
example (Guide p.38). Acts, provisions, clauses and common-law doctrine all count (Guide p.38).
**TRAP: inverted polarity** (effective protection scores 0) and **ID hazard** (host "4.1" is not "4.01").

**Criteria and scores.** Methodology: 1 = no framework able to provide effective protection; 0.5 = limited practice or
scope, OR "practices with certain clauses included in the IP law / relevant law"; 0 = effective protection in any form.
Guide p.38: 0.5 when the framework is more limited in scope or only partially enforced (narrow provisions without
comprehensive coverage); 0 when effective protection exists in any form.

**Tension.** Methodology criterion 2 places clause-based protection at 0.5, while the Guide accepts clauses as a valid form
and scores effectiveness and coverage, not legal form. Slides p.10 adds that in China cases do not count as legal sources,
so Chinese protection must be statutory (round2 China row 29 is).

**Workbook inconsistency on common-law protection.**
- r1-au-024 (round1 Australia row 24) = 0.5 and r1-my-028 (round1 Malaysia row 28) = 0.5: equitable or common-law breach of
  confidence plus statutory clauses.
- r1-sg-023 (round1 Singapore row 23) = 0 and r2-in-043 (round2 India row 43) = 0: the same common-law basis.
- Guide p.38 uses Singapore's breach-of-confidence protection as the model of effective protection, which supports 0 for
  Australia too. The Malaysia row argues its own protection is limited, which the methodology's criterion 2 could support.
  Neither row is used as an exemplar.

**Other rows flagged.**
- r2-id-035: mis-tagged patent-application row (see 4.01); the pool's only score-1 row.
- r2-id-042 (round2 Indonesia row 42): score 0, but its note cites secondary sources "supporting the classification ... as
  having a limited practice/scope", i.e. 0.5. Score and note disagree. Not used.
- r2-in-044 (round2 India row 44): relies on a press release about the IPR Policy 2016. Not used.
- r2-la-026 (round2 Lao PDR row 26), 0.5: used as the boundary exemplar because it matches methodology criterion 2, but the
  IP-law clauses include rights to sue and claim compensation, which could meet the Guide's effectiveness test (0).

**Confusions (trap candidates).** 4.1 vs 4.9 (see above); 4.1 vs 7.1 (personal data protection is not trade secret
protection); officials' confidentiality duties (Anti-Unfair Competition Law Art.15, cited in round2 China row 28's note)
are safeguard evidence for 4.9.

**Exemplars and why.** Singapore 23 (common law, the Guide's example), Thailand 32 (dedicated act with remedies), China 29
(scattered statutes incl. criminal law), India 43 (equity and case law), Russian Federation 32 (federal law) at 0; Lao PDR 26
(clauses in the IP law, boundary 0.5).

**Thin data.** No valid score-1 row.

### "5.1" Lack of passive infrastructure sharing

**What it asks.** (a) whether there is an obligation for passive infrastructure sharing and (b) whether the approach is
mandatory or voluntary (Guide p.41). Passive = non-electronic infrastructure such as buildings, sites, cabinets, towers,
poles, ducts and trays; active sharing (radio access network, core network) is different (Guide p.41 fn 28).
**TRAP: inverted polarity** (a sharing mandate scores 0).

**Criteria and scores.** Methodology: 1 = no obligation; 0.5 = not mandated but practised; 0 = mandated. Guide p.42: 1 =
no obligation; 0.5 = not mandated but practised, **or mandated case by case**; 0 = at least one mandated obligation. Guide
p.42 also gives a two-step check (obligation? mandatory or voluntary?). The methodology lacks the case-by-case clause.
Guide examples (p.41): Thailand mandated; Pakistan, Vanuatu, Hong Kong (China) voluntary but implemented; New Zealand
voluntary co-location framework; Australia mandated on request for declared services.

**Confusions (trap candidates).**
- Active or spectrum sharing presented as passive sharing (round2 India rows 47-48).
- Interconnection presented as passive sharing (round2 China row 31 cites interconnection and unbundled network elements for
  dominant providers).
- Consultation documents used as the source (round2 India row 48: TRAI consultation paper; round1 Malaysia row 30: Public
  Inquiry Report). Not enforced measures.
- 5.1 vs 5.4 (duties on SMP operators); 5.1 vs 6.3 (data-centre establishment).

**Exemplars and why.** Thailand 34 (the Guide's example), Indonesia 44 (statutory mandate), Mongolia 24 (regulator
resolution), Singapore 26 (code of practice), Russian Federation 34 (decree) at 0; Australia 26 (on-request access, 0.5).

**Rows flagged.**
- r2-in-047 (round2 India row 47): scored 0, but its note says infrastructure sharing "is not mandatory", only enabled under
  the Unified License; the clauses cited permit active sharing. Guide p.42 gives 0.5 if practised, otherwise 1.
- r2-in-048 (round2 India row 48): scored 0 on a spectrum-sharing permission (Telecommunications Act 2023 s.8(2)) and a TRAI
  consultation paper that recommends passive sharing. Neither is a passive sharing mandate.
- r2-cn-031 (round2 China row 31): interconnection duties cited as the mandate. The 0 may be right, but the row does not show it.
- r1-my-030 (round1 Malaysia row 30): the operative instrument is the Mandatory Standard on Access; the row cites a report.
- r2-la-028 (round2 Lao PDR row 28): cites the 2011 Telecom Law while its note says a 2021 law replaced it (not yet
  implemented). Repealed-law risk.
- r2-mn-023 (round2 Mongolia row 23): 0.5 rests on a pending regulation and active 5G sharing; Mongolia row 24 already shows
  a mandate.

**Thin data.** No score-1 row.

### "5.2" Foreign equity limits in telecom sector

**What it asks.** The maximum foreign equity share in telecommunications, in private companies and in fully or partially
state-owned companies (Guide p.42; Internal Guide p.12).

**Criteria and scores.** Methodology: 1 = ban, or minority stakes in more than one measure; 0.8 = minority stake (1-50%);
0.5 = controlling stake (51-99%) or restrictions only on SOEs; 0 = full ownership allowed. The Guide mirrors this with
minority = less than 50% and controlling = more than 50% (Guide p.42). A cap of exactly 50% (China's value-added cap,
round2 China row 32) is minority under the methodology's 1-50% band.

**Scope sources.** Pillar 5 is basic and value-added telecom, not broadcasting (Guide p.40). Pillar 5 captures telecom-specific
foreign ownership limits; screening (3.4) and commercial presence (3.5) stay in Pillar 3 (Guide p.11). Telecom and
e-commerce caps are excluded from 3.1, and caps under a horizontal framework are recorded only under 3.1 to avoid
double-counting (Guide p.25); broadcasting FDI caps go to Pillar 3 (Guide p.25 fn 9). Indicator Reference note for 3.1
restates the exclusion.

**Conflict.** Internal Guide p.11 says licensing and foreign equity for telecom include broadcasting, radio frequencies and
VoIP. That contradicts the Guide on broadcasting (p.25 fn 9; p.40). The workbooks follow the Guide: broadcasting caps are
coded 3.1 (round1 Malaysia row 12; round2 Indonesia row 25; round2 Thailand row 15; round2 Russian Federation row 12;
round2 India row 22).

**"More than one measure" in practice.** One act with several capped licence types counts as one measure: round2 Thailand
row 35 (note: changed from 1 to 0.8), round2 China row 32 (49% basic and 50% value-added in one article, 0.8).

**Double-coding with 3.1 (contrary to Guide p.25).**
- A telecom cap coded under 3.1: round1 Malaysia row 13 (3.1 = 0.5) repeats Malaysia row 32 (5.2 = 0.5). The 3.1 copy is
  the misplaced one.
- Horizontal SOE rules coded under both: round2 Indonesia row 48 (5.2) = row 26 (3.1), both 0.5; round2 Russian Federation
  row 36 (5.2) = row 15 (3.1), both 0.5; round2 Thailand row 36 (5.2) = row 14 (3.1), both 0.5; round2 China row 33 (5.2)
  = row 13 (3.1), both 0.

**Confusions (trap candidates).** 5.2 vs 3.1; 5.2 vs 12.01 (Guide p.84); 5.2 vs 3.4 (approval thresholds: Singapore 27,
Russian Federation 35); 5.2 vs 5.3 (Internal Guide p.12); 5.2 vs 5.5 (licence eligibility tied to foreign shareholding is
also scored 5.5: Malaysia 35, Thailand 39).

**Exemplars and why.** Australia 27, Thailand 35, China 32 (0.8); Malaysia 32 (0.5); Singapore 27, India 49 (0); Russian
Federation 35 (negative: horizontal screening is not a telecom cap).

**Rows flagged.**
- r2-id-049 (round2 Indonesia row 49): 0.5 for a 67% cap on ISPs and application service providers attributed to a
  Regulation No.13/2021 whose title (technical standards for LTE/IMT-2020 equipment) does not match the content; it
  contradicts round2 Indonesia row 46 (Presidential Regulation 10/2021 opened these lines to 100%).
- r2-ru-036 (round2 Russian Federation row 36): a minimum state holding (25% plus one share) in joint-stock companies
  receiving state assets. Not a foreign equity cap; horizontal (also 3.1 row 15).
- r2-th-036 (round2 Thailand row 36): note says "Not correct"; the cited section only defines "state enterprise";
  horizontal (also 3.1 row 14).
- r2-id-048 (round2 Indonesia row 48): horizontal SOE cap (SOE law plus a postal regulation), duplicate of 3.1 row 26. It is
  the only SOE-only 0.5 pattern, so that clause of the scoring rule has no clean exemplar.
- r2-id-047 (round2 Indonesia row 47): score 0 is right, but the evidence is a 67% tower cap the row says was later removed.

**Thin data.** No score-1 row (no ban, no multi-measure minority caps).

### "5.3" Shares owned by the Government in telecom companies

**What it asks.** The percentage of shares the Government owns in telecom companies, including SOE operators (Guide p.42).
Practice-based: enforcement and practice evidence and secondary sources are admissible (Internal Guide p.8; Slides pp.8-9).

**Criteria and scores.** 1 = government ownership above 50% in at least one company, or 1-50% in more than one company; 0.5
= 1-50% in one company; 0 = no government shares (Guide p.43; Methodology sheet 5.3).

**Evidence the indicator needs.** Telecom market reports, annual updates by the regulator or government, official company
websites (Guide p.43). The latest telecom market report or an SOE list (e.g. a Ministry of Finance site); list every
government-owned telecom company with its percentage (Internal Guide p.12). The Assignment 2 brief's India case (p.2):
record company name, ownership percentage, source and timeframe; primary sources are official government or regulator
materials; supporting materials are annual reports, company websites and official ownership records; the answer combines
legal analysis with factual verification (also Slides p.58). Market share is to be identified too (Guide p.42), but it does
not enter the score.

**Market structures in the Guide (pp.42-43).** De jure monopoly (Turkmenistan), de facto monopoly, ownership through a foreign
SOE (the Kiribati operator owned by a Fiji state-majority company), partial ownership without dominance (Thailand), several
competing SOEs (China).

**Row level vs economy level.** Rows score single companies: round2 India rows 50 (BSNL, 100%) = 1, 51 (MTNL, 56.25%) = 1,
52 (Vodafone Idea, 23.15%) = 0.5; India's economy score is 1. Rows are added per measure found (Format requirements p.4).

**Confusions (trap candidates).** 5.3 vs 5.2 (Internal Guide p.12); temporary state control of networks (round2 Lao PDR row 30
cites Telecom Law Arts 44-45) is not ownership; postal SOEs (round2 Mongolia row 26 lists Mongolian Post) are not telecom;
regulator-operator links belong to 5.7 (Guide p.46).

**Exemplars and why.** China 34 (the Guide's multiple-SOE example), Australia 28 (statutory 100% ownership), Singapore 28
(indirect ownership through Temasek, boundary), Indonesia 50, Thailand 37 (regulator market report as evidence) at 1; India 52
and Russian Federation 37 at 0.5.

**Rows flagged.**
- r1-my-033 (round1 Malaysia row 33): scored 0.5, but lists government-related stakes of 1-50% in four companies (Telekom
  Malaysia 45.58%, CelcomDigi 7.55%, Maxis 11.48%, Digital Nasional Berhad 35%). Guide p.43 gives 1 for more than one company
  in that band, unless the state funds listed (Khazanah, AmanahRaya Trustees, KWAP, PNB) are not "Government". The Guide does
  not define indirect ownership.
- r2-in-052 (round2 India row 52): the note says the Government's Vodafone Idea stake is 48.99% as of 9 April 2025, the impact
  text says 23.15% (July 2024). Still 0.5; the timeframe needs updating.
- Indirect ownership is treated inconsistently: Singapore 28 counts Temasek's ~51% of Singtel as government ownership above
  50%, while Malaysia 33 aggregates state funds and still scores 0.5.

**Thin data.** No score-0 row (every economy has some government ownership).

### "5.4" Lack of functional/accounting separation

**What it asks.** Whether the economy mandates functional and/or accounting separation for operators with significant
market power (Guide p.43). **TRAP: inverted polarity** with four levels.

**Criteria and scores.** 1 = neither mandated; 0.5 = accounting separation only; 0.25 = functional separation only; 0 = both
(Guide p.44; Methodology sheet 5.4). Functional (operational) separation splits units running different activities, and the
Guide's example of it is New Zealand's structural split into Chorus and Spark (Guide p.43), so structural separation counts
as functional. Accounting separation keeps separate records so costs, revenues and assets can be identified (Guide p.44).

**SMP scope.** The Guide asks about SMP operators (p.43); host rows accept duties on all licensees above a turnover threshold
(round2 India row 53) or on all operators (round2 Russian Federation row 38) as 0.5.

**Confusions (trap candidates).** 5.4 vs 5.1; general financial or statistical reporting is not separation (round2 Lao PDR row
31 cites both); an abuse-of-dominance or cross-subsidy ban with separation only as a possible remedy (round1 Singapore row 29).

**Exemplars and why.** Australia 29 (both, 0); Thailand 38, India 53, Russian Federation 38 (accounting only, 0.5); China 35,
Mongolia 27 (neither, 1).

**Rows flagged.**
- r2-la-031 (round2 Lao PDR row 31): scored 0.25 (functional only). The impact text says the 2015 Decision mandates functional
  separation but not accounting separation; the note says the opposite ("Functional separation is not mandated, only
  accounting separation is found"). If the note is right, the score is 0.5. It is the pool's only 0.25 row. Not used.
- r1-sg-029 (round1 Singapore row 29): says both that accounting separation is required for dominant licensees and that it is
  "not applied by default"; 0.5 plausible. Not used.
- r1-my-034 (round1 Malaysia row 34) is struck through; Malaysia has no other 5.4 row.
- round2 Indonesia row 51 (0.5) cites Government Regulation 52/2000; I could not verify from host materials whether it is
  still in force after Government Regulation 46/2021 (the rows call it "amended").

**Thin data.** No reliable 0.25 row.

### "5.5" Licensing requirements in telecom sector for operators (Tier B)

**What it asks.** Whether licences for private telecom services or for operating telecom facilities carry discriminatory
conditions against foreign firms or significant entry barriers for all providers (Guide p.44).

**Criteria and scores.** Binary. Methodology: 1 = any strict licensing scheme (e.g. discrimination against foreign providers,
minimum capital requirements, mandatory performance requirements); 0 = none. The Guide adds separate value-added licensing,
caps on licence numbers, and examples: administrative frequency allocation (Indonesia), revenue sharing on top of fees
(Bangladesh), a 25% IPO duty (Tanzania) (Guide p.44).

**Scope conflicts.**
- Broadcasting: excluded from Pillar 5 (Guide p.40 fn 27); broadcasting licences are 9.4 (Internal Guide p.14); but Internal
  Guide p.11 says telecom licensing includes broadcasting. The codebook follows the Guide and Internal Guide p.14.
- ISPs: Pillar 5 includes value-added telecom such as online data processing and email (Guide p.40), yet ISP and ICP licences
  go to 9.4 (Internal Guide p.12). Host practice follows the FAQ: India's internet service authorisation is 9.4 (round2 India
  row 122, 0.5).
- Local incorporation: commercial presence requirements are 3.5 (Guide p.11). Workbook split: round1 Singapore row 30 = 1 on
  local incorporation for facilities-based licences; round2 Russian Federation row 39 = 0 on registration as a Russian legal
  entity. (Australia row 30's "constitutional corporation" test is an entity-form rule, not local incorporation, so it is not
  a clean comparison.) The Thai telecom licence text was struck from 3.5 (round2 Thailand row 19) and kept in 5.5
  (row 39, which also has a foreign-shareholding exclusion); the Thai satellite rule sits in both 3.5 (row 21 = 1) and 5.5
  (row 40 = 1); Malaysia's local-incorporation rule for network licences is in 3.5 (round1 Malaysia row 19).
- Revenue-based fees: round2 India row 54 = 0 despite an entry fee plus a licence fee of 8% of adjusted gross revenue (row
  note), while the Guide's Bangladesh example treats revenue sharing on top of fees as a barrier.

**Confusions (trap candidates).** 5.5 vs 9.4, 12.3, 12.4.4 (Guide p.85), 11.2 (equipment certification, Internal Guide p.14),
3.5, 5.2, encryption licensing (round2 Russian Federation row 77 is coded 9.4).

**Exemplars and why.** Malaysia 35 (foreign-company ineligibility plus capital), China 36 (state equity and capital), Thailand
39 (foreigner exclusion) at 1; Australia 30, Russian Federation 39, Lao PDR 32 (capacity criteria), Mongolia 28 at 0.

**Methodology vs host reasoning.** The methodology counts a minimum capital requirement as strict on its own, with no need for
discrimination (Methodology sheet 5.5). Lao PDR 32 reasons from the absence of discrimination and says "adequate financial
resources" could be read as a minimum capital requirement. My inference: an unquantified adequacy test is not a minimum capital
requirement, so 0 stands, but the host's stated reason (no discrimination) would not save a quantified capital floor.

**Rows flagged.**
- r1-sg-030 (round1 Singapore row 30): 1 rests on local incorporation (with 100% foreign ownership allowed) and on dealer
  licences for telecom equipment. Guide p.11 sends the first to 3.5; equipment dealing is not operator licensing. Likely
  over-scored for 5.5.
- r2-in-054 (round2 India row 54): 0 vs the Guide's revenue-share barrier.
- r2-in-055 (round2 India row 55): a press release about experimental and demonstration licences and equipment type approval.
  Not operator licensing, not a legal instrument.
- r2-id-053 (round2 Indonesia row 53): 1 on local legal-entity status and the Minister announcing the number and location of
  operations (plausible as a cap on licences), but it cites Government Regulation 52/2000; check that it is still in force.
  Not used.
- r1-my-035 (round1 Malaysia row 35): its note says "This could be a 0 as well" and mentions a 100% foreign-owned satellite
  licence granted in practice. Kept as the canonical 1 because the text lists foreign-company ineligibility and minimum
  paid-up capital.
- r2-id-055 (round2 Indonesia row 55): numbering allocation, not a licence condition; 0 is harmless.

### "5.7" Lack of independent telecom authority

**What it asks.** Whether the economy has an independent telecommunications regulator, independent of operators, the
Government and other interested persons in decision-making and administration (Guide p.46). **TRAP: inverted polarity.**

**Criteria and scores.** Binary: 1 = no independent authority; 0 = one is established (Guide p.46; Methodology sheet 5.7). The
Guide's two dimensions: functional independence (decisions without approval from government bodies or suppliers; overrides
clearly defined and limited; equal treatment of SOEs and dominant firms; may report to a ministry but free of political
influence) and institutional and financial independence (legally separate from operators; stable dedicated budget; control of
staff beyond established high-level appointments) (Guide p.46). The RDTII scope goes beyond the WTO Reference Paper to
independence from the Government (Guide p.46 fn 30). Evidence: the law establishing the regulator or the Telecommunications Act
(Internal Guide p.13).

**Open point.** The Guide does not say how many criteria must fail for a 1. Host rows score 1 where the regulator is a ministry
or its subordinate agency (round2 China row 37; round2 Russian Federation row 40), an independent body was dissolved into the
ministry (round2 Indonesia row 56), a Minister can override decisions (round1 Singapore row 31), or members are appointed by the
Prime Minister (round2 Mongolia row 29). They score 0 where the Minister gives directions that cannot overrule decisions (round1
Australia row 32) or the regulator follows government policy (round1 Malaysia row 36).

**Confusions (trap candidates).** 5.7 vs 5.3; 5.6 (the Reference Paper's clause 5 is non-regulatory); dispute tribunals (India's
TDSAT) are not the regulator; independence of other regulators (data protection, competition) is out of scope.

**Exemplars and why.** China 37, Indonesia 56, Russian Federation 40, Singapore 31 at 1; Thailand 41, Australia 32 at 0.

**Rows flagged.**
- r2-mn-029 (round2 Mongolia row 29): 1 because the Prime Minister appoints the chair and members; Guide p.46 allows established
  high-level appointments, so appointment alone should not fail the test. Possible mislabel.
- r2-la-033 (round2 Lao PDR row 33): 0 based on the WTO Trade Policy Review 2019 (a secondary source); the note says the
  establishing regulation was not found.
- r2-in-056 (round2 India row 56): cites TRAI's officers-and-staff appointment regulation, not the act establishing TRAI.
  Score plausible, evidence weak. Not used.
- r1-my-036 (round1 Malaysia row 36): "subject to the overall policies set by the Malaysian government"; the row does not analyse
  ministerial directions. Not used.

---------------------------------------------------------------------------------------------------------

## 3. Cross-cutting observations

- Scores in the workbooks are per row (one measure per row; Format requirements p.4). The "more than one measure" or "more than
  one company" escalations (4.3, 4.9, 5.2, 5.3) are economy-level aggregations across rows.
- Multi-mapping is legitimate: one measure may be recorded under several indicators (Guide p.11; Internal Guide p.11; Assignment 1
  answer key p.3). In g2 this shows up as 4.9/7.5/2.2, 5.2/5.5/3.1 and 5.5/3.5.
- Absence rows cite the governing law with score 0 (Guide p.12); host-wide, so not repeated in YAML.
- Guide copy errors to ignore: the 4.6 scoring sentence says "patents" (Guide p.34); the WCT section calls the WCT the "WIPO Patent
  Cooperation Treaty (WCT)" (Guide p.34, out of scope).

## 4. Top concerns for the whole group

1. **ID hazard inside the host data.** round2 Indonesia row 35 (r2-id-035) is tagged 4.1 but is a patent-application row (4.01).
   Any gold or evaluation keyed on the dump label will score Indonesia's trade secret framework 1 while round2 Indonesia row 42
   says 0.
2. **Score bands with no examples.** 4.2 (10 rows), 4.3 (10) and 4.6 (13) are all 0; 5.1 and 5.2 have no score-1 row; 4.1 has no
   valid score-1 row; 4.5 has no score-1 row; 4.01 has no 0.5 row; 5.4 has no reliable 0.25 row; 5.3 has no 0 row. Higher bands
   rest on Guide text alone.
3. **Piracy FAQ vs workbook.** Internal Guide p.12 ("4.5", high piracy rate gives 1) is contradicted by host practice (round2 Thailand
   row 29 moved to a de jure 0; round2 Mongolia row 19 scores 0 despite 85% software piracy). Needs a host ruling; FAQ numbering is
   unreliable.
4. **4.9 scope.** The Guide excludes procurement (2.2) and encryption (Pillar 11) disclosures, yet every workbook row above 0 is one of
   those (Indonesia 41; India 42; Russian Federation 30) or a general security-assistance duty (China 28), and the Guide's own examples
   sit inside its carve-outs. Methodology (court-order disclosure = 0.5) and Guide (safeguards = not scored) also diverge; Malaysia 27
   (warrant-based) = 0.
5. **4.1 common-law protection scored both ways.** Australia 24 and Malaysia 28 = 0.5; Singapore 23 and India 43 = 0 on the same
   basis. The Guide's Singapore example supports 0; the methodology's "certain clauses" criterion pulls toward 0.5.
6. **4.5 closed-list exceptions.** The Guide gives closed lists and bare three-step tests 0.5 (Indonesia example), but China 26,
   Mongolia 18, Russian Federation 28 and Thailand 28 have that structure and are scored 0. Gold for 4.5 is more lenient than the Guide.
7. **5.5 licensing boundaries.** Local registration scored 1 (Singapore 30) and 0 (Russian Federation 39) although Guide p.11
   sends commercial presence to 3.5; India 54's 8% revenue licence fee scored 0 despite the Guide's Bangladesh example;
   broadcasting (Internal Guide p.11 vs Guide p.40) and ISPs (Guide p.40 vs Internal Guide p.12) sit on conflicting host guidance.
8. **5.2 / 3.1 double-coding and 5.3 counting.** Horizontal SOE caps and one telecom cap are coded under both 3.1 and 5.2 (Malaysia
   13/32, Indonesia 26/48, Russian Federation 15/36, Thailand 14/36), contrary to Guide p.25. Malaysia 33 (5.3) = 0.5 despite four
   companies with 1-50% state-related stakes (Guide p.43 gives 1); indirect ownership through state funds is undefined.
9. **Single-row Guide/workbook conflicts.** 4.01 Singapore 16 (procedural only, scored 1; Guide 0.5); 4.3 China 25 (local agent for
   patent matters, scored 0; Guide's 0.5 example); 5.1 India 47 (sharing not mandatory, scored 0); 5.4 Lao PDR 31 (note contradicts
   the 0.25 score); 5.7 Mongolia 29 (appointments, which Guide p.46 permits, scored 1).
10. **Weak or non-legal evidence in scored rows.** Press releases (India 4.5 row 39, 4.1 row 44, 5.5 row 55), consultation papers
    (India 5.1 row 48, Malaysia 5.1 row 30), a bill instead of the act (India 4.6 row 41), a WTO report as sole source (Lao PDR 5.7
    row 33), a wrong-country URL (India 4.01 row 35), and possibly superseded Indonesian Government Regulation 52/2000 (5.1 row 45,
    5.4 row 51, 5.5 row 53; unverified).
