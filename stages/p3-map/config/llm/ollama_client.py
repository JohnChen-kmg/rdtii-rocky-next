"""Ollama backend: same interface, JSON-schema-constrained decoding (format=schema).

Two things this client must not do quietly, both added 2026-09-27.

`num_ctx`. Ollama's own default context is 2,048 tokens and it truncates from the FRONT of
the prompt — exactly where the cached codebook prefix sits. Measured on one real provision:
the call read 2,050 of 6,792 tokens, returned schema-valid JSON, and fired three mutually
exclusive indicators (a ban, a storage requirement and a conditional regime) while its own
trap check said a conditional path existed. It contradicted itself because the trap
descriptions travel in the tool schema, which is not truncated, and the codebook does not.

So the window is a setting (OLLAMA_NUM_CTX, default 16,384), and a call that would not fit
raises rather than returning a confident answer built on a cut prompt. Truncation is
detected after the fact from Ollama's own `prompt_eval_count`, which is exact. The character
estimate before the call only fails fast, and is deliberately optimistic because token
density varies by script: measured 0.21 tokens per character for English, 1.24 for Lao.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

import httpx

from config.llm.base import LLMClient, Usage
from config.settings import SETTINGS

# Ollama reports prompt_eval_count == num_ctx when it has truncated; allow a small margin
# for the tokens the chat template adds around the prompt.
_TRUNCATION_MARGIN = 16


class ContextOverflow(RuntimeError):
    """The prompt does not fit the window, so any answer would rest on a truncated prompt."""


@dataclass
class OllamaClient(LLMClient):
    def complete(self, prompt: str, schema: dict, *, system: str | None = None,
                 max_tokens: int = 2048, cache_system: bool = False) -> dict:
        full = (system + "\n\n" if system else "") + prompt
        num_ctx = SETTINGS.ollama_num_ctx

        optimistic = len(full) // 4          # English density; every other script is worse
        if optimistic + max_tokens > num_ctx:
            raise ContextOverflow(
                f"prompt is at least ~{optimistic:,} tokens plus {max_tokens:,} reserved for "
                f"the reply, against num_ctx={num_ctx:,}. Raise OLLAMA_NUM_CTX or shorten the "
                f"prompt; letting Ollama truncate drops the codebook."
            )

        r = httpx.post(f"{SETTINGS.ollama_host}/api/generate", json={
            "model": self.model, "prompt": full, "stream": False,
            "format": schema,  # ollama >=0.5 constrained decoding
            "options": {"temperature": 0.0, "num_predict": max_tokens, "num_ctx": num_ctx},
        }, timeout=1800)
        r.raise_for_status()
        body = r.json()

        read = int(body.get("prompt_eval_count", 0) or 0)
        if read >= num_ctx - _TRUNCATION_MARGIN:
            raise ContextOverflow(
                f"Ollama read {read:,} prompt tokens with num_ctx={num_ctx:,}, so the prompt "
                f"was truncated from the front and the codebook is missing from it. Raise "
                f"OLLAMA_NUM_CTX."
            )

        self.usage.add(Usage(
            input_tokens=read,
            output_tokens=body.get("eval_count", 0) or 0, calls=1))
        return json.loads(body["response"])
