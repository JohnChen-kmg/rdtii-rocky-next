r"""Deciding whether two names are the same law.

Three stages ask this question and they must agree: the S2 recall gate (is the law a gold row
cites in this economy's corpus), NEW/KNOWN (is this fire's law the baseline's law), and the
evaluator (does a row we filed cite the law the gold row cites).

Two rules, and the second one only became visible when the corpus stopped being English.

**Latin names: cover the CITED name's tokens.** Dividing shared tokens by the shorter name makes
any longer title a match for a shorter one it contains, so a Lao "Criminal Code" resolved a
Malaysian "Criminal Procedure Code (Act 593) 2018". Tokens carrying a digit are dropped first,
because a law number and a year are identifiers rather than name words: the host writes "Law on
Electronic Data Protection No.25/NA 2017" where the corpus carries "Law on Electronic Data
Protection", and keeping "no25na" made Lao's central data-protection statute look absent.

**Non-Latin names: match the original script, not the translation.** Every Chinese and Lao
document in the corpus carries a `law_name_en`, and it is a *translation*: two independent
translations of one Chinese title rarely share 80% of their words. Measured 2026-09-27, matching
Chinese laws on English alone reported thirteen host-cited laws absent, of which at least six were
in the corpus under their own title. The host writes the original inside 《》 alongside its English,
so the reliable key is the CJK or Lao character sequence itself, compared by containment.
"""
from __future__ import annotations

import re

_NORM = re.compile(r"[^a-z0-9 ]")
_WS = re.compile(r"\s+")
# CJK ideographs and Lao. Enough for the six economies; extend with the script when one arrives.
_SCRIPT = re.compile(r"[㐀-鿿຀-໿]+")
MIN_SCRIPT_KEY = 4          # shorter than four characters is not a title
COVERAGE = 0.8              # share of the cited name's tokens a candidate must carry


def normalise(s: str) -> str:
    """Lowercase, punctuation-free, whitespace-collapsed. Drops every non-Latin character."""
    return _NORM.sub("", _WS.sub(" ", (s or "").lower())).strip()


# Words that carry no identity: every statute has them. Kept identical to the sets
# eval/evaluator.py and discovery/newknown.py used, so no consumer loses precision by moving here.
STOPWORDS = {"act", "the", "of", "and", "an", "a", "law", "no"}


def name_tokens(s: str) -> set[str]:
    """The words that identify a law: no stopwords, no law numbers, no years, light plural stem.

    The plural stem is load-bearing: the host writes "Services Tax Act" where the statute says
    "Service Tax Act", and without it that pair scores 0.5.
    """
    out = set()
    for tok in normalise(s).split():
        if tok in STOPWORDS or any(c.isdigit() for c in tok):
            continue
        if len(tok) > 3 and tok.endswith("s") and not tok.endswith("ss"):
            tok = tok[:-1]
        out.add(tok)
    return out


def script_key(s: str) -> str:
    """The non-Latin characters of a name, run together — a title's own fingerprint."""
    return "".join(_SCRIPT.findall(s or ""))


def covers(cited: str, candidate: str) -> bool:
    """Does `candidate` name the law `cited` names? Directional, by the cited name's tokens.

    A one-word name has to match exactly rather than by containment: "Banking Act 1970" reduces to
    {banking}, and containment would let "Islamic Banking Act" stand for it.
    """
    tc, tn = name_tokens(cited), name_tokens(candidate)
    if not tc or not tn:
        return False
    if len(tc) == 1:
        return tc == tn
    return len(tc & tn) / len(tc) >= COVERAGE


def same_script_law(cited: str, candidate: str) -> bool:
    """True when the two names share their original-script title by containment."""
    kc, kn = script_key(cited), script_key(candidate)
    if len(kc) < MIN_SCRIPT_KEY or len(kn) < MIN_SCRIPT_KEY:
        return False
    return kc in kn or kn in kc


def same_law(cited: str, candidate: str) -> bool:
    """Either rule is enough: the original script is decisive, the translation is a fallback."""
    return same_script_law(cited, candidate) or covers(cited, candidate)
