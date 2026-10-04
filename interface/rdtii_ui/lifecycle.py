"""When the interface runs and when it stops, once it has a window of its own.

Started as a tab, the server runs until Ctrl+C, as it always has. Started with a window, it has to stop by
itself when the window is closed, or a hidden server and its stage would stay behind. Three signals say
whether anyone is there:

- the browser process started for the window (it ends 0.2 s after the window closes, measured);
- presence: each open page holds one stream to /api/presence, so the server can count the pages;
- whether a run is in progress.

`decide` turns them into "run" or "stop". It counts loop ticks, not seconds, so a laptop waking from sleep
does not look like a window that has been closed for an hour.

One instance per repository: a note in the state folder says which process serves it and on which port, so
a second double-click brings the first window forward instead of starting a second server.

Standard library only.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

from . import shell
from .proc import pid_alive
from .server import ApiError, App, StreamResponse
from .settings import REPO

TICK = 0.5              # seconds between two looks
GRACE_TICKS = 10        # 5 s with no page before stopping: a reload reconnects well inside it
STARTUP_TICKS = 90      # 45 s for the window to load its first page
ORPHAN_TICKS = 240      # 2 min: a browser process still there with no page and no run is a leftover
MAC_BUSY_TICKS = 60     # 30 s: on a Mac, how long a run survives its page (see decide)


class Presence:
    """How many pages are open, counted by their streams."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.count = 0
        self.ever = False

    def enter(self) -> None:
        with self._lock:
            self.count += 1
            self.ever = True

    def leave(self) -> None:
        with self._lock:
            self.count = max(0, self.count - 1)


def decide(*, window_alive: bool, present: int, ever_present: bool, busy: bool, quiet_ticks: int, age_ticks: int,
           mac: bool = False) -> str:
    """"run" or "stop", for a server that was started with a window.

    quiet_ticks: consecutive ticks with no page connected. age_ticks: ticks since the window was started.
    mac: on macOS an application stays running when its last window is closed, so the browser process says
    nothing; there the page's own stream is the signal, with a longer grace while a run is in progress (a page
    that reloads or crashes must not take the run with it at once).
    """
    if present > 0:
        return "run"
    if window_alive and mac and ever_present:
        return "stop" if quiet_ticks >= (MAC_BUSY_TICKS if busy else GRACE_TICKS) else "run"
    if window_alive:
        if busy or not ever_present:
            return "run"                      # a run is never cut short while its window exists; a first page may be slow
        return "stop" if quiet_ticks >= ORPHAN_TICKS else "run"
    # no browser process and no page: the window was closed, or it never came up
    if ever_present:
        return "stop" if quiet_ticks >= GRACE_TICKS else "run"
    return "stop" if age_ticks >= STARTUP_TICKS else "run"


def watch(app: App, proc, tick: float = TICK, sleep=time.sleep, mac: bool | None = None) -> str:
    """Block until the server should stop; returns why."""
    quiet = age = 0
    mac = (sys.platform == "darwin") if mac is None else mac
    while True:
        sleep(tick)
        age += 1
        if app.stop.is_set():
            return "asked to stop"
        present = app.presence.count
        quiet = 0 if present else quiet + 1
        alive = proc is not None and proc.poll() is None
        busy = bool(app.jobs and app.jobs.busy())
        if decide(window_alive=alive, present=present, ever_present=app.presence.ever, busy=busy,
                  quiet_ticks=quiet, age_ticks=age, mac=mac) == "stop":
            return "the window was closed" if app.presence.ever else "the window did not open"


# ---- one instance per repository ---------------------------------------------------------------------

def ping(host: str, port: int, timeout: float = 1.5) -> dict | None:
    """What answers on that address, if it is this tool. Never goes through a proxy."""
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(f"http://{host}:{port}/api/ping", timeout=timeout) as r:
            got = json.loads(r.read().decode("utf-8"))
    except (OSError, ValueError, urllib.error.URLError):
        return None
    return got if isinstance(got, dict) and got.get("app") == shell.APP_NAME else None


class InstanceNote:
    """The note that says which process serves this repository. It never holds the token."""

    def __init__(self, state_dir: Path, repo: Path = REPO) -> None:
        tag = hashlib.sha1(str(repo.resolve()).lower().encode("utf-8")).hexdigest()[:10]
        self.path = state_dir / f"instance-{tag}.json"
        self.repo = str(repo.resolve())

    def read(self) -> dict | None:
        try:
            got = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        return got if isinstance(got, dict) else None

    def running(self, probe=ping, alive=pid_alive) -> dict | None:
        """The note, when the process it names is alive and answers as this tool for this repository."""
        note = self.read()
        if not note or not alive(int(note.get("pid") or 0)):
            return None
        got = probe(str(note.get("host") or "127.0.0.1"), int(note.get("port") or 0))
        if not got or os.path.normcase(str(got.get("repo") or "")) != os.path.normcase(self.repo):
            return None
        return note

    def write(self, host: str, port: int) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_name(self.path.name + ".part")
        tmp.write_text(json.dumps({"pid": os.getpid(), "host": host, "port": port, "repo": self.repo,
                                   "started": time.strftime("%Y-%m-%dT%H:%M:%S")}), encoding="utf-8")
        tmp.replace(self.path)

    def release(self) -> None:
        note = self.read()
        if note and int(note.get("pid") or 0) == os.getpid():
            try:
                self.path.unlink()
            except OSError:
                pass


# ---- routes -----------------------------------------------------------------------------------------------

def register(app: App) -> None:
    app.presence = Presence()

    @app.route("GET", r"/api/ping")
    def ping_route(app: App, m, q, b):
        return 200, {"app": shell.APP_NAME, "repo": str(REPO.resolve()), "pid": os.getpid(), "shell": app.shell}

    @app.route("GET", r"/api/presence")
    def presence(app: App, m, q, b):
        """One stream per open page. It carries whether a run is in progress, so the page can warn before its
        window is closed; its end is how the server learns the page has gone."""
        if q.get("t") != app.token:
            raise ApiError(403, "missing or bad token; reload the page")

        def events():
            app.presence.enter()
            try:
                yield b"retry: 1000\n\n"
                while not app.stop.is_set():
                    busy = bool(app.jobs and app.jobs.busy())
                    yield ("data: " + json.dumps({"busy": busy, "shell": app.shell}) + "\n\n").encode("utf-8")
                    time.sleep(1.0)
            finally:
                app.presence.leave()
        return 200, StreamResponse(events())

    @app.route("POST", r"/api/shutdown")
    def shutdown(app: App, m, q, b):
        app.stop.set()
        return 200, {"stopping": True}

    @app.route("POST", r"/api/open-url")
    def open_url(app: App, m, q, b):
        """A link to a source, opened in the person's own browser instead of inside the app window."""
        url = str((b or {}).get("url", "")).strip()
        if not shell.open_external(url):
            raise ApiError(400, "only http and https addresses can be opened")
        return 200, {"opened": url}
