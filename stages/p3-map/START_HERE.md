# rdtii-p3-map — START HERE (Project 3: Mapping to the RDTII Index)

> **CURRENT STATE (2026-07-18): pipeline COMPLETE, all three economies mapped +
> verified on corpus v2.4 (392,181 provisions).** The dated kickoff banners below
> are preserved as provenance. For where things actually stand — results, cost
> ledger, review items, the AU multi-volume re-map — read
> **`workflow/WORKFLOW_LOG.md`** (running record), `workflow/REVIEW_PACKET_2026-07-16.md`
> + `workflow/REVIEW_ITEMS.md` (open curation decisions), and
> `workflow/DELTA_AU_v2.4_2026-07-18.md` (latest corpus fix). Judged outputs are in
> `out/submission/`, `out/results/`, `out/audit/`.

> **UPDATE (2026-07-14): the foundation is READY — Hand-off #2 is DELIVERED.**
> P2 shipped the full corpus (305,980 grounded provision records, all 2,616 laws,
> `Desktop\handoff2\`, contract v0.2.0). This folder was seam-audited and synced the
> same day: schemas vendored into `00_contracts/schemas/`, contract re-vendored at
> v0.2.0, requirements/PLAN staleness fixed, and all reference material pulled in.
> **Required reading before building: `docs/FOUNDATION_SYNC_2026-07-14.md`** (the 4
> T0 blockers + resolutions, incl. the coverage-grid decision, and every seam fact
> the code must handle) **and `docs/HANDOFF2_NOTES_2026-07-13.md`** (P2's own release
> notes). Precedence: FOUNDATION_SYNC > KICKOFF_DECISIONS > PLAN.md.

> **UPDATE (2026-07-12):** the promised re-detailing exists — read
> **`docs/KICKOFF_DECISIONS_2026-07-12.md`** (12 decisions + the consolidated mapping
> workflow; it supersedes PLAN.md where they differ). The **P0 instrument is BUILT and
> vendored** into `contracts/instrument/` (`.env` `INSTRUMENT_DIR` points there —
> hash-verified against P0 `output/` on 2026-07-14).

**What this is.** The kickoff kit for **Project 3** — maps each grounded provision to the correct RDTII 2.1 indicator (`P6-I1`…`P7-I5`), blind-verifies, tags **NEW/KNOWN** against the baseline, runs the **Malaysia error-check**, and writes the final consolidated **CSV + JSON**. Owns the **40% substantive-accuracy** block incl. the **20-pt NEW-evidence** lever and the **15-pt audit trail** — the highest-value repo.

## Read in this order
1. **`docs/FOUNDATION_SYNC_2026-07-14.md`** — the seam-audit results: T0 blockers resolved, the coverage-grid decision, and the seam facts the code must handle. **Wins over everything below.**
2. **`docs/HANDOFF2_NOTES_2026-07-13.md`** — P2's release notes for the delivered corpus (`~n` ids, CER honesty, bilingual MY, tag semantics).
3. **`docs/KICKOFF_DECISIONS_2026-07-12.md`** — the 12 design decisions (supersede PLAN.md where they differ).
4. **`PLAN.md`** (provisional) — the full Project 3 plan.
5. **`INTERFACE_CONTRACT.md`** (v0.2.0, re-vendored 2026-07-14) — **§3** (Hand-off #2 you consume), **§4.1** (the 9 indicator definitions — authoritative), **§6** (ownership matrix). Validate against `00_contracts/schemas/`, not the §3.3 prose table.
6. **`reference/Target_Output_Summary.md`** + **`reference/Scoring_Criteria.md`** — the indicator defs, the 13-column schema, and exactly how the 40% is judged.

## Reference material (this *is* the substance of Project 3)
- **`reference/Round1_Baseline_Database.xlsx`** — the **KNOWN baseline** (Consolidated · Singapore · Australia · Malaysia tabs). The `--baseline` target for NEW/KNOWN tagging + the Malaysia error-check.
- **`reference/OUTPUT_TEMPLATE.xlsx`** — the exact 13-column output schema. **⚠️ Its "Indicator Reference" tab is WRONG** (GDPR-style taxonomy) — ignore it; use the methodology definitions only. (Same artifact as `reference/submission_templates/OUTPUT_TEMPLATE_31MAY.xlsx`, the filename `indicators.yaml`'s WARNING cites.)
- **`reference/RDTII_2.1_guide.pdf`** — the authoritative indicator methodology.
- **`reference/rdtii_official/`** — the rest of the official corpus: internal guide, non-regulatory-indicators note, **Round 2 Database** (next-round baseline), hackathon knowledge base, host Q&A summary, and the host's SG/MY/AU **Legal Inventory CSV** (useful coverage cross-check).
- **`reference/assignments/`** — both take-home assignments complete: briefs, **answer key + feedback**, practice dataset, hands-on slides — **worked mapping examples from the host.** Study these before designing the mapping prompts — they de-risk the scoring logic. (The three loose copies at `reference/` root are the same key files.)
- **`reference/submission_templates/`** — README template, pitch-deck template, format-requirements PDF: what Round 1 actually gets submitted.
- **`reference/pre_application/`** — the original application set: **`Technical_memo_rocky.pdf`** (the architecture promised to the judges — keep the Round-1 story continuous with it), concept-video doc, knowledge base.
- **`reference/research_literature/`** — the curated papers behind the design (`AI for law/` is the P3-relevant core: LegalBench-RAG, legal-RAG hallucination evidence, reasoning-focused legal retrieval; each folder has a `*_summary.md` — read those first).

## The traps to encode (from the methodology)
- consent / adequacy = **P6-I4 conditional**, **NOT** a P6-I1 ban.
- "not longer than necessary" is **NOT** P7-I3 (that needs a *minimum* retention period).
- do **not** score data-localisation of **government** data.
- **P7-I1 polarity is inverted** (1 = *no* framework, 0 = comprehensive).

## When you're ready
Projects 0, 1 and 2 are **done** — the full corpus is waiting in `Desktop\handoff2\`.
Next session: detail the Stage-3 mechanism (prefilter → map → blind-verify → NEW/KNOWN
→ final CSV), then build T0 onward. Timeline to Round 1 (20 Jul): scaffold+prefilter
15 Jul · SG slice mapped+verified 17 Jul · three-economy run + NEW/KNOWN 18–19 Jul ·
submit 20 Jul. **Canonical plans** live in `Desktop/RDTII Plan/06_Subproject_Plans/`.
