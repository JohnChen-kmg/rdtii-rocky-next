# AU HTML truncation audit

Scope: all 432 AU `source_type=html` documents fetched from legislation.gov.au in `handoff1_v2/`.

Method: a multi-volume compilation self-declares its volume map in its own front matter (“This compilation is in N volumes … Volume k: sections X‑Y”). The epubFrame viewer renders exactly ONE epub spine document (= one volume), so a document is **truncated** when it declares ≥2 volumes and does not carry the fixed epub lane's complete `p1-epub-spine-doc i/n` extraction-marker set. Covered/expected section ranges (`CharSectno` markers vs the declared map) are shown as evidence; they are not the verdict — several acts define later volumes by Schedule/Chapter or dotted numbering, which section ranges cannot adjudicate. Per-volume TOCs cannot detect the defect at all (each volume carries only its own contents), which is why it was invisible to a TOC-vs-body check. Secondary advisory check: last TOC entry present in body text (dash-spacing normalized).

## Verdict: 0 truncated document(s) remaining (33 truncated but superseded by a complete re-fetch)

## Truncated rows already superseded (kept for provenance)

| truncated doc_id | superseded by | last section in truncated copy |
|---|---|---|
| au-asica2001-001 | au-asica2001-002 | 93H |
| au-ba2015-001 | au-ba2015-002 | 403 |
| au-bsa1992c8a4-001 | au-bsa1992c8a4-002 | 218 |
| au-ca1901-001 | au-ca1901-002 | 126C |
| au-ca1914-001 | au-ca1914-002 | 15F |
| au-ca2001-001 | au-ca2001-002 | 260E |
| au-cca1995-001 | au-cca1995-002 | 5 |
| au-cca2010-001 | au-cca2010-002 | 53ZZC |
| au-cea1918-001 | au-cea1918-002 | 286 |
| au-cta1995-001 | au-cta1995-002 | 22 |
| au-epbca1999-001 | au-epbca1999-002 | 266 |
| au-fbtaa1986-001 | au-fbtaa1986-002 | 78A |
| au-fla1975-001 | au-fla1975-002 | 90 |
| au-fwa2009936e-001 | au-fwa2009936e-002 | 257 |
| au-hia1973-001 | au-hia1973-002 | 106ZR |
| au-itaa1936-001 | au-itaa1936-002 | 78A |
| au-itaa1997-001 | au-itaa1997-002 | 320 |
| au-ma1958-001 | au-ma1958-002 | 261K |
| au-nccpa2009f78b-001 | au-nccpa2009f78b-002 | 322 |
| au-ntsa199954b8-001 | au-ntsa199954b8-002 | 152D |
| au-ntsa199978da-001 | au-ntsa199978da-002 | 610 |
| au-opggsa2006-001 | au-opggsa2006-002 | 286C |
| au-sa1976-001 | au-sa1976-002 | 110S |
| au-sia1993-001 | au-sia1993-002 | 127 |
| au-ssa1991-001 | au-ssa1991-002 | 514F |
| au-ssa1999-001 | au-ssa1999-002 | 25 |
| au-ssa1999dcb5-001 | au-ssa1999dcb5-002 | 123ZO |
| au-ta1979-001 | au-ta1979-002 | 186J |
| au-ta1997-001 | au-ta1997-002 | 310 |
| au-taa1953-001 | au-taa1953-002 | 460 |
| au-tga1989-001 | au-tga1989-002 | 41AG |
| au-vea1986-001 | au-vea1986-002 | 45UY |
| au-wa2007-001 | au-wa2007-002 | 239W |

## Secondary TOC check: 0 flag(s) among non-truncated docs

---

## Verification delta (2026-07-18) — independent re-derivation + acceptance sweep

Run after the fix shipped, per the follow-up audit brief; every check below is
scripted and re-runnable.

1. **List re-derivation, wider detector (union rule):** re-swept ALL AU html docs with
   digit AND word-number forms ("compilation is in two/three/… volumes"). FRL uses
   digits only; the union added **nothing** — the 33 is the exhaustive set. No document
   declaring >1 volumes exists that is not complete-or-superseded.
2. **PDF lane (evidence, was assumption):** first-3-pages text scan of **all 2,271
   corpus PDFs** (AU/SG/MY) for volume/part/jilid declarations → **0 hits**
   (40 textless image scans are the known OCR workload; 0 unreadable).
3. **SG/MY negative:** whole-text check of the 3 largest docs per economy (incl. the
   90.4 MB and 57.3 MB MY scans) → no multi-volume declarations, no "Volume 2"/"Jilid 2"
   continuation cues. SSO and LOM serve one document per law.
4. **Per-act acceptance (33/33 PASS):** for every `-002` doc — complete
   `p1-epub-spine-doc i/n` marker set; **declared volume count == spine document count**
   (e.g. ITAA 1997: 12/12); "Endnote" present in the FINAL volume's text; max section id
   ≥ the About-page's declared final span wherever the volume map is section-numbered
   (schedule/dotted-numbered maps are governed by the spine + Endnote checks). Named
   casualties verified present: TIA 1979 **ss.187A–187N** (Part 5-1A), CCA 2010
   **s.56AA+** (Consumer Data Right, Part IVD), ITAA 1936 **s.262A** (record-keeping).
5. **Provenance census:** 34 crawl_log re-fetch entries (33 acts + 1 disclosed
   byte-identical duplicate), a `.headers.json` sidecar for every new artifact, and the
   P2/P3 hand-off note lists **all 66** doc_ids (33 superseded + 33 new) — verified
   programmatically.

**Storage-shape note for readers of the 2026-07-18 brief:** missing volumes were NOT
stored as separate per-volume rows. Each `-002` doc is the **complete act — every
volume concatenated in spine order** (boundaries preserved as `p1-epub-spine-doc`
comments), superseding its `-001`. One act = one row = one file; P2 re-extracts the 33
`-002` ids additively and retires the `-001` extractions.
