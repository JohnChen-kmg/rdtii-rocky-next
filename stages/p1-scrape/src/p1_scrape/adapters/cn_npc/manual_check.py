"""Build the worklist for updating the sources no tool can read.

`tools/update.py` can re-read CAC and gov.cn, because those hosts permit us. **MIIT and Customs refuse an honest
client**, so nothing automatic will ever tell us that one of their rules was amended or repealed. A person has to
look. This writes that person's worklist: the section pages to open, and **the exact address of every document we
hold**, with the version date printed on it, so the check is a comparison and not a search.

It sends no request. It reads each source's `provenance.tsv` and the watch list, and writes one Markdown file.

    python countries/cn-china/tools/manual_check.py
    python countries/cn-china/tools/manual_check.py --source miit --print

`CONVENTIONS.md` rules 11 and 13. The result goes in the collection folder as `MANUAL_UPDATE_CHECK.md`, and the
date of a completed check is recorded in `watchlist.tsv` with
`python countries/my-malaysia/scraper/watchlist.py <list> --checked <name>`.
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8")

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
#: beside this module. In the development workshop it sat one level up, in
#: countries/cn-china/; here the tools and the list travel together.
WATCHLIST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "watchlist.tsv")

#: What a source is called on the watch list, so the two records can be joined.
WATCH_NAME = {
    "miit": "工业和信息化部",
    "customs": "海关总署",
    "npc-database": "国家法律法规数据库",
}


def collection_dir(base: str) -> str:
    return os.path.join(REPO, "outputs", "CN", base)


def manual_sources(base: str) -> List[Tuple[str, str]]:
    """Every folder collected by hand, active first, then the deferred ones. `(name, path)`."""
    out: List[Tuple[str, str]] = []
    for parent in (os.path.join(collection_dir(base), "manual"),
                   os.path.join(collection_dir(base), "_deferred", "manual")):
        if not os.path.isdir(parent):
            continue
        for name in sorted(os.listdir(parent)):
            path = os.path.join(parent, name)
            if os.path.isfile(os.path.join(path, "provenance.tsv")):
                out.append((name, path))
    return out


def read_provenance(path: str) -> List[Dict[str, str]]:
    """A source's sheet, with short rows padded so a missing trailing column never raises."""
    with open(os.path.join(path, "provenance.tsv"), encoding="utf-8-sig", newline="") as f:
        rows = [r for r in csv.reader(f, delimiter="\t") if r]
    if not rows:
        return []
    head = rows[0]
    return [dict(zip(head, r + [""] * (len(head) - len(r)))) for r in rows[1:]]


def read_watchlist() -> List[Dict[str, str]]:
    if not os.path.exists(WATCHLIST):
        return []
    with open(WATCHLIST, encoding="utf-8", newline="") as f:
        return [{k: (v or "") for k, v in row.items() if k}
                for row in csv.DictReader(f, delimiter="\t", restval="")]


def watch_rows_for(source: str, watch: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """The watch-list rows that belong to one source folder, matched on the issuer's Chinese name."""
    key = WATCH_NAME.get(source)
    return [r for r in watch if key and key in r.get("name", "")] if key else []


def held(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """The documents actually downloaded — those with a file recorded and not declined."""
    return [r for r in rows if r.get("file_saved_as", "").strip()
            and r["file_saved_as"].strip().lower() != "not taken"]


def outstanding(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Rows still to download: named on the sheet, with no file and not declined."""
    return [r for r in rows if not r.get("file_saved_as", "").strip()]


def _cell(s: str, width: int = 0) -> str:
    """A value safe to put in a Markdown table: no pipes, no line breaks, optionally shortened."""
    s = (s or "").replace("|", "/").replace("\n", " ").replace("\r", " ").strip()
    if width and len(s) > width:
        s = s[: width - 1] + "…"
    return s or "—"


def source_section(source: str, path: str, watch: List[Dict[str, str]]) -> List[str]:
    """One source's part of the worklist."""
    rows = read_provenance(path)
    h, todo = held(rows), outstanding(rows)
    deferred = os.sep + "_deferred" + os.sep in path
    lines = [f"## {source}{'  — deferred' if deferred else ''}", ""]

    wr = watch_rows_for(source, watch)
    if wr:
        lines += ["**Open these index pages first**, and compare what they list with the table below.", ""]
        for r in wr:
            last = r.get("last_checked", "").strip() or "**never checked**"
            lines += [f"- [{_cell(r['name'])}]({r['url']}) — {_cell(r.get('what_to_look_for', ''))}",
                      f"  · refuses our client: {_cell(r.get('why_not_automatic', ''))} · last checked: {last}"]
        lines.append("")
    else:
        lines += ["*No index page on the watch list for this source — add one (`watchlist.tsv`), "
                  "or this check has nothing to compare against.*", ""]

    lines += ["**Three questions, in this order:**", "",
              "1. Does the index list anything **new** that is not in the table below?",
              "2. Is any document in the table shown with a **later version date** than the one we hold?",
              "3. Is any document in the table marked **废止 / 失效** (repealed or lapsed)?", ""]

    if h:
        lines += [f"### Documents held — {len(h)}", "",
                  "| # | Document | Reference | Version we hold | Open | File |",
                  "| ---: | :---- | :---- | :---- | :---- | :---- |"]
        for r in h:
            url = r.get("url", "").strip()
            link = f"[open]({url})" if url.startswith("http") else "**no address recorded**"
            lines.append(f"| {_cell(r.get('n', ''))} | {_cell(r.get('title', ''), 46)} | "
                         f"{_cell(r.get('reference', ''), 28)} | "
                         f"{_cell(r.get('version_date_on_document', '') or r.get('stated_in_force', ''), 14)} | "
                         f"{link} | {_cell(r.get('file_saved_as', ''), 34)} |")
        lines.append("")
    else:
        lines += ["*Nothing downloaded from this source yet.*", ""]

    if todo:
        lines += [f"### Still to download — {len(todo)}", ""]
        for r in todo:
            url = r.get("url", "").strip()
            lines.append(f"- {_cell(r.get('title', ''))} — "
                         + (f"[open]({url})" if url.startswith("http") else "*no address recorded*"))
        lines.append("")

    missing = [r for r in h if not r.get("url", "").strip().startswith("http")]
    if missing:
        lines += [f"> **{len(missing)} held documents have no address on the sheet.** They cannot be checked by "
                  "hand until one is recorded — that is the whole cost of a missing `url`.", ""]
    return lines


def build(base: str, only: Optional[str] = None, today: Optional[str] = None) -> str:
    """The whole worklist, as Markdown."""
    today = today or datetime.now().strftime("%Y-%m-%d")
    sources = [(n, p) for n, p in manual_sources(base) if only in (None, n)]
    watch = read_watchlist()
    total_held = sum(len(held(read_provenance(p))) for _, p in sources)

    lines = [
        "# Update by hand — the sources no tool can read",
        "",
        f"**Written {today} by `countries/cn-china/tools/manual_check.py`, from each source's `provenance.tsv`.**",
        "Rewritten on every run; nothing here is hand-edited.",
        "",
        f"`tools/update.py` covers CAC and gov.cn, which permit us. It cannot cover the **{len(sources)} sources "
        f"below, holding {total_held} documents**: their hosts refuse an honest client, so no tool will ever "
        "report that one of these rules was amended or repealed. **Until a person walks this list, an update "
        "check of China is not complete** (`CONVENTIONS.md` rule 11).",
        "",
        "Work through each source, answer its three questions, then record the date:",
        "",
        "```",
        "python countries/my-malaysia/scraper/watchlist.py countries/cn-china/watchlist.tsv --checked <name>",
        "```",
        "",
        "Found something? **Do not edit a stored file.** Add a row to that source's `provenance.tsv`, download the "
        "new version beside the old one, and note the change — a superseded text is kept, not replaced "
        "(`CONVENTIONS.md` rule 6, flag and do not fix).",
        "",
    ]
    for name, path in sources:
        lines += source_section(name, path, watch)
    if not sources:
        lines += ["*No hand-collected source found in this collection.*", ""]
    return "\n".join(lines).rstrip() + "\n"


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--base", default="CN_sources_2026-09-21", help="the collection folder under outputs/CN/")
    ap.add_argument("--source", help="only this source folder, e.g. miit")
    ap.add_argument("--out", help="where to write (default: the collection's MANUAL_UPDATE_CHECK.md)")
    ap.add_argument("--print", dest="show", action="store_true", help="also print it")
    args = ap.parse_args(argv)

    if not os.path.isdir(collection_dir(args.base)):
        print(f"no such collection: {collection_dir(args.base)}")
        return 2
    text = build(args.base, args.source)
    out = args.out or os.path.join(collection_dir(args.base), "MANUAL_UPDATE_CHECK.md")
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    if args.show:
        print(text)
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
