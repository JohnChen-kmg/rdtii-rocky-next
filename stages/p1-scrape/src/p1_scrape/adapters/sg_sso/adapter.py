"""Singapore — Statutes Online (sso.agc.gov.sg).

The Round 1 adapter (fetch recipe, relevance net, seed handling) plus the convention's catalogue step
(CONVENTIONS.md section 2): discovery reads the portal's listings and every current act's detail page through one
paced client that honours robots.txt (`Crawl-delay: 6`), and the crawl replays a link list (`sso.frontier:
links_file`) instead of discovering by itself.

Transport recipe (Round 1, unchanged): the native PDF is `?ViewType=Pdf` over plain requests; the HTML form is a
Playwright capture of `?WholeDoc=1` waiting for `div#legisContent`. Deep anchors are `?ProvIds=<provId>` read from
the rendered table of contents.

Settings (`sources.yaml`, block `sso:`; every key can be overridden by SSO_<KEY> in the environment):
  frontier            discover | links_file       what discover() does; links_file replays sso.links_file / SSO_LINKS_FILE
  detail_pages        all | seed | none            whose detail page is read at the catalogue step (decision 17: all)
  subsidiary_acts     seed | none                  whose subsidiary legislation is listed and fetched (decision 12)
  subsidiary_max_per_act 100                       SL fetched per act at most (the Income Tax Act lists 774); 0 = all
  acts_supp_years     2                            how many years of the Acts Supplement are read (this year back)
  listing_paging      next | orders                next (the code's default): every listing is read 100 rows a page,
                                                   following its Next Page links. orders: one page of
                                                   listing_page_size, the Current listing ASC and DESC (the method
                                                   of 2026-09-15; the portal refused 500-row pages from 2026-09-16)
  listing_rows        100                          rows a page when paging by next
  listing_page_size   500                          rows a page when paging by orders
  read_repealed       true                         the Repealed and Uncommenced listings are read for status
"""
from __future__ import annotations

import os
import re
from datetime import date
from typing import Any, Optional
from urllib.parse import urlparse

from ...inventory import InventoryItem
from ...models import Candidate, FetchPlan
from ...sources import all_query_terms, indicator_pillar, pillar_hint_for
from ...utils import append_query
from ..base import PortalAdapter
# The paced client and the robots.txt rules are shared with Malaysia's adapter until the engine gains them
# (NOTES.md 2.5): one request at a time, the larger of the delay and Crawl-delay, every request logged.
from ..my_gazette.client import LomClient as PacedClient
from ..my_gazette.records import LomThrottled
from ..my_gazette.robots import RobotsRules, robots_token
from .parse import (
    ROOT, ActDetail, ListedLaw, ListedSl, act_code, next_page_path, parse_detail, parse_listing, parse_sl_tab,
    results_count,
)

_SSO_ACT_RE = re.compile(r"sso\.agc\.gov\.sg/(Act|Acts-Supp|SL|SL-Supp)/", re.I)
_TOC_RE = re.compile(r'<input[^>]*\bvalue="(pr[^"]+)"[^>]*>\s*<label[^>]*>([^<]*)</label>', re.I)
_STOP = {"of", "the", "and", "a", "an", "for", "to", "in", "on", "or", "by", "with", "any", "act"}
_AMENDING_TITLE = re.compile(r"\b(Amendment|Amendments|Miscellaneous Amendments|Repeal)\b", re.I)
_DEFAULT_UA = "RDTII-Rocky-Crawler/0.1 (+polite public-law retrieval)"
_HOST = "sso.agc.gov.sg"
_THROTTLE_CODES = (403, 429, 467, 503)          # 467 is SSO's own soft-throttle answer (engine fetcher.py)
_MAX_CONSECUTIVE_FAILURES = 5
_MAX_LISTING_PAGES = 20                         # the Repealed listing, the longest, is 3 pages of 100
_ACCEPTED_RETRIES = 2                           # HTTP 202 on 50 of 525 act pages in the build of 11:50 UTC, 2026-09-15

LISTINGS = {
    "current": "/Browse/Act/Current/All?PageSize={size}&SortBy=Title&SortOrder={order}",
    "repealed": "/Browse/Act/Repealed/All?PageSize={size}",
    "uncommenced": "/Browse/Act/Uncommenced/All?PageSize={size}",
    "acts_supp": "/Browse/Acts-Supp/Published/{year}?PageSize={size}",
}


class SsoUnavailable(RuntimeError):
    """SSO cannot be read on this run: robots.txt disallows, a listing failed, or the page format changed."""


class SgSsoAdapter(PortalAdapter):
    economy = "SG"

    def __init__(self, cfg: dict[str, Any], client: Optional[PacedClient] = None, today: Optional[str] = None):
        self.cfg = cfg
        self.sso_cfg: dict = dict(cfg.get("sso") or {})
        self._vocab = _tokenize(" ".join(all_query_terms(cfg)))   # for anchor scoring
        self._phrases = _relevance_phrases(cfg)                    # for title relevance
        self.inventory: list[InventoryItem] = []
        self.inventory_note: Optional[str] = None
        self.notes: list[str] = []
        self._client: Optional[PacedClient] = client
        self._today = today or date.today().isoformat()
        self._frontier_override: Optional[str] = None
        self._robots_checked = False
        self.robots_record: Optional[dict] = None
        self.sso_error: Optional[str] = None
        # what the catalogue step read
        self.listed: dict[str, list[ListedLaw]] = {}               # listing -> rows
        self.listing_counts: dict[str, dict] = {}
        self.details: dict[str, ActDetail] = {}                    # code -> detail page
        self.subsidiary: dict[str, list[ListedSl]] = {}            # code -> SL rows read
        self.subsidiary_totals: dict[str, Optional[int]] = {}      # code -> SL the tab lists
        self.frontier_meta: Optional[dict] = None
        self._failures_in_a_row = 0
        self.accepted_retries = 0
        self.root = ROOT

    # --- settings -----------------------------------------------------------------------

    #: what each setting means when the registry does not say; `effective_settings` resolves against these, so a
    #: run's catalogue_meta.json records the values the code used, not the ones the registry happened to carry
    SETTING_DEFAULTS: dict[str, Any] = {"detail_pages": "all", "subsidiary_acts": "seed", "subsidiary_max_per_act": 100,
        "acts_supp_years": 2, "listing_paging": "next", "listing_rows": 100, "listing_page_size": 500,
        "read_repealed": True, "frontier": "discover", "root": ROOT,}

    def effective_settings(self, keys=None) -> dict:
        """The settings this run really used: the registry's value, the environment's override, or the default."""
        out: dict[str, Any] = {}
        for key in (keys or tuple(self.SETTING_DEFAULTS)):
            default = self.SETTING_DEFAULTS.get(key)
            value = self._setting(key, default)
            if isinstance(default, bool):
                value = value if isinstance(value, bool) else str(value).strip().lower() not in ("0", "false", "no", "off")
            elif isinstance(default, int) and value is not None:
                value = int(value)
            elif isinstance(default, list) and isinstance(value, str):
                value = [v.strip() for v in value.split(",") if v.strip()]
            out[key] = value
        return out

    def _setting(self, key: str, default: Any) -> Any:
        env = os.environ.get("SSO_" + key.upper())
        return env if env is not None else self.sso_cfg.get(key, default)

    def _root(self) -> str:
        self.root = str(self._setting("root", ROOT)).rstrip("/")
        return self.root

    def _int_setting(self, key: str, default: int) -> int:
        return int(self._setting(key, default))

    def _frontier(self) -> str:
        frontier = str(self._frontier_override or self._setting("frontier", "discover")).strip().lower()
        if frontier not in ("discover", "links_file"):
            raise ValueError(f"sso.frontier / SSO_FRONTIER: {frontier!r} is not discover or links_file")
        return frontier

    def _detail_policy(self) -> str:
        policy = str(self._setting("detail_pages", "all")).strip().lower()
        if policy not in ("all", "seed", "none"):
            raise ValueError(f"sso.detail_pages / SSO_DETAIL_PAGES: {policy!r} is not all, seed or none")
        return policy

    def _subsidiary_policy(self) -> str:
        policy = str(self._setting("subsidiary_acts", "seed")).strip().lower()
        if policy not in ("seed", "none"):
            raise ValueError(f"sso.subsidiary_acts / SSO_SUBSIDIARY_ACTS: {policy!r} is not seed or none")
        return policy

    def _get_client(self, fetcher) -> PacedClient:
        if self._client is None:
            settings = getattr(fetcher, "settings", None)
            ua = getattr(settings, "user_agent", None) or os.environ.get("USER_AGENT") or _DEFAULT_UA
            delay = getattr(settings, "request_delay_seconds", None)
            if delay is None:
                delay = int(os.environ.get("REQUEST_DELAY_MS", "3000")) / 1000.0
            self._client = PacedClient(ua, float(delay))
        return self._client

    def _warn(self, message: str) -> None:
        self.notes.append(message)
        print(f"[crawl] SG: WARNING {message}", flush=True)

    # --- discovery -----------------------------------------------------------------------
    def discover(self, pillars: list[int], scope: str = "relevant", fetcher=None) -> list[Candidate]:
        self._detail_policy(), self._subsidiary_policy()
        if scope == "seed" and self._frontier() == "discover" and fetcher is None:
            self.inventory = self._seed_inventory(pillars)
            return self._seed_candidates(pillars)
        client = self._get_client(fetcher)
        if self._frontier() == "links_file":
            return self._discover_from_links_file(pillars, scope, client, fetcher)
        self._open_sso(client)
        picked = self._build_candidates(pillars, scope, client)
        self._finish(client)
        return list(picked.values())

    def _open_sso(self, client: PacedClient) -> None:
        """robots.txt, then the listings the settings ask for."""
        self._check_robots(client)
        paging = str(self._setting("listing_paging", "next")).strip().lower()
        if paging not in ("next", "orders"):
            raise ValueError(f"sso.listing_paging / SSO_LISTING_PAGING: {paging!r} is not next or orders")
        size = self._int_setting("listing_rows", 100) if paging == "next" else self._int_setting("listing_page_size", 500)
        if paging == "next":
            rows, total, pages = self._read_pages(client, LISTINGS["current"].format(size=size, order="ASC"), "current")
        else:
            rows, total, pages = {}, None, 0
            for order in ("ASC", "DESC"):
                page = self._page(client, LISTINGS["current"].format(size=size, order=order))
                pages += 1
                total = total if total is not None else results_count(page)
                for r in parse_listing(page, "current"):
                    rows.setdefault(r.code, r)
                if total is not None and len(rows) >= total:
                    break
        if not rows:
            raise SsoUnavailable("the Current listing served no act rows: the page format may have changed")
        self.listed["current"] = list(rows.values())
        self.listing_counts["current"] = {"records": len(rows), "total": total}
        if total is not None and len(rows) < total:
            self._warn(f"the Current listing claims {total} acts, {len(rows)} read ({pages} page(s) of {size}): the rest "
                       f"are missing")
        if str(self._setting("read_repealed", True)).lower() not in ("0", "false", "no", "off"):
            for name in ("repealed", "uncommenced"):
                first = LISTINGS[name].format(size=size)
                if paging == "next":
                    got, count, _pages = self._read_pages(client, first, name)
                    self.listed[name] = list(got.values())
                else:
                    page = self._page(client, first)
                    self.listed[name], count = parse_listing(page, name), results_count(page)
                self.listing_counts[name] = {"records": len(self.listed[name]), "total": count}
        years = self._int_setting("acts_supp_years", 2)
        this_year = int(self._today[:4])
        supp: list[ListedLaw] = []
        for year in range(this_year, this_year - years, -1):
            first = LISTINGS["acts_supp"].format(year=year, size=size)
            if paging == "next":
                supp.extend(self._read_pages(client, first, "acts_supp")[0].values())
            else:
                supp.extend(parse_listing(self._page(client, first), "acts_supp"))
        self.listed["acts_supp"] = supp
        self.listing_counts["acts_supp"] = {"records": len(supp), "years": years}

    def _read_pages(self, client: PacedClient, first: str, listing: str) -> tuple[dict[str, ListedLaw], Optional[int], int]:
        """A listing page by page, following its Next Page links until the rows it claims are read, it has no next
        page, or a page adds nothing new. On 2026-09-16 the portal refused the 500-row Current page for hours (HTTP
        403) while 100-row pages and act pages loaded."""
        rows: dict[str, ListedLaw] = {}
        total, path, seen, pages = None, first, set(), 0
        while path and path not in seen and pages < _MAX_LISTING_PAGES:
            seen.add(path)
            page = self._page(client, path)
            pages += 1
            total = total if total is not None else results_count(page)
            before = len(rows)
            for r in parse_listing(page, listing):
                rows.setdefault(r.code, r)
            if (total is not None and len(rows) >= total) or len(rows) == before:
                break
            path = next_page_path(page)
        if total is not None and len(rows) < total and listing != "current":
            self._warn(f"the {listing} listing claims {total} rows, {len(rows)} read ({pages} page(s)): the rest are missing")
        return rows, total, pages

    def _page(self, client: PacedClient, path: str) -> str:
        """One listing or detail page. A throttle answer stops the build (the portal asked); any other failure is the
        caller's to note, except that five in a row stop the build too."""
        resp = client.get(self._root() + path, retries=1)
        for _again in range(_ACCEPTED_RETRIES):        # HTTP 202 without the WAF header: ask again, paced
            if resp.status_code != 202 or _waf_challenge(resp):
                break
            self.accepted_retries += 1
            resp = client.get(self._root() + path, retries=1)
        if _waf_challenge(resp):
            # AWS WAF bot control answers HTTP 202, an empty body and x-amzn-waf-action: challenge (2026-09-15,
            # 13:00 UTC, after 540 paced requests in an hour): a JavaScript challenge a plain client cannot pass
            raise LomThrottled(f"SSO's WAF is challenging this client (HTTP {resp.status_code}, x-amzn-waf-action: "
                               f"challenge) for {path}; wait and rebuild later")
        if resp.status_code in _THROTTLE_CODES:
            raise LomThrottled(f"SSO is throttling: HTTP {resp.status_code} for {path}")
        if resp.status_code != 200:
            self._failures_in_a_row += 1
            if self._failures_in_a_row >= _MAX_CONSECUTIVE_FAILURES:
                raise SsoUnavailable(f"{self._failures_in_a_row} pages in a row failed, the last HTTP {resp.status_code} for {path}")
            raise SsoUnavailable(f"SSO answered HTTP {resp.status_code} for {path}")
        self._failures_in_a_row = 0
        return (resp.content or b"").decode("utf-8", "replace")

    def _check_robots(self, client: PacedClient) -> None:
        if self._robots_checked:
            return
        url = f"{self._root()}/robots.txt"
        resp = client.get(url)
        record = {"url": url, "status": resp.status_code, "read_at": client.log[-1]["ts"] if client.log else None}
        if _waf_challenge(resp):
            self.robots_record = {**record, "waf": "challenge"}
            raise SsoUnavailable("SSO's WAF is challenging this client (HTTP 202, x-amzn-waf-action: challenge) on "
                                 "robots.txt itself: nothing can be read; wait and try later")
        if resp.status_code == 200:
            rules = RobotsRules.parse((resp.content or b"").decode("utf-8", "replace"), robots_token(client.user_agent))
            client.robots = rules
            record.update({"group": rules.group, "crawl_delay": rules.crawl_delay, "rules": rules.rules[:20]})
            if rules.crawl_delay and rules.crawl_delay > client.delay:
                client.delay = float(rules.crawl_delay)
            record["delay_used_s"] = client.delay
        elif resp.status_code >= 500:
            raise SsoUnavailable(f"SSO robots.txt answered HTTP {resp.status_code}; RFC 9309 treats that as full "
                                 f"disallow and no decision allows crawling through it (POLICY.md 5.4)")
        elif resp.status_code in (403, 404, 410):
            record["note"] = "no robots.txt: everything allowed, the delay stays the default"
        else:
            raise SsoUnavailable(f"SSO robots.txt answered HTTP {resp.status_code}: not a robots.txt, not an absence; "
                                 f"nothing is read through it")
        self.robots_record = record
        self._robots_checked = True

    def _finish(self, client: PacedClient) -> None:
        parts = ["SSO listings: " + "; ".join(f"{k} {v.get('records')}" + (f" of {v['total']}" if v.get("total") else "")
                                                for k, v in self.listing_counts.items())]
        parts.append(f"{len(self.details)} detail page(s), {len(self.subsidiary)} SL tab(s) read; "
                     f"{len(client.log)} discovery request(s)")
        self.inventory_note = "; ".join(parts + self.notes)

    # --- the candidates ----------------------------------------------------------------
    def _seed_by_code(self, pillars: list[int]) -> tuple[dict[str, dict], list[dict]]:
        """SSO act seeds keyed by act code, and the other seeds (Acts Supplement, SL, regulator documents)."""
        by_code, others = {}, []
        for law in self.cfg.get("seed_laws", []) or []:
            inds = law.get("indicators", []) or []
            if pillars and not any(indicator_pillar(i) in pillars for i in inds):
                continue
            code = act_code(law.get("url", ""))
            if code:
                by_code[code] = law
            else:
                others.append(law)
        return by_code, others

    @staticmethod
    def _sl_code(url: str) -> Optional[str]:
        m = re.search(r"sso\.agc\.gov\.sg/SL/([A-Za-z0-9-]+)", url or "")
        return m.group(1) if m else None

    @staticmethod
    def _sso_code(url: str) -> Optional[str]:
        """The identifier segment of any SSO document address: PDPA2012, 40-2020, PDPA2012-S65-2021."""
        m = re.search(r"sso\.agc\.gov\.sg/(?:Act|Acts-Supp|SL|SL-Supp)/([A-Za-z0-9-]+)", url or "")
        return m.group(1) if m else None

    def _build_candidates(self, pillars: list[int], scope: str, client: PacedClient) -> dict[str, Candidate]:
        seeds, other_seeds = self._seed_by_code(pillars)
        sl_seeds = {self._sl_code(law.get("url", "")): law for law in other_seeds if self._sl_code(law.get("url", ""))}
        matched_sl: set[str] = set()
        detail_policy, sub_policy = self._detail_policy(), self._subsidiary_policy()
        current = {r.code: r for r in self.listed.get("current", [])}
        self.inventory = [InventoryItem(economy="SG", law_name=r.title, url=self.root + r.path, law_number=None,
                                        source="browse") for r in current.values()]
        self._mark_relevance(self.inventory)
        relevant_codes = {act_code(it.url) for it in self.inventory if it.relevant}
        picked: dict[str, Candidate] = {}

        def add(c: Optional[Candidate]) -> None:
            if c is not None and c.url and c.url not in picked:
                picked[c.url] = c

        # seeds first: SSO acts by code, then the other seeds as they are
        order = list(seeds) + [c for c in current if c not in seeds]
        for code in order:
            row = current.get(code)
            law = seeds.get(code)
            if row is None:
                if law is not None:                 # a seed act the Current listing does not carry (repealed?)
                    add(self._plain_seed(law, "principal_act"))
                continue
            in_scope = scope == "all" or law is not None or (scope == "relevant" and code in relevant_codes)
            if not in_scope:
                continue
            read = detail_policy == "all" or (detail_policy == "seed" and law is not None)
            detail = self._load_detail(code, client) if read else None
            sl_rows = self._load_sl(code, client) if law is not None and sub_policy == "seed" else []
            add(self._principal_candidate(row, detail, law, relevant=code in relevant_codes))
            for sl in sl_rows:
                add(self._sl_candidate(sl, code, row, law=sl_seeds.get(sl.code)))
                matched_sl.add(sl.code)
        for law in other_seeds:
            if self._sl_code(law.get("url", "")) in matched_sl:
                continue                                    # served from its act's SL tab, with the seed's tags
            add(self._plain_seed(law, None))
        if scope == "all":
            titles = [_norm(r.title) for r in self.listed.get("repealed", [])]
            duplicates = {t for t in titles if titles.count(t) > 1}
            for row in self.listed.get("repealed", []):
                add(self._repealed_candidate(row, duplicates))
            for row in self.listed.get("acts_supp", []):
                add(self._acts_supp_candidate(row, current))
        return picked

    def _load_detail(self, code: str, client: PacedClient) -> Optional[ActDetail]:
        if code in self.details:
            return self.details[code]
        try:
            page = self._page(client, f"/Act/{code}")
        except LomThrottled:
            raise
        except SsoUnavailable as e:
            if "in a row" in str(e):
                raise
            self.notes.append(f"{code}: detail page not read ({e})")
            return None
        except Exception as e:  # noqa: BLE001 — a network error on one page is a note, not the end of the build
            self.notes.append(f"{code}: detail page not read ({type(e).__name__}: {e})")
            self._failures_in_a_row += 1
            if self._failures_in_a_row >= _MAX_CONSECUTIVE_FAILURES:
                raise SsoUnavailable(f"{self._failures_in_a_row} pages in a row failed, the last {type(e).__name__}") from e
            return None
        detail = parse_detail(page, code)
        if not detail.versions:
            self.notes.append(f"{code}: detail page holds no timeline")
        self.details[code] = detail
        return detail

    def _load_sl(self, code: str, client: PacedClient) -> list[ListedSl]:
        """The SL tab, page by page (PageIndex from 0) until every listed instrument is read."""
        if code in self.subsidiary:
            return self.subsidiary[code]
        rows: list[ListedSl] = []
        seen: set[str] = set()
        total = None
        cap = self._int_setting("subsidiary_max_per_act", 100)     # the Income Tax Act lists 774 SL: recorded, not all fetched
        for index in range(0, 20):
            if cap and len(rows) >= cap:
                break
            try:
                page = self._page(client, f"/Act/{code}?DocType=Act&ViewType=Sl&PageIndex={index}&PageSize=100")
            except LomThrottled:
                raise
            except Exception as e:  # noqa: BLE001 — a failed tab is a note; the act's own row stands
                self.notes.append(f"{code}: SL tab page {index} not read ({type(e).__name__}: {e})")
                break
            total = results_count(page) if total is None else total
            new = [r for r in parse_sl_tab(page) if r.code not in seen]
            if cap:
                new = new[:max(0, cap - len(rows))]
            rows.extend(new)
            seen.update(r.code for r in new)
            if not new or total is None or len(rows) >= total:
                break
        if total is not None and total > len(rows):
            self.notes.append(f"{code}: {total} SL listed, {len(rows)} read"
                              + (f" (sso.subsidiary_max_per_act={cap})" if cap and len(rows) >= cap else ""))
        self.subsidiary_totals[code] = total
        self.subsidiary[code] = rows
        return rows

    def _principal_candidate(self, row: ListedLaw, detail: Optional[ActDetail], law: Optional[dict],
                             relevant: bool) -> Candidate:
        inds = (law or {}).get("indicators", []) or []
        url = f"{self.root}/Act/{row.code}?ViewType=Pdf"
        number = (detail.original_number if detail else None) or (law or {}).get("law_number") or None
        cand = Candidate(url=url, economy="SG", law_name_guess=(law or {}).get("law_name") or row.title,
                         law_number_guess=number, pillar_hint=pillar_hint_for(inds) if inds else None,
                         indicator_hints=(",".join(inds) or None),
                         seed_query=(",".join(sorted(p for p in self._phrases if p in row.title.lower())) or None),
                         publication_date=_current_version(detail).published_on if detail and _current_version(detail) else None,
                         in_force_status="Current")
        amendments = [{"instrument": v.amended_by, "in_force_from": v.valid_from, "published_on": v.published_on}
                      for v in (detail.amendments if detail else [])]
        flags = []
        if detail is None:
            flags.append("amendment_check_incomplete")
        if not number:
            flags.append("law_number_unknown")       # the oldest timeline entry is a revised edition or an amendment
        if law and law.get("law_name") and detail and detail.title and _norm(law["law_name"]) != _norm(detail.title):
            flags.append("seed_title_differs_from_portal")
        cand.contract_meta = {
            "portal": "sg-sso", "discovery_path": "seed" if law else "browse_listing",
            "seed_provenance": (law or {}).get("provenance"), "portal_id": row.code, "law_number": number,
            "law_name_portal": detail.title if detail else row.title, "document_kind": "principal_act",
            "text_version": "consolidation", "version_as_at": detail.current_valid_from if detail else None,
            "version_source": "portal_detail_page" if detail and detail.current_valid_from else None,
            "published_on": cand.publication_date, "revised_edition": detail.revised_edition if detail else None,
            "revised_edition_note": detail.revised_edition_note if detail else None,
            "versions_listed": len(detail.versions) if detail else None,
            "linked_amendments": amendments, "amendment_check_complete": detail is not None,
            "last_amending_instrument": detail.last_amending_instrument if detail else None,
            "last_amended_year": (detail.last_amending_instrument or "")[-4:] if detail and detail.last_amending_instrument else None,
            "subsidiary_listed": self.subsidiary_totals.get(row.code) if row.code in self.subsidiary else None,
            "subsidiary_read": len(self.subsidiary.get(row.code, [])) if row.code in self.subsidiary else None,
            "language": "eng", "language_source": "portal_default", "legal_status": "in_force",
            "status_source": "portal_listing", "in_force_status": "Current",
            "title_relevant": relevant, "crawl_flags": [], "review_flags": flags,
        }
        return cand

    def _repealed_candidate(self, row: ListedLaw, duplicate_titles: set[str] = frozenset()) -> Optional[Candidate]:
        # The listing links a PDF for few repealed acts (34 of 298 on 2026-09-15), but every repealed act's page
        # serves one at <path>&ViewType=Pdf (checked by HEAD on AA1987: HTTP 200, 24,745 bytes).
        pdf = row.pdf_path or (row.path + ("&" if "?" in row.path else "?") + "ViewType=Pdf")
        name = row.title
        if _norm(row.title) in duplicate_titles:      # the engine keys its id map on the name: keep two acts apart
            name = f"{row.title} [{row.code}, repealed {row.repeal_date or 'undated'}]"
        cand = Candidate(url=self.root + pdf, economy="SG", law_name_guess=name, law_number_guess=row.number,
                         in_force_status="Repealed")
        cand.contract_meta = {
            "portal": "sg-sso", "discovery_path": "browse_listing", "portal_id": row.code, "law_number": row.number,
            "law_name_portal": row.title, "document_kind": "principal_act", "text_version": "consolidation",
            "version_as_at": row.doc_date, "version_source": "portal_listing" if row.doc_date else None,
            "repealed_on": row.repeal_date, "language": "eng", "language_source": "portal_default",
            "legal_status": "repealed", "status_source": "portal_listing", "in_force_status": "Repealed",
            "crawl_flags": [], "review_flags": [],
        }
        return cand

    def _acts_supp_candidate(self, row: ListedLaw, current: dict[str, ListedLaw]) -> Optional[Candidate]:
        """An Acts Supplement entry: an amending act is fetched as published (decision 13's rule, applied to SSO); a
        new principal act is recorded only when the Current listing carries its consolidated text, and fetched as
        enacted when it does not yet (an uncommenced act, or one the listing has not caught up with)."""
        if not row.pdf_path:
            return None
        amending = bool(_AMENDING_TITLE.search(row.title))
        if not amending and _norm(row.title) in {_norm(r.title) for r in current.values()}:
            return None
        cand = Candidate(url=self.root + row.pdf_path, economy="SG", law_name_guess=row.title, law_number_guess=row.number,
                         publication_date=row.doc_date, in_force_status=None)
        cand.contract_meta = {
            "portal": "sg-sso", "discovery_path": "acts_supplement", "portal_id": row.code, "law_number": row.number,
            "law_name_portal": row.title, "document_kind": "amending_act" if amending else "principal_act",
            "text_version": "as_enacted", "published_on": row.doc_date, "principal_law_number": None,
            "principal_link_source": None, "language": "eng", "language_source": "portal_default",
            "legal_status": "unknown", "status_source": None, "crawl_flags": [],
            "review_flags": ["principal_unlinked"] if amending else ["not_in_current_listing"],
        }
        return cand

    def _sl_candidate(self, sl: ListedSl, code: str, parent: ListedLaw, law: Optional[dict] = None) -> Optional[Candidate]:
        if not sl.pdf_path:
            return None
        inds = (law or {}).get("indicators", []) or []
        cand = Candidate(url=self.root + sl.pdf_path, economy="SG", law_name_guess=(law or {}).get("law_name") or sl.title,
                         law_number_guess=sl.number, pillar_hint=pillar_hint_for(inds) if inds else None,
                         indicator_hints=(",".join(inds) or None), publication_date=sl.doc_date, in_force_status="Current")
        cand.contract_meta = {
            "portal": "sg-sso", "discovery_path": "seed" if law else "subsidiary_list",
            "seed_provenance": (law or {}).get("provenance"), "portal_id": sl.code, "law_number": sl.number,
            "law_name_portal": sl.title, "document_kind": "subsidiary_legislation", "text_version": "consolidation",
            "version_as_at": sl.doc_date, "version_source": "portal_listing" if sl.doc_date else None,
            "principal_law_number": (self.details.get(code).original_number if self.details.get(code) else None),
            "principal_portal_id": code, "principal_link_source": "portal_listing",
            "language": "eng", "language_source": "portal_default", "legal_status": "in_force",
            "status_source": "portal_listing", "in_force_status": "Current", "crawl_flags": [], "review_flags": [],
        }
        return cand

    def _plain_seed(self, law: dict, kind: Optional[str]) -> Candidate:
        inds = law.get("indicators", []) or []
        url = law["url"]
        m = _SSO_ACT_RE.search(url)
        if m:                                              # an SSO seed takes the PDF address the crawl will cite
            base = url.split("?", 1)[0].split("#", 1)[0]
            keep = re.search(r"[?&](DocDate=\d{8})", url)
            url = append_query(base, (keep.group(1) + "&" if keep else "") + "ViewType=Pdf")
        if kind is None:
            kind = ({"Acts-Supp": "amending_act", "SL": "subsidiary_legislation", "SL-Supp": "subsidiary_legislation",
                     "Act": "principal_act"}.get(m.group(1)) if m else "agency_or_other")
        code = act_code(url) or self._sso_code(url)
        cand = Candidate(url=url, economy="SG", law_name_guess=law["law_name"], law_number_guess=law.get("law_number") or None,
                         pillar_hint=pillar_hint_for(inds), indicator_hints=(",".join(inds) or None), in_force_status=None)
        cand.contract_meta = {
            "portal": "sg-sso" if _SSO_ACT_RE.search(url) else urlparse(url).hostname, "discovery_path": "seed",
            "seed_provenance": law.get("provenance"), "portal_id": code, "law_number": law.get("law_number") or None,
            "document_kind": kind, "language": "eng", "language_source": "registry", "legal_status": "unknown",
            "status_source": None, "crawl_flags": [], "review_flags": ["status_unknown"],
        }
        return cand

    # --- the links-file frontier ---------------------------------------------------------
    def _discover_from_links_file(self, pillars: list[int], scope: str, client: PacedClient, fetcher=None) -> list[Candidate]:
        from ..my_gazette.catalogue import candidate_from_row, read_documents
        from .catalogue import cfg_fingerprint
        path = str(self._setting("links_file", "") or "")
        if not path:
            raise ValueError("sso.frontier is links_file but sso.links_file / SSO_LINKS_FILE is not set")
        rows, meta = read_documents(path)
        if meta.get("cfg_sha256") and meta["cfg_sha256"] != cfg_fingerprint(self.cfg):
            raise ValueError(f"link file {path} was built from a different registry: rebuild it with sg_sso.catalogue")
        if not meta.get("cfg_sha256"):
            self._warn(f"link file {path} carries no registry fingerprint")
        self.frontier_meta = {"links_file": path, **{k: meta.get(k) for k in ("generated_at", "counts", "scraper_sha256")}}
        sso_ok = True
        try:
            self._check_robots(client)
        except Exception as e:  # noqa: BLE001 — robots.txt unreadable: SSO rows are dropped, other hosts stay
            self.sso_error = f"{type(e).__name__}: {e}"
            self._warn(f"SSO UNAVAILABLE ({self.sso_error}); only rows on other hosts are served")
            sso_ok = False
        _warn_engine_delay(self, fetcher, client)
        picked: dict[str, Candidate] = {}
        dropped = 0
        for row in rows:
            if scope not in (row.get("scopes") or []):
                continue
            if not sso_ok and (urlparse(row["url"]).hostname or "").lower() == _HOST:
                dropped += 1
                continue
            if client.robots is not None and not client.robots.allowed(row["url"]):
                dropped += 1
                continue
            picked.setdefault(row["url"], candidate_from_row(row))
        message = (f"frontier links_file {path} generated {meta.get('generated_at')}: {len(picked)} of {len(rows)} rows "
                   f"in scope {scope}; {dropped} dropped (robots.txt or SSO unavailable)")
        self.notes.insert(0, message)
        print(f"[crawl] SG: {message}", flush=True)
        self.inventory = [InventoryItem(economy="SG", law_name=c.law_name_guess, url=c.url, law_number=c.law_number_guess,
                                        source="links_file") for c in picked.values()]
        self._finish(client)
        if not picked:
            raise RuntimeError(f"SG link file {path} selected no candidates for scope {scope}")
        return list(picked.values())

    # --- Round 1 helpers kept for the seed scope and the inventory artefact ------------------
    def _seed_candidates(self, pillars: list[int]) -> list[Candidate]:
        out: list[Candidate] = []
        for law in self.cfg.get("seed_laws", []) or []:
            inds = law.get("indicators", []) or []
            if pillars and not any(indicator_pillar(i) in pillars for i in inds):
                continue
            out.append(self._plain_seed(law, None))
        return out

    def _seed_inventory(self, pillars: list[int]) -> list[InventoryItem]:
        items = []
        for law in self.cfg.get("seed_laws", []) or []:
            inds = law.get("indicators", []) or []
            if pillars and not any(indicator_pillar(i) in pillars for i in inds):
                continue
            items.append(InventoryItem(economy="SG", law_name=law["law_name"], url=law["url"],
                                       law_number=(law.get("law_number") or None), source="seed", relevant=True))
        return items

    def harvest_inventory(self, fetcher) -> list[InventoryItem]:
        client = self._get_client(fetcher)
        self._open_sso(client)
        items = [InventoryItem(economy="SG", law_name=r.title, url=ROOT + r.path, source="browse")
                 for r in self.listed.get("current", [])]
        self._mark_relevance(items)
        self.inventory = items
        return items

    def _mark_relevance(self, items: list[InventoryItem]) -> None:
        for it in items:
            low = it.law_name.lower()
            matched = sorted(p for p in self._phrases if p in low)
            if matched:
                it.relevant = True
                it.matched_terms = matched

    # --- fetch planning (Round 1, unchanged) ---------------------------------------------
    def build_plans(self, cand: Candidate, forms: str = "both") -> list[FetchPlan]:
        url = cand.url
        if _SSO_ACT_RE.search(url):
            base = url.split("?", 1)[0].split("#", 1)[0]
            keep = re.search(r"[?&](DocDate=\d{8})", url)          # a listed version: keep its DocDate
            pdf_url = append_query(base, "ViewType=Pdf") if not keep else append_query(base, keep.group(1) + "&ViewType=Pdf")
            html = FetchPlan(url=append_query(base, "WholeDoc=1"), method="playwright", form_factor="html",
                             needs_js=True, wait_selector="div#legisContent", scroll=True, kind="page", citation_url=base)
            pdf = FetchPlan(url=pdf_url, method="requests", form_factor="pdf", needs_js=False, kind="native",
                            citation_url=pdf_url)
            if forms == "pdf":
                return [pdf]
            if forms == "html":
                return [html]
            return [html, pdf]
        if url.lower().split("?", 1)[0].endswith(".pdf"):
            return [FetchPlan(url=url, method="requests", form_factor="pdf", needs_js=False, kind="native", citation_url=url)]
        return [FetchPlan(url=url, method="playwright", form_factor="html", needs_js=True, scroll=True, kind="page",
                          citation_url=url)]

    def extract_anchor(self, cand: Candidate, plan: FetchPlan, content: bytes):
        if plan.form_factor != "html" or not _SSO_ACT_RE.search(plan.url):
            return (None, None)
        html = content.decode("utf-8", "replace")
        best_id, best_score = None, 0
        for prov_id, label in _TOC_RE.findall(html):
            label = label.strip()
            if not label[:1].isdigit():
                continue
            score = len(_tokenize(label) & self._vocab)
            if score > best_score:
                best_score, best_id = score, prov_id
        if best_id and best_score > 0:
            return (f"?ProvIds={best_id}", "query")
        return (None, None)


def _norm(text: Optional[str]) -> str:
    return " ".join(str(text or "").split()).casefold()


def _waf_challenge(resp) -> bool:
    headers = getattr(resp, "headers", None) or {}
    value = headers.get("x-amzn-waf-action") or headers.get("X-Amzn-Waf-Action") or ""
    return str(value).lower() in ("challenge", "captcha")


def _current_version(detail: Optional[ActDetail]):
    """The version the page shows as current: the selected one, else the one in force from the current date."""
    if detail is None or not detail.versions:
        return None
    for v in detail.versions:
        if v.selected:
            return v
    for v in detail.versions:
        if v.valid_from == detail.current_valid_from:
            return v
    return detail.versions[-1]


def _warn_engine_delay(adapter, fetcher, client) -> None:
    """The engine's limiter has one delay for every host (REQUEST_DELAY_MS); the crawl must run at the host's
    Crawl-delay or more (POLICY.md 5.5)."""
    settings = getattr(fetcher, "settings", None)
    delay = getattr(settings, "request_delay_seconds", None)
    if delay is None:
        delay = int(os.environ.get("REQUEST_DELAY_MS", "3000")) / 1000.0
    need = getattr(client, "delay", 0.0) or 0.0
    if need and float(delay) < need:
        adapter._warn(f"the engine waits {float(delay):.1f} s between requests; this host's robots.txt asks for "
                      f"{need:.0f} s: set REQUEST_DELAY_MS={int(need * 1000)} before crawling")


def _tokenize(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z]+", text.lower()) if len(w) > 2 and w not in _STOP}


def _relevance_phrases(cfg: dict[str, Any]) -> set[str]:
    """Adjacent-word bigrams from seed_queries (both words meaningful): the title net of Round 1."""
    phrases: set[str] = set()
    for q in all_query_terms(cfg):
        words = re.findall(r"[a-z]+", q.lower())
        for a, b in zip(words, words[1:]):
            if len(a) > 2 and len(b) > 2 and a not in _STOP and b not in _STOP:
                phrases.add(f"{a} {b}")
    return phrases
