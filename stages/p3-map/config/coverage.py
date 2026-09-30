r"""What this tool automates, and the sentence a row carries when it does not.

Decisions M8 and M9: for any indicator the instrument marks as not automated, the stage does not
run the mapper — it writes the row with one fixed sentence in Notes naming the reason category.
Both decisions say the mark comes from the instrument and never from a list here, so it does:

    status: out_of_scope        -> excluded, no row at all (instrument D10; only 6.5 today)
    in the automated set        -> automated: this stage maps it
    evidence: practice          -> manual check, "practice or external evidence" (3.4, 5.3, 9.1)
    otherwise in scope          -> manual check, "outside the automated scope" (the other 49)

One fact cannot come from the instrument, because it is about an economy's portal rather than an
indicator: where the tier that answers an automated indicator is not published, that economy gets
the manual mark for it too. That is China's pillar 6, evidenced in the coverage register
(`RDTII Finale Plan\3_Final_Stage\COVERAGE_AND_MANUAL_CHECKS.md`, hand-edited per-economy section):
the National Database of Laws and Regulations stops above departmental rules, so pillar 6 is
framework-only there. Pillar 7 is fully covered, 5 of 5, and is not marked.

The sentence is one string in one place, as M9 asks, and is quoted from the register.
"""
from __future__ import annotations

from dataclasses import dataclass

from config.indicator_ids import normalize, pillar_of

AUTOMATED, MANUAL, EXCLUDED = "A", "M", "X"

# Reason categories, in the words decision M9 fixes.
REASONS = {
    "scope": "outside the automated scope",
    "practice": "practice or external evidence",
    "portal_tier": "the tier that answers it is not published by this economy's portal",
}
SENTENCE = ("Not automated. The result for this indicator may come from a source other than the "
            "legal dataset. Check it outside the tool. Reason: {reason}.")
# A filed row whose indicator IS automated but whose operative tier the economy's portal does not
# publish: the verdict stands, the coverage is partial, and the row says so.
PARTIAL_SENTENCE = ("Framework-level only for this economy: the operative detail sits in a tier "
                    "its official portal does not publish, so check the result outside the tool.")

# Economy -> the pillars whose answers that economy's portal does not publish below the framework.
# Hand-edited, from the coverage register's per-economy section. Each entry needs evidence there.
PORTAL_TIER_GAPS: dict[str, tuple[int, ...]] = {
    "CN": (6,),
}


@dataclass(frozen=True)
class Coverage:
    indicator: str
    economy: str | None
    cls: str                  # AUTOMATED | MANUAL | EXCLUDED
    reason: str | None        # a key of REASONS, or None when fully automated
    partial: bool = False     # automated, but this economy's portal stops above the answer

    @property
    def automated(self) -> bool:
        return self.cls == AUTOMATED

    @property
    def note(self) -> str:
        """The sentence for Notes, or "" when there is nothing to disclose."""
        if self.reason is None:
            return ""
        if self.partial:
            return PARTIAL_SENTENCE
        return SENTENCE.format(reason=REASONS[self.reason])


def classify(indicator, economy: str | None = None) -> Coverage:
    from config.instrument import load
    ins = load()
    iid = normalize(indicator)
    econ = (economy or "").strip().upper() or None

    entries = {}
    if ins.order:
        for e in ins.order.get("indicators") or []:
            if isinstance(e, dict) and e.get("id") is not None:
                try:
                    entries[normalize(e["id"])] = e
                except Exception:      # an id this stage cannot read is not a classification
                    continue
    entry = entries.get(iid, {})

    if entry and (entry.get("status") or "in_scope") != "in_scope":
        return Coverage(iid, econ, EXCLUDED, None)
    if iid in ins.ids:
        gap = econ is not None and pillar_of(iid) in PORTAL_TIER_GAPS.get(econ, ())
        return Coverage(iid, econ, AUTOMATED, "portal_tier" if gap else None, partial=gap)
    # in the codebook but not automated, or not in the instrument at all: either way this stage
    # does not map it, and saying so is the honest answer
    reason = "practice" if (entry.get("evidence") == "practice") else "scope"
    return Coverage(iid, econ, MANUAL, reason)


def notification(indicator, economy: str | None = None) -> str:
    """The Notes sentence for one (indicator, economy), or "" when nothing needs disclosing."""
    return classify(indicator, economy).note


if __name__ == "__main__":   # python -m config.coverage
    from config.instrument import load
    ins = load()
    order = [e["id"] for e in (ins.order or {}).get("indicators", [])] or list(ins.ids)
    counts: dict[str, int] = {}
    for iid in order:
        c = classify(iid)
        counts[c.cls] = counts.get(c.cls, 0) + 1
    print(f"instrument at {ins.dir}")
    print(f"automated {counts.get(AUTOMATED, 0)} · manual {counts.get(MANUAL, 0)} · "
          f"excluded {counts.get(EXCLUDED, 0)}")
    for iid in order:
        c = classify(iid)
        if c.cls != AUTOMATED:
            print(f"  {c.cls} {iid:8s} {c.reason}")
    for econ, pillars in PORTAL_TIER_GAPS.items():
        for iid in ins.ids:
            c = classify(iid, econ)
            if c.partial:
                print(f"  partial {econ} {iid}: {c.note[:88]}")
