# S10 — Eval · $0 · no LLM

**What we're doing:** measuring how well the pipeline reproduced the known answers,
honestly (we never fed it the answers).

**In → Out**
- In: the judged CSV + `gold_set.jsonl`.
- Out: `out/eval/eval_report_<ECON>.json`.

**How it works** (`eval/evaluator.py`)
- For every **resolvable** gold row (its cited law exists in the corpus), did we emit
  a row with the same (economy, indicator) and a matching law? → **recall**.
- For matched rows, is the Discovery Tag KNOWN (it should be — these ARE baseline
  rows)? → **KNOWN-tag accuracy**.
- Allowlist **OFF** — organic candidates only. The 7 instrument-flagged label-noise
  gold rows are excluded (decision #9).

**Results**
- SG recall **0.846** (11/13) · MY **0.727** (0.889 on parsed-doc rows) · AU
  **0.889** (8/9); KNOWN-tag accuracy 0.82 / 0.81 / 1.0.
- Misses are documented, not hidden (e.g. MY's 4 misses cite parse-failed 2017 Codes
  of Practice — a disclosed corpus gap, not a mapping failure).
