# evidence

Proof that the instrument covers what it claims and scores it consistently. Five artefacts belong
here. Record the command that produced each one and the date it was run.

| Artefact | What it proves | Status 2026-09-13 |
| :---- | :---- | :---- |
| Saved transcript of `python scripts\validate_instrument.py` exiting 0 on the merged 61-indicator instrument | The definition of done was met, not asserted | **Done:** `VALIDATION_2026-09-13.txt` (PASS, exit 0). Re-run from this workspace with `python code\tools\validate.py --save`, which checks the Guide sentences and compares with the finale repo. Not yet vendored into the repo |
| Coverage table listing every in-scope ID with its pillar and its tier | The C1b claim of all twelve pillars | **Done:** `coverage_2026-09-13.md` (`python -X utf8 code\scripts\report_coverage.py --out evidence\coverage_<date>.md`) |
| Per-pillar prompt prefix character counts from step 3D | The per-pillar decision held. It also feeds the cost claim the secretariat verifies against the code | **Measured, not yet in use:** `prefix_sizes_2026-09-13.md` (`python -X utf8 code\scripts\measure_prefix.py`, which renders with today's prompt code). Pillar 12 exceeds the D3 target |
| Before-and-after sample of the same provision scored under legacy and decimal IDs | C2a consistency across the ID migration | **Not possible yet:** needs a mapping run after the mapping stage reads decimal IDs |
| Gold-set result on the 9 Tier A indicators | Measured accuracy. State it beside the plain admission that no gold set exists for the other 52 | **Round 1 figures only** (SG 0.846, MY 0.727 raw / 0.889 parsed, AU 0.889, from `RDTII/pipeline-data/rdtii-p3-map/out/eval/`). The finale gold set now covers all 61 indicators across ten economies, so the "no gold set for the other 52" admission no longer holds; a finale evaluation run is still needed |

Supporting files from the 2026-09-13 build:
- `label_flags_2026-09-13.md`: every flagged gold row (suspect, advisory, host_marked, candidate) and the host verification coverage.
- `citation_audit_2026-09-13.txt`: heuristic check that cited Guide and Internal Guide pages contain what each rule line says. It audits 423 rule lines and lists 30 for review.
  - One wrong page citation was found overnight and corrected before the final run.
  - **Corrected the same morning.** The overnight run's country-name check never matched (a quoting slip left backspace characters in its pattern), so it listed only 19 lines. The corrected run is from `code\tools\audit_citations.py`.
  - The 19 are low-overlap paraphrases; the low-overlap lines were read, and three were checked against the page text.
  - The 11 added lines each name a country example that comes from a workbook row cited in the same line. Each of those rows was looked up in the gold set and matches; no wrong citation was found.

C1b 15 and C2a 10 consume this folder directly. Section 4 of the Stage 3 submission template and the
Coverage Matrix sheet of the finale output workbook are the fields that quote from it.
