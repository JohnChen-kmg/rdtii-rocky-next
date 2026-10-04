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


def _browser_roots() -> list[Path]:
    roots = []
    if os.environ.get("PLAYWRIGHT_BROWSERS_PATH"):
        roots.append(Path(os.environ["PLAYWRIGHT_BROWSERS_PATH"]))
    if os.environ.get("LOCALAPPDATA"):
        roots.append(Path(os.environ["LOCALAPPDATA"]) / "ms-playwright")
    roots.append(Path.home() / ".cache" / "ms-playwright")            # Linux
    roots.append(Path.home() / "Library" / "Caches" / "ms-playwright")  # macOS
    return roots


def _browser_builds() -> tuple:
    """The browser builds on disk, as names: what a launch test's answer depends on."""
    return tuple(sorted(str(d) for root in _browser_roots() if root.is_dir() for d in root.iterdir()
                        if d.is_dir() and d.name.startswith("chromium")))


# Run by the crawler's own Python: start its browser and stop it again.
_LAUNCH_CODE = (
    "import sys\n"
    "from importlib import metadata\n"
    "try:\n"
    "    from playwright.sync_api import sync_playwright\n"
    "except Exception as e:\n"
    "    print('BROWSER no-package ' + type(e).__name__); sys.exit(0)\n"
    "v = metadata.version('playwright')\n"
    "try:\n"
    "    pw = sync_playwright().start()\n"
    "    b = pw.chromium.launch(headless=True)\n"
    "    print('BROWSER ok ' + v + ' ' + b.version)\n"
    "    b.close(); pw.stop()\n"
    "except Exception as e:\n"
    "    print('BROWSER fail ' + v + ' ' + str(e).splitlines()[0][:300])\n")
_launch_lock = threading.Lock()
_launch_cache: dict = {}


def read_launch(output: str, python: str) -> dict:
    """What the launch test printed, as {"ok", "text", "hint"}."""
    line = next((ln for ln in (output or "").splitlines() if ln.startswith("BROWSER ")), "")
    parts = line.split(" ", 3)
    how = f'"{python}" -m playwright install chromium'
    if len(parts) >= 2 and parts[1] == "ok":
        return {"ok": True, "text": f"The crawler's browser starts (Playwright {parts[2]}, Chromium {parts[3] if len(parts) > 3 else ''}).".replace(" )", ")"),
                "hint": ""}
    if len(parts) >= 2 and parts[1] == "no-package":
        return {"ok": False, "text": "The crawler's Python has no Playwright package, so no page can be fetched through a browser.",
                "hint": f'"{python}" -m pip install playwright, then {how}'}
    if len(parts) >= 3 and parts[1] == "fail":
        why = parts[3] if len(parts) > 3 else ""
        if "Executable doesn't exist" in why:
            why = f"Playwright {parts[2]} needs a Chromium build that is not installed (the package was updated after the browser was)"
        return {"ok": False, "text": f"The crawler's browser cannot start: {why}.".replace("..", "."), "hint": how}
    return {"ok": False, "text": "The crawler's browser could not be tested.", "hint": how}


def probe_browser_launch(python: str, run=None) -> dict:
    """Whether the crawler's own Python can start its browser: the only test that tells. A Chromium folder on
    disk says nothing once the Playwright package has moved on to another build; every page fetched through
    the browser then fails as "HTTP 0". The answer is kept until the builds on disk change."""
    from .proc import run_quiet
    key = (python, _browser_builds())
    with _launch_lock:
        if _launch_cache.get("key") == key:
            return _launch_cache["value"]
    try:
        r = (run or run_quiet)([python, "-c", _LAUNCH_CODE], capture_output=True, text=True, encoding="utf-8",
                                errors="replace", timeout=90, env={**os.environ, "PYTHONUTF8": "1"})
        out = read_launch(r.stdout or "", python)
    except Exception as e:  # noqa: BLE001 - a probe never raises
        out = {"ok": False, "text": f"The crawler's browser could not be tested ({type(e).__name__}).", "hint": ""}
    with _launch_lock:
        _launch_cache.update(key=key, value=out)
    return out


_imports_cache: dict = {}


def probe_imports(python: str, cwd: Path, modules: str, pythonpath: str = "", run=None) -> dict:
    """Whether an interpreter can import what a stage needs, said before Start instead of by the run's first
    step. {"ok", "missing"}; kept per interpreter until that program's file changes."""
    from .proc import run_quiet
    try:
        stamp = Path(python).stat().st_mtime_ns
    except OSError:
        stamp = 0
    key = (python, stamp, str(cwd), modules)
    if key in _imports_cache:
        return _imports_cache[key]
    env = {**os.environ, "PYTHONUTF8": "1"}
    if pythonpath:
        env["PYTHONPATH"] = pythonpath
    try:
        r = (run or run_quiet)([python, "-c", f"import {modules}; print('imports ok')"], cwd=str(cwd), env=env,
                                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
        text = (r.stdout or "") + (r.stderr or "")
        if "imports ok" in text:
            out = {"ok": True, "missing": ""}
        else:
            import re
            m = re.search(r"No module named '([^']+)'", text)
            out = {"ok": False, "missing": m.group(1) if m else (text.strip().splitlines() or ["it could not be started"])[-1][:160]}
    except Exception as e:  # noqa: BLE001 - a probe never raises
        out = {"ok": False, "missing": f"it could not be started ({type(e).__name__})"}
    _imports_cache[key] = out
    return out


def warm_browser_probe(python: str) -> None:
    """Test the launch in the background at start, so the header's dot is true before the first Check."""
    threading.Thread(target=probe_browser_launch, args=(python,), name="browser-probe", daemon=True).start()


def probe_chromium(python: str | None = None) -> dict:
    """The header's Chromium dot. A build folder on disk is the least; when the launch test for this Python has
    run, its answer is the one shown."""
    hits = _browser_builds()
    if not hits:
        return {"ok": False, "path": None, "hint": install_hint("chromium")}
    with _launch_lock:
        tested = _launch_cache.get("value") if python and _launch_cache.get("key") == (python, hits) else None
    if tested is not None:
        return {"ok": tested["ok"], "path": hits[-1], "hint": tested["hint"], "text": tested["text"], "tested": True}
    return {"ok": True, "path": hits[-1], "tested": False}


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
