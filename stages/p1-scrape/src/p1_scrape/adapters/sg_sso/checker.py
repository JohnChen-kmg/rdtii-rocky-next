"""The law table for Singapore: one row per law we hold, with what the portal says about its status and dates.

Reads a run or corpus folder and writes `law_table.csv` in it. **It sends no request**: every value comes from
what the catalogue already read (`links_used/documents.jsonl`, `links_used/laws.csv`) and from the crawl's
`manifest.jsonl`. Re-run it whenever a run or corpus changes.

What the dates mean on Statutes Online:

- `effective_date` is the act's **current version date** (`version_as_at`): the day the stored text came into
  force. The portal states it on the act's detail page and in the version list.
- `last_amended` is the **year** of the last amending instrument, which is all the portal's listing gives; the
  instrument itself is named in `last_amending_instrument` (for example `Act 19 of 2025`). A law with no
  amendment listed leaves both empty.
- `repealed_on` comes from the Repealed listing, which carries the repeal date for every one of its acts.
- Subsidiary legislation carries its own version date and its parent act in `principal_law_number`.

`in_force` is the plain-words column: `yes`, `no (repealed)`, `not yet` or `not stated`. It is a reading of
`legal_status`, which holds the contract value, and `status_source` says where that came from. Nothing here is
inferred: what the portal does not state is empty (`POLICY.md` 3.5).

`use` says what a later stage should do with the document (decision 20):

| Value | Meaning |
| :---- | :---- |
| `evidence` | A principal law, a regulation or a practice document: the text states a rule, so it is read, OCR'd where needed, and mapped |
| `evidence, text stale` | The same, but an amending instrument we hold is **newer than this text**, so the text is not the current law on the points that instrument changed (`POLICY.md` 3.3) |
| `linkage` | An amending or commencement instrument: kept and linked to its principal law, but not read for indicators. It carries no indicator tags of its own, and cited in place of the principal it scores zero (`POLICY.md` 3.2) |
| `linkage, text needed` | An amending or commencement instrument **newer than the principal text we hold**: the only place in this corpus where its changes are written out, so it is read and mapped after all |

    python -m p1_scrape.adapters.sg_sso.checker <run or corpus folder> [--out FILE] [--all]

`--all` adds the laws the portal lists that the run did not fetch (the repealed acts a run drops, for instance),
with `scraped` `no` and the reason in `notes`.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Optional

COLUMNS = [
    "law_name", "law_number", "portal_id", "document_kind", "principal_law_number",
    "use",
    "in_force", "legal_status", "status_source",
    "effective_date", "last_amended", "last_amending_instrument", "repealed_on", "revised_edition",
    "scraped", "doc_id", "access_date", "source_url", "file", "run", "notes",
]

IN_FORCE_WORDS = {
    "in_force": "yes",
    "repealed": "no (repealed)",
    "not_yet_in_force": "not yet",
    "unknown": "not stated",
}


def _jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _census(folder: Path) -> dict[str, dict]:
    """The catalogue's one-row-per-act census, keyed by portal id."""
    path = folder / "links_used" / "laws.csv"
    if not path.is_file():
        return {}
    with path.open(encoding="utf-8-sig", newline="") as fh:
        return {r["portal_id"]: r for r in csv.DictReader(fh) if r.get("portal_id")}


def _words(status: Optional[str]) -> str:
    return IN_FORCE_WORDS.get((status or "unknown"), status or "not stated")


def _row(law_name: str, meta: dict, census: dict, stored: Optional[dict], run_name: str,
         url: str, notes: list[str]) -> dict[str, Any]:
    status = meta.get("legal_status") or census.get("legal_status") or "unknown"
    return {
        "use": "",
        "law_name": law_name,
        "law_number": meta.get("law_number") or census.get("law_number") or "",
        "portal_id": meta.get("portal_id") or census.get("portal_id") or "",
        "document_kind": meta.get("document_kind") or "",
        "principal_law_number": meta.get("principal_law_number") or "",
        "in_force": _words(status),
        "legal_status": status,
        "status_source": meta.get("status_source") or "",
        "effective_date": meta.get("version_as_at") or census.get("version_as_at") or "",
        "last_amended": meta.get("last_amended_year") or "",
        "last_amending_instrument": meta.get("last_amending_instrument") or census.get("last_amending_instrument") or "",
        "repealed_on": census.get("repeal_date") or "",
        "revised_edition": meta.get("revised_edition") or census.get("revised_edition") or "",
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
    The portal names each act's last amending instrument on the act's own row, which is the only link it
    gives: its listing of new acts does not say which act each one amends.
    """
    amendments = {r["law_number"].strip().lower(): r for r in rows
                  if r["document_kind"] in ("amending_act", "commencement_instrument") and r["law_number"].strip()}
    stale_principals: set[str] = set()
    newer_amendments: set[str] = set()
    for r in rows:
        if r["document_kind"] != "principal_act" or not r["effective_date"]:
            continue
        amd = amendments.get((r.get("last_amending_instrument") or "").strip().lower())
        if not amd:
            continue
        date = (amd.get("effective_date") or amd.get("published_on") or "").strip()
        if date and date > r["effective_date"]:
            stale_principals.add(r["law_number"].strip().lower())
            newer_amendments.add(amd["law_number"].strip().lower())
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
    """One row per document the folder holds; with include_unfetched, also every listed act it does not."""
    folder = Path(folder)
    stored = {m["source_url"]: m for m in _jsonl(folder / "manifest.jsonl")}
    census = _census(folder)
    rows: list[dict] = []
    seen_ids: set[str] = set()
    for link in _jsonl(folder / "links_used" / "documents.jsonl"):
        url = link.get("url") or ""
        meta = link.get("contract_meta") or {}
        if not include_unfetched and url not in stored:
            continue
        pid = meta.get("portal_id") or ""
        seen_ids.add(pid)
        notes = list(meta.get("review_flags") or [])
        if url not in stored:
            notes.append("listed, not fetched by this run")
        rows.append(_row(link.get("law_name_guess") or "", meta, census.get(pid, {}), stored.get(url),
                         folder.name, url, notes))
    if include_unfetched:
        for pid, c in census.items():
            if pid in seen_ids:
                continue
            meta = {"portal_id": pid, "law_number": c.get("law_number"), "legal_status": c.get("legal_status"),
                    "status_source": "portal_listing", "version_as_at": c.get("version_as_at"),
                    "document_kind": (c.get("document_kinds") or "").split(";")[0]}
            rows.append(_row(c.get("title") or "", meta, c, None, folder.name,
                             c.get("document_url") or "", [c.get("not_crawled_reason") or "not in the list"]))
    _mark_use(rows)
    rows.sort(key=lambda r: (r["use"], r["document_kind"], r["law_name"].lower()))
    return rows


def write(rows: list[dict], out: Path) -> Path:
    out = Path(out)
    # utf-8-sig so Excel on Windows shows the portal's punctuation correctly
    with out.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    return out


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("folder", help="a run or corpus folder under outputs/SG/")
    ap.add_argument("--out", help="default: law_table.csv inside the folder")
    ap.add_argument("--all", action="store_true", help="also the listed acts the run did not fetch")
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
