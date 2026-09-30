# links/

The laws and the links, for Malaysia. `sources.yaml` next door says where to look and how. This folder says
what gets fetched.

| File | Edited by | What it holds |
| :---- | :---- | :---- |
| `seed_laws.yaml` | hand | The laws named on purpose: agency documents and acts chosen by number, each with its URL, fallback URL, indicator tags and `provenance`. Flow style `- {...}` only |
| `documents.jsonl` | the scraper | **Every document the crawl fetches**, one JSON object per line, in crawl order: seeds first, then the acts the title rule selects, then the rest. Each row has the Candidate fields, `scopes` (`seed`, `relevant`, `all`) and the full `contract_meta` |
| `documents.csv` | the scraper | The same rows, flattened, for reading in a spreadsheet |
| `laws.csv` | the scraper | One row per act in the two Laws of Malaysia listings (repeated amendment-listing rows count once): every principal act and amending act, what was decided for it, and `not_crawled_reason` when it has no document in the list |
| `catalogue_meta.json` | the scraper | When the list was built, the settings, the request count, the robots.txt record, the run notes, and sha256 hashes of the scraper files and the registry |
| `discovery_log.jsonl` | the scraper | Every request the build sent, with its time and wait |
| `build.log` | the scraper's console | The notes the last build printed: what was left out on purpose, which timelines could not be read |

**Never edit the generated files.** Rebuild them with absolute paths, from the stage root of a sandbox copy of the stage
with `scraper/` installed as `src/p1_scrape/adapters/my_gazette/` (or of the repo, once the package is handed back):

```
PYTHONPATH=src python -m p1_scrape.adapters.my_gazette.catalogue --registry <this folder>/../sources.yaml --seeds <this folder>/seed_laws.yaml --out <this folder>
```

The build reads robots.txt, both listings and the detail-page timelines `lom.timeline` asks for: 226 paced
requests and 15 minutes under `rule` on 2026-09-14; every act's under `all`, the convention since decision 17
(1,970 requests, 2 h 14 min on 2026-09-15, the list now here). It fetches no document.

**Crawling from the list.** Set `LOM_FRONTIER=links_file` and `LOM_LINKS_FILE=<path>/documents.jsonl`, then
run the normal crawl into a new run folder, given as an absolute path
(`scrape.py --economy MY --scope all --out <your run folder>, e.g. handoff1/MY/MY_ws_<YYYY-MM-DD>`), named
and noted per `outputs/README.md`. `--scope seed` and `--scope relevant` take only the
rows marked for those scopes. The crawl still reads robots.txt first and drops any lom row it disallows. It refuses
a list whose `catalogue_meta.json` fingerprint (`cfg_sha256`: seeds, title rule, lom settings, secondary-copy
whitelist) differs from the registry: rebuild the list first. A list without a fingerprint, such as the copy
the 2026-09-14 crawl used (`outputs\MY\MY_ws_2026-09-14\links_used`, 07:04 UTC), is served with a warning only. For
`--scope relevant` also set `MAX_CANDIDATES_PER_ECONOMY=0`: the relevant scope holds about 190 rows and the Round 1
engine keeps only the first 60 by default (the scraper warns).

**Joining back.** A manifest row's `source_url` equals the row's `url` in `documents.jsonl`, so the metadata the
Round 1 engine does not write (`contract_meta`: document kind, links, status, version date, language, flags)
joins back on it.

**Hand-back.** `seed_laws.yaml` is joined after `sources.yaml` into the repo's `sources_my.yaml`
(`countries/README.md`). The generated files are not handed back as crawl input. Keep the copy a crawl read
in its run folder, as `links_used/` (`outputs/README.md`).
