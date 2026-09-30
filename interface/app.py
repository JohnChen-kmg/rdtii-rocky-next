"""RDTII Rocky interface. Start it with:

    python interface/app.py

then open the address it prints. Standard library only; nothing to install. Every location it reads is
a setting (see interface/DATA_PATHS.md); the defaults work on a clean clone and show the fixture rows.
"""
from __future__ import annotations

import argparse
import os
import sys
import webbrowser
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from rdtii_ui import core, fsguard, jobs, probes, review, settings as settings_mod  # noqa: E402
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
    return app


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="app.py", description="RDTII Rocky interface (standard library only)")
    ap.add_argument("--host", help="bind address (default RDTII_HOST or 127.0.0.1)")
    ap.add_argument("--port", type=int, help="port (default RDTII_PORT or 8765)")
    ap.add_argument("--open", action="store_true", help="open the page in the default browser")
    ap.add_argument("--debug", action="store_true", help="log every request and traceback")
    args = ap.parse_args(argv)
    if args.host:
        os.environ["RDTII_HOST"] = args.host
    if args.port:
        os.environ["RDTII_PORT"] = str(args.port)

    app = build_app()
    app.debug = args.debug
    server = make_server(app)
    s = app.settings
    url = f"http://{s.host}:{s.port}/"
    present = probes.stage_presence(s)
    print(f"RDTII Rocky interface  {url}", flush=True)
    print(f"  repository : {settings_mod.REPO}")
    print(f"  showing    : OUT_DIR={s.out_dir}")
    print(f"  runs root  : {s.runs_root}")
    print(f"  inbox      : {s.inbox_dir}  (hand-collected files, one folder per economy)")
    print("  stages     : " + ", ".join(f"{k} {'present' if v['present'] else 'MISSING'}" for k, v in present.items()))
    print(f"  engines    : {', '.join(app.engines.ids()) or 'none declared'} (selected {app.engines.selected})")
    print("  Ctrl+C stops the server.", flush=True)
    if args.open:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
