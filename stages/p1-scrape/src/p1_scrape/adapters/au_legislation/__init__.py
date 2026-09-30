"""Australia — the Federal Register of Legislation. The adapter package: `AuLegislationAdapter` (adapter.py), the
API records and addresses (api.py) and the catalogue step (catalogue.py). In the repo this package is
src/p1_scrape/adapters/au_legislation/, replacing the Round 1 module au_legislation.py; `from .au_legislation import
AuLegislationAdapter` keeps working."""
from __future__ import annotations

from . import api, catalogue
from .adapter import _MULTIVOL_DECL, AuLegislationAdapter, RegisterUnavailable   # _MULTIVOL_DECL: Round 1's tests import it

__all__ = ["AuLegislationAdapter", "RegisterUnavailable", "_MULTIVOL_DECL", "api", "catalogue"]
