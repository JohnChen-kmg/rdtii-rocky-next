"""Truncation audit over every AU HTML document in the hand-off (2026-07-17).

Why: the epubFrame view of legislation.gov.au renders one epub spine document at a time,
so frame captures of multi-volume compilations silently held volume 1 only (found by the
independent judge's substantive spot-check, 2026-07-17 — e.g. TIA 1979 stopped at
s.186J, losing Part 5-1A data retention).

Method — the strongest available in-file evidence, the compilation's OWN front matter:
every multi-volume compilation self-declares "This compilation is in N volumes" plus each
volume's section range ("Volume 2: sections 187‑300"). (A per-volume TOC cannot be used
alone: each volume carries only its own contents, so a volume-1-only capture has an
internally consistent TOC.) A document is TRUNCATED when it declares ≥2 volumes but the
sections of any later declared volume are absent from the body (CharSectno markers).
As a secondary check, every document's last TOC entry is compared against the body.

Usage:
  python tools/audit_au_truncation.py --handoff handoff1_v2 \
      --report docs/AU_HTML_TRUNCATION_AUDIT_2026-07-17.md [--json out.json]

Exit codes: 0 = no truncated documents; 2 = truncated documents found.
"""
from __future__ import annotations

import argparse
import html as html_mod
import json
import re
import sys
from pathlib import Path

DECL = re.compile(r"This\s+compilation\s+is\s+in\s+(\d+)\s+volumes?", re.I)
# "Volume 2: sections 187 ‑ 300" (any dash flavor; tolerate 'section')
VOL_RANGE = re.compile(
    r"Volume\s+(\d+)\s*:?\s*sections?\s+([0-9]+[A-Z]*)\s*[\-‐‑–—]\s*([0-9]+[A-Z]*)",
    re.I)
SECTNO = re.compile(r'class="CharSectno"[^>]*>\s*([0-9]+[A-Z]*)\s*<')
TOC_ENTRY = re.compile(r'class="TOC\d"[^>]*>(.*?)</p>', re.S)


def _plain(fragment: str) -> str:
    txt = re.sub(r"<[^>]+>", " ", fragment)
    txt = html_mod.unescape(txt)
    return re.sub(r"\s+", " ", txt).strip()


def _sect_key(s: str) -> tuple[int, str]:
    m = re.match(r"([0-9]+)([A-Z]*)", s)
    return (int(m.group(1)), m.group(2)) if m else (0, s)


def audit_document(text: str) -> dict:
    """Return the truncation verdict + evidence for one stored AU HTML document."""
    sections = SECTNO.findall(text)
    present = sorted(set(sections), key=_sect_key)
    out: dict = {
        "declared_volumes": 0,
        "volume_ranges": [],
        "sections_present": len(present),
        "first_section": present[0] if present else None,
        "last_section": present[-1] if present else None,
        "missing_volumes": [],
        "truncated": False,
    }
    # Complete-by-construction evidence: the fixed epub lane stamps every stored
    # artifact with "p1-epub-spine-doc i/n" markers, one per extracted volume.
    markers = {int(a) for a, _ in re.findall(r"p1-epub-spine-doc (\d+)/(\d+)", text)}
    spine_n = max((int(b) for _, b in re.findall(r"p1-epub-spine-doc (\d+)/(\d+)", text)),
                  default=0)
    out["epub_spine_docs"] = spine_n
    epub_complete = spine_n > 0 and markers == set(range(1, spine_n + 1))

    decl = DECL.search(text)
    if decl:
        out["declared_volumes"] = int(decl.group(1))
        # The volume map sits in the front matter right after the declaration. NOTE:
        # ranges are REPORTING evidence only — several acts define later volumes by
        # Schedule/Chapter (Customs Tariff) or dotted numbering (Criminal Code), which
        # no section-range parse can adjudicate. The verdict below does not rely on it.
        window = _plain(text[decl.start():decl.start() + 20000])
        ranges = {int(v): (lo, hi) for v, lo, hi in VOL_RANGE.findall(window)}
        out["volume_ranges"] = [
            {"volume": v, "from": lo, "to": hi} for v, (lo, hi) in sorted(ranges.items())]
        if out["declared_volumes"] >= 2 and not epub_complete:
            # VERDICT: a framed epubFrame capture holds exactly ONE spine document, so a
            # self-declared multi-volume compilation without the complete epub-extraction
            # markers is volume 1 only. (Confirmed empirically: every declared-later
            # volume with a parseable section range had those sections absent.)
            out["truncated"] = True
            have = set(present)
            for v in range(2, out["declared_volumes"] + 1):
                lo = ranges.get(v, (None, None))[0]
                evidenced = (lo is not None and
                             (lo in have or any(_sect_key(s) >= _sect_key(lo) for s in have)))
                if not evidenced:
                    out["missing_volumes"].append(v)
            if not out["missing_volumes"]:
                # Section-number evidence is unreliable for this act (dashed numbering
                # like the GST Act's "114-1"); a one-spine-document capture still cannot
                # contain the later volumes — report them all missing.
                out["missing_volumes"] = list(range(2, out["declared_volumes"] + 1))
    # Secondary signal: last TOC entry should appear in the body text (advisory only;
    # normalize dash spacing — TOCs print "Schedule 1—X", bodies "Schedule 1 — X").
    def _norm(s: str) -> str:
        return re.sub(r"\s*([—–‑-])\s*", r"\1", s.lower())

    tocs = [_plain(t) for t in TOC_ENTRY.findall(text)]
    tocs = [t for t in tocs if t]
    if tocs:
        last = tocs[-1]
        out["last_toc_entry"] = last[:80]
        out["last_toc_in_body"] = _norm(last[:60]) in _norm(_plain(text))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--handoff", default="handoff1_v2")
    ap.add_argument("--report", default="docs/AU_HTML_TRUNCATION_AUDIT_2026-07-17.md")
    ap.add_argument("--json", dest="json_out", default=None)
    args = ap.parse_args()

    handoff = Path(args.handoff)
    rows = []
    with open(handoff / "manifest.jsonl", encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if (r.get("economy") == "AU" and r.get("source_type") == "html"
                    and "legislation.gov.au" in (r.get("source_url") or "")):
                rows.append(r)

    results = []
    for r in rows:
        p = handoff / r["local_path"]
        text = p.read_text(encoding="utf-8", errors="replace")
        res = audit_document(text)
        res["doc_id"] = r["doc_id"]
        res["law_name"] = r["law_name_guess"]
        res["superseded_by"] = None
        results.append(res)

    # A truncated row no longer counts against the corpus once a later row supersedes it.
    by_id = {r["doc_id"]: r for r in results}
    with open(handoff / "manifest.jsonl", encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            m = re.search(r"supersedes\s+(\S+)", row.get("crawl_notes") or "")
            if m and m.group(1) in by_id:
                by_id[m.group(1)]["superseded_by"] = row["doc_id"]

    truncated = [r for r in results if r["truncated"] and not r["superseded_by"]]
    superseded = [r for r in results if r["truncated"] and r["superseded_by"]]
    toc_flags = [r for r in results if not r["truncated"]
                 and r.get("last_toc_in_body") is False]

    lines = [
        "# AU HTML truncation audit",
        "",
        f"Scope: all {len(results)} AU `source_type=html` documents fetched from "
        "legislation.gov.au in `" + str(handoff) + "/`.",
        "",
        "Method: a multi-volume compilation self-declares its volume map in its own "
        "front matter (“This compilation is in N volumes … Volume k: sections X‑Y”). "
        "The epubFrame viewer renders exactly ONE epub spine document (= one volume), "
        "so a document is **truncated** when it declares ≥2 volumes and does not carry "
        "the fixed epub lane's complete `p1-epub-spine-doc i/n` extraction-marker set. "
        "Covered/expected section ranges (`CharSectno` markers vs the declared map) are "
        "shown as evidence; they are not the verdict — several acts define later "
        "volumes by Schedule/Chapter or dotted numbering, which section ranges cannot "
        "adjudicate. Per-volume TOCs cannot detect the defect at all (each volume "
        "carries only its own contents), which is why it was invisible to a TOC-vs-body "
        "check. Secondary advisory check: last TOC entry present in body text "
        "(dash-spacing normalized).",
        "",
        f"## Verdict: {len(truncated)} truncated document(s) remaining "
        f"({len(superseded)} truncated but superseded by a complete re-fetch)",
        "",
    ]
    if truncated:
        lines += [
            "| doc_id | law | declared volumes | covered (present sections) | expected (declared) | missing volumes |",
            "|---|---|---|---|---|---|",
        ]
        for r in sorted(truncated, key=lambda x: x["doc_id"]):
            exp = "; ".join(f"v{v['volume']}: {v['from']}–{v['to']}"
                            for v in r["volume_ranges"]) or "(volume map unparseable)"
            lines.append(
                f"| {r['doc_id']} | {r['law_name'][:48]} | {r['declared_volumes']} "
                f"| ss.{r['first_section']}–{r['last_section']} | {exp} "
                f"| {', '.join(map(str, r['missing_volumes']))} |")
        lines.append("")
    if superseded:
        lines += ["## Truncated rows already superseded (kept for provenance)", "",
                  "| truncated doc_id | superseded by | last section in truncated copy |",
                  "|---|---|---|"]
        for r in sorted(superseded, key=lambda x: x["doc_id"]):
            lines.append(f"| {r['doc_id']} | {r['superseded_by']} | {r['last_section']} |")
        lines.append("")
    lines += [f"## Secondary TOC check: {len(toc_flags)} flag(s) among non-truncated docs", ""]
    if toc_flags:
        lines += ["| doc_id | law | last TOC entry (not matched verbatim in body) |", "|---|---|---|"]
        for r in sorted(toc_flags, key=lambda x: x["doc_id"]):
            lines.append(f"| {r['doc_id']} | {r['law_name'][:48]} | {r.get('last_toc_entry','')} |")
        lines += ["", "TOC flags are advisory (formatting differences can defeat verbatim "
                  "matching); the volume-map check above is the authoritative signal.", ""]

    Path(args.report).write_text("\n".join(lines), encoding="utf-8")
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"[audit] {len(results)} AU html docs; truncated (unsuperseded): {len(truncated)}; "
          f"superseded: {len(superseded)}; report -> {args.report}")
    for r in truncated:
        print(f"  TRUNCATED {r['doc_id']}  last={r['last_section']}  "
              f"missing vols {r['missing_volumes']}  {r['law_name'][:60]}")
    return 2 if truncated else 0


if __name__ == "__main__":
    sys.exit(main())
