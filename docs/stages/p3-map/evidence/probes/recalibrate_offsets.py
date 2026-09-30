"""Set the language offset by measurement instead of by paired glosses.

The offsets in selection.json came from scoring 20 paired provisions per language as source text
and as an English gloss. That measured a *shift* in location. What the six-economy index shows is
that the distributions differ in SHAPE as well, so a shift cannot make the threshold land in the
same place for every language -- and it does not: theta lands at the 93rd percentile of China's
distribution and the 99th of Timor-Leste's, against 97th for the three English economies.

This computes, per language, the offset that puts theta at the same percentile as the English
economies reach for that indicator, and then evaluates the result: candidate volume, cells by
binding term, and the gold gate.

Reads the cached embeddings. Writes nothing.
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict

import numpy as np

sys.path.insert(0, "C:/Users/woshi/Desktop/rdtii-rocky-finale/stages/p3-map")
RUN = "C:/Users/woshi/Desktop/rdtii-finale-p3-runs/run_2026-09-27"
IDX = f"{RUN}/index"
ENG = ["AU", "SG", "MY"]
OTHER = {"TL": "por", "CN": "zho", "LA": "lao"}
LANG = {"AU": "eng", "MY": "eng", "SG": "eng", "CN": "zho", "LA": "lao", "TL": "por"}


def main() -> None:
    from sentence_transformers import SentenceTransformer

    from config.instrument import load as load_instrument
    from config.lawnames import same_law
    from config.selection import load_config, params_for, select_cell
    from config.settings import INDICATORS
    from src.p3map.prefilter.queries import build_queries

    pids, docs, econs = [], [], []
    with open(f"{IDX}/prefilter_corpus.jsonl", encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            pids.append(r["provision_id"]); docs.append(r["doc_id"]); econs.append(r["economy"])
    pids, docs, econs = np.array(pids), np.array(docs), np.array(econs)
    meta = json.loads(open(f"{IDX}/embed_meta.json", encoding="utf-8").read())
    emb = np.lib.format.open_memmap(f"{IDX}/embeddings.f16.npy", mode="r")
    model = SentenceTransformer(meta["model"], device="cuda")
    model.max_seq_length = 512
    q = build_queries()
    inds = list(INDICATORS)
    vecs = model.encode([q[i] for i in inds], normalize_embeddings=True,
                        convert_to_numpy=True).astype(np.float32)
    cfg = load_config()

    sims = {}          # econ -> (n, 9) cosines
    for e in LANG:
        rows = np.flatnonzero(econs == e)
        block = np.asarray(emb[rows], dtype=np.float32)
        sims[e] = (rows, block @ vecs.T)
        del block

    # the percentile the English economies reach, per indicator
    target = []
    for j, ind in enumerate(inds):
        ps = []
        for e in ENG:
            _, s = sims[e]
            th = params_for(ind, e, "eng", cfg=cfg).theta
            ps.append(100.0 * float((s[:, j] < th).sum()) / s.shape[0])
        target.append(float(np.mean(ps)))
    print("English economies' mean percentile, per indicator:")
    print("  " + "  ".join(f"{i}={t:.2f}" for i, t in zip(inds, target)))

    print()
    print("offset that lands theta at that same percentile:")
    print(f"{'lang':6s} {'now':>7s} {'measured':>9s}   per-indicator offsets")
    new_off = {}
    for e, lg in OTHER.items():
        _, s = sims[e]
        offs = []
        for j, ind in enumerate(inds):
            base = cfg["indicators"][ind]["theta"]
            want = float(np.percentile(s[:, j], target[j]))
            offs.append(want - base)
        new_off[lg] = float(np.median(offs))
        print(f"{lg:6s} {cfg['language_offset'][lg]:>+7.3f} {new_off[lg]:>+9.3f}   "
              + " ".join(f"{o:+.3f}" for o in offs))

    # ---- evaluate: volume, binding terms, gold
    ins = load_instrument()
    dm = json.loads(open(f"{IDX}/doc_meta.json", encoding="utf-8").read())
    rows_per_doc = Counter(docs.tolist())
    named = defaultdict(dict)
    for did, d in dm.items():
        ec = d.get("economy")
        if ec and rows_per_doc[did]:
            for nm in (d.get("law_name"), d.get("law_name_en"), d.get("law_name_original")):
                if nm:
                    named[ec][nm] = did
    gold = []
    for g in ins.gold():
        ec, ind = g.get("economy"), g.get("indicator")
        if ec not in LANG or ind not in inds:
            continue
        laws = [x.strip() for x in re.split(r"[;\n]", g.get("law") or "") if x.strip()]
        arts = str(g.get("articles_mentioned") or "")
        if (arts.strip() in ("", "[]", "None") and str(g.get("raw_score", "")).strip() in ("0", "0.0")
                and not ins.is_inverted(ind)):
            continue
        cand = {d for law in laws for nm, d in named[ec].items() if same_law(law, nm)}
        if cand:
            gold.append((g["gold_id"], ec, ind, cand))

    def evaluate(label, offsets):
        c = json.loads(json.dumps(cfg))
        for lg, v in (offsets or {}).items():
            c["language_offset"][lg] = round(v, 3)
        hits, per_e, bound = set(), Counter(), Counter()
        for j, ind in enumerate(inds):
            for e in LANG:
                rows, s = sims[e]
                col = s[:, j]
                order = np.argsort(-col)
                ranked = list(zip(pids[rows[order]].tolist(), col[order].tolist()))
                sel = select_cell(ranked, ind, e, LANG[e], cfg=c)
                per_e[e] += len(sel); bound[sel.bound] += 1
                chosen = set(docs[np.isin(pids, list(sel.candidates))].tolist())
                for gid, ge, gi, cand in gold:
                    if ge == e and gi == ind and (cand & chosen):
                        hits.add(gid)
        tot = sum(per_e.values())
        print(f"{label:34s} {tot:>7,d} " + " ".join(f"{per_e[e]:>6,d}" for e in ("AU","SG","MY","TL","CN","LA"))
              + f" {len(hits):>3d}/{len(gold):<3d} " + " ".join(f"{k}={bound[k]}" for k in ("theta","max","min","exhausted")))
        return hits

    print()
    print(f"{'configuration':34s} {'pairs':>7s} " + " ".join(f"{e:>6s}" for e in ("AU","SG","MY","TL","CN","LA"))
          + f" {'gold':>7s} cells by binding term")
    h0 = evaluate("as configured now", None)
    h1 = evaluate("offsets set by percentile", new_off)
    print()
    print("gold rows gained:", sorted(h1 - h0) or "none", "| lost:", sorted(h0 - h1) or "none")


if __name__ == "__main__":
    main()
