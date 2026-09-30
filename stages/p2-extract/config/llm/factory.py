"""get_llm(settings) -> LLMClient  (dispatch on LLM_PROVIDER, contract section 5.2)."""

from __future__ import annotations

import logging

from config.llm.base import LLMClient
from config.settings import Settings

log = logging.getLogger("config.llm")


def get_llm(settings: Settings, language: str | None = None,
            model: str | None = None) -> LLMClient:
    """The tagging client for one document.

    `language` is the document's own, read from the crawler (D3), and `config/llm/tagmap.py`
    maps it to a model - because the tag prompt asks the model to read a snippet in its
    SOURCE language. A single global `LLM_MODEL` judged Lao provisions with a model measured
    to be the weaker Lao reader; `LLM_MODEL` stays as an explicit override, never the silent
    default. `model` overrides both, for a one-off comparison run.
    """
    provider = settings.llm_provider
    if model is None and language is not None:
        from config.llm import tagmap

        model, why = tagmap.model_and_reason(language)
        log.info("tagging model for %s: %s (%s)", language, model, why)
    model = model or settings.llm_model
    if provider == "anthropic" and not settings.anthropic_api_key:
        # Defense in depth: load_settings() already downgrades, but a caller may
        # construct Settings directly.
        log.warning("ANTHROPIC_API_KEY empty - auto-selecting ollama (contract section 5.2)")
        provider = "ollama"

    if provider == "anthropic":
        from config.llm.anthropic_client import AnthropicClient

        log.info("LLM backend: anthropic / %s", model)
        return AnthropicClient(api_key=settings.anthropic_api_key, model=model)

    if provider == "ollama":
        from config.llm.ollama_client import OllamaClient

        log.info("LLM backend: ollama / %s @ %s", model, settings.ollama_host)
        return OllamaClient(host=settings.ollama_host, model=model)

    raise ValueError(f"Unknown LLM_PROVIDER: {provider!r} (expected 'anthropic' or 'ollama')")
