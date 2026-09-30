"""`_full_section` must find a section heading in the language the document is written in.

The heading forms were written when the run was Singapore, Malaysia and Australia: `26.—(1)`,
`PART IV`, `Division 3`, `Schedule`. Nothing in them matches 第九条, Artigo 15.º or ມາດຕາ 44, and the
migration to six economies never reached them. The failure is silent by construction: when no
heading matches, `_full_section` falls back to a window starting 6,000 characters before the
provision, so the column still fills -- with the wrong text. For a provision near the top of a short
instrument that window starts at the document's first article, which is how a Chinese row came to
show Articles 1-3 beside an English gloss of Article 9.

Measured against the source text on 29 September 2026: the Chinese form matches 49 of 60 sampled
documents, Portuguese 31 of 60 and Lao 38 of 60. The misses are documents with no article structure
(an NPC Standing Committee "decision" is continuous prose) or OCR damage so bad the script did not
survive -- not pattern failures.

This column is reviewer context, never filed evidence: the submitted snippet is byte-anchored
elsewhere. So a wrong extract misleads a human rather than corrupting the submission, which is
exactly why it survived a migration that checked the evidence path.
"""
from __future__ import annotations

import pytest

from src.p3map.output.excel_export import _HEADING_FORMS, _section_re, section_bounds


@pytest.mark.parametrize("economy,line", [
    ("CN", "第九条 任何组织、个人不得"),
    ("CN", "第 9 条 任何组织"),           # spaced, as some sources render it
    ("CN", "第三章 监督管理"),             # the coarser chapter boundary
    ("TL", "Artigo 15.º"),
    ("TL", "Artigo 21"),
    ("TL", "Art. 21"),
    ("TL", "CAPÍTULO III"),
    ("TL", "SECÇÃO VII"),
    ("TL", "TÍTULO II"),
    ("LA", "ມາດຕາ 44 ການລາຍງານປະຈໍາປີ"),
    ("SG", "26.—(1) Any person who"),
    ("SG", "22A.(1) Despite"),
    ("AU", "PART IV"),
    ("MY", "Division 3"),
    ("AU", "Schedule 1"),
])
def test_a_heading_in_the_document_s_own_language_is_found(economy, line):
    assert _section_re(economy).search(line), f"{economy}: {line!r} is a section start"


@pytest.mark.parametrize("economy,line", [
    ("TL", "just a sentence of ordinary prose"),
    ("CN", "为了保护网络信息安全，特作如下决定："),   # a preamble, not a heading
    ("SG", "the parties may agree otherwise"),
])
def test_ordinary_prose_is_not_mistaken_for_a_heading(economy, line):
    assert not _section_re(economy).search(line)


def test_the_english_forms_still_apply_to_every_economy():
    """Unioned, not switched. A Timorese instrument can carry an English heading in a translated
    annex, and a document whose economy we have no form for must keep the old behaviour rather than
    matching nothing at all."""
    for economy in ("CN", "LA", "TL", "SG", "ZZ", ""):
        assert _section_re(economy).search("26.—(1) Any person"), economy
        assert _section_re(economy).search("PART IV"), economy


def test_one_economy_s_form_does_not_leak_into_another():
    """A Chinese heading inside a Singapore document is not a Singapore section start; if it were,
    the union would be pointless and the extract would split on stray CJK."""
    assert not _section_re("SG").search("第九条 任何组织")
    assert not _section_re("AU").search("ມາດຕາ 44")


def test_the_pattern_is_anchored_to_the_start_of_a_line():
    """A cross-reference mid-sentence must not be read as the start of a new section."""
    for economy, text in (("CN", "依照第九条的规定"), ("TL", "nos termos do Artigo 15"),
                          ("SG", "subject to 26.—(1) above")):
        assert not _section_re(economy).search(text), economy


def test_every_form_compiles_and_the_default_is_present():
    assert "" in _HEADING_FORMS, "the English default must exist -- it is unioned into every economy"
    for economy in _HEADING_FORMS:
        _section_re(economy or "ZZ")          # raises on a bad pattern


# --------------------------------------------------------------------- the walk-back boundary


CN_DOC = ("\u5e8f\u8a00\u524d\u8a00\n"
          "\u7b2c\u516b\u6761\u3000\u7b2c\u516b\u6761\u7684\u5185\u5bb9\u5728\u8fd9\u91cc\u3002\n"
          "\u7b2c\u4e5d\u6761\u3000\u7b2c\u4e5d\u6761\u7684\u5185\u5bb9\u5728\u8fd9\u91cc\u3002\n"
          "\u7b2c\u5341\u6761\u3000\u7b2c\u5341\u6761\u7684\u5185\u5bb9\u3002\n")
ART9 = CN_DOC.index("\u7b2c\u4e5d\u6761")
ART10 = CN_DOC.index("\u7b2c\u5341\u6761")


def test_a_heading_exactly_at_the_offset_is_the_section_start():
    """The bug this replaces: `finditer(text, lo, s + 1)` required a heading starting AT s to fit
    inside the window, so a three-character 第九条 at s was skipped and the extract began at 第八条 --
    one article early. snippet_char_start lands exactly on the heading in 397 of 400 sampled Chinese
    provisions, so this was the ordinary case.
    """
    start, end = section_bounds(CN_DOC, ART9, ART9 + 5, _section_re("CN"))
    assert start == ART9, "the extract must begin at the labelled article, not the one before it"
    assert CN_DOC[start:end].startswith("\u7b2c\u4e5d\u6761")
    assert "\u7b2c\u516b\u6761" not in CN_DOC[start:end], "and must not include the previous article"


def test_the_extract_stops_at_the_next_heading():
    start, end = section_bounds(CN_DOC, ART9, ART9 + 5, _section_re("CN"))
    assert end <= ART10
    assert "\u7b2c\u5341\u6761" not in CN_DOC[start:end]


def test_an_offset_inside_the_article_body_still_finds_its_heading():
    inside = ART9 + 6
    start, _ = section_bounds(CN_DOC, inside, inside + 2, _section_re("CN"))
    assert start == ART9


def test_no_heading_behind_the_offset_snaps_to_a_line_start_not_mid_word():
    """A document with no recognisable headings must not begin the extract mid-word."""
    text = "aaaa bbbb cccc\ndddd eeee ffff\ngggg hhhh"
    s = text.index("eeee")
    start, end = section_bounds(text, s, s + 4, _section_re("SG"), back=10, fwd=10)
    assert text[start:end].startswith("dddd"), "snapped to the line start"


def test_the_span_is_never_inverted():
    """end < start would silently produce an empty cell; a reviewer cannot tell that from 'no text'."""
    for s in (0, 5, len(CN_DOC) - 1):
        start, end = section_bounds(CN_DOC, s, s, _section_re("CN"))
        assert end >= start
