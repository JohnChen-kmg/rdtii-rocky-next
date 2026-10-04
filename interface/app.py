"""RDTII Rocky interface. Start it with:

    python interface/app.py             the address is printed; open it in a browser
    python interface/app.py --window    the pages open in a window of their own; closing it stops the tool

or double-click the launcher at the top of the repository. Standard library only; nothing to install. Every
location it reads is a setting (see interface/DATA_PATHS.md); the defaults work on a clean clone and show
the fixture rows.
"""
from __future__ import annotations

import argparse
import os
import sys
import threading
import traceback
import webbrowser
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from rdtii_ui import core, fsguard, jobs, lifecycle, probes, review, settings as settings_mod, shell  # noqa: E402
from rdtii_ui.pages import china, extract, inbox, mapping, scrape  # noqa: E402
from rdtii_ui.server import App, make_server  # noqa: E402


def build_app(env=None) -> App:
    s = settings_mod.load(env)
    settings_mod.check_runs_root(s)
    extract.ensure_inbox(s)
    app = App(s)
    core.register(app)
    jobs.register(app)
    fsguard.register(app)
    scrape.register(app)
    china.register(app)
    extract.register(app)
    inbox.register(app)
    mapping.register(app)
    review.register(app)
    lifecycle.register(app)
    return app


def settings_report(s) -> list[str]:
    """Every setting in effect, one line each, for --print-settings."""
    lines = [f"repository = {settings_mod.REPO}"]
    for row in settings_mod.describe(s):
        state = "" if row["exists"] or not row["value"] else "  (missing)"
        lines.append(f"{row['name']} = {row['value'] or '(none)'}  [{row['source']}]{state}")
    for stage in ("p1", "p2", "p3"):
        lines.append(f"python for {stage} = {s.python_for(stage)}  [{s.python_source(stage)}]")
    t = probes.probe_tesseract(s.tesseract or None)
    lines.append(f"tesseract = {t.get('path') or 'not found: ' + t.get('hint', '')}")
    lines.append(f"reviewer = {s.reviewer}")
    b = shell.find_browser()
    lines.append(f"window browser = {b['path'] if b else 'none found: --window opens an ordinary tab'}")
    lines.append(f"state folder = {shell.state_dir()}")
    return lines


def banner(app: App, url: str) -> None:
    s = app.settings
    present = probes.stage_presence(s)
    print(f"RDTII Rocky interface  {url}", flush=True)
    print(f"  repository : {settings_mod.REPO}")
    print(f"  showing    : OUT_DIR={s.out_dir}")
    print(f"  runs root  : {s.runs_root}")
    print(f"  inbox      : {s.inbox_dir}  (hand-collected files, one folder per economy and source)")
    print("  stages     : " + ", ".join(f"{k} {'present' if v['present'] else 'MISSING'}" for k, v in present.items()))
    print(f"  engines    : {', '.join(app.engines.ids()) or 'none declared'} (selected {app.engines.selected})", flush=True)


def serve_until_interrupt(app: App, server) -> int:
    """The tab way: serve until Ctrl+C."""
    print("  Ctrl+C stops the server.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped.")
    finally:
        app.jobs.shutdown()        # a stage must not outlive the interface that would read and stop it
        server.server_close()
    return 0


def run_tab(args) -> int:
    app = build_app()
    app.debug = args.debug
    try:
        server = make_server(app)
    except OSError as e:
        s = app.settings
        print(f"Cannot serve on {s.host}:{s.port}: {e}\n"
              f"Another program has that port, or this interface is already running at http://{s.host}:{s.port}/ .\n"
              "Stop it, or start with --port 0 to take a free port.", file=sys.stderr)
        return 2
    url = f"http://{app.settings.host}:{app.port}/"
    banner(app, url)
    probes.warm_browser_probe(app.settings.python_for("p1"))
    if args.open:
        webbrowser.open(url)
    return serve_until_interrupt(app, server)


def log_when_no_console(state: Path) -> Path | None:
    """Started by double-click there is no console, and pythonw has no stdout at all: what would be printed
    goes to a log in the state folder."""
    if sys.stdout is not None and sys.stderr is not None:
        return None
    state.mkdir(parents=True, exist_ok=True)
    path = state / "interface.log"
    log = open(path, "a", encoding="utf-8", buffering=1)  # noqa: SIM115 - kept open for the life of the process
    sys.stdout = sys.stdout or log
    sys.stderr = sys.stderr or log
    return path


def run_window(args) -> int:
    state = shell.state_dir()
    log = log_when_no_console(state)
    try:
        return _run_window(args, state)
    except SystemExit as e:
        if e.code not in (None, 0) and log:
            shell.message_box("RDTII Rocky could not start", str(e.code))
        raise
    except Exception as e:  # noqa: BLE001 - with no console, a start that fails must still be seen
        traceback.print_exc()
        if log:
            shell.message_box("RDTII Rocky could not start", f"{type(e).__name__}: {e}\n\nDetails: {log}")
        return 1


def _run_window(args, state: Path) -> int:
    note = lifecycle.InstanceNote(state)
    browser = shell.find_browser(args.browser)
    profile = state / "browser-profile"
    other = note.running()
    if other:      # already serving this repository: show that window, start nothing
        url = f"http://{other['host']}:{other['port']}/"
        if not shell.focus_window():
            if browser:
                shell.launch(browser, url, profile)
            else:
                webbrowser.open(url)
        print(f"RDTII Rocky is already running: {url}")
        return 0

    app = build_app()
    app.debug = args.debug
    try:
        server = make_server(app)
    except OSError:
        server = make_server(app, 0)     # a window needs no fixed address: take a free port
    url = f"http://{app.settings.host}:{app.port}/"
    banner(app, url)
    probes.warm_browser_probe(app.settings.python_for("p1"))
    if not browser:
        named = args.browser or os.environ.get("RDTII_BROWSER")
        print("  window     : " + (f"{named} was not found" if named else "no Edge, Chrome, Brave or Chromium found")
              + "; opening an ordinary tab instead.", flush=True)
        webbrowser.open(url)
        return serve_until_interrupt(app, server)

    app.shell = "window"
    note.write(app.settings.host, app.port)
    print(f"  window     : {browser['name']} in app mode; closing the window stops the interface.", flush=True)
    threading.Thread(target=server.serve_forever, name="http", daemon=True).start()
    try:
        proc = shell.launch(browser, url, profile)
        why = lifecycle.watch(app, proc)
        print(f"stopping: {why}.", flush=True)
    except KeyboardInterrupt:
        print("\nstopped.")
    finally:
        app.stop.set()             # ends the pages' streams
        app.jobs.shutdown()        # a stage must not outlive the interface that would read and stop it
        server.shutdown()
        server.server_close()
        note.release()
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="app.py", description="RDTII Rocky interface (standard library only)")
    ap.add_argument("--host", help="bind address (default RDTII_HOST or 127.0.0.1)")
    ap.add_argument("--port", type=int, help="port (default RDTII_PORT or 8765); 0 takes a free one")
    ap.add_argument("--open", action="store_true", help="open the page in the default browser")
    ap.add_argument("--window", action="store_true",
                    help="open the pages in a window of their own (Edge or Chrome in app mode); closing it stops the interface")
    ap.add_argument("--browser", help="the browser for --window: a path or a command (default RDTII_BROWSER, then Edge, Chrome, Brave, Chromium)")
    ap.add_argument("--debug", action="store_true", help="log every request and traceback")
    ap.add_argument("--print-settings", action="store_true",
                    help="print every setting in effect, with where it came from, and exit")
    args = ap.parse_args(argv)
    if args.host:
        os.environ["RDTII_HOST"] = args.host
    if args.port is not None:
        os.environ["RDTII_PORT"] = str(args.port)

    if args.print_settings:
        for line in settings_report(settings_mod.load()):
            print(line)
        return 0
    return run_window(args) if args.window else run_tab(args)


if __name__ == "__main__":
    sys.exit(main())
