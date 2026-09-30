"""Pre-flight integrity check (2026-07-16 audit, item 1b) — gates every S4 batch.

Verifies every provision_id in out/select/{direct,gray}_pairs.jsonl against
handoff2/provisions.jsonl. Two classes:

  synthetic  — ingest-minted source-text chunks ("<doc>#st.<n>") for the seven
               thin-extraction docs (§3.4d). Expected in pairs BY DESIGN for
               retrieval; the submission writer must re-anchor or doc-fallback
               them (never ship empty URL/section). Reported, not fatal.
  phantom    — any other id absent from the corpus. FATAL: regenerate pair
               files before firing any batch.

Exit code 1 on phantoms. Report: out/preflight_report.json.
"""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict

from config.settings import SETTINGS

_ST = re.compile(r"#st\.\d+$")


def run_preflight() -> dict:
    corpus_ids: set[str] = set()
    with (SETTINGS.handoff2_dir / "provisions.jsonl").open(encoding="utf-8") as f:
        for line in f:
            m = re.search(r'"provision_id":\s*"([^"]+)"', line[:400])
            if m:
                corpus_ids.add(m.group(1))
    print(f"[preflight] corpus ids: {len(corpus_ids)}")

    counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    phantom_samples: list[str] = []
    for band in ("direct", "gray"):
        p = SETTINGS.out_dir / "select" / f"{band}_pairs.jsonl"
        with p.open(encoding="utf-8") as f:
            for line in f:
                r = json.loads(line)
                econ = r.get("economy", "?")
                counts[econ]["pairs"] += 1
                pid = r["provision_id"]
                if pid in corpus_ids:
                    counts[econ]["ok"] += 1
                elif _ST.search(pid):
                    counts[econ]["synthetic"] += 1
                else:
                    counts[econ]["phantom"] += 1
                    if len(phantom_samples) < 20:
                        phantom_samples.append(f"{band}:{pid}")

    total_phantoms = sum(c["phantom"] for c in counts.values())
    report = {
        "corpus_ids": len(corpus_ids),
        "per_economy": {e: dict(c) for e, c in sorted(counts.items())},
        "phantom_total": total_phantoms,
        "phantom_samples": phantom_samples,
        "verdict": "PASS" if total_phantoms == 0 else "FAIL — regenerate pair files",
        "note": "synthetic = ingest source-text chunks (§3.4d), expected; the "
                "submission writer re-anchors or doc-falls-back these ids",
    }
    (SETTINGS.out_dir / "preflight_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report["per_economy"], indent=1))
    print(f"[preflight] {report['verdict']} (synthetic chunks are non-fatal by design)")
    return report


if __name__ == "__main__":
    sys.exit(0 if run_preflight()["phantom_total"] == 0 else 1)
