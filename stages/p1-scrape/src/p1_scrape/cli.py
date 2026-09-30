"""Canonical CLI: `p1-scrape crawl | smoke | validate` (contract §5.3).

Also runnable as `python -m p1_scrape ...`. The friendly wrapper `scrape.py`
maps README-style flags onto these verbs.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from config.settings import load_settings

from .economies import BadCountryInput, parse_economies, parse_pillars


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="p1-scrape",
        description="RDTII Project 1 — crawl live SG/AU/MY legal portals → Hand-off #1.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_crawl = sub.add_parser("crawl", help="Crawl portal(s) and write handoff1/.")
    p_crawl.add_argument("--economy", required=True,
                         help="SG|AU|MY or full name; comma-separated; 'all'.")
    p_crawl.add_argument("--pillars", default="6,7", help="Pillar filter, e.g. 6 or 6,7.")
    p_crawl.add_argument("--out", default="handoff1", help="Output hand-off dir.")
    p_crawl.add_argument("--scope", choices=["seed", "relevant", "all"], default="relevant",
                         help="seed=seed_laws only; relevant=+vocabulary-matched acts; all=whole inventory.")
    p_crawl.add_argument("--forms", choices=["pdf", "html", "both"], default=None,
                         help="Representations per law (default: pdf for --scope all, both otherwise).")
    p_crawl.add_argument("--seed-laws-only", action="store_true",
                         help="Shortcut for --scope seed (deterministic slice path).")
    p_crawl.add_argument("--dry-run", action="store_true",
                         help="Discover + log candidates + write inventory, do not fetch bodies.")

    p_smoke = sub.add_parser("smoke", help="3-portal live-fetch smoke test (banks the 10-pt evidence).")
    p_smoke.add_argument("--out", default="handoff1", help="Output hand-off dir.")

    p_val = sub.add_parser("validate", help="Validate a manifest against the frozen schema.")
    p_val.add_argument("--manifest", required=True, help="Path to handoff1/manifest.csv.")
    p_val.add_argument("--no-file-check", action="store_true",
                       help="Skip on-disk resolution of local_path/http_headers_path.")

    return parser


def cmd_validate(args) -> int:
    from .manifest import validate_manifest

    settings = load_settings()
    report = validate_manifest(
        Path(args.manifest),
        expected_contract_version=settings.contract_version,
        check_files=not args.no_file_check,
    )
    for w in report.warnings:
        print(f"[validate] WARN  {w}")
    for e in report.errors:
        print(f"[validate] ERROR {e}")
    status = "OK" if report.ok else "FAILED"
    print(f"[validate] {status}: {report.row_count} row(s), "
          f"{len(report.errors)} error(s), {len(report.warnings)} warning(s) "
          f"[contract {settings.contract_version}]")
    return 0 if report.ok else 1


def cmd_smoke(args) -> int:
    from .smoke import run_smoke

    settings = load_settings()
    return run_smoke(out_dir=Path(args.out), settings=settings)


def cmd_crawl(args) -> int:
    from .orchestrator import run_crawl

    settings = load_settings()
    try:
        economies = parse_economies(args.economy)
    except BadCountryInput as e:
        print(f"[crawl] WARN unrecognized economy {str(e)!r} — skipping; nothing to crawl.",
              file=sys.stderr)
        return 2
    pillars = parse_pillars(args.pillars)
    return run_crawl(
        economies=economies,
        pillars=pillars,
        out_dir=Path(args.out),
        seed_laws_only=args.seed_laws_only,
        dry_run=args.dry_run,
        settings=settings,
        scope=args.scope,
        forms=args.forms,
    )


_DISPATCH = {"validate": cmd_validate, "smoke": cmd_smoke, "crawl": cmd_crawl}


def _force_utf8_stdout() -> None:
    """Windows consoles default to cp1252 and choke on non-ASCII (arrows, law names)."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
        except Exception:
            pass


def main(argv: list[str] | None = None) -> int:
    _force_utf8_stdout()
    args = build_parser().parse_args(argv)
    handler = _DISPATCH[args.command]
    return handler(args)


if __name__ == "__main__":
    sys.exit(main())
