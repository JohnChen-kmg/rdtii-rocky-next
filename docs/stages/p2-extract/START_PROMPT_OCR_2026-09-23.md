# Starting prompt — extraction and OCR stage, written 2026-09-23

Paste the block below into a fresh session opened in `C:\Users\woshi\Desktop\rdtii-finale-2-extraction`.
It is written for an agent that has not seen this project. Everything it asserts is checkable in the
files it names.

---

You are starting stage 2 of the RDTII finale build: **extraction**. Collection closed on 23 September
and handed over 8,175 documents. Your job is to turn them into grounded, article-level provision
records without losing the shape collection built.

Your workshop is `C:\Users\woshi\Desktop\rdtii-finale-2-extraction`. The stage code is a working copy
in `code\`, edited here and handed back to the repository in one commit at the end (decision D9). The
collection workshop is `C:\Users\woshi\Desktop\rdtii-finale-1-scraping` and is **read-only to you**.

## Read these first, in this order

| File | Why |
| :---- | :---- |
| `C:\Users\woshi\Desktop\RDTII Finale Plan\finale_progress\STAGE_RESULT_p1-scrape_2026-09-23.md` | What collection actually delivered. **Newer than everything in this workshop. Where it disagrees with a plan here, it wins** |
| `PLAN.md` | Work packages W1 to W13, written 2026-09-22 against these same corpora, with hours and a cut order |
| `notes\2026-09-22_inputs_and_asks.md` | The six corpora measured document by document, and where language and use actually live |
| `notes\2026-09-22_code_audit.md` | What in the Round 1 stage breaks on these inputs, with file and line |
| `evidence\2026-09-22_lao_ocr_timing.md` | Lao OCR throughput measured on this machine, and two findings that change the design |
| `DECISIONS.md` | D1 to D9. D1, D3 and D5 bind your design |

Do not re-derive what those files already establish. Cite them and move on.

## What you are given

Six corpora under `C:\Users\woshi\Desktop\rdtii-finale-1-scraping\outputs\<CC>\`. Each economy's
`README.md` there is the index. Start there, not in the folders.

| | Documents | Form | Language | The problem it sets you |
| :---- | ----: | :---- | :---- | :---- |
| **Lao PDR** | 1,762 | **1,692 scans, 24,773 pages.** 70 native | `lao` | 96% has no text layer. Nothing is extractable without OCR, and Lao script OCR is the single largest piece of machine time in the stage |
| **Timor-Leste** | 1,921 | 1,892 native PDF, 37,352 pages. 29 scans | `por` | **One PDF holds many acts.** 911 documents carry more than one law, up to 15. Issues open with a `SUMÁRIO` index |
| **China** | ~1,085 | 942 `.docx` and 3 `.doc` inside 11 zips, 111 CAC HTML, 6 gov.cn HTML, 23 MIIT. No scans | Chinese | **No manifest and no lane.** See below |
| **Malaysia** | 1,391 | 1,331 native, 58 scans, 2 HTML | `eng`, some `msa` | 178 flagged rows, of which 137 matter |
| **Australia** | 1,278 | 793 HTML, 485 native PDF | `eng` | 91 flagged, low risk |
| **Singapore** | 738 | 737 native, 1 scan | `eng` | Effectively clean |

All five non-China manifests are contract 0.2.0 and validate with zero errors. `raw\` is not in git.

## The four hard rules

1. **No quote, no record (D1).** Every `verbatim_snippet` is a character-exact substring of the frozen
   source text you stored, with byte offsets that resolve. A record that cannot be grounded is not
   written. This is the tool's honesty guarantee and it is worth points under criterion C2b.
2. **Language is read, never guessed (D3).** It comes from the crawler, in `law_table.csv` and
   `links_used\documents.jsonl`, as ISO 639-3. If you find yourself detecting a language, stop.
3. **Keep collection's shape.** `doc_id` is the join key throughout. The law tracker,
   `law_table.csv`, is one row per **law**, while the manifest is one row per **document**, and for
   Timor-Leste those differ by a factor of two. Carry `use`, `document_kind`, `legal_status`,
   `law_name`, `law_number` and the content flags through into your output. Downstream scoring must be
   able to get from a provision back to the law tracker row and from there to the page it came from.
4. **Flag, do not fix.** Collection stored wrong files as served and flagged them: 76 Malaysian repeal
   notices filed as acts, 5 files that are a different act altogether, 7 language mismatches. Do not
   silently drop or repair them. Decide whether to exclude, re-fetch or carry the flag, record the
   decision, and make it visible to scoring.

## The formats differ by country, and the Round 1 segmenter handles none of them

The Round 1 segmenter is English common-law only. On Timorese documents it does not fail silently, it
produces **confidently wrong citations**: four principal acts gave 3 to 8 spans each, all cited `s.1`,
`s.2`, `s.3`, against documents whose articles are `Artigo 1.º`. A ceremonial notice produced 25 spans
of which 20 were empty. Wrong citations cost more than missing ones.

| Family | Article marker | Watch for |
| :---- | :---- | :---- |
| Portuguese, Timor-Leste | `Artigo 1.º` | Many acts per PDF, split on the `SUMÁRIO`. Soft hyphens. About 3,300 ceremonial acts, honours and appointments, are still marked as evidence and are noise |
| Lao | ມາດຕາ | OCR output, so the marker itself may be misread. NFC only: NFKC rewrites all 182 Lao titles. The /am/ vowel has two encodings |
| Chinese | 第…条 | Also 附件 annexes, and `（一）` sub-items. `.docx` is a different reader from HTML |
| English | `s.N`, Part, Division, Schedule | Round 1 handles this. It is your regression baseline, and it must not move |

## China is a different shape, deliberately

Read `countries\cn-china\SOURCES.md` and section 4 of the stage result before touching it.

China has **no manifest in the contract's shape**, because one portal cannot hold its operative tier:
the Legislation Law puts laws with the legislature and departmental rules with the State Council, and
the national database forbids automated collection. So the corpus is a folder per source, each with a
`provenance.tsv`, and layer 1 is eleven `.zip` archives of `.docx` files collected by hand.

**Building that manifest is the first China task.** Agree with the developer who does it, question Q3
in `PLAN.md`. Then you need an office-format reader that Round 1 does not have: `.docx`, three `.doc`,
and ministry HTML that differs from the national database's.

Do not treat China's hand collection as a defect. It is a legal constraint, it is documented, and the
submission will be marked on the honesty of that account.

## What is new in this round, and what the developer has asked for

**Compare tools. Do not assume Tesseract, and do not assume nobody translates.**

Three of the six economies are new, and two of them are in scripts nobody on this project has measured.
The stage already has engine stubs at `code\config\ocr\`: `tesseract_engine.py`, `paddle_engine.py`,
`azure_engine.py`, behind a `factory.py` that dispatches on one setting, and an `OCREngine` interface
in `base.py` returning per-page text and per-page mean word confidence. Use that seam.

**For OCR**, run at least three candidates over the same pages and report one table.

- Candidates worth testing: Tesseract with `tessdata_best` against `tessdata_fast`, PaddleOCR,
  and at least one vision-language model reading the page image. Add a cloud document-AI service only
  as an **optional second engine**: the host requires that the pipeline runs end to end with no
  proprietary service, so a proprietary OCR cannot be the only path.
- Measure on the same pages: character error rate against a reference, characters returned, seconds
  per page, and failure behaviour under parallel load.
- Report per script, not pooled. **An English error rate stamped on a Lao page is a false claim.**
  The Round 1 fixtures at `code\fixtures\ocr_reference\` show the shape: a gold page, the OCR output,
  per-word confidences, and a `cer_report.json` from `cer.py`.
- Two measured findings constrain the design. Tesseract worker processes crash intermittently under
  parallel load with an access violation, the same page succeeding on retry, so the pool must retry a
  page, stay alive, and record which pages were retried, with a per-page cache making a killed run
  resumable. And mean word confidence on clean Lao body pages is 58 to 65, so a global floor of 60
  would flag most good Lao pages: set the floor per script from measured pages.
- Budget: the Lao evidence scans are 19,058 pages, about 1.4 hours at 12 to 16 workers with two
  passes, against about 18 hours as the code runs today, which OCRs every page twice.

**For translation**, no workshop currently owns it. The live test says the tool "finds sources,
downloads, **reads and translates**, extracts, maps", and decision D5 says extraction does not
translate. That gap is question Q7 and it is unresolved. Your job is not to settle it alone, but you
must **compare the candidates and hand the developer a recommendation with numbers**: a local
open-weights translation model, a general instruction model prompted to gloss, and a cloud translation
API as the optional second path. Judge them on whether the gloss preserves the legal meaning of a
provision, on cost per thousand provisions, and on whether the original stays the document of record.
Whatever is chosen, the **original text remains the evidence** and the translation is labelled as a
gloss beside it, never substituted for the snippet.

## Answer these before building

`PLAN.md` ends with eight questions for the developer, each with a recommendation. Q2, Q3, Q4 and Q5
block work. Put them to the developer in one message, with your recommendation and what it costs if
the answer goes the other way. Do not stall on the ones that do not block: state your assumption,
write it down, and proceed.

The three the collection stage explicitly handed you are: **what to do about Lao PDR's 96% scans**,
**who builds China's manifest**, and **whether the 137 Malaysian and 80 Timorese flagged files are
re-fetched, excluded, or carried as flags**.

## What to deliver

1. **Grounded provisions for all six corpora**, each carrying `language_of_source`, passing `validate`,
   with every snippet character-exact.
2. **A tool comparison** for OCR and for translation: one table each, same inputs, same metric, per
   script, with the losing options named and why. This is evidence for the submission, not just an
   internal note, and the criteria reward measured cost and honest limits.
3. **Honest numbers**: error rate per script or an explicit statement that none was measured, seconds
   per document, and the engine and version pinned per document in `ocr_engine`.
4. **A live-test path** for Lao PDR and China: a handful of freshly collected documents, from cold,
   in minutes, with caches clearable from the dashboard.

## What not to do

- Do not change anything in the collection workshop. It is read-only. Findings go back as notes and
  the developer decides.
- Do not read the host's Round 1 or Round 2 database to choose a source, a seed or a target. That is
  rule D4 in the collection workshop and it protects the submission's integrity. Cross-checks are
  disclosed as cross-checks.
- Do not translate in place of the original, and do not let a translated string become a
  `verbatim_snippet`.
- Do not defeat a refusal, change a user agent, or disable a certificate check.
- Do not let the English regression move. Singapore, Malaysia and Australia extracted with new code on
  the new corpora must be explainable against Round 1's behaviour.

Work in the walkthrough style this project uses: before an edit, name the files, show the current
control flow in ten lines or fewer, state the change in plain words, and say what you will check
afterwards. After it, append three lines to the changelog saying what, why, and how it was verified.

Start by reading the six files listed above, then tell me what you found that the plan of 22 September
got wrong, and what you propose to do first.
