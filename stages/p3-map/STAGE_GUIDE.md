# P3 stage guide — indicator mapping + verification (submission-repo orientation)

> Submission-repo documentation layered on top of the stage. The stage's own
> `README.md`, workflow docs, and code are preserved **verbatim** from the
> source repository (every committed file is hash-identical to it — including
> three run-evidence logs the source repo force-added past its own gitignore).

## What this stage is

P3 is the judgment stage: it takes the 411,986 byte-grounded provisions from
Hand-off #2 and decides, per RDTII indicator and economy, which provisions
apply and what each economy scores. Design principle: **models are trusted
only where judgment is required — and never alone.** Retrieval over-collects,
a cheap screen thins leniently, an expensive model renders schema-forced
verdicts against the frozen codebook, and every "applies" verdict is then
**re-judged blind** by a different model that never sees the first model's
reasoning. The scoring chain is **baseline-blind** (independently audited);
the Round-1 baseline is touched only downstream, for NEW/KNOWN tagging,
error-checking, and evaluation.

Judged output (after human curation decisions): the 13-column CSV + host-JSON
records per economy — committed under `../../submission/` in this repo, NOT
here (this stage's `out/` is deliberately excluded from version control).

## The pipeline (S0–S10)

| Stage | What it does | Where |
|---|---|---|
| S0 ingest | Streams Hand-off #2; **re-verifies every quote byte-exact** at the seam; preflight rejects phantom provision ids | `src/p3map/ingest.py` |
| S1 prefilter | "The indicator becomes the query": BM25 + dense embeddings over the corpus, queries built from the vendored instrument's signatures | `src/p3map/prefilter/` (`queries.py`) |
| S2 select | Merges legs into direct/gray candidate pairs | `src/p3map/prefilter/` |
| S3 triage | Lenient cheap screen (Claude Haiku) over the gray band — errors default to KEEP | `src/p3map/triage/` |
| S4 map | **Schema-forced Sonnet verdicts** per provision group: core question → explicit trap booleans (ban-vs-conditional, max≠min retention, inverted polarity…) → verdict | `src/p3map/mapping/runner.py` |
| S5 blind verify | Every fired verdict re-judged by Haiku **blind** (provision + question only, never S4's reasoning); Opus 2-of-3 tiebreak; ~⅓ of fires overturned | `src/p3map/verify/blind.py` |
| S6 rollup | Survivors → economy scores with per-indicator basis lines | `src/p3map/chain.py` |
| S7 NEW/KNOWN | 3-tier diff vs the Round-1 baseline (fuzzy law match → section-level); ties resolve to KNOWN (conservative) | `src/p3map/discovery/newknown.py` |
| S8 error-check | Malaysia error-check against flagged baseline rows | `src/p3map/` |
| S9 submission | Curates verified+tagged fires into the judged 13-column CSV + host JSON (six extra fields incl. per-law `provisions[]`, `raw_context`); audit-trio validator (no row without snippet+locator+URL); "No provision found" convention | `src/p3map/output/submission.py` |
| S10 eval | Recall + KNOWN-tag accuracy vs the 51-row gold set; misses reported honestly | `src/p3map/eval/` |

Deterministic re-runs of S6→S10 in order: `src/p3map/chain.py`.

## What's in this folder

| Item | Usage |
|---|---|
| `src/p3map/` | The pipeline above + `ab/` (the pre-registered A/B harness). |
| `contracts/instrument/` | **The vendored P0 instrument, byte-identical to `../p0-instrument/output/`** — the mapper cannot drift from the codebook. |
| `reference/Round1_Baseline_Database.xlsx` | The Round-1 baseline the NEW/KNOWN diff runs against (S7+). |
| `workflow/` | The working record: `MAPPING_MECHANISM.md` (an s.26(1) verdict traced end-to-end), `WORKFLOW_LOG.md` (dated run log + **cost ledger**), `REVIEW_ITEMS.md` (every judgment call + disposition), `DELTA_AU_v2.4*.md` (the two AU re-runs with SG/MY hash-proven untouched). |
| `docs/ab/` | **A/B evidence**: preregistrations + reports for A/B-1..4 — local qwen and DeepSeek (two models, two arms) all FAIL the pre-registered gates (triage FN, byte-exact grounding); the measured basis for the model policy. |
| `docs/` | Mapping framework research, kickoff decisions, shared corpus-audit docs. |
| `logs/run_evidence/` | Force-committed raw run logs (SG mapping + both verify runs) — evidence, not tidiness. |
| `config/`, `requirements.lock`, `.env.example` | Env-driven model/paths config; pinned deps. |
| `tests/` | Hold-out smoke: a non-existent economy must produce 9 well-formed "No provision found" rows, not a crash (`python -m tests.test_holdout_smoke`). |

## Commands

```
pip install -r requirements.lock       # NOTE: pins torch cu124 (CUDA). CPU-only box:
                                       #   pip install torch --index-url https://download.pytorch.org/whl/cpu
                                       # then the rest of the lock.
copy .env.example .env                 # empty key => auto-fallback to local Ollama
python -m src.p3map.cli version        # contract check
python -m src.p3map.cli ingest|prefilter|select|triage   # Phase A (S0–S3, no-key path)
python -m src.p3map.mapping.runner <ECON>                # S4
python -m src.p3map.verify.blind <ECON>                  # S5
python -m src.p3map.chain <ECON>                         # S6–S10 in order
python -m tests.test_holdout_smoke                       # edge-input contract
```

## Integrity properties worth knowing before judging

- **Baseline-blind scoring**: S3/S4/S5/S6 contain no baseline content
  (independently audited); three soft channels (exemplar-guided retrieval
  queries, threshold calibration, output curation) are disclosed in
  `docs/DISCLOSURES.md` at repo root.
- **Nothing scores unverified**: only S5-surviving fires reach the rollup;
  overturned fires are excluded and counted.
- **Curation is human-in-the-loop by design**: every NEW row gets a human
  eyeball; judgment calls and their dispositions live in
  `workflow/REVIEW_ITEMS.md` rather than being silently absorbed.
- **Costs are ledger-evidenced** (`workflow/WORKFLOW_LOG.md` + the committed
  cost ledger); unevidenced figures are nulled and disclosed, not guessed.
