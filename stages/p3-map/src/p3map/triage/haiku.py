"""S3b — Haiku triage of the FULL gray band (the pre-registered A/B fallback).

The 2026-07-15 A/B measured local-qwen false-negative rate at 16% (gate: <5%),
so Haiku's verdicts REPLACE the local ones as the single triage standard.
Same lenient prompt as the local leg. Concurrent (thread pool over live API),
checkpointed to out/triage/haiku_results.jsonl, resume-safe.

Measured cost basis: $0.31 / 200 pairs -> ~$45 for 29,250.
"""
from __future__ import annotations

import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from config import manifest
from config.instrument import load as load_instrument
from config.llm.base import usd
from config.llm.factory import get_llm
from config.settings import INDICATORS, SETTINGS

WORKERS = SETTINGS.triage_workers   # settings, not code: the live hour is rate-limit-bound
JUDGE_SCHEMA = {
    "type": "object",
    "properties": {"keep": {"type": "boolean"},
                   "why": {"type": "string", "maxLength": 120}},
    "required": ["keep", "why"],
}
PROMPT = """You are screening legal provisions for a digital-trade regulation index.

INDICATOR {ind} — {name}:
{definition}

PROVISION (from {law}, {section}):
{text}

Question: could this provision PLAUSIBLY be relevant to the indicator above?
Be lenient — answer YES if there is any reasonable connection (screening only,
a stricter reviewer runs later). Answer NO only if it is clearly unrelated."""


def run_haiku_triage(limit: int = 0) -> None:
    t0 = time.time()
    # By indicator, not by glob. `glob("P*.yaml")` matched nothing once signature files were named
    # decimally, and this stage's errors default to KEEP, so it would have triaged the whole gray
    # band with no definitions and reported success.
    ins = load_instrument()
    defs = {ind: ins.signature(ind) for ind in INDICATORS}

    out_dir = SETTINGS.out_dir / "triage"
    out_dir.mkdir(parents=True, exist_ok=True)
    results_path = out_dir / "haiku_results.jsonl"
    done: set[tuple[str, str]] = set()
    if results_path.exists():
        with results_path.open(encoding="utf-8") as f:
            for line in f:
                try:
                    r = json.loads(line)
                    done.add((r["provision_id"], r["indicator"]))
                except json.JSONDecodeError:
                    continue

    texts, meta = {}, {}
    # ECONOMIES scopes a run (settings.py): the finale triages CN, LA and TL because SG, MY and AU
    # reuse Round 1's verified rows, and on 15 October the draw is ONE economy. Reading the whole
    # gray band regardless would have judged 42,263 pairs instead of 21,175 -- double the cost, and
    # in the live hour, time spent on five economies nobody asked about.
    only = set(SETTINGS.economies)
    pairs, skipped = [], 0
    with (SETTINGS.out_dir / "select" / "gray_pairs.jsonl").open(encoding="utf-8") as f:
        for line in f:
            p = json.loads(line)
            if only and p.get("economy") not in only:
                skipped += 1
                continue
            if (p["provision_id"], p["indicator"]) not in done:
                pairs.append(p)
    if only:
        print(f"[haiku-triage] ECONOMIES={','.join(sorted(only))}: {skipped:,} gray pairs outside the "
              f"scope skipped", flush=True)
    if limit:
        # A priced pre-flight. The keep rate decides S4's volume, and kappa = 0.213 was measured on
        # three ENGLISH economies, so it is a projection rather than a measurement for China, Lao
        # and Timor-Leste. Judging a few hundred pairs first costs cents and sizes the real run.
        pairs = pairs[:limit]
        print(f"[haiku-triage] --limit {limit}: judging {len(pairs):,} pairs only", flush=True)
    wanted = {p["provision_id"] for p in pairs}
    with (SETTINGS.index_dir / "prefilter_corpus.jsonl").open(encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if r["provision_id"] in wanted:
                texts[r["provision_id"]] = r["text"]
                meta[r["provision_id"]] = r
    print(f"[haiku-triage] resuming past {len(done)}; {len(pairs)} pairs to judge, "
          f"{WORKERS} workers", flush=True)

    client = get_llm(SETTINGS, role="verifier")  # claude-haiku-4-5
    lock = threading.Lock()
    counters = {"judged": 0, "kept": 0, "errors": 0}

    def judge(p: dict) -> dict:
        d = defs[p["indicator"]]
        m = meta.get(p["provision_id"], {})
        prompt = PROMPT.format(
            ind=p["indicator"], name=d.get("name", ""),
            definition=d.get("definition_text", ""),
            law=m.get("law_name") or "?", section=m.get("article_section") or "?",
            text=texts.get(p["provision_id"], "")[:2200])
        keep, why = True, "error-default-keep"
        try:
            v = client.complete(prompt, JUDGE_SCHEMA, max_tokens=100)
            keep, why = bool(v.get("keep")), str(v.get("why", ""))[:120]
        except Exception as e:
            with lock:
                counters["errors"] += 1
            why = f"error:{type(e).__name__}"
        return {"provision_id": p["provision_id"], "indicator": p["indicator"],
                "economy": p["economy"], "keep": keep, "why": why}

    with results_path.open("a", encoding="utf-8") as fout, \
            ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futures = [ex.submit(judge, p) for p in pairs]
        for fut in as_completed(futures):
            r = fut.result()
            with lock:
                fout.write(json.dumps(r, ensure_ascii=False) + "\n")
                counters["judged"] += 1
                counters["kept"] += int(r["keep"])
                if counters["judged"] % 500 == 0:
                    fout.flush()
                    rate = counters["judged"] / max(time.time() - t0, 1)
                    eta = (len(pairs) - counters["judged"]) / max(rate, 0.1) / 60
                    print(f"[haiku-triage] {counters['judged']}/{len(pairs)} "
                          f"({rate:.1f}/s, keep {counters['kept']/counters['judged']:.0%}, "
                          f"err {counters['errors']}, ETA {eta:.0f} min, "
                          f"${usd(client.model, client.usage):.2f})", flush=True)

    manifest.record("triage_haiku", model=client.model, judged=counters["judged"],
                    kept=counters["kept"], errors=counters["errors"],
                    resumed_past=len(done),
                    cost_usd=round(usd(client.model, client.usage), 4))
    print(f"[haiku-triage] done: {counters['judged']} judged, kept {counters['kept']} "
          f"({counters['kept']/max(counters['judged'],1):.0%}), errors {counters['errors']}, "
          f"cost ${usd(client.model, client.usage):.2f}, "
          f"{(time.time()-t0)/60:.0f} min", flush=True)


if __name__ == "__main__":
    import argparse

    _ap = argparse.ArgumentParser(description="S3b - Haiku triage of the gray band")
    _ap.add_argument("--limit", type=int, default=0,
                     help="judge at most N pairs (a priced pre-flight); 0 = the whole scope")
    run_haiku_triage(limit=_ap.parse_args().limit)
