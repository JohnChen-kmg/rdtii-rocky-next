"""A/B #1 — is local qwen triage safe? (framework §2.3 gate)

Stratified sample of judged gray pairs (half keep / half drop, spread across
indicators). Haiku re-judges the SAME lenient prompt as reference. The number
that matters is the local FALSE-NEGATIVE rate: pairs qwen DROPPED that Haiku
would keep — those never reach the mapper. Gate: FN < 5% -> local triage stands;
else fall back to Haiku triage (+$60-100).

Cost: ~200 Haiku calls, short prompts -> well under $1.
"""
from __future__ import annotations

import json
import random
import time
from collections import defaultdict


from config.instrument import load as load_instrument
from config.llm.base import usd
from config.llm.factory import get_llm
from config.settings import INDICATORS, SETTINGS

SAMPLE_N = 200
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


def run_ab_triage(sample_n: int = SAMPLE_N) -> dict:
    rng = random.Random(42)  # reproducible sample
    # By indicator, not by glob: glob("P*.yaml") matches nothing once the signature files are
    # named decimally, and this stage defaults to KEEP on a missing definition.
    ins = load_instrument()
    defs = {ind: ins.signature(ind) for ind in INDICATORS}

    judged = []
    with (SETTINGS.out_dir / "triage" / "triage_results.jsonl").open(encoding="utf-8") as f:
        for line in f:
            judged.append(json.loads(line))
    keeps = [j for j in judged if j["keep"] and not j["why"].startswith("error")]
    drops = [j for j in judged if not j["keep"]]
    per_bucket = sample_n // 2
    sample = (rng.sample(keeps, min(per_bucket, len(keeps)))
              + rng.sample(drops, min(per_bucket, len(drops))))

    texts, meta = {}, {}
    wanted = {s["provision_id"] for s in sample}
    with (SETTINGS.index_dir / "prefilter_corpus.jsonl").open(encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if r["provision_id"] in wanted:
                texts[r["provision_id"]] = r["text"]
                meta[r["provision_id"]] = r

    haiku = get_llm(SETTINGS, role="verifier")  # claude-haiku-4-5
    t0 = time.time()
    rows, confusion = [], defaultdict(int)
    for s in sample:
        d = defs[s["indicator"]]
        m = meta.get(s["provision_id"], {})
        prompt = PROMPT.format(
            ind=s["indicator"], name=d.get("name", ""), definition=d.get("definition_text", ""),
            law=m.get("law_name") or "?", section=m.get("article_section") or "?",
            text=texts.get(s["provision_id"], "")[:2200])
        v = haiku.complete(prompt, JUDGE_SCHEMA, max_tokens=100)
        h_keep = bool(v.get("keep"))
        confusion[f"qwen={'K' if s['keep'] else 'D'}|haiku={'K' if h_keep else 'D'}"] += 1
        rows.append({**s, "haiku_keep": h_keep, "haiku_why": v.get("why", "")})

    dropped = [r for r in rows if not r["keep"]]
    fn = sum(1 for r in dropped if r["haiku_keep"])
    fn_rate = fn / len(dropped) if dropped else 0.0
    report = {
        "sample": len(rows),
        "confusion": dict(confusion),
        "local_false_negative_rate": round(fn_rate, 4),
        "gate": "PASS (<5%): keep local triage" if fn_rate < 0.05
                else "FAIL (>=5%): fall back to Haiku triage",
        "haiku_usage": vars(haiku.usage),
        "haiku_cost_usd": round(usd(haiku.model, haiku.usage), 4),
        "elapsed_seconds": round(time.time() - t0, 1),
        "disagreements": [r for r in rows if r["keep"] != r["haiku_keep"]][:40],
    }
    out = SETTINGS.out_dir / "ab" / "ab_triage_report.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: report[k] for k in
                      ("sample", "confusion", "local_false_negative_rate", "gate",
                       "haiku_cost_usd")}, indent=2))
    return report


if __name__ == "__main__":
    run_ab_triage()
