"""Malaysia update check (countries/my-malaysia/updates/): offline tests for the baseline, the P.U. listings, the
comparison, the delta list and the command line. Written 2026-09-14 against pages saved from lom.agc.gov.my on
2026-09-13 and 2026-09-14 (the P.U. records are the first rows of the live listings, saved by hand at 21:47 UTC).

No test sends a request: FakeSession stands in for the portal, as in test_my_catalogue.py, extended with the
P.U. (A)/(B) endpoint and conditional HEAD requests. A baseline run is built offline with scraper.catalogue, then
the fake portal is changed and the check must find exactly those changes.
"""
from __future__ import annotations

import base64
import copy
import csv
import hashlib
import json
import os
import re
from pathlib import Path
from urllib.parse import quote, unquote

import pytest
import yaml

from p1_scrape.adapters import my_gazette as m
from p1_scrape.adapters.my_gazette import catalogue, updates
from p1_scrape.adapters.my_gazette.records import LomUnavailable
from p1_scrape.adapters.my_gazette.updates import baseline as B, delta as X, diff as D, listings as L
from p1_scrape.adapters.my_gazette.updates.__main__ import main as cli_main, new_run_dir

_HERE = Path(__file__).parent
FIX = _HERE / "fixtures" / "my" if (_HERE / "fixtures" / "my").is_dir() else _HERE / "fixtures"
LOM = "https://lom.agc.gov.my"
TODAY = "2026-09-21"


def _read(name: str) -> str:
    return (FIX / name).read_text(encoding="utf-8")


def _records(name: str) -> list[dict]:
    return json.loads(_read(name))["records"]


UPDATED_PAGE = "lom_principal_updated_2026-09-13.html"
UPDATED_RECORDS = _records("lom_updated_records_2026-09-13.json")
AMENDMENT_RECORDS = _records("lom_amendment_records_2026-09-13.json")
PUA_RECORDS = _records("lom_subsid_pua_records_2026-09-14.json")
PUB_RECORDS = _records("lom_subsid_pub_records_2026-09-14.json")
DETAIL_709 = _read("lom_act_detail_709_BI_2026-09-13.html")
DETAIL_A1727 = _read("lom_amendment_detail_A1727_BI_2026-09-13.html")
KEY = m.extract_response_key(_read(UPDATED_PAGE))


def _registry() -> dict:
    for path in (_HERE.parent / "sources.yaml", _HERE.parent / "contracts" / "instrument" / "sources_my.yaml",
                 _HERE.parent / "instrument" / "sources_my.yaml"):
        if path.is_file():
            return yaml.safe_load(path.read_text(encoding="utf-8"))
    raise FileNotFoundError("no Malaysian registry next to the tests")


REGISTRY = _registry()
SEED_709 = {"law_name": "Personal Data Protection Act 2010", "law_number": "Act 709",
            "url": "https://www.pdp.gov.my/ppdpv1/en/akta/", "indicators": ["P6-I1", "P7-I1"],
            "provenance": "round1_registry"}
SEED_A1727 = {"law_name": "Personal Data Protection (Amendment) Act 2024", "law_number": "Act A1727",
              "url": "https://www.pdp.gov.my/x/", "indicators": ["P6-I1", "P7-I3"]}
SEED_GP3 = {"law_name": "Personal Data Protection Guideline on Cross-Border Personal Data Transfer (GP 3/2025)",
            "law_number": "GP 3/2025",
            "url": "https://www.pdp.gov.my/ppdpv1/wp-content/uploads/2025/08/GP_CBPDT_EN-1.pdf",
            "indicators": ["P6-I4"], "provenance": "p3_request:DELTA_CRAWL_REQUEST_2026-07-14#6"}
SINCE = "2026-09-01"


@pytest.fixture(autouse=True)
def _no_lom_environment(monkeypatch):
    for name in list(os.environ):
        if name.startswith("LOM_"):
            monkeypatch.delenv(name)


# --- the fake portal ------------------------------------------------------------------------------------------

def _encrypt(obj: dict, key_hex: str = KEY) -> dict:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    iv = os.urandom(12)
    sealed = AESGCM(bytes.fromhex(key_hex)).encrypt(iv, json.dumps(obj).encode(), None)
    return {"encrypted": True, "data": base64.b64encode(iv + sealed[-16:] + sealed[:-16]).decode()}


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
    """The portal: robots.txt, the listing pages (all carry the key), the four DataTables endpoints, signed detail
    links, and conditional HEADs on documents."""

    def __init__(self, robots=(500, "error"), updated=None, amendments=None, pua=None, pub=None, detail=None,
                 head=None, short=None):
        self.calls: list[tuple[str, str]] = []
        self.headers: list[dict] = []
        self.forms: list[dict] = []
        self.robots = robots
        self.updated = UPDATED_RECORDS if updated is None else updated
        self.amendments = AMENDMENT_RECORDS if amendments is None else amendments
        self.subsid = {"pua": PUA_RECORDS if pua is None else pua, "pub": PUB_RECORDS if pub is None else pub}
        self.detail = {"709": DETAIL_709, "A1727": DETAIL_A1727} if detail is None else detail
        self.head = head or {}                    # url -> HEAD status, or (status, etag, last_modified)
        self.short = short or {}                  # endpoint -> records withheld: the reply claims more than it serves

    def request(self, method, url, data=None, headers=None, timeout=None, allow_redirects=True):
        self.calls.append((method, url))
        self.headers.append(dict(headers or {}))
        if url.endswith("/robots.txt"):
            return FakeResp(*self.robots)
        if method == "HEAD":
            spec = self.head.get(url, 304)
            status, etag, lm = spec if isinstance(spec, tuple) else (spec, '"new"' if spec == 200 else '"same"',
                                                                      "Mon, 15 Sep 2026 00:00:00 GMT")
            resp_headers = {"ETag": etag, "Last-Modified": lm}
            if status in (301, 302, 303, 307, 308):
                resp_headers["Location"] = url + "?session=1"
            return FakeResp(status, "", resp_headers)
        if method == "GET" and ("principal.php?type=" in url or "subsid.php?type=" in url):
            return FakeResp(200, _read(UPDATED_PAGE))
        if method == "POST":
            self.forms.append(dict(data))
            start, length = int(data["start"]), int(data["length"])
            if url.endswith("json-updated-2024.php"):
                records = self.updated
            elif url.endswith("json-amendment-2024.php"):
                records = self.amendments
            elif url.endswith("json-subsid-2024.php"):
                records = sorted(self.subsid[data["type"]], key=lambda r: r.get("publicationDate") or "", reverse=True)
            else:
                return FakeResp(404, "not found")
            withheld = self.short.get(url.rsplit("/", 1)[-1], 0)
            served = records[:len(records) - withheld] if withheld else records
            body = {"draw": data["draw"], "records": served[start:start + length], "recordsTotal": len(records)}
            return FakeResp(200, _encrypt(body))
        if method == "GET" and "processFile.php" in url:
            target = m.decode_token_target(url) or ""
            act = next((k for k in self.detail if f"act={k}&" in target or target.endswith(f"act={k}")), "x")
            return FakeResp(302, "", {"Location": "act-detail.php?a=" + act})
        if method == "GET" and "act-detail.php?a=" in url:
            return FakeResp(200, self.detail.get(url.rsplit("a=", 1)[-1], "Invalid request"))
        return FakeResp(404, "not found")


def _client(session: FakeSession) -> m.LomClient:
    now = [0.0]

    def sleep(s: float) -> None:
        now[0] += s

    return m.LomClient("test-agent", delay_seconds=3.0, session=session, sleep=sleep, clock=lambda: now[0],
                       jitter=False, now_iso=lambda: "2026-09-21T00:00:00Z")


def _get_client_for(session: FakeSession):
    """A stand-in for MyGazetteAdapter._get_client that gives the adapter a client on the fake portal."""
    def get(self, fetcher):
        if self._client is None:
            self._client = _client(session)
        return self._client
    return get


def _cfg(seeds=(SEED_709, SEED_A1727, SEED_GP3), **lom) -> dict:
    cfg = {"economy": "MY", "lom": {"robots_5xx": "allow", "timeline": "rule", "subsidiary_acts": "core",
                                    "subsidiary_max_per_act": 0, **lom},
           "seed_laws": list(seeds), "title_rule": REGISTRY["title_rule"],
           "updates": {"subsidiary_page_size": 3, "subsidiary_max_pages": 5, "subsidiary_lookback_days": 0}}
    return cfg


# --- portal mutations ------------------------------------------------------------------------------------------

def _rec(records: list[dict], act_no: str) -> dict:
    return next(r for r in records if r["lgt_act_no"].strip() == act_no)


def _replace_all(rec: dict, pairs: list[tuple[str, str]]) -> dict:
    out = copy.deepcopy(rec)
    for k, v in out.items():
        if isinstance(v, str):
            for old, new in pairs:
                v = v.replace(old, new)
            out[k] = v
    return out


def _reconsolidated(rec: dict, new_pid: str, new_as_at: str) -> dict:
    """The act's English file replaced by a newer consolidation: new project id, new file name, new As At."""
    p = m.parse_principal(rec)
    doc = next(d for d in p.documents if d.language == "eng")
    old_pid = re.search(r"/(\d+)_BI/", doc.url).group(1)
    old_name = unquote(doc.url.rsplit("/", 1)[-1])
    return _replace_all(rec, [(f"{old_pid}_BI", f"{new_pid}_BI"), (old_name, old_name.replace(".pdf", " NEW.pdf")),
                              (f"lang=BI&date={p.as_at_bi}", f"lang=BI&date={new_as_at}"),
                              (f"<i>As At </i><i>{p.as_at_bi}</i>", f"<i>As At </i><i>{new_as_at}</i>")])


def _renumbered(rec: dict, old: str, new: str) -> dict:
    return _replace_all(rec, [(f"act={old}&", f"act={new}&"), (f'"{old}"', f'"{new}"'), (f"Act {old} ", f"Act {new} "),
                              (f"Akta {old} ", f"Akta {new} ")]) | {"lgt_act_no": new, "lgt_act_id": new}


def _new_amendment(base: dict, a: str, pid: str, title: str, published: str, remark: str) -> dict:
    old_a, old_title = base["ACTNO_LEGISLATION"], m.parse_amendment(base).title_bi
    rec = _replace_all(base, [(old_a, a), (base["ILP_PROJECT_ID"], pid), (base["TajukBI"], title), (old_title, title)])
    rec.update({"nombor": a[1:], "ACTNO_LEGISLATION": a, "ILP_PROJECT_ID": pid, "TajukBI": title,
                "PUBLICATIONDATE": published, "ROYALASSENTDATE": published, "COMMENCEMENTDATEBI": "",
                "COMMENCEMENTREMARKBI": remark, "COMMENCEMENTREMARKBM": remark,
                "LEGISLATIONTITLEBI_LINK": f'<a href="{_detail_token(f"{LOM}/act-detail.php?type=amendment&act={a}&lang=BI")}">{title}</a>',
                "LEGISLATIONTITLEBM_LINK": f'<a href="{_detail_token(f"{LOM}/act-detail.php?type=amendment&act={a}&lang=BM")}">{title}</a>'})
    return rec


def _detail_token(target: str) -> str:
    """A signed detail-page link, which the listing writes with isDirect=1 (a download link has no isDirect)."""
    return _token(target).replace("processFile.php?token=", "processFile.php?isDirect=1&token=")


def _token(target: str) -> str:
    return "processFile.php?token=" + quote(base64.b64encode(f"{target}|deadbeef".encode()).decode())


def _instrument(base: dict, pu_no: str, act_no: str, published: str, path: str, status="PRINCIPAL") -> dict:
    rec = copy.deepcopy(base)
    rec.update({"noPU": pu_no, "ACT_NO": act_no, "publicationDate": published, "statusOfLegislation": status,
                "susunPU": published[:4] + "-" + re.sub(r"\D", "", pu_no.split("/")[0])[-4:].zfill(4),
                "titleBI": f"TEST INSTRUMENT {pu_no}", "titleBM": f"UJIAN {pu_no}",
                "DOC2DOWNLOAD": f'<a href="{_token(LOM + path)}" target="_blank">x</a>',
                "LRA_BI": f'<a href="{LOM}/act-detail.php?act={act_no}&lang=BI">ACT {act_no}</a>'})
    return rec


# --- the baseline run, built offline with the catalogue -------------------------------------------------------

def _build_run(tmp_path: Path, name: str, cfg: dict, session: FakeSession, started: str,
               extra_urls: tuple[str, ...] = ()) -> tuple[Path, dict]:
    """A run folder as the crawl leaves it: the list it read, a manifest (one row per document, validators in the
    headers) and crawl_status.json. `extra_urls` are documents stored by that run beyond its list."""
    adapter = m.MyGazetteAdapter(cfg, client=_client(session), today=TODAY)
    result = catalogue.build(adapter, [6, 7])
    run = tmp_path / name
    catalogue.write(result, run / "links_used")
    rows = []
    stored = [(d["url"], d["law_name_guess"], d["law_number_guess"]) for d in result["documents"]]
    stored += [(u, u.rsplit("/", 1)[-1], None) for u in extra_urls]
    for i, (url, name_, number) in enumerate(stored, start=1):
        rows.append({"doc_id": f"my-d{i:03d}-001", "economy": "MY", "source_url": url,
                     "content_sha256": hashlib.sha256(url.encode()).hexdigest(),
                     "access_date": f"2026-09-01T{7 + i // 60:02d}:{i % 60:02d}:00Z",
                     "local_path": f"raw/my/d{i}/file.pdf", "law_name_guess": name_, "law_number_guess": number,
                     "http": {"headers": {"ETag": f'"e{i}"', "Last-Modified": "Mon, 01 Sep 2026 00:00:00 GMT"}}})
    (run / "manifest.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    (run / "crawl_status.json").write_text(json.dumps({"started_at": started, "state": "done"}), encoding="utf-8")
    return run, result


@pytest.fixture(scope="module")
def world(tmp_path_factory):
    """A baseline run of the fake portal as it was on 2026-09-01, and the portal as it is now: Act 709
    reconsolidated, a new Act 900, one act gone, a new amending act A1800 (commencing by P.U. (B) 400/2026),
    A1727's remark changed, and new P.U. (A) instruments under Acts 709 (core) and 618 (not core)."""
    with pytest.MonkeyPatch.context() as mp:
        for name in list(os.environ):
            if name.startswith("LOM_"):
                mp.delenv(name)
        tmp = tmp_path_factory.mktemp("runs")
        cfg = _cfg()
        # P.U. (A) 300/2026: published after the baseline's date, but that run stored it already
        stored_pua = LOM + "/ilims/upload/portal/akta/outputp/1/PUA%20300_2026.pdf"
        base_pua = [_instrument(PUA_RECORDS[0], "P.U. (A) 300/2026", "709", "2026-09-02", "/ilims/upload/portal/akta/outputp/1/PUA 300_2026.pdf")]
        base_session = FakeSession(pua=base_pua, pub=[])
        run, built = _build_run(tmp, "MY_ws_2026-09-01", cfg, base_session, "2026-09-01T07:00:00Z",
                                extra_urls=(stored_pua,))

        updated = [r for r in UPDATED_RECORDS]
        gone = next(r for r in updated if r["lgt_act_no"].strip() not in ("709", "884")).copy()
        updated = [r for r in updated if r is not gone and r["lgt_act_no"].strip() != gone["lgt_act_no"].strip()]
        updated = [_reconsolidated(r, "7777777", "01-08-2026") if r["lgt_act_no"].strip() == "709" else r for r in updated]
        updated.append(_renumbered(_rec(UPDATED_RECORDS, "884"), "884", "900"))
        amendments = list(AMENDMENT_RECORDS)
        a1727 = next(r for r in amendments if r["ACTNO_LEGISLATION"] == "A1727")
        changed_1727 = dict(a1727, COMMENCEMENTREMARKBI=(a1727["COMMENCEMENTREMARKBI"] or "") + " (except section 3)")
        amendments = [changed_1727 if r is a1727 else r for r in amendments]
        amendments.append(_new_amendment(AMENDMENT_RECORDS[0], "A1800", "8800000",
                                         "PERSONAL DATA PROTECTION (AMENDMENT) ACT 2026", "20/09/2026",
                                         "01/01/2027 [P.U. (B) 400/2026]"))
        pua = base_pua + [
            _instrument(PUA_RECORDS[0], "P.U. (A) 400/2026", "709", "2026-09-05", "/ilims/upload/portal/akta/outputp/2/PUA 400_2026.pdf"),
            _instrument(PUA_RECORDS[0], "P.U. (A) 401/2026", "618", "2026-09-06", "/ilims/upload/portal/akta/outputp/3/PUA 401_2026.pdf"),
            _instrument(PUA_RECORDS[0], "P.U. (A) 250/2026", "709", "2026-07-01", "/ilims/upload/portal/akta/outputp/4/PUA 250_2026.pdf"),
        ]
        pub = [
            _instrument(PUB_RECORDS[0], "P.U. (B) 400/2026", "709", "2026-09-20", "/ilims/upload/portal/akta/outputp/5/PUB 400_2026.pdf"),
            _instrument(PUB_RECORDS[0], "P.U. (B) 335/2026", "44", "2026-09-14", "/ilims/upload/portal/akta/outputp/6/PUB 335_2026.pdf"),
        ]
        now = FakeSession(updated=updated, amendments=amendments, pua=pua, pub=pub)
        baseline = B.load(tmp)
        adapter, changes, instruments, sub_meta = updates.check(cfg, baseline, None, client=_client(now), today=TODAY)
        result = X.build_delta(adapter, adapter._client, changes, baseline, baseline.since_date, [6, 7],
                               subsidiary_meta=sub_meta)
    return {"tmp": tmp, "cfg": cfg, "run": run, "built": built, "baseline": baseline, "now": now,
            "adapter": adapter, "changes": changes, "instruments": instruments, "sub_meta": sub_meta,
            "result": result, "gone": gone}


def _by(changes: D.Changes, change: str) -> dict[str, D.Change]:
    return {c.portal_id: c for c in changes.all() if c.change == change}


# --- 1. the P.U. listings ---------------------------------------------------------------------------------------

def test_a_real_pu_a_record_parses_to_its_number_parent_act_date_status_and_decoded_file():
    inst = L.parse_subsidiary(PUA_RECORDS[0], "pua")
    assert inst.pu_no == "P.U. (A) 324/2026" and inst.act_no == "618" and inst.status == "PRINCIPAL"
    assert inst.publication_date == "2026-09-11" and inst.sort_key == "2026-0324"
    assert inst.url == LOM + "/ilims/upload/portal/akta/outputp/3705640/PUA%20324_2026.pdf"
    assert inst.title_bi.startswith("DEVELOPMENT FINANCIAL INSTITUTIONS")
    assert inst.commencement is None                    # the listing prints "-"


def test_a_real_pu_b_record_parses_and_a_record_without_a_number_is_skipped():
    inst = L.parse_subsidiary(PUB_RECORDS[0], "pub")
    assert inst.pu_no == "P.U. (B) 335/2026" and inst.act_no == "44" and inst.publication_date == "2026-09-14"
    assert L.parse_subsidiary({**PUB_RECORDS[0], "noPU": ""}, "pub") is None


def test_the_listing_is_read_newest_first_and_stops_at_the_first_page_older_than_since():
    records = [_instrument(PUA_RECORDS[0], f"P.U. (A) {n}/2026", "1", f"2026-09-{d:02d}", f"/ilims/x/{n}.pdf")
               for n, d in ((9, 9), (8, 8), (7, 7), (6, 6), (5, 5), (4, 4), (3, 3))]
    session = FakeSession(pua=records)
    client = _client(session)
    found, meta = L.fetch_subsidiary(client, LOM, "pua", L.DEFAULT_LISTINGS["pua"], "2026-09-06", page_size=2)
    assert [i.pu_no for i in found] == ["P.U. (A) 9/2026", "P.U. (A) 8/2026", "P.U. (A) 7/2026", "P.U. (A) 6/2026"]
    assert meta["pages"] == 3 and meta["records_read"] == 6 and meta["stopped_at"] == "a page older than 2026-09-06"
    assert [f["type"] for f in session.forms] == ["pua"] * 3 and all(f["order[0][dir]"] == "desc" for f in session.forms)
    assert session.calls[0] == ("GET", LOM + "/subsid.php?type=pua")
    assert all(h.get("Referer") == LOM + "/subsid.php?type=pua" for h in session.headers[1:])


def test_the_listing_is_read_back_to_the_look_back_floor_and_repeated_records_are_dropped_once():
    records = [_instrument(PUA_RECORDS[0], "P.U. (A) 9/2026", "1", "2026-09-05", "/ilims/x/9.pdf"),
               _instrument(PUA_RECORDS[0], "P.U. (A) 8/2026", "1", "2026-08-25", "/ilims/x/8.pdf"),
               _instrument(PUA_RECORDS[0], "P.U. (A) 8/2026", "1", "2026-08-25", "/ilims/x/8.pdf"),   # straddles two pages
               _instrument(PUA_RECORDS[0], "P.U. (A) 7/2026", "1", "2026-08-01", "/ilims/x/7.pdf")]
    session = FakeSession(pua=records)
    found, meta = L.fetch_all_subsidiary(_client(session), LOM, {"subsidiary_kinds": ["pua"], "subsidiary_page_size": 2,
                                                                  "subsidiary_lookback_days": 10}, "2026-09-01")
    assert [i.pu_no for i in found] == ["P.U. (A) 9/2026", "P.U. (A) 8/2026"]
    assert meta["pua"]["floor"] == "2026-08-22" and meta["pua"]["lookback_days"] == 10
    assert meta["pua"]["repeated_dropped"] == 1 and meta["pua"]["stopped_at"] == "a page older than 2026-08-22"
    assert L.floor_date("2026-09-01", 120) == "2026-05-04" and L.floor_date(None, 120) is None


def test_a_known_key_saves_the_listing_page_and_a_stale_key_reads_it_once():
    session = FakeSession(pua=[_instrument(PUA_RECORDS[0], "P.U. (A) 1/2026", "1", "2026-09-05", "/ilims/x/1.pdf")])
    found, meta = L.fetch_subsidiary(_client(session), LOM, "pua", L.DEFAULT_LISTINGS["pua"], "2026-09-01", key=KEY)
    assert len(found) == 1 and meta["page_reads"] == 0 and [m_ for m_, _u in session.calls] == ["POST"]
    session = FakeSession(pua=[_instrument(PUA_RECORDS[0], "P.U. (A) 1/2026", "1", "2026-09-05", "/ilims/x/1.pdf")])
    found, meta = L.fetch_subsidiary(_client(session), LOM, "pua", L.DEFAULT_LISTINGS["pua"], "2026-09-01", key="00" * 32)
    assert len(found) == 1 and meta["page_reads"] == 1 and [m_ for m_, _u in session.calls] == ["POST", "GET"]


def test_the_page_cap_is_never_silent():
    records = [_instrument(PUA_RECORDS[0], f"P.U. (A) {n}/2026", "1", "2026-09-09", f"/ilims/x/{n}.pdf") for n in range(10)]
    found, meta = L.fetch_subsidiary(_client(FakeSession(pua=records)), LOM, "pua", L.DEFAULT_LISTINGS["pua"],
                                     "2026-01-01", page_size=2, max_pages=2)
    assert len(found) == 4 and "cap" in meta["stopped_at"]


def test_a_listing_page_that_fails_stops_the_check():
    class Down(FakeSession):
        def request(self, method, url, **kw):
            if "subsid.php" in url:
                self.calls.append((method, url))
                return FakeResp(500, "down")
            return super().request(method, url, **kw)
    with pytest.raises(LomUnavailable):
        L.fetch_subsidiary(_client(Down()), LOM, "pua", L.DEFAULT_LISTINGS["pua"], SINCE)


# --- 2. the baseline -------------------------------------------------------------------------------------------

def test_the_baseline_is_the_newest_run_its_listing_state_and_every_stored_document(world):
    b = world["baseline"]
    assert b.name == "MY_ws_2026-09-01" and b.since_date == "2026-09-01"
    assert b.state_run == world["run"] and b.state_dir.name == "links_used"
    assert len(b.principals) == len({r["lgt_act_no"].strip() for r in UPDATED_RECORDS})
    assert "A1727" in b.amendments and b.amendments["A1727"]["listing"] == "amendment"
    assert len(b.stored) == len(world["built"]["documents"]) + 1 and all(d.etag for d in b.stored.values())
    prev = b.previous("709", "principal_act")
    assert prev["stored"] and prev["doc_id"].startswith("my-d") and prev["version_as_at"] == "2023-07-01"


def test_runs_are_ordered_by_end_date_and_a_check_is_named_for_the_period_it_covers(tmp_path):
    for name in ("MY_ws_2026-09-01", "MY_ws_2026-09-14_2", "MY_ws_2026-09-14", "MY_ws_2026-09-14_to_2026-09-14",
                 "MY_ws_2026-09-14_to_2026-09-21", "MY_ws_2026-09-20", "SG_ws_2026-09-15", "notes"):
        (tmp_path / name).mkdir()
    assert [p.name for p in B.list_runs(tmp_path)] == [
        "MY_ws_2026-09-14_to_2026-09-21", "MY_ws_2026-09-20", "MY_ws_2026-09-14_to_2026-09-14",
        "MY_ws_2026-09-14_2", "MY_ws_2026-09-14", "MY_ws_2026-09-01"]
    assert new_run_dir(tmp_path, today="2026-09-14").name == "MY_ws_2026-09-14_3"
    assert new_run_dir(tmp_path, today="2026-09-20").name == "MY_ws_2026-09-20_2"
    assert new_run_dir(tmp_path, today="2026-09-21", since="2026-09-14").name == "MY_ws_2026-09-14_to_2026-09-21_2"
    assert new_run_dir(tmp_path, today="2026-09-22", since="2026-09-21").name == "MY_ws_2026-09-21_to_2026-09-22"
    with pytest.raises(FileNotFoundError):
        B.load(tmp_path / "empty")


def test_without_out_the_check_names_its_folder_for_the_period(world, tmp_path, capsys, monkeypatch):
    outputs = tmp_path / "MY"
    outputs.mkdir()
    import shutil
    shutil.copytree(world["run"], outputs / "MY_ws_2026-09-01")
    registry = tmp_path / "sources.yaml"
    registry.write_text(yaml.safe_dump({k: v for k, v in world["cfg"].items() if k != "seed_laws"}), encoding="utf-8")
    monkeypatch.setattr(m.MyGazetteAdapter, "_get_client", _get_client_for(FakeSession(pua=[], pub=[])))
    monkeypatch.setattr("p1_scrape.adapters.my_gazette.updates.__main__.date",
                        type("D", (), {"today": staticmethod(lambda: __import__("datetime").date(2026, 9, 21))}))
    rc = cli_main(["--outputs", str(outputs), "--registry", str(registry)])
    assert rc == 0
    assert (outputs / "MY_ws_2026-09-01_to_2026-09-21" / "changes.json").is_file()
    assert "MY_ws_2026-09-01_to_2026-09-21" in capsys.readouterr().out


# --- 3. what changed -------------------------------------------------------------------------------------------

def test_a_reconsolidated_act_is_a_new_version_with_the_file_and_date_as_reasons(world):
    ch = _by(world["changes"], "new_version")["709"]
    assert ch.reasons == ["document", "as-at date"] and ch.crawl is True
    assert ch.before["as_at"] == "2023-07-01" and ch.now["as_at"] == "2026-08-01"
    assert "7777777_BI" in ch.url and ch.url == ch.now["document_url"]


def test_a_new_act_a_gone_act_and_an_unchanged_act_are_told_apart(world):
    changes = world["changes"]
    assert _by(changes, "new_act")["900"].crawl is True
    gone = _by(changes, "gone")
    assert list(gone) == [world["gone"]["lgt_act_no"].strip()] and next(iter(gone.values())).crawl is False
    assert "884" not in {c.portal_id for c in changes.principals}


def test_a_new_amending_act_and_a_changed_commencement_remark(world):
    changes = world["changes"]
    new = _by(changes, "new_amending_act")["A1800"]
    assert new.crawl is True and new.now["publication_date"] == "2026-09-20"
    remark = _by(changes, "commencement_changed")["A1727"]
    assert remark.reasons == ["commencement remark"] and remark.url is None
    assert remark.crawl is False and "nothing new to fetch" in remark.note and "detail page was read" in remark.note


def test_new_instruments_are_those_published_since_and_not_stored(world):
    new = _by(world["changes"], "new_instrument")
    assert set(new) == {"P.U. (A) 400/2026", "P.U. (A) 401/2026", "P.U. (B) 400/2026", "P.U. (B) 335/2026"}
    assert "P.U. (A) 300/2026" not in new         # listed since the date, but the baseline run stored it
    assert "P.U. (A) 250/2026" not in new         # published before since
    assert new["P.U. (A) 400/2026"].crawl is True and "core act" in new["P.U. (A) 400/2026"].note
    assert new["P.U. (A) 401/2026"].crawl is False and "subsidiary_acts=core" in new["P.U. (A) 401/2026"].note
    assert new["P.U. (B) 400/2026"].crawl is True and "cited by Act A1800" in new["P.U. (B) 400/2026"].note
    assert new["P.U. (B) 335/2026"].crawl is False


def test_the_summary_counts_every_change_and_what_is_fetched(world):
    s = world["changes"].summary()
    assert s["mode"] == "baseline" and s["baseline_run"] == "MY_ws_2026-09-01" and s["since"] == "2026-09-01"
    assert s["by_change"]["principal"] == {"new_version": 1, "new_act": 1, "gone": 1}
    assert s["by_change"]["amending"] == {"new_amending_act": 1, "commencement_changed": 1}
    assert s["by_change"]["subsidiary"] == {"new_instrument": 4}
    assert s["to_crawl"] == 5 and s["recorded_only"] == 4


def test_nothing_changed_means_no_change_and_no_document(world):
    session = FakeSession(pua=[], pub=[])
    adapter, changes, _i, meta = updates.check(world["cfg"], world["baseline"], None, client=_client(session), today=TODAY)
    assert changes.all() == [] and changes.summary()["total"] == 0
    result = X.build_delta(adapter, adapter._client, changes, world["baseline"], SINCE, [6, 7], subsidiary_meta=meta)
    assert result["documents"] == [] and result["meta"]["counts"] == {"all": 0, "seed": 0, "relevant": 0}
    assert not any(url.endswith(".pdf") for _m, url in session.calls)
    assert all(law["not_crawled_reason"] in (None, "", "unchanged since MY_ws_2026-09-01", "the portal offers no document")
               or law["not_crawled_reason"].startswith("its document is also listed")
               for law in result["laws"] if law["listing"] == "updated")


def test_a_listed_file_that_no_run_stored_is_fetched_again_unless_the_engine_logged_it_as_a_duplicate(world, tmp_path):
    import shutil
    run = tmp_path / "MY_ws_2026-09-01"
    shutil.copytree(world["run"], run)
    rows = [json.loads(l) for l in (run / "manifest.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    lost = next(r for r in rows if r["law_number_guess"] == "Act 884")          # a fetch that failed
    dup = next(r for r in rows if r["law_number_guess"] == "Act 854")           # bytes stored under another url
    (run / "manifest.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows if r not in (lost, dup)), encoding="utf-8")
    (run / "crawl_log.jsonl").write_text(json.dumps({"url": dup["source_url"], "outcome": "duplicate"}) + "\n", encoding="utf-8")
    baseline = B.load(tmp_path)
    assert dup["source_url"] in baseline.duplicates and lost["source_url"] not in baseline.stored
    session = FakeSession(pua=[], pub=[])
    adapter, changes, _i, meta = updates.check(world["cfg"], baseline, None, client=_client(session), today=TODAY)
    assert [(c.portal_id, c.change, c.crawl) for c in changes.all()] == [("884", "not_stored", True)]
    result = X.build_delta(adapter, adapter._client, changes, baseline, SINCE, [6, 7], subsidiary_meta=meta)
    assert [d["url"] for d in result["documents"]] == [lost["source_url"]]
    assert result["documents"][0]["contract_meta"]["update"]["change"] == "not_stored"


def test_link_rows_come_from_every_run_so_a_check_only_run_on_top_keeps_the_previous_document(world, tmp_path):
    import shutil
    shutil.copytree(world["run"], tmp_path / "MY_ws_2026-09-01")
    catalogue.write(world["result"], tmp_path / "MY_ws_2026-09-21" / "links_used")     # a check: no manifest
    baseline = B.load(tmp_path)
    assert baseline.state_run.name == "MY_ws_2026-09-21" and baseline.name == "MY_ws_2026-09-21"
    assert baseline.since_date == "2026-09-21"[:0] + baseline.generated_at[:10]
    urls_709 = [u for u, r in baseline.documents.items() if r["contract_meta"].get("portal_id") == "709"
                and r["contract_meta"].get("document_kind") == "principal_act"]
    assert len(urls_709) == 2
    prev = baseline.previous("709", "principal_act")
    assert prev["stored"] and prev["version_as_at"] == "2023-07-01"


def test_a_listing_that_serves_fewer_records_than_it_claims_stops_the_check(world):
    session = FakeSession(short={"json-updated-2024.php": 3}, pua=[], pub=[])
    with pytest.raises(LomUnavailable, match="incomplete listing"):
        updates.check(world["cfg"], world["baseline"], None, client=_client(session), today=TODAY)


def test_an_amending_act_no_longer_listed_is_gone(world):
    session = FakeSession(amendments=[r for r in AMENDMENT_RECORDS if r["ACTNO_LEGISLATION"] != "A1487"], pua=[], pub=[])
    _a, changes, _i, _m = updates.check(world["cfg"], world["baseline"], None, client=_client(session), today=TODAY)
    assert [(c.portal_id, c.change, c.crawl) for c in changes.amendments] == [("A1487", "gone", False)]


def test_since_is_on_or_after_in_date_mode():
    published_on_since = _new_amendment(AMENDMENT_RECORDS[0], "A1900", "9900000", "TEST (AMENDMENT) ACT 2026",
                                        "01/01/2026", "")
    session = FakeSession(amendments=AMENDMENT_RECORDS + [published_on_since], pua=[], pub=[])
    _a, changes, _i, _m = updates.check(_cfg(), None, "2026-01-01", client=_client(session), today=TODAY)
    by_id = {c.portal_id: c for c in changes.amendments}
    assert "A1900" in by_id and by_id["A1900"].note == D.DATE_MODE_NOTE


def test_changes_markdown_keeps_a_pipe_in_a_title_inside_its_cell():
    changes = D.Changes(since=SINCE, mode="baseline", baseline_run="MY_ws_2026-09-01", principals=[
        D.Change("principal", "new_act", "1", "Act 1", "A | B\nC", ["x"], {}, {}, crawl=True)])
    text = X.changes_markdown(changes, [], {})
    assert "| Act 1: A \\| B C | new_act | x | yes |" in text


def test_a_check_needs_a_since_date_and_refuses_to_report_when_lom_is_unreadable(world):
    with pytest.raises(ValueError):
        updates.check(world["cfg"], None, None, client=_client(FakeSession()), today=TODAY)
    cfg = {**world["cfg"], "lom": {**world["cfg"]["lom"], "robots_5xx": "deny"}}
    with pytest.raises(LomUnavailable):
        updates.check(cfg, world["baseline"], SINCE, client=_client(FakeSession()), today=TODAY)


def test_date_mode_without_a_baseline_flags_acts_by_as_at_date_and_says_it_is_approximate():
    session = FakeSession(pua=[], pub=[])
    adapter, changes, _i, _m = updates.check(_cfg(), None, "2026-01-01", client=_client(session), today=TODAY)
    assert changes.mode == "date"
    acts = _by(changes, "new_or_updated")
    assert "884" in acts and "709" not in acts                      # as at 26-06-2026 against 01-07-2023
    assert "date mode" in acts["884"].note and acts["884"].crawl is True
    assert all(c.now["publication_date"] > "2026-01-01" for c in changes.amendments)


# --- 4. the delta list -----------------------------------------------------------------------------------------

def _docs(world) -> dict[str, dict]:
    return {d["url"]: d for d in world["result"]["documents"]}


def test_the_delta_list_holds_exactly_the_documents_to_fetch_seeds_first(world):
    docs = world["result"]["documents"]
    kinds = [(d["law_number_guess"], d["contract_meta"]["document_kind"]) for d in docs]
    assert kinds == [("Act 709", "principal_act"), ("Act A1800", "amending_act"),
                     ("P.U. (A) 400/2026", "subsidiary_legislation"), ("P.U. (B) 400/2026", "commencement_instrument"),
                     ("Act 900", "principal_act")]
    assert [d["order"] for d in docs] == [1, 2, 3, 4, 5]
    assert docs[0]["scopes"] == ["seed", "relevant", "all"] and docs[1]["scopes"] == ["relevant", "all"]
    assert docs[-1]["scopes"] == ["all"]
    assert all(d["contract_meta"]["discovery_path"] == "delta" for d in docs)


def test_every_delta_row_says_what_changed_and_what_the_baseline_stored(world):
    docs = _docs(world)
    row = next(d for d in docs.values() if d["law_number_guess"] == "Act 709")
    up = row["contract_meta"]["update"]
    assert up["change"] == "new_version" and up["reasons"] == ["document", "as-at date"]
    assert up["baseline_run"] == "MY_ws_2026-09-01" and up["since"] == "2026-09-01" and up["found_by"] == "seed"
    assert up["previous"]["version_as_at"] == "2023-07-01" and up["previous"]["stored"] and up["stored_before"] is False
    assert row["contract_meta"]["version_as_at"] == "2026-08-01" and row["law_name_guess"] == SEED_709["law_name"]
    assert row["indicator_hints"] == "P6-I1,P7-I1"
    new_act = next(d for d in docs.values() if d["law_number_guess"] == "Act 900")
    assert new_act["contract_meta"]["update"]["previous"] is None
    order = next(d for d in docs.values() if d["law_number_guess"] == "P.U. (B) 400/2026")
    assert order["contract_meta"]["commences_law_number"] == "Act A1800" and order["law_name_guess"] == "P.U. (B) 400/2026 commencing Act A1800"
    assert order["contract_meta"]["principal_law_number"] == "Act 709"


def test_the_check_fetches_no_document_and_reads_only_the_changed_acts_timelines(world):
    calls = world["now"].calls
    assert not any(url.lower().endswith(".pdf") for _m, url in calls)
    targets = []
    for method, url in calls:
        if "processFile.php" in url:
            t = m.decode_token_target(url) or ""
            targets.append(re.search(r"[?&]act=([^&#]+)", t).group(1))
    assert sorted(set(targets)) == ["709", "A1727", "A1800"]      # Act 900 is not a rule act: no timeline
    meta = world["result"]["meta"]
    assert meta["list_kind"] == "delta" and meta["delta"]["baseline_state_run"] == "MY_ws_2026-09-01"
    assert meta["cfg_sha256"] == catalogue.cfg_fingerprint(world["cfg"]) and meta["subsidiary_listing"]["pua"]["kept"] == 3
    assert meta["requests"] == len(calls)


def test_laws_csv_names_every_act_and_why_it_is_not_fetched(world):
    laws = {(r["listing"], str(r["portal_id"])): r for r in world["result"]["laws"]}
    assert laws[("updated", "884")]["not_crawled_reason"] == "unchanged since MY_ws_2026-09-01"
    assert laws[("updated", "709")]["in_all"] is True and laws[("updated", "900")]["in_all"] is True
    assert laws[("amendment", "A1727")]["not_crawled_reason"].startswith("commencement_changed: nothing new to fetch")
    assert laws[("amendment", "A1800")]["in_all"] is True


def test_the_written_delta_list_replays_through_the_links_file_frontier(world):
    out = world["tmp"] / "MY_ws_2026-09-21"
    paths = catalogue.write(world["result"], out / "links_used")
    files = X.write_changes(out, world["changes"], [], {"since": SINCE})
    assert Path(files["changes.json"]).is_file() and "P.U. (A) 400/2026" in Path(files["changes.md"]).read_text(encoding="utf-8")
    cfg = {**world["cfg"], "lom": {**world["cfg"]["lom"], "frontier": "links_file", "links_file": paths["documents.jsonl"]}}
    adapter = m.MyGazetteAdapter(cfg, client=_client(FakeSession()), today=TODAY)
    cands = adapter.discover(pillars=[6, 7], scope="all")
    assert [c.url for c in cands] == [d["url"] for d in world["result"]["documents"]]
    assert cands[0].contract_meta["update"]["change"] == "new_version"
    assert adapter._client.session.calls == [("GET", LOM + "/robots.txt")]


# --- 5. stored files, verified by conditional HEAD --------------------------------------------------------------

def test_verify_stored_sends_the_validators_and_a_200_becomes_a_refetch(world):
    b = world["baseline"]
    lom_docs = sorted((d for d in b.stored.values() if "lom.agc.gov.my" in d.url and d.url in b.documents),
                      key=lambda d: d.access_date, reverse=True)
    changed_url = lom_docs[0].url                       # the newest stored lom file, so a limit of 3 reaches it
    session = FakeSession(head={changed_url: 200})
    client = _client(session)
    checks = X.verify_stored(client, "lom.agc.gov.my", b, limit=3)
    assert len(checks) == 3 and all(c["sent"]["If-None-Match"].startswith('"e') for c in checks)
    assert all(h.get("If-Modified-Since") for h in session.headers) and all(m_ == "HEAD" for m_, _u in session.calls)
    flagged = [c for c in checks if c["changed"]]
    assert [c["url"] for c in flagged] == [changed_url] and sum(c["unchanged"] for c in checks) == 2
    refetch = [b.documents[c["url"]] for c in flagged]
    now = FakeSession(pua=[], pub=[])
    adapter, changes, _i, meta = updates.check(world["cfg"], b, None, client=_client(now), today=TODAY)
    result = X.build_delta(adapter, adapter._client, changes, b, SINCE, [6, 7], subsidiary_meta=meta, refetch=refetch)
    assert [d["url"] for d in result["documents"]] == [changed_url]
    assert result["documents"][0]["contract_meta"]["update"]["change"] == "stored_file_changed"
    assert X.verify_stored(client, "lom.agc.gov.my", b, limit=0) == []


def test_a_conditional_head_never_follows_a_redirect_and_a_200_with_the_same_validators_is_not_a_change(world):
    b = world["baseline"]
    lom_docs = sorted((d for d in b.stored.values() if "lom.agc.gov.my" in d.url), key=lambda d: d.access_date, reverse=True)
    redirected, same = lom_docs[0], lom_docs[1]
    session = FakeSession(head={redirected.url: 302, same.url: (200, same.etag, same.last_modified)})
    checks = X.verify_stored(_client(session), "lom.agc.gov.my", b, limit=2)
    by_url = {c["url"]: c for c in checks}
    assert by_url[redirected.url]["outcome"] == "redirect" and by_url[redirected.url]["changed"] is False
    assert by_url[same.url]["outcome"] == "same_validators" and by_url[same.url]["changed"] is False
    assert [m_ for m_, _u in session.calls] == ["HEAD", "HEAD"]        # the redirect is not followed, as a GET or otherwise


def test_the_check_reuses_the_act_listings_key_for_the_pu_listings(world):
    calls = world["now"].calls
    assert not any("subsid.php" in url for _m, url in calls)
    # P.U. (A): 4 records at 3 a page, the first page all on or after the floor, so 2 POSTs; P.U. (B): 1
    assert sum(1 for m_, url in calls if m_ == "POST" and url.endswith("json-subsid-2024.php")) == 3


# --- 6. the template contract and the command line --------------------------------------------------------------

def test_find_changes_returns_the_template_shape(world):
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(m.MyGazetteAdapter, "_get_client", _get_client_for(world["now"]))
        out = updates.find_changes(world["cfg"], SINCE, baseline=world["baseline"])
    assert {k for row in out for k in row} >= {"portal_id", "law_name", "version_as_at", "version_id", "change", "url"}
    by_id = {row["portal_id"]: row for row in out}
    assert by_id["900"]["change"] == "new" and by_id["709"]["change"] == "amended"
    assert by_id[world["gone"]["lgt_act_no"].strip()]["change"] == "gone"
    assert by_id["709"]["url"] == LOM + "/principal.php?type=updated" and by_id["709"]["version_as_at"] == "2026-08-01"


def test_the_command_line_writes_the_run_folder_and_prints_the_crawl_command(world, tmp_path, capsys, monkeypatch):
    outputs = tmp_path / "MY"
    outputs.mkdir()
    import shutil
    shutil.copytree(world["run"], outputs / "MY_ws_2026-09-01")
    registry = tmp_path / "sources.yaml"
    registry.write_text(yaml.safe_dump({k: v for k, v in world["cfg"].items() if k != "seed_laws"}), encoding="utf-8")
    seeds = tmp_path / "seed_laws.yaml"
    seeds.write_text(yaml.safe_dump({"seed_laws": world["cfg"]["seed_laws"]}), encoding="utf-8")
    monkeypatch.setattr(m.MyGazetteAdapter, "_get_client", _get_client_for(world["now"]))
    rc = cli_main(["--outputs", str(outputs), "--registry", str(registry), "--seeds", str(seeds),
                   "--out", str(outputs / "MY_ws_2026-09-21")])
    text = capsys.readouterr().out
    assert rc == 0
    run = outputs / "MY_ws_2026-09-21"
    assert (run / "links_used" / "documents.jsonl").is_file() and (run / "changes.json").is_file()
    assert "5 document(s) to crawl" in text and "LOM_FRONTIER=links_file" in text and "--out " + str(run) in text
    rows = [json.loads(l) for l in (run / "links_used" / "documents.jsonl").read_text(encoding="utf-8").splitlines()]
    assert [r["law_number_guess"] for r in rows][:2] == ["Act 709", "Act A1800"]
    changes = json.loads((run / "changes.json").read_text(encoding="utf-8"))
    assert changes["summary"]["to_crawl"] == 5 and changes["baseline_runs"] == ["MY_ws_2026-09-01"]
    with open(run / "links_used" / "laws.csv", encoding="utf-8-sig", newline="") as fh:
        assert any(r["not_crawled_reason"] == "unchanged since MY_ws_2026-09-01" for r in csv.DictReader(fh))


def test_the_command_line_refuses_a_folder_that_already_holds_a_run(world, tmp_path, capsys, monkeypatch):
    outputs = tmp_path / "MY"
    outputs.mkdir()
    import shutil
    shutil.copytree(world["run"], outputs / "MY_ws_2026-09-01")
    registry = tmp_path / "sources.yaml"
    registry.write_text(yaml.safe_dump({k: v for k, v in world["cfg"].items() if k != "seed_laws"}), encoding="utf-8")
    monkeypatch.setattr(m.MyGazetteAdapter, "_get_client", _get_client_for(FakeSession()))
    before = sorted(p.name for p in (outputs / "MY_ws_2026-09-01").rglob("*"))
    rc = cli_main(["--outputs", str(outputs), "--registry", str(registry), "--out", str(outputs / "MY_ws_2026-09-01")])
    assert rc == 2 and "already holds a check or a crawl" in capsys.readouterr().out
    assert sorted(p.name for p in (outputs / "MY_ws_2026-09-01").rglob("*")) == before
    assert not any(p.name.startswith("MY_ws_2026-09-01_") for p in outputs.iterdir())


def test_the_command_line_exits_2_and_writes_nothing_when_lom_cannot_be_read(world, tmp_path, capsys, monkeypatch):
    outputs = tmp_path / "MY"
    outputs.mkdir()
    import shutil
    shutil.copytree(world["run"], outputs / "MY_ws_2026-09-01")
    registry = tmp_path / "sources.yaml"
    cfg = {k: v for k, v in world["cfg"].items() if k != "seed_laws"}
    cfg["lom"] = {**cfg["lom"], "robots_5xx": "deny"}
    registry.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    monkeypatch.setattr(m.MyGazetteAdapter, "_get_client", _get_client_for(FakeSession()))
    rc = cli_main(["--outputs", str(outputs), "--registry", str(registry)])
    assert rc == 2 and "nothing written" in capsys.readouterr().out
    assert [p.name for p in outputs.iterdir()] == ["MY_ws_2026-09-01"]


# --- 7. the link list against the runs (--list) -----------------------------------------------------------------

def _rebuilt_list(world, tmp_path: Path, fingerprint: str | None = None) -> tuple[Path, dict, dict]:
    """The run's own list plus two rows a rebuild with timeline: all would add: an amendment known only from a
    timeline (no run stored it) and a P.U. (A) whose title a run stored from another address."""
    src = world["run"] / "links_used"
    rows = [json.loads(l) for l in (src / "documents.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    meta = json.loads((src / "catalogue_meta.json").read_text(encoding="utf-8"))
    template = copy.deepcopy(next(r for r in rows if r["contract_meta"].get("document_kind") == "amending_act"))
    new = dict(template, url=LOM + "/ilims/upload/portal/akta/outputaktap/9/Act%20A1799.pdf", law_number_guess="Act A1799",
               law_name_guess="TIMELINE-ONLY (AMENDMENT) ACT 2026", order=len(rows) + 1,
               contract_meta={**template["contract_meta"], "portal_id": "A1799", "law_number": "Act A1799",
                              "discovery_path": "amendment_list", "review_flags": ["not_in_amendment_listing"]})
    # a copy on another host (a seed fetched from the agency's site): the same title on lom would be another document
    elsewhere_doc = next(d for d in world["baseline"].stored.values() if d.law_name_guess and "lom.agc.gov.my" not in d.url)
    sub = dict(copy.deepcopy(template), url=LOM + "/ilims/upload/portal/akta/outputp/9/PUA%20222_2024.pdf",
               law_number_guess="P.U. (A) 222/2024", law_name_guess=elsewhere_doc.law_name_guess, order=len(rows) + 2,
               contract_meta={**template["contract_meta"], "portal_id": "P.U. (A) 222/2024",
                              "document_kind": "subsidiary_legislation", "discovery_path": "seed"})
    out = tmp_path / "links"
    out.mkdir()
    (out / "documents.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows + [new, sub]), encoding="utf-8")
    meta = dict(meta, generated_at="2026-09-15T07:21:14Z", cfg_sha256=fingerprint or meta["cfg_sha256"])
    (out / "catalogue_meta.json").write_text(json.dumps(meta), encoding="utf-8")
    return out / "documents.jsonl", new, {"doc": elsewhere_doc, "row": sub}


def test_the_link_list_against_the_runs_yields_the_unstored_rows_and_names_copies_stored_elsewhere(world, tmp_path):
    from p1_scrape.adapters.my_gazette.updates.listcheck import list_vs_runs
    path, new, elsewhere = _rebuilt_list(world, tmp_path)
    to_fetch, changes, summary = list_vs_runs(path, world["cfg"], world["baseline"])
    assert [r["url"] for r in to_fetch] == [new["url"]]
    by = {c.change: c for c in changes}
    assert set(by) == {"not_in_runs", "stored_elsewhere"}
    assert by["not_in_runs"].crawl is True and by["not_in_runs"].url == new["url"] and by["not_in_runs"].portal_id == "A1799"
    assert "built 2026-09-15T07:21:14Z" in by["not_in_runs"].reasons[0]
    assert by["stored_elsewhere"].crawl is False and elsewhere["doc"].url in by["stored_elsewhere"].reasons[0]
    assert by["stored_elsewhere"].before["doc_id"] == elsewhere["doc"].doc_id
    assert summary["not_in_runs"] == 1 and summary["stored_elsewhere"] == 1 and summary["stored"] == summary["rows"] - 2


def test_a_link_list_built_from_another_registry_is_refused_before_any_comparison(world, tmp_path):
    from p1_scrape.adapters.my_gazette.updates.listcheck import list_vs_runs
    path, _new, _e = _rebuilt_list(world, tmp_path, fingerprint="deadbeef" * 8)
    with pytest.raises(ValueError, match="different registry"):
        list_vs_runs(path, world["cfg"], world["baseline"])


def test_the_command_line_with_a_list_fetches_what_no_run_stored_and_reports_it(world, tmp_path, capsys, monkeypatch):
    outputs = tmp_path / "MY"
    outputs.mkdir()
    import shutil
    shutil.copytree(world["run"], outputs / "MY_ws_2026-09-01")
    registry = tmp_path / "sources.yaml"
    registry.write_text(yaml.safe_dump({k: v for k, v in world["cfg"].items() if k != "seed_laws"}), encoding="utf-8")
    seeds = tmp_path / "seed_laws.yaml"
    seeds.write_text(yaml.safe_dump({"seed_laws": world["cfg"]["seed_laws"]}), encoding="utf-8")
    path, new, _e = _rebuilt_list(world, tmp_path)
    monkeypatch.setattr(m.MyGazetteAdapter, "_get_client", _get_client_for(world["now"]))
    run = outputs / "MY_ws_2026-09-22"
    rc = cli_main(["--outputs", str(outputs), "--registry", str(registry), "--seeds", str(seeds),
                   "--out", str(run), "--list", str(path)])
    text = capsys.readouterr().out
    assert rc == 0 and "1 document(s) no run stored -> fetch, 1 stored under another address" in text
    assert "6 document(s) to crawl" in text
    rows = {r["url"]: r for r in (json.loads(l) for l in (run / "links_used" / "documents.jsonl").read_text(encoding="utf-8").splitlines())}
    row = rows[new["url"]]
    assert row["contract_meta"]["update"]["change"] == "not_in_runs" and row["contract_meta"]["discovery_path"] == "delta"
    assert row["contract_meta"]["update"]["found_by"] == "amendment_list" and row["contract_meta"]["update"]["stored_before"] is False
    changes = json.loads((run / "changes.json").read_text(encoding="utf-8"))
    assert changes["summary"]["by_change"]["list"] == {"not_in_runs": 1, "stored_elsewhere": 1}
    assert changes["summary"]["to_crawl"] == 6 and changes["link_list"]["not_in_runs"] == 1
    md = (run / "changes.md").read_text(encoding="utf-8")
    assert "## Link list against the runs (2)" in md and "**1 stored by no run**" in md
    meta = json.loads((run / "links_used" / "catalogue_meta.json").read_text(encoding="utf-8"))
    assert meta["delta"]["link_list"]["rows"] == changes["link_list"]["rows"]


def test_the_command_line_refuses_a_stale_list_without_a_request_or_a_folder(world, tmp_path, capsys, monkeypatch):
    outputs = tmp_path / "MY"
    outputs.mkdir()
    import shutil
    shutil.copytree(world["run"], outputs / "MY_ws_2026-09-01")
    registry = tmp_path / "sources.yaml"
    registry.write_text(yaml.safe_dump({k: v for k, v in world["cfg"].items() if k != "seed_laws"}), encoding="utf-8")
    path, _new, _e = _rebuilt_list(world, tmp_path, fingerprint="deadbeef" * 8)
    session = FakeSession()
    monkeypatch.setattr(m.MyGazetteAdapter, "_get_client", _get_client_for(session))
    rc = cli_main(["--outputs", str(outputs), "--registry", str(registry), "--list", str(path)])
    assert rc == 2 and "different registry" in capsys.readouterr().out
    assert [p.name for p in outputs.iterdir()] == ["MY_ws_2026-09-01"] and session.calls == []


def test_a_check_without_a_list_writes_no_list_section(world):
    md = X.changes_markdown(world["changes"], [], {"generated_at": "2026-09-21"})
    assert "Link list against the runs" not in md
