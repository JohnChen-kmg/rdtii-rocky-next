# Extraction: turning bytes into grounded provisions

This folder is the workshop for one task. Extraction takes the raw bytes the crawler retrieved
and turns them into clean, article-level text, then into one grounded provision record per
article. It is where the tool's honesty guarantee is enforced.

The code lives in the repo. Since 2026-09-22 a working copy of the whole stage sits in `code\`,
edited here and handed back (decision D9). This folder also holds the plan, the decisions, the
working notes and the evidence. It is not a git repo.

## Read this first, 2026-09-22

**`PLAN.md` was rewritten on 2026-09-22 as a preliminary plan.** The three new economies turned out
to be Timor-Leste, Lao PDR and China, not the Lao and Thai placeholders this page was written around.
Sections below dated 2026-09-12 are kept as history. Where they disagree with these files, these win:

| File | What it holds |
| :---- | :---- |
| `OUTPUT_FORMAT.md` | **The settled output format**, one shape for six economies, carrying how each document was obtained. Written against the host's workbook columns and what stage 3 actually reads |
| `TOOLS_BY_ECONOMY.md` | **Which tool reads and which translates, per economy**, with the number behind each choice |
| `WORKFLOW.md` | **How the stage runs**: six commands, per economy, what is cached, what is parallel, and what to check when something breaks |
| `evidence\2026-09-23_ocr_engine_comparison.md` | Three OCR engines measured on the same pages, per script. Why Tesseract `fast` is the default and why the vision model must not read Lao |
| `evidence\2026-09-23_translation_comparison.md` | Translation candidates against the Lao gazette's own English. Why extraction still translates nothing |
| `notes\2026-09-23_worklog.md` | What was done overnight on 23 September, and how each result was checked |
| `experiments\` | The scripts behind those measurements, and their raw output in `experiments\results\` |
| `PLAN.md` | Work packages W1 to W15, the sequence to 30 September, the cut order, and nine questions for the developer |
| `notes\2026-09-22_inputs_and_asks.md` | The six corpora extraction will read, where language and use actually live, and every ask from the other workshops |
| `notes\2026-09-22_code_audit.md` | What in the stage breaks on the finale inputs, with file and line. Also the instrument impact record |
| `DECISIONS.md` D9 | Why the code is now copied here |

Stale on this page, and not corrected in place:
- the pack table, which has no `por` and lists Thai;
- "The first thing to do", because scraping ran the Lao pilot on 2026-09-20;
- the regression target, which was Round 1's 411,986 records.

## How this workshop is organised

| Path | What it is |
| :---- | :---- |
| `code\` | The working copy of `stages\p2-extract` at repo commit `92a5e9d`, same layout. Left out: the Round 1 `PLAN.md`, `docs\`, `sample_docs\` and `fixtures\tessdata_local\msa.traineddata` |
| `PROVENANCE.tsv` | Each copied file's repo path, commit and sha256 at copy time |
| `PLAN.md`, `DECISIONS.md` | The work and the choices behind it |
| `notes\` | Dated working notes. No source code |
| `evidence\` | The artefacts that back claims others will check |

**Running the copy.** From `code\`, with the Round 1 venv, which has every dependency:

```
$env:PYTHONPATH = "src;."; $env:PYTHONUTF8 = "1"
& "C:\Users\woshi\Desktop\RDTII\pipeline-data\rdtii-p2-extract\.venv\Scripts\python.exe" -m pytest -q
```

Baseline on 2026-09-22, before any edit: 80 passed, 2 skipped. `PYTHONPATH` puts this copy ahead of
the venv's own installed stage, so the tests exercise `code\`.

**Handing back.** Run the drift check first, from this folder. It prints each copied file that was
edited here, and each whose repo original changed since the copy. Where the repo changed, merge that
into the copy before anything goes back. Then follow `PLAN.md` W13: branch the repo, never commit on
`finale`, copy `code\*` to `stages\p2-extract\`, and move the p1 and p3 schema copies in the same
commit (D4).

```
python -X utf8 -c "import csv,hashlib,pathlib as P;R=P.Path(r'C:\Users\woshi\Desktop\rdtii-rocky-finale');h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else 'missing';[print(r['dest'],'| edited here:',h(P.Path(r['dest']))!=r['sha256_at_copy'],'| repo changed:',h(R/r['repo_path'])!=r['sha256_at_copy']) for r in csv.DictReader(open('PROVENANCE.tsv',encoding='utf-8'),delimiter='\t') if h(P.Path(r['dest']))!=r['sha256_at_copy'] or h(R/r['repo_path'])!=r['sha256_at_copy']]"
```

It prints nothing when nothing has moved. A file added here that is not in `PROVENANCE.tsv` is new,
and goes back as a new file.

## What this task owns

| Owns | Where the code is |
| :---- | :---- |
| Manifest ingest and schema gate | `stages\p2-extract\src\rdtii_p2\ingest.py` |
| Lane routing and mis-flag recovery | `stages\p2-extract\src\rdtii_p2\router.py` |
| OCR engine, per page | `stages\p2-extract\config\ocr\tesseract_engine.py` |
| OCR driver, batching and caching | `stages\p2-extract\src\rdtii_p2\ocr_scanned.py`. A stub today. Lane C OCR runs inside `cli.py:_parse_doc` |
| Character error rate measurement | `stages\p2-extract\src\rdtii_p2\cer.py` |
| Normalise once, detect furniture, freeze | `stages\p2-extract\src\rdtii_p2\normalize.py` |
| Article, section and schedule boundaries | `stages\p2-extract\src\rdtii_p2\segment.py` |
| The grounding gate | `stages\p2-extract\src\rdtii_p2\ground.py` |
| Record assembly and soft-hint tagging | `stages\p2-extract\src\rdtii_p2\extract_fields.py` |

All paths above are relative to `C:\Users\woshi\Desktop\rdtii-rocky-finale`.

## What this task does NOT own

| Not owned | Owner |
| :---- | :---- |
| Finding and downloading documents, polite crawling | Crawl task, `stages\p1-scrape` |
| The manifest language column itself | Crawl task. Extraction reads it, never guesses it |
| Indicator mapping, framework alignment | Mapping task, `stages\p3-map` |
| NEW and KNOWN tagging | Mapping task |
| The final fourteen-column workbook | Export task |
| Engine switching from the interface | Interface task, `interface\dashboard.py` |

Extraction does emit `scope`, `data_type` and `obligation_type` as soft hints. Those are
conveniences for the mapping stage, not verdicts, and mapping is free to overrule them.

## Rubric criteria carried

| ID | Criterion | Points | Share carried here |
| :---- | :---- | ----: | :---- |
| C2b | Citation fidelity at scale, article-level, verbatim, no hallucinations | 10 | Effectively all of it. `ground.verify()` is the mechanism |
| C1c | Linguistic versatility, same provision and indicator whatever the language | 10 | A large share. A non-English scanned statute fails here first |
| C4b | No vendor lock-in | 7 | A slice. `OCR_ENGINE` is a declared engine seam alongside the LLM |

C2b is already strong and the job is to protect it. C1c is the exposure.

## Current state, 2026-09-12

Figures quoted from `C:\Users\woshi\Desktop\RDTII Finale Plan\3_Final_Stage\AUTHORITATIVE_NUMBERS.md`.

| Measure | Value |
| :---- | :---- |
| Provision records | 411,986 across 2,673 documents, at corpus v2.4 plus the segmentation fix |
| Grounding | Every quoted snippet a character-exact substring of the frozen source text at recorded offsets, machine re-verified at validation |
| Scanned pages OCR'd | 12,292 in the full run, plus 998 in the v2.1 delta. 43 scanned documents, Tesseract 5.4.0 |
| Character error rate | 0.00% on the committed reference page, re-measured live by `p2-extract demo`. Pilot pages measured 0.93% and 2.72% |
| Corpus-wide error rate | Never claimed. Only one document carries a real hand-keyed gold page. The rest carry a conservative engine fixture estimate, disclosed as such |
| Extraction cost, Round 1 | US$130.44, about 4.9 cents per law, at corpus v2.1. A figure of $107.29 is superseded |
| OCR language | One global value, `OCR_LANG`, default `eng` |

The output data sits at `C:\Users\woshi\Desktop\RDTII\pipeline-data\handoff2`, about 2.4 GB,
holding `provisions.jsonl`, `laws.jsonl`, `source_text\`, `ocr\` and `extract_log.jsonl`.

## The honest gap

State this plainly in the submission. This task has the least planned work in the current build
plan and is the task most exposed by the finale's non-English requirement.

- **One language pack, globally.** `config\settings.py` carries `ocr_lang` as a single scalar,
  default `eng`. Every scanned page in the corpus was read as English.
- **The machine has two packs.** `C:\Program Files\Tesseract-OCR\tessdata` holds `eng` and
  `osd` only, verified 2026-09-12. Thai, Lao, Chinese, Russian and Mongolian have no data
  installed. A Malay pack was side-loaded once at
  `stages\p2-extract\fixtures\tessdata_local\msa.traineddata` because Program Files was not
  writable. That is the pattern to reuse, not a solved problem.
- **No non-Latin error rate exists.** Every committed gold page is a Malaysian English gazette
  scan. Nobody has hand-keyed a Thai, Lao, Chinese, Russian or Mongolian page, so the tool
  cannot honestly quote an accuracy figure for the economies C1c is marked on.
- **The manifest has no language column.** `00_contracts\schemas\manifest.schema.json` sets
  `additionalProperties: false`, so the column cannot simply appear. It has to be added by the
  crawler and re-vendored here in the same commit.
- **The schemas are still Round 1 shaped.** Both the manifest and the provision schema pin
  `economy` to the enum `SG`, `AU`, `MY` and `doc_id` to the pattern `^(sg|au|my)-...`. Six
  economies cannot pass ingest until that is widened. Every row of a new economy would be
  rejected, loudly, at the gate.
- **Segmentation is English shaped.** `segment.py` matches `PART`, `Division`, `SCHEDULE` and
  numbered sections in English forms. Thai and Lao statutes number articles differently.

## The host's own sample folder is the warning shot

Files at `C:\Users\woshi\Desktop\RDTII Finale Plan\1_Rules\Baselines\Sample legislations`,
probed 2026-09-12.

| File | Pages | Text layer | What it tests |
| :---- | ----: | :---- | :---- |
| `Domestic language only\Lao PDR-Law on Electronic Transaction (Amended) No. 31.pdf` | 29 | none, 0 chars | Lao script OCR with no fallback. The hardest case on disk |
| `PDF of scanned documents\Pakistan_PECA.pdf` | 4 | none, 0 chars | Scanned Latin script, small |
| `PDF of scanned documents\India-Public_Procurement_order_2017.pdf` | 7 | none, 0 chars | Scanned Latin script |
| `Multilanguage in one legal file\INDIA-~1.PDF` | 4 | native, about 2,100 chars per page, Latin and Devanagari mixed on the same pages | Language labelling, not OCR. One document, two scripts |
| `Consolidated laws in one volumn\Niue-Legislation Volume 1.pdf` | 683 | native, about 2,700 chars per page, measured across all 683 pages | Many laws in one PDF. A segmentation and law-identity problem |

The useful finding is that only three of the five are OCR problems. The Indian multilingual
file and the Niue volume are native text and fail somewhere else.

## New from the host templates, read line by line on 2026-09-12

Full detail is in `C:\Users\woshi\Desktop\RDTII Finale Plan\3_Final_Stage\REQUIREMENTS.md`.

| Requirement | Source | Consequence for this task |
| :---- | :---- | :---- |
| **The no-proprietary rule covers OCR and translation, not only the language model** | README template, "Swapping the OCR Engine"; Word Section 3 checkbox | Tesseract satisfies it. Any cloud OCR or translation service would have to be optional and declared as proprietary. The open-weights path must run with neither |
| **The README must document swapping the OCR engine**, and flag which options are proprietary | README template | One table: engine, config value, notes. `OCR_ENGINE` is already a seam in `config\ocr\` |
| **Language of Source is the original language**, "not the language you translated into" | Workbook Instructions, field rule | Confirms the plan: the language comes from the manifest and never from a translation step |
| **The Verbatim Snippet is the exact text, verified against the source** | Workbook Instructions | A translated snippet fails this outright. Whatever the translation decision in step 8, the evidence column stays in the source language |
| **Live test step 2 is "reads and translates"** | Orientation slide 9 | Translation is expected somewhere on the day. Step 8's decision is not optional to write down. Translating for the mapper while quoting the original is compatible with every host rule |
| **Word Section 4 asks, per live-test economy, which languages the tool handles** | Word template, Section 4 | The honest answer is limited by installed language packs and gold pages. The table below is the pack list the nine economies imply |
| **Measured cost per document includes an OCR line, and wall-clock seconds per document** | README template, Measured Cost | Record OCR seconds per page per script. It also tells the live-test plan whether a long scan fits inside the hour |
| **Zone 2 is a separate, documented module** | Checklist item 10 | Already true by stage split. Say so in the README |
| **The second pass fetches nothing** | Word Section 2, Run Record | Extraction already runs offline from stored bytes. State that in Section 2 as the reason the second pass is safe |
| **Caches clearable on screen** | Checklist item 26 | Per-run extraction output and the OCR cache must be clearable with the crawler's cache, or a stale OCR result survives the reset |

### Tesseract packs the nine live-test economies imply

Since the scope decision of 2026-09-12, only the packs for the three chosen new economies are
required. Treat this table as the menu.

| Economy | Likely source scripts | Tesseract packs |
| :---- | :---- | :---- |
| Thailand | Thai | `tha` |
| Viet Nam | Vietnamese, Latin with diacritics | `vie` |
| Indonesia | Indonesian, Latin | `ind` |
| China | Simplified Chinese | `chi_sim` |
| India | English and Hindi, often mixed | `eng`, `hin` |
| Kazakhstan | Kazakh and Russian, Cyrillic | `kaz`, `rus` |
| Lao PDR | Lao | `lao` |
| Mongolia | Mongolian, Cyrillic | `mon` |
| Russian Federation | Russian, Cyrillic | `rus` |

Today the machine has `eng` and `osd` only. This list is proposed, not verified against each portal.

## Borrow from Round 1

Round 1 built this stage, measured it and wrote it down. Most of what the finale needs already
exists as a document or a fixture. Point at it, never copy it. Nothing below is duplicated into
this folder, so there stays one source of truth.

Repo paths are relative to `C:\Users\woshi\Desktop\rdtii-rocky-finale`. Planning paths are
absolute. Every path below was checked on disk on 2026-09-12.

### Templates, worth more than the reference material

| Path | Why open it for this task |
| :---- | :---- |
| `stages\p2-extract\fixtures\ocr_reference\` | The gold-page method as a working directory, and the exact shape step 5 must reproduce for Lao. It holds `README.md`, the committed scan `my-cca1997-001.pdf`, and one folder per measured document: `my-cca1997-001\`, `my-cma1998-001\` and the quarantined `my-cma1998-001_oldscan_20260712\`. Each folder carries `gold_page_XXXX.txt`, `page_XXXX.txt`, `page_XXXX.confidences.json` and `cer_report.json`. Copy those filenames exactly so `p2-extract demo` finds the Lao page without new code |
| `stages\p2-extract\fixtures\ocr_reference\README.md` | How to publish a measured error rate without overclaiming. It names the error source per page, keeps the retired 2.72% scan on the page rather than deleting it, and says why the cleaner reprint measurement was deliberately not used to lower the corpus estimate. That is the paragraph to imitate when the Lao figure lands |
| `stages\p2-extract\INTERFACE_CONTRACT.md`, section 3.5 | The acceptance bar a new gold page must clear, fixed in the contract rather than chosen by the author. A native twin, or a hand-keyed sample of at least one full page and 1,500 characters, with the reference file and the offsets committed so a judge can recompute. Section 3.3 is the provision schema that step 7 adds `language_of_source` to |
| `C:\Users\woshi\Desktop\RDTII Finale Plan\1_Rules\Baselines\Sample legislations` | The host's own awkward set, and the acceptance set for steps 3, 9, 11 and 12. The four files that matter are tabled above under the warning shot. Run against these before touching a corpus document, because a failure here is the failure a judge will find |
| `C:\Users\woshi\Desktop\RDTII Finale Plan\2_What_We_Built\Reference\Stage_Plans\round1_plan\DISCLOSURES.md` | The honesty habit in its shortest form. Never present an estimate as a measurement, and every figure names where its evidence lives. Item (a) is the extraction limitations entry, which is the row this task rewrites once the language work is measured |
| `stages\p2-extract\00_contracts\schemas\` | The three files step 1 widens: `manifest.schema.json`, `provision.schema.json` and `laws.schema.json`. These stand in for the planning-folder schemas directory named in the task brief, which does not exist on disk. These are the live vendored copies, so they are the ones that actually gate a row |

### Reference, beside the code

| Path | Why open it for this task |
| :---- | :---- |
| `stages\p2-extract\START_HERE.md` | The fastest orientation to the stage, and the reading order for a developer who has not opened it before. It also names the host sample set as the hardening corpus, which is the same argument this plan makes for steps 11 and 12 |
| `stages\p2-extract\PLAN.md` | The Round 1 build plan. Section 2.4.3 is the Lane C design step 3 modifies, section 2.4.4 is the mis-flag recovery this task inherits, and section 2.4.3a already writes down the verbatim against true statute trap that D1 restates. It is a Round 1 schedule, so this folder's `PLAN.md` supersedes it as the plan of record |
| `stages\p2-extract\STAGE_GUIDE.md` | The submission-facing orientation, and the model for how to describe this stage to a reviewer. Check the scope before quoting its cost. It carries $177.52, the cumulative v2.4 ledger, while the authoritative page carries $130.44 at corpus v2.1 |
| `stages\p2-extract\docs\KICKOFF_DECISIONS_2026-07-12.md` | The source D1 and D2 were recorded from. Read it before reopening either decision, because the reasoning is already written and does not need redoing |
| `stages\p2-extract\docs\HANDOFF2_NOTES_2026-07-13.md` | The full-corpus run note, with the per-lane split and the first OCR lane counts. Its 305,980 record count is the v2.0 figure and is stale. The lane breakdown and the zero-provision accounting are still the model for step 10's regression write-up |
| `stages\p2-extract\docs\HANDOFF2_NOTES_2026-07-14.md` | How a corpus change was absorbed incrementally, re-processing only changed documents. Step 10 needs the same discipline. This note also records the gold page being re-keyed after the Malaysia re-crawl replaced the scan, which is the precedent for a gold page going stale |
| `stages\p2-extract\docs\HANDOFF2_NOTES_2026-07-15.md` | A worked example of disclosing a scope correction. The upstream note announced 15 new instruments and the manifest held 32, and the note says so plainly rather than quietly processing them |
| `stages\p2-extract\docs\HANDOFF2_NOTES_2026-07-18.md` | The v2.4 re-extract of 33 Australian acts, and the superseded-row rule extraction still applies. Skip any manifest row whose `crawl_notes` contains "superseded by" |
| `stages\p2-extract\docs\HANDOFF2_NOTES_2026-07-18b.md` | The segmentation fix that produced the current 411,986 count, including the schedule-clause change. Read it before step 11, because it shows what a segmentation change does to provision ids and therefore to citations |
| `stages\p2-extract\docs\HANDOFF_AU_MULTIVOLUME_2026-07-17.md` | Partial prior art for step 12, cited there with its limits. It covers one act across many volumes, not many acts in one volume |

### Reference, in the planning workspace

| Path | Why open it for this task |
| :---- | :---- |
| `C:\Users\woshi\Desktop\RDTII Finale Plan\2_What_We_Built\Reference\Stage_Plans\2_OCR_and_Tag_Extraction.md` | The original stage plan, about 50 KB. It is byte-identical to `stages\p2-extract\PLAN.md`, same MD5, so open whichever is nearer and do not treat them as two sources |
| `C:\Users\woshi\Desktop\RDTII Finale Plan\2_What_We_Built\Reference\Stage_Reports\p2\P2_README.md` | A snapshot of the stage README as it stood at the first full run, useful for the shape of a stage report. Its figures are superseded: $107.29, 4.1 cents per law, and 2.72% for the CMA 1998 gold page. The current stage `README.md` differs, and the authoritative page governs any figure that reaches the submission |
| `C:\Users\woshi\Desktop\RDTII Finale Plan\2_What_We_Built\Self_Assessment\03_Submission\briefs\STATION_2_P2_EXTRACT.md` | The tightest single briefing on what this stage claims and how each claim was verified, with an artifact path against every number. Its path shorthands are dead. `rdtii-p2-extract`, a Desktop `handoff2` and `RDTII Judge` no longer exist, so translate them to the repo and to `C:\Users\woshi\Desktop\RDTII\pipeline-data\handoff2` as you read |
| `C:\Users\woshi\Desktop\RDTII Finale Plan\2_What_We_Built\Reference\Stage_Plans\0_Interfaces_and_Contracts.md` | The frozen spine every stage keys off, and the authority that settles a disagreement between two stage plans. Read section 8 before step 1, because widening a schema is a contract amendment and it has a defined procedure |
| `C:\Users\woshi\Desktop\RDTII Finale Plan\2_What_We_Built\Self_Assessment\01_Findings\LEAKAGE_AUDIT_2026-07-16.md` | The sealed-test discipline in one page. The live test has no baseline, so every channel by which baseline answers could reach the model must stay closed. It applies here because a language map or a segmentation rule tuned against known documents is the same failure wearing different clothes |
| `C:\Users\woshi\Desktop\RDTII Finale Plan\2_What_We_Built\Self_Assessment\01_Findings\CORPUS_EXTRACTION_AUDIT_2026-07-17.md` | What an independent audit of this stage actually probed, which was source text against the real law rather than byte grounding. It found large documents yielding almost no provisions. That is the exact failure mode a non-Latin document will show, so reuse the probe |
| `C:\Users\woshi\Desktop\RDTII Finale Plan\2_What_We_Built\Self_Assessment\01_Findings\SEGFIX_VERIFICATION_2026-07-18.md` | How a segmentation fix was proved, by re-deriving every acceptance number from a full sweep of `provisions.jsonl` rather than from the builder's notes. Step 10 should be verified the same way |

## The first thing to do

OCR one page of the Lao law with today's English-only settings and keep the output. One hour,
no production code written.

Call `config.ocr.factory.get_ocr(load_settings())` from a throwaway script and run `to_text`
over page 3 of `Lao PDR-Law on Electronic Transaction (Amended) No. 31.pdf`. The `pilot`
command cannot be used yet because it requires a `--gold` transcription that does not exist.

The point is to see with your own eyes what Tesseract with `lang=eng` does to Lao script, and
to save that page text into `evidence\` as the before picture. Every later claim about the
language work is measured against it. Expect near-empty or near-random output. Record the mean
word confidence as well. A low confidence on a legible page is the signal the loud-failure
check in step 3 should be built around.

Then go to `PLAN.md` and start at step 1.
