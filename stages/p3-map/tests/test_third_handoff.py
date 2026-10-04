"""The third instrument hand-off (4 October 2026, decision D17): the roll-up reads two fields from the
blocks, `count_rule` and `absence_score`, in place of what it used to hard-code.

Run from stages/p3-map:
    python -m pytest tests/test_third_handoff.py -q

What must hold: the roll-up of pillars 6 and 7 says what it always said (pinned in
test_second_handoff.py, and again here for the escalation of 6.1 and 6.2); a count rule counts
distinct laws and never lowers a cell; and an empty cell takes the block's answer, which for twenty
indicators is no score at all. Nothing here talks to a model.
"""
from __future__ import annotations

import dataclasses

import pytest

from config.instrument import ESCALATION_RULE, load
from src.p3map import rollup
from src.p3map.output import submission

INS = load()
COUNTING = ["1.4", "2.1", "2.3", "3.1", "3.4", "4.3", "4.9", "5.2", "5.3", "6.1", "6.2", "9.4", "10.1", "10.2", "10.3"]
UNSCORED = ["1.4", "4.2", "4.5", "4.6", "4.1", "5.1", "5.3", "5.4", "5.7", "7.1", "7.2", "8.1", "8.2", "9.1",
            "11.1", "11.2", "11.4", "12.5", "12.6", "12.9"]


def fire(score, doc="d1", verification="agree"):
    return {"score_hint": score, "doc_id": doc, "verification": verification}


# ---- what the instrument hands over -----------------------------------------------------------------

def test_the_blocks_carry_the_two_fields():
    assert [i for i in INS.blocks if INS.block(i).get("count_rule")] == COUNTING
    assert sorted(i for i in INS.blocks if INS.absence(i) == (True, None)) == sorted(UNSCORED)
    assert sum(1 for i in INS.blocks if INS.absence(i) == (True, 0.0)) == 41
    assert all(INS.absence_basis(i) for i in INS.blocks)
    for i in INS.blocks:
        declared, value = INS.absence(i)
        assert declared and (value is None or INS.on_scale(i, value)), i


def test_every_inverted_and_economy_level_indicator_is_unscored_on_an_absence():
    for i in INS.blocks:
        if INS.is_inverted(i) or INS.level(i) == "economy":
            assert INS.absence(i) == (True, None), i


def test_6_1_and_6_2_declare_the_rule_the_stage_always_applied():
    keys = ("method", "counted_scores", "thresholds", "otherwise", "counted_as")
    for i in ("6.1", "6.2"):
        assert {k: INS.count_rule(i)[k] for k in keys} == {k: ESCALATION_RULE[k] for k in keys}
        assert not INS.count_rule(i).get("needs")
    assert INS.count_rule("6.4") is None and INS.count_rule("7.3") is None


def test_a_vintage_without_the_fields_keeps_the_old_answers():
    old = {i: {k: v for k, v in b.items() if k not in ("count_rule", "absence_score", "absence_basis")}
           for i, b in INS.blocks.items()}
    before = dataclasses.replace(INS, blocks=old)
    assert before.count_rule("6.1") == ESCALATION_RULE and before.count_rule("2.3") is None
    assert before.absence("12.5") == (False, 0.0)
    assert rollup.measure_score(before, "6.1", [fire("0.5"), fire("0.5", "d2")])["score"] == 1.0
    assert rollup.measure_score(before, "12.5", [])["score"] == 0.0
    assert submission.absence_hint(before, "7.1") == "0"


# ---- the count rule -----------------------------------------------------------------------------------

def test_6_1_and_6_2_roll_up_as_they_always_did():
    for i in ("6.1", "6.2"):
        assert rollup.measure_score(INS, i, [fire("0.5"), fire("0.5", "d2"), fire("0.5", "d2")]) == {
            "score": 1.0, "basis": "escalation clause: 2 distinct verified half-point measures",
            "evidence_rows": 3, "pending": 0}
        assert rollup.measure_score(INS, i, [fire("0.5"), fire("0.5")]) == {
            "score": 0.5, "basis": "max over 2 verified fires", "evidence_rows": 2, "pending": 0}, "one law, twice"
        assert rollup.measure_score(INS, i, [fire("1"), fire("0.5", "d2"), fire("0.5", "d3")]) == {
            "score": 1.0, "basis": "max over 3 verified fires", "evidence_rows": 3, "pending": 0}


def test_a_count_rule_counts_distinct_laws_at_the_scores_it_names():
    got = rollup.measure_score(INS, "2.3", [fire("0.5"), fire("0.5", "d2")])
    assert got["score"] == 1.0 and got["basis"] == "escalation clause: 2 distinct verified half-point measures"
    assert rollup.measure_score(INS, "2.3", [fire("0.5"), fire("0.5")])["score"] == 0.5, "two provisions of one law"
    got = rollup.measure_score(INS, "3.4", [fire("0.25"), fire("0.25", "d2")])
    assert got["score"] == 0.5 and got["basis"] == "count rule: 2 distinct verified measures at 0.25 give 0.5"
    assert rollup.measure_score(INS, "3.4", [fire("0.25")])["score"] == 0.25
    # a law counts at its HIGHEST verified score: d1 is a 0.5 law, so only d2 is a 0.25 law
    assert rollup.measure_score(INS, "3.4", [fire("0.25"), fire("0.5"), fire("0.25", "d2")])["score"] == 0.5


def test_a_count_rule_never_lowers_a_cell():
    got = rollup.measure_score(INS, "3.4", [fire("1"), fire("0.25", "d2"), fire("0.25", "d3")])
    assert got["score"] == 1.0 and got["basis"] == "max over 3 verified fires"
    assert rollup.apply_count_rule(INS.count_rule("2.3"), {"d1": 0.5}) == (None, "")


def test_1_4_adds_its_measures_and_stops_at_one():
    got = rollup.measure_score(INS, "1.4", [fire("0.25"), fire("0.25", "d2")])
    assert got["score"] == 0.5 and "added, capped at 1" in got["basis"]
    assert rollup.measure_score(INS, "1.4", [fire("0.5"), fire("0.5", "d2"), fire("0.25", "d3")])["score"] == 1.0
    assert rollup.measure_score(INS, "1.4", [fire("0.25")]) == {
        "score": 0.25, "basis": "max over 1 verified fires", "evidence_rows": 1, "pending": 0}


@pytest.mark.parametrize("ind,fact", [("3.1", "sector"), ("5.2", "measure_key"), ("5.3", "company"),
                                      ("10.1", "products"), ("10.2", "procedure"), ("10.3", "products")])
def test_a_rule_that_needs_a_fact_no_verdict_records_says_laws_stand_in(ind, fact):
    score = f"{INS.count_rule(ind)['counted_scores'][0]:g}"
    got = rollup.measure_score(INS, ind, [fire(score), fire(score, "d2")])
    assert got["score"] == 1.0
    assert "counted by distinct laws" in got["count_note"] and fact in got["count_note"]
    assert "count_note" not in rollup.measure_score(INS, "2.3", [fire("0.5"), fire("0.5", "d2")])


# ---- what an absence scores ---------------------------------------------------------------------------

def test_an_empty_cell_of_pillars_6_and_7_is_still_zero():
    for i in ("6.1", "6.2", "6.3", "6.4", "7.3", "7.4", "7.5"):
        assert rollup.measure_score(INS, i, []) == {
            "score": 0.0, "basis": "no VERIFIED qualifying measure", "evidence_rows": 0, "pending": 0}


@pytest.mark.parametrize("ind", ["12.5", "11.2", "1.4", "5.3", "9.1", "11.4", "12.6"])
def test_an_empty_cell_stays_unscored_where_the_block_says_so(ind):
    got = rollup.measure_score(INS, ind, [])
    assert got["score"] == "unscored" and got["evidence_rows"] == 0
    assert "an absence is left unscored for this indicator" in got["basis"]
    assert INS.absence_basis(ind)[:60] in got["basis"]
    waiting = rollup.measure_score(INS, ind, [fire("1", verification="split_flagged")])
    assert waiting["score"] == "unscored" and waiting["pending"] == 1 and "1 fires pending verification" in waiting["basis"]


def test_a_found_threshold_still_scores_12_5():
    """12.5 is inverted but not economy-level: a de minimis rule that is found scores by its branch."""
    assert rollup.measure_score(INS, "12.5", [fire("0.5")])["score"] == 0.5


# ---- the no-provision row -----------------------------------------------------------------------------

def test_a_no_provision_row_carries_the_blocks_absence_score():
    assert submission.absence_hint(INS, "6.1") == "0" and submission.absence_hint(INS, "3.1") == "0"
    for i in UNSCORED:
        assert submission.absence_hint(INS, i) is None, i


def test_a_no_provision_row_says_what_the_instrument_says():
    for i, text in submission._NP_REASON.items():
        assert submission.np_reason(INS, i) == text, "pillars 6 and 7 keep their wording"
        assert INS.null_statement(i) == " ".join(text.split()), "and the instrument copied it"
    assert submission.np_reason(INS, "3.1") == INS.null_statement("3.1") != "no qualifying measure found"
