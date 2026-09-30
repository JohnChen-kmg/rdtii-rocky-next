<!-- Drafting notes for pillar 12 part 1 (12.01, 12.2, 12.3, 12.4.1-12.4.7). Written 2026-09-13 by a Claude drafting agent working from the host
sources in ../sources/. Checked by the lead for structure (checker, merge, citation audit) but NOT reviewed by a
human. Row IDs: r1-/r2-<economy>-<row> = gold_id in the repo gold set. -->

# g6 notes: Pillar 12, first part (12.01, 12.2, 12.3, 12.4.1-12.4.7)

Drafted 2026-09-13. Sources: Guide pp.83-94 (printed), Internal Guide pp.8, 11-14, host indicator tables
(reference + methodology), workbook rows in `rows_pillar_12.jsonl` / `rows_all.jsonl`. Training decks have
no pillar-12 content (grepped slides, assign2 as corrected at 01:36, answerkey, nikita_*, juntong_intro).

## Group-wide facts

- **ID mapping.** Host "12.01" = Guide's first Pillar 12 indicator, "Foreign equity limits in the e-commerce
  sector" (Guide p.84). The Internal Guide calls it "Pillar 12.1" (Internal Guide p.11). The same sentence
  says telecom equity caps are "Pillar 5.1", but host 5.1 is passive infrastructure sharing; telecom equity is
  host 5.2, and Internal Guide p.12 itself says "Indicator 5.2". So p.11's "5.1" is a numbering slip.
  Guide 12.10-12.13 are non-regulatory and out of scope (Internal Guide p.8).
- **Evidence type.** None of the g6 IDs is practice-based (Internal Guide p.8 lists only 3.4, 5.3, 9.1).
  For 12.2, 12.3 and 12.4 the Guide asks for official laws, regulations and other measures and treats the
  OECD Digital STRI only as a pointer (Guide pp.84-86).
- **Weights** (for the lead; not in the brief's schema): 12.01 = 22%, 12.2 = 11%, 12.3 = 11%, online payment
  limitations = 7% as one indicator (Guide pp.90-91). Footnote 53 says the online payment score is not a
  cumulative sum of its measures, but "a cumulative weight is applied" to reflect the breakdown (Guide p.86).
  The Guide does not say how the 7% is split across 12.4.1-12.4.7.
- **Typos in host names/criteria.** 12.4.7 reference name "others restrictions" is fixed to "other
  restrictions" in signatures_spec (criterion also reads "Other restrctions"). 12.3 exception note has
  "pertiaining"; 12.2 criterion has "can be purchases online". Only the 12.4.7 name was changed. The 12.3
  Tier B `category_official` keeps the methodology first line exactly.
- **guide_refs for 12.4.x.** The seven sub-indicators share one Guide section ("Online payment
  limitations", pp.85-86) and one scoring sentence (p.86). The shared defining sentence (p.85) is: "The
  indicator covers requirements for online payments and other requirements affecting the use of electronic
  payment and credit services." The Guide then lists six bullet types, which the methodology copies almost
  word for word as the score-1 criterion of 12.4.1-12.4.6. I used each bullet (verbatim; a list item, not a
  full sentence) as `asks` for 12.4.1-12.4.6. 12.4.7 has no bullet, so it takes the shared sentence. If the
  lead wants a full sentence for all seven, swap in the shared sentence (same page).
- **Codebook `sources`.** I added `related_guide_pages` to the 12.3 block to list the other Guide pages cited
  in its rules (pp.11, 28, 44, 71, 72, 84, 88). Drop the key if the merge script rejects unknown keys.

---

## 12.01 Foreign equity limits in e-commerce sector

**Asks.** Maximum foreign equity shares in the e-commerce sector specifically (Guide p.84). Foreign equity
shares are shares held by foreign natural or legal persons in a firm incorporated in the host economy
(Guide p.84). Guide example: the Philippines bans foreign ownership of retail trade enterprises with paid-up
capital below US$2.5 million (Guide p.84).

**Criteria to scores.** Methodology sheet 12.01: (1) minority stake (1-50%) allowed -> 1; (2) controlling
stake (51-99%) allowed -> 0.5; (3) full ownership (100%) allowed -> 0. The Guide says 1 if only a minority
(less than 50%) stake is allowed, 0.5 where a controlling stake (more than 50%) is allowed but caps exist,
0 if there is no limitation (Guide p.84). The SOE scoring metric used in 3.1 and 5.2 does not apply here
(Guide p.84).

**Guide / methodology / workbook differences.**
- An exact 50% cap: the methodology puts it in band 1 (1-50%). The Guide's wording ("less than 50%" /
  "more than 50%") leaves exactly 50% unplaced.
- A 0% ban is not listed in the methodology bands. The workbook scores a ban 1 (r2-in-142: India bars FDI in
  inventory-based B2C e-commerce). The Guide's own example (Philippines) is also a ban.
- 3.1's section says horizontal-framework caps are recorded only under 3.1, to avoid double counting
  (Guide p.25). So 12.01 takes only caps written for e-commerce.

**Trap candidates (promote later).**
- Telecom equity caps -> 5.2; caps in other digital-trade sectors -> 3.1 (Guide p.84; Internal Guide p.11;
  3.1 Indicator Reference note).
- Horizontal investment-law caps -> 3.1 only (Guide p.25).
- Equity caps on delivery/postal firms -> 3.1: the 49% cap on express delivery firms is coded 3.1 (r2-id-026,
  0.5) and 5.2 (r2-id-048), and scored 0 under 12.01 (r2-id-152). The 12.2 section also sends FDI measures on
  delivery firms to Pillar 3 (Guide p.84).
- Conditions inside e-commerce FDI policy map to Pillar 3 and 10: India's single-brand retail / e-commerce
  conditions appear as 3.4 screening above 49% (r2-in-030), 3.5 physical-store / office conditions
  (r2-in-031) and 10.3 30% local sourcing (r2-in-130). Guide p.11 states this split for Pillar 5 (telecom
  keeps 5.2 ownership caps; screening 3.4 and commercial presence 3.5 stay in Pillar 3). Applying it to
  Pillar 12 is an analogy.

**Exemplars.** India 142 (the only score-1 row), Lao PDR 85 (the only 0.5 row, 90% cap in the e-commerce
decree), China 109 (explicit lifting to 100%), Indonesia 152 (delivery-firm cap is not e-commerce),
Malaysia 96 (caps on physical retail formats are not e-commerce; reviewer thread in the row), Russian
Federation 94 (absence row citing the horizontal law).

**Suspect or contestable rows (not used).**
- r2-id-153 (score 0): e-commerce businesses under IDR 10 billion are reserved for domestic investors. The
  row treats this as a horizontal investment threshold. That is defensible under Guide p.25, but it is close
  to the Guide's Philippines example, a capital-threshold ban presented as an e-commerce equity limit
  (Guide p.84). Needs a ruling.
- r2-th-107 (score 0): Thai Foreign Business Act List 3 means majority-foreign firms need a permit, after
  which 100% is possible. Scored 0 as "full ownership allowed". Inference: a permit-gated majority may
  belong to 3.4 screening rather than 12.01 = 0. No host text settles it.

**Open questions.** Does a minimum-capital threshold for foreign e-commerce investors count as an equity
limit? How should an exact 50% cap be scored?

---

## 12.2 Online purchases and delivery limitations

**Asks.** Direct requirements on online purchases, and on delivery of products bought online, that affect
consumers or retailers (Guide p.84). The Guide lists four types: limits on the number of goods customers
import through e-commerce platforms; limits on the number of goods bought through platforms; delivery
limits applied to the delivery company; and delivery limits applied to users (how, where, when) (Guide p.84).

**Criteria to scores.** Guide: 1 if at least one requirement limits purchases via e-commerce or delivery,
otherwise 0 (Guide p.84). Methodology sheet 12.2: "(1) Any measure limits the number of products that can be
purchases online AND restrictions to delivery ... (2) No measure".

**Guide / methodology / workbook differences.**
- **AND vs OR.** The methodology criterion joins purchase limits and delivery restrictions with "AND". The
  Guide says "or", and the workbook scores either alone: r2-id-154 (delivery only) = 1, r2-cn-110 (purchase
  only) = 1. I followed the Guide and workbook. The lead should confirm.
- **Tax exclusion vs examples.** The Guide excludes taxation, customs duties and fees (Guide p.84). Yet its
  own Argentina example is a US$50/month tax-free allowance with a 50% tax above it, and Brazil's example is a
  per-shipment value cap for express imports (Guide p.84). China's row (r2-cn-110), from a tax policy notice
  setting annual and per-transaction quotas, scored 1. Working reading (inference): a quantity/value cap on
  the e-commerce channel counts even if it is enforced through tax; a pure tax obligation does not
  (r2-id-155, VAT collector thresholds, scored 0).
- **Exception wording.** The Indicator Reference note excludes limits applied "specifically to products
  related to consumer protection" (alcohol, tobacco, pharmaceuticals). The Guide frames it as limits applied
  for consumer-protection purposes, and adds two exclusions the note lacks: taxes/duties/fees, and FDI
  measures on delivery firms, which go to Pillar 3 (Guide p.84).

**Trap candidates.**
- Remote-sale bans on alcohol and tobacco, and online medicine licensing -> not scored (Indicator Reference
  note; Guide p.84; r2-ru-095 lists these and scores 0).
- VAT or tax collection on e-commerce -> not scored under 12.2 (Guide p.84; r2-id-155).
- General de minimis thresholds -> 12.5 (Guide p.86). Inference on where the line falls against the
  Argentina-type allowance.
- FDI conditions on marketplaces or delivery firms -> Pillar 3 (Guide p.84; r2-in-143, 25% single-vendor
  sales cap in FDI policy, scored 0).
- Postal/courier licences without limits -> 0 (r2-mn-072). They are also not 12.3 (Guide p.85).

**Exemplars.** Indonesia 154 (the Guide's own Indonesia example), China 110 (purchase quotas), Russian
Federation 95 (consumer-protection exception), Indonesia 155 (tax exclusion), India 143 (FDI-condition
boundary), Mongolia 72 (delivery licensing without limits).

**Suspect rows.** None clearly mislabelled. r2-cn-110 rests on the tax-exclusion tension above.

---

## 12.3 Licensing scheme for e-commerce providers (B2B and B2C) (Tier B)

**Asks.** Any licensing scheme for e-commerce providers, B2B and B2C (Guide p.85). The indicator focuses on
the licence imposed on e-commerce businesses; licences for other aspects, such as online payment services and
delivery, are not captured (Guide p.85; Indicator Reference note). Guide p.8 cites "a license to operate
businesses in the e-commerce sector" as a typical digital-sector policy.

**Criteria to scores.** Methodology sheet 12.3: any licence for e-commerce providers -> 1; no licence -> 0.
Guide: 1 if at least one licensing requirement for e-commerce providers (Guide p.85). There is no strictness
test, unlike 5.5 (Guide p.44) and 9.4 (Guide p.72).

**How 12.3 relates to 5.5, 9.4 and 12.4.4 (lead's question).**
- **9.4.** 9.4 excludes e-commerce platforms, "covered by Pillar 12" (Guide p.71; 9.4 Indicator Reference
  note: "License for e-commerce platform (captured under Pillar 12)"). ISP/ICP licences are 9.4 (Internal
  Guide p.12); broadcasting, cloud and data-centre licences are 9.4 (Internal Guide p.14). A licensing law for
  digital platforms covering online marketplaces plus other services is recorded under both 9.4 and 12.3
  (Guide p.11). Workbook: China's ICP licence regime appears in 9.4 (r2-cn-089, 0.5), in 3.5 (r2-cn-021, 1)
  and, with the EDI licence and E-Commerce Law art.12, in 12.3 (r2-cn-111, 1).
- **5.5.** No host text contrasts 12.3 with 5.5 directly. 5.5 is a licence for telecom services or
  facilities scored only when strict (Guide p.44); Internal Guide p.12 separates 5.5 from 9.4. China's EDI
  licence (online data and transaction processing) is legally a value-added telecom licence, yet it was
  coded 12.3 (r2-cn-111). The same telecom licensing measures sit under 5.5 in r2-cn-036. The codebook TRAP
  line says telecom service/facility licences are 5.5, while an e-commerce platform licence issued under
  telecom rules stays in 12.3.
- **12.4.4.** A payment-service licence is excluded from 12.3 (Guide p.85; Indicator Reference note) and is
  a 12.4 measure only when it has restrictive conditions: local incorporation, nationality, or limits on
  licence types or numbers (Guide p.85). Asymmetry: 12.3 scores any licence, 12.4.4 does not.

**Registration and notification: the main unresolved point.**
- The Guide's Colombia example is a registration duty: commercial websites of Colombian origin must be entered
  in the commercial registry and report transactions to the tax/customs authority (Guide p.85). The Lao
  example includes an acknowledgement certificate (Guide p.85). The Guide's weight rationale says e-commerce
  licensing "improves reliability and confirms the existence of the business" (Guide p.91). That is almost
  the stated objective of Thailand's e-commercial registration in r2-th-109.
- The workbook scores e-commerce-specific registration and notification 0:
  - r2-th-109: DBD e-commercial registration for transacting websites and marketplaces.
  - r2-th-112: prior notification of digital platforms, "Correct". The r2-th-109 note explains: "prior-
    Notification requirements not the licensing requirement so score it as 0.00".
  - r2-th-113: direct-marketing registration for online sellers above THB 1.8 million.
  - r2-id-156: ESO registration.
  The 9.4 rows follow the same logic (r2-th-087, r2-id-121/122/123 all 0).
- Horizontal registration for all businesses (r1-sg-080 = 0) is consistent under both readings.
- The codebook records this as an UNRESOLVED coding rule instead of picking a side. Economy-level scores do
  not change for Thailand (12.3 = 1 via r2-th-111) or Indonesia (1 via r2-id-157/158). Per-provision gold
  labels would change.

**Suspect rows (not used).**
- r2-th-111 (score 1): licence for digital identification and authentication services under the ETA /
  Royal Decree. This is a trust-service licence, not a licence for an e-commerce provider; the Guide limits
  12.3 to the licence on e-commerce businesses and excludes other aspects (Guide p.85). Likely mislabelled.
  Its home may be 9.4, but that is an inference with no host text.
- r2-id-157 (score 1): general trade business licence under Trade Law art.24, applying to all trading
  business actors. Borderline: horizontal registrations score 0 elsewhere. The row's note, quoting the STRI,
  says there is no specific e-commerce licence but the Trade Act obliges e-commerce producers or
  distributors to be licensed. r2-id-158 (e-commerce licence under PP 80/2019) is the cleaner Indonesian
  score-1 row and was used instead.
- r1-sg-079 (score 0): Broadcasting class licence that the row says automatically covers internet content
  providers "including e-commerce providers". The same instrument is 9.4 = 1 in r1-sg-062. Literally "any
  licence for e-commerce providers" (Methodology sheet 12.3), and Guide p.11 would dual-record it. Keeping 0
  follows Internal Guide p.14 (broadcasting licence -> 9.4). Needs a ruling.
- r2-th-109, r2-th-113, r2-id-156 (score 0): see registration issue above.
- r2-in-144 (score 0): foreign companies doing e-commerce must register under the Companies Act. A
  registration duty, consistent with the workbook's registration = 0 logic. Not used.

**Other trap candidates noted in the codebook.**
- Licence conditioned on setting up a local company -> also 3.5 (Guide p.28, Viet Nam online games example;
  r2-cn-021).
- Foreign e-commerce operators required to open a representative office or appoint a liaison officer ->
  12.8 (Guide p.88; r2-id-178/179/180). r2-id-179's note explicitly rejects a 3.5 link.
- Non-licensing duties in e-commerce statutes: E-Commerce Law art.31 retention -> 7.3 (r2-cn-062);
  PP 80/2019 art.59 data export condition -> 6.4 (r2-id-070).

**Exemplars.** Lao PDR 87 (the Guide's own example), Indonesia 158 (PP 80/2019 business licence), China 111
(EDI/ICP boundary with 9.4), Singapore 80 (horizontal registration = 0), Mongolia 73 (sector permits do not
reach e-commerce operators), Russian Federation 96 and Australia 71 (absence rows). I avoided all
registration/notification rows because of the unresolved conflict.

---

## 12.4 Online payment limitations: shared section (applies to 12.4.1-12.4.7)

- One Guide section (pp.85-86) with a shared lead sentence and six bullet types. One scoring sentence: for
  each measure, 1 if present, otherwise 0 (Guide p.86). Methodology has seven separate binary rows (1/0), each
  "(1) <type> (2) No restriction". Criteria differ only in the type named; the score set is identical.
  12.4.7 ("Other restrictions") has no Guide bullet.
- **Cryptocurrencies** are not listed because their implications are new and lack evidence (Guide p.86).
  Requirements on crypto or digital payment tokens (e.g. Singapore's 2021/2024 PSA amendments mentioned in
  r1-sg-081's note) -> not scored under any 12.4.x. Inference that this means "not scored" rather than
  "unlisted but possible".
- **Security standards (fn 52).** Any international standard referenced in the law counts as international
  (ISO/IEC, PCI DSS, other recognised frameworks) (Guide p.85).
- **Classification matters.** Because a cumulative weight is applied (Guide p.86, fn 53), putting a measure in
  the wrong sub-indicator changes the index even when the economy already has a 1 elsewhere in 12.4.

---

## 12.4.1 Online payment limitations: mandate local bank account

**Asks.** "Requirements to use a local bank account" (Guide p.85; Methodology sheet 12.4.1).

**Trap candidates.** Domestic processing of payments -> 6.1 (r2-ru-043 codes local processing of
international card payments as 6.1). Local storage of payment data -> 6.2 (r2-in-061). Currency mandates
-> 12.4.2. Incorporation conditions on payment licences -> 12.4.4 (Guide p.85).

**Exemplars.** India 145 (escrow with an Indian scheduled commercial bank), India 146 (loads only through
India-regulated instruments), Lao PDR 88 (payment system law: local bank accounts for online payment
services), Singapore 81, Thailand 114, Mongolia 74 (absence/negative).

**Suspect rows (not used).**
- r2-id-159 (score 1): e-money transactions must be processed domestically (BI Reg 20/6/PBI/2018 art.38),
  from which the row infers a need for local bank accounts. Domestic processing is not an account mandate.
  The row's own note, apparently government feedback, says "there is no explicit requirement to use a
  local bank account". Likely mislabelled for 12.4.1; the processing point is a 6.1 or 12.4.6 candidate.
- r2-la-089 (score 1): foreign digital service providers must settle VAT through a local bank account.
  This is about tax payment rather than online payment services. Borderline; not used.
- r1-my-099 (score 0): the impact text talks about currency, not bank accounts (copy from 12.4.2). The score
  is fine; the text is not a usable exemplar.
- r2-la-088 (used): its first rationale (e-signature applicants must show a Lao bank statement) is off-topic.
  The exemplar note points to the payment-system-law part only.

---

## 12.4.2 Online payment limitations: mandate currency used for international payments

**Asks.** "Requirements on the currency used for international payments" (Guide p.85; Methodology sheet
12.4.2).

**Workbook inconsistency (major).** The workbook disagrees on domestic local-currency rules.
- **Indonesia, score 1:** Currency Law art.21, Rupiah for transactions in Indonesia "except for certain
  cross-border transactions" (r2-id-160); e-money regulation art.44, payments in Indonesia in Rupiah
  (r2-id-162); PP 80/2019 art.60 (r2-id-163).
- **Indonesia, score 0:** BI Reg 17/3/PBI/2015, the same Rupiah obligation with an explicit exemption for
  international trade transactions (r2-id-161).
- **E-money in the national currency:** Lao PDR e-money "in Kip only" = 1 (r2-la-090, after a reviewer thread
  first agreed to 0), but Mongolia e-money equal to MNT = 0 (r2-mn-075).
- **PP 80/2019 art.60 wording:** Indonesian feedback in the notes of r2-id-159 and r2-id-166 says art.60 does
  not specifically mandate Rupiah. r2-id-163 also relies on MoT Reg 50/2020, which rows r2-id-158/166/167 say
  was revoked and replaced by MoT Reg 31/2023 (repealed = 0 host-wide).
- **Reading used in drafts:** the Guide's wording targets the currency of international payments. So a
  domestic-only rule with an international-trade exemption does not score (inference aligned with
  r2-id-161). The lead should rule and fix gold labels accordingly.

**Trap candidates.** Advertising ban on foreign-currency prices -> 9.3 (Guide p.71, Uzbekistan example).
Bank-account mandates -> 12.4.1. FX surrender or authorised-channel rules without a currency mandate -> 0
(r2-mn-076).

**Exemplars.** India 147 (Nepal/Bhutan trade settled in INR; the only clean score-1 row), Indonesia 161
(international trade exemption boundary), Thailand 116 (e-money in baht or foreign currency), Mongolia 76,
Singapore 82.

**Not used.** r2-id-160, r2-id-162, r2-id-163, r2-la-090 and r2-mn-075, for the conflicts above.

---

## 12.4.3 Online payment limitations: deviate national standards

**Asks.** "National standards for payment security that deviate from international standards" (Guide p.85;
Methodology sheet 12.4.3). Fn 52 counts any international standard referenced in law (Guide p.85).

**Thin data.** All 12 rows score 0; there is no score-1 example in either workbook. Exemplars teach
negatives only:
- China 114: national standard built on ISO/IEC 18092/21481.
- India 148: RBI directions require internationally accepted standards.
- Indonesia 164: ISO 27001/PCI-DSS alignment.
- Singapore 83: SGQR on EMVCo.
- Singapore 84: voluntary TR 76.
- Thailand 117: PromptPay on ISO 20022.

**Trap candidates (inference).** 11.4 covers deviations from international encryption standards: algorithms,
block size, key length, key management, disclosure beyond ISO validation (Guide p.81). A payment-specific
rule imposing a domestic encryption algorithm could be claimed by both. No host text allocates it; the draft
sends general encryption mandates to 11.4 and payment-security standards to 12.4.3. r2-la-091 (e-signature
key generation on FIPS 140-2, scored 0) is an e-signature rather than a payment measure and was not used.

---

## 12.4.4 Online payment limitations: licensing requirements

**Asks.** "Licensing requirements with restrictive conditions (such as local incorporation requirements,
nationality restrictions, or limitations on the types or numbers of licenses that can be obtained)"
(Guide p.85; Methodology sheet 12.4.4).

**Relation to 12.3.** Payment licences are excluded from 12.3 (Guide p.85; Indicator Reference note) and
scored here only with restrictive conditions. A plain payment licence is 0 in both places.

**Trap candidates.**
- Foreign equity caps on payment/e-money firms -> 3.1 (r2-id-023, 0.8).
- Resident or national director rules under general company law -> 3.3 (Guide p.26, Singapore example;
  r1-sg-011). A nationality condition inside the payment licence itself is 12.4.4 (r1-sg-085).
- A representative office required of foreign payment systems (r2-ru-100) could look like 12.8 local presence
  (Guide pp.87-88). The workbook keeps it here as a licence/registration condition.

**Exemplars.** Singapore 85 (incorporation + citizen/PR director), China 115 (PRC-established entity),
Thailand 118 (Thai-national resident director), Russian Federation 100 (representative office + register),
Australia 75 (foreign ADI branches licensed without retail deposits, i.e. a limit on licence type),
Malaysia 102 and Mongolia 79 (prudential-only conditions = 0).

**Suspect rows (not used).**
- r2-in-149 (score 0): payment aggregator authorisation with fees, standards and net-worth rules. The same
  RBI PA Guidelines require the PA to be "a company incorporated in India" (quoted in r2-in-145 under 12.4.1).
  Local incorporation is a named restrictive condition (Guide p.85), so 12.4.4 should likely be 1.
- r2-la-092 (score 1): conditions are financial capability, infrastructure, technical standards, minimum
  capital, shareholder suitability, and no licence transfer. None is a Guide-named restrictive condition, and
  similar prudential-only regimes scored 0 (r2-mn-079, r1-my-102). The workbook is inconsistent.
- r2-la-093 (score 1): licence for electronic signature certification providers (capital LAK 10 billion, Lao
  technical staff). Not an online payment licence; likely mislabelled. Its proper home is unclear (possibly
  9.4, inference).
- r2-id-165 (score 1): usable in principle, but it says BI Reg 20/6/PBI/2018 caps foreign ownership of non-bank
  e-money issuers at 49%, while r2-id-023 (3.1) cites the same regulation for an 85% foreign cap. r2-id-168
  cites the later BI Reg 23/6/PBI/2021 (15% domestic shares, 51% domestic voting rights). The facts need
  checking for superseded provisions.

---

## 12.4.5 Online payment limitations: ceiling on the maximum amount

**Asks.** "Ceilings on the maximum amount that can be paid by electronic payment methods" (Guide p.85;
Methodology sheet 12.4.5).

**Workbook practice.** Stored-value / e-wallet holding caps are treated as ceilings: Singapore 86, Indonesia
166, Mongolia 81, and Malaysia 103, which reasons that the wallet cap "has a similar effect". AML reporting
thresholds are not (Australia 76, Lao PDR 94). A limit above which extra authentication is required is not
(India 151). China 116 is a hard daily cap on low-authentication payments and scored 1.

**Trap candidates.** Tax-free monthly allowance on online purchases -> 12.2 (Guide p.84, Argentina
example). De minimis duty thresholds -> 12.5 (Guide p.86). Payment-aggregator value caps repeated under
"others" (r2-in-153) -> belong here (see 12.4.7).

**Exemplars.** Singapore 86, China 116, India 150, Indonesia 166 (score 1); Australia 76, Lao PDR 94,
India 151 (boundaries = 0).

**Suspect rows (not used).**
- r2-ru-101 (score 0): "No ceiling on the maximum amount is observed", but the row's note lists 161-FZ art.10
  e-money balance and monthly transfer caps (15,000 / 40,000 / 100,000 / 600,000 roubles). The note is
  headed "(From 2025 July)", so timing may explain it. Otherwise inconsistent with the wallet-cap rows = 1.
- r2-th-119 (score 1): providers must set a maximum e-money value per card or account themselves. The
  regulator sets no amount. Borderline.
- r1-my-103 (score 1): approval needed to raise wallet limits beyond RM5,000. Fine but indirect; not needed.

---

## 12.4.6 Online payment limitations: mandate specific intermediaries

**Asks.** "Requirements mandating the use of specific intermediaries for online payments" (Guide p.85;
Methodology sheet 12.4.6).

**Thin data.** Only one score-1 row, r2-in-152, and it is suspect. It says non-bank payment aggregators need
RBI authorisation while banks do not. That is a licensing requirement, not a mandate to route payments
through a specific intermediary. Other rows score "must use authorised/licensed providers" as 0 (r2-id-167,
r2-mn-082). Likely mislabelled (at most 12.4.4 material). No clean score-1 exemplar exists; the five
exemplars are negatives or boundaries.

**Open question.** r2-ru-043 (6.1, 0.5) describes Russia's requirement that domestic card transactions be
processed by the National Payment Card System as single operator. That reads like a specific-intermediary
mandate too, but r2-ru-102 scores 12.4.6 = 0. The 6.1 row's own note says no official source was located.
Should a national-switch mandate be dual-recorded under 6.1 and 12.4.6 (Guide p.11 dual-recording principle)?

**Trap candidates.** Duty to use licensed providers -> 0 (r2-id-167). Permissive engagement of agents or
aggregators -> 0 (r2-ru-102). Local processing of card payments -> 6.1 (r2-ru-043).

---

## 12.4.7 Online payment limitations: other restrictions

**Asks.** No bullet in the Guide. Anchored on the shared sentence covering "other requirements affecting the
use of electronic payment and credit services" (Guide p.85). Methodology sheet 12.4.7: "(1) Other
restrctions (2) No restriction".

**Residual logic (inference, not host-stated).** Measures that fit a named type (12.4.1-12.4.6) should go
there, not here. The workbook partly follows this: r2-id-168 (payment provider ownership conditions) scored 0
here, and r1-sg-088 (fund-safeguarding and licensed-agent rules) scored 0.

**Exemplars.** Russian Federation 103 (only clean score-1: foreign providers need an agreement with a Russian
operator plus central bank register listing), Singapore 88, Malaysia 105 (a market problem such as card fraud
is not a measure; official-source rule, Internal Guide p.8), Indonesia 168, Mongolia 83 (AML duties not scored).

**Suspect or overlapping rows.**
- r2-in-153 (score 1): per-transaction caps on export receipts via online gateways (USD 10,000) and the PA-CB
  ₹25 lakh per-unit cap. The latter is already 12.4.5 = 1 (r2-in-150). The row says the 2011 gateway
  instructions were replaced by the October 2023 PA-CB circular, so the USD 10,000 cap may be repealed
  (repealed = 0 host-wide). Genuine "other" content is thin (e.g. import payments cannot use small PPIs). Not
  used; possible double count with 12.4.5.
- r2-ru-103 (used, score 1): requiring foreign payment providers to act through a Russian money transfer
  operator could equally be 12.4.6 (specific intermediary). The workbook put it here and scored 12.4.6 = 0
  (r2-ru-102). The sub-indicator choice affects the cumulative weight (Guide p.86 fn 53).

---

## Top concerns

1. **12.3 registration vs licence.** The Guide's Colombia example (registration) and weight rationale point to
   registration counting (Guide pp.85, 91). The workbook scores e-commerce registration and notification 0
   (r2-th-109, r2-th-112, r2-th-113, r2-id-156). This needs a human ruling before gold labels are trusted. The
   codebook carries it as UNRESOLVED.
2. **12.2 criterion "AND".** Methodology sheet 12.2 requires purchase limits AND delivery restrictions. The
   Guide (p.84) and workbook score either one. Drafts follow the Guide.
3. **12.4.2 local-currency rules.** Indonesia scores 1 in rows 160, 162, 163 but 0 in row 161 for the same kind
   of rule. Lao PDR e-money-in-Kip = 1 vs Mongolia e-money-in-MNT = 0. Row 163 also leans on a revoked
   regulation.
4. **Suspect 12.4.x rows that directly teach the wrong sub-indicator:**
   - r2-in-152: licensing coded as specific intermediary; it is the only score-1 row for 12.4.6.
   - r2-id-159: domestic processing coded as local bank account.
   - r2-la-093: e-signature licence coded as payment licensing.
   - r2-in-149: 0 despite a local-incorporation condition.
   - r2-ru-101: 0 despite e-money caps.
   - r2-in-153: 12.4.5 caps repeated under 12.4.7.
5. **12.3 row r2-th-111.** A digital ID/authentication licence scored 1 as an e-commerce licence, likely
   mislabelled. r1-sg-079 (class licence covering e-commerce providers, 9.4 = 1 elsewhere) scored 0, which
   conflicts with Guide p.11 dual recording.
6. **Thin score spread.**
   - 12.4.3 has no score-1 row at all.
   - 12.4.6 has no clean score-1 row.
   - 12.01 has one 1 and one 0.5.
   - 12.4.2 and 12.4.7 have one clean 1 each.
   Signatures for these rely on Guide text more than on labels.
7. **12.01 band edges.** The 0% ban is missing from the methodology bands (workbook scores 1). The exact-50%
   cap is ambiguous between Guide and methodology. Capital-threshold reservations for domestic investors
   (r2-id-153 = 0) sit against the Guide's Philippines example (p.84) and the horizontal-cap rule (p.25).
8. **Cumulative weighting in 12.4.** Misallocating a measure among 12.4.1-12.4.7 moves the index (Guide p.86
   fn 53), yet the Guide defines no residual rule for 12.4.7 and no split of the 7% weight.
