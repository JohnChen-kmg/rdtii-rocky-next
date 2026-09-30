"""handoff1/ storage layout + .headers.json sidecars (contract §2.1/§3.4).

Every retrieved file lands at raw/<cc>/<law_slug>/<ts>__<kind>.<ext> with a sibling
.headers.json capturing HTTP provenance. All paths returned are RELATIVE to the
hand-off dir (no absolute paths in the manifest — portability contract rule).
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .models import HttpMeta
from .utils import slugify, utc_stamp_compact


@dataclass
class StoredFile:
    local_path: str        # relative to handoff dir
    headers_path: str      # relative to handoff dir
    byte_size: int
    abs_path: Path


class Storage:
    def __init__(self, handoff_dir: Path):
        self.handoff_dir = Path(handoff_dir)

    def store(
        self,
        economy: str,
        law_name_or_slug: str,
        kind: str,          # native | scanned | page
        ext: str,           # pdf | html | ...
        content: bytes,
        http: HttpMeta,
    ) -> StoredFile:
        cc = economy.lower()
        law_slug = slugify(law_name_or_slug)
        rel_dir = Path("raw") / cc / law_slug
        abs_dir = self.handoff_dir / rel_dir
        abs_dir.mkdir(parents=True, exist_ok=True)

        stamp = utc_stamp_compact()
        fname = f"{stamp}__{kind}.{ext}"
        # Avoid clobbering if two artifacts share a stamp+kind (rare) — add a suffix.
        rel_file = rel_dir / fname
        abs_file = self.handoff_dir / rel_file
        n = 1
        while abs_file.exists():
            fname = f"{stamp}_{n}__{kind}.{ext}"
            rel_file = rel_dir / fname
            abs_file = self.handoff_dir / rel_file
            n += 1

        abs_file.write_bytes(content)
        headers_rel = rel_file.with_suffix(rel_file.suffix + ".headers.json")
        (self.handoff_dir / headers_rel).write_text(
            json.dumps(http.sidecar_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        to_posix = lambda p: str(p).replace("\\", "/")
        return StoredFile(
            local_path=to_posix(rel_file),
            headers_path=to_posix(headers_rel),
            byte_size=len(content),
            abs_path=abs_file,
        )
