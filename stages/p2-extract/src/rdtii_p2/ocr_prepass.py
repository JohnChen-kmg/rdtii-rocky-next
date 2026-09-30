"""OCR the scanned documents of a corpus in parallel, filling the page cache.

This is the only parallel step in the stage, and it exists because Lao PDR is 19,058 pages of
evidence-use scans. In the run loop, one page at a time, that is about fourteen hours; here it
is about twenty-two minutes, and only the first time, because everything after reads the cache.

Two measured facts shape it (`evidence/2026-09-23_ocr_engine_comparison.md`,
`evidence/2026-09-22_lao_ocr_timing.md`):

  * **Tesseract crashes intermittently under parallel load.** Exit 3221225477, an access
    violation, killed a pool twice at 20 and 24 workers while 12 and 16 were clean - and the
    same page succeeded on a retry. So a page that dies is retried, the pool stays alive, and
    the retry is recorded rather than hidden.
  * **Scaling flattens after about 12 workers**, so the default is 16 and not the machine's
    full 28.

The confidence pass is optional. Tesseract's text comes from `image_to_string`; the second
call, `image_to_data`, only produces the per-word confidences. Skipping it halves the work and
**cannot change a single character of the text**, so it is off for bulk and on when a page is
being measured.
"""

from __future__ import annotations

import logging
import os
import statistics
import time
from dataclasses import dataclass
from pathlib import Path

from rdtii_p2 import ocr_cache

log = logging.getLogger("rdtii_p2.ocr_prepass")

RENDER_DPI = 300
DEFAULT_WORKERS = 16
MAX_ATTEMPTS = 3
PROGRESS_EVERY = 250      # pages between progress lines; Lao is 19,058, so about 76 of them


@dataclass
class PageJob:
    doc_id: str
    path: str
    page: int
    pack: str
    tessdata: str
    with_confidence: bool


def _ocr_page(job: PageJob) -> dict:
    """One page, in its own process. Returns the text and what it cost."""
    os.environ["TESSDATA_PREFIX"] = job.tessdata
    os.environ["OMP_THREAD_LIMIT"] = "1"      # one Tesseract thread per worker
    import pypdfium2 as pdfium
    import pytesseract
    from PIL import ImageOps

    from config.settings import load_settings
    cmd = load_settings().resolve_tesseract_cmd()
    if cmd:
        pytesseract.pytesseract.tesseract_cmd = cmd

    last_error = None
    for attempt in range(MAX_ATTEMPTS):
        try:
            started = time.perf_counter()
            pdf = pdfium.PdfDocument(job.path)
            try:
                image = pdf[job.page - 1].render(scale=RENDER_DPI / 72).to_pil()
            finally:
                pdf.close()
            prepared = ImageOps.autocontrast(ImageOps.grayscale(image))
            confidence = None
            if job.with_confidence:
                data = pytesseract.image_to_data(
                    prepared, lang=job.pack, output_type=pytesseract.Output.DICT)
                values = [float(c) for c, w in zip(data["conf"], data["text"])
                          if w.strip() and float(c) >= 0]
                confidence = statistics.mean(values) if values else None
            text = pytesseract.image_to_string(prepared, lang=job.pack)
            return {"doc_id": job.doc_id, "page": job.page, "text": text,
                    "seconds": round(time.perf_counter() - started, 3),
                    "mean_word_confidence": confidence, "retries": attempt, "error": None}
        except Exception as exc:                      # a crashed Tesseract, almost always
            last_error = f"{type(exc).__name__}: {exc}"
            time.sleep(0.5 * (attempt + 1))
    return {"doc_id": job.doc_id, "page": job.page, "text": "", "seconds": 0.0,
            "mean_word_confidence": None, "retries": MAX_ATTEMPTS, "error": last_error}


def run_prepass(jobs_by_doc: dict, out_dir: Path, workers: int = DEFAULT_WORKERS) -> dict:
    """OCR every page of every document given, in parallel, and fill the cache.

    `jobs_by_doc` maps doc_id -> (path, page_count, language, pack, tessdata, sha256).
    Documents already cached under the same key are skipped before any work starts, and
    each document is written as soon as its own last page returns - so stopping the run,
    or losing the pool to one of Tesseract's access violations, costs only the documents
    that were mid-flight. Re-running picks up from what is on disk.
    """
    import multiprocessing as mp

    pending: list[PageJob] = []
    planned: dict[str, ocr_cache.DocCache] = {}
    skipped = 0
    for doc_id, spec in jobs_by_doc.items():
        path, page_count, language, pack, tessdata, sha = spec
        meta = ocr_cache.DocCache(doc_id=doc_id, content_sha256=sha,
                                  engine=f"tesseract-{pack}", language=language,
                                  dpi=RENDER_DPI,
                                  preprocessing=[f"rasterize@{RENDER_DPI}dpi", "grayscale",
                                                 "autocontrast"])
        if ocr_cache.read(out_dir, doc_id, meta) is not None:
            skipped += 1
            continue
        planned[doc_id] = meta
        for page in range(1, page_count + 1):
            pending.append(PageJob(doc_id, str(path), page, pack, str(tessdata), False))

    if not pending:
        log.info("OCR pre-pass: nothing to do, %d document(s) already cached", skipped)
        return {"documents": 0, "pages": 0, "cached": skipped, "seconds": 0.0, "failed": 0}

    log.info("OCR pre-pass: %d page(s) across %d document(s), %d already cached, %d workers",
             len(pending), len(planned), skipped, workers)
    expected = {doc_id: 0 for doc_id in planned}
    for job in pending:
        expected[job.doc_id] += 1

    started = time.perf_counter()
    collected: dict[str, list[dict]] = {}
    done = failed = retried = 0
    written = 0
    with mp.Pool(workers) as pool:
        # imap_unordered, not map: a document is written to the cache the moment its last
        # page comes back, so a pool that dies at page 18,000 of 19,058 keeps the 17,000-odd
        # pages already paid for. `map` returns nothing until every page is finished, which
        # would have made the resumability this cache is built for a fiction.
        for result in pool.imap_unordered(_ocr_page, pending, chunksize=4):
            done += 1
            doc_id = result["doc_id"]
            pages = collected.setdefault(doc_id, [])
            pages.append(result)
            if result["error"]:
                failed += 1
                log.error("%s page %d failed after %d attempts: %s",
                          doc_id, result["page"], MAX_ATTEMPTS, result["error"])
            elif result["retries"]:
                retried += 1
            if len(pages) == expected[doc_id]:
                pages.sort(key=lambda r: r["page"])
                meta = planned[doc_id]
                meta.pages = [ocr_cache.PageRecord(
                    page=r["page"], chars=len(r["text"]), seconds=r["seconds"],
                    mean_word_confidence=r["mean_word_confidence"], retries=r["retries"])
                    for r in pages]
                ocr_cache.write(out_dir, meta, [r["text"] for r in pages])
                written += 1
                del collected[doc_id]
            if done % PROGRESS_EVERY == 0:
                spent = time.perf_counter() - started
                rate = done / spent if spent else 0
                remaining = (len(pending) - done) / rate / 60 if rate else 0
                log.info("OCR pre-pass: %d/%d pages, %d docs cached, %.1f pages/s, "
                         "~%.0f min left", done, len(pending), written, rate, remaining)
    elapsed = time.perf_counter() - started
    if collected:                       # only reachable if a doc's page count was wrong
        log.warning("%d document(s) left incomplete and were not cached: %s",
                    len(collected), ", ".join(sorted(collected)))

    rate = len(pending) / elapsed if elapsed else 0
    log.info("OCR pre-pass done: %d pages in %.1f min (%.1f pages/s), %d retried, %d failed",
             len(pending), elapsed / 60, rate, retried, failed)
    return {"documents": len(planned), "pages": len(pending), "cached": skipped,
            "seconds": round(elapsed, 1), "pages_per_second": round(rate, 2),
            "retried": retried, "failed": failed}
