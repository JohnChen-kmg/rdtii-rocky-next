"""Is an absolute theta consistent across economies, or is it stricter on some than others?

For every (economy, indicator) this reports the PERCENTILE that theta + delta falls at inside that
economy's own cosine distribution. If the percentiles agree, the absolute rule is consistent and a
size or scale term would add nothing. If Lao's sit systematically higher, the rule is quietly
harsher on a small or compressed corpus, and a quantile theta would be the fix.

Also reports what a fixed-percentile rule would select, so the two designs can be compared on
volume and on the gold row each of them reaches.

Reads the cached embeddings. Writes nothing.
"""
from __future__ import annotations

import json
import sys

import numpy as np

sys.path.insert(0, "C:/Users/woshi/Desktop/rdtii-rocky-finale/stages/p3-map")
RUN = "C:/Users/woshi/Desktop/rdtii-finale-p3-runs/run_2026-09-27"
IDX = f"{RUN}/index"
ECON = ["AU", "SG", "MY", "TL", "CN", "LA"]
LANG = {"AU": "eng", "MY": "eng", "SG": "eng", "CN": "zho", "LA": "lao", "TL": "por"}
# the Lao gold row that misses, and the documents it cites
LA_TARGET = {"la-la1618-001", "la-la1700-001"}      # Financial Consumer Protection Decree
LA_CELL = "6.4"


def main() -> None:
    from sentence_transformers import SentenceTransformer

    from config.selection import load_config, params_for
    from config.settings import INDICATORS
    from src.p3map.prefilter.queries import build_queries

    docs, econs = [], []
    with open(f"{IDX}/prefilter_corpus.jsonl", encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            docs.append(r["doc_id"]); econs.append(r["economy"])
    docs, econs = np.array(docs), np.array(econs)
    meta = json.loads(open(f"{IDX}/embed_meta.json", encoding="utf-8").read())
    emb = np.lib.format.open_memmap(f"{IDX}/embeddings.f16.npy", mode="r")
    model = SentenceTransformer(meta["model"], device="cuda")
    model.max_seq_length = 512
    q = build_queries()
    inds = list(INDICATORS)
    vecs = model.encode([q[i] for i in inds], normalize_embeddings=True,
                        convert_to_numpy=True).astype(np.float32)
    cfg = load_config()

    print("percentile of theta+delta inside each economy's own cosine distribution")
    print(f"{'econ':5s} {'lang':5s} {'rows':>8s} " + " ".join(f"{i:>7s}" for i in inds) + "   mean")
    pct = {}
    la_sims = None
    for e in ECON:
        rows = np.flatnonzero(econs == e)
        block = np.asarray(emb[rows], dtype=np.float32)
        line, vals = f"{e:5s} {LANG[e]:5s} {len(rows):>8,d} ", []
        for j, ind in enumerate(inds):
            s = block @ vecs[j]
            th = params_for(ind, e, LANG[e], cfg=cfg).theta
            p = 100.0 * float((s < th).sum()) / len(s)
            vals.append(p)
            line += f"{p:>7.3f} "
            if e == "LA" and ind == LA_CELL:
                la_sims = (s.copy(), rows.copy())
        pct[e] = vals
        print(line + f"  {np.mean(vals):6.3f}")
        del block

    eng = np.mean([pct[e] for e in ("AU", "SG", "MY")], axis=0)
    print()
    print("gap against the English economies' mean percentile (positive = stricter on that economy)")
    print(f"{'econ':5s} " + " ".join(f"{i:>7s}" for i in inds) + "   mean")
    for e in ("TL", "CN", "LA"):
        d = np.array(pct[e]) - eng
        print(f"{e:5s} " + " ".join(f"{x:>+7.3f}" for x in d) + f"  {d.mean():+6.3f}")

    # what a fixed-percentile theta would do for the Lao cell that misses
    print()
    s, rows = la_sims
    order = np.argsort(-s)
    hit = np.isin(docs[rows[order]], list(LA_TARGET))
    rank = int(np.argmax(hit)) + 1
    cos = float(s[order][hit][0])
    p_now = params_for(LA_CELL, "LA", "lao", cfg=cfg)
    print(f"LA {LA_CELL}: the gold row's best provision is at rank {rank:,} of {len(s):,}, "
          f"cosine {cos:.3f}")
    print(f"  absolute theta now {p_now.theta:.3f} -> "
          f"{int((s >= p_now.theta).sum()):,} rows clear it "
          f"({100.0 * float((s < p_now.theta).sum()) / len(s):.3f}th percentile)")
    for q_pct in (99.9, 99.8, 99.5, 99.0, 98.0, 96.0):
        th = float(np.percentile(s, q_pct))
        n = int((s >= th).sum())
        print(f"  quantile theta at p{q_pct:<5} = {th:.3f} -> {n:>6,d} rows, "
              f"gold row {'INSIDE' if cos >= th and rank <= p_now.max_candidates else 'outside'}"
              f" (ceiling {p_now.max_candidates})")


if __name__ == "__main__":
    main()
