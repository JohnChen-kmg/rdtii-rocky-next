"""What changed on Statutes Online since a date: the decisions, made from what the listings and timelines say.

No request is sent here; `query.py` reads the pages and this module decides. One rule per kind of change:

| Found | Rule | Result |
| :---- | :---- | :---- |
| An act on the Current listing the baseline did not have | | `new_act`, fetched |
| An Acts Supplement entry the baseline did not have | published on or after the date | `new_publication`, fetched |
| A Repealed listing entry | repealed on or after the date, or an act the baseline held as current | `repealed`, reported |
| An act whose file stamp is on or after the date | its timeline is read | see below |
| A regulation on a seed act's tab | not in the baseline, or its date moved | `new_regulation` / `amended`, fetched |

**An amendment is decided by the timeline's in-force date, never by a publication date.** An amending act is
often published long before it takes effect: Act 40 of 2020 was published in December 2020 and took effect in
October 2022, and the Online Criminal Harms Act's version of 15 September 2026 comes from an act published in
March 2025. So a timeline read gives `amended` when the newest in-force date is later than the version date the
baseline recorded, `amended_file_pending` when that newest version has no file yet, and `regenerated` when the
date did not move (the portal regenerates files without any change in the law).

**The file stamp only chooses which timelines to read.** It is when the portal last generated the file, not a
legal date, but a new version always makes a new file, so an act whose file is older than the date cannot have a
new version. `timeline_candidates` orders what passes that test (seeds, then acts the title rule selects, then the
most recently regenerated) and cuts it at the cap, so a long gap cannot provoke the portal's challenge. What the
cap leaves out is reported as `not_checked`, never dropped silently.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Optional

_AMENDING_TITLE = re.compile(r"\b(Amendment|Amendments|Miscellaneous Amendments|Repeal)\b", re.I)
FETCH = ("new_act", "new_publication", "new_regulation", "amended")


@dataclass
class Change:
    change: str
    portal_id: str
    law_name: Optional[str]
    listing: str                                  # current | repealed | acts_supp | regulation
    law_number: Optional[str] = None
    in_force_from: Optional[str] = None           # the newest version's in-force date, from the timeline
    previous_version: Optional[str] = None        # what the baseline recorded
    amended_by: Optional[str] = None
    published_on: Optional[str] = None
    repeal_date: Optional[str] = None
    file_stamp: Optional[str] = None
    has_file: Optional[bool] = None
    parent: Optional[str] = None                  # a regulation's act
    stored_doc_id: Optional[str] = None
    note: Optional[str] = None

    def as_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class Changes:
    since: Optional[str]
    checked_at: Optional[str]
    changes: list[Change] = field(default_factory=list)
    requests: int = 0
    timelines_read: int = 0
    notes: list[str] = field(default_factory=list)

    @property
    def to_fetch(self) -> list[Change]:
        return [c for c in self.changes if c.change in FETCH]

    def counts(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for c in self.changes:
            out[c.change] = out.get(c.change, 0) + 1
        return out


def timeline_candidates(current_rows: list, baseline, since: str, seeds: set, relevant: set,
                        cap: int) -> tuple[list[str], list[str]]:
    """(the acts whose timelines to read, the ones the cap leaves out).

    An act qualifies when its file was generated on or after `since` and the baseline already holds it as current.
    A new act is read regardless and is not counted here: `new_acts` finds those.
    """
    held = baseline.current if baseline is not None else None
    fresh = [r for r in current_rows
             if r.file_stamp and r.file_stamp >= since and (held is None or r.code in held)]
    fresh.sort(key=lambda r: (r.code not in seeds, r.code not in relevant, _negate(r.file_stamp), r.code))
    codes = [r.code for r in fresh]
    return (codes[:cap], codes[cap:]) if cap and cap > 0 else (codes, [])


def _negate(stamp: Optional[str]) -> str:
    """Sort newest first without reversing the whole key."""
    return "".join(chr(0x7F - ord(c)) for c in (stamp or ""))


def new_acts(current_rows: list, baseline) -> list:
    """Acts on the Current listing that the baseline did not hold as current: newly passed, or newly commenced."""
    if baseline is None:
        return []
    held = baseline.current
    return [r for r in current_rows if r.code not in held]


def _current_version(detail):
    if detail is None or not detail.versions:
        return None
    for v in detail.versions:
        if v.selected:
            return v
    for v in detail.versions:
        if v.valid_from == detail.current_valid_from:
            return v
    return detail.versions[-1]


def compare(listed: dict, details: dict, regulations: dict, baseline, since: str, checked_at: Optional[str] = None,
            not_checked: Optional[list[str]] = None, requests: int = 0) -> Changes:
    """Every change the pages show, decided by the rules in this module's docstring."""
    out = Changes(since=since, checked_at=checked_at, requests=requests, timelines_read=len(details))
    current = {r.code: r for r in listed.get("current", [])}
    stored = baseline.by_portal_id if baseline is not None else {}

    def doc_of(code: str) -> Optional[str]:
        d = stored.get(code)
        return d.doc_id if d else None

    # --- new acts: passed, or commenced (the baseline held them as uncommenced) -----------------------------------
    for r in new_acts(listed.get("current", []), baseline):
        was = baseline.listing_of(r.code) if baseline is not None else None
        detail = details.get(r.code)
        v = _current_version(detail)
        out.changes.append(Change(
            change="new_act", portal_id=r.code, law_name=r.title, listing="current", law_number=r.number,
            in_force_from=detail.current_valid_from if detail else None, published_on=v.published_on if v else None,
            file_stamp=r.file_stamp, has_file=bool(r.pdf_path),
            note=("commenced: the baseline listed it as not yet in force" if was == "uncommenced" else None)))

    # --- amendments, from the timelines ---------------------------------------------------------------------------
    for code, detail in details.items():
        row = current.get(code)
        if row is None or (baseline is not None and code not in baseline.current):
            continue                                            # a new act, decided above
        newest = detail.current_valid_from
        previous = baseline.version_of(code) if baseline is not None else None
        v = _current_version(detail)
        if newest and ((previous and newest > previous) or (not previous and newest >= since)):
            change = "amended" if (v and v.pdf_path) else "amended_file_pending"
            note = None if previous else "the baseline recorded no version date; compared with the date instead"
            if change == "amended_file_pending":
                note = ("the portal has not generated a file for this version yet; the next check picks it up "
                        + (f"({note})" if note else "")).strip()
        else:
            change, note = "regenerated", None
        out.changes.append(Change(
            change=change, portal_id=code, law_name=row.title, listing="current",
            law_number=detail.original_number, in_force_from=newest, previous_version=previous,
            amended_by=(v.amended_by if v else None), published_on=(v.published_on if v else None),
            file_stamp=row.file_stamp, has_file=bool(v and v.pdf_path), stored_doc_id=doc_of(code), note=note))

    for code in not_checked or []:
        row = current.get(code)
        out.changes.append(Change(
            change="not_checked", portal_id=code, law_name=row.title if row else None, listing="current",
            file_stamp=row.file_stamp if row else None, previous_version=baseline.version_of(code) if baseline else None,
            note="its file is newer than the date, but the cap on timeline reads was reached: run again to read it"))

    # --- repeals ----------------------------------------------------------------------------------------------------
    held = baseline.current if baseline is not None else set()
    for r in listed.get("repealed", []):
        recent = bool(r.repeal_date and r.repeal_date >= since)
        was_current = r.code in held and r.code not in current
        if recent or was_current:
            out.changes.append(Change(
                change="repealed", portal_id=r.code, law_name=r.title, listing="repealed", law_number=r.number,
                repeal_date=r.repeal_date, stored_doc_id=doc_of(r.code),
                note=("the baseline held it as current" if was_current else None)))

    # --- the Acts Supplement ----------------------------------------------------------------------------------------
    known = baseline.supplement_codes if baseline is not None else set()
    for r in listed.get("acts_supp", []):
        if r.code in known or not (r.doc_date and r.doc_date >= since):
            continue
        amending = bool(_AMENDING_TITLE.search(r.title))
        out.changes.append(Change(
            change="new_publication", portal_id=r.code, law_name=r.title, listing="acts_supp", law_number=r.number,
            published_on=r.doc_date, has_file=bool(r.pdf_path),
            note=("an amending act, fetched as published" if amending else
                  "a new principal act: fetched as enacted only if the Current listing does not carry it yet")))

    # --- regulations under the seed acts ---------------------------------------------------------------------------
    subs = baseline.subsidiary_codes if baseline is not None else set()
    recorded = {}
    if baseline is not None:
        for row in baseline.documents.values():
            m = row.get("contract_meta") or {}
            if m.get("document_kind") == "subsidiary_legislation" and m.get("portal_id"):
                recorded[str(m["portal_id"])] = m.get("version_as_at")
    for act, rows in regulations.items():
        for sl in rows:
            if sl.code not in subs:
                if sl.doc_date and sl.doc_date >= since:
                    out.changes.append(Change(
                        change="new_regulation", portal_id=sl.code, law_name=sl.title, listing="regulation",
                        law_number=sl.number, in_force_from=sl.doc_date, parent=act, has_file=bool(sl.pdf_path)))
            elif sl.doc_date and recorded.get(sl.code) and sl.doc_date > recorded[sl.code]:
                out.changes.append(Change(
                    change="amended", portal_id=sl.code, law_name=sl.title, listing="regulation",
                    law_number=sl.number, in_force_from=sl.doc_date, previous_version=recorded[sl.code],
                    parent=act, has_file=bool(sl.pdf_path), stored_doc_id=doc_of(sl.code)))

    order = {"new_act": 0, "new_publication": 1, "amended": 2, "new_regulation": 3, "amended_file_pending": 4,
             "repealed": 5, "not_checked": 6, "regenerated": 7}
    out.changes.sort(key=lambda c: (order.get(c.change, 9), (c.law_name or "").lower()))
    return out
