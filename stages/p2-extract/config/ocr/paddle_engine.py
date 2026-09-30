"""PaddleOCR engine - OPTIONAL extra, `pip install .[paddle]` (PLAN.md finding #7).

Not in the core pinned install: PaddlePaddle is hard to pin on Windows CPU and
threatens the <10-min Quick Start. Escalation target when Tesseract confidence
or pilot CER fails. Import errors surface as a clear actionable message.
"""

from __future__ import annotations

import statistics
from pathlib import Path

from config.ocr.base import OCREngine, OcrPage, OcrResult
from config.ocr.tesseract_engine import RENDER_DPI, _render_page


class PaddleEngine(OCREngine):
    def __init__(self, lang: str = "en"):
        try:
            from paddleocr import PaddleOCR
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "OCR_ENGINE=paddleocr but the optional extra is not installed. "
                "Run: pip install -r requirements-paddle.txt"
            ) from exc
        self._ocr = PaddleOCR(use_angle_cls=True, lang=lang, show_log=False)
        import paddleocr

        self.engine_id = f"paddleocr-{getattr(paddleocr, '__version__', 'unknown')}-{lang}"

    def to_text(self, pdf_path: Path, pages: list[int] | None = None) -> OcrResult:
        import numpy as np
        import pypdfium2 as pdfium

        pdf = pdfium.PdfDocument(str(pdf_path))
        try:
            page_numbers = pages or list(range(1, len(pdf) + 1))
            result = OcrResult(engine=self.engine_id, preprocessing=[f"rasterize@{RENDER_DPI}dpi"])
            for number in page_numbers:
                image = np.array(_render_page(pdf, number - 1).convert("RGB"))
                raw = self._ocr.ocr(image, cls=True)
                lines, confs = [], []
                for block in raw or []:
                    for entry in block or []:
                        text, conf = entry[1][0], float(entry[1][1])
                        lines.append(text)
                        confs.append(conf * 100)
                result.pages.append(OcrPage(
                    page_number=number,
                    text="\n".join(lines),
                    mean_word_confidence=statistics.mean(confs) if confs else None,
                ))
            return result
        finally:
            pdf.close()
