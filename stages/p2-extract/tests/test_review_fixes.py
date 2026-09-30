"""Regression tests for the adversarial-review findings (stage-2 fix set)."""

from rdtii_p2 import emit, extract_fields, parse_html
from rdtii_p2.normalize import normalize_pages
from rdtii_p2.segment import segment

STATUTE = """PART 1
PRELIMINARY
Short title
1. This Act is the Test Act 2026.
Interpretation
2.—(1) In this Act, a term has its defined meaning.
(2) The Former Commission is dissolved.
Division 2 — Special rules
Application
3. This Act binds the Government.
FIRST SCHEDULE
COLLECTED MATTERS
Schedule body text here.
"""


def test_next_sections_heading_excluded_from_span():
    result = segment(STATUTE)
    s1 = result.find("s.1")
    body = STATUTE[s1.char_start:s1.char_end]
    assert "Interpretation" not in body, "next section's heading must not bleed into s.1"
    assert body.rstrip().endswith("Test Act 2026.")


def test_division_heading_closes_section():
    result = segment(STATUTE)
    s2 = result.find("s.2(2)")
    body = STATUTE[s2.char_start:s2.char_end]
    assert "Division 2" not in body
    assert "Application" not in body


def test_schedule_block_closes_last_section():
    result = segment(STATUTE)
    s3 = result.find("s.3")
    body = STATUTE[s3.char_start:s3.char_end]
    assert "FIRST SCHEDULE" not in body
    assert "Schedule body text" not in body


def test_short_provision_is_emitted_not_dropped():
    # 'The Former Commission is dissolved.' (35 chars) is a real provision;
    # contract 3.2 forbids dropping it (review finding #2)
    result = segment(STATUTE)
    span = result.find("s.2(2)")
    start, end = extract_fields.snippet_offsets(STATUTE, span)
    assert end - start >= extract_fields.SNIPPET_MIN_CHARS
    assert STATUTE[start:end].startswith("The Former Commission is dissolved.")


def test_ordinal_schedule_continued_header_is_always_furniture():
    pages = ["some provision text\nNINTH SCHEDULE — continued\nrelating to the investigation"]
    doc = normalize_pages(pages)
    assert "SCHEDULE — continued" not in doc.text
    assert "some provision text" in doc.text
    assert "relating to the investigation" in doc.text


def test_merge_removes_rows_for_regressed_docs(tmp_path):
    emit.write_provisions(tmp_path, [
        {"doc_id": "sg-a-001", "provision_id": "sg-a-001#s.1"},
        {"doc_id": "sg-b-001", "provision_id": "sg-b-001#s.1"},
    ])
    # second run processed BOTH docs but doc b regressed to zero records
    emit.write_provisions(tmp_path, [{"doc_id": "sg-a-001", "provision_id": "sg-a-001#s.1"}],
                          processed_doc_ids={"sg-a-001", "sg-b-001"})
    with open(tmp_path / "provisions.jsonl", encoding="utf-8") as fh:
        docs = [line for line in fh if "sg-b-001" in line]
    assert not docs, "regressed doc's stale rows must be removed"


def test_remove_stale_by_law(tmp_path):
    emit.write_by_law_empty(tmp_path, "sg-a-001")
    assert (tmp_path / "by_law" / "sg-a-001.json").is_file()
    emit.remove_stale_doc_artifacts(tmp_path, "sg-a-001")
    assert not (tmp_path / "by_law" / "sg-a-001.json").is_file()


DUP_HTML = """
<html><body>
<p class="ActHead5"><a id="_T1"><span class="CharSectno">3</span><span> </span><span>The Code</span></a></p>
<p class="subsection"><span>The Schedule has effect as law.</span></p>
<p class="ActHead1"><a id="_T2"><span class="CharChapNo">Schedule</span><span>—</span><span class="CharChapText">The Code</span></a></p>
<p class="ActHead4"><a id="_T3"><span class="CharDivNo">Division 1</span><span>—</span><span class="CharDivText">General</span></a></p>
<p class="ActHead4"><a id="_T4"><span class="CharDivNo">Subdivision A</span><span>—</span><span class="CharDivText">Basics</span></a></p>
<p class="ActHead5"><a id="_T5"><span class="CharSectno">3</span><span> </span><span>Duplicate number</span></a></p>
<p class="subsection"><span>(2AA) A multi-letter subsection marker.</span></p>
<p class="Compilation"><span>Substantive text in an unknown class must be kept.</span></p>
</body></html>
"""


def _parse_dup(tmp_path):
    path = tmp_path / "dup.html"
    path.write_text(DUP_HTML, encoding="utf-8")
    return parse_html.parse(path, "https://www.legislation.gov.au/x/latest/text")


def test_duplicate_section_numbers_disambiguated(tmp_path):
    doc = _parse_dup(tmp_path)
    citations = [s.article_section for s in doc.spans if s.unit == "section"]
    assert len(citations) == len(set(citations)), f"colliding citations: {citations}"
    assert "s.3" in citations
    assert doc.anchors["s.3"] == "_T1"


def test_subdivision_does_not_evict_division(tmp_path):
    doc = _parse_dup(tmp_path)
    dup = [s for s in doc.spans if s.unit == "section"][1]
    assert any(level.startswith("Division 1") for level in dup.hierarchy), dup.hierarchy
    assert any(level.startswith("Subdivision A") for level in dup.hierarchy)


def test_multiletter_subsection_marker(tmp_path):
    doc = _parse_dup(tmp_path)
    subs = [s.article_section for s in doc.spans if s.unit == "subsection"]
    assert any("(2AA)" in c for c in subs), subs


def test_unknown_class_body_text_kept(tmp_path):
    doc = _parse_dup(tmp_path)
    assert "Substantive text in an unknown class must be kept." in doc.text
