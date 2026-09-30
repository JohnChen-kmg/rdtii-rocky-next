# Every country's tools rechecked, and how consistent their output really is — 24 September 2026

A recheck of the six countries' scrapers, adapters and tools: do they run, and do they produce output a
downstream stage can read the same way for every economy. **No network request was sent** — every check
reads files on disk or runs an offline test. Nothing in the workshop or the repo was modified; the
sandbox lives in the session scratch folder.

The 2026-09-22 workshop audit (`WORKSHOP_AUDIT_2026-09-22.md`) asked "does every suite pass". This asks
the next question: "and does every country say the same thing the same way".

**Headline: the tools work, and they reproduce what we already hold.** Every suite passes, every offline
entry point runs, **12 of the 13 committed law tables regenerate byte-for-byte, and the corpus builder
rebuilds Lao PDR's corpus byte-for-byte and Malaysia's on 1,365 of 1,391 rows** (section 2a — the
exceptions are artifacts predating a code change, not regressions). Against the developer's acceptance
test of 2026-09-25, "as long as the scraping tool match our current result", **the tools pass, and
nothing in section 4 needs applying to keep them passing.** The remaining problems are the countries
agreeing with each other, not with themselves — one value space with a fifth value, one column that means the opposite in one country, and
a validator that rejects two countries for a reason that is the validator's fault.

---

## 1. The sandbox, and why the suites split by location

Built as the 2026-09-22 audit prescribes: the engine stage copied out (without `handoff1_v2`, which
rule 3 says is never read), all five country install steps applied, a virtualenv from the stage's own
pinned `requirements-dev.txt` plus Malaysia's `cryptography==44.0.0`.

| Country | From the workshop | From the sandbox stage | Documented baseline |
| :---- | :---- | :---- | :---- |
| Malaysia | **175 passed** | 2 errors | 175 |
| Singapore | **36 passed** | **36 passed** | 36 |
| Australia | 1 error | **33 passed** (+9 multivolume) | 33 + 9 |
| Timor-Leste | 6 failed, 19 passed, 11 errors | **36 passed** | 36 |
| Lao PDR | 12 failed, 32 passed, 16 errors | **60 passed, 1 xfailed** | 60 + 1 |
| China | **51 passed** | n/a (no engine package) | 32 at the audit; grown since |
| Shared tools | **22 passed** | n/a | 22 |

**Every country reproduces its baseline. But no single location passes them all, and Singapore is the
only country green in both.** Three causes, all traced:

1. **Malaysia needs its own registry.** `tests/test_my_catalogue.py:52-62` resolves the registry as
   `../sources.yaml` first, which in the workshop is the country's real `sources.yaml` (6 top-level
   keys, carrying `title_rule`). In the stage that path does not exist, so it falls through to
   `contracts/instrument/sources_my.yaml` — the Round 1 copy, 4 keys, **no `title_rule`** — and
   collection dies on `KeyError: 'title_rule'`.
2. **Timor-Leste and Lao PDR look for fixtures at `tests/fixtures/<cc>/`**, a directory only their
   install step creates (`cp $WS/tests/fixtures/* $STAGE/tests/fixtures/tl/`). In the workshop the
   fixtures sit directly in `tests/fixtures/`, so every fixture read raises `FileNotFoundError`.
3. **Australia's `test_au_multivolume.py` does `import src…`**, so it needs the stage as working
   directory. It is the engine's own Round 1 test, not a country test.

**And one install-step defect, which is the second of Malaysia's two stage errors.** Malaysia's install
block deletes the flat adapter module (`scraper/WORKFLOW.md:32`) but never deletes the engine's own
`tests/test_my_selection.py`, which imports from it. A pytest *collection* error interrupts the whole
run, so **following Malaysia's documented install verbatim executes no Malaysian test at all.** One
`rm -f` line fixes it. Malaysia's own `NOTES.md:647` and `tests/README.md` already say the file should
go; the install block does not do it.

## 2. What runs offline, per country

| Country | Exercised without a request | Not exercisable offline |
| :---- | :---- | :---- |
| Malaysia | checker reproduced all 1,441 rows of `MY_corpus_2026-09-15/law_table.csv`, 0 differing; `updates.baseline.load()` read 1,415 link rows and 1,392 stored documents | **Every** `updates/__main__.py` mode fetches the lom listings, including `--list`; catalogue likewise. The largest offline gap of the five |
| Singapore | checker rebuilt `SG_corpus_2026-09-16/law_table.csv` field-for-field identical (1,068 laws, 738 scraped) | catalogue and update check reach `--help` only |
| Australia | checker rebuilt its table, `diff` exit 0 (4,779 laws, 1,278 scraped); whole update chain from fixtures: `baseline.load()` 3 runs / 4,776 titles, `diff.compare()`, `delta.write_changes()` | the live API query only. The most completely exercised |
| Timor-Leste | checker byte-identical to the stored table (4,788 acts, 4,677 scraped); `baseline.load()` 4,788 acts / 1,935 URLs | the crawl step cannot start at all (section 4) |
| Lao PDR | checker byte-identical on corpus and run; full chain baseline → parse → diff → delta; `tools/audit_run.py` on a synthetic folder | the crawl step cannot start at all (section 4) |
| China | all 7 tools `--help`; `layer1.py index` regenerated `index.csv` byte-for-byte (945 documents, 188,108 bytes); `manual_check.py` reproduced `MANUAL_UPDATE_CHECK.md` but for its date line; `checkdocs.py` over 4 folders (cac 111/111 exit 0; miit 21/23 exit 1); `collect.py` in three offline modes; `update.py --npc-new` | `collect.py`'s discovery half and the CAC / gov.cn halves of `update.py`. No checker step exists, by decision |

## 2a. The developer's bar: does the tool reproduce what we already have?

Asked and answered on 2026-09-25, after the developer set this as the acceptance test ("as long as the
scraping tool match our current result will be good"). **It does.** Every artifact reproduces, and the
only two exceptions are artifacts that predate a deliberate code change — in both cases the new output
is the better one.

**The law tables — 12 of 13 reproduce byte-for-byte.** Each was regenerated with today's code into a
scratch path and compared by md5. The checker takes `--all` or not, and the committed tables were built
both ways, so both were tried and the matching invocation recorded:

| Folder | Reproduces | With |
| :---- | :---- | :---- |
| `MY_corpus_2026-09-15` | yes | `--all` |
| `SG_corpus_2026-09-16`, `SG_ws_2026-09-15` | yes | `--all` |
| `AU_corpus_2026-09-16` | yes | either |
| `AU_corpus_2026-09-19`, `AU_ws_2026-09-15_to_2026-09-16` | yes | `--all` |
| `AU_corpus_2026-09-15`, `AU_ws_2026-09-19` | yes | plain |
| `TL_corpus_2026-09-20` | yes | `--all` |
| `TL_ws_2026-09-20` | yes | plain |
| `LA_corpus_2026-09-21` | yes | `--all` |
| `LA_ws_2026-09-21` | yes | `--all` |
| **`AU_ws_2026-09-15`** | **no** | — |

The one exception is explained and is not a regression: `AU_ws_2026-09-15/law_table.csv` has **21
columns and no `use`**. It was committed 2026-09-16, and `use` is decision 20, taken that same day. The
current code emits 22 columns, so it cannot reproduce a pre-decision-20 table by construction.
Regenerating it would *add* `use`.

**The corpus builder reproduces too.** `tools/merge_corpus.py` was re-run from the runs on a short path
(the scratchpad prefix alone is ~150 characters, so the rebuild first failed with `WinError 3` — the same
260-character limit that cost Singapore 2 PDFs; a `subst` drive, the technique this workshop already uses
for Singapore, works):

- **Lao PDR** (`LA_corpus_2026-09-21`, built after the long-path guard landed): `manifest.csv`,
  `manifest.jsonl`, `superseded.jsonl` (all 53 rows), `links_used/documents.jsonl` and
  `links_used/laws.csv` **all byte-identical**. Same 1,762 documents, 53 superseded, 1,695 flagged.
- **Malaysia** (`MY_corpus_2026-09-15`): same 1,391 documents, 18 superseded, 0 excluded, 178 flagged,
  validation OK; `superseded.jsonl` and both link files identical. **1,365 of 1,391 manifest rows
  identical**; the 26 that differ differ only in `local_path` and `http_headers_path`, because their
  folder names are 81-127 characters and the current code caps anything over 80.
  `FOLDER_MAX`/`_short()` was added **2026-09-20** (commit `df9a763`, Timor-Leste's crawl); the Malaysia
  corpus was committed **2026-09-16**. So the rebuild differs only where a later guard now applies, and
  that guard is the fix for the failure that lost Singapore two documents.

**China reproduces as well.** `tools/layer1.py index` regenerates
`manual/npc-database/index.csv` — 945 documents read back out of the 11 archives — byte-for-byte; git
reports no modification after the rewrite. (It writes in place and has no `--out`, which is worth
knowing before running it.)

**One thing the rebuild exposed.** `LA_corpus_2026-09-21/corpus_meta.json` records
`validation: {ok: true, errors: []}`, but rebuilding it today gives `ok: false` with the `economy` and
`doc_id` errors of section 4. The corpus was therefore validated on 2026-09-21 against a **widened
schema that exists only in a sandbox**; the repo's schema still rejects Lao PDR. That is the hand-back in
section 4 item 4, and the mismatch between the recorded `ok: true` and today's result is the clearest
evidence it has not landed.

**So, against the developer's bar: the tools pass.** Everything in section 4 below is about the countries
agreeing *with each other*, not about any tool failing to reproduce its own output — and every fix
proposed there would, by design, change output that currently matches. None of it should be applied to
meet this bar.

## 3. Where the output IS consistent — more than expected

- **The five corpus manifests have an identical 29-key shape.** Every one of the binding schema's 15
  required fields is present in all five; `retrieval_method` only ever holds legal enum values
  (`requests`, `playwright`); every null `pdf_is_scanned` sits on a `source_type: html` row, which the
  schema permits (AU 793, MY 2, the rest none). No country carries a key another lacks.
- **All 18 leading law-table columns are present in all five countries, and their relative order is
  identical in all five.** A stage reading by column name, or by the relative order of the contract
  columns, gets the same thing everywhere.
- **`updates/watchlist.tsv` exists for all six** (rule 11): MY 24 sources, CN 66, TL 16, AU 14, SG 14,
  LA 12.
- **Four of five checkers reproduce their shipped law table exactly** from the folder alone, sending no
  request — the reproducibility rule 7 depends on.

## 4. Where it is not — what is worth fixing

### (a) A tool that cannot run

1. **Lao PDR cannot be crawled from a clean stage.** All four engine edits its workflow asks for are
   absent: `economies.py:4-10` has `VALID_CODES = ("SG","AU","MY")` so `parse_economies('LA')` raises;
   `registry.py:5-19` registers no LA adapter; `utils.py:23-32` `slugify` returns `'unknown'` for Lao
   script, so a forced run would file every Lao law under one slug. These are the hand-backs already
   written at `la-lao-pdr/NOTES.md:269-275`. They are edits to the read-only repo, so this is a
   hand-back, not a fix here. Malaysia, Singapore and Australia need none of them.
2. **Timor-Leste has the same blocker, recorded where a reader will not find it.**
   `get_adapter('TL')` raises `NotImplementedError`. But TL's `NOTES.md:182` says "Nothing specific to
   Timor-Leste yet" under *What the engine must change*, its install block does not mention it, and its
   troubleshooting table has no row for it — the fact appears only in
   `outputs/TL/TL_ws_2026-09-20/RUN_NOTE.md:44`. Lao PDR records the same two facts in both places.
   **Consequence:** the 16-document delta in `TL_ws_2026-09-22_to_2026-09-22` cannot be crawled by
   following Timor-Leste's own workflow. Two documentation lines.
3. **Malaysia's install runs no Malaysian test** — section 1, one `rm -f`.

### (b) Output a downstream stage would trip on

4. **`scrape.py --validate` rejects Timor-Leste and Lao PDR on every row — and it is the validator's
   fault, not theirs.** Measured: MY **OK, 0 errors**; SG 5; AU 2; TL **7,684**; LA **7,048**. Every one
   of TL's and LA's is the binding schema hard-coding the three Round 1 economies —
   `economy: {"enum": ["SG","AU","MY"]}` and `doc_id: "^(sg|au|my)-[a-z0-9]+-\\d{3}$"`. `CONTRACT.md`
   lines 78-79 already propose widening both (`^[A-Z]{2}$`, `^[a-z]{2}-[a-z0-9]+-\d{3}$`) as part of the
   unlanded 0.3.0 draft. **Zero real defects in either country.** Two lines in the repo's
   `manifest.schema.json`, and until they land a validating stage accepts Malaysia and rejects 3,683
   Timorese and Lao rows wholesale.
5. **Singapore's 5 and Australia's 2 validator errors are real.** Manifest paths that do not resolve on
   disk, every one 213-233 characters long — the Windows 260-character limit, the same failure
   `merge_corpus.py`'s `FOLDER_MAX = 80` exists to prevent. Singapore is missing **2 actual PDFs**
   (`sg-itr2020-001`, `sg-cr2026-001`) plus 3 header sidecars; Australia is missing 2 sidecars only, no
   document.
6. **`use` has a fifth value, `not held`,** which decision 20 does not define: Timor-Leste 106 rows,
   Lao PDR 7 (`tl/checker.py:107-108`, `la/checker.py:234-235`). Malaysia, Singapore and Australia never
   emit it, and the string appears nowhere in CONVENTIONS or DECISIONS. A downstream filter on the four
   legal values drops those 113 rows. Worse, `la/checker.py:220` documents it as what "every other
   country's checker writes", which is false for three of the four.
7. **Australia labels 3,501 of its own amending acts `use: evidence` with no `source_url`** — 73% of its
   table. Verified: all 3,501 have `scraped: no`, empty `document_kind`, no address, and their own
   `notes` column says "an amending or consequential act". So the row tells extraction to read as
   evidence a document that is not held, is linkage under decision 20, and has no address to fetch.
   Cause: `au/checker.py:176` takes `document_kind` from an empty field for non-crawled titles, so
   `_mark_use` falls through to `evidence`. Malaysia's comparable rows come out `amending_act` /
   `linkage`. Two lines.
8. **Timor-Leste's row grain is one act, not one document.** 4,677 populated rows carry 1,921 distinct
   `doc_id`; the worst repeats 39 times. Malaysia 1,391/1,391, Singapore 738/738, Australia 1,278/1,278,
   Lao PDR 1,766/1,762. **A join on `doc_id` fans out for Timor-Leste and nowhere else.** The cause is
   real — one gazette PDF carries several acts — and TL's `NOTES.md` section 5 lists it as an open
   choice, not a settled contract. It needs settling before extraction joins on `doc_id`.
9. **`linkage` means the opposite in Timor-Leste.** `tl/checker.py:104-106` keys on whether the document
   is *stored*, not on decision 20's stale-pair relation: a stored amending act becomes
   `linkage, text needed` and an unstored one `linkage`. Timor-Leste's table has **no**
   `(scraped=yes, linkage)` row at all; Malaysia has 384. So the OCR saving decision 20 was made for is
   zero for Timor-Leste.
10. **Singapore marks 7 amending instruments `use: evidence`** — the `synthetic_rows: 7` in its
    `catalogue_meta.json`, whose `contract_meta` carries no `document_kind`, so `sg/checker.py:131-139`
    falls through. Among them the Cybersecurity (Amendment) Act 2024 and the Personal Data Protection
    (Amendment) Act 2020, both in scope. A downstream stage maps an amendment as a principal law.
11. **Lao PDR's corpus holds none of the 55 translations its own law table reports** — the
    language-blind `identity()`, already covered in full by extraction's R2 and
    `notes/2026-09-23_answers-to-extraction.md`.
12. **Lao PDR's `notes` drops every review flag.** `la/checker.py:126-137` never reads `review_flags`,
    while Malaysia, Singapore and Australia all begin `notes = list(meta.get("review_flags") or [])`.
    Its census carries 368 flags (`superseded_listing` 309, `unofficial_translation` 55,
    `listed_under_several_kinds` 4); `notes` is filled on 8 of 1,773 rows against 36% of Malaysia's.
13. **`in_force` outside the four readings, and an unvalidated fallback.** Malaysia writes `"in part"`
    on 2 rows (Act 508, Act A1530), against CONVENTIONS' four readings. But `POLICY.md:89` says
    "record what the portal states" and `legal_status: partially_in_force` is legitimate
    (`CONTRACT.md:108`), so `"in part"` is *truthful* — the readings are what is too narrow, and
    mapping it away would destroy information. **The real defect is the fallback at
    `my/checker.py:110-111`, which passes any unmapped status through verbatim**, so a status nobody
    anticipated becomes an unvalidated value in a contract column with no error. Australia has the same
    latent pair at `au/checker.py:57-58` (`"no (ceased)"`, `"never in force"`, 0 rows today).
14. **`last_amended` granularity — weaker than it first looks, and not a contract breach.** Malaysia
    writes a full gazette date where the other four write a year. But `CONTRACT.md:115` defines
    **`last_amended_year`** (`^\d{4}$`) as a *manifest* column and marks its definition open; the law
    table's column is **`last_amended`** (CONVENTIONS section 2 step 7), which is a different column in
    a different file with no format given. So this is a cross-country comparability nit, not a
    violation — and Malaysia's value is the more informative one. Either the law table's `last_amended`
    gets a stated format and everyone follows it, or this stays as documented variation.
15. **`document_kind` vocabulary splits 3-to-1, and the majority is the side that is wrong.**
    `CONTRACT.md:110` enumerates thirteen values including `other` and `repealing_act` — the spellings
    **Lao PDR** uses — and does **not** include `agency_or_other`, which Singapore (5), Australia (3)
    and Timor-Leste (3,311) all emit. So Lao PDR is on contract and the other three are off it, on
    3,319 rows. Aligning the three to `other` is the change the contract asks for.
16. **Interleaved leading columns in Malaysia, Singapore and Australia.** All 18 contract columns are
    present and in the same relative order everywhere, but Malaysia inserts 5 country columns among
    them, Singapore 3 and Australia 4, so `effective_date` sits at index 9 in Australia, 10 in Malaysia
    and 9 in Singapore — no two of the three agree. Only Lao PDR and Timor-Leste literally append their
    extras as CONVENTIONS section 2 step 7 says ("a country adds its own after these"). Reading by name
    is safe; reading by position is not. Either three `COLUMNS` lists change, or the convention's wording
    does — Malaysia, the worked example the sentence was written from, is the origin of the drift.

### (c) Two footguns shared by all five, so nobody's deviation

17. **No checker has an economy guard.** `grep -n economy` over all five `scraper/checker.py` returns
    nothing, and the default output is `law_table.csv` **inside the folder given**
    (`my/checker.py:237`). So pointing Malaysia's checker at Timor-Leste's corpus silently overwrites
    Timor-Leste's law table with a 23-column Malaysian one built from Timorese data. One `if` per
    checker.
18. **No `updates/__main__.py` wraps `main()` in try/finally**, so rule 11's closing "sources this check
    cannot see" list is skipped whenever a check raises — exactly when a reader most needs to know the
    check was incomplete.

## 5. What this recheck did NOT cover

**No network request was sent.** So nothing here tests whether any portal still answers or still answers
the way the adapter expects; whether a crawl completes, resumes or survives a WAF challenge (Singapore's
challenge after ~130 requests is untested); whether any catalogue step still parses today's pages;
whether any update check finds a real change — Australia's, Lao PDR's and Timor-Leste's chains ran
against saved fixtures and produced "unchanged", which proves the plumbing and not the parsing; or
robots.txt, pacing and the rest-and-slow-down behaviour.

Also not covered: whether the corpora's *content* is right (OCR quality, translation accuracy, whether a
status reading matches the portal today), and any comparison against earlier RDTII rounds, which does not
exist yet.

**And one provisioning caveat.** The sandbox installed the packages and tests but ran no country's
registry step: the stage's `sources_my.yaml`, `sources_sg.yaml` and `sources_au.yaml` are byte-identical
to the repo's Round 1 copies and `sources_la.yaml` is absent, so **no catalogue was run against the
registry its own workflow builds.** That the assembly itself is sound was checked separately: applying
Singapore's step 1 to the workshop files yields fingerprint `e44e4da7c2a98f64`, matching the
`cfg_sha256` in its shipped link list, and Australia's reproduces `cd262ac2…` exactly.

## What backs this note

| Claim | How it was produced |
| :---- | :---- |
| Suite results, both locations | `pytest` per country, sandbox venv, `PYTHONPATH=<stage>/src` |
| Validator results and error split | `scrape.py --validate <corpus>/manifest.csv`, errors grouped by kind |
| The stale enum and id pattern | `stages/p1-scrape/contracts/schemas/manifest.schema.json`; `CONTRACT.md:78-79` |
| Manifest key shape, required fields, nulls | `outputs/*/*_corpus_*/manifest.jsonl` |
| Leading-column set, order and relative order | header of every `outputs/*/*/law_table.csv` against CONVENTIONS section 2 step 7 |
| `use`, `in_force`, `scraped` value spaces; AU's 3,501; TL's row grain | the five newest `law_table.csv` |
| Missing files | every `local_path` and `http_headers_path` resolved against the corpus folder |
| Registry difference | `title_rule` presence in the stage copy versus the workshop copy |
| Per-country offline runs, install-step reads, China's seven tools | the 13-agent audit of 2026-09-24; every finding put to a skeptic before it was kept |
