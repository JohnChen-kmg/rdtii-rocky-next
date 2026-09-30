# What extraction will be handed, and what others ask of it, 2026-09-22

Read from the scraping workshop, the finale planning folder and the mapping, dashboard and instrument
workshops. Counts marked *measured* were computed on 2026-09-22 from the corpus files themselves.
Everything else cites where it was read.

Short roots: `S\` is `C:\Users\woshi\Desktop\rdtii-finale-1-scraping`, `P\` is
`C:\Users\woshi\Desktop\RDTII Finale Plan\3_Final_Stage`.

## 1. The six corpora

Scraping writes one corpus per country under `S\outputs\<CC>\`. Downstream reads the corpus, never a run
and never Round 1's `handoff1_v2` again (scraping decisions 15 and 17, `S\outputs\README.md` rule 6). One
p2 run reads one corpus.

| | Corpus | Docs | Form, *measured* | Language | The problem it gives extraction |
| :---- | :---- | ----: | :---- | :---- | :---- |
| **LA** | `LA\LA_corpus_2026-09-21` | 1,762 | 1,692 scanned PDF, **24,773 pages**; 70 native, 1,470 pages | `lao` | **OCR.** Every principal pillar 6 and 7 law is a scan (scraping commit `745163f`). Evidence-use scans: 1,404 docs, 19,058 pages |
| **TL** | `TL\TL_corpus_2026-09-20` | 1,921 | 1,892 native PDF, 37,352 pages; 29 scanned, 822 pages | `por` | **Many acts in one PDF.** A gazette issue opens with a `SUMÁRIO`. 911 of 1,921 documents carry more than one `law_table.csv` row, up to 15 *(measured)*. `S\outputs\TL\README.md` counts 923 of 1,953 issues and one of 39. A 16-document delta waits in `TL_ws_2026-09-22_to_2026-09-22` |
| **CN** | none yet. Sources in `CN\CN_sources_2026-09-21\` | about 1,060 | National database: 942 `.docx` and 3 `.doc` inside 11 zips, by hand. CAC 111 HTML, gov.cn 6 HTML, each with a `.txt` copy. MIIT and Customs still being collected by hand. No scans | Chinese, no field | **No manifest and no lane.** "A manifest in the contract's shape still has to be built before stage 2 can read China" (`S\countries\cn-china\NOTES.md` section 4) |
| MY | `MY\MY_corpus_2026-09-15` | 1,391 | 1,331 native, 58 scanned (1,233 pages), 2 HTML | `eng` 1,244, `msa` 2, blank 195 in `law_table.csv` | English first (scraping decision 14). 17 scans left once linkage rows are skipped |
| SG | `SG\SG_corpus_2026-09-16` | 738 | 737 native, 1 scanned | `eng` | None new |
| AU | `AU\AU_corpus_2026-09-19` | 1,278 | 793 HTML (dated epubs, spine concatenated), 485 native PDF | `eng` | Which AU corpus is current disagrees across three files. `S\outputs\AU\README.md` says `AU_corpus_2026-09-19` |

**Which three are the new economies.** Timor-Leste, Lao PDR and China are the three built
(`S\CONVENTIONS.md` section 6). No `DECISIONS.md` in any workshop records the choice, and
`P\COVERAGE_AND_MANUAL_CHECKS.md` lines 357-360 still say "not yet chosen". **Timor-Leste is not in the
live-test draw.** Only Lao PDR and China protect the live test (`P\Live_Test_15Oct\README.md` lines 6-9).

**Every manifest is still contract 0.2.0**, 28 columns plus an `http` key, on all six corpora
*(measured)*. Contract 0.3.0 is a draft in `S\CONTRACT.md` that "binds when extraction agrees".

## 2. Where the language and the use of each document actually are

Not in the manifest. Two crawler-written places hold it, and reading either keeps D3, because the
crawler wrote it and extraction guesses nothing.

| Source | Key | Holds |
| :---- | :---- | :---- |
| `<corpus>\law_table.csv` | `doc_id` | `language` (LA, MY), `use`, `document_kind`, `legal_status`, `law_name`, `law_number`, `last_amended`. **One row per law, not per document**, so Timorese issues need aggregating |
| `<corpus>\links_used\documents.jsonl` | `url` = manifest `source_url`, 100% join on LA, TL and MY | `contract_meta.language`: LA `lao`, TL `por`, MY `eng`/`msa`/null, SG and AU `eng`. `contract_meta.contains` for Timor-Leste's acts |

The codes in use are ISO 639-3 (`lao`, `por`, `eng`, `msa`), which is what extraction's plan asked for.
`CONTRACT.md` section 7 still lists the code set as open.

**The `use` column** (scraping decision 20): `linkage` rows are amending and commencement instruments,
"not put through OCR and not mapped". `linkage, text needed` is read like evidence. Values seen
*(measured)*:

| | evidence | evidence, text stale | linkage, text needed | linkage | not held |
| :---- | ----: | ----: | ----: | ----: | ----: |
| LA | 1,448 | 4 | 7 | 307 | 7 |
| TL, per act | 3,712 | 727 | 238 | 5 | 106 |
| MY | 843 | 79 | 132 | 387 | 0 |

`not held` is not defined by decision 20. It means the portal lists a law the corpus did not store, so
there is no file to read. About 3,300 Timorese ceremonial acts (honours, appointments, pardons) still
count as `evidence` (`S\countries\tl-timor-leste\NOTES.md` sections 1.4 and 5).

## 3. Lao OCR, what is already known

From `S\countries\_finale-survey\explore-2026-09-20\la-ocr-and-translation.md` and
`S\countries\la-lao-pdr\NOTES.md` section 3.2.

- **Pilot, 2026-09-20.** `lao.traineddata` from tessdata_best, 300 DPI through pypdfium2, pages 1 to 3
  of the Law on Cyber Security 2025. All letters came back as Lao script, with no Thai substitution. The
  title matched the portal's Unicode at 89% as read, and exactly once `ຫນ→ໝ` and `ຫລ→ຫຼ` are folded.
  Stamps and letterheads come back as noise.
- **Speed 1.7 s a page** (LA NOTES line 403). The evidence-use scans, about 19,000 pages, are about
  9 hours in one process, well under an hour across 20 workers on this machine (28 threads).
- **No error rate has been measured.** It needs a page of ground truth. The note names two routes: one
  page keyed by someone who reads Lao, or the gazette's own English PDFs. The second cannot measure OCR
  of Lao text.
- **The pack was not kept.** It exists only in another session's temp folder,
  `AppData\Local\Temp\claude\…rdtii-finale-1-scraping…\scratchpad\tessdata\lao.traineddata`. Program
  Files still holds `eng` and `osd` only.
- **Normalisation.** NFC only. NFKC rewrites all 182 Lao titles. The /am/ vowel has two encodings.
- **The cloud route** the note recommends (Google Document AI plus an LLM, $400 to $630) is proprietary.
  The host's no-proprietary rule covers OCR and translation, so it could only ever be the optional second
  engine, never the only one.
- **The 53 English translations are not authoritative** (developer, 2026-09-20). Lao is the document of
  record. The corpus leaves them out.

## 4. Questions and requests addressed to extraction

| From | Ask | Where |
| :---- | :---- | :---- |
| Scraping | Agree contract 0.3.0. Extraction is named as the party that must agree. The p2 edits are listed | `S\CONTRACT.md` sections 6 and 7; `S\notes\INSTRUMENT_IMPACT_2026-09-13.md` lines 326-340 |
| Scraping | Skip `linkage` rows by joining `law_table.csv` on `doc_id` | `S\outputs\README.md` rule 5 |
| Scraping | Split Timorese issues on the `SUMÁRIO`. Normalise soft hyphens | `S\countries\tl-timor-leste\NOTES.md` section 1.3 |
| Scraping | Lao: `OCR_LANG` is one per run, ingest ignores the language column, no translation stage exists | `S\countries\la-lao-pdr\NOTES.md` section 3.2 |
| Finale issues | "Does stage 2's ingest accept a hand-collected set beside a crawled one, and does it carry the provenance sheet's `version_date_on_document` through?" China's is the first | `P\ISSUES\2026-09-21_update-watchlist.md`, questions for the other stages |
| Instrument | Accept decimal ids and all twelve pillars. Keep article and paragraph. Keep the metadata that separates principal from amending and in-force from draft | `rdtii-finale-0-instrument\NOTICE_FOR_OTHER_STAGES.md` section 4 |
| Dashboard | Expose a function that clears extraction's caches, for the clear control | `rdtii-finale-4-dashboard\PLAN.md` line 27, D15 |
| Dashboard | Write Language of Source. "This task must not invent it" | `rdtii-finale-4-dashboard\PLAN.md` line 214 |
| Mapping | An OCR cost line and wall-clock seconds per document. `document_kind` and status carried through, so zero-score rows can be filtered | `rdtii-finale-3-mapping\PLAN.md` steps 2C and 2F |

## 5. Things nobody owns yet

- **Translation.** Extraction D5 hands it to mapping or the interface. Neither plans it, and no mapping
  file mentions language at all. The live test's step 2 is "reads and translates"
  (`P\REQUIREMENTS.md` line 95). The local model `qwen2.5:14b` is weak in Lao.
- **China's manifest.** Scraping's notes say one must be built. Neither workshop has claimed the job.
- **The Lao gold page.** Needs a person who reads Lao, or a different measurement.
