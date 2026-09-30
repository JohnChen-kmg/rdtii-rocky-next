"""Malaysia (Laws of Malaysia) adapter — offline tests against pages saved from lom.agc.gov.my on
2026-09-13. No test sends a request: the portal is replaced by FakeSession.

Replaces the Round 1 test_my_selection.py, which pinned the upload-order version picker.
"""
from __future__ import annotations

import base64
import json
import os
from pathlib import Path

import pytest

from p1_scrape.adapters import my_gazette as m

_HERE = Path(__file__).parent
FIX = _HERE / "fixtures" / "my" if (_HERE / "fixtures" / "my").is_dir() else _HERE / "fixtures"
LOM = "https://lom.agc.gov.my"
TODAY = "2026-09-13"


def _read(name: str) -> str:
    return (FIX / name).read_text(encoding="utf-8")


UPDATED_PAGE = "lom_principal_updated_2026-09-13.html"
UPDATED_RECORDS = json.loads(_read("lom_updated_records_2026-09-13.json"))["records"]
AMENDMENT_RECORDS = json.loads(_read("lom_amendment_records_2026-09-13.json"))["records"]
# Records the 2026-09-13 code review named: repeals by P.U. (A), "BELUM BERKUAT KUASA", a partial repeal,
# a superseded act, shared files, staged and partial commencements, curly apostrophes, '1959/63' years.
REVIEW_UPDATED = json.loads(_read("lom_updated_records_review_2026-09-13.json"))["records"]
REVIEW_AMENDMENTS = json.loads(_read("lom_amendment_records_review_2026-09-13.json"))["records"]
DETAIL_709 = _read("lom_act_detail_709_BI_2026-09-13.html")
DETAIL_A1727 = _read("lom_amendment_detail_A1727_BI_2026-09-13.html")
KEY = m.extract_response_key(_read(UPDATED_PAGE))

CONTRACT_TEXT_VERSION = {"consolidated", "reprint", "as_enacted", "point_in_time", "unknown", None}
CONTRACT_FLAGS = {"secondary_copy", "finding_aid_resolved", "filename_says_draft", "filename_says_repealed",
                  "number_mismatch", "stale_vs_portal", "no_parser_form", "migrated_from_0_2_0"}
CONTRACT_STATUS = {"in_force", "not_yet_in_force", "partially_in_force", "repealed", "unknown"}
CONTRACT_STATUS_SOURCE = {"portal_field", "portal_listing", "portal_remark", "document_text", "filename_marker", None}
CONTRACT_KIND = {"principal_act", "amending_act", "repealing_act", "commencement_instrument",
                 "subsidiary_legislation", "guidance", "code_or_standard", "official_announcement", "report",
                 "ownership_record", "intergovernmental_notification", "draft_or_bill", "other", None}


def _principal(act_no: str) -> m.PrincipalAct:
    rec = next(r for r in UPDATED_RECORDS + REVIEW_UPDATED if r["lgt_act_no"].strip() == act_no)
    return m.parse_principal(rec)


def _amendment(a: str) -> m.AmendingAct:
    return m.parse_amendment(next(r for r in AMENDMENT_RECORDS + REVIEW_AMENDMENTS if r["ACTNO_LEGISLATION"] == a))


def _encrypt(obj: dict, key_hex: str = KEY) -> dict:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    iv = os.urandom(12)
    sealed = AESGCM(bytes.fromhex(key_hex)).encrypt(iv, json.dumps(obj).encode(), None)
    ct, tag = sealed[:-16], sealed[-16:]
    return {"encrypted": True, "data": base64.b64encode(iv + tag + ct).decode()}


def _offline(updated=(), amendments=(), cfg=None) -> m.MyGazetteAdapter:
    """An adapter whose listings are loaded from records directly, for link and date logic."""
    ad = m.MyGazetteAdapter(cfg or {"economy": "MY", "lom": {}}, today=TODAY)
    for rec in updated:
        p = m.parse_principal(rec)
        ad.principals.setdefault(m._act_key(p.act_no), p)
    for rec in amendments:
        a = m.parse_amendment(rec)
        ad.amendments.setdefault(a.a_number, a)
    lowest = min(ad.amendments.values(), key=lambda a: m._a_number_int(a.a_number), default=None)
    ad.listing_floor = m.iso_date(lowest.publication) if lowest else None
    return ad


# --- decryption ---------------------------------------------------------------------------

def test_real_encrypted_listing_page_decrypts_with_the_key_the_page_publishes():
    payload = json.loads(_read("lom_updated_encrypted_page0_2026-09-13.json"))
    obj = m.decrypt_listing(payload, KEY)
    assert int(obj["recordsTotal"]) == 890
    assert len(obj["records"]) == 10
    assert obj["records"][0]["lgt_act_no"] == "884"


def test_decrypt_accepts_the_bare_base64_form_too():
    wrapped = _encrypt({"recordsTotal": 1, "records": [{"x": 1}]})
    assert m.decrypt_listing(wrapped["data"], KEY)["records"] == [{"x": 1}]


def test_listing_page_without_a_key_fails_loudly():
    with pytest.raises(RuntimeError):
        m.extract_response_key("<html>no key here</html>")


# --- the updated principal listing ---------------------------------------------------------

def test_principal_record_gives_title_as_at_and_encoded_document_url():
    p = _principal("709")
    assert p.title_bi == "PERSONAL DATA PROTECTION ACT 2010"
    assert p.as_at_bi == "01-07-2023"
    doc = m.choose_principal_document(p, ["eng", "msa"])
    assert doc.language == "eng" and doc.edition == "printed"
    assert doc.url == ("https://lom.agc.gov.my/ilims/upload/portal/akta/outputaktap/"
                       "1726091_BI/ACT%20709-REPRINT%202023.pdf")
    assert set(p.detail_links) == {"BI", "BM"}


def test_repealed_marker_after_the_link_is_read_and_kept_out_of_the_title():
    p = _principal("762")
    assert p.repealed_by == "Act 805"
    assert p.title_bi == "GOODS AND SERVICES TAX ACT 2014"
    assert (p.status_kind, p.status_marker) == ("repealed", "Repealed by Act 805")
    assert m.principal_status(p) == ("repealed", "portal_listing")


@pytest.mark.parametrize("act_no, repealed_by, marker", [
    ("691", "P.U. (A) 146/1969", "Repealed by Act P.U. (A) 146/1969"),
    ("192", "P.U.(A)46/1978", "Repealed by Act P.U.(A)46/1978"),
    ("278", "P.U. (A) 37/2008", "Repealed by P.U. (A) 37/2008"),
])
def test_repeal_marker_naming_a_pu_instrument_is_read(act_no, repealed_by, marker):
    p = _principal(act_no)
    assert (p.status_kind, p.repealed_by, p.status_marker) == ("repealed", repealed_by, marker)
    assert "Repealed" not in (p.title_bi or "") and "Dimansuhkan" not in (p.title_bm or "")


def test_not_yet_in_force_marker_in_a_title_is_a_status_not_part_of_the_title():
    p = _principal("775")
    assert p.title_bm == "AKTA PERUBATAN TRADISIONAL DAN KOMPLEMENTARI 2016"
    assert (p.status_kind, p.status_marker) == ("not_yet_in_force", "BELUM BERKUAT KUASA")
    assert m.principal_status(p) == ("not_yet_in_force", "portal_listing")


def test_partial_repeal_is_partially_in_force_with_the_english_marker():
    p = _principal("508")
    assert p.status_kind == "partially_repealed" and p.repealed_by == "Act 655"
    assert p.status_marker.startswith("Repealed by Act 655 in respect of its application to Peninsular Malaysia")
    assert m.principal_status(p) == ("partially_in_force", "portal_listing")


def test_superseded_counts_as_repealed_and_keeps_the_portals_words():
    p = _principal("384")                           # decision 10
    assert (p.status_kind, p.superseded_by, p.status_marker) == ("superseded", "Act 809", "Diganti oleh Akta 809")
    assert p.repealed_by is None
    assert m.principal_status(p) == ("repealed", "portal_listing")


def test_version_is_chosen_by_as_at_date_not_by_edition():
    # Act 26 lists a printed reprint as at 29-06-1947 and an online reprint as at 05-09-2022.
    p = _principal("26")
    doc = m.choose_principal_document(p, ["eng", "msa"])
    assert m.document_as_at(p, doc) == "05-09-2022"
    assert doc.edition == "online"


def test_a_document_never_borrows_another_editions_as_at_date():
    # 26/1947 lists only an online version, dated; its printed 1947 original has no date of its own.
    p = _principal("26/1947")
    original = next(d for d in p.documents if d.edition == "printed")
    assert m.document_as_at(p, original) is None
    assert m.choose_principal_document(p, ["eng"]).edition == "online"
    shared = m.choose_principal_document(p, ["eng"]).url
    assert m.choose_principal_document(p, ["eng"], exclude=frozenset({shared})).url == original.url


def test_online_reprint_is_taken_when_it_is_the_only_english_version():
    p = _principal("593")        # Criminal Procedure Code: BM printed 01-05-2023, BI online 04-07-2023
    doc = m.choose_principal_document(p, ["eng", "msa"])
    assert (doc.language, doc.edition, m.document_as_at(p, doc)) == ("eng", "online", "04-07-2023")
    assert p.online_marker is True


def test_act_listed_without_documents_yields_no_document():
    assert m.choose_principal_document(_principal("663"), ["eng", "msa"]) is None


# --- the amendment listing -----------------------------------------------------------------

def test_amendment_record_fields_and_effective_date_from_the_commencement_remark():
    a = _amendment("A1727")
    assert a.title_bi == "PERSONAL DATA PROTECTION (AMENDMENT) ACT 2024"
    assert a.project_id == "2430673"
    assert (a.royal_assent, a.publication) == ("09/10/2024", "17/10/2024")
    assert m.amendment_effective_date(a) == "2024-12-24"
    assert m.pu_b_refs(a) == ["P.U. (B) 522/2024"]
    assert {d.language for d in a.documents} == {"eng", "msa"}


@pytest.mark.parametrize("a_number, expected", [
    ("A1791", ("not_yet_in_force", "portal_remark")),          # "NOT YET IN FORCE"
    ("A1530", ("partially_in_force", "portal_remark")),        # "Not Yet In Force except ... (19-5-2017) ..."
    ("A1770", ("not_yet_in_force", "portal_listing")),         # commencement date field 01/01/2027
    ("A1486", ("unknown", None)),                              # a past date: not a statement that all is in force
])
def test_amendment_status_is_read_from_what_the_listing_states(a_number, expected):
    assert m.amendment_status(_amendment(a_number), TODAY) == expected


def test_amending_title_reduces_to_the_principal_title():
    assert m.amending_base_title("PERSONAL DATA PROTECTION (AMENDMENT) ACT 2024") == "PERSONAL DATA PROTECTION"
    assert m.title_matches_base("PERSONAL DATA PROTECTION ACT 2010", "PERSONAL DATA PROTECTION")
    assert m.title_matches_base("CRIMINAL PROCEDURE CODE", "CRIMINAL PROCEDURE CODE")
    assert not m.title_matches_base("PERSONAL DATA PROTECTION ACT 2010", "PERSONAL DATA")
    assert m.amending_base_title("SUPPLY ACT 2026") is None
    # a curly apostrophe and a '1959/63' year still match
    assert m.title_matches_base("EMPLOYEES' SOCIAL SECURITY ACT 1969",
                                m.amending_base_title("EMPLOYEES’ SOCIAL SECURITY (AMENDMENT) ACT 2026"))
    assert m.title_matches_base("IMMIGRATION ACT 1959/63", "IMMIGRATION")


def test_lom_dates_are_day_first():
    assert m.iso_date("01-07-2023") == "2023-07-01"
    assert m.iso_date("5/12/2025") == "2025-12-05"
    assert m.iso_date("1-3-2017 - except sections 17, 18, and 19") == "2017-03-01"
    assert m.iso_date("NOT YET IN FORCE") is None


def test_every_date_form_the_portal_writes_is_read():
    assert m.iso_date("2018-04-27") == "2018-04-27"                         # A1568's royal assent field
    assert m.iso_date("17 Oct 2024") == "2024-10-17"                        # a timeline display date
    assert m.all_dates("1 JANUARI 2025 (Seksyen 7) 1 APRIL 2025 (Seksyen 2) 1 JUN 2025 (Seksyen 6)") == [
        "2025-01-01", "2025-04-01", "2025-06-01"]
    assert m.all_dates(_amendment("A1764").commencement_remark) == ["2025-07-01", "2026-01-01"]
    assert m.all_dates(_amendment("A1649").commencement_remark) == ["2022-03-18", "2022-06-30", "2025-12-31"]
    assert m.all_dates("P.U. (B) 522/2024") == []


# --- linking amendments and judging currency, over the review records ----------------------

def test_title_links_survive_curly_apostrophes_slash_years_and_repealed_predecessors():
    ad = _offline(REVIEW_UPDATED, REVIEW_AMENDMENTS)
    link = {a: getattr(ad._principal_for(ad.amendments[a]), "act_no", None)
            for a in ("A1788", "A1790", "A1780", "A1601")}
    assert link == {"A1788": "4", "A1790": "155", "A1780": "317", "A1601": "317"}   # 317, not repealed 210


def test_a_stage_after_the_as_at_date_makes_the_amendment_later_but_counts_what_came_before():
    ad = _offline(REVIEW_UPDATED, REVIEW_AMENDMENTS)
    patents = ad.principals["291"]                      # as at 01-11-2023; A1649 stages 2022, 2022, 31/12/2025
    assert [a.a_number for a in ad._later_amendments(patents)] == ["A1649"]
    assert ad._last_incorporated(patents) == ("Act A1649", "2022")
    cand = ad._principal_candidate(patents, law=None, indicators=[])
    (entry,) = cand.contract_meta["linked_amendments"]
    assert entry["staged_across_as_at"] is True and "stale_vs_portal" in cand.contract_meta["crawl_flags"]


def test_partial_not_yet_in_force_remark_whose_dates_precede_the_as_at_is_incorporated():
    ad = _offline(REVIEW_UPDATED, REVIEW_AMENDMENTS)
    weights = ad.principals["71"]                       # as at 01-09-2017; A1530 dated 19-5-2017 and 1-8-2017
    assert ad._later_amendments(weights) == []
    assert ad._last_incorporated(weights) == ("Act A1530", "2017")


def test_last_amending_instrument_is_the_one_that_took_effect_last():
    ad = _offline(REVIEW_UPDATED, REVIEW_AMENDMENTS)
    # Prison Act: A1486 commenced 1-9-2015, A1474 commenced 15-1-2016
    assert ad._last_incorporated(ad.principals["537"]) == ("Act A1474", "2016")


def test_as_at_before_the_amendment_listing_starts_is_an_incomplete_check():
    ad = _offline(REVIEW_UPDATED, REVIEW_AMENDMENTS)
    assert ad.listing_floor == "2011-06-02"             # A1392's publication date
    meta = ad._principal_candidate(ad.principals["155"], law=None, indicators=[]).contract_meta
    assert meta["amendment_check_complete"] is False and meta["amendment_check_from"] == "2011-06-02"
    assert "amendment_check_incomplete" in meta["review_flags"]
    assert meta["amendments_after_as_at"] == ["Act A1790"]


def test_iso_royal_assent_date_reaches_enacted_on():
    ad = _offline(REVIEW_UPDATED, REVIEW_AMENDMENTS)
    (cand,) = ad._amendment_candidates(ad.amendments["A1568"], None, client=None)
    assert cand.contract_meta["enacted_on"] == "2018-04-27"
    assert "principal_unlinked" in cand.contract_meta["review_flags"]


# --- the detail-page timeline --------------------------------------------------------------

def test_timeline_lists_versions_amendments_and_subsidiary_legislation():
    entries = m.parse_timeline(DETAIL_709)
    assert [e.log_type for e in entries] == [
        "ORIGINAL", "REPRINT ONLINE", "SUBSIDIARY_LEGISLATION", "REPRINT",
        "SUBSIDIARY_LEGISLATION", "AMENDMENTS", "SUBSIDIARY_LEGISLATION"]
    original = entries[0]
    assert (original.publication_date, original.royal_assent_date) == ("10/06/2010", "02/06/2010")
    amendments = [e for e in entries if e.log_type == "AMENDMENTS"]
    assert amendments[0].project_id == _amendment("A1727").project_id
    reprint = next(e for e in entries if e.log_type == "REPRINT")
    assert reprint.file_url == m.choose_principal_document(_principal("709"), ["eng"]).url
    assert [e.pu_no for e in entries if e.log_type == "SUBSIDIARY_LEGISLATION"] == [
        "P.U. (B) 50/2023", "P.U. (B) 263/2023", "P.U. (B) 341/2025"]


def test_amending_acts_timeline_lists_its_commencement_order_with_the_real_dates():
    (order,) = m.parse_timeline(DETAIL_A1727)
    assert (order.log_type, order.pu_no, order.publication_date) == (
        "SUBSIDIARY_LEGISLATION", "P.U. (B) 522/2024", "24/12/2024")
    assert order.file_url == "https://lom.agc.gov.my/ilims/upload/portal/akta/outputp/2587515/PUB%20522_2024.pdf"
    assert m.all_dates(order.commencement_remark) == ["2025-01-01", "2025-04-01", "2025-06-01"]


def test_invalid_request_page_is_an_empty_timeline():
    assert m.parse_timeline("Invalid request") == []


def test_signed_link_target_can_be_read():
    href = _principal("709").detail_links["BI"]
    assert "act-detail.php?act=709&lang=BI" in m.decode_token_target(href)


# --- robots.txt ------------------------------------------------------------------------------

def test_robots_rules_follow_rfc_9309():
    rules = m.RobotsRules.parse(
        "User-agent: *\nDisallow: /principal.php?type=amendment\nDisallow: /*.pdf$\n"
        "Allow: /ilims/upload/portal/akta/outputaktap/*.pdf$\nCrawl-delay: 7\n", "RDTII-Rocky-Crawler")
    assert not rules.allowed(LOM + "/principal.php?type=amendment")
    assert rules.allowed(LOM + "/principal.php?type=updated")
    assert not rules.allowed(LOM + "/other/x.pdf")
    assert rules.allowed(LOM + "/ilims/upload/portal/akta/outputaktap/1/Act%20709.pdf")   # longer Allow wins
    assert rules.allowed(LOM + "/robots.txt")
    assert rules.min_delay() == 7


def test_robots_group_is_matched_on_the_crawlers_product_token_not_mozilla():
    assert m.robots_token(m._DEFAULT_UA) == "RDTII-Rocky-Crawler"
    rules = m.RobotsRules.parse("User-agent: *\nDisallow:\n\nUser-agent: RDTII-Rocky-Crawler\n"
                                "Disallow: /\nCrawl-delay: 12\n", m.robots_token(m._DEFAULT_UA))
    assert not rules.allowed(LOM + "/principal.php?type=updated") and rules.crawl_delay == 12


# --- discovery end to end, against a fake portal -----------------------------------------

class FakeResp:
    def __init__(self, status: int, body, headers=None):
        self.status_code = status
        self.headers = headers or {}
        if isinstance(body, (dict, list)):
            self._json, self.text = body, json.dumps(body)
        else:
            self._json, self.text = None, body
        self.content = self.text.encode()

    def json(self):
        if self._json is None:
            raise ValueError("not json")
        return self._json


class FakeSession:
    def __init__(self, robots=(500, "error"), updated=None, amendments=None, detail=None,
                 fail=None, omit_total=False):
        self.calls: list[tuple[str, str]] = []
        self.robots = robots
        self.updated = UPDATED_RECORDS if updated is None else updated
        self.amendments = AMENDMENT_RECORDS if amendments is None else amendments
        self.detail = {"709": DETAIL_709, "A1727": DETAIL_A1727} if detail is None else detail
        self.fail = fail or {}                     # URL fragment -> (status, headers)
        self.omit_total = omit_total

    def request(self, method, url, data=None, headers=None, timeout=None, allow_redirects=True):
        self.calls.append((method, url))
        for fragment, (status, hdrs) in self.fail.items():
            if fragment in url:
                return FakeResp(status, "unavailable", hdrs)
        if url.endswith("/robots.txt"):
            return FakeResp(*self.robots)
        if method == "GET" and "principal.php?type=" in url:
            return FakeResp(200, _read(UPDATED_PAGE))
        for endpoint, records in (("json-updated-2024.php", self.updated),
                                  ("json-amendment-2024.php", self.amendments)):
            if method == "POST" and url.endswith(endpoint):
                start, length = int(data["start"]), int(data["length"])
                body = {"draw": data["draw"], "records": records[start:start + length]}
                if not self.omit_total:
                    body["recordsTotal"] = len(records)
                return FakeResp(200, _encrypt(body))
        if method == "GET" and "processFile.php" in url:      # the portal answers a signed link with a 302
            target = m.decode_token_target(url) or ""
            act = next((k for k in self.detail if f"act={k}&" in target), "x")
            return FakeResp(302, "", {"Location": "act-detail.php?a=" + act})
        if method == "GET" and "act-detail.php?a=" in url:
            return FakeResp(200, self.detail.get(url.rsplit("a=", 1)[-1], "Invalid request"))
        return FakeResp(404, "not found")


CFG = {
    "economy": "MY",
    "lom": {"robots_5xx": "allow", "subsidiary_from_timeline": True},
    "seed_laws": [
        {"law_name": "Personal Data Protection Act 2010", "law_number": "Act 709",
         "url": "https://www.pdp.gov.my/ppdpv1/en/akta/", "indicators": ["P6-I1", "P7-I1"],
         "provenance": "round1_registry"},
        {"law_name": "Personal Data Protection (Amendment) Act 2024", "law_number": "Act A1727",
         "url": "https://www.pdp.gov.my/x/", "indicators": ["P6-I1", "P7-I3"]},
        {"law_name": "Cyber Security Act 2024", "law_number": "Act 854",
         "url": "https://lom.agc.gov.my", "indicators": ["P7-I2"]},
        {"law_name": "Personal Data Protection Guideline on Cross-Border Personal Data Transfer (GP 3/2025)",
         "law_number": "GP 3/2025", "url": "https://www.pdp.gov.my/ppdpv1/wp-content/uploads/2025/08/GP_CBPDT_EN-1.pdf",
         "indicators": ["P6-I4"], "provenance": "p3_request:DELTA_CRAWL_REQUEST_2026-07-14#6"},
    ],
    "seed_queries": {"P7-I1": ["protection of personal data"]},
}


def _cfg(**lom) -> dict:
    return {**CFG, "lom": {**CFG["lom"], **lom}}


def _adapter(cfg=CFG, ua="test-agent", **session_kw):
    """A fake clock that only moves when the client sleeps, so every recorded sleep is a full gap."""
    sleeps: list[float] = []
    now = [0.0]

    def sleep(s: float) -> None:
        sleeps.append(s)
        now[0] += s

    client = m.LomClient(ua, delay_seconds=3.0, session=FakeSession(**session_kw),
                         sleep=sleep, clock=lambda: now[0], jitter=False, now_iso=lambda: "2026-09-13T00:00:00Z")
    return m.MyGazetteAdapter(cfg, client=client, today=TODAY), client, sleeps


def _hosts(cands) -> set[str]:
    return {m.urlparse(c.url).hostname for c in cands}


def test_seed_discovery_links_the_amendment_its_commencement_order_and_the_stale_principal():
    adapter, client, sleeps = _adapter()
    cands = {c.law_number_guess: c for c in adapter.discover(pillars=[6, 7], scope="seed")}

    pdpa = cands["Act 709"]
    assert pdpa.url.endswith("ACT%20709-REPRINT%202023.pdf")
    assert pdpa.indicator_hints == "P6-I1,P7-I1"
    assert pdpa.seed_query == "personal data"
    meta = pdpa.contract_meta
    assert (meta["document_kind"], meta["version_as_at"], meta["text_version"]) == ("principal_act", "2023-07-01", "reprint")
    assert meta["amendments_after_as_at"] == ["Act A1727"]
    assert meta["crawl_flags"] == ["stale_vs_portal"]
    assert meta["seed_provenance"] == "round1_registry"
    (linked,) = meta["linked_amendments"]
    assert linked["link_source"] == "portal_timeline"
    assert linked["dates"] == ["2024-12-24", "2025-01-01", "2025-04-01", "2025-06-01"]   # listing + the order
    assert pdpa.in_force_status is None and meta["legal_status"] == "unknown"             # never defaulted
    assert pdpa.publication_date == "10/06/2010"   # from the timeline's ORIGINAL entry

    a1727 = cands["Act A1727"]
    assert a1727.indicator_hints is None and a1727.pillar_hint is None
    assert a1727.contract_meta["document_kind"] == "amending_act"
    assert a1727.contract_meta["principal_law_number"] == "Act 709"
    assert a1727.contract_meta["principal_link_source"] == "portal_timeline"
    assert a1727.contract_meta["commencement_instruments_found"] == ["P.U. (B) 522/2024"]
    assert "seed_indicator_hints_dropped" in a1727.contract_meta["review_flags"]

    order = cands["P.U. (B) 522/2024"]
    assert order.url.endswith("/outputp/2587515/PUB%20522_2024.pdf")
    assert (order.contract_meta["document_kind"], order.contract_meta["principal_law_number"],
            order.contract_meta["commences_law_number"]) == ("commencement_instrument", "Act 709", "Act A1727")
    assert order.indicator_hints is None

    # PDPA's timeline lists only P.U. (B) notices, and the default series is P.U. (A)
    assert not [c for c in cands.values() if c.contract_meta.get("document_kind") == "subsidiary_legislation"]

    assert cands["Act 854"].contract_meta["document_kind"] == "principal_act"
    guideline = cands["GP 3/2025"]
    assert guideline.url.endswith("GP_CBPDT_EN-1.pdf") and guideline.contract_meta["portal"] == "other"
    assert guideline.contract_meta["seed_provenance"] == "p3_request:DELTA_CRAWL_REQUEST_2026-07-14#6"

    # one pacer for every discovery request: robots, 2 listing pages, 2 listing POSTs, timelines, and a
    # closing wait so the engine's first lom document request is spaced from the last discovery request
    methods = [c[0] for c in client.session.calls]
    assert methods.count("POST") == 2
    assert len(sleeps) == len(client.session.calls) and all(s >= 3.0 for s in sleeps)
    assert adapter.last_request_at["lom.agc.gov.my"] is not None


def test_every_discovery_request_is_logged_with_its_time_and_wait_and_the_robots_decision_is_kept():
    adapter, client, _ = _adapter()
    adapter.discover(pillars=[6, 7], scope="seed")
    log = adapter.discovery_log
    assert len(log) == len(client.session.calls)
    assert all({"ts", "method", "url", "status", "bytes", "waited_s"} <= set(e) for e in log)
    assert any(e.get("location", "").startswith("act-detail.php") for e in log)
    record = adapter.robots_record
    assert (record["status"], record["applied"], record["robots_5xx_source"]) == (500, "allow", "registry lom.robots_5xx")


def test_pillar_filter_still_applies_to_seeds():
    adapter, _client, _ = _adapter()
    cands = adapter.discover(pillars=[6], scope="seed")
    assert "Act 854" not in {c.law_number_guess for c in cands}


def test_robots_5xx_without_the_registry_decision_keeps_only_seeds_outside_lom(capsys):
    adapter, client, _ = _adapter(cfg={**CFG, "lom": {}})
    cands = adapter.discover(pillars=[6, 7], scope="seed")
    assert [u for _m, u in client.session.calls] == [LOM + "/robots.txt"]
    assert "robots.txt" in adapter.lom_error and adapter.robots_record["applied"] == "deny"
    assert "lom.agc.gov.my" not in _hosts(cands) and cands
    assert "LOM UNAVAILABLE" in capsys.readouterr().out


def test_robots_5xx_decision_is_read_from_the_registry_never_the_environment(monkeypatch):
    monkeypatch.setenv("LOM_ROBOTS_5XX", "allow")
    adapter, client, _ = _adapter(cfg={**CFG, "lom": {}})
    adapter.discover(pillars=[6, 7], scope="seed")
    assert len(client.session.calls) == 1 and adapter.lom_error


def test_a_disallowed_listing_is_never_requested():
    adapter, client, _ = _adapter(robots=(200, "User-agent: *\nDisallow: /json-amendment-2024.php\n"))
    cands = adapter.discover(pillars=[6, 7], scope="seed")
    assert not [u for _m, u in client.session.calls if "json-amendment" in u]
    assert "disallows" in adapter.lom_error and "lom.agc.gov.my" not in _hosts(cands)


def test_a_group_naming_this_crawler_is_obeyed_with_the_real_user_agent():
    robots = "User-agent: *\nAllow: /\n\nUser-agent: RDTII-Rocky-Crawler\nDisallow: /\n"
    adapter, client, _ = _adapter(ua=m._DEFAULT_UA, robots=(200, robots))
    adapter.discover(pillars=[6, 7], scope="seed")
    assert [u for _m, u in client.session.calls] == [LOM + "/robots.txt"] and adapter.lom_error


def test_a_redirect_target_is_checked_before_it_is_requested():
    adapter, client, _ = _adapter(robots=(200, "User-agent: *\nDisallow: /act-detail.php\n"))
    cands = adapter.discover(pillars=[6, 7], scope="seed")
    urls = [u for _m, u in client.session.calls]
    assert any("processFile.php" in u for u in urls) and not any("act-detail.php" in u for u in urls)
    assert any("timeline not read (RobotsDisallowed" in n for n in adapter.notes)
    assert cands and adapter.lom_error is None


def test_lom_documents_robots_disallows_are_dropped_with_a_note():
    robots = "User-agent: *\nDisallow: /ilims/upload/portal/akta/outputaktap/1726091_BI/\n"
    adapter, _client, _ = _adapter(robots=(200, robots))
    cands = adapter.discover(pillars=[6, 7], scope="seed")
    assert not [c for c in cands if "1726091_BI" in c.url]
    assert any("disallowed by lom robots.txt" in n for n in adapter.notes)
    assert "Act A1727" in {c.law_number_guess for c in cands}


def test_crawl_delay_slows_discovery_and_is_published_for_the_engine(capsys):
    adapter, _client, sleeps = _adapter(robots=(200, "User-agent: *\nCrawl-delay: 10\n"))
    adapter.discover(pillars=[6, 7], scope="seed")
    assert sleeps and all(s == 10.0 for s in sleeps)
    assert adapter.host_min_delay == {"lom.agc.gov.my": 10.0}
    assert "REQUEST_DELAY_MS=10000" in capsys.readouterr().out


def test_throttling_waits_retry_after_then_rests_and_slows_before_it_stops_lom_and_keeps_other_seeds():
    adapter, client, sleeps = _adapter(fail={"processFile.php": (429, {"Retry-After": "30"})})
    cands = adapter.discover(pillars=[6, 7], scope="seed")
    assert sleeps.count(30.0) == 2                      # the two short waits on Retry-After come first
    # then six rests, each followed by one more try (decision 23), before lom is given up
    assert len([u for _m, u in client.session.calls if "processFile.php" in u]) == 3 + 6
    assert [s for s in sleeps if s >= 60] [:3] == [60.0, 300.0, 1800.0]
    assert client.rests_taken == 6 and client.delay == 60.0     # slowed, and it stays slow
    assert "throttling" in adapter.lom_error and "resting" in adapter.lom_error
    assert cands and "lom.agc.gov.my" not in _hosts(cands)


def test_a_failing_listing_is_retried_twice_then_only_seeds_outside_lom_are_returned():
    adapter, client, _ = _adapter(fail={"json-amendment-2024.php": (500, {})})
    cands = adapter.discover(pillars=[6, 7], scope="seed")
    assert len([u for _m, u in client.session.calls if "json-amendment" in u]) == 3
    assert "HTTP 500" in adapter.lom_error
    assert "GP 3/2025" in {c.law_number_guess for c in cands} and "lom.agc.gov.my" not in _hosts(cands)


def test_a_run_that_selects_nothing_fails_loudly():
    cfg = {**CFG, "lom": {}, "seed_laws": [CFG["seed_laws"][2]]}      # a lom-only seed, lom denied
    adapter, _client, _ = _adapter(cfg=cfg)
    with pytest.raises(RuntimeError, match="no candidates"):
        adapter.discover(pillars=[6, 7], scope="seed")


def test_a_listing_without_a_record_total_is_paged_until_an_empty_page():
    adapter, client, _ = _adapter(cfg=_cfg(listing_page_size=4), omit_total=True)
    adapter.discover(pillars=[6, 7], scope="seed")
    assert len(adapter.principals) == len(UPDATED_RECORDS)
    assert len([u for _m, u in client.session.calls if "json-updated" in u]) == 4     # 4 + 4 + 3, then empty
    assert any("gave no record total" in n for n in adapter.notes)


def test_yes_no_settings_are_parsed_not_compared_as_text(monkeypatch):
    monkeypatch.setenv("LOM_SUBSIDIARY_FROM_TIMELINE", "False")
    adapter, _client, _ = _adapter(cfg=_cfg(subsidiary_series=["P.U. (B)"]))
    cands = adapter.discover(pillars=[6, 7], scope="seed")
    assert not [c for c in cands if c.contract_meta.get("document_kind") == "subsidiary_legislation"]
    assert any("3 distinct subsidiary instrument(s)" in n for n in adapter.notes)
    monkeypatch.setenv("LOM_SUBSIDIARY_FROM_TIMELINE", "maybe")
    adapter, _client, _ = _adapter()
    with pytest.raises(ValueError, match="LOM_SUBSIDIARY_FROM_TIMELINE"):
        adapter.discover(pillars=[6, 7], scope="seed")


def test_without_a_timeline_the_link_falls_back_to_a_labelled_title_match():
    adapter, _client, _ = _adapter(cfg=_cfg(timeline="none"))
    cands = {c.law_number_guess: c for c in adapter.discover(pillars=[6, 7], scope="seed")}
    assert cands["Act A1727"].contract_meta["principal_link_source"] == "title_match"
    assert cands["Act 709"].contract_meta["amendments_after_as_at"] == ["Act A1727"]
    assert "P.U. (B) 522/2024" not in cands          # the order is found only on the amending act's timeline


def test_an_amendment_on_the_timeline_but_not_in_the_listing_is_still_fetched():
    unlisted = [r for r in AMENDMENT_RECORDS if r["ACTNO_LEGISLATION"] != "A1727"]
    adapter, _client, _ = _adapter(cfg={**CFG, "seed_laws": CFG["seed_laws"][:1]}, amendments=unlisted)
    cands = adapter.discover(pillars=[6, 7], scope="seed")
    (extra,) = [c for c in cands if c.url.endswith("Act%20A1727.pdf")]
    meta = extra.contract_meta
    assert (meta["document_kind"], meta["principal_law_number"], meta["number_in_file_name"]) == (
        "amending_act", "Act 709", "Act A1727")
    assert meta["review_flags"] == ["not_in_amendment_listing"]
    pdpa = next(c for c in cands if c.law_number_guess == "Act 709").contract_meta
    assert pdpa["amendments_after_as_at"] == [extra.url] and pdpa["crawl_flags"] == ["stale_vs_portal"]


def test_inventory_covers_both_listings():
    adapter, _client, _ = _adapter()
    adapter.discover(pillars=[6, 7], scope="seed")
    sources = {it.source for it in adapter.inventory}
    assert sources == {"lom_updated", "lom_amendment"}
    assert len(adapter.inventory) == len(UPDATED_RECORDS) + len(AMENDMENT_RECORDS)


def test_scope_all_over_the_review_records():
    adapter, _client, _ = _adapter(updated=UPDATED_RECORDS + REVIEW_UPDATED,
                                   amendments=AMENDMENT_RECORDS + REVIEW_AMENDMENTS)
    cands = adapter.discover(pillars=[6, 7], scope="all")
    by_url = {c.url: c for c in cands}

    # One file, two acts: stored once, under the act the portal's repeal marker names.
    shared = next(c for u, c in by_url.items() if "Act%20714%20(Repealed%20by%20Act%20811)" in u)
    assert (shared.law_number_guess, shared.contract_meta["legal_status"]) == ("Act 714", "repealed")
    assert [x["portal_id"] for x in shared.contract_meta["also_listed_for"]] == ["811"]

    # 26/1947's newest file is Act 26's: it keeps its own undated original instead of vanishing.
    abduction = next(c for c in cands if c.law_number_guess == "Act 26/1947")
    assert abduction.url.endswith("No.%2026%20of%201947%20(Original)(1).pdf")
    assert abduction.contract_meta["version_as_at"] is None and abduction.contract_meta["version_source"] is None
    assert "newest_document_belongs_to_other_act" in abduction.contract_meta["review_flags"]

    # A1585 is listed in four rows, one per pairing of its files; the act keeps all four files.
    a1585 = next(c for c in cands if c.law_number_guess == "Act A1585")
    assert len(a1585.contract_meta["alternative_documents"]) == 3

    for c in cands:
        meta = c.contract_meta
        assert meta.get("text_version") in CONTRACT_TEXT_VERSION, c.url
        assert set(meta["crawl_flags"]) <= CONTRACT_FLAGS, c.url
        assert meta["legal_status"] in CONTRACT_STATUS and meta["status_source"] in CONTRACT_STATUS_SOURCE
        assert meta["legal_status"] == "unknown" or meta["status_source"], c.url
        assert meta.get("document_kind") in CONTRACT_KIND
        assert meta.get("version_source") is None or meta.get("version_as_at"), c.url
        if meta.get("document_kind") in ("amending_act", "commencement_instrument"):
            assert c.indicator_hints is None


def test_ilims_documents_are_requests_pdf_plans():
    adapter, _client, _ = _adapter()
    cand = next(c for c in adapter.discover(pillars=[6, 7], scope="seed") if c.law_number_guess == "Act 709")
    (plan,) = adapter.build_plans(cand)
    assert (plan.method, plan.form_factor, plan.citation_url) == ("requests", "pdf", cand.url)


def test_act_number_only_from_real_act_refs():
    assert m._act_number("Act 709") == "709"
    assert m._act_number("Act A1727") == "A1727"
    assert m._act_number("GP 3/2025") is None
    assert m._act_number("P.U.(A) 2024") is None


def test_subsidiary_series_filter_and_seeded_instruments():
    cfg = {**_cfg(subsidiary_series=["P.U. (B)"]),
           "seed_laws": CFG["seed_laws"] + [
               {"law_name": "An appointment already seeded", "law_number": "P.U.(B) 263/2023",
                "url": "https://example.gov.my/pub263.pdf", "indicators": ["P7-I1"]}]}
    adapter, _client, _ = _adapter(cfg=cfg)
    cands = adapter.discover(pillars=[6, 7], scope="seed")
    subsidiary = sorted(c.law_number_guess for c in cands
                        if c.contract_meta.get("document_kind") == "subsidiary_legislation"
                        and c.contract_meta.get("discovery_path") == "subsidiary_list")
    assert subsidiary == ["P.U. (B) 341/2025", "P.U. (B) 50/2023"]
    # the seeded instrument is on PDPA's timeline: fetched once, from the portal, under the seed's name
    (seeded,) = [c for c in cands if c.law_number_guess == "P.U. (B) 263/2023"]
    assert seeded.law_name_guess == "An appointment already seeded" and seeded.url.startswith(LOM + "/ilims/")
    assert not [c for c in cands if "example.gov.my" in c.url]
    assert all(c.contract_meta["principal_link_source"] == "portal_timeline" for c in cands
               if c.contract_meta.get("document_kind") == "subsidiary_legislation")


def test_the_signed_link_redirect_is_followed_as_a_second_paced_request():
    adapter, client, sleeps = _adapter()
    adapter.discover(pillars=[6, 7], scope="seed")
    hops = [u for _m, u in client.session.calls if "processFile.php" in u or "act-detail.php" in u]
    assert any("processFile.php" in u for u in hops) and any("act-detail.php?a=709" in u for u in hops)
    assert len(sleeps) == len(client.session.calls)       # every request after the first waited, plus the close


# --- resting when a portal refuses the client (decision 23) ------------------------------------------------------

class _Resp:
    def __init__(self, status, headers=None, body=b"ok"):
        self.status_code, self.headers, self.content = status, headers or {}, body


class _Script:
    """A session that answers from a script, one entry per request, then 200 for ever."""
    def __init__(self, *answers):
        self.answers, self.calls = list(answers), []

    def request(self, method, url, **kw):
        self.calls.append(url)
        return self.answers.pop(0) if self.answers else _Resp(200)


def _paced(session, delay=3.0, **attrs):
    sleeps = []
    client = m.LomClient("test-agent", delay_seconds=delay, session=session, sleep=sleeps.append,
                         clock=lambda: 0.0, jitter=False, now_iso=lambda: "2026-09-16T00:00:00Z")
    for k, v in attrs.items():
        setattr(client, k, v)
    return client, sleeps


def test_a_refused_request_is_rested_on_slowed_down_and_sent_again():
    client, sleeps = _paced(_Script(_Resp(403), _Resp(200)))
    resp = client.get("https://sso.agc.gov.sg/Browse/Act/Current/All?PageSize=500")
    assert resp.status_code == 200
    assert 60.0 in sleeps                                   # the first rest is a minute
    assert client.delay == 6.0 and client.rests_taken == 1  # twice as slow, for the rest of the session
    rested = [e for e in client.log if e.get("outcome") == "rested"]
    assert rested and rested[0]["reason"] == "HTTP 403" and rested[0]["rest_s"] == 60.0


def test_rests_lengthen_and_the_client_gives_up_after_six_in_a_row_saying_how_long_it_waited():
    client, sleeps = _paced(_Script(*[_Resp(467)] * 20))
    with pytest.raises(m.LomThrottled) as err:
        client.get("https://sso.agc.gov.sg/Act/PDPA2012")
    assert [s for s in sleeps if s >= 60] == [60.0, 300.0, 1800.0, 1800.0, 1800.0, 1800.0]
    assert "HTTP 467" in str(err.value) and "throttling" in str(err.value)
    assert "resting 126 min" in str(err.value) and client.delay == 60.0      # capped at a minute between requests


def test_an_answer_between_refusals_resets_the_count_but_not_the_slower_pace():
    client, sleeps = _paced(_Script(_Resp(403), _Resp(200), _Resp(403), _Resp(200)))
    client.get("https://example.gov/a")
    client.get("https://example.gov/b")
    assert [s for s in sleeps if s >= 60] == [60.0, 60.0]   # each started again at a minute
    assert client.delay == 12.0                              # but the pace kept slowing


def test_the_waf_challenge_is_a_refusal_and_a_plain_202_is_not():
    client, sleeps = _paced(_Script(_Resp(202, {"x-amzn-waf-action": "challenge"}, b""), _Resp(200)))
    client.get("https://sso.agc.gov.sg/Act/PDPA2012")
    assert client.rests_taken == 1
    client, sleeps = _paced(_Script(_Resp(202, {}, b"")))
    assert client.get("https://sso.agc.gov.sg/Act/PDPA2012").status_code == 202 and client.rests_taken == 0


def test_robots_txt_is_never_rested_on():
    client, sleeps = _paced(_Script(_Resp(403)))
    assert client.get("https://indiacode.nic.in/robots.txt").status_code == 403
    assert client.rests_taken == 0 and not [s for s in sleeps if s >= 60]


def test_a_retry_after_longer_than_the_rest_is_honoured():
    client, sleeps = _paced(_Script(_Resp(503, {"Retry-After": "900"}), _Resp(503, {"Retry-After": "900"}),
                                    _Resp(503, {"Retry-After": "900"}), _Resp(200)))
    client.get("https://example.gov/x")
    assert 900.0 in sleeps and client.rests_taken == 1


def test_max_rests_zero_restores_the_old_rule_and_the_environment_configures_the_rest(monkeypatch):
    client, _ = _paced(_Script(_Resp(403)), max_rests=0)
    assert client.get("https://example.gov/x").status_code == 403 and client.rests_taken == 0
    monkeypatch.setenv("PACED_RESTS", "30,90")
    monkeypatch.setenv("PACED_MAX_RESTS", "2")
    client, sleeps = _paced(_Script(*[_Resp(403)] * 5))
    with pytest.raises(m.LomThrottled):
        client.get("https://example.gov/x")
    assert [s for s in sleeps if s >= 30] == [30.0, 90.0]
