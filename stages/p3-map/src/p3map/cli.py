"""p3-map CLI (PLAN §10.2). Phase-A subcommands are live; mapping stages land next.

Usage:
  python -m src.p3map.cli version
  python -m src.p3map.cli ingest
  python -m src.p3map.cli prefilter [--leg bm25|dense|both]
  python -m src.p3map.cli select
  python -m src.p3map.cli triage [--limit N]
"""
from __future__ import annotations

import argparse

from config.settings import SETTINGS


def main() -> None:
    ap = argparse.ArgumentParser(prog="p3-map")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("version")
    sub.add_parser("ingest")
    pf = sub.add_parser("prefilter")
    pf.add_argument("--leg", choices=["bm25", "dense", "both"], default="both")
    sub.add_parser("select")
    tr = sub.add_parser("triage")
    tr.add_argument("--limit", type=int, default=None)
    abt = sub.add_parser("ab-triage")
    abt.add_argument("--n", type=int, default=200)
    abm = sub.add_parser("ab-mapper")
    abm.add_argument("--n", type=int, default=150)
    args = ap.parse_args()

    if args.cmd == "version":
        print(f"p3-map 0.1.0 | CONTRACT_VERSION={SETTINGS.contract_version}")
    elif args.cmd == "ingest":
        from src.p3map.ingest import run_ingest
        run_ingest()
    elif args.cmd == "prefilter":
        if args.leg in ("bm25", "both"):
            from src.p3map.prefilter.bm25 import run_bm25
            run_bm25()
        if args.leg in ("dense", "both"):
            from src.p3map.prefilter.dense import run_dense
            run_dense()
    elif args.cmd == "select":
        from src.p3map.select import run_select
        run_select()
    elif args.cmd == "triage":
        from src.p3map.triage.local import run_triage
        run_triage(limit=args.limit)
    elif args.cmd == "ab-triage":
        from src.p3map.ab.ab_triage import run_ab_triage
        run_ab_triage(sample_n=args.n)
    elif args.cmd == "ab-mapper":
        from src.p3map.ab.ab_mapper import run_ab_mapper
        run_ab_mapper(n=args.n)


if __name__ == "__main__":
    main()
