"""CER measurement sanity + the synthetic-scan regression (T2b support)."""

import pytest

from rdtii_p2 import cer


def test_identical_text_is_zero():
    assert cer.cer("An organisation must not transfer data.", "An organisation must not transfer data.") == 0.0


def test_known_error_rate():
    # 1 substitution over 10 reference chars = 0.1
    assert cer.cer("abcdefghij", "abcdefghiX") == pytest.approx(0.1)


def test_whitespace_and_wrap_insensitive():
    reference = "An organisation must not transfer any personal data."
    hypothesis = "An organisation must\nnot   transfer any\npersonal data."
    assert cer.cer(reference, hypothesis) == 0.0


def test_empty_reference_rejected():
    with pytest.raises(ValueError):
        cer.cer("", "anything")


def test_doc_aggregation_is_char_weighted():
    report = cer.measure_doc(
        doc_id="test-001",
        page_pairs=[(1, "a" * 90, "a" * 90), (2, "b" * 10, "X" + "b" * 9)],
        cer_method="gold_page", reference_source="unit test",
        ocr_engine="tesseract-test", preprocessing=[],
    )
    # page 1: CER 0 over 90 chars; page 2: 0.1 over 10 chars -> weighted 0.01
    assert report.doc_cer == pytest.approx(0.01)
    assert report.meets_rubric()  # gold_page + <0.05


def test_synthetic_method_never_claims_rubric():
    report = cer.measure_doc(
        doc_id="test-002",
        page_pairs=[(1, "abc", "abc")],
        cer_method="synthetic", reference_source="degraded render",
        ocr_engine="tesseract-test", preprocessing=[],
    )
    assert report.doc_cer == 0.0
    assert not report.meets_rubric(), "synthetic reference must not claim the <5% rubric item"
