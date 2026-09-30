# AU re-map delta note — corpus v2.4 multi-volume fix (2026-07-18)

Surgical re-run after P2 hand-off #2 repaired the AU multi-volume truncation:
33 AU acts were volume-1-only in every earlier corpus and are now complete
under new `-002` doc_ids; the truncated `-001` extractions are retired. Only
the 33 acts were re-scored — every other AU row and all SG/MY rows are
byte-identical to the 2026-07-15 corpus (do-not-rescore rule honoured).

## What ran (all $0 except the LLM stages)

| step | result |
|---|---|
| Corpus rebuild S0–S2 on v2.4 | 392,181 records, 100% byte-exact grounding, organic recall 1.0 (37/37) |
| Stale inventory (step 1) | **1,178 mapped provisions / 267 verified fires / 16 judged CSV rows** cited retired `-001` docs → marked stale (`out/delta_v24/stale_inventory.json`) |
| Pair merge (step 3) | AU 15,391 pairs = 9,750 v2.3-kept (retired dropped) + 5,456 `-002` added; preflight PASS, 0 phantoms |
| Triage (Haiku) | 4,189 new gray `-002` pairs → 1,453 keeps, $6.56 |
| Map (Sonnet, live) | 2,123 `-002` provisions, **0 residual errors** after retries; +324 new fires; ~$35 (credit exhaustion mid-run required a top-up + resume — see cost note) |
| Verify (Haiku+Opus) | 494 new fires judged (602 overturned across the full AU set), $21.16 cumulative |
| Downstream | newknown / rollup / S9 / S10 / workbook / audit / URL-check all regenerated |

Per-indicator stale fires re-scored: P7-I5 **219**, P7-I3 **42**, P6-I2 **5**,
P6-I3 **1** (the truncated volumes were heaviest in retention + government-access text).

## Acceptance (the named casualties)

- **r1-au-041 P7-I3 — RECOVERED ✅.** Now KNOWN, matched to
  `au-ta1979-002#s.187C(1)` (Telecommunications (Interception and Access)
  Act 1979), snippet *"ending 2 years after the closure of the account to
  which the information or document relates"*, Notes "matches baseline
  r1-au-041". Its pre-v2.4 absence was the corpus defect, exactly as the
  hand-off predicted — not a mapping miss. **This also resolves review-packet
  conflation #2**: the old run matched r1-au-041 to the wrong statute
  (Telecommunications Act 1997 s.306A(4)) because the correct TIA Act 1979
  Part 5-1A text was truncated; the correct provision is now present.
- **P7-I5 — RECOVERED ✅.** au-ta1979-002 now contributes **173 verified-kept
  P7-I5 fires** (interception/access regime complete through Chapter 5) and
  au-ta1997-002 **6** (Part 14 carrier-assistance — ss.313 and 314 mapped;
  s.315(1), the companion no-civil-liability clause, exists in the corpus but
  was not admitted as a P7-I5 candidate — not an obligation, no score impact).
- **r1-au-043 P7-I5 (Data Availability and Transparency Act 2022) — still a
  miss, unchanged.** au-data2022-001 is NOT one of the 33 retired docs; both
  its fires remain verifier 2-of-3 overturns (a precision call, not a corpus
  gap). Disposition unchanged from the 16 Jul review packet.

## Score change (v2.3 → v2.4): AU P6-I1 0.5 → 1.0 — FLAG FOR JOHN

Escalation clause fired on **2 distinct verified sectoral half-point measures**:
- `au-mhra2012-001#s.77(2)` — My Health Records Act (present pre-v2.4)
- `au-cca2010-002#s.57DD(3)` — **new, recovered from the complete CCA 2010**
  (Part IVE Motor Vehicle Service and Repair Information Sharing Scheme was in
  the truncated volume 2). Text: *"A person must not do anything that might
  reasonably enable the sensitive information to be accessed outside Australia
  by the data provider, or any other person"* (civil penalty). A genuine
  sectoral offshore-access prohibition — verified tiebreak_upheld at 0.5.

This is the SAME judgment-call family as the three-economy P6-I2 escalation
(REVIEW_ITEMS §5): sectoral 0.5 measures rolling up to 1.0 under the clause.
It is defensible on the clause's plain text, but if John suppresses the
sectoral-escalation reading for P6-I2 he should suppress it here too — with
only two measures, dropping either returns AU P6-I1 to 0.5. **Drafted as a
divergence for John's decision, not asserted.** No other indicator score
changed.

## Integrity

- All 20 `-002` rows in the judged CSV cite `-002` provision_ids (0 miscited);
  audit-trio (snippet + section + URL) intact on every scored row; 0 violations.
- URL liveness: 92/92 green (`out/urlcheck/submission_urls_2026-07-18.json`).
- Eval: recall 0.889 (8/9), KNOWN-tag accuracy 1.0. CSV 40 → 42 rows.
- v2.3 AU artifacts preserved in `out/delta_v24/` for provenance/rollback.

## Cost note (honest)

The `-002` mapping hit the API credit ceiling mid-run (~750/2,123 provisions);
John topped up and the resume finished it cleanly. AU cumulative map cost is
$84.40 (batch + this live delta); this v2.4 delta added ~$35 map + $6.56
triage + ~$9 verify ≈ **$50**. Ledger figures remain artifact-backed
(out/cost_ledger.json to be refreshed at final packaging).

## One process bug found + fixed (disclosed)

The first `-002` map pass logged 714 "record-missing" errors: retired `-001`
provisions were still present as keeps in `haiku_results.jsonl` (the pair
merge cleaned the selection files but not the triage file), so the mapper
re-proposed dead provisions. They produced no fires and no rows (error rows
are skipped downstream) — zero score impact — but the stale keeps and error
rows were purged so the run is clean. Root-caused, not papered over.
