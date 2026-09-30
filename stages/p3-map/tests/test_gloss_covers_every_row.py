"""The section gloss must cover every provision that becomes a workbook row.

The first version covered only upheld fires, the second every fire. Both left a reviewer of a
Chinese, Lao or Portuguese economy looking at untranslated text on two sheets:

  QA NotInForce  a provision the trap check flagged. It usually never fired -- 68 of the 70 on
                 this run did not -- so a fire-keyed pass skipped essentially all of them.
  QA Errors      a provision whose verdict failed schema validation. It has no verdicts array at
                 all, so every fire-keyed filter skipped it by construction.

What must NOT be glossed is the provision the mapper read and declined. It is not a row on any
sheet, and there are 5,777 of them -- about $14 of translation that no surface would show.
"""
from __future__ import annotations

import dataclasses
import json

import pytest

from config.settings import SETTINGS
from src.p3map.output import gloss as gloss_mod


class _StubLLM:
    model = "stub"
    usage = {}

    def complete(self, prompt, schema, max_tokens=0):  # noqa: ANN001, ARG002
        return {"english": "ENGLISH", "is_literal": True}


@pytest.fixture
def run_dir(tmp_path, monkeypatch):
    """Four provisions, one of each kind the mapper can produce."""
    (tmp_path / "map").mkdir(parents=True)
    (tmp_path / "index").mkdir()

    rows = [
        {"provision_id": "p-fire", "law_name": "Act A", "article_section": "s.1",
         "trap_checks": {"provision_in_force": True},
         "verdicts": [{"indicator": "6.1", "applies": True, "verbatim_quote": "q"}]},
        {"provision_id": "p-nif", "law_name": "Act B", "article_section": "s.2",
         "trap_checks": {"provision_in_force": False},
         "verdicts": [{"indicator": "6.1", "applies": False}]},
        {"provision_id": "p-err", "error": "ValidationError: verdicts Field required"},
        {"provision_id": "p-declined", "law_name": "Act D", "article_section": "s.4",
         "trap_checks": {"provision_in_force": True},
         "verdicts": [{"indicator": "6.1", "applies": False}]},
    ]
    with (tmp_path / "map" / "verdicts_CN.jsonl").open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    with (tmp_path / "index" / "prefilter_corpus.jsonl").open("w", encoding="utf-8") as f:
        for pid, law in (("p-fire", "Act A"), ("p-nif", "Act B"),
                         ("p-err", "Act C"), ("p-declined", "Act D")):
            f.write(json.dumps({"provision_id": pid, "law_name": law,
                                "article_section": "s.x", "text": "原文"}) + "\n")

    monkeypatch.setattr(gloss_mod, "SETTINGS",
                        dataclasses.replace(SETTINGS, out_dir=tmp_path,
                                            index_dir=tmp_path / "index"))
    monkeypatch.setattr(gloss_mod, "get_llm", lambda *a, **k: _StubLLM())
    monkeypatch.setattr(gloss_mod, "usd", lambda *a, **k: 0.0)
    monkeypatch.setattr(gloss_mod.manifest, "record", lambda *a, **k: None)
    return tmp_path


def _glossed(run_dir) -> dict[str, dict]:  # noqa: ANN001
    path = run_dir / "audit" / "gloss_sections_CN.jsonl"
    with path.open(encoding="utf-8") as f:
        return {json.loads(line)["provision_id"]: json.loads(line) for line in f}


def test_fires_not_in_force_and_errors_are_all_glossed(run_dir):
    gloss_mod.run_section_gloss("CN")
    got = _glossed(run_dir)
    assert "p-fire" in got, "a fire must be glossed"
    assert "p-nif" in got, "QA NotInForce shows this row and would show it untranslated"
    assert "p-err" in got, "QA Errors shows this row and it has no verdicts array to key on"


def test_a_declined_provision_is_not_glossed(run_dir):
    """It is not a row on any sheet. Translating it would buy nothing a reviewer can open."""
    gloss_mod.run_section_gloss("CN")
    assert "p-declined" not in _glossed(run_dir)


def test_an_error_row_gets_its_law_name_from_the_corpus(run_dir):
    """Its verdict is what failed to parse, so the reply cannot name the law."""
    gloss_mod.run_section_gloss("CN")
    assert _glossed(run_dir)["p-err"]["law_name"] == "Act C"


def test_the_language_is_named_rather_than_left_to_inference(run_dir):
    """`language_of_source_name` was read from the verdict row and is absent from all of them,
    so every gloss before this said "the source language" and let the model guess."""
    gloss_mod.run_section_gloss("CN")
    assert _glossed(run_dir)["p-fire"]["language_of_source"] == "Chinese"


def test_a_second_run_adds_only_what_is_missing(run_dir):
    """Resume-safe: the widened pass must not re-bill the provisions already glossed."""
    gloss_mod.run_section_gloss("CN")
    before = len(_glossed(run_dir))
    again = gloss_mod.run_section_gloss("CN")
    assert again["glossed"] == 0
    assert len(_glossed(run_dir)) == before
