"""The paced, honest HTTP client every Chinese source goes through.

The developer's rule of 2026-09-21 lives here, in code, so no source module can bypass it:

1. **robots.txt forbids -> we do not fetch.** Read once per host, before the first request.
2. **If robots.txt itself is refused (401, 403, 412), permission cannot be established** and the host is
   refused. MIIT answers 403 for `/robots.txt`; that settles it without a policy argument.
3. **A refusal of a document (403, 412) is recorded and left alone.** It is never retried with another
   client, another User-Agent or a browser.
4. **Human pace**: 8 to 12 s between requests to one host, chosen at random each time.
5. **Rest and slow down** on 429 and 503 (the developer's rule of 2026-09-16): sleep, widen the delay, try again.
   Never just stop, never push harder.

The User-Agent says what we are. It is not configurable from the command line, on purpose.
"""
from __future__ import annotations

import random
import time
import urllib.error
import urllib.request
import urllib.robotparser
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urlparse

USER_AGENT = "RDTII-Rocky-Crawler/0.1 (+polite public-law retrieval)"

#: seconds between two requests to one host; a fresh value is drawn each time
DELAY_MIN, DELAY_MAX = 8.0, 12.0
#: on 429/503: rest this long, then multiply the delay by SLOWDOWN
REST_MIN, REST_MAX, SLOWDOWN, MAX_RESTS = 60.0, 300.0, 1.5, 4

REFUSED = {401, 403, 412}


class HostRefused(Exception):
    """The host does not permit us: robots.txt forbids the path, or robots.txt itself was refused."""


@dataclass
class Response:
    url: str
    status: int
    body: bytes
    content_type: str = ""

    @property
    def ok(self) -> bool:
        return 200 <= self.status < 300

    def text(self) -> str:
        for enc in ("utf-8", "gb18030"):
            try:
                return self.body.decode(enc)
            except UnicodeDecodeError:
                continue
        return self.body.decode("utf-8", errors="replace")


@dataclass
class _Host:
    robots: Optional[urllib.robotparser.RobotFileParser] = None
    verdict: str = ""  # "permits" | "none published" | "refused: ..."
    last: float = 0.0
    scale: float = 1.0


@dataclass
class PoliteClient:
    log: list = field(default_factory=list)
    hosts: dict = field(default_factory=dict)

    # ---- robots -------------------------------------------------------------------
    def _host(self, url: str) -> _Host:
        p = urlparse(url)
        key = f"{p.scheme}://{p.netloc}"
        if key in self.hosts:
            return self.hosts[key]
        h = _Host()
        self.hosts[key] = h
        status, body = self._raw(key + "/robots.txt", h)
        if status == 200 and body.lstrip().lower().startswith((b"user-agent", b"\xef\xbb\xbfuser-agent", b"#", b"allow", b"disallow", b"sitemap")):
            rp = urllib.robotparser.RobotFileParser()
            rp.parse(body.decode("utf-8", errors="replace").splitlines())
            h.robots, h.verdict = rp, "permits (rules read)"
        elif status in (404, 410) or (status == 200):
            # 200 with an HTML page is a catch-all, not a robots file: nothing is stated
            h.verdict = "none published"
        elif status in REFUSED:
            h.verdict = f"refused: robots.txt answered {status}"
        else:
            h.verdict = f"refused: robots.txt unreadable ({status})"
        self.log.append({"event": "robots", "host": key, "status": status, "verdict": h.verdict})
        return h

    def check(self, url: str) -> None:
        h = self._host(url)
        if h.verdict.startswith("refused"):
            raise HostRefused(f"{urlparse(url).netloc}: {h.verdict}")
        if h.robots is not None and not h.robots.can_fetch(USER_AGENT, url):
            raise HostRefused(f"{urlparse(url).netloc}: robots.txt disallows {urlparse(url).path}")

    # ---- pacing -------------------------------------------------------------------
    def _wait(self, h: _Host) -> None:
        gap = random.uniform(DELAY_MIN, DELAY_MAX) * h.scale
        due = h.last + gap
        now = time.time()
        if due > now:
            time.sleep(due - now)

    def _raw(self, url: str, h: _Host, data: Optional[bytes] = None, headers: Optional[dict] = None):
        self._wait(h)
        hdrs = {"User-Agent": USER_AGENT}
        if headers:
            hdrs.update(headers)
        req = urllib.request.Request(url, data=data, headers=hdrs)
        try:
            with urllib.request.urlopen(req, timeout=45) as r:
                body, status = r.read(), r.status
        except urllib.error.HTTPError as e:
            body, status = (e.read() if e.fp else b""), e.code
        except Exception:  # noqa: BLE001 - timeouts, TLS, resets
            body, status = b"", 0
        h.last = time.time()
        return status, body

    # ---- the one public fetch -----------------------------------------------------
    def get(self, url: str, data: Optional[bytes] = None, headers: Optional[dict] = None) -> Response:
        """Fetch one URL within the rules. Raises HostRefused; never retries a refusal."""
        self.check(url)
        h = self._host(url)
        for attempt in range(MAX_RESTS + 1):
            status, body = self._raw(url, h, data, headers)
            self.log.append({"event": "get", "url": url, "status": status, "bytes": len(body)})
            if status in (429, 503) and attempt < MAX_RESTS:
                rest = random.uniform(REST_MIN, REST_MAX)
                h.scale *= SLOWDOWN
                self.log.append({"event": "rest", "url": url, "seconds": round(rest), "scale": h.scale})
                print(f"      rest {rest:.0f}s after HTTP {status}; slowing to x{h.scale:.1f}", flush=True)
                time.sleep(rest)
                continue
            return Response(url, status, body)
        return Response(url, status, body)
