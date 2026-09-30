"""Two questions.

1. With a same-language query, does the ORIGINAL cap function (no per-economy overrides) select
   the Chinese gold rows on merit? If it does, the overrides were paying for a retrieval handicap.

2. Does Lao show the same handicap? Measured without writing any Lao: under the English query,
   compare how well each economy's cosine distribution SEPARATES (p99 minus p50). A cross-lingual
   handicap shows up as compression -- the top of the distribution pulled down toward the middle --
   and that is language-independent evidence.

Reads the cached embeddings. Writes nothing.
"""
from __future__ import annotations

import json
import sys

import numpy as np

sys.path.insert(0, "C:/Users/woshi/Desktop/rdtii-rocky-finale/stages/p3-map")
RUN = "C:/Users/woshi/Desktop/rdtii-finale-p3-runs/run_2026-09-27"
IDX = f"{RUN}/index"
ZH_PATH = ("C:/Users/woshi/AppData/Local/Temp/claude/"
           "c--Users-woshi-Desktop-rdtii-finale-3-mapping/"
           "f6afe178-5962-4643-a0e8-2462d64cf695/scratchpad/zh_query_probe.py")
TARGETS = {
    "6.2": ("r2-cn-043 Map Management Regulations", {"cn-npc5737ded9-001"}),
    "7.4": ("r2-cn-065 Cybersecurity Law", {"cn-cacedb0e7e1-001", "cn-npc0779bd03-001"}),
    "7.5": ("r2-cn-069 Internet Post Comments", {"cn-cacca76d37f-001"}),
}
ECON = ["AU", "SG", "MY", "TL", "CN", "LA"]
LANG = {"AU": "eng", "MY": "eng", "SG": "eng", "CN": "zho", "LA": "lao", "TL": "por"}


def main() -> None:
    from sentence_transformers import SentenceTransformer

    from config.selection import load_config, select_cell
    from src.p3map.prefilter.queries import build_queries

    sys.path.insert(0, ZH_PATH.rsplit("/", 1)[0])
    from zh_query_probe import ZH

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
    en = build_queries()
    inds3 = list(ZH)
    v_en = model.encode([en[i] for i in inds3], normalize_embeddings=True,
                        convert_to_numpy=True).astype(np.float32)
    v_zh = model.encode([ZH[i] for i in inds3], normalize_embeddings=True,
                        convert_to_numpy=True).astype(np.float32)

    # ---- 1. the ORIGINAL cap function (indicator blocks only, no economy overrides)
    base = load_config()
    plain = json.loads(json.dumps(base))
    plain["economy_overrides"] = {"_": "cleared for this probe"}
    cn = np.flatnonzero(econs == "CN")
    cn_emb = np.asarray(emb[cn], dtype=np.float32)
    print("1. the original cap function, no per-economy overrides")
    print(f"   {'cell':6s} {'query':8s} {'rank':>7s} {'cosine':>7s} {'floor':>6s} {'ceiling':>8s} "
          f"{'bound by':>9s} {'cands':>7s}  target selected?")
    for j, ind in enumerate(inds3):
        label, want = TARGETS[ind]
        for name, vec in (("english", v_en[j]), ("chinese", v_zh[j])):
            sims = cn_emb @ vec
            order = np.argsort(-sims)
            ranked = list(zip(pids[cn[order]].tolist(), sims[order].tolist()))
            sel = select_cell(ranked, ind, "CN", "zho", cfg=plain)
            chosen_docs = set(docs[np.isin(pids, list(sel.candidates))].tolist())
            got = bool(chosen_docs & want)
            hit = np.isin(docs[cn[order]], list(want))
            rank = int(np.argmax(hit)) + 1 if hit.any() else -1
            cos = float(sims[order][hit][0]) if hit.any() else float("nan")
            print(f"   {ind:6s} {name:8s} {rank:>7,d} {cos:>7.3f} {sel.params.min_candidates:>6d} "
                  f"{sel.params.max_candidates:>8d} {sel.bound:>9s} {len(sel):>7,d}  "
                  f"{'YES' if got else 'no'}  ({label})")
    del cn_emb

    # ---- 2. how well does the English query separate each economy's corpus?
    print()
    print("2. separation under the ENGLISH query, per economy (higher gap = better ranking signal)")
    print(f"   {'econ':5s} {'lang':5s} {'rows':>9s}" +
          "".join(f"{'p50':>7s}{'p99':>7s}{'max':>7s}{'gap':>7s}" for _ in inds3))
    print(f"   {'':5s} {'':5s} {'':>9s}" + "".join(f"{'--- ' + i + ' ---':>28s}" for i in inds3))
    for e in ECON:
        rows = np.flatnonzero(econs == e)
        block = np.asarray(emb[rows], dtype=np.float32)
        line = f"   {e:5s} {LANG[e]:5s} {len(rows):>9,d}"
        for j, ind in enumerate(inds3):
            s = block @ v_en[j]
            p50, p99, mx = (float(np.percentile(s, 50)), float(np.percentile(s, 99)), float(s.max()))
            line += f"{p50:>7.3f}{p99:>7.3f}{mx:>7.3f}{p99 - p50:>7.3f}"
        print(line)
        del block
    print()
    print("   for China the same three cells under a CHINESE query, for comparison:")
    cn_emb = np.asarray(emb[np.flatnonzero(econs == 'CN')], dtype=np.float32)
    line = f"   {'CN':5s} {'zho*':5s} {len(cn_emb):>9,d}"
    for j, ind in enumerate(inds3):
        s = cn_emb @ v_zh[j]
        p50, p99 = float(np.percentile(s, 50)), float(np.percentile(s, 99))
        line += f"{p50:>7.3f}{p99:>7.3f}{float(s.max()):>7.3f}{p99 - p50:>7.3f}"
    print(line)


if __name__ == "__main__":
    main()
