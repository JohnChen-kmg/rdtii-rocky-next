"""Batched LLM tagging: chunking, id-mapping, and fallback safety.

The batch path must never be able to WORSEN a run: any malformed batch
response degrades that chunk to the proven one-provision path, and tags are
mapped back by id (never by trusting response order alone).
"""

from typing import Any

from config.llm.base import LLMClient
from rdtii_p2 import extract_fields as ef
from rdtii_p2.segment import segment

TEXT = """Short title
1. This Act is the Test Act 2020.
Transfer of data
2.—(1) A person must not transfer data outside the country except with consent.
(2) The Minister may prescribe requirements for any transfer.
Repeal
3. The Former Board is dissolved.
"""


def _items() -> list[ef.TagItem]:
    result = segment(TEXT)
    items = []
    for span in ef.candidate_spans(result):
        start, end = ef.snippet_offsets(TEXT, span)
        items.append((span, TEXT[start:end], TEXT[max(0, start - 60):start]))
    assert len(items) >= 4, [s.article_section for s, _, _ in items]
    return items


class FakeLLM(LLMClient):
    """Schema-shape dispatch: a 'provisions' array property means a batch call."""

    model = "fake"

    def __init__(self, batch_behavior: str = "ok"):
        self.batch_calls = 0
        self.single_calls = 0
        self.batch_behavior = batch_behavior

    def _entry(self, provision_id: str) -> dict[str, Any]:
        return {
            "id": provision_id,
            "scope": "horizontal",
            "data_type": "personal",
            "obligation_type": "conditional" if provision_id == "s.2(1)" else "dp_framework",
            "extraction_confidence": 0.9,
        }

    def complete(self, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        if "provisions" in schema.get("properties", {}):
            self.batch_calls += 1
            ids = schema["properties"]["provisions"]["items"]["properties"]["id"]["enum"]
            if self.batch_behavior == "raise":
                raise RuntimeError("model unavailable")
            if self.batch_behavior == "short":
                return {"provisions": [self._entry(ids[0])]}
            entries = [self._entry(i) for i in ids]
            if self.batch_behavior == "shuffled":
                entries.reverse()
            if self.batch_behavior == "out_of_range":
                for entry in entries:
                    entry["extraction_confidence"] = 1.7
                    entry["obligation_type"] = "not-an-enum-value"
            return {"provisions": entries}
        self.single_calls += 1
        return {"scope": "sectoral", "data_type": "personal",
                "obligation_type": "other", "extraction_confidence": 0.5}


def _tags_by_section(items, tags):
    return {span.article_section: tag for (span, _, _), tag in zip(items, tags)}


def test_batch_maps_by_id_even_when_response_is_shuffled():
    items = _items()
    llm = FakeLLM("shuffled")
    tags = ef.llm_tags_batch(llm, "Test Act 2020", items, batch_size=10)
    assert llm.batch_calls == 1 and llm.single_calls == 0
    by_section = _tags_by_section(items, tags)
    assert by_section["s.2(1)"]["obligation_type"] == "conditional"
    assert by_section["s.2(2)"]["obligation_type"] == "dp_framework"


def test_batch_chunking_respects_batch_size():
    items = _items()
    llm = FakeLLM()
    tags = ef.llm_tags_batch(llm, "Test Act 2020", items, batch_size=2)
    # 4 items / batch 2 -> 2 batch calls (a trailing chunk of one would go single)
    assert llm.batch_calls == len(items) // 2
    assert llm.single_calls == len(items) % 2
    assert len(tags) == len(items)


def test_batch_size_one_is_the_legacy_single_path():
    items = _items()
    llm = FakeLLM()
    tags = ef.llm_tags_batch(llm, "Test Act 2020", items, batch_size=1)
    assert llm.batch_calls == 0 and llm.single_calls == len(items)
    assert all(tag["scope"] == "sectoral" for tag in tags)


def test_wrong_length_batch_falls_back_to_single_calls():
    items = _items()
    llm = FakeLLM("short")
    tags = ef.llm_tags_batch(llm, "Test Act 2020", items, batch_size=10)
    assert llm.batch_calls == 1
    assert llm.single_calls == len(items), "every provision re-tagged individually"
    assert all(tag["scope"] == "sectoral" for tag in tags)


def test_batch_exception_falls_back_to_single_calls():
    items = _items()
    llm = FakeLLM("raise")
    tags = ef.llm_tags_batch(llm, "Test Act 2020", items, batch_size=10)
    assert llm.single_calls == len(items)
    assert len(tags) == len(items)


def test_batch_normalizes_confidence_and_enum():
    items = _items()
    tags = ef.llm_tags_batch(FakeLLM("out_of_range"), "Test Act 2020", items, batch_size=10)
    assert all(tag["obligation_type"] == "other" for tag in tags)
    assert all(tag["extraction_confidence"] == 0.3 for tag in tags), \
        "invalid enum caps confidence so downstream widens rather than trusts"


def test_invalid_scope_and_data_type_fall_back_to_defaults():
    tags = ef._normalize_tags({"scope": "sectral", "data_type": "<UNKNOWN>",
                               "obligation_type": "conditional",
                               "extraction_confidence": 0.9})
    assert tags == {"scope": "horizontal", "data_type": "personal",
                    "obligation_type": "conditional", "extraction_confidence": 0.3}


def test_batch_prompt_reuses_single_prompt_definitions():
    """Batching must not drift the tag semantics the models were tuned on."""
    items = _items()
    span, snippet, before = items[0]
    single = ef._tag_prompt("Test Act 2020", span, snippet, before)
    batch = ef._batch_tag_prompt("Test Act 2020", items)
    assert ef._TAG_DEFINITIONS in single and ef._TAG_DEFINITIONS in batch
    assert "DECISION RULE" in batch
