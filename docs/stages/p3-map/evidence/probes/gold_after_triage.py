"""Gold-set survival through the stages that have actually run: select, then triage.

Same matcher and same exclusions as evidence/probes/gold_funnel.py, pointed at run_2026-09-27
instead of the frozen Round 1 arm. A gold row counts as surviving a stage when at least one
provision of the law it cites reached that stage. Reads only.

Stages that exist in this run: resolvable -> selected (direct + gray) -> triage keep.
S4 has not run, so the funnel stops there.
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict

sys.path.insert(0, "C:/Users/woshi/Desktop/rdtii-rocky-finale/stages/p3-map")
RUN = "C:/Users/woshi/Desktop/rdtii-finale-p3-runs/run_2026-09-27"
IDX, OUT = f"{RUN}/index", f"{RUN}/out"
FRESH = ["CN", "LA", "TL"]                 # the economies triage was scoped to
ALL6 = ["AU", "SG", "MY", "CN", "LA", "TL"]
STAGES = ["in the corpus", "selected", "kept by triage"]


def main() -> None:
    from config.instrument import load as load_instrument
    from config.lawnames import same_law

    # corpus: which docs actually carry provisions, and their names
    rows_per_doc: Counter = Counter()
    doc_of_pid: dict[str, str] = {}
    with open(f"{IDX}/prefilter_corpus.jsonl", encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            rows_per_doc[r["doc_id"]] += 1
            doc_of_pid[r["provision_id"]] = r["doc_id"]
    dm = json.loads(open(f"{IDX}/doc_meta.json", encoding="utf-8").read())
    named = defaultdict(dict)
    for did, d in dm.items():
        e = d.get("economy")
        if e and rows_per_doc[did]:
            for nm in (d.get("law_name"), d.get("law_name_en"), d.get("law_name_original")):
                if nm:
                    named[e][nm] = did

    # stage artefacts
    selected = defaultdict(set)
    for band in ("direct", "gray"):
        with open(f"{OUT}/select/{band}_pairs.jsonl", encoding="utf-8") as f:
            for line in f:
                p = json.loads(line)
                selected[(p["economy"], p["indicator"])].add(p["doc_id"])
    kept = defaultdict(set)
    with open(f"{OUT}/triage/haiku_results.jsonl", encoding="utf-8") as f:
        for line in f:
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if r.get("keep"):
                d = doc_of_pid.get(r["provision_id"])
                if d:
                    kept[(r.get("economy"), r.get("indicator"))].add(d)
    # the direct band bypasses triage entirely -- it goes straight to the mapper
    direct = defaultdict(set)
    with open(f"{OUT}/select/direct_pairs.jsonl", encoding="utf-8") as f:
        for line in f:
            p = json.loads(line)
            direct[(p["economy"], p["indicator"])].add(p["doc_id"])

    ins = load_instrument()
    by_econ, by_ind = defaultdict(Counter), defaultdict(Counter)
    lost, unresolvable = [], []
    for g in ins.gold():
        e, ind = g.get("economy"), g.get("indicator")
        if e not in ALL6 or ind not in ins.ids:
            continue
        laws = [x.strip() for x in re.split(r"[;\n]", g.get("law") or "") if x.strip()]
        arts = str(g.get("articles_mentioned") or "")
        # a score-0 row with no article cited is an absence claim: nothing to retrieve
        if (arts.strip() in ("", "[]", "None") and str(g.get("raw_score", "")).strip() in ("0", "0.0")
                and not ins.is_inverted(ind)):
            continue
        docs = {d for law in laws for nm, d in named[e].items() if same_law(law, nm)}
        if not docs:
            unresolvable.append((e, ind, g["gold_id"], laws[0][:44] if laws else ""))
            continue
        k = (e, ind)
        reached = "in the corpus"
        if docs & selected[k]:
            reached = "selected"
            # survives triage if a kept pair OR a direct-band pair (direct skips triage)
            if docs & (kept[k] | direct[k]):
                reached = "kept by triage"
        idx = STAGES.index(reached)
        for s in STAGES[:idx + 1]:
            by_econ[e][s] += 1
            by_ind[ind][s] += 1
        if idx < len(STAGES) - 1:
            lost.append((e, ind, g["gold_id"], STAGES[idx + 1], laws[0][:40] if laws else ""))

    def table(title, data, key):
        print(f"\n{title}")
        print(f"{key:9s} " + " ".join(f"{s:>15s}" for s in STAGES) + "    survival")
        agg = Counter()
        for k in sorted(data, key=lambda x: -data[x]["in the corpus"]):
            c = data[k]
            agg.update(c)
            base = c["in the corpus"]
            pct = f"{c['kept by triage']/base:>7.1%}" if base else "      -"
            print(f"{k:9s} " + " ".join(f"{c[s]:>15d}" for s in STAGES) + f"    {pct}")
        base = agg["in the corpus"]
        print(f"{'ALL':9s} " + " ".join(f"{agg[s]:>15d}" for s in STAGES)
              + f"    {agg['kept by triage']/base:>7.1%}")
        return agg

    print("Gold rows whose cited law is in the corpus, and how far they got.")
    print("A row survives a stage when >=1 provision of its cited law reached that stage.")
    print("Score-0 rows citing no article are excluded: they assert an absence, so there is")
    print("nothing to retrieve. The direct band bypasses triage and counts as surviving it.")
    agg = table("by economy", by_econ, "economy")
    table("by indicator", by_ind, "indicator")

    fresh = Counter()
    for e in FRESH:
        fresh.update(by_econ[e])
    print(f"\nthe three economies triage actually ran on (CN, LA, TL):")
    print(f"  in the corpus {fresh['in the corpus']}, selected {fresh['selected']}, "
          f"kept {fresh['kept by triage']}  ->  {fresh['kept by triage']/fresh['in the corpus']:.1%}")

    if lost:
        print(f"\nthe {len(lost)} gold rows that stopped short:")
        for e, ind, gid, missing, law in sorted(lost):
            print(f"  {e} {ind:5s} {gid:14s} never {missing:15s} {law}")
    print(f"\ngold rows whose cited law is NOT in the corpus at all: {len(unresolvable)}")
    for e, ind, gid, law in sorted(unresolvable)[:12]:
        print(f"  {e} {ind:5s} {gid:14s} {law}")


if __name__ == "__main__":
    main()
