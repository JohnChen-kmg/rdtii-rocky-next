# finale_progress

**What each stage of the final round delivered, in its own words, as it finished.**

One file per stage, written by the workshop that did the work, dated on the day it closed. A stage result says
what exists, where it is, how good it is, what the next stage inherits and what was deliberately not done — so the
next stage can start without reading the previous one's working notes.

This is not a plan and not an issue record. `3_Final_Stage/GAPS_AND_PLAN.md` is what we intend to do;
`3_Final_Stage/ISSUES/` is for cross-stage problems awaiting a decision. **This folder is what actually happened.**

**In this repository** the folder is `docs/stage_results/`, a copy of the planning folder's `finale_progress`.
The plan named above is `docs/planning/GAPS_AND_PLAN.md` and the issues are in `docs/issues/`. A result is
copied here as written and is not edited afterwards, so a figure in an early result may be superseded by a
later one: the addendum the mapping workshop added to its result after 29 September, for example, is not in
this copy, and its final figures are in `README.md` and `submission/reports/`.

| Stage | Result | Closed | Headline |
| :---- | :---- | :---- | :---- |
| p1 — collection (scraping) | `STAGE_RESULT_p1-scrape_2026-09-23.md` | 2026-09-23 | Six economies, **8,175 documents**, 9.6 GB. Five engine corpora plus China, which has a different shape by law rather than convenience. Three decisions passed to extraction: Lao PDR is 96% scans, China has no contract-shaped manifest, and ~220 documents across Malaysia and Timor-Leste are flagged as not being the law they are filed under |
| p2 — extraction (OCR + fields) | `STAGE_RESULT_p2-extract_2026-09-24.md` | 2026-09-24 | Six economies, **766,526 provisions**, contract 0.3.0, in `Desktop/rdtii-finale-handoff2/`. One 62-field shape for every economy; 18,000 records re-read from the frozen text on disk with 0 grounding mismatches. China's manifest was built here, and its provenance gaps are recorded rather than filled — a UTC retrieval instant exists for 6 of its 1,090 documents. Three things mapping must know before it starts: set `HANDOFF2_DIR` or it silently reads Round 1's July output, `laws.jsonl` is now one row per **act** and not per document, and the contract bump is not optional — the old vendored schema rejected every record this stage emits, including Singapore's |
| p3 — mapping (provisions to indicators) | `STAGE_RESULT_p3-map_2026-09-29.md` | 2026-09-29 | Six economies, **318 rows** (263 scored), in `Desktop/rdtii-finale-p3-runs/run_2026-09-27/`. Timor-Leste mapped against all **61 indicators**, so every pillar appears somewhere. All four host evidence items verified: decimal IDs, snippet + URL + article on every scored row, six economies, three non-English languages. ~$269 as of 29 Sep. Two things the next stage must fix before the tag: `final-submission` still points at **2026-07-20**, and the repo's `submission/` folder still ships Round 1's 13-column `P6-I1` rows, which would make the Coverage Matrix count zero provisions for every economy |
| p0 — instrument (codebook), progress | `PROGRESS_p0-instrument_2026-10-04.md` | not closed; as of 2026-10-04 | **All 61 indicators at pillar 6–7 depth** (tiers A 9, B 52, C 0; it was 9 / 14 / 38 at submission), in `Desktop/rdtii-finale-0-instrument/instrument/output/`. The 52 new blocks are drafts no person has read. Pillar 6–7 prompt byte-identical. Not in any repo yet: the hand-off to `rdtii_rocky_next` is rehearsed (mapping 450 and interface 216 tests pass before and after) and waits on the developer. Mapping must read `framework_name` before the eleven new economy-level indicators score |
| interface — RDTII Rocky, progress | `PROGRESS_interface_2026-10-05.md` | not closed; as of 2026-10-05 | A window of its own, results filed by economy and source, a model per mapping step, a table of runs in every Output, hand collection without a source, a cost report with a calculator. **291 tests** (94 on 1 October), in `Desktop/rdtii_rocky_next/`, pushed to the private repository `rdtii-rocky-next`. One fault found and repaired on the day: every crawl had ended as failed since 4 October. `CODE_MAP.md`, `DATA.md` and the interface's own documents rewritten for this tool. Open: no comparison of two engines' runs, no hosted model called from the page since the rework, no second machine; the recording was re-made at about six minutes |

Two things have changed since the rows above were written. The two faults the mapping row names were
repaired before the release of 1 October: the tag was made on that release, and `submission/` holds the
finale's 14-column rows. And the instrument's hand-off the fourth row waits on was made on 4 October: the 61
blocks are in `stages/p0-instrument/output/` (`docs/CHANGELOG_FINALE.md`, 2026-10-04).

The interface's two earlier reports, a stage result and a progress report of 1 October, are in the planning
folder and are not in this repository; the report of 5 October follows them and stands on its own.

## Companion documents

Not stage results, so not in the table above, but they live here because the stage that wrote them is the
stage that owns the facts in them:

| Document | For whom | What it carries |
| :---- | :---- | :---- |
| `UI_HANDOFF_p3-map_2026-09-29.md` | whoever designs the interface | the exact data contract mapping produces -- every file, path, join key and column -- plus the seven checklist items and 15 rubric points that rest on the UI, and the known-bad rows it must not present as sound. Written because the previous interface was built against paths that then changed underneath it without anyone noticing |

## The rule for these files

A stage result is written **from the files, not from memory**: every count in it can be checked against a manifest,
an audit or a log in the stage's own repository, and it says where. A result that cannot be checked is a claim, and
claims belong in the plan, not here.

The engineering documentation stays with the code. These are summaries for the people downstream.
