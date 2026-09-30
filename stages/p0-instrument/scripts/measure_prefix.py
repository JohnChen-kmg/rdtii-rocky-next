"""Measure the mapping prompt's cached system prefix, per pillar and for all indicators at once.

Renders the codebook exactly the way stages/p3-map/src/p3map/mapping/prompt.py:build_system_prefix()
does today (same header, same kept keys, yaml.dump with sort_keys=True, width 100), but over the
finale codebook (all 61 blocks in indicators.yaml). Decision D3 projected about
176,000 characters for one 61-indicator prefix against 25,974 measured for nine; this script
replaces that projection with a measurement.
"""
from __future__ import annotations

import sys
from collections import defaultdict

import yaml

from rdtii_examples import REPO

OUT = REPO / "output"
KEEP = ("id", "name", "question", "definition", "scoring", "scoring_tree",
        "disambiguation", "coding_rules", "exceptions")


def render(ind_doc: dict, pol_doc: dict, blocks: list[dict]) -> str:
    parts = [
        "You are a legal analyst coding statutory provisions against the RDTII 2.1 "
        "digital-trade indicators (Pillars 6-7). Decide from the provided text only; "
        "never invent provisions. Follow each indicator's scoring tree exactly.",
        "\n## Score polarity\n" + yaml.dump(ind_doc.get("score_polarity", {}), sort_keys=True, allow_unicode=True),
        "\n## Shared definitions\n" + yaml.dump(ind_doc.get("definitions", {}), sort_keys=True, allow_unicode=True),
    ]
    for b in blocks:
        keep = {k: b[k] for k in KEEP if k in b}
        parts.append(f"\n## {b['id']}\n" + yaml.dump(keep, sort_keys=True, allow_unicode=True, width=100))
    parts.append("\n## Cross-cutting scoring policy\n" + yaml.dump(
        {k: pol_doc[k] for k in ("scoring_policy", "edge_cases", "measure_inclusion") if k in pol_doc},
        sort_keys=True, allow_unicode=True, width=100))
    return "\n".join(parts)


def main() -> None:
    order = yaml.safe_load((OUT / "indicator_order.yaml").read_text(encoding="utf-8"))
    hand = yaml.safe_load((OUT / "indicators.yaml").read_text(encoding="utf-8"))
    pol = yaml.safe_load((OUT / "policies.yaml").read_text(encoding="utf-8"))
    by_id = {str(b["id"]): b for b in hand["indicators"]}
    seq = [e["id"] for e in order["indicators"] if e["status"] == "in_scope" and e["id"] in by_id]
    per_pillar = defaultdict(list)
    for iid in seq:
        per_pillar[int(iid.split(".")[0])].append(by_id[iid])
    lines = ["| Prefix | Indicators | Tiers | Characters |", "| :---- | ----: | :---- | ----: |"]
    for p in sorted(per_pillar):
        bl = per_pillar[p]
        tiers = "".join(sorted({b.get("tier", "?") for b in bl}))
        lines.append(f"| Pillar {p} | {len(bl)} | {tiers} | {len(render(hand, pol, bl)):,} |")
    everything = render(hand, pol, [by_id[i] for i in seq])
    lines.append(f"| All in one prefix | {len(seq)} | — | {len(everything):,} |")
    sys.stdout.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
