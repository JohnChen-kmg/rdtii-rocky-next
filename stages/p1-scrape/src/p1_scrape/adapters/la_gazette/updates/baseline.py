"""What the last run knew: the laws the portal listed, and the documents we hold.

A run folder counts as a baseline when it holds `links_used/laws.csv` — the census of every law the portal
listed that day, with the status word it gave each one. Documents come from every run's manifest, newest first,
so a check knows what is already stored even when the listing has not changed.
"""
from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

RUN_DIR = re.compile(r"^LA_ws_[0-9]{4}-[0-9]{2}-[0-9]{2}")
#: Where a run's census is read from, most trustworthy first. `links_rebuilt` is the same portal rows read
#: again by a corrected scraper; when a run carries one it is the better baseline, because `links_used` is
#: frozen as the list the crawl replayed and may carry a defect the scraper has since fixed.
LIST_DIRS = ("links_rebuilt", "links_used", "links")


@dataclass
class Baseline:
    run: Optional[Path] = None
    acts: dict[str, dict] = field(default_factory=dict)            # portal_id -> its laws.csv row
    stored: dict[str, dict] = field(default_factory=dict)          # source_url -> its manifest row
    generated_at: Optional[str] = None
    runs_read: list[str] = field(default_factory=list)

    @property
    def since(self) -> Optional[str]:
        """The day the baseline's list was built: the date a check counts from."""
        return (self.generated_at or "")[:10] or None

    def documents(self) -> set[str]:
        return set(self.stored)

    def act(self, portal_id: str) -> Optional[dict]:
        return self.acts.get(portal_id)


def _read_csv(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    with path.open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def _read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _list_dir(run: Path) -> Optional[Path]:
    for name in LIST_DIRS:
        if (run / name / "laws.csv").is_file():
            return run / name
    return None


#: every date in a run folder's name; the last one is the day the run ended
_DATES = re.compile(r"(\d{4}-\d{2}-\d{2})")


def _ended(run: Path) -> str:
    """The day a run ended, from its name. A crawl is `LA_ws_<date>`; a check is `LA_ws_<since>_to_<date>`, so
    sorting on the whole name ranks a check by the date it counted **from** and can put a fresh check below a
    crawl four days older than it."""
    found = _DATES.findall(run.name)
    return found[-1] if found else ""


def is_partial(run: Path) -> bool:
    """A `--pages` check read only the top of each listing, so its census is a fraction of the portal's and it
    must never become the next baseline: everything below the cut would read as new."""
    changes = run / "changes.json"
    if not changes.is_file():
        return False
    try:
        return bool((json.loads(changes.read_text(encoding="utf-8")) or {}).get("partial"))
    except (ValueError, OSError):
        return False


def runs_under(outputs_dir: str | Path) -> list[Path]:
    """Every LA run folder, the one that ended most recently first."""
    out = Path(outputs_dir)
    if not out.is_dir():
        return []
    return sorted((p for p in out.iterdir() if p.is_dir() and RUN_DIR.match(p.name)),
                  key=lambda p: (_ended(p), p.name), reverse=True)


def load(outputs_dir: Optional[str | Path] = None, run: Optional[str | Path] = None) -> Baseline:
    """The newest run with a list, plus what every run stored. `run` pins one instead."""
    runs = [Path(run)] if run else runs_under(outputs_dir or ".")
    if run and outputs_dir:
        runs = [Path(run)] + [p for p in runs_under(outputs_dir) if p != Path(run)]
    base = Baseline()
    for folder in runs:
        list_dir = _list_dir(folder)
        if list_dir and base.run is None and not is_partial(folder):
            base.run = folder
            for row in _read_csv(list_dir / "laws.csv"):
                if row.get("portal_id"):
                    base.acts[row["portal_id"]] = row
            meta = list_dir / "catalogue_meta.json"
            if meta.is_file():
                base.generated_at = (json.loads(meta.read_text(encoding="utf-8")) or {}).get("generated_at")
        for row in _read_jsonl(folder / "manifest.jsonl") or _read_csv(folder / "manifest.csv"):
            url = row.get("source_url")
            if url and url not in base.stored:                     # newest run wins
                base.stored[url] = row
        base.runs_read.append(folder.name)
    return base
