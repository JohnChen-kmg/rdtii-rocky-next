# Workflow: crawling Laws of Malaysia with this scraper

How to run a full crawl of Malaysia, step by step. For what the website looks like and why the scraper is built
this way, read `../NOTES.md`. For fetching only what changed since the last run, read `../updates/WORKFLOW.md`.

Every command below is run from the **stage root** (the crawl engine's folder, `stages\p1-scrape` in the repo or a
sandbox copy of it) in Git Bash. `<ws>` is this stage, the folder holding `src/`, `tests/` and `handoff1/`.

## 0. Before you start

- **Politeness limits do not move:** 3 s between requests plus jitter, one request at a time, one process against
  `lom.agc.gov.my` at a time. Never run a list build while a crawl runs (`POLICY.md` section 5).
- **robots.txt** on lom answers HTTP 500. The crawl goes ahead only because `sources.yaml` says
  `lom.robots_5xx: allow` (decision 9). If robots.txt ever answers 200, its rules apply from then on.
- **Never write into an earlier run folder.** Every crawl gets a new folder under `<ws>\outputs\MY\`
  (`outputs/README.md`).
- **Do not edit the repo or the instrument.** Work on the copies here; hand them back later (`../../README.md`).

## 1. Install the scraper into the stage

The scraper lives here as a package; the engine expects it at `src/p1_scrape/adapters/my_gazette/`.

```
STAGE=<stage root>          # the repo's stages/p1-scrape, or a sandbox copy of it
WS=<ws>/countries/my-malaysia

# the scraper package (replaces the Round 1 single file my_gazette.py: delete that file)
mkdir -p $STAGE/src/p1_scrape/adapters/my_gazette/updates
cp $WS/scraper/*.py $STAGE/src/p1_scrape/adapters/my_gazette/
cp $WS/updates/*.py $STAGE/src/p1_scrape/adapters/my_gazette/updates/
cp $WS/updates/watchlist.tsv $STAGE/src/p1_scrape/adapters/my_gazette/updates/   # CONVENTIONS rule 11; not Python, so the line above leaves it behind
rm -f $STAGE/src/p1_scrape/adapters/my_gazette.py

# the registry: sources.yaml first, then the seed laws, into BOTH copies (the engine reads contracts\ first)
cat $WS/sources.yaml $WS/links/seed_laws.yaml > $STAGE/contracts/instrument/sources_my.yaml
cp $STAGE/contracts/instrument/sources_my.yaml $STAGE/instrument/sources_my.yaml

# the tests and their fixtures
cp $WS/tests/test_my_*.py $STAGE/tests/
mkdir -p $STAGE/tests/fixtures/my && cp $WS/tests/fixtures/* $STAGE/tests/fixtures/my/

# the audit and the corpus merge (steps 4 and 6), shared by every country
cp $WS/../../tools/audit_run.py $WS/../../tools/merge_corpus.py $STAGE/tools/
cp $WS/../../tools/test_tools.py $STAGE/tests/

# the one dependency the engine's requirements.txt does not list yet (a hand-back request)
python -m pip install cryptography==44.0.0
```

The scraper needs `cryptography` because lom's listings are encrypted. It is inside the block since 2026-09-22: a
workshop audit that built a clean sandbox from the block alone got **85 of 175 tests failing**, every one with
`No module named 'cryptography'`. With it installed, 175 of 175 pass.

Check the install without touching the website:

```
python -m pytest -q tests/test_my_lom.py tests/test_my_catalogue.py tests/test_my_updates.py
```

All 175 must pass (65 + 69 + 41 on 2026-09-16).

## 2. Build the link list (2 h 14 min under `timeline: all`, no documents)

The list says what the crawl will fetch. It is built first so it can be read and checked before anything is
downloaded.

```
PYTHONPATH=src python -m p1_scrape.adapters.my_gazette.catalogue \
    --registry $WS/sources.yaml \
    --seeds $WS/links/seed_laws.yaml \
    --out $WS/links
```

- **What it does:** reads robots.txt, both act listings (885 principal acts and 406 amendment rows on 2026-09-14)
  and the detail pages `lom.timeline` asks for: every act's under `all` (the convention since decision 17; 1,970
  paced requests at two hops per act, 2 h 14 min on 2026-09-15), or only the seed acts' and the title rule's under
  `rule` (226 requests, 15 minutes on 2026-09-14).
- **What it writes** into `links/`: `documents.jsonl` (every document to fetch, in crawl order, with every detail),
  `documents.csv` (the same for Excel), `laws.csv` (one row per listed act and why any has no document),
  `catalogue_meta.json` (settings, request count, robots.txt record, notes, the registry fingerprint) and
  `discovery_log.jsonl` (every request sent). `links/README.md` explains each file.
- **Read the console notes** before crawling. They say what was left out on purpose (subsidiary legislation
  outside the core acts; under `rule`, dates left empty for acts whose timeline was not read) and what could not be
  read.
- **After any change** to `sources.yaml` or `seed_laws.yaml`, rebuild the list. The crawl refuses a list built from
  a different registry.

## 3. Crawl the list into a new run folder

```
RUN=<ws>/outputs/MY/MY_ws_$(date -u +%F)        # add _2, _3 for a second run on the same day
mkdir -p $RUN && cp -r $WS/links $RUN/links_used  # keep the list the crawl read beside its output

LOM_FRONTIER=links_file LOM_LINKS_FILE=$RUN/links_used/documents.jsonl \
    python scrape.py --economy MY --scope all --out $RUN 2>&1 | tee $RUN/logs/crawl_stdout.log
```

- **Scope:** Malaysia crawls `all` (every act, decision 11). `--scope relevant` takes only the acts the title rule
  selects; with it also set `MAX_CANDIDATES_PER_ECONOMY=0`, or the engine keeps only the first 60.
- **Time:** the full crawl of 2026-09-14 took 1 h 34 min for 1,320 documents (624 MB).
- **Give `--out` an absolute path.** The crawl runs from the stage root, where a relative `outputs/…` would land.
- **Watch the console** for `XX` lines (a failed file; lom sometimes answers HTTP 500) and `WARNING` lines.
- **PowerShell** instead of Git Bash: `$env:LOM_FRONTIER="links_file"; $env:LOM_LINKS_FILE="…"; python scrape.py …`.

## 4. Check the result

```
python scrape.py --validate $RUN/manifest.csv       # must say 0 errors
```

Then compare the manifest with the list: every `source_url` in `manifest.jsonl` should be a `url` in
`links_used/documents.jsonl`, and `crawl_log.jsonl` lists every document with its outcome (`ok`, `duplicate`,
`failed`). The scratchpad script used on 2026-09-14 for this is described in the run note of `MY_ws_2026-09-14`.

**Audit what was stored.** The counts alone hide files that are not the law's text: repeal notices of one page,
another act's text behind an act's link, a Malay file behind an English link, scans with no text layer. The audit
reads the first two pages of every stored file and writes `audit.md` and `audit.json` into the run folder
(`<ws>/tools/README.md` lists the flags; the tools are copied into the stage's `tools/` first):

```
PYTHONPATH=src python tools/audit_run.py $RUN
```

On the 2026-09-14 crawl: 132 rows flagged, 116 of them a wrong or unreadable file (`../NOTES.md` 1.3). The files stay
as the portal served them; the flags travel with the rows (decision 17).

## 5. Write the run note

Copy `<ws>/outputs/RUN_NOTE_TEMPLATE.md` to `$RUN/RUN_NOTE.md` and fill it from the files: the times from
`crawl_status.json` and the logs, the counts from `manifest.jsonl` and `crawl_log.jsonl`, what is missing from
`links_used/laws.csv` against the manifest, the wrong files from `audit.md`, and the issues from the console log.
Add the run to `<ws>/outputs/MY/README.md`.

## 6. Write the law table

```
PYTHONPATH=src python -m p1_scrape.adapters.my_gazette.checker $RUN            # law_table.csv in the run folder
PYTHONPATH=src python -m p1_scrape.adapters.my_gazette.checker <corpus> --all  # the corpus, plus the laws it left out
```

One row per law, with what the portal says about its status and dates. It sends no request: every value is already
in the folder. `--all` adds the laws the portal lists that the run did not fetch. The columns and the two rules that
hold for every country are in `CONVENTIONS.md` section 2, step 7. **Read the module's docstring before using the
table for Malaysia:** the portal states a status for 133 of 1,291 laws, so most rows say `not stated`, and
`last_amended` is derived from the amendments in our own corpus, not from the portal.

## 7. Build the corpus (optional)

A run folder holds only what that run fetched. For one folder with the current text of every law, merge the runs
(decision 17: never into a run, always a new folder):

```
PYTHONPATH=src python tools/merge_corpus.py --outputs <ws>/outputs/MY --out <ws>/outputs/MY/MY_corpus_$(date -u +%F)
```

The newest run's copy of each law wins, older copies are listed in `superseded.jsonl`, the audit flags ride on the
rows, and the manifest is validated. `MY_corpus_2026-09-15` was built this way from the three crawls (1,316
documents). Read `CORPUS_NOTE.md` there.

## 8. Things that go wrong

| Symptom | Cause | What to do |
| :---- | :---- | :---- |
| `lom robots.txt answered HTTP 500; RFC 9309 treats that as full disallow` | `lom.robots_5xx` is not `allow` in the registry the engine read | Check both registry copies were rebuilt (step 1). Never set it from the environment: the scraper ignores that on purpose |
| `link file … was built from a different registry` | `sources.yaml` or `seed_laws.yaml` changed after the list was built | Rebuild the list (step 2) |
| `link file … carries no registry fingerprint` | The list was built by the scraper from before 2026-09-14 | Served with a warning only; rebuild when convenient |
| `LOM UNAVAILABLE` | lom could not be read (network, a changed page format, three throttled answers) | Only seeds outside lom are fetched. Stop, read the message, rerun later |
| `scope relevant holds N candidates; the engine keeps the first 60` | The engine's default cap | `MAX_CANDIDATES_PER_ECONOMY=0` |
| `XX … (HTTP 500)` on a file | lom fails to serve that file | Recorded as `failed` in the crawl log. An update check later reports it as `not_stored` and fetches it again |
| A file path longer than 259 characters fails to write | Windows path limit; long paths are off on this machine | Keep `outputs\` at a short path (the longest path in `MY_ws_2026-09-14` is 249 characters) |

## 9. What the settings mean (`sources.yaml`, block `lom:`)

| Setting | Value today | Meaning |
| :---- | :---- | :---- |
| `document_languages` | `[eng, msa]` | English first when the portal has it, Malay only otherwise (decision 14) |
| `timeline` | `all` | Whose detail pages are read. `all`, the convention since decision 17: every act's, so every document carries its dates and amendment links (about 1.8 hours more than `rule`, once per list build). `rule` reads only the seeds and the acts the title rule selects |
| `subsidiary_acts`, `subsidiary_series` | `core`, `["P.U. (A)"]` | Regulations fetched for the core pillar 6 and 7 acts only (decision 12, confirmed by decision 17) |
| `listing_page_size` | 500 | Records per listing request |
| `frontier` | `discover` | The default: read the portal during the crawl. `links_file` replays a list (step 3 sets it in the environment) |
| `robots_5xx` | `allow` | Decision 9 |

The title rule (`title_rule:`) decides which acts count as relevant. It is data, derived from the instrument's
pillar 6 and 7 definitions, never from the gold set (`POLICY.md` section 4).
