"""Manifest ingest: schema gate + contract-MAJOR gate + environment preflight.

Entry gate per PLAN.md section 2.2: `p2-extract run` first
(1) validates the Manifest against 00_contracts/schemas/manifest.schema.json,
(2) checks contract-MAJOR compatibility,
(3) runs the environment preflight (section 2.8a).
Any failure stops the run loudly - never a silent partial output.
"""

from __future__ import annotations

import csv
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import jsonschema

from config.settings import Settings

log = logging.getLogger("rdtii_p2.ingest")

SCHEMA_PATH = Path(__file__).resolve().parents[2] / "00_contracts" / "schemas" / "manifest.schema.json"

# CSV cells are all strings; the schema types them. Coercion rules per field.
_INT_FIELDS = {"http_status", "byte_size", "page_count"}
_BOOL_FIELDS = {"pdf_is_scanned"}
_NULLABLE_IF_EMPTY = {
    "instrument_version", "law_number_guess", "pillar_hint", "indicator_hints",
    "page_count", "anchor_hint", "anchor_kind", "seed_query", "crawl_notes",
    "publication_date", "assent_date", "commencement_date", "in_force_status",
    "pdf_is_scanned",
    # a hand-collected document has no HTTP transaction and may have no
    # recorded retrieval time or address at all - see
    # tools/allow_no_http_transaction.py and allow_unobserved_access_date.py
    "access_date", "http_status", "http_headers_path", "source_url", "law_name_guess", "content_type", "retrieval_method",
}


# P1 standing rule (corpus v2.4 hand-off): a row annotated "superseded by" in crawl_notes is
# provenance-only - a complete re-fetch replaced it under a new doc_id - so it is never
# extracted and never counted.
#
# The test is CASE-INSENSITIVE, and that is the whole point of it being a function. It was a
# case-sensitive `in` test until 2026-09-23, which made the rule a coin-flip: China's MIIT
# provenance row 32 reads "SUPERSEDED by 令68 of 2024-01-18" and would have been extracted and
# scored as current law, while a lowercase note two rows away would have been dropped. Which
# behaviour you got depended on how the collector happened to capitalise a sentence.
def is_superseded(crawl_notes: str | None) -> bool:
    """True when this manifest row records that a later text replaced the one held."""
    return "superseded by" in (crawl_notes or "").lower()


class IngestError(RuntimeError):
    """Fatal ingest failure - the run must stop with this message."""


@dataclass
class ManifestRow:
    data: dict[str, Any]

    def __getattr__(self, name: str) -> Any:
        try:
            return self.data[name]
        except KeyError as exc:
            raise AttributeError(name) from exc


@dataclass
class Manifest:
    rows: list[ManifestRow]
    raw_root: Path
    by_doc_id: dict[str, ManifestRow] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.by_doc_id = {r.data["doc_id"]: r for r in self.rows}

    def resolve_local_path(self, row: ManifestRow) -> Path:
        """local_path is RELATIVE to handoff1/ per contract section 2.1."""
        return self.raw_root / row.data["local_path"]


def _coerce_row(raw: dict[str, str]) -> dict[str, Any]:
    row: dict[str, Any] = {}
    for key, value in raw.items():
        if key in _NULLABLE_IF_EMPTY and value == "":
            row[key] = None
        elif key in _INT_FIELDS:
            row[key] = int(value) if value != "" else None
        elif key in _BOOL_FIELDS:
            if value == "":
                row[key] = None
            else:
                row[key] = value.strip().lower() == "true"
        else:
            row[key] = value
    return row


def load_schema() -> dict[str, Any]:
    if not SCHEMA_PATH.is_file():
        raise IngestError(f"Vendored manifest schema missing: {SCHEMA_PATH}")
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def check_contract_major(row_version: str, pinned_version: str) -> None:
    """Contract section 8: refuse loudly on a MAJOR mismatch, and only MAJOR."""
    row_major = row_version.split(".")[0]
    pinned_major = pinned_version.split(".")[0]
    if row_major != pinned_major:
        raise IngestError(
            f"Manifest is contract {row_version} (major {row_major}.x); this build "
            f"expects {pinned_major}.x - re-sync 00_contracts (contract section 8)."
        )


def load_manifest(manifest_csv: Path, raw_root: Path, settings: Settings) -> Manifest:
    """Read + validate manifest.csv. Raises IngestError on any gate failure."""
    if not manifest_csv.is_file():
        raise IngestError(f"Manifest not found: {manifest_csv}")
    if not raw_root.is_dir():
        raise IngestError(f"--raw root not found: {raw_root}")

    schema = load_schema()
    validator = jsonschema.Draft202012Validator(schema)

    rows: list[ManifestRow] = []
    errors: list[str] = []
    with open(manifest_csv, encoding="utf-8-sig", newline="") as fh:
        for line_number, raw in enumerate(csv.DictReader(fh), start=2):
            row = _coerce_row(raw)
            row_errors = sorted(validator.iter_errors(row), key=lambda e: e.json_path)
            if row_errors:
                doc = row.get("doc_id", f"line {line_number}")
                for err in row_errors[:3]:
                    errors.append(f"{doc}: {err.json_path}: {err.message}")
                continue
            rows.append(ManifestRow(row))

    if errors:
        preview = "\n  ".join(errors[:20])
        raise IngestError(
            f"Manifest failed schema validation ({len(errors)} error(s)):\n  {preview}"
        )
    if not rows:
        raise IngestError(f"Manifest has no valid rows: {manifest_csv}")

    # P1 standing rule (corpus v2.4 hand-off): rows annotated "superseded by"
    # in crawl_notes are provenance-only - a complete re-fetch replaced them
    # under a new doc_id. They are never extracted and never counted.
    superseded = [r for r in rows if is_superseded(r.data.get("crawl_notes"))]
    if superseded:
        rows = [r for r in rows if not is_superseded(r.data.get("crawl_notes"))]
        log.info("skipping %d superseded manifest row(s) (provenance-only): %s%s",
                 len(superseded),
                 ", ".join(r.data["doc_id"] for r in superseded[:5]),
                 ", ..." if len(superseded) > 5 else "")

    check_contract_major(rows[0].data["contract_version"], settings.contract_version)
    log.info("Manifest OK: %d rows, contract %s", len(rows), rows[0].data["contract_version"])
    return Manifest(rows=rows, raw_root=raw_root)


def preflight(settings: Settings, needs_ocr: bool, needs_llm: bool) -> None:
    """Environment preflight (PLAN.md section 2.8a): fail loudly, before any work."""
    problems: list[str] = []

    if needs_ocr and settings.ocr_engine == "tesseract":
        if settings.resolve_tesseract_cmd() is None:
            problems.append(
                "Tesseract binary not found - run: winget install UB-Mannheim.TesseractOCR"
            )

    if needs_llm and settings.llm_provider == "ollama":
        from config.llm.ollama_client import model_is_pulled

        if not model_is_pulled(settings.ollama_host, settings.llm_model):
            problems.append(
                f"LLM_MODEL '{settings.llm_model}' not pulled - run: "
                f"ollama pull {settings.llm_model} (or is the Ollama service down at "
                f"{settings.ollama_host}?)"
            )

    if problems:
        raise IngestError("Environment preflight failed:\n  " + "\n  ".join(problems))
    log.info("Preflight OK (ocr=%s, llm=%s)", needs_ocr, needs_llm)
