"""get_ocr(settings) -> OCREngine  (dispatch on OCR_ENGINE, contract section 5.2)."""

from __future__ import annotations

import logging

from config.ocr.base import OCREngine
from config.settings import Settings

log = logging.getLogger("config.ocr")


def get_ocr(settings: Settings, language: str | None = None) -> OCREngine:
    """The OCR engine for one document.

    `language` is the document's own, read from the crawler (D3) and mapped to a pack by
    `langmap`. `OCR_LANG` stays as an override for a one-off pilot, but it is never the
    silent source: a run that read every Lao page as English is exactly what this argument
    exists to prevent.
    """
    engine = settings.ocr_engine
    if engine == "tesseract":
        from config.ocr import langmap
        from config.ocr.tesseract_engine import TesseractEngine

        cmd = settings.resolve_tesseract_cmd()
        if cmd is None:
            raise RuntimeError(
                "Tesseract binary not found on PATH or in standard install "
                "locations. Install it (winget install UB-Mannheim.TesseractOCR) "
                "or set OCR_ENGINE to another engine."
            )
        pack = langmap.pack_for(language) if language else settings.ocr_lang
        directory = langmap.use_vendored_packs()
        langmap.check_packs([language] if language else [])
        client = TesseractEngine(lang=pack, tesseract_cmd=cmd)
        log.info("OCR backend: %s (%s, packs from %s)", client.engine_id, cmd, directory)
        return client

    if engine == "paddleocr":
        from config.ocr.paddle_engine import PaddleEngine

        client = PaddleEngine(lang="en" if settings.ocr_lang == "eng" else settings.ocr_lang)
        log.info("OCR backend: %s", client.engine_id)
        return client

    if engine == "azure_docint":
        from config.ocr.azure_engine import AzureDocIntEngine

        client = AzureDocIntEngine(settings.azure_docint_key, settings.azure_docint_endpoint)
        log.info("OCR backend: %s", client.engine_id)
        return client

    raise ValueError(
        f"Unknown OCR_ENGINE: {engine!r} (expected tesseract | paddleocr | azure_docint)"
    )
