# Conventions of the scraping tool

The rulebook for every country's scraping tool: what we scrape, how the tool works, what it writes, how a country
folder is laid out, and the rules that do not move. Settled 2026-09-15 with Malaysia as the worked example
(`DECISIONS.md` decisions 11, 15, 16 and 17). `POLICY.md` says what to fetch and how politely; `CONTRACT.md` says
what every economy hands to extraction; this page says how the tool is built, run and stored. Where they overlap,
the older two win and this page points at them.

A country is **on the convention** when every step in section 2 exists for it and every item in section 4 is in
its folder. Section 6 says where each country stands.

## 1. What we scrape

| | Rule | Where it is decided |
| :---- | :---- | :---- |
| **Laws** | Every principal law the official portal lists, at scope `all`: the current consolidated text of each. Not only the seeds, not only the pillar 6 and 7 laws. The title rule marks the relevant ones; the crawl takes all | Decision 11 |
| **Language** | The official English text first when the portal has one, the other official language otherwise. The link list records which was taken | Decision 14 |
| **Amending instruments** | Every amending act the portal lists, linked to its principal law, with no indicator tags of its own | `POLICY.md` 3.2, decision 13 |
| **Subsidiary legislation** | Regulations and orders under the core pillar 6 and 7 acts, and the commencement orders the amending acts cite. The rest is recorded in the list, not fetched. Keep developing the tool with regulations included: the marginal cost is low and the use is real (developer, 2026-09-15) | Decision 12, decision 17 |
| **Timelines** | The detail page (timeline, history, versions) of **every** act is read at the first stage, when the link list is built, so every document carries its dates and amendment links. Not only the relevant acts' pages | Decision 17 |
| **Seeds** | The laws named on purpose in `links/seed_laws.yaml`, with their provenance. The gold set is never a seed | `POLICY.md` section 4 |
| **Versions** | The version the portal dates as current, chosen by the portal's date, never by upload order or filename | `POLICY.md` 3.1 |
| **Status** | Read from the portal (in force, repealed, superseded, not yet commenced); never written as a default | `POLICY.md` 3.5, decision 10 |
| **Not fetched** | Anything robots.txt disallows for the crawler, search endpoints, and every host not named in `sources.yaml` | `POLICY.md` section 5 |

Supply and Appropriation Acts, and Finance Acts with savings provisions, stay as the portal lists them (amending acts,
unlinked): a classification nobody downstream needs today (decision 17).

## 2. The mechanism

Seven steps. The first two make a run; the third checks it; the fourth records it; the fifth fetches only what
changed; the sixth builds what downstream reads; the seventh lists the laws in it for a person to read.

```
sources.yaml + links/seed_laws.yaml         where to look, how, and the laws named on purpose
        |
        |  1. LINK LIST     scraper (catalogue step): reads the portal's listings and every act's
        |                   detail page; fetches no document
        v
links/documents.jsonl, laws.csv             every document to fetch, in crawl order, with its details
        |
        |  2. CRAWL         the shared engine replays the list into a NEW run folder
        v
outputs/<CC>/<CC>_ws_<date>/                manifest, raw files, crawl log, the list it read (links_used/)
        |
        |  3. AUDIT         tools/audit_run.py reads the first pages of every stored file
        v
        audit.md, audit.json                which files are not the law's text; which fetches failed
        |
        |  4. RUN NOTE      written from the files: times, counts, what is missing, the issues
        v
        RUN_NOTE.md; a row in outputs/<CC>/README.md
        |
        |  5. UPDATE CHECK  updates/: re-reads the listings, compares with the last run, writes a
        |                   delta list into outputs/<CC>/<CC>_ws_<since>_to_<date>/; the crawl
        |                   replays it there; then steps 3 and 4 again
        v
        |  6. CORPUS        tools/merge_corpus.py merges every run, newest first, into a new folder
        v
outputs/<CC>/<CC>_corpus_<date>/            one document per law: what extraction and mapping read
        |
        |  7. LAW TABLE     scraper (checker step): reads the folder's own files, sends no request
        v
        law_table.csv                       one row per law: in force or not, effective date, last amendment
```

**Step 1, the link list** (`scraper/`, the catalogue step). Reads robots.txt, every listing the portal offers for laws
and amendments, and the detail page of every act. Writes `links/documents.jsonl` (every document to fetch, with the
contract's metadata in `contract_meta`; `documents.csv` is the same for a spreadsheet), `laws.csv` (every listed law and why any has no document), `catalogue_meta.json`
(settings, request count, robots.txt record, a fingerprint of the registry) and `discovery_log.jsonl` (every request
sent). No document is downloaded. The list is read and checked before the crawl, and the crawl refuses a list built
from a different registry. Malaysia: 226 requests with `timeline: rule` (2026-09-14), 1,970 with `timeline: all` (2026-09-15, 2 h 14 min).

**Step 2, the crawl.** The shared engine (`stages/p1-scrape`, unchanged) replays the list into a new run folder
given as an absolute path. Discovery during the crawl is off; the list is the frontier. The copy of the list the
crawl read is kept in the run folder as `links_used/`. Politeness is the engine's, never relaxed (section 5).

**Step 3, the audit** (`tools/audit_run.py`). The engine's counts cannot show that a stored file is a repeal notice,
another act's text, a Malay file behind an English link, a scan, or a landing page. Reading the first pages can.
The audit flags them (`tools/README.md` lists the flags), lists the failed fetches, and writes `audit.md` and
`audit.json` into the run folder. **Flag, do not fix:** a wrong file stays as the portal served it, flagged, so
extraction knows and the portal can be told (decision 17). The flags are the feedback the interface or an agent
reports as "broken files".

**Step 4, the run note** (`RUN_NOTE.md`, from `outputs/RUN_NOTE_TEMPLATE.md`). Written when the run ends, from the
files: times from `crawl_status.json` and the logs, counts from `manifest.jsonl` and `crawl_log.jsonl`, what is missing
from the list against the manifest, wrong files from `audit.md`, the issues from the console. Later changes to the
folder are added, dated.

**Step 5, the update check** (`updates/`). Asks the portal what changed since the last run instead of crawling
everything: re-reads the listings whole and compares them with the last run's `laws.csv` (the newest run under
`outputs/<CC>/`); reads the dated listings of subsidiary legislation back to the date less a look-back; reports
every change with its reason (`changes.md`) and writes a delta list of only the documents to fetch. The check
writes its own run folder, named for the period it covered; its crawl fills the same folder (the check and its crawl
are one run). A check that finds nothing keeps its folder: it is the record of what the portal listed that day.
Malaysia: 8 requests, plus two per changed or unstored act under `timeline: all`, no document. Conditional requests (`--verify-stored`) are the check on stored files, not the
way to find changes (decision 16). A failed fetch is reported `not_stored` by every later check and tried again.
After a list rebuild, the check is run with `--list links/documents.jsonl`: the rebuilt list is compared with every
run and the documents no run stored (the ones only a timeline reveals) go on the delta list as `not_in_runs`.

**Step 6, the corpus** (`tools/merge_corpus.py`). Runs are never merged into each other. A corpus is a new folder,
`<CC>_corpus_<date>`, built from every run newest first: the newest copy of each law (by portal id and document
kind) wins, older copies are listed in `superseded.jsonl`, audit flags travel with the rows, the manifest is
validated against the contract, and `CORPUS_NOTE.md` says what came from where. It is the one folder downstream
stages read; it is rebuilt, never edited, and it is an option, not a step every run needs (decision 17).

**Step 7, the law table** (`scraper/checker.py`, the checker step, one per country). It writes `law_table.csv`
into a run or corpus folder: one row per law, with what the portal says about it. It sends no request, because
every value is already in the folder (the census `links_used/laws.csv`, the link rows' `contract_meta`, the
manifest). Build it on the corpus for the current picture; on a run to see one crawl.

Every country's table starts with the same columns, so the three line up:
`law_name`, `law_number`, `portal_id`, `document_kind`, `use`, `in_force`, `legal_status`, `status_source`,
`effective_date`, `last_amended`, `last_amending_instrument`, `scraped`, `doc_id`, `access_date`, `source_url`,
`file`, `run`, `notes`. A country adds its own after these (Singapore a repeal date and revised edition,
Australia the enactment date, compilation number and the day the text stops being current, Malaysia the portal's
status marker, the text version and the language).

**The `use` column says what a later stage should do with each document** (decision 20): `evidence` (read it,
OCR it, map it), `evidence, text stale` (the same, but an instrument we hold is newer than this text),
`linkage` (an amending or commencement instrument: keep the link, do not read, OCR or map) and
`linkage, text needed` (an instrument newer than the principal text we hold, so it carries text nothing else in
the corpus carries). The flag is computed from the corpus alone: an instrument dated after the principal text
marks both sides of the pair, which is what `POLICY.md` 3.3 asks for.

Two more rules hold everywhere. **`in_force` is a reading of what the portal states, never an inference**
(`POLICY.md` 3.5): `yes`, `no (repealed)`, `not yet`, `not stated`. And **what a portal does not publish stays
empty**, which is why the tables differ in completeness: Singapore states a status and a version date for every
act, Australia's register answers only for titles in force, and Malaysia states a status for 133 of 1,291 laws.
`--all` adds the laws the portal lists that the run did not fetch, which is how a dropped set (Singapore's
repealed acts) still appears with its status and repeal date.

## 3. What the tool writes

Everything goes under `outputs/<CC>/`, one folder per country, one folder per run or corpus. Nothing goes into
`pipeline-data` or beside the Round 1 corpus (`outputs/README.md` has the working rules and the path-length reason
for the short names).

| Folder | Name | Holds |
| :---- | :---- | :---- |
| A crawl | `<CC>_ws_<YYYY-MM-DD>` (`_2`, `_3` the same day) | `RUN_NOTE.md`; the engine's `manifest.csv`, `manifest.jsonl`, `crawl_log.jsonl`, `raw/`, `cost_report.json`, `crawl_status.json`, `.idmap.json`; `links_used/` (the list it read); `audit.md`, `audit.json`; `logs/` |
| An update check, with its crawl | `<CC>_ws_<since>_to_<YYYY-MM-DD>` | The same, plus `changes.md` and `changes.json`; `links_used/` is the delta list. Without a crawl: no manifest, no `raw/` |
| A corpus | `<CC>_corpus_<YYYY-MM-DD>` | `CORPUS_NOTE.md`, `manifest.csv`, `manifest.jsonl`, `raw/`, `links_used/`, `superseded.jsonl`, `corpus_meta.json`, `law_table.csv` |
| The index | `outputs/<CC>/README.md` | One row per run and corpus: what it is, what it stored, which is current |

Runs sort by their end date; a check sorts after the crawl it followed. `RUN_NOTE.md` is required in every run
folder, even a check that fetched nothing. The manifest is in the Hand-off #1 shape (`CONTRACT.md`); the details the
engine does not write (document kind, links, status, version date, language, flags) are in the link rows and join
back on `source_url`.

## 4. The country folder

`countries/<cc>-<name>/`, the same for every country; a new one starts as a copy of `countries/_template/`.

| Path | What it holds | Required |
| :---- | :---- | :---- |
| `scraper/` | The portal adapter as a package: how to find laws on this portal, how to build the link list, how to fetch each document. `WORKFLOW.md` beside it: how to run a full crawl, step by step, with the exact commands, what goes wrong and what the settings mean | Yes |
| `updates/` | The update check as a package (`python -m … updates`), with its `WORKFLOW.md`: how to run a check, how to read `changes.md`, how to crawl the delta. Until developed, a stub that records where the portal shows changes | Yes |
| `sources.yaml` | The registry's general part: header, portals, crawl settings, the title rule, search terms. Data, not code | Yes |
| `links/` | `seed_laws.yaml` (hand-edited: the laws named on purpose, with provenance) beside the generated link list (`documents.jsonl`, `documents.csv`, `laws.csv`, `catalogue_meta.json`, `discovery_log.jsonl`, never hand-edited). `README.md` says which is which and how to rebuild | Yes |
| `NOTES.md` | The general note, in the fixed layout below | Yes |
| `tests/` | Offline tests against saved portal pages, and `fixtures/` with each page listed by source URL and date. `README.md` says what is tested and what still needs a test | Yes |

**`NOTES.md` layout.** The same numbered sections in every country, so a reader finds the same thing in the same
place. A section with nothing in it yet says so.

| Section | What it answers |
| :---- | :---- |
| 1. The website | 1.1 the sites and hosts used, robots.txt and the delay; 1.2 what the portal looks like: listings, detail pages, file addresses, what each carries; 1.3 what to watch for: quirks, failures, files that are not the text |
| 2. How our scraper works | 2.1 the big picture (the diagram of section 2 above, with this country's figures); 2.2 the code; 2.3 what goes into the link list; 2.4 politeness; 2.5 what the engine must change; 2.6 the update check |
| 3. Runs | One row per run and corpus under `outputs/<CC>/`, with what each is and its result |
| 4. Output format against `CONTRACT.md` | Column by column: where the value comes from on this portal |
| 5. Open choices for the developer | With what to weigh |
| 6. Known gaps | |
| 7. Round 1 corpus, against the portal | What the frozen corpus holds and how it differs |
| 8. Dead ends | Tried, failed, dated |
| 9. Evaluation only | Counts over the gold set, never a seed |
| 10. Files, hand-back and evidence | Every file with its repo counterpart; the hand-back list; what backs the note |

## 5. Rules that do not move

1. **Politeness.** At least 3 s between requests plus jitter, and the host's `Crawl-delay` when it is longer (6 s on
   SSO, 10 s on the Federal Register); one request at a time per host; never two processes against one host at
   once (`POLICY.md` section 5, decision 6). A list build and a crawl never overlap.
   **When a portal refuses us, rest and slow down; do not stop** (decision 23): a minute, then five, then half an
   hour, with the delay doubled each time up to a minute between requests, and a stop only after six refusals in a
   row. The shared paced client does this for every catalogue step and update check.
2. **robots.txt** is read before the first request to a host and recorded with the date. A 5xx answer is a
   decision, recorded per portal (decision 9 for Laws of Malaysia).
3. **Work on the copies in `countries/`.** The repo (`rdtii-rocky-finale`), the instrument files and the Round 1
   corpus (`pipeline-data\…\handoff1_v2`) are not edited; the Round 1 corpus is not read as an input either. Hand
   back later, per `countries/README.md`. Commit only when asked.
4. **Never write into an earlier run folder.** One run, one folder; the two exceptions are in `outputs/README.md`
   rule 1. A retry is a new run. A corpus is a new folder.
5. **Read every act's detail page at the first stage** (section 1). The cost is paid once per list build, and the
   update check touches only the changed acts.
6. **Flag, do not fix.** A stored file that is not the law's text is flagged by the audit and left as served. The
   flags travel into the corpus. Nobody substitutes a file by hand.
7. **Generated files are never hand-edited:** link lists, manifests, audits, corpora. Fix the settings or the code
   and regenerate.
8. **The gold set is never a seed,** and no source code goes into `notes/`.
9. **A change to `sources.yaml` or the seeds invalidates the link list.** Rebuild it; the crawl refuses a stale one.
10. **Every claim in a note comes from a file** the note names: a log, a manifest, a list, an audit.
11. **Every update says what it cannot see** (the developer's rule of 2026-09-21). No economy's evidence sits on
    one website: regulators publish their own codes and circulars, customs and trade bodies publish lists,
    ministries are created and renamed, and portals move or start refusing us. An update check that re-reads the
    main database sees none of that. So each country keeps **`updates/watchlist.tsv`** — every source the update
    check does not collect, with what to look for there — and **every update check prints it before it runs and
    again when it finishes.** A check is not a complete update until those sources have been looked at by hand.
    The shared helper is `my-malaysia/scraper/watchlist.py`, which never raises and never fails a check; record a
    source as looked at with `python countries/my-malaysia/scraper/watchlist.py <list> --checked <name>`. China,
    which has no engine package, keeps `cn-china/watchlist.tsv` and prints it from its own collector.
    **Add a row** whenever a new publisher, list or category turns up. **Promote a row** to automatic collection
    only once its host is shown to permit us.
    **Not every external source is equal** (the developer's note of 2026-09-21). Some serve many indicators —
    China's CAC serves 16 — and some serve exactly one: China's SASAC answers 5.3 and nothing else, SAFE 12.4.2,
    MOFCOM's trade-remedy bureau 1.4. So every row carries **`breadth`** — `multiple`, `single` or `unconfirmed` —
    and says in `breadth_basis` whether it was measured from a per-document checklist or estimated from the
    source's category. It sets priority, not membership: check and automate the many-indicator sources first; keep
    every one-indicator source, because it may be the only place its indicator's answer lives. When a live test
    draws an indicator, list its sources with `--indicator <id>`, which separates the sources **dedicated** to that
    indicator from the general indexes that may carry it.
12. **A document collected by hand must still be machine-readable** (2026-09-22). Where a host refuses our client
    and the developer saves pages in a browser, the file has to carry a **text layer**: extraction reads text, not
    pictures of it. Save with the **browser's own "Save as PDF"**, or Ctrl+S as **`.mhtml`**. Do **not** print
    through the **"Microsoft Print to PDF"** printer — on Windows it converts CJK glyphs to vector outlines, and
    the result looks perfect, carries no fonts, no text blocks and about a thousand drawn curves a page, and
    yields nothing to any parser. It cost 18 MIIT documents a second pass. **Check the first file of any batch**:
    `python countries/cn-china/tools/checkdocs.py <folder>` reports the text layer, page count and characters for
    every file in a folder, and exits non-zero if one is unreadable. **And take the attachment**: on ministry sites
    the page is often a wrapper and the law is in the 附件 — MIIT's 无线电频率划分规定 page runs 2 pages, its `.doc`
    runs 230.

13. **A source that refuses us is updated by a person, and the tool's job is to prepare that walk**
    (2026-09-22). Where a host serves us, the update check re-reads its index and diffs it. Where a host refuses
    an honest client — MIIT's 403, Customs' 412 — **nothing automatic will ever report that one of its rules was
    amended or repealed**, and no amount of tooling changes that. This is a standing weakness of any corpus that
    contains such a source, so it is marked rather than hidden:
    - **Every document collected by hand carries `update_check` in its `provenance.tsv`**, saying how it must be
      re-checked and why no tool can do it.
    - **The update check ends by counting the documents it did not cover** and rebuilding the worklist for them.
    - **The worklist gives the exact address of every document held** — not the site, not the section, the page —
      with the version date we hold, so the check is a comparison and not a search. China's is
      `tools/manual_check.py`, writing `MANUAL_UPDATE_CHECK.md` into the collection; it asks three questions per
      source: is anything **new**, is anything shown with a **later version date**, is anything marked
      **repealed**. A held document with no address is reported as a defect, because it cannot be checked at all.
    - A completed walk is recorded as a date on the watch list (rule 11). **A superseded text is kept beside the
      new one, never overwritten** (rule 6).
14. **The customs and tariff source stays manual in every economy, by decision** (the developer, 2026-09-22).
    Tariff schedules, de minimis thresholds and cross-border e-commerce notices answer a small, known set of
    indicators — **1.4, 12.2, 12.5 and 12.6** — and they are the least automatable material in the whole
    instrument: mostly not legislation at all, published as annexes, HS-code schedules, PDFs and announcements, in
    a different shape in every economy, and often behind a search-only interface. Writing and maintaining six
    parsers to recover four indicators is not worth it, and a schedule parsed wrongly is worse than one read by a
    person. So **no country automates its customs source.** Instead:
    - every country's `updates/watchlist.tsv` carries its customs authority with **the exact page** for the tariff
      schedule and for the de minimis threshold, not just the homepage;
    - when one of those indicators is scored, the researcher is handed **the link**, reads the figure and
      **records the figure, the page and the date read**, so a hand-read number is still evidence somebody else
      can check;
    - the addresses are verified when the row is written, and a row whose address could not be verified says so.

    This is a deliberate limit on the crawler's scope, not an oversight, and it is the one place where "a
    researcher will look" is the designed answer rather than a fallback.

## 6. Where each country stands, 2026-09-22

| Country | Link list | Crawl | Audit | Run notes | Update check | Corpus | Law table | Tests | Notes layout |
| :---- | :---- | :---- | :---- | :---- | :---- | :---- | :---- | :---- | :---- |
| Malaysia (`MY`) | Yes (`scraper/catalogue.py`; rebuilt with `timeline: all` on 2026-09-15: 1,414 documents) | 2 crawls, 2 delta crawls | All 4 crawls audited | All 5 runs | Yes (`updates/`, 3 live checks, two with their delta crawls; `--list` after a rebuild) | `MY_corpus_2026-09-15`, 1,391 documents | Yes, on the corpus (1,441 rows with `--all`) | 175 offline as pytest collects them, plus 22 for the tools | Yes |
| Singapore (`SG`) | Yes since 2026-09-15 (`scraper/catalogue.py`, run once: 1,041 documents; decision 18). The portal's WAF challenges the plain client, so a rebuild waits for a browser transport (`NOTES.md` 1.3) | `SG_ws_2026-09-15`, the first crawl from the list: 739 documents in 15 stretches over 24 hours, 15 September to 16 September | Yes, `RULES["SG"]` since 2026-09-16: 27 flagged of 738, none a wrong file | `SG_ws_2026-09-15` | **Yes** (`updates/`, built 2026-09-16: from a date, amendments by the timeline's in-force date; first live run refused with HTTP 403) | `SG_corpus_2026-09-16`, 738 documents | Yes, on the run and the corpus (1,072 rows with `--all`) | 36 offline | Yes |
| Australia (`AU`) | Yes since 2026-09-15 (`scraper/catalogue.py`: the register's API only, 1,277 documents; decision 18) | `AU_ws_2026-09-15`, the first crawl from the list: 1,277 of 1,277 stored, 12:33 to 17:00 UTC at 10 s; 1 delta crawl | Yes, `RULES["AU"]` since 2026-09-16: 91 flagged of 1,277, 88 of them whole short Acts | Both runs | **Yes** (`updates/`, built and run 2026-09-16: 3 requests check 4,772 titles) | `AU_corpus_2026-09-16`, 1,277 documents | Yes, on the corpus (1,277 rows) | 33 offline, plus Round 1's 9 | Yes |
| Timor-Leste (`TL`) | Yes since 2026-09-20 (`scraper/catalogue.py`: six category pages, 7 requests, 4,788 acts -> 1,953 documents) | `TL_ws_2026-09-20`, the first crawl: **1,935 of 1,953 stored**, 3.9 GB, 06:27 to 14:52 UTC at the portal's `Crawl-delay: 10`, with one resume | Yes, `RULES["TL"]`: 160 flagged of 1,935, 17 missing | `TL_ws_2026-09-20` | **Yes** (`updates/`, built 2026-09-20, **run live 2026-09-22**: 7 requests. The first run exposed an address-comparison defect, fixed the same day; the corrected check found 16 documents to fetch) | `TL_corpus_2026-09-20`, 1,921 documents | Yes, on the run (4,707 acts covered) | 36 offline | Yes |
| Lao PDR (`LA`) | Yes since 2026-09-20, rebuilt 2026-09-21 (`scraper/catalogue.py`: every listing, `old=0` and `old=1`, 193 requests: 1,773 laws -> 1,824 documents) | `LA_ws_2026-09-21`, the first crawl: 1,811 of 1,824 stored in 5 h at 6 s, no refusal | Generic flags only: **`RULES["LA"]` not written** | Both runs | **Yes** (`updates/`, built 2026-09-20, **run live twice on 2026-09-21**: 193 requests each) | `LA_corpus_2026-09-21` | Yes, on the run and the corpus (`scraper/checker.py`) | 60 offline, 1 expected failure (a pending engine change) | Yes |
| China (`CN`) | **Not an engine adapter** — the NPC database forbids crawling. Layer 1: a hand-downloaded export, indexed offline (`tools/layer1.py`: 945 documents). Layer 2: CAC's index (`tools/collect.py`, 111) | `CN_ws_2026-09-21`, CAC: 111 of 111. Layer 1 by hand, 2026-09-21 | **No** — no `RULES["CN"]` and no engine manifest | All three runs | **Yes** (`tools/update.py`, built and **run live 2026-09-22**: 12 requests, nothing changed) | `CN_sources_2026-09-21`, one folder per source; twelve sources in `_deferred/` | **No** — `index.csv` carries each document's version date | 51 offline | Yes, since 2026-09-22, with `SOURCES.md` (source selection) and `WORKFLOW.md` beside it |

**Test counts in this table were measured in a clean sandbox on 2026-09-22**, built from the repo's stage and each country's install step (the workshop audit, `notes/WORKSHOP_AUDIT_2026-09-22.md`).

Malaysia, Singapore and Australia have every step: a link list, a crawl, an audit, a run note, a corpus, a law
table and an update check that has run live. **Timor-Leste is the fourth country** (2026-09-20) and **Lao PDR the
fifth** (2026-09-21) — Lao PDR the first whose update check ran live on the day its first crawl finished. What is
left:

- **Timor-Leste's 16-document delta** (`outputs/TL/TL_ws_2026-09-22_to_2026-09-22`) waits to be crawled, in a sandbox that carries the engine changes Timor-Leste needs.
- **`tools/audit_run.py` has no `RULES["LA"]`**, so Lao PDR's audit applies generic flags only. On a portal where
  93.6% of the documents are scans that means `no_text_layer` on 1,697 of 1,811 rows — a count of the corpus
  rather than a finding — and nothing marks the 116 documents that carry native text and need no OCR.
- **Lao PDR departs from rule 5** (read every act's detail page) on measured evidence, and `DECISIONS.md` has no
  Lao entry to authorise it. It needs the developer's ruling, not a scraper change.
- **Two defects in shared code**, found by Lao PDR and written out in full in `countries/la-lao-pdr/NOTES.md`
  under "Shared-file edits still to make". Neither is applied, because both touch code four countries import:
  `catalogue._cell` collapses whitespace inside a URL (42 Lao filenames carry a double space), and
  `tools/merge_corpus.py` `identity()` ignores language, so 53 English translations were superseded out of the
  Lao corpus.
Their `scraper/WORKFLOW.md` and `updates/WORKFLOW.md` say what runs today and what does not.

## 7. Adding a country

1. Copy `countries/_template/` to `countries/<cc>-<name>/`.
2. Read robots.txt on every host, record it in `NOTES.md` 1.1 with the date and the delay to use.
3. Fill `sources.yaml` (header first) and `links/seed_laws.yaml` with provenance for every seed.
4. Write the adapter in `scraper/` with its catalogue step; write `scraper/WORKFLOW.md` as you go.
5. Build the link list; read `laws.csv` and the console notes before crawling.
6. Crawl into `outputs/<CC>/<CC>_ws_<date>/`; audit; write the run note; add `outputs/<CC>/README.md`.
7. Write `updates/` on the facts in `NOTES.md` 1.2, with its `WORKFLOW.md`; run the first check. **Fill
   `updates/watchlist.tsv`** (rule 11): every regulator `sources.yaml` names but does not crawl, every category of
   the portal the scraper does not read, the customs, tariff and trade-list publishers, and any body the source
   research names that the registry does not. End `__main__.py` with the `_remind` hook the five built countries
   use, so the list is printed before and after every check.
8. Save fixtures, write the tests, list them in `tests/README.md`.
9. Add the country's rules to `tools/audit_run.py`, a row to section 6 above, a row to `outputs/README.md`, and the
   hand-back rows to `countries/README.md`.
