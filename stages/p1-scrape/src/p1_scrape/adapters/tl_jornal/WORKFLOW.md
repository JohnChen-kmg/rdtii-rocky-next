# Workflow: crawling the Jornal da República with this scraper (Timor-Leste)

**Built 2026-09-20.** Seven requests build the whole link list, because each of the six category pages carries its
kind's entire history (`../NOTES.md` 1.2). The documents are native-text Portuguese PDFs; nothing here needs a
browser, and nothing needs OCR.

**Status, 2026-09-20:** the catalogue step, the update check and the law table exist and are tested offline (29
tests). The first crawl has not run. The audit has no `TL` rule set yet, so it applies its generic flags only.

Every command runs from the **stage root** in Git Bash. `<ws>` is this workshop; `$WS` is this country folder.

## 0. Before you start

- **Politeness:** `REQUEST_DELAY_MS=10000`. The portal's robots.txt states `Crawl-delay: 10` and the client adopts
  it at the first request; do not set a smaller delay.
- **One process at a time against `www.mj.gov.tl`.** A list build and a crawl never overlap.
- **Do not edit the repo or the instrument.** Work on the copies here; hand them back later.

## 1. Install the scraper into the stage

```
STAGE=<sandbox>/p1-scrape ; WS=<ws>/countries/tl-timor-leste
mkdir -p $STAGE/src/p1_scrape/adapters/tl_jornal/updates
cp $WS/scraper/*.py $STAGE/src/p1_scrape/adapters/tl_jornal/
cp $WS/updates/*.py $STAGE/src/p1_scrape/adapters/tl_jornal/updates/
cp $WS/updates/watchlist.tsv $STAGE/src/p1_scrape/adapters/tl_jornal/updates/   # CONVENTIONS rule 11; not Python, so the line above leaves it behind

# the registry: sources.yaml first, then the seeds appended
cat $WS/sources.yaml $WS/links/seed_laws.yaml > $STAGE/contracts/instrument/sources_tl.yaml
cp $STAGE/contracts/instrument/sources_tl.yaml $STAGE/instrument/sources_tl.yaml

# the tests and their fixtures
cp $WS/tests/test_tl_*.py $STAGE/tests/
mkdir -p $STAGE/tests/fixtures/tl && cp $WS/tests/fixtures/* $STAGE/tests/fixtures/tl/
```

The package imports the paced client, the robots.txt reader, the title-rule matcher and the link-list writer from
**Malaysia's** package, so that one must be installed too (`../../my-malaysia/scraper/WORKFLOW.md`, step 1).

Check the install without touching the portal:

```
python -m pytest -q tests/test_tl_jornal.py tests/test_tl_updates.py
```

All 36 must pass (23 + 13 on 2026-09-22, in a clean sandbox). Both files, always. The 13 include four added on 2026-09-22 for the address-comparison defect of the first live update check (`../NOTES.md` 2.6).

## 2. Build the link list (about a minute, no documents)

```
REQUEST_DELAY_MS=10000 PYTHONPATH=src python -m p1_scrape.adapters.tl_jornal.catalogue \
    --registry $WS/sources.yaml \
    --seeds $WS/links/seed_laws.yaml \
    --out $WS/links
```

- **What it does:** reads robots.txt, then one page per category (`jornal.categories`, all six by default), parses
  every row into an act, and groups the acts by the gazette issue that carries them.
- **What it writes** into `links/`: `documents.jsonl` (one row per **issue**), `documents.csv`, `laws.csv` (one row
  per **act**, the census), `catalogue_meta.json`, `discovery_log.jsonl`.
- **It prints the identity it uses** on the first line. If that line does not show the contact address, the
  settings did not load — run from the stage root (Singapore lost three runs to this, `../../sg-singapore/NOTES.md`
  1.3).
- **After any change** to `sources.yaml` or `seed_laws.yaml`, rebuild. The crawl refuses a list built from a
  different registry.

## 3. Crawl the list into a new run folder (about 5.5 hours)

```
RUN=R:/outputs/TL/TL_ws_$(date -u +%F)          # a short path: the engine names folders after law titles
mkdir -p $RUN/logs && cp -r $WS/links $RUN/links_used

REQUEST_DELAY_MS=10000 JORNAL_FRONTIER=links_file JORNAL_LINKS_FILE=$RUN/links_used/documents.jsonl \
    python scrape.py --economy TL --scope all --out $RUN 2>&1 | tee $RUN/logs/crawl_stdout.log
```

- **Scope:** `all` takes every issue (about 2,000); `relevant` the seeds and what the title rule selects; `seed`
  the seed acts' issues only.
- **Time:** 2,000 documents at 10 s plus download: about 5.5 hours. Run it overnight.
- **Give `--out` a short, absolute path** (`subst R: <ws>` in PowerShell first): Portuguese titles are long, and
  Windows' 260-character limit bites under `<ws>\outputs\TL\…`.

## 4. Check the result

```
python scrape.py --validate $RUN/manifest.csv       # must say 0 errors
PYTHONPATH=src python tools/audit_run.py $RUN       # audit.md, audit.json in the run folder
```

The audit applies its generic flags; a `TL` rule set is **not written yet**. When it is, it should flag an issue
whose first page is not a gazette masthead, and a file whose `SUMÁRIO` names no act.

## 5. Write the run note

`RUN_NOTE.md` from `outputs/RUN_NOTE_TEMPLATE.md`, then a row in `outputs/TL/README.md`.

## 6. Write the law table

```
PYTHONPATH=src python -m p1_scrape.adapters.tl_jornal.checker $RUN            # law_table.csv in the run folder
PYTHONPATH=src python -m p1_scrape.adapters.tl_jornal.checker <corpus> --all  # the corpus, plus the acts left out
```

One row per **act** (not per document), with `use` (decision 20), the amendment linkage, and `in_force` as
`not stated` everywhere, because the portal states no status.

## 7. Build the corpus (optional)

```
PYTHONPATH=src python tools/merge_corpus.py --outputs <ws>/outputs/TL --out <ws>/outputs/TL/TL_corpus_$(date -u +%F)
```

## 8. Things that go wrong

| Symptom | Cause | What to do |
| :---- | :---- | :---- |
| `the gazette answered HTTP <n>` | One category page failed | Rerun; three failures in a row stop the build and nothing is written |
| `nothing written (JornalUnavailable: … robots.txt …)` | robots.txt answered 5xx, which RFC 9309 treats as a full disallow | Wait and try again. Never crawl through it |
| The portal refuses (403, 429, 503) | Its anti-scraping mechanism, if it ever has one | Nothing to do: the client rests 1, 5, then 30 minutes, halves its speed and carries on (decision 23) |
| `jornal.categories names [...]` | A typo in the registry | The categories are the keys in `scraper/parse.py CATEGORIES` |
| `link file … was built from a different registry` | `sources.yaml` or the seeds changed after the list was built | Rebuild the list (step 2) |
| A document stores under a path that fails | Windows' 260-character limit and a long Portuguese title | Use the `subst` drive (step 3) |
| Many rows with `no document link` | Normal: 34 of 4,846 rows on 2026-09-20 carry no file | They keep their row in `laws.csv` with the reason |

## 9. What the settings mean (`sources.yaml`, block `jornal:`)

| Key | Default | What it does |
| :---- | :---- | :---- |
| `root` | `https://www.mj.gov.tl` | The host |
| `categories` | `all` | Which category pages are read: `all`, or a comma list of `leis`, `decretos_leis`, `decretos_governo`, `decretos_presidente`, `resolucoes_parlamento`, `resolucoes_governo` |
| `document_form` | `pdf` | The portal offers nothing else |
| `frontier` | `discover` | `links_file` replays a list instead; the crawl sets it in the environment |
| `links_file` | — | The list to replay, as a registry key or `JORNAL_LINKS_FILE` |

Every key can be overridden by `JORNAL_<KEY>` in the environment. Changing any key other than `frontier` and
`links_file` changes the list's fingerprint, and the crawl will refuse a stale list. The environment's overrides do
**not** change the fingerprint, but `catalogue_meta.json` records the values the run actually used.
