"""Data models + the frozen Manifest field set (contract §2.2).

The 24-field order below IS the CSV column order — do not reorder (a column
reorder is a MAJOR contract change, §8). REQUIRED_FIELDS is the 15-field
required set; the schema (contracts/schemas/manifest.schema.json) is the
authority — these constants must stay in lockstep with it.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

# --- Manifest field set (contract §2.2 table order) -------------------------

MANIFEST_FIELDS: list[str] = [
    "contract_version",
    "instrument_version",
    "doc_id",
    "economy",
    "source_url",
    "access_date",
    "source_type",
    "pdf_is_scanned",
    "local_path",
    "law_name_guess",
    "law_number_guess",
    "pillar_hint",
    "indicator_hints",
    "retrieval_method",
    "http_status",
    "http_headers_path",
    "content_type",
    "content_sha256",
    "byte_size",
    "page_count",
    "anchor_hint",
    "anchor_kind",
    "seed_query",
    "crawl_notes",
    # v0.2.0 — legal metadata harvested at discovery (all optional; per-portal availability)
    "publication_date",
    "assent_date",
    "commencement_date",
    "in_force_status",
]

REQUIRED_FIELDS: list[str] = [
    "contract_version",
    "doc_id",
    "economy",
    "source_url",
    "access_date",
    "source_type",
    "pdf_is_scanned",
    "local_path",
    "law_name_guess",
    "retrieval_method",
    "http_status",
    "http_headers_path",
    "content_type",
    "content_sha256",
    "byte_size",
]

OPTIONAL_FIELDS: list[str] = [f for f in MANIFEST_FIELDS if f not in REQUIRED_FIELDS]

# Type hints used for CSV<->typed coercion (schema.py).
INT_FIELDS = frozenset({"http_status", "byte_size"})
NULLABLE_INT_FIELDS = frozenset({"page_count"})
NULLABLE_BOOL_FIELDS = frozenset({"pdf_is_scanned"})


# --- Runtime models ---------------------------------------------------------


@dataclass
class Candidate:
    """A discovery target handed from an adapter.discover() to the orchestrator."""

    url: str
    economy: str
    law_name_guess: str
    law_number_guess: Optional[str] = None
    pillar_hint: Optional[str] = None
    indicator_hints: Optional[str] = None
    seed_query: Optional[str] = None
    expect_scanned: bool = False
    # Legal metadata harvested at discovery (v0.2.0). Availability varies by portal.
    publication_date: Optional[str] = None
    assent_date: Optional[str] = None
    commencement_date: Optional[str] = None
    in_force_status: Optional[str] = None
    # Seed-level form override (sources yaml `form:`): "html" pins a register doc to its
    # full-text HTML even when a PDF exists (e.g. AU SOCI — P2's HTML lane parses AU
    # compilations reliably; its PDF splitter does not).
    force_form: Optional[str] = None
    # A single logical law may need >1 fetch (e.g. SG: html + native PDF).
    # Adapters may attach one or more FetchPlans; if empty the orchestrator asks
    # the adapter to resolve() on demand.
    law_slug: Optional[str] = None


@dataclass
class FetchPlan:
    """How to fetch one artifact (adapter.build_plans() output)."""

    url: str                            # the exact URL to fetch
    method: str = "playwright"          # playwright | requests
    form_factor: str = "html"           # html | pdf
    needs_js: bool = True
    wait_selector: Optional[str] = None
    scroll: bool = False
    kind: str = "page"                  # native | scanned | page  (storage filename kind)
    citation_url: Optional[str] = None  # clean URL to record as manifest source_url (defaults to url)
    anchor_hint: Optional[str] = None
    anchor_kind: Optional[str] = None
    # When set, the playwright rung captures THIS iframe's document, not the page shell.
    # (AU legislation.gov.au serves the Act text inside a blob iframe#epubFrame; the outer
    # page is only nav chrome.)
    iframe_selector: Optional[str] = None
    # Post-fetch transform. "epub_html": the fetched bytes are an epub; extract and
    # concatenate ALL spine documents (verified against the OPF spine — a partial
    # extraction is a loud failure, never a silent one). AU multi-volume compilations
    # ship every volume as a separate spine document (2026-07-17 truncation fix).
    unpack: Optional[str] = None
    # Loud-failure guard: if this regex matches the captured HTML, the fetch is marked
    # FAILED even though bytes arrived. Used on the AU framed-HTML fallback, where a
    # multi-volume compilation renders only volume 1 in the epubFrame — a silent partial
    # capture must never be stored (2026-07-17 truncation fix).
    reject_pattern: Optional[str] = None

    def source_url(self) -> str:
        return self.citation_url or self.url


@dataclass
class HttpMeta:
    """HTTP provenance captured on every fetch → the .headers.json sidecar."""

    final_url: str
    status: int
    retrieval_method: str               # playwright | requests | api
    content_type: str = ""
    redirect_chain: list[str] = field(default_factory=list)
    request_headers: dict[str, str] = field(default_factory=dict)
    response_headers: dict[str, str] = field(default_factory=dict)
    fetched_at: str = ""                # ISO-8601 UTC
    error: Optional[str] = None

    def sidecar_dict(self) -> dict[str, Any]:
        return {
            "final_url": self.final_url,
            "status": self.status,
            "retrieval_method": self.retrieval_method,
            "content_type": self.content_type,
            "redirect_chain": self.redirect_chain,
            "request_headers": self.request_headers,
            "response_headers": self.response_headers,
            "fetched_at": self.fetched_at,
            "error": self.error,
        }


@dataclass
class FetchResult:
    """Bytes + provenance returned by fetcher.fetch()."""

    content: bytes
    http: HttpMeta
    ok: bool

    @property
    def status(self) -> int:
        return self.http.status
