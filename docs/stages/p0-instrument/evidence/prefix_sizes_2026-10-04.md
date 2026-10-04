# Mapping prompt prefix sizes — measured 2026-10-04

Characters, not tokens. Two measurements, after every indicator outside pillars 6 and 7 was brought to
pillar 6-7 depth (decision D15).

## 1. With the mapping stage's own prompt code

Command, run from `<finale repo>/stages/p3-map` at commit `b4d3cde` (branch `w2-mapping-finale`), with
`INSTRUMENT_DIR` pointing at this workspace's `instrument/output`:
`python -X utf8 <workspace>/drafting/2026-10-04/snapshots/render_prefix.py <out.txt>`. It calls
`src/p3map/mapping/prompt.py:build_system_prefix()` and changes nothing in the repo. `INDICATORS_SCOPE`
selects the indicators.

| Scope | Indicators | Before (instrument of 13 Sept) | After (4 Oct) |
| :---- | ----: | ----: | ----: |
| Default automated set: pillars 6 and 7 | 9 | 31,929 | 31,929 |
| Every indicator outside pillars 6 and 7 | 52 | 99,567 | 298,967 |
| 10.1 and 10.2 | 2 | not measured | 22,101 |
| 3.1 and 3.5 | 2 | not measured | 21,819 |
| 12.4.1 and 12.4.4 | 2 | not measured | 19,530 |
| 8.1 and 8.2 | 2 | not measured | 18,822 |
| 5.3 and 5.7 | 2 | not measured | 18,605 |

- **The pillar 6-7 prefix is byte-identical before and after** (SHA-256 begins `aac9dd69f874cea5` both
  times; the two files were also compared byte for byte). The saved renders are
  `drafting/2026-10-04/snapshots/prefix_p67_before.txt` and `prefix_p67_after.txt`.
- **A two-indicator scope, the live test's shape, is smaller than the pillar 6-7 prefix.**
- **A run over all 52 other indicators in one prefix is three times its earlier size.** The new blocks
  average about 5,400 characters of rendered rule text against 2,560 for a pillar 6-7 block.

## 2. With the instrument's own script

Command: `python -X utf8 code/scripts/measure_prefix.py`. It renders the same header and the same keys
per block, once per pillar and once for all 61 indicators.

| Prefix | Indicators | Tiers | Characters |
| :---- | ----: | :---- | ----: |
| Pillar 1 | 1 | B | 15,094 |
| Pillar 2 | 3 | B | 23,987 |
| Pillar 3 | 5 | B | 38,717 |
| Pillar 4 | 7 | B | 50,316 |
| Pillar 5 | 6 | B | 41,954 |
| Pillar 6 | 4 | A | 19,842 |
| Pillar 7 | 5 | A | 20,902 |
| Pillar 8 | 4 | B | 26,972 |
| Pillar 9 | 3 | B | 28,796 |
| Pillar 10 | 4 | B | 33,189 |
| Pillar 11 | 4 | B | 32,261 |
| Pillar 12 | 15 | B | 87,016 |
| All in one prefix | 61 | — | 322,081 |

- The shared header (score polarity, shared definitions, cross-cutting policy) repeats in every
  prefix, so the per-pillar figures do not add up to the single-prefix figure.
- Decision D3 targeted per-pillar prefixes no larger than the Round 1 nine-indicator prefix (25,974
  characters at the time). Pillars 3, 4, 5, 8, 9, 10, 11 and 12 now exceed it; pillar 12 is 87,016.
  A scope narrower than a pillar is the way to stay small.
- 13 September figures for comparison: all 61 in one prefix 122,681; pillar 12 alone 29,070.
