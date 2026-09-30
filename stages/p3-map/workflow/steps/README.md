# Pipeline steps — one summary per stage

One document per stage. Each says **what we're doing**, **what goes in → what comes
out**, and for AI stages **exactly what we sent the model and what it sent back**
(real API conversations, real data — the canonical example is Singapore PDPA
s.26(1)). AI examples are shown as chat transcripts: `SYSTEM` / `USER` = what we fed
in, `ASSISTANT` = what we got back.

| Step | File | What it does | LLM? |
|---|---|---|---|
| S0 | [S0_ingest.md](S0_ingest.md) | Load provisions, verify byte-grounding | no ($0) |
| S1 | [S1_prefilter.md](S1_prefilter.md) | Turn indicators into queries, score every provision | no ($0) |
| S2 | [S2_select.md](S2_select.md) | Fuse + cap → direct / gray candidate bands | no ($0) |
| S3 | [S3_triage.md](S3_triage.md) | Cheap keep/drop screen of the gray band | **Haiku** |
| S4 | [S4_mapping.md](S4_mapping.md) | The verdict: does each indicator apply, with a quote | **Sonnet** |
| S5 | [S5_verify.md](S5_verify.md) | Blind re-judge every fire; overturn false ones | **Haiku + Opus** |
| S6 | [S6_rollup.md](S6_rollup.md) | Fires → the 9 economy scores | **2 calls/econ** |
| S7 | [S7_newknown.md](S7_newknown.md) | Tag each fire NEW or KNOWN vs the baseline | no ($0) |
| S8 | [S8_malaysia.md](S8_malaysia.md) | Malaysia error-check (URL/currency/substance) | no ($0) |
| S9 | [S9_emit.md](S9_emit.md) | Curate → the judged 13-column CSV + JSON | no ($0) |
| S10 | [S10_eval.md](S10_eval.md) | Score recall vs the gold set | no ($0) |

**Reference:** [DATA_DICTIONARY.md](DATA_DICTIONARY.md) — what every instrument /
input / output file is, with the **variables inside each** (field-by-field).

Deeper references: `../MAPPING_KNOWLEDGE.md` (instrument + code logic per stage),
`../WORKFLOW_MAP.md` (diagram), `../MAPPING_MECHANISM.md` (the s.26(1) deep trace).
