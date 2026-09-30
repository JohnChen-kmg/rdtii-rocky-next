"""Offline tests for China's collector, updater and layer-1 reader. No test sends a request.

    python -m pytest countries/cn-china/tests -q

Fixtures are real pages saved on 2026-09-21: two State Council Gazette issues (2006 and 2026 markup) and one CAC
listing response.
"""
import csv
import io
import json
import os
import sys
import zipfile

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))


def _dir_holding(marker: str, *candidates: str) -> str:
    """The first candidate that actually contains `marker`.

    China's tools and Malaysia's shared helpers sit in one place in the development
    workshop (countries/cn-china/tools, countries/my-malaysia/scraper) and another in
    the submission repository (src/p1_scrape/adapters/cn_npc, .../my_gazette). This
    suite runs from either, so it looks for the module rather than for a directory
    name — both trees have a `tools/`, but only one of them has China's tools in it.
    """
    for c in candidates:
        if os.path.isfile(os.path.join(c, marker)):
            return c
    return candidates[0]


TOOLS = _dir_holding(
    "checkdocs.py",
    os.path.join(HERE, "..", "tools"),                                       # workshop
    os.path.join(HERE, "..", "src", "p1_scrape", "adapters", "cn_npc"),      # submission
)
_MY = _dir_holding(
    "watchlist.py",                       # Malaysia's shared watch-list helper (CONVENTIONS rule 11)
    os.path.join(HERE, "..", "..", "my-malaysia", "scraper"),                # workshop
    os.path.join(HERE, "..", "src", "p1_scrape", "adapters", "my_gazette"),  # submission
)
FIX = (os.path.join(HERE, "fixtures", "cn")
       if os.path.isdir(os.path.join(HERE, "fixtures", "cn"))
       else os.path.join(HERE, "fixtures"))
sys.path.insert(0, TOOLS)
sys.path.insert(0, _MY)

import checkdocs  # noqa: E402
import collect  # noqa: E402
import layer1  # noqa: E402
import manual_check  # noqa: E402
import polite  # noqa: E402
import update  # noqa: E402
import watchlist  # noqa: E402


def read(name):
    return open(os.path.join(FIX, name), encoding="utf-8", errors="replace").read()


# ---- the polite client: the developer's rule, in code ---------------------------------------------

class FakeNet:
    """Stands in for the network: a table of (url suffix -> (status, body)) and a record of every call."""

    def __init__(self, table):
        self.table, self.calls = table, []

    # set on the class, a callable instance is not bound as a method, so it is not handed the client
    def __call__(self, url, h, data=None, headers=None):
        self.calls.append(url)
        for suffix, answer in self.table.items():
            if url.endswith(suffix):
                return answer if not callable(answer) else answer()
        return 404, b""


@pytest.fixture
def quiet(monkeypatch):
    monkeypatch.setattr(polite.PoliteClient, "_wait", lambda self, h: None)
    monkeypatch.setattr(polite.time, "sleep", lambda s: None)


def client_with(monkeypatch, table):
    net = FakeNet(table)
    monkeypatch.setattr(polite.PoliteClient, "_raw", net)
    return polite.PoliteClient(), net


def test_robots_that_forbids_everyone_refuses_the_host(monkeypatch, quiet):
    c, _ = client_with(monkeypatch, {"/robots.txt": (200, b"User-agent: Baiduspider\nAllow: /\nUser-agent: *\nDisallow: /\n")})
    with pytest.raises(polite.HostRefused):
        c.get("https://www.pbc.gov.cn/tiaofasi/index.html")


def test_a_refused_robots_file_means_permission_cannot_be_established(monkeypatch, quiet):
    c, net = client_with(monkeypatch, {"/robots.txt": (403, b"")})
    with pytest.raises(polite.HostRefused):
        c.get("https://www.miit.gov.cn/zwgk/index.html")
    assert net.calls == ["https://www.miit.gov.cn/robots.txt"], "nothing is fetched after a refused robots file"


def test_no_robots_file_permits(monkeypatch, quiet):
    c, _ = client_with(monkeypatch, {"/robots.txt": (404, b""), "/doc.html": (200, b"ok")})
    assert c.get("https://www.samr.gov.cn/doc.html").ok


def test_a_disallowed_path_is_refused_and_an_allowed_one_is_not(monkeypatch, quiet):
    rules = b"User-agent: *\nDisallow: /wxzf/\n"
    c, _ = client_with(monkeypatch, {"/robots.txt": (200, rules), "/wxzw/a.htm": (200, b"ok")})
    assert c.get("https://www.cac.gov.cn/wxzw/a.htm").ok
    with pytest.raises(polite.HostRefused):
        c.get("https://www.cac.gov.cn/wxzf/b.htm")


def test_a_403_on_a_document_is_never_retried(monkeypatch, quiet):
    c, net = client_with(monkeypatch, {"/robots.txt": (404, b""), "/doc.html": (403, b"")})
    r = c.get("https://www.example.gov.cn/doc.html")
    assert r.status == 403
    assert net.calls.count("https://www.example.gov.cn/doc.html") == 1


def test_a_429_rests_slows_down_and_tries_again(monkeypatch, quiet):
    answers = iter([(429, b""), (200, b"ok")])
    c, net = client_with(monkeypatch, {"/robots.txt": (404, b""), "/doc.html": lambda: next(answers)})
    r = c.get("https://www.example.gov.cn/doc.html")
    assert r.ok
    assert c.hosts["https://www.example.gov.cn"].scale > 1, "the delay widens after a refusal"


def test_the_user_agent_is_honest_and_fixed():
    assert "RDTII" in polite.USER_AGENT and "Mozilla" not in polite.USER_AGENT


# ---- the gazette parser, across twenty years of markup ------------------------------------------------

@pytest.mark.parametrize("text,expected", [
    ("第五十六号", (None, 56)), ("第八十二号", (None, 82)), ("第一百五十一号", (None, 151)), ("第十号", (None, 10)),
    ("第82号", (None, 82)), ("2024年第23号", (2024, 23)), ("〔2025〕第2号", (2025, 2)), ("第845号", (None, 845)),
])
def test_order_numbers_in_both_numeral_systems(text, expected):
    assert collect.cn_number(text) == expected


def test_gazette_2006_issue_parses_orders_with_chinese_numerals():
    rows = collect.parse_gazette_issue(read("gazette_2006_issue35_2026-09-21.html"),
                                       "https://www.gov.cn/gongbao/2006/issue_1069/", "2006年", "第35号")
    orders = [r for r in rows if r["kind"] == "order"]
    assert len(orders) >= 10
    aml = next(r for r in orders if "反洗钱法" in r["title"])
    assert aml["issuer"] == "主席" and aml["order_num"] == 56
    assert aml["url"].startswith("https://www.gov.cn/gongbao/content/2006/")


def test_gazette_2026_issue_parses_ministry_orders():
    rows = collect.parse_gazette_issue(read("gazette_2026_issue26_2026-09-21.html"),
                                       "https://www.gov.cn/gongbao/2026/issue_12986/", "2026年", "第26号")
    mps = next(r for r in rows if r["kind"] == "order" and r["issuer"] == "公安部")
    assert mps["order_num"] == 175 and mps["title"] == "公安机关人民警察证使用管理规定"
    assert not any(r["raw"].endswith("网站") for r in rows), "footer links are not entries"


# ---- sources, links and folders ---------------------------------------------------------------------

def test_verified_links_take_every_link_in_a_row_not_only_the_first():
    urls = [r["url"] for r in collect.verified_links("oscca")]
    assert any("2022-07/14" in u for u in urls) and any("2025-03/27" in u for u in urls), \
        "the second and third certification batches must not be dropped"


def test_manual_hosts_are_never_assigned_to_an_automatic_folder():
    for host in ("www.miit.gov.cn", "www.pbc.gov.cn", "flk.npc.gov.cn", "www.ndrc.gov.cn", "sousuo.www.gov.cn"):
        assert host not in collect.AUTO_HOSTS


def test_a_deferred_source_is_found_where_it_now_lives():
    assert "_deferred" in collect.folder_dir("samr")
    assert "_deferred" not in collect.folder_dir("cac")


def test_the_cac_listing_response_shape_the_collector_reads():
    d = json.loads(read("cac_jsonlist_bmgz_p2_2026-09-21.json"))
    assert int(d["totalRec"]) == 38 and d["list"][0]["infourl"].startswith("//www.cac.gov.cn/")


# ---- layer 1 ----------------------------------------------------------------------------------------

@pytest.mark.parametrize("title,kind", [
    ("中华人民共和国网络安全法", "law"), ("互联网信息服务管理办法", "administrative regulation"),
    ("中华人民共和国电信条例", "administrative regulation"), ("中华人民共和国刑法修正案（三）", "law amendment"),
])
def test_a_title_ending_in_banfa_is_a_regulation_not_a_law(title, kind):
    assert layer1.kind_of(title) == kind


def _zip(path, names):
    with zipfile.ZipFile(path, "w") as z:
        for n in names:
            z.writestr(n, b"x")


def test_layer1_reads_an_export_and_finds_an_amendment_by_its_date(tmp_path):
    old, new = tmp_path / "old", tmp_path / "new"
    old.mkdir(), new.mkdir()
    _zip(old / "a.zip", ["中华人民共和国消防法_20210429.docx", "中华人民共和国国徽法_20201017.docx"])
    _zip(new / "a.zip", ["中华人民共和国消防法_20260101.docx", "一部新法_20260922.docx"])
    d = layer1.diff(layer1.index(str(old)), layer1.index(str(new)))
    assert [r["title"] for r in d["amended"]] == ["中华人民共和国消防法"]
    assert [r["title"] for r in d["added"]] == ["一部新法"]
    assert [r["title"] for r in d["removed"]] == ["中华人民共和国国徽法"]


def test_the_real_export_indexes_completely():
    raw = os.path.join(collect.REPO, "outputs", "CN", "CN_sources_2026-09-21", "manual", "npc-database", "raw")
    if not os.path.isdir(raw):
        pytest.skip("the export is not on this machine; it is kept out of git")
    rows = layer1.index(raw)
    assert len(rows) == 945 and all(r["version_date"] for r in rows)


# ---- the updater ------------------------------------------------------------------------------------

def test_listing_diff_sorts_new_gone_and_retitled():
    d = update.diff_listing([{"url": "u1", "title": "甲"}, {"url": "u2", "title": "乙"}],
                            [{"url": "u2", "title": "乙（修订）"}, {"url": "u3", "title": "丙"}])
    assert [r["title"] for r in d["new"]] == ["丙"]
    assert [r["title"] for r in d["gone"]] == ["甲"]
    assert d["retitled"] == [{"url": "u2", "was": "乙", "now": "乙（修订）"}]


def test_a_text_change_in_whitespace_alone_is_not_a_change():
    assert update._sha("第一条  内容\n") == update._sha("第一条内容")
    assert update._sha("第一条内容") != update._sha("第一条内容已修改")


# ---- the watch list ---------------------------------------------------------------------------------

def test_the_watch_list_is_well_formed():
    path = os.path.join(TOOLS, "watchlist.tsv")
    rows = list(csv.DictReader(open(path, encoding="utf-8"), delimiter="\t", restval=""))
    assert rows and len({len(r) for r in rows}) == 1
    assert {r["breadth"] for r in rows} <= {"multiple", "single", "unconfirmed", "n/a"}
    assert all(r["url"].startswith("http") for r in rows)


def test_the_reminder_never_raises_whatever_the_console():
    buf = io.TextIOWrapper(io.BytesIO(), encoding="ascii")
    watchlist.remind(os.path.join(TOOLS, "watchlist.tsv"), "CN", "test", out=buf)
    watchlist.remind("no/such/file.tsv", "CN", "test", out=io.StringIO())


def test_an_indicator_lookup_separates_dedicated_sources_from_general_indexes():
    assert watchlist._match({"indicators": "12.4.2"}, "12.4.2") == "dedicated"
    assert watchlist._match({"indicators": "12.4.x"}, "12.4.5") == "dedicated"
    assert watchlist._match({"indicators": "all"}, "5.3") == "general"
    assert watchlist._match({"indicators": "7.3"}, "5.3") is None


# ---- rule 12: a hand-collected document must still be machine-readable ----------------------------

def _pdf(body, fonts=True, producer=b""):
    """The smallest thing that parses as a PDF, with a content stream and optionally a font."""
    font = b"/Font << /F1 5 0 R >>" if fonts else b""
    return (b"%PDF-1.4\n" + producer + b"1 0 obj << /Type /Page /Resources << " + font +
            b" >> >> endobj\nstream\n" + body + b"\nendstream\n%%EOF")


def test_a_pdf_that_shows_text_is_readable(tmp_path):
    f = tmp_path / "law.pdf"
    f.write_bytes(_pdf(b"BT /F1 12 Tf (the law) Tj ET"))
    assert checkdocs.check_file(f).verdict == checkdocs.READABLE


def test_a_pdf_of_outlines_has_no_text_layer(tmp_path):
    """What 'Microsoft Print to PDF' makes of a Chinese page: curves, no fonts, no text."""
    f = tmp_path / "outlined.pdf"
    f.write_bytes(_pdf(b"0 0 10 10 re f " * 50, fonts=False))
    r = checkdocs.check_file(f)
    assert r.verdict == checkdocs.NO_TEXT
    assert "path operators" in r.detail


def test_the_printer_is_named_when_it_is_the_cause(tmp_path):
    f = tmp_path / "printed.pdf"
    f.write_bytes(_pdf(b"0 0 10 10 re f", fonts=False, producer=b"/Producer (Microsoft: Print To PDF)\n"))
    assert "Microsoft Print to PDF" in checkdocs.check_file(f).detail


def test_a_compressed_content_stream_is_inflated_before_judging(tmp_path):
    """Page content is normally compressed, so the text operators are invisible in the raw bytes."""
    import zlib
    f = tmp_path / "compressed.pdf"
    f.write_bytes(_pdf(zlib.compress(b"BT /F1 12 Tf (the law) Tj ET")))
    assert checkdocs.check_file(f).verdict == checkdocs.READABLE


def test_an_empty_file_is_a_finding(tmp_path):
    f = tmp_path / "empty.pdf"
    f.write_bytes(b"")
    assert checkdocs.check_file(f).verdict == checkdocs.NO_TEXT


def test_a_word_binary_is_readable_and_its_chinese_is_counted(tmp_path):
    """MIIT's attachments are WPS-written .doc files, which store their text as UTF-16."""
    f = tmp_path / "attachment.doc"
    f.write_bytes(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + "无线电频率划分规定".encode("utf-16-le"))
    r = checkdocs.check_file(f)
    assert r.verdict == checkdocs.READABLE and "9 CJK" in r.detail


def test_saved_markup_is_readable(tmp_path):
    f = tmp_path / "page.mhtml"
    f.write_text("<html><body><p>电信业务经营许可管理办法</p></body></html>", encoding="utf-8")
    assert checkdocs.check_file(f).verdict == checkdocs.READABLE


def test_an_unknown_format_is_reported_but_does_not_fail_the_check(tmp_path):
    (tmp_path / "notes.zip").write_bytes(b"PK\x03\x04rubbish")
    (tmp_path / "law.pdf").write_bytes(_pdf(b"BT /F1 12 Tf (x) Tj ET"))
    assert checkdocs.report(checkdocs.check_folder(tmp_path)) == 0


def test_the_check_exits_non_zero_when_a_file_cannot_be_read(tmp_path, capsys):
    (tmp_path / "outlined.pdf").write_bytes(_pdf(b"0 0 1 1 re f", fonts=False))
    assert checkdocs.main([str(tmp_path)]) == 1
    assert "no text layer" in capsys.readouterr().out


def test_a_folder_of_readable_files_exits_zero(tmp_path):
    (tmp_path / "law.pdf").write_bytes(_pdf(b"BT /F1 12 Tf (the law) Tj ET"))
    assert checkdocs.main([str(tmp_path), "--quiet"]) == 0


# ---- rule 13: the worklist for the sources no tool can read ---------------------------------------

def _collection(tmp_path, monkeypatch, rows, source="miit", parent="manual"):
    """A collection folder with one hand-collected source, and manual_check pointed at it."""
    d = tmp_path / "outputs" / "CN" / "CN_sources_test" / parent / source
    d.mkdir(parents=True)
    head = ["n", "title", "reference", "stated_in_force", "url", "also_at", "file_saved_as",
            "fetched_on", "version_date_on_document", "notes"]
    lines = ["\t".join(head)] + ["\t".join(r) for r in rows]
    (d / "provenance.tsv").write_text("﻿" + "\r\n".join(lines) + "\r\n", encoding="utf-8")
    monkeypatch.setattr(manual_check, "REPO", str(tmp_path))
    return d


def _row(n, title, url="https://example.gov.cn/a.html", saved="a.pdf", version="2020-01-01"):
    return [n, title, "令第42号", "", url, "", saved, "2026-09-22", version, ""]


def test_a_document_with_a_file_is_held_and_one_without_is_still_to_get(tmp_path, monkeypatch):
    _collection(tmp_path, monkeypatch, [_row("1", "held"), _row("2", "wanted", saved="")])
    rows = manual_check.read_provenance(str(tmp_path / "outputs/CN/CN_sources_test/manual/miit"))
    assert [r["title"] for r in manual_check.held(rows)] == ["held"]
    assert [r["title"] for r in manual_check.outstanding(rows)] == ["wanted"]


def test_a_document_read_and_declined_is_neither_held_nor_outstanding(tmp_path, monkeypatch):
    """'not taken' records a judgement, so the row must not come back as work to do."""
    _collection(tmp_path, monkeypatch, [_row("1", "thin notice", saved="not taken")])
    rows = manual_check.read_provenance(str(tmp_path / "outputs/CN/CN_sources_test/manual/miit"))
    assert manual_check.held(rows) == [] and manual_check.outstanding(rows) == []


def test_the_worklist_gives_the_address_of_every_document_held(tmp_path, monkeypatch):
    """The point of the file: a person can open each document without searching for it."""
    _collection(tmp_path, monkeypatch, [_row("1", "one", url="https://www.miit.gov.cn/one.html"),
                                        _row("2", "two", url="https://www.miit.gov.cn/two.html")])
    text = manual_check.build("CN_sources_test", today="2026-09-22")
    assert "https://www.miit.gov.cn/one.html" in text and "https://www.miit.gov.cn/two.html" in text
    assert "Documents held — 2" in text


def test_a_held_document_with_no_address_is_called_out(tmp_path, monkeypatch):
    _collection(tmp_path, monkeypatch, [_row("1", "no address", url="")])
    text = manual_check.build("CN_sources_test", today="2026-09-22")
    assert "no address on the sheet" in text and "**no address recorded**" in text


def test_a_source_with_no_index_page_on_the_watch_list_says_so(tmp_path, monkeypatch):
    """Without an index to compare against, the check has nothing to find new documents with."""
    _collection(tmp_path, monkeypatch, [_row("1", "one")], source="unlisted")
    monkeypatch.setattr(manual_check, "WATCHLIST", str(tmp_path / "none.tsv"))
    assert "No index page on the watch list" in manual_check.build("CN_sources_test", today="2026-09-22")


def test_a_deferred_source_is_included_and_marked(tmp_path, monkeypatch):
    _collection(tmp_path, monkeypatch, [_row("1", "one")], source="ndrc", parent="_deferred/manual")
    text = manual_check.build("CN_sources_test", today="2026-09-22")
    assert "## ndrc" in text and "deferred" in text


def test_a_short_row_does_not_raise(tmp_path, monkeypatch):
    """Sheets are edited by hand; a row missing its trailing columns must not break the worklist."""
    d = _collection(tmp_path, monkeypatch, [_row("1", "one")])
    with open(d / "provenance.tsv", "a", encoding="utf-8", newline="") as f:
        f.write("2\tshort row\r\n")
    assert "short row" in manual_check.build("CN_sources_test", today="2026-09-22")


def test_a_pipe_in_a_title_cannot_break_the_table():
    assert "|" not in manual_check._cell("a | b")
    assert manual_check._cell("") == "—"


def test_the_worklist_counts_the_documents_no_tool_can_check(tmp_path, monkeypatch):
    _collection(tmp_path, monkeypatch, [_row("1", "one"), _row("2", "two"), _row("3", "three", saved="")])
    text = manual_check.build("CN_sources_test", today="2026-09-22")
    assert "holding 2 documents" in text and "an update check of China is not complete" in text
