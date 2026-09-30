"""The sources an update check cannot see, said out loud on every run.

**The developer's rule of 2026-09-21, for every country.** Most of the evidence an index needs does not sit in
one main law database: regulators publish their own codes and circulars, customs and trade bodies publish lists,
ministries are created and renamed, and sites move or start refusing us. An update check that re-reads the main
database cannot see any of that. So it does not pretend to: **every update check prints its country's watch list
before it starts and again when it finishes**, and a check is not a complete update until those sources have
been looked at by hand.

The list for a country is `watchlist.tsv` beside its `updates/__main__.py`. The columns:

    name  url  kind  why_not_automatic  what_to_look_for  expect  indicators  last_checked  address_verified

    kind   regulator         publishes instruments the main database does not carry
           stream            an announcement stream: customs lists, tariff notices, catalogues
           tariff            the customs and tariff source, manual in every economy by decision (rule 14)
           manual-host       the host forbids us, or refuses an honest client
           uncollected       a category of the main portal this scraper does not read yet
           new-publisher     a body not in the source list
           retarget          research says this should be the main database, or a main database has moved
           dead              a host the registry names that no longer answers

`url` is **the page that carries the thing, not the host's front door**: a researcher should be able to open it and
read the figure. `address_verified` is the date somebody opened that address and it worked — a row without one is a
row nobody has proved. It is not `last_checked`, which is the date the source was checked for *changes*.

Record a check (it sets `last_checked` to today), or print the list alone:

    python countries/my-malaysia/scraper/watchlist.py countries/sg-singapore/updates/watchlist.tsv --checked PDPC
    python countries/my-malaysia/scraper/watchlist.py countries/sg-singapore/updates/watchlist.tsv

This module imports nothing from the package, so it runs as a script as well as from an update check, and it
never raises: a broken watch list must not fail the check it is attached to.
"""
from __future__ import annotations

import csv
import os
import sys
from datetime import datetime

STALE_DAYS = 90

#: `breadth`: does the source serve one indicator or several? Not all external sources are equal. A source that
#: serves many indicators (China's CAC serves 16) is worth checking on every update and worth automating first. A
#: source that serves exactly one (China's SASAC, for 5.3 alone) matters only when that indicator does — but it may
#: be the only place that indicator's answer lives, so it is never dropped. `unconfirmed` means not yet known.
_BREADTH_ORDER = {"multiple": 0, "single": 1, "unconfirmed": 2, "n/a": 3}
_BREADTH_TAG = {"multiple": "many", "single": "1 ind", "unconfirmed": "?", "n/a": "-"}
_BROAD = ("all", "most")


def _match(row: dict, indicator: str):
    """'dedicated' if the row names the indicator (or its family, `12.4.x`); 'general' if it is a broad index
    (`all`, `most`) that may carry it; None if neither."""
    want, general = indicator.strip(), False
    for tok in (row.get("indicators") or "").replace(";", ",").split(","):
        tok = tok.strip().split(" ")[0].rstrip("?")
        if not tok:
            continue
        if tok == want or (tok.endswith(".x") and (want + ".").startswith(tok[:-1])):
            return "dedicated"
        if tok.lower() in _BROAD:
            general = True
    return "general" if general else None


def for_indicator(path, indicator: str, out=None) -> None:
    """Which watch-list sources serve one indicator? For a live test that draws it."""
    out = out or sys.stdout
    _, rows = _rows(path)
    dedicated = [r for r in rows if _match(r, indicator) == "dedicated"]
    general = [r for r in rows if _match(r, indicator) == "general"]

    def line(r):
        tag = _BREADTH_TAG.get(r.get("breadth", ""), "?")
        age = "never checked" if _age(r) is None else f"checked {r['last_checked']}"
        _say(out, f"  {tag:<5} {r.get('name', '')[:40]:<42} {age:<24} {r.get('url', '')}")

    _say(out, f"\nIndicator {indicator}: sources on this watch list")
    _say(out, f" Dedicated — they name {indicator} or its family ({len(dedicated)}):")
    for r in sorted(dedicated, key=lambda r: _BREADTH_ORDER.get(r.get("breadth", ""), 9)):
        line(r)
    if not dedicated:
        _say(out, f"  none. {indicator}'s own source is collected automatically, is the main database, or is not yet found.")
    for r in (r for r in dedicated if r.get("breadth") == "single"):
        _say(out, f"  -> {r['name']} serves {indicator} and nothing else.")
    if len(dedicated) == 1:
        # only true when there is exactly one; with several, dropping one still leaves the others
        _say(out, f"  -> It is the only source dedicated to {indicator} on this list: skip it and only the general")
        _say(out, "     indexes below remain.")
    _say(out, f" General indexes that may carry it ({len(general)}):")
    for r in general:
        line(r)


def _rows(path) -> tuple[list[str], list[dict]]:
    with open(path, encoding="utf-8", newline="") as f:
        r = csv.DictReader(f, delimiter="\t", restval="")
        return list(r.fieldnames or []), [{k: (v or "") for k, v in row.items() if k} for row in r]


def _age(row: dict):
    try:
        then = datetime.strptime((row.get("last_checked") or "").strip(), "%Y-%m-%d").date()
    except ValueError:
        return None
    return (datetime.now().date() - then).days


def _say(out, text: str) -> None:
    """Write one line whatever the console's encoding: a Lao or Chinese name must not raise."""
    try:
        out.write(text + "\n")
    except UnicodeEncodeError:
        enc = getattr(out, "encoding", None) or "ascii"
        out.write(text.encode(enc, errors="replace").decode(enc) + "\n")


def remind(path, economy: str, when: str, out=None) -> None:
    """Print the watch list. Never raises."""
    out = out or sys.stdout
    try:
        path = os.fspath(path)
        if not os.path.exists(path):
            _say(out, f"\n[updates] !! {economy}: no watch list at {path}")
            _say(out, "[updates] !! this check cannot say which sources it does not see\n")
            out.flush()
            return
        _, rows = _rows(path)
        # stalest first; within equal staleness, the sources that serve several indicators first
        rows.sort(key=lambda r: (-1 if _age(r) is None else -_age(r), _BREADTH_ORDER.get(r.get("breadth", ""), 9)))
        never = sum(1 for r in rows if _age(r) is None)
        stale = sum(1 for r in rows if (_age(r) or 0) > STALE_DAYS)
        many = sum(1 for r in rows if r.get("breadth") == "multiple")
        one = sum(1 for r in rows if r.get("breadth") == "single")
        bar = "=" * 78
        _say(out, f"\n{bar}\n {economy}: CHECK BY HAND - {len(rows)} sources this update check does not see ({when})")
        _say(out, " This check is NOT a complete update until these have been looked at.")
        _say(out, f" {never} never checked, {stale} not checked in {STALE_DAYS}+ days.")
        _say(out, f" {many} serve several indicators: check those first. {one} serve exactly one: they matter only")
        _say(out, "   for that indicator, but may be the only place its answer lives. Sources for one indicator:")
        _say(out, f"   python countries/my-malaysia/scraper/watchlist.py {path} --indicator 12.5")
        _say(out, f" Record a check:  python countries/my-malaysia/scraper/watchlist.py {path} --checked <name>")
        _say(out, bar)
        for r in rows:
            a = _age(r)
            age = "never checked" if a is None else f"{a} days ago"
            tag = _BREADTH_TAG.get(r.get("breadth", ""), "?")
            _say(out, f" {age:<14} {r.get('kind', ''):<13} {tag:<5} {r.get('name', '')[:34]:<36} {r.get('url', '')}")
        _say(out, " many = several indicators   1 ind = exactly one   ? = not yet known")
        _say(out, bar + "\n")
        out.flush()
    except Exception as e:  # noqa: BLE001 - the reminder must never fail the check
        try:
            _say(out, f"\n[updates] !! {economy}: watch list unreadable ({e}); check it by hand\n")
        except Exception:  # noqa: BLE001
            pass


def mark_checked(path, needle: str) -> int:
    fields, rows = _rows(path)
    hit = [r for r in rows if needle.lower() in (r.get("name", "") + " " + r.get("url", "")).lower()]
    today = datetime.now().strftime("%Y-%m-%d")
    for r in hit:
        r["last_checked"] = today
        print(f"  checked {today}  {r['name']}")
    if not hit:
        print(f"  no row matches {needle!r}")
        return 1
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    return 0


if __name__ == "__main__":
    import argparse

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    ap = argparse.ArgumentParser(description="Print a country's watch list, or record that a source was checked.")
    ap.add_argument("watchlist", help="path to a country's updates/watchlist.tsv")
    ap.add_argument("--checked", metavar="NAME", help="set last_checked to today on every row matching NAME")
    ap.add_argument("--indicator", metavar="ID", help="list the sources that serve one indicator, e.g. 12.5")
    a = ap.parse_args()
    if a.checked:
        raise SystemExit(mark_checked(a.watchlist, a.checked))
    if a.indicator:
        for_indicator(a.watchlist, a.indicator)
        raise SystemExit(0)
    remind(a.watchlist, os.path.basename(os.path.dirname(os.path.dirname(os.path.abspath(a.watchlist)))), "on request")
