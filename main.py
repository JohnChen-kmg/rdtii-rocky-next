#!/usr/bin/env python3
"""RDTII Rocky — single entry point for the consolidated submission repo.

Modes
-----
serve (default)   python main.py --economy Singapore --pillar 6
                  Re-emits the judged results: filters submission/records_<ECON>
                  by pillar into outputs/<ECON>_P<pillar>_<timestamp>.csv/.json.
                  Stdlib only — no heavy imports on this path.

--demo            The scanned-PDF walkthrough: wraps `p2-extract demo` on
                  my-cma1998-001 (live gold-page CER, then the full extraction
                  pipeline over the 144-page scan).

--mini-run        A real end-to-end 5-document slice through P1 -> P2 -> P3,
                  producing labeled demonstration mini-CSVs. `--offline`
                  substitutes the pre-fetched raw files in demo_data/mini_raw/.

--quick           The live-pitch variant of the mini-run: P1 smoke proof +
                  live fetch of TWO laws (html + native pdf), a seconds-scale
                  gold-page CER pilot instead of the full OCR, then the same
                  P2 -> P3 chain on just those two docs. `--offline` supported.

Timing truth: the 5-10 minute quick tier assumes the KEYED stack (Anthropic
API). Keyless runs complete on local Ollama at a much slower, measured
per-provision rate — RUN_SUMMARY.md records the measured rate and a labeled
projection, never a pretended speed. `--map-limit N` caps S4 mapping per
economy for a fast mechanics proof (capped runs are labeled as such).

--docs a,b,c      Override the curated doc slice for --mini-run/--quick with
                  explicit doc_ids ("hand us a law"). Offline mode can serve
                  any doc staged in demo_data/mini_raw/; live mode any law the
                  seed crawl retrieves.

--full-pipeline   Prints the per-stage commands for the complete corpus
                  (no execution) and points at docs/DATA.md.

The repo ships NO API key. Keyless runs fall back to local Ollama, loudly.
This wrapper passes flags and environment variables only — it never modifies
anything under stages/.
"""
from __future__ import annotations

import argparse
import csv
import difflib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent
STAGES = REPO / "stages"
P1 = STAGES / "p1-scrape"
P2 = STAGES / "p2-extract"
P3 = STAGES / "p3-map"
OUTPUTS = REPO / "outputs"
SUBMISSION = REPO / "submission"
MINI_RAW = REPO / "demo_data" / "mini_raw"
DEMO_SCAN = REPO / "demo_data" / "my-cma1998-001.pdf"

# The economy table comes from the stage, never from a copy in this file. Round 1 kept its own
# three-economy dict here, and that is why this wrapper refused China at argument parsing while the
# stage itself was ready for it: `--economy China` and `--docs cn-...-001` both exited 2, the second
# with "no recognizable economy prefix (sg-/my-/au-)". config/economies.py is stdlib-only, so serve
# mode keeps its promise of no heavy imports.
if str(P3) not in sys.path:
    sys.path.insert(0, str(P3))
try:
    from config.economies import (ALIASES as ECON_ALIASES, ECON_NAME as ECON_NAMES,
                                  economies_needing_dense, sparse_leg_adequate)
except ImportError as _exc:  # a broken stage tree must say so, not silently serve three economies
    print(f"[main] cannot read the economy table from {P3}: {_exc}", file=sys.stderr)
    raise

# The curated mini-run slice: 5 docs that verifiably produced rows in the full
# judged run, covering all 3 source types and all 3 economies. Curation is
# disclosed in every mini-run output (see demo_data/mini_raw/README.md).
MINI_DOCS = [
    {"doc_id": "au-scia2018-001", "economy": "AU", "source_type": "html",
     "law": "Security of Critical Infrastructure Act 2018",
     "why": "the HTML lane (host: harder, higher-value); P7-I2 KNOWN anchor s.30CW(4)"},
    {"doc_id": "au-ta1979-002", "economy": "AU", "source_type": "html",
     "law": "Telecommunications (Interception and Access) Act 1979",
     "why": "2nd html doc; strongest html NEW-row producer in the judged run "
            "(5 NEW rows in records_AU)"},
    {"doc_id": "my-cma1998-001", "economy": "MY", "source_type": "pdf_scanned",
     "law": "Communications and Multimedia Act 1998",
     "why": "the mandatory scanned beat; live gold-page CER measurement"},
    {"doc_id": "my-pdpa2010-001", "economy": "MY", "source_type": "pdf_native",
     "law": "Personal Data Protection Act 2010",
     "why": "MY PDPA; KNOWN anchors (257 provisions in the full run)"},
    {"doc_id": "sg-pdpa2012-001", "economy": "SG", "source_type": "pdf_native",
     "law": "Personal Data Protection Act 2012",
     "why": "the canonical s.26(1) trap doc (P6-I4 applies / P6-I1 rejected)"},
]
MINI_BY_ID = {d["doc_id"]: d for d in MINI_DOCS}

# The --quick live-pitch pair: one html + one native pdf, both KNOWN-anchor
# producers, both fetchable live in ~seconds each.
QUICK_DOC_IDS = ["au-scia2018-001", "my-pdpa2010-001"]

_STEPS: list[dict] = []  # (label, seconds, rc) — feeds RUN_SUMMARY.md


def make_disclosure(n_docs: int) -> str:
    return (f"DEMONSTRATION SLICE ({n_docs} curated law"
            f"{'s' if n_docs != 1 else ''}) - NOT the judged submission "
            "records; those are in submission/")


# ------------------------------------------------------------------ helpers --

def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _say(msg: str) -> None:
    print(f"[main] {msg}", flush=True)


def _banner(lines: list[str]) -> None:
    width = max(len(l) for l in lines) + 4
    print("=" * width, flush=True)
    for l in lines:
        print(f"  {l}", flush=True)
    print("=" * width, flush=True)


def resolve_economy(raw: str) -> str:
    """Tolerant economy parsing: names, codes, case-insensitive. Unknown input
    exits 2 with a difflib-powered 'did you mean' plus the valid list."""
    key = (raw or "").strip().lower()
    if key in ECON_ALIASES:
        return ECON_ALIASES[key]
    close = difflib.get_close_matches(key, list(ECON_ALIASES), n=1, cutoff=0.6)
    valid = ", ".join(f"{c} ({ECON_NAMES[c]})" for c in ECON_NAMES)
    if close:
        guess = ECON_ALIASES[close[0]]
        print(f"[main] unknown economy {raw!r} - did you mean "
              f"'{ECON_NAMES[guess]}' ({guess})?  Valid economies: {valid}",
              file=sys.stderr)
    else:
        print(f"[main] unknown economy {raw!r}. Valid economies: {valid}",
              file=sys.stderr)
    sys.exit(2)


def resolve_economies(raw: str | None) -> list[str]:
    if not raw:
        return ["SG", "MY", "AU"]
    seen: list[str] = []
    for tok in raw.split(","):
        if tok.strip():
            code = resolve_economy(tok)
            if code not in seen:
                seen.append(code)
    return seen or ["SG", "MY", "AU"]


def keyless() -> bool:
    return not os.environ.get("ANTHROPIC_API_KEY", "").strip()


def announce_backend() -> str:
    if keyless():
        _banner([
            "NO ANTHROPIC_API_KEY IN THE ENVIRONMENT - RUNNING KEYLESS.",
            "Every LLM step now auto-falls back to LOCAL OLLAMA open-source",
            "models ($0; the pipeline's designed no-key path). Each stage",
            "announces its own fallback again when it starts.",
            "To reproduce the judged configuration, provide a key via the",
            "environment or a .env file (see .env.example).",
        ])
        return "keyless -> local Ollama fallback"
    _say("ANTHROPIC_API_KEY found in the environment - using the API backend.")
    return "Anthropic API (key from environment)"


def tesseract_available() -> bool:
    if shutil.which("tesseract"):
        return True
    candidates = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe"),
    ]
    return any(Path(c).is_file() for c in candidates)


def run_step(label: str, cmd: list[str], cwd: Path, env: dict | None = None,
             check: bool = True) -> int:
    """Run one stage command with live output; record wall-clock for the
    summary. Wrapper-only: flags + env vars, cwd = the stage's own root."""
    _say(f"--> {label}")
    _say("    $ " + " ".join(str(c) for c in cmd) + f"   (cwd={cwd})")
    t0 = time.monotonic()
    proc = subprocess.run(cmd, cwd=str(cwd), env=env)
    dt = time.monotonic() - t0
    _STEPS.append({"label": label, "seconds": round(dt, 1), "rc": proc.returncode})
    _say(f"<-- {label}: rc={proc.returncode} in {dt:.1f}s")
    if check and proc.returncode != 0:
        raise RuntimeError(f"stage step failed (rc={proc.returncode}): {label}")
    return proc.returncode


def _base_env(extra: dict[str, str] | None = None) -> dict[str, str]:
    env = os.environ.copy()
    # Windows consoles default to cp1252; the stages print statute names with
    # non-ASCII characters. Env-var-only fix, no stage changes.
    env.setdefault("PYTHONUTF8", "1")
    env.setdefault("PYTHONIOENCODING", "utf-8")
    if extra:
        env.update(extra)
    return env


# --------------------------------------------------------------- serve mode --

def cmd_serve(economy_raw: str, pillar: int) -> int:
    econ = resolve_economy(economy_raw)
    src_csv = SUBMISSION / f"records_{econ}.csv"
    src_json = SUBMISSION / f"records_{econ}.json"
    if not src_csv.is_file() or not src_json.is_file():
        print(
            "[main] submission/ is not present in this checkout yet.\n"
            "  The judged records (records_{SG,MY,AU}.csv/.json) are force-copied\n"
            "  from the P3 out/ tree only after the final re-emit is verified\n"
            "  (see ASSEMBLY_MANIFEST / docs/DATA.md). Nothing to serve yet.\n"
            "  A labeled demonstration slice is available right now:\n"
            "      python main.py --mini-run --offline",
            file=sys.stderr)
        return 1

    prefix = f"P{pillar}-"
    OUTPUTS.mkdir(exist_ok=True)
    stamp = _ts()
    out_csv = OUTPUTS / f"{econ}_P{pillar}_{stamp}.csv"
    out_json = OUTPUTS / f"{econ}_P{pillar}_{stamp}.json"

    # CSV: preserve the exact column order of the judged file (13 frozen cols).
    with src_csv.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        columns = list(reader.fieldnames or [])
        rows = [r for r in reader if (r.get("Indicator ID") or "").startswith(prefix)]
    with out_csv.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=columns)
        w.writeheader()
        w.writerows(rows)

    # JSON: same per-law grouping + extra fields; only the pillar filter applied.
    data = json.loads(src_json.read_text(encoding="utf-8"))
    laws_out = []
    kept = 0
    for law in data.get("laws", []):
        provisions = [p for p in law.get("provisions", [])
                      if str(p.get("Indicator ID", "")).startswith(prefix)]
        if provisions:
            law_out = dict(law)
            law_out["provisions"] = provisions
            laws_out.append(law_out)
            kept += len(provisions)
    data_out = dict(data)
    data_out["laws"] = laws_out
    out_json.write_text(json.dumps(data_out, ensure_ascii=False, indent=2),
                        encoding="utf-8")

    _say(f"{ECON_NAMES[econ]} pillar {pillar}: {len(rows)} CSV rows "
         f"({len(columns)} columns preserved), {kept} JSON provisions "
         f"across {len(laws_out)} laws")
    _say(f"wrote {out_csv}")
    _say(f"wrote {out_json}")
    return 0


# ------------------------------------------------------- offline P1 staging --

def stage_offline_handoff1(h1: Path) -> None:
    """Substitute the live P1 crawl with the pre-fetched mini_raw slice."""
    _banner([
        "OFFLINE SUBSTITUTION - the live P1 crawl is being SKIPPED.",
        "Pre-fetched raw files from demo_data/mini_raw/ are staged instead",
        "(harvested byte-for-byte from the shipped handoff1_v2 corpus).",
        "Live-crawl evidence for these fetches = the .headers.json sidecars",
        "+ the crawl_log.jsonl slice staged alongside them.",
    ])
    t0 = time.monotonic()
    h1.mkdir(parents=True, exist_ok=True)
    shutil.copy2(MINI_RAW / "manifest.csv", h1 / "manifest.csv")
    shutil.copy2(MINI_RAW / "crawl_log.jsonl", h1 / "crawl_log.jsonl")
    for src in (MINI_RAW / "raw").rglob("*"):
        if src.is_file():
            dst = h1 / src.relative_to(MINI_RAW)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
    # the 12 MB scan is committed once at demo_data/; stage it at its
    # manifest local_path (sha256-identical to the corpus copy)
    with (MINI_RAW / "manifest.csv").open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            if row["doc_id"] == "my-cma1998-001":
                dst = h1 / row["local_path"]
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(DEMO_SCAN, dst)
    _STEPS.append({"label": "P1 offline substitution (mini_raw -> work/handoff1)",
                   "seconds": round(time.monotonic() - t0, 1), "rc": 0})


def _econ_of_doc_id(doc_id: str) -> str | None:
    cc = doc_id.split("-", 1)[0].upper()
    return cc if cc in ECON_NAMES else None


def build_wanted(variant: str, docs_csv: str | None,
                 economies_filter: list[str]) -> list[dict]:
    """The doc slice this run should process (before manifest resolution)."""
    if docs_csv:
        wants = []
        for tok in docs_csv.split(","):
            doc_id = tok.strip()
            if not doc_id:
                continue
            base = MINI_BY_ID.get(doc_id)
            econ = _econ_of_doc_id(doc_id)
            if base is None and econ is None:
                prefixes = "/".join(f"{c.lower()}-" for c in ECON_NAMES)
                _say(f"ERROR: --docs entry {doc_id!r} has no recognizable "
                     f"economy prefix ({prefixes})")
                sys.exit(2)
            wants.append(base or {
                "doc_id": doc_id, "economy": econ, "source_type": None,
                "law": None, "why": "requested via --docs"})
        return wants
    ids = QUICK_DOC_IDS if variant == "quick" else [d["doc_id"] for d in MINI_DOCS]
    return [MINI_BY_ID[i] for i in ids
            if MINI_BY_ID[i]["economy"] in economies_filter]


def resolve_docs(manifest_csv: Path, wants: list[dict]) -> list[dict]:
    """Match the wanted docs against whatever manifest the P1 step produced.

    Offline: doc_ids match exactly. Live: a fresh crawl may mint different
    doc_ids, so fall back to (economy, fuzzy law-name) matching."""
    with manifest_csv.open(encoding="utf-8-sig", newline="") as f:
        rows = [r for r in csv.DictReader(f)
                if "superseded by" not in (r.get("crawl_notes") or "")]
    by_id = {r["doc_id"]: r for r in rows}

    def _tokens(s: str) -> set[str]:
        return {t for t in "".join(c if c.isalnum() else " "
                                   for c in (s or "").lower()).split() if t}

    resolved = []
    for want in wants:
        got = by_id.get(want["doc_id"])
        if got is None and want.get("law"):
            wt = _tokens(want["law"])
            best, best_score = None, 0.0
            for r in rows:
                if r["economy"] != want["economy"]:
                    continue
                rt = _tokens(r.get("law_name_guess") or "")
                if not rt:
                    continue
                score = len(wt & rt) / max(len(wt | rt), 1)
                if r.get("source_type") == want.get("source_type"):
                    score += 0.1
                if score > best_score:
                    best, best_score = r, score
            if best is not None and best_score >= 0.6:
                got = best
                _say(f"doc resolution: {want['law']!r} -> {got['doc_id']} "
                     f"(fuzzy match, score {best_score:.2f})")
        if got is None:
            _say(f"WARNING: {want['doc_id']} ({want.get('law') or 'no law name'}) "
                 f"not found in the produced manifest - dropped from this run "
                 f"(disclosed in RUN_SUMMARY.md). Available doc_ids: "
                 + ", ".join(sorted(by_id)[:12])
                 + (" ..." if len(by_id) > 12 else ""))
            continue
        resolved.append({
            "doc_id": got["doc_id"],
            "economy": got["economy"],
            "source_type": got.get("source_type") or want.get("source_type"),
            "law": got.get("law_name_guess") or want.get("law"),
            "why": want.get("why") or "requested via --docs",
        })
    return resolved


# ------------------------------------------------------- mini-run and quick --

def cmd_pipeline_slice(offline: bool, economy_raw: str | None,
                       variant: str = "mini", docs_csv: str | None = None,
                       map_limit: int | None = None) -> int:
    """The shared P1 -> P2 -> P3 demonstration-slice driver.

    variant='mini'  : the 5-doc slice (full scanned-doc OCR via p2 demo).
    variant='quick' : the live-pitch pair (smoke proof + 2 live fetches +
                      seconds-scale gold-page CER pilot instead of full OCR).
    docs_csv        : explicit doc_id list overriding the curated slice.
    map_limit       : cap S4 mapping at N provisions per economy (an existing
                      stage hook: mapping.runner's positional limit). A capped
                      run proves the chain mechanically; its mini-CSV reflects
                      only the mapped subset and says so.
    """
    economies_filter = resolve_economies(economy_raw)
    wants = build_wanted(variant, docs_csv, economies_filter)
    if not wants:
        _say("nothing to run: the economy filter removed every doc in the slice")
        return 2
    economies = []
    for w in wants:
        if w["economy"] not in economies:
            economies.append(w["economy"])

    stamp = _ts()
    run_dir = OUTPUTS / f"demo_run_{stamp}"
    work = run_dir / "work"
    h1, h2, p3out, index_dir = (work / "handoff1", work / "handoff2",
                                work / "p3out", work / "index")
    run_dir.mkdir(parents=True, exist_ok=True)
    disclosure = make_disclosure(len(wants))
    variant_line = (f"variant: quick ({len(wants)} docs)" if variant == "quick"
                    else f"variant: mini-run ({len(wants)} docs)")

    _banner([disclosure,
             variant_line + ("   [--docs override]" if docs_csv else ""),
             f"run dir: {run_dir}",
             f"economies: {', '.join(economies)}   mode: "
             f"{'offline' if offline else 'live crawl'}"])
    backend = announce_backend()
    tess = tesseract_available()
    if not tess:
        _banner([
            "Tesseract OCR binary NOT FOUND - scanned-PDF beats will be",
            "SKIPPED in this run. Install it to restore them:",
            "    winget install UB-Mannheim.TesseractOCR",
            "The skip is disclosed in RUN_SUMMARY.md.",
        ])

    summary_notes: list[str] = []
    mini_outputs: list[Path] = []
    docs: list[dict] = []
    ok = True
    try:
        # ---- [P1] hand-off #1 -------------------------------------------
        if offline:
            stage_offline_handoff1(h1)
            summary_notes.append(
                "P1 ran in OFFLINE mode: the live crawl was substituted with "
                "the pre-fetched raw files in demo_data/mini_raw/ (harvested "
                "from the shipped handoff1_v2 corpus, sha256-verified). "
                "Live-crawl evidence = the .headers.json sidecars + the "
                "crawl_log.jsonl slice.")
        elif variant == "quick":
            run_step("P1 smoke (3-portal live-fetch proof)",
                     [sys.executable, "scrape.py", "--smoke", "--out", str(h1)],
                     cwd=P1, env=_base_env(), check=False)
            for econ in economies:
                types = {w.get("source_type") for w in wants
                         if w["economy"] == econ}
                types.discard(None)
                forms = ("html" if types == {"html"}
                         else "pdf" if types and types <= {"pdf_native", "pdf_scanned"}
                         else "both")
                run_step(
                    f"P1 live seed-slice crawl ({econ}, forms={forms})",
                    [sys.executable, "scrape.py", "--economy", econ,
                     "--seed-laws-only", "--forms", forms, "--out", str(h1)],
                    cwd=P1, env=_base_env())
            summary_notes.append(
                "P1 quick mode ran LIVE: the 3-portal smoke proof plus the "
                "narrowest existing upstream hook for the target laws - "
                "per-economy `--seed-laws-only` crawls narrowed by `--forms` "
                "(P1 exposes no per-law fetch; the whole per-economy seed "
                "list is fetched, politeness intact, and only the target "
                "docs continue downstream). Evidence: crawl_log.jsonl + "
                ".headers.json sidecars in the work dir.")
        else:
            run_step(
                f"P1 live seed-slice crawl ({','.join(economies)})",
                [sys.executable, "scrape.py", "--economy", ",".join(economies),
                 "--seed-laws-only", "--out", str(h1)],
                cwd=P1, env=_base_env())
            summary_notes.append(
                "P1 ran LIVE (--seed-laws-only slice; politeness intact). "
                "Per-fetch URL/status/sha256 evidence: work/handoff1/"
                "crawl_log.jsonl + the .headers.json sidecars.")

        docs = resolve_docs(h1 / "manifest.csv", wants)
        if not docs:
            raise RuntimeError("no wanted docs resolved from the manifest")
        if len(docs) < len(wants):
            summary_notes.append(
                f"Only {len(docs)}/{len(wants)} wanted docs resolved from the "
                "manifest this run - the missing ones are logged above.")
        if not tess:
            before = len(docs)
            docs = [d for d in docs if d["source_type"] != "pdf_scanned"]
            if len(docs) != before:
                summary_notes.append(
                    "Tesseract was NOT installed on this machine: scanned "
                    "doc(s) (and their live CER measurement) were skipped. "
                    "They remain part of the shipped configuration; install "
                    "Tesseract to run them.")

        # ---- [P2] extract ------------------------------------------------
        p2_env = _base_env()
        common = ["--manifest", str(h1 / "manifest.csv"),
                  "--raw", str(h1), "--out", str(h2)]
        if variant == "quick" and tess:
            # seconds-scale scanned beat: one-page OCR vs the committed gold
            # page (the full 144-page OCR lives in --mini-run / --demo)
            gold = sorted((P2 / "fixtures" / "ocr_reference" / "my-cma1998-001"
                           ).glob("gold_page_*.txt"))
            if gold:
                m = re.search(r"(\d+)", gold[0].stem)
                page = int(m.group(1)) if m else 1
                rc = run_step(
                    f"P2 quick CER pilot (gold page {page}, live one-page OCR)",
                    [sys.executable, "-m", "rdtii_p2.cli", "pilot",
                     "--scan", str(DEMO_SCAN),
                     "--gold", str(gold[0]), "--page", str(page),
                     "--doc-id", "my-cma1998-001",
                     "--out", str(work / "ocr_pilot")],
                    cwd=P2, env=p2_env, check=False)
                summary_notes.append(
                    "Quick-mode scanned beat = a live one-page CER "
                    "re-measurement against the committed gold page "
                    f"(rc={rc}; nonzero = CER missed the <5% bar). The full "
                    "144-page OCR extraction is the --mini-run / --demo path. "
                    f"Report: {work / 'ocr_pilot' / 'my-cma1998-001' / 'cer_report.json'}")
            else:
                summary_notes.append(
                    "Quick-mode CER pilot skipped: no committed gold page "
                    "found under stages/p2-extract/fixtures/ocr_reference/.")
        scanned = [d for d in docs if d["source_type"] == "pdf_scanned"]
        rest = [d for d in docs if d["source_type"] != "pdf_scanned"]
        for d in scanned:
            # demo FIRST: live gold-page CER re-measurement, then the full
            # pipeline over the scan (records inherit the measured CER).
            # p2 demo exits 1 if CER >= 5% - that is a finding, not a crash.
            rc = run_step(
                f"P2 scanned-doc demo + extract ({d['doc_id']}, live CER)",
                [sys.executable, "-m", "rdtii_p2.cli", "demo",
                 "--doc", d["doc_id"], *common],
                cwd=P2, env=p2_env, check=False)
            if rc != 0:
                summary_notes.append(
                    f"P2 demo for {d['doc_id']} returned rc={rc} (it exits "
                    "nonzero when the gold-page CER misses the <5% bar or the "
                    "doc fails) - see the stage output above.")
        for d in rest:
            run_step(
                f"P2 extract {d['doc_id']} ({d['source_type']})",
                [sys.executable, "-m", "rdtii_p2.cli", "run",
                 *common, "--only-doc", d["doc_id"], "--skip-tags"],
                cwd=P2, env=p2_env)
        summary_notes.append(
            "P2 ran with --skip-tags for the non-scanned docs (tags are soft "
            "routing hints; a docs-scale corpus needs no thinning - S3 keeps "
            "everything)." + (
                " The scanned doc was processed via `p2-extract demo` (tags "
                "on), so its records carry the live-measured gold-page CER."
                if scanned else ""))

        # ---- [P3] map ----------------------------------------------------
        p3_env = _base_env({
            "HANDOFF2_DIR": str(h2),
            "MANIFEST_PATH": str(h1 / "manifest.csv"),
            "OUT_DIR": str(p3out),
            "INDEX_DIR": str(index_dir),
        })
        mod = [sys.executable, "-m"]
        run_step("P3 S0 ingest", mod + ["src.p3map.cli", "ingest"], P3, p3_env)
        summary_notes.append(_retrieval_legs(index_dir, economies, p3_env, mod))
        run_step("P3 S2 select (RRF bands + recall gate)",
                 mod + ["src.p3map.cli", "select"], P3, p3_env)
        run_step("P3 S3 gray-band triage (local model)",
                 mod + ["src.p3map.cli", "triage"], P3, p3_env)
        # production triage standard is the S3b judge (see the 07-15 A/B);
        # S4 mapping reads its output file, so it must run (near-no-op on a
        # slice whose gray band is tiny/empty)
        run_step("P3 S3b triage judge (production standard; feeds S4)",
                 mod + ["src.p3map.triage.haiku"], P3, p3_env)
        run_step("P3 baseline parse (Round-1 KNOWN reference)",
                 mod + ["src.p3map.discovery.baseline"], P3, p3_env)
        if keyless():
            summary_notes.append(
                "KEYLESS QUALITY CAVEAT: S4/S5 ran on the local Ollama "
                "fallback. The mapping system prompt (the full instrument) is "
                "~6.5k tokens; an Ollama server at its default 4096 context "
                "window TRUNCATES it, so keyless verdicts are made against a "
                "partial instrument and are slower and weaker than the keyed "
                "path (raise OLLAMA_CONTEXT_LENGTH on the Ollama service to "
                "widen it). The keyless path proves the chain runs without "
                "any key; the judged configuration is the keyed one.")
        if map_limit:
            summary_notes.append(
                f"S4 MAPPING WAS CAPPED at {map_limit} provisions per economy "
                "(--map-limit; the runner's own limit hook). This run is a "
                "MECHANICS PROOF of the chain - the mini-CSV reflects only "
                "the mapped subset, not the full slice.")
        for econ in economies:
            map_cmd = mod + ["src.p3map.mapping.runner", econ]
            if map_limit:
                map_cmd.append(str(map_limit))
            run_step(f"P3 S4 mapping ({econ})"
                     + (f" [capped at {map_limit}]" if map_limit else ""),
                     map_cmd, P3, p3_env)
            run_step(f"P3 S5 blind verify ({econ})",
                     mod + ["src.p3map.verify.blind", econ], P3, p3_env)
            run_step(f"P3 S7 NEW/KNOWN diff ({econ})",
                     mod + ["src.p3map.discovery.newknown", econ], P3, p3_env)
            run_step(f"P3 S6 score rollup ({econ})",
                     mod + ["src.p3map.rollup", econ], P3, p3_env)
            run_step(f"P3 S9 submission emit ({econ})",
                     mod + ["src.p3map.output.submission", econ], P3, p3_env)
            run_step(f"P3 review workbook ({econ})",
                     mod + ["src.p3map.output.excel_export", econ], P3, p3_env)
            run_step(f"P3 audit page ({econ})",
                     mod + ["src.p3map.verify.audit_view", econ], P3, p3_env)
        summary_notes.append(
            "S10 eval was SKIPPED: n/a on a docs-scale slice - recall/F1 "
            "against the full gold set is only meaningful over the full "
            "corpus; see submission/reports for the full-run eval.")

        # ---- collect -----------------------------------------------------
        mini_outputs = collect_mini_outputs(p3out, run_dir, economies, disclosure)
    except Exception as exc:  # summary still gets written on failure
        ok = False
        _say(f"RUN FAILED: {exc}")
    finally:
        write_run_summary(run_dir, stamp, backend, offline, economies,
                          summary_notes, mini_outputs, work, ok,
                          docs or wants, variant_line, disclosure,
                          curated=not docs_csv)

    if ok:
        _banner([f"{variant_line} complete -> {run_dir}",
                 *(f"  {p.name}" for p in mini_outputs),
                 "  RUN_SUMMARY.md"])
    return 0 if ok else 1


def _stub_dense_leg(index_dir: Path) -> None:
    """Empty dense_top.npz so S2's fusion loop sees a zero-contribution dense
    leg (bm25-only path, no torch / no model download). Work-dir file only.

    The keys mirror whatever the sparse leg just wrote, rather than a list in this file: bm25_top.npz
    keys its arrays from the vendored instrument's automated set ("6.1_idx" today, "P6-I1_idx" on a
    Round 1 index), and a stub keyed differently from the leg it pairs with is a silent
    zero-contribution for the wrong reason.
    """
    import numpy as np  # deliberately lazy: serve mode stays stdlib-only

    sparse = index_dir / "bm25_top.npz"
    if not sparse.is_file():
        raise RuntimeError(f"cannot stub the dense leg: {sparse} does not exist, so there are no "
                           "indicator keys to mirror. Did S1 run?")
    with np.load(sparse) as leg:
        keys = list(leg.keys())
    out = {}
    for key in keys:
        if key.endswith("_idx"):
            out[key] = np.zeros(0, dtype=np.int32)
        elif key.endswith("_score"):
            out[key] = np.zeros(0, dtype=np.float32)
    np.savez_compressed(index_dir / "dense_top.npz", **out)
    _say(f"dense leg stubbed: empty dense_top.npz written to the work index dir, mirroring the "
         f"{len(out)} keys of bm25_top.npz (bm25-only fusion; disclosed in RUN_SUMMARY.md)")


def _retrieval_legs(index_dir: Path, economies: list[str], p3_env: dict,
                    mod: list[str]) -> str:
    """Run S1 with the legs this run's economies actually need, and say which.

    The sparse leg is a whitespace/English tokeniser. Measured on the 27 September index, it
    returns ZERO rows for China and zero for Lao PDR across all nine indicators and all 450,000
    top-K slots, and 4.4% for Timor-Leste against a 24.7% corpus share
    (notes/2026-09-27-sparse-leg-blind-to-cn-la.md, in the mapping workspace).

    So for an English corpus, bm25-only plus an empty dense stub is a fair, disclosed shortcut that
    skips a model download. For any other language it is not a shortcut, it is a wrong answer: the
    run would retrieve nothing and report success. This refuses instead, naming the economy.

    Returns the sentence for RUN_SUMMARY.md.
    """
    blind = economies_needing_dense(economies)
    if not blind:
        run_step("P3 S1 prefilter (bm25 leg only)",
                 mod + ["src.p3map.cli", "prefilter", "--leg", "bm25"], P3, p3_env)
        _stub_dense_leg(index_dir)
        return ("P3 prefilter ran the bm25 leg ONLY (no embedding-model download; CPU-instant). "
                "The wrapper wrote an EMPTY dense_top.npz stub into the run's index dir so S2's "
                "rank fusion runs on the bm25 leg alone - a wrapper-side work-dir artifact, zero "
                "stage changes. Every economy in this run has an English corpus, which is the only "
                "case where the sparse leg alone retrieves anything. The judged full run used both "
                "legs.")

    names = ", ".join(f"{ECON_NAMES.get(e, e)} ({e})" for e in blind)
    _say(f"dense leg REQUIRED for {names}: an English tokeniser returns nothing for a non-English "
         f"corpus, so the bm25-only shortcut would retrieve zero candidates and report success")
    try:
        run_step("P3 S1 prefilter (BOTH legs - non-English corpus in this run)",
                 mod + ["src.p3map.cli", "prefilter", "--leg", "both"], P3, p3_env)
    except RuntimeError as exc:
        _banner([
            "STOPPING: this run needs the dense retrieval leg and it did not complete.",
            f"  economies that need it: {names}",
            f"  the S1 failure: {exc}",
            "",
            "The bm25-only shortcut is NOT available for these economies. Measured on the",
            "27 September index, the sparse leg returns zero rows for China and zero for Lao",
            "PDR, so a stubbed dense leg would produce an empty submission while reporting",
            "success. Refusing is the correct outcome, not a fallback.",
            "",
            "To run these economies: install the embedding stack in stages/p3-map",
            "(sentence-transformers + torch) and allow the BGE-M3 model download, then rerun.",
            "For an English-corpus economy (Australia, Malaysia, Singapore) no dense leg is",
            "needed and this wrapper takes the fast path automatically.",
        ])
        raise
    return (f"P3 prefilter ran BOTH legs because this run covers {names}, whose corpora are not in "
            "English. The sparse leg alone returns zero rows for a non-spaced or non-English "
            "script (measured: zero for China and Lao PDR across all nine indicators), so the "
            "bm25-only shortcut this wrapper uses for English economies would have produced an "
            "empty submission while reporting success.")


def collect_mini_outputs(p3out: Path, run_dir: Path, economies: list[str],
                         disclosure: str) -> list[Path]:
    """Copy records_<E>.* to mini_records_<E>.* with the disclosure label
    stamped on (renamed so they can never be confused with the judged files)."""
    outputs = []
    for econ in economies:
        src_csv = p3out / "submission" / f"records_{econ}.csv"
        src_json = p3out / "submission" / f"records_{econ}.json"
        if not src_csv.is_file():
            _say(f"WARNING: no mini records emitted for {econ} ({src_csv})")
            continue
        dst_csv = run_dir / f"mini_records_{econ}.csv"
        dst_json = run_dir / f"mini_records_{econ}.json"
        body = src_csv.read_text(encoding="utf-8-sig")
        dst_csv.write_text(f"# {disclosure}\n{body}", encoding="utf-8-sig")
        if src_json.is_file():
            data = json.loads(src_json.read_text(encoding="utf-8"))
            stamped = {"disclosure": disclosure}
            stamped.update(data if isinstance(data, dict) else {"laws": data})
            dst_json.write_text(json.dumps(stamped, ensure_ascii=False, indent=2),
                                encoding="utf-8")
        outputs.extend([dst_csv, dst_json])
        _say(f"collected {dst_csv.name} + {dst_json.name}")
    return outputs


def _mini_csv_stats(path: Path) -> dict:
    with path.open(encoding="utf-8-sig", newline="") as f:
        first = f.readline()  # the disclosure comment line
        reader = csv.DictReader(f)
        rows = list(reader)
    tags = [r.get("Discovery Tag", "") for r in rows]
    return {"rows": len(rows), "known": tags.count("KNOWN"),
            "new": tags.count("NEW"),
            "no_provision": sum(1 for t in tags if "No provision" in t or t == ""),
            "columns": len(reader.fieldnames or []),
            "has_label": first.startswith("# DEMONSTRATION")}


def write_run_summary(run_dir: Path, stamp: str, backend: str, offline: bool,
                      economies: list[str], notes: list[str],
                      mini_outputs: list[Path], work: Path, ok: bool,
                      docs: list[dict], variant_line: str, disclosure: str,
                      curated: bool) -> None:
    lines = [
        f"# Demonstration-run summary — {stamp}",
        "",
        f"> **{disclosure}**",
        "",
        "The document slice is **curated, not representative**: each doc was",
        "chosen because it verifiably produced rows in the full judged run"
        + (" (or was explicitly requested via `--docs`)" if not curated else "")
        + ".",
        "Provenance and per-file sha256 evidence: `demo_data/mini_raw/README.md`.",
        "",
        f"- {variant_line}",
        f"- status: {'COMPLETED' if ok else 'FAILED (partial — see stage table)'}",
        f"- mode: {'offline (pre-fetched raw substitution)' if offline else 'live crawl'}",
        f"- economies: {', '.join(economies)}",
        f"- LLM backend: {backend}",
        f"- work dir (all intermediates): `{work}`",
        "",
        "## The slice",
        "",
        "| doc_id | economy | source_type | why |",
        "|---|---|---|---|",
    ]
    for d in docs:
        lines.append(f"| `{d['doc_id']}` | {d.get('economy')} | "
                     f"{d.get('source_type')} | {d.get('why') or ''} |")
    if curated and any(d["doc_id"] == "au-ta1979-002" for d in docs):
        lines += [
            "",
            "5th-doc selection rule (per the mini-run spec): prefer a second html",
            "NEW-row producer — `au-ta1979-002` is the strongest html NEW producer",
            "in the judged records (5 NEW rows in `records_AU`).",
        ]
    lines += [
        "",
        "## Stage timings",
        "",
        "| step | wall-clock (s) | rc |",
        "|---|---:|---:|",
    ]
    for s in _STEPS:
        lines.append(f"| {s['label']} | {s['seconds']} | {s['rc']} |")
    total = round(sum(s["seconds"] for s in _STEPS), 1)
    lines += [f"| **total** | **{total}** | |", ""]

    # ---- measured counts (best-effort harvest from the work artifacts)
    lines += ["## Measured counts", ""]
    try:
        ds = [json.loads(l) for l in
              (work / "handoff2" / "doc_status.jsonl").read_text(
                  encoding="utf-8").splitlines() if l.strip()]
        lines.append("Per-doc extraction (from `work/handoff2/doc_status.jsonl`):")
        lines.append("")
        for d in ds:
            lines.append(f"- `{d['doc_id']}`: status={d.get('status')}, "
                         f"provisions={d.get('n_provisions')}, lane={d.get('lane')}")
        lines.append("")
    except OSError:
        lines.append("- doc_status.jsonl not available (P2 did not complete)")
    try:
        sel = json.loads((work / "p3out" / "select" / "select_report.json"
                          ).read_text(encoding="utf-8"))
        t = sel.get("totals", {})
        rg = sel.get("recall_gate", {})
        lines.append(f"- S2 select: direct pairs={t.get('direct', 0)}, "
                     f"gray pairs={t.get('gray', 0)}; recall gate on this "
                     f"slice: {rg.get('hit', 0)}/{rg.get('resolvable_gold_rows', 0)} "
                     "(most gold laws are outside the slice by construction)")
    except OSError:
        lines.append("- select_report.json not available")
    # per-economy corpus size (projection base for the keyless-rate line)
    econ_provisions: dict[str, int] = {}
    try:
        for l in (work / "handoff2" / "doc_status.jsonl").read_text(
                encoding="utf-8").splitlines():
            if l.strip():
                d = json.loads(l)
                cc = _econ_of_doc_id(d.get("doc_id", "")) or "?"
                econ_provisions[cc] = (econ_provisions.get(cc, 0)
                                       + int(d.get("n_provisions") or 0))
    except OSError:
        pass
    cost_usd = 0.0
    for econ in economies:
        for sub, name, tag in (("map", f"map_report_{econ}.json", "S4 map"),
                               ("verify", f"verify_report_{econ}.json", "S5 verify")):
            try:
                rep = json.loads((work / "p3out" / sub / name
                                  ).read_text(encoding="utf-8"))
                cost_usd += float(rep.get("cost_usd", 0) or 0)
                if sub == "map":
                    lines.append(f"- {tag} {econ}: provisions={rep.get('provisions')}, "
                                 f"fires={rep.get('verdict_fires')}, "
                                 f"ungrounded={rep.get('ungrounded_fires')}, "
                                 f"errors={rep.get('errors')}")
                    done = int(rep.get("provisions") or 0)
                    mins = float(rep.get("elapsed_min") or 0)
                    if keyless() and done > 0 and mins > 0:
                        rate = mins * 60.0 / done
                        total = econ_provisions.get(econ, 0)
                        proj = (f"; PROJECTION (labeled, not measured): "
                                f"~{rate * total / 60:.0f} min for all "
                                f"{total} {econ} provisions at this rate"
                                if total > done else "")
                        lines.append(
                            f"- keyless S4 rate {econ}: measured "
                            f"{rate:.1f} s/provision on the local Ollama "
                            f"fallback{proj}. The keyed stack is the "
                            "production path; keyless proves the fallback "
                            "works, not its speed.")
                else:
                    lines.append(f"- {tag} {econ}: done={rep.get('done')}, "
                                 f"agree={rep.get('agree')}, "
                                 f"tiebreaks={rep.get('tiebreaks')}, "
                                 f"overturned={rep.get('overturned')}")
            except OSError:
                pass
    try:
        p2cost = json.loads((work / "handoff2" / "cost_report.json"
                             ).read_text(encoding="utf-8"))
        est = p2cost.get("estimated_usd")
        lines.append(f"- P2 extraction: records={p2cost.get('records_emitted')}, "
                     f"model={p2cost.get('llm_model')}, est. cost="
                     f"{'$%.4f' % est if isinstance(est, (int, float)) else est}")
        if isinstance(est, (int, float)):
            cost_usd += est
    except OSError:
        pass
    lines.append(f"- measured LLM cost this run (from the stages' own logged "
                 f"token counts): ${cost_usd:.2f}"
                 + (" (keyless local models -> $0)" if keyless() else ""))
    lines.append("")

    if mini_outputs:
        lines += ["## Mini outputs", ""]
        for p in mini_outputs:
            if p.suffix == ".csv" and p.is_file():
                st = _mini_csv_stats(p)
                lines.append(f"- `{p.name}`: {st['rows']} rows "
                             f"({st['known']} KNOWN, {st['new']} NEW, "
                             f"{st['no_provision']} no-provision), "
                             f"{st['columns']} columns, disclosure label: "
                             f"{'present' if st['has_label'] else 'MISSING'}")
        lines.append("")

    lines += ["## Disclosures & deviations", ""]
    for n in notes:
        lines.append(f"- {n}")
    lines += [
        "",
        "*Generated by `main.py`. The judged records live in `submission/`; "
        "every number above is measured from this run's own artifacts under "
        "the work dir.*",
    ]
    (run_dir / "RUN_SUMMARY.md").write_text("\n".join(lines) + "\n",
                                            encoding="utf-8")
    _say(f"wrote {run_dir / 'RUN_SUMMARY.md'}")


# --------------------------------------------------------------------- demo --

def cmd_demo() -> int:
    stamp = _ts()
    run_dir = OUTPUTS / f"demo_{stamp}"
    h1, h2 = run_dir / "work" / "handoff1", run_dir / "work" / "handoff2"
    _banner(["Scanned-PDF demo: my-cma1998-001 (Communications and Multimedia "
             "Act 1998, 144-page scan)",
             "Live gold-page CER measurement first, then the full extraction",
             "pipeline over the scan (records inherit the measured CER)."])
    announce_backend()
    if not tesseract_available():
        _banner(["Tesseract OCR is REQUIRED for the demo and was not found.",
                 "Install it, then re-run:",
                 "    winget install UB-Mannheim.TesseractOCR"])
        return 1
    stage_offline_handoff1(h1)
    rc = run_step(
        "p2-extract demo (gold-page CER + full pipeline on the scan)",
        [sys.executable, "-m", "rdtii_p2.cli", "demo", "--doc", "my-cma1998-001",
         "--manifest", str(h1 / "manifest.csv"), "--raw", str(h1),
         "--out", str(h2)],
        cwd=P2, env=_base_env(), check=False)
    if rc == 0:
        _say(f"demo complete - grounded records: {h2 / 'provisions.jsonl'}")
        _say(f"CER report: {h2 / 'ocr' / 'my-cma1998-001' / 'cer_report.json'}")
    else:
        _say(f"demo exited rc={rc} (nonzero = CER missed the <5% bar or the "
             "doc failed; the stage output above has the measurement)")
    return rc


# ------------------------------------------------------------ full-pipeline --

def cmd_full_pipeline() -> int:
    print(f"""\
[main] --full-pipeline prints the real per-stage commands and executes NOTHING.
       Honesty over theater: the full corpus run takes hours and real API spend;
       it is not something a wrapper should silently kick off.

  Corpus + heavy-data logistics (what each mode needs, Release assets,
  regeneration paths): docs/DATA.md

  P0  instrument gates          (cwd stages/p0-instrument)
      python scripts/validate_instrument.py

  P1  full crawl, ~6-8 h politeness-limited   (cwd stages/p1-scrape)
      pip install -r requirements.txt && python -m playwright install chromium
      python scrape.py --all --pillars 6,7 --out handoff1
      python scrape.py --validate handoff1/manifest.csv

  P2  extraction -> Hand-off #2               (cwd stages/p2-extract)
      pip install -e .          (plus Tesseract 5 for the scanned lane)
      p2-extract run --manifest <handoff1>/manifest.csv --raw <handoff1> \\
                     --out <handoff2> --skip-tags
      p2-extract tag-corpus --out <handoff2>       (Batches API; needs a key)
      p2-extract validate --provisions <handoff2>/provisions.jsonl \\
                          --manifest <handoff1>/manifest.csv

  P3  mapping S0..S10                         (cwd stages/p3-map)
      pip install -r requirements.txt
      env: HANDOFF2_DIR, MANIFEST_PATH, OUT_DIR (see config/settings.py)
      python -m src.p3map.cli ingest
      python -m src.p3map.cli prefilter            (both legs; the dense leg
                                                    needs sentence-transformers
                                                    + torch - CPU wheel:
                                                    pip install torch --index-url
                                                    https://download.pytorch.org/whl/cpu)
      python -m src.p3map.cli select
      python -m src.p3map.triage.haiku
      python -m src.p3map.mapping.runner <SG|MY|AU>
      python -m src.p3map.chain <SG|MY|AU>         (S5 verify -> S7 new/known ->
                                                    S6 rollup -> S9 emit ->
                                                    S10 eval -> workbook + audit)

  REAL but small end-to-end alternatives that run on this machine:
      python main.py --mini-run --offline          (5 docs, full scanned OCR)
      python main.py --quick                       (2 docs, live fetch + CER pilot)
""")
    return 0


# --------------------------------------------------------------------- main --

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="main.py",
        description="RDTII Rocky - serve the judged results, run the demo, "
                    "or drive the demonstration pipeline slices.")
    ap.add_argument("--economy", help="SG|MY|AU, full name, case-insensitive "
                                      "(comma-separated for --mini-run)")
    ap.add_argument("--pillar", type=int, choices=[6, 7],
                    help="pillar filter for serve mode")
    ap.add_argument("--demo", action="store_true",
                    help="scanned-PDF walkthrough (live gold-page CER)")
    ap.add_argument("--mini-run", action="store_true", dest="mini_run",
                    help="real 5-doc end-to-end slice (P1 -> P2 -> P3)")
    ap.add_argument("--quick", action="store_true",
                    help="live-pitch slice: smoke proof + 2 live-fetched laws "
                         "+ gold-page CER pilot + the same P2 -> P3 chain. "
                         "5-10 min assumes the KEYED stack; keyless completes "
                         "on local Ollama at a much slower measured rate "
                         "(disclosed in RUN_SUMMARY.md)")
    ap.add_argument("--map-limit", type=int, dest="map_limit",
                    help="cap S4 mapping at N provisions per economy "
                         "(mechanics proof; the capped mini-CSV is labeled)")
    ap.add_argument("--docs", help="comma-separated doc_ids overriding the "
                                   "curated slice (with --mini-run/--quick)")
    ap.add_argument("--offline", action="store_true",
                    help="with --mini-run/--quick: substitute the live crawl "
                         "with demo_data/mini_raw/")
    ap.add_argument("--full-pipeline", action="store_true", dest="full_pipeline",
                    help="print the full-corpus per-stage commands (no execution)")
    args = ap.parse_args(argv)

    if args.full_pipeline:
        return cmd_full_pipeline()
    if args.demo:
        return cmd_demo()
    if args.mini_run and args.quick:
        ap.error("--mini-run and --quick are mutually exclusive")
    if args.mini_run or args.quick:
        return cmd_pipeline_slice(
            offline=args.offline, economy_raw=args.economy,
            variant="quick" if args.quick else "mini", docs_csv=args.docs,
            map_limit=args.map_limit)
    if args.docs:
        ap.error("--docs only applies to --mini-run / --quick")
    if args.offline:
        ap.error("--offline only applies to --mini-run / --quick")
    if args.map_limit:
        ap.error("--map-limit only applies to --mini-run / --quick")
    if not args.economy or args.pillar is None:
        ap.print_help()
        print("\nserve mode needs both --economy and --pillar, e.g.:\n"
              "    python main.py --economy Singapore --pillar 6")
        return 2
    return cmd_serve(args.economy, args.pillar)


if __name__ == "__main__":
    sys.exit(main())
