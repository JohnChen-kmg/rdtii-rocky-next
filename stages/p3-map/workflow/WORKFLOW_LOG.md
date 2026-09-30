# RDTII P3 — Workflow log (2026-07-14 → 2026-07-15)

The complete record of how the mapping pipeline was designed, verified, built, and
run: what happened in each phase, why, what was measured, what it cost, and where
the artifacts live. Companion docs: the design rationale lives in
`docs/MAPPING_FRAMEWORK_RESEARCH_2026-07-14.md`; per-run artifacts in `out/`.

---

## 0 · The task

Map every extracted legal provision (Singapore · Australia · Malaysia) to the 9
RDTII 2.1 regulatory indicators (P6-I1…P6-I4 cross-border data flows; P7-I1…P7-I5
data protection & cybersecurity), blind-verify every verdict, tag findings
NEW/KNOWN against the official Round-1 baseline, document Malaysia baseline
errors, and emit the judged 13-column CSV + JSON with a full audit trail.
Round-1 submission: **20 Jul 2026**. Budget agreed: **$150–260 expected, $400
hard ceiling**, nothing API-billed before the key was funded.

```
corpus (319,026 provisions, byte-grounded)
   │ S0 ingest ($0)          gate: byte-exact grounding
   │ S1 prefilter ($0)       BM25 + dense embeddings, indicator-as-query
   │ S2 selection ($0)       RRF + per-cell caps → direct 9,750 / gray 29,250
   │ S3 triage               gray band → survivors        [A/B-gated: Haiku, $44.54]
   │ S4 mapping (Sonnet)     schema-forced verdicts + trap checks
   │ S5 blind verify         Haiku re-judges blind; Opus tiebreaks
   │ S6 rollup (pending)     economy-level P7-I1/P7-I2 calls
   │ S7 NEW/KNOWN (pending)  3-tier diff vs baseline
   │ S8 MY error-check (pending)
   └ S9/S10 CSV + eval (pending)
```

---

## 1 · Framework research (overnight 2026-07-14, $0)

Deep-research pass over every official RDTII document (guide, internal guide,
assignments + answer key, 59-slide deck, baseline database, templates) and the
delivered corpus. Produced `docs/MAPPING_FRAMEWORK_RESEARCH_2026-07-14.md`:

- **Part 1 — the instrument**: verbatim scoring rules for all 9 indicators, the
  12-trap catalog (ban-vs-conditional, max≠min retention, gov-data exception,
  inverted P7-I1/I2 polarity, enforced-only, escalation clause…), host worked
  examples, baseline anatomy incl. the wrong "Indicator Reference" template tab.
- **Part 2 — the workflow**: the 11-stage funnel above, sized by a measured
  full-corpus keyword scan (not assumptions); 6 design tensions resolved with
  named losing alternatives; cost model; cost-scaling story (caps → distillation
  → content-addressed deltas → steady-state $5–20/economy/yr).
- **Part 3 — external tools & prior art**: MLEB-based embedding evidence,
  metadata-prefixed embedding, adopt/consider/reject table, novelty claim (no
  published LLM automation of RDTII-style legal coding found).
- 8 open questions for the builder.

Key design decisions settled in discussion: batch-first + local-triage budget
profile; two A/Bs before any bulk spend; local models never map or verify.

## 2 · Corpus verification & upstream deltas (2026-07-14 → 15, $0 in P3)

Three corpus generations, each audited by P3 before use:

| Version | What changed | P3 verification result |
|---|---|---|
| v2.0 (305,980 prov / 2,616 docs) | initial delivery | 3-agent crawl-sufficiency audit: **acts-only corpus**, 0 subsidiary/regulator instruments, SG Cybersecurity Act stale, AU SOCI unusable (1 provision), only 4/14 NEW leads present → wrote the 20-item delta-crawl request (`docs/DELTA_CRAWL_REQUEST_2026-07-14.md`) |
| v2.1 (317,388 / 2,638) | P1/P2 re-run, +25 MY acts | SG CA2018 consolidated ✓, MY PDP Amendment Act (DPO/breach/s.129) in-corpus ✓; funnel re-measured; schema change caught (`doc_status.jsonl`) |
| v2.2+v2.3 (319,026 / 2,673) | 18 delta items + 15 discovery instruments (P1 regulator sweep) | **32 instruments adversarially verified by two 15/17-agent workflows** (verdict tables §3.4b/§3.4c): e.g. MAS TRM = guidance-only (never controlling), MY Exemption Order exempts 9 hyperscalers from Act 854 (double-edged NEW), S678/2025 premium NEW with in-text commencement; AU SOCI still broken (P2 lane issue) **but full text recovered in source_text** |

Caution triage (§3.4d): every "missing" section of the 7 thin-extraction docs
verified present in raw source text → build rule: those docs get a source_text
candidate pass + curation quotes ground against source text. Source audit:
**100% of 2,673 documents on official government hosts**; secondary sources were
discovery leads only, never evidence.

## 3 · Phase A build (overnight 15 Jul, ~00:00–02:40, $0)

| Stage | Built | Measured gate |
|---|---|---|
| T0 | git repo, config spine (`config/settings.py`), CLI, README, CUDA env, `requirements.lock` | `version` prints CONTRACT_VERSION 0.2.0 |
| S0 `src/p3map/ingest.py` | streams provisions.jsonl; Tier-1 grounding; schema sampling; source_text chunks (629) for the 7 thin docs | **100% byte-exact on 319,026 records; 0 schema failures; 15 s** |
| S1 sparse `prefilter/bm25.py` | bm25s, indicator-as-query from vendored signatures | 22 s; canonical s.26(1) → P6-I4 rank 39 |
| S1 dense `prefilter/dense.py` | BGE-M3 on RTX 4070 Ti SUPER, resume-safe memmap | 83.7 min **after a 50× fix: max_seq_length 8192→512** (was 7 rows/s) |
| S2 `select.py` | RRF fusion + soft hint boosts + Appendix-A per-cell caps; organic recall gate | direct 9,750 / gray 29,250 pairs; **recall 1.0 (37/37, allowlist OFF)** after 2 fixes: `PREFILTER_FLOOR` recalibrated 0.008→0.0001 (RRF scale); absence rows excluded from denominator *except* inverted-polarity P7-I1/I2 |
| Baseline parser `discovery/baseline.py` | Round-1 country sheets → JSONL | 51 P6/P7 rows = gold distribution exactly (AU 11 / MY 26 / SG 14) |
| S3 local `triage/local.py` | qwen2.5:14b lenient screen, checkpointed | 29,250 pairs, 4.65 h, $0, 4,814 keeps (19%) — later superseded by the A/B verdict |

## 4 · The A/B tests (15 Jul, ~$4)

Pre-registered decision rules, then measurement:

**A/B-1 — local triage vs Haiku (200 stratified pairs, $0.31).**
Local false-negative rate **16%** vs gate <5% → **FAIL** → Haiku triage replaces
local verdicts. Executed immediately: 29,250 pairs, 12 workers, 63 min,
**$44.54, 5,762 keeps (20%), 0 errors** (`out/triage/haiku_results.jsonl`).
The local run cost $0 and bought the measured evidence.

**A/B-2 — Haiku vs Sonnet mapper (150 SG provisions, 384 verdict pairs, $3.69).**
Agreement 93.2% (pass) but Haiku verbatim-quote grounding **43.4%** vs required
98% (Sonnet 91.3% on the same strict check) → **clear FAIL** → Sonnet-first.
Disagreement pattern: Haiku systematically under-includes (misses framework-
existence and DPIA evidence) — the expensive error class.
Report + examples: `out/ab/ab_mapper_report.json`.

## 5 · Singapore slice, end-to-end (15 Jul)

**S4 mapping** (`mapping/runner.py`, Sonnet live, cached instrument prefix):
- Prompt: byte-stable 25,974-char system prefix rendering the full vendored
  instrument; schema-forced verdicts whose field order encodes the coder's
  procedure (core legal question → trap booleans → per-candidate verdicts).
- 3,295 provisions / 4,938 pairs in ~52 min total, **$53.19** (cache reads 38.4M
  tokens — caching is what makes the unit cost $0.016/provision).
- **1,210 fires; 11 ungrounded quotes (0.9%); 2 unrecoverable schema errors (0.06%)**.
- Mid-run fix: 211 truncation failures → output budget scaled by candidate count
  + retry + error-row-retrying resume; 209/211 recovered.
- Fire profile: P6-I1 0 (correct — SG has no ban) · P6-I4 14 (all score 1) ·
  P7-I3 125 · P7-I5 422 · P7-I2 559 (mostly framework-exists evidence) ·
  22 provisions flagged not-in-force by the trap check.
- Canonical trap held: s.26(1) → P6-I4 applies (1, Horizontal, 0.95, grounded);
  P6-I1 rejected with "conditional path exists — not a per se ban."

**S5 blind verify** (`verify/blind.py`, Haiku blind + Opus tiebreak, 2-of-3):
- 272 of 1,210 fires verified before **API credits ran out**: 152 agree,
  120 tiebreaks, 63 overturned (panel cutting false fires — mostly P7-I1/I2
  evidence-vs-operative line, resolved by design at the S6 rollup), 0 splits.
- Remaining 938 fires retry with one command post-top-up.

**Result views** (regenerate anytime):
- `out/audit/index_SG.html` — filterable per-fire evidence table (T4 artifact)
- `out/results/RDTII_P3_results_<ECON>.xlsx` — per-economy review workbook.
  Format contract (iterated with John 2026-07-15, do not regress): row-1
  wrapped explanation banner on EVERY sheet (indicator sheets: 4 bullets —
  what it measures / how mapped / traps); one sheet per indicator + Summary +
  All fires + 3 QA sheets; columns incl. Source URL, Enacted, Last amended,
  Crawled, and Full-section-text (source-text extraction snapped to
  section-heading boundaries); narrow unwrapped Segoe-UI cells, frozen
  banner+header. Full spec: `.claude/skills/results-workbook/SKILL.md`;
  exporter: `src/p3map/output/excel_export.py`.

## 6 · Cost ledger (all measured, none estimated)

| Item | USD |
|---|---|
| P3 A/B tests (both) | 4.00 |
| Haiku gray-band triage (A/B-1 fallback) | 44.54 |
| SG mapping (Sonnet, live, cached) | 53.19 |
| SG verification (partial, 272/1,210) | 2.90 |
| **Spent** | **≈ 104.6** |
| Remaining: SG verify rest (~$12) + AU/MY batch mapping (~$65–75) + AU/MY verify (~$25) + rollup/buffer (~$15) | ~115–130 |
| **Projected total** | **≈ 220–235** (envelope $150–260 · ceiling $400) |

## 7 · Current state & what's next — SUPERSEDED, see §9

(Kept as the 15 Jul snapshot.) Top-up landed 16 Jul; everything below
happened — the running record continues in §9.

1. Resume SG verification (one command, ~$12). ✅ done, $11.54
2. Build S6 economy rollup + S7 NEW/KNOWN 3-tier diff + S8 MY error-check +
   S9 13-column CSV writer + S10 eval vs gold (code, $0). ✅ built + audited
3. AU/MY bulk mapping via Batch API (−50%), overnight 16→17 Jul. ✅ fired 16 Jul
4. NEW-row human review (John) 18–19 Jul; submission 20 Jul.

## 8 · Where everything lives

| What | Where |
|---|---|
| Design & verification record | `docs/MAPPING_FRAMEWORK_RESEARCH_2026-07-14.md` (§3.4b–d = instrument verdicts) |
| Delta-crawl request & status | `docs/DELTA_CRAWL_REQUEST_2026-07-14.md` |
| Overnight build report | `docs/MORNING_REPORT_2026-07-15.md` |
| Pipeline code | `src/p3map/` (ingest · prefilter · select · triage · mapping · verify · discovery · output) + `config/` |
| Stage artifacts & reports | `out/` (ingest_report · select/ · triage/ · ab/ · map/ · verify/ · audit/ · results/) |
| Indexes (rebuildable) | `data/index/` (embeddings 625 MB · bm25_top · dense_top · corpus) |
| Git history | 12 commits, each stage gated & documented |

## 9 · 16 Jul — SG complete · audit hardening · AU/MY batch runs

**SG finished end-to-end.** Verification resumed post-top-up: all 1,210
fires judged (399 overturned — the precision layer working), $14.44 total.
Downstream chain produced the 42-row CSV (0 audit-trio violations), recall
0.846 vs gold (both misses documented in REVIEW_ITEMS: Banking Act model
split; Employment Act minimum lives in uncrawled subsidiary regs), scores
matching baseline except the flagged P6-I2 escalation finding.

**Independent-audit pre-flight fixes, all landed + committed:** (1) phantom
st.* ids root-caused as ingest's §3.4d synthetic source-text chunks;
`preflight.py` now gates every batch (39,000 pairs, 0 phantoms) and the
submission writer re-anchors st.* fires by quote byte-position with a hard
audit-trio validator; (2) map/verify reports made merge-cumulative, SG
backfilled from JSONL ground truth with costs recovered from archived run
logs (`logs/run_evidence/`); (3) `chain.py` enforces S5→S7→S6→S9→S10 and
rollup reads `verified_*.jsonl` directly — SG reconciled exactly (811 kept
fires); (4) AU/MY sizing from measured rates → John chose the Batch API
route.

**Batch lane** (`mapping/batch_runner.py`): same prompt/schema/model/row
shape as the live runner, transport = Message Batches (−50%, ≤24h SLA,
cache best-effort). Preflight PASS → AU fired first (4,310 provisions,
2 batches), then MY (2,523, 1 batch).

**MY complete (~40 min end-to-end).** Batch cleared in 10 min: 2,523/2,523
succeeded, $19.36; 204 truncation-class validation failures retried live
(+$4.63) → 1 permanent schema error (`my-pdpgdbn2025-001#st.10`). 807 fires
→ blind verify $9.18 (281 overturned, 0 splits/errors) → 57-row CSV,
recall 0.727 (0.889 on gold rows whose docs actually parsed — 4 misses cite
the two parse_failed 2017 CoPs; 2 are PDPA score-0 context rows, s.129
filed P6-I4-vs-baseline-P6-I2). New headline finding: **MY P6-I2 escalates
to 1.0 on 12 distinct verified tax-record-localization laws** — the same
judgment call as SG's item 1, now in two economies (REVIEW_ITEMS §5).
Matcher fix en route: light plural stemming (Services↔Service) repaired two
false NEW tags / eval misses; SG artifacts re-run and byte-identical.

**Cost ledger v2 (measured):**

| Item | USD |
|---|---|
| P3 A/B tests (both) | 4.00 |
| Haiku gray-band triage | 44.54 |
| SG mapping (live, cached) | 53.19 |
| SG verification (1,210 fires, complete) | 14.44 |
| MY mapping (batch 19.36 + live retries 4.63) | 23.99 |
| MY verification (807 fires) | 9.18 |
| **Spent** | **≈ 149.3** (+ cents of rollup framework calls) |
| Remaining: AU batch mapping (~$25–40 est) + AU verify (~$12–15 est) | ~40–55 |
| **Projected total** | **≈ 190–205** — inside the $150–260 envelope |

**In flight:** AU batches processing; on landing → live retry of error rows
→ `chain AU` → workbook + audit page. Then: MY error-check substance
cross-refs, curation with John 18–19 Jul, submission 20 Jul.

## 10 · 16 Jul (late) — AU complete: ALL THREE ECONOMIES DONE

**AU batch landed** after 215 min in queue (3,278/3,278 succeeded; the
1,032-request sibling had cleared in ~15 min). Batch lane $40.89; 367
truncation-class validation failures retried live over three passes
(+$7.8) → 4,308/4,310 provisions, 2 permanent schema errors (both
surveillance acts, REVIEW_ITEMS §8). 1,204 fires, 19 ungrounded.

**AU verify $15.64** (15.5 min): 409 agree / 795 tiebreaks / **455
overturned (37.8%)** / 0 splits / 0 errors → 749 kept. Chain → 40-row CSV
(1 audit-trio drop: SOCI synthetic chunk), **recall 0.889 (8/9), KNOWN-tag
accuracy 1.0**. The one miss (DATA Act 2022 → P7-I5) is a verifier
2-of-3 overturn, not a retrieval gap — include-with-note decision queued.
Scores: P6-I1 0.5 (My Health Records class, matches baseline's own
precedent) · **P6-I2 1.0 via escalation on 10 distinct verified laws — the
finding now appears in ALL THREE economies** (SG 3 / MY 12 / AU 10;
REVIEW_ITEMS §5 = the headline curation decision) · P7-I1/I2 0.0
(frameworks exist: Privacy Act 1988, Cyber Security Act 2024) · P7-I4 0.0
(no DPO mandate) · P7-I3/P7-I5 1.0.

**Error-check substance evidence banked:** the mapper independently ruled
MY PDPA s.10(2) a maximum-retention rule (trap check
retention_is_minimum=False, FAQ-trap rationale) — the refutation quote for
SUSPECT baseline row r1-my-053.

**Cost ledger v3 (final shape, all measured):**

| Item | USD |
|---|---|
| P3 A/B tests (both) | 4.00 |
| Haiku gray-band triage | 44.54 |
| SG mapping (live, cached) + verify | 67.63 |
| MY mapping (batch+retries) + verify | 33.17 |
| AU mapping (batch+retries) + verify | 64.34 |
| **Spent — three economies end-to-end** | **≈ 213.7** |

Inside the $150–260 envelope; ceiling $400 never approached. Per-economy
marginal cost (batch lane, mapping+verify): **MY $33 · AU $64** — the
scaling-story numbers for the submission (SUBMISSION_NOTES.md).

**Remaining to submission (20 Jul):** John's curation decisions
(REVIEW_ITEMS §1–8, chiefly the three-economy P6-I2 escalation call) ·
manual anchors for 3 dropped premium rows · combined Output-Data workbook
with traceable-changes coloring · README polish · pitch deck · demo video.

## 11 · 16 Jul (follow-up audit) — last-mile closure

A second independent audit listed 9 last-mile gaps; all closed same day
(commits eefdc5c, 34533d8 + this one). Mapping logic, verification
verdicts, and scores untouched throughout.

1. **Host JSON fields**: records_<ECON>.json rows now carry
   source_pdf_path / ocr_quality_cer / processing_time / model_version /
   raw_context (raw upstream values, nulls honest — 2 real OCR CER values
   ride through on MY), restructured as laws[] grouping provisions[].
   CSV columns verified byte-identical.
2. **Hold-out robustness**: ECON_NAME.get + tolerated missing inputs +
   corpus-law fallback URL; tests/test_holdout_smoke.py PASSES (fake
   economy → 9 valid no-provision rows, no crash, no empty URL).
3. **No-provision rows to contract §6**: Article/Section "n/a", governing
   law name+number+ONE official law-level URL (also replaced the MY rows'
   university-mirror PDF with lom.agc.gov.my), reason in Notes.
4. **URL liveness GREEN**: 92 unique URLs / 0 failures
   (out/urlcheck/submission_urls_2026-07-16.json). Root cause of the 3
   initial failures was OURS: S9's whitespace collapse squashed
   significant double spaces in LOM portal filenames. URLs now exempt.
5. **S8 re-run** against the live 57-row MY submission; Main-CSV crossref
   populated on all 68 check rows.
6. **Never-mapped provisions**: my-pdpgdbn2025-001#st.10 and
   au-sda2004-001#s.27KE(1) recovered (clean verdicts, zero new fires).
   **DISCLOSURE: `au-slaa2021-001#s.63AD(4C)` (Surveillance Legislation
   Amendment (Identify and Disrupt) Act 2021) remains unmapped after 7
   schema-forced attempts — the model repeatedly emits malformed
   trap_checks on this provision. 1 provision of 319,026 (0.0003%);
   AU P7-I5 scores 1 on many other verified fires, so no score impact.**
7. **Cost ledger** (out/cost_ledger.json): **$169.70 evidenced** across 7
   components, each with its evidencing artifact path. THREE components
   have NO surviving machine artifact and are null+disclosed: the
   production Haiku triage run (the $44.54 in §4/§6 is a dated run-time
   prose observation — kept as the session account, quoted nowhere as an
   evidenced figure), rollup framework calls (never metered; cents), and
   misc. The submission quotes only ledger-evidenced figures.
8. **Review packet** (workflow/REVIEW_PACKET_2026-07-16.md): all 29 KNOWN
   rows audited — 2 conflations found (MY GP 3/2025 hidden-as-KNOWN under
   the PDPA baseline row; AU Telecommunications Act 1997 matched to the
   TIA Act 1979 gold row) → retag-NEW candidates; ISA 2016 s.51(3)
   CONFIRMED against the official AGC PDF (mandatory "shall be sent to
   and kept at a place in Malaysia" proviso, criminal penalty); 4 drafted
   divergence rationales (3× P6-I2 escalation + AU P7-I2 CSA-2024
   post-dates-baseline); all 9 eval-miss dispositions machine-verified.
9. **Hygiene**: map_report counters labeled cumulative-across-retries;
   MY eval report carries a resolvability_note (parsed-doc recall
   16/18 = 0.889); doubled cost_note deduped.

Definition-of-done check: S9+S10 regenerated ×3 (42/57/40 rows, recalls
0.846/0.727/0.889, zero validator violations) · JSON six-field/per-law
shape machine-validated (0 violations) · CSV columns byte-identical ·
S8 re-run · URL report green · cost ledger written · review packet
committed.

## 12 · 18 Jul — corpus v2.4 AU multi-volume re-map (surgical)

Hand-off #2 (corpus v2.4) repaired the AU multi-volume truncation: 33 AU
acts were volume-1-only in every earlier corpus, now complete under `-002`
doc_ids (114,536 records vs 41,381 truncated — 2.8× growth; corpus
319,026 → 392,181). Surgical re-run of ONLY the 33 acts; all other AU rows
and all SG/MY rows untouched. Full detail: workflow/DELTA_AU_v2.4_2026-07-18.md.

- **Stale inventory:** 1,178 mapped provisions / 267 fires / 16 CSV rows
  cited retired `-001` docs (P7-I5 219, P7-I3 42, P6-I2 5, P6-I3 1).
- **Rebuild + merge:** v2.4 indexes (byte-exact PASS, recall 1.0); pairs
  = 9,750 v2.3-kept + 5,456 `-002`; preflight PASS. Triage 1,453 keeps
  ($6.56). Map 2,123 `-002` provisions, 0 residual errors (credit ceiling
  hit mid-run → top-up → clean resume). Verify +494 fires.
- **Acceptance:** r1-au-041 P7-I3 RECOVERED (KNOWN via au-ta1979-002
  s.187C(1)) — corpus defect confirmed, not a mapping miss; also resolves
  review-packet conflation #2. P7-I5 recovered (au-ta1979-002 173 kept
  fires through Ch.5; au-ta1997-002 ss.313/314 carrier-assistance).
  r1-au-043 miss unchanged (DATA Act not in the 33; verifier overturn).
- **Score change:** AU **P6-I1 0.5 → 1.0** — complete CCA 2010 surfaced a
  second verified sectoral offshore-access ban (s.57DD(3)); escalation
  clause. Flagged for John (REVIEW_ITEMS §9) as the same call as P6-I2.
- **Integrity:** all 20 `-002` CSV rows cite `-002` ids; audit-trio 0
  violations; URL 92/92 green; eval recall 0.889 / KNOWN-tag 1.0.
- **Process bug fixed:** 714 first-pass "record-missing" errors were stale
  `-001` keeps left in haiku_results.jsonl (merge cleaned selection files
  but not triage) — purged; zero score impact; disclosed not papered over.

## 13 · 18 Jul — corpus v2.4b AU segmentation-fix re-map (2nd surgical delta)

P2 hand-off #2 re-extracted 155 AU docs (65 under-segmented + schedule-clause
recovery). Corpus 392,181 → 411,986. Second AU-only surgical re-run; SG/MY
enforced byte-identical. Full detail: workflow/DELTA_AU_v2.4b_2026-07-18.md.

- **Inventory:** 3,186 mapped provisions / 957 fires cited the 155 docs
  (P7-I5 540, P7-I2 213, P7-I3 102, P7-I1 69).
- **Rebuild + merge:** v2.4b indexes (byte-exact PASS, recall 1.0); pairs =
  v2.4 non-155 + fresh v2.4b 155-doc (+2,058 direct / +5,991 gray; 244 `sch.`
  ids); preflight PASS. Triage 2,266 keeps ($9.37). Map 3,284 provisions,
  2 permanent schema errors (au-pa1988 s.26WE(1), au-tolaa2018 s.49B(2B));
  credit ceiling hit twice → top-ups → clean resumes. Verify +1,129 fires.
- **Acceptance PASS:** APP 8 (P6-I4) recovered via `au-pa1988-001#sch.1 APP 8.2`
  (baseline r1-au-037) — the new schedule citation style works end-to-end;
  SOCI recovered (191 verified fires citing real s.30xx; zero synthetic st.*).
- **Negative control PASS:** SG/MY csv+json+eval byte-identical to baseline
  hashes.
- **Score movements: NONE** — all 9 AU scores unchanged; this delta is
  citation-quality + evidence recovery, not scoring.
- **Honest correction:** review-packet conflation #2 ("resolved by v2.4") is
  NOT fully resolved — the single-shared-token fuzzy match persists; r1-au-041's
  KNOWN slot now cites au-ta1997-002 s.306(3) instead of the baseline's
  au-ta1979-002 s.187C (score-neutral). Flagged for John's curation
  (REVIEW_ITEMS §11), not auto-fixed (protects the negative control).
- Integrity: audit-trio 0 violations; URL 94/94 green. AU cumulative map
  $140.26 / verify $36.05; ledger evidenced total $281.59.
