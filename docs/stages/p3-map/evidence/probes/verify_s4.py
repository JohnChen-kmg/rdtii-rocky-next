"""Verification gate for S4 mapping, run before chain.py touches S5-S10.

`chain.py` has no error handling, so a bad S4 propagates silently through five more stages. These
are the checks PLAN.md's verification table names for S4, plus the two that tonight's measurements
added. Every threshold is a number Round 1 measured, not a guess, and each is printed with its
basis so a failure can be judged rather than merely noticed.

Exit code 0 = safe to chain. 1 = something needs a decision first.

Run from the stage root with the run's environment set, INSTRUMENT_DIR pointed at the workshop:

    OUT_DIR=...\run_2026-09-27\out INDEX_DIR=...\run_2026-09-27\index \
    INSTRUMENT_DIR=...\rdtii-finale-0-instrument\instrument\output \
    python -X utf8 evidence\probes\verify_s4.py
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter, defaultdict

# The economies this run covers. ECONOMIES scopes a run, so the gate must follow it: hard-coding
# three made the gate refuse a Timor-Leste-only run for "no report" on economies it never touched.
ECON = [x.strip().upper() for x in os.environ.get("ECONOMIES", "").split(",") if x.strip()]     or ["CN", "LA", "TL"]
# Round 1's measured bands. A figure outside these is not automatically wrong; it is a thing to
# explain before five more stages are built on it.
FIRE_RATE_BAND = (0.10, 0.45)     # AU 0.196, MY 0.295 fires per mapped provision
# Ungrounded fires are a QUALITY SIGNAL, not a gate, and this threshold was wrong when first
# written (0.005). Two reasons it is now 0.05: submission.py's unfilable_reason() drops any fire
# whose quote is not the source's own bytes, so an ungrounded fire cannot reach the CSV; and Round 1
# shipped at 1.8% (AU, 50 of 2,827 fires). A rate above 5% would mean the anchoring itself broke,
# which is worth stopping for. Below that it is reported and carried.
UNGROUNDED_MAX = 0.05


def main() -> int:
    out = os.environ.get("OUT_DIR")
    if not out:
        print("OUT_DIR is not set; refusing to guess which run to verify")
        return 1
    ok = True

    print("=" * 78)
    print("S4 verification")
    print("=" * 78)

    # ---- 1. reports exist, and what they say
    print("\n1. per-economy reports")
    print(f"   {'econ':5s} {'provisions':>11s} {'fires':>8s} {'fires/prov':>11s} "
          f"{'ungrounded':>11s} {'cost $':>8s}  verdict")
    totals = Counter()
    for e in ECON:
        p = os.path.join(out, "map", f"map_report_{e}.json")
        if not os.path.exists(p):
            print(f"   {e:5s} {'-- no report; S4 has not finished for this economy':<50s}")
            ok = False
            continue
        d = json.load(open(p, encoding="utf-8"))
        prov = int(d.get("provisions") or 0)
        fires = int(d.get("verdict_fires") or 0)
        ung = int(d.get("ungrounded_fires") or 0)
        cost = float(d.get("cost_usd") or 0.0)
        rate = fires / prov if prov else 0.0
        totals["provisions"] += prov; totals["fires"] += fires
        totals["ungrounded"] += ung
        flags = []
        if not (FIRE_RATE_BAND[0] <= rate <= FIRE_RATE_BAND[1]):
            flags.append(f"fire rate outside Round 1's {FIRE_RATE_BAND}")
            ok = False
        if prov and fires:
            rate_u = ung / fires
            if rate_u > UNGROUNDED_MAX:
                flags.append(f"{ung} ungrounded fires ({rate_u:.1%}) - ANCHORING BROKEN")
                ok = False
            elif ung:
                flags.append(f"{ung} ungrounded ({rate_u:.1%}), dropped at emit - ok")
        print(f"   {e:5s} {prov:>11,d} {fires:>8,d} {rate:>11.3f} {ung:>11,d} {cost:>8.2f}  "
              f"{'; '.join(flags) if flags else 'ok'}")
    if totals["provisions"]:
        print(f"   {'ALL':5s} {totals['provisions']:>11,d} {totals['fires']:>8,d} "
              f"{totals['fires']/totals['provisions']:>11.3f} {totals['ungrounded']:>11,d}")

    # ---- 2. every verdict is schema-valid and every fire carries a grounded quote
    print("\n2. verdict integrity (the mapper's own output, before verification)")
    for e in ECON:
        p = os.path.join(out, "map", f"verdicts_{e}.jsonl")
        if not os.path.exists(p):
            print(f"   {e}: -- no verdicts file")
            ok = False
            continue
        rows = errs = fires = ungrounded = no_quote = bad_ind = 0
        inds = Counter()
        seen_pairs = set()
        dupes = 0
        with open(p, encoding="utf-8") as f:
            for line in f:
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    errs += 1
                    continue
                rows += 1
                if "error" in r:
                    errs += 1
                    continue
                for v in r.get("verdicts") or []:
                    ind = str(v.get("indicator") or "")
                    if not ind or ind.startswith("P"):
                        bad_ind += 1
                    key = (r.get("provision_id"), ind)
                    if key in seen_pairs:
                        dupes += 1
                    seen_pairs.add(key)
                    if v.get("applies"):
                        fires += 1
                        inds[ind] += 1
                        q = (v.get("verbatim_quote") or "").strip()   # schema field is verbatim_quote
                        if not q:
                            no_quote += 1
                        elif v.get("quote_grounded_ws") is False:
                            ungrounded += 1
        bad = []
        if errs:
            bad.append(f"{errs} error rows")
        if bad_ind:
            bad.append(f"{bad_ind} legacy/blank indicator ids"); ok = False
        if no_quote:
            bad.append(f"{no_quote} fires with NO quote"); ok = False
        if ungrounded:
            # not a failure: unfilable_reason() refuses these before they can be filed
            bad.append(f"{ungrounded} ungrounded fires (dropped at emit, not filed)")
        if dupes:
            bad.append(f"{dupes} duplicate (provision, indicator) verdicts")
        print(f"   {e}: {rows:,} provisions, {fires:,} fires, "
              f"{'; '.join(bad) if bad else 'clean'}")
        if inds:
            print(f"       fires by indicator: "
                  + ", ".join(f"{k}={v}" for k, v in sorted(inds.items())))

    # ---- 3. the mapper saw the SHIPPING codebook, not Round 1's
    print("\n3. which codebook produced these verdicts")
    try:
        sys.path.insert(0, os.getcwd())
        from config.instrument import load as load_instrument
        ins = load_instrument()
        note = "SHIPPING (decimal)" if ins.vintage == "decimal" else "ROUND 1 (legacy) -- WRONG"
        print(f"   instrument in use: {ins.vintage} vintage, {len(ins.blocks)} blocks -> {note}")
        if ins.vintage != "decimal":
            print("   The new traps in 6.2, 6.3, 7.3 and 7.5 are absent from these verdicts.")
            ok = False
        print(f"   gold rows available to S10: {len(list(ins.gold())):,}")
    except Exception as exc:                                   # noqa: BLE001
        print(f"   could not load the instrument: {exc}")
        ok = False

    # ---- 4. did triage's keeps actually reach the mapper?
    print("\n4. triage keeps vs provisions mapped")
    keeps = defaultdict(set)
    tp = os.path.join(out, "triage", "haiku_results.jsonl")
    if os.path.exists(tp):
        with open(tp, encoding="utf-8") as f:
            for line in f:
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if r.get("keep"):
                    keeps[r.get("economy")].add(r["provision_id"])
        for e in ECON:
            p = os.path.join(out, "map", f"verdicts_{e}.jsonl")
            if not os.path.exists(p):
                continue
            mapped = set()
            with open(p, encoding="utf-8") as f:
                for line in f:
                    try:
                        mapped.add(json.loads(line)["provision_id"])
                    except (json.JSONDecodeError, KeyError):
                        pass
            missed = keeps[e] - mapped
            print(f"   {e}: {len(keeps[e]):,} kept provisions, {len(mapped):,} mapped, "
                  f"{len(missed):,} kept-but-unmapped"
                  + ("  <-- investigate" if missed else ""))
            if missed:
                ok = False

    print("\n" + "=" * 78)
    print("SAFE TO CHAIN" if ok else "DO NOT CHAIN YET - see the flags above")
    print("=" * 78)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
