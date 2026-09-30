# No economy's law lives on one website, and for seven of ten the portal we chose is not where the host's evidence lives

| | |
| :---- | :---- |
| Recorded | 2026-09-21, after the developer observed that no single website can hold all of China's relevant law |
| Status | **Superseded the same day by `2026-09-21_minimal-source-set.md`**, which resolves rows to the instrument rather than the pasted link and gives the real per-economy source counts. Kept for the record. Decisions (f) and (g) moved to that file; (h) is withdrawn, because the premise that our registries target a single portal was wrong |
| Evidence | The host's own coded rows, 1,054 of them with URLs, in `rdtii-finale-0-instrument\instrument\output\gold\gold_set.jsonl`, built from the Round 1 and Round 2 RDTII databases |
| Supersedes | The framing in `2026-09-20_china-legal-structure.md`, which treated the multi-site problem as Chinese |

## The observation, and how far it generalises
> **Corrected the same day, after the developer's second reading.** The counts below are citation counts
> over every URL in a coded row, and that overstates the problem in three ways the developer identified.
> First, a row cites 1.4 to 2.2 URLs on average, and only one of them is usually the **operative** source,
> the publisher of the instrument the row relies on; the rest are supplementary, an explainer page, a press
> release, a secondary index, a law-firm note. Second, some cited hosts are not official at all, such as
> `commonlii.org` for Malaysia or `flevin.com` for Indonesia, so their presence says nothing about what a
> crawler must reach. Third, the long tail is almost entirely supplementary, so counting distinct domains
> measures the tail rather than the requirement.
>
> The honest question is the developer's: **excluding the indicators filled from third-party databases by
> design, the tool needs the main law database plus a small number of genuinely necessary separate sources**,
> such as a customs or tariff site, a central bank, a telecom regulator or a standards body. A greedy count
> of how few hosts cover 80 per cent of rows gives 1 for Australia, Mongolia and Singapore, 2 for Indonesia
> and the Russian Federation, 4 for Lao PDR, 5 for China, then 10 for Thailand, 12 for Malaysia and 17 for
> India. That is the shape of the real answer, and it is much closer to the developer's reading than to the
> table below.
>
> **What survives the correction** is the portal-choice finding in the next section: four of the portals our
> adapters target are cited zero times by the host, and that is not a tail effect. The per-economy minimal
> source sets are being rebuilt properly and will replace this section.


The developer's point was about China: no one site carries all the law the tool needs. That is correct,
and counting the host's own citations shows it is true of **every** economy, and that China is not
even the hard case.

**Citations by official host, per economy.** "Hosts" counts distinct domains. "h50" and "h80" are how
many domains are needed to reach half and four fifths of the citations. Secondary sources such as the
WTO are excluded here; commercial databases are counted separately.

| Economy | Coded rows | Official hosts | Top host's share | h50 | h80 |
| :---- | ----: | ----: | ----: | ----: | ----: |
| India | 146 | 66 | 16% | 8 | 27 |
| Thailand | 115 | 50 | 15% | 7 | 18 |
| Malaysia | 98 | 41 | 16% | 6 | 17 |
| Indonesia | 171 | 36 | 71% | 1 | 5 |
| China | 111 | 34 | 41% | 2 | 9 |
| Australia | 70 | 26 | 69% | 1 | 5 |
| Lao PDR | 90 | 23 | 51% | 1 | 6 |
| Singapore | 81 | 21 | 60% | 1 | 4 |
| Russian Federation | 97 | 16 | 23% | 4 | 11 |
| Mongolia | 75 | 18 | 72% | 1 | 2 |

Read the table twice. The first reading is the developer's point, confirmed: the best case in the set,
Mongolia, still needed eighteen official domains, and Australia, which has the most complete single
legislation register in the region, needed twenty-six. **Nowhere is one site enough.**

The second reading is the surprise. **China is mid-pack.** India needed sixty-six domains and its
busiest one carries a sixth of the evidence; Thailand fifty; Malaysia forty-one. China's evidence is
more concentrated than any of those, because the State Council's site carries a great deal of it. The
thing that makes China hard is not dispersion. It is that the one consolidated database forbids
crawling, which is a different problem and is recorded in `2026-09-20_china-legal-structure.md`.

## The sharper finding: we built around the wrong portal in seven of ten

Each country folder in the scraping workshop, and each survey note, is built around one official
portal. Comparing that choice against the host's citations for the same economy:

| Economy | The portal we built around | Its share of the host's citations | Where the host actually went most | |
| :---- | :---- | ----: | :---- | :---- |
| Australia | `legislation.gov.au` | 69% | `legislation.gov.au` | match |
| Mongolia | `legalinfo.mn` | 71% | `legalinfo.mn` | match |
| Singapore | `sso.agc.gov.sg` | 59% | `sso.agc.gov.sg` | match |
| Lao PDR | `laoofficialgazette.gov.la` | 14% | `laotradeportal.gov.la` 48% | mismatch |
| China | `flk.npc.gov.cn` | 12% | `gov.cn` 39% | mismatch |
| India | `indiacode.nic.in` | 6% | `meity.gov.in` 15%, then `rbi.org.in` | mismatch |
| Malaysia | `lom.agc.gov.my` | **0%** | `mcmc.gov.my` 16%, then `myipo`, `pdp`, `bnm` | mismatch |
| Thailand | `krisdika.go.th` | **0%** | `mdes.go.th` 14%, then `ipthailand`, `ratchakitcha`, `bot.or.th` | mismatch |
| Indonesia | `peraturan.go.id` | **0%** | `peraturan.bpk.go.id` 70% | mismatch |
| Russian Federation | `pravo.gov.ru` | **0%** | `base.garant.ru` 59% | mismatch |

Percentages are of all citations for that economy, including secondary and commercial ones, so they
are a floor for the mismatch rather than a ceiling.

Four of our chosen portals are cited **not once** in the host's entire dataset for that economy.
Malaysia is the plainest case: we built the adapter on the Laws of Malaysia portal, and the host's
ninety-eight Malaysian rows cite the communications regulator, the intellectual-property office, the
data-protection commissioner and the central bank instead.

## Why, and why it was predictable

This is the same delegation pattern the coverage register already records, seen from the other end.
The register classifies seventeen of the sixty-one in-scope indicators as **Dr**, meaning the answer is
a regulator's or administrative body's instrument. A consolidated legislation portal publishes Acts
and, in common-law systems, subsidiary legislation. It does not publish a central bank's policy
document, a communications regulator's determination or a data-protection commissioner's guidance.
Those sit on the regulator's own site, and that is exactly where the host's coders went.

So the register's nature codes predicted this, and the portal-name test in
`..\COVERAGE_AND_MANUAL_CHECKS.md` answered only half the question. **Reading a portal's name tells
you how deep it goes. It tells you nothing about how wide it is.** A source can carry every tier of
legislation and still be missing most of the evidence, because much of the evidence was never
legislation.

Three particular cases deserve their own note.

- **Indonesia.** We surveyed `peraturan.go.id` and `jdih.setneg.go.id`. The host used
  `peraturan.bpk.go.id`, the audit board's database, for seventy percent of its Indonesian citations.
  That is the host answering the dispersal problem by picking the most complete aggregator rather than
  the most senior publisher. It is also the one host that answered our survey with a Cloudflare 403.
- **Thailand.** The Council of State's consolidated text, whose certificate fails for us, is cited
  once. The ministry, the IP office, the Royal Gazette and the central bank carry the evidence.
- **Lao PDR.** The trade portal carries nearly half the citations, three times the gazette's share.
  A trade portal is an unusual primary source, and it exists because Lao PDR built one for its WTO
  commitments.

## The Russian Federation: the host used commercial databases

Of 147 Russian citations, **116, or 79 percent, point at commercial legal information systems**:
`base.garant.ru` 86, `consultant.ru` 17, `docs.cntd.ru` 12, `garant.ru` 1. The official portal
`pravo.gov.ru` is cited zero times. No other economy shows this: the only other commercial citations
in the whole dataset are two to `lawinfochina.com` for China.

This matters for three reasons, and it is not a reason to copy the practice.

1. The Internal Guide's evidence rule says official sources and excludes secondary sources, listing
   reports, news and legal reviews. A commercial system reproducing an official text is arguably not a
   secondary source in that sense, but it is not the official publisher either, and the Guide's own
   example of where to look is the official gazette.
2. **It does not block us.** Our Discovery Tag compares instruments, not URLs, so a baseline row
   citing Garant and a crawled row citing `pravo.gov.ru` are the same provision if the instrument
   matches. The comparison is on law identity, and that needs confirming rather than assuming.
3. It suggests the host's Russian coder found the official portal hard to use, which is consistent
   with what our own survey found: `https` timed out and only `http` answered.

## What this changes

**It does not change the scope decision.** Pillars 6 and 7 stay automated, everything else stays
marked for manual check. This finding sharpens what "automated" has to reach, not how much is
automated.

**It does change what a source registry must contain.** A per-economy registry of one legislation
portal cannot reach the evidence for pillars whose answers are regulator instruments. For pillars 6
and 7 specifically, the register already codes 6.2, 6.3 as Dr, and the host's citations for those
rows bear it out: Singapore's twenty-two IMDA citations and nine from the data-protection commission,
Malaysia's twenty-seven from the communications regulator, India's twenty-two from the central bank.

**It strengthens question 3(b) to the host**, in `..\HOST_EMAIL_DRAFT_2026-09-20.md`, which asks
whether a curated registry of official sources per economy and pillar is acceptable. The answer now
has evidence behind it: the host's own researchers worked from a curated set of regulator sites, not
from one portal, so asking the tool to discover everything from a single legislation database would
hold it to a standard the baseline itself does not meet.

## Decisions for the developer

| | Decision | Why it cannot be settled here |
| :---- | :---- | :---- |
| **(f)** | Whether the source registry for each economy is extended from one legislation portal to a named set including the sector regulators, for pillars 6 and 7 at least | It is a scraping-scope and time decision before the freeze, and the scraping workshop owns the registry |
| **(g)** | Whether a commercial reproduction of an official text is admissible evidence, and separately whether an aggregator such as `peraturan.bpk.go.id` outranks the senior publisher | An instrument-owner ruling on the source hierarchy. Affects Russia now and any economy later |
| **(h)** | Whether the three matched economies are left alone and effort goes to the mismatched ones, or the registry question is deferred past the freeze and recorded as a known limitation | A scope call against eight remaining days |

## Hand-backs

| To | What | Note |
| :---- | :---- | :---- |
| Scraping workshop | The table above, as a finding against each country's `NOTES.md`. For Malaysia, Thailand, Indonesia and the Russian Federation, the portal the adapter targets carries none of the host's cited evidence | **Record only.** No code, adapter or registry change from this file. Decision (f) is the developer's |
| Instrument workshop | Decision (g), the source-hierarchy ruling, and a note that the Dr classification is now empirically confirmed by the host's citation pattern | |
| Deliverables | If (f) is deferred, this belongs in the README's Known Limitations and in Section 4 of the Word document, stated plainly | Honest gaps are marked up |

## Method, and what would weaken this

Counts are citations, not documents: one coded row may cite several URLs, and a busy row weights its
hosts more heavily. Host classification is by domain, so a ministry's subdomain counts separately
from the ministry. The "commercial" and "secondary" lists are hand-written and may miss a domain. The
host's database is the 2025 vintage and our crawls are 2026, so a portal that has since improved would
be judged on old evidence, which is a real risk for Indonesia's national hubs in particular. What the
finding does not depend on is any of that detail: four of our ten portals are cited zero times, and
that margin survives any reasonable reclassification.
