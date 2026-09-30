"""S1 dense leg — sentence-transformers embeddings, indicators as queries.

Encodes the full prefilter corpus once (fp16 memmap on disk, resume-safe) and
the 9 indicator query documents, then computes cosine top-K per indicator.

Outputs:
- data/index/embeddings.f16.npy   (n x dim, fp16, memmap-written in batches)
- data/index/embed_meta.json      (model, dim, n, done_rows — resume marker)
- data/index/dense_top.npz        (per indicator: top-K idx + cosine score)
"""
from __future__ import annotations

import json
import os
import time

import numpy as np

from config.settings import INDICATORS, SETTINGS
from src.p3map.prefilter.queries import build_queries

TOP_K = SETTINGS.prefilter_topk   # PREFILTER_TOPK; 50,000 unless set
FLUSH_EVERY = 40  # batches between meta flushes (resume granularity)


def _load_corpus_texts() -> list[str]:
    texts: list[str] = []
    with (SETTINGS.index_dir / "prefilter_corpus.jsonl").open(encoding="utf-8") as f:
        for line in f:
            texts.append(json.loads(line)["text"])
    return texts


def run_dense() -> None:
    from sentence_transformers import SentenceTransformer

    t0 = time.time()
    texts = _load_corpus_texts()
    n = len(texts)
    print(f"[dense] corpus: {n} rows; loading {SETTINGS.embed_model} on {SETTINGS.embed_device}", flush=True)

    model = SentenceTransformer(SETTINGS.embed_model, device=SETTINGS.embed_device)
    # BGE-M3 defaults to max_seq_length 8192 -> batches pad enormously (measured
    # 7 rows/s). Statute snippets are ~150-700 tokens; 512 is the retrieval-standard
    # cap and restores GPU throughput.
    model.max_seq_length = int(os.getenv("EMBED_MAX_TOKENS", "512"))
    dim = model.get_sentence_embedding_dimension()

    emb_path = SETTINGS.index_dir / "embeddings.f16.npy"
    meta_path = SETTINGS.index_dir / "embed_meta.json"
    start_row = 0
    if meta_path.exists() and emb_path.exists():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        if meta.get("model") == SETTINGS.embed_model and meta.get("n") == n:
            start_row = int(meta.get("done_rows", 0))
            print(f"[dense] resuming at row {start_row}", flush=True)

    mode = "r+" if start_row > 0 else "w+"
    emb = np.lib.format.open_memmap(
        emb_path, mode=mode, dtype=np.float16, shape=(n, dim)
    )

    bs = SETTINGS.embed_batch
    batch_i = 0
    for s in range(start_row, n, bs):
        chunk = texts[s : s + bs]
        vecs = model.encode(
            chunk,
            batch_size=bs,
            normalize_embeddings=True,
            show_progress_bar=False,
            convert_to_numpy=True,
        )
        emb[s : s + len(chunk)] = vecs.astype(np.float16)
        batch_i += 1
        if batch_i % FLUSH_EVERY == 0:
            emb.flush()
            meta_path.write_text(
                json.dumps({"model": SETTINGS.embed_model, "dim": dim, "n": n,
                            "done_rows": s + len(chunk)}), encoding="utf-8")
            done = s + len(chunk)
            rate = (done - start_row) / max(time.time() - t0, 1)
            eta = (n - done) / max(rate, 1)
            print(f"[dense] {done}/{n} rows, {rate:.0f} rows/s, ETA {eta/60:.0f} min", flush=True)
    emb.flush()
    meta_path.write_text(
        json.dumps({"model": SETTINGS.embed_model, "dim": dim, "n": n, "done_rows": n}),
        encoding="utf-8")
    print(f"[dense] embeddings complete in {(time.time()-t0)/60:.1f} min", flush=True)

    # --- query encodings + cosine top-K (corpus embeddings are L2-normalized)
    queries = build_queries()
    qvecs = model.encode(
        [queries[i] for i in INDICATORS],
        normalize_embeddings=True, convert_to_numpy=True,
    ).astype(np.float32)

    out: dict[str, np.ndarray] = {}
    k = min(TOP_K, n)
    block = 100_000
    sims_full = np.empty((n, len(INDICATORS)), dtype=np.float32)
    for s in range(0, n, block):
        sims_full[s : s + block] = emb[s : s + block].astype(np.float32) @ qvecs.T
    for j, ind in enumerate(INDICATORS):
        col = sims_full[:, j]
        idx = np.argpartition(-col, k - 1)[:k]
        idx = idx[np.argsort(-col[idx])]
        out[f"{ind}_idx"] = idx.astype(np.int32)
        out[f"{ind}_score"] = col[idx].astype(np.float32)
        print(f"[dense] {ind}: top cosine {col[idx][0]:.3f}, kth {col[idx][-1]:.3f}", flush=True)

    np.savez_compressed(SETTINGS.index_dir / "dense_top.npz", **out)
    print(f"[dense] done in {(time.time()-t0)/60:.1f} min -> dense_top.npz", flush=True)


if __name__ == "__main__":
    run_dense()
