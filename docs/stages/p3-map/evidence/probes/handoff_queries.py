"""Are the nine query documents byte-identical across the hand-off, and what is in the CN exemplar?"""
from __future__ import annotations

import hashlib
import json
import sys

sys.path.insert(0, "C:/Users/woshi/Desktop/rdtii-rocky-finale/stages/p3-map")
WS = "C:/Users/woshi/Desktop/rdtii-finale-0-instrument/instrument/output"


def build(ins, ind):
    sig = ins.signature(ind)
    parts = [sig.get("name", ""), sig.get("definition_text", ""), " ".join(sig.get("keywords", []))]
    for ex in (sig.get("exemplars") or [])[:2]:
        if (ex.get("impact") or ""):
            parts.append((ex.get("impact") or "")[:400])
    return "\n".join(p for p in parts if p)


def main() -> None:
    from config.instrument import load
    now, new = load(), load(WS)
    same = 0
    for ind in new.ids:
        a, b = build(now, ind), build(new, ind)
        ha = hashlib.sha256(a.encode()).hexdigest()[:12]
        hb = hashlib.sha256(b.encode()).hexdigest()[:12]
        ok = ha == hb
        same += ok
        print(f"{ind:6s} {ha} {hb} {'IDENTICAL' if ok else 'DIFFERS'}")
    print(f"\n{same}/9 query documents unchanged by the hand-off")

    print("\n--- 6.3 exemplars, workshop copy ---")
    for i, ex in enumerate((new.signature("6.3").get("exemplars") or [])):
        mark = " <== IN THE QUERY" if i < 2 else ""
        print(json.dumps(ex, ensure_ascii=False)[:600] + mark)
    print("\n--- and the same in the vendored copy, for provenance ---")
    for i, ex in enumerate((now.signature("6.3").get("exemplars") or [])[:2]):
        print(json.dumps(ex, ensure_ascii=False)[:600])


if __name__ == "__main__":
    main()
