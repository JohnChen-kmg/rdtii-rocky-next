"""Stage E — instrument validation, finale edition (61 scoreable indicators).

Exit code 0 = the instrument is consistent and frozen-ready. Checks, grouped:

  0  indicator_order.yaml   62 listed IDs, canonical decimal text, pillar derivation, 61 in scope,
                            6.5 declared out of scope, host trap rows present; matches the host
                            template's Indicator Reference when the template is present; every entry
                            carries its coverage marks (automated or manual, the reason, the nature
                            of the answer), compared with the coverage register when
                            RDTII_COVERAGE_REGISTER names it
  1  codebook               indicators.yaml holds every in-scope ID exactly once, in host order, each
                            block tier A, B or C; the file's `tiers` key describes all three; required
                            fields per tier
  1b methodology            for ALL 61: category_official and scoring.values machine-match the host
                            methodology sheet; one scoring branch per allowed score, in order
  1d same elements          every Tier A/B block carries weight, scoring_features, guide_examples,
                            null_statement and sources (row numbers checked against the host sheets); a
                            question that differs from the definition; polarity and level only in their
                            allowed forms, with framework_name on every economy-level block
  1e roll-up fields         every block carries absence_score (null or one of its own scoring.values;
                            null on every inverted block) and absence_basis; count_rule sits on the
                            blocks that score by counting, is well formed, and for 6.1 and 6.2 states
                            exactly the rule the mapping stage used to hand-code; all three equal
                            scripts/data/rollup_fields.yaml
  1c citations              Tier A/B: every definition, coding rule, exception and disambiguation line
                            ends with a host citation; Tier A carries the Round 1 trap wording and the
                            finale template's trap rows 80-84 on the right indicators
  2  guide_refs             every in-scope ID has the Guide's defining sentence; when RDTII_GUIDE_TEXT
                            points at a page-numbered Guide extract, each sentence is checked verbatim
                            on its printed page
  3  policies.yaml          contract §4.2 keys plus the finale additions; indicator_sets restates the
                            blocks' polarity and level and the order file's lists exactly, and the
                            polarity sentence names the same inverted indicators
  4  signatures/            one file per in-scope ID, named by ID; >=3 exemplars from >=2 economies,
                            every exemplar round-trips to its workbook row; no suspect row used
  5  gold/gold_set.jsonl    row count equals a fresh parse of both workbooks; every row round-trips;
                            flag statuses valid; exemplar_for matches the curated data
  6  hygiene                no legacy P6-I1-style IDs in output files; indicator_ids.py identical to
                            the mapping stage's vendored copy
  info                      whether output/ has been re-vendored into p3-map/contracts/instrument/,
                            compared file by file, subfolders included, ignoring CRLF against LF
                            (reported, not enforced; pass --require-vendored to enforce)

The mapping stage is looked for beside this stage (stages/p3-map). When the instrument is built
outside the finale repo, set RDTII_FINALE_REPO to the repo root; if neither is found, the two
mapping-stage checks are skipped and an INFO line says so.

What this does NOT prove: Tier A/B prose is written, not extracted, and spot-checked, not machine-diffed
against the Guide; Tier C blocks restate host text and carry no traps; candidate label flags
are machine signals, not reviewed judgements.
"""
from __future__ import annotations

import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import openpyxl
import yaml

from build_rollup_fields import KEYS as ROLLUP_KEYS, wanted as rollup_wanted
from indicator_ids import BadIndicatorId, normalize, pillar_of
from rdtii_examples import (DATA, REPO, ROUND1, ROUND1_SHEETS, ROUND2, ROUND2_SHEETS, SCRIPTS,
                            TEMPLATE_FINAL, category_first_line, load_all, load_methodology,
                            parse_workbook, score_values)

OUT = REPO / "output"
P3MAP = (Path(os.environ["RDTII_FINALE_REPO"]) / "stages" / "p3-map" if os.environ.get("RDTII_FINALE_REPO")
         else REPO.parent / "p3-map")
VENDORED = P3MAP / "contracts" / "instrument"
VENDORED_IDS = P3MAP / "config" / "indicator_ids.py"

CITE = re.compile(r"\((?=[^()]*\b(Guide pp?\.|Internal Guide pp?\.|Methodology sheet|Indicator Reference|"
                  r"workbook round[12]|Extraction slides|Assignment [12]|Canvas deck|Hands-on deck|"
                  r"Non-regulatory|answer key))[^()]*\)")
LEGACY = re.compile(r"\bP\d{1,2}-I\d{1,2}\b")
GUIDE_PAGE = re.compile(r"Guide pp?\.(\d{1,3})(?:\s*[-–]\s*(\d{1,3}))?")
TIER_A_TRAP_TEXT = ("CONDITIONAL FLOW REGIME", "longer than necessary", "GOVERNMENT data",
                    "INVERTED POLARITY", "WARNING_DO_NOT_USE")
HOST_ROW_ON = {"80": ["7.1", "7.2"], "81": ["7.3"], "82": ["7.5"], "83": ["6.2"], "84": ["6.1", "6.4"]}
REQUIRED_ALL = ("id", "pillar", "tier", "review_status", "name", "category_official", "question",
                "scoring", "scoring_tree", "exceptions", "disambiguation")
REQUIRED_AB = ("definition", "coding_rules", "disambiguation")
# Every Tier A and Tier B block carries the same elements as the pillar 6-7 blocks (decision D15).
REQUIRED_FULL = ("weight", "scoring_features", "guide_examples", "null_statement", "sources")
SOURCE_KEYS = ("guide_heading", "guide_pages", "faq_pages", "methodology_row", "template_row")
SHARED_WEIGHT = re.compile(r"^12\.4\.\d$")   # the Guide gives 12.4 one weight; its sub-indicators carry null
ID_IN_PROSE = re.compile(r"(?<![\w.])(\d{1,2}\.\d{1,2}(?:\.\d)?)(?![\w]|\.\d)")

errs: list[str] = []
info: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        errs.append(msg)


def norm_text(s: str) -> str:
    s = (s or "").replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    return re.sub(r"\s+", " ", s).replace("- ", "-").strip().lower()


def load_yaml(p: Path):
    return yaml.safe_load(p.read_text(encoding="utf-8"))


# --- 0. indicator order -----------------------------------------------------
order = load_yaml(OUT / "indicator_order.yaml")
entries = order["indicators"]
ids = [e["id"] for e in entries]
check(len(ids) == 62 and len(set(ids)) == 62, f"order: expected 62 unique IDs, got {len(ids)}/{len(set(ids))}")
for e in entries:
    try:
        check(normalize(e["id"]) == e["id"], f"order: {e['id']!r} is not canonical decimal text")
        check(pillar_of(e["id"]) == e["pillar"], f"order: {e['id']} pillar {e['pillar']} wrong")
    except BadIndicatorId:
        errs.append(f"order: bad ID {e['id']!r}")
in_scope = [e["id"] for e in entries if e["status"] == "in_scope"]
check(len(in_scope) == 61, f"order: expected 61 in scope, got {len(in_scope)}")
check("6.5" in (order.get("out_of_scope") or {}) and "6.5" not in in_scope, "order: 6.5 must be declared out of scope")
# coverage marks (decisions D13 and D14): what the tool automates, and why a manual indicator is manual
marks = order.get("coverage_marks") or {}
check(bool(marks.get("reasons")) and bool(marks.get("nature_codes")) and bool(marks.get("classes")),
      "order: coverage_marks must carry classes, reasons and nature_codes (run build_indicator_order.py)")
coverage_count = Counter()
for e in entries:
    cov, why, nature = e.get("coverage"), e.get("coverage_reason"), e.get("answer_nature")
    coverage_count[cov] += 1
    if e["status"] != "in_scope":
        check(cov == "excluded", f"order: {e['id']} is out of scope, so coverage must be 'excluded'")
        continue
    check(cov in ("automated", "manual"), f"order: {e['id']} coverage {cov!r} must be automated or manual")
    check(why is None if cov == "automated" else why in ("scope", "practice"),
          f"order: {e['id']} coverage_reason {why!r} does not fit coverage {cov!r}")
    check(bool(nature) and all(c in (marks.get("nature_codes") or {}) for c in nature or []),
          f"order: {e['id']} answer_nature {nature!r} must list known nature codes")
    if e.get("evidence") == "practice" and cov == "manual":
        check(why == "practice", f"order: {e['id']} is practice-based, so its manual-check reason must be 'practice'")
check(coverage_count["automated"] >= 1, "order: no indicator is marked automated")
trap_rows = {str(t["template_row"]) for t in order.get("host_mapping_traps", [])}
check({"80", "81", "82", "83", "84", "85"} <= trap_rows, f"order: host trap rows missing: {sorted({'80','81','82','83','84','85'} - trap_rows)}")
if TEMPLATE_FINAL.exists():
    ws = openpyxl.load_workbook(TEMPLATE_FINAL, data_only=True)["Indicator Reference"]
    tmpl = []
    for r in range(4, ws.max_row + 1):
        b = ws.cell(r, 2).value
        if str(ws.cell(r, 1).value or "").lower().startswith("the five mapping traps"):
            break
        if b is not None:
            tmpl.append((str(b).strip(), str(ws.cell(r, 3).value or "").strip()))
    check([t[0] for t in tmpl] == ids, "order: IDs/order differ from the template's Indicator Reference")
    names = {e["id"]: e["name"] for e in entries}
    check(all(names.get(i) == n for i, n in tmpl), "order: names differ from the template's Indicator Reference")
else:
    info.append("template not present: order not re-checked against the Indicator Reference")

# --- 1. codebook -------------------------------------------------------------
meth = load_methodology()
hand = load_yaml(OUT / "indicators.yaml")
check(not (OUT / "indicators_generated.yaml").exists(),
      "codebook: indicators_generated.yaml exists, but the codebook is one file (indicators.yaml) since 2026-09-13")
defined = Counter()
blocks: dict[str, dict] = {}
file_order: list[str] = []
for b in hand["indicators"]:
    try:
        iid = normalize(b["id"])
    except BadIndicatorId:
        errs.append(f"codebook: bad id {b.get('id')!r}")
        continue
    defined[iid] += 1
    blocks[iid] = b
    file_order.append(iid)
    check(isinstance(b["id"], str) and b["id"] == iid, f"codebook: id {b['id']!r} must be quoted decimal text")
    check(b.get("tier") in ("A", "B", "C"), f"codebook {iid}: tier must be A, B or C")
for iid in in_scope:
    check(defined[iid] == 1, f"codebook: {iid} defined {defined[iid]} times (must be exactly once)")
for iid in defined:
    check(iid in in_scope, f"codebook: {iid} is not an in-scope ID")
check(file_order == [i for i in in_scope if i in defined],
      "codebook: blocks are not in host order (python scripts/build_indicators_from_methodology.py --reorder)")
check(set(hand.get("tiers") or {}) == {"A", "B", "C"}, "codebook: the top-level 'tiers' key must describe A, B and C")
check("6.5" in (hand.get("scope", {}).get("out_of_scope") or {}), "codebook: 6.5 exclusion missing from indicators.yaml scope")
itext = (OUT / "indicators.yaml").read_text(encoding="utf-8")
for phrase in TIER_A_TRAP_TEXT:
    check(phrase in itext, f"indicators.yaml: Tier A trap text missing: {phrase}")

tier_count = Counter()
by_id = {e["id"]: e for e in entries}
for iid, b in blocks.items():
    tier = b.get("tier")
    tier_count[tier] += 1
    for k in REQUIRED_ALL:
        check(k in b, f"codebook {iid}: missing {k}")
    if tier in ("A", "B"):
        for k in REQUIRED_AB:
            check(bool(b.get(k)), f"codebook {iid}: tier {tier} needs non-empty {k}")
    check(b.get("pillar") == pillar_of(iid), f"codebook {iid}: pillar {b.get('pillar')} wrong")
    # 1b methodology cross-check
    m = meth.get(iid)
    check(m is not None, f"codebook {iid}: no methodology row")
    if m:
        check(norm_text(b.get("category_official", "")) == norm_text(category_first_line(m["category"])),
              f"codebook {iid}: category_official != methodology: {category_first_line(m['category'])!r}")
        want = score_values(m["possible_scores"])
        got = [float(v) for v in (b.get("scoring") or {}).get("values", [])]
        check(got == want, f"codebook {iid}: scoring.values {got} != methodology {want}")
        tree = b.get("scoring_tree") or []
        check(len(tree) == len(want), f"codebook {iid}: {len(tree)} branches for {len(want)} scores")
        if tree:
            check("else" in tree[-1], f"codebook {iid}: last scoring branch must be else")
            branch_scores = [float(t["score"]) if "score" in t else float(t["else"]["score"]) for t in tree]
            check(branch_scores == want, f"codebook {iid}: branch scores {branch_scores} != {want}")
    # 1c citations
    if tier in ("A", "B"):
        if b.get("definition"):
            check(bool(CITE.search(str(b["definition"]))), f"codebook {iid}: definition lacks a citation")
        for fld in ("coding_rules", "exceptions", "disambiguation"):
            for line in b.get(fld) or []:
                check(bool(CITE.search(str(line))), f"codebook {iid}: {fld} line lacks a citation: {str(line)[:70]}")
        if str(b.get("name", "")).startswith("Lack of"):
            check(b.get("polarity") == "inverted" or "INVERTED" in json.dumps(b.get("disambiguation")),
                  f"codebook {iid}: 'Lack of' indicator must declare inverted polarity")
        # 1d same elements on every Tier A/B block
        for k in REQUIRED_FULL:
            check(k in b, f"codebook {iid}: missing {k}")
        for fld in ("scoring_features", "guide_examples"):
            check(isinstance(b.get(fld, []), list), f"codebook {iid}: {fld} must be a list")
            for line in b.get(fld) or []:
                check(bool(CITE.search(str(line))), f"codebook {iid}: {fld} line lacks a citation: {str(line)[:70]}")
        w = b.get("weight")
        if SHARED_WEIGHT.match(iid):
            check(w is None, f"codebook {iid}: weight must be null (the Guide gives 12.4 one shared weight)")
        else:
            check(isinstance(w, (int, float)) and 0 < w <= 1, f"codebook {iid}: weight {w!r} must be a fraction of 1")
        check(norm_text(b.get("question", "")) != norm_text(b.get("definition", "")),
              f"codebook {iid}: question repeats the definition")
        check(str(b.get("null_statement") or "").lower().startswith("no "), f"codebook {iid}: null_statement must start with 'no'")
        src = b.get("sources") or {}
        for k in SOURCE_KEYS:
            check(k in src, f"codebook {iid}: sources lacks {k}")
        if m:
            check(src.get("methodology_row") == m["row"], f"codebook {iid}: sources.methodology_row {src.get('methodology_row')} != {m['row']}")
        check(src.get("template_row") == by_id[iid]["template_row"],
              f"codebook {iid}: sources.template_row {src.get('template_row')} != {by_id[iid]['template_row']}")
        check(b.get("polarity") in (None, "inverted"), f"codebook {iid}: polarity must be 'inverted' or absent")
        check(b.get("level") in (None, "economy"), f"codebook {iid}: level must be 'economy' or absent")
        if b.get("level") == "economy":
            check(b.get("polarity") == "inverted", f"codebook {iid}: level economy is only for inverted framework indicators")
            check(bool(b.get("framework_name")), f"codebook {iid}: level economy needs framework_name")
        else:
            check("framework_name" not in b, f"codebook {iid}: framework_name without level economy")
    blob = json.dumps(b, ensure_ascii=False)
    for mm in GUIDE_PAGE.finditer(blob):
        for pg in (mm.group(1), mm.group(2)):
            if pg:
                check(1 <= int(pg) <= 118, f"codebook {iid}: Guide page {pg} outside the printed range")
for row, targets in HOST_ROW_ON.items():
    for iid in targets:
        if iid in blocks:
            check(f"Indicator Reference row {row}" in json.dumps(blocks[iid], ensure_ascii=False),
                  f"codebook {iid}: host trap row {row} not encoded")
pillar_weight = defaultdict(float)
for iid, b in blocks.items():
    if isinstance(b.get("weight"), (int, float)):
        pillar_weight[b["pillar"]] += b["weight"]
for p, total in pillar_weight.items():
    check(total <= 1.03, f"codebook: pillar {p} block weights sum to {total:.2f}")


# 1e roll-up fields (decision D17): what an absence scores, and the count rule as data
rollup = load_yaml(DATA / "rollup_fields.yaml")
absence_count = Counter()
for iid, b in blocks.items():
    values = [float(v) for v in (b.get("scoring") or {}).get("values", [])]
    check("absence_score" in b, f"codebook {iid}: missing absence_score (run build_rollup_fields.py)")
    check({k: b[k] for k in ROLLUP_KEYS if k in b} == rollup_wanted(iid, rollup),
          f"codebook {iid}: absence_score, absence_basis or count_rule differs from scripts/data/rollup_fields.yaml (run build_rollup_fields.py)")
    a = b.get("absence_score")
    check(a is None or (isinstance(a, (int, float)) and float(a) in values),
          f"codebook {iid}: absence_score {a!r} must be null or one of scoring.values {values}")
    check(bool(CITE.search(str(b.get("absence_basis") or ""))), f"codebook {iid}: absence_basis missing or without a citation")
    if b.get("polarity") == "inverted":
        check(a is None, f"codebook {iid}: an inverted block's absence is its top score, so absence_score must be null")
    absence_count["unscored" if a is None else "scored"] += 1
    rule = b.get("count_rule")
    if rule is None:
        continue
    for k in ("unit", "counts", "counted_as", "method", "counted_scores", "otherwise", "needs", "basis"):
        check(k in rule, f"codebook {iid}: count_rule lacks {k}")
    check(rule.get("unit") in ("measure", "sector", "company", "product", "procedure"), f"codebook {iid}: count_rule.unit {rule.get('unit')!r} unknown")
    check(rule.get("counted_as") == "law", f"codebook {iid}: count_rule.counted_as must be 'law'")
    check(rule.get("otherwise") == "highest_verified_score", f"codebook {iid}: count_rule.otherwise must be highest_verified_score")
    counted = [float(x) for x in rule.get("counted_scores") or []]
    check(bool(counted) and all(x in values and x > 0 for x in counted),
          f"codebook {iid}: count_rule.counted_scores {counted} must be non-zero values of the block's scale")
    if rule.get("method") == "threshold":
        steps = rule.get("thresholds") or []
        check(bool(steps) and "cap" not in rule, f"codebook {iid}: a threshold count_rule needs thresholds and no cap")
        for t in steps:
            check(isinstance(t.get("at_least"), int) and t["at_least"] >= 2 and float(t.get("score", -1)) in values
                  and float(t.get("score", -1)) > max(counted, default=1),
                  f"codebook {iid}: count_rule threshold {t} must count two or more and give a higher value of the block's scale")
    elif rule.get("method") == "sum":
        check(float(rule.get("cap", -1)) in values and "thresholds" not in rule, f"codebook {iid}: a sum count_rule needs a cap on the block's scale and no thresholds")
    else:
        errs.append(f"codebook {iid}: count_rule.method {rule.get('method')!r} must be threshold or sum")
    check(isinstance(rule.get("needs"), list) and all(set(n) == {"fact", "why"} for n in rule.get("needs") or []),
          f"codebook {iid}: count_rule.needs must be a list of {{fact, why}}")
    check((rule.get("unit") == "measure") or bool(rule.get("needs")), f"codebook {iid}: a count_rule whose unit is not a measure must say what the roll-up needs")
    check(bool(CITE.search(str(rule.get("basis") or ""))), f"codebook {iid}: count_rule.basis lacks a citation")
    cited = {int(pg) for mm in GUIDE_PAGE.finditer(str(rule.get("basis") or "")) for pg in mm.groups() if pg}
    check(cited <= set((b.get("sources") or {}).get("guide_pages") or []), f"codebook {iid}: count_rule.basis cites Guide pages {sorted(cited)} outside the block's sources.guide_pages")
# The mapping stage hand-coded this rule for 6.1 and 6.2 until D17; the declaration must reproduce it exactly.
for iid in ("6.1", "6.2"):
    r = blocks.get(iid, {}).get("count_rule") or {}
    check((r.get("method"), r.get("counted_scores"), r.get("thresholds"), r.get("otherwise"), r.get("needs"))
          == ("threshold", [0.5], [{"at_least": 2, "score": 1}], "highest_verified_score", []),
          f"codebook {iid}: count_rule must state 'two or more distinct half-point measures score 1' and nothing else")
info.append(f"roll-up fields: absence_score scored on {absence_count['scored']} blocks and null on {absence_count['unscored']}; "
            f"count_rule on {sum(1 for b in blocks.values() if 'count_rule' in b)}, of which "
            f"{sum(1 for b in blocks.values() if (b.get('count_rule') or {}).get('needs'))} need a fact the roll-up does not have")


def named_siblings(b: dict) -> set[str]:
    text = re.sub(r"RDTII 2\.1", "RDTII", " ".join(str(x) for f in ("coding_rules", "exceptions", "disambiguation")
                                                    for x in b.get(f) or []))
    return {t for t in ID_IN_PROSE.findall(text) if t in blocks} - {b["id"]}


# A trap is only useful if both blocks carry it: a run may load one indicator without the other.
one_sided = sorted(f"{a}->{o}" for a, b in blocks.items() for o in named_siblings(b)
                   if a not in named_siblings(blocks[o]) and blocks[o]["tier"] != "A")
info.append(f"sibling references not mirrored by the named block (pillar 6-7 blocks exempt): {len(one_sided)}"
            + (f", e.g. {one_sided[:6]}" if one_sided else ""))

# The coverage register is the human-readable twin of the coverage marks (decision D14). It lives in
# the planning folder, outside the repo, so it is compared only when RDTII_COVERAGE_REGISTER names it.
register_path = os.environ.get("RDTII_COVERAGE_REGISTER")
if register_path and Path(register_path).exists():
    reg_text = Path(register_path).read_text(encoding="utf-8")
    split_at = reg_text.find("## M. Manual check")
    reg_row = re.compile(r"^\| (\d{1,2}\.\d{1,2}(?:\.\d)?) \| [^|]* \| ([ABC]) \| ([A-Za-z, ]+?) \| ", re.M)
    reg_rows = {m.group(1): (m.group(2), [c.strip() for c in m.group(3).split(",")],
                             "automated" if m.start() < split_at else "manual")
                for m in reg_row.finditer(reg_text)}
    check(set(reg_rows) == set(in_scope), f"coverage register: its rows differ from the in-scope IDs: {sorted(set(reg_rows) ^ set(in_scope))[:8]}")
    stale_tier = []
    for iid, (reg_tier, reg_nature, reg_class) in reg_rows.items():
        e = by_id.get(iid)
        if not e:
            continue
        check(e.get("answer_nature") == reg_nature, f"coverage register: {iid} nature {reg_nature} != instrument {e.get('answer_nature')}")
        check(e.get("coverage") == reg_class, f"coverage register: {iid} is {reg_class} there and {e.get('coverage')} in the instrument")
        if blocks.get(iid, {}).get("tier") != reg_tier:
            stale_tier.append(iid)
    info.append("coverage register compared: classes and nature codes agree for all " + str(len(reg_rows))
                + (f"; its Tier column is out of date for {len(stale_tier)} indicators (the instrument has no Tier C block now)"
                   if stale_tier else ""))
else:
    info.append("coverage register not compared (set RDTII_COVERAGE_REGISTER to COVERAGE_AND_MANUAL_CHECKS.md)")

# --- 2. guide refs -------------------------------------------------------------
refs = {normalize(k): v for k, v in (load_yaml(DATA / "guide_refs.yaml") or {}).items()}
for iid in in_scope:
    r = refs.get(iid)
    check(bool(r and r.get("asks") and r.get("asks_page")), f"guide_refs: {iid} missing defining sentence")
guide_text_path = os.environ.get("RDTII_GUIDE_TEXT")
guide_checked = 0
if guide_text_path and Path(guide_text_path).exists():
    parts = re.split(r"\n=== PDF PAGE (\d+) ===\n", Path(guide_text_path).read_text(encoding="utf-8"))
    printed = {int(parts[i]) - 12: parts[i + 1] for i in range(1, len(parts), 2)}
    for iid, r in refs.items():
        if not (r and r.get("asks")):
            continue
        page = printed.get(r["asks_page"], "") + " " + printed.get(r["asks_page"] + 1, "")
        check(norm_text(r["asks"]) in norm_text(page), f"guide_refs {iid}: sentence not verbatim on printed p.{r['asks_page']}")
        guide_checked += 1
else:
    info.append("Guide sentences not machine-checked (set RDTII_GUIDE_TEXT to a page-numbered Guide extract)")

# --- 3. policies ---------------------------------------------------------------
pol = load_yaml(OUT / "policies.yaml")
for k in ("source_hierarchy", "citation_url_preference", "conflict_rule", "citation_contract",
          "edge_cases", "measure_inclusion", "scoring_policy", "id_policy"):
    check(k in pol, f"policies.yaml: missing {k}")
for k in ("no_provision_found", "repealed", "broken_url", "same_provision_two_indicators",
          "one_indicator_many_laws", "sectoral_and_horizontal", "bad_country_input",
          "dual_processing_and_storage", "unspecified_retention_period",
          "datacentre_rules_without_mandate", "government_data_measure",
          "amending_act_cited_instead_of_principal"):
    check(k in pol.get("edge_cases", {}), f"policies.yaml: edge case missing: {k}")
for k in ("practice_based", "non_regulatory", "enforced_only"):
    check(k in pol.get("measure_inclusion", {}), f"policies.yaml: measure_inclusion.{k} missing")
check("economy_level_indicators" in pol.get("scoring_policy", {}), "policies.yaml: scoring_policy.economy_level_indicators missing")
# indicator_sets: machine-readable lists that must restate the blocks and the order file exactly
sets = pol.get("indicator_sets") or {}
want_sets = {
    "inverted": [i for i in in_scope if blocks.get(i, {}).get("polarity") == "inverted"],
    "economy_level": [i for i in in_scope if blocks.get(i, {}).get("level") == "economy"],
    "practice_based": [i for i in in_scope if i in (order.get("practice_based") or {})],
    "non_regulatory": list(order.get("non_regulatory_indicators") or []),
}
for k, want_ids in want_sets.items():
    check(sets.get(k) == want_ids, f"policies.yaml: indicator_sets.{k} {sets.get(k)} != {want_ids} (from the blocks and the order file)")
# The mapping stage lifts the inverted IDs out of this sentence, so it has to name the same indicators.
polarity_prose = re.sub(r"RDTII 2\.1", "RDTII", str(pol.get("scoring_policy", {}).get("polarity") or ""))
prose_ids = {t for t in ID_IN_PROSE.findall(polarity_prose) if t in blocks}
check(prose_ids == set(want_sets["inverted"]),
      f"policies.yaml: scoring_policy.polarity names {sorted(prose_ids ^ set(want_sets['inverted']))} differently from the blocks' polarity")

# --- 4. signatures -------------------------------------------------------------
gold = [json.loads(l) for l in (OUT / "gold" / "gold_set.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
suspect_keys = {(g["provenance"]["sheet"], g["provenance"]["row"]) for g in gold
                if (g.get("label_flag") or {}).get("status") in ("suspect", "host_marked")}
all_rows = {(r["sheet"], r["row"]): r for r in load_all()}
sig_dir = OUT / "signatures"
files = {p.stem: p for p in sig_dir.glob("*.yaml")}
check(set(files) == set(in_scope), f"signatures: files differ from in-scope IDs; missing {sorted(set(in_scope)-set(files))[:8]} extra {sorted(set(files)-set(in_scope))[:8]}")
n_exemplars, exemplar_keys = 0, defaultdict(set)
for iid in in_scope:
    p = files.get(iid)
    if not p:
        continue
    sig = load_yaml(p)
    check(sig.get("indicator") == iid, f"signatures {iid}: indicator field {sig.get('indicator')!r}")
    if iid in blocks:
        check(sig.get("tier") == blocks[iid].get("tier"), f"signatures {iid}: tier {sig.get('tier')} != codebook {blocks[iid].get('tier')}")
    check(len(sig.get("keywords", [])) >= 8, f"signatures {iid}: too few keywords")
    check(len(sig.get("definition_text", "")) > 100, f"signatures {iid}: definition_text too short")
    check(bool(sig.get("exemplar_law_types")), f"signatures {iid}: exemplar_law_types missing")
    check(bool(sig.get("negative_signals")), f"signatures {iid}: negative_signals missing")
    exs = sig.get("exemplars", [])
    check(len(exs) >= 3, f"signatures {iid}: only {len(exs)} exemplars (need >=3)")
    check(len({e["economy"] for e in exs}) >= 2, f"signatures {iid}: exemplars from fewer than 2 economies")
    for e in exs:
        key = (e["provenance"]["sheet"], e["provenance"]["row"])
        src = all_rows.get(key)
        check(src is not None, f"signatures {iid}: exemplar source row not found: {key}")
        if src is None:
            continue
        n_exemplars += 1
        exemplar_keys[key].add(iid)
        check(src["indicator"] == iid, f"signatures {iid}: exemplar {key} is {src['indicator']}")
        check(src["raw_score"] == e["score"], f"signatures {iid}: exemplar {key} score drift")
        check(not src["strikethrough"], f"signatures {iid}: exemplar {key} struck through")
        check(key not in suspect_keys, f"signatures {iid}: exemplar {key} is flagged suspect or host-marked Not correct")
        src_law = re.sub(r"\s+", " ", src["law"] or "")
        check(src_law.startswith(re.sub(r"\s+", " ", e["law"] or "")[:30].split("…")[0]),
              f"signatures {iid}: exemplar {key} law text drift")

# --- 5. gold set -----------------------------------------------------------------
fresh = [r for r in (parse_workbook(ROUND1, ROUND1_SHEETS, "round1") + parse_workbook(ROUND2, ROUND2_SHEETS, "round2"))
         if not r["strikethrough"]]
check(len(gold) == len(fresh), f"gold rows {len(gold)} != workbook rows {len(fresh)}")
fresh_by_key = {(r["sheet"], r["row"]): r for r in fresh}
flag_count = Counter()
for g in gold:
    key = (g["provenance"]["sheet"], g["provenance"]["row"])
    src = fresh_by_key.get(key)
    check(src is not None, f"gold {g['gold_id']}: source row gone")
    if src is None:
        continue
    check(g["gold_id"] == src["gold_id"], f"gold {g['gold_id']}: id != {src['gold_id']}")
    for fld in ("economy", "indicator", "raw_score", "law", "coverage"):
        check(g[fld] == src[fld if fld != "raw_score" else "raw_score"], f"gold {g['gold_id']}: {fld} round-trip mismatch")
    check(g["indicator"] in in_scope, f"gold {g['gold_id']}: indicator {g['indicator']} not in scope")
    lf = g.get("label_flag")
    if lf:
        check(lf.get("status") in ("suspect", "advisory", "host_marked", "candidate"), f"gold {g['gold_id']}: bad flag status {lf.get('status')}")
        check(bool(lf.get("reason")), f"gold {g['gold_id']}: flag without reason")
        if lf.get("status") in ("suspect", "advisory"):
            check(bool(lf.get("basis")), f"gold {g['gold_id']}: reviewed flag without basis")
        flag_count[lf["status"]] += 1
    check(sorted(g.get("exemplar_for") or []) == sorted(exemplar_keys.get(key, set())),
          f"gold {g['gold_id']}: exemplar_for {g.get('exemplar_for')} != signatures {sorted(exemplar_keys.get(key, set()))}")
gold_ind = {g["indicator"] for g in gold}
check(gold_ind == set(in_scope), f"gold: indicators without rows: {sorted(set(in_scope) - gold_ind)}")

# --- 6. hygiene -----------------------------------------------------------------
for p in [OUT / "indicators.yaml", OUT / "policies.yaml", OUT / "indicator_order.yaml",
          DATA / "signature_spec.yaml", DATA / "curated_exemplars.yaml", *files.values()]:
    if p.exists():
        hits = LEGACY.findall(p.read_text(encoding="utf-8"))
        shown = p.relative_to(REPO) if p.is_relative_to(REPO) else p.relative_to(SCRIPTS.parent)
        check(not hits, f"{shown}: legacy IDs {sorted(set(hits))[:5]}")


def same_content(a: Path, b: Path) -> bool:
    """Byte comparison that ignores CRLF against LF: git checkouts on Windows (core.autocrlf) differ
    in line endings only, and the committed content is the same."""
    return a.read_bytes().replace(b"\r\n", b"\n") == b.read_bytes().replace(b"\r\n", b"\n")


def tree_diff(a: Path, b: Path) -> list[str]:
    """Relative paths that differ between two folders: missing on either side, or different content."""
    fa = {p.relative_to(a).as_posix() for p in a.rglob("*") if p.is_file() and "__pycache__" not in p.parts}
    fb = {p.relative_to(b).as_posix() for p in b.rglob("*") if p.is_file() and "__pycache__" not in p.parts}
    return sorted(fa ^ fb) + sorted(r for r in fa & fb if not same_content(a / r, b / r))


canon_ids = SCRIPTS / "indicator_ids.py"
if VENDORED_IDS.exists():
    check(same_content(canon_ids, VENDORED_IDS), "indicator_ids.py differs from p3-map/config/indicator_ids.py")
else:
    info.append(f"mapping stage not found at {P3MAP} (set RDTII_FINALE_REPO): indicator_ids.py and vendored-copy checks skipped")


vendored_ok = None
if VENDORED.exists():
    vendored_diff = tree_diff(OUT, VENDORED)
    vendored_ok = not vendored_diff
    info.append("vendored copy p3-map/contracts/instrument/ is " + ("identical" if vendored_ok else
                f"NOT re-vendored yet ({len(vendored_diff)} files differ, e.g. {vendored_diff[:3]})"))
if "--require-vendored" in sys.argv:
    check(bool(vendored_ok), "vendored copy differs from output/" if VENDORED.exists()
          else f"--require-vendored: no vendored copy at {VENDORED}")

# --- report ----------------------------------------------------------------------
for i in info:
    print("INFO  -", i)
if errs:
    print(f"FAIL — {len(errs)} problem(s):")
    for e in errs[:200]:
        print("  -", e)
    if len(errs) > 200:
        print(f"  ... and {len(errs) - 200} more")
    sys.exit(1)
print(f"PASS — {len(in_scope)}/{len(ids)} indicators in scope (6.5 excluded); tiers "
      f"{dict(sorted(tier_count.items()))}; coverage automated {coverage_count['automated']} / manual "
      f"{coverage_count['manual']}; category names + score sets machine-match the methodology "
      f"sheet for all {len(in_scope)}; {n_exemplars} exemplars round-trip; gold {len(gold)} rows round-trip 1:1 "
      f"(flags {dict(sorted(flag_count.items()))}); Guide sentences checked {guide_checked}; policies complete.")
