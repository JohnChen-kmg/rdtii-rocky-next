"""The inbox: documents collected by hand, one folder per economy, filled from the Scraping tab.

A file dropped on the page is written under inbox/<economy>/ with its own name, once. Nothing else is ever
written there: the manifest and law table for these files go under the runs root when Extraction runs.
"""
from __future__ import annotations

import hashlib
import re
import time

BATCH_RX = re.compile(r"\d{4}-\d{2}-\d{2}_\d{6}")   # the drop's local time, named by the page
from pathlib import Path

from .. import readers
from ..server import ApiError, App, rel_or_abs
from ..settings import REPO, Settings
from . import extract

ALLOWED = {".pdf", ".html", ".htm", ".docx", ".doc"}
MAX_BYTES = 250 * 1024 * 1024


def register(app: App) -> None:
    @app.route("GET", r"/api/inbox")
    def inbox(app: App, m, q, b):
        return 200, describe(app.settings)

    @app.route("GET", r"/api/inbox/files")
    def files(app: App, m, q, b):
        code = economy_code(app.settings, q.get("economy", ""))
        return 200, {"economy": code, "files": list_files(app.settings.inbox_dir / code)}

    @app.route("POST", r"/api/inbox/upload")
    def upload(app: App, m, q, b):
        if not isinstance(b, (bytes, bytearray)):
            raise ApiError(400, "send the file's bytes as the body, with Content-Type application/octet-stream")
        return 200, save(app.settings, q.get("economy", ""), q.get("name", ""), bytes(b), q.get("batch", ""))


def economies(s: Settings) -> dict[str, str]:
    names = readers.econ_names(s.stage_dirs["p3"])
    return names or {c: c for c in extract.DEFAULT_LANGUAGE}


def economy_code(s: Settings, raw: str) -> str:
    code = (raw or "").strip().upper()
    if code not in economies(s):
        raise ApiError(400, f"unknown economy code {code or '(none)'}; choose one on the page")
    return code


def safe_name(raw: str) -> str:
    """The file's own name, without any path, in the allowed formats."""
    name = Path((raw or "").replace("\\", "/")).name
    name = re.sub(r"[^\w.\- ()\[\]]+", "_", name).strip(" .")
    if not name or name.startswith("."):
        raise ApiError(400, "the file needs a name")
    if Path(name).suffix.lower() not in ALLOWED:
        raise ApiError(400, f"only PDF, HTML or Word files are accepted: {name}")
    return name[:160]


def list_files(folder: Path) -> list[dict]:
    out = []
    for p in extract.document_files(folder) if folder.is_dir() else []:
        st = p.stat()
        rel = p.relative_to(folder)
        out.append({"name": rel.as_posix(), "kind": extract.DOC_SUFFIXES[p.suffix.lower()],
                    "batch": rel.parts[0] if len(rel.parts) > 1 else "",
                    "size": st.st_size, "added": time.strftime("%Y-%m-%d %H:%M", time.localtime(st.st_mtime))})
    return out


def batches(folder: Path) -> list[dict]:
    """The dated subfolders of an economy's inbox folder that hold files, newest first."""
    out = []
    if folder.is_dir():
        for p in sorted(folder.iterdir(), reverse=True):
            if p.is_dir() and BATCH_RX.fullmatch(p.name):
                n = len(extract.document_files(p))
                if n:
                    out.append({"name": p.name, "files": n, "id": rel_or_abs(p, REPO), "path": str(p)})
    return out


def describe(s: Settings) -> dict:
    names = economies(s)
    # the six economies built so far, plus any other folder that already holds files, so nothing is hidden
    held = sorted(p.name for p in s.inbox_dir.iterdir() if p.is_dir() and p.name in names and extract.document_files(p, limit=1)) if s.inbox_dir.is_dir() else []
    order = [c for c in extract.HAND_ECONOMIES if c in names] + [c for c in held if c not in extract.HAND_ECONOMIES]
    rows = []
    for code in order:
        folder = s.inbox_dir / code
        files = extract.document_files(folder) if folder.is_dir() else []
        rows.append({"code": code, "name": names[code], "files": len(files), "bytes": sum(p.stat().st_size for p in files),
                     "id": rel_or_abs(folder, REPO), "path": str(folder), "batches": batches(folder),
                     "loose": sum(1 for p in files if len(p.relative_to(folder).parts) == 1)})
    return {"root": rel_or_abs(s.inbox_dir, REPO), "root_path": str(s.inbox_dir), "economies": rows}


def save(s: Settings, economy: str, name: str, data: bytes, batch: str = "") -> dict:
    code = economy_code(s, economy)
    name = safe_name(name)
    batch = (batch or "").strip()
    if batch and not BATCH_RX.fullmatch(batch):
        raise ApiError(400, "a batch is named by its time, YYYY-MM-DD_HHMMSS")
    if not data:
        raise ApiError(400, f"{name} is empty")
    if len(data) > MAX_BYTES:
        raise ApiError(413, f"{name} is larger than {MAX_BYTES // (1024 * 1024)} MB")
    folder = s.inbox_dir / code / batch if batch else s.inbox_dir / code
    folder.mkdir(parents=True, exist_ok=True)
    dest = folder / name
    status = "added"
    if dest.exists():
        if hashlib.sha256(dest.read_bytes()).hexdigest() == hashlib.sha256(data).hexdigest():
            return {"saved": dest.name, "status": "already there", "bytes": len(data), "batch": batch,
                    "folder": rel_or_abs(folder, REPO), "count": len(extract.document_files(folder))}
        i = 2
        while (folder / f"{dest.stem} ({i}){dest.suffix}").exists():
            i += 1
        dest = folder / f"{dest.stem} ({i}){dest.suffix}"
        status = "added under a new name: a different file had that name"
    tmp = dest.with_name(dest.name + ".part")
    tmp.write_bytes(data)
    tmp.replace(dest)
    return {"saved": dest.name, "status": status, "bytes": len(data), "batch": batch,
            "folder": rel_or_abs(folder, REPO), "count": len(extract.document_files(folder))}
