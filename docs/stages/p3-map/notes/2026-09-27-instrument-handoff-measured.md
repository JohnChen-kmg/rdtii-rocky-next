# Block C measured before the copy: what the instrument hand-off does and does not change

27 September 2026. Every number here was measured by loading the workshop instrument
(`rdtii-finale-0-instrument/instrument/output`) beside the vendored Round 1 one, through the
stage's own `config.instrument.load(dir)` and `INSTRUMENT_DIR`. Nothing was copied to get them.
Probes: `evidence/probes/handoff_probe.py`, `handoff_queries.py`, `handoff_substantive.py`.

## 1. The hand-off is retrieval-neutral

All nine query documents are **byte-identical** across the hand-off (sha256 of each, 9/9 match).

| | vendored (Round 1) | workshop (shipping) |
| :---- | :---- | :---- |
| vintage | legacy | decimal |
| blocks | 9 | 61 |
| automated set | 9 | **the same 9** - 6.1-6.4, 7.1-7.5 |

So the index (767,105 rows), the dense top-K and the 46,494 selected pairs all stay valid. The
top-K recompute that `PLAN.md` Block A budgeted for is **not needed**. The reason the queries do
not move is that `build_queries()` uses name + definition_text + keywords + two exemplar impacts,
and those fields are unchanged; what the hand-off rewrites is the *judging* text.

## 2. The automated set is entirely Tier A

All nine are `tier: A`. The hand-off's open decision "review of the 14 Tier B drafts"
(`HANDOFF.md`, when-to-hand-off item 2) therefore **cannot touch a filed row**. That precondition
is clear for mapping's purposes; it still matters for the instrument's own submission.

## 3. Every one of the nine judging blocks changes - and every change tightens

Per block, 12-13 shared fields. After normalising away the two edit classes that cannot change a
judgement - the ID form (`P6-I4` to `6.4`) and added source citations (`(Guide p.50)`) - what
survives is 18 substantive field changes:

| cell | substantive fields | what actually changed |
| :---- | :---- | :---- |
| 6.1 | 2 | precedent note now cites the workbook row; trap restated, same rule |
| 6.2 | 2 | **new trap**: a duty to keep books or records with no requirement about *where* is not 6.2 |
| 6.3 | 3 | **new trap**: network-security / access-control rules for licensees are not infrastructure |
| 6.4 | 2 | `scoring_tree` clarified: personal data scores 1 "regardless of whether horizontal or sector-specific" (makes explicit what `coding_rules` already said) |
| 7.1 | 2 | **new rule**: economy-level. "Per-provision citations of a data-protection act tagged 7.1 are not discoveries and score zero" |
| 7.2 | 2 | **new rule**: the same, for a cybersecurity act. Sectoral instruments are recorded but the horizontal act controls the score |
| 7.3 | 3 | **new trap**: a "prescribed period" with no number, a notification deadline or an appeal window is not a retention rule |
| 7.4 | **0** | nothing substantive |
| 7.5 | 2 | **new trap**: not generic inspection of business records by a regulator, and not a secrecy duty with a court-order carve-out |

**No rule is reversed.** Every substantive change either adds a citation or adds a trap that
narrows what counts. That direction matters: a reused row cannot have been made *wrong* by a rule
flip, but it can now be a row the shipping codebook scores **zero**.

This also settles a question `PLAN.md` H3 left as inference. The per-provision 7.1/7.2 filter is
no longer our reading of the methodology - it is the shipping codebook's own sentence.

## 4. Consequence: F2 is scoped too narrowly

`PLAN.md` Block F2 budgets "the 6.2 re-judge: 22 filed provisions, cents". Measured against the
142 rows the reuse path carries (Round 1 SG/MY/AU):

| cell | SG | MY | AU | all | exposure |
| :---- | ---: | ---: | ---: | ---: | :---- |
| 6.1 | 1 | 1 | 2 | 4 | citation only |
| 6.2 | 3 | 10 | 9 | 22 | new trap |
| 6.3 | 1 | 1 | 1 | 3 | new trap |
| 6.4 | 4 | 9 | 2 | 15 | scoring clarified |
| 7.1 | 1 | 1 | 1 | 3 | already compliant - exactly one row per economy |
| 7.2 | 4 | 4 | 4 | 12 | **not compliant** - four rows per economy |
| 7.3 | 13 | 12 | 11 | 36 | new trap |
| 7.4 | 4 | 3 | 1 | 8 | nothing |
| 7.5 | 11 | 16 | 12 | 39 | new trap |
| **all** | | | | **142** | |

- **100 rows** sit in a cell that gained a new trap (6.2, 6.3, 7.3, 7.5). 7.3 and 7.5 are the bulk,
  and both new traps are aimed precisely at the false positive those cells attract.
- **7.1 is already right**: one row per economy, citing the comprehensive act's scope provision.
- **7.2 is not**: four rows per economy. Two of each four are provisions of the *same horizontal
  act* (2 x Cybersecurity Act 2018 for SG, 2 x Cyber Security Act 2024 for MY and AU) - those are
  what the new rule zeroes. The others are sectoral acts (Electricity Supply Act 1990, Security of
  Critical Infrastructure Act 2018), which the codebook keeps as recorded rows.
- **12 rows need nothing** (7.4 entire, plus 6.1).

So the re-judge is ~115 rows, not 22. At the measured $0.016/provision live and $0.0088 batch that
is **about $1.84 live or $1.01 batch** - the cost is not the obstacle; the scope statement was.
Filing a row the shipping codebook scores zero is exactly what H3 exists to prevent, so this is
the same work, correctly sized.

## 5. Verified in advance, without copying

`INSTRUMENT_DIR` pointed at the workshop output, full suite:

| instrument | result |
| :---- | :---- |
| vendored (Round 1) | 215 passed, 11 skipped |
| workshop (shipping) | **218 passed, 8 skipped**, 0 failed |

Four `test_coverage.py` tests go from skipped to passing - the M8/M9 notification marks need
`indicator_order.yaml`, which only the decimal vintage carries. One test starts skipping with the
reason it was written for: `test_instrument.py:175`, "hand-off done - both copies are the decimal
vintage". The remaining skips are the absent hand-off corpus at the default path, unrelated.

`indicator_ids.py` differs between repo and workshop **only in line endings**; content is
identical, which is what `HANDOFF.md`'s line-endings section anticipates.

## 6. What the copy would delete

Only the nine legacy signature files, in each of the two mirrored directories:
`signatures/P6-I1.yaml` through `signatures/P7-I5.yaml`. Nothing else in either target is absent
from the workshop. All 30 tracked files under those paths are committed, so the mirror is
recoverable with `git checkout`. The repo is on branch `w3-instrument`, cut from
`w2-mapping-finale` at `994a6d0`.

The copy itself was refused by the sandbox as irreversible local destruction, both with `/MIR` and
with a non-deleting `/E`. It is waiting on the user.

## 7. Not done, and why

- **`code/scripts/data/`** (3 files, 216K: `signature_spec.yaml`, `curated_exemplars.yaml`,
  `guide_refs.yaml`) is inside the `code\scripts\` mirror the hand-off prescribes, and the build
  scripts need it to regenerate the instrument. `curated_exemplars.yaml` holds host workbook rows,
  so it falls under open **host question 10** - the same category as the gold set the repo already
  tracks. Flagged, not decided.
- **B10, leave-one-economy-out** (`prefilter/queries.py`): measured scope is **one cell**. 6.3's
  first two exemplars are CN and RU, so China's 6.3 query carries a description of a specific
  Chinese law and its gov.cn URL, drawn from the host's Round 1 workbook (its AU sibling still
  carries `provenance: {workbook: round1, sheet: Australia, row: 36}`). This is **pre-existing** -
  the vendored instrument has the same six exemplars - so the hand-off neither creates nor worsens
  it, and CN's pillar 6 already carries the manual-check sentence (M8/M9, `PORTAL_TIER_GAPS`).
  It is still a code fix, so it cannot be made in October. Making the query economy-aware turns
  9 query documents into 9 x economies, which invalidates the selected pairs and needs a top-K
  recompute per economy - cheap in compute, but it re-opens selection.
