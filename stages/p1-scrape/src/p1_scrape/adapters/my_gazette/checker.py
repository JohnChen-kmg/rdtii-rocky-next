"""The law table for Malaysia: one row per law we hold, with what the portal says about its status and dates.

Reads a run or corpus folder and writes `law_table.csv` in it. **It sends no request**: every value comes from
what the catalogue already read (`links_used/documents.jsonl`, `links_used/laws.csv`) and from the crawl's
`manifest.jsonl`. Re-run it whenever a run or corpus changes.

What the dates mean on Laws of Malaysia, and what the portal does **not** say:

- `effective_date` is the text's **as-at date** (`as_at` in the census, printed on the document itself): the day
  the reprint or revised edition speaks from. It is not a commencement date.
- `last_amended` and `last_amending_instrument` are **derived from our own rows**, not from the portal: the
  newest amending instrument we hold for that act, by its gazette date. So the date says when the amendment was
  published, not when it came into force, and an amendment we never fetched is not counted. The portal states no
  "last amended" of its own anywhere. How far that reaches, on `MY_corpus_2026-09-15`: of 469 amending rows, 407
  name the act they amend and 343 also carry a gazette date, which fills the column for 192 of the 822 principal
  acts. An act with an empty `last_amended` has no dated amendment **in our corpus**; it does not mean the act was
  never amended.
- `text_version` says which kind of text the file is: `reprint`, `as_enacted` or a revised edition.
- `published_on` is the gazette date of the document itself.

`in_force` is the plain-words column: `yes`, `no (repealed)`, `not yet` or `not stated`. **A caution for this
country:** Laws of Malaysia states a status for very few acts. In the census of 2026-09-15, 133 of 1,291 rows
carry a marker (repealed, or "Superseded by Act N", which counts as repealed by decision 10) and the rest say
nothing, so `not stated` is the honest answer and no status is inferred from anything else (`POLICY.md` 3.5).
`status_marker` keeps the portal's own words where there are any.

`use` says what a later stage should do with the document (decision 20):

| Value | Meaning |
| :---- | :---- |
| `evidence` | A principal law, a regulation or a practice document: the text states a rule, so it is read, OCR'd where needed, and mapped |
| `evidence, text stale` | The same, but an amending instrument we hold is **newer than this text**, so the text is not the current law on the points that instrument changed (`POLICY.md` 3.3) |
| `linkage` | An amending or commencement instrument: kept and linked to its principal law, but not read for indicators. It carries no indicator tags of its own, and cited in place of the principal it scores zero (`POLICY.md` 3.2) |
| `linkage, text needed` | An amending or commencement instrument **newer than the principal text we hold**: the only place in this corpus where its changes are written out, so it is read and mapped after all |

    python -m p1_scrape.adapters.my_gazette.checker <run or corpus folder> [--out FILE] [--all]

`--all` adds the laws the portal lists that the run did not fetch, with `scraped` `no` and the reason in `notes`.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Any, Optional

COLUMNS = [
    "law_name", "law_number", "portal_id", "document_kind", "principal_law_number",
    "use",
    "in_force", "legal_status", "status_source", "status_marker",
    "effective_date", "text_version", "published_on", "last_amended", "last_amending_instrument",
    "language",
    "scraped", "doc_id", "access_date", "source_url", "file", "run", "notes",
]

IN_FORCE_WORDS = {
    "in_force": "yes",
    "repealed": "no (repealed)",
    "partially_in_force": "in part",
    "not_yet_in_force": "not yet",
    "unknown": "not stated",
}

_DMY = re.compile(r"^(\d{2})-(\d{2})-(\d{4})$")


def _jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _iso(date: Optional[str]) -> str:
    """The census writes as-at dates as DD-MM-YYYY; the table writes every date the same way, YYYY-MM-DD."""
    m = _DMY.match((date or "").strip())
    return f"{m.group(3)}-{m.group(2)}-{m.group(1)}" if m else (date or "").strip()


def _census(folder: Path) -> dict[str, dict]:
    """The catalogue's one-row-per-law census, keyed by law number (its `portal_id` is the bare number)."""
    path = folder / "links_used" / "laws.csv"
    if not path.is_file():
        return {}
    out: dict[str, dict] = {}
    with path.open(encoding="utf-8-sig", newline="") as fh:
        for r in csv.DictReader(fh):
            if r.get("law_number"):
                out[r["law_number"].strip().lower()] = r
    return out


def _amendments(links: list[dict]) -> dict[str, tuple[str, str]]:
    """The newest amending instrument we hold for each act: {principal law number: (gazette date, its number)}."""
    newest: dict[str, tuple[str, str]] = {}
    for link in links:
        meta = link.get("contract_meta") or {}
        if meta.get("document_kind") != "amending_act":
            continue
        parent = (meta.get("principal_law_number") or "").strip().lower()
        date = (meta.get("published_on") or "").strip()
        if not parent or not date:
            continue
        if parent not in newest or date > newest[parent][0]:
            newest[parent] = (date, meta.get("law_number") or link.get("law_number_guess") or "")
    return newest


def _words(status: Optional[str]) -> str:
    return IN_FORCE_WORDS.get((status or "unknown"), status or "not stated")


def _row(law_name: str, meta: dict, census: dict, stored: Optional[dict], run_name: str, url: str,
         amendments: dict[str, tuple[str, str]], notes: list[str]) -> dict[str, Any]:
    status = meta.get("legal_status") or census.get("legal_status") or "unknown"
    number = (meta.get("law_number") or census.get("law_number") or "").strip()
    last = amendments.get(number.lower()) if meta.get("document_kind") == "principal_act" else None
    return {
        "use": "",
        "law_name": law_name,
        "law_number": number,
        "portal_id": meta.get("portal_id") or census.get("portal_id") or "",
        "document_kind": meta.get("document_kind") or "",
        "principal_law_number": meta.get("principal_law_number") or meta.get("commences_law_number") or "",
        "in_force": _words(status),
        "legal_status": status,
        "status_source": meta.get("status_source") or "",
        "status_marker": census.get("status_marker") or "",
        "effective_date": _iso(census.get("as_at")),
        "text_version": meta.get("text_version") or "",
        "published_on": meta.get("published_on") or "",
        "last_amended": last[0] if last else "",
        "last_amending_instrument": last[1] if last else "",
        "language": meta.get("language") or "",
        "scraped": "yes" if stored else "no",
        "doc_id": (stored or {}).get("doc_id") or "",
        "access_date": (stored or {}).get("access_date") or "",
        "source_url": url,
        "file": (stored or {}).get("local_path") or "",
        "run": run_name,
        "notes": "; ".join(n for n in notes if n),
    }


def _stale(rows: list[dict]) -> tuple[set[str], set[str]]:
    """The pairs POLICY.md 3.3 asks to flag: a principal text older than an amending instrument we hold.

    Returns (principal law numbers whose text is stale, amending law numbers that carry the newer text).
    An amendment is linked to its principal by `principal_law_number`, which Laws of Malaysia's timelines give.
    """
    principals = {r["law_number"].strip().lower(): r for r in rows
                  if r["document_kind"] == "principal_act" and r["law_number"].strip()}
    stale_principals: set[str] = set()
    newer_amendments: set[str] = set()
    for r in rows:
        if r["document_kind"] not in ("amending_act", "commencement_instrument"):
            continue
        parent = principals.get((r.get("principal_law_number") or "").strip().lower())
        date = (r.get("published_on") or "").strip()
        if not parent or not date or not parent["effective_date"]:
            continue
        if date > parent["effective_date"]:
            stale_principals.add(parent["law_number"].strip().lower())
            newer_amendments.add(r["law_number"].strip().lower())
    return stale_principals, newer_amendments


def _mark_use(rows: list[dict]) -> list[dict]:
    """Fill the `use` column, and flag the stale pairs (POLICY.md 3.3) on both sides."""
    stale_principals, newer_amendments = _stale(rows)
    for r in rows:
        number = r["law_number"].strip().lower()
        if r["document_kind"] in ("amending_act", "commencement_instrument"):
            r["use"] = "linkage, text needed" if number in newer_amendments else "linkage"
        else:
            r["use"] = "evidence, text stale" if number in stale_principals else "evidence"
    return rows


def rows_for(folder: Path, include_unfetched: bool = False) -> list[dict]:
    """One row per document the folder holds; with include_unfetched, also every listed law it does not."""
    folder = Path(folder)
    stored = {m["source_url"]: m for m in _jsonl(folder / "manifest.jsonl")}
    census = _census(folder)
    links = _jsonl(folder / "links_used" / "documents.jsonl")
    amendments = _amendments(links)
    rows: list[dict] = []
    seen: set[str] = set()
    for link in links:
        url = link.get("url") or ""
        meta = link.get("contract_meta") or {}
        if not include_unfetched and url not in stored:
            continue
        number = (meta.get("law_number") or "").strip().lower()
        seen.add(number)
        notes = list(meta.get("review_flags") or [])
        if url not in stored:
            notes.append("listed, not fetched by this run")
        rows.append(_row(link.get("law_name_guess") or "", meta, census.get(number, {}), stored.get(url),
                         folder.name, url, amendments, notes))
    if include_unfetched:
        for number, c in census.items():
            if number in seen:
                continue
            meta = {"portal_id": c.get("portal_id"), "law_number": c.get("law_number"),
                    "legal_status": c.get("legal_status"), "status_source": "portal_listing",
                    "principal_law_number": c.get("principal_law_number"),
                    "language": c.get("document_language"),
                    "document_kind": (c.get("document_kinds") or "").split(";")[0]}
            rows.append(_row(c.get("title_bi") or c.get("title_bm") or "", meta, c, None, folder.name,
                             c.get("document_url") or "", amendments,
                             [c.get("not_crawled_reason") or "not in the list"]))
    _mark_use(rows)
    rows.sort(key=lambda r: (r["use"], r["document_kind"], r["law_name"].lower()))
    return rows


def write(rows: list[dict], out: Path) -> Path:
    out = Path(out)
    # utf-8-sig so Excel on Windows shows the Malay titles correctly
    with out.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    return out


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("folder", help="a run or corpus folder under outputs/MY/")
    ap.add_argument("--out", help="default: law_table.csv inside the folder")
    ap.add_argument("--all", action="store_true", help="also the listed laws the run did not fetch")
    a = ap.parse_args(argv)
    folder = Path(a.folder)
    rows = rows_for(folder, include_unfetched=a.all)
    out = write(rows, Path(a.out) if a.out else folder / "law_table.csv")
    kept = sum(1 for r in rows if r["scraped"] == "yes")
    by_status: dict[str, int] = {}
    by_use: dict[str, int] = {}
    for r in rows:
        by_status[r["in_force"]] = by_status.get(r["in_force"], 0) + 1
        by_use[r["use"]] = by_use.get(r["use"], 0) + 1
    print(f"[checker] {folder.name}: {len(rows)} laws ({kept} scraped), in force: "
          + ", ".join(f"{k} {v}" for k, v in sorted(by_status.items()))
          + " | use: " + ", ".join(f"{k} {v}" for k, v in sorted(by_use.items())) + f" -> {out}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
