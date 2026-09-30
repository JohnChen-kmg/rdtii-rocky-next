# Run note: AU_ws_2026-09-19

Australia, **a two-document crawl from a rebuilt link list**, 19 September 2026: the Commonwealth of Australia
Constitution Act, newly seeded, and one act whose address on the register moved.

## Read this first

- **The Constitution is now collected.** The developer decided on 2026-09-19 that it belongs in the list: it is an
  Act in force, and the scope we state is every principal act. It is not in the `Act` collection the harvest reads
  (the register keeps it in the `Q` series), so only a seed reaches it; `links/seed_laws.yaml` carries the
  reasoning as its provenance. It claims **no indicator**, and the seed filter was changed so that an untagged seed
  is kept instead of dropped (`countries/au-australia/scraper/adapter.py`, `_seed_by_id`).
- **Two documents fetched, both clean:** 2 stored, 0 flagged by the audit, 0 missing, validation OK.
- **The second document is a re-fetch, not a change of law.** The register moved the as-made address of the Social
  Security and Veterans' Entitlements Legislation Amendment (One-off Payments and Other Budget Measures) Act 2008
  from `.../asmade/2008-07-01/...` to `.../asmade/2008-05-26/...`, with the same version id `C2010C00286`. The text
  is the same; the copy was re-fetched so the stored file still joins to the list by `source_url`.
- **The Water Act 2007 was not fetched again.** The rebuilt list points at its 5 September compilation
  (`C2026C00398`), which the update check of 16 September had already stored (`AU_ws_2026-09-15_to_2026-09-16`).
- **The corpus was rebuilt:** `AU_corpus_2026-09-19`, 1,278 documents from 3 runs, 2 superseded copies listed,
  91 audit flags carried, validation OK. That is what downstream reads.

## At a glance

| | |
| :---- | :---- |
| Country | Australia (`AU`) |
| Run type | Crawl of the rows a rebuilt link list added, from `links/documents.jsonl` of 2026-09-19 22:37 UTC |
| Date | 2026-09-19 |
| Time, UTC | List rebuild 22:27:52 to 22:37:14 (122 requests). Crawl 22:38:59 to 22:39:14 (16 s, 2 requests at `REQUEST_DELAY_MS=10000`) |
| Time, machine clock | US Eastern Daylight Time, UTC−4: 18:27 to 18:39 |
| Stored | 2 of 2: `au-caca-001` (HTML from the dated epub, 1900 Act, text as at 1977-07-29), `au-ssvelaa2008-001` (native PDF) |
| Size | 408,898 bytes |
| Audit | 2 read, **0 flagged**, 0 missing. Rules: `AU` |
| Law table | `law_table.csv`, 2 rows, both `in force` and `evidence` |

## What the list rebuild changed

The rebuild was needed because a new seed invalidates the list's registry fingerprint (`CONVENTIONS.md` rule 9).
Against the list of 2026-09-15: **1,277 rows → 1,278**, three rows differing.

| Title | Before | After | Fetched here |
| :---- | :---- | :---- | :---- |
| Commonwealth of Australia Constitution Act (`C2004Q00685`) | not in the list | in it, as a seed | Yes |
| Water Act 2007 (`C2007A00137`) | compilation `C2026C00302`, 1 July 2026 | `C2026C00398`, 5 September 2026 | No: stored on 16 September |
| Social Security and Veterans' Entitlements… Act 2008 (`C2008A00019`) | as made, dated 1 July 2008 | as made, dated 26 May 2008 | Yes, the address moved |

No other row moved: 1,275 version ids are unchanged since 15 September. The harvest itself grew from 4,765 titles
to 4,768.

## Issues

1. **The whole-of-register harvest still cannot see the Constitution.** It is collected only because it is a seed.
   If the register moves another act out of the `Act` collection, the same blindness applies and nothing reports
   it. Watching for that needs a check the tool does not have.
2. **The re-fetch of `C2008A00019` shows addresses can move without the law changing.** The update check compares
   version ids, so it would not have reported this; only a list rebuild did. It is an argument for the periodic
   rebuild the cadence already asks for.
