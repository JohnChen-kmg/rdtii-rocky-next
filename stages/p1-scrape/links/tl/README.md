# links/

**`seed_laws.yaml` is hand-edited. Everything else here is generated and must never be edited by hand.**

| File | What it is |
| :---- | :---- |
| `seed_laws.yaml` | The laws named on purpose, with the provenance of each. A seed names an act by `portal_key` (`<category>:<number>`, e.g. `decretos_leis:12/2024`), because the gazette has no per-law address: the adapter resolves it to the issue that carries it |
| `documents.jsonl` | **One row per gazette issue**, in crawl order, with the contract's metadata in `contract_meta`. `contains` names every act in the file |
| `documents.csv` | The same, flattened for a spreadsheet |
| `laws.csv` | **One row per act** — the census of everything the six category pages list, with the issue it appears in and why any act has no document |
| `catalogue_meta.json` | The settings the build used, the request count, the robots.txt record, a fingerprint of the registry, and the sha256 of each scraper file |
| `discovery_log.jsonl` | Every request the build sent, with its time |

**Built 2026-09-20, 7 requests, 89 seconds:** 4,788 acts on six category pages, resolving to **1,953 distinct
documents**; 9 seed issues, 198 relevant. 34 acts carry no document link and keep their row with the reason.
923 documents carry more than one act; one carries 39.

**Rebuild** (`../scraper/WORKFLOW.md`, step 2):

```
REQUEST_DELAY_MS=10000 PYTHONPATH=src python -m p1_scrape.adapters.tl_jornal.catalogue \
    --registry <ws>/countries/tl-timor-leste/sources.yaml \
    --seeds <ws>/countries/tl-timor-leste/links/seed_laws.yaml \
    --out <ws>/countries/tl-timor-leste/links
```

**Crawling from the list:** the crawl replays `documents.jsonl` (`JORNAL_FRONTIER=links_file`) and refuses a list
built from a different registry — `catalogue_meta.json` carries `cfg_sha256`, computed over the seeds, the
`jornal:` settings (except `frontier` and `links_file`), the title rule and the search terms. Change any of those
and rebuild.

**Joining back:** a manifest row joins to a document row on `source_url`, and a document row joins to its acts
through `contract_meta.contains` (the `portal_id` of each act in `laws.csv`).

**Hand-back:** `sources.yaml` and `seed_laws.yaml` are joined, `sources.yaml` first, into
`instrument/sources_tl.yaml` and `contracts/instrument/sources_tl.yaml` (`countries/README.md`).
