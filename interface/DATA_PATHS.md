# Where the interface reads its data

Settled 2026-09-29. **The repository ships code, evidence and a small demo corpus. It does not ship the
corpora.** Those are outputs, they are 28 GB across three stages, and two single files in the extraction
hand-off exceed what GitHub accepts. So every data location is a **setting**, with a default that works
on a clean clone.

This matters beyond tidiness. The submission checklist allows settings to change on the day and does not
allow code to change. Anything the interface needs to point somewhere else on 15 October must therefore
be a setting, not a path in a source file.

## The settings, reusing the names the stages already read

Do not invent new names. Each of these is already read by a stage, so the interface and the pipeline
cannot drift apart.

| Setting | Points at | Default for a clean clone | On this machine |
| :---- | :---- | :---- | :---- |
| `HANDOFF1_DIR` | the crawler's corpus: `manifest.csv`, `law_table.csv`, `links_used/`, `raw/` | `demo_data/mini_raw` | `rdtii-finale-1-scraping\outputs\<CC>\<CC>_corpus_<date>` |
| `HANDOFF2_DIR` | extraction's output: `provisions.jsonl`, `laws.jsonl`, `doc_status.jsonl`, `source_text/` | *(demo run output)* | `rdtii-finale-handoff2` |
| `OUT_DIR` | **the mapping run the interface displays**: `submission/`, `rollup/`, `audit/`, `run_manifest.json` | `interface/fixtures` | `rdtii-finale-p3-runs\run_2026-09-27\out` |
| `INDEX_DIR` | the retrieval index, 2.7 GB, rebuilt not shipped | *(built on first run)* | `rdtii-finale-p3-runs\run_2026-09-27\index` |
| `INSTRUMENT_DIR` | the 61-block codebook | `stages/p0-instrument/output` | same, it ships |
| `BASELINE_PATH`, `BASELINE_R2_PATH` | the host's 2025 database, for NEW against KNOWN | **none.** A reviewer places their own copy | wherever your copy is |

**Two traps already caught elsewhere, and they apply here.**

`HANDOFF2_DIR` defaults to `../handoff2`, which on this machine still holds **Round 1's July output**:
411,986 provisions over three economies. Anything that reads it unset looks like it worked. Assert the
economy count at start-up rather than trusting the path.

Timor-Leste's other ten pillars are a **second** mapping tree, `out_tl52`, not a subfolder of the first.
An interface that reads only `OUT_DIR` shows Timor-Leste as a two-pillar economy.

## The engine switch is a setting too, and it is allowlisted

Items 9 and 21 require the model to be switchable from inside the interface with no code or config edit.
The server owns the list and the browser only names a choice from it. These are the only names the
browser may set, and only to values the server has enumerated:

```
LLM_PROVIDER  LLM_MODEL  VERIFIER_MODEL  ESCALATION_MODEL  TRIAGE_MODEL
OLLAMA_MODEL  OLLAMA_HOST  OCR_ENGINE
```

Never let the client supply the variable name, and never a value the server has not listed. Read the
offered engines from `stages/p3-map/config/llm/engines.json` rather than hardcoding them, so the
declared engines and the offered engines cannot diverge.

## What ships, and what a reviewer does instead

| | Ships | Why |
| :---- | :---- | :---- |
| The evidence rows, scores, audit views and glosses | **yes**, about 10 MB | This is the submission |
| Corpus manifests, law tables and link records | **yes**, about 80 MB if brought in | Describes every document without containing one, so provenance claims can be checked |
| `demo_data/` | **yes**, 18 MB | The thirty-minute deploy runs on this. Needs one non-English document added |
| Raw documents, the full provisions file, the retrieval index | **no** | 28 GB, regenerable, and two files exceed GitHub's per-file limit |

A reviewer with no corpus runs the demo chain. A reviewer with their own corpus sets `HANDOFF1_DIR` and
runs the pipeline. Neither needs anything this repository does not carry.

## A note on 15 October

The checklist says the declared tag is what runs on the day, and the short note carries a signed line
that the output was produced by the system frozen at that tag, which a steward initials. **Settings may
change on the day. Code may not.**

So the design rule tonight is to make every knob a setting: the data locations above, the engine names,
the worker counts, the economy and indicator scope, the cache locations. Then anything you want
different on 15 October is a settings change, which is allowed, rather than a code change, which is not.

One question is still unasked and would change this: **may the interface be updated between 30 September
and 15 October?** Worth sending tonight. The cost of asking is one email.
