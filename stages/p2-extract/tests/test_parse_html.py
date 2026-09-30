"""Lane A per-portal parser (legislation.gov.au shape)."""

import pytest

from rdtii_p2 import parse_html

AU_HTML = """
<html><body>
<p class="TOC5"><a href="#x">1 Short title</a></p>
<p id="navPoint_1" class="ActHead2"><a id="_Toc100"><span class="CharPartNo">Chapter&nbsp;1</span><span>—</span><span class="CharPartText">Codification</span></a></p>
<p id="navPoint_2" class="ActHead3"><a id="_Toc101"><span class="CharDivNo">Part&nbsp;2.1</span><span>—</span><span class="CharDivText">Purpose</span></a></p>
<p id="navPoint_3" class="ActHead5"><a id="_Toc110"><span class="CharSectno">16.1</span><span>&nbsp; </span><span>Consent required</span></a></p>
<p class="subsection"><span>(1)</span><span> Proceedings must not be commenced without written consent if:</span></p>
<p class="paragraph"><span>(a)</span><span> the first condition applies; or</span></p>
<p class="subsection"><span>(2)</span><span> A second subsection body.</span></p>
<p id="navPoint_4" class="ActHead5"><a id="_Toc111"><span class="CharSectno">16.2</span><span>&nbsp; </span><span>Next section</span></a></p>
<p class="subsection"><span>Body of the next section without numbered subsections.</span></p>
</body></html>
"""


@pytest.fixture
def parsed(tmp_path):
    path = tmp_path / "au.html"
    path.write_text(AU_HTML, encoding="utf-8")
    return parse_html.parse(path, "https://www.legislation.gov.au/C2004A04868/latest/text")


def test_sections_and_anchors(parsed):
    sections = [s for s in parsed.spans if s.unit == "section"]
    assert [s.article_section for s in sections] == ["s.16.1", "s.16.2"]
    assert parsed.anchors["s.16.1"] == "_Toc110"
    assert parsed.anchors["s.16.1(1)"] == "_Toc110"


def test_hierarchy_path(parsed):
    section = next(s for s in parsed.spans if s.article_section == "s.16.1")
    assert any("Chapter" in level for level in section.hierarchy)
    assert any("Part" in level for level in section.hierarchy)
    assert section.heading == "Consent required"


def test_span_offsets_are_exact(parsed):
    span = next(s for s in parsed.spans if s.article_section == "s.16.1(1)")
    body = parsed.text[span.char_start:span.char_end]
    assert body.startswith("(1) Proceedings must not be commenced")
    assert "(2) A second subsection" not in body
    span2 = next(s for s in parsed.spans if s.article_section == "s.16.1(2)")
    assert parsed.text[span2.char_start:span2.char_end].startswith("(2) A second subsection")


def test_toc_and_nav_excluded(parsed):
    assert parsed.text.count("Short title") == 0, "TOC5 lines are not body text"


def test_unknown_portal_refuses():
    with pytest.raises(NotImplementedError):
        parse_html.parse(__import__("pathlib").Path("x.html"), "https://unknown.example.com/law")
