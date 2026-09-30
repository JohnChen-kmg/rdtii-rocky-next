# Workflow: fetching only what the gazette published or superseded since the last run (Lao PDR)

**Built 2026-09-20**, in the shape Malaysia's, Singapore's, Australia's and Timor-Leste's checks have. Two things
make this one different from all of them:

- **It can see a supersession.** Every listing row carries a status word — ປັດຈຸບັນ (current) or ສະບັບເກົ່າ (old
  version) — so a law that has been replaced is visible in the listing, with no document opened. No other portal
  in this workshop states that per row.
- **It is the dearest check here.** The gazette pages ten rows at a time and **ignores `Document_pageSize`**, so
  there is no cheap first-page read of a listing holding 657 agreements. A full check is about **190 requests**,
  some 25 minutes. `--pages` buys a shallow one for about 25 requests, and says what it gave up.

Every command runs from the **stage root** in Git Bash. `<ws>` is this workshop; `$WS` is this country folder.

## 0. Before you start

- **Politeness:** `REQUEST_DELAY_MS=6000`, our own choice — the portal publishes no robots.txt and states no
  delay (`../NOTES.md` 1.1).
- **No crawl against `laoofficialgazette.gov.la` at the same time**, and no second session running one.
- The scraper package must be installed with its `updates/` subpackage (`../scraper/WORKFLOW.md`, step 1).

## 1. Run the check

```
REQUEST_DELAY_MS=6000 PYTHONPATH=src python -m p1_scrape.adapters.la_gazette.updates \
    --outputs R:/outputs/LA \
    --registry $WS/sources.yaml --seeds $WS/links/seed_laws.yaml
```

The cheap one, when you only want to know what is new:

```
    … --pages 2          # the first two pages of each listing: about 25 requests
```

- **The baseline** is the newest run under `--outputs` that has a `links_used/laws.csv`; `--baseline <run>` pins
  one instead.
- **The date** is the day the baseline's list was built, unless `--since YYYY-MM-DD` says otherwise. With a date
  and no baseline, a law counts as new when the gazette published it on or after that date — the
  ເຜີຍແຜ່ລົງຈົດໝາຍເຫດ column, which is the date the portal orders its own listings by.
- **`--out`** names the run folder; without it the check writes `<outputs>/LA_ws_<since>_to_<today>`. One of
  `--outputs` or `--out` is required, so a run folder never lands in the current directory.
- **The run folder is created even when nothing changed:** the check itself is the record.

## 2. What it reads, and what it costs

| What | Requests |
| :---- | ----: |
| robots.txt | 1 |
| Every listing, `old=0` and `old=1`, in full | about 190 |
| Detail pages | **0** — the listing carries everything |
| Documents, to find out what changed | **0** |

With `--pages 2`: **about 25 requests**, three minutes.

## 3. How it decides

| Found | Verdict | Fetched? |
| :---- | :---- | :---- |
| A law the baseline never listed | `new_law` | Yes — unless we already hold that exact file, and then the note says so |
| A law whose **status word** changed (ປັດຈຸບັນ → ສະບັບເກົ່າ) | `status_changed` | Yes |
| A law we listed whose file no run stored | `not_stored` | Yes |
| A law we listed that now points at a different file | `document_moved` | Yes, keeping the old address in the row |
| A law that now has an English translation it did not have | `translation_added` | Yes — **the English file only**; the Lao text we hold is untouched |
| A law the baseline listed that the portal no longer lists | `delisted` | **No: reported** |
| Everything else | `unchanged` | No |

**There is no `amended` verdict, and that is correct here.** The gazette publishes as made and never edits a
document. An amendment arrives one of two ways, and both are already covered:

- as its own instrument, ກົດໝາຍ ວ່າດ້ວຍການປັບປຸງ…ມາດຕາ — a `new_law` whose `document_kind` is `amending_act`;
- as a whole revised text, ສະບັບປັບປຸງ — a `new_law` of its own, which pushes the text it replaces into the
  `old=1` listing, where the same check reads it as `status_changed`.

**A file is fetched once** however many verdicts point at it: `to_fetch` is deduplicated by address.

## 4. What it writes

| File | What it holds |
| :---- | :---- |
| `changes.json`, `changes.md` | Every verdict above, with the dates, the status word before and after, the old and new addresses, and the notes |
| `links_used/documents.jsonl`, `documents.csv` | The delta list: the files to fetch, built by the adapter's own builder, each row's `contract_meta.update` saying what changed and what the baseline held |
| `links_used/laws.csv` | **Every law the portal lists today**, not only the changed ones, so this run folder is a complete baseline for the next check. After a `--pages` check it is everything *as far as it was read* |
| `links_used/catalogue_meta.json`, `discovery_log.jsonl` | The settings the run used, the registry fingerprint, and every request |

## 5. Crawl the delta list

The check prints the command:

```
REQUEST_DELAY_MS=6000 GAZETTE_FRONTIER=links_file \
    GAZETTE_LINKS_FILE=R:/outputs/LA/LA_ws_<since>_to_<date>/links_used/documents.jsonl \
    python scrape.py --economy LA --scope all --out R:/outputs/LA/LA_ws_<since>_to_<date>
```

Then steps 4 to 7 of `../scraper/WORKFLOW.md`: validate, audit, law table, run note, and the corpus when the run
should reach downstream.

## 6. What it cannot see

- **A scan replaced at the same address.** If the gazette re-uploads a better scan under the same filename,
  nothing in the listing changes and the check will not notice. Only a content hash would, which is
  `POLICY.md` section 6, test three.
- **Anything below the cut, on a `--pages` check.** The gazette lists newest first, so a shallow read finds
  everything recently published, but a status word that changed further down a listing is invisible. A partial
  check therefore **never reports `delisted`** — a law it did not see is not a law the portal dropped — and
  `changes.md` carries that warning on every partial run.
- **Why a law was superseded.** The portal states the new status, never the instrument that caused it. The
  amending law is in the list too; joining the two is the law table's problem, and it is a weak join
  (`../scraper/checker.py`).

## 7. Things that go wrong

| Symptom | Cause | What to do |
| :---- | :---- | :---- |
| `no date to check from` | No run with a list under `--outputs` | Pass `--since`, or build a list first (`../scraper/WORKFLOW.md`, step 2) |
| `--out is needed when there is no --outputs folder` | `--baseline` alone says what to compare with, not where to write | Give `--out` or `--outputs` |
| `the gazette could not be read` (exit 2) | A listing page failed five times, or the format changed | Nothing is written. Try later |
| `<run> already holds a run` (exit 2) | `--out` points at a folder with a manifest | Give a new `--out` (`outputs/README.md` rule 1) |
| Many `not_stored` | The baseline listed laws whose files a crawl never fetched | Expected after a partial crawl: the check queues them |
| Many `status_changed` at once | The National Assembly published a batch of revised texts, which is how it legislates | Read them: each one usually has a matching `new_law` for the revised version |
| `delisted` rows | The portal reorganised a listing | Read them: the copy we hold is unaffected, but the portal's own listing changed |

## 8. What the settings mean

The check reads the same `gazette:` block as the list build (`../scraper/WORKFLOW.md`, section 9); its only
setting of its own is `--pages`. `--pillars` (default `6,7`) decides which seeds count, and a seed with no
indicator tag is always kept.
