"""Tests for the zero-score filters at emit time (finale plan H3 and H5).

Run from stages/p3-map:
    python -m pytest tests/test_submission_filters.py -q

Round 1 filed every KNOWN fire regardless of whether its verbatim quote was byte-grounded, and
persisted `trap_checks` without ever reading them. Both produce rows that look exactly like good
rows and score zero. Measured effect of the fix on the reference arm: Singapore 42 rows unchanged,
Malaysia 57 unchanged, Australia 43 -> 42 (one government-data-only 6.1 row dropped, one
ungrounded KNOWN row replaced by a grounded fire for the same baseline id).
"""
from __future__ import annotations

import pytest

from config.settings import INDICATORS
from src.p3map.output.submission import (
    COLUMNS, ECON_NAME, GOVERNMENT_DATA_EXCLUDED, NEW_CONF, multi_act_caveat,
    searched_but_found_nothing,
    unfilable_reason,
)

GROUNDED = {"quote_grounded_ws": True, "confidence": 0.9}
IN_FORCE = {"provision_in_force": True, "government_data_only": False}


def test_a_clean_fire_is_filable():
    assert unfilable_reason(GROUNDED, IN_FORCE, "6.1") is None


def test_an_ungrounded_quote_is_never_filed():
    """The snippet is the evidence; the host verifies column I against the source."""
    assert unfilable_reason({"quote_grounded_ws": False, "confidence": 1.0},
                            IN_FORCE, "6.1") == "ungrounded_quote"


def test_grounding_does_not_depend_on_the_discovery_tag():
    """Round 1 gated NEW rows only. The rule has no tag argument, which is the point."""
    import inspect
    assert "tag" not in inspect.signature(unfilable_reason).parameters


def test_a_provision_not_in_force_is_not_evidence():
    for tc in ({"provision_in_force": False},
               {"provision_in_force": False, "government_data_only": False}):
        assert unfilable_reason(GROUNDED, tc, "7.3") == "not_in_force"


def test_a_missing_trap_check_does_not_drop_a_row():
    """An older verdict file has no trap_checks; absence is not a finding."""
    assert unfilable_reason(GROUNDED, {}, "6.1") is None
    assert unfilable_reason(GROUNDED, {"provision_in_force": None}, "6.1") is None


def test_government_data_only_drops_exactly_the_indicators_the_codebook_names():
    for ind in ("6.1", "6.2", "6.3", "6.4", "7.3"):
        assert unfilable_reason(GROUNDED, {"government_data_only": True},
                                ind) == "government_data_only", ind
    # 7.5 measures government access to personal data: a government-only obligation is the
    # subject, not a disqualification. 7.1, 7.2 and 7.4 are not on the codebook's list either.
    for ind in ("7.1", "7.2", "7.4", "7.5"):
        assert unfilable_reason(GROUNDED, {"government_data_only": True}, ind) is None, ind


def test_the_excluded_set_is_indicators_this_stage_maps():
    assert GOVERNMENT_DATA_EXCLUDED <= set(INDICATORS)
    assert "7.5" not in GOVERNMENT_DATA_EXCLUDED


def test_the_rule_checks_groundedness_before_the_traps():
    """Order matters only for which reason is reported, and the report is read by a human."""
    assert unfilable_reason({"quote_grounded_ws": False},
                            {"provision_in_force": False}, "6.1") == "ungrounded_quote"


def test_the_confidence_floor_stays_new_only():
    """A baseline-reproducing row must not be dropped for low confidence."""
    assert unfilable_reason({"quote_grounded_ws": True, "confidence": 0.1}, IN_FORCE, "6.1") is None
    assert 0.0 < NEW_CONF < 1.0


def test_the_column_set_and_the_economy_names():
    assert COLUMNS[-1] == "Language of Source", "column N is last; column O is the host's formula"
    assert len(COLUMNS) == 14
    # the Coverage Matrix row labels, which its COUNTIFS matches exactly
    assert ECON_NAME["LA"] == "Lao PDR"
    assert ECON_NAME["TL"] == "Timor-Leste"
    assert ECON_NAME["CN"] == "China"
    assert set(ECON_NAME) >= {"SG", "MY", "AU", "CN", "LA", "TL"}


@pytest.mark.parametrize("ind", ["6.1", "7.5"])
def test_every_mapped_indicator_has_an_answer(ind):
    assert unfilable_reason(GROUNDED, IN_FORCE, ind) is None


def test_the_evaluator_matches_law_names_in_the_citing_direction():
    """The over-count Round 1 corrected by hand, computed instead.

    "Personal Data Protection Code of Practice for Banking Sector and Financial Institutions
    2017" shares all of "Personal Data Protection Act 2010"'s meaningful tokens, so dividing by
    the shorter name made every Code of Practice a match for the Act. Dividing by the CITED name's
    own tokens does not.
    """
    from config.lawnames import covers as _covers
    act = "Personal Data Protection Act 2010"
    code = ("Personal Data Protection Code of Practice For Banking Sector "
            "And Financial Institutions 2017")
    assert not _covers(code, act), "the Act does not name the Code of Practice"
    # a real match still matches, including across an amendment suffix
    assert _covers(act, "Personal Data Protection Act 2010 (Act 709)")
    assert _covers("Banking Act 1970", "Banking Act 1970")
    assert not _covers("Banking Act 1970", "Insurance Act 1966")


# ------------------------------------------------------- H4: the earned tag --

def test_kit_absence_state_reads_the_sample_kit_not_our_own_result():
    """Decision H4. The host defines KNOWN as "it was in the sample kit", so a no-provision row
    may only claim it where the kit carries its own absence row. Round 1 wrote KNOWN
    unconditionally, which claimed the kit contained cells it did not.

    Measured on run_2026-09-27's baseline: of 54 (economy, indicator) cells, 23 carry an absence
    row, 22 carry only positive rows, and 9 have no row at all (every Timor-Leste cell).
    """
    from src.p3map.output.submission import kit_absence_state

    # the kit records an absence: score 0 with no article cited
    assert kit_absence_state([{"articles_mentioned": "", "raw_score": "0"}]) == "reproduces"
    assert kit_absence_state([{"articles_mentioned": "[]", "raw_score": 0.0}]) == "reproduces"
    assert kit_absence_state([{"articles_mentioned": "None", "raw_score": "0.0"}]) == "reproduces"

    # the kit records a measure we did not find: a disagreement, never a reproduction
    assert kit_absence_state([{"articles_mentioned": "Art. 5", "raw_score": "1"}]) == "contradicts"

    # no row at all for the cell
    assert kit_absence_state([]) == "absent"

    # one absence row among several is enough to earn KNOWN
    assert kit_absence_state([{"articles_mentioned": "Art. 5", "raw_score": "1"},
                              {"articles_mentioned": "", "raw_score": 0.0}]) == "reproduces"


def test_only_a_reproduced_absence_earns_the_known_tag():
    """The emitter must tag from that state, and leave the column blank otherwise.

    Blank is a disclosed choice, not an oversight: the host's Instructions say the column takes two
    values, so submission_report_<ECON>.json counts the blanks to make the exposure visible.
    """
    import re
    from pathlib import Path

    src = (Path(__file__).resolve().parents[1]
           / "src/p3map/output/submission.py").read_text(encoding="utf-8")
    assert 'np_tag = "KNOWN" if kit == "reproduces" else ""' in src, \
        "the no-provision tag must be earned from the kit, not hard-coded"
    assert not re.search(r'"Discovery Tag":\s*"KNOWN"', src), \
        "an unconditional KNOWN is back in the no-provision row"
    assert "blank_discovery_tag" in src, "blank tags must be counted in the report"


# --------------------------------------------------------------------------- no-provision citation


def test_a_no_baseline_economy_names_no_law_rather_than_the_biggest_one():
    """Round 1 cited "the largest law in the corpus" as the governing law when no baseline row
    existed. For Timor-Leste that named "Aprova o Codigo Civil" -- the decree ENACTING the civil
    code -- as the governing law for data localisation, on 45 of its 110 filed rows. The civil code
    governs none of pillar 6, and a marker can open the PDF and see that.
    """
    laws = [
        {"economy": "TL", "law_name": "Aprova o Codigo Civil", "law_number": "10/2011",
         "source_url": "https://www.mj.gov.tl/jornal/a.pdf", "provision_count": 99999},
        {"economy": "TL", "law_name": "Lei da Proteccao de Dados", "law_number": "1/2020",
         "source_url": "https://www.mj.gov.tl/jornal/b.pdf", "provision_count": 12},
    ]
    name, number, url, lang, named = searched_but_found_nothing("Timor-Leste", laws)

    assert "Codigo Civil" not in name, "the largest law must not be presented as the governing law"
    assert named is False, "Notes must not claim a governing law was cited for reference"
    assert name == "Timor-Leste — no governing instrument identified"
    assert number == "" and lang == ""


def test_the_citation_says_how_widely_we_looked_and_where():
    """A negative finding is only worth anything if it says what it covered."""
    laws = [{"economy": "TL", "law_name": f"Lei {i}", "law_number": "",
             "source_url": "https://www.mj.gov.tl/jornal/x.pdf", "provision_count": 1}
            for i in range(2879)]
    _, _, url, _, _ = searched_but_found_nothing("Timor-Leste", laws)
    assert url.startswith("n/a"), "it must not masquerade as a working law-level URL"
    assert "2,879" in url, "the corpus size searched is the checkable part of the claim"
    assert "www.mj.gov.tl" in url, "and so is the portal it came from"


def test_the_portal_is_the_dominant_host_not_the_first_one():
    laws = ([{"economy": "TL", "source_url": "https://odd.example/x.pdf"}]
            + [{"economy": "TL", "source_url": "https://www.mj.gov.tl/y.pdf"}] * 20)
    _, _, url, _, _ = searched_but_found_nothing("Timor-Leste", laws)
    assert "www.mj.gov.tl" in url and "odd.example" not in url


def test_a_corpus_with_no_usable_urls_still_produces_a_citation():
    """A missing or non-http source_url must not crash the emitter or fake a host."""
    laws = [{"economy": "XX", "source_url": ""}, {"economy": "XX"}]
    name, _, url, _, named = searched_but_found_nothing("Nowhere", laws)
    assert named is False and name.startswith("Nowhere")
    assert "2 Nowhere instruments searched" in url, "no host claimed when none is known"


def test_an_economy_with_no_corpus_at_all_is_still_labelled():
    name, _, url, _, named = searched_but_found_nothing("Hold-out", [])
    assert named is False
    assert "no corpus available" in name and "hold-out economy" in url


# ------------------------------------------------------------------- multi-act citation caveat


def test_a_single_act_file_carries_no_caveat():
    assert multi_act_caveat(1, 1) == ("", "")
    assert multi_act_caveat(None, 1) == ("", "")
    assert multi_act_caveat(None, None) == ("", "")


def test_a_later_act_is_told_the_law_name_is_probably_wrong():
    """Measured: of 364 multi-act Timorese gazette documents, 364 carry ONE document-level law_name
    across every act and 0 vary by act. So every act but one per file is mislabelled, while upstream
    still reports citation_confidence 'exact'."""
    bucket, note = multi_act_caveat(3, 3)
    assert bucket == "later_act"
    assert "act 3 of 3" in note
    assert "most likely belongs to a different act" in note
    assert "article, quoted text and URL are verified" in note, "the rest of the row still stands"


def test_the_first_act_is_called_probable_not_wrong_and_not_silently_exempt():
    """"A gazette's document title names its first act" is an inference from ordering that has not
    been checked against the PDFs. Warning as if it were wrong overstates; exempting it silently
    relies on the guess. So it says probable, and says the inference is unconfirmed."""
    bucket, note = multi_act_caveat(1, 22)
    assert bucket == "first_act"
    assert "probably right" in note
    assert "have not confirmed" in note


def test_a_missing_act_index_is_uncheckable_rather_than_assumed_fine():
    bucket, note = multi_act_caveat(None, 4)
    assert bucket == "act_unknown"
    assert "not recorded" in note


def test_every_caveat_tells_the_reader_what_to_do():
    for args in ((1, 22), (3, 3), (None, 4)):
        _, note = multi_act_caveat(*args)
        assert note.startswith("CITATION CAVEAT:")
        assert "source" in note and ("confirm" in note or "confirmed" in note)
