"""What a check writes: the delta list the crawl replays, the full census, and `changes.md` for a person.

The delta list is built by the **adapter's own candidate builder**, so a delta row is the same shape as a row of
the full list; only `contract_meta.update` is added, saying what changed and what the baseline held. `laws.csv` is
the whole listing as read today — not only the changed acts — so the run folder is a complete baseline for the
next check.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from ..catalogue import _CANDIDATE_FIELDS, cfg_fingerprint, law_rows, scraper_hashes
from .diff import Changes


def build_delta(adapter, changes: Changes, baseline, pillars: list[int], log=None) -> dict[str, Any]:
    """The rows to crawl (the changed issues) and the census of every act the portal lists."""
    all_cands = adapter._build_candidates(pillars, scope="all")
    seeds, _others = adapter._seed_by_number(pillars)
    relevant = adapter._relevant_codes()
    census = []
    for order, (url, cand) in enumerate(all_cands.items(), start=1):
        row = {name: getattr(cand, name) for name in _CANDIDATE_FIELDS}
        row.update({"order": order, "scopes": ["all"], "contract_meta": cand.contract_meta})
        census.append(row)

    by_url = {row["url"]: row for row in census}
    documents = []
    for order, change in enumerate(changes.to_fetch, start=1):
        row = by_url.get(change.document_url)
        if row is None:
            changes.notes.append(f"{change.portal_id}: {change.document_url} is not in today's listing; not queued")
            continue
        meta = dict(row["contract_meta"])
        meta["update"] = {"change": change.change, "portal_id": change.portal_id,
                          "previous_document_url": change.previous_document_url,
                          "baseline_doc_id": change.stored_doc_id,
                          "baseline_run": baseline.run.name if (baseline and baseline.run) else None,
                          "since": changes.since, "note": change.note}
        documents.append({**row, "order": order, "scopes": ["all"], "contract_meta": meta})

    laws = law_rows(adapter, census, relevant, seeds)
    counts = {"all": len(documents)}
    kinds: dict[str, int] = {}
    for d in documents:
        k = d["contract_meta"].get("document_kind") or "agency_or_other"
        kinds[k] = kinds.get(k, 0) + 1
    log = list(log or [])
    meta = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "economy": "TL", "pillars": pillars, "counts": counts, "document_kinds": kinds,
        "settings": adapter.effective_settings(("categories", "document_form", "root")),
        "cfg_sha256": cfg_fingerprint(adapter.cfg),
        "seed_keys": [[law.get("law_name"), law.get("law_number"), law.get("portal_key")]
                      for law in adapter.cfg.get("seed_laws") or []],
        "requests": len(log), "robots_record": adapter.robots_record, "jornal_error": adapter.jornal_error,
        "listing_counts": adapter.listing_counts, "acts_listed": len(laws),
        "documents_distinct": len(all_cands), "notes": list(changes.notes), "scraper_sha256": scraper_hashes(),
        "update": {"since": changes.since, "checked_at": changes.checked_at, "counts": changes.counts(),
                   "requests": changes.requests,
                   "baseline_run": baseline.run.name if (baseline and baseline.run) else None},
    }
    return {"documents": documents, "laws": laws, "meta": meta, "discovery_log": log}


def write_changes(run_dir: str | Path, changes: Changes, extra: Optional[dict] = None) -> dict:
    """`changes.json` for a machine, `changes.md` for a person."""
    run = Path(run_dir)
    run.mkdir(parents=True, exist_ok=True)
    payload = {"economy": "TL", "since": changes.since, "checked_at": changes.checked_at,
               "requests": changes.requests, "counts": changes.counts(),
               "changes": [c.as_dict() for c in changes.changes if c.change != "unchanged"],
               "unchanged": sum(1 for c in changes.changes if c.change == "unchanged"),
               "to_fetch": [c.document_url for c in changes.to_fetch], "notes": changes.notes, **(extra or {})}
    (run / "changes.json").write_text(json.dumps(payload, ensure_ascii=False, indent=1, default=str),
                                      encoding="utf-8")
    (run / "changes.md").write_text(changes_markdown(changes, extra or {}), encoding="utf-8", newline="\n")
    return {"changes.json": str(run / "changes.json"), "changes.md": str(run / "changes.md")}


def changes_markdown(changes: Changes, extra: dict) -> str:
    counts = changes.counts()
    lines = [f"# What changed on the Jornal da República since {changes.since or 'the last run'}", "",
             f"Checked {changes.checked_at} with {changes.requests} request(s). "
             f"**{len(changes.to_fetch)} document(s) to fetch**.", ""]
    if extra.get("baseline_run"):
        lines += [f"Baseline: `{extra['baseline_run']}`, whose list was built {extra.get('baseline_generated_at')}.",
                  ""]
    lines += ["The gazette is append-only: it publishes acts and never revises an issue, and it states no status.",
              "So a change here is a new act, a file that moved, or an act the portal stopped listing — never an",
              "amended text. An amending act is a new act that names the one it alters.", ""]
    interesting = [c for c in changes.changes if c.change != "unchanged"]
    if interesting:
        lines += ["| Change | Act | Number | Published | Document |", "| :---- | :---- | :---- | :---- | :---- |"]
        for c in sorted(interesting, key=lambda c: (c.change, c.published_on or "")):
            name = (c.law_name or "")[:70]
            doc = (c.document_url or "").rsplit("/", 1)[-1] if c.document_url else "—"
            lines.append(f"| `{c.change}` | {name} | {c.law_number or '—'} | {c.published_on or '—'} | {doc} |")
        lines.append("")
    lines += ["## Counts", "", "| Verdict | Acts |", "| :---- | ----: |"]
    for verdict, n in sorted(counts.items()):
        lines.append(f"| `{verdict}` | {n} |")
    if changes.notes:
        lines += ["", "## Notes", ""] + [f"- {n}" for n in changes.notes]
    if not interesting:
        lines += ["", "Nothing changed."]
    return "\n".join(lines) + "\n"
