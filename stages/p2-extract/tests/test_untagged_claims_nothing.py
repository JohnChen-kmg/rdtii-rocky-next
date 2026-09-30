"""A record must not name a model that did not produce its tags.

Regression test for a defect found on 2026-09-23 by the developer, reading a real Lao record:
it carried `"extraction_model": "qwen2.5:14b"` and the tag triple horizontal/personal/other,
while `extraction_confidence` was null - the signature of the no-LLM path. Measured across the
four finished corpora, **492,178 of 492,178 provisions** made that claim, and not one had been
near a model. The tags were hardcoded placeholders and the model name came from
`settings.llm_model` whether or not anything ran.

What makes it serious is not the wrong value, it is that the wrong value is *shaped like a
finding*. A null reads as a gap; "horizontal, per qwen2.5:14b" reads as a judgement.
"""

from __future__ import annotations

from config.llm import tagmap
from rdtii_p2 import extract_fields


def _record(**overrides):
    record = {"provision_id": "x#s.1", "doc_id": "x", "ocr_engine": "tesseract-lao",
              "model_version": "tesseract-lao", "extraction_model": None,
              "tags_source": "not_tagged"}
    record.update(overrides)
    return record


def test_stamping_a_tagger_keeps_the_ocr_engine():
    record = _record()
    extract_fields.stamp_tagging_model(record, "gemma3:12b", 0.82)
    assert record["extraction_model"] == "gemma3:12b"
    assert record["tags_source"] == "llm"
    # the engine is not lost: the untagged value had no "+" to split on, which is exactly
    # how an earlier version of this fix dropped it
    assert record["model_version"] == "gemma3:12b+tesseract-lao"


def test_a_failed_model_call_is_distinguishable_from_a_successful_one():
    record = _record()
    extract_fields.stamp_tagging_model(record, "gemma3:12b", 0.0)
    assert record["tags_source"] == "llm_failed"
    assert record["extraction_model"] == "gemma3:12b"   # it DID run, and it DID fail


def test_a_record_with_no_ocr_names_only_the_tagger():
    record = _record(ocr_engine=None, model_version=None)
    extract_fields.stamp_tagging_model(record, "qwen2.5:14b", 0.7)
    assert record["model_version"] == "qwen2.5:14b"


def test_legacy_model_version_suffix_is_still_honoured():
    """A provisions.jsonl written before `ocr_engine` existed must not lose its engine."""
    record = {"provision_id": "x#s.1", "model_version": "qwen2.5:14b+tesseract"}
    extract_fields.stamp_tagging_model(record, "claude-haiku-4-5", 0.9)
    assert record["model_version"] == "claude-haiku-4-5+tesseract"


def test_lao_is_tagged_by_the_model_measured_to_read_it():
    """The only language with a scored winner is Lao, and it is the one that is mapped."""
    model, why = tagmap.model_and_reason("lao")
    assert model == "gemma3:12b"
    assert "measured" in why

    # Portuguese and Chinese have only inter-model AGREEMENT measured, not a winner, so
    # they must stay on the incumbent rather than inherit gemma3 by association.
    for language in ("por", "zho"):
        model, why = tagmap.model_and_reason(language)
        assert model == tagmap.DEFAULT_TAGGER, language
        assert why.startswith("default:"), language


def test_an_unmapped_language_falls_back_loudly_rather_than_silently():
    model, why = tagmap.model_and_reason("xyz")
    assert model == tagmap.DEFAULT_TAGGER
    assert "xyz" in why           # the reason names the language, so the run note shows it


def test_one_client_per_model_not_per_language():
    """eng, msa, por and zho share a model; the run must not build four clients for them."""
    grouped = tagmap.models_in_use(["eng", "msa", "por", "zho", "lao"])
    assert grouped["gemma3:12b"] == "lao"
    assert set(grouped[tagmap.DEFAULT_TAGGER].split(", ")) == {"eng", "msa", "por", "zho"}
