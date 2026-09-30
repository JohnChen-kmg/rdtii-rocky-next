"""Native-twin alignment for clean scanned snippets (PLAN.md section 2.4.3a).

When a scanned law also exists as native text, the emitted snippet is sourced
from the twin's clean text (snippet_source=native_twin); OCR output is used
only to locate/align and to measure CER. Lands with T9 (Deliverable #4).
"""

from __future__ import annotations


def align(*args, **kwargs):  # pragma: no cover - T9
    raise NotImplementedError("Native-twin alignment lands at T9 (MY scanned-gazette demo).")
