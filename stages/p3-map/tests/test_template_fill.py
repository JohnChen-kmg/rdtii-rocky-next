"""Filling the host's Output Data sheet — the deliverable C1a, C1b and C1c are read from.

101 rows for 318 produced, so this is where the selection rule lives. These tests pin the parts that
fail silently: an indicator ID written as a number, a row deleted out from under the host's formula,
and an Economy string the Coverage Matrix does not recognise.
"""
from __future__ import annotations

import csv

import pytest

from src.p3map.output.template import (COLUMNS, EXAMPLE_ROWS, FIRST_ROW, LAST_ROW, SLOTS,
                                       curate, fill, row_penalty, verify_filled)

TEMPLATE_HINT = ("the host's OUTPUT_TEMPLATE_FINAL_ROUND.xlsx is not in the repo (it is a rules "
                 "document); these tests build a stand-in with the same geometry")


def _row(econ, ind, conf=0.9, notes="", law="An Act 2020", snip="text", tag="NEW", lang="English"):
    return {"Economy": econ, "Law Name": law, "Law Number / Ref": "1/2020", "Last Amended": "2024",
            "Indicator ID": ind, "Article / Section": "s. 1", "Discovery Tag": tag,
            "Location Reference": "p.1", "Verbatim Snippet": snip, "Mapping Rationale": "because",
            "Source URL": "https://example.gov/a.pdf", "Confidence": str(conf),
            "Notes": notes, "Language of Source": lang}


@pytest.fixture
def stand_in(tmp_path):
    """A workbook with the host's geometry: Output Data with an example block at 6-8, column O
    formulas at 9-109, and a Coverage Matrix whose column A holds the economy labels."""
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Output Data"
    for j, name in enumerate(COLUMNS, start=1):
        ws.cell(row=4, column=j, value=name)
    ws.cell(row=6, column=1, value="▸ EXAMPLE ROWS (not real submissions — delete)")
    ws.cell(row=7, column=1, value="Singapore")
    ws.cell(row=7, column=5, value="6.4")
    ws.cell(row=8, column=1, value="Singapore")
    for r in range(FIRST_ROW, LAST_ROW + 1):
        ws.cell(row=r, column=15,
                value=f'=IF($E{r}="","",IFERROR(INT($E{r}),IFERROR(VALUE(LEFT($E{r},'
                      f'FIND(".",$E{r})-1)),"?")))')
    cm = wb.create_sheet("Coverage Matrix")
    for i, label in enumerate(["Australia", "China", "Lao PDR", "Malaysia", "Singapore",
                               "Timor-Leste"], start=4):
        cm.cell(row=i, column=1, value=label)
    p = tmp_path / "template.xlsx"
    wb.save(p)
    return p


def _csv(tmp_path, name, rows):
    p = tmp_path / name
    with p.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(rows)
    return p


# --------------------------------------------------------------------------- curation


def test_no_provision_rows_are_never_filed():
    """Columns I and K are REQUIRED and a no-provision row has neither. With 2.6x the findings we
    need, the tension does not have to be resolved in the host's favour or ours."""
    rows = [_row("China", "6.1"), _row("China", "6.2", snip="No provision found")]
    chosen, rep = curate(rows, slots=SLOTS)
    assert [r["Indicator ID"] for r in chosen] == ["6.1"]
    assert rep["available_scored_rows"] == 1


def test_breadth_before_depth():
    """One row per (economy, indicator) cell first. A deeply evidenced indicator must not crowd out
    an economy or indicator that has only one row."""
    rows = [_row("China", "6.1", conf=0.9 - i / 100) for i in range(10)]
    rows += [_row("Lao PDR", "7.3", conf=0.5)]
    chosen, _ = curate(rows, slots=2)
    assert {(r["Economy"], r["Indicator ID"]) for r in chosen} == {("China", "6.1"),
                                                                   ("Lao PDR", "7.3")}


def test_mandatory_pillars_win_when_slots_run_short():
    """Pillars 6 and 7 are mandatory; the rest are credit. If cells ever exceed slots, 6 and 7 go
    in first."""
    rows = [_row("China", "2.1"), _row("China", "12.9"), _row("China", "7.3"), _row("China", "6.1")]
    chosen, _ = curate(rows, slots=2)
    assert sorted(r["Indicator ID"] for r in chosen) == ["6.1", "7.3"]


def test_a_caveated_citation_loses_to_a_clean_one_in_the_same_cell():
    """A row whose Law Name may name the wrong act is still evidence, but the host warns that "a
    real act cited to the wrong section scores zero" — so where there is a choice, take the clean
    one."""
    dirty = _row("Timor-Leste", "7.3", conf=0.99,
                 notes="CITATION CAVEAT: ... most likely belongs to a different act ...")
    clean = _row("Timor-Leste", "7.3", conf=0.70)
    chosen, _ = curate([dirty, clean], slots=1)
    assert chosen[0]["Confidence"] == "0.7", "confidence does not outrank a doubtful citation"


def test_an_unknown_act_ranks_below_a_merely_unconfirmed_one():
    unknown = _row("Timor-Leste", "7.3",
                   notes="CITATION CAVEAT: Which act this provision belongs to was not recorded")
    later = _row("Timor-Leste", "7.3",
                 notes="CITATION CAVEAT: ... most likely belongs to a different act ...")
    first = _row("Timor-Leste", "7.3", notes="CITATION CAVEAT: ... probably right ...")
    assert row_penalty(first) < row_penalty(later) < row_penalty(unknown)


def test_the_slots_are_filled_when_there_is_material_for_them():
    rows = [_row("China", f"6.{i % 4 + 1}", conf=0.9 - i / 1000) for i in range(40)]
    chosen, rep = curate(rows, slots=10)
    assert rep["filed"] == 10 == len(chosen)


def test_never_more_than_the_slots():
    rows = [_row("China", f"6.{i % 4 + 1}") for i in range(500)]
    chosen, _ = curate(rows, slots=SLOTS)
    assert len(chosen) <= SLOTS


def test_no_row_is_filed_twice():
    rows = [_row("China", "6.1", conf=0.9 - i / 100) for i in range(30)]
    chosen, _ = curate(rows, slots=20)
    assert len({id(r) for r in chosen}) == len(chosen)


# --------------------------------------------------------------------------- the workbook


def test_indicator_ids_are_written_as_text(stand_in, tmp_path):
    """The Instructions: "entered as a number, 12.10 collapses to 12.1 and 4.01 to 4.1, and the two
    are different indicators." We file 4.01, 12.01 AND 4.1, so this is not hypothetical."""
    recs = _csv(tmp_path, "records_TL.csv",
                [_row("Timor-Leste", "4.01"), _row("Timor-Leste", "4.1"),
                 _row("Timor-Leste", "12.01"), _row("Timor-Leste", "12.4.4")])
    out = tmp_path / "filled.xlsx"
    fill(stand_in, out, [recs])
    v = verify_filled(out)
    assert v["indicator_ids_not_text"] == [], "a numeric ID merges two different indicators"
    assert v["cells_not_text_formatted"] == []
    from openpyxl import load_workbook
    ids = [load_workbook(out)["Output Data"].cell(row=r, column=5).value
           for r in range(FIRST_ROW, FIRST_ROW + 4)]
    assert set(ids) == {"4.01", "4.1", "12.01", "12.4.4"}, "every form survives intact"


def test_the_column_O_formulas_survive(stand_in, tmp_path):
    """The Coverage Matrix reads O9:O109 with fixed ranges, and openpyxl does not rewrite formulas
    when rows move — so the example block is CLEARED, never deleted."""
    recs = _csv(tmp_path, "records_CN.csv", [_row("China", "6.1")])
    out = tmp_path / "filled.xlsx"
    fill(stand_in, out, [recs])
    v = verify_filled(out)
    assert v["column_O_formulas_intact"] == LAST_ROW - FIRST_ROW + 1
    assert v["example_block_cleared"] is True


def test_the_example_rows_are_cleared_but_the_rows_still_exist(stand_in, tmp_path):
    from openpyxl import load_workbook
    recs = _csv(tmp_path, "records_CN.csv", [_row("China", "6.1")])
    out = tmp_path / "filled.xlsx"
    fill(stand_in, out, [recs])
    ws = load_workbook(out)["Output Data"]
    for r in EXAMPLE_ROWS:
        assert ws.cell(row=r, column=1).value is None
    assert ws.cell(row=4, column=1).value == "Economy", "the header did not shift"
    assert str(ws.cell(row=FIRST_ROW, column=15).value).startswith("=IF($E9")


def test_an_economy_the_coverage_matrix_does_not_know_is_refused(stand_in, tmp_path):
    """COUNTIFS compares the Economy string against the Coverage Matrix's own label. The sheet says
    'Lao PDR'; the Instructions suggest "Lao People's Democratic Republic", which would count zero."""
    recs = _csv(tmp_path, "records_LA.csv",
                [_row("Lao People's Democratic Republic", "6.1")])
    with pytest.raises(ValueError, match="Coverage Matrix labels"):
        fill(stand_in, tmp_path / "filled.xlsx", [recs])


def test_unused_slots_are_left_empty(stand_in, tmp_path):
    from openpyxl import load_workbook
    recs = _csv(tmp_path, "records_CN.csv", [_row("China", "6.1")])
    out = tmp_path / "filled.xlsx"
    fill(stand_in, out, [recs])
    ws = load_workbook(out)["Output Data"]
    assert ws.cell(row=FIRST_ROW + 1, column=1).value is None
    assert ws.cell(row=LAST_ROW, column=1).value is None


def test_the_template_itself_is_not_modified(stand_in, tmp_path):
    before = stand_in.read_bytes()
    recs = _csv(tmp_path, "records_CN.csv", [_row("China", "6.1")])
    fill(stand_in, tmp_path / "filled.xlsx", [recs])
    assert stand_in.read_bytes() == before, "the host's rules document must be left alone"
