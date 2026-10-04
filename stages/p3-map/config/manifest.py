"""The run manifest: what ran, on which engine, against which corpus.

C5b asks for evidence that one pipeline produced rows on two engines, and Section 3's second-pass
check asks for a run that fetched nothing. Neither claim can be read out of the filed CSVs: a row
does not record the model that judged it, and a resumed run looks exactly like a fresh one. So each
stage that spends money or reads the corpus appends one entry here, and the header records the
engine, the instrument and the commit as they were **at the time of the run**.

    out/run_manifest.json
      run_id, created, git commit/branch/dirty, contract version
      instrument: directory, vintage, version, the automated indicator set
      engine:     provider, and the model resolved for each role
      settings:   the few that change what a run selects or files
      entries:    one per stage invocation, appended, never rewritten

Writing a manifest must never fail a paid run: every entry point swallows its own errors and says
so on stdout. A missing manifest is a lost mark; a crashed mapper is a lost day.
"""
from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
FILENAME = "run_manifest.json"


def _git(*args: str) -> str:
    try:
        out = subprocess.run(("git", *args), cwd=REPO_ROOT, capture_output=True,
                             text=True, timeout=10)
        return out.stdout.strip() if out.returncode == 0 else ""
    except Exception:
        return ""


def _engine() -> dict:
    """Provider and the model each role actually resolves to, asked of the factory itself."""
    from config.llm import engines
    from config.llm.factory import ROLES, _model_for
    from config.settings import SETTINGS
    try:
        declared = engines.selected()
    except Exception as e:       # a bad RDTII_ENGINE must show up here, not silently
        return {"error": f"{type(e).__name__}: {e}"}
    if declared is not None:
        # the engine's own record, plus the per-role resolution the factory will perform
        out = declared.as_manifest()
        out["roles"] = {}
        for role in ROLES:
            try:        # a role may have been given an engine of its own
                e = engines.selected(role=role) or declared
                out["roles"][role] = {"provider": "ollama" if role == "triage" else e.provider,
                                      "model": e.model_for(role)}
                if e.id != declared.id and role != "triage":
                    out["roles"][role]["engine_id"] = e.id
            except Exception as err:      # a bad role engine: recorded, not raised
                out["roles"][role] = {"provider": None, "model": None,
                                      "error": f"{type(err).__name__}: {err}"}
        out["provider"] = declared.provider
        out["ollama_host"] = SETTINGS.ollama_host if declared.provider == "ollama" else None
        return out
    provider = (SETTINGS.llm_provider or "").strip().lower()
    roles = {}
    for role in ROLES:
        # triage is forced local by decision #3; ask the factory, do not restate the rule
        p = "ollama" if role == "triage" else provider
        try:
            roles[role] = {"provider": p, "model": _model_for(SETTINGS, p, role)}
        except Exception as e:      # an unknown provider: record the failure, do not raise
            roles[role] = {"provider": p, "model": None, "error": f"{type(e).__name__}: {e}"}
    return {"provider": provider, "roles": roles,
            "open_weights": provider == "ollama",
            "ollama_host": SETTINGS.ollama_host if provider == "ollama" else None}


def _instrument() -> dict:
    try:
        from config.instrument import load
        ins = load()
        return {"dir": str(ins.dir), "vintage": ins.vintage,
                "version": ins.top.get("instrument_version") or ins.top.get("version"),
                "blocks": len(ins.blocks), "indicators": list(ins.ids)}
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}


def path() -> Path:
    from config.settings import SETTINGS
    return SETTINGS.out_dir / FILENAME


def header() -> dict:
    from config.settings import ECONOMIES, INDICATORS, SETTINGS
    # Which indicators a run covered. `economies` was recorded and this was not, so an arm scoped to
    # a subset of the instrument did not say which subset -- and re-emitting it without setting
    # INDICATORS_SCOPE silently produced rows for the DEFAULT nine instead. That happened on
    # 29 September to Timor-Leste's 52-indicator arm: 83 rows became 9 for the wrong indicators, and
    # the scope had to be recovered from that arm's own rollup because the manifest could not say.
    # Recorded as the resolved list, not the raw environment variable, so it is true even when the
    # scope came from the instrument's default rather than from a setting.
    _scope = os.getenv("INDICATORS_SCOPE", "").strip()
    return {
        # RUN_ID names the run in the write-up; the output directory is the fallback, because
        # that is what distinguishes two runs on this machine.
        "run_id": os.getenv("RUN_ID") or SETTINGS.out_dir.parent.name or SETTINGS.out_dir.name,
        "created": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "git": {"commit": _git("rev-parse", "HEAD"),
                "branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
                "dirty": bool(_git("status", "--porcelain"))},
        "contract_version": SETTINGS.contract_version,
        "engine": _engine(),
        "instrument": _instrument(),
        "settings": {
            "out_dir": str(SETTINGS.out_dir), "index_dir": str(SETTINGS.index_dir),
            "handoff2_dir": str(SETTINGS.handoff2_dir),
            "economies": list(ECONOMIES) or "all in corpus",
            "indicators": list(INDICATORS),
            "indicators_count": len(INDICATORS),
            "indicators_scope_env": _scope or "(unset — the instrument's automated set)",
            "select_mode": SETTINGS.select_mode,
            "selection_config": SETTINGS.selection_config or "config/selection.json",
            "newknown_sim": SETTINGS.newknown_sim,
            "ollama_num_ctx": SETTINGS.ollama_num_ctx,
            "ingest_gate": SETTINGS.ingest_gate,
        },
        "entries": [],
    }


def load() -> dict:
    p = path()
    if p.exists():
        try:
            m = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(m, dict) and "entries" in m:
                return m
        except (json.JSONDecodeError, OSError):
            pass
    return header()


def record(stage: str, **fields) -> None:
    """Append one stage entry. Never raises: a paid run must not die writing its own record."""
    try:
        m = load()
        entry = {"stage": stage, "at": time.strftime("%Y-%m-%dT%H:%M:%S"), **fields}
        # the engine is recorded per entry as well as in the header: a run resumed after an
        # engine change would otherwise claim the header's engine for rows it did not judge
        entry.setdefault("engine", _engine()["roles"])
        m["entries"].append(entry)
        p = path()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(m, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception as e:      # noqa: BLE001 — see the module docstring
        print(f"[manifest] WARNING: could not record {stage}: {type(e).__name__}: {e}", flush=True)


def summary(m: dict | None = None) -> str:
    m = m or load()
    eng = m.get("engine", {})
    roles = eng.get("roles", {})
    lines = [f"run {m.get('run_id')}  commit {m.get('git', {}).get('commit', '')[:8]}"
             f"{' (dirty)' if m.get('git', {}).get('dirty') else ''}",
             f"engine {eng.get('provider')}"
             f"{' [open weights]' if eng.get('open_weights') else ''}: "
             + ", ".join(f"{r}={v.get('model')}" for r, v in roles.items()),
             f"instrument {m.get('instrument', {}).get('vintage')} "
             f"({m.get('instrument', {}).get('blocks')} blocks)"]
    head_mapper = (roles.get("mapper") or {}).get("model")
    for e in m.get("entries", []):
        rest = ", ".join(f"{k}={v}" for k, v in e.items()
                         if k not in ("stage", "at", "engine"))
        # named only when it differs from the header, so a swapped run reads at a glance
        ent = ((e.get("engine") or {}).get("mapper") or {}).get("model")
        swap = f"  [engine {ent}]" if ent and ent != head_mapper else ""
        lines.append(f"  {e['at']}  {e['stage']:<16s} {rest}{swap}")
    return "\n".join(lines)


if __name__ == "__main__":   # python -m config.manifest
    print(summary())
