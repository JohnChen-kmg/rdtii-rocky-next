"""What changed on the register since the last run: one paged API query, compared with the baseline.

The register answers the question directly. `/v1/versions` filtered by `isLatest eq true` and
`registeredAt ge <since>` returns every title whose latest version was registered since that date, with its
`registerId`. A title whose `registerId` differs from the one the baseline recorded has a **new version**; a title
the baseline never listed is **new**; a title whose status is no longer `InForce` has been **repealed or ceased**.

Two things to know about the query (`../NOTES.md` 1.2 and 1.3):

- **Order every paged query.** The API's `$skip` pages overlap when unordered, which cost a rebuild on
  2026-09-15: 340 titles came back twice and as many were missed.
- **A prefix is not a collection filter.** `C…G…` gazette notices, `C…Q…` bill-era titles and `F…N…` notices
  share the prefixes, and the register registers hundreds of legislative instruments a month that this country
  does not collect (decision 12 takes subsidiary instruments only under an in-scope principal law). `in_scope`
  keeps an Act, a title the baseline already lists, or a seed, and counts the rest as dropped.
- **Query by registration date, not by the version's start date.** The register lags: 46 of the 73 new versions
  found on 2026-09-13 had started before Round 1's crawl ran.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from ..api import LatestVersion

# A title id is <prefix><year><series letter><number>: C1914A00012 is an Act, F2026L01221 a legislative
# instrument, F2026N00693 a notice, C2026G... a gazette notice, C2026Q... a bill-era title. The harvest collects
# the Act collection plus the seeded instruments (decision 12), so those are the series a check may fetch.
_ACT_SERIES = "A"
# Q is the Commonwealth of Australia Constitution Act (C2004Q00685), which IS legislation: it is left out of this
# list so a change to it is never miscounted as a notice. It is still not fetched, because the harvest reads the
# Act collection and the Constitution is not in it; it would have to be seeded (NOTES.md 1.2, 2026-09-19).
_NEVER = ("G", "N", "B", "R")          # gazette notices, notifiable instruments, bulletins, rules-era titles


@dataclass
class Change:
    """One thing that changed, or one thing checked and found unchanged."""
    change: str                   # new_version | new_title | repealed | unchanged
    portal_id: str                # the register's title id
    law_name: Optional[str]
    law_number: Optional[str]
    version_id: Optional[str]     # the register id of the version now current
    previous_version_id: Optional[str]
    start: Optional[str]          # the day the new version's text starts
    registered_at: Optional[str]
    status: Optional[str]
    compilation_number: Optional[str]
    last_amending_instrument: Optional[str]
    stored_doc_id: Optional[str] = None
    stored_access_date: Optional[str] = None
    note: Optional[str] = None

    def as_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class Changes:
    since: Optional[str]
    checked_at: Optional[str]
    changes: list[Change] = field(default_factory=list)
    requests: int = 0
    notes: list[str] = field(default_factory=list)
    prefixes: list[str] = field(default_factory=list)
    dropped: dict[str, int] = field(default_factory=dict)

    @property
    def to_fetch(self) -> list[Change]:
        """The changes that need a document: a new version of a title we hold, or a title we do not."""
        return [c for c in self.changes if c.change in ("new_version", "new_title")]

    def counts(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for c in self.changes:
            out[c.change] = out.get(c.change, 0) + 1
        return out


def _series(register_id: Optional[str]) -> Optional[str]:
    """The series letter of a register id: C2026**C**00368 -> C."""
    rid = (register_id or "").strip()
    return rid[5].upper() if len(rid) > 5 and rid[1:5].isdigit() else None


def is_legislation(v: LatestVersion) -> bool:
    """False for the gazette notices, bills and administrative notices that share the `C` and `F` prefixes."""
    return _series(v.title_id) not in _NEVER


def in_scope(v: LatestVersion, baseline, seeds: Optional[set] = None) -> bool:
    """Whether a title the query returned is one this country collects.

    The harvest reads the **Act collection** and the seeded instruments, so a legislative instrument the baseline
    never listed is out of scope however new it is: the register registers hundreds a month, and decision 12 takes
    subsidiary instruments only under an in-scope principal law. A new **Act** is in scope, because the next full
    list would carry it.
    """
    if not is_legislation(v):
        return False
    if baseline is not None and v.title_id in (baseline.listed or {}):
        return True
    if seeds and v.title_id in seeds:
        return True
    return _series(v.title_id) == _ACT_SERIES


def compare(versions: list[LatestVersion], baseline, since: Optional[str], checked_at: Optional[str] = None,
            requests: int = 0, prefixes: Optional[list[str]] = None, seeds: Optional[set] = None) -> Changes:
    """Every version the query returned, against what the baseline recorded for the same title.

    A title outside what this country collects is counted and dropped, never queued: see `in_scope`.
    """
    out = Changes(since=since, checked_at=checked_at, requests=requests, prefixes=list(prefixes or []))
    dropped: dict[str, int] = {}
    for v in versions:
        if not in_scope(v, baseline, seeds):
            s = _series(v.title_id) or "?"
            key = s if not is_legislation(v) else f"{s} (not collected)"
            dropped[key] = dropped.get(key, 0) + 1
            continue
        listed = (baseline.listed or {}).get(v.title_id) if baseline else None
        previous = (listed or {}).get("version_id") or None
        stored = (baseline.by_portal_id or {}).get(v.title_id) if baseline else None
        status = (v.status or "").strip()
        if status and status.lower() != "inforce":
            change = "repealed"
        elif listed is None:
            change = "new_title"
        elif previous and v.register_id and previous != v.register_id:
            change = "new_version"
        elif not previous:
            change = "new_version"          # the baseline listed the title but recorded no version id
        else:
            change = "unchanged"
        out.changes.append(Change(
            change=change, portal_id=v.title_id, law_name=v.name or (listed or {}).get("title"),
            law_number=(listed or {}).get("law_number"), version_id=v.register_id, previous_version_id=previous,
            start=v.start, registered_at=v.registered_at, status=v.status or (listed or {}).get("legal_status"),
            compilation_number=v.compilation_number, last_amending_instrument=v.last_amending_instrument,
            stored_doc_id=(stored.doc_id if stored else None),
            stored_access_date=(stored.access_date if stored else None),
            note=("the baseline lists this title with no version id" if listed is not None and not previous else None),
        ))
    out.dropped = dropped
    out.changes.sort(key=lambda c: (c.change, (c.law_name or "").lower()))
    return out
