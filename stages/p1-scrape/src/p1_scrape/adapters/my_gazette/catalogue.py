"""The link file: every Malaysian law and every document to crawl, written before the crawl.

    python -m p1_scrape.adapters.my_gazette.catalogue --out <dir> [--registry sources.yaml --seeds seed_laws.yaml]

reads Laws of Malaysia once (robots.txt, both listings, the timelines lom.timeline asks for) and writes:

  laws.csv              one row per listing record: every principal act and amending act the portal lists, what
                        the scraper decided for it, and why a law has no document to crawl
  documents.jsonl       one row per document to crawl, in crawl order (seeds, relevant acts, the rest), with every
                        Candidate field, the scopes it belongs to (seed, relevant, all) and its contract_meta
  documents.csv         the same rows, flattened for reading
  catalogue_meta.json   when and how the file was built: registry and scraper hashes, request count, robots.txt
  discovery_log.jsonl   every request the build sent, with its time and wait

The crawl then serves documents.jsonl (lom.frontier: links_file). The manifest keeps source_url, so a manifest row
joins back to its documents.jsonl row, and through it to the contract_meta the Round 1 engine drops.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import sys
from dataclasses import fields
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from ...models import Candidate
from .parse import (
    _clean, _law_number, choose_document, choose_principal_document, document_as_at, iso_date, principal_status,
)

_CANDIDATE_FIELDS = [f.name for f in fields(Candidate)]
_DOC_COLUMNS = ["order", "scopes", "url", "document_kind", "law_number_guess", "law_name_guess", "portal_id",
                "principal_law_number", "amends", "language", "edition", "version_as_at", "text_version",
                "legal_status", "in_force_status", "discovery_path", "seed_provenance", "title_rule_groups",
                "indicator_hints", "crawl_flags", "review_flags"]
_LAW_COLUMNS = ["listing", "portal_id", "law_number", "title_bi", "title_bm", "status_marker", "legal_status",
                "as_at", "documents_offered", "document_url", "document_language", "document_edition",
                "title_rule_groups", "title_rule_exclusion", "rule_selected", "timeline_read", "principal_law_number",
                "amends", "in_seed", "in_relevant", "in_all", "document_kinds", "not_crawled_reason", "commencement_remark"]


def cfg_fingerprint(cfg: dict) -> str:
    """What a link file depends on in the registry: seeds, title rule, lom settings (not the frontier) and the
    secondary-copy whitelist. A replay refuses a file built from a different registry."""
    lom = {k: v for k, v in (cfg.get("lom") or {}).items()
           if k not in ("frontier", "links_file", "robots_5xx", "listing_page_size")}
    payload = {"seed_laws": cfg.get("seed_laws") or [], "title_rule": cfg.get("title_rule"), "lom": lom,
               "reputable_fallback": (cfg.get("portals") or {}).get("reputable_fallback")}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()


def build(adapter, pillars: list[int], fetcher=None) -> dict[str, Any]:
    """Run discovery once at scope all, then compute which rows the seed and relevant scopes hold. The two smaller
    scopes reuse the listings and timelines already read, so they send no request of their own."""
    adapter._frontier_override = "discover"     # a build always reads the portal, whatever LOM_FRONTIER says
    all_cands = adapter.discover(pillars=pillars, scope="all", fetcher=fetcher)
    if adapter.lom_error or not adapter.principals:
        raise RuntimeError(f"catalogue: Laws of Malaysia was not read ({adapter.lom_error or 'no principal acts'}); "
                           f"nothing written")
    client = adapter._client
    notes = list(adapter.notes)
    requests_before = len(client.log)
    lom_ok = adapter.lom_error is None
    scope_urls = {"all": {c.url for c in all_cands}}
    for scope in ("seed", "relevant"):
        picked = adapter._build_candidates(pillars, scope, client, lom_ok)
        adapter._drop_robots_disallowed(picked, client)
        scope_urls[scope] = set(picked)
    adapter.notes = notes
    extra = len(client.log) - requests_before
    if extra:
        notes.append(f"WARNING: the seed and relevant passes sent {extra} extra request(s)")

    rank = {"seed": 0, "relevant": 1, "all": 2}
    rows = []
    for i, c in enumerate(all_cands):
        scopes = [s for s in ("seed", "relevant", "all") if c.url in scope_urls[s]]
        rows.append((min(rank[s] for s in scopes), i, c, scopes))
    rows.sort(key=lambda t: (t[0], t[1]))
    documents = []
    for order, (_rank, _i, c, scopes) in enumerate(rows, start=1):
        row = {name: getattr(c, name) for name in _CANDIDATE_FIELDS}
        row.update({"order": order, "scopes": scopes, "contract_meta": getattr(c, "contract_meta", {})})
        documents.append(row)

    laws = _law_rows(adapter, documents)
    counts = {scope: len(urls) for scope, urls in scope_urls.items()}
    kinds: dict[str, int] = {}
    for d in documents:
        k = d["contract_meta"].get("document_kind") or "agency_or_other"
        kinds[k] = kinds.get(k, 0) + 1
    meta = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "economy": "MY", "pillars": pillars, "counts": counts, "document_kinds": kinds,
        "rule_id": adapter.title_rule.rule_id if adapter.title_rule else None,
        "settings": {**adapter.effective_settings(("timeline", "subsidiary_acts", "subsidiary_series",
                                                    "subsidiary_max_per_act", "document_languages", "root")),
                     "robots_5xx": adapter.lom_cfg.get("robots_5xx")},
        "cfg_sha256": cfg_fingerprint(adapter.cfg),
        "seed_keys": [[law.get("law_name"), law.get("law_number"), law.get("url")]
                      for law in adapter.cfg.get("seed_laws") or []],
        "requests": len(client.log), "robots_record": adapter.robots_record, "lom_error": adapter.lom_error,
        "listing_counts": adapter.listing_counts, "listing_floor": adapter.listing_floor,
        "timelines_read": len(adapter.timelines), "amendment_timelines_read": len(adapter.amendment_timelines),
        "notes": notes, "scraper_sha256": _scraper_hashes(),
    }
    return {"documents": documents, "laws": laws, "meta": meta, "discovery_log": list(client.log)}


def _law_rows(adapter, documents: list[dict]) -> list[dict]:
    by_portal: dict[str, list[dict]] = {}
    for d in documents:
        pid = d["contract_meta"].get("portal_id")
        if pid:
            by_portal.setdefault(str(pid), []).append(d)
    for d in documents:                      # the other act a shared file was also listed for
        for other in d["contract_meta"].get("also_listed_for", []) or []:
            by_portal.setdefault(str(other.get("portal_id")), [])
    shared_into = {str(o.get("portal_id")): d["contract_meta"].get("portal_id")
                   for d in documents for o in d["contract_meta"].get("also_listed_for", []) or []}
    langs = adapter._languages()
    links = adapter._links()[0]
    amends = adapter._listed_as_amendment()
    out = []
    for p in adapter.principals.values():
        doc = choose_principal_document(p, langs)
        groups, exclusion = adapter._rule_match(p)
        docs = by_portal.get(p.act_no, [])
        status, _src = principal_status(p)
        out.append({
            "listing": "updated", "portal_id": p.act_no, "law_number": _law_number(p.act_no),
            "title_bi": p.title_bi, "title_bm": p.title_bm, "status_marker": p.status_marker, "legal_status": status,
            "as_at": (document_as_at(p, doc) if doc else None) or p.as_at_bi or p.as_at_bm,
            "documents_offered": len(p.documents), "document_url": doc.url if doc else None,
            "document_language": doc.language if doc else None, "document_edition": doc.edition if doc else None,
            "title_rule_groups": groups, "title_rule_exclusion": exclusion, "rule_selected": adapter._rule_act(p),
            "timeline_read": p.act_no in adapter.timelines,
            "principal_law_number": (docs[0]["contract_meta"].get("principal_law_number") if docs else None),
            "amends": [_law_number(a) for a, _e in amends.get(p.act_no, [])], "commencement_remark": None,
            **_membership(docs),
            "not_crawled_reason": _reason(docs, bool(p.documents), shared_into.get(p.act_no)),
        })
    for a in adapter.amendments.values():
        doc = choose_document(a.documents, langs)
        docs = [d for d in by_portal.get(a.a_number, []) if d["contract_meta"].get("document_kind") == "amending_act"]
        link = links.get(a.a_number)
        out.append({
            "listing": "amendment", "portal_id": a.a_number, "law_number": f"Act {a.a_number}",
            "title_bi": a.title_bi, "title_bm": a.title_bm, "status_marker": None,
            "commencement_remark": _clean(a.commencement_remark) or None,
            "legal_status": (docs[0]["contract_meta"].get("legal_status") if docs else None),
            "as_at": iso_date(a.publication), "documents_offered": len(a.documents),
            "document_url": doc.url if doc else None, "document_language": doc.language if doc else None,
            "document_edition": doc.edition if doc else None, "title_rule_groups": [], "title_rule_exclusion": None,
            "rule_selected": None, "timeline_read": a.a_number in adapter.amendment_timelines,
            "principal_law_number": _law_number(link[0].act_no) if link else None, "amends": [],
            **_membership(docs),
            "not_crawled_reason": _reason(docs, bool(a.documents), shared_into.get(a.a_number)),
        })
    return out


def _membership(docs: list[dict]) -> dict:
    scopes = {s for d in docs for s in d["scopes"]}
    return {"in_seed": "seed" in scopes, "in_relevant": "relevant" in scopes, "in_all": "all" in scopes,
            "document_kinds": sorted({d["contract_meta"].get("document_kind") or "" for d in docs})}


def _reason(docs: list[dict], offered: bool, shared_into: Optional[str]) -> Optional[str]:
    if docs:
        return None
    if not offered:
        return "the portal offers no document"
    if shared_into:
        return f"its document is also listed for {shared_into} and is stored once, under that act"
    return "not selected (see the run notes in catalogue_meta.json)"


def _scraper_hashes() -> dict[str, str]:
    here = Path(__file__).parent
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(here.glob("*.py"))}


def write(result: dict[str, Any], out_dir: str | os.PathLike, registry_files: Optional[dict[str, str]] = None) -> dict:
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
    _write_csv(paths["documents.csv"], _DOC_COLUMNS, [_flat_document(r) for r in result["documents"]])
    _write_csv(paths["laws.csv"], _LAW_COLUMNS, [{k: _cell(v) for k, v in r.items()} for r in result["laws"]])
    paths["catalogue_meta.json"].write_text(json.dumps(meta, ensure_ascii=False, indent=1, default=str),
                                            encoding="utf-8")
    with open(paths["discovery_log.jsonl"], "w", encoding="utf-8", newline="\n") as fh:
        for entry in result["discovery_log"]:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return {k: str(v) for k, v in paths.items()}


def _flat_document(row: dict) -> dict:
    m = row["contract_meta"]
    pick = {**{k: row.get(k) for k in ("order", "scopes", "url", "law_number_guess", "law_name_guess",
                                         "in_force_status", "indicator_hints")},
            **{k: m.get(k) for k in ("document_kind", "portal_id", "principal_law_number", "amends", "language",
                                     "edition", "version_as_at", "text_version", "legal_status", "discovery_path",
                                     "seed_provenance", "title_rule_groups", "crawl_flags", "review_flags")}}
    return {k: _cell(v) for k, v in pick.items()}


def _cell(v: Any) -> Any:
    if isinstance(v, (list, tuple, set)):
        return ",".join(str(x) for x in v)
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, str):
        return re.sub(r"\s+", " ", v).strip()          # every CSV cell is single-line
    return "" if v is None else v


def _write_csv(path: Path, columns: list[str], rows: list[dict]) -> None:
    with open(path, "w", encoding="utf-8-sig", newline="") as fh:     # BOM: opens cleanly in Excel
        w = csv.DictWriter(fh, fieldnames=columns, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def read_documents(path: str | os.PathLike) -> tuple[list[dict], dict]:
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"link file not found: {p}")
    rows = [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]
    meta_path = p.with_name("catalogue_meta.json")
    meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.is_file() else {}
    rows.sort(key=lambda r: r.get("order") or 0)
    return rows, meta


def candidate_from_row(row: dict) -> Candidate:
    cand = Candidate(**{k: row.get(k) for k in _CANDIDATE_FIELDS if k in row})
    cand.contract_meta = row.get("contract_meta") or {}
    return cand


# --- command line ---------------------------------------------------------------------------------------------
def _load_cfg(registry: Optional[str], seeds: Optional[str]) -> dict:
    import yaml
    if registry:
        cfg = yaml.safe_load(Path(registry).read_text(encoding="utf-8")) or {}
    else:
        from ...sources import load_sources
        cfg = load_sources("MY")
    if seeds:
        extra = yaml.safe_load(Path(seeds).read_text(encoding="utf-8")) or {}
        cfg["seed_laws"] = extra.get("seed_laws") or []
    return cfg


class _SettingsOnly:
    """The adapter reads only fetcher.settings (user agent and delay); discovery sends its own requests."""

    def __init__(self):
        try:
            from config.settings import load_settings      # the stage's settings, when run from the stage root
            self.settings = load_settings()
        except Exception:  # noqa: BLE001 — outside the stage the adapter falls back to USER_AGENT / REQUEST_DELAY_MS
            self.settings = None



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
    from .adapter import MyGazetteAdapter
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", required=True, help="folder for the link files")
    ap.add_argument("--registry", help="sources.yaml to read instead of the stage's sources_my.yaml")
    ap.add_argument("--seeds", help="a YAML file with seed_laws, merged over the registry's")
    ap.add_argument("--pillars", default="6,7")
    args = ap.parse_args(argv)
    cfg = _load_cfg(args.registry, args.seeds)
    pillars = [int(x) for x in args.pillars.split(",") if x.strip()]
    adapter = MyGazetteAdapter(cfg)
    fetcher = _SettingsOnly()
    _say_identity("MY", fetcher)
    result = build(adapter, pillars, fetcher=fetcher)
    files = {k: v for k, v in (("registry", args.registry), ("seeds", args.seeds)) if v}
    paths = write(result, args.out, registry_files=files)
    m = result["meta"]
    print(f"[catalogue] MY: {m['counts']} documents; kinds {m['document_kinds']}; {m['requests']} requests; "
          f"{len(result['laws'])} listing records -> {paths['documents.jsonl']}")
    for note in m["notes"]:
        print(f"[catalogue] note: {note}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
