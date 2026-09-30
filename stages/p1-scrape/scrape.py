#!/usr/bin/env python3
"""Friendly Quick-Start wrapper → the canonical `p1-scrape` verbs.

    python scrape.py --economy Singapore --pillar 6 [--seed-laws-only] [--out handoff1]
    python scrape.py --all --pillars 6,7
    python scrape.py --smoke
    python scrape.py --validate handoff1/manifest.csv

Windows note: invoke with the venv interpreter, e.g.
    .\\.venv\\Scripts\\python scrape.py --smoke
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
for _p in (str(_ROOT), str(_ROOT / "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from p1_scrape.cli import main as cli_main  # noqa: E402


def _translate(argv: list[str]) -> list[str]:
    ap = argparse.ArgumentParser(
        prog="scrape.py", description="Friendly wrapper for p1-scrape."
    )
    ap.add_argument("--economy", help="SG|AU|MY or full name; comma-separated.")
    ap.add_argument("--all", action="store_true", help="Crawl SG, AU and MY.")
    ap.add_argument("--pillar", "--pillars", dest="pillars", default="6,7")
    ap.add_argument("--out", default="handoff1")
    ap.add_argument("--scope", choices=["seed", "relevant", "all"], default="relevant")
    ap.add_argument("--forms", choices=["pdf", "html", "both"], default=None)
    ap.add_argument("--seed-laws-only", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--smoke", action="store_true", help="3-portal live-fetch smoke.")
    ap.add_argument("--validate", metavar="MANIFEST", help="Validate a manifest.csv.")
    args = ap.parse_args(argv)

    if args.validate:
        return ["validate", "--manifest", args.validate]
    if args.smoke:
        return ["smoke", "--out", args.out]

    economy = "all" if args.all else args.economy
    if not economy:
        ap.error("one of --economy / --all / --smoke / --validate is required")
    canonical = ["crawl", "--economy", economy, "--pillars", args.pillars,
                 "--out", args.out, "--scope", args.scope]
    if args.forms:
        canonical += ["--forms", args.forms]
    if args.seed_laws_only:
        canonical.append("--seed-laws-only")
    if args.dry_run:
        canonical.append("--dry-run")
    return canonical


def main() -> int:
    return cli_main(_translate(sys.argv[1:]))


if __name__ == "__main__":
    sys.exit(main())
