"""Where gold rows are lost, stage by stage, measured on the frozen Round 1 arm.

Every stage of that run left an artifact, so this is measurement rather than projection: for each
gold row whose cited law is in the corpus, did a provision of that law reach the candidate set,
the mapper, a fire, verification, and finally the CSV?

Reads only. The arm is never written to.
"""
from __future__ import annotations

import csv
import json
import re
import sys
from collections import Counter, defaultdict

sys.path.insert(0, "C:/Users/woshi/Desktop/rdtii-rocky-finale/stages/p3-map")
REF = "C:/Users/woshi/Desktop/RDTII/pipeline-data/rdtii-p3-map"
ECON = ["SG", "MY", "AU"]
LEG = {"P6-I1": "6.1", "P6-I2": "6.2", "P6-I3": "6.3", "P6-I4": "6.4",
       "P7-I1": "7.1", "P7-I2": "7.2", "P7-I3": "7.3", "P7-I4": "7.4", "P7-I5": "7.5"}
STAGES = ["resolvable", "selected", "mapped", "fired", "verified", "filed"]


def main() -> None:
    from config.instrument import load as load_instrument
    from config.lawnames import same_law
    from config.selection import load_config

    cls = {i: b.get("class", "?") for i, b in load_config()["indicators"].items()}

    dm = json.loads(open(f"{REF}/data/index/doc_meta.json", encoding="utf-8").read())
    rows_per_doc: Counter = Counter()
    doc_of_pid: dict[str, str] = {}
    with open(f"{REF}/data/index/prefilter_corpus.jsonl", encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            rows_per_doc[r["doc_id"]] += 1
            doc_of_pid[r["provision_id"]] = r["doc_id"]
    named = defaultdict(dict)
    for did, d in dm.items():
        e = d.get("economy")
        if e and rows_per_doc[did]:
            for nm in (d.get("law_name"), d.get("law_name_en"), d.get("law_name_original")):
                if nm:
                    named[e][nm] = did

    # stage artifacts
    selected = defaultdict(set)              # (econ, ind) -> doc_ids
    for band in ("direct", "gray"):
        with open(f"{REF}/out/select/{band}_pairs.jsonl", encoding="utf-8") as f:
            for line in f:
                p = json.loads(line)
                selected[(p["economy"], LEG.get(p["indicator"], p["indicator"]))].add(p["doc_id"])
    mapped, fired, verified, filed = defaultdict(set), defaultdict(set), defaultdict(set), defaultdict(list)
    for e in ECON:
        with open(f"{REF}/out/map/verdicts_{e}.jsonl", encoding="utf-8") as f:
            for line in f:
                row = json.loads(line)
                if "error" in row:
                    continue
                d = doc_of_pid.get(row["provision_id"], row.get("doc_id"))
                for ind in (LEG.get(c, c) for c in row.get("candidates", [])):
                    mapped[(e, ind)].add(d)
                for v in row["verdicts"]:
                    ind = LEG.get(v["indicator"], v["indicator"])
                    mapped[(e, ind)].add(d)
                    if v["applies"]:
                        fired[(e, ind)].add(d)
        with open(f"{REF}/out/verify/verified_{e}.jsonl", encoding="utf-8") as f:
            for line in f:
                r = json.loads(line)
                if r.get("final_applies"):
                    verified[(e, LEG.get(r["indicator"], r["indicator"]))].add(
                        doc_of_pid.get(r["provision_id"], ""))
        with open(f"{REF}/out/submission/records_{e}.csv", encoding="utf-8-sig") as f:
            for r in csv.DictReader(f):
                filed[(e, LEG.get(r["Indicator ID"], r["Indicator ID"]))].append(r["Law Name"])

    ins = load_instrument()
    by_econ = defaultdict(Counter)
    by_class = defaultdict(Counter)
    lost = []
    for g in ins.gold():
        e, ind = g.get("economy"), g.get("indicator")
        if e not in ECON or ind not in ins.ids:
            continue
        laws = [x.strip() for x in re.split(r"[;\n]", g.get("law") or "") if x.strip()]
        arts = str(g.get("articles_mentioned") or "")
        if (arts.strip() in ("", "[]", "None") and str(g.get("raw_score", "")).strip() in ("0", "0.0")
                and not ins.is_inverted(ind)):
            continue
        docs = {d for law in laws for nm, d in named[e].items() if same_law(law, nm)}
        if not docs:
            continue
        k = (e, ind)
        reached = "resolvable"
        for stage, table in (("selected", selected), ("mapped", mapped),
                             ("fired", fired), ("verified", verified)):
            if docs & table[k]:
                reached = stage
            else:
                break
        if reached == "verified" and any(
                any(same_law(law, nm) for law in laws) for nm in filed[k]):
            reached = "filed"
        idx = STAGES.index(reached)
        for s in STAGES[:idx + 1]:
            by_econ[e][s] += 1
            by_class[cls.get(ind, "?")][s] += 1
        if idx < len(STAGES) - 1:
            lost.append((e, ind, g["gold_id"], STAGES[idx + 1], laws[0][:44]))

    def table(title, data, keyname):
        print(f"\n{title}")
        print(f"{keyname:22s} " + " ".join(f"{s:>10s}" for s in STAGES) + "   end-to-end")
        agg = Counter()
        for k in sorted(data, key=lambda x: -data[x]["resolvable"]):
            c = data[k]
            agg.update(c)
            rate = c["filed"] / c["resolvable"] if c["resolvable"] else 0
            print(f"{k:22s} " + " ".join(f"{c[s]:>10d}" for s in STAGES) + f"   {rate:>8.1%}")
        rate = agg["filed"] / agg["resolvable"] if agg["resolvable"] else 0
        print(f"{'ALL':22s} " + " ".join(f"{agg[s]:>10d}" for s in STAGES) + f"   {rate:>8.1%}")
        print(f"{'stage survival':22s} " + " ".join(
            f"{(agg[s] / agg[STAGES[i - 1]] if i and agg[STAGES[i - 1]] else 1):>9.1%} "
            for i, s in enumerate(STAGES)))

    table("gold rows reaching each stage, by economy", by_econ, "economy")
    table("the same, by indicator class", by_class, "class")
    print("\nwhere each lost row stopped:")
    for e, ind, gid, missing_stage, law in sorted(lost):
        print(f"  {e} {ind:5s} {gid:12s} never {missing_stage:9s} {law}")


if __name__ == "__main__":
    main()
