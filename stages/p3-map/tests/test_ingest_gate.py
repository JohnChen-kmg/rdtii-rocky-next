"""Tests for the S0 contract gate (finale plan block D).

Run from stages/p3-map, with the hand-off named as a run would name it:
    HANDOFF2_DIR=<the corpus> python -m pytest tests/test_ingest_gate.py -q
The module skips when HANDOFF2_DIR does not point at a corpus, which is also what stops it from
quietly testing Round 1's July output.

Round 1 printed a warning when the schema validator would not load and counted sampled schema
failures into a report nobody read, then carried on: a corpus that does not meet the contract
could reach the mapper, and C1c/C2 are marked on the claim that it does.

The fixture is built from real hand-off records rather than invented ones, because the point of
the gate is agreement with the vendored provision.schema.json (66 properties, economy as
^[A-Z]{2}$) and a handwritten record would only test the test. The whole module skips where the
hand-off is not on disk.
"""
from __future__ import annotations

import dataclasses
import json
import shutil

import pytest

from config.settings import SETTINGS

pytestmark = pytest.mark.skipif(
    not (SETTINGS.handoff2_dir / "provisions.jsonl").exists(),
    reason=f"no hand-off corpus at {SETTINGS.handoff2_dir}",
)
N_RECORDS = 6


def _mini_handoff(dest, corrupt_index: int | None = None, economy: str | None = None) -> dict:
    """A hand-off of N_RECORDS real provisions, optionally with one record broken."""
    h2 = SETTINGS.handoff2_dir
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "source_text").mkdir(exist_ok=True)

    recs = []
    with (h2 / "provisions.jsonl").open(encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if economy and r.get("economy") != economy:
                continue
            # byte-exact grounding needs the doc's source text to exist
            if (h2 / "source_text" / f"{r['doc_id']}.txt").exists():
                recs.append(r)
            if len(recs) == N_RECORDS:
                break
    assert len(recs) == N_RECORDS, "hand-off too small for this test"

    if corrupt_index is not None:
        # a value the contract forbids: economy is ^[A-Z]{2}$
        recs[corrupt_index] = {**recs[corrupt_index], "economy": "china"}

    with (dest / "provisions.jsonl").open("w", encoding="utf-8") as f:
        for r in recs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    doc_ids = {r["doc_id"] for r in recs}
    for did in doc_ids:
        shutil.copyfile(h2 / "source_text" / f"{did}.txt",
                        dest / "source_text" / f"{did}.txt")
    for name in ("laws.jsonl", "doc_status.jsonl"):
        with (h2 / name).open(encoding="utf-8") as fin, \
                (dest / name).open("w", encoding="utf-8") as fout:
            for line in fin:
                if json.loads(line).get("doc_id") in doc_ids:
                    fout.write(line)
    return {"doc_ids": doc_ids, "records": recs}


def _run(tmp_path, monkeypatch, corrupt_index=None, gate=True, economy=None):
    import src.p3map.ingest as ingest
    fixture = _mini_handoff(tmp_path / "handoff", corrupt_index, economy)
    settings = dataclasses.replace(
        SETTINGS, handoff2_dir=tmp_path / "handoff",
        out_dir=tmp_path / "out", index_dir=tmp_path / "index", ingest_gate=gate)
    monkeypatch.setattr(ingest, "SETTINGS", settings)
    # also the module-level object, because config.manifest reads it directly: without this the
    # test's ingest entry lands in whatever OUT_DIR the shell happens to name
    monkeypatch.setattr("config.settings.SETTINGS", settings)
    monkeypatch.setattr(ingest, "SCHEMA_SAMPLE_EVERY", 1)   # sample every record, not 1 in 64
    monkeypatch.setattr(ingest, "SPECIAL_SOURCE_TEXT_DOCS", [])
    return ingest, settings, fixture


def test_a_clean_corpus_passes_the_gate(tmp_path, monkeypatch):
    ingest, settings, fixture = _run(tmp_path, monkeypatch)
    report = ingest.run_ingest()
    gates = report["gates"]
    assert gates["passed"] is True, gates["failures"]
    assert gates["enforced"] is True
    assert gates["schema_sampled"] == N_RECORDS, "every record was validated in this test"
    assert gates["schema_sample_failures"] == 0
    assert report["records_streamed"] == N_RECORDS
    corpus = (settings.index_dir / "prefilter_corpus.jsonl").read_text(encoding="utf-8")
    assert len(corpus.strip().splitlines()) == N_RECORDS


def test_doc_meta_carries_the_0_3_0_document_fields(tmp_path, monkeypatch):
    """NEW/KNOWN cannot match a Chinese or Lao law name without law_name_en, and the CSV's
    language column has no other source."""
    ingest, settings, fixture = _run(tmp_path, monkeypatch)
    ingest.run_ingest()
    doc_meta = json.loads((settings.index_dir / "doc_meta.json").read_text(encoding="utf-8"))
    assert doc_meta
    for did in fixture["doc_ids"]:
        dm = doc_meta[did]
        for key in ("law_name_en", "law_name_original", "language_of_source",
                    "legal_status", "act_index", "economy", "law_name"):
            assert key in dm, f"{did} is missing {key}"


def test_a_record_that_fails_the_contract_stops_the_run(tmp_path, monkeypatch):
    ingest, settings, _ = _run(tmp_path, monkeypatch, corrupt_index=2)
    with pytest.raises(ingest.IngestGateError) as e:
        ingest.run_ingest()
    assert "provision.schema.json" in str(e.value)
    assert "INGEST_GATE=off" in str(e.value), "the message must name the override"
    # the report is written BEFORE the raise: a failed gate must leave its diagnosis behind
    report = json.loads((settings.out_dir / "ingest_report.json").read_text(encoding="utf-8"))
    assert report["gates"]["passed"] is False
    assert report["gates"]["schema_sample_failures"] == 1
    assert any("provision.schema.json" in f for f in report["gates"]["failures"])
    assert report["schema_error_samples"], "the first errors are recorded for diagnosis"


def test_the_gate_can_be_switched_off_for_a_plumbing_test(tmp_path, monkeypatch):
    ingest, settings, _ = _run(tmp_path, monkeypatch, corrupt_index=2, gate=False)
    report = ingest.run_ingest()          # no raise
    assert report["gates"]["passed"] is False
    assert report["gates"]["enforced"] is False


def test_a_missing_validator_is_a_gate_failure_not_a_warning(tmp_path, monkeypatch):
    """With no validator the run cannot claim the corpus meets the contract."""
    ingest, settings, _ = _run(tmp_path, monkeypatch)
    monkeypatch.setattr(ingest, "Path", _NoSchemaPath)
    with pytest.raises(ingest.IngestGateError) as e:
        ingest.run_ingest()
    assert "could not be loaded" in str(e.value)


class _NoSchemaPath:
    """Stands in for pathlib.Path just long enough to hide the schema file."""

    def __init__(self, *_a, **_k):
        pass

    def read_text(self, *_a, **_k):
        raise FileNotFoundError("provision.schema.json (hidden by the test)")


def test_a_silent_language_of_source_is_filled_from_the_provisions(tmp_path, monkeypatch):
    """China's law rows carry no language, so the threshold and the CSV would have none.

    `language_of_source` is null on all 1,085 CN laws in the hand-off, while every CN provision
    says `language_of_source_name: Chinese`. Without the fallback, China takes the conservative
    default language offset instead of its measured one, and the CSV's language column is empty
    for a sixth of the corpus.
    """
    ingest, settings, fixture = _run(tmp_path, monkeypatch, economy="CN")
    if not fixture["records"]:
        pytest.skip("no Chinese records in this hand-off")
    ingest.run_ingest()
    doc_meta = json.loads((settings.index_dir / "doc_meta.json").read_text(encoding="utf-8"))
    dm = doc_meta[fixture["records"][0]["doc_id"]]
    assert dm["language_of_source"] is None, "the law row is still silent -- that is the premise"
    assert dm["language_of_source_name"] == "Chinese"

    from config.languages import host_name, iso
    assert iso(dm["language_of_source_name"]) == "zho", "and it resolves to the ISO code"
    assert host_name(dm["language_of_source_name"]) == "Chinese", "and to the name column N wants"
