"""One normalising view of the vendored instrument.

Every module that needs the codebook goes through here, and everything it returns is keyed by
**decimal-text indicator ID** (`6.1`, `4.01`, `12.4.1`) whatever the vendored files happen to use.
That is the point: the stage works unchanged against either vintage —

    Round 1 (vendored today)      ids `P6-I1`, no `indicator_order.yaml`, no `level` on a block,
                                  signature files `signatures/P6-I1.yaml`
    finale (waiting on hand-off)  ids `6.1`, `indicator_order.yaml` with 62 entries, `level` on
                                  7.1 and 7.2, signature files `signatures/6.1.yaml`

— so the instrument hand-off becomes a file swap with no code change, and the stage can be tested
before the swap. Nothing here parses an ID as a number: `4.01` and `4.1` are different indicators
(`config/indicator_ids.py`).

The automated set is whichever indicators this stage actually maps. It comes from
`indicator_order.yaml`'s `coverage` mark when that is populated (instrument decision D14, still
null on all 62 entries as of 2026-09-27), and otherwise from pillars 6 and 7 with
`status: in_scope` — which is the same nine either way, and is the scope decision M7.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Iterator

import yaml

from config.indicator_ids import BadIndicatorId, normalize

# Fallbacks for facts the Round 1 instrument does not carry as fields. Each is derived from the
# finale instrument when it is vendored, so these apply only pre-hand-off.
_ECONOMY_LEVEL_FALLBACK = frozenset({"7.1", "7.2"})   # "answer once per economy"
_INVERTED_FALLBACK = frozenset({"7.1", "7.2"})        # "Lack of ..." — absence scores 1
_ID_IN_PROSE = re.compile(r"\b\d{1,2}\.\d{1,2}(?:\.\d{1,2})?\b")

# A Round 1 design choice, not an instrument field: several verified half-point measures in one
# cell justify a 1. Kept here, keyed decimally, so no module carries its own legacy copy.
ESCALATION_IDS = frozenset({"6.1", "6.2"})


class InstrumentError(RuntimeError):
    """The vendored instrument is missing or unreadable."""


def from_artifact(raw) -> str:
    """An indicator id as a run artifact wrote it, normalised to decimal text.

    Round 1's verdicts, verifications and discovery files say "P6-I1". The reuse path reads
    those files, and so does any re-emit, so every read normalises instead of trusting the
    writer's vintage -- otherwise a join silently matches nothing and the stage emits an empty
    CSV while reporting success. An id that cannot be normalised is returned unchanged: it then
    matches no indicator, which is what a stale artifact should do.
    """
    try:
        return normalize(raw)
    except BadIndicatorId:
        return str(raw)


@dataclass(frozen=True)
class Instrument:
    dir: Path
    vintage: str                      # "decimal" or "legacy"
    ids: tuple[str, ...]              # the automated set, host order, decimal text
    blocks: dict = field(repr=False)  # decimal id -> codebook block
    policies: dict = field(repr=False)
    top: dict = field(repr=False)     # indicators.yaml top level, minus the block list
    inverted: frozenset = frozenset()  # "Lack of ..." indicators, resolved at load
    order: dict | None = field(repr=False, default=None)

    # ---- codebook ----------------------------------------------------------------
    def block(self, iid) -> dict:
        key = normalize(iid)
        try:
            return self.blocks[key]
        except KeyError:
            raise InstrumentError(
                f"indicator {key} has no codebook block in {self.dir}; vendored vintage is "
                f"{self.vintage} with {len(self.blocks)} blocks"
            ) from None

    def name(self, iid) -> str:
        return str(self.block(iid).get("name") or normalize(iid))

    def tier(self, iid) -> str | None:
        return self.block(iid).get("tier")

    def level(self, iid) -> str:
        """"economy" answers once per economy; "provision" answers per provision."""
        key = normalize(iid)
        declared = self.block(key).get("level")
        if declared:
            return str(declared)
        return "economy" if key in _ECONOMY_LEVEL_FALLBACK else "provision"

    def is_binary(self, iid) -> bool:
        """True when the scoring tree offers no 0.5 — presence alone decides the cell."""
        scoring = self.block(iid).get("scoring") or {}
        values = scoring.get("values") if isinstance(scoring, dict) else None
        if not values:
            return False
        return not any(abs(float(v) - 0.5) < 1e-9 for v in values)

    def is_inverted(self, iid) -> bool:
        """True for a "Lack of ..." indicator, where an absent framework scores 1."""
        return normalize(iid) in self.inverted

    # ---- retrieval material ------------------------------------------------------
    def signature(self, iid) -> dict:
        """Signature for one indicator, by decimal filename or the legacy one."""
        key = normalize(iid)
        for stem in self._signature_stems(key):
            p = self.dir / "signatures" / f"{stem}.yaml"
            if p.exists():
                sig = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
                sig["indicator"] = key      # normalise, whatever the file says
                return sig
        raise InstrumentError(
            f"no signature file for {key} in {self.dir / 'signatures'} "
            f"(tried {', '.join(self._signature_stems(key))})"
        )

    def signatures(self) -> dict[str, dict]:
        return {iid: self.signature(iid) for iid in self.ids}

    @staticmethod
    def _signature_stems(key: str) -> list[str]:
        from config.indicator_ids import legacy_of
        stems = [key]
        legacy = legacy_of(key)
        if legacy:
            stems.append(legacy)
        return stems

    # ---- gold set ----------------------------------------------------------------
    def gold(self) -> Iterator[dict]:
        """Gold rows with `indicator` normalised. Evaluation only — never a decision input."""
        path = self.dir / "gold" / "gold_set.jsonl"
        if not path.exists():
            return
        with path.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)
                raw = row.get("indicator_id") or row.get("indicator")
                try:
                    row["indicator"] = normalize(raw)
                except BadIndicatorId:
                    row["indicator"] = None
                yield row


def _inverted_ids(policies: dict, blocks: dict) -> frozenset:
    """The "Lack of ..." indicators, read out of the polarity note.

    `scoring_policy.polarity` is prose in both vintages — the finale one names eleven inverted
    and three absence-based IDs inside a sentence — so the IDs are lifted out and intersected
    with the blocks actually present. A request for a machine-readable list is open with the
    instrument workstream; until then this is deterministic and testable.
    """
    prose = str((policies.get("scoring_policy") or {}).get("polarity") or "")
    found = set()
    for raw in _ID_IN_PROSE.findall(prose):
        try:
            found.add(normalize(raw))
        except BadIndicatorId:
            continue
    found &= set(blocks)
    return frozenset(found or _INVERTED_FALLBACK)


def _automated_ids(order: dict | None, blocks: dict) -> tuple[str, ...]:
    if not order:
        # Round 1 instrument: the blocks it carries *are* the automated set.
        return tuple(blocks)
    entries = [e for e in (order.get("indicators") or []) if isinstance(e, dict)]
    marked = [e for e in entries if (e.get("coverage") or "").strip().lower() == "automated"]
    if marked:                                   # instrument decision D14, once populated
        chosen = marked
    else:                                        # scope decision M7: pillars 6 and 7
        chosen = [e for e in entries
                  if str(e.get("pillar")) in ("6", "7")
                  and (e.get("status") or "in_scope") == "in_scope"]
    out = []
    for e in chosen:
        try:
            key = normalize(e["id"])
        except (KeyError, BadIndicatorId):
            continue
        if key in blocks:
            out.append(key)
    return tuple(out)


@lru_cache(maxsize=4)
def load(instrument_dir: str | None = None) -> Instrument:
    from config.settings import SETTINGS
    d = Path(instrument_dir) if instrument_dir else SETTINGS.instrument_dir
    ind_path = d / "indicators.yaml"
    if not ind_path.exists():
        raise InstrumentError(f"no indicators.yaml in {d}")
    doc = yaml.safe_load(ind_path.read_text(encoding="utf-8")) or {}
    raw_blocks = doc.get("indicators") or []
    blocks: dict[str, dict] = {}
    for b in raw_blocks:
        try:
            blocks[normalize(b["id"])] = b
        except (KeyError, BadIndicatorId):
            continue
    if not blocks:
        raise InstrumentError(f"indicators.yaml in {d} carries no readable indicator IDs")

    pol_path = d / "policies.yaml"
    policies = yaml.safe_load(pol_path.read_text(encoding="utf-8")) if pol_path.exists() else {}

    order_path = d / "indicator_order.yaml"
    order = yaml.safe_load(order_path.read_text(encoding="utf-8")) if order_path.exists() else None

    vintage = "decimal" if order is not None else "legacy"
    top = {k: v for k, v in doc.items() if k != "indicators"}
    policies = policies or {}
    return Instrument(dir=d, vintage=vintage, ids=_automated_ids(order, blocks),
                      blocks=blocks, policies=policies, top=top,
                      inverted=_inverted_ids(policies, blocks), order=order)


if __name__ == "__main__":  # python -m config.instrument
    ins = load()
    print(f"instrument at {ins.dir}")
    print(f"vintage {ins.vintage} · {len(ins.blocks)} blocks · automated set {len(ins.ids)}")
    print(f"{'id':8s} {'level':10s} {'binary':7s} {'inv':4s} {'tier':5s} name")
    for iid in ins.ids:
        print(f"{iid:8s} {ins.level(iid):10s} {str(ins.is_binary(iid)):7s} "
              f"{str(ins.is_inverted(iid)):4s} {str(ins.tier(iid) or '-'):5s} {ins.name(iid)[:44]}")
    g = list(ins.gold())
    seen = sorted({r["indicator"] for r in g if r["indicator"]})
    print(f"gold rows: {len(g)}; indicators seen: {seen}")
