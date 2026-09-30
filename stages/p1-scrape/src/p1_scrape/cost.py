"""Per-stage RAW measured counters → handoff1/cost_report.json (§7).

P1 emits ONLY raw counters (wall-clock, bytes, requests, method mix, docs). It does
NOT convert to USD — that would require a rate assumption (an estimate), which the
'REAL MEASURED' constraint forbids. Project 3 owns the consolidated USD roll-up.
"""
from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from .models import FetchResult


@dataclass
class CostMeter:
    request_count: int = 0
    total_bytes: int = 0
    docs_retrieved: int = 0
    retrieval_method_mix: Counter = field(default_factory=Counter)

    def record_fetch(self, result: FetchResult) -> None:
        self.request_count += 1
        self.total_bytes += len(result.content or b"")
        if result.ok:
            self.retrieval_method_mix[result.http.retrieval_method] += 1

    def record_doc(self) -> None:
        self.docs_retrieved += 1

    def write(self, out_dir: Path, wall_clock_seconds: float) -> Path:
        path = Path(out_dir) / "cost_report.json"
        payload = {
            "stage": "p1-scrape",
            "wall_clock_seconds": round(wall_clock_seconds, 3),
            "total_bytes": self.total_bytes,
            "request_count": self.request_count,
            "docs_retrieved": self.docs_retrieved,
            "retrieval_method_mix": dict(self.retrieval_method_mix),
            "note": "raw measured counters only; USD roll-up deferred to Project 3 (§7).",
        }
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return path
