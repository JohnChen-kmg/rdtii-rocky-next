# Lao OCR throughput on this machine, 2026-09-22

Measured to size W4 in `PLAN.md`, because the Lao scans are the only part of this stage whose wall
clock runs to hours. Not an accuracy measurement: no ground truth exists yet (W11).

## Setup

| | |
| :---- | :---- |
| Document | `LA_corpus_2026-09-21\raw\la\la_859\20260921T0101Z__scanned.pdf`, `la-la859-001`, 187 pages, use `evidence` |
| Pages | 4 consecutive body pages for the per-page figures; 48 to 96 page slots, cycling pages 5 to 184, for the throughput figures |
| Code | `code\config\ocr\tesseract_engine.py` at commit `92a5e9d`, its own `_render_page` and `_preprocess`: 300 DPI through pypdfium2, grayscale, autocontrast, `binarize@180` |
| Engine | Tesseract 5.4.0.20240606, `C:\Program Files\Tesseract-OCR` |
| Pack | `lao.traineddata` from tessdata_best, 13.5 MB, and `lao_fast.traineddata`, 7.1 MB, both still in the scraping session's scratchpad. **Neither is in the repo or in Program Files yet** |
| Machine | 28 logical processors, 31.7 GB RAM, 11.9 GB free at the time. `OMP_THREAD_LIMIT=1` per worker |
| Scripts | `ocr_time.py` and `ocr_par.py` in this session's scratchpad. Re-create them from the figures below if they are needed again |

## Per page, one process, stage settings

| Step | Seconds |
| :---- | ----: |
| Render at 300 DPI | 0.05 |
| Grayscale, autocontrast, binarize | 0.03 |
| `image_to_data`, the confidence pass | 1.34 |
| `image_to_string`, the text pass | 1.21 |
| **Total as the stage runs today** | **2.63** |
| Single pass, text only | 1.29 |

Output per page: 1,227 to 1,537 characters, 745 to 1,029 of them Lao script.

The scraping pilot's 1.7 s a page (LA NOTES line 403) is consistent with one pass plus overhead. The
stage is slower because it OCRs every page twice.

## Throughput, and the projection to the Lao evidence scans

19,058 pages is the evidence-use Lao scan count measured on 2026-09-22.

| Workers | Passes | Pack | Pages/s | 19,058 pages |
| ----: | :---- | :---- | ----: | :---- |
| 1 | 2 | best | 0.39 | 13.7 h |
| 12 | 2 | best | 3.86 | 1.4 h |
| 16 | 2 | best | 4.15 | 1.3 h |
| 24 | 2 | best | 4.95 | 1.1 h |
| 24 | 1 | best | 9.32 | 0.6 h |
| 24 | 2 | fast | 8.18 | 0.65 h |

Scaling flattens after about 12 workers. The whole Lao corpus, 24,773 pages, is about 1.4 to 1.8 hours
at 12 to 16 workers, against about 18 hours as the code runs today.

## Two findings that change the plan

1. **Tesseract worker processes crash intermittently under parallel load.** Exit code 3221225477,
   which is an access violation, killed the pool twice: once at 24 workers and once at 20, while 24
   workers succeeded on a re-run and 12 and 16 were clean. The same page succeeds on a retry, so it is
   load-related, not a bad page. **W4 must retry a failed page, keep the pool alive, and record which
   pages were retried.** A per-page cache makes a killed run resumable rather than lost.
2. **Mean word confidence on clean Lao body pages is 58 to 65.** The floor of 60 proposed in W3 would
   flag most good Lao pages. Set the floor per script, from measured pages, or the signal is noise.

## What this does not tell us

Nothing about accuracy. The characters come back as Lao script in the right volume, which is what the
scraping pilot already found. Whether they are the right characters needs W11.
