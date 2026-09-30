# Extraction plan to 30 September

**Written 2026-09-22. Revised 2026-09-23** after collection closed, after the tool experiments, and
after the developer settled four decisions. It replaces the plan of 2026-09-12, kept at
`notes\2026-09-12_PLAN_superseded.md`.

Seven days to code freeze. Hours are working hours for one developer. Work packages are numbered W1
to W15 so they cannot be confused with the old plan's steps 1 to 14.

## Settled on 2026-09-23

| Decision | Choice | Where the evidence is |
| :---- | :---- | :---- |
| OCR engine A | **Tesseract 5.4.0 + `tessdata_fast`**, every script | `evidence\2026-09-23_ocr_engine_comparison.md` |
| OCR engine B, declared | **qwen2.5vl:7b via Ollama** — Latin scripts only, **never Lao** | same |
| Proprietary OCR | Documented as an optional third path, **not built**. Both declared engines are local | developer, 2026-09-23 |
| Translation | **Compared and recommended, not built.** D5 stands | `evidence\2026-09-23_translation_comparison.md` |
| ~220 flagged documents | **Carry and mark.** Exclude only the 87 that are provably not the law they are filed under | developer, 2026-09-23 |
| Round 1 output | **Not reused. Everything extracted fresh** | developer, 2026-09-23 |
| The output format | **Settled**, one shape for six economies | `OUTPUT_FORMAT.md` |

The evidence behind every statement here is in two dated notes:

- `notes\2026-09-22_inputs_and_asks.md`: the six corpora, where language and use actually live, and
  what the other workshops ask of this one.
- `notes\2026-09-22_code_audit.md`: what in the code breaks, with file and line.

Code paths below are relative to `code\`, the working copy of `stages\p2-extract` (decision D9).

## What changed since 12 September

| Then | Now | Consequence |
| :---- | :---- | :---- |
| Three new economies not chosen. Lao and Thai used as placeholders | **Timor-Leste, Lao PDR and China are built** (scraping `CONVENTIONS.md` section 6). Only Lao and China are in the live-test draw | Scripts are Lao, Portuguese and Chinese. Thai work, the Thai gold page and the India case leave the plan |
| Language would arrive as a manifest column | **All six manifests are still contract 0.2.0.** Language is in `law_table.csv` and `links_used\documents.jsonl`, written by the crawler | Read it from there until 0.3.0 lands. D3 holds, because the crawler wrote it |
| Extraction would re-validate Round 1's 411,986 records | **Round 1's `handoff1_v2` is never read again** (scraping decision 17). Each country has a new corpus | Every finale number comes from new runs. 411,986 stays a Round 1 figure |
| Non-Latin segmentation: "cut first" | **All three new economies need it**, or they emit zero provisions | Now the largest single item, and in the freeze minimum |
| Many laws in one PDF: "cut second", one Niue file | **Timor-Leste's gazette issues hold up to 15 acts each.** 911 of 1,921 documents hold more than one | Promoted. An honest fallback exists: single-act issues only |
| Lao OCR untested | **Scraping piloted it on 2026-09-20.** Lao script read cleanly, 1.7 s a page, no error rate measured | The OCR route is settled as Tesseract. The work is language routing, speed and the accuracy evidence |
| China unconsidered | **No manifest.** 942 `.docx` and 3 `.doc` in zips, plus HTML from two ministries | A new intake lane and a manifest someone has to build |
| All twelve pillars possible | **Only pillars 6 and 7 are automated** (developer, 2026-09-20). The rest go to a manual-check register | Extraction still works per document. Hints must accept any pillar, because seeds carry them |

## What the stage must deliver by the freeze

1. **Grounded provisions for all six corpora**, each with `language_of_source`, passing `validate`.
   Every snippet is still a character-exact substring of the frozen text (D1).
2. **A live-test path for Lao and China.** A handful of freshly crawled documents, cold, in minutes,
   with caches clearable from the dashboard.
3. **Honest numbers.** An error rate per script, or a statement that none was measured. Seconds per
   document. No English error rate stamped on a Lao page.

Unchanged from before: D1 no quote no record, D2 the rubric claim scoped in code, D3 language read not
guessed, D5 no translation in extraction.

## Summary

| # | What | Hours | Tier | Needs |
| ----: | :---- | ----: | :---- | :---- |
| W1 | Open the ingest gate to the finale corpora | 5 | 1 | Q2 |
| W2 | Run without an LLM, from any folder, on any console | 1.5 | 1 | |
| W3 | Per-document OCR language, shipped packs, loud failure | 6 | 1 | W1 |
| W4 | Parallel OCR pre-pass with a raw page cache | 5 | 1 | W3 |
| W6 | Normalisation: stop deleting article headings, and fix Portuguese and Lao | 4 | 1 | |
| W5 | Segmenters for Lao, Chinese and Portuguese statutes | 10 | 1 | W1, **W6** |
| W7 | Split Timorese gazette issues into acts | 6 | 2 | Q4 |
| W8 | China intake: `.docx`, `.doc` and ministry HTML | 7 | 1 | Q3 |
| W9 | `language_of_source` in the record, the translation rule in the contract | 2 | 1 | W1 |
| W10 | Cache clear, OCR engine table, seconds per document | 2 | 1 | W4 |
| W11 | Lao accuracy evidence | ~~3 to 5~~ **1** | 1 | **largely done 2026-09-23** |
| W12 | Full runs of six corpora, English regression, validate | 5 | 1 | all of tier 1 |
| W13 | Hand-back to the repo in one commit | 3 | 1 | W12 |
| **W14** | **Flags and exclusions: carry 2,029, exclude 87, write the reasons** | **4** | **1** | W1 |
| **W15** | **The settled output format: schemas, record builder, per-act `laws.jsonl`** | **6** | **1** | W1 |
| | **Tier 1** | **about 60** | | |
| | **With W7** | **about 66** | | |

**Two packages were missing from the 22 September plan.** W14 is the third decision collection
handed over, and the word "flag" appeared once in the whole plan, about OCR confidence. W15 is the
output format itself, which was assumed rather than specified.

**This is more than the old plan's 51 hours, not less.** The old plan's minimum of 30 assumed that
segmentation and multi-law volumes could be cut. On the real three economies they cannot. The honest
reading is that tier 1 needs most of eight working days. If the week slips, cut in the order given near
the end, and say so in the submission rather than discovering it on 29 September.

## If the work runs in parallel

**Total 60 hours, critical path 25.** The packages are mostly independent, so the calendar is set by
the longest chain, not by the sum.

The chain is now **W1 → W9 → W15 → W14 → W12 → W13**, 25 hours: the gate has to open before the record
builder can carry the new fields, the format has to exist before exclusions can be written into it, and
everything has to exist before the full runs and the hand-back. The OCR lane is 13 hours and no longer
sets the calendar, because tonight's work retired most of W3 and all but an hour of W11. Adding W7 does
not lengthen the chain. It costs a lane, not a day.

| Lane | Packages | Hours | Touches, so nobody else may | Blocked by |
| :---- | :---- | ----: | :---- | :---- |
| 1, gate and format, **the critical path** | W1, W9, W15, W14 | 17 | `ingest.py`, `00_contracts\schemas\`, `extract_fields.build_record`, `emit.py` | Q2 |
| 2, OCR | W3, W4, W10 | 13 | `config\ocr\*`, `settings.py`, the new `ocr` command, the cache | |
| 3, text shape | W6, then W5's shared scaffolding | 5 | `normalize.py`, `segment_civil.py` | |
| 3a, 3b, 3c | W5 Lao, Portuguese, Chinese | 3 each | one profile file each, after lane 3 | |
| 4, China | W8 | 7 | `parse_html.py`, a new office-format reader, `router.py` | Q3 |
| 5, evidence | W11 | 1 | `fixtures\ocr_reference\`, `cer.py` | mostly done 2026-09-23 |
| 6, Timorese acts | W7 | 6 | the splitter, `laws.jsonl` writing | Q4, lane 3b |
| serial tail | W12, W13 | 8 | everything | all lanes |

**Three rules make it work.**

1. **Partition by file, not by package.** W1, W3 and W9 all want `cli.py` and `ingest.py`. Two agents
   in one file is how a day disappears. Give each lane its files, and keep `cli.py` edits small and
   sequenced.
2. **Start lane 2 first.** It is the critical path, and it is also the one with hours of machine time
   attached.
3. **Keep one day for the tail.** W12 and W13 are serial by nature, and W12 is where the defects that
   parallel work hid come out.

**Shortening the path further,** if the week is tight: decouple W10 from W12, since the cache-clear
control is a dashboard feature rather than a run requirement, and start W4's pool and cache before W3
finishes, because neither depends on the language map. That takes the chain to about 21 hours.

**Machine time runs alongside.** The six corpora are independent runs. Give each its own `--out`, or
they overwrite each other (`emit.py:35-51`). Total is about 2 to 3 hours, nearly all of it the Lao OCR,
which saturates the CPU on its own, so running the others beside it buys little.

---

## W1. Open the ingest gate to the finale corpora

**5 hours. Blocking.** Today every Lao and Timorese row is refused, and every 0.3.0 row would be.

1. **Widen the three vendored schemas** in `00_contracts\schemas\`:
   - `economy` to `^[A-Z]{2}$`;
   - `doc_id` and `provision_id` to the two-letter class `^[a-z]{2}-[a-z0-9]+-\d{3}$`, which all 3,683
     LA and TL ids already fit;
   - `pillars_in_scope` to 1 to 12;
   - indicator hints to accept decimal text and the legacy `P6-I3` form, since LA and TL seeds still
     carry 19 legacy rows.

   Accept the 0.3.0 columns as optional, so one gate reads both versions.
2. **Add the new columns to the coercion tables** in `ingest.py:28-35`, so an empty cell is null.
3. **Read a corpus's sidecars when the manifest is silent.** Join `law_table.csv` on `doc_id` and
   `links_used\documents.jsonl` on `source_url`. Take `language`, `use`, `document_kind`,
   `legal_status`, `law_name` and `law_number`, in that order of preference: manifest first, then the
   sidecars, then the crawler's per-economy default. Log which one was used for every document. When
   none is present, the value is null, never a guess.
4. **Skip `linkage` rows** (scraping decision 20). Aggregate per document for Timor-Leste, where the
   table is per act: a document is skipped only when every act in it is `linkage`. Skip `not held`
   rows, which have no file.
5. **Superseded:** read `superseded_by` when present. Otherwise the corpus has already excluded the
   superseded copies, so the substring check at `ingest.py:135-139` and `cli.py:627-636` becomes a
   fallback for Round 1 manifests only.
6. **URLs:** read `citation_url` before `source_url` at `cli.py:178-179`, `:420` and
   `extract_fields.py:433-434`.

Done when LA and TL load with zero schema errors, and the same code still loads Round 1's
`handoff1_v2` manifest unchanged.

## W2. Run without an LLM, from any folder, on any console

**1.5 hours.**

- **Ask for the LLM only when tagging.** `preflight` is called with `needs_llm=True` hard-coded
  (`cli.py:245`), so `run --skip-tags` fails without a model or a key.
- **Resolve `logs\`, `fixtures\` and `.env` from the stage folder,** not the working directory
  (`cli.py:56`, `:730`, `:874`, `settings.py:67`).
- **Force UTF-8 output.** A cp1252 console raises on the first Lao title (`cli.py:53`).

## W3. Per-document OCR language, shipped packs, loud failure

**6 hours.** The core of the old plan, kept, with the real scripts.

1. **Build a language map module**, `config\ocr\langmap.py`, from the manifest code to the pack:

| Code | Tesseract | Why |
| :---- | :---- | :---- |
| `lao` | `lao` | Test `lao+eng` on the pilot pages before adopting it. Stamps and reference numbers are Latin |
| `por` | `por` | 29 Timorese scans, 822 pages |
| `zho` | `chi_sim` | No Chinese scans yet. Needed if the live crawl fetches one |
| `eng` | `eng` | |
| `msa` | `msa+eng` | Round 1's side-loaded pack |

2. **Thread the language from `cmd_run` into `_parse_doc`** and `get_ocr` (`cli.py:143`, and the
   `demo` and `pilot` commands). `OCR_LANG` stays as an override for a pilot. It is never the
   silent source.
3. **The packs are vendored, 2026-09-23.** `code\fixtures\tessdata_local\` holds `lao`, `por`,
   `chi_sim`, `eng`, `osd` at `tessdata_best`; `code\fixtures\tessdata_fast\` holds the fast packs.
   Apache-2.0 confirmed at the source, sha256 of each file recorded in the OCR evidence note. They
   were previously in a Claude temp scratchpad, which is session-scoped and deletable.
   **`tessdata_fast` is the default**: measured on real Lao scans it is within half a point of
   `best` (title recovery 0.887 against 0.891, sequence agreement 0.855 against 0.856) at **half the
   time** and half the repository size. Still to do: **set `TESSDATA_PREFIX` in code**, not by hand.
4. **Check the packs in `preflight`** with `pytesseract.get_languages`. A missing pack stops the run
   with the line that fixes it.
5. **Log low-confidence pages, with a floor per script.** Clean Lao body pages measure 58 to 65 mean
   word confidence (`evidence\2026-09-22_lao_ocr_timing.md`), so the floor of 60 the old plan proposed
   would flag most good Lao pages. Set each script's floor from measured pages, or the signal is noise.
6. **Stop claiming an English error rate for every script.** `ENGINE_FIXTURE_ESTIMATE_CER = 0.0272`
   is stamped on every scanned document (`cli.py:297-301`). Make the estimate a table per script. Where
   a script has no measurement, write null with the method `none`, and let the schema allow it
   (`provision.schema.json:64-67`). Make the CER normaliser strip all whitespace for Lao and Chinese
   (`cer.py:25-27`), and record the script in `CerReport` (D6).
7. **Two defects the comparison found in our own harness, both freeze-blocking:**
   - `cmd_pilot` hard-codes `cer_method="gold_page"` (`cli.py:786`). A rendered-twin measurement run
     through it would be labelled a gold page and **pass `meets_rubric()`** — the tool would make the
     under-5% claim on a reference that cannot support it. Add `--cer-method`.
   - Keeping whitespace in the CER normaliser costs **13.3 points on Lao with no recognition error at
     all** (measured: a 15-character string with two spurious spaces scores 0.1333 kept, 0.0000
     stripped). At a 5% bar that decides pass or fail.
   `CerReport` also needs `script`, `seconds_per_page` and `chars_returned`: three of the four
   metrics the developer asked to see are not in it.

## W4. Parallel OCR pre-pass with a raw page cache

**5 hours.** Measured on this machine on 2026-09-22, `evidence\2026-09-22_lao_ocr_timing.md`: the
stage's own engine takes **2.63 s a Lao page**, because it OCRs every page twice
(`tesseract_engine.py:62`, `:66`). The 19,058 evidence-use Lao pages are **13.7 hours in one process
and about 1.3 hours across 16 workers**. Scaling flattens after about 12 workers.

1. **Add an `ocr` command** that OCRs the scanned documents of a manifest across a process pool, one
   Tesseract thread per worker (`OMP_THREAD_LIMIT=1`). **12 to 16 workers, not 20 or more.** Tesseract
   crashed the pool twice with an access violation at 20 and 24 workers, and the same page then
   succeeded on a retry. **Retry a failed page, keep the pool alive, and log the retries.**
2. **Cache raw OCR per page** under `ocr\<doc_id>\`: page text, confidence and seconds. Key the cache
   on `content_sha256`, engine id, language and DPI, so a change to any of them re-OCRs instead of
   silently reusing stale text. Per-document files are written by one worker each, so this is safe in
   parallel where the emit step is not (`emit.py:35-51`).
3. **Make `run` read the cache in lane C,** then normalise. Normalisation can then change without
   another OCR pass.
4. **Keep the double pass for now.** Deriving the text from `image_to_data` alone halves the time,
   but it changes the OCR text of the committed gold pages, so it must re-pass the CER gate. That is a
   tier 3 optimisation.

**Measured in the production configuration on 2026-09-23** — `tessdata_fast`, one pass,
autocontrast, 300 DPI:

| Workers | Pages/s | Lao evidence, 19,058 pp | Whole Lao corpus, 24,773 pp |
| ----: | ----: | ----: | ----: |
| 12 | 12.5 | **25 min** | 33 min |
| 16 | 14.1 | 22 min | 29 min |
| 20 | 15.6 | 20 min | 27 min |

So the Lao OCR is **under half an hour**, not the 13.7 hours the current code would take. The gain
is the fast pack and dropping the second OCR pass, not the worker count. A full pass over all six
corpora is **30 to 45 minutes of machine time**: the 129,000 native pages extract at 1-2 ms each and
China's 943 Word documents parse in 2.1 seconds.

## W5. Segmenters for Lao, Chinese and Portuguese statutes

**10 hours. The largest item. Do W6 first,** or these will be matched against text whose headings have
already been deleted.

Without it the three new economies emit nothing usable. Measured on 2026-09-22, they do not emit
nothing: four Timorese principal acts each produced 3 to 8 spans cited `s.1`, `s.2`, `s.3` against
documents numbered `Artigo 1.º`, and one ceremonial notice produced 25 spans, 20 of them empty. Wrong
citations, not silence.

**Recommendation: a new module, `segment_civil.py`, selected by the document's language, and
`segment.py` untouched.** Selection by language, not by trying patterns on the text, is the same
containment rule the Australian collector already follows. It is also what keeps every English record
byte-identical, which W12 then proves.

| Profile | Units | Citation form | Hours |
| :---- | :---- | :---- | ----: |
| `lao` | ພາກ part, ໝວດ chapter, ມາດຕາ article. Lao or Arabic digits, and Python `\d` accepts both | `art.N` | 3 |
| `zho` | 第…编, 第…章, 第…节, 第…条, then （一） items. Chinese numerals up to hundreds need a parser. 附件 for attachments | `art.N` | 3 |
| `por` | Título, Capítulo, Secção, `Artigo N.º` with its heading on the next line, numbered paragraphs `1 -` and items `a)`. Anexo | `art.N`, `art.N(p)` | 3 |
| Shared | The profile table, the citation writer, and tests on a real page of each | | 1 |

The host's template asks for "Art. 26(2) or S 13(1)(a)", so `Art. N(x)` is the civil-law form and
`s. N(x)` stays for common law. If an article is not found, the document still emits nothing, as
today. **Silence beats a wrong citation.**

**The Lao profile needs one thing the others do not: a number repair.** Measured 2026-09-23 on real
scans — article markers survive OCR (`ມາດຕາ` at line start 19 times of 19 in the Cyber Security
Law) but **the digits are misread**: 30 as 90, 32 as 92, 38 as 88, 55 as 585. Corpus-wide the
article-number sequence agreement is **0.856**, so about one Lao article number in seven is wrong as
read. Articles ascend, so the true number is recoverable from position. Rules:

- take the number from the ascending sequence when the OCR'd digits break it;
- write what OCR read into `article_number_as_read` and set `citation_confidence` to
  `sequence_repaired`;
- where the sequence is ambiguous, mark `unverified` rather than guess;
- drop the table-of-contents repeat first — Lao statutes restate the first articles up front, and
  257 of China's 943 documents carry a `目录` block that would double every chapter.

A repaired citation is recorded, never hidden: "a real act cited to the wrong section scores zero",
and an invisible repair is exactly how that happens.

## W6. Normalisation: stop deleting article headings, and fix Portuguese and Lao

**4 hours. Blocking for W5.**

- **Stop the furniture detector deleting every article heading.** Measured on three Timorese acts on
  2026-09-22: `detect_furniture` (`normalize.py:85-99`) masks digits, so every `Artigo #.º` collapses
  to one shape that repeats on most pages and is dropped, along with `Secção I` to `Secção III`. One
  11-page act goes from 41 `Artigo` headings in the raw text to none after `normalize_pages`. Lao and
  Chinese headings repeat the same way. English escapes only because each section heading carries its
  own words. The fix: never drop a line that matches an article, chapter or section heading in the
  document's language. Keep the detector otherwise, because the gazette page lines are real furniture.
  Add a regression test per language, and one for English proving nothing moved.
- **Keep the hyphen in Portuguese enclitics.** `normalize.py:40` turns `aplica-\nse` into `aplicase`.
  De-hyphenate only when the language is not Portuguese, or when the joined word is not a verb plus
  clitic.
- **Unwrap lines before accented and non-Latin letters** (`normalize.py:44`, `:162`, `:169-170`).
- **Strip soft hyphens and zero-width spaces** (`normalize.py:45`). TL NOTES reports soft hyphens
  inside words in older Timorese PDFs.
- **Lao folding is for matching only.** Fold `ຫນ→ໝ`, `ຫລ→ຫຼ` and the two /am/ spellings when a title
  is compared or an error rate is measured, never in the frozen text. The frozen text is what a judge
  quotes against the scan.

## W7. Split Timorese gazette issues into acts

**6 hours. Tier 2.**

An issue opens with a `SUMÁRIO` naming its acts. `links_used` carries the list as
`contract_meta.contains`. Give every provision its own act's name and number, or a quote from
Decree-Law 13/2026 is cited to whatever act opens the issue, which is a C2b failure.

**Split on the page number, not on title lines.** Measured 2026-09-23: the SUMÁRIO lists each act
with its gazette page — `Decreto do Presidente da República No. 4/2007.......... 2058` — and every
page carries a `Página NNNN` line, which maps to the PDF page by a constant offset (verified across
an 11-page issue, printed 2058 to 2068). Matching act titles in the body is far less reliable: a
regex over the body of one issue found none, because the body prints them in a different case and
form.

**A real case, found on 2026-09-23 while testing translation.** `tl-ldcn-001` is one gazette issue
of 25 March 2026 holding **Lei 1/2026, the Competition Law** (from printed page 276) and
**Decreto-Lei 13/2026 on fuel prices** (from page 284). **Both have an Article 6.** Extracting
without act identity published the fuel article's text under the Competition Law's name — a real
provision cited to the wrong statute, which scores zero. The law tracker already lists both acts
against this one `doc_id`, and the SUMÁRIO already gives both page numbers, so nothing has to be
guessed.

**Do not branch on the `no_sumario` flag.** Of the 35 documents carrying it, 16 do have a SUMÁRIO
inside the two pages the audit read, so the flag is testing something narrower. Test each document
for a parseable index and fall back to `contains` plus article-run detection. That fallback is where
the valuable Timorese law is: the Civil Code (223pp), the Customs Code, the Commercial Companies Law
and the Criminal Procedure Code all arrive through it.

**The record shape needs mapping's agreement (Q4).** The recommendation: keep one `doc_id` per issue,
add `act_index`, `act_name` and `act_number` to each provision, and write one `laws.jsonl` row per act.

**The honest fallback, if W7 is cut:** extract only the 1,010 single-act issues, hold the rest back,
and say so. No provision is then misattributed.

## W8. China intake: `.docx`, `.doc` and ministry HTML

**7 hours. Depends on a China manifest (Q3).**

Verified 2026-09-23 by reading the bytes, so the lane can be designed against facts:

- **943 of the 945 layer-1 files are real OOXML**, including one mislabelled `.doc` — so sniff by
  magic bytes, never by extension. **943 parsed in 2.1 seconds**: machine time is not a factor.
- **46,223 paragraphs begin `第…条`**, across 882 of 943 documents. The 61 without are amendment
  acts, NPC decisions and interpretations, which carry no articles to cite — a property of the
  instrument, to record in `document_kind` rather than flag as a failure.
- The separator after `第一条` is **U+3000**, the ideographic space, not U+0020.
- **All 140 stored China HTML pages are UTF-8**, so no GBK decoding is needed for the frozen bytes.
  A charset sniff is still needed for the live test, which fetches CAC cold.
- Containers: `div.main-content` on CAC (111/111), `#UCAP-CONTENT` on gov.cn, `div.article_fd` on
  MIIT (16 of 17, so a largest-text-block fallback is needed).
- The `.txt` sidecars collection stored are **not** the source of record: they carry page chrome
  (`纠错】`, `首页 > …`) and render the article separator as an ASCII space, so offsets taken against
  them would not resolve. Use them as a free regression oracle on output length for 123 documents.

1. **A `.docx` lane** reading `word/document.xml` with the standard library's `zipfile` and XML
   parser. No new dependency and no licence row. Paragraph breaks become newlines, so the segmenter
   sees lines. Skip the `目录` table of contents: 257 documents carry one.
2. **The two genuine `.doc` files** in the zips are OLE2, and neither is RDTII-relevant (a Basic Law
   interpretation and customs rank insignia) — exclude both with a reason. **The `.doc` that matters
   is elsewhere**: `manual\miit\raw\4564599.doc` is the telecom services catalogue, the only source
   for indicator 5.5. Convert that one by hand, hash both sides, and record the conversion.
3. **A generic HTML lane** for `www.cac.gov.cn` and `www.gov.cn`:
   - Detect the charset from the headers and the `<meta>` tag before decoding (`parse_html.py:53`
     assumes UTF-8).
   - Take the article body by host rule, falling back to the largest text block.
   - Join inline spans without inserting spaces (`parse_html.py:44-46`).

   The live test crawls CAC, so this lane is what runs on 15 October if China is drawn.
4. **Zip members** are unpacked by ingest, or better listed as their own manifest rows by the
   crawler. Q3 decides which.

## W9. `language_of_source` in the record, the translation rule in the contract

**2 hours.**

1. **Add `language_of_source` to `provision.schema.json` and `laws.schema.json`**, string or null,
   copied in `extract_fields.build_record` from the value W1 resolved.
2. **Assert it in `cmd_validate`.**
3. **Copy both schemas to `stages\p3-map\` in the same commit** (D4).
4. **Write D5 into `INTERFACE_CONTRACT.md` section 3.** The verbatim snippet is always in the source
   language. Any translation sits in a separate, labelled field that mapping or the interface owns, and
   never in place of the quote.

## W10. Cache clear, OCR engine table, seconds per document

**2 hours.**

- **Expose one `clear_caches(out_dir)` function** that empties the run's extraction output and the
  W4 page cache. The dashboard's clear control calls it (D15 in the dashboard workshop). Without it a
  stale OCR result survives the reset.
- **Put the README template's OCR swap table in the stage README:** engine, setting, open or
  proprietary. List Tesseract as the default. List Azure as optional and proprietary. Leave Paddle
  off the table unless it is fixed, because `paddle_engine.py` calls the 2.x API with 3.x pinned.
- **Write OCR seconds and wall-clock seconds per document into `cost_report.json`.** Mapping's step
  2C and the README's measured-cost section both read it.

## W11. Lao accuracy evidence

**Largely done on 2026-09-23, about 1 hour left.** Q5 turned out not to block: three references were
found that need nobody who reads Lao, and all three have been measured. Full results in
`evidence\2026-09-23_ocr_engine_comparison.md`.

| Reference | Measured | Result |
| :---- | :---- | :---- |
| Rendered twin, verified Unicode Lao natives | 12 pages | char F1 **0.946**, raw CER 0.178 |
| Title recovery on **real scans** against the portal's own titles | 60 documents, 349 pages | mean **0.891**, none below 0.50 |
| Article-number sequence agreement on real scans | 658 headings | **0.856** |

The text layer had to be checked before it could be a reference: of 70 native Lao PDFs only 24 carry
real Unicode Lao, 44 are mojibake, and `la-la1022-001` is a legacy font mapped into the Lao Unicode
block — it looks like Lao, is a substitution cipher, and would have produced a fabricated error rate.

**What remains: the honest label.** None of these is a `gold_page`, so none supports the under-5%
rubric claim. Either a Lao reader keys one page by 28 September, or the submission reports these
three figures for what they are and says the rubric claim is not made for Lao. The second is
defensible and costs nothing; the first is worth an hour of asking.

The route for any further measurement depends on Q5.

- **If someone who reads Lao can key one page by 28 September,** that is a real `gold_page`. Follow
  the Round 1 fixture layout in `fixtures\ocr_reference\` so `pilot` measures it with no new code.
  Choose a body page of at least 1,500 characters from a pillar 6 or 7 law in the corpus. 5 hours,
  mostly keying.
- **If not,** measure a rendered twin: 48 evidence-use Lao documents are native text. Check first that
  their text layer is Unicode Lao and not a legacy font. Render some pages to image at 300 DPI, OCR
  them, and compare with the text layer. 3 hours.
  - It is an optimistic figure, because a clean render is easier than a gazette scan.
  - Label it `rendered_twin`, a method `meets_rubric` does not accept.
  - Claim only what it measures.

Either way, save the English-pack OCR of the same page as the "before" picture the old plan asked for.

## W12. Full runs of six corpora, English regression, validate

**5 hours of attention, plus wall clock.**

1. **English regression first.** Run the Round 1 code and the new code on the same new SG, MY and AU
   corpora with `--skip-tags`. Every record must be byte-identical apart from `language_of_source`.
   This proves W1 to W9 moved nothing for English. It is the right comparison, because 411,986 was
   measured on a corpus that is no longer read.
2. **Then LA, TL and CN,** one corpus per run, each followed by `validate`.
3. **Record per economy:**
   - documents in and records out;
   - `zero_provisions` and `parse_failed` counts, with the documents named;
   - OCR pages and seconds.

   Write them in `evidence\`.
4. **Probe the zero-provision documents** the way the Round 1 corpus audit did. A large document with
   almost no provisions is the failure a non-Latin segmenter shows first.

## W14. Flags and exclusions

**4 hours. Freeze minimum. Missing from the 22 September plan entirely.**

Collection's rule is "flag, do not fix", and it handed over 2,116 flagged documents. The developer's
decision of 2026-09-23: carry and mark, exclude only what is provably not the law it is filed under.

**Exclude 87, each with a `laws.jsonl` row saying why:**

| Class | Count | Why |
| :---- | ----: | :---- |
| `repeal_notice` (MY) | 76 | The file is a cover sheet, not the act. Verified: median 313 characters, maximum 1,533, none over 3,000. Nothing to quote under D1, so excluding makes the zero explicit rather than unexplained |
| `other_act_text` (MY) | 5 | A different act altogether. `my-wpa2009-001` is filed as the Witness Protection Act 2009 and holds 26,828 characters of the **Judicial Appointments Commission Act 2009** — whose own number appears zero times in it. Its `legal_status` is `unknown` and its `use` is `evidence`, so no other filter catches it, and the real act is already in the corpus under its own id |
| `act_not_in_text` / `acts_not_in_text` (TL) | 4 | Same failure. **Match on the prefix**: collection emits two spellings, and a filter on one silently misses `tl-ro-001` |
| Ministry of Justice Tetum translations (TL) | 2 | `tl-lbn-001` and `tl-kenegpn-001` are translations, headed "TRADUÇÃO", recorded as `por`. Extracting them publishes a translation as source text: a D5 breach and a D3 falsehood in one row |

**Carry and mark 2,029**, including all 1,780 `no_text_layer` (the source publishes images, which is
not a defect) and the 169 `short_principal` (mostly genuine short acts).

**Seven Malaysian `language_mismatch` rows get their language corrected from the flag**, not from
detection — the crawler wrote `eng` and the crawler flagged the file as Malay, so reading the flag is
reading a crawler field and D3 holds. One of them is Act 680, the Electronic Government Activities
Act, which is squarely in scope.

Two more things belong in this package:

- **Delete a dead branch.** `ingest.py:132-143` and `cli.py:625-640` skip rows whose `crawl_notes`
  contains "superseded by". That string appears **0 times in 7,090 rows**. Superseded copies are
  already excluded from the corpus and listed in `superseded.jsonl`.
- **The OCR queue is a union, not a column.** `pdf_is_scanned OR no_text_layer` — the two sets
  differ by 3 documents in Lao and 2 in Malaysia. Filtered by `use`, the Lao queue is **1,404
  documents and 19,058 pages**, not 1,695.

## W15. The settled output format

**6 hours. Freeze minimum.** The specification is `OUTPUT_FORMAT.md`; this is the work of building it.

1. Widen the three vendored schemas and add every new field (W1 does the widening; this adds the
   fields).
2. `extract_fields.build_record` gains the collection-provenance block, the language pair, the
   citation-confidence fields and `page`.
2a. **The English title, `law_name_en`** (+1.5 hours). Everything a reader reads is English except
   the quote (`OUTPUT_FORMAT.md` section 0). The title is the one field that is not English today,
   and stage 3 matches it against a host baseline that names Lao and Chinese laws in English, so
   without it every Lao row is tagged NEW by default. For the 53 Lao laws the gazette published in
   English, read the title off the English PDF's cover and mark it `publisher_translation`;
   otherwise render it and mark it `rendered`. Never take a name from the host's database (D4).
3. `laws.jsonl` becomes **one row per act** and gains `coverage_status` and `exclusion_reason`.
   Without the exclusion channel, stage 3 can pick a document extraction deliberately excluded as
   the governing-law citation for a "No provision found" row — so a Malaysian repeal notice could
   be cited as the authority for an absence.
4. Copy both schemas to `stages\p3-map\00_contracts\schemas\` in the same commit (D4).
5. Drop the fields with no consumer anywhere: `scope`, `extraction_confidence`,
   `extraction_confidence_note`, the `law_name_grounded` and `*_char_*` family, `model_version`,
   `instrument_version`.

## W13. Hand-back to the repo in one commit

**3 hours.**

1. **Run the drift check** from `README.md`. If the repo changed under a working copy, merge that
   first.
2. **Branch the repo. Never commit on `finale`.**
3. **Copy `code\*` back** to `stages\p2-extract\`, together with:
   - p1's 0.3.0 manifest schema;
   - p3's schema copies, which carry the same economy and id pins.

   All in one commit (D4).
4. **Run the stage tests and a clean-clone `run` on one Lao document.** Log the change in the repo's
   `docs\CHANGELOG_FINALE.md`.

---

## Sequence, 23 to 30 September

Tentative. It moves with the answers.

| Day | Work |
| :---- | :---- |
| Tue 22 | Plan, working copy, baseline tests (80 passed, 2 skipped). **Done** |
| Wed 23 | Tool comparisons for OCR and translation, the packs vendored, the output format settled, W11 measured. **Done overnight** |
| Wed 23, day | W2, W1. Lao and Timor-Leste load through the gate. W15 begins |
| Thu 24 | W15 finished, W14. W3 and W4 on the OCR lane. Start the full Lao OCR pre-pass in the evening |
| Fri 25 | W6, then the W5 Lao profile. First Lao run end to end, `validate` |
| Sat 26 | W8 and the Chinese profile, if China's manifest exists by then |
| Sun 27 | The Portuguese profile. Timor-Leste run on single-act issues. W7 if time allows |
| Mon 28 | W12 regression and all six runs. W10. The Lao gold page, if a reader was found |
| Tue 29 | W13 hand-back on a branch, clean-clone test, evidence files |
| Wed 30 | Freeze. Buffer only |

## What gets cut, in order

| Order | Cut | What to say instead |
| ----: | :---- | :---- |
| 1 | Tier 3: single-pass OCR, soft tags for new economies, the CJK compatibility fix, incremental delta skips | Nothing. None is visible to a judge |
| 2 | **W7, Timorese act splitting — the developer's nominated first cut, 2026-09-23** | Extract single-act issues only, name the rest as held back. But build the SUMARIO fallback even so: the Civil Code, the Customs Code and the Commercial Companies Law are single-act SUPLEMENTO issues that arrive through it |
| 3 | The HTML part of W8 | China from the national database's `.docx` only. Say the live test for China then depends on this lane, and that it is not built |
| 4 | W11's gold page, falling back to the rendered twin | Quote the twin as a twin, never as a scan measurement |

**Do not cut W6, or W5 for Lao, or W3.** Without them Lao produces nothing, and Lao is the one new economy in
the live-test draw with a full corpus.

## Questions for the developer

Blocking first. Each carries a recommendation.

| # | Question | Recommendation | Blocks |
| ----: | :---- | :---- | :---- |
| Q1 | Are the three new economies Timor-Leste, Lao PDR and China? No `DECISIONS.md` records it | Record it in scraping's decisions, noting that only Lao and China protect the live test | Nothing here, but D8 and the Word submission quote it |
| Q2 | Does extraction agree contract 0.3.0 now, or read the sidecars until it lands? | Both. Extraction accepts 0.2.0 and 0.3.0 in one gate, and reads `law_table.csv` and `links_used` until the manifest carries `language` and `use`. Agree the must-have columns now: `language` (ISO 639-3), `document_kind`, `legal_status`, `superseded_by`, `citation_url`, `law_name`, `law_number`. The rest can wait | W1 |
| Q3 | Who builds China's manifest? | Scraping, in the contract's shape: one row per file, zip members as their own rows, `source_type` extended with `docx`. It holds the provenance sheets. Extraction builds the lane | W8 |
| Q4 | How is a Timorese act identified in a record? | Keep `doc_id` per issue. Add `act_index`, `act_name` and `act_number` to the provision, one `laws.jsonl` row per act. Needs mapping's agreement | W7 |
| Q5 | Can anyone who reads Lao key one page by 28 September? | **No longer blocking.** Three references were found and measured on 2026-09-23 without one. A gold page is still the only route to the under-5% claim, so it is worth an hour of asking; if the answer is no, the submission reports the three measured figures and says the rubric claim is not made for Lao | ~~W11~~ |
| Q6 | Are soft-hint tags needed on the finale runs? | **Answered by reading mapping's code, 2026-09-23: mostly no.** `scope` and `extraction_confidence` have zero readers. `obligation_type` boosts retrieval on 4 of its 10 values, reaching 0.6% of Round 1 records; `data_type` damps 84% of records uniformly, which is close to a no-op. Run with `--skip-tags`: extraction's cost becomes compute only and no API key is needed anywhere | W12, the cost ledger |
| Q7 | Who translates? The live test says "reads and translates", and no workshop plans it | **Measured 2026-09-23.** Extraction keeps D5 and builds nothing. Where the publisher's own English exists — 53 Lao laws, 1,513 pages, already on disk — use that, not a model. Elsewhere a gloss is a reading aid beside the original, and the model is **`gemma3:12b`**, not qwen: chrF 0.658 against the publisher's English where qwen reaches 0.561, on a ceiling of 0.807. Even so it renamed a cited statute ("the Law on Customs" became "the Tax Code"), so a gloss can never carry an indicator decision. Measured separately: OCR noise moves the English output as much as the model choice does | Not extraction's build |
| Q8 | Do Singapore, Malaysia and Australia go into the workbook from the new corpora or from Round 1's output? | **Answered 2026-09-23: the new corpora, everything fresh.** Reuse would have covered only 1,117 of 3,407 English documents anyway (Australia 1.4%, because it is now fetched as dated epubs), and native text extraction runs at 1-2 ms a page. The 1,117 byte-identical documents are kept as the regression fixture instead | W12 |
| **Q9** | **Will collection re-merge the Lao corpus so the 53 official English translations are addressable?** | **New, and cheap.** `merge_corpus.identity()` ignores language, so all 53 English twins were superseded by their Lao originals and left out of the corpus. They are 1,513 native-text pages, they are the reference the translation comparison used, and 50 of them are the only text-layer copy of a law whose Lao original is a scan. Collection has already logged the defect. Extraction reads the corpus, not the run folder, so either it re-merges or extraction records an explicit exception | Q7's recommendation, and any further translation evidence |
