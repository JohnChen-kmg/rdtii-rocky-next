"""URL-liveness pass over every Source URL in the judged CSVs (2026-07-16
follow-up, item 4). Judges click every URL.

Reuses the S8 machinery: HTTP HEAD (GET on 405), redirects followed,
results cached in out/url_cache.json so re-runs are free. Output:
out/urlcheck/submission_urls_<YYYY-MM-DD>.json — one entry per unique URL
with status and the CSV rows that cite it. Exit 1 if any URL is not 2xx/3xx
(after the fix pass, this should be green or explicitly dispositioned).

    python -m src.p3map.output.urlcheck
"""
from __future__ import annotations

import csv
import json
import sys
import time

import httpx

from config.settings import ECONOMIES, SETTINGS

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}


def _emitted_csvs() -> list:
    """Whatever this run actually emitted, narrowed by ECONOMIES when that is set.

    Round 1 hard-coded ("SG", "MY", "AU"): after the hand-off, a China or Lao PDR run would
    have printed "0 unique URLs, 0 not OK" without opening a single filed row.
    """
    sub_dir = SETTINGS.out_dir / "submission"
    paths = sorted(sub_dir.glob("records_??.csv"))
    if ECONOMIES:
        paths = [p for p in paths if p.stem.split("_", 1)[1] in set(ECONOMIES)]
    if not paths:
        raise SystemExit(f"[urlcheck] no records_XX.csv to check in {sub_dir}")
    return paths


def check_url(url: str, cache: dict) -> str:
    if url in cache:
        return cache[url]
    status = "unreachable"
    try:
        r = httpx.head(url, follow_redirects=True, timeout=20, headers=HEADERS)
        if r.status_code in (405, 403, 400):  # some portals reject HEAD
            r = httpx.get(url, follow_redirects=True, timeout=30, headers=HEADERS)
        status = str(r.status_code)
    except Exception as e:  # noqa: BLE001 — judges may be offline; record, don't crash
        status = f"error:{type(e).__name__}"
    cache[url] = status
    return status


def run_urlcheck() -> int:
    cache_path = SETTINGS.out_dir / "url_cache.json"
    cache = (json.loads(cache_path.read_text(encoding="utf-8"))
             if cache_path.exists() else {})

    cites: dict[str, list[str]] = {}
    for p in _emitted_csvs():
        econ = p.stem.split("_", 1)[1]
        with p.open(encoding="utf-8-sig") as f:
            for i, r in enumerate(csv.DictReader(f), start=2):
                u = (r.get("Source URL") or "").strip()
                ref = f"{econ}:{r['Indicator ID']}:row{i}"
                cites.setdefault(u, []).append(ref)

    results = []
    bad = 0
    for u, refs in sorted(cites.items()):
        if not u.startswith("http"):  # documented placeholders (hold-out only)
            results.append({"url": u, "status": "placeholder", "rows": refs})
            continue
        st = check_url(u, cache)
        ok = st.startswith(("2", "3"))
        bad += 0 if ok else 1
        results.append({"url": u, "status": st, "ok": ok, "rows": refs})

    out_dir = SETTINGS.out_dir / "urlcheck"
    out_dir.mkdir(parents=True, exist_ok=True)
    date = time.strftime("%Y-%m-%d")
    out = out_dir / f"submission_urls_{date}.json"
    out.write_text(json.dumps(
        {"checked": len(results), "not_ok": bad, "results": results},
        indent=1, ensure_ascii=False), encoding="utf-8")
    cache_path.write_text(json.dumps(cache, indent=1), encoding="utf-8")
    for r in results:
        if not r.get("ok", True):
            print(f"[urlcheck] {r['status']:>18} {r['url'][:90]} <- {r['rows'][:2]}")
    print(f"[urlcheck] {len(results)} unique URLs, {bad} not OK -> {out}")
    return bad


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(
        description="Check every Source URL in this run's emitted CSVs. Judges click them. Reads "
                    "whatever the run emitted, narrowed by ECONOMIES; results cached so re-runs "
                    "are free. Exits 1 if any URL is not 2xx/3xx.")
    ap.parse_args()
    sys.exit(1 if run_urlcheck() else 0)
