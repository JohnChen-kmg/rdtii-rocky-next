"""get_llm(settings, role) — dispatch on LLM_PROVIDER. Local is a choice, never an accident.

The model name follows the resolved provider. That is the point of the seam: asking for
provider "ollama" must not hand Ollama an Anthropic model name. Before 2026-09-27 the role
map was read once, from the Anthropic variables, so `LLM_PROVIDER=ollama` alone built
`OllamaClient(model='claude-sonnet-5')` and every call returned HTTP 404 — while
OLLAMA_MODEL, the variable that looks like it selects the local model, was consulted only
in the empty-key fallback.

Which variable supplies the model, per provider and role:

    anthropic   mapper LLM_MODEL · verifier VERIFIER_MODEL · escalation ESCALATION_MODEL
    ollama      mapper/verifier/escalation OLLAMA_MODEL · triage TRIAGE_MODEL

An explicit `model=` argument always wins (the A/B harnesses use it to pin two models of
one provider). An unrecognised provider raises instead of quietly becoming Ollama, and so does
a missing Anthropic key for a judging role — see get_llm.

RDTII_ENGINE selects a declared engine (config/llm/engines.json) and then supplies the provider
and the per-role model in place of LLM_PROVIDER and the four model variables; an explicitly set
model variable still wins over the engine's choice. With RDTII_ENGINE unset nothing changes, so
a run configured before engines existed resolves exactly as it did then.
"""
from __future__ import annotations

import os

from config.llm import engines
from config.llm.base import LLMClient
from config.settings import Settings

PROVIDERS = ("anthropic", "ollama", "openai_compat")
# Reached only through a declared engine (its base URL, key variable and request shape live in
# engines.json): there is no pre-engine variable that names a model for it.
ENGINE_ONLY = ("openai_compat",)
ROLES = ("mapper", "verifier", "escalation", "triage")
# Roles decision #3 reserves for a hosted model: a local model never maps, verifies or breaks
# a tie. "triage" is deliberately absent — that stage is local-first and costs nothing.
JUDGING_ROLES = ("mapper", "verifier", "escalation")


class LLMConfigError(RuntimeError):
    """The engine a role resolved to is not one this role is allowed to use."""


def _model_for(settings: Settings, provider: str, role: str) -> str:
    # get_llm validates the provider before calling this, but the run manifest asks the same
    # question directly: without this line an unknown provider silently answers with the OLLAMA
    # model, and the manifest would record a local model for a run that never used one.
    if provider not in PROVIDERS:
        raise ValueError(f"unknown provider {provider!r}; expected one of {', '.join(PROVIDERS)}")
    if provider in ENGINE_ONLY:
        raise ValueError(f"provider {provider!r} has no model variables of its own; it is reached "
                         f"through a declared engine (RDTII_ENGINE)")
    if provider == "anthropic":
        return {
            "mapper": settings.llm_model,
            "verifier": settings.verifier_model,
            "escalation": settings.escalation_model,
            "triage": settings.triage_model,
        }[role]
    # local: one model for the judging roles, its own for the cheap screen
    return settings.triage_model if role == "triage" else settings.ollama_model


def get_llm(settings: Settings, role: str = "mapper", model: str | None = None) -> LLMClient:
    """role: mapper | verifier | escalation | triage. Explicit `model` overrides."""
    if role not in ROLES:
        raise ValueError(f"unknown role {role!r}; expected one of {', '.join(ROLES)}")

    engine = engines.selected(role=role)     # the role's own engine first, then RDTII_ENGINE
    requested = (engine.provider if engine else (settings.llm_provider or "")).strip().lower()
    if requested not in PROVIDERS:
        raise ValueError(
            f"unknown LLM_PROVIDER {settings.llm_provider!r}; expected one of "
            f"{', '.join(PROVIDERS)}. A third provider needs a branch here and a price "
            f"entry before it can be used (finale plan step 2A)."
        )

    provider = requested
    if role == "triage":
        provider = "ollama"  # decision #3: local never maps/verifies; triage is local-first
    if provider in ENGINE_ONLY:
        if engine is None:
            raise LLMConfigError(
                f"LLM_PROVIDER={requested!r} needs a declared engine: set RDTII_ENGINE to one of "
                f"{', '.join(engines.ids())} (engines.json carries the address and the key variable).")
        if not engine.base_url:
            raise LLMConfigError(f"engine {engine.id} ({engine.label}) declares no base_url")
        if engine.key_env and not os.environ.get(engine.key_env, "").strip():
            # the same refusal as for Claude below, for the same reason: no silent downgrade
            raise LLMConfigError(
                f"role {role!r} resolves to engine {engine.id} ({engine.label}) but "
                f"{engine.key_env} is empty. Set the key, or give the role another engine. "
                f"Refusing to downgrade {role} to a local model silently.")
        resolved = model or engine.model_for(role)
        from config.llm.openai_compat_client import OpenAICompatClient
        return OpenAICompatClient(model=resolved, base_url=engine.base_url,
                                  key_env=engine.key_env or "", request=engine.request_for(resolved))
    if (provider == "anthropic" and role in JUDGING_ROLES
            and not settings.anthropic_api_key.strip()):
        # Round 1 fell back to Ollama here and printed a line. For the finale that is a
        # correctness hole, not a convenience: an unset key would hand MAPPING or VERIFICATION
        # to OLLAMA_MODEL, which decision #3 forbids and neither declared engine names, and the
        # run would file rows and report success having billed nothing. Asking for the local
        # engine is one variable away, so refuse instead.
        route = (f"RDTII_ENGINE={engines.default_id()!r} is engine "
                 f"{engines.get(engines.default_id()).label!r}; select the open-weights engine "
                 f"instead" if engine is not None else
                 f"ask for the local engine explicitly with LLM_PROVIDER=ollama (which would use "
                 f"OLLAMA_MODEL={settings.ollama_model!r})")
        raise LLMConfigError(
            f"role {role!r} resolves to provider 'anthropic' but ANTHROPIC_API_KEY is empty. "
            f"Set the key, or {route}. Refusing to downgrade {role} to a local model silently."
        )
    if provider == "anthropic" and not settings.anthropic_api_key.strip():
        provider = "ollama"   # a non-judging role: local is that role's design anyway

    if engine is not None and provider == engine.provider:
        # the engine's role model, unless a model variable was set explicitly
        resolved = model or engine.model_for(role)
    else:
        # no engine named, or a role forced off the engine's provider (triage)
        resolved = model or _model_for(settings, provider, role)

    # A stale Anthropic name left in LLM_MODEL is the common way to get a local run wrong.
    if (engine is None and provider == "ollama" and model is None and requested == "ollama"
            and role != "triage" and settings.llm_model != resolved):
        print(f"[factory] provider=ollama, role={role}: using OLLAMA_MODEL={resolved!r}. "
              f"LLM_MODEL={settings.llm_model!r} is the Anthropic variable and is ignored.")

    if provider == "anthropic":
        from config.llm.anthropic_client import AnthropicClient
        return AnthropicClient(model=resolved)
    from config.llm.ollama_client import OllamaClient
    return OllamaClient(model=resolved)
