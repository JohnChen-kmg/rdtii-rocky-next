"""Batches-lane invariants: packing, result mapping, apply rewrite, state.

No network: batch results are faked as SimpleNamespace objects shaped like the
anthropic SDK's MessageBatchIndividualResponse.
"""

import json
from types import SimpleNamespace

from rdtii_p2 import tag_batches


def _row(pid: str, doc: str, section: str) -> dict:
    return {
        "provision_id": pid, "doc_id": doc, "law_name": "Test Act 2020",
        "article_section": section, "heading": "Heading", "hierarchy": ["Act", section],
        "snippet": f"Text of {section}.", "context_before": "before",
    }


ROWS = (
    [_row(f"a#s.{i}", "doc-a", f"s.{i}") for i in range(1, 8)]   # 7 rows
    + [_row(f"b#s.{i}", "doc-b", f"s.{i}") for i in range(1, 4)]  # 3 rows
)


def test_make_chunks_groups_per_doc_then_size():
    chunks = tag_batches.make_chunks(ROWS, batch_size=5)
    sizes = [(c.doc_id, len(c.rows)) for c in chunks]
    assert sizes == [("doc-a", 5), ("doc-a", 2), ("doc-b", 3)]
    assert len({c.custom_id for c in chunks}) == 3, "custom_ids unique"
    assert chunks[0].ids == ["s.1", "s.2", "s.3", "s.4", "s.5"]


def test_chunk_params_single_vs_batch_schema():
    chunks = tag_batches.make_chunks(ROWS, batch_size=5)
    multi = tag_batches.chunk_params(chunks[0], "claude-haiku-4-5")
    schema = multi["tools"][0]["input_schema"]
    assert "provisions" in schema["properties"]
    assert set(schema["properties"]["provisions"]["items"]["properties"]["id"]["enum"]) \
        == set(chunks[0].ids)
    assert multi["tool_choice"] == {"type": "tool", "name": "emit_result"}
    assert "Text of s.1." in multi["messages"][0]["content"]

    single_chunk = tag_batches.make_chunks([ROWS[0]], batch_size=5)[0]
    single = tag_batches.chunk_params(single_chunk, "claude-haiku-4-5")
    assert "provisions" not in single["tools"][0]["input_schema"]["properties"]


def _entry(custom_id: str, ids: list[str] | None, *, errored: bool = False):
    if errored:
        return SimpleNamespace(custom_id=custom_id,
                               result=SimpleNamespace(type="errored"))
    payload = {"provisions": [
        {"id": i, "scope": "horizontal", "data_type": "personal",
         "obligation_type": "dp_framework", "extraction_confidence": 0.8}
        for i in ids
    ]}
    message = SimpleNamespace(
        content=[SimpleNamespace(type="tool_use", input=payload)],
        usage=SimpleNamespace(input_tokens=100, output_tokens=50),
    )
    return SimpleNamespace(custom_id=custom_id,
                           result=SimpleNamespace(type="succeeded", message=message))


def test_collect_tags_maps_ids_and_queues_failures():
    chunks = tag_batches.make_chunks(ROWS, batch_size=5)
    entries = [
        _entry(chunks[0].custom_id, chunks[0].ids),
        _entry(chunks[1].custom_id, None, errored=True),
        _entry(chunks[2].custom_id, chunks[2].ids),
    ]
    client = SimpleNamespace(messages=SimpleNamespace(batches=SimpleNamespace(
        results=lambda batch_id: iter(entries))))
    tags, leftovers, usage = tag_batches.collect_tags(client, ["batch_1"], chunks)
    assert len(tags) == 8, "5 from chunk0 + 3 from chunk2"
    assert tags["a#s.1"]["obligation_type"] == "dp_framework"
    assert [r["provision_id"] for r in leftovers] == [f"a#s.{i}" for i in (6, 7)]
    assert usage == {"input_tokens": 200, "output_tokens": 100}


def test_collect_tags_survives_stringified_and_garbage_payloads():
    chunks = tag_batches.make_chunks(ROWS, batch_size=5)
    good = _entry(chunks[0].custom_id, chunks[0].ids)
    # provisions emitted as a JSON string instead of an array
    stringified = _entry(chunks[2].custom_id, chunks[2].ids)
    block = stringified.result.message.content[0]
    block.input = {"provisions": json.dumps(block.input["provisions"])}
    # outright garbage payload must queue for retry, never crash
    garbage = _entry(chunks[1].custom_id, chunks[1].ids)
    garbage.result.message.content[0].input = {"provisions": "not json ["}
    client = SimpleNamespace(messages=SimpleNamespace(batches=SimpleNamespace(
        results=lambda batch_id: iter([good, stringified, garbage]))))
    tags, leftovers, usage = tag_batches.collect_tags(client, ["b"], chunks)
    assert len(tags) == 8, "good + coerced stringified chunks both mapped"
    assert tags["b#s.1"]["obligation_type"] == "dp_framework"
    assert [r["provision_id"] for r in leftovers] == [f"a#s.{i}" for i in (6, 7)]


def test_apply_tags_rewrites_records_and_stamps_model(tmp_path):
    records = [
        {"provision_id": "a#s.1", "doc_id": "doc-a", "scope": "horizontal",
         "data_type": "personal", "obligation_type": "other",
         "extraction_confidence": None, "extraction_model": "qwen2.5:14b",
         "model_version": "qwen2.5:14b+tesseract"},
        {"provision_id": "a#s.2", "doc_id": "doc-a", "scope": "horizontal",
         "data_type": "personal", "obligation_type": "other",
         "extraction_confidence": None, "extraction_model": "qwen2.5:14b",
         "model_version": "qwen2.5:14b"},
    ]
    path = tmp_path / "provisions.jsonl"
    path.write_text("\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8")

    tags = {"a#s.1": {"scope": "sectoral", "data_type": "personal",
                      "obligation_type": "conditional", "extraction_confidence": 0.9}}
    updated, unmatched = tag_batches.apply_tags(tmp_path, tags, "claude-haiku-4-5")
    assert (updated, unmatched) == (1, 0)

    rows = {json.loads(l)["provision_id"]: json.loads(l)
            for l in path.read_text(encoding="utf-8").splitlines() if l.strip()}
    assert rows["a#s.1"]["obligation_type"] == "conditional"
    assert rows["a#s.1"]["model_version"] == "claude-haiku-4-5+tesseract", \
        "OCR-engine suffix survives the model stamp"
    assert rows["a#s.1"]["extraction_model"] == "claude-haiku-4-5"
    assert rows["a#s.2"]["obligation_type"] == "other", "untagged record untouched"
    assert (tmp_path / "by_law" / "doc-a.json").is_file()


def test_state_roundtrip(tmp_path):
    state = {"batch_ids": ["b1"], "model": "claude-haiku-4-5",
             "batch_size": 10, "n_rows": 10}
    tag_batches.save_state(tmp_path, state)
    assert tag_batches.load_state(tmp_path) == state
