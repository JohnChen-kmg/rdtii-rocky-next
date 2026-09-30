"""Hold-out robustness smoke test (2026-07-16 follow-up, item 2).

Judges re-run the pipeline on a hold-out economy. S9 must not crash on an
economy code outside {SG,AU,MY} and must never emit an empty Source URL —
even with zero pipeline artifacts and zero baseline rows for that economy.

    python -m tests.test_holdout_smoke
"""
from __future__ import annotations

import csv

from config.settings import SETTINGS
from src.p3map.output.submission import run_submission


def main() -> None:
    econ = "XX"  # not in ECON_NAME, no artifacts, no baseline, no corpus
    run_submission(econ)
    csv_path = SETTINGS.out_dir / "submission" / f"records_{econ}.csv"
    with csv_path.open(encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 9, f"expected 9 no-provision rows, got {len(rows)}"
    empty_urls = [r["Indicator ID"] for r in rows if not r["Source URL"].strip()]
    assert not empty_urls, f"empty Source URL on {empty_urls}"
    bad_sec = [r["Indicator ID"] for r in rows
               if r["Article / Section"] != "n/a"]
    assert not bad_sec, f"Article/Section not 'n/a' on {bad_sec}"
    assert all(r["Economy"] == econ for r in rows), "ECON_NAME fallback failed"
    assert all(r["Notes"].startswith("no-provision row:") for r in rows)
    # clean up so the fake economy never pollutes real artifacts
    csv_path.unlink()
    (SETTINGS.out_dir / "submission" / f"records_{econ}.json").unlink()
    print(f"HOLD-OUT SMOKE PASS: {len(rows)} no-provision rows, "
          "no empty URL, Article/Section='n/a', no crash")


if __name__ == "__main__":
    main()
