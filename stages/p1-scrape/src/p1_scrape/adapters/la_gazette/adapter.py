"""Lao PDR — the Lao Official Gazette (`laoofficialgazette.gov.la`).

The 2013 Law on Making Legislation requires every law to be published here, which makes the gazette the
authoritative source. It lists laws by kind, ten rows a page, and each row carries the title, the responsible
ministry, the date of the instrument, the date it was gazetted, **the status**, and links to the Lao text and —
for a minority of laws — an English translation (`../NOTES.md` 1.2).

**The documents are scans.** Every Lao PDF read so far is an image with no text layer, so extraction needs OCR;
Tesseract's `lao` model read one correctly on 2026-09-20 (`../NOTES.md` 1.3, 3). Nothing in this adapter reads a
document: every field comes from the listing.

**No detail page is read.** A law's own page carries no field the listing does not already carry, and it offers
fewer files. That is a country-level decision against `CONVENTIONS.md` rule 5, recorded in `../NOTES.md` 2.3
with the evidence, not a silent omission.

**There is no robots.txt.** The server answers HTTP 200 with its own page for any unknown path, so the absence is
not a 404 and must not be read as one. Nothing is disallowed, nothing states a delay, and the client uses a
conservative one of our own choosing (`POLICY.md` 5.1).

Settings (`sources.yaml`, block `gazette:`; every key can be overridden by GAZETTE_<KEY> in the environment):
  frontier        discover | links_file     what discover() does; links_file replays gazette.links_file
  legal_types     all | <comma list>        which kinds are read (the numbers in parse.LEGAL_TYPES)
  superseded      true                      read the `old=1` listings too: the superseded texts and the
                                            amending laws, which appear in no other listing
  english_pdfs    true                      collect the gazette's own English translation where it offers one
  max_pages       120                       pages of one listing at most, a guard against a broken pager. The
                                            longest listing is Agreement at 657 laws = 66 pages; a listing cut
                                            short by this guard is an error, never a warning
  root            https://laoofficialgazette.gov.la
"""
from __future__ import annotations

import os
from typing import Any, Optional
from urllib.parse import urlparse

from ...inventory import InventoryItem
from ...models import Candidate, FetchPlan
from ...sources import indicator_pillar, pillar_hint_for
from ..base import PortalAdapter
from ..my_gazette.client import LomClient as PacedClient
from ..my_gazette.relevance import TitleRule
from ..my_gazette.robots import RobotsRules, robots_token
from .parse import LEGAL_TYPES, ListedLaw, ROOT, fold, listing_path, parse_listing, results_total

_DEFAULT_UA = "RDTII-Rocky-Crawler/0.1 (+polite public-law retrieval)"


class GazetteUnavailable(RuntimeError):
    """The gazette cannot be read on this run: a listing failed, or the page format changed."""


class LaGazetteAdapter(PortalAdapter):
    economy = "LA"

    def __init__(self, cfg: dict[str, Any], client: Optional[PacedClient] = None, today: Optional[str] = None):
        self.cfg = cfg
        self.gazette_cfg: dict = dict(cfg.get("gazette") or {})
        self.title_rule = TitleRule.from_cfg(cfg.get("title_rule"))
        self._client = client
        self._today = today
        self._frontier_override: Optional[str] = None
        self._robots_checked = False
        self.root = ROOT
        self.inventory: list[InventoryItem] = []
        self.inventory_note: Optional[str] = None
        self.notes: list[str] = []
        self.robots_record: dict = {}
        self.gazette_error: Optional[str] = None
        self.listed: dict[int, list[ListedLaw]] = {}          # legal type -> its rows, each law only once
        self.listing_counts: dict[str, dict] = {}
        self.frontier_meta: Optional[dict] = None

    # --- settings and the client ---------------------------------------------------------

    SETTING_DEFAULTS: dict[str, Any] = {"legal_types": "all", "english_pdfs": True, "superseded": True,
                                        "max_pages": 120, "frontier": "discover", "root": ROOT}

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
        env = os.environ.get("GAZETTE_" + key.upper())
        return env if env is not None else self.gazette_cfg.get(key, default)

    def _root(self) -> str:
        self.root = str(self._setting("root", ROOT)).rstrip("/")
        return self.root

    def _frontier(self) -> str:
        frontier = str(self._frontier_override or self._setting("frontier", "discover")).strip().lower()
        if frontier not in ("discover", "links_file"):
            raise ValueError(f"gazette.frontier / GAZETTE_FRONTIER: {frontier!r} is not discover or links_file")
        return frontier

    def _legal_types(self) -> list[int]:
        """The kinds to read, in the order `LEGAL_TYPES` lists them.

        `all` leaves out the listings marked `subset_of`: legaltype 16 is contained in legaltype 6, so reading it
        costs 18 requests and adds no law. Naming it explicitly still reads it.
        """
        asked = str(self._setting("legal_types", "all")).strip().lower()
        if asked in ("all", "*", ""):
            return [t for t, meta in LEGAL_TYPES.items() if "subset_of" not in meta]
        chosen = [int(t.strip()) for t in asked.split(",") if t.strip()]
        unknown = [t for t in chosen if t not in LEGAL_TYPES]
        if unknown:
            raise ValueError(f"gazette.legal_types names {unknown}, which the portal does not have; "
                             f"the kinds are {sorted(LEGAL_TYPES)}")
        return [t for t in LEGAL_TYPES if t in chosen]

    def _olds(self) -> tuple[int, ...]:
        return (0, 1) if self.effective_settings(("superseded",))["superseded"] else (0,)

    def _wants_english(self) -> bool:
        return bool(self.effective_settings(("english_pdfs",))["english_pdfs"])

    def _get_client(self, fetcher) -> PacedClient:
        if self._client is None:
            settings = getattr(fetcher, "settings", None)
            ua = getattr(settings, "user_agent", None) or os.environ.get("USER_AGENT") or _DEFAULT_UA
            delay = getattr(settings, "request_delay_seconds", None)
            if delay is None:
                delay = int(os.environ.get("REQUEST_DELAY_MS", "6000")) / 1000.0
            self._client = PacedClient(ua, float(delay))
        return self._client

    def _warn(self, message: str) -> None:
        self.notes.append(message)
        print(f"[crawl] LA: WARNING {message}", flush=True)

    # --- reading the portal ---------------------------------------------------------------

    def _check_robots(self, client: PacedClient) -> None:
        """There is no robots.txt here, and the server says 200 to everything: the answer is only a record.

        A client that reads "200" as "this file exists" would parse the site's own HTML as crawling rules. So the
        answer counts as a robots file only when it looks like one.
        """
        if self._robots_checked:
            return
        url = f"{self._root()}/robots.txt"
        resp = client.get(url)
        body = (resp.content or b"").decode("utf-8", "replace")
        looks_like_robots = resp.status_code == 200 and "<html" not in body[:400].lower() and \
            any(line.lower().startswith(("user-agent", "disallow", "allow", "sitemap", "crawl-delay"))
                for line in body.splitlines())
        record = {"url": url, "status": resp.status_code, "read_at": client.log[-1]["ts"] if client.log else None,
                  "bytes": len(resp.content or b"")}
        if looks_like_robots:
            rules = RobotsRules.parse(body, robots_token(client.user_agent))
            client.robots = rules
            record.update({"group": rules.group, "crawl_delay": rules.crawl_delay, "rules": rules.rules[:20]})
            if rules.crawl_delay and rules.crawl_delay > client.delay:
                client.delay = float(rules.crawl_delay)
        else:
            record["note"] = ("no robots.txt: the server answers 200 with its own page for any unknown path, so "
                              "nothing is stated and nothing is disallowed. The delay is our own choice")
        record["delay_used_s"] = client.delay
        self.robots_record = record
        self._robots_checked = True

    def _page(self, client: PacedClient, path: str) -> str:
        """One listing page. **A page that fails stops the build**, and nothing is written.

        The paced client has already retried and, on a refusal, already rested and slowed down (decision 23),
        so an error here is one the portal means. Carrying on would write a census short of what the portal
        lists while looking complete, which is the failure `_read_listing`'s guards exist to prevent.
        """
        resp = client.get(self._root() + path, retries=1)
        if resp.status_code != 200:
            raise GazetteUnavailable(f"the gazette answered HTTP {resp.status_code} for {path}")
        return (resp.content or b"").decode("utf-8", "replace")

    def _read_listing(self, client: PacedClient, legal_type: int, old: int, max_pages: int,
                      seen: dict[str, ListedLaw], shallow: bool = False) -> tuple[list[ListedLaw], Optional[int], int, int]:
        """Every page of one kind's listing, at one `old` value. Ten rows a page; the portal states the total.

        A law already seen under an earlier listing is **not** added again: legaltype 6 carries the Civil Code
        and the Penal Code as well as their own listings do, so without this the same law would be crawled and
        counted twice. The row that keeps it records the other listing in `also_listed_under`.
        """
        rows: list[ListedLaw] = []
        ids_here: set[str] = set()
        total, page, pages_read = None, 1, 0
        while page <= max_pages:
            text = self._page(client, listing_path(legal_type, page, old=old))
            pages_read += 1
            if total is None:
                total = results_total(text)
                if total is None:
                    raise GazetteUnavailable(
                        f"legaltype={legal_type}&old={old} printed neither a result count nor "
                        f"{'the empty marker'!s}: the page format may have changed")
                if total == 0:
                    return [], 0, pages_read, 0            # the portal says it lists nothing of this kind
                if total > max_pages * 10 and not shallow:
                    # said before the reading starts, because the alternative is a listing quietly cut short:
                    # `max_pages: 60` truncated the 657-row Agreement listing at 600 on 2026-09-20
                    self._warn(f"legaltype={legal_type}&old={old} lists {total} laws, which needs "
                               f"{-(-total // 10)} pages, and gazette.max_pages is {max_pages}: raise it or "
                               f"this listing will be cut short")
            found = parse_listing(text, legal_type, old=old)
            if not found:
                if page == 1:
                    raise GazetteUnavailable(f"legaltype={legal_type}&old={old} claims {total} laws and served "
                                             f"no parsable row: the page format may have changed")
                break
            new_here = False
            for row in found:
                if row.law_id in ids_here:
                    continue
                ids_here.add(row.law_id)
                new_here = True
                earlier = seen.get(row.law_id)
                if earlier is not None:
                    if legal_type != earlier.legal_type:    # never record a listing as overlapping itself
                        earlier.also_listed_under = tuple(sorted(set(earlier.also_listed_under) | {legal_type}))
                    continue
                seen[row.law_id] = row
                rows.append(row)
            if not new_here:                               # a pager that repeats a page: stop rather than loop
                break
            if total is not None and len(ids_here) >= total:
                break
            page += 1
        if page > max_pages and total and len(ids_here) < total and not shallow:
            # A list build must never finish short and look complete. A **shallow** read is the update check
            # asking for the first N pages on purpose (`../updates/query.py`), so it is not a truncation and
            # must not raise — that mistake made `--pages` abort on every listing longer than N*10.
            raise GazetteUnavailable(
                f"legaltype={legal_type}&old={old}: gazette.max_pages is {max_pages}, and the portal lists "
                f"{total} laws, which needs {-(-total // 10)} pages. {len(ids_here)} were read and "
                f"{total - len(ids_here)} would have been lost. Raise gazette.max_pages and rebuild")
        if not shallow and total and len(ids_here) < total and page <= max_pages:
            # the pager stopped repeating before the portal's own count was reached: also a short listing
            raise GazetteUnavailable(
                f"legaltype={legal_type}&old={old}: the portal states {total} laws and the pager stopped after "
                f"{pages_read} page(s) with {len(ids_here)} read. Nothing is written rather than a short list")
        return rows, total, pages_read, len(ids_here)

    def _open_gazette(self, client: PacedClient, max_pages: Optional[int] = None) -> None:
        """robots.txt, then every page of every kind asked for, current and superseded.

        `max_pages` overrides the registry's guard, and the update check uses it to read only the first pages of
        each listing: the gazette lists newest first, so a shallow read still finds everything recent
        (`../updates/WORKFLOW.md`).
        """
        self._check_robots(client)
        shallow = max_pages is not None          # the update check asking for the first N pages on purpose
        max_pages = int(max_pages or self.effective_settings(("max_pages",))["max_pages"])
        seen: dict[str, ListedLaw] = {}
        for legal_type in self._legal_types():
            name = LEGAL_TYPES[legal_type]["english"]
            kept: list[ListedLaw] = []
            counts: dict[str, Any] = {"kind": name, "records": 0, "pages_read": 0}
            for old in self._olds():
                rows, total, pages, listed_here = self._read_listing(client, legal_type, old, max_pages, seen,
                                                                    shallow=shallow)
                kept.extend(rows)
                counts["pages_read"] += pages
                counts[f"total_old{old}"] = total
                counts[f"listed_old{old}"] = listed_here
                counts[f"records_old{old}"] = len(rows)
                # kept < listed is normal and is not a warning: the difference is laws an earlier listing
                # already named. listed < total is a warning: the pager ran out before the portal's own count.
                if total and listed_here < total and shallow:
                    self.notes.append(f"{name} (legaltype={legal_type}, old={old}): {listed_here} of {total} "
                                      f"law(s) read, the first {pages} page(s) only")
                if listed_here > len(rows):
                    self.notes.append(f"{name} (legaltype={legal_type}, old={old}): {listed_here - len(rows)} of "
                                      f"{listed_here} law(s) were already listed under another kind and are kept "
                                      f"once, under the first")
            counts["records"] = len(kept)
            self.listed[legal_type] = kept
            self.listing_counts[str(legal_type)] = counts
            print(f"[catalogue] LA: {name} (legaltype={legal_type}): {len(kept)} law(s) in "
                  f"{counts['pages_read']} page(s)", flush=True)
        if not any(self.listed.values()):
            raise GazetteUnavailable("no listing served a single law: the portal or the page format has changed")

    # --- the candidates --------------------------------------------------------------------

    def rows(self) -> list[ListedLaw]:
        """Every law read, once each, in the order the listings were read."""
        return [row for _lt, rows in self.listed.items() for row in rows]

    def _seed_by_id(self, pillars: list[int]) -> tuple[dict[str, dict], list[dict]]:
        """Seeds keyed by the portal's law id (`portal_key: "2537"`), and those that name a plain URL."""
        by_id, others = {}, []
        for law in self.cfg.get("seed_laws", []) or []:
            inds = law.get("indicators", []) or []
            # a seed with no indicator tag is a law named on purpose for the list itself, not for an indicator
            if inds and pillars and not any(indicator_pillar(i) in pillars for i in inds):
                continue
            key = str(law.get("portal_key") or "").strip()
            if key:
                by_id[key] = law
            else:
                others.append(law)
        return by_id, others

    def _mark_relevance(self, items: list[InventoryItem]) -> None:
        """The title rule, on the folded Lao title: Lao has no case, so the patterns match the script directly."""
        if self.title_rule is None:
            return
        for it in items:
            groups, _exclusion = self.title_rule.match(fold(it.law_name))
            if groups:
                it.relevant = True
                it.matched_terms = self.title_rule.matched_terms(fold(it.law_name))

    def _relevant_ids(self) -> set[str]:
        if self.title_rule is None:
            return set()
        return {r.law_id for r in self.rows() if self.title_rule.match(r.title)[0]}

    def _shared_addresses(self) -> dict[str, list[str]]:
        """File addresses that more than one law points at, and the laws that point at them.

        A portal defect, not ours: four pairs on 2026-09-20 share a generically named upload — `001.pdf`,
        `003.pdf`, `04.pdf`, `scan0001.pdf`. One of them is claimed by a 2023 Presidential Ordinance and a 2014
        provincial Order, which cannot both be right. The file is fetched once, as served, and **both laws keep
        their row and are flagged** (decision 17: flag, do not fix).
        """
        by_url: dict[str, list[str]] = {}
        for row in self.rows():
            for url in (row.url("lao"), row.url("eng")):
                if url:
                    by_url.setdefault(url, []).append(row.code)
        return {url: codes for url, codes in by_url.items() if len(codes) > 1}

    def _build_candidates(self, pillars: list[int], scope: str) -> dict[str, Candidate]:
        """One candidate per file: the Lao text, and the English translation when the gazette offers one."""
        seeds, _others = self._seed_by_id(pillars)
        relevant = self._relevant_ids()
        want_english = self._wants_english()
        shared = self._shared_addresses()
        picked: dict[str, Candidate] = {}
        for row in self.rows():
            law = seeds.get(row.law_id)
            is_seed = law is not None
            is_relevant = is_seed or row.law_id in relevant
            if scope == "seed" and not is_seed:
                continue
            if scope == "relevant" and not is_relevant:
                continue
            for language in ("lao", "eng"):
                url = row.url(language)
                if not url or (language == "eng" and not want_english):
                    continue
                inds = (law or {}).get("indicators", []) or []
                # POLICY.md 3.2: an amending instrument carries no indicator tags of its own
                tags = [] if row.document_kind == "amending_act" else inds
                cand = Candidate(
                    url=url, economy="LA", law_name_guess=row.title, law_number_guess=None,
                    publication_date=row.gazetted_on,
                    # CONTRACT.md 3.2: this column holds the portal's own words; the normalised
                    # value belongs in contract_meta.legal_status, and does
                    in_force_status=row.status_label,
                    pillar_hint=pillar_hint_for(tags) if tags else None,
                    indicator_hints=(",".join(tags) or None) if tags else None,
                    expect_scanned=True,                   # every Lao PDF read so far is an image
                    # the storage folder and the doc_id key: the gazette's own record id, never the Lao title,
                    # which the engine's slug pattern strips to nothing (`../NOTES.md` 2.5)
                    law_slug=f"la-{row.law_id}" + ("" if language == "lao" else "-en"),
                )
                cand.contract_meta = self._meta(row, language, is_seed=is_seed, law=law,
                                                shared_with=shared.get(url))
                picked[url] = cand
        return picked

    def _meta(self, row: ListedLaw, language: str, is_seed: bool, law: Optional[dict],
              shared_with: Optional[list[str]] = None) -> dict:
        flags: list[str] = []
        if row.legal_status == "unknown" and row.status_label:
            flags.append("status_word_not_recognised")
        if language == "eng":
            flags.append("unofficial_translation")             # the gazette's own English, beside the Lao text
        if not row.made_on:
            flags.append("no_instrument_date")
        if row.also_listed_under:
            flags.append("listed_under_several_kinds")
        if row.old == 1:
            flags.append("superseded_listing")
        others = [c for c in (shared_with or []) if c != row.code]
        if others:
            flags.append("shared_file_address")     # another law points at this same file: at most one is right
        return {
            "portal": urlparse(self._root()).hostname,
            "portal_id": row.code,
            "law_number": None,                                # the listing carries no act number
            "law_name_portal": row.title,
            "document_kind": row.document_kind,
            "principal_law_number": None,                      # the title names no number to link to
            "published_on": row.gazetted_on,
            "made_on": row.made_on,
            "version_as_at": None,                             # the gazette publishes as made
            "legal_status": row.legal_status,
            "status_source": "portal_listing" if row.status_label else None,
            "status_word": row.status_label,
            "language": "lao" if language == "lao" else "eng",
            "language_source": "portal_field",
            "is_translation": language == "eng",
            "is_revised_version": row.is_revised,
            "legal_type": row.legal_type,
            "legal_type_label": LEGAL_TYPES.get(row.legal_type, {}).get("english"),
            "also_listed_under": list(row.also_listed_under),
            "shared_file_with": others,
            "listing": f"legaltype={row.legal_type}&old={row.old}",
            "agency": row.agency,
            "detail_url": f"{self._root()}/index.php?r=site/display&id={row.law_id}",
            "discovery_path": "seed" if is_seed else "browse_listing",
            "seed_provenance": (law or {}).get("provenance"),
            "crawl_flags": [],
            "review_flags": flags,
        }

    # --- the interface ----------------------------------------------------------------------

    def discover(self, pillars: list[int], scope: str = "relevant", fetcher=None) -> list[Candidate]:
        client = self._get_client(fetcher)
        if self._frontier() == "links_file":
            return self._discover_from_links_file(pillars, scope, client, fetcher)
        self._open_gazette(client)
        picked = self._build_candidates(pillars, scope)
        self.inventory = self._inventory()
        self._finish(client)
        return list(picked.values())

    def harvest_inventory(self, fetcher) -> list[InventoryItem]:
        client = self._get_client(fetcher)
        self._open_gazette(client)
        self.inventory = self._inventory()
        return self.inventory

    def _inventory(self) -> list[InventoryItem]:
        items = [InventoryItem(economy="LA", law_name=r.title, url=r.url() or "", law_number=None,
                               listing_date=r.gazetted_on, source="browse")
                 for r in self.rows()]
        self._mark_relevance(items)
        return items

    def _finish(self, client: PacedClient) -> None:
        rows = self.rows()
        english = sum(1 for r in rows if r.pdf_english)
        superseded = sum(1 for r in rows if r.old == 1)
        self.inventory_note = "; ".join(
            [f"Lao gazette: {len(rows)} law(s) across {len(self.listed)} kind(s), {english} with an English "
             f"translation, {superseded} from the superseded listing",
             f"{len(client.log)} discovery request(s)"] + self.notes)

    def _discover_from_links_file(self, pillars: list[int], scope: str, client: PacedClient, fetcher=None) -> list[Candidate]:
        from ..my_gazette.catalogue import candidate_from_row, read_documents
        from .catalogue import cfg_fingerprint
        path = str(self._setting("links_file", "") or "")
        if not path:
            raise ValueError("gazette.frontier is links_file but gazette.links_file / GAZETTE_LINKS_FILE is not set")
        rows, meta = read_documents(path)
        if meta.get("cfg_sha256") and meta["cfg_sha256"] != cfg_fingerprint(self.cfg):
            raise ValueError(f"link file {path} was built from a different registry: rebuild it with la_gazette.catalogue")
        if not meta.get("cfg_sha256"):
            self._warn(f"link file {path} carries no registry fingerprint")
        self.frontier_meta = {"links_file": path, **{k: meta.get(k) for k in ("generated_at", "counts", "scraper_sha256")}}
        try:
            self._check_robots(client)
        except Exception as e:  # noqa: BLE001
            self.gazette_error = f"{type(e).__name__}: {e}"
            self._warn(f"GAZETTE UNAVAILABLE ({self.gazette_error}); no row is served")
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
        """Every document is a PDF fetched with `requests`. They are scans, and `kind` says so."""
        if forms == "html":
            return []
        return [FetchPlan(url=cand.url, method="requests", form_factor="pdf", needs_js=False, kind="scanned",
                          citation_url=cand.url)]
