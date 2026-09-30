"""Which listing titles are relevant: the registry's title rule, and Round 1's search-term phrases.

The title rule (`title_rule:` in sources.yaml) is data derived from the instrument's pillar 6 and 7
indicator definitions, never from the gold set (POLICY.md section 4). It decides where the costly per-act
work goes (timelines, subsidiary legislation) and orders the crawl. It never sets indicator or pillar
hints: the crawler does not map indicators (POLICY.md section 1).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Optional

from ...sources import all_query_terms

_STOP = {"of", "the", "and", "a", "an", "for", "to", "in", "on", "or", "by", "with", "any", "act"}


@dataclass(frozen=True)
class RuleGroup:
    id: str
    tier: str                      # core | sectoral
    indicators: tuple[str, ...]    # labels only, for people reading the link file
    patterns: tuple[re.Pattern, ...]


class TitleRule:
    """Keyword groups matched on a normalised English title (the Malay title when there is no English one)."""

    def __init__(self, groups: list[RuleGroup], exclusions: list[tuple[str, re.Pattern]], rule_id: str):
        self.groups, self.exclusions, self.rule_id = groups, exclusions, rule_id

    @classmethod
    def from_cfg(cls, cfg: Optional[dict]) -> Optional["TitleRule"]:
        if not cfg:
            return None
        groups = [RuleGroup(id=str(g["id"]), tier=str(g.get("tier", "sectoral")),
                            indicators=tuple(str(i) for i in g.get("indicators", []) or []),
                            patterns=tuple(re.compile(p) for p in g.get("patterns", []) or []))
                  for g in cfg.get("groups", []) or []]
        exclusions = [(str(x["id"]), re.compile(x["pattern"])) for x in cfg.get("exclusions", []) or []]
        if not groups:
            raise ValueError("title_rule has no groups")
        return cls(groups, exclusions, str(cfg.get("id", "title_rule")))

    @staticmethod
    def normalise(title: Optional[str]) -> str:
        text = (title or "").upper().replace("’", "'").replace("‘", "'")
        return re.sub(r"\s+", " ", text).strip()

    def match(self, title_bi: Optional[str], title_bm: Optional[str] = None) -> tuple[list[str], Optional[str]]:
        """(matched group ids, exclusion id). A title that hits an exclusion matches no group."""
        text = self.normalise(title_bi or title_bm)
        if not text:
            return [], None
        for xid, rx in self.exclusions:
            if rx.search(text):
                return [], xid
        return [g.id for g in self.groups if any(rx.search(text) for rx in g.patterns)], None

    def matched_terms(self, title_bi: Optional[str], title_bm: Optional[str] = None) -> list[str]:
        """The words the rule matched in the title, lower-cased ('personal data' style), for seed_query."""
        groups, _exclusion = self.match(title_bi, title_bm)
        text = self.normalise(title_bi or title_bm)
        return sorted({m.group(0).strip().lower() for g in self.groups if g.id in groups
                       for rx in g.patterns for m in [rx.search(text)] if m})

    def tier(self, group_ids: list[str]) -> Optional[str]:
        tiers = {g.tier for g in self.groups if g.id in group_ids}
        return "core" if "core" in tiers else ("sectoral" if tiers else None)


def _relevance_phrases(cfg: dict[str, Any]) -> set[str]:
    phrases: set[str] = set()
    for q in all_query_terms(cfg):
        words = re.findall(r"[a-z]+", q.lower())
        for a, b in zip(words, words[1:]):
            if len(a) > 2 and len(b) > 2 and a not in _STOP and b not in _STOP:
                phrases.add(f"{a} {b}")
    return phrases
