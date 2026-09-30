"""The last run: what Laws of Malaysia listed and what was stored, read from outputs/<CC>/<CC>_ws_<date>[_n]/.

A run folder (outputs/README.md) holds the list the crawl read (links_used/, or links_rebuilt/ when a list was rebuilt
with fixed details) and the engine's manifest. The listing state comes from the newest run that has a laws.csv (an
update check's own list counts: what it found and did not fetch is caught again as `not_stored`); the link rows, the
stored documents and the duplicates the engine logged come from every run, newest first, so a delta run's small
manifest sits on top of the full crawl's.
"""
from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from ..parse import _act_key

# A crawl: <CC>_ws_<date>. An update check: <CC>_ws_<since>_to_<date>, the period it covered. Either may end in
# _2, _3 for a second run of the same name on the same day. Runs are ordered by their end date.
RUN_DIR = re.compile(r"^(?P<cc>[A-Z]{2})_ws_(?P<date>\d{4}-\d{2}-\d{2})(?:_to_(?P<to>\d{4}-\d{2}-\d{2}))?(?:_(?P<n>\d+))?$")
LIST_DIRS = ("links_rebuilt", "links_used", "links")


@dataclass
class StoredDocument:
    url: str
    doc_id: str
    run: str                                   # the run folder's name
    content_sha256: Optional[str] = None
    etag: Optional[str] = None
    last_modified: Optional[str] = None
    access_date: Optional[str] = None
    local_path: Optional[str] = None
    law_name_guess: Optional[str] = None
    law_number_guess: Optional[str] = None


@dataclass
class Baseline:
    runs: list[Path] = field(default_factory=list)                # newest first
    state_run: Optional[Path] = None                               # whose laws.csv gives the listing state
    state_dir: Optional[Path] = None                               # its list folder
    started_at: Optional[str] = None                               # the newest run's crawl start, ISO UTC
    generated_at: Optional[str] = None                             # when the state list was built
    principals: dict[str, dict] = field(default_factory=dict)      # _act_key(portal_id) -> laws.csv row
    amendments: dict[str, dict] = field(default_factory=dict)      # A-number, upper -> laws.csv row
    documents: dict[str, dict] = field(default_factory=dict)       # url -> link-list row (with contract_meta), every run
    stored: dict[str, StoredDocument] = field(default_factory=dict)  # url -> the newest stored copy
    duplicates: set[str] = field(default_factory=set)                # urls the engine logged as duplicate (bytes stored under another url)
    notes: list[str] = field(default_factory=list)

    @property
    def since_date(self) -> Optional[str]:
        """The UTC date the newest run started (else the date its list was built): what "since" means by default."""
        stamp = self.started_at or self.generated_at or ""
        return stamp[:10] or None

    @property
    def name(self) -> Optional[str]:
        return self.runs[0].name if self.runs else None

    def previous(self, portal_id: Optional[str], document_kind: Optional[str]) -> Optional[dict]:
        """The stored document of the same law and kind in the baseline: doc_id, url, sha, version, run."""
        if not portal_id:
            return None
        found = None
        for url, row in self.documents.items():
            meta = row.get("contract_meta") or {}
            if str(meta.get("portal_id")) == str(portal_id) and meta.get("document_kind") == document_kind:
                stored = self.stored.get(url)
                candidate = {"url": url, "doc_id": stored.doc_id if stored else None,
                             "content_sha256": stored.content_sha256 if stored else None,
                             "version_as_at": meta.get("version_as_at"), "run": stored.run if stored else None,
                             "stored": stored is not None}
                if stored is not None:              # a row that was fetched beats a newer one that was not
                    return candidate
                found = found or candidate
        return found


def run_sort_key(path: Path) -> tuple:
    """(end date, plain crawl before a check of the same day, suffix): the order runs happened in."""
    m = RUN_DIR.match(path.name)
    if not m:
        return ("", 0, 0)
    return (m.group("to") or m.group("date"), 1 if m.group("to") else 0, int(m.group("n") or 1))


def list_runs(outputs_dir: str | Path, economy: str = "MY") -> list[Path]:
    """Run folders for the economy under outputs/<CC>/ (or a folder holding them), newest first."""
    base = Path(outputs_dir)
    if not base.is_dir():
        return []
    runs = [p for p in base.iterdir() if p.is_dir() and RUN_DIR.match(p.name)
            and RUN_DIR.match(p.name).group("cc") == economy.upper()]
    return sorted(runs, key=run_sort_key, reverse=True)


def list_dir(run: Path) -> Optional[Path]:
    for name in LIST_DIRS:
        if (run / name / "laws.csv").is_file():
            return run / name
    return None


def load(outputs_dir: Optional[str | Path] = None, run: Optional[str | Path] = None,
         economy: str = "MY") -> Baseline:
    """The baseline for a check: `run` alone, or every run under `outputs_dir` (newest first)."""
    if run is not None:
        runs = [Path(run)]
        if not runs[0].is_dir():
            raise FileNotFoundError(f"baseline run folder not found: {runs[0]}")
    else:
        if outputs_dir is None:
            raise ValueError("a baseline needs --outputs <folder of runs> or --baseline <run folder>")
        runs = list_runs(outputs_dir, economy)
        if not runs:
            raise FileNotFoundError(f"no {economy}_ws_<date> run folder under {outputs_dir}")
    b = Baseline(runs=runs)
    status = runs[0] / "crawl_status.json"
    if status.is_file():
        try:
            b.started_at = (json.loads(status.read_text(encoding="utf-8")) or {}).get("started_at")
        except ValueError:
            b.notes.append(f"{status}: unreadable crawl_status.json")
    for r in runs:                                   # listing state: the newest run with a laws.csv
        d = list_dir(r)
        if d is None:
            continue
        b.state_run, b.state_dir = r, d
        with open(d / "laws.csv", encoding="utf-8-sig", newline="") as fh:
            for row in csv.DictReader(fh):
                if row.get("listing") == "amendment":
                    b.amendments[str(row.get("portal_id") or "").upper()] = row
                else:
                    b.principals[_act_key(str(row.get("portal_id") or ""))] = row
        meta = d / "catalogue_meta.json"
        if meta.is_file():
            try:
                b.generated_at = (json.loads(meta.read_text(encoding="utf-8")) or {}).get("generated_at")
            except ValueError:
                b.notes.append(f"{meta}: unreadable catalogue_meta.json")
        break
    if b.state_run is None:
        b.notes.append("no run holds a laws.csv: the listing state is unknown, only stored URLs are compared")
    for r in runs:                                   # link rows: every run's list, the newest row for a url wins
        d = list_dir(r)
        docs = d / "documents.jsonl" if d else None
        if docs is None or not docs.is_file():
            continue
        for line in docs.read_text(encoding="utf-8").splitlines():
            if line.strip():
                row = json.loads(line)
                b.documents.setdefault(row["url"], row)
    for r in runs:                                   # stored documents: every run, the newest copy wins
        manifest = r / "manifest.jsonl"
        if manifest.is_file():
            for line in manifest.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                m = json.loads(line)
                headers = (m.get("http") or {}).get("headers") or {}
                b.stored.setdefault(m["source_url"], StoredDocument(
                    url=m["source_url"], doc_id=m.get("doc_id") or "", run=r.name,
                    content_sha256=m.get("content_sha256"), etag=headers.get("ETag") or headers.get("etag"),
                    last_modified=headers.get("Last-Modified") or headers.get("last-modified"),
                    access_date=m.get("access_date"), local_path=m.get("local_path"),
                    law_name_guess=m.get("law_name_guess"), law_number_guess=m.get("law_number_guess")))
        log = r / "crawl_log.jsonl"                  # the engine stores identical bytes once and logs the other url
        if log.is_file():
            for line in log.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    e = json.loads(line)
                    if e.get("outcome") == "duplicate" and e.get("url"):
                        b.duplicates.add(e["url"])
    if not b.stored:
        b.notes.append("no run holds a manifest.jsonl: nothing is known to be stored")
    return b
