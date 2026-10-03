"""The address a saved web page came from, read from the file itself. Nothing is ever fetched.

A browser's "Save page as" writes the page's address into the file as a comment; a page usually names its
own canonical address as well. Either one spares the person from typing it. An address found this way
becomes the document's cited source, so only http and https addresses of a sane length are accepted, and
the basis is kept with it.
"""
from __future__ import annotations

import html
import re

MAX_URL = 2000
_SAVED_FROM = re.compile(rb"<!--\s*saved from url=\(\d{1,5}\)\s*(\S+)", re.I)
_CANONICAL = re.compile(rb"<link\b[^>]*\brel\s*=\s*[\"']?canonical[\"']?[^>]*>", re.I)
_OG_URL = re.compile(rb"<meta\b[^>]*\bproperty\s*=\s*[\"']?og:url[\"']?[^>]*>", re.I)
_HREF = re.compile(rb"\b(?:href|content)\s*=\s*(?:\"([^\"]*)\"|'([^']*)'|([^\s>]+))", re.I)


def valid_url(url: str) -> bool:
    """An http or https address with a host, no spaces or control characters, of a sane length."""
    url = str(url or "")
    if not url or len(url) > MAX_URL or re.search(r"[\s\x00-\x1f\x7f]", url):
        return False
    return bool(re.match(r"^https?://[^/\s?#]+\.[^/\s?#]+", url, re.I) or re.match(r"^https?://localhost\b", url, re.I))


def _attr(tag: bytes) -> str:
    for m in _HREF.finditer(tag):
        raw = next(g for g in m.groups() if g is not None)
        return html.unescape(raw.decode("utf-8", "replace")).strip()
    return ""


def recover_url(data: bytes) -> tuple[str, str]:
    """(address, basis) for a saved web page, or ("", ""). The basis says where in the file it was found."""
    head = data[:400_000]
    m = _SAVED_FROM.search(head)
    if m:
        # the browser states the address's length, but a hand-edited file may not match it: take the token
        url = m.group(1).decode("utf-8", "replace").strip()
        url = url[:-3] if url.endswith("-->") else url
        if valid_url(url):
            return url, "the browser's saved-from note in the file"
    for rx, basis in ((_CANONICAL, "the page's canonical link"), (_OG_URL, "the page's og:url")):
        m = rx.search(head)
        if m:
            url = _attr(m.group(0))
            if valid_url(url):
                return url, basis
    return "", ""
