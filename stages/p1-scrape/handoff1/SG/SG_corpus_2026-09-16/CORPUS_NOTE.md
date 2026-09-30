# Corpus: SG_corpus_2026-09-16

SG, built 2026-09-16T14:21:06Z by `tools/merge_corpus.py` from 1 run(s): `SG_ws_2026-09-15`.

**738 documents**, one per law and kind, the newest run's copy of each. 1 older copies superseded (`superseded.jsonl`), 0 excluded by flag, 6 carrying content flags from the runs' audits, 0 renamed doc_ids. Validation against contract 0.2.0: OK (738 rows, 0 errors, 0 warnings).

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
| `SG_ws_2026-09-15` | 739 | 738 | 1 | 0 | 0 |

## Content flags carried by the rows

| Flag | Rows |
| :---- | ----: |
| `duplicate_content` | 1 |
| `short_principal` | 5 |

A flagged row is a stored file that is not, or may not be, the law's text (a repeal notice, another act's text, a Malay file recorded as English, a page with no text layer). `links_used/documents.jsonl` names the flags per row.

## Superseded (first 30)

| Older copy | Run | Replaced by | Run |
| :---- | :---- | :---- | :---- |
| sg-cr20185fdd-001 (S 519/2018) | SG_ws_2026-09-15 | sg-cr2018022a-001 | SG_ws_2026-09-15 |
