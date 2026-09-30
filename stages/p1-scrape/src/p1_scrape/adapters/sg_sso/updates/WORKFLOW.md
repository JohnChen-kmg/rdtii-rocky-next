# Workflow: fetching only what changed since a date (Singapore)

**Built 2026-09-16** (decision 22), on the logic the developer settled that day: take a date, find everything on
the portal that changed on or after it, scrape what is new or amended, and report what was repealed. It has the
shape Malaysia's and Australia's checks have (`../../my-malaysia/updates/WORKFLOW.md`,
`../../au-australia/updates/WORKFLOW.md`).

**It has run live.** Its first three runs, on 2026-09-16, were refused because the check sent a bare fallback
User-Agent (section 8); the fourth, on 2026-09-17 with the configured one, read the portal in 22 requests and found
nothing changed since 2026-09-15. The logic is also tested offline on saved pages (`../tests/test_sg_updates.py`).

Every command runs from the **stage root** in Git Bash, through the `subst` drive (`../scraper/WORKFLOW.md`,
step 3). `<ws>` is this workshop.

## 0. Before you start

- **Politeness:** `REQUEST_DELAY_MS=10000`. robots.txt asks for 6 s and forbids `/search`; the check reads robots
  first and never goes below the stated delay.
- **The portal's edge refuses a plain client after sustained access:** a challenge (HTTP 202) after roughly 130
  requests, and on 2026-09-16 a refusal (HTTP 403) on a check's second request, seven hours after a 24-hour crawl.
  **The client now rests and slows down on its own** (decision 23), so a check can take much longer than its request
  count suggests: run it in the background. Never run one against the portal while a crawl is running.
- The scraper package must be installed with its `updates/` subpackage (`../scraper/WORKFLOW.md`, step 1).

## 1. Run the check

```
PYTHONPATH=src python -m p1_scrape.adapters.sg_sso.updates \
    --outputs R:/outputs/SG \
    --registry $WS/sources.yaml --seeds $WS/links/seed_laws.yaml
```

- **The date** is the day the baseline's list was built, or `--since YYYY-MM-DD`. The baseline is the newest run
  under `--outputs` with a `links_used/laws.csv`, or the run `--baseline` names. With no baseline and only a date,
  an act counts as amended when its newest in-force date falls on or after that date.
- **`--max-timelines N`** (default 60): how many act timelines one check may read. The rest are reported as
  `not_checked`, never dropped; run again to read them.
- **`--no-seed-regulations`**: skip the seed acts' regulations tabs (about one request each, eight seed acts today).
- **The run folder** is `<outputs>/SG_ws_<since>_to_<today>`, `_2`, `_3` when taken.

## 2. What it reads, and what it costs

| What | Requests |
| :---- | ----: |
| robots.txt | 1 |
| The Current listing, 100 rows a page by its Next Page links (525 acts) | 6 |
| The Repealed (298) and Uncommenced (10) listings, the same way | 4 |
| The Acts Supplement of this year and last | 2 |
| The timeline of every new act, and of every act whose file is newer than the date, up to the cap | 1 each |
| The regulations tab of each seed act | 1 each |

**A monthly check is roughly 30 to 60 requests.** The Current listing's file stamps showed 19 to 79 regenerated
files a month through 2026; a check from 1 September would read 28 timelines, from 15 August 58.

## 3. How it decides

| Found | Rule | Result |
| :---- | :---- | :---- |
| An act on the Current listing the baseline did not hold | | `new_act`, fetched. If the baseline held it as uncommenced, the note says it commenced |
| An Acts Supplement entry the baseline did not carry | published on or after the date | `new_publication`, fetched as published |
| A Repealed listing entry | repealed on or after the date, or an act the baseline held as current | `repealed`, **reported, not fetched** |
| An act whose file stamp is on or after the date | its timeline is read | `amended` when the newest in-force date is later than the one recorded, fetched; `amended_file_pending` when that version has no file yet, reported; `regenerated` when the date did not move, recorded |
| A regulation on a seed act's tab | not in the baseline, dated on or after the date; or recorded, with a later date | `new_regulation` or `amended`, fetched |

**An amendment is decided by the in-force date on the act's own timeline, never by a publication date.** An
amending act is often published long before it takes effect: Act 40 of 2020 was published in December 2020 and
amended the Personal Data Protection Act from October 2022; the Online Criminal Harms Act's version of
15 September 2026 comes from Act 10 of 2025, published in March 2025. A check comparing publication dates would
have called both unchanged.

**The file stamp only chooses which timelines to read.** The Current listing carries, for each act, the time the
portal last generated its file. It is not a legal date: it matches the version date on 5 of 458 acts, because files
are regenerated without any change in the law. But a new version always makes a new file, so an act whose file is
older than the date cannot have been amended, and its timeline is not read. Seeds are read first, then the acts
the title rule selects, then the most recently regenerated.

## 4. What it writes

| File | What it holds |
| :---- | :---- |
| `changes.json`, `changes.md` | Every decision above, with in-force dates, the instrument that amended each act, repeal dates, and what the cap left unchecked |
| `links_used/documents.jsonl`, `documents.csv` | The documents to fetch, built by the adapter's own row builders; each row's `contract_meta.update` says what changed and what the baseline held |
| `links_used/laws.csv` | **Every listed act**, not only the changed ones. An act whose timeline was read carries the fresh version date; every other act keeps the baseline's. So this run folder is a complete baseline for the next check, and checks chain without a full list rebuild |
| `links_used/catalogue_meta.json`, `discovery_log.jsonl` | The settings and fingerprint the crawl checks, and every request the check sent |

## 5. Crawl the delta list

The check prints the command:

```
REQUEST_DELAY_MS=10000 SSO_FRONTIER=links_file \
    SSO_LINKS_FILE=R:/outputs/SG/SG_ws_<since>_to_<date>/links_used/documents.jsonl \
    python scrape.py --economy SG --scope all --out R:/outputs/SG/SG_ws_<since>_to_<date>
```

Then steps 4 to 7 of `../scraper/WORKFLOW.md`: validate, audit, law table, run note, and the corpus.

## 6. What it cannot see

Written here so nobody discovers it later:

- **A new version whose file the portal has not generated yet** keeps an old file stamp, so its timeline is not
  read until the file appears. The Online Criminal Harms Act's version of 15 September 2026 was such a case.
  Nothing could be fetched for it before then, unless the markup fallback is built.
- **A correction or republication** that does not regenerate the file.
- **New regulations under an act that is not a seed**: those tabs are not read.
- The remedy for all three is an occasional full sweep of every act's timeline, about 525 requests, which needs
  either a browser transport or a day of rest-and-resume cycles.

## 7. Things that go wrong

| Symptom | Cause | What to do |
| :---- | :---- | :---- |
| The check is refused while single requests load | It is not sending the configured User-Agent (the bug of 2026-09-16) | The first line of the check must say `identified as '... contact: ...'`; run it from the stage root so `config.settings` loads |
| The portal refuses (HTTP 403, 429, 467, 503, or a WAF challenge) | Its anti-scraping mechanism | Nothing to do: the client rests (1, 5, then 30 min), halves its speed each time and carries on (decision 23). It stops only after six refusals in a row; then rest for hours and run once more |
| `the portal could not be read: … throttling … after resting` (exit 2) | Six refusals in a row, about two hours of resting | Nothing was written. Rest for hours and run the check once. Do not loop it |
| `challenged the check and it stopped reading` in the notes | HTTP 202 with `x-amzn-waf-action: challenge` partway through the timelines | What it found is written; the acts it did not reach are `not_checked`. Rest 45 minutes, run again |
| Many `not_checked` | The period is long, so more files were regenerated than the cap | Run again after a rest, or check a shorter period with `--since` |
| An act keeps showing `amended_file_pending` | The portal still has no file for its newest version | Expected until the file appears; the next check fetches it |
| `no date to check from` | No run with a list under `--outputs` | Pass `--since`, or build a list first (`../scraper/WORKFLOW.md`, step 2) |

## 8. When to check, and when to rebuild instead

**Agreed with the developer on 2026-09-16:** the update check is the routine, run about monthly; a full rebuild of
the list and a crawl is the safety sweep, run about once a quarter. The reason is the portal, not the code.

| | Full rebuild and crawl | Update check |
| :---- | :---- | :---- |
| Requests | About 1,570: 540 to rebuild the list (every act's page), about 1,030 to fetch 743 documents | About 50 to 130: 12 listing pages, the timelines of acts whose files changed (19 to 79 a month), 8 regulations tabs, then only the changed documents |
| Time, on the evidence of 15 and 16 September | 1 to 2 days: the list build was challenged after 45 minutes, the crawl took 24 hours in 15 stretches | An hour or two, rests included |
| Load on a portal that refuses sustained access | Heavy: the traffic that triggered the blocks | Light |

Re-scraping everything is simpler, not quicker, and it is the approach most likely to be refused.

### The flaws of the update check, stated plainly

1. **Its baseline has gaps.** In `SG_ws_2026-09-15`, **50 of the 525 current acts have no recorded version date**,
   because the portal challenged their pages while the list was built on 2026-09-15. For those acts the check can
   only compare the newest in-force date with the check's own date. A version that took effect after the list was
   built but before that date is called `regenerated` and missed. Those 50 acts are also read only when their file
   was regenerated after the date.
2. **Checks chain, and so do their gaps.** Each check carries forward every act it did not re-read, at the
   baseline's version date (`links_used/laws.csv`). That is what lets checks run without a rebuild, and it is also
   why a gap in one baseline survives every check that follows until a rebuild refreshes it.
3. **Three changes it cannot see at all** (section 6): a new version whose file is not generated yet, a correction
   that does not regenerate the file, and new regulations under acts that are not seeds.
4. **The file-stamp filter trusts the portal's own behaviour.** It rests on one observed rule, that a new version
   always makes a new file. Every act seen on 2026-09-15 and 16 followed it except the one whose new version had no
   file at all. If the portal ever publishes a new version against an old file, the check would not read that
   act's timeline.

The quarterly rebuild is the remedy for all four: it re-reads every act's page, so every version date is fresh and
every gap closes. It is the heavy operation; run it in rested cycles (`../scraper/WORKFLOW.md`, step 3), or with a
browser transport, which would cut it to about 90 minutes.

### The first live runs

- **2026-09-16 21:29 UTC**, the check as first built: robots.txt answered normally, then **HTTP 403 on the Current
  listing**, its second request. It stopped and wrote nothing. No timeline was reached, and timeline pages
  themselves were loading normally that afternoon (the Online Criminal Harms Act's page at 17:01 UTC).
- **2026-09-16 21:39 UTC**, rerun under decision 23, which rests and slows down on a refusal instead of stopping,
  at 15 s between requests. It ran for more than an hour silently, because it reported only at the end; that flaw
  is fixed (the client now prints each rest, and the check prints each phase). Its result is recorded in
  `../NOTES.md` section 3 once it ends.
- **It gave up before 23:45 UTC without reading anything:** HTTP 403 seven times in a row on the 500-row Current listing,
  after 126 minutes of rests at up to 60 s a request.
- **23:45 to 23:53 UTC, one request at a time:** an act page, the Current listing at 100 rows, and its second page by
  path all answered 200 (`../NOTES.md` 1.3). The listing is now read 100 rows a page by its Next Page links.
- **2026-09-17 00:00 to 02:04 UTC**, the check with 100-row paging: **the same seven 403s, on the 100-row page** a
  probe had loaded. So the page size was not the cause. The difference was the User-Agent: the probes, the list build
  and the crawl send the configured one with its contact address; the check sent the adapter's bare fallback. Fixed
  2026-09-17; the check prints the identity it uses on its first line.
- **2026-09-17 02:35 to 02:54 UTC**, with the configured User-Agent, after a 30-minute rest: **every request
  answered**, 22 in all (one HTTP 503 rested a minute and retried). Nothing changed since 2026-09-15, 0 timelines
  to read, 0 documents (`outputs/SG/SG_ws_2026-09-15_to_2026-09-16/RUN_NOTE.md`).
