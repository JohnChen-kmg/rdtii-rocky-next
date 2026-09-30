"""Lao PDR: the listing parser, the catalogue step and the law table, all offline.

The fixtures are seven pages saved from `laoofficialgazette.gov.la` on 2026-09-20 (`tests/README.md` lists each
with its address). No test sends a request.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

import p1_scrape.adapters.la_gazette as m
from p1_scrape.adapters.la_gazette import catalogue, checker
from p1_scrape.adapters.la_gazette.parse import (LEGAL_TYPES, STATUS, document_kind_of, fold, iso_date,
                                                 listing_path, parse_law_page, parse_listing, results_total)
from p1_scrape.adapters.my_gazette.client import LomClient as PacedClient

FIX = Path(__file__).parent / "fixtures" / "la"
ROOT = "https://laoofficialgazette.gov.la"
PAGES = {
    "/robots.txt": "la_robots_answer_2026-09-20.html",
    "/index.php?r=site/list&legaltype=6&old=0": "la_listing_law_p1_2026-09-20.html",
    # the real pages 10 and 19 of the same listing, served as pages 2 and 3 so a three-page listing exercises
    # the pager. Page 10 is the one that carries the Civil Code, which legaltype 1 also lists.
    "/index.php?r=site/list&legaltype=6&old=0&Document_page=2": "la_listing_law_p10_2026-09-20.html",
    "/index.php?r=site/list&legaltype=6&old=0&Document_page=3": "la_listing_law_p19_2026-09-20.html",
    "/index.php?r=site/list&legaltype=6&old=1": "la_listing_law_old1_p1_2026-09-20.html",
    "/index.php?r=site/list&legaltype=16&old=0": "la_listing_law16_p1_2026-09-20.html",
    "/index.php?r=site/list&legaltype=1&old=0": "la_listing_civilcode_2026-09-20.html",
    "/index.php?r=site/list&legaltype=1&old=1": "la_listing_empty_2026-09-20.html",
    "/index.php?r=site/display&id=2597": "la_display_2597_2026-09-20.html",
}
#: every other listing the fake portal is asked for answers with the real "no data" page
EMPTY = "la_listing_empty_2026-09-20.html"


def _read(name: str) -> str:
    return (FIX / name).read_text(encoding="utf-8")


class FakeResp:
    def __init__(self, status: int, content: bytes):
        self.status_code, self.content = status, content
        self.headers, self.text = {}, content.decode("utf-8", "replace")
        self.url = ""


#: How many rows this double can actually serve for each listing. The fixtures are three real pages of a
#: 182-row listing, so the saved pages state 182 — and the adapter now refuses to finish a listing short of the
#: portal's own count, which is the whole point of that guard. A test portal that promises 182 and serves 22 is
#: an inconsistent portal, not a test: the double rewrites the stated total to what it will really hand over.
SERVES = {"legaltype=6&old=0": 22, "legaltype=6&old=1": 10, "legaltype=1&old=0": 1, "legaltype=16&old=0": 10}
_SUMMARY_TOTAL = re.compile(r"(<div class=\"summary\">.*?\d+\s*-\s*\d+\s+\S+\s+)(\d+)", re.S)


class FakeSession:
    """The portal: the saved pages, and the real empty-listing page for anything else under /index.php."""

    def __init__(self, missing=()):
        self.calls: list[tuple[str, str]] = []
        self.missing = set(missing)

    def request(self, method, url, data=None, headers=None, timeout=None, allow_redirects=True):
        self.calls.append((method, url))
        path = url[len(ROOT):]
        if path in self.missing:
            return FakeResp(500, b"error")
        body = None
        if path in PAGES:
            body = (FIX / PAGES[path]).read_bytes()
        elif path.startswith("/index.php"):
            body = (FIX / EMPTY).read_bytes()
        if body is None:
            return FakeResp(404, b"")
        for key, total in SERVES.items():
            if key in path:
                body = _SUMMARY_TOTAL.sub(lambda m: m.group(1) + str(total),
                                          body.decode("utf-8"), count=1).encode("utf-8")
                break
        return FakeResp(200, body)


def _client(session: FakeSession) -> PacedClient:
    return PacedClient("test-agent RDTII-Rocky-Crawler/0.1", 6.0, session=session, sleep=lambda s: None,
                       clock=lambda: 0.0, jitter=False, now_iso=lambda: "2026-09-20T05:00:00Z")


SEEDS = [
    {"law_name": "ກົດໝາຍ ວ່າດ້ວຍການປົກປ້ອງຂໍ້ມູນເອເລັກໂຕຣນິກ", "portal_key": "1216",
     "indicators": ["P7-I1"], "provenance": "the electronic data protection law"},
    {"law_name": "ກົດໝາຍວ່າດ້ວຍ ຄວາມປອດໄພໄຊເບີ", "portal_key": "2537", "indicators": ["P7-I2"],
     "provenance": "the cyber security law"},
    {"law_name": "ກົດໝາຍວ່າດ້ວຍ ອາກອນລາຍໄດ້ (ສະບັບປັບປຸງ)", "portal_key": "2597", "indicators": [],
     "provenance": "the newest law on the portal, and this country's test fixture"},
]

TITLE_RULE = {
    "id": "la-test",
    "groups": [
        {"id": "G1_khomun", "tier": "core", "indicators": ["7.1"], "patterns": ["ຂໍ້ມູນ", "ຂ່າວສານ"]},
        {"id": "G2_cyber", "tier": "core", "indicators": ["7.2"], "patterns": ["ໄຊເບີ", "ຄອມພິວເຕີ"]},
        {"id": "G4_electronic", "tier": "core", "indicators": ["6.2"], "patterns": ["ເອເລັກ", "ລາຍເຊັນ"]},
    ],
    "exclusions": [{"id": "X1_budget", "pattern": "ງົບປະມານແຫ່ງລັດ"}],
}


def _cfg(**gazette) -> dict:
    return {"economy": "LA", "portals": {"primary_statutes": {"root": ROOT}},
            "gazette": {"legal_types": "6", "superseded": False, **gazette},
            "title_rule": TITLE_RULE, "seed_laws": SEEDS,
            "seed_queries": {"P7-I1": ["ການປົກປ້ອງຂໍ້ມູນສ່ວນບຸກຄົນ"]}}


@pytest.fixture(autouse=True)
def _no_env(monkeypatch):
    for name in list(__import__("os").environ):
        if name.startswith("GAZETTE_"):
            monkeypatch.delenv(name)


# --- 1. the parser ------------------------------------------------------------------------------------------

def test_dates_are_day_first_and_impossible_ones_are_refused():
    assert iso_date("25-06-2025") == "2025-06-25"
    assert iso_date("1-4-2026") == "2026-04-01"
    assert iso_date("32-13-2026") is None
    assert iso_date("") is None


def test_folding_settles_the_two_spellings_the_portal_uses_in_one_listing():
    """Both spellings of the /am/ vowel are in the same table — 21 titles use ຳ, 5 use ◌ໍ + າ — so a pattern
    written one way would miss the other. The ligatures fold too, because Tesseract spells them out."""
    assert fold("ປະຈໍາ") == fold("ປະຈຳ") == "ປະຈຳ"
    assert fold("ດໍາລັດ") == "ດຳລັດ"
    assert fold("ກົດຫມາຍ") == fold("ກົດໝາຍ") == "ກົດໝາຍ"        # the OCR pilot's ຫ+ມ against the portal's ໝ
    assert fold("ຫລວງ") == fold("ຫຼວງ")
    assert fold("  ກົດໝາຍ   ວ່າດ້ວຍ ") == "ກົດໝາຍ ວ່າດ້ວຍ"
    assert fold(None) == ""


def test_the_law_listing_parses_into_rows_with_dates_status_and_two_pdf_columns():
    page = _read(PAGES["/index.php?r=site/list&legaltype=6&old=0"])
    rows = parse_listing(page, 6)
    assert results_total(page) == 182
    assert len(rows) == 10                                   # ten rows a page, always
    first = rows[0]
    assert first.law_id == "2597" and first.code == "LA-2597"
    assert first.title == "ກົດໝາຍວ່າດ້ວຍ ອາກອນລາຍໄດ້ (ສະບັບປັບປຸງ)"
    assert (first.made_on, first.gazetted_on) == ("2025-06-25", "2026-06-19")
    assert first.status_label == "ປັດຈຸບັນ" and first.legal_status == "in_force"
    assert first.agency == "ກະຊວງ ການເງິນ"
    assert first.pdf_lao == "/kcfinder/upload/files/88-25-6-2025_0001.pdf" and first.pdf_english is None
    assert first.url() == ROOT + "/kcfinder/upload/files/88-25-6-2025_0001.pdf"
    assert all(r.pdf_lao for r in rows), "every row read on 2026-09-20 offers the Lao text"


def test_the_english_column_comes_before_the_lao_one_and_a_lone_file_is_the_lao_text():
    """The header reads … ເນື້ອໃນ | PDF ອັງກິດ | PDF ລາວ. Getting the order wrong would file every Lao law as a
    translation. No row was ever seen with an English file and no Lao one."""
    page = ('<table><tr><td>ກົດໝາຍ ກ</td><td>ກະຊວງ</td><td>1-1-2020</td><td>2-2-2020</td><td>ກົດໝາຍ</td>'
            '<td>ປັດຈຸບັນ</td><td><a href="/index.php?r=site/display&amp;id=99">ເບິ່ງ</a></td>'
            '<td><a href="/kcfinder/upload/files/X Eng.pdf"><img/></a></td>'
            '<td><a href="/kcfinder/upload/files/ 12. 1.1.2020.pdf"><img/></a></td></tr></table>')
    row = parse_listing(page, 6)[0]
    assert row.pdf_english == "/kcfinder/upload/files/X Eng.pdf"
    assert row.pdf_lao == "/kcfinder/upload/files/ 12. 1.1.2020.pdf"   # spaces inside the name, as served
    assert row.url("eng").endswith("X Eng.pdf")

    lone = page.replace('<td><a href="/kcfinder/upload/files/X Eng.pdf"><img/></a></td>', "<td></td>")
    assert parse_listing(lone, 6)[0].pdf_lao.endswith(" 12. 1.1.2020.pdf")
    assert parse_listing(lone, 6)[0].pdf_english is None


def test_an_address_is_taken_as_the_page_means_it_not_as_the_markup_spells_it():
    """Four addresses in the list of 2026-09-20 carry `&#039;` for an apostrophe. `_unescape` handled only
    `&amp;`, so the crawl asked for the literal entity — and on this portal a path that does not exist answers
    **HTTP 200 with the site's own HTML**, not 404, so the four came back `failed` at status 200 rather than as
    anything obviously missing (`../NOTES.md` 1.3)."""
    from p1_scrape.adapters.la_gazette.parse import _unescape, text_of
    assert _unescape("/kcfinder/upload/files/Women&#039;s_Union Law.pdf") == \
        "/kcfinder/upload/files/Women's_Union Law.pdf"
    assert _unescape("/x/a&amp;b.pdf") == "/x/a&b.pdf"
    assert _unescape("/kcfinder/upload/files/ 69. 11.12.2024.pdf") == \
        "/kcfinder/upload/files/ 69. 11.12.2024.pdf"          # a space inside the name survives untouched
    assert text_of("<td>Women&#039;s &amp; Co&nbsp;Ltd</td>") == "Women's & Co Ltd"

    page = ('<table><tr><td>ກົດໝາຍ ກ</td><td>ກ</td><td>1-1-2020</td><td>2-2-2020</td><td>ກົດໝາຍ</td>'
            '<td>ປັດຈຸບັນ</td><td><a href="/index.php?r=site/display&amp;id=99">ເບິ່ງ</a></td><td></td>'
            '<td><a href="/kcfinder/upload/files/Women&#039;s_Union Law.pdf"><img/></a></td></tr></table>')
    row = parse_listing(page, 6)[0]
    assert "&#039;" not in row.pdf_lao and row.pdf_lao.endswith("Women's_Union Law.pdf")
    assert row.law_id == "99"


def test_the_superseded_listing_carries_old_versions_and_the_amending_laws():
    """`old=1` is where the amendments live: `ກົດໝາຍ ວ່າດ້ວຍການປັບປຸງບາງມາດຕາຂອງ…` appears in no other
    listing, and CONVENTIONS.md section 1 asks for every amending instrument the portal lists."""
    rows = parse_listing(_read(PAGES["/index.php?r=site/list&legaltype=6&old=1"]), 6, old=1)
    assert rows and all(r.old == 1 for r in rows)
    assert {r.status_label for r in rows} == {"ສະບັບເກົ່າ"}
    assert {r.legal_status for r in rows} == {"repealed"}      # decision 17: superseded reads as repealed
    amending = [r for r in rows if r.document_kind == "amending_act"]
    assert amending, "the superseded listing carries amending laws"
    assert all("ປັບປຸງ" in r.title or "ລົບລ້າງ" in r.title for r in amending)


def test_a_revised_version_is_the_consolidated_text_not_an_amending_act():
    """ສະບັບປັບປຸງ (revised version) and ການປັບປຸງ…ມາດຕາ (the amendment of articles) share a root and mean
    opposite things for `document_kind`. 96 of the 182 laws are revised versions."""
    assert document_kind_of("principal_act", "ກົດໝາຍວ່າດ້ວຍ ທຸລະກຳທາງເອເລັກໂຕຣນິກ (ສະບັບປັບປຸງ)") == "principal_act"
    assert document_kind_of("principal_act", "ກົດໝາຍ ວ່າດ້ວຍການປັບປຸງບາງມາດຕາຂອງກົດໝາຍວ່າດ້ວຍນໍ້າ") == "amending_act"
    assert document_kind_of("subsidiary_legislation", "ດຳລັດ ວ່າດ້ວຍການປັບປຸງມາດຕາ 12") == "amending_act"
    assert document_kind_of("principal_act", "ກົດໝາຍວ່າດ້ວຍ ຄວາມປອດໄພໄຊເບີ") == "principal_act"


def test_a_table_that_is_not_the_listing_shape_yields_no_rows():
    """The portal ships a narrower version of the same table on its own front page — eight columns, no
    ສະຖານະພາບ. Read by fixed index it gave 20 rows whose status was `ເບິ່ງ`, the text of the detail link, and
    whose English file was dropped. A row that is not the listing's shape is not a listing row."""
    front = parse_listing(_read("la_robots_answer_2026-09-20.html"), 6)
    assert front == [], "the front page's table is not a listing"
    # and the nine-column listing is unchanged by the guard
    assert len(parse_listing(_read(PAGES["/index.php?r=site/list&legaltype=6&old=0"]), 6)) == 10


def test_the_two_pdf_columns_are_found_after_the_detail_link_not_at_the_end():
    """Taken relative to the ເນື້ອໃນ cell, so a row with a trailing column keeps its English file."""
    page = ('<table><tr><td>ກົດໝາຍ ກ</td><td>ກ</td><td>1-1-2020</td><td>2-2-2020</td><td>ກົດໝາຍ</td>'
            '<td>ປັດຈຸບັນ</td><td><a href="/index.php?r=site/display&amp;id=7">ເບິ່ງ</a></td>'
            '<td><a href="/kcfinder/upload/files/E.pdf"><img/></a></td>'
            '<td><a href="/kcfinder/upload/files/L.pdf"><img/></a></td></tr></table>')
    row = parse_listing(page, 6)[0]
    assert (row.pdf_english, row.pdf_lao) == ("/kcfinder/upload/files/E.pdf", "/kcfinder/upload/files/L.pdf")


def test_an_empty_listing_is_an_answer_and_not_a_failure():
    """`legaltype=4` (Presidential Decree) prints ບໍ່ມີຂໍ້ມູນ — no data. Reading that as a broken page would
    stop a build over a kind the portal simply has none of."""
    page = _read(EMPTY)
    assert results_total(page) == 0
    assert parse_listing(page, 4) == []
    assert results_total("<html>something else entirely</html>") is None


def test_the_portal_states_a_status_on_every_row_and_the_words_map_to_the_contract():
    rows = parse_listing(_read(PAGES["/index.php?r=site/list&legaltype=6&old=0"]), 6)
    assert all(r.status_label for r in rows)
    assert set(STATUS.values()) <= {"in_force", "repealed", "not_yet_in_force"}
    assert STATUS["ປັດຈຸບັນ"] == "in_force" and STATUS["ສະບັບເກົ່າ"] == "repealed"


def test_a_lao_title_that_the_engine_would_slugify_to_nothing_keeps_its_own_slug():
    """`slugify` strips every Lao character, so the engine's storage folder and doc_id key were `unknown` and
    `law` for a whole country. The adapter names each candidate after the gazette's own record id instead
    (`../NOTES.md` 2.5)."""
    # The adapter must not depend on whether the engine's slugify has been fixed: this holds either way.
    adapter = m.LaGazetteAdapter(_cfg(), client=_client(FakeSession()))
    adapter._open_gazette(adapter._client)
    cand = next(iter(adapter._build_candidates([6, 7], "all").values()))
    assert cand.law_slug.startswith("la-") and len(cand.law_slug) < 20


def test_the_engines_own_slugify_keeps_a_lao_title():
    """Engine hand-back, change 4 in the Lao NOTES 2.5, applied in this repository 2026-09-29.

    It was an xfail for as long as the fix lived only in a sandbox: utils.slugify stripped
    every non-Latin script to the one literal "unknown" and acronym_slug to "law", so all
    1,800 Lao laws would have shared a folder and dedup would have read them as versions
    of a single statute. The marker is gone now that the fix is here, because an xfail with
    strict=False would let a revert pass unnoticed — this is the test that catches one.
    """
    from p1_scrape.utils import acronym_slug, slugify
    title = "ກົດໝາຍວ່າດ້ວຍ ຄວາມປອດໄພໄຊເບີ"
    assert slugify(title) != "unknown" and acronym_slug(title) != "law"
    # and two different Lao titles must not collide
    other = "ກົດໝາຍວ່າດ້ວຍ ການໂທລະຄົມມະນາຄົມ"
    assert slugify(title) != slugify(other)
    assert acronym_slug(title) != acronym_slug(other)


def test_the_law_page_adds_nothing_the_listing_does_not_already_carry():
    """The reason no detail page is read. Compare id=2597's own page with its listing row: the same metadata,
    and one download where the listing offers two columns."""
    page = parse_law_page(_read(PAGES["/index.php?r=site/display&id=2597"]), "2597")
    row = parse_listing(_read(PAGES["/index.php?r=site/list&legaltype=6&old=0"]), 6)[0]
    assert page.title == row.title
    assert page.made_on == row.made_on and page.gazetted_on == row.gazetted_on
    assert page.agency == row.agency and page.kind_label == row.kind_label
    assert page.issued_by == "ສະພາແຫ່ງຊາດ"                      # the one field the listing has no column for
    assert list(page.pdfs) == [row.pdf_lao]


# --- 2. the catalogue step ----------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def built():
    session = FakeSession()
    adapter = m.LaGazetteAdapter(_cfg(legal_types="1,6", superseded=True), client=_client(session),
                                 today="2026-09-20")
    result = catalogue.build(adapter, [6, 7])
    return {"adapter": adapter, "result": result, "session": session}


def test_the_build_reads_robots_first_then_the_listings(built):
    calls = [u[len(ROOT):] for _m, u in built["session"].calls]
    assert calls[0] == "/robots.txt"
    assert all(c.startswith("/index.php?r=site/list") for c in calls[1:])
    assert built["adapter"]._client.delay == 6.0              # nothing on the page changes our own delay


def test_the_catch_all_200_is_not_read_as_a_robots_file(built):
    """The gazette answers HTTP 200 with its own 137 KB page for any unknown path. A client that took that for
    a robots.txt would parse the site's HTML as crawling rules."""
    record = built["adapter"].robots_record
    assert record["status"] == 200 and record["bytes"] > 100_000
    assert "crawl_delay" not in record and "rules" not in record
    assert "nothing is stated and nothing is disallowed" in record["note"]
    assert record["delay_used_s"] == 6.0


def test_a_law_in_two_listings_is_kept_once(built):
    """legaltype 6 carries the Civil Code, and legaltype 1 is the Civil Code's own listing. Without this the
    same law would be fetched twice and counted twice."""
    laws = built["result"]["laws"]
    ids = [law["portal_id"] for law in laws]
    assert len(ids) == len(set(ids)), "no law appears twice in the census"
    code = next(law for law in laws if law["portal_id"] == "LA-1619")
    assert code["legal_type"] == 1, "the specific listing is read first and keeps the law"
    assert 6 in code["also_listed_under"]


def test_documents_are_files_and_laws_are_laws(built):
    result, meta = built["result"], built["result"]["meta"]
    assert meta["laws_listed"] == len(result["laws"])
    assert len(result["documents"]) >= len(result["laws"]), "a law with a translation contributes two files"
    assert meta["languages"]["lao"] == len(result["laws"])
    assert meta["settings"]["legal_types"] == "1,6" and meta["settings"]["superseded"] is True
    assert meta["counts"]["all"] == len(result["documents"])
    assert set(meta["statuses"]) <= {"in_force", "repealed", "not_yet_in_force", "unknown"}


def test_an_english_translation_is_its_own_row_and_never_the_authoritative_text(built):
    rows = [d for d in built["result"]["documents"] if d["contract_meta"]["is_translation"]]
    assert rows, "the Civil Code is one of the 21 laws the gazette also publishes in English"
    row = rows[0]
    assert row["contract_meta"]["language"] == "eng"
    assert "unofficial_translation" in row["contract_meta"]["review_flags"]
    lao = next(d for d in built["result"]["documents"]
               if d["contract_meta"]["portal_id"] == row["contract_meta"]["portal_id"]
               and not d["contract_meta"]["is_translation"])
    assert lao["contract_meta"]["language"] == "lao"
    assert lao["law_slug"] + "-en" == row["law_slug"]


def test_the_title_rule_selects_on_folded_lao(built):
    relevant = [d for d in built["result"]["documents"] if "relevant" in d["scopes"]]
    titles = " | ".join(d["law_name_guess"] for d in relevant)
    assert relevant
    assert any(w in titles for w in ("ໄຊເບີ", "ຂໍ້ມູນ", "ເອເລັກ", "ຂ່າວສານ")), titles[:200]


def test_a_seed_is_matched_by_the_portal_id_and_carries_its_provenance(built):
    seeded = [d for d in built["result"]["documents"] if d["contract_meta"]["discovery_path"] == "seed"]
    assert {d["contract_meta"]["portal_id"] for d in seeded} >= {"LA-2597"}
    assert all(d["contract_meta"]["seed_provenance"] for d in seeded)
    seeds, _others = built["adapter"]._seed_by_id([6, 7])
    assert "2597" in seeds, "a seed with no indicator tag is still named on purpose and is kept"


def test_an_amending_instrument_carries_no_indicator_hints(built):
    """POLICY.md 3.2: an amending act is linkage. A seed's indicator tags must not travel onto one."""
    amending = [d for d in built["result"]["documents"]
                if d["contract_meta"]["document_kind"] == "amending_act"]
    assert amending, "the superseded listing supplied amending laws"
    assert all(d["indicator_hints"] is None and d["pillar_hint"] is None for d in amending)


def test_an_address_with_two_spaces_survives_the_csv(built, tmp_path):
    """The shared `_cell` collapses whitespace so a CSV cell stays on one line, which is right for a title and
    wrong for a URL. 42 of this portal's filenames carry two consecutive spaces, and `laws.csv` wrote them as
    one — so the census disagreed with `documents.jsonl` and the manifest, and the update check of 2026-09-21
    read 42 laws as having moved when nothing had."""
    page = ('<table><tr><td>ກົດໝາຍ ກ</td><td>ກ</td><td>1-1-2020</td><td>2-2-2020</td><td>ກົດໝາຍ</td>'
            '<td>ປັດຈຸບັນ</td><td><a href="/index.php?r=site/display&amp;id=5">ເບິ່ງ</a></td>'
            '<td><a href="/kcfinder/upload/files/law on foreign exchange  (Amended) No 15 - NA.pdf"><img/></a></td>'
            '<td><a href="/kcfinder/upload/files/  two  spaces .pdf"><img/></a></td></tr></table>')
    adapter = m.LaGazetteAdapter(_cfg(), client=_client(FakeSession()))
    adapter.listed = {6: parse_listing(page, 6)}
    docs = [{"url": c.url, "law_name_guess": c.law_name_guess, "order": i, "scopes": ["all"],
             "contract_meta": c.contract_meta}
            for i, c in enumerate(adapter._build_candidates([6, 7], "all").values(), start=1)]
    result = {"documents": docs, "laws": catalogue.law_rows(adapter, docs, set(), {}),
              "meta": {}, "discovery_log": []}
    paths = catalogue.write(result, tmp_path / "links", registry_files=None)
    import csv as _csv
    rows = list(_csv.DictReader(Path(paths["laws.csv"]).open(encoding="utf-8-sig", newline="")))
    assert rows[0]["lao_url"].endswith("/kcfinder/upload/files/  two  spaces .pdf")
    assert "foreign exchange  (Amended)" in rows[0]["english_url"], "two spaces, as the portal serves it"
    # and the census agrees with the document rows, which is what the update check compares
    assert {rows[0]["lao_url"], rows[0]["english_url"]} == {d["url"] for d in docs}
    # a title is still collapsed onto one line
    assert "\n" not in rows[0]["title"]


def test_the_list_is_written_with_five_files_and_a_fingerprint(built, tmp_path):
    paths = catalogue.write(built["result"], tmp_path / "links", registry_files=None)
    for name in ("documents.jsonl", "documents.csv", "laws.csv", "catalogue_meta.json", "discovery_log.jsonl"):
        assert Path(paths[name]).is_file()
    meta = json.loads(Path(paths["catalogue_meta.json"]).read_text(encoding="utf-8"))
    assert meta["cfg_sha256"] == catalogue.cfg_fingerprint(built["adapter"].cfg)
    assert meta["economy"] == "LA"
    first = json.loads(Path(paths["documents.jsonl"]).read_text(encoding="utf-8").splitlines()[0])
    assert first["order"] == 1 and first["url"].endswith(".pdf")
    assert first["expect_scanned"] is True                    # every Lao PDF read so far is an image


def test_a_failed_listing_page_stops_the_build():
    session = FakeSession(missing={"/index.php?r=site/list&legaltype=6&old=0"})
    adapter = m.LaGazetteAdapter(_cfg(), client=_client(session), today="2026-09-20")
    with pytest.raises(m.GazetteUnavailable, match="HTTP 500"):
        catalogue.build(adapter, [6, 7])


def test_a_listing_cut_short_by_the_page_guard_stops_the_build():
    """`max_pages: 60` read 600 of the 657 agreements on 2026-09-20 and only warned. A warning scrolls past and
    57 laws go missing, so the guard now refuses to finish short: nothing is written and the message says which
    listing, how many pages it needed and how many laws would have been lost."""
    adapter = m.LaGazetteAdapter(_cfg(legal_types="6", max_pages=1), client=_client(FakeSession()))
    with pytest.raises(m.GazetteUnavailable, match="max_pages"):
        catalogue.build(adapter, [6, 7])
    # and the whole listing is read when the guard is big enough
    ok = m.LaGazetteAdapter(_cfg(legal_types="6", max_pages=120), client=_client(FakeSession()))
    ok._open_gazette(ok._client)
    assert ok.listing_counts["6"]["records_old0"] > 0


def test_a_deliberate_shallow_read_is_not_treated_as_a_truncation():
    """`updates/query.py` asks for the first N pages on purpose, and the guard above must not fire on it. When
    it did, every `--pages` check aborted on the first listing longer than N*10 — which is nearly all of them —
    printed "the gazette could not be read" and exited 2, so the cheap check advertised in `updates/WORKFLOW.md`
    could not run at all."""
    adapter = m.LaGazetteAdapter(_cfg(legal_types="6", superseded=True), client=_client(FakeSession()))
    adapter._open_gazette(adapter._client, max_pages=1)              # the shallow read: no exception
    assert adapter.listed[6], "a shallow read still returns the rows it did see"
    assert adapter.listing_counts["6"]["pages_read"] == 2            # one page of old=0, one of old=1
    assert any("the first" in n for n in adapter.notes), "and it says how far it got"


def test_the_page_count_recorded_is_the_pages_actually_read():
    """It used to record the loop's counter, which is one more than the pages fetched whenever the guard ends
    the loop — the line that read `600 read in 61 page(s)` had fetched 60."""
    adapter = m.LaGazetteAdapter(_cfg(legal_types="1", superseded=True), client=_client(FakeSession()))
    adapter._open_gazette(adapter._client)
    counts = adapter.listing_counts["1"]
    calls = [u for _m, u in adapter._client.session.calls if "site/list" in u]
    assert counts["pages_read"] == len(calls)


def test_an_unknown_legal_type_is_refused_before_any_request():
    adapter = m.LaGazetteAdapter(_cfg(legal_types="6,77"), client=_client(FakeSession()))
    with pytest.raises(ValueError, match="77"):
        adapter.discover([6, 7], scope="all")


def test_all_leaves_out_the_listing_that_is_contained_in_another():
    """legaltype 16 holds 180 of legaltype 6's 182 laws and nothing else, so `all` does not read it: 18
    requests for no law. Naming it explicitly still reads it."""
    adapter = m.LaGazetteAdapter(_cfg(legal_types="all"), client=_client(FakeSession()))
    assert 16 not in adapter._legal_types()
    assert 6 in adapter._legal_types()
    assert LEGAL_TYPES[16]["subset_of"] == 6
    named = m.LaGazetteAdapter(_cfg(legal_types="16"), client=_client(FakeSession()))
    assert named._legal_types() == [16]


def test_every_document_is_fetched_as_a_scanned_pdf(built):
    from p1_scrape.models import Candidate
    cand = built["result"]["documents"][0]
    c = Candidate(url=cand["url"], economy="LA", law_name_guess=cand["law_name_guess"])
    plans = built["adapter"].build_plans(c)
    assert len(plans) == 1
    assert (plans[0].method, plans[0].form_factor, plans[0].kind) == ("requests", "pdf", "scanned")
    assert built["adapter"].build_plans(c, forms="html") == []


def test_a_saved_list_is_replayed_without_reading_the_portal(built, tmp_path):
    """The crawl's own path: `gazette.frontier: links_file`."""
    links = tmp_path / "links"
    catalogue.write(built["result"], links, registry_files=None)
    session = FakeSession()
    adapter = m.LaGazetteAdapter(_cfg(legal_types="1,6", superseded=True, frontier="links_file",
                                      links_file=str(links / "documents.jsonl")),
                                 client=_client(session), today="2026-09-20")
    cands = adapter.discover([6, 7], scope="all")
    assert len(cands) == len(built["result"]["documents"])
    assert all(c.url.endswith(".pdf") for c in cands)
    assert [u[len(ROOT):] for _m, u in session.calls] == ["/robots.txt"]     # robots only: no listing is read
    assert "frontier links_file" in adapter.inventory_note

    stale = m.LaGazetteAdapter(_cfg(legal_types="6", superseded=True, frontier="links_file",
                                    links_file=str(links / "documents.jsonl")), client=_client(FakeSession()))
    with pytest.raises(ValueError, match="different registry"):
        stale.discover([6, 7], scope="all")


def test_listing_paths_are_built_the_way_the_portal_wants_them():
    assert listing_path(6) == "/index.php?r=site/list&legaltype=6&old=0"
    assert listing_path(6, 2) == "/index.php?r=site/list&legaltype=6&old=0&Document_page=2"
    assert listing_path(6, 1, old=1) == "/index.php?r=site/list&legaltype=6&old=1"


# --- 3. the law table ---------------------------------------------------------------------------------------

def _run_with(result, tmp_path, name, urls=None):
    run = tmp_path / name
    (run / "links_used").mkdir(parents=True)
    catalogue.write(result, run / "links_used", registry_files=None)
    docs = result["documents"] if urls is None else [d for d in result["documents"] if d["url"] in urls]
    (run / "manifest.jsonl").write_text("\n".join(json.dumps({
        "doc_id": f"la-{i}", "source_url": d["url"], "access_date": "2026-09-20T06:00:00Z",
        "local_path": f"raw/la/{i}.pdf"}) for i, d in enumerate(docs)), encoding="utf-8")
    return run


def test_the_law_table_answers_in_force_for_every_row_because_the_portal_states_it(built, tmp_path):
    run = _run_with(built["result"], tmp_path, "LA_ws_2026-09-20")
    rows = checker.rows_for(run)
    assert rows
    assert {r["in_force"] for r in rows} <= {"yes", "no (repealed)"}
    assert "not stated" not in {r["in_force"] for r in rows}, "this portal states a status on every row"
    assert all(r["status_source"] == "portal_listing" for r in rows)
    assert all(r["run"] == run.name and r["scraped"] == "yes" for r in rows)
    assert all(r["law_number"] is None for r in rows), "the listing carries no act number for any law"
    path = checker.write(run)
    assert Path(path).read_text(encoding="utf-8-sig").startswith("law_name,law_number,portal_id")


def test_all_adds_the_laws_this_run_did_not_fetch(built, tmp_path):
    keep = {built["result"]["documents"][0]["url"]}
    run = _run_with(built["result"], tmp_path, "LA_ws_partial", urls=keep)
    held = checker.rows_for(run)
    every = checker.rows_for(run, include_all=True)
    assert len(every) > len(held)
    assert any(r["scraped"] == "no" and r["use"] == "not held" for r in every)


#: the only values decision 20 defines, plus `not held`, which every country's checker writes for a law whose
#: document the folder does not have (`tl-timor-leste/scraper/checker.py`)
USE_VOCABULARY = {"evidence", "evidence, text stale", "linkage", "linkage, text needed", "not held"}


def test_use_stays_inside_the_vocabulary_decision_20_defines(built, tmp_path):
    """Decision 20 fixes four values and `CONVENTIONS.md` section 2 step 7 restates them. This checker used to
    emit `superseded text`, an invention, on every repealed law — 293 of the 1,773 on this portal — and this
    test asserted it, so the suite pinned the invention instead of catching it. A later stage filtering on the
    convention's values has no branch for a word only Laos uses."""
    run = _run_with(built["result"], tmp_path, "LA_ws_use")
    rows = checker.rows_for(run, include_all=True)
    uses = {r["use"] for r in rows}
    assert uses <= USE_VOCABULARY, f"out of vocabulary: {uses - USE_VOCABULARY}"
    assert "evidence" in uses
    for r in rows:
        if r["document_kind"] in ("amending_act", "repealing_act") and r["scraped"] != "no":
            assert r["use"].startswith("linkage")
        # a repealed text is not evidence (POLICY.md 3.6): keep the link, do not read it
        elif r["legal_status"] == "repealed" and r["scraped"] != "no":
            assert r["use"] == "linkage"
    assert all(r["effective_date"] == r["gazetted_on"] for r in rows)


def test_a_text_whose_later_amendment_we_hold_is_marked_stale(tmp_path):
    """Decision 20's `evidence, text stale` marks **both** sides of a stale pair, and `POLICY.md` 3.3 is why it
    exists. It was never emitted: `linkage, text needed` was decided by the amendment's own portal status and
    no date was ever compared, so a 2018 text whose 2025 amendment we hold was handed on as current law."""
    laws = [
        {"portal_id": "LA-1442", "title": "ກົດໝາຍວ່າດ້ວຍ ການປະກັນສັງຄົມ", "document_kind": "principal_act",
         "legal_status": "in_force", "gazetted_on": "2018-12-25", "made_on": "2018-12-20",
         "lao_url": "https://x/principal.pdf", "english_url": ""},
        {"portal_id": "LA-2378", "title": "ລັດຖະບັນຍັດວ່າດ້ວຍ ການປັບປຸງ ມາດຕາ 34 ຂອງກົດໝາຍວ່າດ້ວຍ ການປະກັນສັງຄົມ",
         "document_kind": "amending_act", "legal_status": "in_force", "gazetted_on": "2025-06-09",
         "made_on": "2025-06-09", "lao_url": "https://x/amend.pdf", "english_url": ""},
    ]
    run = tmp_path / "LA_ws_stale"
    (run / "links_used").mkdir(parents=True)
    catalogue._write_csv(run / "links_used" / "laws.csv", catalogue._LAW_COLUMNS,
                         [{k: catalogue._cell(v) for k, v in r.items()} for r in laws])
    (run / "manifest.jsonl").write_text("\n".join(json.dumps(
        {"doc_id": f"la-{i}", "source_url": l["lao_url"], "local_path": f"raw/la/{i}.pdf"})
        for i, l in enumerate(laws)), encoding="utf-8")
    rows = {r["portal_id"]: r for r in checker.rows_for(run, include_all=True)}
    assert rows["LA-1442"]["use"] == "evidence, text stale"
    assert rows["LA-1442"]["last_amended"] == "2025"
    assert rows["LA-2378"]["use"].startswith("linkage")


def test_an_amendment_is_never_attached_to_a_text_younger_than_itself(tmp_path):
    """The join is on the words of a title, so it needs the date test to be safe. Without it the real census
    gave LA-2469, a law made in 2024, a `last_amended` of 2016 from an instrument the portal marks repealed —
    a reader would read that as eight untouched years."""
    laws = [
        {"portal_id": "LA-955", "title": "ກົດໝາຍວ່າດ້ວຍ ສະພາປະຊາຊົນຂັ້ນແຂວງ", "document_kind": "principal_act",
         "legal_status": "repealed", "gazetted_on": "2015-05-01", "made_on": "2015-04-01",
         "lao_url": "https://x/2015.pdf", "english_url": ""},
        {"portal_id": "LA-2469", "title": "ກົດໝາຍວ່າດ້ວຍ ສະພາປະຊາຊົນຂັ້ນແຂວງ", "document_kind": "principal_act",
         "legal_status": "in_force", "gazetted_on": "2024-06-28", "made_on": "2024-06-28",
         "lao_url": "https://x/2024.pdf", "english_url": ""},
        {"portal_id": "LA-1171", "title": "ກົດໝາຍວ່າດ້ວຍ ການປັບປຸງບາງມາດຕາຂອງກົດໝາຍວ່າດ້ວຍ ສະພາປະຊາຊົນຂັ້ນແຂວງ",
         "document_kind": "amending_act", "legal_status": "repealed", "gazetted_on": "2016-11-14",
         "made_on": "2016-11-14", "lao_url": "https://x/amend2016.pdf", "english_url": ""},
    ]
    run = tmp_path / "LA_ws_dates"
    (run / "links_used").mkdir(parents=True)
    catalogue._write_csv(run / "links_used" / "laws.csv", catalogue._LAW_COLUMNS,
                         [{k: catalogue._cell(v) for k, v in r.items()} for r in laws])
    (run / "manifest.jsonl").write_text("", encoding="utf-8")
    rows = {r["portal_id"]: r for r in checker.rows_for(run, include_all=True)}
    assert rows["LA-2469"]["last_amending_instrument"] is None, "a 2016 instrument cannot amend a 2024 text"
    assert rows["LA-955"]["last_amended"] == "2016", "it amends the vintage that preceded it"


def test_a_law_whose_lao_text_failed_is_never_reported_as_holding_it(tmp_path):
    """Falling back to the translation asserted we hold the official text when we hold only the gazette's
    English rendering, and labelled an English file `lao` — `POLICY.md` 3.8 records the language of what was
    actually fetched. 55 of the 1,773 laws carry both addresses, so this was live for the first crawl."""
    laws = [{"portal_id": "LA-2202", "title": "ກົດໝາຍວ່າດ້ວຍ ລະບົບການຊຳລະ", "document_kind": "principal_act",
             "legal_status": "in_force", "gazetted_on": "2024-02-13", "made_on": "2023-11-20",
             "lao_url": "https://x/lao.pdf", "english_url": "https://x/eng.pdf"}]
    run = tmp_path / "LA_ws_engonly"
    (run / "links_used").mkdir(parents=True)
    catalogue._write_csv(run / "links_used" / "laws.csv", catalogue._LAW_COLUMNS,
                         [{k: catalogue._cell(v) for k, v in r.items()} for r in laws])
    (run / "manifest.jsonl").write_text(json.dumps(
        {"doc_id": "la-eng-001", "source_url": "https://x/eng.pdf", "local_path": "raw/la/eng.pdf"}),
        encoding="utf-8")
    row = checker.rows_for(run, include_all=True)[0]
    assert row["scraped"] == "translation only"
    assert row["language"] == "eng"
    assert row["file"] is None, "the Lao file is not held and no English path may stand in for it"
    assert row["translation_doc_id"] == "la-eng-001"
    assert "the Lao text, which is the document of record, was not" in row["notes"]


def test_two_laws_pointing_at_one_file_are_both_flagged_and_neither_is_dropped(tmp_path):
    """A portal defect, found by the link list of 2026-09-20: four pairs of unrelated laws share a generically
    named upload (`001.pdf`, `003.pdf`, `04.pdf`, `scan0001.pdf`). One of them is claimed by a 2023 Presidential
    Ordinance and a 2014 provincial Order, which cannot both be right. Flag, do not fix (decision 17): the file
    is fetched once as served, and both laws keep their row and say so."""
    page = ('<table>'
            '<tr><td>ລັດຖະບັນຍັດ ກ</td><td>ກະຊວງ</td><td>9-10-2023</td><td>2-1-2024</td><td>ລັດຖະບັນຍັດ</td>'
            '<td>ປັດຈຸບັນ</td><td><a href="/index.php?r=site/display&amp;id=2178">ເບິ່ງ</a></td><td></td>'
            '<td><a href="/kcfinder/upload/files/003.pdf"><img/></a></td></tr>'
            '<tr><td>ຄຳສັ່ງ ຂ</td><td>ແຂວງ</td><td>10-2-2014</td><td>20-10-2016</td><td>ຄຳສັ່ງ</td>'
            '<td>ປັດຈຸບັນ</td><td><a href="/index.php?r=site/display&amp;id=1069">ເບິ່ງ</a></td><td></td>'
            '<td><a href="/kcfinder/upload/files/003.pdf"><img/></a></td></tr>'
            '</table>')
    adapter = m.LaGazetteAdapter(_cfg(), client=_client(FakeSession()))
    adapter.listed = {6: parse_listing(page, 6)}
    cands = adapter._build_candidates([6, 7], "all")
    assert len(cands) == 1, "one address, one fetch"
    flags = next(iter(cands.values())).contract_meta["review_flags"]
    assert "shared_file_address" in flags

    # and the law table, which computes it from the census alone, names both laws
    result = {"documents": [{**{k: getattr(c, k) for k in ("url", "law_name_guess")},
                             "order": 1, "scopes": ["all"], "contract_meta": c.contract_meta}
                            for c in cands.values()],
              "laws": catalogue.law_rows(adapter, [], set(), {}), "meta": {}, "discovery_log": []}
    run = tmp_path / "LA_ws_shared"
    (run / "links_used").mkdir(parents=True)
    catalogue._write_csv(run / "links_used" / "laws.csv", catalogue._LAW_COLUMNS,
                         [{k: catalogue._cell(v) for k, v in r.items()} for r in result["laws"]])
    rows = {r["portal_id"]: r for r in checker.rows_for(run, include_all=True)}
    assert len(rows) == 2, "both laws keep their row"
    assert rows["LA-2178"]["shared_file_with"] == ["LA-1069"]
    assert rows["LA-1069"]["shared_file_with"] == ["LA-2178"]
    assert "points at this same file" in rows["LA-2178"]["notes"]


def test_a_translation_is_recorded_beside_its_law_not_as_a_row_of_its_own(built, tmp_path):
    run = _run_with(built["result"], tmp_path, "LA_ws_translation")
    rows = {r["portal_id"]: r for r in checker.rows_for(run, include_all=True)}
    code = rows["LA-1619"]                                     # the Civil Code has both languages
    assert code["has_translation"] == "yes" and code["translation_doc_id"]
    assert code["language"] == "lao", "the row is the Lao text; the translation hangs off it"
    assert len(rows) == len(built["result"]["laws"]), "one row per law, never one per file"
