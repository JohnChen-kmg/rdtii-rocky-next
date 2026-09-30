"""Normalization invariants - these freeze offsets forever; regressions here
invalidate every shipped offset, so they are locked hard."""

from rdtii_p2.normalize import normalize_pages


def test_page_offsets_round_trip():
    pages = [
        "PART 1\nPRELIMINARY\n1. Short title\nThis Act is the Test Act.",
        "2. Interpretation\nIn this Act, unless the context otherwise requires.",
        "3. Application\nThis Act binds the Government.",
    ]
    doc = normalize_pages(pages)
    assert len(doc.page_offsets) == 3
    for page_number, offset in doc.page_offsets:
        # each recorded offset lands exactly on that page's first character
        first_line = pages[page_number - 1].split("\n", 1)[0]
        assert doc.text[offset:offset + len(first_line)] == first_line
    assert doc.page_for_offset(doc.page_offsets[2][1]) == 3
    assert doc.page_for_offset(0) == 1


def test_furniture_stripped_and_logged():
    footer = "Singapore Statutes Online   Current version as at 01 Jun 2026"
    pages = [f"Section {i}. Some provision text here.\n{footer}\n{i + 10}" for i in range(1, 7)]
    doc = normalize_pages(pages)
    assert footer not in doc.text
    assert any("Statutes Online" in line for line in doc.furniture_removed)
    # bare page-number lines are gone too
    assert "\n11\n" not in doc.text


def test_dehyphenation_within_and_across_pages():
    pages = [
        "The Commissioner may authorise a trans-\nfer of data.\nThe word conti-",
        "nues on the next page.",
    ]
    doc = normalize_pages(pages)
    assert "transfer of data" in doc.text
    assert "continues on the next page" in doc.text


def test_subsection_markers_never_unwrapped():
    pages = ["26.—(1) An organisation must not transfer\n(2) The Minister may act.\n(a) first item"]
    doc = normalize_pages(pages)
    assert "\n(2) The Minister" in doc.text
    assert "\n(a) first item" in doc.text


def test_fffd_structural_repair():
    pages = [
        "PART 6 � CARE OF PERSONAL DATA\n"
        "Transfer of personal data outside Singapore\n"
        "26.�(1) An organisation must not transfer data.\n"
        "This Part applies to�\n(a) any person who processes data."
    ]
    doc = normalize_pages(pages)
    assert "26.—(1)" in doc.text
    assert "PART 6 — CARE" in doc.text
    assert "applies to—" in doc.text
    assert doc.fffd_remaining == 0


def test_fffd_unknown_position_left_honest():
    pages = ["The term �controller� is defined elsewhere." * 1]
    doc = normalize_pages(pages)
    # lost curly quotes are NOT guessed - left as-is and counted
    assert doc.fffd_remaining == 2
