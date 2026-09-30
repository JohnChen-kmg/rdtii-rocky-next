"""Stage D — normalize the host baseline rows into output/gold/gold_set.jsonl.

One JSON line per coded row in the host workbooks' country sheets, all pillars:
  Round 1 database  Australia · Malaysia · Singapore
  Round 2 database  China · India · Indonesia · Lao PDR · Mongolia · Russian Federation · Thailand

This is the KNOWN set for NEW/KNOWN diffing and the yardstick for retrieval recall and mapping
accuracy, per economy. It is quarantined: discovery, extraction, triage and mapping never use
it to decide anything (mapping-stage decision 11).

label_flag, four statuses:
  suspect      reviewed in Round 1: likely mis-scored against the Guide/FAQ; never used as an exemplar
  advisory     reviewed in Round 1: defensible but nuanced; usable as an exemplar with its note
  host_marked  the host's own data verification marked the row "Not correct" (Thailand sheet,
               columns M-O); the action usually keeps the score and corrects the text or law
               title. Never used as an exemplar. host_verification carries the host's wording.
  candidate    machine check only (2026-09-13): a rule-based signal that the label may conflict
               with host rules. NOT reviewed. Review before relying on it either way.

exemplar_for lists the indicators whose signature uses the row as an exemplar, so an
evaluation of that economy can exclude rows the retrieval query was built from.

Finale change (W3, 2026-09-13): Round 1 covered pillars 6-7 of the Round 1 workbook only.
"""
from __future__ import annotations

import json
import re
from collections import defaultdict

import yaml

from indicator_ids import normalize
from rdtii_examples import (DATA, REPO, articles_mentioned, load_all, load_methodology,
                            score_values)

OUT = REPO / "output" / "gold" / "gold_set.jsonl"
CURATED = DATA / "curated_exemplars.yaml"

# Flags reviewed in Round 1 (gold_id -> flag). Reasons cite the framework sources.
LABEL_FLAGS = {
    "r1-my-053": {
        "status": "suspect",
        "reason": ("Scored 1 for the PDPA Retention Principle, but 'not retaining personal data "
                   "for longer than is required' is a MAXIMUM-period rule; Guide p.60 fn.35 and the "
                   "Internal Guide FAQ (p.13) prescribe score 0 for requirements without a specified minimum "
                   "period. Singapore's identical pattern (PDPA s.25, r1-sg-041) was "
                   "scored 0. Prime Malaysia error-check target."),
    },
    "r1-my-054": {
        "status": "suspect",
        "reason": ("Scored 1 for the Communications CoP retention principle ('kept only as long as "
                   "necessary', s.5.5) — a maximum-period rule that the Guide/FAQ score 0. Same "
                   "pattern as r1-my-053. Prime Malaysia error-check target."),
    },
    "r1-au-034": {
        "status": "advisory",
        "reason": ("Impact text describes 'government medical records' (tension with the "
                   "government-data exception), but the Guide itself uses AU health records as the "
                   "canonical 6.1/6.2 worked example (Guide p.50) — treat 0.5 (sectoral personal data) as "
                   "authoritative precedent."),
    },
    "r1-au-035": {
        "status": "advisory",
        "reason": "Same as r1-au-034 (dual-recorded 6.1+6.2 per the Guide's dual-recording rule, Guide p.51).",
    },
    "r1-my-050": {
        "status": "advisory",
        "reason": ("Sectoral CoP scored 0.5 under 7.1 while the comprehensive PDPA row (r1-my-049) is 0. "
                   "Per the Assignment 1 answer key, sectoral instruments ARE recorded, but the "
                   "horizontal law is the controlling evidence for the indicator-level score — the "
                   "Singapore analog (Banking Act, r1-sg-039) was scored 0. The finale template adds that "
                   "7.1 is answered once per economy (Indicator Reference row 80)."),
    },
    "r1-my-051": {
        "status": "advisory",
        "reason": "Same as r1-my-050 (Communications CoP sectoral complement scored 0.5).",
    },
    "r1-sg-042": {
        "status": "advisory",
        "reason": ("Coverage marked 'Horizontal' but the instrument is a telecom facilities-based "
                   "operator licence — likely sectoral (telecommunications)."),
    },
}

LACK_OF = {"4.5", "4.1", "5.1", "5.4", "5.7", "7.1", "7.2", "8.1", "8.2", "11.1", "12.9"}
_MAX = re.compile(r"(as long as (is )?necessary|no longer than (is )?(necessary|required)|not longer than|"
                  r"longer than (is )?(necessary|required)|only for as long as|cease to retain|cease retaining)", re.I)
_MIN = re.compile(r"(at least|not less than|no less than|minimum (period|of)|\b\d+\s*(years?|months?|days?)\b|"
                  r"\b(one|two|three|four|five|six|seven|eight|nine|ten|twelve|twenty)\s+(years?|months?)\b|permanent)", re.I)
_CONDITION = re.compile(r"\b(unless|except|exception|consent|adequa\w*|approval|permission|authori[sz]ation|"
                        r"subject to (the )?conditions?|comparable (standard|level) of protection)\b", re.I)
_GOV_DATA = re.compile(r"\b(government (data|records|medical records)|public[- ]sector data|state secrets|"
                       r"data (held|owned|processed) by (the )?government)\b", re.I)
_SECTOR_LAW = re.compile(r"\b(telecommunication\w*|banking|bank|insurance|securities|health|medical|payment\w*|"
                         r"broadcast\w*|postal|capital market\w*)\b", re.I)
_EXISTS = re.compile(r"\b(has (enacted|adopted|established)|have (enacted|adopted)|is governed by|are governed by|"
                     r"in place|provides? (a|the) (legal )?framework|comprehensive)\b", re.I)
_ABSENT = re.compile(r"\b(no|not|lack\w*|absen\w+|without|none|does not|doesn't)\b", re.I)


def _f(v):
    try:
        return float(str(v).strip())
    except (TypeError, ValueError):
        return None


def candidate_checks(r: dict, allowed: list[float], economy_min: dict) -> list[str]:
    ind, imp, score = r["indicator"], r["impact"] or "", _f(r["raw_score"])
    out = []
    if score is None:
        out.append("score_missing_or_not_numeric")
    elif allowed and all(abs(score - a) > 1e-9 for a in allowed):
        out.append(f"score_not_in_allowed_set {allowed}")
    if ind == "7.3" and score == 1 and _MAX.search(imp) and not _MIN.search(imp):
        out.append("retention_maximum_period_scored_1 (Guide p.60 fn.35; Indicator Reference row 81)")
    if ind == "6.1" and score and score > 0 and _CONDITION.search(imp):
        out.append("possible_conditional_regime_scored_as_ban (Internal Guide p.13; Indicator Reference row 84)")
    if ind in {"6.1", "6.2", "6.3", "6.4", "7.3"} and score and score > 0 and _GOV_DATA.search(imp):
        out.append("possible_government_data_measure_scored (Indicator Reference notes)")
    # pillars 6-7 only: elsewhere the "sector" is often the indicator's own domain
    # (telecom laws under pillar 5, payment laws under 12.4.x), so the signal is noise
    first_law = re.split(r"[;\n]", r["law"] or "")[0]
    if r["pillar"] in (6, 7) and (r["coverage"] or "").strip().lower() == "horizontal" and _SECTOR_LAW.search(first_law):
        out.append("coverage_horizontal_but_sectoral_law_name")
    if ind in LACK_OF and score == 1 and _EXISTS.search(imp) and not _ABSENT.search(imp):
        out.append("possible_inverted_polarity (framework described as existing but scored 1)")
    if ind in {"7.1", "7.2"} and score is not None:
        m = economy_min.get((r["economy"], ind))
        if m is not None and score > m:
            out.append("economy_level_answer_inconsistent (another row for this economy scores lower; Indicator Reference row 80)")
    if not r["urls"]:
        out.append("no_reference_url")
    return out


def main() -> None:
    rows = [r for r in load_all() if not r["strikethrough"]]
    meth = load_methodology()
    curated = yaml.safe_load(CURATED.read_text(encoding="utf-8")) if CURATED.exists() else {}
    exemplar_for: dict[tuple, list[str]] = defaultdict(list)
    for ind, lst in (curated or {}).items():
        for x in lst:
            exemplar_for[(x["sheet"], x["row"])].append(normalize(ind))
    economy_min: dict[tuple, float] = {}
    for r in rows:
        s = _f(r["raw_score"])
        if r["indicator"] in {"7.1", "7.2"} and s is not None:
            k = (r["economy"], r["indicator"])
            economy_min[k] = min(s, economy_min.get(k, s))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    n_flag = defaultdict(int)
    with OUT.open("w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            allowed = score_values(meth[r["indicator"]]["possible_scores"]) if r["indicator"] in meth else []
            flag = LABEL_FLAGS.get(r["gold_id"])
            hv = r.get("host_verification") or {}
            if flag is None and (hv.get("feedback") or "").strip().lower() == "not correct":
                flag = {"status": "host_marked",
                        "reason": ("Host data verification marked this row Not correct. Action: "
                                   + (hv.get("action") or "none given"))}
            if flag is None:
                checks = candidate_checks(r, allowed, economy_min)
                substantive = [c for c in checks if c != "no_reference_url"]
                if substantive:
                    flag = {"status": "candidate", "checks": checks,
                            "reason": "Machine check only, not reviewed: " + "; ".join(substantive)}
            if flag:
                n_flag[flag["status"]] += 1
            rec = {
                "gold_id": r["gold_id"],
                "baseline_round": r["source"],
                "economy": r["economy"],
                "pillar": r["pillar"],
                "indicator": r["indicator"],
                "raw_score": r["raw_score"],
                "law": r["law"],
                "coverage": r["coverage"],
                "impact": r["impact"],
                "timeframe": r["timeframe"],
                "urls": r["urls"],
                "note": r["note"],
                "update_type": r.get("update_type"),
                "host_verification": r.get("host_verification"),
                "articles_mentioned": articles_mentioned(r["impact"]),
                "label_flag": flag,
                "exemplar_for": exemplar_for.get((r["sheet"], r["row"]), []),
                "provenance": {
                    "workbook": ("Round1_Baseline_Database.xlsx" if r["source"] == "round1"
                                 else "Round2_Methodology_and_Examples.xlsx"),
                    "sheet": r["sheet"],
                    "row": r["row"],
                },
            }
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    by_key = {(r["sheet"], r["row"]): r for r in rows}
    used_suspect = [by_key[k]["gold_id"] for k in exemplar_for if k in by_key
                    and LABEL_FLAGS.get(by_key[k]["gold_id"], {}).get("status") == "suspect"]
    if used_suspect:
        raise SystemExit(f"suspect rows used as exemplars: {used_suspect}")
    print(f"wrote {len(rows)} gold rows -> {OUT.relative_to(REPO)} "
          f"(flags: {dict(n_flag)})")


if __name__ == "__main__":
    main()
