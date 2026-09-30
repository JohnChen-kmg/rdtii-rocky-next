"""Typed settings loaded from .env (contract section 5.1).

Auto-fallback rule: an empty ANTHROPIC_API_KEY forces LLM_PROVIDER=ollama so the
no-key CPU end-to-end run always works. The fallback is logged, never silent.
"""

from __future__ import annotations

import logging
import os
import shutil
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field

log = logging.getLogger("config.settings")

# Well-known Windows install locations checked when the binary is not on PATH.
_TESSERACT_CANDIDATES = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe"),
]


class Settings(BaseModel):
    # --- seams (contract sections 2, 3) ---
    handoff1_dir: Path = Field(default=Path("../rdtii-p1-scrape/handoff1_v2"))
    out_dir: Path = Field(default=Path("../handoff2"))
    contract_version: str = "0.3.0"

    # --- OCR (contract section 5.1) ---
    ocr_engine: str = "tesseract"  # tesseract | paddleocr | azure_docint
    ocr_lang: str = "eng"
    azure_docint_key: str = ""
    azure_docint_endpoint: str = ""

    # --- LLM (contract section 5.1) ---
    llm_provider: str = "ollama"  # ollama | anthropic
    llm_model: str = "qwen2.5:14b"
    anthropic_api_key: str = ""
    ollama_host: str = "http://localhost:11434"
    # provisions packed per tagging call; 1 = one-provision prompts.
    # Measured 2026-07-12 (SG PDPA, qwen2.5:14b): batching does NOT speed up
    # local decode (0.88 vs 1.02 prov/s) but cuts input tokens ~3.3x, so use
    # >1 only where input tokens cost money (LLM_PROVIDER=anthropic).
    tag_batch_size: int = 1

    # --- guardrails / thresholds ---
    max_cost_usd_per_doc: float = 0.25
    native_text_chars_per_page_min: int = 100

    def resolve_tesseract_cmd(self) -> str | None:
        """Absolute path to the Tesseract binary, or None if not installed."""
        found = shutil.which("tesseract")
        if found:
            return found
        for candidate in _TESSERACT_CANDIDATES:
            if Path(candidate).is_file():
                return candidate
        return None


def load_settings(env_file: str | Path | None = None) -> Settings:
    """Load .env (repo root by default) and build a validated Settings object."""
    load_dotenv(env_file or Path(".env"), override=False)
    env = os.environ

    settings = Settings(
        handoff1_dir=Path(env.get("HANDOFF1_DIR", "../rdtii-p1-scrape/handoff1_v2")),
        out_dir=Path(env.get("OUT_DIR", "../handoff2")),
        contract_version=env.get("CONTRACT_VERSION", "0.3.0"),
        ocr_engine=env.get("OCR_ENGINE", "tesseract"),
        ocr_lang=env.get("OCR_LANG", "eng"),
        azure_docint_key=env.get("AZURE_DOCINT_KEY", ""),
        azure_docint_endpoint=env.get("AZURE_DOCINT_ENDPOINT", ""),
        llm_provider=env.get("LLM_PROVIDER", "ollama"),
        llm_model=env.get("LLM_MODEL", "qwen2.5:14b"),
        anthropic_api_key=env.get("ANTHROPIC_API_KEY", ""),
        ollama_host=env.get("OLLAMA_HOST", "http://localhost:11434"),
        tag_batch_size=int(env.get("TAG_BATCH_SIZE", "10")),
        max_cost_usd_per_doc=float(env.get("MAX_COST_USD_PER_DOC", "0.25")),
        native_text_chars_per_page_min=int(env.get("NATIVE_TEXT_CHARS_PER_PAGE_MIN", "100")),
    )

    # Contract section 5.2: empty key => auto-select ollama, loudly.
    if settings.llm_provider == "anthropic" and not settings.anthropic_api_key:
        log.warning(
            "ANTHROPIC_API_KEY is empty - auto-falling back to LLM_PROVIDER=ollama "
            "(no-key CPU run, contract section 5.2)"
        )
        settings.llm_provider = "ollama"

    return settings
