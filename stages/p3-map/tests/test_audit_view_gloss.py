"""The audit page must show the English and must never let it pass for evidence.

Checklist item 11 asks that the audit interface "can be driven by a non-technical policy officer",
and C3a + C3b are 15 marks. For China, Lao PDR and Timor-Leste it could not be: this page rendered
the quote in the source script and nothing else, so a reviewer who does not read it had no way to
check what the tool claimed. The gloss was produced on 28 September and wired only to the Excel
workbook, which is not the interface anyone is marked on.

Showing a translation is safe here and forbidden in the emitter, and the difference is the whole
point: this module writes a review page, output/submission.py writes column I. So these tests pin
both halves -- that the English appears and is labelled, and that it cannot be mistaken for the
filed quote.
"""
from __future__ import annotations

import dataclasses
import json

import pytest

from config.settings import SETTINGS
from src.p3map.verify import audit_view as av

VERDICT = {
    "provision_id": "p1", "economy": "CN", "law_name": "网络安全法",
    "article_section": "Art. 37", "trap_checks": {"provision_in_force": True},
    "verdicts": [{"indicator": "6.2", "applies": True, "score_hint": "1",
                  "coverage": "Horizontal", "confidence": 0.9, "quote_grounded_ws": True,
                  "verbatim_quote": "应当在境内存储", "rationale": "6.2 storage branch"}],
}


@pytest.fixture
def page(tmp_path, monkeypatch):
    """Render index_CN.html with whichever glosses the test installs."""
    for sub in ("map", "audit", "verify"):
        (tmp_path / sub).mkdir(parents=True)
    (tmp_path / "map" / "verdicts_CN.jsonl").write_text(
        json.dumps(VERDICT, ensure_ascii=False) + "\n", encoding="utf-8")
    monkeypatch.setattr(av, "SETTINGS", dataclasses.replace(SETTINGS, out_dir=tmp_path))

    def render(quote_gloss=None, section_gloss=None):
        if quote_gloss is not None:
            (tmp_path / "audit" / "gloss_CN.jsonl").write_text(
                json.dumps(quote_gloss, ensure_ascii=False) + "\n", encoding="utf-8")
        if section_gloss is not None:
            (tmp_path / "audit" / "gloss_sections_CN.jsonl").write_text(
                json.dumps(section_gloss, ensure_ascii=False) + "\n", encoding="utf-8")
        av.render("CN")
        return (tmp_path / "audit" / "index_CN.html").read_text(encoding="utf-8")

    return render


QGLOSS = {"provision_id": "p1", "indicator": "6.2", "english": "shall be stored domestically",
          "is_literal": True, "model": "claude-haiku-4-5", "original": "应当在境内存储"}
SGLOSS = {"provision_id": "p1", "english": "Article 37. Operators shall store data domestically.",
          "is_literal": True, "model": "claude-haiku-4-5"}


def test_the_english_appears_in_the_collapsed_row(page):
    """Not only behind the toggle. A reviewer who cannot read the source script would otherwise have
    to expand every row to learn anything at all, which is not a usable review surface."""
    html = page(QGLOSS, SGLOSS)
    summary = html.split("<summary>")[1].split("</summary>")[0]
    assert "shall be stored domestically" in summary
    assert "应当在境内存储" in summary, "the original stays visible beside it"


def test_every_translation_says_it_is_a_translation_and_not_evidence(page):
    html = page(QGLOSS, SGLOSS)
    assert html.count("machine translation, not evidence") == 2, "quote gloss and section gloss"
    assert "claude-haiku-4-5" in html, "the model is named"
    assert "It is never what we file" in html


def test_the_filed_quote_is_labelled_as_the_source_s_own_bytes(page):
    """The page must make plain which string is the evidence, because both are on screen."""
    html = page(QGLOSS, SGLOSS)
    assert "Quote, as filed (the source&#x27;s own bytes)" in html or \
           "Quote, as filed (the source's own bytes)" in html


def test_a_refused_gloss_is_flagged_rather_than_shown_as_clean(page):
    """is_literal false means the source is too damaged to render. Lao PDR returned 174 of 183
    provision glosses that way, and a reviewer must not read those as a faithful rendering."""
    html = page({**QGLOSS, "is_literal": False}, None)
    assert "too garbled" in html
    assert "EN ⚠" in html, "and the warning reaches the collapsed row too"


def test_a_missing_gloss_file_renders_the_page_anyway(page):
    """S9b is optional and costs money. The review surface must open whether or not it has run."""
    html = page(None, None)
    assert "<tr data-ind=" in html
    assert "machine translation, not evidence" not in html, "no per-row gloss box"
    assert "About the English" not in html, "and no note explaining a feature the page does not use"
    assert "应当在境内存储" in html, "the evidence is still there"


def test_an_empty_english_string_is_not_rendered_as_a_translation(page):
    """A gloss that came back blank must not produce an empty labelled box implying we translated."""
    html = page({**QGLOSS, "english": "   "}, None)
    assert "machine translation, not evidence" not in html
    assert "About the English" not in html


def test_the_note_counts_how_many_rows_are_translated_and_how_many_are_rough(page):
    """A reviewer opening the page should learn the scale before reading a single row."""
    html = page({**QGLOSS, "is_literal": False}, SGLOSS)
    assert "1 of 1 rows carry one" in html
    assert "too damaged" in html


def test_a_corrupt_gloss_line_does_not_break_the_page(page, tmp_path):
    (tmp_path / "audit" / "gloss_CN.jsonl").write_text(
        "{not json\n" + json.dumps(QGLOSS, ensure_ascii=False) + "\n", encoding="utf-8")
    av.render("CN")
    html = (tmp_path / "audit" / "index_CN.html").read_text(encoding="utf-8")
    assert "shall be stored domestically" in html
