"""S5 — blind verification of every fired verdict (PLAN §5.1).

For each (provision, indicator) the mapper fired, a DIFFERENT model (Haiku)
re-answers the core legal question fresh — it never sees the mapper's rationale.
Agree on `applies` and score_hint -> verified. Disagree -> one Opus tiebreak
(also blind); 2-of-3 majority decides, splits are flagged for human review.

Outputs out/verify/verified_<ECON>.jsonl: mapper verdicts + verifier_verdict
(agree | tiebreak_upheld | tiebreak_overturned | split_flagged) per fire.
"""
from __future__ import annotations

import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from config.llm.base import usd
from config import manifest
from config.llm.factory import get_llm
from config.settings import SETTINGS
from src.p3map.mapping.prompt import build_system_prefix

WORKERS = SETTINGS.verify_workers   # settings, not code: the live hour is rate-limit-bound
VERIFY_SCHEMA = {
    "type": "object",
    "properties": {
        "applies": {"type": "boolean"},
        "score_hint": {"type": "string", "enum": ["1", "0.5", "0", "n/a"]},
        "confidence": {"type": "number"},
        "reason": {"type": "string", "maxLength": 300},
    },
    "required": ["applies", "score_hint", "confidence", "reason"],
}
PROMPT = """PROVISION {pid}
Economy: {econ} | Law: {law} | Section: {section}
TEXT:
{text}

QUESTION (answer independently from the text alone): does this provision
constitute evidence for indicator {ind} under its scoring tree? Run the trap
checks in the system instructions before answering. If it applies, which
scoring branch fires ('1', '0.5', '0'); if not, 'n/a'."""


def run_verify(economy: str) -> None:
    t0 = time.time()
    system = build_system_prefix()

    fires = []
    with (SETTINGS.out_dir / "map" / f"verdicts_{economy}.jsonl").open(encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            if "error" in row:
                continue
            for v in row["verdicts"]:
                if v["applies"]:
                    fires.append((row, v))

    out_dir = SETTINGS.out_dir / "verify"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"verified_{economy}.jsonl"
    done: set[tuple[str, str]] = set()
    if out_path.exists():
        kept_lines = []
        with out_path.open(encoding="utf-8") as f:
            for line in f:
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if r.get("verifier_verdict") == "error":  # retried, not resumed past
                    continue
                kept_lines.append(line)
                done.add((r["provision_id"], r["indicator"]))
        out_path.write_text("".join(kept_lines), encoding="utf-8")
    todo = [(row, v) for row, v in fires
            if (row["provision_id"], v["indicator"]) not in done]

    wanted = {row["provision_id"] for row, _ in todo}
    texts: dict[str, str] = {}
    with (SETTINGS.index_dir / "prefilter_corpus.jsonl").open(encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if r["provision_id"] in wanted:
                texts[r["provision_id"]] = r["text"]

    verifier = get_llm(SETTINGS, role="verifier")
    escalator = get_llm(SETTINGS, role="escalation")
    print(f"[verify:{economy}] {len(todo)} fires to verify "
          f"(resumed past {len(done)}); {verifier.model} + {escalator.model} tiebreak",
          flush=True)

    lock = threading.Lock()
    counters = {"done": 0, "agree": 0, "tiebreaks": 0, "overturned": 0,
                "split": 0, "errors": 0}

    def check(row: dict, v: dict) -> dict:
        pid, ind = row["provision_id"], v["indicator"]
        prompt = PROMPT.format(pid=pid, econ=row["economy"], law=row.get("law_name"),
                               section=row.get("article_section"),
                               text=texts.get(pid, "")[:6000], ind=ind)
        base = {"provision_id": pid, "indicator": ind, "economy": row["economy"],
                "mapper": {k: v[k] for k in ("applies", "score_hint", "coverage",
                                             "verbatim_quote", "rationale",
                                             "confidence", "quote_grounded_ws")},
                "trap_checks": row["trap_checks"]}
        try:
            h = verifier.complete(prompt, VERIFY_SCHEMA, system=system,
                                  max_tokens=400, cache_system=True)
            h_agree = (bool(h["applies"]) == v["applies"]
                       and (not v["applies"] or h["score_hint"] == v["score_hint"]))
            if h_agree:
                return {**base, "verifier": h, "verifier_verdict": "agree",
                        "final_applies": v["applies"],
                        "final_score_hint": v["score_hint"]}
            o = escalator.complete(prompt, VERIFY_SCHEMA, system=system,
                                   max_tokens=400, cache_system=True)
            votes_apply = [v["applies"], bool(h["applies"]), bool(o["applies"])]
            maj = votes_apply.count(True) >= 2
            if maj == v["applies"]:
                verdict, fa = "tiebreak_upheld", v["applies"]
                fs = v["score_hint"]
            elif votes_apply.count(maj) == 3 or bool(h["applies"]) == bool(o["applies"]):
                verdict, fa = "tiebreak_overturned", maj
                fs = h["score_hint"] if bool(h["applies"]) == maj else o["score_hint"]
            else:
                verdict, fa, fs = "split_flagged", v["applies"], v["score_hint"]
            return {**base, "verifier": h, "escalation": o,
                    "verifier_verdict": verdict, "final_applies": fa,
                    "final_score_hint": fs}
        except Exception as e:
            return {**base, "verifier_verdict": "error",
                    "error": f"{type(e).__name__}: {str(e)[:150]}",
                    "final_applies": v["applies"], "final_score_hint": v["score_hint"]}

    with out_path.open("a", encoding="utf-8") as fout, \
            ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futures = [ex.submit(check, row, v) for row, v in todo]
        for fut in as_completed(futures):
            r = fut.result()
            with lock:
                fout.write(json.dumps(r, ensure_ascii=False) + "\n")
                counters["done"] += 1
                vv = r["verifier_verdict"]
                if vv == "agree":
                    counters["agree"] += 1
                elif vv.startswith("tiebreak"):
                    counters["tiebreaks"] += 1
                    if vv == "tiebreak_overturned":
                        counters["overturned"] += 1
                elif vv == "split_flagged":
                    counters["split"] += 1
                else:
                    counters["errors"] += 1
                if counters["done"] % 100 == 0:
                    fout.flush()
                    cost = usd(verifier.model, verifier.usage) + usd(
                        escalator.model, escalator.usage)
                    print(f"[verify:{economy}] {counters['done']}/{len(todo)} "
                          f"agree {counters['agree']} tiebreak {counters['tiebreaks']} "
                          f"(overturned {counters['overturned']}) split {counters['split']} "
                          f"err {counters['errors']} ${cost:.2f}", flush=True)

    cost = usd(verifier.model, verifier.usage) + usd(escalator.model, escalator.usage)
    report = {**counters, "economy": economy, "cost_usd": round(cost, 2),
              "elapsed_min": round((time.time() - t0) / 60, 1)}
    # cumulative merge (2026-07-16 audit item 2): resume runs must never
    # clobber prior tallies — sum numeric fields with any existing report
    rp = out_dir / f"verify_report_{economy}.json"
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
    manifest.record("verify", economy=economy, verifier=verifier.model,
                    escalation=escalator.model, fires_verified=counters["done"],
                    resumed_past=len(done), agree=counters["agree"],
                    tiebreaks=counters["tiebreaks"], overturned=counters["overturned"],
                    errors=counters["errors"], cost_usd=round(cost, 4))
    print(f"[verify:{economy}] done (cumulative): {json.dumps(report)}", flush=True)


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="S5 blind verification: a second model re-judges every fire without seeing the first model's reasoning, with a third as 2-of-3 tiebreak. Resumes, so a re-run costs only the new fires.")
    ap.add_argument("economy", nargs="?", default="SG")
    a = ap.parse_args()
    run_verify(a.economy)
