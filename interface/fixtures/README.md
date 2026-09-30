# Interface fixtures

A slice of the real mapping run `run_2026-09-27`, copied 2026-09-29. **Real shapes, not invented
ones**, so that when mapping closes the interface changes a path and nothing else.

| Path | What it is |
| :---- | :---- |
| `submission/records_<E>.csv` | The 14 host columns, in the host's order, UTF-8 with BOM. One file per economy |
| `submission/records_<E>.json` | The same rows as JSON |
| `submission/records_TL_pillars_other.csv` | Timor-Leste's other ten pillars, from the second output tree. The multi-act gazette case |
| `audit/gloss_<E>.jsonl` | Machine-made English beside the original, for Chinese, Lao and Portuguese. Carries `is_literal` and the model that wrote it |
| `audit/gloss_sections_<E>.jsonl` | The same at section level |
| `run_manifest.json` | `engine` and `git` are what prove the engine swap |
| `rollup/economy_scores_<E>.json` | Nine indicator scores per economy. **7.1 and 7.2 are inverted**: 0 means the economy has a framework |

## Four things these fixtures exist to exercise

1. **A no-provision row carries an empty Discovery Tag**, not an empty snippet. It still has a law
   name and a URL. An interface that filters on a missing snippet will show it as a scored row.
2. **Three scripts**: Chinese, Lao and Portuguese. A row's text is in the language of the law, and the
   English sits in the gloss file, labelled machine-made. The original is the evidence and must never
   be replaced by the gloss.
3. **Both Discovery Tag values**, NEW and KNOWN, so both render.
4. **Timor-Leste twice**, pillars 6 and 7 from one tree and the other ten pillars from another. They
   are separate runs and a single reader will miss one of them.

## The real thing

`C:\Users\woshi\Desktop\rdtii-finale-p3-runs\run_2026-09-27\out\` and `...\out_tl52\`.
318 rows, 263 scored. Point the interface's data setting there when mapping settles.

## Extended 2026-09-29 for the interface

- `submission/records_<E>.json` added, sliced from the real run to the rows the CSVs hold. The JSON carries
  `_provision_id`, which is the join key to the gloss files, and `raw_context`, the text around the quote.
- `audit/gloss_<E>.jsonl` and `gloss_sections_<E>.jsonl` were extended with the real run's lines for the rows
  the CSVs hold, so every non-English fixture row that was glossed in the run finds its English here. The
  original 12 lines per file were kept. Timor-Leste's lines come from both arms.
- `verify/verified_<E>.jsonl` added for all six economies, sliced to the fixture rows: the mapper, the verifier
  and the escalation reviewer, each with their own reason. No-provision rows have none, by construction.
