"""Lane D - Office Open XML, for the 943 documents of China's national law database.

`.docx` is a zip holding `word/document.xml`, so this needs no dependency beyond the stdlib and
the `lxml` the stage already uses. **`python-docx` is deliberately not used: it is not installed
in this venv and is not in `pyproject.toml`**, and adding a dependency a week before freeze would
have to survive the clean-machine test for no gain over thirty lines here.

What the database's export actually looks like, measured on the Cybersecurity Law:

    中华人民共和国网络安全法                    <- title
    （2016年11月7日第十二届全国人民代表大会...   <- enactment and amendment history
    目　　录                                     <- a contents list follows
    第一章　总　　则
    ...
    第一条　为了保障网络安全，维护网络空间主权...  <- the articles themselves

162 paragraphs, 10,876 characters, 81 article paragraphs. The text is clean Unicode - there is
no OCR here and no mojibake - so lane D is the cheapest lane in the stage.

**Ideographic space matters.** These documents separate an article marker from its text with
U+3000 (`第一条　为了...`), not an ASCII space. It is preserved exactly: the frozen text must stay
a byte-for-byte record of what the source said, because every `verbatim_snippet` is a
character-exact substring of it (D1). Normalising it away would move every offset after it.

Tables carry real obligations in Chinese regulations (catalogues, fee schedules), so table cells
are emitted in document order rather than skipped.
"""

from __future__ import annotations

import logging
import zipfile
from dataclasses import dataclass
from pathlib import Path

log = logging.getLogger("rdtii_p2.lane_d")

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
DOCUMENT = "word/document.xml"


@dataclass
class DocxDoc:
    text: str
    paragraphs: int
    tables: int


def _paragraph_text(node) -> str:
    """One paragraph's visible text, including any tab and line-break runs."""
    parts: list[str] = []
    for child in node.iter():
        tag = child.tag
        if tag == f"{W}t":
            parts.append(child.text or "")
        elif tag == f"{W}tab":
            parts.append("\t")
        elif tag in (f"{W}br", f"{W}cr"):
            parts.append("\n")
    return "".join(parts).strip()


def extract(path: Path) -> DocxDoc:
    """The frozen text of one OOXML document, in document order."""
    from lxml import etree

    try:
        with zipfile.ZipFile(path) as archive:
            if DOCUMENT not in archive.namelist():
                raise NotImplementedError(
                    f"{path.name}: no {DOCUMENT} in the package - not a Word document")
            body = etree.fromstring(archive.read(DOCUMENT))
    except zipfile.BadZipFile as exc:
        # a legacy OLE2 .doc renamed, or a truncated download
        raise NotImplementedError(f"{path.name}: not an OOXML package ({exc})") from exc

    lines: list[str] = []
    paragraphs = tables = 0
    seen: set[int] = set()

    for node in body.iter(f"{W}p", f"{W}tbl"):
        if id(node) in seen:
            continue
        if node.tag == f"{W}tbl":
            tables += 1
            for row in node.iter(f"{W}tr"):
                cells = []
                for cell in row.iter(f"{W}tc"):
                    inner = [_paragraph_text(p) for p in cell.iter(f"{W}p")]
                    seen.update(id(p) for p in cell.iter(f"{W}p"))
                    cells.append(" ".join(t for t in inner if t))
                line = "\t".join(cells).strip()
                if line:
                    lines.append(line)
            continue
        text = _paragraph_text(node)
        paragraphs += 1
        if text:
            lines.append(text)

    return DocxDoc(text="\n".join(lines) + "\n" if lines else "",
                   paragraphs=paragraphs, tables=tables)


def extract_pages(path: Path) -> list[str]:
    """One 'page' - OOXML has no pagination, and inventing page numbers would put a
    `location_reference` on a record that the printed document does not support."""
    return [extract(path).text]
