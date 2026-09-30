"""Malaysia — Laws of Malaysia (lom.agc.gov.my), driven by the portal's own listings.

Rewritten 2026-09-13 in the scraping workshop (countries/my-malaysia/NOTES.md, POLICY.md,
CONTRACT.md). It replaces the Round 1 act-number walk, which guessed each act's file from
upload order and stored reprints years out of date.

What the portal offers (examined live 2026-09-13):
  principal.php?type=updated    every principal act with its CURRENT consolidation file and its
                                "As At" date, in English (BI) and Malay (BM). 890 acts.
  principal.php?type=amendment  every amending act from A1392 on, with royal assent, publication
                                and commencement, and its PDF in both languages. 406 rows, 402 acts.
Both pages are empty shells. DataTables POSTs to json-updated-2024.php / json-amendment-2024.php,
and the reply is AES-256-GCM encrypted with a key the page itself publishes
(`SEARCH_RESPONSE_KEY`). We read the key from the page on every run and decrypt exactly as the
browser does; nothing is hard-coded.

Detail pages (act-detail.php) only open through the signed `processFile.php?isDirect=1&token=…`
links the listings hand out; a hand-built URL answers "Invalid request". A principal act's detail
page carries its timeline: every version (ORIGINAL, REPRINT, REPRINT ONLINE), every AMENDMENTS
entry and every SUBSIDIARY_LEGISLATION entry, each with a project id and its PDF. An AMENDMENTS
entry's project id equals the amending act's ILP_PROJECT_ID in the amendment listing, which is the
authoritative principal→amendment link. An amending act's detail page lists its commencement
order (a P.U. (B) SUBSIDIARY_LEGISLATION entry) with the order's PDF and its per-section dates.

Documents are plain GETs of /ilims/upload/portal/akta/... PDFs.

Discovery (POLICY.md §3):
  seed      seed_laws from sources.yaml. "Act N" and "Act AN" resolve through the listings; other
            seeds (agency PDFs and pages) resolve as in Round 1. Each seed principal act brings the
            amending acts listed after its as-at date, their commencement orders, and (when
            lom.subsidiary_from_timeline is on) the subsidiary legislation its timeline lists.
  relevant  seed ∪ principal acts whose English title matches the search terms, each with its
            later amending acts.
  all       every principal act (current consolidation) ∪ every amending act.
If lom cannot be read (robots.txt, an outage, throttling), the run still returns the seeds that do
not need lom, lom seeds fall back to their registry URLs and are flagged, and the failure is
printed and kept in `lom_error`.

What each candidate records beyond the 0.2.0 manifest fields is attached as `cand.contract_meta`
(a dict named after CONTRACT.md §3.3 columns). The Round 1 engine ignores it; the 0.3.0 normaliser
reads it. Raw portal values only: status is never defaulted, dates keep the portal's text next to
an ISO form. `crawl_flags` holds only CONTRACT §3.3 values; this adapter's other warnings are in
`review_flags` (NOTES.md §4 proposes them for the contract).

Politeness: every discovery request to lom goes through one pacer (REQUEST_DELAY_MS, default 3 s,
plus up to half again as jitter; longer if robots.txt declares a Crawl-delay). Redirect hops,
retries and throttling back-offs are each paced. robots.txt is read before the first request and
its rules are matched on the crawler's product token against every URL requested and every lom
document handed to the engine. A 5xx robots.txt is treated as the registry's `lom.robots_5xx` says
(POLICY.md §5.4, decision 9), defaulting to "deny". Every request is kept in `discovery_log` with
its time and wait, for the crawl log. Document fetches are paced by the orchestrator's RateLimiter.

Requires the `cryptography` package for AES-GCM (added to requirements at hand-back).
"""
from __future__ import annotations

from .records import (  # noqa: F401
    LomUnavailable, RobotsDisallowed, LomThrottled, LomDocument, ListingVersion, PrincipalAct, AmendingAct, TimelineEntry,
)
from .robots import (  # noqa: F401
    _ROBOTS_TOKEN, RobotsRules, _robots_pattern_matches, robots_token,
)
from .client import (  # noqa: F401
    LomClient, _retry_after_seconds,
)
from .parse import (  # noqa: F401
    _LOM, _LISTINGS, _PATH_SAFE, _STATUS_MARKER, _NYIF_MARKER, _PARTIAL_REPEAL, _NOT_YET_IN_FORCE, _EXCEPT, _PU_B_REF, _TEXT_VERSION, _MONTHS, _DATE_ISO, _DATE_DMY, _DATE_NAMED, extract_response_key, datatables_form, decrypt_listing, parse_principal, principal_status, parse_amendment, amendment_status, pu_b_refs, parse_timeline, portal_file_url, decode_token_target, choose_document, document_as_at, choose_principal_document, _normalise_title, amending_base_title, principal_title_key, title_matches_base, all_dates, iso_date, amendment_effective_date, _documents, _timeline_entry_for, _timeline_entry_date, _title_year, _marker_number, _portal_label, _positive_int, _json_or_text, _clean, _anchor_text, _blank, _dash_blank, _pu_key, _act_key, _law_number, _a_number_int, _act_number,
)
from .relevance import (  # noqa: F401
    RuleGroup, TitleRule,
    _STOP, _relevance_phrases,
)
from .adapter import (  # noqa: F401
    _LOM_HOST, _WHITELIST, _DEFAULT_UA, MyGazetteAdapter,
)
from urllib.parse import urlparse  # noqa: F401,E402  (tests use my_gazette.urlparse)
from . import catalogue  # noqa: F401,E402  (tests and callers use my_gazette.catalogue)
