"""S1 sparse leg — bm25s over the prefilter corpus, indicators as queries.

Outputs data/index/bm25_top.npz: per indicator, the top-K corpus row indices and
scores (K=50k — far past any selection band; ranks beyond that are noise).
Row order shared with the dense leg via corpus_ids.json.
"""
from __future__ import annotations

import json
import time

import numpy as np

import bm25s
import Stemmer

from config.settings import INDICATORS, SETTINGS
from src.p3map.prefilter.queries import build_queries

TOP_K = SETTINGS.prefilter_topk   # PREFILTER_TOPK; 50,000 unless set


def run_bm25() -> None:
    t0 = time.time()
    ids: list[str] = []
    texts: list[str] = []
    with (SETTINGS.index_dir / "prefilter_corpus.jsonl").open(encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            ids.append(rec["provision_id"])
            texts.append(rec["text"])
    print(f"[bm25] corpus loaded: {len(ids)} rows, {time.time()-t0:.0f}s", flush=True)

    stemmer = Stemmer.Stemmer("english")
    corpus_tokens = bm25s.tokenize(texts, stopwords="en", stemmer=stemmer, show_progress=False)
    retriever = bm25s.BM25()
    retriever.index(corpus_tokens, show_progress=False)
    del texts, corpus_tokens
    print(f"[bm25] indexed, {time.time()-t0:.0f}s", flush=True)

    queries = build_queries()
    k = min(TOP_K, len(ids))
    out: dict[str, np.ndarray] = {}
    for ind in INDICATORS:
        qtok = bm25s.tokenize(queries[ind], stopwords="en", stemmer=stemmer, show_progress=False)
        docs, scores = retriever.retrieve(qtok, k=k, show_progress=False)
        out[f"{ind}_idx"] = docs[0].astype(np.int32)
        out[f"{ind}_score"] = scores[0].astype(np.float32)
        nz = int((scores[0] > 0).sum())
        print(f"[bm25] {ind}: top-{k}, nonzero={nz}, max={scores[0].max():.2f}", flush=True)

    (SETTINGS.index_dir / "corpus_ids.json").write_text(json.dumps(ids), encoding="utf-8")
    np.savez_compressed(SETTINGS.index_dir / "bm25_top.npz", **out)
    print(f"[bm25] done in {time.time()-t0:.0f}s -> bm25_top.npz", flush=True)


if __name__ == "__main__":
    run_bm25()
