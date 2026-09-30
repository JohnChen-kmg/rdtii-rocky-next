"""Tier-1 inventory: the complete act/regulation listing per portal (title+URL+date).

Pillar-agnostic and cheap (a few browse-page fetches) — it enumerates EVERYTHING on
the portal so nothing is invisible, powers the Tier-2 relevance filter, and is an
auditable side artifact (handoff1/inventory_<cc>.csv/.jsonl). Reusable for any future
pillar with zero code change.
"""
from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class InventoryItem:
    economy: str
    law_name: str
    url: str
    law_number: Optional[str] = None
    listing_date: Optional[str] = None
    download_url: Optional[str] = None
    source: str = "browse"          # browse | search | seed
    relevant: bool = False          # matched the Tier-2 relevance net
    matched_terms: list[str] = field(default_factory=list)
    # Legal metadata harvested at discovery (v0.2.0).
    publication_date: Optional[str] = None
    assent_date: Optional[str] = None
    commencement_date: Optional[str] = None
    in_force_status: Optional[str] = None

    def as_dict(self) -> dict:
        return {
            "economy": self.economy,
            "law_name": self.law_name,
            "law_number": self.law_number,
            "url": self.url,
            "listing_date": self.listing_date,
            "download_url": self.download_url,
            "source": self.source,
            "relevant": self.relevant,
            "matched_terms": ",".join(self.matched_terms) or None,
            "publication_date": self.publication_date,
            "assent_date": self.assent_date,
            "commencement_date": self.commencement_date,
            "in_force_status": self.in_force_status,
        }


_FIELDS = ["economy", "law_name", "law_number", "url", "listing_date",
           "download_url", "source", "relevant", "matched_terms",
           "publication_date", "assent_date", "commencement_date", "in_force_status"]


def write_inventory(economy: str, items: list[InventoryItem], out_dir: Path) -> tuple[Path, Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    cc = economy.lower()
    csv_path = out_dir / f"inventory_{cc}.csv"
    jsonl_path = out_dir / f"inventory_{cc}.jsonl"
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=_FIELDS)
        w.writeheader()
        for it in items:
            d = it.as_dict()
            w.writerow({k: ("" if d[k] is None else d[k]) for k in _FIELDS})
    with jsonl_path.open("w", encoding="utf-8") as fh:
        for it in items:
            fh.write(json.dumps(it.as_dict(), ensure_ascii=False) + "\n")
    return csv_path, jsonl_path
