"""A superseded row is dropped whatever case the collector wrote the note in.

Until 2026-09-23 the test was a case-sensitive `"superseded by" in crawl_notes`, applied in four
places. China's MIIT provenance row 32 reads "SUPERSEDED by 令68 of 2024-01-18" - so the text it
holds was replaced in 2024, and it would have been extracted and scored as current law, while an
otherwise identical note written in lowercase two rows away would have been dropped. Which
behaviour you got depended on how a human capitalised a sentence.

The developer's instruction on 2026-09-23: if it says superseded by, do not record it.
"""

from __future__ import annotations

import pytest

from rdtii_p2.ingest import is_superseded


@pytest.mark.parametrize("note", [
    "superseded by Act 12 of 2024",
    "SUPERSEDED by 令68 of 2024-01-18",
    "Superseded By the 2023 consolidation",
    "  the held text is SuPeRsEdEd By a later print  ",
    "note: superseded by, see row 7",
])
def test_every_casing_is_dropped(note):
    assert is_superseded(note) is True


@pytest.mark.parametrize("note", [
    None,
    "",
    "THE HELD TEXT IS SUPERSEDED.",          # no "by" - MIIT row 26, deliberately kept
    "supersedes the 2015 catalogue",          # this row REPLACES another; it is the current text
    "superseded",
    "read by the developer and not taken",
])
def test_these_are_kept(note):
    assert is_superseded(note) is False


def test_the_real_china_note_is_now_caught():
    """The exact string from corpus/CN/manual/miit/provenance.tsv row 32."""
    note = ("this is the text the 法律法规 list serves. SUPERSEDED by 令68 of 2024-01-18 "
            "— row 7, still to get. Kept as the best available.")
    assert is_superseded(note) is True
