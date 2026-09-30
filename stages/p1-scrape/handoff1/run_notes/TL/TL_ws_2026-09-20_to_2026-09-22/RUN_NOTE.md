# Run note: TL_ws_2026-09-20_to_2026-09-22 — the first live update check, and a defect it exposed

## Read this first

> **Superseded. Do not crawl this folder's delta list.** It asks for 66 documents, and **50 of them are already
> stored.** The correct check is `TL_ws_2026-09-22_to_2026-09-22`, which asks for 16. This folder is kept, as every
> run folder is, as the record of the defect.

**Timor-Leste's update check had never run live.** It was run on 2026-09-22 during an audit of the workshop, and it
worked — seven requests at the portal's `Crawl-delay: 10`, exit 0 — but its result was wrong: **191 acts reported as
moved, 66 documents to fetch.** Acts from 2008 and 2015 do not move in two days.

## What was wrong

The parser has canonicalised the gazette's addresses since the crawl of 2026-09-20 (`scraper/parse.py`, `_unescape`),
but that crawl's list and manifest record the forms the portal served before the fix. The check compared addresses
as strings:

| Of the 191 "moves" | Old address | New address |
| :---- | :---- | :---- |
| **188** — scheme and host only | `http://mj.gov.tl/jornal/public/docs/2016/serie_1/SERIE_I_NO_5.pdf` | `https://www.mj.gov.tl/jornal/public/docs/2016/serie_1/SERIE_I_NO_5.pdf` |
| **3** — a host-less link, since repaired | `http://public/docs/2015/serie_1/SERIE_I_NO_28.pdf` | `https://www.mj.gov.tl/jornal/public/docs/2015/serie_1/SERIE_I_NO_28.pdf` |

It looked stored documents up the same way, so it found none of the 191 stored. Checked against the baseline's
manifest by canonical address: **50 of the 66 documents to fetch are already held; 16 are genuinely missing.**

## The fix

`scraper/parse.py` gained `canonical_url()`, one key for one file whatever form of the address a run recorded, and
`updates/diff.py` now compares every address — the act's previous and current document, and the stored-document
lookup — by that key, never by string. Four tests were added to `tests/test_tl_updates.py`: three old forms of one
address are unchanged and not fetched again, and a genuinely different file is still a move. The suite is 36 of 36.
The re-run is `TL_ws_2026-09-22_to_2026-09-22`.

## At a glance

| | |
| :---- | :---- |
| Baseline | `TL_ws_2026-09-20`, list built 2026-09-20T06:00:49Z |
| Checked | 2026-09-22T05:08:28Z, 7 requests, exit 0 |
| Result as reported | unchanged 4,569, **document_moved 191**, not_stored 28; 66 documents to fetch |
| Result, correctly | 50 of the 66 already stored — see the re-run |
| Crawled | nothing |
| Watch list | printed before and after, as `CONVENTIONS.md` rule 11 requires — the first run of an engine-installed update check to do so |

## Files

`changes.md`, `changes.json` and `links_used/` as the check wrote them, unedited: `CONVENTIONS.md` rule 7, generated
files are never hand-edited.
