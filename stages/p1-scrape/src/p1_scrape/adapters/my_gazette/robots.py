"""robots.txt rules for one product token (RFC 9309)."""
from __future__ import annotations

import re
from typing import Optional
from urllib.parse import unquote, urlsplit

_ROBOTS_TOKEN = "RDTII-Rocky-Crawler"


class RobotsRules:
    """The rules of one robots.txt for one product token.

    RFC 9309: the group naming the token (case-insensitive) applies, else the '*' group; Allow and
    Disallow patterns support '*' and a closing '$'; the longest matching pattern wins and Allow wins
    a tie; /robots.txt is always allowed. Crawl-delay and Request-rate are read from the same group.
    The standard library's robotparser is not used: it matches on the text before the first '/' of
    the whole User-Agent header ('Mozilla') and ignores wildcards.
    """

    def __init__(self, rules: list[tuple[bool, str]], crawl_delay: Optional[float],
                 request_rate: Optional[float], group: str):
        self.rules, self.crawl_delay, self.request_rate, self.group = rules, crawl_delay, request_rate, group

    @classmethod
    def parse(cls, text: str, token: str) -> "RobotsRules":
        groups: list[dict] = []
        cur: Optional[dict] = None
        in_agents = False
        for raw in (text or "").splitlines():
            line = raw.split("#", 1)[0].strip()
            if ":" not in line:
                continue
            key, value = (x.strip() for x in line.split(":", 1))
            key = key.lower()
            if key == "user-agent":
                if cur is None or not in_agents:
                    cur = {"agents": [], "rules": [], "crawl_delay": None, "request_rate": None}
                    groups.append(cur)
                cur["agents"].append(value.split("/", 1)[0].strip().lower())
                in_agents = True
                continue
            in_agents = False
            if cur is None:
                continue
            if key in ("allow", "disallow") and value:
                cur["rules"].append((key == "allow", value))
            elif key == "crawl-delay":
                try:
                    cur["crawl_delay"] = float(value)
                except ValueError:
                    pass
            elif key == "request-rate":
                m = re.match(r"^(\d+)\s*/\s*(\d+)\s*([smhd]?)", value)
                if m and int(m.group(1)) > 0:
                    unit = {"": 1, "s": 1, "m": 60, "h": 3600, "d": 86400}[m.group(3)]
                    cur["request_rate"] = int(m.group(2)) * unit / int(m.group(1))
        tok = token.lower()
        mine = [g for g in groups if tok in g["agents"]]
        name = token if mine else "*"
        if not mine:
            mine = [g for g in groups if "*" in g["agents"]]
        delays = [g["crawl_delay"] for g in mine if g["crawl_delay"] is not None]
        rates = [g["request_rate"] for g in mine if g["request_rate"] is not None]
        return cls([r for g in mine for r in g["rules"]], max(delays) if delays else None,
                   max(rates) if rates else None, name if mine else "none")

    def allowed(self, url: str) -> bool:
        parts = urlsplit(url)
        path = unquote(parts.path or "/") + (("?" + unquote(parts.query)) if parts.query else "")
        if path == "/robots.txt":
            return True
        best: Optional[tuple[int, bool]] = None
        for allow, pattern in self.rules:
            if _robots_pattern_matches(pattern, path):
                key = (len(pattern), allow)
                if best is None or key > best:
                    best = key
        return True if best is None else best[1]

    def min_delay(self) -> float:
        return max(self.crawl_delay or 0.0, self.request_rate or 0.0)


def _robots_pattern_matches(pattern: str, path: str) -> bool:
    anchored = pattern.endswith("$")
    body = unquote(pattern[:-1] if anchored else pattern)
    rx = "".join(".*" if ch == "*" else re.escape(ch) for ch in body) + ("$" if anchored else "")
    return re.match(rx, path, re.S) is not None


def robots_token(user_agent: str) -> str:
    """The product token robots.txt groups are matched on: this crawler's own name when the UA carries
    it, else the first product of the header."""
    if re.search(re.escape(_ROBOTS_TOKEN), user_agent or "", re.I):
        return _ROBOTS_TOKEN
    return ((user_agent or "").split("/", 1)[0].strip() or "*")
