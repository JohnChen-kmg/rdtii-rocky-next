"""Ollama (open-weight, local, CPU-viable) structured-output client.

Uses Ollama's native structured-output support: passing a JSON Schema as
`format` constrains decoding to schema-valid JSON. No few-shot examples are
used - verified to DEGRADE small-model classification (kickoff decision #6).
"""

from __future__ import annotations

import json
from typing import Any

from config.llm.base import LLMClient


class OllamaClient(LLMClient):
    def __init__(self, host: str, model: str):
        import ollama  # lazy import

        self._client = ollama.Client(host=host)
        self.model = model
        self._input_tokens = 0
        self._output_tokens = 0

    def complete(self, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        response = self._client.chat(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            format=schema,
            options={"temperature": 0},
        )
        self._input_tokens += response.get("prompt_eval_count") or 0
        self._output_tokens += response.get("eval_count") or 0
        return json.loads(response["message"]["content"])

    def usage_totals(self) -> dict[str, int]:
        return {"input_tokens": self._input_tokens, "output_tokens": self._output_tokens}


def model_is_pulled(host: str, model: str) -> bool:
    """Preflight helper (PLAN.md section 2.8a): is `model` actually pulled locally?

    Only ever touches the localhost Ollama endpoint - never the internet
    (offline non-goal, contract section 2.1).
    """
    import ollama

    try:
        listed = ollama.Client(host=host).list()
    except Exception:
        return False
    names = {m.get("model") or m.get("name", "") for m in listed.get("models", [])}
    # "qwen2.5:14b" matches itself; a bare "qwen2.5" matches "qwen2.5:latest"
    return any(n == model or n.split(":")[0] == model for n in names)
