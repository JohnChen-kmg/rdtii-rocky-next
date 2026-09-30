"""Verify config.selection against the Round 1 reference arm.

Run from stages/p3-map:
    python -X utf8 <this file>

Reads only; writes nothing. Reproduces the three checks in
rdtii-finale-3-mapping/notes/2026-09-26-selection-cap-function.md.
"""
from __future__ import annotations

import collections
import csv
import glob
import json
import re
import sys
from pathlib import Path

import numpy as np

STAGE = Path(r"C:\Users\woshi\Desktop\rdtii-rocky-finale\stages\p3-map")
sys.path.insert(0, str(STAGE))
from config.selection import load_config, select_cell  # noqa: E402

RA = Path(r"C:\Users\woshi\Desktop\RDTII\pipeline-data\rdtii-p3-map")
IND = ["P6-I1", "P6-I2", "P6-I3", "P6-I4", "P7-I1", "P7-I2", "P7-I3", "P7-I4", "P7-I5"]
ECON = ["SG", "MY", "AU"]
CFG = load_config()

ids = json.loads((RA / "data/index/corpus_ids.json").read_text(encoding="utf-8"))
dense = np.load(RA / "data/index/dense_top.npz")
sparse = np.load(RA / "data/index/bm25_top.npz")
doc_meta = json.loads((RA / "data/index/doc_meta.json").read_text(encoding="utf-8"))


def run(use_sparse: bool):
    sel, report = {}, []
    for ind in IND:
        d_idx, d_sc = dense[f"{ind}_idx"], dense[f"{ind}_score"]
        s_idx = sparse[f"{ind}_idx"]
        for e in ECON:
            pre = e.lower()
            ranked = ((ids[r], float(s)) for r, s in zip(d_idx, d_sc) if ids[r].startswith(pre))
            sp = [ids[int(r)] for r in s_idx if ids[int(r)].startswith(pre)] if use_sparse else None
            s = select_cell(ranked, ind, e, "eng", sparse=sp)
            sel[(e, ind)] = set(s.candidates)
            report.append(s.report())
    return sel, report


# ---- filed rows ---------------------------------------------------------------------
nk = {}
for f in glob.glob(str(RA / "out/discovery/newknown_*.jsonl")):
    for line in open(f, encoding="utf-8"):
        r = json.loads(line)
        nk[(r["economy"], r["indicator"], (r.get("law_name") or "").strip(),
            (r.get("article_section") or "").strip())] = r["provision_id"]
NAMES = {"Singapore": "SG", "Malaysia": "MY", "Australia": "AU"}
filed = []
for e in ECON:
    for row in csv.DictReader(open(RA / f"out/submission/records_{e}.csv", encoding="utf-8-sig")):
        pid = nk.get((NAMES.get(row["Economy"], e), row["Indicator ID"],
                      row["Law Name"].strip(), row["Article / Section"].strip()))
        if pid:
            filed.append((NAMES.get(row["Economy"], e), row["Indicator ID"], pid, row["Discovery Tag"]))

# ---- gold recall gate, as select.py computes it -------------------------------------
def norm(s):
    s = re.sub(r"\s+", " ", (s or "").lower())
    return re.sub(r"[^a-z0-9 ]", "", s).strip()


def fuzzy(a, b):
    ta, tb = set(a.split()), set(b.split())
    return bool(ta and tb) and len(ta & tb) / min(len(ta), len(tb)) >= 0.8


by_name = collections.defaultdict(list)
for did, dm in doc_meta.items():
    if dm.get("law_name"):
        by_name[norm(dm["law_name"])].append(did)

gold = []
for line in open(RA / "contracts/instrument/gold/gold_set.jsonl", encoding="utf-8"):
    g = json.loads(line)
    ind = g.get("indicator_id") or g.get("indicator")
    e = g.get("economy")
    laws = [x.strip() for x in re.split(r"[;\n]", g.get("law") or "") if x.strip()]
    if not (ind in IND and e in ECON and laws):
        continue
    arts = str(g.get("articles_mentioned") or "")
    if (arts.strip() in ("", "[]", "None")
            and str(g.get("raw_score", "")).strip() in ("0", "0.0")
            and ind not in ("P7-I1", "P7-I2")):
        continue
    cand = set()
    for law in laws:
        for nm, dids in by_name.items():
            if fuzzy(nm, norm(law)):
                cand.update(dids)
    if cand:
        gold.append((g["gold_id"], e, ind, cand))

# ---- verified fires and the 27 economy scores ---------------------------------------
fires = collections.defaultdict(list)
for f in glob.glob(str(RA / "out/verify/verified_*.jsonl")):
    for line in open(f, encoding="utf-8"):
        r = json.loads(line)
        if r.get("final_applies") is True:
            fires[(r["economy"], r["indicator"])].append(
                (r["provision_id"], str(r.get("final_score_hint"))))


def summarise(label, sel, report):
    pairs = sum(len(v) for v in sel.values()) / len(ECON)
    hit = sum(1 for g in gold if g[3] & {p.split("#")[0] for p in sel.get((g[1], g[2]), ())})
    kept = [t for t in filed if t[2] in sel[(t[0], t[1])]]
    new_all = [t for t in filed if t[3] == "NEW"]
    new_kept = [t for t in kept if t[3] == "NEW"]
    tot = got = changed = 0
    for k, lst in fires.items():
        tot += len(lst)
        keep = [x for x in lst if x[0] in sel.get(k, ())]
        got += len(keep)
        mx = lambda rs: max([float(s) for _, s in rs if s not in ("n/a", "None", "")], default=0.0)
        if mx(keep) != mx(lst):
            changed += 1
    print(f"\n--- {label}")
    print(f"  candidate pairs per economy : {pairs:,.0f}        (fixed caps: 13,627)")
    print(f"  gold recall gate            : {hit}/{len(gold)} = {hit/len(gold):.3f}   (gate requires >= 0.95)")
    print(f"  economy-score cells changed : {changed} of {len(fires)}")
    print(f"  filed rows retained         : {len(kept)}/{len(filed)} = {100*len(kept)/len(filed):.0f}%")
    print(f"  NEW rows retained           : {len(new_kept)}/{len(new_all)} = {100*len(new_kept)/len(new_all):.0f}%")
    print(f"  verified fires retained     : {got:,}/{tot:,} = {100*got/tot:.0f}%")
    bound = collections.Counter(r["bound_by"] for r in report)
    print(f"  cells by binding term       : {dict(bound)}")
    return hit == len(gold) and changed == 0


ok_plain = summarise("module as configured, dense only", *run(use_sparse=False))
ok_sparse = summarise("module as configured, with the BM25 top-up (6.4, 7.3)", *run(use_sparse=True))

print("\nper-cell report, with the sparse top-up:")
_, rep = run(use_sparse=True)
print(f"  {'cell':12s} {'cands':>6s} {'direct':>7s} {'gray':>6s} {'bound':>10s} {'theta':>6s}")
for r in rep:
    print(f"  {r['economy']}:{r['indicator']:<9s} {r['candidates']:6d} {r['direct']:7d} "
          f"{r['gray']:6d} {r['bound_by']:>10s} {r['theta_effective']:6.2f}")

sys.exit(0 if (ok_plain and ok_sparse) else 1)
