# output/ — the built instrument (finale, as of 2026-10-04)

Status: **validator green.** Every in-scope indicator has a full-depth codebook block with the same
elements. The nine pillar 6-7 blocks are the Round 1 codebook, used in the Round 1 run and the
30 September submission. The other 52 blocks are drafts: cited and machine-checked, **not yet reviewed
by a person**, and not yet used in a filed run. The mapping stage reads a vendored copy of this folder
at `../p3-map/contracts/instrument/`.

| File | What it is | Made by |
| :---- | :---- | :---- |
| `indicator_order.yaml` | The one ordered list: 62 host IDs, 61 in scope (6.5 declared out), names, weights, host exception notes, the host's five mapping traps (template rows 79-85), practice-based and non-regulatory lists. Every entry also carries the coverage marks: `coverage` (9 automated, 52 manual, 6.5 excluded), `coverage_reason` and `answer_nature`. The mapping stage's automated set is the entries marked `automated` | `scripts/build_indicator_order.py` from `reference/OUTPUT_TEMPLATE_FINAL_ROUND.xlsx` and `scripts/data/coverage.yaml` |
| `indicators.yaml` | The codebook: one block for each of the 61 in-scope indicators, in host order, grouped by pillar, each pillar under a banner saying where its measures live. Every block carries the same keys (the top-level `block_fields` key lists them and says which the mapping prompt renders). Tier A, 9: the pillar 6-7 blocks. Tier B, 52: every other indicator, drafted at Tier A depth (14 on 2026-09-13, 38 on 2026-10-04). No Tier C block at present | edited in place; `scripts/build_indicators_from_methodology.py` adds a Tier C block for any in-scope ID without one |
| `policies.yaml` | Cross-cutting rules: what counts as a measure (incl. host row 85, practice-based and non-regulatory rules), ID policy, citation contract, scoring policy, 12 edge cases. Its last section, `indicator_sets`, lists the inverted, economy-level, practice-based and non-regulatory indicators for programs to read | edited in place |
| `signatures/<ID>.yaml` | One retrieval signature per in-scope indicator (61), named by decimal ID: keywords, embeddable definition text, law types, scope patterns, negative signals, 401 curated exemplars in total | `scripts/build_signatures.py` from `scripts/data/*.yaml` |
| `gold/gold_set.jsonl` | Every coded host row, all pillars: 1,054 rows across 10 economies (Round 1 AU/MY/SG, Round 2 CN/IN/ID/LA/MN/RU/TH), with host verification data, label flags (suspect / advisory / host_marked / candidate; reviewed flags carry `basis`) and `exemplar_for` | `scripts/build_gold.py` from the workbooks and `scripts/data/label_flags.yaml` |
| `INSTRUMENT_NOTES.md` | Plain-language account. Sections 1-7 are narrative; sections 8-10 (one line per indicator, where each pillar's evidence lives, reviewed flags) are generated | narrative edited in place; generated part by `scripts/build_notes.py` |
| `VALIDATION_2026-10-04.txt` | Validator transcript after the 4 October round: PASS, 61/62 in scope, tiers A 9 / B 52, exit code 0 | `scripts/validate_instrument.py` |
| `VALIDATION_2026-09-13.txt`, `VALIDATION_2026-09-27.txt` | Earlier finale transcripts, kept as history | — |
| `VALIDATION_2026-07-16.txt` | Round 1 validator transcript (9 indicators), kept as history | — |

**What a block carries.** Rendered into the mapping prompt: `id`, `name`, `question`, `definition`,
`scoring`, `scoring_tree`, `coding_rules`, `exceptions`, `disambiguation`. Not rendered: `weight`,
`scoring_features`, `guide_examples`, `null_statement`, `sources`, `review_status`, `review_notes`, and
the marks `polarity` (inverted: an absent framework scores 1), `level` (economy: answered once per
economy) and `framework_name`. Never render `review_notes`: it holds open questions, not host text.

**Regenerate** (after a source-workbook or data-file change), from the stage folder:

```
python scripts/build_indicator_order.py
python scripts/build_indicators_from_methodology.py            # adds missing Tier C blocks only
python scripts/build_indicators_from_methodology.py --check    # Tier C blocks against today's host sheets
python scripts/build_signatures.py
python scripts/build_gold.py
python scripts/build_notes.py
RDTII_GUIDE_TEXT=<page-numbered Guide text> python -X utf8 scripts/validate_instrument.py
```

Then copy `output/*` to `../p3-map/contracts/instrument/` and run the validator with
`--require-vendored`.
When this stage folder is built outside the finale repo, set `RDTII_FINALE_REPO` to the repo root so
the validator can find the mapping stage's copies; otherwise it skips those two checks and says so.
The scripts find this stage folder themselves (`scripts/rdtii_examples.py`), so they also run when the
`scripts/` folder is kept beside it rather than inside it, as in the instrument workspace.
`indicators.yaml`, `policies.yaml` and the narrative of `INSTRUMENT_NOTES.md` are edited in place;
signatures, the gold set, the order file and the generated part of the notes are rebuilt by their
scripts. No script rewrites an existing codebook block. When a block's `polarity` or `level` changes,
update `indicator_sets` in `policies.yaml` to match; the validator fails if they differ.
