"""S9c -- fill the host's OUTPUT_TEMPLATE_FINAL_ROUND.xlsx from the emitted records.

The Output Data sheet is the deliverable C1a, C1b and C1c are read from, and it holds **101 rows**
(9 to 109). This run produced 318, of which 263 are scored findings. So the binding constraint is
selection, not retrieval, and this module is where the selection rule lives -- written down and
executable rather than described in a document and done by hand.

    python -m src.p3map.output.template \\
        --template "OUTPUT_TEMPLATE_FINAL_ROUND.xlsx" --out submission/OUTPUT_DATA_FILLED.xlsx \\
        --records <run>/out/submission/records_AU.csv ... <run>/out_tl52/submission/records_TL.csv

Five things about the host's template that this module exists to get right, each read out of the
file rather than assumed:

1. **Column E must be TEXT.** The Instructions sheet: "entered as a number, 12.10 collapses to 12.1
   and 4.01 to 4.1, and the two are different indicators." We file 61 distinct indicator IDs
   including `4.01`, `12.01` AND `4.1` -- so a numeric write merges two different indicators and
   silently loses a row. Every ID is written as a string into a cell forced to text format, and
   `verify_filled()` reads the workbook back to prove it.

2. **Column O is a formula and the Coverage Matrix reads it.**
   `=IF($E9="","",IFERROR(INT($E9),...))` derives the pillar from the ID; the Coverage Matrix counts
   `COUNTIFS('Output Data'!$O$9:$O$109, <pillar>, 'Output Data'!$A$9:$A$109, <economy>)`. Two
   consequences: never write to column O, and **never delete rows**, because openpyxl does not
   rewrite formulas when rows shift and the whole O9:O109 geometry would move out from under both
   the formulas and the Coverage Matrix's fixed ranges.

   So the example block at rows 6-8 is **cleared, not deleted**. The host says "Remove rows 7 and 8
   ... they are illustration only"; clearing the cells removes the illustration, and leaving the row
   count alone keeps the sheet the host's validator expects. Deleting would satisfy the wording and
   break the sheet C1a is read from -- the wrong direction to be wrong in.

3. **The Economy string must match the Coverage Matrix's own label**, because that is what COUNTIFS
   compares against. The label is `Lao PDR`, while the Instructions say "official UN country name,
   e.g. Lao People's Democratic Republic" -- following that advice literally would count zero
   provisions for Lao PDR. Checked against the sheet, not trusted.

4. **Only scored rows are filed.** Columns I (Verbatim Snippet) and K (Source URL) are REQUIRED, and
   a no-provision row has neither by construction. With 263 findings for 101 slots the tension does
   not need resolving: file findings.

5. Rows 7 and 8 of the *example* data use decimal IDs and the Instructions say "Not 'P6-I1'" --
   though cell E5's own help text still reads `e.g. "P6-I1", "P6_I2"`, stale from Round 1. Decimal
   is correct; the header help is wrong.
"""
from __future__ import annotations

import argparse
import csv
import shutil
from collections import Counter, defaultdict
from pathlib import Path

SHEET = "Output Data"
FIRST_ROW = 9
LAST_ROW = 109
SLOTS = LAST_ROW - FIRST_ROW + 1          # 101
EXAMPLE_ROWS = (6, 7, 8)                  # the "▸ EXAMPLE ROWS" block
MANDATORY_PILLARS = ("6", "7")

# host column order; column O is the host's formula and is never written
COLUMNS = ["Economy", "Law Name", "Law Number / Ref", "Last Amended", "Indicator ID",
           "Article / Section", "Discovery Tag", "Location Reference", "Verbatim Snippet",
           "Mapping Rationale", "Source URL", "Confidence", "Notes", "Language of Source"]
INDICATOR_COL = COLUMNS.index("Indicator ID") + 1        # 1-based -> column E


def _pillar(indicator: str) -> str:
    return indicator.split(".")[0]


def row_penalty(r: dict) -> tuple:
    """Lower is better. Only signals that survive into the CSV are used, because that is what the
    filed artefact carries -- a rule that needs the verify/ files cannot be checked from the
    submission alone.

    The citation caveat dominates: a row whose Law Name may name the wrong act is still good
    evidence, but the Instructions warn that "a real act cited to the wrong section scores zero",
    and a marker who checks one and finds a combatants' statute where a credit registry should be
    will not check the rest charitably. `act_unknown` ranks below `later_act` because it cannot be
    resolved by looking, only by guessing.
    """
    notes = r.get("Notes") or ""
    if "Which act this provision belongs to was not recorded" in notes:
        citation = 3
    elif "most likely belongs to a different act" in notes:
        citation = 2
    elif "CITATION CAVEAT" in notes:          # first_act: probably fine, still unconfirmed
        citation = 1
    else:
        citation = 0
    try:
        conf = float(r.get("Confidence") or 0)
    except ValueError:
        conf = 0.0
    return (citation, "verification pending" in notes, -conf, r.get("Law Name") or "")


def curate(rows: list[dict], slots: int = SLOTS) -> tuple[list[dict], dict]:
    """Choose which findings are filed, breadth first and then depth.

    Pass 1 -- one row per (economy, indicator) cell, best by `row_penalty`. Measured on this run
    that is 51 cells for 101 slots, so every cell we can evidence is represented and no economy or
    indicator is squeezed out by a deep one. Cells in the two mandatory pillars are taken first, so
    if the cell count ever exceeds the slots it is pillars 6 and 7 that survive.

    Pass 2 -- the remaining slots go to the best rows left, capped per cell so that one heavily
    evidenced indicator cannot spend them all. The cap rises until the slots are full, which fills
    them without needing a magic number.
    """
    scored = [r for r in rows if not (r.get("Verbatim Snippet") or "").startswith("No provision")]
    by_cell: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for r in scored:
        by_cell[(r["Economy"], r["Indicator ID"])].append(r)
    for v in by_cell.values():
        v.sort(key=row_penalty)

    def cell_key(cell):
        econ, ind = cell
        return (0 if _pillar(ind) in MANDATORY_PILLARS else 1, row_penalty(by_cell[cell][0]),
                econ, ind)

    chosen: list[dict] = []
    for cell in sorted(by_cell, key=cell_key):
        if len(chosen) >= slots:
            break
        chosen.append(by_cell[cell][0])

    taken = {id(r) for r in chosen}
    cap = 2
    while len(chosen) < slots:
        added = 0
        for cell in sorted(by_cell, key=cell_key):
            if len(chosen) >= slots:
                break
            for r in by_cell[cell][:cap]:
                if id(r) not in taken:
                    chosen.append(r)
                    taken.add(id(r))
                    added += 1
                    break
        if not added:
            break                      # every row already chosen
        cap += 1

    chosen.sort(key=lambda r: (r["Economy"], _pillar(r["Indicator ID"]).zfill(3),
                               r["Indicator ID"], r.get("Article / Section") or ""))
    report = {
        "available_scored_rows": len(scored),
        "cells_evidenced": len(by_cell),
        "slots": slots,
        "filed": len(chosen),
        "by_economy": dict(sorted(Counter(r["Economy"] for r in chosen).items())),
        "by_pillar": dict(sorted(Counter(_pillar(r["Indicator ID"]) for r in chosen).items(),
                                 key=lambda kv: int(kv[0]))),
        "by_discovery_tag": dict(sorted(Counter(r.get("Discovery Tag") or "(blank)"
                                                for r in chosen).items())),
        "with_citation_caveat": sum(1 for r in chosen if "CITATION CAVEAT" in (r.get("Notes") or "")),
        "languages": dict(sorted(Counter(r.get("Language of Source") or "" for r in chosen).items())),
    }
    return chosen, report


def coverage_matrix_labels(wb) -> set[str]:      # noqa: ANN001
    """The economy strings COUNTIFS compares against, read from the sheet itself."""
    cm = wb["Coverage Matrix"]
    out = set()
    for r in range(4, cm.max_row + 1):
        v = cm.cell(row=r, column=1).value
        if v and not str(v).startswith("=") and ":" not in str(v) and len(str(v)) < 40:
            out.add(str(v))
    return out


def fill(template: Path, out: Path, records: list[Path], slots: int = SLOTS) -> dict:
    from openpyxl import load_workbook

    rows: list[dict] = []
    for p in records:
        with p.open(encoding="utf-8-sig", newline="") as f:
            rows += list(csv.DictReader(f))
    chosen, report = curate(rows, slots)

    out.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(template, out)                 # keep every other sheet exactly as the host wrote it
    wb = load_workbook(out)
    ws = wb[SHEET]

    labels = coverage_matrix_labels(wb)
    unknown = sorted({r["Economy"] for r in chosen} - labels)
    if unknown:
        raise ValueError(
            f"these Economy strings are not Coverage Matrix labels, so COUNTIFS would count zero "
            f"for them: {unknown}. The sheet's labels include e.g. 'Lao PDR', not the longer UN "
            f"name the Instructions suggest.")

    # Clear the example block. NOT delete_rows -- see the module docstring.
    for r in EXAMPLE_ROWS:
        for c in range(1, ws.max_column + 1):
            if ws.cell(row=r, column=c).value is not None and c != 15:
                ws.cell(row=r, column=c).value = None

    for i, rec in enumerate(chosen):
        row = FIRST_ROW + i
        for j, name in enumerate(COLUMNS, start=1):
            cell = ws.cell(row=row, column=j)
            val = rec.get(name) or ""
            if j == INDICATOR_COL:
                cell.number_format = "@"        # text, so 4.01 does not become 4.1
                cell.value = str(val)
            elif name == "Confidence":
                try:
                    cell.value = float(val) if val != "" else None
                except ValueError:
                    cell.value = None
            else:
                cell.value = str(val) if val != "" else None
    # blank any slot a previous fill used and this one does not
    for row in range(FIRST_ROW + len(chosen), LAST_ROW + 1):
        for j in range(1, len(COLUMNS) + 1):
            ws.cell(row=row, column=j).value = None

    wb.save(out)
    report["template"] = str(template)
    report["out"] = str(out)
    return report


def verify_filled(path: Path) -> dict:
    """Read the saved workbook back. The text-format claim is only worth making if checked."""
    from openpyxl import load_workbook
    wb = load_workbook(path)
    ws = wb[SHEET]
    ids, econs, bad_format, numeric = [], [], [], []
    for row in range(FIRST_ROW, LAST_ROW + 1):
        e = ws.cell(row=row, column=1).value
        ind = ws.cell(row=row, column=INDICATOR_COL)
        if e is None and ind.value is None:
            continue
        econs.append(e)
        ids.append(ind.value)
        if not isinstance(ind.value, str):
            numeric.append((row, ind.value))
        if ind.number_format != "@":
            bad_format.append(row)
    formulas_intact = sum(1 for r in range(FIRST_ROW, LAST_ROW + 1)
                          if str(ws.cell(row=r, column=15).value or "").startswith("=IF("))
    examples_cleared = all(ws.cell(row=r, column=1).value is None for r in EXAMPLE_ROWS)
    return {"rows": len(ids), "distinct_indicators": len(set(ids)),
            "indicator_ids_not_text": numeric, "cells_not_text_formatted": bad_format,
            "column_O_formulas_intact": formulas_intact,
            "example_block_cleared": examples_cleared,
            "economies": dict(sorted(Counter(econs).items()))}


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="S9c — fill the host's Output Data sheet")
    ap.add_argument("--template", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--records", required=True, nargs="+", type=Path)
    ap.add_argument("--slots", type=int, default=SLOTS)
    a = ap.parse_args()
    import json
    rep = fill(a.template, a.out, a.records, a.slots)
    print(json.dumps(rep, indent=2, ensure_ascii=False))
    print(json.dumps(verify_filled(a.out), indent=2, ensure_ascii=False))
