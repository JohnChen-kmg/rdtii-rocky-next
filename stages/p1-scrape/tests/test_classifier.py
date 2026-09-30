"""T3: §2.3 classifier — html | pdf_native | pdf_scanned."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from p1_scrape.classifier import classify, is_valid_pdf

# Host-provided sample legislations. ESCAP's material, so it is not in this repository
# and there is no default path: a reviewer with their own copy points
# RDTII_SAMPLE_LEGISLATION at it and these two tests run against real files. Unset —
# the normal case on a clean clone — they skip, and the committed fixtures in
# tests/fixtures/ already cover the same classifier branches.
_HOST = Path(os.getenv("RDTII_SAMPLE_LEGISLATION", ""))
_NATIVE_REAL = _HOST / "General" / "PERSONAL DATA PROTECTION ACT 2010.pdf"
_SCANNED_REAL = _HOST / "PDF of scanned documents" / "Pakistan_PECA.pdf"

# Static committed fixtures (tests/fixtures/) — no PDF library needed to build them.
_FIXTURES = Path(__file__).parent / "fixtures"


def _native_pdf_bytes() -> bytes:
    """One page with a real text layer (20 lines ≈ 1.2k chars)."""
    return (_FIXTURES / "native_text.pdf").read_bytes()


def _scanned_pdf_bytes() -> bytes:
    """A PDF page with no text layer (mimics an image-only scan → 0 chars/page)."""
    return (_FIXTURES / "scanned_blank.pdf").read_bytes()


def test_html_is_html():
    c = classify(b"<!DOCTYPE html><html><body>Act text</body></html>",
                 content_type="text/html; charset=utf-8")
    assert c.source_type == "html"
    assert c.pdf_is_scanned is None
    assert c.page_count is None


def test_native_pdf_is_native():
    c = classify(_native_pdf_bytes(), content_type="application/pdf")
    assert c.source_type == "pdf_native"
    assert c.pdf_is_scanned is False
    assert c.page_count == 1
    assert c.mean_chars_per_page >= 100


def test_scanned_pdf_is_scanned():
    c = classify(_scanned_pdf_bytes(), content_type="application/pdf")
    assert c.source_type == "pdf_scanned"
    assert c.pdf_is_scanned is True
    assert c.mean_chars_per_page < 100


def test_pdf_detected_by_magic_without_content_type():
    c = classify(_native_pdf_bytes(), content_type="")
    assert c.source_type == "pdf_native"


def test_mislabeled_non_pdf_never_raises():
    """LOM's 5-byte 'false' sentinel is served as application/pdf; classify must not
    crash the crawl (regression for pymupdf.FileDataError killing a full-corpus run)."""
    c = classify(b"false", content_type="application/pdf")
    assert c.source_type == "html"        # no %PDF magic → treated as a non-PDF response
    assert not is_valid_pdf(b"false")


def test_corrupt_pdf_with_magic_is_scanned():
    """Bytes that start with %PDF- but won't open → kept as scanned (raw bytes preserved)."""
    c = classify(b"%PDF-1.4\n<<garbage>>", content_type="application/pdf")
    assert c.source_type == "pdf_scanned"
    assert c.pdf_is_scanned is True
    assert c.page_count is None


@pytest.mark.skipif(not _NATIVE_REAL.exists(), reason="host native sample not present")
def test_real_native_sample():
    c = classify(_NATIVE_REAL.read_bytes(), content_type="application/pdf")
    assert c.source_type == "pdf_native"
    assert c.pdf_is_scanned is False


@pytest.mark.skipif(not _SCANNED_REAL.exists(), reason="host scanned sample not present")
def test_real_scanned_sample():
    c = classify(_SCANNED_REAL.read_bytes(), content_type="application/pdf")
    assert c.source_type == "pdf_scanned"
    assert c.pdf_is_scanned is True
