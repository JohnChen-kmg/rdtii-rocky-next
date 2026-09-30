"""Which act inside a document a provision belongs to.

A Timorese gazette issue is one PDF holding many separate acts - 912 of 1,922 documents, up to 26
in one issue - and `tl-ldcn-001` holds both Lei 1/2026 and Decreto-Lei 13/2026, **each with its
own Article 6**. Until now every provision in such an issue was attributed to a single law name,
so stage 3 grouped them as one law and matched the wrong title against the host's baseline.

**The acts are not detected, they are located.** Collection already handed over one law_table row
per act - 4,788 rows over 1,922 documents, already parsed into `sidecars.DocFacts.acts` - so the
act list, its count, and each act's name, number and kind are known before the text is opened.
Guessing them from the text would be inventing what was already declared, which is the mistake
this stage has made four times in one day. All the text has to answer is *where* each known act
begins.

**The completeness gate is what makes this safe.** `act_index` is emitted only when every act the
sidecar names was found at a distinct offset. A partial split is worse than none: if act 3's
header is missed, its articles are silently folded into act 2 and attributed to the wrong law.
When the gate fails the document keeps `act_index: null` exactly as before, and the laws row
records how many of how many were located, so the shortfall is visible rather than invisible.
"""

from __future__ import annotations

import logging
import re
import unicodedata
from dataclasses import dataclass

log = logging.getLogger("rdtii_p2.acts")

# portal_id prefix -> the words the gazette prints for that instrument. Longest alternatives
# first, so DECRETO-LEI is never matched as DECRETO.
_KIND_WORDS: dict[str, str] = {
    "DL": r"DECRETO[\s­‐-―-]*LEI",
    "DP": r"DECRETO\s+DO\s+PRESIDENTE(?:\s+DA\s+REP[UÚ]BLICA)?|DECRETO\s+PRESIDENCIAL",
    "DG": r"DECRETO\s+DO\s+GOVERNO",
    "RP": r"RESOLU[CÇ][AÃ]O\s+DO\s+PARLAMENTO(?:\s+NACIONAL)?",
    "RG": r"RESOLU[CÇ][AÃ]O\s+DO\s+GOVERNO",
    "L": r"LEI",
}

# "N.º 13/2026", "N.o 13 / 2026", "Nº: 1 / 2019" - the ordinal mark is printed several ways and
# OCR adds more, so the separator class is permissive and the line anchor does the real work.
# Built by concatenation, not str.format: the regex's own {0,6} quantifier is not a placeholder.
_NUM_SEP = r"N[.º°ª⁰oø:'´’\s]{0,6}0*"

# A contents entry looks the same as a header except for the dot leader running to a page number.
_DOT_LEADER = re.compile(r"\.{4,}")


@dataclass
class ActSpan:
    """One located act: where it starts, and what the sidecar says it is."""
    index: int                      # 1-based, in document order
    char_start: int
    char_end: int
    law_name: str | None
    law_number: str | None
    portal_id: str | None
    document_kind: str | None


def _normalise(text: str) -> str:
    """NFC, and the soft hyphen removed - it is invisible and splits DECRETO­LEI in two."""
    return unicodedata.normalize("NFC", text).replace("­", "")


def _pattern_for(portal_id: str) -> re.Pattern | None:
    """The line-anchored header pattern for one act, from its portal_id (KIND-num-year)."""
    parts = (portal_id or "").split("-")
    if len(parts) < 3:
        return None
    kind, number, year = parts[0].upper(), parts[1], parts[2]
    words = _KIND_WORDS.get(kind)
    if not words or not number.isdigit() or not year.isdigit():
        return None
    body = _NUM_SEP + re.escape(number) + r"\s*/\s*" + re.escape(year) + r"(?![0-9])"
    return re.compile(r"(?mi)^[ \t]*(?:" + words + r")[\s,­‐-―-]*" + body)


def locate(text: str, acts: list[dict]) -> tuple[list[ActSpan], int]:
    """(spans, located) - one ActSpan per act the sidecar names, in document order.

    `located` is how many acts were found. The caller compares it to `len(acts)`: only when
    they are equal may the result be used, because an act whose header was missed does not
    leave a gap, it leaves its articles inside the act before it.
    """
    if len(acts) < 2:
        return [], len(acts)

    normalised = _normalise(text)
    offsets: dict[int, int] = {}
    for position, act in enumerate(acts):
        pattern = _pattern_for(act.get("portal_id", ""))
        if pattern is None:
            continue
        # The LAST match, not the first: an issue restates every act in its SUMÁRIO before
        # printing any of them, so the first match is the contents entry. A line carrying a
        # dot leader is a contents entry wherever it appears and is never an anchor.
        best = None
        for match in pattern.finditer(normalised):
            line_end = normalised.find("\n", match.end())
            line = normalised[match.start():line_end if line_end != -1 else len(normalised)]
            if _DOT_LEADER.search(line):
                continue
            best = match.start()
        if best is not None:
            offsets[position] = best

    if len(offsets) != len(acts) or len(set(offsets.values())) != len(acts):
        return [], len(set(offsets.values()))

    ordered = sorted(offsets.items(), key=lambda pair: pair[1])
    spans: list[ActSpan] = []
    for rank, (position, start) in enumerate(ordered):
        end = ordered[rank + 1][1] if rank + 1 < len(ordered) else len(normalised)
        act = acts[position]
        spans.append(ActSpan(
            index=rank + 1, char_start=start, char_end=end,
            law_name=(act.get("law_name") or "").strip() or None,
            law_number=(act.get("law_number") or "").strip() or None,
            portal_id=(act.get("portal_id") or "").strip() or None,
            document_kind=(act.get("document_kind") or "").strip() or None,
        ))
    return spans, len(acts)


def act_at(spans: list[ActSpan], char_start: int) -> ActSpan | None:
    """The act a provision belongs to, by where its snippet starts."""
    found = None
    for span in spans:
        if span.char_start <= char_start < span.char_end:
            found = span
    return found
