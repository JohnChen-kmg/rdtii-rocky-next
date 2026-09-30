# finale_progress

**What each stage of the final round delivered, in its own words, as it finished.**

One file per stage, written by the workshop that did the work, dated on the day it closed. A stage result says
what exists, where it is, how good it is, what the next stage inherits and what was deliberately not done — so the
next stage can start without reading the previous one's working notes.

This is not a plan and not an issue record. `3_Final_Stage/GAPS_AND_PLAN.md` is what we intend to do;
`3_Final_Stage/ISSUES/` is for cross-stage problems awaiting a decision. **This folder is what actually happened.**

| Stage | Result | Closed | Headline |
| :---- | :---- | :---- | :---- |
| p1 — collection (scraping) | `STAGE_RESULT_p1-scrape_2026-09-23.md` | 2026-09-23 | Six economies, **8,175 documents**, 9.6 GB. Five engine corpora plus China, which has a different shape by law rather than convenience. Three decisions passed to extraction: Lao PDR is 96% scans, China has no contract-shaped manifest, and ~220 documents across Malaysia and Timor-Leste are flagged as not being the law they are filed under |
| p2 — extraction (OCR + fields) | `STAGE_RESULT_p2-extract_2026-09-24.md` | 2026-09-24 | Six economies, **766,526 provisions**, contract 0.3.0, in `Desktop/rdtii-finale-handoff2/`. One 62-field shape for every economy; 18,000 records re-read from the frozen text on disk with 0 grounding mismatches. China's manifest was built here, and its provenance gaps are recorded rather than filled — a UTC retrieval instant exists for 6 of its 1,090 documents. Three things mapping must know before it starts: set `HANDOFF2_DIR` or it silently reads Round 1's July output, `laws.jsonl` is now one row per **act** and not per document, and the contract bump is not optional — the old vendored schema rejected every record this stage emits, including Singapore's |
| p3 — mapping (provisions to indicators) | `STAGE_RESULT_p3-map_2026-09-29.md` | 2026-09-29 | Six economies, **318 rows** (263 scored), in `Desktop/rdtii-finale-p3-runs/run_2026-09-27/`. Timor-Leste mapped against all **61 indicators**, so every pillar appears somewhere. All four host evidence items verified: decimal IDs, snippet + URL + article on every scored row, six economies, three non-English languages. ~$269 as of 29 Sep. Two things the next stage must fix before the tag: `final-submission` still points at **2026-07-20**, and the repo's `submission/` folder still ships Round 1's 13-column `P6-I1` rows, which would make the Coverage Matrix count zero provisions for every economy |

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
