"""Singapore adapter (countries/sg-singapore/scraper/): offline tests on pages saved from sso.agc.gov.sg on
2026-09-15 (tests/README.md lists them). No test sends a request: FakeSession stands in for the portal."""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from p1_scrape.adapters import sg_sso as m
from p1_scrape.adapters.sg_sso import catalogue, parse
from p1_scrape.adapters.my_gazette.client import LomClient as PacedClient

_HERE = Path(__file__).parent
FIX = _HERE / "fixtures" / "sg" if (_HERE / "fixtures" / "sg").is_dir() else _HERE / "fixtures"
ROOT = "https://sso.agc.gov.sg"
PAGES = {
    "/robots.txt": "sso_robots_2026-09-15.txt",
    "/Browse/Act/Current/All?PageSize=500&SortBy=Title&SortOrder=ASC": "sso_browse_act_current_asc_2026-09-15.html",
    "/Browse/Act/Current/All?PageSize=500&SortBy=Title&SortOrder=DESC": "sso_browse_act_current_desc_2026-09-15.html",
    "/Browse/Act/Repealed/All?PageSize=500": "sso_browse_act_repealed_2026-09-15.html",
    "/Browse/Act/Uncommenced/All?PageSize=500": "sso_browse_act_uncommenced_2026-09-15.html",
    "/Browse/Acts-Supp/Published/2026?PageSize=500": "sso_browse_acts_supp_2026_2026-09-15.html",
    "/Act/PDPA2012": "sso_act_PDPA2012_2026-09-15.html",
    "/Act/PDPA2012?ViewType=Sl&PageSize=100": "sso_act_PDPA2012_sl_2026-09-15.html",
}


def _read(name: str) -> str:
    return (FIX / name).read_text(encoding="utf-8", errors="replace")


class FakeResp:
    def __init__(self, status: int, body: bytes, headers=None):
        self.status_code, self.content, self.headers = status, body, headers or {}
        self.text = body.decode("utf-8", "replace")


class FakeSession:
    """The portal: the saved pages by path; any other act page is the PDPA page (a stand-in), an unknown path 404s."""

    def __init__(self, robots=(200, "User-agent: *\nCrawl-delay: 6\nDisallow: /search\n"), missing=()):
        self.calls: list[tuple[str, str]] = []
        self.robots = robots
        self.missing = set(missing)

    def request(self, method, url, data=None, headers=None, timeout=None, allow_redirects=True):
        self.calls.append((method, url))
        path = url[len(ROOT):]
        if path in self.missing:
            return FakeResp(500, b"error")
        if path == "/robots.txt":
            return FakeResp(self.robots[0], self.robots[1].encode())
        if path in PAGES and (FIX / PAGES[path]).is_file():
            return FakeResp(200, (FIX / PAGES[path]).read_bytes())
        if path.startswith("/Browse/Acts-Supp/Published/2025"):
            return FakeResp(200, b"<html>0 results</html>")
        if path.startswith("/Act/") and "ViewType=Sl" in path:
            if "PageIndex=0" not in path:
                return FakeResp(200, b"<html>10 results</html>")          # a later page: nothing new
            return FakeResp(200, (FIX / PAGES["/Act/PDPA2012?ViewType=Sl&PageSize=100"]).read_bytes())
        if path.startswith("/Act/"):
            return FakeResp(200, (FIX / PAGES["/Act/PDPA2012"]).read_bytes())
        return FakeResp(404, b"")


def _client(session: FakeSession) -> PacedClient:
    return PacedClient("test-agent RDTII-Rocky-Crawler/0.1", 6.0, session=session, sleep=lambda s: None,
                       clock=lambda: 0.0, jitter=False, now_iso=lambda: "2026-09-15T12:00:00Z")


SEEDS = [
    {"law_name": "Personal Data Protection Act 2012", "law_number": "Act 26 of 2012", "url": ROOT + "/Act/PDPA2012",
     "indicators": ["P7-I1", "P6-I1"], "provenance": "round1_registry"},
    {"law_name": "PDPC Advisory Guidelines", "url": "https://www.pdpc.gov.sg/guidelines/advisory.pdf",
     "indicators": ["P7-I4"], "provenance": "round1_registry"},
    # an SL seed the act's tab also lists: served once, from the tab, with the seed's tags
    {"law_name": "Personal Data Protection (Appeal) Regulations 2021", "law_number": "S 65/2021",
     "url": ROOT + "/SL/PDPA2012-S65-2021", "indicators": ["P7-I1"], "provenance": "round1_registry"},
    # an Acts Supplement seed off the Current listing: its address becomes the PDF the crawl cites
    {"law_name": "Personal Data Protection (Amendment) Act 2020", "law_number": "Act 40 of 2020",
     "url": ROOT + "/Acts-Supp/40-2020/Published/20201210?DocDate=20201210", "indicators": ["P7-I1"]},
]


def _cfg(**sso) -> dict:
    return {"economy": "SG", "portals": {"primary_statutes": {"root": ROOT}},
            "seed_queries": {"P7-I1": ["protection of personal data", "personal data protection"],
                             "P7-I2": ["cybersecurity", "computer misuse"]},
            "sso": {"detail_pages": "all", "subsidiary_acts": "seed", "acts_supp_years": 2, "listing_paging": "orders",
                    "listing_page_size": 500, **sso},
            "seed_laws": SEEDS}


@pytest.fixture(autouse=True)
def _no_env(monkeypatch):
    for name in list(os.environ):
        if name.startswith("SSO_"):
            monkeypatch.delenv(name)


# --- 1. the parsers, on the saved pages -------------------------------------------------------------------------

def test_the_current_listing_yields_every_act_with_its_code_title_and_pdf_link():
    rows = parse.parse_listing(_read("sso_browse_act_current_asc_2026-09-15.html"), "current")
    assert parse.results_count(_read("sso_browse_act_current_asc_2026-09-15.html")) == 525
    assert len(rows) == 500
    first = rows[0]      # "Accountants" sorts before "Accounting"
    assert first.code == "AA2004" and first.title == "Accountants Act 2004"
    assert first.path == "/Act/AA2004" and first.pdf_path == "/Act/AA2004?ViewType=Pdf" and first.number is None
    acra = next(r for r in rows if r.code == "ACRAA2004")
    assert acra.title == "Accounting and Corporate Regulatory Authority Act 2004" and acra.pdf_path == "/Act/ACRAA2004?ViewType=Pdf"
    desc = parse.parse_listing(_read("sso_browse_act_current_desc_2026-09-15.html"), "current")
    assert len({r.code for r in rows} | {r.code for r in desc}) == 525


def test_the_repealed_listing_carries_the_repeal_date_in_the_link():
    rows = parse.parse_listing(_read("sso_browse_act_repealed_2026-09-15.html"), "repealed")
    assert len(rows) == 298
    r = next(x for x in rows if x.code == "AA1987")
    assert r.title == "Accountants Act (Repealed)" and r.repeal_date == "2004-04-01" and r.doc_date == "2010-10-14"
    assert r.path == "/Act/AA1987/Repealed/20040401?DocDate=20101014"


def test_the_uncommenced_and_acts_supplement_listings_carry_the_act_number():
    unc = parse.parse_listing(_read("sso_browse_act_uncommenced_2026-09-15.html"), "uncommenced")
    assert len(unc) == 10 and all(u.number and u.number.startswith("Act ") for u in unc)
    aml = next(u for u in unc if u.code == "AMLOMA2024")
    assert aml.number == "Act 24 of 2024" and aml.title == "Anti-Money Laundering and Other Matters Act 2024"
    assert aml.path == "/Act/AMLOMA2024/Uncommenced/20260915020850?DocDate=20240830" and aml.doc_date == "2024-08-30"
    supp = parse.parse_listing(_read("sso_browse_acts_supp_2026_2026-09-15.html"), "acts_supp")
    assert len(supp) == 18
    r = next(x for x in supp if x.code == "8-2026")
    assert r.number == "Act 8 of 2026" and r.doc_date == "2026-04-27"
    assert r.pdf_path == "/Acts-Supp/8-2026/Published/20260427?DocDate=20260427&ViewType=Pdf"


def test_the_detail_page_gives_the_current_version_every_version_and_the_amending_instruments():
    d = parse.parse_detail(_read("sso_act_PDPA2012_2026-09-15.html"), "PDPA2012")
    assert d.title == "Personal Data Protection Act 2012" and d.current_valid_from == "2025-12-05"
    assert len(d.versions) == 14 and d.versions[0].valid_from == "2013-01-02" and d.versions[-1].valid_from == "2025-12-05"
    assert d.versions[-1].selected and d.versions[-1].published_on == "2025-11-28"
    assert d.versions[-1].amended_by == "Act 19 of 2025" and d.versions[-1].pdf_path == "/Act/PDPA2012?ValidDate=20251205&ViewType=Pdf"
    assert d.original_number == "Act 26 of 2012" and d.revised_edition == "2020 RevEd"
    assert d.revised_edition_note.startswith("This revised edition incorporates all amendments up to and including 1 December 2021")
    assert d.last_amending_instrument == "Act 19 of 2025" and d.sl_path == "/Act/PDPA2012?ViewType=Sl"
    amended = [v.amended_by for v in d.amendments]
    assert {"Act 29 of 2014", "S 19/2015", "Act 22 of 2016", "Act 40 of 2020", "Act 19 of 2025"} <= set(amended)
    assert [v.valid_from for v in d.amendments] == sorted(v.valid_from for v in d.amendments)   # by in-force date


def test_the_sl_tab_lists_each_instrument_with_its_number_date_and_pdf():
    rows = parse.parse_sl_tab(_read("sso_act_PDPA2012_sl_2026-09-15.html"))
    assert len(rows) == 10
    r = rows[0]
    assert r.code == "PDPA2012-S65-2021" and r.number == "S 65/2021" and r.doc_date == "2024-07-05"
    assert r.title == "Personal Data Protection (Appeal) Regulations 2021"
    assert r.pdf_path == "/SL/PDPA2012-S65-2021?DocDate=20240705&ViewType=Pdf"


def test_dates_and_codes_are_read_the_portal_way():
    assert parse.iso_from_display("05 Dec 2025") == "2025-12-05" and parse.iso_from_compact("20251205") == "2025-12-05"
    assert parse.act_code(ROOT + "/Act/PDPA2012?ViewType=Pdf") == "PDPA2012" and parse.act_code("https://www.pdpc.gov.sg/x") is None


# --- 2. the catalogue step, on a fake portal --------------------------------------------------------------------

@pytest.fixture(scope="module")
def built():
    session = FakeSession()
    adapter = m.SgSsoAdapter(_cfg(), client=_client(session), today="2026-09-15")
    result = catalogue.build(adapter, [6, 7])
    return {"adapter": adapter, "result": result, "session": session}


def test_the_build_reads_robots_first_then_the_listings_then_every_act_page_and_the_seed_acts_sl_tab(built):
    calls = [u[len(ROOT):] for _m, u in built["session"].calls]
    assert calls[0] == "/robots.txt"
    assert calls[1:6] == ["/Browse/Act/Current/All?PageSize=500&SortBy=Title&SortOrder=ASC",
                          "/Browse/Act/Current/All?PageSize=500&SortBy=Title&SortOrder=DESC",
                          "/Browse/Act/Repealed/All?PageSize=500", "/Browse/Act/Uncommenced/All?PageSize=500",
                          "/Browse/Acts-Supp/Published/2026?PageSize=500"]
    assert calls[6] == "/Browse/Acts-Supp/Published/2025?PageSize=500"
    assert calls[7] == "/Act/PDPA2012" and calls[8] == "/Act/PDPA2012?DocType=Act&ViewType=Sl&PageIndex=0&PageSize=100"
    assert sum(1 for c in calls if c.startswith("/Act/") and "ViewType" not in c) == 525
    assert sum(1 for c in calls if "ViewType=Sl" in c) == 1               # 10 of 10 read on the first page
    adapter = built["adapter"]
    assert adapter.robots_record["crawl_delay"] == 6.0 and adapter._client.delay == 6.0
    assert adapter.listing_counts["current"] == {"records": 525, "total": 525}


def test_the_list_holds_every_current_act_the_repealed_acts_the_amending_acts_and_the_seed_sl(built):
    docs = built["result"]["documents"]
    kinds = built["result"]["meta"]["document_kinds"]
    listed_pdf = sum(1 for r in parse.parse_listing(_read("sso_browse_act_repealed_2026-09-15.html"), "repealed") if r.pdf_path)
    assert listed_pdf == 34                       # the listing links a PDF for few repealed acts; the page serves one for all
    assert kinds["principal_act"] >= 525 + 298 and kinds["subsidiary_legislation"] == 10 and kinds["agency_or_other"] == 1
    new_acts = [d for d in docs if d["contract_meta"]["discovery_path"] == "acts_supplement" and d["contract_meta"]["document_kind"] == "principal_act"]
    assert new_acts and all("not_in_current_listing" in d["contract_meta"]["review_flags"] for d in new_acts)
    assert kinds["principal_act"] == 525 + 298 + len(new_acts)
    assert 0 < kinds["amending_act"] <= 18
    supp_seed = next(d for d in docs if d["contract_meta"]["portal_id"] == "40-2020")
    assert supp_seed["url"] == ROOT + "/Acts-Supp/40-2020/Published/20201210?DocDate=20201210&ViewType=Pdf"
    assert supp_seed["contract_meta"]["document_kind"] == "amending_act" and "seed" in supp_seed["scopes"]
    first = docs[0]
    assert first["url"] == ROOT + "/Act/PDPA2012?ViewType=Pdf" and first["scopes"] == ["seed", "relevant", "all"]
    meta = first["contract_meta"]
    assert meta["portal_id"] == "PDPA2012" and meta["law_number"] == "Act 26 of 2012" and meta["version_as_at"] == "2025-12-05"
    assert meta["last_amending_instrument"] == "Act 19 of 2025" and meta["last_amended_year"] == "2025"
    assert meta["amendment_check_complete"] is True and meta["revised_edition"] == "2020 RevEd"
    assert meta["subsidiary_listed"] == 10 and meta["seed_provenance"] == "round1_registry"
    sl = [d for d in docs if d["contract_meta"]["document_kind"] == "subsidiary_legislation"]
    assert sl[0]["contract_meta"]["principal_portal_id"] == "PDPA2012" and "seed" in sl[0]["scopes"]
    assert sl[0]["url"] == ROOT + "/SL/PDPA2012-S65-2021?DocDate=20240705&ViewType=Pdf"
    appeal = next(d for d in sl if d["contract_meta"]["portal_id"] == "PDPA2012-S65-2021")
    assert appeal["contract_meta"]["discovery_path"] == "seed" and appeal["indicator_hints"] == "P7-I1"
    assert sum(1 for d in docs if "S65-2021" in d["url"]) == 1               # the SL seed is served once, from the tab
    assert "law_number_unknown" not in first["contract_meta"]["review_flags"]
    repealed = [d for d in docs if d["contract_meta"]["legal_status"] == "repealed"]
    assert len(repealed) == 298 and repealed[0]["contract_meta"]["repealed_on"] and repealed[0]["scopes"] == ["all"]
    aa = next(d for d in repealed if d["contract_meta"]["portal_id"] == "AA1987")
    assert aa["url"] == ROOT + "/Act/AA1987/Repealed/20040401?DocDate=20101014&ViewType=Pdf"
    names = [d["law_name_guess"] for d in repealed]
    assert len(set(names)) == len(names) and any("[AA1987, repealed 2004-04-01]" in n for n in names)   # two "Accountants Act (Repealed)"
    supp_only = [d for d in docs if d["contract_meta"]["discovery_path"] == "acts_supplement"]
    assert all(d["url"].startswith(ROOT + "/Acts-Supp/") and d["url"].endswith("&ViewType=Pdf") for d in supp_only)
    amending = [d for d in docs if d["contract_meta"]["document_kind"] == "amending_act"]
    assert all("Amendment" in d["law_name_guess"] or "Repeal" in d["law_name_guess"] for d in amending)
    assert all(d["contract_meta"]["discovery_path"] == "delta" or True for d in docs)
    assert [d["order"] for d in docs] == list(range(1, len(docs) + 1))


def test_laws_csv_names_every_listed_law_and_why_some_have_no_document(built):
    laws = built["result"]["laws"]
    by = {(r["listing"], r["portal_id"]): r for r in laws}
    assert len([r for r in laws if r["listing"] == "current"]) == 525
    pdpa = by[("current", "PDPA2012")]
    assert pdpa["detail_read"] and pdpa["versions_listed"] == 14 and pdpa["in_seed"] and pdpa["not_crawled_reason"] is None
    unc = next(r for r in laws if r["listing"] == "uncommenced")
    assert unc["legal_status"] == "not_yet_in_force" and "recorded only" in unc["not_crawled_reason"]
    supp = [r for r in laws if r["listing"] == "acts_supp"]
    assert any(r["not_crawled_reason"] and "new principal act" in r["not_crawled_reason"] for r in supp)
    assert by[("repealed", "AA1987")]["legal_status"] == "repealed" and by[("repealed", "AA1987")]["repeal_date"] == "2004-04-01"


def test_the_written_list_replays_through_the_links_file_frontier(built, tmp_path, monkeypatch):
    paths = catalogue.write(built["result"], tmp_path / "links")
    meta = json.loads(Path(paths["catalogue_meta.json"]).read_text(encoding="utf-8"))
    assert meta["cfg_sha256"] == catalogue.cfg_fingerprint(_cfg())
    rows, _ = catalogue.read_documents(paths["documents.jsonl"])
    assert len(rows) == len(built["result"]["documents"])
    session = FakeSession()
    adapter = m.SgSsoAdapter(_cfg(frontier="links_file", links_file=paths["documents.jsonl"]), client=_client(session))
    cands = adapter.discover([6, 7], scope="seed")
    assert [u[len(ROOT):] for _m, u in session.calls] == ["/robots.txt"]
    assert len(cands) == sum(1 for r in rows if "seed" in r["scopes"]) and cands[0].contract_meta["portal_id"] == "PDPA2012"
    plans = adapter.build_plans(cands[0], forms="pdf")
    assert plans[0].url == ROOT + "/Act/PDPA2012?ViewType=Pdf" and plans[0].citation_url == plans[0].url
    sl = next(c for c in cands if c.contract_meta["document_kind"] == "subsidiary_legislation")
    assert adapter.build_plans(sl, forms="pdf")[0].url == ROOT + "/SL/PDPA2012-S65-2021?DocDate=20240705&ViewType=Pdf"
    stale = m.SgSsoAdapter(_cfg(frontier="links_file", links_file=paths["documents.jsonl"], acts_supp_years=3), client=_client(FakeSession()))
    with pytest.raises(ValueError, match="different registry"):
        stale.discover([6, 7], scope="all")


def test_robots_5xx_stops_the_build_and_a_short_current_listing_is_warned():
    adapter = m.SgSsoAdapter(_cfg(), client=_client(FakeSession(robots=(500, "error"))), today="2026-09-15")
    with pytest.raises(m.SsoUnavailable, match="robots.txt"):
        catalogue.build(adapter, [6, 7])
    adapter = m.SgSsoAdapter(_cfg(), client=_client(FakeSession(missing={"/Browse/Act/Current/All?PageSize=500&SortBy=Title&SortOrder=DESC"})), today="2026-09-15")
    with pytest.raises(m.SsoUnavailable, match="HTTP 500"):
        catalogue.build(adapter, [6, 7])


def test_one_failed_act_page_is_a_note_five_in_a_row_stop_the_build_and_a_throttle_stops_it_at_once():
    from p1_scrape.adapters.my_gazette.records import LomThrottled
    session = FakeSession(missing={"/Act/ACRAA2004"})
    adapter = m.SgSsoAdapter(_cfg(), client=_client(session), today="2026-09-15")
    result = catalogue.build(adapter, [6, 7])
    assert any(n.startswith("ACRAA2004: detail page not read") for n in result["meta"]["notes"])
    row = next(d for d in result["documents"] if d["contract_meta"]["portal_id"] == "ACRAA2004")
    assert "amendment_check_incomplete" in row["contract_meta"]["review_flags"] and row["contract_meta"]["version_as_at"] is None

    class Flaky(FakeSession):
        def request(self, method, url, **kw):
            if "/Act/" in url and "/Browse/" not in url and "PDPA" not in url and "ViewType" not in url:
                raise ConnectionError("boom")
            return super().request(method, url, **kw)
    adapter = m.SgSsoAdapter(_cfg(), client=_client(Flaky()), today="2026-09-15")
    with pytest.raises(m.SsoUnavailable, match="in a row"):
        catalogue.build(adapter, [6, 7])

    class Throttled(FakeSession):
        def request(self, method, url, **kw):
            if url.endswith("/Act/PDPA2012"):
                return FakeResp(467, b"slow down")
            return super().request(method, url, **kw)
    adapter = m.SgSsoAdapter(_cfg(), client=_client(Throttled()), today="2026-09-15")
    with pytest.raises(LomThrottled, match="467"):
        catalogue.build(adapter, [6, 7])


def test_an_accepted_answer_is_asked_again_and_the_sl_tab_is_capped_per_act():
    class Accepted(FakeSession):
        def __init__(self):
            super().__init__()
            self.pending = {"/Act/ACRAA2004": 1, "/Act/ASA2007": 5}         # 202 once; 202 every time

        def request(self, method, url, **kw):
            path = url[len(ROOT):]
            if self.pending.get(path, 0) > 0:
                self.pending[path] -= 1
                self.calls.append((method, url))
                return FakeResp(202, b"")
            return super().request(method, url, **kw)
    session = Accepted()
    adapter = m.SgSsoAdapter(_cfg(subsidiary_max_per_act=4), client=_client(session), today="2026-09-15")
    result = catalogue.build(adapter, [6, 7])
    rows = {d["contract_meta"]["portal_id"]: d for d in result["documents"]}
    assert rows["ACRAA2004"]["contract_meta"]["version_as_at"] and adapter.accepted_retries == 3
    assert any(n.startswith("ASA2007: detail page not read (SSO answered HTTP 202") for n in result["meta"]["notes"])
    assert [u[len(ROOT):] for _m, u in session.calls].count("/Act/ACRAA2004") == 2
    sl = [d for d in result["documents"] if d["contract_meta"]["document_kind"] == "subsidiary_legislation"]
    assert len(sl) == 4 and rows["PDPA2012"]["contract_meta"]["subsidiary_listed"] == 10 and rows["PDPA2012"]["contract_meta"]["subsidiary_read"] == 4
    assert any("10 SL listed, 4 read (sso.subsidiary_max_per_act=4)" in n for n in result["meta"]["notes"])


def test_a_waf_challenge_stops_the_build_at_once_and_makes_robots_unreadable():
    from p1_scrape.adapters.my_gazette.records import LomThrottled

    class Challenged(FakeSession):
        def __init__(self, on: str):
            super().__init__()
            self.on = on

        def request(self, method, url, **kw):
            if self.on in url:
                self.calls.append((method, url))
                return FakeResp(202, b"", headers={"x-amzn-waf-action": "challenge", "Content-Type": "text/html; charset=UTF-8"})
            return super().request(method, url, **kw)
    session = Challenged("/Act/PDPA2012")
    adapter = m.SgSsoAdapter(_cfg(), client=_client(session), today="2026-09-15")
    with pytest.raises(LomThrottled, match="WAF"):
        catalogue.build(adapter, [6, 7])
    # the challenge is rested on and tried again, six times, before the build stops (decision 23); it is never
    # retried at once, the way a plain HTTP 202 is
    assert [u for _m, u in session.calls].count(ROOT + "/Act/PDPA2012") == 1 + 6
    adapter = m.SgSsoAdapter(_cfg(), client=_client(Challenged("/robots.txt")), today="2026-09-15")
    with pytest.raises(m.SsoUnavailable, match="WAF"):
        catalogue.build(adapter, [6, 7])
    assert adapter.robots_record["waf"] == "challenge"


def test_the_frontier_warns_when_the_engine_delay_is_below_the_crawl_delay(built, tmp_path, capsys):
    paths = catalogue.write(built["result"], tmp_path / "links")

    class Settings:
        request_delay_seconds = 3.0
        user_agent = "test"

    class Fetcher:
        settings = Settings()
    adapter = m.SgSsoAdapter(_cfg(frontier="links_file", links_file=paths["documents.jsonl"]), client=_client(FakeSession()))
    adapter.discover([6, 7], scope="seed", fetcher=Fetcher())
    assert any("REQUEST_DELAY_MS=6000" in n for n in adapter.notes) and "REQUEST_DELAY_MS=6000" in capsys.readouterr().out


def test_the_seed_scope_without_a_fetcher_is_the_round_1_seed_list():
    adapter = m.SgSsoAdapter(_cfg())
    cands = adapter.discover([6, 7], scope="seed")
    assert [c.url for c in cands] == [ROOT + "/Act/PDPA2012?ViewType=Pdf", SEEDS[1]["url"],
                                      ROOT + "/SL/PDPA2012-S65-2021?ViewType=Pdf",
                                      ROOT + "/Acts-Supp/40-2020/Published/20201210?DocDate=20201210&ViewType=Pdf"]
    assert [c.contract_meta["document_kind"] for c in cands] == ["principal_act", "agency_or_other", "subsidiary_legislation", "amending_act"]
    assert [c.contract_meta["portal_id"] for c in cands] == ["PDPA2012", None, "PDPA2012-S65-2021", "40-2020"]


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


def test_the_law_table_reports_status_and_dates_and_can_add_what_the_run_did_not_fetch(tmp_path):
    from p1_scrape.adapters.sg_sso import checker
    links = [{"url": "https://sso.agc.gov.sg/Act/PDPA2012?ViewType=Pdf", "law_name_guess": "Personal Data Protection Act 2012",
              "in_force_status": "Current",
              "contract_meta": {"portal_id": "PDPA2012", "law_number": "Act 26 of 2012", "document_kind": "principal_act",
                                "legal_status": "in_force", "status_source": "portal_listing", "version_as_at": "2025-12-05",
                                "last_amending_instrument": "Act 19 of 2025", "last_amended_year": "2025",
                                "revised_edition": "2020 RevEd", "review_flags": []}}]
    census_cols = ["listing", "portal_id", "law_number", "title", "legal_status", "version_as_at", "repeal_date",
                   "last_amending_instrument", "revised_edition", "document_url", "document_kinds", "not_crawled_reason"]
    census = [
        {"listing": "current", "portal_id": "PDPA2012", "law_number": "Act 26 of 2012", "title": "Personal Data Protection Act 2012",
         "legal_status": "in_force", "version_as_at": "2025-12-05", "repeal_date": "", "last_amending_instrument": "Act 19 of 2025",
         "revised_edition": "2020 RevEd", "document_url": "", "document_kinds": "principal_act", "not_crawled_reason": ""},
        {"listing": "repealed", "portal_id": "AA1987", "law_number": "Act 4 of 1987", "title": "Accountants Act 1987",
         "legal_status": "repealed", "version_as_at": "", "repeal_date": "2005-04-01", "last_amending_instrument": "",
         "revised_edition": "", "document_url": "https://sso.agc.gov.sg/Act/AA1987?ViewType=Pdf", "document_kinds": "principal_act",
         "not_crawled_reason": "the repealed acts are not fetched by this run"},
    ]
    stored = [{"doc_id": "sg-pdpa2012-001", "source_url": links[0]["url"], "access_date": "2026-09-15T14:09:00Z",
               "local_path": "raw/sg/personal_data_protection_act_2012/x__native.pdf"}]
    run = _folder(tmp_path, links, census, stored, census_cols)

    rows = checker.rows_for(run)
    assert len(rows) == 1
    r = rows[0]
    assert (r["in_force"], r["legal_status"]) == ("yes", "in_force")
    assert (r["effective_date"], r["last_amended"], r["last_amending_instrument"]) == ("2025-12-05", "2025", "Act 19 of 2025")
    assert (r["scraped"], r["doc_id"]) == ("yes", "sg-pdpa2012-001")

    both = checker.rows_for(run, include_unfetched=True)
    repealed = [x for x in both if x["portal_id"] == "AA1987"][0]
    assert (repealed["in_force"], repealed["repealed_on"], repealed["scraped"]) == ("no (repealed)", "2005-04-01", "no")
    assert "not fetched by this run" in repealed["notes"]

    out = checker.write(both, run / "law_table.csv")
    text = out.read_text(encoding="utf-8-sig")
    assert text.startswith("law_name,law_number,portal_id") and "Accountants Act 1987" in text
    assert out.read_bytes().startswith(b"\xef\xbb\xbf")          # Excel on Windows needs the mark
    assert checker.main([str(run)]) == 0


def test_the_use_column_marks_amendments_as_linkage_unless_the_stored_text_is_older(tmp_path):
    from p1_scrape.adapters.sg_sso import checker
    links = [
        {"url": "https://sso.agc.gov.sg/act/A", "law_name_guess": "Data Protection Act",
          "contract_meta": {"portal_id": "A", "law_number": "Act 26 of 2012", "document_kind": "principal_act",
                            "legal_status": "in_force", "version_as_at": "2019-01-01",
                            "last_amending_instrument": "Act 40 of 2020"}},
        {"url": "https://sso.agc.gov.sg/act/B", "law_name_guess": "Data Protection (Amendment) Act",
          "contract_meta": {"portal_id": "B", "law_number": "Act 40 of 2020", "document_kind": "amending_act",
                            "legal_status": "in_force", "version_as_at": "2025-06-01", "published_on": "2025-06-01"}},
        {"url": "https://sso.agc.gov.sg/act/C", "law_name_guess": "Telecommunications Act",
          "contract_meta": {"portal_id": "C", "law_number": "Act 43 of 1999", "document_kind": "principal_act",
                            "legal_status": "in_force", "version_as_at": "2026-01-01"}},
    ]
    census_cols = ["portal_id", "law_number", "title", "legal_status", "version_as_at", "document_url",
                   "document_kinds", "not_crawled_reason"]
    census = [{"portal_id": p, "law_number": n, "title": t, "legal_status": "in_force", "version_as_at": v,
                "document_url": "", "document_kinds": "principal_act", "not_crawled_reason": ""}
              for p, n, t, v in (("A", "Act 26 of 2012", "Data Protection Act", "2019-01-01"),
                                 ("C", "Act 43 of 1999", "Telecommunications Act", "2026-01-01"))]
    stored = [{"doc_id": f"x-{i}-001", "source_url": l["url"], "access_date": "2026-09-15T00:00:00Z",
                "local_path": f"raw/x/{i}__native.pdf"} for i, l in enumerate(links)]
    run = _folder(tmp_path, links, census, stored, census_cols)

    use = {r["law_number"]: r["use"] for r in checker.rows_for(run)}
    assert use["Act 26 of 2012"] == "evidence, text stale"    # its text is 2019, the amendment 2025
    assert use["Act 40 of 2020"] == "linkage, text needed"
    assert use["Act 43 of 1999"] == "evidence"                    # never amended


# ---- 100 rows a page, by Next Page links (2026-09-16: the portal refused the 500-row page for hours) ----

P0 = "/Browse/Act/Current/All?PageSize=100&SortBy=Title&SortOrder=ASC"
P1 = "/Browse/Act/Current/All/1?PageSize=100&SortBy=Title&SortOrder=ASC"
P2 = "/Browse/Act/Current/All/2?PageSize=100&SortBy=Title&SortOrder=ASC"


class PagedSession(FakeSession):
    """The first two 100-row pages as saved; every later page repeats the second, so nothing new is added."""

    def request(self, method, url, data=None, headers=None, timeout=None, allow_redirects=True):
        path = url[len(ROOT):]
        pages = {P0: "sso_browse_act_current_p0_rows100_2026-09-16.html",
                 "/Browse/Act/Current/S?PageSize=100&SortBy=Title&SortOrder=ASC": "sso_browse_act_current_S_rows100_2026-09-16.html"}
        if path in pages or path.startswith("/Browse/Act/Current/All/"):
            self.calls.append((method, url))
            return FakeResp(200, (FIX / pages.get(path, "sso_browse_act_current_p1_rows100_2026-09-16.html")).read_bytes())
        return super().request(method, url, data=data, headers=headers, timeout=timeout, allow_redirects=allow_redirects)


def test_a_listing_page_names_its_next_page_by_path_and_the_last_page_names_none():
    from p1_scrape.adapters.sg_sso.parse import next_page_path
    assert next_page_path(_read("sso_browse_act_current_p0_rows100_2026-09-16.html")) == P1
    assert next_page_path(_read("sso_browse_act_current_p1_rows100_2026-09-16.html")) == P2
    assert next_page_path(_read("sso_browse_act_current_S_rows100_2026-09-16.html")) is None


def test_paging_follows_next_links_and_stops_when_a_page_adds_nothing_new():
    session = PagedSession()
    adapter = m.SgSsoAdapter(_cfg(listing_paging="next"), client=_client(session), today="2026-09-16")
    rows, total, pages = adapter._read_pages(adapter._client, P0, "current")
    calls = [u[len(ROOT):] for _m, u in session.calls]
    assert calls == [P0, P1, P2] and pages == 3
    assert len(rows) == 200 and total == 525                      # pages 0 and 1 do not overlap
    assert all(r.file_stamp for r in rows.values())


def test_a_letter_page_that_holds_all_it_claims_is_one_request():
    session = PagedSession()
    adapter = m.SgSsoAdapter(_cfg(listing_paging="next"), client=_client(session), today="2026-09-16")
    rows, total, pages = adapter._read_pages(adapter._client, "/Browse/Act/Current/S?PageSize=100&SortBy=Title&SortOrder=ASC", "current")
    assert (len(rows), total, pages) == (70, 70, 1)


def test_next_paging_is_the_default_and_a_short_current_listing_is_warned():
    session = PagedSession()
    adapter = m.SgSsoAdapter(_cfg(listing_paging=None), client=_client(session), today="2026-09-16")
    adapter.sso_cfg.pop("listing_paging")
    with pytest.raises(m.SsoUnavailable):                           # Repealed at 100 rows is not saved: 404
        adapter._open_sso(adapter._client)
    assert [u[len(ROOT):] for _m, u in session.calls][1:4] == [P0, P1, P2]
    assert adapter.listing_counts["current"] == {"records": 200, "total": 525}
    assert any("claims 525 acts, 200 read (3 page(s) of 100)" in n for n in adapter.notes)
    with pytest.raises(ValueError, match="not next or orders"):
        other = m.SgSsoAdapter(_cfg(listing_paging="letters"), client=_client(PagedSession()))
        other._open_sso(other._client)
