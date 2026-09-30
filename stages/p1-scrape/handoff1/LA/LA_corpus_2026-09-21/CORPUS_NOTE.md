# Corpus: LA_corpus_2026-09-21

LA, built 2026-09-21T07:03:27Z by `tools/merge_corpus.py` from 2 run(s): `LA_ws_2026-09-21_to_2026-09-21_2`, `LA_ws_2026-09-21`.

**1762 documents**, one per law and kind, the newest run's copy of each. 53 older copies superseded (`superseded.jsonl`), 0 excluded by flag, 1695 carrying content flags from the runs' audits, 0 renamed doc_ids. Validation against contract 0.2.0: OK (1762 rows, 0 errors, 0 warnings).

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
| `LA_ws_2026-09-21_to_2026-09-21_2` | 4 | 4 | 0 | 0 | 0 |
| `LA_ws_2026-09-21` | 1811 | 1758 | 53 | 0 | 0 |

## Content flags carried by the rows

| Flag | Rows |
| :---- | ----: |
| `no_text_layer` | 1695 |
| `short_principal` | 8 |

A flagged row is a stored file that is not, or may not be, the law's text (a repeal notice, another act's text, a Malay file recorded as English, a page with no text layer). `links_used/documents.jsonl` names the flags per row.

## Superseded (first 30)

| Older copy | Run | Replaced by | Run |
| :---- | :---- | :---- | :---- |
| la-la2202en-001 () | LA_ws_2026-09-21 | la-la2202-001 | LA_ws_2026-09-21 |
| la-la880en-001 () | LA_ws_2026-09-21 | la-la880-001 | LA_ws_2026-09-21 |
| la-la2304en-001 () | LA_ws_2026-09-21 | la-la2304-001 | LA_ws_2026-09-21 |
| la-la2130en-001 () | LA_ws_2026-09-21 | la-la2130-001 | LA_ws_2026-09-21 |
| la-la1967en-001 () | LA_ws_2026-09-21 | la-la1967-001 | LA_ws_2026-09-21 |
| la-la752en-001 () | LA_ws_2026-09-21 | la-la752-001 | LA_ws_2026-09-21 |
| la-la549en-001 () | LA_ws_2026-09-21 | la-la549-001 | LA_ws_2026-09-21 |
| la-la459en-001 () | LA_ws_2026-09-21 | la-la459-001 | LA_ws_2026-09-21 |
| la-la447en-001 () | LA_ws_2026-09-21 | la-la447-001 | LA_ws_2026-09-21 |
| la-la428en-001 () | LA_ws_2026-09-21 | la-la428-001 | LA_ws_2026-09-21 |
| la-la2451en-001 () | LA_ws_2026-09-21 | la-la2451-001 | LA_ws_2026-09-21 |
| la-la2452en-001 () | LA_ws_2026-09-21 | la-la2452-001 | LA_ws_2026-09-21 |
| la-la690en-001 () | LA_ws_2026-09-21 | la-la690-001 | LA_ws_2026-09-21 |
| la-la1619en-001 () | LA_ws_2026-09-21 | la-la1619-001 | LA_ws_2026-09-21 |
| la-la1402en-001 () | LA_ws_2026-09-21 | la-la1402-001 | LA_ws_2026-09-21 |
| la-la2386en-001 () | LA_ws_2026-09-21 | la-la2386-001 | LA_ws_2026-09-21 |
| la-la2301en-001 () | LA_ws_2026-09-21 | la-la2301-001 | LA_ws_2026-09-21 |
| la-la2131en-001 () | LA_ws_2026-09-21 | la-la2131-001 | LA_ws_2026-09-21 |
| la-la2036en-001 () | LA_ws_2026-09-21 | la-la2036-001 | LA_ws_2026-09-21 |
| la-la1845en-001 () | LA_ws_2026-09-21 | la-la1845-001 | LA_ws_2026-09-21 |
| la-la1625en-001 () | LA_ws_2026-09-21 | la-la1625-001 | LA_ws_2026-09-21 |
| la-la1554en-001 () | LA_ws_2026-09-21 | la-la1554-001 | LA_ws_2026-09-21 |
| la-la1547en-001 () | LA_ws_2026-09-21 | la-la1547-001 | LA_ws_2026-09-21 |
| la-la1411en-001 () | LA_ws_2026-09-21 | la-la1411-001 | LA_ws_2026-09-21 |
| la-la1280en-001 () | LA_ws_2026-09-21 | la-la1280-001 | LA_ws_2026-09-21 |
| la-la1273en-001 () | LA_ws_2026-09-21 | la-la1273-001 | LA_ws_2026-09-21 |
| la-la1134en-001 () | LA_ws_2026-09-21 | la-la1134-001 | LA_ws_2026-09-21 |
| la-la913en-001 () | LA_ws_2026-09-21 | la-la913-001 | LA_ws_2026-09-21 |
| la-la545en-001 () | LA_ws_2026-09-21 | la-la545-001 | LA_ws_2026-09-21 |
| la-la670en-001 () | LA_ws_2026-09-21 | la-la670-001 | LA_ws_2026-09-21 |
