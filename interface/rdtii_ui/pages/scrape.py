"""The Scraping tab: which economies the crawler can read, what it will read for each, what has to be
checked by hand, and the crawl folders that already exist.

Everything is read from the crawler stage's own files, never hardcoded: the adapter registry, the source
registries, the link lists, and each adapter's watchlist of official sources the crawler never visits.
"""
from __future__ import annotations

import csv
import json
import re
from collections import Counter
from pathlib import Path

from .. import readers
from ..server import ApiError, App, rel_or_abs
from ..settings import REPO, Settings

# Hosts that ask for a slower pace than the engine's 3 s default (stages/p1-scrape/POLICY.md 5.3).
POLITE_DELAY_MS = {"SG": 6000, "AU": 10000}
DEFAULT_DELAY_MS = 3000

# Which registry blocks the adapters actually fetch from: the statutes portal (and the gazette, where the gazette
# is the statutes source). Regulators and agency portals are named as places a researcher looks and are never
# crawled; they appear on the watchlist instead.
CRAWLED_KINDS = ("primary_statutes", "gazette")

MANUAL_SOURCES_NOTE = ("These official sources are named in the registry but are not in our corpus: the crawler never "
                       "visits them. A researcher checks them by hand for now; they may be brought into the crawl in a "
                       "later round. The watchlist says what to look for on each. A file you fetch from them by hand goes in "
                       "the inbox folder, one subfolder per economy (inbox/SG for Singapore); Extraction lists it at once.")


def register(app: App) -> None:
    @app.route("GET", r"/api/scrape/economies")
    def economies(app: App, m, q, b):
        return 200, {"economies": list_economies(app.settings), "pillars": [6, 7],
                     # The stage's scope ids stay; the page shows two of them under plain names. "seed" alone is
                     # not offered: it finds only what a hand-made list already names.
                     "scopes": [{"id": "all", "label": "All", "text": "every principal law the portal lists"},
                                {"id": "relevant", "label": "Sample",
                                 "text": "laws whose titles match the pillar 6 and 7 vocabulary, plus the laws named in the crawler's registry"}],
                     "default_scope": "all",
                     "seed_note": ("The seed list is the laws named on purpose in the crawler's registry. For the live test "
                                   "it must come from the host's portal list only, never from the 2025 database.")}

    @app.route("GET", r"/api/scrape/sources")
    def sources(app: App, m, q, b):
        code = q.get("economy", "").strip().upper()
        if not re.fullmatch(r"[A-Z]{2}", code):
            raise ApiError(400, "economy must be a two-letter code")
        return 200, describe_sources(app.settings, code)

    @app.route("GET", r"/api/scrape/holdings")
    def holdings_route(app: App, m, q, b):
        code = q.get("economy", "").strip().upper()
        if not re.fullmatch(r"[A-Z]{2}", code):
            raise ApiError(400, "economy must be a two-letter code")
        if code == "CN":
            return 200, cn_run.list_documents(app.settings, q.get("scope", "all").strip() or "all")
        return 200, holdings_documents(app.settings, code)

    @app.route("GET", r"/api/scrape/documents")
    def documents(app: App, m, q, b):
        code = q.get("economy", "").strip().upper()
        if not re.fullmatch(r"[A-Z]{2}", code):
            raise ApiError(400, "economy must be a two-letter code")
        scope = q.get("scope", "all").strip() or "all"
        if code == "CN":
            if scope not in {sc["id"] for sc in cn_run.SCOPES}:
                raise ApiError(400, "scope must be all, layer1 or layer2 for China")
            return 200, cn_run.list_documents(app.settings, scope)
        if scope not in ("all", "relevant", "seed"):
            raise ApiError(400, "scope must be all, relevant or seed")
        return 200, list_documents(app.settings, code, scope)

    @app.route("GET", r"/api/scrape/outputs")
    def outputs(app: App, m, q, b):
        return 200, {"folders": list_crawl_folders(app.settings)}

    register_run(app)


# ---- the stage's own tables, read as text ---------------------------------------------------------

def p1_dir(s: Settings) -> Path:
    return s.stage_dirs["p1"]


def registry(s: Settings) -> dict[str, str]:
    """economy code -> adapter package name, from adapters/registry.py."""
    path = p1_dir(s) / "src" / "p1_scrape" / "adapters" / "registry.py"

    def load(p: Path):
        text = p.read_text(encoding="utf-8")
        cls_to_pkg = {cls: pkg for pkg, cls in re.findall(r"^from \.(\w+) import (\w+)", text, re.M)}
        out = {}
        for code, cls in re.findall(r'"([A-Z]{2})":\s*(\w+)', text):
            out[code] = cls_to_pkg.get(cls, cls)
        return out
    return readers.cached(path, load) or {}


def valid_codes(s: Settings) -> list[str]:
    path = p1_dir(s) / "src" / "p1_scrape" / "economies.py"

    def load(p: Path):
        m = re.search(r"VALID_CODES\s*=\s*\((.*?)\)", p.read_text(encoding="utf-8"), re.S)
        return re.findall(r'"([A-Z]{2})"', m.group(1)) if m else []
    return readers.cached(path, load) or []


def adapter_packages(s: Settings) -> dict[str, Path]:
    """Every adapter package folder, by its two-letter prefix (cn_npc has tools but no adapter)."""
    root = p1_dir(s) / "src" / "p1_scrape" / "adapters"
    out = {}
    if root.is_dir():
        for d in root.iterdir():
            if d.is_dir() and re.match(r"^[a-z]{2}_", d.name):
                out.setdefault(d.name[:2].upper(), d)
    return out


def watchlist_path(s: Settings, code: str) -> Path | None:
    pkg = adapter_packages(s).get(code)
    if not pkg:
        return None
    for cand in (pkg / "updates" / "watchlist.tsv", pkg / "watchlist.tsv"):
        if cand.is_file():
            return cand
    return None


def read_watchlist(path: Path) -> list[dict]:
    def load(p: Path):
        with open(p, encoding="utf-8-sig", newline="") as f:
            return [dict(r) for r in csv.DictReader(f, delimiter="\t")]
    return readers.cached(path, load) or []


def links_dir(s: Settings, code: str) -> Path:
    return p1_dir(s) / "links" / code.lower()


def catalogue_meta(s: Settings, code: str) -> dict:
    return readers.cached(links_dir(s, code) / "catalogue_meta.json", readers.read_json) or {}


def link_rows(s: Settings, code: str) -> list[dict]:
    path = links_dir(s, code) / "documents.csv"
    loaded = readers.cached(path, readers.read_csv)
    return loaded[1] if loaded else []


NOT_READ = "not read by the scraper"   # the registries' own phrase on a portal group the crawler does not read


def portals(s: Settings, code: str) -> tuple[list[dict], Path | None]:
    """The portals of sources_<cc>.yaml, each tagged with whether the crawler reads it.

    Two sources of truth, both in the registry itself: the `portals:` block names the official destinations by
    kind, and a portal group whose line carries the registry's comment "not read by the scraper" is not crawled
    whatever its kind; the adapter's own top-level block (lom:, sso:, jornal:, gazette:) carries the `root:` the
    crawler actually reads, so that root is always a crawled portal, merged with the `portals:` entry of the same
    host when there is one. Malaysia is the case that needs both: its statutes come from lom.agc.gov.my, listed
    under a gazette group marked not read, beside a Federal Gazette host that does not resolve."""
    path = p1_dir(s) / "contracts" / "instrument" / f"sources_{code.lower()}.yaml"
    if not path.is_file():
        return [], None

    def host(url: str) -> str:
        return re.sub(r"^https?://", "", url).split("/")[0].lower()

    def load(p: Path):
        out: list[dict] = []
        engine_roots: list[tuple[str, str]] = []   # (block key, root) of the adapter's own blocks
        in_block = False
        subkey = ""
        subkey_read = True
        pending_name = None
        top = ""
        for raw in p.read_text(encoding="utf-8").splitlines():
            if re.match(r"^portals:", raw):
                in_block = True
                top = "portals"
                continue
            if re.match(r"^[A-Za-z_]", raw):
                in_block = False
                top = re.match(r"^([A-Za-z_]+)", raw).group(1)
            if not raw.strip() or raw.lstrip().startswith("#"):
                continue
            if not in_block:
                m = re.match(r'^  root:\s*"([^"]+)"', raw)
                if m and top not in ("updates", "title_rule", "seed_queries"):
                    engine_roots.append((top, m.group(1)))
                continue
            m = re.match(r"^  (\w+):(.*)$", raw)
            if m:
                subkey = m.group(1)
                subkey_read = NOT_READ not in m.group(2).lower()
                pending_name = None
            name = re.search(r'name:\s*"([^"]+)"', raw)
            root = re.search(r'root:\s*"([^"]+)"', raw)
            crawled = subkey in CRAWLED_KINDS and subkey_read
            note = "" if subkey_read else NOT_READ
            if name and root:
                out.append({"name": name.group(1), "root": root.group(1), "kind": subkey, "crawled": crawled, "note": note})
            elif name:
                pending_name = name.group(1)
            elif root and pending_name:
                out.append({"name": pending_name, "root": root.group(1), "kind": subkey, "crawled": crawled, "note": note})
                pending_name = None
        for key, root in engine_roots:
            hit = next((x for x in out if host(x["root"]) == host(root)), None)
            if hit:
                hit["crawled"] = True
                hit["note"] = ""
                if hit["kind"] not in CRAWLED_KINDS or (hit["kind"] == "gazette" and key != "gazette"):
                    hit["kind"] = "primary_statutes"
            else:
                out.insert(0, {"name": f"{host(root)} ({key})", "root": root, "kind": "primary_statutes", "crawled": True, "note": ""})
        return sorted(out, key=lambda x: (not x["crawled"]))   # crawled portals first, registry order kept
    return readers.cached(path, load) or [], path


# ---- what the page shows -----------------------------------------------------------------------------

def list_economies(s: Settings) -> list[dict]:
    from .. import sources as filed
    names = readers.econ_names(s.stage_dirs["p3"])
    reg = registry(s)
    codes = valid_codes(s)
    pkgs = adapter_packages(s)
    present = (p1_dir(s) / "scrape.py").is_file()
    out = []
    shown = list(dict.fromkeys(list(codes) + [c for c in pkgs if c not in codes] + ["CN"]))
    for code in shown:
        pkg = reg.get(code)
        crawlable = present and code in codes and bool(pkg)
        wl = watchlist_path(s, code)
        meta = catalogue_meta(s, code)
        if crawlable:
            note = f"crawler adapter {pkg}"
        elif code == "CN":
            note = ("collected by hand: the national database forbids automated collection in its robots.txt; "
                    "its tools sit in adapters/cn_npc and its sources are on the watchlist")
        elif not present:
            note = "the crawler stage is not in this repository"
        else:
            note = "no crawler adapter registered"
        tools = code == "CN" and present and cn_run.present(s)
        if tools:
            note = "CAC and gov.cn through the China tools; the national database, MIIT and Customs by hand"
        portal = filed.crawl_source(s, code) if crawlable else None
        out.append({
            "code": code, "name": names.get(code, code), "crawlable": crawlable, "tools": tools, "adapter": pkg,
            # the folder a new crawl is filed under: scrape/<code>/<source>/<time>
            "source": filed.CHINA_TOOLS if tools else (portal or {}).get("key", ""),
            "note": note, "delay_ms": POLITE_DELAY_MS.get(code, DEFAULT_DELAY_MS),
            "links": meta.get("counts") if meta else None,
            "watchlist_rows": len(read_watchlist(wl)) if wl else 0,
        })
    return out


def describe_sources(s: Settings, code: str) -> dict:
    names = readers.econ_names(s.stage_dirs["p3"])
    ports, sources_file = portals(s, code)
    cn_facts = None
    if code == "CN":
        ports = cn_run.portals(s)
        cn_facts = cn_run.collection_facts(s)
    meta = catalogue_meta(s, code)
    rows = link_rows(s, code)
    seeds = [r for r in rows if "seed" in (r.get("scopes") or "").split(",")]
    seed_view = [{"law_name": r.get("law_name_guess", ""), "law_number": r.get("law_number_guess", ""),
                  "url": r.get("url", ""), "kind": r.get("document_kind", ""),
                  "indicators": r.get("indicator_hints", ""), "language": r.get("language", ""),
                  "status": r.get("legal_status", "")} for r in seeds[:400]]
    wl = watchlist_path(s, code)
    watch = read_watchlist(wl) if wl else []
    return {
        "economy": code, "name": names.get(code, code),
        "sources_file": rel_or_abs(sources_file, REPO) if sources_file else None,
        "links_file": rel_or_abs(links_dir(s, code) / "documents.csv", REPO) if rows else ((cn_facts or {}).get("counts") and rel_or_abs(cn_run.shipped_cn(s) / cn_run.BASELINE, REPO)) or None,
        "portals": ports,
        "counts": (cn_facts or {}).get("counts") or meta.get("counts") or ({"all": len(rows)} if rows else None),
        "document_kinds": (cn_facts or {}).get("document_kinds") or meta.get("document_kinds") or (dict(Counter(r.get("document_kind", "") for r in rows)) if rows else None),
        "catalogued_at": (cn_facts or {}).get("catalogued_at") or meta.get("generated_at"),
        "facts": (cn_facts or {}).get("facts"), "doclist_label": (cn_facts or {}).get("doclist_label"),
        "scope_hint": (cn_facts or {}).get("scope_hint"), "holdings_label": (cn_facts or {}).get("holdings_label"),
        "holdings_sub": (cn_facts or {}).get("holdings_sub"),
        "holdings": ({"label": "What we hold today", "sub": "(9.30 Finale Submission)", "facts": cn_facts["facts"],
                      "rows": cn_facts["counts"]["all"], "doclist_label": "in the shipped collection",
                      "scope_hint": "by layer, with a filter", "src": "holdings"} if cn_facts else holdings(s, code)),
        "seeds": seed_view, "seeds_total": len(seeds),
        "watchlist": watch, "watchlist_file": rel_or_abs(wl, REPO) if wl else None,
        "manual_note": MANUAL_SOURCES_NOTE,
        "tools_note": cn_run.TOOLS_NOTE if code == "CN" else None,
    }


def shipped_corpus(s: Settings, code: str) -> Path | None:
    """The latest shipped corpus folder of an economy (handoff1/<CC>/<CC>_corpus_<date>/), manifest without bytes."""
    root = p1_dir(s) / "handoff1" / code.upper()
    if not root.is_dir():
        return None
    cands = sorted(p for p in root.iterdir() if p.is_dir() and (p / "manifest.csv").is_file() and "corpus" in p.name)
    return cands[-1] if cands else None


def _yes(v: str | None) -> bool:
    return (v or "").strip().lower() in ("yes", "true", "1")


def not_fetched(rows: list[dict]) -> str:
    """Why some listed laws have no document, counted from the law table's unfetched rows; one short line."""
    if not rows:
        return ""
    missing = [r for r in rows if not _yes(r.get("scraped"))]
    if not missing:
        return "none: every listed law has a document"
    parts: list[str] = []
    amend = sum(1 for r in missing if "compiles it" in (r.get("notes") or ""))
    nodoc = sum(1 for r in missing if "no document" in (r.get("notes") or "").lower())
    repealed = sum(1 for r in missing if (r.get("legal_status") or "") == "repealed" and "no document" not in (r.get("notes") or "").lower())
    nyif = sum(1 for r in missing if (r.get("legal_status") or "") == "not_yet_in_force")
    rest = len(missing) - amend - nodoc - repealed - nyif
    if repealed:
        parts.append(f"{repealed} repealed titles without a current text")
    if nodoc:
        parts.append(f"{nodoc} the portal offers no document for")
    if nyif:
        parts.append(f"{nyif} not yet in force")
    if amend:
        parts.append(f"{amend} amending acts folded into their principal act's compilation")
    if rest > 0:
        parts.append(f"{rest} without a document link")
    return f"{len(missing)} of {len(rows)} listed laws: " + "; ".join(parts)


def holdings(s: Settings, code: str) -> dict | None:
    """What we hold today for an economy: the shipped corpus, described from its manifest and law table."""
    p = shipped_corpus(s, code)
    if not p:
        return None
    d = describe_crawl_folder(p)
    loaded = readers.cached(p / "law_table.csv", readers.read_csv)
    kinds = Counter((r.get("document_kind") or "other") for r in (loaded[1] if loaded else []) if (r.get("doc_id") or "").strip())
    kind_label = {"principal_act": "principal acts", "subsidiary_legislation": "subsidiary legislation", "amending_act": "amending acts",
                  "agency_or_other": "agency or other", "other": "other"}
    date = re.search(r"(\d{4}-\d{2}-\d{2})", p.name)
    types = " · ".join(f"{k.replace('_', ' ')} {v}" for k, v in sorted(d["by_source_type"].items(), key=lambda kv: -kv[1]))
    bytes_note = (", described by the manifest; the files themselves are not in the repository"
                  if d["raw_checked"] and d["raw_present"] == 0 else "")
    facts = [["All", f"{d['rows']} documents in the shipped corpus {p.name}{bytes_note}"],
             ["By type", types or "none"]]
    if kinds:
        facts.append(["By kind", " · ".join(f"{kind_label.get(k, k)} {v}" for k, v in kinds.most_common())])
    nf = not_fetched(loaded[1] if loaded else [])
    if nf:
        facts.append(["Not fetched", nf])
    if d["raw_checked"] and d["raw_present"]:
        facts.append(["Bytes", f"{d['raw_present']} of {d['raw_checked']} checked present"])
    facts.append(["Collected", (date.group(1) if date else "") + "; a run from this page writes a new folder under the runs root, never into it"])
    return {"label": "What we hold today", "sub": "(9.30 Finale Submission)", "facts": facts, "id": rel_or_abs(p, REPO),
            "path": str(p), "rows": d["rows"], "doclist_label": "in the shipped corpus", "scope_hint": "with a filter", "src": "holdings"}


def holdings_documents(s: Settings, code: str) -> dict:
    """The shipped corpus's documents, one row per manifest line, in the shape of the link list."""
    p = shipped_corpus(s, code)
    if not p:
        return {"economy": code, "scope": "all", "total": 0, "counts": {"all": 0}, "documents": [], "scopes": [{"id": "all", "label": "All"}], "file": None}
    loaded = readers.cached(p / "manifest.csv", readers.read_csv)
    rows = loaded[1] if loaded else []
    lt = readers.cached(p / "law_table.csv", readers.read_csv)
    kind_by_doc = {(r.get("doc_id") or "").strip(): (r.get("document_kind") or "") for r in (lt[1] if lt else []) if (r.get("doc_id") or "").strip()}
    out = []
    for i, r in enumerate(rows, 1):
        kind = kind_by_doc.get((r.get("doc_id") or "").strip(), "")
        out.append({"order": i, "law_name": r.get("law_name_guess", ""), "law_number": r.get("law_number_guess", ""),
                    "url": r.get("source_url", ""), "kind": (kind.replace("_", " ") + " · " if kind else "") + (r.get("source_type") or "").replace("_", " "),
                    "indicators": r.get("indicator_hints", ""), "language": "", "status": r.get("in_force_status", ""),
                    "scopes": ["all"], "version": r.get("publication_date") or ""})
    return {"economy": code, "scope": "all", "total": len(out), "counts": {"all": len(out)}, "documents": out,
            "scopes": [{"id": "all", "label": "All"}], "file": rel_or_abs(p / "manifest.csv", REPO)}


def list_documents(s: Settings, code: str, scope: str = "all") -> dict:
    """Every document on the economy's link list, in crawl order, filtered to one scope."""
    rows = link_rows(s, code)
    out = []
    for r in rows:
        scopes = [x for x in (r.get("scopes") or "").split(",") if x]
        if scope not in scopes:
            continue
        out.append({"order": r.get("order", ""), "law_name": r.get("law_name_guess", ""), "law_number": r.get("law_number_guess", ""),
                    "url": r.get("url", ""), "kind": r.get("document_kind", ""), "indicators": r.get("indicator_hints", ""),
                    "language": r.get("language", ""), "status": r.get("legal_status", ""), "scopes": scopes,
                    "version": r.get("version_as_at", "")})
    counts = {k: sum(1 for r in rows if k in (r.get("scopes") or "").split(",")) for k in ("all", "relevant", "seed")}
    return {"economy": code, "scope": scope, "total": len(out), "counts": counts, "documents": out,
            "file": rel_or_abs(links_dir(s, code) / "documents.csv", REPO) if rows else None}


def describe_crawl_folder(path: Path, sample: int = 200) -> dict:
    """What a crawl output folder holds: rows, economies, source types, whether the bytes are present."""
    manifest = path / "manifest.csv"
    info: dict = {"path": str(path), "id": rel_or_abs(path, REPO), "name": path.name,
                  "manifest": manifest.is_file(), "rows": 0, "by_economy": {}, "by_source_type": {},
                  "raw_checked": 0, "raw_present": 0, "law_table": (path / "law_table.csv").is_file(),
                  "fetched_last_pass": None, "crawl_state": None}
    if manifest.is_file():
        loaded = readers.cached(manifest, readers.read_csv)
        rows = loaded[1] if loaded else []
        info["rows"] = len(rows)
        info["by_economy"] = dict(Counter(r.get("economy", "") for r in rows))
        info["by_source_type"] = dict(Counter(r.get("source_type", "") for r in rows))
        checked = rows[:sample]
        info["raw_checked"] = len(checked)
        info["raw_present"] = sum(1 for r in checked if r.get("local_path") and (path / r["local_path"]).is_file())
    cost = readers.cached(path / "cost_report.json", readers.read_json)
    if isinstance(cost, dict):
        info["fetched_last_pass"] = cost.get("docs_retrieved")
    status = readers.cached(path / "crawl_status.json", readers.read_json)
    if isinstance(status, dict):
        info["crawl_state"] = {k: status.get(k) for k in ("state", "attempted", "todo", "stored_total", "updated_at")}
    return info


def list_crawl_folders(s: Settings) -> list[dict]:
    from .. import sources
    out = []
    seen = set()

    def add(p: Path, kind: str, where: dict | None = None):
        rp = p.resolve()
        if rp in seen or not p.is_dir():
            return
        seen.add(rp)
        where = where or {}
        src = sources.find(s, where["economy"], where["source"]) if where.get("source") else None
        filed = {"economy": where.get("economy", ""), "source": where.get("source", ""),
                 "source_name": (src or {}).get("name", "")}
        if not (p / "manifest.csv").is_file() and cn_run.is_run(p):
            out.append({**cn_run.describe_run(p), **filed})
            return
        d = describe_crawl_folder(p)
        # a manifest the interface wrote for hand-collected files is not a crawl: it is never offered for a second pass
        d["kind"] = "hand-collected manifest" if kind == "interface run" and p.name.startswith("hand_") else kind
        d.update(filed)
        out.append(d)

    for p, where in sources.scrape_runs(s):
        add(p, "interface run", where)
    add(s.handoff1_dir, "HANDOFF1_DIR")
    out.extend(hand_collected_folders(s))
    shipped = p1_dir(s) / "handoff1"
    if shipped.is_dir():
        for cc in sorted(shipped.iterdir()):
            if cc.is_dir():
                for p in sorted(cc.iterdir()):
                    if (p / "manifest.csv").is_file():
                        add(p, "shipped manifest")
    return out


def hand_collected_folders(s: Settings) -> list[dict]:
    """The inbox folders that hold files, beside the crawl folders: they too feed Extraction. One row per
    designated source of an economy, and one for files of the older layout filed under no source."""
    from .. import sources
    out = []
    if not s.inbox_dir.is_dir():
        return out

    def row(p: Path, name: str, files: list[Path], code: str, src: dict | None) -> dict:
        batches = sorted({part for f in files for part in f.relative_to(p).parts[:-1] if sources.BATCH_RX.fullmatch(part)})
        return {"path": str(p), "id": rel_or_abs(p, REPO), "name": name, "manifest": False, "rows": len(files),
                "by_economy": {code: len(files)},
                "by_source_type": dict(Counter(cn_run.SUFFIX[f.suffix.lower()] for f in files)),
                "raw_checked": len(files), "raw_present": len(files), "law_table": False,
                "fetched_last_pass": None, "crawl_state": None, "kind": "hand-collected",
                "batches": batches, "economy": code, "source": (src or {}).get("key", ""),
                "source_name": (src or {}).get("name", "")}

    for p in sorted(s.inbox_dir.iterdir()):
        if not (p.is_dir() and re.fullmatch(r"[A-Za-z]{2}", p.name)):
            continue
        code = p.name.upper()
        docs = lambda d: [f for f in d.rglob("*") if f.is_file() and f.suffix.lower() in cn_run.SUFFIX]  # noqa: E731
        filed: set[Path] = set()
        for src in sources.designated(s, code):
            files = docs(p / src["key"]) if (p / src["key"]).is_dir() else []
            filed.update(files)
            if files:
                out.append(row(p / src["key"], src["key"], files, code, src))
        rest = [f for f in docs(p) if f not in filed]
        if rest:
            out.append(row(p, p.name, rest, code, None))
    return out


# =====================================================================================================
# The run: a crawl from a button, with a fresh folder or a second pass over the same one
# =====================================================================================================

import time as _time  # noqa: E402

from .. import probes as _probes  # noqa: E402
from . import cn_run  # noqa: E402
from ..envbuild import ChoiceError, build_env  # noqa: E402
from ..jobs import Job, Step  # noqa: E402

SCOPES = ("seed", "relevant", "all")
FORMS = ("", "pdf", "html", "both")
_FRONTIER_RX = re.compile(r"\b([A-Z]+)_FRONTIER\b")


def register_run(app: App) -> None:
    @app.route("POST", r"/api/scrape/precheck")
    def precheck_route(app: App, m, q, b):
        return 200, {"checks": precheck(app, b or {})}

    @app.route("POST", r"/api/scrape/start")
    def start(app: App, m, q, b):
        if not app.jobs:
            raise ApiError(503, "the run layer is not available")
        checks = precheck(app, b or {})
        fails = [c for c in checks if c["level"] == "fail"]
        if fails:
            raise ApiError(409, "; ".join(c["text"] for c in fails))
        req = b or {}
        n = _norm(app, req)
        tools = {e["code"] for e in list_economies(app.settings) if e.get("tools")}
        engine = [c for c in n["economies"] if c not in tools]
        jobs = []
        if engine and n["mode"] == "same":
            jobs.append(plan_scrape(app, {**req, "economies": engine}))     # a second pass stays in the folder it is given
        else:
            for code in engine:                # a new crawl is filed by economy and source: one run, one folder each
                jobs.append(plan_scrape(app, {**req, "economies": [code]}))
        if "CN" in n["economies"]:
            jobs.append(cn_run.plan_cn(app, req))
        for job in jobs:
            app.jobs.submit(job)
        return 200, {"job": jobs[0].public(), "jobs": [j.public() for j in jobs]}


def frontier_prefix(s: Settings, code: str) -> str | None:
    """The environment prefix an adapter reads its frontier settings from (SSO_, LOM_, REGISTER_, ...)."""
    pkg = registry(s).get(code)
    if not pkg:
        return None
    path = p1_dir(s) / "src" / "p1_scrape" / "adapters" / pkg / "adapter.py"

    def load(p: Path):
        m = _FRONTIER_RX.search(p.read_text(encoding="utf-8", errors="replace"))
        return m.group(1) if m else ""
    return readers.cached(path, load) or None


def links_file(s: Settings, code: str) -> Path | None:
    p = links_dir(s, code) / "documents.jsonl"
    return p if p.is_file() else None


def _norm(app: App, req: dict) -> dict:
    s = app.settings
    econs = [str(e).upper() for e in (req.get("economies") or []) if str(e).strip()]
    scope = str(req.get("scope") or "relevant")
    if scope not in SCOPES:
        raise ApiError(400, f"scope must be one of {', '.join(SCOPES)}")
    forms = str(req.get("forms") or "")
    if forms not in FORMS:
        raise ApiError(400, "forms must be pdf, html, both or blank")
    mode = str(req.get("mode") or "fresh")
    if mode not in ("fresh", "same"):
        raise ApiError(400, "mode must be fresh or same")
    frontier = str(req.get("frontier") or "links")
    if frontier not in ("links", "discover"):
        raise ApiError(400, "frontier must be links or discover")
    folder = None
    if mode == "same":
        ref = str(req.get("folder") or "").strip()
        cand = Path(ref) if ref else None
        cand = (cand if cand and cand.is_absolute() else (REPO / ref)) if ref else None
        if not cand or not cand.is_dir():
            raise ApiError(400, "a second pass needs an existing crawl folder")
        root = s.runs_root.resolve()
        if root not in cand.resolve().parents:
            raise ApiError(403, "a second pass runs only over a folder under the runs root")
        folder = cand
    return {"economies": econs, "scope": scope, "forms": forms, "dry_run": bool(req.get("dry_run")),
            "mode": mode, "frontier": frontier, "folder": folder}


def precheck(app: App, req: dict) -> list[dict]:
    s = app.settings
    checks: list[dict] = []

    def add(level, check, text):
        checks.append({"level": level, "check": check, "text": text, "ok": level != "fail"})

    if not (p1_dir(s) / "scrape.py").is_file():
        add("fail", "stage", "The crawler stage is not in this repository.")
        return checks
    try:
        n = _norm(app, req)
    except ApiError as e:
        add("fail", "request", e.message)
        return checks
    econs = list_economies(s)
    crawlable = {e["code"] for e in econs if e["crawlable"]}
    tools = {e["code"] for e in econs if e.get("tools")}
    engine = [c for c in n["economies"] if c not in tools]
    if not n["economies"]:
        add("fail", "economies", "Choose at least one economy.")
    else:
        bad = [c for c in engine if c not in crawlable]
        if bad:
            add("fail", "economies", f"No crawler adapter for {', '.join(bad)}; those sources are checked by hand.")
        elif engine:
            add("ok", "economies", "Economies: " + ", ".join(engine) + (" through the crawler; China through its tools." if "CN" in n["economies"] else "."))
    if "CN" in n["economies"]:
        checks.extend(cn_run.precheck_cn(app, req))
    if not engine:
        return checks
    n["economies"] = engine
    ch = _probes.probe_chromium()
    add("ok" if ch["ok"] else "warn", "browser",
        "Chromium for Playwright is installed." if ch["ok"] else "Chromium is not installed for Playwright; portals that need a browser will fail. Run: python -m playwright install chromium")
    if n["frontier"] == "links":
        missing = [c for c in n["economies"] if not links_file(s, c)]
        if missing:
            add("fail", "frontier", f"No shipped link list for {', '.join(missing)}; choose live discovery.")
        else:
            add("ok", "frontier", "Replaying the shipped link list: no discovery crawl, the portal is asked only for the documents.")
    else:
        add("warn", "frontier", "Live discovery reads the portal's listings first; that can take up to 20 minutes and prints nothing while it runs.")
    if n["mode"] == "same":
        add("ok", "folder", f"Second pass over {rel_or_abs(n['folder'], REPO)}: laws already retrieved are skipped, so a folder with everything fetched must report 0.")
    else:
        add("ok", "folder", "A fresh folder for each economy, filed by economy and source under outputs/scrape/, so every selected law is fetched.")
    if n["scope"] == "relevant":
        add("ok", "scope", "Sample scope: titles matching the pillar 6 and 7 vocabulary plus the seed list; the crawler's 60-candidate cap is lifted so nothing is cut short.")
        add("warn", "seeds", "The seed list must come from the host's portal list only, never from the 2025 database. Check the registry before a live-test crawl.")
    elif n["scope"] == "all":
        add("warn", "scope", "All scope: every principal law on the portal, one to two thousand documents; hours at the polite pace.")
    delay = max(POLITE_DELAY_MS.get(c, DEFAULT_DELAY_MS) for c in n["economies"]) if n["economies"] else DEFAULT_DELAY_MS
    add("ok", "politeness", f"One request at a time, {delay / 1000:g} s between requests, a named contact in the user agent.")
    if n["dry_run"]:
        add("warn", "dry-run", "Dry run: lists what would be fetched and fetches nothing; no manifest is written.")
    return checks


LANE = {"pdf_native": "native PDF", "pdf_scanned": "scanned PDF", "html": "web page"}


def _ok_line(m, j):
    done = (j.progress.get("done") or 0) + 1
    total = j.progress.get("total")
    every = 1 if not total or total <= 25 else 10
    text = f"Fetched {done}" + (f" of {total}" if total else "") + f": {m[2]} ({LANE.get(m[3], m[3])})." if done % every == 0 or done == total else None
    return (text, {"+done": 1})


P1_RULES: list[tuple[re.Pattern, object]] = [
    (re.compile(r"^imports ok$"), lambda m, j: ("The crawler and its packages import.", None)),
    (re.compile(r"^\[health\] built-in tracker on"), lambda m, j: ("Started. Reading the portal listing first; with live discovery this can take up to 20 minutes and prints nothing.", None)),
    (re.compile(r"^\[crawl\] (\w\w): frontier links_file .*?(\d+) of (\d+) rows in scope"), lambda m, j: (f"{m[1]}: link list replayed, {m[2]} of {m[3]} documents in scope.", None)),
    (re.compile(r"^\[crawl\] (\w\w): inventory (\d+) item"), lambda m, j: (f"{m[1]}: the portal lists {m[2]} laws.", None)),
    (re.compile(r"^\[crawl\] (\w\w): WARNING capping (\d+) -> (\d+)"), lambda m, j: (f"{m[1]}: {m[2]} candidates capped to {m[3]} (MAX_CANDIDATES_PER_ECONOMY).", None)),
    (re.compile(r"^\[crawl\] (\w\w): (\d+) to fetch, (\d+) already retrieved"),
     lambda m, j: ((f"{m[1]}: {m[2]} to fetch, {m[3]} already retrieved." if int(m[2]) else f"{m[1]}: second pass, nothing new to fetch; {m[3]} already retrieved."),
                   {"total": int(m[2]), "done": 0, "unit": "documents"})),
    (re.compile(r"^\[dry-run\] (\w\w) (.+?) -> (\S+)$"), lambda m, j: ((f"Would fetch: {m[2]}" if (j.progress.get('done') or 0) < 12 else None), {"+done": 1})),
    (re.compile(r"^\[crawl\] OK (\w\w) (.+?) -> (\w+) \((\d+)\).*-> (\S+)$"), _ok_line),
    (re.compile(r"^\[crawl\] XX (\w\w) (.+?) -> .*\(HTTP (\d+)\)"), lambda m, j: (f"Could not fetch {m[2]} (HTTP {m[3]}).", {"+failed": 1})),
    (re.compile(r"^\[crawl\] XX (\w\w) (.+?) -> store error: (.*)"), lambda m, j: (f"Could not store {m[2]}: {m[3][:100]}", {"+failed": 1})),
    (re.compile(r"^\[crawl\] -- (\w\w) (.+?) -> skipped"), lambda m, j: (None, {"+skipped": 1})),
    (re.compile(r"^\[crawl\] throttled \(HTTP (\d+)\) on (.+?); cooldown (\d+)s"), lambda m, j: (f"The portal asked us to slow down (HTTP {m[1]}); waiting {m[3]} s.", None)),
    (re.compile(r"^\[health\] (\w\w): (\d+)/(\d+) attempted, (\d+) stored total"), lambda m, j: (None, {"done": int(m[2]), "total": int(m[3])})),
    (re.compile(r"^\[health\] THROTTLE SUSPECTED"), lambda m, j: ("The portal appears to have cut us off; this economy stopped early. Run again later and it resumes.", None)),
    (re.compile(r"^\[crawl\] retry round (\d+)"), lambda m, j: (f"Retry round {m[1]} for throttled documents.", None)),
    (re.compile(r"^\[crawl\] SKIP (\w\w): (\w+): (.*)"), lambda m, j: (f"{m[1]} skipped: {m[3][:160]}", {"+skipped_economies": 1})),
    (re.compile(r"^\[validate\] ERROR (.*)"), lambda m, j: (f"Manifest check error: {m[1][:120]}", None)),
    (re.compile(r"^\[crawl\] manifest has (\d+) row\(s\); validate (OK|FAILED)"), lambda m, j: (f"Manifest written: {m[1]} documents; schema check {m[2]}.", None)),
    (re.compile(r"ModuleNotFoundError: No module named '([^']+)'"), lambda m, j: (f"A Python package is missing: {m[1]}. Install stages/p1-scrape/requirements.txt (or requirements-demo.txt) or point RDTII_PYTHON_P1 at a Python that has it.", None)),
    (re.compile(r"Executable doesn't exist|playwright install"), lambda m, j: ("Chromium is not installed for Playwright: python -m playwright install chromium", None)),
]


def parse_p1(line: str, job: Job):
    for rx, fn in P1_RULES:
        m = rx.search(line)
        if m:
            return fn(m, job)
    return None


def _poll_status(out_dir: Path):
    last = {"k": None}

    def poll(job: Job):
        st = readers.cached(out_dir / "crawl_status.json", readers.read_json)
        if isinstance(st, dict):
            k = (st.get("attempted"), st.get("stored_total"), st.get("state"))
            if k != last["k"]:
                last["k"] = k
                job.bump(done=int(st.get("attempted") or 0), total=int(st.get("todo") or 0) or job.progress.get("total"))
                who = f"{st.get('economy')}: " if st.get("economy") else ""
                return f"{who}{st.get('attempted', 0)} attempted, {st.get('stored_total', 0)} stored ({st.get('state', '')})."
        return None
    return poll


def _all_skipped_fails(n_economies: int):
    """The crawler exits 0 when it skips an economy; a run that skipped every economy has crawled nothing."""
    def hook(job: Job, rc: int) -> None:
        if rc == 0 and (job.progress.get("skipped_economies") or 0) >= n_economies:
            job.progress["_fail"] = ("Nothing was crawled: every selected economy was skipped by the crawler. The reason is "
                                     "in the sentences above; with a stale link list choose live discovery.")
    return hook


def plan_scrape(app: App, req: dict) -> Job:
    s = app.settings
    p1 = p1_dir(s)
    n = _norm(app, req)
    codes = n["economies"]
    if n["mode"] == "same":
        out_dir = n["folder"]
    else:
        from .. import sources
        stamp = _time.strftime("%Y%m%d-%H%M%S")
        portal = sources.crawl_source(s, codes[0]) if len(codes) == 1 else None
        if portal:        # filed by economy, then by the portal the crawler reads
            out_dir = sources.scrape_run_dir(s, codes[0], portal["key"], stamp)
        else:             # several economies in one run, or no portal named: the older single folder
            out_dir = s.runs_root / "scrape" / f"{'-'.join(codes)}_{stamp}"
    extra = {"REQUEST_DELAY_MS": str(max(POLITE_DELAY_MS.get(c, DEFAULT_DELAY_MS) for c in codes)), "PYTHONPATH": "src"}
    if n["scope"] == "relevant":
        # the engine caps this scope at 60 candidates by default and warns; the page never lets a crawl be cut short
        extra["MAX_CANDIDATES_PER_ECONOMY"] = "100000"
    if n["frontier"] == "links":
        for c in codes:
            prefix = frontier_prefix(s, c)
            lf = links_file(s, c)
            if prefix and lf:
                extra[f"{prefix}_FRONTIER"] = "links_file"
                extra[f"{prefix}_LINKS_FILE"] = str(lf)
    try:
        env, public = build_env("p1", app.engines, app.key, {}, extra=extra, with_engine=False)
    except ChoiceError as e:
        raise ApiError(400, str(e)) from None
    py = s.python_for("p1")
    mods = "p1_scrape.cli, playwright, requests, tenacity, dateutil, yaml, jsonschema" + (", cryptography" if "MY" in codes else "")
    argv = [py, "scrape.py", "--economy", ",".join(codes), "--pillars", "6,7", "--out", str(out_dir), "--scope", n["scope"]]
    if n["forms"]:
        argv += ["--forms", n["forms"]]
    if n["dry_run"]:
        argv.append("--dry-run")
    steps = [
        Step(label="check the crawler imports", cwd=p1, env=env, parse=parse_p1,
             argv=[py, "-c", f"import {mods}; print('imports ok')"]),
        Step(label=("dry run: list what would be fetched" if n["dry_run"] else
                    f"crawl {', '.join(codes)}, scope {n['scope']}" + (", second pass" if n["mode"] == "same" else "")),
             cwd=p1, env=env, parse=parse_p1, argv=argv, poll=_poll_status(out_dir),
             on_done=_all_skipped_fails(len(codes))),
    ]
    title = ("Dry run: " if n["dry_run"] else "Crawl ") + ", ".join(codes) + f" ({n['scope']})"
    job = Job(stage="p1", title=title, steps=steps, out_dir=out_dir, env_public=public, redact=app.key.redact)
    job.say(f"{'Second pass over' if n['mode'] == 'same' else 'Fresh folder'} {rel_or_abs(out_dir, REPO)}; "
            f"{'shipped link list' if n['frontier'] == 'links' else 'live discovery'}; one request every {int(extra['REQUEST_DELAY_MS']) / 1000:g} s.")
    return job
