# Run note: MY_ws_2026-09-14_to_2026-09-14

Malaysia, web scraping, 14 September 2026: an **update check** covering 2026-09-14 (the morning's crawl) to
2026-09-14 (this check), the first live run of
`countries/my-malaysia/updates/`. It read the Laws of Malaysia listings and compared them with the crawl of the same
morning (`MY_ws_2026-09-14`). No document was fetched, because nothing needed fetching.

## Read this first

- **This run holds no documents.** It is the record of a check: what the portal listed at 22:08 UTC, what had
  changed since the crawl, and the (empty) list the crawl would have used.
- **One change was found:** P.U. (B) 335/2026, a notice published on 14 September that no amending act cites. It is
  recorded in `changes.md`, not fetched.
- **The current corpus is `MY_corpus_2026-09-15`** (since 2026-09-15; on the day of this check it was `MY_ws_2026-09-14`).

## At a glance

| | |
| :---- | :---- |
| Country | Malaysia (`MY`) |
| Run type | Update check against `MY_ws_2026-09-14`, since 2026-09-14 (baseline mode). No crawl followed: the delta list is empty |
| Date | 2026-09-14 |
| Time, UTC | 22:07:35 to 22:08:28 (the 10 requests); files written 22:08:33 (`links_used/`) and 22:08:37 (`changes.json`, `changes.md`) |
| Time, machine clock | US Eastern Daylight Time, UTC−4: 18:07 to 18:08 |
| Result | Listings: 885 principal acts, 406 amendment rows (402 acts), unchanged. P.U. (A): 100 newest read of 7,306, none since the date. P.U. (B): 100 newest read of 9,150, 1 since the date. **0 documents to fetch** |
| Size | Nothing stored |
| Validation | Not applicable: no manifest. The delta list carries the registry fingerprint (`cfg_sha256` b12494e6…), the same as `countries/my-malaysia/links/` |
| Checked | Figures below come from `links_used/discovery_log.jsonl`, `links_used/catalogue_meta.json` and `changes.json` |

## Steps and times

| Step | UTC | Requests | Output |
| :---- | :---- | :---- | :---- |
| 1. Update check | 22:07:35 to 22:08:28 | 10 to lom, every gap at least 3.0 s (waits 3.0 to 4.3 s): robots.txt (HTTP 500); the updated-acts page and 2 POSTs (885 records); the amendment page and 1 POST (406 rows); the P.U. (A) page and 1 POST (100 newest); the P.U. (B) page and 1 POST (100 newest). No document | `links_used/` (an empty delta list, with `laws.csv` for every act), `changes.json`, `changes.md` |
| 2. Crawl | not run | | nothing to fetch |

## How it was run

- **Engine:** the Round 1 crawl engine in the sandbox copy `scratchpad\sbx2\p1-scrape`, with the workshop's
  `countries/my-malaysia/scraper/` installed as `src/p1_scrape/adapters/my_gazette/` and `updates/` as its
  `updates/` subpackage. The crawl engine itself was not used: the check sends its own paced requests.
- **Registry:** `countries/my-malaysia/sources.yaml` (with the new `updates:` block) and
  `countries/my-malaysia/links/seed_laws.yaml`.
- **Baseline:** the runs under `outputs\MY\`: listing state from `MY_ws_2026-09-14\links_rebuilt\laws.csv`, stored
  documents from both runs' manifests (1,311 distinct URLs). `since` = the day `MY_ws_2026-09-14` started.
- **Politeness:** `REQUEST_DELAY_MS` 3000 plus jitter, one request at a time, every request logged with its wait.
- **Command** (from `<sandbox>`):

  ```
  PYTHONPATH=src python -m p1_scrape.adapters.my_gazette.updates \
      --outputs <workspace>/outputs/MY \
      --registry <workspace>/countries/my-malaysia/sources.yaml \
      --seeds <workspace>/countries/my-malaysia/links/seed_laws.yaml \
      --out <workspace>/outputs/MY/MY_ws_2026-09-14_to_2026-09-14
  ```

## What is in this folder

| Path | What it is |
| :---- | :---- |
| `RUN_NOTE.md` | This note |
| `changes.md`, `changes.json` | Every change found since 2026-09-14, fetched or not, with the reason |
| `links_used/documents.jsonl`, `documents.csv` | The delta list the crawl would replay: empty |
| `links_used/laws.csv` | One row per act the portal lists (1,287): 1,242 "unchanged since MY_ws_2026-09-14", 45 "the portal offers no document" |
| `links_used/catalogue_meta.json` | The check's settings, request count, robots.txt record, listing counts, and `delta`: since, mode, baseline runs, change summary |
| `links_used/discovery_log.jsonl` | The 10 requests, with their times and waits |
| `logs/update_check.log` | The console output |

## What is stored

Nothing. No document was fetched.

## What is missing

1. **Nothing to fetch.** Every principal act's file, as-at date and status marker, and every amending act's file and
   remark, were as the morning crawl's list recorded them.
2. **Recorded, not fetched:** P.U. (B) 335/2026 (Appointment of Assistant Registrar of Fishermen's Associations,
   published 14 September 2026, under Act 44). A P.U. (B) notice is fetched only when an amending act's remark cites
   it as a commencement order, or a seed names it.
3. **What the check cannot see:** a file replaced behind the same path with the same as-at date. `--verify-stored N`
   sends conditional requests for stored files and was not used here. Act 869 is such a case, but not for this
   check: its file was replaced on 21 August 2026, before the morning crawl, which stored the new bytes.
4. **Not retried:** the 4 files that answered HTTP 500 in the morning crawl (Acts 175, 150, A1740, A1626). The code
   of this check compared listings only; the revised code (below) reports a listed file that no run stored as
   `not_stored` and fetches it.

## Issues encountered

1. **lom's robots.txt answered HTTP 500** (22:07:35 UTC), as on every earlier read. Crawled under decision 9.
2. **First live run of the update module.** The code had passed 24 offline tests against the fake portal; this check
   was the first against lom, and behaved as the tests describe: listings read once, P.U. listings read newest first
   and stopped at the first page older than the date, no document requested.
3. **Two runs on one day.** The folder was first named `MY_ws_2026-09-14_2`; it was renamed for the period it covers
   (below).

## Changes after the run

- 2026-09-14: `logs/update_check.log` copied in from the session scratchpad. That log and `catalogue_meta.json` still
  name the folder `MY_ws_2026-09-14_2`.
- 2026-09-14: renamed from `MY_ws_2026-09-14_2` to `MY_ws_2026-09-14_to_2026-09-14`, on the developer's instruction:
  an update check's folder is named for the period it covers (`outputs/README.md`).
- 2026-09-14, after three reviews, the module was revised; this folder is unchanged. A check now sends 8 requests
  (the P.U. pages are not read: the act lists' key is reused), reads the P.U. lists 120 days back, reports listed
  files that no run stored as `not_stored`, fetches a new commencement order only under the same rule as the full
  build, never turns a conditional HEAD into a download, and stops on an incomplete listing.
- 2026-09-15: the second check, `MY_ws_2026-09-14_to_2026-09-15`, took this run's listing state as its baseline; the
  runs were merged into `MY_corpus_2026-09-15` (decision 17). This folder is unchanged.

## Decisions still open that affect this run

- Whether a check that fetches nothing should get a run folder at all (decision 16 says yes: a check is a run).
- Whether P.U. (B) notices under core acts should be fetched (decision 12 widens or not).
