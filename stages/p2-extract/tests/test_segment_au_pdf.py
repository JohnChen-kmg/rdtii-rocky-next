"""AU OPC no-dot heading fallback ("5B Extra-territorial operation of Act").

The fallback must engage only when the dot pattern finds (nearly) nothing, put
the section's quotable content AFTER the same-line heading, and never treat a
line-start date as a section.
"""

from rdtii_p2 import extract_fields as ef
from rdtii_p2.segment import segment

AU_TEXT = """Privacy Act 1988
Contents
1 Short title.............................................................................................1
2 Commencement ..................................................................................1
5A Extension to external Territories.........................................................3
5B Extra-territorial operation of Act ........................................................3
1 Short title
This Act may be cited as the Privacy Act 1988 and it binds the Crown in each
of its capacities under the arrangements set out in this compilation text.
2 Commencement
This Act commences on a day to be fixed by Proclamation, and different days
may be fixed for the commencement of different provisions of this Act.
5A Extension to external Territories
(1) This Act extends to all external Territories, subject to the modifications
that are prescribed by the regulations from time to time for that purpose.
(2) This section does not apply to Schedule 2 or to any instrument under it.
5B Extra-territorial operation of Act
Agencies
(1) This Act extends to an act done, or practice engaged in, outside Australia
and the external Territories by an agency, in the circumstances prescribed.
6 June 2026
(2) The reference above is a date fragment inside the provision body, not a
section heading, and it must never split this provision into two records.
"""

SG_TEXT = """PART 6 — CARE OF PERSONAL DATA
Transfer of personal data outside Singapore
26.—(1) An organisation must not transfer any personal data to a country or
territory outside Singapore except in accordance with prescribed requirements.
(2) The Commission may exempt an organisation from any requirement.
"""


def test_au_fallback_finds_no_dot_sections():
    result = segment(AU_TEXT)
    citations = {span.article_section for span in result.spans}
    assert {"s.1", "s.2", "s.5A", "s.5B", "s.5A(1)", "s.5A(2)", "s.5B(1)"} <= citations


def test_au_heading_is_inline_and_content_excludes_it():
    result = segment(AU_TEXT)
    s5b = result.find("s.5B")
    assert s5b.heading == "Extra-territorial operation of Act"
    s1 = result.find("s.1")
    assert AU_TEXT[s1.char_start:s1.char_end].startswith("This Act may be cited"), \
        "section content starts after the same-line heading"


def test_au_line_start_date_is_not_a_section():
    result = segment(AU_TEXT)
    assert result.find("s.6") is None, "'6 June 2026' must not become a section"
    s5b1 = result.find("s.5B(1)")
    snippet = AU_TEXT[s5b1.char_start:s5b1.char_end]
    assert "6 June 2026" in snippet, "the date line stays inside the provision"


def test_au_span_ends_before_next_section_line():
    result = segment(AU_TEXT)
    s5a2 = result.find("s.5A(2)")
    assert "5B Extra-territorial" not in AU_TEXT[s5a2.char_start:s5a2.char_end]


TABLE_TEXT = """Contents
1 First thing.............................................................................1
2 Definitions.............................................................................1
3 Third thing.............................................................................2
1 First thing
This section is about the first thing and it has a reasonable amount of body
text so that the body sequence is clearly wider than the contents block.
2 Definitions
In this Act, the following table sets out who is the responsible person:
1 A Department The Secretary of the Department
2 A federal court The principal registrar of the court
3 A body corporate The chief executive officer of the body
This trailing sentence still belongs to the definitions section of the Act.
3 Third thing
The third section follows the numbered table and must still be found intact.
Endnotes
2 Definitions am No. 5, 2020
"""


def test_au_numbered_table_rows_do_not_split_or_duplicate_sections():
    result = segment(TABLE_TEXT)
    citations = [span.article_section for span in result.spans if span.unit == "section"]
    assert citations == ["s.1", "s.2", "s.3"], citations
    s2 = result.find("s.2")
    body = TABLE_TEXT[s2.char_start:s2.char_end]
    assert "principal registrar" in body, "table rows stay inside the section"
    assert result.find("s.2").heading == "Definitions", "endnote echo ignored"


def test_sg_text_never_engages_au_fallback():
    result = segment(SG_TEXT)
    assert result.find("s.26(1)") is not None
    start, end = ef.snippet_offsets(SG_TEXT, result.find("s.26(1)"))
    assert SG_TEXT[start:end].startswith("An organisation must not transfer")
