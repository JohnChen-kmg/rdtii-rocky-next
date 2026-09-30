"""S2 candidate selection: a score threshold with a floor and a ceiling.

Replaces the nine hand-set integers in `src/p3map/select.py` (`CAPS`, `GRAY_MULT`,
`PREFILTER_FLOOR`). Derivation and verification against the Round 1 reference arm:
`rdtii-finale-3-mapping/notes/2026-09-26-selection-cap-function.md`. Measured there:
7,864 candidate pairs per economy against 13,627 for the caps, gold recall 37/37
unchanged, 0 of 27 economy scores changed, 120 of 135 filed evidence rows retained.

THE FUNCTION, for one economy `e` and one indicator `i`:

    theta_eff = theta[i] + language_offset[L]      L = language of e's corpus
    S         = { p in corpus(e) : cos(p, query[i]) >= theta_eff }, ordered by score desc
    N         = clip( |S| , min_candidates[i] , max_candidates[i] )
    direct    = the selected p with score >= direct_band   -> straight to the mapper
    gray      = the rest                                   -> cheap triage first

EVERY VARIABLE

    e                 economy code, e.g. "SG". From the run's task, never a hard-coded list.
    i                 indicator, decimal text, e.g. "7.3". Never float-parsed: 4.01 != 4.1.
    L                 language of the source document, e.g. "lao". Read from the crawler's
                      own field on the provision record; never detected from characters.
    cos(p, query[i])  dense cosine, BGE-M3, between the provision's prefilter text and the
                      indicator's query document (name + definition + keywords + exemplars,
                      built by `src/p3map/prefilter/queries.py`). Comparable across
                      indicators and economies, which is why it can carry a threshold:
                      every Round 1 filed row scored >= 0.540, and random provisions top
                      out at 0.51.
    theta[i]          per-indicator threshold, 0.53-0.62. Set from the 10th percentile of
                      that indicator's filed-row scores.
    language_offset   per-language correction, 0 to -0.03, measured on paired source/gloss
                      provisions. Negative lowers the threshold.
    min_candidates    the floor. A cell is always looked at this deeply, so a null result is
                      evidenced rather than assumed -- "no provision found" is a required
                      output, not an absence of one.
    max_candidates    the ceiling, and the budget guard. Flat per indicator: depth needed
                      does NOT scale with corpus size (Australia holds 3.85x Malaysia's
                      provisions and needed the same depth for 7.3 and 7.5).
    direct_band       0.65. Splits the selection into the two lanes.
    sparse_topup      how many BM25 hits to union in. Non-zero only for 6.4 and 7.3, the two
                      indicators whose sparse leg measurably beats their dense leg.

Corpus size never appears as a term. It enters through |S|, which measured a stable 6-8% of
provisions across three economies -- content-based, with no coefficient to fit and nothing to
inflate by adding boilerplate.

WHICH TERM BOUND the cell is recorded on every result, because it classifies the indicator
and it converts a silent truncation into a stated limit:

    "theta"      sparse indicator -- the threshold ran out of candidates before the ceiling
    "max"        diffuse indicator -- the ceiling truncated; the recall claim is bounded here
    "min"        nothing scored above the threshold; the floor took the best available
    "exhausted"  the economy's corpus holds fewer candidates than the floor asks for

Stdlib only, so the interface can read the same JSON.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Iterable, Sequence

from config.indicator_ids import normalize

CONFIG_PATH = Path(__file__).with_name("selection.json")

_REQUIRED = ("theta", "min_candidates", "max_candidates", "sparse_topup")
_BOUND_THETA, _BOUND_MAX, _BOUND_MIN, _BOUND_EMPTY = "theta", "max", "min", "exhausted"


class SelectionConfigError(ValueError):
    """The parameter file is missing or internally inconsistent."""


class UnknownIndicator(KeyError):
    """No parameters for this indicator, and no class to fall back to.

    Deliberately fatal, for the same reason an unpriced model is (decision M5): a silently
    defaulted threshold spends money and produces rows that look like every other row.
    """


@dataclass(frozen=True)
class CellParams:
    """The resolved parameters for one (economy, indicator, language) cell."""

    indicator: str
    economy: str
    language: str
    theta: float            # effective, after the language offset
    theta_base: float
    language_offset: float
    direct_band: float
    min_candidates: int
    max_candidates: int
    sparse_topup: int
    source: str             # "indicator", "class:<name>", or "override"


@dataclass(frozen=True)
class Selection:
    """What one cell hands on, and why it stopped."""

    direct: tuple[str, ...]
    gray: tuple[str, ...]
    bound: str
    params: CellParams

    @property
    def candidates(self) -> tuple[str, ...]:
        return self.direct + self.gray

    def __len__(self) -> int:
        return len(self.direct) + len(self.gray)

    def report(self) -> dict:
        """One line for `select_report.json`, so a missing row has one attributable cause."""
        return {
            "economy": self.params.economy,
            "indicator": self.params.indicator,
            "language": self.params.language,
            "candidates": len(self),
            "direct": len(self.direct),
            "gray": len(self.gray),
            "bound_by": self.bound,
            "theta_effective": round(self.params.theta, 4),
            "theta_base": self.params.theta_base,
            "language_offset": self.params.language_offset,
            "min_candidates": self.params.min_candidates,
            "max_candidates": self.params.max_candidates,
            "params_from": self.params.source,
        }


@lru_cache(maxsize=4)
def load_config(path: str | None = None) -> dict:
    p = Path(path) if path else CONFIG_PATH
    try:
        cfg = json.loads(p.read_text(encoding="utf-8"))
    except FileNotFoundError as e:
        raise SelectionConfigError(f"selection parameters not found: {p}") from e
    validate_config(cfg)
    return cfg


def validate_config(cfg: dict) -> None:
    """Fail loudly at load, not mid-run."""
    if "score" not in cfg or "direct_band" not in cfg["score"]:
        raise SelectionConfigError("score.direct_band is required")
    classes = {k: v for k, v in cfg.get("class_defaults", {}).items() if not k.startswith("_")}
    if not classes:
        raise SelectionConfigError("class_defaults is required")
    for name, block in classes.items():
        _check_block(f"class_defaults.{name}", block, require_all=True)
    for iid, block in _indicator_blocks(cfg).items():
        cls = block.get("class")
        if cls is not None and cls not in classes:
            raise SelectionConfigError(f"indicator {iid}: unknown class {cls!r}")
        _check_block(f"indicators.{iid}", block, require_all=cls is None)
    for econ, inds in _overrides(cfg).items():
        if not isinstance(inds, dict):
            raise SelectionConfigError(f"economy_overrides.{econ} must be an object")


def _check_block(where: str, block: dict, *, require_all: bool) -> None:
    if require_all:
        missing = [f for f in _REQUIRED if f not in block]
        if missing:
            raise SelectionConfigError(f"{where}: missing {', '.join(missing)}")
    if "theta" in block and not 0.0 < float(block["theta"]) < 1.0:
        raise SelectionConfigError(f"{where}: theta must be a cosine in (0, 1)")
    lo, hi = block.get("min_candidates"), block.get("max_candidates")
    if lo is not None and hi is not None and int(lo) > int(hi):
        raise SelectionConfigError(f"{where}: min_candidates {lo} exceeds max_candidates {hi}")
    for f in ("min_candidates", "max_candidates", "sparse_topup"):
        if f in block and int(block[f]) < 0:
            raise SelectionConfigError(f"{where}: {f} must not be negative")


def _indicator_blocks(cfg: dict) -> dict:
    return {k: v for k, v in cfg.get("indicators", {}).items() if not k.startswith("_")}


def _overrides(cfg: dict) -> dict:
    return {k: v for k, v in cfg.get("economy_overrides", {}).items() if not k.startswith("_")}


def language_offset(language: str | None, cfg: dict | None = None) -> float:
    """Offset for this language, or the conservative default for an unmeasured one."""
    cfg = cfg or load_config()
    table = cfg.get("language_offset", {})
    key = (language or "").strip().lower()
    if key in table and not key.startswith("_"):
        return float(table[key])
    return float(table.get("_default", 0.0))


def params_for(
    indicator,
    economy: str,
    language: str | None = None,
    *,
    indicator_class: str | None = None,
    cfg: dict | None = None,
) -> CellParams:
    """Resolve one cell's parameters.

    `indicator_class` supplies the class for an indicator with no measured entry -- the 52
    outside pillars 6 and 7. Assign it from the codebook (see selection.json), don't guess.
    """
    cfg = cfg or load_config()
    iid = normalize(indicator)
    blocks = _indicator_blocks(cfg)
    classes = {k: v for k, v in cfg.get("class_defaults", {}).items() if not k.startswith("_")}

    block: dict = {}
    source = ""
    if iid in blocks:
        block = dict(blocks[iid])
        source = "indicator"
        cls = block.get("class")
        if cls:
            block = {**classes[cls], **block}
    else:
        cls = indicator_class
        if cls is None:
            raise UnknownIndicator(
                f"no parameters for indicator {iid}; pass indicator_class "
                f"(one of {', '.join(sorted(classes))}) or add it to selection.json"
            )
        if cls not in classes:
            raise SelectionConfigError(f"unknown class {cls!r}")
        block = dict(classes[cls])
        source = f"class:{cls}"

    econ = (economy or "").strip().upper()
    override = _overrides(cfg).get(econ, {}).get(iid)
    if override:
        block = {**block, **{k: v for k, v in override.items() if not k.startswith("_")}}
        source = "override"

    _check_block(f"resolved {econ}:{iid}", block, require_all=True)
    base = float(block["theta"])
    offset = language_offset(language, cfg)
    return CellParams(
        indicator=iid,
        economy=econ,
        language=(language or "").strip().lower(),
        theta=round(base + offset, 6),
        theta_base=base,
        language_offset=offset,
        direct_band=float(cfg["score"]["direct_band"]),
        min_candidates=int(block["min_candidates"]),
        max_candidates=int(block["max_candidates"]),
        sparse_topup=int(block["sparse_topup"]),
        source=source,
    )


def select_cell(
    ranked: Iterable[tuple[str, float]],
    indicator,
    economy: str,
    language: str | None = None,
    *,
    indicator_class: str | None = None,
    sparse: Sequence[str] | None = None,
    cfg: dict | None = None,
) -> Selection:
    """Select one cell's candidates.

    `ranked` is (provision_id, score) for this economy and indicator, **ordered by score
    descending** -- one pass, so a generator is fine. `sparse` is the BM25 ranking for the
    same cell, used only where `sparse_topup` is non-zero.
    """
    p = params_for(indicator, economy, language, indicator_class=indicator_class, cfg=cfg)
    direct: list[str] = []
    gray: list[str] = []
    bound = _BOUND_EMPTY
    n = 0

    for pid, score in ranked:
        if n >= p.max_candidates:
            bound = _BOUND_MAX
            break
        if score >= p.theta:
            (direct if score >= p.direct_band else gray).append(pid)
            n += 1
            continue
        # below the threshold: keep taking only until the floor is met
        if n < p.min_candidates:
            gray.append(pid)          # a below-threshold pick is never sent straight to the mapper
            n += 1
            bound = _BOUND_MIN
            continue
        if bound != _BOUND_MIN:
            bound = _BOUND_THETA
        break
    else:
        # the ranking ran out before any limit applied
        bound = _BOUND_EMPTY if n < p.min_candidates else (
            _BOUND_MIN if bound == _BOUND_MIN else _BOUND_THETA)

    if sparse and p.sparse_topup:
        seen = set(direct) | set(gray)
        for pid in list(sparse)[: p.sparse_topup]:
            if pid not in seen:
                gray.append(pid)
                seen.add(pid)

    return Selection(direct=tuple(direct), gray=tuple(gray), bound=bound, params=p)


def indicators(cfg: dict | None = None) -> list[str]:
    """Indicators with measured parameters, in file order."""
    return list(_indicator_blocks(cfg or load_config()))


def classes(cfg: dict | None = None) -> list[str]:
    cfg = cfg or load_config()
    return [k for k in cfg.get("class_defaults", {}) if not k.startswith("_")]


if __name__ == "__main__":  # python -m config.selection
    c = load_config()
    print(f"selection.json v{c.get('version')} ({c.get('updated')}) — config valid")
    print(f"{'ind':6s} {'class':22s} {'theta':>6s} {'min':>5s} {'max':>6s} {'sparse':>7s}")
    for iid in indicators(c):
        p = params_for(iid, "SG", "eng", cfg=c)
        cls = _indicator_blocks(c)[iid].get("class", "-")
        print(f"{iid:6s} {cls:22s} {p.theta_base:6.2f} {p.min_candidates:5d} "
              f"{p.max_candidates:6d} {p.sparse_topup:7d}")
    print("\nlanguage offsets:", {k: v for k, v in c["language_offset"].items() if not k.startswith("_")})
    print("classes for unmeasured indicators:", ", ".join(classes(c)))
