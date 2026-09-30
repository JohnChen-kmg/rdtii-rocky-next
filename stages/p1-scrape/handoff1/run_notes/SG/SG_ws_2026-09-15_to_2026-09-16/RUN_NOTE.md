# Run note: SG_ws_2026-09-15_to_2026-09-16

Singapore, **the first update check that could read the portal**: what Statutes Online changed since 15 September
2026, the day the list of `SG_ws_2026-09-15` was built.

## Read this first

- **Nothing changed.** No new act, no act on the Acts Supplement that the baseline did not carry, no repeal, no new
  regulation under a seed act, and no act whose file was regenerated on or after 15 September, so no timeline needed
  reading. **0 documents to crawl**; this folder is the record of the check.
- **22 requests, every one answered.** One HTTP 503 on the Trade Marks Act's regulations tab; the client rested a
  minute and the retry answered 200 (decision 23).
- **Three checks before this one were refused** (HTTP 403 on every listing request, 2026-09-16 21:29 UTC to
  2026-09-17 02:04 UTC). The check was sending a bare fallback User-Agent without the contact address; the list
  build, the crawl and single probes send the configured one and were not refused. Fixed before this run, which
  printed its identity on its first line (`countries/sg-singapore/NOTES.md` 1.3).
- **One kind of change this check cannot see is known to be pending:** the Online Criminal Harms Act's version in
  force from 15 September 2026 had no file on the portal on 16 September, so its file stamp did not move and its
  timeline was not read (`countries/sg-singapore/updates/WORKFLOW.md` sections 6 and 8). It will show as `amended`
  once the portal generates the file.

## At a glance

| | |
| :---- | :---- |
| Country | Singapore (`SG`) |
| Run type | Update check against `SG_ws_2026-09-15` (since 2026-09-15), no crawl |
| Time, UTC | 2026-09-17 02:35:52 to 02:54:16, after a 30-minute rest |
| Time, machine clock | US Eastern Daylight Time, UTC−4: 2026-09-16 22:35 to 22:54, hence `_to_2026-09-16` in the folder name |
| Pace | `REQUEST_DELAY_MS=15000`, plus jitter and page time: requests 19 s to 100 s apart |
| Identity | The stage's configured User-Agent, with its contact address |
| Listings read | Current 525 (6 pages of 100), Repealed 298 (3 pages), Uncommenced (1 page), Acts Supplement 2026 and 2025, 44 entries |
| Timelines read | 0 (no act's file stamp on or after 2026-09-15) |
| Regulations tabs | The 8 seed acts; nothing new. The Income Tax Act lists 774, of which the first 100 are read (`sso.subsidiary_max_per_act`) |
| Result | `changes.json`: no changes |

## Files

| File | What it holds |
| :---- | :---- |
| `changes.json`, `changes.md` | The check's decisions: none, and the one note |
| `links_used/laws.csv` | All 877 listed laws, each act at the baseline's version date (nothing was re-read). A complete baseline for the next check |
| `links_used/documents.jsonl`, `documents.csv` | The delta list: empty |
| `links_used/catalogue_meta.json`, `discovery_log.jsonl` | The settings and registry fingerprint, and all 22 requests with their times and statuses |

## Issues

1. **The baseline's gap is carried forward.** 50 of the 525 current acts have no recorded version date in
   `SG_ws_2026-09-15`; this check re-read none of them, so they still have none (`updates/WORKFLOW.md` section 8,
   flaw 1). The quarterly rebuild closes it.
2. **The Online Criminal Harms Act** (above): expected `amended_file_pending` until the portal publishes the file.
