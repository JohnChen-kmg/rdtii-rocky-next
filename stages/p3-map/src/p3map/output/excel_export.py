"""Excel export — human-browsable workbook per economy in out/results/.

Sheets: Summary (run stats + per-indicator counts), Fires (every fired verdict
with quote/rationale/verification), Overturned (panel-rejected fires),
NotInForce (trap-flagged provisions), Ungrounded (quote-check failures),
Errors (provisions whose verdict never parsed, so nothing was decided).

Every sheet that shows a non-English provision shows the machine English beside it, from
audit/gloss_*.jsonl. Read-only and optional -- a missing gloss leaves the column blank. The
English column sits immediately right of the exact text it translates; "Full section text" is a
wider, separate extract and carries no translation claim.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

import pandas as pd
import yaml

from config.instrument import from_artifact, load as load_instrument
from config.settings import SETTINGS

_ILLEGAL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
_YEAR = re.compile(r"\b(1[89]\d{2}|20[0-2]\d)\b")

# Column order of a fire row -- used ONLY to shape an empty workbook (see run()).
FIRE_COLUMNS = ["Indicator", "Law", "Section", "Source URL", "Enacted", "Last amended",
                "Crawled", "Score hint", "Coverage", "Confidence", "Quote grounded",
                "Verification", "Final applies", "Verbatim quote", "English (machine)",
                "Provision text", "Provision text (English, machine)", "Full section text",
                "Rationale", "Verifier reason", "Provision ID"]
NIF_COLUMNS = ["provision_id", "law", "section", "core_answer",
               "Provision text", "Provision text (English, machine)", "Full section text"]
# The provisions whose verdict failed schema validation. Until now they existed only as a count on
# the Summary sheet, so a reviewer could see that 176 provisions failed and never see which ones.
ERR_COLUMNS = ["provision_id", "law", "section", "error",
               "Provision text", "Provision text (English, machine)", "Full section text"]

# how each indicator was actually mapped — shown in the sheet banner
_MECHANISM = {
    "6.1": {"how": "ban/local-processing keyword net + embeddings; Sonnet verdict, blind-verified",
              "traps": "'conditional_path_exists' guards the #1 error — a transfer WITH conditions is 6.4, not a ban"},
    "6.2": {"how": "local-storage-copy signature net + embeddings; Sonnet verdict, blind-verified",
              "traps": "sectoral storage rules score 0.5-class coverage; government-data rules excluded"},
    "6.3": {"how": "domestic-infrastructure net (rare wording — the dense/embedding leg carries this indicator)",
              "traps": "licensing and operational data-centre rules are excluded by the scoring tree"},
    "6.4": {"how": "conditional-flow net (consent / adequacy / contract / TIA terms); Sonnet answers the core legal question first, blind-verified",
              "traps": "'conditional_path_exists' separates it from 6.1; personal-data conditions score 1 even if sectoral"},
    "7.1": {"how": "framework-existence evidence collected per provision; the economy-level answer comes from a dedicated rollup — only the controlling scope provision reaches the CSV",
              "traps": "INVERTED POLARITY: 1 = NO data-protection framework, so evidence rows carry score 0"},
    "7.2": {"how": "same two-level design as 7.1 (evidence rows -> economy rollup)",
              "traps": "INVERTED POLARITY: 1 = NO cybersecurity framework; sectoral instruments (MAS/APRA/CII) are 0.5-class evidence, binding-status checked per instrument"},
    "7.3": {"how": "retention-period net + embeddings; Sonnet verdict, blind-verified",
              "traps": "'retention_is_minimum': only 'at least X' rules count — maximum / 'no longer than necessary' / destroy-after rules are rejected (the classic baseline error)"},
    "7.4": {"how": "DPO/DPIA net (lexically distinctive); Sonnet verdict, blind-verified",
              "traps": "DPO duty -> 1, DPIA-only -> 0.25-flag; guidance-only instruments recorded but never controlling"},
    "7.5": {"how": "government-access net (production orders, decryption, technical assistance); Sonnet verdict, blind-verified",
              "traps": "warrantless / undefined-authority access pushes toward 1; regulator incident-reporting is NOT government access"},
}


# How a section begins, per legal tradition. The English forms were written when the run was
# Singapore, Malaysia and Australia; the migration to six economies never reached them, so for
# Chinese, Lao and Portuguese _full_section found no heading at all and silently fell back to a
# window starting 6,000 characters before the provision -- which, near the top of a short
# instrument, is the document's first article. Measured against the source text on 29 September:
# the Chinese form matches 49 of 60 sampled documents, Portuguese 31 of 60, Lao 38 of 60, and the
# misses are documents with no article structure (an NPC "decision" is continuous prose) or OCR so
# damaged the script did not survive -- not pattern failures.
_HEADING_FORMS = {
    # 26.—(1) / 22A.(1) / PART IV / Division 3 / Schedule
    "": r"\d{1,4}[A-Z]{0,3}\.(?:—|–|-|\s*\()|PART\s+[0-9IVXL]+|Division\s+\d+|Schedule\b",
    # 第九条 / 第 9 条, and the coarser 第三章
    "CN": r"第\s*[0-9一二三四五六七八九十百千零]+\s*[条章]",
    # Artigo 15 / Artigo 15.º / Art. 21, and the coarser divisions a gazette uses
    "TL": (r"(?:Artigo|Art\.)\s*\d+"
           r"|CAP[ÍI]TULO\s+[0-9IVXLA-Z]+|SEC[ÇC][ÃA]O\s+[0-9IVXLA-Z]+"
           r"|T[ÍI]TULO\s+[0-9IVXLA-Z]+"),
    # ມາດຕາ 44 (Article). ພາກ (Part) is left out: OCR mangles it often enough to split mid-article.
    "LA": r"ມາດຕາ\s*\d+",
}


def _section_re(economy: str) -> "re.Pattern[str]":
    """The economy's own heading forms, unioned with the English ones.

    Unioned rather than switched: a corpus is not monolingual -- Timorese instruments carry English
    headings in translated annexes, and an economy we have no form for still gets the English
    behaviour instead of nothing.
    """
    extra = _HEADING_FORMS.get(economy.upper(), "")
    alts = _HEADING_FORMS[""] + ("|" + extra if extra else "")
    return re.compile(r"^\s*(?:" + alts + ")", re.MULTILINE)


def section_bounds(text: str, s: int, e: int, sec_re, back: int = 6000,
                   fwd: int = 8000) -> tuple[int, int]:
    """Widen the byte span (s, e) outward to the section that contains it.

    Walks back to the nearest heading at or before `s` and forward to the next one after `e`.

    The subtle part is "at or before". The obvious spelling, `sec_re.finditer(text, lo, s + 1)`,
    requires a heading beginning exactly AT s to fit inside the window, so a three-character 第九条
    at s never matched and the walk-back landed on 第八条 -- one article early, every time. Measured
    29 September 2026: `snippet_char_start` lands exactly on the heading in 397 of 400 sampled
    Chinese provisions, so that was the common case rather than a corner. Scanning past s and
    keeping the last match that starts at or before it is what makes the extract begin at the
    labelled article: verified at 514/516 for China, 188/188 for Lao PDR, 310/316 for Timor-Leste.
    """
    lo = max(0, s - back)
    start = lo
    for m in sec_re.finditer(text, lo):
        if m.start() > s:
            break
        start = m.start()
    hi = min(len(text), e + fwd)
    nxt = sec_re.search(text, e)
    end = nxt.start() if nxt and nxt.start() < hi else hi
    # no heading behind us at all: at least snap to a line start rather than mid-word
    if start == lo and lo > 0:
        nl = text.rfind("\n", lo, s)
        start = nl + 1 if nl != -1 else lo
    return start, max(end, start)


def _indicator_banner(ind: str) -> str:
    try:
        # Through the loader: it resolves the signature filename for either instrument
        # vintage, so the banner survives the hand-off instead of falling back to a bare ID.
        sig = load_instrument().signature(ind)
        name = sig.get("name", ind)
        definition = (sig.get("definition_text") or "").split(". ")[0].strip()
    except Exception:
        name, definition = ind, ""
    m = _MECHANISM.get(ind, {})
    return "\n".join([
        f"• {ind} — {name}",
        f"• What it measures: {definition}.",
        f"• How it was mapped: {m.get('how', '')}.",
        f"• Traps / scoring rules applied: {m.get('traps', '')}.",
    ])


def _clean(s, cap: int = 8000):  # noqa: ANN001
    if s is None:
        return ""
    return _ILLEGAL.sub("", str(s))[:cap]


def _style_workbook(path) -> None:  # noqa: ANN001
    """Readable styling: Segoe UI, bold banded header, wrapped long columns,
    sensible widths, frozen header row."""
    from openpyxl import load_workbook
    from openpyxl.styles import Alignment, Font, PatternFill

    widths = {"Indicator": 8, "Law": 28, "Section": 10, "Source URL": 24,
              "Last amended": 14, "Crawled": 11, "Score hint": 8,
              "Coverage": 10, "Confidence": 9, "Quote grounded": 8,
              "Verification": 14, "Final applies": 8, "Verbatim quote": 36,
              "English (machine)": 36, "Provision text": 40,
              "Provision text (English, machine)": 40, "Full section text": 40,
              "Rationale": 28, "Verifier reason": 28,
              "Provision ID": 24, "core_answer": 30,
              "provision_id": 24, "law": 28, "section": 10, "error": 40}
    wb = load_workbook(path)
    for ws in wb.worksheets:
        # all sheets carry a banner in row 1 (bulleted, wrapped); header is row 2
        hrow = 2 if (ws["A1"].value and str(ws["A1"].value).lstrip().startswith("•")) else 1
        if hrow == 2:
            ncols = ws.max_column
            ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=ncols)
            b = ws.cell(row=1, column=1)
            b.font = Font(name="Segoe UI", size=10, italic=True, color="1F3864")
            b.fill = PatternFill("solid", fgColor="DEEAF6")
            b.alignment = Alignment(vertical="top", wrap_text=True)
            ws.row_dimensions[1].height = 88
        header_cells = ws[hrow]
        for c in header_cells:
            c.font = Font(name="Segoe UI", size=10, bold=True, color="FFFFFF")
            c.fill = PatternFill("solid", fgColor="2F5496")
            c.alignment = Alignment(vertical="top")
        headers = {c.value: c.column_letter for c in header_cells if c.value}
        for name, letter in headers.items():
            ws.column_dimensions[letter].width = widths.get(name, 14)
        for row in ws.iter_rows(min_row=hrow + 1):
            for c in row:
                c.font = Font(name="Segoe UI", size=10)
                c.alignment = Alignment(vertical="top", wrap_text=False)
        ws.freeze_panes = f"A{hrow + 1}"
    wb.save(path)


def export(economy: str = "SG", extra_dirs=()) -> None:      # noqa: ANN001
    """One workbook per economy.

    `extra_dirs` names further run directories to fold in, for an economy mapped in more than one
    arm. Timor-Leste is that case: pillars 6 and 7 in `out/` and the other 52 indicators in
    `out_tl52/`, which gave it two workbooks and two records files while every other economy had
    one. A reviewer should open one workbook per country, so the arms are unioned here rather than
    left for a human to reconcile -- and the submission needs one file per economy anyway.

    Only the per-arm files are unioned (verdicts, verify, the glosses). The corpus and handoff2 are
    shared, and the workbook is written to the PRIMARY out_dir.
    """
    out_dir = SETTINGS.out_dir / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    arms = [SETTINGS.out_dir, *(Path(d) for d in extra_dirs)]

    # Full original text per provision, paragraph-aligned: use the byte offsets
    # into source_text and snap outward to blank-line boundaries so the extract
    # starts at the top of the section/paragraph, not mid-sentence.
    offsets: dict[str, tuple[str, int, int]] = {}
    prov_meta: dict[str, dict] = {}
    with (SETTINGS.handoff2_dir / "provisions.jsonl").open(encoding="utf-8") as f:
        for line in f:
            if f'"economy": "{economy}"' not in line and f'"economy":"{economy}"' not in line:
                continue
            r = json.loads(line)
            s, e = r.get("snippet_char_start"), r.get("snippet_char_end")
            if isinstance(s, int) and isinstance(e, int):
                offsets[r["provision_id"]] = (r["doc_id"], s, e)
            prov_meta[r["provision_id"]] = {
                "url": r.get("source_url") or "",
                "last_amended": r.get("last_amended") or "",
                "crawled": r.get("access_date") or "",
                # an error row's verdict never parsed, so its law and section come from here
                "law_name": r.get("law_name") or "",
                "article_section": r.get("article_section") or "",
            }

    # The text the glosser read, keyed by provision. This is the corpus row the whole pipeline
    # judged -- law name, section, page and the provision itself -- and it is what
    # gloss_sections_<ECON>.jsonl translated. It sits immediately left of its English so the two
    # columns are the same bytes in two languages. "Full section text" beside them is a WIDER,
    # separate extract from the source document (see _full_section), and nothing claims to
    # translate it.
    prov_text: dict[str, str] = {}
    _corpus = SETTINGS.index_dir / "prefilter_corpus.jsonl"
    if _corpus.exists():
        with _corpus.open(encoding="utf-8") as f:
            for line in f:
                if f'"economy": "{economy}"' not in line and f'"economy":"{economy}"' not in line:
                    continue
                r = json.loads(line)
                prov_text[r["provision_id"]] = r.get("text") or ""

    _doc_cache: dict[str, str] = {}

    def _full_section(pid: str) -> str:
        if pid not in offsets:
            return ""
        doc_id, s, e = offsets[pid]
        if doc_id not in _doc_cache:
            p = SETTINGS.handoff2_dir / "source_text" / f"{doc_id}.txt"
            # a few docs hot, not one: fire, not-in-force and error rows are interleaved in the
            # verdicts file, and a single-slot cache re-reads the same document between them
            if len(_doc_cache) >= 4:
                _doc_cache.clear()
            _doc_cache[doc_id] = (
                p.read_text(encoding="utf-8", errors="replace") if p.exists() else "")
        text = _doc_cache[doc_id]
        if not text:
            return ""
        start, end = section_bounds(text, s, e, _section_re(economy))
        return text[start:end].strip()

    verify = {}
    for arm in arms:
        vpath = arm / "verify" / f"verified_{economy}.jsonl"
        if not vpath.exists():
            continue
        with vpath.open(encoding="utf-8") as f:
            for line in f:
                r = json.loads(line)
                verify[(r["provision_id"], from_artifact(r["indicator"]))] = r

    # English glosses of non-English quotes, produced by output/gloss.py into audit/.
    # Read-only and optional: the workbook is a review surface, so a missing gloss file leaves the
    # column blank rather than failing the export. The gloss NEVER travels to the submission -- it
    # is not in the CSV's column set and output/submission.py does not open this file.
    gloss = {}
    for arm in arms:
        gpath = arm / "audit" / f"gloss_{economy}.jsonl"
        if gpath.exists():
            for line in gpath.open(encoding="utf-8"):
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    continue
                txt = str(r.get("english") or "").strip()
                if txt and not r.get("is_literal", True):
                    txt = "[not literal — source text is garbled] " + txt
                gloss[(r["provision_id"], from_artifact(r["indicator"]))] = txt

    # the whole provision, glossed once per provision rather than per indicator
    gloss_sec = {}
    for arm in arms:
        gspath = arm / "audit" / f"gloss_sections_{economy}.jsonl"
        if gspath.exists():
            for line in gspath.open(encoding="utf-8"):
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    continue
                txt = str(r.get("english") or "").strip()
                if txt and not r.get("is_literal", True):
                    txt = "[not literal — source text is garbled] " + txt
                gloss_sec[r["provision_id"]] = txt

    fires, not_in_force, errored = [], [], []
    n_prov = n_err = 0
    # A provision can be judged in BOTH arms -- the two cover different indicators, but the same
    # article can be a candidate for one of pillar 6's and one of pillar 3's. Fires are per
    # (provision x indicator) and all of them belong in the workbook; the provision-LEVEL surfaces
    # must not double-count, so they are keyed on the provision.
    seen_prov: set[str] = set()
    seen_nif: set[str] = set()
    seen_err: set[str] = set()
    for arm in arms:
        _vp = arm / "map" / f"verdicts_{economy}.jsonl"
        if not _vp.exists():
            continue
        for line in _vp.open(encoding="utf-8"):
            row = json.loads(line)
            if "error" in row:
                pid = row.get("provision_id") or ""
                if pid in seen_err:
                    continue
                seen_err.add(pid)
                n_err += 1
                pm = prov_meta.get(pid, {})
                errored.append({
                    "provision_id": pid,
                    "law": _clean(pm.get("law_name"), 200),
                    "section": _clean(pm.get("article_section"), 60),
                    "error": _clean(row.get("error"), 600),
                    "Provision text": _clean(prov_text.get(pid, ""), 12000),
                    "Provision text (English, machine)": _clean(gloss_sec.get(pid, ""), 12000),
                    "Full section text": _clean(_full_section(pid), 12000),
                })
                continue
            if row["provision_id"] not in seen_prov:
                seen_prov.add(row["provision_id"])
                n_prov += 1
            if (not row["trap_checks"].get("provision_in_force", True)
                    and row["provision_id"] not in seen_nif):
                seen_nif.add(row["provision_id"])
                not_in_force.append({
                    "provision_id": row["provision_id"],
                    "law": _clean(row.get("law_name"), 200),
                    "section": _clean(row.get("article_section"), 60),
                    "core_answer": _clean(row.get("core_legal_question_answer"), 500),
                    "Provision text": _clean(prov_text.get(row["provision_id"], ""), 12000),
                    "Provision text (English, machine)": _clean(
                        gloss_sec.get(row["provision_id"], ""), 12000),
                    "Full section text": _clean(_full_section(row["provision_id"]), 12000),
                })
            for v in row["verdicts"]:
                if not v["applies"]:
                    continue
                ind = from_artifact(v["indicator"])
                vv = verify.get((row["provision_id"], ind), {})
                pm = prov_meta.get(row["provision_id"], {})
                fires.append({
                    "Indicator": ind,
                    "Law": _clean(row.get("law_name"), 200),
                    "Section": _clean(row.get("article_section"), 60),
                    "Source URL": _clean(pm.get("url"), 300),
                    "Enacted": (_YEAR.search(row.get("law_name") or "") or [""])[0]
                               if _YEAR.search(row.get("law_name") or "") else "",
                    "Last amended": _clean(pm.get("last_amended"), 60),
                    "Crawled": _clean(pm.get("crawled"), 30),
                    "Score hint": v["score_hint"],
                    "Coverage": v["coverage"],
                    "Confidence": v["confidence"],
                    "Quote grounded": v["quote_grounded_ws"],
                    "Verification": vv.get("verifier_verdict", "pending"),
                    "Final applies": vv.get("final_applies", ""),
                    "Verbatim quote": _clean(v["verbatim_quote"], 2000),
                    # blank for an English source: there is nothing to gloss
                    "English (machine)": _clean(gloss.get((row["provision_id"], ind), ""), 2000),
                    "Provision text": _clean(prov_text.get(row["provision_id"], ""), 12000),
                    "Provision text (English, machine)": _clean(
                        gloss_sec.get(row["provision_id"], ""), 12000),
                    "Full section text": _clean(
                        _full_section(row["provision_id"]), 12000),
                    "Rationale": _clean(v["rationale"], 400),
                    "Verifier reason": _clean(
                        (vv.get("verifier") or {}).get("reason"), 400),
                    "Provision ID": row["provision_id"],
                })

    df = (pd.DataFrame(fires).sort_values(["Indicator", "Law", "Section"])
          if fires else pd.DataFrame(columns=FIRE_COLUMNS))
    by_ind = df.groupby("Indicator").agg(
        fires=("Provision ID", "count"),
        verified_agree=("Verification", lambda s: (s == "agree").sum()),
        overturned=("Verification", lambda s: (s == "tiebreak_overturned").sum()),
        pending=("Verification", lambda s: (s == "pending").sum()),
    ).reset_index()
    summary_rows = [
        {"Metric": "Economy", "Value": economy},
        {"Metric": "Provisions mapped", "Value": n_prov},
        {"Metric": "Mapping errors (flagged)", "Value": f"{n_err}  (listed on QA Errors)"},
        {"Metric": "Fires (indicator x provision)", "Value": len(df)},
        {"Metric": "Verification outcomes",
         "Value": json.dumps(dict(Counter(df["Verification"])))},
        {"Metric": "Ungrounded quotes", "Value": int((~df["Quote grounded"]).sum())},
        {"Metric": "Not-in-force provisions flagged", "Value": len(not_in_force)},
    ]

    # every sheet: row 1 = wrapped explanation banner, row 2 = header, data row 3+
    sheet_banners = {
        "Summary": f"• Run summary for {economy}: pipeline stats on top, per-indicator fire/verification counts below.\n"
                   "• Source: S4 Sonnet mapping + S5 blind verification (Haiku, Opus tiebreaks).\n"
                   "• 'pending' = fires awaiting verification (paused on API credits).",
        "All fires": "• Every (provision × indicator) verdict the mapper fired, all indicators together.\n"
                     "• One row per fire: quote (byte-grounded), the provision text and its machine English, rationale, verifier outcome.\n"
                     "• 'Provision text' and 'Provision text (English, machine)' are the SAME text in two languages. 'Full section text' is a wider extract from the source document and is NOT what the English column translates.\n"
                     "• Use the per-indicator sheets for the same rows grouped by indicator, with indicator explanations.",
        "QA Overturned": "• Fires REMOVED by the verification panel: Haiku disagreed blind and Opus sided with Haiku (2-of-3).\n"
                         "• These never reach the submission; kept here for audit and error analysis.",
        "QA Ungrounded": "• Fires whose verbatim quote failed the exact-substring check even after whitespace collapse.\n"
                         "• Curation locates the quote in the source PDF/text or drops the row — never submitted as-is.",
        "QA NotInForce": "• Provisions the trap check flagged as not yet commenced / repealed / bill-stage.\n"
                         "• Enforced-only rule: these cannot be scored; listed for transparency and NEW-lead follow-up.\n"
                         "• The provision text is shown with its machine English, so the flag can be checked against the text.",
        "QA Errors": "• Provisions whose verdict failed schema validation — the model's reply did not parse, so NO judgement exists for them.\n"
                     "• They are not misses and not rejections: nothing was decided. The provision text is shown, with its machine English, so it can be read and, if it matters, re-run.\n"
                     "• The law name and section come from the corpus, not from the reply, because the reply is what failed.",
    }

    path = out_dir / f"RDTII_P3_results_{economy}.xlsx"
    with pd.ExcelWriter(path, engine="openpyxl") as xl:
        def _sheet(frame, name, banner):  # noqa: ANN001
            frame.to_excel(xl, sheet_name=name, index=False, startrow=1)
            xl.book[name].cell(row=1, column=1, value=banner)

        _sheet(pd.DataFrame(summary_rows), "Summary", sheet_banners["Summary"])
        by_ind.to_excel(xl, sheet_name="Summary", index=False,
                        startrow=len(summary_rows) + 3)
        _sheet(df, "All fires", sheet_banners["All fires"])
        for ind in sorted(df["Indicator"].unique()):
            _sheet(df[df["Indicator"] == ind], ind, _indicator_banner(ind))
        _sheet(df[df["Verification"] == "tiebreak_overturned"],
               "QA Overturned", sheet_banners["QA Overturned"])
        _sheet(df[~df["Quote grounded"]], "QA Ungrounded", sheet_banners["QA Ungrounded"])
        _sheet(pd.DataFrame(not_in_force, columns=None if not_in_force else NIF_COLUMNS),
               "QA NotInForce", sheet_banners["QA NotInForce"])
        _sheet(pd.DataFrame(errored, columns=None if errored else ERR_COLUMNS),
               "QA Errors", sheet_banners["QA Errors"])
    _style_workbook(path)
    print(f"[excel] {len(df)} fires -> {path}")


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Per-economy review workbook")
    ap.add_argument("economy", nargs="?", default="SG")
    ap.add_argument("--extra-dirs", nargs="*", default=[],
                    help="further run directories for an economy mapped in more than one arm, "
                         "e.g. --extra-dirs <run>/out_tl52 when the primary OUT_DIR is <run>/out. "
                         "One workbook per country is what a reviewer should open.")
    a = ap.parse_args()
    export(a.economy, extra_dirs=a.extra_dirs)
