"""Australia adapter (countries/au-australia/scraper/): offline tests on API replies saved from
api.prod.legislation.gov.au on 2026-09-15 (tests/README.md lists them). No test sends a request."""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from urllib.parse import unquote

import pytest

from p1_scrape.adapters import au_legislation as m
from p1_scrape.adapters.au_legislation import api as A, catalogue
from p1_scrape.adapters.my_gazette.client import LomClient as PacedClient

_HERE = Path(__file__).parent
FIX = _HERE / "fixtures" / "au" if (_HERE / "fixtures" / "au").is_dir() else _HERE / "fixtures"
WWW = "https://www.legislation.gov.au"


def _fixture(name: str) -> dict:
    return json.loads((FIX / name).read_text(encoding="utf-8"))


PRIVACY_TITLE = _fixture("api_titles_privacy_act_2026-09-15.json")["value"][0]
PRIVACY_VERSION = _fixture("api_versions_privacy_act_latest_2026-09-15.json")["value"][0]
PAGE_TITLES = _fixture("api_titles_page_2026-09-15.json")["value"]        # 3 titles, the first not principal


def _title(tid: str, name: str, principal=True, year=2000, number=1, status="InForce") -> dict:
    return {**PRIVACY_TITLE, "id": tid, "name": name, "isPrincipal": principal, "year": year, "number": number, "status": status}


def _version(tid: str, start="2026-06-04", comp="104", reg="C2026C00227") -> dict:
    """A latest version like the Privacy Act's; an as-made title (comp None or "0") carries its own id as registerId."""
    v = dict(PRIVACY_VERSION)
    compiled = comp not in (None, "0", 0)
    v.update({"titleId": tid, "start": f"{start}T00:00:00", "compilationNumber": comp if compiled else 0,
              "registerId": reg if compiled else tid})
    return v


# the relevance net is Round 1's: adjacent-word bigrams of the seed_queries against the lowercase title, so the fake
# TIA title is spelt without the brackets that keep "telecommunications" and "interception" apart on the register
TITLES = [PRIVACY_TITLE, _title("C2004A02124", "Telecommunications Interception and Access Act 1979", year=1979, number=114),
          _title("C2008A00073", "Statute Law Revision Act 2008", principal=False, year=2008, number=73),
          _title("C2004A04868", "Criminal Code Act 1995", year=1995, number=12)]
SEED_TITLES = {"C2018A00148": _title("C2018A00148", "Telecommunications and Other Legislation Amendment (Assistance and Access) Act 2018",
                                     principal=False, year=2018, number=148),
               "F2025L00278": {**_title("F2025L00278", "Cyber Security (Ransomware Payment Reporting) Rules 2025", year=2025, number=0),
                               "collection": "LegislativeInstrument", "seriesType": "LegislativeInstrument"},
               "F2021L00289": {**_title("F2021L00289", "Telecommunications Regulations 2021", year=2021, number=0),
                               "collection": "LegislativeInstrument", "seriesType": "LegislativeInstrument"}}
VERSIONS = {"C2004A03712": PRIVACY_VERSION,
            "C2004A02124": _version("C2004A02124", "2026-08-27", "134", "C2026C00134"),
            "C2004A04868": _version("C2004A04868", "2026-07-01", "160", "C2026C00160"),
            "C2018A00148": _version("C2018A00148", "2018-12-09", None, None),
            "F2025L00278": _version("F2025L00278", "2025-03-03", "0", None),          # as-made, as on the register
            "F2021L00289": _version("F2021L00289", "2025-05-30", "1", "F2025C00300")}  # a compiled instrument


class FakeResp:
    def __init__(self, status, body: bytes, headers=None):
        self.status_code, self.content, self.headers = status, body, headers or {}
        self.text = body.decode("utf-8", "replace")


class FakeSession:
    def __init__(self, api_error: int | None = None, www_robots=(200, "User-agent: *\nCrawl-delay: 10\nDisallow: /assets/\n")):
        self.calls: list[tuple[str, str]] = []
        self.api_error = api_error
        self.www_robots = www_robots

    def request(self, method, url, data=None, headers=None, timeout=None, allow_redirects=True):
        self.calls.append((method, url))
        if url == "https://api.prod.legislation.gov.au/robots.txt":
            return FakeResp(404, b"")
        if url == WWW + "/robots.txt":
            return FakeResp(self.www_robots[0], self.www_robots[1].encode())
        if url.startswith(A.API + "/titles"):
            if self.api_error:
                return FakeResp(self.api_error, b"error")
            q = unquote(url)
            if "id in (" in q:
                ids = re.findall(r"'([CF]\d{4}[A-Z]\d{5})'", q)
                return FakeResp(200, json.dumps({"value": [SEED_TITLES[i] for i in ids if i in SEED_TITLES]}).encode())
            skip = int(re.search(r"\$skip=(\d+)", q).group(1))
            return FakeResp(200, json.dumps({"value": TITLES if skip == 0 else []}).encode())
        if url.startswith(A.API + "/versions"):
            ids = re.findall(r"'([CF]\d{4}[A-Z]\d{5})'", unquote(url))
            return FakeResp(200, json.dumps({"value": [VERSIONS[i] for i in ids if i in VERSIONS]}).encode())
        return FakeResp(404, b"")


def _client(session: FakeSession, delay=3.0) -> PacedClient:
    return PacedClient("test-agent RDTII-Rocky-Crawler/0.1", delay, session=session, sleep=lambda s: None,
                       clock=lambda: 0.0, jitter=False, now_iso=lambda: "2026-09-15T12:00:00Z")


SEEDS = [
    {"law_name": "Privacy Act 1988", "law_number": "No. 119, 1988", "url": WWW + "/C2004A03712", "indicators": ["P6-I3", "P7-I1"], "provenance": "round1_registry"},
    {"law_name": "Telecommunications and Other Legislation Amendment (Assistance and Access) Act 2018", "law_number": "No. 148, 2018",
     "url": WWW + "/C2018A00148", "indicators": ["P7-I5"], "form": "html"},
    {"law_name": "Cyber Security (Ransomware Payment Reporting) Rules 2025", "law_number": "F2025L00278", "url": WWW + "/F2025L00278",
     "indicators": ["P7-I2"], "form": "html"},
    {"law_name": "Telecommunications Regulations 2021", "law_number": "F2021L00289", "url": WWW + "/F2021L00289",
     "indicators": ["P7-I5"], "form": "html"},
    {"law_name": "Privacy (Credit Reporting) Code 2024", "url": "https://www.oaic.gov.au/x/code.pdf", "indicators": ["P7-I1"]},
]


def _cfg(**reg) -> dict:
    return {"economy": "AU", "seed_queries": {"P7-I1": ["Australian Privacy Principles", "handling of personal information"],
                                              "P7-I5": ["telecommunications interception warrant", "access to stored communications"]},
            "register": {"detail_pages": "all", "version_batch": 18, "title_page_size": 100, "max_titles": 6000, "collection": "Act", **reg},
            "seed_laws": SEEDS}


@pytest.fixture(autouse=True)
def _no_env(monkeypatch):
    for name in list(os.environ):
        if name.startswith("REGISTER_"):
            monkeypatch.delenv(name)


# --- 1. the API records -----------------------------------------------------------------------------------------

def test_a_title_reply_parses_to_number_status_and_principal_flag():
    t = A.parse_titles(_fixture("api_titles_privacy_act_2026-09-15.json"))[0]
    assert t.id == "C2004A03712" and t.name == "Privacy Act 1988" and t.law_number == "No. 119, 1988"
    assert t.is_principal and t.is_in_force and t.status == "InForce" and t.making_date == "1988-12-14" and t.series_type == "Act"
    page = A.parse_titles(_fixture("api_titles_page_2026-09-15.json"))
    assert len(page) == 3 and page[0].is_principal is False and page[0].law_number == "No. 73, 2008"


def test_a_version_reply_parses_to_the_dated_compilation_and_its_amendments():
    v = A.parse_versions(_fixture("api_versions_privacy_act_latest_2026-09-15.json"))[0]
    assert v.title_id == "C2004A03712" and v.register_id == "C2026C00227" and v.start == "2026-06-04" and v.end == "2026-12-10"
    assert v.compilation_number == "104" and v.registered_at == "2026-06-17" and v.is_compilation and v.is_current
    assert v.last_amending_instrument == "Strengthening Oversight of the National Intelligence Community Act 2025 (No. 75, 2025)"
    assert v.amendments[0].title_id == "C2025A00075" and v.amendments[0].provisions == "sch 1 (items 240, 241)"
    assert A.pdf_url(v) == WWW + "/C2004A03712/2026-06-04/2026-06-04/text/original/pdf"
    assert A.epub_url(v) == WWW + "/C2004A03712/2026-06-04/2026-06-04/text/original/epub"
    asmade = A.parse_versions({"value": [_version("C2021A00098", "2021-09-03", "0", None)]})[0]
    assert not asmade.is_compilation and asmade.register_id == "C2021A00098"
    assert A.pdf_url(asmade) == WWW + "/C2021A00098/asmade/2021-09-03/text/original/pdf" and A.epub_url(asmade) is None


def test_the_registered_since_query_lists_the_versions_the_update_check_will_use():
    vs = A.parse_versions(_fixture("api_versions_registered_since_2026-09-15.json"))
    assert len(vs) == 5 and vs[0].title_id == "C1914A00012" and vs[0].register_id == "C2026C00368" and vs[0].registered_at == "2026-09-02"
    assert "registeredAt ge 2026-09-01T00:00:00" in unquote(A.versions_since_url("2026-09-01"))
    assert unquote(A.versions_url(["C1", "C2"])).endswith("titleId in ('C1','C2')")
    assert A.batches(["a", "b", "c"], 2) == [["a", "b"], ["c"]]
    assert A.register_id(WWW + "/Details/C2021A00098") == "C2021A00098" and A.register_id("https://www.oaic.gov.au/x") is None


# --- 2. the catalogue step, on a fake register ------------------------------------------------------------------

@pytest.fixture(scope="module")
def built():
    session = FakeSession()
    adapter = m.AuLegislationAdapter(_cfg(), client=_client(session), www_client=_client(session, 3.0))
    result = catalogue.build(adapter, [6, 7])
    return {"adapter": adapter, "result": result, "session": session}


def test_the_build_reads_robots_on_both_hosts_then_titles_then_versions_and_touches_no_www_page(built):
    calls = [u for _m, u in built["session"].calls]
    assert calls[0] == "https://api.prod.legislation.gov.au/robots.txt" and calls[1] == WWW + "/robots.txt"
    assert calls[2].startswith(A.API + "/titles?") and "$skip=0" in calls[2]        # a short page is the last page
    assert calls[3].startswith(A.API + "/versions?") and "titleId%20in" in calls[3]
    assert calls[4].startswith(A.API + "/titles?") and "id%20in" in calls[4]         # the seeds the harvest lacks
    assert len(calls) == 5 and all(not u.startswith(WWW) or u.endswith("/robots.txt") for u in calls)
    adapter = built["adapter"]
    assert adapter.robots_record["www"]["crawl_delay"] == 10.0 and adapter._www.delay == 10.0
    assert adapter.robots_record["api"]["status"] == 404 and adapter._api.delay == 3.0
    assert adapter.harvest_counts == {"collection": "Act", "titles": 4, "principal": 3, "non_principal": 1, "pages": 1,
                                      "rows": 4, "repeated": 0}
    assert "$orderby=id" in calls[2]                                            # unstable pages overlap without it
    assert set(adapter.versions) == {"C2004A03712", "C2004A02124", "C2004A04868", "C2018A00148", "F2025L00278", "F2021L00289"}


def test_the_list_holds_every_principal_act_with_its_dated_file_and_the_seeds_in_their_forms(built):
    docs = built["result"]["documents"]
    kinds = built["result"]["meta"]["document_kinds"]
    assert kinds == {"principal_act": 3, "amending_act": 1, "subsidiary_legislation": 2, "agency_or_other": 1}
    first = docs[0]
    assert first["url"] == WWW + "/C2004A03712/2026-06-04/2026-06-04/text/original/epub" and first["scopes"] == ["seed", "relevant", "all"]
    meta = first["contract_meta"]
    assert meta["portal_id"] == "C2004A03712" and meta["law_number"] == "No. 119, 1988" and meta["version_as_at"] == "2026-06-04"
    assert meta["version_id"] == "C2026C00227" and meta["compilation_number"] == "104" and meta["published_on"] == "2026-06-17"
    assert meta["pdf_url"] == WWW + "/C2004A03712/2026-06-04/2026-06-04/text/original/pdf" and meta["epub_url"] == first["url"]
    assert meta["last_amending_instrument"].startswith("Strengthening Oversight") and meta["last_amended_year"] == "2025"
    assert meta["legal_status"] == "in_force" and meta["amendment_check_complete"] is True and meta["text_version"] == "consolidation"
    tola = next(d for d in docs if d["contract_meta"]["portal_id"] == "C2018A00148")     # as-made in the fake, form: html
    assert tola["url"] == WWW + "/C2018A00148/latest/text" and tola["contract_meta"]["document_kind"] == "amending_act"
    assert tola["contract_meta"]["text_version"] == "as_enacted" and "as_made_only" in tola["contract_meta"]["review_flags"]
    assert tola["contract_meta"]["pdf_url"] == WWW + "/C2018A00148/asmade/2018-12-09/text/original/pdf" and tola["contract_meta"]["epub_url"] is None
    rules = next(d for d in docs if d["contract_meta"]["portal_id"] == "F2025L00278")     # as-made, form: html
    assert rules["url"] == WWW + "/F2025L00278/latest/text" and rules["contract_meta"]["document_kind"] == "subsidiary_legislation"
    assert rules["contract_meta"]["pdf_url"] == WWW + "/F2025L00278/asmade/2025-03-03/text/original/pdf"
    regs = next(d for d in docs if d["contract_meta"]["portal_id"] == "F2021L00289")      # compiled, form: html
    assert regs["url"] == WWW + "/F2021L00289/2025-05-30/2025-05-30/text/original/epub"
    code = next(d for d in docs if d["contract_meta"]["document_kind"] == "agency_or_other")
    assert code["url"].startswith("https://www.oaic.gov.au/") and code["scopes"] == ["seed", "relevant", "all"]
    tia = next(d for d in docs if d["contract_meta"]["portal_id"] == "C2004A02124")
    assert tia["scopes"] == ["relevant", "all"] and tia["contract_meta"]["discovery_path"] == "api_listing"
    criminal = next(d for d in docs if d["contract_meta"]["portal_id"] == "C2004A04868")
    assert criminal["scopes"] == ["all"] and criminal["url"].endswith("/2026-07-01/2026-07-01/text/original/epub")


def test_the_pdf_form_takes_the_dated_pdf_for_compilations_and_the_as_made_pdf_otherwise():
    session = FakeSession()
    adapter = m.AuLegislationAdapter(_cfg(document_form="pdf"), client=_client(session), www_client=_client(session))
    docs = {d["contract_meta"]["portal_id"]: d for d in catalogue.build(adapter, [6, 7])["documents"]}
    assert docs["C2004A03712"]["url"].endswith("/2026-06-04/2026-06-04/text/original/pdf")
    assert docs["C2018A00148"]["url"] == WWW + "/C2018A00148/latest/text"        # form: html on an as-made title
    assert docs["F2021L00289"]["url"].endswith("/text/original/epub")            # form: html on a compilation


def test_laws_csv_names_every_harvested_title_including_the_amending_acts_not_fetched(built):
    laws = {r["portal_id"]: r for r in built["result"]["laws"]}
    assert laws["C2008A00073"]["is_principal"] is False and "decision 13" in laws["C2008A00073"]["not_crawled_reason"]
    assert laws["C2008A00073"]["legal_status"] == "in_force"                       # mapped, as the document rows are
    assert laws["C2004A03712"]["version_id"] == "C2026C00227" and laws["C2004A03712"]["in_seed"] and laws["C2004A03712"]["amendments_listed"] == 1
    assert laws["C2018A00148"]["is_principal"] is False and laws["C2018A00148"]["in_seed"]


def test_the_written_list_replays_through_the_links_file_frontier(built, tmp_path):
    paths = catalogue.write(built["result"], tmp_path / "links")
    meta = json.loads(Path(paths["catalogue_meta.json"]).read_text(encoding="utf-8"))
    assert meta["cfg_sha256"] == catalogue.cfg_fingerprint(_cfg()) and meta["www_requests"] == 1
    session = FakeSession()
    adapter = m.AuLegislationAdapter(_cfg(frontier="links_file", links_file=paths["documents.jsonl"]),
                                     client=_client(session), www_client=_client(session))
    cands = adapter.discover([6, 7], scope="relevant")
    assert [u for _m, u in session.calls] == ["https://api.prod.legislation.gov.au/robots.txt", WWW + "/robots.txt"]
    assert len(cands) == 6 and cands[0].contract_meta["portal_id"] == "C2004A03712"
    assert any("REQUEST_DELAY_MS=10000" in n for n in adapter.notes)              # the engine's 3 s is below the 10 s
    down = m.AuLegislationAdapter(_cfg(frontier="links_file", links_file=paths["documents.jsonl"]),
                                  client=_client(FakeSession()), www_client=_client(FakeSession(www_robots=(500, "error"))))
    only = down.discover([6, 7], scope="all")
    assert [c.url for c in only] == ["https://www.oaic.gov.au/x/code.pdf"]            # register rows dropped, the rest served
    plan = adapter.build_plans(cands[0], forms="pdf")[0]
    assert plan.method == "requests" and plan.unpack == "epub_html" and plan.citation_url == cands[0].url
    framed = next(c for c in cands if c.url.endswith("/latest/text"))
    p = adapter.build_plans(framed)[0]
    assert p.method == "playwright" and p.iframe_selector == "iframe#epubFrame" and p.reject_pattern
    stale = m.AuLegislationAdapter(_cfg(frontier="links_file", links_file=paths["documents.jsonl"], version_batch=10),
                                   client=_client(FakeSession()), www_client=_client(FakeSession()))
    with pytest.raises(ValueError, match="different registry"):
        stale.discover([6, 7], scope="all")


def test_an_api_error_stops_the_build_and_nothing_is_written():
    adapter = m.AuLegislationAdapter(_cfg(), client=_client(FakeSession(api_error=500)), www_client=_client(FakeSession()))
    with pytest.raises(m.RegisterUnavailable, match="HTTP 500"):
        catalogue.build(adapter, [6, 7])
    # a 503 three times in a row is the paced client's own stop (throttling), raised before the build can report
    with pytest.raises(Exception, match="throttling"):
        catalogue.build(m.AuLegislationAdapter(_cfg(), client=_client(FakeSession(api_error=503)), www_client=_client(FakeSession())), [6, 7])


def test_the_seed_scope_without_a_fetcher_is_the_seed_list_in_round_1_form():
    adapter = m.AuLegislationAdapter(_cfg())
    cands = adapter.discover([6, 7], scope="seed")
    assert [c.contract_meta["portal_id"] for c in cands] == ["C2004A03712", "C2018A00148", "F2025L00278", "F2021L00289", None]
    assert cands[0].url == WWW + "/C2004A03712/latest/text" and "version_unknown" in cands[0].contract_meta["review_flags"]


# --- the law table (scraper/checker.py) -----------------------------------------------------------------------

def _folder(tmp_path, links, census, stored, census_cols):
    """A run folder with just what the checker reads: a manifest, the list it used and the census."""
    (tmp_path / "links_used").mkdir(parents=True)
    (tmp_path / "manifest.jsonl").write_text(
        "".join(json.dumps(r) + "\n" for r in stored), encoding="utf-8")
    (tmp_path / "links_used" / "documents.jsonl").write_text(
        "".join(json.dumps(r) + "\n" for r in links), encoding="utf-8")
    import csv as _csv
    with (tmp_path / "links_used" / "laws.csv").open("w", encoding="utf-8", newline="") as fh:
        w = _csv.DictWriter(fh, fieldnames=census_cols, lineterminator="\n")
        w.writeheader()
        w.writerows(census)
    return tmp_path


def test_the_law_table_reports_the_compilation_dates_and_what_the_harvest_did_not_fetch(tmp_path):
    from p1_scrape.adapters.au_legislation import checker
    links = [{"url": f"{WWW}/C2004A03712/2026-06-04/2026-06-04/text/original/epub", "law_name_guess": "Privacy Act 1988",
              "contract_meta": {"portal_id": "C2004A03712", "law_number": "No. 119, 1988", "document_kind": "principal_act",
                                "legal_status": "in_force", "status_source": "portal_api", "enacted_on": "1988-12-14",
                                "version_as_at": "2026-06-04", "version_ends": "2026-12-10", "compilation_number": 98,
                                "version_id": "C2026C00227", "last_amending_instrument": "Strengthening Oversight Act 2025",
                                "last_amended_year": "2025", "review_flags": []}}]
    census_cols = ["series", "portal_id", "law_number", "title", "is_principal", "legal_status", "version_as_at",
                   "version_id", "compilation_number", "last_amending_instrument", "document_url", "document_kinds",
                   "not_crawled_reason"]
    census = [
        {"series": "Act", "portal_id": "C2004A03712", "law_number": "No. 119, 1988", "title": "Privacy Act 1988",
         "is_principal": "True", "legal_status": "in_force", "version_as_at": "2026-06-04", "version_id": "C2026C00227",
         "compilation_number": "98", "last_amending_instrument": "Strengthening Oversight Act 2025", "document_url": "",
         "document_kinds": "principal_act", "not_crawled_reason": ""},
        {"series": "Act", "portal_id": "C2004A99999", "law_number": "No. 1, 1999", "title": "An Amending Act 1999",
         "is_principal": "False", "legal_status": "in_force", "version_as_at": "1999-01-01", "version_id": "",
         "compilation_number": "0", "last_amending_instrument": "", "document_url": "", "document_kinds": "",
         "not_crawled_reason": "not principal"},
    ]
    stored = [{"doc_id": "au-pa1988-001", "source_url": links[0]["url"], "access_date": "2026-09-15T12:33:19Z",
               "local_path": "raw/au/privacy_act_1988/x__page.html"}]
    run = _folder(tmp_path, links, census, stored, census_cols)

    rows = checker.rows_for(run)
    assert len(rows) == 1
    r = rows[0]
    assert (r["in_force"], r["enacted_on"]) == ("yes", "1988-12-14")
    assert (r["effective_date"], r["effective_until"], r["compilation_number"]) == ("2026-06-04", "2026-12-10", 98)
    assert (r["last_amended"], r["scraped"]) == ("2025", "yes")

    both = checker.rows_for(run, include_unfetched=True)
    other = [x for x in both if x["portal_id"] == "C2004A99999"][0]
    assert (other["scraped"], other["notes"]) == ("no", "not principal")
    assert checker.main([str(run)]) == 0


def test_the_use_column_marks_amendments_as_linkage_unless_the_stored_text_is_older(tmp_path):
    from p1_scrape.adapters.au_legislation import checker
    links = [
        {"url": "https://www.legislation.gov.au/act/A", "law_name_guess": "Data Protection Act",
          "contract_meta": {"portal_id": "A", "law_number": "No. 119, 1988", "document_kind": "principal_act",
                            "legal_status": "in_force", "version_as_at": "2019-01-01",
                            "last_amending_instrument": "No. 98, 2021"}},
        {"url": "https://www.legislation.gov.au/act/B", "law_name_guess": "Data Protection (Amendment) Act",
          "contract_meta": {"portal_id": "B", "law_number": "No. 98, 2021", "document_kind": "amending_act",
                            "legal_status": "in_force", "version_as_at": "2025-06-01", "published_on": "2025-06-01"}},
        {"url": "https://www.legislation.gov.au/act/C", "law_name_guess": "Telecommunications Act",
          "contract_meta": {"portal_id": "C", "law_number": "No. 47, 1997", "document_kind": "principal_act",
                            "legal_status": "in_force", "version_as_at": "2026-01-01"}},
    ]
    census_cols = ["portal_id", "law_number", "title", "legal_status", "version_as_at", "document_url",
                   "document_kinds", "not_crawled_reason"]
    census = [{"portal_id": p, "law_number": n, "title": t, "legal_status": "in_force", "version_as_at": v,
                "document_url": "", "document_kinds": "principal_act", "not_crawled_reason": ""}
              for p, n, t, v in (("A", "No. 119, 1988", "Data Protection Act", "2019-01-01"),
                                 ("C", "No. 47, 1997", "Telecommunications Act", "2026-01-01"))]
    stored = [{"doc_id": f"x-{i}-001", "source_url": l["url"], "access_date": "2026-09-15T00:00:00Z",
                "local_path": f"raw/x/{i}__native.pdf"} for i, l in enumerate(links)]
    run = _folder(tmp_path, links, census, stored, census_cols)

    use = {r["law_number"]: r["use"] for r in checker.rows_for(run)}
    assert use["No. 119, 1988"] == "evidence, text stale"    # its text is 2019, the amendment 2025
    assert use["No. 98, 2021"] == "linkage, text needed"
    assert use["No. 47, 1997"] == "evidence"                    # never amended


def test_a_seed_with_no_indicator_tag_is_still_collected():
    """The Commonwealth of Australia Constitution Act is a seed that claims no indicator (2026-09-19).

    It is in the Q series, which the Act-collection harvest never returns, so only the seed reaches it; before this
    the pillar filter dropped every untagged seed, and it could not be collected at all. A seed tagged for other
    pillars is still left out.
    """
    cfg = _cfg()
    cfg["seed_laws"] = SEEDS + [
        {"law_name": "Commonwealth of Australia Constitution Act", "url": WWW + "/C2004Q00685", "indicators": [],
         "provenance": "the developer, 2026-09-19"},
        {"law_name": "A law for another pillar", "url": WWW + "/C2004A09999", "indicators": ["P1-I1"]},
    ]
    adapter = m.AuLegislationAdapter(cfg, client=_client(FakeSession()), www_client=_client(FakeSession(), 3.0))
    seeds = adapter._seed_by_id([6, 7])
    assert "C2004Q00685" in seeds and "C2004A09999" not in seeds
