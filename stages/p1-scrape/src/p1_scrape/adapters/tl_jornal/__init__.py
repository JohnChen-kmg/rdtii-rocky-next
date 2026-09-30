"""Timor-Leste — the Jornal da República. The adapter package: `TlJornalAdapter` (adapter.py), the category-page
parser (parse.py), the catalogue step that writes the link list (catalogue.py) and the law table (checker.py).
In the repo this package is src/p1_scrape/adapters/tl_jornal/."""
from __future__ import annotations

from . import catalogue, checker, parse
from .adapter import JornalUnavailable, TlJornalAdapter
from .parse import CATEGORIES

__all__ = ["CATEGORIES", "JornalUnavailable", "TlJornalAdapter", "catalogue", "checker", "parse"]
