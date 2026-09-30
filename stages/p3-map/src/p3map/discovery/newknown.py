"""S7 — NEW/KNOWN diff: 3-tier matcher vs the host baseline (framework §2.5).

The baseline is Round 1 for AU/MY/SG and Round 2 for CN/LA; Timor-Leste is in neither book, so
every TL fire is instrument-level NEW by construction.

For each verified fire, match against baseline rows in the same
(economy, indicator) cell:

  Tier 1 — law match: normalized names (whitespace collapse, punctuation strip,
           amendment-suffix tolerance), token-set fuzzy >= NEWKNOWN_SIM. The baseline is
           written in English, so the fire's own law_name is tried first and then the
           document's English and original-script names from doc_meta — a Chinese or Lao
           name scores 0 against an English one on token overlap.
  Tier 2 — section match: canonical section roots (s.26(1) -> "26") vs the
           baseline impact text's cited sections.
  Verdicts (KNOWN-biased — ties go to KNOWN; reproducing the baseline is
           rewarded, over-claiming NEW is penalized):
    law + section matched          -> KNOWN (cites the matched baseline row)
    law matched, section not cited -> provision-level NEW
    no law match in the cell       -> instrument-level NEW
    law matched, baseline cites no sections -> KNOWN (semantic tier deferred
           to curation eyeball — flagged)
  Premium NEW: law's last_amended/enacted postdates the baseline currency.

Outputs out/discovery/newknown_<ECON>.jsonl + a summary report.
"""
from __future__ import annotations

import json
import re
from collections import defaultdict

from config.instrument import from_artifact
from config.settings import SETTINGS

FUZZY_T = SETTINGS.newknown_sim  # 0.85 unless NEWKNOWN_SIM says otherwise
BASELINE_CURRENCY_YEAR = 2025  # baseline compiled ~early 2026, current to 2025


def _norm(s: str) -> str:
    s = re.sub(r"\s+", " ", (s or "").lower())
    s = re.sub(r"\(revised[^)]*\)|\(amendment[^)]*\)", " ", s)
    return re.sub(r"[^a-z0-9 ]", "", s).strip()


def _tokens(s: str) -> set[str]:
    # light plural stem: baseline writes "Services Tax Act", statutes "Service
    # Tax Act" — without it the fuzzy containment falls to 0.5 (< threshold)
    stop = {"act", "the", "of", "and", "an", "a", "law", "no"}
    out = set()
    for t in _norm(s).split():
        if t in stop or t.isdigit():
            continue
        if len(t) > 3 and t.endswith("s") and not t.endswith("ss"):
            t = t[:-1]
        out.add(t)
    return out


def _fuzzy(a: str, b: str) -> float:
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / min(len(ta), len(tb))


_SEC_ROOT = re.compile(r"(\d+[A-Z]{0,3})")


def _section_root(article_section: str) -> str:
    m = _SEC_ROOT.search(article_section or "")
    return m.group(1) if m else ""


def _baseline_sections(impact: str, note: str = "") -> set[str]:
    """Section roots cited in the baseline row's impact/note prose."""
    text = f"{impact} {note}"
    roots = set()
    for m in re.finditer(
            r"(?:section|sections|s\.|art\.|article|articles|reg\.|regulation)\s*"
            r"(\d+[A-Z]{0,3})", text, re.I):
        roots.add(m.group(1).upper())
    return roots


def _doc_names() -> dict[str, tuple[str, ...]]:
    """doc_id -> the other names its law is known by (English, original script).

    Written by ingest from laws.jsonl. An index built before that change carries neither key,
    and .get then falls back to the fire's own law_name -- Round 1's behaviour exactly.
    """
    p = SETTINGS.index_dir / "doc_meta.json"
    if not p.exists():
        return {}
    out: dict[str, tuple[str, ...]] = {}
    for did, dm in json.loads(p.read_text(encoding="utf-8")).items():
        names = tuple(n for n in (dm.get("law_name_en"), dm.get("law_name_original")) if n)
        if names:
            out[did] = names
    return out


def run_newknown(economy: str) -> dict:
    doc_names = _doc_names()
    # An economy may legitimately have no baseline at all: Timor-Leste has neither a Round 1 nor a
    # Round 2 sheet, so every one of its rows is NEW by construction. This used to require the file
    # and died with FileNotFoundError, which is the same assumption -- that every economy has a
    # baseline -- that once tagged no-provision rows KNOWN. An absent file means "nothing to
    # reproduce", not "the run is broken"; output/submission.py already guarded it this way.
    baseline_cells: dict[str, list[dict]] = defaultdict(list)
    bl_path = SETTINGS.out_dir / "baseline_rows.jsonl"
    if bl_path.exists():
        with bl_path.open(encoding="utf-8") as f:
            for line in f:
                b = json.loads(line)
                if b["in_p3_scope"] and b["economy"] == economy:
                    baseline_cells[b["indicator"]].append(b)
    else:
        print(f"[newknown:{economy}] no baseline_rows.jsonl in this run directory: every fire is "
              f"NEW by construction", flush=True)
    if not baseline_cells:
        print(f"[newknown:{economy}] the baseline carries no in-scope row for this economy: "
              f"every fire is NEW", flush=True)

    # verified fires only (final_applies true); pending-verification fires are
    # tagged too so the draft CSV is complete — flagged verification_pending
    fires = []
    verified: dict[tuple[str, str], dict] = {}
    vpath = SETTINGS.out_dir / "verify" / f"verified_{economy}.jsonl"
    if vpath.exists():
        with vpath.open(encoding="utf-8") as f:
            for line in f:
                r = json.loads(line)
                verified[(r["provision_id"], from_artifact(r["indicator"]))] = r
    with (SETTINGS.out_dir / "map" / f"verdicts_{economy}.jsonl").open(encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            if "error" in row:
                continue
            for v in row["verdicts"]:
                if not v["applies"]:
                    continue
                ind = from_artifact(v["indicator"])
                vv = verified.get((row["provision_id"], ind))
                if vv is not None and not vv["final_applies"]:
                    continue  # overturned by the panel
                fires.append({**{k: row[k] for k in
                                 ("provision_id", "doc_id", "law_name",
                                  "article_section", "economy")},
                              "indicator": ind,
                              "score_hint": (vv or {}).get("final_score_hint",
                                                           v["score_hint"]),
                              "coverage": v["coverage"],
                              "verification": (vv or {}).get("verifier_verdict",
                                                             "pending")})

    out_dir = SETTINGS.out_dir / "discovery"
    out_dir.mkdir(parents=True, exist_ok=True)
    counts = defaultdict(int)
    with (out_dir / f"newknown_{economy}.jsonl").open("w", encoding="utf-8") as fout:
        for fire in fires:
            cell = baseline_cells.get(fire["indicator"], [])
            names: list[str] = []
            for nm in (fire["law_name"], *doc_names.get(fire["doc_id"], ())):
                if nm and nm not in names:
                    names.append(nm)
            best, best_score, best_name = None, 0.0, ""
            for b in cell:
                for law in re.split(r"[;\n]", b["law"] or ""):
                    for nm in names:
                        sc = _fuzzy(nm, law)
                        if sc > best_score:
                            best, best_score, best_name = b, sc, nm
            via = "" if best_name in ("", fire["law_name"]) else " (matched on the English name)"
            tag, matched_id, evidence = "NEW", None, ""
            if best is not None and best_score >= FUZZY_T:
                roots = _baseline_sections(best.get("impact", ""), best.get("note", ""))
                fire_root = _section_root(fire["article_section"] or "").upper()
                if fire_root and fire_root in roots:
                    tag, matched_id = "KNOWN", best["baseline_id"]
                    evidence = f"law+section match (s.{fire_root}){via}"
                elif not roots:
                    tag, matched_id = "KNOWN", best["baseline_id"]
                    evidence = f"law match; baseline cites no sections (eyeball at curation){via}"
                else:
                    tag, matched_id = "NEW", best["baseline_id"]
                    evidence = (f"provision-level NEW: law known, "
                                f"s.{fire_root or '?'} not cited by baseline{via}")
            else:
                evidence = "instrument-level NEW: no law match in cell"
            counts[tag] += 1
            fout.write(json.dumps({**fire, "discovery_tag": tag,
                                   "baseline_match": matched_id,
                                   "match_evidence": evidence,
                                   "law_matched_name": best_name,
                                   "law_fuzzy": round(best_score, 3)},
                                  ensure_ascii=False) + "\n")

    report = {"economy": economy, "fires_tagged": len(fires), **counts}
    (out_dir / f"newknown_report_{economy}.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8")
    print(f"[newknown:{economy}] {json.dumps(report)}")
    return report


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="S7 NEW/KNOWN: tags each fire against the baseline the sample kit provides.")
    ap.add_argument("economy", nargs="?", default="SG")
    a = ap.parse_args()
    run_newknown(a.economy)
