"""OCR once, keep the raw pages, and make a killed run resumable.

Round 1 cached the *normalised* text keyed on `doc_id` alone. That is two problems at once:
change the normaliser and the cache is silently stale, and change the OCR language or the
engine and the cache does not notice at all.

Here the cache is per page and keyed on everything that could change the characters:

    out/ocr/<doc_id>/meta.json     the key and the per-page record
    out/ocr/<doc_id>/page_0007.txt the raw OCR text of page 7, exactly as the engine gave it

Raw, not normalised, so a normalisation change costs nothing. Keyed on the file's own
sha256, so a re-crawled document re-OCRs by itself.

The key also records seconds and mean word confidence per page, which is where the cost table
and the per-script quality figures come from.
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path

log = logging.getLogger("rdtii_p2.ocr_cache")

CACHE_VERSION = 1


@dataclass
class PageRecord:
    page: int
    chars: int
    seconds: float
    mean_word_confidence: float | None = None
    retries: int = 0


@dataclass
class DocCache:
    doc_id: str
    content_sha256: str
    engine: str
    language: str
    dpi: int
    preprocessing: list[str] = field(default_factory=list)
    pages: list[PageRecord] = field(default_factory=list)
    cache_version: int = CACHE_VERSION

    def key(self) -> tuple:
        return (self.content_sha256, self.engine, self.language, self.dpi, self.cache_version)


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def cache_dir(out_dir: Path, doc_id: str) -> Path:
    return out_dir / "ocr" / doc_id


def read(out_dir: Path, doc_id: str, expect: DocCache) -> list[str] | None:
    """The cached pages when the key still matches, else None so the caller re-OCRs."""
    directory = cache_dir(out_dir, doc_id)
    meta_path = directory / "meta.json"
    if not meta_path.is_file():
        return None
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        log.warning("%s: OCR cache metadata unreadable, re-OCRing", doc_id)
        return None
    stored = (meta.get("content_sha256"), meta.get("engine"), meta.get("language"),
              meta.get("dpi"), meta.get("cache_version"))
    if stored != expect.key():
        log.info("%s: OCR cache key changed %s -> %s, re-OCRing",
                 doc_id, stored, expect.key())
        return None
    pages = []
    for record in meta.get("pages", []):
        page_path = directory / f"page_{record['page']:04d}.txt"
        if not page_path.is_file():
            log.warning("%s: page %d missing from the cache, re-OCRing the document",
                        doc_id, record["page"])
            return None
        pages.append(page_path.read_text(encoding="utf-8"))
    return pages or None


def write(out_dir: Path, meta: DocCache, page_texts: list[str]) -> None:
    directory = cache_dir(out_dir, meta.doc_id)
    directory.mkdir(parents=True, exist_ok=True)
    for record, text in zip(meta.pages, page_texts):
        (directory / f"page_{record.page:04d}.txt").write_text(
            text, encoding="utf-8", newline="\n")
    payload = asdict(meta)
    (directory / "meta.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")


def summarise(out_dir: Path) -> dict:
    """Totals for the run note: pages, seconds and retries actually spent on OCR."""
    root = out_dir / "ocr"
    docs = pages = retries = 0
    seconds = 0.0
    by_language: dict[str, int] = {}
    if not root.is_dir():
        return {"documents": 0, "pages": 0, "seconds": 0.0, "retries": 0, "by_language": {}}
    for meta_path in root.glob("*/meta.json"):
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        docs += 1
        for record in meta.get("pages", []):
            pages += 1
            seconds += float(record.get("seconds") or 0.0)
            retries += int(record.get("retries") or 0)
        language = meta.get("language", "?")
        by_language[language] = by_language.get(language, 0) + len(meta.get("pages", []))
    return {"documents": docs, "pages": pages, "seconds": round(seconds, 1),
            "retries": retries, "by_language": by_language}
