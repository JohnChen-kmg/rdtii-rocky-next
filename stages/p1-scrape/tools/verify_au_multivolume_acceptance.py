"""Verification delta, HTML side (2026-07-18):
A. Wider multi-volume detector (digits OR word numbers) over ALL AU html docs — union vs the 33.
D. Per-act acceptance on the 33 complete -002 docs.
E. Hand-off note completeness (all 33 ids listed).
"""
import json, re, sys
from pathlib import Path

H = Path("handoff1_v2")
rows = {}
for line in open(H / "manifest.jsonl", encoding="utf-8"):
    r = json.loads(line)
    rows[r["doc_id"]] = r

WORDS = ("two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|"
         "fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty")
DECL_WIDE = re.compile(r"compilation\s+is\s+in\s+(\d+|" + WORDS + r")\s+volumes?", re.I)
W2N = {w: i for i, w in enumerate(WORDS.split("|"), start=2)}
SECTNO = re.compile(r'class="CharSectno"[^>]*>\s*([0-9]+[A-Z]*)\s*<')
MARK = re.compile(r"p1-epub-spine-doc (\d+)/(\d+)")

def sect_key(s):
    m = re.match(r"([0-9]+)([A-Z]*)", s)
    return (int(m.group(1)), m.group(2)) if m else (0, s)

def plain(s):
    s = re.sub(r"<[^>]+>", " ", s)
    s = s.replace("&nbsp;", " ").replace("&#xa0;", " ").replace("&#x2011;", "-")
    return re.sub(r"\s+", " ", s)

# ---------- A. wider detector over ALL AU html ----------
superseded = set()
for r in rows.values():
    m = re.search(r"superseded by\s+(\S+)", r.get("crawl_notes") or "")
    if m:
        pass
for r in rows.values():
    m = re.search(r"supersedes\s+(\S+)", r.get("crawl_notes") or "")
    if m:
        superseded.add(m.group(1))

flagged = []            # docs declaring >1 volumes WITHOUT complete spine markers, not superseded
word_form_hits = []     # any doc using the word form at all
declared_all = {}       # doc_id -> declared N (max across matches)
for d, r in sorted(rows.items()):
    if not (r["economy"] == "AU" and r["source_type"] == "html"):
        continue
    t = (H / r["local_path"]).read_text(encoding="utf-8", errors="replace")
    ns = []
    for m in DECL_WIDE.finditer(t):
        v = m.group(1).lower()
        ns.append(int(v) if v.isdigit() else W2N[v])
        if not v.isdigit():
            word_form_hits.append((d, v))
    if not ns:
        continue
    n = max(ns)
    declared_all[d] = n
    marks = {int(a) for a, _ in MARK.findall(t)}
    spine_n = max((int(b) for _, b in MARK.findall(t)), default=0)
    complete = spine_n > 0 and marks == set(range(1, spine_n + 1))
    if n > 1 and not complete and d not in superseded:
        flagged.append((d, n))

old33 = sorted(d for d in superseded if d.startswith("au-"))
print("A) wider-detector declarations found in", len(declared_all), "AU html docs")
print("A) word-form ('in two volumes' etc.) hits:", word_form_hits or "NONE — digits only on FRL")
print("A) docs declaring >1 vols, NOT complete, NOT superseded:", flagged or "NONE")
print("A) superseded truncated set size (should be 33):", len(old33))

# ---------- D. acceptance on the 33 -002 docs ----------
PROBES = {
    "au-ta1979-002": ["187A", "187N"],       # Part 5-1A span ends at 187N
    "au-cca2010-002": ["56AA"],              # CDR Part IVD
    "au-itaa1936-002": ["262A"],             # record-keeping
}
fails = []
print()
print("D) acceptance per act (33 complete -002 docs):")
pairs = {}
for old in old33:
    new = old[:-4] + "-002"
    pairs[old] = new
    r = rows.get(new)
    if not r:
        fails.append((new, "row missing")); continue
    t = (H / r["local_path"]).read_text(encoding="utf-8", errors="replace")
    marks = MARK.findall(t)
    spine_n = max((int(b) for _, b in marks), default=0)
    got = {int(a) for a, _ in marks}
    spine_ok = spine_n > 0 and got == set(range(1, spine_n + 1))
    decl = declared_all.get(new, 0)
    decl_ok = (decl == spine_n)
    # final volume text = after the last spine marker
    last_pos = max(m.end() for m in MARK.finditer(t))
    final_txt = t[last_pos:]
    endnote_ok = bool(re.search(r"Endnote", final_txt))
    # max section vs declared final end (digits only; schedule-based maps skipped)
    sects = SECTNO.findall(t)
    max_sect = max(sects, key=sect_key) if sects else None
    p = plain(t[:40000])
    vol_ends = re.findall(r"Volume\s+\d+\s*:?\s*sections?\s+[0-9]+[A-Z]*\s*(?:to|[-‐‑–—])\s*([0-9]+[A-Z]*)", p, re.I)
    span_ok, span_note = True, "schedule/dotted map — spine+Endnote govern"
    if vol_ends:
        final_end = vol_ends[-1]
        span_ok = max_sect is not None and sect_key(max_sect) >= sect_key(final_end)
        span_note = f"max s.{max_sect} >= declared end s.{final_end}"
    probe_missing = [x for x in PROBES.get(new, []) if x not in t]
    ok = spine_ok and decl_ok and endnote_ok and span_ok and not probe_missing
    status = "OK " if ok else "FAIL"
    print(f"  {status} {new}: spine {spine_n}/{spine_n if spine_ok else '??'} "
          f"decl={decl} endnote={endnote_ok} {span_note}"
          + (f" PROBE-MISSING={probe_missing}" if probe_missing else ""))
    if not ok:
        fails.append((new, f"spine_ok={spine_ok} decl_ok={decl_ok} "
                           f"endnote={endnote_ok} span_ok={span_ok} probes={probe_missing}"))

# provenance census
log_refetch = 0
for line in open(H / "crawl_log.jsonl", encoding="utf-8"):
    if "multi-volume re-fetch" in line:
        log_refetch += 1
sidecars_missing = [new for new in pairs.values()
                    if new in rows and not (H / rows[new]["http_headers_path"]).exists()]
print(f"D) crawl_log re-fetch entries: {log_refetch} (expect 34 = 33 + 1 disclosed dup)")
print(f"D) sidecars missing: {sidecars_missing or 'NONE'}")

# ---------- E. hand-off note completeness ----------
note = Path("docs/HANDOFF_AU_MULTIVOLUME_2026-07-17.md").read_text(encoding="utf-8")
missing_in_note = [x for pair in pairs.items() for x in pair if x not in note]
print()
print("E) hand-off note lists all 66 ids (33 old + 33 new):",
      "YES" if not missing_in_note else f"MISSING {missing_in_note}")

print()
print("VERDICT:", "ALL PASS" if not fails and not flagged and not sidecars_missing
      and not missing_in_note else f"FAILURES: {fails or ''} {flagged or ''}")
sys.exit(0 if not fails and not flagged else 1)
