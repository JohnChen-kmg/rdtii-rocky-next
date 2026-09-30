"""Lane C driver - scanned-PDF OCR at corpus scale (T9 + kickoff decision #3).

Priority order over the 12,292 scanned pages: (a) gold-set/seed-law MY docs,
(b) manifest-title matches against P0 signature keywords, (c) the rest
overnight. OCR once, cache forever in source_text/. The per-page engine work
lives in config/ocr/ (get_ocr); this module owns batching, caching, and the
doc-level CER bookkeeping. The single-page pilot path is `p2-extract pilot`.
"""

from __future__ import annotations


def run_lane_c(*args, **kwargs):  # pragma: no cover - T9
    raise NotImplementedError("Corpus-scale Lane C lands at T9; use 'p2-extract pilot' for T2b.")
