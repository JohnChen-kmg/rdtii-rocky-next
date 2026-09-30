"""Politeness: per-host rate limiting + advisory robots (§5.1).

Stance: seed-law canonical URLs (public statute pages) are never hard-blocked;
robots is advisory scope guidance for search/discovery paths. We crawl one
document at a time at a low, jittered rate with an identifiable UA.
"""
from __future__ import annotations

import random
import time
import urllib.robotparser
from urllib.parse import urlparse

from .utils import host_of


class RateLimiter:
    """Enforce a minimum jittered delay between requests to the same host."""

    def __init__(self, delay_seconds: float):
        self.delay = max(0.0, delay_seconds)
        self._last: dict[str, float] = {}

    def wait(self, url: str) -> None:
        host = host_of(url)
        now = time.monotonic()
        last = self._last.get(host)
        if last is not None:
            jitter = random.uniform(0, self.delay * 0.5)
            target = last + self.delay + jitter
            sleep_for = target - now
            if sleep_for > 0:
                time.sleep(sleep_for)
        self._last[host] = time.monotonic()


class RobotsAdvisor:
    """Advisory robots check. Never a hard block on seed-law canonical URLs.

    Used to decide whether a *discovery/search* path should be avoided in favour of
    a canonical URL. Failure to fetch robots.txt is treated as 'allowed' (advisory).
    """

    def __init__(self, user_agent: str, respect_for_discovery: bool = True):
        self.user_agent = user_agent
        self.respect_for_discovery = respect_for_discovery
        self._cache: dict[str, urllib.robotparser.RobotFileParser | None] = {}

    def _parser(self, url: str):
        parsed = urlparse(url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        if base not in self._cache:
            rp = urllib.robotparser.RobotFileParser()
            rp.set_url(base + "/robots.txt")
            try:
                rp.read()
            except Exception:
                rp = None  # advisory: unreachable robots => no guidance
            self._cache[base] = rp
        return self._cache[base]

    def discovery_allowed(self, url: str) -> bool:
        """True if a discovery/search fetch of `url` is within robots scope guidance."""
        if not self.respect_for_discovery:
            return True
        rp = self._parser(url)
        if rp is None:
            return True
        try:
            return rp.can_fetch(self.user_agent, url)
        except Exception:
            return True
