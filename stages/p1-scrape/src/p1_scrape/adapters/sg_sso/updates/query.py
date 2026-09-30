"""The requests a check sends, in order, all through the adapter's own paced client and parser.

| What | Requests |
| :---- | ----: |
| robots.txt | 1 |
| The Current listing, 100 rows a page by its Next Page links (the portal refused the 500-row page) | 6 |
| The Repealed and Uncommenced listings, the same way | 4 |
| The Acts Supplement of this year and last | 2 |
| The timeline of every new act, and of every act whose file is newer than the date, up to the cap | 1 each |
| The regulations tab of each seed act, when asked | 1 each, more for a long tab |

**The portal's edge challenges a plain client after roughly 130 requests in a short time**
(`../NOTES.md` 1.3). A check reads twelve listing pages and then the timelines, capped at 60 by default, so it stays
well under that. If the challenge appears anyway, the check stops reading timelines at once, reports every act it
did not reach as `not_checked`, and still writes what it found: the listings it already read are not wasted.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from ....inventory import InventoryItem
from ...my_gazette.records import LomThrottled
from ..parse import act_code
from .diff import Changes, compare, new_acts, timeline_candidates


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def relevant_codes(adapter, current_rows: list) -> set:
    """The acts the title rule selects, worked out the way the catalogue does."""
    items = [InventoryItem(economy="SG", law_name=r.title, url=adapter.root + r.path, law_number=None, source="browse")
             for r in current_rows]
    adapter._mark_relevance(items)
    return {act_code(it.url) for it in items if it.relevant}


def check(adapter, client, baseline, since: str, pillars: list[int], max_timelines: int = 60,
          seed_regulations: bool = True) -> Changes:
    """Read the listings, then the timelines worth reading, then the seed acts' regulations; decide."""
    adapter._check_robots(client)
    adapter._open_sso(client)
    current_rows = adapter.listed.get("current", [])
    seeds = set(adapter._seed_by_code(pillars)[0])
    relevant = relevant_codes(adapter, current_rows)

    to_read, over_cap = timeline_candidates(current_rows, baseline, since, seeds, relevant, max_timelines)
    fresh = [r.code for r in new_acts(current_rows, baseline)]
    order = fresh + [c for c in to_read if c not in fresh]
    print(f"[updates] SG: listings read ({len(current_rows)} current, {len(adapter.listed.get('repealed', []))} "
          f"repealed, {len(adapter.listed.get('acts_supp', []))} in the Acts Supplement); {len(order)} timeline(s) to "
          f"read, {len(over_cap)} over the cap; {len(client.log)} request(s) so far", flush=True)
    notes: list[str] = []
    stopped: Optional[str] = None
    for i, code in enumerate(order):
        if i and i % 10 == 0:
            print(f"[updates] SG: {i} of {len(order)} timelines read; {len(client.log)} request(s) so far", flush=True)
        try:
            adapter._load_detail(code, client)
        except LomThrottled as e:
            stopped = str(e)
            over_cap = [c for c in order[i:] if c not in adapter.details] + over_cap
            break

    regulations: dict[str, list] = {}
    if seed_regulations and stopped is None:
        print(f"[updates] SG: timelines done; reading the seed acts' regulations tabs", flush=True)
        on_current = {r.code for r in current_rows}
        for code in sorted(seeds & on_current):
            try:
                regulations[code] = adapter._load_sl(code, client)
            except LomThrottled as e:
                stopped = str(e)
                notes.append(f"the regulations tabs of {len(seeds & on_current) - len(regulations)} seed act(s) were "
                             f"not read")
                break

    details = {c: adapter.details[c] for c in order if c in adapter.details}
    changes = compare(adapter.listed, details, regulations, baseline, since, checked_at=_now(),
                      not_checked=over_cap, requests=len(client.log))
    if stopped:
        changes.notes.append(f"the portal's edge challenged the check and it stopped reading: {stopped}. Everything "
                             f"it did not reach is listed as not_checked; run the check again after a rest")
    changes.notes.extend(notes)
    changes.notes.extend(adapter.notes)
    return changes
