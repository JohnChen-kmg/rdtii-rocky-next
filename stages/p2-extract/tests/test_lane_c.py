"""Lane C (corpus OCR): parse, cache reuse, and CER-estimate honesty."""

from pathlib import Path
from types import SimpleNamespace

import config.ocr.factory as ocr_factory
from config.ocr.base import OcrPage, OcrResult
from config.settings import Settings
from rdtii_p2 import cer, cli, emit

SCAN_TEXT_P1 = """PERSONAL DATA PROTECTION ACT
1. This Act may be cited as the Test Scanned Act 2010.
2. (1) This Act applies throughout the country to all processing of data.
"""
SCAN_TEXT_P2 = """(2) The Minister may prescribe further requirements for processing.
3. The repealed enactment continues to apply to pending proceedings.
"""


class FakeEngine:
    engine_id = "fake-ocr"

    def __init__(self):
        self.calls = 0

    def to_text(self, pdf_path: Path, pages=None) -> OcrResult:
        self.calls += 1
        return OcrResult(
            engine="fake-ocr-1.0-eng",
            pages=[OcrPage(1, SCAN_TEXT_P1, 96.0), OcrPage(2, SCAN_TEXT_P2, 94.0)],
            preprocessing=["grayscale", "300dpi"],
        )


def _route():
    from rdtii_p2 import router

    return router.Route(lane="C", source_type_final="pdf_scanned",
                        pdf_is_scanned_final=True, reroute_reason=None)


def test_lane_c_parses_and_reports_engine(tmp_path, monkeypatch):
    engine = FakeEngine()
    # get_ocr takes the document language since W3: the pack is chosen per document,
    # not once per run from OCR_LANG
    monkeypatch.setattr(ocr_factory, "get_ocr", lambda settings, language=None: engine)
    normalized, segmented, anchors, ocr_meta = cli._parse_doc(
        "my-test-001", _route(), tmp_path / "scan.pdf", "https://x", Settings(),
        tmp_path, force=False)
    assert engine.calls == 1
    assert "cited as the Test Scanned Act" in normalized.text
    assert segmented.find("s.2(2)") is not None
    assert ocr_meta == {"engine": "fake-ocr-1.0-eng",
                        "preprocessing": ["grayscale", "300dpi"], "cached": False}


def test_lane_c_reuses_frozen_text_without_engine(tmp_path, monkeypatch):
    engine = FakeEngine()
    # get_ocr takes the document language since W3: the pack is chosen per document,
    # not once per run from OCR_LANG
    monkeypatch.setattr(ocr_factory, "get_ocr", lambda settings, language=None: engine)
    normalized, *_ = cli._parse_doc("my-test-001", _route(), tmp_path / "scan.pdf",
                                    "https://x", Settings(), tmp_path, force=False)
    emit.write_source_text(tmp_path, "my-test-001", normalized)

    def explode(settings):
        raise AssertionError("cached lane C must not construct an engine")

    monkeypatch.setattr(ocr_factory, "get_ocr", explode)
    cached, segmented, _anchors, ocr_meta = cli._parse_doc(
        "my-test-001", _route(), tmp_path / "scan.pdf", "https://x", Settings(),
        tmp_path, force=False)
    assert cached.text == normalized.text
    assert cached.page_for_offset(0) == 1
    assert ocr_meta["cached"] is True
    assert segmented.find("s.2(2)") is not None


def test_estimate_report_is_disclosed_and_never_claims_rubric():
    report = cer.make_estimate_report("my-test-001", "fake-ocr-1.0-eng", ["300dpi"])
    assert report.cer_method == "engine_fixture_estimate"
    assert report.doc_cer == cer.ENGINE_FIXTURE_ESTIMATE_CER
    assert not report.meets_rubric(), "estimates must never claim the <5% item"
    assert "fixtures/ocr_reference" in report.reference_source


DUPLICATE_NUMBERING = """PART 1 — FIRST INSTRUMENT
5. The first instrument's fifth section carries this provision text.
PART 2 — SECOND INSTRUMENT
5. The second instrument's fifth section carries different provision text.
"""


def test_duplicate_citations_get_unique_provision_ids(tmp_path):
    from rdtii_p2 import router, segment as segment_mod
    from rdtii_p2.normalize import NormalizedDoc

    row = SimpleNamespace(data={
        "doc_id": "xx-dup-001", "economy": "MY", "law_name_guess": "Dup Act",
        "law_number_guess": None, "local_path": "raw/x.pdf", "source_url": "https://x",
        "retrieval_method": "http", "access_date": "2026-07-12",
        "instrument_version": "2.1.0", "anchor_hint": None, "anchor_kind": None,
    })
    decision = router.Route(lane="B", source_type_final="pdf_native",
                            pdf_is_scanned_final=False, reroute_reason=None)
    normalized = NormalizedDoc(text=DUPLICATE_NUMBERING)
    segmented = segment_mod.segment(DUPLICATE_NUMBERING)
    records, _meta, tag_rows = cli._extract_doc(
        "xx-dup-001", row, decision, normalized, segmented, None, Settings(), tmp_path)
    ids = [r["provision_id"] for r in records]
    assert len(ids) == len(set(ids)) == 2, ids
    assert ids == ["xx-dup-001#s.5", "xx-dup-001#s.5~2"]
    assert all(r["article_section"] == "s.5" for r in records), \
        "the human citation stays honest; only the id disambiguates"
    assert [t["provision_id"] for t in tag_rows] == ids


def test_scanned_rows_sort_after_native_and_by_keyword():
    def row(doc_id, source_type, title):
        return SimpleNamespace(data={"doc_id": doc_id, "source_type": source_type,
                                     "law_name_guess": title})

    rows = [
        row("my-3", "pdf_scanned", "Stamp Duties Act"),
        row("my-2", "pdf_scanned", "Computer Crimes Act 1997"),
        row("sg-1", "pdf_native", "Personal Data Protection Act 2012"),
    ]
    ordered = sorted(rows, key=cli._scanned_rank)
    assert [r.data["doc_id"] for r in ordered] == ["sg-1", "my-2", "my-3"]
