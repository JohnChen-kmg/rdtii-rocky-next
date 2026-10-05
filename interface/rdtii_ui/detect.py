"""Language and economy detection for hand-collected files. Standard library only.

Used two ways, never as the record. As a suggestion, when a folder does not name its economy: the text is read
and the page proposes one for the reviewer to confirm. As a check, when the folder does name it: a file whose
text reads as Lao inside inbox/CN earns a warning. The extraction stage keeps its own rule, a document's
language is declared and never sniffed, and what the interface passes to it is still the economy's language
from the economy table. Detection here only helps a person put the file in the right place.

What can be read: web pages and Word files whole; native PDFs roughly, from the literal strings of their text
streams, which fails for scanned pages and for fonts that map characters to glyph ids (most Chinese and Lao
PDFs). Every file says whether it could be read, so the count of checked files is honest.
"""
from __future__ import annotations

import html
import re
import zipfile
import zlib
from collections import Counter
from pathlib import Path

# One economy per language in this instrument. English is shared and needs the text's own marks.
LANGUAGE_ECONOMY = {"zho": "CN", "lao": "LA", "por": "TL", "msa": "MY"}
# Languages a folder may legitimately hold: Malaysia publishes in English and Malay.
ACCEPTED = {"SG": {"eng"}, "AU": {"eng"}, "IN": {"eng"}, "MY": {"eng", "msa"}, "CN": {"zho"}, "LA": {"lao"}, "TL": {"por"}}
LABEL = {"eng": "English", "zho": "Chinese", "lao": "Lao", "por": "Portuguese", "msa": "Malay"}

STOP = {
    "eng": {"the", "of", "and", "to", "in", "shall", "section", "act", "or", "any", "by", "be", "is", "for", "this",
            "under", "that", "with", "not", "may", "person", "means", "which", "such", "who", "have", "from", "on"},
    "por": {"de", "da", "do", "e", "a", "o", "que", "em", "para", "artigo", "lei", "dos", "das", "não", "com", "os",
            "as", "ou", "por", "no", "na", "pelo", "pela", "ao", "é", "são", "presente", "deve", "sem", "nos"},
    "msa": {"dan", "yang", "atau", "bagi", "hendaklah", "seksyen", "akta", "oleh", "mana", "mana-mana", "tidak", "di",
            "kepada", "dengan", "ini", "adalah", "boleh", "dalam", "itu", "daripada", "seorang", "apa-apa", "jika",
            "telah", "bahawa", "pada", "ke", "atas", "bolehlah"},
}
# Country marks for English text: the strong ones name the state or its statute book, the last is the bare name.
MARKS = {
    "SG": [r"republic of singapore", r"singapore statutes", r"parliament of singapore", r"\bsingapore\b"],
    "AU": [r"commonwealth of australia", r"federal register of legislation", r"parliament of australia", r"\baustralia\b"],
    "MY": [r"laws of malaysia", r"yang di-pertuan agong", r"dewan rakyat", r"\bmalaysia\b"],
    "IN": [r"republic of india", r"gazette of india", r"parliament of india", r"\bindia\b"],
}

CJK_RX = re.compile(r"[\u4e00-\u9fff\u3400-\u4dbf]")
LAO_RX = re.compile(r"[\u0e80-\u0eff]")
LATIN_WORD_RX = re.compile(r"[a-záàâãéêíóôõúçñ][a-záàâãéêíóôõúçñ\-]*", re.I)
TAG_RX = re.compile(r"<[^>]+>")
PDF_STREAM_RX = re.compile(rb"stream\r?\n(.*?)\r?\nendstream", re.S)
PDF_STRING_RX = re.compile(rb"\((?:\\.|[^\\)])*\)")
_ESC = {b"n": b"\n", b"r": b"", b"t": b" ", b"b": b"", b"f": b"", b"(": b"(", b")": b")", b"\\": b"\\"}


# ---- text ------------------------------------------------------------------------------------------------

def html_text(data: bytes) -> str:
    text = None
    for enc in ("utf-8", "cp1252"):
        try:
            text = data.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    if text is None:
        text = data.decode("utf-8", "replace")
    text = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", text)
    return html.unescape(TAG_RX.sub(" ", text))


def docx_text(path: Path) -> str:
    with zipfile.ZipFile(path) as z:
        xml = z.read("word/document.xml").decode("utf-8", "replace")
    return html.unescape(TAG_RX.sub(" ", xml))


def pdf_text(data: bytes, limit: int = 200_000) -> str:
    """The literal strings of the text streams: good for simple fonts, noise or nothing for glyph-id fonts."""
    out: list[str] = []
    size = 0
    for m in PDF_STREAM_RX.finditer(data):
        raw = m.group(1)
        try:
            content = zlib.decompress(raw)
        except zlib.error:
            content = raw
        if b"BT" not in content:
            continue
        for s in PDF_STRING_RX.findall(content):
            s = s[1:-1]
            # one pass over the escapes: a named one, an octal code, or any other backslash-character pair
            s = re.sub(rb"\\([0-7]{1,3}|.)",
                       lambda mm: bytes([int(mm.group(1), 8) & 0xFF]) if mm.group(1)[:1] in b"01234567" and len(mm.group(1)) <= 3 and all(c in b"01234567" for c in mm.group(1))
                       else _ESC.get(mm.group(1), mm.group(1)), s, flags=re.S)
            piece = s.decode("latin-1")
            out.append(piece)
            size += len(piece)
        if size > limit:
            break
    return " ".join(out)


def read_text(path: Path, limit: int = 600_000) -> tuple[str, str]:
    """(text, note): the note says why there is no text."""
    suffix = path.suffix.lower()
    try:
        if suffix in (".html", ".htm"):
            return html_text(path.read_bytes()[:limit]), ""
        if suffix == ".docx":
            return docx_text(path), ""
        if suffix == ".pdf":
            text = pdf_text(path.read_bytes())
            if _readable_units(text) < 40:
                return "", "no readable text layer: scanned, or a font the reader cannot decode"
            return text, ""
        return "", "format not read"
    except (OSError, zipfile.BadZipFile, KeyError) as e:
        return "", f"could not read the file ({e.__class__.__name__})"


def _readable_units(text: str) -> int:
    # Latin words of three letters or more: a PDF whose font maps characters to glyph ids gives single
    # letters and scraps here, which are not text (found 5 October 2026: Singapore's PDPA read that way)
    return (sum(1 for w in LATIN_WORD_RX.findall(text) if len(w) >= 3)
            + len(CJK_RX.findall(text)) + len(LAO_RX.findall(text)))


# ---- language and economy --------------------------------------------------------------------------------

def detect_language(text: str) -> tuple[str | None, str]:
    """(language, basis). None when the text is too short or the stop words do not separate the candidates."""
    cjk, lao = len(CJK_RX.findall(text)), len(LAO_RX.findall(text))
    # single letters are left out: "e", "a" and "o" are Portuguese words, and they are also what the noise of
    # an undecodable PDF font is made of, which read an English act as Portuguese
    words = [w.lower() for w in LATIN_WORD_RX.findall(text) if len(w) >= 2]
    latin = len(words)
    if cjk >= 40 and cjk > latin / 4:
        return "zho", "script"
    if lao >= 40 and lao > latin / 4:
        return "lao", "script"
    if latin < 40:
        return None, "too little readable text"
    hits = {lang: sum(1 for w in words if w in stop) for lang, stop in STOP.items()}
    ranked = sorted(hits.items(), key=lambda kv: -kv[1])
    best, second = ranked[0], ranked[1]
    if best[1] >= 8 and best[1] >= 2 * max(second[1], 1):
        return best[0], "stop words"
    return None, "the stop words do not separate English, Portuguese and Malay"


def detect_economy(text: str, language: str | None) -> tuple[str | None, str]:
    if language in LANGUAGE_ECONOMY:
        return LANGUAGE_ECONOMY[language], "the language"
    if language != "eng":
        return None, ""
    low = text.lower()
    score = {}
    for code, patterns in MARKS.items():
        strong = sum(len(re.findall(p, low)) for p in patterns[:-1])
        weak = len(re.findall(patterns[-1], low))
        score[code] = 3 * strong + weak
    ranked = sorted(score.items(), key=lambda kv: -kv[1])
    if ranked[0][1] >= 3 and ranked[0][1] >= 2 * max(ranked[1][1], 1):
        return ranked[0][0], "country marks in the text"
    return None, "no country mark stands out"


def detect_file(path: Path) -> dict:
    text, note = read_text(path)
    if not text:
        return {"file": path.name, "language": None, "economy": None, "basis": note}
    language, basis = detect_language(text)
    if not language:
        return {"file": path.name, "language": None, "economy": None, "basis": basis}
    economy, ebasis = detect_economy(text, language)
    return {"file": path.name, "language": language, "economy": economy,
            "basis": basis + (f"; economy from {ebasis}" if ebasis else "")}


def detect_folder(files: list[Path], declared: str | None = None, limit: int = 60,
                  economy_of: dict[str, str] | None = None) -> dict:
    """Detection over the first `limit` files. `declared` is the economy the folder names, if any; `economy_of`
    gives a declared economy per file name when the folder holds one subfolder per economy."""
    per = [detect_file(p) for p in files[:limit]]
    readable = [r for r in per if r["language"]]
    by_language = Counter(r["language"] for r in readable)
    by_economy = Counter(r["economy"] for r in readable if r["economy"])
    suggested = None
    if by_economy:
        top, n = by_economy.most_common(1)[0]
        if n >= 0.8 * len(readable):
            suggested = top
    mismatch = []
    for r in readable:
        decl = (economy_of or {}).get(r["file"], declared)
        if decl and decl in ACCEPTED and r["language"] not in ACCEPTED[decl]:
            mismatch.append(r)
    unread = len(per) - len(readable)
    langs = ", ".join(f"{LABEL.get(k, k)} in {v}" for k, v in by_language.most_common())
    if not per:
        line = "no files"
    elif not readable:
        line = f"no readable text in {len(per)} file(s) before OCR; nothing to check"
    else:
        line = f"{langs} of {len(readable)} readable file(s)"
        if unread:
            line += f", {unread} not readable before OCR"
        if len(files) > len(per):
            line += f", first {len(per)} of {len(files)} checked"
        if suggested and not declared and not economy_of:
            line += f"; the text points to {suggested}"
    return {"checked": len(per), "total": len(files), "readable": len(readable), "unreadable": unread,
            "by_language": dict(by_language), "by_economy": dict(by_economy), "suggested_economy": suggested,
            "mismatch": len(mismatch), "mismatch_files": [f"{r['file']} ({LABEL.get(r['language'], r['language'])})" for r in mismatch[:8]],
            "files": per, "line": line}
