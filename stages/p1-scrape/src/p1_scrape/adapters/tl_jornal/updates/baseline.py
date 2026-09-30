"""What the last run knew: the acts the portal listed, and the documents we hold.

A run folder counts as a baseline when it holds `links_used/laws.csv` — the census of every act the portal listed
that day. Documents come from every run's manifest, newest first, so a check knows what is already stored even
when the listing has not changed.
"""
from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

RUN_DIR = re.compile(r"^TL_ws_[0-9]{4}-[0-9]{2}-[0-9]{2}")
LIST_DIRS = ("links_used", "links_rebuilt", "links")


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


def runs_under(outputs_dir: str | Path) -> list[Path]:
    """Every TL run folder, newest name first."""
    out = Path(outputs_dir)
    if not out.is_dir():
        return []
    return sorted((p for p in out.iterdir() if p.is_dir() and RUN_DIR.match(p.name)), key=lambda p: p.name,
                  reverse=True)


def load(outputs_dir: Optional[str | Path] = None, run: Optional[str | Path] = None) -> Baseline:
    """The newest run with a list, plus what every run stored. `run` pins one instead."""
    runs = [Path(run)] if run else runs_under(outputs_dir or ".")
    if run and outputs_dir:
        runs = [Path(run)] + [p for p in runs_under(outputs_dir) if p != Path(run)]
    base = Baseline()
    for folder in runs:
        list_dir = _list_dir(folder)
        if list_dir and base.run is None:
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
