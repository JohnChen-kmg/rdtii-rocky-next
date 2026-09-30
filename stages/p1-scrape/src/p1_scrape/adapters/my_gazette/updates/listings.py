"""The P.U. (A) and P.U. (B) listings: every subsidiary instrument with its date, parent act and file, newest first.

subsid.php?type=pua|pub is an empty shell like the act listings; its DataTables POSTs to json-subsid-2024.php with
type=pua|pub and decrypts the reply with the key the page publishes (the same key on every listing page read so far,
so a check reuses the act listing's key and reads the P.U. page only if decryption fails). Column 0 is the publication
date and the page orders by it, descending, so the first records are the newest. A check reads pages until one is
older than the floor: `since` less updates.subsidiary_lookback_days, because an instrument can be uploaded well after
its publication date (P.U. (B) 196/2026: published 29 May 2026, uploaded 3 September). Undated records sort last and
are never reached. The date sort is not unique, so records repeated across pages are dropped by number.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any, Optional

from ..parse import (
    _LOM, _blank, _clean, _dash_blank, _json_or_text, _positive_int, datatables_form, decode_token_target,
    decrypt_listing, extract_response_key, iso_date, portal_file_url,
)
from ..records import LomUnavailable

DEFAULT_LISTINGS = {
    "pua": {"page": "subsid.php?type=pua", "endpoint": "json-subsid-2024.php", "form": {"type": "pua"}},
    "pub": {"page": "subsid.php?type=pub", "endpoint": "json-subsid-2024.php", "form": {"type": "pub"}},
}
DEFAULT_PAGE_SIZE = 500          # as the act listings; one POST covers more than a year of either series
DEFAULT_MAX_PAGES = 30
DEFAULT_LOOKBACK_DAYS = 120
_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@dataclass
class SubsidiaryInstrument:
    kind: str                                  # pua | pub
    pu_no: str                                 # "P.U. (A) 324/2026", as the listing prints it
    sort_key: Optional[str]                    # the listing's own "2026-0324"
    title_bi: Optional[str]
    title_bm: Optional[str]
    publication_date: Optional[str]            # ISO
    status: Optional[str]                      # PRINCIPAL | AMENDMENT | PINDAAN | CORRIGENDUM | CANCEL | REVOCATION | REPRINT …
    act_no: Optional[str]                      # the parent act's number, "618"
    project_id: Optional[str]
    url: Optional[str]                         # the PDF, decoded from the signed download link
    related: Optional[str]                     # the instrument it amends or revokes, when the listing says
    commencement: Optional[str]
    raw: dict = field(default_factory=dict, repr=False)


def _date(value: Any) -> Optional[str]:
    s = _blank(value)
    if not s:
        return None
    return s if _ISO.match(s) else iso_date(s)


def _file_url(rec: dict, root: str) -> Optional[str]:
    href = re.search(r'href="([^"]+)"', rec.get("DOC2DOWNLOAD") or "")
    if not href:
        return None
    target = decode_token_target(href.group(1))
    if not target:
        return None
    for prefix in (root.rstrip("/"), _LOM):
        if target.startswith(prefix + "/"):
            return portal_file_url(target[len(prefix):], root)
    if "/ilims/upload/" in target:              # another host spelling of a lom path: keep the lom form
        return portal_file_url(target[target.index("/ilims/"):], root)
    return target


def parse_subsidiary(rec: dict, kind: str, root: str = _LOM) -> Optional[SubsidiaryInstrument]:
    pu_no = _clean(rec.get("noPU"))
    if not pu_no:
        return None
    return SubsidiaryInstrument(
        kind=kind, pu_no=pu_no, sort_key=_blank(rec.get("susunPU")),
        title_bi=_clean(rec.get("titleBI")) or None, title_bm=_clean(rec.get("titleBM")) or None,
        publication_date=_date(rec.get("publicationDate")), status=_clean(rec.get("statusOfLegislation")) or None,
        act_no=_clean(rec.get("ACT_NO")) or None, project_id=_blank(rec.get("PROJECT_ID")),
        url=_file_url(rec, root),
        related=_clean(rec.get("RELATEDPS1")) or _clean(rec.get("RELATEDPS3")) or None,
        commencement=_dash_blank(rec.get("commencementRemarkBi")) or _blank(rec.get("commencementDate")),
        raw=rec)


def floor_date(since: Optional[str], lookback_days: int) -> Optional[str]:
    """`since` less the look-back: instruments are read back to this date."""
    if not since:
        return None
    return (date.fromisoformat(since) - timedelta(days=max(0, lookback_days))).isoformat()


def fetch_subsidiary(client, root: str, kind: str, listing: dict, floor: Optional[str],
                     page_size: int = DEFAULT_PAGE_SIZE, max_pages: int = DEFAULT_MAX_PAGES,
                     key: Optional[str] = None) -> tuple[list[SubsidiaryInstrument], dict]:
    """Newest first, page by page, until a page ends before `floor` (ISO date), the listing ends, or `max_pages`.
    With `key` (the act listing page's SEARCH_RESPONSE_KEY) the listing page is read only if decryption fails.
    Returns the instruments dated on or after `floor`, one per number, and what the paging did."""
    page_path, endpoint = str(listing.get("page")), str(listing.get("endpoint"))
    extra = dict(listing.get("form") or {})
    page_reads = 0

    def read_key() -> str:
        nonlocal page_reads
        page = client.get(f"{root}/{page_path}", retries=2)
        if page.status_code != 200:
            raise LomUnavailable(f"lom {page_path} answered HTTP {page.status_code}")
        page_reads += 1
        return extract_response_key(page.text)

    if key is None:
        key = read_key()
    records: list[dict] = []
    start, draw, total, stopped = 0, 1, None, "listing end"
    while True:
        form = datatables_form(draw, start, page_size)
        form.update({k: str(v) for k, v in extra.items()})
        resp = client.post(f"{root}/{endpoint}", form, referer=f"{root}/{page_path}", retries=2)
        if resp.status_code != 200:
            raise LomUnavailable(f"lom {endpoint} ({kind}) answered HTTP {resp.status_code}")
        body = _json_or_text(resp)
        try:
            obj = decrypt_listing(body, key)
        except Exception as first:  # noqa: BLE001 — a stale key: read the page's key once and try again
            if page_reads:
                raise LomUnavailable(f"lom {endpoint} ({kind}): reply could not be decrypted ({first})") from first
            key = read_key()
            obj = decrypt_listing(body, key)
        reported = _positive_int(obj.get("recordsTotal"))
        if reported is not None:
            total = reported
        batch = obj.get("records") or obj.get("data") or []
        if not batch:
            break
        records.extend(batch)
        start += len(batch)
        draw += 1
        oldest = min((d for d in (_date(r.get("publicationDate")) for r in batch) if d), default=None)
        if floor and oldest and oldest < floor:
            stopped = f"a page older than {floor}"
            break
        if total is not None and start >= total:
            break
        if draw > max_pages:
            stopped = f"the {max_pages}-page cap (subsidiary_max_pages); older instruments were not read"
            break
    seen: set[str] = set()
    parsed: list[SubsidiaryInstrument] = []
    repeated = 0
    for inst in (parse_subsidiary(r, kind, root) for r in records):
        if inst is None:
            continue
        if inst.pu_no in seen:                  # the date sort is not unique: a record can straddle two pages
            repeated += 1
            continue
        seen.add(inst.pu_no)
        parsed.append(inst)
    kept = [inst for inst in parsed if not floor or inst.publication_date is None or inst.publication_date >= floor]
    meta = {"kind": kind, "page": page_path, "records_read": len(records), "records_total": total,
            "pages": draw - 1, "page_size": page_size, "page_reads": page_reads, "stopped_at": stopped,
            "floor": floor, "repeated_dropped": repeated, "kept": len(kept),
            "undated": sum(1 for inst in kept if inst.publication_date is None)}
    return kept, meta


def fetch_all_subsidiary(client, root: str, updates_cfg: dict, since: Optional[str],
                         key: Optional[str] = None) -> tuple[list[SubsidiaryInstrument], dict]:
    """Every configured series (updates.subsidiary_listings; default P.U. (A) and P.U. (B)), back to `since` less
    updates.subsidiary_lookback_days."""
    listings = dict(DEFAULT_LISTINGS)
    listings.update(updates_cfg.get("subsidiary_listings") or {})
    kinds = list(updates_cfg.get("subsidiary_kinds") or listings.keys())
    page_size = max(1, int(updates_cfg.get("subsidiary_page_size") or DEFAULT_PAGE_SIZE))
    max_pages = max(1, int(updates_cfg.get("subsidiary_max_pages") or DEFAULT_MAX_PAGES))
    lookback = updates_cfg.get("subsidiary_lookback_days")
    lookback = DEFAULT_LOOKBACK_DAYS if lookback is None else int(lookback)
    floor = floor_date(since, lookback)
    out: list[SubsidiaryInstrument] = []
    meta: dict[str, Any] = {}
    for kind in kinds:
        if kind not in listings:
            raise ValueError(f"updates.subsidiary_kinds names {kind!r}, which updates.subsidiary_listings does not define")
        found, m = fetch_subsidiary(client, root, kind, listings[kind], floor, page_size, max_pages, key=key)
        m["since"], m["lookback_days"] = since, lookback
        out.extend(found)
        meta[kind] = m
    return out, meta


def pages_needed(total: int, page_size: int) -> int:
    return math.ceil(total / page_size) if total else 0
