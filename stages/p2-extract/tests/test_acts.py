"""Locating the acts inside one gazette issue, and refusing to guess when one is missing.

912 of 1,922 Timorese documents hold more than one act, and `tl-ldcn-001` holds both Lei 1/2026
and Decreto-Lei 13/2026, each with its own Article 6. Until 2026-09-23 every provision in such a
document was attributed to a single law.

The rule these tests pin is the completeness gate: `act_index` is emitted only when EVERY act the
sidecar names was found at a distinct offset. A missed act does not leave a gap in the output, it
leaves its articles inside the act before it, attributed to the wrong law - so a partial split is
worse than none.
"""

from __future__ import annotations

from rdtii_p2 import acts

TWO_ACTS = """\
SUMÁRIO
LEI N.º 1/2026 ................................................ 3
DECRETO-LEI N.º 13/2026 ....................................... 9

LEI N.º 1/2026
de 25 de Março
Lei da Concorrência

Artigo 1.º
Objecto
A presente lei estabelece o regime jurídico da concorrência.

Artigo 6.º
Práticas restritivas
São proibidos os acordos entre empresas.

DECRETO-LEI N.º 13/2026
de 25 de Março

Artigo 1.º
Âmbito
O presente diploma estabelece medidas de estabilização.

Artigo 6.º
Vigência
O presente diploma entra em vigor no dia seguinte.
"""

SIDECAR = [
    {"portal_id": "L-1-2026", "law_number": "1/2026",
     "law_name": "Lei da Concorrência", "document_kind": "principal_act"},
    {"portal_id": "DL-13-2026", "law_number": "13/2026",
     "law_name": "Medidas de Estabilização", "document_kind": "principal_act"},
]


def test_both_acts_are_located_and_ordered_by_position():
    spans, located = acts.locate(TWO_ACTS, SIDECAR)
    assert located == 2 and len(spans) == 2
    assert [s.index for s in spans] == [1, 2]
    assert spans[0].law_number == "1/2026"
    assert spans[1].law_number == "13/2026"
    assert spans[0].char_end == spans[1].char_start        # contiguous, no gap


def test_the_summario_listing_is_not_the_anchor():
    """An issue restates every act up front; the contents entry must not open the act."""
    spans, _ = acts.locate(TWO_ACTS, SIDECAR)
    # the real LEI header is the second occurrence, after the dot-leader listing
    assert TWO_ACTS.count("LEI N.º 1/2026") == 2
    assert spans[0].char_start > TWO_ACTS.index("....")


def test_each_act_keeps_its_own_article_numbering():
    spans, _ = acts.locate(TWO_ACTS, SIDECAR)
    first = TWO_ACTS[spans[0].char_start:spans[0].char_end]
    second = TWO_ACTS[spans[1].char_start:spans[1].char_end]
    assert "Artigo 1." in first and "Artigo 6." in first
    assert "Artigo 1." in second and "Artigo 6." in second   # BOTH acts have an Article 6


def test_a_provision_is_assigned_by_where_its_snippet_starts():
    spans, _ = acts.locate(TWO_ACTS, SIDECAR)
    in_second = TWO_ACTS.index("Âmbito")
    assert acts.act_at(spans, in_second).index == 2
    in_first = TWO_ACTS.index("Objecto")
    assert acts.act_at(spans, in_first).index == 1


def test_an_unlocatable_act_withholds_the_whole_document():
    """The gate: one missing header means no act_index at all, not a partial split."""
    sidecar = SIDECAR + [{"portal_id": "RG-99-2026", "law_number": "99/2026",
                          "law_name": "Não está no texto", "document_kind": "principal_act"}]
    spans, located = acts.locate(TWO_ACTS, sidecar)
    assert spans == []            # withheld
    assert located == 2           # and the shortfall is reported: 2 of 3


def test_a_single_act_document_is_left_alone():
    spans, located = acts.locate(TWO_ACTS, SIDECAR[:1])
    assert spans == [] and located == 1


def test_decreto_lei_is_not_matched_as_decreto_do_governo():
    """Longest-first alternation: the kind words overlap and the wrong one attributes the
    act to a different instrument entirely."""
    text = "DECRETO-LEI N.º 13/2026\nArtigo 1.º\nTexto.\n"
    spans, located = acts.locate(
        text, [{"portal_id": "DG-13-2026", "law_number": "13/2026", "law_name": "x",
                "document_kind": "principal_act"},
               {"portal_id": "DL-13-2026", "law_number": "13/2026", "law_name": "y",
                "document_kind": "principal_act"}])
    assert spans == []            # DG-13-2026 is genuinely absent, so the gate withholds
    assert located == 1


def test_a_soft_hyphen_inside_the_kind_word_still_matches():
    """U+00AD is invisible in a PDF and splits DECRETO-LEI in two."""
    text = "DECRETO­-LEI N.º 4/2019\nArtigo 1.º\nTexto suficiente aqui.\n"
    spans, located = acts.locate(
        text, [{"portal_id": "DL-4-2019", "law_number": "4/2019", "law_name": "z",
                "document_kind": "principal_act"},
               {"portal_id": "L-9-2019", "law_number": "9/2019", "law_name": "w",
                "document_kind": "principal_act"}])
    assert located == 1           # the DL was found; the L is absent, so the gate holds


def test_a_malformed_portal_id_is_skipped_not_guessed():
    spans, located = acts.locate(TWO_ACTS, [{"portal_id": "", "law_number": "1/2026",
                                             "law_name": "x", "document_kind": "y"},
                                            SIDECAR[1]])
    assert spans == [] and located == 1
