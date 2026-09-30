"""Re-fetch the AU multi-volume compilations truncated by the epubFrame capture
(2026-07-17 defect; see docs/AU_HTML_TRUNCATION_AUDIT_2026-07-17.md).

For each truncated doc_id: resolve the act's dated epub URL from its /latest/downloads
page (official host only), fetch it through the FIXED pipeline (epub → ALL spine
documents concatenated, verified — the exact code path future crawls use), then store via
the normal orchestrator machinery so §5.4 supersession applies: the idmap allocates the
NEXT seq for the same law (au-ta1979-002), the new row carries "supersedes au-ta1979-001",
and no other doc_id changes. The superseded row is kept in the manifest (provenance) and
its crawl_notes are annotated so nobody consumes the truncated text unknowingly.

Every fetch is rate-limited, logged to crawl_log.jsonl, and leaves a .headers.json
sidecar, as always. Each stored artifact is acceptance-checked on the spot (complete
spine-marker set; the audit detector must report NOT truncated) — a shortfall stops the
doc with a loud failure, never a silent partial.

Usage:
  python tools/refetch_au_multivolume.py --handoff handoff1_v2 [--only au-ta1979-001,...]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config.settings import load_settings

from src.p1_scrape.adapters.au_legislation import _REG_ID, AuLegislationAdapter
from src.p1_scrape.cost import CostMeter
from src.p1_scrape.crawl_logger import CrawlLogger
from src.p1_scrape.dedup import Dedup
from src.p1_scrape.fetcher import Fetcher
from src.p1_scrape.manifest import validate_manifest, write_manifest
from src.p1_scrape.models import Candidate
from src.p1_scrape.orchestrator import _load_existing_manifest, _store_row
from src.p1_scrape.politeness import RateLimiter
from src.p1_scrape.storage import Storage

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_au_truncation import audit_document  # noqa: E402

# Priority order (P3's scored-indicator material first): TIA 1979 carries the s.187C
# 2-year metadata-retention obligation (AU P7-I3, host baseline r1-au-041); Telecom 1997
# and Corporations 2001 also carry scored material. The rest follow in doc_id order.
PRIORITY = ["au-ta1979-001", "au-ta1997-001", "au-ca2001-001"]

# Per-document acceptance probes (defect-specific): phrases that MUST be present in the
# complete text and were absent from the truncated volume-1 capture.
MUST_CONTAIN = {
    "au-ta1979-001": ["187C", "data retention"],
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--handoff", default="handoff1_v2")
    ap.add_argument("--only", default=None,
                    help="comma-separated doc_ids (default: all truncated per the audit)")
    args = ap.parse_args()
    out_dir = Path(args.handoff)

    rows_by_id = _load_existing_manifest(out_dir)

    # Target list: every AU html doc whose stored text the audit judges truncated and
    # that has NOT already been superseded by a complete re-fetch (idempotent re-runs).
    superseded = {m.group(1) for row in rows_by_id.values()
                  for m in [re.search(r"supersedes\s+(\S+)", row.get("crawl_notes") or "")]
                  if m}
    targets: list[str] = []
    for doc_id, row in rows_by_id.items():
        if doc_id in superseded:
            continue
        if not (row.get("economy") == "AU" and row.get("source_type") == "html"
                and "legislation.gov.au" in (row.get("source_url") or "")):
            continue
        text = (out_dir / row["local_path"]).read_text(encoding="utf-8", errors="replace")
        if audit_document(text)["truncated"]:
            targets.append(doc_id)
    if args.only:
        chosen = [d.strip() for d in args.only.split(",") if d.strip()]
        unknown = [d for d in chosen if d not in targets]
        if unknown:
            print(f"[refetch] NOT truncated / unknown: {unknown}")
        targets = [d for d in chosen if d in targets]
    targets.sort(key=lambda d: (PRIORITY.index(d) if d in PRIORITY else len(PRIORITY), d))
    print(f"[refetch] {len(targets)} truncated doc(s) to re-fetch: {targets[:5]}{'…' if len(targets) > 5 else ''}")

    settings = load_settings()
    logger = CrawlLogger(out_dir / "crawl_log.jsonl")
    storage = Storage(out_dir)
    dedup = Dedup(out_dir)
    rate = RateLimiter(settings.request_delay_seconds)
    meter = CostMeter()
    adapter = AuLegislationAdapter(cfg={})
    start = time.monotonic()
    ok_map: dict[str, str] = {}
    failed: list[str] = []

    with Fetcher(settings) as fetcher:
        for doc_id in targets:
            row = rows_by_id[doc_id]
            law = row["law_name_guess"]
            m = _REG_ID.search(row["source_url"] or "")
            if not m:
                logger.narrate(f"[refetch] XX {doc_id}: no register id in source_url")
                failed.append(doc_id)
                continue
            rate.wait(row["source_url"])
            _, epub_url = adapter._doc_urls(m.group(1), fetcher)
            if not epub_url:
                logger.narrate(f"[refetch] XX {doc_id}: could not resolve dated epub URL")
                failed.append(doc_id)
                continue
            cand = Candidate(
                url=epub_url, economy="AU", law_name_guess=law,
                law_number_guess=row.get("law_number_guess"),
                pillar_hint=row.get("pillar_hint"), indicator_hints=row.get("indicator_hints"),
                seed_query=row.get("seed_query"),
                publication_date=row.get("publication_date"),
                assent_date=row.get("assent_date"),
                commencement_date=row.get("commencement_date"),
                in_force_status=row.get("in_force_status"), force_form="html")
            (plan,) = adapter.build_plans(cand, forms="html")
            rate.wait(plan.url)
            result = fetcher.fetch(plan)
            meter.record_fetch(result)
            logger.log(plan.url, result.http,
                       outcome=("ok" if (result.ok and result.content) else "failed"),
                       note=f"{law} (multi-volume re-fetch, supersedes {doc_id})")
            if not (result.ok and result.content):
                logger.narrate(f"[refetch] XX {doc_id} {law}: fetch failed "
                               f"(HTTP {result.http.status}; {result.http.error})")
                failed.append(doc_id)
                continue

            before = set(rows_by_id)
            stored = _store_row(cand, plan, result, adapter, storage, dedup, meter,
                                logger, settings, rows_by_id)
            new_ids = set(rows_by_id) - before
            if not stored or len(new_ids) != 1:
                logger.narrate(f"[refetch] XX {doc_id} {law}: store failed "
                               f"(stored={stored}, new_ids={new_ids})")
                failed.append(doc_id)
                continue
            new_id = new_ids.pop()

            # Acceptance: the stored artifact must NOT be truncated any more.
            stored_text = (out_dir / rows_by_id[new_id]["local_path"]).read_text(
                encoding="utf-8", errors="replace")
            verdict = audit_document(stored_text)
            probes = [p for p in MUST_CONTAIN.get(doc_id, [])
                      if p.lower() not in stored_text.lower()]
            if verdict["truncated"] or probes:
                logger.narrate(f"[refetch] XX {new_id} FAILS acceptance "
                               f"(truncated={verdict['truncated']}, missing probes={probes})")
                failed.append(doc_id)
                continue

            # Honest labeling of the superseded row (manifest is living corpus state,
            # not an append-only log): say WHY it was superseded.
            old_note = row.get("crawl_notes") or ""
            row["crawl_notes"] = (old_note + "; " if old_note else "") + (
                f"superseded by {new_id} (2026-07-17: epubFrame capture held volume 1 of "
                f"{verdict['declared_volumes']} only — multi-volume truncation fix)")
            ok_map[doc_id] = new_id
            logger.narrate(f"[refetch] OK {doc_id} -> {new_id} "
                           f"({verdict['epub_spine_docs']} spine docs, "
                           f"last section {verdict['last_section']})")
            dedup.save()
            write_manifest(list(rows_by_id.values()), out_dir)

    dedup.save()
    write_manifest(list(rows_by_id.values()), out_dir)
    if targets:
        # An idle (0-target) idempotency re-run must not clobber the previous real
        # run's measured counters.
        meter.write(out_dir, wall_clock_seconds=time.monotonic() - start)
    report = validate_manifest(out_dir / "manifest.csv", settings.contract_version)
    logger.narrate(f"[refetch] done: {len(ok_map)} superseded OK, {len(failed)} failed; "
                   f"manifest {len(rows_by_id)} rows; validate "
                   f"{'OK' if report.ok else 'FAILED'}")
    logger.close()
    print(json.dumps({"ok": ok_map, "failed": failed, "validate_ok": report.ok}, indent=2))
    return 0 if (not failed and report.ok) else 1


if __name__ == "__main__":
    sys.exit(main())
