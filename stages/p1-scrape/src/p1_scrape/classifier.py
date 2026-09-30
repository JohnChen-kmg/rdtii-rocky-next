"""Source-type classifier (contract §2.3).

Rule:
  - Not a PDF (HTML)                → source_type=html,        pdf_is_scanned=null
  - PDF, mean chars/page >= thresh  → source_type=pdf_native,  pdf_is_scanned=false
  - PDF, mean chars/page <  thresh  → source_type=pdf_scanned, pdf_is_scanned=true

P1 makes the CLASSIFICATION only; P2 measures OCR quality. A mis-flag is recoverable
(P2 re-checks) but the field must always be present. Default threshold = 100.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pypdfium2 as pdfium  # BSD/Apache — NOT PyMuPDF (AGPL, incompatible with Apache-2.0 release)


@dataclass
class Classification:
    source_type: str                       # html | pdf_native | pdf_scanned
    pdf_is_scanned: Optional[bool]          # None only when html
    page_count: Optional[int]
    mean_chars_per_page: Optional[float] = None


def looks_like_pdf(content: bytes, content_type: str = "") -> bool:
    if content[:5] == b"%PDF-":
        return True
    return "application/pdf" in (content_type or "").lower()


def is_valid_pdf(content: bytes) -> bool:
    """A real PDF starts with the %PDF- magic. Guards against mislabeled non-PDFs
    (e.g. LOM's 5-byte 'false' sentinel, or HTML error pages served as application/pdf)."""
    return content[:5] == b"%PDF-"


def classify(content: bytes, content_type: str = "", threshold: int = 100) -> Classification:
    if looks_like_pdf(content, content_type):
        try:
            return _classify_pdf(content, threshold)
        except Exception:
            # A response that claims to be a PDF but won't open. If it lacks the %PDF
            # magic it's a mislabeled non-PDF → html; otherwise a corrupt/truncated PDF
            # whose raw bytes we still keep (P2 re-examines) → scanned. Never crash.
            if not is_valid_pdf(content):
                return Classification(source_type="html", pdf_is_scanned=None, page_count=None)
            return Classification("pdf_scanned", True, None, 0.0)
    return Classification(source_type="html", pdf_is_scanned=None, page_count=None)


def _classify_pdf(content: bytes, threshold: int) -> Classification:
    doc = pdfium.PdfDocument(content)
    try:
        pages = len(doc)
        if pages == 0:
            return Classification("pdf_scanned", True, 0, 0.0)
        total_chars = 0
        for page in doc:
            textpage = page.get_textpage()
            # get_text_range() extracts the full text layer (like fitz's get_text),
            # not just text within page bounds — keeps counts consistent with the
            # corpus manifest built under the same threshold.
            total_chars += len(textpage.get_text_range())
            textpage.close()
            page.close()
        mean = total_chars / pages
        if mean >= threshold:
            return Classification("pdf_native", False, pages, mean)
        return Classification("pdf_scanned", True, pages, mean)
    finally:
        doc.close()
