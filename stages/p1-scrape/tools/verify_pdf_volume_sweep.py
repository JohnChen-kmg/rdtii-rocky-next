"""Verification delta, PDF side (2026-07-18):
B. First-3-pages scan of EVERY PDF in the corpus (AU/SG/MY) for multi-volume/multi-part
   declarations — closes the "PDF lane unaffected" claim with evidence.
C. Deep whole-text check of the 3 largest docs per SG/MY (any form).
"""
import json, re
from pathlib import Path
import pypdfium2 as pdfium

H = Path("handoff1_v2")
rows = [json.loads(l) for l in open(H / "manifest.jsonl", encoding="utf-8")]

WORDS = "two|three|four|five|six|seven|eight|nine|ten|eleven|twelve"
PAT = re.compile(
    r"(compilation\s+is\s+in\s+(?:\d+|" + WORDS + r")\s+volumes?"
    r"|volume\s+\d+\s+of\s+\d+"
    r"|jilid\s+\d+"                      # Malay: volume
    r"|part\s+\d+\s+of\s+\d+\s+parts)", re.I)

def pdf_head_text(path, npages=3):
    try:
        doc = pdfium.PdfDocument(str(path))
    except Exception as e:
        return f"<unreadable: {e}>"
    try:
        out = []
        for i in range(min(npages, len(doc))):
            try:
                out.append(doc[i].get_textpage().get_text_range())
            except Exception:
                pass
        return "\n".join(out)
    finally:
        doc.close()

# ---------- B. all PDFs, first 3 pages ----------
hits, unreadable, scanned_empty = [], [], 0
pdf_rows = [r for r in rows if r["source_type"].startswith("pdf")]
print(f"B) scanning {len(pdf_rows)} PDFs (first 3 pages each)...", flush=True)
for i, r in enumerate(pdf_rows):
    if i and i % 400 == 0:
        print(f"   ...{i}/{len(pdf_rows)}", flush=True)
    t = pdf_head_text(H / r["local_path"])
    if t.startswith("<unreadable"):
        unreadable.append(r["doc_id"])
        continue
    if not t.strip():
        scanned_empty += 1        # image scans yield no text — expected for pdf_scanned
        continue
    m = PAT.search(t)
    if m:
        hits.append((r["doc_id"], r["economy"], m.group(0)[:60], r["law_name_guess"][:50]))
print(f"B) DONE. multi-volume/part declarations in PDF front matter: {len(hits)}")
for h in hits:
    print("   HIT", h)
print(f"B) unreadable: {unreadable or 'NONE'}; textless (image scans): {scanned_empty}")

# ---------- C. 3 largest docs per SG/MY, whole text ----------
print()
for cc in ("SG", "MY"):
    big = sorted((r for r in rows if r["economy"] == cc),
                 key=lambda r: -r["byte_size"])[:3]
    for r in big:
        p = H / r["local_path"]
        if r["source_type"].startswith("pdf"):
            doc = pdfium.PdfDocument(str(p))
            t = "\n".join(doc[i].get_textpage().get_text_range() for i in range(len(doc)))
            doc.close()
        else:
            t = p.read_text(encoding="utf-8", errors="replace")
        m = PAT.search(t)
        # also look for any 'Volume 2'/'Jilid 2' style continuation cue
        m2 = re.search(r"(volume|jilid)\s*(2|II)\b", t, re.I)
        print(f"C) {cc} {r['doc_id']} ({r['byte_size']/1e6:.1f} MB, "
              f"{r['source_type']}) {r['law_name_guess'][:45]!r}: "
              f"decl={'HIT: '+m.group(0)[:40] if m else 'none'}; "
              f"vol2-cue={'HIT: '+m2.group(0) if m2 else 'none'}")
print()
print("PDF-SIDE VERDICT:", "CLEAN" if not hits else "HITS FOUND — investigate above")
