"""S4 — the mapping run: schema-forced Sonnet verdicts per provision group.

Pairs = direct band + Haiku-triage keeps, grouped by provision (one call per
provision with its candidate indicator set). Cached instrument prefix
(decision #6). Concurrent, checkpointed to out/map/verdicts_<ECON>.jsonl,
cost-metered with a hard stop (COST_HARD_STOP applies to the whole run).

Every verdict carries a whitespace-collapsed quote-grounding flag; hard
validation (drop + log) happens in S5 validators, not here — recall first.
"""
from __future__ import annotations

import json
import re
import threading
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

from config.llm.base import usd
from config import manifest
from config.llm.factory import get_llm
from config.settings import SETTINGS
from src.p3map.mapping.anchor import anchor
from src.p3map.mapping.prompt import build_system_prefix, build_user_turn
from src.p3map.mapping.schema import (MAPPING_SCHEMA, MappingVerdict,
                                      coerce_verdict)

WORKERS = SETTINGS.map_workers   # settings, not code: the live hour is rate-limit-bound


def _ws(s: str) -> str:
    """Round 1's grounding comparison, kept for the audit trail.

    Nothing calls it any more: mapping/anchor.py does the work, because this comparison silently
    failed on Chinese (one inserted space, or "，" written as ",", and the row was lost).
    """
    return re.sub(r"\s+", " ", s or "").strip().lower()


def _load_pairs(economy: str) -> dict[str, set[str]]:
    """provision_id -> candidate indicators (direct band + haiku keeps)."""
    cands: dict[str, set[str]] = defaultdict(set)
    with (SETTINGS.out_dir / "select" / "direct_pairs.jsonl").open(encoding="utf-8") as f:
        for line in f:
            p = json.loads(line)
            if p["economy"] == economy:
                cands[p["provision_id"]].add(p["indicator"])
    with (SETTINGS.out_dir / "triage" / "haiku_results.jsonl").open(encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if r["economy"] == economy and r["keep"]:
                cands[r["provision_id"]].add(r["indicator"])
    return cands


def run_mapping(economy: str, limit: int | None = None) -> None:
    t0 = time.time()
    cands = _load_pairs(economy)

    out_dir = SETTINGS.out_dir / "map"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"verdicts_{economy}.jsonl"
    done: set[str] = set()
    if out_path.exists():
        kept_lines = []
        with out_path.open(encoding="utf-8") as f:
            for line in f:
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if "error" in r:  # error rows are retried, not resumed past
                    continue
                kept_lines.append(line)
                done.add(r["provision_id"])
        out_path.write_text("".join(kept_lines), encoding="utf-8")

    todo = [pid for pid in cands if pid not in done]
    if limit:
        todo = todo[:limit]
    wanted = set(todo)
    recs: dict[str, dict] = {}
    with (SETTINGS.index_dir / "prefilter_corpus.jsonl").open(encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if r["provision_id"] in wanted:
                recs[r["provision_id"]] = r

    system = build_system_prefix()
    client = get_llm(SETTINGS, role="mapper")
    n_pairs = sum(len(cands[p]) for p in todo)
    print(f"[map:{economy}] {len(todo)} provisions / {n_pairs} pairs "
          f"(resumed past {len(done)}); model {client.model}, {WORKERS} workers", flush=True)

    lock = threading.Lock()
    counters = {"done": 0, "applies": 0, "errors": 0, "ungrounded": 0, "quote_recut": 0}
    stop_flag = threading.Event()

    def map_one(pid: str) -> dict | None:
        if stop_flag.is_set():
            return None
        rec = recs.get(pid)
        if rec is None:
            return {"provision_id": pid, "error": "record-missing"}
        candidates = sorted(cands[pid])
        try:
            # long candidate lists produce long verdict arrays: budget output
            # by candidate count, retry once on truncation/validation failure
            max_out = 2048 + 512 * len(candidates)
            try:
                raw = client.complete(build_user_turn(rec, candidates), MAPPING_SCHEMA,
                                      system=system, max_tokens=max_out,
                                      cache_system=True)
                v = MappingVerdict.model_validate(coerce_verdict(raw))
            except Exception:
                raw = client.complete(build_user_turn(rec, candidates), MAPPING_SCHEMA,
                                      system=system, max_tokens=8192,
                                      cache_system=True)
                v = MappingVerdict.model_validate(coerce_verdict(raw))
            verdicts = []
            for x in v.verdicts:
                # M10: the quote is cut from the source by span selection, so what is filed
                # is the source's own bytes whatever the model did to the characters on the way
                # out. Round 1 compared whitespace-collapsed substrings and filed the model's
                # copy; on Chinese, one inserted space or one ASCII comma lost the row (and now
                # that an ungrounded row is not filed at all, it would lose it silently).
                a = anchor(x.verbatim_quote, rec["text"])
                row = {**x.model_dump(), "quote_grounded_ws": a.grounded,
                       "quote_anchor": a.how}
                if a.grounded:
                    if a.repaired:
                        row["verbatim_quote_model"] = x.verbatim_quote
                        row["verbatim_quote"] = a.quote
                    row["quote_span"] = [a.start, a.end]
                verdicts.append(row)
            return {
                "provision_id": pid, "economy": economy,
                "doc_id": rec["doc_id"], "law_name": rec.get("law_name"),
                "article_section": rec.get("article_section"),
                "candidates": candidates,
                "core_legal_question_answer": v.core_legal_question_answer,
                "who_is_regulated": v.who_is_regulated,
                "conditions_and_exceptions": v.conditions_and_exceptions,
                # which narrative fields came back blank (schema.py _record_narrative_gaps):
                # recorded so the gap is visible, never a reason to drop the provision.
                "narrative_gaps": v.narrative_gaps,
                "trap_checks": v.trap_checks.model_dump(),
                "verdicts": verdicts,
                "model": client.model,
            }
        except Exception as e:
            return {"provision_id": pid, "economy": economy,
                    "error": f"{type(e).__name__}: {str(e)[:150]}"}

    with out_path.open("a", encoding="utf-8") as fout, \
            ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futures = [ex.submit(map_one, pid) for pid in todo]
        for fut in as_completed(futures):
            row = fut.result()
            if row is None:
                continue
            with lock:
                fout.write(json.dumps(row, ensure_ascii=False) + "\n")
                counters["done"] += 1
                if "error" in row:
                    counters["errors"] += 1
                else:
                    counters["applies"] += sum(1 for x in row["verdicts"] if x["applies"])
                    counters["ungrounded"] += sum(
                        1 for x in row["verdicts"]
                        if x["applies"] and not x["quote_grounded_ws"])
                    counters["quote_recut"] += sum(
                        1 for x in row["verdicts"] if "verbatim_quote_model" in x)
                cost = usd(client.model, client.usage)
                if cost >= SETTINGS.cost_hard_stop:
                    print(f"[map:{economy}] HARD STOP at ${cost:.2f}", flush=True)
                    stop_flag.set()
                if counters["done"] % 100 == 0:
                    fout.flush()
                    rate = counters["done"] / max(time.time() - t0, 1)
                    eta = (len(todo) - counters["done"]) / max(rate, 0.01) / 60
                    print(f"[map:{economy}] {counters['done']}/{len(todo)} "
                          f"({rate:.1f}/s, fires {counters['applies']}, "
                          f"ungrounded {counters['ungrounded']}, err {counters['errors']}, "
                          f"ETA {eta:.0f} min, ${cost:.2f})", flush=True)

    cost = usd(client.model, client.usage)
    report = {"economy": economy, "provisions": counters["done"],
              "verdict_fires": counters["applies"],
              "ungrounded_fires": counters["ungrounded"],
              # how often the model's copy of the quote differed from the source's own bytes.
              # A quoting-fidelity number per engine, which Section 5 has no other source for.
              "quotes_recut_from_source": counters["quote_recut"],
              "errors": counters["errors"], "cost_usd": round(cost, 2),
              "elapsed_min": round((time.time() - t0) / 60, 1)}
    # cumulative merge (2026-07-16 audit item 2): never clobber prior tallies
    rp = out_dir / f"map_report_{economy}.json"
    if rp.exists():
        try:
            prev = json.loads(rp.read_text(encoding="utf-8"))
            for k, v in report.items():
                if isinstance(v, (int, float)) and isinstance(prev.get(k), (int, float)):
                    report[k] = round(v + prev[k], 2)
            if prev.get("cost_note"):
                report["cost_note"] = prev["cost_note"]
        except (json.JSONDecodeError, OSError):
            pass
    rp.write_text(json.dumps(report, indent=2), encoding="utf-8")
    # Per invocation, not cumulative: `mapped` against `resumed_past` is the second-pass
    # evidence Section 3 asks for — a rerun that fetched nothing has mapped 0.
    manifest.record("map", economy=economy, model=client.model,
                    provisions_mapped=counters["done"], resumed_past=len(done),
                    pairs=n_pairs, fires=counters["applies"],
                    ungrounded=counters["ungrounded"], errors=counters["errors"],
                    cost_usd=round(cost, 4))
    print(f"[map:{economy}] done (cumulative): {json.dumps(report)}", flush=True)


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(
        description="S4 live mapping for one economy. Retries once on a validation failure; the "
                    "batch lane (batch_runner) is half the price but asynchronous.")
    ap.add_argument("economy", nargs="?", default="SG")
    ap.add_argument("limit", nargs="?", type=int, default=None,
                    help="stop after this many provisions -- prices a pre-flight. NOTE it takes a "
                         "PREFIX of an ordered file, so the sample is not random and its keep rate "
                         "is not the band's: a 150-pair China pre-flight read 68%% against 35.7%% "
                         "for the full band.")
    a = ap.parse_args()
    run_mapping(a.economy, a.limit)
