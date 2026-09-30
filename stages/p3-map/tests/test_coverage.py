"""Tests for config.coverage — what the tool automates, and what a row discloses (M8, M9).

Run from stages/p3-map:
    python -m pytest tests/test_coverage.py -q

Both decisions turn on the same thing: "the mark is only honest if it is complete. A notification on
some uncovered indicators and silence on others tells the reader that silence means covered." So the
classification has to come from the instrument rather than a list, and it has to answer for every
indicator, including ones this stage has never seen.
"""
from __future__ import annotations

import pytest

from config.coverage import (
    AUTOMATED, EXCLUDED, MANUAL, PORTAL_TIER_GAPS, REASONS, classify, notification,
)
from config.instrument import load
from config.settings import INDICATORS


def test_the_automated_set_is_the_stage_scope():
    for iid in INDICATORS:
        c = classify(iid)
        assert c.cls == AUTOMATED, iid
        assert c.automated is True
        assert c.note == "", "a fully covered row has nothing to disclose"


def test_the_counts_match_the_coverage_register():
    """The register says 9 automated, 52 manual, and 6.5 excluded from the host's 62."""
    ins = load()
    if not ins.order:
        pytest.skip("the legacy instrument carries no indicator_order.yaml")
    counts = {AUTOMATED: 0, MANUAL: 0, EXCLUDED: 0}
    for e in ins.order["indicators"]:
        counts[classify(e["id"]).cls] += 1
    assert counts == {AUTOMATED: 9, MANUAL: 52, EXCLUDED: 1}


def test_an_out_of_scope_indicator_gets_no_row_and_no_sentence():
    ins = load()
    if not ins.order:
        pytest.skip("the legacy instrument carries no indicator_order.yaml")
    c = classify("6.5")
    assert c.cls == EXCLUDED
    assert c.note == "", "instrument D10: no row at all, so nothing to say in one"


def test_practice_evidence_is_named_as_such():
    """3.4, 5.3 and 9.1 are marked `evidence: practice` in the instrument."""
    ins = load()
    if not ins.order:
        pytest.skip("the legacy instrument carries no indicator_order.yaml")
    for iid in ("3.4", "5.3", "9.1"):
        c = classify(iid)
        assert c.cls == MANUAL, iid
        assert c.reason == "practice", iid
        assert REASONS["practice"] in c.note


def test_an_indicator_outside_the_automated_set_says_so():
    ins = load()
    if not ins.order:
        pytest.skip("the legacy instrument carries no indicator_order.yaml")
    c = classify("1.4")
    assert c.cls == MANUAL and c.reason == "scope"
    assert "Not automated" in c.note
    assert "Check it outside the tool" in c.note


def test_an_indicator_the_instrument_has_never_heard_of_is_still_answered():
    """Silence must never mean covered, so an unknown id is manual, not automated."""
    c = classify("11.9")
    assert c.cls == MANUAL
    assert c.note


def test_chinas_pillar_six_is_marked_and_its_pillar_seven_is_not():
    """The register: China's database stops above departmental rules, so pillar 6 is
    framework-only there, while pillar 7 is covered 5 of 5."""
    assert PORTAL_TIER_GAPS["CN"] == (6,)
    for iid in ("6.1", "6.2", "6.3", "6.4"):
        c = classify(iid, "CN")
        assert c.cls == AUTOMATED, "it is still mapped"
        assert c.partial is True
        assert "Framework-level only" in c.note
        assert "check the result outside the tool" in c.note
    for iid in ("7.1", "7.2", "7.3", "7.4", "7.5"):
        assert classify(iid, "CN").note == "", iid


def test_no_other_economy_is_marked():
    for econ in ("SG", "MY", "AU", "LA", "TL"):
        for iid in INDICATORS:
            assert notification(iid, econ) == "", f"{econ}:{iid}"


def test_the_economy_argument_is_optional_and_case_insensitive():
    assert classify("6.1", "cn").partial is True
    assert classify("6.1", " CN ").partial is True
    assert classify("6.1").partial is False, "with no economy there is no portal claim to make"


def test_the_sentence_is_one_string_in_one_place():
    """M9: "The sentence is one string in one place." One reason category per row, named."""
    seen = {classify(i, "CN").note for i in ("6.1", "6.2")} | {classify("1.4").note}
    assert len(seen) == 2
    for note in seen:
        assert note.endswith(".")
        assert note.count("Reason:") <= 1
