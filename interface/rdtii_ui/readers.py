"""Readers for what the stages write. Pure functions plus a small mtime cache.

Nothing here imports stage code. Every column value stays a string: indicator IDs are decimal text and a
`6.10` must never become `6.1`.
"""
from __future__ import annotations

import ast
import csv
import json
import re
import threading
from pathlib import Path

HOST_COLUMNS = (
    "Economy", "Law Name", "Law Number / Ref", "Last Amended", "Indicator ID", "Article / Section",
    "Discovery Tag", "Location Reference", "Verbatim Snippet", "Mapping Rationale", "Source URL",
    "Confidence", "Notes", "Language of Source",
)
NO_PROVISION_SNIPPET = "No provision found"
INVERTED_INDICATORS = ("7.1", "7.2")  # a score of 0 means the economy HAS a framework
AUTOMATED_PILLARS = (6, 7)  # decision M7: the automated set is pillars 6 and 7

FALLBACK_ECON_NAMES = {
    "SG": "Singapore", "AU": "Australia", "MY": "Malaysia",
    "CN": "China", "LA": "Lao PDR", "TL": "Timor-Leste",
}

_lock = threading.Lock()
_cache: dict[str, tuple[tuple, object]] = {}


def cached(path: Path, loader):
    """Load `path` through `loader`, re-reading only when its mtime or size changes. None if absent."""
    try:
        st = path.stat()
    except OSError:
        return None
    key = (st.st_mtime_ns, st.st_size)
    # keyed on the loader too: one file may be read two ways (indicator_order.yaml as the list and as its notes)
    skey = (str(path), getattr(loader, "__qualname__", None) or repr(loader))
    with _lock:
        hit = _cache.get(skey)
        if hit and hit[0] == key:
            return hit[1]
    value = loader(path)
    with _lock:
        _cache[skey] = (key, value)
    return value


# ---- primitive readers -------------------------------------------------------------------------

def read_csv(path: Path) -> tuple[list[str], list[dict]]:
    """UTF-8 with or without BOM. Every cell a string; missing cells become ''."""
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        header = list(reader.fieldnames or [])
        rows = []
        for raw in reader:
            rows.append({k: (v if v is not None else "") for k, v in raw.items() if k is not None})
        return header, rows


def read_jsonl(path: Path) -> list[dict]:
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def read_json(path: Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def count_lines(path: Path) -> int:
    n = 0
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            n += chunk.count(b"\n")
    return n


def dir_size(path: Path) -> int:
    total = 0
    for p in path.rglob("*"):
        try:
            if p.is_file():
                total += p.stat().st_size
        except OSError:
            pass
    return total


# ---- mapping-run files ----------------------------------------------------------------------

def records_csv(path: Path):
    return cached(path, read_csv)


def records_json_index(path: Path) -> dict:
    """records_<E>.json -> {(law, article, indicator): provision}. The JSON carries _provision_id."""
    def load(p: Path):
        doc = read_json(p)
        idx: dict = {}
        for law in doc.get("laws", []):
            for prov in law.get("provisions", []):
                key = (prov.get("Law Name", ""), prov.get("Article / Section", ""), str(prov.get("Indicator ID", "")))
                idx.setdefault(key, prov)
        return idx
    return cached(path, load) or {}


def gloss_index(path: Path) -> dict:
    """audit/gloss_<E>.jsonl -> by (provision_id, indicator) and by (law, article, indicator)."""
    def load(p: Path):
        by_pid: dict = {}
        by_key: dict = {}
        rows = read_jsonl(p)
        for g in rows:
            by_pid.setdefault((g.get("provision_id"), str(g.get("indicator", ""))), g)
            by_key.setdefault((g.get("law_name", ""), g.get("article_section", ""), str(g.get("indicator", ""))), []).append(g)
        return {"by_pid": by_pid, "by_key": by_key, "total": len(rows),
                "not_literal": sum(1 for g in rows if g.get("is_literal") is False)}
    return cached(path, load) or {"by_pid": {}, "by_key": {}, "total": 0, "not_literal": 0}


def sections_index(path: Path) -> dict:
    """audit/gloss_sections_<E>.jsonl -> by provision_id and by (law, article)."""
    def load(p: Path):
        by_pid: dict = {}
        by_key: dict = {}
        rows = read_jsonl(p)
        for g in rows:
            by_pid.setdefault(g.get("provision_id"), g)
            by_key.setdefault((g.get("law_name", ""), g.get("article_section", "")), []).append(g)
        return {"by_pid": by_pid, "by_key": by_key, "total": len(rows),
                "not_literal": sum(1 for g in rows if g.get("is_literal") is False)}
    return cached(path, load) or {"by_pid": {}, "by_key": {}, "total": 0, "not_literal": 0}


def verified_index(path: Path) -> dict:
    """verify/verified_<E>.jsonl -> {(provision_id, indicator): row}."""
    def load(p: Path):
        idx: dict = {}
        for v in read_jsonl(p):
            idx.setdefault((v.get("provision_id"), str(v.get("indicator", ""))), v)
        return idx
    return cached(path, load) or {}


def rollup(path: Path) -> dict:
    return cached(path, read_json) or {}


def run_manifest(path: Path) -> dict:
    return cached(path, read_json) or {}


def manifest_engine_label(manifest: dict) -> str:
    eng = manifest.get("engine") or {}
    if eng.get("engine_id"):
        return str(eng.get("label") or f"Engine {eng['engine_id']}")
    roles = eng.get("roles") or {}
    mapper = roles.get("mapper") or {}
    model = mapper.get("model") if isinstance(mapper, dict) else mapper
    if eng.get("provider") or model:
        return f"{eng.get('provider', '')}: {model or '?'}".strip(": ")
    return ""


def manifest_cost(manifest: dict) -> float:
    return round(sum(float(e.get("cost_usd") or 0) for e in manifest.get("entries", [])), 4)


# ---- the stage's economy table, read as text ------------------------------------------------

def econ_names(p3_dir: Path) -> dict[str, str]:
    """ECON_NAME from stages/p3-map/config/economies.py, without importing it."""
    path = p3_dir / "config" / "economies.py"

    def load(p: Path):
        text = p.read_text(encoding="utf-8")
        m = re.search(r"^ECON_NAME\s*=\s*(\{.*?^\})", text, re.S | re.M)
        if not m:
            return dict(FALLBACK_ECON_NAMES)
        try:
            return dict(ast.literal_eval(m.group(1)))
        except (ValueError, SyntaxError):
            return dict(FALLBACK_ECON_NAMES)
    return cached(path, load) or dict(FALLBACK_ECON_NAMES)


# ---- the instrument's ordered indicator list, a tiny YAML reader for one known shape ------------

_KEY_LINE = re.compile(r"^  [a-z_]+:")


def _scalar(raw: str):
    s = raw.strip()
    if s in ("", "null", "~"):
        return None
    if len(s) >= 2 and s[0] == s[-1] and s[0] in "'\"":
        inner = s[1:-1]
        return inner.replace("''", "'") if s[0] == "'" else inner
    if re.fullmatch(r"-?\d+", s):
        return int(s)
    return s


def parse_indicator_order(path: Path) -> dict:
    """indicator_order.yaml -> {"meta": {...}, "indicators": [{id, pillar, pillar_label, name, status, ...}]}.

    Handles exactly the file's shape: a top-level `indicators:` list of flat mappings whose long values
    wrap onto more-indented continuation lines. Not a general YAML parser.
    """
    def load(p: Path):
        meta: dict = {}
        items: list[dict] = []
        cur: dict | None = None
        last_key: str | None = None
        in_list = False
        for raw in p.read_text(encoding="utf-8").splitlines():
            if not raw.strip() or raw.lstrip().startswith("#"):
                continue
            if not raw.startswith((" ", "-")):
                key, _, val = raw.partition(":")
                in_list = key.strip() == "indicators"
                if not in_list and val.strip():
                    meta[key.strip()] = _scalar(val)
                cur = None
                continue
            if not in_list:
                continue
            if raw.startswith("- "):
                cur = {}
                items.append(cur)
                body = raw[2:]
            elif _KEY_LINE.match(raw):
                body = raw.strip()
            else:
                if cur is not None and last_key:
                    cur[last_key] = (cur[last_key] + " " + raw.strip()).strip()
                continue
            key, _, val = body.partition(":")
            last_key = key.strip()
            cur[last_key] = val.strip()
        for it in items:
            for k, v in list(it.items()):
                it[k] = _scalar(v) if isinstance(v, str) else v
            it["id"] = str(it.get("id", ""))
        return {"meta": meta, "indicators": items}
    return cached(path, load) or {"meta": {}, "indicators": []}


def codebook_tiers(path: Path) -> dict[str, str]:
    """indicator id -> tier letter, from the codebook's blocks (`- id: "6.1"` followed by `tier: A`)."""
    def load(p: Path) -> dict[str, str]:
        text = p.read_text(encoding="utf-8")
        out: dict[str, str] = {}
        for m in re.finditer(r'^  - id: "([^"]+)"\n(?:(?!  - id:).*\n){0,6}?\s*tier: ([A-Za-z])', text, re.M):
            out[m.group(1)] = m.group(2).upper()
        return out
    return cached(path, load) or {}


def codebook_tier_notes(path: Path) -> dict[str, str]:
    """tier letter -> the codebook's own description, from its top-level `tiers:` block (folded YAML text)."""
    def load(p: Path) -> dict[str, str]:
        text = p.read_text(encoding="utf-8")
        m = re.search(r"^tiers:\n((?:  .*\n|\n)+?)(?=^\S)", text, re.M)
        if not m:
            return {}
        out: dict[str, str] = {}
        for tier, body in re.findall(r"^  ([A-Z]): >\n((?:    .*\n)+)", m.group(1), re.M):
            out[tier] = re.sub(r"\s+", " ", body).strip()
        return out
    return cached(path, load) or {}


def practice_based(path: Path) -> dict[str, str]:
    """indicator id -> the instrument's reason, from indicator_order.yaml's practice_based map."""
    def load(p: Path) -> dict[str, str]:
        text = p.read_text(encoding="utf-8")
        m = re.search(r"^practice_based:\n((?:  .*\n)+)", text, re.M)
        if not m:
            return {}
        pairs = re.findall(r"^  '([^']+)':\s*'(.*?)'\s*$", m.group(1), re.M | re.S)
        return {k: re.sub(r"\s+", " ", v).strip() for k, v in pairs}
    return cached(path, load) or {}


def automated_ids(order: dict) -> list[str]:
    """The automated set, the way stages/p3-map/config/instrument.py derives it: entries marked
    `coverage: automated` when any are (instrument decision D14), else pillars 6 and 7 (decision M7)."""
    entries = [it for it in order.get("indicators", []) if it.get("status", "in_scope") == "in_scope"]
    marked = [it for it in entries if str(it.get("coverage") or "").strip().lower() == "automated"]
    chosen = marked or [it for it in entries if it.get("pillar") in AUTOMATED_PILLARS]
    return [it["id"] for it in chosen]
