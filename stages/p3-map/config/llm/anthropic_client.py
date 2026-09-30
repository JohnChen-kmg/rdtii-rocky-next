"""Anthropic backend: schema-forced via a required tool call (SDK 0.116).

Decision #6: the instrument prefix rides as a cached system block
(cache_control ephemeral, ttl 1h) — byte-stable, no timestamps.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

import anthropic

from config.llm.base import LLMClient, Usage


@dataclass
class AnthropicClient(LLMClient):
    def __post_init__(self) -> None:
        self._client = anthropic.Anthropic()

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
        raise ValueError(f"no tool_use block in response: {json.dumps(resp.model_dump())[:200]}")
