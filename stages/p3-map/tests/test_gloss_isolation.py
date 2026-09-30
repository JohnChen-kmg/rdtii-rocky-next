"""The English gloss exists for the reviewer and must never reach the submission.

The standing rule is that a translated string never becomes a verbatim snippet. The safest way to
keep a rule is to make breaking it impossible rather than merely forbidden, so the gloss lives in
its own file that the emitter does not open. These tests pin that arrangement.
"""
from __future__ import annotations

import re
from pathlib import Path

STAGE = Path(__file__).resolve().parents[1]
SUBMISSION = (STAGE / "src/p3map/output/submission.py").read_text(encoding="utf-8")
GLOSS = (STAGE / "src/p3map/output/gloss.py").read_text(encoding="utf-8")


def test_the_emitter_never_reads_a_gloss():
    """No code path can carry a machine translation into column I.

    Checks for a READ, not for the word: the emitter may discuss the arrangement in a comment, and
    the first version of this test failed on exactly that -- a stale comment left over from a
    reverted change, which was worth finding but is not the thing being guarded.
    """
    assert "gloss_" not in SUBMISSION, "submission.py names a gloss file"
    assert "from src.p3map.output.gloss" not in SUBMISSION
    assert "import gloss" not in SUBMISSION
    assert not re.search(r'"audit"\s*/\s*f?"gloss', SUBMISSION)


def test_the_gloss_writes_only_to_audit():
    """It must not write into map/, verify/ or submission/, which feed the CSV."""
    writes = re.findall(r'out_dir\s*=\s*SETTINGS\.out_dir\s*/\s*"([^"]+)"', GLOSS)
    assert writes, "no write target found — has the module been restructured?"
    assert set(writes) == {"audit"}, f"gloss writes to {sorted(set(writes))}, expected only audit/"
    for forbidden in ('"submission"', '"map" / f"verdicts', '"verify" / f"verified'):
        if forbidden.startswith('"map"') or forbidden.startswith('"verify"'):
            continue          # it READS those, which is fine
    assert 'SETTINGS.out_dir / "submission"' not in GLOSS


def test_every_gloss_carries_its_original_and_says_it_is_machine_made():
    """A gloss is read against the bytes, never instead of them."""
    assert '"original": m["quote"]' in GLOSS, "the source text must travel with the gloss"
    assert '"machine_translation": True' in GLOSS
    assert '"model": client.model' in GLOSS


def test_english_rows_are_not_glossed():
    """Nothing to translate, and no reason to spend on it."""
    assert "language_of_source" in GLOSS


def test_the_glosser_may_refuse():
    """OCR damage must be reportable rather than smoothed into a clean sentence.

    Measured on this run: 16 of Lao PDR's 117 quotes came back is_literal false, and the flagged
    text is genuinely corrupt -- the Lao for "not less than ten years" survives OCR as characters
    that do not spell it. Those quotes are still correctly grounded, because they are the source's
    own bytes, but a host reviewer checking them against the PDF would see the damage.
    """
    assert '"is_literal"' in GLOSS and "required" in GLOSS
    assert "too garbled" in GLOSS or "garbled" in GLOSS
