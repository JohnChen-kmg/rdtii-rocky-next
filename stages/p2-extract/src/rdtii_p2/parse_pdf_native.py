"""Lane B - native PDF text extraction via pypdfium2 (kickoff decision #1).

pypdfium2 (BSD/Apache) replaces the PLAN.md pdfplumber/PyMuPDF pairing: PyMuPDF
is AGPL-3.0 (incompatible with the Apache-2.0 mandate) and pypdfium2 is
benchmark-equal on legal PDFs.
"""

from __future__ import annotations

import logging
from pathlib import Path

log = logging.getLogger("rdtii_p2.lane_b")


def extract_pages(pdf_path: Path) -> list[str]:
    """Per-page raw text, 1:1 with PDF pages (empty string for blank pages)."""
    import pypdfium2 as pdfium

    pdf = pdfium.PdfDocument(str(pdf_path))
    try:
        pages = []
        for index in range(len(pdf)):
            textpage = pdf[index].get_textpage()
            try:
                pages.append(textpage.get_text_bounded())
            finally:
                textpage.close()
        return pages
    finally:
        pdf.close()


def mean_chars_per_page(pdf_path: Path, sample_pages: int = 10) -> float:
    """Extractable chars/page on a page sample - the scanned-detection metric
    (contract section 2.3; threshold NATIVE_TEXT_CHARS_PER_PAGE_MIN)."""
    import pypdfium2 as pdfium

    pdf = pdfium.PdfDocument(str(pdf_path))
    try:
        count = len(pdf)
        if count == 0:
            return 0.0
        step = max(1, count // sample_pages)
        sampled = list(range(0, count, step))[:sample_pages]
        total = 0
        for index in sampled:
            textpage = pdf[index].get_textpage()
            try:
                total += len(textpage.get_text_bounded().strip())
            finally:
                textpage.close()
        return total / len(sampled)
    finally:
        pdf.close()
