"""Load the per-economy crawl-target registry (sources_<cc>.yaml).

Prefers the vendored pinned copy in contracts/instrument/, falling back to the
working instrument/ dir. Pillars/indicators/vocabulary are DATA here, never
hardcoded — expanding to other pillars = editing the YAML, not the crawler.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

_REPO = Path(__file__).resolve().parents[2]
_SEARCH = [_REPO / "contracts" / "instrument", _REPO / "instrument"]


@lru_cache(maxsize=8)
def load_sources(economy: str) -> dict[str, Any]:
    cc = economy.lower()
    for base in _SEARCH:
        p = base / f"sources_{cc}.yaml"
        if p.exists():
            return yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    raise FileNotFoundError(
        f"sources_{cc}.yaml not found in {[str(b) for b in _SEARCH]}"
    )


def indicator_pillar(indicator_id: str) -> int | None:
    """'P6-I4' -> 6, 'P7-I2' -> 7."""
    s = indicator_id.upper().lstrip("P")
    try:
        return int(s.split("-", 1)[0])
    except (ValueError, IndexError):
        return None


def pillar_hint_for(indicators: list[str]) -> str | None:
    pillars = {indicator_pillar(i) for i in indicators}
    pillars.discard(None)
    has6, has7 = 6 in pillars, 7 in pillars
    if has6 and has7:
        return "both"
    if has6:
        return "P6"
    if has7:
        return "P7"
    return None


def all_query_terms(cfg: dict[str, Any]) -> list[str]:
    """Flatten every seed_queries phrase across all indicator buckets (anchor vocab)."""
    terms: list[str] = []
    for phrases in (cfg.get("seed_queries") or {}).values():
        if isinstance(phrases, list):
            terms.extend(str(p) for p in phrases)
    return terms
