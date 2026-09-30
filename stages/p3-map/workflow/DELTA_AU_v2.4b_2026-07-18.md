# AU re-map delta note — corpus v2.4b segmentation fix (2026-07-18, 2nd delta)

Second AU-only surgical re-run, after P2 hand-off #2's **segmentation fix**:
155 AU docs re-extracted (65 under-segmented + schedule-clause recovery +
principal acts). Corpus 392,181 → **411,986** records (SG 95,320 · AU 251,332 ·
MY 65,334). **SG/MY are byte-identical to v2.4** — enforced as a negative
control, not assumed. Only the 155 AU docs were re-scored. Full P2 notes:
`rdtii-p2-extract/docs/HANDOFF2_NOTES_2026-07-18b.md`.

## What ran

| step | result |
|---|---|
| Stale inventory | **3,186 mapped provisions / 957 verified fires / stale CSV rows** cited the 155 changed docs (fires P7-I5 540, P7-I2 213, P7-I3 102, P7-I1 69) |
| Rebuild S0–S2 (v2.4b) | 411,986 records, 100% byte-exact grounding, recall 1.0 (37/37) |
| Pair merge | v2.4 pairs for non-155 docs + fresh v2.4b pairs for the 155 (direct +2,058 / gray +5,991); **244 schedule-style `sch.` ids admitted**; preflight PASS, 0 phantoms |
| Triage (Haiku) | 5,991 new gray pairs → 2,266 keeps, $9.37 |
| Map (Sonnet, live) | 3,284 delta provisions, **2 residual schema errors** (below); credit ceiling hit twice mid-run → top-ups → clean resumes |
| Verify | +1,129 new fires judged; AU cumulative 2,827 fires / 1,025 overturned / $36.05 |
| Downstream | newknown / rollup / S9 / S10 / workbook / audit / URL-check regenerated |

## Acceptance (the named recoveries) — ALL PASS

- **APP 8 (P6-I4) — RECOVERED via the new schedule citation ✅.** The P6-I4
  KNOWN row now cites **`au-pa1988-001#sch.1 APP 8.2`** (Privacy Act 1988
  Schedule 1 Australian Privacy Principle 8.2), snippet *"the recipient of the
  information is subject to a law, or binding scheme, that has the effect of
  protecting the information…"*, matched to baseline **r1-au-037**. APP 8 is
  the baseline's canonical P6-I4 citation and was unreachable pre-fix
  (schedule text produced zero provisions). Bonus: P7-I1 KNOWN now cites
  `sch.1 APP 6.2`. **The `sch.` citation style flows end-to-end** (2 such rows
  in the judged CSV; audit-trio intact).
- **SOCI Act (au-scia2018-001) — RECOVERED ✅.** 1 → 719 provisions upstream;
  **191 verified-kept fires** now cite real sections (s.30AB, s.30AG, s.30AH,
  s.30AI, s.30CW…). The P7-I2 KNOWN row cites `s.30CW(4)`. **Zero synthetic
  `st.*` chunks** remain in the SOCI CSV rows (the earlier mangled
  `s.? [Part 2…]` synthetic row is gone; last delta's audit-trio drop of
  `au-scia2018-001#st.219` did not recur).

## Negative control — PASS

SG and MY `records_*.csv`, `records_*.json`, and `eval_report_*.json` are all
**byte-identical** to the pre-delta hashes (`out/delta_20260718b/inventory.json`
→ `negcontrol_baseline_sha`). SG/MY were never re-scored.

## Score movements — NONE

All nine AU scores identical to the v2.4 run (P6-I1 1.0 · P6-I2 1.0 · P6-I3 0 ·
P6-I4 1.0 · P7-I1 0 · P7-I2 0 · P7-I3 1.0 · P7-I4 0 · P7-I5 1.0). This delta is
a **citation-quality and evidence-recovery** improvement (APP 8 canonical
citation, SOCI real sections), not a scoring change. AU CSV stays 42 rows;
eval recall 0.889 (8/9), KNOWN-tag accuracy 1.0. The prior v2.4 findings hold
(P6-I1 escalation on My Health Records + CCA s.57DD; r1-au-043 DATA Act miss
unchanged — not in the 155).

## Honest correction + one citation flag for John (REVIEW_ITEMS §11)

Review-packet conflation #2, which I reported "resolved by v2.4", is **not
fully resolved** — the underlying matcher weakness persists and this delta
surfaced it. The fuzzy law-matcher scores "Telecommunications Act 1997" and
"Telecommunications (Interception and Access) Act 1979" as identical (both
reduce to the single shared token "telecommunication", ratio 1.0), so both
acts' P7-I3 fires tag KNOWN→r1-au-041. Curation fills r1-au-041's single KNOWN
slot with the best-ranked fire and this run chose **`au-ta1997-002 s.306(3)`**
instead of the baseline's actual **`au-ta1979-002 s.187C`** (which IS present,
KNOWN, verified `agree`). **Score-neutral** (P7-I3 = 1.0 either way), but the
judged citation differs from the baseline's canonical one. NOT auto-fixed: the
fix lives in shared curation logic and altering it risks the SG/MY negative
control this task requires. **John's curation call:** swap the r1-au-041 KNOWN
citation to `au-ta1979-002 s.187C(1)` (one-line edit; the fire is available).

## Disclosures

- **2 provisions permanently unmapped** after 3+ schema-forced retries:
  `au-pa1988-001#s.26WE(1)` (Privacy Act NDB scheme — NOT APP 8, no acceptance
  impact) and `au-tolaa2018-001#s.49B(2B)`. 2 of 3,284 delta provisions.
- Integrity: audit-trio 0 violations; URL liveness **94/94 green**
  (`out/urlcheck/submission_urls_2026-07-18.json`).
- Cost this delta ≈ **$80** (triage $9.37 + map delta ~$55.9 + verify delta
  ~$14.9); AU cumulative map $140.26 / verify $36.05; ledger evidenced total
  **$281.59** (`out/cost_ledger.json`). Credit ceiling hit twice mid-map;
  resumed clean after top-ups (no lost work).
- v2.4 AU artifacts preserved in `out/delta_20260718b/` for rollback.
