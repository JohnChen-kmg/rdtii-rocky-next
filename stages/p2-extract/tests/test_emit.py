"""Incremental-run merge semantics: a re-run of one doc must never clobber others."""

import json

from rdtii_p2 import emit
from rdtii_p2.normalize import normalize_pages
from rdtii_p2.status import DocStatus


def _read_jsonl(path):
    with open(path, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def test_provisions_merge_replaces_only_touched_docs(tmp_path):
    first = [{"doc_id": "sg-a-001", "provision_id": "sg-a-001#s.1", "n": 1},
             {"doc_id": "sg-b-001", "provision_id": "sg-b-001#s.1", "n": 1}]
    emit.write_provisions(tmp_path, first)
    second = [{"doc_id": "sg-b-001", "provision_id": "sg-b-001#s.1", "n": 2},
              {"doc_id": "sg-b-001", "provision_id": "sg-b-001#s.2", "n": 2}]
    emit.write_provisions(tmp_path, second)
    rows = _read_jsonl(tmp_path / "provisions.jsonl")
    assert len(rows) == 3
    assert {r["doc_id"] for r in rows} == {"sg-a-001", "sg-b-001"}
    assert all(r["n"] == 2 for r in rows if r["doc_id"] == "sg-b-001")
    assert next(r for r in rows if r["doc_id"] == "sg-a-001")["n"] == 1


def test_doc_status_merge_no_duplicates(tmp_path):
    emit.write_doc_status(tmp_path, [DocStatus("sg-a-001", "ok", 3, "B", None, "pdf_native")])
    emit.write_doc_status(tmp_path, [DocStatus("sg-a-001", "ok", 5, "B", None, "pdf_native")])
    rows = _read_jsonl(tmp_path / "doc_status.jsonl")
    assert len(rows) == 1 and rows[0]["n_provisions"] == 5


def test_source_text_frozen_lf_no_bom(tmp_path):
    doc = normalize_pages(["line one\nline two", "second page text"])
    path = emit.write_source_text(tmp_path, "sg-x-001", doc)
    raw = path.read_bytes()
    assert not raw.startswith(b"\xef\xbb\xbf"), "no BOM (contract 3.4)"
    assert b"\r\n" not in raw, "LF only (contract 3.4)"
    assert path.read_text(encoding="utf-8") == doc.text
