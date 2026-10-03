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
from pathlib import Path
from .paths import child_path
from .probes import tool_path_dirs

ALLOWLIST = (
    "LLM_PROVIDER", "LLM_MODEL", "VERIFIER_MODEL", "ESCALATION_MODEL", "TRIAGE_MODEL",
    "OLLAMA_MODEL", "OLLAMA_HOST", "OCR_ENGINE", "RDTII_ENGINE",
)
SECRET_MARKERS = ("KEY", "TOKEN", "SECRET", "PASSWORD")


class KeyHolder:
    """Holds the API key in process memory for the lifetime of the server. Never written, never rendered."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._key = ""
        self._set_at: float | None = None

    def set(self, key: str) -> None:
        key = (key or "").strip()
        if not key or not re.fullmatch(r"[\x21-\x7e]{8,400}", key):
            raise ValueError("a key is 8 to 400 printable characters with no spaces")
        with self._lock:
            self._key = key
            self._set_at = time.time()

    def clear(self) -> None:
        with self._lock:
            self._key = ""
            self._set_at = None

    def get(self) -> str:
        with self._lock:
            return self._key

    def held(self) -> bool:
        with self._lock:
            return bool(self._key)

    def public(self) -> dict:
        with self._lock:
            return {"held": bool(self._key), "set_at": self._set_at}

    def redact(self, line: str) -> str:
        k = self.get()
        return line.replace(k, "[key redacted]") if k and k in line else line


def load_engines(p3_dir: Path) -> dict | None:
    path = p3_dir / "config" / "llm" / "engines.json"
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

    def public(self) -> dict:
        with self._lock:
            sel = self.selected
        engines = []
        for eid, e in self.doc.get("engines", {}).items():
            engines.append({
                "id": eid, "label": e.get("label", eid), "provider": e.get("provider"),
                "open_weights": bool(e.get("open_weights")), "roles": e.get("roles", {}),
                "workers": e.get("workers"), "batch_lane": bool(e.get("batch_lane")),
                "digest": e.get("digest"), "key_env": e.get("key_env"), "endpoint_env": e.get("endpoint_env"),
            })
        return {"selected": sel, "default": self.doc.get("default"), "declared_in": self.doc.get("_path"),
                "engines": engines}


# ---- the environment a stage process receives ---------------------------------------------------------

import os as _os  # noqa: E402

PROVIDERS = ("anthropic", "ollama")
DEFAULT_OLLAMA_HOST = "http://localhost:11434"


class ChoiceError(ValueError):
    """The browser named a variable or a value the server does not offer."""


class NeedsKey(RuntimeError):
    """The chosen engine needs an API key and none is held."""


def enumerate_values(name: str, engines: EngineState, ollama_models: list[str] | None = None) -> set[str]:
    """Every value the server will accept for one allowlisted name. Anything else is refused."""
    if name == "RDTII_ENGINE":
        return set(engines.ids())
    if name == "LLM_PROVIDER":
        return set(PROVIDERS)
    if name in ("LLM_MODEL", "VERIFIER_MODEL", "ESCALATION_MODEL", "TRIAGE_MODEL", "OLLAMA_MODEL"):
        vals = set(ollama_models or [])
        for e in engines.doc.get("engines", {}).values():
            vals.update(str(v) for v in (e.get("roles") or {}).values())
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


def build_env(stage: str, engines: EngineState, key: KeyHolder, choices: dict | None = None,
              extra: dict | None = None, ollama_models: list[str] | None = None,
              with_engine: bool = True) -> tuple[dict, dict]:
    """(env, public): the child environment and the non-secret part of it the page may show.

    Every allowlisted name and the key are removed first and set explicitly, because the stages load
    their own .env without overriding, so a stray file could otherwise decide a run. A stage that uses
    no AI engine (the crawler) passes with_engine=False and never needs a key.
    """
    env = _os.environ.copy()
    for name in ALLOWLIST + ("ANTHROPIC_API_KEY",):
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
        workers = e.get("workers")
        if workers:
            for w in ("MAP_WORKERS", "VERIFY_WORKERS", "TRIAGE_WORKERS"):
                env[w] = str(workers)
                public[w] = str(workers)
        if e.get("endpoint_env"):
            host = env.get(e["endpoint_env"]) or _os.environ.get(e["endpoint_env"]) or DEFAULT_OLLAMA_HOST
            env[e["endpoint_env"]] = host
            public[e["endpoint_env"]] = host
        key_env = e.get("key_env")
        if key_env:
            if not key.held():
                raise NeedsKey(f"engine {eid} ({e.get('label', '')}) needs {key_env}; hold a key in the banner under Engine Selection on the Mapping tab first")
            env[key_env] = key.get()
            public[key_env] = "(held in memory)"
        else:
            env["ANTHROPIC_API_KEY"] = ""
    for k, v in (extra or {}).items():
        env[k] = str(v)
        public[k] = str(v)
    return env, public
