# Run note: LA_ws_2026-09-21_to_2026-09-21

Lao PDR, **the first update check**, 21 September 2026, run three minutes after the first crawl finished. It
read the whole portal again and compared it with `LA_ws_2026-09-21`. **No document was crawled from this
check's delta list**, and the reason is the point of this note.

## Read this first

- **The check works. Its first answer did not.** It reported 46 laws whose file had moved. **42 of those 46
  were false**, and the fault was ours, in the census the check compared against — not in the portal and not in
  the comparison.
- **`laws.csv` had a corrupted copy of 46 addresses.** The shared CSV writer puts every cell through
  `re.sub(r"\s+", " ", …)` so a cell stays on one line. That is right for a title and wrong for a URL: **42 of
  this portal's filenames contain two consecutive spaces** — `law on foreign exchange management  (Amended)
  No 15 - NA.pdf` — and the census wrote them as one. The check read today's real address against yesterday's
  flattened one and concluded the file had moved.
- **Nothing was ever fetched from a wrong address.** `documents.jsonl` and `manifest.jsonl` both carry the real
  two-space address, and all 46 documents are stored and validate. Only the census was wrong, and only in the
  column the check compares on.
- **This folder is kept as the record of what the portal listed on 2026-09-21**, which is what a check's folder
  is for (`CONVENTIONS.md` section 2, step 5). The corrected check is `LA_ws_2026-09-21_to_2026-09-21_2`.

## At a glance

| | |
| :---- | :---- |
| Country | Lao PDR (`LA`) |
| Run type | Update check against `LA_ws_2026-09-21`, **no crawl** |
| Date | 2026-09-21 |
| Time, UTC | 05:30:33 to 05:58 (about 27 minutes) |
| Requests | **193** — robots.txt and every listing page, `old=0` and `old=1` |
| Documents fetched | **0** |
| Verdicts | 1,720 `unchanged`, 46 `document_moved`, 9 `not_stored` |
| Of which real | **4** `document_moved` and **9** `not_stored` — 13 documents |
| Status | **Superseded by `_2`.** Kept as the record of the listing on this date |
| Checked | `changes.json`, `changes.md`, `links_used/catalogue_meta.json`, `links_used/laws.csv` |

## What it found, and what was real

| Verdict | Reported | Real | What the rest were |
| :---- | ----: | ----: | :---- |
| `unchanged` | 1,720 | 1,720 | — |
| `document_moved` | 46 | **4** | 42 were the whitespace defect above. The 4 real ones are the addresses that carry an HTML entity, `&#039;` for an apostrophe: the crawl asked for the literal entity, the corrected parser asks for the apostrophe, so the address genuinely changed between the two lists |
| `not_stored` | 9 | 9 | The nine documents the portal links but does not serve (`../LA_ws_2026-09-21/RUN_NOTE.md`) |
| `new_law` | 0 | 0 | Nothing was published in the five hours between the list build and the check |
| `status_changed` | 0 | 0 | No law changed its status word |
| `delisted` | 0 | 0 | — |

**That `new_law` and `status_changed` are both zero is the expected answer, not a failure.** The check ran the
same morning as the crawl; the portal had no time to change. What it does prove is that the check reads the
whole portal, matches 1,720 of 1,773 laws exactly, and costs 193 requests.

## The defect, and where it is fixed

`_cell()` in Malaysia's `catalogue.py` is imported by Singapore, Australia, Timor-Leste and Lao PDR. Collapsing
whitespace in a URL column is wrong for all of them; it has simply never shown, because no other portal in this
workshop has a filename with two consecutive spaces in it.

This session was not permitted to edit another country's folder, so the fix is local: Lao PDR's `catalogue.py`
now writes URL columns verbatim (`_URL_COLUMNS`, `_cells`), and a test covers it. **The shared change is written
up in `countries/la-lao-pdr/NOTES.md` under "Shared-file edits still to make"** — it belongs in `_cell` itself,
so every country gets it.

`updates/baseline.py` also now prefers a run's `links_rebuilt/` census over its frozen `links_used/`, so a
corrected list fixes future checks without anyone rewriting what the crawl actually replayed.

## What is in this folder

| Path | What it is |
| :---- | :---- |
| `RUN_NOTE.md` | This note |
| `changes.md`, `changes.json` | Every verdict, with the address before and after |
| `links_used/` | The delta list (55 rows, 42 of them spurious) and **the full census of the 1,773 laws the portal listed on 2026-09-21**, written by the scraper as it then stood — so its `laws.csv` carries the same whitespace defect |
| `links_used/discovery_log.jsonl` | All 193 requests, with their times and waits |

No `manifest.*` and no `raw/`: nothing was crawled from this check.

## Politeness

193 requests at `REQUEST_DELAY_MS=6000` plus jitter, one at a time, one process against the host. **No refusal
of any kind** — the portal has now taken about 4,000 requests from us in a day without once pushing back. The
delay is ours: this host publishes no robots.txt.

## Changes after the run

- **2026-09-21:** superseded by `LA_ws_2026-09-21_to_2026-09-21_2`, run after the census defect was fixed and
  the link list rebuilt. This folder is unchanged apart from this note.
