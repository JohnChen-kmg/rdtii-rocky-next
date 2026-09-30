# How the extraction stage runs

**Proposed 2026-09-23.** Six commands, run per economy, each resumable and each cheap to repeat
except the one that is not. The design follows from three measured facts:

- **OCR is expensive once and free afterwards** — 25 minutes for Lao, then a page cache makes every
  re-run minutes. So OCR is its own step, never inside the extract loop.
- **Segmentation is what will be re-run twenty times** — it is where the work is, and it costs
  seconds. So it must not depend on re-reading pixels.
- **Outputs are rewritten wholesale at the end of a run** (`emit.py` read-merge-rewrite), so two
  runs pointed at one output folder lose each other's work. One writer, one economy, one folder.

---

## The six commands

```
p2 ingest   --corpus <CC>_corpus_<date>          # decide what to read, and what not to
p2 ocr      --corpus ... --workers 16            # the only parallel step; fills the page cache
p2 extract  --corpus ... --out handoff2/<CC>     # single writer: text -> provisions
p2 gloss    --out handoff2/<CC> [--headings]     # optional, never blocks extraction
p2 validate --out handoff2/<CC>                  # re-prove the grounding, count everything
p2 report   --out handoff2/<CC>                  # run note, cost table, coverage
```

### 1. `ingest` — decide what to read

Reads `manifest.jsonl` plus the two sidecars the manifest does not carry: `law_table.csv` for
`use`, `language`, `document_kind` and `legal_status`, and `links_used/documents.jsonl` for
`contract_meta.content_flags`, joined on `contract_meta.corpus.doc_id`.

It writes **`doc_status.jsonl` first, before anything is processed**, with a row for every document
including the ones it will not read:

| Decision | Rule |
| :---- | :---- |
| skip, `linkage` | every act in the document is linkage — collection decision 20 |
| skip, `not_held` | the portal lists the law, the corpus has no file |
| **exclude, `wrong_instrument`** | `other_act_text`, `act(s)_not_in_text` — the file is a different act |
| **exclude, `repeal_notice_only`** | the file is a repeal cover sheet, no act text |
| **exclude, `translation_not_source`** | a Ministry of Justice translation filed as the original |
| **exclude, `repealed`** | `legal_status` says repealed: a repealed provision scores zero. **Applied whatever `use` says** — Malaysia's law table marks 90 repealed acts `use: evidence`, because `_mark_use` never reads the status |
| read | everything else, flags carried onto every record |

Deciding this first, and writing it down first, is what makes coverage reportable: a document is
never silently absent.

### 2. `ocr` — the only parallel step

Queue is `pdf_is_scanned OR no_text_layer`, minus the skips above. **12 to 16 workers**, one
Tesseract thread each. Measured: 12.5 pages/s at 12 workers, 14.1 at 16, and Tesseract crashes the
pool intermittently above 16, so the pool retries a page and stays alive.

The cache is per page, keyed on **content sha256 + engine id + language + DPI**, holding the raw
page text, the mean word confidence and the seconds. Raw, not normalised — so a normalisation change
costs nothing, and a killed run resumes.

| | Pages | Time at 16 workers |
| :---- | ----: | ----: |
| Lao PDR | 19,058 | **22 min** |
| Timor-Leste | 822 | ~1 min |
| Malaysia | ~1,000 | ~1 min |
| Singapore, Australia, China | ~20 | seconds |

### 3. `extract` — one writer, and the step that gets re-run

Per document: take the text (page cache, native layer, HTML, or `.docx`), normalise **without
deleting article headings**, segment with the profile for that document's language, ground every
span, build the record.

Runs single-process on purpose. It is seconds per document once OCR is cached, and the outputs are
rewritten as a set.

### 4. `gloss` — optional, separate, and never in the way

Two tiers, because the volumes are three orders of magnitude apart:

| Tier | Volume | Cost | Why |
| :---- | ----: | ----: | :---- |
| `--headings` | ~47,600 Lao provisions | **6.5 h**, batched 20 a call | Mapping's BM25 leg uses an English stemmer and English keywords, so for Lao it finds nothing today. English headings restore half the retrieval |
| full snippet | **~3,600 per economy judged, ~8,000 including triage** (measured on Round 1: 2.62% and 5.77% of provisions) | **5.7 h and 12.7 h for Lao** | Only needed if the judging model cannot read the language. A model that reads Lao needs none of it |

A gloss is `article_heading_en` or `snippet_en`, always labelled, never the `verbatim_snippet`, and
never grounded. The step **rewrites `provisions.jsonl` in place**, adding those two fields and
touching nothing else — so it obeys the one-writer rule and can be re-run without re-extracting.
It writes no new file, because stage 3 reads only four artefacts and would never see a fifth.

Extraction runs fine without this step. The full text stays in `source_text/<doc_id>.txt` in the
original language either way, and that is what every offset indexes and what `validate` re-proves.

### 5. `validate` — prove it rather than claim it

Re-reads every record and re-asserts `source_text[start:end] == verbatim_snippet`. Also: schema,
`provision_id` uniqueness (the Timorese collision is real — two acts in one issue both had an
Article 6), that every excluded document has a reason, and that no `ocr_quality_cer` carries a
figure measured on a different script.

### 6. `report` — the run note

Documents in, records out, `zero_provisions` and `parse_failed` named, OCR pages and seconds, and
the coverage table. This is the raw material for the submission's measured-cost section.

---

## Running the whole thing

**Per economy, in this order**, each into its own output folder:

```
Singapore, Australia   quickest, English, no OCR         -> the regression baseline
Malaysia               English, 17 scans
Timor-Leste            Portuguese, act splitting
Lao PDR                the long one: OCR first, overnight if you like
China                  last: needs its manifest built first
```

Six folders, not one. Stage 3 already runs per economy, and one writer per folder is what keeps a
run from eating another's output.

**Wall clock for a full pass: 30 to 45 minutes**, nearly all of it Lao OCR, and only the first time.

## The regression that keeps English honest

Before any of the above is trusted: run the new code over Singapore, Malaysia and Australia and
compare against Round 1's records for the **1,117 documents whose bytes are byte-identical**. Same
input bytes, so every record must match apart from the new fields. Any difference is a finding with
a document name attached, not a judgement call.

## What to do when something breaks

| Symptom | Where to look first |
| :---- | :---- |
| A document yields zero provisions | Was its language profile selected? Did the furniture detector eat the headings? |
| A citation looks wrong | `citation_confidence` — was the number repaired, and does `article_number_as_read` disagree? |
| A quote fails validation | The frozen text changed under the offsets: normalisation ran after freezing |
| A run loses records | Two runs shared an output folder |
| OCR is slow | The double pass is back, or the page cache is not being hit |
