# Output format of the extraction stage

**Settled 2026-09-23.** One shape for all six economies, whether a document was crawled from a
national law database or downloaded by hand from a ministry that refuses an automated client.

Three things had to agree, and this format is the intersection:

| Master | What it demands |
| :---- | :---- |
| The host's workbook, `OUTPUT_TEMPLATE_FINAL_ROUND.xlsx` | 15 columns, including **Language of Source** ("Thai, Vietnamese, Bahasa Indonesia, Russian, English. Drives criterion C1c") and **Notes** ("flag unusual cases, bilingual sources, OCR issues") |
| Stage 3, mapping | Reads exactly four artefacts and nothing else: `provisions.jsonl`, `laws.jsonl`, `doc_status.jsonl`, `source_text/`. It never reads `by_law/`, `extract_log.jsonl` or the manifest, so **anything new must land on one of those four or it will not be seen** |
| The developer, 2026-09-23 | A document that is not in the economy's official law database must say so, and a hand-collected document must carry the collector's own note |

The grounding rule is unchanged and is not negotiable (D1): `verbatim_snippet` is a character-exact
substring of `source_text/<doc_id>.txt` at the recorded offsets, re-verified before the record is
written, and a provision that cannot be grounded is not emitted.

## 0. The language rule: English everywhere except the quote

**Every field a reader reads is English. One field is not, and that is the evidence.**

| In English | In the source language |
| :---- | :---- |
| Economy, Law Name, Law Number, Last Amended, Indicator ID, Article / Section, Discovery Tag, Location Reference, Mapping Rationale, Source URL, Confidence, Notes, Language of Source | **`verbatim_snippet`**, and the frozen `source_text` it is cut from |

The exception is the host's rule, not ours. Column I says "Copy the EXACT text — no edits, no
paraphrasing", and column N, **Language of Source**, exists precisely *because* the quote is not in
English: it tells the reader which language they are looking at. A translated snippet is not
verbatim, cannot be a character-exact substring of the stored text, and would end both D1 and the
citation-fidelity claim with it.

**So the law's title must be carried twice.** The workbook's Law Name column is read by a judge and
matched by stage 3 against the host's baseline, where Lao and Chinese laws are named **in English**.
A record that offers only `ກົດໝາຍວ່າດ້ວຍ ຄວາມປອດໄພໄຊເບີ` cannot be matched, so every Lao row would
be tagged NEW by default — a scoring consequence, not a presentation one.

| Field | Holds |
| :---- | :---- |
| `law_name_original` | The title as the source prints it: `ກົດໝາຍວ່າດ້ວຍ ຄວາມປອດໄພໄຊເບີ` |
| `law_name_en` | The English title, which is what the workbook's column B carries: "Law on Cyber Security" |
| `law_name_en_source` | `publisher_translation` \| `rendered` \| `none` — **where the English title came from** |

Titles are a bounded and far safer task than provisions: a title is a name, it is one line, it never
enters the evidence column, and for Lao there is an authoritative source. The gazette published its
own English edition of 53 laws, and the English title is printed on their cover pages — those are
`publisher_translation`. Everything else is `rendered`, labelled as such, and a reviewer can see at a
glance which titles were machine-made. Nothing is ever taken from the host's own database: that is
rule D4, and it would be selection from the gold set.

**Note for the crawler:** the manifest's `law_name_guess` for all 53 English Lao documents holds the
**Lao** title, not the English one, so the English title has to be read from the PDF rather than
joined from a column.

---

## 1. The artefacts

```
handoff2/
  provisions.jsonl        one grounded provision per line
  laws.jsonl              one row per LAW (not per document) that the stage read
  doc_status.jsonl        one row per document, including the ones deliberately excluded
  source_text/<doc_id>.txt   the frozen text the offsets index into, UTF-8, LF, no BOM
  ocr/<doc_id>/           per-page OCR text, confidences, seconds - the cache and the evidence
  by_law/<doc_id>.json    provisions grouped per law (kept for the dashboard; mapping ignores it)
  extract_log.jsonl       append-only decisions and drops
  cost_report.json        seconds and cost per document
```

---

## 2. `provisions.jsonl`

### 2.1 Identity and law

| Field | Type | Req | Where it comes from | Who reads it |
| :---- | :---- | :--: | :---- | :---- |
| `contract_version` | SemVer | ✅ | settings | version gate |
| `provision_id` | string | ✅ | `<doc_id>#<article_section>`, or `<doc_id>#a<act_index>#<article_section>` when one document holds several acts | mapping key, export |
| `doc_id` | string | ✅ | manifest | join to everything |
| `economy` | `^[A-Z]{2}$` | ✅ | manifest | workbook column A, via the UN-name table |
| `law_name_en` | string | ✅ | **English** title of the act. What workbook column B carries | workbook B, and stage 3's NEW/KNOWN match against the host baseline |
| `law_name_original` | string | ✅ | The act's title as printed, in the source language | audit, the dashboard's source view |
| `law_name_en_source` | `publisher_translation` \| `rendered` \| `none` | ✅ | Where the English title came from, so a machine-made name is visible as one | review |
| `law_number` | string \| null | ✅ | the act's official number | workbook C |
| `last_amended` | string \| null | ✅ | law tracker, else the text | workbook D |
| `act_index` | int \| null | ✅ | position of the act inside the document, 1-based; null when the document is one law | disambiguates a gazette issue |
| `act_count` | int | ✅ | how many acts the document holds | review, and a signal that splitting happened |

**Why act identity is a field and not a convention.** A Timorese gazette issue holds up to 39
separate acts under one `doc_id`. Without `act_index` two acts in one issue both produce
`#Art. 5` and collide, and stage 3 groups the whole issue under a single law name. Measured: 911 of
1,921 Timorese documents carry more than one law.

### 2.2 The citation

| Field | Type | Req | Notes |
| :---- | :---- | :--: | :---- |
| `article_section` | string | ✅ | The host asks for "Art. 26(2) or S 13(1)(a)". Common law writes `s. 26(1)`, civil law `Art. 26(2)`, China `Art. 26`. One form per legal tradition, chosen by the document's language, never mixed |
| `article_number_as_read` | string \| null | ✅ | What OCR actually read, before any repair |
| `citation_confidence` | `exact` \| `sequence_repaired` \| `unverified` | ✅ | How the number was arrived at |
| `citation_repair_method` | string \| null | ⬜ | e.g. `ascending_sequence`, when repaired |
| `page` | int \| null | ✅ | The printed page. Separate from the prose locator so it is machine-usable |
| `location_reference` | string \| null | ✅ | Human locator, workbook column H: "Part VI, p.42" |

**Why `citation_confidence` exists.** Measured on Lao scans: article markers survive OCR (`ມາດຕາ`
found at line start 19 times of 19 in one law) but **the digits after them are misread** — 30 read
as 90, 32 as 92, 38 as 88. Corpus-wide the article-number sequence agreement is **0.856**, so about
one Lao article number in seven is wrong as read. The number is recoverable from position because
articles ascend, but a silently repaired citation is a wrong citation nobody can see, and "a real
act cited to the wrong section scores zero". So the repair is recorded, not hidden, and a citation
that cannot be resolved either way is `unverified` and can be filtered rather than published.

### 2.3 The evidence

| Field | Type | Req | Notes |
| :---- | :---- | :--: | :---- |
| `verbatim_snippet` | string | ✅ | Character-exact substring of the frozen text. Never translated, never repaired, never normalised after freezing |
| `snippet_char_start` / `_end` | int | ✅ | Character offsets into `source_text/<doc_id>.txt` |
| `snippet_source` | `html` \| `native` \| `ocr` \| `docx` | ✅ | Where the characters came from. `ocr` is what puts "quoted from OCR" in the workbook's Notes |
| `raw_context_before` / `_after` | string | ✅ | ~200 characters either side. **Load-bearing**: stage 3 indexes them for retrieval and permits the model to quote from them, so they must be publishable text |
| `source_url` | URL | ✅ | `citation_url` when the crawler recorded one, else `source_url` |

### 2.3a Where the law's text lives, and in which language

**The full text is stored once, in the original language.** `source_text/<doc_id>.txt` holds the
whole document — every page, normalised once and frozen — and every offset in every record indexes
into it. That file is the grounding reference and the thing `validate` re-proves against. There is
no second copy and no translated copy of it, deliberately: a second full text would be a second
candidate for "the text of record", and the first time someone quoted the wrong one the citation
guarantee would be gone.

**English is carried per provision, never per document, and never with offsets.**

| Field | Scope | Cost | Status |
| :---- | :---- | :---- | :---- |
| `law_name_en` | every record | trivial | **In.** The workbook's Law Name column needs it |
| `article_heading_en` | every provision of a non-English document | ~0.5 s each: **6.5 h for Lao**, about 20 h for Lao, Chinese and Portuguese together | **Proposed, phase 2.** Restores mapping's English BM25 leg, which finds nothing in Lao today |
| `snippet_en` | only the provisions a model actually reads — **measured on Round 1: 5.77% of provisions reach triage, 2.62% reach the judge**, about 8,000 and 3,600 per economy | **12.7 h and 5.7 h for Lao** at 5.7 s a provision | **Proposed, and it belongs to stage 3 — and only if the judging model cannot read the language** |

**The rule that keeps this safe: no character offset ever points into English text.** Offsets exist
only for `verbatim_snippet` and the grounded metadata, and they only ever index
`source_text/<doc_id>.txt`. An English field is a labelled derivative with no offsets, so it cannot
be mistaken for evidence by any consumer, including a careless one.

**Why not a full English `source_text_en/`:** 47,645 Lao provisions at 5.7 s each is 75 hours, and
Timor-Leste and China would roughly triple it. It would also be the second text of record described
above.

**How much would actually be translated, measured rather than guessed.** Round 1's own run:
triage read 23,765 distinct provisions (5.77%), the judge read 10,792 (2.62% of provisions, 2.96%
of the text), and 142 rows were published (0.03%). Mapping's caps are **per economy and absolute**,
not proportional, so a smaller corpus gives a larger share: for Lao's ~47,600 provisions the same
caps mean roughly **17% read by some model and 8% judged**.

**But the honest answer is that it depends on the engine, not on the corpus.** A judging model that
reads Lao needs no gloss at all; one that does not needs about 18 hours of it for Lao. That is a
real cost difference between the two declared engines and belongs in the engine comparison, not
buried here. Note also that glossing **every** article heading (6.5 h) is cheaper than glossing the
candidate bodies (18 h) and helps retrieval as well, so if only one is affordable it is the
headings.

### 2.4 Collection provenance — new, and the reason this document exists

Every record carries how its bytes were obtained. Same fields for every economy.

| Field | Values | Notes |
| :---- | :---- | :---- |
| `collection_channel` | `portal_crawl` \| `api` \| `hand_collected` | How it was retrieved. `hand_collected` is not a defect: `flk.npc.gov.cn` forbids automated collection in its robots.txt, and MIIT and Customs refuse an honest client |
| `in_official_database` | true \| false \| null | **Whether the economy's official law database carries this document.** False for a Chinese departmental rule, which the Legislation Law files with the State Council rather than the NPC. Null where the economy has no single database |
| `source_authority` | `national_database` \| `official_gazette` \| `ministry_site` \| `agency_announcement` \| `mirror` | Which tier published the copy we hold. `mirror` matters: two Chinese customs documents are held only as a gov.cn or MOFCOM mirror, and must cite the mirror |
| `collection_note` | string \| null | **The collector's own words, carried verbatim** from the hand-collection provenance sheet. For example: "The saved page is the 1-page 通告 wrapper only — the catalogue itself is the attachment" |
| `content_flags` | array of strings | Collection's own flags, carried and never resolved: `repeal_notice`, `no_text_layer`, `short_principal`, `language_mismatch`, `other_act_text`, `no_sumario`, `duplicate_content`, `as_made_short_act`, … |
| `provenance_ref` | string \| null | Where to check: the provenance sheet and row, e.g. `manual/miit/provenance.tsv#14` |

This is what lets the workbook's Notes column say, truthfully and per row: *"Collected by hand from
the issuing ministry; not carried by the national law database."*

### 2.5 The law's own status

| Field | Values | Notes |
| :---- | :---- | :---- |
| `language_of_source` | ISO 639-3 (`lao`, `por`, `zho`, `eng`, `msa`) | Read from the crawler, never detected (D3) |
| `language_of_source_name` | `Lao`, `Portuguese`, `Chinese`, `English`, `Malay` | What the workbook's column N actually wants |
| `language_source` | `portal_field` \| `registry_default` \| `content_flag` \| `economy_default` | How the language was known. `content_flag` covers the seven Malaysian rows the crawler labelled `eng` and flagged `language_mismatch`: reading the flag is reading a crawler field, not detecting. `economy_default` covers a corpus with no sidecar at all — China has neither `law_table.csv` nor `links_used/`, so the language comes from the economy's own declaration in `corpus/economies.json`. Still a declaration that was read, never a detection (D3) |
| `document_kind` | `principal_act`, `amending_act`, `subsidiary_legislation`, `official_announcement`, … | From the law tracker. Lets mapping drop an amending act cited instead of the principal |
| `legal_status` | `in_force`, `repealed`, `not_yet_in_force`, `unknown` | From the law tracker, as the portal states it |
| `use` | `evidence`, `linkage`, … | The law tracker's own column. `linkage` rows are not extracted at all |

### 2.6 Quality and processing

| Field | Type | Notes |
| :---- | :---- | :---- |
| `ocr_engine` | string \| null | Engine and version pinned per document, e.g. `tesseract-5.4.0.20240606-lao` |
| `ocr_quality_cer` | number \| null | **Null unless a figure was measured for that script.** Never an English figure on a Lao page |
| `ocr_cer_method` | `gold_page` \| `native_twin` \| `rendered_twin` \| `estimate` \| `none` | What the number is. Only the first two may support the under-5% claim |
| `ocr_script` | `lao`, `por`, `zho`, `eng` \| null | Which script the figure belongs to |
| `extraction_model` | string \| **null** | The model that produced this record's **tags**, and null when none has run. Never the configured default: the record must not name a model that did not judge it |
| `tags_source` | `llm` \| `llm_failed` \| `not_tagged` | Which of the three states `scope`/`data_type`/`obligation_type` are in. `not_tagged` means all three are null and no model has run |
| `processing_seconds` | number | Per document wall clock, for the cost table |
| `access_date` | ISO UTC | From the manifest |

---

## 3. `laws.jsonl` — one row per law, and the exclusion channel

One row per **act**, not per document, so a Timorese issue yields many. Every row the stage read
appears, including the ones that yielded nothing and the ones deliberately excluded.

| Field | Notes |
| :---- | :---- |
| `doc_id`, `act_index`, `economy`, `law_name_en`, `law_name_original`, `law_number`, `source_url` | Identity. The English title is what stage 3 matches against the host baseline |
| `provision_count` | 0 is meaningful and must be kept |
| `coverage_status` | **New.** `searched` \| `zero_provisions` \| `excluded` \| `not_automated` |
| `exclusion_reason` | **New.** Why, in words, when `excluded` |
| `language_of_source`, `document_kind`, `legal_status`, `use` | As above |
| `collection_channel`, `in_official_database`, `source_authority`, `collection_note`, `content_flags` | As above |
| `pillars_in_scope`, `indicators_searched` | Hints only, decimal ids accepted |
| `notes` | Free text for a reviewer |

**Why `coverage_status` is not optional.** Stage 3 emits a "No provision found" row when an indicator
has no row, and it picks the governing law to cite by fuzzy-matching law names across `laws.jsonl`.
Today nothing stops it citing a document that extraction deliberately excluded — so a Malaysian
repeal notice filed as an act could become the citation for a "no provision" claim. `excluded` plus a
reason closes that, and it is also what makes the exclusion visible to a judge instead of a silent
gap.

---

## 4. `doc_status.jsonl`

One row per document: `doc_id`, `status` (`ok`, `zero_provisions`, `parse_failed`, `excluded`),
`reason`, `pages`, `ocr_pages`, `ocr_seconds`, `ocr_retries`, `acts_found`, `content_flags`,
`collection_channel`. This is the per-document ledger the run note and the cost table are built from.

---

## 5. How a row reaches the workbook

Stage 3 writes the workbook; this is where each column's content originates.

| # | Column | Comes from |
| --: | :---- | :---- |
| A | Economy | `economy`, expanded to the official UN name |
| B | Law Name | `law_name_en` — **the act's English title**, not the document's. `law_name_original` travels beside it and can be shown in Notes |
| C | Law Number / Ref | `law_number` |
| D | Last Amended | `last_amended` |
| E | Indicator ID | Stage 3, decimal text (`6.4`) |
| F | Article / Section | `article_section` |
| G | Discovery Tag | Stage 3 (NEW / KNOWN) |
| H | Location Reference | `location_reference`, built from `page` |
| I | Verbatim Snippet | the model's quote, grounded against `source_text` |
| J | Mapping Rationale | Stage 3 |
| K | Source URL | `source_url` |
| L | Confidence | Stage 3 |
| M | **Notes** | Composed from `content_flags`, `collection_channel`, `in_official_database`, `collection_note`, `snippet_source` and `citation_confidence` |
| N | **Language of Source** | `language_of_source_name` |
| O | Pillar | formula in the template |

---

## 6. The same shape in six economies

| | Channel | In the official database | Authority | Language | The wrinkle |
| :---- | :---- | :---- | :---- | :---- | :---- |
| Singapore | `portal_crawl` | true | `national_database` | `eng` | none |
| Australia | `portal_crawl` | true | `national_database` | `eng` | 793 documents are HTML |
| Malaysia | `portal_crawl` | true | `national_database` | `eng`, `msa` | 7 rows are Malay behind an English label; the flag corrects the language |
| Timor-Leste | `portal_crawl` | true | `official_gazette` | `por` | one PDF holds many acts, so `act_index` is used |
| Lao PDR | `portal_crawl` | true | `official_gazette` | `lao` | 96% scans, so `snippet_source` is `ocr` and `citation_confidence` carries the repair |
| China, layer 1 | `hand_collected` | **true** | `national_database` | `zho` | 943 `.docx`; hand-collected because robots.txt forbids automation |
| China, layer 2 | `hand_collected` or `portal_crawl` | **false** | `ministry_site` | `zho` | departmental rules the national database does not carry — the distinction this format exists to record |

---

## 7. What Round 1 carried that this drops

Checked against stage 3's source: these have **no consumer anywhere**.

| Dropped | Evidence |
| :---- | :---- |
| `scope` | Written into the prefilter corpus and never read |
| `extraction_confidence`, `extraction_confidence_note` | Zero readers. Set on 411,986 of 411,986 Round 1 records, 73% at or below 0.2, clustered on a 0.05 ladder — a model tic, not a measurement |
| `law_name_grounded`, `law_name_char_*`, `law_number_char_*`, `last_amended_char_*` | Zero readers |
| `model_version`, `instrument_version` | Stage 3 rebuilds its own |

`obligation_type` and `data_type` are **kept but demoted**: only four of `obligation_type`'s ten
values affect retrieval, and they reach 0.6% of records. They stay because they are free, and
because removing a field costs a contract bump; they are not to be improved.

---

## 8. Versioning, and who has to agree

Every field here is additive and optional, except the widened patterns, so this is a **MINOR** bump
to `0.3.0` under §8 of the interface contract. Three things must land in one commit or the pipeline
breaks:

1. `code\00_contracts\schemas\{provision,laws,manifest}.schema.json` — widen `economy` to
   `^[A-Z]{2}$`, `doc_id` and `provision_id` to `^[a-z]{2}-[a-z0-9]+-\d{3}(#.+)?$`, pillars to 1–12,
   `source_type` to add `docx`, and add every field above.
2. The same schema files vendored into `stages\p3-map\00_contracts\schemas\` — mapping validates
   against its own copy and rejects Hand-off #2 otherwise.
3. `stages\p3-map` must learn the new economies: `ECONOMIES = ["SG","AU","MY"]`
   (`config\settings.py:78`) silently drops every Lao, Timorese and Chinese candidate, and
   `ECON_NAME` needs the UN names.

Item 3 is mapping's work, not extraction's, but it is the reason a clean Hand-off #2 would still
produce an empty workbook. It is raised with that workshop.

---

## 9. Worked examples

A Lao provision, OCR'd, article number repaired from position:

```json
{"provision_id": "la-la2537-001#Art. 30", "doc_id": "la-la2537-001", "economy": "LA",
 "law_name_en": "Law on Cyber Security", "law_name_en_source": "publisher_translation",
 "law_name_original": "ກົດໝາຍວ່າດ້ວຍ ຄວາມປອດໄພໄຊເບີ", "law_number": "33/ສພຊ", "act_index": null, "act_count": 1,
 "article_section": "Art. 30", "article_number_as_read": "90", "citation_confidence": "sequence_repaired",
 "citation_repair_method": "ascending_sequence", "page": 12,
 "verbatim_snippet": "ມາດຕາ 30 ...", "snippet_char_start": 18422, "snippet_char_end": 18980,
 "snippet_source": "ocr", "language_of_source": "lao", "language_of_source_name": "Lao",
 "language_source": "portal_field", "collection_channel": "portal_crawl",
 "in_official_database": true, "source_authority": "official_gazette", "collection_note": null,
 "content_flags": ["no_text_layer"], "document_kind": "principal_act", "legal_status": "unknown",
 "use": "evidence", "ocr_engine": "tesseract-5.4.0.20240606-lao", "ocr_quality_cer": null,
 "ocr_cer_method": "none", "ocr_script": "lao", "extraction_model": null, "tags_source": "not_tagged"}
```

A Chinese departmental rule, hand-collected, **not** in the national database:

```json
{"provision_id": "cn-miit014#Art. 8", "doc_id": "cn-miit014", "economy": "CN",
 "law_name_en": "Catalogue of Telecommunications Services (2015 edition)", "law_name_en_source": "rendered",
 "law_name_original": "电信业务分类目录（2015年版）", "article_section": "Art. 8", "citation_confidence": "exact",
 "snippet_source": "docx", "language_of_source": "zho", "language_of_source_name": "Chinese",
 "language_source": "registry_default", "collection_channel": "hand_collected",
 "in_official_database": false, "source_authority": "ministry_site",
 "collection_note": "by hand — 403 to any honest client; the catalogue is the attachment",
 "provenance_ref": "manual/miit/provenance.tsv#1", "content_flags": [],
 "document_kind": "subsidiary_legislation", "legal_status": "in_force"}
```

A Timorese act inside a gazette issue that holds two. **This is a real case, not an invented
one**: `tl-ldcn-001` carries Lei 1/2026 (competition) and Decreto-Lei 13/2026 (fuel prices), and
**both have an Article 6**. Without `act_index` the second is published as the first:

```json
{"provision_id": "tl-ldcn-001#a2#Art. 6", "doc_id": "tl-ldcn-001", "economy": "TL",
 "law_name_en": "Temporary Fuel Price Stabilisation and Security of Supply Measures", "law_name_en_source": "rendered",
 "law_name_original": "Medidas de Estabilização Temporária do Preço dos Combustíveis",
 "law_number": "Decreto-Lei N.º 13/2026", "act_index": 2, "act_count": 2,
 "article_section": "Art. 6", "citation_confidence": "exact", "page": 284,
 "snippet_source": "native", "language_of_source": "por", "language_of_source_name": "Portuguese",
 "collection_channel": "portal_crawl", "in_official_database": true,
 "source_authority": "official_gazette", "content_flags": []}
```

The sibling record for the same document carries `act_index: 1`,
`law_name: "Lei da Concorrência"`, `law_number: "Lei N.º 1/2026"` and `page: 276` — its own
Article 6 is "Práticas restritivas horizontais".

---

## 10. Still open

| Question | Who decides |
| :---- | :---- |
| Whether stage 3 will read `act_index` and group by act rather than by document | mapping |
| The citation form per tradition, checked against the host's own Round 2 rows — `Art. 26(2)` is the template's example, but the host's Lao and Chinese rows have not been seen | developer, without reading the gold set for selection |
| Whether `in_official_database` should also appear as its own workbook column rather than only inside Notes | developer, and it is a question for the host |
| Re-merging the Lao corpus so the 53 official English translations are addressable | collection |
