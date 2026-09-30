# Decisions: Scraping

Task-level choices and the reason for each. Newest at the bottom, so the file reads as a history.

Code changes are not logged here. They belong in
`C:\Users\woshi\Desktop\rdtii-rocky-finale\docs\CHANGELOG_FINALE.md`, three lines each.
A decision recorded here is a choice that survives the code that implements it.

---

## 2026-09-12, decision 1: The economy list is derived from the YAML files present

**Decision:** There is no economy registry. `economies.py` globs `sources_<cc>.yaml` across the
two directories in `sources.py` `_SEARCH` and builds the code and alias tables from each file's
header. Adding an economy means adding a file.

**Why:** Adding an economy already requires that YAML file. A second list is a second place to
forget. The list is hard-coded in three places today, and every one of them has to agree before a
new economy validates.

**Consequence if reversed:** A central registry file becomes a fourth thing to edit and a fourth
thing to forget. C1a asks for "minimal reconfiguration". A checklist with four edits in it reads
worse than a checklist with two, and the difference is visible to a marker.

---

## 2026-09-12, decision 2: The Hand-off #1 contract goes to 0.3.0, a MINOR bump

**Decision:** Append four optional columns, `language`, `source_language_note`, `superseded_by`
and `run_id`. Widen the `economy` enum to a two-letter pattern and widen the `doc_id` pattern from
`^(sg|au|my)-` to `^[a-z]{2}-`. Version `0.3.0`. The p2 and p3 vendored copies are re-vendored in
the same commit.

**Why:** Appended optional fields are MINOR under the interface contract. Column order is frozen,
so appending rather than inserting keeps the change MINOR rather than MAJOR. All three schema
copies set `additionalProperties: false`, so p2 rejects a p1 row carrying a new column until its
copy is updated. Same commit, or the pipeline breaks between stages.

**Consequence if reversed:** Without the `language` column, C1c has no machine-readable basis and
the claim "same indicator, whatever the language" rests on assertion. Without the widened
patterns, a Thai document fails validation after a working adapter has already fetched it, which
is the most expensive place to discover the problem.

---

## 2026-09-12, decision 3: Delta detection compares URL, then validators, then content

**Decision:** Compare the plan URL against the stored URL first. Then send a conditional GET. Use
sha256 of the body as the arbiter. Add a text-hash guard for PDFs.

**Why:** Each economy fails a different test, and the cheapest conclusive test comes first.
Australia embeds the compilation date in the URL, so a changed URL settles it with no request at
all. Singapore and Malaysia send `Last-Modified`, so one conditional request settles those.
Singapore regenerates PDF bytes server-side, so a byte hash alone reports false updates on
documents that have not changed. The sidecar counts behind this are tabled in PLAN.md step 1B-3.
Australia carries `Last-Modified` on 1 sidecar in 1,302, so no conditional request can settle it.

**Consequence if reversed:** Comparing content first means fetching every document to find out
nothing changed. That breaks the host's constraint that the live test's second pass fetches
nothing. It also puts three economies of traffic onto government portals that four other teams
read in the same hour.

---

## 2026-09-12, decision 4: The four pipeline-data folders stay siblings

**Decision:** `handoff2`, `rdtii-p1-scrape`, `rdtii-p2-extract` and `rdtii-p3-map` stay as
siblings under `C:\Users\woshi\Desktop\RDTII\pipeline-data`. Do not move one.

**Why:** They address each other by relative path. The extract stage writes to `../handoff2`. The
mapping stage reads `../rdtii-p1-scrape/handoff1_v2/manifest.csv`. Verified as siblings on
2026-09-12.

**Consequence if reversed:** Two stages break on a path that resolves nowhere, with an error that
names a directory rather than the move that caused it. The loss is an afternoon of debugging for
no gain.

---

## 2026-09-12, decision 5, proposed: `indicator_hints` values move to decimal text

**Decision, proposed, not yet taken:** Change the values written into `indicator_hints` from
`P6-I1` form to decimal text such as `6.1`. Also update the schema description at
`contracts/schemas/manifest.schema.json` line 77, which still gives `P7-I2` as its example.
Line 77 carries the same text in all three schema copies.

**Why:** The finale forbids the `P6-I1` format outright, and the description of a column is the
first thing a secretariat reviewer reads. The values come from the `indicators:` lists in
`sources_<cc>.yaml`, so this is instrument work that lands in a crawler-owned column. The column
itself is free text, so changing the values inside it is not a schema break and does not need a
MAJOR bump. Recommendation is to do it inside the 0.3.0 commit, because the file is open anyway
and a second pass over three schema copies is wasted effort.

**Blocked on:** host question 4, whether the format change is retroactive, and on the twelve-pillar
instrument workstream, which owns the ID vocabulary. `stages/p0-instrument/scripts/indicator_ids.py`
already exists and owns parsing and legacy translation. Use it rather than writing a second parser.

**Consequence if reversed:** The manifest keeps a column whose documented example is in a banned
format. It is cosmetic until a judge reads the schema. A judge will read the schema. C2b is 10
marks for citation fidelity, and the schema is where fidelity is defined.

---

## 2026-09-12, decision 6: Politeness defaults do not move, for any economy

**Decision:** `REQUEST_DELAY_MS` stays at 3000, `MAX_CONCURRENCY_PER_HOST` stays at 1, and
`RESPECT_ROBOTS_FOR_DISCOVERY` stays true. New economies inherit these. No per-economy override
is added.

**Why:** The host states the limits twice and asks for 1 request per second. The current default
is three times slower than the floor, with jitter added on top by `RateLimiter.wait`. Five teams
read the same government sites in the same hour on 15 October. A crawler that is visibly polite
is evidence. A crawler with a per-economy speed dial is an invitation to turn it up at 2 a.m. on
29 September.

**Consequence if reversed:** A full crawl takes 6 to 8 hours per economy and that is the pressure
that will produce the reversal. The gain is hours. The loss is a defensible claim, a possible
block from a government portal during the live test, and the goodwill of four other teams.

---

## 2026-09-12, decision 7: Six economies are required, three of them new and non-English

**Decision:** The 30 September submission covers six economies. Singapore, Malaysia and
Australia are done. Three new economies are required, and all three must be non-English. More
than six is optional. Only pillars 6 and 7 are required, so seed laws and seed queries for the new
economies target data-protection, cybersecurity, telecom, e-transaction and sectoral data rules,
not the whole statute book.

**Why:** The developer's scope call. Six satisfies both host readings of C1a: three in the
workbook, six on slide 7. Slide 7 also asks for at least three non-English economies, and the
three Round 1 economies are English, so every new one has to be non-English. India would not count.

Pick the three from the nine live-test economies, so each one also protects the live test:
Thailand, Viet Nam, Indonesia, China, Kazakhstan, Lao PDR, Mongolia, Russian Federation. Which three
is still open and waits on host question 1.

**Consequence if reversed:** Adding a fourth economy costs another 6 to 12 developer hours and 6 to
8 hours of crawl wall clock. Dropping below six risks C1a under the slide 7 reading. Choosing an
English economy for one of the three fails the three non-English bar.

**Addendum, 2026-09-16: the list is eight, and one of them cannot be crawled.** The developer gave the final
round's own list: **China, India, Indonesia, Lao PDR, Mongolia, Russian Federation, Thailand, Timor-Leste**, at
least three to be chosen, described as non-English, with unorganised websites and complex legal architecture.
That replaces the working assumption above: **Viet Nam and Kazakhstan are not on it, and Timor-Leste is.** A
survey of all eight the same day (`countries/_finale-survey/`, one `robots.txt` per host, nothing crawled) found:

- **China's National Database of Laws and Regulations forbids automated collection in its own robots.txt**
  (`Disallow: /` for every agent, under a comment prohibiting any crawler). Under `POLICY.md` 5.5 that ends it
  unless the host obtains permission; the sites that do allow crawling are not consolidated law.
- **India's portals refuse our client** (Akamai, HTTP 403 on robots.txt and the site root). English anyway, so it
  cannot be one of the three non-English economies.
- **Russia, Timor-Leste, Mongolia and Lao PDR have nothing technical in the way**; Russia additionally has a
  sitemap and a documented read-only API. **Thailand** needs a TLS fix for the Council of State and may meet a
  Cloudflare shield on the Law Portal. **Indonesia's** two national hubs did not answer at all.

The survey read no page and no terms of use, and chose no seed laws: it answers "can we, and at what cost", not
"what is in the law".

---

## 2026-09-13, decision 8: One policy, one contract, and a folder per economy

**Decision:** Singapore, Malaysia and Australia are revisited with two goals: amendment coverage, and
one output format for every economy, so the next stage reads them all the same way. The workshop is
organised around that.

- **`POLICY.md` says what the crawler fetches and how.** Sources, amendments, status, seeds and
  leakage, politeness and robots.txt, finding updates.
- **`CONTRACT.md` says what every economy hands on.** Files, columns, formats and the one conformance
  check. It is a draft of contract 0.3.0 until extraction agrees.
- **`countries/<cc>-<name>/` holds the same five things for each economy:** `scraper.py` (the main
  scraping file), `sources.yaml`, `updates.py` (not developed yet), `NOTES.md` and `tests/`. A new
  economy starts as a copy of `countries/_template/`. *Revised by decision 11 (2026-09-14): `scraper/` and
  `updates/` are folders, and the seed laws and generated link lists live in `links/`.*

`scraper.py`, `sources.yaml` and the Round 1 tests are working copies of repo files. They are edited
here and copied back at hand-off, following `countries/README.md`. `countries/PROVENANCE.tsv` records
each copy's repo path, repo commit (`92a5e9d`) and sha256, and a drift check runs before hand-back.
Shared engine code is never copied.

This replaces the README's former rule "Never copy source here" (line 5, since reworded to point to
this decision), for `countries/` only. `notes/` keeps its own rule of no source code.

**Revised the same day.** The first layout mirrored repo paths, with a read-only `_shared/` snapshot and
per-folder reference copies. The developer judged it too complicated. It was replaced by the layout
above, keeping the same working copies and hashes.

**Why:** The developer's call. The Malaysia crawl missed amendment data, and all three economies write
the same manifest fields in different formats. For example, SG writes no dates, MY writes `DD/MM/YYYY`
and AU writes ISO dates. One rule set that every economy is checked against is the only way a seventh
economy looks the same as the first six. It is also the evidence for C1a's "minimal reconfiguration".
The instrument workstream adopted the same work-here, hand-back-later model in its decision D9.

**Corrected the same day, after the instrument impact check.** `in_force_status` is not a
formatting difference. SG writes the literal `Current` for every row, MY never sets it, and AU reads it
only when the register is harvested. Unifying its spelling would hand extraction a clean-looking status
that nobody read from a portal. That status is exactly what the finale uses to reject drafts and repealed
text. So the one output format carries only observed values, null where nothing was read, with the source
recorded. Amendment coverage means a link from each amending act to its principal act. It does not mean
more amending acts seeded with the principal's indicator tags, because those rows score zero if cited.
See `notes/INSTRUMENT_IMPACT_2026-09-13.md` item B6, and `POLICY.md` section 3.

**Consequence if reversed:** Without a policy and a contract, each adapter keeps its own dialect and
extraction, mapping and the dashboard keep growing per-economy branches, as they did in Round 1. Without the country folders,
the per-economy work happens directly in the repo, which is workable but mixes three revisits with 1A
and 1B edits on the same files. Keeping copies without the provenance hashes is worse. The repo and the
folder drift silently. A hand-back then overwrites a repo change nobody noticed, which is how a fix made
in July disappears in October.

---

## 2026-09-13, decision 9: Laws of Malaysia is crawled while its robots.txt answers 5xx

**Decision, confirmed by the developer on 2026-09-14** ("keep web scrape, until all the law are scraped"):
`lom.agc.gov.my` may be crawled while its
robots.txt answers HTTP 5xx, at the default politeness limits and no faster. It is set per portal in
the registry (`countries/my-malaysia/sources.yaml`, `lom.robots_5xx: allow`), never in code. The Malaysia
scraper refuses to go past robots.txt when the key is absent, and obeys robots.txt whenever it answers
200. Re-check robots.txt before each Malaysia run; the day it answers 200, its rules apply. The key is
read from the registry only: an environment variable cannot open the gate.

**What already happened under the instruction.** On 2026-09-13 the developer said the portal works and
asked for its updated-act and amendment listings to be examined and the Malaysia scraper to be built.
Under that instruction:
- 15 logged requests were sent by hand, at least 6 s apart. One of them (19:39:57 UTC) also followed a
  redirect without a pause, so 16 HTTP requests.
- A dry run and a seed-scope crawl of the new scraper were run in a sandbox, both with `REQUEST_DELAY_MS=4000`
  (4 s plus up to 2 s jitter between request starts to a host).
  - The crawl's console note records 12 discovery requests: robots.txt, 5 listing requests and 6 timeline links.
    Each timeline link also redirected, and the scraper of that day followed the redirect without a pause or a
    count, so 18 HTTP discovery requests.
  - The crawl then made 25 document requests (17 stored).
  - No discovery log of either run was kept. Both are now in `outputs\MY\MY_ws_2026-09-13` (decision 15).
- robots.txt answered HTTP 500 on every recorded read up to then: three by the amendment audit, one by hand,
  and the seed crawl's (in its console output). The dry run's read was not recorded.
- After the code review, 3 more requests by hand (robots.txt and one amending act's detail page) and a
  live seed discovery of the revised scraper (28 requests, at least 3 s apart, no documents) were sent.
  robots.txt answered HTTP 500 on both further reads, the last at 21:02 UTC.
- On 2026-09-14:
  - 5 more requests by hand at 05:49 UTC: robots.txt, and the detail pages of Acts 53 and 874.
  - The live build of the Malaysian link list: 226 requests from 06:49 to 07:04 UTC, at least 3 s apart,
    no documents.
  - From 07:05 UTC, a scope-all crawl of the 1,320 listed documents into
    `pipeline-data\rdtii-p1-scrape\my_finale`, moved the same day to `outputs\MY\MY_ws_2026-09-14` (decision 15).
  - The crawl ended at 08:39:43 UTC: 1,311 documents stored, 5 duplicates, 4 files answering HTTP 500.
  - From 08:40 to 08:56 UTC, a second build of the link list with the fixed scraper: 226 requests, no documents.
  - robots.txt answered HTTP 500 at 05:49, 06:49 and 08:40 UTC; the crawl's own read is not logged.

**Why:**
- Laws of Malaysia is the only reachable official statutes portal for Malaysia. The federal gazette host
  does not resolve.
- Without the portal, Malaysia cannot be re-crawled, and the amendment gap cannot be closed. Round 1 holds
  PDPA as at 2016, and the portal lists a 2023 reprint.
- A 5xx is a server fault, not a statement of the operator's wishes. Reading it as advisory, while
  keeping the crawl at the politeness limits and identified by its User-Agent and contact address, is a
  defensible reading.
- RFC 9309 (section 2.3.1.4) requires the strict one. A crawler MUST assume complete disallow while
  robots.txt answers 5xx, and only after a long outage (its example is 30 days) MAY it treat the file as
  unavailable. The first 500 was logged on 2026-09-13, so this is a departure from the RFC. It is recorded
  here rather than left implicit.

**Consequence if reversed:** Malaysia's official portal is out of reach until its robots.txt is fixed.
The Round 1 corpus stays as it is, with 241 acts stored as a different file from the one the portal
lists as current today. The 15 October live test is unaffected: Malaysia is not in the draw.

---

## 2026-09-14, decision 10: A portal's "Superseded by" counts as repealed

**Decision:** When an official portal marks a law "Superseded by Act N" (Laws of Malaysia: "(Superseded
by Act N)" or "(Diganti oleh Akta N)"), the row's `legal_status` is `repealed` and `status_source` is
`portal_listing`. `in_force_status` keeps the portal's words as printed, and the superseding act is kept
beside it (`portal_superseded_by` in the Malaysian scraper).

**Why:** The developer's reading of the law, 2026-09-14: superseded counts as repealed. On Laws of
Malaysia the marker appears where a revised edition under the Revision of Laws Act 1968 has replaced the
old act under a new number (Pool Betting Act 1967, Act 384, is superseded by Act 809, its 2018 revised
edition). The revised editions themselves print a "LIST OF LAWS OR PARTS THEREOF SUPERSEDED" under paragraphs
7(ii) and (iii) of the Revision of Laws Act 1968, naming the old act (10 of the 11 in the Round 1 corpus). Two of
the 12 were absorbed into a consolidation rather than revised under a new number. Act 143 is in Act 784's
list of amendments, and Act 492 says it consolidates Act 131 (that 131 was an amending act is inferred from
its title). Either way the old text is no longer
the law in force, and `CONTRACT.md` 3.3 has no separate value.

**Consequence if reversed:** 12 Malaysian listing records go back to `unknown`: one crawled row (Act 384, the only one with a document),
and 11 Round 1 rows at migration, and mapping could treat a replaced
text as current beside its revised edition.

---

## 2026-09-14, decision 11: Destinations in `sources.yaml`, laws and links in `links/`, and a link list before the crawl

**Decision.** This revises decision 8's "five things" for each country folder.

- **`sources.yaml` holds the general part.** That is the destinations (portal roots, listing pages and
  endpoints, agency sites, the secondary-copy whitelist), the crawl settings, the title rule and the
  search terms.
- **`links/seed_laws.yaml` holds the laws named on purpose**, with their URLs, indicator tags and
  provenance. It is hand-edited, in flow style.
- **`links/documents.jsonl` lists every document to crawl** (with `documents.csv` and `laws.csv` beside
  it). Where a scraper can enumerate its portal, it generates the list before the crawl and nobody
  edits it by hand. The crawl can replay it (`frontier: links_file`). A list must be rebuilt after any
  change to the scraper or the registry. The list the 2026-09-14 crawl used (07:04 UTC) predates the review
  fixes and the full P.U. numbers in `links/seed_laws.yaml`, and carries no registry fingerprint, so a replay
  of it only warns. It is kept beside the crawl. The list was rebuilt with the fixed scraper at 08:56 UTC.
- **`scraper/` and `updates/` are folders**, because a scraper may need several files.
- **At hand-back, `sources.yaml` and `links/seed_laws.yaml` are joined** into one `sources_<cc>.yaml`,
  so the repo, the engine, the dashboard and `INTERFACE_CONTRACT.md` section 4 see today's shape.

**For Malaysia:**
- **Scope.** The crawl covers:
  - the document the principal listing offers for each act (45 of 885 offer none);
  - every amending act;
  - the commencement orders found on read timelines;
  - the subsidiary legislation decision 12 selects;
  - amendments known only from a timeline;
  - the agency seeds.
- **The title rule.** It is in `sources.yaml`, derived from the instrument's pillar 6 and 7 definitions,
  never from the gold set. It defines scope `relevant` (seeds plus the acts it selects: 189 rows in the
  crawl's list of 2026-09-14 07:04 UTC and 184 in the list rebuilt at 08:56, above the engine's default cap of 60). It orders the crawl (seeds, then acts the rule
  selects, then the rest) and
  decides where the costly per-act work goes: detail-page timelines, and subsidiary legislation under
  decision 12. It never sets indicator or pillar hints.

**Why:**
- **The developer's request, 2026-09-14:** the sources should hold the general destinations, another
  file should hold the link of every law, and then all the files are crawled; scraper and updates
  become folders.
- **Joining the files at hand-back** keeps the repo unchanged. The research of 2026-09-14 found three
  things:
  - Moving the seeds out of the one registry file makes Singapore and Australia select no seeds,
    silently.
  - It also blanks the dashboard's seed table.
  - `INTERFACE_CONTRACT.md` section 4 names seed laws as part of `sources_<cc>.yaml`.
- **Retrieving every Malaysian act,** not only the ones the rule selects:
  - The rule (v3) picks 122 of 890 acts, 87 of them not repealed or superseded. No title rule catches six
    acts in which the Public Prosecutor
    authorises interception, or about nine acts that set a minimum retention period for private records
    (Round 1 texts, verified).
  - The developer confirmed decision 9 as "keep web scrape, until all the law are scraped".
  - Decision 7 limits the seeds and search terms of the new economies, not a listing Laws of Malaysia
    publishes in six requests.
- **A written list before the crawl** can be reviewed and diffed for step 1B. Its rows carry the
  metadata the Round 1 engine drops, joined to the manifest on `source_url`.

**Consequence if reversed:** the seeds go back into `sources.yaml`. A Malaysian crawl rediscovers the portal
each time, leaves no reviewable list, and loses `contract_meta` at the engine.

---

## 2026-09-14, decision 12 (confirmed 2026-09-15 by decision 17): Malaysia fetches subsidiary legislation for the core pillar 6 and 7 acts

**Decision, proposed 2026-09-14 and confirmed by the developer on 2026-09-15 (decision 17, item 1).** It is set in `sources.yaml`
(`lom.subsidiary_acts: core`), and the link list and crawl of 2026-09-14 used it (44 subsidiary
instruments). This narrows `POLICY.md` 3.4 for Laws of Malaysia:
- **Which acts.** A principal act's timeline subsidiary legislation is fetched when the act matches a core
  group of the title rule and is not repealed or superseded (`lom.subsidiary_acts: core`). The core
  groups are data protection, cyber security and computer misuse, communications and interception,
  electronic transactions and online services, and criminal procedure and security.
- **Which instruments.** Only the P.U. (A) series (regulations, rules, orders, exemption orders), each
  P.U. number once, with no cap.
- **P.U. (B) notices** are not fetched. On acts outside the core groups they are counted in the run
  notes, together with the P.U. (A) instruments; on core acts they are dropped without a count.
- **Commencement orders** of amending acts are the exception (`POLICY.md` 3.3). One is fetched when a
  read timeline (the amending act's own, or its principal's) lists the P.U. (B) number the amending act's
  commencement remark cites. On 2026-09-14 that gave 17 orders for 286 distinct cited numbers (287 citations).
- **Seeds naming a P.U. instrument.** The portal copy on the parent act's timeline replaces the agency
  copy, whatever this setting says (`POLICY.md` 2).
- **Sectoral acts** (tax, companies, finance, health, employment) get their subsidiary legislation
  counted, not fetched.

**Why:**
- **The developer asked whether mapping needs regulations or only the main acts.** Mapping cites
  whichever instrument holds the quoted text, one instrument per row. Round 1's judged rows cite
  principal acts 80% of the time and regulations 6%. Malaysia's pillar 6 and 7 baseline cites no Laws of
  Malaysia subsidiary legislation (counts only, `POLICY.md` 4.5).
- **But regulations carry binding detail the acts do not:**
  - the Cyber Security Act 2024's incident-notification regulations set the reporting times;
  - its exemption order takes nine companies out of the Act;
  - a minimum retention period set only in a regulation is what indicator 7.3 scores.
- **The host's guidance** asks researchers to go down the hierarchy of law.
- **Timelines of sectoral acts are streams of untitled instruments.** The Income Tax Act lists 176
  distinct P.U. (A) instruments since 2021, 173 of them untitled.
- **P.U. (B) notices include appointments** (one of the three on Act 709's timeline), and their kind
  cannot be judged before download: the other two are untitled.

**Consequence if reversed:**
- Turned off, the corpus holds main acts and commencement orders only, and indicator evidence set in
  regulations is missed.
- Widened to every act, the crawl adds hundreds of untitled tax and customs instruments.

---

## 2026-09-14, decision 13: A Malaysian act the portal lists as another act's amendment is an amending act, unless AGC keeps its own text

**Decision.** Some principal-listing acts are amendments. When a detail-page timeline the crawl reads lists
such an act under AMENDMENTS, and the project id in the act's own document path matches (or the file is
the same), the act is recorded as:
- `document_kind` `amending_act`;
- `principal_law_number` the act whose timeline lists it, and `amends` every such act;
- no indicator tags;
- `text_version` `as_enacted`;
- the review flag `listed_as_principal_by_portal`.

Finance Acts are the main case. An act that AGC has since reprinted or updated online has a new document and
project id. It keeps operative text of its own and stays `principal_act`.

An act the listing marks repealed, partially repealed or superseded, or whose document is a repeal notice, is
never reclassified. It stays `principal_act` with the review flag `listed_on_other_timeline` (Companies Act
1965, Act 125, on Act 197's timeline). The crawl's link list of 2026-09-14 07:04 UTC predates this rule and
still records Act 125 as an amending act; the list rebuilt at 08:56 UTC records it as a principal act.

**Why:**
- **The developer's rule, 2026-09-14:** Finance Acts count as principal acts only if they serve the
  same function as principal acts.
- **What the portal data shows:**
  - The Income Tax Act's timeline lists 48 of the 49 Finance Acts as its amendments.
  - All 47 Finance Acts whose texts could be read begin "An Act to amend".
  - AGC keeps updated texts of several (Acts 742, 812, 683, 693, 702, 661), which is the portal's own
    sign that their text still operates on its own.
- **Why the rule rests on portal data.** `CONTRACT.md` 3.3 takes `document_kind` from the portal's own
  data, never from a title alone. A timeline listing is portal data; a title or a long title read by regex is
  not.
- **Known limits:**
  - At least 17 Finance Acts carry savings, transitional or "special provision" sections. Those not
    reprinted are still recorded as amending acts, flagged for review.
  - A Finance Act is linked only when a timeline that lists it was read. The Income Tax Act is a seed,
    so its timeline is always read.

**Consequence if reversed:** Finance Acts stay untagged `principal_act` rows with no link to the acts they amend. Mapping could cite
an amending act in place of the Income Tax Act, which scores zero.

---

## 2026-09-14, decision 14: Malaysia takes the English text first when AGC publishes one

**Decision.** For each Laws of Malaysia document:
- **English first.** Take the latest-dated English text AGC publishes, printed or online; Malay only
  when the act has no English text (Acts 565 and 519 today).
- **Official, not authoritative.** Here "official" means published by the Attorney General's Chambers on
  Laws of Malaysia, and not a translation (a `/terjemahan/` path). The scraper does not test the path: no
  translation is chosen today only because all 40 are Malay, and English is taken whenever it exists.
- **What each listing row records.**
  - A principal act's row records its `language`, its `edition` (printed or online) and the listing's
    online asterisk (`online_marker`).
  - An amending act's row records `language` and `edition`.
  - Documents found on timelines, and agency seeds, record `language` null.
- **The review flag `english_online_malay_printed`** marks the acts where the English text exists only
  online while a printed Malay text exists (about 20).
- **Amendments in the gap between the two dates are still fetched** (Act 527 and A1613).

This amends `POLICY.md` 3.8 for Malaysia.

**Why:**
- **The developer's rule, 2026-09-14:** always English first, as long as it is official; if not,
  Malay.
- **Why not "printed only":**
  - The listing says online versions are not the reprints made under section 14 of the Revision of Laws
    Act 1968.
  - A printed-only rule would leave 311 acts with no text, including seed Acts 53, 563 and 747.
  - It would take a Criminal Procedure Code text from before amendment A1682.
  - The printed icon also marks original gazette copies and old revised editions.
- **"Official" is not "authoritative":**
  - Under section 6 of the National Language Acts the Malay text of a law made from 1 September 1967
    prevails unless the English text is prescribed.
  - Earlier laws keep English until a Malay translation is prescribed (section 7).
  - Round 1 front pages record an English prescription on 13 files and a Malay one on 6.
  - Mapping should read the language column rather than assume.

**Consequence if reversed:**
- A Malay-first rule changes the text of most acts, and extraction and mapping expect English today.
- A printed-only rule leaves 311 acts with nothing.

---

## 2026-09-14, decision 15: Each web-scraping run gets its own folder in `outputs/<CC>/`, named `<CC>_ws_<date>`, with a run note

**Decision.**
- **Where.** Crawl output goes to the workshop's `outputs/`, where others can find it: one folder per country
  (`outputs/MY/`), and inside it one folder per run. Not into `pipeline-data`, and never into `handoff1_v2`.
- **Country folder.** It holds a `README.md` indexing the country's runs. The country's general note, on what its
  website looks like and how our scraper works, is `countries/<cc>-<name>/NOTES.md`.
- **Name.** `<CC>_ws_<YYYY-MM-DD>`: the manifest's economy code, `ws` for web scraping, and the UTC date the run
  started. A second run for the same country on the same day ends in `_2`.
- **Run note.** Every run folder holds a `RUN_NOTE.md` that records the run, its date and times, what is
  missing and the issues encountered. `outputs/RUN_NOTE_TEMPLATE.md` gives the headings.
- **Existing runs.**
  - The 2026-09-14 crawl moved from `pipeline-data\rdtii-p1-scrape\my_finale` to `outputs\MY\MY_ws_2026-09-14`.
  - The 2026-09-13 dry run, seed crawl and discovery-only check were copied from the session scratchpad to
    `outputs\MY\MY_ws_2026-09-13`. The scratchpad copies were left in place.
  - **How:** copied.
    - For the 2026-09-14 crawl, all 2,635 files were checked against the original's SHA-256, every manifest row
      against its file, and the manifest validated again. Then the `my_finale` original was deleted.
    - For the 2026-09-13 run, the seed crawl's 42 files were compared byte for byte with the scratchpad and the
      manifest validated again. All 49 files were compared again after the next move: 0 differences.
  - **Later the same day** both runs moved from `outputs\` into the country folder `outputs\MY\`, a rename. Both
    manifests were validated again and every stored document checked against its SHA-256 (1,311 and 17).

**Why:**
- **The developer's rules, 2026-09-14:**
  - The web-scraping output goes inside this workshop or another new folder for others to access.
  - Each run's folder is named country + ws + date and holds a note recording the run, time, date, what is missing
    and the issues encountered.
  - A main folder per country (`MY`) arranges the files by country.
  - A general note of what the country's website looks like and how our scraper works is the country's
    `NOTES.md`.
- **The short country code leaves more room under Windows' 259-character limit.** Long paths are not enabled on
  this machine.
  - The longest file path in `MY/MY_ws_2026-09-14` is 249 characters, 10 under the limit. With the country name in
    both places (`my-malaysia/my-malaysia_ws_2026-09-14`) it would be 267, over the limit.
  - The 2026-09-13 test lost 8 of 25 documents to paths of 263 to 273 characters.
- **A note beside the files** keeps what is missing and what went wrong with the data it describes, where a
  reader of the files will see it.

**Consequence if reversed:**
- Runs scatter again across `pipeline-data` and the scratchpad, and the scratchpad is deleted with the session.
- Without the note, a reader has to rebuild the missing list and the issues from the logs.

**Knock-on, not yet done:**
- Decision 4 still holds. Extraction defaults to `../rdtii-p1-scrape/handoff1_v2` (p2 `HANDOFF1_DIR`) and mapping to
  `../rdtii-p1-scrape/handoff1_v2/manifest.csv` (p3 `MANIFEST_PATH`), so neither sees a run here until those
  settings point at the run folder and its `manifest.csv`. Whether to switch is to be agreed with those stages.
- Moving a run into `pipeline-data` is not the way to feed it to them.

---

## 2026-09-14, decision 16: Malaysia finds updates by re-reading the listings and comparing them with the last run, and a check is a run

**Decision.**
- **How updates are found.** `countries/my-malaysia/updates/` reads the two act listings whole and the newest pages
  of the P.U. (A) and P.U. (B) listings, and compares them with the newest run under `outputs/MY/`: for each act the
  file and as-at date the listing gives now against `laws.csv`; for amending acts the file and commencement remark;
  for instruments the publication date and whether the file is stored. About 10 paced requests, no document.
- **What is fetched** is written as a delta list in the link-file format, into a new run folder, and the normal
  crawl replays it into that folder. The crawl then fetches only the changed and new documents.
- **"Since"** is the day the newest run started, or `--since`. Without a run to compare with, the check works by
  date, and every act row it reports says so. Instruments are read back to the date less a look-back (120 days),
  because an instrument can be uploaded months after its publication date.
- **A listed file that no run stored** (a failed or skipped fetch) is reported `not_stored` and fetched, unless the
  engine logged it as a duplicate of a stored file.
- **Conditional requests are the check on stored files,** not the way to find changes: `--verify-stored N` sends
  one HEAD per stored file with its ETag and Last-Modified, and 304 means unchanged. It is off by default.
- **A check is a run.** It gets a run folder and a run note even when it fetches nothing. The folder sits beside the
  crawls under `outputs/MY/` and is named for the period the check covers, `<CC>_ws_<since>_to_<date>`
  (`MY_ws_2026-09-14_to_2026-09-14` is the first; the developer asked for the period in the name on 2026-09-14).
  Its crawl, when there is one, goes into the same folder: the check and its crawl are one run.
- **The settings** live in an `updates:` block of `sources.yaml`, outside the link-file fingerprint.

**Why.**
- **The developer's request, 2026-09-14:** pick up the date of the last scrape, or a given date, and fetch only the
  laws that changed since, instead of everything.
- **The portal publishes no upload date for an act's file** (NOTES.md 1.3), so nothing but the listing itself can say
  which acts are new or re-consolidated. Reading it whole costs 3 requests; comparing it with the last run is exact.
- **Subsidiary legislation has dated, newest-first listings** with the parent act (7,306 P.U. (A), 9,150 P.U. (B) on
  2026-09-14). One POST each (with the act lists' key; the page is read only if that key fails) finds everything
  published since a date.
- **Validators hold on lom** (of 559 byte-identical files refetched at the same path between July and September
  2026, 557 kept ETag and Last-Modified and 2 were re-uploaded with new ones; the one file whose bytes changed changed
  its validators too; a conditional GET and a conditional HEAD answered 304 on 2026-09-14), so a stored file can be
  confirmed unchanged in one request, at worst fetched again needlessly. That settles POLICY.md section 6's order
  for Malaysia: listing identity first, conditional request second, hash third, as decision 3 proposed. Act 869
  shows why the second step exists: its file was replaced behind the same path with the listing unchanged.
- **A check that fetches nothing is still evidence** of what the portal listed on that day, and the live test's second
  pass must show that it read 0 documents (`evidence/README.md` artefact 3).

**Consequence if reversed.**
- Fetching every file to find out what changed is 1,300 requests and 600 MB per check; the listing diff is 10 requests.
- Without a run folder for a check, the day's reading of the portal is lost.

**Knock-on, not yet done.**
- Merging runs into one current corpus (`CONTRACT.md` section 5). A delta run's manifest holds only what it fetched;
  the previous document of each changed law is named in `contract_meta.update.previous` (found across every run's
  list), but no `superseded_by` is written onto the older row, which sits in another run folder.
- The P.U. (B) rule follows the full build: a new commencement order is fetched only for an amending act whose detail
  page `lom.timeline` reads. Widening it is decision 12's business.
- The engine's `.idmap.json` starts fresh in each run folder, so a delta run mints its own `doc_id`s.
- Singapore and Australia have no update check yet; `countries/_template/updates/__init__.py` names Malaysia's as the
  model.

## 2026-09-15, decision 17: The Malaysia tool is settled, its conventions apply to every country, wrong files are flagged, and a corpus is a new folder

**Decision.** The developer's answers of 2026-09-15 to the eight open items, and the rulebook they settle
(`CONVENTIONS.md`).
1. **Subsidiary legislation stays as decision 12 has it:** P.U. (A) instruments under the core pillar 6 and 7 acts
   are fetched, the rest recorded. "In general the act is enough", but the tool keeps regulations in: the marginal
   cost is low and there is potential use. Whether to map them later is mapping's cost to weigh, not scraping's.
2. **Supply and Appropriation Acts stay amending acts, unlinked,** as the portal lists them. Not worth a rule.
3. **Finance Acts with savings or special-provision sections stay amending acts** unless AGC reprinted them
   (decision 13). Either answer is fine; this one costs nothing.
4. **Files that are not the law's text are flagged, not fixed.** `tools/audit_run.py` reads the first pages of every
   stored file in a run and writes `audit.md` and `audit.json` into the run folder: repeal notices, another act's
   text, a Malay file behind an English link, gazette notices, scans with no text layer, landing pages, and the
   fetches that failed. The file stays as the portal served it. The flags travel into the corpus (item 8) and are
   the "broken files" feedback the interface, or an agent, reports. A few broken links are not a problem; not
   knowing which they are would be.
5. **Every act's timeline is read at the first stage.** `lom.timeline: all` in `sources.yaml`, a convention for every
   country: the detail page of every law is read when the link list is built, so every document carries its dates
   and amendment links. Malaysia's list was rebuilt with it on 2026-09-15 (05:07 to 07:21 UTC, 1,970 paced requests):
   1,414 documents against 1,315, every act dated, 0 incomplete amendment checks against 298 (`NOTES.md` 2.3). The
   98 documents the rebuilt list revealed that no run held were fetched the same day through the check's new
   `--list` mode (the developer's "yes", 2026-09-15): 75 stored, 23 failing on the portal's side.
6. **Hands off the Round 1 corpus.** `pipeline-data\rdtii-p1-scrape\handoff1_v2` is neither edited nor read as an
   input; nothing is migrated from it. A brand-new corpus folder replaces it (item 8). Whether to delete it later
   is the developer's call, not this task's.
7. **The 4 files that failed on 2026-09-14 were retried** through the update check's `not_stored` rule on
   2026-09-15 (`MY_ws_2026-09-14_to_2026-09-15`): HTTP 500 from the portal again, all four. Every later check retries
   them. Nothing more to do on our side.
8. **Runs are never merged into each other.** A corpus is a new folder, `outputs/<CC>/<CC>_corpus_<date>`, built by
   `tools/merge_corpus.py` from every run newest first: the newest copy of each law wins, older copies are listed
   in `superseded.jsonl`, audit flags travel with the rows, the manifest is validated. It is an option, run when a
   corpus is wanted, not a step of every run; nothing is re-crawled to make it. The first is
   `MY_corpus_2026-09-15`: 1,316 documents from 3 runs, 18 older copies superseded, 2 doc_ids renamed, 0 errors.

And, from the same instruction ("settle down the MY scraping tool, update the convention"):
- **`CONVENTIONS.md`** is the rulebook: what we scrape, the six-step mechanism (link list, crawl, audit, run note,
  update check, corpus), what the tool writes, the country folder and the fixed `NOTES.md` layout, the rules that do
  not move, and where each country stands.
- **Singapore and Australia are brought onto the same layout** (notes in the fixed sections, a `WORKFLOW.md` in
  `scraper/` and in `updates/` that says what runs today and what does not, an `outputs/<CC>/README.md` with no
  runs), without a live request to either portal. Their code is the Round 1 adapter until the catalogue step and
  the update check are built.

**Why.**
- The developer's answers, 2026-09-15, quoted in `notes/` only through this entry; the instruction was to settle
  the Malaysia tool, write the convention down, and apply it to Singapore and Australia.
- Reading page 1 found about 100 wrong files that no count showed (`MY_ws_2026-09-14` run note). Doing it by hand
  each run does not scale; doing it by script and keeping the flags with the rows does.
- The audit's first draft flagged 53 files as "another act's text"; 48 were "Revision of Laws Act 1968" read as an
  act number, or gazette prints. Calibrating on the real corpus before adopting the rules is why the flags can be
  trusted (`tools/README.md`).
- A delta run's manifest holds only what it fetched (decision 16, knock-on). Without a merge, "the current text of
  every act" is three folders and a rule in someone's head. Merging into a run would destroy the record of what that
  run fetched; a new folder keeps both.
- `timeline: all` costs about 1.8 hours once per list build and touches only changed acts afterwards, and it removes
  the 298 documents with no full amendment check and the 798 acts with no dates (`NOTES.md` section 5, before).

**Consequence if reversed.**
- Fixing wrong files by hand makes the corpus unreproducible and hides the portal's fault.
- Merging into a run loses the run; not merging leaves downstream reading three folders.
- Reading only the relevant acts' timelines leaves most acts without dates and amendment links.

**Knock-on.**
- The engine's `.idmap.json` starts fresh in each run folder, so a delta run can mint a `doc_id` an earlier run gave
  to another document; the corpus keeps the older run's id and renames the newer row to the next free suffix,
  recorded in its note (`NOTES.md` 2.6). A stable id across runs needs the engine to read the previous run's map.
- `CONTRACT.md` section 5 and `PLAN.md` 1B-5 expect `superseded_by` written onto the older row. Runs are never
  edited, so the corpus writes it in `superseded.jsonl` beside its manifest; whether the 0.3.0 manifest carries the
  column from there is for the contract draft.
- Downstream stages still read `handoff1_v2` by default (`outputs/README.md` rule 6). Pointing them at
  `MY_corpus_2026-09-15` is a settings change to agree with extraction and mapping.
- `tools/` in the workshop goes back to the repo's `stages/p1-scrape/tools/` with its tests (`countries/README.md`).

## 2026-09-15, decision 18, proposed: Singapore and Australia get catalogue steps, and Australia's compilations are fetched as the dated epub

**Decision.** On the developer's "please go ahead" (item 4 of the morning summary, 2026-09-15), both Round 1
adapters became packages with the convention's catalogue step (`CONVENTIONS.md` section 2), tested offline on
pages and API replies saved that day, and run live the same day.
- **Singapore** (`countries/sg-singapore/scraper/`): the catalogue reads robots.txt, the Current listing twice
  (525 acts), the Repealed (298) and Uncommenced (10) listings, the Acts Supplement of this year and last, every
  current act's detail page (its current version date, every version with its amending instrument, the original
  number) and the SL tab of the seed acts, all over plain GET at the portal's `Crawl-delay` of 6 s. A row's address
  is the PDF (`/Act/<CODE>?ViewType=Pdf`, Round 1's `source_url` form). Repealed acts are fetched too: every
  repealed act's page serves a PDF at `<path>&ViewType=Pdf` although the listing links one for only 34 of 298.
  Uncommenced acts are recorded only (their address changes daily). An Acts Supplement entry is fetched as an
  amending act when its title says so; a new principal act's consolidated text comes from the Current listing
  (decision 13's rule applied to SSO).
- **Australia** (`countries/au-australia/scraper/`): the catalogue reads the register's API only: every in-force
  Act (48 pages of 100), then the latest version of every principal Act in batches of 18 (its start date, register
  id, compilation number and the amendments it incorporates), then the seeds' titles. The `www` host, whose
  `Crawl-delay` is 10 s, is touched only for its robots.txt; the documents come from it at the crawl. Amending acts
  are recorded, not fetched: the register compiles them into the principal act (decision 13's rule).
- **Australia's document form is the dated epub** (`register.document_form: epub`): every compilation has one, single-
  or multi-volume, with every volume as spine documents that the engine concatenates (`p1_scrape.epub`), whereas
  the dated PDF exists for single-volume acts only (a multi-volume act answers HTTP 405). `pdf` is the alternative
  setting: single-volume acts as PDF, multi-volume ones failing. An as-made title (compilation number 0, register id
  equal to the title id) has a PDF at `<id>/asmade/<start>/text/original/pdf` and no epub; a `form: html` seed that
  is as-made keeps Round 1's framed capture.
- **The epub's citation is its own dated address**, no longer the undated `/latest/text` (FX4 of the notes; Round 1's
  multi-volume test changed with it).
- **The paced client and the robots.txt rules are shared** by import from Malaysia's package until the engine gains
  them (an engine request, `NOTES.md` 2.5 of each country).

**Why.**
- The convention asks for a link list before any crawl and every act's detail read at the first stage; neither
  Round 1 adapter had a catalogue step, and both discovered during the crawl without pacing discovery.
- The addresses were checked live before being written into a list: SSO's repealed PDF by one HEAD (AA1987,
  HTTP 200, 24,745 bytes); the register's dated PDF (Privacy Act, HTTP 200, `application/pdf`), the multi-volume
  PDF (Criminal Code, HTTP 405) and epub (HTTP 200, `application/epub+zip`), and the as-made address from two
  downloads pages (C2021A00098, F2025L00278), on 2026-09-15.
- One form for every Australian act removes the multi-volume failure mode (2026-07-17's truncation) and the
  downloads-page pass that cost 3.5 hours at 10 s; the developer can set `pdf` if extraction prefers PDFs.

**Consequence if reversed.**
- `document_form: pdf` loses the multi-volume acts (33 in Round 1) until a second pass fetches their epubs.
- Without the catalogue steps, Singapore and Australia stay off the convention: no list, no audit, no update check.

**Knock-on.**
- The first crawls need the engine's delay raised to the host's `Crawl-delay` (`REQUEST_DELAY_MS=6000` for SSO,
  `10000` for the register) because the engine's limiter has one delay for every host (`POLICY.md` 5.5).
- No Singapore or Australian update check yet (`updates/WORKFLOW.md` of each says how it will run); no
  subsidiary legislation beyond the seed acts (decision 12's rule); Australia's repealed titles are not harvested.
- **Singapore's edge challenged the plain client** from about the 45th minute of the catalogue build (50 act pages
  answered HTTP 202) and answers every request since 13:00 UTC with `x-amzn-waf-action: challenge`, `robots.txt`
  included (`sg-singapore/NOTES.md` 1.3). The list of 11:50 to 12:58 UTC stands (1,041 documents, 50 acts without
  details). The challenge lifted after an hour's silence (a probe at 14:05 UTC: `robots.txt` HTTP 200), and the
  first crawl ran from that list from 14:09 UTC at 6 s, watched for the challenge's return; the rebuild with the
  review fixes waits for a quieter day, or for a browser transport in the catalogue. Australia's register did not
  challenge (its crawl ran at 10 s).
- Hand-back: the packages replace `adapters/sg_sso.py` and `adapters/au_legislation.py`; `PROVENANCE.tsv` rows
  changed to the package folders.
- **Afternoon of 2026-09-15, how the crawls were kept going.** Singapore's crawl was challenged after 131 fetches
  (14:35 UTC) and resumed in cycles: an hour's silence, one probe of `robots.txt`, the same run at 15 s. The first
  resume (15:36 UTC) was not challenged but a watcher misread the log's tail and killed it after 9 fetches; from
  15:52 UTC the engine is left to stop itself (it does, after 10 empty answers, writing its manifest first). A
  crawl killed from outside loses every document stored since the engine's last checkpoint (one every 10): the
  audit now reports those files (`orphan_file`). Three titles (two Singaporean, one Australian) are too long for
  Windows' 260-character path limit under `outputs\<CC>\...` and failed to store (`store_failed` in the audit);
  the crawls run through a `subst` drive (`R:`) so every path fits. Both are engine requests for the hand-back
  (each country's `NOTES.md` 2.5): a capped storage folder name and a checkpoint per stored document.

## 2026-09-16, decision 19: Singapore's repealed acts are dropped from the crawl, and every country's scraper writes a law table

**Decision.** Two answers from the developer on 2026-09-16, after the figures below were put in front of them.

1. **The 298 repealed Singaporean acts are not fetched.** The run `SG_ws_2026-09-15` continues from a filtered
   list, `links_used/documents_no_repealed.jsonl` (743 of the 1,041 rows), which the crawl reads for the rest of
   the run; the full list stays beside it. The repealed acts keep their row in the census (`links_used/laws.csv`,
   with the portal's repeal date) and appear in the law table under `--all` with `scraped` `no`. A repealed act
   that is ever cited can be fetched on its own: it is one request.
2. **A law table, `scraper/checker.py`, one per country** (`CONVENTIONS.md` section 2, step 7). It writes
   `law_table.csv` into a run or corpus folder: one row per law with `in_force`, the effective date and the last
   amendment, plus the columns each portal supports. It sends no request. The developer asked for the table itself
   at this stage, **not** a comparison against earlier years' records, and accepted that the three countries answer
   with different completeness. Built on 2026-09-16: `MY_corpus_2026-09-15` 1,441 rows (1,391 scraped),
   `AU_corpus_2026-09-15` 1,277, `SG_ws_2026-09-15` 1,072 (599 scraped so far).

**Why, on the repealed acts:**
- `POLICY.md` 3.6 says repealed text is not evidence, and a repealed act cannot be the measure an indicator asks
  about. The instrument's source hierarchy (statute, regulation, guidance, tracker) has no rung for it.
- They were in the list under decision 11 ("crawl every law on a portal"), which was taken before this portal's
  edge began challenging our client. At the pace the challenge allows, the 298 are about five hours of crawling.
- The value they carry, "this law is no longer in force, and here is when it ended", is in the census already: 298
  rows with a repeal date, read from the Repealed listing when the list was built.
- The ordering made this urgent rather than academic: the crawl fetches seeds, then the acts the title rule
  selects, then the rest, and 23 Acts Supplement rows sit **after** the repealed block. Stopping the run at the
  repealed acts would have lost those 23; a filtered list keeps them.

**Why a table per country, not one shared tool** (the developer's reasoning, accepted):
- Each portal records dates its own way, and the differences are not cosmetic. Singapore states a current version
  date for every act and names the last amending instrument. Australia gives a compilation's start, its end when a
  later one is registered, and the enactment date, but answers only for titles in force, so a repealed title is
  absent rather than marked. Malaysia states a status for 133 of 1,291 laws and no "last amended" at all, so that
  column is derived from the amendments in our own corpus and covers 192 of 822 principal acts.
- The leading columns are the same in all three, so the tables line up; the country-specific ones follow.
- `in_force` is a reading of what the portal states, never an inference (`POLICY.md` 3.5): `yes`, `no (repealed)`,
  `not yet`, `not stated`.

**What this does not do.** It does not compare our holdings with what earlier RDTII rounds recorded. The developer
deferred that ("we dont need to compare at this stage"). When it is wanted, the input is the earlier round's own
record, and the comparison can be an offline join against the census, needing no new requests.

**Also settled on 2026-09-16, from the same conversation:** regulations stay as decision 12 defines them. They are
a small and largely paid cost (86 of Malaysia's 1,391 documents, 188 of Singapore's list, 7 of Australia's), the
instrument does score them below statutes, and the expensive part of the collection is elsewhere. Left open: the
developer's question about treating amending and commencement instruments as linkage only, excluded from OCR and
mapping (37% of Malaysia's corpus, and where 41 of the 55 scans sit), and whether Singapore's update check waits
for a browser transport while Australia's is built from one API query.

## 2026-09-16, decision 20: Amending and commencement instruments are linkage, except where our text has not caught up with them

**Decision.** On the developer's instruction of 2026-09-16 ("then, do it in the linkage way"), an amending or
commencement instrument is **kept, linked to its principal law, and not read for indicators**. It is not put
through OCR and not mapped. The exception is the pair `POLICY.md` 3.3 already asks to flag: when an instrument we
hold is **newer than the principal text we hold**, that instrument is the only place in the corpus where its
changes are written out, so it is read and mapped like any other evidence.

Every country's law table now carries a `use` column that states which case a document falls in
(`scraper/checker.py`, `CONVENTIONS.md` section 2, step 7):

| Value | What a later stage does |
| :---- | :---- |
| `evidence` | Read it, OCR it if it is a scan, map it |
| `evidence, text stale` | The same, knowing an instrument we hold is newer than this text |
| `linkage` | Keep the row and the link to the principal. Do not read, OCR or map |
| `linkage, text needed` | Read and map after all: our principal text predates it |

**What it comes to, on `MY_corpus_2026-09-15`** (Malaysia is the only country this touches: Australia holds 3
amending documents and Singapore's are the Acts Supplement of two years):

| Use | Documents | Scans needing OCR |
| :---- | ----: | ----: |
| `evidence` | 797 | 15 |
| `evidence, text stale` | 78 | 1 |
| `linkage` | 384 | 39 |
| `linkage, text needed` | 132 | 1 |

So 384 documents, 28% of the corpus, are dropped from OCR and mapping, and the OCR queue falls from 56 scans to
17. The carve-out costs 132 documents, one of which is a scan.

**Why:**
- **`POLICY.md` 3.2:** an amending instrument carries no indicator tags of its own, and an amending act cited in
  place of the principal scores zero. Mapping one cannot produce a scoring row, and doing it by accident produces
  a zero-scoring row, so the exclusion removes a way to lose marks rather than a way to gain them.
- **The instrument's source hierarchy** (statute, regulation, guidance, tracker) has no rung for an amendment: it
  is part of a statute's history, not a separate measure.
- **But an amendment is still law, and sometimes it is the only text we hold that states the current rule.** Two
  of our own files show the two shapes. The Arbitration (Amendment) Act 2024 reads "by substituting for the words
  'Parts I, II and IV' the words 'Parts I and II, Chapter 2 of Part III and Part IV'", which says nothing on its
  own. The Penal Code (Amendment) Act 2023 writes out a whole new section 507a creating the offence of stalking,
  which is the rule itself. Our Arbitration Act is stored as at 1 November 2018 and that amendment is dated
  1 November 2024, so on the points it changed the amending act is the only current text in the corpus.
- **The linkage is the point of keeping them.** Recording that Act 646 was amended by A1737 in 2024 is what tells
  a reader, and the audit, that the 2018 text is stale.

**How the flag is computed,** from the corpus alone, with no new requests: an amending or commencement document
whose date is later than the principal text's date marks both sides, the principal `evidence, text stale` and the
instrument `linkage, text needed`. Malaysia links the two by `principal_law_number`, which its timelines give;
Singapore and Australia link them by the principal act's own `last_amending_instrument`, which is the only link
those portals publish (their listings of new acts do not say which act each one amends).

**Consequence if reversed:** mapping all 516 Malaysian amending and commencement documents adds 39 scans to the
OCR queue and produces rows that cannot be cited under `POLICY.md` 3.2. Dropping the carve-out as well would leave
78 Malaysian principal texts cited as current when an amendment we hold says otherwise.

## 2026-09-16, decision 21: Australia's update check is built; Singapore's waits, and will not poll every act

**Decision.** On the developer's instruction ("for AUS, please build it and create documentation as convention"),
`countries/au-australia/updates/` is a working package, run live the same day. It asks the register's API for
every latest version registered since the baseline's list was built, compares each `registerId` with the one the
baseline recorded, and writes a delta list the ordinary crawl replays.

**What it cost to check the whole statute book: 3 requests**, plus 2 for `robots.txt`. The first live check found
**one changed law** of 4,772 titles: the Water Act 2007, recompiled from `C2026C00302` to `C2026C00398`. It was
fetched, audited and merged into `AU_corpus_2026-09-16`
(`outputs/AU/AU_ws_2026-09-15_to_2026-09-16/RUN_NOTE.md`).

**The scope rule, learnt from the first live run.** The query returns every title in the `C` and `F` prefixes, and
the baseline lists only the Act collection, so the first run queued 31 legislative instruments the country does
not collect. A title is in scope when the baseline already lists it, when it is a seed, or when it is an Act;
everything else is counted by series and dropped (`updates/diff.py`, `in_scope`). That first run folder was
deleted and the check re-run.

**Singapore's check is deliberately not built the way its stub describes.** The stub assumes a version-date read
on each of the 525 current acts, about 52 minutes at the portal's stated delay. The crawl of 15 and 16 September
showed that the edge challenges a plain client after roughly 130 requests, so that sweep would fail halfway and
take a day in cycles. The design to build instead, when the developer chooses:

- Read the **Acts Supplement** and the **subsidiary legislation supplement** for the period. Between them they
  name new acts, new amending acts, new regulations and, crucially, **commencement notifications**: commencement
  is what changes a consolidated text, and it can lag publication by months.
- Each new instrument names the act it affects on its own first page. Re-read only those acts' detail pages.
- A monthly check is then a handful of listing requests plus one per real change, well inside what the portal
  tolerates, and **no browser transport is needed**.
- **What that design misses,** and must be stated wherever it is used: a change no supplement announces, such as a
  revised edition republication or a correction. The remedy is an occasional full sweep, which does need either
  the browser transport or a day of cycles.

**Why the two countries differ so much:** Australia's register publishes version identity as data, so a
comparison is arithmetic. Singapore publishes it as a date on each act's page, so finding it costs a request per
act. That is a property of the portals, not of the tool.

## 2026-09-16, decision 22: Singapore's update check works from a date, and decides amendments by the timeline

**Decision.** The developer's design, settled step by step on 2026-09-16: the last run's list carries every law and
its date, or a date is entered by hand, as Malaysia's check already allows. The check takes that date, finds
everything on the portal that changed on or after it, scrapes what is new or amended, and reports what was
repealed. Two refinements came out of reading the portal's own pages that day, and the developer adopted both.

- **An amendment is decided by the in-force date on the act's timeline** ("go with the timeline date for amend").
  An amending act is often published long before it takes effect: Act 40 of 2020 was published in December 2020 and
  took effect in October 2022, and the Online Criminal Harms Act's version of 15 September 2026 comes from Act 10 of
  2025, published in March 2025. Comparing publication dates would have missed both.
- **The Current listing's file stamp chooses which timelines to read.** Each row carries when the portal last
  generated the act's file. That is not a legal date (it matches the version date on 5 of 458 acts), but a new
  version always makes a new file, so an act whose file is older than the date cannot have been amended. The rest
  have their timeline read, seeds first, capped at 60 so a long period cannot provoke the portal's challenge.

Repeals come from the Repealed listing's dates and are reported, never fetched. New and amending acts come from the
Acts Supplement's dates. New regulations under the eight seed acts come from their regulations tabs.

**What it cannot see,** written into `updates/WORKFLOW.md`: a new version whose file the portal has not generated
yet, a correction that does not regenerate the file, and new regulations under an act that is not a seed. An
occasional full sweep of every timeline is the remedy, and that is what a browser transport would make cheap.

**Built:** `countries/sg-singapore/updates/` (baseline, query, diff, delta, command line), 14 offline tests on saved
pages, and the parser now keeps each listing row's file stamp. The check's `laws.csv` carries forward every act it
did not re-read at the baseline's version date, so its run folder is a complete baseline for the next check.

**Not yet run live.** The first attempt, 2026-09-16 21:29 UTC and seven hours after the 24-hour crawl ended, got
robots.txt normally and then **HTTP 403** on the Current listing. The check stopped and wrote nothing. The portal's
edge has moved from challenging our client to refusing it; that is the strongest evidence yet for the browser
transport, and the reason the live run waits.

**Addendum, 2026-09-16, the cadence and the flaws.** Asked whether it would be quicker to re-scrape Singapore than
to maintain an update check, the developer agreed on both, on different schedules: the check about monthly, a full
rebuild about quarterly. A rebuild costs about 1,570 requests and one to two days on this portal; a check about 50
to 130 requests and an hour or two. The check's flaws are written into `countries/sg-singapore/updates/WORKFLOW.md`
section 8: 50 of 525 acts in the baseline have no recorded version date, checks carry those gaps forward until a
rebuild, three kinds of change are invisible to it, and its file-stamp filter relies on the portal always
regenerating a file for a new version. The quarterly rebuild closes all four.

**Addendum, 2026-09-17, the refused checks.** Three live update checks were refused (HTTP 403) on every listing
request, the second and third after two hours of rests each, while single requests loaded. The first explanation,
that the 500-row listing page was too heavy, was wrong: the third check read 100 rows a page and was refused on the
very page a probe had loaded. What differed was the User-Agent. The check built its client without the stage's
settings and sent the adapter's bare fallback, with no contact address, where the list build, the crawl and the
probes send the configured one. That was a bug and is fixed: the check now identifies itself exactly as every other
step does. Listings are also read 100 rows a page by their Next Page links (`sso.listing_paging: next`; `orders` keeps
the old read), which is lighter and was kept. The registry is unchanged, so the list of 2026-09-15 keeps its
fingerprint. Four tests added; 280 pass. **The next check, 2026-09-17 02:35 UTC with the configured User-Agent,
read the portal in 22 requests without a refusal** and found nothing changed since 2026-09-15.

## 2026-09-16, decision 23: When a portal refuses us, rest and slow down; do not stop

**Decision.** The developer's rule of 2026-09-16: Singapore "and also other countries" have anti-scraping
mechanisms, and when one refuses us, "stop for 30 mins or 1 min, then it is ok, just decrease the frequency to visit
the website". Every catalogue step and update check now does that instead of stopping.

**How it works,** in the paced client all three countries share (`countries/my-malaysia/scraper/client.py`):

- **A refusal** is HTTP 403, 429, 467 or 503, or any answer carrying `x-amzn-waf-action` (Singapore's edge sends its
  challenge that way, with HTTP 202). A plain HTTP 202 is not a refusal: Singapore sends it while a page is prepared.
- **On a refusal the client rests**, a minute the first time, five minutes the second, half an hour after that,
  **doubles its delay between requests** (up to one request a minute) for the rest of the session, and sends the
  same request again. A Retry-After the portal asks for is honoured when it is longer.
- **An answer that is not a refusal resets the count**, but the slower pace stays.
- **Six refusals in a row stop it**, about two hours of resting, with a message that says how long it rested and how
  slow it went, so a stop is a real finding and not an impatient one.
- **robots.txt is never rested on**: its answer is taken as given.
- **Tunable without code:** `PACED_RESTS` (seconds, comma-separated), `PACED_MAX_RESTS`, `PACED_SLOWDOWN`,
  `PACED_MAX_DELAY`. `max_rests = 0` restores the old stop-at-once rule.

**Why.** Stopping at the first refusal threw away work a pause would have saved. The first live Singapore update
check stopped on its second request, a single HTTP 403, and wrote nothing. The crawl of 15 and 16 September had
already shown the portal recovers after a rest, and that the rest governs how long the next stretch lasts.

**Two tests changed on purpose,** because they pinned the old rule: Malaysia's throttling test and Singapore's WAF
challenge test each now expect six rests and six more tries before the stop. Seven new tests cover the client's
rule itself. 276 tests pass.

**Not covered here:** the engine's document crawl uses its own fetcher, not this client. For crawls the same rule is
applied from outside by the resume loop (rest, probe once, resume slower); building it into the engine's fetcher is
added to the hand-back requests.
