"""The Mapping tab: finished runs, their rows with the English gloss beside the original, one row in
detail, and the indicator picker for the Set up block.

The rules this module must not break: indicator IDs stay text; a blank Discovery Tag is a value, not an
error; the gloss is shown beside the original and labelled machine-made, never in its place; Timor-Leste's
two arms are read as two arms and summed; 7.1 and 7.2 are inverted.
"""
from __future__ import annotations

import re
from pathlib import Path

from .. import readers
from ..server import ApiError, App, rel_or_abs
from ..settings import FIXTURES_DIR, REPO, Settings, arm_dirs

RECORDS_RX = re.compile(r"^records_([A-Z]{2})(?:_(.+))?\.csv$")


def register(app: App) -> None:
    @app.route("GET", r"/api/map/runs")
    def runs(app: App, m, q, b):
        return 200, {"runs": list_runs(app.settings)}

    @app.route("GET", r"/api/map/rows")
    def rows(app: App, m, q, b):
        run = find_run(app.settings, q.get("run", ""))
        all_rows, notes = build_rows(run, app.settings)
        filtered = apply_filters(all_rows, q)
        return 200, {
            "run": run, "total": len(all_rows), "shown": len(filtered), "rows": filtered,
            "corpus_notes": notes,
            "economies": sorted({(r["_econ"], r["Economy"]) for r in all_rows}),
            "indicators": sorted({r["Indicator ID"] for r in all_rows}, key=indicator_sort_key),
        }

    @app.route("GET", r"/api/map/row")
    def row(app: App, m, q, b):
        run = find_run(app.settings, q.get("run", ""))
        try:
            i = int(q.get("i", ""))
        except ValueError:
            raise ApiError(400, "i must be an integer row index") from None
        return 200, row_detail(run, i, app.settings)

    @app.route("GET", r"/api/map/indicators")
    def indicators(app: App, m, q, b):
        return 200, indicator_picker(app.settings)

    register_run(app)


# ---- runs ---------------------------------------------------------------------------------------

def _records_files(arm: Path) -> list[Path]:
    """records_<E>.csv under <arm>/submission/, or directly under <arm> for a filed submission folder."""
    for folder in (arm / "submission", arm):
        files = sorted(p for p in folder.glob("records_*.csv") if RECORDS_RX.match(p.name))
        if files:
            return files
    return []


def _describe_run(run_id: str, name: str, arms: list[Path], kind: str) -> dict:
    economies: set[str] = set()
    total = 0
    for arm in arms:
        for f in _records_files(arm):
            code = RECORDS_RX.match(f.name).group(1)
            economies.add(code)
            loaded = readers.records_csv(f)
            total += len(loaded[1]) if loaded else 0
    manifest = readers.run_manifest(arms[0] / "run_manifest.json") if arms else {}
    return {
        "id": run_id, "name": name, "kind": kind,
        "arms": [a.name for a in arms], "arm_paths": [str(a) for a in arms],
        "economies": sorted(economies), "rows": total,
        "engine": readers.manifest_engine_label(manifest),
        "created": manifest.get("created"), "run_id": manifest.get("run_id"),
        "cost_usd": readers.manifest_cost(manifest) if manifest else None,
        "git": (manifest.get("git") or {}).get("commit"),
    }


def list_runs(s: Settings) -> list[dict]:
    runs: list[dict] = []
    arms = [a for a in arm_dirs(s) if _records_files(a)]
    if arms:
        kind = "fixture" if s.out_dir.resolve() == FIXTURES_DIR.resolve() else "run"
        name = "fixtures (real rows from run_2026-09-27)" if kind == "fixture" else s.out_dir.name
        runs.append(_describe_run(rel_or_abs(s.out_dir, REPO), name, arms, kind))
    maps = s.runs_root / "map"
    if maps.is_dir():
        for d in sorted((p for p in maps.iterdir() if p.is_dir()), key=lambda p: p.name, reverse=True):
            run_arms = sorted(p for p in d.glob("out*") if p.is_dir() and _records_files(p))
            if run_arms:
                runs.append(_describe_run(rel_or_abs(d, REPO), d.name, run_arms, "run"))
    sub = s.submission_dir
    if sub.is_dir() and _records_files(sub):
        runs.append(_describe_run(rel_or_abs(sub, REPO), "filed submission (frozen)", [sub], "frozen"))
    return runs


def find_run(s: Settings, run_id: str) -> dict:
    for run in list_runs(s):
        if run["id"] == run_id:
            return run
    raise ApiError(404, f"no run named {run_id!r}; choose one from the list")


# ---- rows ---------------------------------------------------------------------------------------

def _kind(r: dict) -> str:
    if r.get("Article / Section", "").strip().lower() == "n/a" or r.get("Verbatim Snippet", "").strip() == readers.NO_PROVISION_SNIPPET:
        return "no_provision"
    return "scored"


def _gloss_for(gloss: dict, pid, law: str, art: str, ind: str) -> tuple[dict | None, bool]:
    g = gloss["by_pid"].get((pid, ind)) if pid else None
    if g:
        return g, False
    cands = gloss["by_key"].get((law, art, ind)) or []
    if cands:
        return cands[0], len(cands) > 1
    return None, False


def _donor_arms(s: Settings, arm: Path) -> list[Path]:
    """Arms whose gloss files may stand in for a run that carries none (the packaged submission ships
    the audit pages but not the gloss files). A borrowed quote gloss is used only when its `original`
    equals the row's Verbatim Snippet byte for byte, so it can never describe a different text."""
    return [d for d in arm_dirs(s) if d.resolve() != arm.resolve()]


def _borrowed_gloss(donors: list[dict], pid, law: str, art: str, ind: str, snippet: str) -> dict | None:
    for gloss in donors:
        g, _ = _gloss_for(gloss, pid, law, art, ind)
        if g and g.get("original") == snippet:
            return g
    return None


def _scores_for(arm: Path, code: str) -> dict:
    """Indicator scores for one economy in one arm. A run keeps them in rollup/; the packaged submission
    keeps them in reports/, with a second file per extra arm. Earlier files win on a repeated key."""
    scores: dict = {}
    files = [arm / "rollup" / f"economy_scores_{code}.json"]
    files += sorted((arm / "reports").glob(f"economy_scores_{code}*.json")) if (arm / "reports").is_dir() else []
    for f in files:
        doc = readers.rollup(f)
        if isinstance(doc, dict) and isinstance(doc.get("scores"), dict):
            for k, v in doc["scores"].items():
                scores.setdefault(str(k), v)
    return scores


def build_rows(run: dict, s: Settings) -> tuple[list[dict], dict]:
    """Every row of every records file in every arm, with gloss, score and verification joined on."""
    names = readers.econ_names(s.stage_dirs["p3"])
    rows: list[dict] = []
    notes: dict[str, dict] = {}
    multi_arm = len(run["arm_paths"]) > 1
    for arm_s in run["arm_paths"]:
        arm = Path(arm_s)
        for f in _records_files(arm):
            code, suffix = RECORDS_RX.match(f.name).groups()
            loaded = readers.records_csv(f)
            if not loaded:
                continue
            header, csv_rows = loaded
            arm_label = arm.name if multi_arm else (suffix.replace("_", " ") if suffix else "")
            json_idx = readers.records_json_index(f.with_suffix(".json"))
            gloss = readers.gloss_index(arm / "audit" / f"gloss_{code}.jsonl")
            sections = readers.sections_index(arm / "audit" / f"gloss_sections_{code}.jsonl")
            donors = ([readers.gloss_index(d / "audit" / f"gloss_{code}.jsonl") for d in _donor_arms(s, arm)]
                      if not gloss["total"] else [])
            donors = [d for d in donors if d["total"]]
            scores = _scores_for(arm, code)
            verified = readers.verified_index(arm / "verify" / f"verified_{code}.jsonl")
            if sections["total"]:
                n = notes.setdefault(code, {"economy": names.get(code, code), "total": 0, "not_literal": 0})
                n["total"] += sections["total"]
                n["not_literal"] += sections["not_literal"]
            for r in csv_rows:
                law, art, ind = r.get("Law Name", ""), r.get("Article / Section", ""), r.get("Indicator ID", "")
                prov = json_idx.get((law, art, ind))
                pid = prov.get("_provision_id") if prov else None
                g, ambiguous = _gloss_for(gloss, pid, law, art, ind)
                borrowed = False
                if g is None and donors:
                    g = _borrowed_gloss(donors, pid, law, art, ind, r.get("Verbatim Snippet", ""))
                    borrowed = g is not None
                sc = scores.get(ind)
                v = verified.get((pid, ind)) if pid else None
                row = {col: r.get(col, "") for col in header}
                row.update({
                    "_i": len(rows), "_econ": code, "_econ_name": names.get(code, r.get("Economy", code)),
                    "_arm": arm_label, "_file": rel_or_abs(f, REPO), "_kind": _kind(r), "_pid": pid,
                    "_gloss": ({"english": g.get("english"), "is_literal": g.get("is_literal"),
                                "model": g.get("model"), "ambiguous": ambiguous, "borrowed": borrowed} if g else None),
                    "_score": (sc.get("score") if isinstance(sc, dict) else None),
                    "_score_inverted": ind in readers.INVERTED_INDICATORS,
                    "_verification": (v.get("verifier_verdict") if v else None),
                    "_final_applies": (v.get("final_applies") if v else None),
                })
                rows.append(row)
    for n in notes.values():
        n["rate"] = round(n["not_literal"] / n["total"], 3) if n["total"] else 0.0
    if run.get("kind") != "frozen":
        from .. import review as _review
        latest, _ = _review.load_decisions(s, run["id"])
        if latest:
            for r in rows:
                d = latest.get(_review.row_key(r))
                if d:
                    r["_decision"] = {"verdict": d["verdict"], "reason": d.get("reason", ""), "reviewer": d.get("reviewer"),
                                      "decided_at": d.get("decided_at"), "corrections": d.get("corrections") or {}}
    return rows, notes


def apply_filters(rows: list[dict], q: dict) -> list[dict]:
    econ = q.get("economy", "").strip().upper()
    ind = q.get("indicator", "").strip()
    tag = q.get("tag", "").strip()
    text = q.get("q", "").strip().lower()
    out = []
    for r in rows:
        if econ and r["_econ"] != econ:
            continue
        if ind and r.get("Indicator ID") != ind:
            continue
        if tag:
            want = "" if tag == "none" else tag.upper()
            if r.get("Discovery Tag", "") != want:
                continue
        if text:
            hay = " ".join([r.get("Law Name", ""), r.get("Article / Section", ""), r.get("Verbatim Snippet", ""),
                            (r.get("_gloss") or {}).get("english") or "", r.get("Notes", "")]).lower()
            if text not in hay:
                continue
        out.append(r)
    return out


def indicator_sort_key(ind: str):
    return tuple(int(p) if p.isdigit() else 0 for p in str(ind).split("."))


def row_detail(run: dict, i: int, s: Settings) -> dict:
    rows, notes = build_rows(run, s)
    if not 0 <= i < len(rows):
        raise ApiError(404, f"row {i} is not in this run (it has {len(rows)} rows)")
    r = dict(rows[i])
    arm = None
    for arm_s in run["arm_paths"]:
        if rel_or_abs(Path(arm_s), REPO) in r["_file"] or r["_file"].startswith(rel_or_abs(Path(arm_s), REPO)):
            arm = Path(arm_s)
            break
    arm = arm or Path(run["arm_paths"][0])
    code, ind, law, art, pid = r["_econ"], r["Indicator ID"], r["Law Name"], r["Article / Section"], r["_pid"]
    f = REPO / r["_file"] if not Path(r["_file"]).is_absolute() else Path(r["_file"])
    prov = readers.records_json_index(f.with_suffix(".json")).get((law, art, ind)) or {}
    sections = readers.sections_index(arm / "audit" / f"gloss_sections_{code}.jsonl")
    sg = sections["by_pid"].get(pid) if pid else None
    if not sg:
        cands = sections["by_key"].get((law, art)) or []
        sg = cands[0] if cands else None
    if not sg and pid and not sections["total"]:
        for d in _donor_arms(s, arm):
            sg = readers.sections_index(d / "audit" / f"gloss_sections_{code}.jsonl")["by_pid"].get(pid)
            if sg:
                break
    sc = _scores_for(arm, code).get(ind)
    v = readers.verified_index(arm / "verify" / f"verified_{code}.jsonl").get((pid, ind)) if pid else None
    r.update({
        "_section_gloss": ({"original": sg.get("original"), "english": sg.get("english"),
                            "is_literal": sg.get("is_literal"), "model": sg.get("model")} if sg else None),
        "_raw_context": prov.get("raw_context"),
        "_record_type": prov.get("_record_type"),
        "_score_detail": sc if isinstance(sc, dict) else None,
        "_verify": ({"mapper": v.get("mapper"), "verifier": v.get("verifier"),
                     "verifier_verdict": v.get("verifier_verdict"), "final_applies": v.get("final_applies"),
                     "final_score_hint": v.get("final_score_hint"), "trap_checks": v.get("trap_checks")} if v else None),
        "_corpus_note": notes.get(code),
        "_arm_dir": str(arm),
        "_read_only": run["kind"] == "frozen",
    })
    r.setdefault("_decision", None)
    if run["kind"] != "frozen":
        from .. import review as _review
        _, lines = _review.load_decisions(s, run["id"])
        key = _review.row_key(r)
        r["_decision_history"] = [d for d in lines if d.get("key") == key]
    return r


# ---- the indicator picker -------------------------------------------------------------------------

def indicator_picker(s: Settings) -> dict:
    order = readers.parse_indicator_order(s.instrument_dir / "indicator_order.yaml")
    items = [it for it in order.get("indicators", []) if it.get("status") == "in_scope"]
    automated = readers.automated_ids(order)
    tiers = readers.codebook_tiers(s.instrument_dir / "indicators.yaml")
    practice = readers.practice_based(s.instrument_dir / "indicator_order.yaml")
    pillars: dict[int, dict] = {}
    for it in items:
        p = pillars.setdefault(int(it.get("pillar") or 0), {"pillar": int(it.get("pillar") or 0),
                                                            "label": it.get("pillar_label") or f"Pillar {it.get('pillar')}",
                                                            "indicators": []})
        p["indicators"].append({"id": it["id"], "name": it.get("name"), "automated": it["id"] in automated,
                                "tier": tiers.get(it["id"]), "practice_based": practice.get(it["id"]),
                                "evidence": it.get("evidence")})
    return {
        "source": str(s.instrument_dir / "indicator_order.yaml"),
        "listed": order.get("meta", {}).get("listed"), "in_scope": len(items),
        "automated": automated,
        "tiers": {"A": "reviewed: scoring tree, coding rules, traps and worked examples; pillars 6 and 7",
                  "B": "drafted at Tier A depth from the guides, not yet reviewed",
                  "C": "the host's methodology criteria from the Round 1 database only, extracted by script; a row mapped "
                       "under it names the tier in Notes and needs a higher confidence before it is tagged NEW"},
        "tier_counts": {t: sum(1 for it in items if tiers.get(it["id"]) == t) for t in ("A", "B", "C")},
        "tier_ids": {t: [it["id"] for it in items if tiers.get(it["id"]) == t] for t in ("A", "B", "C")},
        "tier_text": readers.codebook_tier_notes(s.instrument_dir / "indicators.yaml"),
        "practice_based": {it["id"]: practice[it["id"]] for it in items if it["id"] in practice},
        "pillars": [pillars[k] for k in sorted(pillars)],
    }


# =====================================================================================================
# The run: which extraction output to map, the pre-run checks, the step plan, and the progress parser
# =====================================================================================================

import json as _json  # noqa: E402
import subprocess as _subprocess  # noqa: E402
import time as _time  # noqa: E402

from .. import probes as _probes  # noqa: E402
from ..envbuild import ChoiceError, NeedsKey, build_env  # noqa: E402
from ..jobs import Job, Step  # noqa: E402
from .extract import DEFAULT_LANGUAGE as _LANG  # noqa: E402

P3_MODULE = "src.p3map"

# An empty dense leg keyed like the sparse leg, so candidate selection sees a zero-contribution dense
# side (the bm25-only path: no torch, no model download). Runs under the stage's Python for numpy.
DENSE_STUB_CODE = (
    "import sys, numpy as np\n"
    "from pathlib import Path\n"
    "idx = Path(sys.argv[1]); sparse = idx / 'bm25_top.npz'\n"
    "if not sparse.is_file(): raise SystemExit(f'no {sparse}: run the keyword index first')\n"
    "with np.load(sparse) as leg: keys = list(leg.keys())\n"
    "out = {k: (np.zeros(0, dtype=np.int32) if k.endswith('_idx') else np.zeros(0, dtype=np.float32)) for k in keys}\n"
    "np.savez_compressed(idx / 'dense_top.npz', **out)\n"
    "print(f'[dense] stub written: empty dense_top.npz mirroring {len(out)} keys of bm25_top.npz', flush=True)\n"
)


def register_run(app: App) -> None:
    @app.route("GET", r"/api/map/handoffs")
    def handoffs(app: App, m, q, b):
        return 200, {"handoffs": list_handoffs(app.settings), "python": app.settings.python_for("p3"),
                     "economy_names": readers.econ_names(app.settings.stage_dirs["p3"]),
                     "stage_present": (app.settings.stage_dirs["p3"] / "src" / "p3map" / "cli.py").is_file()}

    @app.route("POST", r"/api/map/precheck")
    def precheck_route(app: App, m, q, b):
        return 200, {"checks": precheck(app, b or {})}

    @app.route("POST", r"/api/map/start")
    def start(app: App, m, q, b):
        if not app.jobs:
            raise ApiError(503, "the run layer is not available")
        checks = precheck(app, b or {})
        fails = [c for c in checks if c["level"] == "fail"]
        if fails:
            raise ApiError(409, "; ".join(c["text"] for c in fails))
        job = plan_map(app, b or {})
        app.jobs.submit(job)
        return 200, {"job": job.public()}


# ---- handoffs -----------------------------------------------------------------------------------------

def index_dir_for(s: Settings, handoff: Path) -> Path:
    if handoff.resolve() == s.handoff2_dir.resolve():
        return s.index_dir
    return s.runs_root / "index" / handoff.name


def describe_handoff(s: Settings, path: Path, kind: str) -> dict:
    laws = readers.cached(path / "laws.jsonl", readers.read_jsonl) or []
    status = readers.cached(path / "doc_status.jsonl", readers.read_jsonl) or []
    econs: dict[str, int] = {}
    for law in laws:
        code = (law.get("economy") or str(law.get("doc_id", ""))[:2].upper() or "?")
        econs[code] = econs.get(code, 0) + 1
    idx = index_dir_for(s, path)
    dense = idx / "dense_top.npz"
    return {
        "id": rel_or_abs(path, REPO), "path": str(path), "name": path.name, "kind": kind,
        "complete": all((path / f).is_file() for f in ("provisions.jsonl", "laws.jsonl", "doc_status.jsonl")),
        "economies": econs, "documents": len(status), "docs_ok": sum(1 for r in status if r.get("status") == "ok"),
        "provisions": sum(int(r.get("n_provisions") or 0) for r in status), "laws": len(laws),
        "languages": {c: _LANG.get(c) for c in econs},
        "index": {"dir": str(idx), "id": rel_or_abs(idx, REPO),
                  "corpus": (idx / "prefilter_corpus.jsonl").is_file(), "bm25": (idx / "bm25_top.npz").is_file(),
                  "dense": dense.is_file(), "dense_is_stub": dense.is_file() and dense.stat().st_size < 4096},
    }


def list_handoffs(s: Settings) -> list[dict]:
    out = []
    seen = set()

    def add(p: Path, kind: str):
        rp = p.resolve()
        if rp in seen or not p.is_dir() or not (p / "laws.jsonl").is_file():
            return
        seen.add(rp)
        out.append(describe_handoff(s, p, kind))

    add(s.handoff2_dir, "HANDOFF2_DIR")
    root = s.runs_root / "extract"
    if root.is_dir():
        for p in sorted(root.iterdir(), reverse=True):
            add(p, "extraction run")
    return out


def find_handoff(s: Settings, ref: str) -> dict:
    ref = (ref or "").strip()
    for h in list_handoffs(s):
        if h["id"] == ref or h["path"] == ref:
            return h
    p = Path(ref) if ref else None
    if p is not None:
        p = p if p.is_absolute() else REPO / p
        if p.is_dir() and (p / "laws.jsonl").is_file():
            return describe_handoff(s, p, "typed")
    raise ApiError(404, f"no extraction output at {ref!r}; run Extraction first or point HANDOFF2_DIR at one")


# ---- the request --------------------------------------------------------------------------------------

def _norm_request(app: App, req: dict) -> dict:
    s = app.settings
    h = find_handoff(s, req.get("handoff") or "")
    present = list(h["economies"])
    economies = [str(e).upper() for e in (req.get("economies") or present) if str(e).strip()]
    order = readers.parse_indicator_order(s.instrument_dir / "indicator_order.yaml")
    in_scope = [it["id"] for it in order.get("indicators", []) if it.get("status") == "in_scope"]
    indicators = [str(i) for i in (req.get("indicators") or readers.automated_ids(order))]
    engine = str(req.get("engine") or app.engines.selected or "")
    select_mode = str(req.get("select_mode") or "caps")
    if select_mode not in ("caps", "scores"):
        raise ApiError(400, "select_mode must be caps or scores")
    dense = str(req.get("dense") or "auto")
    if dense not in ("auto", "real", "stub"):
        raise ApiError(400, "dense must be auto, real or stub")
    rebuild = bool(req.get("rebuild_index"))
    limit = req.get("limit")
    try:
        limit = int(limit) if limit not in (None, "", 0, "0") else None
    except (TypeError, ValueError):
        raise ApiError(400, "limit must be a whole number") from None
    idx = Path(h["index"]["dir"])
    have_dense_real = h["index"]["dense"] and not h["index"]["dense_is_stub"]
    if dense == "auto":
        dense = "real" if (have_dense_real and not rebuild) or select_mode == "scores" else "stub"
    return {"handoff": h, "economies": economies, "present": present, "indicators": indicators, "in_scope": in_scope,
            "engine": engine, "select_mode": select_mode, "dense": dense, "rebuild": rebuild,
            "gloss": bool(req.get("gloss", True)), "limit": limit, "index_dir": idx,
            "run_name": re.sub(r"[^A-Za-z0-9_.-]", "_", str(req.get("run_name") or ""))[:40]}


def _torch_state(py: str, cwd: Path) -> dict:
    code = "import torch;print('cuda' if torch.cuda.is_available() else 'cpu')"
    try:
        r = _subprocess.run([py, "-c", code], capture_output=True, text=True, timeout=90, cwd=str(cwd))
        err = r.stderr.strip().splitlines()[-1] if r.returncode != 0 and r.stderr.strip() else None
        return {"ok": r.returncode == 0, "device": r.stdout.strip() if r.returncode == 0 else None, "error": err}
    except (OSError, _subprocess.TimeoutExpired) as e:
        return {"ok": False, "device": None, "error": str(e)}


def _bge_cached() -> bool:
    home = Path.home() / ".cache" / "huggingface" / "hub"
    return any(home.glob("models--BAAI--bge-m3*"))


def precheck(app: App, req: dict) -> list[dict]:
    s = app.settings
    checks: list[dict] = []

    def add(level: str, check: str, text: str):
        checks.append({"level": level, "check": check, "text": text, "ok": level != "fail"})

    p3 = s.stage_dirs["p3"]
    py = s.python_for("p3")
    if not (p3 / "src" / "p3map" / "cli.py").is_file():
        add("fail", "stage", "The mapping stage is not in this repository.")
        return checks
    try:
        r = _subprocess.run([py, "-c", f"import {P3_MODULE}.cli, numpy, bm25s; print('ok')"], capture_output=True,
                            text=True, timeout=90, cwd=str(p3))
        if r.returncode == 0:
            add("ok", "stage", "The mapping stage and its packages import.")
        else:
            last = (r.stderr.strip().splitlines() or ["unknown error"])[-1]
            add("fail", "stage", f"The mapping stage does not import with {py}: {last}. Install requirements-demo.txt "
                                 "or point RDTII_PYTHON_P3 at a Python that has them.")
            return checks
    except (OSError, _subprocess.TimeoutExpired) as e:
        add("fail", "stage", f"Could not run {py}: {e}")
        return checks

    try:
        n = _norm_request(app, req)
    except ApiError as e:
        add("fail", "input", e.message)
        return checks
    h = n["handoff"]
    if not h["complete"]:
        add("fail", "input", "That extraction output is incomplete: provisions.jsonl, laws.jsonl and doc_status.jsonl are all needed.")
    else:
        add("ok", "input", f"{h['name']}: {h['documents']} documents, {h['provisions']} provisions; economies "
                           + ", ".join(f"{c} ({k} laws)" for c, k in h["economies"].items()) + ".")
    missing_e = [e for e in n["economies"] if e not in n["present"]]
    if not n["economies"]:
        add("fail", "economies", "Choose at least one economy.")
    elif missing_e:
        add("fail", "economies", f"Not in this extraction output: {', '.join(missing_e)}.")
    else:
        add("ok", "economies", "Economies: " + ", ".join(n["economies"]) + ".")
    bad_i = [i for i in n["indicators"] if i not in n["in_scope"]]
    if not n["indicators"]:
        add("fail", "indicators", "Choose at least one indicator.")
    elif bad_i:
        add("fail", "indicators", f"Not in the instrument: {', '.join(bad_i)}.")
    else:
        shown = ", ".join(n["indicators"][:12]) + (" and more" if len(n["indicators"]) > 12 else "")
        add("ok", "indicators", f"{len(n['indicators'])} indicator(s): {shown}.")

    idx = n["index_dir"]
    have = h["index"]
    if n["rebuild"] or not have["corpus"] or not have["bm25"]:
        add("ok", "index", f"The corpus index will be built at {rel_or_abs(idx, REPO)}: read every provision, then the keyword index.")
    else:
        add("ok", "index", f"Reusing the index at {rel_or_abs(idx, REPO)}.")
    if n["dense"] == "stub":
        non_english = [e for e in n["economies"] if _LANG.get(e, "eng") != "eng"]
        if n["select_mode"] == "scores":
            add("fail", "dense", "Score thresholds need the meaning index; choose the real dense leg or the caps rule.")
        elif non_english:
            add("fail", "dense", f"Keyword retrieval alone reads almost nothing in {', '.join(non_english)} "
                                 "(measured: zero of 450,000 slots for Chinese and Lao). Use the real dense leg.")
        else:
            add("warn", "dense", "Keyword index only; the meaning index is stubbed empty. Fine for English corpora with the caps rule; nothing is downloaded.")
    elif have["dense"] and not have["dense_is_stub"] and not n["rebuild"]:
        add("ok", "dense", "Reusing the meaning index (BGE-M3 embeddings).")
    else:
        t = _torch_state(py, p3)
        if not t["ok"]:
            add("fail", "dense", f"The meaning index needs torch and sentence-transformers: {t['error'] or 'not importable'}. "
                                 "Choose the stub for English corpora, or install the CPU wheel.")
        else:
            cached = _bge_cached()
            add("ok" if t["device"] == "cuda" else "warn", "dense",
                f"Meaning index will be built on {t['device']}" + ("" if t["device"] == "cuda" else ", which is slow for large corpora")
                + ("; the BGE-M3 model is cached." if cached else "; the BGE-M3 model, about 2 GB, will be downloaded first."))
    add("ok", "selection", "Candidate rule: " + ("Round 1 fixed caps, fused over both legs." if n["select_mode"] == "caps"
                                                   else "measured score thresholds per indicator and language."))

    eid = n["engine"]
    try:
        e = app.engines.get(eid)
    except ValueError as exc:
        add("fail", "engine", str(exc))
        e = None
    if e:
        label = f"{eid} ({e.get('label', '')})"
        if e.get("key_env"):
            add("ok" if app.key.held() else "fail", "engine",
                f"Engine {label}: " + ("API key held in memory." if app.key.held() else "needs an API key; hold one in the banner under Engine Selection first."))
        else:
            ol = _probes.probe_ollama(ttl=5)
            model = (e.get("roles") or {}).get("mapper", "")
            if not ol["ok"]:
                add("fail", "engine", f"Engine {label}: Ollama is not answering at {ol['host']} ({ol.get('error', '')}). Start Ollama first.")
            elif model and model not in ol["models"]:
                add("fail", "engine", f"Engine {label}: model {model} is not pulled on {ol['host']} (present: {', '.join(ol['models'][:8])}). Run: ollama pull {model}")
            else:
                dg = ol["digests"].get(model, "") or ""
                want = (e.get("digest") or "").replace("sha256:", "")
                if want and dg and not dg.startswith(want[:12]):
                    add("warn", "engine", f"Engine {label}: {model} is present but its digest {dg[:12]} differs from the declared {want[:12]}.")
                else:
                    add("ok", "engine", f"Engine {label}: Ollama answering, {model} present" + (f", digest {dg[:12]} matches the declaration." if want else "."))
    have_b = [p for p in (s.baseline_path, s.baseline_r2_path) if p and Path(p).exists()]
    if have_b:
        add("ok", "baseline", f"Baseline database found ({len(have_b)} file(s)); NEW against KNOWN will be real.")
    else:
        add("warn", "baseline", "No baseline database set (BASELINE_PATH, BASELINE_R2_PATH): every row will be tagged NEW.")
    if n["limit"]:
        add("warn", "cap", f"Demo cap: at most {n['limit']} borderline pairs screened and {n['limit']} provisions mapped per economy. This proves the chain, not the coverage.")
    add("ok", "output", "A fresh run folder under outputs/map/, never reused, so a new indicator scope cannot skip provisions.")
    return checks


# ---- the plan -----------------------------------------------------------------------------------------

def _cost(job: Job, stage: str, value) -> None:
    try:
        c = float(value)
    except (TypeError, ValueError):
        return
    costs = job.progress.setdefault("costs", {})
    costs[stage] = c
    job.progress["cost_usd"] = round(sum(costs.values()), 4)


def _special_doc_note(m, j):
    n = j.progress.get("special_docs_missing", 0) + 1
    j.progress["special_docs_missing"] = n
    if n == 1:
        return ("Some documents the full corpus treats specially are not in this input; expected on a slice.", None)
    return None


def _json_or_empty(s: str) -> dict:
    try:
        d = _json.loads(s)
        return d if isinstance(d, dict) else {}
    except ValueError:
        return {}


def _triage_tick(m, j):
    _cost(j, "triage", m[7])
    return (f"Screened {m[1]} of {m[2]} borderline pairs, keeping {m[4]}%, about {m[6]} min left.",
            {"done": int(m[1]), "total": int(m[2]), "unit": "pairs"})


def _map_tick(m, j):
    _cost(j, "map", m[9])
    return (f"{m[1]}: {m[2]} of {m[3]} provisions judged, {m[5]} matches so far, about {m[8]} min left.",
            {"done": int(m[2]), "total": int(m[3]), "unit": "provisions"})


def _map_done(m, j):
    d = _json_or_empty(m[2])
    if d.get("cost_usd") is not None:
        _cost(j, "map", d["cost_usd"])
    return (f"{m[1]}: careful reading done, {d.get('verdict_fires', '?')} matches from {d.get('provisions', '?')} provisions"
            + (f", {d.get('errors')} error(s)" if d.get("errors") else "") + ".", None)


def _verify_tick(m, j):
    _cost(j, "verify", m[7])
    return (f"{m[1]}: {m[2]} of {m[3]} matches re-checked; {m[4]} agreed, {m[6]} overturned.",
            {"done": int(m[2]), "total": int(m[3]), "unit": "matches"})


def _verify_done(m, j):
    d = _json_or_empty(m[2])
    if d.get("cost_usd") is not None:
        _cost(j, "verify", d["cost_usd"])
    return (f"{m[1]}: blind re-check done, {d.get('agree', '?')} agreed, {d.get('overturned', '?')} overturned.", None)


def _newknown_done(m, j):
    d = _json_or_empty(m[2])
    if "fires_tagged" not in d and "NEW" not in d and "new" not in d:
        return (f"{m[1]}: NEW and KNOWN tags assigned.", None)
    new = d.get("new", d.get("NEW", 0))
    known = d.get("known", d.get("KNOWN", 0))
    return (f"{m[1]}: {new} NEW, {known} KNOWN of {d.get('fires_tagged', new + known)} matches.", None)


def _gloss_done(m, j):
    _cost(j, "gloss", m[5])
    return (f"{m[1]}: {m[2]} quotes translated, {m[3]} flagged not literal.", None)


def _sections_done(m, j):
    _cost(j, "gloss_sections", m[5])
    return (f"{m[1]}: {m[2]} provision texts translated, {m[3]} not literal.", None)


P3_RULES: list[tuple[re.Pattern, object]] = [
    (re.compile(r"^imports ok$"), lambda m, j: ("The mapping stage and its packages import.", None)),
    (re.compile(r"^\[ingest\] (\d+) records, (\d+)s"), lambda m, j: (f"Indexing: {int(m[1]):,} provisions read so far.", None)),
    (re.compile(r"^\[ingest\] done: (\d+) records \+ (\d+) chunks in ([\d.]+)s"), lambda m, j: (f"Corpus indexed: {int(m[1]):,} provisions in {float(m[3]):.0f} s.", None)),
    (re.compile(r"^\[ingest\] WARNING: special doc (\S+) has no source_text"), lambda m, j: _special_doc_note(m, j)),
    (re.compile(r"^\[ingest\] (GATE|WARNING):?(.*)"), lambda m, j: (f"Index warning: {m[2].strip(' :')[:140]}", None)),
    (re.compile(r"^\[bm25\] corpus loaded: (\d+) rows"), lambda m, j: (f"Keyword index: {int(m[1]):,} rows loaded.", None)),
    (re.compile(r"^\[bm25\] done in (\d+)s"), lambda m, j: (f"Keyword index built in {m[1]} s.", None)),
    (re.compile(r"^\[dense\] corpus: (\d+) rows; loading (\S+) on (\w+)"), lambda m, j: (f"Meaning index: embedding {int(m[1]):,} rows with {m[2]} on {m[3]}.", None)),
    (re.compile(r"^\[dense\] (\d+)/(\d+) rows, (\d+) rows/s, ETA (\d+) min"), lambda m, j: (f"Meaning index {m[1]} of {m[2]} rows, about {m[4]} min left.", {"done": int(m[1]), "total": int(m[2]), "unit": "rows"})),
    (re.compile(r"^\[dense\] done in ([\d.]+) min"), lambda m, j: (f"Meaning index built in {m[1]} min.", None)),
    (re.compile(r"^\[dense\] stub written"), lambda m, j: ("Meaning index stubbed empty: keyword retrieval only for this run.", None)),
    (re.compile(r"^\[select\] mode (\w+) · ([\d,]+) corpus rows · economies (.+?) · (\d+) indicators"), lambda m, j: (f"Selecting candidates for {m[3]} across {m[4]} indicator(s), {m[1]} rule.", None)),
    (re.compile(r"^\[select\] direct=(\d+) gray=(\d+)"), lambda m, j: (f"{m[1]} strong and {m[2]} borderline candidate pairs chosen.", None)),
    (re.compile(r"^\[select\] WARNING (.*)"), lambda m, j: (f"Selection warning: {m[1][:140]}", None)),
    (re.compile(r"^\[haiku-triage\] resuming past (\d+); (\d+) pairs to judge"), lambda m, j: (f"Screening {m[2]} borderline pairs with the quick reader.", {"done": 0, "total": int(m[2]), "unit": "pairs"})),
    (re.compile(r"^\[haiku-triage\] --limit (\d+): judging ([\d,]+) pairs only"), lambda m, j: (f"Demo cap: screening only {m[2]} pairs.", None)),
    (re.compile(r"^\[haiku-triage\] (\d+)/(\d+) \(([\d.]+)/s, keep (\d+)%, err (\d+), ETA (\d+) min, \$([\d.]+)\)"), _triage_tick),
    (re.compile(r"^\[haiku-triage\] done: (\d+) judged, kept (\d+)"), lambda m, j: (f"Screening done: {m[2]} of {m[1]} kept.", None)),
    (re.compile(r"^\[baseline\] absent, skipped"), lambda m, j: ("No baseline database found: every row will be tagged NEW.", None)),
    (re.compile(r"^\[baseline\] (\d+) rows total, (\d+) in P6/P7 scope"), lambda m, j: (f"Baseline loaded: {m[1]} rows, {m[2]} in scope.", None)),
    (re.compile(r"^\[map:(\w\w)\] (\d+) provisions / (\d+) pairs .*?model (\S+), (\d+) workers"), lambda m, j: (f"{m[1]}: careful reading of {m[2]} provisions with {m[4]}, {m[5]} worker(s).", {"done": 0, "total": int(m[2]), "unit": "provisions"})),
    (re.compile(r"^\[map:(\w\w)\] (\d+) provisions / (\d+) pairs"), lambda m, j: (f"{m[1]}: careful reading of {m[2]} provisions.", {"done": 0, "total": int(m[2]), "unit": "provisions"})),
    (re.compile(r"^\[map:(\w\w)\] (\d+)/(\d+) \(([\d.]+)/s, fires (\d+), ungrounded (\d+), err (\d+), ETA (\d+) min, \$([\d.]+)\)"), _map_tick),
    (re.compile(r"^\[map:(\w\w)\] HARD STOP at \$([\d.]+)"), lambda m, j: (f"Cost ceiling reached at ${m[2]}; mapping stopped.", None)),
    (re.compile(r"^\[map:(\w\w)\] done \(cumulative\): (\{.*\})$"), _map_done),
    (re.compile(r"^\[verify:(\w\w)\] (\d+) fires to verify"), lambda m, j: (f"{m[1]}: a second model re-checks {m[2]} matches blind.", {"done": 0, "total": int(m[2]), "unit": "matches"})),
    (re.compile(r"^\[verify:(\w\w)\] (\d+)/(\d+) agree (\d+) tiebreak (\d+) \(overturned (\d+)\).*?\$([\d.]+)"), _verify_tick),
    (re.compile(r"^\[verify:(\w\w)\] done \(cumulative\): (\{.*\})$"), _verify_done),
    (re.compile(r"^\[newknown:(\w\w)\] no baseline_rows"), lambda m, j: (f"{m[1]}: no baseline in this run, every match tagged NEW.", None)),
    (re.compile(r"^\[newknown:(\w\w)\] (\{.*\})$"), _newknown_done),
    (re.compile(r"^\[rollup:(\w\w)\] economy-level engine unavailable"), lambda m, j: (f"{m[1]}: the economy-level scores could not be computed (engine unavailable).", None)),
    (re.compile(r"^\[rollup:(\w\w)\] "), lambda m, j: (f"{m[1]}: indicator scores computed.", None)),
    (re.compile(r"^\[submission:(\w\w)\] (\d+) rows -> "), lambda m, j: (f"{m[1]}: {m[2]} evidence rows written in the host's 14 columns.", None)),
    (re.compile(r"^\[submission\] DROP"), lambda m, j: (None, {"+skipped": 1})),
    (re.compile(r"^\[eval:(\w\w)\] \{"), lambda m, j: (f"{m[1]}: self-evaluation written.", None)),
    (re.compile(r"^\[gloss:(\w\w)\] nothing to gloss"), lambda m, j: (f"{m[1]}: nothing to translate.", None)),
    (re.compile(r"^\[gloss:(\w\w)\] (\d+) quotes to gloss on (\S+)"), lambda m, j: (f"{m[1]}: translating {m[2]} quotes into English with {m[3]}, for review only.", None)),
    (re.compile(r"^\[gloss:(\w\w)\] (\d+) glossed, (\d+) flagged not literal, (\d+) errors,.*?\$([\d.]+)"), _gloss_done),
    (re.compile(r"^\[gloss-sections:(\w\w)\] (\d+) provisions on (\S+)"), lambda m, j: (f"{m[1]}: translating {m[2]} provision texts.", None)),
    (re.compile(r"^\[gloss-sections:(\w\w)\] (\d+) glossed, (\d+) not literal, (\d+) errors,.*?\$([\d.]+)"), _sections_done),
    (re.compile(r"^\[excel\] (\d+) fires -> "), lambda m, j: (f"Review workbook written ({m[1]} matches).", None)),
    (re.compile(r"^\[audit\] (\d+) fires -> "), lambda m, j: (f"Audit page written ({m[1]} matches).", None)),
    (re.compile(r"LLMConfigError|ANTHROPIC_API_KEY is empty"), lambda m, j: ("The chosen engine needs an API key: hold one in the banner under Engine Selection and start again.", None)),
    (re.compile(r"ConnectError|Connection refused|actively refused"), lambda m, j: ("Cannot reach the local model server (Ollama). Start it and run again.", None)),
    (re.compile(r"ContextOverflow"), lambda m, j: ("The local model's context window is too small for the codebook; raise OLLAMA_NUM_CTX.", None)),
    (re.compile(r"ModuleNotFoundError: No module named '([^']+)'"), lambda m, j: (f"A Python package is missing: {m[1]}. Install requirements-demo.txt or point RDTII_PYTHON_P3 at a Python that has it.", None)),
    (re.compile(r"^\[manifest\] WARNING"), lambda m, j: ("Warning: the run record could not be updated.", None)),
]


def parse_p3(line: str, job: Job):
    for rx, fn in P3_RULES:
        m = rx.search(line)
        if m:
            return fn(m, job)
    return None


def _poll_manifest(out_dir: Path):
    seen = {"n": 0}

    def poll(job: Job):
        mf = out_dir / "run_manifest.json"
        if not mf.is_file():
            return None
        doc = readers.run_manifest(mf)
        entries = doc.get("entries") or []
        if len(entries) > seen["n"]:
            e = entries[-1]
            seen["n"] = len(entries)
            model = ((e.get("engine") or {}).get("mapper") or {}).get("model") or e.get("model") or ""
            cost = e.get("cost_usd")
            text = f"Recorded in the run manifest: {e.get('stage')}"
            if e.get("economy"):
                text += f" for {e['economy']}"
            if model:
                text += f" on {model}"
            if cost is not None:
                text += f", ${float(cost):.2f}"
            return text + "."
        return None
    return poll


def plan_map(app: App, req: dict) -> Job:
    s = app.settings
    p3 = s.stage_dirs["p3"]
    n = _norm_request(app, req)
    h = n["handoff"]
    idx = n["index_dir"]
    eid = n["engine"]
    stamp = _time.strftime("%Y%m%d-%H%M%S")
    run_name = f"{stamp}_{eid}" + (f"_{n['run_name']}" if n["run_name"] else "")
    out_dir = s.runs_root / "map" / run_name / "out"
    extra = {
        "HANDOFF2_DIR": str(h["path"]), "INDEX_DIR": str(idx), "OUT_DIR": str(out_dir),
        "ECONOMIES": ",".join(n["economies"]), "INDICATORS_SCOPE": ",".join(n["indicators"]),
        "INSTRUMENT_DIR": str(s.instrument_dir), "SELECT_MODE": n["select_mode"], "RUN_ID": run_name,
    }
    if s.baseline_path:
        extra["BASELINE_PATH"] = s.baseline_path
    if s.baseline_r2_path:
        extra["BASELINE_R2_PATH"] = s.baseline_r2_path
    try:
        env, public = build_env("p3", app.engines, app.key, {"RDTII_ENGINE": eid}, extra=extra)
    except ChoiceError as e:
        raise ApiError(400, str(e)) from None
    except NeedsKey as e:
        raise ApiError(409, str(e)) from None
    py = s.python_for("p3")
    have = h["index"]
    need_dense = n["rebuild"] or not have["dense"] or (n["dense"] == "real" and have["dense_is_stub"])
    if need_dense and n["dense"] == "real" and "EMBED_DEVICE" not in env:
        t = _torch_state(py, p3)
        env["EMBED_DEVICE"] = t.get("device") or "cpu"
        public["EMBED_DEVICE"] = env["EMBED_DEVICE"]
    mod = [py, "-m"]
    steps: list[Step] = [Step(label="check the mapping stage imports", cwd=p3, env=env, parse=parse_p3,
                              argv=[py, "-c", f"import {P3_MODULE}.cli, numpy, bm25s; print('imports ok')"])]
    if n["rebuild"] or not have["corpus"]:
        steps.append(Step(label="read every provision into the corpus index", cwd=p3, env=env, parse=parse_p3,
                          argv=mod + [f"{P3_MODULE}.cli", "ingest"]))
    if n["rebuild"] or not have["bm25"]:
        steps.append(Step(label="build the keyword index", cwd=p3, env=env, parse=parse_p3,
                          argv=mod + [f"{P3_MODULE}.cli", "prefilter", "--leg", "bm25"]))
    if need_dense:
        if n["dense"] == "real":
            steps.append(Step(label="build the meaning index (BGE-M3 embeddings)", cwd=p3, env=env, parse=parse_p3,
                              argv=mod + [f"{P3_MODULE}.cli", "prefilter", "--leg", "dense"]))
        else:
            steps.append(Step(label="stub the meaning index (keyword retrieval only)", cwd=p3, env=env, parse=parse_p3,
                              argv=[py, "-c", DENSE_STUB_CODE, str(idx)]))
    steps.append(Step(label=f"select candidate pairs ({n['select_mode']} rule)", cwd=p3, env=env, parse=parse_p3,
                      argv=mod + [f"{P3_MODULE}.cli", "select"]))
    tri = mod + [f"{P3_MODULE}.triage.haiku"] + (["--limit", str(n["limit"])] if n["limit"] else [])
    steps.append(Step(label="quick screen of the borderline pairs", cwd=p3, env=env, parse=parse_p3, argv=tri))
    have_baseline = any(p and Path(p).exists() for p in (s.baseline_path, s.baseline_r2_path))
    if have_baseline:
        steps.append(Step(label="load the baseline database (NEW against KNOWN)", cwd=p3, env=env, parse=parse_p3,
                          argv=mod + [f"{P3_MODULE}.discovery.baseline"]))
    for e in n["economies"]:
        steps.append(Step(label=f"{e}: careful reading of each provision, engine {eid}", cwd=p3, env=env, parse=parse_p3,
                          argv=mod + [f"{P3_MODULE}.mapping.runner", e] + ([str(n["limit"])] if n["limit"] else []),
                          poll=_poll_manifest(out_dir)))
        chain = mod + [f"{P3_MODULE}.chain", e] + (["--gloss"] if n["gloss"] else [])
        steps.append(Step(label=f"{e}: blind re-check, NEW against KNOWN, scores, evidence rows, self-evaluation"
                                + (", English glosses" if n["gloss"] else "") + ", workbook, audit page",
                          cwd=p3, env=env, parse=parse_p3, argv=chain, poll=_poll_manifest(out_dir)))
    title = f"Map {', '.join(n['economies'])} on {len(n['indicators'])} indicator(s), engine {eid}"
    job = Job(stage="p3", title=title, steps=steps, out_dir=out_dir.parent, env_public=public, redact=app.key.redact)
    job.say(f"Run folder: {rel_or_abs(out_dir, REPO)}. Engine {eid}: {app.engines.get(eid).get('label', '')}.")
    if not have_baseline:
        job.say("No baseline database is configured (BASELINE_PATH, BASELINE_R2_PATH), so the baseline load is "
                "skipped and every match will be tagged NEW.")
    return job
