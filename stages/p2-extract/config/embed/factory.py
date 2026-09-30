"""get_embedder(settings) - vendored for parity with rdtii-p3-map; UNUSED by P2.

The dense prefilter is Project 3's (PLAN.md finding #13). This stub keeps the
config/ tree identical across the two repos per contract section 5.2 without
dragging sentence-transformers into P2's pinned install.
"""

from __future__ import annotations

from config.settings import Settings


def get_embedder(settings: Settings):  # pragma: no cover - P3-only path
    raise NotImplementedError(
        "get_embedder is not used by rdtii-p2-extract (dense prefilter is "
        "Project 3's; see PLAN.md finding #13). rdtii-p3-map vendors the real "
        "implementation."
    )
