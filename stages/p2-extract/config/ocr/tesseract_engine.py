"""Tesseract 5 engine (default, CPU, core requirement).

Pre-clean per PLAN.md section 2.4.3: rasterize at 300 DPI via pypdfium2,
grayscale, autocontrast, adaptive-ish binarization. Deskew is intentionally
minimal for the pilot; escalate preprocessing only if the CER pilot demands it.
"""

from __future__ import annotations

import logging
import statistics
from pathlib import Path

from config.ocr.base import OCREngine, OcrPage, OcrResult

log = logging.getLogger("config.ocr.tesseract")

RENDER_DPI = 300


def _render_page(pdf, page_index: int):
    """Render one 0-based page to a PIL image at RENDER_DPI."""
    page = pdf[page_index]
    bitmap = page.render(scale=RENDER_DPI / 72)
    return bitmap.to_pil()


def _preprocess(image):
    """Grayscale + autocontrast + Otsu-style binarization via PIL."""
    from PIL import ImageOps

    gray = ImageOps.grayscale(image)
    gray = ImageOps.autocontrast(gray)
    # Simple global threshold; Tesseract also does its own internal Otsu
    binary = gray.point(lambda px: 255 if px > 180 else 0, mode="1")
    return binary


class TesseractEngine(OCREngine):
    def __init__(self, lang: str = "eng", tesseract_cmd: str | None = None):
        import pytesseract

        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        self._pytesseract = pytesseract
        self.lang = lang
        version = str(pytesseract.get_tesseract_version())
        self.engine_id = f"tesseract-{version}-{lang}"

    def to_text(self, pdf_path: Path, pages: list[int] | None = None) -> OcrResult:
        import pypdfium2 as pdfium

        pdf = pdfium.PdfDocument(str(pdf_path))
        try:
            page_numbers = pages or list(range(1, len(pdf) + 1))
            result = OcrResult(
                engine=self.engine_id,
                preprocessing=[f"rasterize@{RENDER_DPI}dpi", "grayscale", "autocontrast", "binarize@180"],
            )
            for number in page_numbers:
                image = _preprocess(_render_page(pdf, number - 1))
                data = self._pytesseract.image_to_data(
                    image, lang=self.lang, output_type=self._pytesseract.Output.DICT
                )
                # Reconstruct text with line structure from TSV blocks
                text = self._pytesseract.image_to_string(image, lang=self.lang)
                confidences = [
                    float(conf) for conf, word in zip(data["conf"], data["text"])
                    if word.strip() and float(conf) >= 0
                ]
                mean_conf = statistics.mean(confidences) if confidences else None
                result.pages.append(
                    OcrPage(page_number=number, text=text, mean_word_confidence=mean_conf)
                )
                log.info("OCR p.%d: %d chars, mean word conf %.1f",
                         number, len(text), mean_conf if mean_conf is not None else -1)
            return result
        finally:
            pdf.close()
