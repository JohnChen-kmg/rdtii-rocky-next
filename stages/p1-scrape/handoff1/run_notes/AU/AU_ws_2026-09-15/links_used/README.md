# links/

The laws and the links, for Australia. `sources.yaml` next door says where to look and how (block `register:`).
This folder says what gets fetched.

| File | Edited by | What it holds |
| :---- | :---- | :---- |
| `seed_laws.yaml` | hand | The 20 seeds named on purpose (10 Acts, 7 legislative instruments, 3 regulator documents), with their links, indicator tags and provenance. Flow style `- {...}` only |
| `documents.jsonl` | the scraper | **Every document the crawl fetches**, one JSON object per line, in crawl order: seeds first, then the Acts the title net selects, then the rest. Each row has the Candidate fields, `scopes` and the full `contract_meta` (title id, `No. N, YYYY`, the version's start date and register id, compilation number, the amendments it incorporates, status, the PDF and epub addresses) |
| `documents.csv` | the scraper | The same rows, flattened |
| `laws.csv` | the scraper | One row per title the API harvest returned, principal or not, with its latest version and `not_crawled_reason` when it has no document in the list |
| `catalogue_meta.json` | the scraper | When the list was built, the settings, the request counts per host, both robots.txt records (www Crawl-delay 10; the API has none), the harvest figures, the notes, the registry fingerprint |
| `discovery_log.jsonl` | the scraper | Every request the build sent |
| `build.log` | the scraper's console | The notes the last build printed |

**Never edit the generated files.** Rebuild them from the stage root of a sandbox copy of the stage with `scraper/`
installed as `src/p1_scrape/adapters/au_legislation/` (`../scraper/WORKFLOW.md`, step 2):

```
PYTHONPATH=src python -m p1_scrape.adapters.au_legislation.catalogue --registry <this folder>/../sources.yaml --seeds <this folder>/seed_laws.yaml --out <this folder>
```

The build reads the API only (about 120 requests at 3 s, under 10 minutes) plus the two robots.txt files. It reads
no `www` page and fetches no document.

**Crawling from the list.** Set `REGISTER_FRONTIER=links_file`, `REGISTER_LINKS_FILE=<path>/documents.jsonl` and
`REQUEST_DELAY_MS=10000` (the `www` host's Crawl-delay), then run the normal crawl into a new run folder
(`../scraper/WORKFLOW.md`, step 3). The crawl refuses a list built from a different registry.

**Joining back.** A manifest row's `source_url` equals the row's `url` in `documents.jsonl` (the dated epub
`https://www.legislation.gov.au/<id>/<start>/<start>/text/original/epub` under `document_form: epub`).

**Hand-back.** `seed_laws.yaml` is joined after `sources.yaml` into the repo's `sources_au.yaml`
(`countries/README.md`). The generated files are not handed back as crawl input.
