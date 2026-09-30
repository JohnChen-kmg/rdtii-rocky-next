"""Tests for config.llm.engines and the factory's engine path (finale plan J2, J3).

Run from stages/p3-map:
    python -m pytest tests/test_engines.py -q

Submission checklist item 9 asks that the model backend be swappable "from inside the interface,
with no code or config change", and C5b awards four marks for showing the swap. That needs one
name, and it needs the old configuration to keep working unchanged — a run configured yesterday
must resolve today exactly as it did then.
"""
from __future__ import annotations

import dataclasses
import json

import pytest

from config.llm import engines
from config.llm.factory import get_llm
from config.settings import SETTINGS

ANTHROPIC = dataclasses.replace(
    SETTINGS, llm_provider="anthropic", anthropic_api_key="test-key-not-used",
    llm_model="claude-sonnet-5", verifier_model="claude-haiku-4-5",
    escalation_model="claude-opus-4-8", ollama_model="llama3.1:8b",
    triage_model="qwen2.5:14b")


@pytest.fixture(autouse=True)
def _no_engine(monkeypatch):
    """Each test says for itself whether an engine is selected."""
    monkeypatch.delenv(engines.ENGINE_ENV, raising=False)
    for var in engines.ROLE_ENV.values():
        monkeypatch.delenv(var, raising=False)


def test_two_engines_are_declared_one_of_them_open_weights():
    ids = engines.ids()
    assert ids == ["A", "B"], "C4b/C5b declare exactly two"
    assert engines.get("A").open_weights is False
    assert engines.get("B").open_weights is True
    assert engines.default_id() in ids


def test_engine_b_is_pinned_by_digest():
    """A tag can be repointed upstream; a digest cannot."""
    b = engines.get("B")
    assert b.digest and b.digest.startswith("sha256:")
    assert len(b.digest.split(":", 1)[1]) == 64
    assert engines.get("A").digest is None, "no dated checkpoint string exists for these models"


def test_every_engine_names_a_model_for_every_role():
    doc = engines.load()
    for eid in engines.ids():
        e = engines.get(eid)
        for role in doc["roles"]:
            assert e.model_for(role), f"{eid}:{role}"


def test_only_engine_a_declares_the_batch_lane():
    """The Message Batches lane is Anthropic-only by decision M3."""
    assert engines.get("A").batch_lane is True
    assert engines.get("B").batch_lane is False


def test_nothing_is_selected_unless_the_variable_is_set(monkeypatch):
    assert engines.selected() is None, "an unset engine is the pre-engine path, not the default"
    monkeypatch.setenv(engines.ENGINE_ENV, "B")
    assert engines.selected().id == "B"
    monkeypatch.setenv(engines.ENGINE_ENV, "  b  ")
    assert engines.selected().id == "B", "trimmed and case-insensitive"
    monkeypatch.setenv(engines.ENGINE_ENV, "")
    assert engines.selected() is None


def test_an_undeclared_engine_raises_and_lists_the_declared_ones(monkeypatch):
    monkeypatch.setenv(engines.ENGINE_ENV, "C")
    with pytest.raises(engines.EngineError) as e:
        engines.selected()
    assert "RDTII_ENGINE" in str(e.value)
    for eid in engines.ids():
        assert eid in str(e.value)


def test_an_explicit_model_variable_beats_the_engine(monkeypatch):
    """The A/B harnesses pin two models of one provider; that must keep working."""
    monkeypatch.setenv(engines.ENGINE_ENV, "B")
    monkeypatch.setenv("LLM_MODEL", "qwen2.5:32b")
    assert engines.selected().model_for("mapper") == "qwen2.5:32b"
    assert engines.selected().model_for("verifier") == "qwen2.5:14b", "only the role that was set"


def test_the_factory_follows_the_selected_engine(monkeypatch):
    monkeypatch.setenv(engines.ENGINE_ENV, "B")
    for role in ("mapper", "verifier", "escalation", "triage"):
        c = get_llm(ANTHROPIC, role=role)
        assert type(c).__name__ == "OllamaClient", role
        assert c.model == "qwen2.5:14b", role


def test_engine_b_needs_no_api_key(monkeypatch):
    """Checklist item 12: the pipeline must run on the open-weights engine alone."""
    monkeypatch.setenv(engines.ENGINE_ENV, "B")
    no_key = dataclasses.replace(ANTHROPIC, anthropic_api_key="")
    for role in ("mapper", "verifier", "escalation"):
        assert get_llm(no_key, role=role).model == "qwen2.5:14b"


def test_engine_a_still_refuses_without_a_key(monkeypatch):
    from config.llm.factory import LLMConfigError
    monkeypatch.setenv(engines.ENGINE_ENV, "A")
    with pytest.raises(LLMConfigError) as e:
        get_llm(dataclasses.replace(ANTHROPIC, anthropic_api_key=""), role="mapper")
    assert "RDTII_ENGINE" in str(e.value), "the message must name the engine route"


def test_with_no_engine_the_old_configuration_decides(monkeypatch):
    """The pre-engine path, unchanged: LLM_PROVIDER plus the four model variables."""
    local = dataclasses.replace(ANTHROPIC, llm_provider="ollama", ollama_model="llama3.1:8b")
    assert get_llm(local, role="mapper").model == "llama3.1:8b"
    assert engines.selected() is None


def test_the_manifest_records_the_engine_and_its_digest(monkeypatch, tmp_path):
    from config import manifest
    monkeypatch.setenv(engines.ENGINE_ENV, "B")
    monkeypatch.setattr("config.settings.SETTINGS",
                        dataclasses.replace(SETTINGS, out_dir=tmp_path / "out"))
    manifest.record("map", economy="CN")
    m = json.loads(manifest.path().read_text(encoding="utf-8"))
    assert m["engine"]["engine_id"] == "B"
    assert m["engine"]["digest"].startswith("sha256:")
    assert m["engine"]["open_weights"] is True
    assert m["entries"][0]["engine"]["mapper"]["model"] == "qwen2.5:14b"


def test_a_bad_engine_shows_up_in_the_manifest_rather_than_crashing_a_run(monkeypatch, tmp_path):
    from config import manifest
    monkeypatch.setenv(engines.ENGINE_ENV, "nonsense")
    monkeypatch.setattr("config.settings.SETTINGS",
                        dataclasses.replace(SETTINGS, out_dir=tmp_path / "out"))
    assert "error" in manifest._engine()


def test_the_batch_lane_refuses_an_engine_that_does_not_declare_it(monkeypatch):
    from config.llm.factory import LLMConfigError
    from src.p3map.mapping.batch_runner import _require_batch_provider
    monkeypatch.setenv(engines.ENGINE_ENV, "B")
    with pytest.raises(LLMConfigError) as e:
        _require_batch_provider("submit")
    assert "batch lane" in str(e.value)
    monkeypatch.setenv(engines.ENGINE_ENV, "A")
    _require_batch_provider("submit")     # must not raise
