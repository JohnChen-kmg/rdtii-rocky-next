"""S9d -- assemble the submission folder: ONE file per economy, whatever produced it.

The host reads one records file, one workbook and one audit page per economy. This run does not
naturally produce that: Timor-Leste is mapped in two arms (pillars 6 and 7 in `out/`, the other 52
indicators in `out_tl52/`), so it had two of each while every other economy had one. This module is
where the arms become one country's output.

    python -m src.p3map.output.package --out submission \\
        --arm AU=<run>/out --arm CN=<run>/out --arm LA=<run>/out --arm MY=<run>/out \\
        --arm SG=<run>/out --arm TL=<run>/out --arm TL=<run>/out_tl52 \\
        --template "OUTPUT_TEMPLATE_FINAL_ROUND.xlsx"

Run the workbook and audit-page exports with `--extra-dirs` FIRST, so the per-country files this
copies already cover every arm. `build()` checks that rather than trusting it: if a workbook is
missing an indicator that one of its arms fired on, the arms were not merged and it says so instead
of shipping half a country.

What the folder holds, per economy:

    records_<E>.csv     the filed rows, 14 columns in the host's order
    records_<E>.json    the same rows in the host's per-law shape
    RDTII_P3_results_<E>.xlsx   the review workbook -- every fire, kept and rejected, plus QA sheets
    audit/index_<E>.html        the audit page, quote beside its machine English
    reports/                    economy scores, eval, submission and map reports

plus `OUTPUT_DATA_FILLED.xlsx`, the host's own template with the curated 101 rows (see template.py),
and a README stating what each file is and what is known to be wrong with it.
"""
from __future__ import annotations

import argparse
import csv
import json
import shutil
from collections import Counter
from pathlib import Path

CSV_COLUMNS = ["Economy", "Law Name", "Law Number / Ref", "Last Amended", "Indicator ID",
               "Article / Section", "Discovery Tag", "Location Reference", "Verbatim Snippet",
               "Mapping Rationale", "Source URL", "Confidence", "Notes", "Language of Source"]
REPORTS = ("rollup/economy_scores_{e}.json", "eval/eval_report_{e}.json",
           "submission/submission_report_{e}.json", "map/map_report_{e}.json")


def merge_csv(paths: list[Path]) -> list[dict]:
    """Concatenate the arms' filed rows.

    No dedupe, deliberately. The arms cover disjoint indicator sets -- verified on this run: 9
    indicators in one and 52 in the other, zero overlap, and zero collisions on
    (indicator, law, section). A dedupe here would silently drop a real row the day the arms DO
    overlap, and `build()` reports the row count so a duplicate would show as an unexpected total.
    """
    rows: list[dict] = []
    for p in paths:
        with p.open(encoding="utf-8-sig", newline="") as f:
            r = csv.DictReader(f)
            missing = [c for c in CSV_COLUMNS if c not in (r.fieldnames or [])]
            if missing:
                raise ValueError(f"{p} is missing host columns {missing}")
            rows += list(r)
    return rows


def merge_json(paths: list[Path]) -> dict:
    """Merge the per-law JSON. A law cited in both arms becomes one entry with both arms'
    provisions, because the host's shape is one entry per law, not per pass."""
    out: dict | None = None
    laws: dict[tuple, dict] = {}
    for p in paths:
        d = json.loads(p.read_text(encoding="utf-8"))
        if out is None:
            out = {k: v for k, v in d.items() if k != "laws"}
        for law in d.get("laws") or []:
            key = (law.get("law_name") or "", law.get("law_number") or "",
                   law.get("source_url") or "")
            if key in laws:
                laws[key].setdefault("provisions", []).extend(law.get("provisions") or [])
            else:
                laws[key] = {**law, "provisions": list(law.get("provisions") or [])}
    out = out or {}
    out["laws"] = list(laws.values())
    return out


def _workbook_covers_every_arm(economy: str, arms: list[Path], workbook: Path) -> list[str]:
    """Indicators an arm fired on that the workbook does not show -> the arms were not merged."""
    from openpyxl import load_workbook
    fired: set[str] = set()
    for arm in arms:
        vp = arm / "map" / f"verdicts_{economy}.jsonl"
        if not vp.exists():
            continue
        for line in vp.open(encoding="utf-8"):
            r = json.loads(line)
            if "error" in r:
                continue
            for v in r.get("verdicts") or []:
                if v.get("applies"):
                    fired.add(str(v["indicator"]))
    wb = load_workbook(workbook, read_only=True)
    shown: set[str] = set()
    ws = wb["All fires"]
    rows = list(ws.iter_rows(min_row=2, values_only=True))
    if rows:
        hdr = [str(c) if c is not None else "" for c in rows[0]]
        i = hdr.index("Indicator")
        shown = {str(r[i]) for r in rows[1:] if r[i] not in (None, "")}
    wb.close()
    return sorted(fired - shown)


def build(arms: dict[str, list[Path]], out: Path, template: Path | None = None) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    (out / "audit").mkdir(exist_ok=True)
    (out / "reports").mkdir(exist_ok=True)

    report: dict = {"economies": {}, "warnings": []}
    csv_paths: list[Path] = []
    for econ, dirs in sorted(arms.items()):
        primary = dirs[0]
        recs = [d / "submission" / f"records_{econ}.csv" for d in dirs]
        rows = merge_csv([p for p in recs if p.exists()])
        dest = out / f"records_{econ}.csv"
        # with the byte-order mark, as the run's own CSV has it: without one, Excel on a Chinese, Lao or
        # Thai Windows reads the file in the local code page and shows every non-English snippet as noise
        with dest.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction="ignore")
            w.writeheader()
            w.writerows(rows)
        csv_paths.append(dest)

        js = [d / "submission" / f"records_{econ}.json" for d in dirs]
        js = [p for p in js if p.exists()]
        if js:
            (out / f"records_{econ}.json").write_text(
                json.dumps(merge_json(js), indent=1, ensure_ascii=False), encoding="utf-8")

        wb_src = primary / "results" / f"RDTII_P3_results_{econ}.xlsx"
        if wb_src.exists():
            shutil.copy2(wb_src, out / wb_src.name)
            if len(dirs) > 1:
                missing = _workbook_covers_every_arm(econ, dirs, wb_src)
                if missing:
                    report["warnings"].append(
                        f"{econ}: the workbook does not show indicators {missing}, which an arm "
                        f"fired on. Re-run excel_export with --extra-dirs before packaging.")
        audit_src = primary / "audit" / f"index_{econ}.html"
        if audit_src.exists():
            shutil.copy2(audit_src, out / "audit" / audit_src.name)
        for pat in REPORTS:
            for d in dirs:
                src = d / pat.format(e=econ)
                if src.exists():
                    tag = "" if d is primary else f"_{d.name}"
                    shutil.copy2(src, out / "reports" / f"{src.stem}{tag}{src.suffix}")

        inds = {r["Indicator ID"] for r in rows}
        report["economies"][econ] = {
            "arms": [str(d) for d in dirs],
            "rows": len(rows),
            "indicators": len(inds),
            "scored": sum(1 for r in rows
                          if not (r.get("Verbatim Snippet") or "").startswith("No provision")),
            "languages": dict(sorted(Counter(r.get("Language of Source") or "" for r in rows).items())),
        }

    if template:
        from src.p3map.output.template import fill, verify_filled
        filled = out / "OUTPUT_DATA_FILLED.xlsx"
        report["output_data"] = fill(Path(template), filled, csv_paths)
        report["output_data_verified"] = verify_filled(filled)
    report["total_rows"] = sum(v["rows"] for v in report["economies"].values())
    (out / "package_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="S9d — assemble the submission folder")
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--arm", action="append", required=True, metavar="ECON=DIR",
                    help="repeat per arm; the FIRST for an economy is its primary directory")
    ap.add_argument("--template", type=Path, default=None)
    a = ap.parse_args()
    arms: dict[str, list[Path]] = {}
    for spec in a.arm:
        econ, _, d = spec.partition("=")
        arms.setdefault(econ.strip(), []).append(Path(d.strip()))
    rep = build(arms, a.out, a.template)
    print(json.dumps(rep, indent=2, ensure_ascii=False))
    for w in rep["warnings"]:
        print(f"WARNING: {w}")
