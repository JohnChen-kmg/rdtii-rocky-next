"""Named engines: one declaration, selected by RDTII_ENGINE.

Submission checklist item 9 asks that "the AI model backend is swappable from inside the
interface, with no code or config change", and C5b's four marks are awarded for showing the swap
happen. That needs one name an interface can set — not four model variables and a provider.

    RDTII_ENGINE=A   the hosted Claude stack
    RDTII_ENGINE=B   the open-weights stack, pinned by digest
    unset            the stage behaves exactly as it did before engines existed: LLM_PROVIDER and
                     the four model variables, read directly

Since 2026-10-04 a role may be given an engine of its own (RDTII_ENGINE_MAPPER, _VERIFIER,
_ESCALATION), and the declaration lists, per engine, the models a role may be given and their
price cards. Engines C, D and E speak the OpenAI-compatible chat API; none of them has been
measured, and the declaration says so (`measured: false`).

Precedence, highest first:

    1. an explicit `model=` argument          (the A/B harnesses pin two models of one provider)
    2. an explicitly set model variable       (LLM_MODEL, VERIFIER_MODEL, ...)
    3. the selected engine's role model       (engines.json)
    4. the settings default                   (the pre-engine path)

Rule 2 is deliberate and is why this module reads os.environ rather than Settings: "did the
operator set this variable" is a question about the environment, and a Settings field cannot
distinguish a value that was set from a default that looks the same.

Nothing here talks to a model or validates a key; `config/llm/factory.py` still owns that, and
decision #3 (a local model never maps, verifies or breaks a tie) is enforced there.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

CONFIG_PATH = Path(__file__).with_name("engines.json")
ENGINE_ENV = "RDTII_ENGINE"
# An alternative declaration, the way SELECTION_CONFIG names an alternative parameter file: an
# engine can be added or re-pointed for one run without editing the tracked file.
ENGINES_FILE_ENV = "RDTII_ENGINES_FILE"
# Which variable overrides which role. The names are Round 1's and are kept: they appear in
# .env.example, in the runbook and in the A/B harnesses.
ROLE_ENV = {"mapper": "LLM_MODEL", "verifier": "VERIFIER_MODEL",
            "escalation": "ESCALATION_MODEL", "triage": "TRIAGE_MODEL"}
# A role may be given its own engine (added 2026-10-04): reading on one provider, re-checking on
# another. Unset, the role follows RDTII_ENGINE, so a run that names one engine resolves exactly
# as it did before. triage has none: it is local by decision #3.
ROLE_ENGINE_ENV = {"mapper": "RDTII_ENGINE_MAPPER", "verifier": "RDTII_ENGINE_VERIFIER",
                   "escalation": "RDTII_ENGINE_ESCALATION"}


class EngineError(ValueError):
    """The engine declaration is missing, unreadable, or names an engine that is not declared."""


@dataclass(frozen=True)
class Engine:
    id: str
    label: str
    provider: str
    open_weights: bool
    roles: dict
    workers: int
    key_env: str | None
    endpoint_env: str | None
    batch_lane: bool
    digest: str | None = None
    base_url: str | None = None                         # openai_compat engines only
    request: dict = field(default_factory=dict)         # how that provider wants a request shaped
    models: tuple = ()                                  # the models a role may be given, with prices
    measured: bool = True                               # False: the pipeline was never scored on it

    def spec(self, model: str) -> dict:
        """The declared entry of one of this engine's models, or {} for a model it does not list."""
        return next((dict(m) for m in self.models if m.get("id") == model), {})

    def request_for(self, model: str) -> dict:
        """The engine's request shape with the model's own settings laid over it."""
        spec = self.spec(model)
        out = {**self.request, **(spec.get("request") or {})}
        out["extra"] = {**(self.request.get("extra") or {}), **((spec.get("request") or {}).get("extra") or {})}
        out["max_tokens_extra"] = int(spec.get("max_tokens_extra") or 0)
        return out

    def model_for(self, role: str) -> str:
        """The engine's model for one role, with an explicitly set variable taking precedence."""
        override = os.environ.get(ROLE_ENV.get(role, ""), "").strip()
        if override:
            return override
        try:
            return self.roles[role]
        except KeyError:
            raise EngineError(
                f"engine {self.id} declares no model for role {role!r}; "
                f"declared roles: {', '.join(sorted(self.roles))}") from None

    def as_manifest(self) -> dict:
        """What the run record should carry about this engine."""
        return {"engine_id": self.id, "label": self.label, "provider": self.provider,
                "open_weights": self.open_weights, "digest": self.digest,
                "roles": {r: self.model_for(r) for r in self.roles}}


def load(path: str | None = None) -> dict:
    return _load(str(path or os.environ.get(ENGINES_FILE_ENV, "").strip() or CONFIG_PATH))


@lru_cache(maxsize=4)
def _load(path: str) -> dict:
    p = Path(path)
    try:
        doc = json.loads(p.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise EngineError(f"no engine declaration at {p}") from None
    except json.JSONDecodeError as e:
        raise EngineError(f"engine declaration at {p} is not valid JSON: {e}") from None
    engines = doc.get("engines") or {}
    if not engines:
        raise EngineError(f"engine declaration at {p} declares no engines")
    for eid, block in engines.items():
        missing = [k for k in ("provider", "roles", "open_weights") if k not in block]
        if missing:
            raise EngineError(f"engine {eid} is missing {', '.join(missing)}")
    return doc


def ids(path: str | None = None) -> list[str]:
    return list(load(path)["engines"])


def get(engine_id: str, path: str | None = None) -> Engine:
    doc = load(path)
    key = str(engine_id).strip()
    block = doc["engines"].get(key) or doc["engines"].get(key.upper())
    if block is None:
        raise EngineError(
            f"{ENGINE_ENV}={engine_id!r} is not a declared engine; declared: "
            f"{', '.join(doc['engines'])}. An engine needs an entry in engines.json, and a "
            f"provider branch and a price card before it can be used.")
    return Engine(
        id=block.get("id", key), label=block.get("label", key),
        provider=str(block["provider"]).strip().lower(),
        open_weights=bool(block["open_weights"]), roles=dict(block["roles"]),
        workers=int(block.get("workers", 1)),
        key_env=block.get("key_env"), endpoint_env=block.get("endpoint_env"),
        batch_lane=bool(block.get("batch_lane", False)),
        digest=block.get("digest"),
        base_url=block.get("base_url"), request=dict(block.get("request") or {}),
        models=tuple(block.get("models") or ()), measured=bool(block.get("measured", True)))


def default_id(path: str | None = None) -> str:
    doc = load(path)
    return doc.get("default") or next(iter(doc["engines"]))


def selected(path: str | None = None, role: str | None = None) -> Engine | None:
    """The engine RDTII_ENGINE names, or None when it is unset.

    None is not an error and not a fallback to the default: with no engine named, the stage reads
    LLM_PROVIDER and the model variables exactly as it did before this file existed. That is what
    keeps a run started yesterday reproducible today.

    With `role`, the engine that role was given on its own (ROLE_ENGINE_ENV) comes first.
    """
    raw = os.environ.get(ROLE_ENGINE_ENV.get(role or "", ""), "").strip() if role else ""
    raw = raw or os.environ.get(ENGINE_ENV, "").strip()
    if not raw:
        return None
    return get(raw, path)


def spec_of(model: str, path: str | None = None) -> dict:
    """The declared entry of a model, whichever engine lists it; {} for one no engine lists."""
    for block in load(path)["engines"].values():
        for m in block.get("models") or ():
            if m.get("id") == model:
                return dict(m)
    return {}


def price_cards(path: str | None = None) -> dict:
    """model -> (input, output, cache read, cache write) in $/MTok, for every declared model that
    carries a card. config/llm/base.py keeps its own three and asks here for the rest."""
    out: dict = {}
    for block in load(path)["engines"].values():
        for m in block.get("models") or ():
            price = m.get("price")
            if isinstance(price, (list, tuple)) and len(price) == 4:
                out.setdefault(m["id"], tuple(float(x) for x in price))
    return out


if __name__ == "__main__":   # python -m config.llm.engines
    doc = load()
    print(f"engines.json v{doc.get('version')} · default {default_id()} · "
          f"selected {os.environ.get(ENGINE_ENV) or '(none — pre-engine path)'}")
    for eid in ids():
        e = get(eid)
        print(f"\n[{e.id}] {e.label}")
        print(f"  provider {e.provider}  open_weights {e.open_weights}  workers {e.workers}"
              f"  batch_lane {e.batch_lane}")
        if e.digest:
            print(f"  digest {e.digest}")
        for role in doc["roles"]:
            mark = "" if not os.environ.get(ROLE_ENV.get(role, ""), "").strip() else "  <- env"
            print(f"  {role:<10s} {e.model_for(role)}{mark}")
