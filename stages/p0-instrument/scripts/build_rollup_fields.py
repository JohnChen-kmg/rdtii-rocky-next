"""Write the two roll-up fields into the codebook blocks.

  python build_rollup_fields.py          rewrite the fields in output/indicators.yaml
  python build_rollup_fields.py --check  exit 1 if a block differs from the data file; write nothing

The values live in scripts/data/rollup_fields.yaml (decision D17):

  absence_score, absence_basis   on every block: what a cell scores when the tool searched the corpus
                                 and found no qualifying provision (one of the block's own values, or
                                 null for "leave the cell unscored"), and why
  count_rule                     on the blocks that score by how many measures an economy has: what is
                                 counted, which per-measure scores count, the thresholds, what applies
                                 otherwise, and the facts a verdict would need for an exact count

Blocks travel as text (codebook_file.py). The three keys are inserted just above each block's
`sources:` line and nothing else in the block is touched: the run stops if any other key of any
block would parse differently afterwards. None of the three is in the mapping prompt's allow-list.
"""
from __future__ import annotations

import json
import re
import sys

import yaml

from codebook_file import assemble, split
from rdtii_examples import DATA, REPO

OUT = REPO / "output"
CODEBOOK = OUT / "indicators.yaml"
FIELDS = DATA / "rollup_fields.yaml"
KEYS = ("absence_score", "absence_basis", "count_rule")
KEY_LINE = re.compile(r"^    ([A-Za-z_]+):")       # a block-level key: four spaces, then the key
RULE_ORDER = ("unit", "counts", "counted_as", "method", "counted_scores", "thresholds", "cap",
              "otherwise", "needs", "basis")


def q(s: str) -> str:
    """A string as a double-quoted YAML scalar on one line."""
    return json.dumps(" ".join(str(s).split()), ensure_ascii=False)


def num(x) -> str:
    return f"{x:g}"


def wanted(iid: str, data: dict) -> dict:
    """The three keys for one block, as values."""
    ab = data["absence"]
    if iid in ab["unscored"]:
        out = {"absence_score": None, "absence_basis": " ".join(ab["unscored"][iid].split())}
    else:
        src = ab["scored"].get(iid) or ab["default"]
        out = {"absence_score": src["score"],
               "absence_basis": " ".join(src["basis"].format(id=iid).split())}
    rule = data["count_rules"]["rules"].get(iid)
    if rule:
        out["count_rule"] = {k: (" ".join(rule[k].split()) if isinstance(rule[k], str) else rule[k])
                             for k in RULE_ORDER if k in rule}
    return out


def render(fields: dict) -> str:
    """The three keys as block text, four-space indent, one value per line."""
    score = fields["absence_score"]
    lines = [f"    absence_score: {'null' if score is None else num(score)}",
             f"    absence_basis: {q(fields['absence_basis'])}"]
    rule = fields.get("count_rule")
    if rule:
        lines.append("    count_rule:")
        for k in RULE_ORDER:
            if k not in rule:
                continue
            v = rule[k]
            if k == "counted_scores":
                lines.append(f"      {k}: [{', '.join(num(x) for x in v)}]")
            elif k == "thresholds":
                lines.append(f"      {k}:")
                lines += [f"        - {{at_least: {t['at_least']}, score: {num(t['score'])}}}" for t in v]
            elif k == "needs":
                if not v:
                    lines.append(f"      {k}: []")
                else:
                    lines.append(f"      {k}:")
                    lines += [f"        - {{fact: {n['fact']}, why: {q(n['why'])}}}" for n in v]
            elif k == "cap":
                lines.append(f"      {k}: {num(v)}")
            elif k in ("counts", "basis"):
                lines.append(f"      {k}: {q(v)}")
            else:
                lines.append(f"      {k}: {v}")
    return "\n".join(lines) + "\n"


def strip_keys(block: str) -> str:
    """The block text without the three keys (a key runs until the next block-level key)."""
    out, skipping = [], False
    for line in block.splitlines(keepends=True):
        m = KEY_LINE.match(line)
        if m:
            skipping = m.group(1) in KEYS
        if not skipping:
            out.append(line)
    return "".join(out)


def with_fields(block: str, fields: dict) -> str:
    lines = strip_keys(block).splitlines(keepends=True)
    at = [i for i, ln in enumerate(lines) if ln.startswith("    sources:")]
    if len(at) != 1:
        raise SystemExit(f"block needs exactly one `sources:` line to anchor the fields, found {len(at)}")
    return "".join(lines[:at[0]]) + render(fields) + "".join(lines[at[0]:])


def main() -> int:
    data = yaml.safe_load(FIELDS.read_text(encoding="utf-8"))
    text = CODEBOOK.read_text(encoding="utf-8")
    order = yaml.safe_load((OUT / "indicator_order.yaml").read_text(encoding="utf-8"))["indicators"]
    cb = split(text)
    if assemble(cb, order) != text:
        raise SystemExit("indicators.yaml does not survive split and assemble unchanged; fix that first")
    before = {str(b["id"]): b for b in yaml.safe_load(text)["indicators"]}

    known = set(cb.blocks)
    for where, ids in (("absence.unscored", data["absence"]["unscored"]), ("absence.scored", data["absence"]["scored"]),
                       ("count_rules.rules", data["count_rules"]["rules"])):
        stray = sorted(set(map(str, ids)) - known)
        if stray:
            raise SystemExit(f"rollup_fields.yaml {where}: no block for {stray}")

    want = {iid: wanted(iid, data) for iid in cb.blocks}
    for iid in cb.blocks:
        cb.blocks[iid] = with_fields(cb.blocks[iid], want[iid])
    new_text = assemble(cb, order)

    after = {str(b["id"]): b for b in yaml.safe_load(new_text)["indicators"]}
    for iid, b in after.items():
        got = {k: b[k] for k in KEYS if k in b}
        if got != want[iid]:
            raise SystemExit(f"{iid}: the written fields do not parse back to the data file: {got}")
        rest = {k: v for k, v in b.items() if k not in KEYS}
        was = {k: v for k, v in before[iid].items() if k not in KEYS}
        if rest != was or list(rest) != list(was):
            raise SystemExit(f"{iid}: a key other than {KEYS} would change; nothing written")

    scored = sum(1 for f in want.values() if f["absence_score"] is not None)
    summary = (f"absence_score on {len(want)} blocks ({scored} scored, {len(want) - scored} unscored); "
               f"count_rule on {sum(1 for f in want.values() if 'count_rule' in f)}")
    if "--check" in sys.argv:
        if new_text != text:
            print("indicators.yaml is out of date with scripts/data/rollup_fields.yaml (run build_rollup_fields.py)")
            return 1
        print(f"up to date: {summary}")
        return 0
    if new_text == text:
        print(f"no change: {summary}")
        return 0
    CODEBOOK.write_text(new_text, encoding="utf-8", newline="\n")
    print(f"wrote {CODEBOOK.relative_to(REPO).as_posix()}: {summary}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
