# Stage result — extraction (p2-extract), 2026-09-24

**What this stage was for.** Turn the corpora collection handed over into article-level provision records that
the mapping stage can read and a judge can check: one record per provision, each carrying a quotation that is
provably a piece of the stored document, in the language the law was written in, with everything a reader needs
to get from the record back to the page.

**Status: frozen for six economies.** 766,526 provisions. Every count below can be checked against
`provisions.jsonl`, `laws.jsonl`, `doc_status.jsonl` or the corpus manifests, and the file to check is named.

---

## 1. What exists

**`C:\Users\woshi\Desktop\rdtii-finale-handoff2\`** — 5.9 GB. This is Hand-off #2.

| Economy | Provisions | Law rows | Language | Where the text came from |
| :---- | ----: | ----: | :---- | :---- |
| **Australia** | 302,243 | 1,277 | eng | 284,524 HTML, 17,719 native PDF |
| **Timor-Leste** | 189,557 | **2,879** | por | 186,827 native PDF, 2,730 OCR |
| **Singapore** | 110,661 | 738 | eng | 110,652 native PDF, 9 OCR |
| **Malaysia** | 72,505 | 1,389 | 72,359 eng / **146 msa** | 72,294 native PDF, 211 OCR |
| **China** | 50,026 | 1,085 | zho | 46,725 docx, 3,247 HTML, 54 OCR |
| **Lao PDR** | 41,534 | 1,762 | lao | **41,362 OCR**, 172 native |
| **Total** | **766,526** | **9,130** | | |

```
rdtii-finale-handoff2/
  provisions.jsonl     766,526   one grounded provision per line
  laws.jsonl             9,130   one row per ACT, not per document
  doc_status.jsonl       8,180   one row per document, including every one not read
  source_text/          14,722   the frozen text the offsets index into
  by_law/                7,361   provisions grouped per law (dashboard; mapping ignores it)
  tag_inputs.jsonl     766,526   sidecar for a later tagging pass
  extract_log.jsonl      7,417   decisions and drops
  HANDOFF2.md                    what is here, what was checked, what is missing
```

**Set `HANDOFF2_DIR` to this folder.** It defaults to `../handoff2`, which still holds **Round 1's July output** —
411,986 provisions over three economies. Mapping run without setting it will read that and look like it worked.

---

## 2. How good it is

### The grounding rule holds, and was checked against the files rather than the writer

Every `verbatim_snippet` is a character-exact substring of `source_text/<doc_id>.txt` at the recorded offsets. That
was re-checked by re-reading the frozen text from disk and comparing bytes — **18,000 records sampled across the
six economies, 0 mismatches**, and again on the merged hand-off after assembly, 5,000 sampled, 0 bad. A provision
that could not be grounded was never written.

`p2-extract validate` passes on the full Timorese corpus: `schema=PASS grounding=PASS doc_status=PASS`.

### One shape for every economy

All six have an **identical 62-field key set**, one distinct shape each, **0 off-contract enum values**, 0 schema
errors on the sampled records, and `contract_version: 0.3.0` on all 766,526. There is no economy-specific field
and no economy-specific omission.

### Citations, which is where the risk is

| Economy | exact | restart (text trusted) | repaired from position |
| :---- | ----: | ----: | ----: |
| Timor-Leste | 180,297 | 4,591 | **4,669 (2.5%)** |
| Lao PDR | 39,836 | 213 | **1,485 (3.6%)** |
| China | 50,006 | 4 | 16 (0.03%) |
| SG / AU / MY | all | — | — |

A repaired number means the text printed something the position contradicts. Every such record carries
`article_number_as_read` — what the page actually says — and `citation_confidence`, so a repair is visible rather
than silent. **A real act cited to the wrong article scores zero, so none of this is hidden.**

### Languages are read, never detected

`language_of_source` comes from the crawler's own field, or from the economy's declaration where a corpus has no
sidecar at all (China). It is never guessed from the characters. Malaysia's 146 Malay provisions are Malay because
collection flagged them, not because something looked at the script.

---

## 3. What mapping inherits that is new

| Field | Why it is there |
| :---- | :---- |
| `law_name_en` + `law_name_original` + `law_name_en_source` | **100% filled.** Stage 3 matches the English title against the host baseline, where Lao and Chinese laws are named in English. `source_is_english` for SG/AU/MY; `rendered` — machine-made and labelled — for TL, LA, CN |
| `act_index`, `act_count` | A Timorese gazette issue is one file holding several separate acts, each with its own Article 6. `act_count` is authoritative from collection's law table even where `act_index` is withheld |
| `citation_confidence`, `article_number_as_read` | Whether the article number was printed or recovered |
| `language_of_source`, `language_source` | Workbook column N, and where the language came from |
| `collection_channel`, `in_official_database`, `source_authority`, `collection_note` | Whether a document sits in the national law database or was collected by hand, with the collector's own note |
| `source_url_basis`, `access_date_basis`, `access_date_observed` | **What a provenance value rests on.** See §5 |
| `tags_source` | `llm`, `llm_failed` or `not_tagged` — so a null tag is a recorded gap, not an unexplained blank |

**`laws.jsonl` is one row per act, not per document.** Timor-Leste has 2,879 rows over 1,921 documents and 1,315
distinct law numbers. A consumer that keys it on `doc_id` will keep only the last act of each issue.

---

## 4. Every document is accounted for

No document disappears without a recorded reason.

| Economy | manifest | read | zero provisions | excluded | skipped | parse failed |
| :---- | ----: | ----: | ----: | ----: | ----: | ----: |
| Singapore | 738 | 717 | — | — | 21 linkage | — |
| Australia | 1,278 | 1,256 | 18 | — | 3 linkage | 1 |
| Malaysia | 1,391 | 900 | 13 | 92 | **384 linkage** | 2 |
| Timor-Leste | 1,921 | 1,026 | 889 | 6 | — | — |
| Lao PDR | 1,762 | 1,109 | 348 | **291 repealed** | 14 linkage | — |
| China | 1,091 | 1,061 | 24 | — | 1 superseded | 5 |

- **linkage** — collection marked the row as existing to navigate to a law, not to be the law.
- **excluded** — repealed, or provably not the instrument it is filed under. The reason is on the row.
- **zero provisions** — parsed cleanly, no citable article. Timor-Leste's 889 are appointments, decorations and
  resolutions; China's 24 carry no numbering at all.
- **parse failed** — 5 of the 8 are legacy OLE2 `.doc`, which nothing in the pinned environment reads.

---

## 5. China has a different shape, and the gaps are written down

China had no contract-shaped manifest when collection closed. One was built: **1,091 rows** over 1,092 files, from
five `provenance.tsv` files plus the database's own index. One byte-identical duplicate excluded, one superseded
row dropped, **1,090 extracted**.

Three columns carry a recorded gap rather than an invented value, because the national database forbids automated
collection and publishes no per-document address:

| Column | Filled | What the gap looks like |
| :---- | ----: | :---- |
| `access_date` | **6 of 1,090** | `access_date_basis` says which of five states; `access_date_observed` keeps collection's own string verbatim |
| `source_url` | 1,090 | 945 carry the **database root** with `source_url_basis: database_root`; traced by title, unique across all 945, plus version date |
| `http_status`, `http_headers_path` | 0 | 974 documents had no HTTP request at all |

**Constructed per-document URLs were considered and rejected**: they would look authoritative and resolve to
nothing. `corpus/CN/PROVENANCE_GAPS.md` in the extraction workshop is the full account.

**Customs collected nothing.** Its folder is empty and its README routes two of its three documents to a source
collection deferred. This is a collection gap, not an absence of Chinese customs law, and should not be read as one.

---

## 6. What was deliberately not done

| Not done | Why |
| :---- | :---- |
| **No provision is tagged.** `scope`, `data_type`, `obligation_type` are null; `tags_source: not_tagged` | These fields have no consumer in mapping. `OUTPUT_FORMAT.md` §7 records them as demoted and "not to be improved". A record must never name a model that did not judge it |
| **Nothing is translated except act titles.** The snippet stays in its source language | The host's column I says copy the exact text. A translated snippet is not verbatim and cannot be a substring of the stored text. Only the act's NAME is rendered, and every rendered title says so |
| **`act_index` is null on ~36% of Timorese provisions** | Two gates withhold rather than guess: no `act_index` unless every act the law table names was located at a distinct offset, and never for a provision whose article heading sits in a different act than its text. A partial split silently folds one act's articles into another. `act_count` stays authoritative |
| **5 legacy OLE2 `.doc` unread** | Needs a dependency added days before freeze. Recorded as `parse_failed` with the reason |
| **The Round 1 regression was not run** | See below. This is the one worth knowing about |

### The limit of what has been checked

Every check run on this stage is **internal**: self-consistency across economies, determinism per lane, grounding
against our own frozen text, conformance to our own schemas. All of it says the output agrees with itself.

Nothing compared it to an independent baseline. 1,117 documents are byte-identical between Round 1 and this round
and could have been diffed. That was judged not worth the remaining time — and it is the only check that could
surface a systematic error every internal check reproduces faithfully. **That is not hypothetical:** a bug that
emitted the same provision twice wherever an article citation repeated lived in Round 1's code, shipped in Round
1's output, and survived three of this stage's own audits before being caught. It cost 6,321 duplicated records in
Malaysia alone.

---

## 7. Where things are

| | |
| :---- | :---- |
| Hand-off #2 | `C:\Users\woshi\Desktop\rdtii-finale-handoff2\` — point `HANDOFF2_DIR` here |
| Code | `stages/p2-extract/`, branch **`p2-extract-contract-0.3.0`**, pushed. 126 tests pass in the repository |
| Contract | **0.3.0**, MINOR. Additive or loosening throughout; both stages' vendored schemas are byte-identical |
| Working notes | `rdtii-finale-2-extraction/` — `CHANGELOG.md`, `OPEN_ISSUES.md`, `REFRESH.md`, `OUTPUT_FORMAT.md` |

**The contract bump is not optional for mapping.** Its vendored schema had `economy: enum ["SG","AU","MY"]`, a
doc_id pattern of `^(sg|au|my)-` and `additionalProperties: false` against 27 new fields. Before the bump it
rejected every record this stage emits, **including Singapore's**. The branch carries the updated copy into
`stages/p3-map/` as well; both are byte-identical.

### A new batch from collection

Four commands, documented in `REFRESH.md`:

```
python tools/import_corpora.py    # finds the newest <CC>_corpus_<date>, hashes it
python tools/refresh.py           # what changed? reads only, writes nothing
python tools/refresh.py --run     # extracts only that, and fills the titles
python tools/render_law_titles.py --all
```

`refresh` compares by `content_sha256`, not by date: a re-crawl rewrites `access_date` on every row, so a date
comparison marks the whole corpus changed. **Withdrawn documents are reported, never deleted** — a dropped
document and a short batch look identical from here, and those are opposite situations.

Verified end to end: re-extracting a single Singapore document left 110,661 provisions, 717 documents, 738 law
rows and 738 doc_status rows exactly as they were, with 0 duplicate ids. A partial run does not truncate the corpus.
