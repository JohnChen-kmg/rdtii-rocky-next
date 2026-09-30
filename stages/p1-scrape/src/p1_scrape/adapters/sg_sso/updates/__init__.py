"""Singapore — what changed on Statutes Online since a date, and the delta list to crawl for it.

**Built 2026-09-16**, on the logic the developer settled that day. Two steps, like the other countries:

1. **check** — take a date (the day the last run's list was built, or `--since`), read the portal's listings,
   read the timeline of every act that could have changed, and decide. It writes `changes.json` and `changes.md`.
2. **delta** — the documents to fetch, as a link list the ordinary crawl replays into the same run folder.

**What changed, and how each is decided** (`diff.py` has the rules):

- **New acts**: on the Current listing, not held by the baseline. Fetched.
- **New and amending acts as published**: Acts Supplement entries dated on or after the date. Fetched.
- **Repeals**: Repealed listing entries dated on or after the date. **Reported, not fetched.**
- **Amendments**: the act's **timeline**, never a publication date. An amending act can be published years
  before it takes effect (Act 40 of 2020: published December 2020, in force October 2022), so an act is amended
  when the newest in-force date on its timeline is later than the date the baseline recorded. Fetched.
- **New regulations under the seed acts**: each seed act's regulations tab. Fetched.

**Why this does not read all 525 act pages.** The portal's edge challenges a plain client after about 130
requests (`../NOTES.md` 1.3). The Current listing carries, for each act, the time its file was last generated.
That is not a legal date (it matches the version date on 5 of 458 acts), but a new version always makes a new
file, so an act whose file is older than the date cannot have been amended. Only the rest have their timeline
read, and a cap (60 by default) keeps a long gap inside the portal's tolerance.

**What it cannot see**, each written into `updates/WORKFLOW.md` rather than left to be discovered:

- **A new version whose file the portal has not generated yet** keeps an old file stamp, so it is not read until
  the file appears (the Online Criminal Harms Act's version of 15 September 2026 was such a case). Nothing could be
  fetched for it before then anyway.
- **A correction or republication** that does not regenerate the file.
- **New regulations under an act that is not a seed**: those tabs are not read.

What was known before the build, and still holds: the act page's `versionDateHidden` is the current valid-from
date; `Last-Modified` is a generation stamp and not a signal; the per-act RSS feed repeats a provision once per
version; robots.txt asks for 6 seconds and forbids `/search`.

    python -m p1_scrape.adapters.sg_sso.updates --outputs <ws>/outputs/SG
"""
from __future__ import annotations

from .baseline import Baseline, StoredDocument, list_runs
from .baseline import load as load_baseline
from .delta import build_delta, carried_forward, changes_markdown, write_changes
from .diff import FETCH, Change, Changes, compare, new_acts, timeline_candidates
from .query import check, relevant_codes

__all__ = ["Baseline", "StoredDocument", "list_runs", "load_baseline", "build_delta", "carried_forward",
           "changes_markdown", "write_changes", "FETCH", "Change", "Changes", "compare", "new_acts",
           "timeline_candidates", "check", "relevant_codes", "find_changes"]


def find_changes(cfg: dict, since: str, fetcher=None) -> list[dict]:
    """The shape `countries/_template/updates/__init__.py` describes, for a caller that wants the changes only.
    With no baseline, an act is amended when its newest in-force date falls on or after `since`."""
    from ..adapter import SgSsoAdapter

    adapter = SgSsoAdapter(cfg)
    client = adapter._get_client(fetcher)
    changes = check(adapter, client, baseline=None, since=since, pillars=[6, 7])
    return [c.as_dict() for c in changes.changes]
