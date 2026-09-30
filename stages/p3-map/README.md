# rdtii-p3-map — Mapping legal provisions to the RDTII 2.1 index

Maps **766,526 grounded legal provisions** across six economies (Australia · China · Lao PDR ·
Malaysia · Singapore · Timor-Leste, from `handoff2/` contract **0.3.0**) to the **61** automated
RDTII 2.1 indicators across all twelve pillars, blind-verifies every verdict, tags NEW/KNOWN against
the baseline, and emits the judged **14-column** CSV + JSON with a full audit trail.

Indicator IDs are **decimal** — `6.1`, `12.4.1` — never `P6-I1`. The host's Output Data sheet derives
the pillar from them with a formula, and its Coverage Matrix counts that formula's result.

**Status (29 September 2026):** run `run_2026-09-27` complete. 14,456 provisions judged, **319 rows**
filed across six economies, **$275.24**. 422 tests. The assembled submission is in the repository's
`submission/` folder, which has its own README stating what is known to be wrong with it.

## Quick start (Windows, <10 min)

```powershell
py -3 -m venv .venv ; .venv\Scripts\activate
pip install -r requirements.lock        # pinned exact versions
copy .env.example .env                  # fill ANTHROPIC_API_KEY (may stay empty -> Ollama fallback)
python -m src.p3map.cli version         # prints the contract version
```

Then point `.env` at your data. **Three of these are not optional:**

| | |
| :---- | :---- |
| `HANDOFF2_DIR` | the extraction corpus. Default is `../handoff2`, which on this machine still holds Round 1's July output — a run that forgets this reads 411,986 stale provisions and looks fine |
| `OUT_DIR`, `INDEX_DIR` | the run directory. Never point them at `RDTII/pipeline-data/rdtii-p3-map`, which is frozen Round 1 evidence |
| `ECONOMIES` | scopes a run, e.g. `CN`. Unset means every economy in the corpus |
| `INDICATORS_SCOPE` | scopes the indicators, e.g. `3.5,9.1`. Unset means the instrument's automated set. **The run manifest records what this resolved to** — it did not until 29 September, and a re-emit without it silently produced rows for the wrong nine indicators |

## Pipeline stages

Phase A (S0–S2) runs at $0 and needs no API key.

| Stage | Command | What it does |
| :---- | :---- | :---- |
| S0 ingest | `python -m src.p3map.cli ingest` | streams `provisions.jsonl`, byte-exact grounding check, schema gate on a sample |
| S1 sparse | `python -m src.p3map.cli prefilter --leg bm25` | BM25, indicator-as-query from the vendored instrument. **Returns nothing for a non-English corpus** — an English tokeniser over Chinese or Lao produces no matchable term |
| S1 dense | `python -m src.p3map.cli prefilter --leg dense` | BGE-M3 embeddings, cosine vs indicator queries; resume-safe. **Required for CN, LA and TL** |
| S2 select | `python -m src.p3map.cli select` | RRF fusion, hint boosts, scored per-cell selection (`SELECT_MODE=caps` reverts to the Round 1 rule) |
| S3a triage | `python -m src.p3map.cli triage` | local screen of the gray band, $0 |
| S3b triage | `python -m src.p3map.triage.haiku` | paid relevance screen; `--limit` prices a pre-flight |
| — baseline | `python -m src.p3map.discovery.baseline` | once per run, reads the baseline sheets for NEW/KNOWN |
| S4 map | `python -m src.p3map.mapping.runner <E>` (live) or `python -m src.p3map.mapping.batch_runner submit\|poll\|fetch <E>` (−50%) | Sonnet schema-forced verdicts. The batch lane retries a result it cannot parse, live, once |
| S5–S10 | `python -m src.p3map.chain <E>` | verify → NEW/KNOWN → rollup → emit → eval → workbook → audit page |

`chain` takes two flags that exist because both failures are silent:

```
python -m src.p3map.chain CN --gloss                         # + machine English (paid)
python -m src.p3map.chain TL --extra-dirs <run>/out_tl52      # economy mapped in two arms
```

Without `--gloss` the English columns in the workbook and audit page are blank, which reads as
"nothing to translate". Without `--extra-dirs` a two-arm economy gets a workbook that looks normal
and is missing 52 indicators.

### Whole-run steps, after the last economy

These choose across every economy at once, so they are not in the per-economy chain:

```powershell
python -m src.p3map.output.urlcheck                          # liveness of every filed Source URL

python -m src.p3map.output.template `
  --template "OUTPUT_TEMPLATE_FINAL_ROUND.xlsx" --out OUTPUT_DATA_FILLED.xlsx `
  --records <run>/out/submission/records_*.csv                # S9c: the host's sheet, 101 rows

python -m src.p3map.output.package --out ../../submission `
  --arm AU=<run>/out --arm CN=<run>/out --arm LA=<run>/out `
  --arm MY=<run>/out --arm SG=<run>/out `
  --arm TL=<run>/out --arm TL=<run>/out_tl52 `
  --template "OUTPUT_TEMPLATE_FINAL_ROUND.xlsx"                # S9d: the submission folder
```

S9d writes one records file, one workbook and one audit page per economy, and **reports any indicator
an arm fired on that the copied workbook does not show** — the check that catches a half-merged
country, which is otherwise invisible.

**Swap the model:** one `.env` line (`LLM_MODEL`, `TRIAGE_MODEL`, `VERIFIER_MODEL`,
`ESCALATION_MODEL`, `EMBED_MODEL`, `OLLAMA_MODEL`), or `RDTII_ENGINE=B` for the whole open-weights
stack declared in `config/llm/engines.json`. An empty `ANTHROPIC_API_KEY` falls back to local Ollama.
The batch lane refuses to run when the resolved engine is not Anthropic, rather than billing Anthropic
while the operator believes the run is local.

## Design references
- `docs/MAPPING_FRAMEWORK_RESEARCH_2026-07-14.md` — the full framework (funnel
  sizing measured on the real corpus, trap catalog, cost model, verification
  verdicts on all 32 delta/discovery instruments §3.4b–d).
- `docs/KICKOFF_DECISIONS_2026-07-12.md` — the 12 design decisions.
- `INTERFACE_CONTRACT.md` v0.2.0 — seams; validate against `00_contracts/schemas/`.
