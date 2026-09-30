# Workflow: fetching only what changed since the last run (Australia)

**Built and run 2026-09-16** (decision 21), in the shape Malaysia's has (`../../my-malaysia/updates/WORKFLOW.md`,
decision 16). A check reads the register's API, compares what it returns with the last run, writes a delta list,
and the ordinary crawl replays that list into the same run folder.

**It is cheap.** The whole statute book is checked in **three requests**, because the register states version
identity: every version carries a `registerId`, and a title whose id differs from the one we recorded has a new
text. No document is fetched to find that out. The first live check, 16 September 2026, found one changed law
(the Water Act 2007) out of 4,772 titles.

Every command is run from the **stage root** in Git Bash, through the `subst` drive (`../scraper/WORKFLOW.md`,
step 3). `<ws>` is this workshop.

## 0. Before you start

- **Politeness:** `REQUEST_DELAY_MS=10000`, the `www` host's `Crawl-delay`. The API host publishes no robots.txt,
  and the check reads both files before it queries anything.
- **No crawl against either host at the same time.**
- The scraper package must be installed with its `updates/` subpackage (`../scraper/WORKFLOW.md`, step 1, plus
  `cp $WS/updates/*.py $STAGE/src/p1_scrape/adapters/au_legislation/updates/`).

## 1. Run the check

```
RUN_OUT=<ws>/outputs/AU
PYTHONPATH=src python -m p1_scrape.adapters.au_legislation.updates \
    --outputs R:/outputs/AU \
    --registry $WS/sources.yaml --seeds $WS/links/seed_laws.yaml
```

- **The baseline** is the newest run under `--outputs` that has a `links_used/laws.csv`, because that file carries
  every title's `version_id`. `--baseline <run>` pins one instead.
- **The period** starts the day the baseline's list was built, unless `--since YYYY-MM-DD` says otherwise.
- **The run folder** is `<outputs>/AU_ws_<since>_to_<today>`, with `_2`, `_3` when the name is taken, unless
  `--out` says otherwise. It is created even when nothing changed: the check itself is the record.

## 2. What the check reads, and what it costs

| What | Where | Requests |
| :---- | :---- | ----: |
| robots.txt on both hosts | `api.prod.legislation.gov.au`, `www.legislation.gov.au` | 2, once per run |
| Every latest version registered since `<since>` | `/v1/versions?$filter=isLatest eq true and registeredAt ge <since> and startswith(titleId,'<prefix>')&$orderby=registeredAt`, 100 a page, once per prefix (`C` Acts, `F` instruments) | 1 per page, usually 1 each |
| The `Title` record of anything that changed | `/v1/titles?$filter=id in (…)`, 18 ids a query | 1 per 18 changed titles |

**Order every paged query.** The API's `$skip` pages overlap when unordered; that cost a rebuild on 2026-09-15.
**Query by registration date, not by the version's start date:** the register lags, and 46 of the 73 new versions
found on 2026-09-13 had started before Round 1's crawl ran.

## 3. What it decides

| Verdict | When | Fetched? |
| :---- | :---- | :---- |
| `new_version` | The baseline lists the title and its `version_id` differs, or the baseline recorded none | Yes |
| `new_title` | The title is in scope and the baseline never listed it | Yes |
| `unchanged` | The register re-registered the version we already hold | No, recorded |
| `repealed` | The title's status is no longer `InForce` | No, recorded |
| dropped | Out of scope: see below | No, counted by series |

**Scope, and why it matters.** The register registers hundreds of legislative instruments a month, and the
harvest reads the **Act collection plus the seeded instruments** (decision 12). So a title is in scope when the
baseline already lists it, when it is a seed, or when it is an Act; everything else is counted and dropped, by
series, in `changes.json`. Without that rule the first live check queued 31 out-of-scope instruments
(`outputs/AU/AU_ws_2026-09-15_to_2026-09-16/RUN_NOTE.md`, issue 1). Gazette notices, bills and administrative
notices are never in scope.

## 4. What it writes

| File | What it holds |
| :---- | :---- |
| `changes.json` | Every title the query returned in scope, with its verdict, both version ids, the dates, and what the baseline stored for it; plus the dropped counts and the request count |
| `changes.md` | The same, to read: a table of the changes, a table of what was checked and unchanged, and the notes |
| `links_used/documents.jsonl`, `documents.csv` | The delta list, built by the same adapter code the full list uses. Each row's `contract_meta.update` says what changed, the baseline's version id and the document it stored |
| `links_used/laws.csv`, `catalogue_meta.json`, `discovery_log.jsonl` | The changed titles, the settings and fingerprint, and every request the check sent |

## 5. Crawl the delta list

The check prints the command. It is the ordinary crawl pointed at the delta list and the same run folder:

```
REQUEST_DELAY_MS=10000 REGISTER_FRONTIER=links_file \
    REGISTER_LINKS_FILE=R:/outputs/AU/AU_ws_<since>_to_<date>/links_used/documents.jsonl \
    python scrape.py --economy AU --scope all --out R:/outputs/AU/AU_ws_<since>_to_<date>
```

Then steps 4 to 7 of `../scraper/WORKFLOW.md`: validate, audit, law table, run note, and the corpus when the run
should reach downstream.

## 6. What the check does not cover

Each is recorded rather than silently skipped, and each is a decision rather than a defect:

- **New instruments made under an Act.** `www.legislation.gov.au/<titleId>/latest/authorises` lists them, at one
  request per Act at the 10-second delay. The check sees a new instrument only when it is itself a title the
  query returns and is in scope.
- **A rectification that does not change the register id.** The register does correct documents in place. Only a
  content hash would catch that (`POLICY.md` section 6, test three).
- **A title that stops being returned at all.** A repeal shows here while the API still returns the title with a
  status other than `InForce`. One that disappears is caught by the next full list build.

## 7. Things that go wrong

| Symptom | Cause | What to do |
| :---- | :---- | :---- |
| `no date to check from` | The baseline has no list, or `--outputs` points at an empty folder | Pass `--since YYYY-MM-DD`, or point at a run with `links_used/laws.csv` |
| The portal refuses (HTTP 403, 429, 467, 503, or a WAF challenge) | Its anti-scraping mechanism | Nothing to do: the client rests (1, 5, then 30 min), halves its speed each time and carries on (decision 23). It stops only after six refusals in a row; then rest for hours and run once more |
| `the register could not be read` (exit 2) | The API answered an error that is not a refusal, or refused six times in a row | Nothing is written. Try later; the register is usually back within minutes |
| A title is fetched although nothing changed | The baseline lists it with no `version_id` | Expected: it cannot be compared, so it is fetched and `contract_meta.update` says why |
| Many `new_title` rows for instruments | The scope rule is not in force (a stale copy of `diff.py`) | Reinstall `updates/`; `in_scope` keeps Acts, seeds and titles the baseline lists |
| `stopped at N pages` in the notes | More changes than the paging cap | Rerun with a later `--since`, or raise the cap in `query.py` |
