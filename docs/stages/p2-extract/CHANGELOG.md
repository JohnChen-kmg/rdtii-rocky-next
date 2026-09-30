# Changelog — extraction workshop

Three lines per change: what, why, how it was verified. Newest last. Code changes land in
`code/`, which is a working copy of `stages/p2-extract` and is handed back in one commit (D9).

---

## 2026-09-23 — corpora imported

**What:** `corpus/<CC>/` for six economies, metadata copied and hashed (49 files,
`corpus/PROVENANCE.tsv`), `raw/` addressed through a directory junction rather than copied.
**Why:** extraction must join on the manifest, the law table and the link rows, so those are frozen
here; the 9.2 GB of PDFs must stay byte-identical to collection's corpus, so they live once.
**Verified:** all five junctions resolve to real files of the expected size; China's 11 archives are
present; manifest row counts match collection's (LA 1,762 · TL 1,921 · MY 1,391 · SG 738 · AU 1,278).

## 2026-09-23 — W1, the ingest gate widened to six economies

**What:** `code/00_contracts/schemas/{manifest,provision,laws}.schema.json` — `economy` from the
enum `SG|AU|MY` to `^[A-Z]{2}$`; `doc_id` to `^[a-z]{2}-[a-z0-9]+-\d{3}$`; `provision_id` gains an
optional `#a<act_index>` for a document holding several acts; `source_type` gains `docx` and `doc`;
`retrieval_method` gains `hand_collected`; `pillar_hint` accepts pillar numbers as text;
`pillars_in_scope` becomes integers 1 to 12; indicator patterns accept decimal ids beside legacy ones.
Applied by `tools/widen_schemas.py`, which edits the parsed JSON and is idempotent.
**Why:** the Round 1 gate refused every Lao and Timorese row — 3,524 errors on 1,762 Lao documents,
two per row. Nothing else could start until it opened.
**Verified:** all five corpora now load (SG 738 · AU 1,278 · MY 1,391 · TL 1,921 · LA 1,762, 7,090
documents); Round 1's `handoff1_v2` still loads at exactly 2,673 rows, so the widening broke no
existing behaviour; 80 tests pass, 2 skipped, unchanged from the baseline.

## 2026-09-23 — W2, a run no longer demands a model

**What:** `code/src/rdtii_p2/cli.py` — `preflight(..., needs_llm=True)` became
`needs_llm=not args.skip_tags`.
**Why:** the hard-coded flag made `run --skip-tags` fail on a machine with no pulled Ollama model
and no API key, which is the finale's normal mode and the clean-machine case the deployment test
uses. The tags are soft hints that mapping mostly ignores.
**Verified:** Singapore ran end to end with no model present — 738 documents, 111,748 provisions.

## 2026-09-23 — W14, the gate reads what collection knew, and says what it did not read

**What:** new `code/src/rdtii_p2/sidecars.py` joins `law_table.csv` and
`links_used/documents.jsonl` on `contract_meta.corpus.doc_id`, resolves each document's language
with its provenance, and decides read / skip / exclude. `status.py` gains the `excluded` and
`skipped` statuses, which **require a reason**, and carries the collection facts. `cli.py` writes
those rows before any processing, and `run` gains `--default-language` and `--mismatch-language`.
**Why:** the manifest carries neither language, nor `use`, nor whether collection flagged the stored
file as not being the law it is filed under. Without them extraction would read 76 Malaysian repeal
notices and 5 files holding a different act, and would stamp `eng` on 7 Malay documents.
**Verified:** counts reconcile with collection's independent measurement — Malaysia 92 excluded
(their 87 to drop, plus the 5 wrong-file documents that stay in the corpus and correctly yield
nothing), Lao 291, Timor-Leste 6, Australia 3 linkage skips. Every document now resolves a language
with a recorded source; Act 680 correctly reads `msa` via `content_flag`.

## 2026-09-23 — W15, the record carries provenance, act identity and citation standing

**What:** `extract_fields.build_record` gains 23 fields and `provision.schema.json` the matching
entries: the collection provenance block, `language_of_source` with its display name and source,
`law_name_en` / `law_name_original` / `law_name_en_source`, `act_index` / `act_count`,
`article_number_as_read` / `citation_confidence` / `citation_repair_method`, `page`, and
`ocr_cer_method` / `ocr_script`. `provision_id` becomes `<doc_id>#a<n>#<section>` when a document
holds several acts. Additive: nothing existing was removed or re-meant.
**Why:** `OUTPUT_FORMAT.md`. The workbook's Notes and Language of Source columns, stage 3's law-name
match, and the Lao citation repair all need fields that did not exist.
**Verified:** Act 680 carries `language_of_source: msa` via `content_flag` with the flag itself in
`content_flags`; 44 records validate against the widened schema with 0 errors; 80 tests pass.

**Not done, deliberately:** `scope` and `extraction_confidence` have no reader anywhere in stage 3,
but both sit in the required list of the mapping stage's own schema copy, so removing them is a
coordinated change with that workshop rather than a one-sided one.

## 2026-09-23 — W6, article headings survive normalisation

**What:** `normalize.py` gains `is_structural_heading()` and the furniture detector skips those
lines. Protects the Portuguese (`Artigo`, `Capítulo`, `Secção`, `Título`, `Anexo`), Lao (ມາດຕາ,
ພາກ, ໝວດ) and Chinese (第…条/章/节, 附件) heading forms. **English is deliberately not protected**,
because a common-law heading carries its own words so it never looks like furniture — which means
the Round 1 regression cannot move.
**Why:** the detector masks digits, so in a civil-law statute every article heading collapses to one
shape, repeats on most pages, and is deleted. `tl-ldcn-001` went from 41 `Artigo` headings in the
raw text to none after normalisation, taking the segmenter's only anchors with it.
**Verified:** three Timorese acts keep 41, 40 and 239 headings, while `Jornal da República` and the
`Série I … Página #` line are still removed as furniture. No line in a Singapore act matches any
protected pattern. 80 tests pass.

## 2026-09-23 — normalisation was non-deterministic; now it is not

**What:** `_clean_page` built its affix-stripping patterns by iterating `furniture`, a `set[str]`.
Now it iterates `sorted(furniture, key=lambda s: (-len(s), s))` — longest shape first, then
alphabetical.
**Why:** the patterns are applied in sequence and each rewrites the line, so two overlapping
furniture shapes gave different output depending on which was tried first. Set iteration order
depends on Python's per-process string hashing, so **the same document normalised to different text
on different runs**. `source_text` is what every character offset indexes into, so this meant a
re-run could leave earlier offsets pointing at the wrong characters, and it would have produced
phantom differences in the English regression.
**Found by:** the regression check itself — 59 of 60 Singapore documents were byte-identical and one
was not, and the one that was not had no protected heading in it, so the furniture change could not
explain it. Three runs of that document gave 17,440, 17,512 and 17,440 characters.
**Verified:** five separate processes now produce an identical sha256; 80 tests pass.

## 2026-09-23 — W5, a segmenter for the civil-law and CJK traditions

**What:** new `code/src/rdtii_p2/segment_civil.py` with three profiles — `por` (Artigo N.º,
numbered paragraphs "N.", CAPÍTULO/SECÇÃO/TÍTULO), `lao` (ມາດຕາ, ພາກ, ໝວດ) and `zho` (第N条,
chapters, sections, 附件, with a Chinese-numeral parser). `cli._segment_for` picks the profile from
the document's **declared language**, never by trying patterns on the text, and English keeps
`segment.py` untouched. Citations follow the host's template: `Art. 26(2)`.
Also in the profile: the contents block is dropped (a statute restates its headings up front, and
left in, every article is found twice with no body), the article's own title is captured as the span
heading, and the hierarchy keeps the most recent division at each level rather than the last two
headings seen.
**Why:** the Round 1 segmenter is common-law only. On Timorese acts it produced 3 to 8 spans cited
`s.1`, `s.2` against documents numbered `Artigo 1.º` — confidently wrong citations, which cost more
than missing ones.
**Verified:** three Timorese acts segment to 40, 39 and 26 articles with 0 contents entries left in;
the Competition Law extracts 98 grounded provisions cited `Art. 2(1)`, `Art. 6(1)`…, all 98
re-verified as character-exact, Language of Source "Portuguese"; 80 tests still pass.

**Built but not yet exercised:** the `lao` and `zho` profiles, including the article-number repair
that Lao needs. They run when those corpora do.

## 2026-09-23 — W3 and W4, per-document OCR language and a parallel pre-pass

**What:** new `code/config/ocr/langmap.py` maps the crawler's ISO 639-3 language to a Tesseract
pack (`zho` → `chi_sim`, `msa` → `msa+eng`), points `TESSDATA_PREFIX` at the packs vendored here
**in code rather than asking a reviewer to export it**, and fails before a run with the exact
download line when a pack is missing. `get_ocr(settings, language=...)` takes the document's
language; `OCR_LANG` remains an override, never the silent source.
New `ocr_cache.py` and `ocr_prepass.py`, and a new `p2-extract ocr` command: the scanned documents
of a corpus are OCR'd across a process pool into a **per-page cache keyed on the file's sha256, the
engine, the language and the DPI**. Lane C reads that cache.
**Why:** Lao PDR is 19,058 pages of evidence-use scans. In the run loop, one page at a time with the
double pass, that is about fourteen hours; and the Round 1 cache was keyed on `doc_id` alone, so it
went stale silently when the language or the engine changed.
**Design forced by measurement:** a page that dies is retried up to three times and the pool stays
alive, because Tesseract crashes intermittently under parallel load (exit 3221225477 at 20 and 24
workers, the same page succeeding on retry); the default is 16 workers because scaling flattens
after 12; and the confidence pass is off for bulk, which halves the work and **cannot change a
character of the text**, since the text comes from `image_to_string` either way.
**Verified:** the Lao Cyber Security Law OCR'd 26 pages at 7.9 pages/s, then extracted 81 articles
with all 81 grounded exactly, Language of Source "Lao", `snippet_source: ocr`,
`ocr_engine: tesseract-lao`. **10 article numbers were repaired from sequence** — OCR read 92, 96,
850, 858 where the statute says 32, 36, 50, 58 — and each record carries
`article_number_as_read` and `citation_repair_method` so the repair is auditable rather than silent.
80 tests pass; the two lane C stubs were updated to the new `get_ocr` signature.

## 2026-09-23 — the OCR pre-pass now writes as it goes

**What:** `ocr_prepass.run_prepass` moved from `pool.map` to `pool.imap_unordered`, writing each
document into the cache the moment its own last page returns, with a progress line every 250 pages.
New `code/tests/test_ocr_prepass.py` asserts the property directly: document N is readable from
disk while document N+1 is still being read.
**Why:** found three minutes into the Lao run, by asking why only one document was cached. `map`
returns nothing until every page of every document is finished, so 19,058 Lao pages would have
produced **nothing on disk until the last one** — and a pool lost to one of the Tesseract access
violations the retry logic exists for would have thrown the whole pass away. `ocr_cache`'s own
docstring promised "a killed run resumable"; `map` made that untrue, and the promise is the reason
the cache exists at all.
**Verified:** 84 documents cached in the first two minutes of the restarted run, against one in the
first three of the old one; measured rate 1,032 pages/min (17.2 pages/s) across 14 workers, faster
than the 14.1 estimated. 83 tests pass, 2 skipped.
**Known and not changed:** `cli.cmd_run` still calls `emit.write_provisions` once after the document
loop, so a run's provisions appear only at the end. That is survivable at 30 minutes a corpus and
the Timor-Leste run was nearly finished when this was found; it is worth revisiting if a corpus ever
gets long enough that losing a run matters.

## 2026-09-23 — W8 begins: China's 945 database documents unpacked

**What:** new `tools/unpack_cn.py` extracts the national law database's 11 bulk-download archives
into `corpus/CN/manual/npc-database/unpacked/`. **945 members: 942 `.docx` and 3 `.doc`**, no
duplicates across the eleven archives.
**Why nothing is written into `raw/`:** those archives are the artifact of record. The database
forbids automated collection, so the download was made by hand and cannot be repeated by a tool;
`raw/` stays byte-identical to what collection handed over.
**Checked because it is the usual failure:** Chinese file names in a Windows-made zip are normally
GBK bytes with the UTF-8 flag clear, which Python decodes as cp437 mojibake — and the name is the
whole provenance story here, since it carries the title and the version date
(`中华人民共和国消防法_20210429.docx`). The unpacker recovers the name through cp437 and GBK and
checks the result for CJK. Measured: all 945 names were already honest UTF-8, so nothing needed
recovering. The guard stays, because a later export may not be.
**Also established:** `corpus/CN` is a real local copy, not a junction — unlike `corpus/LA/raw`,
which resolves into the collection workshop. Unpacking here touches nothing read-only.

## 2026-09-23 — a record no longer claims a model that never ran

**Found by the developer**, reading a real Lao provision: `"extraction_model": "qwen2.5:14b"`
sitting beside `scope: horizontal`, `data_type: personal`, `obligation_type: other` and
`extraction_confidence: null`. The null confidence is the signature of the **no-LLM** path — the
LLM-failure path writes 0.0 and a real call writes a number. Measured across the finished
corpora: **681,557 of 681,557 provisions** (SG 110,730, AU 302,541, MY 78,826, TL 189,460,
LA 80) carried that model name, and not one had been near a model. Every run used `--skip-tags`,
which is the intended design — tagging is a separate pass — but `extract_fields` stamped
`settings.llm_model` unconditionally and filled the three tag fields with hardcoded placeholders.

**Why it mattered more than a wrong value:** the wrong value was *shaped like a finding*. A null
reads as a gap; "horizontal, per qwen2.5:14b" reads as a judgement. Mapping had no way to tell
them apart, and neither did a judge.

**What changed.** An untagged record now says so: `scope`/`data_type`/`obligation_type` are null,
`extraction_model` is null, `model_version` names only what actually touched the record (the OCR
engine alone, where OCR is all that ran), and a new `tags_source` field carries `llm`,
`llm_failed` or `not_tagged` so the state never has to be inferred from a null confidence.
`tools/allow_untagged.py` widens `provision.schema.json` to permit it — the old schema made the
three fields enum-only and `extraction_model` a non-empty string, so **there was no way to encode
"not tagged"**, which is how the placeholders got there in the first place.
`extract_fields.stamp_tagging_model()` is now the single place a tagger is recorded, used by both
the inline lane and the Batches lane; it rebuilds `model_version` from the record's own
`ocr_engine` rather than splitting the old string on "+", because an untagged record's value has
no "+" to split and the engine was being silently dropped. A provision the Batches lane does not
tag keeps its untagged state instead of inheriting the model name from the record beside it.

**And the tagging model is now per language.** New `code/config/llm/tagmap.py`, mirroring
`config/ocr/langmap.py`: `get_llm(settings, language=...)` picks the model from the document's
declared language, and one client is built per model rather than per language.
**Lao maps to `gemma3:12b` because that is the only language with a measured winner** — chrF
0.658 against `qwen2.5:14b`'s 0.561 on 12 articles, and gemma3 fixed both of qwen's substantive
errors: qwen rendered "ປອດພາສີ" (duty-free) as "free", losing that the article was about customs,
and hardened "promotes" into "shall promote", which is exactly the policy-versus-obligation
distinction `obligation_type` encodes. **Portuguese and Chinese stay on the incumbent**, because
what was measured there is the two models' agreement with each other (0.846, 0.836) — which says
they agree, not which is right. Choosing gemma3 for them would be inventing a result. Both limits
are written into the module: it measures translation, not tagging, and qwen2.5 is Apache-2.0
where Gemma carries its own terms.
**Verified:** `la-la2537-001` re-extracted — 80 articles, 0 dropped, `tags_source: not_tagged`,
`extraction_model: null`, `model_version: "tesseract-5.4.0.20240606-lao"`. 90 tests pass, 2
skipped; new `tests/test_untagged_claims_nothing.py` covers the stamp, the failed-call case, the
legacy suffix, and that por/zho are NOT mapped to gemma3. All five corpora are being re-run.

## 2026-09-23 — W8 groundwork: three defects China exposed in code that already shipped

China has no manifest yet, but investigating it found three problems in the running stage. All
three were measured, two by building a throwaway CN manifest and pushing it through the real
`ingest.load_manifest`, `router.route` and `segment_civil`.

**1. The portal parser was chosen by substring, so the answer depended on typing order.**
`parse_html.parse` tested `if host in source_url` over an insertion-ordered dict and took the
first hit. `"gov.cn" in "https://www.cac.gov.cn/..."` is true, and China's three portals are
cac.gov.cn (112 documents), miit.gov.cn (16) and www.gov.cn (11) — so registering `gov.cn`
first would have sent **139 of 140 pages to the wrong parser**, about 128 of them silently,
because a parser that finds no container returns little rather than raising. Matching is now on
the **host**, with the **most specific registered host winning**. Suffix matching alone does not
fix this — `www.cac.gov.cn` really is a subdomain of `gov.cn` — so length breaks the tie, and it
does so whatever the order. `tests/test_portal_dispatch.py` registers the parent host first on
purpose and asserts all four hosts still route correctly. Australia, 793 HTML documents, re-ran
on the new dispatch with **0 parser failures** and 302,541 provisions, unchanged.

**2. A corpus with no sidecar lost its language.** `load_facts` returns `{}` when there is no
`law_table.csv` and no `links_used/` — exactly China — and the run loop read
`language = getattr(facts.get(doc_id), "language", None)`, so every Chinese document would have
arrived as `None`, selecting the **common-law segmenter and the English OCR pack**. `cmd_ocr`
has always fallen back to the economy's declared default; the run loop did not, and the two
disagreeing is the whole bug. The run loop now falls back the same way, the resolved language is
threaded into the record, and `language_source` records `economy_default` when it came from the
declaration rather than from the crawler — never "detected" (D3).

**3. `--fresh` deleted the OCR page cache.** `tools/run_economy.py` ran `shutil.rmtree(out)`,
and the cache lives at `out/<CC>/ocr/`. It threw away **19,054 cached Lao pages — 20.8 minutes
of 16-way parallel OCR** — and the run then re-read them one page at a time inside the
single-threaded loop, a roughly fourteen-hour job. Nothing failed and nothing warned; the only
symptom was a document count that crept instead of climbing, which is how it was caught.
`--fresh` now clears the outputs and keeps the cache, removing only `cer_report.json`, which is
a run artefact that happens to live in the same folder. Keeping it costs nothing: the cache is
keyed on the file's sha256, the engine, the language and the DPI, so a stale entry re-OCRs
itself. `tests/test_fresh_keeps_ocr_cache.py` drives the real code, not a copy.

**Also measured, for the record:** `python-docx` is **not installed** in the venv and is not in
`pyproject.toml`, so the planned docx lane must use stdlib `zipfile` + `lxml` — verified to open
all 943 OOXML packages with zero failures. And
`corpus/CN/manual/npc-database/index.csv` already exists: a complete 945-row index
(`title, version_date, kind, file, archive, bytes`), 945/945 ISO dates, zero mismatches against
disk, which supplies `law_name_guess`, `publication_date` and the archive join with no parsing.

## 2026-09-23 — all five collected economies re-extracted with honest provenance

| Economy | Provisions | Laws | Notes |
| :---- | ----: | ----: | :---- |
| Australia | 302,541 | — | unchanged count; 793 HTML documents re-parsed on the new host dispatch, 0 parser failures |
| Timor-Leste | 189,355 | 1,921 | 1,026 documents yield provisions; 889 zero, 4 wrong_instrument, 2 translation_not_source |
| Singapore | 110,730 | — | unchanged count |
| Malaysia | 78,826 | — | unchanged count, including the 146 Malay provisions |
| **Lao PDR** | **41,534** | 1,762 | first full run: 41,362 snippets from OCR, 172 native |
| **Total** | **722,986** | | |

Every record now carries `extraction_model: null` and `tags_source: not_tagged`, because no
model has run — which is true, and was not what the previous 681,557 records said.

**Lao, the corpus this round was built for.** 19,080 pages OCR'd in 20.1 minutes at 16 workers,
0 retried and 0 failed, then the whole extraction pass ran off the cache in under a minute with
no Tesseract process alive. 37,115 citations exact and **4,419 repaired from sequence** — 10.6%,
consistent with the 0.856 article-number sequence agreement measured beforehand — each carrying
`article_number_as_read` and `citation_repair_method` so the repair is auditable. Language is
`lao`/`portal_field` on all 41,534: read from the crawler, never detected.

**The grounding rule re-checked independently.** Rather than trusting the gate that wrote the
records, the frozen `source_text/<doc_id>.txt` was re-read from disk and the bytes at each
recorded offset compared to the stored `verbatim_snippet`: **4,000 records sampled per economy,
20,000 in total, 0 mismatches and 0 missing source files.** D1 holds across all five.

**Timor-Leste's count moved, and the reason is recorded rather than smoothed over:** 189,460 on
the first run against 189,355 now, 105 fewer. The first run was not `--fresh` and inherited an
output folder holding 888 `by_law` files from earlier pilots, and `emit.write_provisions` merges
by `doc_id`; the re-run was `--fresh`. The fresh number is the authoritative one. The old file
was overwritten, so this is the likely cause rather than a proven one — what can be said firmly
is that none of the three code changes between the runs (tagging provenance, host dispatch,
language fallback) can alter a provision count for a pure-PDF corpus with complete sidecar facts.

## 2026-09-23 — W8: China has a manifest, and the gaps are written down rather than filled

**`corpus/CN/manifest.csv`, 1,091 rows**, built by `tools/build_cn_manifest.py` from the five
`provenance.tsv` files plus the database's own 945-row `index.csv`. It **passes the real
`ingest.load_manifest`** and all 1,091 `local_path`s resolve on disk. The arithmetic reconciles:
1,092 files = 1,091 rows + 1 byte-identical duplicate, listed with its reason in
`corpus/CN/manifest_exclusions.json`. The other five manifests still pass unchanged.

**The developer's instruction was to document the gap and progress.** `corpus/CN/PROVENANCE_GAPS.md`
is that document, and every number in it was re-derived from the finished manifest rather than
carried over from the investigation. Three columns now carry a recorded gap:

| Column | Filled | Recorded gap |
| :---- | ----: | :---- |
| `access_date` | **6 of 1,091** | `access_date_basis` says which of five states; `access_date_observed` keeps collection's own string verbatim |
| `source_url` | 1,086 | 945 carry the database root with `source_url_basis = database_root`; 5 are null, `not_recorded` |
| `http_status`, `http_headers_path` | 0 | 974 had no HTTP request at all; 117 had one whose headers were never stored |

A UTC instant exists for six documents. CAC's 111 stamps are naive, MIIT's are dates without
times, the mirror's read `(resumed)`, and the 945 database documents have only the download
session's stamp from the archive filename. The offset is nowhere recorded, and this corpus proves
guessing unsafe: file mtimes are demonstrably local *write* times, since CAC's 111 collapse to
one bulk-copy stamp and the 945 unpacked files to the unpack stamp. **A `Z` on a naive stamp
would be a fabricated instant in the column a judge uses to check when the law was read.**

**Contract changes, all additive and all so a gap can be stated.** `source_url`, `access_date`,
`law_name_guess`, `http_status` and `http_headers_path` became nullable; `source_url_basis`,
`access_date_basis` and `access_date_observed` were added; `ingest._NULLABLE_IF_EMPTY` gained the
seven columns a hand-collected document cannot fill. The tightened `access_date` pattern was
checked against every existing record first — **722,986 of 722,986 conform**, so nothing already
written was invalidated.

**Four defects found in my own first build, by inspecting it rather than trusting it:**
* **Deduplication kept the wrong copy.** The byte-identical PDF pair was resolved by directory
  order, which discarded the copy that HAD a provenance row and kept the orphan. Dedup is now
  deferred until every row is built and keeps the better-documented copy, naming it in the
  exclusion reason.
* **Titles were being thrown away.** A file no provenance row names was getting an empty
  `law_name_guess`, when collection had saved it under the instrument's own title — four of the
  five are recovered from the filename, with `crawl_notes` recording that is where it came from.
* **`3554809.doc` would have been titled "3554809".** An attachment id is not a name for a law,
  so `law_name_guess` is null and the schema was widened to permit it.
* **Two provenance rows name the same file**, and `setdefault` silently took the first. The
  ambiguity is now written into `crawl_notes` instead of being hidden.

**And one claim from the adversarial review was checked and found wrong.** The judge critic
reported that MIIT row 32 would be silently dropped, having no `doc_status` row and no
`laws.jsonl` row, because its note contains "superseded by". `ingest.py:136` matches
**case-sensitively** and the note reads `"SUPERSEDED by"`, so no China row is at risk today. The
rule is still a coin-flip in both directions and is recorded as such — but the finding as stated
was not true, and was not passed on as though it were.

**Not yet built, and the reason China still cannot run:** there is no `docx` lane, no OLE2 `.doc`
reader, and no parser registered for `cac.gov.cn`, `miit.gov.cn` or `www.gov.cn`. The host
dispatch is now safe for when they are added.

## 2026-09-23 — "superseded by" is now case-insensitive, and reaches the file it describes

**Developer's instruction:** if a row says superseded by, do not record it.

The test was `"superseded by" in crawl_notes`, case-sensitive, written out in four places. China's
MIIT provenance row 32 reads **"SUPERSEDED by 令68 of 2024-01-18"** — so the held text was
replaced in 2024 — and it would have been extracted and scored as current law, while an identical
note written in lowercase two rows away would have been dropped. Which behaviour you got depended
on how a human capitalised a sentence. It is now one function, `ingest.is_superseded`, matching on
`.lower()`, used by all four sites, with `tests/test_superseded_rule.py` covering five casings
and the real China note.

**The warning also had to reach the right file.** Row 32 names `电信设备进网管理办法.pdf`, which is
not on disk; what is on disk is the `.html`. A filename-only join therefore kept a superseded text
with no warning on it. The manifest builder now carries a supersession warning **by title**, and
carries nothing else that way: the same title also matches row 7, whose `file_saved_as` is
literally the string `not taken`, so inheriting a URL or a date by title would attach a row to a
file it does not describe. A supersession warning only ever errs toward dropping.

**Result:** `corpus/CN/manifest.csv` holds 1,091 rows; `ingest.load_manifest` drops 1 as
superseded; **1,090 reach extraction**. 1,092 files on disk = 1,090 + 1 duplicate + 1 superseded.
No row in the other five economies is affected (0 before, 0 after). 115 tests pass, 2 skipped.

**New `OPEN_ISSUES.md`** lists everything still outstanding with options and costs. The two that
matter most: China has no reader for any of its 1,090 documents, and **Timor-Leste's `act_index`
is null on all 189,355 provisions** — measured today — although collection measured 911 of 1,921
Timorese documents holding more than one act. Every act in a multi-act gazette issue is currently
attributed to a single law name, silently.

## 2026-09-23 — China reads. Lane D, three portal parsers, and a script-calibration bug

**The developer asked why China could not be read, and the answer was that it could.** The files
were always readable; the pipeline had no lane wired to them. Reading the Cybersecurity Law out
of its `.docx` took twenty lines of stdlib: 162 paragraphs, 10,876 characters, 81 articles.

**New `parse_docx.py` — lane D**, Office Open XML, via stdlib `zipfile` + the `lxml` already in
use. `python-docx` is deliberately not used: it is **not installed** and not in
`pyproject.toml`, and a new dependency a week before freeze would have to survive the
clean-machine test for no gain. Tables are emitted in document order because Chinese regulations
carry real obligations in them, and U+3000 (the ideographic space that separates `第一条` from its
text) is preserved exactly, because every snippet is a character-exact substring of the frozen
text and normalising it would move every offset after it.

**Three Chinese portal parsers**, registered for `cac.gov.cn`, `miit.gov.cn` and `gov.cn` — which
only works safely because of the host dispatch fixed earlier today, since the first two are
subdomains of the third. They return text and **no spans on purpose**: the pages carry no section
markup, so the `zho` segmenter does the article work rather than a second, disagreeing
implementation. Encoding is resolved per page, since these hosts declare GB2312/GBK about as
often as UTF-8 and sometimes declare one and store the other.

**The bug that mattered: a script-calibrated threshold was discarding real law.** The
contents-block detector drops a heading whose body is under `MIN_BODY_CHARS = 120`. Chinese
articles have a **median body of 79 characters** and **65 of the Cybersecurity Law's 81 fall
under 120** — so the detector threw away 49 real articles as table-of-contents entries, including
`第八十一条 "This Law takes effect on 1 June 2017"`, the article carrying the commencement date.
The law's actual contents block lists *chapters*, not articles, so none of the 49 were contents
at all. Fixed with a per-script threshold (`zho`: 24) plus a positional guard: a heading is only
a contents candidate if it sits before the first substantial body.

**And the fix was then narrowed, because half of it was not measured.** Applied to Lao, the same
change recovered 1,087 provisions — and sampling them found cross-references among them.
`ມາດຕາ 51.` (9 characters) and `ມາດຕາ 64 ຂໍ 6 ຂອງກົດຫາຍສະບັບນີ` ("Article 64 point 6 of this
law") are mentions **inside** another article, which OCR line breaks push to the start of a line
where the article pattern matches. The 120-character default had been filtering them by accident.
The positional guard is now scoped to `zho`, where it was measured at 81 of 81; Lao and
Portuguese keep the behaviour that produced their verified output. **Lao returned to exactly
41,534 provisions**, its verified number. Whether Lao's threshold should move is now an open
question with a measurement attached, not an analogy with Chinese.

**Also fixed:** `parse_html._host_of(None)` raised a `TypeError` that surfaced as "a bytes-like
object is required, not 'str'" on the five China files whose address collection never recorded.
A null `source_url` is a real state, and it now refuses cleanly naming `source_url_basis`.

**China's first full run: 49,319 provisions over 994 documents.** Of 1,090 documents, 994
extracted, 88 parsed cleanly with no citable provision, and **8 failed — all clean, explained
refusals**: 5 legacy OLE2 `.doc` (one file with a `.doc` extension turned out to be OOXML and
read fine) and 3 HTML with no recorded address. Down from 144 before the parsers existed.
**Independent D1 re-check: 4,000 records sampled, 0 grounding mismatches.**

## 2026-09-23 — Timor-Leste was citing the wrong article on two-thirds of its corpus

**Found while scoping the multi-act work, and far worse than the missing field it was filed as.**
`OPEN_ISSUES.md` recorded B1 as "act_index null on all 189,355 provisions", which reads as an
attribution gap. Measured against the shipped output, the real defect was that **120,968 of
189,355 Timorese provisions — 63.9% — cited an article number their own text contradicts**: the
page says `Artigo 1` and the record said `Art. 11`; the page says `Artigo 20` and the record said
`Art. 8`. A real act cited to the wrong article is the failure the host scores zero.

**One branch in `_repair_sequence`.** Its docstring states the rule correctly — *"when the number
read does not continue the run **but the next one does**, the odd number is an OCR misread"* — and
the implementation never looked at the next one. Any drift beyond three overrode the text with
the positional number. For Lao that is right: an isolated misread, with the following article
continuing the run. For a Timorese gazette issue holding many acts, each new act **restarts at
Artigo 1 and a fresh ascending run begins**, and the code renumbered every act after the first.
Now implemented as written, with one-step lookahead: a drop followed by a continuing run is a
restart, the text is trusted, and the record says `citation_confidence: sequence_restart`. No act
boundary detection is needed for this, which is why it landed first.

| | contradicts its own text | before |
| :---- | ----: | ----: |
| Timor-Leste | **4,526 (2.6%)** | 120,968 (63.9%) |
| Lao PDR | **1,565 (3.8%)** | 4,807 (11.6%) |

Lao improved too, and its provision count did not move: 41,534 before and after.

**And the fix exposed a second bug that had been hidden by the first.** Timor-Leste came back
11,999 provisions lighter with **zero drops logged**, because the records were never built at all:
`candidate_spans` decided "this article has subsections" from a set of `hierarchy[-2]`, the parent
article's **citation string**. That is only safe while every article in a document has a distinct
number — which was true precisely because the numbers were being fabricated into one ascending
run. Once restarts were honoured, act 2's `Art. 1` matched act 1's `Art. 1` and was filtered out
as though it had subsections of its own. A filtered candidate is never a record, so it is never
reported as dropped. Now decided by **character range**, which belongs to one act. All six
economies are re-running, because `candidate_spans` is shared.

**Scoping verdict on the splitting proper** (`feasible: true, confidence: high`): `act_count` is
free and authoritative — `corpus/TL/law_table.csv` already carries **one row per act**, 4,788 rows
over 1,921 documents, already parsed into `sidecars.DocFacts.acts` and already passed to
`build_record`. Acts should be located, not detected: 84.1% of acts and 80.5% of multi-act
documents locate cleanly, and a **completeness gate** — emit `act_index` only when the located
count equals the sidecar's count — turns the 16% miss into withheld output rather than wrong
output, because a partial split silently folds act 3's articles into act 2. Realistic cost
**6–8 h**, or 10–12 h with one `laws.jsonl` row per act; `OPEN_ISSUES.md`'s "half a day" was
optimistic by 2–3×. One trap recorded: `cmd_validate` collapses `laws.jsonl` into a doc_id-keyed
dict and will fail on every multi-act document the moment per-act rows are emitted.

## 2026-09-23 — English titles, the contract bump, and a detector that should never have existed

**`law_name_en` is now filled on all 766,477 provisions**, where it had been null on every one.
`OUTPUT_FORMAT.md` §0 records why that mattered: stage 3 matches this field against the host's
baseline, where Lao and Chinese laws are named in English, so a record offering only its
original-language title cannot be matched and is tagged NEW by default.

| | provisions | law_name_en_source |
| :---- | ----: | :---- |
| Australia, Singapore, Malaysia | 485,409 | `source_is_english` - the law is published in English, nothing translated |
| Timor-Leste | 189,557 | `rendered` |
| China | 49,977 | `rendered` |
| Lao PDR | 41,534 | `rendered` |

`tools/render_law_titles.py` translates the act's NAME and nothing else: no snippet is touched,
no offset moves, the frozen text is not read. D5 holds. Every machine-made title is labelled
`rendered` so a reviewer can see which they are, and renderings are cached by (title, model) so a
re-run is free.

**A bug that nearly shipped, and it was the project's own standing mistake.** The first version
decided "is this title already English?" by looking at the characters. `_NON_LATIN` permits the
Latin-1 supplement so that curly quotes and em-dashes in English titles do not force a rendering -
and **Portuguese accents live in exactly that range**. All 983 distinct Timorese titles were
therefore declared English and left untranslated: `Aprova o Código Civil` would have gone into
the workbook as its own English name and matched nothing. Lao and Chinese escaped only because
their scripts fall outside Latin-1. The economy **declares** its language in
`LANGUAGE_BY_ECONOMY`; writing a detector instead is the same error as reading every Lao page as
English, and D3 exists to prevent it. The declaration is now read, and the character test survives
only as a secondary guard inside an English-declared economy.

**Contract bumped 0.2.0 -> 0.3.0.** Not bureaucracy: mapping's vendored `provision.schema.json`
has `additionalProperties: false`, `economy: enum ["SG","AU","MY"]` and a doc_id pattern of
`^(sg|au|my)-`. A real China record validated against it produces **9 errors**, and so would
every Singapore record, because all of them now carry fields the old schema forbids. Without the
bump stage 3 ingests nothing at all. The delta is additive or loosening throughout - 27 new
provision properties, 9 loosened, no removals, nothing newly required - so MINOR is correct.

**Tagging withdrawn from the plan.** `OUTPUT_FORMAT.md` §7 already records that `scope` and
`extraction_confidence` have zero readers and were deliberately dropped, and that
`obligation_type`/`data_type` are "kept but demoted ... they are not to be improved". Two to four
hours had been put on the developer's list against a decision this project had already made.

**The Round 1 regression downgraded to optional.** It was described as the only check that
catches a silent break, but the double-count bug fixed earlier today was in Round 1's own code,
so its output carries it. That baseline is not known-good, and a diff against it would report
today's deliberate fixes as failures. Worth reading as a diff; not a gate.

**Final state, all six economies re-run and verified:**

| Economy | Provisions | D1 mismatches | Schema errors | Citation ≠ text |
| :---- | ----: | ----: | ----: | ----: |
| Australia | 302,243 | 0 | 0 | 0.0% |
| Timor-Leste | 189,557 | 0 | 0 | 2.5% |
| Singapore | 110,661 | 0 | 0 | 0.0% |
| Malaysia | 72,505 | 0 | 0 | 0.0% |
| China | 49,977 | 0 | 0 | 0.0% |
| Lao PDR | 41,534 | 0 | 0 | 3.6% |
| **Total** | **766,477** | **0** | **0** | |

D1 and schema checked on 18,000 sampled records, re-read from the frozen text on disk rather than
trusted from the writer. China's earlier "100% citation mismatch" was a fault in the CHECK, which
compared the glyph 一 against the digit 1; parsing the numeral gives 0.03%, and 0.0% after the
ordinal-style records are counted properly.

## 2026-09-23 — B1: a provision now says which act it belongs to

**New `code/src/rdtii_p2/acts.py`.** 912 of 1,922 Timorese documents are one gazette issue
holding several separate acts - up to 26 - and `tl-ldcn-001` holds both Lei 1/2026 and
Decreto-Lei 13/2026, **each with its own Article 6**. Every provision in such a document was
attributed to a single law name, so mapping grouped them as one law and matched the wrong title
against the host's baseline.

**The acts are located, not detected.** Collection already handed over one `law_table.csv` row
per act - 4,788 rows over 1,922 documents, already parsed into `sidecars.DocFacts.acts` - so the
act list, its count, and each act's name, number and kind were known before the text was opened.
All the text has to answer is *where* each known act begins, from its `portal_id` (`DL-13-2026`
-> `DECRETO-LEI N.º 13/2026`, line-anchored). Guessing the acts from the text would have been
inventing what was already declared, which is the error this stage made four separate times today.

**The completeness gate is what makes it safe.** `act_index` is emitted only when every act the
sidecar names was found at a **distinct** offset. A missed act does not leave a gap in the output
- it leaves its articles inside the act before it, attributed to the wrong law - so a partial
split is worse than none. When the gate fails the document keeps `act_index: null` exactly as
before, and `act_count` still carries the sidecar's authoritative number, so a reader can tell
"one act" from "several acts we could not separate".

**Measured before the run:** 802 of 911 multi-act documents fully located, **88.0%**, against the
80.5% the scoping estimated; 3,227 of 3,667 acts located.

Three details that the text forced:
* **The SUMÁRIO is not the anchor.** An issue restates every act in a contents list before
  printing any of them, so the first match is the listing. The last match wins, and any line
  carrying a dot leader (`....`) is never an anchor.
* **Longest-first alternation.** `DECRETO-LEI` must not match as `DECRETO DO GOVERNO`; the kind
  words overlap and the wrong one attributes an act to a different instrument entirely.
* **U+00AD.** The soft hyphen is invisible in a PDF and splits `DECRETO­LEI` in two. Stripped
  before matching.

The act's own `law_number` now overrides the document-level guess on its provisions, and the
provision id becomes `<doc_id>#a<n>#<section>` - the shape `_provision_id` has always supported
and nothing ever passed. `tests/test_acts.py` pins the gate, the SUMÁRIO case, the overlapping
kind words, the soft hyphen, and that both acts keep their own Article 6. 125 tests pass.

**B1 result, after two corrections found by reading the output rather than trusting it.**

The first run assigned `act_index` to 128,144 provisions, but only **73.9%** of act slices began
at Artigo 1 and **9.2% began above Artigo 10** - a seam in the wrong place. Reading four of the
worst showed the cause was not the seam at all: a Timorese **resolution** numbers its items
"1. 2. 3." with no `Artigo`, so the segmenter attaches them to the last article heading it saw,
which can be in the act before. The provision's text is in act 2 and its heading is in act 1, and
neither is a safe answer. Those provisions now have `act_index` **withheld**, and the run says so.

| act slice begins at | before the guard | after |
| :---- | ----: | ----: |
| Artigo 1 | 73.9% | **84.2%** |
| Artigo 2-3 | 13.3% | 13.3% |
| Artigo 4-10 | 3.6% | 1.4% |
| **above Artigo 10 (wrong)** | **9.2%** | **1.1%** |

7,454 provisions were withheld to buy that: 120,690 carry `act_index` (63.7% of the corpus,
552 documents, 850 distinct law numbers), and 97.5% of the slices they sit in begin at Artigo 1-3.

Second correction: `law_name_en` fell to 60% on Timor-Leste after the split, because each act now
carries **its own** title and `titles_of()` read `laws.jsonl` and stopped as soon as it found
anything. `laws.jsonl` holds one title per DOCUMENT; the per-act titles exist only in
`provisions.jsonl`, so 827 of them were never offered to the renderer. It now reads both files.

**Final state, six economies:**

| Economy | Provisions | D1 | Schema | Citation ≠ text | law_name_en | act_index |
| :---- | ----: | ----: | ----: | ----: | ----: | ----: |
| Australia | 302,243 | 0 | 0 | 0.0% | 100% | n/a |
| Timor-Leste | 189,557 | 0 | 0 | 2.5% | 100% | 64% |
| Singapore | 110,661 | 0 | 0 | 0.0% | 100% | n/a |
| Malaysia | 72,505 | 0 | 0 | 0.0% | 100% | n/a |
| China | 49,977 | 0 | 0 | 0.0% | 100% | n/a |
| Lao PDR | 41,534 | 0 | 0 | 3.6% | 100% | n/a |
| **Total** | **766,477** | **0** | **0** | | | |

18,000 records re-read from the frozen text on disk; 0 provision_id collisions across all six;
125 tests pass, 2 skipped.

## 2026-09-24 — the contract reaches mapping, and laws.jsonl carries one row per act

**Schemas synced into the repository**, on branch `p2-extract-contract-0.3.0` off `finale` at
`92a5e9d` — branched, not committed, and `finale` untouched. All three schemas copied into
**both** `stages/p2-extract/00_contracts/schemas/` and `stages/p3-map/00_contracts/schemas/`,
which are now byte-identical to each other and to the working copy.

Verified rather than assumed: 2,400 real records sampled across the six economies were validated
against **each stage's own vendored copy** — 0 rejected by either. Before this, mapping's copy
rejected every record we emit, including Singapore's, because it carried
`economy: enum ["SG","AU","MY"]`, a doc_id pattern of `^(sg|au|my)-` and
`additionalProperties: false` against 27 new fields.

**`laws.jsonl` now carries one row per ACT.** Mapping reads that file as the list of laws
searched, so one row per document said a 26-act gazette issue was one law, whatever the
provisions underneath said.

| | before | after |
| :---- | ----: | ----: |
| Timor-Leste laws.jsonl rows | 1,921 | **2,879** |
| rows carrying act_index | 0 | 1,312 |
| distinct law numbers | ~1,000 | **1,315** |

An act's own name and number now beat the document-level guess on its rows, because a gazette
issue's `law_name_guess` is the ISSUE, not any of the acts printed in it. Documents the gates
withheld keep exactly one row, so nothing changed for the other five economies.

**The trap the scoping warned about, fixed before it fired.** `cmd_validate` built
`laws_by_doc` as a dict keyed on `doc_id` and compared **one** row's `provision_count` against
the document's record total. With per-act rows that keeps only the last act's count and fails on
every multi-act document. It now sums across a document's rows. Measured on the finished corpus:
**0 documents where the summed count disagrees with the records**, over 2,879 rows.

Provisions the straddle gate withheld still get a row of their own, noted as
"provisions whose act could not be determined", so the per-document total reconciles instead of
quietly losing them. `laws.schema.json` gained `act_index`, `act_count`, `acts_located`,
`law_name_original`, `law_name_en` and `law_name_en_source`; it has `additionalProperties: false`,
so this was required, not optional. 125 tests pass.

## 2026-09-24 — Hand-off #2 assembled, and the stage handed back

**The hand-off had never been assembled, and that was the last real gap.** Extraction writes one
folder per economy, `out/<CC>/`, because a run is per economy. The interface contract §3.1 is a
single directory, and `p3-map` opens `provisions.jsonl`, `laws.jsonl`, `doc_status.jsonl` and
`source_text/` at the root of `HANDOFF2_DIR`. Those are not the same shape, so mapping would have
read whatever was last written there - **Round 1's output from 2026-07-18**, 411,986 provisions
over three economies. The outputs existed and were verified; they were simply not where the next
stage looks.

New `tools/assemble_handoff2.py`. Written to the Desktop as `rdtii-finale-handoff2/` on the developer's
instruction: Round 1's `handoff2/` is the previous deliverable, there is no backup of it, and the
tool refuses a destination named exactly `handoff2` rather than trusting a flag. Confirmed after
writing: Round 1 still has its 411,986 lines, dated 2026-07-18.

The merge is a concatenation, not a reconciliation, and that is only defensible because the ids
do not collide - checked **before** writing anything: 8,180 distinct doc_ids and 766,477 distinct
provision_ids, 0 duplicated in either.

| | rows |
| :---- | ----: |
| provisions.jsonl | 766,477 |
| tag_inputs.jsonl | 766,477 |
| laws.jsonl | 9,127 |
| doc_status.jsonl | 8,180 |
| extract_log.jsonl | 7,415 |
| source_text/ | 14,716 files |
| by_law/ | 7,358 files |

**Verified on the merged files, not on the sources they came from**: every count matches what was
planned, 0 duplicate provision_ids survived the merge, and grounding was re-checked by re-reading
`source_text/<doc_id>.txt` from the hand-off directory - 5,000 sampled, 0 bad.

**Stage handed back** at commit `dbc28bf`, branch `p2-extract-contract-0.3.0` off `finale`
(`92a5e9d`), working tree clean, `finale` untouched. 45 files, and **126 tests pass inside the
repository**, which is the check that proves a hand-back rather than a copy. `tessdata_fast` is
vendored (D7); `tessdata_local`, the 58 MB "best" packs, is gitignored as a research option the
evidence measured within half a point of fast at twice the cost.

**A new batch is now four commands** (`REFRESH.md`). Two things had to be fixed first, and both
would have failed silently: the corpus folders were hardcoded with dates, so a new batch would
have been ignored while the import reported success over the stale corpus; and two tools carried
absolute Desktop paths, in a repository whose previous commit was "no absolute paths out to the
Desktop". `tools/refresh.py` compares by `content_sha256` rather than date - a re-crawl rewrites
`access_date` on every row - and **withdrawn documents are reported, never deleted**, because a
short batch and a real withdrawal look identical from here. Verified end to end: re-extracting a
single Singapore document left 110,661 provisions, 717 documents, 738 law rows and 738
doc_status rows exactly as they were.

## 2026-09-24 — frozen

**Final state. Numbers above this line are what was true when each entry was written; these are
what is on disk now.**

| Economy | Provisions | Fields | Contract |
| :---- | ----: | ----: | :---- |
| Australia | 302,243 | 62 | 0.3.0 |
| Timor-Leste | 189,557 | 62 | 0.3.0 |
| Singapore | 110,661 | 62 | 0.3.0 |
| Malaysia | 72,505 | 62 | 0.3.0 |
| China | 50,026 | 62 | 0.3.0 |
| Lao PDR | 41,534 | 62 | 0.3.0 |
| **Total** | **766,526** | | |

Earlier entries cite 766,477 and China at 49,977. Both were correct when written; China gained
49 provisions when the three MIIT HTML files whose address collection never recorded were given
the ministry's own site under `source_url_basis: source_site`, which let lane A dispatch them.

**Every document in every manifest is accounted for**, and every absence has a recorded reason:

| Economy | manifest | ok | zero_provisions | excluded | skipped | parse_failed |
| :---- | ----: | ----: | ----: | ----: | ----: | ----: |
| Singapore | 738 | 717 | — | — | 21 linkage | — |
| Australia | 1,278 | 1,256 | 18 | — | 3 linkage | 1 |
| Malaysia | 1,391 | 900 | 13 | 92 | 384 linkage | 2 |
| Timor-Leste | 1,921 | 1,026 | 889 | 6 | — | — |
| Lao PDR | 1,762 | 1,109 | 348 | 291 repealed | 14 linkage | — |
| China | 1,091 | 1,061 | 24 | — | 1 superseded | 5 |

**One more defect found while preparing the freeze**, same class as the OCR cache one:
`--fresh` deleted `out/<CC>/extracted_hashes.json`, the baseline `tools/refresh.py` compares an
incoming batch against. Five of the six had been destroyed by the contract-version re-run, so
the first action on a new batch would have reported every document as changed and silently
redone twenty minutes of Lao OCR and an hour of extraction. `--fresh` now keeps it, a test pins
that, and all six baselines are recorded.

**Frozen here on the developer's instruction.** What is left is known, documented and optional:
Timor-Leste `act_index` null on about a third of its provisions (withheld by design, `act_count`
authoritative), citation-vs-text mismatch of 2.5% in Timor-Leste and 3.6% in Lao PDR (flagged
per record), no provision tagged (deliberate — the fields have no consumer in mapping), 5 legacy
OLE2 `.doc` unread, and the Round 1 English regression never run. That last one is the only
check that could find an error every internal check would reproduce faithfully; it was judged
not worth the remaining time, and that judgement is recorded here rather than left implicit.
