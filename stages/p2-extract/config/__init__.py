"""Shared P7 config/model-swap package (contract section 5).

Vendored identically into rdtii-p2-extract and rdtii-p3-map from
00_contracts/config_template/. Both projects call get_llm(settings) /
get_ocr(settings) and never instantiate a vendor SDK directly - swapping
any model-bearing engine is a .env edit, not a rewrite.
"""

from config.settings import Settings, load_settings

__all__ = ["Settings", "load_settings"]
