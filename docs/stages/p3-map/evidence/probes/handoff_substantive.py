"""Of the codebook changes the hand-off brings, how much could flip a verdict?

Every one of the nine blocks differs. Two kinds of edit cannot change a judgement:
  - the ID form ('P6-I4' -> '6.4'), which is the migration itself
  - an added Guide/Reference citation, e.g. ' (Guide p.50)'
This normalises both away and reports what survives, per indicator and per field. What survives is
the text that could change a verdict, and therefore the scope of any re-judge.
"""
from __future__ import annotations

import json
import re
import sys

sys.path.insert(0, "C:/Users/woshi/Desktop/rdtii-rocky-finale/stages/p3-map")
WS = "C:/Users/woshi/Desktop/rdtii-finale-0-instrument/instrument/output"
LEGACY = {"P6-I1": "6.1", "P6-I2": "6.2", "P6-I3": "6.3", "P6-I4": "6.4",
          "P7-I1": "7.1", "P7-I2": "7.2", "P7-I3": "7.3", "P7-I4": "7.4", "P7-I5": "7.5"}
CITE = re.compile(r"\s*\((?:Guide|Indicator Reference|Reference|Methodology)[^)]*\)")
RANGE = re.compile(r"\b6\.1-6\.4\b")


def norm(s: str) -> str:
    s = str(s)
    for a, b in LEGACY.items():
        s = s.replace(a, b)
    s = s.replace("P6-I1..P6-I4", "6.1-6.4").replace("6.1..6.4", "6.1-6.4")
    s = CITE.sub("", s)
    s = re.sub(r"[\u2018\u2019]", "'", s)
    s = re.sub(r"[\u201c\u201d]", '"', s)
    return re.sub(r"\s+", " ", s).strip()


def flat(v) -> str:
    if isinstance(v, (list, tuple)):
        return " || ".join(flat(x) for x in v)
    if isinstance(v, dict):
        return " || ".join(f"{k}={flat(v[k])}" for k in sorted(v))
    return norm(v)


def main() -> None:
    from config.instrument import load
    now, new = load(), load(WS)

    IGNORE = {"id", "tier", "review_status"}
    print("after normalising away the ID form and added citations:")
    print(f"{'ind':6s} {'fields':>7s} {'cosmetic':>9s} {'SUBSTANTIVE':>12s}   fields that really changed")
    tot_sub = 0
    detail = []
    for ind in new.ids:
        a, b = now.blocks[ind], new.blocks[ind]
        shared = sorted((set(a) & set(b)) - IGNORE)
        cosmetic, sub = 0, []
        for k in shared:
            if a[k] == b[k]:
                continue
            if flat(a[k]) == flat(b[k]):
                cosmetic += 1
            else:
                sub.append(k)
                detail.append((ind, k, flat(a[k]), flat(b[k])))
        tot_sub += len(sub)
        print(f"{ind:6s} {len(shared):>7d} {cosmetic:>9d} {len(sub):>12d}   {sub}")
    print(f"\nsubstantive field changes across all nine blocks: {tot_sub}")
    print(f"new fields added to every block: tier, review_status (+ level on 7.1, 7.2)")

    print("\n" + "=" * 100)
    print("every substantive change, in full")
    for ind, k, ta, tb in detail:
        print(f"\n### {ind} · {k}")
        if len(ta) < 700 and len(tb) < 700:
            print(f"  WAS: {ta}")
            print(f"  NOW: {tb}")
        else:
            import difflib
            sm = difflib.SequenceMatcher(None, ta.split(), tb.split())
            for tag, i1, i2, j1, j2 in sm.get_opcodes():
                if tag == "equal":
                    continue
                w_a = " ".join(ta.split()[i1:i2])[:300]
                w_b = " ".join(tb.split()[j1:j2])[:300]
                if tag == "delete":
                    print(f"  - {w_a}")
                elif tag == "insert":
                    print(f"  + {w_b}")
                else:
                    print(f"  - {w_a}")
                    print(f"  + {w_b}")


if __name__ == "__main__":
    main()
