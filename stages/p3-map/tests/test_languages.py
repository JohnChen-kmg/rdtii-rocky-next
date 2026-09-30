"""Tests for config.languages — the two directions a language has to travel.

Run from stages/p3-map:
    python -m pytest tests/test_languages.py -q

S2 needs a code, to pick the selection threshold's offset. Column N of the host sheet needs a
name, and it is REQUIRED and marked: "Original language of the legal document — e.g. Thai,
Vietnamese, Bahasa Indonesia, Russian, English. Drives criterion C1c."
"""
from __future__ import annotations

from config.languages import NAMES, host_name, iso
from config.selection import load_config


def test_iso_accepts_a_code_or_a_name():
    assert iso("eng") == "eng"
    assert iso("Chinese") == "zho"
    assert iso("  LAO  ") == "lao"
    assert iso("Portuguese") == "por"
    assert iso("Bahasa Malaysia") == "msa"
    assert iso("en") == "eng", "older manifests write two-letter codes"
    assert iso(None) is None
    assert iso("") is None
    assert iso("Klingon") is None, "an unrecognised name must not become a code"


def test_every_language_the_offsets_measure_is_reachable():
    """A measured offset that no corpus value resolves to would never be applied."""
    measured = {k for k in load_config()["language_offset"] if not k.startswith("_")}
    for code in measured:
        assert iso(code) == code, code
        assert host_name(code), f"{code} has no name to file in column N"


def test_host_name_gives_the_name_the_sheet_asks_for():
    assert host_name("eng") == "English"
    assert host_name("zho") == "Chinese"
    assert host_name("Chinese") == "Chinese"
    assert host_name("lao") == "Lao"
    assert host_name("por") == "Portuguese"
    assert host_name("msa") == "Bahasa Malaysia"
    # the host's own examples from the column description
    for example in ("Thai", "Vietnamese", "Bahasa Indonesia", "Russian", "English"):
        assert host_name(example) == example, example


def test_host_name_never_guesses():
    assert host_name(None) == ""
    assert host_name("") == ""
    assert host_name("Klingon") == ""
    assert host_name("xyz") == "", "an ISO code with no name is not an answer to 'which language'"


def test_the_six_finale_economies_all_have_a_name():
    """Corpus values as `laws.jsonl` and the provision records actually write them."""
    for value, expected in (("eng", "English"),      # AU, MY, SG
                            ("Chinese", "Chinese"),  # CN, via the provision record
                            ("lao", "Lao"),          # LA
                            ("por", "Portuguese"),   # TL
                            ("msa", "Bahasa Malaysia")):   # 9 Malaysian laws
        assert host_name(value) == expected


def test_names_and_aliases_agree():
    """Every name filed must resolve back to the code it came from."""
    for code, name in NAMES.items():
        assert iso(name) == code or iso(name) is None, (code, name)
        if iso(name) is not None:
            assert host_name(name) == name
