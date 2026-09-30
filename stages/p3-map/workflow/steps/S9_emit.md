# S9 — Curate + emit · $0 · no LLM · the gatekeeper

**What we're doing:** turning verified, tagged fires into the judged **13-column
CSV** (+ a richer JSON), and emitting a mandatory row wherever an indicator has no
qualifying provision.

**In → Out**
- In: verified fires + NEW/KNOWN tags + provision metadata.
- Out: `out/submission/records_<ECON>.csv` (13 frozen columns) + `.json`.

**How it curates** (`output/submission.py`)
- **KNOWN:** one row per baseline row; the slot goes to the fire whose **law matches
  the baseline law** (Jaccard tie-break), then verification, then confidence.
- **NEW:** confidence ≥ 0.75, quote grounded, not overturned; dedupe by (doc,
  section root); per-cell caps (8, or 10 for the multi-row P7-I3/I5).
- **Baseline-reproduction guarantee:** any baseline law that fired gets its best fire
  outside the caps.
- **No-provision rows:** Article/Section = `"n/a"`, cite the governing law + one
  working URL + the reason in Notes (contract §6 variant).

**Hard gate (rubric FAIL trigger):** every scored row must carry a non-empty
**Article/Section + Verbatim Snippet + Source URL** — else it is dropped and logged.
Plus a URL-liveness pass (94/94 green). Result: SG 42 / MY 57 / AU 42 rows.
