# Code audit of the Round 1 extraction stage, 2026-09-22

What in `stages\p2-extract` breaks on the finale inputs, with file and line. Read on the repo at
`92a5e9d`, branch `finale`. Branch `finale` and `master` do not differ under `stages/p2-extract`, and
no finale commit has touched the stage. Paths below are relative to `code\`, the working copy, which
is byte-identical to the stage at that commit (`PROVENANCE.tsv`).

This note is also the instrument impact record that `NOTICE_FOR_OTHER_STAGES.md` section 6 asks each
workshop for. That list is section 9.

## 1. What the stage is

| Part | Size | Note |
| :---- | :---- | :---- |
| `src\rdtii_p2\` | 3,275 lines | `cli` 887, `segment` 492, `extract_fields` 453, `tag_batches` 273, `parse_html` 267, `normalize` 188, `ingest` 172, `emit` 154, `cer` 130, `ground` 73, `router` 66, `parse_pdf_native` 55. `ocr_scanned.py` and `twin.py` are stubs |
| `config\` | 554 lines | Settings, the OCR engines (Tesseract, Paddle, Azure), the LLM clients (Anthropic, Ollama) |
| `tests\` | 14 files, 82 tests | Baseline in this copy, 2026-09-22: **80 passed, 2 skipped**, run with the Round 1 venv at `RDTII\pipeline-data\rdtii-p2-extract\.venv` and `PYTHONPATH=src;.`. The system Python lacks `jiwer` |
| CLI | 5 commands | `run`, `tag-corpus`, `validate`, `demo`, `pilot` (`cli.py:810-875`) |

The flow is `load_manifest` → `route` (lane A html, B native PDF, C scanned PDF) → `normalize_pages`
→ `segment` → `build_record` with `copy_grounded` and `verify` → `provisions.jsonl`, `laws.jsonl`,
`doc_status.jsonl`, `source_text\`. The LLM fills four soft tags only (`extract_fields.py:28-42`).
Quotes, offsets and citations are deterministic, so grounding needs no model.

## 2. The ingest gate rejects every finale row

| Where | What | Effect |
| :---- | :---- | :---- |
| `00_contracts\schemas\manifest.schema.json:37`, `:41` | `doc_id` `^(sg\|au\|my)-…`, `economy` enum `SG, AU, MY` | Every Lao and Timorese row fails. The ids already fit the widened pattern `^[a-z]{2}-[a-z0-9]+-\d{3}$`: 1,762 of 1,762 LA and 1,921 of 1,921 TL, counted 2026-09-22 |
| `manifest.schema.json:7` | `additionalProperties: false` | Every contract 0.3.0 row fails |
| `provision.schema.json:21-23`, `laws.schema.json:15-16` | The same economy and id pins | Output rows for LA, TL and CN fail `validate` |
| `laws.schema.json:20`, `:23` | Pillars `[6, 7]`, indicators `^P[67]-I[1-5]$` | Decimal ids fail |
| `ingest.py:28-35` | The coercion tables hold 0.2.0 fields only | A new column arrives as `""`, not null |
| `ingest.py:135-139`, `cli.py:627-636` | Superseded rows found by the substring "superseded by" in `crawl_notes` | The finale corpora carry no such notes. They list superseded copies in `superseded.jsonl` and leave them out of the manifest |
| `ingest.py:90-98`, `:145` | `check_contract_major` compares the major version of row 0 only | A 0.3.0 manifest passes the version check and then fails the schema |
| `cli.py:178-179`, `:420`, `extract_fields.py:433-434` | URLs built from `source_url` | Never read `citation_url`. On LA, `source_url` is unencoded on 1,374 rows (LA NOTES section 6) |
| `cli.py:407-408` | `pillar_hint` mapped to 6, 7 or both only | Other pillars dropped silently |

## 3. Nothing segments a non-English statute

`segment.py` is common-law and English. When nothing matches, the document gets zero records and the
status `zero_provisions`. There is no whole-document fallback.

**Measured on Timorese documents, 2026-09-22, and it is worse than silence.** Four principal acts
produced 3 to 8 spans each, all cited `s.1`, `s.2`, `s.3`, against documents whose articles are
`Artigo 1.º`. A ceremonial notice produced 25 spans cited `s.01` to `s.25`, of which 20 were empty and
the rest quoted a list of organisation names. So the failure is not zero provisions, it is **a handful
of confidently wrong citations**, which is a C2b failure rather than a gap. Section 10 explains why the
headings never reached the segmenter at all.

| Line | Pattern | Why it fails |
| :---- | :---- | :---- |
| 25, 26 | `^PART`, `^Division` | English heading words |
| 29-33, 38 | Numbered sections need a Latin capital after the number | Never true in Lao or Chinese, and not the Portuguese `Artigo 1.º` shape |
| 40-42, 115, 245-249 | Month names, `Endnotes`, FIRST to TENTH | English |
| 46 | Subsections `(1)` only | No `a)`, `1 -`, `（一）` |
| 52, 54, 261, 264 | `SCHEDULE`, `Schedule N` | English |
| 293 | "australian privacy principle" | Australia only |
| 337 | `isupper()` | Meaningless for Lao and Chinese |
| 309-310, 387, 438, 469 | Citations `s.N`, `s.N(sub)`, `sch.N cl.`, `para` | No `Artigo`, ມາດຕາ, 第…条 |

`parse_html.py` has the same shape at lines 75, 104, 172-173, 194 and 239, and supports one portal
only, `legislation.gov.au` (`parse_html.py:255-257`). Any other host raises and the document is
`parse_failed`.

## 4. Normalisation is English-shaped in five places

| Line | Pattern | Effect |
| :---- | :---- | :---- |
| `normalize.py:40` | De-hyphenate `([a-z])-\n([a-z])` | **Corrupts Portuguese enclitics.** `aplica-\nse` becomes `aplicase`. Misses accented letters |
| `normalize.py:44`, `:162`, `:169-170` | Unwrap before `[a-z]`, sentence end `[.:;—]` | ASCII only. No `。` or `；`. Lao and Chinese keep hard line breaks inside sentences, which is faithful but ragged |
| `normalize.py:36-38` | U+FFFD repairs look for Latin letters | English only |
| `normalize.py:45` | Control characters C0 and DEL only | Zero-width spaces and soft hyphens survive. TL NOTES says the older Timorese PDFs carry soft hyphens inside words |
| `normalize.py:50` | "schedule … continued" furniture | English |

## 4a. The furniture detector deletes every civil-law article heading

**Measured 2026-09-22. The worst single defect for the finale, and it is upstream of the segmenter.**

`detect_furniture` (`normalize.py:85-99`) masks digits in each line, then drops any line whose masked
shape appears on at least 30% of pages. In a civil-law statute every article heading has one shape, so
the mask collapses them all into one:

| Document | Pages | Shapes dropped |
| :---- | ----: | :---- |
| `tl-ldcn-001`, Lei da Concorrência | 11 | **`Artigo #.º`**, `Jornal da República`, the page line |
| `tl-p-001`, Pesticidas | 12 | **`Artigo #.º`**, **`Secção I`, `Secção II`, `Secção III`**, `Jornal da República`, the page line |
| `tl-aoccdpndenaesr-001` | 78 | **`Artigo #.º`**, `Jornal da República`, the page line |

In `tl-ldcn-001` the raw page text holds 41 `Artigo` headings. After `normalize_pages` it holds
**none**. Only lowercase cross-references such as "nos termos do artigo 8.º" survive, because they sit
inside a sentence.

English statutes escape by accident: a section heading such as `12.—(1) Interpretation` carries its own
words, so no two masked lines are equal.

**Lao and Chinese will behave like Portuguese**, because ມາດຕາ and 第…条 headings repeat the same shape
on every page. **So W6 must land before W5**, or the new segmenters will be matching against text with
the headings already removed.

The fix is not to weaken furniture detection, which earns its place on gazette page lines. It is to
never drop a line that matches an article, chapter or section heading in the document's own language.

Furniture detection is otherwise language-neutral.

## 5. OCR runs in one language, and claims an English error rate for every script

| Where | What |
| :---- | :---- |
| `config\settings.py:35`, `:75` | `ocr_lang` is one global value, default `eng` |
| `config\ocr\factory.py:25`, `:32` | The only reader of it. Paddle gets `lao`, `chi_sim` or `por` unmapped |
| `cli.py:143`, `:742`, `:771` | The three `get_ocr` call sites. `_parse_doc` never sees the manifest row |
| Nowhere | `TESSDATA_PREFIX` is set by hand, per the stage README, lines 22-24. `eng` is gitignored in `fixtures\tessdata_local` (`.gitignore:31-32`), so `msa+eng` fails on a clean clone |
| `ingest.py:154-158` | Preflight checks the Tesseract binary, never the language packs |
| `config\ocr\tesseract_engine.py:32-35` | Fixed binarisation at 180, no deskew, no `--psm`. Thin Lao marks and CJK strokes are at risk. Measure before changing |
| `tesseract_engine.py:62`, `:66` | **Two full OCR passes per page**, `image_to_data` then `image_to_string` |
| `cer.py:99`, `cli.py:297-301` | `ENGINE_FIXTURE_ESTIMATE_CER = 0.0272`, the Malaysian English gazette figure, stamped on every uncached scanned document. On a Lao document that is a false claim. The schema requires a number for scanned documents (`provision.schema.json:64-67`) |
| `cer.py:25-27` | CER keeps whitespace. Tesseract's spaces between Lao or Chinese characters count as errors |
| `config\ocr\paddle_engine.py:26`, `:41` | Written against the Paddle 2.x API while `paddleocr>=3` is pinned. Probably broken. Do not declare it as a swap option until it runs |

## 6. China's formats have no lane

- **No `.docx` or `.doc` support.** `router.py:21` knows `html`, `pdf_native` and `pdf_scanned` only.
  China's national database layer is 942 `.docx` and 3 `.doc` inside 11 zips.
- **HTML is read as UTF-8 unconditionally** (`parse_html.py:53`). A GBK page raises.
- **HTML whitespace collapse inserts spaces between inline spans** (`parse_html.py:44-46`). Chinese
  has none, so a quoted snippet gains spaces the page does not show.
- **NFC rewrites CJK compatibility ideographs** (U+F900 to U+FAD9). The frozen text then differs from
  the source bytes. Rare in statutes. Disclose rather than fix.

## 7. It cannot run a large corpus fast or safely

| Where | What | Effect |
| :---- | :---- | :---- |
| `cli.py:258` | One process, one document at a time | The Round 1 figure of 12,292 pages in about 100 minutes came from 6 workers run outside this code (`docs\HANDOFF2_NOTES_2026-07-13.md:69`) |
| `emit.py:35-51`, `:113-117` | Outputs are read, merged and rewritten at the end of each run | Two runs on one output folder: the last writer wins |
| `cli.py:254` | All records held in memory to the end | A crash loses everything except `source_text` |
| `cli.py:135-142`, `emit.py:73-84` | The OCR cache is the normalised `source_text`, keyed on `doc_id` only | Goes stale when the language, the engine or the file changes. Raw OCR is never kept, so a normalisation change means OCR again |
| none | No cache-clear operation | Checklist item 26 and dashboard D15 need one |
| `cli.py:245` | `preflight(..., needs_llm=True)` hard-coded | `run --skip-tags` still fails without a pulled Ollama model or an Anthropic key |
| `cli.py:56`, `:730`, `:874`, `settings.py:67` | `logs\`, `fixtures\ocr_reference`, `.env` resolved from the working directory | Works only when run from the stage folder |
| `cli.py:53` | Logs to stdout | A cp1252 console raises `UnicodeEncodeError` on Lao or Chinese titles unless `PYTHONUTF8=1` |

No absolute Desktop path is in the stage. The only hit is `.gitignore:23 Desktop.ini`.

## 8. Claims in the stage docs the code does not back

- "Content-exact tag grafting" (`STAGE_GUIDE.md:54`, `:72`, `README.md:119`). No `.py` contains it. It
  was presumably an external script. Either commit it or drop the sentence before the release.
- `twin.align` is a stub (`src\rdtii_p2\twin.py`), though `STAGE_GUIDE.md:56` describes it as working.
- `bs4`, `lxml` and `tqdm` are declared in `pyproject.toml` and never imported. Remove them, or the
  licence table in Word Section 3 lists dependencies the tool does not use.
- `MAX_COST_USD_PER_DOC` is read and never enforced.
- `TAG_BATCH_SIZE` defaults to 10 in `load_settings` (`settings.py:82`) and to 1 in the class and in
  `.env.example`.

## 9. Instrument impact, per the notice of 2026-09-13

The instrument is not handed off yet (`rdtii-finale-0-instrument\HANDOFF.md`), so nothing below breaks
today. It breaks on the day the crawler writes decimal ids.

| Notice item | Where it bites | Change |
| :---- | :---- | :---- |
| Decimal ids, never parsed as numbers | `laws.schema.json:23` pattern `^P[67]-I[1-5]$`. `cli.py:422` splits `indicator_hints` and copies the tokens | Accept both shapes as text. Seed rows in LA and TL still carry `P6-I3` style hints, 11 and 8 rows |
| All twelve pillars | `cli.py:407-408`, `laws.schema.json:20`, `manifest.schema.json:73` | Widen to pillar numbers as text, as `CONTRACT.md` section 3.2 proposes |
| Keep article and paragraph on every provision | `segment.py` citations | Already true for English. The new segmenters must keep it, in each tradition's own form |
| Principal against amending, in force against draft | Not read today | Carry `document_kind` and `legal_status` from the corpus into `laws.jsonl` so mapping can drop zero-score rows |
| Signature keywords English only | Not extraction's code | Mapping's prefilter. Noted because it is why extraction must not translate the frozen text to help it |

**Requests to the instrument: none.** Extraction reads no instrument file. The soft-hint tag enum at
`extract_fields.py:28-31` is pillar 6 and 7 shaped, and that is extraction's own vocabulary, not the
instrument's.
