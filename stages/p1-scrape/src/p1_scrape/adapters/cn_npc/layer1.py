"""Layer 1: read the national database's bulk-download archives offline, and compare two of them.

`flk.npc.gov.cn` forbids automated collection, so its export is downloaded by hand. This module never sends a
request. It reads what the developer downloaded:

    index(archive_dir)             every document in the archives: title, version date, kind, archive
    diff(old_dir, new_dir)         added, removed, and amended (same title, a later version date)

Every file name in an export carries its version date, `中华人民共和国消防法_20210429.docx`, so an amendment
shows up as a changed date on an unchanged title — no text comparison is needed to find one.

    python countries/cn-china/tools/layer1.py index outputs/CN/CN_sources_2026-09-21/manual/npc-database/raw
    python countries/cn-china/tools/layer1.py diff  <old raw folder> <new raw folder>
"""
from __future__ import annotations

import csv
import glob
import os
import re
import sys
import zipfile

NAME = re.compile(r"^(?P<title>.+?)_(?P<date>\d{8})\.(?P<ext>docx?|pdf|txt)$", re.I)


def _decode(zinfo: zipfile.ZipInfo) -> str:
    """Chinese Windows archives store names in GBK without the UTF-8 flag; zipfile reads them as cp437."""
    n = zinfo.filename
    if zinfo.flag_bits & 0x800:  # the archive says the name is UTF-8
        return n
    try:
        return n.encode("cp437").decode("gbk")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return n


def kind_of(title: str) -> str:
    t = title
    if "修正案" in t:
        return "law amendment"
    if re.search(r"(解释|答复)$", t) and ("全国人民代表大会常务委员会" in t or "最高人民" in t):
        return "interpretation"
    if t.startswith("全国人民代表大会") and re.search(r"决定$", t):
        return "NPC decision"
    # before the test for 法: "…管理办法" ends in 法 but is an administrative regulation, not a law
    if re.search(r"(条例|规定|办法|细则|规则)$", t):
        return "administrative regulation"
    if t.endswith("法") or t.endswith("法典"):
        return "law"
    if t.endswith("决定"):
        return "decision"
    return "other"


def index(archive_dir: str) -> list[dict]:
    rows = []
    for z in sorted(glob.glob(os.path.join(archive_dir, "*.zip"))):
        with zipfile.ZipFile(z) as f:
            for zi in f.infolist():
                if zi.is_dir():
                    continue
                name = _decode(zi).rsplit("/", 1)[-1]
                m = NAME.match(name)
                title, date = (m.group("title"), m.group("date")) if m else (os.path.splitext(name)[0], "")
                rows.append({
                    "title": title,
                    "version_date": f"{date[:4]}-{date[4:6]}-{date[6:]}" if date else "",
                    "kind": kind_of(title),
                    "file": name,
                    "archive": os.path.basename(z),
                    "bytes": zi.file_size,
                })
    return rows


def diff(old: list[dict], new: list[dict]) -> dict:
    """Compare two indexes by title. A title in both with a later date is amended; with an earlier one, reverted."""
    o = {r["title"]: r for r in old}
    n = {r["title"]: r for r in new}
    added = [n[t] for t in n if t not in o]
    removed = [o[t] for t in o if t not in n]
    amended = [{"title": t, "was": o[t]["version_date"], "now": n[t]["version_date"]}
               for t in n if t in o and n[t]["version_date"] > o[t]["version_date"]]
    earlier = [{"title": t, "was": o[t]["version_date"], "now": n[t]["version_date"]}
               for t in n if t in o and n[t]["version_date"] < o[t]["version_date"]]
    return {"added": added, "removed": removed, "amended": amended, "earlier": earlier}


def write_index(rows: list[dict], path: str) -> None:
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["title", "version_date", "kind", "file", "archive", "bytes"])
        w.writeheader()
        w.writerows(sorted(rows, key=lambda r: (r["kind"], r["title"])))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) >= 3 and sys.argv[1] == "index":
        rows = index(sys.argv[2])
        out = os.path.join(os.path.dirname(os.path.abspath(sys.argv[2])), "index.csv")
        write_index(rows, out)
        kinds = {}
        for r in rows:
            kinds[r["kind"]] = kinds.get(r["kind"], 0) + 1
        print(f"{len(rows)} documents -> {out}")
        for k, v in sorted(kinds.items(), key=lambda kv: -kv[1]):
            print(f"  {v:>4}  {k}")
    elif len(sys.argv) >= 4 and sys.argv[1] == "diff":
        d = diff(index(sys.argv[2]), index(sys.argv[3]))
        for k in ("added", "removed", "amended", "earlier"):
            print(f"{k}: {len(d[k])}")
            for r in d[k][:20]:
                print("   ", r.get("title"), r.get("was", ""), r.get("now", r.get("version_date", "")))
    else:
        print(__doc__)
