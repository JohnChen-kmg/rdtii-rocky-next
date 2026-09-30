"""The last run: what Statutes Online listed, with every act's version date, and what was stored.

Read from `outputs/SG/SG_ws_<date>[_n]/`. The listing state comes from the newest run that has a
`links_used/laws.csv`, because that file records **every listed act with the version date its timeline gave**,
which is what a check compares. An update check writes one too, carrying forward every act it did not re-read, so
a check is itself a valid baseline for the next one. The link rows and the stored documents come from every run,
newest first.

Nothing here sends a request.
"""
from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

RUN_DIR = re.compile(r"^SG_ws_(\d{4}-\d{2}-\d{2})(?:_to_(\d{4}-\d{2}-\d{2}))?(?:_(\d+))?$")


@dataclass
class StoredDocument:
    doc_id: str
    source_url: str
    law_name_guess: Optional[str]
    access_date: Optional[str]
    run: str


@dataclass
class Baseline:
    run: Optional[Path]
    laws: dict[str, dict] = field(default_factory=dict)        # portal id -> laws.csv row, every listing
    documents: dict[str, dict] = field(default_factory=dict)   # url -> link row, newest run first
    stored: dict[str, StoredDocument] = field(default_factory=dict)
    by_portal_id: dict[str, StoredDocument] = field(default_factory=dict)
    generated_at: Optional[str] = None
    runs_read: list[str] = field(default_factory=list)

    @property
    def since(self) -> Optional[str]:
        """The day the baseline's list was built: the date a check looks from, unless it is given one."""
        return (self.generated_at or "")[:10] or None

    def listing_of(self, portal_id: str) -> Optional[str]:
        return (self.laws.get(portal_id) or {}).get("listing") or None

    def version_of(self, portal_id: str) -> Optional[str]:
        return (self.laws.get(portal_id) or {}).get("version_as_at") or None

    @property
    def current(self) -> set[str]:
        return {pid for pid, r in self.laws.items() if r.get("listing") == "current"}

    @property
    def subsidiary_codes(self) -> set[str]:
        """Every regulation a run's list carried, so a new one on a seed act's tab can be told apart."""
        return {str((r.get("contract_meta") or {}).get("portal_id")) for r in self.documents.values()
                if (r.get("contract_meta") or {}).get("document_kind") == "subsidiary_legislation"
                and (r.get("contract_meta") or {}).get("portal_id")}

    @property
    def supplement_codes(self) -> set[str]:
        """Every Acts Supplement entry a run's list or census carried."""
        return ({pid for pid, r in self.laws.items() if r.get("listing") == "acts_supp"}
                | {str((r.get("contract_meta") or {}).get("portal_id")) for r in self.documents.values()
                   if (r.get("contract_meta") or {}).get("discovery_path") == "acts_supplement"})


def run_sort_key(path: Path) -> tuple:
    m = RUN_DIR.match(path.name)
    if not m:
        return ("", "", 0)
    start, end, n = m.group(1), m.group(2) or "", int(m.group(3) or 1)
    return (end or start, start, n)


def list_runs(outputs_dir: str | Path) -> list[Path]:
    out = Path(outputs_dir)
    if not out.is_dir():
        return []
    return sorted((p for p in out.iterdir() if p.is_dir() and RUN_DIR.match(p.name)), key=run_sort_key)


def _jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load(outputs_dir: Optional[str | Path] = None, run: Optional[str | Path] = None) -> Baseline:
    """The newest run's listing state, and every run's link rows and stored documents."""
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
        ld = r / "links_used"
        # a run may hold a filtered list beside the full one (SG_ws_2026-09-15 dropped the repealed acts); the
        # full list is the one that names every document
        for row in _jsonl(ld / "documents.jsonl"):
            b.documents.setdefault(row.get("url") or "", row)
        laws = ld / "laws.csv"
        if b.run is None and laws.is_file():
            b.run = r
            with laws.open(encoding="utf-8-sig", newline="") as fh:
                for row in csv.DictReader(fh):
                    if row.get("portal_id"):
                        b.laws.setdefault(row["portal_id"], row)
            meta = ld / "catalogue_meta.json"
            if meta.is_file():
                try:
                    b.generated_at = json.loads(meta.read_text(encoding="utf-8")).get("generated_at")
                except Exception:  # noqa: BLE001 — only the default date is lost
                    pass
        for m in _jsonl(r / "manifest.jsonl"):
            url = m.get("source_url") or ""
            if not url or url in b.stored:
                continue
            d = StoredDocument(doc_id=m.get("doc_id") or "", source_url=url, law_name_guess=m.get("law_name_guess"),
                               access_date=m.get("access_date"), run=r.name)
            b.stored[url] = d
            pid = ((b.documents.get(url) or {}).get("contract_meta") or {}).get("portal_id")
            if pid:
                b.by_portal_id.setdefault(str(pid), d)
    return b
