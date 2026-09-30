"""A/B #2 — Haiku-first vs Sonnet-first mapper (framework §2.10 open question #6).

Groups the top SG direct-band pairs per provision (a provision's candidate set),
runs the SAME schema-forced mapping prompt through Haiku and Sonnet (cached
instrument prefix), and reports: verdict agreement, quote-grounding validity
(exact-substring check — the hard validator), score_hint agreement, and measured
cost per provision each. Decision input, not a gate: if Haiku agrees >=90% on
`applies` AND its quotes ground >=98%, Haiku-first (+Sonnet escalation) is viable
(~$80-130 total); else Sonnet-first stands (~$150-260).

Default 150 provisions (~450 verdicts) ≈ $6-9 live; --n to resize.
"""
from __future__ import annotations

import json
import time
from collections import defaultdict

from config.llm.base import usd
from config.llm.factory import get_llm
from config.settings import SETTINGS
from src.p3map.mapping.prompt import build_system_prefix, build_user_turn
from src.p3map.mapping.schema import MAPPING_SCHEMA, MappingVerdict

DEFAULT_N = 150


def _sg_provision_groups(n: int) -> list[tuple[dict, list[str]]]:
    """Top-RRF SG provisions with their candidate indicator sets."""
    cands: dict[str, list[tuple[float, str]]] = defaultdict(list)
    with (SETTINGS.out_dir / "select" / "direct_pairs.jsonl").open(encoding="utf-8") as f:
        for line in f:
            p = json.loads(line)
            if p["economy"] == "SG":
                # "score" since 2026-09-27 (a cosine in scores mode, an RRF score in caps
                # mode); "rrf" is what Round 1's pair files carry.
                cands[p["provision_id"]].append(
                    (float(p.get("score", p.get("rrf", 0.0))), p["indicator"]))
    ranked = sorted(cands.items(), key=lambda kv: -max(s for s, _ in kv[1]))[:n]
    wanted = {pid for pid, _ in ranked}
    recs = {}
    with (SETTINGS.index_dir / "prefilter_corpus.jsonl").open(encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if r["provision_id"] in wanted:
                recs[r["provision_id"]] = r
    return [(recs[pid], sorted({ind for _, ind in pairs}))
            for pid, pairs in ranked if pid in recs]


def run_ab_mapper(n: int = DEFAULT_N) -> dict:
    groups = _sg_provision_groups(n)
    system = build_system_prefix()
    print(f"[ab-mapper] {len(groups)} SG provisions; prefix {len(system)} chars")

    clients = {"haiku": get_llm(SETTINGS, role="mapper", model="claude-haiku-4-5"),
               "sonnet": get_llm(SETTINGS, role="mapper", model="claude-sonnet-5")}
    t0 = time.time()
    results = []
    for gi, (rec, candidates) in enumerate(groups):
        user = build_user_turn(rec, candidates)
        row = {"provision_id": rec["provision_id"], "candidates": candidates}
        for name, cl in clients.items():
            try:
                raw = cl.complete(user, MAPPING_SCHEMA, system=system,
                                  max_tokens=2048, cache_system=True)
                v = MappingVerdict.model_validate(raw)
                row[name] = {
                    "verdicts": {x.indicator: {"applies": x.applies,
                                               "score_hint": x.score_hint,
                                               "coverage": x.coverage,
                                               "quote_grounded": x.verbatim_quote in rec["text"],
                                               "conf": x.confidence}
                                 for x in v.verdicts},
                    "traps": v.trap_checks.model_dump(),
                }
            except Exception as e:
                row[name] = {"error": f"{type(e).__name__}: {str(e)[:150]}"}
        results.append(row)
        if (gi + 1) % 25 == 0:
            print(f"[ab-mapper] {gi+1}/{len(groups)}", flush=True)

    # ---- metrics
    agree = total = 0
    ground = {"haiku": [0, 0], "sonnet": [0, 0]}
    score_agree = score_total = 0
    for row in results:
        h, s = row.get("haiku", {}), row.get("sonnet", {})
        if "verdicts" not in h or "verdicts" not in s:
            continue
        for ind in row["candidates"]:
            hv, sv = h["verdicts"].get(ind), s["verdicts"].get(ind)
            if not (hv and sv):
                continue
            total += 1
            agree += int(hv["applies"] == sv["applies"])
            if hv["applies"] and sv["applies"]:
                score_total += 1
                score_agree += int(hv["score_hint"] == sv["score_hint"])
            for name, v in (("haiku", hv), ("sonnet", sv)):
                if v["applies"]:
                    ground[name][1] += 1
                    ground[name][0] += int(v["quote_grounded"])

    report = {
        "provisions": len(groups),
        "verdict_pairs": total,
        "applies_agreement": round(agree / total, 4) if total else None,
        "score_hint_agreement_when_both_apply":
            round(score_agree / score_total, 4) if score_total else None,
        "quote_grounding": {k: {"rate": round(a / b, 4) if b else None, "n": b}
                            for k, (a, b) in ground.items()},
        "cost_usd": {k: round(usd(c.model, c.usage), 4) for k, c in clients.items()},
        "usage": {k: vars(c.usage) for k, c in clients.items()},
        "elapsed_seconds": round(time.time() - t0, 1),
        "decision_rubric": "Haiku-first viable if applies_agreement>=0.90 AND "
                           "haiku quote grounding>=0.98; else Sonnet-first.",
    }
    out = SETTINGS.out_dir / "ab" / "ab_mapper_report.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"report": report, "rows": results}, indent=2,
                              ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    import sys
    run_ab_mapper(int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_N)
