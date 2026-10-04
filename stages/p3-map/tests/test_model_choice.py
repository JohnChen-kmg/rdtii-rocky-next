"""Tests for the model choice added 2026-10-04: a role's own engine, the declared models and their
price cards, the OpenAI-compatible client, the Claude client's auto-tool mode, and the caps scale.

Run from stages/p3-map:
    python -m pytest tests/test_model_choice.py -q

Nothing here talks to a provider: every HTTP call is replaced. What these tests hold is that the
default path is untouched (no role engine, the three measured Claude models, scale 1.0) and that
the new path sends what each provider's reference asks for.
"""
from __future__ import annotations

import dataclasses
import json

import httpx
import pytest

from config.llm import base, engines
from config.llm.factory import LLMConfigError, get_llm
from config.llm.openai_compat_client import OpenAICompatClient, ProviderError, parse_json, read_usage
from config.settings import SETTINGS

ANTHROPIC = dataclasses.replace(
    SETTINGS, llm_provider="anthropic", anthropic_api_key="test-key-not-used",
    llm_model="claude-sonnet-5", verifier_model="claude-haiku-4-5",
    escalation_model="claude-opus-4-8", ollama_model="llama3.1:8b", triage_model="qwen2.5:14b")
SCHEMA = {"type": "object", "properties": {"keep": {"type": "boolean"}}, "required": ["keep"]}
KEYS = ("DEEPSEEK_API_KEY", "MOONSHOT_API_KEY", "OPENAI_API_KEY")


@pytest.fixture(autouse=True)
def _clean(monkeypatch):
    monkeypatch.delenv(engines.ENGINE_ENV, raising=False)
    monkeypatch.delenv(engines.ENGINES_FILE_ENV, raising=False)
    for var in list(engines.ROLE_ENV.values()) + list(engines.ROLE_ENGINE_ENV.values()) + list(KEYS):
        monkeypatch.delenv(var, raising=False)


class Reply:
    def __init__(self, status=200, content='{"keep": true}', usage=None, finish="stop"):
        self.status_code = status
        self._doc = {"choices": [{"message": {"content": content}, "finish_reason": finish}],
                     "usage": usage or {"prompt_tokens": 100, "completion_tokens": 7}}
        self.text = json.dumps(self._doc) if status == 200 else content

    def json(self):
        return self._doc


def capture(monkeypatch, replies):
    """Replace httpx.post; returns the list the sent requests are appended to."""
    sent = []
    queue = list(replies)

    def post(url, json=None, headers=None, timeout=None):
        sent.append({"url": url, "body": json, "headers": headers})
        r = queue.pop(0)
        if isinstance(r, Exception):
            raise r
        return r
    monkeypatch.setattr(httpx, "post", post)
    monkeypatch.setattr("config.llm.openai_compat_client.time.sleep", lambda s: None)
    return sent


# ---- the declaration -------------------------------------------------------------------------

def test_the_measured_cards_in_the_declaration_are_the_stages_own():
    """Two places name a price for the three measured models; they must never drift apart."""
    cards = engines.price_cards()
    for model, card in base.PRICES.items():
        assert cards[model] == card, model


def test_every_declared_model_has_a_card_and_says_whether_it_was_measured():
    for eid in engines.ids():
        e = engines.get(eid)
        assert e.models, f"{eid} lists no models"
        for m in e.models:
            assert len(m["price"]) == 4, m["id"]
            assert isinstance(m["measured"], bool), m["id"]
            if not e.measured:
                assert m["measured"] is False, f"{m['id']}: its engine is not measured"
        for role in ("mapper", "verifier", "escalation"):
            assert e.spec(e.roles[role]), f"{eid}: the {role} model is not in its own list"


def test_a_declared_model_is_metered_and_an_unknown_one_is_not():
    u = base.Usage(input_tokens=1_000_000, output_tokens=1_000_000)
    assert base.usd("claude-sonnet-5", u) == pytest.approx(18.0), "the stage's own card, unchanged"
    assert base.usd("deepseek-flash", u) == pytest.approx(1.5)
    assert base.usd("no-such-model", u) == 0.0
    assert base.price_card("no-such-model") is None


def test_an_alternative_declaration_can_be_named(monkeypatch, tmp_path):
    doc = json.loads(engines.CONFIG_PATH.read_text(encoding="utf-8"))
    doc["engines"]["L"] = {**doc["engines"]["C"], "id": "L", "label": "a local test server",
                          "base_url": "http://localhost:11434/v1", "key_env": None}
    alt = tmp_path / "engines.json"
    alt.write_text(json.dumps(doc), encoding="utf-8")
    monkeypatch.setenv(engines.ENGINES_FILE_ENV, str(alt))
    assert "L" in engines.ids()
    monkeypatch.delenv(engines.ENGINES_FILE_ENV)
    assert "L" not in engines.ids()


# ---- a role's own engine ---------------------------------------------------------------------

def test_a_role_follows_the_run_engine_unless_it_is_given_its_own(monkeypatch):
    monkeypatch.setenv(engines.ENGINE_ENV, "B")
    assert engines.selected(role="verifier").id == "B"
    monkeypatch.setenv("RDTII_ENGINE_VERIFIER", "C")
    assert engines.selected(role="verifier").id == "C"
    assert engines.selected(role="mapper").id == "B", "only the role that was set"
    assert engines.selected().id == "B", "and the run's engine is still the run's engine"


def test_the_factory_builds_each_role_on_its_own_engine(monkeypatch):
    monkeypatch.setenv(engines.ENGINE_ENV, "B")
    monkeypatch.setenv("RDTII_ENGINE_VERIFIER", "C")
    monkeypatch.setenv("VERIFIER_MODEL", "deepseek-v4-pro")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key-not-used")
    mapper, verifier = get_llm(ANTHROPIC, role="mapper"), get_llm(ANTHROPIC, role="verifier")
    assert type(mapper).__name__ == "OllamaClient" and mapper.model == "qwen2.5:14b"
    assert type(verifier).__name__ == "OpenAICompatClient"
    assert verifier.model == "deepseek-v4-pro", "the model variable still wins over the engine's"
    assert verifier.base_url == "https://api.deepseek.com"
    assert verifier.key_env == "DEEPSEEK_API_KEY"
    assert get_llm(ANTHROPIC, role="triage").model == "qwen2.5:14b", "triage stays local"


@pytest.mark.parametrize("eid,key_env", [("C", "DEEPSEEK_API_KEY"), ("D", "MOONSHOT_API_KEY"),
                                         ("E", "OPENAI_API_KEY")])
def test_a_hosted_engine_refuses_without_its_own_key(monkeypatch, eid, key_env):
    """The Claude key is set and must not stand in for another provider's."""
    monkeypatch.setenv(engines.ENGINE_ENV, eid)
    with pytest.raises(LLMConfigError) as e:
        get_llm(ANTHROPIC, role="mapper")
    assert key_env in str(e.value)
    monkeypatch.setenv(key_env, "test-key-not-used")
    assert type(get_llm(ANTHROPIC, role="mapper")).__name__ == "OpenAICompatClient"


def test_the_compatible_provider_cannot_be_asked_for_without_an_engine():
    with pytest.raises(LLMConfigError) as e:
        get_llm(dataclasses.replace(ANTHROPIC, llm_provider="openai_compat"), role="mapper")
    assert "RDTII_ENGINE" in str(e.value)


def test_the_manifest_records_each_roles_engine(monkeypatch, tmp_path):
    from config import manifest
    monkeypatch.setenv(engines.ENGINE_ENV, "B")
    monkeypatch.setenv("RDTII_ENGINE_VERIFIER", "C")
    monkeypatch.setattr("config.settings.SETTINGS",
                        dataclasses.replace(SETTINGS, out_dir=tmp_path / "out"))
    roles = manifest._engine()["roles"]
    assert roles["mapper"] == {"provider": "ollama", "model": "qwen2.5:14b"}
    assert roles["verifier"] == {"provider": "openai_compat", "model": "deepseek-flash", "engine_id": "C"}
    assert roles["triage"]["provider"] == "ollama"


# ---- the OpenAI-compatible client ------------------------------------------------------------

def client(eid: str, model: str, monkeypatch) -> OpenAICompatClient:
    e = engines.get(eid)
    monkeypatch.setenv(e.key_env, "sk-secret-value")
    return OpenAICompatClient(model=model, base_url=e.base_url, key_env=e.key_env,
                              request=e.request_for(model))


def test_deepseek_is_sent_what_its_reference_asks_for(monkeypatch):
    sent = capture(monkeypatch, [Reply(usage={"prompt_tokens": 100, "completion_tokens": 7,
                                              "prompt_cache_hit_tokens": 80, "prompt_cache_miss_tokens": 20})])
    c = client("C", "deepseek-flash", monkeypatch)
    out = c.complete("the provision", SCHEMA, system="the codebook", max_tokens=400, cache_system=True)
    assert out == {"keep": True}
    req = sent[0]
    assert req["url"] == "https://api.deepseek.com/chat/completions"
    assert req["headers"]["Authorization"] == "Bearer sk-secret-value"
    body = req["body"]
    assert body["model"] == "deepseek-flash" and body["max_tokens"] == 400 and body["temperature"] == 0
    assert body["thinking"] == {"type": "disabled"}
    assert body["response_format"] == {"type": "json_object"}
    assert body["messages"][0] == {"role": "system", "content": "the codebook"}, "the prefix is sent untouched"
    assert body["messages"][1]["content"].startswith("the provision")
    assert json.dumps(SCHEMA) in body["messages"][1]["content"]
    assert (c.usage.input_tokens, c.usage.cache_read_tokens, c.usage.output_tokens, c.usage.calls) == (20, 80, 7, 1)


def test_a_reasoning_model_gets_room_to_think_and_no_temperature(monkeypatch):
    sent = capture(monkeypatch, [Reply(), Reply()])
    client("E", "gpt-6.1-sol", monkeypatch).complete("p", SCHEMA, max_tokens=100)
    body = sent[0]["body"]
    assert sent[0]["url"] == "https://api.openai.com/v1/chat/completions"
    assert body["max_completion_tokens"] == 100 + 4096 and "max_tokens" not in body
    assert "temperature" not in body
    assert body["reasoning_effort"] == "low"
    client("D", "kimi-k2.6", monkeypatch).complete("p", SCHEMA, max_tokens=100)
    body = sent[1]["body"]
    assert sent[1]["url"] == "https://api.moonshot.ai/v1/chat/completions"
    assert body["max_completion_tokens"] == 100 and body["thinking"] == {"type": "disabled"}


def test_the_cached_part_is_read_under_each_providers_name():
    assert read_usage({"prompt_tokens": 100, "completion_tokens": 5,
                       "prompt_tokens_details": {"cached_tokens": 60}}).cache_read_tokens == 60
    kimi = read_usage({"prompt_tokens": 100, "completion_tokens": 5, "cached_tokens": 30})
    assert (kimi.input_tokens, kimi.cache_read_tokens) == (70, 30)
    plain = read_usage({"prompt_tokens": 100, "completion_tokens": 5})
    assert (plain.input_tokens, plain.cache_read_tokens) == (100, 0)
    assert read_usage(None).calls == 1


def test_a_busy_provider_is_tried_again_and_a_refusal_is_not(monkeypatch):
    sent = capture(monkeypatch, [Reply(429, "slow down"), httpx.ConnectError("no route"), Reply()])
    assert client("C", "deepseek-flash", monkeypatch).complete("p", SCHEMA) == {"keep": True}
    assert len(sent) == 3
    sent = capture(monkeypatch, [Reply(401, "bad key sk-secret-value")])
    with pytest.raises(ProviderError) as e:
        client("C", "deepseek-flash", monkeypatch).complete("p", SCHEMA)
    assert len(sent) == 1, "a refusal is final"
    assert "401" in str(e.value)
    assert "sk-secret-value" not in str(e.value), "the key never reaches a message"


def test_a_reply_that_is_not_the_object_asked_for_raises(monkeypatch):
    assert parse_json('Here it is:\n```json\n{"keep": false}\n```') == {"keep": False}
    for bad in ("no json here", "[1, 2]", "{broken"):
        with pytest.raises(ProviderError):
            parse_json(bad)
    capture(monkeypatch, [Reply(content="", finish="length")])
    with pytest.raises(ProviderError) as e:
        client("D", "kimi-k3", monkeypatch).complete("p", SCHEMA)
    assert "max_tokens_extra" in str(e.value)


# ---- the Claude client -----------------------------------------------------------------------

class _Block:
    def __init__(self, type_, **kw):
        self.type = type_
        self.__dict__.update(kw)


class _Messages:
    def __init__(self, content):
        self.sent, self._content = [], content

    def create(self, **kwargs):
        self.sent.append(kwargs)
        usage = _Block("usage", input_tokens=10, output_tokens=5)
        return _Block("message", content=self._content, usage=usage)


def claude(model: str, content, monkeypatch):
    import anthropic
    from config.llm.anthropic_client import AnthropicClient
    messages = _Messages(content)
    monkeypatch.setattr(anthropic, "Anthropic", lambda: _Block("client", messages=messages))
    return AnthropicClient(model=model), messages


@pytest.mark.parametrize("model", sorted(base.PRICES))
def test_the_measured_claude_models_are_sent_the_request_they_always_were(model, monkeypatch):
    c, messages = claude(model, [_Block("tool_use", input={"keep": True})], monkeypatch)
    assert c.complete("the provision", SCHEMA, system="the codebook", max_tokens=400,
                      cache_system=True) == {"keep": True}
    assert messages.sent[0] == {
        "model": model, "max_tokens": 400,
        "messages": [{"role": "user", "content": "the provision"}],
        "tools": [{"name": "emit_verdict", "description": "Emit the structured verdict.",
                   "input_schema": SCHEMA}],
        "tool_choice": {"type": "tool", "name": "emit_verdict"},
        "system": [{"type": "text", "text": "the codebook",
                    "cache_control": {"type": "ephemeral", "ttl": "1h"}}],
    }


def test_a_model_that_refuses_a_forced_tool_is_asked_on_auto(monkeypatch):
    c, messages = claude("claude-sonnet-5-5", [_Block("thinking"), _Block("tool_use", input={"keep": False})],
                         monkeypatch)
    assert c.complete("the provision", SCHEMA, max_tokens=400) == {"keep": False}
    sent = messages.sent[0]
    assert sent["tool_choice"] == {"type": "auto"}
    assert sent["max_tokens"] == 400 + 4096
    assert sent["messages"][0]["content"].startswith("the provision")
    assert "emit_verdict" in sent["messages"][0]["content"]
    # answered in text instead of calling the tool: the object in the text is still the verdict
    c, _ = claude("claude-opus-5-5", [_Block("text", text='{"keep": true}')], monkeypatch)
    assert c.complete("p", SCHEMA) == {"keep": True}


# ---- the caps scale --------------------------------------------------------------------------

def test_the_caps_scale_is_round_one_at_one_and_never_reaches_zero():
    from src.p3map import select
    assert SETTINGS.caps_scale == 1.0, "unset, the caps are Round 1's"
    for ind, cap in select.CAPS.items():
        assert select.scaled_cap(ind) == cap
        assert select.scaled_cap(ind, 0.5) == round(cap * 0.5)
        assert select.scaled_cap(ind, 2.0) == cap * 2
        assert select.scaled_cap(ind, 0.0001) == 1
