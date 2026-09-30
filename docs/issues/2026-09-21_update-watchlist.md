# Every update must say what it cannot see: a watch list per economy, printed on every run

| | |
| :---- | :---- |
| Recorded | 2026-09-21, from the scraping workshop, after the developer's ruling of the same day |
| Status | **Settled for scraping and built.** Three questions for other stages, and decisions (l) to (n) below |
| Settled by | The developer: *"for our update tool, we may not automatically capture these, but we should notify the user every time we update that we need to check the list"* — and *"make this a universal thing: for most of the countries, there will be links outside of the main law database, like custom lists"* |
| Builds on | `2026-09-21_minimal-source-set.md` (no economy's evidence sits on one site), `2026-09-20_china-legal-structure.md` (China's executive channel), `2026-09-20_subordinate-tier-coverage.md` decision (e) (mark what is unreachable) |
| Evidence | `rdtii-finale-1-scraping\outputs\CN\CN_ws_2026-09-21\RUN_NOTE.md` and `…\CN_sources_2026-09-21\`, both of 2026-09-21 |

## The finding

The earlier records established that an index's evidence is spread across a main law database and a named
set of other sources, in every economy. This record adds the consequence for **updating**, which none of
them addressed: **re-reading the main database next year cannot see most of what changed.**

Three things the scraping workshop measured on 2026-09-21 make that concrete.

1. **A hand-picked list of documents is backward induction.** For China the workshop had compiled 94
   verified documents by starting from the indicators and working back to the instrument that answers each.
   When CAC's own index was then crawled whole, **42 of its 68 tier-2 documents were not on that list** — a
   list four research agents had verified document by document. A list built from what we already know is
   blind to what was published since, and it shapes the corpus toward answers we already held.
2. **Sources change under the list.** `moj.gov.cn`, which `2026-09-20_china-legal-structure.md` recommended
   as China's cross-ministry rules database, now answers its robots.txt with a 302 to a hidden bot-trap link, so
   permission cannot be established. The minimal-source-set record already notes that Thailand's Council of
   State renamed its domain and that Malaysia's `federalgazette.agc.gov.my` no longer resolves.
3. **Publishers appear.** China created the 国家数据局 (National Data Administration) in 2023, and it issues
   data rules — pillar 6 and 7 territory. No source list written before 2023 names it, and no re-crawl of an
   existing site would surface it.

So an update has two loops, and only the first can be automated:

| Loop | When | What | How |
| :---- | :---- | :---- | :---- |
| Inner | Every run | Re-read each known index and diff it against the last run: added, removed, repealed | Automatic |
| Outer | Every run, by reminder | Look at every source the tool does not collect: regulators, customs and trade lists, uncollected portal categories, new publishers | **By hand**, prompted by the tool |

## What the scraping workshop built

- **A watch list per economy**, `countries\<cc>\updates\watchlist.tsv` (China: `countries\cn-china\watchlist.tsv`):
  every source the update check does not collect, with its kind, why it is not automatic, what to look for
  there, when a new version is expected, the indicators it serves, and the date it was last looked at.
- **Every update check prints it before it runs and again when it finishes**, sorted by how long since each
  source was checked, and says in terms that the check is not a complete update until they have been looked at.
  One shared helper does this for all five built economies; it never raises and never fails a check.
- **A way to record a look**, so the reminder stays signal rather than noise:
  `python countries\my-malaysia\scraper\watchlist.py <list> --checked <name>`.
- **The rule is in the rulebook** as `CONVENTIONS.md` section 5 rule 11, and step 7 of adding a country now
  requires the list.

| Economy | Sources on its watch list | Of note |
| :---- | ----: | :---- |
| China | 23 | 8 hosts that refuse us, 7 announcement streams, 4 publishers not in the source list, and gov.cn's cross-ministry library as the canary |
| Malaysia | 9 | 7 regulators its registry names but never crawls, MITI for pre-2011 trade material, and the dead gazette host |
| Australia | 5 | OAIC, Home Affairs, ACSC, and ACMA and Border Force from the minimal-source-set record |
| Timor-Leste | 5 | the two uncollected Jornal categories, Diploma Ministerial (`node/23`) and Outros Actos (`node/29`) |
| Singapore | 4 | PDPC, IMDA, CSA, and MAS |
| Lao PDR | 3 | **the Trade Portal, which the minimal-source-set record says should be the main database** |

**No regulator's robots.txt has been read for any of the five built economies**, and every list says so
rather than implying otherwise. That is the first thing a person looking down the list should do.

## Not every external source is equal: one indicator or several

Added the same day at the developer's note: *"some of the external sources only appear for one specific
indicator, while some of them might be suitable for multiple indicators."*

Measured for China by aggregating the indicators on every document in `CN_layer2_checklist.md` to the source
that publishes it (70 of 80 rows joined automatically, the other 10 placed by hand):

| Source | Indicators it serves | | Source | Indicators it serves |
| :---- | ----: | :---- | :---- | ----: |
| CAC | **16** | | SAMR | 4 |
| MIIT | 12 | | CNCA, OSCCA, NPPA | 3 each |
| gov.cn | 7 | | MPS, NHC | 2 each |
| NDRC, MOFCOM, PBOC, standards | 6 each | | **SAFE (12.4.2), Customs (12.2), NRTA and MCT (9.4), MOST (6.1), SASAC (5.3)** | **1 each** |
| MOF and the Tariff Commission | 5 | | | |

**Six of China's twenty sources serve exactly one indicator; CAC alone serves sixteen.** Two consequences, and
they pull in opposite directions:

- **For effort,** breadth sets the order. Check and automate the many-indicator sources first; a watch list
  sorted by breadth puts the hour where the evidence is.
- **For coverage,** a one-indicator source is never dropped, because it may be the only place its indicator's
  answer lives. SASAC's directory is the **only** lead for 5.3 in any source we hold. Skipping it does not lower
  5.3's score; it removes the evidence for it.

Every watch list now carries `breadth` and `breadth_basis`. China's values are measured; the other five
economies' are estimated from each source's category, because no per-document checklist exists for them yet, and
each row says which. `--indicator <id>` lists an indicator's sources, separating those **dedicated** to it from
the **general** indexes (the national database, a rules library, gov.cn) that may carry it.

**The check also found a publisher nobody had listed.** The checklist cites 地图管理条例 and the 测绘地理信息 rules
for 6.1 and 6.3; their publisher, the 自然资源部 (Ministry of Natural Resources), was in neither the links file
nor any source list. It is on China's watch list now. That is the watch-list argument made in miniature: the list
was built from what we knew, and a second reading of our own files found a gap in it.

**For the mapping stage** this sharpens the question below. A null result for an indicator served by one
dedicated source, unchecked, is the weakest null there is — nothing else was ever going to answer it.

## Questions for the other stages

**Extraction.** Documents from watch-list sources arrive by hand, with a `provenance.tsv` and no
`discovery_log.jsonl` (`POLICY.md` section 4 asks that hand-picked sets be disclosed). Does stage 2's ingest
accept a hand-collected set beside a crawled one, and does it carry the provenance sheet's
`version_date_on_document` through? China's is the first: `outputs\CN\CN_sources_2026-09-21\manual\`.

**Mapping.** When an indicator's operative source is on a watch list and has **not** been checked, a null result
is not "no provision found". It is "not looked for". Should the mapping stage read the watch list's
`indicators` and `last_checked` columns and say so in the row's informative statement? This is decision (e) of
`2026-09-20_subordinate-tier-coverage.md` applied to time rather than to reachability.

**Instrument.** The watch list's `indicators` column is the first per-economy map of which indicators depend on
a source outside the main database. It could seed the per-economy reachability marker of decision D14 instead
of being derived twice.

## Decisions

| | Decision | Owner |
| :---- | :---- | :---- |
| **(l)** | **Is the reminder advisory or a gate?** Today it is advisory: it prints, and the check still exits 0. A gate would refuse to call an update complete while any source is unchecked past a threshold. Advisory cannot be ignored silently but can be ignored; a gate cannot be ignored but will be bypassed if it is noisy | Developer |
| **(m)** | **How stale is too stale?** The helper flags sources unchecked for 90 days. Annual reissues (China's tariff plan and import licence catalogue every late December) suggest checking at least around each reissue date; the `expect` column records them | Developer |
| **(n)** | **When a watch-list source is shown to permit us and has a bounded rules section, is it promoted to automatic collection?** The rule says yes. Four Chinese publishers already qualify on robots.txt alone | Developer |

## Hand-backs

| To | What | Constraint |
| :---- | :---- | :---- |
| Scraping workshop | Done: the helper, six lists, the hooks, rule 11, the template. Open: read robots.txt for every regulator on the five lists; build the inner-loop diff for China, which re-reads today but does not yet diff | The reminder never fails a check; keep it so |
| Extraction workshop | The question above: ingest of a hand-collected set with its provenance sheet | |
| Mapping workshop | The question above: "not looked for" as a distinct null statement | Ties to decision (e) |
| Instrument workshop | The question above: seed D14 from the watch lists' `indicators` columns | |
| Deliverables | One sentence for the methodology: *"The tool re-reads each economy's main database on every update. Sources it cannot collect are listed per economy and printed at every update for a person to review."* | Honest gaps are marked up |

## What would weaken this

The lists are seeded from each registry, each country's notes and the minimal-source-set record. **They are a
starting set, not a complete one**, and they will be wrong in the same direction the hand-built China list was:
they name what we already knew. The canary row on China's list — a cross-ministry library where a rule from an
unfamiliar issuer is the sign the list is out of date — is the only mechanism here that can catch a source nobody
thought of. The other five economies have no canary yet.
