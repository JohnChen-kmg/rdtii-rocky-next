"""Lane dispatch on source_type + mis-flag recovery (PLAN.md section 2.4/2.4.4).

Project 1 classifies; Project 2 re-checks. On every PDF we independently
measure mean extractable chars/page and reroute if the classification is wrong,
correcting BOTH provenance fields (source_type and pdf_is_scanned) so the
emitted record stays internally consistent (finding #15). Every reroute is
logged by the caller into extract_log.jsonl.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from config.settings import Settings
from rdtii_p2 import parse_pdf_native

log = logging.getLogger("rdtii_p2.router")

LANE_BY_TYPE = {"html": "A", "pdf_native": "B", "pdf_scanned": "C",
                # lane D: Office Open XML, China's national law database
                "docx": "D", "doc": "D"}


@dataclass
class Route:
    lane: str                       # "A" | "B" | "C"
    source_type_final: str          # post-recheck source_type
    pdf_is_scanned_final: bool | None
    reroute_reason: str | None = None
    chars_per_page: float | None = None


def route(source_type: str, pdf_is_scanned: bool | None, local_path: Path,
          settings: Settings) -> Route:
    if source_type == "html":
        return Route(lane="A", source_type_final="html", pdf_is_scanned_final=None)
    if source_type in ("docx", "doc"):
        # no text-layer recheck: an OOXML package either parses or raises, and there is
        # nothing to mis-flag the way a scanned PDF can be mis-flagged as native
        return Route(lane="D", source_type_final=source_type, pdf_is_scanned_final=None)

    threshold = settings.native_text_chars_per_page_min
    chars = parse_pdf_native.mean_chars_per_page(local_path)

    if source_type == "pdf_native" and chars < threshold:
        reason = (
            f"manifest says pdf_native but mean {chars:.0f} extractable chars/page "
            f"< {threshold} - rerouted to Lane C (OCR)"
        )
        log.warning("%s: %s", local_path.name, reason)
        return Route(lane="C", source_type_final="pdf_scanned",
                     pdf_is_scanned_final=True, reroute_reason=reason,
                     chars_per_page=chars)

    if source_type == "pdf_scanned" and chars >= threshold:
        reason = (
            f"manifest says pdf_scanned but a clean text layer exists "
            f"({chars:.0f} chars/page >= {threshold}) - parsed natively (Lane B)"
        )
        log.warning("%s: %s", local_path.name, reason)
        return Route(lane="B", source_type_final="pdf_native",
                     pdf_is_scanned_final=False, reroute_reason=reason,
                     chars_per_page=chars)

    return Route(
        lane=LANE_BY_TYPE[source_type],
        source_type_final=source_type,
        pdf_is_scanned_final=(source_type == "pdf_scanned"),
        chars_per_page=chars,
    )
