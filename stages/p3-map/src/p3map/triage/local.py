"""S3 — gray-band triage on the local model (qwen2.5:14b via Ollama). $0.

Kickoff decision #3: local models never MAP or VERIFY — this stage only answers
a lenient binary relevance question ("could this provision plausibly bear on
this indicator?") to cut the gray band before paid mapping. Recall-biased:
uncertain -> KEEP. Checkpointed to out/triage/triage_results.jsonl (resume-safe).
"""
from __future__ import annotations

import json
import re
import time

import httpx

from config.instrument import load as load_instrument
from config.settings import INDICATORS, SETTINGS

PROMPT = """You are screening legal provisions for a digital-trade regulation index.

INDICATOR {ind} — {name}:
{definition}

PROVISION (from {law}, {section}):
{text}

Question: could this provision PLAUSIBLY be relevant to the indicator above?
Be lenient — answer YES if there is any reasonable connection (screening only,
a stricter reviewer runs later). Answer NO only if it is clearly unrelated.

Reply with exactly one line of JSON: {{"keep": true/false, "why": "<max 15 words>"}}"""


def _defs() -> dict[str, dict]:
    ins = load_instrument()
    out = {}
    for ind in INDICATORS:
        sig = ins.signature(ind)
        out[ind] = {"name": sig.get("name", ind),
                    "definition": sig.get("definition_text", "")}
    return out


def _corpus_text() -> dict[str, str]:
    texts = {}
    with (SETTINGS.index_dir / "prefilter_corpus.jsonl").open(encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            texts[r["provision_id"]] = r["text"]
    return texts


def run_triage(limit: int | None = None) -> None:
    t0 = time.time()
    defs = _defs()
    texts = _corpus_text()

    out_dir = SETTINGS.out_dir / "triage"
    out_dir.mkdir(parents=True, exist_ok=True)
    results_path = out_dir / "triage_results.jsonl"

    done: set[tuple[str, str]] = set()
    if results_path.exists():
        with results_path.open(encoding="utf-8") as f:
            for line in f:
                try:
                    r = json.loads(line)
                    done.add((r["provision_id"], r["indicator"]))
                except json.JSONDecodeError:
                    continue
    print(f"[triage] resuming past {len(done)} judged pairs", flush=True)

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
        print(f"[triage] ECONOMIES={','.join(sorted(only))}: {skipped:,} gray pairs outside the "
              f"scope skipped", flush=True)
    if limit:
        pairs = pairs[:limit]
    total = len(pairs)
    print(f"[triage] {total} pairs to judge on {SETTINGS.triage_model}", flush=True)

    client = httpx.Client(timeout=120)
    url = f"{SETTINGS.ollama_host}/api/generate"
    kept = judged = errors = 0
    with results_path.open("a", encoding="utf-8") as fout:
        for p in pairs:
            d = defs[p["indicator"]]
            prompt = PROMPT.format(
                ind=p["indicator"], name=d["name"], definition=d["definition"],
                law=p.get("law_name") or "?", section=p.get("article_section") or "?",
                text=texts.get(p["provision_id"], "")[:2200],
            )
            keep, why = True, "triage-error-default-keep"  # recall-biased default
            try:
                resp = client.post(url, json={
                    "model": SETTINGS.triage_model, "prompt": prompt,
                    "stream": False, "format": "json",
                    # num_ctx: Ollama defaults to 2,048 and truncates from the front, which
                    # would drop the indicator definition and leave the provision. 2,200
                    # characters of Lao is about 2,730 tokens (measured 1.24 tokens/char
                    # against 0.21 for English), so the default overflows on that corpus in
                    # a stage whose errors default to KEEP.
                    "options": {"temperature": 0.0, "num_predict": 60,
                                "num_ctx": SETTINGS.ollama_num_ctx},
                })
                resp.raise_for_status()
                raw = resp.json().get("response", "")
                m = re.search(r"\{.*\}", raw, re.S)
                if m:
                    j = json.loads(m.group(0))
                    keep = bool(j.get("keep", True))
                    why = str(j.get("why", ""))[:120]
            except Exception as e:  # keep on any failure — recall over precision
                errors += 1
                why = f"error:{type(e).__name__}"
            judged += 1
            kept += int(keep)
            fout.write(json.dumps({
                "provision_id": p["provision_id"], "indicator": p["indicator"],
                "economy": p["economy"], "keep": keep, "why": why,
            }, ensure_ascii=False) + "\n")
            if judged % 200 == 0:
                fout.flush()
                rate = judged / max(time.time() - t0, 1)
                eta_h = (total - judged) / max(rate, 0.01) / 3600
                print(f"[triage] {judged}/{total} ({rate:.2f}/s, keep {kept/judged:.0%}, "
                      f"err {errors}, ETA {eta_h:.1f}h)", flush=True)

    print(f"[triage] done: {judged} judged, kept {kept} ({kept/max(judged,1):.0%}), "
          f"errors {errors}, {(time.time()-t0)/3600:.2f}h", flush=True)


if __name__ == "__main__":
    import sys
    run_triage(limit=int(sys.argv[1]) if len(sys.argv) > 1 else None)
