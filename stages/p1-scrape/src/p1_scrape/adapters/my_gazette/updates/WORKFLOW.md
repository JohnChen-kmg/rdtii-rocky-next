# Workflow: fetching only what changed since the last run

How to run the update check for Malaysia, step by step. The check asks the website what has been published since
the date of the last run and fetches only that; for the main acts, which carry no upload date, it compares today's
list of acts with the list saved from the last run. Why it works this way: `../NOTES.md` section 2.6 and decision 16.

Every command is run from the **stage root** (see `../scraper/WORKFLOW.md`, step 1, for installing the scraper and
this package there). `<ws>` is this stage, the folder holding `src/`, `tests/` and `handoff1/`.

## 1. What you need

- A previous run under `<ws>\outputs\MY\` to compare with. The newest is used by default. A run folder counts when it
  holds `links_used\laws.csv` (or `links_rebuilt\laws.csv`) and, for the stored documents, `manifest.jsonl`.
- No crawl running against lom at the same time.

## 2. Run the check (about a minute, no documents)

```
WS=<ws>/countries/my-malaysia
PYTHONPATH=src python -m p1_scrape.adapters.my_gazette.updates \
    --outputs <ws>/outputs/MY \
    --registry $WS/sources.yaml \
    --seeds $WS/links/seed_laws.yaml
```

- **What it does:** 8 paced requests: robots.txt, both act listings whole, and the newest page of the P.U. (A) and
  of the P.U. (B) listing. More requests only when an act changed (its detail page is read) or a P.U. listing needs a
  second page. No document is fetched.
- **"Since"** is the day the newest run started. Give `--since YYYY-MM-DD` to use another date.
- **Where it writes:** a new run folder beside the crawls, `<ws>\outputs\MY\MY_ws_<since>_to_<today>`, named for the
  period the check covers (`_2`, `_3` on a second run of that name the same day),
  holding `changes.md` and `changes.json` (every change found, fetched or not, with the reason) and `links_used\`
  (the delta list: only the documents to fetch, in the format the crawl replays; `laws.csv` says for every act
  "unchanged since <run>" or what changed). `--out <folder>` names the folder instead; an existing run folder is
  refused.
- **Exit code 2** and nothing written when lom could not be read, served an incomplete listing, or the `--out`
  folder already holds a run.

The console ends with the number of documents to crawl and the exact crawl command.

**After a list rebuild, add `--list`:** the listings cannot show the amendments and commencement orders only a
timeline reveals, so a list rebuilt with `lom.timeline: all` holds documents no run stored. `--list
$WS/links/documents.jsonl` compares that list with every run before any request (a list built from another
registry is refused) and puts every row no run stored on the delta list as `not_in_runs`; a row whose title a run
stored from another address is `stored_elsewhere`, recorded only. On 2026-09-15 that was 98 documents to fetch,
75 stored (`outputs/MY/MY_ws_2026-09-15_to_2026-09-15`).

## 3. Read `changes.md`

| Change | Meaning | Fetched? |
| :---- | :---- | :---- |
| `new_act`, `new_amending_act`, `new_instrument` | Not in the last run's list | Yes (an instrument only when it is under a core act, or a commencement order an amending act cites under the timeline rule, or a seed names it) |
| `new_version` | The act's file or "As At" date changed | Yes, with its later amendments and, for core acts, its regulations |
| `not_stored` | The list is unchanged but no run stored the file (a failed fetch, like the 4 HTTP 500 files of 2026-09-14) | Yes |
| `status_changed`, `listing_changed`, `commencement_changed` | Only the marker, the title, the documents offered or the commencement remark changed; the file is the one already stored | No |
| `gone` | An act the last run listed is no longer listed | No |
| `stored_file_changed` | `--verify-stored`: a stored file answered "changed" | Yes |
| `not_in_runs` | `--list`: the link list holds the document and no run stored it | Yes |
| `stored_elsewhere` | `--list`: the same title is stored from another address (an agency's copy of a seed) | No |

If the count of documents to crawl is 0, stop here: the run folder is the record of the check. Write its
`RUN_NOTE.md` (step 5) and add it to `<ws>\outputs\MY\README.md`.

## 4. Crawl the delta list into the same run folder

```
RUN=<ws>/outputs/MY/MY_ws_<since>_to_<date>    # the folder the check wrote
LOM_FRONTIER=links_file LOM_LINKS_FILE=$RUN/links_used/documents.jsonl \
    python scrape.py --economy MY --scope all --out $RUN 2>&1 | tee $RUN/logs/crawl_stdout.log
python scrape.py --validate $RUN/manifest.csv
PYTHONPATH=src python tools/audit_run.py $RUN        # audit.md: files that are not the law's text
```

The check and its crawl are one run: this is the one time a crawl writes into a folder that already exists
(`outputs/README.md`, rule 1). Every stored row's `contract_meta.update` (in `links_used\documents.jsonl`) says what
changed, why, and which document the earlier run held for the same law.

## 5. Write the run note

From `<ws>/outputs/RUN_NOTE_TEMPLATE.md`: the times from `links_used\discovery_log.jsonl` and `crawl_status.json`,
the changes from `changes.md`, what was fetched from `manifest.jsonl`, the wrong files from `audit.md`. The note of
`MY_ws_2026-09-14_to_2026-09-14` is the example of a check that fetched nothing; `MY_ws_2026-09-14_to_2026-09-15` of
one that crawled.

**Then, when a corpus is wanted:** the delta run holds only what it fetched. `tools/merge_corpus.py` builds a new
folder with the newest copy of every law across the runs (`../scraper/WORKFLOW.md`, step 6; decision 17). Never
merge into a run.

## 6. Checking stored files (optional)

The listing cannot show a file replaced behind the same path with the same "As At" date. It happens: Act 869's
file changed on 21 August 2026 with its listing entry untouched. To catch that:

```
... updates --outputs <ws>/outputs/MY --registry ... --seeds ... --verify-stored 200
```

sends one conditional HEAD per stored lom file, newest first, 200 of them here (one request each, no body):
304 means unchanged; 200 with other validators means changed, and the file goes onto the delta list as
`stored_file_changed`. All 1,297 lom files would take about an hour and a half. Off by default.

## 7. Settings (`sources.yaml`, block `updates:`)

| Setting | Value today | Meaning |
| :---- | :---- | :---- |
| `subsidiary_listings` | P.U. (A) and P.U. (B) pages and endpoint | Where the instrument listings are |
| `subsidiary_page_size` | 500 | Records per request, newest first |
| `subsidiary_lookback_days` | 120 | Read the listings back this far before the date: an instrument can be uploaded months after its publication date |
| `subsidiary_max_pages` | 30 | A check further back than that says so and stops |
| `verify_stored` | 0 | The default for `--verify-stored` |

The block is outside the link-list fingerprint: changing it does not invalidate a list. Which acts' detail pages are
read and whose regulations are fetched follow the scraper's own settings (`lom.timeline`, `lom.subsidiary_acts`).

## 8. Things that go wrong

| Symptom | What to do |
| :---- | :---- |
| `lom could not be read, nothing written (LomUnavailable: lom served an incomplete listing …)` | The portal served fewer records than it claims; a comparison would call the missing acts "gone". Rerun later |
| `… already holds a check or a crawl` | Give a new `--out`, or omit it to get the next free folder name |
| `an update check needs a baseline run or --since` | No run under `--outputs`: give `--since YYYY-MM-DD` (date mode, approximate for acts) |
| Many `new_instrument` rows, none fetched | Expected: instruments under acts outside the core groups are recorded only (decision 12). Widen `lom.subsidiary_acts` to fetch more |
| The same `gone` or `status_changed` rows on every check | Expected until a crawl updates the listing state: only a run with a `laws.csv` becomes the new baseline, and a check writes one |
