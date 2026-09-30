"""Indicator ID helpers — finale decision F1: decimal text is the one vocabulary.

The host's finale template writes indicator IDs as text: '6.1', '4.01', '12.4.1'.
This module exists to prevent two hazards:

  * never float-parse an ID   — float('4.01') == float('4.1'), but 4.01 (Patent
    application issues) and 4.1 (Lack of trade-secrets framework) are DIFFERENT
    indicators
  * never derive order from the ID — the host's numbering has gaps, and 4.01 sorts
    before 4.1 only by convention; order comes from the instrument list

Canonical copy: stages/p0-instrument/scripts/indicator_ids.py
Vendored copy:  stages/p3-map/config/indicator_ids.py   (the validator diffs the two)
"""
from __future__ import annotations

import re

LEGACY_RE = re.compile(r"^P(\d{1,2})-I(\d{1,2})$")            # Round-1 form, e.g. P6-I1
DECIMAL_RE = re.compile(r"^\d{1,2}\.\d{1,2}(?:\.\d{1,2})?$")  # 6.1 · 4.01 · 12.4.1

# The nine Round-1 indicators, for reading Round-1 artifacts and diffing the baseline.
LEGACY_TO_DECIMAL = {
    "P6-I1": "6.1", "P6-I2": "6.2", "P6-I3": "6.3", "P6-I4": "6.4",
    "P7-I1": "7.1", "P7-I2": "7.2", "P7-I3": "7.3", "P7-I4": "7.4", "P7-I5": "7.5",
}
DECIMAL_TO_LEGACY = {v: k for k, v in LEGACY_TO_DECIMAL.items()}


class BadIndicatorId(ValueError):
    """Raised for anything that is not a recognisable indicator ID."""


def normalize(raw) -> str:
    """'P6-I1' | '6.1' | ' 12.4.1 ' | 6.1 (float from a spreadsheet) -> canonical text.

    Floats are accepted only because openpyxl returns them for numeric cells; they are
    rendered with '%g' (6.1 -> '6.1', 7.3000000001 -> '7.3'). Anything else raises.
    """
    if isinstance(raw, bool):
        raise BadIndicatorId(raw)
    if isinstance(raw, (int, float)):
        s = "%g" % raw
    else:
        s = str(raw).strip()
    m = LEGACY_RE.match(s)
    if m:
        s = f"{int(m.group(1))}.{int(m.group(2))}"
    if not DECIMAL_RE.match(s):
        raise BadIndicatorId(raw)
    return s


def is_indicator_id(raw) -> bool:
    try:
        normalize(raw)
        return True
    except BadIndicatorId:
        return False


def pillar_of(iid) -> int:
    """'12.4.1' -> 12. Same result as the host template's 'Pillar (auto)' column formula."""
    return int(normalize(iid).split(".")[0])


def legacy_of(iid) -> str | None:
    """'6.1' -> 'P6-I1' for the nine Round-1 indicators; None for every other ID."""
    return DECIMAL_TO_LEGACY.get(normalize(iid))


def sort_key(iid, order) -> tuple[int, int]:
    """Sort by instrument order, never by numeric value.

    `order` is the instrument's ordered ID list. Unknown IDs raise, because an ID that
    is not in the instrument should never reach a sort.
    """
    iid = normalize(iid)
    try:
        return (pillar_of(iid), list(order).index(iid))
    except ValueError:
        raise BadIndicatorId(f"{iid} not in instrument order") from None
