"""Audit view (PLAN T4) — renders out/audit/index.html from map+verify outputs.

Self-contained HTML: summary tiles, per-indicator counts, and a filterable
table of every fire with quote, rationale, trap checks, and the verifier
outcome. No external assets; opens offline.
"""
from __future__ import annotations

import html
import json
from collections import Counter

from pathlib import Path

from config.settings import SETTINGS


def _glosses(economy: str, arms) -> tuple[dict, dict]:      # noqa: ANN001
    """The machine English, if S9b has run. Read-only and optional.

    Checklist item 11 asks that the audit interface "can be driven by a non-technical policy
    officer". For a Chinese, Lao or Portuguese economy it could not be: this page showed the quote
    in the source script and nothing else, so a reviewer who does not read it had no way to check
    what the tool claimed. The gloss existed from 28 September and reached only the Excel workbook.

    The translation is shown, never filed. This module writes a review page; the emitter is
    output/submission.py, which does not open these files at all, and
    tests/test_gloss_isolation.py pins that by checking for the read.
    """
    quote, section = {}, {}
    for name, sink, key in (
            (f"gloss_{economy}.jsonl", quote, lambda r: (r["provision_id"], r["indicator"])),
            (f"gloss_sections_{economy}.jsonl", section, lambda r: r["provision_id"])):
      for arm in arms:                                       # noqa: E111 — flat is clearer here
        p = arm / "audit" / name
        if not p.exists():
            continue
        with p.open(encoding="utf-8") as f:
            for line in f:
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    continue
                txt = str(r.get("english") or "").strip()
                if not txt:
                    continue
                sink[key(r)] = {"en": txt, "literal": bool(r.get("is_literal", True)),
                                "model": r.get("model") or "", "original": r.get("original") or ""}
    return quote, section


def _load(economy: str, extra_dirs=()):      # noqa: ANN001
    """Fires for one economy, unioning every arm it was mapped in.

    Timor-Leste is mapped in two: pillars 6 and 7 in `out/`, the other 52 indicators in `out_tl52/`.
    That gave it two audit pages while every other economy had one. A reviewer should open one page
    per country, so the arms are unioned rather than left for a human to reconcile.
    """
    arms = [SETTINGS.out_dir, *(Path(d) for d in extra_dirs)]
    fires = []
    gloss_q, gloss_s = _glosses(economy, arms)
    verify = {}
    for arm in arms:
        vpath = arm / "verify" / f"verified_{economy}.jsonl"
        if not vpath.exists():
            continue
        with vpath.open(encoding="utf-8") as f:
            for line in f:
                r = json.loads(line)
                verify[(r["provision_id"], r["indicator"])] = r
    for arm in arms:                                           # noqa: E111
      vp = arm / "map" / f"verdicts_{economy}.jsonl"
      if vp.exists():
        for line in vp.open(encoding="utf-8"):
            row = json.loads(line)
            if "error" in row:
                continue
            for v in row["verdicts"]:
                if not v["applies"]:
                    continue
                vv = verify.get((row["provision_id"], v["indicator"]))
                fires.append({
                    "pid": row["provision_id"], "ind": v["indicator"],
                    "law": row.get("law_name") or "", "sec": row.get("article_section") or "",
                    "score": v["score_hint"], "cov": v["coverage"],
                    "conf": v["confidence"], "grounded": v["quote_grounded_ws"],
                    "quote": v["verbatim_quote"], "rat": v["rationale"],
                    "traps": row["trap_checks"],
                    # an indicator outside pillars 6 and 7 answers its own numbered TRAP lines
                    # (mapping/schema.py); a pillar 6-7 row carries none and renders as before
                    "own": [t.get("trap") for t in (v.get("own_traps") or []) if t.get("in_play")],
                    "verdict": (vv or {}).get("verifier_verdict", "pending"),
                    "final": (vv or {}).get("final_applies", None),
                    "en": gloss_q.get((row["provision_id"], v["indicator"])),
                    "en_sec": gloss_s.get(row["provision_id"]),
                })
    return fires


def render(economy: str = "SG", extra_dirs=()) -> None:      # noqa: ANN001
    fires = _load(economy, extra_dirs)
    out_dir = SETTINGS.out_dir / "audit"
    out_dir.mkdir(parents=True, exist_ok=True)

    by_ind = Counter(f["ind"] for f in fires)
    by_verdict = Counter(f["verdict"] for f in fires)

    def esc(s):  # noqa: ANN001
        return html.escape(str(s or ""))

    rows_html = []
    for f in sorted(fires, key=lambda x: (x["ind"], x["law"], x["sec"])):
        badge = {"agree": "#2e7d32", "tiebreak_upheld": "#1565c0",
                 "tiebreak_overturned": "#c62828", "split_flagged": "#e65100",
                 "error": "#757575", "pending": "#9e9e9e"}.get(f["verdict"], "#9e9e9e")
        traps = ", ".join(k for k, v in f["traps"].items() if v) or "—"
        if f.get("own"):
            traps += "; this indicator's TRAP lines in play: " + ", ".join(str(n) for n in f["own"])
        en, en_sec = f.get("en"), f.get("en_sec")

        def _mt(g, label):
            """A machine translation, always labelled, never presented as the source."""
            if not g:
                return ""
            warn = ("" if g["literal"] else
                    "<br><i class='warn'>the glosser reports the source text is too garbled "
                    "(OCR damage) to render faithfully — read this against the original</i>")
            return (f"<p class='mt'><b>{label} — machine translation, not evidence"
                    f"{' · ' + esc(g['model']) if g['model'] else ''}:</b><br>"
                    f"{esc(g['en'])}{warn}</p>")

        # The English belongs in the COLLAPSED row, not only behind the toggle: a reviewer who
        # cannot read the source script otherwise has to expand every row to learn anything.
        preview = esc(f["quote"][:100]) + "…"
        if en:
            flag = "" if en["literal"] else " ⚠"
            preview += (f"<br><span class='mt'>EN{flag}: {esc(en['en'][:110])}…</span>")
        rows_html.append(f"""
<tr data-ind="{esc(f['ind'])}" data-verdict="{esc(f['verdict'])}">
 <td>{esc(f['ind'])}</td>
 <td title="{esc(f['pid'])}">{esc(f['law'][:48])}<br><small>{esc(f['sec'])}</small></td>
 <td>{esc(f['score'])}<br><small>{esc(f['cov'])}</small></td>
 <td><span style="color:{badge};font-weight:600">{esc(f['verdict'])}</span><br>
     <small>conf {f['conf']:.2f}{'' if f['grounded'] else ' · ⚠ ungrounded'}</small></td>
 <td><details><summary>{preview}</summary>
     <p><b>Quote, as filed (the source's own bytes):</b><br>{esc(f['quote'])}</p>
     {_mt(en, 'The same quote in English')}
     <p><b>Rationale:</b> {esc(f['rat'])}</p>
     <p><b>Traps true:</b> {esc(traps)}</p>
     {_mt(en_sec, 'The whole provision in English')}</details></td>
</tr>""")

    # Explain the blue boxes only on a page that has some. An English-source economy has nothing to
    # translate, and a note about a feature the page does not use reads as boilerplate.
    n_en = sum(1 for f in fires if f.get("en") or f.get("en_sec"))
    n_rough = sum(1 for f in fires
                  if (f.get("en") and not f["en"]["literal"])
                  or (f.get("en_sec") and not f["en_sec"]["literal"]))
    gloss_note = ("" if not n_en else
                  "<p class='src'><b>About the English.</b> Text in a blue box is a "
                  "<b>machine translation, shown so this page can be read by someone who does not "
                  "read the source language. It is never what we file.</b> The evidence is always "
                  "the quote above it — the source document's own bytes, located by byte offset. "
                  f"{n_en} of {len(fires)} rows carry one"
                  + (f", and on {n_rough} the translator reports the source is too damaged (OCR) to "
                     "render faithfully rather than inventing a clean sentence — those rows need a "
                     "human against the PDF." if n_rough else ".")
                  + "</p>")

    tiles = "".join(
        f"<div class='tile'><div class='n'>{v}</div><div class='l'>{esc(k)}</div></div>"
        for k, v in [("fires", len(fires))] + sorted(by_verdict.items()))
    ind_tiles = "".join(
        f"<div class='tile'><div class='n'>{v}</div><div class='l'>{esc(k)}</div></div>"
        for k, v in sorted(by_ind.items()))
    options = "".join(f"<option>{esc(i)}</option>" for i in sorted(by_ind))

    page = f"""<!doctype html><meta charset="utf-8">
<title>RDTII P3 audit — {esc(economy)}</title>
<style>
 body{{font:14px/1.45 system-ui,sans-serif;margin:24px;max-width:1200px}}
 .tiles{{display:flex;gap:10px;flex-wrap:wrap;margin:12px 0}}
 .tile{{border:1px solid #ddd;border-radius:8px;padding:8px 14px;text-align:center}}
 .tile .n{{font-size:20px;font-weight:700}} .tile .l{{color:#666;font-size:12px}}
 table{{border-collapse:collapse;width:100%}} td,th{{border-top:1px solid #eee;padding:6px 8px;vertical-align:top;text-align:left}}
 details summary{{cursor:pointer;color:#444}}
 select{{padding:4px}}
 .mt{{color:#1a3f6b;background:#f2f6fb;border-left:3px solid #9bb8d6;padding:4px 8px;margin:6px 0}}
 .warn{{color:#a13b00}}
 .src{{border:1px solid #e0c98a;background:#fdf8ec;padding:8px 12px;border-radius:6px;margin:10px 0}}
</style>
<h1>RDTII P3 — mapping audit · {esc(economy)}</h1>
<p>Every fired (provision × indicator) verdict with its byte-grounded quote, rationale,
trap checks, and blind-verification outcome. Raw data: <code>out/map/verdicts_{esc(economy)}.jsonl</code>,
<code>out/verify/verified_{esc(economy)}.jsonl</code>.</p>
{gloss_note}
<div class="tiles">{tiles}</div>
<div class="tiles">{ind_tiles}</div>
<p>Filter: indicator <select id="fi"><option>all</option>{options}</select>
 verdict <select id="fv"><option>all</option><option>agree</option><option>tiebreak_upheld</option>
 <option>tiebreak_overturned</option><option>split_flagged</option><option>pending</option><option>error</option></select></p>
<table><thead><tr><th>Indicator</th><th>Law / section</th><th>Score</th><th>Verification</th><th>Evidence</th></tr></thead>
<tbody>{''.join(rows_html)}</tbody></table>
<script>
const fi=document.getElementById('fi'),fv=document.getElementById('fv');
function apply(){{for(const tr of document.querySelectorAll('tbody tr')){{
 tr.style.display=((fi.value==='all'||tr.dataset.ind===fi.value)&&(fv.value==='all'||tr.dataset.verdict===fv.value))?'':'none';}}}}
fi.onchange=fv.onchange=apply;
</script>"""
    (out_dir / f"index_{economy}.html").write_text(page, encoding="utf-8")
    print(f"[audit] {len(fires)} fires -> out/audit/index_{economy}.html")


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Per-economy audit page")
    ap.add_argument("economy", nargs="?", default="SG")
    ap.add_argument("--extra-dirs", nargs="*", default=[],
                    help="further run directories for an economy mapped in more than one arm")
    a = ap.parse_args()
    render(a.economy, extra_dirs=a.extra_dirs)
