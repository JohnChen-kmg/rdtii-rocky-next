"""The pre-pass must write each document as it completes, not at the end of the corpus.

This is a regression test for a real bug, caught three minutes into the Lao run on
2026-09-23. `run_prepass` used `pool.map`, which returns only when every page of every
document is finished - so 19,058 Lao pages produced nothing on disk until the very last
one, and a pool lost to one of Tesseract's intermittent access violations (the crashes
the retry logic exists for) would have thrown away the entire pass. `ocr_cache`'s own
docstring promised "a killed run resumable"; `map` made that untrue.

The property under test is not "the cache is correct at the end" - `map` satisfied that.
It is that document N is readable from disk *while document N+1 is still being OCR'd*.
"""

from __future__ import annotations

import json

from rdtii_p2 import ocr_cache, ocr_prepass


class _LazyPool:
    """Stands in for mp.Pool: runs jobs in-process and yields them one at a time.

    `observer` is called after each page is handed back, so the test can look at the
    output directory mid-pass - which is exactly what a crash would interrupt.
    """

    def __init__(self, texts, observer):
        self._texts = texts
        self._observer = observer

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def imap_unordered(self, func, jobs, chunksize=1):
        for job in jobs:
            yield {"doc_id": job.doc_id, "page": job.page,
                   "text": self._texts[(job.doc_id, job.page)],
                   "seconds": 0.01, "mean_word_confidence": None,
                   "retries": 0, "error": None}
            self._observer()


def _install(monkeypatch, texts, observer):
    import multiprocessing as mp
    monkeypatch.setattr(mp, "Pool", lambda workers: _LazyPool(texts, observer))


def _jobs(spec):
    """doc_id -> page_count, as run_prepass wants it."""
    return {doc_id: (f"{doc_id}.pdf", pages, "lao", "lao", "/tessdata",
                     f"sha-{doc_id}") for doc_id, pages in spec.items()}


def test_document_is_cached_before_the_pass_finishes(tmp_path, monkeypatch):
    spec = {"la-first-001": 2, "la-second-001": 2, "la-third-001": 2}
    texts = {(doc, page): f"{doc} page {page}"
             for doc, pages in spec.items() for page in range(1, pages + 1)}

    seen: list[list[str]] = []

    def observe():
        cached = sorted(p.parent.name for p in (tmp_path / "ocr").glob("*/meta.json"))
        seen.append(cached)

    _install(monkeypatch, texts, observe)
    report = ocr_prepass.run_prepass(_jobs(spec), tmp_path, workers=4)

    # the heart of it: the first document was on disk after its 2nd page, with four
    # pages of the corpus still to come. Under pool.map every snapshot is empty.
    assert seen[1] == ["la-first-001"], seen
    assert seen[3] == ["la-first-001", "la-second-001"], seen
    assert report["documents"] == 3 and report["pages"] == 6 and report["failed"] == 0


def test_cached_pages_are_readable_and_the_rerun_skips_them(tmp_path, monkeypatch):
    spec = {"la-only-001": 3}
    texts = {("la-only-001", page): f"ມາດຕາ {page}" for page in (1, 2, 3)}
    _install(monkeypatch, texts, lambda: None)
    ocr_prepass.run_prepass(_jobs(spec), tmp_path, workers=2)

    meta = ocr_cache.DocCache(doc_id="la-only-001", content_sha256="sha-la-only-001",
                              engine="tesseract-lao", language="lao",
                              dpi=ocr_prepass.RENDER_DPI)
    pages = ocr_cache.read(tmp_path, "la-only-001", meta)
    assert pages == ["ມາດຕາ 1", "ມາດຕາ 2", "ມາດຕາ 3"]

    stored = json.loads((tmp_path / "ocr" / "la-only-001" / "meta.json").read_text(
        encoding="utf-8"))
    assert [p["page"] for p in stored["pages"]] == [1, 2, 3]   # written in page order

    # second pass: the key matches, so nothing is OCR'd again
    def fail():
        raise AssertionError("a cached document must not be re-OCR'd")

    _install(monkeypatch, texts, fail)
    again = ocr_prepass.run_prepass(_jobs(spec), tmp_path, workers=2)
    assert again == {"documents": 0, "pages": 0, "cached": 1, "seconds": 0.0, "failed": 0}


def test_a_failed_page_is_counted_and_the_document_still_lands(tmp_path, monkeypatch):
    """A page Tesseract could not read must not cost the pages around it."""
    spec = {"la-partial-001": 2}
    texts = {("la-partial-001", 1): "ມາດຕາ 1", ("la-partial-001", 2): "ok"}

    import multiprocessing as mp

    class _OnePageFails(_LazyPool):
        def imap_unordered(self, func, jobs, chunksize=1):
            for result in super().imap_unordered(func, jobs, chunksize):
                if result["page"] == 2:
                    result = {**result, "text": "", "error": "OSError: access violation",
                              "retries": ocr_prepass.MAX_ATTEMPTS}
                yield result

    monkeypatch.setattr(mp, "Pool", lambda workers: _OnePageFails(texts, lambda: None))
    report = ocr_prepass.run_prepass(_jobs(spec), tmp_path, workers=1)

    assert report["failed"] == 1
    meta = ocr_cache.DocCache(doc_id="la-partial-001", content_sha256="sha-la-partial-001",
                              engine="tesseract-lao", language="lao",
                              dpi=ocr_prepass.RENDER_DPI)
    assert ocr_cache.read(tmp_path, "la-partial-001", meta) == ["ມາດຕາ 1", ""]
