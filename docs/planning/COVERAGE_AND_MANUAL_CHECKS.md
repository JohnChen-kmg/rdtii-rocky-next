# Coverage register: what the tool automates, where each answer lives, and what a researcher checks by hand

Generated 2026-09-20 from the instrument's `indicator_order.yaml` (IDs, names, pillars, evidence type) and
`indicators.yaml` (depth tier), then annotated. Regenerate the tables from those files when they change;
hand-edit only the sections marked as such. The machine-readable form of the same marks belongs in the
instrument (decision D14). The two must agree.

Revised the same day after the developer's correction: an earlier version treated everything below the
statute as outside the legal dataset. That is China's case, not the general one. In most jurisdictions the
official gazette or legislation database publishes delegated legislation too, so the general gap is
narrower and is stated below.

## The rule

The developer's decision of 2026-09-20: **the tool automates pillars 6 and 7.** Every other indicator, in
every economy, is **marked for a researcher's manual check**, with the reason, rather than built. Where an
automated indicator's operative tier is not published by an economy's portal, that economy gets the same
mark for that indicator.

**The mark in the output.** Every row, or null row, for a marked indicator carries one sentence in Notes,
and the review screen shows the same flag:

> Not automated. The result for this indicator may come from a source other than the legal dataset.
> Check it outside the tool. Reason: outside the automated scope, or practice or external evidence, or
> the tier that answers it is not published by this economy's portal.

## Where an indicator's answer lives, in general

This holds for any economy. It comes from the shape of legal systems, not from any one country's portal.

Every legal order stacks its instruments. Primary legislation sets frameworks and principles. Delegated
legislation carries the operative detail: regulations, orders, decrees, ministerial regulations, customs
notifications. Below that sit regulator and administrative instruments: central-bank circulars, regulator
decisions, licence conditions, registry policies. Below that, technical standards, which are not law but are
made binding by reference. Below that, practice: what a regulator actually does, who actually owns what.

**How far down the official source goes differs by legal family, and that is the point the China survey
hid.** In most jurisdictions the official gazette or legislation database publishes delegated legislation,
because that is where a regulation acquires force. In civil-law systems built on legal normative documents,
such as Viet Nam, Russia and Kazakhstan, ministry and central-bank circulars are legal normative documents
and sit in the same database. In common-law systems, such as Singapore, Malaysia, Australia and India,
rules and regulations made under an Act are subsidiary legislation and sit on the legislation portal, but a
regulator's notices, guidelines and policy documents are administrative and sit on the regulator's own
site. China is the exception among the economies surveyed: its central database stops above departmental
rules, and it forbids crawling.

Legislatures delegate on purpose. A number, a list or a technical specification changes often and needs
expertise, so it is put where the executive or a regulator can change it. That gives one test that
predicts where an indicator's answer lives: **what kind of thing is the answer?**

| Code | Nature of the answer | Where it lives | In the official legal dataset? |
| :---- | :---- | :---- | :---- |
| **L** | A rule's existence: does a framework, a safe harbour, a prohibition exist | Primary legislation | Yes |
| **Dg** | A number or a list set by delegated legislation: a threshold, cap, period, customs list, negative list issued as a decree | The official gazette or legislation database | Yes, in most jurisdictions. Not in China's database. **Ours collects it only under core or seed acts, decision 12** |
| **Dr** | A number, list or procedure set by a regulator or administrative body: central-bank circulars, regulator decisions, licence conditions, registry policies | The regulator | Yes where such instruments are legal normative documents (civil-law systems of that kind). **No in common-law systems**, where they sit on the regulator's site |
| **T** | A technical specification | Standards documents, made binding by reference | No |
| **F** | A fact or a practice: who owns shares, what is actually blocked, whether screening was ever applied | Ownership records, announcements, reports | No |
| **W** | An international trade posture: measures in force, participation in a moratorium | WTO notifications, administrative trade determinations | Partly. Each measure is gazetted domestically, but the count is assembled at the WTO |

Mixed codes name the operative answer first. "L, Dg" means the statute states the rule and a regulation
sets the number. "Dr, Dg" means the instrument is usually a regulator's, though in some economies it is
a gazetted regulation.

### Across the 61 in-scope indicators

| Where the answer lives | Count | Indicators |
| :---- | ----: | :---- |
| **Statute** (L first) | 22 | 3.3, 4.01, 4.2, 4.3, 4.5, 4.6, 4.1, 5.5, 5.7, 6.1, 6.4, 7.1, 7.2, 7.3, 7.4, 7.5, 8.1, 8.2, 9.3, 11.1, 12.3, 12.9 |
| **Gazetted delegated legislation** (Dg first). Official everywhere but China's database; a collection-scope question for us | 16 | 2.1, 2.3, 3.1, 3.2, 3.5, 5.2, 10.1, 10.2, 10.3, 10.4, 11.2, 11.3, 12.01, 12.2, 12.5, 12.8 |
| **Regulator or administrative instrument** (Dr first). Official; in the legal dataset in civil-law systems, on the regulator's site in common-law ones | 17 | 2.2, 4.9, 5.1, 5.4, 6.2, 6.3, 8.3, 8.4, 9.4, 12.4.1, 12.4.2, 12.4.3, 12.4.4, 12.4.5, 12.4.6, 12.4.7, 12.7 |
| **Outside any law database, everywhere** (F, T, W) | 6 | 1.4, 3.4, 5.3, 9.1, 11.4, 12.6 |

**So the general answer to "which indicators need checking outside the legal dataset" has three parts.**

1. **Six, in every economy**, because no legal instrument states the answer: 1.4, 3.4, 5.3, 9.1, 11.4, 12.6.
2. **17 more in common-law economies**, where the regulator's instrument is administrative and off the
   legislation portal: the Dr set above. In civil-law systems of the legal-normative-document kind these are in
   the official dataset.
3. **Everything below the statute in China**, because its database omits the tier. That is 33
   indicators plus the six, and it is the case the survey measured.

The 16 gazetted-delegation indicators are not a dataset gap in most economies. They are a scope
question for our crawler, which collects subsidiary instruments only under core or seed acts. Widening that
is decision (b) in the issue record, not a manual check.

### The quickest test: read the portal's own name

Across the nine finale economies there is a pattern worth one paragraph, because it costs nothing to apply
and it predicted the China result before anyone counted indicators.

**A portal named after a class of document stops at that class. A portal named after the system, the act
category or the act of publication carries the whole ladder.** `flk.npc.gov.cn` is 法律法规, "laws and
administrative regulations", and the tiers below it have different names in Chinese, 部门规章 departmental
rules, 规范性文件 normative documents, 目录 catalogues, which is exactly what it does not carry. `indiacode.nic.in`
is the India **Code**, the Acts, and the rules and notifications under them are in the **Gazette** instead.
Against that, `vbpl.vn` is *văn bản pháp luật*, legal normative documents, a category Viet Nam's law on
promulgation defines to include ministerial circulars; `adilet.zan.kz` is the justice ministry's bank of
normative legal acts, and a Kazakh ministerial order takes effect by being registered there; `pravo.gov.ru`
is *официальное опубликование*, official publication, which is an act, not a document class; `legalinfo.mn`
is legal **information**; and a *gazette*, in Bangkok, Vientiane or Dili, is by definition where an
instrument of any tier acquires force. Indonesia is the one that misleads: `peraturan.go.id` promises
*peraturan*, regulations, but the hub that answered us is the State Secretariat's, and the ministerial layer
sits across a federation of other JDIH sites.

### The other half of the question: depth, not breadth

The name test answers how far down a source goes. It says nothing about how much of the evidence sits
there at all. A legislation portal publishes legislation. It does not publish a central bank’s policy
document, a communications regulator’s determination or a data-protection commissioner’s guidance, and
for 17 of the 61 indicators that is where the answer is. So a source can carry every tier of legislation
and still miss much of the evidence, because much of the evidence was never legislation.

Resolving every one of the host’s coded rows to its operative publisher, rather than counting the links
a researcher happened to paste, gives the size of the problem. **For pillars 6 and 7 the median economy
needs two websites in total.** Eight of ten need three or fewer; Mongolia and the Russian Federation need
only the main database; China needs five, Thailand eight and India ten. Across all twelve pillars the
median is eight, from two for Mongolia to twenty-three for India. Roughly three fifths of that apparatus
serves pillars the tool does not automate: customs, procurement, standards bodies, IP offices and domain
registries never touch pillars 6 and 7 at all.

**Three of ten need a different main database** than the one our survey named: Lao PDR should target the
National Trade Repository rather than the Gazette, Thailand the Council of State’s current domain, and
Indonesia the audit board’s collection. Two more need a corrected address rather than a different source.
The per-economy sets, the recurring source categories and the decisions each raises are in
`ISSUES\2026-09-21_minimal-source-set.md`.

One consequence reaches the mapping stage. In four economies the main law database is barely cited by the
host at all, not once in Malaysia, so **a discovery comparison must match on instrument name and section,
never on URL**, or it will score the main database at zero and be measuring the wrong thing.

### Do the official sources publish the delegated tier? What the survey saw

The nine finale economies, plus Timor-Leste. From the scraping workshop's portal survey in `C:\Users\woshi\Desktop\rdtii-finale-1-scraping\countries\_finale-survey`.
"What the name says" and "general position" are readings of the source's own title and of legal knowledge;
"survey saw" cites a file in that folder. The survey read robots.txt and a few listings. It fetched no law.

| Economy | Official source | What the name says | Delegated tier | What the survey saw |
| :---- | :---- | :---- | :---- | :---- |
| Viet Nam | `vbpl.vn` | *Văn bản pháp luật*, legal normative documents, the category itself | **In it.** Laws, decrees, decisions and ministerial circulars are all legal normative documents | Robots file saved, a sitemap offered. No survey note yet |
| Kazakhstan | `adilet.zan.kz` | *Ädilet*, justice: the Ministry of Justice's bank of normative legal acts | **In it.** Ministerial orders take effect by state registration there | Robots file saved. No survey note yet |
| Russian Federation | `pravo.gov.ru`, `publication.pravo.gov.ru` | *Официальное опубликование*, official publication, an act rather than a class | **In it.** Federal laws, presidential and government acts, and registered ministerial orders | `ru-russian-federation.md`: full amendment history per law; an attribute search with act-type and issuing-body fields |
| Mongolia | `legalinfo.mn` | Unified Legal **Information** System | **In it.** Laws with government and ministerial resolutions | `mn-mongolia.md`: no robots rules published at all |
| Thailand | `ratchakitcha.soc.go.th`, `krisdika.go.th`, `law.go.th` | *Ratchakitchanubeksa*, the Royal **Gazette**; the Council of State; the Law Portal | **In the gazette.** Ministerial regulations and notifications take effect on publication. The Council of State site is consolidated Acts | `th-thailand.md`: three sources with different roles; the Council of State's certificate fails; the portal is behind Cloudflare |
| Lao PDR | `laoofficialgazette.gov.la` | The Official **Gazette**, required by the 2013 Law on Making Legislation | **In it.** Laws and decrees, organised by issue | `la-lao-pdr.md` and the 2026-09-20 exploration: the only official source, and the PDFs are scans with no text layer |
| Timor-Leste | `mj.gov.tl/jornal` | *Jornal da República*, the **gazette** | **In it.** Série I carries laws, decree-laws, government decrees and ministerial diplomas | `tl-timor-leste.md`: six categories read, 2,000 documents; the Diploma Ministerial category was not read |
| Indonesia | `peraturan.go.id`, `jdihn.go.id`, `jdih.setneg.go.id` | *Peraturan*, regulations. The name promises the tier | **Split.** Official, but across a federation of JDIH sites and ministry sites, not one hub | `id-indonesia.md`: the two national hubs never answered; the one that did carries laws and government regulations, "not the ministerial and regional layers where much of Indonesia's data and cyber rulemaking sits" |
| India | `indiacode.nic.in`, `egazette.gov.in` | The India **Code**, the Acts. The **Gazette**, separately | **In the gazette, not the code.** Rules and notifications are gazetted; the consolidated FDI policy is a departmental circular on the ministry's own site | `in-india.md`: both main sites answer 403 to our client; the gazette's certificate fails |
| China | `flk.npc.gov.cn` | 法律法规, laws and administrative **regulations**. The name stops where the database stops | **Not in it.** Departmental rules, normative documents, national standards, catalogues and negative lists are all outside | `cn-china-coverage.md`: 43 of 61 indicators not answerable from what it carries; `robots.txt` forbids automated collection for every agent |

So of the nine, **one is a genuine tier gap**. Seven publish the delegated tier in the official source, and
for those the obstacle is technical or a matter of our own collection scope. Indonesia is a dispersal
problem rather than an omission. The manual-check marks in the tables below are therefore driven by the
nature of the answer, not by the portal, except in China.

## Summary of automation

| Class | Count | What it means |
| :---- | ----: | :---- |
| **A** Automated | 9 | Pillars 6 and 7. Retrieved, extracted, mapped and verified by the tool |
| **M** Manual check | 52 | In scope for the index, not automated. Marked in every output. A researcher answers it from the sources named below |
| **X** Excluded | 14 | Non-regulatory. The host fills these from external databases and treaty status. No row is written. One of them, 6.5, is on the host's list; the other 13 are not (instrument D10) |

## A. Automated: pillars 6 and 7

Automated does not mean the statute holds the whole answer. Six of the nine have operative detail below the
statute. The crawler collects gazetted subsidiary legislation under core or seed acts; regulator instruments
such as central-bank circulars are collected only where a seed names them.

| ID | Indicator | Tier | Nature | Where the answer lives | Researcher still checks |
| :---- | :---- | :---- | :---- | :---- | :---- |
| 6.1 | Ban and local processing requirements | A | L, Dg | Transfer bans are in the data-protection statute; local-processing mandates are often sectoral regulations | Statute, with delegated detail as coded |
| 6.2 | Local storage requirements | A | Dr, Dg | Storage-location duties are mostly sectoral: central-bank and health-regulator instruments, sometimes gazetted regulations | Regulator instrument. In the official database where such instruments are legal normative documents; on the regulator's site in common-law systems |
| 6.3 | Infrastructure requirements | A | Dr, Dg | Infrastructure mandates are sectoral regulator instruments or licence conditions | Regulator instrument. In the official database where such instruments are legal normative documents; on the regulator's site in common-law systems |
| 6.4 | Conditional flow regimes | A | L, Dg | Conditional-transfer regimes are in the statute; adequacy lists and standard clauses are delegated | Statute, with delegated detail as coded |
| 7.1 | Lack of comprehensive legal framework for data protection | A | L | Existence of a comprehensive data-protection law. Primary law, one answer per economy | Statute |
| 7.2 | Lack of dedicated legal framework for cybersecurity | A | L | Existence of a dedicated cybersecurity law. Primary law, one answer per economy | Statute |
| 7.3 | Minimum period of data retention requirements | A | L, Dg | Minimum retention periods appear in statutes and in regulations in roughly equal measure | Statute, with delegated detail as coded |
| 7.4 | Data Protection Impact Assessment (DPIA) or Data Protection Officer (DPO) requirements | A | L, Dg | The DPO duty is usually in the statute; the thresholds that trigger it are often regulations | Statute, with delegated detail as coded |
| 7.5 | Requirements to allow government access to personal data | A | L | Access powers and their judicial gate are in criminal procedure codes and interception statutes | Statute |

## M. Manual check: every other in-scope indicator

The "where the answer lives" column is the general legal position. It is not verified per economy. A
researcher confirms it for each economy and records what they find in the per-economy section.


### Pillar 1: Tariffs and Trade Defence

| ID | Indicator | Tier | Nature | Where the answer lives, in general | Check |
| :---- | :---- | :---- | :---- | :---- | :---- |
| 1.4 | Trade defence measures including anti-dumping, countervailing duties and safeguards on ICT-related goods imported by other economies within the considered United Nations region | C | W | Each measure is an administrative determination, gazetted domestically and notified to the WTO. The statute only enables them; the WTO gateway is the practical index | Outside any law database, in every economy |

### Pillar 2: Public Procurement

| ID | Indicator | Tier | Nature | Where the answer lives, in general | Check |
| :---- | :---- | :---- | :---- | :---- | :---- |
| 2.1 | Foreign exclusions from public procurement related to ICT goods and digital services | B | Dg, Dr | Exclusions and preferences sit in procurement regulations, with buy-national circulars and policies below them | Official gazette or legislation database in most jurisdictions. Our crawler collects it only under core or seed acts |
| 2.2 | Specific requirements on source codes, encryption and trade secrets | C | Dr, Dg | Source-code and security-review conditions are cyber-agency or procurement rules, sometimes gazetted regulations | Regulator instrument. In the official database where such instruments are legal normative documents; on the regulator's site in common-law systems |
| 2.3 | Limitations in procurement bidding | B | Dg | Bidding thresholds and registration conditions are in procurement regulations | Official gazette or legislation database in most jurisdictions. Our crawler collects it only under core or seed acts |

### Pillar 3: Foreign Direct Investment

| ID | Indicator | Tier | Nature | Where the answer lives, in general | Check |
| :---- | :---- | :---- | :---- | :---- | :---- |
| 3.1 | Foreign equity limits in sectors relevant to digital trade | C | Dg | Equity caps sit in negative lists issued as decrees or presidential regulations. India's consolidated FDI policy is administrative; China's list is off its database | Official gazette or legislation database in most jurisdictions. Our crawler collects it only under core or seed acts |
| 3.2 | Joint venture requirements | C | Dg | Joint-venture conditions are negative-list entries | Official gazette or legislation database in most jurisdictions. Our crawler collects it only under core or seed acts |
| 3.3 | Nationality or residency requirements for board of directors or managers | C | L | Company or sector law states who may sit on a board | Statute |
| 3.4 | Screening of investment and acquisitions | C | F | The regime is in law. The top score needs a case where screening actually blocked a digital investment | Outside any law database, in every economy |
| 3.5 | Commercial presence requirements to offer cross-border services in sectors relevant to digital trade | B | Dg, L | Whether a licence needs local establishment is usually in sector licensing regulations; some sector statutes say it | Official gazette or legislation database in most jurisdictions. Our crawler collects it only under core or seed acts |

### Pillar 4: Intellectual Property Rights

| ID | Indicator | Tier | Nature | Where the answer lives, in general | Check |
| :---- | :---- | :---- | :---- | :---- | :---- |
| 4.01 | Patent application issues | C | L | Patentability of software and disclosure burdens are in the patent statute, with office guidelines below | Statute |
| 4.2 | Patent enforcement issues: civil and administrative procedures and remedies; and provisional measures | C | L | Remedies and provisional measures are in the patent statute and the civil procedure code, with court rules below | Statute |
| 4.3 | Patent enforcement issues: others | C | L | Other enforcement issues: statute and procedure code, with court rules and, where used, judicial interpretations | Statute |
| 4.5 | Lack of copyright framework and exceptions | C | L | Existence of a copyright framework and its exceptions. Primary law | Statute |
| 4.6 | Online copyright enforcement issues: civil and administrative procedures and remedies; and provisional measures | C | L | Online enforcement remedies: statute and procedure code, with court rules below | Statute |
| 4.9 | Mandatory disclosure of trade secrets, such as souce code and algorithms | B | Dr | Algorithm registration, source-code and data disclosure duties are regulator rules, not statutes | Regulator instrument. In the official database where such instruments are legal normative documents; on the regulator's site in common-law systems |
| 4.1 | Lack of effective trade secrets legal framework | C | L | Existence of a trade-secrets framework. Primary law | Statute |

### Pillar 5: Telecom Regulations & Competition

| ID | Indicator | Tier | Nature | Where the answer lives, in general | Check |
| :---- | :---- | :---- | :---- | :---- | :---- |
| 5.1 | Lack of passive infrastructure sharing | C | Dr, L | A sharing obligation is usually a regulator regulation or licence condition; the telecom law may state the principle | Regulator instrument. In the official database where such instruments are legal normative documents; on the regulator's site in common-law systems |
| 5.2 | Foreign equity limits in telecom sector | C | Dg, L | Telecom equity caps sit in the telecom law in some economies and in the investment negative list in others | Official gazette or legislation database in most jurisdictions. Our crawler collects it only under core or seed acts |
| 5.3 | Shares owned by the Government in telecom companies | C | F | An ownership fact. Company registers, state-enterprise lists, market reports. No legal instrument states it | Outside any law database, in every economy |
| 5.4 | Lack of functional/accounting separation | C | Dr | Functional or accounting separation is imposed by regulator decision or licence condition | Regulator instrument. In the official database where such instruments are legal normative documents; on the regulator's site in common-law systems |
| 5.5 | Licensing requirements in telecom sector for operators | B | L, Dg | The licensing regime is in the telecom law; categories, fees and conditions are in regulations | Statute, with delegated detail as coded |
| 5.7 | Lack of independent telecom authority | C | L | Formal independence of the regulator is written in the telecom law. De facto independence would be practice | Statute |

### Pillar 8: Internet Intermediary Liability

| ID | Indicator | Tier | Nature | Where the answer lives, in general | Check |
| :---- | :---- | :---- | :---- | :---- | :---- |
| 8.1 | Lack of safe harbour for copyright infringements | B | L | Existence of a copyright safe harbour. Primary law | Statute |
| 8.2 | Lack of safe harbour for other illegal activities | B | L | Existence of a general safe harbour. Primary law | Statute |
| 8.3 | User identify requirements | B | Dr, Dg | Real-name and SIM registration duties are regulator regulations or ministry orders | Regulator instrument. In the official database where such instruments are legal normative documents; on the regulator's site in common-law systems |
| 8.4 | Monitoring requirements | B | Dr, Dg | Monitoring duties on intermediaries are regulator regulations or orders | Regulator instrument. In the official database where such instruments are legal normative documents; on the regulator's site in common-law systems |

### Pillar 9: Content Access

| ID | Indicator | Tier | Nature | Where the answer lives, in general | Check |
| :---- | :---- | :---- | :---- | :---- | :---- |
| 9.1 | Blocking or filtering commercial web content | B | F | The power to block is in law; the blocklist and the practice are published in no instrument at any tier | Outside any law database, in every economy |
| 9.3 | Online advertising requirements | C | L, Dg | Advertising law states the principle; online-specific rules are regulator instruments | Statute, with delegated detail as coded |
| 9.4 | Licensing requirements for online content providers and applications (social media platforms, new providers, VPN, cloud servics, etc.) | B | Dr, Dg | Licensing of content providers and applications is set by regulator or ministry rules | Regulator instrument. In the official database where such instruments are legal normative documents; on the regulator's site in common-law systems |

### Pillar 10: Non-technical NTMs

| ID | Indicator | Tier | Nature | Where the answer lives, in general | Check |
| :---- | :---- | :---- | :---- | :---- | :---- |
| 10.1 | Import ban applied to ICT goods and online services (e.g. network equipment, servers, handsets, applications, and data processing) | C | Dg | Import bans are prohibited-goods lists under the foreign-trade or customs law, gazetted | Official gazette or legislation database in most jurisdictions. Our crawler collects it only under core or seed acts |
| 10.2 | Other import restrictions on ICT goods and online services | C | Dg | Import licensing and restrictions are gazetted lists and orders | Official gazette or legislation database in most jurisdictions. Our crawler collects it only under core or seed acts |
| 10.3 | Local content requirements | C | Dg, Dr | Local-content lists are gazetted; preferences often arrive as policy notices | Official gazette or legislation database in most jurisdictions. Our crawler collects it only under core or seed acts |
| 10.4 | Export restrictions on ICTgoods and online services | C | Dg | Export restrictions are gazetted export-control lists | Official gazette or legislation database in most jurisdictions. Our crawler collects it only under core or seed acts |

### Pillar 11: Standards and Procedures

| ID | Indicator | Tier | Nature | Where the answer lives, in general | Check |
| :---- | :---- | :---- | :---- | :---- | :---- |
| 11.1 | Lack of transparent technical standards | C | L, F | The standards framework is in law; transparency is a practice of publication and WTO TBT notification | Statute |
| 11.2 | Self-certification limitations for product safety (radio transmissions, EMC/EMI) | C | Dg, T | Self-certification limits are gazetted technical regulations, referencing standards documents | Official gazette or legislation database in most jurisdictions. Our crawler collects it only under core or seed acts |
| 11.3 | Product screening and testing requirements | C | Dg, T | Screening and testing requirements are gazetted technical regulations, referencing standards documents | Official gazette or legislation database in most jurisdictions. Our crawler collects it only under core or seed acts |
| 11.4 | Deviation from international encryption standards (ISO, IEC, ITU, FIPS, AES, TDES, and ECC) | C | T | The deviation is itself a national standard compared with ISO, IEC or ITU. A standards document, not a law | Outside any law database, in every economy |

### Pillar 12: Online Sales and Transactions

| ID | Indicator | Tier | Nature | Where the answer lives, in general | Check |
| :---- | :---- | :---- | :---- | :---- | :---- |
| 12.01 | Foreign equity limits in e-commerce sector | C | Dg | E-commerce equity caps are negative-list entries | Official gazette or legislation database in most jurisdictions. Our crawler collects it only under core or seed acts |
| 12.2 | Online purchases and delivery limitations | C | Dg | Purchase and delivery limits are sector regulations and product lists | Official gazette or legislation database in most jurisdictions. Our crawler collects it only under core or seed acts |
| 12.3 | Licensing scheme for e-commerce providers (B2B and B2C) | B | L, Dg | The licensing scheme is in the e-commerce law; scope and conditions are in regulations | Statute, with delegated detail as coded |
| 12.4.1 | Online payment limitations: mandate local bank account | C | Dr, Dg | Local-account mandates are central-bank rules | Regulator instrument. In the official database where such instruments are legal normative documents; on the regulator's site in common-law systems |
| 12.4.2 | Online payment limitations: mandate currency used for international payments | C | Dr, Dg | Currency mandates for international payments are central-bank or exchange-control rules | Regulator instrument. In the official database where such instruments are legal normative documents; on the regulator's site in common-law systems |
| 12.4.3 | Online payment limitations: deviate national standards | C | Dr, T | Deviation from national payment standards: central-bank rules referencing technical standards | Regulator instrument. In the official database where such instruments are legal normative documents; on the regulator's site in common-law systems |
| 12.4.4 | Online payment limitations: licensing requirements | C | Dr, Dg | Payment-service licensing is central-bank rules | Regulator instrument. In the official database where such instruments are legal normative documents; on the regulator's site in common-law systems |
| 12.4.5 | Online payment limitations: ceiling on the maximum amount | C | Dr, Dg | Payment ceilings are central-bank circulars | Regulator instrument. In the official database where such instruments are legal normative documents; on the regulator's site in common-law systems |
| 12.4.6 | Online payment limitations: mandate specific intermediaries | C | Dr, Dg | Mandated intermediaries are set by central-bank notice | Regulator instrument. In the official database where such instruments are legal normative documents; on the regulator's site in common-law systems |
| 12.4.7 | Online payment limitations: others restrictions | C | Dr, Dg | Other payment restrictions are central-bank rules and circulars | Regulator instrument. In the official database where such instruments are legal normative documents; on the regulator's site in common-law systems |
| 12.5 | Low De Minimis | C | Dg | De minimis values are customs regulations or tariff-commission notices, gazetted | Official gazette or legislation database in most jurisdictions. Our crawler collects it only under core or seed acts |
| 12.6 | Imposition of custom duties on electronic transmission | C | W | Duties on electronic transmissions are a trade-policy stance tied to the WTO moratorium; a duty would appear in the tariff schedule, and none does | Outside any law database, in every economy |
| 12.7 | Domain name requirements | C | Dr | Domain-name requirements are registry or ministry rules | Regulator instrument. In the official database where such instruments are legal normative documents; on the regulator's site in common-law systems |
| 12.8 | Local presence requirements for online service providers | B | Dg | Local-presence duties on online providers are sector licensing or e-commerce regulations | Official gazette or legislation database in most jurisdictions. Our crawler collects it only under core or seed acts |
| 12.9 | Lack of legal framework for online consumer protection | B | L | Existence of an online consumer-protection framework. Primary law | Statute |

## X. Excluded: non-regulatory

No row is written for these. The host fills them from external databases and treaty status.

| IDs | Source the host uses |
| :---- | :---- |
| 1.1, 1.2 | WITS database |
| 9.2 | V-Dem database |
| 1.3, 2.4, 4.4, 4.7, 4.8, 5.6, 6.5, 12.10, 12.11, 12.12, 12.13 | Treaty and agreement status |

## Per-economy notes, hand-edited

What is known about each economy's portal and the tier it publishes. Add a block when an economy is
built or surveyed. Every claim names its evidence.

### China, the special case

Evidence: `explore-2026-09-20\cn-china-coverage.md` in the survey folder, desk research, nothing fetched
from the database.

- **Why it is special.** Two things coincide that do not elsewhere: the central database omits the whole
  departmental tier, and it forbids automated collection. The delegation pattern is general; the missing
  tier is China's.
- **Portal tier.** The National Database of Laws and Regulations carries the constitution, laws, administrative
  regulations, supervisory regulations, judicial interpretations and local regulations. It does not carry
  departmental rules, normative documents, national standards, or catalogues, announcements and negative lists.
- **Pillar 7 is fully covered**, 5 of 5. Pillar 4 is covered if judicial interpretations count. Pillar 12 is 6 of 15.
  Pillars 1, 2, 3, 5, 6, 9, 10 and 11 are framework-only: the number sits in a tier the database does not carry.
- **Pillar 6 is framework-only for China.** Even the automated pillar needs the manual mark here.
- **Nine indicators no tier reaches:** 5.3, 4.9, 11.4, 12.4.5, 12.4.6, 12.5, 10.3, 12.7, 9.1. Three are F or T
  by nature and would be outside anywhere; the other six are Dg or Dr and are China's database gap.
- **Covered can still be wrong.** Telecom foreign equity reads 49 or 50 percent from the database; a MIIT notice
  of October 2024 lifted the cap in four zones.
- **Automated collection is forbidden** by the database's robots.txt. Any Chinese set is hand-collected, or
  crawled from ministry sites that permit it. Open decision (d) in the issue record.

- **Why, and where the tier actually is.** The gap is a split of channels, not of publicity. Under the 立法法
  departmental rules are filed with the State Council and published in the 国务院公报 and on the Ministry of
  Justice site, so they sit in the executive's databases: the 公报 and 政策文件库 on gov.cn, which permits
  crawling, and the 国家规章库 on moj.gov.cn. The host's own Round 2 China rows cite gov.cn three times as often
  as the NPC database. Analysis and hand-backs: `ISSUES\2026-09-20_china-legal-structure.md`.

### Timor-Leste

Evidence: `countries\tl-timor-leste\NOTES.md` and `sources.yaml` in the scraping workshop; the crawl of 2026-09-20.

- **Portal tier.** The Jornal da República publishes the whole statute book as gazette issues, including the
  ministerial tier. Six categories were collected: laws, decree-laws, government decrees, presidential decrees,
  parliamentary resolutions, government resolutions. The Diploma Ministerial category was not read, though
  some diplomas arrive inside collected issues. A collection gap on our side, not a portal gap. Open decision (c).
- **No data-protection statute at all**, per the workshop's notes. For 7.1 that is the answer, not a gap.
  A commitment on data or telecoms may arrive only as a treaty ratification, which is why parliamentary
  resolutions are collected.

### Malaysia, Singapore, Australia, common-law systems

Evidence: scraping decisions 12, 17 and 18, and each country's `sources.yaml`.

- **The portals publish subsidiary legislation.** Laws of Malaysia lists P.U. (A) and P.U. (B) instruments
  under each act; Singapore Statutes Online has a subsidiary-legislation tab per act; the Federal Register of
  Legislation holds every legislative instrument. The Dg tier is on the portal.
- **What we collect is narrower.** Malaysia fetches P.U. (A) under core pillar 6 and 7 acts; Singapore the
  subsidiary tab of seed acts, at most 100 per act by default; Australia the in-force Act collection plus
  seeded instruments. A pillar 6 or 7 threshold under a non-core, non-seed act is not collected.
- **Regulator instruments are off the portal.** Bank Negara policy documents, MAS notices, MCMC and IMDA
  instruments and ACMA determinations live on the regulator's site. For the Dr indicators, including 6.2 and
  6.3 in the automated pillars, the researcher checks the regulator, not the legislation portal.

### The three new economies

Not yet chosen (host question 1). Add a block for each when its portal is surveyed, before its first crawl,
stating which of Dg and Dr the official source publishes.

## How to extend this register

1. When an economy is surveyed, add its per-economy block: which tiers the official source publishes, which
   we collect, which we count, which we skip, and the evidence.
2. When a tier is found missing for an automated indicator, add the economy override to the instrument's
   machine-readable marks and note it here.
3. Regenerate the tables from the instrument files whenever `indicator_order.yaml` or a tier changes. The
   nature codes live in the generator and change only with a reason written into this file.
4. Before 30 September, copy the per-economy readiness into Word Section 4 and the summary into the README's
   Known Limitations.

