"""Child processes, in one place.

Every process the interface starts goes through here, for three reasons that are easy to get wrong one
call at a time:

- On Windows a child must be started with CREATE_NO_WINDOW, or it opens a console window of its own
  whenever the interface itself has none (started by double-click, or with pythonw). The hidden console
  is inherited by the grandchildren (tesseract, git, the browser a crawl drives), so they stay quiet too.
- Stop has to end the whole tree, not the direct child: an extraction run owns OCR workers, a crawl owns
  a browser. Windows does it with taskkill /T; POSIX needs the child in a session of its own so its
  process group can be signalled.
- A stage must run with a console Python. pythonw.exe has no stdout, so it is mapped to its twin.

Standard library only.
"""
from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
CREATE_NEW_PROCESS_GROUP = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0x00000200)


def quiet_flags(extra: int = 0, os_name: str | None = None) -> int:
    """The creation flags for a child that must not open a console window (0 off Windows)."""
    return (CREATE_NO_WINDOW | extra) if (os_name or os.name) == "nt" else 0


def run_quiet(argv, **kw) -> subprocess.CompletedProcess:
    """subprocess.run without a console window."""
    if os.name == "nt":
        kw["creationflags"] = kw.get("creationflags", 0) | CREATE_NO_WINDOW
    return subprocess.run(argv, **kw)  # noqa: S603 - argv is built by the interface, never by the page


def popen_quiet(argv, *, new_group: bool = False, **kw) -> subprocess.Popen:
    """subprocess.Popen without a console window. new_group=True makes the child the head of a tree that
    kill_tree can end as a whole: a process group on Windows, a session on POSIX."""
    if os.name == "nt":
        flags = kw.pop("creationflags", 0) | CREATE_NO_WINDOW
        if new_group:
            flags |= CREATE_NEW_PROCESS_GROUP
        kw["creationflags"] = flags
    elif new_group:
        kw.setdefault("start_new_session", True)
    return subprocess.Popen(argv, **kw)  # noqa: S603


def kill_tree(proc: subprocess.Popen, grace: float = 5.0) -> None:
    """End a child and everything it started. Returns when the child has exited or the grace has run out."""
    if proc.poll() is not None:
        return
    if os.name == "nt":
        run_quiet(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True)
        try:
            proc.wait(timeout=grace)
        except subprocess.TimeoutExpired:
            pass
        return
    # POSIX. A child started with new_group=True leads its own session, so its group id is its pid and
    # the group holds every descendant that did not leave it. Otherwise only the child can be signalled.
    try:
        pgid = os.getpgid(proc.pid)
    except OSError:
        pgid = None
    own_group = pgid is not None and pgid == proc.pid and pgid != os.getpgrp()

    def send(sig: int) -> None:
        try:
            if own_group:
                os.killpg(pgid, sig)
            else:
                proc.send_signal(sig)
        except (ProcessLookupError, PermissionError, OSError):
            pass

    send(signal.SIGTERM)
    try:
        proc.wait(timeout=grace)
    except subprocess.TimeoutExpired:
        send(signal.SIGKILL)
        try:
            proc.wait(timeout=grace)
        except subprocess.TimeoutExpired:
            pass
    if own_group:
        # the head has gone; anything in its group that ignored TERM is ended now
        deadline = time.monotonic() + 1.0
        while time.monotonic() < deadline:
            try:
                os.killpg(pgid, 0)
            except (ProcessLookupError, PermissionError, OSError):
                return
            time.sleep(0.05)
        send(signal.SIGKILL)


def pid_alive(pid: int) -> bool:
    """Whether a process with this id is running. Never signals it: on Windows os.kill(pid, 0) would end it."""
    if pid is None or pid <= 0:
        return False
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes
        k32 = ctypes.WinDLL("kernel32", use_last_error=True)
        k32.OpenProcess.restype = wintypes.HANDLE
        k32.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
        handle = k32.OpenProcess(0x1000, False, int(pid))   # PROCESS_QUERY_LIMITED_INFORMATION
        if not handle:
            return ctypes.get_last_error() == 5          # access denied: it exists, it is not ours
        try:
            code = wintypes.DWORD()
            ok = k32.GetExitCodeProcess(handle, ctypes.byref(code))
            return bool(ok) and code.value == 259        # STILL_ACTIVE
        finally:
            k32.CloseHandle(handle)
    try:
        os.kill(int(pid), 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def console_python(exe: str | None = None) -> str:
    """The interpreter to run a stage with: pythonw (no console, no stdout) is mapped to the python beside it."""
    exe = exe or sys.executable or "python"
    p = Path(exe)
    if p.stem.lower() == "pythonw":
        twin = p.with_name("python" + p.suffix)
        if twin.is_file():
            return str(twin)
    return str(exe)
