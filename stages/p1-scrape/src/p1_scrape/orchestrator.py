"""Frontier loop (§3.2): discover -> fetch -> classify -> store -> manifest row.

Non-interactive; per-economy fault isolation. Built for a COMPLETE, pillar-agnostic
corpus crawl: `--scope all` retrieves every act; pillar/indicator relevance is a
downstream (P3) concern, so nothing is excluded by pillar at retrieval time.

Robust against gov-portal throttling (SSO's HTTP 467): a work-queue with adaptive
cooldown + retry rounds, and resumable crawls (skip laws already retrieved, cumulative
manifest) so a long crawl can be re-run to completion.
"""
from __future__ import annotations

import json
import time
from collections import Counter, deque
from pathlib import Path
from typing import Optional

from config.settings import Settings

from .adapters.registry import get_adapter
from .classifier import classify, is_valid_pdf
from .cost import CostMeter
from .crawl_logger import CrawlLogger
from .dedup import Dedup
from .fetcher import THROTTLE_STATUSES, Fetcher
from .inventory import write_inventory
from .manifest import validate_manifest, write_manifest
from .models import Candidate, FetchPlan, HttpMeta
from .politeness import RateLimiter
from .storage import Storage
from .utils import sha256_hex, utc_now_iso

_KIND_EXT = {
    "pdf_native": ("native", "pdf"),
    "pdf_scanned": ("scanned", "pdf"),
    "html": ("page", "html"),
}
_MAX_RETRY_ROUNDS = 4


class CrawlHealth:
    """Built-in crawl tracker: reports WHILE the crawl runs and detects portal throttling.

    Always on for every crawl (no separate process to remember), so a future re-run —
    e.g. Singapore — self-reports:
      - a [health] heartbeat narrated every ~60s (stored/attempted/recent outcomes);
      - out_dir/crawl_status.json, refreshed continuously, for humans or the external
        watcher (tools/crawl_tracker.py) to poll;
      - THROTTLE DETECTION: N consecutive "PDF plan answered with non-PDF junk" responses
        is the signature of SSO's anti-bot (it serves the HTML page instead of the PDF).
        The economy is aborted early with a loud message — continuing would only deepen
        the throttle; a later resumed run picks up where this one stopped.
    """

    BEAT_SECONDS = 60
    CONSECUTIVE_JUNK_LIMIT = 10

    def __init__(self, out_dir: Path, logger):
        self.out_dir = Path(out_dir)
        self.logger = logger
        self.economy = ""
        self.todo = 0
        self.attempted = 0
        self.stored_total = 0
        self.consecutive_junk = 0
        self.recent: deque[str] = deque(maxlen=40)
        self.started_at = time.time()
        self._last_beat = 0.0
        self.state = "starting"

    def start_economy(self, economy: str, todo: int) -> None:
        self.economy, self.todo, self.attempted = economy, todo, 0
        self.consecutive_junk = 0
        self.recent.clear()
        self.state = "crawling"
        self._beat(force=True)

    def record(self, outcome: str, stored: bool) -> None:
        """outcome ∈ ok | throttled | not_ready (pdf plan got non-pdf junk) | failed."""
        self.attempted += 1
        self.recent.append(outcome)
        if stored:
            self.stored_total += 1
        if outcome == "ok":
            self.consecutive_junk = 0
        elif outcome == "not_ready":
            self.consecutive_junk += 1
        self._beat()

    def throttle_suspected(self) -> bool:
        return self.consecutive_junk >= self.CONSECUTIVE_JUNK_LIMIT

    def finish(self, state: str) -> None:
        self.state = state
        self._beat(force=True)

    def _beat(self, force: bool = False) -> None:
        now = time.time()
        if not force and now - self._last_beat < self.BEAT_SECONDS:
            return
        self._last_beat = now
        mix = dict(Counter(self.recent))
        if not force:
            self.logger.narrate(f"[health] {self.economy}: {self.attempted}/{self.todo} attempted, "
                                f"{self.stored_total} stored total; recent={mix}")
        try:
            (self.out_dir / "crawl_status.json").write_text(json.dumps({
                "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now)),
                "state": self.state,
                "economy": self.economy,
                "attempted": self.attempted,
                "todo": self.todo,
                "stored_total": self.stored_total,
                "consecutive_junk": self.consecutive_junk,
                "recent_outcomes": mix,
                "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(self.started_at)),
            }, indent=2), encoding="utf-8")
        except OSError:
            pass  # status file is best-effort; never fail the crawl over it


def _resolve_forms(forms: Optional[str], scope: str) -> str:
    if forms in ("pdf", "html", "both"):
        return forms
    # Default: the full corpus is PDF-per-law (efficient); curated subsets show both.
    return "pdf" if scope == "all" else "both"


def _load_existing_manifest(out_dir: Path) -> dict[str, dict]:
    """Load prior manifest.jsonl rows (for resumable/cumulative crawls), keyed by doc_id."""
    path = out_dir / "manifest.jsonl"
    rows: dict[str, dict] = {}
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
            if obj.get("doc_id"):
                rows[obj["doc_id"]] = obj
        except json.JSONDecodeError:
            continue
    return rows


def run_crawl(
    economies: list[str],
    pillars: list[int],
    out_dir: Path,
    seed_laws_only: bool = False,
    dry_run: bool = False,
    settings: Optional[Settings] = None,
    scope: str = "relevant",
    forms: Optional[str] = None,
) -> int:
    assert settings is not None
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    if seed_laws_only:
        scope = "seed"
    forms = _resolve_forms(forms, scope)

    start = time.monotonic()
    logger = CrawlLogger(out_dir / "crawl_log.jsonl")
    storage = Storage(out_dir)
    dedup = Dedup(out_dir)
    rate = RateLimiter(settings.request_delay_seconds)
    meter = CostMeter()
    health = CrawlHealth(out_dir, logger)
    logger.narrate(f"[health] built-in tracker on: heartbeat + {out_dir / 'crawl_status.json'} "
                   f"(external watcher: python tools/crawl_tracker.py --out {out_dir})")

    existing = _load_existing_manifest(out_dir)   # resume: keep prior rows
    rows_by_id: dict[str, dict] = dict(existing)

    def checkpoint() -> None:
        """Persist idmap + manifest mid-crawl so a killed long job can resume."""
        dedup.save()
        write_manifest(list(rows_by_id.values()), out_dir)

    with Fetcher(settings) as fetcher:
        for economy in economies:
            # Full per-economy fault isolation: a failure in one economy's discovery or
            # crawl (network, portal outage, unexpected data) must never abort the others.
            try:
                adapter = get_adapter(economy)
                cands = adapter.discover(pillars=pillars, scope=scope, fetcher=fetcher)
                inv = getattr(adapter, "inventory", None) or []
                # Only a real harvest (relevant/all) may write inventory_<cc>.csv — a
                # seed run's inventory is just the curated seed list and must not
                # clobber a full-portal harvest artifact (2026-07-16 audit fix).
                if inv and scope in ("relevant", "all"):
                    write_inventory(economy, inv, out_dir)
                if inv:
                    note = getattr(adapter, "inventory_note", None)
                    logger.narrate(f"[crawl] {economy}: inventory {len(inv)} item(s)"
                                   + (f" ({note})" if note else ""))

                cap = settings.max_candidates_per_economy
                if scope == "relevant" and cap and len(cands) > cap:
                    logger.narrate(f"[crawl] {economy}: WARNING capping {len(cands)} -> {cap} "
                                   f"(raise MAX_CANDIDATES_PER_ECONOMY)")
                    cands = cands[:cap]

                # Resume: drop laws already retrieved in a prior run.
                fresh = [c for c in cands
                         if not dedup.is_retrieved(c.economy, c.law_name_guess, c.law_slug)]
                skipped = len(cands) - len(fresh)
                logger.narrate(f"[crawl] {economy}: {len(fresh)} to fetch, {skipped} already "
                               f"retrieved [scope={scope}, forms={forms}, pillars={pillars}]")

                work = [(c, p) for c in fresh for p in adapter.build_plans(c, forms=forms)
                        if dedup.url_is_new(p.url)]
                health.start_economy(economy, len(work))
                _crawl_queue(work, adapter, fetcher, storage, dedup, rate, meter, logger,
                             settings, rows_by_id, dry_run, checkpoint, health)
            except Exception as e:  # noqa: BLE001 — isolate the economy, keep the rest
                logger.narrate(f"[crawl] SKIP {economy}: {type(e).__name__}: {e}")
            finally:
                if not dry_run:
                    checkpoint()   # persist this economy's progress before the next

    health.finish("done")

    dedup.save()
    rc = 0
    if not dry_run:
        rows = list(rows_by_id.values())
        write_manifest(rows, out_dir)
        meter.write(out_dir, wall_clock_seconds=time.monotonic() - start)
        report = validate_manifest(out_dir / "manifest.csv", settings.contract_version)
        for e in report.errors[:20]:
            logger.narrate(f"[validate] ERROR {e}")
        logger.narrate(f"[crawl] manifest has {len(rows)} row(s); "
                       f"validate {'OK' if report.ok else 'FAILED'} "
                       f"[contract {settings.contract_version}]")
        rc = 0 if report.ok else 1
    logger.close()
    return rc


def _crawl_queue(work, adapter, fetcher, storage, dedup, rate, meter, logger,
                 settings, rows_by_id, dry_run, checkpoint, health=None) -> None:
    """Process (candidate, plan) work with adaptive throttle cooldown + retry rounds."""
    consecutive_throttle = 0
    stored_since_ckpt = 0
    rnd = 0
    while work and rnd <= _MAX_RETRY_ROUNDS:
        retry: list = []
        for cand, plan in work:
            if dry_run:
                logger.narrate(f"[dry-run] {cand.economy} {cand.law_name_guess} -> {plan.url}")
                continue
            rate.wait(plan.url)
            result = fetcher.fetch(plan)
            meter.record_fetch(result)
            # "ok" in the audit log requires an actually-retrieved artifact (bytes present),
            # not merely a sub-400 status (2026-07-16 audit fix).
            logger.log(plan.url, result.http,
                       outcome=("ok" if (result.ok and result.content) else "failed"),
                       note=cand.law_name_guess)

            if result.ok and result.content:
                consecutive_throttle = 0
                try:
                    stored = _store_row(cand, plan, result, adapter, storage, dedup, meter,
                                        logger, settings, rows_by_id)
                except Exception as e:  # noqa: BLE001 — one bad doc must not kill the crawl
                    logger.narrate(f"[crawl] XX {cand.economy} {cand.law_name_guess} "
                                   f"-> store error: {type(e).__name__}: {e}")
                    logger.log(plan.url, result.http, outcome="error",
                               note=f"store {type(e).__name__}: {e}")
                    stored = False
                if health:
                    health.record("ok", stored)
                if stored:
                    stored_since_ckpt += 1
                    if stored_since_ckpt >= 10:
                        checkpoint()
                        stored_since_ckpt = 0
                continue

            if result.http.status in THROTTLE_STATUSES:
                if health:
                    health.record("throttled", False)
                consecutive_throttle += 1
                retry.append((cand, plan))
                cooldown = min(30 * consecutive_throttle, 300)
                logger.narrate(f"[crawl] throttled (HTTP {result.http.status}) on "
                               f"{cand.law_name_guess}; cooldown {cooldown}s")
                time.sleep(cooldown)
            else:
                # A pdf plan answered 2xx/3xx WITHOUT pdf bytes = portal junk (SSO's
                # anti-bot serves the HTML page instead of the PDF). Track it — a run
                # of these means the portal has cut us off and the economy should stop.
                junk = plan.form_factor == "pdf" and result.http.status < 400
                if health:
                    health.record("not_ready" if junk else "failed", False)
                logger.narrate(f"[crawl] XX {cand.economy} {cand.law_name_guess} "
                               f"-> {plan.url} (HTTP {result.http.status})")
                if health and health.throttle_suspected():
                    logger.narrate(
                        f"[health] THROTTLE SUSPECTED: {health.consecutive_junk} consecutive "
                        f"non-PDF responses from {cand.economy} — stopping this economy early. "
                        f"Re-run later; resume will skip what's already retrieved.")
                    checkpoint()
                    health.finish("throttle_suspected")
                    return

        if retry and len(retry) < len(work):      # made progress → retry the throttled ones
            rnd += 1
            logger.narrate(f"[crawl] retry round {rnd}: {len(retry)} throttled URL(s); "
                           f"cooling down 120s first")
            time.sleep(120)
            work = retry
        else:
            if retry:
                logger.narrate(f"[crawl] {len(retry)} URL(s) still throttled after retries "
                               f"(logged; re-run to resume)")
            break


def _store_row(cand, plan, result, adapter, storage, dedup, meter, logger,
               settings, rows_by_id) -> bool:
    # A PDF-intended fetch that returned non-PDF bytes is a failed/garbage response
    # (e.g. LOM's 5-byte 'false' sentinel, or an HTML error page mislabeled as
    # application/pdf) — skip, don't store it as a law.
    if plan.form_factor == "pdf" and not is_valid_pdf(result.content):
        logger.log(plan.url, result.http, outcome="skipped",
                   note=f"not a valid PDF ({len(result.content)}B, {result.http.content_type})")
        logger.narrate(f"[crawl] -- {cand.economy} {cand.law_name_guess} "
                       f"-> skipped (not a valid PDF)")
        return False
    sha = sha256_hex(result.content)
    if not dedup.content_is_new(sha):
        logger.log(plan.url, result.http, outcome="duplicate", note="sha already stored")
        return False
    cls = classify(result.content, result.http.content_type, settings.scan_char_threshold)
    anchor_hint, anchor_kind = (None, None)
    if cls.source_type == "html":
        anchor_hint, anchor_kind = adapter.extract_anchor(cand, plan, result.content)
    kind, ext = _KIND_EXT[cls.source_type]
    # The storage folder and the doc_id key come from the adapter's law_slug when it set
    # one, and from the title when it did not — so Singapore, Malaysia and Australia are
    # untouched, while a Lao law lands at raw/la/la_2537/ as la-la2537-001 rather than
    # every Lao law sharing raw/la/unknown/ under la-law-NNN.
    sf = storage.store(cand.economy, cand.law_slug or cand.law_name_guess,
                       kind, ext, result.content, result.http)
    doc_id, supersedes = dedup.stable_id(cand.economy, cand.law_name_guess, sha, cand.law_slug)
    row = _build_row(settings, cand, plan, cls, sf, sha, result.http,
                     doc_id, anchor_hint, anchor_kind, supersedes)
    rows_by_id[doc_id] = row
    meter.record_doc()
    anchor_txt = f" anchor {anchor_hint}" if anchor_hint else ""
    logger.narrate(f"[crawl] OK {cand.economy} {cand.law_name_guess} "
                   f"-> {cls.source_type} ({result.status}){anchor_txt} -> {doc_id}")
    return True


def _build_row(settings, cand: Candidate, plan: FetchPlan, cls, sf, sha: str,
               http: HttpMeta, doc_id: str, anchor_hint, anchor_kind, supersedes) -> dict:
    ct = (http.content_type or "").split(";")[0].strip()
    if not ct:
        ct = "application/pdf" if cls.source_type.startswith("pdf") else "text/html"
    return {
        "contract_version": settings.contract_version,
        "instrument_version": None,
        "doc_id": doc_id,
        "economy": cand.economy,
        "source_url": plan.source_url(),
        "access_date": http.fetched_at or utc_now_iso(),
        "source_type": cls.source_type,
        "pdf_is_scanned": cls.pdf_is_scanned,
        "local_path": sf.local_path,
        "law_name_guess": cand.law_name_guess,
        "law_number_guess": cand.law_number_guess,
        "pillar_hint": cand.pillar_hint,
        "indicator_hints": cand.indicator_hints,
        "retrieval_method": http.retrieval_method,
        "http_status": http.status,
        "http_headers_path": sf.headers_path,
        "content_type": ct,
        "content_sha256": sha,
        "byte_size": sf.byte_size,
        "page_count": cls.page_count,
        "anchor_hint": anchor_hint,
        "anchor_kind": anchor_kind,
        "seed_query": cand.seed_query,
        "crawl_notes": (f"supersedes {supersedes}" if supersedes else None),
        "publication_date": cand.publication_date,
        "assent_date": cand.assent_date,
        "commencement_date": cand.commencement_date,
        "in_force_status": cand.in_force_status,
        # what the adapter read from the portal about this file (its language, whether it is a
        # translation, its legal status). Written to manifest_meta.jsonl beside the manifest, never into
        # it: the contract's row allows no other field.
        "contract_meta": getattr(cand, "contract_meta", None) or None,
        "http": {
            "status": http.status,
            "redirect_chain": http.redirect_chain,
            "headers": http.response_headers,
        },
    }
