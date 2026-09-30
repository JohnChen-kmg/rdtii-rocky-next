# Workflow: crawling Singapore Statutes Online with this scraper

How to run a full crawl of Singapore, step by step, in the shape every country follows (`CONVENTIONS.md` section 2).
For what the website looks like and why the scraper is built this way, read `../NOTES.md`. For fetching only what
changed, read `../updates/WORKFLOW.md` (not developed yet).

**Status, 2026-09-15:** the catalogue step exists and was run live once (decision 18); the update check is a stub.
**From 13:00 UTC the portal's edge answered every request from our plain client with a WAF challenge** (HTTP 202,
`x-amzn-waf-action: challenge`; `../NOTES.md` 1.3); it lifted after an hour's silence, and the first crawl ran from
the list from 14:09 UTC. The adapter stops at once on that answer; a rebuild of the list waits for a quieter day.
`../NOTES.md` section 3 says which runs exist under `outputs/SG/`.

Every command is run from the **stage root** (the crawl engine's folder, `stages\p1-scrape` in the repo or a
sandbox copy of it) in Git Bash. `<ws>` is this stage, the folder holding `src/`, `tests/` and `handoff1/`.

## 0. Before you start

- **Politeness on `sso.agc.gov.sg`: 6 s between requests** (`Crawl-delay: 6`, read live 2026-09-13 and 2026-09-15),
  plus jitter, one request at a time. **Never request `/search`** (disallowed). The catalogue's client reads
  robots.txt first and raises its delay to the `Crawl-delay`.
- **The engine's limiter has one delay for every host** (`REQUEST_DELAY_MS`, default 3000): the crawl must run with
  `REQUEST_DELAY_MS=6000`. The links-file frontier warns when it is lower.
- **Never write into an earlier run folder.** Every crawl gets a new folder under `<ws>\outputs\SG\`
  (`outputs/README.md`).
- **Do not edit the repo or the instrument.** Work on the copies here; hand them back later.

## 1. Install the scraper into the stage

The scraper is a package; the engine expects it at `src/p1_scrape/adapters/sg_sso/` (it replaces the Round 1
module `sg_sso.py`, which must go).

```
STAGE=<stage root>
WS=<ws>/countries/sg-singapore

rm -f $STAGE/src/p1_scrape/adapters/sg_sso.py
mkdir -p $STAGE/src/p1_scrape/adapters/sg_sso
cp $WS/scraper/*.py $STAGE/src/p1_scrape/adapters/sg_sso/
mkdir -p $STAGE/src/p1_scrape/adapters/sg_sso/updates
cp $WS/updates/*.py $STAGE/src/p1_scrape/adapters/sg_sso/updates/
cp $WS/updates/watchlist.tsv $STAGE/src/p1_scrape/adapters/sg_sso/updates/   # CONVENTIONS rule 11; not Python, so the line above leaves it behind

# the registry: sources.yaml first, then the seed laws, into BOTH copies (the engine reads contracts\ first)
cat $WS/sources.yaml $WS/links/seed_laws.yaml > $STAGE/contracts/instrument/sources_sg.yaml
cp $STAGE/contracts/instrument/sources_sg.yaml $STAGE/instrument/sources_sg.yaml

# the tests and their fixtures; the audit and the corpus merge, shared by every country
cp $WS/tests/test_sg_*.py $STAGE/tests/
mkdir -p $STAGE/tests/fixtures/sg && cp $WS/tests/fixtures/* $STAGE/tests/fixtures/sg/
cp $WS/../../tools/audit_run.py $WS/../../tools/merge_corpus.py $STAGE/tools/
```

The package imports the paced client and the robots.txt rules from Malaysia's package (`..my_gazette.client`,
`..my_gazette.robots`), so Malaysia's package must be installed too (`../../my-malaysia/scraper/WORKFLOW.md`, step 1).

Check the install without touching the website:

```
python -m pytest -q tests/test_sg_sso.py tests/test_sg_updates.py
```

All 36 must pass (22 + 14 on 2026-09-19). Both files, always: until 2026-09-19 this step named only the first, so the update check's 14 tests never ran in the stage.

## 2. Build the link list (about an hour, no documents)

```
PYTHONPATH=src python -m p1_scrape.adapters.sg_sso.catalogue \
    --registry $WS/sources.yaml \
    --seeds $WS/links/seed_laws.yaml \
    --out $WS/links
```

- **What it does:** reads robots.txt, the Current listing 100 rows a page by its Next Page links (six pages, 525
  acts; until 2026-09-16 one 500-row page read ascending and descending, which the portal then refused), the Repealed (298) and Uncommenced (10) listings, the Acts Supplement of this year and
  last, **every current act's detail page** (its current version date, every version with its amending instrument,
  the original number, the revised edition) and the SL tab of the seed acts, page by page. About 540 requests at
  6 s or more: an hour. No document is downloaded.
- **What it writes** into `links/`: `documents.jsonl`, `documents.csv`, `laws.csv` (every listed act, in the four
  listings), `catalogue_meta.json` and `discovery_log.jsonl`. `links/README.md` explains each file.
- **Read the console notes** before crawling: acts whose page could not be read (their rows carry
  `amendment_check_incomplete`), SL tabs cut short, the Acts Supplement entries recorded only.
- **What goes in:** every current act as its PDF (`/Act/<CODE>?ViewType=Pdf`); every repealed act as its PDF (the
  page serves one even where the listing links none); the amending acts of the Acts Supplement as published, and
  a new principal act the Current listing does not carry yet; the SL of the seed acts; the seeds' own documents.
  Uncommenced acts are recorded only (their address changes daily).
- **After any change** to `sources.yaml` or `seed_laws.yaml`, rebuild the list. The crawl refuses a list built from
  a different registry.

## 3. Crawl the list into a new run folder (about 1.5 hours)

```
RUN=<ws>/outputs/SG/SG_ws_$(date -u +%F)        # add _2, _3 for a second run on the same day
mkdir -p $RUN/logs && cp -r $WS/links $RUN/links_used

REQUEST_DELAY_MS=6000 SSO_FRONTIER=links_file SSO_LINKS_FILE=$RUN/links_used/documents.jsonl \
    python scrape.py --economy SG --scope all --out $RUN 2>&1 | tee $RUN/logs/crawl_stdout.log
```

- **Scope:** `all` takes every row; `relevant` the seeds and the acts the title net selects; `seed` the seeds.
- **Forms:** with no `--forms`, scope `all` fetches only the PDF of each act (the row's address), as Round 1 did;
  `--forms both` adds a Playwright capture of `?WholeDoc=1` per act. The PDF alone carries the version footer and
  the legislative history.
- **Time:** at 6 to 9 s a document plus download, about 1.5 hours for 830 rows.
- **Give `--out` an absolute path.** The crawl runs from the stage root.
- **Give `--out` a short path.** The engine names each document's folder after the whole law name; two titles in
  the list of 2026-09-15 push the path past Windows' 260-character limit under `<ws>\outputs\SG\...` and their
  store fails (`../NOTES.md` 1.3). Map the workshop to a drive letter first (`subst R: <ws>` in PowerShell, once
  per logon; `subst R: /D` removes it) and pass `--out R:/outputs/SG/SG_ws_<date>`. The files land in the same
  folder; the manifest's paths are relative and do not change.
- **Let the engine stop itself.** On the WAF challenge (HTTP 202, empty body) it stops after 10 in a row, writing
  its manifest first. A crawl killed from outside loses every document stored since its last checkpoint (one every
  10 stored documents): the files stay under `raw/` without a manifest row (`orphan_file` in the audit) and the
  next resume fetches them again.
- **Resume:** the same command with the same `--out` continues a stopped run; the engine skips what the manifest
  already holds.

## 4. Check the result

```
python scrape.py --validate R:/outputs/SG/SG_ws_<date>/manifest.csv     # must say 0 errors
PYTHONPATH=src python tools/audit_run.py R:/outputs/SG/SG_ws_<date>     # audit.md, audit.json in the run folder
```

**Both through the `subst` drive, for the same reason the crawl uses it** (step 3): two Singaporean titles are long
enough that their files cannot be opened from the workshop path. Run from `<ws>` instead and the validation
reports a path that does not resolve, and the audit flags a readable file as `unreadable_file`.

The audit (`<ws>/tools/README.md`) applies its generic flags to Singapore: scans with no text layer, duplicate
bytes, failed fetches. Singapore rules (the short title on page 1 against the row, "REPEALED" markers, the Revised
Edition page) are not written yet; add them to `RULES["SG"]` in `tools/audit_run.py` with a test.

## 5. Write the run note

Copy `<ws>/outputs/RUN_NOTE_TEMPLATE.md` to `$RUN/RUN_NOTE.md` and fill it from the files (times from
`crawl_status.json` and the logs, counts from `manifest.jsonl` and `crawl_log.jsonl`, wrong files from `audit.md`).
Add the run to `<ws>/outputs/SG/README.md`.

## 6. Write the law table

```
PYTHONPATH=src python -m p1_scrape.adapters.sg_sso.checker $RUN            # law_table.csv in the run folder
PYTHONPATH=src python -m p1_scrape.adapters.sg_sso.checker <corpus> --all  # the corpus, plus the laws it left out
```

One row per law, with what the portal says about its status and dates (the version date, the last amending act, the repeal date). It sends no request: every value
is already in the folder. `--all` adds the laws the portal lists that the run did not fetch. The columns and the
two rules that hold for every country are in `CONVENTIONS.md` section 2, step 7; what the dates mean here is in
the module's own docstring.

## 7. Build the corpus (optional)

```
PYTHONPATH=src python tools/merge_corpus.py --outputs <ws>/outputs/SG --out <ws>/outputs/SG/SG_corpus_$(date -u +%F)
```

One folder with the newest copy of every law across the runs (`CONVENTIONS.md` step 6). Not needed after a single
crawl.

## 8. Things that go wrong

| Symptom | Cause | What to do |
| :---- | :---- | :---- |
| `SSO is throttling: HTTP 467` (or 403, 429, 503) | The portal's soft throttle | The build stops at once. Wait, then rebuild; do not shorten the delay |
| `N pages in a row failed` | The portal or the network is down mid-build | The build stops; rebuild later. One failed page alone is a note and a row without dates |
| A listing shows 20 rows | The default page size | The catalogue asks for `PageSize=100` and follows the Next Page links; the SL tab is read page by page at 100 |
| `link file … was built from a different registry` | `sources.yaml` or the seeds changed after the build | Rebuild the list (step 2) |
| `the engine waits 3.0 s … set REQUEST_DELAY_MS=6000` | The crawl was started without the delay | Stop and restart with `REQUEST_DELAY_MS=6000` |
| `store FileNotFoundError` in the crawl log, HTTP 200 | The document's path is over Windows' 260-character limit (a long title) | Run with `--out` on a `subst` drive (step 3); `store_failed` in the audit lists the documents |
| HTTP 202, empty body, `x-amzn-waf-action: challenge` | The edge's WAF challenge (`../NOTES.md` 1.3) | The engine stops after 10; wait an hour, probe `robots.txt` once, resume the same run at `REQUEST_DELAY_MS=15000` |
| `Last-Modified` moved, bytes did not | SSO regenerates the PDF; the header is a generation stamp | Not a change signal (`../NOTES.md` 1.3). Compare the detail page's version date, then bytes |
| Two repealed acts with the same title | "Accountants Act (Repealed)" appears twice | The list appends `[CODE, repealed DATE]` to the second, so the engine's name-keyed id map keeps them apart |

## 9. What the settings mean (`sources.yaml`, block `sso:`)

| Setting | Value today | Meaning |
| :---- | :---- | :---- |
| `root` | `https://sso.agc.gov.sg` | The portal |
| `detail_pages` | `all` | Whose detail page the catalogue reads: every current act (decision 17); `seed` reads the seeds' only; `none` reads none |
| `subsidiary_acts` | `seed` | Whose SL tab is read and fetched (decision 12's rule); `none` |
| `subsidiary_max_per_act` | unset (the code's default, 100) | SL fetched per act at most; every tab's total is recorded. Left out of `sources.yaml` so the list of 2026-09-15 keeps its fingerprint; any key added or changed invalidates a list |
| `acts_supp_years` | 2 | Years of the Acts Supplement read, this year backwards |
| `listing_page_size` | 500 | The portal's maximum |
| `read_repealed` | `true` | Read the Repealed and Uncommenced listings |
| `frontier` | `discover` | The default; `links_file` replays a list (step 3 sets it in the environment with `SSO_LINKS_FILE`) |

Every key can be overridden by `SSO_<KEY>` in the environment. `portals.primary_statutes` (`crawl_style: playwright`)
and `portals.regulators` are Round 1's; the title net (`seed_queries`, legacy `P6-I1` … `P7-I5` keys: do not re-tag)
decides which acts count as relevant. Two amending acts in `links/seed_laws.yaml` carry indicator tags they should
not (`../NOTES.md` 1.3).
