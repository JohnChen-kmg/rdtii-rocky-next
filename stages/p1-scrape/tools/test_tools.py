"""Offline tests for tools/audit_run.py and tools/merge_corpus.py on hand-made run folders with hand-made PDFs.

Run from the stage root (the tools sit in tools/ there): python -m pytest -q tests/test_tools.py
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve().parent
for cand in (_HERE.parent / "tools", _HERE):
    if (cand / "audit_run.py").is_file():
        sys.path.insert(0, str(cand))
        break
import audit_run  # noqa: E402
import merge_corpus  # noqa: E402

from p1_scrape.models import MANIFEST_FIELDS  # noqa: E402


# --- a PDF with real text, written by hand -----------------------------------------------------------------------

def _esc(s: str) -> str:
    return s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def make_pdf(pages: list[str]) -> bytes:
    """One page per entry; each entry's lines become text lines pdfium can extract (Helvetica, no embedding)."""
    n = len(pages)
    page_ids = [3 + 2 * i for i in range(n)]
    font_id = 3 + 2 * n
    objs: list[bytes] = [b"<< /Type /Catalog /Pages 2 0 R >>",
                         f"<< /Type /Pages /Kids [{' '.join(f'{p} 0 R' for p in page_ids)}] /Count {n} >>".encode()]
    for i, text in enumerate(pages):
        cid = page_ids[i] + 1
        objs.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents {cid} 0 R "
                    f"/Resources << /Font << /F1 {font_id} 0 R >> >> >>".encode())
        stream = "BT /F1 12 Tf 72 720 Td 14 TL " + " ".join(f"({_esc(line)}) Tj T*" for line in text.split("\n")) + " ET"
        objs.append(f"<< /Length {len(stream)} >>\nstream\n{stream}\nendstream".encode())
    objs.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for i, o in enumerate(objs, start=1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n".encode() + o + b"\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode()
    for off in offsets:
        out += f"{off:010d} 00000 n \n".encode()
    out += f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    return bytes(out)


def test_the_hand_made_pdf_yields_its_text_and_page_count(tmp_path):
    p = tmp_path / "x.pdf"
    p.write_bytes(make_pdf(["LAWS OF MALAYSIA\nAct 709\nPERSONAL DATA PROTECTION ACT 2010", "page two"]))
    n, text, err = audit_run.read_pdf_head(p)
    assert err is None and n == 2 and "LAWS OF MALAYSIA Act 709" in text


# --- a run folder with documents, link rows, a manifest and a crawl log -------------------------------------------

def _row(**kw) -> dict:
    base = {k: None for k in MANIFEST_FIELDS}
    base.update({"contract_version": "0.2.0", "economy": "MY", "access_date": "2026-09-01T07:00:00Z",
                 "source_type": "pdf_native", "pdf_is_scanned": False, "retrieval_method": "requests",
                 "http_status": 200, "content_type": "application/pdf", "page_count": 1})
    base.update(kw)
    return base


DOCS = {
    # key: (doc_id, law_number, law_name, kind, language, url, pages of text, source_type)
    "pdpa": ("my-pdpa2010-001", "Act 709", "Personal Data Protection Act 2010", "principal_act", "eng",
             "https://lom.agc.gov.my/x/ACT%20709-REPRINT%202023.pdf",
             ["LAWS OF MALAYSIA\nREPRINT\nAct 709\nPERSONAL DATA PROTECTION ACT 2010\nAs at 1 July 2023", "2", "3", "4", "5", "6"], "pdf_native"),
    "notice": ("my-aa1976-001", "Act 168", "ANTIQUITIES ACT 1976", "principal_act", "eng",
               "https://lom.agc.gov.my/x/Act%20168.pdf",
               ["LAWS OF MALAYSIA\nAct 168\nANTIQUITIES ACT 1976\n(Repealed by the National Heritage Act 2005 [Act 645])"], "pdf_native"),
    "wrong": ("my-wpa2009-001", "Act 696", "WITNESS PROTECTION ACT 2009", "principal_act", "eng",
              "https://lom.agc.gov.my/x/Act%20695%20(Reprint%202019).pdf",
              ["LAWS OF MALAYSIA\nREPRINT\nAct 695\nJUDICIAL APPOINTMENTS COMMISSION ACT 2009\nAs at 1 September 2019"] + ["p"] * 24, "pdf_native"),
    "malay": ("my-egaa2007-001", "Act 680", "ELECTRONIC GOVERNMENT ACTIVITIES ACT 2007", "principal_act", "eng",
              "https://lom.agc.gov.my/x/Akta%20680%20BM.pdf",
              ["UNDANG-UNDANG MALAYSIA\nCETAKAN SEMULA\nAkta 680\nAKTA AKTIVITI KERAJAAN ELEKTRONIK 2007\nSebagaimana pada 1 November 2017"] + ["p"] * 24, "pdf_native"),
    "amend": ("my-pdpa2024-001", "Act A1727", "Personal Data Protection (Amendment) Act 2024", "amending_act", "eng",
              "https://lom.agc.gov.my/x/Act%20A1727.pdf",
              ["LAWS OF MALAYSIA\nAct A1727\nPERSONAL DATA PROTECTION (AMENDMENT) ACT 2024"] + ["p"] * 10, "pdf_native"),
    "supp": ("my-aqsa2016-001", None, "Amendment of QUANTITY SURVEYORS ACT 1967 (07 Jun 2016)", "amending_act", None,
             "https://lom.agc.gov.my/x/Pub011(75)y2016.pdf",
             ["MALAYSIA\nWarta Kerajaan\n7hb Jun 2016 TAMBAHAN No. 75\nPERUNDANGAN (B)\nP.U. (B) 272"] + ["p"] * 3, "pdf_native"),
    "gaz_ok": ("my-aa2013-001", "Act A1452", "ANIMALS (AMENDMENT) ACT 2013", "amending_act", "eng",
               "https://lom.agc.gov.my/x/11.%20Act%20A%201452_unlocked.pdf",
               ["M A L A Y S I A\nWarta Kerajaan\nHIS MAJESTY'S GOVERNMENT GAZETTE\nJil. 57 No. 6 TAMBAHAN No. 7 AKTA 20hb Mac 2013\nNo. Tajuk ringkas/Short title Akta A1452 Animals (Amendment) Act 2013",
                "Animals (Amendment) 1\nLAWS OF MALAYSIA\nAct A1452\nANIMALS (AMENDMENT) ACT 2013"] + ["p"] * 33, "pdf_native"),
    "gaz_wrong": ("my-jra2011-001", "Act A1412", "JUDGES' REMUNERATION (AMENDMENT) (NO. 2) ACT 2011", "amending_act", "eng",
                  "https://lom.agc.gov.my/x/ACT%20A1412.pdf",
                  ["M A L A Y S I A\nWarta Kerajaan\nHIS MAJESTY'S GOVERNMENT GAZETTE\nJil. 55 No. 26 TAMBAHAN No. 14 AKTA\nAkta A1409 Pensions (Amendment) Act 2011",
                   "Pensions (Amendment) 1\nLAWS OF MALAYSIA\nAct A1409\nPENSIONS (AMENDMENT) ACT 2011"] + ["p"] * 3, "pdf_native"),
    "html": ("my-pdpcp2017-001", None, "PDP Code of Practice for the Banking Sector", None, None,
             "https://www.pdp.gov.my/code/", None, "html"),
    "scan": ("my-cia1950-001", "Act 5", "COMMISSIONS OF ENQUIRY ACT 1950", "principal_act", "eng",
             "https://lom.agc.gov.my/x/Act%205.pdf", [""] * 12, "pdf_scanned"),
}


def make_run(root: Path, name: str, keys: list[str], started: str, failed: tuple = (), overrides: dict | None = None,
             audit_flags: dict | None = None, portal_ids: bool = True) -> Path:
    run = root / name
    (run / "links_used").mkdir(parents=True)
    rows, links, log = [], [], []
    for i, key in enumerate(keys, start=1):
        doc_id, number, law_name, kind, lang, url, pages, stype = DOCS[key]
        if overrides and key in overrides:
            o = overrides[key]
            url, pages, doc_id = o.get("url", url), o.get("pages", pages), o.get("doc_id", doc_id)
            number, law_name = o.get("number", number), o.get("law_name", law_name)
        folder = run / "raw" / "my" / key
        folder.mkdir(parents=True)
        if stype == "html":
            path = folder / f"{started[:10].replace('-', '')}__page.html"
            path.write_text("<html><head><title>Landing page</title></head><body>download</body></html>", encoding="utf-8")
        else:
            path = folder / f"{started[:10].replace('-', '')}__native.pdf"
            path.write_bytes(make_pdf(pages))
        headers = Path(str(path) + ".headers.json")
        headers.write_text(json.dumps({"response_headers": {"ETag": f'"e{i}"'}}), encoding="utf-8")
        rel = path.relative_to(run).as_posix()
        rows.append(_row(doc_id=doc_id, source_url=url, local_path=rel, http_headers_path=rel + ".headers.json",
                         law_name_guess=law_name, law_number_guess=number, source_type=stype,
                         pdf_is_scanned=None if stype == "html" else (stype == "pdf_scanned"),
                         content_type="text/html" if stype == "html" else "application/pdf",
                         content_sha256=hashlib.sha256(path.read_bytes()).hexdigest(), byte_size=path.stat().st_size,
                         page_count=None if stype == "html" else len(pages), access_date=started,
                         http={"headers": {"ETag": f'"e{i}"'}}))
        links.append({"url": url, "economy": "MY", "law_name_guess": law_name, "law_number_guess": number, "order": i,
                      "scopes": ["all"], "contract_meta": {"portal_id": ((number or "").replace("Act ", "") or None) if portal_ids else None,
                                                           "document_kind": kind, "language": lang}})
        log.append({"ts": started, "url": url, "host": "lom.agc.gov.my", "outcome": "ok", "status": 200, "note": law_name})
    for url, note in failed:
        log.append({"ts": started, "url": url, "host": "lom.agc.gov.my", "outcome": "failed", "status": 500,
                    "retrieval_method": "playwright", "note": note})
        links.append({"url": url, "economy": "MY", "law_name_guess": note, "law_number_guess": "Act 175", "order": 99,
                      "scopes": ["all"], "contract_meta": {"portal_id": "175", "document_kind": "principal_act", "language": "eng"}})
    from p1_scrape.manifest import write_manifest
    write_manifest(rows, run)
    (run / "crawl_log.jsonl").write_text("".join(json.dumps(e) + "\n" for e in log), encoding="utf-8")
    (run / "crawl_status.json").write_text(json.dumps({"started_at": started, "state": "done"}), encoding="utf-8")
    (run / "links_used" / "documents.jsonl").write_text("".join(json.dumps(l) + "\n" for l in links), encoding="utf-8")
    (run / "links_used" / "laws.csv").write_text("listing,portal_id\nupdated,709\n", encoding="utf-8")
    (run / "links_used" / "catalogue_meta.json").write_text(json.dumps({"cfg_sha256": "abc", "rule_id": "r", "settings": {}}), encoding="utf-8")
    if audit_flags:
        (run / "audit.json").write_text(json.dumps({"rows": [{"doc_id": d, "flags": f} for d, f in audit_flags.items()]}), encoding="utf-8")
    return run


@pytest.fixture()
def crawl(tmp_path):
    return make_run(tmp_path, "MY_ws_2026-09-01", list(DOCS), "2026-09-01T07:00:00Z",
                    failed=(("https://lom.agc.gov.my/x/Act%20175%20original.pdf", "TRADE MARKS ACT 1976"),))


# --- the audit ----------------------------------------------------------------------------------------------------

def test_the_audit_flags_notices_wrong_files_wrong_language_scans_and_landing_pages(crawl):
    result = audit_run.audit(crawl)
    flags = {r["doc_id"]: r["flags"] for r in result["rows"]}
    assert flags["my-pdpa2010-001"] == []
    assert set(flags["my-aa1976-001"]) == {"short_principal", "repeal_notice"}
    assert flags["my-wpa2009-001"] == ["other_act_text"]
    assert flags["my-egaa2007-001"] == ["language_mismatch"]
    assert flags["my-pdpa2024-001"] == []
    assert set(flags["my-aqsa2016-001"]) == {"subsidiary_amendment", "parent_not_named"}
    assert flags["my-aa2013-001"] == ["gazette_print"]
    assert flags["my-jra2011-001"] == ["not_an_amending_act"]
    assert flags["my-pdpcp2017-001"] == ["html_stored"]
    assert flags["my-cia1950-001"] == ["no_text_layer"]
    assert result["summary"]["flagged"] == 8 and result["summary"]["missing"] == 1
    assert result["missing"][0]["status"] == 500 and result["missing"][0]["law_number"] == "Act 175"
    assert result["rules"] == "MY" and result["summary"]["by_flag"]["fetch_failed"] == 1


def test_the_audit_writes_json_and_markdown_beside_the_manifest_and_the_cli_exits_0(crawl, capsys):
    rc = audit_run.main([str(crawl)])
    assert rc == 0 and (crawl / "audit.json").is_file()
    md = (crawl / "audit.md").read_text(encoding="utf-8")
    assert "**8 flagged**" in md and "my-wpa2009-001" in md and "TRADE MARKS ACT 1976" in md and "Act 695" in md
    assert "8 flagged, 1 missing" in capsys.readouterr().out
    assert audit_run.main([str(crawl / "nowhere")]) == 1


def test_without_a_rule_set_only_the_generic_flags_apply(crawl):
    result = audit_run.audit(crawl, economy="ZZ")          # an economy no rule set covers
    flags = {r["doc_id"]: r["flags"] for r in result["rows"]}
    assert flags["my-wpa2009-001"] == [] and flags["my-egaa2007-001"] == [] and flags["my-jra2011-001"] == []
    # without the repeal words, a one-page principal act is only something to look at
    assert set(flags["my-aa1976-001"]) == {"short_principal", "one_page_principal"} and flags["my-cia1950-001"] == ["no_text_layer"]
    # HTML is a fault only where a rule set says so, but a stored page with almost no text is a finding anywhere:
    # that is how a landing page is caught in a country whose rules are not written yet
    assert flags["my-pdpcp2017-001"] == ["empty_document"]
    assert result["rules"] is None


def test_the_same_bytes_under_two_doc_ids_are_flagged(tmp_path):
    run = make_run(tmp_path, "MY_ws_2026-09-02", ["pdpa", "amend"], "2026-09-02T07:00:00Z",
                   overrides={"amend": {"pages": DOCS["pdpa"][6]}})
    flags = {r["doc_id"]: r["flags"] for r in audit_run.audit(run)["rows"]}
    assert "duplicate_content" in flags["my-pdpa2010-001"] and "duplicate_content" in flags["my-pdpa2024-001"]


# --- the corpus merge ---------------------------------------------------------------------------------------------

def test_the_corpus_takes_the_newest_copy_of_each_law_and_records_what_it_replaced(tmp_path, crawl):
    audit_run.main([str(crawl)])
    new_pages = ["LAWS OF MALAYSIA\nREPRINT\nAct 709\nPERSONAL DATA PROTECTION ACT 2010\nAs at 1 August 2026"] + ["p"] * 7
    delta = make_run(tmp_path, "MY_ws_2026-09-01_to_2026-09-20", ["pdpa"], "2026-09-20T07:00:00Z",
                     overrides={"pdpa": {"url": "https://lom.agc.gov.my/x/ACT%20709-REPRINT%202026.pdf", "pages": new_pages}})
    audit_run.main([str(delta)])
    out = tmp_path / "MY_corpus_2026-09-21"
    meta = merge_corpus.merge(tmp_path, out, "MY")
    assert meta["validation"]["ok"] and meta["documents"] == len(DOCS) and meta["superseded"] == 1
    assert meta["runs"] == ["MY_ws_2026-09-01_to_2026-09-20", "MY_ws_2026-09-01"]
    rows = {json.loads(l)["doc_id"]: json.loads(l) for l in (out / "manifest.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()}
    pdpa = rows["my-pdpa2010-001"]
    assert pdpa["source_url"].endswith("2026.pdf") and "from MY_ws_2026-09-01_to_2026-09-20" in pdpa["crawl_notes"]
    assert (out / pdpa["local_path"]).is_file() and (out / pdpa["http_headers_path"]).is_file()
    assert "flags repeal_notice" in rows["my-aa1976-001"]["crawl_notes"] or "repeal_notice" in rows["my-aa1976-001"]["crawl_notes"]
    superseded = [json.loads(l) for l in (out / "superseded.jsonl").read_text(encoding="utf-8").splitlines()]
    assert superseded[0]["run"] == "MY_ws_2026-09-01" and superseded[0]["superseded_by_run"] == "MY_ws_2026-09-01_to_2026-09-20"
    assert superseded[0]["url"].endswith("2023.pdf") and superseded[0]["identity"] == ["law", "709", "principal_act"]
    links = [json.loads(l) for l in (out / "links_used" / "documents.jsonl").read_text(encoding="utf-8").splitlines()]
    by_doc = {l["contract_meta"]["corpus"]["doc_id"]: l for l in links}
    assert by_doc["my-wpa2009-001"]["contract_meta"]["content_flags"] == ["other_act_text"]
    assert (out / "links_used" / "laws.csv").is_file() and (out / "CORPUS_NOTE.md").is_file()
    note = (out / "CORPUS_NOTE.md").read_text(encoding="utf-8")
    assert "Validation against contract 0.2.0: OK" in note and "`other_act_text` | 1" in note and "`gazette_print` | 1" in note


def test_flagged_rows_can_be_left_out_and_a_corpus_never_overwrites(tmp_path, crawl):
    audit_run.main([str(crawl)])
    out = tmp_path / "MY_corpus_2026-09-21"
    meta = merge_corpus.merge(tmp_path, out, "MY", exclude_flags=("repeal_notice", "other_act_text"))
    assert meta["documents"] == len(DOCS) - 2 and meta["excluded"] == 2
    assert {e["doc_id"] for e in meta["excluded_rows"]} == {"my-aa1976-001", "my-wpa2009-001"}
    with pytest.raises(FileExistsError):
        merge_corpus.merge(tmp_path, out, "MY")
    assert merge_corpus.main(["--outputs", str(tmp_path), "--out", str(out)]) == 1


def test_a_document_the_engine_logged_as_a_duplicate_is_not_a_missing_document(tmp_path, crawl):
    log = crawl / "crawl_log.jsonl"
    log.write_text(log.read_text(encoding="utf-8") + json.dumps({"url": "https://lom.agc.gov.my/x/dup.pdf", "outcome": "duplicate"}) + "\n", encoding="utf-8")
    result = audit_run.audit(crawl)
    assert result["summary"]["missing"] == 1
    meta = merge_corpus.merge(tmp_path, tmp_path / "MY_corpus_2026-09-22", "MY")
    assert meta["duplicates_logged"] == 1


def test_the_corpus_cli_reports_and_hardlinks_when_asked(tmp_path, crawl, capsys):
    out = tmp_path / "MY_corpus_2026-09-23"
    rc = merge_corpus.main(["--outputs", str(tmp_path), "--out", str(out), "--hardlink"])
    assert rc == 0 and "validation OK" in capsys.readouterr().out
    src = crawl / "raw" / "my" / "pdpa" / "20260901__native.pdf"
    dest = out / "raw" / "my" / "pdpa" / "20260901__native.pdf"
    assert dest.is_file() and dest.read_bytes() == src.read_bytes()


def test_two_runs_that_minted_the_same_doc_id_for_different_laws_both_keep_their_document(tmp_path, crawl):
    # the delta run's id map started fresh: its new act (Act 885) got the id the crawl gave the PDPA
    delta = make_run(tmp_path, "MY_ws_2026-09-01_to_2026-09-20", ["notice"], "2026-09-20T07:00:00Z",
                     overrides={"notice": {"doc_id": "my-pdpa2010-001", "number": "Act 885", "law_name": "NATIONAL TRUST FUND ACT 2026",
                                           "url": "https://lom.agc.gov.my/x/Act%20885.pdf",
                                           "pages": ["LAWS OF MALAYSIA\nAct 885\nNATIONAL TRUST FUND ACT 2026"] + ["p"] * 25}})
    out = tmp_path / "MY_corpus_2026-09-21"
    meta = merge_corpus.merge(tmp_path, out, "MY")
    assert meta["validation"]["ok"] and meta["documents"] == len(DOCS) + 1 and meta["superseded"] == 0
    assert len(meta["renamed"]) == 1 and meta["per_run"][delta.name]["renamed"] == 1
    r = meta["renamed"][0]
    assert r["doc_id"] == "my-pdpa2010-002" and r["doc_id_in_run"] == "my-pdpa2010-001" and r["run"] == delta.name
    assert r["collided_with"] == {"doc_id": "my-pdpa2010-001", "run": crawl.name, "law_number": "Act 709"}
    rows = {json.loads(l)["doc_id"]: json.loads(l) for l in (out / "manifest.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()}
    assert rows["my-pdpa2010-001"]["law_number_guess"] == "Act 709"
    assert rows["my-pdpa2010-002"]["law_number_guess"] == "Act 885" and "doc_id in run: my-pdpa2010-001" in rows["my-pdpa2010-002"]["crawl_notes"]
    links = [json.loads(l) for l in (out / "links_used" / "documents.jsonl").read_text(encoding="utf-8").splitlines()]
    assert {l["contract_meta"]["corpus"]["doc_id"] for l in links if l["law_number_guess"] == "Act 885"} == {"my-pdpa2010-002"}
    assert "## Renamed doc_ids" in (out / "CORPUS_NOTE.md").read_text(encoding="utf-8")


def test_an_older_run_whose_list_lacks_portal_ids_is_still_superseded_by_the_same_law(tmp_path):
    old = make_run(tmp_path, "MY_ws_2026-08-01", ["pdpa", "amend"], "2026-08-01T07:00:00Z", portal_ids=False)
    new = make_run(tmp_path, "MY_ws_2026-09-01", ["pdpa", "amend"], "2026-09-01T07:00:00Z",
                   overrides={"pdpa": {"url": "https://lom.agc.gov.my/x/ACT%20709-REPRINT%202026.pdf",
                                       "pages": ["LAWS OF MALAYSIA\nAct 709\nPERSONAL DATA PROTECTION ACT 2010\nAs at 1 August 2026"]}})
    meta = merge_corpus.merge(tmp_path, tmp_path / "MY_corpus_2026-09-02", "MY")
    assert meta["validation"]["ok"] and meta["documents"] == 2 and meta["superseded"] == 2 and not meta["renamed"]
    matched = {json.loads(l)["doc_id"]: json.loads(l)["matched_on"]
               for l in (tmp_path / "MY_corpus_2026-09-02" / "superseded.jsonl").read_text(encoding="utf-8").splitlines()}
    assert matched == {"my-pdpa2010-001": "doc_id", "my-pdpa2024-001": "url"}
    assert meta["runs"] == [new.name, old.name]


def test_a_fetch_that_failed_and_then_succeeded_is_not_missing_and_a_bare_run_gets_kinds_from_numbers(tmp_path):
    run = make_run(tmp_path, "MY_ws_2026-09-03", ["pdpa", "notice"], "2026-09-03T07:00:00Z",
                   failed=(("https://lom.agc.gov.my/x/Act%20175%20original.pdf", "TRADE MARKS ACT 1976"),))
    log = run / "crawl_log.jsonl"
    entries = [json.loads(l) for l in log.read_text(encoding="utf-8").splitlines()]
    # the PDPA failed first, then was stored: the last word is the manifest's
    entries.insert(0, {"url": DOCS["pdpa"][5], "outcome": "failed", "status": 500, "note": "store FileNotFoundError: C:\\very\\long\\path"})
    log.write_text("".join(json.dumps(e) + "\n" for e in entries), encoding="utf-8")
    shutil.rmtree(run / "links_used")   # no link list at all: the 2026-09-13 case
    result = audit_run.audit(run)
    assert [m["url"] for m in result["missing"]] == ["https://lom.agc.gov.my/x/Act%20175%20original.pdf"]
    assert result["missing"][0]["law"] is None and result["missing"][0]["note"] == "TRADE MARKS ACT 1976"
    kinds = {r["doc_id"]: (r["kind"], r["kind_source"]) for r in result["rows"]}
    assert kinds["my-pdpa2010-001"] == ("principal_act", "law_number") and kinds["my-aa1976-001"] == ("principal_act", "law_number")
    assert result["summary"]["without_link_row"] == 2
    flags = {r["doc_id"]: r["flags"] for r in result["rows"]}
    assert set(flags["my-aa1976-001"]) == {"short_principal", "repeal_notice"}
    md = audit_run.to_markdown(result)
    assert "2 rows have no link row" in md and "| Log note |" in md


def test_a_one_page_principal_file_without_the_repeal_words_is_flagged_to_look_at(tmp_path):
    run = make_run(tmp_path, "MY_ws_2026-09-04", ["notice"], "2026-09-04T07:00:00Z",
                   overrides={"notice": {"pages": ["PEPLALED (Y: CT 759 LAWS OF MALAYSIAA Act 168 ISLAMIC BANKING ACT 1983 badly scanned words here"]}})
    flags = {r["doc_id"]: r["flags"] for r in audit_run.audit(run)["rows"]}
    assert set(flags["my-aa1976-001"]) == {"short_principal", "one_page_principal"}


def test_the_parent_probe_accepts_either_word_of_the_parent_name(tmp_path):
    run = make_run(tmp_path, "MY_ws_2026-09-05", ["supp"], "2026-09-05T07:00:00Z",
                   overrides={"supp": {"law_name": "Amendment of COMMUNICATIONS AND MULTIMEDIA ACT 1998 (05 Nov 2015)",
                                       "pages": ["MALAYSIA\nWarta Kerajaan\n5hb November 2015 TAMBAHAN No. 141\nPERUNDANGAN (B)\nP.U. (B) 444\nAKTA KOMUNIKASI DAN MULTIMEDIA 1998 Pemberitahuan"] + ["p"] * 3}})
    flags = {r["doc_id"]: r["flags"] for r in audit_run.audit(run)["rows"]}
    assert flags["my-aqsa2016-001"] == ["subsidiary_amendment"]   # "MULTIMEDIA" is on the page: not a bundle of other notices


def test_excluding_the_newest_copy_does_not_bring_the_older_copy_back(tmp_path):
    old = make_run(tmp_path, "MY_ws_2026-08-01", ["pdpa"], "2026-08-01T07:00:00Z")
    new = make_run(tmp_path, "MY_ws_2026-09-01", ["pdpa"], "2026-09-01T07:00:00Z",
                   overrides={"pdpa": {"url": "https://lom.agc.gov.my/x/ACT%20709%20(Repealed).pdf",
                                       "pages": ["LAWS OF MALAYSIA\nAct 709\n(Repealed by Act 900)"]}},
                   audit_flags={"my-pdpa2010-001": ["repeal_notice"]})
    meta = merge_corpus.merge(tmp_path, tmp_path / "MY_corpus_2026-09-02", "MY", exclude_flags=("repeal_notice",))
    assert meta["documents"] == 0 and meta["excluded"] == 1 and meta["superseded"] == 1
    s = json.loads((tmp_path / "MY_corpus_2026-09-02" / "superseded.jsonl").read_text(encoding="utf-8").splitlines()[0])
    assert s["run"] == old.name and s["superseded_by_run"] == new.name and s["superseded_by_excluded"] is True and s["matched_on"] == "law"


def test_two_instruments_sharing_a_non_act_number_and_a_doc_id_are_not_one_law(tmp_path):
    old = make_run(tmp_path, "MY_ws_2026-08-01", ["pdpa"], "2026-08-01T07:00:00Z", portal_ids=False,
                   overrides={"pdpa": {"doc_id": "my-csr2024-001", "number": "P.U.(A) 2024", "law_name": "Cyber Security (Compounding) Regulations 2024",
                                       "url": "https://lom.agc.gov.my/x/compounding.pdf", "pages": ["P.U. (A) 1 Compounding"]}})
    new = make_run(tmp_path, "MY_ws_2026-09-01", ["pdpa"], "2026-09-01T07:00:00Z", portal_ids=False,
                   overrides={"pdpa": {"doc_id": "my-csr2024-001", "number": "P.U.(A) 2024", "law_name": "Cyber Security (Licensing) Regulations 2024",
                                       "url": "https://lom.agc.gov.my/x/licensing.pdf", "pages": ["P.U. (A) 2 Licensing"]}})
    meta = merge_corpus.merge(tmp_path, tmp_path / "MY_corpus_2026-09-02", "MY")
    assert meta["documents"] == 2 and meta["superseded"] == 0 and len(meta["renamed"]) == 1
    assert meta["renamed"][0]["run"] == new.name and meta["renamed"][0]["doc_id"] == "my-csr2024-002"
    assert meta["runs"] == [new.name, old.name]


def test_a_document_without_a_link_row_still_gets_a_corpus_link_row(tmp_path, crawl):
    links = crawl / "links_used" / "documents.jsonl"
    rows = [l for l in links.read_text(encoding="utf-8").splitlines() if '"my-' not in l or "pdp.gov.my" not in l]
    rows = [l for l in links.read_text(encoding="utf-8").splitlines() if "https://www.pdp.gov.my/code/" not in l]
    links.write_text("\n".join(rows) + "\n", encoding="utf-8")
    out = tmp_path / "MY_corpus_2026-09-21"
    meta = merge_corpus.merge(tmp_path, out, "MY")
    assert meta["documents"] == len(DOCS) and meta["synthetic_link_rows"] == 1 and meta["validation"]["ok"]
    lrs = [json.loads(l) for l in (out / "links_used" / "documents.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(lrs) == len(DOCS)
    syn = [l for l in lrs if l["contract_meta"].get("synthetic")]
    assert syn[0]["url"] == "https://www.pdp.gov.my/code/" and syn[0]["contract_meta"]["corpus"]["doc_id"] == "my-pdpcp2017-001"


def test_a_store_error_and_a_file_in_no_manifest_row_are_reported(tmp_path):
    run = make_run(tmp_path, "MY_ws_2026-09-02", list(DOCS)[:1], "2026-09-02T07:00:00Z")
    with (run / "crawl_log.jsonl").open("a", encoding="utf-8") as fh:   # the bytes arrived, the engine could not write them
        for outcome, note in (("ok", "A LONG NAME"), ("error", "store FileNotFoundError: [Errno 2] No such file or directory: 'C:/x'")):
            fh.write(json.dumps({"ts": "2026-09-02T07:01:00Z", "url": "https://lom.agc.gov.my/x/long.pdf", "host": "lom.agc.gov.my",
                                 "outcome": outcome, "status": 200, "note": note}) + "\n")
    orphan = run / "raw" / "my" / "killed_law" / "20260902T0705Z__native.pdf"   # written after the last checkpoint
    orphan.parent.mkdir(parents=True)
    orphan.write_bytes(b"%PDF-1.4 x")
    result = audit_run.audit(run)
    assert result["summary"]["by_flag"].get("store_failed") == 1 and "fetch_failed" not in result["summary"]["by_flag"]
    assert [m["flags"] for m in result["missing"]] == [["store_failed"]]
    assert result["summary"]["orphan_files"] == 1
    assert result["orphans"][0]["path"] == "raw/my/killed_law/20260902T0705Z__native.pdf"
    md = audit_run.to_markdown(result)
    assert "## Orphan files" in md and "killed_law" in md and "store_failed" in md


# --- the rule sets of Singapore and Australia ----------------------------------------------------------------------

def _one(tmp_path, cc: str, name: str, number: str, kind: str, pages: list[str], source_type: str = "pdf_native"):
    """A run of one document, so a rule can be read on its own."""
    run = tmp_path / f"{cc}_ws_2026-09-16"
    (run / "links_used").mkdir(parents=True)
    folder = run / "raw" / cc.lower() / "x"
    folder.mkdir(parents=True)
    if source_type == "html":
        path = folder / "a__page.html"
        path.write_text(pages[0], encoding="utf-8")
    else:
        path = folder / "a__native.pdf"
        path.write_bytes(make_pdf(pages))
    rel = path.relative_to(run).as_posix()
    row = _row(doc_id=f"{cc.lower()}-x-001", source_url="https://example.test/x", local_path=rel,
               http_headers_path=rel + ".headers.json", law_name_guess=name, law_number_guess=number,
               source_type=source_type, content_type="text/html" if source_type == "html" else "application/pdf",
               content_sha256=hashlib.sha256(path.read_bytes()).hexdigest(), byte_size=path.stat().st_size,
               page_count=None if source_type == "html" else len(pages), access_date="2026-09-16T00:00:00Z",
               pdf_is_scanned=None if source_type == "html" else False, economy=cc)
    Path(str(path) + ".headers.json").write_text("{}", encoding="utf-8")
    from p1_scrape.manifest import write_manifest
    write_manifest([row], run)
    (run / "links_used" / "documents.jsonl").write_text(json.dumps(
        {"url": "https://example.test/x", "economy": cc, "law_name_guess": name, "law_number_guess": number,
         "order": 1, "scopes": ["all"], "contract_meta": {"document_kind": kind, "portal_id": "x"}}) + "\n",
        encoding="utf-8")
    (run / "crawl_log.jsonl").write_text(json.dumps(
        {"ts": "2026-09-16T00:00:00Z", "url": "https://example.test/x", "outcome": "ok", "status": 200}) + "\n",
        encoding="utf-8")
    return run


SG_STATUTES = ("THE STATUTES OF THE REPUBLIC OF SINGAPORE\nPERSONAL DATA PROTECTION ACT 2012\n2020 REVISED EDITION\n"
               "This revised edition incorporates all amendments up to and including 1 December 2021")
SG_SUPPLY = ("SUPPLY ACT 2025\n(No. 11 of 2025)\nARRANGEMENT OF SECTIONS\nSection 1. Short title and commencement\n"
             "2. Supply from Consolidated Fund\n3. Supply from Development Fund")


def test_the_singapore_rules_read_the_four_prints_the_portal_uses(tmp_path):
    # the consolidated text of the right act: nothing to say
    run = _one(tmp_path / "a", "SG", "Personal Data Protection Act 2012", "Act 26 of 2012", "principal_act",
               [SG_STATUTES, "PART 1 PRELIMINARY", "3", "4", "5"])
    assert audit_run.audit(run, economy="SG")["rows"][0]["flags"] == []

    # a four-page act printed in full is the whole act, not a short principal to look at
    run = _one(tmp_path / "b", "SG", "Supply Act 2025", "Act 11 of 2025", "principal_act",
               [SG_SUPPLY, "2", "3", "4"])
    assert audit_run.audit(run, economy="SG")["rows"][0]["flags"] == ["short_act_as_printed"]

    # another act's text under this row: the numbers on the page disagree with the row
    run = _one(tmp_path / "c", "SG", "Supply Act 2025", "Act 11 of 2025", "principal_act",
               ["SUPPLY ACT 2024\n(No. 9 of 2024)\nARRANGEMENT OF SECTIONS", "2", "3", "4", "5"])
    assert "other_act_text" in audit_run.audit(run, economy="SG")["rows"][0]["flags"]

    # an amending act is published in the Acts Supplement, which is the form, not a fault
    run = _one(tmp_path / "d", "SG", "Cybersecurity (Amendment) Act 2024", "Act 19 of 2024", "amending_act",
               ["REPUBLIC OF SINGAPORE GOVERNMENT GAZETTE\nACTS SUPPLEMENT\nPublished by Authority\n"
                "Cybersecurity (Amendment) Act 2024\n(No. 19 of 2024)", "2", "3", "4", "5"])
    assert audit_run.audit(run, economy="SG")["rows"][0]["flags"] == ["gazette_print"]


def test_a_singapore_repeal_act_is_not_a_repeal_notice_but_a_wrong_short_file_is(tmp_path):
    # an act whose own job is to repeal another: the file is right
    run = _one(tmp_path / "a", "SG", "Reciprocal Enforcement of Commonwealth Judgments (Repeal) Act 2019",
               "Act 24 of 2019", "principal_act",
               ["RECIPROCAL ENFORCEMENT OF COMMONWEALTH JUDGMENTS (REPEAL) ACT 2019\n(No. 24 of 2019)\n"
                "ARRANGEMENT OF SECTIONS\n1. Short title and commencement\n2. Repeal", "2", "3", "4", "5"])
    assert "repeal_notice" not in audit_run.audit(run, economy="SG")["rows"][0]["flags"]

    # a short file that says the act was repealed, under an act's own name: look at it
    run = _one(tmp_path / "b", "SG", "Trade Marks Act 1998", "Act 46 of 1998", "principal_act",
               ["TRADE MARKS ACT 1998\n(No. 46 of 1998)\nARRANGEMENT OF SECTIONS\n"
                "This Act is repealed by Act 12 of 2020", "2"])
    assert "repeal_notice" in audit_run.audit(run, economy="SG")["rows"][0]["flags"]


def test_the_australia_rules_survive_the_registers_old_scans_and_name_the_renamed_acts(tmp_path):
    # an as-made act of three pages, printed with its own number: the whole act
    run = _one(tmp_path / "a", "AU", "Surplus Revenue Act 1908", "No. 15, 1908", "principal_act",
               ["SURPLUS REVENUE . No. 1 5 o f 1908 . An Ac t relatin g t o th e paymen t to th e several State s",
                "2", "3"])
    flags = audit_run.audit(run, economy="AU")["rows"][0]["flags"]
    assert flags == ["as_made_short_act"]          # the OCR spaces the digits; the squashed read finds the number

    # a one-page as-made act is explained by the same flag and not also called a one-page principal
    run = _one(tmp_path / "b", "AU", "Seat of Government Act 1908", "No. 24, 1908", "principal_act",
               ["SEAT O F GOVERNMENT . No. 2 4 o f 1908 . An Ac t t o Determin e th e Sea t o f Governmen t"])
    assert audit_run.audit(run, economy="AU")["rows"][0]["flags"] == ["as_made_short_act"]

    # the act was renamed since it was enacted: the title differs but the number is this act's
    run = _one(tmp_path / "c", "AU", "Protection of Word Anzac Act 1920", "No. 54, 1920", "principal_act",
               ["1920. War Precautions Act Repeal. No. 54.\nWAR PRECAUTIONS ACT REPEAL.\nNo. 54 of 1920.\n"
                "An Act to repeal the War Precautions Act 1914-1918", "2", "3", "4", "5"])
    assert audit_run.audit(run, economy="AU")["rows"][0]["flags"] == ["renamed_since_enactment"]

    # the act it amends is named first, which must not make this another act's text
    run = _one(tmp_path / "d", "AU", "Commonwealth Banks Act 1973", "No. 18, 1973", "principal_act",
               ["Commonwealth Banks Act 1973 No . 18 of 1973 AN ACT To amend the Commonwealth Banks Act 1959-1968",
                "2", "3", "4", "5"])
    assert audit_run.audit(run, economy="AU")["rows"][0]["flags"] == []


def test_the_markup_reader_gets_past_the_boilerplate_and_an_empty_document_is_a_finding(tmp_path):
    """The register's epub-derived documents open with a style block and a coat-of-arms image, so a reader that
    stops at 4 KB or falls back to raw markup sees no words at all: 52 of Australia's documents read as empty
    before this was fixed (2026-09-16)."""
    filler = "<style>" + ("a{color:red}" * 400) + "</style>"
    page = ('<!DOCTYPE html><html><head><title>Cyber Security Act 2024</title>' + filler + '</head><body>'
            '<div><p><img src="image.001.jpeg" alt="Commonwealth Coat of Arms"></p>'
            '<p class="ShortT"><span>Cyber Security Act 2024</span></p>'
            '<p>An Act about the security of critical infrastructure, and for related purposes.</p></div></body></html>')
    run = _one(tmp_path / "a", "AU", "Cyber Security Act 2024", "No. 9, 2024", "principal_act", [page],
               source_type="html")
    result = audit_run.audit(run, economy="AU")
    row = result["rows"][0]
    assert "empty_document" not in row["flags"] and "html_stored" not in row["flags"]   # HTML is a form here
    assert "Cyber Security Act 2024" in row["evidence"] and "<p" not in row["evidence"]
    assert row["flags"] == []

    # a page with the markup but no words is a finding, in any country
    run = _one(tmp_path / "b", "AU", "Cyber Security Act 2024", "No. 9, 2024", "principal_act",
               ["<html><head><title>x</title></head><body><div><img src='a.png'></div></body></html>"],
               source_type="html")
    assert audit_run.audit(run, economy="AU")["rows"][0]["flags"] == ["empty_document"]

