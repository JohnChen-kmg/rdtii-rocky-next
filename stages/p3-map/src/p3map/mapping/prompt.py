"""Mapping-prompt assembly (decisions #5/#6).

System prefix = the vendored instrument rendered byte-stably (all 9 indicator
blocks always present, fixed order, no timestamps) -> prompt-cacheable.
User turn = the provision + its candidate indicators.
"""
from __future__ import annotations

import json
from functools import lru_cache

import yaml

from config.instrument import load as load_instrument
from config.settings import INDICATORS


@lru_cache(maxsize=1)
def build_system_prefix() -> str:
    # Through the loader, so the prefix renders the same whether the vendored instrument keys its
    # blocks "P6-I1" or "6.1". The rendered ID is always decimal, which is what the model must emit.
    ins = load_instrument()
    ind_doc, pol_doc = ins.top, ins.policies

    parts = [
        "You are a legal analyst coding statutory provisions against the RDTII 2.1 "
        "digital-trade indicators (Pillars 6-7). Decide from the provided text only; "
        "never invent provisions. Follow each indicator's scoring tree exactly.",
        "\n## Score polarity\n" + yaml.dump(ind_doc.get("score_polarity", {}),
                                            sort_keys=True, allow_unicode=True),
        "\n## Shared definitions\n" + yaml.dump(ind_doc.get("definitions", {}),
                                                sort_keys=True, allow_unicode=True),
    ]
    for ind in INDICATORS:  # fixed order — byte-stable prefix
        b = ins.block(ind)
        # Allow-list, so a field the instrument adds later cannot leak into the prompt. It is also
        # what keeps `review_notes` out: the instrument forbids rendering it as host text.
        keep = {k: b[k] for k in (
            "id", "name", "question", "definition", "scoring", "scoring_tree",
            "disambiguation", "coding_rules", "exceptions") if k in b}
        keep["id"] = ind  # decimal, whatever the file says
        parts.append(f"\n## {ind}\n" + yaml.dump(keep, sort_keys=True,
                                                 allow_unicode=True, width=100))
    parts.append("\n## Cross-cutting scoring policy\n" + yaml.dump(
        {k: pol_doc[k] for k in ("scoring_policy", "edge_cases", "measure_inclusion")
         if k in pol_doc}, sort_keys=True, allow_unicode=True, width=100))
    return "\n".join(parts)


def build_user_turn(rec: dict, candidates: list[str]) -> str:
    return (
        f"PROVISION {rec['provision_id']}\n"
        f"Economy: {rec.get('economy')} | Law: {rec.get('law_name')} | "
        f"Section: {rec.get('article_section')}\n"
        f"TEXT (context :: snippet :: context):\n{rec.get('text','')[:6000]}\n\n"
        f"CANDIDATE INDICATORS (emit exactly one verdict per candidate): "
        f"{json.dumps(candidates)}\n"
        "Answer the core legal question first, run every trap check, then emit "
        "verdicts. verbatim_quote must be an exact substring of TEXT."
    )
