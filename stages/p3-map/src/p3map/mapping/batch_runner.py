"""S4 batch lane — Anthropic Message Batches for the AU/MY bulk mapping run.

Identical prompt, schema, model, and output row shape to the live runner
(runner.py); only the transport differs: Message Batches = 50% pricing on
every token class, <=24h completion SLA, prompt-cache hits best-effort.
The judged demo path stays LIVE (decision #8); S5 verify stays live.

Verbs:
  python -m src.p3map.mapping.batch_runner dryrun AU  # build only: counts/size/$ est
  python -m src.p3map.mapping.batch_runner submit AU  # build + submit batches
  python -m src.p3map.mapping.batch_runner poll AU    # one status snapshot
  python -m src.p3map.mapping.batch_runner watch AU   # poll 5-min, fetch when ended
  python -m src.p3map.mapping.batch_runner fetch AU   # ingest -> verdicts_<ECON>.jsonl

State: out/map/batches_<ECON>.json (batch ids + custom_id->provision_id
manifest; custom_ids must match ^[a-zA-Z0-9_-]{1,64}$ so provision ids like
"sg-pdpa2012-001#s26.1" cannot ride directly).

Failed / unvalidated results land as error rows in verdicts_<ECON>.jsonl;
the live runner's resume (`python -m src.p3map.mapping.runner <ECON>`)
retries exactly those rows with its 8192-token fallback.
`src.p3map.preflight` must PASS before submit (audit item 1b).
"""
from __future__ import annotations

import json
import sys
import time

from config.llm.base import PRICES, Usage, usd
from config.llm.factory import LLMConfigError, get_llm
from config.settings import SETTINGS
from src.p3map.mapping.anchor import anchor
from src.p3map.mapping.prompt import build_system_prefix, build_user_turn
from src.p3map.mapping.runner import _load_pairs
from src.p3map.mapping.schema import (MAPPING_SCHEMA, MappingVerdict,
                                      coerce_verdict)

BATCH_DISCOUNT = 0.5          # Message Batches price = 50% of live, all classes
# This lane is Anthropic-only by decision M3: no other provider is wired for it, and every price
# here is an Anthropic price halved. The guard exists because the failure is silent and expensive
# in the wrong direction: with LLM_PROVIDER=ollama an operator believes they are running the free
# local engine, while these three verbs would submit to Anthropic and bill for it.
BATCH_PROVIDER = "anthropic"
MAX_BATCH_BYTES = 100 * 2**20  # stay far below the 256MB request-payload cap
MAX_BATCH_REQS = 6000          # cap well below the 100k/batch limit
POLL_SECONDS = 300

ENDED = {"ended"}  # processing_status: in_progress | canceling | ended


def _require_batch_provider(verb: str) -> None:
    from config.llm import engines
    declared = engines.selected()
    if declared is not None and not declared.batch_lane:
        raise LLMConfigError(
            f"engine {declared.id} ({declared.label}) does not declare the batch lane, and "
            f"`{verb}` would submit to Anthropic regardless. Use the live path: "
            f"python -m src.p3map.mapping.runner <ECON>")
    provider = (declared.provider if declared else (SETTINGS.llm_provider or "")).strip().lower()
    if provider != BATCH_PROVIDER:
        raise LLMConfigError(
            f"the batch lane is {BATCH_PROVIDER}-only (decision M3), but LLM_PROVIDER is "
            f"{provider!r}. `{verb}` would submit to Anthropic and bill for it while the "
            f"engine says otherwise. Use the live path for another engine: "
            f"python -m src.p3map.mapping.runner <ECON>"
        )


def _state_path(economy: str):
    return SETTINGS.out_dir / "map" / f"batches_{economy}.json"


def _load_state(economy: str) -> dict:
    p = _state_path(economy)
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {"economy": economy, "model": SETTINGS.llm_model, "batches": []}


def _save_state(state: dict) -> None:
    p = _state_path(state["economy"])
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(state, indent=1, ensure_ascii=False), encoding="utf-8")


def _done_pids(economy: str) -> set[str]:
    """provision_ids already holding a NON-error row in the verdicts file."""
    done: set[str] = set()
    vp = SETTINGS.out_dir / "map" / f"verdicts_{economy}.jsonl"
    if vp.exists():
        with vp.open(encoding="utf-8") as f:
            for line in f:
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if "error" not in r:
                    done.add(r["provision_id"])
    return done


def _load_records(pids: set[str]) -> dict[str, dict]:
    recs: dict[str, dict] = {}
    with (SETTINGS.index_dir / "prefilter_corpus.jsonl").open(encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if r["provision_id"] in pids:
                recs[r["provision_id"]] = r
    return recs


def _build_requests(economy: str):
    """-> (chunks, manifest, stats): chunks = list of request-lists sized under
    the payload caps; manifest maps custom_id -> provision_id."""
    cands = _load_pairs(economy)
    done = _done_pids(economy)
    todo = sorted(pid for pid in cands if pid not in done)
    recs = _load_records(set(todo))

    system = build_system_prefix()
    sys_block = [{"type": "text", "text": system,
                  "cache_control": {"type": "ephemeral", "ttl": "1h"}}]
    tools = [{"name": "emit_verdict",
              "description": "Emit the structured verdict.",
              "input_schema": MAPPING_SCHEMA}]

    manifest: dict[str, str] = {}
    chunks: list[list[dict]] = [[]]
    chunk_bytes = 0
    n_pairs, missing = 0, 0
    for i, pid in enumerate(todo):
        rec = recs.get(pid)
        if rec is None:      # cannot happen post-preflight; never silently drop
            missing += 1
            continue
        candidates = sorted(cands[pid])
        n_pairs += len(candidates)
        cid = f"r{i:06d}"
        manifest[cid] = pid
        req = {
            "custom_id": cid,
            "params": {
                "model": SETTINGS.llm_model,
                "max_tokens": 2048 + 512 * len(candidates),
                "system": sys_block,
                "messages": [{"role": "user",
                              "content": build_user_turn(rec, candidates)}],
                "tools": tools,
                "tool_choice": {"type": "tool", "name": "emit_verdict"},
            },
        }
        size = len(json.dumps(req, ensure_ascii=False).encode("utf-8"))
        if chunks[-1] and (chunk_bytes + size > MAX_BATCH_BYTES
                           or len(chunks[-1]) >= MAX_BATCH_REQS):
            chunks.append([])
            chunk_bytes = 0
        chunks[-1].append(req)
        chunk_bytes += size

    if not chunks[-1]:
        chunks.pop()
    stats = {"provisions": len(manifest), "pairs": n_pairs,
             "already_done": len(done & set(cands)), "record_missing": missing,
             "batches": len(chunks)}
    return chunks, manifest, stats


def _estimate(stats: dict) -> str:
    # measured SG live rate: $0.0163/provision mapped; batch = 50%
    est = stats["provisions"] * 0.0163 * BATCH_DISCOUNT
    return (f"~${est:.0f} at the measured SG rate x batch discount "
            f"(cache best-effort in batches; +15% margin => ~${est * 1.15:.0f})")


def dryrun(economy: str) -> None:
    provider = (SETTINGS.llm_provider or "").strip().lower()
    if provider != BATCH_PROVIDER:
        print(f"[batch:{economy}] NOTE: LLM_PROVIDER={provider!r}; this estimate is an Anthropic "
              f"batch estimate, and submit/poll/fetch will refuse until the engine says "
              f"{BATCH_PROVIDER!r}")
    chunks, _, stats = _build_requests(economy)
    total_mb = sum(len(json.dumps(r, ensure_ascii=False).encode("utf-8"))
                   for c in chunks for r in c) / 2**20
    print(f"[batch:{economy}] DRYRUN {json.dumps(stats)} "
          f"payload {total_mb:.0f}MB, est {_estimate(stats)}")


def submit(economy: str) -> None:
    _require_batch_provider("submit")
    import anthropic
    chunks, manifest, stats = _build_requests(economy)
    if stats["record_missing"]:
        print(f"[batch:{economy}] ABORT: {stats['record_missing']} provision ids "
              "have no corpus record — run preflight and regenerate pairs")
        sys.exit(1)
    if not chunks:
        print(f"[batch:{economy}] nothing to submit (all provisions done)")
        return
    state = _load_state(economy)
    inflight = [b["batch_id"] for b in state["batches"] if not b["ingested"]]
    if inflight:  # done-set only sees the verdicts file, not queued batches
        print(f"[batch:{economy}] ABORT: un-ingested batches exist ({inflight}); "
              "watch/fetch them first or resubmission will duplicate provisions")
        sys.exit(1)
    client = anthropic.Anthropic()
    print(f"[batch:{economy}] submitting {stats['batches']} batch(es): "
          f"{json.dumps(stats)}; est {_estimate(stats)}", flush=True)
    for i, chunk in enumerate(chunks):
        mb = client.messages.batches.create(requests=chunk)
        state["batches"].append({
            "batch_id": mb.id, "n_requests": len(chunk),
            "submitted_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "status": mb.processing_status, "ingested": False,
            "manifest": {r["custom_id"]: manifest[r["custom_id"]] for r in chunk},
        })
        _save_state(state)   # save after EACH create: a later failure loses nothing
        print(f"[batch:{economy}] {i + 1}/{len(chunks)} -> {mb.id} "
              f"({len(chunk)} requests)", flush=True)
    print(f"[batch:{economy}] submitted; next: "
          f"python -m src.p3map.mapping.batch_runner watch {economy}")


def poll(economy: str, quiet: bool = False) -> bool:
    """True when every submitted batch has ended."""
    _require_batch_provider("poll")
    import anthropic
    state = _load_state(economy)
    if not state["batches"]:
        print(f"[batch:{economy}] no batches submitted")
        return False
    client = anthropic.Anthropic()
    all_ended = True
    for b in state["batches"]:
        mb = client.messages.batches.retrieve(b["batch_id"])
        b["status"] = mb.processing_status
        c = mb.request_counts
        line = (f"[batch:{economy}] {b['batch_id']} {mb.processing_status} "
                f"(ok {c.succeeded} / err {c.errored} / exp {c.expired} / "
                f"cancel {c.canceled} / pending {c.processing})")
        if not quiet:
            print(line, flush=True)
        if mb.processing_status not in ENDED:
            all_ended = False
    _save_state(state)
    return all_ended


def fetch(economy: str) -> None:
    """Ingest ended batches into verdicts_<ECON>.jsonl (idempotent)."""
    _require_batch_provider("fetch")
    import anthropic
    state = _load_state(economy)
    client = anthropic.Anthropic()
    out_path = SETTINGS.out_dir / "map" / f"verdicts_{economy}.jsonl"
    done = _done_pids(economy)

    pending_pids: set[str] = set()
    for b in state["batches"]:
        if not b["ingested"]:
            pending_pids.update(b["manifest"].values())
    recs = _load_records(pending_pids - done)

    # A retry has to rebuild the request, which needs the candidate indicators as well as the
    # record -- submit() has always loaded both, fetch() only ever loaded the records. The live
    # client is built on first use, so a clean fetch creates none and calls nothing.
    cands = _load_pairs(economy)
    system = build_system_prefix()
    live: list = []                      # one-slot lazy holder for the retry client

    def _live_client():
        if not live:
            live.append(get_llm(SETTINGS, role="mapper"))
            print(f"[batch:{economy}] parse failures present -> retrying live on "
                  f"{live[0].model} (full price, not the batch 50%)", flush=True)
        return live[0]

    usage = Usage()
    counters = {"rows": 0, "applies": 0, "errors": 0, "ungrounded": 0, "dup": 0,
                "retried": 0, "retry_recovered": 0}
    with out_path.open("a", encoding="utf-8") as fout:
        for b in state["batches"]:
            if b["ingested"]:
                continue
            batch_usage = Usage()
            mb = client.messages.batches.retrieve(b["batch_id"])
            if mb.processing_status not in ENDED:
                print(f"[batch:{economy}] {b['batch_id']} still "
                      f"{mb.processing_status}; skipping", flush=True)
                continue
            for res in client.messages.batches.results(b["batch_id"]):
                pid = b["manifest"].get(res.custom_id)
                if pid is None or pid in done:
                    counters["dup"] += pid is not None
                    continue
                row = _row_from_result(economy, pid, res, recs, batch_usage)
                # The batch result is fixed once fetched, so "retry" means re-sampling live. Skip
                # record-missing: that is our own bookkeeping, not a bad sample, and a retry would
                # fail identically because there is no record to build a prompt from.
                if "error" in row and row["error"] != "record-missing" and pid in recs:
                    counters["retried"] += 1
                    row = _retry_live(economy, pid, recs[pid], sorted(cands.get(pid) or []),
                                      system, _live_client(), row["error"])
                    counters["retry_recovered"] += "error" not in row
                fout.write(json.dumps(row, ensure_ascii=False) + "\n")
                done.add(pid)
                counters["rows"] += 1
                if "error" in row:
                    counters["errors"] += 1
                else:
                    counters["applies"] += sum(1 for x in row["verdicts"] if x["applies"])
                    counters["ungrounded"] += sum(1 for x in row["verdicts"]
                                                  if x["applies"] and not x["quote_grounded_ws"])
            b["ingested"] = True
            # Cost is recorded PER BATCH, not accumulated into the report. Re-ingesting a batch --
            # which is free, because Message Batches results are retained for 29 days and retrieval
            # is not billed -- must not bill it twice. Measured 2026-09-27: it did, and the report
            # claimed $51.72 against $38.81 actually billed.
            # FIRST ingest wins, and a later one never changes it. The first fetch of an ended
            # batch reads every result, so it measures the whole batch; a re-ingest reads only the
            # rows still missing, so its usage is a fraction. Overwriting was the bug that made a
            # re-parse of 98 rows report $0.67 against the $21.86 actually billed. Clear the field
            # by hand if a batch genuinely needs re-pricing.
            measured = round(usd(SETTINGS.llm_model, batch_usage) * BATCH_DISCOUNT, 4)
            if b.get("cost_usd") is None:
                b["cost_usd"] = measured
                b["cost_source"] = "first ingest of this batch, all results"
            else:
                b["last_reparse_usd"] = measured      # recorded, never billed
            b["ingested_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
            _save_state(state)
            print(f"[batch:{economy}] ingested {b['batch_id']} "
                  f"(${b['cost_usd']:.2f} billed for this batch"
                  + (f", re-parse {measured:.2f} not billed" if b.get("last_reparse_usd")
                     else "") + ")", flush=True)

    # The report states what the verdicts file HOLDS, not what this invocation happened to write.
    # It used to add each fetch's counters to the previous report, which made "provisions" exceed
    # the number of provisions that exist (3,466 against 2,617) once a batch was re-ingested.
    state_counts = _counts_from_verdicts(economy)
    batch_cost = sum(float(b.get("cost_usd") or 0.0) for b in state["batches"])
    # Live retries are billed at FULL price and are NOT part of any batch's cost, so they are
    # accumulated separately and cumulatively across fetches -- unlike a re-ingest, a retry is a
    # real new call every time it happens, so first-ingest-wins must not apply to it. Priced once
    # here from the client's own accumulated usage, never per retry.
    if live:
        state["retry_live_usd"] = round(
            float(state.get("retry_live_usd") or 0.0) + usd(live[0].model, live[0].usage), 4)
        state["retry_live_calls"] = int(state.get("retry_live_calls") or 0) + counters["retried"]
        _save_state(state)
    retry_cost = float(state.get("retry_live_usd") or 0.0)
    cost = batch_cost + retry_cost
    report = {"economy": economy, **state_counts, "cost_usd": round(cost, 2),
              "cost_usd_batch_lane": round(batch_cost, 2),
              "retry_live_usd": round(retry_cost, 4),
              "retry_live_calls": int(state.get("retry_live_calls") or 0)}
    # cumulative merge (audit item 2): never clobber prior tallies
    rp = SETTINGS.out_dir / "map" / f"map_report_{economy}.json"
    report["cost_note"] = ("cost_usd is the TOTAL billed for this economy = cost_usd_batch_lane + "
                           "retry_live_usd. Batch rows are priced at the Message Batches 50% "
                           "discount from result usage, summed once per batch id; a re-ingest of a "
                           "retained batch is free and does not add to it. Live retries of rows "
                           "whose batch result would not parse are priced at FULL rate and "
                           "accumulate across fetches, because each retry is a new billed call")
    report["batches"] = [{"batch_id": b["batch_id"], "n_requests": b["n_requests"],
                          "cost_usd": b.get("cost_usd")} for b in state["batches"]]
    rp.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"[batch:{economy}] fetch done: {json.dumps(counters)} "
          f"this fetch ${usd(SETTINGS.llm_model, usage) * BATCH_DISCOUNT:.2f}, "
          f"billed total for {economy} ${cost:.2f}"
          + (f" (batch ${batch_cost:.2f} + live retries ${retry_cost:.2f})" if retry_cost else "")
          + "", flush=True)
    if counters["retried"]:
        print(f"[batch:{economy}] retried {counters['retried']} unparseable results live, "
              f"recovered {counters['retry_recovered']}", flush=True)
    if counters["errors"]:
        print(f"[batch:{economy}] {counters['errors']} error rows remain after one live retry "
              f"each; they are on the QA Errors sheet with their provision text", flush=True)


def _counts_from_verdicts(economy: str) -> dict:
    """What verdicts_<ECON>.jsonl actually holds: the single source of truth for the report."""
    vp = SETTINGS.out_dir / "map" / f"verdicts_{economy}.jsonl"
    provisions: set[str] = set()
    fires = ungrounded = errors = 0
    if vp.exists():
        with vp.open(encoding="utf-8") as f:
            for line in f:
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    continue
                provisions.add(r.get("provision_id"))
                if "error" in r:
                    errors += 1
                    continue
                for v in r.get("verdicts") or []:
                    if v.get("applies"):
                        fires += 1
                        if not v.get("quote_grounded_ws"):
                            ungrounded += 1
    return {"provisions": len(provisions), "verdict_fires": fires,
            "ungrounded_fires": ungrounded, "errors": errors}


def _row_from_result(economy: str, pid: str, res, recs: dict, usage: Usage) -> dict:
    if res.result.type != "succeeded":
        err = getattr(getattr(res.result, "error", None), "error", None)
        detail = getattr(err, "message", "") or res.result.type
        return {"provision_id": pid, "economy": economy,
                "error": f"batch_{res.result.type}: {str(detail)[:150]}"}
    msg = res.result.message
    u = msg.usage
    usage.add(Usage(
        input_tokens=u.input_tokens, output_tokens=u.output_tokens,
        cache_read_tokens=getattr(u, "cache_read_input_tokens", 0) or 0,
        cache_write_tokens=getattr(u, "cache_creation_input_tokens", 0) or 0,
        calls=1))
    rec = recs.get(pid)
    if rec is None:
        return {"provision_id": pid, "economy": economy, "error": "record-missing"}
    try:
        raw = next(blk.input for blk in msg.content if blk.type == "tool_use")
        v = MappingVerdict.model_validate(coerce_verdict(raw))
    except (StopIteration, Exception) as e:
        return {"provision_id": pid, "economy": economy,
                "error": f"{type(e).__name__}: {str(e)[:150]}"}
    return _row_from_verdict(economy, pid, rec, v, SETTINGS.llm_model)


def _row_from_verdict(economy: str, pid: str, rec: dict, v: MappingVerdict, model: str) -> dict:
    """Shape a validated verdict into a verdicts row. Shared by the batch result path and the live
    retry below, so a retried provision is indistinguishable in the data from a first-try one."""
    verdicts = []
    for x in v.verdicts:
        # identical to the live runner: M10's span cut, so the two lanes file the same bytes
        a = anchor(x.verbatim_quote, rec["text"])
        row = {**x.model_dump(), "quote_grounded_ws": a.grounded, "quote_anchor": a.how}
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
        "candidates": sorted({x.indicator for x in v.verdicts}),
        "core_legal_question_answer": v.core_legal_question_answer,
        "who_is_regulated": v.who_is_regulated,
        "conditions_and_exceptions": v.conditions_and_exceptions,
        # identical to the live runner: the gap is recorded, the provision is kept
        "narrative_gaps": v.narrative_gaps,
        "trap_checks": v.trap_checks.model_dump(),
        "verdicts": verdicts,
        "model": model,
    }


def _retry_live(economy: str, pid: str, rec: dict, candidates: list[str], system: str,
                client, first_error: str) -> dict:
    """Re-sample ONE provision live, because a batch result cannot be re-sampled in place.

    Why this exists. Measured 29 September: 225 of 14,456 S4 calls produced no usable verdict, and
    124 of those were a degenerate sample -- the model returned the SHAPE of a tool call, its input
    literally `{'parameter name': 'value'}` or `{'parameter': '...'}`. It correlates with nothing:
    the failures' provision text has a median length of 814 characters against 821 for the
    successes, and the 124 are spread over 87 distinct documents with a worst case of 5 in 326. It
    is a random ~0.86% rate, and re-sampling clears it.

    What turned a 0.86% sampling glitch into 1.6% permanent data loss was an asymmetry: the LIVE
    runner has retried once since Round 1, and this lane parsed once and wrote an error row, then
    PRINTED `-> retry live: python -m ...` as advice for a human to notice. Nobody noticed. The
    batch lane carried half the run, so essentially all 225 came from here. A live failure needs
    two consecutive bad samples, about one row in 14,000.

    Billed at FULL price, not the Message Batches 50% -- this is an ordinary live call. The client
    accumulates its own usage across calls, so the caller prices it ONCE after the loop rather than
    per retry; adding it here would count every earlier retry again on each new one.
    """
    try:
        raw = client.complete(build_user_turn(rec, candidates), MAPPING_SCHEMA,
                              system=system, max_tokens=8192, cache_system=True)
        v = MappingVerdict.model_validate(coerce_verdict(raw))
    except Exception as e:                                          # noqa: BLE001
        # Both attempts failed. Say so, and keep both reasons: a provision that fails twice for the
        # same reason is a different animal from one that fails two different ways, and the error
        # row is the only place that distinction survives.
        return {"provision_id": pid, "economy": economy,
                "error": (f"batch+retry both failed | batch: {first_error[:110]} "
                          f"| retry: {type(e).__name__}: {str(e)[:110]}")}
    row = _row_from_verdict(economy, pid, rec, v, client.model)
    row["retried_live"] = True
    row["batch_error"] = first_error[:150]
    return row


def watch(economy: str) -> None:
    t0 = time.time()
    while True:
        if poll(economy):
            print(f"[batch:{economy}] all batches ended after "
                  f"{(time.time() - t0) / 60:.0f} min; fetching", flush=True)
            fetch(economy)
            return
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    import argparse

    VERBS = {"dryrun": dryrun, "submit": submit, "poll": poll, "watch": watch, "fetch": fetch}
    ap = argparse.ArgumentParser(
        description="S4 via Anthropic Message Batches, at 50% of live. Anthropic-only by decision "
                    "M3; the lane refuses to run when the resolved engine is something else, "
                    "rather than billing Anthropic while the operator believes the run is local.")
    ap.add_argument("verb", nargs="?", default="poll", choices=sorted(VERBS),
                    help="dryrun prices it; submit sends; poll reports; watch waits; fetch ingests "
                         "and retries live any result that will not parse")
    ap.add_argument("economy", nargs="?", default="AU")
    a = ap.parse_args()
    assert SETTINGS.llm_model in PRICES, f"no price card for {SETTINGS.llm_model}"
    VERBS[a.verb](a.economy)
