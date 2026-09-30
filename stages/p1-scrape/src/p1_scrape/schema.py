"""Load manifest.schema.json and coerce/validate rows against it.

`validate` (this schema) is the single source of truth for the manifest field
set — the prose in PLAN.md/INTERFACE_CONTRACT.md is a convenience restatement.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .models import INT_FIELDS, NULLABLE_BOOL_FIELDS, NULLABLE_INT_FIELDS, OPTIONAL_FIELDS

_REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = _REPO_ROOT / "contracts" / "schemas" / "manifest.schema.json"

_OPTIONAL = frozenset(OPTIONAL_FIELDS)


@lru_cache(maxsize=1)
def load_schema() -> dict[str, Any]:
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(
            f"manifest.schema.json not found at {SCHEMA_PATH} — vendor 00_contracts first (T0)."
        )
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def get_validator() -> Draft202012Validator:
    schema = load_schema()
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def _coerce_bool(val: Any) -> Any:
    if isinstance(val, bool) or val is None:
        return val
    s = str(val).strip().lower()
    if s in {"true", "1", "yes"}:
        return True
    if s in {"false", "0", "no"}:
        return False
    if s == "":
        return None
    return val  # let the schema reject anything else


def _coerce_int(val: Any) -> Any:
    if isinstance(val, int) or val is None:
        return val
    s = str(val).strip()
    if s == "":
        return None
    try:
        return int(s)
    except ValueError:
        return val


def coerce_csv_row(raw: dict[str, Any]) -> dict[str, Any]:
    """Turn a CSV string row into a typed dict the schema can validate.

    Empty strings in OPTIONAL fields become null; ints/bools are parsed.
    Required string fields keep '' (so the schema fails them loudly).
    """
    out: dict[str, Any] = {}
    for key, val in raw.items():
        if key in INT_FIELDS:
            out[key] = _coerce_int(val)
        elif key in NULLABLE_INT_FIELDS:
            out[key] = _coerce_int(val)
        elif key in NULLABLE_BOOL_FIELDS:
            out[key] = _coerce_bool(val)
        elif key in _OPTIONAL and (val is None or str(val) == ""):
            out[key] = None
        else:
            out[key] = val
    return out


def validate_row(row: dict[str, Any]) -> list[str]:
    """Return a list of human-readable schema errors for one typed row ([] if valid)."""
    validator = get_validator()
    errors = []
    for err in sorted(validator.iter_errors(row), key=lambda e: list(e.path)):
        loc = ".".join(str(p) for p in err.path) or "(row)"
        errors.append(f"{loc}: {err.message}")
    return errors
