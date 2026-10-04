"""Segmenting a statute that is not written in the common-law style.

`segment.py` reads English common-law acts: "12.—(1)", PART, Division, SCHEDULE. It is left
exactly as it is, because the Round 1 corpus is the regression baseline and nothing here may
move it. This module handles the other three traditions in the finale corpus, and the profile
is chosen by the document's declared language, never by trying patterns on the text - the same
containment rule the Australian collector already follows.

    por   Timor-Leste     Artigo 1.o, numbered paragraphs "1 - ", CAPITULO / SECCAO / TITULO
    lao   Lao PDR         maatraa (article), phaak / muat (part, chapter)
    zho   China           di-N-tiao (article), chapter, section, annex

Two things every profile must get right:

**The table of contents.** A statute restates its article headings up front. Left in, every
article is found twice and the first copy has no body. A heading whose body is shorter than
MIN_BODY_CHARS, in a run of such headings, is a contents entry and is dropped.

**The article number.** For Lao the number comes off a scan, and about one in seven is misread
(30 read as 90, 32 as 92, 38 as 88). Articles ascend, so the number is repaired from position -
and the repair is recorded on the span, never silently applied, because an invisible repair is
a wrong citation nobody can see.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

from rdtii_p2.segment import SegmentResult, Span

log = logging.getLogger("rdtii_p2.segment_civil")

# A heading with less body than this, among others like it, is a contents entry.
#
# The threshold is PER SCRIPT, because 120 characters is not a comparable quantity of law in
# an alphabetic and a logographic script. Measured on the Chinese Cybersecurity Law: its 81
# articles have a median body of 79 characters and 65 of the 81 fall under 120, so a single
# Latin-calibrated threshold discarded 49 real articles as contents - including
# 第八十一条 "This Law takes effect on 1 June 2017", a 24-character provision that carries the
# commencement date. Chinese and Lao pack far more meaning per character than Portuguese.
MIN_BODY_CHARS = 120
# Only Chinese is lowered, and only because it was measured. Lao was lowered to 60 on
# 2026-09-23 and reverted the same hour: it recovered 1,087 provisions, but a sample
# showed cross-references among them - "ມາດຕາ 15 ຂອງດໍາລັດສະບັບນີ້" ("Article 15 of
# this decree") is a mention inside another article, not a heading, and OCR line breaks
# put it at the start of a line where the pattern matches. The 120-char default was
# filtering those by accident. Lowering it needs its own measurement, not an analogy
# with Chinese.
MIN_BODY_CHARS_BY_LANGUAGE = {"zho": 24}

# Languages whose contents block is identified by POSITION (the run of short
# headings before the first substantial body) as well as by length.
POSITIONAL_CONTENTS_GUARD = {"zho"}


def min_body_chars(language: str) -> int:
    return MIN_BODY_CHARS_BY_LANGUAGE.get(language, MIN_BODY_CHARS)
# How far a number may stray from its expected position before the sequence is abandoned
# rather than repaired. A gap of three is a genuine gap in the statute; a jump of sixty is OCR.
MAX_SEQUENCE_DRIFT = 3


@dataclass
class Profile:
    language: str
    article: re.Pattern            # one capture group: the article number
    divisions: tuple               # (unit name, compiled pattern) outermost first
    subsection: re.Pattern | None  # one capture group: the paragraph number
    numerals: str = "arabic"       # "arabic" | "chinese"
    # A second numbering style the same language uses for a different KIND of instrument.
    # Only tried when the primary pattern finds nothing.
    article_alt: re.Pattern | None = None
    alt_min_matches: int = 3       # below this, an alt match is prose, not structure

    def cite(self, number: str, sub: str | None = None) -> str:
        """The host's template asks for 'Art. 26(2) or S 13(1)(a)'."""
        return f"Art. {number}" + (f"({sub})" if sub else "")


_CHINESE_DIGITS = {"零": 0, "〇": 0, "一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
                   "六": 6, "七": 7, "八": 8, "九": 9}


def chinese_numeral(text: str) -> int | None:
    """第二十四条 -> 24. Handles the forms a statute actually uses, up to the thousands."""
    if text.isdigit():
        return int(text)
    total, section, digit = 0, 0, 0
    for ch in text:
        if ch in _CHINESE_DIGITS:
            digit = _CHINESE_DIGITS[ch]
        elif ch == "十":
            section += (digit or 1) * 10
            digit = 0
        elif ch == "百":
            section += (digit or 1) * 100
            digit = 0
        elif ch == "千":
            section += (digit or 1) * 1000
            digit = 0
        else:
            return None
    return total + section + digit


# The key of the English-edition profile. Not a language code: no document declares it, the stage
# picks it (cli._segment_for) for a file declared English in an economy that writes in articles.
ENGLISH_ARTICLES = "eng-articles"

PROFILES: dict[str, Profile] = {
    "por": Profile(
        language="por",
        # "Artigo 5.o" on its own line. The ordinal mark is printed several ways and OCR
        # adds more, so the tail is permissive; the line anchor does the real work.
        #
        # Two forms the first pattern missed, both measured on 4 October 2026 on documents that
        # came out with no provisions: seven decree-laws of 2003 to 2005 whose text layer puts a
        # NON-BREAKING space between the word and the number ("Artigo\u00a01.o"), and a treaty
        # text that writes the word in capitals ("ARTIGO 7"). A space is a space here, whichever
        # code point the PDF used; the frozen text itself is not touched.
        article=re.compile(r"(?m)^[ \t\xa0]*(?:Artigo|ARTIGO)[ \t\xa0]+(\d{1,3})\s*[.º°o⁰]*[ \t\xa0]*$"),
        divisions=(
            ("title", re.compile(r"(?m)^[ \t\xa0]*T[ÍI]TULO\b[^\n]*", re.IGNORECASE)),
            ("chapter", re.compile(r"(?m)^[ \t\xa0]*CAP[ÍI]TULO\b[^\n]*", re.IGNORECASE)),
            ("section", re.compile(r"(?m)^[ \t\xa0]*SEC[ÇC][ÃA]O\b[^\n]*", re.IGNORECASE)),
        ),
        # A Timorese article reads:
        #     Artigo 6.o
        #     Praticas restritivas horizontais      <- the article's title
        #     1. Sao proibidos os acordos ...       <- numbered paragraphs
        #     a) Fixar, de forma direta ...         <- lettered items inside a paragraph
        # so the paragraph is "N." at the line start. Measured on the Competition Law:
        # 86 paragraphs and 98 lettered items. The letters stay inside their paragraph,
        # because an item is not separately citable - the host wants "Art. 26(2)".
        subsection=re.compile(r"(?m)^[ \t\xa0]*(\d{1,2})\.[ \t\xa0]+"),
    ),
    # An ENGLISH EDITION of a law from an economy that writes in articles: the Lao gazette publishes
    # its own English translation of some laws, headed "Article 12" with the title on the same line
    # or the next. It is chosen by what the crawler declared (the file is English, the economy's own
    # language has a profile here), never by reading the text: see cli._segment_for.
    # "Article 12 of this Law" at the start of a wrapped line is a cross-reference, so the words that
    # follow a reference are refused, and so is a heading line that runs on like a sentence.
    ENGLISH_ARTICLES: Profile(
        language="eng",
        article=re.compile(r"(?m)^[ \t\xa0]*Article[ \t\xa0]+(\d{1,3})"
                           r"(?![ \t\xa0]*(?:of|and|or|to|in|on|shall|is|are|above|below|hereof)\b)"
                           r"[.:]?(?:[ \t\xa0]+[^\n]{0,110})?[ \t\xa0]*$"),
        divisions=(
            ("part", re.compile(r"(?m)^[ \t\xa0]*Part[ \t\xa0]+[IVXLC\d]+\b[^\n]*")),
            ("chapter", re.compile(r"(?m)^[ \t\xa0]*Chapter[ \t\xa0]+[IVXLC\d]+\b[^\n]*")),
            ("section", re.compile(r"(?m)^[ \t\xa0]*Section[ \t\xa0]+[IVXLC\d]+\b[^\n]*")),
        ),
        subsection=None,
    ),
    "lao": Profile(
        language="lao",
        article=re.compile("(?m)^[ \t]*ມາດຕາ[ \t]*(\\d{1,3})"),
        divisions=(
            ("part", re.compile("(?m)^[ \t]*ພາກ[^\n]*")),
            ("chapter", re.compile("(?m)^[ \t]*ໝວດ[^\n]*")),
        ),
        subsection=None,     # Lao articles are not sub-numbered in the corpus
    ),
    "zho": Profile(
        language="zho",
        article=re.compile("(?m)^[ \t]*第([一二三四五六七"
                           "八九十百千零〇\\d]+)[条條]"),
        divisions=(
            ("chapter", re.compile("(?m)^[ \t]*第[^\n]{1,12}[章][^\n]*")),
            ("section", re.compile("(?m)^[ \t]*第[^\n]{1,12}[节節][^\n]*")),
        ),
        subsection=None,     # (一)(二) items are parts of the article's own sentence
        numerals="chinese",
        # 法 and 条例 number their provisions 第一条; 决定, 通知, 规定 and 意见 number
        # theirs 一、二、三. Measured on China's corpus: 64 of the 88 documents that
        # produced NOTHING use the second style, some with over fifty numbered items -
        # including the NPC Standing Committee's Decision on Safeguarding Internet
        # Security, which is squarely in scope for this index. The marker must be at the
        # start of a line: "本决定第一条、第二条" inside a sentence is a cross-reference,
        # and it is exactly what a looser pattern would wrongly promote to a heading.
        article_alt=re.compile("(?m)^[ 	]*([一二三四五六七八九十]{1,3})[、．]"),
    ),
}


@dataclass
class _Heading:
    number_as_read: str
    value: int | None
    start: int
    body_start: int
    assigned: int | None = None
    confidence: str = "exact"
    repair: str | None = None
    hierarchy: tuple = field(default_factory=tuple)


def _divisions(text: str, profile: Profile) -> list[tuple[int, str, str]]:
    """(offset, unit, heading text) for every division heading, in document order."""
    found = []
    for unit, pattern in profile.divisions:
        for m in pattern.finditer(text):
            found.append((m.start(), unit, m.group(0).strip()))
    return sorted(found)


def _repair_sequence(headings: list[_Heading]) -> int:
    """Assign each article its number, repairing a misread digit from its position.

    Articles ascend by one. When the number read does not continue the run but the next
    one does, the odd number is an OCR misread and the position is right.
    """
    repaired = 0
    expected: int | None = None
    numbered = [h for h in headings if h.value is not None]
    following = {id(h): numbered[i + 1] if i + 1 < len(numbered) else None
                 for i, h in enumerate(numbered)}
    for h in headings:
        if h.value is None:
            h.confidence = "unverified"
            continue
        nxt = following[id(h)]
        if expected is None:
            h.assigned, expected = h.value, h.value + 1
            continue
        if h.value == expected:
            h.assigned, expected = h.value, h.value + 1
            continue
        if abs(h.value - expected) <= MAX_SEQUENCE_DRIFT:
            # a real gap in the statute: repealed articles leave holes
            h.assigned, expected = h.value, h.value + 1
            continue
        # A big drift is one of two very different things, and the difference is the NEXT
        # number. An OCR misread is isolated: the article after it continues the original
        # run (Lao reads 30 as 90, then 31 follows). A new instrument RESTARTS: the number
        # drops to 1 and a fresh ascending run begins from it.
        #
        # Until 2026-09-23 this branch overrode the text in both cases, and on Timor-Leste,
        # where one gazette issue holds many acts, that renumbered every act after the
        # first: **120,968 of 189,355 provisions - 63.9% - cited a number their own text
        # contradicts**, "Artigo 1" emitted as "Art. 11". A real act cited to the wrong
        # article scores zero, so this was the most damaging line in the stage.
        if nxt is not None and nxt.value == h.value + 1:
            h.assigned, expected = h.value, h.value + 1
            h.confidence = "sequence_restart"
            continue
        h.assigned = expected
        h.confidence = "sequence_repaired"
        h.repair = "ascending_sequence"
        expected += 1
        repaired += 1
    return repaired


def segment_civil(text: str, language: str) -> SegmentResult:
    """Segment a statute in one of the civil-law / CJK traditions."""
    profile = PROFILES.get(language)
    if profile is None:
        raise KeyError(f"no segmenter profile for language {language!r}; "
                       f"known: {', '.join(sorted(PROFILES))}")

    matches = list(profile.article.finditer(text))
    alt_used = False
    if not matches and profile.article_alt is not None:
        alt = list(profile.article_alt.finditer(text))
        if len(alt) >= profile.alt_min_matches:
            matches, alt_used = alt, True
            log.info("no %s article markers; using the ordinal style instead (%d items)",
                     profile.language, len(alt))
    if not matches:
        return SegmentResult(spans=[], n_sections=0, dropped_toc_candidates=0)

    headings: list[_Heading] = []
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        raw = m.group(1)
        value = chinese_numeral(raw) if profile.numerals == "chinese" else (
            int(raw) if raw.isdigit() else None)
        headings.append(_Heading(number_as_read=raw, value=value,
                                 start=m.start(), body_start=m.end()))
        headings[-1].body_end = end                                  # type: ignore[attr-defined]

    # The contents block: a run of headings with almost nothing between them.
    #
    # Two guards, because a length test alone is not enough. First the threshold is the one
    # for this script. Second, a heading is only a contents candidate if it sits inside the
    # document's actual contents block - the run before the first substantial body - so a
    # genuinely short article late in the statute is kept. A commencement article is the
    # shortest provision in most statutes and it is never in the table of contents.
    threshold = min_body_chars(profile.language)
    bodies = [len(text[h.body_start:h.body_end].strip())              # type: ignore[attr-defined]
              for h in headings]
    # The positional guard applies ONLY where it was measured, which is Chinese. On Lao it
    # recovered 999 provisions and let cross-references in with them - "ມາດຕາ 51." (9
    # characters) and "ມາດຕາ 64 ຂໍ 6 ຂອງກົດຫາຍສະບັບນີ" ("Article 64 point 6 of this law")
    # are mentions inside another article, which OCR line breaks push to the start of a line
    # where the pattern matches. The 120-character default was filtering them by accident.
    # Lao and Portuguese keep the behaviour that produced their verified output; changing
    # them needs its own measurement, not an analogy with Chinese (see OPEN_ISSUES.md).
    positional = profile.language in POSITIONAL_CONTENTS_GUARD
    first_substantial = (next((i for i, n in enumerate(bodies) if n >= threshold),
                              len(headings)) if positional else len(headings))

    dropped = 0
    kept: list[_Heading] = []
    for index, h in enumerate(headings):
        if bodies[index] < threshold and (not positional or index < first_substantial):
            dropped += 1
            continue
        kept.append(h)
    if not kept:
        return SegmentResult(spans=[], n_sections=0, dropped_toc_candidates=dropped)

    repaired = _repair_sequence(kept)
    divisions = _divisions(text, profile)

    spans: list[Span] = []
    for h in kept:
        # the most recent division at EACH level, outermost first - not simply the last
        # two headings, which on a run of chapters gives "CAPITULO II, CAPITULO III"
        current: dict[str, str] = {}
        for offset, unit, heading in divisions:
            if offset < h.start:
                current[unit] = heading[:60]
        order = [unit for unit, _ in profile.divisions]
        context = tuple(current[unit] for unit in order if unit in current)
        number = str(h.assigned if h.assigned is not None else h.number_as_read)
        citation = profile.cite(number)
        body_end = h.body_end                                        # type: ignore[attr-defined]
        # the line after the number is the article's own title, which is what a reader
        # needs to recognise the provision: "Artigo 6.o / Praticas restritivas horizontais"
        first_line = text[h.body_start:body_end].strip().split("\n", 1)[0].strip()
        title = first_line if 0 < len(first_line) <= 120 else None
        span = Span(article_section=citation, unit="section",
                    char_start=h.start, char_end=body_end,
                    heading=title, hierarchy=context + (citation,))
        span.number_as_read = h.number_as_read                       # type: ignore[attr-defined]
        span.citation_confidence = h.confidence                      # type: ignore[attr-defined]
        span.citation_repair_method = h.repair                       # type: ignore[attr-defined]
        spans.append(span)

        if profile.subsection is not None:
            body = text[h.body_start:body_end]
            subs = list(profile.subsection.finditer(body))
            for j, sm in enumerate(subs):
                sub_end = subs[j + 1].start() if j + 1 < len(subs) else len(body)
                if sub_end - sm.start() < 40:
                    continue
                sub_citation = profile.cite(number, sm.group(1))
                sub = Span(article_section=sub_citation, unit="subsection",
                           char_start=h.body_start + sm.start(),
                           char_end=h.body_start + sub_end,
                           heading=None,
                           hierarchy=context + (citation, sub_citation))
                sub.number_as_read = h.number_as_read                # type: ignore[attr-defined]
                sub.citation_confidence = h.confidence               # type: ignore[attr-defined]
                sub.citation_repair_method = h.repair                # type: ignore[attr-defined]
                spans.append(sub)

    log.info("segmented (%s): %d articles, %d spans, %d contents entries dropped%s",
             language, len(kept), len(spans), dropped,
             f", {repaired} article numbers repaired from sequence" if repaired else "")
    return SegmentResult(spans=spans, n_sections=len(kept), dropped_toc_candidates=dropped)
