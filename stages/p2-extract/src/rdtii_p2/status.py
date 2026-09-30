"""doc_status.jsonl bookkeeping (PLAN.md section 2.3.1, finding #4).

Absence of a record is ambiguous; exactly one status row per touched Manifest
doc lets P3 distinguish "law parsed, nothing citable" (write a No-provision
row) from "cost-aborted / parse-failed" (do NOT fabricate an absence row).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

VALID_STATUSES = {"ok", "zero_provisions", "cost_aborted", "parse_failed",
                  # decided before any processing, by sidecars.DocFacts.decide()
                  "excluded", "skipped"}


@dataclass
class DocStatus:
    doc_id: str
    status: str                    # ok | zero_provisions | cost_aborted | parse_failed
    n_provisions: int
    lane: str | None               # A | B | C (post-reroute), None if never routed
    reason: str | None
    source_type_final: str | None
    doc_cer: float | None = None
    # what collection knew about the document, carried so coverage is reportable and a
    # judge can see why a document was not read rather than finding it simply absent
    language_of_source: str | None = None
    language_source: str | None = None
    content_flags: list | None = None
    use: list | None = None
    document_kind: list | None = None
    legal_status: list | None = None
    act_count: int | None = None

    def __post_init__(self) -> None:
        if self.status not in VALID_STATUSES:
            raise ValueError(f"invalid doc status {self.status!r}")
        if self.status != "ok" and self.n_provisions != 0:
            raise ValueError(
                f"{self.doc_id}: non-ok status {self.status!r} must carry 0 provisions"
            )
        if self.status == "ok" and self.n_provisions < 1:
            raise ValueError(f"{self.doc_id}: status ok requires >= 1 provision")
        if self.status in {"excluded", "skipped"} and not self.reason:
            raise ValueError(f"{self.doc_id}: {self.status} requires a reason")

    def to_dict(self) -> dict:
        return asdict(self)
