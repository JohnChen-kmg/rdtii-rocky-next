"""OCREngine interface (contract section 5.2).

to_text(pdf_path) -> OcrResult with per-page text + per-page mean word
confidence. CER is NOT computed here - it needs a reference transcription and
belongs to rdtii_p2.cer (contract section 3.5).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class OcrPage:
    page_number: int  # 1-based
    text: str
    mean_word_confidence: float | None  # 0-100 scale, None if engine gives none


@dataclass
class OcrResult:
    engine: str            # pinned "name-version-lang", e.g. "tesseract-5.4.0-eng"
    pages: list[OcrPage] = field(default_factory=list)
    preprocessing: list[str] = field(default_factory=list)

    @property
    def text(self) -> str:
        return "\n".join(p.text for p in self.pages)


class OCREngine(ABC):
    engine_id: str

    @abstractmethod
    def to_text(self, pdf_path: Path, pages: list[int] | None = None) -> OcrResult:
        """OCR the given 1-based pages (all pages if None)."""
