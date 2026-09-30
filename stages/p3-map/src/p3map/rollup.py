"""S6 — economy-level score rollup (framework §2.4).

Provision-level indicators (6.1-6.4, 7.3, 7.4, 7.5): deterministic
max-rollup over verified fires' final score hints, with the methodology
clauses applied:
- escalation clause (6.1/6.2 ONLY): >=2 half-point measures -> 1
- 6.4 asymmetry: personal-data conditions score 1 even if sectoral
  (already encoded in the scoring tree; rollup just takes max)
- government-data-only fires never reach here (trap-filtered at S4).

Economy-level indicators (7.1, 7.2 — INVERTED polarity): one dedicated
LLM call per (economy, indicator) that answers the framework-existence
question from the collected evidence rows (needs API credits; stub result
'pending' when the call fails).

Output: out/rollup/economy_scores_<ECON>.json — score + the evidence rows
behind it. Scores live in records.json (`score_value`), never a 14th CSV column.
"""
from __future__ import annotations

import json
from collections import defaultdict

from config import manifest
from config.instrument import ESCALATION_IDS, from_artifact, load as load_instrument
from config.llm.base import usd
from config.settings import INDICATORS, SETTINGS

# Which indicators allow a 0.5 is the codebook's business, not this file's: it is read from each
# block's `scoring.values` via the instrument loader. Derived that way it reproduces the set this
# module used to hard-code — 6.3, 7.3 and 7.5 — against both instrument vintages, and it keeps
# working if the codebook changes a scoring tree.
ESCALATION_INDICATORS = ESCALATION_IDS  # a Round 1 design choice; see config/instrument.py

FRAMEWORK_PROMPT = """Evidence rows collected for {econ} / {ind} (each: law, section, coverage, quote):
{evidence}
{rejected}
QUESTION ({ind}, INVERTED polarity): does {econ} LACK a {what}?
Score 1 = no framework exists; 0.5 = sectoral/partial only; 0 = comprehensive
framework exists. Judge ONLY from the material above.

controlling_law must NAME the instrument your score rests on. If the material does not let you name
one, return controlling_law empty -- an absence of retrieved evidence is not evidence of absence, and
the cell will be left unscored rather than guessed."""
WHAT = {"7.1": "comprehensive legal framework for personal data protection",
        "7.2": "dedicated legal framework for cybersecurity"}
SCHEMA = {"type": "object",
          "properties": {"score": {"type": "string", "enum": ["1", "0.5", "0"]},
                         "controlling_law": {"type": "string"},
                         "reason": {"type": "string", "maxLength": 400}},
          "required": ["score", "controlling_law", "reason"]}


def run_rollup(economy: str) -> dict:
    # 2026-07-16 audit item 3: read verification outcomes DIRECTLY (the
    # discovery file is a downstream artifact that raced this stage once);
    # doc/law/coverage joined from the map verdicts.
    mapmeta: dict[tuple[str, str], dict] = {}
    with (SETTINGS.out_dir / "map" / f"verdicts_{economy}.jsonl").open(encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            if "error" in row:
                continue
            for v in row["verdicts"]:
                mapmeta[(row["provision_id"], from_artifact(v["indicator"]))] = {
                    "doc_id": row["doc_id"], "law_name": row.get("law_name"),
                    "article_section": row.get("article_section"),
                    "coverage": v.get("coverage")}

    fires_by_ind: dict[str, list[dict]] = defaultdict(list)
    # An economy-level cell gets the REJECTED candidates too, with the reviewers' own reasons.
    # A rejection there is a finding, not silence: on Lao 7.1 the reviewers concluded that the law
    # governs "electronic data ... rather than personal data with access/rectification/erasure
    # rights", which argues the framework is not comprehensive -- and the cell still scored nothing,
    # because zero upheld fires meant zero evidence. Decision of 29 September: a reasoned rejection
    # may inform an economy-level score, and _framework_score() must still name a controlling law or
    # return pending, so it can conclude "a law exists but is not comprehensive" from evidence and
    # can never conclude "no law exists" from an absence of retrieval.
    rejected_by_ind: dict[str, list[dict]] = defaultdict(list)
    with (SETTINGS.out_dir / "verify" / f"verified_{economy}.jsonl").open(encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            ind = from_artifact(r["indicator"])
            if not r.get("final_applies"):
                mm = mapmeta.get((r["provision_id"], ind), {})
                why = ((r.get("verifier") or {}).get("reason")
                       or (r.get("escalation") or {}).get("reason") or "")
                rejected_by_ind[ind].append({
                    "law_name": mm.get("law_name", ""),
                    "article_section": mm.get("article_section", ""),
                    "reason": str(why)[:400]})
                continue  # never evidence for a provision-level cell
            mm = mapmeta.get((r["provision_id"], ind), {})
            fires_by_ind[ind].append({
                "provision_id": r["provision_id"],
                "indicator": ind,
                "score_hint": r.get("final_score_hint"),
                "verification": r["verifier_verdict"],
                "doc_id": mm.get("doc_id", ""),
                "law_name": mm.get("law_name", ""),
                "article_section": mm.get("article_section", ""),
                "coverage": mm.get("coverage", "?"),
            })

    ins = load_instrument()
    # The economy-level call is the only paid work in this stage, and Round 1 recorded neither its
    # cost nor its model. One client for the run, built only if an economy-level indicator exists,
    # and a failure to build it leaves those cells "pending" exactly as a failed call did — the
    # provision-level scores below do not depend on a model at all and must still be computed.
    client, client_error = None, None
    if any(ins.level(i) == "economy" for i in INDICATORS):
        try:
            from config.llm.factory import get_llm
            client = get_llm(SETTINGS, role="mapper")
        except Exception as e:  # noqa: BLE001 — recorded, not raised
            client_error = f"{type(e).__name__}: {e}"
            print(f"[rollup:{economy}] economy-level engine unavailable: {client_error}",
                  flush=True)

    scores: dict[str, dict] = {}
    for ind in INDICATORS:
        fires = fires_by_ind.get(ind, [])
        if ins.level(ind) == "economy":
            scores[ind] = _framework_score(economy, ind, fires, client, client_error,
                                           rejected=rejected_by_ind.get(ind, []))
            continue
        verified = [t for t in fires
                    if t["verification"] in ("agree", "tiebreak_upheld")]
        pending = [t for t in fires
                   if t["verification"] not in ("agree", "tiebreak_upheld")]
        vals, val_laws = [], defaultdict(list)
        for t in verified:
            try:
                x = float(t["score_hint"])
            except (ValueError, TypeError):
                continue
            vals.append(x)
            val_laws[x].append(t["doc_id"])
        if not vals:
            scores[ind] = {"score": 0.0 if not pending else "provisional-0",
                           "basis": "no VERIFIED qualifying measure"
                                    + (f" ({len(pending)} fires pending verification)"
                                       if pending else ""),
                           "evidence_rows": 0, "pending": len(pending)}
            continue
        score = max(vals)
        basis = f"max over {len(vals)} verified fires"
        # escalation clause counts distinct MEASURES (laws), verified only
        if (ind in ESCALATION_INDICATORS and score == 0.5
                and len(set(val_laws[0.5])) >= 2):
            score, basis = 1.0, (f"escalation clause: {len(set(val_laws[0.5]))} "
                                 "distinct verified half-point measures")
        if ins.is_binary(ind) and score == 0.5:
            score, basis = 0.0, "binary indicator: lone 0.5 does not qualify (flagged)"
        scores[ind] = {"score": score, "basis": basis,
                       "evidence_rows": len(vals), "pending": len(pending)}

    cost = usd(client.model, client.usage) if client is not None else 0.0
    out_dir = SETTINGS.out_dir / "rollup"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"economy_scores_{economy}.json").write_text(
        json.dumps({"economy": economy, "scores": scores,
                    "economy_level_model": client.model if client else None,
                    "cost_usd": round(cost, 4)}, indent=2,
                   ensure_ascii=False), encoding="utf-8")
    manifest.record("rollup", economy=economy,
                    model=client.model if client else None,
                    economy_level_cells=sum(1 for i in INDICATORS
                                            if ins.level(i) == "economy"),
                    pending=sum(1 for v in scores.values() if v["score"] == "pending"),
                    cost_usd=round(cost, 4))
    print(f"[rollup:{economy}] " + json.dumps(
        {k: v["score"] for k, v in scores.items()}) + f" (${cost:.4f})")
    return scores


def _framework_score(economy: str, ind: str, fires: list[dict],
                     client=None, client_error: str | None = None,
                     rejected: list[dict] | None = None) -> dict:
    # fires arriving here are verified-kept only (audit item 3)
    ev_lines = []
    for t in fires[:40]:
        ev_lines.append(f"- {t['law_name']} {t['article_section']} "
                        f"[{t.get('coverage','?')}]")
    rejected = rejected or []
    rej_block = ""
    if rejected:
        rej_lines = [f"- {r['law_name']} {r['article_section']}: {r['reason']}"
                     for r in rejected[:20]]
        rej_block = (
            "\nCandidates a blind reviewer REJECTED for this cell, with its reasons. A rejection"
            " can still tell you what the law is and is not -- for instance that an instrument"
            " exists but is not comprehensive:\n"
            + "\n".join(rej_lines) + "\n")
    if not ev_lines and not rejected:
        return {"score": "pending", "basis": "no evidence rows collected and none rejected",
                "evidence_rows": 0, "rejected_rows": 0}
    if client is None:
        return {"score": "pending",
                "basis": f"economy-level engine unavailable: {client_error or 'no client'}",
                "evidence_rows": len(fires)}
    try:
        v = client.complete(
            FRAMEWORK_PROMPT.format(econ=economy, ind=ind,
                                    evidence="\n".join(ev_lines) or "(none upheld)",
                                    rejected=rej_block,
                                    what=WHAT[ind]),
            SCHEMA, max_tokens=400)
        # Same shape problem the mapper had, and the same remedy: a schema-forced reply can arrive
        # inside an envelope, or with a descriptive key missing. Measured 2026-09-27, Lao PDR 7.2
        # failed with a bare KeyError and the cell came out "pending" with 36 verified evidence rows
        # sitting unused; the identical call then succeeded. A transient shape must not cost a score.
        if isinstance(v, dict) and len(v) == 1:
            only = next(iter(v.values()))
            if isinstance(only, dict) and "score" in only:
                v = only
        if "score" not in v:
            return {"score": "pending",
                    "basis": f"economy-level reply carried no score; keys were {sorted(v)}",
                    "evidence_rows": len(fires)}
        # score cannot be defaulted -- it is the answer. The two descriptive fields can.
        law = str(v.get("controlling_law") or "").strip()
        if not law:
            # The scorer was asked to name the instrument its score rests on and could not. That is
            # the guard against scoring an absence from a retrieval gap.
            return {"score": "pending",
                    "basis": ("economy-level call named no controlling law, so the cell is left "
                              "unscored rather than inferred from absent evidence: "
                              + str(v.get("reason") or "")[:240]),
                    "evidence_rows": len(fires), "rejected_rows": len(rejected)}
        return {"score": float(v["score"]),
                "basis": v.get("reason") or "no reason returned by the economy-level call",
                "controlling_law": law,
                "evidence_rows": len(fires), "rejected_rows": len(rejected)}
    except Exception as e:
        return {"score": "pending",
                "basis": f"economy-level call failed: {type(e).__name__}",
                "evidence_rows": len(fires)}


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="S6 rollup: the economy-level score per indicator, from verified fires. Leaves a cell `pending` rather than inferring one from absent evidence.")
    ap.add_argument("economy", nargs="?", default="SG")
    a = ap.parse_args()
    run_rollup(a.economy)
