"""Tests for config.selection (S2 candidate selection: threshold, floor, ceiling).

Run from stages/p3-map:
    python -m pytest tests/test_selection.py -q

Derivation and the verification against Round 1:
rdtii-finale-3-mapping/notes/2026-09-26-selection-cap-function.md
"""
from __future__ import annotations

import copy

import pytest

from config.indicator_ids import BadIndicatorId
from config.selection import (
    SelectionConfigError, UnknownIndicator, classes, indicators, language_offset,
    load_config, params_for, select_cell, validate_config,
)

CFG = load_config()


# ---- the parameter file itself ------------------------------------------------------

AUTOMATED_NINE = ["6.1", "6.2", "6.3", "6.4", "7.1", "7.2", "7.3", "7.4", "7.5"]


def test_config_covers_the_nine_with_measurements_and_the_rest_with_a_class_only():
    """The nine carry measured theta/floor/ceiling. The other 52 carry ONLY a class.

    That separation is the point: a measured cell states a number someone measured, and a
    class-only cell states an assignment made from the codebook. If a class-only entry ever gains
    its own theta, that is a measurement claim and it needs evidence behind it.
    """
    ids = indicators(CFG)
    assert set(AUTOMATED_NINE) <= set(ids)
    assert CFG["score"]["direct_band"] == 0.65
    assert set(classes(CFG)) == {
        "horizontal_instrument", "subject_specific", "recurring_duty", "prohibition"}
    for iid in AUTOMATED_NINE:
        b = CFG["indicators"][iid]
        assert "theta" in b and "min_candidates" in b and "max_candidates" in b, iid
    for iid in set(ids) - set(AUTOMATED_NINE):
        b = CFG["indicators"][iid]
        assert b.get("class") in classes(CFG), iid
        assert not ({"theta", "min_candidates", "max_candidates"} & set(b)), (
            f"{iid} is class-only; a bare number here is an unevidenced measurement claim")


def test_every_indicator_resolves_and_stays_inside_its_own_bounds():
    for iid in indicators(CFG):
        p = params_for(iid, "SG", "eng")
        assert 0.5 <= p.theta_base <= 0.7, iid
        assert 0 < p.min_candidates <= p.max_candidates, iid


@pytest.mark.parametrize("bad", [
    {"class_defaults": {}},                                              # no classes
    {"indicators": {"6.1": {"theta": 1.4, "min_candidates": 1,
                            "max_candidates": 2, "sparse_topup": 0}}},   # theta out of range
    {"indicators": {"6.1": {"theta": 0.6, "min_candidates": 900,
                            "max_candidates": 100, "sparse_topup": 0}}}, # floor above ceiling
    {"indicators": {"6.1": {"class": "no_such_class"}}},                 # unknown class
])
def test_validate_config_rejects_inconsistency(bad):
    cfg = copy.deepcopy(CFG)
    for k, v in bad.items():
        if k == "indicators":
            cfg[k] = {**cfg[k], **v}
        else:
            cfg[k] = v
    with pytest.raises(SelectionConfigError):
        validate_config(cfg)


# ---- resolving parameters ----------------------------------------------------------

def test_legacy_indicator_ids_are_accepted():
    assert params_for("P7-I3", "MY", "eng").indicator == "7.3"
    assert params_for("7.3", "MY", "eng").theta_base == params_for("P7-I3", "MY", "eng").theta_base


def test_a_float_indicator_id_is_refused():
    # 4.01 and 4.1 are different indicators; nothing may float-parse an ID.
    with pytest.raises(BadIndicatorId):
        params_for("seven point three", "SG", "eng")


def test_language_lowers_the_threshold_and_never_raises_it():
    base = params_for("7.3", "SG", "eng")
    lao = params_for("7.3", "LA", "lao")
    por = params_for("7.3", "TL", "por")
    assert base.language_offset == 0.0
    assert lao.theta < base.theta and por.theta < lao.theta
    assert base.theta == base.theta_base


def test_an_unmeasured_language_gets_the_conservative_default():
    assert language_offset("tha", CFG) == CFG["language_offset"]["_default"]
    assert language_offset(None, CFG) == CFG["language_offset"]["_default"]


def test_an_indicator_outside_the_config_needs_a_class_and_otherwise_refuses():
    """6.5 is the one in-instrument indicator excluded from scope, so it has no entry."""
    with pytest.raises(UnknownIndicator):
        params_for("6.5", "TL", "por")
    p = params_for("6.5", "TL", "por", indicator_class="subject_specific")
    assert p.source == "class:subject_specific"
    assert p.max_candidates == CFG["class_defaults"]["subject_specific"]["max_candidates"]


def test_an_economy_override_wins():
    cfg = copy.deepcopy(CFG)
    cfg["economy_overrides"] = {"CN": {"6.1": {"max_candidates": 2400}}}
    assert params_for("6.1", "CN", "zho", cfg=cfg).max_candidates == 2400
    assert params_for("6.1", "SG", "eng", cfg=cfg).max_candidates == 1800
    assert params_for("6.1", "CN", "zho", cfg=cfg).source == "override"


# ---- selecting ---------------------------------------------------------------------

def ranked(scores):
    """(provision_id, score) in descending score order, as S1 hands it over."""
    return [(f"sg-x-001#s.{i}", s) for i, s in enumerate(sorted(scores, reverse=True))]


def test_the_threshold_binds_when_candidates_run_out_above_it():
    p = params_for("7.4", "SG", "eng")           # theta 0.62, min 100, max 500
    rows = ranked([0.70] * 150 + [0.40] * 500)
    sel = select_cell(rows, "7.4", "SG", "eng")
    assert sel.bound == "theta"
    assert len(sel) == 150
    assert p.min_candidates <= len(sel) <= p.max_candidates


def test_the_ceiling_binds_and_truncates_at_the_maximum():
    rows = ranked([0.80] * 900)                   # 7.4's ceiling is 500
    sel = select_cell(rows, "7.4", "SG", "eng")
    assert sel.bound == "max"
    assert len(sel) == 500


def test_the_floor_takes_the_best_available_when_nothing_clears_the_threshold():
    rows = ranked([0.30] * 400)                   # all far below theta
    sel = select_cell(rows, "7.4", "SG", "eng")
    assert sel.bound == "min"
    assert len(sel) == 100                        # 7.4's floor
    assert sel.direct == ()                       # a below-threshold pick is never direct
    assert len(sel.gray) == 100


def test_exhausted_is_distinct_from_the_floor_binding():
    sel = select_cell(ranked([0.30] * 12), "7.4", "SG", "eng")
    assert sel.bound == "exhausted"
    assert len(sel) == 12                         # the corpus simply holds no more


def test_the_band_splits_at_the_direct_threshold():
    rows = ranked([0.90, 0.80, 0.66, 0.64, 0.63])  # 6.4: theta 0.61, direct band 0.65
    sel = select_cell(rows, "6.4", "SG", "eng")
    assert len(sel.direct) == 3 and len(sel.gray) == 2
    assert len(sel) == 5 and sel.candidates[:3] == sel.direct


def test_language_offset_changes_what_is_selected():
    # 6.2: theta 0.59 for English, 0.56 for Portuguese. 200 rows at 0.575 sit between them.
    rows = ranked([0.575] * 200)
    eng = select_cell(rows, "6.2", "SG", "eng")
    assert eng.bound == "min" and len(eng) == 150        # nothing clears 0.59; the floor takes 150
    assert eng.direct == ()                             # and none of it goes straight to the mapper
    por = select_cell(rows, "6.2", "TL", "por")
    assert por.bound == "theta" and len(por) == 200      # all 200 clear 0.56


def test_sparse_topup_only_where_configured_and_deduped():
    rows = ranked([0.90] * 10)                                 # 10 above theta, then nothing
    extra = ["sg-x-001#s.0", "sg-y-002#s.1", "sg-y-002#s.2"]   # the first is already selected
    on = select_cell(rows, "6.4", "SG", "eng", sparse=extra)   # 6.4 tops up to 100
    assert len(on) == 12 and "sg-y-002#s.2" in on.gray
    off = select_cell(rows, "6.2", "SG", "eng", sparse=extra)  # 6.2 tops up 0
    assert len(off) == 10


def test_a_generator_is_consumed_in_one_pass():
    sel = select_cell(((f"p{i}", 0.9 - i / 1000) for i in range(80)), "7.4", "SG", "eng")
    assert len(sel) == 80 and sel.bound == "exhausted"


def test_report_names_the_binding_term_for_the_run_log():
    r = select_cell(ranked([0.80] * 900), "7.4", "SG", "eng").report()
    assert r["bound_by"] == "max" and r["candidates"] == 500
    assert r["indicator"] == "7.4" and r["economy"] == "SG"
    assert r["theta_effective"] == r["theta_base"]


def test_gold_derived_overrides_are_labelled_in_sample():
    """Decision M15. The four per-cell overrides were fitted to where baseline rows ranked, so a
    recall figure computed with them is in-sample. The file must say so in its own words, because
    a reviewer reads selection.json directly and an unlabelled override reads as a measurement.

    This test exists to stop the labels being quietly rewritten into sounding principled while the
    values stay fitted. If an override is ever genuinely derived without consulting the baseline,
    remove its entry from EXPECTED and say why in the commit.
    """
    import json
    from pathlib import Path

    cfg = json.loads((Path(__file__).resolve().parents[1] / "config/selection.json")
                     .read_text(encoding="utf-8"))
    ov = cfg["economy_overrides"]
    assert "IN-SAMPLE" in ov["_measured"], "_measured must state that these values are fitted"
    assert "56/63" in ov["_measured"], "_measured must name the figure we actually report"

    EXPECTED = [("SG", "7.1"), ("CN", "7.5"), ("CN", "6.2"), ("CN", "7.4")]
    present = [(e, ind) for e, cells in ov.items() if isinstance(cells, dict)
               and not e.startswith("_") for ind in cells]
    assert sorted(present) == sorted(EXPECTED), (
        f"the override set changed: {sorted(present)}. Every entry must carry its own IN-SAMPLE "
        "label and a note on what makes its value fitted.")
    for e, ind in EXPECTED:
        note = ov[e][ind].get("_", "")
        assert "IN-SAMPLE" in note, f"{e} {ind} is not labelled in-sample"
        assert "fitted" in note.lower(), f"{e} {ind} does not say what makes its value fitted"

    # theta is the relevance decision and no override may touch it
    for e, cells in ov.items():
        if not isinstance(cells, dict) or e.startswith("_"):
            continue
        for ind, vals in cells.items():
            assert "theta" not in vals, (
                f"{e} {ind} overrides theta; only floors and ceilings may be adjusted, or the "
                "relevance decision itself becomes fitted")
