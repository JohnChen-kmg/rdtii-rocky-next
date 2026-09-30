"""Command line: check Singapore Statutes Online for changes since a date and write the delta list to crawl.

    python -m p1_scrape.adapters.sg_sso.updates --outputs <workspace>/outputs/SG \\
        [--baseline <run folder>] [--since YYYY-MM-DD] [--out <run folder>] \\
        [--registry sources.yaml --seeds links/seed_laws.yaml] [--pillars 6,7] \\
        [--max-timelines 60] [--no-seed-regulations]

The date is the day the baseline's list was built (the newest run under --outputs, or --baseline), unless --since
gives one. Without --out the run folder is <outputs>/SG_ws_<since>_to_<today>[_n]. It prints the crawl command.

Exit 0 also when nothing changed; exit 2 when the portal could not be read at all, and nothing is written then.
"""
from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path
from typing import Optional

from ...my_gazette.records import LomThrottled
from ..adapter import SgSsoAdapter, SsoUnavailable
from ..catalogue import _load_cfg, write
from . import build_delta, check, load_baseline, relevant_codes, write_changes


def new_run_dir(outputs: Path, today: Optional[str] = None, since: Optional[str] = None) -> Path:
    stamp = today or date.today().isoformat()
    name = f"SG_ws_{since}_to_{stamp}" if since else f"SG_ws_{stamp}"
    if not (outputs / name).exists():
        return outputs / name
    n = 2
    while (outputs / f"{name}_{n}").exists():
        n += 1
    return outputs / f"{name}_{n}"


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--outputs", help="the country's run folders, outputs/SG")
    ap.add_argument("--baseline", help="one run folder to compare with, instead of the newest under --outputs")
    ap.add_argument("--since", help="check from this date (default: the day the baseline's list was built)")
    ap.add_argument("--out", help="the run folder to write")
    ap.add_argument("--registry", help="sources.yaml")
    ap.add_argument("--seeds", help="links/seed_laws.yaml")
    ap.add_argument("--pillars", default="6,7")
    ap.add_argument("--max-timelines", type=int, default=60,
                    help="act timelines one check may read; the rest are reported as not checked")
    ap.add_argument("--no-seed-regulations", action="store_true",
                    help="do not read the seed acts' regulations tabs (about one request per seed act)")
    a = ap.parse_args(argv)
    if not a.outputs and not a.baseline:
        ap.error("--outputs or --baseline is needed")
    if not a.outputs and not a.out:
        # --baseline says what to compare with, not where to write: without this the run folder landed in the
        # current directory, outside outputs/SG (audit, 2026-09-19)
        ap.error("--out is needed when there is no --outputs folder to put the run in")
    pillars = [int(p) for p in str(a.pillars).split(",") if p.strip()]

    baseline = load_baseline(outputs_dir=a.outputs, run=a.baseline)
    if baseline.run is not None:
        print(f"[updates] SG: baseline {baseline.run.name}"
              + (f", list built {baseline.generated_at}" if baseline.generated_at else "")
              + f"; {len(baseline.current)} current act(s) with their version dates, "
                f"{len(baseline.stored)} document(s) stored across {len(baseline.runs_read)} run(s)", flush=True)
    else:
        baseline = None
    since = a.since or (baseline.since if baseline else None)
    if not since:
        print("[updates] SG: no date to check from; pass --since or point --outputs at a run with a list",
              file=sys.stderr, flush=True)
        return 2

    adapter = SgSsoAdapter(_load_cfg(a.registry, a.seeds))
    # the stage's settings, as the list build and the crawl use them: the configured User-Agent with its contact
    # address and REQUEST_DELAY_MS. Until 2026-09-17 the check passed None and sent the adapter's bare fallback
    # User-Agent instead, and the portal refused every one of its listing requests (../NOTES.md 1.3)
    from ...my_gazette.catalogue import _SettingsOnly
    client = adapter._get_client(_SettingsOnly())
    print(f"[updates] SG: identified as {client.user_agent!r}, {client.delay:g} s between requests", flush=True)
    try:
        changes = check(adapter, client, baseline, since, pillars, max_timelines=a.max_timelines,
                        seed_regulations=not a.no_seed_regulations)
    except (LomThrottled, SsoUnavailable) as e:
        print(f"[updates] SG: the portal could not be read: {e}; nothing written", file=sys.stderr, flush=True)
        return 2

    relevant = relevant_codes(adapter, adapter.listed.get("current", []))
    run_dir = Path(a.out) if a.out else new_run_dir(Path(a.outputs), since=since)
    run_dir.mkdir(parents=True, exist_ok=True)
    result = build_delta(adapter, changes, baseline, pillars, relevant, log=client.log)
    registry_files = {n: p for n, p in (("sources.yaml", a.registry), ("seed_laws.yaml", a.seeds)) if p}
    paths = write(result, run_dir / "links_used", registry_files or None)
    paths.update(write_changes(run_dir, changes, {
        "baseline_run": baseline.run.name if (baseline and baseline.run) else None,
        "baseline_generated_at": baseline.generated_at if baseline else None,
        "max_timelines": a.max_timelines, "seed_regulations": not a.no_seed_regulations}))

    counts = changes.counts()
    n = len(result["documents"])
    print(f"[updates] SG: since {since}: {counts}; {changes.requests} request(s), {changes.timelines_read} timeline(s) "
          f"read, no document fetched", flush=True)
    for c in changes.changes:
        if c.change != "regenerated":
            extra = (f" in force {c.in_force_from} by {c.amended_by}" if c.change.startswith("amended") and c.amended_by
                     else f" repealed {c.repeal_date}" if c.change == "repealed" else "")
            print(f"[updates]   {c.change:22} {c.portal_id:18} {(c.law_name or '')[:50]}{extra}", flush=True)
    for note in changes.notes:
        print(f"[updates] note: {note}", flush=True)
    print(f"[updates] SG: {n} document(s) to crawl -> {paths['documents.jsonl']}; {paths['changes.md']}", flush=True)
    if n:
        print(f"[updates] next: REQUEST_DELAY_MS=10000 SSO_FRONTIER=links_file SSO_LINKS_FILE={paths['documents.jsonl']} "
              f"python scrape.py --economy SG --scope all --out {run_dir}", flush=True)
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
        from ...my_gazette.watchlist import remind
    except Exception:  # noqa: BLE001 - a missing helper must not stop the check
        print("[updates] !! watch-list helper missing: this check cannot say which sources it does not see",
              flush=True)
        return
    remind(os.path.join(os.path.dirname(os.path.abspath(__file__)), "watchlist.tsv"), "SG", when)


if __name__ == "__main__":
    _remind("before this check")
    _code = main()
    _remind("after this check")
    sys.exit(_code)
