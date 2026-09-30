"""T3/T3b invariants: URL composition, marker trimming, grounded metadata."""

from rdtii_p2 import extract_fields as ef
from rdtii_p2.segment import segment


def test_compose_url_query_style():
    assert ef.compose_url("https://sso.agc.gov.sg/Act/PDPA2012", "?ProvIds=pr26-", "query") \
        == "https://sso.agc.gov.sg/Act/PDPA2012?ProvIds=pr26-"
    # base already has a query string -> & join (contract 2.4)
    assert ef.compose_url("https://sso.agc.gov.sg/Act/PDPA2012?ViewType=Pdf", "?ProvIds=pr26-", "query") \
        == "https://sso.agc.gov.sg/Act/PDPA2012?ViewType=Pdf&ProvIds=pr26-"


def test_compose_url_fragment_and_none():
    assert ef.compose_url("https://www.legislation.gov.au/C2004A04868/latest/text", "#sec.6", "fragment") \
        == "https://www.legislation.gov.au/C2004A04868/latest/text#sec.6"
    assert ef.compose_url("https://example.gov", None, None) == "https://example.gov"
    assert ef.compose_url("https://example.gov", "?x=1", "none") == "https://example.gov"


TEXT = """PART 6 — CARE OF PERSONAL DATA
Transfer of personal data outside Singapore
26.—(1) An organisation must not transfer any personal data to a country or
territory outside Singapore except in accordance with prescribed requirements.
(2) The Commission may exempt an organisation from any requirement.
"""


def test_snippet_offsets_trim_marker():
    result = segment(TEXT)
    span = result.find("s.26(1)")
    start, end = ef.snippet_offsets(TEXT, span)
    assert TEXT[start:end].startswith("An organisation must not transfer")
    assert not TEXT[start:end].endswith("\n")
    sub2 = result.find("s.26(2)")
    start2, end2 = ef.snippet_offsets(TEXT, sub2)
    assert TEXT[start2:end2].startswith("The Commission may exempt")


def test_law_name_prefers_short_title_sentence():
    text = "PERSONAL DATA PROTECTION\nACT 2012\n1. This Act is the Personal Data Protection Act 2012."
    field = ef.ground_law_name(text, "Personal Data Protection Act 2012")
    assert field.value == "Personal Data Protection Act 2012"
    assert text[field.char_start:field.char_end] == field.value


def test_law_name_null_when_ungrounded():
    assert ef.ground_law_name("completely unrelated text", "Imaginary Act 2099").value is None


def test_law_number_skips_amendment_contexts():
    text = (
        "Compilation No. 174\n"
        "Includes amendments: Act No. 53, 2026\n"
        "Some text [Act 40 of 2020 wef 01/10/2022] more text\n"
        "This Act is the Test Act, Act 26 of 2012 as enacted.\n"
    )
    field = ef.ground_law_number(text, "Act 26 of 2012")
    assert field.value == "Act 26 of 2012"
    # the amending-act mention and the wef bracket were both skipped
    assert field.char_start > text.index("as enacted") - 40


def test_law_number_null_rather_than_amending_act():
    text = "Compilation No. 174\nIncludes amendments: Act No. 53, 2026\nbody text follows here\n"
    assert ef.ground_law_number(text, None).value is None


def test_last_amended_patterns():
    sg = "This revised edition incorporates all amendments up to and including 1 December 2021."
    assert ef.ground_last_amended(sg).value == "1 December 2021"
    au = "Compilation No. 174\nIncludes amendments: Act No. 53, 2026\n"
    field = ef.ground_last_amended(au)
    assert field.value == "2026"
    assert au[field.char_start:field.char_end] == "2026"
    assert ef.ground_last_amended("no amendment statement here").value is None


def test_candidate_spans_prefers_subsections():
    result = segment(TEXT)
    candidates = ef.candidate_spans(result)
    citations = [span.article_section for span in candidates]
    assert "s.26(1)" in citations and "s.26(2)" in citations
    assert "s.26" not in citations, "section with subsections is not itself a candidate"
