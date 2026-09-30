# Answers to extraction's five requests, 23 September 2026

From collection (workshop `rdtii-finale-1-scraping`) in answer to
`rdtii-finale-2-extraction\notes\2026-09-23_requests_to_collection.md`. Every figure extraction
quoted was re-measured here against the corpora and the link lists; every one reproduces exactly.
The findings below are the ones the re-measurement added.

Nothing in this note changes a file. R5 and R2 both need the developer's decision, for the reasons
in the last section.

**Read R5 and R2 together.** They touch the same documents, and the order in which they are applied
changes the result.

---

## R5. Dropping the repealed documents — accepted in principle, with three corrections

Extraction's measurements are right:

| | Rows `repealed` | With a stored file | Measured here |
| :---- | ----: | ----: | :---- |
| Malaysia | 133 | 90 | identical |
| Lao PDR | 293 | 291 | identical |
| Singapore | 297 | 0 | identical |

Malaysia's `unknown` count (1,285 of 1,441) is identical too. The Singapore mechanism does work end
to end: its 297 repealed acts carry a `law_table.csv` row with `in_force: no (repealed)`, no `doc_id`
and no `file`, which is exactly the coverage answer R5 wants.

### Correction 1 — the two Malaysian sets are one set, not two

R5 reads as 90 repealed files *plus* 76 `repeal_notice` files. They overlap almost entirely:
**75 of the 76 `repeal_notice` files are already inside the 90.** The union is **91**, not 166. The
one addition is `my-coca1968-001` (Act 437, Co-operative College (Incorporation) Act 1968) — the act
NOTES.md 1.2 already records as carrying no marker, where only the file says "Superseded by Act 865".

### Correction 2 — the carve-out is *inside* the drop set

This is the one that matters. R5 asks that the 5 Malaysian `other_act_text` files be kept, because
they are evidence that AGC serves the wrong document at a stable address.

**Four of those five are `legal_status: repealed`.** A rule that drops every repealed file deletes
exactly the evidence R5 asks to preserve:

| doc_id | Act | In the drop set? |
| :---- | :---- | :---- |
| `my-crefaaa1985-001` | Convention on the Recognition and Enforcement of Foreign Arbitral Awards | yes |
| `my-jca1947-001` | Juvenile Courts Act 1947 | yes |
| `my-lolpa1997-001` | Labuan Offshore Limited Partnerships Act 1997 | yes |
| `my-stta1984-001` | Share (Land Based Company) Transfer Tax Act 1984 | yes |
| `my-wpa2009-001` | Witness Protection Act 2009 | no (`unknown`) |

With the carve-out applied, **Malaysia drops 87 files** — not 90, not 91 and not 166.

### Correction 3 — "not one is topic-relevant" does not hold for Lao PDR

The claim is right for Malaysia. It is wrong for Lao PDR, and the check is Lao PDR's own title rule
(`countries/la-lao-pdr/sources.yaml`, `la-gazette-title-relevance-v1`), which matches on Lao script,
not on rendered English:

- **56 of the 291** Lao repealed-with-file documents match the title rule.
- **16 of them match at `core` tier**, among them:
  - `LA-447` ກົດໝາຍວ່າດ້ວຍ ທຸລະກຳທາງເອເລັກໂຕຣນິກ — the Law on Electronic Transactions (G4)
  - `LA-459` Telecommunications Law, revised (G3)
  - `LA-530` Media Law (G3)
  - eight subsidiary instruments on internet services, state e-mail, data centres and mobile and
    internet service quality (`LA-904`, `LA-1015`, `LA-1024`, `LA-1092`, `LA-1118`, `LA-1247`,
    `LA-1270`, `LA-1396`)

The topic-relevance argument should be dropped, because it is not true. **The argument that survives
the check is the better one anyway:** 14 of those 16 have an in-force document in the same corpus
sharing the title stem, so the current law is already held. Two do not — `LA-752`
(anti-money-laundering, superseded under a different title by `LA-2304`, which is held) and `LA-1316`
(an enterprise-registration instruction). Those two should be named in the corpus note rather than
dropped silently.

### Where the rule should be applied: at the merge, not at the crawl

R5 says this is "a crawl/merge rule applied by code", which is right, but for Malaysia and Lao PDR the
two are not interchangeable.

**A crawl-time drop cannot honour correction 2.** Whether a file holds another act's text is known
only from `tools/audit_run.py`, which reads the first pages of a file that has already been fetched.
Drop repealed acts at the crawl and the next rebuild never fetches those four files, so the audit
never flags them and the evidence is gone. Singapore could drop at the crawl because its WAF made the
298 acts about five hours of crawling (decision 19) and there was no audit evidence to preserve.
Malaysia and Lao PDR have neither constraint: both portals already served us these files at ordinary
politeness.

At the merge the rule is code-applied, reproducible from the runs, and keeps the audit evidence. Two
parts, and only one of them is new work:

1. **The 76 Malaysian `repeal_notice` files need no code at all.** `tools/merge_corpus.py` already
   has `--exclude-flags`; an excluded row still claims its law, so an older copy cannot come back in
   its place, and every excluded row is listed in `CORPUS_NOTE.md`. One caution: the docstring's
   example is literally `--exclude-flags repeal_notice,other_act_text`. Do **not** copy it — the
   second flag names the files R5 asks to keep.
2. **Dropping on `legal_status` is new.** `--exclude-flags` filters on audit flags, not on status. A
   `--exclude-status repealed` option is a small addition to the same function, and it is what R5
   actually asks for.

### The hazard that does not wait for R5

Independent of whether a single file is dropped:

- Malaysia's 90 repealed-with-file rows are **all marked `use: evidence`**.
- Lao PDR's 291 are all `linkage` or `linkage, text needed`, so decision 20 already keeps them out of
  reading and mapping.

`_mark_use` in `countries/my-malaysia/scraper/checker.py:169-178` decides `use` from `document_kind`
alone and never reads `legal_status`. So Malaysia's law table is currently telling extraction to read
90 repealed acts as evidence. That is the live risk R5 is really about, and it is fixed in the `use`
column whether or not any file is ever dropped. It is worth doing first.

---

## R2. The language-aware `identity()` — confirmed exactly, and it collides with R5

Every claim verifies:

- `outputs/LA/LA_corpus_2026-09-21/superseded.jsonl` holds **53 rows, and all 53 are the English
  editions**, every one matched on `("law", portal_id, document_kind)` with language ignored
  (`tools/merge_corpus.py:96-101`). None of the 55 English editions is in the corpus; 53 of the 55
  are on disk in `LA_ws_2026-09-21`.
- **50 of the 53 have a Lao original that is a scan** (`pdf_is_scanned`), so they are the only
  text-layer copy of those laws. Confirmed.

**The collision.** Of the 53 English editions, **16 belong to laws whose status is `repealed`**, and
**15 of those 16 are among the 50 "only text-layer copy" documents**. Applying R5 to Lao PDR as
written therefore deletes 16 of the 53 documents R2 exists to recover, including the English text of
the Electronic Transactions Law (`LA-447`), the revised Telecommunications Law (`LA-459`), `LA-428`
and `LA-752`.

R2 then yields **37** English editions, not 53. That may well be the right answer — a repealed law's
English translation is still a repealed law — but it is a decision, not a detail, and it should be
made knowingly rather than discovered after the re-merge. The two requests must be applied in one
pass, not one after the other.

---

## R1. Malaysia's in-force status — the answer is no, but disclose the sharper version

**No source on the portal states in-force status as a field.** Three checks, all offline, no requests:

1. **The listing carries no status field.** `principal.php?type=updated` returns records whose only
   status-like column is `lgt_log_type`, which is `UPDATED` on every row. Status exists only as a
   marker written into the title text — "(Repealed by Act N)", "(Superseded by …)",
   "(BELUM BERKUAT KUASA)" — and 1,151 of 1,291 census rows carry no marker.
2. **The timelines add nothing.** We already read every act's detail page under `timeline: all`, and
   80 documents carry `timeline_log_type: REPEALED`. **All 80 are acts the listing had already
   marked.** The timeline confirms the marker and never extends it. That cost is already paid, so
   there is no second pass worth running.
3. **The marker is close to complete.** The only independent detector available is the document
   itself: 76 files are repeal notices rather than act text. The listing had already said `repealed`
   on **75 of the 76 — 98.7%**. The single miss is Act 437, already recorded in NOTES.md 1.2.

So the answer to "can the portal supply it, even partially" is no. But two things should change in
how it is disclosed.

**First, the population is smaller than 1,285.** Of those rows, 455 are amending acts and 47 are
commencement instruments — 502 documents that decision 20 already classifies as `linkage` and never
reads for indicators. Whether they are in force is not a question extraction needs answered. The
population where the question actually bites is **783 rows marked `use: evidence`**, of which **726
are principal acts holding a file**.

**Second, `unknown` is not "nobody knows".** AGC marks the exceptions and does not mark the rule, and
on the one check we can run, that marking is 98.7% complete. The honest submission sentence is nearer
to: *AGC publishes a status marker only for acts that are repealed, superseded or not yet in force;
1,285 rows carry no marker, and where the marker could be tested independently it had caught 75 of 76
repeals.* That is a materially more useful disclosure than "status could not be established".

**One correction to the request as written:** R1's heading says `unknown` on 1,135 of 1,291. The right
pair is **1,285 of 1,441**, as R5's own table gives it — 1,291 is the census row count, 1,441 the law
table under `--all`.

---

## R3. The seven Malay-only acts — AGC has no English file to fetch

No. This is not a failed fetch that can be retried; it is what AGC has filed. Act 680, the one in
scope, shows it plainly:

| Slot | Address |
| :---- | :---- |
| English (BI) | `outputaktap/15862_BI/Akta 680 BM Reprint 2017_unlocked.pdf` |
| Malay (BM) | `outputaktap/15863_BM/Akta 680 BM Reprint 2017_unlocked.pdf` |

**The same file name in both slots, and the name itself says `BM`.** AGC uploaded the Malay reprint
into the English project folder. There is no third address to try.

The other six are the same failure in one of two shapes. Acts 104 and 337 carry Malay file names
(`Akta 104 (cetakan 2018)`, `Akta 337 (Muktamad)`) inside `_BI` folders. Acts 348, 556 and 575 sit
under the portal's `/LOM/EN/` directory holding Malay files (`575 BM (Dimansuhkan).pdf`,
`556 Repealed by Act 679.pdf`). For all seven, every entry in `alternative_documents` is also the
Malay file — the portal offers no English candidate anywhere.

Two things narrow the request further: **three of the seven are `repealed`** (Acts 310, 556, 575), so
under R5 they leave the corpus regardless, and Act 310 is also one of the `other_act_text` files.
**R3's live scope is four acts, and Act 680 is the only one in scope for pillars 6 and 7.**

This is a portal defect worth reporting to AGC — precisely what "flag, do not fix" (CONVENTIONS rule
6) exists to surface. Extraction's fallback of `language_of_source: msa` is the correct record of what
AGC actually publishes today.

**One thing collection can still do, on the developer's word:** seven conditional requests
(`--verify-stored`), one per act, to confirm AGC has not replaced the files since 15 September. Seven
requests at 3 s is under a minute and well inside POLICY section 5. It is not run here because it is a
live request to a government portal, and the decision to send it is the developer's.

---

## R4. China's manifest — extraction should build it; one column is the only real gap

The recommendation is right: the schema is extraction's, the provenance sheets are collection's, so
extraction builds and collection reviews. Collection agrees. But the blocker is not ownership.

**First, so this is not misread: China's law text is fully readable today.** Measured 2026-09-24 over
all 11 layer-1 archives — **942 of 942 `.docx` documents carry a text layer**, 5,962,730 characters in
total, median 4,782 and up to 170,732, and **911 (96.7%) carry numbered articles (第N条)**. Nothing
about China blocks reading, quoting or extracting provisions. The gap below is in the manifest's
provenance columns, not in the documents.

**What China holds,** in three shapes, 1,102 active documents (the `_deferred/` sources excluded):

| Shape | Documents | What it carries |
| :---- | ----: | :---- |
| Auto (`auto/cac`, `auto/govcn`) | 117 | `provenance.tsv` with `url`, `fetched`, `via`; `run_log.jsonl` for govcn |
| Manual (`manual/miit`, its `mirror_permitted`) | 40 | `provenance.tsv` with `url`, `fetched_on`, `version_date_on_document`, `update_check`; saved by hand in a browser |
| Layer 1 (`manual/npc-database`) | 945 | `index.csv` — title, version date, kind, file, archive, bytes — inside **11 ZIP archives** |

**Most of the missing columns are free.** `content_sha256`, `byte_size`, `content_type`,
`source_type`, `pdf_is_scanned`, `page_count` and `local_path` are all computable offline from the
bytes; `law_name_guess` is the title; `economy` and `access_date` are in the sheets. Extraction can do
all of that without a request and without collection.

**Three columns the bytes do not supply.** Checked against the binding schema,
`stages\p1-scrape\contracts\schemas\manifest.schema.json` (0.2.0), whose `required` list holds all
three. Only the first is a genuine obstacle:

1. **`source_url` — the real gap, and only for the 945 layer-1 documents.** The schema requires
   `^https?://` and says the URL "must resolve at judging time". The bulk download records no address:
   `index.csv` has no URL column, and searching every part of the `.docx` packages — `document.xml`,
   `docProps/core.xml`, `app.xml`, `custom.xml`, the rels — finds no URL and no database id anywhere.
   The archive gives title and version date (the file name is `<title>_<YYYYMMDD>.docx`), which a
   person can resolve on `flk.npc.gov.cn` by title, but no tool can without per-document requests to a
   host whose robots.txt forbids automated collection. Under CONVENTIONS rule 13 that is a reported
   defect on 945 documents. The other 155 (117 auto, 38 manual) do carry URLs.
2. **`retrieval_method` — a one-value widening.** The enum is `playwright`, `requests`, `api`, and 985
   of China's 1,102 documents were saved by a person in a browser or came as a bulk archive. It needs
   a fourth value; that is all.
3. **`local_path` — a `mkdir` and an unzip.** The schema wants a relative path to stored bytes, and the
   945 documents sit inside 11 ZIPs. Unpacking them is a collection step and cheap. Not a blocker.

**And the contract change is smaller than it looks:** CONTRACT.md is explicitly "a draft proposal for
contract version 0.3.0" and says "nothing here binds until extraction agrees and it lands in one commit
across stages". So the retrieval method for hand-collected documents, and the rule for a document whose
publisher gives no per-document address, fold into the 0.3.0 work already in flight rather than needing
a bump on top of a settled contract. It still wants deciding before extraction writes the loader, so
that the loader is written against the agreed shape — but it is an amendment to a draft, not a
renegotiation.

---

## What needs the developer

| # | Decision |
| :---- | :---- |
| 1 | **R5 scope.** Drop repealed files from Malaysia (87, after the wrong-file carve-out) and Lao PDR (291)? Applied at the merge, not the crawl, for the reason above |
| 2 | **R5 and R2 order.** Does a repealed Lao law's English edition go with it? Yes gives 37 recovered English editions; no gives 53 and needs the drop rule to spare `language == eng` |
| 3 | **The `use` fix.** Should `_mark_use` read `legal_status`, so Malaysia's 90 repealed acts stop being marked `evidence`? Independent of 1 and 2, and the one that removes the actual risk |
| 4 | **R2 itself** — the language-aware `identity()`, one of the two shared-code defects already logged in `countries/la-lao-pdr/NOTES.md`, still awaiting a ruling |
| 5 | **R3's seven conditional requests** to AGC — yes or no |
| 6 | **R4's two amendments to the 0.3.0 draft** — a retrieval method for hand-collected documents, and what `source_url` holds for the 945 layer-1 documents whose publisher gives no per-document address. China's text is readable; this is the provenance column only |

Items 1 to 4 are merge-stage or checker-stage work on a new corpus folder, so rule 4 (never write into
an earlier run folder) and rule 7 (generated files are never hand-edited) both hold: the corpora are
rebuilt from the runs, not edited.

## What backs this note

| Claim | File |
| :---- | :---- |
| Repealed counts, `use`, status distributions | `outputs/{MY,LA,SG}/*/law_table.csv` |
| The 76 repeal notices, the 5 wrong files, the 7 language mismatches | `outputs/MY/MY_corpus_2026-09-15/audit.json` |
| The 53 superseded English editions, matched on `law` | `outputs/LA/LA_corpus_2026-09-21/superseded.jsonl` |
| Language, status and `timeline_log_type` per document | `countries/{my-malaysia,la-lao-pdr}/links/documents.jsonl` |
| Lao topic relevance | `countries/la-lao-pdr/sources.yaml`, `title_rule` |
| Malaysia's listing fields | `countries/my-malaysia/tests/fixtures/lom_updated_records_2026-09-13.json` |
| Scanned Lao originals | `outputs/LA/LA_ws_2026-09-21/manifest.jsonl`, `pdf_is_scanned` |
| China's holdings | `outputs/CN/CN_sources_2026-09-21/**/provenance.tsv`, `manual/npc-database/index.csv` |
| The exclusion mechanism | `tools/merge_corpus.py:1-20,156-220`; `countries/my-malaysia/scraper/checker.py:169-178` |
