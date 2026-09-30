# Deferred: set aside on 2026-09-22, not deleted

**Moved here so the corpus could focus on the national law database and the three key areas — CAC, MIIT and
Customs.** Nothing was deleted. Each folder keeps its files, its provenance sheet and its place in the manual/auto
split, and every source here stays on the watch list, so every run of the tool still says it is not being checked.

## What deferring costs

Measured from the breadth check (each source's indicators, aggregated from `CN_layer2_checklist.md`):

- The active layer 2 — CAC, MIIT, gov.cn, Customs — still serves **31 indicators**.
- **18 indicators are left with no active layer-2 source**, and fall back on layer 1 alone. For most of them the
  national database states the principle and not the number, so they become framework-only.
- **Only one of the 18 is in pillars 6 and 7: 7.5**, government access, whose procedure sits in MPS 令151. Layer 1
  answers pillar 7 in full on its own (5 of 5, `explore-2026-09-20/cn-china-coverage.md`), so 7.5 stays answerable.
- The other 17 are outside the automated pillars, which **decision (a) of 2026-09-20 already marks for a
  researcher's manual check**. Deferring them is consistent with that decision, not a new gap.

| Indicator | Its only sources, all deferred |
| :---- | :---- |
| 1.4 | MOF, MOFCOM |
| 2.3 | MOFCOM, NDRC |
| 3.2, 12.01 | NDRC |
| **5.3** | SASAC — the only lead for it anywhere |
| **7.5** | MPS (layer 1 still answers pillar 7) |
| 9.3, 11.1, 12.9 | SAMR |
| 10.1, 10.4 | MOFCOM |
| 11.4 | OSCCA, the standards platform |
| 12.4.2 | SAFE |
| 12.4.4, 12.4.5, 12.4.6, 12.4.7 | PBOC |
| 12.6 | MOF |

**If a live test draws one of these indicators, bring back its source first.** `watchlist.py <list> --indicator
<id>` names it.

## What is here

### `manual/` — to collect by hand, when brought back

| Folder | Publisher | Listed | Why deferred |
| :---- | :---- | ----: | :---- |
| `pboc-safe/` | 人民银行 + 外汇局 | 7 | PBOC's database is long and mostly irrelevant — monetary policy, banking supervision, credit. The 7 listed are payments only (12.4.x); if brought back, **take those 7, not the database** |
| `ndrc/` | 发展改革委 | 5 | Investment and procurement pillars, not 6 or 7. The negative list is still the only source for 3.2 and 12.01 |
| `mps/` | 公安部 | 2 | 7.5's procedure; layer 1 already answers pillar 7 |
| `nhc/` | 卫生健康委 | 2 | Health-data notices; CAC and layer 1 carry pillars 6 and 7 |
| `standards-idonly/` | GB/T | 6 rows | Identifiers only, never downloaded; 11.4 |

### `auto/` — partly collected; the tool resumes where each stopped

| Folder | Publisher | State when deferred | Relevant share |
| :---- | :---- | :---- | ----: |
| `samr/` | 市场监督管理总局 | **203 of 235 pages**, stopped 2026-09-22; no provenance sheet for that run yet | 18% |
| `mofcom/` | 商务部 | 160 of 160, complete; 512 files with attachments, 207 MB | 22% |
| `oscca/` | 国家密码管理局 | 12 of 12, complete | — |
| `mof-tariff/` | 财政部 + 关税税则委员会 | 5 of 5, complete — includes the ¥50 de minimis | — |
| `cnca/` | 认监委 | 2 of 2, complete; 52 attachment files, 77 MB | — |
| `sectoral/` | NPPA, NRTA, MCT, MOST, SASAC | 5 of 5, complete — **SASAC is the only lead for 5.3** | — |
| `gazette/` | 国务院公报 | index **stopped at 180 of 936 issues**, cache kept; recall check not run | discovery only |

Two things were never fetched and would be on the next run: **26 links recovered by the multi-link fix** of
2026-09-21 (OSCCA's second and third certification batches, MOFCOM's 2023 technology-catalogue base text, the
tariff plan's companion 税则, and others), and the rest of SAMR.

**The gazette is a discovery log, not a proxy for the law in force.** It gives a rule's text as issued — not
consolidated, no repeal status, possibly incomplete. If brought back, use it to find rules, and take their current
text from the national database or the ministry's own 现行有效 list.

## To bring a source back

```
python countries/cn-china/tools/collect.py samr               # continues here, in _deferred/auto/samr
python countries/cn-china/tools/collect.py gazette --list-only
```

The collector finds each source where it lives, so a run continues the deferred folder. **To make a source active
again, move its folder back** to `../manual/` or `../auto/` and change its row in `../README.md`.
