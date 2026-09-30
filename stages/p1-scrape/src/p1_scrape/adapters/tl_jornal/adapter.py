"""Timor-Leste — the Jornal da República (`www.mj.gov.tl/jornal`).

The gazette is the law: Série I carries the acts, and there is no consolidated database, no detail page and no
search worth using. Six category pages carry the whole statute book — 4,846 rows over 2002 to 2026 — so the
catalogue step is **six requests**, and every act's number, title, date and document address come from them
(`../NOTES.md` 1.2).

**One document can carry several acts.** `SERIE_I_NO_13.pdf` holds Lei 3/2026 and Lei 4/2026; a 2026 issue held a
law and a government decree-law. So the crawl's unit is the **issue**, fetched once, and `laws.csv` keeps every
act with the issue it appears in. A row's `contract_meta.contains` names the other acts in the same file, which is
what stage 2 needs to split it (`../NOTES.md` 2.3).

Transport: one paced client, `Crawl-delay: 10` as the portal's robots.txt asks. Documents are native-text PDFs
fetched with `requests`; nothing here needs a browser.

Settings (`sources.yaml`, block `jornal:`; every key can be overridden by JORNAL_<KEY> in the environment):
  frontier        discover | links_file     what discover() does; links_file replays jornal.links_file
  categories      all | <comma list>        which category pages are read (the keys of parse.CATEGORIES)
  document_form   pdf                       the portal offers nothing else
  root            https://www.mj.gov.tl     the host
"""
from __future__ import annotations

import os
import re
from typing import Any, Optional
from urllib.parse import urlparse

from ...inventory import InventoryItem
from ...models import Candidate, FetchPlan
from ...sources import indicator_pillar, pillar_hint_for
from ..base import PortalAdapter
from ..my_gazette.client import LomClient as PacedClient
from ..my_gazette.records import LomThrottled
from ..my_gazette.relevance import TitleRule
from ..my_gazette.robots import RobotsRules, robots_token
from .parse import CATEGORIES, ListedAct, ROOT, category_path, fold, parse_category

_DEFAULT_UA = "RDTII-Rocky-Crawler/0.1 (+polite public-law retrieval)"
_MAX_CONSECUTIVE_FAILURES = 3          # six pages in all: three failures in a row means the portal, not the page


class JornalUnavailable(RuntimeError):
    """The gazette cannot be read on this run: robots.txt disallows, a category failed, or the format changed."""


class TlJornalAdapter(PortalAdapter):
    economy = "TL"

    def __init__(self, cfg: dict[str, Any], client: Optional[PacedClient] = None, today: Optional[str] = None):
        self.cfg = cfg
        self.jornal_cfg: dict = dict(cfg.get("jornal") or {})
        self.title_rule = TitleRule.from_cfg(cfg.get("title_rule"))
        self._client = client
        self._today = today
        self._frontier_override: Optional[str] = None
        self._robots_checked = False
        self._failures_in_a_row = 0
        self.root = ROOT
        self.inventory: list[InventoryItem] = []
        self.inventory_note: Optional[str] = None
        self.notes: list[str] = []
        self.robots_record: dict = {}
        self.jornal_error: Optional[str] = None
        self.listed: dict[str, list[ListedAct]] = {}          # category -> its rows
        self.listing_counts: dict[str, dict] = {}
        self.issues: dict[str, list[ListedAct]] = {}          # document url -> the acts it carries
        self.frontier_meta: Optional[dict] = None

    # --- settings and the client ---------------------------------------------------------

    #: what each setting means when the registry does not say; `effective_settings` resolves against these, so a
    #: run's catalogue_meta.json records the values the code used, not the ones the registry happened to carry
    SETTING_DEFAULTS: dict[str, Any] = {"categories": "all", "document_form": "pdf", "frontier": "discover",
                                        "root": ROOT}

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
            out[key] = value
        return out

    def _setting(self, key: str, default: Any) -> Any:
        env = os.environ.get("JORNAL_" + key.upper())
        return env if env is not None else self.jornal_cfg.get(key, default)

    def _root(self) -> str:
        self.root = str(self._setting("root", ROOT)).rstrip("/")
        return self.root

    def _frontier(self) -> str:
        frontier = str(self._frontier_override or self._setting("frontier", "discover")).strip().lower()
        if frontier not in ("discover", "links_file"):
            raise ValueError(f"jornal.frontier / JORNAL_FRONTIER: {frontier!r} is not discover or links_file")
        return frontier

    def _categories(self) -> list[str]:
        asked = str(self._setting("categories", "all")).strip().lower()
        if asked in ("all", "*", ""):
            return list(CATEGORIES)
        chosen = [c.strip() for c in asked.split(",") if c.strip()]
        unknown = [c for c in chosen if c not in CATEGORIES]
        if unknown:
            raise ValueError(f"jornal.categories names {unknown}, which the portal does not have; "
                             f"the categories are {list(CATEGORIES)}")
        return chosen

    def _get_client(self, fetcher) -> PacedClient:
        if self._client is None:
            settings = getattr(fetcher, "settings", None)
            ua = getattr(settings, "user_agent", None) or os.environ.get("USER_AGENT") or _DEFAULT_UA
            delay = getattr(settings, "request_delay_seconds", None)
            if delay is None:
                delay = int(os.environ.get("REQUEST_DELAY_MS", "10000")) / 1000.0
            self._client = PacedClient(ua, float(delay))
        return self._client

    def _warn(self, message: str) -> None:
        self.notes.append(message)
        print(f"[crawl] TL: WARNING {message}", flush=True)

    # --- reading the portal ---------------------------------------------------------------

    def _check_robots(self, client: PacedClient) -> None:
        """robots.txt first, and its `Crawl-delay: 10` is obeyed (POLICY.md 5.5)."""
        if self._robots_checked:
            return
        url = f"{self._root()}/robots.txt"
        resp = client.get(url)
        record = {"url": url, "status": resp.status_code, "read_at": client.log[-1]["ts"] if client.log else None}
        if resp.status_code == 200:
            rules = RobotsRules.parse((resp.content or b"").decode("utf-8", "replace"), robots_token(client.user_agent))
            client.robots = rules
            record.update({"group": rules.group, "crawl_delay": rules.crawl_delay, "rules": rules.rules[:20]})
            if rules.crawl_delay and rules.crawl_delay > client.delay:
                client.delay = float(rules.crawl_delay)
            record["delay_used_s"] = client.delay
        elif resp.status_code >= 500:
            raise JornalUnavailable(f"the gazette's robots.txt answered HTTP {resp.status_code}; RFC 9309 treats "
                                    f"that as a full disallow (POLICY.md 5.4)")
        elif resp.status_code in (403, 404, 410):
            record["note"] = "no robots.txt: everything allowed, the delay stays the default"
        else:
            raise JornalUnavailable(f"the gazette's robots.txt answered HTTP {resp.status_code}: not a robots.txt "
                                    f"and not an absence; nothing is read through it")
        self.robots_record = record
        self._robots_checked = True

    def _page(self, client: PacedClient, path: str) -> str:
        """One category page. A throttle answer stops the build; three failures in a row stop it too."""
        resp = client.get(self._root() + path, retries=1)
        if resp.status_code != 200:
            self._failures_in_a_row += 1
            if self._failures_in_a_row >= _MAX_CONSECUTIVE_FAILURES:
                raise JornalUnavailable(f"{self._failures_in_a_row} pages in a row failed, the last "
                                        f"HTTP {resp.status_code} for {path}")
            raise JornalUnavailable(f"the gazette answered HTTP {resp.status_code} for {path}")
        self._failures_in_a_row = 0
        return (resp.content or b"").decode("utf-8", "replace")

    def _open_jornal(self, client: PacedClient) -> None:
        """robots.txt, then one request per category page. That is the whole read."""
        self._check_robots(client)
        for category in self._categories():
            page = self._page(client, category_path(CATEGORIES[category]["node"]))
            rows = parse_category(page, category)
            if not rows:
                raise JornalUnavailable(f"the {category} page served no act rows: the page format may have changed")
            self.listed[category] = rows
            with_doc = sum(1 for r in rows if r.document_path)
            self.listing_counts[category] = {"records": len(rows), "with_document": with_doc,
                                             "documents": len({r.document_url for r in rows if r.document_path})}
            if with_doc < len(rows):
                self._warn(f"{category}: {len(rows) - with_doc} of {len(rows)} rows carry no document link; they are "
                           f"listed with no_document_on_portal")

    # --- the candidates --------------------------------------------------------------------

    def _seed_by_number(self, pillars: list[int]) -> tuple[dict[str, dict], list[dict]]:
        """Seeds keyed by `<category>:<number>` (`decretos_leis:12/2024`), and the seeds that name a plain URL."""
        by_number, others = {}, []
        for law in self.cfg.get("seed_laws", []) or []:
            inds = law.get("indicators", []) or []
            # a seed with no indicator tag is a law named on purpose for the list itself, not for an indicator
            if inds and pillars and not any(indicator_pillar(i) in pillars for i in inds):
                continue
            key = str(law.get("portal_key") or "").strip()
            if key:
                by_number[key] = law
            else:
                others.append(law)
        return by_number, others

    def _mark_relevance(self, items: list[InventoryItem]) -> None:
        """The title rule, on accent-folded Portuguese: `Proteção` and `PROTECÇÃO` match one pattern."""
        if self.title_rule is None:
            return
        for it in items:
            groups, _exclusion = self.title_rule.match(fold(it.law_name))
            if groups:
                it.relevant = True
                it.matched_terms = self.title_rule.matched_terms(fold(it.law_name))

    def _relevant_codes(self) -> set[str]:
        items = [InventoryItem(economy="TL", law_name=r.title, url=r.document_url or "", law_number=r.number,
                               listing_date=r.published_on, source="browse")
                 for rows in self.listed.values() for r in rows]
        self._mark_relevance(items)
        by_title = {(it.law_name, it.law_number) for it in items if it.relevant}
        return {r.code for rows in self.listed.values() for r in rows if (r.title, r.number) in by_title}

    def _build_candidates(self, pillars: list[int], scope: str) -> dict[str, Candidate]:
        """One candidate per **issue**, because one PDF can carry several acts."""
        seeds, _others = self._seed_by_number(pillars)
        relevant = self._relevant_codes()
        self.issues = {}
        for category, rows in self.listed.items():
            for row in rows:
                if row.document_url:
                    self.issues.setdefault(row.document_url, []).append(row)

        picked: dict[str, Candidate] = {}
        for url, acts in self.issues.items():
            seed_acts = [a for a in acts if f"{a.category}:{a.number}" in seeds]
            # a seeded issue is named after the act we seeded, not after whichever act leads the issue: the seed
            # is the reason the document is fetched, and its name is the one a reader expects to see
            lead = seed_acts[0] if seed_acts else self._lead_act(acts)
            seed_hits = [seeds[f"{a.category}:{a.number}"] for a in seed_acts]
            is_seed = bool(seed_hits)
            is_relevant = is_seed or any(a.code in relevant for a in acts)
            if scope == "seed" and not is_seed:
                continue
            if scope == "relevant" and not is_relevant:
                continue
            law = seed_hits[0] if seed_hits else None
            inds = (law or {}).get("indicators", []) or []
            cand = Candidate(
                url=url, economy="TL", law_name_guess=lead.title,
                law_number_guess=lead.number, publication_date=lead.published_on,
                pillar_hint=pillar_hint_for(inds) if inds else None,
                indicator_hints=(",".join(inds) or None) if inds else None,
                seed_query=None, expect_scanned=False, law_slug=lead.code.lower(),
            )
            cand.contract_meta = self._meta(lead, acts, is_seed=is_seed, law=law)
            picked[url] = cand
        return picked

    @staticmethod
    def _lead_act(acts: list[ListedAct]) -> ListedAct:
        """Which act names the issue: a principal act first, then the earliest number."""
        order = {"principal_act": 0, "amending_act": 1, "subsidiary_legislation": 2, "agency_or_other": 3}
        return sorted(acts, key=lambda a: (order.get(a.document_kind, 4), a.published_on or "", a.code))[0]

    def _meta(self, lead: ListedAct, acts: list[ListedAct], is_seed: bool, law: Optional[dict]) -> dict:
        flags: list[str] = []
        if len(acts) > 1:
            flags.append("several_acts_in_one_document")
        if not lead.number:
            flags.append("law_number_unknown")
        if lead.amends:
            flags.append("amends_another_act")
        host = urlparse(lead.document_url or "").hostname or ""
        if host and host not in (urlparse(self._root()).hostname or ""):
            # a handful of rows point at the gazette's former domain, www.jornal.gov.tl, which no longer answers
            flags.append("document_on_another_host")
        return {
            "portal": urlparse(self._root()).hostname,
            "portal_id": lead.code,
            "law_number": lead.number,
            "law_name_portal": lead.title,
            "document_kind": lead.document_kind,
            "principal_law_number": lead.amends,
            "published_on": lead.published_on,
            "version_as_at": None,                 # the gazette publishes as made; there is no consolidated text
            "legal_status": "unknown",             # the portal states none (`../NOTES.md` 1.3)
            "status_source": None,
            "language": "por",
            "language_source": "portal",
            "category": lead.category,
            "category_label": CATEGORIES[lead.category]["label"],
            "contains": [a.code for a in sorted(acts, key=lambda a: a.code)],
            "contains_titles": [a.title for a in sorted(acts, key=lambda a: a.code)][:12],
            "discovery_path": "seed" if is_seed else "browse",
            "seed_provenance": (law or {}).get("provenance"),
            "crawl_flags": [],
            "review_flags": flags,
        }

    # --- the interface ----------------------------------------------------------------------

    def discover(self, pillars: list[int], scope: str = "relevant", fetcher=None) -> list[Candidate]:
        client = self._get_client(fetcher)
        if self._frontier() == "links_file":
            return self._discover_from_links_file(pillars, scope, client, fetcher)
        self._open_jornal(client)
        picked = self._build_candidates(pillars, scope)
        self.inventory = [InventoryItem(economy="TL", law_name=r.title, url=r.document_url or "", law_number=r.number,
                                        listing_date=r.published_on, source="browse")
                          for rows in self.listed.values() for r in rows]
        self._mark_relevance(self.inventory)
        self._finish(client)
        return list(picked.values())

    def harvest_inventory(self, fetcher) -> list[InventoryItem]:
        client = self._get_client(fetcher)
        self._open_jornal(client)
        self.inventory = [InventoryItem(economy="TL", law_name=r.title, url=r.document_url or "", law_number=r.number,
                                        listing_date=r.published_on, source="browse")
                          for rows in self.listed.values() for r in rows]
        self._mark_relevance(self.inventory)
        return self.inventory

    def _finish(self, client: PacedClient) -> None:
        parts = ["Jornal categories: " + "; ".join(f"{k} {v['records']} rows, {v['documents']} documents"
                                                   for k, v in self.listing_counts.items())]
        parts.append(f"{len(self.issues)} distinct document(s); {len(client.log)} discovery request(s)")
        self.inventory_note = "; ".join(parts + self.notes)

    def _discover_from_links_file(self, pillars: list[int], scope: str, client: PacedClient, fetcher=None) -> list[Candidate]:
        from ..my_gazette.catalogue import candidate_from_row, read_documents
        from .catalogue import cfg_fingerprint
        path = str(self._setting("links_file", "") or "")
        if not path:
            raise ValueError("jornal.frontier is links_file but jornal.links_file / JORNAL_LINKS_FILE is not set")
        rows, meta = read_documents(path)
        if meta.get("cfg_sha256") and meta["cfg_sha256"] != cfg_fingerprint(self.cfg):
            raise ValueError(f"link file {path} was built from a different registry: rebuild it with tl_jornal.catalogue")
        if not meta.get("cfg_sha256"):
            self._warn(f"link file {path} carries no registry fingerprint")
        self.frontier_meta = {"links_file": path, **{k: meta.get(k) for k in ("generated_at", "counts", "scraper_sha256")}}
        try:
            self._check_robots(client)
        except Exception as e:  # noqa: BLE001 — robots unreadable: say so loudly and serve nothing
            self.jornal_error = f"{type(e).__name__}: {e}"
            self._warn(f"JORNAL UNAVAILABLE ({self.jornal_error}); no row is served")
            return []
        out = []
        for row in rows:
            if scope != "all" and scope not in (row.get("scopes") or ["all"]):
                continue
            cand = candidate_from_row(row)
            if client.robots is not None and not client.robots.allowed(urlparse(cand.url).path or "/"):
                continue
            out.append(cand)
        self.inventory_note = (f"frontier links_file {path} generated {meta.get('generated_at')}: "
                               f"{len(out)} of {len(rows)} rows in scope {scope}")
        return out

    def build_plans(self, cand: Candidate, forms: str = "both") -> list[FetchPlan]:
        """Every document is a native-text PDF fetched with `requests`; the portal offers no other form."""
        url = cand.url
        if forms == "html":
            return []
        return [FetchPlan(url=url, method="requests", form_factor="pdf", needs_js=False, kind="native",
                          citation_url=url)]


def _live(row: ListedAct) -> bool:
    """A row the portal still lists. The gazette never withdraws an issue, so this is always true today."""
    return bool(row.document_path)
