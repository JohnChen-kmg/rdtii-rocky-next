"""Coverage table for the instrument: every in-scope ID with pillar, tier and evidence depth.

Usage: python scripts/report_coverage.py [--out PATH]   (markdown to stdout, or to PATH)
Feeds the C1b coverage claim: which indicators exist, at what depth, backed by how many
exemplars and baseline rows.
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

import yaml

from rdtii_examples import DATA, REPO

OUT = REPO / "output"


def main() -> None:
    order = yaml.safe_load((OUT / "indicator_order.yaml").read_text(encoding="utf-8"))
    blocks = {str(b["id"]): b for b in yaml.safe_load((OUT / "indicators.yaml").read_text(encoding="utf-8"))["indicators"]}
    refs = yaml.safe_load((DATA / "guide_refs.yaml").read_text(encoding="utf-8")) or {}
    gold = [json.loads(l) for l in (OUT / "gold" / "gold_set.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    gold_by = defaultdict(list)
    for g in gold:
        gold_by[g["indicator"]].append(g)

    rows, tiers, pillar_sum = [], Counter(), defaultdict(Counter)
    for e in order["indicators"]:
        iid = e["id"]
        if e["status"] != "in_scope":
            rows.append(f"| {iid} | {e['pillar']} | {e['name']} | out of scope | — | — | — | — | — | — | — | — |")
            continue
        b = blocks.get(iid, {})
        sig_p = OUT / "signatures" / f"{iid}.yaml"
        sig = yaml.safe_load(sig_p.read_text(encoding="utf-8")) if sig_p.exists() else {}
        exs = sig.get("exemplars", [])
        g = gold_by.get(iid, [])
        flags = Counter((x.get("label_flag") or {}).get("status") for x in g)
        tier = b.get("tier", "missing")
        tiers[tier] += 1
        pillar_sum[e["pillar"]][tier] += 1
        scores = " / ".join(str(v) for v in (b.get("scoring") or {}).get("values", []))
        ref = refs.get(iid) or {}
        pages = ref.get("guide_pages") or []
        page_txt = (f"p.{pages[0]}" if len(pages) == 1 else f"pp.{pages[0]}-{pages[-1]}") if pages else "—"
        traps = sum(1 for d in b.get("disambiguation") or [] if str(d).startswith("TRAP"))
        rows.append(
            f"| {iid} | {e['pillar']} | {e['name']} | {tier} | {scores} | {e['evidence']} | {traps} | "
            f"{len(sig.get('keywords', []))} | {len(exs)} ({len({x['economy'] for x in exs})} econ.) | "
            f"{len(g)} ({len({x['economy'] for x in g})} econ.) | "
            f"{flags.get('suspect', 0)}/{flags.get('advisory', 0)}/{flags.get('host_marked', 0)}/{flags.get('candidate', 0)} | {page_txt} |")

    lines = [
        f"# Instrument coverage — generated {date.today().isoformat()}",
        "",
        f"Listed: {order['listed']} · in scope: {order['in_scope']} · tiers: "
        + ", ".join(f"{k} {v}" for k, v in sorted(tiers.items()))
        + f" · baseline rows: {len(gold)} across {len({g['economy'] for g in gold})} economies.",
        "",
        "Tier A = the Round 1 codebook, used in the Round 1 run and the 30 September submission · Tier B = drafted at "
        "Tier A depth with the same elements, not yet reviewed · Tier C = host text only, no traps (none when the count "
        "is absent). All tiers sit in one file, `indicators.yaml`, in host order. "
        "Flags = suspect / advisory (reviewed) / host_marked (host verification said Not correct) / candidate (machine, unreviewed).",
        "",
        "## By pillar",
        "",
        "| Pillar | Indicators | Tier A | Tier B | Tier C |",
        "| ----: | ----: | ----: | ----: | ----: |",
    ]
    for p in sorted(pillar_sum):
        c = pillar_sum[p]
        lines.append(f"| {p} | {sum(c.values())} | {c.get('A', 0)} | {c.get('B', 0)} | {c.get('C', 0)} |")
    lines += [
        "",
        "## Every indicator",
        "",
        "| ID | Pillar | Indicator | Tier | Scores | Evidence | TRAP lines | Keywords | Exemplars | Baseline rows | Flags s/a/h/c | Guide |",
        "| :---- | ----: | :---- | :---- | :---- | :---- | ----: | ----: | :---- | :---- | :---- | :---- |",
        *rows,
    ]
    text = "\n".join(lines) + "\n"
    if "--out" in sys.argv:
        Path(sys.argv[sys.argv.index("--out") + 1]).write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)


if __name__ == "__main__":
    main()
