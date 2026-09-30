"""Build a corpus folder from the runs of one country: the latest full crawl plus every update since, merged.

    python tools/merge_corpus.py --outputs <ws>/outputs/MY --out <ws>/outputs/MY/MY_corpus_<date> [--economy MY]
        [--hardlink] [--exclude-flags repeal_notice,other_act_text]

A run folder holds only what that run fetched (outputs/README.md), so nothing on disk is "the current text of every
law" until the runs are merged. This tool never writes into a run: it creates a new folder in the Hand-off #1 shape
(manifest.csv, manifest.jsonl, raw/) that extraction and mapping can read, plus the record of where each document
came from and which older copies it replaced. Decision 17.

How a law is identified across runs: by the link list's portal_id and document_kind (contract_meta in
links_*/documents.jsonl); a document with no link row is identified by its URL; a row with the same URL, or the
same doc_id for the same law (an older run's list may lack the portal_id), or the same bytes as an included row is
the same document. The newest run's document wins; the older copies are listed in superseded.jsonl, with what they
matched on, and not copied. A row left out by --exclude-flags still claims its law, so an older copy does not come
back in its place. Two runs can mint the same doc_id for different documents (the engine's id map starts fresh per
run): the older run keeps the id and the newer row gets the next free suffix, recorded in the note. URLs the engine logged as duplicates are not
documents. Audit flags (tools/audit_run.py, audit.json in each run) travel with the rows as content_flags; rows
carrying a flag named in --exclude-flags are left out and listed in the note.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

RUN_DIR = re.compile(r"^(?P<cc>[A-Z]{2})_ws_(?P<date>\d{4}-\d{2}-\d{2})(?:_to_(?P<to>\d{4}-\d{2}-\d{2}))?(?:_(?P<n>\d+))?$")
LIST_DIRS = ("links_rebuilt", "links_used", "links")


def run_started(path: Path) -> str:
    """When the run's crawl started (crawl_status.json), else when its list was written; '' when unknown."""
    for rel, key in (("crawl_status.json", "started_at"), ("links_used/catalogue_meta.json", "generated_at")):
        p = path / rel
        if p.is_file():
            try:
                return str(json.loads(p.read_text(encoding="utf-8")).get(key) or "")
            except (OSError, ValueError):
                return ""
    return ""


def run_sort_key(path: Path) -> tuple:
    """Newest last: by end date, then by the time the run started (a check named _to_<D> and a crawl dated D
    are ordered by when they ran), then a check after a crawl, then the same-day suffix."""
    m = RUN_DIR.match(path.name)
    if not m:
        return ("", "", 0, 0)
    return (m.group("to") or m.group("date"), run_started(path), 1 if m.group("to") else 0, int(m.group("n") or 1))


def list_runs(outputs: Path, economy: str) -> list[Path]:
    """Run folders that crawled (a manifest), newest first."""
    runs = [p for p in outputs.iterdir() if p.is_dir() and RUN_DIR.match(p.name)
            and RUN_DIR.match(p.name).group("cc") == economy.upper() and (p / "manifest.jsonl").is_file()]
    return sorted(runs, key=run_sort_key, reverse=True)


def guess_economy(outputs: Path) -> Optional[str]:
    """The country code: the folder's name when it is one (outputs/MY), else the one code its run folders share."""
    if re.fullmatch(r"[A-Z]{2}", outputs.name):
        return outputs.name
    codes = {RUN_DIR.match(p.name).group("cc") for p in outputs.iterdir() if p.is_dir() and RUN_DIR.match(p.name)}
    return codes.pop() if len(codes) == 1 else None


def _jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def list_dir(run: Path) -> Optional[Path]:
    for name in LIST_DIRS:
        if (run / name / "documents.jsonl").is_file() or (run / name / "laws.csv").is_file():
            return run / name
    return None


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def identity(row: dict, link: Optional[dict]) -> tuple:
    meta = (link or {}).get("contract_meta") or {}
    if meta.get("portal_id") and meta.get("document_kind"):
        return ("law", str(meta["portal_id"]), meta["document_kind"])
    return ("url", row["source_url"])


#: how long a law's folder may be inside the corpus. A corpus path is a few characters longer than the run path it
#: comes from (`TL_corpus_2026-09-20` against `TL_ws_2026-09-20`), so a folder that just fitted in the run can
#: overflow Windows' 260-character limit here. Timor-Leste's Portuguese titles hit this on 2026-09-20.
FOLDER_MAX = 80


def _short(rel: str) -> str:
    """The same path with any over-long folder capped, keeping a hash so two long names cannot collide."""
    parts = Path(rel).parts
    out = []
    for part in parts:
        if len(part) > FOLDER_MAX and "." not in part:            # a folder, not a file name
            part = part[:FOLDER_MAX - 9].rstrip("_") + "_" + hashlib.sha256(part.encode()).hexdigest()[:8]
        out.append(part)
    return str(Path(*out)).replace("\\", "/")


def place_file(src: Path, rel: str, run: Path, out: Path, hardlink: bool) -> str:
    """Copy (or hard-link) src into the corpus at rel; on a name clash with different bytes, under raw/<run>/."""
    rel = _short(rel)
    dest = out / rel
    if dest.exists():
        if sha256_of(dest) == sha256_of(src):
            return rel
        rel = str(Path("raw") / run.name / Path(rel).relative_to("raw")).replace("\\", "/") if rel.startswith("raw/") \
            else f"raw/{run.name}/{rel}"
        dest = out / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    if hardlink:
        try:
            os.link(src, dest)
            return rel
        except OSError:
            pass
    shutil.copy2(src, dest)
    return rel


ACT_NUMBER = re.compile(r"^act a?\d{1,4}$")


def same_law(a: dict, b: dict) -> bool:
    """Two manifest rows describe the same law when their act numbers agree ("Act 709", "Act A1727"); a number that
    is not an act number ("P.U.(A) 2024" names several instruments) must agree together with the name."""
    na, nb = (a.get("law_number_guess") or "").strip().lower(), (b.get("law_number_guess") or "").strip().lower()
    names = (a.get("law_name_guess") or "").strip().lower() == (b.get("law_name_guess") or "").strip().lower()
    if na and nb:
        return na == nb and (names or ACT_NUMBER.match(na) is not None)
    return names


def merge(outputs: Path, out: Path, economy: str, hardlink: bool = False,
          exclude_flags: tuple[str, ...] = ()) -> dict[str, Any]:
    from p1_scrape.manifest import validate_manifest, write_manifest
    from p1_scrape.models import MANIFEST_FIELDS

    runs = list_runs(outputs, economy)
    if not runs:
        raise FileNotFoundError(f"no {economy}_ws_<date> run with a manifest.jsonl under {outputs}")
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"{out} exists and is not empty: a corpus is never written into an existing folder")
    out.mkdir(parents=True, exist_ok=True)
    corpus_name = out.name

    # pass 1: which row of each law is kept, newest run first
    seen: dict[tuple, dict] = {}            # by law identity (portal_id + kind, else URL)
    seen_urls: dict[str, dict] = {}         # by URL: the same address is the same document whatever the list said
    seen_ids: dict[str, list[dict]] = {}    # by doc_id, counted only for the same law (an older list may lack the portal_id)
    seen_sha: dict[str, dict] = {}          # by content: the same bytes twice fail validation, so the newest copy stays
    included: list[dict] = []
    superseded: list[dict] = []
    excluded: list[dict] = []
    per_run: dict[str, dict[str, int]] = {}
    duplicates: set[str] = set()
    for run in runs:
        for e in _jsonl(run / "crawl_log.jsonl"):
            if e.get("outcome") == "duplicate" and e.get("url"):
                duplicates.add(e["url"])
    for run in runs:
        d = list_dir(run)
        links = {r["url"]: r for r in _jsonl(d / "documents.jsonl")} if d else {}
        audit = {r["doc_id"]: r for r in (json.loads((run / "audit.json").read_text(encoding="utf-8")).get("rows", [])
                                          if (run / "audit.json").is_file() else [])}
        stats = per_run.setdefault(run.name, {"documents": 0, "included": 0, "superseded": 0, "excluded": 0, "renamed": 0})
        for m in _jsonl(run / "manifest.jsonl"):
            stats["documents"] += 1
            link = links.get(m["source_url"])
            key = identity(m, link)
            flags = list((audit.get(m["doc_id"]) or {}).get("flags") or [])
            entry = {"doc_id": m["doc_id"], "doc_id_in_run": m["doc_id"], "run": run.name, "url": m["source_url"],
                     "content_sha256": m.get("content_sha256"), "law_number": m.get("law_number_guess"),
                     "law_name": m.get("law_name_guess"), "flags": flags, "row": m, "link": link, "key": key, "path": run}
            prior, matched = None, None
            if key in seen:
                prior, matched = seen[key], key[0]
            elif m["source_url"] in seen_urls:
                prior, matched = seen_urls[m["source_url"]], "url"
            elif any(same_law(m, e["row"]) for e in seen_ids.get(m["doc_id"], [])):
                prior, matched = next(e for e in seen_ids[m["doc_id"]] if same_law(m, e["row"])), "doc_id"
            elif m.get("content_sha256") and m["content_sha256"] in seen_sha:
                prior, matched = seen_sha[m["content_sha256"]], "content"
            public = {k: entry[k] for k in ("doc_id", "run", "url", "content_sha256", "law_number", "law_name", "flags")}
            if prior is not None:
                stats["superseded"] += 1
                superseded.append({**public, "superseded_by": prior, "superseded_by_run": prior["run"],
                                   "identity": list(key), "matched_on": matched,
                                   **({"superseded_by_excluded": True} if prior.get("excluded") else {})})
                continue
            # an excluded row still claims its law: an older copy must not come back in its place
            seen[key] = seen_urls[m["source_url"]] = entry
            seen_ids.setdefault(m["doc_id"], []).append(entry)
            if m.get("content_sha256"):
                seen_sha[m["content_sha256"]] = entry
            if any(f in exclude_flags for f in flags):
                entry["excluded"] = True
                stats["excluded"] += 1
                excluded.append({**public, "identity": list(key)})
                continue
            stats["included"] += 1
            included.append(entry)

    # pass 2: doc_ids. The engine's id map starts fresh in every run, so two runs can mint the same id for two
    # different documents. The older run keeps its id (it was there first, and stays stable across corpora); the
    # newer row gets the next free suffix, and the rename is recorded.
    taken: dict[str, dict] = {}        # doc_id -> the entry that holds it, oldest run first
    reserved = {e["doc_id_in_run"] for e in included}   # a new suffix must not be an id a later row still holds
    renamed: list[dict] = []
    for entry in reversed(included):
        doc_id = entry["doc_id_in_run"]
        if doc_id in taken:
            stem = re.sub(r"-\d{3}$", "", doc_id)
            n = 2
            while f"{stem}-{n:03d}" in taken or f"{stem}-{n:03d}" in reserved:
                n += 1
            holder = taken[doc_id]
            entry["doc_id"] = f"{stem}-{n:03d}"
            renamed.append({"doc_id": entry["doc_id"], "doc_id_in_run": doc_id, "run": entry["run"],
                            "law_number": entry["law_number"], "law_name": entry["law_name"],
                            "collided_with": {"doc_id": doc_id, "run": holder["run"], "law_number": holder["law_number"]}})
            per_run[entry["run"]]["renamed"] += 1
        taken[entry["doc_id"]] = entry
    for s_ in superseded:
        s_["superseded_by"] = s_["superseded_by"]["doc_id"]   # the corpus id, after renaming

    # pass 3: the rows and their files
    rows: list[dict] = []
    link_rows: list[dict] = []
    for entry in included:
        m, run, flags, link = entry["row"], entry["path"], entry["flags"], entry["link"]
        row = {k: m.get(k) for k in MANIFEST_FIELDS}
        if m.get("http") is not None:
            row["http"] = m["http"]
        row["doc_id"] = entry["doc_id"]
        row["local_path"] = place_file(run / m["local_path"], m["local_path"], run, out, hardlink)
        if m.get("http_headers_path") and (run / m["http_headers_path"]).is_file():
            row["http_headers_path"] = place_file(run / m["http_headers_path"], m["http_headers_path"], run, out, hardlink)
        else:
            row["http_headers_path"] = None   # a path into the run folder would not resolve here
        note = f"corpus {corpus_name}: from {run.name}" + (f"; flags {','.join(flags)}" if flags else "")
        if entry["doc_id"] != entry["doc_id_in_run"]:
            note += f"; doc_id in run: {entry['doc_id_in_run']}"
        row["crawl_notes"] = f"{m['crawl_notes']}; {note}" if m.get("crawl_notes") else note
        rows.append(row)
        # one link row per corpus document: the run's row, or a stand-in for a document its list did not carry
        lr = dict(link) if link is not None else {
            "url": m["source_url"], "economy": m.get("economy"), "law_name_guess": m.get("law_name_guess"),
            "law_number_guess": m.get("law_number_guess"), "scopes": [], "contract_meta": {"synthetic": True}}
        lr["contract_meta"] = {**(lr.get("contract_meta") or {}), "content_flags": flags,
                               "corpus": {"run": run.name, "doc_id": entry["doc_id"], "doc_id_in_run": entry["doc_id_in_run"]}}
        link_rows.append(lr)
    rows.sort(key=lambda r: (r.get("law_number_guess") or "", r["doc_id"]))
    write_manifest(rows, out)
    report = validate_manifest(out / "manifest.csv", "0.2.0")
    ok = not report.errors

    lu = out / "links_used"
    lu.mkdir(exist_ok=True)
    with open(lu / "documents.jsonl", "w", encoding="utf-8", newline="\n") as fh:
        for i, lr in enumerate(link_rows, start=1):
            lr["order"] = i
            fh.write(json.dumps(lr, ensure_ascii=False, default=str) + "\n")
    state_run = next((r for r in runs if list_dir(r) and (list_dir(r) / "laws.csv").is_file()), None)
    if state_run is not None:
        shutil.copy2(list_dir(state_run) / "laws.csv", lu / "laws.csv")
    newest_meta = {}
    if state_run is not None and (list_dir(state_run) / "catalogue_meta.json").is_file():
        newest_meta = json.loads((list_dir(state_run) / "catalogue_meta.json").read_text(encoding="utf-8"))
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    kinds: dict[str, int] = {}
    for lr in link_rows:
        k = (lr.get("contract_meta") or {}).get("document_kind") or "agency_or_other"
        kinds[k] = kinds.get(k, 0) + 1
    flagged = sum(1 for e in included if e["flags"])
    synthetic = sum(1 for lr in link_rows if lr["contract_meta"].get("synthetic"))
    (lu / "catalogue_meta.json").write_text(json.dumps({
        "generated_at": generated, "economy": economy, "list_kind": "corpus", "corpus": corpus_name,
        "counts": {"all": len(rows)}, "document_kinds": kinds, "runs": [r.name for r in runs],
        "state_run": state_run.name if state_run else None, "cfg_sha256": newest_meta.get("cfg_sha256"),
        "rule_id": newest_meta.get("rule_id"), "settings": newest_meta.get("settings"),
        "synthetic_rows": synthetic,
        "notes": ["a corpus list: the link rows of the documents in this corpus, from every run merged; a row marked "
                  "contract_meta.synthetic stands in for a document whose run had no link row for it"],
    }, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    with open(out / "superseded.jsonl", "w", encoding="utf-8", newline="\n") as fh:
        for s in superseded:
            fh.write(json.dumps(s, ensure_ascii=False) + "\n")
    meta = {"corpus": corpus_name, "economy": economy, "generated_at": generated, "runs": [r.name for r in runs],
            "per_run": per_run, "documents": len(rows), "superseded": len(superseded), "excluded": len(excluded),
            "excluded_flags": list(exclude_flags), "flagged": flagged, "duplicates_logged": len(duplicates),
            "renamed": renamed, "synthetic_link_rows": synthetic,
            "hardlink": hardlink, "validation": {"ok": ok, "rows": report.row_count, "errors": report.errors,
                                                  "warnings": report.warnings},
            "state_run": state_run.name if state_run else None, "excluded_rows": excluded}
    (out / "corpus_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1, default=str),
                                          encoding="utf-8", newline="\n")
    (out / "CORPUS_NOTE.md").write_text(corpus_note(meta, link_rows, superseded, excluded, runs), encoding="utf-8", newline="\n")
    return meta


def corpus_note(meta: dict, link_rows: list[dict], superseded: list[dict], excluded: list[dict],
                runs: list[Path]) -> str:
    v = meta["validation"]
    lines = [f"# Corpus: {meta['corpus']}", "",
             f"{meta['economy']}, built {meta['generated_at']} by `tools/merge_corpus.py` from {len(runs)} run(s): "
             + ", ".join(f"`{r.name}`" for r in runs) + ".", "",
             f"**{meta['documents']} documents**, one per law and kind, the newest run's copy of each. "
             f"{meta['superseded']} older copies superseded (`superseded.jsonl`), {meta['excluded']} excluded by flag, "
             f"{meta['flagged']} carrying content flags from the runs' audits, {len(meta['renamed'])} renamed doc_ids. "
             f"Validation against contract 0.2.0: "
             f"{'OK' if v['ok'] else 'FAILED'} ({v['rows']} rows, {len(v['errors'])} errors, {len(v['warnings'])} warnings).", "",
             "## What is in this folder", "",
             "| Path | What it is |", "| :---- | :---- |",
             "| `manifest.csv`, `manifest.jsonl` | The corpus, in the Hand-off #1 shape. `crawl_notes` says which run each row came from and its content flags |",
             "| `raw/` | The documents and their header files, copied from the runs under their original paths |",
             "| `superseded.jsonl` | Every older copy a newer run replaced: doc_id, run, URL, the doc_id that supersedes it, and what they matched on (`law`: portal id and kind; `url`; `doc_id`, the same law under the same id; `content`, the same bytes) |",
             "| `links_used/documents.jsonl` | One link row per document here, with `contract_meta.content_flags` and `corpus.run`; a row marked `synthetic` stands in for a document its run's list did not carry |",
             "| `links_used/laws.csv`, `catalogue_meta.json` | The listing state of the newest run that has one |",
             "| `corpus_meta.json` | The figures above, per run |", "",
             "## Per run", "", "| Run | Documents | Included | Superseded | Excluded | Renamed |",
             "| :---- | ----: | ----: | ----: | ----: | ----: |"]
    for name, s in meta["per_run"].items():
        lines.append(f"| `{name}` | {s['documents']} | {s['included']} | {s['superseded']} | {s['excluded']} | {s.get('renamed', 0)} |")
    lines.append("")
    if meta["renamed"]:
        lines += ["## Renamed doc_ids", "",
                  "The engine's id map starts fresh in every run, so two runs minted the same doc_id for two different documents. "
                  "The older run's document keeps the id; the newer one is renamed here (its run folder keeps the id it minted, "
                  "recorded in `crawl_notes` as `doc_id in run`).", "",
                  "| In this corpus | In its run | Run | Law | Collided with |", "| :---- | :---- | :---- | :---- | :---- |"]
        for r in meta["renamed"]:
            c = r["collided_with"]
            lines.append(f"| {r['doc_id']} | {r['doc_id_in_run']} | {r['run']} | {r['law_number'] or ''} {(r['law_name'] or '')[:50]} | "
                         f"{c['doc_id']} in {c['run']} ({c['law_number'] or ''}) |")
        lines.append("")
    flag_counts: dict[str, int] = {}
    for lr in link_rows:
        for f in lr["contract_meta"].get("content_flags") or []:
            flag_counts[f] = flag_counts.get(f, 0) + 1
    if flag_counts:
        lines += ["## Content flags carried by the rows", "", "| Flag | Rows |", "| :---- | ----: |"]
        lines += [f"| `{k}` | {n} |" for k, n in sorted(flag_counts.items())] + ["",
                  "A flagged row is a stored file that is not, or may not be, the law's text (a repeal notice, another act's text, "
                  "a Malay file recorded as English, a page with no text layer). `links_used/documents.jsonl` names the flags per row.", ""]
    if excluded:
        lines += ["## Excluded by flag", "", "| doc_id | Law | Flags | Run |", "| :---- | :---- | :---- | :---- |"]
        lines += [f"| {e['doc_id']} | {e['law_number'] or ''} {(e['law_name'] or '')[:60]} | {', '.join(e['flags'])} | {e['run']} |" for e in excluded] + [""]
    if superseded:
        lines += ["## Superseded (first 30)", "", "| Older copy | Run | Replaced by | Run |", "| :---- | :---- | :---- | :---- |"]
        lines += [f"| {s['doc_id']} ({s['law_number'] or ''}) | {s['run']} | {s['superseded_by']} | {s['superseded_by_run']} |"
                  for s in superseded[:30]] + [""]
    if not v["ok"]:
        lines += ["## Validation errors", ""] + [f"- {e}" for e in v["errors"]] + [""]
    return "\n".join(lines)


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--outputs", required=True, help="the country's run folders, outputs/<CC>")
    ap.add_argument("--out", required=True, help="the new corpus folder, outputs/<CC>/<CC>_corpus_<date>")
    ap.add_argument("--economy", help="default: from the --outputs folder name")
    ap.add_argument("--hardlink", action="store_true", help="hard-link files instead of copying (same drive)")
    ap.add_argument("--exclude-flags", default="", help="comma-separated audit flags whose rows are left out")
    args = ap.parse_args(argv)
    outputs, out = Path(args.outputs), Path(args.out)
    economy = (args.economy or guess_economy(outputs) or "").upper()
    if not economy:
        print(f"[corpus] cannot tell the country from {outputs}; pass --economy", flush=True)
        return 1
    flags = tuple(f.strip() for f in args.exclude_flags.split(",") if f.strip())
    try:
        meta = merge(outputs, out, economy, args.hardlink, flags)
    except (FileNotFoundError, FileExistsError) as e:
        print(f"[corpus] {e}", flush=True)
        return 1
    v = meta["validation"]
    print(f"[corpus] {out.name}: {meta['documents']} documents from {len(meta['runs'])} run(s), "
          f"{meta['superseded']} superseded, {meta['excluded']} excluded, {meta['flagged']} flagged; "
          f"validation {'OK' if v['ok'] else 'FAILED'} -> {out / 'CORPUS_NOTE.md'}", flush=True)
    return 0 if v["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
