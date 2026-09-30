# Plan: Scraping

Workstream 1 of the finale build plan. Two steps, about 25 hours, plus adapter work that is
blocked on the host's answer about economies. Code freeze is 30 September 2026.

All paths below are relative to `C:\Users\woshi\Desktop\rdtii-rocky-finale\stages\p1-scrape`
unless the path starts with `interface/`, `stages/` or `main.py`, which are repo root. A bare
`docs/` means `stages/p1-scrape/docs/`. The repo also has its own `docs/` at the root, so read
the prefix before you open a file.

### Changed by the host templates, read 2026-09-12

The workbook's Run Record sheet says C5a scores zero if no documents are fetched during the live
hour, and the checklist requires caches clearable on screen. Three new steps follow. They are
proposed, not yet agreed, and they are not in the hour counts below.

| Step | What | Hours | Needed for freeze |
| :---- | :---- | ----: | :---- |
| 1C | **Seed-scoped live discovery.** Given an economy, a pillar and two indicator IDs, fetch only the seed laws tagged with those indicators, inside the politeness limits, in minutes. Scoped down on 2026-09-12: reuse the existing `--scope seed` mode for the six covered economies and pillars 6 and 7. A general ranked discovery for any economy and pillar is optional | 3 to 4 | Yes |
| 1D | **Cache clear.** One function that empties the run's raw folder, crawl log and `.idmap.json`, callable from the interface. Clearing the raw folder but leaving the index makes the resume check skip every law, which is exactly the C5a zero | 2 | Yes |
| 1E | **Run Record export.** Tag every crawl-log line with the pass, Engine A or Engine B, and export the host's columns: source URL, pass, time hh:mm, size KB, file type | 2 | Yes |

The nine live-test economies now matter more than the C1a count. Viet Nam and Kazakhstan are in
the draw with no baseline sheet, so an adapter for each moves from stretch to live-test risk.

## Step 1A: economy-agnostic crawler, about 13 hours

Goal: adding an economy means adding one YAML file and one adapter module. No edit to
`economies.py`, no edit to `registry.py`, no edit to a schema.

| # | Task | Hours | Files touched |
| :---- | :---- | ----: | :---- |
| 1A-1 | YAML economy header | 1.5 | `instrument/sources_{sg,my,au}.yaml` and the three copies in `contracts/instrument/` |
| 1A-2 | `economies.py` reads the glob | 2.0 | `src/p1_scrape/economies.py`, `src/p1_scrape/sources.py` |
| 1A-3 | Registry imports by name | 1.5 | `src/p1_scrape/adapters/registry.py` |
| 1A-4 | `law_slug` honoured, hash fallback | 2.0 | `src/p1_scrape/utils.py`, `storage.py`, `dedup.py`, `orchestrator.py` |
| 1A-5 | Language plumbed end to end | 2.0 | `src/p1_scrape/models.py`, `orchestrator.py`, `fetcher.py` |
| 1A-6 | Contract bump to 0.3.0 and re-vendor | 2.0 | `CONTRACT_VERSION`, three `manifest.schema.json` copies, `models.py` |
| 1A-7 | Written checklist and adapter template | 2.0 | `docs/ADDING_AN_ECONOMY.md`, `src/p1_scrape/adapters/_template.py` |

### 1A-1 YAML economy header, 1.5 h

Add a header block above the existing `economy: SG` key in each sources file. Eight keys: `code`,
`name`, `matrix_label`, `aliases`, `adapter`, `default_language`, `script` and `smoke_urls`. The
template is `countries/_template/sources.yaml`.

`name` is the official UN name and `matrix_label` the Coverage Matrix row label (host question 7).
`adapter` carries a module path such as `p1_scrape.adapters.sg_sso:SgSsoAdapter`. `smoke_urls` lists
the URLs the adapter's portal must serve, and the first that answers wins. They are used by
`src/p1_scrape/smoke.py`, which runs as `python scrape.py --smoke`, and by the deploy check.

Edit `instrument/` and `contracts/instrument/` in the same commit. They are byte-identical today.
`sources.py` `_SEARCH` prefers the `contracts/instrument/` copy, so editing only the working copy
changes nothing and gives no error.

**Done when** all three files parse under `yaml.safe_load` and carry all eight keys.

### 1A-2 `economies.py` reads the glob, 2.0 h

Delete `_NAME_TO_CODE` and `VALID_CODES`. Replace them with a cached function. It globs
`sources_*.yaml` across both directories in `sources.py` `_SEARCH` order. First hit wins per code.
It builds the code and alias tables from the headers.

Keep `BadCountryInput`, `normalize_economy` and `parse_economies` signatures unchanged.
`cli.py` imports all three and `main.py` drives `scrape.py` with `--economy`, so a signature
change ripples further than it looks.

`parse_pillars` still hard-limits to pillars 6 and 7 at `economies.py:57`, with the same pair
repeated in the fallbacks at lines 47 and 59. That is a twelve-pillar task, not this one. Leave it
and note it in the code map.

**Done when** `python -c "from p1_scrape.economies import parse_economies; print(parse_economies('all'))"`
prints the codes with no list in the file, and dropping a fourth YAML in makes it appear.

### 1A-3 Registry imports by name, 1.5 h

Replace the if-chain in `get_adapter` with `importlib.import_module` on the header's `adapter`
value, then `getattr` for the class. Raise a clear error naming the YAML file and the missing
module when the import fails. A typo in a YAML must not surface as a bare `ImportError`.

**Done when** `get_adapter("SG")` still returns `SgSsoAdapter` and no economy code appears
anywhere in `registry.py`.

### 1A-4 `law_slug` honoured with a hash fallback, 2.0 h

Two separate slug paths exist and both break on non-Latin text.

| Function | Used for | Break |
| :---- | :---- | :---- |
| `utils.slugify` | The `raw/<cc>/<slug>/` directory, via `storage.Storage.store` | Returns `"unknown"` for a title with no ASCII letters |
| `utils.acronym_slug` | The `doc_id` middle segment, via `dedup._slug_key` | Returns `"law"` for the same input |

Fix both. Prefer `Candidate.law_slug` when the adapter sets it. Otherwise transliterate where a
cheap rule exists, and otherwise fall back to a short sha256 prefix of the title so two different
Thai laws cannot land on the same key. Thread `cand.law_slug` into the `storage.store` call at
`orchestrator.py:345` and into `dedup.stable_id` at `orchestrator.py:346`.

The fallback must be deterministic. A re-run has to mint the same `doc_id`, or `.idmap.json`
supersession breaks and every downstream join breaks with it.

**Done when** a unit test feeds two distinct Thai titles and gets two distinct directories and
two distinct `doc_id` values, stable across two calls.

### 1A-5 Language plumbed end to end, 2.0 h

Add `language` and `source_language_note` to `Candidate`, to `MANIFEST_FIELDS` and to
`_build_row` at `orchestrator.py:357`. The adapter sets them. The YAML header's
`default_language` supplies the value when the adapter cannot tell.

Also make the fetcher stop forcing English. `fetcher.py:73` sets `Accept-Language: en` on the
requests session at construction time, and `fetcher.py:85` sets a US locale on the Playwright
context. Both are per-`Fetcher`, not per-request, so a per-plan header is the cleaner fix. Add
an `accept_language` field to `FetchPlan` and apply it in `_rung_requests` at `fetcher.py:152`.
The Playwright locale is harder, because the context is created once and reused. Recommendation:
set the context locale from the economy currently being crawled in `run_crawl`, and recreate the
context when the economy changes. Crawls are per-economy sequential, so the cost is one browser
context per economy, not per document.

**Done when** an SG row still reads `en`, and a manual Thai fetch records `th` with the portal's
own `Content-Language` header visible in the sidecar.

### 1A-6 Contract bump to 0.3.0 and re-vendor, 2.0 h

Four optional columns appended, two patterns widened, three files changed, one commit.

| Change | Where |
| :---- | :---- |
| Append `language`, `source_language_note`, `superseded_by`, `run_id` | `models.py:15` `MANIFEST_FIELDS`, and `properties` in each schema copy |
| Widen `economy` from the `SG, AU, MY` enum to a two-letter pattern | schema line 41 in each copy |
| Widen `doc_id` from `^(sg\|au\|my)-...` to `^[a-z]{2}-[a-z0-9]+-\d{3}$` | schema line 37 in each copy |
| Set `0.3.0` | `CONTRACT_VERSION` |

The three copies are `contracts/schemas/manifest.schema.json`,
`stages/p2-extract/00_contracts/schemas/manifest.schema.json` and
`stages/p3-map/00_contracts/schemas/manifest.schema.json`. All three set
`additionalProperties: false`, so a p1 row carrying a new column fails p2 validation until p2 is
re-vendored. Re-vendor in the same commit. This is the single highest-risk edit in the workstream,
because it breaks two downstream stages if half-done.

Fix the two drifts while the file is open. The p1 copy's description still says "24 fields" and
carries 28. The `indicator_hints` description at line 77 still gives the legacy `P7-I2` example.
Lines 37, 41 and 77 hold the same content in all three copies.

**Done when** `python scrape.py --validate <manifest>` passes on the existing frozen manifest at
`C:\Users\woshi\Desktop\RDTII\pipeline-data\rdtii-p1-scrape\handoff1_v2\manifest.csv` with 0
errors, and p2 ingests the same file unchanged.

### 1A-7 Checklist and adapter template, 2.0 h

Write `stages/p1-scrape/docs/ADDING_AN_ECONOMY.md`. Numbered, no prose, with the order of
operations and the smoke command at each stage. Add `src/p1_scrape/adapters/_template.py` with
the three methods stubbed and every portal-specific decision marked.

This document is worth marks on its own. C4a wants a stranger deploying from documentation.
C1a wants "minimal reconfiguration", and a checklist is the proof that the reconfiguration is
minimal rather than the claim that it is.

**Done when** someone can follow it end to end without opening `orchestrator.py`.

## Step 1B: delta crawl, about 12 hours

Goal: a second run fetches only what changed, and reports what it did. The host states twice that
the live test's second pass must fetch nothing and must read 0 documents.

| # | Task | Hours | Files touched |
| :---- | :---- | ----: | :---- |
| 1B-1 | `current_version` lookup in the index | 2.0 | `src/p1_scrape/dedup.py` |
| 1B-2 | Conditional headers and 304 | 2.5 | `src/p1_scrape/fetcher.py`, `models.py` |
| 1B-3 | Plan-URL comparison first | 1.5 | `src/p1_scrape/orchestrator.py` |
| 1B-4 | Hash before store | 2.0 | `src/p1_scrape/orchestrator.py` `_store_row` |
| 1B-5 | `superseded_by` written back | 1.5 | `orchestrator.py`, `src/p1_scrape/manifest.py` |
| 1B-6 | Run record and changed-docs file | 1.5 | new `src/p1_scrape/run_record.py` |
| 1B-7 | `--delta` reachable from the button | 1.0 | `cli.py`, `scrape.py`, `main.py`, `interface/dashboard.py` |

### 1B-1 `current_version` lookup, 2.0 h

`.idmap.json` already stores a per-law version list with `content_sha256`, `first_seen` and a
`current` flag, written by `dedup.stable_id`. Add a read side. Return the current entry's sha, the
stored plan URL and the stored validators for a given economy and law.

The plan URL and the validators are not in the index today. Add them at write time in
`stable_id`. The validators exist already in the `.headers.json` sidecars, so a backfill is
possible, and is on the cut list rather than the critical path.

**Done when** a lookup against the frozen `.idmap.json` returns the right sha for a known law.

### 1B-2 Conditional requests, 2.5 h

Send `If-None-Match` and `If-Modified-Since` when the index has validators. Treat `304` as a
success with no body, not as a failure. `_rung_requests` at `fetcher.py:152` is the only rung
that can do this cleanly, so a delta check should pin `method="requests"` and never escalate to
Playwright on a 304.

`_with_backoff` at `fetcher.py:130` retries on throttle statuses. Check that 304 is not caught in
that net before writing anything else.

**Done when** a re-fetch of an unchanged SG PDF returns 304 and logs `unchanged`, with one request
and no bytes stored.

### 1B-3 Comparison order, 1.5 h

Compare in this order, and stop at the first answer.

| Order | Test | Why it comes first |
| ----: | :---- | :---- |
| 1 | Plan URL against the stored URL | Australia embeds the compilation date in the URL, so a changed URL is a changed law with no request at all |
| 2 | Conditional GET | Singapore and Malaysia send `Last-Modified`, so one cheap request settles it |
| 3 | sha256 of the body | The arbiter when neither of the above is conclusive |
| 4 | Text hash for PDFs | Singapore regenerates PDF bytes server-side, so a byte hash alone reports false updates |

The order is not a guess. Counted over the `.headers.json` sidecars in the frozen
`handoff1_v2/raw/` tree on 2026-09-12, the validators each portal actually sends are these.

| Economy | Sidecars | Carry `Last-Modified` | Carry `ETag` |
| :---- | ----: | ----: | ----: |
| SG | 545 | 545 | 4 |
| MY | 869 | 866 | 866 |
| AU | 1,302 | 1 | 399 |

Australia is the economy a conditional GET cannot settle, which is why the URL test has to come
first. Singapore and Malaysia are settled by test 2 almost every time.

Test 4 is the cut candidate. Without it, SG PDFs will occasionally report a spurious update. That
costs a re-fetch and a superseded row. It never loses a document, which is why it can be cut.

### 1B-4 Hash before store, 2.0 h

Today `_store_row` at `orchestrator.py:325` computes the sha on line 336, then calls
`dedup.content_is_new` on line 337. That guard only catches duplicates inside the current run,
because `_seen_sha` starts empty on every run. The one cross-run comparison is `dedup.stable_id`
on line 346, and by then `storage.store` has already written the bytes on line 345. So an
unchanged re-fetch leaves a second copy on disk under a new timestamped filename, in the
`raw/<cc>/<law_slug>/<ts>__<kind>.<ext>` layout that `storage.store` uses.

Move the decision above the write. If the sha matches the current version, log `unchanged`, do
not store, do not mint a row, and count it in the run record.

**Done when** a delta run over an unchanged economy adds 0 files under `raw/` and 0 manifest rows.

### 1B-5 `superseded_by` written back, 1.5 h

`stable_id` already returns a `supersedes` note. `_build_row` at `orchestrator.py:357` puts it
into `crawl_notes` as free text, on `orchestrator.py:386`. Free text cannot be joined on. Write
the new `superseded_by` column onto the **old** row instead.

`write_manifest` in `manifest.py` needs no change. It rewrites `manifest.csv` and
`manifest.jsonl` in full from the row list it is handed. The work is to mutate the prior row in
memory before that write. `_load_existing_manifest` at `orchestrator.py:130` loads the prior rows
and `orchestrator.py:177` puts them into `rows_by_id`, so the old row is already there to edit.

Keep `crawl_notes` populated as well for one release. Two readers depend on it.

### 1B-6 Run record, 1.5 h

Write `run_record.json` beside `cost_report.json` in the hand-off directory. Model it on
`cost.py` `CostMeter.write`, which is the existing pattern for a measured, non-estimated artifact.

| Field | Meaning |
| :---- | :---- |
| `run_id` | Also written onto every manifest row minted in this run |
| `new` | Documents seen for the first time |
| `updated` | Documents whose content changed |
| `unchanged` | Documents confirmed identical, the number that must read 0 documents fetched |
| `gone` | Documents in the index that the portal no longer serves |
| `changed_doc_ids` | Newline-delimited file path, for the next stage |

Write the changed list as a plain file of `doc_id` lines. P2's `--only-docs` flag reads a file,
not a comma list, per `stages/p2-extract/src/rdtii_p2/cli.py:68`. Match that format exactly.

`gone` detection is the first thing to cut. It needs a full portal re-discovery to be trustworthy,
which is the expensive half of a crawl.

### 1B-7 `--delta` reachable from a button, 1.0 h

A run starts from a button, not a command line. The flag has to travel four files.

| File | What to add |
| :---- | :---- |
| `src/p1_scrape/cli.py` | `--delta` on the `crawl` sub-parser at line 24 |
| `scrape.py` | `--delta` in `_translate`, passed through to the canonical verb |
| `main.py` | A `--delta` argument, and the flag appended to both `scrape.py` argv lists, at lines 467 and 481 |
| `interface/dashboard.py` | A checkbox in the run spec, and the flag in `build_cmd` at line 962 |

`main.py` builds the `scrape.py` argv twice, at lines 467 and 481. Both hard-code
`--seed-laws-only` on the next line and neither offers a delta option. Patch both, or the flag
works from one run mode only. Without this step the delta crawl exists and no judge can reach it.
One hour of plumbing protects six marks.

**Done when** a second press of the same button in the interface reports 0 documents fetched.

## Minimum for the 30 September freeze

| Must ship | Why |
| :---- | :---- |
| All of 1A | C1a is 15 marks and is the largest single item this task touches |
| 1B-1 to 1B-4 | Delta detection with `--delta`, which is what makes a second pass read 0 |
| 1B-7 | A capability no judge can reach scores nothing |
| 1C, scoped down, 1D cache clear, 1E run record | Added 2026-09-12. Without them the first pass can fetch nothing and C5a scores zero. Under the scope decision 1C shrinks to about 3 to 4 hours: reuse the existing `--scope seed` mode, filtered to seed laws tagged with the two drawn indicators, for the six covered economies only |
| **Exactly three new economy adapters, all non-English** | Scope decision 2026-09-12, `DECISIONS.md` decision 7. Six economies total. Seed laws for pillars 6 and 7 only. Prefer live-test economies. A fourth is optional |

Settings may change after 30 September. Code may not. Anything that needs a code edit on
15 October is not shippable, and that includes adding an economy.

## What gets cut first, in this order

| Order | Cut | Cost of cutting |
| ----: | :---- | :---- |
| 1 | `gone` detection in 1B-6 | The run record reports new, updated and unchanged only. Say so in the field list rather than omitting the field |
| 2 | Rebuilding `.idmap.json` from a manifest | Recovery from a lost index means a full re-crawl. Acceptable while the index is backed up |
| 3 | The PDF text-hash guard, test 4 in 1B-3 | SG PDFs occasionally report a false update. Wasteful, never wrong |
| 4 | The adapter template `_template.py` | The checklist in 1A-7 still ships. The template is a convenience, the checklist is the evidence |

Do not cut 1A-6. A half-vendored schema breaks p2 and p3, and that costs far more than it saves.

## Blocked: new economy adapters

Blocked on host question 1, filed in
`C:\Users\woshi\Desktop\RDTII Finale Plan\3_Final_Stage\OPEN_QUESTIONS_FOR_HOST.md`.

| Item | Estimate |
| :---- | :---- |
| One adapter, discover plus build_plans plus anchors | 4 to 8 hours |
| Seed-law curation for one economy | 2 to 4 hours |
| First full crawl, per economy, wall clock | 6 to 8 hours, politeness-limited |

The crawl hours are not developer hours, but they are calendar hours and they cannot be
parallelised across hosts without breaking the politeness limits. Plan the crawls overnight and
start them before the adapters are polished.

## Changed by the instrument notice, read 2026-09-13

The instrument moved to decimal IDs and 61 indicators across twelve pillars. Nothing in this stage
breaks at its hand-off, but several steps below are now incomplete. The full list, with file and line,
is `notes/INSTRUMENT_IMPACT_2026-09-13.md`. The requests are in `notes/REQUESTS_TO_INSTRUMENT_2026-09-13.md`.
The steps are not rewritten yet, because the scope decision in item C2 comes first.

| Step | What changes | Item |
| :---- | :---- | :---- |
| 1A-1 | Done-when also needs a registry lint: quoted IDs, in scope, not non-regulatory | A3 |
| 1A-2 | `parse_pillars` cannot stay deferred. It widens any pillar to 6 and 7, and code freezes 30 September | A4 |
| 1A-5, 1A-6 | Add `pillar_hint`, `indicator_hints`, document kind, amendment link and observed status. P2 and P3 `laws.schema.json` change too. The done-when cannot pass as written | B1 to B6 |
| New | Migrate registries and helpers to decimal IDs, in one commit | A1, A2, C5 |
| 1C | Pillars 1 to 12, an `--indicators` input, a loud failure on zero seeds, and a scope that says which draws it covers | A5, A6, C1, C3 |
| Estimates | Every figure assumes pillars 6 and 7 | C6 |
