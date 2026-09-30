"""Grounding gate - "no quote = no record" (contract section 3.2).

The snippet bytes are ALWAYS copied from the frozen source_text between chosen
offsets, never taken from an LLM. Before any record is written the assertion
source_text[start:end] == verbatim_snippet is re-verified; on mismatch the
record is dropped and the drop is logged. Structurally unfakeable.
"""

from __future__ import annotations

from dataclasses import dataclass

CONTEXT_WIDTH = 200


class GroundingError(AssertionError):
    """Offset/snippet mismatch - the record carrying it must be dropped."""


@dataclass
class GroundedSnippet:
    snippet: str
    char_start: int
    char_end: int
    context_before: str
    context_after: str


def copy_grounded(text: str, start: int, end: int) -> GroundedSnippet:
    """Copy snippet bytes + ~200-char contexts from the frozen text."""
    if not (0 <= start < end <= len(text)):
        raise GroundingError(f"offsets [{start}:{end}] out of bounds for len {len(text)}")
    return GroundedSnippet(
        snippet=text[start:end],
        char_start=start,
        char_end=end,
        context_before=text[max(0, start - CONTEXT_WIDTH):start],
        context_after=text[end:end + CONTEXT_WIDTH],
    )


def verify(text: str, start: int, end: int, snippet: str) -> None:
    """The hard gate: raises GroundingError unless bytes match exactly."""
    actual = text[start:end]
    if actual != snippet:
        preview_expected = snippet[:80].replace("\n", "\\n")
        preview_actual = actual[:80].replace("\n", "\\n")
        raise GroundingError(
            f"grounding assertion failed at [{start}:{end}]: "
            f"expected {preview_expected!r}... got {preview_actual!r}..."
        )


def locate_exact(text: str, needle: str, hint_start: int | None = None) -> int | None:
    """Find `needle` verbatim; prefer the occurrence nearest hint_start.

    Retry path for LLM-pointed headings (PLAN 2.6 step 3): the LLM returns
    heading TEXT, this locates it, and offsets are recomputed - the LLM never
    emits offsets or quoted bytes.
    """
    if not needle:
        return None
    first = text.find(needle)
    if first == -1:
        return None
    if hint_start is None:
        return first
    best, position = None, first
    while position != -1:
        if best is None or abs(position - hint_start) < abs(best - hint_start):
            best = position
        position = text.find(needle, position + 1)
    return best
