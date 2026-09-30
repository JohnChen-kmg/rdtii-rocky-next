"""The core fetcher: Playwright + requests with a logged escalation ladder (§3.3).

Per fetch, on failure we escalate and each rung is captured in HttpMeta:
  - HTML (needs JS):  Playwright goto(domcontentloaded) -> goto(networkidle)
  - PDF / direct:     requests GET -> Playwright APIRequestContext (shares session cookies)

Anti-throttle: ONE browser context is reused across all fetches (persistent session
cookies → looks like a single browser navigating, not N bots), and throttle statuses
(429/467/403/503) trigger exponential backoff + retry. Every attempt records status,
final URL, redirect chain, headers and retrieval_method, so even a fully-failed URL
leaves auditable live-fetch evidence.
"""
from __future__ import annotations

import re
import time
from typing import Callable

import requests

from config.settings import Settings

from .epub import EpubExtractionError, concat_epub_html
from .models import FetchPlan, FetchResult, HttpMeta
from .utils import utc_now_iso

# Statuses that mean "slow down" rather than "gone". 467 is SSO's soft anti-bot throttle.
THROTTLE_STATUSES = {429, 403, 467, 503}


def _failed(url: str, method: str, err: str, status: int = 0) -> FetchResult:
    return FetchResult(
        content=b"",
        http=HttpMeta(final_url=url, status=status, retrieval_method=method,
                      error=err, fetched_at=utc_now_iso()),
        ok=False,
    )


def _postprocess(plan: FetchPlan, result: FetchResult) -> FetchResult:
    """Apply the plan's post-fetch transform/guards to an otherwise-OK result.

    Any shortfall marks the result NOT ok (the error is recorded in HttpMeta and thus
    in crawl_log.jsonl) — a partial or wrong-shaped artifact must fail loudly, never
    be stored silently (2026-07-17 AU multi-volume truncation fix).
    """
    if plan.unpack == "epub_html":
        try:
            result.content = concat_epub_html(result.content)
            # The stored artifact is the extracted HTML; the sidecar's response headers
            # still show the original application/epub+zip for provenance.
            result.http.content_type = "text/html"
        except EpubExtractionError as e:
            result.http.error = f"epub unpack failed: {e}"
            return FetchResult(content=b"", http=result.http, ok=False)
    if plan.reject_pattern:
        text = result.content.decode("utf-8", "replace")
        if re.search(plan.reject_pattern, text):
            result.http.error = (f"reject_pattern matched ({plan.reject_pattern!r}): "
                                 "capture is a known-partial rendering")
            return FetchResult(content=result.content, http=result.http, ok=False)
    return result


class Fetcher:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._pw = None
        self._browser = None
        self._context = None
        self._requests = requests.Session()
        self._requests.headers.update({
            "User-Agent": settings.user_agent, "Accept-Language": "en",
        })

    # --- Playwright lifecycle (lazy; one browser+context reused across fetches) ---

    def _ctx(self):
        if self._context is None:
            from playwright.sync_api import sync_playwright

            self._pw = sync_playwright().start()
            self._browser = self._pw.chromium.launch(headless=True)
            self._context = self._browser.new_context(
                user_agent=self.settings.user_agent, locale="en-US")
        return self._context

    def close(self) -> None:
        try:
            if self._context is not None:
                self._context.close()
            if self._browser is not None:
                self._browser.close()
        finally:
            if self._pw is not None:
                self._pw.stop()
            self._context = self._browser = self._pw = None
            self._requests.close()

    def __enter__(self) -> "Fetcher":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    # --- Public API ----------------------------------------------------------

    def fetch(self, plan: FetchPlan) -> FetchResult:
        if plan.form_factor == "pdf" or plan.method == "requests":
            rungs: list[Callable[[FetchPlan], FetchResult]] = [
                self._rung_requests, self._rung_api_request,
            ]
        else:
            rungs = [
                lambda p: self._rung_playwright(p, wait_until="domcontentloaded"),
                lambda p: self._rung_playwright(p, wait_until="networkidle", extra_wait_ms=1500),
            ]

        last: FetchResult | None = None
        for rung in rungs:
            result = self._with_backoff(rung, plan)
            last = result
            if result.ok and result.status < 400 and result.content:
                result = _postprocess(plan, result)
                last = result
                if result.ok:
                    return result
        return last if last is not None else _failed(plan.url, "unknown", "no rung ran")

    def _with_backoff(self, rung, plan: FetchPlan) -> FetchResult:
        """Retry a rung on throttle statuses with exponential backoff (honors the slow-down).

        Gov portals (SSO's 467) can block for a while, so back off generously — better to
        wait and retrieve than to drop a document.
        """
        delay = max(10.0, self.settings.request_delay_seconds * 2)
        result = None
        for attempt in range(self.settings.fetch_retries):
            try:
                result = rung(plan)
            except Exception as e:  # noqa: BLE001 — record and let the caller escalate
                return _failed(plan.url, "playwright", f"{type(e).__name__}: {e}")
            if result.status not in THROTTLE_STATUSES:
                return result
            if attempt < self.settings.fetch_retries - 1:
                time.sleep(delay)
                delay = min(delay * 2, 120.0)
        return result if result is not None else _failed(plan.url, "unknown", "no attempt")

    # --- Rungs ---------------------------------------------------------------

    def _rung_requests(self, plan: FetchPlan) -> FetchResult:
        # SSO (and some portals) build PDFs on demand: a first hit can return HTTP 202
        # ("accepted, generating") or a 200 whose body isn't a PDF yet (an RSS/HTML
        # placeholder). For a PDF plan, briefly retry so the generated PDF lands — this
        # recovers the transient majority without invoking the heavy throttle cooldown.
        resp = None
        for attempt in range(4):
            resp = self._requests.get(
                plan.url, timeout=self.settings.fetch_timeout_seconds, allow_redirects=True)
            pdf_ready = plan.form_factor != "pdf" or resp.content[:5] == b"%PDF-"
            not_ready = resp.status_code == 202 or (
                plan.form_factor == "pdf" and resp.status_code < 400 and not pdf_ready)
            if not_ready and attempt < 3:
                time.sleep(4 * (attempt + 1))     # 4s, 8s, 12s
                continue
            break
        pdf_ready = plan.form_factor != "pdf" or resp.content[:5] == b"%PDF-"
        http = HttpMeta(
            final_url=resp.url, status=resp.status_code, retrieval_method="requests",
            content_type=resp.headers.get("Content-Type", ""),
            redirect_chain=[r.url for r in resp.history],
            request_headers=dict(self._requests.headers), response_headers=dict(resp.headers),
            fetched_at=utc_now_iso(),
        )
        ok = resp.status_code < 400 and pdf_ready
        return FetchResult(content=resp.content, http=http, ok=ok)

    def _rung_api_request(self, plan: FetchPlan) -> FetchResult:
        ctx = self._ctx()
        resp = ctx.request.get(plan.url, timeout=self.settings.fetch_timeout_ms)
        body = resp.body()
        http = HttpMeta(
            final_url=resp.url, status=resp.status, retrieval_method="playwright",
            content_type=resp.headers.get("content-type", ""),
            request_headers={"User-Agent": self.settings.user_agent},
            response_headers=dict(resp.headers), fetched_at=utc_now_iso(),
        )
        # ok requires a retrieved artifact of the expected type — a 202/empty body or an
        # HTML placeholder for a PDF plan is NOT a retrieval (2026-07-16 audit fix; the
        # BNM RMiT 202 was logged "ok" through this rung).
        pdf_ready = plan.form_factor != "pdf" or body[:5] == b"%PDF-"
        ok = resp.status < 400 and pdf_ready and len(body) > 0
        return FetchResult(content=body, http=http, ok=ok)

    def _rung_playwright(self, plan: FetchPlan, *, wait_until: str,
                         extra_wait_ms: int = 0) -> FetchResult:
        ctx = self._ctx()
        page = ctx.new_page()
        try:
            response = page.goto(plan.url, wait_until=wait_until,
                                 timeout=self.settings.fetch_timeout_ms)
            status = response.status if response else 0
            # On a throttle, return early without waiting for selectors (nothing there).
            if status in THROTTLE_STATUSES:
                return FetchResult(content=b"", ok=False, http=HttpMeta(
                    final_url=(response.url if response else plan.url), status=status,
                    retrieval_method="playwright", fetched_at=utc_now_iso()))
            if plan.wait_selector:
                try:
                    page.wait_for_selector(plan.wait_selector,
                                           timeout=min(self.settings.fetch_timeout_ms, 20000))
                except Exception:
                    pass
            if plan.scroll:
                self._scroll(page)
            if extra_wait_ms:
                page.wait_for_timeout(extra_wait_ms)

            final_url = response.url if response else plan.url
            ctype = response.headers.get("content-type", "text/html") if response else "text/html"
            http = HttpMeta(
                final_url=final_url, status=status, retrieval_method="playwright",
                content_type=ctype, redirect_chain=self._redirect_chain(response),
                request_headers={"User-Agent": self.settings.user_agent},
                response_headers=dict(response.headers) if response else {},
                fetched_at=utc_now_iso(),
            )

            if plan.iframe_selector:
                # Capture the framed document (AU epubFrame), not the nav shell.
                frame_html = self._iframe_html(page, plan.iframe_selector,
                                               settle_ms=max(extra_wait_ms, 1500))
                if not frame_html or len(frame_html) < 5000:
                    # Frame not materialised yet → signal not-ok so fetch() escalates.
                    http.error = "iframe content not ready"
                    return FetchResult(content=b"", http=http, ok=False)
                return FetchResult(content=frame_html.encode("utf-8"), http=http, ok=status < 400)

            html = page.content()
            return FetchResult(content=html.encode("utf-8"), http=http, ok=status < 400)
        finally:
            page.close()

    def _iframe_html(self, page, selector: str, settle_ms: int = 1500):
        """Return the inner document HTML of a (possibly blob:) iframe, or None if not ready."""
        try:
            page.wait_for_selector(selector, timeout=min(self.settings.fetch_timeout_ms, 25000))
        except Exception:
            return None
        handle = page.query_selector(selector)
        frame = handle.content_frame() if handle else None
        if frame is None:
            return None
        try:
            frame.wait_for_load_state("networkidle", timeout=20000)
        except Exception:
            pass
        page.wait_for_timeout(settle_ms)
        try:
            return frame.content()
        except Exception:
            return None

    # --- Playwright helpers --------------------------------------------------

    @staticmethod
    def _scroll(page, rounds: int = 15) -> None:
        prev = -1
        for _ in range(rounds):
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(400)
            height = page.evaluate("document.body.scrollHeight")
            if height == prev:
                break
            prev = height

    @staticmethod
    def _redirect_chain(response) -> list[str]:
        chain: list[str] = []
        if response is None:
            return chain
        try:
            req = response.request.redirected_from
            while req is not None:
                chain.append(req.url)
                req = req.redirected_from
        except Exception:
            return []
        chain.reverse()
        return chain
