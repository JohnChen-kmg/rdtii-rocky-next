"""Anthropic backend: schema-forced via a required tool call (SDK 0.116).

Decision #6: the instrument prefix rides as a cached system block
(cache_control ephemeral, ttl 1h) — byte-stable, no timestamps.

Since 2026-10-04 a model the engine declaration marks `tool_choice: auto` is asked differently:
per the provider's documentation the 5.5 models and Fable 5.1 refuse a forced tool call, so the
tool is offered on `auto`, the prompt says to answer by calling it, and the reply budget grows by
the model's `max_tokens_extra` because those models always think. NOT RUN: no call has been made
to those models from this pipeline. Every other model, the three measured ones included, is sent
exactly the request it was sent before.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

import anthropic

from config.llm.base import LLMClient, Usage

AUTO_TOOL_INSTRUCTION = "\n\nAnswer only by calling the emit_verdict tool."


def _declared(model: str) -> dict:
    """The model's entry in the engine declaration; {} when it has none or the file is unreadable."""
    try:
        from config.llm import engines
        return engines.spec_of(model)
    except Exception:
        return {}


@dataclass
class AnthropicClient(LLMClient):
    def __post_init__(self) -> None:
        self._client = anthropic.Anthropic()
        spec = _declared(self.model)
        self._auto_tool = spec.get("tool_choice") == "auto"
        self._extra_tokens = int(spec.get("max_tokens_extra") or 0) if self._auto_tool else 0

    def complete(self, prompt: str, schema: dict, *, system: str | None = None,
                 max_tokens: int = 2048, cache_system: bool = False) -> dict:
        kwargs: dict = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
            "tools": [{
                "name": "emit_verdict",
                "description": "Emit the structured verdict.",
                "input_schema": schema,
            }],
            "tool_choice": {"type": "tool", "name": "emit_verdict"},
        }
        if self._auto_tool:
            kwargs["tool_choice"] = {"type": "auto"}
            kwargs["max_tokens"] = max_tokens + self._extra_tokens
            kwargs["messages"] = [{"role": "user", "content": prompt + AUTO_TOOL_INSTRUCTION}]
        if system:
            block: dict = {"type": "text", "text": system}
            if cache_system:
                block["cache_control"] = {"type": "ephemeral", "ttl": "1h"}
            kwargs["system"] = [block]

        resp = self._client.messages.create(**kwargs)
        u = resp.usage
        self.usage.add(Usage(
            input_tokens=u.input_tokens, output_tokens=u.output_tokens,
            cache_read_tokens=getattr(u, "cache_read_input_tokens", 0) or 0,
            cache_write_tokens=getattr(u, "cache_creation_input_tokens", 0) or 0,
            calls=1))
        for blk in resp.content:
            if blk.type == "tool_use":
                return blk.input
        if self._auto_tool:
            # on `auto` the model may answer in text; a JSON object there is still the verdict
            from config.llm.openai_compat_client import parse_json
            text = "".join(getattr(blk, "text", "") or "" for blk in resp.content
                           if blk.type == "text")
            if text.strip():
                return parse_json(text)
        raise ValueError(f"no tool_use block in response: {json.dumps(resp.model_dump())[:200]}")
