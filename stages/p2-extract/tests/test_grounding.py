"""T5 gate behavior: source_text[a:b] == snippet, drop on mismatch."""

import pytest

from rdtii_p2 import ground

TEXT = "PART 6\n26.—(1) An organisation must not transfer any personal data.\n(2) More."


def test_copy_grounded_round_trip():
    start = TEXT.index("An organisation")
    end = TEXT.index("personal data.") + len("personal data.")
    grounded = ground.copy_grounded(TEXT, start, end)
    assert grounded.snippet == TEXT[start:end]
    ground.verify(TEXT, grounded.char_start, grounded.char_end, grounded.snippet)
    assert grounded.context_before.endswith("26.—(1) ")
    assert grounded.context_after.startswith("\n(2)")


def test_corrupted_offset_is_rejected():
    start = TEXT.index("An organisation")
    snippet = "An organisation must not transfer"
    with pytest.raises(ground.GroundingError):
        ground.verify(TEXT, start + 1, start + 1 + len(snippet), snippet)


def test_llm_text_never_trusted():
    # an LLM 'quote' that paraphrases must fail the byte-exact gate
    paraphrase = "An organization must not transfer personal data"
    assert ground.locate_exact(TEXT, paraphrase) is None
    with pytest.raises(ground.GroundingError):
        ground.verify(TEXT, 8, 8 + len(paraphrase), paraphrase)


def test_locate_exact_prefers_nearest_to_hint():
    text = "alpha beta alpha beta alpha"
    assert ground.locate_exact(text, "alpha", hint_start=0) == 0
    assert ground.locate_exact(text, "alpha", hint_start=14) == 11
    assert ground.locate_exact(text, "alpha", hint_start=len(text)) == 22


def test_out_of_bounds_offsets_rejected():
    with pytest.raises(ground.GroundingError):
        ground.copy_grounded(TEXT, 10, len(TEXT) + 5)
