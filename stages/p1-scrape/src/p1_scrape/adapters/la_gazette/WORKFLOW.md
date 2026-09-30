# Workflow: crawling the Lao Official Gazette with this scraper (Lao PDR)

**Built 2026-09-20.** The gazette pages ten rows at a time and ignores `Document_pageSize`, so the link list is
the dearest in the workshop after Malaysia's: about **190 listing requests**, some 25 minutes. It is still far
cheaper than the crawl, because **95% of the documents are scans** and a Lao PDF averages about 2.1 MB
(measured over the 1,630 documents of the first crawl, not estimated).

**Nothing here does OCR.** The scraper collects documents; OCR is stage 2's work (`../NOTES.md` 3.2).

Every command runs from the **stage root** in Git Bash. `<ws>` is this workshop; `$WS` is this country folder.

## 0. Before you start

- **Politeness:** `REQUEST_DELAY_MS=6000`. The portal publishes **no robots.txt** and states no delay, so 6 s is
  **our own choice**, not the host's (`../NOTES.md` 1.1, `POLICY.md` 5.1). Do not lower it.
- **One process at a time against `laoofficialgazette.gov.la`.** A list build and a crawl never overlap, and no
  second session runs one either. Check first: `Get-CimInstance Win32_Process -Filter "Name like '%python%'"`.
- **Set `USER_AGENT` with a contact address.** The catalogue prints the identity it will use on its first line;
  if that line does not show the address, the settings did not load — run from the stage root (Singapore lost
  three runs to this, `../../sg-singapore/NOTES.md` 1.3).
- **Do not edit the repo or the instrument.** Work on the copies here; hand them back later.

## 1. Install the scraper into the stage

```
STAGE=<sandbox>/p1-scrape ; WS=<ws>/countries/la-lao-pdr
mkdir -p $STAGE/src/p1_scrape/adapters/la_gazette/updates
cp $WS/scraper/*.py $STAGE/src/p1_scrape/adapters/la_gazette/
cp $WS/updates/*.py $STAGE/src/p1_scrape/adapters/la_gazette/updates/
cp $WS/updates/watchlist.tsv $STAGE/src/p1_scrape/adapters/la_gazette/updates/   # CONVENTIONS rule 11; not Python, so the line above leaves it behind

# the registry: sources.yaml first, then the seeds appended
cat $WS/sources.yaml $WS/links/seed_laws.yaml > $STAGE/contracts/instrument/sources_la.yaml
cp $STAGE/contracts/instrument/sources_la.yaml $STAGE/instrument/sources_la.yaml

# the tests and their fixtures
cp $WS/tests/test_la_*.py $STAGE/tests/
mkdir -p $STAGE/tests/fixtures/la && cp $WS/tests/fixtures/* $STAGE/tests/fixtures/la/
```

The package imports the paced client, the robots.txt reader, the title-rule matcher and the link-list writer from
**Malaysia's** package, so that one must be installed too (`../../my-malaysia/scraper/WORKFLOW.md`, step 1).

**Four engine changes are needed before any of this runs**, and they go in the **sandbox copy only** — the repo
is read-only. Each is a hand-back request; `../NOTES.md` 2.5 carries the diff.

| What breaks without it | Where |
| :---- | :---- |
| `WARN unrecognized economy 'LA' — skipping; nothing to crawl.` | `economies.py`, `adapters/registry.py` |
| `economy: 'LA' is not one of ['SG','AU','MY']` at validation | `contracts/schemas/manifest.schema.json` |
| **Every Lao law stores in `raw/la/unknown/` under doc_id `la-law-NNN`** | `utils.py`, `dedup.py`, `orchestrator.py` |

Check the install without touching the portal:

```
python -m pytest -q tests/test_la_gazette.py tests/test_la_updates.py
```

All 60 must pass, with 1 expected failure, 40 + 20 on 2026-09-22 (`../tests/README.md`). Both files, always.

## 2. Build the link list (about 25 minutes, no documents)

```
REQUEST_DELAY_MS=6000 PYTHONPATH=src python -m p1_scrape.adapters.la_gazette.catalogue \
    --registry $WS/sources.yaml \
    --seeds $WS/links/seed_laws.yaml \
    --out $WS/links
```

- **What it does:** reads robots.txt, then every page of every kind's listing, `old=0` (current) and `old=1`
  (superseded, and the amending laws). Ten rows a page. No detail page is read — the law's own page carries no
  field the listing does not (`../NOTES.md` 2.3).
- **What it writes** into `links/`: `documents.jsonl` (one row per **file**, Lao and English separately),
  `documents.csv`, `laws.csv` (one row per **law**, the census), `catalogue_meta.json`, `discovery_log.jsonl`.
- **After any change** to `sources.yaml` or `seed_laws.yaml`, rebuild. The crawl refuses a list built from a
  different registry.

Read `laws.csv` and the console notes before crawling. Two lines are normal and are not faults:

- `Presidential Decree (legaltype=4): 0 law(s)` — the portal prints ບໍ່ມີຂໍ້ມູນ, no data, for that kind.
- `N law(s) were already listed under another kind` — legaltype 6 also carries the Civil Code and the Penal
  Code, which have listings of their own. Each law is kept once, under the first listing that named it.

## 3. Crawl the list into a new run folder (about 4 to 5 hours, 4 to 6 GB)

```
RUN=R:/outputs/LA/LA_ws_$(date -u +%F)          # a short path; see below
mkdir -p $RUN/logs && cp -r $WS/links $RUN/links_used

REQUEST_DELAY_MS=6000 GAZETTE_FRONTIER=links_file GAZETTE_LINKS_FILE=$RUN/links_used/documents.jsonl \
    python scrape.py --economy LA --scope all --out $RUN 2>&1 | tee $RUN/logs/crawl_stdout.log
```

- **Scope:** `all` takes every file; `relevant` the seeds and what the title rule selects; `seed` the seed laws
  only. The title rule was written without a Lao reader (`../NOTES.md` 5), so **crawl at `all`** and let the
  rule order the work rather than decide it.
- **Time:** about 1,800 documents at 6 s plus the download of a 2.1 MB file — about five hours (the crawl of
  2026-09-21 took 5 h 4 min for 1,824).
- **Size:** budget 5 GB. Nearly every page of nearly every document is an image.
- **Give `--out` a short, absolute path** (`subst R: <ws>` in PowerShell first). Lao titles run to 87
  characters, and although this adapter names each storage folder after the gazette's record id (`la-2537`)
  rather than the title, the corpus path is longer than the run path and the margin is worth keeping.

## 4. Check the result

```
python scrape.py --validate $RUN/manifest.csv       # must say 0 errors
PYTHONPATH=src python tools/audit_run.py $RUN       # audit.md, audit.json in the run folder
```

**Expect `no_text_layer` on about 95% of the rows.** There is no `RULES["LA"]` in `tools/audit_run.py` yet, so
the audit applies its generic flags, and where nearly every document is a scan that flag counts the corpus
rather than finding anything. `../NOTES.md` 2.5 carries the rule set to add, which turns it into a count and
keeps a flag for what is actually worth a person's time here — and marks the 5% that carry native text, because
stage 2 can read those without OCR.

## 5. Write the run note

`RUN_NOTE.md` from `outputs/RUN_NOTE_TEMPLATE.md`, then a row in `outputs/LA/README.md`.

## 6. Write the law table

```
PYTHONPATH=src python -m p1_scrape.adapters.la_gazette.checker $RUN            # law_table.csv in the run folder
PYTHONPATH=src python -m p1_scrape.adapters.la_gazette.checker <corpus> --all  # the corpus, plus the laws left out
```

One row per **law** (not per file: a translation is recorded against its law, not beside it). `in_force` is
answered on **every** row, because the gazette states a status word on every row — which is rarer than it
sounds. When the run carries a `links_rebuilt/` folder — a later list of the same portal rows read by a
corrected scraper — the table uses that census instead of `links_used/`, and says which on its last line.

## 7. Build the corpus (optional)

```
PYTHONPATH=src python tools/merge_corpus.py --outputs <ws>/outputs/LA --out <ws>/outputs/LA/LA_corpus_$(date -u +%F)
```

## 8. Things that go wrong

| Symptom | Cause | What to do |
| :---- | :---- | :---- |
| `the gazette answered HTTP <n>` | One listing page failed | **The build stops and nothing is written.** The paced client has already retried and, on a refusal, already rested and slowed down, so an error here is one the portal means. Rerun later |
| `gazette.max_pages is N … would have been lost` | A listing is longer than the page guard | Raise `max_pages` in `sources.yaml` and rebuild. The build **stops** rather than writing a short listing: `60` cut the 657-row Agreement listing to 600 on 2026-09-20, and a warning was too quiet for a fault that loses 57 laws |
| `printed neither a result count nor the empty marker` | The page format changed | Nothing is written. Read the page by hand before changing the parser |
| `the pager stopped after N page(s) with M read` | The portal's own count and its pager disagree | Nothing is written rather than a short census. Re-read the listing by hand |
| The portal refuses (403, 429, 503) | Its anti-scraping mechanism, if it ever shows one | Nothing to do: the client rests 1, 5, then 30 minutes, halves its speed and carries on (decision 23). **Never lower the delay or change the User-Agent to get past it** |
| `gazette.legal_types names [...]` | A typo in the registry | The kinds are the keys of `scraper/parse.py LEGAL_TYPES` |
| `link file … was built from a different registry` | `sources.yaml` or the seeds changed after the list was built | Rebuild the list (step 2) |
| Every document stored under `raw/la/unknown/` | The engine's slug fix is not installed (step 1) | Install it. `slugify` strips every Lao character |
| `audit.md` flags `no_text_layer` on everything | Normal here | Section 4 |

## 9. What the settings mean (`sources.yaml`, block `gazette:`)

| Key | Default | What it does |
| :---- | :---- | :---- |
| `root` | `https://laoofficialgazette.gov.la` | The host |
| `legal_types` | `all` | Which listings are read, by the portal's own `legaltype` number. `all` leaves out legaltype 16, which is contained in legaltype 6 (`../NOTES.md` 1.2); naming it explicitly still reads it |
| `superseded` | `true` | Read `old=1` as well as `old=0`. **Turning this off loses every amending law**, which the portal lists nowhere else |
| `english_pdfs` | `true` | Take the gazette's own English translation where it offers one, as its own row with `language: eng` |
| `max_pages` | `120` | Pages of one listing at most: a guard against a broken pager. The longest listing is Agreement, 657 laws = 66 pages. A listing cut short by this guard raises `GazetteUnavailable` and nothing is written — `60` silently cut Agreement to 600 on 2026-09-20 |
| `frontier` | `discover` | `links_file` replays a list instead; the crawl sets it in the environment |
| `links_file` | — | The list to replay, as a registry key or `GAZETTE_LINKS_FILE` |

Every key can be overridden by `GAZETTE_<KEY>` in the environment. Changing any key other than `frontier` and
`links_file` changes the list's fingerprint, and the crawl will refuse a stale list. The environment's overrides
do **not** change the fingerprint, but `catalogue_meta.json` records the values the run actually used.
