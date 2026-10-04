"""Whether the extraction stage can read a hand-collected file, judged from what the file is, not what it
is called.

The stage chooses its reader from the manifest's source type and reads only what it has a reader for: a PDF
(text layer, or OCR when it has none), a Word .docx, and a web page from a portal it has a parser for. A
file that is none of those fails inside the run with a message about packages and parsers. Judging the file
here, before the run, turns that into a plain line and a thing to do.

Standard library only; nothing is fetched and nothing is converted here.
"""
from __future__ import annotations

import zipfile
from pathlib import Path

OLE2 = bytes.fromhex("D0CF11E0A1B11AE1")      # the container of .doc, .xls, .ppt and Kingsoft .wps
_BOMS = (b"\xef\xbb\xbf", b"\xff\xfe", b"\xfe\xff")


def sniff(path: Path) -> str:
    """What the file is, from its first bytes: pdf, docx, zip, doc_ole, rtf, html or other."""
    try:
        with open(path, "rb") as f:
            head = f.read(4096)
    except OSError:
        return "other"
    if b"%PDF-" in head[:1024]:
        return "pdf"
    if head.startswith(b"PK\x03\x04"):
        try:
            with zipfile.ZipFile(path) as zf:
                return "docx" if "word/document.xml" in zf.namelist() else "zip"
        except (zipfile.BadZipFile, OSError):
            return "zip"
    if head.startswith(OLE2):
        return "doc_ole"
    body = head
    for bom in _BOMS:
        if body.startswith(bom):
            body = body[len(bom):]
    low = body.replace(b"\x00", b"").lstrip().lower()
    if low.startswith(b"{\\rtf"):
        return "rtf"
    # markup of any kind: a whole page, an XHTML page that opens with <?xml, or the fragment a tool saved
    if b"<html" in low[:2000] or (low[:1] == b"<" and (low[1:2].isalpha() or low[1:2] in (b"!", b"?"))):
        return "html"
    return "other"


def match_host(host: str, hosts) -> str | None:
    """The registered portal a host belongs to: the host itself or a parent domain, the longest one winning.
    The same rule the stage applies when it picks a parser."""
    host = (host or "").lower().strip(".")
    host = host[4:] if host.startswith("www.") else host
    hits = [h for h in hosts if host == h or host.endswith("." + h)]
    return max(hits, key=len) if hits else None


def judge(path: Path, named: str, host: str, html_hosts) -> dict:
    """{"kind", "status", "method", "action"} for one file. `named` is the kind its suffix claims (pdf, html,
    docx, doc); `host` is where it came from, when known. status is "ready" or "cannot_read"; action says
    what to do about a file that cannot be read, in plain words."""
    kind = sniff(path)

    def no(action: str) -> dict:
        return {"kind": kind, "status": "cannot_read", "method": "", "action": action}

    def yes(method: str, note: str = "") -> dict:
        return {"kind": kind, "status": "ready", "method": method, "action": note}

    web_page_instead = "Not the document: the download saved a web page under this name. Fetch the file itself again."
    if named == "pdf":
        if kind == "pdf":
            return yes("PDF: its text layer, or OCR when it has none")
        return no(web_page_instead if kind == "html" else "Not a PDF, whatever its name says. Fetch it again.")
    if named in ("docx", "doc"):
        if kind == "docx":
            return yes("Word", "named .doc, but it is a .docx and reads as one" if named == "doc" else "")
        if kind == "doc_ole":
            return no("Old Word format (.doc): the reader takes .docx only. Open it and Save As .docx, then drop the .docx.")
        if kind == "html":
            return no(web_page_instead)
        return no("Not a Word document, whatever its name says. Fetch it again.")
    if named == "html":
        if kind != "html":
            return no("Not a web page, whatever its name says.")
        if not host:
            return no("No address is noted for this page, so no parser can be chosen. Type the page's address.")
        portal = match_host(host, html_hosts)
        if portal:
            return yes(f"web page, the {portal} parser")
        return no(f"No reader for pages from {host}. Print the page to PDF (Ctrl+P, Save as PDF) and drop the PDF.")
    return no("Not a kind of file the reader takes.")
