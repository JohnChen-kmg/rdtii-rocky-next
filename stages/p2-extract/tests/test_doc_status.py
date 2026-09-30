"""doc_status.jsonl invariants (finding #4)."""

import pytest

from rdtii_p2.status import DocStatus


def test_ok_requires_provisions():
    with pytest.raises(ValueError):
        DocStatus("sg-x-001", "ok", 0, "B", None, "pdf_native")
    DocStatus("sg-x-001", "ok", 3, "B", None, "pdf_native")


def test_non_ok_must_have_zero_provisions():
    with pytest.raises(ValueError):
        DocStatus("sg-x-001", "cost_aborted", 2, "B", "cap hit", "pdf_native")
    for status in ("zero_provisions", "cost_aborted", "parse_failed"):
        DocStatus("sg-x-001", status, 0, "B", "reason", "pdf_native")


def test_invalid_status_rejected():
    with pytest.raises(ValueError):
        DocStatus("sg-x-001", "skipped", 0, None, None, None)
