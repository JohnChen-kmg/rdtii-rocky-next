"""The link list for Lao PDR: every law the gazette lists, and every file to crawl.

    python -m p1_scrape.adapters.la_gazette.catalogue --out <dir> [--registry sources.yaml --seeds seed_laws.yaml]

reads the gazette's listings — ten rows a page, one listing per kind of instrument, current (`old=0`) and
superseded (`old=1`) — and writes the five files every country writes (CONVENTIONS.md section 2). The crawl then
replays documents.jsonl (`gazette.frontier: links_file`). No document is downloaded here.

**A law can have two files**: the Lao text, which is the law, and an English translation where the gazette offers
one. `laws.csv` has one row per law; `documents.jsonl` has one row per file, each with its own language.

**A law is listed once**, even when two of the portal's listings carry it: legaltype 6 also carries the Civil
Code and the Penal Code, which have listings of their own. The row keeps the first listing that named it and
records the rest in `also_listed_under`.
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
from .parse import LEGAL_TYPES

#: Columns that hold an address. **Their whitespace is never collapsed.**
#:
#: The shared `_cell` puts every string through `re.sub(r"\s+", " ", v)` so a CSV cell stays on one line. That is
#: right for a title and wrong for a URL: 42 of this portal's filenames contain **two consecutive spaces**
#: (`law on foreign exchange management  (Amended) No 15 - NA.pdf`), and collapsing them wrote an address into
#: `laws.csv` that the portal does not serve. The documents were fetched correctly — `documents.jsonl` and the
#: manifest keep the real address — but the census did not match them, and the update check of 2026-09-21 read
#: the difference as 42 laws whose file had moved. `_cell` is Malaysia's and is imported by four countries, so
#: the fix is made here rather than there; the shared change is written up in `../NOTES.md`.
_URL_COLUMNS = frozenset({"url", "lao_url", "english_url", "detail_url", "source_url"})


def _cells(row: dict) -> dict:
    return {k: (v if k in _URL_COLUMNS else _cell(v)) for k, v in row.items()}

__all__ = ["build", "cfg_fingerprint", "law_rows", "main", "read_documents", "scraper_hashes", "write"]

_LAW_COLUMNS = ["legal_type", "legal_type_label", "listing", "portal_id", "title", "agency", "made_on",
                "gazetted_on", "legal_status", "status_word", "document_kind", "is_revised_version",
                "also_listed_under", "lao_url", "english_url", "has_translation", "in_seed", "in_relevant",
                "in_all", "not_crawled_reason"]
_DOC_COLUMNS = ["order", "scopes", "url", "document_kind", "law_name_guess", "portal_id", "language",
                "is_translation", "published_on", "made_on", "legal_status", "status_word", "legal_type_label",
                "listing", "agency", "discovery_path", "seed_provenance", "indicator_hints", "crawl_flags",
                "review_flags"]


def cfg_fingerprint(cfg: dict) -> str:
    """What a link file depends on: the seeds, the gazette settings (not the frontier), the title rule, the terms."""
    gazette = {k: v for k, v in (cfg.get("gazette") or {}).items() if k not in ("frontier", "links_file")}
    payload = {"seed_laws": cfg.get("seed_laws") or [], "gazette": gazette, "title_rule": cfg.get("title_rule"),
               "seed_queries": cfg.get("seed_queries")}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()


def build(adapter, pillars: list[int], fetcher=None) -> dict[str, Any]:
    """Discovery once at scope all; the seed and relevant scopes are computed from what was read."""
    adapter._frontier_override = "discover"
    all_cands = adapter.discover(pillars=pillars, scope="all", fetcher=fetcher)
    client = adapter._client
    seeds, _others = adapter._seed_by_id(pillars)
    relevant = adapter._relevant_ids()
    rank = {"seed": 0, "relevant": 1, "all": 2}
    rows = []
    for i, c in enumerate(all_cands):
        meta = c.contract_meta
        law_id = str(meta.get("portal_id") or "").replace("LA-", "")
        is_seed = meta.get("discovery_path") == "seed"
        is_relevant = is_seed or law_id in relevant
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
    languages: dict[str, int] = {}
    for d in documents:
        k = d["contract_meta"].get("document_kind") or "other"
        kinds[k] = kinds.get(k, 0) + 1
        lang = d["contract_meta"].get("language") or "?"
        languages[lang] = languages.get(lang, 0) + 1
    meta = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "economy": "LA", "pillars": pillars, "counts": counts, "document_kinds": kinds, "languages": languages,
        "rule_id": adapter.title_rule.rule_id if adapter.title_rule else None,
        "settings": adapter.effective_settings(("legal_types", "superseded", "english_pdfs", "max_pages", "root")),
        "cfg_sha256": cfg_fingerprint(adapter.cfg),
        "seed_keys": [[law.get("law_name"), law.get("portal_key")] for law in adapter.cfg.get("seed_laws") or []],
        "requests": len(client.log), "robots_record": adapter.robots_record, "gazette_error": adapter.gazette_error,
        "listing_counts": adapter.listing_counts, "laws_listed": len(laws),
        "statuses": _tally(laws, "legal_status"), "listings": _tally(laws, "listing"),
        "translations": sum(1 for law in laws if law.get("has_translation")),
        "notes": list(adapter.notes), "scraper_sha256": scraper_hashes(),
    }
    return {"documents": documents, "laws": laws, "meta": meta, "discovery_log": list(client.log)}


def _tally(laws: list[dict], field: str) -> dict[str, int]:
    out: dict[str, int] = {}
    for law in laws:
        key = str(law.get(field) or "unknown")
        out[key] = out.get(key, 0) + 1
    return out


def law_rows(adapter, documents: list[dict], relevant: set, seeds: dict) -> list[dict]:
    """One row per **law**, with both of its files. A law the portal lists without a file keeps its row."""
    scopes_by_url = {d["url"]: set(d["scopes"]) for d in documents}
    out = []
    for row in adapter.rows():
        lao, english = row.url("lao"), row.url("eng")
        scopes = scopes_by_url.get(lao or "", set()) | scopes_by_url.get(english or "", set())
        reason = None
        if not lao and not english:
            reason = "the portal lists this law with no file"
        elif not scopes:
            reason = "not selected"
        out.append({
            "legal_type": row.legal_type,
            "legal_type_label": LEGAL_TYPES.get(row.legal_type, {}).get("english"),
            "listing": f"legaltype={row.legal_type}&old={row.old}",
            "portal_id": row.code, "title": row.title, "agency": row.agency,
            "made_on": row.made_on, "gazetted_on": row.gazetted_on,
            "legal_status": row.legal_status, "status_word": row.status_label,
            "document_kind": row.document_kind, "is_revised_version": row.is_revised,
            "also_listed_under": list(row.also_listed_under),
            "lao_url": lao, "english_url": english, "has_translation": bool(english),
            "in_seed": row.law_id in seeds or ("seed" in scopes),
            "in_relevant": row.law_id in relevant or ("relevant" in scopes),
            "in_all": bool(lao or english), "not_crawled_reason": reason,
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
    _write_csv(paths["documents.csv"], _DOC_COLUMNS, [_flat_la(r) for r in result["documents"]])
    _write_csv(paths["laws.csv"], _LAW_COLUMNS, [_cells(r) for r in result["laws"]])
    paths["catalogue_meta.json"].write_text(json.dumps(meta, ensure_ascii=False, indent=1, default=str),
                                            encoding="utf-8")
    with open(paths["discovery_log.jsonl"], "w", encoding="utf-8", newline="\n") as fh:
        for entry in result["discovery_log"]:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return {k: str(v) for k, v in paths.items()}


def _flat_la(row: dict) -> dict:
    m = row["contract_meta"]
    pick = {**{k: row.get(k) for k in ("order", "scopes", "url", "law_name_guess", "indicator_hints")},
            **{k: m.get(k) for k in ("document_kind", "portal_id", "language", "is_translation", "published_on",
                                     "made_on", "legal_status", "status_word", "legal_type_label", "listing",
                                     "agency", "discovery_path", "seed_provenance", "crawl_flags",
                                     "review_flags")}}
    return _cells(pick)


def _load_cfg(registry: Optional[str], seeds: Optional[str]) -> dict:
    import yaml
    if registry:
        cfg = yaml.safe_load(Path(registry).read_text(encoding="utf-8")) or {}
    else:
        from ...sources import load_sources
        cfg = load_sources("LA")
    if seeds:
        extra = yaml.safe_load(Path(seeds).read_text(encoding="utf-8")) or {}
        cfg["seed_laws"] = extra.get("seed_laws") or []
    return cfg


def _say_identity(fetcher) -> None:
    """Print the User-Agent and delay this build will use, before the first request.

    Singapore's update check of 2026-09-16 was refused on every request because it fell back to a bare
    User-Agent with no contact address, and nothing said so (`../../sg-singapore/NOTES.md` 1.3).
    """
    settings = getattr(fetcher, "settings", None)
    ua = getattr(settings, "user_agent", None) or os.environ.get("USER_AGENT") or "(the adapter's fallback)"
    delay = getattr(settings, "request_delay_seconds", None)
    if delay is None:
        delay = int(os.environ.get("REQUEST_DELAY_MS", "6000")) / 1000.0
    print(f"[catalogue] LA: identified as {ua!r}, {float(delay):g} s between requests", flush=True)


def main(argv: Optional[list[str]] = None) -> int:
    from ..my_gazette.catalogue import _SettingsOnly
    from .adapter import LaGazetteAdapter
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", required=True, help="the links/ folder to write")
    ap.add_argument("--registry", help="sources.yaml to read instead of the stage's sources_la.yaml")
    ap.add_argument("--seeds", help="links/seed_laws.yaml")
    ap.add_argument("--pillars", default="6,7")
    args = ap.parse_args(argv)
    cfg = _load_cfg(args.registry, args.seeds)
    pillars = [int(x) for x in args.pillars.split(",") if x.strip()]
    adapter = LaGazetteAdapter(cfg)
    fetcher = _SettingsOnly()
    _say_identity(fetcher)
    try:
        result = build(adapter, pillars, fetcher=fetcher)
    except Exception as e:  # noqa: BLE001 — the gazette unreadable or the format changed: nothing is written
        print(f"[catalogue] LA: nothing written ({type(e).__name__}: {e})", file=sys.stderr, flush=True)
        return 2
    files = {k: v for k, v in (("registry", args.registry), ("seeds", args.seeds)) if v}
    paths = write(result, args.out, registry_files=files)
    m = result["meta"]
    print(f"[catalogue] LA: {m['laws_listed']} law(s) -> {len(result['documents'])} file(s) "
          f"({m['languages']}); {m['counts']}; statuses {m['statuses']}; {m['requests']} request(s) "
          f"-> {paths['documents.jsonl']}", flush=True)
    for note in m["notes"]:
        print(f"[catalogue] note: {note}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
