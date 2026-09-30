# Run note: CN_sources_2026-09-21_to_2026-09-22 — China's first update check

## Read this first

**The first live run of `countries/cn-china/tools/update.py`**, one day after the baseline collection. Nothing
had changed, which is the expected answer after a day — and it is the useful one for a first run, because it shows
the check does not raise false alarms: the six gov.cn pages were re-read and all six compared **unchanged**, so the
text comparison is not tripped by page furniture.

## At a glance

| | |
| :---- | :---- |
| Baseline | `CN_sources_2026-09-21` |
| Run | 2026-09-22, `python countries/cn-china/tools/update.py --fetch` |
| Requests | **12, all HTTP 200** — 6 CAC listings, 6 gov.cn pages — plus the two hosts' robots.txt |
| robots.txt | `www.cac.gov.cn` permits; `www.gov.cn` permits |
| Layer 1 | **not compared** — no fresh export was passed (`--npc-new`) |
| CAC | 111 listed; **0 new, 0 gone, 0 retitled** |
| gov.cn | 6 re-read; **0 changed** |
| Exit | 0 |

## What this check does not see

MIIT and Customs, which are collected by hand; every source in `CN_sources_2026-09-21/_deferred/`; and the
publishers not yet collected. The watch list was printed before and after the check, as `CONVENTIONS.md` rule 11
requires, and its table is `CN_sources_2026-09-21/CHECK_BY_HAND.md`. **This check is not a complete update until
those have been looked at** — and the national database, the core of the corpus, is only compared when a fresh export
is downloaded by hand.

## Files

`changes.md` (the result in words), `cac_changes.csv` and `govcn_changes.csv` (empty of changes; the gov.cn file lists
each page's before and after text hashes), `run_log.jsonl` (every request and both robots verdicts). No `auto/cac/`,
because there was nothing new to fetch.
