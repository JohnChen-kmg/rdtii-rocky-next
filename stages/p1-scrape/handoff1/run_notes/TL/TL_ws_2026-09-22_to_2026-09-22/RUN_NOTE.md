# Run note: TL_ws_2026-09-22_to_2026-09-22 — the update check, corrected

## Read this first

**The correct result of Timor-Leste's first live update checks.** Run on 2026-09-22 straight after
`TL_ws_2026-09-20_to_2026-09-22`, whose result was wrong: the check compared the gazette's addresses as strings,
and a baseline recorded before the parser canonicalised them made 191 acts look moved (that folder's note has the
detail). With `canonical_url()` in `scraper/parse.py` and every comparison in `updates/diff.py` going through it:

- **Nothing moved.** 4,759 acts unchanged.
- **29 acts in 16 issues are not stored** — the documents the first crawl could not fetch, still missing. These are the
  delta list, and they are genuine.
- Seven requests at the portal's `Crawl-delay: 10`, no refusal, exit 0.

**Its baseline is the previous check**, not the crawl, because the tool takes the newest run that has a list
(`updates/WORKFLOW.md`). That is why the folder is named from 2026-09-22. Stored documents are read from every run's
manifest, so the crawl of 2026-09-20 still supplies them, and the result is the same as against the crawl.

## At a glance

| | |
| :---- | :---- |
| Baseline | `TL_ws_2026-09-20_to_2026-09-22` (its list: 2026-09-22T05:08:29Z); stored documents from `TL_ws_2026-09-20` |
| Checked | 2026-09-22T05:12:23Z, 7 requests, exit 0 |
| Result | **unchanged 4,759, not_stored 29** — 16 documents to fetch |
| Crawled | **nothing** — the delta crawl is the developer's to run |
| Watch list | printed before and after |

## The delta crawl, when wanted

```
REQUEST_DELAY_MS=10000 JORNAL_FRONTIER=links_file \
  JORNAL_LINKS_FILE=<ws>/outputs/TL/TL_ws_2026-09-22_to_2026-09-22/links_used/documents.jsonl \
  python scrape.py --economy TL --scope all --out <ws>/outputs/TL/TL_ws_2026-09-22_to_2026-09-22
```

About three minutes at 10 s. It needs the engine to accept economy `TL` — one of the hand-back requests in
`countries/tl-timor-leste/NOTES.md` — so it runs in a sandbox that carries them, as the first crawl did. Several of
the 16 failed the first time for reasons the portal owns (a space in a file name, a former domain), so expect some to
fail again; `changes.md` lists each.

## Files

`changes.md`, `changes.json` and `links_used/`, as the check wrote them.
