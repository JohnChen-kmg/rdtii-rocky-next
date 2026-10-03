"""Path safety for the Clear buttons.

Clear may delete only inside the runs root, only folders of a known shape, never a folder a running job
is writing, never a reparse point, and never anything git tracks. It is two steps: a preview that names
what would go, then a confirmation token that expires in a minute.
"""
from __future__ import annotations

import os
import re
import secrets
import shutil
import stat
import subprocess
import sys
import threading
import time
from pathlib import Path

from .server import ApiError
from .proc import run_quiet
from .settings import REPO, Settings

# kind -> the sub-folders that may be cleared on their own inside a run folder of that kind
CLEARABLE = {
    "scrape": ("raw",),
    "extract": ("ocr", "source_text", "logs"),
    "index": (),
    "map": (),
    "reviews": (),
}
TOKEN_TTL_S = 60

_tokens: dict[str, tuple[Path, float]] = {}
_lock = threading.Lock()
_tracked: set[Path] | None = None


def git_program() -> str | None:
    """git, or None when it is absent. On macOS /usr/bin/git is a stub that opens an "install the developer
    tools" dialog when the tools are missing, so it is only used once xcode-select confirms they are there."""
    exe = shutil.which("git")
    if not exe:
        return None
    if sys.platform == "darwin" and os.path.realpath(exe) == "/usr/bin/git":
        try:
            if run_quiet(["/usr/bin/xcode-select", "-p"], capture_output=True, timeout=5).returncode != 0:
                return None
        except (OSError, subprocess.TimeoutExpired):
            return None
    return exe


def tracked_files() -> set[Path]:
    """Every path git tracks, resolved, read once. Empty when git is unavailable (the runs-root rule still holds)."""
    global _tracked
    if _tracked is None:
        git = git_program()
        if git is None:
            _tracked = set()
            return _tracked
        try:
            out = run_quiet([git, "ls-files", "-z"], cwd=str(REPO), capture_output=True, timeout=20)
            names = out.stdout.decode("utf-8", "replace").split("\0") if out.returncode == 0 else []
            _tracked = {(REPO / n).resolve() for n in names if n}
        except (OSError, subprocess.TimeoutExpired):
            _tracked = set()
    return _tracked


def _is_reparse_point(p: Path) -> bool:
    try:
        st = os.lstat(p)
    except OSError:
        return False
    attrs = getattr(st, "st_file_attributes", 0)
    return bool(attrs & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)) or os.path.islink(p)


def check_clearable(s: Settings, raw_path: str, busy: list[Path]) -> Path:
    if not raw_path or not str(raw_path).strip():
        raise ApiError(400, "path is required")
    p = Path(raw_path)
    p = (p if p.is_absolute() else REPO / p)
    if not p.exists():
        raise ApiError(404, f"{p} does not exist")
    target = p.resolve()
    root = s.runs_root.resolve()
    try:
        rel = target.relative_to(root)
    except ValueError:
        raise ApiError(403, f"Clear only works inside the runs root {root}") from None
    parts = rel.parts
    if len(parts) < 2 or parts[0] not in CLEARABLE:
        raise ApiError(403, f"Clear works on one run folder or its cache, under {', '.join(sorted(CLEARABLE))}/<name>")
    # a run folder is <kind>/<name>, or for crawl results filed by source, scrape/<economy>/<source>/<run>
    depth = 4 if parts[0] == "scrape" and re.fullmatch(r"[A-Z]{2}", parts[1]) else 2
    if len(parts) < depth:
        raise ApiError(403, "Clear works on one run folder, not on a whole economy or source")
    if len(parts) == depth + 1 and parts[depth] not in CLEARABLE[parts[0]]:
        raise ApiError(403, f"inside a {parts[0]} folder only {', '.join(CLEARABLE[parts[0]]) or 'the whole folder'} may be cleared")
    if len(parts) > depth + 1:
        raise ApiError(403, "Clear works on one run folder or one of its named caches, not deeper")
    if _is_reparse_point(target) or any(_is_reparse_point(a) for a in target.parents if root in a.parents or a == root):
        raise ApiError(403, "refusing to follow a link or junction")
    for b in busy:
        rb = b.resolve()
        if rb == target or target in rb.parents or rb in target.parents:
            raise ApiError(409, "a running job is writing there; stop it first")
    tracked = tracked_files()
    if target in tracked or any(t == target or target in t.parents for t in tracked):
        raise ApiError(403, "that folder holds files the repository tracks; Clear never touches them")
    return target


def measure(target: Path) -> tuple[int, int]:
    files = 0
    size = 0
    for p in target.rglob("*"):
        try:
            if p.is_file():
                files += 1
                size += p.stat().st_size
        except OSError:
            pass
    return files, size


def issue_token(target: Path) -> str:
    tok = secrets.token_urlsafe(16)
    with _lock:
        now = time.time()
        for k, (_, exp) in list(_tokens.items()):
            if exp < now:
                del _tokens[k]
        _tokens[tok] = (target, now + TOKEN_TTL_S)
    return tok


def redeem_token(tok: str) -> Path:
    with _lock:
        hit = _tokens.pop(tok or "", None)
    if not hit:
        raise ApiError(410, "that confirmation expired or was already used; preview again")
    target, exp = hit
    if exp < time.time():
        raise ApiError(410, "that confirmation expired; preview again")
    return target


def clear(target: Path) -> None:
    if target.is_dir():
        shutil.rmtree(target)
    else:
        target.unlink()


def register(app) -> None:
    @app.route("POST", r"/api/clear/preview")
    def preview(app, m, q, b):
        target = check_clearable(app.settings, (b or {}).get("path", ""), app.jobs.busy_dirs() if app.jobs else [])
        files, size = measure(target)
        return 200, {"path": str(target), "files": files, "bytes": size, "token": issue_token(target),
                     "expires_in_s": TOKEN_TTL_S}

    @app.route("POST", r"/api/clear/confirm")
    def confirm(app, m, q, b):
        target = redeem_token((b or {}).get("token", ""))
        # re-check at the moment of deletion: a job may have started since the preview
        target = check_clearable(app.settings, str(target), app.jobs.busy_dirs() if app.jobs else [])
        files, size = measure(target)
        clear(target)
        return 200, {"removed": str(target), "files": files, "bytes": size}
