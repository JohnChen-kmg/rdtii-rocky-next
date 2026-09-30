# Corpus: MY_corpus_2026-09-15

MY, built 2026-09-15T11:58:23Z by `tools/merge_corpus.py` from 4 run(s): `MY_ws_2026-09-15_to_2026-09-15`, `MY_ws_2026-09-14_to_2026-09-15`, `MY_ws_2026-09-14`, `MY_ws_2026-09-13`.

**1391 documents**, one per law and kind, the newest run's copy of each. 18 older copies superseded (`superseded.jsonl`), 0 excluded by flag, 178 carrying content flags from the runs' audits, 9 renamed doc_ids. Validation against contract 0.2.0: OK (1391 rows, 0 errors, 0 warnings).

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
| `MY_ws_2026-09-15_to_2026-09-15` | 75 | 75 | 0 | 0 | 7 |
| `MY_ws_2026-09-14_to_2026-09-15` | 6 | 6 | 0 | 0 | 2 |
| `MY_ws_2026-09-14` | 1311 | 1310 | 1 | 0 | 0 |
| `MY_ws_2026-09-13` | 17 | 0 | 17 | 0 | 0 |

## Renamed doc_ids

The engine's id map starts fresh in every run, so two runs minted the same doc_id for two different documents. The older run's document keeps the id; the newer one is renamed here (its run folder keeps the id it minted, recorded in `crawl_notes` as `doc_id in run`).

| In this corpus | In its run | Run | Law | Collided with |
| :---- | :---- | :---- | :---- | :---- |
| my-puca2026-002 | my-puca2026-001 | MY_ws_2026-09-14_to_2026-09-15 | P.U. (B) 200/2026 P.U. (B) 200/2026 commencing Act A1780 | my-puca2026-001 in MY_ws_2026-09-14 (P.U. (B) 76/2026) |
| my-rta2026-002 | my-rta2026-001 | MY_ws_2026-09-14_to_2026-09-15 | Act A1794 ROAD TRANSPORT (AMENDMENT) ACT 2026 | my-rta2026-001 in MY_ws_2026-09-14 (Act A1789) |
| my-aa2013-002 | my-aa2013-001 | MY_ws_2026-09-15_to_2026-09-15 |  Amendment of Act 125 (04 Jan 2013) | my-aa2013-001 in MY_ws_2026-09-14 (Act A1452) |
| my-aa2011-002 | my-aa2011-001 | MY_ws_2026-09-15_to_2026-09-15 |  Amendment of Act 273 (07 Apr 2011) | my-aa2011-001 in MY_ws_2026-09-14 (Act A1395) |
| my-aa1976-002 | my-aa1976-001 | MY_ws_2026-09-15_to_2026-09-15 |  Amendment of Act 287 (27 Feb 1976) | my-aa1976-001 in MY_ws_2026-09-14 (Act 168) |
| my-aa2018-003 | my-aa2018-001 | MY_ws_2026-09-15_to_2026-09-15 |  Amendment of Act 313 (01 Jan 2018) | my-aa2018-001 in MY_ws_2026-09-14 (Act A1569) |
| my-puca2024-002 | my-puca2024-001 | MY_ws_2026-09-15_to_2026-09-15 | P.U. (B) 247/2024 P.U. (B) 247/2024 commencing Act A1714 | my-puca2024-001 in MY_ws_2026-09-14 (P.U. (B) 522/2024) |
| my-puca2026-003 | my-puca2026-001 | MY_ws_2026-09-15_to_2026-09-15 | P.U. (B) 90/2026 P.U. (B) 90/2026 commencing Act A1789 | my-puca2026-001 in MY_ws_2026-09-14 (P.U. (B) 76/2026) |
| my-puca2025-002 | my-puca2025-001 | MY_ws_2026-09-15_to_2026-09-15 | P.U. (B) 279/2025 P.U. (B) 279/2025 commencing Act A1723 | my-puca2025-001 in MY_ws_2026-09-14 (P.U. (B) 329/2025) |

## Content flags carried by the rows

| Flag | Rows |
| :---- | ----: |
| `gazette_notice` | 1 |
| `gazette_print` | 7 |
| `html_stored` | 2 |
| `language_mismatch` | 7 |
| `no_text_layer` | 56 |
| `one_page_principal` | 1 |
| `other_act_text` | 5 |
| `parent_not_named` | 1 |
| `repeal_notice` | 76 |
| `short_principal` | 90 |
| `subsidiary_amendment` | 23 |

A flagged row is a stored file that is not, or may not be, the law's text (a repeal notice, another act's text, a Malay file recorded as English, a page with no text layer). `links_used/documents.jsonl` names the flags per row.

## Superseded (first 30)

| Older copy | Run | Replaced by | Run |
| :---- | :---- | :---- | :---- |
| my-sta2018-001 (Act 807) | MY_ws_2026-09-14 | my-sta2018-001 | MY_ws_2026-09-14_to_2026-09-15 |
| my-pdpa2010-001 (Act 709) | MY_ws_2026-09-13 | my-pdpa2010-001 | MY_ws_2026-09-14 |
| my-pdpa2024-001 (Act A1727) | MY_ws_2026-09-13 | my-pdpa2024-001 | MY_ws_2026-09-14 |
| my-csa2024-001 (Act 854) | MY_ws_2026-09-13 | my-csa2024-001 | MY_ws_2026-09-14 |
| my-cca1997-001 (Act 563) | MY_ws_2026-09-13 | my-cca1997-001 | MY_ws_2026-09-14 |
| my-cpc-001 (Act 593) | MY_ws_2026-09-13 | my-cpc-001 | MY_ws_2026-09-14 |
| my-soa2012-001 (Act 747) | MY_ws_2026-09-13 | my-soa2012-001 | MY_ws_2026-09-14 |
| my-ita1967-001 (Act 53) | MY_ws_2026-09-13 | my-ita1967-001 | MY_ws_2026-09-14 |
| my-csr2024-001 (P.U.(A) 2024) | MY_ws_2026-09-13 | my-csr202460e1-001 | MY_ws_2026-09-14 |
| my-pdps2015-001 (JPDP.100-1/1/10) | MY_ws_2026-09-13 | my-pdps2015-001 | MY_ws_2026-09-14 |
| my-pdpr2013-001 (P.U.(A) 335/2013) | MY_ws_2026-09-13 | my-pdpr2013-001 | MY_ws_2026-09-14 |
| my-gtrm2023-001 (SC-GL/2-2023) | MY_ws_2026-09-13 | my-gtrm2023-001 | MY_ws_2026-09-14 |
| my-cso2025-001 (P.U.(A) 2025) | MY_ws_2026-09-13 | my-cso2025-001 | MY_ws_2026-09-14 |
| my-rmtpd2025-001 () | MY_ws_2026-09-13 | my-rmtpd2025-001 | MY_ws_2026-09-14 |
| my-cpca2023-001 (Act A1692) | MY_ws_2026-09-13 | my-cpca2023-001 | MY_ws_2026-09-14 |
| my-cpca2024-001 (Act A1722) | MY_ws_2026-09-13 | my-cpca2024-001 | MY_ws_2026-09-14 |
| my-cpca2025-001 (Act A1751) | MY_ws_2026-09-13 | my-cpca2025-001 | MY_ws_2026-09-14 |
| my-soa2024-001 (Act A1736) | MY_ws_2026-09-13 | my-soa2024-001 | MY_ws_2026-09-14 |
