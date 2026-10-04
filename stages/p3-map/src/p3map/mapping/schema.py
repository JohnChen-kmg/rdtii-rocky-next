"""Mapping-verdict schema (KICKOFF decision #5).

Field ORDER encodes the human coder's decision procedure — the model must answer
the core legal question and run the trap checks BEFORE emitting applies/score:
core_legal_question_answer -> who_is_regulated -> conditions_and_exceptions ->
trap_checks -> per-candidate verdicts. Closed 9-ID vocabulary; rationale <=300.
"""
from __future__ import annotations

import json

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from config.indicator_ids import pillar_of
from config.instrument import load as load_instrument
from config.settings import INDICATORS

# The scores a verdict may carry are the run's own scope's: the union of its blocks' scales, read
# from each block's `scoring.values` (second instrument hand-off, 4 October 2026: 23 indicators are
# binary, 3.1 and 5.2 add 0.8, 3.4 and 5.4 add 0.25, 1.4 has five steps). The union, not each
# indicator's own list, because one document is sent for the whole run -- and because for the nine
# indicators of pillars 6 and 7 the union is 1 / 0.5 / 0, so the document they are sent has not
# moved by a byte. Whether a value belongs to ITS indicator is checked where scores are used
# (rollup.py), against the block.
SCORE_LABELS: tuple[str, ...] = (*load_instrument().labels(INDICATORS), "n/a")
_MEASURED_LABELS = ("1", "0.5", "0", "n/a")
_SCORE_HINT_TEXT = (
    "The scoring-tree branch outcome for THIS provision: one of '1', "
    "'0.5', '0', 'n/a'. Economy rollup happens downstream; binary indicators "
    "never 0.5." if SCORE_LABELS == _MEASURED_LABELS else
    "The scoring-tree branch outcome for THIS provision: one of "
    + ", ".join(f"'{x}'" for x in SCORE_LABELS)
    + ". Use only a value the indicator's own scoring tree offers. Economy rollup happens downstream.")


NARRATIVE_FIELDS = ("core_legal_question_answer", "who_is_regulated",
                    "conditions_and_exceptions")
# Fields the validator DERIVES from the answer rather than asks the model for. They are popped out
# of the schema the model is sent (_schema_requiring_traps), so adding one here cannot change what
# the model is asked for, and so cannot change how the model behaves.
DERIVED_FIELDS = ("narrative_gaps",)


class TrapChecks(BaseModel):
    """Explicit booleans, one per catalogued trap (PLAN §4.3 + instrument)."""
    conditional_path_exists: bool | None = Field(
        default=None,
        description="True if a compliant transfer path exists (conditions/consent/"
        "adequacy) -> 6.4 territory, NOT a 6.1 ban.")
    retention_is_minimum: bool | None = Field(
        default=None,
        description="True ONLY if the provision sets a MINIMUM retention period "
        "('at least X'/'not less than X'). Maximum/'no longer than necessary'/"
        "destroy-after rules are NOT 7.3.")
    government_data_only: bool | None = Field(
        default=None,
        description="True if the obligation applies only to government/public-"
        "sector data (not scored for 6.1-6.4, 7.3).")
    provision_in_force: bool | None = Field(
        default=None,
        description="False if the text is enacted-but-not-commenced, repealed, "
        "or a bill (enforced-only rule).")
    sectoral_scope: bool | None = Field(
        default=None,
        description="True if the obligation is limited to a sector/data category "
        "rather than horizontal (drives 0.5-class coverage).")


class IndicatorVerdict(BaseModel):
    indicator: str = Field(description=f"One of {INDICATORS} — closed vocabulary.")
    applies: bool = Field(description="Does this provision constitute evidence for "
                          "this indicator per its scoring tree?")
    # Closed vocabularies, not prose. Both are read downstream as values, not as text:
    # rollup.py:91 does float(score_hint), and submission.py:256/:261 count rows by
    # coverage == "Horizontal" / "Sectoral". A free-text field here validated fine and
    # silently broke both — measured 2026-09-27, a local model returned score_hint
    # 'default' and, on a second run, a whole sentence. verify/blind.py:28 already
    # constrains score_hint this way; the mapper now matches its verifier.
    coverage: Literal["Horizontal", "Sectoral", "None"] = Field(
        description="Horizontal | Sectoral | None")
    score_hint: Literal[SCORE_LABELS] = Field(description=_SCORE_HINT_TEXT)
    verbatim_quote: str = Field(description="EXACT substring of the provided "
                                "provision text that carries the obligation. No "
                                "paraphrase — validated byte-for-byte downstream.")
    rationale: str = Field(description="<=300 chars; name the scoring-tree branch "
                           "or disqualifier that fired.")
    confidence: float = Field(ge=0.0, le=1.0)


# ---- which trap questions a run is asked (4 October 2026) ------------------------------------------
# The five questions of TrapChecks were written for pillars 6 and 7. A run whose scope lies inside
# those pillars is asked exactly them, as every measured run was. An indicator outside them is asked
# its OWN traps and no other indicator's (the developer's decision of 4 October): the TRAP lines of
# its block's disambiguation list, which the prompt numbers, answered inside that indicator's verdict
# before `applies`. The five stay for any pillar 6-7 indicator in the same run. One check is about
# the provision and not about an indicator, and it decides whether a row can be filed at all:
# `provision_in_force` is asked in every run.
_PILLARS_6_7 = (6, 7)
OWN_TRAPS = any(pillar_of(i) not in _PILLARS_6_7 for i in INDICATORS)


def _own_trap_count(indicator) -> int:
    """How many numbered TRAP lines the prompt shows for this indicator: none for pillars 6 and 7,
    whose traps are the five of TrapChecks, and none for an id the instrument does not carry."""
    try:
        if pillar_of(indicator) in _PILLARS_6_7:
            return 0
        return len(load_instrument().traps(indicator))
    except Exception:
        return 0


class ProvisionChecks(BaseModel):
    """What a run with no pillar 6-7 indicator is asked about the provision itself."""
    provision_in_force: bool | None = Field(
        default=None, description=TrapChecks.model_fields["provision_in_force"].description)


class OwnTrap(BaseModel):
    trap: int = Field(ge=1, description="The number of the TRAP line in THIS indicator's block "
                      "(TRAP 1, TRAP 2, ...).")
    in_play: bool = Field(description="True if the situation that TRAP line describes is present "
                          "in this provision.")


class ScopedVerdict(BaseModel):
    """IndicatorVerdict with the indicator's own traps answered first. Same fields, same wording."""
    indicator: str = Field(description=IndicatorVerdict.model_fields["indicator"].description)
    own_traps: list[OwnTrap] = Field(
        default_factory=list,
        description="This indicator's OWN trap checks, and no other indicator's: one entry for each "
        "numbered TRAP line in this indicator's block, in order. Run them before deciding `applies`, "
        "and decide in line with every trap that is in play. Leave the list empty for an indicator "
        "of pillars 6 and 7, whose traps are in trap_checks.")
    applies: bool = Field(description=IndicatorVerdict.model_fields["applies"].description)
    coverage: Literal["Horizontal", "Sectoral", "None"] = Field(
        description=IndicatorVerdict.model_fields["coverage"].description)
    score_hint: Literal[SCORE_LABELS] = Field(description=_SCORE_HINT_TEXT)
    verbatim_quote: str = Field(description=IndicatorVerdict.model_fields["verbatim_quote"].description)
    rationale: str = Field(description=IndicatorVerdict.model_fields["rationale"].description)
    confidence: float = Field(ge=0.0, le=1.0)
    # Derived, never asked of the model: which of the indicator's TRAP lines the answer left out.
    own_traps_gap: list[int] = Field(
        default_factory=list,
        description="Numbers of this indicator's TRAP lines the answer did not cover. Recorded, never fatal.")

    @model_validator(mode="after")
    def _record_own_traps_gap(self):
        answered = {t.trap for t in self.own_traps}
        self.own_traps_gap = [n for n in range(1, _own_trap_count(self.indicator) + 1)
                              if n not in answered]
        return self


RunTraps = TrapChecks if any(pillar_of(i) in _PILLARS_6_7 for i in INDICATORS) else ProvisionChecks
RunVerdict = ScopedVerdict if OWN_TRAPS else IndicatorVerdict


class MappingVerdict(BaseModel):
    core_legal_question_answer: str = Field(
        default="",
        description="One or two sentences: what does this provision actually "
        "require or prohibit, for whom?")
    who_is_regulated: str = ""
    conditions_and_exceptions: str = Field(
        default="",
        description="Conditions, exceptions, provisos in or around the text; "
        "'none visible' if none.")
    trap_checks: RunTraps = Field(default_factory=RunTraps)
    verdicts: list[RunVerdict] = Field(
        description="One verdict per CANDIDATE indicator named in the request — "
        "no more, no fewer.")
    # Derived here, never asked of the model (DERIVED_FIELDS): which narrative fields arrived
    # blank, so the gap is visible in the filed row instead of costing the row.
    narrative_gaps: list[str] = Field(
        default_factory=list,
        description="Names of the narrative fields that arrived blank. Recorded, never fatal.")

    @model_validator(mode="after")
    def _record_narrative_gaps(self):
        """Record a blank narrative field; NEVER discard the provision over one.

        Measured 2026-09-27: 30 of China's 98 remaining failures were complete negative answers --
        every verdict `applies: false`, each with a real quote and rationale -- that omitted the
        narrative the model had no reason to write. Two of those fields (`who_is_regulated`,
        `conditions_and_exceptions`) are read NOWHERE downstream, and the third only in an Excel
        audit column via .get(). Discarding a correct refusal to enforce fields nothing consumes is
        a formatting preference, not a quality gate.

        Measured 2026-09-29: that finding was applied to declines and not to FIRES, and this gate
        then raised on 29 whole provisions -- every verdict on them, including quotes already paid
        for and already grounded. 10 of the 29 were missing only the two fields nothing reads; the
        other 19 also missed `core_legal_question_answer`. What makes dropping the raise safe is
        that reasoning does not live in these three fields: IndicatorVerdict.rationale is required
        per verdict, so a filed row still carries, per indicator, the scoring-tree branch that
        fired. So the gap is now DATA -- `narrative_gaps`, which travels into the verdicts row --
        rather than a silent deletion.

        The list is filled unconditionally, for a fire and for a decline alike: it states a fact
        about the payload, not a judgement on it, and a reader who cares only about filed rows
        filters on `applies` in the same row. Assigning it here also means a value the model
        invented for this field can never survive into the row.
        """
        self.narrative_gaps = [f for f in NARRATIVE_FIELDS
                               if not (getattr(self, f) or "").strip()]
        return self


def _schema_requiring_traps() -> dict:
    """The schema the MODEL is given: every trap still required.

    The validator accepts a missing trap (bool | None) so that one omitted boolean does not throw
    away an otherwise complete answer -- measured 2026-09-27, that alone cost 237 of 4,530
    provisions. But the model must still be ASKED for all five, or it stops reasoning about the
    traps at all, and the traps are the whole point of this stage. So Pydantic's "optional" is
    reversed here, in the payload only: the two are deliberately different documents.

    DERIVED_FIELDS go the other way: the validator fills them from the answer, so the model is not
    asked for them at all. Dropping them here is what keeps this document byte-identical while the
    validator gains a field -- a schema change is a prompt change, and a prompt change one day
    before a freeze is a behaviour change nobody has time to measure.
    """
    schema = MappingVerdict.model_json_schema()
    for prop_name in DERIVED_FIELDS:
        (schema.get("properties") or {}).pop(prop_name, None)
    # narrative fields are optional to the validator (see the model validator) but the model is
    # still asked for all of them: a prompt that stops requesting reasoning stops getting it.
    schema["required"] = sorted(f for f in MappingVerdict.model_fields
                                if f not in DERIVED_FIELDS)
    for prop in (schema.get("properties") or {}).values():
        prop.pop("default", None)
    for name, defn in (schema.get("$defs") or {}).items():
        if name == "ScopedVerdict":
            # the indicator's own traps are asked for, in their place before `applies`; the gap
            # list is derived by the validator and never asked
            props = defn.get("properties") or {}
            props.pop("own_traps_gap", None)
            (props.get("own_traps") or {}).pop("default", None)
            defn["required"] = [f for f in ScopedVerdict.model_fields if f != "own_traps_gap"]
        if name == RunTraps.__name__:
            defn["required"] = sorted(RunTraps.model_fields)
            for prop in (defn.get("properties") or {}).values():
                # bool | None renders as anyOf[bool, null]; the model is asked for a plain boolean
                if "anyOf" in prop:
                    prop.pop("anyOf", None)
                    prop["type"] = "boolean"
                prop.pop("default", None)
    return schema


MAPPING_SCHEMA: dict = _schema_requiring_traps()

_TOP = frozenset(MappingVerdict.model_fields)
_TRAP = frozenset(RunTraps.model_fields)


def coerce_verdict(raw: dict, _depth: int = 0) -> dict:
    """Make a schema-forced tool result validate when only its SHAPE is wrong.

    Measured 2026-09-27 on the first real batch run: of 4,530 provisions, 1,487 (32.8%) failed
    validation, and almost none of them because the model judged badly. Across China's 2,617
    results the tool input arrived in six shapes:

        1,754  the five fields at the top level                              -- correct
          509  everything nested under a single "verdict" key                -- envelope
           71  the same, under "parameter"                                   -- envelope
           40  the same, under "parameters"                                  -- envelope
          124  trap_checks' own booleans hoisted to the top level            -- flattened
           46  only "verdicts", the narrative fields missing                 -- genuinely partial

    The first three are one bug and the fourth is another, and both are lossless to repair. Only
    the last is a real refusal to answer, and it stays a refusal.

    This matters beyond the batch: the same envelope would cost a third of the rows in the
    15 October live hour, where there is no time to notice or re-run. So the parser tolerates the
    shape and the content is judged on its merits.

    Two deliberate limits. It never invents a value -- a missing narrative field stays missing and
    the row still fails. And it only unwraps an envelope whose single key is NOT one of our own
    field names, so a legitimate payload is never mistaken for a wrapper.
    """
    if not isinstance(raw, dict) or _depth > 3:
        return raw

    # --- envelope: exactly one key, not one of ours, holding a dict
    if len(raw) == 1:
        (key, val), = raw.items()
        if key not in _TOP and isinstance(val, dict):
            return coerce_verdict(val, _depth + 1)

    out = dict(raw)

    # --- verdicts serialised as text instead of a list (16 of China's failures)
    v = out.get("verdicts")
    if isinstance(v, str):
        try:
            parsed = json.loads(v)
        except (json.JSONDecodeError, TypeError):
            parsed = None
        if isinstance(parsed, list):
            out["verdicts"] = parsed
        elif isinstance(parsed, dict):
            out["verdicts"] = [parsed]

    # --- trap_checks serialised as text
    tc = out.get("trap_checks")
    if isinstance(tc, str):
        try:
            parsed = json.loads(tc)
        except (json.JSONDecodeError, TypeError):
            parsed = None
        if isinstance(parsed, dict):
            out["trap_checks"] = parsed
        else:
            out.pop("trap_checks")          # unparseable: let the default stand

    # --- flattened: trap booleans hoisted out of trap_checks
    hoisted = {k: out.pop(k) for k in list(out) if k in _TRAP}
    if hoisted:
        existing = out.get("trap_checks")
        merged = dict(existing) if isinstance(existing, dict) else {}
        for k, v in hoisted.items():
            merged.setdefault(k, v)          # an explicit trap_checks entry wins
        out["trap_checks"] = merged

    return out

