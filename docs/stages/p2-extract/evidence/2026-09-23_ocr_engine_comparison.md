# OCR engines compared, 2026-09-23

Four engines over the same pages, measured per script: Tesseract with each of its two pack sets, and
two local vision-language models. Run on this machine, offline, with no proprietary service. Scripts: `experiments\ocr_bench.py`, `experiments\build_twins.py`,
`experiments\scan_quality.py`. Raw output: `experiments\results\`.

## What was measured, and against what

Nobody on this project reads Lao, so the usual answer, a hand-keyed gold page, was not available.
Three references were used instead, and each is labelled for what it is.

| Reference | What it is | Size | Honest limit |
| :---- | :---- | :---- | :---- |
| `gold_page` | The Round 1 hand-keyed page of a real Malaysian gazette scan | 1 page, 1,504 chars | English only. The only reference that satisfies `cer.meets_rubric` |
| `rendered_twin` | A native-text page rendered to an image and OCR'd back | 27 pages, 74k chars | **Optimistic.** A clean render is easier than a gazette scan. Never a scan measurement |
| Real scans | The production input, checked two ways that need no transcription: does OCR give back the portal's own title, and do article numbers run in sequence | 498 pages over 85 documents | Measures recognition where it matters, at scale |

**The text layer was verified, never assumed.** Of 70 native Lao PDFs, only 24 carry real Unicode
Lao. 44 are mojibake (0 Lao characters) and at least one, `la-la1022-001`, is a legacy 8-bit font
mapped into the Lao Unicode block: it looks like Lao, is a substitution cipher, and would have
produced a fabricated error rate. `build_twins.py` rejects both classes by counting common against
rare consonants.

## Result, per engine and script

CER raw is order-sensitive. char F1 is order-insensitive: which characters came back, ignoring where
they landed. Both are reported because a twin reference carries the PDF's own reading order, which on
a two-column page is not the order anyone reads in.

| Engine | Script | Reference | Pages | CER raw | char F1 | In expected script | s/page |
| :---- | :---- | :---- | ----: | ----: | ----: | ----: | ----: |
| Tesseract `best` | Lao | twin | 12 | 0.178 | **0.946** | 100% | 1.92 |
| Tesseract `fast` | Lao | twin | 12 | 0.183 | 0.943 | 100% | **0.95** |
| **qwen2.5vl:7b** | **Lao** | twin | 12 | **1.782** | **0.076** | **36%** | 27.3 |
| **gemma3:12b** | **Lao** | twin | 4 | **3.900** | **0.008** | **0%** | 48.0 |
| Tesseract `best` | Portuguese | twin | 9 | 0.225 | 0.943 | 100% | 3.73 |
| Tesseract `fast` | Portuguese | twin | 9 | 0.226 | 0.937 | 100% | 1.67 |
| qwen2.5vl:7b | Portuguese | twin | 9 | **0.184** | 0.883 | 100% | 15.0 |
| Tesseract `best` | English | twin | 6 | 0.036 | 0.999 | 100% | 1.41 |
| Tesseract `fast` | English | twin | 6 | 0.037 | 0.998 | 100% | 0.75 |
| qwen2.5vl:7b | English | twin | 6 | 0.037 | 0.998 | 100% | 8.33 |
| **Tesseract `best`** | **English** | **gold_page** | 1 | **0.0047** | 0.998 | 100% | 1.90 |
| Tesseract `fast` | English | gold_page | 1 | 0.0047 | 0.998 | 100% | 1.14 |
| qwen2.5vl:7b | English | gold_page | 1 | 0.0106 | 0.989 | 100% | 8.07 |

## The three findings that decide the engine

**1. The vision model cannot read Lao, and fails in the worst possible way.** `qwen2.5vl:7b`
transliterates Lao into **Thai script**: 36% of returned letters are in the expected script, char F1
is 0.076, and it returns 142% of the reference length. It is not garbled output a checker would
catch, it is fluent, confident text in the wrong script. Sample, where the reference reads
`ມາດຕາ 4 ອົງການຄຸ້ມຄອງ…`:

```
พะทกิ ๒
พะละบิดยาด, สิค, ซั้นที่ และ ถอมรับผิดชอบอยู่อุภามจัดตั้ง
มาตา 4 อิภามถุ่มถอถ้ามอมไม่ ...
```

It is reading the page — `มาตา 4` is `ມາດຕາ 4`, article 4 — and writing it in the wrong script.
Under D1 a snippet must be a character-exact substring of the frozen text, so this engine cannot
produce a citable Lao provision at all.

**And the model that knows Lao best cannot read it.** `gemma3:12b` was added to this comparison
afterwards, because it won the translation test on Lao — chrF 0.658 against qwen2.5's 0.561,
`2026-09-23_translation_comparison.md`. As an OCR engine it is **worse than qwen2.5vl, not
better**: zero Lao characters on every page, 390% character error rate, and 48 seconds a page. It
writes Lao pages out in **Khmer** (`មាត្រា`, the Khmer word for "article") on one page and in Thai on
another, where it ran to 23,467 characters — 342% of the page — before degenerating into a repeating
loop.

**Knowing a language is not the same as reading its script from pixels.** Gemma 3 understands Lao
well enough to translate it better than any other local model here, and still cannot transcribe a
Lao page. The two capabilities come apart, and so do the tools: Tesseract reads the pixels, and a
language model is only useful once someone else has turned them into characters.

**A configuration trap worth recording:** at Ollama's default context the model returned 22
characters and looked useless on every script. With `num_ctx` set explicitly it returns full pages.
The English failure was ours; the Lao failure is the model's. Round 1 hit the same default.

**2. `tessdata_fast` is as accurate as `tessdata_best` and twice as fast.** On real Lao scans the two
are within half a point on every measure. `fast` is also 6.4 MB against 13.5 MB per language, which
matters for a repository that must clone inside the thirty-minute test.

| Pack | Title recovery, mean | Article sequence agreement | s/page |
| :---- | ----: | ----: | ----: |
| `best` | 0.891 | 0.856 | 1.92 |
| `fast` | 0.887 | 0.855 | 0.95 |

**3. On real Lao scans, recognition is good and the citation is the weak point.** 60 evidence-use Lao
documents, 349 pages:

| Measure | Result |
| :---- | :---- |
| Title recovery against the portal's own Unicode title | mean **0.891**, median 0.899. 55 of 60 above 0.80, **none below 0.50** |
| Article-number sequence agreement | **0.856** — 95 of 658 article numbers break the sequence |

Portuguese scans, 25 documents, 149 pages: title recovery mean 0.866, median 0.913; sequence
agreement 0.906.

The sequence figure is the one to act on. Article markers survive OCR well — `ມາດຕາ` was found at
line start 19 times out of 19 in the Cyber Security Law — but the **digits after the marker are
misread**: 30 read as 90, 32 as 92, 38 as 88, 55 as 585. A citation built from the OCR'd digit would
name the wrong article about one time in seven, and "a real act cited to the wrong section scores
zero". The number is recoverable from position, because articles run 1, 2, 3.

## Is Tesseract actually good at Lao, or just the only one left?

Both, and the distinction matters for what the submission may claim.

**Our preprocessing is not the limit.** Eight variants swept over the same Lao pages
(`experiments\ocr_tuning.py`): the fixed 180 threshold the stage uses today, autocontrast alone,
grayscale alone, a per-page Otsu threshold, page-segmentation modes 4 and 6, `lao+eng`, and 400 DPI.
**Every one lands between char F1 0.932 and 0.941.** The suspicion that a hard threshold was erasing
thin Lao tone marks is not supported: Otsu wins by 0.0013 and is slightly faster, so it is worth
adopting as the more principled default, but it is a rounding change. 400 DPI is *worse* and slower.
`lao+eng` is worse and twice as slow.

So about 0.94 character agreement is what this engine does on Lao. It is the engine's ceiling, not a
configuration we can tune our way out of.

**Against the field, that is good.** The only published Lao OCR benchmark, SEA-Vision over 914 Lao
pages, puts the best system at 0.195 normalised edit distance and open-weight systems between 0.25
and 0.82. Our twin figures sit in the same range as the best system there, at zero cost and with
nothing leaving the machine. Lao OCR is simply a field in poor shape.

**Against the rubric, it is not enough, and we should say so.** Char F1 0.94 implies roughly one
character in seventeen wrong; raw CER on the twins is 0.18 to 0.22. The under-5% claim cannot be
made for Lao on this evidence, and `cer.meets_rubric` would refuse it anyway because no Lao
reference is a `gold_page`.

**What OCR quality does and does not put at risk.** It does not touch D1: the snippet is always a
character-exact substring of the text we froze, so every Lao provision remains internally consistent
and auditable against our own stored text. What it puts at risk is fidelity to the *printed*
statute — a perfectly grounded quote can still be a faithful quotation of a misread page — and the
citation, which is why the article number is repaired from sequence and the repair is recorded.

## What this means for the engine declaration

| | Engine | Role |
| :---- | :---- | :---- |
| A | **Tesseract 5.4.0 + `tessdata_fast`** | The default, every script, fully offline |
| B | **qwen2.5vl:7b via Ollama** | The declared second engine. Competitive on Latin scripts — it beats Tesseract on Portuguese raw CER (0.184 against 0.225) — and **must not be used for Lao** |

Both are local and open weights, so the pipeline runs end to end with no proprietary service, which
is what the host requires. A cloud document-AI service is documented as an optional third path and
is not built: Google is the only one that reads Lao at all, it publishes no Lao accuracy figure, and
it would put every document on someone else's machine.

Candidates ruled out, with the reason: **gemma3:12b**, tested as an OCR engine on the strength of
its Lao translation, returns no Lao characters at all and loops. **PaddleOCR** does not support Lao, and `paddle_engine.py`
calls three PaddleOCR 2.x APIs while `pyproject.toml` pins `paddleocr>=3` — it cannot run as
written. **EasyOCR** and **docTR** have no Lao. **Azure Document Intelligence** has no Lao.

## What ships in the repository

Measured after vendoring: `tessdata_best` for the five packs is **58 MB**, `tessdata_fast` for four
is **15 MB**. D7 says the packs ship in the repository so a reviewer needs no network inside the
thirty-minute clean-machine test, and 58 MB is a real cost in a repository that must clone quickly.

**Ship the fast packs only, 15 MB**, since they measure the same, and document the one-line download
for `tessdata_best` for anyone who wants to re-run the comparison. The comparison itself is the
evidence that nothing is lost by doing so.

The rendered twin pages under `experiments\` are 29 MB and stay in the workshop. They are
reproducible from the corpus with `build_twins.py` and do not belong in the repository.

## What is still not measurable

- **A rubric-legal Lao error rate.** `cer.meets_rubric` accepts only `native_twin` or `gold_page`.
  Every Lao figure here is a `rendered_twin` or a scan proxy, and is reported as such. A hand-keyed
  Lao page by someone who reads Lao remains the only route to the under-5% claim.
- **Any Chinese error rate.** China's corpus holds no scans, so there is no page to measure. Two
  MIIT PDFs are image-only and would need `chi_sim`, which is now vendored but unmeasured.
- **Parallel behaviour of the vision model.** Only Tesseract has been run at scale here.

## A defect this comparison found in our own harness

`cmd_pilot` hard-codes `cer_method="gold_page"` (`code\src\rdtii_p2\cli.py:786`). A twin measurement
run through it would be labelled a gold page and would **pass `meets_rubric()`** — the tool would
make the under-5% claim on a reference that does not support it. `pilot` needs `--cer-method`, and
`CerReport` needs `script`, `seconds_per_page` and `chars_returned`, before any of these numbers
reach the submission.

Second defect: `cer.py` normalises by collapsing whitespace but keeping it. Lao and Chinese do not
space between words, and Tesseract inserts spaces at glyph clusters. Measured on this machine: a
15-character Lao string with two spurious spaces and **no recognition error at all** scores CER
0.1333 with whitespace kept, 0.0000 with it stripped. At a 5% bar that decides pass or fail.
