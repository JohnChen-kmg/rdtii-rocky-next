"""Review decisions and the export.

A decision is one appended line in outputs/reviews/<run>/decisions.jsonl: accept, reject with a reason,
or correct up to five fields. Lines are never rewritten; the latest line for a row wins and the earlier
lines are the audit trail. Review applies to run output only; the frozen submission is read-only.

The export writes the host's 14 columns, in the host's order, as CSV (UTF-8 with BOM) and as xlsx built
with zipfile where every cell is an inline string, so `6.10` can never collapse to `6.1` and column O,
the host's own formula, is never written. Rejected rows leave the file; corrections are substituted in
place; review_log.csv beside the export carries every decision including the removals. The writer reads
the records files and the decisions, and never a gloss file: a translation can never become evidence.
"""
from __future__ import annotations

import csv
import io
import json
import re
import time
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape as _xml_escape

from . import readers
from .readers import HOST_COLUMNS
from .server import ApiError, App, FileResponse, rel_or_abs
from .settings import REPO, Settings

VERDICTS = ("accept", "reject", "correct")
REJECT_REASONS = ("wrong indicator", "quote not in the source", "citation wrong", "provision not in force",
                  "out of scope", "other")
CORRECTABLE = ("Indicator ID", "Article / Section", "Verbatim Snippet", "Discovery Tag", "Notes")
DISCOVERY_TAGS = ("NEW", "KNOWN", "")


def row_key(r: dict) -> str:
    """The finding key: provision id when the JSON gave one, else law, article and indicator."""
    pid = r.get("_pid")
    return f"{r['_econ']}|{pid or (r.get('Law Name', '') + '#' + r.get('Article / Section', ''))}|{r.get('Indicator ID', '')}"


def review_dir(s: Settings, run_id: str) -> Path:
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "__", run_id).strip("_")[:80]
    return s.runs_root / "reviews" / safe


def decisions_path(s: Settings, run_id: str) -> Path:
    return review_dir(s, run_id) / "decisions.jsonl"


def load_decisions(s: Settings, run_id: str) -> tuple[dict, list]:
    """(latest decision per key, every line in order)."""
    p = decisions_path(s, run_id)
    lines = readers.cached(p, readers.read_jsonl) or []
    latest: dict = {}
    for d in lines:
        latest[d["key"]] = d
    return latest, lines


def record_decision(s: Settings, run: dict, row: dict, body: dict, in_scope: set[str]) -> dict:
    if run.get("kind") == "frozen":
        raise ApiError(403, "the filed submission is frozen; review applies to run output only")
    verdict = str(body.get("verdict", "")).strip().lower()
    if verdict not in VERDICTS:
        raise ApiError(400, f"verdict must be one of {', '.join(VERDICTS)}")
    reason = str(body.get("reason", "")).strip()
    corrections_in = body.get("corrections") or {}
    corrections: dict = {}
    if verdict == "reject" and not reason:
        raise ApiError(400, "a rejection needs a reason")
    if verdict == "correct":
        if not isinstance(corrections_in, dict) or not corrections_in:
            raise ApiError(400, "a correction needs at least one changed field")
        for col, val in corrections_in.items():
            if col not in CORRECTABLE:
                raise ApiError(400, f"{col!r} cannot be corrected here; only {', '.join(CORRECTABLE)}")
            val = "" if val is None else str(val)
            if val == row.get(col, ""):
                continue
            if col == "Indicator ID":
                if val not in in_scope:
                    raise ApiError(400, f"{val!r} is not an indicator the instrument carries")
            if col == "Discovery Tag" and val not in DISCOVERY_TAGS:
                raise ApiError(400, "Discovery Tag must be NEW, KNOWN or blank")
            if col == "Verbatim Snippet":
                val = val.strip()
                if not val:
                    raise ApiError(400, "a Verbatim Snippet cannot be emptied; reject the row instead")
                gloss = (row.get("_gloss") or {}).get("english") or ""
                if gloss and val == gloss.strip():
                    raise ApiError(400, "that is the machine translation; the snippet must stay the source's own words")
                ctx = row.get("_raw_context") or {}
                source = "".join([ctx.get("before") or "", ctx.get("span") or row.get("Verbatim Snippet", ""), ctx.get("after") or ""])
                if val not in row.get("Verbatim Snippet", "") and val not in source:
                    raise ApiError(400, "the corrected snippet must be a passage of the source text shown on this row")
            corrections[col] = val
        if not corrections:
            raise ApiError(400, "nothing changed")
    reviewer = str(body.get("reviewer") or s.reviewer).strip()[:80] or s.reviewer
    line = {
        "decided_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "reviewer": reviewer, "run": run["id"],
        "economy": row["_econ"], "key": row_key(row), "provision_id": row.get("_pid"),
        "indicator": row.get("Indicator ID", ""), "law_name": row.get("Law Name", ""),
        "article": row.get("Article / Section", ""), "verdict": verdict, "reason": reason,
        "corrections": corrections, "prior": {c: row.get(c, "") for c in HOST_COLUMNS},
    }
    p = decisions_path(s, run["id"])
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps(line, ensure_ascii=False) + "\n")
    return line


# ---- the export -----------------------------------------------------------------------------------

def apply_decisions(rows: list[dict], latest: dict) -> tuple[list[dict], int, int]:
    """Rows after review: rejected rows removed, corrections substituted. Returns (rows, rejected, corrected)."""
    out = []
    rejected = corrected = 0
    for r in rows:
        d = latest.get(row_key(r))
        if d and d["verdict"] == "reject":
            rejected += 1
            continue
        row = {c: r.get(c, "") for c in HOST_COLUMNS}
        if d and d["verdict"] == "correct":
            row.update({k: v for k, v in d["corrections"].items() if k in HOST_COLUMNS})
            corrected += 1
        out.append(row)
    return out, rejected, corrected


def write_csv(rows: list[dict], path: Path) -> None:
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(HOST_COLUMNS)
        for r in rows:
            w.writerow([r.get(c, "") for c in HOST_COLUMNS])


_BAD_XML = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def _cell(ref: str, text: str) -> str:
    text = _BAD_XML.sub("", str(text))
    return f'<c r="{ref}" t="inlineStr"><is><t xml:space="preserve">{_xml_escape(text)}</t></is></c>'


def _col(i: int) -> str:
    s = ""
    i += 1
    while i:
        i, rem = divmod(i - 1, 26)
        s = chr(65 + rem) + s
    return s


def write_xlsx(rows: list[dict], path: Path, sheet_name: str = "Output Data") -> None:
    """A minimal workbook: one sheet, every cell an inline string, columns A to N only."""
    lines = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
             '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>']
    all_rows = [list(HOST_COLUMNS)] + [[r.get(c, "") for c in HOST_COLUMNS] for r in rows]
    for ri, values in enumerate(all_rows, start=1):
        cells = "".join(_cell(f"{_col(ci)}{ri}", v) for ci, v in enumerate(values))
        lines.append(f'<row r="{ri}">{cells}</row>')
    lines.append("</sheetData></worksheet>")
    sheet_xml = "".join(lines)
    content_types = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                     '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                     '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                     '<Default Extension="xml" ContentType="application/xml"/>'
                     '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
                     '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
                     '</Types>')
    rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
            '</Relationships>')
    workbook = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
                'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
                f'<sheets><sheet name="{_xml_escape(sheet_name)}" sheetId="1" r:id="rId1"/></sheets></workbook>')
    wb_rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
               '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
               '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
               '</Relationships>')
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types)
        z.writestr("_rels/.rels", rels)
        z.writestr("xl/workbook.xml", workbook)
        z.writestr("xl/_rels/workbook.xml.rels", wb_rels)
        z.writestr("xl/worksheets/sheet1.xml", sheet_xml)


def write_review_log(lines: list[dict], path: Path) -> None:
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["decided_at", "reviewer", "run", "economy", "provision_id", "indicator", "law_name", "article",
                    "verdict", "reason", "corrections", "prior"])
        for d in lines:
            w.writerow([d.get("decided_at"), d.get("reviewer"), d.get("run"), d.get("economy"), d.get("provision_id"),
                        d.get("indicator"), d.get("law_name"), d.get("article"), d.get("verdict"), d.get("reason"),
                        json.dumps(d.get("corrections") or {}, ensure_ascii=False),
                        json.dumps(d.get("prior") or {}, ensure_ascii=False)])


def export(s: Settings, run: dict, rows: list[dict], economy: str, fmt: str) -> dict:
    if fmt not in ("csv", "xlsx"):
        raise ApiError(400, "fmt must be csv or xlsx")
    latest, lines = load_decisions(s, run["id"])
    if run.get("kind") == "frozen":
        latest, lines = {}, []
    chosen = [r for r in rows if not economy or r["_econ"] == economy.upper()]
    out_rows, rejected, corrected = apply_decisions(chosen, latest)
    out_dir = review_dir(s, run["id"]) / "export"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    name = f"records_{economy.upper() if economy else 'ALL'}_{stamp}.{fmt}"
    path = out_dir / name
    (write_csv if fmt == "csv" else write_xlsx)(out_rows, path)
    log_path = out_dir / "review_log.csv"
    write_review_log(lines, log_path)
    return {"path": path, "filename": name, "rows": len(out_rows), "rejected": rejected, "corrected": corrected,
            "review_log": str(log_path), "decisions": len(lines)}


# ---- routes -------------------------------------------------------------------------------------------

def register(app: App) -> None:
    from .pages import mapping as _mapping

    @app.route("GET", r"/api/map/decisions")
    def list_decisions(app: App, m, q, b):
        run = _mapping.find_run(app.settings, q.get("run", ""))
        latest, lines = load_decisions(app.settings, run["id"])
        return 200, {"run": run["id"], "latest": latest, "lines": lines, "reasons": list(REJECT_REASONS),
                     "correctable": list(CORRECTABLE), "reviewer": app.settings.reviewer,
                     "path": rel_or_abs(decisions_path(app.settings, run["id"]), REPO)}

    @app.route("POST", r"/api/map/decisions")
    def decide(app: App, m, q, b):
        b = b or {}
        run = _mapping.find_run(app.settings, str(b.get("run", "")))
        try:
            i = int(b.get("i"))
        except (TypeError, ValueError):
            raise ApiError(400, "i (the row index) is required") from None
        row = _mapping.row_detail(run, i, app.settings)
        order = readers.parse_indicator_order(app.settings.instrument_dir / "indicator_order.yaml")
        in_scope = {it["id"] for it in order.get("indicators", []) if it.get("status") == "in_scope"}
        line = record_decision(app.settings, run, row, b, in_scope)
        return 200, {"decision": line}

    @app.route("GET", r"/api/map/export")
    def export_route(app: App, m, q, b):
        run = _mapping.find_run(app.settings, q.get("run", ""))
        rows, _ = _mapping.build_rows(run, app.settings)
        result = export(app.settings, run, rows, q.get("economy", "").strip(), q.get("fmt", "csv"))
        ctype = ("text/csv; charset=utf-8" if result["filename"].endswith(".csv")
                 else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        return 200, FileResponse(result["path"], result["filename"], ctype,
                                 headers={"X-RDTII-Rows": str(result["rows"]), "X-RDTII-Rejected": str(result["rejected"]),
                                          "X-RDTII-Corrected": str(result["corrected"])})

    @app.route("GET", r"/api/map/export/summary")
    def export_summary(app: App, m, q, b):
        run = _mapping.find_run(app.settings, q.get("run", ""))
        rows, _ = _mapping.build_rows(run, app.settings)
        latest, lines = load_decisions(app.settings, run["id"])
        economy = q.get("economy", "").strip().upper()
        chosen = [r for r in rows if not economy or r["_econ"] == economy]
        out_rows, rejected, corrected = apply_decisions(chosen, latest)
        accepted = sum(1 for r in chosen if (latest.get(row_key(r)) or {}).get("verdict") == "accept")
        return 200, {"rows_in": len(chosen), "rows_out": len(out_rows), "rejected": rejected, "corrected": corrected,
                     "accepted": accepted, "decisions": len(lines), "frozen": run.get("kind") == "frozen",
                     "export_dir": rel_or_abs(review_dir(app.settings, run["id"]) / "export", REPO)}
