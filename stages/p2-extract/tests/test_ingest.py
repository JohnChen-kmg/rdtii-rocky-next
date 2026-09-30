"""Entry-gate behavior: schema validation, coercion, contract-MAJOR gate."""

import csv

import pytest

from config.settings import Settings
from rdtii_p2.ingest import IngestError, check_contract_major, load_manifest

GOOD_ROW = {
    "contract_version": "0.2.0", "instrument_version": "", "doc_id": "sg-testact-001",
    "economy": "SG", "source_url": "https://sso.agc.gov.sg/Act/TEST",
    "access_date": "2026-07-11T04:02:40Z", "source_type": "pdf_native",
    "pdf_is_scanned": "false", "local_path": "raw/sg/test/file.pdf",
    "law_name_guess": "Test Act 2026", "law_number_guess": "", "pillar_hint": "P6",
    "indicator_hints": "P6-I4", "retrieval_method": "requests", "http_status": "200",
    "http_headers_path": "raw/sg/test/file.pdf.headers.json",
    "content_type": "application/pdf", "content_sha256": "a" * 64, "byte_size": "1000",
    "page_count": "", "anchor_hint": "", "anchor_kind": "", "seed_query": "",
    "crawl_notes": "", "publication_date": "", "assent_date": "",
    "commencement_date": "", "in_force_status": "",
}


def _write_manifest(tmp_path, rows):
    path = tmp_path / "manifest.csv"
    with open(path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(GOOD_ROW))
        writer.writeheader()
        writer.writerows(rows)
    return path


def test_valid_row_loads_and_coerces(tmp_path):
    manifest = load_manifest(_write_manifest(tmp_path, [GOOD_ROW]), tmp_path, Settings())
    row = manifest.rows[0].data
    assert row["pdf_is_scanned"] is False
    assert row["http_status"] == 200
    assert row["page_count"] is None
    assert row["law_number_guess"] is None


def test_bad_doc_id_rejected(tmp_path):
    bad = dict(GOOD_ROW, doc_id="SG_BAD_ID")
    with pytest.raises(IngestError, match="schema validation"):
        load_manifest(_write_manifest(tmp_path, [bad]), tmp_path, Settings())


def test_absolute_local_path_rejected(tmp_path):
    bad = dict(GOOD_ROW, local_path=r"C:\abs\path.pdf")
    with pytest.raises(IngestError, match="schema validation"):
        load_manifest(_write_manifest(tmp_path, [bad]), tmp_path, Settings())


def test_html_row_must_null_pdf_is_scanned(tmp_path):
    bad = dict(GOOD_ROW, source_type="html", pdf_is_scanned="true")
    with pytest.raises(IngestError, match="schema validation"):
        load_manifest(_write_manifest(tmp_path, [bad]), tmp_path, Settings())


def test_contract_major_gate():
    check_contract_major("0.2.0", "0.2.0")
    check_contract_major("0.3.5", "0.2.0")  # MINOR drift tolerated
    with pytest.raises(IngestError, match="re-sync 00_contracts"):
        check_contract_major("1.0.0", "0.2.0")
