"""Command line: check Laws of Malaysia for changes since the last run and write the delta list to crawl.

    python -m p1_scrape.adapters.my_gazette.updates --outputs <workspace>/outputs/MY \\
        [--baseline <run folder>] [--since YYYY-MM-DD] [--out <run folder>] \\
        [--registry sources.yaml --seeds links/seed_laws.yaml] [--pillars 6,7] [--verify-stored N] \\
        [--list links/documents.jsonl]

Reads the portal's listings (no document), compares them with the baseline (the newest run under --outputs, or
--baseline), and writes <run folder>/links_used/ (documents.jsonl …), changes.json and changes.md. With --list it
also compares a link list built by scraper.catalogue with the runs and fetches every document the list holds that
no run stored (an amendment known only from a timeline, a commencement order): the way to catch up after a list
rebuild with lom.timeline: all. Without --out the
run folder is <outputs>/MY_ws_<since>_to_<today>[_n], the period the check covers. It then prints the crawl
command. Exit 0 also when nothing changed; exit 2 when lom could not be read (nothing is written then).
"""
from __future__ import annotations

import argparse
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Optional

from ..catalogue import _SettingsOnly, _load_cfg, write
from . import build_delta, check, load_baseline, verify_stored, write_changes
from .baseline import RUN_DIR
from .listcheck import list_vs_runs


def refetch_row(baseline, url: str) -> dict:
    """The link row of a stored document that answered 200 to a conditional HEAD, or a row made from the manifest
    when no run's list holds one."""
    row = baseline.documents.get(url)
    if row is not None:
        return row
    d = baseline.stored[url]
    return {"url": url, "economy": "MY", "law_name_guess": d.law_name_guess or url.rsplit("/", 1)[-1],
            "law_number_guess": d.law_number_guess,
            "contract_meta": {"portal": "my-lom", "discovery_path": "delta", "document_kind": None,
                              "portal_id": None, "language": None, "language_source": None,
                              "legal_status": "unknown", "status_source": None, "crawl_flags": [],
                              "review_flags": ["no_link_row_in_baseline"]}}


def new_run_dir(outputs: Path, economy: str = "MY", today: Optional[str] = None,
                since: Optional[str] = None) -> Path:
    """The next free run folder: <CC>_ws_<today> for a crawl, <CC>_ws_<since>_to_<today> for an update check
    (the period it covers), with _2, _3 when the name is taken."""
    stamp = today or date.today().isoformat()
    name = f"{economy}_ws_{since}_to_{stamp}" if since else f"{economy}_ws_{stamp}"
    base = outputs / name
    if not base.exists():
        return base
    n = 2
    while (outputs / f"{name}_{n}").exists():
        n += 1
    return outputs / f"{name}_{n}"


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--outputs", help="the country's run folders, outputs/MY (the newest is the baseline)")
    ap.add_argument("--baseline", help="one run folder to compare with, instead of the newest under --outputs")
    ap.add_argument("--since", help="ISO date; default: the day the baseline run started")
    ap.add_argument("--out", help="the new run folder; default: <outputs>/MY_ws_<since>_to_<today>")
    ap.add_argument("--registry", help="sources.yaml to read instead of the stage's sources_my.yaml")
    ap.add_argument("--seeds", help="a YAML file with seed_laws, merged over the registry's")
    ap.add_argument("--pillars", default="6,7")
    ap.add_argument("--verify-stored", type=int, default=None, metavar="N",
                    help="also send a conditional HEAD for the N newest stored lom files (default: updates.verify_stored, 0)")
    ap.add_argument("--no-baseline", action="store_true", help="date mode: compare with --since only")
    ap.add_argument("--list", metavar="DOCUMENTS_JSONL",
                    help="also compare this link list (links/documents.jsonl, built by scraper.catalogue from the same "
                         "registry) with the runs, and fetch what the list holds that no run stored")
    args = ap.parse_args(argv)
    cfg = _load_cfg(args.registry, args.seeds)
    pillars = [int(x) for x in args.pillars.split(",") if x.strip()]
    if args.since and not RUN_DIR.match(f"MY_ws_{args.since}"):
        ap.error("--since must be YYYY-MM-DD")

    baseline = None
    if not args.no_baseline and (args.baseline or args.outputs):
        baseline = load_baseline(args.outputs, run=args.baseline)
    since = args.since or (baseline.since_date if baseline else None)
    if since is None:
        ap.error("give --outputs or --baseline (a run to compare with), or --since YYYY-MM-DD")
    list_rows, list_changes, list_meta = [], [], None
    if args.list:
        if baseline is None:
            ap.error("--list needs runs to compare with: give --outputs or --baseline")
        try:                                             # before any request: a stale list is refused first
            list_rows, list_changes, list_meta = list_vs_runs(args.list, cfg, baseline)
        except (FileNotFoundError, ValueError) as e:
            print(f"[updates] MY: {e}; nothing written", flush=True)
            return 2
    if args.out:
        run_dir = Path(args.out)
        if (run_dir / "links_used" / "documents.jsonl").exists() or (run_dir / "manifest.jsonl").exists():
            print(f"[updates] MY: {run_dir} already holds a check or a crawl; a check never writes into an earlier "
                  f"run (outputs/README.md). Give a new --out, or omit it", flush=True)
            return 2
    elif args.outputs:
        run_dir = new_run_dir(Path(args.outputs), since=since)
    else:
        ap.error("--out is needed when there is no --outputs folder to put the run in")

    fetcher = _SettingsOnly()
    print(f"[updates] MY: checking lom since {since}"
          + (f" against {baseline.name} ({len(baseline.stored)} stored documents, listing state from "
             f"{baseline.state_run.name if baseline.state_run else 'no run'})" if baseline else " (date mode)"),
          flush=True)
    try:
        adapter, changes, instruments, sub_meta = check(cfg, baseline, since, fetcher=fetcher)
    except Exception as e:  # noqa: BLE001 — lom unreadable, a network error, a format change: nothing is written
        print(f"[updates] MY: lom could not be read, nothing written ({type(e).__name__}: {e})", flush=True)
        return 2
    client = adapter._client
    changes.listed.extend(list_changes)
    limit = args.verify_stored if args.verify_stored is not None else int((cfg.get("updates") or {}).get("verify_stored") or 0)
    verification = verify_stored(client, adapter.host, baseline, limit) if baseline and limit else []
    refetch = [refetch_row(baseline, v["url"]) for v in verification if v["changed"]]
    result = build_delta(adapter, client, changes, baseline, since, pillars, subsidiary_meta=sub_meta, refetch=refetch,
                         list_rows=list_rows, list_meta=list_meta)
    adapter._finish(client)
    files = {k: v for k, v in (("registry", args.registry), ("seeds", args.seeds)) if v}
    paths = write(result, run_dir / "links_used", registry_files=files)
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    extra = {"economy": "MY", "since": since, "baseline_runs": [r.name for r in baseline.runs] if baseline else [],
             "requests": len(client.log), "listing_counts": adapter.listing_counts, "subsidiary_listing": sub_meta,
             "robots_record": adapter.robots_record, "generated_at": generated, "link_list": list_meta}
    paths.update(write_changes(run_dir, changes, verification, extra))

    s = changes.summary()
    n = len(result["documents"])
    print(f"[updates] MY: {s['total']} change(s) since {since}: {s['by_change']}; {len(client.log)} requests, "
          f"no document fetched", flush=True)
    for ch in changes.all():
        if ch.kind == "list":
            continue                                     # summarised below, not one line per document
        if ch.crawl or ch.change in ("gone", "status_changed", "new_version", "stored_file_changed"):
            print(f"[updates]   {ch.kind:10} {ch.change:22} {ch.law_number}: {(ch.law_name or '')[:60]}"
                  f" ({'; '.join(ch.reasons)}){' -> fetch' if ch.crawl else ''}", flush=True)
    if list_meta is not None:
        print(f"[updates] MY: link list {list_meta['list']} (built {list_meta['generated_at']}): {list_meta['rows']} rows, "
              f"{list_meta['not_in_runs']} document(s) no run stored -> fetch, {list_meta['stored_elsewhere']} stored "
              f"under another address", flush=True)
    if verification:
        print(f"[updates] MY: {len(verification)} stored file(s) checked: "
              f"{sum(1 for v in verification if v['unchanged'])} unchanged, "
              f"{sum(1 for v in verification if v['changed'])} changed", flush=True)
    for note in result["meta"]["notes"]:
        print(f"[updates] note: {note}", flush=True)
    print(f"[updates] MY: {n} document(s) to crawl -> {paths['documents.jsonl']}; {paths['changes.md']}", flush=True)
    if n:
        print(f"[updates] next: LOM_FRONTIER=links_file LOM_LINKS_FILE={paths['documents.jsonl']} "
              f"python scrape.py --economy MY --scope all --out {run_dir}", flush=True)
    else:
        print("[updates] next: nothing to crawl; keep the run folder as the record of this check", flush=True)
    return 0


def _remind(when: str) -> None:
    """Say which sources this check cannot see, before it runs and after (the developer's rule of 2026-09-21).

    The list is `watchlist.tsv` beside this file. The helper never raises; if it cannot even be imported, the
    check still runs and says so. Hand-back: copy `watchlist.tsv` with this package, not only its `*.py`.
    """
    import os

    try:
        from ..watchlist import remind
    except Exception:  # noqa: BLE001 - a missing helper must not stop the check
        print("[updates] !! watch-list helper missing: this check cannot say which sources it does not see",
              flush=True)
        return
    remind(os.path.join(os.path.dirname(os.path.abspath(__file__)), "watchlist.tsv"), "MY", when)


if __name__ == "__main__":
    _remind("before this check")
    _code = main()
    _remind("after this check")
    sys.exit(_code)
