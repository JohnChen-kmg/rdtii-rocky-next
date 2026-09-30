"""Lane A - per-portal HTML parsers (kickoff decision #5).

Statute pages are structured documents: the portal's own DOM classes give
section boundaries AND deep-link anchors for free, which generic boilerplate
strippers destroy. Each parser emits the frozen text and exact section spans
in one pass, so Lane A needs no separate segmentation step.

Implemented portals:
- legislation.gov.au (Federal Register of Legislation "/text" pages):
  p.ActHead1 Schedule | p.ActHead2 Chapter | p.ActHead3 Part |
  p.ActHead4 Division | p.ActHead5 section (span.CharSectno + <a id> anchor) |
  p.subsection/paragraph/... body blocks.
"""

from __future__ import annotations

import logging
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable
from urllib.parse import urlparse

from rdtii_p2.segment import Span

log = logging.getLogger("rdtii_p2.lane_a")

# BLOCKLIST, not allowlist: the corpus contains dozens of substantive body
# classes (Definition, Penalty, Tabletext, item, ...); silently dropping an
# unknown class loses statutory text that can then never be grounded. Only
# classes that are provably navigation/duplication are excluded.
_AU_NON_BODY = re.compile(r"^(?:TOC\w*|Toc\w*|notemargin\w*|Header\w*|CompHeading)$")
_AU_STRUCTURE = {"ActHead1": 1, "ActHead2": 2, "ActHead3": 3, "ActHead4": 4}


@dataclass
class HtmlDoc:
    text: str = ""
    spans: list[Span] = field(default_factory=list)
    # section citation -> DOM anchor id (deep-link fragment)
    anchors: dict[str, str] = field(default_factory=dict)


def _block_text(node) -> str:
    text = node.text(separator=" ", strip=False)
    text = unicodedata.normalize("NFC", text).replace("\xa0", " ")
    return re.sub(r"\s+", " ", text).strip()


def parse_au(html_path: Path) -> HtmlDoc:
    """legislation.gov.au parser: one pass -> frozen text + section spans."""
    from selectolax.parser import HTMLParser

    tree = HTMLParser(html_path.read_text(encoding="utf-8"))
    doc = HtmlDoc()
    lines: list[str] = []
    offset = 0
    hierarchy: dict[int, str] = {}

    @dataclass
    class _Open:
        number: str
        heading: str
        anchor: str | None
        start: int
        levels: tuple[str, ...]

    open_section: _Open | None = None

    seen_citations: set[str] = set()

    def close_section(end: int) -> None:
        nonlocal open_section
        if open_section is None:
            return
        citation = f"s.{open_section.number}"
        if citation in seen_citations:
            # head-Act s.3 vs Schedule s.3, or repeated item numbers across
            # amendment Schedules: provision_id must stay unique (contract 3.3)
            container = open_section.levels[-1] if open_section.levels else "dup"
            citation = f"{citation} [{container[:40]}]"
            suffix = 2
            while citation in seen_citations:
                citation = f"s.{open_section.number} [{container[:36]} #{suffix}]"
                suffix += 1
        seen_citations.add(citation)
        section_span = Span(
            article_section=citation, unit="section",
            char_start=open_section.start, char_end=end,
            heading=open_section.heading,
            hierarchy=open_section.levels + (citation,),
        )
        doc.spans.append(section_span)
        if open_section.anchor:
            doc.anchors[citation] = open_section.anchor
        open_section = None

    for node in tree.css("p"):
        cls = node.attributes.get("class") or ""
        if cls in _AU_STRUCTURE:
            level = _AU_STRUCTURE[cls]
            label = _block_text(node)
            # Division and Subdivision share class ActHead4 - a Subdivision
            # must not overwrite its parent Division in the hierarchy path
            if cls == "ActHead4" and label.lower().startswith("subdivision"):
                level = 5
            if open_section is not None:
                close_section(offset)
            hierarchy[level] = label
            for deeper in list(hierarchy):
                if deeper > level:
                    del hierarchy[deeper]
        elif cls == "ActHead5":
            if open_section is not None:
                close_section(offset)
            sectno_node = node.css_first("span.CharSectno")
            number = _block_text(sectno_node) if sectno_node else ""
            full = _block_text(node)
            heading = full[len(number):].strip() if number and full.startswith(number) else full
            anchor_node = node.css_first("a[id]")
            anchor = anchor_node.attributes.get("id") if anchor_node else None
            open_section = _Open(
                number=number or "?", heading=heading, anchor=anchor,
                start=offset,
                levels=tuple(hierarchy[k] for k in sorted(hierarchy)),
            )
        elif cls and _AU_NON_BODY.match(cls):
            continue  # navigation, TOC duplicates, margin notes
        else:
            line = _block_text(node)
            if not line:
                continue
            block = line + "\n"
            lines.append(block)
            offset += len(block)
            continue
        # structure/section headings also land in the text as their own lines
        line = _block_text(node)
        if line:
            block = line + "\n"
            lines.append(block)
            offset += len(block)

    if open_section is not None:
        close_section(offset)

    doc.text = "".join(lines)

    if not doc.spans:
        # Regulator instruments registered on the FRL (APRA prudential
        # standards, OAIC APP codes) are Word exports, not OPC act markup:
        # headings live in h1-h4 (with navPoint ids), some body text in <li>,
        # and no p.ActHead* exists. Re-parse with the instrument shape so the
        # frozen text is COMPLETE (the p-only pass drops heading/li text) and
        # numbered h-headings become sections. Act pages never reach here.
        instrument = _parse_au_instrument(tree)
        log.info("lane A act shape found 0 sections - instrument shape: "
                 "%d sections, %d chars", len(instrument.spans),
                 len(instrument.text))
        doc = instrument

    _add_subsection_spans(doc)

    n_sections = sum(1 for s in doc.spans if s.unit == "section")
    log.info("lane A parsed %d sections, %d spans, %d anchors",
             n_sections, len(doc.spans), len(doc.anchors))
    return doc


# instrument-shape section heading: "9 Privacy management plan" - a number
# then a SHORT title (not a full sentence, which is how Word exports also
# number body paragraphs at heading levels)
_INSTRUMENT_HEADING = re.compile(r"^(\d{1,3}[A-Z]?)\s+(\D.{0,99})$")
_INSTRUMENT_PART = re.compile(r"^(?:Part|Schedule|Chapter)\s+\d+", re.I)


def _parse_au_instrument(tree) -> HtmlDoc:
    """FRL Word-export instruments: p/h1-h4/li blocks in document order.
    Numbered short h2-h4 headings open sections (navPoint anchors); h1 and
    Part/Schedule headings become hierarchy labels; everything else is body.
    Instruments whose paragraph numbers are literal text (APRA "15." style)
    yield zero sections here - the caller falls back to the generic
    segmenter over the (now complete) frozen text."""
    doc = HtmlDoc()
    lines: list[str] = []
    offset = 0
    hierarchy: list[str] = []
    open_section: tuple[str, str, str | None, int] | None = None  # number, heading, anchor, start

    def close_section(end: int) -> None:
        nonlocal open_section
        if open_section is None:
            return
        number, heading, anchor, start = open_section
        citation = f"s.{number}"
        if any(s.article_section == citation for s in doc.spans):
            suffix = 2
            while any(s.article_section == f"{citation}~{suffix}" for s in doc.spans):
                suffix += 1
            citation = f"{citation}~{suffix}"
        doc.spans.append(Span(
            article_section=citation, unit="section",
            char_start=start, char_end=end, heading=heading,
            hierarchy=tuple(hierarchy) + (citation,),
        ))
        if anchor:
            doc.anchors[citation] = anchor
        open_section = None

    for node in tree.css("p, h1, h2, h3, h4, li"):
        line = _block_text(node)
        if not line:
            continue
        tag = node.tag
        heading_match = (_INSTRUMENT_HEADING.match(line)
                         if tag in ("h2", "h3", "h4") else None)
        if heading_match and not heading_match.group(2).rstrip().endswith((".", ";", ":")):
            close_section(offset)
            open_section = (heading_match.group(1), heading_match.group(2).strip(),
                            node.attributes.get("id"), offset)
        elif tag == "h1" or (tag in ("h2", "h3") and _INSTRUMENT_PART.match(line)):
            close_section(offset)
            hierarchy = [line]
        block = line + "\n"
        lines.append(block)
        offset += len(block)

    close_section(offset)
    doc.text = "".join(lines)
    return doc


def _add_subsection_spans(doc: HtmlDoc) -> None:
    """Subsection spans: markers "(1) " at line starts inside each section."""
    section_spans = [s for s in doc.spans if s.unit == "section"]
    for section in section_spans:
        body = doc.text[section.char_start:section.char_end]
        matches = [
            (m.group(1), m.start())
            for m in re.finditer(r"^\((\d+[A-Z]{0,2})\)\s", body, re.M)
        ]
        for index, (number, rel_offset) in enumerate(matches):
            end_rel = matches[index + 1][1] if index + 1 < len(matches) else len(body)
            citation = f"{section.article_section}({number})"
            doc.spans.append(Span(
                article_section=citation, unit="subsection",
                char_start=section.char_start + rel_offset,
                char_end=section.char_start + end_rel,
                heading=section.heading,
                hierarchy=section.hierarchy + (f"({number})",),
            ))
            if section.article_section in doc.anchors:
                doc.anchors[citation] = doc.anchors[section.article_section]


# ------------------------------------------------------- Chinese portals ----

# host -> the container the body actually lives in, measured on the real pages
_CN_CONTAINERS = {
    "cac.gov.cn": "div#BodyLabel",
    "gov.cn": "div#UCAP-CONTENT",
    "miit.gov.cn": "div#con_con",
}


def _decode(raw: bytes) -> str:
    """Chinese government pages declare GB2312/GBK about as often as UTF-8, and some
    declare one and store the other. The declaration is tried first, then the two that
    actually occur, and the first that round-trips without replacement characters wins."""
    head = raw[:2048].decode("ascii", errors="ignore").lower()
    declared = None
    for probe in ("charset=utf-8", "charset=gb2312", "charset=gbk", "charset=gb18030"):
        if probe in head:
            declared = probe.split("=", 1)[1]
            break
    for encoding in [e for e in (declared, "utf-8", "gb18030") if e]:
        try:
            return raw.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            continue
    return raw.decode("utf-8", errors="replace")


def parse_cn_portal(html_path: Path, container: str) -> HtmlDoc:
    """One Chinese ministry page: the body container's blocks, in document order.

    No spans are returned on purpose. These pages carry no section markup - an article is a
    plain <p> beginning 第X条 - so the frozen text goes to the `zho` segmenter, which already
    knows Chinese numerals and the chapter/section vocabulary. Inventing DOM spans here would
    duplicate that and disagree with it.
    """
    from selectolax.parser import HTMLParser

    tree = HTMLParser(_decode(html_path.read_bytes()))
    node = tree.css_first(container)
    if node is None:
        # never silently fall back to the whole page: that pulls in the navigation and
        # the related-links rail, and every offset after it would index into furniture
        raise NotImplementedError(
            f"{html_path.name}: container {container} not found - the portal template "
            "changed, or this page is not an instrument page")
    lines: list[str] = []
    for block in node.css("p, td, li, h1, h2, h3"):
        text = _block_text(block)
        if text:
            lines.append(text)
    if not lines:                      # some pages put the body in bare text nodes
        text = _block_text(node)
        if text:
            lines = [text]
    doc = HtmlDoc(text=("\n".join(lines) + "\n") if lines else "")
    log.info("lane A (CN %s) -> %d block(s), %d chars", container, len(lines), len(doc.text))
    return doc


PORTAL_PARSERS = {
    "legislation.gov.au": parse_au,
    # China. Order is irrelevant - `parse` takes the most specific matching host - but
    # cac.gov.cn and miit.gov.cn ARE subdomains of gov.cn, so this only works because of that.
    "cac.gov.cn": lambda path: parse_cn_portal(path, _CN_CONTAINERS["cac.gov.cn"]),
    "miit.gov.cn": lambda path: parse_cn_portal(path, _CN_CONTAINERS["miit.gov.cn"]),
    "gov.cn": lambda path: parse_cn_portal(path, _CN_CONTAINERS["gov.cn"]),
}


def _host_of(source_url: str | None) -> str:
    """The host alone, lowercased, without credentials or port. "" when there is no URL.

    A null source_url is a real state, not a bug: China holds five ministry files whose
    address collection never recorded, and `urlparse(None)` raises a TypeError that surfaces
    as "a bytes-like object is required, not 'str'" - which says nothing about the document.
    """
    if not source_url:
        return ""
    netloc = urlparse(source_url).netloc.lower()
    return netloc.rpartition("@")[2].partition(":")[0]


def parse(html_path: Path, source_url: str) -> HtmlDoc:
    """Dispatch to the parser for this document's portal.

    Matching is on the **host**, and the most specific registered host wins.

    Both halves of that matter, and China is what proved it. The original test was
    `if host in source_url` - a substring of the whole URL, over an insertion-ordered
    dict, first match wins. China's three portals are `cac.gov.cn` (112 documents),
    `miit.gov.cn` (16) and `www.gov.cn` (11), and `"gov.cn" in "https://www.cac.gov.cn/..."`
    is true, so registering `gov.cn` first would have sent **139 of 140 pages to the wrong
    parser** - 128 of them silently producing the wrong text, because a parser that finds
    no container returns little rather than raising. The correctness of the run would have
    depended on the order three lines were typed in, with nothing saying so.

    Longest-match also cannot be fixed by matching the host suffix alone: `www.cac.gov.cn`
    really is a subdomain of `gov.cn`, so a suffix test matches both and the ambiguity comes
    straight back. Length is what breaks the tie, and it does so whatever the order.
    """
    host = _host_of(source_url)
    if not host:
        raise NotImplementedError(
            "this document has no recorded source_url, so no per-portal parser can be "
            "chosen for it - see source_url_basis on its manifest row")
    best: tuple[str, Callable[[Path], HtmlDoc]] | None = None
    for registered, parser in PORTAL_PARSERS.items():
        if host == registered or host.endswith("." + registered):
            if best is None or len(registered) > len(best[0]):
                best = (registered, parser)
    if best is not None:
        return best[1](html_path)
    raise NotImplementedError(
        f"no per-portal parser for {source_url} - add one to PORTAL_PARSERS "
        "(generic boilerplate extraction is deliberately not used, decision #5)"
    )
