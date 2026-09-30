# S7 — NEW / KNOWN diff · $0 · no LLM

**What we're doing:** tagging each verified fire as **KNOWN** (it reproduces a
Round-1 baseline row) or **NEW** (a discovery beyond the baseline).

**In → Out**
- In: verified fires + `out/baseline_rows.jsonl` (the Round-1 answer key).
- Out: `out/discovery/newknown_<ECON>.jsonl` (each fire + tag + match evidence).

**How it works** (`discovery/newknown.py`)
- **Tier 1 — law match:** normalized, plural-stemmed law-name token overlap ≥ 0.85.
- **Tier 2 — section match:** section root (e.g. `s.26(1)` → `26`) vs the baseline
  row's cited sections.
- **KNOWN-biased:** law + section match → KNOWN; ties → KNOWN. Over-claiming NEW is
  the penalized error; reproducing the baseline is rewarded.
- Post-baseline amendments (newer than the baseline) → **premium NEW**.

**Example:** the `s.26(1)` P6-I4 fire matches baseline row `r1-sg-036` (PDPA s.26) →
**KNOWN**. Result (SG): 428 KNOWN / 383 NEW.
