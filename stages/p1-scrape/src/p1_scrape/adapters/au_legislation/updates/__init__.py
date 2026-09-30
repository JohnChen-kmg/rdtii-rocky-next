"""Australia — what changed on the Federal Register since the last run, and the delta list to crawl for it.

Two steps, like the scraper (`../NOTES.md` 2.6), and **built 2026-09-16** on the developer's instruction:

1. **check** — one paged API query per title-id prefix for every latest version registered since the baseline's
   list was built, plus one batched query for the `Title` record of anything that changed. Three to six requests,
   no document, nothing on the `www` host beyond `robots.txt`. It writes `changes.json` and `changes.md`.
2. **delta** — the changed titles as a link list (`links_used/`), built by the same adapter code the full list
   uses, which the crawl then replays into the same run folder.

**Why the register makes this cheap.** Version identity is explicit: every version carries a `registerId`, and a
title whose id differs from the one we recorded has a new text. Nothing has to be re-read to find that out, and
no document is fetched to compare. Australia's whole statute book can be checked in about five requests, where
Singapore's portal would need one page per act.

**What the check does not cover yet**, each recorded rather than silently skipped:

- **New subsidiary instruments under an Act** (`<titleId>/latest/authorises` on the `www` host, at its 10-second
  delay). The check sees a new instrument only when the instrument itself is a title the query returns.
- **A rectification that does not change the register id.** The register does correct documents in place; the id
  test cannot see that, and only a content hash would (`POLICY.md` section 6, test three).
- **Titles that vanish from the harvest.** A repeal shows here when the API still returns the title with a status
  other than `InForce`. A title that stops being returned at all is caught by the next full list build, not by
  this check.

    python -m p1_scrape.adapters.au_legislation.updates --outputs <ws>/outputs/AU

`updates/WORKFLOW.md` has the whole procedure and what each file it writes holds.
"""
from __future__ import annotations

from .baseline import Baseline, StoredDocument, list_runs
from .baseline import load as load_baseline
from .query import RegisterUnavailable, check, titles_for, versions_since
from .delta import build_delta, changes_markdown, write_changes
from .diff import Change, Changes, compare, in_scope, is_legislation

__all__ = ["Baseline", "StoredDocument", "list_runs", "load_baseline", "check", "versions_since", "titles_for",
           "RegisterUnavailable", "build_delta", "write_changes", "changes_markdown", "Change", "Changes",
           "compare", "in_scope", "is_legislation", "find_changes"]


def find_changes(cfg: dict, since: str, fetcher=None) -> list[dict]:
    """The shape `countries/_template/updates/__init__.py` describes, for a caller that wants the changes only.

    The command line is the supported entry point; this wrapper exists so the engine's own update hook can call
    the check without knowing how the package is laid out.
    """
    from ..adapter import AuLegislationAdapter

    adapter = AuLegislationAdapter(cfg)
    api, www = adapter._clients(fetcher)
    adapter._check_robots(api, www)
    changes, _found = check(adapter, api, baseline=None, since=since, root=adapter._api_root())
    return [c.as_dict() for c in changes.changes]
