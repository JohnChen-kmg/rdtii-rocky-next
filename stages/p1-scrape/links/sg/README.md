# links/

The laws and the links, for Singapore. `sources.yaml` next door says where to look and how (block `sso:`). This
folder says what gets fetched.

| File | Edited by | What it holds |
| :---- | :---- | :---- |
| `seed_laws.yaml` | hand | The 21 laws named on purpose, with their links, indicator tags and provenance. Flow style `- {...}` only |
| `documents.jsonl` | the scraper | **Every document the crawl fetches**, one JSON object per line, in crawl order: seeds first, then the acts the title net selects, then the rest. Each row has the Candidate fields, `scopes` (`seed`, `relevant`, `all`) and the full `contract_meta` (act code, official number, current version date, the amending instruments, revised edition, status) |
| `documents.csv` | the scraper | The same rows, flattened, for a spreadsheet |
| `laws.csv` | the scraper | One row per act in the Current, Repealed, Uncommenced and Acts Supplement listings: what was decided for it, and `not_crawled_reason` when it has no document in the list |
| `catalogue_meta.json` | the scraper | When the list was built, the settings, the request count, the robots.txt record (Crawl-delay 6), the notes, the registry fingerprint |
| `discovery_log.jsonl` | the scraper | Every request the build sent, with its time and wait |
| `build.log` | the scraper's console | The notes the last build printed |

**Never edit the generated files.** Rebuild them from the stage root of a sandbox copy of the stage with `scraper/`
installed as `src/p1_scrape/adapters/sg_sso/` (`../scraper/WORKFLOW.md`, step 2):

```
PYTHONPATH=src python -m p1_scrape.adapters.sg_sso.catalogue --registry <this folder>/../sources.yaml --seeds <this folder>/seed_laws.yaml --out <this folder>
```

The build reads robots.txt, the listings and every current act's detail page at 6 s or more: about 540 requests, an
hour. It fetches no document.

**Crawling from the list.** Set `SSO_FRONTIER=links_file`, `SSO_LINKS_FILE=<path>/documents.jsonl` and
`REQUEST_DELAY_MS=6000`, then run the normal crawl into a new run folder (`../scraper/WORKFLOW.md`, step 3). The
crawl refuses a list whose `catalogue_meta.json` fingerprint differs from the registry: rebuild the list first.

**Joining back.** A manifest row's `source_url` equals the row's `url` in `documents.jsonl`
(`https://sso.agc.gov.sg/Act/<CODE>?ViewType=Pdf`), so the metadata the Round 1 engine does not write joins back on it.

**Hand-back.** `seed_laws.yaml` is joined after `sources.yaml` into the repo's `sources_sg.yaml`
(`countries/README.md`). The generated files are not handed back as crawl input; the copy a crawl read stays in its
run folder as `links_used/`.
