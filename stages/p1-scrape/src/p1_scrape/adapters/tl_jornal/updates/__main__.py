"""Fetch only what the Jornal da República published since the last run.

    python -m p1_scrape.adapters.tl_jornal.updates --outputs <ws>/outputs/TL \\
        [--baseline <run folder>] [--since YYYY-MM-DD] [--out <run folder>] \\
        [--registry sources.yaml --seeds links/seed_laws.yaml]

Reads robots.txt and the six category pages, compares them with the last run's `laws.csv`, writes a delta list
into a new run folder, and prints the crawl command that replays it. Nothing is downloaded here.

Exit 2 and nothing written: the gazette could not be read, there is no date to check from, or `--out` names a
folder that already holds a run.
"""
from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path
from typing import Optional

from ..adapter import JornalUnavailable, TlJornalAdapter
from ..catalogue import _load_cfg, _say_identity, write
from . import build_delta, check, load_baseline, write_changes


def new_run_dir(outputs: Path, today: Optional[str] = None, since: Optional[str] = None) -> Path:
    """`TL_ws_<since>_to_<today>`, `_2`, `_3` when the name is taken. `today` is the machine's date."""
    stamp = today or date.today().isoformat()
    name = f"TL_ws_{since}_to_{stamp}" if since else f"TL_ws_{stamp}"
    if not (outputs / name).exists():
        return outputs / name
    for n in range(2, 50):
        if not (outputs / f"{name}_{n}").exists():
            return outputs / f"{name}_{n}"
    raise RuntimeError(f"{outputs / name} and 48 numbered variants all exist")


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--outputs", help="the country's run folders, outputs/TL")
    ap.add_argument("--baseline", help="one run folder to compare with, instead of the newest under --outputs")
    ap.add_argument("--since", help="check from this date (default: the day the baseline's list was built)")
    ap.add_argument("--out", help="the run folder to write (default: <outputs>/TL_ws_<since>_to_<today>)")
    ap.add_argument("--registry", help="sources.yaml")
    ap.add_argument("--seeds", help="links/seed_laws.yaml")
    ap.add_argument("--pillars", default="6,7")
    a = ap.parse_args(argv)
    if not a.outputs and not a.baseline:
        ap.error("--outputs or --baseline is needed")
    if not a.outputs and not a.out:
        # --baseline says what to compare with, not where to write
        ap.error("--out is needed when there is no --outputs folder to put the run in")
    pillars = [int(p) for p in str(a.pillars).split(",") if p.strip()]

    baseline = load_baseline(outputs_dir=a.outputs, run=a.baseline)
    if baseline.run is not None:
        print(f"[updates] TL: baseline {baseline.run.name}"
              + (f", list built {baseline.generated_at}" if baseline.generated_at else "")
              + f"; {len(baseline.acts)} act(s) listed, {len(baseline.stored)} document(s) stored across "
                f"{len(baseline.runs_read)} run(s)", flush=True)
    else:
        baseline = None
    since = a.since or (baseline.since if baseline else None)
    if not since:
        print("[updates] TL: no date to check from; pass --since or point --outputs at a run with a list",
              file=sys.stderr, flush=True)
        return 2

    from ...my_gazette.catalogue import _SettingsOnly
    adapter = TlJornalAdapter(_load_cfg(a.registry, a.seeds))
    fetcher = _SettingsOnly()
    _say_identity(fetcher)
    client = adapter._get_client(fetcher)
    try:
        changes = check(adapter, client, baseline, since, pillars)
    except JornalUnavailable as e:
        print(f"[updates] TL: the gazette could not be read: {e}; nothing written", file=sys.stderr, flush=True)
        return 2

    run_dir = Path(a.out) if a.out else new_run_dir(Path(a.outputs), since=since)
    if (run_dir / "manifest.csv").exists():
        print(f"[updates] TL: {run_dir} already holds a run; give a new --out", file=sys.stderr, flush=True)
        return 2
    run_dir.mkdir(parents=True, exist_ok=True)
    result = build_delta(adapter, changes, baseline, pillars, log=client.log)
    registry_files = {name: path for name, path in (("sources.yaml", a.registry), ("seed_laws.yaml", a.seeds)) if path}
    paths = write(result, run_dir / "links_used", registry_files or None)
    paths.update(write_changes(run_dir, changes, {
        "baseline_run": baseline.run.name if (baseline and baseline.run) else None,
        "baseline_generated_at": baseline.generated_at if baseline else None}))
    counts = changes.counts()
    print(f"[updates] TL: since {since}: {counts}; {changes.requests} request(s), "
          f"{len(changes.to_fetch)} document(s) to crawl -> {paths['documents.jsonl']}; {paths['changes.md']}",
          flush=True)
    for note in changes.notes:
        print(f"[updates] note: {note}", flush=True)
    if changes.to_fetch:
        print(f"[updates] next: REQUEST_DELAY_MS=10000 JORNAL_FRONTIER=links_file "
              f"JORNAL_LINKS_FILE={paths['documents.jsonl']} "
              f"python scrape.py --economy TL --scope all --out {run_dir}", flush=True)
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
    remind(os.path.join(os.path.dirname(os.path.abspath(__file__)), "watchlist.tsv"), "TL", when)


if __name__ == "__main__":
    _remind("before this check")
    _code = main()
    _remind("after this check")
    raise SystemExit(_code)
