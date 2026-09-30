"""The law table for Timor-Leste: one row per act, from a run or corpus folder, with no request sent.

    python -m p1_scrape.adapters.tl_jornal.checker <run-or-corpus> [--all] [--out law_table.csv]

Every value comes from files already in the folder — `links_used/laws.csv` (the census of what the portal listed),
the link rows' `contract_meta`, and the manifest (what was actually stored). `--all` adds the acts the portal
lists that this run did not fetch, so a dropped set still appears with its dates.

**What this country cannot fill in, and why.** The gazette publishes as-made acts and states no status: nothing on
the portal says whether a law is in force, amended or repealed. So `in_force` is `not stated` for every row and
`legal_status` is `unknown` — a reading of the portal, never an inference (`POLICY.md` 3.5). What *can* be said is
which acts amend which: an amending act names its target in its own title, so `last_amended` and
`last_amending_instrument` are filled from the listing itself, and `use` (decision 20) follows from the dates.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Optional

COLUMNS = ["law_name", "law_number", "portal_id", "document_kind", "use", "in_force", "legal_status",
           "status_source", "effective_date", "last_amended", "last_amending_instrument", "scraped", "doc_id",
           "access_date", "source_url", "file", "run", "notes",
           # Timor-Leste's own, after the common ones (CONVENTIONS.md section 2)
           "category_label", "published_on", "amends_law_number", "acts_in_document"]


def _read_csv(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    with path.open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def _read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def rows_for(folder: str | Path, include_all: bool = False) -> list[dict]:
    """One row per act. Without `--all`, only the acts whose document this folder holds."""
    run = Path(folder)
    laws = _read_csv(run / "links_used" / "laws.csv")
    links = _read_jsonl(run / "links_used" / "documents.jsonl")
    manifest = _read_jsonl(run / "manifest.jsonl") or _read_csv(run / "manifest.csv")
    stored = {str(m.get("source_url")): m for m in manifest if m.get("source_url")}
    meta_by_url = {row.get("url"): (row.get("contract_meta") or {}) for row in links}

    by_number: dict[str, dict] = {}
    for law in laws:
        if law.get("law_number"):
            by_number.setdefault(str(law["law_number"]), law)

    out = []
    for law in laws:
        url = law.get("document_url") or ""
        doc = stored.get(url)
        if not doc and not include_all:
            continue
        meta = meta_by_url.get(url, {})
        amends = (law.get("amends_law_number") or "").strip() or None
        last_amended, last_instrument = _amendment_of(law, laws)
        out.append({
            "law_name": law.get("title"), "law_number": law.get("law_number"), "portal_id": law.get("portal_id"),
            "document_kind": law.get("document_kind"),
            "use": _use(law, doc is not None, last_amended, amends),
            "in_force": "not stated",                  # the gazette states none (module docstring)
            "legal_status": law.get("legal_status") or "unknown", "status_source": None,
            "effective_date": law.get("published_on"),
            "last_amended": last_amended, "last_amending_instrument": last_instrument,
            "scraped": "yes" if doc else "no",
            "doc_id": (doc or {}).get("doc_id"), "access_date": (doc or {}).get("access_date"),
            "source_url": url or None, "file": (doc or {}).get("local_path"), "run": run.name,
            "notes": law.get("not_crawled_reason"),
            "category_label": law.get("category_label"), "published_on": law.get("published_on"),
            "amends_law_number": amends,
            "acts_in_document": law.get("acts_in_document") or (len(meta.get("contains") or []) or None),
        })
    return out


def _amendment_of(law: dict, laws: list[dict]) -> tuple[Optional[str], Optional[str]]:
    """The latest act that names this one as the act it alters, by publication date."""
    number = str(law.get("law_number") or "")
    if not number:
        return None, None
    amendments = [a for a in laws if (a.get("amends_law_number") or "").strip() == number]
    if not amendments:
        return None, None
    newest = max(amendments, key=lambda a: a.get("published_on") or "")
    year = (newest.get("published_on") or "")[:4] or None
    return year, f"{newest.get('category_label')} n.º {newest.get('law_number')}"


def _use(law: dict, stored: bool, last_amended: Optional[str], amends: Optional[str]) -> str:
    """What a later stage should do with this document (decision 20).

    An amending act is linkage, not evidence; it becomes `linkage, text needed` when it is the newest text of the
    law it alters, which in a gazette country is the normal case, because no consolidated text exists.
    """
    kind = law.get("document_kind")
    if kind == "amending_act":
        return "linkage, text needed" if stored else "linkage"
    if not stored:
        return "not held"
    if last_amended and (law.get("published_on") or "")[:4] and last_amended > (law.get("published_on") or "")[:4]:
        return "evidence, text stale"
    return "evidence"


def write(folder: str | Path, include_all: bool = False, out: Optional[str] = None) -> str:
    rows = rows_for(folder, include_all)
    target = Path(out) if out else Path(folder) / "law_table.csv"
    with target.open("w", encoding="utf-8-sig", newline="") as fh:     # the byte-order mark Excel needs
        writer = csv.DictWriter(fh, fieldnames=COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: _cell(row.get(k)) for k in COLUMNS})
    return str(target)


def _cell(value: Any) -> Any:
    if isinstance(value, (list, tuple)):
        return "; ".join(str(v) for v in value)
    return "" if value is None else value


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("folder", help="a run or corpus folder under outputs/TL/")
    ap.add_argument("--all", action="store_true", help="include the acts the portal lists that this folder lacks")
    ap.add_argument("--out", help="where to write (default: <folder>/law_table.csv)")
    a = ap.parse_args(argv)
    rows = rows_for(a.folder, a.all)
    path = write(a.folder, a.all, a.out)
    uses: dict[str, int] = {}
    for row in rows:
        uses[row["use"]] = uses.get(row["use"], 0) + 1
    scraped = sum(1 for r in rows if r["scraped"] == "yes")
    print(f"[checker] TL: {len(rows)} act(s) ({scraped} scraped); use: "
          + ", ".join(f"{k} {v}" for k, v in sorted(uses.items())) + f" -> {path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
