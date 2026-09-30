"""Malaysia (Laws of Malaysia) adapter: offline tests for the title rule, the timeline and subsidiary-legislation
policies, Finance Acts listed as principal acts, registry destinations, the link-file catalogue and the links_file
frontier. Written 2026-09-14 against pages saved from lom.agc.gov.my on 2026-09-13 and 2026-09-14.

No test sends a request: the portal is replaced by FakeSession, copied from test_my_lom.py.
"""
from __future__ import annotations

import base64
import csv
import json
import os
import re
from dataclasses import fields
from pathlib import Path
from urllib.parse import unquote, urlparse

import pytest
import yaml

from p1_scrape.adapters import my_gazette as m
from p1_scrape.models import Candidate

_HERE = Path(__file__).parent
FIX = _HERE / "fixtures" / "my" if (_HERE / "fixtures" / "my").is_dir() else _HERE / "fixtures"
LOM = "https://lom.agc.gov.my"
TODAY = "2026-09-14"


def _read(name: str) -> str:
    return (FIX / name).read_text(encoding="utf-8")


def _records(name: str) -> list[dict]:
    return json.loads(_read(name))["records"]


UPDATED_PAGE = "lom_principal_updated_2026-09-13.html"
UPDATED_RECORDS = _records("lom_updated_records_2026-09-13.json")
AMENDMENT_RECORDS = _records("lom_amendment_records_2026-09-13.json")
REVIEW_UPDATED = _records("lom_updated_records_review_2026-09-13.json")
REVIEW_AMENDMENTS = _records("lom_amendment_records_review_2026-09-13.json")
# Acts 874, 862, 742 and 719 (Finance Acts 2025, 2024, 2012, 2011) and Act 53 (Income Tax Act 1967).
FINANCE_RECORDS = _records("lom_updated_records_finance_2026-09-14.json")
DETAIL_709 = _read("lom_act_detail_709_BI_2026-09-13.html")
DETAIL_A1727 = _read("lom_amendment_detail_A1727_BI_2026-09-13.html")
DETAIL_53 = _read("lom_act_detail_53_BI_2026-09-14.html")
DETAIL_874 = _read("lom_act_detail_874_BI_2026-09-14.html")
KEY = m.extract_response_key(_read(UPDATED_PAGE))


def _registry() -> dict:
    """The real registry: ../sources.yaml in the workshop, the assembled sources_my.yaml in the stage."""
    for path in (_HERE.parent / "sources.yaml", _HERE.parent / "contracts" / "instrument" / "sources_my.yaml",
                 _HERE.parent / "instrument" / "sources_my.yaml"):
        if path.is_file():
            return yaml.safe_load(path.read_text(encoding="utf-8"))
    raise FileNotFoundError("no Malaysian registry next to the tests")


REGISTRY = _registry()
RULE = m.TitleRule.from_cfg(REGISTRY["title_rule"])

SEED_709 = {"law_name": "Personal Data Protection Act 2010", "law_number": "Act 709",
            "url": "https://www.pdp.gov.my/ppdpv1/en/akta/", "indicators": ["P6-I1", "P7-I1"],
            "provenance": "round1_registry"}
SEED_A1727 = {"law_name": "Personal Data Protection (Amendment) Act 2024", "law_number": "Act A1727",
              "url": "https://www.pdp.gov.my/x/", "indicators": ["P6-I1", "P7-I3"]}
SEED_854 = {"law_name": "Cyber Security Act 2024", "law_number": "Act 854", "url": "https://lom.agc.gov.my",
            "indicators": ["P7-I2"]}
SEED_53 = {"law_name": "Income Tax Act 1967", "law_number": "Act 53", "url": "https://lom.agc.gov.my",
           "indicators": ["P7-I3"]}
SEED_874 = {"law_name": "Finance Act 2025", "law_number": "Act 874", "url": "https://lom.agc.gov.my",
            "indicators": ["P7-I3"], "provenance": "test"}
SEED_26 = {"law_name": "Legal Aid Act 1971", "law_number": "Act 26", "url": "https://lom.agc.gov.my",
           "indicators": ["P7-I3"]}                     # a seed the title rule does not select
SEED_GP3 = {"law_name": "Personal Data Protection Guideline on Cross-Border Personal Data Transfer (GP 3/2025)",
            "law_number": "GP 3/2025",
            "url": "https://www.pdp.gov.my/ppdpv1/wp-content/uploads/2025/08/GP_CBPDT_EN-1.pdf",
            "indicators": ["P6-I4"], "provenance": "p3_request:DELTA_CRAWL_REQUEST_2026-07-14#6"}


@pytest.fixture(autouse=True)
def _no_lom_environment(monkeypatch):
    """Settings come from the cfg under test only: LOM_* variables would override them."""
    for name in list(os.environ):
        if name.startswith("LOM_"):
            monkeypatch.delenv(name)


def _principal(act_no: str, records=None) -> m.PrincipalAct:
    pool = records if records is not None else UPDATED_RECORDS + REVIEW_UPDATED + FINANCE_RECORDS
    return m.parse_principal(next(r for r in pool if r["lgt_act_no"].strip() == act_no))


def _amendment(a: str) -> m.AmendingAct:
    return m.parse_amendment(next(r for r in AMENDMENT_RECORDS + REVIEW_AMENDMENTS if r["ACTNO_LEGISLATION"] == a))


def _unique(records: list[dict]) -> list[dict]:
    seen, out = set(), []
    for r in records:
        if r["lgt_act_no"].strip() not in seen:
            seen.add(r["lgt_act_no"].strip())
            out.append(r)
    return out


def _encrypt(obj: dict, key_hex: str = KEY) -> dict:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    iv = os.urandom(12)
    sealed = AESGCM(bytes.fromhex(key_hex)).encrypt(iv, json.dumps(obj).encode(), None)
    ct, tag = sealed[:-16], sealed[-16:]
    return {"encrypted": True, "data": base64.b64encode(iv + tag + ct).decode()}


# --- a fake portal, as in test_my_lom.py, with configurable listing paths -----------------

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
                 pages=("principal.php?type=",),
                 endpoints=("json-updated-2024.php", "json-amendment-2024.php")):
        self.calls: list[tuple[str, str]] = []
        self.headers: list[dict] = []
        self.robots = robots
        self.updated = UPDATED_RECORDS if updated is None else updated
        self.amendments = AMENDMENT_RECORDS if amendments is None else amendments
        self.detail = {"709": DETAIL_709, "A1727": DETAIL_A1727} if detail is None else detail
        self.pages, self.endpoints = pages, endpoints

    def request(self, method, url, data=None, headers=None, timeout=None, allow_redirects=True):
        self.calls.append((method, url))
        self.headers.append(dict(headers or {}))
        if url.endswith("/robots.txt"):
            return FakeResp(*self.robots)
        if method == "GET" and any(p in url for p in self.pages):
            return FakeResp(200, _read(UPDATED_PAGE))
        for endpoint, records in zip(self.endpoints, (self.updated, self.amendments)):
            if method == "POST" and url.endswith(endpoint):
                start, length = int(data["start"]), int(data["length"])
                body = {"draw": data["draw"], "records": records[start:start + length],
                        "recordsTotal": len(records)}
                return FakeResp(200, _encrypt(body))
        if method == "GET" and "processFile.php" in url:      # the portal answers a signed link with a 302
            target = m.decode_token_target(url) or ""
            act = next((k for k in self.detail if f"act={k}&" in target), "x")
            return FakeResp(302, "", {"Location": "act-detail.php?a=" + act})
        if method == "GET" and "act-detail.php?a=" in url:
            return FakeResp(200, self.detail.get(url.rsplit("a=", 1)[-1], "Invalid request"))
        return FakeResp(404, "not found")


def _adapter(cfg: dict, ua: str = "test-agent", **session_kw):
    sleeps: list[float] = []
    now = [0.0]

    def sleep(s: float) -> None:
        sleeps.append(s)
        now[0] += s

    client = m.LomClient(ua, delay_seconds=3.0, session=FakeSession(**session_kw),
                         sleep=sleep, clock=lambda: now[0], jitter=False, now_iso=lambda: "2026-09-14T00:00:00Z")
    return m.MyGazetteAdapter(cfg, client=client, today=TODAY), client


def _cfg(seeds=(SEED_709,), title_rule=True, **lom) -> dict:
    cfg = {"economy": "MY", "lom": {"robots_5xx": "allow", **lom}, "seed_laws": list(seeds)}
    if title_rule:
        cfg["title_rule"] = REGISTRY["title_rule"]
    return cfg


def _timeline_targets(client) -> list[str]:
    """The act parameter of every signed detail-page link requested, in order."""
    out = []
    for _method, url in client.session.calls:
        if "processFile.php" in url:
            target = m.decode_token_target(url) or ""
            found = re.search(r"[?&]act=([^&#]+)", target)
            out.append(unquote(found.group(1)) if found else target)
    return out


def _by_number(cands) -> dict[str, Candidate]:
    return {c.law_number_guess: c for c in cands}


def _kind(cands, kind: str) -> list[Candidate]:
    return [c for c in cands if c.contract_meta.get("document_kind") == kind]


def _host(url: str) -> str:
    return (urlparse(url).hostname or "").lower()


# --- 1. the title rule, from the real registry block ---------------------------------------

def test_title_rule_is_built_from_the_registry_block():
    block = REGISTRY["title_rule"]
    assert RULE.rule_id == block["id"]
    assert [g.id for g in RULE.groups] == [g["id"] for g in block["groups"]]
    assert [x for x, _rx in RULE.exclusions] == [x["id"] for x in block["exclusions"]]
    assert m.TitleRule.from_cfg(None) is None and m.TitleRule.from_cfg({}) is None
    with pytest.raises(ValueError, match="no groups"):
        m.TitleRule.from_cfg({"id": "empty", "groups": []})


@pytest.mark.parametrize("title, groups, exclusion, tier", [
    (_principal("709").title_bi, ["G1_data_protection_privacy"], None, "core"),
    (_principal("854").title_bi, ["G2_cybersecurity_computer_misuse"], None, "core"),
    (_principal("53").title_bi, ["S2_tax_records"], None, "sectoral"),
    (_principal("874").title_bi, [], "X1_annual_finance_act", None),
    (_amendment("A1727").title_bi, [], "X2_amending_repeal_validation_dissolution", None),
    (_principal("811").title_bi, [], "X2_amending_repeal_validation_dissolution", None),
    (_principal("26").title_bi, [], None, None),
])
def test_title_rule_matches_real_listing_titles(title, groups, exclusion, tier):
    assert RULE.match(title) == (groups, exclusion)
    assert RULE.tier(groups) == tier


def test_the_listing_titles_behind_the_rule_examples():
    assert _principal("709").title_bi == "PERSONAL DATA PROTECTION ACT 2010"
    assert _principal("53").title_bi == "INCOME TAX ACT 1967"
    assert _principal("874").title_bi == "FINANCE ACT 2025"
    assert _amendment("A1727").title_bi == "PERSONAL DATA PROTECTION (AMENDMENT) ACT 2024"
    # an exclusion wins over a group the title also hits (DATA)
    assert RULE.match("PERSONAL DATA PROTECTION (AMENDMENT) ACT 2024")[0] == []


def test_title_rule_tier_prefers_core_and_the_malay_title_is_used_only_without_an_english_one():
    assert RULE.tier(["S2_tax_records", "G1_data_protection_privacy"]) == "core"
    assert RULE.tier([]) is None and RULE.tier(["no_such_group"]) is None
    pdpa = _principal("709")
    assert RULE.match(None, pdpa.title_bm) == (["G1_data_protection_privacy"], None)   # AKTA ... DATA ...
    assert RULE.match(_principal("26").title_bi, pdpa.title_bm) == ([], None)          # English first
    assert RULE.match(None, None) == ([], None)


def test_title_rule_normalises_case_whitespace_and_curly_apostrophes():
    curly = _amendment("A1788").title_bi                 # the amendment listing writes EMPLOYEES’
    assert "’" in curly
    assert m.TitleRule.normalise(curly) == "EMPLOYEES' SOCIAL SECURITY (AMENDMENT) ACT 2026"
    assert m.TitleRule.normalise("  personal   data\tprotection ") == "PERSONAL DATA PROTECTION"
    assert m.TitleRule.normalise(None) == ""
    act4 = _principal("4").title_bi                      # the updated listing writes EMPLOYEES'
    assert act4 == "EMPLOYEES' SOCIAL SECURITY ACT 1969"
    assert RULE.match(act4.replace("'", "’")) == RULE.match(act4) == (["S5_employment_records"], None)
    strict = m.TitleRule.from_cfg({"id": "t", "groups": [
        {"id": "EMP", "tier": "sectoral", "patterns": [r"^EMPLOYEES' SOCIAL SECURITY ACT\b"]}]})
    assert strict.match(act4.replace("'", "‘").lower()) == (["EMP"], None)


# --- 2. lom.timeline: rule ------------------------------------------------------------------

LIVE_RULE_ACTS = {"709", "854", "747", "593", "563", "53", "4"}


def test_rule_acts_in_the_fixture_records_are_what_the_timeline_test_expects():
    parsed = [m.parse_principal(r) for r in UPDATED_RECORDS + REVIEW_UPDATED]
    matched = {p.act_no for p in parsed if RULE.match(p.title_bi, p.title_bm)[0]}
    live = {p.act_no for p in parsed if p.act_no in matched and p.status_kind not in ("repealed", "superseded")}
    assert live == LIVE_RULE_ACTS
    assert matched - live == {"762"}                     # GOODS AND SERVICES TAX ACT 2014, repealed by Act 805
    assert _principal("762").status_kind == "repealed"


def test_timeline_rule_with_scope_seed_reads_only_the_seeds_timelines():
    adapter, client = _adapter(_cfg(seeds=(SEED_709, SEED_26), timeline="rule"),
                               updated=UPDATED_RECORDS + REVIEW_UPDATED, amendments=AMENDMENT_RECORDS + REVIEW_AMENDMENTS)
    adapter.discover(pillars=[6, 7], scope="seed")
    targets = _timeline_targets(client)
    assert [t for t in targets if not t.startswith("A")] == ["709", "26"]     # Act 26 is a seed, not a rule act
    assert targets == ["709", "26", "A1727"]             # and PDPA's later amendment, for its commencement order
    assert set(adapter.timelines) == {"709", "26"}


def test_timeline_rule_with_scope_all_reads_seeds_and_live_rule_acts_only():
    adapter, client = _adapter(_cfg(seeds=(SEED_709, SEED_26), timeline="rule"),
                               updated=UPDATED_RECORDS + REVIEW_UPDATED, amendments=AMENDMENT_RECORDS + REVIEW_AMENDMENTS)
    cands = adapter.discover(pillars=[6, 7], scope="all")
    principal_targets = [t for t in _timeline_targets(client) if not re.match(r"^A\d", t)]
    assert sorted(principal_targets) == sorted(LIVE_RULE_ACTS | {"26"})   # each once
    assert "762" not in principal_targets                               # a rule act, but repealed
    assert not {"884", "406 (Revised)", "811", "384", "714"} & set(principal_targets)  # unmatched, excluded, superseded
    assert set(adapter.timelines) == LIVE_RULE_ACTS | {"26"}
    # every amending act whose timeline was read belongs to an act whose timeline was read
    for a in [t for t in _timeline_targets(client) if re.match(r"^A\d", t)]:
        assert adapter._principal_for(adapter.amendments[a]).act_no in LIVE_RULE_ACTS
    assert any("their timelines were not read (lom.timeline=rule)" in n for n in adapter.notes)
    assert {c.law_number_guess for c in cands} >= {"Act 762", "Act 884"}  # still crawled, without a timeline


def test_timeline_seed_with_a_title_rule_still_reads_only_seed_timelines():
    adapter, client = _adapter(_cfg(timeline="seed"), updated=UPDATED_RECORDS + REVIEW_UPDATED)
    adapter.discover(pillars=[6, 7], scope="all")
    assert [t for t in _timeline_targets(client) if not t.startswith("A")] == ["709"]


def test_timeline_rule_without_a_title_rule_is_a_configuration_error_before_any_request():
    adapter, client = _adapter(_cfg(title_rule=False, timeline="rule"))
    with pytest.raises(ValueError, match="no title_rule"):
        adapter.discover(pillars=[6, 7], scope="seed")
    assert client.session.calls == []
    adapter, client = _adapter(_cfg(timeline="everything"))
    with pytest.raises(ValueError, match="lom.timeline"):
        adapter.discover(pillars=[6, 7], scope="seed")
    assert client.session.calls == []


# --- 3. lom.subsidiary_acts -------------------------------------------------------------------

def _timeline_page(entries: list[dict]) -> str:
    """A detail page holding only a timeline, in the markup of the saved Act 709 page
    (lom_act_detail_709_BI_2026-09-13.html): nav anchors, then one events-content item per anchor."""
    nav, items = [], []
    for i, e in enumerate(entries):
        selected = ' class="selected" ' if i == 0 else " "
        nav.append(f'<li>\n<a href="#0" data-date="{e["date"]}" data-project-id="{e["pid"]}" '
                   f'data-log-type="{e["log_type"]}" class="{"selected " if i == 0 else " "}event_a">\n'
                   f'{e["display"]}<br>{e["log_type"].title()}</a>\n</li>\n')
        lines = "".join(f"{k}: {v}<br>" for k, v in e["fields"].items())
        items.append(f'<li {selected}data-date="{e["date"]}">\n<p style="text-align:center">\n{e["display"]}\n<br>\n'
                     f'{lines}<br></p>\n<div style ="text-align:right">Total Act Views</div>\n'
                     f'<div class="col_full"><iframe data-src="pdfjs/web/viewer.html?file=../../..{e["path"]}'
                     f'&embedded=true" style="width:100%; height:800px;" frameborder="0" allowfullscreen '
                     f'class="lazy"></iframe></div>\n</li>\n')
    return ('<div class="tab-content clearfix" id="timeline"><section class="cd-horizontal-timeline">\n'
            '<div class="timeline"><div class="events-wrapper"><div class="events"><ol>\n' + "".join(nav)
            + '</ol></div></div></div>\n<div class="events-content">\n<ol>\n' + "".join(items)
            + '</ol>\n</div> <!-- tutup class events-content -->\n</section></div>')


def _core_timeline_854() -> tuple[str, dict]:
    """Act 854 (Cyber Security Act 2024, a core act) with 27 distinct P.U. (A) instruments, two of them listed
    twice under a differently written number and another file, and one P.U. (B) notice."""
    doc = m.choose_principal_document(_principal("854"), ["eng", "msa"])
    entries = [{"date": "26/06/2024", "pid": "900001", "log_type": "ORIGINAL", "display": "26 Jun 2024",
                "fields": {"Publication Date": "26/06/2024", "Royal Assent Date": "18/06/2024"},
                "path": unquote(urlparse(doc.url).path)}]
    for n in range(1, 28):
        entries.append({"date": f"{n:02d}/03/2025", "pid": str(910000 + n), "log_type": "SUBSIDIARY_LEGISLATION",
                        "display": f"{n:02d} Feb 2025",
                        "fields": {"Publication Date": f"{n:02d}/02/2025", "Commencement Remark": "-",
                                   "P.U. No.": f"P.U. (A) {n}/2025"},
                        "path": f"/ilims/upload/portal/akta/outputp/{910000 + n}/PUA {n}_2025.pdf"})
    for n, written in ((3, "P.U.(A) 3/2025"), (7, "P.U. (A)  7/2025")):
        entries.append({"date": "28/03/2025", "pid": str(920000 + n), "log_type": "SUBSIDIARY_LEGISLATION",
                        "display": "28 Feb 2025",
                        "fields": {"Publication Date": "28/02/2025", "Commencement Remark": "-", "P.U. No.": written},
                        "path": f"/ilims/upload/portal/akta/outputp/{920000 + n}/PUA {n}_2025 copy.pdf"})
    entries.append({"date": "29/03/2025", "pid": "930001", "log_type": "SUBSIDIARY_LEGISLATION",
                    "display": "28 Mar 2025",
                    "fields": {"Publication Date": "28/03/2025", "Commencement Remark": "-", "P.U. No.": "P.U. (B) 99/2025"},
                    "path": "/ilims/upload/portal/akta/outputp/930001/PUB 99_2025.pdf"})
    return _timeline_page(entries), {"doc": doc, "entries": entries}


def _distinct_subsidiary(html: str, prefix: str = "") -> set[str]:
    return {m._pu_key(e.pu_no) for e in m.parse_timeline(html)
            if e.log_type == "SUBSIDIARY_LEGISLATION" and e.file_url and e.pu_no and m._pu_key(e.pu_no).startswith(prefix)}


def test_the_synthetic_core_timeline_parses_like_a_real_one():
    html, info = _core_timeline_854()
    entries = m.parse_timeline(html)
    assert len(entries) == 31 and entries[0].log_type == "ORIGINAL"
    assert entries[0].file_url == info["doc"].url
    assert (entries[3].pu_no, entries[3].publication_date) == ("P.U. (A) 3/2025", "03/02/2025")
    assert entries[3].file_url == LOM + "/ilims/upload/portal/akta/outputp/910003/PUA%203_2025.pdf"
    assert len(_distinct_subsidiary(html)) == 28 and len(_distinct_subsidiary(html, "PU(A)")) == 27


def test_subsidiary_core_fetches_a_core_acts_pu_a_instruments_once_each_without_a_cap_and_skips_sectoral_acts():
    html, _info = _core_timeline_854()
    cfg = _cfg(seeds=(SEED_854, SEED_53), timeline="seed", subsidiary_acts="core", subsidiary_max_per_act=0)
    adapter, _client = _adapter(cfg, detail={"854": html, "53": DETAIL_53})
    cands = adapter.discover(pillars=[6, 7], scope="seed")
    subsidiary = _kind(cands, "subsidiary_legislation")
    assert len(subsidiary) == 27                                            # no cap at 0, and deduped
    assert sorted(c.law_number_guess for c in subsidiary) == sorted(f"P.U. (A) {n}/2025" for n in range(1, 28))
    assert {c.contract_meta["principal_law_number"] for c in subsidiary} == {"Act 854"}
    by_pu = {c.law_number_guess: c for c in subsidiary}
    assert by_pu["P.U. (A) 3/2025"].url.endswith("/910003/PUA%203_2025.pdf")   # the first listing is kept
    assert not [c for c in cands if "copy.pdf" in c.url or "PUB%2099_2025" in c.url]
    assert not any("fetching the newest" in n for n in adapter.notes)
    assert all(c.indicator_hints is None and c.contract_meta["principal_link_source"] == "portal_timeline"
               for c in subsidiary)
    # Act 53 (Income Tax, sectoral) had its timeline read but none of its instruments fetched
    skipped = len(_distinct_subsidiary(DETAIL_53))
    assert skipped == 172
    assert (f"{skipped} distinct subsidiary instrument(s) listed on 1 read timeline(s) not fetched under "
            f"lom.subsidiary_acts=core (decision 12): Act 53 {skipped}") in adapter.notes


def test_subsidiary_cap_when_set_keeps_the_newest_and_says_so():
    html, _info = _core_timeline_854()
    cfg = _cfg(seeds=(SEED_854,), timeline="seed", subsidiary_acts="core", subsidiary_max_per_act=5)
    adapter, _client = _adapter(cfg, detail={"854": html})
    subsidiary = _kind(adapter.discover(pillars=[6, 7], scope="seed"), "subsidiary_legislation")
    assert sorted(c.law_number_guess for c in subsidiary) == sorted(f"P.U. (A) {n}/2025" for n in range(23, 28))
    assert "Act 854: 27 subsidiary instruments on the timeline, fetching the newest 5" in adapter.notes


def test_subsidiary_rule_over_act_53s_real_timeline_dedupes_repeated_pu_numbers_with_no_cap():
    cfg = _cfg(seeds=(SEED_53,), timeline="seed", subsidiary_acts="rule", subsidiary_max_per_act=0)
    adapter, _client = _adapter(cfg, detail={"53": DETAIL_53})
    subsidiary = _kind(adapter.discover(pillars=[6, 7], scope="seed"), "subsidiary_legislation")
    listed = [e for e in m.parse_timeline(DETAIL_53)
              if e.log_type == "SUBSIDIARY_LEGISLATION" and e.file_url and e.pu_no and m._pu_key(e.pu_no).startswith("PU(A)")]
    distinct = {m._pu_key(e.pu_no) for e in listed}
    assert (len(listed), len(distinct)) == (208, 168)                     # the portal repeats 40 entries
    numbers = [m._pu_key(c.law_number_guess) for c in subsidiary]
    assert len(subsidiary) == 168 and set(numbers) == distinct             # one candidate per number, none capped
    assert {c.contract_meta["principal_law_number"] for c in subsidiary} == {"Act 53"}
    assert not any("fetching the newest" in n for n in adapter.notes)


@pytest.mark.parametrize("lom, policy", [
    ({"subsidiary_from_timeline": True}, "seed"),
    ({"subsidiary_from_timeline": "yes"}, "seed"),
    ({"subsidiary_from_timeline": False}, "none"),
    ({}, "none"),
    ({"subsidiary_acts": "core", "subsidiary_from_timeline": True}, "core"),
    ({"subsidiary_acts": "RULE"}, "rule"),
])
def test_subsidiary_policy_reads_the_new_key_and_the_legacy_yes_no_key(lom, policy):
    adapter, _client = _adapter(_cfg(**lom))
    assert adapter._subsidiary_policy() == policy


def test_legacy_subsidiary_from_timeline_fetches_the_seed_acts_instruments():
    html, _info = _core_timeline_854()
    cfg = _cfg(seeds=(SEED_854,), title_rule=False, subsidiary_from_timeline=True, subsidiary_max_per_act=0)
    adapter, _client = _adapter(cfg, detail={"854": html})
    assert len(_kind(adapter.discover(pillars=[6, 7], scope="seed"), "subsidiary_legislation")) == 27


@pytest.mark.parametrize("lom, title_rule, message", [
    ({"subsidiary_acts": "everything"}, True, "is not none, seed, core or rule"),
    ({"subsidiary_acts": "core"}, False, "no title_rule"),
    ({"subsidiary_acts": "rule"}, False, "no title_rule"),
])
def test_an_invalid_subsidiary_policy_raises_before_any_request(lom, title_rule, message):
    adapter, client = _adapter(_cfg(title_rule=title_rule, **lom))
    with pytest.raises(ValueError, match=message):
        adapter.discover(pillars=[6, 7], scope="seed")
    assert client.session.calls == []


# --- 4. Finance Acts on Act 53's timeline ----------------------------------------------------

def test_act_53s_timeline_lists_finance_acts_by_the_project_id_of_their_current_document():
    entries = m.parse_timeline(DETAIL_53)
    amendments = {e.project_id: e for e in entries if e.log_type == "AMENDMENTS"}
    (original_874,) = m.parse_timeline(DETAIL_874)
    doc_874 = m.choose_principal_document(_principal("874", FINANCE_RECORDS), ["eng", "msa"])
    assert original_874.log_type == "ORIGINAL" and original_874.file_url == doc_874.url
    assert f"/{original_874.project_id}_BI/" in doc_874.url
    assert amendments[original_874.project_id].file_url == doc_874.url
    for act in ("862", "719"):
        doc = m.choose_principal_document(_principal(act, FINANCE_RECORDS), ["eng", "msa"])
        pid = re.search(r"/(\d+)_B[IM]/", doc.url).group(1)
        assert amendments[pid].file_url == doc.url
    # Finance Act 2012 is listed under the 2012 file and project id; the listing offers a 2025 online reprint
    (entry_742,) = [e for e in amendments.values() if e.file_url and e.file_url.endswith("/LOM/EN/ACT%20742.pdf")]
    doc_742 = m.choose_principal_document(_principal("742", FINANCE_RECORDS), ["eng", "msa"])
    assert entry_742.project_id == "742"
    assert doc_742.url.endswith("/3439788_BI/ACT%20742%20AS%20AT%202025.pdf") and doc_742.edition == "online"
    assert "3439788" not in amendments


def test_either_the_project_id_or_the_same_file_links_a_finance_act_to_act_53():
    """On the saved pages the two agree for every act matched (16 on Act 53's timeline), so each is tested alone
    by altering one AMENDMENTS entry of the real timeline."""
    from dataclasses import replace
    ad = _offline_adapter(FINANCE_RECORDS)
    doc = {a: m.choose_principal_document(ad.principals[a], ["eng", "msa"]).url for a in ("874", "862", "719")}

    def altered(e: m.TimelineEntry) -> m.TimelineEntry:
        if e.log_type != "AMENDMENTS" or not e.file_url:
            return e
        if e.file_url == doc["874"]:                       # the project id alone
            return replace(e, file_url=LOM + "/ilims/upload/portal/akta/LOM/EN/Act%20874%20elsewhere.pdf")
        if e.file_url == doc["862"]:                       # the same file alone
            return replace(e, project_id="99862")
        if e.file_url == doc["719"]:                       # neither
            return replace(e, project_id="99719", file_url=LOM + "/ilims/upload/portal/akta/LOM/EN/Act%20719%20old.pdf")
        return e

    ad.timelines["53"] = [altered(e) for e in m.parse_timeline(DETAIL_53)]
    listed = ad._listed_as_amendment()
    assert [a for a, _e in listed["874"]] == ["53"] and [a for a, _e in listed["862"]] == ["53"]
    assert "719" not in listed and "742" not in listed and "53" not in listed
    kinds = {a: ad._principal_candidate(ad.principals[a], law=None, indicators=[]).contract_meta["document_kind"]
             for a in ("874", "862", "719", "742", "53")}
    assert kinds == {"874": "amending_act", "862": "amending_act", "719": "principal_act", "742": "principal_act",
                     "53": "principal_act"}


def _finance_run(timeline: str, seeds, scope: str, detail=None):
    adapter, client = _adapter(_cfg(seeds=seeds, timeline=timeline), updated=FINANCE_RECORDS,
                               detail=detail or {"53": DETAIL_53, "874": DETAIL_874})
    return adapter, client, _by_number(adapter.discover(pillars=[6, 7], scope=scope))


@pytest.mark.parametrize("timeline, seeds", [("seed", (SEED_53,)), ("rule", ())])
def test_finance_acts_listed_under_act_53s_amendments_are_amending_acts(timeline, seeds):
    adapter, client, cands = _finance_run(timeline, seeds, "all")
    assert [t for t in _timeline_targets(client) if not t.startswith("A")] == ["53"]
    for act in ("Act 874", "Act 862", "Act 719"):
        c = cands[act]
        meta = c.contract_meta
        assert (meta["document_kind"], meta["principal_law_number"], meta["amends"]) == (
            "amending_act", "Act 53", ["Act 53"]), act
        assert (meta["principal_link_source"], meta["text_version"]) == ("portal_timeline", "as_enacted"), act
        assert "listed_as_principal_by_portal" in meta["review_flags"], act
        assert c.indicator_hints is None and c.pillar_hint is None, act
        assert meta["title_rule_exclusion"] == "X1_annual_finance_act"
    reprinted = cands["Act 742"].contract_meta
    assert (reprinted["document_kind"], reprinted["principal_law_number"], reprinted["amends"]) == (
        "principal_act", None, [])
    assert "listed_as_principal_by_portal" not in reprinted["review_flags"]
    assert reprinted["text_version"] == "reprint"                          # an online reprint, no timeline read
    assert cands["Act 53"].contract_meta["document_kind"] == "principal_act"


def test_a_seeded_finance_act_keeps_no_indicator_hints_and_its_own_timeline_dates():
    adapter, client, cands = _finance_run("seed", (SEED_53, SEED_874), "seed")
    assert sorted(t for t in _timeline_targets(client) if not t.startswith("A")) == ["53", "874"]
    finance = cands["Act 874"]
    meta = finance.contract_meta
    assert (meta["document_kind"], meta["amends"], meta["discovery_path"], meta["seed_provenance"]) == (
        "amending_act", ["Act 53"], "seed", "test")
    assert finance.indicator_hints is None and finance.pillar_hint is None
    assert (meta["timeline_log_type"], meta["text_version"]) == ("ORIGINAL", "as_enacted")
    assert (finance.publication_date, finance.assent_date) == ("31/12/2025", "27/12/2025")
    assert cands["Act 53"].indicator_hints == "P7-I3"


def test_without_act_53s_timeline_a_finance_act_stays_a_principal_act():
    _adapter_, _client, cands = _finance_run("none", (SEED_53,), "all")
    meta = cands["Act 874"].contract_meta
    assert (meta["document_kind"], meta["amends"]) == ("principal_act", [])
    assert "listed_as_principal_by_portal" not in meta["review_flags"]


# --- 5. review flag english_online_malay_printed ---------------------------------------------

def _offline_adapter(records, languages=None) -> m.MyGazetteAdapter:
    lom = {"document_languages": languages} if languages else {}
    ad = m.MyGazetteAdapter({"economy": "MY", "lom": lom}, today=TODAY)
    for rec in records:
        p = m.parse_principal(rec)
        ad.principals.setdefault(m._act_key(p.act_no), p)
    return ad


def test_english_online_reprint_beside_a_malay_printed_one_is_flagged():
    ad = _offline_adapter(UPDATED_RECORDS)
    cpc = ad._principal_candidate(ad.principals["593"], law=None, indicators=[])     # Criminal Procedure Code
    meta = cpc.contract_meta
    assert (meta["language"], meta["edition"], meta["version_as_at"]) == ("eng", "online", "2023-07-04")
    assert "english_online_malay_printed" in meta["review_flags"]
    assert any(u.endswith("AKTA%20593%20MUKTAMAD.pdf") for u in meta["alternative_documents"])
    pdpa = ad._principal_candidate(ad.principals["709"], law=None, indicators=[]).contract_meta
    assert pdpa["edition"] == "printed" and "english_online_malay_printed" not in pdpa["review_flags"]
    legal_aid = ad._principal_candidate(ad.principals["26"], law=None, indicators=[]).contract_meta
    assert (legal_aid["language"], legal_aid["edition"]) == ("eng", "online")   # its Malay text is online too
    assert "english_online_malay_printed" not in legal_aid["review_flags"]


def test_malay_first_takes_the_printed_malay_text_and_raises_no_flag():
    ad = _offline_adapter(UPDATED_RECORDS, languages=["msa", "eng"])
    meta = ad._principal_candidate(ad.principals["593"], law=None, indicators=[]).contract_meta
    assert (meta["language"], meta["edition"]) == ("msa", "printed")
    assert "english_online_malay_printed" not in meta["review_flags"]


# --- 6. destinations from the registry -------------------------------------------------------

MIRROR = "https://mirror.lom.test"
MIRROR_LISTINGS = {"updated": {"page": "legislation.php?list=principal", "endpoint": "api/principal-2026.php"},
                   "amendment": {"page": "legislation.php?list=amending", "endpoint": "api/amending-2026.php"}}


def _mirror_adapter(robots=(500, "error")):
    cfg = _cfg(root=MIRROR + "/", listings=MIRROR_LISTINGS)
    return _adapter(cfg, robots=robots, pages=("legislation.php?list=",),
                    endpoints=("api/principal-2026.php", "api/amending-2026.php"))


def test_a_custom_lom_root_and_listings_change_every_discovery_request():
    adapter, client = _mirror_adapter()
    cands = adapter.discover(pillars=[6, 7], scope="seed")
    urls = [u for _m, u in client.session.calls]
    assert adapter.root == MIRROR and adapter.host == "mirror.lom.test"
    assert urls[0] == MIRROR + "/robots.txt"
    assert all(u.startswith(MIRROR + "/") for u in urls)
    assert client.session.calls[1:5] == [
        ("GET", MIRROR + "/legislation.php?list=principal"), ("POST", MIRROR + "/api/principal-2026.php"),
        ("GET", MIRROR + "/legislation.php?list=amending"), ("POST", MIRROR + "/api/amending-2026.php")]
    post = client.session.calls.index(("POST", MIRROR + "/api/principal-2026.php"))
    assert client.session.headers[post]["Referer"] == MIRROR + "/legislation.php?list=principal"
    assert any(u.startswith(MIRROR + "/processFile.php") for u in urls)
    assert any(u == MIRROR + "/act-detail.php?a=709" for u in urls)
    assert adapter.robots_record["url"] == MIRROR + "/robots.txt"
    assert set(adapter.last_request_at) == {"mirror.lom.test"}
    assert "Act 709" in {c.law_number_guess for c in cands}


def test_the_default_destinations_are_the_registry_values():
    cfg = {"economy": "MY", "lom": REGISTRY["lom"], "portals": REGISTRY["portals"]}
    adapter = m.MyGazetteAdapter(cfg, today=TODAY)
    assert adapter.root == REGISTRY["lom"]["root"].rstrip("/")
    assert adapter.listings == {k: (v["page"], v["endpoint"]) for k, v in REGISTRY["lom"]["listings"].items()}
    assert adapter.whitelist == tuple(x.lstrip("*.") for x in REGISTRY["portals"]["reputable_fallback"])
    bare = m.MyGazetteAdapter({"economy": "MY"}, today=TODAY)
    assert (bare.root, bare.listings, bare.whitelist) == (LOM, m._LISTINGS, m._WHITELIST)


def test_document_urls_follow_a_custom_lom_root():
    adapter, _client = _mirror_adapter()
    cands = adapter.discover(pillars=[6, 7], scope="seed")
    lom_docs = [c for c in cands if c.contract_meta.get("portal") == "my-lom"]
    assert lom_docs and all(c.url.startswith(MIRROR + "/ilims/") for c in lom_docs)


def _fallback_seed() -> dict:
    return {"law_name": "Cyber Security Act 2024", "law_number": "Act 854", "url": "https://lom.agc.gov.my",
            "fallback_url": "https://statutes.mirror-copy.example/act854.pdf", "indicators": ["P7-I2"]}


def test_reputable_fallback_from_the_registry_decides_which_secondary_copy_is_used():
    seeds = (_fallback_seed(), SEED_GP3)
    custom = {"economy": "MY", "lom": {}, "seed_laws": list(seeds),           # robots.txt 500, no decision: lom out
              "portals": {"reputable_fallback": ["*.mirror-copy.example"]}}
    adapter, _client = _adapter(custom)
    assert adapter.whitelist == ("mirror-copy.example",)
    cands = _by_number(adapter.discover(pillars=[6, 7], scope="seed"))
    assert cands["Act 854"].url == "https://statutes.mirror-copy.example/act854.pdf"
    assert cands["Act 854"].contract_meta["crawl_flags"] == ["secondary_copy"]

    registry = {**custom, "portals": REGISTRY["portals"]}
    adapter, _client = _adapter(registry)
    cands = _by_number(adapter.discover(pillars=[6, 7], scope="seed"))
    assert "Act 854" not in cands and "GP 3/2025" in cands
    assert "seed 'Cyber Security Act 2024': no resolvable URL" in adapter.notes


# --- 7. the catalogue ---------------------------------------------------------------------------

CATALOGUE_UPDATED = _unique(UPDATED_RECORDS + FINANCE_RECORDS)
CATALOGUE_DETAIL = {"709": DETAIL_709, "A1727": DETAIL_A1727, "53": DETAIL_53, "874": DETAIL_874}


def _catalogue_adapter(**session_kw):
    cfg = _cfg(seeds=(SEED_709, SEED_A1727, SEED_GP3), timeline="rule", subsidiary_acts="core",
               subsidiary_max_per_act=0)
    kw = {"updated": CATALOGUE_UPDATED, "detail": CATALOGUE_DETAIL, **session_kw}
    return _adapter(cfg, **kw)


@pytest.fixture(scope="module")
def built():
    with pytest.MonkeyPatch.context() as mp:          # module scope runs before the autouse fixture
        for name in list(os.environ):
            if name.startswith("LOM_"):
                mp.delenv(name)
        adapter, client = _catalogue_adapter()
        result = m.catalogue.build(adapter, [6, 7])
    return adapter, client, result


def _rank(row: dict) -> int:
    return 0 if "seed" in row["scopes"] else (1 if "relevant" in row["scopes"] else 2)


def test_catalogue_documents_carry_nested_scopes_in_crawl_order(built):
    adapter, client, result = built
    docs = result["documents"]
    assert [d["order"] for d in docs] == list(range(1, len(docs) + 1))
    scope = {s: {d["url"] for d in docs if s in d["scopes"]} for s in ("seed", "relevant", "all")}
    assert scope["seed"] and scope["seed"] < scope["relevant"] < scope["all"]
    assert scope["all"] == {d["url"] for d in docs} and len(scope["all"]) == len(docs)
    assert [_rank(d) for d in docs] == sorted(_rank(d) for d in docs)          # seeds, then relevant, then the rest
    assert result["meta"]["counts"] == {s: len(u) for s, u in scope.items()}
    seed_numbers = {d["law_number_guess"] for d in docs if "seed" in d["scopes"]}
    assert {"Act 709", "Act A1727", "P.U. (B) 522/2024", "GP 3/2025"} <= seed_numbers
    assert docs[0]["law_number_guess"] == "Act 709"
    relevant_only = {d["law_number_guess"] for d in docs if _rank(d) == 1}
    assert {"Act 854", "Act 747", "Act 593", "Act 563", "Act 53"} <= relevant_only
    assert "Act 762" not in relevant_only and "Act 874" not in relevant_only


def test_catalogue_order_is_scope_rank_first_then_discovery_order(monkeypatch):
    adapter, _client = _catalogue_adapter()
    discover = adapter.discover
    monkeypatch.setattr(adapter, "discover", lambda **kw: list(reversed(discover(**kw))))
    docs = m.catalogue.build(adapter, [6, 7])["documents"]
    assert [d["order"] for d in docs] == list(range(1, len(docs) + 1))
    assert [_rank(d) for d in docs] == sorted(_rank(d) for d in docs)
    seed_rows = [d for d in docs if _rank(d) == 0]
    assert docs[:len(seed_rows)] == seed_rows
    assert seed_rows[-1]["law_number_guess"] == "Act 709"      # discovery order, reversed, within the seed rank


def test_catalogue_scopes_send_no_extra_request_and_meta_counts_them(built):
    adapter, client, result = built
    meta = result["meta"]
    assert meta["requests"] == len(client.session.calls) == len(result["discovery_log"])
    assert not any("extra request" in n for n in meta["notes"])
    assert meta["rule_id"] == REGISTRY["title_rule"]["id"]
    assert meta["settings"]["timeline"] == "rule" and meta["settings"]["subsidiary_acts"] == "core"
    assert meta["timelines_read"] == len(adapter.timelines)
    assert sum(meta["document_kinds"].values()) == len(result["documents"])
    assert meta["document_kinds"]["agency_or_other"] == 1                  # the GP 3/2025 guideline


def test_catalogue_laws_has_a_row_for_every_listing_record(built):
    adapter, _client, result = built
    laws = result["laws"]
    assert len(laws) == len(adapter.principals) + len(adapter.amendments)
    assert {r["portal_id"] for r in laws if r["listing"] == "updated"} == {p.act_no for p in adapter.principals.values()}
    assert {r["portal_id"] for r in laws if r["listing"] == "amendment"} == set(adapter.amendments)
    assert all(set(r) == set(m.catalogue._LAW_COLUMNS) for r in laws)
    row = {(r["listing"], r["portal_id"]): r for r in laws}
    no_docs = row[("updated", "663")]
    assert (no_docs["documents_offered"], no_docs["document_url"], no_docs["in_all"]) == (0, None, False)
    assert no_docs["not_crawled_reason"] == "the portal offers no document"
    assert all(r["not_crawled_reason"] == "the portal offers no document" for r in laws if r["documents_offered"] == 0)
    assert all(r["not_crawled_reason"] is None for r in laws if r["in_all"])
    pdpa = row[("updated", "709")]
    assert (pdpa["in_seed"], pdpa["rule_selected"], pdpa["timeline_read"], pdpa["not_crawled_reason"]) == (
        True, True, True, None)
    finance = row[("updated", "874")]
    assert (finance["principal_law_number"], finance["amends"], finance["title_rule_exclusion"]) == (
        "Act 53", ["Act 53"], "X1_annual_finance_act")
    assert (finance["rule_selected"], finance["in_relevant"], finance["document_kinds"]) == (
        False, False, ["amending_act"])
    gst = row[("updated", "762")]
    assert (gst["title_rule_groups"], gst["rule_selected"], gst["legal_status"]) == (
        ["S2_tax_records"], False, "repealed")
    a1727 = row[("amendment", "A1727")]
    assert (a1727["principal_law_number"], a1727["in_seed"], a1727["timeline_read"]) == ("Act 709", True, True)


def test_catalogue_write_then_read_documents_round_trips(built, tmp_path):
    _adapter_, client, result = built
    paths = m.catalogue.write(result, tmp_path / "links")
    assert set(paths) == {"documents.jsonl", "documents.csv", "laws.csv", "catalogue_meta.json", "discovery_log.jsonl"}
    rows, meta = m.catalogue.read_documents(paths["documents.jsonl"])
    assert rows == json.loads(json.dumps(result["documents"], ensure_ascii=False, default=str))
    assert meta == json.loads(json.dumps(result["meta"], ensure_ascii=False, default=str))
    with open(paths["documents.csv"], encoding="utf-8-sig", newline="") as fh:
        table = list(csv.DictReader(fh))
    assert list(table[0]) == m.catalogue._DOC_COLUMNS and len(table) == len(rows)
    assert [int(r["order"]) for r in table] == [r["order"] for r in rows]
    with open(paths["laws.csv"], encoding="utf-8-sig", newline="") as fh:
        assert len(list(csv.DictReader(fh))) == len(result["laws"])
    log_lines = Path(paths["discovery_log.jsonl"]).read_text(encoding="utf-8").splitlines()
    assert len(log_lines) == len(client.session.calls)


def test_candidate_from_row_restores_every_field_and_contract_meta(built, tmp_path):
    _adapter_, _client, result = built
    paths = m.catalogue.write(result, tmp_path / "links")
    rows, _meta = m.catalogue.read_documents(paths["documents.jsonl"])
    for row in rows:
        cand = m.catalogue.candidate_from_row(row)
        assert isinstance(cand, Candidate)
        assert {f.name: getattr(cand, f.name) for f in fields(Candidate)} == {
            f.name: row[f.name] for f in fields(Candidate)}
        assert cand.contract_meta == row["contract_meta"]
    finance = next(m.catalogue.candidate_from_row(r) for r in rows if r["law_number_guess"] == "Act 874")
    assert (finance.contract_meta["document_kind"], finance.contract_meta["amends"]) == ("amending_act", ["Act 53"])


# --- 8. lom.frontier: links_file ------------------------------------------------------------------

@pytest.fixture(scope="module")
def links_file(built, tmp_path_factory):
    _adapter_, _client, result = built
    paths = m.catalogue.write(result, tmp_path_factory.mktemp("links"))
    rows, _meta = m.catalogue.read_documents(paths["documents.jsonl"])
    return Path(paths["documents.jsonl"]), rows


def _frontier_adapter(path, robots=(500, "error"), robots_5xx="allow", seeds=None):
    """The registry the link file was built from (a replay refuses another one), set to replay it."""
    cfg = _catalogue_adapter()[0].cfg
    cfg = {**cfg, "lom": {**cfg["lom"], "frontier": "links_file"}}
    if seeds is not None:
        cfg["seed_laws"] = list(seeds)
    if path is not None:
        cfg["lom"]["links_file"] = str(path)
    if robots_5xx:
        cfg["lom"]["robots_5xx"] = robots_5xx
    else:
        cfg["lom"].pop("robots_5xx", None)
    return _adapter(cfg, robots=robots)


@pytest.mark.parametrize("scope", ["seed", "relevant", "all"])
def test_links_file_frontier_serves_exactly_the_rows_of_the_scope_in_order_after_robots_txt_only(links_file, scope):
    path, rows = links_file
    adapter, client = _frontier_adapter(path)
    cands = adapter.discover(pillars=[6, 7], scope=scope)
    expected = [r for r in rows if scope in r["scopes"]]
    assert [c.url for c in cands] == [r["url"] for r in expected]
    assert [c.contract_meta for c in cands] == [r["contract_meta"] for r in expected]
    assert client.session.calls == [("GET", LOM + "/robots.txt")]
    assert adapter.frontier_meta["links_file"] == str(path)
    assert adapter.notes[0].startswith(f"frontier links_file {path} generated ")
    assert f": {len(expected)} of {len(rows)} rows in scope {scope}; 0 dropped by robots.txt" in adapter.notes[0]


def test_links_file_frontier_drops_a_lom_row_robots_txt_disallows(links_file):
    path, rows = links_file
    target = next(r["url"] for r in rows if "seed" in r["scopes"] and _host(r["url"]) == "lom.agc.gov.my")
    robots = f"User-agent: *\nDisallow: {urlparse(target).path}$\n"
    adapter, client = _frontier_adapter(path, robots=(200, robots))
    cands = adapter.discover(pillars=[6, 7], scope="seed")
    assert [c.url for c in cands] == [r["url"] for r in rows if "seed" in r["scopes"] and r["url"] != target]
    assert f"{target}: disallowed by lom robots.txt, not fetched" in adapter.notes
    assert client.session.calls == [("GET", LOM + "/robots.txt")]
    assert adapter.robots_record["applied"] == "rules"


def test_links_file_frontier_keeps_only_rows_outside_lom_when_robots_5xx_is_denied(links_file, capsys):
    path, rows = links_file
    adapter, client = _frontier_adapter(path, robots_5xx=None)
    cands = adapter.discover(pillars=[6, 7], scope="all")
    # as discover() does: the seeds come first, lom seeds through their registry URLs, then the other non-lom rows
    fallback = [s["url"] for s in (SEED_709, SEED_A1727, SEED_GP3)]
    expected = fallback + [r["url"] for r in rows if _host(r["url"]) != "lom.agc.gov.my" and r["url"] not in fallback]
    assert [c.url for c in cands] == expected
    assert client.session.calls == [("GET", LOM + "/robots.txt")]
    assert "robots.txt" in adapter.lom_error and adapter.robots_record["applied"] == "deny"
    assert "LOM UNAVAILABLE" in capsys.readouterr().out


def test_links_file_frontier_without_a_path_is_a_configuration_error_before_any_request():
    adapter, client = _frontier_adapter(None)
    with pytest.raises(ValueError, match="links_file"):
        adapter.discover(pillars=[6, 7], scope="seed")
    assert client.session.calls == []


def test_links_file_path_can_come_from_the_environment(links_file, monkeypatch):
    path, rows = links_file
    monkeypatch.setenv("LOM_LINKS_FILE", str(path))
    adapter, _client = _frontier_adapter(None)
    assert [c.url for c in adapter.discover(pillars=[6, 7], scope="seed")] == [
        r["url"] for r in rows if "seed" in r["scopes"]]


def test_links_file_frontier_that_selects_nothing_fails_loudly(links_file, tmp_path):
    _path, rows = links_file
    only_rest = tmp_path / "documents.jsonl"
    only_rest.write_text("".join(json.dumps(r) + "\n" for r in rows if "seed" not in r["scopes"]), encoding="utf-8")
    adapter, client = _frontier_adapter(only_rest)
    with pytest.raises(RuntimeError, match="selected no candidates for scope seed"):
        adapter.discover(pillars=[6, 7], scope="seed")
    assert client.session.calls == [("GET", LOM + "/robots.txt")]
    adapter, _client = _frontier_adapter(tmp_path / "missing.jsonl")
    with pytest.raises(FileNotFoundError):
        adapter.discover(pillars=[6, 7], scope="seed")



# --- 9. fixes from the 2026-09-14 review ----------------------------------------------------------

def test_a_catalogue_build_discovers_whatever_lom_frontier_says(built, monkeypatch, tmp_path):
    monkeypatch.setenv("LOM_FRONTIER", "links_file")
    monkeypatch.setenv("LOM_LINKS_FILE", str(tmp_path / "an-old-list.jsonl"))
    adapter, _client = _catalogue_adapter()
    result = m.catalogue.build(adapter, [6, 7])
    assert result["meta"]["counts"] == built[2]["meta"]["counts"]
    assert result["meta"]["cfg_sha256"] == m.catalogue.cfg_fingerprint(adapter.cfg)


def test_a_catalogue_build_that_could_not_read_lom_writes_nothing():
    cfg = _catalogue_adapter()[0].cfg
    adapter, _client = _adapter({**cfg, "lom": {k: v for k, v in cfg["lom"].items() if k != "robots_5xx"}})
    with pytest.raises(RuntimeError, match="nothing written"):
        m.catalogue.build(adapter, [6, 7])


def test_a_link_file_built_from_another_registry_is_refused(links_file):
    path, _rows = links_file
    adapter, client = _frontier_adapter(path, seeds=(SEED_709, SEED_A1727, SEED_GP3, SEED_854))
    with pytest.raises(ValueError, match="different registry"):
        adapter.discover(pillars=[6, 7], scope="seed")
    assert client.session.calls == []


def test_a_seed_naming_a_pu_instrument_resolves_to_the_portal_copy_once():
    html, _info = _core_timeline_854()
    seed_pu = {"law_name": "Cyber Security (Example) Regulations 2025", "law_number": "P.U. (A) 5/2025",
               "url": "https://www.nacsa.gov.my/doc/example.pdf", "indicators": ["P7-I2"],
               "provenance": "p1_discovery_sweep:2026-07-15"}
    for policy in ("none", "core"):
        adapter, _client = _adapter(_cfg(seeds=(SEED_854, seed_pu), subsidiary_acts=policy, subsidiary_max_per_act=0),
                                    detail={"854": html})
        cands = adapter.discover(pillars=[6, 7], scope="seed")
        assert not [c for c in cands if "nacsa.gov.my" in c.url]
        (resolved,) = [c for c in cands if c.law_number_guess == "P.U. (A) 5/2025"]
        assert resolved.law_name_guess == seed_pu["law_name"] and resolved.indicator_hints == "P7-I2"
        assert resolved.url.startswith(LOM + "/ilims/upload/portal/akta/outputp/910005/")
        meta = resolved.contract_meta
        assert (meta["document_kind"], meta["discovery_path"], meta["principal_law_number"]) == (
            "subsidiary_legislation", "seed", "Act 854")
        assert meta["review_flags"] == ["seed_resolved_to_portal"] and meta["seed_provenance"] == seed_pu["provenance"]


def test_a_seed_with_an_incomplete_pu_number_is_warned_about(capsys):
    seed = {"law_name": "Cyber Security (Example) Regulations 2024", "law_number": "P.U.(A) 2024",
            "url": "https://www.nacsa.gov.my/doc/example.pdf", "indicators": ["P7-I2"]}
    adapter, _client = _adapter(_cfg(seeds=(SEED_709, seed)))
    adapter.discover(pillars=[6, 7], scope="seed")
    assert "without N/YYYY" in capsys.readouterr().out


def test_a_repealed_act_on_another_acts_timeline_is_flagged_not_reclassified():
    adapter = _offline_adapter(UPDATED_RECORDS + REVIEW_UPDATED)
    repealed = adapter.principals["691"]
    doc = m.choose_principal_document(repealed, ["eng", "msa"])
    adapter.timelines["53"] = m.parse_timeline(DETAIL_53) + [m.TimelineEntry(
        date="01/01/2015", display_date="01 Jan 2015", log_type="AMENDMENTS", project_id="999999", file_url=doc.url)]
    assert "691" not in adapter._listed_as_amendment()
    assert adapter._listed_on_other_timeline()["691"] == ["53"]
    meta = adapter._principal_candidate(repealed, law=None, indicators=[]).contract_meta
    assert (meta["document_kind"], meta["legal_status"]) == ("principal_act", "repealed")
    assert "listed_on_other_timeline" in meta["review_flags"] and meta["listed_on_timeline_of"] == ["Act 53"]


def test_seed_query_holds_the_words_the_title_rule_matched():
    assert RULE.matched_terms("PERSONAL DATA PROTECTION ACT 2010") == ["data"]
    assert RULE.matched_terms("INCOME TAX ACT 1967") == ["tax"]
    assert RULE.matched_terms("FINANCE ACT 2025") == []
    adapter, _client = _adapter(_cfg(seeds=(SEED_709,)))
    cands = _by_number(adapter.discover(pillars=[6, 7], scope="seed"))
    assert cands["Act 709"].seed_query == "data"
    assert cands["Act 709"].contract_meta["title_rule_groups"] == ["G1_data_protection_privacy"]


def test_an_empty_reputable_fallback_list_means_no_secondary_copies():
    assert m.MyGazetteAdapter({"economy": "MY", "portals": {"reputable_fallback": []}}, today=TODAY).whitelist == ()
    assert m.MyGazetteAdapter({"economy": "MY"}, today=TODAY).whitelist == m._WHITELIST


def test_commencement_text_in_manifest_columns_is_single_line():
    adapter = _offline_adapter([])
    amd = m.parse_amendment(next(r for r in REVIEW_AMENDMENTS if r["ACTNO_LEGISLATION"] == "A1530"))
    assert "\n" in amd.commencement_remark
    (cand,) = adapter._amendment_candidates(amd, None, client=None)
    assert "\n" not in cand.commencement_date and "\n" not in cand.in_force_status
    assert cand.contract_meta["commencement_note"] == amd.commencement_remark        # the raw text is kept
    assert m.catalogue._cell("a\r\n\r\nb  c") == "a b c"


def test_the_last_amending_instrument_can_be_a_plain_numbered_act_on_the_timeline():
    _adapter_, _client, cands = _finance_run("seed", (SEED_53,), "seed")
    meta = cands["Act 53"].contract_meta
    assert (meta["last_amending_instrument"], meta["last_amended_year"]) == ("Act 874", "2025")
    assert "Act 874" in {e["law_number"] for e in meta["linked_amendments"]}


def test_an_amendment_known_only_from_a_timeline_gets_a_short_name():
    adapter = _offline_adapter(UPDATED_RECORDS)
    entry = m.TimelineEntry(date="14/12/1967", display_date="14 Dec 1967", log_type="AMENDMENTS", project_id="1",
                            file_url=LOM + "/ilims/upload/portal/akta/outputaktap/1_BI/ACT%20A77.pdf")
    cand = adapter._timeline_amendment_candidate(entry, adapter.principals["53"])
    assert cand.law_name_guess == "Amendment of Act 53 (14 Dec 1967)"
    assert cand.contract_meta["amends_title"] == "INCOME TAX ACT 1967"


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


def test_the_law_table_normalises_the_as_at_date_and_takes_the_last_amendment_from_our_own_rows(tmp_path):
    from p1_scrape.adapters.my_gazette import checker
    links = [
        {"url": "https://lom.agc.gov.my/act-detail.php?act=709", "law_name_guess": "Personal Data Protection Act 2010",
         "contract_meta": {"portal_id": "709", "law_number": "Act 709", "document_kind": "principal_act",
                           "legal_status": "unknown", "status_source": None, "text_version": "reprint",
                           "published_on": "2010-06-10", "language": "eng", "review_flags": []}},
        {"url": "https://lom.agc.gov.my/act-detail.php?act=A1709", "law_name_guess": "PDPA (Amendment) Act 2024",
         "contract_meta": {"portal_id": "A1709", "law_number": "Act A1709", "document_kind": "amending_act",
                           "principal_law_number": "Act 709", "published_on": "2024-10-17", "language": "eng"}},
        {"url": "https://lom.agc.gov.my/act-detail.php?act=A1600", "law_name_guess": "An older amendment",
         "contract_meta": {"portal_id": "A1600", "law_number": "Act A1600", "document_kind": "amending_act",
                           "principal_law_number": "Act 709", "published_on": "2016-01-01", "language": "eng"}},
    ]
    census_cols = ["listing", "portal_id", "law_number", "title_bi", "title_bm", "status_marker", "legal_status",
                   "as_at", "document_url", "document_language", "document_kinds", "not_crawled_reason",
                   "principal_law_number"]
    census = [
        {"listing": "updated", "portal_id": "709", "law_number": "Act 709", "title_bi": "Personal Data Protection Act 2010",
         "title_bm": "", "status_marker": "", "legal_status": "unknown", "as_at": "15-09-2026", "document_url": "",
         "document_language": "eng", "document_kinds": "principal_act", "not_crawled_reason": "", "principal_law_number": ""},
        {"listing": "updated", "portal_id": "384", "law_number": "Act 384", "title_bi": "Pool Betting Act 1967",
         "title_bm": "", "status_marker": "Superseded by Act 809", "legal_status": "repealed", "as_at": "01-01-2018",
         "document_url": "https://lom.agc.gov.my/act-detail.php?act=384", "document_language": "eng",
         "document_kinds": "principal_act", "not_crawled_reason": "", "principal_law_number": ""},
    ]
    stored = [{"doc_id": "my-pdpa2010-001", "source_url": links[0]["url"], "access_date": "2026-09-14T07:00:00Z",
               "local_path": "raw/my/personal_data_protection_act_2010/x__native.pdf"}]
    run = _folder(tmp_path, links, census, stored, census_cols)

    rows = checker.rows_for(run)
    assert len(rows) == 1
    r = rows[0]
    assert (r["in_force"], r["legal_status"], r["status_marker"]) == ("not stated", "unknown", "")
    assert r["effective_date"] == "2026-09-15"                     # the census writes 15-09-2026
    assert (r["last_amended"], r["last_amending_instrument"]) == ("2024-10-17", "Act A1709")   # the newer of the two
    assert (r["text_version"], r["language"], r["scraped"]) == ("reprint", "eng", "yes")

    both = checker.rows_for(run, include_unfetched=True)
    superseded = [x for x in both if x["law_number"] == "Act 384"][0]
    assert (superseded["in_force"], superseded["status_marker"]) == ("no (repealed)", "Superseded by Act 809")
    assert superseded["effective_date"] == "2018-01-01"
    amendment = [x for x in both if x["law_number"] == "Act A1709"][0]
    assert amendment["last_amended"] == ""                          # only a principal act gets one
    assert checker.main([str(run)]) == 0


def test_the_use_column_marks_amendments_as_linkage_unless_the_stored_text_is_older(tmp_path):
    from p1_scrape.adapters.my_gazette import checker
    links = [
        {"url": "https://lom.agc.gov.my/a/646", "law_name_guess": "ARBITRATION ACT 2005",
         "contract_meta": {"portal_id": "646", "law_number": "Act 646", "document_kind": "principal_act",
                           "legal_status": "unknown", "text_version": "reprint", "published_on": "2005-12-30"}},
        {"url": "https://lom.agc.gov.my/a/A1737", "law_name_guess": "ARBITRATION (AMENDMENT) ACT 2024",
         "contract_meta": {"portal_id": "A1737", "law_number": "Act A1737", "document_kind": "amending_act",
                           "principal_law_number": "Act 646", "published_on": "2024-11-01"}},
        {"url": "https://lom.agc.gov.my/a/A1395", "law_name_guess": "ARBITRATION (AMENDMENT) ACT 2011",
         "contract_meta": {"portal_id": "A1395", "law_number": "Act A1395", "document_kind": "amending_act",
                           "principal_law_number": "Act 646", "published_on": "2011-06-30"}},
        {"url": "https://lom.agc.gov.my/a/709", "law_name_guess": "PERSONAL DATA PROTECTION ACT 2010",
         "contract_meta": {"portal_id": "709", "law_number": "Act 709", "document_kind": "principal_act",
                           "legal_status": "unknown", "text_version": "reprint", "published_on": "2010-06-10"}},
    ]
    census_cols = ["listing", "portal_id", "law_number", "title_bi", "title_bm", "status_marker", "legal_status",
                   "as_at", "document_url", "document_language", "document_kinds", "not_crawled_reason",
                   "principal_law_number"]
    def c(portal_id, number, title, as_at):
        return {"listing": "updated", "portal_id": portal_id, "law_number": number, "title_bi": title, "title_bm": "",
                "status_marker": "", "legal_status": "unknown", "as_at": as_at, "document_url": "",
                "document_language": "eng", "document_kinds": "principal_act", "not_crawled_reason": "",
                "principal_law_number": ""}
    census = [c("646", "Act 646", "ARBITRATION ACT 2005", "01-11-2018"),      # the text predates A1737
              c("709", "Act 709", "PERSONAL DATA PROTECTION ACT 2010", "15-09-2026")]
    stored = [{"doc_id": f"my-x{i}-001", "source_url": l["url"], "access_date": "2026-09-14T07:00:00Z",
               "local_path": f"raw/my/x{i}/a__native.pdf"} for i, l in enumerate(links)]
    run = _folder(tmp_path, links, census, stored, census_cols)

    use = {r["law_number"]: r["use"] for r in checker.rows_for(run)}
    assert use["Act 646"] == "evidence, text stale"     # stored as at 2018, amended 2024
    assert use["Act A1737"] == "linkage, text needed"   # the amendment the stored text does not carry
    assert use["Act A1395"] == "linkage"                # older than the stored text: already consolidated in
    assert use["Act 709"] == "evidence"                 # nothing newer than its text
