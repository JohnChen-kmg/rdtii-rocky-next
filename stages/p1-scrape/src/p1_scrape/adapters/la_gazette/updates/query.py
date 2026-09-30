"""The requests a check sends: robots.txt, then every listing page, current and superseded.

This is the one place where Laos is dearer than Timor-Leste. The gazette pages ten rows at a time and ignores
`Document_pageSize`, so there is no cheap "first page only" read of a listing that holds 657 agreements. A full
check re-reads every page: about 190 requests, some 25 minutes at 6 s (`../NOTES.md` 2.6).

`--pages N` is the cheap check, and it is honest about what it gives up: the gazette lists newest first by the
date it published each instrument, so the first pages carry everything recent. Reading two pages of each
listing costs about 25 requests and finds anything published since the last run, but it cannot see a law far
down a listing whose **status word** changed, and `changes.md` says so on every partial check.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from .diff import Changes, compare


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def check(adapter, client, baseline, since: Optional[str], pillars: list[int],
          pages: Optional[int] = None) -> Changes:
    """Read the listings, then compare what the portal lists with what the baseline held."""
    adapter._check_robots(client)
    kinds, olds = adapter._legal_types(), adapter._olds()
    limit = f", first {pages} page(s) of each" if pages else " in full"
    print(f"[updates] LA: reading {len(kinds)} listing(s) x {len(olds)} (current/superseded){limit} "
          f"at {client.delay:g} s", flush=True)
    adapter._open_gazette(client, max_pages=pages)
    for legal_type, counts in adapter.listing_counts.items():
        print(f"[updates] LA:   legaltype={legal_type} {counts['kind']}: {counts['records']} law(s) in "
              f"{counts['pages_read']} page(s)", flush=True)
    changes = compare(adapter.listed, baseline, since, checked_at=_now(), requests=len(client.log),
                      partial=bool(pages))
    changes.notes.extend(adapter.notes)
    if pages:
        changes.notes.append(
            f"PARTIAL CHECK: only the first {pages} page(s) of each listing were read. The gazette lists newest "
            f"first, so anything newly published is here, but a status word that changed further down a listing "
            f"is not, and every law below the cut is absent from the comparison rather than delisted")
    return changes
