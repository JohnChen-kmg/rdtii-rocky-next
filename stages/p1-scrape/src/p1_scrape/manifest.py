"""Manifest writer (CSV + JSONL) and the `validate` gate.

- write_manifest(): emits handoff1/manifest.csv (flat) + manifest.jsonl (with the
  nested `http` object that would bloat the CSV).
- validate_manifest(): the hard gate — schema validation (per row), CONTRACT_VERSION
  MAJOR compatibility, content_sha256 uniqueness, and (optionally) that every
  local_path / http_headers_path resolves on disk. Exit criterion for T0/T5.
"""
from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Optional

from .models import MANIFEST_FIELDS
from .schema import coerce_csv_row, validate_row


# --- Serialization helpers --------------------------------------------------


def _csv_value(val: Any) -> str:
    if val is None:
        return ""
    if isinstance(val, bool):
        return "true" if val else "false"
    return str(val)


def write_manifest(rows: list[dict[str, Any]], out_dir: Path) -> tuple[Path, Path]:
    """Write manifest.csv + manifest.jsonl into out_dir (handoff1/).

    Each row is a dict keyed by MANIFEST_FIELDS. A row may additionally carry an
    "http" dict; it is written only to the JSONL (nested), never to the CSV.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "manifest.csv"
    jsonl_path = out_dir / "manifest.jsonl"

    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=MANIFEST_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: _csv_value(row.get(k)) for k in MANIFEST_FIELDS})

    with jsonl_path.open("w", encoding="utf-8") as fh:
        for row in rows:
            obj: dict[str, Any] = {k: row.get(k) for k in MANIFEST_FIELDS}
            if row.get("http") is not None:
                obj["http"] = row["http"]
            fh.write(json.dumps(obj, ensure_ascii=False) + "\n")

    return csv_path, jsonl_path


# --- Validation gate --------------------------------------------------------


def _major(version: str) -> str:
    return (version or "").strip().split(".", 1)[0]


@dataclass
class ValidationReport:
    ok: bool = True
    row_count: int = 0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def fail(self, msg: str) -> None:
        self.ok = False
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)


def validate_manifest(
    csv_path: Path,
    expected_contract_version: str,
    check_files: bool = True,
) -> ValidationReport:
    """Validate a manifest.csv against the schema + version gate + integrity checks."""
    report = ValidationReport()
    csv_path = Path(csv_path)
    if not csv_path.exists():
        report.fail(f"manifest not found: {csv_path}")
        return report

    handoff_dir = csv_path.parent
    expected_major = _major(expected_contract_version)

    with csv_path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        header = reader.fieldnames or []
        # Column order is frozen (§8) — enforce it.
        if header != MANIFEST_FIELDS:
            missing = [f for f in MANIFEST_FIELDS if f not in header]
            extra = [f for f in header if f not in MANIFEST_FIELDS]
            if missing or extra:
                report.fail(
                    f"manifest columns mismatch (missing={missing}, extra={extra})"
                )
            else:
                report.fail("manifest columns present but out of the frozen §2.2 order")

        seen_sha: dict[str, str] = {}
        seen_docid: set[str] = set()
        for i, raw in enumerate(reader, start=1):
            row = coerce_csv_row(raw)
            for err in validate_row(row):
                report.fail(f"row {i}: {err}")

            # CONTRACT_VERSION MAJOR gate.
            cv = raw.get("contract_version", "")
            if _major(cv) != expected_major:
                report.fail(
                    f"row {i}: contract_version {cv!r} major != build {expected_contract_version!r} "
                    f"— re-sync 00_contracts"
                )

            # sha256 uniqueness (dedup enforced, §2.4).
            sha = raw.get("content_sha256", "")
            if sha:
                if sha in seen_sha:
                    report.fail(
                        f"row {i}: duplicate content_sha256 (also row for doc {seen_sha[sha]})"
                    )
                else:
                    seen_sha[sha] = raw.get("doc_id", "?")

            # doc_id uniqueness.
            did = raw.get("doc_id", "")
            if did:
                if did in seen_docid:
                    report.fail(f"row {i}: duplicate doc_id {did!r}")
                seen_docid.add(did)

            # Files resolve on disk (relative to handoff1/).
            if check_files:
                for pf in ("local_path", "http_headers_path"):
                    rel = raw.get(pf, "")
                    if rel and not (handoff_dir / rel).exists():
                        report.fail(f"row {i}: {pf} does not resolve on disk: {rel}")

            report.row_count += 1

    # Validate the JSONL sibling if present (same rows + optional nested http).
    jsonl_path = handoff_dir / "manifest.jsonl"
    if jsonl_path.exists():
        _validate_jsonl(jsonl_path, expected_major, report)
    else:
        report.warn("manifest.jsonl not found alongside manifest.csv")

    if report.row_count == 0:
        report.warn("manifest has 0 data rows (empty hand-off)")

    return report


def _validate_jsonl(path: Path, expected_major: str, report: ValidationReport) -> None:
    with path.open(encoding="utf-8") as fh:
        for i, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as e:
                report.fail(f"manifest.jsonl line {i}: invalid JSON ({e})")
                continue
            for err in validate_row(obj):
                report.fail(f"manifest.jsonl line {i}: {err}")
            if _major(obj.get("contract_version", "")) != expected_major:
                report.fail(
                    f"manifest.jsonl line {i}: contract_version major mismatch"
                )
