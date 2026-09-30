"""ISO 639-3 codes, and the language names the host sheet asks for.

Two stages need this in opposite directions, so it lives in one place and they cannot disagree:

- S2 resolves a corpus language to a **code**, to pick the selection threshold's offset
  (`config/selection.py` keys its offsets `eng`, `por`, `zho`, `lao`, `msa`);
- the emitter turns whatever the corpus says into the **name** column N wants: "Original language
  of the legal document — e.g. Thai, Vietnamese, Bahasa Indonesia, Russian, English. Drives
  criterion C1c." (OUTPUT_TEMPLATE_FINAL_ROUND.xlsx, Output Data row 5).

The corpus writes both forms: `laws.jsonl` carries `language_of_source` as an ISO code (`eng`,
`lao`, `por`, and null on every Chinese law), while a provision record carries
`language_of_source_name` as a name (`Chinese`). Both are accepted; neither is guessed. An
unrecognised value resolves to None or "", because a wrong language in column N is a wrong answer
on a criterion, while a blank is a visible gap.
"""
from __future__ import annotations

import re

# ISO 639-3 -> the name to file. The Bahasa forms follow the host's own examples.
NAMES = {
    "eng": "English", "zho": "Chinese", "lao": "Lao", "por": "Portuguese",
    "tet": "Tetum", "msa": "Bahasa Malaysia", "ind": "Bahasa Indonesia",
    "tha": "Thai", "vie": "Vietnamese", "rus": "Russian", "kaz": "Kazakh",
    "mon": "Mongolian", "hin": "Hindi", "khm": "Khmer", "mya": "Burmese",
    "nep": "Nepali", "sin": "Sinhala", "tam": "Tamil", "urd": "Urdu",
    "jpn": "Japanese", "kor": "Korean", "fas": "Persian", "ara": "Arabic",
    "ben": "Bengali", "dzo": "Dzongkha", "kir": "Kyrgyz", "tgk": "Tajik",
    "tuk": "Turkmen", "uzb": "Uzbek", "fij": "Fijian", "smo": "Samoan",
    "ton": "Tongan", "bis": "Bislama", "tpi": "Tok Pisin", "fil": "Filipino",
    "div": "Dhivehi", "mri": "Maori",
}
# What the corpus and the host materials write, lowercased -> ISO 639-3.
ALIASES = {
    "english": "eng", "chinese": "zho", "mandarin": "zho", "simplified chinese": "zho",
    "lao": "lao", "laotian": "lao", "portuguese": "por", "tetum": "tet", "tetun": "tet",
    "malay": "msa", "bahasa malaysia": "msa", "bahasa melayu": "msa",
    "indonesian": "ind", "bahasa indonesia": "ind", "thai": "tha",
    "vietnamese": "vie", "russian": "rus", "kazakh": "kaz", "mongolian": "mon",
    "hindi": "hin", "khmer": "khm", "burmese": "mya", "myanmar": "mya",
    "nepali": "nep", "sinhala": "sin", "tamil": "tam", "urdu": "urd",
    "japanese": "jpn", "korean": "kor", "persian": "fas", "dari": "fas",
    "arabic": "ara", "bengali": "ben", "filipino": "fil", "tagalog": "fil",
    # two-letter codes appear in older manifests
    "en": "eng", "zh": "zho", "lo": "lao", "pt": "por", "ms": "msa", "id": "ind",
    "th": "tha", "vi": "vie", "ru": "rus", "kk": "kaz", "mn": "mon",
}


def iso(value) -> str | None:
    """An ISO 639-3 code from a code or a name. None when the value says nothing usable."""
    s = str(value or "").strip().lower()
    if not s:
        return None
    if s in ALIASES:
        return ALIASES[s]
    if re.fullmatch(r"[a-z]{3}", s) and s in NAMES:
        return s
    if re.fullmatch(r"[a-z]{3}", s):
        return s          # an ISO code we have no name for: still a code
    return None


def host_name(value) -> str:
    """The name column N expects, or "" — never a guess.

    A three-letter code with no entry in NAMES comes back as "", not as the code: the column is
    read by a person, and "khm" is not an answer to "which language is this".
    """
    code = iso(value)
    if code and code in NAMES:
        return NAMES[code]
    # a name we already know how to file, passed through unchanged
    s = str(value or "").strip()
    if s in NAMES.values():
        return s
    return ""
