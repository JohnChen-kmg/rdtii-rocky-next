# Authoritative Round 1 numbers

Established 2026-09-10 by comparing every copy on disk. **Quote from this page, not from
memory and not from the older copies in `../RDTII Plan`.** Section 2 of the Stage 3 Word
template requires measured cost, and the secretariat verifies cost claims against the code.

## Corpus

The ledger that reconciles every version is `rdtii-rocky-finale/stages/p1-scrape/docs/CORPUS_VERSIONS.md`.

| | Value |
| :---- | :---- |
| Current documents | **2,673** (SG 536 · MY 869 · AU 1,268) |
| Manifest rows | **2,706** = 2,673 current + 33 superseded |
| Forms | 2,228 native PDF · 43 scanned PDF · 402 HTML |
| Corpus version | v2.4, 18 July 2026 |
| Raw size | about 1.85 GB including superseded files |
| Validation | 0 errors, 0 warnings across 2,706 rows |

Version history: v2.0 2,616 → v2.1 2,641 → v2.2 2,658 → v2.3 2,673 → v2.4 2,706 rows.
**Any figure of 2,616 or 2,641 is stale.**

## Provisions and results

| | Value |
| :---- | :---- |
| Provision records | **411,986** across 2,673 documents, v2.4 plus segmentation fix |
| Judged rows | SG 42 (30 NEW / 12 KNOWN) · MY 57 (46 / 11) · AU 43 (30 / 13) |
| NEW rows total | **106**, plus two explicit "no provision found" rows per economy |

Earlier record counts of 305,980 and 317,388 are the v2.0 and v2.1 figures. Both are stale.

## Cost — two ledgers, different scopes, do not add them casually

**Mapping and verification**, `submission/reports/cost_ledger.json`, refreshed 18 July after
the v2.4 AU re-map. Evidenced total **US$281.59**.

| Component | USD |
| :---- | ----: |
| SG mapping | 53.65 |
| SG verify | 14.44 |
| MY mapping | 24.01 |
| MY verify | 9.18 |
| AU mapping | 140.26 |
| AU verify | 36.05 |
| A/B tests | 4.00 |
| **Evidenced total** | **281.59** |

Three components are **disclosed as unevidenced**: `triage_haiku`, `rollup_framework_calls`
and `other`. The ledger's own policy is that the submission quotes only what it evidences and
never reconstructs a figure from memory. Keep that policy.

**Extraction**, measured separately in P2's own report: **US$130.44**, about 4.9 cents per law
at corpus v2.1, on Claude Haiku 4.5 via the Batches API across six itemized batches. A figure
of $107.29 is the superseded v2.0 number.

These two ledgers cover different stages, so neither is the pipeline total. There is no single
evidenced end-to-end figure for Round 1.

## What the finale needs that Round 1 did not have

- **One unified cost ledger**, per run and per engine, produced by logging without manual
  arithmetic. The rubric says so twice, and the live-test short note has a cost field per pass.
- **No unevidenced components.** Three disclosed gaps were acceptable in Round 1 and will read
  worse when cost is also recorded live on 15 October.
- **Portable evidence paths.** `cost_ledger.json` records its evidence as absolute paths into
  `C:\Users\woshi\Desktop\rdtii-p3-map\out\`, outside the repo. A reviewer cloning the public
  repo cannot follow them. Make the evidence trail repo-relative.

## Other measured claims

| Claim | Authoritative value |
| :---- | :---- |
| OCR character error rate | **0.00%** on the committed reference page, re-measured live by the demo command. Pilot pages 0.93% and 2.72%. Never claim a corpus-wide rate: only one document carries a real gold page, the rest are engine fixture estimates |
| Local fallback throughput | about 1 provision per second on one consumer GPU, measured, at US$0 |
| Cross-model reproducibility | citations, offsets and metadata byte-identical 309 of 309 across `qwen2.5:14b`, `llama3.1:8b` and Claude Haiku 4.5 |
| Scanned pages OCR'd | 12,292 in the full run plus 998 in the v2.1 delta, Tesseract 5.4 |
