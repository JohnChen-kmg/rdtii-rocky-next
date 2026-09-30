"""Hand-off #2 writers (contract section 3.1 + PLAN.md section 2.3).

handoff2/
  provisions.jsonl   by_law/<doc_id>.json   source_text/<doc_id>.txt
  laws.jsonl         doc_status.jsonl       ocr/<doc_id>/...
  extract_log.jsonl  cost_report.json

source_text files are UTF-8, LF, no BOM (contract 3.4). A .pages.json sidecar
(page -> char offset) is additive provenance for location_reference - it is not
part of the frozen contract surface.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from rdtii_p2.normalize import NormalizedDoc
from rdtii_p2.status import DocStatus


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def _merge_jsonl(path: Path, new_rows: list[dict[str, Any]], key: str,
                 replaced: set[str] | None = None) -> list[dict[str, Any]]:
    """Incremental-run semantics: rows for doc_ids PROCESSED by this run
    replace their old rows - including docs that regressed to zero records
    (their stale rows must vanish, so `replaced` is the processed set, not
    merely the set of docs with new rows). Other docs' rows survive."""
    if replaced is None:
        replaced = {row[key] for row in new_rows}
    kept: list[dict[str, Any]] = []
    if path.is_file():
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    row = json.loads(line)
                    if row[key] not in replaced:
                        kept.append(row)
    return kept + new_rows


def write_source_text(out_dir: Path, doc_id: str, doc: NormalizedDoc) -> Path:
    folder = out_dir / "source_text"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{doc_id}.txt"
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(doc.text)
    sidecar = folder / f"{doc_id}.pages.json"
    sidecar.write_text(
        json.dumps({"page_offsets": doc.page_offsets,
                    "furniture_removed": doc.furniture_removed}, ensure_ascii=False),
        encoding="utf-8",
    )
    return path


def read_source_text(out_dir: Path, doc_id: str) -> str:
    return (out_dir / "source_text" / f"{doc_id}.txt").read_text(encoding="utf-8")


def read_normalized(out_dir: Path, doc_id: str) -> NormalizedDoc | None:
    """Rehydrate a frozen doc (OCR cache: 'OCR once, cache forever')."""
    text_path = out_dir / "source_text" / f"{doc_id}.txt"
    sidecar = out_dir / "source_text" / f"{doc_id}.pages.json"
    if not (text_path.is_file() and sidecar.is_file()):
        return None
    meta = json.loads(sidecar.read_text(encoding="utf-8"))
    return NormalizedDoc(
        text=text_path.read_text(encoding="utf-8"),
        page_offsets=[tuple(pair) for pair in meta.get("page_offsets", [])],
        furniture_removed=meta.get("furniture_removed", []),
    )


def append_extract_log(out_dir: Path, event: dict[str, Any]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    event = {"ts": _now(), **event}
    with open(out_dir / "extract_log.jsonl", "a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(event, ensure_ascii=False) + "\n")


def write_doc_status(out_dir: Path, statuses: list[DocStatus]) -> None:
    path = out_dir / "doc_status.jsonl"
    _write_jsonl(path, _merge_jsonl(path, [s.to_dict() for s in statuses], "doc_id"))


def write_laws(out_dir: Path, law_rows: list[dict[str, Any]],
               processed_doc_ids: set[str] | None = None) -> None:
    path = out_dir / "laws.jsonl"
    _write_jsonl(path, _merge_jsonl(path, law_rows, "doc_id", processed_doc_ids))


def write_tag_inputs(out_dir: Path, rows: list[dict[str, Any]],
                     processed_doc_ids: set[str] | None = None) -> None:
    """Sidecar consumed by `p2-extract tag-corpus` (Batches lane): everything a
    provision's tag prompt needs, keyed by provision_id, merged per-doc."""
    path = out_dir / "tag_inputs.jsonl"
    _write_jsonl(path, _merge_jsonl(path, rows, "doc_id", processed_doc_ids))


def write_provisions(out_dir: Path, records: list[dict[str, Any]],
                     processed_doc_ids: set[str] | None = None) -> None:
    path = out_dir / "provisions.jsonl"
    merged = _merge_jsonl(path, records, "doc_id", processed_doc_ids)
    _write_jsonl(path, merged)
    by_law = out_dir / "by_law"
    by_law.mkdir(parents=True, exist_ok=True)
    grouped: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        grouped.setdefault(record["doc_id"], []).append(record)
    for doc_id, doc_records in grouped.items():
        (by_law / f"{doc_id}.json").write_text(
            json.dumps({"doc_id": doc_id, "provisions": doc_records},
                       ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


def remove_stale_doc_artifacts(out_dir: Path, doc_id: str) -> None:
    """A doc that failed THIS run must not keep last run's by_law file - the
    doc_status row now says parse_failed and P3 must see a consistent seam.
    (Its provisions/laws rows are removed by the processed-set merge; the old
    source_text is left in place because nothing references it any more.)"""
    stale = out_dir / "by_law" / f"{doc_id}.json"
    if stale.is_file():
        stale.unlink()


def write_by_law_empty(out_dir: Path, doc_id: str) -> None:
    """Laws with zero citable provisions still get a by_law file (contract 3.1)."""
    by_law = out_dir / "by_law"
    by_law.mkdir(parents=True, exist_ok=True)
    (by_law / f"{doc_id}.json").write_text(
        json.dumps({"doc_id": doc_id, "provisions": []}, indent=2), encoding="utf-8"
    )


def write_cost_report(out_dir: Path, report: dict[str, Any]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "cost_report.json").write_text(
        json.dumps({"generated_at": _now(), **report}, indent=2), encoding="utf-8"
    )
