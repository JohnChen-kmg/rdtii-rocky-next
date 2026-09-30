"""S2 — candidate selection and the recall gate.

Two modes, chosen by SELECT_MODE:

**scores** (default) — `config/selection.py`. Per (economy × indicator), take every provision
whose dense cosine against the indicator's query document clears θ(indicator) + δ(language),
clamped by that indicator's floor and ceiling; at or above the 0.65 band a candidate goes
straight to the mapper, between θ and the band it gets the cheap triage screen first. Derivation
and the verification against Round 1: rdtii-finale-3-mapping/notes/2026-09-26-selection-cap-
function.md. Measured against the reference arm: 7,864 candidate pairs per economy against
13,627, gold recall unchanged, no economy score changed, 120 of 135 filed rows retained.

**caps** — Round 1 exactly: RRF over the BM25 and dense rank lists, hint boosts, then a fixed
per-cell cap for the direct band and 3× that for the gray band. Kept so a surprise on 15 October
is one variable from reverting.

Recall gate (decision #11: allowlist OFF, organic only), in both modes: for every resolvable
gold row, its (doc, indicator) must appear in direct+gray candidates. Gold is a yardstick; it
never adds a candidate.

Outputs: out/select/direct_pairs.jsonl, gray_pairs.jsonl, select_report.json.
"""
from __future__ import annotations

import json
import re
import time
from collections import Counter, defaultdict

import numpy as np

from config import manifest
from config.indicator_ids import legacy_of, pillar_of
from config.instrument import load as load_instrument
from config.languages import iso
from config.lawnames import same_law
from config.selection import language_offset, load_config, select_cell
from config.settings import ECONOMIES, INDICATORS, SETTINGS

MODES = ("scores", "caps")

# ---- caps mode (Round 1) ---------------------------------------------------------------
RRF_K = 60
# Appendix A per-cell direct-band caps (per economy), keyed decimally.
CAPS = {
    "6.1": 500, "6.2": 300, "6.3": 200, "6.4": 500,
    "7.1": 150, "7.2": 200, "7.3": 600, "7.4": 200, "7.5": 600,
}
GRAY_MULT = 3          # gray band ceiling = GRAY_MULT x cap per cell
HINT_BOOST = 0.35      # multiplicative RRF boost for aligned obligation_type
NONPERSONAL_DAMP = 0.85  # data_type=non-personal down-weights P7 (never removes)
# INERT as of hand-off #2: scope, data_type and obligation_type are null on all 766,526 records
# (`tags_source: not_tagged`), so neither boost can fire. Kept, keyed decimally, in case tagging
# returns; if it does not, remove both in the post-freeze cleanup.
OBLIGATION_ALIGN = {"ban": "6.1", "storage": "6.2",
                    "infrastructure": "6.3", "conditional": "6.4"}

# selection.json keys its offsets by ISO 639-3; config/languages.py knows both forms the
# corpus writes, and the emitter reads the same table in the other direction for column N.


def _languages() -> dict[str, str | None]:
    """economy -> the ISO code its corpus is mostly written in, weighted by provision count.

    One language per cell, not per provision: θ + δ is calibrated per cell, and every economy
    here has one dominant language of legislation. None means the corpus does not say — true
    today of all 1,085 Chinese laws, whose `language_of_source` is null while their provisions
    carry `language_of_source_name: Chinese` (note filed with the extraction workstream). An
    unknown language takes selection.json's conservative default offset.
    """
    path = SETTINGS.index_dir / "doc_meta.json"
    if not path.exists():
        return {}
    tally: dict[str, Counter] = defaultdict(Counter)
    for dm in json.loads(path.read_text(encoding="utf-8")).values():
        econ = dm.get("economy")
        if not econ:
            continue
        code = iso(dm.get("language_of_source")) or iso(dm.get("language_of_source_name"))
        tally[econ][code] += int(dm.get("provision_count") or 1)
    return {econ: c.most_common(1)[0][0] for econ, c in tally.items()}


def _leg_top(leg, ind: str) -> np.ndarray:
    """Top-K row indices for one indicator, from an index of either vintage.

    An index built before the decimal migration keys its arrays "P6-I1_idx"; one built after keys
    them "6.1_idx". Reading both means a 3.5-hour embedding run survives the migration.
    """
    return _leg_array(leg, ind, "idx")


def _leg_scores(leg, ind: str) -> np.ndarray:
    return _leg_array(leg, ind, "score")


def _leg_array(leg, ind: str, kind: str) -> np.ndarray:
    for key in (f"{ind}_{kind}", f"{legacy_of(ind)}_{kind}"):
        if key in leg:
            return leg[key]
    raise KeyError(f"no top-K {kind} array for indicator {ind} in the index "
                   f"(tried {ind}_{kind} and {legacy_of(ind)}_{kind})")


def _economies(meta: list[dict]) -> list[str]:
    """Whichever economies the corpus holds, narrowed by ECONOMIES when that is set."""
    present = sorted({m["economy"] for m in meta if m.get("economy")})
    if not ECONOMIES:
        return present
    wanted = [e for e in ECONOMIES if e in present]
    missing = [e for e in ECONOMIES if e not in present]
    if missing:
        print(f"[select] ECONOMIES names {', '.join(missing)}, absent from the corpus; "
              f"present: {', '.join(present)}", flush=True)
    return wanted


def _load_corpus_meta() -> list[dict]:
    rows = []
    with (SETTINGS.index_dir / "prefilter_corpus.jsonl").open(encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            rows.append({
                "provision_id": r["provision_id"], "doc_id": r["doc_id"],
                "economy": r["economy"], "law_name": r.get("law_name"),
                "article_section": r.get("article_section"),
                "obligation_type": r.get("obligation_type"),
                "data_type": r.get("data_type"),
                "lang_malay_guess": r.get("lang_malay_guess", False),
            })
    return rows


def _pair(m: dict, ind: str, score: float, signal: str) -> str:
    return json.dumps({
        "provision_id": m["provision_id"], "doc_id": m["doc_id"],
        "economy": m["economy"], "indicator": ind,
        "score": round(score, 6), "signal": signal,
        "law_name": m["law_name"], "article_section": m["article_section"],
    }, ensure_ascii=False) + "\n"


def run_select() -> dict:
    t0 = time.time()
    mode = (SETTINGS.select_mode or "").strip().lower()
    if mode not in MODES:
        raise SystemExit(f"[select] SELECT_MODE={SETTINGS.select_mode!r}; expected one of "
                         f"{', '.join(MODES)}")
    meta = _load_corpus_meta()
    n = len(meta)
    bm = np.load(SETTINGS.index_dir / "bm25_top.npz")
    dn = np.load(SETTINGS.index_dir / "dense_top.npz")
    economies = _economies(meta)
    if not economies:
        raise SystemExit("[select] no economies to select for; check ECONOMIES and the corpus")
    print(f"[select] mode {mode} · {n:,} corpus rows · economies {', '.join(economies)} · "
          f"{len(INDICATORS)} indicators", flush=True)

    out_dir = SETTINGS.out_dir / "select"
    out_dir.mkdir(parents=True, exist_ok=True)

    direct_f = (out_dir / "direct_pairs.jsonl").open("w", encoding="utf-8")
    gray_f = (out_dir / "gray_pairs.jsonl").open("w", encoding="utf-8")
    report: dict = {"mode": mode, "cells": {}, "totals": Counter()}
    cell_pairs: dict[tuple, set] = defaultdict(set)  # (econ, ind) -> doc_ids (recall gate)

    try:
        if mode == "scores":
            _select_by_score(meta, bm, dn, economies, direct_f, gray_f, cell_pairs, report)
        else:
            _select_by_caps(meta, bm, dn, economies, direct_f, gray_f, cell_pairs, report)
    finally:
        direct_f.close()
        gray_f.close()

    report["recall_gate"] = _recall_gate(economies, cell_pairs)
    report["totals"] = dict(report["totals"])
    report["elapsed_seconds"] = round(time.time() - t0, 1)
    (out_dir / "select_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    rg = report["recall_gate"]
    manifest.record("select", mode=mode, economies=list(economies),
                    direct=report["totals"].get("direct", 0),
                    gray=report["totals"].get("gray", 0),
                    gold_recall=rg["recall"], gold_rows=rg["resolvable_gold_rows"],
                    selection_config=report.get("selection_config"))
    print(f"[select] direct={report['totals'].get('direct', 0)} "
          f"gray={report['totals'].get('gray', 0)} recall={rg['recall']} "
          f"({rg['hit']}/{rg['resolvable_gold_rows']}) misses={len(rg['misses'])}", flush=True)
    return report


def _select_by_score(meta, bm, dn, economies, direct_f, gray_f, cell_pairs, report) -> None:
    """Threshold on the dense cosine, clamped by the per-indicator floor and ceiling."""
    cfg = load_config(SETTINGS.selection_config or None)
    langs = _languages()
    by_pid = {m["provision_id"]: m for m in meta}
    report["selection_config"] = SETTINGS.selection_config or "config/selection.json"
    report["selection_version"] = cfg.get("version")
    report["languages"] = {e: {"language": langs.get(e),
                               "theta_offset": language_offset(langs.get(e), cfg)}
                           for e in economies}
    for e in economies:
        lg = report["languages"][e]
        print(f"[select] {e}: language {lg['language'] or 'unknown'} "
              f"(theta offset {lg['theta_offset']:+.3f})", flush=True)

    wanted = set(economies)
    for ind in INDICATORS:
        d_idx, d_sc = _leg_top(dn, ind), _leg_scores(dn, ind)
        ranked: dict[str, list] = defaultdict(list)
        for i, s in zip(d_idx, d_sc):
            m = meta[int(i)]
            if m["economy"] in wanted:
                ranked[m["economy"]].append((m["provision_id"], float(s)))
        sparse: dict[str, list] = defaultdict(list)
        for i in _leg_top(bm, ind):
            m = meta[int(i)]
            if m["economy"] in wanted:
                sparse[m["economy"]].append(m["provision_id"])

        for econ in economies:
            sel = select_cell(ranked[econ], ind, econ, langs.get(econ),
                              sparse=sparse[econ] or None, cfg=cfg)
            score_of = dict(ranked[econ])
            for band, pids, fh in (("direct", sel.direct, direct_f), ("gray", sel.gray, gray_f)):
                for pid in pids:
                    m = by_pid[pid]
                    # a sparse top-up row has no dense score of its own
                    fh.write(_pair(m, ind, score_of.get(pid, 0.0), "dense_cosine"))
                    cell_pairs[(econ, ind)].add(m["doc_id"])
                    report["totals"][band] += 1
            report["cells"][f"{econ}:{ind}"] = sel.report()
            # A cell that ran out of ranking below its floor is the one shape that silently
            # produces no rows: the top-K is global across economies, so an economy the dense
            # leg ranks low can be starved before its own floor is met.
            if sel.bound == "exhausted":
                print(f"[select] WARNING {econ}:{ind} exhausted the ranking at {len(sel)} "
                      f"candidates (floor {sel.params.min_candidates}); the top-K may not reach "
                      f"this economy", flush=True)
        cells = [report["cells"][f"{e}:{ind}"] for e in economies]
        print(f"[select] {ind}: " + ", ".join(
            f"{e}={c['candidates']}({c['direct']}d/{c['gray']}g,{c['bound_by']})"
            for e, c in zip(economies, cells)), flush=True)


def _select_by_caps(meta, bm, dn, economies, direct_f, gray_f, cell_pairs, report) -> None:
    """Round 1 exactly: RRF fusion, hint boosts, fixed per-cell caps."""
    n = len(meta)
    for ind in INDICATORS:
        rrf = np.zeros(n, dtype=np.float32)
        for leg in (bm, dn):
            idx = _leg_top(leg, ind)
            ranks = np.arange(1, len(idx) + 1, dtype=np.float32)
            rrf[idx] += 1.0 / (RRF_K + ranks)
        # hint boosts (soft, never gates)
        for i, m in enumerate(meta):
            if rrf[i] == 0.0:
                continue
            if OBLIGATION_ALIGN.get(m["obligation_type"] or "") == ind:
                rrf[i] *= 1.0 + HINT_BOOST
            if pillar_of(ind) == 7 and (m["data_type"] or "") == "non-personal":
                rrf[i] *= NONPERSONAL_DAMP

        order = np.argsort(-rrf)
        cap = CAPS[ind]
        taken = Counter()          # per economy, direct band
        gray_taken = Counter()
        floor = SETTINGS.prefilter_floor
        for i in order:
            score = float(rrf[i])
            if score <= 0.0:
                break
            m = meta[i]
            econ = m["economy"]
            if econ not in economies:
                continue
            if taken[econ] < cap:
                taken[econ] += 1
                direct_f.write(_pair(m, ind, score, "rrf"))
                cell_pairs[(econ, ind)].add(m["doc_id"])
                report["totals"]["direct"] += 1
            elif gray_taken[econ] < cap * GRAY_MULT and score >= floor:
                gray_taken[econ] += 1
                gray_f.write(_pair(m, ind, score, "rrf"))
                cell_pairs[(econ, ind)].add(m["doc_id"])
                report["totals"]["gray"] += 1
            if all(taken[e] >= cap and gray_taken[e] >= cap * GRAY_MULT
                   for e in economies):
                break
        for e in economies:
            report["cells"][f"{e}:{ind}"] = {
                "direct": taken[e], "gray": gray_taken[e]}
        print(f"[select] {ind}: direct {dict(taken)}, gray {dict(gray_taken)}", flush=True)


def _recall_gate(economies, cell_pairs) -> dict:
    """Gold arrives through the instrument loader, which normalises `indicator` to decimal text,
    so the gate works against either instrument vintage. Gold is a yardstick only: it never adds
    a candidate (decision #11).

    A gold row counts in the denominator only when the law it cites is in THIS economy's corpus
    with provisions to retrieve. Measured 2026-09-27, all three conditions were needed, and
    without them the gate reported 0.871 where the honest figure was 0.947:

    - **same economy.** The name index was global, so "Criminal Procedure Code (Act 593) 2018",
      a Malaysian row, resolved against two Lao documents. A cross-economy match can never hit,
      because the candidate set is per economy, so it only ever inflated the denominator.
    - **the cited law's tokens must be covered**, not the shorter name's. "Criminal Code" covers
      all of its own tokens inside the Malaysian title, which is how a Lao penal code came to
      stand for a Malaysian procedure code.
    - **provisions exist.** A document in doc_meta with zero corpus rows cannot be retrieved by
      anything, so counting it as a retrieval failure measures extraction.

    The rows that fall out are not silently dropped: they are reported as `unresolvable`, with
    their cited law, because each one is a scraping request.
    """
    gold_rows, hits, misses, unresolvable = 0, 0, [], []
    doc_by_name: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))
    doc_meta = json.loads((SETTINGS.index_dir / "doc_meta.json").read_text(encoding="utf-8"))
    rows_per_doc: Counter = Counter()
    with (SETTINGS.index_dir / "prefilter_corpus.jsonl").open(encoding="utf-8") as f:
        for line in f:
            rows_per_doc[json.loads(line)["doc_id"]] += 1
    for did, dm in doc_meta.items():
        econ = dm.get("economy")
        if not econ or rows_per_doc[did] == 0:
            continue
        # every name the document is known by: the original, its English translation, and the
        # original-script form. A Chinese or Lao title cannot be compared as Latin text, and its
        # English name is a translation the host words differently.
        for name in (dm.get("law_name"), dm.get("law_name_en"), dm.get("law_name_original")):
            if name:
                doc_by_name[econ][name].append(did)

    ins = load_instrument()
    for g in ins.gold():
        ind = g.get("indicator")
        econ = g.get("economy")
        raw_law = g.get("law") or ""
        laws = [x.strip() for x in re.split(r"[;\n]", raw_law) if x.strip()]
        if not (ind in INDICATORS and econ in economies and laws):
            continue
        # absence rows (score-0, no articles cited — e.g. r1-au-036 "No infrastructure
        # requirements were found") are emitted by the deterministic no-provision stage (§7.2),
        # not retrieval: exclude from the retrieval-recall denominator. EXCEPT the inverted-
        # polarity indicators 7.1 and 7.2, where score 0 means a framework EXISTS — the cited
        # framework act is retrievable evidence.
        arts = str(g.get("articles_mentioned") or "")
        no_articles = arts.strip() in ("", "[]", "None")
        if (no_articles
                and str(g.get("raw_score", "")).strip() in ("0", "0.0")
                and not ins.is_inverted(ind)):
            continue
        # resolvable = a law this gold row cites is in THIS economy's corpus, with provisions
        cand_docs: set[str] = set()
        for law in laws:
            for name, dids in doc_by_name[econ].items():
                if same_law(law, name):
                    cand_docs.update(dids)
        if not cand_docs:
            # not crawled, or crawled and unparsed: a scraping gap, not a retrieval failure
            unresolvable.append({"gold": g.get("gold_id"), "econ": econ, "ind": ind,
                                 "law": laws[0][:120]})
            continue
        gold_rows += 1
        if cand_docs & cell_pairs[(econ, ind)]:
            hits += 1
        else:
            misses.append({"gold": g.get("gold_id"), "econ": econ, "ind": ind,
                           "laws": laws[:2]})

    recall = hits / gold_rows if gold_rows else None
    return {
        "resolvable_gold_rows": gold_rows, "hit": hits,
        "recall": round(recall, 4) if recall is not None else None,
        "target": 0.95, "misses": misses,
        # every one of these is a law a host gold row cites that this economy's corpus does not
        # hold: a request for the scraping stage, not a number to tune here
        "unresolvable_gold_rows": len(unresolvable),
        "unresolvable": unresolvable,
    }


if __name__ == "__main__":
    run_select()
