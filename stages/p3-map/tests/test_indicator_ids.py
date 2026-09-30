"""Tests for config.indicator_ids (finale decision F1: decimal-text indicator IDs).

Run from stages/p3-map:
    python -m pytest tests/test_indicator_ids.py -q
"""
from __future__ import annotations

import filecmp
from pathlib import Path

import pytest

from config.indicator_ids import (
    BadIndicatorId, LEGACY_TO_DECIMAL, is_indicator_id, legacy_of, normalize,
    pillar_of, sort_key,
)

# The finale indicator list, in the host's own order (OUTPUT_TEMPLATE_FINAL_ROUND.xlsx,
# sheet 'Indicator Reference'). 6.5 is included here because the host lists it; the
# instrument keeps it out of scope. 62 entries.
HOST_ORDER = [
    "1.4",
    "2.1", "2.2", "2.3",
    "3.1", "3.2", "3.3", "3.4", "3.5",
    "4.01", "4.2", "4.3", "4.5", "4.6", "4.9", "4.1",
    "5.1", "5.2", "5.3", "5.4", "5.5", "5.7",
    "6.1", "6.2", "6.3", "6.4", "6.5",
    "7.1", "7.2", "7.3", "7.4", "7.5",
    "8.1", "8.2", "8.3", "8.4",
    "9.1", "9.3", "9.4",
    "10.1", "10.2", "10.3", "10.4",
    "11.1", "11.2", "11.3", "11.4",
    "12.01", "12.2", "12.3",
    "12.4.1", "12.4.2", "12.4.3", "12.4.4", "12.4.5", "12.4.6", "12.4.7",
    "12.5", "12.6", "12.7", "12.8", "12.9",
]


def excel_pillar_auto(e: str):
    """Emulates the host template's column-O formula:
    =IF(E="","",IFERROR(INT(E),IFERROR(VALUE(LEFT(E,FIND(".",E)-1)),"?")))"""
    if e == "":
        return ""
    try:
        return int(float(e))          # INT(E): Excel coerces numeric text
    except ValueError:
        return int(e[: e.find(".")])  # three-level IDs fall through to LEFT(...)


def test_host_order_has_62_unique_ids():
    assert len(HOST_ORDER) == 62
    assert len(set(HOST_ORDER)) == 62


@pytest.mark.parametrize("raw,expected", [
    ("P6-I1", "6.1"), ("P7-I5", "7.5"), ("6.1", "6.1"), (" 12.4.1 ", "12.4.1"),
    (6.1, "6.1"), (7.3000000001, "7.3"), ("4.01", "4.01"), ("12.01", "12.01"),
])
def test_normalize(raw, expected):
    assert normalize(raw) == expected


@pytest.mark.parametrize("raw", ["", "6", "P6", "6.1.2.3", "abc", None, True, "6-1"])
def test_normalize_rejects(raw):
    with pytest.raises(BadIndicatorId):
        normalize(raw)
    assert not is_indicator_id(raw)


def test_four_point_oh_one_is_not_four_point_one():
    # The hazard the whole module exists for.
    assert normalize("4.01") != normalize("4.1")
    assert float("4.01") != float("4.1")  # true, but never rely on it: 4.10 would collapse
    assert normalize(4.01) == "4.01"


@pytest.mark.parametrize("iid,pillar", [
    ("6.1", 6), ("12.4.1", 12), ("4.01", 4), ("4.1", 4), ("P7-I3", 7), ("1.4", 1),
])
def test_pillar_of(iid, pillar):
    assert pillar_of(iid) == pillar


def test_pillar_of_matches_host_formula_for_every_id():
    for iid in HOST_ORDER:
        assert pillar_of(iid) == excel_pillar_auto(iid), iid


def test_legacy_round_trip_for_the_nine():
    for legacy, decimal in LEGACY_TO_DECIMAL.items():
        assert normalize(legacy) == decimal
        assert legacy_of(decimal) == legacy
    assert legacy_of("8.3") is None
    assert legacy_of("12.4.1") is None


def test_sort_key_follows_instrument_order_not_numeric_value():
    order = HOST_ORDER
    keyed = sorted(["4.1", "4.9", "4.01", "12.4.1", "1.4"], key=lambda i: sort_key(i, order))
    assert keyed == ["1.4", "4.01", "4.9", "4.1", "12.4.1"]
    with pytest.raises(BadIndicatorId):
        sort_key("9.2", order)  # 9.2 does not exist in the host list


def test_vendored_copy_is_byte_identical_to_canonical():
    here = Path(__file__).resolve()
    p3_copy = here.parents[1] / "config" / "indicator_ids.py"
    p0_canon = here.parents[2] / "p0-instrument" / "scripts" / "indicator_ids.py"
    assert p0_canon.exists(), p0_canon
    assert filecmp.cmp(p0_canon, p3_copy, shallow=False), "re-vendor indicator_ids.py"
