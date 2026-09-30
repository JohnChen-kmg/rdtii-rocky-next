"""Australia — the Federal Register of Legislation (www.legislation.gov.au and its OData API).

The Round 1 adapter's fetch recipe (native PDF; the dated epub for multi-volume acts; a framed capture as the last
resort) with the convention's catalogue step (CONVENTIONS.md section 2): discovery reads the API through one paced
client (every in-force principal Act, then the latest version of each in batches of 18: its dated file, its
compilation number and the amendments it incorporates) and never touches the www host, whose Crawl-delay is 10 s.
The documents come from www at the crawl, at that delay. The crawl replays a link list (register.frontier:
links_file).

Settings (`sources.yaml`, block `register:`; every key can be overridden by REGISTER_<KEY> in the environment):
  frontier          discover | links_file        what discover() does; links_file replays register.links_file / REGISTER_LINKS_FILE
  detail_pages      all | seed | none            whose latest version is read from the API (decision 17: all)
  version_batch     18                           title ids per versions request (an OR-chain of 18 answers 400)
  title_page_size   100                          the API's maximum $top
  max_titles        6000                         a stop on the title harvest
  collection        Act                          the register collection harvested
  document_form     epub | pdf                   the form fetched for a compilation: the dated epub holds every
                                                 volume of every act (decision 18, proposed); the dated PDF exists for
                                                 single-volume acts only (a multi-volume act answers HTTP 405)
"""
from __future__ import annotations

import os
import re
from typing import Any, Optional
from urllib.parse import urlparse

from ...inventory import InventoryItem
from ...models import Candidate, FetchPlan
from ...sources import all_query_terms, indicator_pillar, pillar_hint_for
from ..base import PortalAdapter
# The paced client and robots.txt rules are shared with Malaysia's adapter until the engine gains them (NOTES.md 2.5).
from ..my_gazette.client import LomClient as PacedClient
from ..my_gazette.robots import RobotsRules, robots_token
from .api import (
    API, WWW, LatestVersion, Title, batches, decode, epub_url, parse_titles, parse_versions, pdf_url, register_id,
    titles_by_id_url, titles_url, versions_url,
)

_EPUB = "iframe#epubFrame"                         # last-resort framed HTML (single-volume only)
_MULTIVOL_DECL = r"This\s+compilation\s+is\s+in\s+\d+\s+volumes?"
_REG_ID = re.compile(r"([CF]\d{4}[A-Z]\d{5})")
_STOP = {"of", "the", "and", "a", "an", "for", "to", "in", "on", "or", "by", "with", "any", "act"}
_DEFAULT_UA = "RDTII-Rocky-Crawler/0.1 (+polite public-law retrieval)"
_STATUS = {"InForce": "in_force", "Repealed": "repealed", "Ceased": "ceased", "NeverEffective": "never_in_force"}


class RegisterUnavailable(RuntimeError):
    """The register cannot be read on this run: the API answered an error, or its shape changed."""


class AuLegislationAdapter(PortalAdapter):
    economy = "AU"

    def __init__(self, cfg: dict[str, Any], client: Optional[PacedClient] = None, www_client: Optional[PacedClient] = None):
        self.cfg = cfg
        self.reg_cfg: dict = dict(cfg.get("register") or {})
        self._phrases = _relevance_phrases(cfg)
        self.inventory: list[InventoryItem] = []
        self.inventory_note: Optional[str] = None
        self.notes: list[str] = []
        self._api: Optional[PacedClient] = client
        self._www: Optional[PacedClient] = www_client
        self._frontier_override: Optional[str] = None
        self.robots_record: dict = {}
        self.register_error: Optional[str] = None
        self.titles: dict[str, Title] = {}                 # every title the harvest returned, principal or not
        self.versions: dict[str, LatestVersion] = {}       # title id -> latest version
        self.harvest_counts: dict = {}
        self.frontier_meta: Optional[dict] = None

    # --- settings and clients ----------------------------------------------------------

    #: what each setting means when the registry does not say; `effective_settings` resolves against these, so a
    #: run's catalogue_meta.json records the values the code used, not the ones the registry happened to carry
    SETTING_DEFAULTS: dict[str, Any] = {"detail_pages": "all", "version_batch": 18, "title_page_size": 100, "max_titles": 6000,
        "collection": "Act", "document_form": "epub", "frontier": "discover", "api": API,}

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
        env = os.environ.get("REGISTER_" + key.upper())
        return env if env is not None else self.reg_cfg.get(key, default)

    def _int_setting(self, key: str, default: int) -> int:
        return int(self._setting(key, default))

    def _frontier(self) -> str:
        frontier = str(self._frontier_override or self._setting("frontier", "discover")).strip().lower()
        if frontier not in ("discover", "links_file"):
            raise ValueError(f"register.frontier / REGISTER_FRONTIER: {frontier!r} is not discover or links_file")
        return frontier

    def _detail_policy(self) -> str:
        policy = str(self._setting("detail_pages", "all")).strip().lower()
        if policy not in ("all", "seed", "none"):
            raise ValueError(f"register.detail_pages / REGISTER_DETAIL_PAGES: {policy!r} is not all, seed or none")
        return policy

    def _clients(self, fetcher) -> tuple[PacedClient, PacedClient]:
        settings = getattr(fetcher, "settings", None)
        ua = getattr(settings, "user_agent", None) or os.environ.get("USER_AGENT") or _DEFAULT_UA
        delay = getattr(settings, "request_delay_seconds", None)
        if delay is None:
            delay = int(os.environ.get("REQUEST_DELAY_MS", "3000")) / 1000.0
        if self._api is None:
            self._api = PacedClient(ua, float(delay))
        if self._www is None:
            self._www = PacedClient(ua, float(delay))
        return self._api, self._www

    @property
    def _client(self) -> Optional[PacedClient]:
        return self._api

    def _warn(self, message: str) -> None:
        self.notes.append(message)
        print(f"[crawl] AU: WARNING {message}", flush=True)

    # --- discovery -----------------------------------------------------------------------
    def discover(self, pillars: list[int], scope: str = "relevant", fetcher=None) -> list[Candidate]:
        self._detail_policy()
        if scope == "seed" and self._frontier() == "discover" and fetcher is None:
            cands = self._seed_candidates(pillars, {})
            self.inventory = [_seed_item(c) for c in cands]
            return cands
        api, www = self._clients(fetcher)
        if self._frontier() == "links_file":
            return self._discover_from_links_file(pillars, scope, api, www, fetcher)
        self._check_robots(api, www)
        self._harvest(api)
        seeds = self._seed_by_id(pillars)
        wanted = self._version_ids(scope, seeds)
        self._read_versions(api, wanted)
        picked = self._build_candidates(pillars, scope, seeds, api)
        self._finish(api)
        return list(picked.values())

    def _check_robots(self, api: PacedClient, www: PacedClient) -> None:
        for name, client, root in (("api", api, self._api_root().rsplit("/v1", 1)[0]), ("www", www, WWW)):
            if name in self.robots_record:
                continue
            resp = client.get(f"{root}/robots.txt")
            record = {"url": f"{root}/robots.txt", "status": resp.status_code, "read_at": client.log[-1]["ts"] if client.log else None}
            if resp.status_code == 200:
                rules = RobotsRules.parse((resp.content or b"").decode("utf-8", "replace"), robots_token(client.user_agent))
                client.robots = rules
                record.update({"group": rules.group, "crawl_delay": rules.crawl_delay, "rules": rules.rules[:20]})
                if rules.crawl_delay and rules.crawl_delay > client.delay:
                    client.delay = float(rules.crawl_delay)
            elif resp.status_code >= 500:
                raise RegisterUnavailable(f"{root}/robots.txt answered HTTP {resp.status_code} (POLICY.md 5.4)")
            else:
                record["note"] = "no robots.txt: everything allowed, the delay stays the default"
            record["delay_used_s"] = client.delay
            self.robots_record[name] = record

    def _api_root(self) -> str:
        return str(self._setting("api", API)).rstrip("/")

    def _harvest(self, api: PacedClient) -> None:
        """Every in-force title of the collection, 100 a page; non-principal titles are kept for laws.csv only."""
        size, cap = self._int_setting("title_page_size", 100), self._int_setting("max_titles", 6000)
        collection = str(self._setting("collection", "Act"))
        root = self._api_root()
        skip, pages, rows, repeated = 0, 0, 0, 0
        while skip < cap:
            url = titles_url(skip, size, collection=collection).replace(API, root, 1)
            resp = api.get(url, retries=1)
            if resp.status_code != 200:
                raise RegisterUnavailable(f"the API answered HTTP {resp.status_code} for the title harvest at $skip={skip}")
            data = decode(resp.content or b"")
            batch = parse_titles(data)
            pages += 1
            for t in batch:
                rows += 1
                if t.id in self.titles:
                    repeated += 1                      # a page overlap: the pages are not stable
                self.titles.setdefault(t.id, t)
            if len(batch) < size:
                break
            skip += size
        principal = sum(1 for t in self.titles.values() if t.is_principal)
        self.harvest_counts = {"collection": collection, "titles": len(self.titles), "principal": principal,
                               "non_principal": len(self.titles) - principal, "pages": pages, "rows": rows,
                               "repeated": repeated}
        if repeated:
            self._warn(f"the title harvest returned {repeated} title(s) more than once across {pages} pages: the API's "
                       f"paging is not stable and as many titles may be missing; rebuild")
        if not self.titles:
            raise RegisterUnavailable("the API returned no titles: the query or the shape may have changed")

    def _seed_by_id(self, pillars: list[int]) -> dict[str, dict]:
        """The seeds this run collects, by register id.

        A seed tagged for other pillars is left out. **A seed with no indicator tag is kept**: it is a law named on
        purpose for the list itself, carrying no claim for any indicator (the Constitution, 2026-09-19). Before that
        it was dropped, so such a seed could not be collected at all.
        """
        out = {}
        for law in self.cfg.get("seed_laws", []) or []:
            inds = law.get("indicators", []) or []
            if inds and pillars and not any(indicator_pillar(i) in pillars for i in inds):
                continue
            rid = register_id(law.get("url", ""))
            if rid:
                out[rid] = law
        return out

    def _version_ids(self, scope: str, seeds: dict[str, dict]) -> list[str]:
        policy = self._detail_policy()
        principal = [t.id for t in self.titles.values() if t.is_principal]
        if policy == "none":
            return []
        # every seed's version is read, harvested or not: a seeded amending act is in the harvest (in force, not
        # principal) and would otherwise get no version, no date and a framed capture
        if policy == "seed" or scope == "seed":
            ids = list(seeds)
        elif scope == "relevant":
            rel = self._relevant_ids()
            ids = [i for i in principal if i in rel] + list(seeds)
        else:
            ids = principal + list(seeds)
        return list(dict.fromkeys(ids))

    def _read_versions(self, api: PacedClient, ids: list[str]) -> None:
        size = self._int_setting("version_batch", 18)
        root = self._api_root()
        for chunk in batches([i for i in ids if i not in self.versions], size):
            resp = api.get(versions_url(chunk).replace(API, root, 1), retries=1)
            if resp.status_code != 200:
                self.notes.append(f"versions for {len(chunk)} title(s) not read: HTTP {resp.status_code}")
                continue
            for v in parse_versions(decode(resp.content or b"")):
                self.versions.setdefault(v.title_id, v)
        missing = [i for i in ids if i not in self.versions]
        if missing:
            self.notes.append(f"{len(missing)} title(s) have no latest version in the API: {', '.join(missing[:10])}"
                              + (" …" if len(missing) > 10 else ""))
        outside = [i for i in ids if i not in self.titles]
        if outside:                                   # seeds the harvest did not carry: amending acts, instruments
            for chunk in batches(outside, size):
                resp = api.get(titles_by_id_url(chunk).replace(API, root, 1), retries=1)
                if resp.status_code == 200:
                    for t in parse_titles(decode(resp.content or b"")):
                        self.titles.setdefault(t.id, t)

    def _relevant_ids(self) -> set[str]:
        return {t.id for t in self.titles.values() if any(p in t.name.lower() for p in self._phrases)}

    def _build_candidates(self, pillars: list[int], scope: str, seeds: dict[str, dict], api: PacedClient) -> dict[str, Candidate]:
        relevant = self._relevant_ids()
        self.inventory = [InventoryItem(economy="AU", law_name=t.name, url=f"{WWW}/{t.id}", law_number=t.id, source="api",
                                        assent_date=t.making_date, in_force_status=t.status,
                                        relevant=t.id in relevant) for t in self.titles.values() if t.is_principal]
        picked: dict[str, Candidate] = {}

        def add(c: Optional[Candidate]) -> None:
            if c is not None and c.url and c.url not in picked:
                picked[c.url] = c

        order = list(seeds) + [t.id for t in self.titles.values() if t.is_principal and t.id not in seeds]
        for rid in order:
            law = seeds.get(rid)
            title = self.titles.get(rid)
            in_scope = law is not None or scope == "all" or (scope == "relevant" and rid in relevant)
            if not in_scope:
                continue
            if title is None and law is None:
                continue
            add(self._register_candidate(rid, title, self.versions.get(rid), law, relevant=rid in relevant))
        for law in self.cfg.get("seed_laws", []) or []:
            inds = law.get("indicators", []) or []
            if inds and pillars and not any(indicator_pillar(i) in pillars for i in inds):
                continue
            if not register_id(law.get("url", "")):
                add(self._plain_seed(law))
        return picked

    def _register_candidate(self, rid: str, title: Optional[Title], v: Optional[LatestVersion], law: Optional[dict],
                            relevant: bool) -> Optional[Candidate]:
        inds = (law or {}).get("indicators", []) or []
        form = (law or {}).get("form") or None
        document_form = str(self._setting("document_form", "epub")).strip().lower()
        if document_form not in ("epub", "pdf"):
            raise ValueError(f"register.document_form / REGISTER_DOCUMENT_FORM: {document_form!r} is not epub or pdf")
        if v is not None and v.is_compilation:
            # every compilation has a dated epub with every volume; the dated PDF exists for single-volume acts only
            url = epub_url(v) if (form == "html" or document_form == "epub") else pdf_url(v)
        elif v is not None:
            # as-made: a PDF, no epub; a form:html seed keeps Round 1's framed capture of the viewer
            url = f"{WWW}/{rid}/latest/text" if form == "html" else pdf_url(v)
        else:
            url = f"{WWW}/{rid}/latest/text"           # no version known: the framed capture, as Round 1
        name = (law or {}).get("law_name") or (title.name if title else (v.name if v else rid))
        number = (title.law_number if title else None) or (law or {}).get("law_number") or None
        if rid.startswith("F"):
            kind = "subsidiary_legislation"
        elif title is not None and not title.is_principal:
            kind = "amending_act"
        else:
            kind = "principal_act"
        cand = Candidate(url=url, economy="AU", law_name_guess=name, law_number_guess=number,
                         pillar_hint=pillar_hint_for(inds) if inds else None, indicator_hints=(",".join(inds) or None),
                         seed_query=(",".join(sorted(p for p in self._phrases if p in name.lower())) or None),
                         assent_date=title.making_date if title else None, in_force_status=title.status if title else (v.status if v else None),
                         force_form=form)
        flags = []
        if v is None:
            flags.append("amendment_check_incomplete")
            flags.append("version_unknown")
        if v is not None and not v.is_compilation:
            flags.append("as_made_only")
        if kind == "amending_act":
            flags.append("principal_unlinked")
        if law and law.get("law_name") and title and _norm(law["law_name"]) != _norm(title.name):
            flags.append("seed_title_differs_from_portal")
        amendments = [{"instrument": r.instrument, "title_id": r.title_id, "provisions": r.provisions}
                      for r in (v.amendments if v else [])]
        cand.contract_meta = {
            "portal": "au-register", "discovery_path": "seed" if law else "api_listing",
            "seed_provenance": (law or {}).get("provenance"), "portal_id": rid, "law_number": number,
            "law_name_portal": title.name if title else (v.name if v else None), "document_kind": kind,
            "text_version": ("consolidation" if v and v.is_compilation else "as_enacted" if v else "unknown"),
            "version_as_at": v.start if v else None, "version_source": "portal_api" if v and v.start else None,
            "version_id": v.register_id if v else None, "compilation_number": v.compilation_number if v else None,
            "published_on": v.registered_at if v else None, "version_ends": v.end if v else None,
            "pdf_url": pdf_url(v) if v else None, "epub_url": epub_url(v) if v else None,
            "linked_amendments": amendments, "amendment_check_complete": v is not None,
            "last_amending_instrument": v.last_amending_instrument if v else None,
            "last_amended_year": (str(max(r.year for r in v.amendments if r.year)) if v and any(r.year for r in v.amendments) else None),
            "enacted_on": title.making_date if title else None, "series_type": title.series_type if title else None,
            "is_principal": title.is_principal if title else None,
            "language": "eng", "language_source": "portal_default",
            "legal_status": _STATUS.get((title.status if title else (v.status if v else "")) or "", "unknown"),
            "status_source": "portal_api" if title or v else None, "in_force_status": cand.in_force_status,
            "title_relevant": relevant, "crawl_flags": [], "review_flags": flags,
        }
        return cand

    def _plain_seed(self, law: dict) -> Candidate:
        inds = law.get("indicators", []) or []
        cand = Candidate(url=law["url"], economy="AU", law_name_guess=law["law_name"], law_number_guess=law.get("law_number") or None,
                         pillar_hint=pillar_hint_for(inds), indicator_hints=(",".join(inds) or None), force_form=law.get("form") or None)
        cand.contract_meta = {
            "portal": urlparse(law["url"]).hostname, "discovery_path": "seed", "seed_provenance": law.get("provenance"),
            "portal_id": None, "law_number": law.get("law_number") or None, "document_kind": "agency_or_other",
            "language": "eng", "language_source": "registry", "legal_status": "unknown", "status_source": None,
            "crawl_flags": [], "review_flags": ["status_unknown"],
        }
        return cand

    def _seed_candidates(self, pillars: list[int], versions: dict[str, LatestVersion]) -> list[Candidate]:
        out: list[Candidate] = []
        for law in self.cfg.get("seed_laws", []) or []:
            inds = law.get("indicators", []) or []
            if inds and pillars and not any(indicator_pillar(i) in pillars for i in inds):
                continue
            rid = register_id(law.get("url", ""))
            if rid:
                c = self._register_candidate(rid, self.titles.get(rid), versions.get(rid), law, relevant=True)
            else:
                c = self._plain_seed(law)
            if c is not None:
                out.append(c)
        return out

    def _finish(self, api: PacedClient) -> None:
        h = self.harvest_counts
        parts = [f"register API: {h.get('titles', 0)} titles ({h.get('principal', 0)} principal) in {h.get('pages', 0)} page(s); "
                 f"{len(self.versions)} latest versions read; {len(api.log)} API request(s)"]
        if self._www is not None and self._www.log:
            parts.append(f"{len(self._www.log)} www request(s)")
        self.inventory_note = "; ".join(parts + self.notes)

    # --- the links-file frontier ---------------------------------------------------------
    def _discover_from_links_file(self, pillars: list[int], scope: str, api: PacedClient, www: PacedClient,
                                  fetcher=None) -> list[Candidate]:
        from ..my_gazette.catalogue import candidate_from_row, read_documents
        from .catalogue import cfg_fingerprint
        path = str(self._setting("links_file", "") or "")
        if not path:
            raise ValueError("register.frontier is links_file but register.links_file / REGISTER_LINKS_FILE is not set")
        rows, meta = read_documents(path)
        if meta.get("cfg_sha256") and meta["cfg_sha256"] != cfg_fingerprint(self.cfg):
            raise ValueError(f"link file {path} was built from a different registry: rebuild it with au_legislation.catalogue")
        if not meta.get("cfg_sha256"):
            self._warn(f"link file {path} carries no registry fingerprint")
        self.frontier_meta = {"links_file": path, **{k: meta.get(k) for k in ("generated_at", "counts", "scraper_sha256")}}
        register_ok = True
        try:
            self._check_robots(api, www)
        except Exception as e:  # noqa: BLE001 — robots.txt unreadable: register rows are dropped, other hosts stay
            self.register_error = f"{type(e).__name__}: {e}"
            self._warn(f"REGISTER UNAVAILABLE ({self.register_error}); only rows on other hosts are served")
            register_ok = False
        _warn_engine_delay(self, fetcher, www)
        picked: dict[str, Candidate] = {}
        dropped = 0
        for row in rows:
            if scope not in (row.get("scopes") or []):
                continue
            host = (urlparse(row["url"]).hostname or "").lower()
            if host.endswith("legislation.gov.au") and (not register_ok or (www.robots is not None and not www.robots.allowed(row["url"]))):
                dropped += 1
                continue
            picked.setdefault(row["url"], candidate_from_row(row))
        message = (f"frontier links_file {path} generated {meta.get('generated_at')}: {len(picked)} of {len(rows)} rows "
                   f"in scope {scope}; {dropped} dropped by robots.txt")
        self.notes.insert(0, message)
        print(f"[crawl] AU: {message}", flush=True)
        self.inventory = [InventoryItem(economy="AU", law_name=c.law_name_guess, url=c.url, law_number=c.law_number_guess,
                                        source="links_file") for c in picked.values()]
        self.inventory_note = message
        if not picked:
            raise RuntimeError(f"AU link file {path} selected no candidates for scope {scope}")
        return list(picked.values())

    # --- Round 1 API kept: the inventory artefact ------------------------------------------
    def harvest_inventory(self, fetcher) -> list[InventoryItem]:
        api, www = self._clients(fetcher)
        self._check_robots(api, www)
        self._harvest(api)
        rel = self._relevant_ids()
        self.inventory = [InventoryItem(economy="AU", law_name=t.name, url=f"{WWW}/{t.id}/latest/text", law_number=t.id,
                                        source="api", assent_date=t.making_date, in_force_status=t.status,
                                        relevant=t.id in rel) for t in self.titles.values() if t.is_principal]
        return self.inventory

    def _mark_relevance(self, items: list[InventoryItem]) -> None:
        for it in items:
            matched = sorted(p for p in self._phrases if p in it.law_name.lower())
            if matched:
                it.relevant = True
                it.matched_terms = matched

    # --- fetch planning: native PDF, epub full text, or the framed fallback (Round 1) -------------
    def build_plans(self, cand: Candidate, forms: str = "both") -> list[FetchPlan]:
        url = cand.url
        if "/text/original/pdf" in url or url.lower().split("?", 1)[0].endswith(".pdf"):
            return [FetchPlan(url=url, method="requests", form_factor="pdf", needs_js=False, kind="native", citation_url=url)]
        if "/text/original/epub" in url:
            # The dated epub holds every volume; the fetcher concatenates the spine or fails loudly. The citation is
            # the epub's own dated address (version-pinned; Round 1 cited the undated /latest/text).
            return [FetchPlan(url=url, method="requests", form_factor="html", needs_js=False, kind="page",
                              citation_url=url, unpack="epub_html")]
        if "/latest/text" in url:
            return [FetchPlan(url=url, method="playwright", form_factor="html", needs_js=True, scroll=False, kind="page",
                              citation_url=url, iframe_selector=_EPUB, reject_pattern=_MULTIVOL_DECL)]
        return [FetchPlan(url=url, method="playwright", form_factor="html", needs_js=True, scroll=True, kind="page",
                          citation_url=url)]


def _norm(text: Optional[str]) -> str:
    return " ".join(str(text or "").split()).casefold()


def _warn_engine_delay(adapter, fetcher, client) -> None:
    """The engine's limiter has one delay for every host (REQUEST_DELAY_MS); the crawl must run at the www host's
    Crawl-delay or more (POLICY.md 5.5)."""
    settings = getattr(fetcher, "settings", None)
    delay = getattr(settings, "request_delay_seconds", None)
    if delay is None:
        delay = int(os.environ.get("REQUEST_DELAY_MS", "3000")) / 1000.0
    need = getattr(client, "delay", 0.0) or 0.0
    if need and float(delay) < need:
        adapter._warn(f"the engine waits {float(delay):.1f} s between requests; www.legislation.gov.au's robots.txt asks "
                      f"for {need:.0f} s: set REQUEST_DELAY_MS={int(need * 1000)} before crawling")


def _seed_item(c: Candidate) -> InventoryItem:
    return InventoryItem(economy="AU", law_name=c.law_name_guess, url=c.url, law_number=c.law_number_guess,
                         source="seed", relevant=True)


def _relevance_phrases(cfg: dict[str, Any]) -> set[str]:
    phrases: set[str] = set()
    for q in all_query_terms(cfg):
        words = re.findall(r"[a-z]+", q.lower())
        for a, b in zip(words, words[1:]):
            if len(a) > 2 and len(b) > 2 and a not in _STOP and b not in _STOP:
                phrases.add(f"{a} {b}")
    return phrases
