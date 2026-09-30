"""Indicator-as-query construction (PLAN §3.1) from the vendored instrument.

Each indicator becomes one query document: name + definition_text + keywords
+ up to two exemplar impact snippets. Positive signal only — negative_signals
belong to the mapper's trap checks, not retrieval.
"""
from __future__ import annotations

from config.instrument import load as load_instrument
from config.settings import INDICATORS


def build_queries() -> dict[str, str]:
    queries: dict[str, str] = {}
    ins = load_instrument()
    for ind in INDICATORS:
        sig = ins.signature(ind)
        parts = [
            sig.get("name", ""),
            sig.get("definition_text", ""),
            " ".join(sig.get("keywords", [])),
        ]
        for ex in (sig.get("exemplars") or [])[:2]:
            impact = (ex.get("impact") or "")[:400]
            if impact:
                parts.append(impact)
        queries[ind] = "\n".join(p for p in parts if p)
    return queries


if __name__ == "__main__":
    for ind, q in build_queries().items():
        print(f"--- {ind}: {len(q)} chars, head: {q[:90]!r}")
