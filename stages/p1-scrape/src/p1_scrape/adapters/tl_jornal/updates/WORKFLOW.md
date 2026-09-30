# Workflow: fetching only what the gazette published since the last run (Timor-Leste)

**Built 2026-09-20**, in the shape Malaysia's, Singapore's and Australia's checks have. A check costs **seven
requests** — robots.txt and the six category pages — because each page carries its kind's whole history, so
"what changed" is a comparison, not a search.

Every command runs from the **stage root** in Git Bash. `<ws>` is this workshop; `$WS` is this country folder.

## 0. Before you start

- **Politeness:** `REQUEST_DELAY_MS=10000`, the delay the portal's robots.txt states. The check reads robots first
  and adopts it.
- **No crawl against `www.mj.gov.tl` at the same time.**
- The scraper package must be installed with its `updates/` subpackage (`../scraper/WORKFLOW.md`, step 1).

## 1. Run the check

```
REQUEST_DELAY_MS=10000 PYTHONPATH=src python -m p1_scrape.adapters.tl_jornal.updates \
    --outputs R:/outputs/TL \
    --registry $WS/sources.yaml --seeds $WS/links/seed_laws.yaml
```

- **The baseline** is the newest run under `--outputs` that has a `links_used/laws.csv`; `--baseline <run>` pins
  one instead.
- **The date** is the day the baseline's list was built, unless `--since YYYY-MM-DD` says otherwise. With a date
  and no baseline, an act counts as new when the portal publishes it on or after that date.
- **`--out`** names the run folder; without it the check writes `<outputs>/TL_ws_<since>_to_<today>`. One of
  `--outputs` or `--out` is required, so a run folder never lands in the current directory.
- **The run folder is created even when nothing changed:** the check itself is the record.

## 2. What it reads, and what it costs

| What | Requests |
| :---- | ----: |
| robots.txt | 1 |
| The six category pages | 6 |
| Documents, to find out what changed | **0** |

**Seven requests, about a minute.** No detail page exists, no timeline has to be read, and no API is involved.

## 3. How it decides

The gazette is **append-only**: it publishes acts and never revises an issue, and it states no status anywhere.

| Found | Verdict | Fetched? |
| :---- | :---- | :---- |
| An act the baseline never listed | `new_act` | Yes — unless we already hold its issue, and then the note says so |
| An act we listed whose issue no run stored | `not_stored` | Yes |
| An act we listed that now points at a different file | `document_moved` | Yes, keeping the old address in the row |
| An act the baseline listed that the portal no longer lists | `delisted` | **No: reported** |
| Everything else | `unchanged` | No |

**There is no `amended` verdict, and that is correct here.** An amending act is a *new act* whose title names the
act it alters ("Primeira alteração ao Decreto-Lei n.º 15/2012"), and the linkage is written into
`contract_meta.principal_law_number`. The text of the act it amends never changes on the portal.

**An issue is fetched once** however many acts point at it: `to_fetch` is deduplicated by document address.

## 4. What it writes

| File | What it holds |
| :---- | :---- |
| `changes.json`, `changes.md` | Every verdict above, with the dates, the old and new addresses, and the notes |
| `links_used/documents.jsonl`, `documents.csv` | The delta list: the issues to fetch, built by the adapter's own builder, each row's `contract_meta.update` saying what changed and what the baseline held |
| `links_used/laws.csv` | **Every act the portal lists today**, not only the changed ones, so this run folder is a complete baseline for the next check |
| `links_used/catalogue_meta.json`, `discovery_log.jsonl` | The settings the run used, the registry fingerprint, and all seven requests |

## 5. Crawl the delta list

The check prints the command:

```
REQUEST_DELAY_MS=10000 JORNAL_FRONTIER=links_file \
    JORNAL_LINKS_FILE=R:/outputs/TL/TL_ws_<since>_to_<date>/links_used/documents.jsonl \
    python scrape.py --economy TL --scope all --out R:/outputs/TL/TL_ws_<since>_to_<date>
```

Then steps 4 to 7 of `../scraper/WORKFLOW.md`: validate, audit, law table, run note, and the corpus when the run
should reach downstream.

## 6. What it cannot see

- **A correction inside an issue.** If the ministry replaces a PDF at the same address, nothing in the listing
  changes and the check will not notice. Only a content hash would, which is `POLICY.md` section 6, test three.
- **An act published without a listing row.** The check trusts the six category pages; an act that never appears
  on one is invisible to it, as it is to the list build.
- **Anything about force or repeal**, because the portal states nothing. A repeal is visible only as a later act
  whose title says so.

## 7. Things that go wrong

| Symptom | Cause | What to do |
| :---- | :---- | :---- |
| `no date to check from` | No run with a list under `--outputs` | Pass `--since`, or build a list first (`../scraper/WORKFLOW.md`, step 2) |
| `--out is needed when there is no --outputs folder` | `--baseline` alone says what to compare with, not where to write | Give `--out` or `--outputs` |
| `the gazette could not be read` (exit 2) | A category page failed, or robots.txt answered 5xx | Nothing is written. Try later |
| `<run> already holds a run` (exit 2) | `--out` points at a folder with a manifest | Give a new `--out` (`outputs/README.md` rule 1) |
| Many `not_stored` | The baseline listed acts whose issues a crawl never fetched | Expected after a partial crawl: the check queues them |
| `delisted` rows | The portal reorganised a category page | Read them: the copy we hold is unaffected, but the portal's own listing changed |

## 8. What the settings mean

The check reads the same `jornal:` block as the list build (`../scraper/WORKFLOW.md`, section 9); it has no
settings of its own. `--pillars` (default `6,7`) decides which seeds count, and a seed with no indicator tag is
always kept.
