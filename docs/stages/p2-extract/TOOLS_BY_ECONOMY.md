# Which tool reads, and which tool translates, in each economy

**Settled 2026-09-23** from the measurements in `evidence\2026-09-23_ocr_engine_comparison.md` and
`evidence\2026-09-23_translation_comparison.md`. Every tool named here is local and open weights, so
the pipeline runs end to end with no proprietary service.

## The short version

| Economy | Documents | What actually needs OCR | OCR tool | Translation tool |
| :---- | ----: | :---- | :---- | :---- |
| **Lao PDR** | 1,762 | **1,404 documents, 19,058 pages** — the whole corpus is images | **Tesseract 5.4.0, `lao`, `tessdata_fast`** | **None in extraction.** The gazette's own English for 53 laws; `gemma3:12b` gloss elsewhere, labelled, never evidence |
| **Timor-Leste** | 1,921 | 29 documents, 822 pages | **Tesseract, `por`, `tessdata_fast`** | None needed. Optional gloss: `gemma3:12b` |
| **China** | ~1,092 | **Nothing in the corpus.** 2 image-only MIIT PDFs, and whatever the live test fetches | **Tesseract, `chi_sim`** — provisioned, unmeasured | None needed. Optional gloss: `gemma3:12b` or `qwen2.5:14b` |
| **Malaysia** | 1,391 | 17 documents after linkage rows are skipped | **Tesseract, `eng`** (`msa` for the Malay files) | **None.** See the note below |
| **Singapore** | 738 | 1 document | **Tesseract, `eng`** | None — English |
| **Australia** | 1,278 | None — 793 HTML, 485 native PDF | None | None — English |

**Engine B, the declared alternative, is `qwen2.5vl:7b` via Ollama** and applies to the Latin-script
scans above: Malaysia, Timor-Leste, Singapore. It is competitive there — it beats Tesseract on
Portuguese raw CER, 0.184 against 0.225 — and it **must never be pointed at Lao**, where it returns
36% of its letters in Thai script.

## Why each choice, with the number behind it

### Lao PDR — the only hard case

| | |
| :---- | :---- |
| Why Tesseract | It is the only engine tested that returns Lao characters at all. `qwen2.5vl:7b` writes Lao in Thai (0% to 36% in-script); `gemma3:12b` writes it in Khmer and then loops; PaddleOCR, EasyOCR, docTR and Azure have no Lao; Google Document AI is the only cloud service that does, and it is proprietary |
| Why `fast` over `best` | Measured on real scans: title recovery 0.887 against 0.891, sequence agreement 0.855 against 0.856 — a difference of half a point — at **half the time** and **half the repository size** |
| How good it is | About 94% character agreement; 0.891 title recovery on real scans; **0.856 article-number sequence agreement**, so roughly one article number in seven is misread and repaired from position |
| What it cannot claim | The under-5% error rate. No Lao reference is a `gold_page`, and the measured figures do not support it |
| Tuning | Eight preprocessing and mode variants all landed within 0.3 points. Otsu thresholding is marginally better and faster than the current fixed threshold, and worth adopting; nothing else moves |

### Timor-Leste, Singapore, Australia, Malaysia — routine

Latin script, and Tesseract reads the real Malaysian gazette scan at **CER 0.0047** against a
hand-keyed page. Timor-Leste's scans measure 0.866 title recovery and 0.906 sequence agreement. The
OCR workload is tiny in all four: 47 documents between them, against Lao's 1,404.

### China — no OCR at all, for now

The corpus is 943 Word documents and 140 HTML pages, with **no scans**. The `chi_sim` pack is
vendored for two image-only MIIT PDFs and for whatever the live test fetches on 15 October, and it
is **unmeasured**: there is no Chinese page with a reference to measure against, so the honest report
is `cer_method: none`.

## Translation, in one place

**Extraction translates nothing, in any economy** (D5). The verbatim snippet is always the source
language, at the recorded offsets. What follows is for whoever displays or reads a provision.

| Economy | Is a gloss needed? | If one is shown |
| :---- | :---- | :---- |
| **Lao PDR** | The only real case | **Prefer the publisher's own English** — the gazette published it for 53 laws, 1,513 pages, already on disk. Otherwise `gemma3:12b`: chrF 0.658 against that publisher English, where `qwen2.5:14b` reaches 0.561 and `llama3.1:8b` 0.338 |
| **China** | Convenience only | `gemma3:12b` or `qwen2.5:14b`. The two agree with each other at **0.836**, and the Chinese gloss of the Cybersecurity Law was checked by hand and is legally precise |
| **Timor-Leste** | Convenience only | Same models; inter-model agreement **0.846** |
| **Malaysia** | **No** | The corpus is English. See below |
| **Singapore, Australia** | No | English |

### Malaysia, and the seven acts that are not in English

Malaysia's AGC publishes an English version, so there is no translation task — with one correction
to "all of them have an English version": **we do not hold English for seven acts.** The English link
served the Malay file, which is why collection flagged them `language_mismatch`, and no act in the
corpus has a second copy in the other language. One of them is **Act 680, the Electronic Government
Activities Act 2007**, which is in scope for a digital-trade index.

The fix is not a translation tool. Mark those seven `language_of_source: msa` from the crawler's own
flag — reading a crawler field, not detecting a language, so D3 holds — and ask collection whether
AGC's English text can be re-fetched.

## What is not measured, and must be reported as such

- **Any Chinese error rate.** No scans, no reference.
- **Any rubric-legal Lao error rate.** Every Lao reference is a rendered twin or a scan proxy, never
  a hand-keyed gold page.
- **Any cloud engine.** Named as optional, never built, never measured.
- **Parallel behaviour of anything but Tesseract.**
