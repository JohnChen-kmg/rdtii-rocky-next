"""What belongs to this machine, not to the repository: which Python runs each stage.

A stage often has its packages in an environment of its own, somewhere a clean clone cannot know. From a
terminal that was an environment variable; started by double-click there is no terminal to set one in. The
choice is therefore kept in a small file in the state folder, `machine.json`, and set from the Appendix
page. An environment variable of the same name still wins, and a `.venv` in the repository is still found
by itself when nothing is named.

Standard library only.
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path

from . import paths as _paths, settings as settings_mod
from .proc import run_quiet
from .server import ApiError, App

STAGES = (("p1", "Scraping", "RDTII_PYTHON_P1"), ("p2", "Extraction", "RDTII_PYTHON_P2"), ("p3", "Mapping", "RDTII_PYTHON_P3"))


def register(app: App) -> None:
    @app.route("GET", r"/api/machine")
    def get(app: App, m, q, b):
        return 200, describe(app)

    @app.route("POST", r"/api/machine")
    def post(app: App, m, q, b):
        b = b or {}
        set_python(app, str(b.get("name", "")), str(b.get("value", "")))
        return 200, describe(app)


def describe(app: App) -> dict:
    s = app.settings
    kept = settings_mod.read_machine()
    rows = []
    for stage, label, name in STAGES:
        rows.append({"stage": stage, "label": label, "name": name, "python": s.python_for(stage),
                     "chosen_by": s.python_source(stage), "kept": kept.get(name, ""),
                     "from_environment": bool(os.environ.get(name, "").strip())})
    return {"file": str(settings_mod.machine_file()), "stages": rows}


def check_python(value: str) -> str:
    """The interpreter a value names, after a look that it is one: it must exist and answer as Python 3."""
    raw = _paths.expand(value.strip().strip('"'))
    found = raw if Path(raw).is_file() else (shutil.which(raw) if _paths.is_bare_command(raw) else None)
    if not found:
        raise ApiError(400, f"{raw} is not a file on this machine; give the full path of the python program")
    try:
        r = run_quiet([found, "--version"], capture_output=True, text=True, timeout=30)
    except (OSError, ValueError) as e:
        raise ApiError(400, f"{raw} could not be started: {e}") from None
    said = (r.stdout or r.stderr or "").strip()
    if r.returncode != 0 or not said.startswith("Python 3"):
        raise ApiError(400, f"{raw} does not answer as Python 3 (it said: {said[:80] or 'nothing'})")
    return raw


def set_python(app: App, name: str, value: str) -> None:
    """Keep, or with an empty value forget, the Python of one stage; it takes effect at once."""
    if name not in {n for _s, _l, n in STAGES}:
        raise ApiError(400, "name must be RDTII_PYTHON_P1, RDTII_PYTHON_P2 or RDTII_PYTHON_P3")
    if app.jobs and app.jobs.busy():
        raise ApiError(409, "a run is in progress; change the Python when it has finished")
    kept = settings_mod.read_machine()
    if value.strip():
        kept[name] = check_python(value)
    else:
        kept.pop(name, None)
    try:
        settings_mod.write_machine(kept)
    except OSError as e:
        raise ApiError(500, f"could not write {settings_mod.machine_file()}: {e}") from None
    app.settings = settings_mod.load()

