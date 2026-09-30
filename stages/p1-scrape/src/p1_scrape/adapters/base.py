"""PortalAdapter interface (contract §3.1).

Each adapter implements three things and nothing else:
  discover(pillars, scope)     -> [Candidate]   (from seed_laws / inventory / search)
  build_plans(candidate)       -> [FetchPlan]   (one law may need >1 fetch: html + pdf)
  extract_anchor(cand, plan, content) -> (anchor_hint, anchor_kind)   (optional, post-fetch)

Scope: 'seed' (deterministic seed_laws only) | 'relevant' (seed + vocabulary net) |
'all' (whole inventory). Pillars/vocabulary come from sources_<cc>.yaml, never hardcoded.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from ..models import Candidate, FetchPlan


class PortalAdapter(ABC):
    economy: str = ""

    @abstractmethod
    def discover(self, pillars: list[int], scope: str = "relevant", fetcher=None) -> list[Candidate]:
        ...

    @abstractmethod
    def build_plans(self, candidate: Candidate, forms: str = "both") -> list[FetchPlan]:
        """forms ∈ {pdf, html, both} — which representation(s) to retrieve."""
        ...

    def extract_anchor(
        self, candidate: Candidate, plan: FetchPlan, content: bytes
    ) -> tuple[Optional[str], Optional[str]]:
        """Post-fetch deep-link extraction from rendered HTML. Default: none."""
        return (None, None)
