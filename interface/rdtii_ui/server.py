"""The HTTP layer: a route table, a per-process token on every POST, JSON and static helpers.

Standard library only: ThreadingHTTPServer + BaseHTTPRequestHandler. Routes are registered by the page
modules with `app.route(method, pattern)`; each handler returns (status, json-able object).
"""
from __future__ import annotations

import json
import mimetypes
import re
import secrets
import sys
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from .envbuild import EngineState, KeyHolder, load_engines
from .settings import STATIC_DIR, Settings


class ApiError(Exception):
    def __init__(self, status: int, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.message = message


class FileResponse:
    """A handler may return this instead of a JSON object to stream a file it just wrote."""

    def __init__(self, path: Path, filename: str, content_type: str, headers: dict | None = None) -> None:
        self.path = Path(path)
        self.filename = filename
        self.content_type = content_type
        self.headers = headers or {}


MAX_BODY = 260 * 1024 * 1024   # a file dropped on the page; the inbox route has its own, lower cap


class App:
    """Everything the handlers share: settings, the token, the key, the engine choice, the routes."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.token = secrets.token_urlsafe(24)
        self.key = KeyHolder()
        self.engines = EngineState(load_engines(settings.stage_dirs["p3"]))
        self.routes: list[tuple[str, re.Pattern, object]] = []
        self.jobs = None  # set by jobs.py when the run layer is wired in
        self.debug = False

    def route(self, method: str, pattern: str):
        def deco(fn):
            self.routes.append((method.upper(), re.compile(pattern), fn))
            return fn
        return deco


class Handler(BaseHTTPRequestHandler):
    app: App = None  # type: ignore[assignment]
    server_version = "rdtii-ui/0.1"
    protocol_version = "HTTP/1.1"

    # -- plumbing -----------------------------------------------------------------------------------
    def log_message(self, fmt, *args):  # noqa: D401 - quiet unless debugging
        if self.app and self.app.debug:
            sys.stderr.write("[http] " + (fmt % args) + "\n")

    def _send(self, status: int, body: bytes, ctype: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _json(self, status: int, obj) -> None:
        body = json.dumps(obj, ensure_ascii=False, default=str).encode("utf-8")
        self._send(status, body, "application/json; charset=utf-8")

    def _file(self, status: int, fr: FileResponse) -> None:
        body = fr.path.read_bytes()
        self.send_response(status)
        self.send_header("Content-Type", fr.content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Content-Disposition", f'attachment; filename="{fr.filename}"')
        self.send_header("Cache-Control", "no-store")
        for k, v in fr.headers.items():
            self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _index(self) -> None:
        page = (STATIC_DIR / "index.html").read_text(encoding="utf-8").replace("__TOKEN__", self.app.token)
        self._send(200, page.encode("utf-8"), "text/html; charset=utf-8")

    def _static(self, path: str) -> None:
        rel = path[len("/static/"):]
        target = (STATIC_DIR / rel).resolve()
        if not target.is_file() or STATIC_DIR.resolve() not in target.parents:
            return self._json(404, {"error": "no such file"})
        ctype = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        if ctype.startswith("text/") or ctype in ("application/javascript", "application/json"):
            ctype += "; charset=utf-8"
        self._send(200, target.read_bytes(), ctype)

    def do_GET(self):  # noqa: N802
        self._dispatch("GET")

    def do_HEAD(self):  # noqa: N802
        self._dispatch("GET")

    def do_POST(self):  # noqa: N802
        self._dispatch("POST")

    def do_DELETE(self):  # noqa: N802
        self._dispatch("DELETE")

    def _dispatch(self, method: str) -> None:
        parts = urlsplit(self.path)
        path = parts.path
        if method == "GET" and path == "/":
            return self._index()
        if method == "GET" and path.startswith("/static/"):
            return self._static(path)
        if method == "GET" and path == "/favicon.ico":
            return self._send(204, b"", "image/x-icon")
        query = {k: v[-1] for k, v in parse_qs(parts.query, keep_blank_values=True).items()}
        body = None
        if method in ("POST", "DELETE"):
            if self.headers.get("X-RDTII-Token") != self.app.token:
                return self._json(403, {"error": "missing or bad token; reload the page"})
            length = int(self.headers.get("Content-Length") or 0)
            if length > MAX_BODY:
                return self._json(413, {"error": f"body larger than {MAX_BODY // (1024 * 1024)} MB"})
            raw = self.rfile.read(length) if length else b""
            ctype = (self.headers.get("Content-Type") or "application/json").split(";")[0].strip().lower()
            if ctype == "application/json" or not raw.strip():
                try:
                    body = json.loads(raw.decode("utf-8")) if raw.strip() else {}
                except (ValueError, UnicodeDecodeError):
                    return self._json(400, {"error": "body must be JSON"})
            else:
                body = raw   # a file upload; the route decides what to do with the bytes
        for m, rx, fn in self.app.routes:
            if m != method:
                continue
            match = rx.fullmatch(path)
            if not match:
                continue
            try:
                status, obj = fn(self.app, match, query, body)
            except ApiError as e:
                status, obj = e.status, {"error": e.message}
            except Exception as e:  # noqa: BLE001 - report to the page, keep serving
                if self.app.debug:
                    traceback.print_exc()
                status, obj = 500, {"error": f"{type(e).__name__}: {e}"}
            if isinstance(obj, FileResponse):
                return self._file(status, obj)
            return self._json(status, obj)
        self._json(404, {"error": f"no route for {method} {path}"})


def make_server(app: App) -> ThreadingHTTPServer:
    Handler.app = app
    server = ThreadingHTTPServer((app.settings.host, app.settings.port), Handler)
    server.daemon_threads = True
    return server


def rel_or_abs(path: Path, root: Path) -> str:
    """A repo-relative POSIX path when inside the repo, the absolute path otherwise. Used as run ids."""
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError:
        return str(path.resolve())
