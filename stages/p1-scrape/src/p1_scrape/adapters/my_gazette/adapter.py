"""MyGazetteAdapter: Laws of Malaysia discovery and fetch planning."""
from __future__ import annotations

import math
import os
import re
from datetime import date
from typing import Any, Optional
from urllib.parse import unquote, urlparse

from ...inventory import InventoryItem
from ...models import Candidate, FetchPlan
from ...sources import indicator_pillar, pillar_hint_for
from ..base import PortalAdapter
from .client import LomClient
from .parse import (
    _LISTINGS, _LOM, _TEXT_VERSION, _a_number_int, _act_key, _act_number, _json_or_text, _law_number,
    _clean, _portal_label, _positive_int, _pu_key, _timeline_entry_date, _timeline_entry_for, _title_year,
    all_dates, amending_base_title, amendment_status, choose_document, choose_principal_document,
    datatables_form, decrypt_listing, document_as_at, extract_response_key, iso_date, parse_amendment,
    parse_principal, parse_timeline, principal_status, principal_title_key, pu_b_refs,
)
from .records import (
    AmendingAct, LomThrottled, LomUnavailable, PrincipalAct, TimelineEntry,
)
from .relevance import TitleRule, _relevance_phrases
from .robots import RobotsRules

_LOM_HOST = "lom.agc.gov.my"
_WHITELIST = ("cyrilla.org", "commonlii.org", "um.edu.my")
_DOC_PID = re.compile(r"/(\d+)_B[IM]/")


def _live(p: PrincipalAct) -> bool:
    return p.status_kind not in ("repealed", "superseded")


_DEFAULT_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
               "Chrome/120.0.0.0 Safari/537.36 RDTII-Rocky-Crawler/0.1 (+polite public-law retrieval)")


class MyGazetteAdapter(PortalAdapter):
    economy = "MY"

    def __init__(self, cfg: dict[str, Any], client: Optional[LomClient] = None,
                 today: Optional[str] = None):
        self.cfg = cfg
        self.lom_cfg: dict[str, Any] = dict(cfg.get("lom") or {})
        self._phrases = _relevance_phrases(cfg)
        self._client = client
        self._today = today or date.today().isoformat()
        self.inventory: list[InventoryItem] = []
        self.inventory_note: Optional[str] = None
        self.principals: dict[str, PrincipalAct] = {}
        self.amendments: dict[str, AmendingAct] = {}
        self.timelines: dict[str, list[TimelineEntry]] = {}             # principal act_no -> entries
        self.amendment_timelines: dict[str, list[TimelineEntry]] = {}   # A-number -> entries
        self._timelines_read = 0                                       # for the progress line
        self.notes: list[str] = []
        self.lom_error: Optional[str] = None
        self.robots_record: Optional[dict] = None
        self.host_min_delay: dict[str, float] = {}
        self.last_request_at: dict[str, float] = {}
        self.listing_counts: dict[str, dict] = {}
        self.listing_floor: Optional[str] = None      # ISO publication date of the lowest A-number listed
        self._listing_key: Optional[str] = None        # SEARCH_RESPONSE_KEY of the last listing page read
        self._robots_checked = False
        self._terms: dict[str, str] = {}
        self._links_cache: Optional[tuple[int, dict, dict]] = None
        self._title_index: Optional[dict[str, list[PrincipalAct]]] = None
        # Destinations come from the registry (sources.yaml lom.root, lom.listings, portals.reputable_fallback);
        # the constants are only defaults. Document URLs in listing replies are paths under the same root.
        self.root = str(self.lom_cfg.get("root") or _LOM).rstrip("/")
        self.host = (urlparse(self.root).hostname or _LOM_HOST).lower()
        listings = self.lom_cfg.get("listings") or {}
        self.listings = {kind: (str((listings.get(kind) or {}).get("page") or page),
                                str((listings.get(kind) or {}).get("endpoint") or endpoint))
                         for kind, (page, endpoint) in _LISTINGS.items()}
        fallback = (cfg.get("portals") or {}).get("reputable_fallback")
        self.whitelist = _WHITELIST if fallback is None else tuple(str(x).lstrip("*.") for x in fallback)
        self.title_rule = TitleRule.from_cfg(cfg.get("title_rule"))
        self._rule_cache: dict[str, tuple[list[str], Optional[str]]] = {}
        self._amends_cache: Optional[tuple[int, dict, dict]] = None
        self._frontier_override: Optional[str] = None      # set by scraper.catalogue: a build always discovers
        self.frontier_meta: Optional[dict] = None

    @property
    def discovery_log(self) -> list[dict]:
        """Every discovery request: ts, method, url, status, bytes, waited_s, and location/error/attempt."""
        return self._client.log if self._client is not None else []

    # --- configuration -------------------------------------------------------------------

    #: what each setting means when the registry does not say; `effective_settings` resolves against these, so a
    #: run's catalogue_meta.json records the values the code used, not the ones the registry happened to carry
    SETTING_DEFAULTS: dict[str, Any] = {"timeline": "seed", "subsidiary_acts": "none", "subsidiary_series": ["P.U. (A)"],
        "subsidiary_max_per_act": 25, "document_languages": ["eng", "msa"], "frontier": "discover",}

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
        env = os.environ.get("LOM_" + key.upper())
        return env if env is not None else self.lom_cfg.get(key, default)

    def _bool_setting(self, key: str, default: bool) -> bool:
        value = self._setting(key, default)
        if isinstance(value, bool):
            return value
        text = str(value).strip().lower()
        if text in {"1", "true", "yes", "on"}:
            return True
        if text in {"0", "false", "no", "off"}:
            return False
        raise ValueError(f"lom.{key} / LOM_{key.upper()}: {value!r} is not a yes/no value")

    def _int_setting(self, key: str, default: int, minimum: int = 0) -> int:
        value = int(self._setting(key, default))
        if value < minimum:
            raise ValueError(f"lom.{key} / LOM_{key.upper()}: {value} is below {minimum}")
        return value

    def _list_setting(self, key: str, default: list[str]) -> list[str]:
        value = self._setting(key, default)
        if isinstance(value, str):
            value = [x.strip() for x in value.split(",") if x.strip()]
        return list(value)

    def _timeline_policy(self) -> str:
        """Whose detail-page timelines are read: seed acts, seed acts plus acts the title rule selects, every act
        in scope, or none."""
        policy = str(self._setting("timeline", "seed")).strip().lower()
        if policy not in ("seed", "rule", "all", "none"):
            raise ValueError(f"lom.timeline / LOM_TIMELINE: {policy!r} is not seed, rule, all or none")
        if policy == "rule" and self.title_rule is None:
            raise ValueError("lom.timeline is 'rule' but the registry has no title_rule")
        return policy

    def _subsidiary_policy(self) -> str:
        """Whose timeline subsidiary legislation is fetched: none, seed acts, core-rule acts (the title rule's
        core groups, seeds included when they match), or every rule act and seed."""
        if "subsidiary_acts" in self.lom_cfg or os.environ.get("LOM_SUBSIDIARY_ACTS") is not None:
            policy = str(self._setting("subsidiary_acts", "none")).strip().lower()
        elif "subsidiary_from_timeline" in self.lom_cfg or os.environ.get("LOM_SUBSIDIARY_FROM_TIMELINE") is not None:
            policy = "seed" if self._bool_setting("subsidiary_from_timeline", False) else "none"
        else:
            policy = "none"
        if policy not in ("none", "seed", "core", "rule"):
            raise ValueError(f"lom.subsidiary_acts / LOM_SUBSIDIARY_ACTS: {policy!r} is not none, seed, core or rule")
        if policy in ("core", "rule") and self.title_rule is None:
            raise ValueError(f"lom.subsidiary_acts is {policy!r} but the registry has no title_rule")
        return policy

    def _frontier(self) -> str:
        """discover: read the portal now. links_file: crawl the rows of a link file built earlier."""
        frontier = str(self._frontier_override or self._setting("frontier", "discover")).strip().lower()
        if frontier not in ("discover", "links_file"):
            raise ValueError(f"lom.frontier / LOM_FRONTIER: {frontier!r} is not discover or links_file")
        return frontier

    def _languages(self) -> list[str]:
        return self._list_setting("document_languages", ["eng", "msa"])

    def _get_client(self, fetcher) -> LomClient:
        if self._client is None:
            settings = getattr(fetcher, "settings", None)
            ua = getattr(settings, "user_agent", None) or os.environ.get("USER_AGENT") or _DEFAULT_UA
            delay = getattr(settings, "request_delay_seconds", None)
            if delay is None:
                delay = int(os.environ.get("REQUEST_DELAY_MS", "3000")) / 1000.0
            self._client = LomClient(ua, float(delay))
        return self._client

    def _warn(self, message: str) -> None:
        """A run note that is also printed: the orchestrator narrates notes only for a non-empty inventory."""
        self.notes.append(message)
        print(f"[crawl] MY: WARNING {message}", flush=True)

    # --- discovery -----------------------------------------------------------------------
    def discover(self, pillars: list[int], scope: str = "relevant", fetcher=None) -> list[Candidate]:
        self._check_settings()          # a bad setting is a configuration error, not a lom outage
        client = self._get_client(fetcher)
        if self._frontier() == "links_file":
            return self._discover_from_links_file(pillars, scope, client, fetcher)
        lom_ok = True
        try:
            self._open_lom(client)
        except Exception as e:  # noqa: BLE001 — robots.txt, network, format change: lom is out, the seeds stay
            lom_ok = self._lom_failed(e)
        try:
            picked = self._build_candidates(pillars, scope, client, lom_ok)
        except LomThrottled as e:
            self._lom_failed(e)
            picked = self._build_candidates(pillars, scope, client, lom_ok=False)
        self._drop_robots_disallowed(picked, client)
        self._warn_engine_cap(scope, picked, fetcher)
        self._finish(client)
        if not picked:
            raise RuntimeError("MY discovery selected no candidates"
                               + (f" (lom unavailable: {self.lom_error})" if self.lom_error else ""))
        return list(picked.values())

    def _warn_engine_cap(self, scope: str, picked: dict[str, Candidate], fetcher) -> None:
        """The Round 1 engine keeps only the first MAX_CANDIDATES_PER_ECONOMY candidates of scope relevant."""
        cap = getattr(getattr(fetcher, "settings", None), "max_candidates_per_economy", None)
        if scope == "relevant" and cap and len(picked) > cap:
            cut = list(picked.values())[cap:]
            acts = sum(1 for c in cut if c.contract_meta.get("document_kind") == "principal_act")
            self._warn(f"scope relevant holds {len(picked)} candidates; the engine keeps the first {cap} and cuts "
                       f"{len(cut)} ({acts} principal acts). Set MAX_CANDIDATES_PER_ECONOMY=0 for no cap")

    def _check_settings(self) -> None:
        self._timeline_policy()
        self._subsidiary_policy()
        self._frontier()
        self._int_setting("listing_page_size", 500, minimum=1)
        self._int_setting("subsidiary_max_per_act", 25)
        if not self._languages():
            raise ValueError("lom.document_languages / LOM_DOCUMENT_LANGUAGES is empty")

    def _open_lom(self, client: LomClient) -> None:
        self._check_robots(client)
        self._load_listings(client)

    # --- the title rule ------------------------------------------------------------------
    def _rule_match(self, p: PrincipalAct) -> tuple[list[str], Optional[str]]:
        if self.title_rule is None:
            return [], None
        if p.act_no not in self._rule_cache:
            self._rule_cache[p.act_no] = self.title_rule.match(p.title_bi, p.title_bm)
        return self._rule_cache[p.act_no]

    def _rule_act(self, p: PrincipalAct) -> bool:
        """The title rule selects p, and the listing does not mark it repealed or superseded."""
        return bool(self._rule_match(p)[0]) and _live(p)

    def _priority_acts(self) -> set[str]:
        seeds = {_act_number(law.get("law_number", "")) for law in self.cfg.get("seed_laws", []) or []}
        return {a for a in seeds if a} | {q.act_no for q in self.principals.values() if self._rule_act(q)}

    def _core_act(self, p: PrincipalAct) -> bool:
        groups = self._rule_match(p)[0]
        return self.title_rule is not None and self.title_rule.tier(groups) == "core" and _live(p)

    def _lom_failed(self, error: BaseException) -> bool:
        self.lom_error = f"{type(error).__name__}: {error}"
        self.principals, self.amendments = {}, {}
        self.timelines, self.amendment_timelines = {}, {}
        self._links_cache, self._title_index = None, None
        self.inventory = []
        self._warn(f"LOM UNAVAILABLE ({self.lom_error}). Only seeds outside lom are returned; lom seeds "
                   f"fall back to their registry URLs, flagged secondary_copy where whitelisted.")
        return False

    def _build_candidates(self, pillars: list[int], scope: str, client: LomClient,
                         lom_ok: bool) -> dict[str, Candidate]:
        timeline_policy = self._timeline_policy() if lom_ok else "none"
        if lom_ok:
            self.inventory = self._inventory_items()
            self._mark_relevance(self.inventory)
        self._terms = {it.law_number: ",".join(it.matched_terms) for it in self.inventory if it.matched_terms}
        picked: dict[str, Candidate] = {}

        def add(c: Optional[Candidate]) -> None:
            if c is not None and c.url:
                self._add_candidate(picked, c)

        # 1. Resolve seeds against the listings, without building candidates yet.
        seeds: list[tuple[dict, str, Any]] = []
        for law in self.cfg.get("seed_laws", []) or []:
            inds = law.get("indicators", []) or []
            if pillars and not any(indicator_pillar(i) in pillars for i in inds):
                continue
            seeds.append((law, *self._resolve_seed(law)))
        seed_principals = [obj for _law, kind, obj in seeds if kind == "principal"]
        seed_amendments = {obj.a_number for _law, kind, obj in seeds if kind == "amendment"}

        relevant = {it.law_number for it in self.inventory if it.relevant and it.source == "lom_updated"}
        relevant_principals = [p for p in self.principals.values()
                               if _law_number(p.act_no) in relevant and p not in seed_principals]
        if scope == "seed":
            principals = list(seed_principals)
        elif scope == "relevant":
            principals = seed_principals + relevant_principals
        else:  # all: seeds first, then relevant acts, then the rest, so an interrupted crawl has the important ones
            chosen = set(map(id, seed_principals + relevant_principals))
            principals = seed_principals + relevant_principals + [p for p in self.principals.values()
                                                                  if id(p) not in chosen]

        def reads_timeline(p: PrincipalAct) -> bool:
            return (timeline_policy == "all" or (timeline_policy in ("seed", "rule") and p in seed_principals)
                    or (timeline_policy == "rule" and self._rule_act(p)))

        # 2. Read principal timelines first, so every principal→amendment link below can use them.
        for p in principals:
            if reads_timeline(p):
                self._load_timeline(p, client)

        def read_amendment_timeline(amd: AmendingAct, principal: Optional[PrincipalAct]) -> bool:
            return timeline_policy != "none" and (
                timeline_policy == "all" or amd.a_number in seed_amendments
                or (principal is not None and reads_timeline(principal)))

        # 2b. Amending acts' own timelines (their commencement orders), before any principal is judged
        # stale: an order's per-section dates count toward the as-at comparison.
        if timeline_policy != "none":
            for _law, kind, obj in seeds:
                if kind == "amendment":
                    self._load_amendment_timeline(obj, client)
            for p in principals:
                for amd in self._later_amendments(p):
                    if read_amendment_timeline(amd, p):
                        self._load_amendment_timeline(amd, client)

        # 3. Seed candidates, in registry order.
        for law, kind, obj in seeds:
            inds = law.get("indicators", []) or []
            if kind == "principal":
                cand = self._principal_candidate(obj, law=law, indicators=inds)
                if cand is None:
                    self.notes.append(f"Act {obj.act_no}: listed but no document offered")
                add(cand)
            elif kind == "amendment":
                principal = self._principal_for(obj)
                for cand in self._amendment_candidates(obj, principal, client, law=law,
                                                       read_timeline=read_amendment_timeline(obj, principal)):
                    if cand.contract_meta.get("document_kind") == "amending_act" and inds:
                        cand.contract_meta["review_flags"].append("seed_indicator_hints_dropped")
                    add(cand)
            else:
                add(self._non_lom_seed(law))

        # 4. Principal acts in scope, their later amendments, and the subsidiary legislation the policy asks for.
        subsidiary_policy = self._subsidiary_policy()
        subsidiary_skipped: dict[str, int] = {}
        seed_by_pu: dict[str, dict] = {}
        for law, _kind, _obj in seeds:
            key = _pu_key(law.get("law_number", ""))
            if re.fullmatch(r"PU\([AB]\)\d+/\d{4}", key):
                seed_by_pu[key] = law
            elif key.startswith("PU("):
                self._warn(f"seed '{law.get('law_name')}' names {law.get('law_number')!r} without N/YYYY: it cannot "
                           f"be matched to the portal's copy, so both copies may be fetched")

        def wants_subsidiary(p: PrincipalAct) -> bool:
            return ((subsidiary_policy == "seed" and p in seed_principals)
                    or (subsidiary_policy == "core" and self._core_act(p))
                    or (subsidiary_policy == "rule" and (p in seed_principals or self._rule_act(p))))

        for p in principals:
            is_seed = p in seed_principals
            if not is_seed:
                taken = frozenset(u for u, c in picked.items() if c.contract_meta.get("portal_id") != p.act_no)
                add(self._principal_candidate(p, law=None, indicators=[], taken=taken))
            for amd in self._later_amendments(p):
                for cand in self._amendment_candidates(amd, p, client,
                                                       read_timeline=read_amendment_timeline(amd, p)):
                    add(cand)
            for entry in self._later_timeline_only_amendments(p):
                listed_act = next((q for q, found in self._listed_as_amendment().items()
                                   if any(e is entry for _a, e in found)), None)
                if listed_act is not None:
                    add(self._principal_candidate(self.principals[_act_key(listed_act)], law=None, indicators=[]))
                else:
                    add(self._timeline_amendment_candidate(entry, p))
            listed = [e for e in self.timelines.get(p.act_no, [])
                      if e.log_type == "SUBSIDIARY_LEGISLATION" and e.file_url and e.pu_no]
            if not listed:
                continue
            for entry in {_pu_key(e.pu_no): e for e in reversed(listed) if _pu_key(e.pu_no) in seed_by_pu}.values():
                law = seed_by_pu[_pu_key(entry.pu_no)]      # POLICY.md 2: the statutes portal outranks the agency
                for url in [u for u, c in picked.items() if c.contract_meta.get("discovery_path") == "seed"
                            and c.contract_meta.get("portal") == "other"
                            and _pu_key(c.law_number_guess or "") == _pu_key(entry.pu_no)]:
                    del picked[url]
                add(self._subsidiary_candidate(entry, p, law=law))
            if not wants_subsidiary(p):
                subsidiary_skipped[p.act_no] = len({_pu_key(e.pu_no) for e in listed})
                continue
            for cand in self._subsidiary_candidates(p, listed):
                add(cand)

        if scope == "all":
            for amd in self.amendments.values():
                for cand in self._amendment_candidates(amd, self._principal_for(amd), client, read_timeline=False):
                    add(cand)

        if subsidiary_skipped:
            self.notes.append(f"{sum(subsidiary_skipped.values())} distinct subsidiary instrument(s) listed on "
                              f"{len(subsidiary_skipped)} read timeline(s) not fetched under "
                              f"lom.subsidiary_acts={subsidiary_policy} (decision 12): "
                              + ", ".join(f"Act {k} {v}" for k, v in sorted(subsidiary_skipped.items(),
                                                                          key=lambda kv: -kv[1])[:12]))
        if lom_ok and scope == "all" and timeline_policy != "all":
            unread = sum(1 for p in principals if p.act_no not in self.timelines)
            self.notes.append(f"publication, assent and commencement dates left empty for {unread} principal "
                              f"act(s): their timelines were not read (lom.timeline={timeline_policy})")
        if lom_ok and self.listing_floor:
            early = sum(1 for p in principals if p.act_no not in self.timelines
                        and (iso_date(self._stored_as_at(p)) or "") < self.listing_floor)
            if early:
                self.notes.append(f"{early} principal act(s) are as at a date before the amendment listing "
                                  f"starts ({self.listing_floor}) and had no timeline read: amendments between "
                                  f"their as-at date and then are not checked (review flag "
                                  f"amendment_check_incomplete)")
        return picked

    def _add_candidate(self, picked: dict[str, Candidate], cand: Candidate) -> None:
        """Keep one candidate per URL. A document listed for two acts is kept once and never silently:
        the other act is recorded on it and in the run notes."""
        prev = picked.get(cand.url)
        if prev is None:
            picked[cand.url] = cand
            return
        pm, cm = prev.contract_meta, cand.contract_meta
        if pm.get("portal_id") == cm.get("portal_id") and pm.get("document_kind") == cm.get("document_kind"):
            return
        keep, drop = prev, cand
        # The portal's own repeal marker names which act a shared repeal-notice file belongs to:
        # Acts 811 and 714 both list "Act 714 (Repealed by Act 811).pdf"; it is filed under 714.
        if (pm.get("document_kind") == cm.get("document_kind") == "principal_act"
                and pm.get("discovery_path") != "seed"
                and cm.get("repealed_by") and cm.get("repealed_by") == f"Act {pm.get('portal_id')}"):
            keep, drop = cand, prev
        km, dm = keep.contract_meta, drop.contract_meta
        km.setdefault("also_listed_for", []).append(
            {"portal_id": dm.get("portal_id"), "document_kind": dm.get("document_kind"),
             "law_name_portal": dm.get("law_name_portal"), "legal_status": dm.get("legal_status")})
        km["also_listed_for"].extend(dm.get("also_listed_for", []))
        if "document_shared_with_other_act" not in km["review_flags"]:
            km["review_flags"].append("document_shared_with_other_act")
        self.notes.append(f"{unquote(cand.url.rsplit('/', 1)[-1])}: listed for {_portal_label(pm)} and "
                          f"{_portal_label(cm)}; stored once, under {_portal_label(km)}")
        picked[cand.url] = keep

    def _drop_robots_disallowed(self, picked: dict[str, Candidate], client: LomClient) -> None:
        """The document queue never reads robots.txt, so lom documents it disallows are dropped here."""
        if client.robots is None:
            return
        for url in [u for u in picked if (urlparse(u).hostname or "").lower() in {self.host, _LOM_HOST}]:
            if not client.robots.allowed(url):
                del picked[url]
                self.notes.append(f"{url}: disallowed by lom robots.txt, not fetched")

    def _finish(self, client: LomClient) -> None:
        if client.log:
            client._pace()      # the engine's first lom document request then comes a full delay later
            self.last_request_at = {self.host: client._last} if client._last is not None else {}
        counts = self.listing_counts
        parts = []
        if counts:
            parts.append("lom listings: " + "; ".join(
                f"{k} {v['records']} of {v['total'] if v['total'] is not None else '?'} records"
                for k, v in counts.items()))
        if self.frontier_meta is None:
            parts.append(f"{len(self.principals)} principal acts, {len(self.amendments)} amending acts; "
                         f"{len(self.timelines)} act and {len(self.amendment_timelines)} amendment timeline(s) read")
        parts.append(f"{len(client.log)} discovery request(s)")
        self.inventory_note = "; ".join(parts + self.notes)

    def _discover_from_links_file(self, pillars: list[int], scope: str, client: LomClient,
                                  fetcher=None) -> list[Candidate]:
        """Serve the rows of a link file (links/documents.jsonl) built by scraper.catalogue. The file must have been
        built from this registry. robots.txt is still read first (decision 9), lom rows it disallows are dropped,
        seeds fall back to their registry URLs when lom is unavailable, and a file that yields nothing fails."""
        from .catalogue import candidate_from_row, cfg_fingerprint, read_documents   # catalogue imports this module
        path = str(self._setting("links_file", "") or "")
        if not path:
            raise ValueError("lom.frontier is links_file but lom.links_file / LOM_LINKS_FILE is not set")
        rows, meta = read_documents(path)
        if meta.get("cfg_sha256") and meta["cfg_sha256"] != cfg_fingerprint(self.cfg):
            built = {tuple(k) for k in meta.get("seed_keys") or []}
            now = {(law.get("law_name"), law.get("law_number"), law.get("url")) for law in self.cfg.get("seed_laws") or []}
            raise ValueError(f"link file {path} was built from a different registry (seeds added {sorted(now - built)}, "
                             f"removed {sorted(built - now)}; title rule {meta.get('rule_id')} against "
                             f"{self.title_rule.rule_id if self.title_rule else None}): rebuild it with scraper.catalogue")
        if not meta.get("cfg_sha256"):
            self._warn(f"link file {path} carries no registry fingerprint: its seeds and indicator tags may be stale")
        self.frontier_meta = {"links_file": path, **{k: meta.get(k) for k in ("generated_at", "rule_id", "pillars",
                                                                              "counts", "scraper_sha256")}}
        lom_ok = True
        try:
            self._check_robots(client)
        except Exception as e:  # noqa: BLE001
            lom_ok = self._lom_failed(e)
        if meta.get("pillars") and pillars and sorted(meta["pillars"]) != sorted(pillars):
            self._warn(f"link file was built for pillars {meta['pillars']}, this run asks for {pillars}")
        picked: dict[str, Candidate] = {}
        lom_hosts = {self.host, _LOM_HOST}
        n_lom_down = 0
        for row in rows:
            if scope not in (row.get("scopes") or []):
                continue
            if not lom_ok and (urlparse(row["url"]).hostname or "").lower() in lom_hosts:
                n_lom_down += 1
                continue
            picked.setdefault(row["url"], candidate_from_row(row))
        if not lom_ok:                  # as discover() does: seeds on lom fall back to their registry URLs
            fallback: dict[str, Candidate] = {}
            for law in self.cfg.get("seed_laws", []) or []:
                inds = law.get("indicators", []) or []
                if pillars and not any(indicator_pillar(i) in pillars for i in inds):
                    continue
                cand = self._non_lom_seed(law)
                if cand is not None:
                    fallback.setdefault(cand.url, cand)
            picked = {**fallback, **{u: c for u, c in picked.items() if u not in fallback}}
        before = len(picked)
        self._drop_robots_disallowed(picked, client)
        n_robots = before - len(picked)
        self._warn_engine_cap(scope, picked, fetcher)
        message = (f"frontier links_file {path} generated {meta.get('generated_at')} (rule {meta.get('rule_id')}): "
                   f"{len(picked)} of {len(rows)} rows in scope {scope}; {n_robots} dropped by robots.txt; "
                   f"{n_lom_down} lom rows dropped because lom is unavailable")
        self.notes.insert(0, message)
        print(f"[crawl] MY: {message}", flush=True)
        self._finish(client)
        if not picked:
            raise RuntimeError(f"MY link file {path} selected no candidates for scope {scope}"
                               + (f" (lom unavailable: {self.lom_error})" if self.lom_error else ""))
        return list(picked.values())

    def harvest_inventory(self, fetcher) -> list[InventoryItem]:
        """The full lom inventory from the two listings (kept for callers of the Round 1 API)."""
        client = self._get_client(fetcher)
        self._open_lom(client)
        items = self._inventory_items()
        client._pace()
        return items

    # --- robots.txt ----------------------------------------------------------------------
    def _check_robots(self, client: LomClient) -> None:
        if self._robots_checked:
            return
        url = f"{self.root}/robots.txt"
        resp = client.get(url)
        # Read from the registry only, never the environment: it is a recorded decision (decision 9).
        policy = str(self.lom_cfg.get("robots_5xx", "deny")).strip().lower()
        record = {"url": url, "status": resp.status_code, "checked_at": client.log[-1]["ts"],
                  "robots_5xx": policy, "robots_5xx_source": ("registry lom.robots_5xx"
                                                             if "robots_5xx" in self.lom_cfg else "default")}
        self.robots_record = record
        if resp.status_code >= 500:
            record["applied"] = "allow" if policy == "allow" else "deny"
            if policy != "allow":
                raise LomUnavailable(
                    f"lom robots.txt answered HTTP {resp.status_code}; RFC 9309 treats that as full "
                    f"disallow. Set lom.robots_5xx: allow in sources.yaml only on a recorded decision "
                    f"(POLICY.md §5.4).")
            self.notes.append(f"robots.txt HTTP {resp.status_code}, crawled under the registry's "
                              f"lom.robots_5xx=allow (decision 9)")
        elif resp.status_code == 200:
            rules = RobotsRules.parse(resp.text, client.robots_agent)
            client.robots = rules
            record.update({"applied": "rules", "group": rules.group, "crawl_delay": rules.crawl_delay,
                           "request_rate_s": rules.request_rate})
            declared = rules.min_delay()
            if declared > client.delay:
                self._warn(f"lom robots.txt asks for {declared:g} s between requests; discovery waits that "
                           f"long. The engine's document limiter does not read it yet: set "
                           f"REQUEST_DELAY_MS={int(declared * 1000)} for this run")
                client.delay = declared
                self.host_min_delay = {self.host: declared}
        else:
            record["applied"] = f"no rules (HTTP {resp.status_code})"
        self._robots_checked = True

    # --- listings ------------------------------------------------------------------------
    def _load_listings(self, client: LomClient) -> None:
        if self.principals and self.amendments:
            return
        for rec in self._fetch_listing(client, "updated"):
            p = parse_principal(rec, self.root)
            if p is not None:
                self.principals.setdefault(_act_key(p.act_no), p)
        if not self.principals:
            raise LomUnavailable("lom updated-principal listing returned no acts")
        for rec in self._fetch_listing(client, "amendment"):
            a = parse_amendment(rec, self.root)
            if a is None:
                continue
            kept = self.amendments.setdefault(a.a_number.upper(), a)
            if kept is not a:        # the listing repeats an act once per pairing of its files
                known = {d.url for d in kept.documents}
                kept.documents.extend(d for d in a.documents if d.url not in known)
        if not self.amendments:
            self._warn("lom amendment listing returned no acts: no amending act is linked or fetched, and "
                       "every principal act is marked amendment_check_incomplete")
        else:
            lowest = min(self.amendments.values(), key=lambda a: _a_number_int(a.a_number))
            self.listing_floor = iso_date(lowest.publication)
        self.listing_counts["updated"]["unique"] = len(self.principals)
        self.listing_counts["amendment"]["unique"] = len(self.amendments)
        self._links_cache, self._title_index = None, None

    def _fetch_listing(self, client: LomClient, kind: str) -> list[dict]:
        page_path, endpoint = self.listings[kind]
        page = client.get(f"{self.root}/{page_path}", retries=2)
        if page.status_code != 200:
            raise LomUnavailable(f"lom {page_path} answered HTTP {page.status_code}")
        key = extract_response_key(page.text)
        self._listing_key = key                  # the update check reuses it for the P.U. listings
        size = self._int_setting("listing_page_size", 500, minimum=1)
        records: list[dict] = []
        start, draw, total = 0, 1, None
        max_pages = math.ceil(20000 / size) + 2
        while True:
            resp = client.post(f"{self.root}/{endpoint}", datatables_form(draw, start, size),
                               referer=f"{self.root}/{page_path}", retries=2)
            if resp.status_code != 200:
                raise LomUnavailable(f"lom {endpoint} answered HTTP {resp.status_code}")
            obj = decrypt_listing(_json_or_text(resp), key)
            reported = _positive_int(obj.get("recordsTotal"))
            if reported is not None:
                total = reported
                max_pages = math.ceil(total / size) + 2
            batch = obj.get("records") or obj.get("data") or []
            if not batch:
                break
            records.extend(batch)
            start += len(batch)
            draw += 1
            if total is not None and start >= total:
                break
            if draw > max_pages:
                raise LomUnavailable(f"lom {endpoint}: pagination did not converge after {draw - 1} pages")
        self.listing_counts[kind] = {"records": len(records), "total": total}
        if total is None:
            self.notes.append(f"{kind} listing gave no record total; paged until an empty page "
                              f"({len(records)} records)")
        elif len(records) < total:
            self._warn(f"{kind} listing returned {len(records)} of {total} records")
        return records

    # --- detail-page timelines -----------------------------------------------------------
    def _load_timeline(self, p: PrincipalAct, client: LomClient) -> None:
        if p.act_no in self.timelines:
            return
        link = p.detail_links.get("BI") or p.detail_links.get("BM")
        self.timelines[p.act_no] = self._read_timeline(f"Act {p.act_no}", link, "updated", client)
        self._links_cache = None

    def _load_amendment_timeline(self, amd: AmendingAct, client: LomClient) -> list[TimelineEntry]:
        if amd.a_number not in self.amendment_timelines:
            self.amendment_timelines[amd.a_number] = self._read_timeline(
                f"Act {amd.a_number}", amd.detail_link, "amendment", client)
        return self.amendment_timelines[amd.a_number]

    def _read_timeline(self, label: str, link: Optional[str], listing: str,
                       client: LomClient) -> list[TimelineEntry]:
        if not link:
            self.notes.append(f"{label}: no detail link in listing")
            return []
        try:
            resp = client.get(f"{self.root}/{link}", referer=f"{self.root}/{self.listings[listing][0]}")
        except LomThrottled:
            raise
        except Exception as e:  # noqa: BLE001 — one unreadable timeline is a note, not a failed run
            self.notes.append(f"{label}: timeline not read ({type(e).__name__}: {e})")
            return []
        entries = parse_timeline(resp.text if resp.status_code == 200 else "", self.root)
        if not entries:
            self.notes.append(f"{label}: timeline unreadable (HTTP {resp.status_code})")
        self._timelines_read += 1
        if self._timelines_read % 50 == 0:
            # a build under `timeline: all` sends about 1,970 requests over two hours; without this it printed
            # nothing until the end and looked hung (audit, 2026-09-19)
            print(f"[catalogue] MY: {self._timelines_read} timeline(s) read; {len(client.log)} request(s) so far",
                  flush=True)
        return entries

    # --- linking amendments to principals ------------------------------------------------
    def _links(self) -> tuple[dict[str, tuple[PrincipalAct, str]], dict[str, list[AmendingAct]]]:
        """A-number -> (principal, link source), and principal act_no -> its linked amending acts.
        A read timeline's project id is authoritative; otherwise a unique English title match."""
        key = len(self.timelines)
        if self._links_cache is not None and self._links_cache[0] == key:
            return self._links_cache[1], self._links_cache[2]
        by_project: dict[str, str] = {}
        for act_no, entries in self.timelines.items():
            for e in entries:
                if e.log_type == "AMENDMENTS" and e.project_id:
                    by_project.setdefault(e.project_id, act_no)
        links: dict[str, tuple[PrincipalAct, str]] = {}
        for a in self.amendments.values():
            act_no = by_project.get(a.project_id or "")
            if act_no is not None and _act_key(act_no) in self.principals:
                links[a.a_number] = (self.principals[_act_key(act_no)], "portal_timeline")
                continue
            p = self._title_match(a)
            if p is not None:
                links[a.a_number] = (p, "title_match")
        by_principal: dict[str, list[AmendingAct]] = {}
        for a_number, (p, _src) in links.items():
            by_principal.setdefault(p.act_no, []).append(self.amendments[a_number])
        self._links_cache = (key, links, by_principal)
        return links, by_principal

    def _title_match(self, amd: AmendingAct) -> Optional[PrincipalAct]:
        base = amending_base_title(amd.title_bi)
        if not base:
            return None
        if self._title_index is None:
            index: dict[str, list[PrincipalAct]] = {}
            for p in self.principals.values():
                k = principal_title_key(p.title_bi)
                if k:
                    index.setdefault(k, []).append(p)
            self._title_index = index
        hits = self._title_index.get(principal_title_key(base), [])
        if len(hits) > 1:      # e.g. an act and its repealed predecessor: prefer the one in force,
            year = _title_year(amd.title_bi)          # when it is not younger than the amending act
            hits = [p for p in hits if p.status_kind not in ("repealed", "superseded")
                    and year is not None and (_title_year(p.title_bi) or 9999) <= year]
        return hits[0] if len(hits) == 1 else None

    def _principal_for(self, amd: AmendingAct) -> Optional[PrincipalAct]:
        link = self._links()[0].get(amd.a_number)
        return link[0] if link else None

    def _link_source(self, amd: AmendingAct, p: Optional[PrincipalAct]) -> Optional[str]:
        link = self._links()[0].get(amd.a_number)
        return link[1] if link and p is not None and link[0] is p else None

    def _amendments_of(self, p: PrincipalAct) -> list[AmendingAct]:
        return list(self._links()[1].get(p.act_no, []))

    def _listed_as_amendment(self) -> dict[str, list[tuple[str, TimelineEntry]]]:
        """Principal-listing act_no -> [(amended act_no, entry)], for acts a read timeline lists under
        AMENDMENTS by the project id in the act's current document path, or by the same file.

        This is how the portal shows that a plain-numbered act, such as a Finance Act, amends another act
        (Act 53's timeline lists 48 of 49 Finance Acts). A match means the act's current document is the text
        as enacted. An act AGC has since reprinted has a new file and project id, keeps operative text of its
        own, and stays a principal act (decision 13)."""
        return self._timeline_listings()[0]

    def _listed_on_other_timeline(self) -> dict[str, list[str]]:
        """Repealed, superseded or repeal-notice acts a read timeline lists under AMENDMENTS: flagged, never
        reclassified. A repeal notice filed under a listed project id is not the text as enacted."""
        return self._timeline_listings()[1]

    def _timeline_listings(self) -> tuple[dict[str, list[tuple[str, TimelineEntry]]], dict[str, list[str]]]:
        key = len(self.timelines)
        if self._amends_cache is not None and self._amends_cache[0] == key:
            return self._amends_cache[1], self._amends_cache[2]
        by_pid: dict[str, tuple[str, bool]] = {}
        by_url: dict[str, tuple[str, bool]] = {}
        for q in self.principals.values():
            doc = choose_principal_document(q, self._languages())
            if doc is None:
                continue
            flag_only = not _live(q) or q.status_kind == "partially_repealed" or bool(
                re.search(r"repeal|mansuh", unquote(doc.name), re.I))
            m = _DOC_PID.search(doc.url)
            if m:
                by_pid.setdefault(m.group(1), (q.act_no, flag_only))
            by_url.setdefault(unquote(doc.url), (q.act_no, flag_only))
        out: dict[str, list[tuple[str, TimelineEntry]]] = {}
        flagged: dict[str, list[str]] = {}
        for act_no, entries in self.timelines.items():
            for e in entries:
                if e.log_type != "AMENDMENTS":
                    continue
                hit = by_pid.get(e.project_id or "") or (by_url.get(unquote(e.file_url)) if e.file_url else None)
                if not hit or hit[0] == act_no:
                    continue
                other, flag_only = hit
                if flag_only:
                    if act_no not in flagged.setdefault(other, []):
                        flagged[other].append(act_no)
                elif not any(a == act_no for a, _e in out.get(other, [])):
                    out.setdefault(other, []).append((act_no, e))
        self._amends_cache = (key, out, flagged)
        return out, flagged

    def _timeline_only_amendments(self, p: PrincipalAct) -> list[TimelineEntry]:
        """AMENDMENTS entries on p's timeline with no row in the amendment listing (before A1392)."""
        listed = {a.project_id for a in self.amendments.values() if a.project_id}
        return [e for e in self.timelines.get(p.act_no, [])
                if e.log_type == "AMENDMENTS" and e.file_url and e.project_id not in listed]

    def _stored_as_at(self, p: PrincipalAct) -> Optional[str]:
        """Raw as-at date of the document this adapter will store for p (the listing's other date if
        that document's own edition has none)."""
        doc = choose_principal_document(p, self._languages())
        return (document_as_at(p, doc) if doc else None) or p.as_at_bi or p.as_at_bm

    def _amendment_dates(self, a: AmendingAct) -> list[str]:
        """Every date the portal gives for an amendment taking effect: its commencement field and remark,
        and the remark of its commencement order when that order's timeline entry was read."""
        dates = all_dates(a.commencement_date) + all_dates(a.commencement_remark)
        refs = {_pu_key(r) for r in pu_b_refs(a)}
        for e in self.amendment_timelines.get(a.a_number, []):
            if e.log_type == "SUBSIDIARY_LEGISLATION" and e.pu_no and _pu_key(e.pu_no) in refs:
                dates += all_dates(e.commencement_remark) + all_dates(e.commencement_date)
        return sorted(set(dates))

    def _amendment_view(self, a: AmendingAct, as_at: Optional[str]) -> dict:
        status, _src = amendment_status(a, self._today)
        dates = self._amendment_dates(a) or [d for d in (iso_date(a.publication),) if d]
        after = None if as_at is None else (status == "not_yet_in_force" or not dates or max(dates) > as_at)
        included = [d for d in dates if as_at is not None and d <= as_at] if status != "not_yet_in_force" else []
        return {"amendment": a, "dates": dates, "after": after, "included_dates": included,
                "staged_across_as_at": bool(after and included)}

    def _later_amendments(self, p: PrincipalAct) -> list[AmendingAct]:
        """Amending acts with any listed date after the stored consolidation's as-at date, or not yet in
        force, or with no date at all (POLICY §3.3)."""
        as_at = iso_date(self._stored_as_at(p))
        out = [v["amendment"] for v in (self._amendment_view(a, as_at) for a in self._amendments_of(p))
               if as_at is None or v["after"]]
        return sorted(out, key=lambda a: _a_number_int(a.a_number))

    def _later_timeline_only_amendments(self, p: PrincipalAct) -> list[TimelineEntry]:
        as_at = iso_date(self._stored_as_at(p))
        return [e for e in self._timeline_only_amendments(p)
                if as_at is None or (_timeline_entry_date(e) or "9999") > as_at]

    def _last_incorporated(self, p: PrincipalAct) -> tuple[Optional[str], Optional[str]]:
        """(instrument, year) of the amendment that took effect last on or before the as-at date."""
        as_at = iso_date(self._stored_as_at(p))
        if as_at is None:
            return None, None
        done: list[tuple[str, int, str]] = []
        for a in self._amendments_of(p):
            v = self._amendment_view(a, as_at)
            if v["included_dates"]:
                done.append((max(v["included_dates"]), _a_number_int(a.a_number), a.a_number))
        for q, found in self._listed_as_amendment().items():      # plain-numbered acts, e.g. Finance Acts
            for amended, e in found:
                when = _timeline_entry_date(e)
                if amended == p.act_no and when and when <= as_at:
                    done.append((when, _a_number_int(q), q))
        if not done:
            return None, None
        when, _n, number = max(done, key=lambda t: (t[0], t[1]))
        return _law_number(number), when[:4]

    # --- candidates ----------------------------------------------------------------------
    def _resolve_seed(self, law: dict) -> tuple[str, Any]:
        """('principal', PrincipalAct) | ('amendment', AmendingAct) | ('other', None)."""
        num = _act_number(law.get("law_number", ""))
        if num and num.upper().startswith("A"):
            amd = self.amendments.get(num.upper())
            if amd is not None and amd.documents:
                return "amendment", amd
        elif num:
            p = self.principals.get(_act_key(num))
            if p is not None and p.documents:
                return "principal", p
        return "other", None

    def _principal_candidate(self, p: PrincipalAct, law: Optional[dict], indicators: list[str],
                             taken: frozenset[str] = frozenset()) -> Optional[Candidate]:
        doc = choose_principal_document(p, self._languages(), exclude=taken)
        if doc is None:
            return None
        first_choice = choose_principal_document(p, self._languages())
        as_at_raw = document_as_at(p, doc)
        stored_as_at = iso_date(self._stored_as_at(p))
        entries = self.timelines.get(p.act_no) or []
        original = next((e for e in entries if e.log_type == "ORIGINAL"), None)
        matched_entry = _timeline_entry_for(doc, entries)
        views = [self._amendment_view(a, stored_as_at) for a in self._amendments_of(p)]
        links = self._links()[0]
        later = self._later_amendments(p)
        timeline_only = self._timeline_only_amendments(p)
        later_unlisted = self._later_timeline_only_amendments(p)
        last_instrument, last_year = self._last_incorporated(p)
        status, status_source = principal_status(p)
        check_complete = bool(self.amendments) and (bool(entries) or (
            stored_as_at is not None and self.listing_floor is not None and stored_as_at >= self.listing_floor))

        crawl_flags, review_flags = [], []
        if later or later_unlisted:
            crawl_flags.append("stale_vs_portal")
        if not check_complete:
            review_flags.append("amendment_check_incomplete")
        newest = max((iso_date(document_as_at(p, d)) or "" for d in p.documents), default="")
        if newest and newest > (iso_date(as_at_raw) or ""):
            review_flags.append("newer_version_in_other_language")
        if doc.language not in self._languages()[:1]:
            review_flags.append("preferred_language_unavailable")
        if (doc.language == "eng" and doc.edition == "online"
                and any(d.language == "msa" and d.edition == "printed" for d in p.documents)):
            review_flags.append("english_online_malay_printed")     # decision 14: English first, both official
        amends = self._listed_as_amendment().get(p.act_no, [])
        if amends:
            review_flags.append("listed_as_principal_by_portal")
            if indicators:
                review_flags.append("seed_indicator_hints_dropped")
            indicators = []                                            # amending acts carry no indicator tags
        listed_on = self._listed_on_other_timeline().get(p.act_no, [])
        if listed_on:
            review_flags.append("listed_on_other_timeline")
        if first_choice is not None and doc.url != first_choice.url:
            review_flags.append("newest_document_belongs_to_other_act")
            self.notes.append(f"Act {p.act_no}: its newest listed document is already stored for another act; "
                              f"stored {unquote(doc.name)} instead")

        cand = Candidate(
            url=doc.url, economy="MY",
            law_name_guess=(law or {}).get("law_name") or p.title_bi or p.title_bm or f"Act {p.act_no}",
            law_number_guess=_law_number(p.act_no),
            pillar_hint=(pillar_hint_for(indicators) if indicators else None),
            indicator_hints=(",".join(indicators) or None),
            seed_query=self._terms.get(_law_number(p.act_no)) or None,
            publication_date=(original.publication_date if original else None),
            assent_date=(original.royal_assent_date if original else None),
            commencement_date=(original.commencement_remark or original.commencement_date) if original else None,
            in_force_status=p.status_marker,
        )
        version_as_at = iso_date(as_at_raw)
        rule_groups, rule_exclusion = self._rule_match(p)
        pid_act = {e.project_id: q for q, found in self._listed_as_amendment().items()
                   for a, e in found if a == p.act_no and e.project_id}
        priority = self._priority_acts() if amends else set()
        amended = sorted({a for a, _e in amends}, key=lambda a: (a not in priority, _a_number_int(a)))
        cand.contract_meta = {
            "portal": "my-lom", "discovery_path": "seed" if law else "browse_listing",
            "seed_provenance": (law or {}).get("provenance"),
            "portal_id": p.act_no, "law_name_portal": p.title_bi or p.title_bm,
            "law_number": _law_number(p.act_no),
            "document_kind": "amending_act" if amends else "principal_act",
            "principal_law_number": _law_number(amended[0]) if amended else None,
            "principal_link_source": "portal_timeline" if amended else None,
            "amends": [_law_number(a) for a in amended],
            "listed_on_timeline_of": [_law_number(a) for a in listed_on],
            "title_rule_groups": rule_groups, "title_rule_exclusion": rule_exclusion,
            "title_rule_tier": self.title_rule.tier(rule_groups) if self.title_rule else None,
            "text_version": ("as_enacted" if amends else
                             _TEXT_VERSION.get(matched_entry.log_type, "unknown") if matched_entry
                             else ("reprint" if doc.edition == "online" else None)),
            "timeline_log_type": matched_entry.log_type if matched_entry else None,
            "edition": doc.edition, "online_marker": p.online_marker,
            "language": doc.language, "language_source": "portal_field",
            "version_as_at_raw": as_at_raw, "version_as_at": version_as_at,
            "version_source": "portal_field" if version_as_at else None,
            "legal_status": status, "status_source": status_source, "status_marker": p.status_marker,
            "repealed_by": p.repealed_by, "portal_superseded_by": p.superseded_by,
            "published_on": iso_date(original.publication_date) if original else None,
            "enacted_on": iso_date(original.royal_assent_date) if original else None,
            "linked_amendments": [
                {"law_number": f"Act {v['amendment'].a_number}", "link_source": links[v["amendment"].a_number][1],
                 "dates": v["dates"], "after_as_at": v["after"], "staged_across_as_at": v["staged_across_as_at"]}
                for v in sorted(views, key=lambda v: _a_number_int(v["amendment"].a_number))
            ] + [
                {"law_number": _law_number(pid_act[e.project_id]) if e.project_id in pid_act else None,
                 "link_source": "portal_timeline", "listed_in_amendment_listing": False,
                 "project_id": e.project_id, "dates": [d for d in (_timeline_entry_date(e),) if d],
                 "after_as_at": (None if stored_as_at is None
                                 else (_timeline_entry_date(e) or "9999") > stored_as_at),
                 "file_url": e.file_url}
                for e in timeline_only
            ],
            "amendments_after_as_at": [f"Act {a.a_number}" for a in later] + [
                _law_number(pid_act[e.project_id]) if e.project_id in pid_act else e.file_url for e in later_unlisted],
            "amendment_check_complete": check_complete,
            "amendment_check_from": None if check_complete or entries else self.listing_floor,
            "last_amending_instrument": last_instrument, "last_amended_year": last_year,
            "alternative_documents": [d.url for d in p.documents if d.url != doc.url],
            "timeline_read": bool(entries),
            "crawl_flags": crawl_flags, "review_flags": review_flags,
        }
        return cand

    def _amendment_candidates(self, amd: AmendingAct, principal: Optional[PrincipalAct], client: LomClient,
                              law: Optional[dict] = None, read_timeline: bool = False) -> list[Candidate]:
        """The amending act and, when its own timeline is read, the commencement order(s) its remark cites."""
        doc = choose_document(amd.documents, self._languages())
        if doc is None:
            return []
        timeline = self._load_amendment_timeline(amd, client) if read_timeline else \
            self.amendment_timelines.get(amd.a_number)
        refs = pu_b_refs(amd)
        pool = list(timeline or []) + list(self.timelines.get(principal.act_no, []) if principal else [])
        orders: dict[str, TimelineEntry] = {}
        for e in pool:
            if (e.log_type == "SUBSIDIARY_LEGISLATION" and e.pu_no and e.file_url
                    and _pu_key(e.pu_no) in {_pu_key(r) for r in refs}):
                orders.setdefault(_pu_key(e.pu_no), e)
        unresolved = [r for r in refs if _pu_key(r) not in orders]

        raw_remark = amd.commencement_remark or None
        remark = _clean(raw_remark) or None                  # manifest text is single-line (CONTRACT.md 3.1)
        status, status_source = amendment_status(amd, self._today)
        review_flags = [] if principal else ["principal_unlinked"]
        if unresolved and timeline:
            review_flags.append("commencement_instrument_unresolved")
        cand = Candidate(
            url=doc.url, economy="MY",
            law_name_guess=(law or {}).get("law_name") or amd.title_bi or amd.title_bm or f"Act {amd.a_number}",
            law_number_guess=f"Act {amd.a_number}",
            pillar_hint=None, indicator_hints=None,       # amending acts carry no indicator tags (POLICY §3.2)
            seed_query=self._terms.get(f"Act {amd.a_number}") or None,
            publication_date=amd.publication, assent_date=amd.royal_assent,
            commencement_date=(remark or amd.commencement_date),
            in_force_status=(remark if status in ("not_yet_in_force", "partially_in_force")
                             and status_source == "portal_remark" else None),
        )
        cand.contract_meta = {
            "portal": "my-lom", "discovery_path": "seed" if law else "amendment_list",
            "seed_provenance": (law or {}).get("provenance"),
            "portal_id": amd.a_number, "law_name_portal": amd.title_bi or amd.title_bm,
            "law_number": f"Act {amd.a_number}", "project_id": amd.project_id,
            "document_kind": "amending_act", "text_version": "as_enacted",
            "edition": doc.edition, "language": doc.language, "language_source": "portal_field",
            "principal_law_number": _law_number(principal.act_no) if principal else None,
            "principal_link_source": self._link_source(amd, principal),
            "published_on": iso_date(amd.publication), "enacted_on": iso_date(amd.royal_assent),
            "commenced_on": iso_date(amd.commencement_date), "commencement_note": raw_remark,
            "commencement_dates": self._amendment_dates(amd),
            "commencement_instrument_refs": refs,
            "commencement_instruments_found": [orders[_pu_key(r)].pu_no for r in refs if _pu_key(r) in orders],
            "amendment_timeline_read": bool(timeline),
            "timeline_instruments": [e.pu_no for e in timeline or [] if e.log_type == "SUBSIDIARY_LEGISLATION" and e.pu_no],
            "legal_status": status, "status_source": status_source,
            "alternative_documents": [d.url for d in amd.documents if d.url != doc.url],
            "crawl_flags": [], "review_flags": review_flags,
        }
        out = [cand]
        for ref in refs:
            entry = orders.get(_pu_key(ref))
            if entry is not None:
                out.append(self._commencement_candidate(entry, amd, principal))
        return out

    def _commencement_candidate(self, entry: TimelineEntry, amd: AmendingAct,
                                principal: Optional[PrincipalAct]) -> Candidate:
        cand = Candidate(
            url=entry.file_url, economy="MY",
            law_name_guess=f"{entry.pu_no} commencing Act {amd.a_number}",
            law_number_guess=entry.pu_no, publication_date=entry.publication_date,
            commencement_date=entry.commencement_remark or entry.commencement_date)
        cand.contract_meta = {
            "portal": "my-lom", "discovery_path": "subsidiary_list", "project_id": entry.project_id,
            "portal_id": entry.pu_no, "law_number": entry.pu_no,
            "document_kind": "commencement_instrument", "text_version": "as_enacted",
            "principal_law_number": _law_number(principal.act_no) if principal else None,
            "principal_link_source": self._link_source(amd, principal),
            "commences_law_number": f"Act {amd.a_number}",
            "published_on": iso_date(entry.publication_date),
            "commencement_note": entry.commencement_remark, "commencement_dates": all_dates(entry.commencement_remark),
            "language": None, "language_source": None,
            "legal_status": "unknown", "status_source": None,
            "crawl_flags": [], "review_flags": [] if principal else ["principal_unlinked"],
        }
        return cand

    def _timeline_amendment_candidate(self, entry: TimelineEntry, p: PrincipalAct) -> Candidate:
        """An AMENDMENTS entry on p's timeline that the amendment listing does not carry (before A1392)."""
        when = _timeline_entry_date(entry)
        name = unquote(entry.file_url.rsplit("/", 1)[-1])
        cand = Candidate(
            url=entry.file_url, economy="MY",
            law_name_guess=f"Amendment of Act {p.act_no} ({entry.display_date or when})",   # short: paths < 260
            law_number_guess=None, publication_date=entry.publication_date,
            commencement_date=entry.commencement_remark or entry.commencement_date)
        cand.contract_meta = {
            "portal": "my-lom", "discovery_path": "amendment_list", "project_id": entry.project_id,
            "portal_id": entry.project_id, "document_kind": "amending_act", "text_version": "as_enacted",
            "principal_law_number": _law_number(p.act_no), "principal_link_source": "portal_timeline",
            "amends_title": p.title_bi or p.title_bm,
            "number_in_file_name": (lambda m: f"Act {m.group(0)}" if m else None)(re.search(r"\bA\d{3,4}\b", name)),
            "published_on": iso_date(entry.publication_date), "timeline_date": when,
            "language": None, "language_source": None,
            "legal_status": "unknown", "status_source": None,
            "crawl_flags": [], "review_flags": ["not_in_amendment_listing"],
        }
        return cand

    def _subsidiary_candidates(self, p: PrincipalAct, listed: list[TimelineEntry]) -> list[Candidate]:
        wanted = {_pu_key(s) for s in self._list_setting("subsidiary_series", ["P.U. (A)"])}
        seeded = {_pu_key(law.get("law_number", "")) for law in self.cfg.get("seed_laws", []) or []}
        unique: dict[str, TimelineEntry] = {}
        for e in listed:                          # timelines repeat entries: dedupe by P.U. number first
            if any(_pu_key(e.pu_no).startswith(w) for w in wanted) and _pu_key(e.pu_no) not in seeded:
                unique.setdefault(_pu_key(e.pu_no), e)
        chosen = sorted(unique.values(), key=lambda e: iso_date(e.publication_date or e.date) or "", reverse=True)
        cap = self._int_setting("subsidiary_max_per_act", 25)
        if cap and len(chosen) > cap:   # never a silent cap: the run notes say what was left out
            self.notes.append(f"Act {p.act_no}: {len(chosen)} subsidiary instruments on the timeline, "
                              f"fetching the newest {cap}")
            chosen = chosen[:cap]
        return [self._subsidiary_candidate(e, p) for e in chosen]

    def _subsidiary_candidate(self, entry: TimelineEntry, p: PrincipalAct, law: Optional[dict] = None) -> Candidate:
        """A timeline instrument; with `law`, the seed that names it (its name, tags and provenance are kept)."""
        name = entry.pu_no or f"Subsidiary legislation of Act {p.act_no} ({entry.display_date})"
        inds = (law or {}).get("indicators", []) or []
        cand = Candidate(
            url=entry.file_url, economy="MY",
            law_name_guess=(law or {}).get("law_name") or f"{name} under Act {p.act_no}",   # short: paths < 260
            law_number_guess=entry.pu_no, publication_date=entry.publication_date,
            pillar_hint=(pillar_hint_for(inds) if inds else None), indicator_hints=(",".join(inds) or None),
            commencement_date=entry.commencement_remark or entry.commencement_date)
        cand.contract_meta = {
            "portal": "my-lom", "discovery_path": "seed" if law else "subsidiary_list",
            "seed_provenance": (law or {}).get("provenance"), "project_id": entry.project_id,
            "portal_id": entry.pu_no, "law_number": entry.pu_no,
            "document_kind": "subsidiary_legislation", "text_version": "as_enacted",
            "principal_law_number": _law_number(p.act_no), "principal_link_source": "portal_timeline",
            "published_on": iso_date(entry.publication_date), "commencement_note": entry.commencement_remark,
            "language": None, "language_source": None,
            "legal_status": "unknown", "status_source": None, "crawl_flags": [],
            "review_flags": ["seed_resolved_to_portal"] if law else [],
        }
        return cand

    def _non_lom_seed(self, law: dict) -> Optional[Candidate]:
        """Agency PDFs and pages, as in Round 1; a whitelisted secondary copy is flagged (POLICY §2)."""
        inds = law.get("indicators", []) or []
        primary = law.get("url", "") or ""
        fb = law.get("fallback_url", "") or ""
        flags: list[str] = []
        if primary.lower().split("?", 1)[0].endswith(".pdf") or law.get("form") == "pdf":
            url = primary
        elif primary and not primary.rstrip("/").endswith("agc.gov.my"):
            url = primary
        elif fb and any(w in fb for w in self.whitelist):
            url, flags = fb, ["secondary_copy"]
        else:
            self.notes.append(f"seed '{law.get('law_name')}': no resolvable URL")
            return None
        cand = Candidate(
            url=url, economy="MY", law_name_guess=law["law_name"],
            law_number_guess=(law.get("law_number") or None),
            pillar_hint=pillar_hint_for(inds), indicator_hints=(",".join(inds) or None),
            force_form=(law.get("form") or None))
        cand.contract_meta = {"portal": "other", "discovery_path": "seed",
                              "seed_provenance": law.get("provenance"), "document_kind": None,
                              "language": None, "language_source": None,
                              "legal_status": "unknown", "status_source": None,
                              "crawl_flags": flags, "review_flags": []}
        return cand

    # --- inventory -----------------------------------------------------------------------
    def _inventory_items(self) -> list[InventoryItem]:
        items: list[InventoryItem] = []
        langs = self._languages()
        for p in self.principals.values():
            doc = choose_principal_document(p, langs)
            items.append(InventoryItem(
                economy="MY", law_name=p.title_bi or p.title_bm or f"Act {p.act_no}",
                url=(doc.url if doc else ""), law_number=_law_number(p.act_no),
                listing_date=(document_as_at(p, doc) if doc else None) or p.as_at_bi or p.as_at_bm,
                source="lom_updated", in_force_status=p.status_marker))
        for a in self.amendments.values():
            doc = choose_document(a.documents, langs)
            items.append(InventoryItem(
                economy="MY", law_name=a.title_bi or a.title_bm or f"Act {a.a_number}",
                url=(doc.url if doc else ""), law_number=f"Act {a.a_number}",
                listing_date=a.publication, source="lom_amendment",
                publication_date=a.publication, assent_date=a.royal_assent,
                commencement_date=_clean(a.commencement_remark or a.commencement_date) or None))
        return items

    def _mark_relevance(self, items: list[InventoryItem]) -> None:
        """With a title rule: a principal act is relevant when the rule selects it and it is not repealed or
        superseded; matched_terms are the words the rule matched in the title (seed_query, CONTRACT.md 3.2), and
        the group ids go to contract_meta.title_rule_groups. Without a rule: Round 1's search-term phrases."""
        if self.title_rule is not None:
            by_number = {_law_number(p.act_no): p for p in self.principals.values()}
            for it in items:
                p = by_number.get(it.law_number or "") if it.source == "lom_updated" else None
                if p is not None and self._rule_act(p):
                    it.relevant = True
                    it.matched_terms = self.title_rule.matched_terms(p.title_bi, p.title_bm)
            return
        for it in items:
            matched = sorted(ph for ph in self._phrases if ph in (it.law_name or "").lower())
            if matched:
                it.relevant = True
                it.matched_terms = matched

    # --- fetch planning: MY documents are PDFs ---------------------------------------------
    def build_plans(self, cand: Candidate, forms: str = "both") -> list[FetchPlan]:
        url = cand.url
        if (url.lower().split("?", 1)[0].endswith(".pdf") or "/ilims/upload/" in url
                or cand.force_form == "pdf"):
            return [FetchPlan(url=url, method="requests", form_factor="pdf",
                              needs_js=False, kind="native", citation_url=url)]
        return [FetchPlan(url=url, method="playwright", form_factor="html",
                          needs_js=True, scroll=True, kind="page", citation_url=url)]
