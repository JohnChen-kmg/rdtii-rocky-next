"""The app window: the same pages in a window of their own, with no install.

A Chromium-family browser already on the machine (Edge on Windows, Chrome on a Mac) is started in app mode,
`--app=<address>`, on a profile kept for this tool alone. That gives a window with no tabs and no address bar,
its own icon on the taskbar, and a process that lives exactly as long as the window, which is how the
interface knows when to stop. Nothing is installed and nothing is bundled; when no such browser is found the
page opens as an ordinary tab, as before.

Measured on Windows 11 with Edge and with Chrome (3 October 2026): the process started here owns the window
and exits 0.2 s after the window closes.

Standard library only.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import webbrowser
from pathlib import Path

from . import weburl
from .proc import popen_quiet, run_quiet

APP_NAME = "rdtii-rocky"
WINDOW_TITLE = "RDTII Rocky"
WINDOW_SIZE = (1500, 1000)


def _platform(platform: str | None = None) -> str:
    p = platform or sys.platform
    return "win" if p.startswith("win") else "mac" if p == "darwin" else "linux"


def state_dir(env=None, platform: str | None = None, home: Path | None = None) -> Path:
    """Where this tool keeps what belongs to the machine, not to a project: the window's browser profile, the
    instance note, the log. RDTII_STATE_DIR names it; otherwise the system's usual place for a user's data."""
    env = os.environ if env is None else env
    named = (env.get("RDTII_STATE_DIR") or "").strip()
    if named:
        return Path(os.path.expandvars(os.path.expanduser(named)))
    home = home or Path.home()
    kind = _platform(platform)
    if kind == "win":
        base = env.get("LOCALAPPDATA") or env.get("APPDATA")
        return (Path(base) if base else home / "AppData" / "Local") / APP_NAME
    if kind == "mac":
        return home / "Library" / "Application Support" / APP_NAME
    base = env.get("XDG_STATE_HOME")
    return (Path(base) if base else home / ".local" / "state") / APP_NAME


# ---- finding a browser that has app mode -------------------------------------------------------------

def _registry_app_paths(exe: str) -> list[str]:
    """Where Windows says a program is installed (App Paths), for a browser put somewhere unusual."""
    out = []
    try:
        import winreg
    except ImportError:
        return out
    for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
        try:
            with winreg.OpenKey(hive, rf"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\{exe}") as key:
                value, _ = winreg.QueryValueEx(key, None)
                if value:
                    out.append(str(value).strip('"'))
        except OSError:
            continue
    return out


def browser_candidates(platform: str | None = None, env=None, home: Path | None = None,
                       registry=_registry_app_paths) -> list[tuple[str, str]]:
    """(name, path or command) in the order they are tried: the browser every machine of that kind has first."""
    env = os.environ if env is None else env
    home = home or Path.home()
    kind = _platform(platform)
    out: list[tuple[str, str]] = []
    if kind == "win":
        pf = [env.get("ProgramFiles(x86)"), env.get("ProgramFiles"), env.get("LOCALAPPDATA")]
        rel = [("Edge", r"Microsoft\Edge\Application\msedge.exe", "msedge.exe"),
               ("Chrome", r"Google\Chrome\Application\chrome.exe", "chrome.exe"),
               ("Brave", r"BraveSoftware\Brave-Browser\Application\brave.exe", "brave.exe"),
               ("Chromium", r"Chromium\Application\chrome.exe", "")]
        for name, tail, exe in rel:
            for base in pf:
                if base:      # joined by hand, so the list reads the same whatever system builds it
                    out.append((name, base.rstrip("\\/") + "\\" + tail))
            for found in (registry(exe) if exe else []):
                out.append((name, found))
        return out
    if kind == "mac":
        apps = [("Chrome", "Google Chrome.app/Contents/MacOS/Google Chrome"),
                ("Edge", "Microsoft Edge.app/Contents/MacOS/Microsoft Edge"),
                ("Brave", "Brave Browser.app/Contents/MacOS/Brave Browser"),
                ("Chromium", "Chromium.app/Contents/MacOS/Chromium")]
        for name, tail in apps:
            out.append((name, f"/Applications/{tail}"))
            out.append((name, f"{home.as_posix()}/Applications/{tail}"))
        return out
    for name, cmd in (("Chrome", "google-chrome"), ("Chrome", "google-chrome-stable"), ("Chromium", "chromium"),
                      ("Chromium", "chromium-browser"), ("Edge", "microsoft-edge"), ("Edge", "microsoft-edge-stable"),
                      ("Brave", "brave-browser")):
        out.append((name, cmd))
    return out


def find_browser(override: str | None = None, platform: str | None = None, env=None, home: Path | None = None,
                 exists=os.path.isfile, which=shutil.which, registry=_registry_app_paths) -> dict | None:
    """{"name", "path"} of a browser with app mode, or None. `override` (RDTII_BROWSER, --browser) is a path or
    a command name; when it is given and not found, nothing else is tried, so a wrong setting is seen."""
    env = os.environ if env is None else env
    named = (override or env.get("RDTII_BROWSER") or "").strip().strip('"')
    if named:
        full = os.path.expandvars(os.path.expanduser(named))
        if exists(full):
            return {"name": Path(full).stem, "path": full}
        hit = which(named)
        return {"name": Path(hit).stem, "path": hit} if hit else None
    for name, cand in browser_candidates(platform, env, home, registry):
        if "/" in cand or "\\" in cand:      # a path; a bare word is a command, looked up on PATH
            if exists(cand):
                return {"name": name, "path": cand}
        else:
            hit = which(cand)
            if hit:
                return {"name": name, "path": hit}
    return None


def app_args(path: str, url: str, profile: Path, size: tuple[int, int] = WINDOW_SIZE) -> list[str]:
    """The command line for an app window. The profile is this tool's own, so the window never joins the
    person's everyday browser (whose process would outlive the window) and never shows its first-run pages."""
    return [path, f"--app={url}", f"--user-data-dir={profile}", "--no-first-run", "--no-default-browser-check",
            "--disable-background-mode",          # the process ends with the window
            "--disable-sync",
            # Translate: the pages show originals beside English on purpose.
            # msImplicitSignin: without it a new Edge profile signs itself in to the Windows account and puts a
            # sync dialog over the window (measured: of four variants only this one left the profile with no
            # account; --guest and --inprivate still signed in, and add a suffix to the window title).
            "--disable-features=Translate,msImplicitSignin",
            f"--window-size={size[0]},{size[1]}"]


def launch(browser: dict, url: str, profile: Path) -> subprocess.Popen:
    profile.mkdir(parents=True, exist_ok=True)
    return popen_quiet(app_args(browser["path"], url, profile), stdin=subprocess.DEVNULL,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


# ---- the rest of the desktop ---------------------------------------------------------------------------

def open_external(url: str) -> bool:
    """Open a web address in the person's own browser. Only http and https: the page must not be able to
    start anything else on the machine."""
    if not weburl.valid_url(url):
        return False
    try:
        return bool(webbrowser.open(url))
    except (webbrowser.Error, OSError):
        return False


def focus_window(title: str = WINDOW_TITLE) -> bool:
    """Bring a window of this tool that is already open to the front (Windows only). True when one was found."""
    if os.name != "nt":
        return False
    import ctypes
    from ctypes import wintypes
    u = ctypes.windll.user32
    found: list[int] = []
    proc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)

    def cb(hwnd, _l):
        if u.IsWindowVisible(hwnd):
            cls = ctypes.create_unicode_buffer(64)
            u.GetClassNameW(hwnd, cls, 64)
            if cls.value.startswith("Chrome_WidgetWin"):
                n = u.GetWindowTextLengthW(hwnd)
                buf = ctypes.create_unicode_buffer(n + 1)
                u.GetWindowTextW(hwnd, buf, n + 1)
                if buf.value == title:           # an app window's title is the page's, with nothing added
                    found.append(hwnd)
        return True
    u.EnumWindows(proc(cb), 0)
    if not found:
        return False
    hwnd = found[0]
    if u.IsIconic(hwnd):
        u.ShowWindow(hwnd, 9)                # SW_RESTORE
    u.SetForegroundWindow(hwnd)
    if u.GetForegroundWindow() != hwnd:      # a background process may take the foreground after a key event of its own
        u.keybd_event(0x12, 0, 0, 0)
        u.keybd_event(0x12, 0, 0x0002, 0)
        u.SetForegroundWindow(hwnd)
    return True


def message_box(title: str, text: str) -> None:
    """Say something when there is no console to print to (started by double-click)."""
    try:
        if os.name == "nt":
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, text, title, 0x10)      # MB_ICONERROR
            return
        if sys.platform == "darwin":
            script = 'display dialog "{}" with title "{}" buttons {{"OK"}} with icon stop'.format(
                text.replace("\\", "\\\\").replace('"', '\\"'), title.replace('"', '\\"'))
            run_quiet(["osascript", "-e", script], capture_output=True, timeout=120)
            return
    except Exception:  # noqa: BLE001 - a dialog that cannot be shown must not hide the error it was for
        pass
    sys.stderr.write(f"{title}: {text}\n")
