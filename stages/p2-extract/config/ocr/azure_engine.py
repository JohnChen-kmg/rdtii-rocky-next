"""Azure Document Intelligence engine - cloud, optional, key-gated.

Documented fallback for the hardest gazette scans only; never required for the
no-key CPU run (PLAN.md section 2.4.3 tier 3). If the key is empty the factory
refuses loudly rather than silently downgrading.
"""

from __future__ import annotations

from pathlib import Path

from config.ocr.base import OCREngine, OcrPage, OcrResult


class AzureDocIntEngine(OCREngine):
    def __init__(self, key: str, endpoint: str):
        if not key or not endpoint:
            raise RuntimeError(
                "OCR_ENGINE=azure_docint requires AZURE_DOCINT_KEY and "
                "AZURE_DOCINT_ENDPOINT in .env (cloud OCR is opt-in only)."
            )
        try:
            from azure.ai.documentintelligence import DocumentIntelligenceClient
            from azure.core.credentials import AzureKeyCredential
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "azure-ai-documentintelligence is not installed; it is an "
                "optional cloud dependency (pip install azure-ai-documentintelligence)."
            ) from exc
        self._client = DocumentIntelligenceClient(endpoint, AzureKeyCredential(key))
        self.engine_id = "azure_docint-prebuilt-read"

    def to_text(self, pdf_path: Path, pages: list[int] | None = None) -> OcrResult:
        with open(pdf_path, "rb") as fh:
            poller = self._client.begin_analyze_document("prebuilt-read", body=fh)
        analysis = poller.result()
        result = OcrResult(engine=self.engine_id, preprocessing=[])
        wanted = set(pages) if pages else None
        for page in analysis.pages:
            if wanted and page.page_number not in wanted:
                continue
            lines = [line.content for line in (page.lines or [])]
            words = page.words or []
            mean_conf = (
                sum(w.confidence for w in words) / len(words) * 100 if words else None
            )
            result.pages.append(OcrPage(
                page_number=page.page_number,
                text="\n".join(lines),
                mean_word_confidence=mean_conf,
            ))
        return result
