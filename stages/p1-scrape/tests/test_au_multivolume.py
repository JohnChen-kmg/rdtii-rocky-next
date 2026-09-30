"""Regression tests for the 2026-07-17 AU multi-volume truncation defect.

The epubFrame view of legislation.gov.au renders ONE epub spine document at a time, so a
frame capture of a multi-volume compilation silently yielded volume 1 only (33 acts,
incl. TIA 1979 — its Part 5-1A data-retention sections live in volume 2). The fix:
multi-volume acts are fetched as the dated epub and ALL spine documents are extracted and
concatenated (verified against the OPF spine); the framed fallback now rejects — fails
loudly — any capture that self-declares multiple volumes. These tests pin both behaviors.
"""
from __future__ import annotations

import io
import re
import zipfile

import pytest

from src.p1_scrape.adapters.au_legislation import _MULTIVOL_DECL, AuLegislationAdapter
from src.p1_scrape.epub import EpubExtractionError, concat_epub_html
from src.p1_scrape.fetcher import _postprocess
from src.p1_scrape.models import Candidate, FetchPlan, FetchResult, HttpMeta


def _make_epub(docs: dict[str, bytes], spine_missing: bool = False) -> bytes:
    """A minimal legislation.gov.au-shaped epub: OEBPS/document_N/document_N.html."""
    items, refs = [], []
    for i, name in enumerate(docs, 1):
        items.append(f'<item id="doc{i}" href="{name}" media-type="application/xhtml+xml"/>')
        refs.append(f'<itemref idref="doc{i}"/>')
    if spine_missing:
        items.append('<item id="ghost" href="document_9/document_9.html" '
                     'media-type="application/xhtml+xml"/>')
        refs.append('<itemref idref="ghost"/>')
    opf = (
        '<?xml version="1.0"?><package xmlns="http://www.idpf.org/2007/opf" version="2.0">'
        f'<manifest>{"".join(items)}</manifest><spine>{"".join(refs)}</spine></package>'
    )
    container = (
        '<?xml version="1.0"?><container xmlns="urn:oasis:names:tc:opendocument:xmlns:container">'
        '<rootfiles><rootfile full-path="OEBPS/document.opf" '
        'media-type="application/oebps-package+xml"/></rootfiles></container>'
    )
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("mimetype", "application/epub+zip")
        z.writestr("META-INF/container.xml", container)
        z.writestr("OEBPS/document.opf", opf)
        for name, body in docs.items():
            z.writestr(f"OEBPS/{name}", body)
    return buf.getvalue()


# --- concat_epub_html: every volume, in spine order, or a loud failure ---------------


def test_epub_concat_includes_every_volume_in_spine_order():
    data = _make_epub({
        "document_1/document_1.html": b"<html>VOLUME-ONE ss 1-186J</html>",
        "document_2/document_2.html": b"<html>VOLUME-TWO 187C data retention</html>",
    })
    out = concat_epub_html(data).decode()
    assert "VOLUME-ONE" in out and "VOLUME-TWO" in out
    assert out.index("VOLUME-ONE") < out.index("VOLUME-TWO")
    # volume boundaries stay visible + machine-checkable in the stored artifact
    assert "p1-epub-spine-doc 1/2" in out and "p1-epub-spine-doc 2/2" in out


def test_epub_concat_fails_loudly_when_a_spine_document_is_missing():
    data = _make_epub({"document_1/document_1.html": b"<html>only vol 1</html>"},
                      spine_missing=True)
    with pytest.raises(EpubExtractionError, match="missing from archive"):
        concat_epub_html(data)


def test_epub_concat_rejects_non_epub_bytes():
    with pytest.raises(EpubExtractionError, match="not a zip"):
        concat_epub_html(b"<html>an error page, not an epub</html>")


# --- fetcher postprocess: unpack + reject guard --------------------------------------


def _result(content: bytes) -> FetchResult:
    return FetchResult(content=content, ok=True,
                       http=HttpMeta(final_url="u", status=200, retrieval_method="requests"))


def test_postprocess_unpacks_epub_plan_to_html():
    plan = FetchPlan(url="https://www.legislation.gov.au/C2004A02124/2026-06-04/2026-06-04/"
                         "text/original/epub", unpack="epub_html", form_factor="html")
    data = _make_epub({"document_1/document_1.html": b"<html>A</html>",
                       "document_2/document_2.html": b"<html>B 187C</html>"})
    out = _postprocess(plan, _result(data))
    assert out.ok and b"187C" in out.content
    assert out.http.content_type == "text/html"


def test_postprocess_fails_loudly_on_partial_epub():
    plan = FetchPlan(url="u", unpack="epub_html", form_factor="html")
    data = _make_epub({"document_1/document_1.html": b"<html>A</html>"}, spine_missing=True)
    out = _postprocess(plan, _result(data))
    assert not out.ok and out.content == b"" and "epub unpack failed" in out.http.error


def test_reject_pattern_fails_framed_capture_of_multivolume_act():
    # The exact self-declaration found in the truncated TIA 1979 capture.
    partial = b"<p><span>This compilation is in 2 volumes</span></p><p>ss 1-186J only</p>"
    plan = FetchPlan(url="https://www.legislation.gov.au/C2004A02124/latest/text",
                     reject_pattern=_MULTIVOL_DECL)
    out = _postprocess(plan, _result(partial))
    assert not out.ok and "reject_pattern" in out.http.error


def test_reject_pattern_passes_single_volume_capture():
    plan = FetchPlan(url="u", reject_pattern=_MULTIVOL_DECL)
    out = _postprocess(plan, _result(b"<html>a complete single-volume act</html>"))
    assert out.ok


# --- adapter plan routing ------------------------------------------------------------


def _adapter() -> AuLegislationAdapter:
    return AuLegislationAdapter(cfg={})


def test_build_plans_epub_url_is_a_requests_unpack_plan_citing_its_dated_address():
    # 2026-09-15 (FX4): the citation is the epub's own version-pinned address, no longer the undated /latest/text
    cand = Candidate(url="https://www.legislation.gov.au/C2004A02124/2026-06-04/2026-06-04/"
                         "text/original/epub", economy="AU", law_name_guess="TIA Act 1979")
    (plan,) = _adapter().build_plans(cand, forms="html")
    assert plan.method == "requests" and plan.unpack == "epub_html"
    assert plan.form_factor == "html"
    assert plan.citation_url == cand.url


def test_build_plans_framed_fallback_carries_the_multivolume_reject_guard():
    cand = Candidate(url="https://www.legislation.gov.au/C2004A02124/latest/text",
                     economy="AU", law_name_guess="TIA Act 1979")
    (plan,) = _adapter().build_plans(cand, forms="html")
    assert plan.iframe_selector == "iframe#epubFrame"
    assert plan.reject_pattern and re.search(plan.reject_pattern,
                                             "This compilation is in 12 volumes")
