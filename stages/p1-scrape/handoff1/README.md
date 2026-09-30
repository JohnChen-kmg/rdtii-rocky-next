# handoff1/ — what the crawler retrieved, described but not contained

This is the evidence for the retrieval stage: **one folder per economy, holding the record of every
document collected, and none of the documents themselves.** About 68 MB, against 19 GB of retrieved law
that stays out of the repository.

`HANDOFF1_DIR` (`interface/DATA_PATHS.md`) points at **one** economy's corpus folder below. Set it to the
economy you want to read.

| Economy | Folder | Documents described | Notes |
| :---- | :---- | ----: | :---- |
| Malaysia | `MY/MY_corpus_2026-09-15/` | 1,391 | 1,441 law-table rows with `--all` |
| Singapore | `SG/SG_corpus_2026-09-16/` | 738 | repealed acts dropped at the crawl (decision 19) |
| Australia | `AU/AU_corpus_2026-09-19/` | 1,278 | 4,779 law-table rows with `--all` |
| Timor-Leste | `TL/TL_corpus_2026-09-20/` | 1,921 | one gazette file can carry several acts |
| Lao PDR | `LA/LA_corpus_2026-09-21/` | 1,762 | 93.6% scans; see the note on translations |
| China | `CN/` | ~1,100 | a different shape by decision — see below |

Each corpus folder holds `manifest.csv` and `manifest.jsonl` (the Hand-off #1 rows), `law_table.csv` (one
row per law, with its in-force reading and dates), `links_used/` (the link list the crawl replayed, and
the census of every law the portal listed), `superseded.jsonl`, `audit.json` and `audit.md` (which stored
files are not the law's text), `corpus_meta.json` and `CORPUS_NOTE.md`.

`run_notes/` carries the note and audit of every individual crawl and update check, including the ones
whose bulk data did not travel — the narrative record of how each corpus was built.

## What is not here, and how to get it

**The documents.** `raw/` is excluded at every depth, and so are the two folder names China's
collector uses instead — `files/` for document bodies and `text/` for extracted plain text. `manifest.csv` gives every one of them a
`source_url`, a `content_sha256` and a `byte_size`, so a reviewer can re-fetch any row and prove it is
the same bytes. Re-crawling an economy repopulates `raw/` under the folder `local_path` already names.

**So `scrape.py --validate` will report two errors per row on a fresh clone** — `local_path does not
resolve on disk` and `http_headers_path does not resolve on disk` — and nothing else. That is the
documents being absent, not a contract breach. Measured 2026-09-29 across all five corpora: **zero
schema errors, zero `economy` errors, zero `doc_id` errors**. Validate after a crawl, not before.

## China is a different shape, by decision

China has no `_corpus_` folder and no `law_table.csv`, because the national database
(`flk.npc.gov.cn`) forbids automated collection in its robots.txt. Its documents were collected by hand
and the collection is organised by source instead: `CN_sources_2026-09-21/` with one folder per
publisher, each carrying a `provenance.tsv`; `manual/npc-database/index.csv` indexing the 945 documents
of the bulk download; `CN_layer2_links.md` as the link registry; and `MANUAL_UPDATE_CHECK.md`, the
worklist for the re-check no tool can perform.

**One thing China loses that a crawl cannot restore.** For the five crawlable economies the
documents are absent but re-fetchable. China's are not: MIIT answers 403, Customs 412, and the
national database forbids automated collection, which is why they were collected by hand. So the
8.7 MB of extracted text that was in the collection does not ship either, and a reviewer who wants
China's text follows the addresses in each `provenance.tsv` by hand, as the collector did. Whether
to ship it instead is a redistribution question for the developer, not a technical one.

Two consequences for anyone reading China programmatically. Its rows carry **no** field of the Hand-off
#1 manifest schema, so it needs its own reader. And `CN_ws_2026-09-21/` uses the `_ws_` name the
conventions reserve for an engine crawl while sharing no column with the engine's manifest — so do not
glob `*_ws_*/manifest.csv` across economies and expect one shape.

## Reproducing a law table from what is here

The checker sends no request and reads only the folder, so a reviewer can rebuild any law table and
compare it byte for byte with the one shipped:

```
PYTHONPATH=src python -m p1_scrape.adapters.la_gazette.checker \
    handoff1/LA/LA_corpus_2026-09-21 --all --out /tmp/law_table.csv
```

Measured 2026-09-25 in the development workshop: 12 of the 13 committed law tables regenerate
byte-for-byte. The exception is Australia's first run table, which predates the `use` column
(decision 20) by a day and so cannot be reproduced by current code. `docs/stages/p1-scrape/notes/
2026-09-24_tooling-recheck.md` has the full measurement.
