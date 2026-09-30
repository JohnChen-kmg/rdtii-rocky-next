# The index's coverage depends on a legal tier our portals may not carry

| | |
| :---- | :---- |
| Recorded | 2026-09-20, from the scraping workshop's research of the same day |
| Status | **Open.** Decisions (b) to (d) pending. Decisions (a) and (e) settled by the developer on 2026-09-20, see below |
| Decides | The developer |
| Acts on the decisions | Scraping workshop for collection and registries. Instrument workshop for reachability marking. Mapping workshop for how unreachable indicators are emitted |
| Origin evidence | `C:\Users\woshi\Desktop\rdtii-finale-1-scraping\countries\_finale-survey\explore-2026-09-20\cn-china-coverage.md` |
| Code freeze | 30 September 2026. Anything below that needs a code change is decided before then or not at all |

This record changes no scraping code and no registry. The scraping workshop owns those and holds the
evidence. It records the finding, verifies what can be verified from the workshops' own files, and puts
the decisions in front of the developer.

## The finding

Framework law delegates the operative list or threshold to a subordinate instrument: a catalogue, a
negative list, a standard, a ministerial rule. The principle sits in the statute; the number sits one
or more tiers below. So whether an economy is scoreable depends less on its statute book than on
whether its official source publishes that lower tier, and on whether we collect it.

**The delegation is general. The portal gap is not.** Sharpened on 2026-09-20 after the developer's
correction. In most jurisdictions the official gazette or legislation database publishes delegated
legislation, because that is where a regulation acquires force, and in civil-law systems built on
legal normative documents it publishes regulator circulars too. So for most economies the question is
shape 2 below, what our crawler chooses to collect, or shape 3, a page we missed. China is the surveyed
exception: its central database stops above departmental rules and forbids crawling, which is shape 1.
Six indicators are outside any law database in every economy because no instrument states their
answer: 1.4, 3.4, 5.3, 9.1, 11.4, 12.6. The full classification of all 61 is in
`..\COVERAGE_AND_MANUAL_CHECKS.md`.

It appears in three shapes, and each needs a different response.

## Shape 1. The portal does not carry the tier

**China.** The National Database of Laws and Regulations, `flk.npc.gov.cn`, carries six categories:
the constitution, laws, administrative regulations, supervisory regulations, judicial interpretations
and local regulations. It does not carry departmental rules (部门规章), normative documents
(规范性文件), national standards (GB, GB/T) or catalogues, announcements and negative lists
(目录, 公告, 负面清单).

Measured against the instrument's 61 in-scope indicators, by the workshop's desk research:

| Class | Indicators | Meaning |
| :---- | ----: | :---- |
| Fully answerable from laws plus administrative regulations | 18 | The database suffices |
| Framework only | 31 | The principle is in a law; the number is a tier below |
| Reachable at no tier the database carries | 9 | See the table below |

Pillar 7 is fully covered, 5 of 5. Pillars 1, 2, 3, 5, 6, 9, 10 and 11 are framework-only in their
entirety. Pillar 4 is good if judicial interpretations count as evidence, which is a question for the
instrument. Pillar 12 is mixed, 6 of 15 covered.

The nine no tier reaches:

| Indicator | Where the answer actually lives |
| :---- | :---- |
| 5.3 state shareholding in telecom | No legal instrument at any tier. SASAC's central-enterprise catalogue and listed-company filings |
| 4.9 source-code and algorithm disclosure | Four CAC departmental rules, 2022 to 2025 |
| 11.4 deviation from encryption standards | The deviation is itself a set of GB/T standards. Unreachable by construction |
| 12.4.5 payment ceilings | A PBOC circular and a 2015 announcement |
| 12.4.6 mandated intermediaries | A PBOC migration notice |
| 12.5 de minimis | A Tariff Commission announcement and a ministry notice |
| 10.3 local content | A State Council General Office notice, one rung below the database's floor |
| 12.7 domain names | One MIIT order |
| 9.1 blocking and filtering | The legal basis is in the database. The blocklist is published in no instrument at any tier |

**A further trap: covered can still be wrong.** The database gives foreign equity in telecom as 49 or
50 percent. A MIIT notice of October 2024 lifted the cap entirely for IDC, CDN, ISP and related services
in four zones. An index reading only the database reports the old number with full confidence.

**Two corrections the research made to earlier assumptions.** Judicial interpretations and local
regulations are carried, which an earlier note had denied. And the counts of 302 laws and 605
regulations came from the developer, not from a source the research could verify without touching the
site.

**What the research did not do.** Nothing was fetched from `flk.npc.gov.cn`. Its robots.txt is saved
at `countries\_finale-survey\robots\CN_flk.npc.gov.cn_robots.txt` and reads `User-agent: *`,
`Disallow: /`, under a comment forbidding automated tools, scripts or crawlers collecting or copying
site data. The two sites that permit crawling, `www.gov.cn` and `www.npc.gov.cn`, are saved beside it
and are not substitutes: they publish news and new laws, not the consolidated database.

## Shape 2. The portal carries the tier and our scope excludes it

The general rule is `POLICY.md` 3.4 in the scraping workshop: fetch subsidiary instruments listed
under an in-scope principal law, and limit this to in-scope laws, because every current instrument on
a portal is thousands of requests. Each economy narrows it further.

| Economy | What is collected below the act | Setting |
| :---- | :---- | :---- |
| Malaysia | P.U. (A) instruments under acts in the title rule's core groups: data protection, cyber security, communications, electronic transactions, criminal procedure. P.U. (B) notices not fetched. Sectoral acts counted, not fetched | `lom.subsidiary_acts: core`, decision 12, confirmed by decision 17 |
| Singapore | The subsidiary-legislation tab of seed acts only, at most 100 per act by the code's default | `sso.subsidiary_acts: seed`, `subsidiary_max_per_act` commented at 100 |
| Australia | The in-force Act collection plus seeded instruments. No subsidiary rule | `register.collection: Act` |
| Timor-Leste | Six gazette categories, all acts of constitutional organs. See shape 3 for the tier not read | `jornal.categories: all` |

Every core group and every seed is a pillar 6 or 7 instrument. That is sound for a data-and-privacy
index. It is possibly wrong if the live test draws another pillar, because the instrument that answers
it may be a regulation under an act no registry seeds. The `POLICY.md` 3.4 rule does not need to
change for this; the list of in-scope laws does.

## Shape 3. The portal carries the tier and we missed it

**Timor-Leste.** Reported by the developer on 2026-09-20: the Jornal da República publishes a
Diploma Ministerial category at `?q=node/23`, the ministerial implementing tier, and an Outros Actos
category at `?q=node/29`, and the crawl of 2026-09-20 collected neither. Several institution-specific
pages are also uncollected.

What the workshop's own records confirm and do not confirm:

| Claim | Workshop record |
| :---- | :---- |
| Six categories were collected | Confirmed. `countries\tl-timor-leste\sources.yaml` sets `categories: all`, which names exactly six: leis, decretos_leis, decretos_governo, decretos_presidente, resolucoes_parlamento, resolucoes_governo, at nodes 12, 13, 18, 10, 19, 20. The exploration table lists the same six plus three landing pages |
| The ministerial tier exists and carries regulation | Confirmed in substance. `countries\tl-timor-leste\NOTES.md` states that rules come from Lei and Decreto-Lei as primary law, and from Decreto do Governo "and ministerial diplomas" as subsidiary law. One collected gazette issue contains a Diploma Ministerial in its summary, so the tier is published in the same Série I issues |
| Pages `node/23` and `node/29` exist and were not read | **Not in the records.** Neither page number appears in the exploration file, the notes, the sources file or the crawl outputs. This rests on the developer's report |

This is a defect in collection, not a scope decision, and the fix is cheap: two more category pages
at the portal's `Crawl-delay` of 10 seconds. It belongs to the scraping workshop as a hand-back
request. Because the document unit is a gazette issue and 923 issues carry more than one act, some
ministerial diplomas are already inside collected issues without being catalogued as acts. Reading
the two category pages would catalogue them and fetch the issues not yet held.

## Why this matters now

The host's rules for the live test, from the workbook's Instructions sheet and the Run Record sheet,
recorded in `..\REQUIREMENTS.md` under "Read line by line from the primary host documents":

- One economy, one pillar, two indicators. "It may be a pillar you were never asked to work."
- If no documents are fetched during the hour, C5a scores zero regardless of the evidence file.
- All twelve pillars are in scope for the submission, with 6 and 7 mandatory.

Against that, `rdtii-finale-1-scraping\notes\INSTRUMENT_IMPACT_2026-09-13.md` records three items as
unresolved. All three were re-checked for this record.

| Item | What it says | Re-checked 2026-09-20 |
| :---- | :---- | :---- |
| C2 | Scraping decision 7 requires pillars 6 and 7 only. The instrument's notice for other stages says all twelve pillars need registries. The instrument contradicts itself: D8 says 6 and 7 required, D11 built all 61 codebook blocks and did not withdraw D8. "Recorded, not resolved. The developer decides" | Confirmed. `POLICY.md` section 1 now says "Pillars. Open." |
| C1 | Every seed in every registry is tagged pillar 6 or 7, so a draw elsewhere selects no seed and C5a scores zero | Confirmed. The Timor-Leste title rule's nine groups carry only 6.x and 7.x indicators. The SG, MY and AU registries carry only P6 and P7 tags |
| A4 | `parse_pillars` in the repo silently rewrites any other pillar, or bad input, to 6 and 7, so such a draw fetches the wrong documents and exits 0 | Confirmed in `stages\p1-scrape\src\p1_scrape\economies.py`: `if n in (6, 7)` with a fallback of `[6, 7]`. Also `main.py` restricts `--pillar` to `choices=[6, 7]` and the dashboard rejects any pillar outside 6 and 7. The workshop's own scrapers pass `[6, 7]` as a literal too |

One fact changed since decision 7 was taken on 2026-09-12. The instrument workshop built all 61
codebook blocks the next day, D11. The cost of twelve pillars is therefore no longer in the
instrument. It is in registries, seeds and the subordinate tier, which is this issue.

## What is verified and what is reported

| | Verified from files on disk | Reported, not yet verified |
| :---- | :---- | :---- |
| China coverage counts 18, 31, 9 | The workshop's research file states them. They are desk research from secondary sources, and the file says prices, dates and instrument numbers should be re-checked before publication | The underlying legal facts, which no file here can verify |
| Robots on the three Chinese hosts | Saved robots files, read | |
| Decision 12's scope, and the SG, AU and TL settings | `DECISIONS.md` and each `sources.yaml`, read | |
| Timor-Leste collected six categories | `sources.yaml` and the exploration table | |
| Timor-Leste has a Diploma Ministerial tier | `NOTES.md` names it; one collected issue contains one | That it is a separate category page at `node/23`, and that `node/29` exists |
| C1, C2, A4 | Code and registries, read | |

## The decisions, which are the developer's

Each has what is known and a recommendation with its reason. A recommendation is not a decision.
Nothing moves until the developer's answer is entered in the owning workshop's `DECISIONS.md`.

### a. Does decision 7's "pillars 6 and 7 only" stand?

**Settled by the developer, 2026-09-20.** Two statements, taken together. First: "we don't need to
automate for those special pillars, just mark them down." Then: "not only for China, there's a general
pattern that some pillars will not be covered, which need researcher to do manual checking, please
mark those down." So decision 7 stands. The tool automates pillars 6 and 7. Every indicator it does
not automate, in any economy, is marked for a researcher's manual check, with the reason, rather than
built. The register of those marks is `..\COVERAGE_AND_MANUAL_CHECKS.md`. One code consequence
survives: the silent rewrite of any other pillar to 6 and 7, item A4, must become an explicit
out-of-scope message before the freeze, or the tool cannot say what it does not cover. The thin seed
layer recommended below is now optional insurance, not a plan.

**Known.** The host requires twelve pillars in the submission and may draw any pillar in the live
test. The instrument for all 61 indicators exists. Every registry and every seed is pillar 6 or 7.
Three code paths reject or silently rewrite other pillars, and the code freezes in ten days. With
uniform draws, a pillar 6 or 7 task is roughly one chance in six; by indicator count it is 9 of 61.

**Options.**

| Option | Cost | What it buys |
| :---- | :---- | :---- |
| Keep 6 and 7 only, everywhere | Nothing | C5a's six points are most likely lost, and C1b's "further domains" share is lost |
| Widen to twelve pillars at full depth for six economies | Not feasible in ten days | |
| Keep 6 and 7 as the deep, required scope for the workbook. Add a thin all-pillar seed layer for the live-test economies only: the framework act per pillar, tagged, so any draw selects at least one law. Fix A4 and A5 so pillars 1 to 12 and two indicators can be passed | About 2 to 3 hours for A4 and A5. About 3 to 4 hours per built economy for the thin layer | A draw outside 6 and 7 fetches something, maps something, and scores above zero. Depth stays where the workbook is marked |

**Recommendation.** The third option. Fix A4 and A5 regardless of anything else, because they are
cheap, freeze-bound, and today turn a live-test draw into a silent wrong fetch. The thin layer must be
seeded from the instrument's exemplar law types and the portal's own listings, never from gold-set
URLs, per the leakage rules in `INSTRUMENT_IMPACT_2026-09-13.md` section D.

### b. Does decision 12's subsidiary-instrument scope stand for twelve pillars?

**Known.** The rule fetches subsidiary instruments under core pillar 6 and 7 acts and counts the
rest. It is sound for the workbook. For a live-test draw on another pillar, the operative instrument
is often a regulation under an act no registry seeds.

**Recommendation.** Tie it to (a). If the thin layer is built, make subsidiary fetching follow the
run's selected seeds rather than a static core-group list: whatever act a live-test run selects, fetch
its subsidiary instruments in that run. One pillar and two indicators select a handful of acts, so the
cost is bounded. The `POLICY.md` 3.4 rule stays as written. This is a scraping-workshop design
point, not a decision this record can take.

### c. For each economy, which subordinate tier does its portal publish, and do we collect it?

**Known.** The answer is not written down for any economy. Timor-Leste's ministerial tier is the
immediate case.

**Recommendation.** Make a tier matrix a required artefact for every built economy: the tiers the
portal publishes, which we collect, which we count, which we skip, and why. One table per country in
its `NOTES.md`. For Timor-Leste, hand back a request to read `node/23` and `node/29` and add their
categories, once their existence is confirmed from a saved page. Two requests at the portal's
crawl delay.

### d. For China, is the route a hand-collected set, and does it extend beyond the NPC database?

**Known.** `flk.npc.gov.cn` forbids automated collection in its robots.txt, in writing. `www.gov.cn`
and `www.npc.gov.cn` permit crawling. A manual set already exists at
`rdtii-finale-1-scraping\outputs\CN\CN_manual_2026-09-20`. The ministries whose instruments hold
the missing tier are CAC, MIIT, NDRC and MOFCOM, MOF and Customs, SAMR and PBOC, plus the national
standards platform. Their robots files have not been read.

**Recommendation.** China is the most expensive candidate among the three new economies for exactly
this reason, and the three are not yet chosen. If China is chosen: laws and administrative regulations
by hand from the database, since the prohibition is on automated tools; the departmental tier by
crawling each ministry site after reading its robots.txt; and a dated note recording that the
prohibition's wording also covers copying site data, so the developer has made a judgment, not
missed one. If China is not chosen, record it as the reason.

### e. Should structurally unreachable indicators be marked as such rather than scored as absent?

**Decided by the developer, 2026-09-20.** In the developer's words: "we don't need to automate for
those special pillars, just mark them down, as a notification for users that the result may be from
another source than the legal dataset." So: no retrieval or mapping is built for an indicator whose
answer is not published in any legal instrument. The instrument marks it, and every output row or
null row for it carries a notification that the result may come from a source other than the legal
dataset and is to be checked outside the tool. Entered in the instrument's and the mapping workshop's
decision logs the same day.

**Known.** The instrument already classes 3.4, 5.3 and 9.1 as practice-evidence indicators, in scope,
per `rdtii-finale-0-instrument\notes\finale_scope_and_id_hazards.md`. The China research finds 5.3
answered by no legal instrument at all, 9.1's blocklist published nowhere, and 11.4's deviation
being itself a set of standards. The host's format guidance says that where there is no relevant law,
provide an informative statement, and the host marks honesty up.

**Recommendation.** Yes. Add a reachability marker in the instrument, per indicator and where needed
per economy, with three values: reachable in law, reachable only in practice evidence, unreachable by
construction with the reason. Have the mapping stage emit the reason as the row's informative
statement instead of a bare no-provision-found. This is one YAML field and one null-statement
variant. It is also the honest answer to the live-test short note's question of which indicator a
ministry should check first.

## What happens next

1. The developer answers (a) to (e), or as many as are ready.
2. Each answer is entered in the owning workshop's `DECISIONS.md`: (a) and (b) in scraping, with a
   matching entry in the instrument's log withdrawing or confirming D8; (c) in scraping; (d) in
   scraping; (e) in the instrument's log, with a mapping entry for the emit behaviour.
3. The scraping workshop receives the hand-back requests that follow: A4 and A5, the Timor-Leste
   categories, the thin layer if chosen, the tier matrix.
4. This record's status line changes to closed, with the date.
