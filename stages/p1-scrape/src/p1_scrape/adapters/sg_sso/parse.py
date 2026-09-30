"""Parsers for Singapore Statutes Online pages, saved on 2026-09-15 (tests/fixtures/).

Every page is server-rendered: plain GET returns the listings and the detail pages with their timelines, so no
browser is needed to read them (NOTES.md section 8). Each parser takes the page's HTML and returns records; no
parser sends a request.
"""
from __future__ import annotations

import html as html_lib
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

ROOT = "https://sso.agc.gov.sg"

_ROW_SPLIT_RE = re.compile(r"(?=<tr\b)")      # a header row without </tr> would otherwise swallow the first act
_LINK_RE = re.compile(r'<a class="non-ajax" href="(/(?:Act|Acts-Supp|SL|SL-Supp)/[^"]+)"[^>]*>(.*?)</a>', re.S)
_NUMBER_COL_RE = re.compile(r'<td class="hidden-xs col-no">\s*(.*?)\s*</td>', re.S)
_RESULTS_RE = re.compile(r"([\d,]+)\s+results?", re.I)
_PDF_RE = re.compile(r'href="([^"]*ViewType=Pdf[^"]*)"')
_LI_RE = re.compile(r'<li class="(?P<cls>[^"]*)" data-id="(?P<id>[^"]+)">(?P<body>.*?)</li>', re.S)
_STATUS_RE = re.compile(r'<div class="group_status">(.*?)</div>\s*</div>', re.S)
_DATE_RE = re.compile(r"\b(\d{2} [A-Z][a-z]{2} \d{4})\b")
_ACT_NO_RE = re.compile(r"\b(Act|Ordinance|Ord\.?)\s+(\d+)\s+of\s+(\d{4})\b")
_SL_NO_RE = re.compile(r"\bS\s+(\d+)/(\d{4})\b")


def _rows(page: str) -> list[str]:
    """The page cut at every `<tr`: one chunk per table row, whether or not the row is closed."""
    return _ROW_SPLIT_RE.split(page)[1:]


def _text(fragment: str) -> str:
    return " ".join(html_lib.unescape(re.sub(r"<[^>]+>", " ", fragment)).split())


def _unescape(url: str) -> str:
    return html_lib.unescape(url)


def _strip_stamp(url: str) -> str:
    """Drop the cache-busting `_=YYYYMMDDhhmmss` the portal appends to download links."""
    url = re.sub(r"[&?]_=\d+", "", url)
    return url


def iso_from_display(text: Optional[str]) -> Optional[str]:
    """'05 Dec 2025' -> '2025-12-05'."""
    if not text:
        return None
    try:
        return datetime.strptime(text.strip(), "%d %b %Y").date().isoformat()
    except ValueError:
        return None


def iso_from_compact(text: Optional[str]) -> Optional[str]:
    """'20251205' -> '2025-12-05'."""
    if not text or not re.fullmatch(r"\d{8}", text):
        return None
    return f"{text[:4]}-{text[4:6]}-{text[6:]}"


_NEXT_RE = re.compile(r'<a href="([^"]+)"[^>]*aria-label="Next Page"')


def next_page_path(page: str) -> Optional[str]:
    """The listing's own Next Page link (`/Browse/Act/Current/All/1?PageSize=100&...`), or None on the last page.

    The portal pages listings by path, counting from 0 after the first page; `PageIndex=` in the query is ignored
    (2026-09-16)."""
    m = _NEXT_RE.search(page)
    if not m:
        return None
    path = _unescape(m.group(1))
    return path if path.startswith("/Browse/") else None


def results_count(page: str) -> Optional[int]:
    m = _RESULTS_RE.search(page)
    return int(m.group(1).replace(",", "")) if m else None


@dataclass
class ListedLaw:
    """One row of a browse listing."""
    listing: str                     # current | repealed | uncommenced | acts_supp
    code: str                        # PDPA2012; 8-2026 for an Acts Supplement entry
    title: str
    path: str                        # the row's link, as listed (no host)
    number: Optional[str] = None     # "Act 8 of 2026" when the listing has a number column
    pdf_path: Optional[str] = None   # the row's PDF link, stamp removed
    repeal_date: Optional[str] = None
    doc_date: Optional[str] = None   # DocDate=YYYYMMDD on the row's link, ISO
    # the `_=YYYYMMDDhhmmss` on the row's PDF link, ISO: when the portal last GENERATED the file, not a legal date.
    # It matches the act's version date on 5 of 458 acts (2026-09-15), because files are regenerated without any
    # change in the law; but a new version always makes a new file, so an older stamp rules a new version out.
    file_stamp: Optional[str] = None


def parse_listing(page: str, listing: str) -> list[ListedLaw]:
    """The rows of one page of a Current, Repealed, Uncommenced or Acts Supplement listing."""
    out: list[ListedLaw] = []
    seen: set[str] = set()
    for row in _rows(page):
        m = _LINK_RE.search(row)
        if not m:
            continue
        path, title = _unescape(m.group(1)), _text(m.group(2))
        if not title:
            continue
        kind, rest = path.lstrip("/").split("/", 1)
        code = rest.split("/", 1)[0].split("?", 1)[0]
        if code in seen:
            continue
        seen.add(code)
        num = _NUMBER_COL_RE.search(row)
        pdf = _PDF_RE.search(row)
        rd = re.search(r"/Repealed/(\d{8})", path)
        dd = re.search(r"DocDate=(\d{8})", path)
        stamp = re.search(r"_=(\d{8})", pdf.group(1)) if pdf else None
        out.append(ListedLaw(listing=listing, code=code, title=title, path=path,
                             number=_text(num.group(1)) or None if num else None,
                             pdf_path=_strip_stamp(_unescape(pdf.group(1))) if pdf else None,
                             repeal_date=iso_from_compact(rd.group(1)) if rd else None,
                             doc_date=iso_from_compact(dd.group(1)) if dd else None,
                             file_stamp=iso_from_compact(stamp.group(1)) if stamp else None))
    return out


@dataclass
class Version:
    valid_from: Optional[str]        # ISO, from ValidDate=
    display_date: Optional[str]
    published_on: Optional[str]      # ISO, the popover's data-date
    status: str                      # the group_status text: "Amended by Act 19 of 2025", "Act 26 of 2012", "2020 RevEd"
    amended_by: Optional[str]        # "Act 19 of 2025" | "S 19/2015" when the status says so
    selected: bool                   # the current version on the page
    path: Optional[str]              # the version's page, no host
    pdf_path: Optional[str]


@dataclass
class ActDetail:
    code: str
    title: Optional[str]
    current_valid_from: Optional[str]           # ISO
    versions: list[Version] = field(default_factory=list)
    original_number: Optional[str] = None       # "Act 26 of 2012": the oldest version's status without "Amended by"
    revised_edition: Optional[str] = None       # "2020 RevEd" when a version carries it
    revised_edition_note: Optional[str] = None  # the front page's "This revised edition incorporates ..." sentence
    sl_path: Optional[str] = None

    @property
    def amendments(self) -> list[Version]:
        return [v for v in self.versions if v.amended_by]

    @property
    def last_amending_instrument(self) -> Optional[str]:
        """The newest amending instrument whose version is in force on or before the current one."""
        cur = self.current_valid_from
        cands = [v for v in self.amendments if v.valid_from and (cur is None or v.valid_from <= cur)]
        cands.sort(key=lambda v: v.valid_from or "")
        return cands[-1].amended_by if cands else None


def parse_detail(page: str, code: str) -> ActDetail:
    """An act's page: the current version's valid-from date (beside `versionDateHidden`), every version on the
    desktop timeline with its amending instrument, and the front page's revised-edition sentence."""
    t = re.search(r"<title>\s*(.*?)\s*-\s*Singapore Statutes Online\s*</title>", page, re.S)
    title = _text(t.group(1)) if t else None
    cur = re.search(r'id="versionsButton2">\s*(\d{2} [A-Z][a-z]{2} \d{4})', page)
    if not cur:
        cur = re.search(r'id="versionDateHidden"[^>]*/>\s*(\d{2} [A-Z][a-z]{2} \d{4})', page)
    current = iso_from_display(cur.group(1)) if cur else None
    versions: list[Version] = []
    for m in _LI_RE.finditer(page):
        cls, body = m.group("cls"), m.group("body")
        if "mobile" in cls.split():
            continue                                   # the mobile timeline repeats the desktop one
        vd = re.search(r"ValidDate=(\d{8})", body)
        if not vd:
            continue
        disp = _DATE_RE.search(_text(body))
        pub = re.search(r'data-date="([^"]+)"', body)
        st = _STATUS_RE.search(body)
        status = _text(st.group(1)) if st else ""
        am = re.match(r"Amended by\s+(.+)$", status)
        first = re.search(r'href="([^"]+)"', body)
        pdf = _PDF_RE.search(body)
        versions.append(Version(valid_from=iso_from_compact(vd.group(1)), display_date=disp.group(1) if disp else None,
                                published_on=iso_from_display(pub.group(1)) if pub else None, status=status,
                                amended_by=am.group(1).strip() if am else None, selected="selected" in cls.split(),
                                path=_strip_stamp(_unescape(first.group(1))).split("&ViewType", 1)[0] if first else None,
                                pdf_path=_strip_stamp(_unescape(pdf.group(1))) if pdf else None))
    versions.sort(key=lambda v: v.valid_from or "")
    original = next((v.status for v in versions if v.status and not v.amended_by and "RevEd" not in v.status), None)
    reved = next((v.status for v in versions if "RevEd" in v.status), None)
    note = re.search(r'<td class="revdTxt">(.*?)</td>', page, re.S)
    sl = re.search(r'href="(/Act/[^"?]+\?ViewType=Sl)"', page)
    if current is None and versions:
        sel = [v for v in versions if v.selected]
        current = (sel or versions)[-1].valid_from
    return ActDetail(code=code, title=title, current_valid_from=current, versions=versions,
                     original_number=original, revised_edition=reved,
                     revised_edition_note=_text(note.group(1)) if note else None,
                     sl_path=_unescape(sl.group(1)) if sl else None)


@dataclass
class ListedSl:
    code: str                        # PDPA2012-S65-2021
    title: str
    number: Optional[str]            # "S 65/2021"
    path: str                        # /SL/PDPA2012-S65-2021?DocDate=20240705
    doc_date: Optional[str]          # ISO
    pdf_path: Optional[str]


def parse_sl_tab(page: str) -> list[ListedSl]:
    """The subsidiary legislation listed under an act (`?ViewType=Sl`)."""
    out: list[ListedSl] = []
    seen: set[str] = set()
    for row in _rows(page):
        m = re.search(r'<a class="non-ajax" href="(/SL/[^"]+)"[^>]*>(.*?)</a>', row, re.S)
        if not m:
            continue
        path = _unescape(m.group(1))
        code = path.split("/SL/", 1)[1].split("?", 1)[0]
        if code in seen:
            continue
        seen.add(code)
        num = _SL_NO_RE.search(_text(row))
        pdf = _PDF_RE.search(row)
        dd = re.search(r"DocDate=(\d{8})", path)
        out.append(ListedSl(code=code, title=_text(m.group(2)), number=f"S {num.group(1)}/{num.group(2)}" if num else None,
                            path=path, doc_date=iso_from_compact(dd.group(1)) if dd else None,
                            pdf_path=_strip_stamp(_unescape(pdf.group(1))) if pdf else None))
    return out


def sl_tab_total(page: str) -> Optional[int]:
    return results_count(page)


def act_code(url: str) -> Optional[str]:
    """/Act/PDPA2012?ViewType=Pdf -> PDPA2012; None for anything that is not an SSO act page."""
    m = re.search(r"sso\.agc\.gov\.sg/Act/([A-Za-z0-9]+)(?:[/?#]|$)", url or "")
    return m.group(1) if m else None

