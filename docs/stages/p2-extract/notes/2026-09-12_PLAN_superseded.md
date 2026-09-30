# Extraction plan to 30 September

Eighteen days to code freeze. Steps are ordered so that the freeze minimum lands first and the
refinements are the ones that get cut. Hours are working hours for one developer.

Every step marked **proposed** is not in the current build plan. The recommendation and the
reason are given rather than a list of options. Steps marked **agreed** already exist as
committed behaviour or as a decision recorded in `DECISIONS.md`.

All repo paths below are relative to `C:\Users\woshi\Desktop\rdtii-rocky-finale\stages\p2-extract`
unless stated otherwise.

## Summary

| Step | What | Hours | Status | Freeze minimum |
| ----: | :---- | ----: | :---- | :---- |
| 1 | Widen the vendored schemas for six economies | 3 | Proposed | Yes, blocking |
| 2 | Manifest language column, read not guessed | 2 | Agreed, unbuilt | Yes, blocking |
| 3 | Per-document OCR language with loud failure | 5 | Proposed | Yes |
| 4 | Acquire and vendor the language packs | 3 | Proposed | Yes |
| 5 | Lao gold reference page, hand-keyed | 5 | Proposed | Yes |
| 6 | Second non-Latin gold page, Thai | 4 | Proposed | No, strongly wanted |
| 7 | `language_of_source` reaches the provision record | 3 | Proposed | Yes |
| 8 | Translation decision, written not built | 1 | Proposed, see D5 | Yes |
| 9 | Mixed-script documents, the India case | 3 | Proposed | No |
| 10 | Regression over the Round 1 corpus | 4 | Proposed | Yes |
| 11 | Non-Latin segmentation | 8 | Proposed | No, cut first |
| 12 | Consolidated multi-law volumes, the Niue case | 6 | Proposed | No, cut second |
| | **Total** | **47** | | **Minimum 26** |

Forty-seven hours against eighteen days is not comfortable, because this task is one of several
the same developer owns. That is why steps 11 and 12 are named as cuts now rather than
discovered as cuts on 28 September.

### Changed by the host templates, read 2026-09-12

- **Superseded in part by the scope decision below.** Step 4's pack list became the nine live-test economies, not the planning set: `tha`, `vie`,
  `ind`, `chi_sim`, `hin`, `kaz`, `rus`, `lao`, `mon`. See the table in `README.md`. Step 4 grows by
  about one hour. Kazakh and Vietnamese were not previously in scope.
- **Step 8 gains a constraint.** The workbook says Language of Source is the original language and
  the snippet is the exact source text. The live test says "reads and translates". Any translation
  therefore serves the mapper only and never reaches the evidence columns. Any translator must also
  run without a proprietary service, because the README template extends that rule to translation.
- **New step 13, OCR timing per script, 2 hours, freeze minimum yes.** The README template asks for
  wall-clock seconds per document, and the live hour is 90 minutes for everything. Time Tesseract on
  one page of each installed script and record it in `evidence\`. If a 100-page scan in an unfamiliar
  script cannot finish in the hour, the live-test plan has to know before 15 October, not during it.
- **New step 14, cache clear hook, 1 hour, freeze minimum yes.** Checklist item 26 requires caches
  clearable on screen. Expose one function that empties the run's extraction output and OCR cache,
  so the crawl task's clear operation can call it.

Revised total: 51 hours, minimum 30.

### Scope decision, 2026-09-12

**Required: six economies, three of them new and non-English, pillars 6 and 7. Further is optional.**
See `DECISIONS.md` D8.

- **Step 4 installs packs for the three chosen economies only**, not all nine. Two or three packs
  instead of nine, so about 2 hours rather than 4. The nine-economy table in `README.md` is the menu
  to choose from.
- **Steps 5 and 6, the gold pages, follow the chosen scripts.** Lao and Thai were placeholders. Key one
  gold page for each non-Latin script among the three chosen economies.
- **Step 13 times only the chosen scripts.**
- Nothing else changes. Grounding, the language column and the translation decision are the same
  work whether there are two pillars or twelve.

---

## Step 1. Widen the vendored schemas for six economies

**Hours: 3. Proposed. Blocking, do this first.**

Today the gate refuses every economy that is not Singapore, Malaysia or Australia. Verified
2026-09-12 in `00_contracts\schemas\manifest.schema.json` and
`00_contracts\schemas\provision.schema.json`.

| Constraint | Current value | Effect on a Thai document |
| :---- | :---- | :---- |
| `economy` | `enum: ["SG", "AU", "MY"]` | Row rejected at `ingest.load_manifest` |
| `doc_id` | `pattern: ^(sg\|au\|my)-[a-z0-9]+-\d{3}$` | Row rejected |
| `pillar_hint` | `enum: ["P6", "P7", "both", null]` | Rejected once pillars 1 to 12 are in scope |
| `additionalProperties` | `false` on both schemas | Any new column rejects the whole row |

Do this:

1. **Wait for the crawler's authored schema.** The crawler stage owns the source of truth at
   `..\p1-scrape\contracts\schemas\manifest.schema.json`. Extraction re-vendors, per D4. Do not
   author a divergent copy here.
2. **Copy both schema files** into `00_contracts\schemas\` in the same commit as the crawler
   bump, and bump `CONTRACT_VERSION`. `ingest.check_contract_major` only refuses on a MAJOR
   mismatch, so a widened enum inside `0.x` will not be caught automatically. Widening an enum
   is backward compatible for old rows, so a MINOR bump is correct.
3. **Widen `provision.schema.json` to match**, then copy it to `..\p3-map\00_contracts\schemas\`.
   The mapping stage vendors its own copy and will reject Hand-off #2 otherwise.
4. **Run `p2-extract validate`** over the existing `handoff2` output to prove the widening broke
   nothing. A widened enum must still accept all 411,986 Round 1 records.

Files touched: `00_contracts\schemas\manifest.schema.json`,
`00_contracts\schemas\provision.schema.json`, `..\p3-map\00_contracts\schemas\*.json`,
`config\settings.py` if `contract_version` moves.

**Recommendation on `doc_id`.** Replace the country alternation with a two-letter lowercase
class, `^[a-z]{2}-[a-z0-9]+-\d{3}$`. It stays a real gate against malformed ids, needs no edit
when a seventh economy arrives, and satisfies the rubric's "minimal reconfiguration" wording on
C1a.

---

## Step 2. Manifest language column, read not guessed

**Hours: 2. Agreed as D3, unbuilt.**

The column arrives from the crawler. Extraction reads it and never guesses.

1. **Add the column to `_NULLABLE_IF_EMPTY`** in `ingest.py` so an empty CSV cell coerces to
   `None` rather than an empty string that fails a schema pattern.
2. **Decide the value space with the crawler.** Recommend ISO 639-3 codes, lowercase, comma
   separated for a multilingual document, for example `lao`, `tha`, `eng,hin`. ISO 639-3 maps
   one to one onto Tesseract pack names far more often than ISO 639-1 does, which removes a
   translation table. Name the column `language`.
3. **Fail the row, not the run.** Apply this when the column is absent and the document is a
   scan. A native-text HTML page in an unknown language still extracts correctly, because
   grounding operates on bytes. A scan without a language is unreadable, so it must stop.

Files touched: `src\rdtii_p2\ingest.py`.

**Open dependency.** If the crawler cannot detect language reliably for every source, the
fallback is a per-economy default in the crawler's seed configuration, not a guess here. Raise
this with the crawl task in the first two days. It blocks steps 3 and 5.

---

## Step 3. Per-document OCR language with loud failure

**Hours: 5. Proposed. The core of the task.**

Today `Settings.ocr_lang` is a single global string, default `eng`, read once in
`config\ocr\factory.py:get_ocr`. Every document in a run gets the same pack.

1. **Add a language map module**, `config\ocr\langmap.py`, holding one dict from the manifest
   language code to a Tesseract pack string. Recommended starting entries:

| Manifest `language` | Tesseract pack | Note |
| :---- | :---- | :---- |
| `eng` | `eng` | Installed |
| `msa` | `msa+eng` | Already side-loaded at `fixtures\tessdata_local\msa.traineddata` |
| `tha` | `tha+eng` | Thai statutes carry English headings and numerals |
| `lao` | `lao+eng` | |
| `zho` | `chi_sim+eng` | Confirm simplified against traditional per source |
| `rus` | `rus+eng` | |
| `mon` | `mon+rus` | Mongolian uses Cyrillic. `rus` is the safety net, not `eng` |

   Always append `+eng` where the statute mixes Latin numerals or English short titles. Tesseract
   accepts multi-language strings and the cost is a small speed penalty.

2. **Thread the language through the call chain.** `get_ocr(settings)` becomes
   `get_ocr(settings, lang=...)`. There are three call sites in `cli.py`: the lane C branch of
   `_parse_doc`, and the `demo` and `pilot` commands. Note the gap. `_parse_doc` does not
   receive the `ManifestRow`. Its caller `cmd_run` holds the row and passes only
   `row.data["source_url"]` through. So `_parse_doc` needs a new `lang` parameter threaded from
   `cmd_run`, which is where the manifest value is read. `TesseractEngine.__init__` already
   takes `lang` and already embeds it into `engine_id`, which reads
   `tesseract-5.4.0.20240606-<lang>` on this machine, so the provenance field needs no change.
3. **Build the loud failure.** Before the first page is rendered, call
   `pytesseract.get_languages(config="")` and compare against the requested packs. On a missing
   pack raise through `ingest.IngestError` with the exact winget or download line to fix it.
   Wire the same check into `ingest.preflight`, which already fails loudly for a missing
   Tesseract binary and an unpulled Ollama model. That function is the right home.
4. **Add a confidence floor as the second net.** `TesseractEngine.to_text` already computes
   `mean_word_confidence` per page. A page under a floor, recommend 60, on a document whose
   `pdf_is_scanned` is true should be logged as `low_confidence_page` into
   `extract_log.jsonl`, and the document's status should carry the count. This catches the case
   the pack check cannot see, which is a pack present but wrong.

Files touched: `config\ocr\factory.py`, `config\ocr\langmap.py` (new), `config\settings.py`,
`src\rdtii_p2\ingest.py`, `src\rdtii_p2\cli.py`.

**Recommendation on `OCR_LANG`.** Keep the environment variable as an override, not as the
source. It stays useful for a one-off pilot and for the interface's engine controls, and the
manifest value wins when present. Log which one was used, every document.

---

## Step 4. Acquire and vendor the language packs

**Hours: 3. Proposed.**

Verified 2026-09-12: `C:\Program Files\Tesseract-OCR\tessdata` holds `eng.traineddata` and
`osd.traineddata` only. Tesseract is 5.4.0.20240606 and is not on `PATH`, which
`Settings.resolve_tesseract_cmd` already handles by probing the Program Files locations.

1. **Put the new packs beside the Malay one**, in `fixtures\tessdata_local\`, and set
   `TESSDATA_PREFIX` from within `get_ocr` rather than asking a reviewer to set it by hand. The
   current README asks the reviewer to export the variable. That will not survive the
   thirty-minute clean-machine test, so the code should set it.
2. **Check the size before committing.** `tessdata_best` files are roughly 10 to 15 MB each.
   Five new packs is plausibly 60 MB in a repo that must clone quickly. Recommend
   `tessdata_fast` for the shipped default and `tessdata_best` only if step 5 shows the fast
   pack missing the error rate bar. Measure, do not assume.
3. **Confirm the licence file before committing anything.** Google's tessdata repositories are
   published under Apache 2.0, which matches the repo licence. Verify the LICENSE file in the
   exact release you download. Record the URL and the commit hash in `evidence\`. The host
   forbids shipping licensed text. An unverified third-party blob in a public repo is exactly
   the thing the secretariat will ask about.
4. **Write the download step into the deployment guide** either way, so a reviewer who clones
   without large files can still run.

Files touched: `fixtures\tessdata_local\`, `config\ocr\factory.py`, `README.md` in the stage,
and the repo deployment guide.

---

## Step 5. Lao gold reference page, hand-keyed

**Hours: 5. Proposed. This is the honesty step.**

Without this the tool cannot claim any accuracy figure for a non-Latin economy, and C1c is
marked on exactly that. `cer.CerReport.meets_rubric` refuses the under-5% claim unless
`cer_method` is `native_twin` or `gold_page`, which is the right behaviour and must not be
loosened.

1. **Pick the page.** Use the host's own file,
   `C:\Users\woshi\Desktop\RDTII Finale Plan\1_Rules\Baselines\Sample legislations\Domestic language only\Lao PDR-Law on Electronic Transaction (Amended) No. 31.pdf`.
   It has 29 pages and zero extractable characters, confirmed 2026-09-12, so it is a true scan.
   Choose a body page with at least 1,500 characters, matching the existing fixture standard.
2. **Hand-key it.** Render the page at 300 DPI first, key against the image, and save as
   `fixtures\ocr_reference\<doc_id>\gold_page_XXXX.txt`, UTF-8, LF. Budget three hours. Keying
   a script you do not read is slow and this is the honest cost of the claim.
3. **Measure with the existing command.** `p2-extract pilot --scan ... --gold ... --page N
   --doc-id ...` already writes `cer_report.json`, the OCR page text and the confidences. No new
   measurement code is needed.
4. **Record the caveat in the report, not only in prose.** `cer.py` normalises both sides with
   NFC plus whitespace collapse. For Lao and Thai that is not neutral. Those scripts do not put
   spaces between words, and combining vowel and tone marks count as separate characters in a
   character-level Levenshtein distance. The same visual error can therefore score differently
   from a Latin one. Add the script name to `CerReport` and say so in the field description, so
   a judge comparing 0.93% English against a Lao figure is not misled.

Files touched: `fixtures\ocr_reference\<doc_id>\`, `src\rdtii_p2\cer.py` for the script field.

**What to claim afterwards.** State the measured Lao page rate and the script it is on. Never
average it with the English pages. Never extend it to Thai. The existing habit of disclosing
`engine_fixture_estimate` separately from `gold_page` is the pattern, and it already carries a
conservative source string in `cer.ENGINE_FIXTURE_SOURCE`. Extend that habit per script.

---

## Step 6. Second non-Latin gold page, Thai

**Hours: 4. Proposed.** Not the freeze minimum. It is the difference between one data point and
a claim.

One gold page on one script is a data point. Two on two scripts is a method. If time allows
only one more thing after step 5, do this rather than step 11.

Follow the same procedure as step 5 on a Thai scanned statute. Take it from the crawler's own
corpus, not from the sample folder. The evidence trail then runs end to end from a real crawl.

---

## Step 7. `language_of_source` reaches the provision record

**Hours: 3. Proposed. Freeze minimum.**

The finale workbook has fourteen columns. The new one is the language of the source document.
It has to travel manifest to provision record to mapping to workbook, and extraction owns the
middle leg.

1. **Add the field to `provision.schema.json`.** `additionalProperties` is `false`, so an
   unregistered key fails validation for every row. Recommend the field name
   `language_of_source`, matching the workbook column, with type string and null allowed.
2. **Set it in `extract_fields.build_record`**, from `row["language"]`, beside the other
   provenance fields such as `source_type` and `ocr_engine`. It is a copied manifest value, not
   an inference, so it needs no grounding offsets.
3. **Copy the schema to `..\p3-map\00_contracts\schemas\provision.schema.json`** in the same
   commit, for the same reason as step 1.
4. **Assert it in `cli.py:cmd_validate`.** The validate command is where a missing field should
   surface, before the mapping stage sees the file.

**Recommendation on multilingual documents.** Take the Indian file, which carries Latin and
Devanagari on the same page. Record the document-level value as the comma list the manifest
gave, for example `eng,hin`. Do not try to set a per-provision language in this pass.
A per-provision value would be an inference, and an inference in a provenance column is the
thing this task exists to avoid. Step 9 revisits it.

Files touched: `src\rdtii_p2\extract_fields.py`, `src\rdtii_p2\cli.py`,
`00_contracts\schemas\provision.schema.json`, `..\p3-map\00_contracts\schemas\provision.schema.json`.

---

## Step 8. Translation decision, written not built

**Hours: 1. Proposed, recorded as D5 in `DECISIONS.md`.**

The recommendation is that extraction does no translation and stays wholly in the source
language. The reason is the host's own rule: the verbatim snippet is the evidence. A translated
snippet is not a substring of the frozen source text, so `ground.verify` would have to be
relaxed to admit it, and C2b would be gone.

What this costs and what it buys is written up in D5. The work here is to write the rule into
the interface contract so the mapping stage cannot quietly assume a translated field exists.

Files touched: `INTERFACE_CONTRACT.md` in the stage, section 3.

---

## Step 9. Mixed-script documents, the India case

**Hours: 3. Proposed. Not the freeze minimum.**

`INDIA-~1.PDF` in the host's sample folder is native text, about 2,100 characters per page,
Latin and Devanagari interleaved on the same pages, verified 2026-09-12. It is not an OCR
problem at all. It is a segmentation problem, because the Hindi text is usually the same
provision repeated, and a naive segmenter emits each provision twice.

The cheapest honest handling is to emit both and let them both be grounded, then let the
mapping stage deduplicate on indicator. Do not silently drop the Hindi half. Dropping the
domestic-language text would be a poor answer to a C1c question from a judge.

Log a `mixed_script_document` note into `extract_log.jsonl` so the behaviour is visible.

---

## Step 10. Regression over the Round 1 corpus

**Hours: 4. Proposed. Freeze minimum, and the last thing before the tag.**

Every step above touches a schema or the record builder. The 411,986 existing records are the
evidence base for C2b and must survive unchanged except for the new column.

1. **Re-run `p2-extract validate`** against `C:\Users\woshi\Desktop\RDTII\pipeline-data\handoff2`.
2. **Confirm the grounding assertion still passes on every record.** This is the number that is
   quoted in the submission, so it must be re-measured, not remembered.
3. **Confirm the record count.** A changed count means segmentation moved, which means a
   citation moved, which means the submission text is wrong.
4. **Re-run `p2-extract demo`** so the live character error rate measurement still passes its
   own gate. The demo is deliverable-facing and a judge may run it.

---

## Step 11. Non-Latin segmentation. CUT FIRST

**Hours: 8. Proposed.**

`segment.py` matches English forms only. Verified patterns at the top of the file: `_PART` on
`^PART`, `_DIVISION` on `^Division`, `_SCHEDULE` on `SCHEDULE`, plus numbered-section variants
and an Australian no-dot fallback.

Thai statutes use มาตรา for a section. Lao uses ມາດຕາ for an article. Neither matches. What
happens today is that `_pick_body_run` finds nothing, the decimal-paragraph fallback finds
nothing, and the document emits zero provisions or one giant span.

Cut this first because the failure is visible and honest rather than wrong. A document that
produces no provisions is reported as producing no provisions. A document that produces a
mis-cited provision is a C2b failure. If the choice is between silence and a wrong citation,
take silence, and say in the submission which documents fell back to whole-document spans.

If it is built, copy the shape of the Australian pass. That pass is not inside
`_collect_candidates`. It is a separate collector, `_collect_candidates_au`, called from
`segment()` only when the dot-pattern pass returns under five sections, and it wins only if it
finds more. Add a third collector the same way and engage it under the same rule. That
containment rule already exists in the file and is the reason a well-segmented Singapore
document never switches shape.

---

## Step 12. Consolidated multi-law volumes, the Niue case. CUT SECOND

**Hours: 6. Proposed.**

`Niue-Legislation Volume 1.pdf` is 683 pages of native text holding many separate laws in one
PDF. One manifest row becomes one `doc_id`, so every provision in the volume would carry one
`law_name` and one `law_number`. That is a citation fidelity problem, which is C2b, so it is not
trivial to dismiss.

There is partial prior art in the stage at `docs\HANDOFF_AU_MULTIVOLUME_2026-07-17.md`. Read
it before designing anything, but read it for what it is. It covers one act spread across many
volumes, not many acts inside one volume, so it does not solve law identity. The reusable part
is the volume-boundary convention. P1 marks each spine document with an HTML comment,
`<!-- p1-epub-spine-doc i/n: ... -->`, and P2 splits on it. Niue needs the same idea applied to
a page range in a PDF, with the act title read from the page rather than handed over.

Cut this second because it is one document class rather than a whole economy, and because the
honest fallback is available. If the volume is not split, say so, and record the volume-level
`law_name` with a note that the provision belongs to a named act within it.

---

## Minimum for 30 September freeze

Steps 1, 2, 3, 4, 5, 7, 8, 10. Twenty-six hours.

That delivers three things.

| Delivered | Steps |
| :---- | :---- |
| Per-document OCR language that fails loudly on a missing pack | 3, 4 |
| At least one hand-keyed non-Latin gold page with a measured character error rate | 5 |
| The language column reaching the output | 2, 7 |

The task brief names those three as the minimum. Steps 1, 8 and 10 carry the rest. They are the
schema widening the other steps sit on, the written translation rule, and the regression that
proves nothing broke.

## What gets cut, in order

| Order | Cut | What to say instead |
| ----: | :---- | :---- |
| 1 | Step 11, non-Latin segmentation | Name the affected documents and report zero or whole-document spans. Silence beats a wrong citation |
| 2 | Step 12, consolidated volumes | Record the volume-level law name and disclose the limitation |
| 3 | Step 9, mixed-script handling | Emit both language versions, let mapping deduplicate |
| 4 | Step 6, second gold page | Claim one script only, and say so in the same sentence |

Do not cut step 5. A per-document language setting with no measured error rate is a feature
with no evidence, and the rubric is marked on evidence.
