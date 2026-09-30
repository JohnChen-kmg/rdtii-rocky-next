"""The link list for Timor-Leste: every act the Jornal da República lists, and every document to crawl.

    python -m p1_scrape.adapters.tl_jornal.catalogue --out <dir> [--registry sources.yaml --seeds seed_laws.yaml]

reads the gazette once — robots.txt and six category pages, seven requests in all — and writes the same five files
every country writes (CONVENTIONS.md section 2; the writer is shared with Malaysia's): documents.jsonl,
documents.csv, laws.csv, catalogue_meta.json, discovery_log.jsonl. The crawl then replays documents.jsonl
(`jornal.frontier: links_file`). No document is downloaded here.

**The unit of `laws.csv` is the act; the unit of `documents.jsonl` is the gazette issue.** One issue can carry
several acts, so the two files have different lengths on purpose, and each document row names the acts it carries
in `contract_meta.contains`.
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
from .parse import CATEGORIES

__all__ = ["build", "cfg_fingerprint", "law_rows", "main", "read_documents", "write"]

_LAW_COLUMNS = ["category", "category_label", "portal_id", "law_number", "title", "document_kind", "legal_status",
                "published_on", "amends_law_number", "document_url", "acts_in_document", "in_seed", "in_relevant",
                "in_all", "not_crawled_reason"]
_DOC_COLUMNS = ["order", "scopes", "url", "document_kind", "law_number_guess", "law_name_guess", "portal_id",
                "principal_law_number", "language", "published_on", "legal_status", "category", "acts_in_document",
                "discovery_path", "seed_provenance", "indicator_hints", "crawl_flags", "review_flags"]


def cfg_fingerprint(cfg: dict) -> str:
    """What a link file depends on in the registry: seeds, the jornal settings (not the frontier), the title rule."""
    jornal = {k: v for k, v in (cfg.get("jornal") or {}).items() if k not in ("frontier", "links_file")}
    payload = {"seed_laws": cfg.get("seed_laws") or [], "jornal": jornal, "title_rule": cfg.get("title_rule"),
               "seed_queries": cfg.get("seed_queries")}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()


def build(adapter, pillars: list[int], fetcher=None) -> dict[str, Any]:
    """Discovery once at scope all; the seed and relevant scopes are computed from what was read, no extra request."""
    adapter._frontier_override = "discover"
    all_cands = adapter.discover(pillars=pillars, scope="all", fetcher=fetcher)
    client = adapter._client
    seeds, _others = adapter._seed_by_number(pillars)
    relevant = adapter._relevant_codes()
    rank = {"seed": 0, "relevant": 1, "all": 2}
    rows = []
    for i, c in enumerate(all_cands):
        meta = c.contract_meta
        acts = meta.get("contains") or []
        is_seed = meta.get("discovery_path") == "seed"
        is_relevant = is_seed or any(code in relevant for code in acts)
        scopes = [s for s, on in (("seed", is_seed), ("relevant", is_relevant), ("all", True)) if on]
        rows.append((min(rank[s] for s in scopes), i, c, scopes))
    rows.sort(key=lambda t: (t[0], t[1]))
    documents = []
    for order, (_rank, _i, c, scopes) in enumerate(rows, start=1):
        row = {name: getattr(c, name) for name in _CANDIDATE_FIELDS}
        row.update({"order": order, "scopes": scopes, "contract_meta": c.contract_meta})
        documents.append(row)
    laws = law_rows(adapter, documents, relevant, seeds)
    counts = {scope: sum(1 for d in documents if scope in d["scopes"]) for scope in ("all", "seed", "relevant")}
    kinds: dict[str, int] = {}
    for d in documents:
        k = d["contract_meta"].get("document_kind") or "agency_or_other"
        kinds[k] = kinds.get(k, 0) + 1
    meta = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "economy": "TL", "pillars": pillars, "counts": counts, "document_kinds": kinds,
        "settings": adapter.effective_settings(("categories", "document_form", "root")),
        "cfg_sha256": cfg_fingerprint(adapter.cfg),
        "seed_keys": [[law.get("law_name"), law.get("law_number"), law.get("portal_key")]
                      for law in adapter.cfg.get("seed_laws") or []],
        "requests": len(client.log), "robots_record": adapter.robots_record, "jornal_error": adapter.jornal_error,
        "listing_counts": adapter.listing_counts, "acts_listed": sum(len(v) for v in adapter.listed.values()),
        "documents_distinct": len(adapter.issues), "notes": list(adapter.notes),
        "scraper_sha256": scraper_hashes(),
    }
    return {"documents": documents, "laws": laws, "meta": meta, "discovery_log": list(client.log)}


def law_rows(adapter, documents: list[dict], relevant: set, seeds: dict) -> list[dict]:
    """One row per **act**, with the document it appears in. Acts the portal lists without a file keep their row."""
    scopes_by_url = {d["url"]: set(d["scopes"]) for d in documents}
    out = []
    for category in CATEGORIES:
        for act in adapter.listed.get(category, []):
            url = act.document_url
            scopes = scopes_by_url.get(url or "", set())
            in_seed = f"{act.category}:{act.number}" in seeds
            reason = None
            if not url:
                reason = "the portal lists this act with no document link"
            elif not scopes:
                reason = "not selected"
            out.append({
                "category": act.category, "category_label": CATEGORIES[act.category]["label"],
                "portal_id": act.code, "law_number": act.number, "title": act.title,
                "document_kind": act.document_kind,
                "legal_status": "unknown",          # the gazette states none: as-made publication only
                "published_on": act.published_on, "amends_law_number": act.amends,
                "document_url": url, "acts_in_document": len(adapter.issues.get(url or "", [])) or None,
                "in_seed": in_seed or ("seed" in scopes), "in_relevant": act.code in relevant or ("relevant" in scopes),
                "in_all": bool(url), "not_crawled_reason": reason,
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
        meta["registry_sha256"] = {name: hashlib.sha256(Path(path).read_bytes()).hexdigest()
                                   for name, path in registry_files.items()}
    paths = {name: out / name for name in ("documents.jsonl", "documents.csv", "laws.csv", "catalogue_meta.json",
                                           "discovery_log.jsonl")}
    with open(paths["documents.jsonl"], "w", encoding="utf-8", newline="\n") as fh:
        for row in result["documents"]:
            fh.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
    _write_csv(paths["documents.csv"], _DOC_COLUMNS, [_flat_tl(r) for r in result["documents"]])
    _write_csv(paths["laws.csv"], _LAW_COLUMNS, [{k: _cell(v) for k, v in r.items()} for r in result["laws"]])
    paths["catalogue_meta.json"].write_text(json.dumps(meta, ensure_ascii=False, indent=1, default=str),
                                            encoding="utf-8")
    with open(paths["discovery_log.jsonl"], "w", encoding="utf-8", newline="\n") as fh:
        for entry in result["discovery_log"]:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return {k: str(v) for k, v in paths.items()}


def _flat_tl(row: dict) -> dict:
    m = row["contract_meta"]
    pick = {**{k: row.get(k) for k in ("order", "scopes", "url", "law_number_guess", "law_name_guess",
                                       "indicator_hints")},
            **{k: m.get(k) for k in ("document_kind", "portal_id", "principal_law_number", "language",
                                     "published_on", "legal_status", "category", "discovery_path",
                                     "seed_provenance", "crawl_flags", "review_flags")},
            "acts_in_document": len(m.get("contains") or [])}
    return {k: _cell(v) for k, v in pick.items()}


def _load_cfg(registry: Optional[str], seeds: Optional[str]) -> dict:
    import yaml
    if registry:
        cfg = yaml.safe_load(Path(registry).read_text(encoding="utf-8")) or {}
    else:
        from ...sources import load_sources
        cfg = load_sources("TL")
    if seeds:
        extra = yaml.safe_load(Path(seeds).read_text(encoding="utf-8")) or {}
        cfg["seed_laws"] = extra.get("seed_laws") or []
    return cfg


def _say_identity(fetcher) -> None:
    """Print the User-Agent and delay this build will use, before the first request (Singapore's lesson of
    2026-09-17: a bare fallback User-Agent was refused on every request, and nothing said so)."""
    settings = getattr(fetcher, "settings", None)
    ua = getattr(settings, "user_agent", None) or os.environ.get("USER_AGENT") or "(the adapter's fallback)"
    delay = getattr(settings, "request_delay_seconds", None)
    if delay is None:
        delay = int(os.environ.get("REQUEST_DELAY_MS", "10000")) / 1000.0
    print(f"[catalogue] TL: identified as {ua!r}, {float(delay):g} s between requests", flush=True)


def main(argv: Optional[list[str]] = None) -> int:
    from ..my_gazette.catalogue import _SettingsOnly
    from .adapter import TlJornalAdapter
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", required=True, help="the links/ folder to write (documents.jsonl, laws.csv, ...)")
    ap.add_argument("--registry", help="sources.yaml to read instead of the stage's sources_tl.yaml")
    ap.add_argument("--seeds", help="links/seed_laws.yaml")
    ap.add_argument("--pillars", default="6,7")
    args = ap.parse_args(argv)
    cfg = _load_cfg(args.registry, args.seeds)
    pillars = [int(x) for x in args.pillars.split(",") if x.strip()]
    adapter = TlJornalAdapter(cfg)
    fetcher = _SettingsOnly()
    _say_identity(fetcher)
    try:
        result = build(adapter, pillars, fetcher=fetcher)
    except Exception as e:  # noqa: BLE001 — the gazette unreadable or the format changed: nothing is written
        print(f"[catalogue] TL: nothing written ({type(e).__name__}: {e})", file=sys.stderr, flush=True)
        return 2
    files = {k: v for k, v in (("registry", args.registry), ("seeds", args.seeds)) if v}
    paths = write(result, args.out, registry_files=files)
    m = result["meta"]
    print(f"[catalogue] TL: {m['acts_listed']} act(s) listed -> {m['documents_distinct']} document(s); "
          f"{m['counts']}; kinds {m['document_kinds']}; {m['requests']} request(s) -> {paths['documents.jsonl']}",
          flush=True)
    for note in m["notes"]:
        print(f"[catalogue] note: {note}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
