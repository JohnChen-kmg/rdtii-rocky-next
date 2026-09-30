"""Tests for config.llm.factory — the engine seam (C4b/C5b, kickoff decision #3).

Run from stages/p3-map:
    python -m pytest tests/test_llm_factory.py -q

Nothing here talks to a model. The seam's job is to resolve (provider, model) correctly and to
refuse the combinations the declaration forbids, and that is all these tests check.
"""
from __future__ import annotations

import dataclasses

import pytest

from config.llm.factory import JUDGING_ROLES, LLMConfigError, PROVIDERS, ROLES, get_llm
from config.settings import SETTINGS


def cfg(**kw):
    return dataclasses.replace(SETTINGS, **kw)


ANTHROPIC = cfg(llm_provider="anthropic", anthropic_api_key="test-key-not-used",
                llm_model="claude-sonnet-5", verifier_model="claude-haiku-4-5",
                escalation_model="claude-opus-5", ollama_model="qwen2.5:14b",
                triage_model="qwen2.5:14b")
NO_KEY = dataclasses.replace(ANTHROPIC, anthropic_api_key="")
LOCAL = dataclasses.replace(ANTHROPIC, llm_provider="ollama")


@pytest.mark.parametrize("role", JUDGING_ROLES)
def test_a_missing_key_refuses_instead_of_going_local(role):
    """Round 1 downgraded to OLLAMA_MODEL here and printed a line.

    Decision #3 reserves mapping, verification and tie-breaks for a hosted model, and the two
    declared engines name specific checkpoints. A silent downgrade would file rows from a model
    neither engine names, bill nothing, and report success.
    """
    with pytest.raises(LLMConfigError) as e:
        get_llm(NO_KEY, role=role)
    msg = str(e.value)
    assert role in msg
    assert "ANTHROPIC_API_KEY" in msg
    assert "LLM_PROVIDER=ollama" in msg, "the message must name the explicit local route"
    assert "qwen2.5:14b" in msg, "and the model that route would use"


def test_triage_is_local_whatever_the_provider_says():
    """The cheap screen is local by design, so a missing key is not an error there."""
    for settings in (ANTHROPIC, NO_KEY, LOCAL):
        c = get_llm(settings, role="triage")
        assert type(c).__name__ == "OllamaClient"
        assert c.model == "qwen2.5:14b"       # TRIAGE_MODEL, not OLLAMA_MODEL's judging model


def test_explicit_local_needs_no_key():
    """LLM_PROVIDER=ollama is how engine B is asked for; it must work with no key set."""
    for role in JUDGING_ROLES:
        c = get_llm(dataclasses.replace(LOCAL, anthropic_api_key=""), role=role)
        assert type(c).__name__ == "OllamaClient"
        assert c.model == "qwen2.5:14b"


def test_the_model_follows_the_provider():
    """Asking for ollama must never hand Ollama an Anthropic model name."""
    c = get_llm(LOCAL, role="mapper")
    assert c.model == LOCAL.ollama_model != LOCAL.llm_model


def _anthropic_constructible() -> bool:
    """AnthropicClient builds an SDK client in __post_init__, which needs credentials present.

    Whether they are is a property of the machine, not of the seam, so the one test that
    constructs the hosted client skips where they are absent.
    """
    try:
        import anthropic
        anthropic.Anthropic()
        return True
    except Exception:
        return False


@pytest.mark.skipif(not _anthropic_constructible(),
                    reason="no Anthropic credentials on this machine")
def test_anthropic_roles_take_their_own_model_variables():
    got = {r: get_llm(ANTHROPIC, role=r).model for r in ROLES}
    assert got["mapper"] == "claude-sonnet-5"
    assert got["verifier"] == "claude-haiku-4-5"
    assert got["escalation"] == "claude-opus-5"
    assert got["triage"] == "qwen2.5:14b"      # forced local


def test_an_explicit_model_wins():
    c = get_llm(LOCAL, role="mapper", model="pinned:tag")
    assert c.model == "pinned:tag"


def test_an_unknown_provider_raises_rather_than_becoming_ollama():
    with pytest.raises(ValueError) as e:
        get_llm(cfg(llm_provider="openai"), role="mapper")
    assert "openai" in str(e.value)
    for p in PROVIDERS:
        assert p in str(e.value), "the message must list the providers that do exist"


def test_an_unknown_role_raises():
    with pytest.raises(ValueError):
        get_llm(ANTHROPIC, role="curator")


def test_triage_is_not_a_judging_role():
    assert set(JUDGING_ROLES) == set(ROLES) - {"triage"}


def test_model_for_refuses_an_unknown_provider():
    """Asked directly, as the run manifest asks it, it must not answer with the local model."""
    from config.llm.factory import _model_for
    with pytest.raises(ValueError) as e:
        _model_for(ANTHROPIC, "openai", "mapper")
    assert "openai" in str(e.value)
    assert _model_for(ANTHROPIC, "ollama", "mapper") == ANTHROPIC.ollama_model
