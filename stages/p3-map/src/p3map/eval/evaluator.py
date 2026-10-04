"""S10 — eval vs the gold set (decision #11: allowlist OFF, organic only).

Row-level: for every resolvable gold row (its cited law exists in the corpus),
did the pipeline emit a curated row with the same (economy, indicator) and a
matching law? Reports per-indicator recall + the misses. Field-level: for
matched rows, does Discovery Tag say KNOWN (it should — these ARE baseline
rows)? Excludes the label-noise rows flagged by the instrument (decision #9), read
from each row's own `label_flag` since the second hand-off of 4 October 2026.

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

# The seven rows Round 1's review set aside, named by id until the instrument carried the call on
# the row. Kept as the record of what every published pillar 6-7 figure was computed without; a
# test holds that the rule below sets aside exactly these seven in pillars 6 and 7.
EXCLUDE_FLAGGED = {"r1-my-053", "r1-my-054", "r1-au-034", "r1-au-035",
                   "r1-my-050", "r1-my-051", "r1-sg-042"}


def excluded_by_flag(g: dict) -> str | None:
    """Why a gold row does not count as gold, or None when it does.

    suspect        its score contradicts an explicit host rule, or it sits under the wrong indicator
    round1_review  set aside by Round 1's review, suspect and advisory alike: two and five rows, the
                   seven above, so the published figures are computed over the rows they always were

    An advisory, host-marked or candidate row from the drafting review of 4 October counts as gold
    in the headline figure (the developer's decision of 4 October); `row_recall_unflagged` is the
    same measure over rows that carry no flag at all.
    """
    flag = g.get("label_flag") if isinstance(g.get("label_flag"), dict) else {}
    if flag.get("status") == "suspect":
        return "suspect"
    if flag.get("basis") == "round1_review":
        return "round1_review"
    return None


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
    set_aside: dict[str, int] = defaultdict(int)      # reason -> gold rows not counted
    in_scope: dict[str, int] = defaultdict(int)       # indicator -> gold rows this economy has for it
    counted: dict[str, int] = defaultdict(int)        # indicator -> of those, rows left as gold
    flagged_counted: dict[str, int] = defaultdict(int)  # status -> counted rows that carry a flag
    clean_rows, clean_hits = 0, 0                     # the same measure over unflagged rows only
    # Through the loader, so `indicator` is decimal text whichever instrument is vendored.
    # Reading the raw file instead lets a decimal gold set silently yield row_recall: None
    # against a legacy INDICATORS list -- a metric that reports nothing while looking like a pass.
    for g in load_instrument().gold():
        if g.get("economy") != economy or g.get("indicator") not in INDICATORS:
            continue
        in_scope[g["indicator"]] += 1
        why = excluded_by_flag(g)
        if why:
            set_aside[why] += 1
            continue
        counted[g["indicator"]] += 1
        status = (g.get("label_flag") or {}).get("status") if isinstance(g.get("label_flag"), dict) else None
        laws = [x.strip() for x in re.split(r"[;\n]", g.get("law") or "") if x.strip()]
        cited_docs = [d for law in laws for name in doc_names if same_law(law, name)
                      for d in docs_by_name[name]]
        if not cited_docs:
            continue                      # not in the corpus at all: outside the denominator
        gold_rows += 1
        if status:
            flagged_counted[status] += 1
        else:
            clean_rows += 1
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
            if not status:
                clean_hits += 1
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
        # What the flags did to the denominator, so a figure can be read against its rows.
        "gold_rows_set_aside_by_flag": dict(set_aside),
        "flagged_rows_counted_as_gold": dict(flagged_counted),
        "unflagged_gold_rows": clean_rows,
        "row_recall_unflagged": round(clean_hits / clean_rows, 4) if clean_rows else None,
        # An indicator whose every gold row for this economy was set aside has no gold left: the
        # run says nothing about it either way, which is not the same as a recall of zero.
        "indicators_with_no_gold_left": sorted(i for i, n in in_scope.items() if not counted.get(i)),
        "note": ("allowlist OFF; gold rows flagged suspect, and the seven set aside by Round 1's review, "
                 "are excluded (label_flag; decision #9/#11); advisory, host-marked and candidate rows "
                 "count, and row_recall_unflagged leaves them out"),
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
