"""Anthropic (Claude) structured-output client via forced tool use."""

from __future__ import annotations

import json
from typing import Any

from config.llm.base import LLMClient


class AnthropicClient(LLMClient):
    def __init__(self, api_key: str, model: str):
        import anthropic  # imported lazily so the no-key path never needs it

        self._client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self._input_tokens = 0
        self._output_tokens = 0

    def complete(self, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        response = self._client.messages.create(
            model=self.model,
            max_tokens=2048,
            tools=[
                {
                    "name": "emit_result",
                    "description": "Return the structured extraction result.",
                    "input_schema": schema,
                }
            ],
            tool_choice={"type": "tool", "name": "emit_result"},
            messages=[{"role": "user", "content": prompt}],
        )
        self._input_tokens += response.usage.input_tokens
        self._output_tokens += response.usage.output_tokens
        for block in response.content:
            if block.type == "tool_use":
                return dict(block.input)
        raise ValueError(f"Anthropic returned no tool_use block: {json.dumps(response.model_dump(), default=str)[:500]}")

    def usage_totals(self) -> dict[str, int]:
        return {"input_tokens": self._input_tokens, "output_tokens": self._output_tokens}
