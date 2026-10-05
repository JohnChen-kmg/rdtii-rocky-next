"""Documents that came out with no provisions although they are written in articles (4 October 2026).

Three causes, each found by opening the frozen text of a real document:
  * seven Timorese decree-laws of 2003 to 2005 put a NON-BREAKING space in "Artigo 1.o";
  * a treaty text carried by a Timorese resolution writes "ARTIGO 7";
  * the Lao gazette's own English editions were split with the Lao pattern, because a crawl run from the
    interface carries neither side file and the crawler's language for the file was lost.
"""
from __future__ import annotations

import json

from rdtii_p2 import segment_civil, sidecars
from rdtii_p2.cli import _segment_for

BODY = "O presente diploma regula o exercicio da actividade e as obrigacoes dos operadores licenciados, " \
       "nos termos da lei e dos regulamentos em vigor, incluindo os deveres de informacao ao regulador."
NBSP = " "


def _por(word: str, space: str) -> str:
    return "".join(f"{word}{space}{n}.º\nObjecto\n{n}. {BODY}\n" for n in (1, 2, 3))


def test_a_heading_with_a_non_breaking_space_is_a_heading():
    plain = segment_civil.segment_civil(_por("Artigo", " "), "por")
    hard = segment_civil.segment_civil(_por("Artigo", NBSP), "por")
    assert plain.n_sections == 3
    assert hard.n_sections == 3, "the text layer of the 2003 decree-laws separates word and number with U+00A0"


def test_a_heading_in_capitals_is_a_heading():
    text = "".join(f"ARTIGO {n}\nREUNIAO DE ALTOS FUNCIONARIOS\n{BODY}\n" for n in (1, 2, 3))
    assert segment_civil.segment_civil(text, "por").n_sections == 3


ENGLISH = "".join(
    f"Article {n} {title}\n"
    f"The payment system operator shall keep its records and report to the Bank of the Lao PDR in accordance with "
    f"Article {n + 20} of this Law\nand with the regulations issued under it, within the period that they set.\n"
    for n, title in ((1, "Objectives"), (2, "Payment System"), (3, "Definitions")))


def test_an_english_edition_in_an_article_economy_is_split_by_its_articles():
    assert _segment_for(ENGLISH, "eng", "lao").n_sections == 3
    assert _segment_for(ENGLISH, "lao", "lao").n_sections == 0, "read as Lao it gave nothing: the defect"


def test_a_reference_at_the_start_of_a_line_is_not_a_heading():
    text = ENGLISH.replace("in accordance with Article 21 of this Law\n", "in accordance with\nArticle 21 of this Law\n")
    got = _segment_for(text, "eng", "lao")
    assert got.n_sections == 3, "'Article 21 of this Law' opens a wrapped line; it is a cross-reference"


def test_english_in_a_common_law_economy_keeps_the_common_law_segmenter():
    """Singapore, Australia and Malaysia are untouched: the English-article profile is only tried when the
    economy's own language is written in articles."""
    assert segment_civil.ENGLISH_ARTICLES not in ("eng", "msa")
    seen = []
    real = segment_civil.segment_civil
    segment_civil.segment_civil = lambda text, language: seen.append(language) or real(text, language)
    try:
        _segment_for(ENGLISH, "eng", "eng")
        _segment_for(ENGLISH, "eng", None)
        _segment_for(ENGLISH, "msa", "msa")
    finally:
        segment_civil.segment_civil = real
    assert seen == []


def test_the_crawlers_language_is_read_from_the_manifest_when_no_side_file_is_there(tmp_path):
    rows = [{"doc_id": "la-la2202-001", "contract_meta": {"language": "lao", "language_source": "portal_field"}},
            {"doc_id": "la-la2202en-001", "contract_meta": {"language": "eng", "language_source": "portal_field",
                                                            "is_translation": True}},
            {"doc_id": "la-la9-001"}]                                   # a row with no facts takes the default
    (tmp_path / "manifest.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    facts = sidecars.load_facts(tmp_path, registry_default_language="lao")
    assert (facts["la-la2202en-001"].language, facts["la-la2202en-001"].language_source) == ("eng", "portal_field")
    assert facts["la-la2202-001"].language == "lao"
    assert "la-la9-001" not in facts            # nothing declared: the run loop gives it the economy's language


def test_a_side_file_keeps_its_say_over_the_manifest(tmp_path):
    (tmp_path / "law_table.csv").write_text("doc_id,language,use\nla-la1-001,lao,in_scope\n", encoding="utf-8")
    (tmp_path / "manifest.jsonl").write_text(
        json.dumps({"doc_id": "la-la1-001", "contract_meta": {"language": "eng"}}) + "\n", encoding="utf-8")
    assert sidecars.load_facts(tmp_path)["la-la1-001"].language == "lao"


def test_the_crawlers_language_is_read_from_the_file_beside_the_manifest(tmp_path):
    """Since 5 October 2026 the crawler writes the adapters' facts to manifest_meta.jsonl, because its own
    contract gate refuses any other field in the manifest. Extraction reads that file first."""
    meta = [{"doc_id": "la-la2202en-001", "contract_meta": {"language": "eng", "language_source": "portal_field"}},
            {"doc_id": "la-la2202-001", "contract_meta": {"language": "lao", "language_source": "portal_field"}}]
    (tmp_path / "manifest_meta.jsonl").write_text("".join(json.dumps(r) + "\n" for r in meta), encoding="utf-8")
    (tmp_path / "manifest.jsonl").write_text(
        json.dumps({"doc_id": "la-la2202en-001"}) + "\n" + json.dumps({"doc_id": "la-la2202-001", "contract_meta": {"language": "por"}}) + "\n",
        encoding="utf-8")
    facts = sidecars.load_facts(tmp_path, registry_default_language="lao")
    assert (facts["la-la2202en-001"].language, facts["la-la2202en-001"].language_source) == ("eng", "portal_field")
    assert facts["la-la2202-001"].language == "lao"         # the file beside the manifest has its say first
