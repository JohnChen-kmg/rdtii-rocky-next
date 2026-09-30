"""Content check of a run folder: which stored files are not the law's text, and which fetches failed.

    python tools/audit_run.py <run folder> [--economy MY] [--pages 2]

Reads the run's manifest.jsonl, crawl_log.jsonl and link list (links_rebuilt/, links_used/ or links/ documents.jsonl),
opens every stored file (the first pages of a PDF, the head of an HTML page) and writes audit.json and audit.md beside
the manifest. It changes nothing else. The crawl engine's counts cannot show these problems; reading the first pages
can (countries/my-malaysia/NOTES.md 1.3). Calibrated on the 1,311 files of MY_ws_2026-09-14 (decision 17).

Flags on every economy (no rule set needed):
  fetch_failed        a document the crawl log records as failed and no row stored (listed under "missing")
  store_failed        the bytes arrived but the engine could not write them (a path over Windows' limit; "missing")
  orphan_file         a file under raw/ that no manifest row names (a crawl killed before its checkpoint)
  empty_document      an HTML document whose readable text is almost nothing (the markup is there, the words are not)
  title_not_in_text   fewer than half the law title's distinctive words appear in the file (SG, AU)
  no_text_layer       a PDF whose first pages have no usable text: scanned, OCR needed
  unreadable_file     the file cannot be opened
  duplicate_content   the same bytes stored under two doc_ids in this run
  short_principal     a principal act of at most 4 pages: usually a repeal notice, sometimes a short act
  one_page_principal  a one-page principal-act file whose text does not say "repealed": a notice whose words the
                      rules did not match (OCR), or a scan. Look
A row without a link row (no links_*/documents.jsonl, or a URL not in it) gets its kind from the law number
("Act NNN" a principal act, "Act ANNNN" an amending act); audit.md says how many rows that was.

Flags from the economy's rule set (RULES; Malaysia today). Wrong-file flags:
  html_stored         an HTML page stored where the portal serves documents (a landing page); on a portal where
                      HTML is a form of the law (Australia's framed captures) no rule set says so and nothing is flagged
  other_act_text      the first pages never give the row's act number but do give another act's
  repeal_notice       a short principal-act file whose text says the act is repealed or superseded
  language_mismatch   the text is in a language other than the one the link list recorded (bilingual gazette
                      prints excepted)
  gazette_notice      a gazette notification (P.W. number) stored as a principal act
  not_an_amending_act an amending-act file that is a gazette supplement never naming that act
  parent_not_named    an amendment recorded as a P.U. order whose first pages never name the act it amends
                      (often a bundle of notices, the right one further in)
Informational flags (the text is there, in another form):
  gazette_print       an amending act stored as its gazette print: cover page first, the act from page 2
  subsidiary_amendment an "amending act" row that is a P.U. order, as the portal's amendment listing gives it

Exit 0 when the audit ran (flags are findings, not failures); 1 when the run folder cannot be read.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

LIST_DIRS = ("links_rebuilt", "links_used", "links")
SHORT_PAGES = 4
MIN_TEXT_CHARS = 40
DEFAULT_PAGES = 2



def _jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def _link_rows(run: Path) -> dict[str, dict]:
    for name in LIST_DIRS:
        p = run / name / "documents.jsonl"
        if p.is_file():
            return {r["url"]: r for r in _jsonl(p)}
    return {}


def read_pdf_head(path: Path, pages: int = 1) -> tuple[Optional[int], str, Optional[str]]:
    """(page count, text of the first `pages` pages, error)."""
    try:
        import pypdfium2 as pdfium
    except ImportError as e:  # pragma: no cover - environment problem
        return None, "", f"pypdfium2 missing: {e}"
    try:
        pdf = pdfium.PdfDocument(str(path))
        n = len(pdf)
        text = " ".join(pdf[i].get_textpage().get_text_range() for i in range(min(pages, n)))
        return n, " ".join(text.split()), None
    except Exception as e:  # noqa: BLE001 — an unreadable file is a finding
        return None, "", f"{type(e).__name__}: {e}"


_TAG = re.compile(r"<[^>]+>")
_DROP = re.compile(r"<(script|style|head)\b.*?</\1>", re.I | re.S)
_ENTITY = {"&nbsp;": " ", "&amp;": "&", "&lt;": "<", "&gt;": ">", "&quot;": '"', "&#160;": " ", "&#8217;": "'"}


def read_html_head(path: Path, chars: int = 4000) -> tuple[str, Optional[str]]:
    """The readable text at the start of an HTML document, with the markup taken out.

    Reads enough of the file to get past the boilerplate: the register's epub-derived documents open with a style
    block and a coat-of-arms image, so the first 4 KB of one carries no words at all. `chars` is how much text is
    returned, not how much file is read.
    """
    try:
        raw = path.read_bytes()[:400_000].decode("utf-8", "replace")
    except OSError as e:
        return "", f"{type(e).__name__}: {e}"
    title = re.search(r"<title>(.*?)</title>", raw, re.I | re.S)
    body = re.split(r"<body\b[^>]*>", raw, maxsplit=1, flags=re.I)
    text = _DROP.sub(" ", body[-1])
    text = _TAG.sub(" ", text)
    for entity, ch in _ENTITY.items():
        text = text.replace(entity, ch)
    text = re.sub(r"&[a-zA-Z#0-9]{2,8};", " ", text)
    out = " ".join(text.split())
    if title:
        head = " ".join(_TAG.sub(" ", title.group(1)).split())
        if head and head.lower() not in out[:200].lower():
            out = f"{head} {out}"
    return out[:chars], None


def kind_from_number(number: Any) -> Optional[str]:
    """The document kind a Malaysian-style law number implies, for a row with no link row."""
    n = str(number or "").strip()
    if re.fullmatch(r"Act A\d{1,4}", n, re.I):
        return "amending_act"
    if re.fullmatch(r"Act \d{1,3}", n, re.I):
        return "principal_act"
    return None




def audit_row(row: dict, link: Optional[dict], run: Path, rules: Optional[dict], pages: int) -> dict:
    meta = (link or {}).get("contract_meta") or {}
    kind, kind_source = meta.get("document_kind"), "link_row"
    if link is None:
        kind, kind_source = kind_from_number(row.get("law_number_guess")), "law_number"
    flags: list[str] = []
    evidence = ""
    page_count: Optional[int] = None
    path = run / row["local_path"]
    if row.get("source_type") == "html":
        if rules and rules.get("html_is_a_fault"):
            flags.append("html_stored")
        text, err = read_html_head(path)
        evidence = text[:200]
        if err:
            flags.append("unreadable_file")
            evidence = err
        else:
            if len(text) < MIN_TEXT_CHARS and "html_stored" not in flags:
                flags.append("empty_document")   # where HTML is a fault, html_stored already says so
            elif rules:
                flags = rule_flags(row, meta, kind, None, text, rules, flags)
    else:
        page_count, text, err = read_pdf_head(path, pages)
        if err:
            flags.append("unreadable_file")
            evidence = err
        else:
            evidence = text[:200]
            if len(text) < MIN_TEXT_CHARS:
                flags.append("no_text_layer")
            if kind == "principal_act" and page_count is not None and page_count <= SHORT_PAGES:
                flags.append("short_principal")
            if rules and text and len(text) >= MIN_TEXT_CHARS:
                flags = rule_flags(row, meta, kind, page_count, text, rules, flags)
            explained = {"repeal_notice", "no_text_layer", "as_made_short_act", "short_act_as_printed"}
            if kind == "principal_act" and page_count == 1 and not explained & set(flags):
                flags.append("one_page_principal")   # nothing has explained why one page is the whole act
    return {"doc_id": row["doc_id"], "law_number": row.get("law_number_guess"), "law_name": row.get("law_name_guess"),
            "kind": kind, "kind_source": kind_source if kind else None, "language_recorded": meta.get("language"),
            "page_count": page_count,
            "byte_size": row.get("byte_size"), "flags": flags, "evidence": evidence, "local_path": row["local_path"]}


def title_match(name: Optional[str], text: str, stop: set) -> tuple[int, int]:
    """How many of a law title's distinctive words appear in the text, and how many there are.

    Calibration, 2026-09-16: on Singapore's 739 documents 737 match every word and 2 match four of five; on
    Australia's 1,277, 1,208 match every word once the markup reader works. So a file that carries **less than
    half** of its title's distinctive words is worth looking at, and anything above that is normal drafting
    (a word dropped, an ampersand, a dash).
    """
    words = [w.upper() for w in re.findall(r"[A-Za-z]{3,}", name or "")]
    words = [w for w in words if w not in stop]
    if not words:
        return 0, 0
    haystack = re.sub(r"[^A-Z0-9 ]+", " ", text.upper())
    return sum(1 for w in words if w in haystack), len(words)


def numbers_in(text: str, pattern: "re.Pattern") -> set:
    """Every law number in the text, read twice: as printed, and with the spaces taken out.

    The register's older prints come from OCR that spaces letters and digits ("No. 1 5 o f 1908"), so a pattern
    that only reads the text as printed misses the act's own number and then calls the file another act's text.
    """
    found = {(m.group(1), m.group(2)) for m in pattern.finditer(text)}
    return found | {(m.group(1), m.group(2)) for m in pattern.finditer(re.sub(r"\s+", "", text))}


def rule_flags(row: dict, meta: dict, kind: Optional[str], page_count: Optional[int], text: str, rules: dict,
               generic: Optional[list[str]] = None) -> list[str]:
    """The flags for one row: the generic ones the caller found, as the country's rules leave them."""
    apply = rules.get("apply")
    if apply is not None:
        return apply(row, meta, kind, page_count, text, rules, list(generic or []))
    return list(generic or [])


def _my_flags(row: dict, meta: dict, kind: Optional[str], page_count: Optional[int], text: str, rules: dict,
              flags: list[str]) -> list[str]:
    number = re.sub(r"^\s*Act\s+", "", str(row.get("law_number_guess") or ""), flags=re.I).strip().upper()
    numbers = {m.group(1).replace(" ", "").upper() for m in rules["act_number"].finditer(text)}
    head = text[:800]
    cover = bool(rules["gazette_cover"].search(head))
    if kind in ("principal_act", "amending_act") and rules["number_form"].match(number):
        if number not in numbers and numbers - {number}:
            flags.append("other_act_text")
    if kind == "principal_act" and page_count is not None and page_count <= SHORT_PAGES and rules["repeal"].search(text):
        flags.append("repeal_notice")
    if kind == "principal_act" and cover and rules["gazette_notice"].search(head):
        flags.append("gazette_notice")
    if kind == "amending_act":
        if rules["number_form"].match(number) and cover:
            flags = [f for f in flags if f != "other_act_text"]
            flags.append("gazette_print" if number in numbers else "not_an_amending_act")
        if not number and (cover or rules["pu_number"].search(head)):
            flags.append("subsidiary_amendment")
            m = rules["parent_name"].match(str(row.get("law_name_guess") or "").strip())
            if m:
                words = [w for w in re.findall(r"[A-Za-z]+", m.group(1)) if w.upper() not in ("ACT", "THE", "OF", "AND")][:2]
                if words and not any(w.upper() in text.upper() for w in words):
                    flags.append("parent_not_named")
    recorded = meta.get("language")
    if recorded and recorded in rules["languages"] and not cover:
        own = rules["languages"][recorded].search(head)
        others = [lang for lang, rx in rules["languages"].items() if lang != recorded and rx.search(head)]
        if others and not own:
            flags.append("language_mismatch")
    return flags


def _sg_flags(row: dict, meta: dict, kind: Optional[str], page_count: Optional[int], text: str, rules: dict,
              flags: list[str]) -> list[str]:
    """Singapore. Statutes Online prints every document to one of four patterns, which is what makes this checkable:

    - a revised edition opens `THE STATUTES OF THE REPUBLIC OF SINGAPORE`, the title, `<YYYY> REVISED EDITION`;
    - an act passed since the 2020 revision opens with the title and `(No. N of YYYY)`;
    - subsidiary legislation opens `First published in the Government Gazette …`, `No. S <n>`, then its parent act;
    - an act as passed is printed in the `ACTS SUPPLEMENT` to the gazette.
    """
    head = text[:1200]
    hit, total = title_match(row.get("law_name_guess"), text, rules["stop"])
    if total and hit * 2 < total:
        flags.append("title_not_in_text")

    number = str(row.get("law_number_guess") or "")
    if kind in ("principal_act", "amending_act"):
        want = rules["row_number"].search(number)
        mine = (want.group(1), want.group(2)) if want else None
        on_page = {(m.group(1), m.group(2)) for m in rules["act_number"].finditer(head)}
        if mine and on_page and mine not in on_page:
            flags.append("other_act_text")
    if kind == "subsidiary_legislation":
        m, want = rules["sl_number"].search(head), rules["sl_number_row"].search(number)
        if m and want and m.group(1) != want.group(1):
            flags.append("other_act_text")

    name = str(row.get("law_name_guess") or "")
    is_repeal_act = bool(rules["repeal_act"].search(name))
    if (kind == "principal_act" and page_count is not None and page_count <= SHORT_PAGES
            and rules["repeal"].search(text) and not is_repeal_act):
        flags.append("repeal_notice")
    # a short act that opens with its own title and either the statutes print or its arrangement of sections is
    # the whole act: the Supply Acts and the Pensions (Expatriate Officers) Act are four pages of law
    if "short_principal" in flags and hit == total and (rules["statutes_print"].search(head)
                                                        or rules["arrangement"].search(head)):
        flags = [f for f in flags if f != "short_principal"]
        flags.append("short_act_as_printed")
    if kind == "amending_act" and rules["acts_supplement"].search(head):
        flags.append("gazette_print")                 # the form the portal publishes an act in, not a fault
    if kind == "principal_act" and rules["acts_supplement"].search(head):
        flags.append("act_as_passed")                 # the supplement print, not the consolidated text
    return flags


def _au_flags(row: dict, meta: dict, kind: Optional[str], page_count: Optional[int], text: str, rules: dict,
              flags: list[str]) -> list[str]:
    """Australia. Two shapes: a compilation unpacked from the register's epub, which opens with the title, and an
    act as made, which opens with the title, `No. N of YYYY` and `An Act to …`.

    The register's as-made prints are often three or four pages, so the generic `short_principal` fires on 89 of
    them. Where the page names the act and its number and says what it does, that is the whole act and the flag is
    replaced by `as_made_short_act`, which is informational.
    """
    head = text[:1500]
    hit, total = title_match(row.get("law_name_guess"), text, rules["stop"])
    if total and hit * 2 < total:
        flags.append("title_not_in_text")

    number = str(row.get("law_number_guess") or "")
    on_page = numbers_in(head, rules["act_number"])
    want = rules["row_number"].search(number)
    mine = (want.group(1), want.group(2)) if want else None
    numbers_agree = bool(mine and mine in on_page)
    # the first number on a page is often the act being amended ("An Act to amend the Commonwealth Banks Act
    # 1959-1968"), so a mismatch is only a finding when this act's own number is nowhere on the page
    if mine and not numbers_agree and on_page:
        flags.append("other_act_text")
    if "title_not_in_text" in flags and numbers_agree:
        # the right act under the name it was enacted with: six of these, renamed since (the Flags Act 1953 is
        # printed as FLAGS, No. 1 of 1954)
        flags = [f for f in flags if f != "title_not_in_text"]
        flags.append("renamed_since_enactment")
    if "short_principal" in flags and numbers_agree:
        flags = [f for f in flags if f != "short_principal"]
        flags.append("as_made_short_act")
    return flags



def _tl_flags(row: dict, meta: dict, kind: Optional[str], page_count: Optional[int], text: str, rules: dict,
              flags: list[str]) -> list[str]:
    """Timor-Leste. The portal serves **two shapes**, and the checks differ by shape.

    Most documents are a **gazette issue**: it opens with the masthead "Jornal da República" and a `SUMÁRIO`
    naming the acts inside, and it can carry several acts (`contract_meta.contains`). A minority are **per-law
    extracts** at addresses like `2002_2005/leis_parlamento_nacional/6_2005.pdf`, which carry one act and no
    masthead — 105 of them were flagged as "not a gazette issue" before this rule knew the difference
    (2026-09-20).

    A one-page document is normal here (a short decree fills one page), so it is not flagged. What is worth a
    person's time: a file that is neither shape, an issue with no contents page, and an issue that does not
    contain the acts the listing promised.
    """
    url = str(row.get("source_url") or "")
    head = text[:2500]
    per_law = bool(rules["per_law_path"].search(url))
    if not text.strip():
        return flags                                    # a scan: the generic no_text_layer flag already says so

    if per_law:
        hit, total = title_match(row.get("law_name_guess"), text, rules["stop"])
        if total and hit * 2 < total:
            flags.append("act_not_in_text")             # a single-act file that is not the act it claims
        return flags

    if not rules["masthead"].search(head):
        flags.append("not_a_gazette_issue")             # neither an issue nor a per-law extract
        return flags
    if not rules["sumario"].search(head):
        flags.append("no_sumario")                      # an issue whose contents page is missing or unreadable
        return flags
    named = [t for t in (meta.get("contains_titles") or [])[:6] if t]
    if named and not any(title_match(t, text, rules["stop"])[0] >= 2 for t in named):
        flags.append("acts_not_in_text")                # the issue does not contain the acts the listing promised
    return flags


RULES: dict[str, dict[str, Any]] = {
    "MY": {
        # an act number: "Act 709", "Akta A1727"; a year after "Act" ("Revision of Laws Act 1968") is not one
        "act_number": re.compile(r"\b(?:Act|Akta)\s+(A\s?\d{1,4}|\d{1,3})(?!\d)", re.I),
        "number_form": re.compile(r"^A?\d{1,4}$"),
        "repeal": re.compile(r"repealed by|dimansuhkan|superseded by|diganti oleh|ceased to|terhenti", re.I),
        "gazette_notice": re.compile(r"P\.W\.\s*\d+|PEMBERITAHUAN", re.I),
        "gazette_cover": re.compile(r"WARTA KERAJAAN|GOVERNMENT GAZETTE|TAMBAHAN No\.", re.I),
        "pu_number": re.compile(r"P\.U\. \((?:A|B)\)\s*\d+", re.I),
        "parent_name": re.compile(r"^Amendment of (.+?)(?:\s*\(\d{2} \w{3} \d{4}\))?$", re.I),
        "html_is_a_fault": True,  # lom serves PDFs; an HTML page stored as a document is a landing page
        "languages": {
            "msa": re.compile(r"UNDANG-UNDANG MALAYSIA|\bAKTA\b|SEBAGAIMANA PADA|CETAKAN SEMULA|DIMANSUHKAN", re.I),
            "eng": re.compile(r"LAWS OF MALAYSIA|\bAS AT\b|\bACT\b|REPRINT|REPEALED", re.I),
        },
        "apply": _my_flags,
    },
    "SG": {
        "act_number": re.compile(r"\(?No\.\s*(\d{1,3})\s+of\s+(\d{4})\)?", re.I),
        "sl_number": re.compile(r"\bNo\.\s*S\s*(\d{1,4})\b", re.I),
        "sl_number_row": re.compile(r"\bS\s*(\d{1,4})\s*/", re.I),
        "row_number": re.compile(r"(?:Act\s+)?(\d{1,3})\s+of\s+(\d{4})", re.I),
        "statutes_print": re.compile(r"THE STATUTES OF THE REPUBLIC OF SINGAPORE", re.I),
        "arrangement": re.compile(r"ARRANGEMENT OF (SECTIONS|REGULATIONS|RULES|ORDERS|PARAGRAPHS)", re.I),
        "acts_supplement": re.compile(r"ACTS SUPPLEMENT", re.I),
        "repeal": re.compile(r"\(REPEALED\)|repealed by|\bRepeal of\b", re.I),
        # an act whose own job is to repeal another is not a repeal notice stored in place of an act
        "repeal_act": re.compile(r"\(Repeal\)|\bRepeal Act\b", re.I),
        "html_is_a_fault": True,   # SSO serves PDFs today; when the markup fallback lands, set this False
        "stop": {"ACT", "ACTS", "THE", "AND", "FOR", "REGULATIONS", "REGULATION", "ORDER", "ORDERS", "RULES",
                 "NOTIFICATION", "AMENDMENT", "REPEALED", "CHAPTER", "SINGAPORE"},
        "apply": _sg_flags,
    },
    "TL": {
        "masthead": re.compile(r"Jornal\s+da\s+Rep[uú]blica", re.I),
        # a per-law extract, not an issue: .../2002_2005/leis_parlamento_nacional/6_2005.pdf
        "per_law_path": re.compile(r"/(leis_parlamento_nacional|decreto_lei_governo|decreto_governo|"
                                   r"resolucao_[a-z_]+|decreto_presidente[a-z_]*)/", re.I),
        "sumario": re.compile(r"SUM[ÁA]RIO", re.I),
        "act_number": re.compile(r"N\.?\s*[º°o]?\s*(\d{1,3})\s*/\s*(\d{4})", re.I),
        "html_is_a_fault": True,      # the gazette serves PDFs; an HTML page stored as a document is a landing page
        "stop": {"LEI", "LEIS", "DECRETO", "DECRETOS", "RESOLUCAO", "RESOLUCOES", "DO", "DA", "DE", "DOS", "DAS",
                 "E", "O", "A", "SOBRE", "PRIMEIRA", "SEGUNDA", "ALTERACAO", "APROVA", "REGIME", "JURIDICO",
                 "GOVERNO", "PARLAMENTO", "NACIONAL", "REPUBLICA"},
        "apply": _tl_flags,
    },
    "AU": {
        # "No. 110, 1999", "No . 18 of 1973" and the bare "73 of 2006" a compilation cover uses
        "act_number": re.compile(r"(?:No\s*\.\s*)?(\d{1,3})\s*(?:of|,)\s*(\d{4})", re.I),
        "row_number": re.compile(r"No\.\s*(\d{1,3})\s*,\s*(\d{4})", re.I),
        "html_is_a_fault": False,  # the register publishes epubs; our HTML is the unpacked text, by design
        "stop": {"ACT", "ACTS", "THE", "AND", "FOR", "AUSTRALIA", "AUSTRALIAN", "COMMONWEALTH", "AMENDMENT",
                 "REGULATIONS", "REGULATION", "RULES", "DETERMINATION", "INSTRUMENT"},
        "apply": _au_flags,
    },
}


def audit(run: Path, economy: Optional[str] = None, pages: int = DEFAULT_PAGES) -> dict:
    manifest = _jsonl(run / "manifest.jsonl")
    if not manifest and not (run / "crawl_log.jsonl").is_file():
        raise FileNotFoundError(f"{run}: no manifest.jsonl and no crawl_log.jsonl")
    economy = (economy or (manifest[0].get("economy") if manifest else None) or "").upper()
    rules = RULES.get(economy)
    links = _link_rows(run)
    rows = [audit_row(m, links.get(m["source_url"]), run, rules, pages) for m in manifest]
    by_sha: dict[str, list[str]] = {}
    for m in manifest:
        by_sha.setdefault(m.get("content_sha256") or "", []).append(m["doc_id"])
    for r, m in zip(rows, manifest):
        if len(by_sha.get(m.get("content_sha256") or "", [])) > 1:
            r["flags"].append("duplicate_content")
    stored_urls = {m["source_url"] for m in manifest}
    failed: dict[str, dict] = {}   # by URL, the last entry: a fetch that failed and then succeeded is not missing
    for e in _jsonl(run / "crawl_log.jsonl"):
        url = e.get("url") or ""
        if e.get("outcome") in ("ok", "duplicate") or url in stored_urls:
            continue
        link = links.get(url)
        note = " ".join(str(e.get("note") or "").split())
        # the bytes arrived but the engine could not write them (a path over Windows' limit, a full disk): the
        # document is missing all the same, but the portal is not the cause
        store_error = e.get("outcome") == "error" and note.startswith("store ")
        failed[url] = {"url": url, "law": (link or {}).get("law_name_guess"), "law_number": (link or {}).get("law_number_guess"),
                       "status": e.get("status"), "outcome": e.get("outcome"), "note": note[:160],
                       "flags": ["store_failed" if store_error else "fetch_failed"]}
    missing = list(failed.values())
    orphans = orphan_files(run, manifest)
    no_link = sum(1 for m in manifest if m["source_url"] not in links)
    counts: dict[str, int] = {}
    for r in rows + missing:
        for f in r["flags"]:
            counts[f] = counts.get(f, 0) + 1
    if orphans:
        counts["orphan_file"] = len(orphans)
    return {"run": run.name, "economy": economy, "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "pages_read": pages, "rules": economy if rules else None,
            "summary": {"documents": len(rows), "flagged": sum(1 for r in rows if r["flags"]), "missing": len(missing),
                        "orphan_files": len(orphans), "without_link_row": no_link, "by_flag": counts},
            "rows": rows, "missing": missing, "orphans": orphans}


def orphan_files(run: Path, manifest: list[dict]) -> list[dict]:
    """Files under raw/ that no manifest row names: written by a crawl that was killed before its next
    checkpoint (the engine writes the manifest every 10 stored documents). Not part of the run's output; the
    next resume fetches those documents again."""
    raw = run / "raw"
    if not raw.is_dir():
        return []
    named = set()
    for m in manifest:
        for key in ("local_path", "http_headers_path"):
            if m.get(key):
                named.add(str(m[key]).replace("\\", "/").lstrip("./"))
    orphans = []
    for path in sorted(raw.rglob("*")):
        if path.is_file():
            rel = path.relative_to(run).as_posix()
            if rel not in named:
                orphans.append({"path": rel, "folder": path.parent.name, "bytes": path.stat().st_size})
    return orphans


def to_markdown(result: dict) -> str:
    s = result["summary"]
    orphans = result.get("orphans") or []
    lines = [f"# Content check: {result['run']}", "",
             f"{s['documents']} stored documents read (first {result['pages_read']} page(s) each), "
             f"**{s['flagged']} flagged**, **{s['missing']} missing** (failed fetches or stores, never in the manifest). Rules: "
             f"{result['rules'] or 'generic only'}. "
             + (f"{s['without_link_row']} rows have no link row (their kind comes from the law number). " if s.get("without_link_row") else "")
             + (f"{len(orphans)} files under raw/ belong to no manifest row. " if orphans else "")
             + f"Generated {result['generated_at']}.", ""]
    if s["by_flag"]:
        lines += ["| Flag | Rows |", "| :---- | ----: |"] + [f"| `{k}` | {v} |" for k, v in sorted(s["by_flag"].items())] + [""]
    flagged = [r for r in result["rows"] if r["flags"]]
    if flagged:
        lines += ["## Flagged documents", "", "| doc_id | Law | Kind | Pages | Flags | First page |",
                  "| :---- | :---- | :---- | ----: | :---- | :---- |"]
        for r in flagged:
            law = f"{r['law_number'] or ''}: {(r['law_name'] or '')[:60]}".strip(": ")
            lines.append(f"| {r['doc_id']} | {_cell(law)} | {r['kind'] or ''} | {r['page_count'] or ''} | "
                         f"{', '.join(r['flags'])} | {_cell(r['evidence'][:110])} |")
        lines.append("")
    if result["missing"]:
        lines += ["## Missing: fetches or stores that failed", "", "| Law | HTTP | Outcome | Flag | Address | Log note |",
                  "| :---- | :---- | :---- | :---- | :---- | :---- |"]
        for m in result["missing"]:
            lines.append(f"| {_cell((m.get('law_number') or '') + ' ' + (m.get('law') or ''))} | {m.get('status') or ''} | "
                         f"{m.get('outcome') or ''} | {', '.join(m.get('flags') or [])} | {m.get('url')} | {_cell(m.get('note'))} |")
        lines.append("")
    if orphans:
        lines += ["## Orphan files: under raw/ but in no manifest row", "",
                  "Written by a crawl that was stopped before its next checkpoint (the engine writes the manifest every "
                  "10 stored documents). They are not part of the run's output; a resume fetches these documents again.", "",
                  "| Folder | File | Bytes |", "| :---- | :---- | ----: |"]
        for o in orphans:
            lines.append(f"| {_cell(o['folder'])} | {_cell(o['path'])} | {o['bytes']} |")
        lines.append("")
    if not flagged and not result["missing"] and not orphans:
        lines += ["Nothing flagged.", ""]
    return "\n".join(lines)


def _cell(text: Any) -> str:
    return " ".join(str(text or "").split()).replace("|", "\\|")


def write(result: dict, run: Path) -> dict[str, str]:
    (run / "audit.json").write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    (run / "audit.md").write_text(to_markdown(result), encoding="utf-8", newline="\n")
    return {"audit.json": str(run / "audit.json"), "audit.md": str(run / "audit.md")}


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("run", help="the run folder (outputs/<CC>/<CC>_ws_<date>)")
    ap.add_argument("--economy", help="rule set to apply; default: the manifest's economy")
    ap.add_argument("--pages", type=int, default=DEFAULT_PAGES, help="pages of each PDF to read (default 2)")
    args = ap.parse_args(argv)
    run = Path(args.run)
    try:
        result = audit(run, args.economy, max(1, args.pages))
    except FileNotFoundError as e:
        print(f"[audit] {e}", flush=True)
        return 1
    paths = write(result, run)
    s = result["summary"]
    print(f"[audit] {run.name}: {s['documents']} documents, {s['flagged']} flagged, {s['missing']} missing; "
          f"{s['by_flag']} -> {paths['audit.md']}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
