"""Economy codes, the names the host sheet wants, and whether the sparse leg can serve them.

Three places need this and must not disagree: the emitter writes column A, the wrapper at the repo
root resolves `--economy` and the `--docs` doc-id prefix, and S1 decides which retrieval legs a run
needs. Round 1 kept its own three-economy tuple in each of them, which is how
`main.py` came to refuse China at argument parsing while the stage itself was ready for it.

Stdlib only, deliberately: `main.py`'s serve path promises no heavy imports, so this module must be
importable without yaml, numpy or torch.

What is NOT here: the membership of the sealed 15 October draw. The workspace records a
contradiction between the sources on that point, so no list in the code should imply it is settled.
`ECON_NAME` is simply every economy this system can name; `SETTINGS.economies` scopes a run.
"""
from __future__ import annotations

# code -> exactly the strings in the Coverage Matrix sheet of OUTPUT_TEMPLATE_FINAL_ROUND.xlsx,
# whose per-economy counts are COUNTIFS against column A. The Instructions sheet says "official UN
# country name, e.g. Lao People's Democratic Republic", but that string matches no row in the
# matrix, so filing it would count zero provisions for that economy and fail checklist item 15
# ("Coverage Matrix shows three or more economies"). The sheet wins over the prose.
#
# So this table is load-bearing, not cosmetic: filing "TH" where the matrix says "Thailand" counts
# zero provisions for Thailand.
ECON_NAME = {
    "SG": "Singapore", "AU": "Australia", "MY": "Malaysia",
    "CN": "China", "LA": "Lao PDR", "TL": "Timor-Leste",
    "TH": "Thailand", "VN": "Viet Nam", "ID": "Indonesia", "IN": "India",
    "KZ": "Kazakhstan", "MN": "Mongolia", "RU": "Russian Federation",
}

# The language of the corpus text, ISO 639-3 (config/languages.py names them).
#
# MEASURED on the 27 September index, as the share of top-K slots the BM25 leg returned for that
# economy (notes/2026-09-27-sparse-leg-blind-to-cn-la.md):
#   AU, SG, MY  eng   the sparse leg carries them; Round 1 filed 142 rows off it
#   CN          zho   ZERO rows across all nine indicators and all 450,000 slots
#   LA          lao   ZERO
#   TL          por   4.4% against a 24.7% corpus share -- Latin script, but the queries are
#                     English, so the tokeniser matches almost nothing
# ASSUMED for the rest, from the language their legislation is published in. Unmeasured: no corpus
# has been built for them. India's central legislation is published in English.
PRIMARY_LANGUAGE = {
    "SG": "eng", "AU": "eng", "MY": "eng", "IN": "eng",
    "CN": "zho", "LA": "lao", "TL": "por",
    "TH": "tha", "VN": "vie", "ID": "ind", "KZ": "kaz", "MN": "mon", "RU": "rus",
}

# Everything that has ever named an economy to this system, lowercased -> code. Built from the
# names above plus the spellings the host materials, the crawler manifests and a hurried operator
# actually use.
ALIASES = {
    "sgp": "SG", "mys": "MY", "aus": "AU", "chn": "CN", "lao": "LA", "tls": "TL",
    "tha": "TH", "vnm": "VN", "idn": "ID", "ind": "IN", "kaz": "KZ", "mng": "MN", "rus": "RU",
    "laos": "LA", "lao pdr": "LA", "lao people's democratic republic": "LA",
    "timor leste": "TL", "east timor": "TL", "timor-leste": "TL",
    "vietnam": "VN", "viet nam": "VN",
    "russia": "RU", "russian federation": "RU",
    "prc": "CN", "people's republic of china": "CN",
}
for _code, _name in ECON_NAME.items():
    ALIASES[_code.lower()] = _code
    ALIASES[_name.lower()] = _code


def resolve(raw) -> str | None:
    """A two-letter code from a code, a name or a known spelling. None when nothing matches.

    Never guesses: an unknown economy must be reported, because silently mapping it to a
    neighbouring code would file rows under the wrong economy.
    """
    s = str(raw or "").strip().lower()
    if not s:
        return None
    return ALIASES.get(s)


def official_name(econ) -> str:
    """The name column A wants, or the code unchanged when we have no name for it.

    Not called `host_name`: `config.languages.host_name` already means "the name column N wants",
    and the emitter imports both.
    """
    code = resolve(econ) or str(econ or "").strip().upper()
    return ECON_NAME.get(code, code)


def language(econ) -> str | None:
    """The ISO 639-3 language of that economy's corpus, or None when we have no basis to say."""
    code = resolve(econ)
    return PRIMARY_LANGUAGE.get(code) if code else None


def sparse_leg_adequate(econ) -> bool:
    """Can a BM25 leg with English queries retrieve anything for this economy?

    Only where the corpus is in English. This is measured, not assumed: an English tokeniser over
    Chinese or Lao text produces no term that an English query can match, and the 27 September
    index returned exactly zero rows for both. Portuguese is Latin-script and still only reached
    4.4% of its corpus share, so "Latin script" is not the test -- the language is.

    An economy we have no language for returns False. A run that cannot say what language it is
    reading should not quietly assume the easy case.
    """
    return language(econ) == "eng"


def economies_needing_dense(economies) -> list[str]:
    """Those economies in the run whose corpus the sparse leg cannot read, in the order given.

    A caller that skips the dense leg must consult this first. An empty list is the only case in
    which bm25 alone, or an empty dense stub, retrieves anything at all.
    """
    return [e for e in economies if not sparse_leg_adequate(e)]
