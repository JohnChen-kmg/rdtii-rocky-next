<!-- Drafting notes for pillar 12 part 2 (12.5-12.9). Written 2026-09-13 by a Claude drafting agent working from the host
sources in ../sources/. Checked by the lead for structure (checker, merge, citation audit) but NOT reviewed by a
human. Row IDs: r1-/r2-<economy>-<row> = gold_id in the repo gold set. -->

# g7 notes: Pillar 12, second part (host IDs 12.5, 12.6, 12.7, 12.8, 12.9)

Drafted 2026-09-13. Sources: Guide pillar 12 text (printed pp.83-94), Guide pillars 3, 4, 6, 7 and 9 for
siblings, Guide intro p.10, Internal Guide (PDF pages), Non-regulatory note, host indicator tables,
workbook rows (round1 AU/MY/SG, round2 CN/IN/ID/LA/MN/RU/TH). Anything below marked **inference** is
my reading and is not written into any cited rule.

**ID matching.** Guide sections on pp.86-88 map by name to host IDs in host order: "Low de minimis" = 12.5,
"Imposition of customs duties on electronic transmission" = 12.6, "Domain name requirements" = 12.7,
"Local presence requirements" = 12.8, "Lack of legal framework for online consumer protection" = 12.9.
No numbering hazard inside this group. The Guide lists these as the 5th to 9th pillar 12 issues (p.83).

**Name and text typos in host tables.** 12.6 reference name and methodology category say "custom duties"
(Guide: "customs duties"); signatures_spec uses "customs" with a YAML comment. 12.7 criteria say
"registrater" (read: register). 12.5 criteria say "below < 200 USD" (redundant, same meaning).

**`asks` choice.** guide_refs carries the Guide's question sentence plus, for 12.5, 12.6, 12.8 and 12.9,
the next sentence where it defines the key term or scope. 12.7 keeps one sentence because footnote
marker 56 interrupts the text that lists the three covered requirement types (p.87).

**Weights (informational, host reference weight is null for pillar 12).** Guide pp.90-91: 12.5-12.8 are
7% each; 12.9 is 4%. The thirteen stated pillar 12 weights sum to 99% (rounding in the Guide).

---

## 12.5 Low De Minimis

**What it asks.** Whether an economy has a de minimis threshold, meaning a value ceiling for goods below
which no duty or tax is charged at the border (Guide p.86). The benchmark is USD 200, attributed to an
ICC (2016) recommendation (Guide p.86). Researchers use official laws, regulations and notifications;
the Global Express Association database is a pointer only (Guide p.86).

**Criteria to scores.** Methodology sheet 12.5: (1) no de minimis = 1; (2) de minimis below USD 200 = 0.5;
(3) de minimis at or above USD 200 = 0. The Guide states the same three outcomes, with "equal to or
above" USD 200 scoring 0, and says exchange rates should come from the IMF (Guide p.86).

**Lead check: Internal Guide p.15.** Verified. The FAQ (a question about converting PhP 10,000 against a
133 SDR threshold) answers that the methodology changed to a USD 200 threshold "according to the UNECE
prescribed guidelines" and tells researchers to use the IMF USD rate as of 31 August.
- Threshold and score values: **no conflict.** Guide p.86, Methodology sheet 12.5 and Internal Guide p.15
  all use USD 200 and the same three outcomes.
- Attribution: **conflict, cosmetic.** Guide p.86 credits the ICC (2016); Internal Guide p.15 credits UNECE
  guidelines. It does not change any score. Rules cite the Guide.
- Conversion date: the 31 August IMF rate appears **only** in Internal Guide p.15; the Guide says only
  "IMF". Complementary, not contradictory, but the pipeline must carry the date from the FAQ.
- The FAQ question shows the earlier SDR 133 threshold. Rows still quote SDR equivalents (Malaysia 106:
  84 SDR; Singapore 89: 208 SDR; Indonesia 169: 2 SDR). No row in the pool changes outcome between the
  SDR 133 and USD 200 methods.
- **Workbook practice does not follow the IMF 31 August rule**: India 154 converts "as of December 2023",
  Thailand 122 "as of June 2025", others give undated approximations. No row sits near USD 200 (closest:
  Russia EUR 200, about USD 230; Singapore SGD 400, about USD 298), so no score is affected in the sample.

**Polarity hazard (trap candidate).** No de minimis rule scores 1 (Guide p.86; Methodology sheet 12.5).
That reverses the general rule that absence of a measure scores 0 (Internal Guide p.10). A pipeline that
finds no threshold provision must not default to 0.

**Confusions (trap candidates for promotion).**
- **12.2 purchase limits.** The Guide's 12.2 examples include a USD 3,000 per-shipment value limit for
  express imports (Brazil) and a USD 50 monthly tax-free allowance (Argentina) (Guide p.84). China's
  cross-border e-commerce quotas (RMB 5,000 per transaction, RMB 26,000 per year) are coded 12.2 = 1
  (workbook round2 China row 110), while China's exemption for shipments with duty under RMB 50 is coded
  12.5 (workbook round2 China row 119). Open issue: the Argentina tax-free allowance resembles a de
  minimis, yet the 12.2 section also says tax and customs duty measures are outside 12.2 (Guide p.84).
  g6 covers 12.2 and may hit the same tension.
- **Merger-control "de minimis".** India row 154 mixes in a Central Government exemption for acquisitions,
  mergers or amalgamations of enterprises with assets below INR 350 crore or turnover below INR 1,000
  crore (the row links the Competition Commission's combination-notice page). That is not a border
  valuation ceiling (Guide p.86). Keyword trap: "de minimis" alone is not enough.
- **Rules-of-origin "de minimis".** Mongolia row 84's note mentions this second meaning. Not 12.5.
- **Vendor-collected GST or sales tax on low-value goods.** Australia 79, Singapore 89 and Malaysia 106
  describe GST or sales tax now charged on low-value imports through vendor or platform collection; the
  researchers still scored the customs threshold. Consistent with the Guide's "at the border" wording
  (Guide p.86). **Inference:** such taxes do not remove the de minimis for scoring.
- **12.6** for duties on digitally transmitted products.

**Exemplars chosen (7 rows, 6 economies).** Singapore 89 and Russia 104 (score 0, at or above USD 200);
Malaysia 106, Indonesia 169, Lao PDR 97 (score 0.5); China 119 (boundary: threshold on the duty amount,
not goods value, coded 0.5); Russia 105 (boundary: air-baggage allowance, which the row itself says does
not apply to internet purchases or post). **No score-1 exemplar**: the only two score-1 rows are doubtful.

**Rows I think are mislabelled or doubtful (excluded).**
- **r2-in-154** (India row 154, score 1). The row states a de minimis regime of INR 100 (duty and GST
  exempt) and INR 1,000 (GST exempt). A de minimis below USD 200 is 0.5 (Guide p.86; Methodology sheet
  12.5). Either the score should be 0.5, or the INR 100 statement is not supported by the cited courier
  regulation. The merger-control paragraph is irrelevant. Human check needed.
- **r2-mn-084** (Mongolia row 84, score 1, "no legislation directly determining the de minimis rule").
  The row cites Article 38.1.15 exempting personal international mail parcels up to ten times the monthly
  minimum wage (and no more than two goods of a type) from customs tax. That fits the Guide's definition
  of a value ceiling below which no duty or tax is charged (Guide p.86), and comparable personal-goods
  exemptions are coded as de minimis rules in Lao PDR 97 and Russia 104. The score should probably be 0 or
  0.5, depending on the USD value of the wage multiple, which cannot be computed from host sources.
- **r2-th-122** (Thailand row 122, score 0.5). THB 1,500 (about USD 46) supports 0.5, but the note column
  says "Not correct", a Thailand reviewer mark with no explanation (nine Thailand rows carry it).
  Excluded until the mark is explained.
- **r1-au-079** (Australia row 79, score 0). The score agrees (AUD 1,000, about USD 640), but the law
  column names the A New Tax System (Australian Business Number) Act 1999, which does not look like the
  source of a customs threshold (**inference**). Not used; the law citation should be checked.

**Open questions.**
1. Thresholds that differ by channel (Malaysia: air courier only; Russia: post vs air baggage; Lao PDR:
   non-commercial goods). Rows use the postal or courier threshold relevant to online purchases (Russia
   104 vs 105), but no host rule says so.
2. Is a duty-amount threshold (China 119) a "valuation ceiling for goods" (Guide p.86)?
3. Routing of tax-free purchase allowances: 12.2 (per the Argentina example, Guide p.84) or 12.5?

---

## 12.6 Imposition of customs duties on electronic transmission

**What it asks.** Whether an economy imposes customs duties or cross-border duties on electronic
transmission, meaning import and export of digital products by electronic means (Guide p.86).
Footnote 55 notes that WTO law does not define electronic transmission and that the WTO moratorium has
run since 1998 and was extended at MC13 (Guide p.86).

**What counts.** Legal mechanisms or regulations that allow such duties count **even when current tariff
lines are zero** (Guide p.86). The Guide's example: Indonesia classifies intangible goods delivered
electronically (software, electronic data, multimedia) under HS heading 99.01 at a 0% rate, which shows
that a legal framework for such duties exists (Guide p.86).

**Score set: {1, 0.5, 0}, normal polarity.** Methodology sheet 12.6: (1) imposition of duties on
electronic transmission = 1; (2) legal mechanisms or regulations applicable to impose such duties = 0.5;
(3) no restriction = 0. The Guide matches: 0 when no legal mechanism exists, 0.5 when a mechanism exists
even at zero rates, 1 when duties are actively imposed "in practice" (Guide p.86).

**Evidence type (open question).** Score 1 needs duties imposed in practice (Guide p.86), which reads
like practice evidence. But 12.6 is not on the Internal Guide's list of practice-based indicators (3.4,
5.3, 9.1; Internal Guide p.8). **Inference:** a published tariff schedule with a non-zero rate on
electronic transmissions would be the official-source evidence for 1.

**Confusions (trap candidates).**
- **Consumption taxes are not customs duties.** India row 155 records GST registration for offshore
  online information and database access services, calling it "like a customs duty", and codes 0
  (workbook round2 India row 155). Malaysia row 107 also separates VAT or GST on digital services from
  tariffs. The Indonesia 12.2 row 155 codes VAT on foreign digital services 0 under 12.2.
- **Tariffs on physical ICT goods** are the non-regulatory tariff indicators 1.1 and 1.2 (Internal Guide
  p.8; Non-regulatory note), not 12.6.
- **12.5** for low-value parcel thresholds.
- Statements of adherence to the WTO moratorium or the JSI (Australia 80, Malaysia 107, Thailand 123)
  support a 0; they are not measures.

**Exemplars chosen (6 rows, 6 economies).** Indonesia 170 (the only 0.5 row; matches the Guide's
example); Russia 106 and Lao PDR 98 (0, customs law reaches physical goods only); India 155 (boundary:
GST); Mongolia 85 and Australia 80 (absence rows). **No score-1 row exists in the workbooks.**

**Rows I think are mislabelled or doubtful.**
- **r2-id-171** (Indonesia row 171, score 0). It describes Minister of Finance Regulation 17/2018 (as
  amended in 2022) creating HS lines at 0% for software and other digital products. That is the exact
  mechanism the Guide scores 0.5 (Guide p.86), and row 170 codes the same regulation 0.5. Mislabelled
  (0 should be 0.5), or a duplicate of row 170 that should be struck.
- **r2-th-123** (Thailand row 123, score 0). Note column says "Not correct" without explanation. Excluded.

**Open question.** Does "cross-border duties" (Guide p.86) reach levies other than customs duties, such
as a dedicated import levy on digital downloads? No host guidance.

---

## 12.7 Domain name requirements

**What it asks.** Requirements on commercial domain names (Guide p.87). Three covered types: a rule that
companies have a local domain name to do electronic retail in the market; a local presence condition for
using a local domain name; a duty to appoint a local representative (Guide p.87). All commercial ccTLDs
and their sub-domains are in scope; .gov, .mil, .edu and .org are not listed because they are not
commercial (Guide p.87).

**Score set: {1, 0.5, 0}.** Methodology sheet 12.7: (1) physical presence required, or a requirement to
register a local domain name to conduct electronic retail = 1; (2) local representative required = 0.5;
(3) no restriction = 0. Guide p.87 matches: 1 for a physical presence condition or a duty to obtain a
local domain name for e-commerce; 0.5 for a mandated local administrator; 0 for no requirement. The Guide
says "local administrator" in the scoring sentence and "local representative" in the scope sentence;
the methodology says "local representative". Same meaning.

**Guide examples mapped to branches (inference; the Guide does not state their scores).** Brazil (foreign
companies need a representative in the country to register a domain) fits 0.5. New Caledonia (residence
or local registered office, plus a local administrative contact) fits 1. Viet Nam (licensed online
newspapers, websites, portals and social networks must use .vn) fits 1.

**Guide inconsistency.** The body text excludes ".org" (Guide p.87), but footnote 56 says the indicator
refers to .com, .net and .org within a ccTLD used for commercial purposes (Guide p.87). Second-level
".org.xx" domains (e.g. .org.au, named in Australia row 81) are therefore ambiguous.

**Presence tied to a domain stays here.** The weights text describes domain name requirements as covering
commercial or local presence requirements to buy local domain names (Guide p.91). A presence condition
that only gates the domain belongs to 12.7, not 3.5 or 12.8.

**Confusions (trap candidates).**
- **12.8.** Indonesia row 176 (filed under 12.7) describes the duty for foreign e-commerce operators above
  thresholds to appoint a local representative. That duty is coded under 12.8 (workbook round2 Indonesia
  row 178). A representative duty not tied to a domain belongs to 12.8 (Guide pp.87-88).
- **12.3.** Registration of commercial websites in a commercial registry is a 12.3 licensing example
  (Guide p.85, Colombia), not a domain name rule.
- **Government-only domain mandates** are out (Guide p.87); Lao PDR row 99's note applies this to the rule
  that party and government websites use .la.
- **"Prioritise" or "encourage" wording.** Indonesia rows 172, 176 and 177 code "must prioritise" or
  "encourage" .id use as 0, even though row 176 says Government Regulation 80/2019 Article 21 attaches
  sanctions (warnings, blacklisting, blocking, licence revocation). A sanction-backed prioritisation may
  be a mandate (1). Human ruling needed.
- **Registrant identity checks** (China 121) are not domain name requirements.
- Host training slides (slides.txt, PDF p.12) cite Cambodia's 2022 Notification No.0837 requiring the
  ".com.kh" domain in annual declarations of commercial enterprises, only as an example of a binding
  government notification. **Inference:** it is the kind of source that carries 12.7; not a Guide example.

**Exemplars chosen (7 rows, 7 economies).** Australia 81 and Thailand 125 (1, presence conditions);
Malaysia 108 and Singapore 91 (0.5, local administrative contact); Lao PDR 99 (negative, government
mandate excluded); China 121 (negative, identity information); Russia 107 (absence row).

**Rows I think are mislabelled or doubtful (excluded).**
- **r2-id-173 (.co.id), r2-id-174 (.net.id), r2-id-175 (.biz.id)**, all 0.5. The texts describe
  eligibility limited to entities operating in Indonesia, incorporated in Indonesia, telecom entities
  meeting local requirements, or Indonesian SMEs. None describes a local administrator duty. Under the
  Guide a presence condition scores 1 (Guide p.87), and comparable conditions score 1 in Australia 81 and
  Thailand 125/126. A possible reason for 0.5 on .co.id (brand holders may register with a brand
  certificate or power of attorney) is not stated as a local administrator.
- **r2-id-176** (0). Sanction-backed Article 21 prioritisation of .id; see above. Boundary, not used.
- **r2-th-124** (.co.th, 0.5). Plausible (foreign trademark owners must appoint an attorney-in-fact), but
  the row does not say the agent must be local. Not used.
- **r2-th-126** (.net.th, 1). Consistent with the Guide but sector-specific (telecom licensees). Not used;
  Thailand 125 preferred.

**Open questions.**
1. When one second-level category requires presence (.in.th) but another gives foreigners an agent route
   (.co.th), which decides? Thailand codes the stricter category (1); Indonesia codes presence-only
   categories 0.5. A host rule is needed.
2. Are ".org.xx" second-level domains in or out (body text vs footnote 56)?
3. Is a sanction-backed duty to "prioritise" the national domain a mandate?

---

## 12.8 Local presence requirements for online service providers (Tier B)

**What it asks.** Whether an economy imposes local presence requirements on online service providers
(Guide p.87). A local presence requirement means a physical representative office, local agent, legal
representative or post-box in the economy (Guide p.87). It targets preconditions for cross-border Mode 1
supply without a physical office and asks only for administrative representation, such as an agent or
contact point (Guide p.87). Registered office or registered agent rules under corporate law are excluded
because they apply after Mode 3 establishment (Guide pp.87-88). If one law imposes both an entity duty and
a representative duty, the measure is classified as commercial presence (Guide p.88). Guide examples:
Indonesia, Korea, Türkiye (Guide p.88).

**Criteria to scores.** Methodology sheet 12.8: (1) local presence requirement for at least one sector = 1;
(2) no requirement = 0. Guide p.88 matches.

**Lead check: "nearest neighbour of 6.3, overlaps 3.5".**
- **3.5 overlap: strongly supported.** 3.5 covers services supplied through a locally established office,
  branch, subsidiary or representative office (Mode 3) and excludes registration-only duties (Guide
  p.27). 12.8's definition also uses "representative office" (Guide p.87); the Guide resolves the overlap
  with the Mode 1 vs Mode 3 split and the stronger-obligation tie-break (Guide pp.87-88). Contrasting
  examples: Pakistan's permanent registered office for large social media companies is a 3.5 example
  (Guide p.27); Türkiye's appointed representative for social networks is a 12.8 example (Guide p.88).
  Workbook pairs show the host applying this: Australia 16/82 and Singapore 14/92 (corporate-law
  registered office coded 3.5 = 1, 12.8 = 0); Russia 23/108 (236-FZ coded 3.5 = 1, 12.8 = 0); Indonesia
  179's note rejects 3.5 because no entity is required; Mongolia 87 says only a commercial presence rule
  exists. Malaysia 109 is the exception (see below).
- **6.3 "nearest neighbour": not supported by any source.** 6.3 is about establishing or using a local data
  centre or server as a condition for services (Guide pp.51-52). Neither section refers to the other, and
  the Internal Guide's 6.3 FAQ contrasts 6.3 with 9.4 licensing, not with 12.8 (Internal Guide p.13). No
  6.3 row mentions a representative or local presence. The only 12.8 row that mentions a data centre is
  Malaysia 109, where a local data centre triggers a licence. Not written into any rule.
- **Sourced neighbours found instead** (all used in the codebook): 12.7 (local representative for domain
  registration, Guide p.87); 7.4 (China's PIPL Article 52 person-in-charge coded 7.4, row 63, vs Article
  53 offshore representative coded 12.8, row 122; Guide p.61 also mentions, inside the 7.4 examples, a
  Türkiye rule that foreign controllers appoint a local representative); 4.01 and 4.3 (local agents for
  patent filing and enforcement, Guide pp.29-31); 12.4.4 (Russia row 100: representative office for
  foreign payment systems); 9.4 (Indonesia row 121: electronic system operator registration coded 0 under
  9.4, while row 179 codes the liaison officers 12.8 = 1).
- Further trap candidate: India 7.4 row 96 codes a DPO who must be based in India as 7.4 = 1. A residence
  condition on a DPO stays in 7.4.

**Exemplars chosen (8 rows, 7 economies; 3 score-1, 5 score-0).** Indonesia 179 (canonical, the Guide's
example), China 122, Indonesia 178; Australia 82 and Singapore 92 (registered office negatives); Russia 108
(boundary with 3.5); Mongolia 87 (commercial presence only); Lao PDR 100 (absence row).

**Rows I think are mislabelled or doubtful (excluded).**
- **r1-my-109** (Malaysia row 109, score 1). The basis is a duty to be locally incorporated for the ASP(C)
  class licence for social media and messaging providers, plus cloud licensing triggered by local
  presence or a local data centre. Local incorporation is commercial presence, which goes to 3.5 under
  the tie-break (Guide p.88; Guide p.27). Malaysia already has 3.5 rows 19-20 on incorporation, and the
  licence itself is a 9.4 matter (Internal Guide p.12). Likely should be 0 under 12.8 unless a separate
  representative duty exists.
- **r2-th-128** (Thailand row 128, score 0). Section 11 of the Royal Decree on digital platform services
  requires offshore providers to appoint, in writing, a point of contact located in Thailand. The
  researcher reasoned that a contact point is not a representative office, local agent, legal
  representative or post-box. But the Guide says local presence only mandates administrative
  representation "(e.g., an agent or contact point)" (Guide p.87) and counts rules requiring "a local
  contact point" (Guide p.88). **Conflicts with the Guide; likely 1.** The Thailand 9.4 row 87 and 12.3
  row 112 treat the same decree as a non-licensing notification (0), which is a separate question.
- **r2-th-129** (Thailand row 129, score 1). Traffic-data retention notification; clause 9.3 requires
  personnel to coordinate with officers. The row gives no locality condition and no link to foreign
  providers supplying remotely, and the same notification is coded 7.3 = 1 (Thailand row 65). Doubtful
  12.8 evidence, and inconsistent with row 128, where an explicitly local contact point is coded 0.
- **r2-th-127** (Thailand row 127, score 1; the note records a change from 0 to 1). Foreign Business Act
  licence conditioned on residence in Thailand or a resident appointed representative. It is a
  horizontal licensing condition for foreigners operating a business in Thailand, and the Thailand 3.5
  notes say the FBA carries no commercial presence requirement. Whether it is a Mode 1 precondition for
  online services is unclear. Doubtful.
- **r2-id-180** (Indonesia row 180, score 1). Internally contradictory: it says a representative office
  must be established, then that the 2021 amendment has no explicit physical or representative office
  requirement. Duplicates row 179.
- **r2-in-157** (India row 157, score 0). Not wrong, but thin; its note about RBI cross-border payment
  aggregators (companies incorporated in India) is a 3.5 or 12.4.4 type fact, not 12.8.

**Disagreements.** Thailand 128 vs Guide pp.87-88. Malaysia 109 vs the Guide's tie-break and the AU/SG/RU
practice. Thailand 128 vs 129 inside one sheet. "Representative office" appears in both the 3.5
definition (Guide p.27) and the 12.8 definition (Guide p.87).

**Open questions.**
1. A law offering alternatives (branch, representative office or legal entity; Russia 236-FZ). The Guide's
   tie-break covers laws imposing both duties, not alternatives. The host coded it 3.5.
2. Does a representative duty that applies equally to domestic and foreign providers count? The Guide
   frames 12.8 as a precondition for foreign providers.
3. Threshold-based "deemed physical presence" (Indonesia Government Regulation 80/2019 Article 7, as
   described in row 176): no Guide text. The host coded the related Trade Regulation 31/2023 Article 18
   representative duty 12.8 = 1 (row 178).

---

## 12.9 Lack of legal framework for online consumer protection (Tier B)

**What it asks.** Whether an economy has adopted an online consumer protection legal framework
(Guide p.88). The law need not be e-commerce specific: a cross-sector consumer protection law can extend
to online purchases, and the protection may sit in the rules for offline transactions or in a separate
regulation (Guide p.88). The UNCTAD tracker is a pointer only (Guide p.88). The Guide's scoring chapter
gives an offline-only consumer protection regime as an example of a measure that raises costs by
treating online and offline differently (Guide p.10). No economy example and no exception is given.

**Criteria to scores (inverted polarity).** Methodology sheet 12.9: (1) no consumer protection framework
applicable to online commerce = 1; (2) consumer protection law applicable to online commerce = 0.
Guide p.88 matches.

**Lead check: "broad wording and high false-positive risk".**
- **Broad wording: confirmed.** Any consumer protection law that reaches online purchases counts, general
  or specific (Guide p.88). All 10 economies have one, so all 23 rows score 0 and the indicator is
  saturated at 0 in this sample.
- **False-positive risk: partly confirmed, as a tagging risk rather than a scoring risk.** Law families
  filed under 12.9 across the 23 rows:
  - 9 general consumer protection acts: AU 83, SG 93, CN 123, IN 159, ID 181, LA 101, MN 88, RU 109, TH 131;
  - 5 e-commerce consumer rules: MY 111, CN 124, IN 158, ID 183, ID 184;
  - 3 electronic transactions or e-commerce recognition laws: MY 110, ID 182, LA 103;
  - 1 unfair contract terms act: TH 130;
  - 1 telecom and internet consumer decision: LA 102 (secondary source only);
  - 1 e-money rule: MY 112;
  - 1 anti-scam rating and technical reference: SG 94;
  - 1 e-signature law: RU 110;
  - 1 set of data protection provisions: ID 185.

  At least RU 110, ID 185 and MY 110 are not consumer protection laws. Because presence scores 0 and every
  economy also has a real consumer law, none of these changed a score. The scoring risks for a pipeline
  are (a) polarity inversion, reading consumer protection text as a restriction and scoring 1, and (b) in
  an economy with no consumer law, accepting an e-signature, e-transactions or data protection law as the
  framework and producing a false 0. Neither can be observed in the sample. Consumer-protection language
  is also an exclusion test in 9.3 (Guide p.71; Internal Guide p.14) and 12.2 (Guide p.84), so provisions
  will be pulled toward 12.9 from those indicators.
- **Economy-level framing.** The host's Indicator Reference traps (rows 79-85) say framework indicators
  7.1 and 7.2 are answered once per economy and per-provision citations are not discoveries. The host
  says this only for 7.1 and 7.2; **applying it to 12.9 is my inference**. The codebook's once-per-economy
  rule cites the Guide p.88 wording instead.

**Exemplars chosen (8 rows, 8 economies, all score 0; no score-1 row exists).** Singapore 93 (general law
suffices), India 158 (e-commerce rules), Malaysia 111 (e-commerce regulations), Lao PDR 101 (scope
article), Mongolia 88 (general law; the draft does not count), China 124 (e-commerce law), Russia 109
(applies to foreign online sellers), Thailand 131 (same act coded 0 under 9.3, row 82).

**Off-target rows (excluded; scores are not wrong).**
- **r2-ru-110** (Russia row 110): Federal Law 63-FZ on electronic signatures. Not consumer protection; it
  relates to 12.12, which is non-regulatory (Non-regulatory note).
- **r2-id-185** (Indonesia row 185): Government Regulation 71/2019 personal data consent and breach
  notification. Pillar 7 material (Guide p.57).
- **r1-my-110** (Malaysia row 110): Electronic Commerce Act 2006, a legal recognition statute. Its consumer
  protection claim rests on the Consumer Protection Act recorded separately (row 111).
- **r1-my-112** (Malaysia row 112): e-money approval under the Financial Services Act; consumer clauses are
  incidental, and payment licensing is 12.4.4 territory (Guide p.85).
- **r1-sg-094** (Singapore row 94): anti-scam Transaction Safety Ratings and Technical Reference 76. These
  are ratings and guidelines, and whether they bind is unclear.
- **r2-la-102** (Lao PDR row 102): the note says only a secondary source was available for the Decision.

**Disagreements.** None on scores. The Guide gives no example or exception; the Indicator Reference note is
empty, so `exceptions` and `guide_examples` are empty lists in the codebook.

**Open questions.**
1. Partial coverage: what if the only consumer law excludes cross-border sellers or digital content? The
   Guide's test is applicability to online purchases; there is no guidance on partial coverage.
2. Do non-binding e-commerce guidelines (e.g. Singapore TR 76) count? The Guide asks for official laws
   and regulations (Guide p.88).

---

## Checker result
`python -X utf8 check_drafts.py g7`: 0 errors, 0 warnings (run after these notes were written).

## Top concerns
1. **Thailand 12.8 rows contradict the Guide and each other.** Row 128 codes an offshore platform's
   mandated in-country point of contact 0, but Guide pp.87-88 count contact points. Row 129 codes a
   coordinator duty with no locality condition 1. Human ruling needed before Thai rows are used as gold.
2. **Malaysia 12.8 row 109 scores local incorporation as local presence.** That breaks the Guide p.88
   tie-break and the host's own Australia, Singapore and Russia 3.5/12.8 pairs.
3. **Indonesia 12.6 rows 170 and 171** give 0.5 and 0 to the same zero-rated Chapter 99 tariff lines. The
   Guide's own Indonesia example supports 0.5.
4. **12.5 has no trustworthy score-1 row, and absence scores 1**, the reverse of the general absence rule.
   India 154 and Mongolia 84 are coded 1 while describing value-based exemptions.
5. **12.5 sources disagree on attribution and conversion detail.** The Guide cites the ICC (2016) and the
   Internal Guide cites UNECE for the USD 200 threshold. Only the Internal Guide fixes the IMF 31 August
   rate, and no workbook row uses it.
6. **12.7 cross-sheet inconsistency.** Indonesia codes presence-only second-level domains 0.5, while
   Thailand and Australia code comparable presence conditions 1. It is unclear whether the strictest
   category or the foreign-accessible route decides, and ".org" is both excluded (body) and included
   (footnote 56).
7. **12.9 is saturated at 0 and has no score-1 example.** Rows attach off-target laws (e-signature, data
   protection, e-commerce recognition). The real risks are polarity inversion and false 0s where an
   economy lacks a consumer law.
8. **The plan's claim that 12.8 is 6.3's nearest neighbour has no source.** Sourced neighbours are 3.5
   (strong), 12.7, 7.4, 4.01/4.3, 12.4.4 and 9.4; only those are written into rules.
