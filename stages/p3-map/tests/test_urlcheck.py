"""Tests for which economies the URL check actually checks.

Run from stages/p3-map:
    python -m pytest tests/test_urlcheck.py -q

Nothing here makes a request. Round 1 hard-coded ("SG", "MY", "AU"), so after the hand-off a China
or Lao PDR run would have printed "0 unique URLs, 0 not OK" and exited zero, having opened no filed
row at all — the failure mode that matters here is the one that looks like a pass.
"""
from __future__ import annotations

import dataclasses

import pytest

from config.settings import SETTINGS
from src.p3map.output import urlcheck


def _emit(tmp_path, *economies, name="records_{}.csv"):
    d = tmp_path / "submission"
    d.mkdir(parents=True, exist_ok=True)
    for e in economies:
        (d / name.format(e)).write_text(
            "Economy,Indicator ID,Source URL\nX,6.1,https://example.gov/a\n", encoding="utf-8")
    return dataclasses.replace(SETTINGS, out_dir=tmp_path)


def test_it_checks_whatever_the_run_emitted(tmp_path, monkeypatch):
    monkeypatch.setattr(urlcheck, "SETTINGS", _emit(tmp_path, "CN", "LA", "TL"))
    monkeypatch.setattr(urlcheck, "ECONOMIES", ())
    got = {p.stem.split("_", 1)[1] for p in urlcheck._emitted_csvs()}
    assert got == {"CN", "LA", "TL"}


def test_economies_narrows_it(tmp_path, monkeypatch):
    monkeypatch.setattr(urlcheck, "SETTINGS", _emit(tmp_path, "CN", "LA", "SG"))
    monkeypatch.setattr(urlcheck, "ECONOMIES", ("CN", "LA"))
    got = {p.stem.split("_", 1)[1] for p in urlcheck._emitted_csvs()}
    assert got == {"CN", "LA"}


def test_an_economy_that_emitted_nothing_is_simply_absent(tmp_path, monkeypatch):
    monkeypatch.setattr(urlcheck, "SETTINGS", _emit(tmp_path, "CN"))
    monkeypatch.setattr(urlcheck, "ECONOMIES", ("CN", "LA"))
    got = {p.stem.split("_", 1)[1] for p in urlcheck._emitted_csvs()}
    assert got == {"CN"}, "no crash, and no silent claim about LA either"


def test_nothing_to_check_is_an_error_not_a_pass(tmp_path, monkeypatch):
    """The Round 1 failure mode: a green report over zero rows."""
    monkeypatch.setattr(urlcheck, "SETTINGS", _emit(tmp_path))
    monkeypatch.setattr(urlcheck, "ECONOMIES", ())
    with pytest.raises(SystemExit) as e:
        urlcheck._emitted_csvs()
    assert "records_XX.csv" in str(e.value)


def test_only_two_letter_economy_files_are_read(tmp_path, monkeypatch):
    """A holdout or scratch CSV beside the real ones must not become an economy."""
    settings = _emit(tmp_path, "SG")
    (tmp_path / "submission" / "records_SG_draft.csv").write_text("x\n", encoding="utf-8")
    (tmp_path / "submission" / "records_all.csv").write_text("x\n", encoding="utf-8")
    monkeypatch.setattr(urlcheck, "SETTINGS", settings)
    monkeypatch.setattr(urlcheck, "ECONOMIES", ())
    assert [p.name for p in urlcheck._emitted_csvs()] == ["records_SG.csv"]


def test_the_economy_comes_from_the_filename(tmp_path, monkeypatch):
    """run_urlcheck labels each citation with it, so a wrong split mislabels every row."""
    monkeypatch.setattr(urlcheck, "SETTINGS", _emit(tmp_path, "LA"))
    monkeypatch.setattr(urlcheck, "ECONOMIES", ())
    p = urlcheck._emitted_csvs()[0]
    assert p.stem.split("_", 1)[1] == "LA"


def test_run_urlcheck_checks_http_urls_and_passes_over_placeholders(tmp_path, monkeypatch):
    """End to end with the network stubbed: what is checked, what is skipped, what exit code."""
    import json
    d = tmp_path / "submission"
    d.mkdir(parents=True)
    (d / "records_LA.csv").write_text("""Economy,Indicator ID,Source URL
Lao PDR,6.1,https://laoofficialgazette.gov.la/act
Lao PDR,6.2,https://laoofficialgazette.gov.la/act
Lao PDR,7.3,n/a - hold-out economy without corpus (documented placeholder)
""", encoding="utf-8")
    monkeypatch.setattr(urlcheck, "SETTINGS", dataclasses.replace(SETTINGS, out_dir=tmp_path))
    monkeypatch.setattr(urlcheck, "ECONOMIES", ())
    calls = []

    def fake_check(url, cache):
        calls.append(url)
        return "200"

    monkeypatch.setattr(urlcheck, "check_url", fake_check)
    bad = urlcheck.run_urlcheck()

    assert bad == 0, "a placeholder is not a broken URL"
    assert calls == ["https://laoofficialgazette.gov.la/act"], "one request per UNIQUE url"
    out = next((tmp_path / "urlcheck").glob("submission_urls_*.json"))
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["checked"] == 2 and report["not_ok"] == 0
    kinds = {r["status"] for r in report["results"]}
    assert kinds == {"200", "placeholder"}
    cited = [r for r in report["results"] if r["status"] == "200"][0]["rows"]
    assert len(cited) == 2 and all(c.startswith("LA:") for c in cited), cited
