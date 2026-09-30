"""Timor-Leste: the category-page parser, the catalogue step and the law table, all offline.

The fixtures are two category pages saved from `www.mj.gov.tl` on 2026-09-20 and the portal's robots.txt
(`tests/README.md` lists each with its address). No test sends a request.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import p1_scrape.adapters.tl_jornal as m
from p1_scrape.adapters.my_gazette.client import LomClient as PacedClient
from p1_scrape.adapters.my_gazette.relevance import TitleRule
from p1_scrape.adapters.tl_jornal import catalogue, checker
from p1_scrape.adapters.tl_jornal.parse import CATEGORIES, act_number, amended_number, fold, iso_date, parse_category

FIX = Path(__file__).parent / "fixtures" / "tl"
ROOT = "https://www.mj.gov.tl"
PAGES = {
    "/jornal/?q=node/12": "tl_jornal_leis_2026-09-20.html",
    "/jornal/?q=node/18": "tl_jornal_decretos_governo_2026-09-20.html",
    "/robots.txt": "tl_jornal_robots_2026-09-20.txt",
}


def _read(name: str) -> str:
    return (FIX / name).read_text(encoding="utf-8")


class FakeResp:
    def __init__(self, status: int, content: bytes):
        self.status_code, self.content = status, content
        self.headers, self.text = {}, content.decode("utf-8", "replace")
        self.url = ""


class FakeSession:
    """The portal: the two saved category pages and robots.txt; anything else is a 404."""

    def __init__(self, missing=()):
        self.calls: list[tuple[str, str]] = []
        self.missing = set(missing)

    def request(self, method, url, data=None, headers=None, timeout=None, allow_redirects=True):
        self.calls.append((method, url))
        path = url[len(ROOT):]
        if path in self.missing:
            return FakeResp(500, b"error")
        if path in PAGES:
            return FakeResp(200, (FIX / PAGES[path]).read_bytes())
        return FakeResp(404, b"")


def _client(session: FakeSession) -> PacedClient:
    return PacedClient("test-agent RDTII-Rocky-Crawler/0.1", 10.0, session=session, sleep=lambda s: None,
                       clock=lambda: 0.0, jitter=False, now_iso=lambda: "2026-09-20T05:00:00Z")


SEEDS = [
    {"law_name": "Lei da Concorrência", "law_number": "1/2026", "portal_key": "leis:1/2026", "indicators": [],
     "provenance": "the newest principal law on the portal"},
    {"law_name": "Lei de Proteção ao Consumidor", "law_number": "8/2016", "portal_key": "leis:8/2016",
     "indicators": ["P6-I4"], "provenance": "consumer protection"},
    {"law_name": "Regulamenta a prestação de serviços de telecomunicações na rede móvel", "law_number": "9/2008",
     "portal_key": "decretos_governo:9/2008", "indicators": ["P6-I3", "P7-I3"], "provenance": "mobile services"},
]

TITLE_RULE = {
    "id": "tl-test",
    "groups": [
        {"id": "G3_comunicacoes", "tier": "core", "indicators": ["6.3", "7.3"],
         "patterns": [r"\bTELECOMUNICAC", r"\bCOMUNICACOES\b"]},
        {"id": "G4_eletronico", "tier": "core", "indicators": ["6.2"],
         "patterns": [r"\bELE(C)?TRONIC", r"\bDIGITAL\b"]},
        {"id": "S4_consumidor", "tier": "sectoral", "indicators": ["6.4"], "patterns": [r"\bCONSUMIDOR"]},
    ],
    "exclusions": [{"id": "X1_condecoracoes", "pattern": r"^(CONDECORA|NOMEACAO)"}],
}


def _cfg(**jornal) -> dict:
    return {"economy": "TL", "portals": {"primary_statutes": {"root": ROOT}},
            "jornal": {"categories": "leis,decretos_governo", **jornal},
            "title_rule": TITLE_RULE, "seed_laws": SEEDS,
            "seed_queries": {"P7-I1": ["protecao de dados pessoais"]}}


@pytest.fixture(autouse=True)
def _no_env(monkeypatch):
    for name in list(__import__("os").environ):
        if name.startswith("JORNAL_"):
            monkeypatch.delenv(name)


# --- 1. the parser ------------------------------------------------------------------------------------------

def test_a_number_is_read_however_the_portal_writes_it():
    assert act_number("N.º 1/2026") == "1/2026"
    assert act_number("N.o 12 /2024") == "12/2024"
    assert act_number("N. o 72 / 2023") == "72/2023"
    assert act_number("No12/2019") == "12/2019"
    assert act_number("N0 16/2017") == "16/2017"
    assert act_number("4/2017") == "4/2017"
    assert act_number("No. 08/2016") == "8/2016"            # the leading zero is decoration
    assert act_number("sem número") is None


def test_dates_are_day_first_and_impossible_ones_are_refused():
    assert iso_date("25/3/2026") == "2026-03-25"
    assert iso_date("1/04/2026") == "2026-04-01"
    assert iso_date("08/07/2016") == "2016-07-08"
    assert iso_date("32/13/2026") is None
    assert iso_date("") is None


def test_folding_settles_the_accents_but_not_the_1990_spelling_reform():
    """`fold()` removes accents and case. It cannot remove the extra consonant the older spelling carries, so
    the title rule writes both out — which is why the registry says PROTEC(C)?AO and ELE(C)?TRONIC."""
    assert fold("Proteção de Dados") == "PROTECAO DE DADOS"
    assert fold("PROTECÇÃO DE DADOS") == "PROTECCAO DE DADOS"      # one c more, and that is the point
    assert fold("Comércio Eletrónico") == "COMERCIO ELETRONICO"
    assert fold("Comércio Electrónico") == "COMERCIO ELECTRONICO"
    rule = TitleRule.from_cfg(TITLE_RULE)
    for spelling in ("Edição Eletrónica do Jornal", "Edição Electrónica do Jornal"):
        groups, _exclusion = rule.match(fold(spelling))
        assert "G4_eletronico" in groups, spelling


def test_an_amending_title_names_the_act_it_alters():
    assert amended_number("Primeira alteração ao Decreto-Lei n.º 75/2023, de 15 de setembro") == "75/2023"
    assert amended_number("Segunda alteração à Lei n.º 3/2004, de 14 de abril, sobre Partidos Políticos") == "3/2004"
    assert amended_number("Lei da Concorrência") is None


def test_the_laws_page_parses_into_acts_with_number_title_date_and_document():
    rows = parse_category(_read(PAGES["/jornal/?q=node/12"]), "leis")
    assert len(rows) > 250                                   # 320 rows on 2026-09-20, 2002 to 2026
    first = rows[0]
    assert (first.number, first.title) == ("1/2026", "Lei da Concorrência")
    assert first.published_on == "2026-03-25" and first.code == "L-1-2026"
    assert first.document_url.endswith("/public/docs/2026/serie_1/SERIE_I_NO_12.pdf")
    assert first.document_kind == "principal_act"
    assert all(r.category == "leis" for r in rows)
    assert sum(1 for r in rows if r.document_path) > len(rows) * 0.9


def test_one_document_carries_several_acts():
    rows = parse_category(_read(PAGES["/jornal/?q=node/12"]), "leis")
    by_doc: dict[str, list] = {}
    for r in rows:
        if r.document_url:
            by_doc.setdefault(r.document_url, []).append(r)
    shared = [acts for acts in by_doc.values() if len(acts) > 1]
    assert shared, "the portal lists several laws against one gazette issue"
    assert len(by_doc) < len(rows)                            # so documents are fewer than acts


def test_an_amendment_is_a_different_document_kind_from_a_principal_act():
    rows = parse_category(_read(PAGES["/jornal/?q=node/12"]), "leis")
    amending = [r for r in rows if r.amends]
    assert amending and all(r.document_kind == "amending_act" for r in amending)
    assert any(r.amends == "3/2004" for r in amending)


def test_a_government_decree_is_subsidiary_legislation():
    rows = parse_category(_read(PAGES["/jornal/?q=node/18"]), "decretos_governo")
    assert rows and all(r.document_kind in ("subsidiary_legislation", "amending_act") for r in rows)
    assert CATEGORIES["decretos_governo"]["label"] == "Decreto do Governo"


# --- 2. the catalogue step ----------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def built():
    session = FakeSession()
    adapter = m.TlJornalAdapter(_cfg(), client=_client(session), today="2026-09-20")
    result = catalogue.build(adapter, [6, 7])
    return {"adapter": adapter, "result": result, "session": session}


def test_the_build_reads_robots_then_one_page_per_category_and_nothing_else(built):
    calls = [u[len(ROOT):] for _m, u in built["session"].calls]
    assert calls == ["/robots.txt", "/jornal/?q=node/12", "/jornal/?q=node/18"]
    assert built["adapter"].robots_record["crawl_delay"] == 10.0
    assert built["adapter"]._client.delay == 10.0             # the portal's own delay is adopted


def test_documents_are_issues_and_laws_are_acts(built):
    result = built["result"]
    assert len(result["laws"]) > len(result["documents"])     # several acts share an issue
    meta = result["meta"]
    assert meta["acts_listed"] == len(result["laws"])
    assert meta["documents_distinct"] == len(result["documents"])
    assert meta["settings"]["categories"] == "leis,decretos_governo"     # what the code used, not null
    assert meta["counts"]["all"] == len(result["documents"])


def test_a_document_row_names_every_act_in_the_file(built):
    rows = [d for d in built["result"]["documents"] if len(d["contract_meta"]["contains"]) > 1]
    assert rows, "at least one issue carries more than one act"
    row = rows[0]
    assert "several_acts_in_one_document" in row["contract_meta"]["review_flags"]
    assert len(row["contract_meta"]["contains_titles"]) == min(12, len(row["contract_meta"]["contains"]))
    assert row["contract_meta"]["language"] == "por"
    assert row["contract_meta"]["legal_status"] == "unknown"   # the gazette states none


def test_the_title_rule_selects_on_folded_portuguese(built):
    relevant = {d["contract_meta"]["portal_id"] for d in built["result"]["documents"] if "relevant" in d["scopes"]}
    titles = " | ".join(d["law_name_guess"] for d in built["result"]["documents"] if "relevant" in d["scopes"])
    assert relevant
    low = titles.lower()
    assert any(word in low for word in ("telecomunica", "consumidor", "eletr", "electr", "digital")), low[:200]
    # and an honours decree, which the exclusion drops, is not relevant
    assert "condecora" not in low


def test_a_seed_is_matched_by_its_number_and_carries_its_provenance(built):
    seeded = [d for d in built["result"]["documents"] if d["contract_meta"]["discovery_path"] == "seed"]
    assert seeded, "the seeds name acts the portal lists"
    numbers = {d["contract_meta"]["law_number"] for d in seeded} | {
        c for d in seeded for c in d["contract_meta"]["contains"]}
    assert "L-1-2026" in numbers or "1/2026" in numbers
    assert all(d["contract_meta"]["seed_provenance"] for d in seeded)


def test_a_seed_with_no_indicator_tag_is_kept(built):
    """`Lei da Concorrência` claims no indicator; it is still named on purpose, so it stays in the list."""
    seeds, _others = built["adapter"]._seed_by_number([6, 7])
    assert "leis:1/2026" in seeds


def test_the_list_is_written_with_five_files_and_a_fingerprint(built, tmp_path):
    paths = catalogue.write(built["result"], tmp_path / "links", registry_files=None)
    for name in ("documents.jsonl", "documents.csv", "laws.csv", "catalogue_meta.json", "discovery_log.jsonl"):
        assert Path(paths[name]).is_file()
    meta = json.loads(Path(paths["catalogue_meta.json"]).read_text(encoding="utf-8"))
    assert meta["cfg_sha256"] == catalogue.cfg_fingerprint(built["adapter"].cfg)
    assert meta["economy"] == "TL"
    first = json.loads(Path(paths["documents.jsonl"]).read_text(encoding="utf-8").splitlines()[0])
    assert first["order"] == 1 and first["url"].endswith(".pdf")


def test_a_failed_category_page_stops_the_build():
    session = FakeSession(missing={"/jornal/?q=node/12"})
    adapter = m.TlJornalAdapter(_cfg(), client=_client(session), today="2026-09-20")
    with pytest.raises(m.JornalUnavailable, match="HTTP 500"):
        catalogue.build(adapter, [6, 7])


def test_an_unknown_category_is_refused_before_any_request():
    adapter = m.TlJornalAdapter(_cfg(categories="leis,inventada"), client=_client(FakeSession()))
    with pytest.raises(ValueError, match="inventada"):
        adapter.discover([6, 7], scope="all")


def test_every_document_is_fetched_as_a_native_pdf(built):
    cand = built["result"]["documents"][0]
    from p1_scrape.models import Candidate
    c = Candidate(url=cand["url"], economy="TL", law_name_guess=cand["law_name_guess"])
    plans = built["adapter"].build_plans(c)
    assert len(plans) == 1
    assert (plans[0].method, plans[0].form_factor, plans[0].kind) == ("requests", "pdf", "native")
    assert built["adapter"].build_plans(c, forms="html") == []


# --- 3. the law table ---------------------------------------------------------------------------------------

def test_the_law_table_reads_a_folder_and_states_what_the_portal_does_not(built, tmp_path):
    run = tmp_path / "TL_ws_2026-09-20"
    (run / "links_used").mkdir(parents=True)
    catalogue.write(built["result"], run / "links_used", registry_files=None)
    docs = built["result"]["documents"][:3]
    (run / "manifest.jsonl").write_text("\n".join(json.dumps({
        "doc_id": f"tl-{i}", "source_url": d["url"], "access_date": "2026-09-20T06:00:00Z",
        "local_path": f"raw/tl/{i}.pdf"}) for i, d in enumerate(docs)), encoding="utf-8")

    rows = checker.rows_for(run)
    assert rows, "the acts whose issue this run stored"
    assert {r["in_force"] for r in rows} == {"not stated"}      # never inferred
    assert all(r["run"] == run.name for r in rows)
    assert all(r["scraped"] == "yes" for r in rows)

    every = checker.rows_for(run, include_all=True)
    assert len(every) > len(rows)
    assert any(r["scraped"] == "no" and r["use"] == "not held" for r in every)
    path = checker.write(run, include_all=True)
    assert Path(path).read_text(encoding="utf-8-sig").startswith("law_name,law_number,portal_id")


def test_an_amending_act_is_linkage_and_its_target_says_who_amended_it(built, tmp_path):
    run = tmp_path / "TL_ws_amend"
    (run / "links_used").mkdir(parents=True)
    catalogue.write(built["result"], run / "links_used", registry_files=None)
    (run / "manifest.jsonl").write_text("\n".join(json.dumps({
        "doc_id": f"tl-{i}", "source_url": d["url"], "access_date": "2026-09-20T06:00:00Z",
        "local_path": f"raw/tl/{i}.pdf"}) for i, d in enumerate(built["result"]["documents"])), encoding="utf-8")
    rows = {r["portal_id"]: r for r in checker.rows_for(run, include_all=True)}
    amending = [r for r in rows.values() if r["document_kind"] == "amending_act"]
    assert amending and all(r["use"].startswith("linkage") for r in amending)
    amended = [r for r in rows.values() if r["last_amending_instrument"]]
    assert amended, "an act that a later act alters names its amendment"


def test_a_saved_list_is_replayed_without_reading_the_portal(built, tmp_path):
    """The crawl's own path: `jornal.frontier: links_file`. Until 2026-09-20 this call passed an argument the
    shared helper does not take, and the crawl skipped the whole country with a TypeError."""
    links = tmp_path / "links"
    catalogue.write(built["result"], links, registry_files=None)
    session = FakeSession()
    adapter = m.TlJornalAdapter(_cfg(frontier="links_file", links_file=str(links / "documents.jsonl")),
                                client=_client(session), today="2026-09-20")
    cands = adapter.discover([6, 7], scope="all")
    assert len(cands) == len(built["result"]["documents"])
    assert all(c.url.endswith(".pdf") for c in cands)
    assert [u[len(ROOT):] for _m, u in session.calls] == ["/robots.txt"]      # robots only: no listing is read
    assert "frontier links_file" in adapter.inventory_note

    stale = m.TlJornalAdapter(_cfg(frontier="links_file", links_file=str(links / "documents.jsonl"),
                                   categories="leis"), client=_client(FakeSession()))
    with pytest.raises(ValueError, match="different registry"):
        stale.discover([6, 7], scope="all")


def test_a_link_that_lost_its_host_is_read_as_the_relative_link_it_is():
    """The portal writes `http://public/docs/…` on some rows: the host is missing and the first path segment has
    been read as one. Ten documents were lost to this in the crawl of 2026-09-20."""
    from p1_scrape.adapters.tl_jornal.parse import JORNAL, ListedAct
    row = ListedAct(category="leis", code="L-1-2015", number="1/2015", title="Uma lei",
                    published_on="2015-01-01", document_path="public/docs/2015/serie_1/SERIE_I_NO_28.pdf",
                    document_kind="principal_act")
    assert row.document_url == JORNAL + "public/docs/2015/serie_1/SERIE_I_NO_28.pdf"

    page = ('<table><tr><td>N.º 1/2015</td><td>Uma lei</td><td>1/1/2015</td>'
            '<td><a href="http://public/docs/2015/serie_1/SERIE_I_NO_28.pdf">PT</a></td></tr></table>')
    parsed = parse_category(page, "leis")[0]
    assert parsed.document_path == "public/docs/2015/serie_1/SERIE_I_NO_28.pdf"
    assert parsed.document_url.startswith("https://www.mj.gov.tl/jornal/")

    other = ('<table><tr><td>N.º 2/2015</td><td>Outra lei</td><td>1/1/2015</td>'
             '<td><a href="http://www.jornal.gov.tl/public/docs/2015/serie_1/x.pdf">PT</a></td></tr></table>')
    kept = parse_category(other, "leis")[0]
    assert kept.document_url == "http://www.jornal.gov.tl/public/docs/2015/serie_1/x.pdf"   # stated, not rewritten


def test_the_same_file_listed_under_two_host_spellings_is_one_address():
    """The portal lists an issue as a relative link on one row and as `http://mj.gov.tl/...` on another. Left
    alone, the crawl fetches it twice and the manifest carries two rows with one content hash: 14 such pairs in
    the crawl of 2026-09-20."""
    page = ('<table>'
            '<tr><td>N.º 1/2015</td><td>Orgânica do Ministério da Defesa</td><td>1/1/2015</td>'
            '<td><a href="public/docs/2015/serie_1/SERIE_I_NO_25.pdf">PT</a></td></tr>'
            '<tr><td>N.º 2/2015</td><td>Condecoração na Ordem da Guerrilha</td><td>2/1/2015</td>'
            '<td><a href="http://mj.gov.tl/jornal/public/docs/2015/serie_1/SERIE_I_NO_25.pdf">PT</a></td></tr>'
            '</table>')
    rows = parse_category(page, "leis")
    assert len(rows) == 2
    assert rows[0].document_url == rows[1].document_url, "one file, one address"
    assert rows[0].document_url.startswith("https://www.mj.gov.tl/jornal/public/docs/")
