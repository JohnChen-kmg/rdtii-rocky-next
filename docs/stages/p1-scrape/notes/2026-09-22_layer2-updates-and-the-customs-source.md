# Updating what we cannot crawl, and the customs source — 2026-09-22

Two decisions by the developer on 2026-09-22, both universal, both now in `CONVENTIONS.md` as **rules 13 and 14**.
This note records what they are, why, what was built, and the addresses the research found.

## Decision 1 — a source that refuses us is updated by a person, and the tool prepares that walk

> *"For layer two websites, the update can be a little bit hard and troublesome. We will need manual checking for
> these websites. When we do the manual checking, we need to provide the URL to that specific page."*

**The problem.** An update check works by re-reading an index and diffing it. Where the host refuses an honest
client — MIIT answers 403, China Customs 412 — there is no index to re-read. **Nothing automatic will ever report
that one of those rules was amended or repealed**, and no amount of tooling changes it. China holds 23 such
documents today. Left unmarked, they would go stale silently while the corpus looked complete.

**What was built** (China; the same shape applies to any economy that acquires such a source):

| | |
| :---- | :---- |
| `update_check` column in every hand-collected `provenance.tsv` | says how each document must be re-checked, and why no tool can do it |
| `countries/cn-china/tools/manual_check.py` | writes `MANUAL_UPDATE_CHECK.md` into the collection: the index pages to open, then **the exact address of every document held** with the version date we hold, so the walk is a comparison and not a search |
| The three questions, per source | anything **new** on the index · anything with a **later version date** · anything marked **废止 / 失效** |
| `tools/update.py` | now ends by counting the documents it did **not** cover and rebuilding that worklist |

A held document with **no address** is reported as a defect, because it cannot be checked at all — that is the
whole cost of an empty `url` cell, and it is now visible.

## Decision 2 — the customs and tariff source stays manual in every economy

> *"For the customs list, because it's universal for every country, let's keep that manual. Let's not automate the
> customs list for each country. When we do that indicator, we can just provide the link, and the researcher can
> check that manually."*

**Why this is the right call, and not a shortcut.** The customs cluster answers **1.4, 12.2, 12.5 and 12.6**. The
research below establishes that these four indicators would cost six different parsers, and that several of the
figures are not in any parseable document at all:

- **Malaysia's tariff is search-only.** JKDM's HS Explorer has no downloadable consolidated schedule, and its
  result URLs carry expiring tokens — nothing stable to point a tool at.
- **Timor-Leste has no standing tariff instrument.** Rates are re-enacted **annually in the State Budget law**, so
  the current rate is not on the customs site at all.
- **Lao PDR's tariff host refuses HTML** to an automated client (403) while serving its PDFs (200), and the
  customs department's own site **forbids every agent every path** in robots.txt.
- **Singapore's line-item rates live only inside a PDF** linked from the page.
- **China's figures are in announcements**, not legislation: the annual 关税调整方案 and the 行邮税 公告.

A schedule parsed wrongly is worse than one read by a person. So the crawler stops here **by design** — the one
place in this workshop where "a researcher will look" is the intended answer rather than a fallback. What makes it
auditable rather than vague: the watch list carries **the exact page**, and the researcher records **the figure,
the page and the date read**.

**And the decision costs less than it looks, because in some economies the tariff is already in the corpus.**
Where the rates are enacted as legislation, the main database carries them and no manual step is needed for 1.4 or
12.6 at all:

| Economy | Where the applied rates legally sit | Already in our corpus? |
| :---- | :---- | :---- |
| **Australia** | Schedule 3 of the **Customs Tariff Act 1995** — an Act | **Yes**, `au-cta1995-001` in `AU_corpus_2026-09-15`, fetched 2026-09-15 |
| **Malaysia** | **P.U.(A) orders** under the Customs Act 1967 (PDK 2025) — subsidiary legislation on `lom.agc.gov.my` | **Partly**: the parent Customs Act 1967 (Act 235) is in `MY_corpus_2026-09-15`; the P.U.(A) duty orders are not, because subsidiary legislation is taken only under the core pillar 6 and 7 acts (decision 12) |
| **Lao PDR** | the **Trade Portal's** nomenclature, changed under Article 178 of the Customs Law | No |
| **Timor-Leste** | re-enacted **annually in the State Budget law** | No |
| **Singapore** | a **PDF schedule** linked from the customs site | No |
| **China** | an annual **announcement** of the Tariff Commission | No |

So what the manual customs source is really for is **the part no legal corpus can hold**: the de minimis
thresholds, which are administrative figures, and the cross-border e-commerce notices. That is a smaller and more
honest claim than "the tariff is manual", and it is what rule 14 is scoped to.

## The addresses, verified 2026-09-22

Every row below was opened on 2026-09-22 unless marked otherwise, robots.txt was read for each host, and no
refusal was retried. They are now rows in each economy's `updates/watchlist.tsv` (China's is
`countries/cn-china/watchlist.tsv`), with `address_verified` set — a new column, distinct from `last_checked`,
which remains the date the source was checked for *changes*.

| Economy | Tariff | De minimis | robots |
| :---- | :---- | :---- | :---- |
| **Malaysia** | `ezhs.customs.gov.my` — **PDK 2025**, plus ~19 preferential schedules. Search-only | **MYR 500 CIF, air courier only** — Item 94, Customs Duties (Exemption) Order 2017 (`mylvg.customs.gov.my/FAQ`) | permits; only Joomla system paths disallowed |
| **Singapore** | `customs.gov.sg` list of dutiable goods — four categories only; HS rates in the linked PDF | **S$400 CIF, air or post**, liquor and tobacco excluded | permits; `/search` disallowed |
| **Timor-Leste** | `customs.gov.tl` duties and taxes — **import duty 5%** since the 2023 State Budget | **$10 of duty**, not of value — roughly $200 CIF at 5% | permits; stock WordPress |
| **Lao PDR** | `laotradeportal.gov.la` search commodity — AHTN 2022. **The Trade Portal, not the customs site** | **1,500,000 LAK**, Article 94 of the 2020 Customs Law, duties only | **`customs.gov.la` forbids everything**; the Trade Portal has no `*` group |
| **China** | `gss.mof.gov.cn` — the annual 关税调整方案 | the ¥50 行邮税 threshold, in a Tariff Commission 公告 | Customs refuses an honest client (412) |
| **Australia** | `abf.gov.au` current Working Tariff — Schedule 3. **The rates are law and we already hold the Act** (C2004A04997, in `AU_corpus_2026-09-15`) | **AUD 1,000 per consignment**; GST at point of sale since 2018-07-01 | permits everything but `/sitesearch?` — **yet ABF 403s an honest client**, a User-Agent block, not a prohibition |

## Traps the research found — each one would have cost a researcher an afternoon

1. **Singapore did not abolish its de minimis in 2023.** The S$400 border relief is intact. What changed on
   2023-01-01 is that GST is collected **at the point of sale** by registered overseas sellers. A great deal of
   secondary commentary says the threshold was removed; it is wrong in exactly the way that matters here.
2. **Timor-Leste's import duty is 5%, not 2.5%** — 2.5% is the *sales tax*. Worse, the customs site contradicts
   itself: its **Tariff Finder still shows 2.50% on every HS line, with no date stamp**, while its duties page and
   the 2023 booklet say 5%. A researcher who lands on the Tariff Finder first gets a stale rate and no warning.
3. **Malaysia's tariff text is not on the customs site.** Its orders hub stops at the 2017 base order and defers to
   `lom.agc.gov.my` — **which this workshop already crawls.** Check the MY corpus before recording a gap.
4. **Lao PDR's figure is only in the law.** Commercial de minimis trackers list Lao PDR as none or zero; Article 94
   of the 2020 Customs Law says 1,500,000 LAK. Quote the kip figure and the article, never a USD conversion: the
   kip has depreciated far since 2020, so a USD number silently depends on its vintage.
5. **A converter saying "no text" can be wrong.** The Lao customs law PDF was reported as unreadable image data by
   one extractor and yielded 171,078 characters to PyMuPDF. Compare with `checkdocs.py`, which looks for fonts and
   text operators, before writing a document off. (The opposite error — a file that *looks* fine and holds no
   text — is rule 12, and cost 23 MIIT documents a second pass the same day.)
6. **Australia's customs-notice list hides everything recent from a static fetch.** The served HTML carries an
   archive table of 1,480 rows covering **1996–2017 only**; notices from 2018 on are rendered client-side. A
   scraper reading that page would report the list as complete and miss eight years. Current notice PDFs are at a
   predictable path (`/help-and-support-subsite/CustomsNotices/YYYY-NN.pdf`).
7. **A 403 is not always a prohibition.** ABF's robots.txt permits every path used here and the site still answers
   403 to an honest client, because it filters on User-Agent. Under the developer's standing rule the verdict is
   the same either way — we do not defeat a 403 — but the *reason* matters when reading a robots survey: the
   refusal is the host's client filter, not its stated policy. The mirror case is Lao PDR's Trade Portal, where
   robots has no `*` group at all: silence, which is not permission.
8. **Malaysia's old `.aspx` addresses still rank first in search and all 404.** The department moved to Joomla, its
   English pages are a JavaScript shell with no menu in the HTML, and its declared sitemap contains two URLs.

## What is still open

- **Lao PDR has no express-consignment de minimis.** Article 52 of the Customs Law subjects online and postal
  goods to control with no threshold and delegates the rules to a Ministry of Finance regulation **that was not
  located**. That regulation is the real gap for 12.2 and 12.5 in Lao PDR.
- **Timor-Leste's current rate lives in the annual State Budget law**, which is not published on the customs site.
  Whoever scores 1.4 or 12.6 for Timor-Leste has to find the 2026 budget law first.
- **Timor-Leste joined ASEAN in 2025**, so ATIGA preferential rates may begin diverging from the flat 5%.
- Whether any of these figures should be stored as evidence files rather than read live at scoring time. Today
  they are read live, which is why the date read must be recorded with the figure.

## Where this is written down

`CONVENTIONS.md` rules 13 and 14 · each economy's `updates/watchlist.tsv` (and `countries/cn-china/watchlist.tsv`)
· `countries/cn-china/SOURCES.md`, sections on whole-section-versus-selection, the expansion problem, and layer 2's
manual update · `countries/cn-china/tools/manual_check.py` and its ten tests.
