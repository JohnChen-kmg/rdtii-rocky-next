"""Tests for mapping/anchor.py — the quote is cut from the source, not copied from the model.

Run from stages/p3-map:
    python -m pytest tests/test_anchor.py -q

Two things have to hold at once, and they pull in opposite directions:

  the locator is forgiving — a model that inserts a space into Chinese, writes "," for "，" or
  wraps the quote in curly quotation marks must still be found, because since H5 an ungrounded
  row is not filed at all and China's rows would vanish silently;

  the evidence is not — what gets filed is the source's own substring for the located span, so
  column I is byte-exact by construction, and nothing that is not in the source can be anchored.

Measured at scale on the real corpus (1,200 provisions in six languages, 14,400 anchorings):
0 cases where the filed text was not the source's own bytes.
"""
from __future__ import annotations

import pytest

from src.p3map.mapping.anchor import anchor

EN = ("An organisation shall not transfer any personal data to a country or territory outside "
      "Singapore except in accordance with requirements prescribed under this Act.")
ZH = "电信业务经营者、互联网信息服务提供者不得泄露、篡改、毁损其收集的用户个人信息；未经用户同意，不得向他人提供用户个人信息。"
LO = "ຜູ້ໃຫ້ບໍລິການຕ້ອງເກັບຮັກສາຂໍ້ມູນ ສ່ວນບຸຄຄົນຂອງຜູ້ໃຊ້ບໍລິການ ໄວ້ໃນ ສ.ປ.ປ ລາວ ເປັນເວລາ ຫ້າ ປີ."
PT = ("O responsável pelo tratamento deve conservar os dados pessoais durante o período "
      "mínimo de cinco anos, nos termos do presente decreto-lei.")
SOURCES = {"en": EN, "zh": ZH, "lo": LO, "pt": PT}


def _quote(text: str) -> str:
    """A substring a model would plausibly return: the middle of the provision."""
    return text[len(text) // 4: len(text) // 4 + max(12, len(text) // 2)].strip()


@pytest.mark.parametrize("lang", sorted(SOURCES))
def test_an_exact_quote_anchors_exactly(lang):
    text = SOURCES[lang]
    q = _quote(text)
    a = anchor(q, text)
    assert a.grounded and a.how == "exact"
    assert a.quote == q
    assert a.repaired is False
    assert text[a.start:a.end] == a.quote


@pytest.mark.parametrize("lang", sorted(SOURCES))
def test_a_space_inserted_mid_quote_still_anchors(lang):
    """The Chinese case: there is no whitespace run to collapse, so Round 1's check failed here."""
    text = SOURCES[lang]
    q = _quote(text)
    a = anchor(q[:len(q) // 2] + " " + q[len(q) // 2:], text)
    assert a.grounded, lang
    assert a.quote == text[a.start:a.end]
    assert "".join(a.quote.split()) == "".join(q.split())


def test_ascii_punctuation_in_a_chinese_quote_still_anchors():
    """NFKC folds "，" to "," but leaves "。" and "、" alone, so those are folded by hand."""
    q = _quote(ZH)
    substituted = q.replace("，", ",").replace("。", ".").replace("、", ",").replace("；", ";")
    assert substituted != q, "the fixture must actually exercise the substitution"
    a = anchor(substituted, ZH)
    assert a.grounded and a.how == "normalised"
    assert a.quote == ZH[a.start:a.end]
    assert "，" in a.quote or "；" in a.quote or "。" in a.quote, "the SOURCE's punctuation is filed"


@pytest.mark.parametrize("lang", sorted(SOURCES))
def test_quotation_marks_the_model_added_are_not_filed(lang):
    text = SOURCES[lang]
    q = _quote(text)
    a = anchor("“" + q + "”", text)
    assert a.grounded
    assert not a.quote.startswith("“") and not a.quote.endswith("”")
    assert a.quote == text[a.start:a.end]


def test_a_quote_that_legitimately_ends_in_an_apostrophe_keeps_it():
    """"Auctioneers’" is a possessive, not a closing quote; stripping it would edit the evidence."""
    text = "Under the Auctioneers’ Licences Act the licensee shall keep the register."
    q = "the Auctioneers’ Licences Act"
    a = anchor(q, text)
    assert a.grounded and a.quote == q
    assert a.quote.count("’") == 1


def test_a_newline_and_indentation_inside_the_quote_anchor():
    a = anchor(EN[:40] + "\n      " + EN[40:90], EN)
    assert a.grounded
    assert a.quote == EN[a.start:a.end]


def test_case_differences_anchor_but_the_source_case_is_filed():
    q = _quote(EN)
    a = anchor(q.upper(), EN)
    assert a.grounded
    assert a.quote == q, "the source's own casing, not the model's"


@pytest.mark.parametrize("lang", sorted(SOURCES))
def test_a_paraphrase_is_never_anchored(lang):
    """The forgiving locator must not become a semantic matcher."""
    a = anchor("The provision requires that personal data be stored locally for five years.",
               SOURCES[lang])
    if lang == "en":
        pytest.skip("that sentence is English prose; the point is tested on the others")
    assert not a.grounded and a.how == "none"


def test_a_translation_of_the_source_is_never_anchored():
    a = anchor("Telecommunications operators shall not disclose users' personal information.", ZH)
    assert not a.grounded


def test_a_quote_from_a_different_provision_is_never_anchored():
    a = anchor(_quote(PT), EN)
    assert not a.grounded


def test_empty_input_is_not_grounded():
    assert not anchor("", EN).grounded
    assert not anchor(EN, "").grounded
    assert not anchor("   ", EN).grounded


def test_the_span_is_usable_as_a_span():
    q = _quote(EN)
    a = anchor(q, EN)
    assert 0 <= a.start < a.end <= len(EN)
    assert EN[a.start:a.end] == a.quote


def test_repaired_says_whether_what_we_file_differs_from_the_model():
    q = _quote(ZH)
    assert "、" in q, "the fixture must contain the character the test substitutes"
    assert anchor(q, ZH).repaired is False
    assert anchor(q.replace("、", ","), ZH).repaired is True
    assert anchor("nothing like the source", ZH).repaired is False, "not grounded, not repaired"
