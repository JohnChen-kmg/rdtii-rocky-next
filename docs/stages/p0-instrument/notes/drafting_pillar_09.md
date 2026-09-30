<!-- Drafting notes for pillar 9 (9.1, 9.3, 9.4). Written 2026-09-13 by a Claude drafting agent working from the host
sources in ../sources/. Checked by the lead for structure (checker, merge, citation audit) but NOT reviewed by a
human. Row IDs: r1-/r2-<economy>-<row> = gold_id in the repo gold set. -->

# g4 notes: Pillar 9 (Content access): 9.1, 9.3, 9.4

Conventions. Guide pages are printed pages (printed = PDF - 12). Internal Guide pages are its PDF
pages (general rules pp.5-10, FAQ pp.11-15). Workbook rows are cited as `sheet row N` from
`rows_pillar_09.jsonl` / `rows_all.jsonl`. 9.2 Internet shutdowns (Guide p.70) is non-regulatory
(Non-regulatory note; Internal Guide p.8) and is not drafted. Pillar weights (Guide pp.72-73):
9.1 33%, 9.2 33%, 9.3 13%, 9.4 21%.

Input check. The corrected `assign2.txt` (Assignment 2 brief) has no Pillar 9 content, and none of
these drafts cite it. Its general point, that practice-oriented indicators mix legal and factual
evidence, is illustrated with 5.3 only.

Workbook pool (unstruck): 9.1 has 32 rows (25 scored 1, 7 scored 0, none 0.5). 9.3 has 25 rows
(11 scored 1, 14 scored 0; Indonesia has 11 of them; 2 Thailand rows are struck). 9.4 has 25 rows
(8 scored 1, 10 scored 0.5, 7 scored 0; China has 6). All 10 economies appear for each ID. Some
scores are stored as text `"1.00\n"` (Russian Federation 9.3 rows 73-76; China 9.4 rows 88, 90).

---

## 9.1 Blocking or filtering commercial web content (Tier B)

### What it asks
It asks whether there have been any instances of blocking or filtering commercial web content,
either by a Government or by Internet intermediaries as the Government requires (Guide p.69).
Blocking denies access to a commercial website in its entirety. Filtering limits access to certain
content on a website (Guide p.69). The harm is limiting commercial sites on broad public-policy
grounds without clear or objective criteria (Guide p.69). Guide examples: Brunei Darussalam's
best-efforts ban on content against the public interest or national harmony, and Türkiye's
blocking powers plus a 24-hour removal duty for large social networks (Guide p.69).

### Criteria to scores
- Methodology sheet 9.1: (1) any blocking measure -> 1; (2) any filtering measure -> 0.5;
  (3) no blocking or filtering, except internationally agreed illegal content/child pornography -> 0.
- Guide p.70: 1 for each blocking measure, whatever the technique (IP/protocol, DPI, URL, DNS).
  0.5 for each filtering measure. Otherwise 0.
- Exclusions: political, criminal (e.g. child pornography), age-restricted, defamation and other
  non-commercial content (Guide p.70; Indicator Reference note). IP-infringement blocking is not a
  restriction (Guide p.70 only, not in the reference note).
- The codebook scores a measure that permits whole-site blocking as 1 even when it also permits
  content removal. That follows from criterion (1) "any blocking measure". It is a reading, not
  explicit host text.

### Evidence type (practice-based)
- Internal Guide p.8 names 9.1 (with 3.4 and 5.3) as a sub-pillar focused on enforcement and
  practice, an exception to official-sources-only.
- Host training slides PDF p.8 say secondary sources for 3.4, 5.3 and 9.1 may be recorded and
  scored. PDF p.9 lists practice sources for 9.1: official annual reports, regulator market reports,
  company websites, actual cases, technical monitoring reports, reputable secondary materials and
  media releases.
- Slides quiz 3 (PDF pp.20-21). The text extraction loses the answer, which is shown by icon images.
  I checked the icon colours with PyMuPDF (read-only) and calibrated them on quiz 2 (PDF p.19).
  There, green marks the in-force Thai PDPA and the Indian DPDP Act, and red marks the repealed
  directive, draft rules, Meta announcement, Wikipedia and the law-firm article. All five 9.1 items
  are green. So the host counts the government blocking announcement, the Bhutan ISP licensing
  rules, the Miscellaneous Offences Act, the GreatFire.org report and India's IT Rules 2021 as RDTII
  sources for 9.1. China row 86 (GreatFire.org / Freedom House) therefore fits host practice.
- Disagreement: Guide p.70 (and the general rule on Guide p.12) says secondary sources should only
  guide researchers to primary sources. The codebook follows Internal Guide p.8 plus the training.
  policies.yaml `official_sources_only` ("secondary sources are NEVER evidence") needs a 9.1
  override (see Top concerns).

### Confusions (sources)
- **8.4 Monitoring requirements.** 8.4 covers duties to actively monitor, or to remove or block
  illegal content (Guide p.67; Internal Guide p.13). Guide p.68 adds that intermediaries may then
  impose unnecessary blocking and filtering, "which are the measures under Pillar 9". The Guide's
  own 9.1 Türkiye example includes a platform removal duty (Guide p.69). Workbooks code the same
  instruments under both:
  - Indonesia PM Kominfo 5/2020: 8.4 row 102 = 1; 9.1 row 107 = 1.
  - Russian Federation 149-FZ: 8.4 row 65 = 1; 9.1 row 70 = 1.
  - Singapore Broadcasting Act ss.45E-45I: **8.4 row 53 = 0 but 9.1 row 59 = 1**.
  - Malaysia Content Code 2022: 8.4 rows 70-71, 9.1 row 74 and 9.3 row 75.
  - Mongolia General Regulatory Conditions of Digital Content Service: 8.4 row 49, 9.1 row 55,
    9.4 row 58.

  Guide p.11 allows recording one measure under every applicable indicator.
- **10.1 Import bans on online services.** Guide p.74 says "import bans on certain applications"
  are 10.1. India's 2020 ban of 267 apps via s.69A is 10.1 row 125. The 2023 blocking of 232
  betting and loan apps is 9.1 row 119. The placement is inconsistent.
- **9.2 Internet shutdowns** (non-regulatory). Lao PDR row 59 (Telecom Law Art.45: temporary
  government control of networks during unrest) is a network-control or shutdown power, not
  blocking of commercial content.
- **9.4.** The registration or licence precondition belongs in 9.4 (Indonesia row 122 = 0). Blocking
  for non-registration belongs in 9.1 (Indonesia row 107 = 1).
- **3.5 / 12.8.** Russia's 236-FZ requires a branch, representative office or Russian entity. That
  duty is commercial presence, 3.5 (Guide pp.27-28), and Guide p.88 says mixed duties count as
  commercial presence. The access restriction for breaching it is 9.1 (row 72).
- *Inference only:* copyright site-blocking injunctions (Australia row 54) are excluded from 9.1.
  They may evidence provisional measures under 4.6 (Guide p.34). No host text links them.

### Exemplar choices (8; 4 scored 1, 4 scored 0; 7 economies)
Indonesia 107 is the canonical commercial case: PayPal and Steam were blocked for non-registration.
Russian Federation 72 shows blocking as the sanction on foreign platforms. China 86 is pure practice
evidence (secondary sources, now confirmed by the slide quiz). Lao PDR 60 is a broad-grounds legal
basis like the Guide's Türkiye example. Australia 54 shows the IP exclusion and Australia 55 the
criminal-content exclusion. India 118 shows that blocking already-illegal betting apps is not
recorded; host hands-on training PDF p.10 says the same for Singapore's illegal remote gambling
sites. Mongolia 54 is an absence row where a repealed law is not scored. **No 0.5 row exists in
either workbook.**

### Rows I think are mislabelled or doubtful (not used)
| gold_id | score | problem | source |
|---|---|---|---|
| r1-my-073 (Malaysia 73) | 1 | Sedition Act s.10A orders against seditious publications are political content, which is excluded. The commercial examples in the note (scam e-commerce sites, Grindr) are not tied to the cited Act; the copyright ArtStation block is excluded anyway. | Guide p.70; Indicator Reference note |
| r1-sg-060 (Singapore 60) | 1 | OCHA directions apply to online activity furthering criminal offences, i.e. criminal content. Host training treats blocking of already-illegal services as not recordable. | Guide p.70; hands-on PDF p.10 |
| r1-sg-059 (Singapore 59) | 1 | Borderline. "Egregious content" is criminal or harmful, but a non-compliant online service can be blocked whole. The same provisions score 0 in 8.4 (Singapore 53). Needs a host ruling. | Guide p.70 |
| r2-in-115 (India 115) | 0 | The law field names the Interception, Monitoring and Decryption Rules 2009, but the impact and second URL describe the Blocking Rules 2009. A score of 0 conflicts with India 116 = 1 for the same s.69A power. | workbook internal |
| r2-in-117 (India 117) | 1 | The URL is a "proposed amended" IT Rules PDF (drafts score 0). The content is misinformation about Government business, which is non-commercial. The note links an unrelated betting-games article. *Outside host sources:* I believe the 2023 fact-check-unit amendment was stayed and then struck down in 2024; verify. | Guide p.70; host-wide draft rule |
| r2-in-119 (India 119) | 1 | Sourced only from a news article ("cannot find the official one"). It mixes betting apps (India 118 scores the same kind of order 0) with loan apps. Similar app bans are coded 10.1 (India 125). | hands-on PDF p.10; Guide p.74 |
| r2-id-104 (Indonesia 104) | 1 | The cited instruments (personal-data regulation 20/2016, population-administration GR 40/2019) do not provide the blocking. The practice examples are pornography-based (Vimeo). The row's own note doubts the score. | Guide p.70 |
| r2-la-058 (Lao PDR 58) | 1 | The impact says no blocked or filtered websites were found. The note says it is not related to commercial content and that V-Dem political filtering should not count. Art.29 is a service-suspension right. The text supports 0. | Guide p.69-70 |
| r2-la-059 (Lao PDR 59) | 1 | A network-control power (9.2 type), not blocking of commercial web content. | Guide p.70; Non-regulatory note |
| r2-th-081 (Thailand 81) | 1 | The NCPO notifications target criticism of the NCPO and incitement, which is political and excluded. The MDES statistics are mostly gambling and fraud. Mixed; needs a host ruling. | Guide p.70 |

Scored correctly but not used: Indonesia 108 (0, pornography) reads as an advertising analysis with
speculative blocking. Russian Federation 68 (0, ISP fines) teaches ancillary penalties = 0 and is
cited in coding_rules, not curated.

### Guide / methodology / workbook disagreements
1. **Secondary sources.** Guide pp.12 and 70 say leads only. Internal Guide p.8 and the training
   say record and score.
2. **Exclusion breadth.** Methodology criterion (3) names only internationally agreed illegal
   content/child pornography. Guide p.70 and the reference note exclude five categories, and the
   IP exclusion is only in the Guide.
3. **0.5 filtering never used.** Several score-1 rows describe content-level removal (Malaysia 74,
   Mongolia 55). They stay at 1 where the measure also allows whole-site blocking. A removal-only
   measure would be 0.5 under the Guide, but the workbooks have no example.
4. **"Instances" vs legal bases.** Guide p.69 asks about instances. Most score-1 rows are legal
   powers with no documented use, and Lao PDR 58 records "no record found" yet scores 1.
5. **Political vs commercial.** Internal Guide p.14 records measures that impact commercial
   websites whatever the justification. Guide p.70 excludes political content. News-media blocking
   scores 1 (India 116, Russian Federation 71, Singapore 58). The host does not draw the line
   between a commercial news site and political content.

### Open questions
- Does a legal power never shown to be used earn 1? The workbooks say yes; the Guide's wording says
  "instances".
- Is legality judged economy by economy (gambling legal in AU, illegal in SG/ID/IN)? The training
  says "country specific context is necessary".
- Should blocking a whole platform for ignoring harmful-content directions (Singapore 59) count as
  commercial?

---

## 9.3 Online advertising requirements (not Tier B; trap candidates below)

### What it asks
It covers requirements limiting online advertising. It excludes general consumer protection (bans
on misleading or false ads) and product-specific limits for public health or safety (weapons, drugs,
tobacco, alcohol, medicine) (Guide p.71). Rules silent on medium count as online unless clearly
offline-only (Guide p.71 fn.44). Offline-only advertising rules are excluded (Guide p.9; Internal
Guide p.14, billboard example). Guide examples (p.71):
- Marshall Islands: bilingual ads plus Commission approval.
- Kazakhstan: comparative or discrediting ads banned.
- Russian Federation: 5% unpaid social advertising plus reporting.
- Uzbekistan: prices in foreign currency banned.

The OECD Digital STRI is a guide to primary sources (Guide p.71).

### Criteria to scores
- Methodology sheet 9.3: (1) any restriction on online advertising -> 1; (2) no restriction -> 0.
  Values [1, 0].
- Guide p.71: 1 for each requirement limiting online advertising, otherwise 0. Consumer-protection
  ad measures score 0.
- Indicator Reference note: do not score requirements that ads must not be misleading. This is
  narrower than the Guide, which also excludes product-specific health and safety limits.

### Trap candidates (for promotion)
1. **Consumer protection vs restriction** (Guide p.71; Internal Guide p.14; reference note). The
   workbooks follow it for truthfulness rules: Indonesia 109 and 110, Thailand 82 and Singapore 61
   all score 0. They split on **pre-approval or certification regimes**: India 121 (self-declaration
   that an ad is not misleading) = 1, Lao PDR 61 (prior permission from the consumer protection
   committee) = 1. The Guide's Marshall Islands example (Commission approval) suggests approval
   regimes are restrictions when the purpose is not consumer protection. Needs a host ruling.
2. **Product-specific public health or safety limits -> 0** (Guide p.71). Workbooks follow it for
   tobacco (India 120, Indonesia 112), alcohol (Indonesia 113), pharmaceuticals (Indonesia 114) and
   medical products (China 87). Gambling is not in the Guide's list and is split: Indonesia 115 = 0
   (gambling illegal), Australia 56 = 1 (live-sport gambling ads).
3. **Offline-only -> not scored** (Internal Guide p.14; Guide p.9). Australia 56 relies partly on an
   Australian-content quota for ads on commercial TV.
4. **Platform duty to moderate content, including ads -> 8.4, not 9.3** (Guide p.67). Indonesia 118
   (GR 71/2019 Art.100) and 119 (PM Kominfo 5/2020 Art.9) score 9.3 = 1, while the same PM 5/2020
   is 8.4 row 102.
5. **Non-binding codes or guidelines -> 0.** Thailand 83 (ETDA guideline), Singapore 61 (SCAP
   self-regulation). Consistent with host-wide enforced-measure rules.
6. **Political or election advertising -> 0 (non-commercial).** Indonesia 117 (Internal Guide p.7
   excludes non-commercial services).
7. *Inference only:* a local-content quota for ads may belong to 10.3 (Guide pp.75-76, Bhutan OTT
   local content). Misleading-ad bans inside a consumer protection act may evidence the 12.9
   framework (Guide p.88). Neither link is stated by the host.

### Exemplar choices (7; 3 scored 1, 4 scored 0; 5 economies)
- Russian Federation 75 is the Guide's own example.
- Russian Federation 74 (ad tokens and state register) is an online-specific administrative duty.
- Malaysia 75 is a weaker score-1 row: its unacceptable-products list includes non-health items
  such as marriage agencies, but also slimming products and fire crackers, which are excluded.
- Negatives: India 120 (tobacco), Indonesia 109 (misleading ads, the host exception), Indonesia 117
  (political ads), Thailand 83 (non-binding).

I stopped at 7 because the other score-1 rows are more Russian rows (73, 76) or doubtful (below).

### Rows I think are mislabelled or doubtful (not used)
| gold_id | score | problem | source |
|---|---|---|---|
| r1-au-056 (Australia 56) | 1 | The gambling-ad limits look like harm minimisation, and the Australian-content quota applies to commercial TV (offline). The only online element is gambling ads during live-sport streams. | Guide p.71; Internal Guide p.14 |
| r2-id-118 (Indonesia 118) | 1 | A general content-moderation duty for electronic system operators is a monitoring requirement, not an ad restriction. | Guide p.67 |
| r2-id-119 (Indonesia 119) | 1 | Same as above; the same regulation is 8.4 row 102. | Guide p.67 |
| r2-in-121 (India 121) | 1 | The certificate attests that ads are not misleading (consumer protection), yet it is a pre-publication step for every ad. Needs a host ruling. | Guide p.71; Internal Guide p.14 |
| r2-la-061 (Lao PDR 61) | 1 | Prior permission under the Consumer Protection Law; the other cited articles are truthfulness rules. Needs a host ruling. | Guide p.71 |
| r2-mn-056 (Mongolia 56) | 1 | Art.12 (permission to place ads on others' pages, advertiser contact details, fee notice) resembles consent and consumer-protection rules. The Art.6.5 bans are about legality or safety. The impact cites an "Advertising Law of 2022", but the timeframe says last amended December 2019. | Internal Guide p.14 |

Plausible 1 but not used: Russian Federation 73 (mostly excluded products, plus a digital-currency ad
ban and gambling ads restricted to certain Russian sites) and 76 (ban on ads on restricted or
"undesirable" resources, in force from September 2025).

### Open questions
- Does the product exclusion extend to gambling and crypto or financial ads (Indonesia 116 = 0)?
- Russian Federation 75's note mentions a 3% levy on online-advertising revenue from April 2025. Is
  that a separate 9.3 measure? It is not scored in the row.

---

## 9.4 Licensing requirements for online content providers and applications (Tier B)

### What it asks
A licensing scheme for online service providers: ICPs and applications such as social media, news
providers (media and broadcast), VPNs and cloud services. It excludes telecom facilities and service
providers (Pillar 5) and e-commerce platforms (Pillar 12). It asks whether ICPs need a licence to
operate and whether that licence is strict (Guide p.71).

A licence is strict when its conditions significantly limit market access or competition beyond
normal standards (Guide p.72):
- commercial presence;
- nationality or residency;
- excessively high paid-up capital;
- mandated government-approved systems, local data storage or proprietary technology.

### Criteria to scores
- Methodology sheet 9.4: (1) any strict licence, or more than one measure of category (2) -> 1;
  (2) any licensing scheme -> 0.5; (3) no restriction -> 0.
- Guide p.72: 1 for a strict scheme, also 1 if more than one licensing requirement (even if not
  strict), 0.5 for just one scheme, otherwise 0.
- Scope aids:
  - ISP and ICP licences are 9.4; telecom licences are 5.5 (Internal Guide p.12).
  - Data-centre licensing may be 9.4 (Internal Guide p.13).
  - 9.4 covers broadcasting licences, cloud computing and data centres (Internal Guide p.14).
  - A platform licence spanning marketplaces, car sharing and social media goes to both 9.4 and
    12.3 (Guide p.11).

### Confusions (sources)
- **5.5** (Guide p.44; Internal Guide p.12). India's Unified Licence is 5.5 row 54, while its ISP
  authorisation is 9.4 row 122. Malaysia's NFP/NSP licences are 5.5 row 35, while its ASP/CASP
  licences are 9.4 rows 76-77. Russia's encryption and broadcasting licensing appear in both 5.5
  row 39 (score 0) and 9.4 rows 77-78.
- **Host documents disagree on ISPs.** Guide p.71 and the reference note exclude telecom *service
  providers*; Internal Guide p.12 puts ISP licences in 9.4. The codebook follows p.12 by licence type.
- **Host documents disagree on broadcasting.** Internal Guide p.11 (Pillar 3 FAQ) says telecom
  licensing "include[s] broadcasting services". Guide p.40 excludes broadcasting from Pillar 5, and
  Internal Guide p.14 puts broadcasting licences in 9.4. The workbooks follow 9.4 (Russian
  Federation 78, Thailand 86, Mongolia 57).
- **12.3.** Thailand's digital-platform decree is coded 12.3 row 112 and 9.4 row 87, both 0,
  consistent with Guide p.11. But the registration threshold differs: Guide p.85 counts Colombia's
  commercial-registry registration of websites as a 12.3 licensing example, whereas 9.4 rows score
  registration or notification 0 (Thailand 87; Indonesia 121-123; Lao PDR 63).
- **6.3** (Internal Guide p.13).
  - China online publishing: 6.3 row 49 = 1 and 9.4 row 88 = 1, consistent.
  - China ride-hailing: servers-in-China condition in 6.3 row 47 = 1, but the 9.4 licence row 92
    is only 0.5.
  - Lao PDR data-centre licence: recorded in 6.3 row 37 at 0 (correct for 6.3) but suppressed from
    9.4 by the row 62 note, contrary to Internal Guide p.13.
- **3.5 / 12.8** (Guide pp.27-28, 87-88). A local-entity condition inside a licence makes it strict
  (China 90). Indonesia's PSE liaison-officer duty is the Guide's own 12.8 example (Guide p.88).
- **8.4.** Singapore's Internet Code of Practice appears in 8.4 row 56 and 9.4 row 62.
- **9.1.** Blocking for non-registration (Indonesia 107) vs the registration itself (Indonesia 122).

### The escalation problem (per-economy rows)
| Economy | Rows and scores |
|---|---|
| CN | 88=1, 89=0.5, 90=1, 91=0.5, 92=0.5, 93=0.5 |
| RU | 77=0.5, 78=0.5 |
| ID | 120=0.5, 121=0, 122=0, 123=0, 124=0.5 |
| SG | 62=1, 63=1 |
| MY | 76=1, 77=1 |
| MN | 57=1, 58=1 |
| IN | 122=0.5 |
| TH | 86=0.5, 87=0 |
| LA | 62=0, 63=0 |
| AU | 57=0 |

Round 1 Singapore and Malaysia, and Round 2 Mongolia, give every row 1 when the economy has two
schemes. Singapore 62 is an automatic class licence with no strict condition. China, Russia and
Indonesia keep non-strict rows at 0.5 despite having several schemes. The Guide's rule is
economy-level, so the pipeline needs a decision: a row-level score hint plus an economy roll-up, or
per-row escalation. The codebook states the Guide rule and cites the Round 2 practice.

### Exemplar choices (8; 4 scored 1, 2 scored 0.5, 2 scored 0; 6 economies)
- China 90: strict by local entity plus Chinese-citizen editor-in-chief (exact Guide criteria).
- Malaysia 76: strict by foreign-company ineligibility, Bumiputera equity and paid-up capital.
- China 88: strict by in-country servers; boundary with 6.3.
- Singapore 63: online news licence, score 1 via the more-than-one-scheme rule or the bond.
- India 122 and Thailand 86: the only 0.5 rows consistent with the Guide, since each economy has a
  single scheme. India 122 is the 5.5 boundary (ISP); Thailand 86 is broadcasting.
- Thailand 87: notification is not a licence.
- Australia 57: absence row.

### Rows I think are mislabelled or doubtful (not used)
| gold_id | score | problem | source |
|---|---|---|---|
| r2-id-120 (Indonesia 120) | 0.5 | **The Guide cites this exact IoT licence and local-MSISDN addressing rule as a strict example**, so it should be 1. Indonesia also has two licensing rows (120, 124). | Guide p.72 |
| r2-cn-092 (China 92) | 0.5 | The same Interim Measures (Art.5) require servers in mainland China (China 6.3 row 47), which is a strictness condition, and China has several schemes. | Guide p.72 |
| r2-la-062 (Lao PDR 62) | 0 | The note records an Internet Data Center operating licence and Mass Media Law licences for online media, then suppresses both. Both are 9.4 scope, so rows are probably missing and the score is likely understated. | Internal Guide pp.13-14; Guide p.71 |
| r2-id-124 (Indonesia 124) | 0.5 | Speculative ("VPNs may fall under") use of the general telecom-services licence, which is Pillar 5. | Indicator Reference note; Guide p.71 |
| r2-mn-058 (Mongolia 58) | 1 | Mongolia 8.4 row 52 says the 2022 Permit Law stopped issuing content-service special licences. Check that the 2011/2015 General Conditions licence is still enforced. | workbook round2 Mongolia row 52 |
| r1-my-077 (Malaysia 77) | 1 | Claims VPNs and cloud services fall under the social-media and messaging class licence; the quoted sections do not show that (verify). Score 1 holds only via escalation. | workbook internal |
| r2-id-121 (Indonesia 121) | 0 | Internally contradictory: the impact says registration, not licensing, while the note says "Indonesia enforces licensing requirements". | workbook internal |
| r2-cn-089/091/093, r2-ru-077/078 | 0.5 | Each is plausible on its own, but under Guide p.72 the economy has more than one scheme, so 1. | Guide p.72 |

### Open questions
- Where is the line between registration or notification and a licence for 9.4, and should it
  match 12.3's Colombia example?
- Is encryption-service licensing (Russian Federation 77) in 9.4? Guide p.72 lists the World Map of
  Encryption Laws as a 9.4 source, which suggests yes.
- Ride-hailing, maps and IoT are coded 9.4 (China 92, 93; Indonesia 120), and IoT is a Guide
  example. Confirm that "applications" reaches sector platforms that are not content services.

---

## Names, typos, checker
- 9.4 reference and methodology name typos, "new providers" -> "news providers" and "cloud servics"
  -> "cloud services", are fixed in `name` (spec and codebook). `category_official` keeps host text.
- 9.1 note typo "aged-restricted" is written "age-restricted" in rules.
- Internal Guide FAQ names: 9.3 "Restrictions to online advertising"; 9.4 "Licensing schemes for
  digital content providers, digital services and applications" (used as keyword variants).
- Guide erratum outside my IDs: Guide p.11 says import bans and local content requirements are
  "under Pillar 9"; they are Pillar 10.
- `python -X utf8 check_drafts.py g4`: 0 errors, 0 warnings (final run). Two citations fall outside
  the brief's standard forms and are always paired with a standard one: "host training slides PDF
  pp.8-9 and 21" and "host hands-on training PDF p.10".

## Top concerns (group)
1. **9.1 is practice-based, but policies.yaml says secondary sources are never evidence.** Internal
   Guide p.8, slides PDF pp.8-9 and the quiz answer (all five 9.1 sources accepted, including the
   GreatFire.org report) conflict with Guide p.70. An indicator-level override is needed.
2. **9.4 escalation is inconsistent in the gold data.** Round 1 Singapore and Malaysia and Round 2
   Mongolia escalate per row; China, Russia and Indonesia do not. The Guide's own strict IoT example
   is 0.5 in Indonesia row 120. Row-level scores for 9.4 are unreliable as gold without a roll-up
   rule.
3. **9.1 exclusions are applied unevenly.** Political content (Malaysia 73 Sedition Act, Thailand
   81 NCPO) and criminal content (Singapore 60 OCHA) score 1, while criminal, age-restricted, IP and
   illegal-gambling rows score 0 (Australia 54-55, Indonesia 108, India 118). India 118 and 119 give
   betting-app blocking opposite scores. Lao PDR 58 scores 1 with "no record found".
4. **9.1's 0.5 filtering branch has no workbook example.** Takedown-type duties are scored 1, so the
   pipeline cannot learn 0.5 from gold.
5. **9.3's consumer-protection line is not settled.** Approval or certification regimes (India 121,
   Lao PDR 61) and moderation duties (Indonesia 118-119, which look like 8.4) score 1. Gambling ads
   split: Australia 56 = 1, Indonesia 115 = 0.
6. **9.4 scope conflicts between host documents.** ISPs: Guide p.71 vs Internal Guide p.12.
   Broadcasting: Internal Guide p.11 vs p.14 and Guide p.40. Data-centre licences: Lao PDR 62
   suppresses one contrary to Internal Guide p.13.
7. **9.4 registration vs licensing.** Registration and prior notification score 0 (Thailand 87,
   Indonesia 121-123), while Guide p.85 counts registration as licensing for 12.3, and Indonesia's
   PSE regime is the Guide's 12.8 example (p.88).
8. **The same instrument is dual-coded with different scores.** Singapore Broadcasting Act
   ss.45E-45I is 8.4 = 0 but 9.1 = 1. India app bans are split between 10.1 (row 125) and 9.1
   (row 119). The mapping pipeline should emit candidate rows for every sibling indicator rather
   than pick one.
