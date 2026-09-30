"""Tests for config.manifest — the run record the engine swap is proven from.

Run from stages/p3-map:
    python -m pytest tests/test_manifest.py -q

C5b's four marks rest on showing that one pipeline produced rows on two engines, and Section 3's
second-pass check on showing a run that fetched nothing. A filed row records neither, so if the
manifest is wrong or absent the claim cannot be made at all — and that is why `record()` is
written to swallow its own failures rather than take a paid run down with it.
"""
from __future__ import annotations

import dataclasses
import json

import pytest

from config import manifest
from config.settings import SETTINGS


@pytest.fixture
def run_dir(tmp_path, monkeypatch):
    """A manifest in a scratch out/ directory, with SETTINGS pointed at it."""
    settings = dataclasses.replace(SETTINGS, out_dir=tmp_path / "out")
    monkeypatch.setattr("config.settings.SETTINGS", settings)
    return settings


def test_the_header_records_what_a_reviewer_has_to_check(run_dir):
    h = manifest.header()
    assert h["run_id"], "a run with no id cannot be cited in the write-up"
    assert h["created"]
    assert h["contract_version"] == SETTINGS.contract_version
    assert set(h["engine"]["roles"]) == {"mapper", "verifier", "escalation", "triage"}
    assert h["instrument"]["vintage"] in ("legacy", "decimal")
    assert h["instrument"]["indicators"], "the automated set is part of what a run means"
    assert h["entries"] == []
    for key in ("select_mode", "economies", "newknown_sim", "handoff2_dir"):
        assert key in h["settings"]


def test_the_commit_is_recorded_and_dirtiness_with_it(run_dir):
    git = manifest.header()["git"]
    if not git["commit"]:
        pytest.skip("not a git checkout")
    assert len(git["commit"]) == 40
    assert isinstance(git["dirty"], bool), "a dirty tree must be visible, not implied"


def test_record_appends_and_persists(run_dir):
    manifest.record("ingest", records=766526, documents=9006)
    manifest.record("select", mode="scores", direct=3648)
    m = json.loads(manifest.path().read_text(encoding="utf-8"))
    assert [e["stage"] for e in m["entries"]] == ["ingest", "select"]
    assert m["entries"][0]["records"] == 766526
    assert m["entries"][1]["mode"] == "scores"
    assert m["entries"][0]["at"] <= m["entries"][1]["at"]


def test_every_entry_carries_its_own_engine(run_dir):
    """A run resumed after an engine change must not claim the header's engine for old rows."""
    manifest.record("map", economy="SG")
    e = json.loads(manifest.path().read_text(encoding="utf-8"))["entries"][0]
    assert set(e["engine"]) == {"mapper", "verifier", "escalation", "triage"}
    assert e["engine"]["mapper"]["model"]


def test_record_never_raises_even_when_it_cannot_write(tmp_path, monkeypatch, capsys):
    """A lost mark beats a lost day: the mapper must not die writing its own record."""
    blocked = tmp_path / "file-not-a-dir"
    blocked.write_text("", encoding="utf-8")
    monkeypatch.setattr("config.settings.SETTINGS",
                        dataclasses.replace(SETTINGS, out_dir=blocked / "out"))
    manifest.record("map", economy="SG")        # must not raise
    assert "[manifest] WARNING" in capsys.readouterr().out


def test_the_engine_block_follows_llm_provider(monkeypatch):
    """The swap has to be visible here, or it cannot be shown to have happened."""
    monkeypatch.setattr("config.settings.SETTINGS", dataclasses.replace(
        SETTINGS, llm_provider="ollama", ollama_model="qwen2.5:14b",
        triage_model="qwen2.5:14b", llm_model="claude-sonnet-5"))
    eng = manifest._engine()
    assert eng["provider"] == "ollama"
    assert eng["open_weights"] is True
    for role in ("mapper", "verifier", "escalation", "triage"):
        assert eng["roles"][role]["model"] == "qwen2.5:14b", role

    monkeypatch.setattr("config.settings.SETTINGS", dataclasses.replace(
        SETTINGS, llm_provider="anthropic", llm_model="claude-sonnet-5",
        verifier_model="claude-haiku-4-5", escalation_model="claude-opus-4-8",
        triage_model="qwen2.5:14b"))
    eng = manifest._engine()
    assert eng["open_weights"] is False
    assert eng["roles"]["mapper"]["model"] == "claude-sonnet-5"
    assert eng["roles"]["verifier"]["model"] == "claude-haiku-4-5"
    assert eng["roles"]["escalation"]["model"] == "claude-opus-4-8"
    assert eng["roles"]["triage"]["provider"] == "ollama", "decision #3: triage is always local"


def test_an_unknown_provider_is_recorded_as_an_error_not_a_crash(monkeypatch):
    monkeypatch.setattr("config.settings.SETTINGS",
                        dataclasses.replace(SETTINGS, llm_provider="openai"))
    roles = manifest._engine()["roles"]
    assert roles["mapper"]["model"] is None
    assert "error" in roles["mapper"]


def test_summary_names_the_models_and_the_entries(run_dir):
    manifest.record("map", economy="SG", provisions_mapped=1200, resumed_past=0)
    manifest.record("map", economy="SG", provisions_mapped=0, resumed_past=1200)
    text = manifest.summary()
    assert "mapper=" in text
    assert "provisions_mapped=0" in text, "the second pass must be legible in one glance"
    assert "resumed_past=1200" in text


# ------------------------------------------------------- what the run was scoped to


def test_the_header_records_which_indicators_the_run_covered():
    """`economies` was recorded and the indicator scope was not, so an arm covering a SUBSET of the
    instrument did not say which subset. On 29 September that cost a file: re-emitting
    Timor-Leste's 52-indicator arm without setting INDICATORS_SCOPE silently produced 9 rows for
    the default nine indicators, 83 rows were overwritten, and the manifest could not say what the
    original scope had been -- it had to be recovered from that arm's own rollup.
    """
    from config.settings import INDICATORS
    s = manifest.header()["settings"]
    assert s["indicators"] == list(INDICATORS), "the resolved list, so it is true either way"
    assert s["indicators_count"] == len(INDICATORS)
    assert "indicators_scope_env" in s, "and whether it came from a setting or the default"


def test_the_scope_is_the_resolved_list_not_the_raw_setting(monkeypatch):
    """Recorded resolved, so a default-scoped run says what it covered rather than saying nothing.
    The raw variable is kept beside it to show where the scope came from."""
    s = manifest.header()["settings"]
    assert s["indicators"], "a run with no INDICATORS_SCOPE still names its indicators"
    assert "unset" in s["indicators_scope_env"], "and says the scope was not set by hand"
