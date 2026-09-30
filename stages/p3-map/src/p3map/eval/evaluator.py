"""S10 — eval vs the gold set (decision #11: allowlist OFF, organic only).

Row-level: for every resolvable gold row (its cited law exists in the corpus),
did the pipeline emit a curated row with the same (economy, indicator) and a
matching law? Reports per-indicator recall + the misses. Field-level: for
matched rows, does Discovery Tag say KNOWN (it should — these ARE baseline
rows)? Excludes the label-noise rows flagged by the instrument (decision #9).

Run per economy after S9. Output: out/eval/eval_report_<ECON>.json.
"""
from __future__ import annotations

import csv
import json
import re
from collections import defaultdict

from config.instrument import from_artifact, load as load_instrument
from config.lawnames import same_law
from config.settings import INDICATORS, SETTINGS

EXCLUDE_FLAGGED = {"r1-my-053", "r1-my-054", "r1-au-034", "r1-au-035",
                   "r1-my-050", "r1-my-051", "r1-sg-042"}


def run_eval(economy: str) -> dict:
    # name -> the documents it names, with the one fact that decides whether a gold row could
    # have been mapped at all: does the document have provisions in the corpus. A cited law that
    # exists only as a parse_failed shell is a corpus gap, not a mapping failure, and counting it
    # as a miss understates recall while counting it as resolvable overstates the denominator.
    docs_by_name: dict[str, list[dict]] = defaultdict(list)
    doc_meta = json.loads((SETTINGS.index_dir / "doc_meta.json").read_text(encoding="utf-8"))
    for did, dm in doc_meta.items():
        if dm.get("economy") != economy:
            continue
        # law_name_en as well as law_name: a gold row cites the English name, and a Chinese or
        # Lao law_name scores 0 against it on token overlap
        for name in (dm.get("law_name"), dm.get("law_name_en"), dm.get("law_name_original")):
            if name:
                docs_by_name[name].append({"doc_id": did, **dm})
    doc_names = set(docs_by_name)

    with (SETTINGS.out_dir / "submission" / f"records_{economy}.csv").open(
            encoding="utf-8-sig") as f:
        ours = list(csv.DictReader(f))
    ours_by_ind: dict[str, list[dict]] = defaultdict(list)
    for r in ours:
        # a CSV emitted before the decimal migration says "P6-I1"
        ours_by_ind[from_artifact(r["Indicator ID"])].append(r)

    gold_rows, hits, misses, tag_ok = 0, 0, [], 0
    unparsed, unparsed_ids = 0, []
    # Through the loader, so `indicator` is decimal text whichever instrument is vendored.
    # Reading the raw file instead lets a decimal gold set silently yield row_recall: None
    # against a legacy INDICATORS list -- a metric that reports nothing while looking like a pass.
    for g in load_instrument().gold():
        if g.get("economy") != economy or g.get("indicator") not in INDICATORS:
            continue
        if g.get("gold_id") in EXCLUDE_FLAGGED:
            continue
        laws = [x.strip() for x in re.split(r"[;\n]", g.get("law") or "") if x.strip()]
        cited_docs = [d for law in laws for name in doc_names if same_law(law, name)
                      for d in docs_by_name[name]]
        if not cited_docs:
            continue                      # not in the corpus at all: outside the denominator
        gold_rows += 1
        if not any((d.get("provision_count") or 0) > 0 for d in cited_docs):
            # the document is in the corpus but has no provisions: upstream extraction failed,
            # so no retrieval or mapping decision could have reached this row
            unparsed += 1
            if len(unparsed_ids) < 12:
                unparsed_ids.append(g["gold_id"])
        matched = None
        for r in ours_by_ind.get(g["indicator"], []):
            if any(same_law(law, r["Law Name"]) for law in laws):
                matched = r
                break
        if matched:
            hits += 1
            if matched["Discovery Tag"] == "KNOWN":
                tag_ok += 1
        else:
            misses.append({"gold": g["gold_id"], "ind": g["indicator"],
                           "law": laws[:1]})

    parsed_rows = gold_rows - unparsed
    report = {
        "economy": economy,
        "resolvable_gold_rows": gold_rows,
        "row_recall": round(hits / gold_rows, 4) if gold_rows else None,
        # The honest denominator. A gold row whose cited document has no provisions in the corpus
        # could not have been mapped by anything, so recall over it measures extraction, not
        # mapping. Round 1 stated this for Malaysia as a hard-coded paragraph naming four gold
        # ids and a recall of 16/18 — true of that run and false of every other, and it would
        # have shipped in an evidence file. It is now measured, for every economy.
        "cited_but_unparsed_sources": unparsed,
        "cited_but_unparsed_examples": unparsed_ids,
        "gold_rows_with_parsed_sources": parsed_rows,
        "row_recall_on_parsed_sources": (round(hits / parsed_rows, 4)
                                         if parsed_rows > 0 else None),
        "known_tag_accuracy_on_hits": round(tag_ok / hits, 4) if hits else None,
        "misses": misses,
        "csv_rows": len(ours),
        "note": "allowlist OFF; label-noise gold rows excluded (decision #9/#11)",
        "law_match": ("config/lawnames.py: the CITED law's tokens must be covered by the "
                      "candidate name (not the other way round), and an original-script title "
                      "matches by containment, because an English name here is a translation"),
    }
    if unparsed:
        report["resolvability_note"] = (
            f"{unparsed} of {gold_rows} resolvable gold rows cite a document that is in the "
            f"corpus with zero provisions (upstream extraction failed), so no mapping decision "
            f"could reach them: a corpus gap, not a mapping failure. Recall over the "
            f"{parsed_rows} rows whose sources parsed is "
            f"{report['row_recall_on_parsed_sources']}.")
    out_dir = SETTINGS.out_dir / "eval"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"eval_report_{economy}.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8")
    print(f"[eval:{economy}] {json.dumps(report, indent=1)}")
    return report


if __name__ == "__main__":
    import sys
    run_eval(sys.argv[1] if len(sys.argv) > 1 else "SG")
