# Corpus: AU_corpus_2026-09-19

AU, built 2026-09-19T22:39:37Z by `tools/merge_corpus.py` from 3 run(s): `AU_ws_2026-09-19`, `AU_ws_2026-09-15_to_2026-09-16`, `AU_ws_2026-09-15`.

**1278 documents**, one per law and kind, the newest run's copy of each. 2 older copies superseded (`superseded.jsonl`), 0 excluded by flag, 91 carrying content flags from the runs' audits, 0 renamed doc_ids. Validation against contract 0.2.0: OK (1278 rows, 0 errors, 0 warnings).

## What is in this folder

| Path | What it is |
| :---- | :---- |
| `manifest.csv`, `manifest.jsonl` | The corpus, in the Hand-off #1 shape. `crawl_notes` says which run each row came from and its content flags |
| `raw/` | The documents and their header files, copied from the runs under their original paths |
| `superseded.jsonl` | Every older copy a newer run replaced: doc_id, run, URL, the doc_id that supersedes it, and what they matched on (`law`: portal id and kind; `url`; `doc_id`, the same law under the same id; `content`, the same bytes) |
| `links_used/documents.jsonl` | One link row per document here, with `contract_meta.content_flags` and `corpus.run`; a row marked `synthetic` stands in for a document its run's list did not carry |
| `links_used/laws.csv`, `catalogue_meta.json` | The listing state of the newest run that has one |
| `corpus_meta.json` | The figures above, per run |

## Per run

| Run | Documents | Included | Superseded | Excluded | Renamed |
| :---- | ----: | ----: | ----: | ----: | ----: |
| `AU_ws_2026-09-19` | 2 | 2 | 0 | 0 | 0 |
| `AU_ws_2026-09-15_to_2026-09-16` | 1 | 1 | 0 | 0 | 0 |
| `AU_ws_2026-09-15` | 1277 | 1275 | 2 | 0 | 0 |

## Content flags carried by the rows

| Flag | Rows |
| :---- | ----: |
| `as_made_short_act` | 88 |
| `renamed_since_enactment` | 2 |
| `short_principal` | 1 |

A flagged row is a stored file that is not, or may not be, the law's text (a repeal notice, another act's text, a Malay file recorded as English, a page with no text layer). `links_used/documents.jsonl` names the flags per row.

## Superseded (first 30)

| Older copy | Run | Replaced by | Run |
| :---- | :---- | :---- | :---- |
| au-wa2007-001 (No. 137, 2007) | AU_ws_2026-09-15 | au-wa2007-001 | AU_ws_2026-09-15_to_2026-09-16 |
| au-ssvelaa2008-001 (No. 19, 2008) | AU_ws_2026-09-15 | au-ssvelaa2008-001 | AU_ws_2026-09-19 |
