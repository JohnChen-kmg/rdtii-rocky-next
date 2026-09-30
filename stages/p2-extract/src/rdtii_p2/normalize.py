"""Normalization - applied ONCE, then frozen as source_text/<doc_id>.txt.

Every char offset in the hand-off (snippet, context, grounded metadata) indexes
into the exact string this module produces (contract section 3.4). Changing any
rule here after texts are frozen invalidates all offsets: version the change and
re-run the corpus instead.

Pipeline (deterministic, no LLM):
  per page : NFC -> newline canonicalization -> control-char strip ->
             page furniture removal (repeated headers/footers, bare page numbers)
             -> trailing-whitespace strip -> in-page de-hyphenation + line unwrap
  at joins : cross-page de-hyphenation / paragraph unwrap, page offsets recorded
             AFTER all transformations so they are exact.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

# Furniture detection: a line is furniture if its digit-masked form appears on
# >= FURNITURE_PAGE_FRACTION of pages (min FURNITURE_MIN_PAGES absolute).
# 0.3, not 0.5: running headers commonly alternate two odd/even-page variants,
# each present on only ~half the pages (SSO '3 Act 2012 2020 Ed.' vs
# '2020 Ed. Act 2012 4'). Repeated real content at 30% of pages does not occur
# in statutes; headers at ~48%/37% do.
FURNITURE_PAGE_FRACTION = 0.3
FURNITURE_MIN_PAGES = 3
FURNITURE_MAX_LEN = 100

# U+FFFD repair: SSO/MY statute PDFs encode the structural em-dash with no
# ToUnicode map, so it extracts as the replacement char. Only positions where
# statute typography makes the lost glyph unambiguous are repaired; every other
# U+FFFD is left as-is (verbatim honesty) and counted.
_FFFD_SECTION_MARKER = re.compile(r"(?<=\d\.)�(?=\s*\()")     # "26.<?>(1)"
_FFFD_HEADING_SEP = re.compile(r"(?<=[A-Za-z0-9)]) � (?=[A-Z0-9(])")  # "Part 6 <?> TITLE"
_FFFD_LIST_INTRO = re.compile(r"(?<=[a-z])�(?=\s*$)", re.M)   # "applies to<?>\n(a)..."

_DEHYPHEN_IN_PAGE = re.compile(r"([a-z])-\n([a-z])")
# Unwrap a soft line break: previous line does not end a sentence/clause and the
# next line continues in lowercase. Lines opening with "(" are NEVER unwrapped -
# "(1)"/"(a)" markers must stay at line starts for boundary detection.
_UNWRAP_IN_PAGE = re.compile(r"(?<![.:;—])\n(?=[a-z])")
_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_ONLY_DIGITS_PUNCT = re.compile(r"^[\d\s.\-–—()\[\]/]*$")
# always-furniture line shapes regardless of page frequency: '-- continued'
# running headers use ordinal WORDS ('NINTH SCHEDULE - continued') that
# digit-masking cannot unify, and each variant sits below the page threshold
_ALWAYS_FURNITURE = re.compile(r"(?i)^\S{1,20}\s+schedules?\s*[—–-]\s*continued\s*$")


@dataclass
class NormalizedDoc:
    text: str
    # 1-based page number -> char offset in `text` where that page begins
    page_offsets: list[tuple[int, int]] = field(default_factory=list)
    furniture_removed: list[str] = field(default_factory=list)
    fffd_remaining: int = 0  # unrepaired U+FFFD chars left in the frozen text

    def page_for_offset(self, offset: int) -> int | None:
        page = None
        for number, start in self.page_offsets:
            if start <= offset:
                page = number
            else:
                break
        return page


def _mask_digits(line: str) -> str:
    return re.sub(r"\d+", "#", line.strip())


def _canonicalize(page_text: str) -> str:
    text = unicodedata.normalize("NFC", page_text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _CONTROL_CHARS.sub("", text)
    text = _FFFD_SECTION_MARKER.sub("—", text)
    text = _FFFD_HEADING_SEP.sub(" — ", text)
    text = _FFFD_LIST_INTRO.sub("—", text)
    return text


# A civil-law or CJK statute numbers every article the same way, so once digits are masked
# every article heading collapses to ONE shape - "Artigo #.o" - which then repeats on most
# pages and is removed as page furniture. Measured on three Timorese acts: one 11-page act
# went from 41 "Artigo" headings in the raw text to none after normalisation, taking the
# segmenter's only anchors with it.
#
# English is deliberately NOT protected. A common-law heading carries its own words
# ("12.-(1) Interpretation"), so no two masked lines are equal and the detector never treats
# them as furniture. Leaving English alone means the Round 1 regression cannot move.
_HEADING_PATTERNS = (
    r"^\s*Artigo\s+\d{1,3}",                                   # Portuguese article
    r"^\s*(CAP[IÍ]TULO|Cap[ií]tulo|SEC[CÇ][AÃ]O|Sec[cç][aã]o"
    r"|T[IÍ]TULO|T[ií]tulo|ANEXO|Anexo)\b",                    # Portuguese divisions
    "^\\s*ມາດຕາ",                      # Lao: maatraa, article
    "^\\s*(ພາກ|ໝວດ)",             # Lao: phaak / muat
    "^\\s*第[一二三四五六七八九十百"
    "零〇\\d]+[条條章节節编篇]",   # Chinese divisions
    "^\\s*附件",                                        # Chinese annex
)
_HEADING_RE = re.compile("|".join(_HEADING_PATTERNS))


def is_structural_heading(line: str) -> bool:
    """True for a line that numbers a division of the law in a tradition where every such
    heading shares one shape. Such a line is never page furniture."""
    return bool(_HEADING_RE.match(line))


def detect_furniture(pages: list[str]) -> set[str]:
    """Digit-masked lines that repeat across enough pages to be page furniture."""
    if len(pages) < FURNITURE_MIN_PAGES:
        return set()
    counts: dict[str, int] = {}
    for page_text in pages:
        seen_on_page = set()
        for line in page_text.split("\n"):
            if is_structural_heading(line):
                continue                      # an article heading is never furniture
            masked = _mask_digits(line)
            if masked and len(masked) <= FURNITURE_MAX_LEN:
                seen_on_page.add(masked)
        for masked in seen_on_page:
            counts[masked] = counts.get(masked, 0) + 1
    threshold = max(FURNITURE_MIN_PAGES, int(len(pages) * FURNITURE_PAGE_FRACTION))
    return {masked for masked, count in counts.items() if count >= threshold}


def _mask_to_regex(masked: str) -> str:
    """Digit-masked furniture shape -> regex matching its concrete occurrences."""
    return re.escape(masked).replace(r"\#", r"\d+")


def _clean_page(page_text: str, furniture: set[str], removed: list[str]) -> str:
    # headers sometimes glue onto a body line during extraction: strip them
    # when a furniture shape appears as a line prefix or suffix too
    # Longest shape first, then alphabetically. The order matters and must not vary:
    # these patterns are applied in sequence and each one rewrites the line, so two
    # overlapping furniture shapes give different output depending on which is tried
    # first. Iterating the set directly made that order depend on Python's per-process
    # string hashing, so the same document normalised to different text on different
    # runs - and source_text is what every character offset indexes into.
    affix_patterns = [
        (re.compile(r"^" + _mask_to_regex(m) + r"\s+"),
         re.compile(r"\s+" + _mask_to_regex(m) + r"$"))
        for m in sorted(furniture, key=lambda shape: (-len(shape), shape))
    ]
    kept: list[str] = []
    for line in page_text.split("\n"):
        stripped = line.rstrip()
        masked = _mask_digits(stripped)
        if masked and masked in furniture:
            if stripped not in removed:
                removed.append(stripped)
            continue
        if stripped and _ONLY_DIGITS_PUNCT.match(stripped):
            # bare page numbers / rules - never provision content
            continue
        if stripped and _ALWAYS_FURNITURE.match(stripped):
            if stripped not in removed:
                removed.append(stripped)
            continue
        for prefix, suffix in affix_patterns:
            new = prefix.sub("", stripped)
            new = suffix.sub("", new)
            if new != stripped:
                fragment = stripped.replace(new, "").strip()
                if fragment and fragment not in removed:
                    removed.append(fragment)
                stripped = new
        kept.append(stripped)
    text = "\n".join(kept)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = _DEHYPHEN_IN_PAGE.sub(r"\1\2", text)
    text = _UNWRAP_IN_PAGE.sub(" ", text)
    return text.strip("\n")


def normalize_pages(raw_pages: list[str]) -> NormalizedDoc:
    """Normalize per-page text into the single frozen source_text string."""
    canonical = [_canonicalize(p) for p in raw_pages]
    furniture = detect_furniture(canonical)
    removed: list[str] = []

    parts: list[str] = []
    page_offsets: list[tuple[int, int]] = []
    accumulated = 0

    for index, page_text in enumerate(canonical, start=1):
        cleaned = _clean_page(page_text, furniture, removed)
        if not parts:
            joiner = ""
        else:
            prev_tail = parts[-1][-2:] if parts[-1] else ""
            if re.search(r"[a-z]-$", prev_tail) and re.match(r"[a-z]", cleaned or " "):
                # cross-page hyphenated word: drop the hyphen, join directly
                parts[-1] = parts[-1][:-1]
                accumulated -= 1
                joiner = ""
            elif (
                parts[-1]
                and not re.search(r"[.:;—]$", parts[-1])
                and re.match(r"[a-z]", cleaned or " ")
            ):
                joiner = " "
            else:
                joiner = "\n"
        parts.append(cleaned)
        page_offsets.append((index, accumulated + len(joiner)))
        if joiner:
            parts.insert(-1, joiner)
            accumulated += len(joiner)
        accumulated += len(cleaned)

    text = "".join(parts)
    return NormalizedDoc(
        text=text,
        page_offsets=page_offsets,
        furniture_removed=removed,
        fffd_remaining=text.count("�"),
    )
