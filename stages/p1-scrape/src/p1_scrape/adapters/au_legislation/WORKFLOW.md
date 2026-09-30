# Workflow: crawling the Federal Register of Legislation with this scraper

How to run a full crawl of Australia, step by step, in the shape every country follows (`CONVENTIONS.md` section 2).
For what the register looks like and why the scraper is built this way, read `../NOTES.md`. For fetching only what
changed, read `../updates/WORKFLOW.md` (not developed yet).

**Status, 2026-09-15:** the catalogue step exists and was run live (decision 18); the first crawl from its list was
started the same day into `outputs/AU/AU_ws_2026-09-15/`. The update check is a stub.

Every command is run from the **stage root** (`stages\p1-scrape` in the repo or a sandbox copy) in Git Bash. `<ws>`
is this stage, the folder holding `src/`, `tests/` and `handoff1/`. In the development
workshop it was a `countries/<cc>-<name>/` folder; in this repository the adapter, its tests and
its evidence all live under `stages/p1-scrape/`.

## 0. Before you start

- **Two hosts, two delays:** `www.legislation.gov.au` at **10 s** between requests (`Crawl-delay: 10`, read live
  2026-09-13 and 2026-09-15; `/assets/` disallowed); `api.prod.legislation.gov.au` at the default 3 s plus jitter
  (no robots.txt: HTTP 404). One request at a time per host.
- **The catalogue step never touches `www`** except for its robots.txt; the crawl fetches every document from `www`.
- **The engine's limiter has one delay for every host** (`REQUEST_DELAY_MS`, default 3000): the crawl must run with
  `REQUEST_DELAY_MS=10000`. The links-file frontier warns when it is lower.
- **Never write into an earlier run folder.** Every crawl gets a new folder under `<ws>\outputs\AU\`.
- **Do not edit the repo or the instrument.** Work on the copies here; hand them back later.

## 1. Install the scraper into the stage

The scraper is a package; the engine expects it at `src/p1_scrape/adapters/au_legislation/` (it replaces the Round 1
module `au_legislation.py`, which must go).

```
STAGE=<stage root>
WS=<ws>/countries/au-australia

rm -f $STAGE/src/p1_scrape/adapters/au_legislation.py
mkdir -p $STAGE/src/p1_scrape/adapters/au_legislation
cp $WS/scraper/*.py $STAGE/src/p1_scrape/adapters/au_legislation/
mkdir -p $STAGE/src/p1_scrape/adapters/au_legislation/updates
cp $WS/updates/*.py $STAGE/src/p1_scrape/adapters/au_legislation/updates/
cp $WS/updates/watchlist.tsv $STAGE/src/p1_scrape/adapters/au_legislation/updates/   # CONVENTIONS rule 11; not Python, so the line above leaves it behind

# the registry: sources.yaml first, then the seed laws, into BOTH copies (the engine reads contracts\ first)
cat $WS/sources.yaml $WS/links/seed_laws.yaml > $STAGE/contracts/instrument/sources_au.yaml
cp $STAGE/contracts/instrument/sources_au.yaml $STAGE/instrument/sources_au.yaml

# the tests and their fixtures; the audit and the corpus merge, shared by every country
cp $WS/tests/test_au_*.py $STAGE/tests/
mkdir -p $STAGE/tests/fixtures/au && cp $WS/tests/fixtures/* $STAGE/tests/fixtures/au/
cp $WS/../../tools/audit_run.py $WS/../../tools/merge_corpus.py $STAGE/tools/
```

The package imports the paced client and the robots.txt rules from Malaysia's package (`..my_gazette.client`,
`..my_gazette.robots`), so Malaysia's package must be installed too (`../../my-malaysia/scraper/WORKFLOW.md`, step 1).

Check the install without touching the register:

```
python -m pytest -q tests/test_au_register.py tests/test_au_multivolume.py tests/test_au_updates.py
```

All 32 must pass (12 + 9 + 11 on 2026-09-19). All three files, always: until 2026-09-19 this step named only the first two, so the update check's tests never ran in the stage.

## 2. Build the link list (about 9 minutes, no documents)

```
PYTHONPATH=src python -m p1_scrape.adapters.au_legislation.catalogue \
    --registry $WS/sources.yaml \
    --seeds $WS/links/seed_laws.yaml \
    --out $WS/links
```

- **What it does:** reads both robots.txt files, every in-force title of the `Act` collection from the API (48 pages
  of 100, `$orderby=id`: 4,765 titles on 2026-09-15, 1,264 of them principal), the latest version of every
  principal act and of every seed in batches of 18 (its start date, register id, compilation number and the
  amendments it incorporates), and the seeds' own titles. 121 API requests at 3.0 to 4.5 s and 1 `www` request on
  2026-09-15, about 9 minutes.
- **What it writes** into `links/`: `documents.jsonl`, `documents.csv`, `laws.csv` (every harvested title, principal
  or not), `catalogue_meta.json`, `discovery_log.jsonl`. `links/README.md` explains each file.
- **The document form** is set by `register.document_form` (`epub`: every compilation's dated epub, every volume;
  `pdf`: the dated PDF, single-volume acts only). An as-made title gets its as-made PDF either way; a `form: html`
  seed that is as-made keeps Round 1's framed capture (`../NOTES.md` 1.2).
- **After any change** to `sources.yaml` or `seed_laws.yaml`, rebuild the list. The crawl refuses a list built from
  a different registry.

## 3. Crawl the list into a new run folder (about 4 hours)

```
RUN=<ws>/outputs/AU/AU_ws_$(date -u +%F)        # add _2, _3 for a second run on the same day
mkdir -p $RUN/logs && cp -r $WS/links $RUN/links_used

REQUEST_DELAY_MS=10000 REGISTER_FRONTIER=links_file REGISTER_LINKS_FILE=$RUN/links_used/documents.jsonl \
    python scrape.py --economy AU --scope all --out $RUN 2>&1 | tee $RUN/logs/crawl_stdout.log
```

- **Scope:** `all` takes every row (1,277 on 2026-09-15); `relevant` the seeds and the acts the title net selects;
  `seed` the 20 seeds.
- **Time:** 1,277 documents at 10 s plus jitter and download: about 4 hours.
- **Forms:** the row's address decides: a dated epub is fetched by `requests` and its spine concatenated into HTML
  (`unpack: epub_html`, every volume, or a loud failure); a PDF by `requests`; a `/latest/text` address by a
  Playwright capture of the viewer's frame that rejects a multi-volume act (Round 1's guard).
- **Give `--out` an absolute path.** The crawl runs from the stage root.
- **Give `--out` a short path.** The engine names each document's folder after the whole law name; one title in
  the list of 2026-09-15 pushes the path past Windows' 260-character limit under `<ws>\outputs\AU\...` and its
  store fails (`../NOTES.md` 1.3). Map the workshop to a drive letter first (`subst R: <ws>` in PowerShell, once
  per logon; `subst R: /D` removes it) and pass `--out R:/outputs/AU/AU_ws_<date>`. The files land in the same
  folder; the manifest's paths are relative and do not change.
- **Resume:** the same command with the same `--out` continues a stopped run; the engine skips what the manifest
  already holds. A crawl killed from outside loses the documents stored since its last checkpoint (one every 10):
  their files stay under `raw/` without a row (`orphan_file` in the audit) and the resume fetches them again.

## 4. Check the result

```
python scrape.py --validate $RUN/manifest.csv       # must say 0 errors
PYTHONPATH=src python tools/audit_run.py $RUN       # audit.md, audit.json in the run folder
```

The audit applies its generic flags (`<ws>/tools/README.md`); there is no `AU` rule set yet. Epub-derived HTML and
framed captures are HTML documents by design, so no HTML flag applies to Australia.

## 5. Write the run note

Copy `<ws>/outputs/RUN_NOTE_TEMPLATE.md` to `$RUN/RUN_NOTE.md` and fill it from the files. Add the run to
`<ws>/outputs/AU/README.md`.

## 6. Write the law table

```
PYTHONPATH=src python -m p1_scrape.adapters.au_legislation.checker $RUN            # law_table.csv in the run folder
PYTHONPATH=src python -m p1_scrape.adapters.au_legislation.checker <corpus> --all  # the corpus, plus the laws it left out
```

One row per law, with what the portal says about its status and dates (the compilation's start and end, the last amending Act, the enactment date). It sends no request: every value
is already in the folder. `--all` adds the laws the portal lists that the run did not fetch. The columns and the
two rules that hold for every country are in `CONVENTIONS.md` section 2, step 7; what the dates mean here is in
the module's own docstring.

## 7. Build the corpus (optional)

```
PYTHONPATH=src python tools/merge_corpus.py --outputs <ws>/outputs/AU --out <ws>/outputs/AU/AU_corpus_$(date -u +%F)
```

## 8. Things that go wrong

| Symptom | Cause | What to do |
| :---- | :---- | :---- |
| The harvest note says titles came back more than once | The API's `$skip` pages overlap when unordered | The query orders by id since 2026-09-15; if it recurs, rebuild |
| HTTP 405 on a `/text/original/pdf` address | A multi-volume compilation has no single PDF | Use `document_form: epub` (the default), or fetch that act's epub |
| `link file … was built from a different registry` | `sources.yaml` or the seeds changed after the build | Rebuild the list (step 2) |
| `the engine waits 3.0 s … set REQUEST_DELAY_MS=10000` | The crawl was started without the delay | Stop and restart with `REQUEST_DELAY_MS=10000` |
| An OR-chain of title ids returns 400 | An API node-count limit | `titleId in (...)` with at most 18 ids (the setting `version_batch`) |
| A datetime filter returns 400 | A trailing `Z` on the literal | Drop the `Z` (`api.versions_since_url` does) |
| `REGISTER UNAVAILABLE` at the crawl | `www`'s robots.txt could not be read | Register rows are dropped for that run; rerun later |
| `store FileNotFoundError` in the crawl log, HTTP 200 | The document's path is over Windows' 260-character limit (a long title) | Run with `--out` on a `subst` drive (step 3); `store_failed` in the audit lists the documents |

## 9. What the settings mean (`sources.yaml`, block `register:`)

| Setting | Value today | Meaning |
| :---- | :---- | :---- |
| `api` | `https://api.prod.legislation.gov.au/v1` | The OData API the catalogue reads |
| `detail_pages` | `all` | Whose latest version is read: every principal act (decision 17); `seed` reads the seeds' only; `none` reads none |
| `version_batch` | 18 | Title ids per versions request |
| `title_page_size` | 100 | The API's maximum `$top` |
| `max_titles` | 6000 | A stop on the harvest |
| `collection` | `Act` | The collection harvested, in force |
| `document_form` | `epub` | The form fetched for a compilation (decision 18, proposed); `pdf` is the alternative |
| `frontier` | `discover` | The default; `links_file` replays a list (step 3 sets it in the environment with `REGISTER_LINKS_FILE`) |

Every key can be overridden by `REGISTER_<KEY>` in the environment. The title net (`seed_queries`, legacy
`P6-I1` … `P7-I5` keys: do not re-tag) decides which acts count as relevant.
