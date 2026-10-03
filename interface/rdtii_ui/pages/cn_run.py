"""China from the Scraping tab.

The crawler engine has no China adapter, on purpose: the national database forbids automated collection. The
publishers that permit us, CAC and gov.cn first, are read by the China tools in adapters/cn_npc (collect.py,
update.py), which the page runs as a job of their own with the crawler's interpreter. Their output is a folder of
raw files with a provenance sheet, which Extraction lists as an input with the economy fixed to China. The national
database, MIIT and Customs stay by hand whatever the page does.

The tools find their data root through HANDOFF1_DIR (the folder that holds CN/); the page points that at a fresh
run folder under the runs root, stages the shipped collection's index files there for the update check (never the
bytes), and lets the tools write beside them. Nothing under stages/ is written.
"""
from __future__ import annotations

import csv
import re
import shutil
import time
from collections import Counter
from pathlib import Path

from ..envbuild import ChoiceError, build_env
from ..jobs import Job, Step
from ..server import ApiError, App, rel_or_abs
from ..settings import REPO, Settings

BASELINE = "CN_sources_2026-09-21"      # the shipped collection the tools compare against and write beside
MODES = {
    "update": "Update check: what changed at CAC and gov.cn since the shipped collection",
    "collect": "Collect the ticked publishers",
}
# Layer 1 is the national database; layer 2 the publishers the laws delegate to. `mode` says who reads it: the
# China tools, or a person. `src` is the collect tool's source name (gov.cn's verified links are its `links`).
PUBLISHERS = [
    {"name": "National database 国家法律法规数据库", "root": "https://flk.npc.gov.cn", "src": "npc-database", "layer": 1, "mode": "hand",
     "what": "every law and regulation in force, consolidated, with status",
     "run": "forbids automated tools in its robots.txt: the export is downloaded by hand, about five minutes; the update check compares two exports offline"},
    {"name": "CAC 国家互联网信息办公室", "root": "https://www.cac.gov.cn", "src": "cac", "layer": 2, "mode": "tools",
     "what": "the operative rules of pillars 6 and 7", "run": "a collection takes its whole rules index, six listing requests; the update check re-reads it and fetches what is new"},
    {"name": "gov.cn 中国政府网", "root": "https://www.gov.cn", "src": "links", "layer": 2, "mode": "tools",
     "what": "permitted official copies, the verified links", "run": "a collection takes the verified links; the update check re-reads the copies held and compares their text"},
    {"name": "MIIT 工业和信息化部", "root": "https://www.miit.gov.cn", "src": "miit", "layer": 2, "mode": "hand",
     "what": "the telecom catalogue and licensing rules", "run": "refuses an automated client: saved by hand; the worklist tool lists the pages to open"},
    {"name": "Customs 海关总署", "root": "https://www.customs.gov.cn", "src": "customs", "layer": 2, "mode": "hand",
     "what": "e-commerce supervision modes and lists", "run": "refuses an automated client: saved by hand"},
    {"name": "SAMR 国家市场监督管理总局", "root": "https://www.samr.gov.cn", "src": "samr", "layer": 2, "mode": "tools",
     "what": "market regulation rules", "run": "a collection takes its whole rules section; collected once, then set aside on 2026-09-22, and a run continues it there"},
    {"name": "MOFCOM 商务部", "root": "https://www.mofcom.gov.cn", "src": "mofcom", "layer": 2, "mode": "tools",
     "what": "commerce rules in force", "run": "a collection takes its rules library; collected once, then set aside on 2026-09-22, and a run continues it there"},
    {"name": "OSCCA 国家密码管理局", "root": "https://www.oscca.gov.cn", "src": "oscca", "layer": 2, "mode": "tools",
     "what": "cryptography rules", "run": "a collection takes its two sections whole; collected once, then set aside on 2026-09-22, and a run continues it there"},
]
SET_ASIDE_ON = "2026-09-22"
SELECTABLE = [p["src"] for p in PUBLISHERS if p["mode"] == "tools"]
NAMES = {p["src"]: p["name"].split(" ")[0] for p in PUBLISHERS}
NAMES.update({"cnca": "CNCA", "mof-tariff": "MOF tariff", "sectoral": "sectoral publishers", "gazette": "gazette index"})
TOOLS_NOTE = ("Not crawled by the engine: the national database forbids automated tools. The China tools read the "
              "publishers above from this page. Grey cards were listed by the tools but never taken into Extraction, so "
              "they are not in the corpus. The rest is collected by hand.")
INDEX_FILES = ("list.csv", "provenance.tsv", "manifest.json", "README.md", "run_log.jsonl", "index.csv")
SUFFIX = {".pdf": "pdf", ".html": "html", ".htm": "html", ".docx": "docx", ".doc": "doc"}


def tools_dir(s: Settings) -> Path:
    return s.stage_dirs["p1"] / "src" / "p1_scrape" / "adapters" / "cn_npc"


def shipped_cn(s: Settings) -> Path:
    return s.stage_dirs["p1"] / "handoff1" / "CN"


def present(s: Settings) -> bool:
    return (tools_dir(s) / "collect.py").is_file() and (tools_dir(s) / "update.py").is_file()


def held_counts(s: Settings) -> dict[str, int]:
    """Documents held from each source in the active part of the shipped collection."""
    base = shipped_cn(s) / BASELINE
    out: dict[str, int] = {}
    for p in PUBLISHERS:
        folder = {"links": "govcn"}.get(p["src"], p["src"])
        if p["src"] == "npc-database":
            out[p["src"]] = len(_read(base / "manual" / "npc-database" / "index.csv"))
        elif p["mode"] == "hand":
            out[p["src"]] = len(_read(base / "manual" / folder / "provenance.tsv", "\t"))
        else:
            out[p["src"]] = len(_read(base / "auto" / folder / "list.csv"))
    return out


def set_aside_counts(s: Settings) -> dict[str, int]:
    """Documents listed from each source in the collection's _deferred part: collected, then set aside, not deleted."""
    base = shipped_cn(s) / BASELINE / "_deferred" / "auto"
    out: dict[str, int] = {}
    if base.is_dir():
        for folder in sorted(base.iterdir()):
            n = len(_read(folder / "list.csv"))
            if n:
                out[folder.name] = n
    return out


def portals(s: Settings | None = None) -> list[dict]:
    """China's sources by layer: who reads each, what a run fetches there, how many documents we hold from it."""
    held = held_counts(s) if s is not None else {}
    aside = set_aside_counts(s) if s is not None else {}
    return [{"name": p["name"], "root": p["root"], "kind": "china_tools", "crawled": True, "note": p["what"],
             "run": p["run"], "held": held.get(p["src"], 0), "set_aside": aside.get(p["src"], 0), "set_aside_on": SET_ASIDE_ON,
             "layer": p["layer"], "mode": p["mode"], "src": p["src"],
             "selectable": p["mode"] == "tools", "deferred": p["mode"] == "tools" and not held.get(p["src"], 0)}
            for p in PUBLISHERS]


def norm_mode(req: dict) -> tuple[str, list[str]]:
    """(mode, sources): update, or collect with the ticked publishers. The older collect_cac and collect_all still work."""
    mode = str(req.get("cn_mode") or "update")
    if mode == "collect_cac":
        return "collect", ["cac"]
    if mode == "collect_all":
        return "collect", list(SELECTABLE)
    if mode == "update":
        return "update", []
    if mode != "collect":
        raise ApiError(400, "cn_mode must be update or collect")
    sources = [str(x) for x in (req.get("cn_sources") or []) if str(x) in SELECTABLE]
    if not sources:
        raise ApiError(400, "tick at least one publisher the China tools may read")
    return "collect", [src for src in SELECTABLE if src in sources]


# ---- the run folder ------------------------------------------------------------------------------------

def stage_links(s: Settings, data: Path) -> int:
    """The verified-links list the collect tool reads for its `links` sources."""
    links = shipped_cn(s) / "CN_layer2_links.md"
    (data / "CN").mkdir(parents=True, exist_ok=True)
    if links.is_file():
        shutil.copy2(links, data / "CN" / links.name)
        return 1
    return 0


def stage_baseline(s: Settings, data: Path) -> int:
    """Copy the shipped collection's index files under data/CN, never the bytes, so the update check has its baseline."""
    src = shipped_cn(s) / BASELINE
    if not src.is_dir():
        return 0
    n = 0
    for p in src.rglob("*"):
        if p.is_file() and (p.name in INDEX_FILES or (p.suffix == ".md" and p.parent == src)):
            dest = data / "CN" / p.relative_to(shipped_cn(s))
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, dest)
            n += 1
    return n + stage_links(s, data)


def is_run(p: Path) -> bool:
    return (p / "data" / "CN").is_dir()


def raw_files(run_dir: Path) -> list[Path]:
    """Every document a China tools run fetched: the files inside any raw/ folder under the run."""
    return [p for p in run_dir.rglob("*") if p.is_file() and "raw" in p.relative_to(run_dir).parts and p.suffix.lower() in SUFFIX]


def source_folders(run_dir: Path) -> list[Path]:
    """The folders that hold a raw/ of fetched documents (auto/cac and the like), each an Extraction input."""
    seen: dict[Path, None] = {}
    for p in raw_files(run_dir):
        parts = p.relative_to(run_dir).parts
        i = parts.index("raw")
        seen.setdefault(run_dir.joinpath(*parts[:i]), None)
    return list(seen)


def describe_run(run_dir: Path) -> dict:
    files = raw_files(run_dir)
    by_src = Counter(p.relative_to(run_dir).parts[p.relative_to(run_dir).parts.index("raw") - 1] for p in files)
    return {"path": str(run_dir), "id": rel_or_abs(run_dir, REPO), "name": run_dir.name, "manifest": False,
            "rows": len(files), "by_economy": {"CN": len(files)} if files else {},
            "by_source_type": dict(Counter(SUFFIX[p.suffix.lower()] for p in files)),
            "raw_checked": len(files), "raw_present": len(files), "law_table": False,
            "fetched_last_pass": len(files) if files else None, "crawl_state": None,
            "kind": "China tools run", "cn_sources": dict(by_src)}


# ---- check and plan ------------------------------------------------------------------------------------

def precheck_cn(app: App, req: dict) -> list[dict]:
    s = app.settings
    out: list[dict] = []

    def add(level: str, check: str, text: str) -> None:
        out.append({"level": level, "check": check, "text": "China: " + text, "ok": level != "fail"})

    if not present(s):
        add("fail", "cn_tools", "the China tools (adapters/cn_npc) are not in this repository.")
        return out
    try:
        mode, sources = norm_mode(req)
    except ApiError as e:
        add("fail", "cn_mode", e.message)
        return out
    dry = bool(req.get("dry_run"))
    add("ok", "cn_tools", "the China tools are present; they read only the hosts that permit us, one request every 6 to 12 s.")
    picked = ", ".join(NAMES[x] for x in sources)
    add("ok", "cn_mode", (MODES[mode] + (f": {picked}" if sources else "")) + ("; dry run, lists and fetches nothing" if dry else "") + ".")
    if mode == "update":
        if (shipped_cn(s) / BASELINE / "auto" / "cac" / "list.csv").is_file():
            add("ok", "cn_baseline", f"compared against the shipped collection {BASELINE}; its index files are staged into the run folder.")
        else:
            add("fail", "cn_baseline", f"the shipped collection {BASELINE} has no CAC index to compare against.")
        if not dry:
            add("ok", "cn_fetch", "new CAC documents are fetched into the run folder; the gov.cn copies are compared by text.")
    elif sources == ["cac"]:
        add("ok", "cn_scope", "a full collection of the CAC index takes about 12 minutes.")
    else:
        add("warn", "cn_scope", f"{len(sources)} publishers at one request every 6 to 12 s: expect an hour or more.")
    add("ok", "cn_hand", "the national database, MIIT and Customs stay by hand; the China page lists what to check.")
    add("ok", "cn_output", f"writes to {rel_or_abs(s.runs_root / 'scrape', REPO)}/CN/china-tools/<time>, a new folder; the documents then appear in 2 Extraction → Input.")
    return out


def _refusal_note(job: Job, code: int) -> None:
    if code == 2:
        job.say("A host refused the tool, so this check is incomplete; the lines above say which.")


def plan_cn(app: App, req: dict) -> Job:
    s = app.settings
    if not present(s):
        raise ApiError(409, "the China tools are not in this repository")
    mode, sources = norm_mode(req)
    dry = bool(req.get("dry_run"))
    from .. import sources as filed        # `sources` below is the list of publishers this run reads
    run_dir = filed.scrape_run_dir(s, "CN", filed.CHINA_TOOLS, time.strftime("%Y%m%d-%H%M%S"))
    data = run_dir / "data"
    (data / "CN").mkdir(parents=True, exist_ok=True)
    staged = stage_baseline(s, data) if mode == "update" else stage_links(s, data)
    try:
        env, public = build_env("p1", app.engines, app.key, {}, extra={"HANDOFF1_DIR": str(data), "PYTHONPATH": "src"}, with_engine=False)
    except ChoiceError as e:
        raise ApiError(400, str(e)) from None
    py = s.python_for("p1")
    verb = "list" if dry else "collect"
    if mode == "update":
        steps = [Step(label="update check: re-read the CAC index and the gov.cn copies" + ("" if dry else ", fetch what is new"),
                      cwd=tools_dir(s), env=env, parse=parse_cn, ok_codes=(0, 2), on_done=_refusal_note,
                      argv=[py, "update.py", "--base", BASELINE] + ([] if dry else ["--fetch"]))]
        title = "China: Update check"
    elif sources == list(SELECTABLE):
        steps = [Step(label=f"{verb} every publisher the tools may read: " + ", ".join(NAMES[x] for x in sources),
                      cwd=tools_dir(s), env=env, parse=parse_cn, ok_codes=(0, 2), on_done=_refusal_note,
                      argv=[py, "collect.py", "all"] + (["--list-only"] if dry else []))]
        title = "China: Collect every publisher"
    else:
        steps = [Step(label=f"{verb} {NAMES[src]}" + (", its whole rules index" if src == "cac" else ", the verified links" if src == "links" else ""),
                      cwd=tools_dir(s), env=env, parse=parse_cn, ok_codes=(0, 2), on_done=_refusal_note,
                      argv=[py, "collect.py", src] + (["--list-only"] if dry else [])) for src in sources]
        title = "China: Collect " + ", ".join(NAMES[x] for x in sources)
    job = Job(stage="p1", title=title + (" (dry run)" if dry else ""), steps=steps,
              out_dir=run_dir, env_public=public, redact=app.key.redact)
    job.say(f"Run folder {rel_or_abs(run_dir, REPO)}; the tools read only the hosts that permit us, one request every 6 to 12 s."
            + (f" Staged {staged} index file(s) of {BASELINE} to compare against." if staged else ""))
    job.say("The national database, MIIT and Customs stay by hand; the China page lists what to check.")
    return job


# ---- the tools' prints, in plain words ---------------------------------------------------------------

CN_RULES: list[tuple[re.Pattern, object]] = [
    (re.compile(r"^\s*(\d+)/(\d+)\s+REFUSED\s*(.*)$"), lambda m, j: (f"Refused by the host at document {m[1]} of {m[2]}.", {"+failed": 1})),
    (re.compile(r"^\s*(\d+)/(\d+)\s+(HTTP \d+|\S+)\s+(?:\d+c\s+)?(.*)$"),
     lambda m, j: (f"Fetched {m[1]} of {m[2]}: {m[4].strip()[:60]}", {"done": int(m[1]), "total": int(m[2]), "unit": "documents"})),
    (re.compile(r"^\s*(\d+) listed now; (\d+) new, (\d+) gone, (\d+) retitled"),
     lambda m, j: (f"CAC lists {m[1]} documents now: {m[2]} new, {m[3]} gone, {m[4]} retitled.", None)),
    (re.compile(r"^\[(\w[\w-]*)\] (\d+) documents listed"), lambda m, j: (f"{m[1]}: {m[2]} documents listed.", {"total": int(m[2]), "done": 0, "unit": "documents"})),
    (re.compile(r"^\[(layer 1|CAC|gov\.cn)\] (.*)$"), lambda m, j: (f"{m[1]}: {m[2].strip()}.", None)),
    (re.compile(r"CHECK BY HAND — (\d+) sources"), lambda m, j: (f"{m[1]} sources remain to check by hand; the China page lists them.", None)),
    (re.compile(r"^written: (.*)$"), lambda m, j: (f"Written: {m[1].strip()}", None)),
    (re.compile(r"^\s*robots\s+(\S+)\s+(.*)$"), lambda m, j: (f"robots.txt {m[1]}: {m[2].strip()}", None)),
    (re.compile(r"REFUSED: (.*)"), lambda m, j: (f"Refused: {m[1].strip()[:120]}", None)),
    (re.compile(r"^===== summary"), lambda m, j: ("Summary follows.", None)),
    # the tool prints every watch-list row (age, kind, name, address); the page keeps the one-line count above
    (re.compile(r"https?://\S+"), lambda m, j: None),
]


def parse_cn(line: str, job: Job):
    for rx, fn in CN_RULES:
        m = rx.search(line)
        if m:
            return fn(m, job)
    text = line.strip()
    if not text or text.startswith("="):
        return None
    return (text[:160], None)


# ---- the documents the shipped collection lists --------------------------------------------------------

SCOPES = [{"id": "all", "label": "All"}, {"id": "layer1", "label": "Layer 1: national database"},
          {"id": "layer2", "label": "Layer 2: publishers"}]


def _read(path: Path, delimiter: str = ",") -> list[dict]:
    if not path.is_file():
        return []
    with open(path, encoding="utf-8-sig", newline="") as f:
        return [dict(r) for r in csv.DictReader(f, delimiter=delimiter)]


def list_documents(s: Settings, scope: str = "all") -> dict:
    """Every document the shipped China collection holds or lists: the national database export (by hand), CAC and
    gov.cn (crawled by the China tools), MIIT and Customs (by hand). No link list exists for China; this is it."""
    base = shipped_cn(s) / BASELINE
    rows: list[dict] = []

    def add(title, number, url, kind, status, version, layer):
        rows.append({"order": len(rows) + 1, "law_name": (title or "").strip(), "law_number": (number or "").strip(),
                     "url": (url or "").strip(), "kind": kind, "indicators": "", "language": "zho",
                     "status": status, "scopes": ["all", layer], "version": (version or "").strip()})

    for r in _read(base / "manual" / "npc-database" / "index.csv"):
        add(r.get("title"), "", "", f"national database: {r.get('kind') or 'document'}", "held, downloaded by hand", r.get("version_date"), "layer1")
    for r in _read(base / "auto" / "cac" / "list.csv"):
        add(r.get("title"), "", r.get("url"), f"CAC: {r.get('section') or 'index'}", "crawled by the China tools", r.get("date"), "layer2")
    for r in _read(base / "auto" / "govcn" / "list.csv"):
        add(r.get("title"), r.get("reference"), r.get("url"), "gov.cn: verified copy", "crawled by the China tools", r.get("date"), "layer2")
    for src, label in (("miit", "MIIT"), ("customs", "Customs")):
        for r in _read(base / "manual" / src / "provenance.tsv", "\t"):
            add(r.get("title"), r.get("reference"), r.get("url"), f"{label}: by hand", "held, saved by hand",
                r.get("version_date_on_document") or r.get("stated_in_force"), "layer2")
    counts = {sc["id"]: sum(1 for r in rows if sc["id"] in r["scopes"]) for sc in SCOPES}
    out = [r for r in rows if scope in r["scopes"]]
    return {"economy": "CN", "scope": scope, "total": len(out), "counts": counts, "documents": out, "scopes": SCOPES,
            "file": rel_or_abs(base, REPO)}


def collection_facts(s: Settings) -> dict:
    """The counts the China card shows in place of a link list's All and Sample."""
    d = list_documents(s, "all")
    aside = set_aside_counts(s)
    by_kind = Counter(r["kind"].split(":")[0] for r in d["documents"])
    kinds = " · ".join(f"{k} {v}" for k, v in by_kind.most_common() if k != "national database")
    return {"counts": d["counts"], "document_kinds": dict(by_kind), "catalogued_at": BASELINE[-10:],
            "facts": [["All", f"{d['counts']['all']} documents in the active collection"],
                      ["Layer 1", f"{d['counts']['layer1']} in the national database export, downloaded by hand"],
                      ["Layer 2", f"{d['counts']['layer2']} from the publishers: {kinds}"],
                      ["Set aside", (f"{sum(aside.values())} more listed on {BASELINE[-10:]} from " + " · ".join(f"{NAMES.get(k, k)} {v}" for k, v in aside.items())
                                     + f"; set aside on {SET_ASIDE_ON}, kept, not in the corpus") if aside else "none"],
                      ["Collected", BASELINE[-10:] + "; a run from this page writes a new folder beside it, never into it"]],
            "holdings_label": "What we hold today", "holdings_sub": "(9.30 Finale Submission)",
            "doclist_label": "in the shipped collection", "scope_hint": "by layer, with a filter"}
