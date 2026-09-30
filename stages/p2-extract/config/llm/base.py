"""LLMClient interface (contract section 5.2).

One structured-output signature - complete(prompt, schema) -> dict - so that
swapping Claude <-> Ollama is a .env edit, never a rewrite. Callers must treat
the returned dict as untrusted model output: quoted bytes are NEVER taken from
it (grounding rule, contract section 3.2).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class LLMClient(ABC):
    """Structured-output LLM client. Implementations pin their model id."""

    model: str

    @abstractmethod
    def complete(self, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        """Return a dict conforming to `schema` (JSON Schema object)."""

    def usage_totals(self) -> dict[str, int]:
        """Cumulative token usage {input_tokens, output_tokens} for cost_report."""
        return {"input_tokens": 0, "output_tokens": 0}
