"""T2 golden tests: hierarchy-aware segmentation.

The synthetic statute test always runs; the real-corpus SG PDPA golden test
runs whenever HANDOFF1_DIR resolves (dev box), and the in-repo SG
Telecommunications Act sample keeps a real SSO-shaped document in CI.
"""

import pytest

from conftest import HANDOFF1_DIR, SAMPLE_DOCS
from rdtii_p2 import parse_pdf_native, segment
from rdtii_p2.normalize import normalize_pages

SYNTHETIC = """ARRANGEMENT OF SECTIONS
1. Short title
2. Interpretation
26. Transfer of personal data outside Singapore
27. Access to personal data
PART 1
PRELIMINARY
Short title
1. This Act is the Test Act 2026.
Interpretation
2.—(1) In this Act, unless the context otherwise requires.
(2) A second subsection with content.
PART 6 — CARE OF PERSONAL DATA
Transfer of personal data outside Singapore
26.—(1) An organisation must not transfer any personal data to a country or
territory outside Singapore except in accordance with prescribed requirements.
(2) The Minister may make regulations for this purpose.
Access to personal data
27. On request of an individual, an organisation must provide access.
"""


def test_synthetic_statute_golden():
    result = segment.segment(SYNTHETIC)
    span = result.find("s.26(1)")
    assert span is not None, "s.26(1) must be found"
    text = SYNTHETIC[span.char_start:span.char_end]
    assert text.startswith("26.—(1) An organisation must not transfer")
    assert "The Minister" not in text, "subsection (2) must not leak into (1)"
    assert span.heading == "Transfer of personal data outside Singapore"
    assert span.hierarchy[-2:] == ("s.26", "(1)")
    assert any("Part 6" in level for level in span.hierarchy)
    # TOC lines mirroring body headings must not create phantom early sections
    body_26 = result.find("s.26")
    assert body_26.char_start > SYNTHETIC.index("PART 1")


def test_subsection_2_boundaries():
    result = segment.segment(SYNTHETIC)
    span = result.find("s.26(2)")
    assert span is not None
    text = SYNTHETIC[span.char_start:span.char_end]
    assert text.startswith("(2) The Minister may make regulations")
    assert "Access to personal data" not in text or "27." not in text


@pytest.mark.skipif(
    not (HANDOFF1_DIR / "manifest.csv").is_file(),
    reason="P1 corpus not available on this machine",
)
def test_real_sg_pdpa_s26_golden():
    import csv

    with open(HANDOFF1_DIR / "manifest.csv", encoding="utf-8-sig", newline="") as fh:
        row = next(r for r in csv.DictReader(fh) if r["doc_id"] == "sg-pdpa2012-001")
    pdf_path = HANDOFF1_DIR / row["local_path"]
    doc = normalize_pages(parse_pdf_native.extract_pages(pdf_path))
    result = segment.segment(doc.text)

    span = result.find("s.26(1)")
    assert span is not None
    text = doc.text[span.char_start:span.char_end]
    assert "must not transfer any personal data to a country or territory outside Singapore" in text
    assert span.heading == "Transfer of personal data outside Singapore"
    assert result.n_sections > 40, "PDPA 2020 Rev Ed has far more than 40 sections"
    assert result.dropped_toc_candidates > 0, "front TOC must be suppressed"


@pytest.mark.skipif(
    not (SAMPLE_DOCS / "General" / "Telecommunications Act 1999.pdf").is_file(),
    reason="sample_docs not present",
)
def test_sample_sg_telecom_act_sections():
    pdf_path = SAMPLE_DOCS / "General" / "Telecommunications Act 1999.pdf"
    doc = normalize_pages(parse_pdf_native.extract_pages(pdf_path))
    result = segment.segment(doc.text)
    assert result.n_sections > 60, "Telecom Act has sections 1-98"
    span = result.find("s.26(1)")
    assert span is not None
    body = doc.text[span.char_start:span.char_end]
    assert "must not enter into or enforce any agreement" in body
    assert span.heading is not None and "exclusive agreement" in span.heading.lower()
