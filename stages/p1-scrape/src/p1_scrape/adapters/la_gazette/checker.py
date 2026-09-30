"""The law table for Lao PDR: one row per law, from a run or corpus folder, with no request sent.

    python -m p1_scrape.adapters.la_gazette.checker <run-or-corpus> [--all] [--out law_table.csv]

Every value comes from files already in the folder — `links_used/laws.csv` (the census of what the portal
listed), the link rows' `contract_meta`, and the manifest (what was actually stored). `--all` adds the laws the
portal lists that this run did not fetch, so a dropped set still appears with its dates and its status.

**What this country can fill in, and what it cannot.** The gazette states a status on **every** row — ປັດຈຸບັນ
(current) or ສະບັບເກົ່າ (old version) — so `in_force` is answered for every law, which is rarer than it sounds:
Malaysia states one for 133 of 1,291. What the portal never states is a **version date**: it publishes as made,
so `version_as_at` is empty everywhere and `effective_date` is the date the gazette published the instrument.

**The amendment linkage is weak here, and the table says so rather than inventing it.** A Lao amending title
("ກົດໝາຍ ວ່າດ້ວຍການປັບປຸງບາງມາດຕາຂອງກົດໝາຍວ່າດ້ວຍ…") names the law it alters *in words*, with no number to join
on, and the portal exposes no link between the two. A pair therefore has to clear three tests, not one: the
target phrase must match the law's title, the amendment must be **dated after** the text it amends, and where
several vintages of one title match, the newest that is still older than the amendment wins. Without the date
test the join produced false links on the real census — a 2024 law given a 2016 "last amendment" from an
instrument the portal itself marks repealed. `amends_title_names` carries what the title actually said, so a
reader can judge the join rather than trust it.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Any, Optional

COLUMNS = ["law_name", "law_number", "portal_id", "document_kind", "use", "in_force", "legal_status",
           "status_source", "effective_date", "last_amended", "last_amending_instrument", "scraped", "doc_id",
           "access_date", "source_url", "file", "run", "notes",
           # Lao PDR's own, after the common ones (CONVENTIONS.md section 2)
           "language", "has_translation", "translation_doc_id", "translation_file", "legal_type_label",
           "listing", "status_word", "made_on", "gazetted_on", "is_revised_version", "agency",
           "amends_title_names", "shared_file_with"]

#: `in_force` is a reading of the portal's own word, never an inference (POLICY.md 3.5, CONVENTIONS.md section 2)
IN_FORCE = {"in_force": "yes", "repealed": "no (repealed)", "not_yet_in_force": "not yet"}

#: The instruments that are linkage rather than text to read (POLICY.md 3.2, CONTRACT.md 3.3)
LINKAGE_KINDS = ("amending_act", "repealing_act", "commencement_instrument")

#: "…of the Law on X" — the words a Lao amending title uses before naming its target. The phrase is cut at a
#: conjunction as well as at punctuation: ມາດຕາ 146 ຂອງກົດໝາຍ ອາຍາ **ແລະ** ມາດຕາ 75 … would otherwise run on
#: and swallow the second article reference into the target's name.
_TARGET_RE = re.compile(r"(?:ຂອງ|ຕໍ່)\s*((?:ກົດໝາຍ|ລັດຖະບັນຍັດ|ດຳລັດ|ຂໍ້ຕົກລົງ)[^,()]*?)(?=\s*(?:ແລະ|ມາດຕາ|$))")


def _read_csv(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    with path.open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def _read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _dated(law: dict) -> str:
    """The date a law takes effect for ordering: the gazette's publication date, its instrument date otherwise."""
    return (law.get("gazetted_on") or law.get("made_on") or "")


#: Where the census is read from, in order of preference. `links_used` is what the crawl actually replayed and
#: is never rewritten (`outputs/README.md` rule 1). `links_rebuilt` is a later list of the **same** portal rows
#: read by a corrected scraper: same addresses, better metadata. When a run carries one, the law table uses it,
#: because the manifest joins on `source_url` and the bytes are unaffected by a classification fix.
LIST_DIRS = ("links_rebuilt", "links_used", "links")


def list_dir_of(run: Path) -> Optional[Path]:
    for name in LIST_DIRS:
        if (run / name / "laws.csv").is_file():
            return run / name
    return None


def rows_for(folder: str | Path, include_all: bool = False) -> list[dict]:
    """One row per law. Without `--all`, only the laws whose document this folder holds."""
    run = Path(folder)
    lists = list_dir_of(run) or (run / "links_used")
    laws = _read_csv(lists / "laws.csv")
    links = _read_jsonl(lists / "documents.jsonl")
    manifest = _read_jsonl(run / "manifest.jsonl") or _read_csv(run / "manifest.csv")
    stored = {str(m.get("source_url")): m for m in manifest if m.get("source_url")}
    meta_by_url = {row.get("url"): (row.get("contract_meta") or {}) for row in links}

    # A file address more than one law points at. Computed here, from the folder's own census, so it is known
    # even when the link list predates the adapter's own flag (`../NOTES.md` 1.3): four pairs on 2026-09-20
    # share a generically named upload, and at most one law of each pair can be the document's real subject.
    claims: dict[str, list[str]] = {}
    for law in laws:
        for url in ((law.get("lao_url") or ""), (law.get("english_url") or "")):
            if url:
                claims.setdefault(url, []).append(law.get("portal_id") or "")

    amendments, targets_of = _amendment_index(laws)
    # the laws whose Lao text this folder really holds, for decision 20's "newer than the principal text we
    # hold" test — an instrument cannot carry wording nothing else carries if we do not have what it amends
    held_lao = {law.get("portal_id") for law in laws if (law.get("lao_url") or "") in stored}

    out = []
    for law in laws:
        lao_url, english_url = (law.get("lao_url") or ""), (law.get("english_url") or "")
        # The two languages are tracked apart. Falling back from a failed Lao fetch to the translation would
        # assert we hold the official text when we hold only the gazette's English rendering of it, and would
        # label an English file `lao` — POLICY.md 3.8 records the language of what was actually fetched.
        doc_lao = stored.get(lao_url) if lao_url else None
        doc_eng = stored.get(english_url) if english_url else None
        if not doc_lao and not doc_eng and not include_all:
            continue
        meta = meta_by_url.get(lao_url) or meta_by_url.get(english_url) or {}
        kind = law.get("document_kind") or "principal_act"
        status = law.get("legal_status") or "unknown"
        shared = [c for c in claims.get(lao_url or english_url, []) if c != law.get("portal_id")]
        last_amended, last_instrument, amend_date = amendments.get(law.get("portal_id") or "", (None, None, None))
        target = targets_of.get(law.get("portal_id") or "")
        holds_target = bool(target and target[0] in held_lao)

        notes = []
        if law.get("not_crawled_reason"):
            notes.append(law["not_crawled_reason"])
        if shared:
            notes.append("another law points at this same file: " + ", ".join(shared))
        if doc_eng and not doc_lao:
            notes.append("only the gazette's English translation was stored; the Lao text, which is the "
                         "document of record, was not")
        if shared:
            notes.append("the portal serves one upload per path, so at most one of these laws is this file's "
                         "subject; read as linkage, not as this law's text")

        out.append({
            "law_name": law.get("title"),
            "law_number": None,                             # the listing carries no act number for any law
            "portal_id": law.get("portal_id"), "document_kind": kind,
            "use": _use(kind, status, doc_lao is not None, doc_eng is not None, _dated(law), amend_date,
                        targets_of.get(law.get("portal_id") or ""), holds_target, bool(shared)),
            "in_force": IN_FORCE.get(status, "not stated"),
            "legal_status": status,
            "status_source": law.get("status_word") and "portal_listing",
            "effective_date": law.get("gazetted_on"),
            "last_amended": last_amended, "last_amending_instrument": last_instrument,
            "scraped": "yes" if doc_lao else ("translation only" if doc_eng else "no"),
            "doc_id": (doc_lao or {}).get("doc_id"), "access_date": (doc_lao or {}).get("access_date"),
            "source_url": lao_url or english_url or None,
            "file": (doc_lao or {}).get("local_path"), "run": run.name,
            "notes": "; ".join(notes),
            "language": "lao" if doc_lao else ("eng" if doc_eng else (meta.get("language") or None)),
            "has_translation": "yes" if english_url else "no",
            "translation_doc_id": (doc_eng or {}).get("doc_id"),
            "translation_file": (doc_eng or {}).get("local_path"),
            "legal_type_label": law.get("legal_type_label"), "listing": law.get("listing"),
            "status_word": law.get("status_word"),
            "made_on": law.get("made_on"), "gazetted_on": law.get("gazetted_on"),
            "is_revised_version": law.get("is_revised_version"), "agency": law.get("agency"),
            "amends_title_names": _target_of(law), "shared_file_with": shared,
        })
    return out


def _target_of(law: dict) -> Optional[str]:
    """What an amending or repealing title says it acts on, in the title's own words. Never a number: the
    portal states none for any instrument."""
    if (law.get("document_kind") or "") not in LINKAGE_KINDS:
        return None
    m = _TARGET_RE.search(law.get("title") or "")
    return m.group(1).strip() if m else None


def _amendment_index(laws: list[dict]) -> tuple[dict[str, tuple[Optional[str], Optional[str], Optional[str]]],
                                                dict[str, tuple[str, str]]]:
    """For each law, the latest instrument that amends it: (year, instrument, that instrument's date).

    Three tests, because the only thing to join on is the words of a title and a wrong link is worse than none
    (the docstring at the top of this file says why, and what a looser join produced on the real census):

    1. the amending title's target phrase must match the law's title from the start, either way round;
    2. the amendment must be **dated after** the law it is attached to — an instrument cannot amend a text that
       did not yet exist, and this alone removed the false pairs;
    3. where several vintages of one title qualify, the amendment attaches to the **newest** text older than
       itself, which is the one it was actually written against.
    """
    targets = []
    for a in laws:
        phrase = _target_of(a)
        if phrase:
            targets.append((a, phrase, _dated(a)))

    out: dict[str, tuple[Optional[str], Optional[str], Optional[str]]] = {}
    targets_of: dict[str, tuple[str, str]] = {}          # instrument -> (the law it acts on, that law's date)
    for a, phrase, a_date in targets:
        candidates = [law for law in laws
                      if (law.get("document_kind") or "") not in LINKAGE_KINDS
                      and (law.get("title") or "").strip()
                      and ((law["title"].startswith(phrase) or phrase.startswith(law["title"])))
                      and _dated(law) and a_date and _dated(law) < a_date]
        if not candidates:
            continue
        target = max(candidates, key=_dated)                      # the newest text this amendment could mean
        pid = target.get("portal_id") or ""
        targets_of[a.get("portal_id") or ""] = (pid, _dated(target))
        held = out.get(pid)
        if held is None or (held[2] or "") < a_date:
            year = (a.get("made_on") or a.get("gazetted_on") or "")[:4] or None
            out[pid] = (year, f"{a.get('portal_id')} {(a.get('title') or '')[:60]}", a_date)
    return out, targets_of


def _use(kind: str, status: str, stored_lao: bool, stored_eng: bool, own_date: str,
         amend_date: Optional[str], target: Optional[tuple], holds_target: bool, disputed: bool) -> str:
    """What a later stage should do with this document (decision 20).

    The vocabulary is fixed — `evidence`, `evidence, text stale`, `linkage`, `linkage, text needed` — plus
    `not held` for a law whose document this folder does not have, as every other country's checker writes.

    - A **disputed file** is one two laws both point at. The portal serves one upload per path, so at most one
      claimant is right and nothing in the census says which. Both are `linkage`: the link is worth keeping,
      the bytes are not safe to read as this law's text. Calling both `evidence` would hand a later stage four
      laws scored against a different instrument (`../NOTES.md` 1.3).
    - An **amending or repealing instrument** is linkage. It becomes `linkage, text needed` only in decision
      20's narrow case: **we hold the principal it acts on, and this instrument is newer than that text**, so
      the instrument carries wording nothing else in the corpus carries. An instrument whose target we cannot
      identify is plain `linkage` — the claim needs a principal to be about.
    - A **repealed text** is not evidence (`POLICY.md` 3.6). It is `linkage`: keep the link, do not read.
    - A text we hold whose **amendment we also hold, dated later**, is `evidence, text stale` — the other side
      of the same pair, which is what decision 20 asks for.
    """
    if not stored_lao and not stored_eng:
        return "not held"
    if disputed:
        return "linkage"
    if kind in LINKAGE_KINDS:
        if target and holds_target and own_date and target[1] and own_date > target[1]:
            return "linkage, text needed"
        return "linkage"
    if status == "repealed":
        return "linkage"
    if amend_date and own_date and amend_date > own_date:
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
    ap.add_argument("folder", help="a run or corpus folder under outputs/LA/")
    ap.add_argument("--all", action="store_true", help="include the laws the portal lists that this folder lacks")
    ap.add_argument("--out", help="where to write (default: <folder>/law_table.csv)")
    a = ap.parse_args(argv)
    rows = rows_for(a.folder, a.all)
    path = write(a.folder, a.all, a.out)
    lists = list_dir_of(Path(a.folder))
    uses: dict[str, int] = {}
    forces: dict[str, int] = {}
    for row in rows:
        uses[row["use"]] = uses.get(row["use"], 0) + 1
        forces[row["in_force"]] = forces.get(row["in_force"], 0) + 1
    scraped = sum(1 for r in rows if r["scraped"] == "yes")
    translation_only = sum(1 for r in rows if r["scraped"] == "translation only")
    amended = sum(1 for r in rows if r["last_amending_instrument"])
    print(f"[checker] LA: {len(rows)} law(s) ({scraped} with the Lao text"
          + (f", {translation_only} with only a translation" if translation_only else "") + "); use: "
          + ", ".join(f"{k} {v}" for k, v in sorted(uses.items()))
          + "; in force: " + ", ".join(f"{k} {v}" for k, v in sorted(forces.items()))
          + f"; {amended} law(s) linked to an amendment"
          + (f"; census from {lists.name}/" if lists else "")
          + f" -> {path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
