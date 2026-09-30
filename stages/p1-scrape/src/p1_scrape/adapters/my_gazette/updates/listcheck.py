"""The link list against the runs: the documents the list holds that no run stored.

The check finds changes in the portal's listings (diff.py). A list built with lom.timeline: all also holds documents
the listings never show: amendments known only from an act's timeline, and the commencement orders on an amending
act's page. After a list rebuild, --list compares that list with every run and puts the unstored rows on the delta
list (decision 17; NOTES.md 2.3: 103 such documents on 2026-09-15). No request is sent for this.

A row whose address no run stored but whose title a run stored from another host (a seed fetched from an agency's
copy instead of lom's) is reported `stored_elsewhere` and not fetched; the same title on the same host is another
document (a Malay copy beside the English one) and is fetched.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from ..catalogue import cfg_fingerprint, read_documents
from .baseline import Baseline
from .diff import Change


def _norm(text: Optional[str]) -> str:
    return " ".join(str(text or "").split()).casefold()


def _host(url: Optional[str]) -> str:
    return (urlparse(url or "").hostname or "").lower()


def list_vs_runs(list_path: str | Path, cfg: dict, baseline: Optional[Baseline]) -> tuple[list[dict], list[Change], dict]:
    """(rows to fetch, one Change per list row no run stored, a summary). Refuses a list built from another registry:
    its rows would not match the seeds and title rule the crawl checks against."""
    rows, meta = read_documents(list_path)
    fingerprint = cfg_fingerprint(cfg)
    if meta.get("cfg_sha256") and meta["cfg_sha256"] != fingerprint:
        raise ValueError(f"link list {list_path} was built from a different registry (fingerprint "
                         f"{meta['cfg_sha256'][:8]}… against {fingerprint[:8]}…): rebuild it with scraper.catalogue "
                         f"before comparing it with the runs")
    stored = baseline.stored if baseline else {}
    dup = baseline.duplicates if baseline else set()
    by_title = {}
    for d in stored.values():
        if d.law_name_guess:
            by_title.setdefault(_norm(d.law_name_guess), d)
    to_fetch: list[dict] = []
    changes: list[Change] = []
    for row in rows:
        url = row.get("url")
        if not url or url in stored or url in dup:
            continue
        meta_row = row.get("contract_meta") or {}
        portal_id = str(meta_row.get("portal_id") or row.get("law_number_guess") or url)
        now = {"document_url": url, "document_kind": meta_row.get("document_kind"),
               "discovery_path": meta_row.get("discovery_path"),
               "principal_law_number": meta_row.get("principal_law_number"),
               "list_generated_at": meta.get("generated_at")}
        elsewhere = by_title.get(_norm(row.get("law_name_guess")))
        if elsewhere is not None and _host(elsewhere.url) == _host(url):
            elsewhere = None                      # the same title on the same host is another document (a Malay copy)
        if elsewhere is not None:
            changes.append(Change("list", "stored_elsewhere", portal_id, row.get("law_number_guess") or "",
                                  row.get("law_name_guess"),
                                  [f"the same title is stored from another address ({elsewhere.url})"], now,
                                  {"document_url": elsewhere.url, "run": elsewhere.run, "doc_id": elsewhere.doc_id},
                                  crawl=False, note="not fetched: a copy under another address exists"))
            continue
        changes.append(Change("list", "not_in_runs", portal_id, row.get("law_number_guess") or "",
                              row.get("law_name_guess"),
                              [f"in the link list built {meta.get('generated_at') or 'undated'}, stored by no run"],
                              now, {}, crawl=True, url=url))
        to_fetch.append(row)
    summary = {"list": str(list_path), "generated_at": meta.get("generated_at"), "cfg_sha256": meta.get("cfg_sha256"),
               "rows": len(rows), "stored": sum(1 for r in rows if r.get("url") in stored),
               "duplicates": sum(1 for r in rows if r.get("url") in dup),
               "not_in_runs": len(to_fetch), "stored_elsewhere": len(changes) - len(to_fetch)}
    return to_fetch, changes, summary
