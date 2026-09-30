"""economy code -> PortalAdapter."""
from __future__ import annotations

from ..sources import load_sources
from .au_legislation import AuLegislationAdapter
from .base import PortalAdapter
from .la_gazette import LaGazetteAdapter
from .my_gazette import MyGazetteAdapter
from .sg_sso import SgSsoAdapter
from .tl_jornal import TlJornalAdapter

#: Every economy this engine can crawl, in the order they were built. China has no
#: entry on purpose: the national database forbids automated collection, so China's
#: documents are collected by hand and its tools sit in adapters/cn_npc/.
_ADAPTERS = {
    "SG": SgSsoAdapter,
    "MY": MyGazetteAdapter,
    "AU": AuLegislationAdapter,
    "TL": TlJornalAdapter,
    "LA": LaGazetteAdapter,
}


def get_adapter(economy: str) -> PortalAdapter:
    cc = economy.upper()
    cfg = load_sources(cc)
    try:
        adapter = _ADAPTERS[cc]
    except KeyError:
        raise NotImplementedError(f"adapter for {cc} not supported") from None
    return adapter(cfg)
