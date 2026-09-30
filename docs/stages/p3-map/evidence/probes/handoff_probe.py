"""What the instrument hand-off actually changes for the mapping stage.

Loads the workshop instrument beside the currently vendored one and reports the automated set,
the signature exemplars' economies (the leave-one-economy-out question, B10), and how each of the
nine query documents changes. Reads only; copies nothing.
"""
from __future__ import annotations

import sys
from collections import Counter

sys.path.insert(0, "C:/Users/woshi/Desktop/rdtii-rocky-finale/stages/p3-map")
WS = "C:/Users/woshi/Desktop/rdtii-finale-0-instrument/instrument/output"


def main() -> None:
    from config.instrument import load

    now = load()                 # vendored, Round 1
    new = load(WS)               # what the hand-off brings

    print(f"vendored : vintage {now.vintage:8s} {len(now.blocks):3d} blocks  automated {len(now.ids)}: {list(now.ids)}")
    print(f"workshop : vintage {new.vintage:8s} {len(new.blocks):3d} blocks  automated {len(new.ids)}: {list(new.ids)}")
    print(f"automated set identical: {list(now.ids) == list(new.ids) or sorted(now.ids) == sorted(new.ids)}")
    print()

    print("exemplars on the nine automated signatures, by economy")
    print(f"{'ind':6s} {'vendored':>9s} {'workshop':>9s}   economies of the workshop exemplars (first 2 = the query)")
    leak = []
    for ind in new.ids:
        a = (now.signature(ind).get("exemplars") or []) if ind in now.ids else []
        b = new.signature(ind).get("exemplars") or []
        econs = [str(e.get("economy") or e.get("jurisdiction") or "?") for e in b]
        used = econs[:2]
        print(f"{ind:6s} {len(a):>9d} {len(b):>9d}   used={used}  all={dict(Counter(econs))}")
        for e in used:
            if e in ("CN", "LA", "TL", "China", "Lao PDR", "Timor-Leste"):
                leak.append((ind, e))
    print()
    print("first-two exemplars drawn from an economy we map fresh:", leak or "none")
    print()

    # what the query documents become
    from config.settings import INDICATORS
    print(f"settings.INDICATORS right now: {len(INDICATORS)} -> {list(INDICATORS)}")
    print()
    print("query document length, vendored vs workshop")
    print(f"{'ind':6s} {'now':>7s} {'after':>7s}   head of the workshop query")
    for ind in new.ids:
        def build(ins):
            sig = ins.signature(ind)
            parts = [sig.get("name", ""), sig.get("definition_text", ""),
                     " ".join(sig.get("keywords", []))]
            for ex in (sig.get("exemplars") or [])[:2]:
                if (ex.get("impact") or ""):
                    parts.append((ex.get("impact") or "")[:400])
            return "\n".join(p for p in parts if p)
        qn = build(now) if ind in now.ids else ""
        qa = build(new)
        print(f"{ind:6s} {len(qn):>7d} {len(qa):>7d}   {qa[:70]!r}")


if __name__ == "__main__":
    main()
