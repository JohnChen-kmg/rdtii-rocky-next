# Corpus: TL_corpus_2026-09-20

TL, built 2026-09-20T14:59:28Z by `tools/merge_corpus.py` from 1 run(s): `TL_ws_2026-09-20`.

**1921 documents**, one per law and kind, the newest run's copy of each. 14 older copies superseded (`superseded.jsonl`), 0 excluded by flag, 146 carrying content flags from the runs' audits, 0 renamed doc_ids. Validation against contract 0.2.0: OK (1921 rows, 0 errors, 0 warnings).

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
| `TL_ws_2026-09-20` | 1935 | 1921 | 14 | 0 | 0 |

## Content flags carried by the rows

| Flag | Rows |
| :---- | ----: |
| `act_not_in_text` | 3 |
| `acts_not_in_text` | 1 |
| `duplicate_content` | 14 |
| `no_sumario` | 35 |
| `no_text_layer` | 29 |
| `not_a_gazette_issue` | 4 |
| `short_principal` | 65 |

A flagged row is a stored file that is not, or may not be, the law's text (a repeal notice, another act's text, a Malay file recorded as English, a page with no text layer). `links_used/documents.jsonl` names the flags per row.

## Superseded (first 30)

| Older copy | Run | Replaced by | Run |
| :---- | :---- | :---- | :---- |
| tl-hfnesnjdhiem-001 (2/2016) | TL_ws_2026-09-20 | tl-paolnddasppt2004-001 | TL_ws_2026-09-20 |
| tl-cdraapdrcnddripneee-001 (10/2016) | TL_ws_2026-09-20 | tl-adlnddj2008-001 | TL_ws_2026-09-20 |
| tl-coqprmadcnopdstlpcndacodtlnddmd2015-001 (44/2015) | TL_ws_2026-09-20 | tl-rcodooidt-001 | TL_ws_2026-09-20 |
| tl-conodganddad2015-001 (53/2015) | TL_ws_2026-09-20 | tl-ondmrdd-001 | TL_ws_2026-09-20 |
| tl-nosdragccdccdpndrb-001 (57/2015) | TL_ws_2026-09-20 | tl-qcocdieaose-001 | TL_ws_2026-09-20 |
| tl-dodidcedmdodtleseopmdrmdaj-001 (61/2015) | TL_ws_2026-09-20 | tl-ondmrdj-001 | TL_ws_2026-09-20 |
| tl-ccodtlcoeqcpldlon-001 (62/2015) | TL_ws_2026-09-20 | tl-ondpndcdm8034-001 | TL_ws_2026-09-20 |
| tl-cqpvrmadcdnopdstlpcndanddmd2015-001 (64/2015) | TL_ws_2026-09-20 | tl-copnkrxgo-001 | TL_ws_2026-09-20 |
| tl-aaredcoedirapdendjd2013-001 (2/2015) | TL_ws_2026-09-20 | tl-qaorondpndrb-001 | TL_ws_2026-09-20 |
| tl-acgded2013-001 (4/2015) | TL_ws_2026-09-20 | tl-opdrbntdaanjdcodrbdtdtlccoaddlnddm2009-001 | TL_ws_2026-09-20 |
| tl-roaerbdtdtless-001 (18/2015) | TL_ws_2026-09-20 | tl-neereprosjapordtn-001 | TL_ws_2026-09-20 |
| tl-aardedt-001 (12/2015) | TL_ws_2026-09-20 | tl-cpdrdeapmdgc-001 | TL_ws_2026-09-20 |
| tl-dndfopb-001 (22/2015) | TL_ws_2026-09-20 | tl-ro-001 | TL_ws_2026-09-20 |
| tl-sopdinudeodcrepodceb-001 (43/2015) | TL_ws_2026-09-20 | tl-soacopmdhsrvdmeoosc-001 | TL_ws_2026-09-20 |
