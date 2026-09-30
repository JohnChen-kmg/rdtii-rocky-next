"""Stage A, Tier C — give every in-scope indicator a codebook block, built from host text when none exists.

  python build_indicators_from_methodology.py            add a Tier C block for each in-scope ID that
                                                         has none in output/indicators.yaml
  python build_indicators_from_methodology.py --check    compare each Tier C block with what the host
                                                         sheets give today; write nothing
  python build_indicators_from_methodology.py --reorder  also rewrite the file in host order when
                                                         nothing is missing
(Run it from any folder; it finds the instrument stage itself, see rdtii_examples.py.)

The codebook is one file with one block per indicator in host order (codebook_file.py). This script
never changes a block that exists: to take an indicator deeper, edit its block in place and raise
its `tier`. A new block restates only host text:

  category, criteria and possible scores   host methodology sheet (Round 1 database)
  name, exception note                     finale template, Indicator Reference sheet
  question / definition                    the Guide's defining sentence for the indicator,
                                           verbatim with its printed page (scripts/data/guide_refs.yaml)

Tier C blocks carry no traps, coding rules of our own or worked examples. The file's `tiers`
key says so, and rows mapped under a Tier C indicator must say so in Notes (decision D4).

The script refuses rather than guesses: an ID whose numbered criteria do not line up
one-to-one with its possible scores stops it.
"""
from __future__ import annotations

import re
import sys
from datetime import date

import yaml

from codebook_file import assemble, render_block, split
from indicator_ids import normalize
from rdtii_examples import DATA, REPO, category_first_line, load_methodology, score_values

ORDER = REPO / "output" / "indicator_order.yaml"
CODEBOOK = REPO / "output" / "indicators.yaml"
GUIDE_REFS = DATA / "guide_refs.yaml"

_NUMBERED = re.compile(r"^\s*(\d)\)\s*(.+?)\s*$")


def _num(v: float):
    return int(v) if float(v).is_integer() else float(v)


def parse_criteria(iid: str, criteria: str, n_scores: int) -> tuple[list[str], list[str]]:
    """Split host criteria text into numbered categories and free-standing note lines."""
    cats, notes = [], []
    for line in str(criteria).replace("\r", "").split("\n"):
        line = re.sub(r"\s+", " ", line).strip()
        if not line:
            continue
        m = _NUMBERED.match(line)
        if m:
            if int(m.group(1)) != len(cats) + 1:
                raise SystemExit(f"{iid}: criteria numbering out of sequence at {line!r}")
            cats.append(m.group(2))
        elif cats:
            notes.append(line)
        else:
            raise SystemExit(f"{iid}: text before the first numbered criterion: {line!r}")
    if len(cats) != n_scores:
        raise SystemExit(f"{iid}: {len(cats)} criteria for {n_scores} possible scores — refusing to guess")
    return cats, notes


def exception_texts(iid: str, category: str, host_note: str | None) -> list[str]:
    out, seen = [], set()
    parts = str(category).split("\n")[1:]
    for p in parts:
        p = re.sub(r"\s+", " ", p).strip()
        if p:
            key = re.sub(r"[^a-z0-9]", "", p.lower())
            seen.add(key)
            out.append(f"{p} (Methodology sheet {iid})")
    if host_note:
        note = re.sub(r"\s+", " ", host_note).strip()
        key = re.sub(r"[^a-z0-9]", "", note.lower())
        if not any(key.startswith(s[:40]) or s.startswith(key[:40]) for s in seen):
            out.append(f"{note} (Indicator Reference note)")
    return out


def tier_c_block(e: dict, meth: dict, refs: dict, order: dict) -> dict:
    """The Tier C block for one indicator entry of indicator_order.yaml, from host text only."""
    iid = e["id"]
    m = meth[iid]
    values = score_values(m["possible_scores"])
    cats, notes = parse_criteria(iid, m["criteria"], len(values))
    ref = refs.get(iid) or {}
    category = category_first_line(m["category"])
    if ref.get("asks"):
        asks = re.sub(r"\s+", " ", ref["asks"]).strip()
        question = f"{asks} (Guide p.{ref['asks_page']})"
    else:
        question = f"{category} (Methodology sheet {iid})"
    tree = []
    for i, (cat, v) in enumerate(zip(cats, values)):
        text = f"{cat} (Methodology sheet {iid})"
        if i == len(values) - 1:
            tree.append({"else": {"score": _num(v), "meaning": text}})
        else:
            tree.append({"if": text, "score": _num(v)})
    coding = [f"{n} (Methodology sheet {iid})" for n in notes]
    if e.get("evidence") == "practice":
        coding.append(f"{order['practice_based'][iid]}")
    return {
        "id": iid,
        "pillar": e["pillar"],
        "tier": "C",
        "review_status": f"extracted by script from host sheets on {date.today().isoformat()}; not reviewed",
        "name": e["name"],
        "category_official": category,
        "question": question,
        "definition": question,
        "scoring": {"values": [_num(v) for v in values],
                    "type": "binary" if len(values) == 2 else "ordinal"},
        "scoring_tree": tree,
        "coding_rules": coding,
        "exceptions": exception_texts(iid, m["category"], e.get("host_note")),
        "disambiguation": [],
        "sources": {
            "methodology_row": m["row"],
            "template_row": e["template_row"],
            "guide_pages": ref.get("guide_pages"),
            "guide_heading": ref.get("guide_heading"),
        },
    }


def main() -> None:
    order = yaml.safe_load(ORDER.read_text(encoding="utf-8"))
    refs = yaml.safe_load(GUIDE_REFS.read_text(encoding="utf-8")) if GUIDE_REFS.exists() else {}
    refs = {normalize(k): v for k, v in (refs or {}).items()}
    meth = load_methodology()

    text = CODEBOOK.read_text(encoding="utf-8")
    cb = split(text)
    existing = {str(b["id"]): b for b in yaml.safe_load(text)["indicators"]}
    if set(cb.blocks) != set(existing):
        raise SystemExit("indicators.yaml: the block layout and the YAML disagree; fix the file by hand first")
    in_scope = [e for e in order["indicators"] if e["status"] == "in_scope"]

    if "--check" in sys.argv:
        drift = []
        for e in in_scope:
            b = existing.get(e["id"])
            if b is None or b.get("tier") != "C":
                continue
            fresh = tier_c_block(e, meth, refs, order)
            keys = sorted((set(fresh) | set(b)) - {"review_status"})
            changed = [k for k in keys if fresh.get(k) != b.get(k)]
            if changed:
                drift.append(f"{e['id']}: {', '.join(changed)}")
        n_c = sum(1 for b in existing.values() if b.get("tier") == "C")
        print(f"checked {n_c} Tier C blocks against the host sheets: "
              + ("no differences" if not drift else f"{len(drift)} differ\n  " + "\n  ".join(drift)))
        sys.exit(1 if drift else 0)

    added = []
    for e in in_scope:
        if e["id"] not in cb.blocks:
            cb.blocks[e["id"]] = render_block(tier_c_block(e, meth, refs, order))
            added.append(e["id"])
    if not added and "--reorder" not in sys.argv:
        print(f"nothing to add: all {len(in_scope)} in-scope indicators have a block")
        return
    new_text = assemble(cb, order["indicators"])
    yaml.safe_load(new_text)  # must still parse
    CODEBOOK.write_text(new_text, encoding="utf-8", newline="\n")
    missing_refs = [i for i in added if not (refs.get(i) or {}).get("asks")]
    print(f"wrote {CODEBOOK.relative_to(REPO)}: added {len(added)} Tier C block(s) {added}"
          + (f"; no Guide sentence yet for {missing_refs}" if missing_refs else ""))


if __name__ == "__main__":
    main()
