"""The requests a check sends: robots.txt, then one page per category. Six or seven in all.

That is the whole cost of knowing what Timor-Leste published since the last run, because each category page
carries its entire history (`../NOTES.md` 1.2). No document is fetched to find out what changed, and no detail
page exists to read.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from .diff import Changes, compare


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def check(adapter, client, baseline, since: Optional[str], pillars: list[int]) -> Changes:
    """Read every category page, then compare what the portal lists with what the baseline held."""
    adapter._check_robots(client)
    print(f"[updates] TL: reading {len(adapter._categories())} category page(s) at {client.delay:g} s", flush=True)
    adapter._open_jornal(client)
    for category, counts in adapter.listing_counts.items():
        print(f"[updates] TL:   {category}: {counts['records']} act(s), {counts['documents']} document(s)", flush=True)
    changes = compare(adapter.listed, baseline, since, checked_at=_now(), requests=len(client.log))
    changes.notes.extend(adapter.notes)
    return changes
