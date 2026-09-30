"""Tests for S2's two selection modes and its language resolution.

Run from stages/p3-map:
    python -m pytest tests/test_select_modes.py -q

The end-to-end check for this stage is not here, because it needs a built index: it is the run
against the frozen Round 1 arm recorded in
rdtii-finale-3-mapping/notes/2026-09-27-selection-wired.md — caps mode reproduces Round 1 cell
for cell, scores mode holds gold recall at 37/37 with a quarter fewer candidates. These tests
cover the parts that do not need an index.
"""
from __future__ import annotations

import dataclasses
import json

import pytest

from config.settings import SETTINGS
from src.p3map import select


def test_the_two_modes_are_the_only_two():
    assert select.MODES == ("scores", "caps")
    assert SETTINGS.select_mode in select.MODES, "the default must be one of them"


def test_an_unknown_mode_stops_the_run(tmp_path, monkeypatch):
    """A typo must not fall through to one mode or the other: they cost different money."""
    monkeypatch.setattr(select, "SETTINGS", dataclasses.replace(SETTINGS, select_mode="score"))
    with pytest.raises(SystemExit) as e:
        select.run_select()
    assert "SELECT_MODE" in str(e.value)


def test_caps_cover_every_indicator():
    from config.settings import INDICATORS
    assert set(select.CAPS) == set(INDICATORS)


def _doc_meta(tmp_path, rows: dict) -> object:
    (tmp_path / "doc_meta.json").write_text(json.dumps(rows), encoding="utf-8")
    return dataclasses.replace(SETTINGS, index_dir=tmp_path)


def test_languages_are_resolved_per_economy_by_provision_weight(tmp_path, monkeypatch):
    monkeypatch.setattr(select, "SETTINGS", _doc_meta(tmp_path, {
        "my-a": {"economy": "MY", "language_of_source": "eng", "provision_count": 900},
        "my-b": {"economy": "MY", "language_of_source": "msa", "provision_count": 40},
        "la-a": {"economy": "LA", "language_of_source": "lao", "provision_count": 500},
        # China: the law row is silent, the provisions are not (see ingest)
        "cn-a": {"economy": "CN", "language_of_source": None,
                 "language_of_source_name": "Chinese", "provision_count": 300},
    }))
    assert select._languages() == {"MY": "eng", "LA": "lao", "CN": "zho"}


def test_an_economy_with_no_language_at_all_resolves_to_none(tmp_path, monkeypatch):
    """None is honest, and config/selection.py answers it with the conservative offset."""
    monkeypatch.setattr(select, "SETTINGS", _doc_meta(tmp_path, {
        "xx-a": {"economy": "XX", "provision_count": 10},
    }))
    assert select._languages() == {"XX": None}
    from config.selection import language_offset, load_config
    cfg = load_config()
    assert language_offset(None, cfg) == cfg["language_offset"]["_default"]
    assert language_offset(None, cfg) <= 0, "the default must loosen the threshold, never tighten"


def test_languages_is_empty_without_an_index(tmp_path, monkeypatch):
    monkeypatch.setattr(select, "SETTINGS", dataclasses.replace(SETTINGS, index_dir=tmp_path))
    assert select._languages() == {}


def test_both_index_vintages_are_readable():
    """A 3.5-hour embedding run must survive the decimal migration."""
    import numpy as np
    legacy = {"P6-I1_idx": np.array([1, 2]), "P6-I1_score": np.array([0.9, 0.8])}
    decimal = {"6.1_idx": np.array([3]), "6.1_score": np.array([0.7])}
    for leg in (legacy, decimal):
        assert len(select._leg_top(leg, "6.1")) >= 1
        assert len(select._leg_scores(leg, "6.1")) >= 1
    with pytest.raises(KeyError) as e:
        select._leg_top({}, "6.1")
    assert "6.1_idx" in str(e.value) and "P6-I1_idx" in str(e.value)


def test_a_pair_row_names_its_signal():
    """Downstream reads `score`; which signal produced it decides what the number means."""
    m = {"provision_id": "sg-x-001#s.26", "doc_id": "sg-x-001", "economy": "SG",
         "law_name": "Act", "article_section": "s.26"}
    row = json.loads(select._pair(m, "6.4", 0.6123456, "dense_cosine"))
    assert row["indicator"] == "6.4"
    assert row["score"] == 0.612346
    assert row["signal"] == "dense_cosine"
    assert row["provision_id"] == m["provision_id"]
