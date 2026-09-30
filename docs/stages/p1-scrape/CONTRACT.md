# Output contract: what every economy's crawl delivers

The shape of the crawler's hand-off to extraction. `POLICY.md` covers what gets fetched.

**Status: draft proposal for contract version 0.3.0, written 2026-09-13.** Today's authority is
`stages\p1-scrape\contracts\schemas\manifest.schema.json` (0.2.0), restated in `INTERFACE_CONTRACT.md`
§2.2 in the repo. The p2-extract and p3-map copies of §2.2 list all 28 fields; the p1-scrape copy
still lists the 24 of 0.1.0. Nothing here binds until extraction agrees and it lands in one commit
across stages (section 6).

## 1. The rule

**Every economy's output has one shape: the same files, the same columns, and one value space per
column.**

1. **Adapters return raw portal values.** One shared normaliser turns them into the manifest row. No
   adapter writes a manifest field directly.
2. **Unknown is null.** Never an empty string in JSON, never a default, never a guess.
3. **Portal facts are observed, not assumed.** A field that reports what a portal says holds only what
   was read, with where it was read from.
4. **Raw text survives in raw columns only.** Normalised columns have enforced formats.
5. **Seed rows and discovered rows look the same.** In Round 1 they did not, even within one economy.

Why this is needed: 0.2.0 accepts any string in 11 of its 28 columns, so "0 errors" hid the following,
counted on the frozen 2,706-row manifest.

| Column | Singapore | Malaysia | Australia |
| :---- | :---- | :---- | :---- |
| `publication_date`, `assent_date` | empty | `DD/MM/YYYY` | assent ISO only |
| `commencement_date` | empty | free text, some Malay, cut at 200 characters | empty |
| `in_force_status` | `Current` stamped on every row | never set | `InForce` from the register |
| `law_number_guess` | empty on 523 of 536 | `Act 709` | register IDs (`C2004A00148`, `F2025L00278`) on 1,286 rows |
| `law_name_guess` | title case | ALL CAPS on 754, bare `Act N` on 95 | title case |
| `source_url` | a PDF download link | unencoded spaces on 837 | dated PDF links, or undated `/latest/text` |
| Last amended | no column | no column | no column; the date is in the URL on 866 rows |

The output template's column 4, Last Amended, is required, so the stages downstream guessed it. Singapore
got the 2020 Revised Edition cut-off, "1 December 2021", on 484 documents, and 338 of those have a later
consolidation date printed in the same PDF.

## 2. What a run delivers

| File | Rule |
| :---- | :---- |
| `raw/<cc>/<dir>/<timestamp>__<kind>.<ext>` | The retrieved bytes. Paths in the manifest are relative. Proposed: `<dir>` becomes a stable identity (the `doc_id` stem) instead of a slug of the title |
| `<file>.headers.json` | One sidecar per stored file, with the same nine keys everywhere: `final_url`, `status`, `retrieval_method`, `content_type`, `redirect_chain`, `request_headers`, `response_headers`, `fetched_at`, `error` |
| `manifest.jsonl` | One row per document. **The typed authority** |
| `manifest.csv` | The same rows, flattened. An empty cell means null, booleans are lowercase `true` and `false`, integers are unquoted |
| `crawl_log.jsonl` | One line per request. It already records `content_type`. Proposed additions: `doc_id`, `economy`, `pass` (Engine A or Engine B), `byte_size` |
| `cost_report.json` | Measured cost of the run |
| `run_record.json` | Planned in step 1B-6: new, updated, unchanged and gone counts, plus the `run_id` |
| `inventory_<cc>_<run_id>.csv` | What the portal listed. Proposed: written per run and never overwritten, with the same normalised columns as the manifest. Round 1's seed runs overwrote the full inventories |

## 3. Columns

### 3.1 Rules for every column

- **Dates** are ISO 8601. Reduced precision is allowed (`2025`, `2025-06`, `2025-06-04`) and a day is
  never invented. Timestamps are UTC with a trailing `Z`.
- **Lists** are comma-separated with no spaces, in a declared order. Indicator IDs follow
  `indicator_order.yaml`, never a numeric sort.
- **Indicator IDs** are decimal text, validated against the in-scope list.
- **Single-line text** has no newlines, collapsed whitespace and Unicode NFC.
- **Enumerations added in 0.3.0** are lowercase snake_case strings, not booleans, so no stage adds a
  boolean coercion. Older value spaces keep their form: `economy` stays upper case, `pillar_hint`
  keeps `P6`, `P7` and `both`, and `pdf_is_scanned` stays boolean.
- **Every new column joins P2's empty-to-null list** (`ingest.py` `_NULLABLE_IF_EMPTY`). Otherwise an
  empty CSV cell reaches the schema as `""` and fails its enumeration or pattern.

### 3.2 The 28 columns of 0.2.0

Unchanged unless the last column says otherwise. The 15 required columns stay required.

| Column | Required | Rule | Change in 0.3.0 |
| :---- | :---- | :---- | :---- |
| `contract_version` | yes | SemVer | One version per manifest file |
| `instrument_version` | no | informational | Filled from the instrument hand-off tag instead of always null |
| `doc_id` | yes | `<cc>-<slug>-<seq>` | Pattern widened to `^[a-z]{2}-[a-z0-9]+-\d{3}$`. `seq` counts versions of the same law only. It never counts two different laws that share a title, which happened on 4 Malaysian pairs. The rule applies to new rows: the 4 frozen `-002` doc_ids are kept, because Hand-off #2 is keyed on `doc_id`, and `portal_id` tells each pair apart |
| `economy` | yes | two-letter code | Enum widened to `^[A-Z]{2}$`, equal to the country folder's code |
| `source_url` | yes | `^https?://` | The URL the stored bytes came from after redirects, percent-encoded, equal to the sidecar `final_url`, as 0.2.0's prose already says. Round 1 wrote the adapter's citation URL instead, which differs on 871 frozen rows (Malaysia 837 with unencoded spaces; Australia 33 epub rows citing `/latest/text`, and 1 redirect). The migration rewrites them from the sidecar. P2 builds its provision and `laws.jsonl` URLs from this column, and P3 exports those as Source URL, so P2 reads `citation_url` first, in the same commit |
| `access_date` | yes | ISO UTC | none |
| `source_type` | yes | `html`, `pdf_native`, `pdf_scanned` | none |
| `pdf_is_scanned` | yes | null only for `html` | none |
| `local_path`, `http_headers_path` | yes | relative | none |
| `law_name_guess` | yes | non-empty | Kept as the raw title. `law_name` is added |
| `law_number_guess` | no | free text | Kept as raw. `law_number` and `portal_id` are added |
| `pillar_hint` | no | enum `P6`, `P7`, `both` | Widened to the legacy enum or pillar numbers as text (`6`, `6,7`, `12`). **Open**, section 7 |
| `indicator_hints` | no | free text | Pattern for decimal IDs. Legacy tokens accepted only on 0.2.x rows |
| `retrieval_method` | yes | `playwright`, `requests`, `api` | none |
| `http_status`, `byte_size` | yes | integer | none |
| `content_type`, `content_sha256` | yes | string, 64 hex | none |
| `page_count` | no | integer or null | none |
| `anchor_hint`, `anchor_kind` | no | deep link | Empty on all 2,706 rows. **Open**: fill or deprecate |
| `seed_query` | no | free text | Holds the matched title terms, not the query its name implies. Kept, and documented as matched terms. `discovery_path` is added alongside it for how the document was found |
| `crawl_notes` | no | free text | For people only. No stage may parse it. Machine flags move to `crawl_flags` |
| `publication_date`, `assent_date`, `commencement_date` | no | raw portal text | Kept raw, display only. ISO columns are added |
| `in_force_status` | no | raw portal text | Holds only a value read from the portal, else null. The Singapore literal goes. `legal_status` is added |

### 3.3 Columns added in 0.3.0

All are appended, all optional. **Must** means needed for the freeze and the output template.
**Should** means needed for uniform output. **Later** means useful but not blocking.

| Column | Format | What it holds | Who reads it | Priority |
| :---- | :---- | :---- | :---- | :---- |
| `language` | ISO 639-3, comma list (`eng`, `msa,eng`) | Language of this document's text, per document, never per economy | P2 picks the OCR language. The export renders column 14 | Must |
| `language_source` | `portal_field`, `response_header`, `registry_default`, `text_detect` | How the language was known. Replaces the `source_language_note` column of decision 2 and `PLAN.md` 1A-5 and 1A-6 | Review | Must |
| `legal_status` | `in_force`, `not_yet_in_force`, `partially_in_force`, `repealed`, `unknown` | Status as the portal states it | P3 drops repealed and not-yet-in-force rows | Must |
| `status_source` | `portal_field`, `portal_listing`, `portal_remark`, `document_text`, `filename_marker` | Where the status came from. `filename_marker` may only yield `unknown` plus a flag. `document_text` counts only when the official document itself states the status, such as a repeal notice | P3, review | Must |
| `document_kind` | `principal_act`, `amending_act`, `repealing_act`, `commencement_instrument`, `subsidiary_legislation`, `guidance`, `code_or_standard`, `official_announcement`, `report`, `ownership_record`, `intergovernmental_notification`, `draft_or_bill`, `other` | What the document is, from the portal's own data, never from a title alone. For example Laws of Malaysia `type=amendment`, or Australia's register `isPrincipal` read together with the amending titles named in its version lists: the flag alone is true on 110 amendment-titled Acts in the corpus | P3 re-cites the principal for an amending act and drops a draft or bill. P2 skips indicator hints on `amending_act`, `repealing_act` and `commencement_instrument` rows | Must |
| `principal_law_number` | same form as `law_number` | For an amending, commencement or subsidiary instrument: the law it belongs to | P3 | Must |
| `principal_doc_id` | `doc_id` pattern, or null | The same law, when it is in the corpus | P3 | Must |
| `version_as_at` | ISO date | The date of the version the stored bytes are: consolidation, compilation or as-at date | P2, the delta check, review | Must |
| `version_source` | `portal_field`, `url`, `document_text` | Where `version_as_at` came from. Never a response header or a filename: `Last-Modified` is a generation or upload stamp, and filenames mislead (`POLICY.md` 3.1) | Review | Must |
| `last_amended_year` | `^\d{4}$` or null | Year the most recent amendment included in the stored version took effect. Null for an unamended text. **Definition open**, section 7 | Output template column 4 | Must |
| `last_amending_instrument` | official number | The instrument behind `last_amended_year` | P3 Notes | Should |
| `law_number` | the official number as the portal prints it for the law itself (`Act 26 of 2012`, `Act 709`, `No. 119, 1988`), or null | Never a register ID, and never the number of a different instrument, such as the act that amended this one | Output template column 3 | Must |
| `portal_id` | string | The portal's identifier: Australia's register title ID, the SSO act code, the Laws of Malaysia act parameter | The delta check, citation links | Must |
| `version_id` | string, or null | The portal's identifier for the stored version, such as Australia's compilation register ID (`C2026C00227`). Null where the portal has none | The delta check (`POLICY.md` section 6), review | Must |
| `superseded_by` | `doc_id` pattern | Written onto the old row when a newer version is stored | P2 skips superseded rows by this column, not by a substring | Must |
| `run_id` | string | The run that minted the row | The Run Record | Must |
| `published_on`, `enacted_on`, `commenced_on` | ISO date, reduced precision | Normalised dates. The raw columns stay | P2, P3 currency checks | Should |
| `commencement_note` | free text, not truncated | The full commencement remark, including per-section and per-territory dates | Review | Should |
| `text_version` | `consolidated`, `reprint`, `as_enacted`, `point_in_time`, `unknown` | Which version of the text was stored | P2, review | Should |
| `law_name` | official short title with year, mixed case, no editorial additions | A bare `Act N` is invalid | Output template column 2 | Should |
| `citation_url` | `^https?://\S+$` | The human page for the law on the official portal, pinned to the version where the portal allows it | Output template column 11 | Should |
| `discovery_path` | `seed`, `browse_listing`, `api_enumeration`, `number_enumeration`, `amendment_list`, `subsidiary_list`, `delta`, `manual_request` | How the document was found | Review, recall audits | Should |
| `crawl_flags` | comma list from a fixed set: `secondary_copy`, `finding_aid_resolved`, `filename_says_draft`, `filename_says_repealed`, `number_mismatch`, `stale_vs_portal`, `no_parser_form`, `migrated_from_0_2_0` | Machine-readable warnings | Review, P3 | Should |
| `transform` | `none`, `epub_spine_concat` | How stored bytes differ from the fetched response, as with Australia's multi-volume acts | P2 | Later |

## 4. The conformance check

**One check runs over every economy's manifest before hand-off.** It lives in the repo's
`scrape.py --validate`. Country test folders never copy it.

1. **Schema:** types, patterns and enumerations from section 3.
2. **Cross-field rules:**
   - An `html` row has null `pdf_is_scanned`.
   - An amending, commencement or subsidiary row has `principal_law_number`.
   - `legal_status` other than `unknown` needs `status_source` of `portal_field`, `portal_listing`,
     `portal_remark` or `document_text` (`POLICY.md` 3.5).
   - `version_as_at` is on or before `access_date`, and `last_amended_year` is not later than the
     access year.
   - `superseded_by` names a `doc_id` in the same manifest.
   - Every indicator token is in scope and not non-regulatory.
   - An amending, repealing or commencement row carries no indicator hints.
   - `source_url` is not on a finding-aid host.
   - `law_name` is not a bare `Act N`.
3. **Coverage report:** the share of non-null values per column, per economy, printed on every run.
   A column filled for one economy and empty for another is visible rather than hidden behind
   "0 errors".
4. **Older manifests still validate.** A manifest whose header is the first N columns of the current
   field list passes, because columns are only ever appended. Today the header check requires an
   exact match (`manifest.py:99`), so the frozen 28-column manifest would fail as soon as a column is
   added.

## 5. Mixed versions after a re-crawl

**A manifest file is written at one `contract_version`.** When older rows are loaded, an offline
migration fills every column it can derive without a request, then re-stamps the version. Columns it
cannot derive stay null, and the row gets `crawl_flags=migrated_from_0_2_0`.

What the migration can derive, measured on the frozen corpus:
- **Malaysia:** `publication_date` and `assent_date` (`DD/MM/YYYY`, on 795 and 744 rows) convert to
  ISO without loss. `commencement_date` does not: of 779 values, 79 hold no date, 123 hold two or more
  and 10 are cut at 200 characters. `commenced_on` is filled only where a value holds one date, and the
  10 cut values need the portal again for `commencement_note`. `version_as_at` comes from the printed
  as-at date on at least 644 of 867 PDFs.
- **Australia:** `version_as_at` comes from the dated fetch URL, and `version_id` from the sidecar's
  content-disposition filename, on 899 rows. `law_number` comes from the cover on 1,256 of 1,268. On
  at least 35 of those the first `No. N, YYYY` on the cover is an amending Act's number, so each value is
  checked against the title before it is written.
- **Singapore:** `version_as_at` comes from the PDF footer or Revised Edition page on 523 of 523 acts.
  `law_number` comes from the legislative history or page 1 on 522. `last_amended_year` comes from the
  history, parsed in full rather than truncated, except for the 36 acts enacted after the revision,
  which have no history: 25 carry inline `[Act N of YYYY wef …]` or `[S N/YYYY wef …]` notes to parse
  and 11 carry none.
- **Legacy indicator IDs** convert through the instrument's `indicator_ids.normalize()` (`P6-I1` to
  `6.1`). `legacy_of()` maps the other way.

## 6. Changing the contract

**§8 of `INTERFACE_CONTRACT.md`.**
- An added optional field is PATCH.
- A new enum value, or a new required field with a default, is MINOR.
- A renamed or removed field, a changed type, reordered CSV columns, or changed indicator scoring
  semantics is MAJOR. §8 also freezes the 13-column CSV order and the 9 indicator definitions.

0.3.0 is MINOR only while every existing column is kept. It adds values to `economy` and
`pillar_hint`, which §8 makes MINOR, and widens the `doc_id` pattern, which §8 does not cover.
Removing `anchor_hint` and `anchor_kind` instead of filling them would make it MAJOR. The freeze on
the 9 indicator definitions is a question for the instrument hand-off, because the finale instrument
replaces them (request R3, `notes/INSTRUMENT_IMPACT_2026-09-13.md` B7). The appended columns alone
would be PATCH. This corrects decision 2, which called appended optional columns MINOR.

**In practice any column change breaks validation somewhere.** Every schema copy sets
`additionalProperties: false`, the header check is exact, and extraction coerces types from its own
tables. So every change lands in one commit that touches:
- **P1:** the schema, `models.py` `MANIFEST_FIELDS`, and the header check in `manifest.py`.
- **P2:** its three schema copies (`manifest`, `laws`, `provision`), whose `doc_id`, `provision_id`
  and economy pins, `pillars_in_scope` enum `[6, 7]` and indicator pattern `^P[67]-I[1-5]$` must
  widen; the coercion tables in `ingest.py`; the `pillar_hint` map at `cli.py:408`; the
  "superseded by" substring checks at `ingest.py:135-139` and `cli.py:625-640`, which move to
  `superseded_by`; and the URLs built from `source_url` at `cli.py:179` and `:420`, which read
  `citation_url` first.
- **P3:** its three schema copies, which carry the same pins.
- **All:** every copy of `INTERFACE_CONTRACT.md`.

**Legacy values stay valid.** Removing the `pillar_hint` legacy values would make 0.3.0 MAJOR, and would
fail the 63 frozen rows that carry them.

## 7. Open questions, to settle with extraction and mapping

| Question | Options | Evidence |
| :---- | :---- | :---- |
| **What "Last Amended" means** | This draft proposes the year the latest amendment took effect in the stored version. The candidates disagree: on 209 of 866 Australian compilations the amending Act's year and the compilation start year differ, and P2 uses the Act year. Singapore's 2020 Revised Edition date is a revision, not an amendment. The host baseline's wording is mixed: month-level ("last amended in October 2024"), year-only ("in 2024") and day-level ("on 1 February 2021") wording all occur | `countries/au-australia/NOTES.md`, `countries/sg-singapore/NOTES.md` |
| The language code set | ISO 639-3, matching extraction's plan and its OCR packs, or ISO 639-1, as step 1A-5's done-when says | If the two plans ship as written, P1 writes `th` and P2 expects `tha` |
| `pillar_hint` shape | Widen to pillar numbers as text, or keep it legacy-only and derive pillars from `indicator_hints` | `notes/INSTRUMENT_IMPACT_2026-09-13.md` B1 |
| `law_number`: add a column or re-mean `law_number_guess` | This draft adds `law_number` and keeps the guess raw. Re-meaning it changes 1,286 Australian values | section 3.2 |
| `anchor_hint` and `anchor_kind` | Fill them from a per-portal template, or deprecate them | Empty on all 2,706 rows |
| The `document_kind` vocabulary | As in section 3.3, or merged with extraction's own terms | P2 and P3 both need it to avoid zero-score rows |
| More `crawl_flags` values | Add the warnings the Malaysia scraper keeps in `review_flags` (`amendment_check_incomplete`, `principal_unlinked`, `newer_version_in_other_language`, `document_shared_with_other_act` and others), or keep them outside the manifest | `countries/my-malaysia/NOTES.md` section 4 |
| ~~A status for "superseded"~~ | Settled by decision 10 (2026-09-14): counts as `repealed` | Laws of Malaysia marks 12 acts this way |
