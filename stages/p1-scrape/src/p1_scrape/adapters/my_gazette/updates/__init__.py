"""Malaysia — what changed on Laws of Malaysia since the last run, and the delta list to crawl for it.

Two steps, like the scraper (NOTES.md section 2.6):

  1. check   read the portal's listings (8 paced requests with the registry's settings, more when a P.U. series
             needs more than one page or an act changed; no document fetched) and compare them with the last run
             under outputs/MY/ (or with a date), writing changes.json;
  2. delta   write links_used/ (documents.jsonl, laws.csv, catalogue_meta.json, discovery_log.jsonl) for the changed
             and new laws only, in the format the crawl replays. With --list, also for every document a link list
             built by scraper.catalogue holds that no run stored (listcheck.py: the amendments and commencement
             orders only a timeline shows, after a rebuild with lom.timeline: all). The crawl then fetches only those:

    python -m p1_scrape.adapters.my_gazette.updates --outputs <workspace>/outputs/MY [--since YYYY-MM-DD] \\
        --registry sources.yaml --seeds links/seed_laws.yaml [--out <run folder>]
    LOM_FRONTIER=links_file LOM_LINKS_FILE=<run folder>/links_used/documents.jsonl \\
        python scrape.py --economy MY --scope all --out <run folder>

The run folder sits beside the crawls under outputs/MY/ and is named for the period the check covers,
<CC>_ws_<since>_to_<date> (outputs/MY/MY_ws_2026-09-14_to_2026-09-14 is the first).

Where the portal shows changes (examined live on 2026-09-13 and 2026-09-14):
- **Principal acts.** No upload date is published. An act's version identity is the file the updated listing gives
  for it (its path carries a project id) and the "As At" date. A new consolidation is a different file, usually with
  a later date. The listing is read whole (1 GET and 2 POSTs of 500 records; 885 records on 2026-09-14) and compared,
  act by act, with the last run's laws.csv. Between 2026-09-13 and 2026-09-14 nothing changed except 5 records dropped
  (406 (Revised), 91 (revised), 49/1965, 31/1961, 26/1947: suffixed numbers offering the files of Acts 406, 91, 49, 31
  and 26, which the 2026-09-13 run had counted as acts of their own, 890).
- **Amending acts.** The amendment listing carries every act from A1392 (2 June 2011) with publication, assent and
  commencement dates; A-numbers rise with time. New = not in the last run's listing (in date mode: published after
  the date). A remark can change later ("NOT YET IN FORCE" gains a date): that is a change to record, not a file to fetch.
- **Subsidiary legislation.** subsid.php?type=pua and type=pub list every P.U. (A) (7,306 on 2026-09-14) and P.U. (B)
  (9,150) with a publication date, the parent act (ACT_NO), a status (the page maps PRINCIPAL, AMENDMENT, CORRIGENDUM,
  CANCEL or REVOCATION, REPRINT and REPRINT ONLINE; the pages read on 2026-09-14 showed PRINCIPAL, AMENDMENT, PINDAAN,
  CORRIGENDUM and CANCEL) and the file, and the server sorts them newest first (json-subsid-2024.php, form type=pua|pub).
  New since a date = the first pages, read until a page is older than the date less updates.subsidiary_lookback_days
  (120: an instrument can be uploaded months after its publication date), minus what a run already stored.
- **The home page's "What's New" panel** lists what was published on each of the last seven days. Its "Principal Act"
  and "Amendment Act" boxes show the three newest acts (884, 883, 882 and A1793, A1792, A1791 on 2026-09-14); its
  "List of P.U. (A)" and "List of P.U. (B)" boxes show three untitled numbers that are not the newest three (P.U. (A)
  262, 253, 324/2026; P.U. (B) 98.1998, 335/2026, 334/2026). It is not read: the listings cover any window, and its
  "See All" link (kuda.php) is commented out.
- **Per file, after the fact.** lom's ETag and Last-Modified are stable for a URL in almost every case: of the 560 files
  refetched at the same path between July and September 2026, 559 were byte-identical, 557 of those kept both
  validators and 2 (Acts 719 and 866) were re-uploaded unchanged with new ones; the one file whose bytes changed
  behind its path (Act 869, uploaded 21 August 2026, as-at date unchanged) changed its validators too. A conditional
  GET answers 304 with no body (checked 2026-09-14 21:47 UTC on the stored PDPA file), and so does the conditional
  HEAD that --verify-stored sends (22:28 UTC). Last-Modified is the upload time, on or after the as-at date for 732
  of 733 dated acts (the exception is Act 548). No listing exposes it, so it cannot find changes; it can confirm that
  a stored file is unchanged, one HEAD request per file (--verify-stored N), never following a redirect.
- **Not a signal:** filenames; the order of records; and, for the files uploaded on 2023-11-06, their Last-Modified,
  which is that day's bulk-upload time (516 of the 1,297 lom files stored on 2026-09-14; 581 of Round 1's 856).
- **Commencement orders** stay on the amending act's own detail page. Being P.U. (B) notices they should appear in
  the P.U. (B) listing too (none was on the page read on 2026-09-14), so a P.U. (B) that an amending act's remark
  cites is fetched from the listing when new.
- robots.txt answered HTTP 500 on every read; the registry's lom.robots_5xx governs (POLICY.md 5.4, decision 9).

What a check does not do: it never fetches a document; it refuses a run folder that already holds a check or a
crawl; and against a run it never guesses (date mode, with no run or --no-baseline, flags principal acts by as-at
date and says on each row that this is approximate). An act whose file and date the listing still gives as before is
reported unchanged even if the portal replaced the bytes behind the same path; --verify-stored is the check for that.
"""
from __future__ import annotations

from typing import Optional

from ..adapter import MyGazetteAdapter
from ..records import LomUnavailable
from .baseline import Baseline, list_runs, load as load_baseline
from .delta import build_delta, verify_stored, write_changes
from .diff import Change, Changes, compare
from .listcheck import list_vs_runs
from .listings import SubsidiaryInstrument, fetch_all_subsidiary, parse_subsidiary

__all__ = ["Baseline", "Change", "Changes", "SubsidiaryInstrument", "build_delta", "check", "compare",
           "fetch_all_subsidiary", "find_changes", "list_runs", "list_vs_runs", "load_baseline", "parse_subsidiary",
           "verify_stored", "write_changes"]


def check(cfg: dict, baseline: Optional[Baseline], since: Optional[str], fetcher=None, client=None,
          today: Optional[str] = None) -> tuple[MyGazetteAdapter, Changes, list[SubsidiaryInstrument], dict]:
    """Read the portal once and compare it with the baseline (or the date). Raises when lom cannot be read: a
    check that did not see the portal reports nothing rather than "no change"."""
    if since is None and baseline is not None:
        since = baseline.since_date
    if since is None:
        raise ValueError("an update check needs a baseline run or --since YYYY-MM-DD")
    adapter = MyGazetteAdapter(cfg, client=client, today=today)
    adapter._frontier_override = "discover"          # a check always reads the portal, whatever LOM_FRONTIER says
    adapter._check_settings()
    lom = adapter._get_client(fetcher)
    adapter._open_lom(lom)                           # robots.txt, then both listings
    short = [f"{k}: {v.get('records')} of {v.get('total')}" for k, v in adapter.listing_counts.items()
             if v.get("total") is not None and (v.get("records") or 0) < v["total"]]
    if short:                                        # a partial listing would report the missing acts as gone
        raise LomUnavailable(f"lom served an incomplete listing ({'; '.join(short)}); nothing compared")
    instruments, sub_meta = fetch_all_subsidiary(lom, adapter.root, cfg.get("updates") or {}, since,
                                                 key=adapter._listing_key)
    changes = compare(adapter, baseline, since, instruments)
    return adapter, changes, instruments, sub_meta


def find_changes(cfg: dict, since: str, fetcher=None, baseline: Optional[Baseline] = None) -> list[dict]:
    """The shape countries/_template/updates/__init__.py asks for: one dict per law the portal shows as new or changed
    since `since` (ISO date). Raw portal values only; `url` is where the change was seen."""
    adapter, changes, _instruments, _meta = check(cfg, baseline, since, fetcher=fetcher)
    pages = {"principal": adapter.listings["updated"][0], "amending": adapter.listings["amendment"][0]}
    out = []
    for ch in changes.all():
        seen = pages.get(ch.kind) or (cfg.get("updates") or {}).get("subsidiary_listings", {}).get(
            ch.now.get("kind", ""), {}).get("page") or f"subsid.php?type={ch.now.get('kind', 'pua')}"
        out.append({"portal_id": ch.portal_id, "law_name": ch.law_name,
                    "version_as_at": ch.now.get("as_at") or ch.now.get("publication_date"),
                    "version_id": ch.now.get("document_url") or ch.now.get("url"),
                    "change": _template_change(ch), "url": f"{adapter.root}/{seen}", "detail": ch.as_dict()})
    return out


def _template_change(ch: Change) -> str:
    if ch.change in ("new_act", "new_amending_act", "new_instrument", "new_or_updated"):
        return "new"
    if ch.change == "gone":
        return "gone"
    if (ch.now.get("status_marker") or "").lower().startswith(("(repealed", "(dimansuhkan", "(superseded", "(diganti")):
        return "repealed"
    return "amended"
