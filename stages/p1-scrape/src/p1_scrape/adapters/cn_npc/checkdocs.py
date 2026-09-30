"""Check that documents collected by hand can actually be read by a machine.

`CONVENTIONS.md` rule 12. A page saved in a browser looks right to a human whatever route it took, but
Windows' "Microsoft Print to PDF" printer converts CJK glyphs to vector outlines: the file carries no fonts
and no text, only drawn curves, and extraction gets nothing from it. This reports every file in a folder and
exits non-zero if one is unreadable, so the first file of a batch settles the method before the other
seventeen are saved the same wrong way.

Standard library only, on purpose: it runs anywhere the developer is saving files, with no install step.

    python countries/cn-china/tools/checkdocs.py outputs/CN/CN_sources_2026-09-21/manual/miit/raw
    python countries/cn-china/tools/checkdocs.py <folder> --quiet   # only the unreadable ones
"""

from __future__ import annotations

import argparse
import re
import sys
import zlib
from pathlib import Path
from typing import Iterable, List, NamedTuple, Optional

# Text-showing operators: `(text) Tj`, `[...] TJ`, `(text) '`, `(text) "`.
_SHOW_TEXT = re.compile(rb"(?:\bTj|\bTJ|\bT\*)")
_BT = re.compile(rb"\bBT\b")
_FONT = re.compile(rb"/(?:Font|BaseFont|FontFile\d?)\b")
_STREAM = re.compile(rb"stream\r?\n(.*?)endstream", re.DOTALL)

READABLE = "readable"
NO_TEXT = "no text layer"
UNKNOWN = "unknown format"


class Report(NamedTuple):
    """What one file turned out to be."""

    path: Path
    verdict: str
    detail: str

    @property
    def ok(self) -> bool:
        return self.verdict == READABLE


def _inflate_streams(data: bytes, limit: int = 400) -> bytes:
    """Decompress the first `limit` FlateDecode streams and return them joined.

    A PDF's page content is normally compressed, so the text operators are invisible in the raw bytes. Streams
    that are images or that fail to decompress are skipped — they say nothing either way.
    """
    out: List[bytes] = []
    for n, m in enumerate(_STREAM.finditer(data)):
        if n >= limit:
            break
        try:
            out.append(zlib.decompress(m.group(1)))
        except zlib.error:
            out.append(m.group(1))  # uncompressed, or a codec we do not read
    return b"".join(out)


def check_pdf(data: bytes) -> Report:
    """Judge a PDF by whether anything in it shows text."""
    pages = len(re.findall(rb"/Type\s*/Page\b", data)) or len(re.findall(rb"/Count\s+(\d+)", data))
    body = data + _inflate_streams(data)
    fonts = len(_FONT.findall(body))
    shows = len(_SHOW_TEXT.findall(body))
    blocks = len(_BT.findall(body))
    if fonts and (shows or blocks):
        return Report(Path(), READABLE, f"{pages} pages, {fonts} font refs, {shows} text operators")
    curves = len(re.findall(rb"\bre\b|\bc\b|\bf\*?\b", body))
    why = "printed as outlines or scanned as images"
    if b"Microsoft: Print To PDF" in data:
        why = "made with 'Microsoft Print to PDF', which outlines CJK glyphs"
    return Report(Path(), NO_TEXT, f"{pages} pages, no fonts, {curves} path operators — {why}")


def check_ole(data: bytes) -> Report:
    """A Word 97-2003 `.doc`: a compound file whose text is stored UTF-16, so it is always readable."""
    text = data.decode("utf-16-le", errors="ignore")
    cjk = len(re.findall(r"[一-鿿]", text))
    return Report(Path(), READABLE, f"Word binary, {cjk:,} CJK characters")


def check_zip_office(data: bytes) -> Report:
    """A `.docx`/`.xlsx`: a zip of XML."""
    return Report(Path(), READABLE, f"Office Open XML, {len(data):,} bytes")


def check_text(data: bytes) -> Report:
    """HTML, MHTML or plain text: readable by definition, but report how much of it there is."""
    text = data.decode("utf-8", errors="ignore")
    stripped = re.sub(r"<[^>]+>", "", text)
    cjk = len(re.findall(r"[一-鿿]", stripped))
    words = len(stripped.split())
    return Report(Path(), READABLE, f"markup, {cjk:,} CJK characters, {words:,} words")


def check_file(path: Path) -> Report:
    """Read one file and report what a parser would get out of it."""
    try:
        data = path.read_bytes()
    except OSError as exc:  # unreadable on disk is still a finding
        return Report(path, UNKNOWN, f"could not be read: {exc}")
    if not data:
        return Report(path, NO_TEXT, "empty file")
    if data[:5] == b"%PDF-":
        rep = check_pdf(data)
    elif data[:8] == b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1":
        rep = check_ole(data)
    elif data[:2] == b"PK" and path.suffix.lower() in {".docx", ".xlsx", ".pptx"}:
        rep = check_zip_office(data)
    elif path.suffix.lower() in {".html", ".htm", ".mhtml", ".mht", ".txt", ".md", ".xml"}:
        rep = check_text(data)
    else:
        return Report(path, UNKNOWN, f"not a format this checks ({path.suffix or 'no suffix'})")
    return rep._replace(path=path)


def check_folder(folder: Path) -> List[Report]:
    """Every file directly in `folder`, in name order."""
    return [check_file(p) for p in sorted(folder.iterdir()) if p.is_file()]


def _say(line: str) -> None:
    """Print a line that survives a console that cannot encode it."""
    try:
        print(line)
    except UnicodeEncodeError:
        print(line.encode("ascii", "replace").decode("ascii"))


def report(reports: Iterable[Report], quiet: bool = False) -> int:
    """Print the findings; return the number that cannot be read."""
    reports = list(reports)
    bad = [r for r in reports if r.verdict == NO_TEXT]
    for r in reports:
        if quiet and r.ok:
            continue
        mark = "ok  " if r.ok else ("FAIL" if r.verdict == NO_TEXT else "?   ")
        _say(f"  {mark} {r.path.name}\n         {r.detail}")
    _say("")
    _say(f"{len(reports)} files: {sum(1 for r in reports if r.ok)} readable, {len(bad)} with no text layer, "
         f"{sum(1 for r in reports if r.verdict == UNKNOWN)} not checked")
    if bad:
        _say("")
        _say("These carry no text and extraction would get nothing from them. Save them again with the")
        _say("browser's own 'Save as PDF', or with Ctrl+S as 'Webpage, Single File (.mhtml)' —")
        _say("not through the 'Microsoft Print to PDF' printer (CONVENTIONS.md rule 12).")
    return len(bad)


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Check that hand-collected documents carry a text layer.")
    ap.add_argument("folder", type=Path, help="the folder to check, usually a source's raw/")
    ap.add_argument("--quiet", action="store_true", help="print only the files that cannot be read")
    args = ap.parse_args(argv)
    if not args.folder.exists():
        _say(f"no such folder: {args.folder}")
        return 2
    _say(f"Checking {args.folder}")
    return 1 if report(check_folder(args.folder), quiet=args.quiet) else 0


if __name__ == "__main__":
    sys.exit(main())
