# Run note: AU_ws_2026-09-15_to_2026-09-16

Australia, **the first update check**, 16 September 2026: what the Federal Register has registered since the day
the link list was built, and the crawl of the one document that changed.

## Read this first

- **The whole Australian statute book was checked in 3 requests**, plus 2 for `robots.txt`. No document was read
  to find out what changed: the register states version identity, so a comparison of ids is enough.
- **One law changed:** the Water Act 2007, recompiled from `C2026C00302` to `C2026C00398`, in force from
  5 September 2026, registered on 16 September, by the Murray-Darling Basin Agreement flows regulations. It was
  fetched into this folder.
- **39 other titles the query returned were dropped as out of scope**, and the count is kept: 21 legislative
  instruments this country does not collect (decision 12 takes subsidiary instruments only under an in-scope
  principal law), 9 notices, 8 gazette notices and 1 bulletin. **None of them is a missed law**; a new Act would
  have been kept.
- **The corpus was rebuilt with this run:** `outputs/AU/AU_corpus_2026-09-16`, 1,277 documents, the older Water
  Act copy superseded.

## At a glance

| | |
| :---- | :---- |
| Country | Australia (`AU`) |
| Run type | Update check against `AU_ws_2026-09-15` (since 2026-09-15, the day that run's list was built), then the crawl of its delta list |
| Date | 2026-09-16 |
| Time, UTC | Check 17:12:20 to 17:12:36. Crawl 17:13:01 to 17:13:03 |
| Time, machine clock | US Eastern Daylight Time, UTC−4: 13:12 to 13:13 |
| Result | 2 titles in scope answered the query: **1 new version fetched**, 1 checked and unchanged. 39 out-of-scope titles counted and dropped |
| Size | 1 document, HTML unpacked from the register's epub |
| Validation | `scrape.py --validate manifest.csv`: 1 row, 0 errors, 0 warnings, contract 0.2.0 |
| Audit | `tools/audit_run.py`: 0 flagged, 0 missing |
| Status | **Usable.** The first run of the Australian update check, built the same day (decision 21) |
| Checked | `changes.json`, `links_used/catalogue_meta.json`, `manifest.jsonl`, `crawl_log.jsonl`, `audit.json` |

## Steps and times

| Step | UTC | Requests | Output |
| :---- | :---- | :---- | :---- |
| 1. Update check | 17:12:20 to 17:12:36 | 5 to the API host: `robots.txt` on both hosts, then one paged query per prefix (`C` for Acts, `F` for instruments) for versions registered since 2026-09-15, then one batched query for the changed title's record | `changes.json`, `changes.md`, `links_used/` (1 document) |
| 2. Crawl of the delta list | 17:13:01 to 17:13:03 | 1 document fetch at `REQUEST_DELAY_MS=10000` | `raw/`, `manifest.*`, `crawl_log.jsonl` |
| 3. Validate, audit, law table | 17:14 | none | `audit.md`, `audit.json`, `law_table.csv` |
| 4. Corpus | 17:14 | none | `outputs/AU/AU_corpus_2026-09-16` (1,277 documents, 1 superseded) |

## How it was run

- **Engine and scraper:** the sandbox copy `scratchpad\sbx2\p1-scrape` with `countries/au-australia/scraper/` and
  the new `updates/` installed as `adapters/au_legislation/` and its `updates/` subpackage.
- **Registry:** `countries/au-australia/sources.yaml` and `links/seed_laws.yaml`, fingerprint `f2e6cf88…`.
- **Baseline:** `AU_ws_2026-09-15`, whose list was built 2026-09-15T12:33:16Z. It lists 4,772 titles with their
  version ids and holds 1,277 stored documents.
- **Politeness:** `REQUEST_DELAY_MS=10000`, one request at a time, `robots.txt` read on both hosts first. The API
  publishes none; `www` asks for 10 s.
- **Commands** (from `<sandbox>`; `<ws>` the workshop, `<run>` this folder):

  ```
  PYTHONPATH=src python -m p1_scrape.adapters.au_legislation.updates --outputs <ws>/outputs/AU \
      --registry <ws>/countries/au-australia/sources.yaml --seeds <ws>/countries/au-australia/links/seed_laws.yaml
  REQUEST_DELAY_MS=10000 REGISTER_FRONTIER=links_file REGISTER_LINKS_FILE=<run>/links_used/documents.jsonl \
      python scrape.py --economy AU --scope all --out <run>
  python scrape.py --validate <run>/manifest.csv
  PYTHONPATH=src python tools/audit_run.py <run>
  PYTHONPATH=src python -m p1_scrape.adapters.au_legislation.checker <run>
  PYTHONPATH=src python tools/merge_corpus.py --outputs <ws>/outputs/AU --out <ws>/outputs/AU/AU_corpus_2026-09-16 --hardlink
  ```

  Every path above ran through the `subst` drive `R:` (`countries/au-australia/scraper/WORKFLOW.md`, step 3).

## What is in this folder

| Path | What it is |
| :---- | :---- |
| `RUN_NOTE.md` | This note |
| `changes.md`, `changes.json` | Everything the check found: the change fetched, the title checked and unchanged, and the 39 dropped with their series |
| `links_used/` | The delta list: 1 document, with `contract_meta.update` recording what changed and which document the baseline held |
| `manifest.csv`, `manifest.jsonl`, `crawl_log.jsonl`, `raw/`, `cost_report.json`, `crawl_status.json`, `.idmap.json` | The engine's output for the one document |
| `audit.md`, `audit.json`, `law_table.csv` | The content check and the law table for this run |
| `logs/crawl_stdout.log` | The crawl's console output |

## What is stored

One document: the Water Act 2007 as the compilation in force from 5 September 2026, fetched as the register's
dated epub and unpacked to HTML, 1 law, `use` `evidence`.

## What is missing

### Documents not downloaded

None. Everything in scope that changed was fetched.

### Not collected, by the settings

- **21 legislative instruments** registered since the baseline that this country does not collect. The harvest
  reads the Act collection and the seeded instruments only (decision 12). Their ids and names are in
  `changes.json` only as a count by series, not individually: the query returns them, the check drops them.
- **9 notices, 8 gazette notices, 1 bulletin**: not legislation.
- **New instruments made under an Act** (`<titleId>/latest/authorises` on the `www` host). The check does not
  read that page; it would cost one request per Act at 10 s.

### Missing details (metadata)

Nothing beyond what a crawl row normally lacks. The one row carries its version id, compilation number,
registration date and the amending instrument that caused the recompilation.

## Stored, but not what the row says

Nothing flagged.

## Issues encountered

1. **The first live run queued 31 documents that are out of scope.** The query returns every title in the `C` and
   `F` prefixes, and our baseline lists only the Act collection, so each new legislative instrument looked like a
   new law. The scope rule was added the same hour (`updates/diff.py`, `in_scope`): a title is in scope when the
   baseline already lists it, when it is a seed, or when it is an Act. That first folder was deleted and the check
   re-run; this folder is the corrected run. The rule is covered by a test.
2. **A title the baseline lists with no version id cannot be compared,** so it is fetched and the reason recorded
   in `contract_meta.update`. None occurred here; the case is covered by a test.

## Changes after the run

- **2026-09-16 17:14 UTC:** validated, audited, the law table written, and `outputs/AU/AU_corpus_2026-09-16` built
  from both runs, superseding the older Water Act copy.

## Decisions still open that affect this run

- **How often the check runs.** Three requests a time means it can run daily without any strain on the register.
- **Whether to read `authorises`** for new instruments under the seeded Acts, at one request per Act.
- **A rectification that does not change the register id** is invisible to the id test; only a content hash would
  catch it (`POLICY.md` section 6).
