"""The Extraction tab: what can be fed to the extraction stage, what it holds, the Start button, and the
extraction outputs that exist.

An input is either a crawl folder (it has a manifest.csv) or a folder of hand-collected documents (PDF,
HTML or Word files and no manifest). The stage requires a manifest validated against its schema, so for
the second kind the interface writes one under the runs root and points the stage at the user's folder
for the bytes. Nothing is ever written into the user's folder or into the repository's tracked tree.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import shutil
import time
from collections import Counter
from pathlib import Path

from .. import detect, readers, readiness, sources
from ..envbuild import ChoiceError, NeedsKey, build_env
from ..jobs import Job, Step
from ..server import ApiError, App, rel_or_abs
from ..settings import REPO, Settings
from . import cn_run, scrape

DOC_SUFFIXES = {".pdf": "pdf", ".html": "html", ".htm": "html", ".docx": "docx", ".doc": "doc"}
CONTENT_TYPES = {".pdf": "application/pdf", ".html": "text/html", ".htm": "text/html",
                 ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                 ".doc": "application/msword"}
# The extraction stage parses HTML only from portals it knows (parse_html.py); anything else is parse_failed.
HTML_HOSTS = ("legislation.gov.au", "cac.gov.cn", "miit.gov.cn", "gov.cn")
# Economy -> ISO 639-3 language the stage's OCR and segmenter profiles expect (config/languages).
DEFAULT_LANGUAGE = {"SG": "eng", "AU": "eng", "MY": "eng", "IN": "eng", "CN": "zho", "LA": "lao", "TL": "por"}
# The economies built so far: the inbox offers these, and creates a folder for each at start.
HAND_ECONOMIES = ("SG", "AU", "MY", "TL", "LA", "CN")
LANGUAGES = [{"id": "eng", "label": "English"}, {"id": "zho", "label": "Chinese"}, {"id": "lao", "label": "Lao"},
             {"id": "por", "label": "Portuguese"}, {"id": "msa", "label": "Malay"}]
CONTRACT_VERSION = "0.3.0"
# The 28 manifest columns the crawler writes, in its order (models.py MANIFEST_FIELDS). Read from the demo
# manifest when present so a contract change is a file change, not a code change.
FALLBACK_COLUMNS = (
    "contract_version", "instrument_version", "doc_id", "economy", "source_url", "access_date", "source_type",
    "pdf_is_scanned", "local_path", "law_name_guess", "law_number_guess", "pillar_hint", "indicator_hints",
    "retrieval_method", "http_status", "http_headers_path", "content_type", "content_sha256", "byte_size",
    "page_count", "anchor_hint", "anchor_kind", "seed_query", "crawl_notes", "publication_date", "assent_date",
    "commencement_date", "in_force_status",
)
LANE_NAMES = {"A": "web page", "B": "native PDF", "C": "scanned PDF, OCR", "D": "Word document"}


LANG_LABEL = {x["id"]: x["label"] for x in LANGUAGES}


def recorded_languages(folder: Path) -> dict[str, str]:
    """doc_id -> the language the crawler recorded, read as the stage reads it: law_table.csv first, then the
    link rows in links_used/documents.jsonl. Documents absent from both are the ones the default fills."""
    out: dict[str, str] = {}
    lt = folder / "law_table.csv"
    if lt.is_file():
        loaded = readers.cached(lt, readers.read_csv)
        for r in (loaded[1] if loaded else []):
            doc, lang = (r.get("doc_id") or "").strip(), (r.get("language") or "").strip()
            if doc and lang and doc not in out:
                out[doc] = lang
    lu = folder / "links_used" / "documents.jsonl"
    if lu.is_file():
        def load(path: Path) -> dict[str, str]:
            found: dict[str, str] = {}
            with open(path, encoding="utf-8") as fh:
                for line in fh:
                    if not line.strip():
                        continue
                    meta = (json.loads(line).get("contract_meta") or {})
                    doc = ((meta.get("corpus") or {}).get("doc_id") or "").strip()
                    if doc and meta.get("language"):
                        found[doc] = str(meta["language"])
            return found
        for doc, lang in (readers.cached(lu, load) or {}).items():
            out.setdefault(doc, lang)
    return out


def language_plan(by_economy: dict) -> list[tuple[str, str]]:
    """(economy, language) from the stage's economy table; an economy it does not know reads as English."""
    return [(e, DEFAULT_LANGUAGE.get(e, "eng")) for e in sorted(k for k in by_economy if k)]


def describe_languages(folder: Path, rows: list[dict], by_economy: dict) -> dict:
    rec = recorded_languages(folder)
    counts = Counter(rec[r["doc_id"]] for r in rows if r.get("doc_id") in rec)
    blank_by = Counter((r.get("economy") or "").upper() for r in rows if r.get("doc_id") not in rec)
    plan = language_plan(by_economy)
    fill = ", ".join(f"{e} {LANG_LABEL.get(l, l)}" for e, l in plan)
    recorded = " · ".join(f"{k} {v}" for k, v in counts.most_common())
    blank = sum(blank_by.values())
    if counts and blank:
        line = f"{recorded} recorded by the crawler; {blank} not stated, filled from the economy table ({fill})"
    elif counts:
        line = f"{recorded}, recorded by the crawler"
    else:
        line = f"none recorded by the crawler; every document takes its economy's language ({fill})"
    return {"recorded": dict(counts), "blank": blank, "blank_by_economy": dict(blank_by), "plan": plan,
            "unknown_economies": [e for e, _ in plan if e not in DEFAULT_LANGUAGE],
            "passes": len({l for _, l in plan}) > 1, "line": line}


def register(app: App) -> None:
    @app.route("GET", r"/api/extract/inputs")
    def inputs(app: App, m, q, b):
        names = readers.econ_names(app.settings.stage_dirs["p3"])
        return 200, {"inputs": list_inputs(app.settings), "languages": LANGUAGES,
                     "default_language": DEFAULT_LANGUAGE, "html_hosts": list(html_hosts(app.settings)),
                     "economies": [{"code": c, "name": n} for c, n in names.items()],
                     "stage_present": (app.settings.stage_dirs["p2"] / "src" / "rdtii_p2" / "cli.py").is_file(),
                     "python": app.settings.python_for("p2")}

    @app.route("GET", r"/api/extract/describe")
    def describe(app: App, m, q, b):
        return 200, describe_input(resolve_folder(q.get("path", "")), "typed", app.settings)

    @app.route("POST", r"/api/extract/manifest/preview")
    def manifest_preview(app: App, m, q, b):
        b = b or {}
        folder = resolve_folder(b.get("path", ""))
        rows = build_manifest_rows(folder, b.get("economy", ""), s=app.settings)
        keep = ("doc_id", "economy", "source_type", "pdf_is_scanned", "page_count", "byte_size", "law_name_guess",
                "local_path", "source_url", "_status", "_method", "_action", "_url_basis", "_source")
        return 200, {"path": str(folder), "rows": [{k: r.get(k, "") for k in keep} for r in rows], "count": len(rows),
                     "ready": sum(1 for r in rows if r.get("_status") == "ready"),
                     "cannot_read": sum(1 for r in rows if r.get("_status") != "ready")}

    @app.route("POST", r"/api/extract/precheck")
    def precheck_route(app: App, m, q, b):
        return 200, {"checks": precheck(app, b or {})}

    @app.route("POST", r"/api/extract/start")
    def start(app: App, m, q, b):
        if not app.jobs:
            raise ApiError(503, "the run layer is not available")
        checks = precheck(app, b or {})
        fails = [c for c in checks if c["level"] == "fail"]
        if fails:
            raise ApiError(409, "; ".join(c["text"] for c in fails))
        job = plan_extract(app, b or {})
        app.jobs.submit(job)
        return 200, {"job": job.public()}

    @app.route("GET", r"/api/extract/outputs")
    def outputs(app: App, m, q, b):
        return 200, {"folders": list_outputs(app.settings)}


# ---- inputs -------------------------------------------------------------------------------------------

def resolve_folder(raw: str) -> Path:
    raw = (raw or "").strip()
    if not raw:
        raise ApiError(400, "path is required")
    p = Path(raw)
    p = p if p.is_absolute() else (REPO / p)
    if not p.is_dir():
        raise ApiError(404, f"{p} is not a folder on this machine")
    return p


def html_hosts(s: Settings | None = None) -> tuple[str, ...]:
    """The portals the extraction stage has a web-page parser for, read from the stage's own parse_html.py so
    the page and the stage cannot disagree; the list above is the fallback when that file cannot be read."""
    if s is None:
        return HTML_HOSTS
    path = s.stage_dirs["p2"] / "src" / "rdtii_p2" / "parse_html.py"

    def load(p: Path):
        m = re.search(r"^PORTAL_PARSERS[^=]*=\s*\{(.*?)^\}", p.read_text(encoding="utf-8"), re.M | re.S)
        return tuple(re.findall(r'^\s*"([a-z0-9.-]+\.[a-z]{2,})"\s*:', m.group(1), re.M)) if m else ()
    try:
        return readers.cached(path, load) or HTML_HOSTS
    except OSError:
        return HTML_HOSTS


def cn_out_name(run: Path, src: str) -> str:
    """The extraction output name for one publisher of a China tools run, in either folder layout."""
    return f"{run.name}_{src}" if run.name.startswith("CN_") else f"CN_{src}_{run.name}"


def describe_input(path: Path, kind: str, s: Settings | None = None) -> dict:
    if (path / "manifest.csv").is_file():
        d = scrape.describe_crawl_folder(path)
        d["kind"] = "crawled"
        d["origin"] = kind
        where = sources.scrape_identity(s, path) if s is not None else {}
        d["out_name"] = ("demo" if path.resolve() == (REPO / "demo_data" / "mini_raw").resolve()
                         else f"{where['economy']}_{where['source']}_{where['run']}" if where else path.name)
        d["economy_folder"], d["source"] = where.get("economy", ""), where.get("source", "")
        econs = [e for e in d["by_economy"] if e]
        d["language_default"] = DEFAULT_LANGUAGE.get(econs[0]) if len(econs) == 1 else None
        loaded = readers.cached(path / "manifest.csv", readers.read_csv)
        d["languages"] = describe_languages(path, loaded[1] if loaded else [], d["by_economy"])
        d["language_plan"] = d["languages"]["plan"]
        d["language_line"] = d["languages"]["line"]
        d["documents_present"] = d["raw_present"] == d["raw_checked"] if d["raw_checked"] else False
        d["recoverable"] = recoverable_count(path) if d["raw_present"] < d["raw_checked"] else 0
        return d
    if (path / "provenance.tsv").is_file():
        run = next((a for a in path.parents if cn_run.is_run(a)), None)
        if run:
            return describe_hand_folder(path, kind, economy="CN", out_name=cn_out_name(run, path.name), s=s)
    return describe_hand_folder(path, kind, s=s)


def folder_economy(name: str) -> str | None:
    """A folder named by a two-letter economy code declares that economy."""
    return name.upper() if re.fullmatch(r"[A-Za-z]{2}", name) else None


def economy_of_file(folder: Path, p: Path) -> str | None:
    parts = p.relative_to(folder).parts
    return folder_economy(parts[0]) if len(parts) > 1 else None


_DETECT_CACHE: dict = {}


def detect_cached(folder: Path, files: list[Path], declared: str | None, economy_of: dict | None) -> dict:
    """detect.detect_folder, remembered while the files' names, sizes and times stay the same."""
    key = (str(folder), declared, tuple((p.name, p.stat().st_size, p.stat().st_mtime_ns) for p in files[:60]))
    hit = _DETECT_CACHE.get(key)
    if hit is None:
        hit = detect.detect_folder(files, declared=declared, economy_of=economy_of)
        _DETECT_CACHE.clear()
        _DETECT_CACHE[key] = hit
    return hit


def describe_hand_folder(path: Path, kind: str, economy: str | None = None, out_name: str | None = None,
                         s: Settings | None = None) -> dict:
    files = document_files(path)
    total = sum(p.stat().st_size for p in files)
    fixed = economy
    # where the folder sits in the inbox says the economy, the designated source and the batch
    where = {} if fixed else (sources.inbox_identity(path, s.inbox_dir) if s is not None else {}) or {}
    if not where and not fixed and path.name.lower() != "inbox":
        where = sources.inbox_identity(path)             # a folder given by its path alone: read from its names
        if s is not None and not where.get("legacy"):
            where = {}                                   # outside the inbox only the older shapes count
    source_key = where.get("source", "")
    src = sources.find(s, where["economy"], source_key) if (s is not None and source_key) else None
    economy = economy or where.get("economy") or folder_economy(path.name)
    batch = where.get("batch", "")
    if source_key and out_name is None:
        out_name = f"{economy}_{source_key}" + (f"_{batch}" if batch else "")
    by_sub = Counter(economy_of_file(path, p) for p in files)
    per_subfolder = economy is None and bool(files) and all(by_sub) and len(by_sub) >= 1 and None not in by_sub
    if per_subfolder:
        by_economy = {k: v for k, v in sorted(by_sub.items())}
        economy_of = {p.name: economy_of_file(path, p) for p in files[:60]}
        detected = detect_cached(path, files, None, economy_of) if files else None
        econ_line = "from the folder names: " + ", ".join(f"{k} {v}" for k, v in by_economy.items())
    else:
        by_economy = {economy: len(files)} if economy and files else {}
        detected = detect_cached(path, files, economy, None) if files else None
        econ_line = (f"{economy}, fixed by the China tools run" if fixed else f"{economy}, from the inbox folder of the source {source_key}" if source_key
                     else f"{economy}, from the folder {path.parent.name if batch else path.name}" if economy
                     else "not named by the folder; " + (f"the text points to {detected['suggested_economy']}" if detected and detected.get("suggested_economy") else "choose it in Run"))
    plan = language_plan(by_economy) if by_economy else []
    return {"path": str(path), "id": rel_or_abs(path, REPO), "name": path.name, "kind": "hand_collected",
            "origin": kind, "manifest": False, "rows": len(files),
            "by_source_type": dict(Counter(DOC_SUFFIXES[p.suffix.lower()] for p in files)),
            "by_economy": by_economy, "economy": economy, "per_subfolder": per_subfolder, "detected": detected,
            "batch": batch, "out_name": out_name or (f"{economy}_{batch}" if batch else path.name),
            "source": source_key, "source_name": (src or {}).get("name", ""), "source_url": (src or {}).get("url", ""),
            "economy_source": "the China tools run" if fixed else ("the folder name" if economy else None),
            "size_bytes": total, "documents_present": bool(files), "language_default": None,
            "language_plan": plan, "language_line": econ_line,
            "note": ("No manifest: the interface writes one (document ids, hashes, sizes, page counts) and a law table "
                     "under the runs root before extraction runs, and never writes into this folder. HTML parses only "
                     "from the portals the stage knows: " + ", ".join(html_hosts(s)))}


def ensure_inbox(s: Settings) -> None:
    """The inbox and one subfolder per economy exist from the first start, so the guidance points at real folders."""
    try:
        s.inbox_dir.mkdir(parents=True, exist_ok=True)
        for code in HAND_ECONOMIES:
            (s.inbox_dir / code).mkdir(exist_ok=True)
            for src in sources.designated(s, code):
                (s.inbox_dir / code / src["key"]).mkdir(exist_ok=True)
    except OSError:
        pass


def document_files(path: Path, limit: int = 5000) -> list[Path]:
    files = []
    for p in sorted(path.rglob("*")):
        if p.is_file() and p.suffix.lower() in DOC_SUFFIXES:
            files.append(p)
            if len(files) >= limit:
                break
    return files


def list_inputs(s: Settings) -> list[dict]:
    out = []
    seen = set()

    def add(p: Path, kind: str):
        rp = p.resolve()
        if rp in seen or not p.is_dir():
            return
        seen.add(rp)
        if not (p / "manifest.csv").is_file() and cn_run.is_run(p):
            for src in cn_run.source_folders(p):
                out.append(describe_hand_folder(src, "China tools", economy="CN", out_name=cn_out_name(p, src.name), s=s))
            return
        out.append(describe_input(p, kind, s))

    add(s.handoff1_dir, "HANDOFF1_DIR")
    if s.inbox_dir.is_dir():
        is_batch = lambda d: bool(sources.BATCH_RX.fullmatch(d.name))  # noqa: E731
        filled = [p for p in sorted(s.inbox_dir.iterdir()) if p.is_dir() and folder_economy(p.name) and document_files(p, limit=1)]
        for p in filled:
            subs = [d for d in sorted(p.iterdir()) if d.is_dir()]
            # one designated source (every batch), then each of its batches
            for src in (d for d in subs if not is_batch(d) and document_files(d, limit=1)):
                add(src, "hand-collected source")
                for b in sorted((d for d in src.iterdir() if d.is_dir() and is_batch(d)), reverse=True):
                    if document_files(b, limit=1):
                        add(b, "hand-collected batch")
            add(p, "inbox")                                  # the economy's whole inbox, every source
            for sub in sorted((d for d in subs if is_batch(d)), reverse=True):
                if document_files(sub, limit=1):
                    add(sub, "inbox batch")                  # a batch of the older layout, filed under no source
        if len(filled) > 1:
            add(s.inbox_dir, "inbox, every economy")
    for p, _where in sources.scrape_runs(s):
        add(p, "interface crawl")
    shipped = s.stage_dirs["p1"] / "handoff1"
    if shipped.is_dir():
        for cc in sorted(shipped.iterdir()):
            if cc.is_dir():
                for p in sorted(cc.iterdir()):
                    if (p / "manifest.csv").is_file():
                        add(p, "shipped manifest")
    return out


# ---- recovering committed bytes by hash --------------------------------------------------------------

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def committed_by_hash() -> dict[str, Path]:
    """Loose documents committed once under demo_data/, keyed by sha256. The demo scan lives there because
    the manifest's local_path copy would double the repository's size for the same bytes."""
    demo = REPO / "demo_data"
    out = {}
    if demo.is_dir():
        for p in demo.iterdir():
            if p.is_file() and p.suffix.lower() in DOC_SUFFIXES:
                out[readers.cached(p, sha256_file)] = p
    return out


def missing_rows(folder: Path) -> list[dict]:
    loaded = readers.cached(folder / "manifest.csv", readers.read_csv)
    rows = loaded[1] if loaded else []
    return [r for r in rows if r.get("local_path") and not (folder / r["local_path"]).is_file()]


def recoverable_count(folder: Path) -> int:
    by_hash = committed_by_hash()
    return sum(1 for r in missing_rows(folder) if r.get("content_sha256") in by_hash)


def stage_input(s: Settings, folder: Path) -> Path:
    """Copy a crawl folder whose bytes are partly missing into the runs root and fill the gaps from the
    committed copies, verified by sha256. Returns the staged folder."""
    missing = missing_rows(folder)
    by_hash = committed_by_hash()
    unrecoverable = [r["doc_id"] for r in missing if r.get("content_sha256") not in by_hash]
    if unrecoverable:
        raise ApiError(409, f"{len(unrecoverable)} of the manifest's documents are not in this folder and cannot be "
                            f"recovered from committed copies (first: {unrecoverable[0]}). Run the crawler for this "
                            "corpus first; a shipped manifest describes documents without containing them.")
    dest = s.runs_root / "scrape" / folder.name
    dest.mkdir(parents=True, exist_ok=True)
    for name in ("manifest.csv", "manifest.jsonl", "crawl_log.jsonl", "law_table.csv", "cost_report.json"):
        if (folder / name).is_file():
            shutil.copy2(folder / name, dest / name)
    if (folder / "raw").is_dir():
        for src in (folder / "raw").rglob("*"):
            if src.is_file():
                d = dest / src.relative_to(folder)
                d.parent.mkdir(parents=True, exist_ok=True)
                if not d.is_file() or d.stat().st_size != src.stat().st_size:
                    shutil.copy2(src, d)
    for r in missing:
        d = dest / r["local_path"]
        d.parent.mkdir(parents=True, exist_ok=True)
        if not d.is_file():
            shutil.copy2(by_hash[r["content_sha256"]], d)
    return dest


# ---- a manifest for hand-collected documents --------------------------------------------------------

def manifest_columns() -> list[str]:
    demo = REPO / "demo_data" / "mini_raw" / "manifest.csv"
    loaded = readers.cached(demo, readers.read_csv)
    return list(loaded[0]) if loaded and loaded[0] else list(FALLBACK_COLUMNS)


_PAGE_RX = re.compile(rb"/Type\s*/Page(?![s/])")
_FONT_RX = re.compile(rb"/Font\b")


def pdf_probe(path: Path) -> tuple[int | None, bool | None]:
    """(page_count, looks_scanned) from the PDF's own bytes; a guess the stage re-checks per page."""
    try:
        data = path.read_bytes()
    except OSError:
        return None, None
    pages = len(_PAGE_RX.findall(data)) or None
    scanned = _FONT_RX.search(data) is None
    return pages, scanned


def slug(stem: str) -> str:
    s = re.sub(r"[^a-z0-9]", "", stem.lower())
    return (s[:32] or "doc")


def provenance_urls(folder: Path) -> dict[str, str]:
    """relative path, file name (or stem) -> source address, from every provenance sheet at or under the folder:
    the one a China tools run writes beside raw/, and the one the inbox keeps beside each batch of files."""
    out: dict[str, str] = {}
    sheets = [folder / "provenance.tsv"] + sorted(p for p in folder.rglob("provenance.tsv") if p.parent != folder)
    for sheet in sheets:
        if not sheet.is_file():
            continue
        try:
            with open(sheet, encoding="utf-8-sig", newline="") as f:
                rows = list(csv.DictReader(f, delimiter="\t"))
        except (OSError, csv.Error):
            continue
        rel = sheet.parent.relative_to(folder).as_posix()
        for r in rows:
            name = str(r.get("file") or r.get("file_saved_as") or "").strip()
            url = str(r.get("url") or "").strip()
            if name and url:
                out[name if rel in ("", ".") else f"{rel}/{name}"] = url
                out.setdefault(name, url)
    return out


def batch_of_file(folder: Path, p: Path) -> str:
    """The dated batch folder a file sits in, under the input folder or under its economy subfolder."""
    parts = p.relative_to(folder).parts[:-1]
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}_\d{6}", folder.name):
        return folder.name
    for part in parts:
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}_\d{6}", part):
            return part
    return ""


def build_manifest_rows(folder: Path, economy: str, source_urls: dict | None = None, s: Settings | None = None,
                        only_ready: bool = False) -> list[dict]:
    """One manifest row per file. The economy is the one given, else the one the folder's place in the inbox
    names, else the name of the subfolder each file sits in (the inbox holds one subfolder per economy).

    Each row also says, in keys that start with an underscore and never reach the manifest file, whether the
    stage can read the file (_status, _method, _action) and where its address came from (_url_basis, _source).
    only_ready=True leaves out the files that cannot be read."""
    here = (sources.inbox_identity(folder, s.inbox_dir) if s is not None else {}) or {}
    if not here:
        named = sources.inbox_identity(folder)
        here = named if (s is None or named.get("legacy")) else {}
    economy = (economy or "").strip().upper() or folder_economy(folder.name) or here.get("economy", "") or ""
    if economy and not re.fullmatch(r"[A-Z]{2}", economy):
        raise ApiError(400, "choose the economy these documents belong to (two-letter code)")
    cols = manifest_columns()
    rows = []
    seq: Counter = Counter()
    urls = dict(source_urls or {}) or provenance_urls(folder)
    fetched_by_tool = any(cn_run.is_run(a) for a in folder.parents)
    hosts = html_hosts(s)
    src_cache: dict[Path, dict | None] = {}

    def source_for(p: Path, econ: str) -> dict | None:
        """The designated source a file was filed under, from the inbox folder it sits in."""
        if s is None:
            return None
        if p.parent not in src_cache:
            ident = sources.inbox_identity(p.parent, s.inbox_dir) or {}
            src_cache[p.parent] = sources.find(s, econ, ident["source"]) if ident.get("source") else None
        return src_cache[p.parent]

    for p in document_files(folder):
        econ = economy or economy_of_file(folder, p)
        if not econ:
            raise ApiError(400, f"choose the economy these documents belong to, or put {p.name} in a folder named by its economy code")
        ext = p.suffix.lower()
        kind = DOC_SUFFIXES[ext]
        base = slug(p.stem)
        seq[(econ, base)] += 1
        doc_id = f"{econ.lower()}-{base}-{seq[(econ, base)]:03d}"
        st = p.stat()
        page_count, scanned = (pdf_probe(p) if kind == "pdf" else (None, None))
        rel = p.relative_to(folder).as_posix()
        own = urls.get(rel) or urls.get(p.name) or urls.get(p.stem) or urls.get(p.stem.split("__")[0]) or ""
        src = source_for(p, econ)
        # a file with no address of its own is cited to its designated source's page, and says so
        address = own or (src or {}).get("url", "")
        basis = "the file's own address" if own else ("the source's page" if address else "")
        verdict = readiness.judge(p, kind, sources.host_of(address), hosts)
        row = {c: "" for c in cols}
        row.update({"_status": verdict["status"], "_method": verdict["method"], "_action": verdict["action"],
                    "_url_basis": basis, "_source": (src or {}).get("key", "")})
        row.update({
            "contract_version": CONTRACT_VERSION, "doc_id": doc_id, "economy": econ,
            "source_url": address,
            "access_date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(st.st_mtime)),
            "source_type": ("pdf_scanned" if scanned else "pdf_native") if kind == "pdf" else kind,
            "pdf_is_scanned": ("true" if scanned else "false") if kind == "pdf" else "",
            "local_path": p.relative_to(folder).as_posix(),
            "law_name_guess": re.sub(r"[_\-]+", " ", p.stem).strip(),
            "retrieval_method": "requests" if fetched_by_tool else "hand_collected", "http_status": "", "http_headers_path": "",
            "content_type": CONTENT_TYPES[ext], "content_sha256": readers.cached(p, sha256_file),
            "byte_size": str(st.st_size), "page_count": str(page_count) if page_count else "",
            "crawl_notes": ("fetched by the China tools; manifest written by the interface" if fetched_by_tool else "collected by hand; manifest written by the interface")
                           + (f"; source {src['key']}" if src else "")
                           + (f"; batch {batch_of_file(folder, p)}" if batch_of_file(folder, p) else "")
                           + ("; address is the source's page, the document's own was not recorded" if address and not own else ""),
        })
        rows.append(row)
    if not rows:
        raise ApiError(404, f"no PDF, HTML or Word files under {folder}")
    if only_ready:
        ready = [r for r in rows if r["_status"] == "ready"]
        if not ready:
            raise ApiError(409, f"none of the {len(rows)} file(s) under {folder.name} can be read as they are; "
                                "the Readiness list in Set up says what to do for each")
        return ready
    return rows


def write_manifest(s: Settings, folder: Path, rows: list[dict], left_out: list[dict] | None = None) -> Path:
    where = sources.inbox_identity(folder, s.inbox_dir) or {}
    stamp = time.strftime("%Y%m%d-%H%M%S")
    if where.get("source"):          # filed like a crawl: by economy, then source
        dest = sources.scrape_run_dir(s, where["economy"], where["source"], f"hand_{where.get('batch') or 'all'}_{stamp}")
    else:
        dest = s.runs_root / "scrape" / f"hand_{slug(folder.name)}_{stamp}"
    dest.mkdir(parents=True, exist_ok=True)
    cols = manifest_columns()
    with open(dest / "manifest.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in cols})
    with open(dest / "law_table.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["law_name", "doc_id", "economy", "language", "batch", "source"])
        w.writeheader()
        for r in rows:
            econ = (r.get("economy") or "").upper()
            w.writerow({"law_name": r.get("law_name_guess", ""), "doc_id": r["doc_id"], "economy": econ,
                        "language": DEFAULT_LANGUAGE.get(econ, "eng"),
                        "batch": batch_of_file(folder, folder / r["local_path"]), "source": r.get("_source", "")})
    if left_out:
        with open(dest / "left_out.csv", "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["file", "is", "what_to_do"])
            w.writeheader()
            for r in left_out:
                w.writerow({"file": r.get("local_path", ""), "is": r.get("source_type", ""), "what_to_do": r.get("_action", "")})
    (dest / "MANIFEST_NOTE.md").write_text(
        f"# Written by the interface\n\nManifest and law table for the hand-collected folder `{folder}`. The bytes stay "
        f"in that folder; `local_path` is relative to it. retrieval_method is `hand_collected`. A source URL is the "
        f"address noted for the file in the provenance sheet beside it; a file with none is cited to its designated "
        f"source's page, and its crawl note says so. The language is the economy's, from the stage's economy table, "
        f"and is also passed to the stage as the default for every document."
        + (f" {len(left_out)} file(s) the reader cannot take were left out; `left_out.csv` lists each with what to do.\n"
           if left_out else "\n"), encoding="utf-8")
    return dest / "manifest.csv"


# ---- the job --------------------------------------------------------------------------------------------

P2_RULES: list[tuple[re.Pattern, object]] = [
    (re.compile(r"^\[P2\] Manifest OK: (\d+) rows"), lambda m, j: (f"Manifest accepted: {m[1]} documents.",
                                                                  {"total": int(m[1]), "done": 0, "unit": "documents"})),
    (re.compile(r"^\[P2\] Preflight OK"), lambda m, j: ("Tools found; starting to read.", None)),
    (re.compile(r"^\[P2\] OCR pre-pass: (\d+) page\(s\) across (\d+) document\(s\), (\d+) already cached, (\d+) workers"),
     lambda m, j: (f"OCR: {m[1]} pages in {m[2]} scanned document(s), {m[3]} already cached, {m[4]} workers.",
                   {"total": int(m[1]), "done": int(m[3]) if False else 0, "unit": "pages"})),
    (re.compile(r"^\[P2\] OCR pre-pass: (\d+)/(\d+) pages, (\d+) docs cached, ([\d.]+) pages/s, ~(\d+) min left"),
     lambda m, j: (f"OCR {m[1]} of {m[2]} pages, about {m[5]} min left.", {"done": int(m[1]), "total": int(m[2]), "unit": "pages"})),
    (re.compile(r"^\[P2\] OCR pre-pass done: (\d+) pages in ([\d.]+) min"),
     lambda m, j: (f"OCR finished: {m[1]} pages in {m[2]} min.", {"done": int(m[1]), "total": int(m[1])})),
    (re.compile(r"^\[P2\] OCR pre-pass: nothing to do, (\d+) document"), lambda m, j: ("OCR: every scanned page is already cached.", None)),
    (re.compile(r"^\[P2\] no scanned documents"), lambda m, j: ("No scanned documents; OCR skipped.", None)),
    (re.compile(r"^\[P2\] (\S+): lane ([ABCD]) \((\w+)\)"),
     lambda m, j: (f"Reading {(j.progress.get('done') or 0) + 1}" + (f" of {j.progress['total']}" if j.progress.get('total') else "")
                   + f": {m[1]} ({LANE_NAMES.get(m[2], m[2])}).", {"+done": 1})),
    (re.compile(r"^\[P2\] (\S+): (\d+) records grounded, (\d+) dropped"), lambda m, j: (f"{m[1]}: {m[2]} provisions found.", None)),
    (re.compile(r"^\[P2\] (\S+): raw file missing"), lambda m, j: (f"{m[1]}: its file is missing; skipped.", {"+failed": 1})),
    (re.compile(r"^\[P2\] (\S+): lane (\w) failed: (.*)"), lambda m, j: (f"{m[1]} could not be read: {m[3][:120]}", {"+failed": 1})),
    (re.compile(r"rerouted to Lane C"), lambda m, j: ("A PDF marked native has no text layer; sending it through OCR instead.", None)),
    (re.compile(r"^\[P2\] not read: (\d+) of (\d+) documents"), lambda m, j: (f"{m[1]} of {m[2]} documents excluded by the law table.", None)),
    (re.compile(r"^\[P2\] run complete: (\d+) docs"), lambda m, j: (f"Done: {m[1]} documents read; provisions, law list and status written.", None)),
    (re.compile(r"ModuleNotFoundError: No module named '([^']+)'"),
     lambda m, j: (f"A Python package is missing: {m[1]}. Install the stage's requirements (pip install -r "
                   "requirements-demo.txt) or point RDTII_PYTHON_P2 at a Python that has them.", None)),
    (re.compile(r"^imports ok$"), lambda m, j: ("The extraction stage and its packages import.", None)),
    (re.compile(r"[Tt]esseract.*not (found|installed)|TesseractNotFoundError"),
     lambda m, j: ("Tesseract is not installed or not on PATH: " + probes.install_hint("tesseract"), None)),
]


def parse_p2(line: str, job: Job):
    for rx, fn in P2_RULES:
        m = rx.search(line)
        if m:
            return fn(m, job)
    return None


def precheck(app: App, req: dict) -> list[dict]:
    """Pre-flight for an extraction run, in plain words: stage, interpreter, input, documents, language, OCR, output."""
    from urllib.parse import urlparse

    from .. import probes
    s = app.settings
    checks: list[dict] = []

    def add(level: str, check: str, text: str) -> None:
        checks.append({"level": level, "check": check, "text": text, "ok": level != "fail"})

    p2 = s.stage_dirs["p2"]
    if not (p2 / "src" / "rdtii_p2" / "cli.py").is_file():
        add("fail", "stage", "The extraction stage is not in this repository.")
        return checks
    add("ok", "stage", "Extraction stage present.")
    py = s.python_for("p2")
    if Path(py).is_file() or shutil.which(py):
        add("ok", "interpreter", f"Interpreter: {py}.")
    else:
        add("fail", "interpreter", f"Interpreter not found: {py}. Set RDTII_PYTHON_P2 to a Python that has the stage's packages.")

    try:
        folder = resolve_folder(req.get("input", ""))
        desc = describe_input(folder, "request", s)
    except ApiError as e:
        add("fail", "input", getattr(e, "message", None) or str(e))
        return checks
    if desc.get("error"):
        add("fail", "input", str(desc["error"]))
        return checks
    kind = desc["kind"]
    types = desc.get("by_source_type") or {}
    if kind == "crawled":
        add("ok", "input", f"Crawl folder {desc['name']}: {desc['rows']} documents, "
                           + (", ".join(f"{k} {v}" for k, v in types.items()) or "no documents") + ".")
        if desc.get("raw_checked") and desc["raw_present"] < desc["raw_checked"]:
            missing = desc["raw_checked"] - desc["raw_present"]
            rec = int(desc.get("recoverable") or 0)
            if rec >= missing:
                add("warn", "documents", f"{missing} document(s) are not in the folder; committed copies are restored by hash into a staged copy.")
            else:
                add("fail", "documents", f"{missing} document(s) are not in the folder and only {rec} can be restored by hash. Run the crawler for this folder first.")
        else:
            add("ok", "documents", "Every document the manifest lists is present.")
        loaded = readers.cached(folder / "manifest.csv", readers.read_csv)
        rows = loaded[1] if loaded else []
        hosts = sorted({(urlparse(r.get("source_url") or r.get("url") or "").hostname or "") for r in rows if r.get("source_type") == "html"} - {""})
        known = html_hosts(s)
        odd = [h for h in hosts if not readiness.match_host(h, known)]
        if odd:
            add("warn", "html", f"Web pages from {', '.join(odd)}: the reader has parsers for {len(known)} registered hosts only; pages from other hosts are not read.")
    else:
        econ = str(req.get("economy") or desc.get("economy") or "").strip().upper()
        names = readers.econ_names(s.stage_dirs["p3"])
        det = desc.get("detected") or {}
        if desc.get("per_subfolder"):
            codes = list(desc["by_economy"])
            bad = [c for c in codes if names and c not in names]
            if bad:
                add("fail", "economy", f"Folder name(s) that are not an economy code: {', '.join(bad)}.")
            else:
                add("ok", "economy", "Economies from the folder names: " + ", ".join(f"{names.get(c, c)} ({c}) {n}" for c, n in desc["by_economy"].items()) + ".")
        elif not econ:
            hint = det.get("suggested_economy")
            add("fail", "economy", "Choose the economy these documents belong to; it names every document id."
                                   + (f" The text points to {names.get(hint, hint)} ({hint}); confirm it in Run." if hint else ""))
        elif names and econ not in names:
            add("fail", "economy", f"Unknown economy code {econ}.")
        else:
            add("ok", "economy", f"Economy: {names.get(econ, econ)} ({econ})" + (f", from {desc['economy_source']}." if desc.get("economy_source") else "."))
        if det:
            if det["readable"] == 0:
                add("warn", "detection", f"Text check: {det['line']}.")
            elif det["mismatch"]:
                add("warn", "detection", f"Text check: {det['mismatch']} file(s) do not fit their folder: "
                                         + ", ".join(det["mismatch_files"]) + ". Move them, or expect the wrong language.")
            else:
                add("ok", "detection", f"Text check: {det['line']}; consistent with the folder.")
        n = int(desc.get("rows") or 0)
        if not n:
            add("fail", "input", "No PDF, HTML or Word file in this folder.")
        else:
            add("ok", "input", f"{n} hand-collected file(s): " + ", ".join(f"{k} {v}" for k, v in types.items())
                               + ". The interface writes manifest.csv and law_table.csv for them."
                               + (f" Source: {desc['source_name'] or desc['source']}." if desc.get("source") else ""))
        hand_rows = []
        if n and (desc.get("per_subfolder") or (econ and (not names or econ in names))):
            try:
                hand_rows = build_manifest_rows(folder, "" if desc.get("per_subfolder") else econ, s=s)
            except ApiError as e:
                add("fail", "input", getattr(e, "message", None) or str(e))
        if hand_rows:
            cannot = [r for r in hand_rows if r["_status"] != "ready"]
            ready_n = len(hand_rows) - len(cannot)
            if desc.get("source"):
                # a designated source: only what the reader can take goes into the run
                if not ready_n:
                    add("fail", "readiness", f"None of the {len(hand_rows)} file(s) can be read as they are. "
                                             + " ".join(f"{Path(r['local_path']).name}: {r['_action']}" for r in cannot[:3]))
                elif cannot:
                    add("warn", "readiness", f"{ready_n} of {len(hand_rows)} file(s) will be read; {len(cannot)} are left out. "
                                             + " ".join(f"{Path(r['local_path']).name}: {r['_action']}" for r in cannot[:3])
                                             + (" And more: see Readiness in Set up." if len(cannot) > 3 else ""))
                else:
                    add("ok", "readiness", f"All {ready_n} file(s) can be read.")
                unaddressed = sum(1 for r in hand_rows if r["_status"] == "ready" and r["_url_basis"] != "the file's own address")
                if unaddressed:
                    add("warn", "address", f"{unaddressed} file(s) have no address of their own and will be cited to the "
                                           "source's page. Type each file's address in the Hand-collected block to cite the document itself.")
            elif cannot:
                add("warn", "readiness", f"{len(cannot)} of {len(hand_rows)} file(s) will fail in the run: "
                                         + " ".join(f"{Path(r['local_path']).name}: {r['_action']}" for r in cannot[:3]))
            # only a PDF that really has no text layer needs OCR
            types = dict(Counter(r["source_type"] for r in hand_rows if r["_status"] == "ready" or not desc.get("source")))

    if kind == "crawled":
        lang_info = desc["languages"]
        if lang_info["unknown_economies"]:
            add("warn", "language", f"No entry in the language table for {', '.join(lang_info['unknown_economies'])}: "
                                    "their unlabelled documents are read as English.")
        add("ok", "language", "Languages: " + lang_info["line"] + ("; read in one pass per economy." if lang_info["passes"] else "."))
    elif desc.get("per_subfolder"):
        add("ok", "language", "Languages from the economy table: " + ", ".join(f"{c} {LANG_LABEL.get(l, l)}" for c, l in language_plan(desc["by_economy"])) + ".")
    elif econ and (not names or econ in names):
        lang = DEFAULT_LANGUAGE.get(econ)
        if lang:
            add("ok", "language", f"Language: {LANG_LABEL.get(lang, lang)} ({lang}), from the economy table for {econ}; "
                                  "passed to the stage for every document and written into the law table.")
        else:
            add("warn", "language", f"No entry in the language table for {econ}: the documents are read as English.")

    scanned = int(types.get("pdf_scanned") or 0) or (int(types.get("pdf") or 0) if kind != "crawled" else 0)
    if kind != "crawled" and "pdf_scanned" not in types and "pdf" not in types:
        scanned = 0
    if scanned:
        t = probes.probe_tesseract()
        if t.get("ok"):
            add("ok", "ocr", f"{scanned} scanned PDF(s) go through OCR; Tesseract found" + (f" at {t['path']}" if t.get("path") else "") + ".")
        else:
            add("fail", "ocr", f"{scanned} scanned PDF(s) need OCR, but Tesseract was not found. "
                               f"Install it ({probes.install_hint('tesseract')}) or set RDTII_TESSERACT to the program.")
    else:
        add("ok", "ocr", "No scanned PDF: no OCR needed.")
    if req.get("pack", "fast") not in ("fast", "best"):
        add("fail", "ocr", "The OCR pack must be fast or best.")

    out_name = re.sub(r"[^A-Za-z0-9_.-]", "_", str(req.get("out_name") or desc.get("out_name") or folder.name))[:60]
    out_dir = s.runs_root / "extract" / out_name
    if out_dir.is_dir():
        add("warn", "output", f"{rel_or_abs(out_dir, REPO)} exists: the run reuses its OCR cache and frozen text. Clear OCR cache first for a fresh OCR.")
    else:
        add("ok", "output", f"Writes to {rel_or_abs(out_dir, REPO)}, a new folder.")
    return checks


def plan_extract(app: App, req: dict) -> Job:
    s = app.settings
    p2 = s.stage_dirs["p2"]
    if not (p2 / "src" / "rdtii_p2" / "cli.py").is_file():
        raise ApiError(409, "the extraction stage is not in this repository")
    folder = resolve_folder(req.get("input", ""))
    desc = describe_input(folder, "request", s)
    pack = req.get("pack") or "fast"
    if pack not in ("fast", "best"):
        raise ApiError(400, "pack must be fast or best")
    try:
        workers = max(1, min(32, int(req.get("workers") or 16)))
    except ValueError:
        raise ApiError(400, "workers must be a number") from None
    out_name = re.sub(r"[^A-Za-z0-9_.-]", "_", str(req.get("out_name") or desc.get("out_name") or folder.name))[:60]
    out_dir = s.runs_root / "extract" / out_name
    notes: list[str] = []

    if desc["kind"] == "crawled":
        raw_dir = folder
        if desc["raw_checked"] and desc["raw_present"] < desc["raw_checked"]:
            raw_dir = stage_input(s, folder)
            notes.append(f"Staged a copy under {rel_or_abs(raw_dir, REPO)} and restored "
                         f"{len(missing_rows(folder))} committed document(s) by hash.")
        manifest = raw_dir / "manifest.csv"
        loaded = readers.cached(manifest, readers.read_csv)
        rows = loaded[1] if loaded else []
        n_docs = len(rows)
        plan = language_plan(desc["by_economy"])
    else:
        every = build_manifest_rows(folder, str(req.get("economy") or desc.get("economy") or ""),
                                    req.get("source_urls") or None, s=s)
        # from a designated source only what the reader can take goes into the run; elsewhere every file, as before
        left_out = [r for r in every if r["_status"] != "ready"] if desc.get("source") else []
        rows = [r for r in every if r not in left_out]
        if not rows:
            raise ApiError(409, f"none of the {len(every)} file(s) can be read as they are; the Readiness list in Set up says what to do for each")
        manifest = write_manifest(s, folder, rows, left_out)
        raw_dir = folder
        n_docs = len(rows)
        plan = language_plan(Counter(r["economy"] for r in rows))
        notes.append(f"Wrote a manifest and a law table ({', '.join(LANG_LABEL.get(l, l) for _, l in plan)}) for {n_docs} "
                     f"hand-collected document(s) under {rel_or_abs(manifest.parent, REPO)}."
                     + (f" {len(left_out)} file(s) the reader cannot take were left out; left_out.csv lists them." if left_out else ""))

    try:
        env, public = build_env("p2", app.engines, app.key, req.get("choices") or {},
                                extra={"HANDOFF1_DIR": str(raw_dir), "OUT_DIR": str(out_dir), "OCR_ENGINE": "tesseract"})
    except ChoiceError as e:
        raise ApiError(400, str(e)) from None
    except NeedsKey:
        env, public = build_env("p2", app.engines, app.key, {"RDTII_ENGINE": next((i for i in app.engines.ids() if not app.engines.get(i).get("key_env")), app.engines.selected)},
                                extra={"HANDOFF1_DIR": str(raw_dir), "OUT_DIR": str(out_dir), "OCR_ENGINE": "tesseract"})
    py = s.python_for("p2")
    # The crawler's per-document language always wins inside the stage; --default-language fills the documents it
    # left blank and is recorded as registry_default. One pass when every economy reads in one language, else one
    # pass per economy with that economy's language: the stage merges its outputs per document.
    langs = sorted({lang for _, lang in plan}) or ["eng"]
    passes: list[tuple[str | None, str]] = [(None, langs[0])] if len(langs) == 1 else plan

    def econ_of(r: dict) -> str:
        return (r.get("economy") or "").strip().upper()

    common = ["--manifest", str(manifest), "--raw", str(raw_dir), "--out", str(out_dir)]
    steps = [Step(label="check the extraction stage imports", cwd=p2, env=env, parse=parse_p2,
                  argv=[py, "-c", "import rdtii_p2.cli, pypdfium2, pytesseract, jsonschema, pydantic; print('imports ok')"])]
    for econ, lang in passes:
        sel = (["--economy", econ] if econ else []) + ["--default-language", lang]
        mine = [r for r in rows if econ is None or econ_of(r) == econ]
        scanned = sum(1 for r in mine if r.get("source_type") == "pdf_scanned")
        who = f" for {econ}" if econ else ""
        if scanned:
            steps.append(Step(label=f"OCR the scanned pages{who}, {workers} workers, {pack} pack", cwd=p2, env=env, parse=parse_p2,
                              argv=[py, "-m", "rdtii_p2.cli", "ocr", *common, *sel, "--workers", str(workers), "--pack", pack],
                              poll=lambda job: None))
        run_argv = [py, "-m", "rdtii_p2.cli", "run", *common, *sel, "--skip-tags"]
        if req.get("force"):
            run_argv.append("--force")
        steps.append(Step(label=f"read and segment {len(mine)} document(s){who} in {LANG_LABEL.get(lang, lang)}, "
                                "freeze the text, verify every quote",
                          cwd=p2, env=env, parse=parse_p2, argv=run_argv, poll=_poll_doc_status(out_dir)))
    title_langs = ", ".join(LANG_LABEL.get(l, l) for l in langs)
    job = Job(stage="p2", title=f"Extract {folder.name} ({n_docs} documents, {title_langs})", steps=steps, out_dir=out_dir,
              env_public=public, redact=app.key.redact)
    for n in notes:
        job.say(n)
    return job


def _poll_doc_status(out_dir: Path):
    last = {"n": -1}

    def poll(job: Job):
        f = out_dir / "doc_status.jsonl"
        if f.is_file():
            n = readers.count_lines(f)
            if n != last["n"]:
                last["n"] = n
                return f"{n} document status line(s) written so far."
        return None
    return poll


# ---- outputs ---------------------------------------------------------------------------------------------

def describe_output(path: Path, kind: str) -> dict:
    status_file = path / "doc_status.jsonl"
    statuses: Counter = Counter()
    lanes: Counter = Counter()
    provisions_total = 0
    if status_file.is_file():
        for row in readers.cached(status_file, readers.read_jsonl) or []:
            statuses[row.get("status", "?")] += 1
            lanes[row.get("lane") or "?"] += 1
            provisions_total += int(row.get("n_provisions") or 0)
    prov = path / "provisions.jsonl"
    cost = readers.cached(path / "cost_report.json", readers.read_json)
    return {
        "path": str(path), "id": rel_or_abs(path, REPO), "name": path.name, "kind": kind,
        "documents": sum(statuses.values()), "by_status": dict(statuses), "by_lane": dict(lanes),
        "provisions": provisions_total, "provisions_file": prov.is_file(),
        "laws": readers.count_lines(path / "laws.jsonl") if (path / "laws.jsonl").is_file() else 0,
        "wallclock_seconds": (cost or {}).get("wallclock_seconds") if isinstance(cost, dict) else None,
        "cache_bytes": {"ocr": readers.dir_size(path / "ocr") if (path / "ocr").is_dir() else 0,
                        "source_text": readers.dir_size(path / "source_text") if (path / "source_text").is_dir() else 0},
    }


def list_outputs(s: Settings) -> list[dict]:
    out = []
    seen = set()

    def add(p: Path, kind: str):
        rp = p.resolve()
        if rp in seen or not p.is_dir():
            return
        seen.add(rp)
        out.append(describe_output(p, kind))

    root = s.runs_root / "extract"
    if root.is_dir():
        for p in sorted(root.iterdir(), reverse=True):
            add(p, "interface run")
    add(s.handoff2_dir, "HANDOFF2_DIR")
    return out


def valid_doc_id(doc_id: str) -> bool:
    return bool(re.fullmatch(r"[a-z]{2}-[a-z0-9]+-\d{3}", doc_id))
