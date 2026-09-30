"""The batch lane must retry a result it cannot parse, not write an error row and print advice.

Measured 29 September 2026: 225 of 14,456 S4 calls produced no usable verdict. 124 of those were a
degenerate sample -- the model returned the SHAPE of a tool call, its input literally
`{'parameter name': 'value'}`. It correlates with nothing: the failures' provision text has a
median length of 814 characters against 821 for the successes, and they spread over 87 distinct
documents with a worst case of 5 in 326. A random ~0.86% rate that re-sampling clears.

What turned that into 1.6% permanent loss was an asymmetry between the lanes. The live runner has
retried once since Round 1; this lane parsed once, wrote an error row, and PRINTED
`-> retry live: python -m ...` as advice for a human to act on. Nobody did, and batch carried half
the run.

These tests pin the three properties that could otherwise cost money or data silently:
one retry per failure, no client at all on a clean fetch, and retry cost kept out of the batch
ledger's first-ingest-wins rule.
"""
from __future__ import annotations

import dataclasses
import json
import sys
import types

import pytest

from config.llm.base import Usage
from config.settings import SETTINGS
from src.p3map.mapping import batch_runner as br

GOOD_TOOL_INPUT = {
    "core_legal_question_answer": "yes, transfer is banned outright",
    "who_is_regulated": "data controllers",
    "conditions_and_exceptions": "none",
    "trap_checks": {"conditional_path_exists": False, "retention_is_minimum": False,
                    "government_data_only": False, "provision_in_force": True,
                    "sectoral_scope": False},
    "verdicts": [{"indicator": "6.1", "applies": True, "score_hint": "1",
                  "coverage": "Horizontal", "confidence": 0.9,
                  "verbatim_quote": "transfer abroad is prohibited",
                  "rationale": "6.1 outright ban branch"}],
}
# what the model actually sent on 124 of the 225 failures
PLACEHOLDER_TOOL_INPUT = {"parameter name": "value"}

REC = {"provision_id": "p1", "doc_id": "d1", "law_name": "Act A", "article_section": "s.1",
       "text": "It is provided that transfer abroad is prohibited in all cases."}


# --------------------------------------------------------------------------- fakes


class _Block:
    type = "tool_use"

    def __init__(self, payload): self.input = payload


class _Msg:
    def __init__(self, payload):
        self.content = [_Block(payload)]
        self.usage = types.SimpleNamespace(
            input_tokens=100, output_tokens=50,
            cache_read_input_tokens=0, cache_creation_input_tokens=0)


class _Result:
    def __init__(self, cid, payload):
        self.custom_id = cid
        self.result = types.SimpleNamespace(type="succeeded", message=_Msg(payload))


class _StubLLM:
    """A live client. `replies` is consumed one per call; an Exception instance is raised."""

    model = "claude-sonnet-5"

    def __init__(self, replies):
        self._replies = list(replies)
        self.calls = 0
        self.usage = Usage(input_tokens=1000, output_tokens=500, calls=1)

    def complete(self, *a, **k):
        self.calls += 1
        r = self._replies.pop(0) if self._replies else RuntimeError("no reply queued")
        if isinstance(r, Exception):
            raise r
        return r


def _fake_anthropic(results):
    """A stand-in for the `anthropic` module that fetch() imports inside the function."""
    class _Batches:
        def retrieve(self, bid): return types.SimpleNamespace(processing_status="ended")
        def results(self, bid): return iter(results)

    class _Anthropic:
        def __init__(self, *a, **k): self.messages = types.SimpleNamespace(batches=_Batches())

    return types.SimpleNamespace(Anthropic=_Anthropic)


@pytest.fixture
def lane(tmp_path, monkeypatch):
    """A one-batch, one-provision lane whose result payload the test chooses."""
    (tmp_path / "map").mkdir(parents=True)
    monkeypatch.setattr(br, "SETTINGS", dataclasses.replace(SETTINGS, out_dir=tmp_path))
    monkeypatch.setattr(br, "_require_batch_provider", lambda verb: None)
    monkeypatch.setattr(br, "_load_records", lambda pids: {"p1": REC})
    monkeypatch.setattr(br, "_load_pairs", lambda e: {"p1": {"6.1"}})
    monkeypatch.setattr(br, "build_system_prefix", lambda: "SYSTEM")
    monkeypatch.setattr(br, "_counts_from_verdicts", lambda e: {"provisions": 1})

    state = {"economy": "CN", "model": "claude-sonnet-5",
             "batches": [{"batch_id": "b1", "ingested": False, "n_requests": 1,
                          "manifest": {"r000000": "p1"}}]}

    def install(tool_input, llm=None):
        monkeypatch.setattr(br, "_load_state", lambda e: json.loads(json.dumps(state)))
        monkeypatch.setitem(sys.modules, "anthropic",
                            _fake_anthropic([_Result("r000000", tool_input)]))
        if llm is not None:
            monkeypatch.setattr(br, "get_llm", lambda *a, **k: llm)
        return tmp_path

    return install


def _rows(tmp_path):
    p = tmp_path / "map" / "verdicts_CN.jsonl"
    return [json.loads(l) for l in p.open(encoding="utf-8")] if p.exists() else []


# --------------------------------------------------------------------------- tests


def test_an_unparseable_result_is_retried_live_exactly_once_and_recovers(lane):
    llm = _StubLLM([GOOD_TOOL_INPUT])
    tmp = lane(PLACEHOLDER_TOOL_INPUT, llm)
    br.fetch("CN")

    assert llm.calls == 1, "exactly one retry per failed result -- never a loop"
    rows = _rows(tmp)
    assert len(rows) == 1
    row = rows[0]
    assert "error" not in row, "the retry recovered the provision"
    assert row["retried_live"] is True and row["batch_error"]
    assert [v["applies"] for v in row["verdicts"]] == [True]
    assert row["verdicts"][0]["quote_grounded_ws"] is True, "the quote is anchored as usual"
    assert row["model"] == "claude-sonnet-5"


def test_when_the_retry_also_fails_the_error_row_names_both_attempts(lane):
    llm = _StubLLM([ValueError("still a placeholder")])
    tmp = lane(PLACEHOLDER_TOOL_INPUT, llm)
    br.fetch("CN")

    assert llm.calls == 1
    row = _rows(tmp)[0]
    assert "error" in row
    assert "batch+retry both failed" in row["error"]
    assert "ValueError" in row["error"], "the retry's own reason is kept"
    assert "batch:" in row["error"], "and so is the batch's"


def test_a_clean_fetch_builds_no_live_client_and_makes_no_call(lane, monkeypatch):
    """The retry must cost nothing when nothing failed -- not one construction, not one call."""
    built: list = []
    llm = _StubLLM([])

    def _record(*a, **k):
        built.append(1)
        return llm

    tmp = lane(GOOD_TOOL_INPUT)
    monkeypatch.setattr(br, "get_llm", _record)
    br.fetch("CN")

    assert built == [], "a clean fetch must not construct a live client"
    assert llm.calls == 0
    row = _rows(tmp)[0]
    assert "error" not in row and "retried_live" not in row

    report = json.loads((tmp / "map" / "map_report_CN.json").read_text(encoding="utf-8"))
    assert report["retry_live_usd"] == 0 and report["retry_live_calls"] == 0


def test_a_record_missing_row_is_not_retried(lane, monkeypatch):
    """Our own bookkeeping, not a bad sample: there is no record to build a prompt from, so a retry
    would fail identically and be billed for the privilege."""
    llm = _StubLLM([GOOD_TOOL_INPUT])
    tmp = lane(PLACEHOLDER_TOOL_INPUT, llm)
    monkeypatch.setattr(br, "_load_records", lambda pids: {})
    br.fetch("CN")

    assert llm.calls == 0, "record-missing must not spend"
    assert _rows(tmp)[0]["error"] == "record-missing"


def test_retry_cost_is_separate_from_the_batch_ledger(lane):
    """The batch's own cost_usd is first-ingest-wins at the 50% rate. A live retry is a full-price
    new call, so it must be accumulated apart -- folding it in would corrupt a figure that a
    previous change already got wrong once ($0.67 recorded against $21.86 billed)."""
    llm = _StubLLM([GOOD_TOOL_INPUT])
    tmp = lane(PLACEHOLDER_TOOL_INPUT, llm)
    br.fetch("CN")

    report = json.loads((tmp / "map" / "map_report_CN.json").read_text(encoding="utf-8"))
    assert report["retry_live_calls"] == 1
    assert report["retry_live_usd"] > 0, "a live retry costs real money and must be stated"
    assert report["cost_usd"] == pytest.approx(
        report["cost_usd_batch_lane"] + report["retry_live_usd"], abs=0.01)
    assert "FULL rate" in report["cost_note"]

    state = json.loads((tmp / "map" / "batches_CN.json").read_text(encoding="utf-8"))
    assert state["retry_live_usd"] > 0
    batch = state["batches"][0]
    assert batch["cost_usd"] == pytest.approx(report["cost_usd_batch_lane"], abs=0.01), (
        "the retry must not have been added to the batch's own cost")
