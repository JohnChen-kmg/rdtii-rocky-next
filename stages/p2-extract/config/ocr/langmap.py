"""Which Tesseract language pack reads a document, and where the packs live.

The manifest's language is ISO 639-3, written by the crawler. Tesseract's pack names are
mostly the same three letters, but not always - Chinese is `chi_sim`, not `zho` - so the
mapping is written down rather than assumed.

The packs are vendored in this repository (D7) so a reviewer needs no network inside the
thirty-minute clean-machine test, and `TESSDATA_PREFIX` is set here in code rather than asked
of the reviewer, because an instruction to export an environment variable by hand does not
survive that test.

`tessdata_fast` is the default. Measured on 60 real Lao scans, 349 pages: title recovery 0.887
against `best`'s 0.891 and article-number sequence agreement 0.855 against 0.856 - within half a
point - at half the time and half the repository size
(`evidence/2026-09-23_ocr_engine_comparison.md`).
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

log = logging.getLogger("config.ocr.langmap")

# ISO 639-3 (what the crawler writes) -> Tesseract pack string
LANGUAGE_TO_PACK = {
    "eng": "eng",
    "lao": "lao",
    "por": "por",
    "zho": "chi_sim",
    "msa": "msa+eng",     # the Malay pack Round 1 side-loaded, with English for the numerals
}
DEFAULT_PACK = "eng"

_FIXTURES = Path(__file__).resolve().parents[2] / "fixtures"
PACK_DIRS = {"fast": _FIXTURES / "tessdata_fast", "best": _FIXTURES / "tessdata_local"}
DEFAULT_QUALITY = "fast"


def pack_for(language: str | None) -> str:
    """The pack string for a document's language, e.g. 'lao' or 'msa+eng'."""
    if not language:
        return DEFAULT_PACK
    pack = LANGUAGE_TO_PACK.get(language)
    if pack is None:
        log.warning("no Tesseract pack mapped for language %r - falling back to %r. "
                    "Add it to LANGUAGE_TO_PACK rather than letting a document be read "
                    "in the wrong language.", language, DEFAULT_PACK)
        return DEFAULT_PACK
    return pack


def tessdata_dir(quality: str = DEFAULT_QUALITY) -> Path:
    directory = PACK_DIRS.get(quality)
    if directory is None:
        raise ValueError(f"unknown pack quality {quality!r}; expected one of {list(PACK_DIRS)}")
    return directory


def use_vendored_packs(quality: str = DEFAULT_QUALITY) -> Path:
    """Point Tesseract at the packs committed here. Returns the directory used."""
    directory = tessdata_dir(quality)
    os.environ["TESSDATA_PREFIX"] = str(directory)
    return directory


def installed_packs(quality: str = DEFAULT_QUALITY) -> set[str]:
    return {p.stem for p in tessdata_dir(quality).glob("*.traineddata")}


def check_packs(languages, quality: str = DEFAULT_QUALITY) -> None:
    """Fail before a run rather than per page, and say exactly what is missing.

    A missing pack is not a per-document warning: Tesseract simply refuses to initialise, so
    every scanned page of that language would fail one at a time, hours into a run.
    """
    have = installed_packs(quality)
    wanted: dict[str, str] = {}
    for language in {lang for lang in languages if lang}:
        for part in pack_for(language).split("+"):
            wanted[part] = language
    missing = {pack: lang for pack, lang in wanted.items() if pack not in have}
    if missing:
        listing = ", ".join(f"{pack} (for {lang})" for pack, lang in sorted(missing.items()))
        raise RuntimeError(
            f"Tesseract language pack(s) missing from {tessdata_dir(quality)}: {listing}. "
            f"Present: {', '.join(sorted(have)) or 'none'}. Download the pack from "
            f"https://github.com/tesseract-ocr/tessdata_{quality}/ and commit it beside the "
            f"others, then record its URL and sha256 in evidence/ (decision D7)."
        )
