"""Path rules that must hold on every operating system. Pure functions, standard library only; this module
imports nothing else from the interface, so settings, probes and the pages can all use it."""
from __future__ import annotations

import os
from pathlib import Path


def expand(raw: str) -> str:
    """`~` and environment variables in a path typed into a setting."""
    return os.path.expandvars(os.path.expanduser(str(raw)))


def is_bare_command(raw: str) -> bool:
    """`python3`, not a path: found on PATH by the system, never joined to a folder."""
    return bool(raw) and "/" not in raw and "\\" not in raw and not Path(raw).is_absolute()


def venv_python(venv: Path, os_name: str | None = None) -> Path | None:
    """The interpreter inside a virtual environment, or None. Never resolved: on POSIX it is a symbolic link
    to the base interpreter, and following the link would lose the environment."""
    os_name = os_name or os.name
    names = (("Scripts", "python.exe"),) if os_name == "nt" else (("bin", "python"), ("bin", "python3"))
    for parts in names:
        cand = venv.joinpath(*parts)
        if cand.is_file() or cand.is_symlink():
            return cand
    return None


def child_path(base: str, dirs, pathsep: str | None = None, case_sensitive: bool | None = None) -> str:
    """PATH for a child process: the given folders first, then the inherited PATH, with nothing listed twice.

    A program started by double-click (Finder, Explorer) inherits a short PATH that lacks Homebrew and the
    like, so the folders the tools were found in are put in front for the stages.
    """
    pathsep = pathsep or os.pathsep
    if case_sensitive is None:
        case_sensitive = os.name != "nt"
    key = (lambda x: x) if case_sensitive else (lambda x: x.lower())
    seen: set[str] = set()
    out: list[str] = []
    for item in list(dirs) + [p for p in str(base or "").split(pathsep)]:
        item = str(item).strip()
        if not item:
            continue
        k = key(item.rstrip("/\\") or item)
        if k in seen:
            continue
        seen.add(k)
        out.append(item)
    return pathsep.join(out)
