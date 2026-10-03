"""Health probes for the header: is Ollama answering, is Tesseract installed, is Chromium installed,
is each stage's code present. Every probe returns a small dict and never raises."""
from __future__ import annotations

import json
import os
import shutil
import sys
import threading
import time
import urllib.request
from pathlib import Path

from .settings import Settings

_ollama_lock = threading.Lock()
_ollama_cache: dict = {"at": 0.0, "host": None, "result": None}


def probe_ollama(host: str | None = None, ttl: float = 30.0) -> dict:
    host = (host or os.environ.get("OLLAMA_HOST") or "http://127.0.0.1:11434").rstrip("/")
    if not host.startswith("http"):
        host = "http://" + host
    with _ollama_lock:
        fresh = (_ollama_cache["host"] == host and time.monotonic() - _ollama_cache["at"] < ttl
                 and _ollama_cache["result"])
        if fresh:
            return _ollama_cache["result"]
    url = f"{host}/api/tags"
    try:
        with urllib.request.urlopen(url, timeout=1.5) as resp:
            data = json.loads(resp.read().decode("utf-8", "replace"))
        models = [m.get("name") for m in data.get("models", []) if m.get("name")]
        digests = {m.get("name"): m.get("digest") for m in data.get("models", []) if m.get("name")}
        result = {"ok": True, "host": host, "models": models, "digests": digests, "how": f"GET {url}"}
    except Exception as exc:  # noqa: BLE001 - a probe reports, it does not fail
        result = {"ok": False, "host": host, "models": [], "digests": {}, "error": str(exc), "how": f"GET {url}"}
    with _ollama_lock:
        _ollama_cache.update(at=time.monotonic(), host=host, result=result)
    return result


def tesseract_candidates(platform: str | None = None, env=None) -> list[str]:
    """Where Tesseract usually is when it is not on PATH, per operating system."""
    platform = platform or sys.platform
    env = os.environ if env is None else env
    if platform.startswith("win"):
        out = [r"C:\Program Files\Tesseract-OCR\tesseract.exe",
               r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"]
        if env.get("LOCALAPPDATA"):
            out.append(env["LOCALAPPDATA"] + r"\Programs\Tesseract-OCR\tesseract.exe")
        return out
    if platform == "darwin":                                    # Homebrew (Apple silicon, Intel), MacPorts
        return ["/opt/homebrew/bin/tesseract", "/usr/local/bin/tesseract", "/opt/local/bin/tesseract"]
    return ["/usr/bin/tesseract", "/usr/local/bin/tesseract",
            "/home/linuxbrew/.linuxbrew/bin/tesseract", "/snap/bin/tesseract"]


TESSERACT_CANDIDATES = tuple(tesseract_candidates())


def install_hint(tool: str, platform: str | None = None) -> str:
    """The one-line way to install a missing tool on this operating system."""
    platform = platform or sys.platform
    if tool == "tesseract":
        if platform.startswith("win"):
            return "winget install UB-Mannheim.TesseractOCR"
        if platform == "darwin":
            return "brew install tesseract"
        return "sudo apt install tesseract-ocr"
    if tool == "chromium":
        return "python -m playwright install chromium"
    return ""


def probe_tesseract(override: str | None = None) -> dict:
    """Tesseract: the RDTII_TESSERACT setting, then PATH, then the usual places for this system."""
    override = os.environ.get("RDTII_TESSERACT", "") if override is None else override
    if override:
        p = Path(os.path.expandvars(os.path.expanduser(override)))
        if p.is_file():
            return {"ok": True, "path": str(p)}
    found = shutil.which("tesseract")
    if found:
        return {"ok": True, "path": found}
    for c in tesseract_candidates():
        if Path(c).is_file():
            return {"ok": True, "path": c}
    return {"ok": False, "path": None, "hint": install_hint("tesseract")}


def tool_path_dirs(platform: str | None = None) -> list[str]:
    """Folders a stage needs on its PATH: where Tesseract was found, and on macOS and Linux the package
    managers' folders, which a program started from Finder or a desktop launcher does not inherit."""
    platform = platform or sys.platform
    dirs: list[str] = []
    t = probe_tesseract()
    if t.get("ok") and t.get("path"):
        dirs.append(str(Path(t["path"]).parent))
    extra = []
    if platform == "darwin":
        extra = ["/opt/homebrew/bin", "/usr/local/bin", "/opt/local/bin"]
    elif not platform.startswith("win"):
        extra = ["/usr/local/bin", "/home/linuxbrew/.linuxbrew/bin"]
    dirs += [d for d in extra if Path(d).is_dir() and d not in dirs]
    return dirs


def probe_chromium() -> dict:
    roots = []
    if os.environ.get("PLAYWRIGHT_BROWSERS_PATH"):
        roots.append(Path(os.environ["PLAYWRIGHT_BROWSERS_PATH"]))
    if os.environ.get("LOCALAPPDATA"):
        roots.append(Path(os.environ["LOCALAPPDATA"]) / "ms-playwright")
    roots.append(Path.home() / ".cache" / "ms-playwright")            # Linux
    roots.append(Path.home() / "Library" / "Caches" / "ms-playwright")  # macOS
    for root in roots:
        if root.is_dir():
            hits = sorted(p.name for p in root.glob("chromium-*") if p.is_dir())
            if hits:
                return {"ok": True, "path": str(root / hits[-1])}
    return {"ok": False, "path": None, "hint": install_hint("chromium")}


STAGE_ENTRY = {
    "p1": ("scrape.py",),
    "p2": ("src", "rdtii_p2", "cli.py"),
    "p3": ("src", "p3map", "cli.py"),
}


def stage_presence(s: Settings) -> dict:
    out = {}
    for stage, d in s.stage_dirs.items():
        entry = d.joinpath(*STAGE_ENTRY[stage])
        out[stage] = {"dir": str(d), "present": entry.is_file(), "entry": str(entry)}
    return out
