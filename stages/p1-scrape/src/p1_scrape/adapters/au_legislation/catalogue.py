"""The link list for Australia: every in-force principal Act the register lists and every document to crawl.

    python -m p1_scrape.adapters.au_legislation.catalogue --out <dir> [--registry sources.yaml --seeds seed_laws.yaml]

reads the register's API once (robots.txt on both hosts, the title harvest, the latest version of every act in
batches of 18, the seeds' titles) and writes the same five files the other countries' steps write
(CONVENTIONS.md section 2): documents.jsonl, documents.csv, laws.csv, catalogue_meta.json, discovery_log.jsonl.
No www page is read: the dated document address comes from the version's start date (api.py). The crawl then
replays documents.jsonl (register.frontier: links_file) at the www host's Crawl-delay of 10 s.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from ..my_gazette.catalogue import _CANDIDATE_FIELDS, _cell, _write_csv, read_documents
from .adapter import _STATUS as STATUS

__all__ = ["build", "cfg_fingerprint", "law_rows", "main", "read_documents", "write"]   # read_documents is shared

_LAW_COLUMNS = ["series", "portal_id", "law_number", "title", "is_principal", "legal_status", "version_as_at",
                "version_id", "compilation_number", "published_on", "amendments_listed", "last_amending_instrument",
                "document_url", "in_seed", "in_relevant", "in_all", "document_kinds", "not_crawled_reason"]
_DOC_COLUMNS = ["order", "scopes", "url", "document_kind", "law_number_guess", "law_name_guess", "portal_id",
                "version_id", "language", "version_as_at", "text_version", "legal_status", "last_amending_instrument",
                "discovery_path", "seed_provenance", "indicator_hints", "crawl_flags", "review_flags"]


def cfg_fingerprint(cfg: dict) -> str:
    reg = {k: v for k, v in (cfg.get("register") or {}).items() if k not in ("frontier", "links_file")}
    payload = {"seed_laws": cfg.get("seed_laws") or [], "register": reg, "seed_queries": cfg.get("seed_queries")}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()


def build(adapter, pillars: list[int], fetcher=None) -> dict[str, Any]:
    adapter._frontier_override = "discover"
    all_cands = adapter.discover(pillars=pillars, scope="all", fetcher=fetcher)
    api = adapter._api
    seeds = adapter._seed_by_id(pillars)
    seed_urls = {law.get("url") for law in adapter.cfg.get("seed_laws") or []}
    relevant = adapter._relevant_ids()
    rank = {"seed": 0, "relevant": 1, "all": 2}
    rows = []
    for i, c in enumerate(all_cands):
        meta = c.contract_meta
        is_seed = meta.get("discovery_path") == "seed" or c.url in seed_urls or meta.get("portal_id") in seeds
        rel = is_seed or meta.get("portal_id") in relevant
        scopes = [s for s, on in (("seed", is_seed), ("relevant", rel), ("all", True)) if on]
        rows.append((min(rank[s] for s in scopes), i, c, scopes))
    rows.sort(key=lambda t: (t[0], t[1]))
    documents = []
    for order, (_r, _i, c, scopes) in enumerate(rows, start=1):
        row = {name: getattr(c, name) for name in _CANDIDATE_FIELDS}
        row.update({"order": order, "scopes": scopes, "contract_meta": c.contract_meta})
        documents.append(row)
    laws = law_rows(adapter, documents)
    counts = {scope: sum(1 for d in documents if scope in d["scopes"]) for scope in ("all", "seed", "relevant")}
    kinds: dict[str, int] = {}
    for d in documents:
        k = d["contract_meta"].get("document_kind") or "agency_or_other"
        kinds[k] = kinds.get(k, 0) + 1
    log = list(api.log) + (list(adapter._www.log) if adapter._www is not None else [])
    meta = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "economy": "AU", "pillars": pillars, "counts": counts, "document_kinds": kinds,
        "settings": adapter.effective_settings(("detail_pages", "version_batch", "title_page_size", "max_titles",
                                                "collection", "document_form")),
        "cfg_sha256": cfg_fingerprint(adapter.cfg),
        "seed_keys": [[law.get("law_name"), law.get("law_number"), law.get("url")] for law in adapter.cfg.get("seed_laws") or []],
        "requests": len(log), "api_requests": len(api.log), "www_requests": len(adapter._www.log) if adapter._www is not None else 0,
        "robots_record": adapter.robots_record, "register_error": adapter.register_error,
        "harvest": adapter.harvest_counts, "versions_read": len(adapter.versions),
        "notes": list(adapter.notes), "scraper_sha256": scraper_hashes(),
    }
    return {"documents": documents, "laws": laws, "meta": meta, "discovery_log": log}


def law_rows(adapter, documents: list[dict]) -> list[dict]:
    by_portal: dict[str, list[dict]] = {}
    for d in documents:
        pid = d["contract_meta"].get("portal_id")
        if pid:
            by_portal.setdefault(str(pid), []).append(d)
    out = []
    for t in adapter.titles.values():
        v = adapter.versions.get(t.id)
        docs = by_portal.get(t.id, [])
        scopes = {s for d in docs for s in d["scopes"]}
        reason = None
        if not docs:
            reason = ("an amending or consequential act: the register compiles it into the principal act (decision 13)"
                      if not t.is_principal else "not selected")
        out.append({
            "series": t.id[:1], "portal_id": t.id, "law_number": t.law_number, "title": t.name, "is_principal": t.is_principal,
            "legal_status": docs[0]["contract_meta"].get("legal_status") if docs else STATUS.get(t.status or "", "unknown"),
            "version_as_at": v.start if v else None, "version_id": v.register_id if v else None,
            "compilation_number": v.compilation_number if v else None, "published_on": v.registered_at if v else None,
            "amendments_listed": len(v.amendments) if v else None,
            "last_amending_instrument": v.last_amending_instrument if v else None,
            "document_url": docs[0]["url"] if docs else None,
            "in_seed": "seed" in scopes, "in_relevant": "relevant" in scopes, "in_all": "all" in scopes,
            "document_kinds": sorted({d["contract_meta"].get("document_kind") or "" for d in docs}),
            "not_crawled_reason": reason,
        })
    return out


def scraper_hashes() -> dict[str, str]:
    here = Path(__file__).parent
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(here.glob("*.py"))}


def write(result: dict[str, Any], out_dir: str | Path, registry_files: Optional[dict[str, str]] = None) -> dict:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    meta = dict(result["meta"])
    if registry_files:
        meta["registry_sha256"] = {name: hashlib.sha256(Path(path).read_bytes()).hexdigest() for name, path in registry_files.items()}
    paths = {name: out / name for name in ("documents.jsonl", "documents.csv", "laws.csv", "catalogue_meta.json", "discovery_log.jsonl")}
    with open(paths["documents.jsonl"], "w", encoding="utf-8", newline="\n") as fh:
        for row in result["documents"]:
            fh.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
    _write_csv(paths["documents.csv"], _DOC_COLUMNS, [_flat(r) for r in result["documents"]])
    _write_csv(paths["laws.csv"], _LAW_COLUMNS, [{k: _cell(v) for k, v in r.items()} for r in result["laws"]])
    paths["catalogue_meta.json"].write_text(json.dumps(meta, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    with open(paths["discovery_log.jsonl"], "w", encoding="utf-8", newline="\n") as fh:
        for entry in result["discovery_log"]:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return {k: str(v) for k, v in paths.items()}


def _flat(row: dict) -> dict:
    m = row["contract_meta"]
    pick = {**{k: row.get(k) for k in ("order", "scopes", "url", "law_number_guess", "law_name_guess", "indicator_hints")},
            **{k: m.get(k) for k in ("document_kind", "portal_id", "version_id", "language", "version_as_at", "text_version",
                                     "legal_status", "last_amending_instrument", "discovery_path", "seed_provenance",
                                     "crawl_flags", "review_flags")}}
    return {k: _cell(v) for k, v in pick.items()}


def _load_cfg(registry: Optional[str], seeds: Optional[str]) -> dict:
    import yaml
    if registry:
        cfg = yaml.safe_load(Path(registry).read_text(encoding="utf-8")) or {}
    else:
        from ...sources import load_sources
        cfg = load_sources("AU")
    if seeds:
        extra = yaml.safe_load(Path(seeds).read_text(encoding="utf-8")) or {}
        cfg["seed_laws"] = extra.get("seed_laws") or []
    return cfg



def _say_identity(cc: str, fetcher) -> None:
    """Print the User-Agent and delay this build will use, before the first request.

    The update check of 2026-09-16 was refused on every request because it fell back to a bare User-Agent with no
    contact address, and nothing said so (`countries/sg-singapore/NOTES.md` 1.3). A build has the same failure
    mode: `config.settings` loads only from the stage root.
    """
    settings = getattr(fetcher, "settings", None)
    ua = getattr(settings, "user_agent", None) or os.environ.get("USER_AGENT") or "(the adapter's fallback)"
    delay = getattr(settings, "request_delay_seconds", None)
    if delay is None:
        delay = int(os.environ.get("REQUEST_DELAY_MS", "3000")) / 1000.0
    print(f"[catalogue] {cc}: identified as {ua!r}, {float(delay):g} s between requests", flush=True)

def main(argv: Optional[list[str]] = None) -> int:
    from ..my_gazette.catalogue import _SettingsOnly
    from .adapter import AuLegislationAdapter
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", required=True)
    ap.add_argument("--registry")
    ap.add_argument("--seeds")
    ap.add_argument("--pillars", default="6,7")
    args = ap.parse_args(argv)
    cfg = _load_cfg(args.registry, args.seeds)
    pillars = [int(x) for x in args.pillars.split(",") if x.strip()]
    adapter = AuLegislationAdapter(cfg)
    try:
        fetcher = _SettingsOnly()
        _say_identity("AU", fetcher)
        result = build(adapter, pillars, fetcher=fetcher)
    except Exception as e:  # noqa: BLE001 — the register unreadable or its shape changed: nothing is written
        print(f"[catalogue] AU: nothing written ({type(e).__name__}: {e})", flush=True)
        return 2
    files = {k: v for k, v in (("registry", args.registry), ("seeds", args.seeds)) if v}
    paths = write(result, args.out, registry_files=files)
    m = result["meta"]
    print(f"[catalogue] AU: {m['counts']} documents; kinds {m['document_kinds']}; {m['api_requests']} API and "
          f"{m['www_requests']} www request(s); harvest {m['harvest']}; {m['versions_read']} versions -> {paths['documents.jsonl']}", flush=True)
    for note in m["notes"]:
        print(f"[catalogue] note: {note}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
