"""The last run: what the Federal Register listed and what was stored, read from `outputs/AU/AU_ws_<date>[_n]/`.

A run folder (`outputs/README.md`) holds the list the crawl read (`links_used/`) and the engine's manifest. The
register state comes from the newest run that has a `laws.csv`, because that file carries **every title's
`version_id`**, which is the value a check compares. The link rows and the stored documents come from every run,
newest first, so a delta run's small manifest sits on top of the full crawl's.

Nothing here sends a request.
"""
from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

RUN_DIR = re.compile(r"^AU_ws_(\d{4}-\d{2}-\d{2})(?:_to_(\d{4}-\d{2}-\d{2}))?(?:_(\d+))?$")


@dataclass
class StoredDocument:
    """One document a run stored, from its manifest."""
    doc_id: str
    source_url: str
    law_name_guess: Optional[str]
    law_number_guess: Optional[str]
    access_date: Optional[str]
    run: str


@dataclass
class Baseline:
    run: Optional[Path]                       # the run whose laws.csv gives the register state
    listed: dict[str, dict] = field(default_factory=dict)      # register id -> laws.csv row
    documents: dict[str, dict] = field(default_factory=dict)   # url -> link row, newest run first
    stored: dict[str, StoredDocument] = field(default_factory=dict)   # url -> the document stored for it
    by_portal_id: dict[str, StoredDocument] = field(default_factory=dict)
    generated_at: Optional[str] = None        # when the baseline's list was built, the default `since`
    runs_read: list[str] = field(default_factory=list)

    @property
    def since(self) -> Optional[str]:
        """The date the check covers from: the day the baseline's list was built."""
        return (self.generated_at or "")[:10] or None

    def version_of(self, portal_id: str) -> Optional[str]:
        row = self.listed.get(portal_id)
        return (row or {}).get("version_id") or None


def run_sort_key(path: Path) -> tuple:
    """Runs sort by the date in the folder name, a check after the crawl it followed, then by the suffix."""
    m = RUN_DIR.match(path.name)
    if not m:
        return ("", "", 0)
    start, end, n = m.group(1), m.group(2) or "", int(m.group(3) or 1)
    return (end or start, start, n)


def list_runs(outputs_dir: str | Path, economy: str = "AU") -> list[Path]:
    """Every run folder under `outputs/AU/`, newest last."""
    out = Path(outputs_dir)
    if not out.is_dir():
        return []
    runs = [p for p in out.iterdir() if p.is_dir() and RUN_DIR.match(p.name)]
    return sorted(runs, key=run_sort_key)


def list_dir(run: Path) -> Optional[Path]:
    """The folder holding the list a run read."""
    for name in ("links_used", "links_rebuilt"):
        if (run / name / "documents.jsonl").is_file():
            return run / name
    return None


def _jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load(outputs_dir: Optional[str | Path] = None, run: Optional[str | Path] = None) -> Baseline:
    """The baseline: the newest run's register state, and every run's link rows and stored documents.

    `run` pins one run folder; otherwise every run under `outputs_dir` is read, newest first.
    """
    if run is not None:
        runs = [Path(run)]
    elif outputs_dir is not None:
        runs = list(reversed(list_runs(outputs_dir)))
    else:
        raise ValueError("load() needs outputs_dir or run")

    b = Baseline(run=None)
    for r in runs:
        if not r.is_dir():
            continue
        b.runs_read.append(r.name)
        ld = list_dir(r)
        if ld is not None:
            for row in _jsonl(ld / "documents.jsonl"):
                b.documents.setdefault(row.get("url") or "", row)
            meta = ld / "catalogue_meta.json"
            laws = ld / "laws.csv"
            if b.run is None and laws.is_file():
                b.run = r
                with laws.open(encoding="utf-8-sig", newline="") as fh:
                    for row in csv.DictReader(fh):
                        if row.get("portal_id"):
                            b.listed[row["portal_id"]] = row
                if meta.is_file():
                    try:
                        b.generated_at = json.loads(meta.read_text(encoding="utf-8")).get("generated_at")
                    except Exception:  # noqa: BLE001 — a damaged meta file only costs the default `since`
                        pass
        for m in _jsonl(r / "manifest.jsonl"):
            url = m.get("source_url") or ""
            if url and url not in b.stored:
                d = StoredDocument(doc_id=m.get("doc_id") or "", source_url=url,
                                   law_name_guess=m.get("law_name_guess"), law_number_guess=m.get("law_number_guess"),
                                   access_date=m.get("access_date"), run=r.name)
                b.stored[url] = d
                link = b.documents.get(url) or {}
                pid = ((link.get("contract_meta") or {}).get("portal_id")) or ""
                if pid:
                    b.by_portal_id.setdefault(pid, d)
    return b
