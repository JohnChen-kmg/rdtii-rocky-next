"""Command line: ask the Federal Register what changed since the last run and write the delta list to crawl.

    python -m p1_scrape.adapters.au_legislation.updates --outputs <workspace>/outputs/AU \\
        [--baseline <run folder>] [--since YYYY-MM-DD] [--out <run folder>] \\
        [--registry sources.yaml --seeds links/seed_laws.yaml] [--pillars 6,7] [--prefixes C,F]

Reads the register's API (no document, no `www` page beyond `robots.txt`), compares what it returns with the
baseline (the newest run under `--outputs`, or `--baseline`), and writes `<run folder>/links_used/`
(documents.jsonl …), `changes.json` and `changes.md`. Without `--out` the run folder is
`<outputs>/AU_ws_<since>_to_<today>[_n]`, the period the check covers. It then prints the crawl command.

Exit 0 also when nothing changed; exit 2 when the register could not be read, and nothing is written then.
"""
from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path
from typing import Optional

from ..adapter import AuLegislationAdapter, RegisterUnavailable
from ..catalogue import _load_cfg, write
from . import build_delta, check, load_baseline, write_changes
from .baseline import RUN_DIR


def new_run_dir(outputs: Path, economy: str = "AU", today: Optional[str] = None,
                since: Optional[str] = None) -> Path:
    """The next free run folder: `<CC>_ws_<since>_to_<today>` for an update check, with `_2`, `_3` when taken."""
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
    ap.add_argument("--outputs", help="the country's run folders, outputs/AU")
    ap.add_argument("--baseline", help="one run folder to compare with, instead of the newest under --outputs")
    ap.add_argument("--since", help="check from this date (default: the day the baseline's list was built)")
    ap.add_argument("--out", help="the run folder to write (default: <outputs>/AU_ws_<since>_to_<today>)")
    ap.add_argument("--registry", help="sources.yaml")
    ap.add_argument("--seeds", help="links/seed_laws.yaml")
    ap.add_argument("--pillars", default="6,7")
    ap.add_argument("--prefixes", default="C,F", help="title id prefixes to query: C acts, F instruments")
    a = ap.parse_args(argv)

    if not a.outputs and not a.baseline:
        ap.error("--outputs or --baseline is needed")
    if not a.outputs and not a.out:
        # --baseline says what to compare with, not where to write: without this the run folder landed in the
        # current directory, outside outputs/AU (audit, 2026-09-19)
        ap.error("--out is needed when there is no --outputs folder to put the run in")
    pillars = [int(p) for p in str(a.pillars).split(",") if p.strip()]
    prefixes = tuple(p.strip().upper() for p in str(a.prefixes).split(",") if p.strip())

    cfg = _load_cfg(a.registry, a.seeds)
    adapter = AuLegislationAdapter(cfg)
    api, www = adapter._clients(None)

    baseline = load_baseline(outputs_dir=a.outputs, run=a.baseline) if (a.outputs or a.baseline) else None
    if baseline is not None and baseline.run is not None:
        print(f"[updates] AU: baseline {baseline.run.name}"
              + (f", list built {baseline.generated_at}" if baseline.generated_at else "")
              + f"; {len(baseline.listed)} title(s) listed, {len(baseline.stored)} document(s) stored "
                f"across {len(baseline.runs_read)} run(s)", flush=True)
    since = a.since or (baseline.since if baseline else None)
    if not since:
        print("[updates] AU: no date to check from; pass --since or point --outputs at a run with a list",
              file=sys.stderr, flush=True)
        return 2

    try:
        adapter._check_robots(api, www)
        changes, found = check(adapter, api, baseline, since=since, prefixes=prefixes,
                               root=adapter._api_root())
    except RegisterUnavailable as e:
        print(f"[updates] AU: the register could not be read: {e}; nothing written", file=sys.stderr, flush=True)
        return 2

    run_dir = Path(a.out) if a.out else new_run_dir(Path(a.outputs), since=since)
    run_dir.mkdir(parents=True, exist_ok=True)
    result = build_delta(adapter, changes, found, pillars, api_log=api.log)
    result["meta"]["update"]["baseline_run"] = baseline.run.name if (baseline and baseline.run) else None
    registry_files = {name: path for name, path in (("sources.yaml", a.registry), ("seed_laws.yaml", a.seeds)) if path}
    paths = write(result, run_dir / "links_used", registry_files or None)
    paths.update(write_changes(run_dir, changes,
                               {"baseline_run": baseline.run.name if (baseline and baseline.run) else None,
                                "baseline_generated_at": baseline.generated_at if baseline else None,
                                "runs_read": baseline.runs_read if baseline else []}))

    counts = changes.counts()
    n = len(result["documents"])
    print(f"[updates] AU: {sum(counts.values())} title(s) answered the query since {since}: {counts}; "
          f"{changes.requests} API request(s), no document fetched", flush=True)
    for ch in changes.changes:
        if ch.change != "unchanged":
            print(f"[updates]   {ch.change:12} {ch.portal_id:12} {(ch.law_name or '')[:52]}"
                  f"  {ch.previous_version_id or '-'} -> {ch.version_id or '-'}", flush=True)
    for note in result["meta"]["notes"]:
        print(f"[updates] note: {note}", flush=True)
    print(f"[updates] AU: {n} document(s) to crawl -> {paths['documents.jsonl']}; {paths['changes.md']}", flush=True)
    if n:
        print(f"[updates] next: REQUEST_DELAY_MS=10000 REGISTER_FRONTIER=links_file "
              f"REGISTER_LINKS_FILE={paths['documents.jsonl']} "
              f"python scrape.py --economy AU --scope all --out {run_dir}", flush=True)
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
    remind(os.path.join(os.path.dirname(os.path.abspath(__file__)), "watchlist.tsv"), "AU", when)


if __name__ == "__main__":
    _remind("before this check")
    _code = main()
    _remind("after this check")
    sys.exit(_code)
