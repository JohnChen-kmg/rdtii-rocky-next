"""Tests for config.instrument — the normalising view of the vendored instrument.

Run from stages/p3-map:
    python -m pytest tests/test_instrument.py -q

The loader exists so the stage behaves identically against either vendored vintage (Round 1's
`P6-I1` files or the finale's `6.1` files), which makes the 30 September hand-off a file swap
instead of a code change. Almost every test here is therefore written to pass BOTH before and
after that swap; the two that are not say so in their names, and the last one compares the
vintages directly whenever the finale instrument is reachable.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from config.instrument import ESCALATION_IDS, InstrumentError, load
from config.settings import INDICATORS

DECIMAL = re.compile(r"^\d{1,2}\.\d{1,2}(?:\.\d{1,2})?$")
# The automated set, decision M7. Nine indicators on either vintage.
NINE = ("6.1", "6.2", "6.3", "6.4", "7.1", "7.2", "7.3", "7.4", "7.5")
ECONOMY_LEVEL = {"7.1", "7.2"}          # answered once per economy, not per provision
BINARY = {"6.3", "7.3", "7.5"}          # scoring tree offers no 0.5
INVERTED = {"7.1", "7.2"}               # "Lack of ..." — an absent framework scores 1

# Where the finale instrument lives while it waits for the hand-off. Relative to the stage root
# so the probe is portable; the test skips when it is not there.
FINALE_CANDIDATES = ("../../../rdtii-finale-0-instrument/instrument/output",)


@pytest.fixture(scope="module")
def ins():
    return load()


def test_loads_and_is_cached(ins):
    assert ins.dir.exists()
    assert ins.vintage in ("legacy", "decimal")
    assert load() is ins, "load() must be cached — every stage calls it per indicator"
    assert ins.blocks, "no codebook blocks"


def test_vintage_follows_the_files(ins):
    """`indicator_order.yaml` is the finale instrument's own marker, and nothing else."""
    assert (ins.dir / "indicator_order.yaml").exists() == (ins.vintage == "decimal")
    assert (ins.order is not None) == (ins.vintage == "decimal")


def test_ids_are_decimal_text_whatever_the_files_say(ins):
    assert ins.ids, "empty automated set"
    assert len(set(ins.ids)) == len(ins.ids), "duplicate indicator id"
    for iid in ins.ids:
        assert DECIMAL.match(iid), f"{iid!r} is not decimal text"
        assert "P" not in iid and "-" not in iid
    assert set(ins.ids) == set(NINE), "the automated set is decision M7's nine"


def test_settings_indicators_come_from_the_loader():
    assert tuple(INDICATORS) == load().ids


def test_blocks_are_keyed_decimally_and_accept_either_form(ins):
    block = ins.block("6.1")
    assert isinstance(block, dict) and block
    assert ins.block("P6-I1") is block, "a legacy id must normalise to the same block"
    assert ins.name("6.1")
    for iid in ins.ids:
        assert iid in ins.blocks


def test_unknown_indicator_names_the_vintage(ins):
    with pytest.raises(InstrumentError) as e:
        ins.block("6.99")
    assert "6.99" in str(e.value) and ins.vintage in str(e.value)


def test_level(ins):
    for iid in ins.ids:
        expected = "economy" if iid in ECONOMY_LEVEL else "provision"
        assert ins.level(iid) == expected, iid


def test_is_binary_is_read_from_the_scoring_tree(ins):
    for iid in ins.ids:
        assert ins.is_binary(iid) is (iid in BINARY), iid


def test_is_inverted(ins):
    for iid in ins.ids:
        assert ins.is_inverted(iid) is (iid in INVERTED), iid


def test_escalation_ids_are_decimal():
    assert ESCALATION_IDS == frozenset({"6.1", "6.2"})


def test_every_automated_indicator_has_a_usable_signature(ins):
    sigs = ins.signatures()
    assert set(sigs) == set(ins.ids)
    for iid, sig in sigs.items():
        assert sig["indicator"] == iid, "the loader normalises the id in the file"
        assert sig.get("name"), iid
        assert (sig.get("definition_text") or "").strip(), iid
        assert sig.get("keywords"), iid


def test_missing_signature_raises_and_lists_what_it_tried(ins, tmp_path):
    (tmp_path / "signatures").mkdir()
    (tmp_path / "indicators.yaml").write_text(
        "indicators:\n  - id: '6.1'\n    name: x\n", encoding="utf-8")
    with pytest.raises(InstrumentError) as e:
        load(str(tmp_path)).signature("6.1")
    assert "6.1" in str(e.value) and "P6-I1" in str(e.value)


def test_gold_rows_arrive_normalised(ins):
    rows = list(ins.gold())
    assert rows, "no gold rows"
    seen = set()
    for r in rows:
        iid = r["indicator"]
        assert iid is None or DECIMAL.match(iid), repr(iid)
        if iid:
            seen.add(iid)
    assert set(NINE) <= seen, "gold must cover the automated set"
    for r in rows[:50]:
        assert re.match(r"^[A-Z]{2}$", r.get("economy") or ""), r.get("gold_id")


def test_gold_is_never_a_decision_input():
    """The loader hands gold out as an iterator of plain rows and nothing else.

    Decision #11 keeps the allowlist off: gold is a yardstick, so no helper here may resolve a
    gold row to a candidate. This test fails if such a helper is ever added.
    """
    api = {n for n in dir(load()) if not n.startswith("_")}
    assert "gold" in api
    assert not {n for n in api if "allow" in n or "seed" in n}


def test_an_empty_directory_is_an_instrument_error(tmp_path):
    with pytest.raises(InstrumentError):
        load(str(tmp_path))


def test_a_codebook_with_no_readable_ids_is_an_instrument_error(tmp_path):
    (tmp_path / "indicators.yaml").write_text(
        "indicators:\n  - id: not-an-id\n    name: x\n", encoding="utf-8")
    with pytest.raises(InstrumentError):
        load(str(tmp_path))


def _finale_dir() -> Path | None:
    for cand in FINALE_CANDIDATES:
        p = Path(cand)
        if (p / "indicators.yaml").exists() and (p / "indicator_order.yaml").exists():
            return p
    return None


def test_both_vintages_answer_the_nine_identically():
    """The hand-off must not change a single answer the stage depends on.

    Skipped once the finale instrument IS the vendored one (there is then only one vintage to
    compare), and wherever the instrument workshop is not on disk.
    """
    finale = _finale_dir()
    if finale is None:
        pytest.skip("finale instrument not reachable from this checkout")
    a, b = load(), load(str(finale))
    if a.vintage == b.vintage == "decimal":
        pytest.skip("hand-off done — both copies are the decimal vintage")
    assert a.ids == b.ids
    for iid in a.ids:
        assert a.level(iid) == b.level(iid), iid
        assert a.is_binary(iid) == b.is_binary(iid), iid
        assert a.is_inverted(iid) == b.is_inverted(iid), iid
        assert b.signature(iid)["indicator"] == iid
    assert len(b.blocks) > len(a.blocks), "the finale codebook carries all 61 blocks"
    assert len(list(b.gold())) > len(list(a.gold()))
