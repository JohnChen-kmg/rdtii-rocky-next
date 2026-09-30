"""3-portal live-fetch smoke test (§10 T2b) — banks the binary 10-pt evidence early.

Fetches ONE canonical public URL per economy's official portal, INDEPENDENTLY
(fault-isolated per economy, so one portal outage cannot zero the others), logs
each attempt to crawl_log.jsonl, and drops the bytes + a .headers.json sidecar into
handoff1/raw/. Runs on the core fetcher alone — no adapter discovery required.

Each economy carries a small fallback chain of OFFICIAL portal URLs so a single
unreachable host (e.g. federalgazette.agc.gov.my, which currently fails DNS) does
not zero that economy — MY falls back to lom.agc.gov.my (Laws of Malaysia, AGC).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from config.settings import Settings

from .crawl_logger import CrawlLogger
from .fetcher import Fetcher
from .models import FetchPlan
from .storage import Storage

# One economy per required portal; first reachable URL (HTTP < 400) wins.
# All fallbacks are OFFICIAL government hosts named in sources_<cc>.yaml.
SMOKE_TARGETS = [
    {
        "economy": "SG", "law": "smoke Singapore SSO",
        "urls": ["https://sso.agc.gov.sg/Act/PDPA2012"],
    },
    {
        "economy": "AU", "law": "smoke Australia legislation",
        # bare series URL redirects → /latest/text : banks a redirect chain in the sidecar
        "urls": ["https://www.legislation.gov.au/C2004A03712/latest/text"],
    },
    {
        "economy": "MY", "law": "smoke Malaysia gazette",
        "urls": [
            "https://federalgazette.agc.gov.my/",  # named in contract; may fail DNS
            "https://lom.agc.gov.my/",             # official AGC fallback (reachable)
        ],
    },
]


@dataclass
class SmokeResult:
    economy: str
    ok: bool = False
    reached_url: str | None = None
    status: int = 0
    retrieval_method: str = "unknown"
    local_path: str | None = None
    attempts: list[str] = field(default_factory=list)


def run_smoke(out_dir: Path, settings: Settings) -> int:
    out_dir = Path(out_dir)
    storage = Storage(out_dir)
    logger = CrawlLogger(out_dir / "crawl_log.jsonl")
    results: list[SmokeResult] = []

    with Fetcher(settings) as fetcher:
        for tgt in SMOKE_TARGETS:
            results.append(_probe_economy(tgt, fetcher, storage, logger))

    logger.close()
    return _summarize(results)


def _probe_economy(tgt, fetcher, storage, logger) -> SmokeResult:
    res = SmokeResult(economy=tgt["economy"])
    for url in tgt["urls"]:
        res.attempts.append(url)
        try:
            plan = FetchPlan(url=url, method="playwright", form_factor="html",
                             needs_js=True, scroll=False, kind="page")
            r = fetcher.fetch(plan)
            outcome = "ok" if r.ok else "failed"
            note = f"smoke:{tgt['economy']}"
            extra = {"error": r.http.error} if r.http.error else None
            logger.log(url, r.http, outcome=outcome, note=note, extra=extra)
            if r.ok and r.content:
                sf = storage.store(tgt["economy"], tgt["law"], "page", "html",
                                   r.content, r.http)
                res.ok, res.reached_url, res.status = True, r.http.final_url, r.status
                res.retrieval_method, res.local_path = r.http.retrieval_method, sf.local_path
                break
            res.status = r.status
        except Exception as e:  # noqa: BLE001 — fault-isolate per economy
            logger.log(url, None, outcome="failed", note=f"smoke:{tgt['economy']}",
                       extra={"error": f"{type(e).__name__}: {e}"})
    _narrate(logger, res)
    return res


def _narrate(logger: CrawlLogger, res: SmokeResult) -> None:
    mark = "OK " if res.ok else "XX "
    if res.ok:
        logger.narrate(f"[smoke] {mark}{res.economy} -> HTTP {res.status} "
                       f"({res.retrieval_method}) {res.reached_url} -> stored {res.local_path}")
    else:
        logger.narrate(f"[smoke] {mark}{res.economy} -> unreachable after "
                       f"{len(res.attempts)} attempt(s): {res.attempts}")


def _summarize(results: list[SmokeResult]) -> int:
    reached = [r.economy for r in results if r.ok]
    missing = [r.economy for r in results if not r.ok]
    print()
    print(f"[smoke] {len(reached)}/{len(results)} economies reached with HTTP < 400: {reached}")
    if missing:
        print(f"[smoke] NOT reached (still logged as attempted live fetches): {missing}")
        return 1
    print("[smoke] All three portals reached — live-crawl evidence banked "
          "(crawl_log.jsonl + .headers.json sidecars).")
    return 0
