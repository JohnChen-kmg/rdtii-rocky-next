"""The HTTP layer: a route table, a per-process token on every POST, JSON and static helpers.

Standard library only: ThreadingHTTPServer + BaseHTTPRequestHandler. Routes are registered by the page
modules with `app.route(method, pattern)`; each handler returns (status, json-able object).
"""
from __future__ import annotations

import json
import re
import secrets
import socket
import sys
import threading
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


class StreamResponse:
    """A handler may return this to keep the connection open and send chunks as they come (server-sent
    events). `chunks` yields bytes; it is closed when the page goes away, so a generator's `finally` runs."""

    def __init__(self, chunks, content_type: str = "text/event-stream; charset=utf-8") -> None:
        self.chunks = chunks
        self.content_type = content_type


MAX_BODY = 260 * 1024 * 1024   # a file dropped on the page; the inbox route has its own, lower cap

# The media type of each static file, by suffix. Not asked of the system: on Windows that answer comes from the
# registry, where another program may have set .js to text/plain, and the page then refuses its own script.
MEDIA_TYPES = {
    ".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8", ".js": "text/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8", ".webmanifest": "application/manifest+json; charset=utf-8",
    ".svg": "image/svg+xml", ".png": "image/png", ".ico": "image/x-icon", ".jpg": "image/jpeg",
    ".txt": "text/plain; charset=utf-8", ".woff2": "font/woff2",
}


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
        self.shell = "tab"               # "window" when the page runs in the tool's own app window
        self.port = settings.port        # the port really bound, set by make_server
        self.presence = None             # set by lifecycle.py: how many pages are open
        self.stop = threading.Event()    # set to end a server that was started with a window

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

    def _stream(self, status: int, sr: StreamResponse) -> None:
        """Send chunks until the source ends or the page goes away. One thread per open stream."""
        self.close_connection = True
        try:
            self.send_response(status)
            self.send_header("Content-Type", sr.content_type)
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Accel-Buffering", "no")
            self.send_header("Connection", "close")
            self.end_headers()
            for chunk in sr.chunks:
                self.wfile.write(chunk)
                self.wfile.flush()
        except OSError:
            pass                       # the page closed, reloaded, or the machine slept: not an error
        finally:
            close = getattr(sr.chunks, "close", None)
            if close:
                close()

    def _index(self) -> None:
        page = ((STATIC_DIR / "index.html").read_text(encoding="utf-8")
                .replace("__TOKEN__", self.app.token).replace("__SHELL__", self.app.shell))
        self._send(200, page.encode("utf-8"), "text/html; charset=utf-8")

    def _static(self, path: str) -> None:
        rel = path[len("/static/"):]
        target = (STATIC_DIR / rel).resolve()
        if not target.is_file() or STATIC_DIR.resolve() not in target.parents:
            return self._json(404, {"error": "no such file"})
        self._send(200, target.read_bytes(), MEDIA_TYPES.get(target.suffix.lower(), "application/octet-stream"))

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
            icon = STATIC_DIR / "favicon.ico"
            return self._send(200, icon.read_bytes(), "image/x-icon") if icon.is_file() else self._send(204, b"", "image/x-icon")
        query = {k: v[-1] for k, v in parse_qs(parts.query, keep_blank_values=True).items()}
        body = None
        if method in ("POST", "DELETE"):
            if self.headers.get("X-RDTII-Token") != self.app.token:
                self.close_connection = True      # the body is left unread: the connection must not be reused
                return self._json(403, {"error": "missing or bad token; reload the page"})
            length = int(self.headers.get("Content-Length") or 0)
            if length > MAX_BODY:
                self.close_connection = True
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
            if isinstance(obj, StreamResponse):
                return self._stream(status, obj)
            return self._json(status, obj)
        self._json(404, {"error": f"no route for {method} {path}"})


class Server(ThreadingHTTPServer):
    """One server per port. The stock class asks for SO_REUSEADDR, which on Windows lets a second process bind
    a port that is already served: two interfaces then answer the same address in turn, each refusing the
    other's token. Windows gets SO_EXCLUSIVEADDRUSE instead; elsewhere SO_REUSEADDR is kept, where it only
    means a port just released can be taken again at once."""
    daemon_threads = True
    allow_reuse_address = sys.platform != "win32"

    def server_bind(self) -> None:
        if sys.platform == "win32":
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()

    def handle_error(self, request, client_address) -> None:
        # a page that closes or reloads mid-request is routine for a browser, not an error to print
        if isinstance(sys.exc_info()[1], ConnectionError) and not (Handler.app and Handler.app.debug):
            return
        super().handle_error(request, client_address)


def make_server(app: App, port: int | None = None) -> ThreadingHTTPServer:
    """Bind the server. port=0 asks the system for a free one; the port really bound is left in app.port."""
    Handler.app = app
    server = Server((app.settings.host, app.settings.port if port is None else port), Handler)
    app.port = server.server_address[1]
    return server


def rel_or_abs(path: Path, root: Path) -> str:
    """A repo-relative POSIX path when inside the repo, the absolute path otherwise. Used as run ids."""
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError:
        return str(path.resolve())
