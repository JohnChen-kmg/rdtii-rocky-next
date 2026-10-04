"""T0/T5: manifest write→validate round-trip + enforcement of the frozen schema."""
from __future__ import annotations

import hashlib
from pathlib import Path

from p1_scrape.manifest import validate_manifest, write_manifest


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _valid_row(handoff: Path, doc_id="sg-pdpa2012-001", source_type="pdf_native",
               pdf_is_scanned=False, sha=None) -> dict:
    """Build one schema-valid row and materialize its raw file + sidecar on disk."""
    rel_dir = Path("raw/sg/pdpa_2012")
    (handoff / rel_dir).mkdir(parents=True, exist_ok=True)
    ext = "pdf" if source_type.startswith("pdf") else "html"
    kind = {"pdf_native": "native", "pdf_scanned": "scanned", "html": "page"}[source_type]
    fname = f"20260710T0000Z__{kind}.{ext}"
    body = f"dummy-{doc_id}-{source_type}".encode()
    (handoff / rel_dir / fname).write_bytes(body)
    (handoff / rel_dir / f"{fname}.headers.json").write_text("{}", encoding="utf-8")
    local_path = str(rel_dir / fname).replace("\\", "/")
    return {
        "contract_version": "0.1.0",
        "instrument_version": "2.1.0",
        "doc_id": doc_id,
        "economy": "SG",
        "source_url": "https://sso.agc.gov.sg/Act/PDPA2012",
        "access_date": "2026-07-10T00:00:00Z",
        "source_type": source_type,
        "pdf_is_scanned": pdf_is_scanned,
        "local_path": local_path,
        "law_name_guess": "Personal Data Protection Act 2012",
        "law_number_guess": "Act 26 of 2012",
        "pillar_hint": "both",
        "indicator_hints": "P6-I4,P7-I1",
        "retrieval_method": "requests",
        "http_status": 200,
        "http_headers_path": local_path + ".headers.json",
        "content_type": "application/pdf",
        "content_sha256": sha or _sha(body),
        "byte_size": len(body),
        "page_count": 42,
        "anchor_hint": "?ProvIds=pr26-",
        "anchor_kind": "query",
        "seed_query": None,
        "crawl_notes": None,
    }


def test_valid_manifest_passes(tmp_path):
    row = _valid_row(tmp_path)
    csv_path, jsonl_path = write_manifest([row], tmp_path)
    assert csv_path.exists() and jsonl_path.exists()
    report = validate_manifest(csv_path, "0.1.0")
    assert report.ok, report.errors
    assert report.row_count == 1


def test_metadata_fields_roundtrip(tmp_path):
    """v0.2.0 legal-metadata fields validate and round-trip through the CSV."""
    import csv as _csv

    row = _valid_row(tmp_path)
    row.update({"publication_date": "10/06/2010", "assent_date": "02/06/2010",
                "commencement_date": "15-11-2013 [P.U.(B) 464/2013]",
                "in_force_status": "Current"})
    csv_path, _ = write_manifest([row], tmp_path)
    report = validate_manifest(csv_path, "0.1.0")
    assert report.ok, report.errors
    with csv_path.open(encoding="utf-8") as fh:
        got = next(_csv.DictReader(fh))
    assert got["publication_date"] == "10/06/2010"
    assert got["assent_date"] == "02/06/2010"
    assert got["in_force_status"] == "Current"


def test_html_row_null_scanned_ok(tmp_path):
    row = _valid_row(tmp_path, doc_id="sg-pdpa2012-002", source_type="html",
                     pdf_is_scanned=None)
    csv_path, _ = write_manifest([row], tmp_path)
    report = validate_manifest(csv_path, "0.1.0")
    assert report.ok, report.errors


def test_html_row_nonnull_scanned_fails(tmp_path):
    row = _valid_row(tmp_path, source_type="html", pdf_is_scanned=True)
    csv_path, _ = write_manifest([row], tmp_path)
    report = validate_manifest(csv_path, "0.1.0")
    assert not report.ok  # html must have pdf_is_scanned=null


def test_contract_version_major_gate(tmp_path):
    row = _valid_row(tmp_path)
    row["contract_version"] = "1.0.0"  # major mismatch vs build 0.x
    csv_path, _ = write_manifest([row], tmp_path)
    report = validate_manifest(csv_path, "0.1.0")
    assert not report.ok
    assert any("major" in e for e in report.errors)


def test_absolute_path_rejected(tmp_path):
    row = _valid_row(tmp_path)
    row["local_path"] = r"C:\somewhere\raw\x.pdf"  # absolute → contract violation (the portability rule)
    csv_path, _ = write_manifest([row], tmp_path)
    report = validate_manifest(csv_path, "0.1.0", check_files=False)
    assert not report.ok


def test_duplicate_sha_rejected(tmp_path):
    r1 = _valid_row(tmp_path, doc_id="sg-pdpa2012-001", sha="a" * 64)
    r2 = _valid_row(tmp_path, doc_id="sg-pdpa2012-002", sha="a" * 64)
    csv_path, _ = write_manifest([r1, r2], tmp_path)
    report = validate_manifest(csv_path, "0.1.0")
    assert not report.ok
    assert any("duplicate content_sha256" in e for e in report.errors)


def test_bad_doc_id_pattern_fails(tmp_path):
    row = _valid_row(tmp_path)
    row["doc_id"] = "SG_PDPA_1"  # wrong pattern
    csv_path, _ = write_manifest([row], tmp_path)
    report = validate_manifest(csv_path, "0.1.0", check_files=False)
    assert not report.ok


def test_the_adapters_facts_travel_in_the_jsonl_only(tmp_path):
    """What an adapter read from the portal about a file (its language, whether it is a translation) is
    written to manifest.jsonl, so extraction can read it in a crawl run; the CSV keeps the contract's columns."""
    import csv
    import json

    row = _valid_row(tmp_path)
    row["contract_meta"] = {"language": "eng", "language_source": "portal_field", "is_translation": True}
    plain = _valid_row(tmp_path, doc_id="sg-ca1967-001", sha=_sha(b"other"))
    csv_path, jsonl_path = write_manifest([row, plain], tmp_path)
    rows = [json.loads(line) for line in jsonl_path.read_text(encoding="utf-8").splitlines()]
    assert rows[0]["contract_meta"]["language"] == "eng"
    assert "contract_meta" not in rows[1]                       # an adapter that declares nothing adds nothing
    with csv_path.open(encoding="utf-8", newline="") as fh:
        assert "contract_meta" not in (csv.DictReader(fh).fieldnames or [])
