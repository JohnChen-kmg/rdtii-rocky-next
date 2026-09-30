"""The query: ask the register what has been registered since the last run, and read the titles behind it.

Requests, all to the API host at its paced client, none to `www` and no document:

| What | Requests |
| :---- | ----: |
| Versions registered since `<since>`, per prefix, 100 a page | 1 per page, usually 1 |
| The `Title` record of any changed title the baseline does not carry | 1 per 18 titles |

`robots.txt` of the API host is read by the adapter's own check before anything else.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from ..adapter import RegisterUnavailable            # one class, so the CLI's handler catches what this raises
from ..api import API, batches, decode, parse_titles, parse_versions, titles_by_id_url, versions_since_url
from .diff import Changes, compare

__all__ = ["RegisterUnavailable", "check", "titles_for", "versions_since"]


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def versions_since(api, since: str, prefixes: tuple[str, ...] = ("C", "F"), page: int = 100,
                   max_pages: int = 20, root: str = API) -> tuple[list, int, list[str]]:
    """Every latest version registered on or after `since`, one paged query per prefix."""
    found, requests, notes = [], 0, []
    for prefix in prefixes:
        skip = 0
        for _ in range(max_pages):
            url = versions_since_url(since, prefix=prefix, top=page, skip=skip).replace(API, root, 1)
            resp = api.get(url, retries=1)
            requests += 1
            if resp.status_code != 200:
                raise RegisterUnavailable(
                    f"the API answered HTTP {resp.status_code} for versions registered since {since} "
                    f"(prefix {prefix}, $skip={skip})")
            batch = parse_versions(decode(resp.content or b""))
            found.extend(batch)
            if len(batch) < page:
                break
            skip += page
        else:
            notes.append(f"prefix {prefix}: stopped at {max_pages} pages of {page}; there may be more")
    return found, requests, notes


def titles_for(api, ids: list[str], size: int = 18, root: str = API) -> tuple[dict, int, list[str]]:
    """The `Title` record of each id, in batches: the register's name, number, status and making date."""
    titles, requests, notes = {}, 0, []
    for chunk in batches(list(dict.fromkeys(ids)), size):
        resp = api.get(titles_by_id_url(chunk).replace(API, root, 1), retries=1)
        requests += 1
        if resp.status_code != 200:
            notes.append(f"titles for {len(chunk)} id(s) not read: HTTP {resp.status_code}")
            continue
        for t in parse_titles(decode(resp.content or b"")):
            titles[t.id] = t
    return titles, requests, notes


def check(adapter, api, baseline, since: Optional[str] = None, prefixes: tuple[str, ...] = ("C", "F"),
          root: Optional[str] = None) -> tuple[Changes, dict]:
    """What changed since `since` (default: the day the baseline's list was built), and the titles behind it."""
    since = since or (baseline.since if baseline else None)
    if not since:
        raise ValueError("no date to check from: pass --since, or point --outputs at a run with a list")
    root = root or API
    versions, requests, notes = versions_since(api, since, prefixes=prefixes, root=root)
    seeds = set(adapter._seed_by_id([6, 7]))
    changes = compare(versions, baseline, since=since, checked_at=_now(), requests=requests,
                      prefixes=list(prefixes), seeds=seeds)
    changes.notes.extend(notes)

    wanted = [c.portal_id for c in changes.to_fetch]
    titles, more, tnotes = titles_for(api, wanted, size=adapter._int_setting("version_batch", 18), root=root)
    changes.requests += more
    changes.notes.extend(tnotes)
    by_id = {v.title_id: v for v in versions}
    return changes, {"titles": titles, "versions": by_id}
