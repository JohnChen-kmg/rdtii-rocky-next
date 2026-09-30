"""Lao PDR — the Lao Official Gazette. The adapter package: `LaGazetteAdapter` (adapter.py), the listing parser
(parse.py), the catalogue step that writes the link list (catalogue.py) and the law table (checker.py).
In the repo this package is src/p1_scrape/adapters/la_gazette/."""
from __future__ import annotations

from . import catalogue, checker, parse
from .adapter import GazetteUnavailable, LaGazetteAdapter
from .parse import LEGAL_TYPES, STATUS, fold

__all__ = ["GazetteUnavailable", "LEGAL_TYPES", "LaGazetteAdapter", "STATUS", "catalogue", "checker", "fold",
           "parse"]
