"""Anchor a model's quote to the source text, and file the source's own bytes.

The host's rule for column I is "Copy the EXACT text — no edits, no paraphrasing", verified
against the source. Round 1 checked that with one comparison — whitespace collapsed, lowercased,
substring — and filed whatever the model returned. On English that is nearly always the same
string. On Chinese it is not:

    exact substring                      grounded
    one space inserted                   NOT grounded   (Chinese has no spaces to collapse)
    full-width "，" normalised to ","     NOT grounded
    wrapped in curly quotation marks     NOT grounded

Measured on real corpus text, 2026-09-27. Since a row whose quote is not grounded is no longer
filed at all (H5), an imperfectly quoting model would have cost every Chinese row while the run
reported success.

Decision M10 settles what to do: the quote is cut from the source by span selection. So this module
locates the model's quote in the source under progressively more forgiving comparisons, and returns
**the source's own substring** for that span. What gets filed is then byte-exact by construction,
whatever the model did to the characters on the way out.

The comparisons, in order, and each one reports itself:

    exact        the quote is already a substring of the source
    whitespace   equal once runs of whitespace collapse (Round 1's check)
    normalised   equal once NFKC-folded, case-folded, quote marks dropped, CJK punctuation
                 mapped to its ASCII form and ALL whitespace removed. NFKC maps "，" to "," but
                 leaves "。" and "、" alone, so those are folded here; removing whitespace
                 entirely is what forgives a space inserted into Chinese
    none         not found: the row cannot be filed

`normalised` is the loosest and it is still strict in the way that matters: the same characters in
the same order. It cannot match a paraphrase, a summary or a translation, because none of those
survive NFKC folding as the same character sequence.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

# Quotation marks a model likes to wrap a quote in, and which are never part of the evidence
# unless they are in the source at that position -- which the exact and whitespace passes catch
# first.
_EDGE_QUOTES = "\"'“”„‟‘’‚‛«»‹›「」『』"
_WS = re.compile(r"\s+")

# CJK punctuation that NFKC does NOT fold, mapped to the ASCII form a model substitutes for it.
# Measured need: NFKC turns the fullwidth comma "，" into "," but leaves the ideographic full stop
# "。" and the ideographic comma "、" alone, so a model that writes ASCII punctuation in a Chinese
# quote fails to anchor on those characters alone. Folding them costs nothing, because the text we
# file is always re-cut from the source: the locator may be forgiving, the evidence is not.
_PUNCT_FOLD = {
    "。": ".", "、": ",", "・": ",", "〜": "~", "〝": '"', "〞": '"',
    "「": '"', "」": '"', "『": '"', "』": '"', "〈": "<", "〉": ">",
    "《": "<", "》": ">", "【": "[", "】": "]", "〔": "[", "〕": "]",
    "‧": ".", "·": ".", "–": "-", "—": "-", "‒": "-", "―": "-",
    "‘": "'", "’": "'", "“": '"', "”": '"', "„": '"', "‟": '"',
}


@dataclass(frozen=True)
class Anchored:
    """The result of anchoring one quote."""

    quote: str          # the source's own bytes for the matched span, or the model's quote intact
    grounded: bool
    how: str            # exact | whitespace | normalised | none
    start: int = -1     # span in the source text, when one was found
    end: int = -1

    @property
    def repaired(self) -> bool:
        """True when what we file differs from what the model returned."""
        return self.grounded and self.how != "exact"


def _fold(s: str) -> tuple[str, list[int]]:
    """NFKC-fold, case-fold and drop whitespace; keep each kept character's source index.

    NFKC is applied per character so the index mapping stays exact: a character that expands to
    several (such as "㍿") contributes several folded characters, all pointing at it.
    """
    out: list[str] = []
    idx: list[int] = []
    for i, ch in enumerate(s):
        if ch.isspace():
            continue
        folded = unicodedata.normalize("NFKC", _PUNCT_FOLD.get(ch, ch)).casefold()
        for c in folded:
            out.append(c)
            idx.append(i)
    return "".join(out), idx


def anchor(quote: str, text: str) -> Anchored:
    """Find `quote` in `text` and return the source's own substring for that span."""
    q = (quote or "").strip()
    t = text or ""
    if not q or not t:
        return Anchored(quote or "", False, "none")

    # Two forms to look for: the quote as returned, and the quote with the marks a model may
    # have wrapped it in removed. The unstripped form is tried first at every pass, because a
    # quote can legitimately END in one of those characters -- "Auctioneers’" is a
    # possessive, not a closing quote, and stripping it would edit the evidence.
    forms = [q]
    stripped = q.strip(_EDGE_QUOTES).strip()
    if stripped and stripped != q:
        forms.append(stripped)

    for form in forms:                      # 1. exact
        at = t.find(form)
        if at >= 0:
            return Anchored(t[at:at + len(form)], True, "exact", at, at + len(form))

    for form in forms:                      # 2. whitespace collapsed, Round 1's comparison
        span = _span_by_collapse(form, t)
        if span is not None:
            s, e = span
            return Anchored(t[s:e], True, "whitespace", s, e)

    for form in forms:                      # 3. NFKC, case, punctuation, all whitespace
        span = _span_by_fold(form, t)
        if span is not None:
            s, e = span
            return Anchored(t[s:e], True, "normalised", s, e)

    return Anchored(q, False, "none")


def _span_by_collapse(q: str, t: str) -> tuple[int, int] | None:
    """Match with runs of whitespace collapsed on both sides, case-insensitively."""
    qc = _WS.sub(" ", q).strip().lower()
    if not qc:
        return None
    # build the collapsed text alongside the source index of each collapsed character
    out: list[str] = []
    idx: list[int] = []
    prev_space = False
    for i, ch in enumerate(t):
        if ch.isspace():
            if out and not prev_space:
                out.append(" ")
                idx.append(i)
            prev_space = True
            continue
        prev_space = False
        out.append(ch.lower())
        idx.append(i)
    tc = "".join(out)
    at = tc.find(qc)
    if at < 0:
        return None
    return idx[at], idx[at + len(qc) - 1] + 1


def _span_by_fold(q: str, t: str) -> tuple[int, int] | None:
    qf, _ = _fold(q)
    if not qf:
        return None
    tf, tidx = _fold(t)
    at = tf.find(qf)
    if at < 0:
        return None
    return tidx[at], tidx[at + len(qf) - 1] + 1
