"""The engine choice, the in-memory key, and the allowlist the browser is held to.

The browser names a choice; the server validates it against a list the server owns. The client never
supplies a variable name, and never a value the server has not enumerated. The engines themselves come
from stages/p3-map/config/llm/engines.json so the declared engines and the offered engines cannot drift.
"""
from __future__ import annotations

import json
import re
import threading
import time
import os as _os
from pathlib import Path
from .paths import child_path
from .probes import tool_path_dirs

ALLOWLIST = (
    "LLM_PROVIDER", "LLM_MODEL", "VERIFIER_MODEL", "ESCALATION_MODEL", "TRIAGE_MODEL",
    "OLLAMA_MODEL", "OLLAMA_HOST", "OCR_ENGINE", "RDTII_ENGINE",
    "RDTII_ENGINE_MAPPER", "RDTII_ENGINE_VERIFIER", "RDTII_ENGINE_ESCALATION",
)
SECRET_MARKERS = ("KEY", "TOKEN", "SECRET", "PASSWORD")
DEFAULT_KEY = "ANTHROPIC_API_KEY"
# The three roles a run may give an engine and a model of their own, and the variables that say so.
ROLE_ENGINE = {"mapper": "RDTII_ENGINE_MAPPER", "verifier": "RDTII_ENGINE_VERIFIER",
               "escalation": "RDTII_ENGINE_ESCALATION"}
ROLE_MODEL = {"mapper": "LLM_MODEL", "verifier": "VERIFIER_MODEL", "escalation": "ESCALATION_MODEL"}
ROLE_WORKERS = {"mapper": ("MAP_WORKERS",), "verifier": ("VERIFY_WORKERS", "TRIAGE_WORKERS")}


class KeyHolder:
    """Holds each provider's API key in process memory for the lifetime of the server, under the name
    of the variable its engine reads. Never written, never rendered. With no name given, every call
    means the Claude key, as it did when there was one provider."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._keys: dict[str, tuple[str, float]] = {}

    def set(self, key: str, name: str = DEFAULT_KEY) -> None:
        key = (key or "").strip()
        if not key or not re.fullmatch(r"[\x21-\x7e]{8,400}", key):
            raise ValueError("a key is 8 to 400 printable characters with no spaces")
        if not re.fullmatch(r"[A-Z][A-Z0-9_]{2,40}", name or ""):
            raise ValueError("a key is held under the name of the variable its engine reads")
        with self._lock:
            self._keys[name] = (key, time.time())

    def clear(self, name: str | None = None) -> None:
        """Forget one key, or every key when no name is given."""
        with self._lock:
            if name is None:
                self._keys.clear()
            else:
                self._keys.pop(name, None)

    def get(self, name: str = DEFAULT_KEY) -> str:
        with self._lock:
            return self._keys.get(name, ("", 0.0))[0]

    def held(self, name: str = DEFAULT_KEY) -> bool:
        with self._lock:
            return name in self._keys

    def public(self) -> dict:
        with self._lock:
            first = self._keys.get(DEFAULT_KEY)
            return {"held": first is not None, "set_at": first[1] if first else None,
                    "names": {n: {"held": True, "set_at": at} for n, (_, at) in self._keys.items()}}

    def redact(self, line: str) -> str:
        with self._lock:
            keys = [k for k, _ in self._keys.values()]
        for k in keys:
            if k in line:
                line = line.replace(k, "[key redacted]")
        return line


def load_engines(p3_dir: Path) -> dict | None:
    # RDTII_ENGINES_FILE names an alternative declaration; the stage honours the same variable
    path = Path(_os.environ.get("RDTII_ENGINES_FILE", "").strip() or p3_dir / "config" / "llm" / "engines.json")
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not doc.get("engines"):
        return None
    doc["_path"] = str(path)
    return doc


class EngineState:
    """Which declared engine the next run will use. Selectable only among the declared ids."""

    def __init__(self, doc: dict | None) -> None:
        self._lock = threading.Lock()
        self.doc = doc or {"engines": {}, "default": None}
        self.selected: str | None = self.doc.get("default") if self.doc.get("engines") else None
        if self.selected not in self.ids():
            self.selected = next(iter(self.ids()), None)

    def ids(self) -> list[str]:
        return list(self.doc.get("engines", {}).keys())

    def get(self, eid: str) -> dict:
        try:
            return self.doc["engines"][eid]
        except KeyError:
            raise ValueError(f"'{eid}' is not a declared engine; declared: {', '.join(self.ids()) or 'none'}") from None

    def select(self, eid: str) -> str:
        eid = str(eid or "").strip()
        self.get(eid)
        with self._lock:
            self.selected = eid
        return eid

    def key_names(self) -> list[str]:
        """The variable each hosted engine reads its key from, in declaration order."""
        out: list[str] = []
        for e in self.doc.get("engines", {}).values():
            if e.get("key_env") and e["key_env"] not in out:
                out.append(e["key_env"])
        return out

    def models_of(self, eid: str, ollama_models: list[str] | None = None) -> list[dict]:
        """The models a role may be given on one engine: the declared list (else the role models),
        and for a local engine whatever else its server holds, which is neither priced nor measured."""
        e = self.get(eid)
        out = [dict(m) for m in e.get("models") or [] if m.get("id")]
        seen = {m["id"] for m in out}
        for mid in dict.fromkeys(str(v) for k, v in (e.get("roles") or {}).items() if k != "triage"):
            if mid not in seen:
                out.append({"id": mid, "label": mid, "price": None, "measured": bool(e.get("measured", True))})
                seen.add(mid)
        if e.get("provider") == "ollama":
            for mid in ollama_models or []:
                if mid not in seen:
                    out.append({"id": mid, "label": mid, "price": [0.0, 0.0, 0.0, 0.0], "measured": False})
                    seen.add(mid)
        return out

    def public(self, ollama_models: list[str] | None = None) -> dict:
        with self._lock:
            sel = self.selected
        engines = []
        for eid, e in self.doc.get("engines", {}).items():
            engines.append({
                "id": eid, "label": e.get("label", eid), "provider": e.get("provider"),
                "open_weights": bool(e.get("open_weights")), "roles": e.get("roles", {}),
                "workers": e.get("workers"), "batch_lane": bool(e.get("batch_lane")),
                "digest": e.get("digest"), "key_env": e.get("key_env"), "endpoint_env": e.get("endpoint_env"),
                "name": e.get("name") or e.get("label", eid), "measured": bool(e.get("measured", True)),
                "model_prefix": e.get("model_prefix") or "",
                "price_source": e.get("price_source"), "models": self.models_of(eid, ollama_models),
            })
        return {"selected": sel, "default": self.doc.get("default"), "declared_in": self.doc.get("_path"),
                "engines": engines}


# ---- the environment a stage process receives ---------------------------------------------------------

PROVIDERS = ("anthropic", "ollama", "openai_compat")
DEFAULT_OLLAMA_HOST = "http://localhost:11434"


class ChoiceError(ValueError):
    """The browser named a variable or a value the server does not offer."""


class NeedsKey(RuntimeError):
    """The chosen engine needs an API key and none is held."""


def enumerate_values(name: str, engines: EngineState, ollama_models: list[str] | None = None) -> set[str]:
    """Every value the server will accept for one allowlisted name. Anything else is refused."""
    if name == "RDTII_ENGINE" or name in ROLE_ENGINE.values():
        return set(engines.ids())
    if name == "LLM_PROVIDER":
        return set(PROVIDERS)
    if name in ("LLM_MODEL", "VERIFIER_MODEL", "ESCALATION_MODEL", "TRIAGE_MODEL", "OLLAMA_MODEL"):
        vals = set(ollama_models or [])
        for e in engines.doc.get("engines", {}).values():
            vals.update(str(v) for v in (e.get("roles") or {}).values())
            vals.update(str(m["id"]) for m in e.get("models") or [] if m.get("id"))
        return vals
    if name == "OLLAMA_HOST":
        return {DEFAULT_OLLAMA_HOST, "http://127.0.0.1:11434", _os.environ.get("OLLAMA_HOST", "").rstrip("/") or DEFAULT_OLLAMA_HOST}
    if name == "OCR_ENGINE":
        return {"tesseract"}
    return set()


def validate_choices(choices: dict | None, engines: EngineState, ollama_models: list[str] | None = None) -> dict:
    out: dict[str, str] = {}
    for name, value in (choices or {}).items():
        if name not in ALLOWLIST:
            raise ChoiceError(f"{name!r} is not a setting the page may change; allowed: {', '.join(ALLOWLIST)}")
        if any(mark in str(name).upper() for mark in SECRET_MARKERS):
            raise ChoiceError("a key never rides a launch request")
        value = str(value)
        allowed = enumerate_values(name, engines, ollama_models)
        if value not in allowed:
            raise ChoiceError(f"{value!r} is not an offered value for {name}; offered: {', '.join(sorted(allowed)) or 'none'}")
        out[name] = value
    return out


def role_choices(roles: dict | None, engines: EngineState, eid: str,
                 ollama_models: list[str] | None = None) -> tuple[dict, dict]:
    """(variables, engine per role) for the roles a run gives an engine or a model of their own.

    `roles` is {role: {"engine": id, "model": id}}. A role left on the run's engine with that engine's
    own model yields no variable at all, so a run that changes nothing receives what it always did.
    """
    out: dict[str, str] = {}
    used = {role: eid for role in ROLE_ENGINE}
    base = engines.get(eid)
    for role, pick in (roles or {}).items():
        if role not in ROLE_ENGINE:
            raise ChoiceError(f"{role!r} is not a role a model can be chosen for; roles: {', '.join(ROLE_ENGINE)}")
        pick = pick or {}
        rid = str(pick.get("engine") or eid)
        try:
            e = engines.get(rid)
        except ValueError as exc:
            raise ChoiceError(str(exc)) from None
        offered = [m["id"] for m in engines.models_of(rid, ollama_models)]
        model = str(pick.get("model") or (e.get("roles") or {}).get(role) or "")
        if model not in offered:
            raise ChoiceError(f"{model!r} is not a model of {e.get('label') or rid}; offered: {', '.join(offered) or 'none'}")
        used[role] = rid
        if rid != eid:
            out[ROLE_ENGINE[role]] = rid
        if rid != eid or model != (base.get("roles") or {}).get(role):
            out[ROLE_MODEL[role]] = model
    return out, used


def build_env(stage: str, engines: EngineState, key: KeyHolder, choices: dict | None = None,
              extra: dict | None = None, ollama_models: list[str] | None = None,
              with_engine: bool = True, roles: dict | None = None) -> tuple[dict, dict]:
    """(env, public): the child environment and the non-secret part of it the page may show.

    Every allowlisted name and every key are removed first and set explicitly, because the stages load
    their own .env without overriding, so a stray file could otherwise decide a run. A stage that uses
    no AI engine (the crawler) passes with_engine=False and never needs a key. `roles` gives a role an
    engine or a model of its own; each engine in use then needs its own key held.
    """
    env = _os.environ.copy()
    key_names = tuple(dict.fromkeys((DEFAULT_KEY,) + tuple(engines.key_names())))
    for name in ALLOWLIST + key_names:
        env.pop(name, None)
    path = child_path(env.get("PATH", ""), tool_path_dirs())
    if path:
        env["PATH"] = path          # the stages find Tesseract and the package managers' tools
    env["PYTHONUTF8"] = "1"
    env["PYTHONUNBUFFERED"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    if stage == "p2":
        env["PYTHONPATH"] = "src" + _os.pathsep + "."
    chosen = validate_choices(choices, engines, ollama_models)
    env.update(chosen)
    public: dict[str, str] = dict(chosen)
    eid = (chosen.get("RDTII_ENGINE") or engines.selected) if with_engine else None
    if eid:
        e = engines.get(eid)
        env["RDTII_ENGINE"] = eid
        public["RDTII_ENGINE"] = eid
        role_vars, used = role_choices(roles, engines, eid, ollama_models)
        env.update(role_vars)
        public.update(role_vars)
        for role, names in ROLE_WORKERS.items():      # each role's thread count follows its own engine
            workers = engines.get(used[role]).get("workers")
            if workers:
                for w in names:
                    env[w] = str(workers)
                    public[w] = str(workers)
        in_use = [engines.get(i) for i in dict.fromkeys([eid] + list(used.values()))]
        for u in in_use:
            if u.get("endpoint_env"):
                host = env.get(u["endpoint_env"]) or _os.environ.get(u["endpoint_env"]) or DEFAULT_OLLAMA_HOST
                env[u["endpoint_env"]] = host
                public[u["endpoint_env"]] = host
        for name in key_names:                        # a key no engine of this run reads stays empty
            env[name] = ""
        for u in in_use:
            key_env = u.get("key_env")
            if key_env:
                if not key.held(key_env):
                    raise NeedsKey(f"{u.get('label') or u.get('id', '')} needs {key_env}; hold a key in the banner under Engine Selection on the Mapping tab first")
                env[key_env] = key.get(key_env)
                public[key_env] = "(held in memory)"
    for k, v in (extra or {}).items():
        env[k] = str(v)
        public[k] = str(v)
    return env, public
