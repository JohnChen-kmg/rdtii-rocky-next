"""The second instrument hand-off (4 October 2026): scales per block, economy-level questions from
the block, the prompt header from the scope, the evaluator from the flags.

Run from stages/p3-map:
    python -m pytest tests/test_second_handoff.py -q

Two kinds of test. The first kind holds the MEASURED PATH still: every request a model receives for
the nine indicators of pillars 6 and 7 is compared with what it was before this change, by
fingerprint or word for word, because every filed row and every reported figure came from those
requests. The second kind covers what is new for the other 52. Nothing here talks to a model.
"""
from __future__ import annotations

import csv
import dataclasses
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from config.instrument import load
from config.settings import INDICATORS, SETTINGS
from src.p3map import rollup
from src.p3map.eval import evaluator
from src.p3map.mapping.prompt import build_system_prefix, scope_label
from src.p3map.mapping.schema import SCORE_LABELS, IndicatorVerdict
from src.p3map.verify import blind

STAGE_ROOT = Path(__file__).resolve().parent.parent
INS = load()


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _canon(doc) -> str:
    return json.dumps(doc, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


# ---- the measured path has not moved ---------------------------------------------------------------
# Fingerprints taken on 4 October 2026 at commit bafe873, before any of this was written. (The
# mapper's own answer form is pinned in test_verdict_coercion.py.)

def test_the_default_scope_is_still_the_nine_of_pillars_6_and_7():
    assert INDICATORS == ("6.1", "6.2", "6.3", "6.4", "7.1", "7.2", "7.3", "7.4", "7.5")
    assert SCORE_LABELS == ("1", "0.5", "0", "n/a")


def test_the_prompt_for_pillars_6_and_7_has_not_moved():
    prefix = build_system_prefix()
    assert len(prefix) == 31929
    assert _sha(prefix) == "aac9dd69f874cea51d6e010bd3e57112089e79c0121acb283bdc1070534333b9"


def test_the_re_check_for_pillars_6_and_7_has_not_moved():
    assert _sha(_canon(blind.VERIFY_SCHEMA)) == "98847e003310b941e83bdd128da572b57e1a73459fdc048ca9beed62d1ccda4e"
    assert _sha(blind.PROMPT) == "15155df025365efbcbd651b837c6bc736b241b2b98ccb6e2d1d8cd84b52d9ee6"
    assert blind.VERIFY_SCHEMA["properties"]["score_hint"]["enum"] == ["1", "0.5", "0", "n/a"]


MEASURED_QUESTION = """Evidence rows collected for {econ} / {ind} (each: law, section, coverage, quote):
{evidence}
{rejected}
QUESTION ({ind}, INVERTED polarity): does {econ} LACK a {what}?
Score 1 = no framework exists; 0.5 = sectoral/partial only; 0 = comprehensive
framework exists. Judge ONLY from the material above.

controlling_law must NAME the instrument your score rests on. If the material does not let you name
one, return controlling_law empty -- an absence of retrieved evidence is not evidence of absence, and
the cell will be left unscored rather than guessed."""
MEASURED_WHAT = {"7.1": "comprehensive legal framework for personal data protection",
                 "7.2": "dedicated legal framework for cybersecurity"}


@pytest.mark.parametrize("ind", ["7.1", "7.2"])
def test_the_economy_level_question_for_7_1_and_7_2_has_not_moved(ind):
    args = dict(econ="SG", ind=ind, evidence="- Some Act s.1 [Horizontal]", rejected="")
    now = rollup.FRAMEWORK_PROMPT.format(what=INS.framework_name(ind), scale=rollup.framework_scale(INS, ind), **args)
    assert now == MEASURED_QUESTION.format(what=MEASURED_WHAT[ind], **args)
    assert rollup.framework_schema(INS, ind) == {
        "type": "object",
        "properties": {"score": {"type": "string", "enum": ["1", "0.5", "0"]},
                       "controlling_law": {"type": "string"},
                       "reason": {"type": "string", "maxLength": 400}},
        "required": ["score", "controlling_law", "reason"]}


def test_any_scope_inside_pillars_6_and_7_keeps_the_measured_header():
    for scope in (("6.1", "6.4"), ("7.3",), INDICATORS):
        assert scope_label(scope) == "Pillars 6-7"


# ---- scales come from the blocks -------------------------------------------------------------------

def test_every_block_states_its_own_scale():
    assert INS.values("6.1") == (1.0, 0.5, 0.0)
    assert INS.values("7.3") == (1.0, 0.0)
    assert INS.values("3.1") == INS.values("5.2") == (1.0, 0.8, 0.5, 0.0)
    assert INS.values("3.4") == INS.values("5.4") == (1.0, 0.5, 0.25, 0.0)
    assert INS.values("1.4") == (1.0, 0.75, 0.5, 0.25, 0.0)
    assert sum(1 for i in INS.blocks if INS.values(i) == (1.0, 0.0)) == 23, "the binary ones"
    assert INS.labels(["3.1", "5.4"]) == ("1", "0.8", "0.5", "0.25", "0")
    assert INS.labels(["5.7", "12.9"]) == ("1", "0")


def test_a_score_is_on_scale_only_for_its_own_block():
    assert INS.on_scale("3.1", "0.8") and INS.on_scale("3.1", 0.5)
    assert not INS.on_scale("6.1", "0.8")
    assert not INS.on_scale("7.3", "0.5"), "a binary indicator offers no half point"
    assert not INS.on_scale("6.1", "n/a") and not INS.on_scale("6.1", None)


def test_a_verdict_takes_the_scores_of_the_scope_and_nothing_else():
    ok = dict(indicator="6.1", applies=True, coverage="Horizontal", verbatim_quote="q", rationale="r", confidence=0.9)
    assert IndicatorVerdict(score_hint="0.5", **ok).score_hint == "0.5"
    with pytest.raises(Exception):
        IndicatorVerdict(score_hint="0.8", **ok)      # 0.8 is 3.1's and 5.2's, not this scope's


def _in_scope(scope: str, code: str) -> dict:
    """Run `code` in a fresh interpreter whose run scope is `scope` (the scope is fixed at import)."""
    env = {**os.environ, "INDICATORS_SCOPE": scope, "PYTHONIOENCODING": "utf-8"}
    env.pop("RDTII_ENGINE", None)
    out = subprocess.run([sys.executable, "-c", code], cwd=str(STAGE_ROOT), env=env, capture_output=True,
                         text=True, encoding="utf-8", timeout=120)
    assert out.returncode == 0, out.stderr[-800:]
    return json.loads(out.stdout.strip().splitlines()[-1])


PROBE = """
import json
from src.p3map.mapping.prompt import build_system_prefix
from src.p3map.mapping.schema import MAPPING_SCHEMA, SCORE_LABELS
from src.p3map.verify import blind
import re
prefix = build_system_prefix()
head = prefix.split("\\n")[0]
defs = MAPPING_SCHEMA["$defs"]
verdict = defs.get("ScopedVerdict") or defs["IndicatorVerdict"]
checks = defs.get("TrapChecks") or defs["ProvisionChecks"]
hint = verdict["properties"]["score_hint"]
print(json.dumps({"labels": list(SCORE_LABELS), "enum": hint["enum"], "says": hint["description"],
                  "verify": blind.VERIFY_SCHEMA["properties"]["score_hint"]["enum"],
                  "verify_prompt": blind.PROMPT.splitlines()[-1], "head": head,
                  "defs": sorted(defs), "provision_checks": sorted(checks["properties"]),
                  "checks_required": checks["required"], "verdict_fields": list(verdict["properties"]),
                  "verdict_required": verdict["required"],
                  "numbered": re.findall(r"TRAP (\\d+)", prefix), "unnumbered_6_1": "TRAP (the #1 mis-mapping)" in prefix}))
"""
FIVE = ["conditional_path_exists", "government_data_only", "provision_in_force", "retention_is_minimum", "sectoral_scope"]


def test_another_scope_is_offered_its_own_scores_in_reading_and_re_check():
    got = _in_scope("3.1,5.4", PROBE)
    assert got["labels"] == got["enum"] == got["verify"] == ["1", "0.8", "0.5", "0.25", "0", "n/a"]
    assert "'0.8'" in got["says"] and "own scoring tree" in got["says"]
    assert got["verify_prompt"] == "scoring branch fires ('1', '0.8', '0.5', '0.25', '0'); if not, 'n/a'."
    assert "(Pillars 3, 5)" in got["head"] and "Pillars 6-7" not in got["head"]


def test_a_binary_scope_is_not_offered_a_half_point():
    got = _in_scope("5.7,12.9", PROBE)
    assert got["enum"] == got["verify"] == ["1", "0", "n/a"]
    assert "(Pillars 5, 12)" in got["head"]
    assert "(Pillar 12)" in _in_scope("12.4.1,12.9", PROBE)["head"]


# ---- the roll-up -----------------------------------------------------------------------------------

def fire(score, doc="d1", verification="agree"):
    return {"score_hint": score, "doc_id": doc, "verification": verification}


def test_the_roll_up_of_pillars_6_and_7_says_what_it_always_said():
    assert rollup.measure_score(INS, "6.4", [fire("1"), fire("0.5", "d2")]) == {
        "score": 1.0, "basis": "max over 2 verified fires", "evidence_rows": 2, "pending": 0}
    assert rollup.measure_score(INS, "6.1", [fire("0.5"), fire("0.5", "d2")]) == {
        "score": 1.0, "basis": "escalation clause: 2 distinct verified half-point measures",
        "evidence_rows": 2, "pending": 0}
    assert rollup.measure_score(INS, "7.3", [fire("0.5")]) == {
        "score": 0.0, "basis": "binary indicator: lone 0.5 does not qualify (flagged)",
        "evidence_rows": 1, "pending": 0}
    assert rollup.measure_score(INS, "6.2", []) == {
        "score": 0.0, "basis": "no VERIFIED qualifying measure", "evidence_rows": 0, "pending": 0}
    assert rollup.measure_score(INS, "6.2", [fire("1", verification="split_flagged")]) == {
        "score": "provisional-0", "basis": "no VERIFIED qualifying measure (1 fires pending verification)",
        "evidence_rows": 0, "pending": 1}


def test_a_four_step_indicator_keeps_its_own_values():
    got = rollup.measure_score(INS, "3.1", [fire("0.8"), fire("0.5", "d2")])
    assert got["score"] == 0.8 and got["evidence_rows"] == 2 and "off_scale" not in got
    assert rollup.measure_score(INS, "5.4", [fire("0.25")])["score"] == 0.25


def test_a_value_outside_the_blocks_scale_is_set_aside_and_counted():
    got = rollup.measure_score(INS, "2.1", [fire("0.8"), fire("0.5", "d2")])      # 2.1 is 1 / 0.5 / 0
    assert got["score"] == 0.5 and got["evidence_rows"] == 1 and got["off_scale"] == 1
    assert "1 verified value(s) outside this indicator's scale set aside" in got["basis"]
    only = rollup.measure_score(INS, "12.4.1", [fire("0.25")])                    # binary; 0.25 is not its value
    assert only["score"] == 0.0 and only["off_scale"] == 1 and "set aside" in only["basis"]


class Fake:
    model = "fake"

    def __init__(self, reply):
        self.reply, self.sent = reply, []

    def complete(self, prompt, schema, **kw):
        self.sent.append((prompt, schema))
        return self.reply


FIRES = [{"law_name": "Telecom Act", "article_section": "s.9", "coverage": "Horizontal"}]


def test_every_economy_level_indicator_has_a_framework_to_ask_about():
    economy = [i for i in INS.blocks if INS.level(i) == "economy"]
    assert len(economy) == 13
    assert all(INS.framework_name(i) for i in economy)
    assert all(INS.is_inverted(i) for i in economy), "the question asks whether the economy LACKS it"


def test_an_economy_level_indicator_is_asked_with_its_own_framework_and_tree():
    fake = Fake({"score": "0.25", "controlling_law": "Telecom Act", "reason": "accounting separation only"})
    got = rollup._framework_score("TL", "5.4", FIRES, client=fake)
    assert got["score"] == 0.25 and got["controlling_law"] == "Telecom Act"
    prompt, schema = fake.sent[0]
    assert f"does TL LACK a {INS.framework_name('5.4')}?" in prompt
    assert "Apply this indicator's own scoring tree and answer with one of '1', '0.5', '0.25', '0':" in prompt
    assert "score: 0.25" in prompt, "the block's branches, not the 7.1 sentence"
    assert "sectoral/partial only" not in prompt
    assert schema["properties"]["score"]["enum"] == ["1", "0.5", "0.25", "0"]
    binary = Fake({"score": "1", "controlling_law": "Telecom Act", "reason": "no independent regulator"})
    assert rollup._framework_score("TL", "5.7", FIRES, client=binary)["score"] == 1.0
    assert binary.sent[0][1]["properties"]["score"]["enum"] == ["1", "0"]


def test_an_answer_off_the_indicators_scale_leaves_the_cell_unscored():
    got = rollup._framework_score("TL", "5.7", FIRES, client=Fake({"score": "0.5", "controlling_law": "Telecom Act", "reason": "x"}))
    assert got["score"] == "pending" and "does not offer" in got["basis"]


def test_no_named_law_still_leaves_the_cell_unscored():
    got = rollup._framework_score("TL", "11.1", FIRES, client=Fake({"score": "1", "controlling_law": "", "reason": "nothing found"}))
    assert got["score"] == "pending" and "named no controlling law" in got["basis"]


# ---- the evaluator reads the flags -----------------------------------------------------------------

def test_the_rule_sets_aside_exactly_the_seven_of_round_one_in_pillars_6_and_7():
    gold = list(INS.gold())
    p67 = {g["gold_id"] for g in gold if g["indicator"] and g["indicator"].split(".")[0] in ("6", "7")
           and evaluator.excluded_by_flag(g)}
    assert p67 == evaluator.EXCLUDE_FLAGGED, "the published pillar 6-7 figures keep their rows"
    why = [evaluator.excluded_by_flag(g) for g in gold]
    assert why.count("suspect") == 53 and why.count("round1_review") == 5
    kept = [g for g in gold if not evaluator.excluded_by_flag(g)]
    statuses = [(g.get("label_flag") or {}).get("status") for g in kept]
    assert statuses.count("advisory") == 157 and statuses.count("host_marked") == 34 and statuses.count("candidate") == 7


def test_the_report_says_what_the_flags_did(monkeypatch, tmp_path):
    def row(gid, ind, law, status=None, basis=None):
        g = {"gold_id": gid, "economy": "XX", "indicator": ind, "law": law}
        if status:
            g["label_flag"] = {"status": status, "basis": basis}
        return g
    gold = [row("g1", "3.1", "Investment Act"), row("g2", "3.1", "Ownership Act", "advisory", "drafting_review_2026-10-04"),
            row("g3", "3.1", "Wrong Act", "suspect", "drafting_review_2026-10-04"), row("g4", "5.7", "Regulator Act", "suspect", "drafting_review_2026-10-04"),
            row("g5", "5.4", "Telecom Act", "advisory", "round1_review")]
    out, idx = tmp_path / "out", tmp_path / "index"
    (out / "submission").mkdir(parents=True)
    idx.mkdir()
    docs = {f"d{n}": {"economy": "XX", "law_name": name, "provision_count": 5}
            for n, name in enumerate(["Investment Act", "Ownership Act", "Wrong Act", "Regulator Act", "Telecom Act"])}
    (idx / "doc_meta.json").write_text(json.dumps(docs), encoding="utf-8")
    with (out / "submission" / "records_XX.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["Indicator ID", "Law Name", "Discovery Tag"])
        w.writeheader()
        w.writerow({"Indicator ID": "3.1", "Law Name": "Investment Act", "Discovery Tag": "KNOWN"})
    monkeypatch.setattr(evaluator, "SETTINGS", dataclasses.replace(SETTINGS, out_dir=out, index_dir=idx))
    monkeypatch.setattr(evaluator, "INDICATORS", ("3.1", "5.4", "5.7"))
    monkeypatch.setattr(evaluator, "load_instrument", lambda: type("G", (), {"gold": staticmethod(lambda: iter(gold))})())
    rep = evaluator.run_eval("XX")
    assert rep["gold_rows_set_aside_by_flag"] == {"suspect": 2, "round1_review": 1}
    assert rep["resolvable_gold_rows"] == 2 and rep["row_recall"] == 0.5          # g1 found, g2 missed
    assert rep["flagged_rows_counted_as_gold"] == {"advisory": 1}
    assert rep["unflagged_gold_rows"] == 1 and rep["row_recall_unflagged"] == 1.0
    assert rep["indicators_with_no_gold_left"] == ["5.4", "5.7"], "no gold is not a recall of zero"
    assert [m["gold"] for m in rep["misses"]] == ["g2"]


# ---- each indicator answers its own traps, and no other indicator's ---------------------------------

def test_every_block_has_traps_of_its_own_to_ask():
    counts = {i: len(INS.traps(i)) for i in INS.blocks}
    assert sum(counts.values()) == 263 and min(counts.values()) >= 1
    assert counts["3.1"] == 7 and counts["5.4"] == 6


def test_a_run_inside_pillars_6_and_7_is_asked_the_five_it_always_was():
    got = _in_scope("6.1,6.4", PROBE)
    assert got["defs"] == ["IndicatorVerdict", "TrapChecks"]
    assert got["provision_checks"] == got["checks_required"] == FIVE
    assert "own_traps" not in got["verdict_fields"]
    assert got["numbered"] == [] and got["unnumbered_6_1"], "the blocks of pillars 6 and 7 are rendered as before"


def test_an_indicator_outside_them_is_asked_only_its_own_traps():
    got = _in_scope("3.1,5.4", PROBE)
    assert got["defs"] == ["OwnTrap", "ProvisionChecks", "ScopedVerdict"]
    assert got["provision_checks"] == got["checks_required"] == ["provision_in_force"], \
        "no pillar 6-7 trap is asked; whether the text is in force is about the provision, and filing depends on it"
    fields = got["verdict_fields"]
    assert fields.index("indicator") < fields.index("own_traps") < fields.index("applies"), "traps before the verdict"
    assert "own_traps" in got["verdict_required"]
    assert "own_traps_gap" not in fields, "derived, never asked of the model"
    # the prompt numbers each block's own TRAP lines from 1: seven for 3.1, six for 5.4
    assert got["numbered"] == [str(n) for n in range(1, 8)] + [str(n) for n in range(1, 7)]


def test_a_mixed_run_keeps_the_five_for_its_pillar_6_7_indicator():
    got = _in_scope("6.1,3.1", PROBE)
    assert got["provision_checks"] == FIVE
    assert "own_traps" in got["verdict_fields"]
    assert got["numbered"] == [str(n) for n in range(1, 8)] and got["unnumbered_6_1"], "3.1 numbered, 6.1 as it was"


GAP_PROBE = """
import json
from src.p3map.mapping.schema import MappingVerdict
base = dict(applies=True, coverage="Sectoral", verbatim_quote="q", rationale="r", confidence=0.8)
v = MappingVerdict.model_validate({"trap_checks": {"provision_in_force": True}, "verdicts": [
    {"indicator": "3.1", "own_traps": [{"trap": 1, "in_play": False}, {"trap": 2, "in_play": True}], "score_hint": "0.8", **base},
    {"indicator": "5.4", "score_hint": "0.25", **base}]})
rows = [x.model_dump() for x in v.verdicts]
print(json.dumps({"gap_3_1": rows[0]["own_traps_gap"], "gap_5_4": rows[1]["own_traps_gap"], "traps_3_1": rows[0]["own_traps"],
                  "in_force": v.trap_checks.model_dump()}))
"""


def test_a_trap_left_unanswered_is_recorded_and_costs_nothing():
    got = _in_scope("3.1,5.4", GAP_PROBE)
    assert got["traps_3_1"] == [{"trap": 1, "in_play": False}, {"trap": 2, "in_play": True}]
    assert got["gap_3_1"] == [3, 4, 5, 6, 7]
    assert got["gap_5_4"] == [1, 2, 3, 4, 5, 6], "no trap answered at all: still a verdict, with the gap on the row"
    assert got["in_force"] == {"provision_in_force": True}


# ---- the economy-level question carries its evidence ------------------------------------------------

def test_a_new_economy_level_indicator_is_given_the_quotes():
    fires = [{"law_name": "Telecom Act", "article_section": "s.9", "coverage": "Horizontal",
              "quote": "the  dominant operator shall keep\nseparate accounts"}]
    fake = Fake({"score": "0.5", "controlling_law": "Telecom Act", "reason": "accounting separation"})
    rollup._framework_score("TL", "5.4", fires, client=fake)
    assert '- Telecom Act s.9 [Horizontal] "the dominant operator shall keep separate accounts"' in fake.sent[0][0]


@pytest.mark.parametrize("ind", ["7.1", "7.2"])
def test_7_1_and_7_2_keep_the_evidence_rows_they_were_measured_with(ind):
    fires = [{"law_name": "Data Act", "article_section": "s.3", "coverage": "Horizontal", "quote": "personal data shall"}]
    fake = Fake({"score": "0", "controlling_law": "Data Act", "reason": "comprehensive"})
    rollup._framework_score("SG", ind, fires, client=fake)
    assert "- Data Act s.3 [Horizontal]\n" in fake.sent[0][0]
    assert "personal data shall" not in fake.sent[0][0]
