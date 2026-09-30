"""Singapore — Statutes Online. The adapter package: `SgSsoAdapter` (adapter.py), the page parsers (parse.py) and
the catalogue step that writes the link list (catalogue.py). In the repo this package is
src/p1_scrape/adapters/sg_sso/, replacing the Round 1 module sg_sso.py; `from .sg_sso import SgSsoAdapter` keeps
working."""
from __future__ import annotations

from . import catalogue, parse
from .adapter import LISTINGS, SgSsoAdapter, SsoUnavailable

__all__ = ["LISTINGS", "SgSsoAdapter", "SsoUnavailable", "catalogue", "parse"]
