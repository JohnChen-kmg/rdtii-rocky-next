# links/

**`seed_laws.yaml` is hand-edited. Everything else here is generated and must never be edited by hand.**

| File | What it is |
| :---- | :---- |
| `seed_laws.yaml` | The laws named on purpose, with the provenance of each. A seed names a law by `portal_key`, which is the gazette's **own record id** (the `id=` of its page): there is no act number anywhere on this portal, and the file addresses are too inconsistent to build one from |
| `documents.jsonl` | **One row per file**, in crawl order, with the contract's metadata in `contract_meta`. A law with an English translation contributes **two** rows — same `portal_id`, different `law_slug` (`la-2537` and `la-2537-en`) and different `language` |
| `documents.csv` | The same, flattened for a spreadsheet |
| `laws.csv` | **One row per law** — the census of everything every listing names, once each, with both of its files and why a law has none |
| `catalogue_meta.json` | The settings the build used, the request count, the robots.txt record, a fingerprint of the registry, and the sha256 of each scraper file |
| `discovery_log.jsonl` | Every request the build sent, with its time and how long it waited |

**Built 2026-09-20 23:56 to 2026-09-21 00:24 UTC, 194 requests, 28 minutes:** every listing the portal offers
for laws, at `old=0` (current) and `old=1` (superseded), ten rows a page. **1,773 laws resolving to 1,824
files** — 1,769 Lao and 55 English. No document was downloaded, no detail page was read, and the portal did not
refuse a single request.

| | |
| :---- | ----: |
| Laws listed | 1,773 |
| Files to crawl | 1,824 (`all`); 334 `relevant`; 14 `seed` |
| In force / repealed | 1,480 / 293 |
| Principal acts / subsidiary / amending / other | 356 / 1,249 / 41 / 178 |
| Laws with an English translation | 55 |

**Three things in this list are not obvious, and each is a portal property rather than ours:**

1. **1,769 Lao files cover 1,773 laws.** Four pairs of unrelated laws point at the **same** file — the generic
   uploads `001.pdf`, `003.pdf`, `04.pdf` and `scan0001.pdf`. One of them is claimed by both a 2023 Presidential
   Ordinance and a 2014 provincial Order, which cannot both be right. The file is fetched once as served, both
   laws keep their row, and both are flagged (`shared_file_address`; `../NOTES.md` 1.3). Flag, do not fix.
2. **Two laws are listed under two kinds.** `legaltype=6` (Law) also carries the Civil Code and the Penal Code,
   which have listings of their own. Each is kept once, under the more specific listing, with the other named in
   `also_listed_under`.
3. **`legaltype=16` is not in this list at all.** It holds 180 of `legaltype=6`'s 182 laws and nothing else, so
   reading it costs 18 requests and adds no law (`../NOTES.md` 1.2). `legaltype=4` is in the list with **zero**
   laws: the portal prints ບໍ່ມີຂໍ້ມູນ, no data, for that kind.

**Rebuild** (`../scraper/WORKFLOW.md`, step 2) — about 28 minutes, and **never while a crawl is running**:

```
REQUEST_DELAY_MS=6000 PYTHONPATH=src python -m p1_scrape.adapters.la_gazette.catalogue \
    --registry <ws>/countries/la-lao-pdr/sources.yaml \
    --seeds <ws>/countries/la-lao-pdr/links/seed_laws.yaml \
    --out <ws>/countries/la-lao-pdr/links
```

**Crawling from the list:** the crawl replays `documents.jsonl` (`GAZETTE_FRONTIER=links_file`) and refuses a
list built from a different registry — `catalogue_meta.json` carries `cfg_sha256`, computed over the seeds, the
`gazette:` settings (except `frontier` and `links_file`), the title rule and the search terms. Change any of
those and rebuild.

**Joining back:** a manifest row joins to a document row on `source_url`, and a document row joins to its law
through `contract_meta.portal_id`, which is the key `laws.csv` is indexed by. Because a translation is a second
row against the same `portal_id`, join on `portal_id` **and** `language` when you want one file.

**Hand-back:** `sources.yaml` and `seed_laws.yaml` are joined, `sources.yaml` first, into
`instrument/sources_la.yaml` and `contracts/instrument/sources_la.yaml` (`countries/README.md`). The generated
files here are never handed back as crawl input.
