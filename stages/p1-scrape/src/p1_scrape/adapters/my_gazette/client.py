"""Transport: one paced session for every discovery request to lom."""
from __future__ import annotations

import email.utils
import os
import random
import sys
import time
from datetime import datetime, timezone
from typing import Any, Callable, Optional
from urllib.parse import urljoin

from .records import LomThrottled, LomUnavailable, RobotsDisallowed
from .robots import RobotsRules, robots_token

DEFAULT_RESTS = (60.0, 300.0, 1800.0)       # a minute, five minutes, half an hour; the last one repeats


class LomClient:
    """GET/POST to a portal, one request at a time, paced and logged. Shared by every country's catalogue step and
    update check (Malaysia's lom, Singapore's SSO, Australia's register).

    `session` is a requests.Session-like object; tests inject a fake. `sleep`, `clock` and `now_iso`
    are injectable so tests never wait.

    **When a portal refuses the client, it rests and slows down rather than stopping** (decision 23, the developer's
    rule of 2026-09-16: "stop for 30 minutes or 1 minute, then it is OK; just decrease the frequency"). A refusal is
    HTTP 403, 429, 467 or 503, or any answer carrying `x-amzn-waf-action` (AWS WAF's challenge, which Singapore's
    edge sends with HTTP 202). On a refusal the client rests for the next period in `rests`, doubles its delay
    between requests (up to `max_delay`) for the rest of the session, and sends the same request again. An answer
    that is not a refusal resets the count; `max_rests` refusals in a row stop it with `LomThrottled`, whose message
    says how long it rested and how slow it went.

    Two exceptions. **robots.txt is never rested on**: its answer is taken as given, so a portal that refuses it is
    read as refusing everything. And **`max_rests = 0` restores the rule before this one**: 429/503 retried twice on
    Retry-After and a stop at the third in a row, every other refusal handed back to the caller.

    Configure from the environment without touching code: `PACED_RESTS` (seconds, comma-separated),
    `PACED_MAX_RESTS`, `PACED_SLOWDOWN`, `PACED_MAX_DELAY`.
    """

    throttle_retries = 2          # re-sends of one request after HTTP 429/503, before any rest
    throttle_limit = 3            # consecutive 429/503 answers that stop discovery when rests are off
    retry_after_cap = 600.0       # seconds
    rests: tuple = DEFAULT_RESTS
    max_rests = 6                 # refusals in a row, each followed by a rest, before giving up
    slowdown = 2.0                # the delay is multiplied by this at every rest
    max_delay = 60.0              # seconds: the slowest pace a rest can push the client to

    def __init__(self, user_agent: str, delay_seconds: float = 3.0, session=None,
                 sleep: Callable[[float], None] = time.sleep,
                 clock: Callable[[], float] = time.monotonic, jitter: bool = True,
                 now_iso: Optional[Callable[[], str]] = None):
        if session is None:
            import requests  # P1 dependency; imported lazily so parsers stay importable without it
            session = requests.Session()
        self.session = session
        self.user_agent = user_agent
        self.robots_agent = robots_token(user_agent)
        self.robots: Optional[RobotsRules] = None
        self.delay = max(0.0, delay_seconds)
        self._sleep, self._clock, self._jitter = sleep, clock, jitter
        self._now_iso = now_iso or (lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
        self._last: Optional[float] = None
        self._throttled = 0
        self.log: list[dict] = []
        self.rests = _env_floats("PACED_RESTS", self.rests)
        self.max_rests = int(os.environ.get("PACED_MAX_RESTS", self.max_rests))
        self.slowdown = float(os.environ.get("PACED_SLOWDOWN", self.slowdown))
        self.max_delay = float(os.environ.get("PACED_MAX_DELAY", self.max_delay))
        self._rests_in_a_row = 0
        self.rests_taken = 0          # over the whole session, for the run's record
        self.rested_s = 0.0

    def _pace(self, min_gap: float = 0.0) -> float:
        """Sleep until one delay (plus jitter), or `min_gap` if longer, has passed since the last request."""
        if self._last is None and min_gap <= 0:
            return 0.0
        target = max(self.delay + (random.uniform(0, self.delay * 0.5) if self._jitter else 0.0), min_gap)
        wait = target - ((self._clock() - self._last) if self._last is not None else 0.0)
        if wait > 0:
            self._sleep(wait)
            return wait
        return 0.0

    def _record(self, method: str, url: str, status: Optional[int], size: int, waited: float, ts: str,
                **extra: Any) -> None:
        entry = {"ts": ts, "method": method, "url": url, "status": status, "bytes": size,
                 "waited_s": round(waited, 3)}
        entry.update({k: v for k, v in extra.items() if v not in (None, 0)})
        self.log.append(entry)

    def request(self, method: str, url: str, data: Optional[dict] = None,
                referer: Optional[str] = None, timeout: float = 120.0, max_redirects: int = 5,
                retries: int = 0, headers: Optional[dict] = None):
        """One paced request. Redirects are followed here, one paced hop at a time, so the signed
        processFile.php link and the detail page it redirects to are two spaced requests. Each hop is
        checked against robots.txt first. HTTP 429/503 waits Retry-After (capped) and re-sends; three
        in a row raise LomThrottled. `retries` re-sends after a network error or another 5xx. `headers`
        adds request headers (the update check's If-None-Match / If-Modified-Since)."""
        headers = {"User-Agent": self.user_agent, **(headers or {})}
        if referer:
            headers["Referer"] = referer
        if method == "POST":
            headers["X-Requested-With"] = "XMLHttpRequest"
        for _hop in range(max_redirects + 1):
            if self.robots is not None and not self.robots.allowed(url):
                self._record(method, url, None, 0, 0.0, self._now_iso(), outcome="blocked_by_robots")
                raise RobotsDisallowed(f"lom robots.txt disallows {url}")
            attempt, min_gap = 0, 0.0
            while True:
                waited = self._pace(min_gap)
                ts = self._now_iso()
                try:
                    resp = self.session.request(method, url, data=data, headers=headers,
                                                timeout=timeout, allow_redirects=False)
                except Exception as e:  # noqa: BLE001 — network error or timeout: logged, retried, re-raised
                    self._last = self._clock()
                    self._record(method, url, None, 0, waited, ts, attempt=attempt,
                                 error=f"{type(e).__name__}: {e}")
                    if attempt < retries:
                        attempt, min_gap = attempt + 1, 0.0
                        continue
                    raise
                self._last = self._clock()
                resp_headers = getattr(resp, "headers", None) or {}
                location = resp_headers.get("Location")
                self._record(method, url, resp.status_code, len(resp.content or b""), waited, ts,
                             attempt=attempt, location=location)
                refusal = None if _is_robots(url) else _refusal(resp)
                if refusal is not None and self.max_rests > 0:
                    if resp.status_code in (429, 503) and attempt < self.throttle_retries:
                        attempt += 1                          # a short wait on Retry-After comes first
                        min_gap = _retry_after_seconds(resp_headers.get("Retry-After"),
                                                       self.retry_after_cap, 2 * self.delay)
                        continue
                    if self._rests_in_a_row >= self.max_rests:
                        raise LomThrottled(
                            f"the portal is throttling this client: {refusal} {self._rests_in_a_row + 1} times in a "
                            f"row, after resting {self.rested_s / 60:.0f} min in all and slowing to "
                            f"{self.delay:g} s between requests ({url})")
                    rest = self.rests[min(self._rests_in_a_row, len(self.rests) - 1)]
                    asked = resp_headers.get("Retry-After")
                    if asked:
                        rest = max(rest, _retry_after_seconds(asked, 24 * 3600.0, rest))
                    self.delay = min(self.max_delay, max(self.delay, 1.0) * self.slowdown)
                    self._rests_in_a_row += 1
                    self.rests_taken += 1
                    self.rested_s += rest
                    self._record(method, url, resp.status_code, 0, 0.0, self._now_iso(), outcome="rested",
                                 rest_s=rest, delay_s=self.delay, reason=refusal)
                    # a rest can be half an hour: say so as it starts, or a long run looks hung
                    host = url.split("//", 1)[-1].split("/", 1)[0]
                    print(f"[paced] {self._now_iso()} {host} refused ({refusal}), refusal {self._rests_in_a_row} of "
                          f"{self.max_rests}: resting {rest / 60:g} min, then {self.delay:g} s between requests",
                          file=sys.stderr, flush=True)
                    # the rest has done the waiting: the next refusal goes straight to the next rest
                    attempt, min_gap = self.throttle_retries, rest
                    continue
                if refusal is None:
                    self._rests_in_a_row = 0
                if resp.status_code in (429, 503):
                    self._throttled += 1
                    if self._throttled >= self.throttle_limit:
                        raise LomThrottled(f"lom is throttling discovery: HTTP {resp.status_code} "
                                           f"{self._throttled} times in a row ({url})")
                    if attempt < self.throttle_retries:
                        attempt += 1
                        min_gap = _retry_after_seconds(resp_headers.get("Retry-After"),
                                                       self.retry_after_cap, 2 * self.delay)
                        continue
                    return resp
                if resp.status_code < 400:
                    self._throttled = 0
                if resp.status_code >= 500 and attempt < retries:
                    attempt, min_gap = attempt + 1, 0.0
                    continue
                break
            if resp.status_code in (301, 302, 303, 307, 308) and location:
                if max_redirects == 0:          # the caller wants the redirect itself, not its target
                    return resp
                url = urljoin(url, location)
                if resp.status_code in (301, 302, 303) and method != "HEAD":
                    method, data = "GET", None   # a HEAD stays a HEAD: it must never turn into a download
                continue
            return resp
        raise LomUnavailable(f"lom: more than {max_redirects} redirects from {url}")

    def get(self, url: str, referer: Optional[str] = None, retries: int = 0):
        return self.request("GET", url, referer=referer, retries=retries)

    def post(self, url: str, data: dict, referer: Optional[str] = None, retries: int = 0):
        return self.request("POST", url, data=data, referer=referer, retries=retries)


def _refusal(resp) -> Optional[str]:
    """Why an answer is a refusal, or None. A plain HTTP 202 is not one: Singapore's portal sends it while a page is
    being prepared, and only the WAF header turns it into a challenge."""
    headers = {str(k).lower(): v for k, v in (getattr(resp, "headers", None) or {}).items()}
    action = headers.get("x-amzn-waf-action")
    if action:
        return f"HTTP {resp.status_code}, WAF {action}"
    if resp.status_code in (403, 429, 467, 503):
        return f"HTTP {resp.status_code}"
    return None


def _is_robots(url: str) -> bool:
    return url.split("?", 1)[0].rstrip("/").lower().endswith("/robots.txt")


def _env_floats(name: str, default: tuple) -> tuple:
    raw = os.environ.get(name)
    if not raw:
        return tuple(default)
    values = tuple(float(v) for v in raw.replace(";", ",").split(",") if v.strip())
    return values or tuple(default)


def _retry_after_seconds(value: Optional[str], cap: float, default: float) -> float:
    if not value:
        return default
    try:
        return min(cap, max(0.0, float(value)))
    except ValueError:
        pass
    try:
        when = email.utils.parsedate_to_datetime(value)
        return min(cap, max(0.0, (when - datetime.now(timezone.utc)).total_seconds()))
    except (TypeError, ValueError):
        return default
