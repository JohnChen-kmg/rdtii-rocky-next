"""What changed: the portal's listings now, against the baseline run (or a date when there is none)."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Optional

from ..parse import (
    _act_key, _clean, _law_number, choose_document, choose_principal_document, document_as_at, iso_date,
)
from .baseline import Baseline
from .listings import SubsidiaryInstrument

DATE_MODE_NOTE = ("date mode: chosen by date, not by comparison with a run; an act re-uploaded with an older "
                  "as-at date is missed")


@dataclass
class Change:
    kind: str                     # principal | amending | subsidiary | list
    change: str                   # new_act | new_version | status_changed | listing_changed | not_stored | gone
                                  # | new_or_updated | new_amending_act | commencement_changed | new_instrument
                                  # | stored_file_changed | not_in_runs | stored_elsewhere
    portal_id: str
    law_number: str
    law_name: Optional[str]
    reasons: list[str]
    now: dict                     # the listing's values today
    before: dict                  # the baseline's values
    crawl: Optional[bool]         # whether the delta list fetches something for it (None: decided by policy later)
    url: Optional[str] = None     # the document the delta list fetches, when it does
    note: Optional[str] = None

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass
class Changes:
    since: Optional[str]
    mode: str                     # baseline | date
    baseline_run: Optional[str]
    principals: list[Change] = field(default_factory=list)
    amendments: list[Change] = field(default_factory=list)
    subsidiary: list[Change] = field(default_factory=list)
    listed: list[Change] = field(default_factory=list)      # the link list against the runs (--list)
    notes: list[str] = field(default_factory=list)

    def all(self) -> list[Change]:
        return self.principals + self.amendments + self.subsidiary + self.listed

    def summary(self) -> dict:
        counts: dict[str, dict[str, int]] = {}
        for ch in self.all():
            bucket = counts.setdefault(ch.kind, {})
            bucket[ch.change] = bucket.get(ch.change, 0) + 1
        return {"since": self.since, "mode": self.mode, "baseline_run": self.baseline_run, "by_change": counts,
                "to_crawl": sum(1 for ch in self.all() if ch.crawl), "recorded_only": sum(1 for ch in self.all() if not ch.crawl),
                "total": len(self.all())}

    def as_dict(self) -> dict:
        return {"summary": self.summary(), "notes": self.notes,
                "principals": [c.as_dict() for c in self.principals],
                "amendments": [c.as_dict() for c in self.amendments],
                "subsidiary": [c.as_dict() for c in self.subsidiary],
                "listed": [c.as_dict() for c in self.listed]}


def _int(value) -> Optional[int]:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def compare(adapter, baseline: Optional[Baseline], since: Optional[str],
            instruments: list[SubsidiaryInstrument]) -> Changes:
    """Baseline mode compares each listing record with the run's laws.csv row, and reports a listed file that no run
    stored (a failed or skipped fetch) as `not_stored`. Date mode (no baseline) takes acts whose as-at date, amending
    acts whose publication date and instruments whose publication date fall on or after `since`; every such act row
    says that this is approximate."""
    langs = adapter._languages()
    has_state = baseline is not None and (baseline.principals or baseline.amendments)
    mode = "baseline" if has_state else "date"
    out = Changes(since=since, mode=mode, baseline_run=baseline.name if baseline else None)
    if baseline is not None:
        out.notes.extend(baseline.notes)
    stored = baseline.stored if baseline else {}
    dup = baseline.duplicates if baseline else set()

    def unstored(url: Optional[str]) -> bool:
        return bool(has_state and url and url not in stored and url not in dup)

    # --- principal acts
    for key, p in adapter.principals.items():
        doc = choose_principal_document(p, langs)
        as_at = iso_date((document_as_at(p, doc) if doc else None) or p.as_at_bi or p.as_at_bm)
        now = {"document_url": doc.url if doc else None, "as_at": as_at, "status_marker": p.status_marker,
               "documents_offered": len(p.documents), "title": p.title_bi or p.title_bm,
               "language": doc.language if doc else None, "edition": doc.edition if doc else None}
        row = baseline.principals.get(key) if has_state else None
        law_number, name = _law_number(p.act_no), p.title_bi or p.title_bm
        if row is None:
            if has_state:
                out.principals.append(Change("principal", "new_act", p.act_no, law_number, name,
                                             ["not in the baseline listing"], now, {}, crawl=doc is not None,
                                             url=now["document_url"]))
            elif since and as_at and as_at >= since and doc is not None:
                out.principals.append(Change("principal", "new_or_updated", p.act_no, law_number, name,
                                             [f"as-at date {as_at} on or after {since}"], now, {}, crawl=True,
                                             url=now["document_url"], note=DATE_MODE_NOTE))
            continue
        before = {"document_url": row.get("document_url") or None, "as_at": iso_date(row.get("as_at")),
                  "status_marker": row.get("status_marker") or None,
                  "documents_offered": _int(row.get("documents_offered")),
                  "title": row.get("title_bi") or row.get("title_bm") or None}
        reasons = []
        if now["document_url"] != before["document_url"]:
            reasons.append("document")
        if now["as_at"] != before["as_at"]:
            reasons.append("as-at date")
        if (now["status_marker"] or "") != (before["status_marker"] or ""):
            reasons.append("status marker")
        if before["documents_offered"] is not None and now["documents_offered"] != before["documents_offered"]:
            reasons.append("documents offered")
        if _clean(now["title"] or "") != _clean(before["title"] or ""):
            reasons.append("title")
        if not reasons:
            if unstored(now["document_url"]):
                out.principals.append(Change("principal", "not_stored", p.act_no, law_number, name,
                                             ["the listed file is stored by no run (a failed or skipped fetch)"],
                                             now, before, crawl=True, url=now["document_url"]))
            continue
        if "document" in reasons or "as-at date" in reasons:
            change, crawl = "new_version", doc is not None
        elif "status marker" in reasons:
            change, crawl = "status_changed", False
        else:
            change, crawl = "listing_changed", False
        if not crawl and unstored(now["document_url"]):
            change, crawl = "not_stored", True
            reasons.append("the listed file is stored by no run")
        out.principals.append(Change("principal", change, p.act_no, law_number, name, reasons, now, before,
                                     crawl=crawl, url=now["document_url"] if crawl else None,
                                     note=None if crawl else "the file the listing gives is the one already stored"
                                     if now["document_url"] in stored else None))
    if has_state:
        for key, row in baseline.principals.items():
            if key not in adapter.principals:
                out.principals.append(Change("principal", "gone", str(row.get("portal_id")), row.get("law_number") or "",
                                             row.get("title_bi") or row.get("title_bm"), ["no longer listed"], {},
                                             {"document_url": row.get("document_url"), "as_at": iso_date(row.get("as_at")),
                                              "status_marker": row.get("status_marker")}, crawl=False))

    # --- amending acts
    for key, a in adapter.amendments.items():
        doc = choose_document(a.documents, langs)
        now = {"document_url": doc.url if doc else None, "publication_date": iso_date(a.publication),
               "commencement_remark": _clean(a.commencement_remark) or None,
               "commencement_date": _clean(a.commencement_date) or None, "title": a.title_bi or a.title_bm}
        row = baseline.amendments.get(key) if has_state else None
        law_number, name = f"Act {a.a_number}", a.title_bi or a.title_bm
        if row is None:
            if has_state or (since and now["publication_date"] and now["publication_date"] >= since):
                out.amendments.append(Change("amending", "new_amending_act", a.a_number, law_number, name,
                                             ["not in the baseline listing" if has_state
                                              else f"published {now['publication_date']} on or after {since}"],
                                             now, {}, crawl=doc is not None, url=now["document_url"],
                                             note=None if has_state else DATE_MODE_NOTE))
            continue
        before = {"document_url": row.get("document_url") or None, "publication_date": iso_date(row.get("as_at")),
                  "commencement_remark": _clean(row.get("commencement_remark") or "") or None}
        reasons = []
        if now["document_url"] != before["document_url"]:
            reasons.append("document")
        if (now["commencement_remark"] or "") != (before["commencement_remark"] or ""):
            reasons.append("commencement remark")
        if before["publication_date"] and now["publication_date"] != before["publication_date"]:
            reasons.append("publication date")
        if not reasons:
            if unstored(now["document_url"]):
                out.amendments.append(Change("amending", "not_stored", a.a_number, law_number, name,
                                             ["the listed file is stored by no run (a failed or skipped fetch)"],
                                             now, before, crawl=True, url=now["document_url"]))
            continue
        if "document" in reasons or unstored(now["document_url"]):
            change, crawl, note = ("new_version" if "document" in reasons else "not_stored"), doc is not None, None
            if "document" not in reasons:
                reasons.append("the listed file is stored by no run")
        else:
            change, crawl = "commencement_changed", True
            note = "the act's own file is unchanged; its detail page is re-read for a commencement order"
        out.amendments.append(Change("amending", change, a.a_number, law_number, name, reasons, now, before,
                                     crawl=crawl, url=now["document_url"] if change != "commencement_changed" else None,
                                     note=note))
    if has_state:
        for key, row in baseline.amendments.items():
            if key not in adapter.amendments:
                out.amendments.append(Change("amending", "gone", str(row.get("portal_id")), row.get("law_number") or "",
                                             row.get("title_bi") or row.get("title_bm"), ["no longer listed"], {},
                                             {"document_url": row.get("document_url"),
                                              "publication_date": iso_date(row.get("as_at"))}, crawl=False))

    # --- subsidiary legislation, from the P.U. listings (newest first, already cut at the look-back floor)
    seen: set[str] = set()
    for inst in instruments:
        if inst.pu_no in seen:
            continue
        seen.add(inst.pu_no)
        if inst.url and (inst.url in stored or inst.url in dup):
            continue
        now = {"kind": inst.kind, "url": inst.url, "publication_date": inst.publication_date, "status": inst.status,
               "act_no": inst.act_no, "principal_law_number": _law_number(inst.act_no) if inst.act_no else None,
               "project_id": inst.project_id, "related": inst.related, "commencement": inst.commencement,
               "title": inst.title_bi or inst.title_bm}
        out.subsidiary.append(Change("subsidiary", "new_instrument", inst.pu_no, inst.pu_no,
                                     inst.title_bi or inst.title_bm,
                                     [f"published {inst.publication_date or 'undated'}, not stored by any run"],
                                     now, {}, crawl=None, url=inst.url))
    return out


def by_portal_id(changes: Changes, kind: str) -> dict[str, Change]:
    key = (lambda c: _act_key(c.portal_id)) if kind == "principal" else (lambda c: c.portal_id.upper())
    return {key(c): c for c in changes.all() if c.kind == kind}
