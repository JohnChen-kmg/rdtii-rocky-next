# output/ — the built instrument (finale draft, 2026-09-13)

Status: **draft, validator green, not yet vendored** into `../p3-map/contracts/instrument/`.
The mapping stage still reads the Round 1 copy (nine indicators, legacy IDs) until its own
loader, prompt and hard-coded literals move to decimal IDs (finale plan steps 3B-3D).

| File | What it is | Made by |
| :---- | :---- | :---- |
| `indicator_order.yaml` | The one ordered list: 62 host IDs, 61 in scope (6.5 declared out), names, weights, host exception notes, the host's five mapping traps (template rows 79-85), practice-based and non-regulatory lists | `scripts/build_indicator_order.py` from `reference/OUTPUT_TEMPLATE_FINAL_ROUND.xlsx` |
| `indicators.yaml` | The codebook: one block for each of the 61 in-scope indicators, in host order, grouped by pillar. Each block's `tier` says how deep it goes (the top-level `tiers` key describes them). Tier A, 9: the pillar 6-7 blocks of the Round 1 codebook, migrated to decimal IDs and extended with the host trap rows. Tier B, 14: drafted at Tier A depth on 2026-09-13, **not yet reviewed**. Tier C, 38: extracted from the host methodology sheet, the Indicator Reference notes and the Guide's defining sentence, no traps | edited in place; `scripts/build_indicators_from_methodology.py` adds a Tier C block for any in-scope ID without one |
| `policies.yaml` | Cross-cutting rules: what counts as a measure (incl. host row 85, practice-based and non-regulatory rules), ID policy, citation contract, scoring policy (incl. economy-level 7.1/7.2), 12 edge cases | edited in place |
| `signatures/<ID>.yaml` | One retrieval signature per in-scope indicator (61), named by decimal ID: keywords, embeddable definition text, law types, scope patterns, negative signals, 400 curated exemplars in total | `scripts/build_signatures.py` from `scripts/data/*.yaml` |
| `gold/gold_set.jsonl` | Every coded host row, all pillars: 1,054 rows across 10 economies (Round 1 AU/MY/SG, Round 2 CN/IN/ID/LA/MN/RU/TH), with host verification data and label flags (suspect / advisory / host_marked / candidate), and `exemplar_for` | `scripts/build_gold.py` |
| `INSTRUMENT_NOTES.md` | Plain-language account (Round 1 pillars 6-7, plus a finale section) | edited in place |
| `VALIDATION_2026-09-13.txt` | Finale validator transcript: PASS, 61/62 in scope, exit code 0 | `scripts/validate_instrument.py` |
| `VALIDATION_2026-07-16.txt` | Round 1 validator transcript (9 indicators), kept as history | — |

**Regenerate** (after a source-workbook or data-file change), from the stage folder:

```
python scripts/build_indicator_order.py
python scripts/build_indicators_from_methodology.py            # adds missing Tier C blocks only
python scripts/build_indicators_from_methodology.py --check    # Tier C blocks against today's host sheets
python scripts/build_signatures.py
python scripts/build_gold.py
RDTII_GUIDE_TEXT=<page-numbered Guide text> python -X utf8 scripts/validate_instrument.py
```

Then, once the mapping stage is ready for decimal IDs, copy `output/*` to
`../p3-map/contracts/instrument/` and run the validator with `--require-vendored`.
When this stage folder is built outside the finale repo, set `RDTII_FINALE_REPO` to the repo root so
the validator can find the mapping stage's copies; otherwise it skips those two checks and says so.
The scripts find this stage folder themselves (`scripts/rdtii_examples.py`), so they also run when the
`scripts/` folder is kept beside it rather than inside it, as in the instrument workspace.
`indicators.yaml`, `policies.yaml` and `INSTRUMENT_NOTES.md` are edited in place; signatures, the gold set
and the order file are rebuilt by their scripts. To take an indicator deeper, edit its block and raise its
`tier`. No script rewrites an existing codebook block.
