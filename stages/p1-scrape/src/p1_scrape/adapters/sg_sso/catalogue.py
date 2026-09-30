"""The link list for Singapore: every law Statutes Online lists and every document to crawl, written before the crawl.

    python -m p1_scrape.adapters.sg_sso.catalogue --out <dir> [--registry sources.yaml --seeds seed_laws.yaml]

reads SSO once (robots.txt, the Current listing 100 rows a page, the Repealed, Uncommenced and Acts Supplement listings, every
current act's detail page, the SL tab of the seed acts) and writes the same five files Malaysia's step writes
(CONVENTIONS.md section 2; the writer is shared with it): documents.jsonl, documents.csv, laws.csv,
catalogue_meta.json, discovery_log.jsonl. The crawl then replays documents.jsonl (sso.frontier: links_file).
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
from .adapter import _current_version
from .parse import act_code

__all__ = ["build", "cfg_fingerprint", "law_rows", "main", "read_documents", "write"]   # read_documents is shared

_LAW_COLUMNS = ["listing", "portal_id", "law_number", "title", "legal_status", "version_as_at", "published_on",
                "repeal_date", "detail_read", "versions_listed", "amendments_listed", "last_amending_instrument",
                "revised_edition", "subsidiary_listed", "document_url", "in_seed", "in_relevant", "in_all",
                "document_kinds", "not_crawled_reason"]
_DOC_COLUMNS = ["order", "scopes", "url", "document_kind", "law_number_guess", "law_name_guess", "portal_id",
                "principal_law_number", "language", "version_as_at", "text_version", "legal_status",
                "last_amending_instrument", "discovery_path", "seed_provenance", "indicator_hints", "crawl_flags",
                "review_flags"]


def cfg_fingerprint(cfg: dict) -> str:
    """What a link file depends on in the registry: seeds, the SSO settings (not the frontier) and the search terms."""
    sso = {k: v for k, v in (cfg.get("sso") or {}).items() if k not in ("frontier", "links_file")}
    payload = {"seed_laws": cfg.get("seed_laws") or [], "sso": sso, "seed_queries": cfg.get("seed_queries")}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()


def build(adapter, pillars: list[int], fetcher=None) -> dict[str, Any]:
    """Discovery once at scope all; the seed and relevant scopes are computed from what was read, without a request."""
    adapter._frontier_override = "discover"
    all_cands = adapter.discover(pillars=pillars, scope="all", fetcher=fetcher)
    client = adapter._client
    seeds, _others = adapter._seed_by_code(pillars)
    seed_urls = {law.get("url") for law in adapter.cfg.get("seed_laws") or []}
    relevant_codes = {act_code(it.url) for it in adapter.inventory if it.relevant}
    rank = {"seed": 0, "relevant": 1, "all": 2}
    rows = []
    for i, c in enumerate(all_cands):
        meta = c.contract_meta
        is_seed = meta.get("discovery_path") == "seed" or c.url in seed_urls or \
            (meta.get("document_kind") == "subsidiary_legislation" and meta.get("principal_portal_id") in seeds)
        relevant = is_seed or (meta.get("portal_id") in relevant_codes)
        scopes = [s for s, on in (("seed", is_seed), ("relevant", relevant), ("all", True)) if on]
        rows.append((min(rank[s] for s in scopes), i, c, scopes))
    rows.sort(key=lambda t: (t[0], t[1]))
    documents = []
    for order, (_rank, _i, c, scopes) in enumerate(rows, start=1):
        row = {name: getattr(c, name) for name in _CANDIDATE_FIELDS}
        row.update({"order": order, "scopes": scopes, "contract_meta": c.contract_meta})
        documents.append(row)
    laws = law_rows(adapter, documents)
    counts = {scope: sum(1 for d in documents if scope in d["scopes"]) for scope in ("all", "seed", "relevant")}
    kinds: dict[str, int] = {}
    for d in documents:
        k = d["contract_meta"].get("document_kind") or "agency_or_other"
        kinds[k] = kinds.get(k, 0) + 1
    meta = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "economy": "SG", "pillars": pillars, "counts": counts, "document_kinds": kinds,
        "settings": adapter.effective_settings(("detail_pages", "subsidiary_acts", "subsidiary_max_per_act",
                                                "acts_supp_years", "listing_paging", "listing_rows",
                                                "listing_page_size", "read_repealed")),
        "accepted_retries": adapter.accepted_retries,
        "cfg_sha256": cfg_fingerprint(adapter.cfg),
        "seed_keys": [[law.get("law_name"), law.get("law_number"), law.get("url")] for law in adapter.cfg.get("seed_laws") or []],
        "requests": len(client.log), "robots_record": adapter.robots_record, "sso_error": adapter.sso_error,
        "listing_counts": adapter.listing_counts, "detail_pages_read": len(adapter.details),
        "sl_tabs_read": len(adapter.subsidiary), "notes": list(adapter.notes), "scraper_sha256": scraper_hashes(),
    }
    return {"documents": documents, "laws": laws, "meta": meta, "discovery_log": list(client.log)}


def law_rows(adapter, documents: list[dict]) -> list[dict]:
    by_portal: dict[str, list[dict]] = {}
    for d in documents:
        pid = d["contract_meta"].get("portal_id")
        if pid:
            by_portal.setdefault(str(pid), []).append(d)
    out = []
    for listing in ("current", "repealed", "uncommenced", "acts_supp"):
        for r in adapter.listed.get(listing, []):
            docs = by_portal.get(r.code, [])
            own = [d for d in docs if d["contract_meta"].get("document_kind") in ("principal_act", "amending_act")]
            detail = adapter.details.get(r.code)
            scopes = {s for d in own for s in d["scopes"]}
            status = {"current": "in_force", "repealed": "repealed", "uncommenced": "not_yet_in_force"}.get(listing)
            if listing == "acts_supp":
                status = "unknown"
            reason = None
            if not own:
                if listing == "uncommenced":
                    reason = "not yet in force; the portal's address for its text changes daily, so it is recorded only"
                elif listing == "acts_supp":
                    reason = "a new principal act: its consolidated text comes from the Current listing"
                elif listing == "repealed" and not r.pdf_path:
                    reason = "the portal offers no document"
                else:
                    reason = "not selected"
            out.append({
                "listing": listing, "portal_id": r.code, "law_number": r.number or (detail.original_number if detail else None),
                "title": r.title, "legal_status": status,
                "version_as_at": detail.current_valid_from if detail else r.doc_date,
                "published_on": (_current_version(detail).published_on if detail and _current_version(detail) else r.doc_date),
                "repeal_date": r.repeal_date, "detail_read": detail is not None,
                "versions_listed": len(detail.versions) if detail else None,
                "amendments_listed": len(detail.amendments) if detail else None,
                "last_amending_instrument": detail.last_amending_instrument if detail else None,
                "revised_edition": detail.revised_edition if detail else None,
                "subsidiary_listed": adapter.subsidiary_totals.get(r.code) if r.code in adapter.subsidiary else None,
                "document_url": own[0]["url"] if own else None,
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
    _write_csv(paths["documents.csv"], _DOC_COLUMNS, [_flat_sg(r) for r in result["documents"]])
    _write_csv(paths["laws.csv"], _LAW_COLUMNS, [{k: _cell(v) for k, v in r.items()} for r in result["laws"]])
    paths["catalogue_meta.json"].write_text(json.dumps(meta, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    with open(paths["discovery_log.jsonl"], "w", encoding="utf-8", newline="\n") as fh:
        for entry in result["discovery_log"]:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return {k: str(v) for k, v in paths.items()}


def _flat_sg(row: dict) -> dict:
    m = row["contract_meta"]
    pick = {**{k: row.get(k) for k in ("order", "scopes", "url", "law_number_guess", "law_name_guess", "indicator_hints")},
            **{k: m.get(k) for k in ("document_kind", "portal_id", "principal_law_number", "language", "version_as_at",
                                     "text_version", "legal_status", "last_amending_instrument", "discovery_path",
                                     "seed_provenance", "crawl_flags", "review_flags")}}
    return {k: _cell(v) for k, v in pick.items()}


def _load_cfg(registry: Optional[str], seeds: Optional[str]) -> dict:
    import yaml
    if registry:
        cfg = yaml.safe_load(Path(registry).read_text(encoding="utf-8")) or {}
    else:
        from ...sources import load_sources
        cfg = load_sources("SG")
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
    from .adapter import SgSsoAdapter
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", required=True, help="the links/ folder to write (documents.jsonl, laws.csv, ...)")
    ap.add_argument("--registry", help="sources.yaml to read instead of the stage's sources_sg.yaml")
    ap.add_argument("--seeds", help="a YAML file with seed_laws, merged over the registry's")
    ap.add_argument("--pillars", default="6,7")
    args = ap.parse_args(argv)
    cfg = _load_cfg(args.registry, args.seeds)
    pillars = [int(x) for x in args.pillars.split(",") if x.strip()]
    adapter = SgSsoAdapter(cfg)
    try:
        fetcher = _SettingsOnly()
        _say_identity("SG", fetcher)
        result = build(adapter, pillars, fetcher=fetcher)
    except Exception as e:  # noqa: BLE001 — SSO unreadable or the format changed: nothing is written
        print(f"[catalogue] SG: nothing written ({type(e).__name__}: {e})", flush=True)
        return 2
    files = {k: v for k, v in (("registry", args.registry), ("seeds", args.seeds)) if v}
    paths = write(result, args.out, registry_files=files)
    m = result["meta"]
    print(f"[catalogue] SG: {m['counts']} documents; kinds {m['document_kinds']}; {m['requests']} requests; "
          f"{m['detail_pages_read']} detail pages, {m['sl_tabs_read']} SL tabs -> {paths['documents.jsonl']}", flush=True)
    for note in m["notes"]:
        print(f"[catalogue] note: {note}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
