"""Routes shared by every tab: health, settings, the engine choice, the key, the document list."""
from __future__ import annotations

import time
from pathlib import Path

from . import __version__, probes, settings as settings_mod
from .server import ApiError, App
from .settings import REPO


def register(app: App) -> None:
    @app.route("GET", r"/api/health")
    def health(app: App, m, q, b):
        s = app.settings
        ollama = probes.probe_ollama()
        return 200, {
            "app": "RDTII Rocky interface", "version": __version__, "repo": str(REPO),
            "now": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "settings": settings_mod.describe(s),
            "reviewer": s.reviewer,
            "stages": probes.stage_presence(s),
            "probes": {
                "ollama": {"ok": ollama["ok"], "host": ollama["host"], "models": ollama["models"][:40],
                           "error": ollama.get("error")},
                "tesseract": probes.probe_tesseract(),
                "chromium": probes.probe_chromium(),
                "key": app.key.public(),
            },
            "engine": app.engines.public(),
            "job": app.jobs.public_summary() if app.jobs else {"active": None, "queued": []},
        }

    @app.route("GET", r"/api/engines")
    def engines(app: App, m, q, b):
        return 200, app.engines.public()

    @app.route("POST", r"/api/engine")
    def select_engine(app: App, m, q, b):
        try:
            eid = app.engines.select((b or {}).get("id", ""))
        except ValueError as e:
            raise ApiError(400, str(e)) from None
        return 200, {"selected": eid, "engine": app.engines.public()}

    @app.route("GET", r"/api/key")
    def key_status(app: App, m, q, b):
        return 200, app.key.public()

    @app.route("POST", r"/api/key")
    def key_set(app: App, m, q, b):
        try:
            app.key.set((b or {}).get("key", ""))
        except ValueError as e:
            raise ApiError(400, str(e)) from None
        return 200, app.key.public()

    @app.route("DELETE", r"/api/key")
    def key_clear(app: App, m, q, b):
        app.key.clear()
        return 200, app.key.public()

    def _explorer_windows():
        """Top-level Explorer folder windows, as (hwnd, title)."""
        import ctypes
        from ctypes import wintypes
        u = ctypes.windll.user32
        found = []
        proc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
        def cb(hwnd, _l):
            cls = ctypes.create_unicode_buffer(64)
            u.GetClassNameW(hwnd, cls, 64)
            if cls.value == "CabinetWClass":
                n = u.GetWindowTextLengthW(hwnd)
                buf = ctypes.create_unicode_buffer(n + 1)
                u.GetWindowTextW(hwnd, buf, n + 1)
                found.append((hwnd, buf.value))
            return True
        u.EnumWindows(proc(cb), 0)
        return found

    def _bring_to_front(hwnd):
        """A background process may not take the foreground; Windows lets it after a key event of its own."""
        import ctypes
        u = ctypes.windll.user32
        if u.IsIconic(hwnd):
            u.ShowWindow(hwnd, 9)  # SW_RESTORE
        u.SetForegroundWindow(hwnd)
        if u.GetForegroundWindow() != hwnd:
            u.keybd_event(0x12, 0, 0, 0)       # ALT down
            u.keybd_event(0x12, 0, 0x0002, 0)  # ALT up
            u.SetForegroundWindow(hwnd)
        if u.GetForegroundWindow() != hwnd:
            u.SwitchToThisWindow(hwnd, True)

    def _open_in_explorer(p):
        """Open the folder in Explorer and bring that window to the front; an Explorer window already showing
        the folder is reused rather than opened again."""
        import os
        import time
        before = _explorer_windows()
        same = [h for h, t in before if t == p.name or t.startswith(p.name + " - ")]  # "mini_raw - File Explorer"
        if same:
            _bring_to_front(same[-1])
            return
        os.startfile(str(p))  # noqa: S606 - opens Explorer on the machine running the server
        seen = {h for h, _ in before}
        for _ in range(30):
            time.sleep(0.1)
            new = [h for h, _t in _explorer_windows() if h not in seen]
            if new:
                _bring_to_front(new[-1])
                return

    @app.route("POST", r"/api/open")
    def open_folder(app: App, m, q, b):
        """Open a folder in the machine's file manager. Only folders the interface itself shows: the runs root,
        the fixtures, the demo data and the configured hand-off locations."""
        import os
        import sys
        from pathlib import Path
        from .proc import popen_quiet
        raw = str((b or {}).get("path", "")).strip()
        if not raw:
            raise ApiError(400, "path is required")
        p = Path(raw)
        p = (p if p.is_absolute() else REPO / p).resolve()
        if not p.is_dir():
            raise ApiError(404, f"{p} is not a folder")
        s = app.settings
        roots = [s.runs_root, REPO / "interface" / "fixtures", REPO / "demo_data", s.handoff1_dir, s.handoff2_dir,
                 s.out_dir, s.submission_dir, s.inbox_dir, REPO / "stages" / "p1-scrape" / "handoff1"]
        if not any(p == r.resolve() or r.resolve() in p.parents for r in roots if r):
            raise ApiError(403, "only folders the interface shows can be opened from here")
        try:
            if os.name == "nt":
                _open_in_explorer(p)
            elif sys.platform == "darwin":
                popen_quiet(["open", str(p)])
            else:
                popen_quiet(["xdg-open", str(p)])
        except OSError as e:
            raise ApiError(500, f"could not open the folder: {e}") from None
        return 200, {"opened": str(p)}

    @app.route("GET", r"/api/docs")
    def docs(app: App, m, q, b):
        return 200, {"docs": list_docs()}

    @app.route("GET", r"/api/doc")
    def doc(app: App, m, q, b):
        rel = q.get("path", "")
        allowed = {d["path"] for d in list_docs()}
        if rel not in allowed:
            raise ApiError(404, "not a listed document")
        text = (REPO / rel).read_text(encoding="utf-8", errors="replace")
        return 200, {"path": rel, "text": text}


DOC_GLOBS = (
    "README.md", "ASSEMBLY.md", "docs/*.md", "interface/*.md", "interface/fixtures/README.md",
    "demo_data/mini_raw/README.md", "stages/*/README.md", "stages/*/STAGE_GUIDE.md",
    "stages/p3-map/workflow/steps/*.md",
    "stages/p1-scrape/handoff1/CN/*.md", "stages/p1-scrape/handoff1/CN/*/*.md", "stages/p1-scrape/handoff1/CN/*/*/*.md",
)


def list_docs() -> list[dict]:
    out = []
    seen = set()
    for pattern in DOC_GLOBS:
        for p in sorted(REPO.glob(pattern)):
            if p.is_file() and p not in seen:
                seen.add(p)
                rel = p.relative_to(REPO).as_posix()
                out.append({"path": rel, "title": p.stem.replace("_", " "), "folder": p.parent.relative_to(REPO).as_posix() or "."})
    return out
