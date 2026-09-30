"""Health probes for the header: is Ollama answering, is Tesseract installed, is Chromium installed,
is each stage's code present. Every probe returns a small dict and never raises."""
from __future__ import annotations

import json
import os
import shutil
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


TESSERACT_CANDIDATES = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe"),
)


def probe_tesseract() -> dict:
    found = shutil.which("tesseract")
    if found:
        return {"ok": True, "path": found}
    for c in TESSERACT_CANDIDATES:
        if Path(c).is_file():
            return {"ok": True, "path": c}
    return {"ok": False, "path": None, "hint": "winget install UB-Mannheim.TesseractOCR"}


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
    return {"ok": False, "path": None, "hint": "python -m playwright install chromium"}


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
