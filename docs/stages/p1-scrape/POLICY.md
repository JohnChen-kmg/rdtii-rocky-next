# Scraping policy

What the crawler fetches, from where, and how politely. The shape of what it hands on is in
`CONTRACT.md`. Draft, written 2026-09-13.

A rule here changes only through a dated entry in `DECISIONS.md`. A rule that is still an open
decision is marked **Open**, and section 7 lists them all.

The evidence for each rule is in `notes/` or in a country's `NOTES.md`.

## 1. Scope

**Economies.**
- The 30 September submission covers six economies: Singapore, Malaysia and Australia, plus three
  new ones, all non-English (decision 7).
- The live test on 15 October draws one economy on the day, from Thailand, Viet Nam, Indonesia,
  China, India, Kazakhstan, Lao PDR, Mongolia and the Russian Federation.
- Which three new economies is still open (host question 1).

**Indicators.**
- IDs are decimal text as the host writes them: `6.1`, `4.01`, `12.4.1`. Never numbers, never
  `P6-I1`. The list and its order come from the instrument's `indicator_order.yaml`.
- 61 indicators are in scope.
- The crawler never searches for the 14 non-regulatory indicators: 1.1, 1.2, 1.3, 2.4, 4.4, 4.7, 4.8,
  5.6, 6.5, 9.2 and 12.10 to 12.13. The host fills them from external databases.
- 3.4, 5.3 and 9.1 are practice-based. Their evidence may be announcements, reports or ownership
  records (section 3.9).

**Pillars. Open.** Decision 7 requires pillars 6 and 7 only. The instrument notice says every
pillar needs registries, and the live test can draw any of the twelve. See
`notes/INSTRUMENT_IMPACT_2026-09-13.md` items C1 and C2.

**What the crawler does not do.** It retrieves official text and records where and when it came
from. It does not translate, interpret, split provisions or map indicators.

## 2. Sources

Fetch from the highest source in this order that holds the text. The order follows the instrument's
`policies.yaml` `citation_url_preference`. That list's comment gives `lom.agc.gov.my` as an example of a
gazette scan. This table ranks Laws of Malaysia, which publishes the revised reprints, as the statutes
portal.

| # | Source | Example |
| ----: | :---- | :---- |
| 1 | The official statutes portal | Singapore Statutes Online, Laws of Malaysia, Federal Register of Legislation |
| 2 | The issuing agency or regulator | A data protection commission's codes, guidelines and standards |
| 3 | The official gazette | A national gazette site |
| 4 | An intergovernmental publisher, only for a document the economy itself submitted | A WTO trade-remedy notification, for 1.4. **Open**: request R4 asks the instrument for this class |
| 5 | A reputable secondary copy | Last resort only, when no official copy is reachable. Always flagged in the manifest |

Four rules go with the table.

1. **Finding aids are never a source.** I-TIP, Global Trade Alert, WTO Trade Policy Reviews, the
   Global Express Association database, DSTRI, UNCTAD Cyber Tracker and ITU DataHub point to a law.
   Resolve the pointer to the official text, or drop it.
2. **Search guides discovery. The official portal supplies the evidence**, never the reverse.
3. **Non-government company or ownership records** are allowed only as evidence for 3.4, 5.3 and 9.1.
4. **Host inventories supply law names, never URLs.** The Round 1 inventories carry finding-aid and
   law-firm URLs.

## 3. What to fetch for each law

**3.1 The principal law as in force.** Fetch the current consolidated text where the portal publishes
one. Choose the version by the date the portal or the document gives for it: an as-at date, a
compilation date, or a version-in-force date. Never choose by upload order or filename. In Round 1 the
Malaysia crawl kept the last `/EN/` file listed on each act's page (`my_gazette.py:176-178`), never the
printed date. The stored text of 23 acts predates amending acts held in the same corpus. Whether the
picker passed over a newer file is unknown, because no detail page was stored.

**3.2 Amendments are linked to the principal, never substituted for it.**
- Record every amending instrument the portal lists for a principal law, linked to that law.
- An amending instrument carries no indicator tags of its own.
- Why: an amending act cited instead of the principal act scores zero.

**3.3 A consolidation older than the latest amendment.** When the portal lists an amendment that took
effect after the stored text's as-at date, fetch that amending instrument and its commencement
instrument too, and flag the pair. Malaysia's PDPA is stored as of 2016, next to its separate 2024
amending act.

**3.4 Subsidiary legislation.** Fetch the instruments the portal lists under an in-scope principal
law, such as regulations, orders and notifications. Limit this to in-scope laws. Every current
instrument on a portal is thousands of requests.
- **Malaysia** (decision 12, confirmed by decision 17; set in `sources.yaml` and used by the 2026-09-14 crawl):
  - **Fetched:** P.U. (A) instruments on the read timelines of acts in the title rule's core groups that
    are not repealed or superseded.
  - **Not fetched:** P.U. (B) notices, except the commencement orders a read timeline lists.

**3.5 Status is read from the portal, never assumed.**
- Record what the portal states: in force, not yet in force, repealed.
- When the portal says nothing, the status is unknown.
- A filename may raise a flag. It never sets the status.
- The official document's own statement counts as the portal's statement, for example a repeal notice
  the portal publishes as the act's text.
- No adapter writes a default. Round 1 stamped "Current" on every Singapore row.

**3.6 Drafts, bills and repealed text are not evidence.** If one is fetched, record it as what it is:
`document_kind` `draft_or_bill` for a draft or a bill, `legal_status` `repealed` for repealed text
(`CONTRACT.md` 3.3). Never drop it silently. Judge from the document, not the filename: 13 Malaysian
files named "draft" are official reprints.

**3.7 Landing pages.** When a stored page has no operative text and links one document, fetch that
document as the law's text.

**3.8 Language.** Fetch the text in its source language. Never ask a bilingual portal for English when
the original is another language. Record the language of every document.
- **Malaysia** (decision 14): English first when the Attorney General's Chambers publishes an English text,
  printed or online; Malay only when it does not. Official is not authoritative, so every row taken from the
  listings records its language and edition.

**3.9 Practice evidence.** For 3.4, 5.3 and 9.1, official announcements, reports and ownership records
may be fetched. Each is recorded with its document kind, so nothing downstream mistakes it for a
statute.

## 4. Seeds and leakage

1. **Every seed records where it came from:** a portal browse, an official search, or a named host
   document.
2. **Never seed from the host baseline:** the instrument's `gold_set.jsonl`, the signature exemplars,
   or the Round 2 country sheets. Seeding from them makes every result KNOWN and the live test
   circular.
3. **Viet Nam and Kazakhstan have no baseline sheet.** Find their regional instruments (EAEU, ASEAN)
   on the official publishers. Do not copy them from another economy's sheet.
4. **Any use of a host row is disclosed** in a dated note. The Round 1 leakage audit's reasoning is
   re-run over each new registry before it is committed.
5. **Retrieval rules are systematic.** "Every amending act listed on the principal act's page" is a
   rule. A list of laws taken from the gold set is not. The gold set may measure a recall gap, reported
   as a number, and nothing else.

Round 1's own disclosure is incomplete. Five seeds were requested by gold ID or error-check target: four
cite a gold row ID, and the MAS Notice cites an error-check narrative. This workshop's own paraphrase of
the audit (`README.md` line 220) drops "hard" from "no hard backward induction". Correct both before any
submission text quotes them. See `notes/INSTRUMENT_IMPACT_2026-09-13.md` item D3.

## 5. Politeness and robots.txt

**5.1 The delay.** One request at a time per host. The wait between two requests to a host is the
larger of `REQUEST_DELAY_MS` (3,000 ms by default) and the host's robots.txt `Crawl-delay`, plus up to
half again as jitter. No economy gets its own speed setting (decision 6).

**5.1a A refusal is a reason to slow down, not to stop** (decision 23). Every portal we crawl has an
anti-scraping mechanism. When one refuses a request (HTTP 403, 429, 467 or 503, or a WAF challenge), rest a minute,
then five, then half an hour, lowering the frequency each time, and try again; stop only when six refusals come in a
row. robots.txt is the exception: its answer is taken as given.

**5.2 robots.txt.** Read it before the first request to a host, and obey it for discovery. **Open**:
whether it also binds seed URLs. Round 1's settings exempted them (`ROBOTS_HARD_BLOCK=false`), host
checklist item 25 asks for "robots.txt respected" with no exemption, and 5.4's strict reading assumes it
binds every fetch.

**5.3 What the hosts declared on 2026-09-13.** Read live by the amendment audit of the Round 1 corpus.
A verifier re-fetched SSO's the same day. The other rows were checked against the audit's saved
responses:

| Host | robots.txt | Effect |
| :---- | :---- | :---- |
| `sso.agc.gov.sg` | `Crawl-delay: 6`, `Disallow: /search` | 6 s between requests. In Round 1's crawl log, 389 of 523 gaps between lines were under 6 s (median 5 s) |
| `www.legislation.gov.au` | `Crawl-delay: 10`, `Disallow: /assets/` | 10 s between requests. Round 1's limiter waited 3 to 4.5 s for documents, and its downloads-page discovery requests did not wait at all |
| `api.prod.legislation.gov.au` | none (404) | The default delay |
| `lom.agc.gov.my` | HTTP 500, on every read that day (the last at 21:02 UTC), and again on 2026-09-14 | See 5.4 and decision 9 |
| `federalgazette.agc.gov.my` | does not resolve | Unreachable |
| `www.pdp.gov.my` | none (404) | The default delay |

**5.4 A robots.txt that answers 5xx. Open for every portal except Laws of Malaysia (decision 9).**
- RFC 9309 says to treat it as a full disallow.
- Round 1's code never reads robots.txt (5.5). Its unused `RobotsAdvisor` treats an unreachable
  robots.txt, such as a DNS failure, as allowed (`politeness.py:55-58`). It treats a 5xx answer as
  disallowed, though: Python 3.12's `urllib.robotparser` swallows the error without setting `allow_all`,
  so `can_fetch` returns False.
- Today Laws of Malaysia, Malaysia's main portal, answers 500. Under the strict reading no Malaysian
  law can be fetched from it.
- Re-check before any Malaysia run, and record the choice.
- **Decided:** `DECISIONS.md` decision 9 (confirmed 2026-09-14) allows Laws of Malaysia through a
  per-portal registry key, `lom.robots_5xx: allow`, at the default limits, until the Malaysian laws are
  all retrieved. The Malaysia scraper sends nothing to lom past robots.txt without that key.

**5.5 The Round 1 code breaks this section.** It never reads robots.txt: `RobotsAdvisor` is defined and
never called. It never reads `Crawl-delay`. The limiter also covers only the document queue:
`RateLimiter.wait` is called in one place, `orchestrator.py:256`. Discovery requests go straight to
`fetcher.fetch`, with no wait and no crawl-log line. They include up to 900 Laws of Malaysia detail
pages (`my_gazette.py:114`), one Federal Register downloads page per candidate
(`au_legislation.py:120`) and the register API pages (`au_legislation.py:247`). Inside one fetch, a 202
answer is re-requested after 4 s (`fetcher.py:165`), under SSO's 6 s, and a failed rung falls straight
through to a second request (`fetcher.py:120-121`). A fix has to put every request to a host through
the per-host wait, including discovery, retries and robots.txt itself. Until that is fixed, nothing may
claim that robots.txt is respected (`notes/INSTRUMENT_IMPACT_2026-09-13.md` item C9).

**5.6 The live test.**
- The hour is a cold crawl.
- The raw folder, the crawl log and `.idmap.json` can all be cleared on screen before the clock
  starts.
- A second pass fetches nothing.
- A run that selects zero laws fails loudly. It never exits 0. A second pass that selects laws and finds
  none changed exits 0.

## 6. Finding updates

Each country's `updates/` answers one question: where does this portal show that something changed?
Deciding whether a stored law changed is shared by every economy, and works the same way for each.

**Proposed refinement of decision 3, once agreed:**
1. **Compare the portal's version identity with the stored one.** Per portal:
   - Australia: the version's register ID, which is the compilation ID, or the title ID for an as-made
     version.
   - Malaysia: the file and As At date the updated listing (`principal.php?type=updated`) gives for the act
     now, compared with the last run's `laws.csv` (decision 16). This is decision 3's URL test. Amending acts
     by the amendment listing; P.U. (A) and P.U. (B) by their own listings, newest first by publication date.
   - Singapore: the timeline's current version date.
2. **Then a conditional GET.**
3. **Then a content hash.**

What the Round 1 corpus showed about each test:
- **Australia:** the dated fetch URL is learnt only by requesting each title's downloads page. That is
  about 3.5 hours for 1,265 register titles (1,258 Acts, 7 legislative instruments) at the portal's
  10-second crawl-delay. 366 framed rows, 362 of them as-made, are stored under the undated
  `/latest/text` URL. A new compilation of an as-made Act still resolves to a dated PDF, so the URL test
  catches it. The test misses rectifications, and the 4 compiled framed seeds raise a false alarm when
  they move to epub. One API query on registration date found the changed Act compilations in 3 paged
  requests.
- **Singapore:** `Last-Modified` is not a legal date. PDPA's copies fetched on 11 and 14 July 2026 are
  byte-identical, yet read 10 December 2025 and 14 July 2026, on a version in force from 5 December 2025.
  It moves without the law or the bytes changing.
- **Malaysia (observed 2026-09-14):** a consolidation's file path carries a project id, and the 241 Round 1
  rows that point at a different file from today's show that a new consolidation arrives under a new path.
  Re-reading the listing (decision 3's URL test) finds it; a conditional GET on the stored URL alone would
  not. Between the readings of 2026-09-13, the morning and the evening of 2026-09-14 no act's file, date or
  marker changed. Per file, ETag and Last-Modified are stable for a URL in almost every case (of 559
  byte-identical files refetched at the same path since July, 557 kept both; 2 were re-uploaded unchanged with
  new validators; the 1 file whose bytes changed, Act 869, changed its validators with its listing entry
  unchanged) and a conditional request answers 304 with no body, so test 2 settles a stored file in one
  request. Last-Modified is the upload time, not a legal date, and no listing exposes it. The P.U. (A) and
  P.U. (B) listings carry a publication date and the parent act, newest first, so new subsidiary legislation
  is found with one POST per series. `countries/my-malaysia/updates/` implements this (NOTES.md 2.6,
  decision 16).

After the crawl, two steps this policy does not cover belong to `CONVENTIONS.md` (decision 17): the audit that
flags stored files which are not the law's text, and the merge of runs into a corpus folder.

## 7. Open decisions

| Decision | Blocks | Where the evidence is |
| :---- | :---- | :---- |
| Pillar scope: 6 and 7, or every pillar the draw can reach | Registries, 1C, estimates | `notes/INSTRUMENT_IMPACT_2026-09-13.md` C1, C2 |
| Whether robots.txt binds seed URLs or only discovery | The README politeness table, checklist item 25 | Section 5.2 |
| A robots.txt answering 5xx, for portals other than Laws of Malaysia (decided for it by decision 9) | A crawl of any other portal whose robots.txt answers 5xx | Section 5.4, `DECISIONS.md` decision 9 |
| Wire robots.txt and `Crawl-delay` into the crawler, or drop the claim | The README politeness table, checklist item 25 | Section 5.5 |
| The change-detection order: decided for Malaysia (decision 16), open for Singapore and Australia until their update checks exist | Step 1B | Section 6, `CONVENTIONS.md` section 6 |
| Where the seeds for the three new registries come from | New registries | Section 4 |
| A source class for WTO documents | Crawling 1.4 | Request R4 |
