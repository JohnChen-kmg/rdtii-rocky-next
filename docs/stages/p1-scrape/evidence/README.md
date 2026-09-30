# evidence/

Seven artefacts this task must produce. Each one backs a claim that somebody else will check.

| # | Artefact | Taken from | What it proves |
| ----: | :---- | :---- | :---- |
| 1 | A new economy added by YAML and adapter alone | The commit diff, plus the crawl log for its first run | C1a, 15 marks for minimal reconfiguration |
| 2 | Manifest rows for a non-English economy | `manifest.csv` rows with `language` populated, plus the portal's own `Content-Language` header in the `.headers.json` sidecar | This task's share of C1c |
| 3 | A two-pass delta run | `run_record.json`, plus the matching `crawl_log.jsonl` slice | The second pass fetches nothing and reads 0 documents |
| 4 | A politeness sample | A per-request log written by the rate limiter: one line per HTTP request to each host, discovery, retries and robots.txt included, with the start time to the millisecond. Not `crawl_log.jsonl`, which logs one line per document after the fetch returns, to the second, and never logs discovery requests | Requests to one host sit at least the larger of three seconds and that host's robots.txt `Crawl-delay` apart (`POLICY.md` 5.1): 6 s on SSO, 10 s on the Federal Register |
| 5 | Measured cost | `cost_report.json` from every real run | Feeds the one unified cost ledger |
| 6 | Seed provenance and a leakage re-check, per registry | Each `countries/<cc>-<name>/sources.yaml` `provenance` key, plus a dated note re-running the Round 1 leakage audit's reasoning | No new registry's seeds came from the host baseline (`POLICY.md` section 4, rule 2). Any use of a host row, and every Round 1 seed that did come from the baseline, is disclosed. Added 2026-09-13, `POLICY.md` section 4 |
| 7 | A conformance report across economies | `scrape.py --validate` coverage output, per column per economy | Every economy's output has one shape (`CONTRACT.md` section 4). Added 2026-09-13 |

Artefact 3 is needed on 15 October, for the live stress test's discovery run. The submission's
live-test note quotes it.

Artefact 5 feeds the submission's measured-cost section. The secretariat verifies it against the
code.

`run_record.json` does not exist yet. Step 1B-6 in PLAN.md creates it.

The per-request log for artefact 4 does not exist yet either. It waits on the fix in `POLICY.md` 5.5.

Keep copies here. Put the run date in every filename.

The frozen Round 1 corpus stays at
`C:\Users\woshi\Desktop\RDTII\pipeline-data\rdtii-p1-scrape\handoff1_v2`. It is never duplicated
into this folder. New runs live in `outputs/<CC>/<CC>_ws_<YYYY-MM-DD>/` (update checks in `<CC>_ws_<since>_to_<date>/`) with their `RUN_NOTE.md` and `audit.md`, and merge into `outputs/<CC>/<CC>_corpus_<date>/` (decisions 15 to 17);
copy only the artefact a claim needs into this folder.
