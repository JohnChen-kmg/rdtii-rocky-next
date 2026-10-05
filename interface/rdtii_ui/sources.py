"""The sources of each economy, and the folder each one owns.

Every result is filed under its economy and then its source, the same way on both sides:

    <runs root>/scrape/<CC>/<source>/<run>/     what the crawler fetched from a portal
    <inbox>/<CC>/Hand_collected/<batch>/        what a person fetched by hand, one dated batch per drop
    <inbox>/<CC>/<source>/<batch>/              the same, filed under a designated source (the layout before it)

A source is designated by the stage's own files, never by a list kept here: the portal an economy's adapter
crawls comes from its source registry, the sources collected by hand come from its watchlist, and China's
from the publisher table of its tools. A source's folder name (its key) is made from its address, so it is
the same on every machine and readable in a file manager.

The older shapes are still read, so nothing made before this layout disappears: a run folder directly under
scrape/ (`SG_20260930-000323`, `CN_20260930-103644`, `hand_...`) and files or dated batches directly under
an economy's inbox folder.
"""
from __future__ import annotations

import re
import unicodedata
from pathlib import Path

from .settings import Settings

BATCH_RX = re.compile(r"\d{4}-\d{2}-\d{2}_\d{6}")      # a drop's local time, named by the page
ECON_RX = re.compile(r"[A-Z]{2}")
KEY_RX = re.compile(r"[a-z0-9][a-z0-9-]{0,63}")
CHINA_TOOLS = "china-tools"                            # the source folder of a China tools run
HAND = "Hand_collected"                                # the one folder of an economy for files fetched by hand


def hand_source() -> dict:
    """The folder every hand-collected file goes to, in the shape of a source. It has no page of its own: a file
    is cited to the address noted for it, or to none."""
    return {"key": HAND, "name": "Hand-collected", "url": "", "host": "", "kind": "", "why": "", "what": "", "mode": "hand"}


def is_hand(key: str) -> bool:
    return (key or "").strip().lower() == HAND.lower()


def slug(text: str, limit: int = 40) -> str:
    """Lower-case ASCII with hyphens; empty when the text has no Latin letters or digits."""
    folded = unicodedata.normalize("NFKD", str(text or "")).encode("ascii", "ignore").decode("ascii")
    out = re.sub(r"[^a-z0-9]+", "-", folded.lower()).strip("-")
    if len(out) > limit:                       # cut at a word, never mid-word
        out = out[:limit + 1].rsplit("-", 1)[0] if "-" in out[:limit + 1] else out[:limit]
    return out.strip("-")


def host_of(url: str) -> str:
    host = re.sub(r"^[a-z][a-z0-9+.-]*://", "", str(url or "").strip(), flags=re.I).split("/")[0].split("?")[0].lower()
    host = host.split("@")[-1].split(":")[0]
    return host[4:] if host.startswith("www.") else host


def host_key(url: str) -> str:
    return slug(host_of(url).replace(".", "-"), 48)


# ---- which sources an economy has -------------------------------------------------------------------

def crawl_source(s: Settings, code: str) -> dict | None:
    """The portal the crawler's adapter reads for an economy, with its folder key."""
    from .pages import scrape
    ports, _ = scrape.portals(s, code)
    hit = next((p for p in ports if p.get("crawled")), None)
    if not hit:
        return None
    return {"key": host_key(hit["root"]) or slug(hit["name"]) or "portal", "name": hit["name"], "url": hit["root"],
            "host": host_of(hit["root"]), "mode": "crawl"}


def designated(s: Settings, code: str) -> list[dict]:
    """The sources of an economy that are collected by hand, each with its folder key.

    China's are the publishers its tools mark "by hand" (the national database, MIIT, Customs), under the
    folder names the shipped collection already uses. Every other economy's are the rows of its watchlist.
    """
    from .pages import cn_run, scrape
    code = code.upper()
    if code == "CN":
        return [{"key": p["src"], "name": p["name"], "url": p["root"], "host": host_of(p["root"]),
                 "kind": f"layer {p['layer']}", "why": p.get("run", ""), "what": p.get("what", ""), "mode": "hand"}
                for p in cn_run.PUBLISHERS if p.get("mode") == "hand"]
    wl = scrape.watchlist_path(s, code)
    rows = [r for r in (scrape.read_watchlist(wl) if wl else []) if (r.get("name") or "").strip()]
    hosts = [host_key(r.get("url", "")) for r in rows]
    out: list[dict] = []
    used: set[str] = set()
    for i, r in enumerate(rows):
        base = hosts[i] or slug(r["name"]) or f"source-{i + 1}"
        key = base
        if hosts.count(hosts[i]) > 1 or key in used:
            # several sources on one host: the part of the name after the middle dot tells them apart
            tail = slug(r["name"].split("·")[-1], 28) or slug(re.sub(r"^[a-z]+://[^/]+", "", r.get("url", "")), 28)
            key = f"{base}-{tail}" if tail and tail != base else base
        n = 2
        while key in used:
            key = f"{base}-{n}"
            n += 1
        used.add(key)
        out.append({"key": key[:64].strip("-"), "name": r["name"].strip(), "url": (r.get("url") or "").strip(),
                    "host": host_of(r.get("url", "")), "kind": (r.get("kind") or "").strip(),
                    "why": (r.get("why_not_automatic") or "").strip(), "what": (r.get("what_to_look_for") or "").strip(),
                    "mode": "hand"})
    return out


def find(s: Settings, code: str, key: str) -> dict | None:
    """A source of an economy by its folder key: the hand-collected folder, a designated one, or the crawled portal."""
    if is_hand(key):
        return hand_source()
    key = (key or "").strip().lower()
    for src in designated(s, code):
        if src["key"] == key:
            return src
    cs = crawl_source(s, code) if code.upper() != "CN" else None
    if cs and cs["key"] == key:
        return cs
    if code.upper() == "CN" and key == CHINA_TOOLS:
        return {"key": CHINA_TOOLS, "name": "China tools", "url": "", "host": "", "mode": "tools"}
    return None


# ---- where things are filed ---------------------------------------------------------------------------

def scrape_run_dir(s: Settings, code: str, source_key: str, run: str) -> Path:
    return s.runs_root / "scrape" / code.upper() / source_key / run


def is_economy_folder(p: Path) -> bool:
    """A folder directly under scrape/ that holds sources, as against a run folder of the older layout."""
    return bool(ECON_RX.fullmatch(p.name)) and p.is_dir() and not (p / "manifest.csv").is_file()


def scrape_runs(s: Settings) -> list[tuple[Path, dict]]:
    """Every run folder under the runs root's scrape/, newest first within its group, with where it sits:
    {"economy", "source", "run"} for the layout by source, {} for a run folder of the older layout."""
    root = s.runs_root / "scrape"
    out: list[tuple[Path, dict]] = []
    if not root.is_dir():
        return out
    for p in sorted(root.iterdir(), reverse=True):
        if not p.is_dir():
            continue
        if not is_economy_folder(p):
            out.append((p, {}))
            continue
        for src in sorted(x for x in p.iterdir() if x.is_dir()):
            for run in sorted((x for x in src.iterdir() if x.is_dir()), reverse=True):
                out.append((run, {"economy": p.name, "source": src.name, "run": run.name}))
    return out


def scrape_identity(s: Settings, path: Path) -> dict:
    """Where a folder sits under scrape/: {"economy", "source", "run"} in the layout by source, else {}."""
    try:
        parts = path.resolve().relative_to((s.runs_root / "scrape").resolve()).parts
    except ValueError:
        return {}
    if len(parts) >= 3 and ECON_RX.fullmatch(parts[0]):
        return {"economy": parts[0], "source": parts[1], "run": parts[2]}
    return {}


def inbox_identity(path: Path, inbox_dir: Path | None = None) -> dict:
    """What an inbox folder is, from its place: {"economy", "source", "batch", "legacy"}.

    inbox/CN                         -> the economy
    inbox/CN/Hand_collected                    -> the hand-collected folder, every batch
    inbox/CN/Hand_collected/2026-10-05_101522  -> one batch of it
    inbox/CN/miit                    -> one designated source, every batch (the layout before it)
    inbox/CN/miit/2026-10-03_101522  -> one batch of a source
    inbox/CN/2026-09-30_101522       -> a batch of the older layout, with no source (legacy)
    Read from the folder names, so it also works for a folder given by its path alone.
    """
    names = [path.name, path.parent.name, path.parent.parent.name]
    if inbox_dir is not None:
        try:
            rel = path.resolve().relative_to(inbox_dir.resolve()).parts
        except ValueError:
            return {}
        names = list(reversed(rel)) + ["", "", ""]
        if not rel:
            return {}
        if len(rel) > 3 or not ECON_RX.fullmatch(rel[0].upper()):
            return {}
    is_econ = lambda n: bool(re.fullmatch(r"[A-Za-z]{2}", n or ""))  # noqa: E731
    is_batch = lambda n: bool(BATCH_RX.fullmatch(n or ""))           # noqa: E731
    is_key = lambda n: n == HAND or (bool(KEY_RX.fullmatch(n or "")) and not is_batch(n) and not is_econ(n))  # noqa: E731
    a, b, c = names[0], names[1], names[2]
    if is_batch(a) and is_key(b) and is_econ(c):
        return {"economy": c.upper(), "source": b, "batch": a, "legacy": False}
    if is_batch(a) and is_econ(b):
        return {"economy": b.upper(), "source": "", "batch": a, "legacy": True}
    if is_key(a) and is_econ(b):
        return {"economy": b.upper(), "source": a, "batch": "", "legacy": False}
    if is_econ(a) and (inbox_dir is not None or True):
        return {"economy": a.upper(), "source": "", "batch": "", "legacy": True}
    return {}
