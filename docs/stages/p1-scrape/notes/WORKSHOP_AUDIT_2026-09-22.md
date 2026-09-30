# Workshop audit, 2026-09-22

Asked by the developer on closing China's stage: *"revisit the whole working folder, if all the countries' working
folders follow the convention, and the scraper and updater tools work in a correct way."*

## How it was checked

1. **Structure**, by script, against `CONVENTIONS.md` sections 4 and 5 and `outputs/README.md`: every required path in
   every country folder, the ten `NOTES.md` sections in order, rule 11's watch list and hook, and every run and corpus
   folder's required notes.
2. **Every test suite, in a clean sandbox** built from the repo's `stages/p1-scrape` — without its `handoff1_v2`, which
   rule 3 says is never read — and each country's documented install step, in a new virtualenv from the stage's own
   pinned `requirements-dev.txt`. Then rebuilt from scratch with the corrected install steps and run again.
3. **The engine's own tests** with all five packages installed, which is what the hand-back will do to the repo.
4. **Two updaters live**: China's new one, on its first run, and Timor-Leste's, which had never run live.

## Result

**Every suite passes on a fresh install from the documented steps: 419 tests, and 1 expected failure.**

| Suite | Result | Was documented as |
| :---- | :---- | :---- |
| Malaysia | 175 passed | 175 |
| Singapore | 36 passed | 32 |
| Australia | 33 passed, plus the engine's Round 1 multivolume test, 9 | 22 plus 9 |
| Timor-Leste | 36 passed | 29 |
| Lao PDR | 60 passed, 1 expected failure | 59 |
| China | 32 passed | new |
| Shared tools | 22 passed | 17 in one table, 22 in another |
| The engine's own, with every package installed | 25 passed | — |

**Every country's update check has now run live at least once.** Malaysia 3, Singapore 1 successful after its
identity fix, Australia 1, Lao PDR 2, **Timor-Leste 2 (both 2026-09-22), China 1 (2026-09-22)**.

**Structure: every country folder and run folder follows the layout.** Two items remain, both known and explained
below.

## Found and fixed

1. **Timor-Leste's update check re-fetched documents it already held.** Its first live run reported **191 acts as moved
   and asked for 66 documents, 50 of them already stored**. The check compared addresses as strings, and the baseline
   recorded forms the parser has canonicalised since: 188 differed only in scheme and host, and 3 were repaired
   host-less links. `canonical_url()` was added to `scraper/parse.py`, and every comparison in `updates/diff.py` now
   goes through it; four tests were added. The re-run asked for **16**, the documents the first crawl could not
   fetch. The defective run folder is kept, as every run is, and its note says not to crawl its delta.
2. **A Lao test asserted an engine change still to be handed back**, so the suite failed against the engine as it
   stands. It mixed two claims. It is now split: the adapter's own guarantee stays a hard test, and the engine change is
   an expected failure that names its hand-back and passes once the engine carries the fix.
3. **No install step copied `updates/watchlist.tsv`.** Each copies `updates/*.py`, and the watch list is not Python, so
   an installed update check would have printed "no watch list" instead of the sources it cannot see (rule 11). The line
   is added to all five.
4. **Malaysia's `cryptography` dependency sat outside its install block**, in a sentence after it. A sandbox built from
   the block alone failed **85 of 175 tests**, every one with `No module named 'cryptography'`. It is inside the block
   now, pinned to the version the hand-back names.
5. **Stale counts**: the test counts in `CONVENTIONS.md` section 6, `tools/README.md`, and the two workflows' "all N
   must pass" lines.
6. **China had no `NOTES.md`** in the ten-section layout. Written, beside `SOURCES.md` and `WORKFLOW.md`.

## Found, not fixed — and why

| Item | Why not fixed tonight |
| :---- | :---- |
| `tools/audit_run.py` has no `RULES["LA"]` | Already a documented open item. It changes Lao PDR's audit output, and the rules need the care the other countries' got |
| The two shared-code defects Lao PDR found: `catalogue._cell` collapses whitespace in a URL; `merge_corpus.identity()` ignores language | Both change behaviour in code four countries import. They need the developer's call and a run across MY, SG, AU and TL |
| `MY_ws_2026-09-13` has no `links_used/` | Not a defect: that crawl predates link lists, and its note says so |
| Hand-back to the repo, which is read-only here | Recorded in `countries/README.md`: `cryptography==44.0.0` in `requirements.txt`; the repo's `tests/test_my_selection.py` deleted. **One nuance**: only its four `_extract_pdf_url` tests test the filename heuristic `CONVENTIONS.md` section 1 now forbids — its `_act_number` test still holds against the package and could be kept. Timor-Leste's and Lao PDR's engine changes: the economy code, the adapter registry, the manifest schema, the slug |
| Timor-Leste's 16-document delta | A crawl, the developer's to run, in a sandbox that carries the engine changes Timor-Leste needs |

## Worth knowing

**The earlier scratch virtualenv had been partly cleared** — `pip` and `pytest` had lost their entry points. It lived in
the Windows temp folder, like every sandbox in this workshop, and temp is cleaned. A sandbox that passed last week can
fail today for reasons that have nothing to do with the code. Rebuild from the stage and the install steps rather than
reuse one; this audit did, twice.

## Nothing committed

Every change above is on disk and uncommitted, as the conventions require until the developer asks.
