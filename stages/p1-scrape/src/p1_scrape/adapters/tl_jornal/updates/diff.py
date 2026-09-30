"""What changed on the Jornal da República since the last run, and what that means for the crawl.

The gazette is append-only: issues are published and never revised, and the portal states no status. So the
comparison is honest and short — an act is either one we already listed, or it is not:

| Found | Verdict | Fetched? |
| :---- | :---- | :---- |
| An act the baseline never listed | `new_act` | Yes, unless we already hold its issue |
| An act we listed, whose issue we never stored (a failed fetch, or a new run) | `not_stored` | Yes |
| An act we listed, now pointing at a different file | `document_moved` | Yes |
| An act the baseline listed that the portal no longer lists | `delisted` | No: reported |
| Anything else | `unchanged` | No |

With `--since` and no baseline, an act counts as `new_act` when the portal publishes it on or after that date.
There is no "amended" verdict here, because the portal never amends a document: an amending act is a **new act**
that names the one it alters, and the linkage lives in `contract_meta.principal_law_number`.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from ..parse import canonical_url

FETCH = ("new_act", "not_stored", "document_moved")


@dataclass
class Change:
    change: str                       # new_act | not_stored | document_moved | delisted | unchanged
    portal_id: str
    law_name: Optional[str] = None
    law_number: Optional[str] = None
    category: Optional[str] = None
    published_on: Optional[str] = None
    document_url: Optional[str] = None
    previous_document_url: Optional[str] = None
    stored_doc_id: Optional[str] = None
    note: Optional[str] = None

    def as_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}


@dataclass
class Changes:
    since: Optional[str] = None
    checked_at: Optional[str] = None
    requests: int = 0
    changes: list[Change] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def to_fetch(self) -> list[Change]:
        """One entry per document to crawl: an issue is fetched once however many acts point at it."""
        seen, out = set(), []
        for c in self.changes:
            if c.change in FETCH and c.document_url and c.document_url not in seen:
                seen.add(c.document_url)
                out.append(c)
        return out

    def counts(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for c in self.changes:
            out[c.change] = out.get(c.change, 0) + 1
        return out


def compare(listed: dict, baseline, since: Optional[str], checked_at: Optional[str] = None,
            requests: int = 0) -> Changes:
    """Every act the portal lists today against what the baseline held."""
    out = Changes(since=since, checked_at=checked_at, requests=requests)
    held = dict(baseline.acts) if baseline is not None else {}
    stored = baseline.stored if baseline is not None else {}
    # matched by canonical address, never by string: a baseline may record an older form of the same file's address
    stored_by_key = {canonical_url(u): row for u, row in stored.items()}

    def held_row(u):
        return stored_by_key.get(canonical_url(u)) if u else None

    seen: set[str] = set()

    for category, rows in listed.items():
        for row in rows:
            seen.add(row.code)
            was = held.get(row.code)
            url = row.document_url
            common = dict(portal_id=row.code, law_name=row.title, law_number=row.number, category=category,
                          published_on=row.published_on, document_url=url)
            if was is None:
                if baseline is None and since and (row.published_on or "") < since:
                    continue                                   # date mode: older than the date, not a change
                note = None
                if held_row(url) is not None:
                    note = "the issue that carries it is already stored: the act is new to the list, not to us"
                out.changes.append(Change(change="new_act", note=note,
                                          stored_doc_id=(held_row(url) or {}).get("doc_id"), **common))
                continue
            before = (was.get("document_url") or "").strip() or None
            if url and before and canonical_url(url) != canonical_url(before):
                out.changes.append(Change(change="document_moved", previous_document_url=before,
                                          note="the portal now points this act at a different file", **common))
            elif url and held_row(url) is None:
                out.changes.append(Change(change="not_stored", **common,
                                          note="listed before, but no run holds its issue"))
            else:
                out.changes.append(Change(change="unchanged", stored_doc_id=(held_row(url) or {}).get("doc_id"),
                                          **common))

    for portal_id, was in held.items():
        if portal_id in seen:
            continue
        out.changes.append(Change(change="delisted", portal_id=portal_id, law_name=was.get("title"),
                                  law_number=was.get("law_number"), category=was.get("category"),
                                  published_on=was.get("published_on"),
                                  document_url=(was.get("document_url") or None),
                                  note="the portal no longer lists this act; the copy we hold is unaffected"))
    return out
