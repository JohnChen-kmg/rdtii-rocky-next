# Corpus version ledger — Hand-off #1 (`handoff1_v2/`)

The manifest schema (contract 0.2.0, frozen) carries no version field, so this ledger is
the **first-class record** of what each corpus version contains. Distinguish versions by
this table + each row's `access_date`. Full doc_id tables live in the completion-report
addenda; per-fetch evidence is in `crawl_log.jsonl`.

| Version | Date window (UTC) | What changed | Docs added / replaced | Running total |
|---|---|---|---|---|
| **v2.0** | 2026-07-11 → 07-12 | Initial complete pillar-agnostic corpus (SG browse-listing crawl; MY lom act 1–900; AU register API enumeration) | +2,616 | **2,616** (SG 525 / MY 833 / AU 1,258) |
| **v2.1** | 2026-07-14 | Version-currency fixes: **all 858 MY rows replaced** with current `/EN/` consolidations or newest reprints (+25 net new acts, incl. 2026 legislation); `sg-ca2018-001` replaced in place (Acts-Supp original → current consolidation incl. 2024 amendments); ~9 SG seed docs refreshed in place (same doc_ids) | +25 net (858 MY replace 833; 10 SG replaced in place) | **2,641** (SG 525 / MY 858 / AU 1,258) |
| **v2.2** | 2026-07-14 (late) | P3's 18-item delta request, 18/18 fetched: SG subsidiary legislation + PDPC/MAS (6), MY PDP guidelines + Act 854 P.U.(A) regs (8), AU F-series instruments (3) + `au-scia2018-001` **purged as PDF and re-added as full-text HTML** (same doc_id, new form) | +18 fetched / **+17 net** (1 purge) | **2,658** (SG 531 / MY 866 / AU 1,261) — doc_ids: report **Addendum 2** |
| **v2.3** | 2026-07-15 | Proactive discovery sweep: 15 regulator instruments (SG 5: NDB regs, CII regs 2018+2025, CCoP 2.0, MAS TRM · MY 3: PDP Regs 2013, SC GTRM, 854 Exemption Order · AU 7: CIRMP/TSRMP rules, Smart-Devices rules, CPS 230+234, AGA-Governance + Credit-Reporting codes). 1 attempted fetch failed and is NOT in the corpus: BNM RMiT (HTTP 202 bot-gate; logged, incl. the 2026-07-16 disclosed outcome correction) | +15 | **2,673** (SG 536 / MY 869 / AU 1,268) — doc_ids: report **Addendum 3** |
| **v2.4** | 2026-07-17 → 07-18 | **CRITICAL fix — AU multi-volume truncation** (independent judge's spot-check): the epubFrame HTML capture held volume 1 only for every multi-volume compilation. All **33** affected acts re-fetched COMPLETE via the register's dated epub (all volumes concatenated, spine-verified) under §5.4 supersession: new seq `-002`, `supersedes` notes, superseded `-001` rows kept + annotated. Flagship: `au-ta1979-002` now contains Part 5-1A (s.187C metadata retention). Audit: `AU_HTML_TRUNCATION_AUDIT_2026-07-17.md` — 0 truncated remaining | +33 rows (33 laws superseded in place; 0 net new laws) | **2,706 rows = 2,673 current + 33 superseded** (SG 536 / MY 869 / AU 1,268 current) — doc_ids: report **Addendum 5** |

Reconciliation notes:
- 2,616 → 2,641 → (+18 fetched, −1 purged) 2,658 → (+15) **2,673** → (+33 superseded
  rows) **2,706 rows / 2,673 current**. Anyone re-deriving v2.2/v2.3 deltas from fetch
  logs will count 18 and 15 *fetches*; the SOCI purge is why v2.2's *net* row change is
  +17. v2.4 adds rows without adding laws: each of the 33 is a complete re-issue of an
  existing law (`-002` supersedes `-001`; both rows kept). The v2.4 fetch log shows 34
  epub fetches for 33 docs (one disclosed duplicate TIA fetch, byte-identical).
- v2.4 verification delta (2026-07-18, see the audit report): wider-detector re-sweep
  (word-number forms) added nothing — 33 is exhaustive; all 2,271 corpus PDFs scanned,
  0 multi-volume declarations (PDF lane clean by evidence); SG/MY negative confirmed;
  33/33 per-act acceptance PASS (spine complete, declared==spine count, Endnote in
  final volume, named casualties 187A–N / 56AA / 262A present).
- Superseded raw files from replaced rows remain on disk beside their replacements
  (provenance); the v1 corpus is preserved whole in `handoff1_old_v01/`.
- Forms at v2.4 (current versions): 2,228 pdf_native / 43 pdf_scanned / 402 html;
  ~1.85 GB incl. superseded raw files; `validate` 0 errors, 0 warnings (2,706 rows).
