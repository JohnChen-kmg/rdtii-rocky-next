# Mapping prompt prefix sizes — measured 2026-09-13

Command: `python -X utf8 scripts/measure_prefix.py` in the worktree stage (`rdtii-rocky-finale-w3/stages/p0-instrument`).
It renders the finale codebook exactly as `stages/p3-map/src/p3map/mapping/prompt.py:build_system_prefix()`
renders the Round 1 codebook today (same header, same kept keys, `yaml.dump` sorted, width 100),
once per pillar and once for all 61 indicators. Characters, not tokens.

| Prefix | Indicators | Tiers | Characters |
| :---- | ----: | :---- | ----: |
| Pillar 1 | 1 | C | 10,065 |
| Pillar 2 | 3 | B C | 17,374 |
| Pillar 3 | 5 | B C | 16,631 |
| Pillar 4 | 7 | B C | 19,486 |
| Pillar 5 | 6 | B C | 17,627 |
| Pillar 6 | 4 | A | 19,842 |
| Pillar 7 | 5 | A | 20,902 |
| Pillar 8 | 4 | B | 22,917 |
| Pillar 9 | 3 | B C | 19,921 |
| Pillar 10 | 4 | C | 12,727 |
| Pillar 11 | 4 | C | 13,084 |
| Pillar 12 | 15 | B C | 29,070 |
| **All 61 in one prefix** | 61 | — | **122,681** |

Reference points:
- Today's nine-indicator prefix: **25,974** characters (decision D3, measured in Round 1).
- D3's projection for one 61-indicator prefix: **about 176,000**. The measurement is 122,681, lower because
  38 indicators are Tier C and carry no traps or examples.

What it means for decision D3 (per-pillar prefixes):
- D3's target was "each pillar prefix at or below today's nine-indicator prefix". **Eleven pillars meet it;
  pillar 12 (29,070) does not.** Pillar 8 (22,917) is close.
- 8,815 characters of every prefix are the shared header, definitions and cross-cutting policies (measured by
  rendering with no indicator blocks). Per-pillar prefixes repeat that block twelve times; a single prefix carries it once.
- The single prefix is 4.7× today's. Whether per-pillar calls or one cached prefix is cheaper depends on how
  candidates spread across pillars per provision, which this measurement cannot show. Settle it with a small
  mapping run once the mapping stage reads decimal IDs.
