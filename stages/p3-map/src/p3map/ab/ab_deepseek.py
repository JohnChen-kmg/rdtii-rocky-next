"""A/B-3 (triage) + A/B-4 (mapper) for a cheap-model swap candidate: DeepSeek V4
Flash. Same methodology as A/B-1 (ab_triage.py) / A/B-2 (ab_mapper.py):
pre-registered decision rules, measure, binary PASS/FAIL.

TEST-ONLY. This module never imports into S3/S4/S5, never writes into out/map,
out/verify, out/submission, or any judged CSV. All output lands in out/ab/.
DeepSeek is reached over its OpenAI-compatible endpoint via httpx (already a
dep) — the `openai` package is deliberately NOT added to production deps.

Config is env-ONLY; the key is never written to any file, log line, or report:
    AB3_API_KEY     (required for spend)
    AB3_BASE_URL    (default https://api.deepseek.com)
    AB3_MODEL       (non-thinking arm, default deepseek-v4-flash)
    AB3_MODEL_THINK (thinking arm,     default deepseek-reasoner)
    AB3_BUDGET_USD  (hard cap, default 2.0)

Verbs:
    python -m src.p3map.ab.ab_deepseek validate       # $0 input check
    python -m src.p3map.ab.ab_deepseek preregister     # $0 write preregistration
    python -m src.p3map.ab.ab_deepseek ab3             # A/B-3 triage (spends)
    python -m src.p3map.ab.ab_deepseek ab4             # A/B-4 mapper (spends)
"""
from __future__ import annotations

import json
import os
import random
import re
import threading
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

import httpx
import yaml

from config.settings import SETTINGS
from src.p3map.mapping.prompt import build_system_prefix, build_user_turn
from src.p3map.mapping.schema import MAPPING_SCHEMA, MappingVerdict

# --- DeepSeek posted prices, $/1M tokens (retrieved 2026-07-18 from
# https://api-docs.deepseek.com/quick_start/pricing). deepseek-reasoner is the
# thinking mode of deepseek-v4-flash and shares its price card; reasoning tokens
# are billed as output tokens (no separate line item).
PRICE_TABLE = {
    "deepseek-v4-flash": {"cache_hit": 0.0028, "cache_miss": 0.14, "output": 0.28},
    "deepseek-reasoner": {"cache_hit": 0.0028, "cache_miss": 0.14, "output": 0.28},
    "deepseek-chat": {"cache_hit": 0.0028, "cache_miss": 0.14, "output": 0.28},
    "deepseek-v4-pro": {"cache_hit": 0.003625, "cache_miss": 0.435, "output": 0.87},
}
PRICE_META = {
    "source": "https://api-docs.deepseek.com/quick_start/pricing",
    "retrieved": "2026-07-18",
    "currency": "USD per 1,000,000 tokens",
    "note": "reasoner = thinking mode of v4-flash; reasoning tokens billed as "
            "output. deepseek-chat/deepseek-reasoner deprecate 2026-07-24.",
}

TRIAGE_PROMPT = """You are screening legal provisions for a digital-trade regulation index.

INDICATOR {ind} — {name}:
{definition}

PROVISION (from {law}, {section}):
{text}

Question: could this provision PLAUSIBLY be relevant to the indicator above?
Be lenient — answer YES if there is any reasonable connection (screening only,
a stricter reviewer runs later). Answer NO only if it is clearly unrelated."""
TRIAGE_SCHEMA = {"type": "object",
                 "properties": {"keep": {"type": "boolean"},
                                "why": {"type": "string", "maxLength": 120}},
                 "required": ["keep", "why"]}

AB_DIR = SETTINGS.out_dir / "ab"
CANONICAL_TRAP = "sg-pdpa2012-001#s.26(1)"  # P6-I4 applies; P6-I1 rejected


@dataclass
class AB3Config:
    base_url: str
    model: str
    model_think: str
    budget_usd: float
    has_key: bool

    @classmethod
    def from_env(cls) -> "AB3Config":
        return cls(
            base_url=os.getenv("AB3_BASE_URL", "https://api.deepseek.com"),
            model=os.getenv("AB3_MODEL", "deepseek-v4-flash"),
            model_think=os.getenv("AB3_MODEL_THINK", "deepseek-reasoner"),
            budget_usd=float(os.getenv("AB3_BUDGET_USD", "2.0")),
            has_key=bool(os.getenv("AB3_API_KEY", "").strip()),
        )


class BudgetExceeded(Exception):
    pass


class DeepSeekClient:
    """OpenAI-compatible chat client with per-call measured cost + a hard budget
    cap. Schema-forced via response_format=json_object (DeepSeek's reasoner arm
    does not accept forced tool_choice), with the JSON schema appended to the
    user turn; the S4 system prefix stays byte-identical for prefix caching."""

    def __init__(self, cfg: AB3Config) -> None:
        self.cfg = cfg
        self._key = os.getenv("AB3_API_KEY", "").strip()  # never persisted
        self.spent_usd = 0.0
        self.usage = defaultdict(int)
        self.calls = 0
        self.cache_hit_tokens = 0
        self.cache_miss_tokens = 0
        self._url = cfg.base_url.rstrip("/") + "/chat/completions"
        self._lock = threading.Lock()  # guards cost accounting under concurrency

    def _price(self, model: str) -> dict:
        return PRICE_TABLE.get(model, PRICE_TABLE["deepseek-v4-flash"])

    def complete(self, system: str | None, user: str, schema: dict, *,
                 model: str, max_tokens: int,
                 thinking: bool = False) -> tuple[dict | None, dict]:
        """Returns (parsed_or_None, meta). meta carries cost, tokens, mode,
        parse_ok, cache-hit share, and the exact thinking request state.
        Raises BudgetExceeded when the cap is hit. `thinking` toggles DeepSeek
        V4 reasoning via the documented request params (v4-pro reasons by
        default, so the non-thinking arm sends type=disabled explicitly).
        Thread-safe: budget check + accounting take the lock; the HTTP call
        does not."""
        with self._lock:
            if self.spent_usd >= self.cfg.budget_usd:
                raise BudgetExceeded(f"budget ${self.cfg.budget_usd} reached")
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        user_schema = (user + "\n\nReturn ONLY a JSON object conforming to this "
                       "JSON Schema (no prose, no markdown fence):\n"
                       + json.dumps(schema))
        messages.append({"role": "user", "content": user_schema})
        body = {"model": model, "messages": messages,
                "max_tokens": max_tokens, "temperature": 0,
                "response_format": {"type": "json_object"}}
        if thinking:
            body["thinking"] = {"type": "enabled"}
            body["reasoning_effort"] = "high"
        else:
            body["thinking"] = {"type": "disabled"}
        req_thinking = body["thinking"]["type"]
        t0 = time.time()
        parsed, err = None, None
        try:
            resp = httpx.post(self._url, json=body, timeout=120,
                              headers={"Authorization": f"Bearer {self._key}",
                                       "Content-Type": "application/json"})
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            u = data.get("usage", {}) or {}
            hit = int(u.get("prompt_cache_hit_tokens", 0) or 0)
            miss = int(u.get("prompt_cache_miss_tokens",
                             u.get("prompt_tokens", 0)) or 0)
            out = int(u.get("completion_tokens", 0) or 0)
            reasoning = int((u.get("completion_tokens_details") or {})
                            .get("reasoning_tokens", 0) or 0)
            p = self._price(model)
            cost = (hit * p["cache_hit"] + miss * p["cache_miss"]
                    + out * p["output"]) / 1e6  # reasoning ⊆ completion_tokens
            with self._lock:
                self.spent_usd += cost
                self.calls += 1
                self.cache_hit_tokens += hit
                self.cache_miss_tokens += miss
                for k, v in (("in_hit", hit), ("in_miss", miss),
                             ("out", out), ("reasoning", reasoning)):
                    self.usage[k] += v
            try:
                parsed = json.loads(content)
            except json.JSONDecodeError:
                m = re.search(r"\{.*\}", content, re.DOTALL)
                if m:
                    try:
                        parsed = json.loads(m.group(0))
                    except json.JSONDecodeError:
                        err = "json-parse-failed"
                else:
                    err = "json-parse-failed"
            meta = {"cost_usd": cost, "in_hit": hit, "in_miss": miss,
                    "out": out, "reasoning_tokens": reasoning,
                    "cache_hit_share": round(hit / max(hit + miss, 1), 3),
                    "parse_ok": parsed is not None, "error": err,
                    "req_thinking": req_thinking,
                    "elapsed_s": round(time.time() - t0, 2)}
            return parsed, meta
        except BudgetExceeded:
            raise
        except Exception as e:  # network/HTTP/etc — never leak the key in text
            msg = re.sub(re.escape(self._key), "<redacted>", str(e)) if self._key else str(e)
            return None, {"cost_usd": 0.0, "parse_ok": False,
                          "error": f"{type(e).__name__}: {msg[:150]}",
                          "req_thinking": req_thinking,
                          "elapsed_s": round(time.time() - t0, 2)}


# --------------------------------------------------------------------------- #
# input validation — fail loudly, named list                                  #
# --------------------------------------------------------------------------- #
def _required_inputs() -> dict[str, bool]:
    o, idx, inst = SETTINGS.out_dir, SETTINGS.index_dir, SETTINGS.instrument_dir
    checks = {
        "out/triage/triage_results.jsonl": (o / "triage" / "triage_results.jsonl").exists(),
        "out/triage/haiku_results.jsonl": (o / "triage" / "haiku_results.jsonl").exists(),
        "out/map/verdicts_SG.jsonl": (o / "map" / "verdicts_SG.jsonl").exists(),
        "out/map/verdicts_AU.jsonl": (o / "map" / "verdicts_AU.jsonl").exists(),
        "out/map/verdicts_MY.jsonl": (o / "map" / "verdicts_MY.jsonl").exists(),
        "out/verify/verified_SG.jsonl": (o / "verify" / "verified_SG.jsonl").exists(),
        "out/verify/verified_AU.jsonl": (o / "verify" / "verified_AU.jsonl").exists(),
        "out/verify/verified_MY.jsonl": (o / "verify" / "verified_MY.jsonl").exists(),
        "gold_set.jsonl": (inst / "gold" / "gold_set.jsonl").exists(),
        "instrument signatures": bool(list((inst / "signatures").glob("P*.yaml"))),
        "prefilter_corpus.jsonl": (idx / "prefilter_corpus.jsonl").exists(),
        "AB3_API_KEY (env)": bool(os.getenv("AB3_API_KEY", "").strip()),
    }
    return checks


def validate(verbose: bool = True) -> tuple[bool, list[str]]:
    checks = _required_inputs()
    missing = [k for k, ok in checks.items() if not ok]
    if verbose:
        for k, ok in checks.items():
            print(f"  [{'ok ' if ok else 'MISS'}] {k}")
        print(f"[validate] {'ALL PRESENT' if not missing else 'MISSING: ' + ', '.join(missing)}")
    return (not missing), missing


# --------------------------------------------------------------------------- #
# corpus / reference loaders                                                   #
# --------------------------------------------------------------------------- #
def _corpus_index() -> dict[str, dict]:
    recs = {}
    with (SETTINGS.index_dir / "prefilter_corpus.jsonl").open(encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            recs[r["provision_id"]] = r
    return recs


def _signatures() -> dict:
    defs = {}
    for f in (SETTINGS.instrument_dir / "signatures").glob("P*.yaml"):
        sig = yaml.safe_load(f.read_text(encoding="utf-8"))
        defs[sig["indicator"]] = sig
    return defs


def _haiku_triage_lookup() -> dict[tuple[str, str], bool]:
    out = {}
    with (SETTINGS.out_dir / "triage" / "haiku_results.jsonl").open(encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            out[(r["provision_id"], r["indicator"])] = bool(r["keep"])
    return out


# --------------------------------------------------------------------------- #
# A/B-3 sample reconstruction (pre-registered branch)                         #
# --------------------------------------------------------------------------- #
def reconstruct_ab3_sample(sample_n: int = 200) -> dict:
    """Mirror ab_triage.run_ab_triage's seed-42 stratified draw over
    triage_results.jsonl (qwen). Decide reuse-vs-redraw per the pre-registered
    rule and return the sample + provenance."""
    corpus = set(_corpus_index().keys())
    rng = random.Random(42)
    judged = [json.loads(l) for l in
              (SETTINGS.out_dir / "triage" / "triage_results.jsonl").open(encoding="utf-8")]
    keeps = [j for j in judged if j["keep"] and not j["why"].startswith("error")]
    drops = [j for j in judged if not j["keep"]]
    per = sample_n // 2
    sample = (rng.sample(keeps, min(per, len(keeps)))
              + rng.sample(drops, min(per, len(drops))))
    dead = [s["provision_id"] for s in sample if s["provision_id"] not in corpus]

    # cross-check: the 40 persisted A/B-1 disagreement ids should be in the sample
    ab1 = json.loads((SETTINGS.out_dir / "ab" / "ab_triage_report.json").read_text(encoding="utf-8"))
    ab1_dis = {d["provision_id"] for d in ab1.get("disagreements", [])}
    sample_ids = {s["provision_id"] for s in sample}
    dis_in_sample = ab1_dis & sample_ids

    if not dead:
        return {"branch": "reuse", "sample": sample, "n": len(sample),
                "dead_ab1_ids": [], "ab1_disagreements_in_sample":
                f"{len(dis_in_sample)}/{len(ab1_dis)}",
                "crosscheck_ok": len(dis_in_sample) == len(ab1_dis)}

    # REDRAW: seed-42 over current haiku_results.jsonl, same stratification
    rng2 = random.Random(42)
    hj = [json.loads(l) for l in
          (SETTINGS.out_dir / "triage" / "haiku_results.jsonl").open(encoding="utf-8")]
    hj = [j for j in hj if j["provision_id"] in corpus]
    hkeeps = [j for j in hj if j["keep"] and not str(j.get("why", "")).startswith("error")]
    hdrops = [j for j in hj if not j["keep"]]
    redraw = (rng2.sample(hkeeps, min(per, len(hkeeps)))
              + rng2.sample(hdrops, min(per, len(hdrops))))
    return {"branch": "redraw", "sample": redraw, "n": len(redraw),
            "dead_ab1_ids": dead, "n_dead": len(dead),
            "redraw_source": "out/triage/haiku_results.jsonl",
            "reason": f"{len(dead)} of {len(sample)} A/B-1 seed-42 ids no longer "
                      "resolve in the v2.4b index (retirement / re-segmentation)"}


# --------------------------------------------------------------------------- #
# A/B-3 run                                                                    #
# --------------------------------------------------------------------------- #
def run_ab3(sample_n: int = 200) -> dict:
    ok, missing = validate(verbose=False)
    if missing:
        return _abort_report("ab3", f"missing required inputs: {missing}")
    cfg = AB3Config.from_env()
    corpus = _corpus_index()
    defs = _signatures()
    hlook = _haiku_triage_lookup()
    samp = reconstruct_ab3_sample(sample_n)
    client = DeepSeekClient(cfg)

    from config.llm.factory import get_llm  # fresh Haiku only where needed
    haiku = get_llm(SETTINGS, role="verifier")

    rows, confusion = [], defaultdict(int)
    parse_fail, fresh_haiku, budget_aborted = 0, 0, False
    for s in samp["sample"]:
        pid, ind = s["provision_id"], s["indicator"]
        rec = corpus.get(pid)
        if rec is None:
            continue
        d = defs[ind]
        prompt = TRIAGE_PROMPT.format(
            ind=ind, name=d.get("name", ""), definition=d.get("definition_text", ""),
            law=rec.get("law_name") or "?", section=rec.get("article_section") or "?",
            text=(rec.get("text") or "")[:2200])
        try:
            # non-thinking screen; 512 tok headroom so any residual reasoning
            # on reason-by-default models (v4-pro) still leaves JSON content
            parsed, meta = client.complete(None, prompt, TRIAGE_SCHEMA,
                                           model=cfg.model, max_tokens=512,
                                           thinking=False)
        except BudgetExceeded:
            budget_aborted = True
            break
        ds_keep = bool(parsed.get("keep")) if parsed else True  # error defaults keep
        if not meta.get("parse_ok"):
            parse_fail += 1
        # reference = Haiku production verdict where present, else fresh Haiku
        if (pid, ind) in hlook:
            h_keep = hlook[(pid, ind)]
        else:
            fresh_haiku += 1
            try:
                hv = haiku.complete(prompt, TRIAGE_SCHEMA, max_tokens=100)
                h_keep = bool(hv.get("keep"))
            except Exception:
                h_keep = True
        confusion[f"deepseek={'K' if ds_keep else 'D'}|haiku={'K' if h_keep else 'D'}"] += 1
        rows.append({"provision_id": pid, "indicator": ind,
                     "deepseek_keep": ds_keep, "haiku_keep": h_keep,
                     "deepseek_why": (parsed or {}).get("why", "")[:120],
                     "parse_ok": meta.get("parse_ok"), "mode": "non-thinking"})

    ds_drops = [r for r in rows if not r["deepseek_keep"]]
    fn = sum(1 for r in ds_drops if r["haiku_keep"])
    fn_rate = fn / len(ds_drops) if ds_drops else 0.0
    agree = sum(1 for r in rows if r["deepseek_keep"] == r["haiku_keep"])
    from config.llm.base import usd as claude_usd
    report = {
        "test": "A/B-3 triage (DeepSeek vs Haiku reference)",
        "status": "BUDGET-ABORTED" if budget_aborted else "complete",
        "provider": "deepseek", "model": cfg.model, "mode": "non-thinking",
        "base_url": cfg.base_url, "price_table": PRICE_TABLE[cfg.model],
        "price_meta": PRICE_META,
        "sample_provenance": {k: v for k, v in samp.items() if k != "sample"},
        "n_judged": len(rows),
        "confusion": dict(confusion),
        "deepseek_false_negative_rate": round(fn_rate, 4),
        "overall_agreement": round(agree / len(rows), 4) if rows else None,
        "schema_parse_failure_rate": round(parse_fail / len(rows), 4) if rows else None,
        "fresh_haiku_calls": fresh_haiku,
        "gate": ("PASS (<5% FN): DeepSeek triage viable" if fn_rate < 0.05
                 else "FAIL (>=5% FN): DeepSeek triage not viable"),
        "deepseek_cost_usd": round(client.spent_usd, 4),
        "deepseek_calls": client.calls,
        "deepseek_cache_hit_share": round(
            client.cache_hit_tokens / max(client.cache_hit_tokens + client.cache_miss_tokens, 1), 3),
        "reference_haiku_cost_usd": round(claude_usd(haiku.model, haiku.usage), 4),
        "disagreements": [r for r in rows if r["deepseek_keep"] != r["haiku_keep"]][:5],
    }
    _write_report(report, section="ab3")
    print(json.dumps({k: report[k] for k in
                      ("status", "n_judged", "deepseek_false_negative_rate",
                       "overall_agreement", "schema_parse_failure_rate", "gate",
                       "deepseek_cost_usd")}, indent=2))
    return report


# --------------------------------------------------------------------------- #
# A/B-4 sampling + run                                                         #
# --------------------------------------------------------------------------- #
def _load_sonnet_verdicts(econ: str) -> dict[str, dict]:
    out = {}
    with (SETTINGS.out_dir / "map" / f"verdicts_{econ}.jsonl").open(encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if "error" not in r:
                out[r["provision_id"]] = r
    return out


def _verified_fires(econ: str) -> set[tuple[str, str]]:
    out = set()
    with (SETTINGS.out_dir / "verify" / f"verified_{econ}.jsonl").open(encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if r.get("final_applies") and r.get("verifier_verdict") in ("agree", "tiebreak_upheld"):
                out.add((r["provision_id"], r["indicator"]))
    return out


def sample_ab4(n: int = 150, seed: int = 4) -> dict:
    """150 provisions stratified across SG/AU/MY, oversampling trap-relevant and
    S5-verified provisions; the canonical SG s.26(1) trap is force-included."""
    rng = random.Random(seed)
    pool = {}          # pid -> {econ, row, trap, verified}
    for econ in ("SG", "AU", "MY"):
        sv = _load_sonnet_verdicts(econ)
        vf = _verified_fires(econ)
        for pid, row in sv.items():
            tc = row.get("trap_checks", {})
            trap = bool(tc.get("conditional_path_exists") or tc.get("retention_is_minimum")
                        or not tc.get("provision_in_force", True)
                        or any(v["indicator"] in ("P7-I1", "P7-I2") for v in row["verdicts"]))
            verified = any((pid, v["indicator"]) in vf for v in row["verdicts"])
            pool[pid] = {"econ": econ, "trap": trap, "verified": verified}
    trap_ids = [p for p, m in pool.items() if m["trap"]]
    ver_ids = [p for p, m in pool.items() if m["verified"] and not m["trap"]]
    rest_ids = [p for p, m in pool.items() if not m["trap"] and not m["verified"]]
    rng.shuffle(trap_ids); rng.shuffle(ver_ids); rng.shuffle(rest_ids)
    # oversample: ~50% trap, ~35% verified, ~15% rest
    picked = trap_ids[:int(n * 0.5)] + ver_ids[:int(n * 0.35)]
    picked += rest_ids[:max(0, n - len(picked))]
    picked = picked[:n]
    if CANONICAL_TRAP in pool and CANONICAL_TRAP not in picked:
        picked[-1] = CANONICAL_TRAP
    return {"seed": seed, "n": len(picked), "ids": picked,
            "strata": {"trap": sum(pool[p]["trap"] for p in picked),
                       "verified": sum(pool[p]["verified"] for p in picked),
                       "by_econ": dict(Counter(pool[p]["econ"] for p in picked))},
            "canonical_trap_included": CANONICAL_TRAP in picked}


def run_ab4(n: int = 150) -> dict:
    ok, missing = validate(verbose=False)
    if missing:
        return _abort_report("ab4", f"missing required inputs: {missing}")
    cfg = AB3Config.from_env()
    corpus = _corpus_index()
    samp = sample_ab4(n)
    sonnet = {}
    for econ in ("SG", "AU", "MY"):
        sonnet.update(_load_sonnet_verdicts(econ))
    vf_all = set()
    for econ in ("SG", "AU", "MY"):
        vf_all |= _verified_fires(econ)
    system = build_system_prefix()
    client = DeepSeekClient(cfg)

    # both arms use the SAME base model; thinking is a request flag (V4 param).
    # deepseek-v4-pro reasons by default so the non-thinking arm sends
    # type=disabled; the thinking arm sends enabled + reasoning_effort=high.
    arms = {"non-thinking": (cfg.model, False), "thinking": (cfg.model, True)}
    per_arm: dict[str, dict] = {}
    budget_aborted = False
    workers = int(os.getenv("AB3_WORKERS", "8"))

    def map_one(pid: str, model: str, think: bool) -> dict | None:
        rec = corpus.get(pid)
        srow = sonnet.get(pid)
        if rec is None or srow is None:
            return None
        candidates = sorted({v["indicator"] for v in srow["verdicts"]})
        max_out = (2048 + 512 * len(candidates)) * (2 if think else 1)
        user = build_user_turn(rec, candidates)
        parsed, meta = client.complete(system, user, MAPPING_SCHEMA,
                                       model=model, max_tokens=max_out,
                                       thinking=think)  # BudgetExceeded propagates
        valid, verdicts, traps = False, {}, {}
        if parsed is not None:
            try:
                v = MappingVerdict.model_validate(parsed)
                valid = True
                for x in v.verdicts:
                    verdicts[x.indicator] = {
                        "applies": x.applies, "score_hint": x.score_hint,
                        "coverage": x.coverage,
                        "quote_grounded": x.verbatim_quote in rec["text"],
                        "quote": x.verbatim_quote[:160]}
                traps = v.trap_checks.model_dump()
            except Exception:
                traps = {}
        return {"provision_id": pid, "econ": _econ_of(pid, sonnet),
                "candidates": candidates, "valid": valid,
                "verdicts": verdicts, "traps": traps,
                "model_version": model, "provider": "deepseek",
                "mode": "thinking" if think else "non-thinking",
                "req_thinking": meta.get("req_thinking"), "meta": meta,
                "sonnet": {v["indicator"]: v for v in srow["verdicts"]}}

    for arm, (model, think) in arms.items():
        rows = []
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futs = {ex.submit(map_one, pid, model, think): pid for pid in samp["ids"]}
            try:
                for fut in as_completed(futs):
                    r = fut.result()
                    if r is not None:
                        rows.append(r)
            except BudgetExceeded:
                budget_aborted = True
                for f in futs:
                    f.cancel()
        print(f"[ab4:{arm}] {len(rows)} provisions done, "
              f"${client.spent_usd:.3f} spent", flush=True)
        per_arm[arm] = _score_arm(model, rows, vf_all)
        if budget_aborted:
            break

    report = {
        "test": "A/B-4 mapper (DeepSeek vs Sonnet reference)",
        "status": "BUDGET-ABORTED" if budget_aborted else "complete",
        "provider": "deepseek", "base_url": cfg.base_url,
        "price_meta": PRICE_META,
        "sample": {k: v for k, v in samp.items() if k != "ids"},
        "reference": "out/map/verdicts_{SG,AU,MY}.jsonl (Sonnet; AU v2.4b)",
        "arms": per_arm,
        "deepseek_total_cost_usd": round(client.spent_usd, 4),
        "gates": "grounding>=0.98 AND agreement>=0.90 AND no systematic trap "
                 "failure -> PASS mapping. A/B-3 PASS + A/B-4 FAIL -> triage-only.",
    }
    _write_report(report, section="ab4")
    print(json.dumps({"status": report["status"],
                      "arms": {a: {k: d.get(k) for k in
                                   ("grounding_rate", "applies_agreement",
                                    "verdict_agreement_vs_verified",
                                    "trap_accuracy", "canonical_s26_ok",
                                    "schema_valid_rate", "gate",
                                    "cost_per_provision_usd")}
                               for a, d in per_arm.items()}}, indent=2))
    return report


def _econ_of(pid: str, sonnet: dict) -> str:
    return (sonnet.get(pid) or {}).get("economy", "?")


def _score_arm(model: str, rows: list[dict], vf_all: set) -> dict:
    g_ok = g_tot = 0
    ag = ag_tot = 0
    agv = agv_tot = 0
    trap_ok = trap_tot = 0
    valid = 0
    canon_ok = None
    per_econ = defaultdict(lambda: [0, 0])  # applies-agree, total
    for r in rows:
        valid += int(r["valid"])
        if not r["valid"]:
            continue
        for ind in r["candidates"]:
            dv = r["verdicts"].get(ind)
            sv = r["sonnet"].get(ind)
            if not (dv and sv):
                continue
            ag_tot += 1
            same = int(dv["applies"] == sv["applies"])
            ag += same
            per_econ[r["econ"]][1] += 1
            per_econ[r["econ"]][0] += same
            if (r["provision_id"], ind) in vf_all:
                agv_tot += 1
                agv += same
            if dv["applies"]:
                g_tot += 1
                g_ok += int(dv["quote_grounded"])
        # canonical s.26(1): P6-I4 applies True, P6-I1 applies False
        if r["provision_id"] == CANONICAL_TRAP:
            i4 = r["verdicts"].get("P6-I4"); i1 = r["verdicts"].get("P6-I1")
            canon_ok = bool(i4 and i4["applies"] and (not i1 or not i1["applies"]))
    # trap-set accuracy: over trap provisions, applies-agreement with Sonnet
    for r in rows:
        if not r["valid"]:
            continue
        tc = r["traps"]
        if not (tc.get("conditional_path_exists") or tc.get("retention_is_minimum")
                or not tc.get("provision_in_force", True)):
            continue
        for ind in r["candidates"]:
            dv, sv = r["verdicts"].get(ind), r["sonnet"].get(ind)
            if dv and sv:
                trap_tot += 1
                trap_ok += int(dv["applies"] == sv["applies"])
    cost = sum(r["meta"].get("cost_usd", 0) for r in rows)
    reasoning = sum(r["meta"].get("reasoning_tokens", 0) for r in rows)
    grounding = g_ok / g_tot if g_tot else None
    agreement = ag / ag_tot if ag_tot else None
    trap_acc = trap_ok / trap_tot if trap_tot else None
    gate = None
    if grounding is not None and agreement is not None:
        systematic_trap_fail = (trap_acc is not None and trap_acc < 0.90) or (canon_ok is False)
        gate = ("PASS" if grounding >= 0.98 and agreement >= 0.90
                and not systematic_trap_fail else "FAIL")
    return {
        "model": model, "n_provisions": len(rows),
        "schema_valid_rate": round(valid / len(rows), 4) if rows else None,
        "grounding_rate": round(grounding, 4) if grounding is not None else None,
        "grounding_n": g_tot,
        "applies_agreement": round(agreement, 4) if agreement is not None else None,
        "applies_agreement_n": ag_tot,
        "verdict_agreement_vs_verified": round(agv / agv_tot, 4) if agv_tot else None,
        "verdict_agreement_vs_verified_n": agv_tot,
        "trap_accuracy": round(trap_acc, 4) if trap_acc is not None else None,
        "trap_n": trap_tot,
        "canonical_s26_ok": canon_ok,
        "per_economy_applies_agreement": {e: round(a / b, 4) if b else None
                                          for e, (a, b) in per_econ.items()},
        "cost_usd": round(cost, 4),
        "cost_per_provision_usd": round(cost / len(rows), 5) if rows else None,
        "reasoning_tokens": reasoning,
        "projected_full_run_cost_usd_LABEL_PROJECTION":
            round(cost / len(rows) * 10574, 2) if rows else None,
        "gate": gate,
        "disagreement_examples": [
            {"provision_id": r["provision_id"], "indicator": ind,
             "deepseek": r["verdicts"].get(ind), "sonnet_applies":
             r["sonnet"].get(ind, {}).get("applies")}
            for r in rows if r["valid"]
            for ind in r["candidates"]
            if r["verdicts"].get(ind) and r["sonnet"].get(ind)
            and r["verdicts"][ind]["applies"] != r["sonnet"][ind]["applies"]][:5],
    }


# --------------------------------------------------------------------------- #
# reports                                                                      #
# --------------------------------------------------------------------------- #
def _abort_report(section: str, reason: str) -> dict:
    rep = {"test": section, "status": "BLOCKED", "reason": reason,
           "inputs": _required_inputs(), "price_meta": PRICE_META}
    _write_report(rep, section=section)
    print(f"[{section}] BLOCKED: {reason}")
    return rep


def _write_report(section_report: dict, section: str) -> None:
    AB_DIR.mkdir(parents=True, exist_ok=True)
    path = AB_DIR / "ab_deepseek_report.json"
    full = {}
    if path.exists():
        try:
            full = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            full = {}
    full[section] = section_report
    full["_meta"] = {"provider": "deepseek", "price_meta": PRICE_META,
                     "notes": [
                         "TEST-ONLY: no S3/S4/S5 default changed; nothing written "
                         "to out/map, out/verify, out/submission, or any judged CSV.",
                         "S5 blind verify remains Claude-family by design "
                         "(cross-family verification), regardless of this outcome.",
                         "No cross-provider output parity is claimed; the only "
                         "admissible claim shape is identical citations + disclosed "
                         "deltas (project honesty rule).",
                         "API key is env-only and never written to any file/log/report."]}
    path.write_text(json.dumps(full, indent=2, ensure_ascii=False), encoding="utf-8")


def write_preregistration(stamp: str) -> None:
    """$0. Writes the pre-registration BEFORE any spend, including the sample
    branch decided from the current index (reuse vs redraw). `stamp` is passed
    in (never Date.now here) so the caller controls the timestamp."""
    cfg = AB3Config.from_env()
    ok, missing = validate(verbose=False)
    try:
        samp = reconstruct_ab3_sample()
        branch = {k: v for k, v in samp.items() if k != "sample"}
    except Exception as e:
        branch = {"error": f"could not reconstruct: {type(e).__name__}: {e}"}
    md = f"""# A/B-3 (triage) + A/B-4 (mapper) — DeepSeek V4 Flash swap: PRE-REGISTRATION

Timestamp: {stamp}
Provider: DeepSeek (OpenAI-compatible), base {cfg.base_url}
Models: non-thinking `{cfg.model}` · thinking `{cfg.model_think}`
Budget cap: ${cfg.budget_usd:.2f} (hard; measured from API usage fields, abort → BUDGET-ABORTED)

Registered BEFORE any API spend. Methodology mirrors A/B-1 (ab_triage.py) and
A/B-2 (ab_mapper.py): fixed sample, fixed reference, pre-registered binary gate.

## Price table (posted, recorded pre-spend)
Source: {PRICE_META['source']} · retrieved {PRICE_META['retrieved']} · {PRICE_META['currency']}
- {cfg.model}: cache-hit {PRICE_TABLE[cfg.model]['cache_hit']} / cache-miss {PRICE_TABLE[cfg.model]['cache_miss']} / output {PRICE_TABLE[cfg.model]['output']}
- {cfg.model_think}: same card (reasoning tokens billed as output). {PRICE_META['note']}

## Input readiness (fail-loud list)
{"ALL PRESENT" if ok else "MISSING: " + ", ".join(missing)}

## A/B-3 — triage. Sample rule (branch chosen from the current index)
- Draw: `random.Random(42)` over `out/triage/triage_results.jsonl`, 100 keeps +
  100 drops, exactly as ab_triage.py. Validate every provision_id against the
  CURRENT (v2.4b) index.
- If ALL resolve → REUSE (cross-check: the 40 persisted A/B-1 disagreement ids
  must be in the sample). If ANY gone → REDRAW seed-42, same stratification,
  over current `out/triage/haiku_results.jsonl`; disclose the redraw + death count.
- **Decided now:** branch = **{branch.get('branch', 'unknown')}**; details:
  `{json.dumps(branch)}`
- Prompt: ab_triage.py PROMPT verbatim; parse errors default to KEEP.
- Reference = Haiku: production verdict from haiku_results.jsonl where the pair
  exists there, else a fresh Haiku call with the same prompt (split logged).
- Metrics: DeepSeek false-negative rate (drops that Haiku keeps), overall
  agreement, schema-parse-failure rate, measured $.
- **GATE: FN < 5% → PASS (DeepSeek triage viable).** Report, then STOP for
  John's go-ahead before any A/B-4 spend.

## A/B-4 — mapper (only after go-ahead)
- 150 provisions stratified SG/AU/MY × 9 indicators; oversample (a) trap-relevant
  (ban-vs-conditional, retention max/min, not-in-force, inverted P7-I1/I2) and
  (b) S5-verified fires. Seed logged. Canonical `sg-pdpa2012-001#s.26(1)`
  force-included.
- Same schema-forced S4 prompt (byte-identical system prefix for cache parity;
  DeepSeek enforcement = response_format json_object, not a tool call — recorded,
  no parity claimed). Output budget scales by candidate count.
- Reference = S4 Sonnet verdicts on disk (`out/map/verdicts_{{SG,AU,MY}}.jsonl`,
  AU v2.4b). TWO arms reported separately: non-thinking + thinking (reasoning
  tokens in cost).
- Metrics/arm: strict char-offset quote grounding; applies-agreement overall AND
  vs the S5-verified subset; trap-set accuracy (+ canonical s.26(1) must hold:
  P6-I4 applies, P6-I1 rejected); schema validity; per-economy (watch MY Malay
  grounding); measured cost/provision incl. reasoning; projected full-run cost
  (labelled projection).
- **GATES: grounding ≥ 98% AND agreement ≥ 90% AND no systematic trap failure →
  PASS mapping. A/B-3 PASS + A/B-4 FAIL → verdict "triage-only".**

## Invariants
- TEST-ONLY: no S3/S4/S5 default changed; nothing written to out/map, out/verify,
  out/submission, or any judged CSV. All output → out/ab/.
- S5 blind verify stays Claude-family by design (cross-family verification),
  regardless of outcome.
- API key is env-only (`AB3_API_KEY`); never written to any file, log, or report.
- No cross-provider output parity claimed — identical citations + disclosed
  deltas is the only admissible claim shape.
"""
    AB_DIR.mkdir(parents=True, exist_ok=True)
    (AB_DIR / "ab_deepseek_preregistration.md").write_text(md, encoding="utf-8")
    print(f"[preregister] wrote out/ab/ab_deepseek_preregistration.md "
          f"(branch={branch.get('branch', '?')}, inputs "
          f"{'OK' if ok else 'MISSING: ' + ','.join(missing)})")


if __name__ == "__main__":
    import sys
    verb = sys.argv[1] if len(sys.argv) > 1 else "validate"
    if verb == "validate":
        validate()
    elif verb == "preregister":
        write_preregistration(sys.argv[2] if len(sys.argv) > 2 else "unset")
    elif verb == "ab3":
        run_ab3()
    elif verb == "ab4":
        run_ab4()
    else:
        print(f"unknown verb: {verb}")
