# Starting prompt — the interface, written 2026-09-29

Paste the block below into a fresh session opened in `C:\Users\woshi\Desktop\rdtii_rocky_finale_9.30`.
Written for an agent that has not seen this project.

---

You are building the interface for the RDTII finale submission, from scratch, tonight. The host's
deadline is **tomorrow, 30 September**. Three pipeline stages have closed and their output is waiting.

You are in `C:\Users\woshi\Desktop\rdtii_rocky_finale_9.30`, which is the submission repository. Build
in `interface\`. The release tag cut from this repository is what a marker deploys and what runs on
15 October, so what is in this tree is the submission and what is outside it is not.

## Read these first

| File | Why |
| :---- | :---- |
| `interface\DATA_PATHS.md` | The settings contract. Every data location is a setting, and this names them |
| `interface\fixtures\README.md` | The 60 real rows already in place, and the four traps they exercise |
| `C:\Users\woshi\Desktop\RDTII Finale Plan\finale_progress\UI_HANDOFF_p3-map_2026-09-29.md` | **The full data contract.** Every file, path, join key and column, written by the stage that produces them |
| `C:\Users\woshi\Desktop\rdtii-finale-4-dashboard\PLAN.md` | Fourteen work packages and a cut order, from 12 September. Its decisions are still live; its packages predate the rebuild decision |
| `C:\Users\woshi\Desktop\rdtii-finale-4-dashboard\DECISIONS.md` | Standard library only; the interface never edits the pipeline; secrets in memory only; review applies to run output and never to the frozen submission |

## Why this is worth 15 points, and which points

Seven checklist items and two rubric criteria rest on the interface, C3a at 10 and C3b at 5.

| Item | What it actually requires |
| :---- | :---- |
| **9** and **21** | The AI backend is **swappable from inside the interface, with no code or config change**, and a steward can watch the swap happen |
| **11** | The audit view is driveable by a **non-technical policy officer** |
| **18** | It deploys from the repository at the declared tag |
| **24** | A run starts **from a button**, progress is in plain words, review and export happen in the interface |
| **26** | Cache and downloaded-document folders are **clearable on screen** before the clock starts |
| **29** | It can be left available for the marking period |

**Read that list again and notice what is not on it: layout.** These are verbs, not screens. A page that
looks finished but cannot switch an engine scores less than a plain one that can. Build the verbs first
and in the order above, and stop when the night ends rather than leaving one half-built.

## The prior failure, which is the one to avoid

The old interface, `interface/dashboard.py` in the development repository, is 433 KB of single-file
standard library. It was written on 12 September against `work/p3out/map/verdicts_*` and
`work/p3out/ingest_report.json`. Mapping's directory layout, economy table and indicator scope then all
changed underneath it and nobody noticed. It also makes **34 references to the row files and zero to the
gloss files**, which is why a non-technical officer opening the China page today sees a Chinese quote
and no English.

So: **bind to the names in the handoff document, and read your data through the settings in
`DATA_PATHS.md`.** Fixtures are already in `interface\fixtures\` for exactly this reason. Point at them
by default, and at the real run through one setting.

## One thing in the old file is worth keeping

Items 9 and 21 need the model switchable from the browser. The obvious implementation, letting the page
post a name that the server puts in the environment, lets anyone who reaches the page set arbitrary
environment variables in a process that spends money and reads the corpus. The old file solves it with a
**server-side allowlist**: the browser may only name a choice from a fixed set, and only these names:

```
LLM_PROVIDER  LLM_MODEL  VERIFIER_MODEL  ESCALATION_MODEL  TRIAGE_MODEL
OLLAMA_MODEL  OLLAMA_HOST  OCR_ENGINE
```

Keep that shape. The UI names a choice, the server validates it against a list the server owns. Never
let the client supply the variable name, and never a value the server has not enumerated. Read the
offered engines from `stages\p3-map\config\llm\engines.json` rather than hardcoding them, so the declared
engines and the offered engines cannot drift apart.

## Seven things about the data that will bite you

1. **Timor-Leste appears twice.** `out/` holds the six-economy, nine-indicator arm; `out_tl52/` holds
   Timor-Leste against the other 52 indicators, in a directory with the **same file names**. Anything
   that globs `records_TL.csv` finds two different files. Read them as two arms and sum for any
   economy-level total: Timor-Leste's 110 rows are 27 plus 83.
2. **Scores are not in the rows.** They live only in `rollup/economy_scores_<E>.json`. And **7.1 and 7.2
   are inverted**: a score of 0 means the economy *has* a framework.
3. **A blank Discovery Tag is a deliberate value.** It means the row is neither a discovery nor a
   baseline reproduction. Do not render it as an error and do not coerce it to NEW.
4. **Indicator IDs are decimal text and must stay text.** The host's own formula in column O derives the
   pillar from them. Given `P6-I1` it returns a question mark and the Coverage Matrix then counts zero
   provisions for every economy. Keep `6.10` from becoming `6.1`. **Column O must stay empty** in our
   output, because it is the host's formula and a fifteenth data column overwrites it.
5. **An error row in `map/verdicts_<E>.jsonl` has only three keys**: `provision_id`, `economy`, `error`.
   Check for the error key before touching anything else.
6. **When a row looks wrong, `verify/verified_<E>.jsonl` is the file to read.** It carries the mapper,
   the verifier and the escalation reviewer, each with their own reason.
7. **`Full section text` in the workbook is not what the English column translates.** It is a wider,
   separate extract, and for Chinese it falls back to a window beginning 6,000 characters before the
   provision, which near the top of a short instrument is the document's first article. Do not build a
   side-by-side comparison on that column.

## The rule about translations, which is absolute

The quote is the evidence, byte-anchored to the stored text. **A translated string must never become a
`Verbatim Snippet`, in the screen or in any export.** Show the English beside the original, labelled
machine-made. The export writer never opens a gloss file and a test pins that, so do not route around it.

`audit/gloss_<E>.jsonl` glosses the quote and `audit/gloss_sections_<E>.jsonl` glosses the provision
text, both keyed on the provision. A gloss prefixed `[not literal — source text is garbled]` is the
glosser refusing to smooth over OCR damage. The flag rate is 0 to 13% on quotes, 10% for China, 39 to
43% for Timor-Leste and **96% for Lao PDR**. At 96% that flag has stopped discriminating and should be
shown as a property of the corpus, not as a per-row warning.

## The gap to close first

The existing audit view is 119 lines and renders five columns: indicator, law and section, score,
verification, and the evidence. **No English at all.** That is precisely what item 11 asks about. A
reviewer must be able to open a Chinese, Lao or Portuguese row and read what it says, with the original
beside it and the machine origin stated. Build that before anything cosmetic.

## What to deliver, in priority order

1. **It runs from this repository** with no absolute paths and no manual setup beyond the documented
   settings. Test it by pretending to be a reviewer who just cloned.
2. **Review a row and see the English.** Original and gloss side by side, labelled, with the score, the
   verification and the citation confidence visible.
3. **Switch the engine from the page**, through the allowlist, with the switch visible while it happens
   and the choice recorded in the run manifest.
4. **Start a run from a button**, with progress in plain words rather than log lines.
5. **Clear the caches and the downloaded documents from the page.**
6. **Export the rows** in the 14 columns, in the host's order, without touching column O.

## What not to do

- Do not edit anything under `stages\`. The interface never edits the pipeline.
- Do not write secrets to disk. They live in memory for the process lifetime.
- Do not let review alter the frozen submission rows. Review applies to run output, and a decision is an
  append-only record rather than an edit in place.
- Do not copy the old dashboard in. If any older interface ends up in this tree, the README and the Word
  document have to say which one a marker deploys, or the marks land on whichever a reviewer opens first.
- Do not invent data shapes. Everything you need is named in the handoff document and present in
  `interface\fixtures\`.

## Before you write code, tell me

Which of the six deliverables above you can finish tonight, in what order, and what you would drop
first. Then show me the one screen that closes item 11, because that is the gap with the most marks
behind it and the least code in front of it.
