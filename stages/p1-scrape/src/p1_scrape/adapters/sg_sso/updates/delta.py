"""The delta list and the record of a check.

Rows are built by **the adapter's own row builders** (`_principal_candidate`, `_acts_supp_candidate`,
`_sl_candidate`), so a delta row and a full-list row for the same document are identical but for
`contract_meta.update`, which says what changed, the version the baseline recorded, the new one, and the document
the baseline stored.

`laws.csv` is written for **every listed act**, not only the changed ones. Acts whose timeline this check read get
their fresh version date; every other act keeps the one the baseline recorded. That makes the check's own run
folder a complete baseline for the next check, which is how checks chain without ever rebuilding the full list.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from ..catalogue import _CANDIDATE_FIELDS, cfg_fingerprint, law_rows, scraper_hashes
from .diff import Changes

# the fields a check leaves as the baseline recorded them when it did not re-read the act's timeline
_VERSION_FIELDS = ("version_as_at", "published_on", "detail_read", "versions_listed", "amendments_listed",
                   "last_amending_instrument", "revised_edition", "subsidiary_listed")
# the fields that describe what a run fetched, kept from the baseline for an act this check did not fetch
_FETCH_FIELDS = ("document_url", "in_seed", "in_relevant", "in_all", "document_kinds", "not_crawled_reason")


def build_delta(adapter, changes: Changes, baseline, pillars: list[int], relevant: set,
                log: Optional[list] = None) -> dict[str, Any]:
    current = {r.code: r for r in adapter.listed.get("current", [])}
    supp = {r.code: r for r in adapter.listed.get("acts_supp", [])}
    seeds = adapter._seed_by_code(pillars)[0]
    documents: list[dict] = []
    for ch in changes.to_fetch:
        cand, is_seed = None, ch.portal_id in seeds
        if ch.listing == "current":
            row = current.get(ch.portal_id)
            if row is not None:
                cand = adapter._principal_candidate(row, adapter.details.get(ch.portal_id), seeds.get(ch.portal_id),
                                                    relevant=ch.portal_id in relevant)
        elif ch.listing == "acts_supp":
            row = supp.get(ch.portal_id)
            cand = adapter._acts_supp_candidate(row, current) if row is not None else None
            if cand is None and row is not None:
                changes.notes.append(f"{ch.portal_id} ({row.title}): a new principal act whose consolidated text the "
                                     f"Current listing already carries, so it comes from there, not the supplement")
                continue
        elif ch.listing == "regulation":
            sl = next((s for s in adapter.subsidiary.get(ch.parent or "", []) if s.code == ch.portal_id), None)
            parent = current.get(ch.parent or "")
            if sl is not None and parent is not None:
                cand = adapter._sl_candidate(sl, ch.parent, parent, law=None)
                is_seed = ch.parent in seeds
        if cand is None or not cand.url:
            changes.notes.append(f"{ch.portal_id}: no address could be built, so it is recorded and not fetched")
            continue
        meta = dict(cand.contract_meta)
        meta["discovery_path"] = "delta"
        meta["update"] = {"change": ch.change, "since": changes.since, "in_force_from": ch.in_force_from,
                          "previous_version": ch.previous_version, "amended_by": ch.amended_by,
                          "published_on": ch.published_on, "baseline_doc_id": ch.stored_doc_id}
        row = {name: getattr(cand, name) for name in _CANDIDATE_FIELDS}
        rel = is_seed or ch.portal_id in relevant or (ch.parent in relevant if ch.parent else False)
        row.update({"order": len(documents) + 1,
                    "scopes": [s for s, on in (("seed", is_seed), ("relevant", rel), ("all", True)) if on],
                    "contract_meta": meta})
        documents.append(row)

    laws = carried_forward(adapter, baseline, documents)
    counts = {scope: sum(1 for d in documents if scope in d["scopes"]) for scope in ("all", "seed", "relevant")}
    kinds: dict[str, int] = {}
    for d in documents:
        k = d["contract_meta"].get("document_kind") or "agency_or_other"
        kinds[k] = kinds.get(k, 0) + 1
    log = list(log or [])
    meta = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "economy": "SG", "pillars": pillars, "counts": counts, "document_kinds": kinds,
        "settings": adapter.effective_settings(("detail_pages", "subsidiary_acts", "subsidiary_max_per_act",
                                                "acts_supp_years", "listing_paging", "listing_rows",
                                                "listing_page_size", "read_repealed")),
        "accepted_retries": adapter.accepted_retries, "cfg_sha256": cfg_fingerprint(adapter.cfg),
        "seed_keys": [[law.get("law_name"), law.get("law_number"), law.get("url")]
                      for law in adapter.cfg.get("seed_laws") or []],
        "requests": len(log), "robots_record": adapter.robots_record, "sso_error": adapter.sso_error,
        "listing_counts": adapter.listing_counts, "detail_pages_read": len(adapter.details),
        "sl_tabs_read": len(adapter.subsidiary), "notes": list(changes.notes), "scraper_sha256": scraper_hashes(),
        "update": {"since": changes.since, "checked_at": changes.checked_at, "counts": changes.counts(),
                   "requests": changes.requests, "timelines_read": changes.timelines_read,
                   "baseline_run": baseline.run.name if (baseline is not None and baseline.run) else None},
    }
    return {"documents": documents, "laws": laws, "meta": meta, "discovery_log": log}


def carried_forward(adapter, baseline, documents: list[dict]) -> list[dict]:
    """Every listed act now, each with the freshest version date anyone has read."""
    fresh = law_rows(adapter, documents)
    if baseline is None:
        return fresh
    fetched = {str(d["contract_meta"].get("portal_id")) for d in documents}
    seen = set()
    for row in fresh:
        pid = row["portal_id"]
        seen.add(pid)
        old = baseline.laws.get(pid)
        if old is None:
            continue
        if pid not in adapter.details:
            for k in _VERSION_FIELDS:
                row[k] = old.get(k)
        if pid not in fetched:
            for k in _FETCH_FIELDS:
                row[k] = old.get(k)
    # an act the baseline listed that no listing carries now: kept, so the next check can still say what happened
    for pid, old in baseline.laws.items():
        if pid not in seen:
            fresh.append(dict(old, not_crawled_reason=(old.get("not_crawled_reason") or "")
                              + ("; " if old.get("not_crawled_reason") else "") + "not on any listing at this check"))
    return fresh


def write_changes(out_dir: str | Path, changes: Changes, extra: Optional[dict] = None) -> dict[str, str]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    payload = {"economy": "SG", "since": changes.since, "checked_at": changes.checked_at,
               "requests": changes.requests, "timelines_read": changes.timelines_read, "counts": changes.counts(),
               "notes": changes.notes, "changes": [c.as_dict() for c in changes.changes], **(extra or {})}
    (out / "changes.json").write_text(json.dumps(payload, ensure_ascii=False, indent=1, default=str),
                                      encoding="utf-8", newline="\n")
    (out / "changes.md").write_text(changes_markdown(changes, extra or {}), encoding="utf-8", newline="\n")
    return {"changes.json": str(out / "changes.json"), "changes.md": str(out / "changes.md")}


def _cell(value: Any) -> str:
    return " ".join(str(value if value is not None else "").split()).replace("|", "\\|")


_HEAD = {
    "new_act": "New acts",
    "new_publication": "New in the Acts Supplement",
    "amended": "Amended",
    "new_regulation": "New regulations under the seed acts",
    "amended_file_pending": "Amended, but the portal has no file for the new version yet",
    "repealed": "Repealed",
    "not_checked": "Not checked: the cap on timeline reads was reached",
    "regenerated": "File regenerated, law unchanged",
}


def changes_markdown(changes: Changes, extra: dict) -> str:
    counts = changes.counts()
    fetch = len(changes.to_fetch)
    lines = [f"# What changed on Singapore Statutes Online since {changes.since}", "",
             f"Checked {changes.checked_at} with {changes.requests} request(s), {changes.timelines_read} act "
             f"timeline(s) read. **{fetch} document(s) to fetch**"
             + (f", {counts.get('repealed', 0)} repeal(s) reported" if counts.get("repealed") else "")
             + (f", {counts.get('not_checked', 0)} act(s) left unchecked by the cap" if counts.get("not_checked") else "")
             + ".", ""]
    if extra.get("baseline_run"):
        lines += [f"Baseline: `{extra['baseline_run']}`"
                  + (f", whose list was built {extra.get('baseline_generated_at')}" if extra.get("baseline_generated_at")
                     else "") + ".", ""]
    lines += ["An amendment is decided by the **in-force date on the act's own timeline**, compared with the version "
              "date the baseline recorded. A publication date is never used for it, because an amending act can be "
              "published years before it takes effect.", ""]
    if counts:
        lines += ["| What | Count |", "| :---- | ----: |"] + \
                 [f"| {_HEAD.get(k, k)} | {counts[k]} |" for k in _HEAD if k in counts] + [""]
    for kind in _HEAD:
        rows = [c for c in changes.changes if c.change == kind]
        if not rows:
            continue
        lines += [f"## {_HEAD[kind]}", ""]
        if kind in ("amended", "amended_file_pending", "regenerated"):
            lines += ["| Law | In force from | Recorded before | Amended by | File generated |",
                      "| :---- | :---- | :---- | :---- | :---- |"]
            lines += [f"| {_cell(c.law_name)} | {_cell(c.in_force_from)} | {_cell(c.previous_version)} | "
                      f"{_cell(c.amended_by)} | {_cell(c.file_stamp)} |" for c in rows]
        elif kind == "repealed":
            lines += ["| Law | Repealed on | Note |", "| :---- | :---- | :---- |"]
            lines += [f"| {_cell(c.law_name)} | {_cell(c.repeal_date)} | {_cell(c.note)} |" for c in rows]
        elif kind == "not_checked":
            lines += ["| Law | File generated | Recorded version |", "| :---- | :---- | :---- |"]
            lines += [f"| {_cell(c.law_name)} | {_cell(c.file_stamp)} | {_cell(c.previous_version)} |" for c in rows]
        else:
            lines += ["| Law | Number | Date | Note |", "| :---- | :---- | :---- | :---- |"]
            lines += [f"| {_cell(c.law_name)} | {_cell(c.law_number)} | {_cell(c.published_on or c.in_force_from)} | "
                      f"{_cell(c.note)} |" for c in rows]
        lines.append("")
    if changes.notes:
        lines += ["## Notes", ""] + [f"- {n}" for n in changes.notes] + [""]
    if not changes.changes:
        lines += ["Nothing changed.", ""]
    return "\n".join(lines)
