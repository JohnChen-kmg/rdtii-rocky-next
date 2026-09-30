"""Reading the Jornal da República's category pages.

The portal lists every act of a kind on **one page**, in a four-column table under a year heading:

    NUMÉRO      | DESCRIÇÃO                        | PUBLICADA EM | PDF
    N.º 1/2026  | Lei da Concorrência              | 25/3/2026    | PT -> public/docs/2026/serie_1/SERIE_I_NO_12.pdf

So a single request yields, for every act, its official number, its Portuguese title, the date it was published
and the address of the gazette issue that carries it. There is no detail page, no paging and no search
(`../NOTES.md` 1.2).

Two things this parser has to absorb, both seen on the live pages (2026-09-20):

- **The number is written a dozen ways**: `N.º 1/2026`, `N.o 12 /2024`, `N. o 72 / 2023`, `No12/2019`, `N0 16/2017`,
  `4/2017`, `N.° 1 /2026`. Only the digits mean anything, so they are what is kept.
- **Portuguese has two orthographies in the same table**: `eletrónico` and `electrónico`, `proteção` and
  `protecção`, because the 1990 agreement was adopted part-way through the period. Anything matching on titles
  must accept both, which is why `fold()` exists.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Optional
from urllib.parse import unquote, urljoin

ROOT = "https://www.mj.gov.tl"
JORNAL = f"{ROOT}/jornal/"

_ROW_RE = re.compile(r"<tr[^>]*>(.*?)</tr>", re.S | re.I)
_CELL_RE = re.compile(r"<t[dh][^>]*>(.*?)</t[dh]>", re.S | re.I)
_TAG_RE = re.compile(r"<[^>]+>")
_PDF_RE = re.compile(r'href="([^"]+\.pdf)"', re.I)
_NUMBER_RE = re.compile(r"(\d{1,4})\s*/\s*(\d{4})")
_DATE_RE = re.compile(r"(\d{1,2})\s*/\s*(\d{1,2})\s*/\s*(\d{4})")
# "Primeira alteração ao Decreto-Lei n.º 75/2023, de 15 de setembro" — an amendment names what it amends
#: the gazette's own host, however a row spells it. `www.jornal.gov.tl` is a FORMER domain and is not here: it
#: is a different site, so rows naming it keep it and are flagged instead (`../NOTES.md` 1.3)
_SAME_SITE = {"mj.gov.tl", "www.mj.gov.tl"}

_AMENDS_RE = re.compile(r"altera[çc][ãa]o\s+(?:ao|à|aos|do|da)\s+([^,]{0,60}?)n\.?[º°o]?\s*(\d{1,4}\s*/\s*\d{4})",
                        re.I)

#: the six category pages, by the node id the portal gives them, with what a row on each one is
CATEGORIES = {
    "leis": {"node": 12, "label": "Lei do Parlamento Nacional", "kind": "principal_act", "prefix": "L"},
    "decretos_leis": {"node": 13, "label": "Decreto-Lei do Governo", "kind": "principal_act", "prefix": "DL"},
    "decretos_governo": {"node": 18, "label": "Decreto do Governo", "kind": "subsidiary_legislation", "prefix": "DG"},
    "decretos_presidente": {"node": 10, "label": "Decreto do Presidente da República", "kind": "agency_or_other",
                            "prefix": "DP"},
    "resolucoes_parlamento": {"node": 19, "label": "Resolução do Parlamento Nacional", "kind": "agency_or_other",
                              "prefix": "RP"},
    "resolucoes_governo": {"node": 20, "label": "Resolução do Governo", "kind": "agency_or_other", "prefix": "RG"},
}


def category_path(node: int) -> str:
    """The address of one category page. The portal's own links use the `?q=node/<id>` form."""
    return f"/jornal/?q=node/{node}"


def text_of(html: str) -> str:
    """The visible text of a fragment, with entities and whitespace settled."""
    out = _TAG_RE.sub(" ", html)
    for entity, char in (("&nbsp;", " "), ("&amp;", "&"), ("&quot;", '"'), ("&#039;", "'"), ("&lt;", "<"),
                         ("&gt;", ">")):
        out = out.replace(entity, char)
    return re.sub(r"\s+", " ", out).strip()


def fold(text: str) -> str:
    """Upper case without accents, so `Proteção` and `PROTECÇÃO` and `protecao` all match one pattern."""
    stripped = "".join(c for c in unicodedata.normalize("NFD", text or "") if not unicodedata.combining(c))
    return stripped.upper()


def iso_date(text: str) -> Optional[str]:
    """`25/3/2026` → `2026-03-25`. The portal writes day first, sometimes zero-padded, sometimes not."""
    m = _DATE_RE.search(text or "")
    if not m:
        return None
    day, month, year = (int(g) for g in m.groups())
    if not (1 <= day <= 31 and 1 <= month <= 12):
        return None
    return f"{year:04d}-{month:02d}-{day:02d}"


def act_number(text: str) -> Optional[str]:
    """`N.o 12 /2024` → `12/2024`. Everything but the digits is decoration."""
    m = _NUMBER_RE.search(text or "")
    return f"{int(m.group(1))}/{m.group(2)}" if m else None


def amended_number(title: str) -> Optional[str]:
    """The act an amending title names: `Primeira alteração ao Decreto-Lei n.º 75/2023…` → `75/2023`."""
    m = _AMENDS_RE.search(title or "")
    return f"{int(m.group(2).split('/')[0].strip())}/{m.group(2).split('/')[1].strip()}" if m else None


@dataclass
class ListedAct:
    """One row of one category page: an act, and the gazette issue that carries it."""

    category: str                    # leis | decretos_leis | decretos_governo | decretos_presidente | resolucoes_*
    code: str                        # our portal id: L-1-2026, DL-12-2024
    number: Optional[str]            # 1/2026, as the portal numbers it
    title: str                       # the Portuguese description, as listed
    published_on: Optional[str]      # ISO, from the PUBLICADA EM column
    document_path: Optional[str]     # the issue's address, relative to the host
    document_kind: str               # principal_act | amending_act | subsidiary_legislation | agency_or_other
    amends: Optional[str] = None     # the act number this one alters, when the title says so
    year: Optional[str] = None

    @property
    def document_url(self) -> Optional[str]:
        return urljoin(JORNAL, self.document_path) if self.document_path else None


def parse_category(page: str, category: str) -> list[ListedAct]:
    """Every act row on one category page, in the order the portal lists them (newest year first)."""
    meta = CATEGORIES[category]
    out: list[ListedAct] = []
    seen: set[str] = set()
    for row in _ROW_RE.findall(page):
        cells = [text_of(c) for c in _CELL_RE.findall(row)]
        if len(cells) < 4 or not cells[1]:
            continue                                   # a year heading, the header row, or the filter row
        number, title, when = act_number(cells[0]), cells[1], iso_date(cells[2])
        if not title or fold(title) in ("DESCRICAO", "DESCRIÇÃO"):
            continue
        pdf = _PDF_RE.search(row)
        amends = amended_number(title)
        year = (number or "").split("/")[-1] if number else (when or "")[:4] or None
        code = f"{meta['prefix']}-{number.replace('/', '-')}" if number else f"{meta['prefix']}-{len(out) + 1}-{year}"
        if code in seen:                               # the portal repeats a row when an act spans two issues
            code = f"{code}-{sum(1 for c in seen if c.startswith(code)) + 1}"
        seen.add(code)
        out.append(ListedAct(
            category=category, code=code, number=number, title=title, published_on=when,
            document_path=_unescape(pdf.group(1)) if pdf else None,
            document_kind="amending_act" if amends and meta["kind"] == "principal_act" else meta["kind"],
            amends=amends, year=year,
        ))
    return out


def canonical_url(url: Optional[str]) -> Optional[str]:
    """One key for one file, whatever form of the gazette's address a run recorded.

    The parser has canonicalised addresses since the crawl of 2026-09-20 (`_unescape`, below), but a baseline written
    before that records the old forms. Compared as strings they differ, and the update check of 2026-09-22 reported
    **191 acts as moved and asked to re-fetch 50 issues it already held** — 188 differed only in scheme and host
    (`http://mj.gov.tl/…` against `https://www.mj.gov.tl/…`), 3 were the repaired host-less links. So an address is
    compared by this key, never by its string. The key is for matching only; it is never stored or fetched.
    The former domain, `www.jornal.gov.tl`, is left as stated, as `_unescape` leaves it.
    """
    if not url:
        return url
    u = url.replace("&amp;", "&").strip()
    m = re.match(r"^https?://([^/]+)(/.*)$", u)
    if not m:
        return u
    host, path = m.group(1).lower(), unquote(m.group(2))
    if "." not in host:                                  # http://public/docs/... : a relative link read as a host
        host, path = "www.mj.gov.tl", "/jornal/" + host + path
    if host in _SAME_SITE:
        return "https://www.mj.gov.tl" + path
    return u


def _unescape(url: str) -> str:
    """The row's address, with one repair the portal makes necessary.

    Some rows carry a **malformed absolute link**: `http://public/docs/2015/serie_1/SERIE_I_NO_28.pdf`, where the
    host is missing and "public" — the first path segment — has been read as one. A client follows that to a host
    that does not exist. Ten such rows were found in the crawl of 2026-09-20, and they are treated as the relative
    links they plainly are.

    Rows that name the gazette's **former domain** (`www.jornal.gov.tl`) are left exactly as the portal states
    them, and flagged instead: rewriting a stated address would be fixing, not flagging (`CONVENTIONS.md` rule 6).
    """
    url = url.replace("&amp;", "&").strip()
    m = re.match(r"^https?://([^/]+)(/.*)$", url)
    if not m:
        return url
    host, path = m.group(1).lower(), m.group(2)
    if "." not in host:                                  # a host with no dot is not a host
        return host + path                               # "public" + "/docs/..." -> "public/docs/..."
    if host in _SAME_SITE:
        # the same file is listed twice, as a relative link and as `http://mj.gov.tl/...`: one canonical address,
        # or the crawl stores it twice and the manifest carries two rows with one content hash (14 pairs on
        # 2026-09-20). Only this host family is canonicalised; another domain is left as stated, and flagged
        return path.replace("/jornal/", "", 1) if path.startswith("/jornal/") else path.lstrip("/")
    return url


def results_count(page: str) -> Optional[int]:
    """How many data rows the page holds. The portal states no total, so this is the parser's own count."""
    return sum(1 for row in _ROW_RE.findall(page) if len(_CELL_RE.findall(row)) >= 4) or None
