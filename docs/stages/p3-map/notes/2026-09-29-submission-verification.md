# Submission verification against the host's 29-item checklist

29 September 2026, one day before the code freeze. Verified against
`OUTPUT_TEMPLATE_FINAL_ROUND.xlsx` and the repository itself, not against notes.

---

## 0. Two findings that outranked everything else — BOTH RESOLVED LOCALLY, 29 Sep evening

**Not yet pushed.** Everything below is committed on `finale` in the local clone; nothing has been
sent to GitHub. The push is the one step held for John, because it publishes to the repository the
host grades.

| was | now |
| :---- | :---- |
| `final-submission` pointed at 2026-07-20, 40 commits behind | **`finale-submission-2026-09-30`** created at `eb064ca`, an annotated tag whose message states the run, the contents and the known limitations. `finale` fast-forwarded 55 commits; trees identical to `w2-mapping-finale`; `p2-extract-contract-0.3.0` contained |
| `submission/` shipped Round 1: 13 columns, `P6-I1` IDs, AU/MY/SG only | **319 rows, six economies, 14 columns, decimal IDs**, one records file + one workbook + one audit page per economy, plus `OUTPUT_DATA_FILLED.xlsx` — the host's template with all 101 rows |

**One decision left for John:** `final-submission` still points at July. It was NOT moved, because
the declared tag has to match whatever the Word document says, and the Word document is not written.
Either declare `finale-submission-2026-09-30` in Section 1, or say the word and I will move
`final-submission` to the same commit. **Leaving two tags undeclared is the ambiguity that loses the
marks**, the same way two interfaces in one repo would.

---

## 0b. The original statement of those findings, for the record

### The release tag points at July

```
final-submission  ->  2ba4be2  "Pitch deck: final slide pass"   2026-07-20
```

Checklist item 2 reads: *"Final release tag recorded — **that exact tag is what will run on
15 October**."* The tag we hold is three months old and predates the entire finale. `finale` itself
is **40 commits behind** `w2-mapping-finale`, and neither `p2-extract-contract-0.3.0` (4 commits) nor
the instrument hand-off is merged into it.

**As it stands, the 15 October live test would run Round 1's code.** Nothing else on this checklist
matters more.

### `submission/` still ships Round 1's rows

`submission/records_{AU,MY,SG}.csv` carry **13 columns** and **`P6-I1`-style indicator IDs**. Filing
those would:

- make the host's Pillar formula in column O return `"?"` for every row, so the Coverage Matrix's
  `COUNTIFS($O$9:$O$109, 1, …)` counts **zero provisions for every economy** — failing item 15 and
  the sheet criterion C1a is read from;
- fail item 17 outright, because there is no column N at all;
- and omit China, Lao PDR and Timor-Leste entirely.

The 318 rows this run produced are in `rdtii-finale-p3-runs/run_2026-09-27/`, not in `submission/`.

---

## 1. The 29 items

`OK` verified today · `~` partly there · `TODO` not done · `LIVE` belongs to 15 October

### Repository (1–5)

| # | item | state |
| :-- | :---- | :---- |
| 1 | GitHub repo public and accessible | `~` remote exists (`JohnChen-kmg/rdtii-rocky-finale`); visibility unverified from here |
| 2 | **Final release tag = what runs on 15 October** | **`TODO`** — tag points at 2026-07-20 |
| 3 | LICENSE contains Apache 2.0 | **`OK`** verified |
| 4 | README follows `README_template_FINAL_ROUND.md`, every section | `~` README.md exists with Quick Start, Full Usage, Architecture; not yet diffed against the host template, which we hold |
| 5 | Quick Start reaches a working system in <30 min on a clean machine | `TODO` untested claim |

### Deployment (6–8)

| # | item | state |
| :-- | :---- | :---- |
| 6 | Deployment guide in the Stage 3 Word template, Section 1 | `TODO` — **we DO hold the template**: `RDTII Finale Plan/1_Rules/Final_Round/submission_template_stage3_v2_CLEAN.docx`. My earlier note that we lacked it was wrong |
| 7 | Someone who did not build it deployed from the guide alone, <30 min | `TODO` |
| 8 | Docker / Python requirements documented, no hardcoded paths | **`OK`** `requirements-demo.txt` present; grep finds no absolute Desktop paths in shipping code |

### Architecture (9–11)

| # | item | state |
| :-- | :---- | :---- |
| 9 | AI backend swappable from inside the interface, no code or config change | `~` `interface/dashboard.py` (433 KB, v3.16) gates `LLM_PROVIDER`, `LLM_MODEL`, `VERIFIER_MODEL`, `ESCALATION_MODEL`, `TRIAGE_MODEL`, `OLLAMA_MODEL/HOST`, `OCR_ENGINE` through `MODEL_ENV_ALLOWLIST`. Skeleton present; not exercised against this run's code |
| 10 | Zone 1 and Zone 2 separate, documented modules | **`OK`** `stages/p1-scrape` and `stages/p2-extract`, each with its own docs |
| 11 | Audit interface works, driveable by a non-technical officer | `~` dashboard exists; the claim is untested |

### Compliance (12–13)

| # | item | state |
| :-- | :---- | :---- |
| 12 | Core pipeline runs end to end on open weights alone | `~` engine B (`qwen2.5:14b`, digest-pinned) reproduced a Sonnet verdict on the canonical trap case; **never run end to end** |
| 13 | Dependencies with licences, Word Section 3 | `TODO` needs the Word template |

### Evidence (14–17) — all four verified today

| # | item | state |
| :-- | :---- | :---- |
| 14 | Output Data complete — IDs as text, snippets, live URLs | **`OK`** across 318 rows: every indicator ID matches `\d+(\.\d+)+`; every one of 263 scored rows has an Article/Section, a snippet and a URL; 14 columns. **But see §0 — this is in the run directory, not `submission/`** |
| 15 | Coverage Matrix shows three or more economies | **`OK`** six: China 55, Malaysia 53, Australia 39, Singapore 36, Lao PDR 25, Timor-Leste 110 |
| 16 | Both mandatory pillars covered | **`OK`** pillar 6 = 72 rows, pillar 7 = 163. And **all twelve pillars** appear, from the Timor-Leste widening |
| 17 | At least one non-English source in Language of Source | **`OK`** three: Chinese 55, Lao 25, Portuguese 110 |

### Interface (18–19)

| # | item | state |
| :-- | :---- | :---- |
| 18 | Interface deploys from the repo at the declared tag — C3a + C3b, **15 points** | `TODO` blocked by item 2 |
| 19 | 3–4 minute walkthrough recording | `TODO` |

### Live test (20–29)

| # | item | state |
| :-- | :---- | :---- |
| 20 | Two engines declared in the Word submission | `~` `config/llm/engines.json` declares A (Claude, pinned checkpoints) and B (`qwen2.5:14b`, pinned by digest); the Word document is not written |
| 21 | Engine switch made inside the interface, watchable | `~` dashboard skeleton |
| 22 | Second pass re-reads downloaded documents, fetching nothing | `~` resume logic exists in every stage; never demonstrated as a clean second pass |
| 23 | Engine Comparison sheet producible | `LIVE` the sheet says "completed during the live hour" |
| 24 | Run from a button, progress in plain words, review and export in the interface | `~` dashboard |
| 25 | Politeness ON by default — 1 req/s per site, robots.txt | **`OK`** scraping workshop's `POLICY.md` §5 and `CONVENTIONS.md`: robots.txt read, politeness "the engine's, never relaxed" |
| 26 | Cache and download folders clearable on screen | `~` dashboard |
| 27 | Cost recorded per run and per engine, in US dollars | **`OK`** every stage report carries `cost_usd`; `config/manifest.py` records the engine per run. Measured total to date **$263.44** |
| 28 | Ready for any of the nine economies and languages, in any pillar | **`OK` as of today** — `ECON_NAME` covers 13 economies, `ECONOMIES` scopes a run, `INDICATORS_SCOPE` reaches all 61 indicators, and the retrieval-leg guard refuses a non-English economy rather than silently returning nothing |
| 29 | Interface left available for the marking period | `TODO` deployment decision |

**Tally: 9 verified, 12 partial, 7 to do, 1 live-hour.** Mapping owns items 14–17, 27 and 28 — **all six are verified** — and contributes to 12, 20, 22 and 23.

---

## 2. What is left, in the order I would do it

### Before the freeze tomorrow

1. **Promote this run's output into `submission/`.** Replace the Round 1 CSVs with the 318 rows, all six economies, 14 columns, decimal IDs. Without this the evidence items fail however good the rows are. ~20 minutes, no cost.
2. **Merge and re-tag.** `finale` needs `p2-extract-contract-0.3.0` and `w2-mapping-finale` (which already carries the instrument hand-off through `ad27d1f`), then a new release tag. This is `PLAN.md` Block 0 step 3, and it decides what runs on 15 October.
3. **Diff the README against `README_template_FINAL_ROUND.md`** — we hold the template at
   `rdtii-finale-0-instrument/sources/host_finale_rules/`. Item 4 says "every section, not just Quick Start".

### Before 15 October, but after the freeze (settings and documents, not code)

4. **The Stage 3 Word document** — `1_Rules/Final_Round/submission_template_stage3_v2_CLEAN.docx`. Sections 1 (deployment guide), 3 (dependencies and licences) and 5 (the two engines), plus a **Live Test Readiness** table asking, per economy, which pillars and **languages** the system handles and whether it runs end to end. Section 5 cannot be corrected after the deadline.
5. **The interface walkthrough recording** (item 19) and the clean-machine deployment test (items 5, 7).
6. **One end-to-end run on engine B alone** (item 12) — currently proven on a single provision.
7. **A clean second pass** demonstrating nothing is re-fetched (item 22).

### Mapping's own remainder, all optional polish

8. C1 from the problems register — stage reports cross-checked against their own output, as gates.
9. The gazette-title refusal, and Timor-Leste's "Approves the Civil Code" no-provision citation.
10. Retry the 117 empty replies (~$1.90).
11. Block I — curating 101 rows from 318. **Selection is now the binding constraint, not retrieval.**

---

## 3. The submission package

### What the repository holds today

```
rdtii-rocky-finale/
  LICENSE                  Apache 2.0                          item 3  OK
  README.md                21 KB, Quick Start + Architecture   item 4  ~
  main.py                  51 KB — the CLI entry point: serve / demo / mini-run / quick / docs
  requirements-demo.txt                                        item 8  OK
  interface/
    dashboard.py           433 KB, single file, stdlib only, v3.16    items 9,11,21,24,26
    README.md  PLAN.md  CLAUDE.md  MIGRATION_NOTE.md
  stages/
    p0-instrument/         the codebook — 61 blocks as of today
    p1-scrape/             Zone 1                              item 10 OK
    p2-extract/            Zone 2                              item 10 OK
    p3-map/                mapping, 286 tests
  docs/                    CHANGELOG_FINALE, CODE_MAP, DATA, DISCLOSURES, WORKFLOW
  submission/              ** STALE — Round 1's 13-column rows **
  demo_data/  outputs/
```

### What `submission/` must contain

| | |
| :---- | :---- |
| `records_{AU,CN,LA,MY,SG,TL}.csv` | 14 columns, decimal IDs, 318 rows |
| `records_*.json` | the host's per-law JSON shape |
| `RDTII_P3_results_*.xlsx` | the per-economy audit workbooks |
| `economy_scores_*.json` | the rollup scores — supporting evidence; the workbook has no score column |
| the filled `OUTPUT_TEMPLATE_FINAL_ROUND.xlsx` | Output Data, Coverage Matrix; Engine Comparison and Run Record are filled in the live hour |
| `audit/` | the HTML audit views |

Two rows of that table are new decisions: whether Timor-Leste's two files are concatenated or kept
separate, and whether the rollup JSONs ship as supporting evidence (Round 1 did that, and the
workbook still has no score column).

### The interface

`interface/dashboard.py` is a 433 KB single-file stdlib-only dashboard, migrated from the Round 1
`rdtii-dashboard` repo on 10 September, first put under version control at v3.16. Its
`MIGRATION_NOTE.md` says what it already covers: engine switching from the UI through a server-side
allowlist, and an Ollama probe for the open-weights lane.

**Seven checklist items and 15 rubric points (C3a 10, C3b 5) rest on it**, and none of them is
verified against the code as it now stands. It has not been exercised since 10 September, while
mapping changed substantially underneath it — `main.py`'s economy table, the indicator scope, the
emit columns. **That gap is the largest unquantified risk in the submission**, and it is not a
mapping problem.

---

## 4. Do we need a start prompt for the next stage?

**Yes, and it is the natural next artefact.** Every stage in this workspace has had one —
`START_PROMPT_MAPPING_2026-09-24.md` is mapping's — and the next stage is not more mapping. It is
**submission assembly and the interface**: items 1–13 and 18–29, the Word document, the recording,
the clean-machine test, and the 101-row curation.

That stage has its own workshop already: `rdtii-finale-4-dashboard`.

What its start prompt has to carry, which nothing currently states in one place:

- the two findings in §0, because they are deadline-bound and neither is an interface task;
- that mapping is done and what it produced — 318 rows, six economies, 61 indicators, $263.44;
- the six evidence items mapping has already secured, so that stage does not re-litigate them;
- the seven items that rest on `dashboard.py` and the fact that it has not run against current code;
- the standing constraints, which do not change: no backward induction from the gold set, the
  original is the evidence, notes back to other workshops rather than edits;
- and the honest state of the problems register, so the next stage inherits the open items rather
  than rediscovering them.

---

## 5. What the template itself says, read cell by cell (added 29 Sep, evening)

Read out of `OUTPUT_TEMPLATE_FINAL_ROUND.xlsx` rather than inferred. Seven sheets: **Output Data**,
Indicator Reference, **Coverage Matrix**, Engine Comparison, Run Record, **Submission Checklist**,
Instructions. Three of those we fill, two are the live hour, two are reference.

### Decimal indicator IDs are confirmed by the host, and the cell help contradicts itself

The Instructions sheet: *"Write the RDTII 2.1 code exactly: 6.1, 6.4, 7.3, 12.3, 12.9. **Not
'P6-I1'**, not 'Pillar 6 Indicator 1'."* The example rows 7 and 8 use `6.4` and `7.4`. The column O
formula parses the integer part of a decimal.

**But cell E5's own help text still reads `e.g. "P6-I1", "P6_I2"`** — stale Round 1 wording the host
did not update. Anyone reading only the column header would file the legacy form and score zero on
the Coverage Matrix. Ours are decimal.

### Column E must be TEXT, and we are one of the few teams this can actually bite

The Instructions: *"Column E is formatted as text. This matters: entered as a number, 12.10 collapses
to 12.1 and 4.01 to 4.1, and the two are different indicators."*

We file **61 distinct indicator IDs**, and two of them are exactly the dangerous shape: **`4.01` and
`12.01`**. We also file `4.1` separately. So if column E is written numerically, `4.01` and `4.1`
merge into one indicator and a real row is lost. Whatever writes the Output Data sheet must write
these as strings into text-formatted cells, and the filled workbook must be re-read to confirm it.

### Curate from the 263 scored rows only — no no-provision rows

101 slots (rows 9 to 109, after deleting the example rows) against **318 rows = 263 scored + 55
no-provision**. Scored rows alone are 2.6x the slots, so no no-provision row needs to be filed.

That is not only a space argument. Columns I (Verbatim Snippet) and K (Source URL) are both
**REQUIRED**, and a no-provision row by construction has neither — ours carry "No provision found"
and an `n/a — N instruments searched` string. Round 1 filed them on the reading that the host wants
an explicit absence rather than a blank; the finale template says nothing about absence rows and does
say those two columns are required. With 2.6x the rows we need, the tension does not have to be
resolved: file findings.

### Other rules worth having in one place

| rule | source |
| :---- | :---- |
| **Delete example rows 7 and 8** before submitting | Instructions, GENERAL RULES |
| Data occupies rows 9–109 → **101 slots** | column O formulas |
| Do not rename or reorder columns; the secretariat validates against them | Instructions |
| No merged cells in the data area | Instructions |
| One row per provision; a provision touching two indicators gets two rows | Instructions |
| Column O is a formula — do not type in it, do not delete it | Instructions + N4 header |
| Mapping Rationale is **OPTIONAL**, max 300 chars, must name the legal mechanism | J5 |
| Confidence is optional, and *"flagging low confidence is treated as a strength"* | Instructions |
| Language of Source is *"the original language of the document, not the language you translated into"* | Instructions |
| Article / Section: *"a real act cited to the wrong section scores zero"* | Instructions |

That last line is why the multi-act citation caveat matters: it is the section that must be right,
and ours are — it is the act *name* that is in doubt.

### The Submission Checklist is a sheet we fill, and the host miscounts it

29 numbered items in the sheet; the Instructions sheet says *"Twenty-six items"*. The sheet is
authoritative. Columns `Status` and `Notes / evidence` are **both empty** — nothing is pre-filled.
Sections: Repository 5, Deployment 3, Architecture 3, Compliance 2, Evidence 4, Interface 2, Live
test 10 — which is exactly the grouping in §1 above, so the verification there maps onto it one to
one.

### Two things that shape curation rather than formatting

- **C1a:** *"Three or more diverse economies processed autonomously, with minimal reconfiguration
  between them. **Depth across three beats a thin pass over ten.**"* Six economies over 101 slots is
  about 17 rows each, which is depth. Spreading thinner to look broader would score worse.
- **The interface is a submitted deliverable**, not a file: *"the system a reviewer reaches by
  deploying your repository at the declared tag. C3a and C3b (15 points) are marked on it during the
  fortnight."* Plus a **3–4 minute screen recording of the audit view**, submitted with the Word
  document, which is *"the fallback if we cannot deploy your system from your guide."*

### The live test, for the record

One of nine economies whose 2025 database we hold — Thailand, Viet Nam, Indonesia, China, India,
Kazakhstan, Lao PDR, Mongolia, the Russian Federation — with one pillar and two indicators,
announced at the start of the hour. *"It may be a pillar you were never asked to work."* We hold
corpora for China and Lao PDR only; the retrieval-leg guard refuses a non-English economy rather
than returning nothing, and `ECON_NAME` covers all thirteen.
