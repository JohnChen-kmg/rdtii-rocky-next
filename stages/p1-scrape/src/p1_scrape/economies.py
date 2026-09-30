"""Economy code normalization + the 'must not crash on bad input' rule (§9.1)."""
from __future__ import annotations

_NAME_TO_CODE = {
    "sg": "SG", "singapore": "SG",
    "au": "AU", "australia": "AU",
    "my": "MY", "malaysia": "MY",
    "tl": "TL", "timor-leste": "TL", "timor leste": "TL", "east timor": "TL",
    "la": "LA", "lao": "LA", "laos": "LA", "lao pdr": "LA",
}

#: The economies this engine can crawl. China is deliberately absent: the national
#: database forbids automated collection in its robots.txt, so China's documents are
#: collected by hand and its tools live in adapters/cn_npc/ with no adapter at all.
VALID_CODES = ("SG", "AU", "MY", "TL", "LA")


class BadCountryInput(ValueError):
    """Raised for an unrecognized economy — callers log a warning and exit non-zero."""


def normalize_economy(token: str) -> str:
    code = _NAME_TO_CODE.get(token.strip().lower())
    if code is None:
        raise BadCountryInput(token)
    return code


def parse_economies(spec: str) -> list[str]:
    """Parse 'SG', 'Singapore', 'SG,AU,MY', 'all' → list of codes. Order-preserving, deduped."""
    if spec is None:
        raise BadCountryInput("<empty>")
    spec = spec.strip()
    if spec.lower() in {"all", "*"}:
        return list(VALID_CODES)
    out: list[str] = []
    for tok in spec.split(","):
        tok = tok.strip()
        if not tok:
            continue
        code = normalize_economy(tok)
        if code not in out:
            out.append(code)
    if not out:
        raise BadCountryInput(spec)
    return out


def parse_pillars(spec: str | None) -> list[int]:
    """Parse '6', '6,7', None → [6] / [6,7] / [6,7] (default both)."""
    if not spec:
        return [6, 7]
    out: list[int] = []
    for tok in str(spec).split(","):
        tok = tok.strip().replace("P", "").replace("p", "")
        if not tok:
            continue
        try:
            n = int(tok)
        except ValueError:
            continue
        if n in (6, 7) and n not in out:
            out.append(n)
    return out or [6, 7]
