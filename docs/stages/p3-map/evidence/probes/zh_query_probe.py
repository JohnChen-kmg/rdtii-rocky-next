"""Is the remaining Chinese shortfall the embedder, or the query's language?

BGE-M3 is cross-lingual, but cross-lingual retrieval is systematically weaker than same-language
retrieval. This scores China's provisions twice for the same indicator -- once with the English
query document the pipeline builds today, once with a Chinese one of the same shape -- and reports
where the gold-cited provisions land under each.

Reads the cached embeddings; embeds only the query documents. Writes nothing.
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

# Chinese query documents, same shape as the English ones: name, definition, keyword line.
# Written from the indicator definitions, using the terms Chinese instruments actually use.
ZH = {
    "6.2": (
        "本地存储要求\n"
        "法律要求将某类数据的副本存储在境内；数据仍可向境外提供，只要境内保留副本。"
        "关注副本的存储地点，而非数据保存期限，也不是建设基础设施的义务。"
        "覆盖个人信息或跨行业适用时限制程度更高。\n"
        "境内存储 在中华人民共和国境内存储 数据本地化 留存于境内 存储于境内 副本 本地留存 "
        "数据出境 境内保存 服务器设在境内 数据库设在境内 用户个人信息应当存储在境内"
    ),
    "7.4": (
        "个人信息保护负责人或个人信息保护影响评估要求\n"
        "强制性义务，要求指定个人信息保护负责人，或者开展个人信息保护影响评估。"
        "评分以负责人义务为准：普遍适用的负责人要求为1，仅限特定行业为0.5，没有为0。"
        "该义务必须是强制性的；建议性或者鼓励性的评估不计入。\n"
        "个人信息保护负责人 数据保护官 指定负责人 设立专门机构 个人信息保护影响评估 "
        "风险评估 事前评估 合规审计 网络安全负责人 专门安全管理机构 安全管理负责人 "
        "确定网络安全负责人 履行个人信息保护职责"
    ),
    "7.5": (
        "要求向政府提供个人数据的规定\n"
        "法律要求网络运营者、平台或者数据处理者向公安机关、国家安全机关或者其他主管部门"
        "提供用户个人信息、提供技术支持和协助，或者配合调取数据。"
        "无需司法审查即可调取时限制程度更高。\n"
        "为公安机关 国家安全机关 依法维护国家安全和侦查犯罪的活动提供技术支持和协助 "
        "配合调查 提供用户信息 调取数据 查询 依法留存 向有关部门提供 配合监督检查 "
        "接受监督检查 提供必要的支持和协助"
    ),
}
# The gold rows that miss or nearly miss, and the documents they cite.
TARGETS = {
    "6.2": ("r2-cn-043 Map Management Regulations", {"cn-npc5737ded9-001"}),
    "7.4": ("r2-cn-065 Cybersecurity Law", {"cn-cacedb0e7e1-001", "cn-npc0779bd03-001"}),
    "7.5": ("r2-cn-069 Internet Post Comments Provisions", {"cn-cacca76d37f-001"}),
}


def main() -> None:
    from sentence_transformers import SentenceTransformer

    from config.selection import load_config, params_for
    from src.p3map.prefilter.queries import build_queries

    docs, econs = [], []
    with open(f"{IDX}/prefilter_corpus.jsonl", encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            docs.append(r["doc_id"])
            econs.append(r["economy"])
    docs, econs = np.array(docs), np.array(econs)
    cn = np.flatnonzero(econs == "CN")
    print(f"[probe] {len(cn):,} Chinese rows of {len(docs):,}", flush=True)

    meta = json.loads(open(f"{IDX}/embed_meta.json", encoding="utf-8").read())
    emb = np.lib.format.open_memmap(f"{IDX}/embeddings.f16.npy", mode="r")
    cn_emb = np.asarray(emb[cn], dtype=np.float32)      # ~100 MB
    print(f"[probe] loaded {cn_emb.shape} embeddings, model {meta['model']}", flush=True)

    model = SentenceTransformer(meta["model"], device="cuda")
    model.max_seq_length = 512
    en = build_queries()
    cfg = load_config()

    inds = list(ZH)
    vec_en = model.encode([en[i] for i in inds], normalize_embeddings=True,
                          convert_to_numpy=True).astype(np.float32)
    vec_zh = model.encode([ZH[i] for i in inds], normalize_embeddings=True,
                          convert_to_numpy=True).astype(np.float32)

    print()
    print(f"{'cell':6s} {'query':8s} {'theta':>6s} {'rows>=theta':>12s} {'target rank':>12s} "
          f"{'cosine':>7s} {'selected?':>10s}   {'target'}")
    for j, ind in enumerate(inds):
        label, want = TARGETS[ind]
        p = params_for(ind, "CN", "zho", cfg=cfg)
        for name, vec in (("english", vec_en[j]), ("chinese", vec_zh[j])):
            sims = cn_emb @ vec
            order = np.argsort(-sims)
            ranked_docs = docs[cn[order]]
            hit = np.isin(ranked_docs, list(want))
            n_above = int((sims >= p.theta).sum())
            if hit.any():
                rank = int(np.argmax(hit)) + 1
                cos = float(sims[order][hit][0])
                # selected if within the ceiling and (above theta or within the floor)
                inside = rank <= p.max_candidates and (cos >= p.theta or rank <= p.min_candidates)
                mark = "YES" if inside else "no"
                print(f"{ind:6s} {name:8s} {p.theta:>6.3f} {n_above:>12,d} {rank:>12,d} "
                      f"{cos:>7.3f} {mark:>10s}   {label}")
            else:
                print(f"{ind:6s} {name:8s} {p.theta:>6.3f} {n_above:>12,d} {'not found':>12s} "
                      f"{'-':>7s} {'no':>10s}   {label}")
    print()
    print("cosine distribution over Chinese rows, per query language:")
    for j, ind in enumerate(inds):
        for name, vec in (("english", vec_en[j]), ("chinese", vec_zh[j])):
            sims = cn_emb @ vec
            print(f"  {ind} {name:8s} mean {sims.mean():.3f}  p50 {np.percentile(sims,50):.3f}  "
                  f"p99 {np.percentile(sims,99):.3f}  max {sims.max():.3f}")


if __name__ == "__main__":
    main()
