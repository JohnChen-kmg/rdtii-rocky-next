#!/usr/bin/env python3
"""Crawl progress tracker / stall + throttle detector.

Watches a running crawl's manifest.jsonl and crawl_log.jsonl and EXITS (so the harness
re-engages the operator) when:
  - progress STALLS: no new manifest rows for --stall-seconds, or
  - a THROTTLE burst appears: the recent crawl_log is mostly skipped/failed outcomes.

It prints a progress line each poll so interim state is visible. Non-invasive (read-only).

    python tools/crawl_tracker.py --out handoff1_v2 --stall-seconds 480
"""
from __future__ import annotations

import argparse
import json
import time
from collections import Counter
from pathlib import Path


def _rows(path: Path) -> int:
    try:
        with path.open(encoding="utf-8") as fh:
            return sum(1 for line in fh if line.strip())
    except FileNotFoundError:
        return 0


def _recent_outcomes(log: Path, n: int = 50) -> dict:
    try:
        with log.open(encoding="utf-8") as fh:
            tail = [line for line in fh if line.strip()][-n:]
    except FileNotFoundError:
        return {}
    c: Counter = Counter()
    for line in tail:
        try:
            c[json.loads(line).get("outcome", "?")] += 1
        except json.JSONDecodeError:
            pass
    return dict(c)


def main() -> int:
    ap = argparse.ArgumentParser(description="Crawl stall/throttle tracker.")
    ap.add_argument("--out", required=True, help="crawl output dir (holds manifest.jsonl)")
    ap.add_argument("--stall-seconds", type=int, default=480, help="report a stall after this idle time")
    ap.add_argument("--poll-seconds", type=int, default=60)
    ap.add_argument("--throttle-window", type=int, default=50, help="crawl_log tail size to scan")
    ap.add_argument("--throttle-ratio", type=float, default=0.7,
                    help="if >=this fraction of the recent window is skipped/failed while not growing, flag it")
    ap.add_argument("--max-hours", type=float, default=6.0)
    a = ap.parse_args()

    out = Path(a.out)
    manifest, log = out / "manifest.jsonl", out / "crawl_log.jsonl"
    last, last_change, start = _rows(manifest), time.monotonic(), time.monotonic()
    print(f"[tracker] watching {manifest} (stall>{a.stall_seconds}s, poll {a.poll_seconds}s)", flush=True)

    while True:
        time.sleep(a.poll_seconds)
        now = time.monotonic()
        count = _rows(manifest)
        elapsed = int(now - start)
        if count != last:
            print(f"[tracker] {count} rows (+{count - last}) @ {elapsed}s", flush=True)
            last, last_change = count, now
            continue

        idle = int(now - last_change)
        mix = _recent_outcomes(log, a.throttle_window)
        bad = mix.get("skipped", 0) + mix.get("failed", 0) + mix.get("error", 0)
        total = sum(mix.values()) or 1
        print(f"[tracker] no new rows for {idle}s at {count}; recent outcomes={mix}", flush=True)

        if idle >= a.stall_seconds:
            print(f"[tracker] STALL: {count} rows, no growth for {idle}s. recent={mix}", flush=True)
            print("[tracker] EXIT -> operator should re-engage (crawl may be hung, throttled, or done).", flush=True)
            return 2
        if bad / total >= a.throttle_ratio and idle >= a.poll_seconds * 2:
            print(f"[tracker] THROTTLE SUSPECTED: {bad}/{total} recent fetches skipped/failed while stalled.", flush=True)
            print("[tracker] EXIT -> operator should re-engage (portal likely throttling).", flush=True)
            return 3
        if now - start > a.max_hours * 3600:
            print(f"[tracker] max watch time ({a.max_hours}h) reached at {count} rows; exiting.", flush=True)
            return 0


if __name__ == "__main__":
    raise SystemExit(main())
