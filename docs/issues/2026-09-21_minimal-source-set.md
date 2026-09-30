# How many websites the crawler actually needs: the main law database plus a named few

| | |
| :---- | :---- |
| Recorded | 2026-09-21 |
| Status | Open. Decisions (f) to (k) below. Two of them are questions for the host, not for us |
| Replaces | `2026-09-21_source-dispersion.md`, whose citation counting overstated the problem. Kept with a correction banner |
| Evidence | The host's own coded rows for ten economies, in `rdtii-finale-0-instrument\instrument\output\gold\gold_set.jsonl`. The 13 indicators the host fills from third-party databases are excluded throughout, so every row here is one the tool would have to answer |
| Method | Twenty-one agents: one analyst and one adversarial challenger per economy, then a synthesis that resolved each disagreement. Row-by-row resolution of the operative publisher from the instrument name, not from the pasted link. 227 pillar 6 and 7 rows, 1,054 rows in total |

## The answer

The developer's reading holds. **The tool needs one main law database per economy plus a named set of
separate sources.** It does not need the dozens of domains a raw citation count suggests, and the
distinction that collapses the count is the one the developer drew: an operative source publishes the
instrument, everything else is supplementary.

**For pillars 6 and 7, the two mandatory pillars and the only ones the tool automates, the median
economy needs two websites in total.**

| Economy | Sites needed for pillars 6 and 7 | Which |
| :---- | ----: | :---- |
| Mongolia | 1 | `legalinfo.mn` alone |
| Russian Federation | 1 | `pravo.gov.ru` alone |
| Lao PDR | 2 | Trade Portal, Official Gazette |
| Malaysia | 2 | Laws of Malaysia, the data-protection department |
| Indonesia | 2 | the audit board's database, the financial services authority |
| Australia | 2 | the Federal Register, the privacy commissioner |
| Singapore | 3 | Statutes Online, the privacy commission, the infocomm authority |
| China | 5 | the NPC database, `gov.cn`, the cyberspace administration, the central bank, the standards systems |
| Thailand | 8 | consolidated law, the Royal Gazette, and six regulators |
| India | 10 | India Code, the electronics ministry, and eight financial and telecom regulators |

Eight of ten need three sites or fewer. Two need only the main database.

**Across all twelve pillars** the totals rise, and this is where the developer's observation about
customs sites bites:

| Economy | Total sites | Economy | Total sites |
| :---- | ----: | :---- | ----: |
| Mongolia | 2 | Singapore | 8 |
| Russian Federation | 4 | Indonesia | 9 |
| Lao PDR | 5 | China | 11 |
| Malaysia | 7 | Thailand | 17 |
| Australia | 8 | India | 23 |

Median 8, range 2 to 23. **Roughly three fifths of that apparatus exists to serve pillars the tool does
not automate**: trade in ICT goods, procurement, intellectual property, content, goods controls,
technical standards and online sales. Only 36 of the 94 sites across all ten minimal sets are touched by
pillars 6 and 7 at all.

So China needs more than most, at eleven, but India at twenty-three and Thailand at seventeen are the
outliers, not China.

## What the earlier count got wrong

An earlier file reported that India needed 66 websites, Thailand 50 and Malaysia 41. That was wrong in
the three ways the developer identified.

**A cited link is usually not a source to extract from.** Rows cite 1.4 to 2.2 URLs each, and one of
them publishes the instrument. The rest corroborate.

**Many cited hosts are not official publishers.** Malaysia's rows reach the Personal Data Protection Act
through a University of Malaya human-resources page, a law firm's file server, an NGO rights tracker and
a pharmaceutical company's website. Russia's reach federal statutes through three commercial systems.

**The instrument decides the source, not the link.** Resolving on instrument identity is what moved the
numbers most, and the clearest case is the intellectual-property office. Malaysia's IP office is the
second most cited host in the country, with fourteen citations and seven first-position links, and it is
the operative publisher for **zero** rows, because every pillar 4 row names an Act. Russia's patent
office is the third most cited government host and is likewise operative for none.

## Three economies need a different main database

| Economy | We target | Should be | Why |
| :---- | :---- | :---- | :---- |
| Lao PDR | the Official Gazette | **`laotradeportal.gov.la`**, the National Trade Repository | 71 citations against the Gazette's 21. WTO accession and the ASEAN trade-in-goods agreement oblige Lao PDR to publish tariff, licensing and standards material there. The Gazette stays as the second source, because a law takes force 15 days after gazetting and it is the only site carrying the Penal Code and the Consumer Protection Law |
| Thailand | `krisdika.go.th` | **`searchlaw.ocs.go.th`**, the Council of State's consolidated database | The Council of State renamed its domain. The Royal Gazette is the second most important Thai source, not a fallback, because consolidation stops at the Royal Decree tier and the whole Ministerial Regulation layer exists only in the Gazette |
| Indonesia | `peraturan.go.id` | **`peraturan.bpk.go.id`**, the audit board's database | 70 per cent of Indonesian citations, and it alone answers 29 of 35 pillar 6 and 7 rows. It is also the host that answered our survey with a Cloudflare block, so this is a technical problem, not a legal one |

Two further corrections to how we address a source we already have right.

**Russia.** The crawler must target the consolidated legislation bank on `pravo.gov.ru`, **not**
`publication.pravo.gov.ru`. The promulgation subdomain begins in 2011, and the statutes that carry the
Russian rows are older: the mass-media law of 1991, consumer protection 1992, foreign investment 1999,
communications 2003, information and personal data 2006, the national payment system of June 2011. A
crawler pointed at the promulgation subdomain cannot reach any of them.

**Malaysia.** The Laws of Malaysia portal **is** the electronic Federal Gazette and serves subsidiary
legislation from 26 April 2011 onward. Two consequences. A separate customs source is not needed,
because the orders in question are post-2011 subsidiary instruments the portal already serves. And
`federalgazette.agc.gov.my`, which our registry lists, does not resolve at all. The real boundary in
Malaysia is temporal rather than institutional, which is why the trade ministry is needed for pre-2011
material such as the anti-dumping regulations of 1994.

**China** is best recorded as a **two-backbone economy** rather than one main database with satellites.
The NPC database and `gov.cn` are co-equal: the State Council site is the operative publisher for about
28 rows on its own account, under the rule that an administrative rule is published in either the State
Council gazette or the department's own gazette.

## Our registries are already the right shape for the automated pillars

The scraping workshop's registries are multi-host and were built for pillars 6 and 7. Measured against
the host's rows, resolving Acts to the legislation portal, they already cover every pillar 6 and 7 row
for all four built economies. Malaysia's registry already names the communications regulator, the
data-protection department, the central bank, the companies commission and the legislation portal. That
is the pattern this analysis recommends, built before the analysis and correct.

**No adapter needs rewriting.** The work this file implies is a registry widening for pillars we have
already decided not to automate, plus the three retargets above.

## The recurring categories, and what the customs hypothesis actually is

The developer's customs observation is right as a tendency, in 7 of 10 economies, but the reason is
sharper than "customs is a different site". What a consolidated database never carries is the **annex,
schedule and notification layer**: the tariff schedule itself, the goods lists coded by tariff heading,
the anti-dumping notifications, the annually reissued catalogues. The database publishes the enabling
Act and stops.

Three economies need no separate customs source at all, each for a nameable reason. Singapore gazettes
its control lists as subsidiary legislation into Statutes Online. Mongolia puts even the prohibited-goods
list on `legalinfo.mn`. Lao PDR's Trade Portal is the National Trade Repository, so tariff and licensing
material is legally required to be there. Two refinements worth carrying: in India, Thailand and China
the customs role **splits across two bodies**, import policy and duty imposition, and in Indonesia it is
the finance and trade ministries rather than the customs agency. A registry keyed on "the customs agency"
will miss it.

| Category | Economies | Indicators it answers | In pillars 6 and 7? |
| :---- | ----: | :---- | :---- |
| Financial-sector regulator | 8 | 12.4.1 to 12.4.7, 6.2, 6.4, 7.1, 7.3 | Yes, in 5 |
| Telecommunications regulator | 8 | 5.x, 8.3, 8.4, 9.x, 11.2, 11.3 | Yes, in 3 |
| Customs, tariff and trade remedies | 7 | 1.4, 10.1, 10.2, 10.4, 12.5, 12.6 | **No** |
| Procurement rulebook | 6 | 2.1, 2.2, 2.3 | **No** |
| Data-protection or cyber authority | 6 | 6.4, 7.1 to 7.5 | Yes, in 6 |
| Standards body | 5 | 11.1 to 11.4, 2.2 | Barely |
| Country-code domain registry | 4 | 12.7 | **No** |
| Gazette held apart from the code | 3 | 2.3, 7.1, 10.1, 10.2, commencement dates | Partly |
| Intellectual-property office | 3 | 4.x | **No** |
| Courts | 3 | 4.1, 4.5, 8.1 | **No** |

Only three categories survive into the mandatory pillars: the data-protection or cybersecurity authority,
the financial regulator where an indicator is scored sector by sector, and the telecom regulator where
retention duties sit in licence conditions.

## The single highest-leverage question, and it is for the host

**Indicator 7.3, record retention, is what makes India and Thailand expensive.** The host coded it sector
by sector. In India it alone pulls in the international financial services authority, the securities
board, the insurance regulator, the company affairs ministry, the computer emergency team and part of the
central bank and telecom department. In Thailand it pulls in the central bank, the digital economy
ministry, the telecom regulator and the credit information committee.

If the host confirms 7.3 is scored on the horizontal rule rather than on every sectoral regulator's
instrument, **India's pillar 6 and 7 burden falls from 10 sites to about 3, and Thailand's from 8 to
about 4.** That one answer is worth more to the freeze than anything else on the open list. Added to the
host email as question 4.

## A warning about how we validate

**URL matching cannot validate the crawler.** The main law database is cited 0 times in Malaysia out of
172 citations, twice in Russia out of 147, 12 times in Thailand out of 250 and 14 times in India out of
254. Any discovery comparison that matches our crawled URLs against the host's cited URLs will score near
zero for the main database in those four economies and will be measuring the wrong thing. **Match on
instrument name and section.** This is a direct instruction to whoever builds the Discovery Tag
comparison.

One failure mode is worse than a gap. Indonesia's row on copyright limitations names a Constitutional
Court decision as a co-equal instrument alongside the statute, and a constitutional ruling displaces
statutory text. A crawler reading only the statute returns a confidently **wrong** answer rather than a
missing one.

## What a per-economy source registry must contain

Eight parts, from the synthesis. The load-bearing one is B's boundary field.

- **A, the main database.** Host, aliases and dead or renamed hosts, issuing body, which tiers it carries,
  and explicitly **which it does not**, recording the boundary type: institutional as in China,
  tiered as in Thailand, or temporal as in Malaysia. Then text state, consolidated against as-enacted,
  which is what Russia turns on. Then URL grammars, retrieval mechanics and script.
- **B, necessary sources**, keyed by **hostname, never by body**. Merging two registrable domains deletes
  a crawl target from a deliverable that is a list of websites. Each carries a category from a fixed list
  and a mandatory prose field giving the legal reason it is not on the main database.
- **C, a supplementary denylist**, with reasons. Without it a naive crawler follows commercial databases,
  a university human-resources page, NGO re-publications and telecom operators' corporate sites. Include
  the per-economy "looks like a source and is not" list: the Malaysian and Russian IP offices, Singapore's
  customs.
- **D, an instrument-name resolution table**, because URL matching fails. Instrument name and section to
  publisher, with title traps: two Chinese instruments whose titles read like departmental rules are in
  fact State Council regulations, so classify on the instrument number, not the title.
- **E, the coverage ceiling**: rows with no extractable legal source, by class.
- **F, shared cross-economy sources** provisioned once, such as the ASEAN mutual-recognition texts, so
  four economies do not each count them.
- **G, open verification items**, each with the change in set size it would resolve.
- **H, freshness and version pinning**, for quarterly and annual reissues and superseded instruments the
  host's 2025 coding still names.

## Decisions

| | Decision | Owner |
| :---- | :---- | :---- |
| **(f)** | Whether any registry is widened beyond pillars 6 and 7 before the freeze. On this evidence the honest default is **no**: the automated pillars are covered and the rest are already marked for manual check | Developer |
| **(g)** | Whether a commercial reproduction of an official text is admissible, and whether a government aggregator outranks the nominal senior publisher | Instrument owner |
| **(i)** | The three retargets: Lao PDR to the Trade Portal, Thailand to the Council of State's current domain, Indonesia to the audit board's database. Thailand and Lao PDR also change which sources pillars 6 and 7 need | Developer, with the scraping workshop |
| **(j)** | **Ask the host** whether indicator 7.3 is scored horizontally or sector by sector. Worth 7 sites in India and 4 in Thailand | Host |
| **(k)** | **Ask the host** whether a non-legislative text is admissible as an operative source: an executive programme page, a self-regulatory code, a regulator's advisory guide, a paywalled standard. Four of Singapore's eight sources stand or fall on it | Host |

## Hand-backs

| To | What | Constraint |
| :---- | :---- | :---- |
| Scraping workshop | The three retargets, the dead Malaysian gazette host, the Russian subdomain correction, and that the existing registries already cover pillars 6 and 7 | **Record only.** No registry or adapter change follows from this file. Decision (f) and (i) are the developer's |
| Mapping workshop | Match the Discovery Tag on instrument name and section, never on URL. The main database is cited almost never in four economies | Blocking for the comparison export |
| Instrument workshop | Decisions (g) and (k), and that the register's regulator-sourced classification is confirmed | |
| Deliverables | Per-economy source counts belong in Section 2 of the Word document as evidence the architecture is economy-agnostic | |

## What would weaken this

**Nothing was retrieved for seven of the ten economies.** Assignments are inferred from each row's
instrument name read against national publication law. Only Australia, Malaysia, Mongolia and parts of
Thailand carry live checks, and those produced the most useful findings: the Malaysian subsidiary-
legislation discovery, the dead gazette domain, the Thai single-page-app behaviour.

**Coverage percentages are softer than they look.** Each row is assigned one operative publisher so the
counts sum cleanly, but around twenty Chinese rows and a comparable share elsewhere name two or more
instruments straddling publishers. Read every figure as "rows with at least one operative source
reachable", not "rows fully answerable". China's stated 98 per cent is closer to 95 on a consistent rule.

**Four added hosts have zero citations behind them**: the Chinese industry ministry, India's computer
emergency team and information ministry, and Indonesia's industry ministry. Each follows from a named
instrument with no publisher in the smaller set, which is the stated rule, but each is an inference. They
are also the cheapest things to confirm by hand before the freeze.

**Thailand's set of seventeen rests on achieved coverage, not on a tier rule.** The challenger showed the
premise that Thai consolidation stops at the Royal Decree tier is not a correct statement of current law,
because `law.go.th` is a statutory central system agencies must populate. That host is cited zero times in
250. One check could collapse Thailand from seventeen to single figures.

**Lao PDR's coverage was overstated by its analyst** at 98.9 per cent. The honest figure is 76.7 per cent
on cited links and about 92 per cent on defensible instrument-level reachability. All seven Lao
intellectual-property rows cite only international databases, with no Lao official publisher anywhere.

**The host's own citation layer has defects.** Four Malaysian rows name the Copyright Act and cite the
Patents Act. An Australian row names an instrument that does not exist. An Indian citation points at
Ghana's research council. Several Indonesian links carry a parameter suggesting part of the citation layer
was assembled by a language model and never verified. These will trip the tool and are worth raising with
the host.

**Source completeness and retrievability are different problems.** Thailand's consolidated database is a
single-page app serving the same shell for every document. Its cyber agency's five operative rows sit
behind unguessable share links. China's database serves pages behind JavaScript and gates standards behind
a viewer. Malaysia's act viewer refused automated fetches, which is very likely why the host's researchers
used twenty mirrors. Track them in separate columns.

**Script handling may matter more than source count in two economies.** At least fourteen operative Lao
documents are Lao script, and Mongolian uses Cyrillic with raw non-ASCII in URL paths.
