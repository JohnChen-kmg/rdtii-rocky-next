"""coerce_verdict: repair a schema-forced result whose SHAPE is wrong, never its content.

Measured on the first real batch run, 27 September 2026: 1,487 of 4,530 provisions (32.8%) failed
validation, and almost none because the model judged badly. Six shapes came back; three of them
were one envelope bug and one was a flattening bug. Repairing those two took validation from 67.2%
to 96.4% without a single new API call, on answers already paid for.
"""
from __future__ import annotations

import copy
import hashlib
import json

import pytest
from pydantic_core import PydanticUndefined

from src.p3map.mapping.schema import (DERIVED_FIELDS, MAPPING_SCHEMA, NARRATIVE_FIELDS,
                                      IndicatorVerdict, MappingVerdict, TrapChecks,
                                      coerce_verdict)

# sha256 of the canonical JSON of MAPPING_SCHEMA as it stood at 6ce0cf1, i.e. before the narrative
# gate was relaxed. The document the model receives must not have moved: see
# test_the_document_sent_to_the_model_has_not_moved.
SENT_SCHEMA_SHA256 = "025bc24e7685b0fde1d56821fee72e62cdb9b6bd6b57df8d18cf4aee0d598b78"


def _canonical(schema: dict) -> str:
    return json.dumps(schema, sort_keys=True, separators=(",", ":"))

GOOD_TRAPS = {"conditional_path_exists": False, "retention_is_minimum": False,
              "government_data_only": False, "provision_in_force": True,
              "sectoral_scope": False}
GOOD_VERDICT = {"indicator": "7.3", "applies": False, "coverage": "None", "score_hint": "0",
                "verbatim_quote": "x", "rationale": "y", "confidence": 0.6}
BODY = {"core_legal_question_answer": "a", "who_is_regulated": "b",
        "conditions_and_exceptions": "c", "trap_checks": dict(GOOD_TRAPS),
        "verdicts": [dict(GOOD_VERDICT)]}


def test_the_flat_shape_is_untouched():
    assert coerce_verdict(dict(BODY)) == BODY
    MappingVerdict.model_validate(coerce_verdict(dict(BODY)))


@pytest.mark.parametrize("wrapper", ["verdict", "parameter", "parameters", "input", "result"])
def test_a_single_key_envelope_is_unwrapped(wrapper):
    """509 results nested everything under "verdict", 71 under "parameter", 40 under "parameters"."""
    MappingVerdict.model_validate(coerce_verdict({wrapper: dict(BODY)}))


def test_nested_envelopes_are_unwrapped_to_a_depth_limit():
    MappingVerdict.model_validate(coerce_verdict({"a": {"b": dict(BODY)}}))


def test_a_legitimate_payload_is_never_mistaken_for_an_envelope():
    """The unwrap only fires when the single key is NOT one of our own field names."""
    one = {"verdicts": [dict(GOOD_VERDICT)]}
    assert coerce_verdict(one) == one, "a real field must not be unwrapped as a wrapper"


def test_hoisted_trap_booleans_are_renested():
    """124 results lifted trap_checks' own booleans to the top level."""
    raw = {k: v for k, v in BODY.items() if k != "trap_checks"}
    raw.update(GOOD_TRAPS)
    out = coerce_verdict(raw)
    assert out["trap_checks"] == GOOD_TRAPS
    assert not (set(GOOD_TRAPS) & set(out) - {"trap_checks"}), "hoisted keys must be removed"
    MappingVerdict.model_validate(out)


def test_an_explicit_trap_checks_entry_wins_over_a_hoisted_one():
    raw = dict(BODY)
    raw["trap_checks"] = {**GOOD_TRAPS, "provision_in_force": False}
    raw["provision_in_force"] = True            # hoisted duplicate, must lose
    assert coerce_verdict(raw)["trap_checks"]["provision_in_force"] is False


def test_a_missing_trap_is_recorded_as_not_stated_never_invented():
    """237 answers omitted conditional_path_exists alone. Defaulting it to False would assert
    "no compliant transfer path exists", which is exactly the 6.1-vs-6.4 judgement the trap
    guards. It comes back None instead, and every downstream reader already tolerates that:
    submission.py tests `is False` / `is True`, excel_export uses .get(..., True).
    """
    raw = dict(BODY)
    raw["trap_checks"] = {k: v for k, v in GOOD_TRAPS.items() if k != "conditional_path_exists"}
    v = MappingVerdict.model_validate(coerce_verdict(raw))
    assert v.trap_checks.conditional_path_exists is None
    assert v.trap_checks.provision_in_force is True


def test_a_firing_verdict_missing_one_narrative_field_is_kept_and_the_gap_recorded():
    """This test used to pin the opposite: a FIRE missing narrative raised, and the provision --
    every verdict on it, quotes included -- was discarded. Measured 2026-09-29, that cost 29 whole
    provisions of the 225 S4 calls that produced no verdict, 13% of the loss. `who_is_regulated` is
    read NOWHERE downstream, so the gap is now data, not a deletion.
    """
    raw = {k: v for k, v in BODY.items() if k != "who_is_regulated"}
    raw["verdicts"] = [{**GOOD_VERDICT, "applies": True}]
    v = MappingVerdict.model_validate(coerce_verdict(raw))
    assert [x.applies for x in v.verdicts] == [True], "the fire must survive the missing field"
    assert v.narrative_gaps == ["who_is_regulated"], "the gap must be visible, not silent"
    assert v.core_legal_question_answer == "a", "a field that WAS answered is untouched"


def test_a_fire_missing_every_narrative_field_still_carries_each_verdict_rationale():
    """What makes dropping the raise safe: the reasoning does not live in the narrative fields.

    IndicatorVerdict.rationale is required per verdict, so a filed row still names the
    scoring-tree branch that fired, per indicator. Of the 29 discarded provisions, 10 missed only
    the two fields nothing reads and 19 also missed core_legal_question_answer.
    """
    raw = {"verdicts": [{**GOOD_VERDICT, "applies": True, "rationale": "6.1 ban branch"},
                        {**GOOD_VERDICT, "indicator": "6.4", "applies": True,
                         "rationale": "6.4 conditional path"}]}
    v = MappingVerdict.model_validate(coerce_verdict(raw))
    assert v.narrative_gaps == ["core_legal_question_answer", "who_is_regulated",
                                "conditions_and_exceptions"]
    assert [x.rationale for x in v.verdicts] == ["6.1 ban branch", "6.4 conditional path"]


def test_rationale_is_required_on_every_verdict():
    """Relaxing the narrative gate is only safe while this holds, so pin it."""
    field = IndicatorVerdict.model_fields["rationale"]
    assert field.is_required() and field.default is PydanticUndefined
    assert "rationale" in IndicatorVerdict.model_json_schema()["required"]
    with pytest.raises(Exception, match="rationale"):
        MappingVerdict.model_validate(
            {"verdicts": [{k: v for k, v in GOOD_VERDICT.items() if k != "rationale"}]})


def test_a_complete_answer_records_no_gap():
    assert MappingVerdict.model_validate(coerce_verdict(dict(BODY))).narrative_gaps == []


def test_narrative_gaps_is_derived_here_never_taken_from_the_model():
    """The model is not asked for this field; a value it invented must not reach the row."""
    raw = {**BODY, "narrative_gaps": ["who_is_regulated", "made", "up"]}
    assert MappingVerdict.model_validate(coerce_verdict(raw)).narrative_gaps == []


def test_narrative_gaps_survives_model_dump_into_the_row():
    """Both lanes file `v.narrative_gaps` in the verdicts row; a dump that drops it hides the gap."""
    raw = {k: v for k, v in BODY.items() if k != "conditions_and_exceptions"}
    raw["verdicts"] = [{**GOOD_VERDICT, "applies": True}]
    dumped = MappingVerdict.model_validate(coerce_verdict(raw)).model_dump()
    assert dumped["narrative_gaps"] == ["conditions_and_exceptions"]


def test_a_decline_may_omit_the_narrative():
    """30 of China's failures were complete refusals that skipped fields nothing reads.

    `who_is_regulated` and `conditions_and_exceptions` are read NOWHERE downstream;
    `core_legal_question_answer` only in one Excel audit column, via .get(). Discarding a correct
    refusal to enforce them was a formatting preference, not a quality gate.
    """
    raw = {"verdicts": [dict(GOOD_VERDICT)]}            # applies=False
    v = MappingVerdict.model_validate(coerce_verdict(raw))
    assert v.core_legal_question_answer == ""
    assert [x.applies for x in v.verdicts] == [False]


def test_verdicts_serialised_as_a_string_is_parsed():
    """16 of China's failures returned the list as JSON text."""
    import json as _json
    raw = {**BODY, "verdicts": _json.dumps([dict(GOOD_VERDICT)])}
    v = MappingVerdict.model_validate(coerce_verdict(raw))
    assert len(v.verdicts) == 1 and v.verdicts[0].indicator == "7.3"


def test_trap_checks_serialised_as_a_string_is_parsed():
    import json as _json
    raw = {**BODY, "trap_checks": _json.dumps(dict(GOOD_TRAPS))}
    v = MappingVerdict.model_validate(coerce_verdict(raw))
    assert v.trap_checks.provision_in_force is True


def test_unparseable_trap_checks_falls_back_to_not_stated():
    raw = {**BODY, "trap_checks": "the provision is in force"}
    v = MappingVerdict.model_validate(coerce_verdict(raw))
    assert v.trap_checks.provision_in_force is None


def test_the_model_is_still_asked_for_the_narrative():
    """The validator is lenient; the request is not. A prompt that stops asking stops getting.

    This used to assert set equality between `required` and every model field. That held only while
    the model was asked for exactly what the validator holds, and it broke the moment the validator
    gained a field it DERIVES rather than requests. Equality was never the point -- being asked for
    the narrative was -- so the assertion is now the intent, with the derived fields excluded.
    """
    for f in NARRATIVE_FIELDS:
        assert f in MAPPING_SCHEMA["required"], f"the model must still be asked for {f}"
    assert sorted(MAPPING_SCHEMA["required"]) == sorted(
        f for f in MappingVerdict.model_fields if f not in DERIVED_FIELDS)
    for name, prop in MAPPING_SCHEMA["properties"].items():
        assert "default" not in prop, f"{name} must not advertise a default to the model"


def test_a_derived_field_is_never_offered_to_the_model():
    """A field the validator fills must appear in neither half of the sent document.

    In `required` it would make the model invent a value; in `properties` alone it would still
    advertise the field and invite one. `_schema_requiring_traps` pops it from both.
    """
    for f in DERIVED_FIELDS:
        assert f in MappingVerdict.model_fields, f"{f} is not a model field -- stale constant?"
        assert f not in MAPPING_SCHEMA["required"], f"{f} must not be asked of the model"
        assert f not in MAPPING_SCHEMA.get("properties", {}), f"{f} must not be advertised"


def test_the_document_sent_to_the_model_has_not_moved():
    """The strongest form of the constraint above: byte-identity, not absence.

    Relaxing the narrative gate had to change the validator WITHOUT changing the request, because a
    schema change is a prompt change and a prompt change is a behaviour change -- and this landed
    one day before the host's 30 September submission deadline, with no time to measure one. The
    hash is of MAPPING_SCHEMA's canonical JSON at 6ce0cf1, verified equal after the change.

    If this fails, the model is being asked for something different than it was. Do not re-pin the
    hash to make it pass unless changing the request is the deliberate, measured intent.
    """
    got = hashlib.sha256(_canonical(MAPPING_SCHEMA).encode()).hexdigest()
    assert got == SENT_SCHEMA_SHA256, (
        "the schema sent to the model changed; re-pin only if that was intended")


def test_the_sent_schema_is_not_the_validator_schema():
    """They are deliberately different documents, and mutating one must not touch the other."""
    before = _canonical(MAPPING_SCHEMA)
    scratch = copy.deepcopy(MAPPING_SCHEMA)
    scratch["required"] = []
    scratch.get("properties", {}).clear()
    assert _canonical(MAPPING_SCHEMA) == before, "MAPPING_SCHEMA is aliased, not copied"


def test_non_dict_input_passes_through_untouched():
    for junk in ("a string", 7, None, ["a", "list"]):
        assert coerce_verdict(junk) == junk


def test_the_model_is_still_required_to_answer_every_trap():
    """The validator is lenient; the schema we SEND is not. If the model stops being asked for the
    traps it stops reasoning about them, and the traps are the point of this stage.
    """
    td = MAPPING_SCHEMA["$defs"]["TrapChecks"]
    assert sorted(td["required"]) == sorted(TrapChecks.model_fields), \
        "all five traps must be required in the payload sent to the model"
    for name, prop in td["properties"].items():
        assert prop.get("type") == "boolean", f"{name} must be asked for as a plain boolean"
        assert "anyOf" not in prop and "default" not in prop, \
            f"{name} must not advertise null or a default to the model"
