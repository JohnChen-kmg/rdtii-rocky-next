"""The inbox: documents collected by hand from an economy's designated sources, filled from the Scraping tab.

A file dropped on the page is written under inbox/<economy>/<source>/<batch>/ with its own name, once, and
the address it came from is noted beside it in provenance.tsv, the way the China collection has always
recorded its hand-collected files. Only the sources the stage's own files designate are offered: an
economy's watchlist, and for China the publishers its tools mark "by hand". There is no box for anything
else, because a file with no known source has no reading method and no citation.

Nothing but the files and that one sheet is ever written here: the manifest and the law table for these
files go under the runs root when Extraction runs.
"""
from __future__ import annotations

import csv
import hashlib
import io
import re
import time
import zipfile
from pathlib import Path

from .. import readers, readiness, sources, weburl
from ..server import ApiError, App, rel_or_abs
from ..settings import REPO, Settings
from . import extract

BATCH_RX = sources.BATCH_RX                      # the drop's local time, named by the page
ALLOWED = {".pdf", ".html", ".htm", ".docx", ".doc"}
ARCHIVES = {".zip"}                              # unpacked on arrival: the national database exports laws in bulk
MAX_BYTES = 250 * 1024 * 1024
MAX_MEMBERS = 5000                               # files taken from one archive
MAX_UNPACKED = 2 * 1024 * 1024 * 1024            # bytes taken from one archive
PROVENANCE = "provenance.tsv"
PROV_COLUMNS = ["file", "url", "url_basis", "fetched_on", "source"]


def register(app: App) -> None:
    @app.route("GET", r"/api/inbox")
    def inbox(app: App, m, q, b):
        return 200, describe(app.settings)

    @app.route("GET", r"/api/inbox/files")
    def files(app: App, m, q, b):
        s = app.settings
        code = economy_code(s, q.get("economy", ""))
        key = (q.get("source") or "").strip()
        src = source_of(s, code, key) if key else None
        folder = s.inbox_dir / code / src["key"] if src else s.inbox_dir / code
        return 200, {"economy": code, "source": key, "files": list_files(folder, s, src)}

    @app.route("POST", r"/api/inbox/upload")
    def upload(app: App, m, q, b):
        if not isinstance(b, (bytes, bytearray)):
            raise ApiError(400, "send the file's bytes as the body, with Content-Type application/octet-stream")
        return 200, save(app.settings, q.get("economy", ""), q.get("source", ""), q.get("name", ""), bytes(b),
                         q.get("batch", ""), q.get("url", ""))

    @app.route("POST", r"/api/inbox/address")
    def address(app: App, m, q, b):
        b = b or {}
        return 200, set_address(app.settings, str(b.get("economy", "")), str(b.get("source", "")),
                                str(b.get("batch", "")), str(b.get("file", "")), str(b.get("url", "")))


# ---- who and where ----------------------------------------------------------------------------------

def economies(s: Settings) -> dict[str, str]:
    names = readers.econ_names(s.stage_dirs["p3"])
    return names or {c: c for c in extract.DEFAULT_LANGUAGE}


def economy_code(s: Settings, raw: str) -> str:
    code = (raw or "").strip().upper()
    if code not in economies(s):
        raise ApiError(400, f"unknown economy code {code or '(none)'}; choose one on the page")
    return code


def source_of(s: Settings, code: str, key: str) -> dict:
    """The designated source of that economy with that folder key, or a refusal that names the choices."""
    key = (key or "").strip().lower()
    listed = sources.designated(s, code)
    hit = next((x for x in listed if x["key"] == key), None)
    if not hit:
        names = ", ".join(x["key"] for x in listed) or "none designated"
        raise ApiError(400, f"choose one of {code}'s designated sources ({names}); files from any other place are not taken")
    return hit


def safe_name(raw: str, allowed: set[str] | None = None) -> str:
    """The file's own name, without any path, in the allowed formats. A long name loses its middle, never its
    suffix: the suffix is what says how the file is read."""
    allowed = ALLOWED if allowed is None else allowed
    name = Path((raw or "").replace("\\", "/")).name
    name = re.sub(r"[^\w.\- ()\[\]]+", "_", name).strip(" .")
    if not name or name.startswith("."):
        raise ApiError(400, "the file needs a name")
    suffix = Path(name).suffix
    if suffix.lower() not in allowed:
        raise ApiError(400, f"only PDF, HTML or Word files are accepted: {name}")
    stem = name[: len(name) - len(suffix)]
    return stem[: 160 - len(suffix)].rstrip(" .") + suffix


# ---- the address sheet beside the files -------------------------------------------------------------

def read_provenance(folder: Path) -> dict[str, dict]:
    """file name -> its row of provenance.tsv in that folder. The China collection's own sheets name the
    column file_saved_as; both spellings are read."""
    sheet = folder / PROVENANCE
    if not sheet.is_file():
        return {}
    try:
        with open(sheet, encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f, delimiter="\t"))
    except (OSError, csv.Error):
        return {}
    out = {}
    for r in rows:
        name = str(r.get("file") or r.get("file_saved_as") or "").strip()
        if name:
            out[name] = {k: str(v or "").strip() for k, v in r.items() if k}
    return out


def note_address(folder: Path, name: str, url: str, basis: str, source_key: str) -> None:
    """Write or replace one file's line of the sheet. The sheet keeps any other column it already had."""
    rows = read_provenance(folder)
    row = rows.get(name, {})
    row.update({"file": name, "url": url, "url_basis": basis, "source": source_key,
                "fetched_on": row.get("fetched_on") or time.strftime("%Y-%m-%d")})
    rows[name] = row
    cols = PROV_COLUMNS + sorted({k for r in rows.values() for k in r} - set(PROV_COLUMNS))
    tmp = folder / (PROVENANCE + ".part")
    with open(tmp, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, delimiter="\t", extrasaction="ignore")
        w.writeheader()
        for key in sorted(rows):
            w.writerow({c: rows[key].get(c, "") for c in cols})
    tmp.replace(folder / PROVENANCE)


# ---- what the folders hold ---------------------------------------------------------------------------

def reads_as(s: Settings, path: Path, kind: str, url: str, src: dict | None) -> dict:
    """Whether the extraction stage can read the file, and how: {"status", "method", "action"}. A file with no
    address of its own is judged by its source's page, the same rule the manifest follows."""
    address = url or (src or {}).get("url", "")
    verdict = readiness.judge(path, kind, sources.host_of(address), extract.html_hosts(s))
    return {k: verdict[k] for k in ("status", "method", "action")}


def list_files(folder: Path, s: Settings | None = None, src: dict | None = None) -> list[dict]:
    """Every document under a folder, with its batch and the address noted for it; with the settings and the
    source it was filed under, also how the stage reads it."""
    out = []
    sheets: dict[Path, dict] = {}
    for p in extract.document_files(folder) if folder.is_dir() else []:
        st = p.stat()
        rel = p.relative_to(folder)
        batch = next((part for part in rel.parts[:-1] if BATCH_RX.fullmatch(part)), "")
        prov = sheets.setdefault(p.parent, read_provenance(p.parent)).get(p.name, {})
        kind = extract.DOC_SUFFIXES[p.suffix.lower()]
        row = {"name": rel.as_posix(), "kind": kind, "batch": batch,
               "size": st.st_size, "added": time.strftime("%Y-%m-%d %H:%M", time.localtime(st.st_mtime)),
               "url": prov.get("url", ""), "url_basis": prov.get("url_basis", "")}
        if s is not None and src is not None:
            row.update(reads_as(s, p, kind, row["url"], src))
        out.append(row)
    return out


def batches(folder: Path) -> list[dict]:
    """The dated subfolders of a folder that hold files, newest first."""
    out = []
    if folder.is_dir():
        for p in sorted(folder.iterdir(), reverse=True):
            if p.is_dir() and BATCH_RX.fullmatch(p.name):
                n = len(extract.document_files(p))
                if n:
                    out.append({"name": p.name, "files": n, "id": rel_or_abs(p, REPO), "path": str(p)})
    return out


def describe(s: Settings) -> dict:
    """Every economy offered, each with its designated sources and what each source's folder holds."""
    names = economies(s)
    # the six economies built so far, plus any other folder that already holds files, so nothing is hidden
    held = sorted(p.name for p in s.inbox_dir.iterdir() if p.is_dir() and p.name in names and extract.document_files(p, limit=1)) if s.inbox_dir.is_dir() else []
    order = [c for c in extract.HAND_ECONOMIES if c in names] + [c for c in held if c not in extract.HAND_ECONOMIES]
    rows = []
    for code in order:
        folder = s.inbox_dir / code
        files = extract.document_files(folder) if folder.is_dir() else []
        srcs = []
        sorted_n = 0
        for src in sources.designated(s, code):
            sf = folder / src["key"]
            sfiles = extract.document_files(sf) if sf.is_dir() else []
            sorted_n += len(sfiles)
            srcs.append({**src, "files": len(sfiles), "bytes": sum(p.stat().st_size for p in sfiles),
                         "id": rel_or_abs(sf, REPO), "path": str(sf), "batches": batches(sf),
                         "loose": sum(1 for p in sfiles if len(p.relative_to(sf).parts) == 1)})
        rows.append({"code": code, "name": names[code], "files": len(files), "bytes": sum(p.stat().st_size for p in files),
                     "id": rel_or_abs(folder, REPO), "path": str(folder), "sources": srcs,
                     "unsorted": len(files) - sorted_n,          # files of the older layout, filed under no source
                     "batches": batches(folder),
                     "loose": sum(1 for p in files if len(p.relative_to(folder).parts) == 1)})
    return {"root": rel_or_abs(s.inbox_dir, REPO), "root_path": str(s.inbox_dir), "economies": rows}


# ---- taking a file in ---------------------------------------------------------------------------------

def _write_once(folder: Path, name: str, data: bytes) -> tuple[str, str]:
    """(the name it has in the folder, what happened): the same bytes are kept once, a different file with the
    same name gets a numbered name."""
    dest = folder / name
    status = "added"
    if dest.exists():
        if hashlib.sha256(dest.read_bytes()).hexdigest() == hashlib.sha256(data).hexdigest():
            return dest.name, "already there"
        i = 2
        while (folder / f"{dest.stem} ({i}){dest.suffix}").exists():
            i += 1
        dest = folder / f"{dest.stem} ({i}){dest.suffix}"
        status = "added under a new name: a different file had that name"
    tmp = dest.with_name(dest.name + ".part")
    tmp.write_bytes(data)
    tmp.replace(dest)
    return dest.name, status


def _member_name(info: zipfile.ZipInfo) -> str:
    """A zip member's name. One not flagged as UTF-8 was most likely written on a Chinese system, where the
    names are GBK; zipfile hands those over mis-decoded as cp437."""
    raw = info.filename
    if not info.flag_bits & 0x800:
        try:
            alt = raw.encode("cp437").decode("gb18030")
            if any("一" <= ch <= "鿿" for ch in alt):
                raw = alt
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass
    return Path(raw.replace("\\", "/")).name


def unpack(folder: Path, data: bytes, source_key: str) -> dict:
    """Take the documents out of a zip archive into the folder, flat, under their own safe names. Members are
    read one by one and never extracted to a path the archive names, so nothing can be written elsewhere."""
    try:
        zf = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile:
        raise ApiError(400, "that file is not a zip archive") from None
    infos = [i for i in zf.infolist() if not i.is_dir()]
    if len(infos) > MAX_MEMBERS:
        raise ApiError(413, f"the archive holds {len(infos)} files; at most {MAX_MEMBERS} are taken at once")
    added = same = 0
    skipped: list[str] = []
    total = 0
    for info in infos:
        name = _member_name(info)
        try:
            name = safe_name(name)
        except ApiError:
            skipped.append(name)
            continue
        if info.flag_bits & 0x1 or info.file_size > MAX_BYTES:
            skipped.append(name)
            continue
        total += info.file_size
        if total > MAX_UNPACKED:
            raise ApiError(413, f"the archive unpacks to more than {MAX_UNPACKED // (1024 ** 3)} GB")
        with zf.open(info) as member:
            body = member.read(MAX_BYTES + 1)
        if not body or len(body) > MAX_BYTES:
            skipped.append(name)
            continue
        saved, status = _write_once(folder, name, body)
        if status == "already there":
            same += 1
        else:
            added += 1
        if not read_provenance(folder).get(saved):
            note_address(folder, saved, "", "", source_key)
    return {"added": added, "already_there": same, "skipped": len(skipped), "skipped_names": skipped[:10]}


def save(s: Settings, economy: str, source: str, name: str, data: bytes, batch: str = "", url: str = "") -> dict:
    code = economy_code(s, economy)
    src = source_of(s, code, source)
    name = safe_name(name, ALLOWED | ARCHIVES)
    batch = (batch or "").strip()
    if batch and not BATCH_RX.fullmatch(batch):
        raise ApiError(400, "a batch is named by its time, YYYY-MM-DD_HHMMSS")
    if not data:
        raise ApiError(400, f"{name} is empty")
    if len(data) > MAX_BYTES:
        raise ApiError(413, f"{name} is larger than {MAX_BYTES // (1024 * 1024)} MB")
    url = (url or "").strip()
    if url and not weburl.valid_url(url):
        raise ApiError(400, "the address must start with http:// or https://")
    folder = s.inbox_dir / code / src["key"] / batch if batch else s.inbox_dir / code / src["key"]
    folder.mkdir(parents=True, exist_ok=True)
    common = {"batch": batch, "source": src["key"], "folder": rel_or_abs(folder, REPO), "bytes": len(data)}
    if Path(name).suffix.lower() in ARCHIVES:
        got = unpack(folder, data, src["key"])
        status = (f"unpacked: {got['added']} added" + (f", {got['already_there']} already there" if got["already_there"] else "")
                  + (f", {got['skipped']} not taken (not PDF, HTML or Word)" if got["skipped"] else ""))
        return {**common, "saved": name, "status": status, "unpacked": got, "url": "", "url_basis": "",
                "count": len(extract.document_files(folder))}
    saved, status = _write_once(folder, name, data)
    basis = "typed on the page" if url else ""
    if not url and Path(name).suffix.lower() in (".html", ".htm"):
        url, basis = weburl.recover_url(data)
    if url or not read_provenance(folder).get(saved):
        note_address(folder, saved, url, basis, src["key"])
    kind = extract.DOC_SUFFIXES[Path(saved).suffix.lower()]
    return {**common, "saved": saved, "status": status, "url": url, "url_basis": basis,
            "reads": reads_as(s, folder / saved, kind, url, src),
            "count": len(extract.document_files(folder))}


def set_address(s: Settings, economy: str, source: str, batch: str, name: str, url: str) -> dict:
    """Record, or clear, the address one file came from."""
    code = economy_code(s, economy)
    src = source_of(s, code, source)
    batch = (batch or "").strip()
    if batch and not BATCH_RX.fullmatch(batch):
        raise ApiError(400, "a batch is named by its time, YYYY-MM-DD_HHMMSS")
    folder = s.inbox_dir / code / src["key"] / batch if batch else s.inbox_dir / code / src["key"]
    name = Path((name or "").replace("\\", "/")).name
    if not name or not (folder / name).is_file():
        raise ApiError(404, "no such file in that folder")
    url = (url or "").strip()
    if url and not weburl.valid_url(url):
        raise ApiError(400, "the address must start with http:// or https://")
    note_address(folder, name, url, "typed on the page" if url else "", src["key"])
    return {"file": name, "url": url, "batch": batch, "source": src["key"]}
