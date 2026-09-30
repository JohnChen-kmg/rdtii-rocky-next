"""The delta list: the documents to crawl for what changed, in the link-file format the crawl replays.

Rows are built by **the same adapter code the full list uses** (`_register_candidate`), with the same settings, so
a delta row and a full-list row for the same title are identical but for `contract_meta.update`, which records
what changed, the version the baseline held and the document it stored for it.

`write` is the catalogue's own writer, so the folder holds the same five files a full list does.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from ..catalogue import _CANDIDATE_FIELDS, cfg_fingerprint, law_rows, scraper_hashes
from .diff import Changes


def build_delta(adapter, changes: Changes, found: dict, pillars: list[int],
                api_log: Optional[list] = None) -> dict[str, Any]:
    """A catalogue-shaped result holding one row per changed title."""
    titles, versions = found.get("titles") or {}, found.get("versions") or {}
    for tid, t in titles.items():
        adapter.titles.setdefault(tid, t)
    for tid, v in versions.items():
        adapter.versions.setdefault(tid, v)

    seeds = adapter._seed_by_id(pillars)
    relevant = adapter._relevant_ids()
    documents: list[dict] = []
    for ch in changes.to_fetch:
        pid = ch.portal_id
        cand = adapter._register_candidate(pid, adapter.titles.get(pid), adapter.versions.get(pid),
                                           seeds.get(pid), relevant=pid in relevant)
        if cand is None or not cand.url:
            changes.notes.append(f"{pid}: no address could be built, so it is recorded and not fetched")
            continue
        meta = dict(cand.contract_meta)
        meta["discovery_path"] = "delta"
        meta["update"] = {"change": ch.change, "version_id": ch.version_id,
                          "previous_version_id": ch.previous_version_id, "registered_at": ch.registered_at,
                          "start": ch.start, "baseline_doc_id": ch.stored_doc_id,
                          "baseline_access_date": ch.stored_access_date}
        is_seed = pid in seeds
        row = {name: getattr(cand, name) for name in _CANDIDATE_FIELDS}
        row.update({"order": len(documents) + 1,
                    "scopes": [s for s, on in (("seed", is_seed), ("relevant", is_seed or pid in relevant),
                                               ("all", True)) if on],
                    "contract_meta": meta})
        documents.append(row)

    laws = law_rows(adapter, documents)
    counts = {scope: sum(1 for d in documents if scope in d["scopes"]) for scope in ("all", "seed", "relevant")}
    kinds: dict[str, int] = {}
    for d in documents:
        k = d["contract_meta"].get("document_kind") or "agency_or_other"
        kinds[k] = kinds.get(k, 0) + 1
    log = list(api_log or [])
    meta = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "economy": "AU", "pillars": pillars, "counts": counts, "document_kinds": kinds,
        "settings": adapter.effective_settings(("detail_pages", "version_batch", "title_page_size",
                                                "max_titles", "collection", "document_form")),
        "cfg_sha256": cfg_fingerprint(adapter.cfg),
        "seed_keys": [[law.get("law_name"), law.get("law_number"), law.get("url")]
                      for law in adapter.cfg.get("seed_laws") or []],
        "requests": len(log), "api_requests": len(log), "www_requests": 0,
        "robots_record": adapter.robots_record, "register_error": adapter.register_error,
        "harvest": adapter.harvest_counts, "versions_read": len(adapter.versions),
        "notes": list(adapter.notes) + list(changes.notes), "scraper_sha256": scraper_hashes(),
        "update": {"since": changes.since, "checked_at": changes.checked_at, "prefixes": changes.prefixes,
                   "counts": changes.counts(), "requests": changes.requests, "dropped_series": changes.dropped,
                   "baseline_run": None},
    }
    return {"documents": documents, "laws": laws, "meta": meta, "discovery_log": log}


def write_changes(out_dir: str | Path, changes: Changes, extra: Optional[dict] = None) -> dict[str, str]:
    """`changes.json` and `changes.md`: everything the check found, fetched or not."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    payload = {"economy": "AU", "since": changes.since, "checked_at": changes.checked_at,
               "prefixes": changes.prefixes, "requests": changes.requests, "counts": changes.counts(),
               "dropped_series": changes.dropped, "notes": changes.notes,
               "changes": [c.as_dict() for c in changes.changes], **(extra or {})}
    (out / "changes.json").write_text(json.dumps(payload, ensure_ascii=False, indent=1, default=str),
                                      encoding="utf-8", newline="\n")
    (out / "changes.md").write_text(changes_markdown(changes, extra or {}), encoding="utf-8", newline="\n")
    return {"changes.json": str(out / "changes.json"), "changes.md": str(out / "changes.md")}


def _cell(text: Any) -> str:
    return " ".join(str(text if text is not None else "").split()).replace("|", "\\|")


def changes_markdown(changes: Changes, extra: dict) -> str:
    counts = changes.counts()
    lines = [f"# What changed on the Federal Register since {changes.since}", "",
             f"Checked {changes.checked_at} with {changes.requests} API request(s), prefixes "
             f"{', '.join(changes.prefixes) or '-'}. "
             f"**{len(changes.to_fetch)} document(s) to fetch**, "
             f"{counts.get('unchanged', 0)} title(s) checked and unchanged"
             + (f", {counts.get('repealed', 0)} repealed or ceased" if counts.get("repealed") else "") + ".", ""]
    if extra.get("baseline_run"):
        lines += [f"Baseline: `{extra['baseline_run']}`"
                  + (f", whose list was built {extra.get('baseline_generated_at')}"
                     if extra.get("baseline_generated_at") else "") + ".", ""]
    if counts:
        lines += ["| What | Titles |", "| :---- | ----: |"] + \
                 [f"| {k.replace('_', ' ')} | {v} |" for k, v in sorted(counts.items())] + [""]
    if changes.dropped:
        lines += ["Dropped as not legislation (the `C` prefix is shared): "
                  + ", ".join(f"{v} in series {k}" for k, v in sorted(changes.dropped.items())) + ".", ""]
    rows = [c for c in changes.changes if c.change != "unchanged"]
    if rows:
        lines += ["## Every change", "",
                  "| What | Law | Number | New version | Baseline version | In force from | Registered |",
                  "| :---- | :---- | :---- | :---- | :---- | :---- | :---- |"]
        for c in rows:
            lines.append(f"| {c.change.replace('_', ' ')} | {_cell(c.law_name)} | {_cell(c.law_number)} | "
                         f"{_cell(c.version_id)} | {_cell(c.previous_version_id)} | {_cell((c.start or '')[:10])} | "
                         f"{_cell((c.registered_at or '')[:10])} |")
        lines.append("")
    unchanged = [c for c in changes.changes if c.change == "unchanged"]
    if unchanged:
        lines += ["## Checked and unchanged", "",
                  "The register re-registered these versions since the baseline, but the version id is the one we "
                  "already hold, so no document is fetched.", "",
                  "| Law | Version | Registered |", "| :---- | :---- | :---- |"]
        for c in unchanged:
            lines.append(f"| {_cell(c.law_name)} | {_cell(c.version_id)} | {_cell((c.registered_at or '')[:10])} |")
        lines.append("")
    if changes.notes:
        lines += ["## Notes", ""] + [f"- {n}" for n in changes.notes] + [""]
    if not changes.changes:
        lines += ["Nothing changed.", ""]
    return "\n".join(lines)
