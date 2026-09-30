"""The Federal Register of Legislation's OData API (api.prod.legislation.gov.au/v1): records, queries and the
addresses the register serves documents at. No function here sends a request.

Shapes seen live on 2026-09-15 (tests/fixtures/api_*.json):
  titles   id, name, collection, subCollection, isPrincipal, isInForce, status (InForce | Ceased | Repealed |
           NeverEffective), makingDate, year, number, seriesType, hasCommencedUnincorporatedAmendments, ...
  versions titleId, registerId (the compilation id, C2026C00227; the title id for an as-made version), start, end,
           isCurrent, isLatest, registeredAt, compilationNumber, status, reasons (the amendments the compilation
           incorporates: affectedByTitle with titleId, name, year, number, provisions)
A dated document lives at <www>/<titleId>/<start>/<start>/text/original/pdf (checked by HEAD on the Privacy Act's
C2026C00227: HTTP 200, application/pdf), the epub with every volume at .../text/original/epub.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Optional
from urllib.parse import quote

API = "https://api.prod.legislation.gov.au/v1"
WWW = "https://www.legislation.gov.au"
REG_ID = re.compile(r"\b([CF]\d{4}[A-Z]\d{5})\b")      # C: acts and compilations; F: legislative instruments
TITLE_FIELDS = "id,name,collection,subCollection,isPrincipal,isInForce,status,makingDate,year,number,seriesType"


def iso(value: Optional[str]) -> Optional[str]:
    """'2026-06-04T00:00:00' -> '2026-06-04'."""
    return value[:10] if value and len(value) >= 10 else None


@dataclass
class Title:
    id: str
    name: str
    collection: Optional[str]
    is_principal: bool
    is_in_force: bool
    status: Optional[str]
    making_date: Optional[str]      # ISO
    year: Optional[int]
    number: Optional[int]
    series_type: Optional[str]
    raw: dict = field(repr=False, default_factory=dict)

    @property
    def law_number(self) -> Optional[str]:
        return f"No. {self.number}, {self.year}" if self.number is not None and self.year else None


@dataclass
class Reason:
    affect: Optional[str]
    title_id: Optional[str]
    name: Optional[str]
    year: Optional[int]
    number: Optional[int]
    provisions: Optional[str]
    series_type: Optional[str]

    @property
    def instrument(self) -> Optional[str]:
        if not self.name:
            return None
        return f"{self.name} (No. {self.number}, {self.year})" if self.number is not None and self.year else self.name


@dataclass
class LatestVersion:
    title_id: str
    register_id: Optional[str]
    start: Optional[str]            # ISO
    end: Optional[str]
    registered_at: Optional[str]    # ISO date
    compilation_number: Optional[str]
    name: Optional[str]
    status: Optional[str]
    is_current: Optional[bool]
    reasons: list[Reason] = field(default_factory=list)
    raw: dict = field(repr=False, default_factory=dict)

    @property
    def is_compilation(self) -> bool:
        """A compiled version has a compilation number above 0 and its own register id; an as-made title's latest
        version carries compilationNumber 0 and the title id as registerId (C2021A00098, F2025L00278, 2026-09-15)."""
        return bool(self.compilation_number) and self.compilation_number != "0" and self.register_id != self.title_id

    @property
    def amendments(self) -> list[Reason]:
        return [r for r in self.reasons if (r.affect or "").lower() == "amend" and r.name]

    @property
    def last_amending_instrument(self) -> Optional[str]:
        ams = self.amendments
        if not ams:
            return None
        ams = sorted(ams, key=lambda r: ((r.year or 0), (r.number or 0)))
        return ams[-1].instrument


def parse_titles(data: Any) -> list[Title]:
    out = []
    for v in (data or {}).get("value", []) or []:
        if not v.get("id"):
            continue
        out.append(Title(id=v["id"], name=v.get("name") or v["id"], collection=v.get("collection"),
                         is_principal=bool(v.get("isPrincipal")), is_in_force=bool(v.get("isInForce")),
                         status=v.get("status"), making_date=iso(v.get("makingDate")), year=v.get("year"),
                         number=v.get("number"), series_type=v.get("seriesType"), raw=v))
    return out


def parse_versions(data: Any) -> list[LatestVersion]:
    out = []
    for v in (data or {}).get("value", []) or []:
        if not v.get("titleId"):
            continue
        reasons = []
        for r in v.get("reasons") or []:
            t = r.get("affectedByTitle") or {}
            reasons.append(Reason(affect=r.get("affect"), title_id=t.get("titleId"), name=t.get("name"), year=t.get("year"),
                                  number=t.get("number"), provisions=t.get("provisions"), series_type=t.get("seriesType")))
        out.append(LatestVersion(title_id=v["titleId"], register_id=v.get("registerId"), start=iso(v.get("start")),
                                 end=iso(v.get("end")), registered_at=iso(v.get("registeredAt")),
                                 compilation_number=(str(v["compilationNumber"]) if v.get("compilationNumber") not in (None, "") else None),
                                 name=v.get("name"), status=v.get("status"), is_current=v.get("isCurrent"),
                                 reasons=reasons, raw=v))
    return out


def decode(body: bytes) -> Optional[dict]:
    try:
        return json.loads(body.decode("utf-8", "replace"))
    except (ValueError, AttributeError):
        return None


# --- queries ---------------------------------------------------------------------------------------------------

def titles_url(skip: int, top: int, in_force: bool = True, collection: str = "Act") -> str:
    """One page of the title harvest. `$orderby=id` is required: without it the API's `$skip` pages overlap (the
    build of 12:05 UTC on 2026-09-15 saw 340 principal titles twice and missed about as many)."""
    flt = f"isInForce eq {'true' if in_force else 'false'} and collection eq '{collection}'"
    return f"{API}/titles?$filter={quote(flt)}&$select={TITLE_FIELDS}&$orderby=id&$skip={skip}&$top={top}"


def titles_by_id_url(ids: list[str]) -> str:
    flt = "id in (" + ",".join(f"'{i}'" for i in ids) + ")"
    return f"{API}/titles?$filter={quote(flt)}&$select={TITLE_FIELDS}"


def versions_url(ids: list[str]) -> str:
    """The latest version of each title, up to 18 ids per request (an OR-chain of 18 answers 400)."""
    flt = "isLatest eq true and titleId in (" + ",".join(f"'{i}'" for i in ids) + ")"
    return f"{API}/versions?$filter={quote(flt)}"


def versions_since_url(since: str, prefix: str = "C", top: int = 100, skip: int = 0) -> str:
    """Every latest version registered on or after `since` (ISO date; no trailing Z on the literal)."""
    flt = f"isLatest eq true and registeredAt ge {since}T00:00:00 and startswith(titleId,'{prefix}')"
    return f"{API}/versions?$filter={quote(flt)}&$orderby=registeredAt&$top={top}&$skip={skip}"


# --- document addresses --------------------------------------------------------------------------------------

def pdf_url(v: LatestVersion) -> Optional[str]:
    """The dated PDF of a compilation (a multi-volume compilation has none: HTTP 405), or the as-made PDF of a title
    never compiled (<id>/asmade/<start>/text/original/pdf, the downloads page's own link, 2026-09-15)."""
    if not v.start:
        return None
    if v.is_compilation:
        return f"{WWW}/{v.title_id}/{v.start}/{v.start}/text/original/pdf"
    return f"{WWW}/{v.title_id}/asmade/{v.start}/text/original/pdf"


def epub_url(v: LatestVersion) -> Optional[str]:
    """The dated epub of a compilation: every volume as spine documents (p1_scrape.epub), single-volume acts
    included. An as-made title offers no epub (its downloads page lists PDF and Word only)."""
    if v.is_compilation and v.start:
        return f"{WWW}/{v.title_id}/{v.start}/{v.start}/text/original/epub"
    return None


def register_id(url: str) -> Optional[str]:
    m = REG_ID.search(url or "")
    return m.group(1) if m and "legislation.gov.au" in (url or "") else None


def batches(items: list[str], size: int) -> list[list[str]]:
    return [items[i:i + size] for i in range(0, len(items), size)]
