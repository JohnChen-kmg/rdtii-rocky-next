"""Scraping › China: the one economy collected by hand, and why.

Everything shown is read from the crawler stage's own China material under stages/p1-scrape/handoff1/CN and
the cn_npc adapter package: the robots rule per host, the two layers, the watchlist of sources a person checks,
the shipped folders with their counts, and the notes themselves for reading in the page.
"""
from __future__ import annotations

import csv
from collections import OrderedDict
from pathlib import Path

from .. import readers
from ..server import App, rel_or_abs
from ..settings import REPO, Settings
from . import scrape

# The robots rule per host, as recorded in handoff1/CN/README.md on 2026-09-21. A summary of a shipped note.
HOST_RULES = [
    ("flk.npc.gov.cn", "national database", "robots.txt forbids automated collection in as many words, then Disallow: /", "hand only"),
    ("www.pbc.gov.cn", "central bank", "User-agent: * / Disallow: /", "hand only"),
    ("www.cac.gov.cn", "cyberspace administration", "permits, with four paths disallowed", "crawled, one request every 6 s"),
    ("www.gov.cn", "government portal", "permits, legacy paths only", "crawlable; six permitted copies taken"),
    ("www.miit.gov.cn, www.ndrc.gov.cn", "industry and reform ministries", "403 to any client, robots.txt included", "hand: permission cannot be established"),
    ("www.customs.gov.cn", "customs", "412, and a certificate the browser rejects", "hand, via mirrors"),
    ("SAMR, MOFCOM, OSCCA, MOF, CNCA, NHC, MOST", "other ministries", "no robots.txt published", "nothing disallowed; deferred"),
]

# Watchlist kinds, in the order the page shows them, with a plain label.
KIND_LABELS = OrderedDict([
    ("layer-1", "Layer 1: the national database"),
    ("manual-host", "Layer 2 hosts that refuse an automated client"),
    ("regulator", "Regulators named as sources but never crawled"),
    ("stream", "Announcement streams"),
    ("new-publisher", "Publishers found during research"),
    ("tariff", "Tariff and customs pages"),
    ("standards", "National standards"),
    ("canary", "Canaries: pages watched for change"),
])


def register(app: App) -> None:
    @app.route("GET", r"/api/scrape/china")
    def china(app: App, m, q, b):
        return 200, describe(app.settings)


def cn_root(s: Settings) -> Path:
    return scrape.p1_dir(s) / "handoff1" / "CN"


def _rows(path: Path, delimiter: str = ",") -> int:
    if not path.is_file():
        return 0
    with open(path, encoding="utf-8-sig", newline="") as f:
        return sum(1 for _ in csv.DictReader(f, delimiter=delimiter))


def shipped_folders(s: Settings) -> list[dict]:
    root = cn_root(s)
    out = []
    if not root.is_dir():
        return out
    for p in sorted(root.iterdir()):
        if not p.is_dir():
            continue
        d = {"name": p.name, "id": rel_or_abs(p, REPO), "manifest_rows": _rows(p / "manifest.csv"),
             "provenance_rows": _rows(p / "provenance.tsv", "\t"), "notes": []}
        for note in ("README.md", "RUN_NOTE.md", "FINDINGS.md", "LINKS.md", "CHECK_BY_HAND.md", "MANUAL_UPDATE_CHECK.md"):
            if (p / note).is_file():
                d["notes"].append(rel_or_abs(p / note, REPO))
        # the corpus folder: one line per source with its provenance count
        sources = []
        for mode in ("manual", "auto"):
            mdir = p / mode
            if mdir.is_dir():
                for src in sorted(mdir.iterdir()):
                    if src.is_dir():
                        sources.append({"source": src.name, "mode": mode, "provenance_rows": _rows(src / "provenance.tsv", "\t"),
                                        "index_rows": _rows(src / "index.csv") or _rows(src / "list.csv")})
        deferred = p / "_deferred"
        if deferred.is_dir():
            n = sum(1 for mode in ("manual", "auto") if (deferred / mode).is_dir() for x in (deferred / mode).iterdir() if x.is_dir())
            d["deferred_sources"] = n
        d["sources"] = sources
        out.append(d)
    return out


def watchlist_grouped(s: Settings) -> list[dict]:
    wl = scrape.watchlist_path(s, "CN")
    rows = scrape.read_watchlist(wl) if wl else []
    groups: OrderedDict[str, list] = OrderedDict((k, []) for k in KIND_LABELS)
    for r in rows:
        groups.setdefault(r.get("kind", "other"), []).append(r)
    return [{"kind": k, "label": KIND_LABELS.get(k, k), "rows": v} for k, v in groups.items() if v]


def docs(s: Settings) -> list[dict]:
    root = cn_root(s)
    out = []
    if root.is_dir():
        for p in sorted(root.glob("*.md")) + sorted(root.glob("*/*.md")) + sorted(root.glob("*/*/*.md")):
            if p.is_file() and "_deferred" not in p.parts[-3:-1]:
                out.append({"path": rel_or_abs(p, REPO), "title": p.relative_to(root).as_posix()})
    return out


def describe(s: Settings) -> dict:
    wl = scrape.watchlist_path(s, "CN")
    return {
        "present": cn_root(s).is_dir(),
        "root": rel_or_abs(cn_root(s), REPO),
        "hosts": [{"host": h, "who": w, "robots": r, "action": a} for h, w, r, a in HOST_RULES],
        "watchlist": watchlist_grouped(s),
        "watchlist_total": len(scrape.read_watchlist(wl)) if wl else 0,
        "watchlist_file": rel_or_abs(wl, REPO) if wl else None,
        "folders": shipped_folders(s),
        "docs": docs(s),
        "tools": [
            {"name": "layer1.py", "does": "reads a hand-downloaded export offline and diffs two exports: laws added, removed, amended by the version date in each file name. Sends no request."},
            {"name": "update.py", "does": "re-reads the CAC and gov.cn indexes, the two hosts that permit us, and lists what is new, gone or retitled; layer 1 only by comparing two hand exports."},
            {"name": "manual_check.py", "does": "writes the worklist for MIIT and Customs: the section pages to open and the exact address and version date of every document held, so the check is a comparison, not a search."},
            {"name": "triage.py", "does": "sorts a listing pasted from a browser, offline: already held, superseded, or new."},
            {"name": "checkdocs.py", "does": "checks that hand-saved files are machine-readable; a page printed to PDF on Windows loses its text."},
        ],
    }
