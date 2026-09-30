"""Epub → concatenated full-text HTML (AU multi-volume compilations, 2026-07-17 fix).

legislation.gov.au publishes multi-volume compilations as ONE epub whose spine holds one
HTML document per volume (OEBPS/document_1/document_1.html, document_2/…). The site's
epub viewer (iframe#epubFrame) renders a single spine document at a time, so a frame
capture silently yields volume 1 only. Fetching the epub directly and concatenating ALL
spine documents — verified against the OPF spine — is the only capture that is complete
by construction.

concat_epub_html() raises EpubExtractionError on ANY shortfall (bad zip, missing OPF,
spine item absent from the archive, zero documents): a partial extraction must be a loud
failure, never a stored artifact.
"""
from __future__ import annotations

import io
import posixpath
import re
import zipfile
from xml.etree import ElementTree


class EpubExtractionError(ValueError):
    """The epub could not be FULLY extracted (partial output is never returned)."""


def concat_epub_html(data: bytes) -> bytes:
    """Return every spine HTML document of the epub, concatenated in spine order.

    Each document is preceded by a provenance comment naming its archive path and
    position, so the volume boundaries stay visible (and machine-checkable) in the
    stored artifact.
    """
    try:
        z = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile as e:
        raise EpubExtractionError(f"not a zip/epub: {e}") from e
    with z:
        names = set(z.namelist())
        opf_name = _find_opf(z, names)
        try:
            opf = ElementTree.fromstring(z.read(opf_name))
        except ElementTree.ParseError as e:
            raise EpubExtractionError(f"unparseable OPF {opf_name}: {e}") from e

        hrefs = _spine_html_hrefs(opf, posixpath.dirname(opf_name))
        if not hrefs:
            raise EpubExtractionError("OPF spine lists no HTML documents")

        parts: list[bytes] = []
        for i, href in enumerate(hrefs, 1):
            if href not in names:
                raise EpubExtractionError(
                    f"spine document {href} missing from archive ({i}/{len(hrefs)})")
            marker = f"<!-- p1-epub-spine-doc {i}/{len(hrefs)}: {href} -->\n".encode()
            parts.append(marker + z.read(href))
        return b"\n".join(parts)


def _find_opf(z: zipfile.ZipFile, names: set[str]) -> str:
    """META-INF/container.xml names the OPF; fall back to the only *.opf in the zip."""
    if "META-INF/container.xml" in names:
        try:
            root = ElementTree.fromstring(z.read("META-INF/container.xml"))
            for el in root.iter():
                if el.tag.endswith("rootfile") and el.get("full-path") in names:
                    return el.get("full-path")
        except ElementTree.ParseError:
            pass
    opfs = [n for n in names if n.endswith(".opf")]
    if len(opfs) == 1:
        return opfs[0]
    raise EpubExtractionError("cannot locate the OPF package document")


def _spine_html_hrefs(opf: ElementTree.Element, opf_dir: str) -> list[str]:
    """Spine order → archive paths of the HTML/XHTML content documents."""
    items: dict[str, tuple[str, str]] = {}     # id -> (href, media-type)
    for el in opf.iter():
        if el.tag.endswith("item") and el.get("id") and el.get("href"):
            items[el.get("id")] = (el.get("href"), el.get("media-type") or "")
    hrefs: list[str] = []
    for el in opf.iter():
        if el.tag.endswith("itemref") and el.get("idref") in items:
            href, media = items[el.get("idref")]
            if "html" in media.lower() or re.search(r"\.x?html?$", href, re.I):
                hrefs.append(posixpath.normpath(posixpath.join(opf_dir, href)))
    return hrefs
