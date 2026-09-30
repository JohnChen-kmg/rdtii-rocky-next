"""Which portal parser reads a page must not depend on the order parsers were registered.

Before 2026-09-23 `parse_html.parse` tested `if host in source_url` over an insertion-ordered
dict and took the first hit. That is a substring of the whole URL, so `"gov.cn"` matches
`https://www.cac.gov.cn/...`, and China's three portals - cac.gov.cn (112 documents),
miit.gov.cn (16) and www.gov.cn (11) - would have been routed by whichever of the three lines
happened to be typed first. Registering `gov.cn` first sends 139 of 140 pages to the wrong
parser, and a parser that finds no container returns little rather than raising, so most of
that damage is silent.

Matching the host *suffix* alone does not fix it either: `www.cac.gov.cn` genuinely is a
subdomain of `gov.cn`. Only "most specific registered host wins" is order-independent.
"""

from __future__ import annotations

import pytest

from rdtii_p2 import parse_html


@pytest.fixture
def portals(monkeypatch):
    """Register three nested hosts, deliberately worst-order: the parent first."""
    seen: list[str] = []

    def make(name):
        def parser(path):
            seen.append(name)
            return parse_html.HtmlDoc(text=name)
        return parser

    monkeypatch.setattr(parse_html, "PORTAL_PARSERS", {
        "gov.cn": make("govcn"),            # the parent, registered FIRST on purpose
        "cac.gov.cn": make("cac"),
        "miit.gov.cn": make("miit"),
    })
    return seen


@pytest.mark.parametrize("url, expected", [
    ("https://www.cac.gov.cn/2026-09/11/c_1790876575309197.htm", "cac"),
    ("https://www.miit.gov.cn/zwgk/zcwj/wjfb/tg/art/2020/art_e98406cd.html", "miit"),
    ("https://www.gov.cn/zhengce/zhengceku/202510/content_7044914.htm", "govcn"),
    ("https://gov.cn/gongbao/content/2013/content_2473881.htm", "govcn"),
])
def test_the_most_specific_host_wins_whatever_the_order(url, expected, portals, tmp_path):
    page = tmp_path / "p.html"
    page.write_text("<html></html>", encoding="utf-8")
    doc = parse_html.parse(page, url)
    assert doc.text == expected, f"{url} -> {doc.text}, expected {expected}"


def test_the_path_is_not_searched(tmp_path, monkeypatch):
    """A registered host appearing in the PATH must not select that parser."""
    monkeypatch.setattr(parse_html, "PORTAL_PARSERS", {
        "legislation.gov.au": lambda path: parse_html.HtmlDoc(text="au"),
    })
    page = tmp_path / "p.html"
    page.write_text("<html></html>", encoding="utf-8")
    with pytest.raises(NotImplementedError):
        # the old substring test matched this; it is a Chinese host quoting the AU one
        parse_html.parse(page, "https://www.gov.cn/mirror/legislation.gov.au/C2004A/text")


def test_a_lookalike_host_does_not_match(tmp_path, monkeypatch):
    monkeypatch.setattr(parse_html, "PORTAL_PARSERS", {
        "gov.cn": lambda path: parse_html.HtmlDoc(text="govcn"),
    })
    page = tmp_path / "p.html"
    page.write_text("<html></html>", encoding="utf-8")
    for hostile in ("https://notgov.cn/a.htm", "https://gov.cn.example.com/a.htm"):
        with pytest.raises(NotImplementedError):
            parse_html.parse(page, hostile)


def test_australia_still_dispatches(tmp_path):
    """The real registration must keep working - AU is the English regression corpus."""
    assert "legislation.gov.au" in parse_html.PORTAL_PARSERS
    assert parse_html._host_of(
        "https://www.legislation.gov.au/C2004A03712/latest/text") == "www.legislation.gov.au"
    # www. subdomain of the registered host resolves to the AU parser
    host = parse_html._host_of("https://www.legislation.gov.au/x/text")
    assert host.endswith(".legislation.gov.au")


def test_port_and_credentials_are_stripped():
    assert parse_html._host_of("https://user:pw@WWW.Gov.CN:8443/a") == "www.gov.cn"


def test_a_null_source_url_refuses_cleanly(tmp_path):
    """Five China files have no recorded address; urlparse(None) raised a TypeError that
    surfaced as "a bytes-like object is required, not 'str'" and said nothing useful."""
    page = tmp_path / "p.html"
    page.write_text("<html></html>", encoding="utf-8")
    for empty in (None, ""):
        with pytest.raises(NotImplementedError, match="no recorded source_url"):
            parse_html.parse(page, empty)
    assert parse_html._host_of(None) == ""
