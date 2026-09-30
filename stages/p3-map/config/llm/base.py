"""Contract §5.2: one structured-output interface, provider swap is a .env edit."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    calls: int = 0

    def add(self, other: "Usage") -> None:
        self.input_tokens += other.input_tokens
        self.output_tokens += other.output_tokens
        self.cache_read_tokens += other.cache_read_tokens
        self.cache_write_tokens += other.cache_write_tokens
        self.calls += other.calls


# $/MTok (input, output, cache_read, cache_write_1h) — 2026-07 price card
PRICES = {
    "claude-sonnet-5": (3.0, 15.0, 0.30, 6.0),
    "claude-haiku-4-5": (1.0, 5.0, 0.10, 2.0),
    "claude-opus-4-8": (5.0, 25.0, 0.50, 10.0),
}


def usd(model: str, u: Usage) -> float:
    p = PRICES.get(model)
    if p is None:
        return 0.0
    return (u.input_tokens * p[0] + u.output_tokens * p[1]
            + u.cache_read_tokens * p[2] + u.cache_write_tokens * p[3]) / 1e6


@dataclass
class LLMClient(ABC):
    model: str = ""
    usage: Usage = field(default_factory=Usage)

    @abstractmethod
    def complete(self, prompt: str, schema: dict, *, system: str | None = None,
                 max_tokens: int = 2048, cache_system: bool = False) -> dict:
        """Return a dict conforming to `schema` (JSON Schema). Raises on failure."""
